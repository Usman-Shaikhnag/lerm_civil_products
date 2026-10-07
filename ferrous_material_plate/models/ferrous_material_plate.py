import math
from decimal import Decimal, ROUND_HALF_UP

from odoo import api, fields, models


# ---------------------------------------------------------------------------
# Parameter internal ids
# ---------------------------------------------------------------------------
P_DIA = '15435b52-60a2-42b4-9184-c92d14461d05'
P_WEIGHT = 'e51814b1-3d5c-4911-9f26-2af927bea1d8'
P_LENGTH = '8fece550-65f7-4933-8b32-0e1da1139732'
P_AREA = '32f9cd72-a686-4b50-8cb4-2d0d179c7e82'
P_GAUGE = '9bd3393f-99a9-4f36-a133-3d5ad85a456a'
P_FINAL_LENGTH = '41a5d5d2-023f-4310-b1b7-eeb9c8aa1196'
P_YIELD_LOAD = '3af4d412-20e7-4e46-ac3a-c97db3bb779a'
P_ULT_LOAD = '2b306d73-dcd3-4e3c-9212-a58c43e31fd4'
P_YIELD_STRESS = '1870c58c-563e-4763-a10d-fb80aad45955'
P_UTS = 'ab3315da-f518-4690-9f8b-2433101c918f'
P_ELONGATION = '64dba7ca-5036-4448-9e99-f00ea5dec147'
P_WPM = 'd1dcf292-21b5-4ed8-97f7-2ab7f8b98eea'
P_FRACTURE = '082042cc-b308-4b39-ad5f-b9a0db502f46'
P_BEND = '4c6946e5-4dd0-4464-9d04-ab458ed2f1da'
P_REBEND = 'dfe95b70-98ed-420b-a4bf-2e12490fb410'
P_TS_YS = 'b98af6e1-e2d7-40be-b302-6f7447561c63'

# parameter internal id -> visibility field
VISIBLE_MAP = {
    P_DIA: 'dia_visible',
    P_WEIGHT: 'weight_visible',
    P_LENGTH: 'length_visible',
    P_AREA: 'area_visible',
    P_GAUGE: 'gauge_length_visible',
    P_FINAL_LENGTH: 'final_length_visible',
    P_YIELD_LOAD: 'yeild_load_visible',
    P_ULT_LOAD: 'ultimate_load_visible',
    P_YIELD_STRESS: 'proof_yeild_stress_visible',
    P_UTS: 'ult_tens_strgth_visible',
    P_ELONGATION: 'elongation_visible',
    P_WPM: 'weight_per_meter_visible',
    P_FRACTURE: 'fracture_visible',
    P_BEND: 'bend_visible',
    P_REBEND: 'rebend_visible',
}

# parameters that only need to be flagged as calculated
CALC_ONLY = {P_DIA, P_WEIGHT, P_LENGTH}

# parameter internal id -> (value field on this model, nabl field or None)
RESULT_MAP = {
    P_AREA: ('area', None),
    P_GAUGE: ('gauge_length1', None),
    P_FINAL_LENGTH: ('final_length', None),
    P_YIELD_LOAD: ('yeild_load', None),
    P_ULT_LOAD: ('ultimate_load', None),
    P_YIELD_STRESS: ('proof_yeild_stress', 'yield_nabl'),
    P_UTS: ('ult_tens_strgth', 'uts_nabl'),
    P_ELONGATION: ('elongation', 'elongation_nabl'),
    P_WPM: ('weight_per_meter', 'weight_per_meter_nabl'),
    P_BEND: ('bend_test', None),
    P_REBEND: ('re_bend_test', None),
    P_FRACTURE: ('fracture', None),
}


class FerrousMaterialPlate(models.Model):
    _name = "ferrous.material.plate"
    _inherit = "lerm.eln"
    _rec_name = "name"

    Id_no = fields.Char("ID No")
    name = fields.Char("Name", default="Ferrous Material Plate")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many(
        'lerm.parameter.master', string="Parameters",
        compute="_compute_sample_parameters", store=True)
    eln_ref = fields.Many2one('lerm.eln', string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test", string="Tests")

    grade = fields.Many2one('lerm.grade.line', string="Grade",
                            compute="_compute_grade_id", store=True)
    size = fields.Many2one('lerm.size.line', string="Size",
                           compute="_compute_size_id", store=True)

    # ------------------------------------------------------------------
    # Input / result fields
    # ------------------------------------------------------------------
    dia_visible = fields.Boolean("Dia mm visible", compute="_compute_visible", store=True)
    Dia = fields.Float(string="Dia mm")

    weight_visible = fields.Boolean("Weight, in kg visible", compute="_compute_visible", store=True)
    weight = fields.Float(string="Weight, in kg", digits=(10, 4))

    length_visible = fields.Boolean("Length mm visible", compute="_compute_visible", store=True)
    length = fields.Float(string="Length mm", digits=(16, 4))

    area_visible = fields.Boolean("AREA mm² visible", compute="_compute_visible", store=True)
    area = fields.Float(string="AREA mm²", compute="_compute_area", store=True)

    gauge_length_visible = fields.Boolean("Gauge Length mm visible", compute="_compute_visible", store=True)
    gauge_length1 = fields.Integer(string="Gauge Length mm", compute="_compute_gauge_length", store=True)

    final_length_visible = fields.Boolean("FINAL LENGTH mm visible", compute="_compute_visible", store=True)
    final_length = fields.Float(string="FINAL LENGTH mm")

    yeild_load_visible = fields.Boolean("Yield Load visible", compute="_compute_visible", store=True)
    yeild_load = fields.Float(string="0.2% proof Load / Yield Load, KN")
    requirement_yield = fields.Float(string="Requirement", compute="_compute_requirement_yield", store=True)

    ultimate_load_visible = fields.Boolean("Ultimate Load visible", compute="_compute_visible", store=True)
    ultimate_load = fields.Float(string="Ultimate Load, KN")
    requirement_utl = fields.Float(string="Requirement", compute="_compute_requirement_utl", store=True)

    proof_yeild_stress_visible = fields.Boolean("Proof Stress visible", compute="_compute_visible", store=True)
    proof_yeild_stress = fields.Float("0.2% Proof Stress / Yield Stress N/mm2",
                                      compute="_compute_proof_yeild_stress", store=True, digits=(12, 2))

    ult_tens_strgth_visible = fields.Boolean("UTS visible", compute="_compute_visible", store=True)
    ult_tens_strgth = fields.Float(string="Ultimate Tensile Strength, N/mm2",
                                   compute="_compute_ult_tens_strgth", store=True, digits=(12, 2))

    elongation_visible = fields.Boolean("% Elongation visible", compute="_compute_visible", store=True)
    elongation = fields.Float(string="% Elongation", compute="_compute_elongation_percent",
                              store=True, digits=(12, 2))
    requirement_elongation = fields.Float(string="Requirement",
                                          compute="_compute_requirement_elongation", store=True)

    weight_per_meter_visible = fields.Boolean("Weight Per Meter visible", compute="_compute_visible", store=True)
    weight_per_meter = fields.Float(string="Weight per meter, kg/m", compute="_compute_weight_per_meter",
                                    digits=(10, 2), store=True)
    requirement_weight_per_meter = fields.Float(string="Requirement",
                                                compute="_compute_requirement_weight_per_meter",
                                                digits=(16, 4), store=True)

    fracture_visible = fields.Boolean("Fracture visible", compute="_compute_visible", store=True)
    fracture = fields.Char("Fracture (Within Gauge Length)", default="W.G.L")

    bend_visible = fields.Boolean("Bend Test visible", compute="_compute_visible", store=True)
    bend_test = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non-satisfactory', 'Non-Satisfactory')], "Bend Test")

    rebend_visible = fields.Boolean("Re-bend Test visible", compute="_compute_visible", store=True)
    re_bend_test = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non-satisfactory', 'Non-Satisfactory')], "Re-Bend Test")

    ts_ys_ratio = fields.Float(string="TS/YS Ratio", compute="_compute_ts_ys_ratio", store=True)
    requirement_ts_ys = fields.Float(string="Requirement", compute="_compute_requirement_ts_ys", store=True)

    # ------------------------------------------------------------------
    # Conformity / NABL
    # ------------------------------------------------------------------
    uts_conformity = fields.Selection(
        [('pass', 'Pass'), ('fail', 'Fail')], string="Conformity",
        compute="_compute_uts_conformity", store=True)
    yield_conformity = fields.Selection(
        [('pass', 'Pass'), ('fail', 'Fail')], string="Conformity",
        compute="_compute_yield_conformity", store=True)
    elongation_conformity = fields.Selection(
        [('pass', 'Pass'), ('fail', 'Fail')], string="Conformity",
        compute="_compute_elongation_conformity", store=True)
    ts_ys_conformity = fields.Selection(
        [('pass', 'Pass'), ('fail', 'Fail')], string="Conformity",
        compute="_compute_ts_ys_conformity", store=True)
    weight_per_meter_conformity = fields.Selection(
        [('pass', 'Pass'), ('fail', 'Fail')], string="Conformity",
        compute="_compute_weight_per_meter_conformity", store=True)

    uts_nabl = fields.Selection(
        [('pass', 'Nabl'), ('fail', 'Non-Nabl')], string="NABL",
        compute="_compute_uts_nabl", store=True)
    yield_nabl = fields.Selection(
        [('pass', 'Nabl'), ('fail', 'Non-Nabl')], string="NABL",
        compute="_compute_yield_nabl", store=True)
    elongation_nabl = fields.Selection(
        [('pass', 'Nabl'), ('fail', 'Non-Nabl')], string="NABL",
        compute="_compute_elongation_nabl", store=True)
    ts_ys_nabl = fields.Selection(
        [('pass', 'Nabl'), ('fail', 'Non-Nabl')], string="NABL",
        compute="_compute_ts_ys_nabl", store=True)
    weight_per_meter_nabl = fields.Selection(
        [('pass', 'Nabl'), ('fail', 'Non-Nabl')], string="NABL",
        compute="_compute_weight_per_meter_nabl", store=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @api.model
    def _get_param(self, internal_id):
        return self.env['lerm.parameter.master'].sudo().search(
            [('internal_id', '=', internal_id)], limit=1)

    def _conformity(self, param_id, value, match_field, check_max=True):
        """'pass'/'fail' against the requirement row matching grade/size."""
        self.ensure_one()
        param = self._get_param(param_id)
        mu = param.mu_value
        lower = value - value * mu
        upper = value + value * mu
        for row in param.parameter_table:
            if row[match_field].id == self[match_field].id:
                if lower >= row.req_min and (not check_max or upper <= row.req_max):
                    return 'pass'
                return 'fail'
        return 'fail'

    def _nabl(self, param_id, value, check_max=True):
        """'pass'/'fail' against the lab range of the parameter."""
        self.ensure_one()
        param = self._get_param(param_id)
        mu = param.mu_value
        lower = value - value * mu
        upper = value + value * mu
        if lower >= param.lab_min_value and (not check_max or upper <= param.lab_max_value):
            return 'pass'
        return 'fail'

    def _requirement(self, param_id, match_field):
        """req_min of the row matching grade/size, else 0."""
        self.ensure_one()
        param = self._get_param(param_id)
        for row in param.parameter_table:
            if row[match_field].id == self[match_field].id:
                return row.req_min
        return 0

    # ------------------------------------------------------------------
    # Core computes
    # ------------------------------------------------------------------
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        for record in self:
            record.grade = record.eln_ref.grade_id.id

    @api.depends('eln_ref')
    def _compute_size_id(self):
        for record in self:
            record.size = record.eln_ref.size_id.id

    # NOTE: depends on the current user (parameter-based assignment). A stored
    # compute that depends on env.user is only recomputed when the listed
    # dependencies change, so the stored value reflects whoever triggered it.
    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    def _compute_sample_parameters(self):
        current_user = self.env.user
        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue
            user_results = record.eln_ref.parameters_result.filtered(
                lambda r: r.technician and r.technician.id == current_user.id)
            record.sample_parameters = [(6, 0, user_results.mapped('parameter').ids)]

    @api.depends('eln_ref', 'sample_parameters')
    def _compute_visible(self):
        for record in self:
            active_ids = set(record.sample_parameters.mapped('internal_id'))
            for internal_id, fname in VISIBLE_MAP.items():
                record[fname] = internal_id in active_ids

    def get_all_fields(self):
        record = self.browse(self.ids[0])
        return {name: record[name] for name in record._fields}

    # ------------------------------------------------------------------
    # Submit button
    # ------------------------------------------------------------------
    def open_eln_page(self):
        self.ensure_one()
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == self.env.user)

        for result in technician_results:
            pid = result.parameter.internal_id

            if pid in CALC_ONLY:
                result.calculated = True
                continue

            cfg = RESULT_MAP.get(pid)
            if not cfg:
                continue
            value_attr, nabl_attr = cfg

            field = self._fields[value_attr]
            value = self[value_attr]
            if field.type == 'selection':
                value = dict(field.selection).get(value) or ''
            elif field.type == 'float':
                value = str(round(value, 2))
            else:
                value = str(value)

            result.result_char = value
            result.calculated = True
            if nabl_attr:
                result.nabl_status = 'nabl' if self[nabl_attr] == 'pass' else 'non-nabl'

        return {
            'view_mode': 'form',
            'res_model': "lerm.eln",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.eln_ref.id,
        }

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record.eln_ref.write({'model_id': record.id})
        return records

    # ------------------------------------------------------------------
    # Calculations
    # ------------------------------------------------------------------
    @api.depends('weight', 'length')
    def _compute_weight_per_meter(self):
        for record in self:
            record.weight_per_meter = record.weight / record.length if record.length else 0.0

    @api.depends('weight', 'length')
    def _compute_area(self):
        for record in self:
            if record.length:
                record.area = (record.weight / record.length) / 0.00774
            else:
                record.area = 0.0

    @api.depends('area')
    def _compute_gauge_length(self):
        for record in self:
            gl = math.sqrt(record.area) * 5.65 if record.area > 0 else 0.0
            # round half up
            record.gauge_length1 = int(math.ceil(gl) if gl - int(gl) >= 0.5 else math.floor(gl))

    @api.depends('yeild_load', 'area')
    def _compute_proof_yeild_stress(self):
        for record in self:
            record.proof_yeild_stress = (
                (record.yeild_load / record.area) * 1000 if record.area else 0.0)

    @api.depends('ultimate_load', 'area')
    def _compute_ult_tens_strgth(self):
        for record in self:
            if record.area:
                value = Decimal(record.ultimate_load) / Decimal(record.area) * Decimal('1000')
                record.ult_tens_strgth = float(value.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP))
            else:
                record.ult_tens_strgth = 0.0

    @api.depends('gauge_length1', 'final_length')
    def _compute_elongation_percent(self):
        for record in self:
            if record.gauge_length1:
                record.elongation = (
                    (record.final_length - record.gauge_length1) / record.gauge_length1) * 100
            else:
                record.elongation = 0.0

    @api.depends('ult_tens_strgth', 'proof_yeild_stress')
    def _compute_ts_ys_ratio(self):
        for record in self:
            record.ts_ys_ratio = (
                record.ult_tens_strgth / record.proof_yeild_stress
                if record.proof_yeild_stress else 0.0)

    # ------------------------------------------------------------------
    # Requirements
    # ------------------------------------------------------------------
    @api.depends('eln_ref', 'grade')
    def _compute_requirement_yield(self):
        for record in self:
            record.requirement_yield = record._requirement(P_YIELD_STRESS, 'grade')

    @api.depends('eln_ref', 'grade')
    def _compute_requirement_utl(self):
        for record in self:
            record.requirement_utl = record._requirement(P_UTS, 'grade')

    @api.depends('eln_ref', 'grade')
    def _compute_requirement_elongation(self):
        for record in self:
            record.requirement_elongation = record._requirement(P_ELONGATION, 'grade')

    @api.depends('eln_ref', 'size')
    def _compute_requirement_weight_per_meter(self):
        for record in self:
            record.requirement_weight_per_meter = record._requirement(P_WPM, 'size')

    @api.depends('eln_ref', 'grade')
    def _compute_requirement_ts_ys(self):
        for record in self:
            record.requirement_ts_ys = record._requirement(P_TS_YS, 'grade')

    # ------------------------------------------------------------------
    # Conformity
    # ------------------------------------------------------------------
    @api.depends('proof_yeild_stress', 'eln_ref', 'grade')
    def _compute_yield_conformity(self):
        for record in self:
            record.yield_conformity = record._conformity(
                P_YIELD_STRESS, record.proof_yeild_stress, 'grade')

    @api.depends('ult_tens_strgth', 'eln_ref', 'grade')
    def _compute_uts_conformity(self):
        for record in self:
            record.uts_conformity = record._conformity(
                P_UTS, record.ult_tens_strgth, 'grade')

    @api.depends('elongation', 'eln_ref', 'grade')
    def _compute_elongation_conformity(self):
        for record in self:
            record.elongation_conformity = record._conformity(
                P_ELONGATION, record.elongation, 'grade')

    @api.depends('weight_per_meter', 'eln_ref', 'size')
    def _compute_weight_per_meter_conformity(self):
        for record in self:
            record.weight_per_meter_conformity = record._conformity(
                P_WPM, record.weight_per_meter, 'size')

    @api.depends('ts_ys_ratio', 'eln_ref', 'grade')
    def _compute_ts_ys_conformity(self):
        for record in self:
            # TS/YS only has a minimum requirement
            record.ts_ys_conformity = record._conformity(
                P_TS_YS, record.ts_ys_ratio, 'grade', check_max=False)

    # ------------------------------------------------------------------
    # NABL
    # ------------------------------------------------------------------
    @api.depends('proof_yeild_stress', 'eln_ref', 'grade')
    def _compute_yield_nabl(self):
        for record in self:
            record.yield_nabl = record._nabl(P_YIELD_STRESS, record.proof_yeild_stress)

    @api.depends('ult_tens_strgth', 'eln_ref', 'grade')
    def _compute_uts_nabl(self):
        for record in self:
            record.uts_nabl = record._nabl(P_UTS, record.ult_tens_strgth)

    @api.depends('elongation', 'eln_ref', 'grade')
    def _compute_elongation_nabl(self):
        for record in self:
            record.elongation_nabl = record._nabl(P_ELONGATION, record.elongation)

    @api.depends('weight_per_meter', 'eln_ref', 'size')
    def _compute_weight_per_meter_nabl(self):
        for record in self:
            record.weight_per_meter_nabl = record._nabl(P_WPM, record.weight_per_meter)

    @api.depends('ts_ys_ratio', 'eln_ref', 'grade')
    def _compute_ts_ys_nabl(self):
        for record in self:
            record.ts_ys_nabl = record._nabl(P_TS_YS, record.ts_ys_ratio, check_max=False)


class MechanicalTmtTest(models.Model):
    _name = "mechanical.tmt.test"
    _rec_name = "name"
    name = fields.Char("Name")