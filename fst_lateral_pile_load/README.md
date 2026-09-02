# FST Lateral Pile Load

Native QWeb report + form module for the Initial Lateral Pile Load Test (`fst.lateral.pile.load.test`).

## SRF integration

The lateral pile load test form is linked to the SRF. When a sample is raised in the SRF for
this test, its **Open Form** button (on the sample and on the ELN parameter row) opens the
`fst.lateral.pile.load.test` form, which then shows **SRF**, **Discipline** and **Group**
populated from the linked sample.

For that to work the module needs a **parameter master** whose `ir_model` points at
`fst.lateral.pile.load.test` and whose `calculation_type` is `form_based`. The following
master-data chain must exist in the database (create it via the UI under
Materials / Parameters, or run the XML-RPC snippet below):

- `lerm_civil.discipline` – e.g. `MECHANICAL`
- `lerm_civil.group` – e.g. `Soil-Field`, under that discipline
- `product.template` (material) – `is_sample = True`, `is_product_based_calculation = False`,
  discipline + group set, `parameter_table1` contains the parameter
- `lerm_civil.test_method` – e.g. `IS 2911-PART 4`
- `lerm.parameter.master` – `PILE LATERL`
  - `calculation_type = 'form_based'`
  - `ir_model = fst.lateral.pile.load.test`
  - `discipline`, `group`, `material`, `test_method` set

## Creating the required data via XML-RPC

Local dev stack in this repo runs Odoo 17 (container `knack17-web-1`) on `http://localhost:8090`,
database `knack`. Example (matches the `All Product` CSV row: `PILE LATERL / Soil-Field / MECHANICAL / IS 2911-PART 4`):

```python
import xmlrpc.client

URL = "http://localhost:8090"
DB, USER, PW = "knack", "usman.shaikhnag@esehat.org", "12345678"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USER, PW, {})
m = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

def sr(model, domain, fields, limit=10):
    return m.execute_kw(DB, uid, PW, model, 'search_read', [domain, fields], {'limit': limit})

def create(model, vals):
    return m.execute_kw(DB, uid, PW, model, 'create', [vals])

def get_or_create(model, domain, vals):
    found = sr(model, domain, ['id'])
    return found[0]['id'] if found else create(model, vals)

# 1. Discipline (reuse existing, e.g. MECHANICAL)
discipline_id = sr('lerm_civil.discipline', [['discipline', '=', 'MECHANICAL']], ['id'])[0]['id']

# 2. Group under that discipline
group_id = get_or_create('lerm_civil.group',
    [['group', '=', 'Soil-Field']],
    {'group': 'Soil-Field', 'discipline': discipline_id})

# 3. Material (product.template)
material_id = get_or_create('product.template',
    [['name', '=', 'PILE LATERL']],
    {'name': 'PILE LATERL', 'lab_name': 'PILE LATERL', 'type': 'service',
     'sale_ok': True, 'purchase_ok': False, 'list_price': 0.0,
     'is_sample': True, 'is_product_based_calculation': False,
     'discipline': discipline_id, 'group': [(6, 0, [group_id])]})

# 4. Test method
tm_id = get_or_create('lerm_civil.test_method',
    [['test_method', '=', 'IS 2911-PART 4']],
    {'test_method': 'IS 2911-PART 4', 'product': material_id, 'parameter': [(6, 0, [])]})

# 5. Parameter master -> fst.lateral.pile.load.test
ir_model_id = sr('ir.model', [['model', '=', 'fst.lateral.pile.load.test']], ['id'])[0]['id']
param_id = get_or_create('lerm.parameter.master',
    [['parameter_name', '=', 'PILE LATERL']],
    {'parameter_name': 'PILE LATERL',
     'calculation_type': 'form_based',
     'ir_model': ir_model_id,
     'test_method': tm_id,
     'discipline': discipline_id,
     'group': group_id,
     'material': material_id,
     'fetch_by_grade': False, 'fetch_by_size': False,
     'testing_days': 30})

# 6. Link parameter into the material so it appears in the SRF Add Sample wizard
m.execute_kw(DB, uid, PW, 'product.template', 'write', [[material_id], {'parameter_table1': [(4, param_id)]}])
m.execute_kw(DB, uid, PW, 'lerm_civil.test_method', 'write', [[tm_id], {'parameter': [(4, param_id)]}])

print("material:", material_id, "| parameter:", param_id, "| group:", group_id, "| test_method:", tm_id)
```

## How the flow works

1. In the SRF, add a sample with material `PILE LATERL` and parameter `PILE LATERL`.
2. On allotment an ELN is created and its `parameters_result[0].calculation_type` is `form_based`,
   so the **Open Form** button is shown on the sample and on the ELN parameter row.
3. Clicking it opens (or creates) the `fst.lateral.pile.load.test` form, passing
   `srf_id / sample_id / parameter_id / eln_ref` in the context.
4. The FST record stores those links and computes **Discipline** and **Group** from the sample;
   its `create()` writes `model_id` back to the ELN / parameter result so later clicks reopen the
   same FST record instead of creating a new one.
