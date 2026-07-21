# Plan: Extract Plate Load Test from `fst` into `fst_plate_load`

## Summary

Create `fst_plate_load/` as a new module following the same pattern as `fst_ert`, `fst_borehole`, etc. Move all plate-load-test-related code out of `fst/` into `fst_plate_load/`.

## Dependency Model

```
fst_plate_load ── depends ──> base, lerm_civil, fst
```

Same pattern as `fst_ert`, `fst_borehole`. Depends on `fst` for:
- `fst.view_ert_dashboard` (dashboard card injection via inherited view)
- `fst.fst_group` (security group)

## What Moves to `fst_plate_load`

| Category | What | Source → Target |
|----------|------|-----------------|
| **Models** (3) | `fst.plate.load.test`, `fst.plate.load.test.contents`, `report.fst.plate_load_test_template` | `fst/models/plate_load_test.py` → `fst_plate_load/models/plate_load_test.py` |
| **Views** (2) | form view + tree view for `fst.plate.load.test` | `fst/views/plate_load_test_views.xml` → `fst_plate_load/views/plate_load_test_views.xml` |
| **Security** (2 ACLs) | `access_plate_load_test`, `access_plate_load_test_contents_user` | `fst/security/ir.model.access.csv` → `fst_plate_load/security/ir.model.access.csv` |
| **Report** (1 QWeb template) | `plate_load_test_template` (508 lines) | `fst/reports/plate_load_test_template.xml` → `fst_plate_load/reports/plate_load_test_template.xml` |
| **Controller** (1 class, 2 routes) | `PlateLoadTestController` | `fst/controllers/plate_load_test_controller.py` → `fst_plate_load/controllers/plate_load_test_controller.py` |
| **Dashboard action** | `action_plate_load_test` act_window | Remove from `fst/views/ert.xml`, add to `fst_plate_load/views/plate_load_test_views.xml` |
| **Dashboard card** | Plate Load Test card-box | Remove from `fst/views/ert.xml` kanban, inject via inherited view from `fst_plate_load` |

## Files to Create in `fst_plate_load/`

```
fst_plate_load/
├── __init__.py
│   from . import controllers
│   from . import models
├── __manifest__.py
│   name: 'FST Plate Load Test'
│   version: '1.2'
│   depends: ['base', 'lerm_civil', 'fst']
│   data: [
│       'security/ir.model.access.csv',
│       'views/plate_load_test_views.xml',
│       'reports/plate_load_test_template.xml',
│   ]
├── controllers/
│   ├── __init__.py
│   │   from . import plate_load_test_controller
│   └── plate_load_test_controller.py
│       → copy from fst/controllers/plate_load_test_controller.py (UNCHANGED)
├── models/
│   ├── __init__.py
│   │   from . import plate_load_test
│   └── plate_load_test.py
│       → copy from fst/models/plate_load_test.py (UNCHANGED)
├── views/
│   └── plate_load_test_views.xml
│       → copy from fst/views/plate_load_test_views.xml
│       → ADD: action_plate_load_test act_window (moved from fst/views/ert.xml)
│       → ADD: inherited view injecting card into fst.view_ert_dashboard:
│
│         <record id="plate_load_dashboard_card" model="ir.ui.view">
│           <field name="model">lerm.ert.dashboard</field>
│           <field name="inherit_id" ref="fst.view_ert_dashboard"/>
│           <field name="arch" type="xml">
│             <xpath expr="//div[contains(@class, 'card-box')][last()]" position="after">
│               <div class="card-box" style="...">
│                 <h3 class="title">Plate Load Test</h3>
│                 <a type="action" name="%(action_plate_load_test)d"
│                    style="background:#ffb300; color:#fff;">Records</a>
│               </div>
│             </xpath>
│           </field>
│         </record>
│
├── security/
│   └── ir.model.access.csv
│       id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
│       access_plate_load_test,access_plate_load_test,model_fst_plate_load_test,fst.fst_group,1,1,1,1
│       access_plate_load_test_contents_user,...model_fst_plate_load_test_contents,fst.fst_group,1,1,1,1
└── reports/
    └── plate_load_test_template.xml
        → copy from fst/reports/plate_load_test_template.xml (UNCHANGED)
```

## Modifications to `fst/`

### `fst/__manifest__.py`
- Remove from `data`: `'views/plate_load_test_views.xml'`, `'reports/plate_load_test_template.xml'`

### `fst/models/__init__.py`
- Remove line: `from . import plate_load_test`

### `fst/models/plate_load_test.py`
- DELETE the file

### `fst/views/plate_load_test_views.xml`
- DELETE the file

### `fst/reports/plate_load_test_template.xml`
- DELETE the file

### `fst/views/ert.xml`
- Remove `action_plate_load_test` act_window record
- Remove the Plate Load Test card-box div from the kanban

### `fst/security/ir.model.access.csv`
- Remove 2 plate load ACLs (lines: `access_plate_load_test` and `access_plate_load_test_contents_user`)

### `fst/controllers/plate_load_test_controller.py`
- DELETE the file

### `fst/controllers/__init__.py`
- Remove line: `from . import plate_load_test_controller`

## What Stays Unchanged

- `fst_borehole/`, `fst_lateral_pile_load/`, `routine_vertical_plt/` — no cross-references
- `fst_ert/` — no cross-references
- `plate_load/` (standalone module) — separate implementation, no change (note: pre-existing `report.fst.plate_load_test_template` naming conflict remains)

## Pre-existing Issues (not addressed)

The abstract model `report.fst.plate_load_test_template` is defined in BOTH `fst_plate_load/` and `plate_load/models/plate_load_test_fst.py`. Both query different models (`fst.plate.load.test` vs `lerm.plate.load.test`). This conflict existed before extraction.
