"""
Authentication module for API access
Created by D. Theoden
Date: June 12, 2025
"""

import base64
import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import LegacyApplicationClient
from .config import (
    URL,
    USERNAME,
    PASSWORD,
    DATABASE,
    AUTH_MODE,
    EDGE_API_KEY,
    EDGE_API_KEY_HEADER,
    EDGE_BEARER_TOKEN,
    EDGE_BASIC_USER,
    EDGE_BASIC_PASS,
)


def get_bearer_token():
    """Get bearer token using OAuth 2.0 Resource Owner Password Credentials Grant."""
    try:
        client = LegacyApplicationClient(client_id='IOMApp')
        oauth = OAuth2Session(client=client)
        token_url = f"{URL}/oauthserver/connect/token"

        token = oauth.fetch_token(
            token_url=token_url,
            username=USERNAME,
            password=PASSWORD,
            client_id='IOMApp',
            scope='openid Innovator offline_access',
            database=DATABASE,
        )

        return token['access_token']

    except Exception as err:
        import sys
        print(f"Error in get_bearer_token: {err}", file=sys.stderr)
        return get_bearer_token_manual()


def get_bearer_token_manual():
    """Fallback manual OAuth 2.0 implementation."""
    try:
        token_url = f"{URL}/oauthserver/connect/token"
        token_data = {
            'grant_type': 'password',
            'username': USERNAME,
            'password': PASSWORD,
            'database': DATABASE,
            'scope': 'openid Innovator offline_access',
            'client_id': 'IOMApp',
        }

        token_response = requests.post(
            token_url,
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )

        token_response.raise_for_status()
        token_json = token_response.json()
        return token_json['access_token']

    except requests.exceptions.HTTPError as http_err:
        import sys
        print(f"HTTP error in get_bearer_token_manual: {http_err}", file=sys.stderr)
        print(f"Response content: {http_err.response.text}", file=sys.stderr)
        raise http_err
    except Exception as err:
        import sys
        print(f"Error in get_bearer_token_manual: {err}", file=sys.stderr)
        raise err


def build_auth_headers() -> dict[str, str]:
    """Construct request headers for the configured auth mode."""
    mode = AUTH_MODE
    if mode == 'ARAS_OAUTH':
        token = get_bearer_token()
        return {'Authorization': f'Bearer {token}'}
    if mode == 'NONE':
        return {}
    if mode == 'API_KEY':
        if not EDGE_API_KEY:
            raise ValueError('AUTH_MODE=API_KEY requires EDGE_API_KEY')
        return {EDGE_API_KEY_HEADER: EDGE_API_KEY}
    if mode == 'EDGE_BEARER':
        if not EDGE_BEARER_TOKEN:
            raise ValueError('AUTH_MODE=EDGE_BEARER requires EDGE_BEARER_TOKEN')
        return {'Authorization': f'Bearer {EDGE_BEARER_TOKEN}'}
    if mode == 'BASIC':
        if not EDGE_BASIC_USER or not EDGE_BASIC_PASS:
            raise ValueError('AUTH_MODE=BASIC requires EDGE_BASIC_USER and EDGE_BASIC_PASS')
        creds = f'{EDGE_BASIC_USER}:{EDGE_BASIC_PASS}'
        encoded = base64.b64encode(creds.encode()).decode()
        return {'Authorization': f'Basic {encoded}'}
    raise ValueError(f'Unknown AUTH_MODE: {mode}')
