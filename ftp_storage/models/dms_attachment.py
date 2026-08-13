# -*- coding: utf-8 -*-

import base64
import re
from io import BytesIO

import requests

from odoo.exceptions import UserError

from odoo.addons.document_management.controllers.token import issue_token

DMS_RECORD_MODELS = ('lerm.civil.srf', 'lerm.srf.sample', 'lerm.eln')

RECORD_FIELD_DOC_TYPES = {
    ('lerm.civil.srf', 'attachment_path'): 'SRF Attachment',
    ('lerm.srf.sample', 'datasheet_path'): 'Sample Datasheet',
    ('lerm.srf.sample', 'report_path'): 'Sample Report',
    ('lerm.eln', 'witness_path'): 'ELN Witness',
    ('lerm.eln', 'attachment_path'): 'ELN Attachment',
}


def _sanitize(value):
    name = str(value or '').strip()
    name = name.replace(' ', '_')
    name = re.sub(r'[^A-Za-z0-9._-]', '_', name)
    return name or 'record'


def record_folder_parts(record):
    """Nested DMS folder path parts for a record, e.g. SRF/<srf>/<kes>/<eln>."""
    if record._name == 'lerm.civil.srf':
        return ['SRF', _sanitize(record.srf_id)]
    if record._name == 'lerm.srf.sample':
        srf_no = _sanitize(record.srf_id.srf_id) if record.srf_id else 'SRF'
        return ['SRF', srf_no, _sanitize(record.kes_no)]
    if record._name == 'lerm.eln':
        sample = record.sample_id
        srf_no = _sanitize(sample.srf_id.srf_id) if sample and sample.srf_id else 'SRF'
        kes_no = _sanitize(sample.kes_no) if sample else 'SAMPLE'
        return ['SRF', srf_no, kes_no, _sanitize(record.eln_id)]
    return []


def dms_config(env):
    """URL of the FastAPI backend as seen from the Odoo server itself."""
    icp = env['ir.config_parameter'].sudo()
    url = (icp.get_param('document_management.fastapi_server_url') or '').strip()
    if not url:
        url = (icp.get_param('document_management.fastapi_url') or '').strip()
    url = url.rstrip('/')
    if not url:
        raise UserError(
            'The DMS FastAPI backend is not configured. '
            'Set it in Settings -> Document Management.')
    return url


def dms_secret(env):
    secret = env['ir.config_parameter'].sudo().get_param(
        'document_management.fastapi_secret', '')
    if not secret:
        raise UserError(
            'The DMS shared secret is not configured. '
            'Set it in Settings -> Document Management.')
    return secret.encode('utf-8')


def _decode_binary(value):
    """A Binary field value is base64-encoded (str or bytes); decode it."""
    if isinstance(value, str):
        value = value.encode('utf-8')
    if isinstance(value, bytes):
        try:
            return base64.b64decode(value, validate=True)
        except Exception:
            return value
    return value


def _find_or_create_folder(env, parts):
    Folder = env['dms.folder'].sudo()
    current = False
    for part in parts:
        folder = Folder.search([
            ('name', '=', part),
            ('parent_id', '=', current.id if current else False),
        ], limit=1)
        if not folder:
            folder = Folder.create({
                'name': part,
                'parent_id': current.id if current else False,
            })
        current = folder
    return current


def _document_type_id(env, record, record_field):
    name = RECORD_FIELD_DOC_TYPES.get((record._name, record_field))
    if not name:
        return False
    doc_type = env['dms.document.type'].sudo().search([('name', '=', name)], limit=1)
    return doc_type.id if doc_type else False


def upload_to_dms(env, record, file_data, file_name, record_field):
    """Upload a record attachment to the DMS and create the linked dms.file."""
    if not file_data:
        raise UserError('No file data provided.')
    url = dms_config(env)
    parts = record_folder_parts(record)
    folder = _find_or_create_folder(env, parts)
    folder_path = '/'.join(parts) if parts else ''

    token = issue_token({'uid': env.uid, 'fid': 0, 'path': folder_path, 'op': 'upload'},
                        secret=dms_secret(env))

    resp = requests.post(
        url + '/api/v1/files/upload?token=' + token,
        files={'file': (file_name, BytesIO(_decode_binary(file_data)),
                        'application/octet-stream')},
        data={'folder_path': folder_path},
        timeout=120,
    )
    if resp.status_code >= 400:
        raise UserError('DMS upload failed: %s' % resp.text[:300])
    data = resp.json()

    File = env['dms.file'].sudo()
    # One file per record + button: replace any previous upload.
    File.search([
        ('res_model', '=', record._name),
        ('res_id', '=', record.id),
        ('record_field', '=', record_field),
    ]).unlink()

    return File.create({
        'name': data['name'],
        'original_name': file_name,
        'folder_id': folder.id or False,
        'mime_type': data.get('mime') or 'application/octet-stream',
        'size': data.get('size') or 0,
        'sha256': data.get('sha256') or '',
        'storage_path': data.get('storage_path') or '',
        'res_model': record._name,
        'res_id': record.id,
        'record_field': record_field,
        'document_type_id': _document_type_id(env, record, record_field),
        'status': 'active',
        'user_id': env.user.id,
    })


def record_download_url(record, record_field):
    return '/dms/record_file/%s/%s/%s/download' % (record._name, record.id, record_field)
