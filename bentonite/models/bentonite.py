from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import math
import base64
import io
import logging

_logger = logging.getLogger(__name__)


class MechanicalBentonite(models.Model):
    _name = "mechanical.bentonite"
    _inherit = "lerm.eln"
    _description = 'mechanical.bentonite'
    _rec_name = "name"

    name = fields.Char("Name", default="Bentonite")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master', string="Parameters", compute="_compute_sample_parameters", store=True)

    grade = fields.Many2one('lerm.grade.line', string="Grade", compute="_compute_grade_id", store=True)
    size_id = fields.Many2one('lerm.size.line', string="Size", compute="_compute_size_id", store=True)
    eln_ref = fields.Many2one('lerm.eln', string="ELN")

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    sample_id = fields.Many2one('lerm.srf.sample', string='Sample')

    notes_id = fields.One2many('bentonite.notes', 'parent_id', string="Notes")

    # ---------------- Liquid Limit ----------------
    ll_name = fields.Char("Name", default="Liquid Limit")
    ll_visible = fields.Boolean("Liquid Limit Visible", compute="_compute_visible")

    ll_child_lines = fields.One2many('bentonite.ll.line', 'parent_id', string="Liquid Limit")

    liquid_limit_result = fields.Float(string="Liquid Limit (%)", compute="_compute_liquid_limit_result", digits=(16, 2))
    ll_graph = fields.Binary(string="Flow Curve", compute="_compute_ll_graph", store=True)

    ll_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity', compute="_compute_ll_conformity", store=True)

    ll_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', compute="_compute_ll_nabl", store=True)

    # ---------------- Wet Fineness ----------------
    wet_fineness_name = fields.Char("Name", default="Wet Fineness")
    wet_fineness_visible = fields.Boolean("Wet Fineness Visible", compute="_compute_visible")

    wet_fineness_int_wt = fields.Float(string="Initial Weight (g)")
    wet_fineness_lines = fields.One2many('bentonite.wet.fineness.line', 'parent_id', string="Wet Fineness")

    wet_fineness_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity', compute="_compute_wet_fineness_conformity", store=True)

    wet_fineness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', compute="_compute_wet_fineness_nabl", store=True)

    # ---------------- Dry Fineness ----------------
    dry_fineness_name = fields.Char("Name", default="Dry Fineness")
    dry_fineness_visible = fields.Boolean("Dry Fineness Visible", compute="_compute_visible")

    dry_fineness_int_wt = fields.Float(string="Initial Weight (g)")
    dry_fineness_lines = fields.One2many('bentonite.dry.fineness.line', 'parent_id', string="Dry Fineness")

    dry_fineness_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity', compute="_compute_dry_fineness_conformity", store=True)

    dry_fineness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', compute="_compute_dry_fineness_nabl", store=True)

    # ---------------- Moisture Content ----------------
    moisture_name = fields.Char("Name", default="Moisture Content")
    moisture_visible = fields.Boolean("Moisture Content Visible", compute="_compute_visible")

    moisture_m1 = fields.Float(string="Initial Weight M1 (g)")
    moisture_m2 = fields.Float(string="Dry Weight M2 (g)")
    moisture_content_result = fields.Float(string="Moisture Content (%)", compute="_compute_moisture_content_result", digits=(16, 2))

    moisture_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity', compute="_compute_moisture_conformity", store=True)

    moisture_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', compute="_compute_moisture_nabl", store=True)

    # ---------------- Sand Content ----------------
    sand_name = fields.Char("Name", default="Sand Content")
    sand_visible = fields.Boolean("Sand Content Visible", compute="_compute_visible")

    sand_initial_wt = fields.Float(string="Initial Weight (g)")
    sand_final_wt = fields.Float(string="Final Weight (g)")
    sand_content_result = fields.Float(string="Sand Content (%)", compute="_compute_sand_content_result", digits=(16, 2))

    sand_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity', compute="_compute_sand_conformity", store=True)

    sand_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', compute="_compute_sand_nabl", store=True)

    @api.model
    def default_get(self, fields_list):
        res = super(MechanicalBentonite, self).default_get(fields_list)

        default_notes = [
            (0, 0, {
                'sr_no': 'i',
                'notes': 'Attention is drawn to the limitations of liability, indemnification, and jurisdiction provisions applicable to this report. The information contained herein reflects the findings of Geonyms India Private Limited at the time of testing and only within the scope of work and instructions received from the Client, where applicable',
            }),
            (0, 0, {
                'sr_no': 'ii',
                'notes': 'The Companys responsibility is limited to the Client for whom this report has been issued. This report does not relieve any party from exercising its rights and fulfilling its obligations under any contract, agreement, or applicable statutory requirements. Unless otherwise stated, the results reported herein relate only to the sample(s) tested and do not necessarily indicate the quality of the entire lot, batch, or material from which the sample(s) were drawn. ',
            }),
            (0, 0, {
                'sr_no': 'iii',
                'notes': 'The sample(s) tested shall be retained for a period of ninety (90) days from the date of issue of this report unless otherwise agreed with the Client. This report shall not be reproduced, except in full, without the prior written approval of Geonyms India Private Limited. ',
            }),
            (0, 0, {
                'sr_no': 'iv',
                'notes': 'Partial reproduction, unauthorized alteration, forgery, falsification, or misuse of this report is prohibited and may result in legal action.',
            }),
            (0, 0, {
                'sr_no': 'v',
                'notes': ' Any complaint concerning this report shall be submitted in writing within fifteen (15) days from the date of issue of the report. The use of this report or extracts thereof in advertisements, promotional material, media publications, or any public disclosure requires prior written approval from Geonyms India Private Limited',
            }),
        ]

        res['notes_id'] = default_notes
        return res

    # ---------------- Computed results ----------------
    @api.depends('ll_child_lines.moisture_content')
    def _compute_liquid_limit_result(self):
        for rec in self:
            values = [line.moisture_content for line in rec.ll_child_lines if line.moisture_content]
            rec.liquid_limit_result = round(sum(values) / len(values), 2) if values else 0.0

    @api.depends('ll_child_lines.penetration', 'll_child_lines.moisture_content')
    def _compute_ll_graph(self):
        for rec in self:
            rec.ll_graph = False
            points = [(l.penetration, l.moisture_content) for l in rec.ll_child_lines if l.penetration and l.moisture_content]
            if len(points) < 2:
                continue
            try:
                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                import numpy as np

                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                order = np.argsort(xs)
                xs = [xs[i] for i in order]
                ys = [ys[i] for i in order]

                fig, ax = plt.subplots(figsize=(6, 4))
                ax.set_xscale('log')
                ax.plot(xs, ys, 'o-', color='b')
                ax.set_xlabel('Penetration (mm)')
                ax.set_ylabel('Moisture Content (%)')
                ax.set_title('Flow Curve')
                ax.grid(True, which='both', ls='--', alpha=0.4)

                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=100)
                plt.close(fig)
                rec.ll_graph = base64.b64encode(buf.getvalue())
            except Exception as e:
                _logger.warning("Bentonite LL graph generation failed: %s", e)

    @api.depends('moisture_m1', 'moisture_m2')
    def _compute_moisture_content_result(self):
        for rec in self:
            if rec.moisture_m1:
                rec.moisture_content_result = round(((rec.moisture_m1 - rec.moisture_m2) / rec.moisture_m1) * 100, 2)
            else:
                rec.moisture_content_result = 0.0

    @api.depends('sand_initial_wt', 'sand_final_wt')
    def _compute_sand_content_result(self):
        for rec in self:
            if rec.sand_initial_wt:
                rec.sand_content_result = round((rec.sand_final_wt / rec.sand_initial_wt) * 100, 2)
            else:
                rec.sand_content_result = 0.0

    # ---------------- Conformity / NABL ----------------
    def _get_parameter_master(self, internal_id):
        return self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', internal_id)], limit=1)

    def _fineness_passing(self, lines):
        if not lines:
            return 0.0
        finest = lines.sorted(key=lambda l: l.sieve_size)
        return finest[0].pct_passing or 0.0

    @api.depends('liquid_limit_result', 'eln_ref', 'grade')
    def _compute_ll_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.ll_conformity = 'na'
                continue
            record.ll_conformity = 'fail'
            line = self._get_parameter_master('bentonite-ll-4a1b-4c2d-8e3f-000000000001')
            materials = line.parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lower = record.liquid_limit_result - record.liquid_limit_result * line.mu_value
                    upper = record.liquid_limit_result + record.liquid_limit_result * line.mu_value
                    if lower >= material.req_min and upper <= material.req_max:
                        record.ll_conformity = 'pass'
                        break

    @api.depends('liquid_limit_result', 'eln_ref', 'grade')
    def _compute_ll_nabl(self):
        for record in self:
            record.ll_nabl = 'fail'
            line = self._get_parameter_master('bentonite-ll-4a1b-4c2d-8e3f-000000000001')
            lower = record.liquid_limit_result - record.liquid_limit_result * line.mu_value
            upper = record.liquid_limit_result + record.liquid_limit_result * line.mu_value
            if lower >= line.lab_min_value and upper <= line.lab_max_value:
                record.ll_nabl = 'pass'

    @api.depends('wet_fineness_lines', 'eln_ref', 'grade')
    def _compute_wet_fineness_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.wet_fineness_conformity = 'na'
                continue
            record.wet_fineness_conformity = 'fail'
            line = self._get_parameter_master('bentonite-wf-4a1b-4c2d-8e3f-000000000002')
            materials = line.parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    result = record._fineness_passing(record.wet_fineness_lines)
                    lower = result - result * line.mu_value
                    upper = result + result * line.mu_value
                    if lower >= material.req_min and upper <= material.req_max:
                        record.wet_fineness_conformity = 'pass'
                        break

    @api.depends('wet_fineness_lines', 'eln_ref', 'grade')
    def _compute_wet_fineness_nabl(self):
        for record in self:
            record.wet_fineness_nabl = 'fail'
            line = self._get_parameter_master('bentonite-wf-4a1b-4c2d-8e3f-000000000002')
            result = record._fineness_passing(record.wet_fineness_lines)
            lower = result - result * line.mu_value
            upper = result + result * line.mu_value
            if lower >= line.lab_min_value and upper <= line.lab_max_value:
                record.wet_fineness_nabl = 'pass'

    @api.depends('dry_fineness_lines', 'eln_ref', 'grade')
    def _compute_dry_fineness_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.dry_fineness_conformity = 'na'
                continue
            record.dry_fineness_conformity = 'fail'
            line = self._get_parameter_master('bentonite-df-4a1b-4c2d-8e3f-000000000003')
            materials = line.parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    result = record._fineness_passing(record.dry_fineness_lines)
                    lower = result - result * line.mu_value
                    upper = result + result * line.mu_value
                    if lower >= material.req_min and upper <= material.req_max:
                        record.dry_fineness_conformity = 'pass'
                        break

    @api.depends('dry_fineness_lines', 'eln_ref', 'grade')
    def _compute_dry_fineness_nabl(self):
        for record in self:
            record.dry_fineness_nabl = 'fail'
            line = self._get_parameter_master('bentonite-df-4a1b-4c2d-8e3f-000000000003')
            result = record._fineness_passing(record.dry_fineness_lines)
            lower = result - result * line.mu_value
            upper = result + result * line.mu_value
            if lower >= line.lab_min_value and upper <= line.lab_max_value:
                record.dry_fineness_nabl = 'pass'

    @api.depends('moisture_content_result', 'eln_ref', 'grade')
    def _compute_moisture_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.moisture_conformity = 'na'
                continue
            record.moisture_conformity = 'fail'
            line = self._get_parameter_master('bentonite-mc-4a1b-4c2d-8e3f-000000000004')
            materials = line.parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lower = record.moisture_content_result - record.moisture_content_result * line.mu_value
                    upper = record.moisture_content_result + record.moisture_content_result * line.mu_value
                    if lower >= material.req_min and upper <= material.req_max:
                        record.moisture_conformity = 'pass'
                        break

    @api.depends('moisture_content_result', 'eln_ref', 'grade')
    def _compute_moisture_nabl(self):
        for record in self:
            record.moisture_nabl = 'fail'
            line = self._get_parameter_master('bentonite-mc-4a1b-4c2d-8e3f-000000000004')
            lower = record.moisture_content_result - record.moisture_content_result * line.mu_value
            upper = record.moisture_content_result + record.moisture_content_result * line.mu_value
            if lower >= line.lab_min_value and upper <= line.lab_max_value:
                record.moisture_nabl = 'pass'

    @api.depends('sand_content_result', 'eln_ref', 'grade')
    def _compute_sand_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.sand_conformity = 'na'
                continue
            record.sand_conformity = 'fail'
            line = self._get_parameter_master('bentonite-sc-4a1b-4c2d-8e3f-000000000005')
            materials = line.parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lower = record.sand_content_result - record.sand_content_result * line.mu_value
                    upper = record.sand_content_result + record.sand_content_result * line.mu_value
                    if lower >= material.req_min and upper <= material.req_max:
                        record.sand_conformity = 'pass'
                        break

    @api.depends('sand_content_result', 'eln_ref', 'grade')
    def _compute_sand_nabl(self):
        for record in self:
            record.sand_nabl = 'fail'
            line = self._get_parameter_master('bentonite-sc-4a1b-4c2d-8e3f-000000000005')
            lower = record.sand_content_result - record.sand_content_result * line.mu_value
            upper = record.sand_content_result + record.sand_content_result * line.mu_value
            if lower >= line.lab_min_value and upper <= line.lab_max_value:
                record.sand_nabl = 'pass'

    # ---------------- Visibility ----------------
    @api.depends('sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.ll_visible = False
            record.wet_fineness_visible = False
            record.dry_fineness_visible = False
            record.moisture_visible = False
            record.sand_visible = False

            for sample in record.sample_parameters:
                if sample.internal_id == "bentonite-ll-4a1b-4c2d-8e3f-000000000001":
                    record.ll_visible = True
                if sample.internal_id == "bentonite-wf-4a1b-4c2d-8e3f-000000000002":
                    record.wet_fineness_visible = True
                if sample.internal_id == "bentonite-df-4a1b-4c2d-8e3f-000000000003":
                    record.dry_fineness_visible = True
                if sample.internal_id == "bentonite-mc-4a1b-4c2d-8e3f-000000000004":
                    record.moisture_visible = True
                if sample.internal_id == "bentonite-sc-4a1b-4c2d-8e3f-000000000005":
                    record.sand_visible = True

    # ---------------- ELN linkage ----------------
    def prefill_data(self):
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'bentonite.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
            },
        }

    def open_eln_page(self):
        current_user = self.env.user
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            if result.parameter.internal_id == 'bentonite-ll-4a1b-4c2d-8e3f-000000000001':
                result.calculated = True
                result.result_char = round(self.liquid_limit_result, 2)
                result.nabl_status = 'nabl' if self.ll_nabl == 'pass' else 'non-nabl'
                continue
            if result.parameter.internal_id == 'bentonite-wf-4a1b-4c2d-8e3f-000000000002':
                result.calculated = True
                result.result_char = round(self._fineness_passing(self.wet_fineness_lines), 2)
                result.nabl_status = 'nabl' if self.wet_fineness_nabl == 'pass' else 'non-nabl'
                continue
            if result.parameter.internal_id == 'bentonite-df-4a1b-4c2d-8e3f-000000000003':
                result.calculated = True
                result.result_char = round(self._fineness_passing(self.dry_fineness_lines), 2)
                result.nabl_status = 'nabl' if self.dry_fineness_nabl == 'pass' else 'non-nabl'
                continue
            if result.parameter.internal_id == 'bentonite-mc-4a1b-4c2d-8e3f-000000000004':
                result.calculated = True
                result.result_char = round(self.moisture_content_result, 2)
                result.nabl_status = 'nabl' if self.moisture_nabl == 'pass' else 'non-nabl'
                continue
            if result.parameter.internal_id == 'bentonite-sc-4a1b-4c2d-8e3f-000000000005':
                result.calculated = True
                result.result_char = round(self.sand_content_result, 2)
                result.nabl_status = 'nabl' if self.sand_nabl == 'pass' else 'non-nabl'
                continue

        return {
            'view_mode': 'form',
            'res_model': "lerm.eln",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.eln_ref.id,
        }

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    @api.model
    def create(self, vals):
        record = super(MechanicalBentonite, self).create(vals)
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

    def read(self, fields=None, load='_classic_read'):
        self._compute_sample_parameters()
        self._compute_visible()
        return super(MechanicalBentonite, self).read(fields=fields, load=load)


class BentoniteLLLine(models.Model):
    _name = "bentonite.ll.line"
    parent_id = fields.Many2one('mechanical.bentonite', string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    penetration = fields.Float(string="Penetration (mm)")
    container_no = fields.Char(string="Container No.")
    wt_container_wet_soil = fields.Float(string="Weight of Container + Wet Soil (g)")
    wt_container_dry_soil = fields.Float(string="Weight of Container + Dry Soil (g)")
    wt_water = fields.Float(string="Weight of Water (g)", compute="_compute_wt_water", store=True)
    wt_container = fields.Float(string="Weight of Container (g)")
    wt_dry_soil = fields.Float(string="Weight of Dry Soil (g)", compute="_compute_wt_dry_soil", store=True)
    moisture_content = fields.Float(string="Moisture Content (%)", compute="_compute_moisture_content", store=True)

    @api.depends('wt_container_wet_soil', 'wt_container_dry_soil')
    def _compute_wt_water(self):
        for rec in self:
            rec.wt_water = rec.wt_container_wet_soil - rec.wt_container_dry_soil

    @api.depends('wt_container_dry_soil', 'wt_container')
    def _compute_wt_dry_soil(self):
        for rec in self:
            rec.wt_dry_soil = rec.wt_container_dry_soil - rec.wt_container

    @api.depends('wt_water', 'wt_dry_soil')
    def _compute_moisture_content(self):
        for rec in self:
            if rec.wt_dry_soil:
                rec.moisture_content = round((rec.wt_water / rec.wt_dry_soil) * 100, 2)
            else:
                rec.moisture_content = 0.0

    @api.model
    def create(self, vals):
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1
        return super(BentoniteLLLine, self).create(vals)


class BentoniteWetFinenessLine(models.Model):
    _name = "bentonite.wet.fineness.line"
    parent_id = fields.Many2one('mechanical.bentonite', string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    sieve_size = fields.Float(string="Sieve Size (mm)")
    retained_wt = fields.Float(string="Retained Wt. (g)")
    cum_retained = fields.Float(string="Cum. Wt. Retained (g)", compute="_compute_cum_retained", store=True)
    pct_retention = fields.Float(string="% of Retention", compute="_compute_pct_retention", store=True)
    pct_passing = fields.Float(string="% of Passing", compute="_compute_pct_passing", store=True)

    @api.depends('parent_id.wet_fineness_lines.retained_wt', 'parent_id.wet_fineness_lines.sieve_size')
    def _compute_cum_retained(self):
        for rec in self:
            lines = rec.parent_id.wet_fineness_lines.sorted(key=lambda l: l.sieve_size, reverse=True)
            cum = 0.0
            for line in lines:
                cum += line.retained_wt
                line.cum_retained = round(cum, 3)

    @api.depends('cum_retained', 'parent_id.wet_fineness_int_wt')
    def _compute_pct_retention(self):
        for rec in self:
            if rec.parent_id.wet_fineness_int_wt:
                rec.pct_retention = round((rec.cum_retained / rec.parent_id.wet_fineness_int_wt) * 100, 2)
            else:
                rec.pct_retention = 0.0

    @api.depends('pct_retention')
    def _compute_pct_passing(self):
        for rec in self:
            rec.pct_passing = round(100 - rec.pct_retention, 2)

    @api.model
    def create(self, vals):
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1
        return super(BentoniteWetFinenessLine, self).create(vals)


class BentoniteDryFinenessLine(models.Model):
    _name = "bentonite.dry.fineness.line"
    parent_id = fields.Many2one('mechanical.bentonite', string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    sieve_size = fields.Float(string="Sieve Size (mm)")
    retained_wt = fields.Float(string="Retained Wt. (g)")
    cum_retained = fields.Float(string="Cum. Wt. Retained (g)", compute="_compute_cum_retained", store=True)
    pct_retention = fields.Float(string="% of Retention", compute="_compute_pct_retention", store=True)
    pct_passing = fields.Float(string="% of Passing", compute="_compute_pct_passing", store=True)

    @api.depends('parent_id.dry_fineness_lines.retained_wt', 'parent_id.dry_fineness_lines.sieve_size')
    def _compute_cum_retained(self):
        for rec in self:
            lines = rec.parent_id.dry_fineness_lines.sorted(key=lambda l: l.sieve_size, reverse=True)
            cum = 0.0
            for line in lines:
                cum += line.retained_wt
                line.cum_retained = round(cum, 3)

    @api.depends('cum_retained', 'parent_id.dry_fineness_int_wt')
    def _compute_pct_retention(self):
        for rec in self:
            if rec.parent_id.dry_fineness_int_wt:
                rec.pct_retention = round((rec.cum_retained / rec.parent_id.dry_fineness_int_wt) * 100, 2)
            else:
                rec.pct_retention = 0.0

    @api.depends('pct_retention')
    def _compute_pct_passing(self):
        for rec in self:
            rec.pct_passing = round(100 - rec.pct_retention, 2)

    @api.model
    def create(self, vals):
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1
        return super(BentoniteDryFinenessLine, self).create(vals)


class BentoniteNotes(models.Model):
    _name = "bentonite.notes"

    parent_id = fields.Many2one('mechanical.bentonite', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
