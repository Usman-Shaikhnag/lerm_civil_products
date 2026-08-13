# DMS FastAPI backend entrypoint.
#
#   uvicorn main:app --host 0.0.0.0 --port 8000
#
# Environment variables:
#   DMS_STORAGE_PATH    directory where files are stored (default: /var/lib/dms_files)
#   DMS_SECRET          shared secret with Odoo (required)
#   DMS_LIBREOFFICE_BIN path to LibreOffice binary (default: soffice)
#   DMS_MAX_UPLOAD_MB   maximum upload size in MB (default: 512)

import os

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import config
from converters import ConversionError
from routers import files, preview


@asynccontextmanager
async def lifespan(app: FastAPI):
    config._ensure_storage()
    yield


app = FastAPI(
    title='DMS Backend',
    version='1.0.0',
    description='Local file storage and preview conversion backend for the Odoo DMS module.',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
    max_age=0,  # never cache preflight responses (avoid stale CORS in browsers)
)

app.include_router(files.router)
app.include_router(preview.router)


@app.exception_handler(config.TokenError)
async def token_error_handler(request: Request, exc: config.TokenError):
    return JSONResponse(status_code=401, content={'detail': str(exc)})


@app.exception_handler(ConversionError)
async def conversion_error_handler(request: Request, exc: ConversionError):
    return JSONResponse(status_code=422, content={'detail': str(exc)})


@app.get('/api/v1/health')
def health():
    return {
        'status': 'ok',
        'storage': config.STORAGE_PATH,
        'storage_ok': os.path.isdir(config.STORAGE_PATH) and os.access(config.STORAGE_PATH, os.W_OK),
        'secret_configured': bool(config.SECRET),
    }


@app.get('/api/v1/config')
def config_endpoint():
    return {
        'storage_path': config.STORAGE_PATH,
        'secret_configured': bool(config.SECRET),
    }
