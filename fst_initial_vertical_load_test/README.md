# FST Initial Vertical Load Test

Native QWeb report + form module for the Initial Vertical Pile Load Test
(`fst.initial.vertical.load.test`). It follows the structure of
`fst_lateral_pile_load` and records four dial gauges (A, B, C, D).

## Formulas

The reading table follows the "Welspun Initial Vertical Load test" sheet:

- `Load (MT) = Pressure Gauge Reading (kg/cm²) × Effective Area of Jack / 1000`
- `Cumulative Dial Reading = Dial A + Dial B + Dial C + Dial D`
- `Average Dial Reading = (Cumulative Dial at end of step − Cumulative Dial at start of step) / 4`
- `Cumulative Average Reading = previous cumulative + Average Dial Reading` (running total)

From the settlement summary:

- `Gross Settlement = maximum cumulative settlement`
- `Net Settlement = cumulative settlement after unloading`
- `Rebound = Gross Settlement − Net Settlement`
- `Design Load = Maximum Test Load / 2.5`

## SRF integration

The form is linked to the SRF exactly like `fst_lateral_pile_load`. When a sample is
raised for this test, its **Open Form** button opens the
`fst.initial.vertical.load.test` form, which shows **SRF**, **Discipline** and **Group**
populated from the linked sample.

The module needs a **parameter master** whose `ir_model` points at
`fst.initial.vertical.load.test` and whose `calculation_type` is `form_based`. The
following master-data chain must exist in the database (create it via the UI under
Materials / Parameters, or run the XML-RPC snippet below):

- `lerm_civil.discipline` – e.g. `MECHANICAL`
- `lerm_civil.group` – e.g. `Soil-Field`, under that discipline
- `product.template` (material) – `is_sample = True`, `is_product_based_calculation = False`,
  discipline + group set, `parameter_table1` contains the parameter
- `lerm_civil.test_method` – e.g. `IS 2911-PART 4`
- `lerm.parameter.master` – e.g. `PILE VERT`
  - `calculation_type = 'form_based'`
  - `ir_model = fst.initial.vertical.load.test`
  - `discipline`, `group`, `material`, `test_method` set

## Creating the required data via XML-RPC

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
    [['name', '=', 'PILE VERT']],
    {'name': 'PILE VERT', 'lab_name': 'PILE VERT', 'type': 'service',
     'sale_ok': True, 'purchase_ok': False, 'list_price': 0.0,
     'is_sample': True, 'is_product_based_calculation': False,
     'discipline': discipline_id, 'group': [(6, 0, [group_id])]})

# 4. Test method
tm_id = get_or_create('lerm_civil.test_method',
    [['test_method', '=', 'IS 2911-PART 4']],
    {'test_method': 'IS 2911-PART 4', 'product': material_id, 'parameter': [(6, 0, [])]})

# 5. Parameter master -> fst.initial.vertical.load.test
ir_model_id = sr('ir.model', [['model', '=', 'fst.initial.vertical.load.test']], ['id'])[0]['id']
param_id = get_or_create('lerm.parameter.master',
    [['parameter_name', '=', 'PILE VERT']],
    {'parameter_name': 'PILE VERT',
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
