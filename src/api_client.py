"""
Generic API Client for RESTful operations
Created by D. Theoden
Date: June 12, 2025
"""

import requests
from .auth import build_auth_headers
from .config import (URL, BASE_PATH, BACKEND, EDGE_METHOD_PREFIX, TIMEOUT)


class APIClient:
    def __init__(self):
        self.url = (URL or '').rstrip('/')
        self.base_path = BASE_PATH or ''
        self.backend = BACKEND
        self.edge_method_prefix = EDGE_METHOD_PREFIX
        self.timeout = TIMEOUT
        self.headers: dict[str, str] | None = None

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

    def get_items(self, endpoint, expand=None, filter_param=None, select=None):
        """Retrieve items from the configured API backend."""
        try:
            self._ensure_headers()

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
            return response.json()
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
