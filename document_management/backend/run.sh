#!/usr/bin/env bash
# Start the DMS FastAPI backend.
#
#   ./run.sh                      # uses defaults below
#   DMS_SECRET=mysecret ./run.sh  # set the shared secret
#
# Environment variables (all optional):
#   DMS_STORAGE_PATH    where documents are stored (default: ~/dms_files)
#   DMS_SECRET          shared secret, MUST match Odoo Settings -> Shared Secret
#   DMS_LIBREOFFICE_BIN path to LibreOffice binary (default: soffice)
#   DMS_PORT            listen port (default: 8000)

set -euo pipefail
cd "$(dirname "$0")"

export DMS_STORAGE_PATH="${DMS_STORAGE_PATH:-$HOME/dms_files}"
export DMS_SECRET="${DMS_SECRET:-}"
export DMS_LIBREOFFICE_BIN="${DMS_LIBREOFFICE_BIN:-soffice}"
PORT="${DMS_PORT:-8000}"

if [ -z "$DMS_SECRET" ]; then
    echo "ERROR: DMS_SECRET is not set." >&2
    echo "  Set the same secret in Odoo: Settings -> Document Management -> Shared Secret" >&2
    exit 1
fi

if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

mkdir -p "$DMS_STORAGE_PATH"

echo "DMS backend"
echo "  storage : $DMS_STORAGE_PATH"
echo "  secret  : ${#DMS_SECRET} chars"
echo "  url     : http://localhost:$PORT  (health: /api/v1/health)"
echo "Starting..."
exec .venv/bin/uvicorn main:app --host 0.0.0.0 --port "$PORT"
