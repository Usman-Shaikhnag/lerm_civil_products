#!/bin/bash

# Configuration
ADDONS_DIR="/home/usman/Dev/odoo/demo17/demo17-practice-addon17"
ODOO_BIN_PATH="/home/usman/Dev/odoo/demo17/odoo/odoo-bin" # Adjust this to your actual odoo-bin path
CONFIG_FILE="/home/usman/Dev/odoo/demo17/odoo.conf"       # Adjust this to your odoo.conf path
DB_NAME="demo1"                              # Replace with your actual database name

# Find all directories containing a __manifest__.py file, extract the folder name, and join with commas
MODULES=$(find "$ADDONS_DIR" -mindepth 1 -maxdepth 2 -name "__manifest__.py" -printf "%h\n" | awk -F/ '{print $NF}' | paste -sd "," -)

if [ -z "$MODULES" ]; then
    echo "❌ No Odoo modules found in $ADDONS_DIR"
    exit 1
fi

echo "✅ Found the following modules to upgrade:"
echo "$MODULES"
echo "--------------------------------------------------------"

if [ "$1" == "--run" ]; then
    if [ -z "$DB_NAME" ]; then
        echo "⚠️  Please set your DB_NAME in this script before running with --run"
        exit 1
    fi
    echo "🚀 Starting Odoo to upgrade modules..."
    python3 "$ODOO_BIN_PATH" -c "$CONFIG_FILE" -d "$DB_NAME" -u "$MODULES" --stop-after-init
else
    echo "💡 To execute the upgrade automatically, edit this script to set your ODOO_BIN_PATH, CONFIG_FILE, and DB_NAME, then run:"
    echo "   ./upgrade_all.sh --run"
    echo ""
    echo "Or run manually using:"
    echo "python3 /path/to/odoo-bin -c /path/to/odoo.conf -d <your_db_name> -u $MODULES"
fi
