# Document Management System — FastAPI backend
#
# Run with:
#   export DMS_STORAGE_PATH=/var/lib/dms_files
#   export DMS_SECRET=change-me
#   uvicorn main:app --host 0.0.0.0 --port 8000
#
# Storage path and secret must match the Odoo settings
# (Settings -> Document Management).

import base64
import hashlib
import hmac
import json
import os
import time

STORAGE_PATH = os.environ.get('DMS_STORAGE_PATH', '/var/lib/dms_files')
SECRET = os.environ.get('DMS_SECRET', '').encode('utf-8')
LIBREOFFICE_BIN = os.environ.get('DMS_LIBREOFFICE_BIN', 'soffice')
PREVIEW_CACHE_DIR = os.path.join(STORAGE_PATH, '_preview_cache')
MAX_UPLOAD_BYTES = int(os.environ.get('DMS_MAX_UPLOAD_MB', '512')) * 1024 * 1024


class TokenError(Exception):
    pass


def _b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _b64url_decode(data):
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _ensure_storage():
    os.makedirs(STORAGE_PATH, exist_ok=True)
    os.makedirs(PREVIEW_CACHE_DIR, exist_ok=True)


def resolve_path(relative_path):
    """Resolve a storage-relative path to an absolute path, safely.
    Empty/blank paths resolve to the storage root."""
    _ensure_storage()
    root = os.path.normpath(STORAGE_PATH)
    if not relative_path:
        return root
    rel = relative_path.lstrip('/')
    full = os.path.normpath(os.path.join(STORAGE_PATH, rel))
    if full != root and not full.startswith(root + os.sep):
        raise TokenError('Invalid file path.')
    return full


def decode_token(token):
    if not token:
        raise TokenError('Missing token.')
    parts = token.split('.')
    if len(parts) != 3:
        raise TokenError('Malformed token.')
    signing_input = parts[0] + '.' + parts[1]
    try:
        signature = _b64url_decode(parts[2])
    except Exception as exc:
        raise TokenError('Malformed token signature.') from exc
    expected = hmac.new(SECRET, signing_input.encode('utf-8'), hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise TokenError('Invalid token signature.')
    try:
        claims = json.loads(_b64url_decode(parts[1]))
    except Exception as exc:
        raise TokenError('Invalid token payload.') from exc
    if int(claims.get('exp', 0)) < int(time.time()):
        raise TokenError('Token expired.')
    return claims


def require_op(token, operation):
    claims = decode_token(token)
    if claims.get('op') != operation:
        raise TokenError('Token does not allow this operation.')
    return claims


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()
