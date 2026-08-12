# Document Management System (document_management)

Odoo 17 module that stores documents **locally on the server** with a modern
**OWL** Drive-like UI and a **FastAPI** backend for file storage, streaming and
preview conversion.

## Architecture

```
OWL UI (Odoo) ── jsonrpc ──▶ Odoo controllers  (metadata, permissions, audit, JWT)
     │
     └──── REST (Bearer JWT) ──▶ FastAPI  ──▶ local disk
                                 (upload / download / preview / delete / move)
```

- **Odoo** is the source of truth: metadata, permission engine, audit trail, session security.
- **FastAPI** stores the physical files on the server and renders previews.
- Storage path and FastAPI URL/secret are configurable in **Settings → Document Management**.

## Installation (Odoo in Docker)

This module is designed to run with **Odoo 17 in Docker** and a **FastAPI**
backend for file storage. Two parts:

- **A. Odoo (Docker)** — the module lives on the host and is mounted **into the
  container as a volume** (bind mount), then installed.
- **B. FastAPI backend** — run it either **in its own container**
  (recommended for a server) or **on the host** (for development / simple
  setups). Pick one option and skip the other.

### 0. Quick start — DMS backend in its own compose (easiest)

A `docker-compose.yml` ships with the module that runs **only the FastAPI
backend** (Odoo runs in your existing stack). It's fully standalone:

```bash
cd /path/to/document_management
DMS_SECRET='pick-a-long-random-secret' docker compose up -d dms-backend
```

Check it's healthy:

```bash
curl http://localhost:8000/api/v1/health   # {"status":"ok",...}
```

Then configure **Settings → Document Management** in your existing Odoo:

- **FastAPI Base URL** = `http://localhost:8000` (browser)
- **FastAPI Server URL** = `http://host.docker.internal:8000` (Odoo container →
  host port 8000; use the host LAN IP if `host.docker.internal` doesn't resolve)
- **Storage Path** = `/var/lib/dms_files`
- **Shared Secret** = the same `DMS_SECRET` you passed to `docker compose up`

> If you prefer, copy the `dms-backend` service block into your existing
> `docker-compose.yml` instead of running a second file — then use
> `http://dms-backend:8000` as the Server URL if the services share a network.
> LibreOffice is installed in the container on first start (takes a few
> minutes); remove the apt line to skip Word previews.

### A. Install the Odoo module (Docker)

The addon is kept on the **host filesystem** in a folder that is **bind-mounted
into the Odoo container** as a volume. Your `docker-compose.yml` must map it to
the container addons path:

```yaml
services:
  web:
    image: odoo:17.0
    volumes:
      - /opt/odoo/addons:/mnt/extra-addons   # host addons folder mounted into the container
```

1. Copy `document_management` into the **host** folder that is mounted into the
   container (the bind-mount source, e.g. `/opt/odoo/addons`):

```bash
scp -r document_management user@server:/opt/odoo/addons/
chmod -R a+rX /opt/odoo/addons/document_management   # must be readable by the container
```

   Because of the bind mount, the module is immediately visible inside the
   container at `/mnt/extra-addons/document_management`.

2. Install it **inside the container**:

```bash
docker exec -it <web_container> odoo -d <dbname> -u document_management --stop-after-init \
  --db_host=db --db_user=odoo --db_password=odoo
docker restart <web_container>
```

`<dbname>` is your Odoo database. Verify:

```bash
docker exec -it <db_container> psql -U odoo -d <dbname> \
  -c "SELECT name,state FROM ir_module_module WHERE name='document_management';"
# expect: document_management | installed
```

> **Upgrading later:** edit/copy the files on the **host** folder, then re-run
> the same `docker exec ... -u document_management` command and restart the
> container — the bind mount means the container sees the new files immediately.

### B1. FastAPI in its own container (recommended for a server)

Add a service to your `docker-compose.yml`:

```yaml
  dms-backend:
    image: python:3.11-slim
    working_dir: /app
    ports:
      - "8000:8000"
    environment:
      - DMS_STORAGE_PATH=/var/lib/dms_files
      - DMS_SECRET=YOUR_LONG_RANDOM_SECRET
      - DMS_LIBREOFFICE_BIN=soffice
    volumes:
      - /opt/odoo/addons/document_management/backend:/app
      - dms-files:/var/lib/dms_files
    command: >
      sh -c "pip install --no-cache-dir -r /app/requirements.txt &&
             apt-get update && apt-get install -y --no-install-recommends libreoffice &&
             uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir /app"
    restart: unless-stopped

volumes:
  dms-files:
```

> Installing LibreOffice inside the image takes a while on first `up`. You can
> drop the `apt-get` line — Word previews will be unavailable but PDF, images,
> CSV and XLSX (HTML-table fallback) still work.

Start it:

```bash
docker compose up -d dms-backend
```

Then configure Odoo (see "Configure Odoo" below) with:

- **FastAPI Base URL** = `http://localhost:8000` (browser reaches the mapped port)
- **FastAPI Server URL** = `http://dms-backend:8000` (Odoo container reaches FastAPI by its compose service name)
- **Storage Path** = `/var/lib/dms_files`
- **Shared Secret** = `YOUR_LONG_RANDOM_SECRET`

### B2. FastAPI on the host (development / simple setups)

```bash
# on the server OS (not in Docker)
cd /opt/odoo/addons/document_management/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Debian/Ubuntu: sudo apt-get install libreoffice   (for Word/Excel previews)

export DMS_STORAGE_PATH=/var/lib/dms_files
export DMS_SECRET='YOUR_LONG_RANDOM_SECRET'
uvicorn main:app --host 0.0.0.0 --port 8000
```

Or use the bundled launcher: `DMS_SECRET='...' ./run.sh` (creates the venv and
starts uvicorn; `DMS_PORT` overrides the port).

For it to survive reboots, install it as a systemd service
(`/etc/systemd/system/dms-backend.service`):

```ini
[Unit]
Description=DMS FastAPI backend
After=network.target

[Service]
User=<odoo-user>
WorkingDirectory=/opt/odoo/addons/document_management/backend
Environment="DMS_STORAGE_PATH=/var/lib/dms_files"
Environment="DMS_SECRET=YOUR_LONG_RANDOM_SECRET"
ExecStart=/opt/odoo/addons/document_management/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now dms-backend
```

Then configure Odoo (see below) with:

- **FastAPI Base URL** = `http://<server-ip>:8000` (browser must be able to reach this — open the port or use a reverse proxy)
- **FastAPI Server URL** = `http://host.docker.internal:8000` (Odoo container → host FastAPI; if `host.docker.internal` doesn't resolve on your Linux Docker host, use the server's LAN IP, e.g. `http://192.168.x.x:8000`)
- **Storage Path** = `/var/lib/dms_files`
- **Shared Secret** = `YOUR_LONG_RANDOM_SECRET`

### Configure Odoo

Settings → Document Management (or the Documents → Settings menu):

- **Storage Path** — must match `DMS_STORAGE_PATH`.
- **FastAPI Base URL** — URL of the backend **as seen from the browser**.
- **FastAPI Server URL** — URL of the backend **as seen from the Odoo server**
  itself (used for rename/move/delete). Leave empty to reuse the browser URL.
- **Shared Secret** — must match `DMS_SECRET`.
- **Enable Audit Trail** — toggle login/document auditing.

### URL rules (most common source of trouble)

| Setting | Used for | Value |
|---|---|---|
| **FastAPI Base URL** | Upload / preview / download from the browser | `http://localhost:8000` (B1) or `http://<server-ip>:8000` (B2) |
| **FastAPI Server URL** | Rename / move / delete from the Odoo server | `http://dms-backend:8000` (B1) or `http://host.docker.internal:8000` (B2). Empty → falls back to the Base URL. |
| **Shared Secret** | Signing tokens between Odoo & FastAPI | Must equal `DMS_SECRET` |

### Health check & final verification

1. `curl http://localhost:8000/api/v1/health` → `{"status":"ok","storage_ok":true,"secret_configured":true}`
2. Open **Documents → Document Drive**, upload a PDF/XLSX/CSV → it appears and previews.
3. Grant another user `read` → they see the file with no Download button; grant `download` → the button appears.
4. Restart the container and the backend, then confirm it still works.

### Backup note

Back up the **Odoo database** and the **storage directory together** — the DB
holds the metadata, the storage directory holds the bytes. In B1 the
`dms-files` volume covers storage; in B2 keep `/var/lib/dms_files` persistent
on the host.

## Features

- Drive UI (grid / list, search, breadcrumbs, folders)
- Previews: PDF, images, DOCX/XLSX (LibreOffice → PDF), CSV/XLSX (HTML table)
- Configurable local storage
- Access control
  - user / role / team / department based permissions
  - Read / Write / Download / Delete / Manage flags
  - folder inheritance, public & private documents
  - owner full access
- Audit trail (uploads, downloads, previews, renames, moves, permission changes, logins)
- Tags, document types, departments, teams, roles, projects, customers, vendors, employees
- Document date, expiry date, status, dynamic custom fields, version history, starring

## Security groups

| Group | Rights |
|---|---|
| DMS / User | Browse & manage own/shared documents |
| DMS / Uploader | Upload (implies User) |
| DMS / Manager | Manage master data, all documents, settings |
| DMS / Auditor | View the audit trail |

## Backend endpoints (FastAPI)

| Method | Path | Token op | Purpose |
|---|---|---|---|
| POST | `/api/v1/files/upload` | `upload` | Store a file (multipart `file` + `folder_path`) |
| GET | `/api/v1/files/content` | `download` | Stream file (Range supported) |
| GET | `/api/v1/files/preview` | `preview` | PDF / image / HTML-table preview |
| GET | `/api/v1/files/thumbnail` | `thumbnail` | Image thumbnail |
| DELETE | `/api/v1/files` | `delete` | Delete physical file |
| POST | `/api/v1/files/move` | `move` | Rename / move physical file |
| GET | `/api/v1/health` | – | Health check |

Tokens are issued by Odoo (`/dms/get_token`) and are short-lived HMAC-signed JWTs.

See `document_management/backend/README.md` for details.
