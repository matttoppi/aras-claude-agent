"""
Configuration module for API MCP Server
Created by D. Theoden
Date: June 12, 2025
"""

import os
from dotenv import load_dotenv

# Ensure values from .env override any pre-set environment variables
load_dotenv(override=True)

def _sanitize_base_url(url: str | None) -> str | None:
    """Normalize API_URL to avoid common mistakes.

    - Trim whitespace
    - Remove trailing slashes
    - Remove trailing '/Server' (case-insensitive) if present
    """
    if not url:
        return url
    u = url.strip().rstrip('/')
    # Remove trailing '/Server' if user included it in API_URL
    if u.lower().endswith('/server'):
        u = u[: -len('/server')]
    return u

URL = _sanitize_base_url(os.getenv('API_URL'))
USERNAME = os.getenv('API_USERNAME')
PASSWORD = os.getenv('API_PASSWORD')
DATABASE = os.getenv('ARAS_DATABASE')
TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
RETRY_COUNT = int(os.getenv('API_RETRY_COUNT', '3'))
RETRY_DELAY = int(os.getenv('API_RETRY_DELAY', '1'))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'api_client.log')

# Backend selection and routing
BACKEND = os.getenv('API_BACKEND', 'ARAS').upper()
EDGE_METHOD_PREFIX = os.getenv('EDGE_METHOD_PREFIX', 'methods')
DEFAULT_BASE_PATH = '/Server/Odata' if BACKEND == 'ARAS' else ''
BASE_PATH = os.getenv('API_BASE_PATH', DEFAULT_BASE_PATH)

# Authentication strategy inputs
AUTH_MODE = os.getenv(
    'AUTH_MODE',
    'ARAS_OAUTH' if BACKEND == 'ARAS' else 'NONE',
).upper()
EDGE_API_KEY_HEADER = os.getenv('EDGE_API_KEY_HEADER', 'x-api-key')
EDGE_API_KEY = os.getenv('EDGE_API_KEY')
EDGE_BEARER_TOKEN = os.getenv('EDGE_BEARER_TOKEN')
EDGE_BASIC_USER = os.getenv('EDGE_BASIC_USER')
EDGE_BASIC_PASS = os.getenv('EDGE_BASIC_PASS')
