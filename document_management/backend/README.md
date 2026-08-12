# DMS FastAPI Backend

Microservice that stores documents on the local server and renders previews for
the Odoo **Document Management System** module.

## Features

- Local server file storage (configurable location)
- Streamed downloads with HTTP Range support
- Previews:
  - **PDF / Images** – served directly
  - **DOCX / DOC / XLSX / XLS** – converted to PDF with headless LibreOffice
  - **XLSX** – falls back to an HTML table via `openpyxl`
  - **CSV** – rendered as an HTML table
- Token auth (HMAC-SHA256 JWT) signed by Odoo with a shared secret
- Rename / move / delete of the physical files

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

LibreOffice is required for DOCX/XLSX previews:

```bash
# macOS
brew install --cask libreoffice
# Debian/Ubuntu
apt-get install libreoffice
```

## Run

```bash
export DMS_STORAGE_PATH=/var/lib/dms_files
export DMS_SECRET='<same secret as configured in Odoo Settings>'
export DMS_LIBREOFFICE_BIN=soffice
uvicorn main:app --host 0.0.0.0 --port 8000
```

Health check: `GET /api/v1/health`

## Configuration

| Env var | Default | Description |
|---|---|---|
| `DMS_STORAGE_PATH` | `/var/lib/dms_files` | Where documents are stored (must match Odoo settings) |
| `DMS_SECRET` | *(empty)* | Shared secret used to verify tokens signed by Odoo |
| `DMS_LIBREOFFICE_BIN` | `soffice` | Path to the LibreOffice binary |
| `DMS_MAX_UPLOAD_MB` | `512` | Maximum upload size in MB |

## Endpoints

| Method | Path | Token op | Description |
|---|---|---|---|
| POST | `/api/v1/files/upload` | `upload` | Upload a file (multipart `file` + `folder_path` form field) |
| GET | `/api/v1/files/content` | `download` | Stream the file (attachment, Range supported) |
| GET | `/api/v1/files/preview` | `preview` | Render a preview (PDF / image / HTML table) |
| GET | `/api/v1/files/thumbnail` | `thumbnail` | Resized thumbnail for images |
| DELETE | `/api/v1/files` | `delete` | Delete the physical file |
| POST | `/api/v1/files/move` | `move` | Rename / move the physical file (`{"new_path": "..."}`) |
| GET | `/api/v1/health` | – | Service health |

Tokens are issued by Odoo (`/dms/get_token`). Pass them either in the
`Authorization: Bearer <token>` header or as a `?token=` query parameter.
