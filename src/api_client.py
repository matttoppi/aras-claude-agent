"""
Generic API Client for RESTful operations
Created by D. Theoden
Date: June 12, 2025
"""

import time
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher

import requests

from .auth import build_auth_headers
from .config import (
    AUTO_RESOLVE_ITEMTYPE,
    BASE_PATH,
    BACKEND,
    EDGE_METHOD_PREFIX,
    ITEMTYPE_ALIASES,
    SCHEMA_CACHE_TTL,
    TIMEOUT,
    URL,
)


class APIClient:
    def __init__(self):
        self.url = (URL or '').rstrip('/')
        self.base_path = BASE_PATH or ''
        self.backend = BACKEND
        self.edge_method_prefix = EDGE_METHOD_PREFIX
        self.timeout = TIMEOUT
        self.headers: dict[str, str] | None = None
        self._schema_cache: dict | None = None
        self._schema_cache_time: float = 0.0

    def authenticate(self):
        """Authenticate with the API and cache headers."""
        try:
            self.headers = build_auth_headers()
            return True
        except Exception as error:
            import sys
            self.headers = None
            print(f"Authentication error: {error}", file=sys.stderr)
            return False

    def _ensure_headers(self):
        if self.headers is None:
            if not self.authenticate():
                raise RuntimeError('Failed to authenticate with API backend')

    @staticmethod
    def _join(*parts: str) -> str:
        cleaned = []
        for part in parts:
            if not part:
                continue
            cleaned.append(part.strip('/'))
        if not cleaned:
            return ''
        result = cleaned[0]
        for piece in cleaned[1:]:
            result = f"{result}/{piece}"
        return result

    def _build_url(self, endpoint: str, is_method: bool = False) -> str:
        endpoint = (endpoint or '').strip('/')

        if self.backend == 'ARAS':
            base = self._join(self.url, self.base_path)
            if is_method:
                return self._join(base, f"Method('{endpoint}')")
            return self._join(base, endpoint)

        # EDGE routing: expect API_URL (and optional BASE_PATH) to include instance/app
        base = self._join(self.url, self.base_path)
        if is_method:
            return self._join(base, self.edge_method_prefix, endpoint)
        return self._join(base, endpoint)

    def get_metadata_raw(self) -> str:
        """Fetch OData $metadata (CSDL) with BOM-safe UTF-8 decoding."""
        self._ensure_headers()
        metadata_url = self._build_url('$metadata')
        response = requests.get(
            metadata_url,
            headers={
                'Accept': 'application/xml',
                **(self.headers or {}),
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.content.decode('utf-8-sig', errors='replace')

    def _build_schema_index(self) -> dict:
        """Parse CSDL and build a lookup of entity sets to types."""
        csdl = self.get_metadata_raw()
        ns = {
            'edmx': 'http://docs.oasis-open.org/odata/ns/edmx',
            'edm': 'http://docs.oasis-open.org/odata/ns/edm',
        }
        root = ET.fromstring(csdl)

        type_shortname: dict[str, str] = {}
        entity_sets: dict[str, dict[str, str]] = {}

        for schema in root.findall('edmx:DataServices/edm:Schema', ns):
            namespace = schema.get('Namespace', '')
            for entity_type in schema.findall('edm:EntityType', ns):
                et_name = entity_type.get('Name')
                if namespace and et_name:
                    type_shortname[f'{namespace}.{et_name}'] = et_name

            for container in schema.findall('edm:EntityContainer', ns):
                for entity_set in container.findall('edm:EntitySet', ns):
                    es_name = entity_set.get('Name')
                    entity_type_fqn = entity_set.get('EntityType')
                    if not es_name or not entity_type_fqn:
                        continue

                    short = type_shortname.get(
                        entity_type_fqn, entity_type_fqn.split('.')[-1]
                    )
                    entity_sets[es_name] = {
                        'entity_type': entity_type_fqn,
                        'short_type': short,
                        'namespace': entity_type_fqn.rsplit('.', 1)[0]
                        if '.' in entity_type_fqn
                        else '',
                    }

        def _norm(value: str) -> str:
            return ''.join(ch for ch in (value or '').lower() if ch.isalnum())

        return {
            'entities': entity_sets,
            'by_exact': set(entity_sets.keys()),
            'by_norm': {_norm(name): name for name in entity_sets.keys()},
            '_norm': _norm,
        }

    def _get_schema_index(self, force: bool = False) -> dict:
        """Return cached schema index, refreshing on TTL expiration."""
        now = time.time()
        if (
            force
            or self._schema_cache is None
            or (now - self._schema_cache_time) > SCHEMA_CACHE_TTL
        ):
            self._schema_cache = self._build_schema_index()
            self._schema_cache_time = now
        return self._schema_cache

    def resolve_endpoint(self, candidate: str, min_score: float = 0.82) -> dict:
        """Resolve a user-supplied label to an entity set."""
        idx = self._get_schema_index()
        norm = idx['_norm']

        candidate_norm = norm(candidate)
        # Alias lookup (direct and normalized)
        alias_match = (
            ITEMTYPE_ALIASES.get(candidate)
            or ITEMTYPE_ALIASES.get(candidate.lower())
            or ITEMTYPE_ALIASES.get(candidate.upper())
        )
        if not alias_match:
            for alias_key, target in ITEMTYPE_ALIASES.items():
                if norm(alias_key) == candidate_norm:
                    alias_match = target
                    break

        if alias_match:
            return {
                'match': alias_match,
                'score': 1.0,
                'reason': 'alias',
                'suggestions': [],
            }

        if candidate_norm in idx['by_norm']:
            entity = idx['by_norm'][candidate_norm]
            return {
                'match': entity,
                'score': 1.0,
                'reason': 'normalized-equal',
                'suggestions': [],
            }

        best: tuple[str, float] | None = None
        suggestions: list[tuple[str, float]] = []

        for entity_set in idx['by_exact']:
            score = SequenceMatcher(None, candidate_norm, norm(entity_set)).ratio()
            suggestions.append((entity_set, score))
            if best is None or score > best[1]:
                best = (entity_set, score)

        suggestions.sort(key=lambda item: item[1], reverse=True)
        top_suggestions = suggestions[:5]

        if best and best[1] >= min_score:
            return {
                'match': best[0],
                'score': best[1],
                'reason': 'fuzzy',
                'suggestions': top_suggestions,
            }

        return {
            'match': None,
            'score': best[1] if best else 0.0,
            'reason': 'no-match',
            'suggestions': top_suggestions,
        }

    def get_items(
        self,
        endpoint,
        expand=None,
        filter_param=None,
        select=None,
        auto_resolve: bool | None = None,
    ):
        """Retrieve items from the configured API backend (with optional endpoint auto-resolution)."""
        try:
            self._ensure_headers()

            requested_endpoint = endpoint
            resolution_note = ''

            do_auto_resolve = (
                AUTO_RESOLVE_ITEMTYPE if auto_resolve is None else bool(auto_resolve)
            )

            # Auto resolve by fuzzy lookup of entity sets and aliases
            if do_auto_resolve:
                try:
                    idx = self._get_schema_index()
                    if endpoint not in idx['by_exact']:
                        resolution = self.resolve_endpoint(endpoint)
                        if resolution.get('match'):
                            resolution_note = (
                                f"resolved '{endpoint}' -> '{resolution['match']}' "
                                f"(via {resolution.get('reason')}, score={resolution.get('score', 0):.2f})"
                            )
                            endpoint = resolution['match']
                except Exception:
                    # Endpoint resolution is best-effort; fall back silently.
                    pass

            api_url = self._build_url(endpoint)
            params = []
            if expand:
                params.append(f"$expand={expand}")
            if filter_param:
                params.append(f"$filter={filter_param}")
            if select:
                params.append(f"$select={select}")
            if params:
                api_url = f"{api_url}?{'&'.join(params)}"

            response = requests.get(
                api_url,
                headers={
                    'Accept': 'application/json',
                    **(self.headers or {}),
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            if resolution_note and isinstance(data, dict):
                meta = data.setdefault('_meta', {})
                meta['endpoint_resolution'] = resolution_note
                meta['requested_endpoint'] = requested_endpoint
            return data
        except Exception as error:
            import sys
            print(f"Error getting items: {error}", file=sys.stderr)
            raise error

    def create_item(self, endpoint, data):
        """Create a new item using the configured API backend."""
        try:
            self._ensure_headers()
            response = requests.post(
                self._build_url(endpoint),
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    **(self.headers or {}),
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as error:
            import sys
            print(f"Error creating item: {error}", file=sys.stderr)
            raise error

    def call_method(self, method_name, data):
        """Invoke a method on the configured API backend."""
        try:
            self._ensure_headers()
            response = requests.post(
                self._build_url(method_name, is_method=True),
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    **(self.headers or {}),
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as error:
            import sys
            print(f"Error calling method {method_name}: {error}", file=sys.stderr)
            raise error

    def get_list(self, list_id, expand=None):
        """Get list data from the configured API backend."""
        try:
            self._ensure_headers()
            if self.backend == 'ARAS':
                list_url = self._build_url(f"List('{list_id}')")
            else:
                list_url = self._build_url(list_id)
            if expand:
                list_url = f"{list_url}?$expand={expand}"

            response = requests.get(
                list_url,
                headers={
                    'Accept': 'application/json',
                    **(self.headers or {}),
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Exception as error:
            import sys
            print(f"Error getting list {list_id}: {error}", file=sys.stderr)
            raise error
