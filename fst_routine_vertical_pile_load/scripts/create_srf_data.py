#!/usr/bin/env python3
"""Create the SRF master data required for the Routine Vertical Pile Load Test.

Installs/uses the ``fst_routine_vertical_pile_load`` module, then ensures the
master-data chain needed to raise an SRF sample for
``fst.routine.vertical.load.test``:

    discipline -> group -> material (product.template) -> test method
    -> parameter master (calculation_type='form_based', ir_model=<routine model>)

Existing discipline/group/material/test-method are reused; the parameter is
created only if it does not exist yet. Safe to run multiple times.

Usage:
    python3 create_srf_data.py \
        [--url http://localhost:8090] [--db knack] \
        [--user you@example.com] [--password secret] \
        [--install-module]

Environment overrides: ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD
"""

import argparse
import os
import xmlrpc.client

MODULE_NAME = "fst_routine_vertical_pile_load"
PARAMETER_MODEL = "fst.routine.vertical.load.test"

DISCIPLINE_NAME = "MECHANICAL"
GROUP_NAME = "Soil-Field"
MATERIAL_NAME = "PILE VERT ROUTINE"
TEST_METHOD_NAME = "IS 2911-PART 4"
PARAMETER_NAME = "PILE VERT ROUTINE"
TESTING_DAYS = 30


class Client:
    def __init__(self, url, db, user, password):
        self.url = url.rstrip("/")
        self.db = db
        self.user = user
        self.password = password
        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.uid = common.authenticate(db, user, password, {})
        if not self.uid:
            raise SystemExit("Authentication failed.")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    def call(self, model, method, *args, **kwargs):
        return self.models.execute_kw(
            self.db, self.uid, self.password, model, method, list(args), kwargs
        )

    def search(self, model, domain, **kwargs):
        return self.call(model, "search", domain, **kwargs)

    def search_read(self, model, domain, fields, **kwargs):
        return self.call(model, "search_read", domain, fields, **kwargs)

    def create(self, model, vals):
        return self.call(model, "create", vals)

    def write(self, model, ids, vals):
        return self.call(model, "write", ids, vals)

    def get_or_create(self, model, domain, vals):
        found = self.search(model, domain, limit=1)
        if found:
            return found[0], False
        return self.create(model, vals), True


def ensure_module_installed(client):
    modules = client.search_read(
        "ir.module.module",
        [("name", "=", MODULE_NAME)],
        ["name", "state"],
    )
    if not modules:
        raise SystemExit(f"Module {MODULE_NAME!r} not found in the database.")
    state = modules[0]["state"]
    if state == "installed":
        print(f"Module {MODULE_NAME}: already installed")
        return
    print(f"Module {MODULE_NAME}: installing (state={state})...")
    client.call("ir.module.module", "button_immediate_install", [modules[0]["id"]])
    print(f"Module {MODULE_NAME}: installed")


def ensure_srf_data(client):
    discipline_id, created = client.get_or_create(
        "lerm_civil.discipline",
        [("discipline", "=", DISCIPLINE_NAME)],
        {"discipline": DISCIPLINE_NAME},
    )
    print(f"discipline {DISCIPLINE_NAME!r}: id={discipline_id} created={created}")

    group_id, created = client.get_or_create(
        "lerm_civil.group",
        [("group", "=", GROUP_NAME), ("discipline", "=", discipline_id)],
        {"group": GROUP_NAME, "discipline": discipline_id},
    )
    print(f"group {GROUP_NAME!r}: id={group_id} created={created}")

    material_id, created = client.get_or_create(
        "product.template",
        [("name", "=", MATERIAL_NAME)],
        {
            "name": MATERIAL_NAME,
            "display_name": MATERIAL_NAME,
            "lab_name": MATERIAL_NAME,
            "type": "service",
            "sale_ok": True,
            "purchase_ok": False,
            "list_price": 0.0,
            "is_sample": True,
            "is_product_based_calculation": False,
            "discipline": discipline_id,
            "group": [(6, 0, [group_id])],
        },
    )
    print(f"material {MATERIAL_NAME!r}: id={material_id} created={created}")

    test_method_id, created = client.get_or_create(
        "lerm_civil.test_method",
        [("test_method", "=", TEST_METHOD_NAME), ("product", "=", material_id)],
        {"test_method": TEST_METHOD_NAME, "product": material_id},
    )
    print(f"test method {TEST_METHOD_NAME!r}: id={test_method_id} created={created}")

    ir_models = client.search_read(
        "ir.model", [("model", "=", PARAMETER_MODEL)], ["id", "model"]
    )
    if not ir_models:
        raise SystemExit(
            f"Model {PARAMETER_MODEL!r} not found. Install the module first."
        )
    ir_model_id = ir_models[0]["id"]

    parameter_id, created = client.get_or_create(
        "lerm.parameter.master",
        [
            ("parameter_name", "=", PARAMETER_NAME),
            ("ir_model", "=", ir_model_id),
        ],
        {
            "parameter_name": PARAMETER_NAME,
            "calculation_type": "form_based",
            "ir_model": ir_model_id,
            "test_method": test_method_id,
            "discipline": discipline_id,
            "group": group_id,
            "material": material_id,
            "fetch_by_grade": False,
            "fetch_by_size": False,
            "testing_days": TESTING_DAYS,
        },
    )
    print(f"parameter {PARAMETER_NAME!r}: id={parameter_id} created={created}")

    # Link the parameter to the material and test method so it shows up while
    # raising a sample.
    material_links = client.search_read(
        "product.template", [("id", "=", material_id)], ["parameter_table1"]
    )[0]["parameter_table1"]
    if parameter_id not in material_links:
        client.write(
            "product.template", [material_id], {"parameter_table1": [(4, parameter_id)]}
        )
        print(f"linked parameter to material {material_id}")

    method_links = client.search_read(
        "lerm_civil.test_method", [("id", "=", test_method_id)], ["parameter"]
    )[0]["parameter"]
    if parameter_id not in method_links:
        client.write(
            "lerm_civil.test_method", [test_method_id], {"parameter": [(4, parameter_id)]}
        )
        print(f"linked parameter to test method {test_method_id}")

    return {
        "discipline_id": discipline_id,
        "group_id": group_id,
        "material_id": material_id,
        "test_method_id": test_method_id,
        "parameter_id": parameter_id,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("ODOO_URL", "http://localhost:8090"))
    parser.add_argument("--db", default=os.environ.get("ODOO_DB", "knack"))
    parser.add_argument("--user", default=os.environ.get("ODOO_USER", ""))
    parser.add_argument("--password", default=os.environ.get("ODOO_PASSWORD", ""))
    parser.add_argument("--install-module", action="store_true",
                        help="Install the module if it is not installed yet.")
    args = parser.parse_args()

    if not args.user or not args.password:
        parser.error("--user/--password (or ODOO_USER/ODOO_PASSWORD) are required.")

    client = Client(args.url, args.db, args.user, args.password)
    print(f"Connected: url={args.url} db={args.db} uid={client.uid}")

    if args.install_module:
        ensure_module_installed(client)

    result = ensure_srf_data(client)
    print("\nDone. SRF master data ready:")
    for key, value in result.items():
        print(f"  {key} = {value}")


if __name__ == "__main__":
    main()
