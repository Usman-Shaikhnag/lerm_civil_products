# AGENTS.md

## Repo layout

Monorepo of **91 Odoo 17 addons** for a construction-materials testing lab (LERM). Each top-level directory is one Odoo module with `__manifest__.py`. There is no shared Python package, root manifest, CI, or test runner.

The working branch is `knack17_lerm`.

## Architecture

- `lerm_civil` — the core LERM app (sample/SRF/ELN registers, material & parameter masters, datasheets). Nearly every other module depends on it.
- `lerm_civil_inv` — invoicing (depends on `lerm_civil`, `base_accounting_kit`, `l10n_in`, etc.).
- Material-testing modules (`cement_opc`, `concrete_cube`, `soil`, `brick`, `fly_ash`, …) are near-identical thin wrappers: `depends: ['base','sale','lerm_civil']`, with `models/`, `views/`, `reports/`, `security/`. If you edit one, mirror it across the others.
- `documents` — Odoo's stock Documents app (OEEL-1), heavily extended; recently wired so SRF/Sample/ELN uploads land in DMS. It is mostly upstream Odoo code.
- `document_management` — custom DMS: OWL UI + **FastAPI microservice** in `document_management/backend/`. Run separately via its bundled `docker-compose.yml` / `run.sh`; see `document_management/README.md`. Also read `document_management/backend/README.md`.
- `ftp_storage` — depends on `lerm_civil` + `document_management`; requires `paramiko`.
- `fst` and `report_py3o` use the OCA Py3o report engine (needs LibreOffice). The material modules instead use **native QWeb reports** whose templates call `lerm_civil.mechanical_data_sheet_header` (see `reports/*_datasheet.xml` in any material module).
- `lerm_mobile` — JSON REST controllers (`/mobile/...`) for a mobile app; `type='json'`, `auth='none'`, `csrf=False`.

## Commands

- `./upgrade_all.sh [--run]` collects every module name and runs `odoo-bin -u <all> --stop-after-init` against DB `demo1`. Paths are hardcoded to a **Linux** dev box (`/home/usman/Dev/odoo/demo17/...`); edit them before running. This is the intended way to install/upgrade — there is no local dev stack in this repo.
- No tests to run in-repo; no lint/format/typecheck config exists. Keep edits style-consistent with the neighboring files.

## Gotchas

- **`*.pyc` / `__pycache__` files are already tracked in git** (83 of them) and show up as modified in every `git status`. Never stage or commit them — only stage real source changes.
- Manifests are inconsistent: some use Odoo 13-era `version: '13.0.1'` (e.g. `lerm_civil`, `lerm_civil_inv`) and one-line dict formatting on Odoo 17. Don't "fix" these — match the style of the module you're editing.
- `requirements.txt` pins `odoo==17.0.post20250725` and very old deps (Werkzeug 2.0.2); don't bump versions.
- Commit messages in this repo are terse single-line summaries (e.g. `ADD`, `SAVE`, descriptive one-liners).

## Production server (deployment)

Production is an Odoo 17 Docker stack. Access is via SSH as root.

> **SECURITY WARNING**: credentials below are **live secrets** committed in this repo (AGENTS.md is git-tracked and pushed to GitHub). Rotate them immediately if this repo ever becomes public or is shared outside the team.

- **Host**: `knack17_0426Esehat` — configured in `~/.ssh/config`:
  ```ini
  Host knack17_0426Esehat
      HostName 89.117.52.222
      User root
      # password: 0426Esehat
  ```
  Server runs Docker with three services:
  - `odoo` (odoo:17) → `:8069`, addons bind-mounted from the host volume at `/var/lib/docker/volumes/prod-data/_data` (a git checkout of this repo, branch `knack17_lerm`).
  - `db` (postgres:15) — the single production database is `demo_db` (psql: `docker exec db psql -U odoo -d demo_db`).
  - `document_management-dms-backend-1` (FastAPI) → `:8000` — the DMS backend for the `document_management` module.
- The checkout may have **uncommitted production-specific edits** (e.g. `door/models/door.py` internal_ids that only exist in this DB). Never reset/checkout blindly — reconcile those changes first.
- Deploy = update the checkout, install/upgrade changed modules, restart:
  ```bash
  ssh knack17_0426Esehat
  cd /var/lib/docker/volumes/prod-data/_data && git pull
  docker exec odoo odoo -d demo_db -u <changed_modules> --stop-after-init \
    --db_host=db --db_user=odoo --db_password=odoo
  docker restart odoo
  ```
- DMS backend health: `curl http://localhost:8000/api/v1/health`. Config lives in `ir_config_parameter` (`document_management.*`); the Odoo container is attached to the `document_management_default` network so it reaches the backend via `http://dms-backend:8000`.
- **After changing `ir_config_parameter` via raw SQL, `docker restart odoo`** — the running Odoo process caches config params in memory and will keep serving the stale value (e.g. DMS previews kept failing after `fastapi_url` was updated directly in Postgres until Odoo was restarted).
- **DMS uploads fail with "Access Denied by ACLs ... model: dms.file"** for any user who is not in a DMS group (`group_dms_user`/`group_dms_uploader`/`group_dms_manager`). Assign the DMS/User (or higher) group via Settings → Users; the user must re-login for it to take effect.
- **DMS previews/downloads fail with "sent an invalid response" when accessed via `https://knack17.lerm.in`** — the frontend builds file URLs from `document_management.fastapi_url`, which must be HTTPS and reachable from the browser. It is set to `https://knack17.lerm.in/dms-files`, proxied by nginx (`/etc/nginx/sites-available/knack17`, `location /dms-files/` → `http://127.0.0.1:8000/`). Do not point it at plain `http://89.117.52.222:8000` — the browser upgrades to HTTPS and gets an invalid response. `fastapi_server_url` stays `http://dms-backend:8000` for Odoo-side calls.
- `upgrade_all.sh` targets a *Linux dev box* (DB `demo1`, paths `/home/usman/Dev/...`) — it is **not** the production deploy path; use the docker steps above.

## Sources of truth

- `upgrade_all.sh` — module list + install command (the only executable source).
- `document_management/README.md` + `backend/README.md` — DMS setup, URL rules (Base URL vs Server URL), health check.
- Read a material module (e.g. `cement_opc`) as the canonical pattern before adding a new one.
