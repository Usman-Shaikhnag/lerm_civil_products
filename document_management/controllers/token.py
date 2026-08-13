# -*- coding: utf-8 -*-

import base64
import hashlib
import hmac
import json
import time

from odoo import http
from odoo.exceptions import UserError


def _b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _b64url_decode(data):
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _get_secret():
    icp = http.request.env['ir.config_parameter'].sudo()
    secret = icp.get_param('document_management.fastapi_secret', '')
    if not secret:
        raise UserError(
            'The FastAPI shared secret is not configured. '
            'Please set it in Settings -> Document Management.')
    return secret.encode('utf-8')


def issue_token(claims, ttl=600, secret=None):
    """Issue a compact HMAC-SHA256 JWT with the configured shared secret.

    Pass `secret` explicitly (e.g. from an env) when no HTTP request is active.
    """
    now = int(time.time())
    payload = dict(claims)
    payload['iat'] = now
    payload['exp'] = now + ttl
    header = {'alg': 'HS256', 'typ': 'JWT'}
    signing_input = (
        _b64url_encode(json.dumps(header).encode('utf-8')) + '.' +
        _b64url_encode(json.dumps(payload).encode('utf-8'))
    )
    if secret is None:
        secret = _get_secret()
    signature = hmac.new(secret, signing_input.encode('utf-8'),
                         hashlib.sha256).digest()
    return signing_input + '.' + _b64url_encode(signature)


def decode_token(token):
    """Decode and verify a token. Returns claims dict or None."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        signing_input = parts[0] + '.' + parts[1]
        signature = _b64url_decode(parts[2])
        expected = hmac.new(_get_secret(), signing_input.encode('utf-8'),
                            hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            return None
        claims = json.loads(_b64url_decode(parts[1]))
        if int(claims.get('exp', 0)) < int(time.time()):
            return None
        return claims
    except Exception:
        return None
