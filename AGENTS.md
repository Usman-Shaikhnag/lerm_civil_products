# AGENTS.md — LERM Infra practice-addon17

## What this is

Odoo 17 addon monorepo for a civil engineering materials testing lab (LERM).
72 modules: custom (LERM core, material tests, dashboards), OCA community, and third-party.

## Odoo version mix

- **`lerm_civil`** and **`lerm_civil_inv`** are version **13.0.1** — core modules in migration.
- All other modules declare **17.0.x** or a simple version like `1.2`.
- Material testing modules (aac_block, bitumen, soil, etc.) depend on `base`, `sale`, `lerm_civil`.

## Key modules & ownership

| Module | Role |
|--------|------|
| `lerm_civil` (13.0.1) | Core — disciplines, materials, samples, SRFs, ELNs, parameters, portal, security groups |
| `lerm_civil_inv` (13.0.1) | Custom invoicing for lab billing |
| `lerm_civil_dashboard` (17.0) | Owl 2 + Chart.js dashboard |
| `lerm_equipments` | Equipment / calibration tracking |
| `lerm_mobile` | Mobile API endpoints |
| `customer_ageing_dashboard` (17.0) | AR ageing, Owl 2 dashboard with API |
| `report_qr` (17.0) | QR-coded lab report wizard |
| `document_filestore` (17.0) | Document storage via `ftp_storage` |
| `ftp_storage` | SFTP integration (requires `paramiko`) |
| `account_gl_report` (17.0) | General Ledger report, Owl 2 |

## Material testing modules

50+ modules, one per material type. All follow the same pattern: depend on `base`, `sale`, `lerm_civil`; declare version `1.2`; contain `models/`, `views/`, `reports/`, `security/` directories.

| Module | Material |
|--------|----------|
| `aac_block` | AAC Block |
| `admixture` | Admixture |
| `ballast` | Ballast |
| `bitumen` | Bitumen |
| `bitumen_concrete` | Bitumen Concrete |
| `bitumen_mix` | Bitumen Mix |
| `brick` | Brick |
| `brick_brunt_clay` | Burnt Clay Brick |
| `cement_chequerd_tile` | Cement Chequered Tile |
| `cement_opc` | OPC Cement |
| `cement_ppc` | PPC Cement |
| `cement_psc` | PSC Cement |
| `chequerd_tile` | Chequered Tile |
| `coarse_aggregate` | Coarse Aggregate |
| `concrete_beam` | Concrete Beam |
| `concrete_core` | Concrete Core |
| `concrete_cube` | Concrete Cube |
| `concrete_cylinder` | Concrete Cylinder |
| `concrete_mix_design` | Concrete Mix Design |
| `concrete_paving_blocks` | Concrete Paving Blocks |
| `crushed_sand_chemical` | Crushed Sand (Chemical) |
| `crusher_run_macadam` | Crusher Run Macadam |
| `fine_aggregate` | Fine Aggregate |
| `fine_aggrigate_chemical` | Fine Aggregate (Chemical) |
| `fly_ash` | Fly Ash |
| `fly_ash_chemical` | Fly Ash (Chemical) |
| `fst` | Field Static Test |
| `ggbs` | GGBS |
| `gsb` | Granular Sub-Base |
| `gypsum_chemical` | Gypsum (Chemical) |
| `hardent_concrete_chemical` | Hardened Concrete (Chemical) |
| `isat` | Initial Surface Absorption Test |
| `kerb_stone` | Kerb Stone |
| `microsilica` | Microsilica |
| `ndt` | Non-Destructive Testing |
| `paver_block` | Paver Block |
| `pile_integrity` | Pile Integrity |
| `plate_load` | Plate Load Test |
| `rcmt` | Rapid Chloride Migration Test |
| `rcpt` | Rapid Chloride Permeability Test |
| `rock` | Rock |
| `soil` | Soil |
| `soil_resistivity` | Soil Resistivity |
| `ss_tmt_bar` | Stainless Steel TMT Bar |
| `stones` | Stones |
| `tile` | Tile |
| `tmt_bar` | TMT Bar |
| `wbm` | Water Bound Macadam |
| `wmm` | Wet Mix Macadam |
| `wpt` | Water Permeability Test |

## Architecture

- **SRF** (Sample Receipt Form) → **ELN** (Electronic Lab Notebook) → Report → Invoice
- Models use `mail.thread` + `mail.activity.mixin` for Odoo messaging.
- Dashboards use **Owl 2** with **Chart.js**.
- Report rendering: QWeb PDF or py3o/LibreOffice (`report_py3o`).

## Material testing module structure (all 50+ follow the same pattern)

Every module has: `models/`, `views/`, `reports/`, `security/` + `__manifest__.py` (version `1.2`, depends `['base','sale','lerm_civil']`).

### Directory layout

```
material_module/
├── models/
│   ├── __init__.py
│   ├── material_module.py               # Main model inheriting lerm.eln
│   ├── prefill_data_wizard.py           # Transient model for data copying
│   └── report/
│       └── material_ds_report.py        # Abstract models for report rendering
├── views/
│   └── material_module.xml              # Form view + prefill wizard view
├── reports/
│   ├── material_datasheet.xml           # QWeb datasheet template
│   └── material_report.xml              # QWeb report template
└── security/
    └── ir.model.access.csv
```

### Main model (`_name = "mechanical.<material>"`, inherits `lerm.eln`)

Mandatory fields:
- `name` (Char, default = material name), `parameter_id`, `sample_parameters` (Many2many computed), `eln_ref`, `grade`, `eln_state`
- Optionally `size_id` if the material has sizing

Key methods (all modules have these):
- `_compute_visible` — maps each test parameter's `lerm.parameter.master.internal_id` (UUID) to a boolean visibility field
- `_compute_sample_parameters` — filters parameters by technician (respects `kes_admin_access_group` / `lerm_sample_verification` / `lerm_sample_approval` groups)
- `_compute_grade_id`, `_compute_size_id` — derived from `eln_ref`
- `open_eln_page` — writes computed results back to ELN `parameters_result`, then opens the ELN form
- `prefill_data` — copies data from a prior sample's record (same material, different sample)
- `create` override — sets `eln_ref.model_id = record.id`

### Per-test-parameter pattern (7 elements per parameter)

| Element | Type | Purpose |
|---------|------|---------|
| `<param>_name` | `Char(default="Parameter Name")` | Section header |
| `<param>_visible` | `Boolean(compute="_compute_visible")` | Visibility by UUID |
| `<param>_line_ids` | `One2many` to child line model | Raw data entry rows |
| `<computed>_<param>` | `Float(compute=..., store=True)` | Aggregate result (avg, max, etc.) |
| `<computed>_<param>_confirmity` | `Selection(pass/fail/na, compute=...)` | Pass/Fail vs specification (from `lerm.parameter.master.parameter_table` by `grade.id`) |
| `<computed>_<param>_nabl` | `Selection(pass/fail, compute=...)` | NABL Pass/Fail (from `lerm.parameter.master.lab_min_value`/`lab_max_value`) |
| (optional) `requirement_<param>` | `Float` | Specification value display |

### Child line models

One per test parameter. Pattern:
- `_name = "<module>.<test_name>.line"`
- Fields: `parent_id` (Many2one to main model), `sample_no` (Integer, auto-incremented)
- `create()` override auto-increments `sample_no`
- `_reorder_serial_numbers()` helper method

### Notes model

- `_name = "mechanical.<material>.notes"`
- Fields: `parent_id` (Many2one), `sr_no` (Char), `notes` (Char)

### Prefill data wizard

- `_name = "<module>.prefill.data"` (TransientModel)
- Fields: `product_id`, `sample_id` (with domain filter)
- `prefill_data()` method: copies normal fields + One2many lines, filters by visibility

### Report abstract models (`models/report/material_ds_report.py`)

Two classes per module:
- `_name = 'report.<module>.<report_name>'` — full report with QR codes, NABL logic
- `_name = 'report.<module>.<datasheet_name>'` — datasheet (simpler, no QR)

Both implement `_get_report_values(docids, data)` to resolve ELN → model data.

### Form view structure

- `<form create="false">` with `<sheet>`
- Header: material name + "Prefill Data" button
- Info group: `srf_id` (invisible), `sample_id`, `eln_ref`, `grade`, `eln_state`
- `sample_parameters` tree
- Per-parameter sections: `<div invisible="not <param>_visible">` → header + editable tree + result/conformity/nabl table
- `<notebook>` with Notes page
- "Submit" button calling `open_eln_page`

### Security (`ir.model.access.csv`)

Rows for each model (main + child lines + notes + wizard), one per group:
- `lerm_civil.kes_technician_access_group` — technician access
- `lerm_civil.kes_mechanical` — mechanical group access

Model ID format in CSV: `<module>.model_<model_name>` (dots replaced with underscores in model_name).

### UUID mapping (critical)

Every test parameter is identified by a UUID (`lerm.parameter.master.internal_id`). These UUIDs connect `_compute_visible`, `open_eln_page`, conformity/NABL computation, and report templates. Any new module must use UUIDs that match `lerm.parameter.master` records created in `lerm_civil`.

### Registration in lerm_civil

`product.template` (material) has `product_based_calculation` (One2many to `lerm.product.based.calculation`) which links:
- `ir_model` → the material's model (e.g., `mechanical.aac.block`)
- `grade` → `lerm.grade.line`
- `main_report_template` / `datasheet_report_template`

## Key dependencies (external)

- `paramiko` — required by `ftp_storage`
- `py3o.template` / `py3o.formats` + LibreOffice — required by `report_py3o`
- `matplotlib` — used by ELN charting in `lerm_civil`

## Test Server

| Detail | Value |
|--------|-------|
| Host | `173.249.5.45` |
| User | `root` |
| Password | `henrydsa1963` |
| Project path | `/root/lerm_infra` |
| Addons path | `/root/lerm_infra/practice-addon17` |
| Docker container | `lerm_infra-web-1` |
| Docker database | `lerm_infra-db-1` |
| DB container hostname | `db` |
| DB user | `odoo` |
| DB password | `odoo` |

### Git push to server

```bash
sshpass -p 'henrydsa1963' ssh -o StrictHostKeyChecking=no root@173.249.5.45 "cd /root/lerm_infra/practice-addon17 && git pull origin infra_demo"
```

### Upgrade all material testing modules

```bash
sshpass -p 'henrydsa1963' ssh -o StrictHostKeyChecking=no root@173.249.5.45 "docker exec lerm_infra-web-1 odoo -d <database> --addons-path=/mnt/extra-addons --db_host=db --db_user=odoo --db_password=odoo -u aac_block,admixture,ballast,bitumen,bitumen_concrete,bitumen_mix,brick,brick_brunt_clay,cement_chequerd_tile,cement_opc,cement_ppc,cement_psc,chequerd_tile,coarse_aggregate,concrete_beam,concrete_core,concrete_cube,concrete_cylinder,concrete_mix_design,concrete_paving_blocks,crushed_sand_chemical,crusher_run_macadam,fine_aggregate,fine_aggrigate_chemical,fly_ash,fly_ash_chemical,fst,ggbs,gsb,gypsum_chemical,hardent_concrete_chemical,isat,kerb_stone,microsilica,ndt,paver_block,pile_integrity,plate_load,rcmt,rcpt,rock,soil,soil_resistivity,ss_tmt_bar,stones,tile,tmt_bar,wbm,wmm,wpt --stop-after-init"
```

Replace `<database>` with the target database name (e.g., `infra`).

### Upgrade a single module

```bash
docker exec lerm_infra-web-1 odoo -d <database> --addons-path=/mnt/extra-addons --db_host=db --db_user=odoo --db_password=odoo -u <module_name> --stop-after-init
```

## Commands

No build/test/lint tooling is configured. There is no CI, no Makefile, no pre-commit, no testing framework setup.

Standard Odoo workflow (run from an Odoo instance):

```
./odoo-bin -d <dbname> --addons-path=addons,practice-addon17 -u <module_name>
```

## Code conventions

- Module `__manifest__.py` uses legacy dict syntax (no `{'key': 'val'}` for lerm_civil; some use `{'key': 'val'}`, some use Python dict with `# -*- coding: utf-8 -*-`).
- Security groups defined in `lerm_civil/security/security.xml`.
- `ir.model.access.csv` in each module's `security/` directory.
- Some modules contain `import wdb; wdb.set_trace()` debugger breakpoints and commented-out code — legacy.

## What not to do

- Do not add CI, testing, linting, Docker, or pre-commit setup unless explicitly asked — none exists and the repo does not need it.
- Do not modify `lerm_civil` or `lerm_civil_inv` version declarations (they are 13.0.1 during migration).
- Do not remove debugger imports (`wdb`) or commented code — there is too much of it and it is not an active concern.
