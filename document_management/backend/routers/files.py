# File upload / download / delete / move endpoints.

import hashlib
import os
import shutil

from fastapi import APIRouter, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse

import config
from converters import guess_kind

router = APIRouter(prefix='/api/v1/files', tags=['files'])


def _token_from_request(authorization: str = Header(None, alias='Authorization'), token: str = None):
    if token:
        return token
    if authorization and authorization.lower().startswith('bearer '):
        return authorization[7:].strip()
    return None


@router.post('/upload')
async def upload_file(
    file: UploadFile,
    folder_path: str = Form(''),
    token: str = None,
    authorization: str = Header(None, alias='Authorization'),
):
    claims = config.require_op(_token_from_request(authorization, token), 'upload')
    folder_path = folder_path or claims.get('path', '')
    safe_folder = config.resolve_path(folder_path)
    # resolve_path normalizes + ensures under storage root
    name = file.filename or 'file'
    safe_name = os.path.basename(name.replace(' ', '_'))
    if not safe_name:
        raise HTTPException(400, 'Invalid file name.')
    dest_dir = safe_folder
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, safe_name)
    if os.path.exists(dest):
        base, ext = os.path.splitext(safe_name)
        counter = 1
        while os.path.exists(os.path.join(dest_dir, '%s_%d%s' % (base, counter, ext))):
            counter += 1
        safe_name = '%s_%d%s' % (base, counter, ext)
        dest = os.path.join(dest_dir, safe_name)

    size = 0
    digest = hashlib.sha256()
    with open(dest, 'wb') as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > config.MAX_UPLOAD_BYTES:
                out.close()
                os.remove(dest)
                raise HTTPException(413, 'File exceeds maximum upload size.')
            digest.update(chunk)
            out.write(chunk)

    rel = os.path.relpath(dest, config.STORAGE_PATH)
    return {
        'name': safe_name,
        'storage_path': rel.replace(os.sep, '/'),
        'size': size,
        'sha256': digest.hexdigest(),
        'mime': file.content_type or 'application/octet-stream',
        'kind': guess_kind(dest),
    }


@router.get('/content')
async def download_file(
    token: str = None,
    authorization: str = Header(None, alias='Authorization'),
    filename: str = None,
):
    claims = config.require_op(_token_from_request(authorization, token), 'download')
    path = config.resolve_path(claims.get('path', ''))
    if not os.path.isfile(path):
        raise HTTPException(404, 'File not found.')
    download_name = filename or os.path.basename(path)
    media = 'application/octet-stream' if guess_kind(path) == 'other' else None
    return FileResponse(
        path,
        media_type=media,
        filename=download_name,
        content_disposition_type='attachment',
    )


@router.delete('')
async def delete_file(
    token: str = None,
    authorization: str = Header(None, alias='Authorization'),
):
    claims = config.require_op(_token_from_request(authorization, token), 'delete')
    path = config.resolve_path(claims.get('path', ''))
    if os.path.isfile(path):
        os.remove(path)
    # clean orphaned preview caches for this sha if present
    sha = claims.get('sha')
    if sha:
        cached = os.path.join(config.PREVIEW_CACHE_DIR, sha + '.pdf')
        if os.path.exists(cached):
            os.remove(cached)
    return {'deleted': True}


@router.post('/move')
async def move_file(
    body: dict,
    token: str = None,
    authorization: str = Header(None, alias='Authorization'),
):
    claims = config.require_op(_token_from_request(authorization, token), 'move')
    old_path = config.resolve_path(claims.get('path', ''))
    new_path = config.resolve_path(body.get('new_path') or '')
    if not os.path.isfile(old_path):
        raise HTTPException(404, 'Source file not found.')
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    shutil.move(old_path, new_path)
    return {
        'old_path': os.path.relpath(old_path, config.STORAGE_PATH).replace(os.sep, '/'),
        'new_path': os.path.relpath(new_path, config.STORAGE_PATH).replace(os.sep, '/'),
    }
