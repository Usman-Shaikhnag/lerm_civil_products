# AGENTS.md — LERM Infra practice-addon17

Odoo 17 addon monorepo for a civil engineering materials testing lab (LERM). 86 dirs including ~72 modules.

## Module types

| Type | Convention | Examples |
|------|-----------|----------|
| Material testing (50+) | `depends: [base, sale, lerm_civil]`, version `1.2` | `aac_block`, `bitumen`, `soil`, `concrete_cube` |
| Core (migrating from v13) | `lerm_civil`(13.0.1), `lerm_civil_inv`(13.0.1) | SRF→ELN→Report→Invoice pipeline |
| FST sub-modules (split from `fst`) | `depends: [base, lerm_civil, fst]`, module prefixed `fst_` | `fst_borehole`, `fst_lateral_pile_load` |

## Split modules caveats

Modules that were extracted from the `fst` module (like `fst_borehole`, `fst_lateral_pile_load`) depend on `fst` and inherit the `fst.fst_group` security group. They own their models, views, and ACLs.

When extracting a new sub-module from `fst`:
- New module depends on `[base, lerm_civil, fst]` (NOT vice versa — no circular dep)
- Move the models + views + ACLs + actions out of `fst`
- `fst` must NOT depend on the sub-module
- Cross-module `@api.depends` paths (e.g., `borehole_lines.soil_borehole_id.graph_image`) will fail at registry build if the target model is in a module loaded later. Simplify to `depends('borehole_lines')` instead.

## Key modules

| Module | Role |
|--------|------|
| `lerm_civil` (13.0.1) | Core — disciplines, materials, samples, SRFs, ELNs, parameters, portal, security groups |
| `lerm_civil_inv` (13.0.1) | Custom invoicing |
| `fst` | Field Static Tests — ERT dashboard, pile/plate/soil tests, security group `fst.fst_group` |
| `fst_borehole` | Borehole logging (SPT, grain size, direct shear) — split from `fst` |
| `fst_lateral_pile_load` | Initial lateral pile load test — split from `fst` |
| `plate_load` | Plate load test — split from `fst` |

## Model naming

Material tests: `_name = "mechanical.<material>"` inheriting `lerm.eln`.
FST models: `_name = "soil.borehole"`, `"soil.borehole.nvalue"`, `"spt.n.value"`, `"pullout.pile.load.test.parent"`, etc. — no standard prefix.
Each `fst_submodule` keeps the same `_name` values that were in the original `fst/borehole.py`.

## Architecture

- SRF → ELN → Report → Invoice
- Dashboards: Owl 2 + Chart.js (`lerm_civil_dashboard`, `customer_ageing_dashboard`)
- Reports: QWeb PDF or py3o/LibreOffice (`report_py3o`)
- Matplotlib used extensively for graphs (borehole logs, shear, grain size, pile load curves)
- Security groups in `lerm_civil/security/security.xml`; `fst_group` in `fst/security/security.xml`
- UUID-based parameter mapping: `lerm.parameter.master.internal_id` connects compute visibility, conformity, NABL, and reports

## Per-test-parameter pattern (material modules)

Each parameter has 7 elements: `_name`, `_visible` (Boolean, computed by UUID), `_line_ids` (One2many), computed result, conformity (pass/fail/na vs spec), NABL pass/fail, optional requirement.

## Child line model pattern (material modules)

- `_name = "<module>.<test_name>.line"`
- `parent_id` (Many2one), `sample_no` (Integer, auto-incremented in `create()` override)
- `_reorder_serial_numbers()` helper

## FST Dashboard kanban cards

`fst/views/ert.xml` defines `view_ert_dashboard` — a kanban with grid of `card-box` divs. Sub-modules inject cards via inherited views (e.g., `fst_borehole` injects the Soil card). Installing/uninstalling the sub-module toggles the card visibility.

## Server & deployment

Local Docker: `lerm_infra-web-1` container, `lerm_infra-db-1` database.
Remote: `root@173.249.5.45` (password: `henrydsa1963`), project at `/root/lerm_infra/practice-addon17`.

```bash
# Upgrade single module
docker exec lerm_infra-web-1 odoo -d infra --addons-path=/mnt/extra-addons --db_host=db --db_user=odoo --db_password=odoo -u <module> --stop-after-init

# Upgrade two modules (order matters if one depends on the other)
docker exec lerm_infra-web-1 odoo -d infra --addons-path=/mnt/extra-addons --db_host=db --db_user=odoo --db_password=odoo -u mod1,mod2 --stop-after-init

# Restart after upgrade
docker restart lerm_infra-web-1

# Push local changes to server
git push origin infra_demo && sshpass -p 'henrydsa1963' ssh root@173.249.5.45 "cd /root/lerm_infra/practice-addon17 && git pull origin infra_demo"
```

## Conventions & constraints

- Use legacy dict syntax in `__manifest__.py` (not `{}` on some modules, `{}` on others — match the file)
- `__manifest__.py` may include `# -*- coding: utf-8 -*-` (do not remove)
- Security groups: `lerm_civil.kes_technician_access_group`, `lerm_civil.kes_mechanical`, `fst.fst_group`
- ACL model IDs in CSV: `<module>.model_<model_name>` (dots → underscores)
- Do NOT modify `lerm_civil` or `lerm_civil_inv` version (stays 13.0.1 during migration)
- Do NOT add CI, linting, testing, Docker, or pre-commit — none exists, not needed
- Do NOT remove `import wdb; wdb.set_trace()` or commented-out code — legacy, not an active concern
- No Makefile, no test framework, no typechecker, no codegen
