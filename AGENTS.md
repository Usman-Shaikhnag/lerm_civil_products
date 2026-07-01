# AGENTS.md — practice-addon17

## What this is

Odoo v13 addons (with some v17 modules) for a civil engineering materials testing lab (LERM). Monorepo of ~60+ addons: one core (`lerm_civil`), one invoicing hub (`lerm_civil_inv`), ~50 material-specific test addons, and a handful of utility/OCA modules.

## Key addons & ownership

| Addon | Role | Depends on |
|---|---|---|
| `lerm_civil` | **Core hub** — ELN, SRF, samples, parameters, datasheets, reports, portal, instruments | `base, contacts, product, hr, lerm_civil_inv, mail, ...` |
| `lerm_civil_inv` | Invoicing (sale, account, l10n_in, base_account_budget) | `sale, account, l10n_in, base_account_budget, ...` |
| `lerm_civil_dashboard` | Dashboard views | `lerm_civil` |
| `lerm_equipments` | Equipment/instrument management | — |
| `lerm_mobile` | Mobile interface | `lerm_civil` |
| `fst` | Field soil testing (ERT, borehole, pile load, plate load) | `lerm_civil, soil_resistivity` |
| `report_py3o` | LibreOffice-based reporting engine (v17, OCA) | `web` + `py3o.template`, `py3o.formats`, `libreoffice` |
| `soil/`, `bitumen/`, `concrete_cube/`, `brick/`, … | **Standard material test addons** — `_name = "mechanical.*"`, `_inherit = "lerm.eln"`, full UUID+conformity pattern | `base, lerm_civil` (some also `sale`) |
| `ndt/` | **NDT suite** — 10 sub-models (`ndt.rebound.hammer`, `ndt.upv`, …), NOT `mechanical.*` | `base, sale, lerm_civil` |
| `pile_integrity/` | Pile integrity testing — `_name = "pile.integrity"`, no conformity/NABL | `base, lerm_civil` |
| `isat/` | Initial Surface Absorption — `_name = "mech.isat"` (not `mechanical.`) | `base, sale, lerm_civil` |
| `ss_tmt_bar/` | SS/TMT steel bar — `mechanical.*` but with extra wizard for bar-line entry | `base, lerm_civil` |
| `kg_hide_menu`, `custom_login`, `keyboard_nav`, `query_deluxe`, `web_window_title`, `ftp_storage`, `document_filestore`, `report_qr` | **Utility/OCA modules** — no `lerm.eln` inheritance, v17 era | varies |

## Workflow conventions

- **All material addons** `_inherit = "lerm.eln"`. Most use `_name = "mechanical.<material>"` (standard pattern), but `ndt/` uses `ndt.*`, `pile_integrity/` uses `pile.integrity`, and `isat/` uses `mech.isat`. Standard addons share an identical skeleton: main model + `prefill_data_wizard` + report model.
- Conformity/NABL status is computed via **hardcoded UUID strings** looked up in `lerm.parameter.master`. These UUIDs are environment-sensitive — changing them breaks computations silently.
- ELN lifecycle states: `Allotted → In-Test → In-Check → Approved → Rejected → Cancelled`.
- Test graphs are generated with matplotlib and stored as `fields.Binary` (base64 PNG).
- Many computed methods use `sudo()` for data access.

## Product-based calculation pattern

Product-to-test-model mapping is configured in `lerm_civil` via `product.template`:
- `is_product_based_calculation` (Boolean) marks products that use material addon workflow.
- `product_based_calculation` (One2many to `lerm.product.based.calculation`) maps product + grade → `ir.model` (e.g., `mechanical.soil`) + report templates.
- `grade_table` / `size_table` hold per-product grade/size options.

**Visibility chain:** Product → SRF → ELN → `eln_ref.parameters_result` → `_compute_sample_parameters` reads assigned params (admins see all) → `_compute_visible` toggles `*_visible` Booleans by matching `sample_parameters.internal_id` against hardcoded UUIDs → form XML uses `attrs="{'invisible': [('*_visible', '=', False)]}"`.

- The `grade` field on each material model is computed from `eln_ref.grade_id` and stored.
- Conformity/NABL computation queries `lerm.parameter.master` by UUID, then filters `parameter_table` by `grade.id` to get `req_min`/`req_max`.
- Many material addons override `read()` to call `_compute_sample_parameters()` then `_compute_visible()` on every form load.

## Open form button pattern (Prefill → Submit)

Each material addon form has two `type="object"` buttons:

**Prefill Data** — calls `prefill_data()` on the main model, which opens a TransientModel wizard (`<material>.prefill.data`). Wizard has `product_id` and `sample_id` (domain-filtered to same product, excludes current sample). Its `prefill_data()` method copies simple + One2many fields from a previous test record via `copy_data()`, **skipping sections that are not visible** on the current form. Closes with `ir.actions.act_window_close`.

**Submit** — calls `open_eln_page()` which:
1. Filters `eln_ref.parameters_result` by current technician.
2. For each param, matches by `parameter.internal_id` UUID, writes computed result to `result_char` and `nabl_status`.
3. Returns `ir.actions.act_window` opening `lerm.eln` form at `res_id=self.eln_ref.id`.

**Reverse direction:** ELN form has an "Open Test Form" button calling `open_product_based_form()` in `lerm_civil/models/eln.py`. It looks up `product_based_calculation` matching product + grade, finds the `ir_model.model` string, and opens the material addon form (creating a new record or opening existing via `self.model_id`). On `create()`, the material addon writes `model_id` back to the ELN record.

## Version inconsistency

- Core modules (`lerm_civil`, `lerm_civil_inv`): `13.0.1` (Odoo 13 era).
- Material addons: `1.2`.
- Utility/OCA modules (`report_py3o`, `web_responsive`, etc.): `17.0.*`.

## Known issues to watch

- **Copy-paste manifests**: Many material addons have irrelevant/holdover summaries like `"Sales internal machinery"`. Don't trust manifest prose — look at actual code.
- **`brick` addon** has `_compute_sample_parameters` defined twice — second definition silently overrides the first.
- **Leftover debug code**: `import wdb; wdb.set_trace()` appears commented in many files.
- **No tests** for `lerm_civil`, `lerm_civil_inv`, or any material test addon. Tests exist only in utility modules (`documents/`, `database_cleanup/`, `report_py3o/`, `web_responsive/`).
- **Category casing**: `'Lerm Civil'` vs `'LERM CIVIL'` differs across addons.

## Commands

No project-level build/test/lint tooling exists (no Makefile, tox, CI, pre-commit, or ruff config). The standard Odoo server addons-path pattern applies:

```
./odoo/odoo-bin -d <db> --addons-path=addons,.../practice-addon17
```

### Update modules on production server

```bash
sshpass -p '162026EML' ssh -o StrictHostKeyChecking=no root@13.140.181.34 "docker exec geonyms odoo -d geonyms --db_host db --db_user odoo --db_password odoo -u <comma-separated-modules> --stop-after-init"
```

### Pull latest code on production server

```bash
sshpass -p '162026EML' ssh -o StrictHostKeyChecking=no root@13.140.181.34 "docker exec geonyms bash -c 'cd /mnt/extra-addons && git pull origin lerm_geonyms'"
```

## Configuration

Addons use `whool` build system (no `setup.py` / `setup.cfg`). `.gitignore` ignores `*.pyc`, `__pycache__/`, and `.DS_Store`.

## Production Server

| Detail | Value |
|---|---|
| Server IP | `13.140.181.34` |
| User | `root` |
| Password | `162026EML` |
| Docker container | `geonyms` (Odoo 17.0) |
| DB container | `db` (PostgreSQL 15) |
| Database name | `geonyms` |
| DB user/password | `odoo` / `odoo` |
| DB host | `db` (linked container) |
| Addons path | `/mnt/extra-addons` |
| Odoo config | `/etc/odoo/odoo.conf` |
| Odoo data dir | `/var/lib/odoo` |
| Web port | `8069` |
| Git remote | `https://github.com/Usman-Shaikhnag/lerm_civil_products.git` |
| Git branch | `lerm_geonyms` |

### Update all installed modules (on server)

```bash
docker exec geonyms odoo -d geonyms --db_host db --db_user odoo --db_password odoo -u <comma-separated-modules> --stop-after-init
```

### Known server issues

- `ftp_storage` XML views can cause `relaxng.assert_` errors — check `/mnt/extra-addons/ftp_storage/views/*.xml` if updates fail.
- Missing unmaintained modules (`Cover_Block`, `door`, `gypsum_plaster_board`, `ht_strand`, `pt_grout`, `shuttering_plywood`, `wood`) produce non-blocking warnings on startup.
- LibreOffice not installed on server — `report_py3o` reports will warn but not crash.
