# Preview and thumbnail endpoints.

import os

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

import config
import converters

router = APIRouter(prefix='/api/v1/files', tags=['preview'])


def _token_from_request(authorization: str = Header(None, alias='Authorization'), token: str = None):
    if token:
        return token
    if authorization and authorization.lower().startswith('bearer '):
        return authorization[7:].strip()
    return None


@router.get('/preview', response_class=HTMLResponse)
async def preview_file(
    token: str = None,
    authorization: str = Header(None, alias='Authorization'),
):
    claims = config.require_op(_token_from_request(authorization, token), 'preview')
    path = config.resolve_path(claims.get('path', ''))
    if not os.path.isfile(path):
        raise HTTPException(404, 'File not found.')

    kind = converters.guess_kind(path)
    if kind == 'image':
        return FileResponse(path)
    if kind == 'pdf':
        return FileResponse(path, media_type='application/pdf')
    if kind == 'csv':
        try:
            html_body = converters.csv_to_html(path)
        except Exception:
            raise HTTPException(415, 'Could not read this CSV file.')
        return _html_document(html_body, os.path.basename(path))
    if kind == 'excel':
        try:
            pdf = converters.get_or_create_pdf(path)
            return FileResponse(pdf, media_type='application/pdf')
        except converters.ConversionError:
            try:
                html_body = converters.xlsx_to_html(path)
            except Exception:
                raise HTTPException(415, 'Preview not available for this spreadsheet.')
            return _html_document(html_body, os.path.basename(path))
    if kind == 'word':
        try:
            pdf = converters.get_or_create_pdf(path)
            return FileResponse(pdf, media_type='application/pdf')
        except converters.ConversionError:
            raise HTTPException(415, 'Preview not available for this document.')
    raise HTTPException(415, 'Preview not available for this file type.')


@router.get('/thumbnail')
async def thumbnail_file(
    token: str = None,
    authorization: str = Header(None, alias='Authorization'),
):
    claims = config.require_op(_token_from_request(authorization, token), 'thumbnail')
    path = config.resolve_path(claims.get('path', ''))
    if not os.path.isfile(path):
        raise HTTPException(404, 'File not found.')
    kind = converters.guess_kind(path)
    if kind != 'image':
        raise HTTPException(415, 'Thumbnails are only available for images.')
    try:
        from PIL import Image
    except ImportError:
        return FileResponse(path)
    sha = config.sha256_of(path)
    thumb_path = os.path.join(config.PREVIEW_CACHE_DIR, sha + '_thumb.png')
    if not os.path.exists(thumb_path):
        with Image.open(path) as img:
            img.thumbnail((256, 256))
            img.convert('RGB').save(thumb_path, 'PNG')
    return FileResponse(thumb_path, media_type='image/png')


def _html_document(body_html, title):
    css = (
        'body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#fff;'
        'margin:0;padding:16px;color:#1f2328}'
        '.dms-preview-note{color:#6e7781;font-size:12px;margin-top:8px}'
        '.dms-empty{color:#6e7781;padding:24px;text-align:center}'
        '.dms-table-wrap{overflow:auto;max-height:70vh;border:1px solid #d0d7de;'
        'border-radius:8px}'
        '.dms-preview-table{border-collapse:collapse;width:100%;font-size:13px}'
        '.dms-preview-table th,.dms-preview-table td{border:1px solid #d0d7de;'
        'padding:6px 10px;text-align:left;white-space:nowrap}'
        '.dms-preview-table thead th{position:sticky;top:0;background:#f6f8fa;'
        'font-weight:600}'
        '.dms-preview-table tbody tr:nth-child(even){background:#fafbfc}'
    )
    return HTMLResponse(
        '<!DOCTYPE html><html><head><meta charset="utf-8"><title>' +
        os.path.basename(title) + '</title><style>' + css +
        '</style></head><body>' + body_html + '</body></html>'
    )
