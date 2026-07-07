from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math



class Microsilica(models.Model):
    _name = "mechanical.microsilica"
    _inherit = "lerm.eln"
    _description = 'mechanical.microsilica'
    _rec_name = "name"


    name = fields.Char("Name",default="Microsilica")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)


    # 1 — Fineness by Wet Sieving (45 Micron)

    wet_sieving_name = fields.Char("Name", default="Fineness of Silica Fume by Wet Sieving (45 Micron)")
    wet_sieving_visible = fields.Boolean("Wet Sieving Visible", compute="_compute_visible")

    sample_weight_ws = fields.Float(string="Sample Weight (Ws) (g)", default=100.0)
    sieve_size_ws = fields.Char(string="Sieve Size Used", default="45 Micron")

    wet_sieving_line_ids = fields.One2many(
        'microsilica.wet.sieving.line',
        'parent_id',
        string="Wet Sieving Trials"
    )

    avg_percent_passing = fields.Float(
        string="Average % Material Passing",
        compute="_compute_avg_percent_passing",
        store=True
    )

    @api.depends('wet_sieving_line_ids.percent_passing')
    def _compute_avg_percent_passing(self):
        for rec in self:
            vals = rec.wet_sieving_line_ids.mapped('percent_passing')
            if vals:
                rec.avg_percent_passing = sum(vals) / len(vals)
            else:
                rec.avg_percent_passing = 0.0

    wet_sieving_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail', compute="_compute_wet_sieving_conformity")

    wet_sieving_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_wet_sieving_nabl", store=True)

    @api.depends('avg_percent_passing', 'eln_ref')
    def _compute_wet_sieving_conformity(self):
        for record in self:
            record.wet_sieving_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', '52147fgtre-5f8c-44a2-984b-6ad2a17d250c')])
            materials = line.parameter_table
            for material in materials:
                req_min = material.req_min
                req_max = material.req_max
                mu_value = line.mu_value
                lower = record.avg_percent_passing - record.avg_percent_passing * mu_value
                upper = record.avg_percent_passing + record.avg_percent_passing * mu_value
                if lower >= req_min and upper <= req_max:
                    record.wet_sieving_conformity = 'pass'
                    break
                else:
                    record.wet_sieving_conformity = 'fail'

    @api.depends('avg_percent_passing', 'eln_ref')
    def _compute_wet_sieving_nabl(self):
        for record in self:
            record.wet_sieving_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', '52147fgtre-5f8c-44a2-984b-6ad2a17d250c')])
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            lower = record.avg_percent_passing - record.avg_percent_passing * mu_value
            upper = record.avg_percent_passing + record.avg_percent_passing * mu_value
            if lower >= lab_min and upper <= lab_max:
                record.wet_sieving_nabl = 'pass'
            else:
                record.wet_sieving_nabl = 'fail'


    # 2 — Compressive Strength of Micro Silica

    compressive_strength_name = fields.Char("Name", default="Compressive Strength of Micro Silica")
    compressive_strength_visible = fields.Boolean("Compressive Strength Visible", compute="_compute_visible")

    wt_of_sand_cs = fields.Float(string="Weight of Sand (g)")
    wt_of_cement_silica_cs = fields.Float(string="Weight of Cement + Silica (g)")
    std_consistency_p = fields.Float(string="Standard Consistency P (%)")
    water_weight_cs = fields.Float(string="Weight of Water (g)", compute="_compute_water_weight_cs", store=True)

    @api.depends('std_consistency_p')
    def _compute_water_weight_cs(self):
        for rec in self:
            if rec.std_consistency_p:
                rec.water_weight_cs = rec.std_consistency_p / 4.0 + 3.0
            else:
                rec.water_weight_cs = 0.0

    temp_cs = fields.Float("Temperature °c")
    humidity_cs = fields.Float("Humidity %")
    start_date_cs = fields.Date("Start Date")
    end_date_cs = fields.Date("End Date")

    comp_str_line_ids = fields.One2many(
        'microsilica.compressive.strength.line',
        'parent_id',
        string="Compressive Strength Samples"
    )

    avg_7_strength = fields.Float("Avg Compressive Strength 7 Days (N/mm²)", compute="_compute_avg_strength_by_age", store=True)
    avg_14_strength = fields.Float("Avg Compressive Strength 14 Days (N/mm²)", compute="_compute_avg_strength_by_age", store=True)
    avg_28_strength = fields.Float("Avg Compressive Strength 28 Days (N/mm²)", compute="_compute_avg_strength_by_age", store=True)

    @api.depends('comp_str_line_ids.comp_strength', 'comp_str_line_ids.age_days')
    def _compute_avg_strength_by_age(self):
        for rec in self:
            rec.avg_7_strength = 0.0
            rec.avg_14_strength = 0.0
            rec.avg_28_strength = 0.0
            for age, field in [(7, 'avg_7_strength'), (14, 'avg_14_strength'), (28, 'avg_28_strength')]:
                lines = rec.comp_str_line_ids.filtered(lambda l: l.age_days == str(age))
                vals = lines.mapped('comp_strength')
                if vals:
                    setattr(rec, field, sum(vals) / len(vals))

    compressive_strength_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail', compute="_compute_compressive_strength_conformity")

    compressive_strength_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_compressive_strength_nabl", store=True)

    @api.depends('avg_28_strength', 'eln_ref')
    def _compute_compressive_strength_conformity(self):
        for record in self:
            record.compressive_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', '658798cvfd-889b-477c-a355-0476f6bcd0d7')])
            materials = line.parameter_table
            for material in materials:
                req_min = material.req_min
                req_max = material.req_max
                mu_value = line.mu_value
                lower = record.avg_28_strength - record.avg_28_strength * mu_value
                upper = record.avg_28_strength + record.avg_28_strength * mu_value
                if lower >= req_min and upper <= req_max:
                    record.compressive_strength_conformity = 'pass'
                    break
                else:
                    record.compressive_strength_conformity = 'fail'

    @api.depends('avg_28_strength', 'eln_ref')
    def _compute_compressive_strength_nabl(self):
        for record in self:
            record.compressive_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', '658798cvfd-889b-477c-a355-0476f6bcd0d7')])
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            lower = record.avg_28_strength - record.avg_28_strength * mu_value
            upper = record.avg_28_strength + record.avg_28_strength * mu_value
            if lower >= lab_min and upper <= lab_max:
                record.compressive_strength_nabl = 'pass'
            else:
                record.compressive_strength_nabl = 'fail'


    # 3 — Specific Gravity

    specific_gravity_name = fields.Char("Name", default="Specific Gravity of Micro Silica")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible", compute="_compute_visible")

    specific_gravity_tables = fields.One2many(
        'microsilica.specific.gravity.line',
        'parent_id',
        string="Specific Gravity"
    )

    specific_gravity_avrg = fields.Float(string="Average", compute="_compute_specific_gravity_avrg")

    specific_gravity_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail', compute="_compute_specific_gravity_conformity")

    specific_gravity_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_specific_gravity_nabl", store=True)

    @api.depends('specific_gravity_tables.spe_gravt_microsilica')
    def _compute_specific_gravity_avrg(self):
        for record in self:
            vals = record.specific_gravity_tables.mapped('spe_gravt_microsilica')
            if vals:
                record.specific_gravity_avrg = sum(vals) / len(vals)
            else:
                record.specific_gravity_avrg = 0.0

    @api.depends('specific_gravity_avrg', 'eln_ref')
    def _compute_specific_gravity_conformity(self):
        for record in self:
            record.specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', '658fgtrcd-80ef-4de0-96ba-a279f27b9ede')])
            materials = line.parameter_table
            for material in materials:
                req_min = material.req_min
                req_max = material.req_max
                mu_value = line.mu_value
                lower = record.specific_gravity_avrg - record.specific_gravity_avrg * mu_value
                upper = record.specific_gravity_avrg + record.specific_gravity_avrg * mu_value
                if lower >= req_min and upper <= req_max:
                    record.specific_gravity_conformity = 'pass'
                    break
                else:
                    record.specific_gravity_conformity = 'fail'

    @api.depends('specific_gravity_avrg', 'eln_ref')
    def _compute_specific_gravity_nabl(self):
        for record in self:
            record.specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', '658fgtrcd-80ef-4de0-96ba-a279f27b9ede')])
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            lower = record.specific_gravity_avrg - record.specific_gravity_avrg * mu_value
            upper = record.specific_gravity_avrg + record.specific_gravity_avrg * mu_value
            if lower >= lab_min and upper <= lab_max:
                record.specific_gravity_nabl = 'pass'
            else:
                record.specific_gravity_nabl = 'fail'


    # 4 — Accelerated Pozzolanic Activity Index (7 days)

    pozzolanic_name = fields.Char("Name", default="Accelerated pozzolanic activity index with portland cement")
    pozzolanic_visible = fields.Boolean("Pozzolanic Visible", compute="_compute_visible")

    temp_pozzolanic = fields.Float("Temperature °c")
    humidity_pozzolanic = fields.Float("Humidity %")
    start_date_pozzolanic = fields.Date("Start Date")
    end_date_pozzolanic = fields.Date("End Date")

    # Test Mixture
    tm_high_range_water = fields.Integer(string="High Range water reducer (g)")
    tm_wt_microsilica = fields.Integer(string="Weight of Microsilica (g)", default=50)
    tm_wt_cement = fields.Integer(string="Weight of Cement (g)", default=450)
    tm_wt_sand_grade1 = fields.Float(string="Weight of Standard Sand (g) Grade-I", default=458.33)
    tm_wt_sand_grade2 = fields.Float(string="Weight of Standard Sand (g) Grade-II", default=458.33)
    tm_wt_sand_grade3 = fields.Float(string="Weight of Standard Sand (g) Grade-III", default=458.33)
    tm_quantity_water = fields.Integer(string="Quantity of Water (g)")

    tm_measured_val1 = fields.Float(string="Measured Values")
    tm_measured_val2 = fields.Float(string="Measured Values")
    tm_measured_val3 = fields.Float(string="Measured Values")
    tm_measured_val4 = fields.Float(string="Measured Values")

    tm_avg_measured = fields.Float(string="Average", compute="_compute_tm_avg_measured")
    tm_percent_flow = fields.Float(string="% Flow", compute="_compute_tm_flow")

    @api.depends('tm_measured_val1', 'tm_measured_val2', 'tm_measured_val3', 'tm_measured_val4')
    def _compute_tm_avg_measured(self):
        for rec in self:
            vals = [v for v in [rec.tm_measured_val1, rec.tm_measured_val2, rec.tm_measured_val3, rec.tm_measured_val4] if v]
            rec.tm_avg_measured = sum(vals) / len(vals) if vals else 0.0

    @api.depends('tm_avg_measured')
    def _compute_tm_flow(self):
        for rec in self:
            rec.tm_percent_flow = rec.tm_avg_measured - 100

    # 7 Days Casting — Test Mixture
    tm_casting_date = fields.Date(string="Date of Casting")
    tm_testing_date = fields.Date(string="Date of Testing", compute="_compute_tm_testing_date")
    tm_casting_line_ids = fields.One2many('microsilica.pozzolanic.tm.line', 'parent_id', string="Test Mixture 7 Days")
    tm_avg_7days = fields.Float("Average", compute="_compute_tm_avg_7days")
    tm_comp_strength_7 = fields.Float("Compressive Strength", compute="_compute_tm_comp_7")

    @api.depends('tm_casting_date')
    def _compute_tm_testing_date(self):
        for rec in self:
            if rec.tm_casting_date:
                cast = fields.Datetime.from_string(rec.tm_casting_date)
                rec.tm_testing_date = fields.Datetime.to_string(cast + timedelta(days=7))
            else:
                rec.tm_testing_date = False

    @api.depends('tm_casting_line_ids.compressive_strength')
    def _compute_tm_avg_7days(self):
        for rec in self:
            vals = rec.tm_casting_line_ids.mapped('compressive_strength')
            rec.tm_avg_7days = round(sum(vals) / len(vals), 2) if vals else 0

    @api.depends('tm_avg_7days')
    def _compute_tm_comp_7(self):
        for rec in self:
            int_part = math.floor(rec.tm_avg_7days)
            frac = rec.tm_avg_7days - int_part
            if 0 < frac <= 0.25:
                rec.tm_comp_strength_7 = int_part
            elif 0.25 < frac <= 0.75:
                rec.tm_comp_strength_7 = int_part + 0.5
            elif 0.75 < frac <= 1:
                rec.tm_comp_strength_7 = int_part + 1
            else:
                rec.tm_comp_strength_7 = 0

    # Control Sample
    cs_high_range_water = fields.Integer(string="High Range water reducer (g)")
    cs_wt_cement = fields.Integer(string="Weight of Cement (g)", default=500)
    cs_wt_sand_grade1 = fields.Float(string="Weight of Standard Sand (g) Grade-I", default=458.33)
    cs_wt_sand_grade2 = fields.Float(string="Weight of Standard Sand (g) Grade-II", default=458.33)
    cs_wt_sand_grade3 = fields.Float(string="Weight of Standard Sand (g) Grade-III", default=458.33)
    cs_quantity_water = fields.Integer(string="Quantity of Water (g)")

    cs_measured_val1 = fields.Float(string="Measured Values")
    cs_measured_val2 = fields.Float(string="Measured Values")
    cs_measured_val3 = fields.Float(string="Measured Values")
    cs_measured_val4 = fields.Float(string="Measured Values")

    cs_avg_measured = fields.Float(string="Average", compute="_compute_cs_avg_measured")
    cs_percent_flow = fields.Float(string="% Flow", compute="_compute_cs_flow")

    @api.depends('cs_measured_val1', 'cs_measured_val2', 'cs_measured_val3', 'cs_measured_val4')
    def _compute_cs_avg_measured(self):
        for rec in self:
            vals = [v for v in [rec.cs_measured_val1, rec.cs_measured_val2, rec.cs_measured_val3, rec.cs_measured_val4] if v]
            rec.cs_avg_measured = sum(vals) / len(vals) if vals else 0.0

    @api.depends('cs_avg_measured')
    def _compute_cs_flow(self):
        for rec in self:
            rec.cs_percent_flow = rec.cs_avg_measured - 100

    # 7 Days Casting — Control Sample
    cs_casting_date = fields.Date(string="Date of Casting")
    cs_testing_date = fields.Date(string="Date of Testing", compute="_compute_cs_testing_date")
    cs_casting_line_ids = fields.One2many('microsilica.pozzolanic.cs.line', 'parent_id', string="Control Sample 7 Days")
    cs_avg_7days = fields.Float("Average", compute="_compute_cs_avg_7days")
    cs_comp_strength_7 = fields.Float("Compressive Strength", compute="_compute_cs_comp_7")

    @api.depends('cs_casting_date')
    def _compute_cs_testing_date(self):
        for rec in self:
            if rec.cs_casting_date:
                cast = fields.Datetime.from_string(rec.cs_casting_date)
                rec.cs_testing_date = fields.Datetime.to_string(cast + timedelta(days=7))
            else:
                rec.cs_testing_date = False

    @api.depends('cs_casting_line_ids.cs_compressive_strength')
    def _compute_cs_avg_7days(self):
        for rec in self:
            vals = rec.cs_casting_line_ids.mapped('cs_compressive_strength')
            rec.cs_avg_7days = round(sum(vals) / len(vals), 2) if vals else 0

    @api.depends('cs_avg_7days')
    def _compute_cs_comp_7(self):
        for rec in self:
            int_part = math.floor(rec.cs_avg_7days)
            frac = rec.cs_avg_7days - int_part
            if 0 < frac <= 0.25:
                rec.cs_comp_strength_7 = int_part
            elif 0.25 < frac <= 0.75:
                rec.cs_comp_strength_7 = int_part + 0.5
            elif 0.75 < frac <= 1:
                rec.cs_comp_strength_7 = int_part + 1
            else:
                rec.cs_comp_strength_7 = 0

    # Accelerated Pozzolanic Activity Index
    pozzolanic_index = fields.Float(
        "Accelerated Pozzolanic Activity Index 7 Days (%)",
        compute="_compute_pozzolanic_index"
    )

    @api.depends('tm_avg_7days', 'cs_avg_7days')
    def _compute_pozzolanic_index(self):
        for rec in self:
            if rec.cs_avg_7days:
                rec.pozzolanic_index = round((rec.tm_avg_7days / rec.cs_avg_7days) * 100, 2)
            else:
                rec.pozzolanic_index = 0

    pozzolanic_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail', compute="_compute_pozzolanic_conformity")

    pozzolanic_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_pozzolanic_nabl", store=True)

    @api.depends('pozzolanic_index', 'eln_ref')
    def _compute_pozzolanic_conformity(self):
        for record in self:
            record.pozzolanic_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', 'ddd2525aw-19f0-48b6-8e09-e7076a4b04b5')])
            materials = line.parameter_table
            for material in materials:
                req_min = material.req_min
                req_max = material.req_max
                mu_value = line.mu_value
                lower = record.pozzolanic_index - record.pozzolanic_index * mu_value
                upper = record.pozzolanic_index + record.pozzolanic_index * mu_value
                if lower >= req_min and upper <= req_max:
                    record.pozzolanic_conformity = 'pass'
                    break
                else:
                    record.pozzolanic_conformity = 'fail'

    @api.depends('pozzolanic_index', 'eln_ref')
    def _compute_pozzolanic_nabl(self):
        for record in self:
            record.pozzolanic_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', 'ddd2525aw-19f0-48b6-8e09-e7076a4b04b5')])
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            lower = record.pozzolanic_index - record.pozzolanic_index * mu_value
            upper = record.pozzolanic_index + record.pozzolanic_index * mu_value
            if lower >= lab_min and upper <= lab_max:
                record.pozzolanic_nabl = 'pass'
            else:
                record.pozzolanic_nabl = 'fail'


    # Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.wet_sieving_visible = False
            record.compressive_strength_visible = False
            record.specific_gravity_visible = False
            record.pozzolanic_visible = False

            for sample in record.sample_parameters:
                if sample.internal_id == 'ddd2525aw-19f0-48b6-8e09-e7076a4b04b5':
                    record.pozzolanic_visible = True
                if sample.internal_id == '52147fgtre-5f8c-44a2-984b-6ad2a17d250c':
                    record.wet_sieving_visible = True
                if sample.internal_id == '658fgtrcd-80ef-4de0-96ba-a279f27b9ede':
                    record.specific_gravity_visible = True
                if sample.internal_id == '658798cvfd-889b-477c-a355-0476f6bcd0d7':
                    record.compressive_strength_visible = True

    def open_eln_page(self):
        current_user = self.env.user
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            if result.parameter.internal_id == 'ddd2525aw-19f0-48b6-8e09-e7076a4b04b5':
                result.result_char = round(self.pozzolanic_index, 2)
                result.calculated = True
                result.nabl_status = 'nabl' if self.pozzolanic_nabl == 'pass' else 'non-nabl'
                continue

            if result.parameter.internal_id == '52147fgtre-5f8c-44a2-984b-6ad2a17d250c':
                result.result_char = round(self.avg_percent_passing, 2)
                result.calculated = True
                result.nabl_status = 'nabl' if self.wet_sieving_nabl == 'pass' else 'non-nabl'
                continue

            if result.parameter.internal_id == '658fgtrcd-80ef-4de0-96ba-a279f27b9ede':
                result.result_char = round(self.specific_gravity_avrg, 2)
                result.calculated = True
                result.nabl_status = 'nabl' if self.specific_gravity_nabl == 'pass' else 'non-nabl'
                continue

            if result.parameter.internal_id == '658798cvfd-889b-477c-a355-0476f6bcd0d7':
                result.result_char = round(self.avg_28_strength, 2)
                result.calculated = True
                result.nabl_status = 'nabl' if self.compressive_strength_nabl == 'pass' else 'non-nabl'
                continue

        return {
            'view_mode': 'form',
            'res_model': "lerm.eln",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.eln_ref.id,
        }

    @api.model
    def create(self, vals):
        record = super(Microsilica, self).create(vals)
        record.eln_ref.write({'model_id': record.id})
        return record

    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    def _compute_sample_parameters(self):
        current_user = self.env.user

        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            if (
                current_user.has_group('lerm_civil.kes_admin_access_group')
                or current_user.has_group('lerm_civil.lerm_sample_verification')
                or current_user.has_group('lerm_civil.lerm_sample_approval')
            ):
                parameter_ids = record.eln_ref.parameters_result.mapped('parameter').ids
            else:
                user_param_results = record.eln_ref.parameters_result.filtered(
                    lambda r: r.technician and r.technician.id == current_user.id
                )
                parameter_ids = user_param_results.mapped('parameter').ids

            record.sample_parameters = [(6, 0, parameter_ids)]

    def prefill_data(self):
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'mech.microsilica.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
            },
        }

    notes_id = fields.One2many('mechanical.microsilica.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

    @api.model
    def _default_notes_lines(self):
        return [
            (0, 0, {'sr_no': 'i', 'notes': 'The results stated in this report apply only to the tested sample(s) and are based on the conditions and parameters at the time of testing.'}),
            (0, 0, {'sr_no': 'ii', 'notes': 'This report is invalid without the official paper seal of Make Infracon.'}),
            (0, 0, {'sr_no': 'iii', 'notes': 'All test results are confidential and will not be disclosed to any third party without written consent of the client, except where required by law.'}),
            (0, 0, {'sr_no': 'iv', 'notes': 'Any discrepancies or complaints regarding this report must be communicated in writing within 7 days from the date of issue.'}),
            (0, 0, {'sr_no': 'v', 'notes': 'This report shall not be reproduced, except in full, without the prior written approval of Make Infracon.'}),
            (0, 0, {'sr_no': 'vi', 'notes': 'The laboratory assumes no responsibility for the purpose for which the test results are used or for any subsequent actions taken based on these results.'}),
        ]


# ============================================================
# Child Line Models
# ============================================================

class MicrosilicaWetSievingLine(models.Model):
    _name = "microsilica.wet.sieving.line"

    parent_id = fields.Many2one('mechanical.microsilica', string="Parent Id")

    sr_no = fields.Integer("S.No", readonly=True, copy=False, default=1)
    sample_weight = fields.Float("Weight of Sample (Ws) (g)", default=100.0)
    weight_retained = fields.Float("Weight of Residue Retained (Wr) (g)")
    weight_passing = fields.Float("Weight of Material Passing (Ws - Wr) (g)", compute="_compute_weight_passing")
    percent_passing = fields.Float("% of Material Passing", compute="_compute_percent_passing")

    @api.depends('sample_weight', 'weight_retained')
    def _compute_weight_passing(self):
        for rec in self:
            rec.weight_passing = rec.sample_weight - rec.weight_retained

    @api.depends('weight_passing', 'sample_weight')
    def _compute_percent_passing(self):
        for rec in self:
            if rec.sample_weight:
                rec.percent_passing = (rec.weight_passing / rec.sample_weight) * 100
            else:
                rec.percent_passing = 0.0

    @api.model
    def create(self, vals):
        if vals.get('parent_id'):
            existing = self.search([('parent_id', '=', vals['parent_id'])])
            vals['sr_no'] = (max(existing.mapped('sr_no')) + 1) if existing else 1
        return super(MicrosilicaWetSievingLine, self).create(vals)

    def _reorder_serial_numbers(self):
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class MicrosilicaCompressiveStrengthLine(models.Model):
    _name = "microsilica.compressive.strength.line"

    parent_id = fields.Many2one('mechanical.microsilica', string="Parent Id")

    sr_no = fields.Integer("S.No", readonly=True, copy=False, default=1)
    age_days = fields.Selection([
        ('7', '7 Days'),
        ('14', '14 Days'),
        ('28', '28 Days'),
    ], string="Age in Days", default='7')
    weight_g = fields.Float("Weight (g)")
    density_g_cc = fields.Float("Density (g/cc)", compute="_compute_density")
    load_kN = fields.Float("Load at Failure (kN)")
    comp_strength = fields.Float("Compressive Strength (N/mm²)", compute="_compute_comp_strength")

    CUBE_DIM = 70.6

    @api.depends('weight_g')
    def _compute_density(self):
        vol = self.CUBE_DIM ** 3
        for rec in self:
            rec.density_g_cc = rec.weight_g / vol if vol else 0.0

    @api.depends('load_kN')
    def _compute_comp_strength(self):
        area = self.CUBE_DIM ** 2
        for rec in self:
            rec.comp_strength = (rec.load_kN * 1000.0) / area if area else 0.0

    @api.model
    def create(self, vals):
        if vals.get('parent_id'):
            existing = self.search([('parent_id', '=', vals['parent_id'])])
            vals['sr_no'] = (max(existing.mapped('sr_no')) + 1) if existing else 1
        return super(MicrosilicaCompressiveStrengthLine, self).create(vals)

    def _reorder_serial_numbers(self):
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class MicrosilicaSpecificGravityLine(models.Model):
    _name = "microsilica.specific.gravity.line"

    parent_id = fields.Many2one('mechanical.microsilica', string="Parent Id")

    sr_no = fields.Integer("Trial", readonly=True, copy=False, default=1)
    w1_microsilica = fields.Float("Weight of Micro Silica Sample - W1 (g)", default=64.0)
    v1_initial = fields.Float("Initial Reading of Flask - V1 (ml)")
    v2_final = fields.Float("Final Reading of Flask - V2 (ml)")
    volume_silica = fields.Float("Volume of Micro Silica (V2-V1) (ml)", compute="_compute_volume_silica")
    wt_equal_vol_water = fields.Float("Weight of Equal Volume of Water (g)", compute="_compute_wt_equal_vol_water")
    spe_gravt_microsilica = fields.Float("Sp. Gravity of Micro Silica", compute="_compute_spe_gravt_microsilica")

    @api.depends('v2_final', 'v1_initial')
    def _compute_volume_silica(self):
        for rec in self:
            rec.volume_silica = rec.v2_final - rec.v1_initial

    @api.depends('volume_silica')
    def _compute_wt_equal_vol_water(self):
        for rec in self:
            rec.wt_equal_vol_water = rec.volume_silica * 1.0

    @api.depends('w1_microsilica', 'wt_equal_vol_water')
    def _compute_spe_gravt_microsilica(self):
        for rec in self:
            if rec.wt_equal_vol_water:
                rec.spe_gravt_microsilica = rec.w1_microsilica / rec.wt_equal_vol_water
            else:
                rec.spe_gravt_microsilica = 0.0

    @api.model
    def create(self, vals):
        if vals.get('parent_id'):
            existing = self.search([('parent_id', '=', vals['parent_id'])])
            vals['sr_no'] = (max(existing.mapped('sr_no')) + 1) if existing else 1
        return super(MicrosilicaSpecificGravityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class PozzolanicTestMixture7DaysLine(models.Model):
    _name = "microsilica.pozzolanic.tm.line"

    parent_id = fields.Many2one('mechanical.microsilica', string="Parent Id")

    length = fields.Float("Length in mm")
    width = fields.Float("Width in mm")
    crosssectional_area = fields.Float("Crosssectional Area", compute="_compute_crosssectional_area")
    wt_cube = fields.Float("wt of Cube in gm")
    crushing_load = fields.Float("Crushing Load in KN")
    compressive_strength = fields.Float("Compressive Strength (N/mm²)", compute="_compute_compressive_strength")

    @api.depends('length', 'width')
    def _compute_crosssectional_area(self):
        for rec in self:
            rec.crosssectional_area = rec.length * rec.width

    @api.depends('crosssectional_area', 'crushing_load')
    def _compute_compressive_strength(self):
        for rec in self:
            if rec.crosssectional_area:
                rec.compressive_strength = (rec.crushing_load / rec.crosssectional_area) * 1000
            else:
                rec.compressive_strength = 0


class PozzolanicControlSample7DaysLine(models.Model):
    _name = "microsilica.pozzolanic.cs.line"

    parent_id = fields.Many2one('mechanical.microsilica', string="Parent Id")

    cs_length = fields.Float("Length in mm")
    cs_width = fields.Float("Width in mm")
    cs_crosssectional_area = fields.Float("Crosssectional Area", compute="_compute_cs_crosssectional_area")
    cs_wt_cube = fields.Float("wt of Cube in gm")
    cs_crushing_load = fields.Float("Crushing Load in KN")
    cs_compressive_strength = fields.Float("Compressive Strength (N/mm²)", compute="_compute_cs_compressive_strength")

    @api.depends('cs_length', 'cs_width')
    def _compute_cs_crosssectional_area(self):
        for rec in self:
            rec.cs_crosssectional_area = rec.cs_length * rec.cs_width

    @api.depends('cs_crosssectional_area', 'cs_crushing_load')
    def _compute_cs_compressive_strength(self):
        for rec in self:
            if rec.cs_crosssectional_area:
                rec.cs_compressive_strength = (rec.cs_crushing_load / rec.cs_crosssectional_area) * 1000
            else:
                rec.cs_compressive_strength = 0


class MicrosilicaNotes(models.Model):
    _name = "mechanical.microsilica.notes"

    parent_id = fields.Many2one('mechanical.microsilica', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
