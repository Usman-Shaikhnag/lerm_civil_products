from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math

import logging
_logger = logging.getLogger(__name__)



class BurntClayHollowBrick(models.Model):
    _name = "mechanical.burnt.clay.hollow.brick"
    _inherit = "lerm.eln"
    _rec_name = "name_burnt_clay_hollow_brick"


    name_burnt_clay_hollow_brick = fields.Char("Name",default="Burnt Clay Hollow Brick")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id



    # Crushing Value
    crushing_value_name = fields.Char("Name",default="Crushing Value")
    crushing_visible = fields.Boolean("Crushing Value Visible",compute="_compute_visible")

    crushing_value_child_lines = fields.One2many('burnt.clay.hollow.brick.crushing.value.line','parent_id',string="Crushing Value")

    average_crushing_value = fields.Float(
        string="Average Crushing Value",
        compute="_compute_average_crushing_value", store=True)

    @api.depends('crushing_value_child_lines.acv')
    def _compute_average_crushing_value(self):
        for rec in self:
            lines = rec.crushing_value_child_lines
            if lines:
                total = sum(line.acv for line in lines)
                rec.average_crushing_value = round(total / len(lines), 2)
            else:
                rec.average_crushing_value = 0.0

    average_crushing_value_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_average_crushing_value_conformity", store=True)

    @api.depends('average_crushing_value','eln_ref','grade')
    def _compute_average_crushing_value_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_crushing_value_conformity = 'na'
                continue
            record.average_crushing_value_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ea70f185-651e-456c-83ec-253420b76855')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ea70f185-651e-456c-83ec-253420b76855')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_crushing_value - record.average_crushing_value*mu_value
                    upper = record.average_crushing_value + record.average_crushing_value*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_crushing_value_conformity = 'pass'
                        break
                    else:
                        record.average_crushing_value_conformity = 'fail'

    average_crushing_value_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_crushing_value_nabl", store=True)

    @api.depends('average_crushing_value','eln_ref','grade')
    def _compute_average_crushing_value_nabl(self):
        
        for record in self:
            record.average_crushing_value_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ea70f185-651e-456c-83ec-253420b76855')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ea70f185-651e-456c-83ec-253420b76855')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_crushing_value - record.average_crushing_value*mu_value
                    upper = record.average_crushing_value + record.average_crushing_value*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_crushing_value_nabl = 'pass'
                        break
                    else:
                        record.average_crushing_value_nabl = 'fail'


    # Dimension
    dimension_name = fields.Char("Name",default="Dimension")
    dimension_visible = fields.Boolean("Dimension Visible",compute="_compute_visible")

    dimension_child_lines = fields.One2many('burnt.clay.hollow.brick.dimension.line','parent_id',string="Dimension")

    avg_length = fields.Float(
        string="Average Length",
        compute="_compute_averages",
        store=True
    )

    avg_width = fields.Float(
        string="Average Width",
        compute="_compute_averages",
        store=True
    )

    avg_height = fields.Float(
        string="Average Height",
        compute="_compute_averages",
        store=True
    )

    avg_area = fields.Float(
        string="Average Cross Sectional Area",
        compute="_compute_averages",
        store=True
    )

    @api.depends(
        'dimension_child_lines.length',
        'dimension_child_lines.width',
        'dimension_child_lines.height',
        'dimension_child_lines.area'
    )
    def _compute_averages(self):
        for rec in self:
            lines = rec.dimension_child_lines

            if not lines:
                rec.avg_length = 0.0
                rec.avg_width = 0.0
                rec.avg_height = 0.0
                rec.avg_area = 0.0
                continue

            count = len(lines)

            rec.avg_length = round(sum(lines.mapped('length')) / count, 2)
            rec.avg_width = round(sum(lines.mapped('width')) / count, 2)
            rec.avg_height = round(sum(lines.mapped('height')) / count, 2)
            rec.avg_area = round(sum(lines.mapped('area')) / count, 2)


    avg_length_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_length_conformity", store=True)

    @api.depends('avg_length','eln_ref','grade')
    def _compute_avg_length_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_length_conformity = 'na'
                continue
            record.avg_length_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','70024868-33a5-41e1-bc5f-17a9e34d5c00')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','70024868-33a5-41e1-bc5f-17a9e34d5c00')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_length - record.avg_length*mu_value
                    upper = record.avg_length + record.avg_length*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_length_conformity = 'pass'
                        break
                    else:
                        record.avg_length_conformity = 'fail'

    avg_length_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_length_nabl", store=True)

    @api.depends('avg_length','eln_ref','grade')
    def _compute_avg_length_nabl(self):
        
        for record in self:
            record.avg_length_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','70024868-33a5-41e1-bc5f-17a9e34d5c00')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','70024868-33a5-41e1-bc5f-17a9e34d5c00')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_length - record.avg_length*mu_value
                    upper = record.avg_length + record.avg_length*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_length_nabl = 'pass'
                        break
                    else:
                        record.avg_length_nabl = 'fail'

    avg_width_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_width_conformity", store=True)

    @api.depends('avg_width','eln_ref','grade')
    def _compute_avg_width_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_width_conformity = 'na'
                continue
            record.avg_width_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f510e3df-e0f4-4266-909b-6765a99b04db')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f510e3df-e0f4-4266-909b-6765a99b04db')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_width - record.avg_width*mu_value
                    upper = record.avg_width + record.avg_width*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_width_conformity = 'pass'
                        break
                    else:
                        record.avg_width_conformity = 'fail'

    avg_width_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_width_nabl", store=True)

    @api.depends('avg_width','eln_ref','grade')
    def _compute_avg_width_nabl(self):
        
        for record in self:
            record.avg_width_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f510e3df-e0f4-4266-909b-6765a99b04db')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f510e3df-e0f4-4266-909b-6765a99b04db')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_width - record.avg_width*mu_value
                    upper = record.avg_width + record.avg_width*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_width_nabl = 'pass'
                        break
                    else:
                        record.avg_width_nabl = 'fail'

    
    avg_height_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_height_conformity", store=True)

    @api.depends('avg_height','eln_ref','grade')
    def _compute_avg_height_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_height_conformity = 'na'
                continue
            record.avg_height_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3b508566-fa84-4a8e-9162-bfc13971e348')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3b508566-fa84-4a8e-9162-bfc13971e348')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_height - record.avg_height*mu_value
                    upper = record.avg_height + record.avg_height*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_height_conformity = 'pass'
                        break
                    else:
                        record.avg_height_conformity = 'fail'

    avg_height_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_height_nabl", store=True)

    @api.depends('avg_height','eln_ref','grade')
    def _compute_avg_height_nabl(self):
        
        for record in self:
            record.avg_height_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3b508566-fa84-4a8e-9162-bfc13971e348')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3b508566-fa84-4a8e-9162-bfc13971e348')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_height - record.avg_height*mu_value
                    upper = record.avg_height + record.avg_height*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_height_nabl = 'pass'
                        break
                    else:
                        record.avg_height_nabl = 'fail'


    avg_area_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_area_conformity", store=True)

    @api.depends('avg_area','eln_ref','grade')
    def _compute_avg_area_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_area_conformity = 'na'
                continue
            record.avg_area_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b4368958-ca01-4724-8bd9-67514a3eb2ad')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b4368958-ca01-4724-8bd9-67514a3eb2ad')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_area - record.avg_area*mu_value
                    upper = record.avg_area + record.avg_area*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_area_conformity = 'pass'
                        break
                    else:
                        record.avg_area_conformity = 'fail'

    avg_area_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_area_nabl", store=True)

    @api.depends('avg_area','eln_ref','grade')
    def _compute_avg_area_nabl(self):
        
        for record in self:
            record.avg_area_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b4368958-ca01-4724-8bd9-67514a3eb2ad')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b4368958-ca01-4724-8bd9-67514a3eb2ad')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_area - record.avg_area*mu_value
                    upper = record.avg_area + record.avg_area*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_area_nabl = 'pass'
                        break
                    else:
                        record.avg_area_nabl = 'fail'


    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.crushing_visible = False
            record.dimension_visible = False
            
            for sample in record.sample_parameters:

                if sample.internal_id == "ea70f185-651e-456c-83ec-253420b76855":
                    record.crushing_visible = True

                if sample.internal_id == "65a8f5a6-5915-49b9-8fdd-70dc724bab58":
                    record.dimension_visible = True

    def open_eln_page(self):
        current_user = self.env.user
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

            if result.parameter.internal_id == '65a8f5a6-5915-49b9-8fdd-70dc724bab58':
                result.calculated = True

            if result.parameter.internal_id == '70024868-33a5-41e1-bc5f-17a9e34d5c00':
                result.calculated = True

            if result.parameter.internal_id == 'f510e3df-e0f4-4266-909b-6765a99b04db':
                result.calculated = True

            if result.parameter.internal_id == '3b508566-fa84-4a8e-9162-bfc13971e348':
                result.calculated = True

            if result.parameter.internal_id == 'b4368958-ca01-4724-8bd9-67514a3eb2ad':
                result.calculated = True

            if result.parameter.internal_id == 'ea70f185-651e-456c-83ec-253420b76855':
                result.calculated = True
                result.result_char = round(self.average_crushing_value,2)
                if self.average_crushing_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
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
        record = super(BurntClayHollowBrick, self).create(vals)
        record.eln_ref.write({'model_id':record.id})
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
    
    def get_all_fields(self):
        record = self.env['mechanical.burnt.clay.hollow.brick'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    # def prefill_data(self):
    #     view_id = self.env.ref('burnt_clay_hollow_brick.action_burnt_clay_hollow_brick_prefill_data_wizard').id
    #     return {
    #         'view_mode': 'form',
    #         'res_model': 'burnt.clay.hollow.brick.prefill.data',
    #         'target': 'new',
    #         'type': 'ir.actions.act_window',
    #         'view_id': view_id,
    #         'context': {
    #             'default_product_id': self.eln_ref.sample_id.material_id.id,
    #             'exclude_sample_id': self.eln_ref.sample_id.id,
    #         }
    #     }


    notes_id = fields.One2many('mechanical.burnt.clay.hollow.brick.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

    @api.model
    def _default_notes_lines(self):
        return [
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


class CrushingValueLine(models.Model):
    _name = "burnt.clay.hollow.brick.crushing.value.line"
    parent_id = fields.Many2one('mechanical.burnt.clay.hollow.brick',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)
    w1 = fields.Float(string="Weight of Mould + Aggregate (W1)")
    w2 = fields.Float(string="Weight of Empty Mould (W2)")
    w3 = fields.Float(string="Weight Passing 2.36 mm Sieve (W3)")
    acv = fields.Float(string="Aggregate Crushing Value (A.C.V) = W3/(W1-W2)x 100",
                        compute="_compute_acv", store=True)

    @api.depends('w1', 'w2', 'w3')
    def _compute_acv(self):
        for rec in self:
            if (rec.w1 - rec.w2) != 0:
                rec.acv = (rec.w3 / (rec.w1 - rec.w2)) * 100
            else:
                rec.acv = 0.0

    @api.model
    def create(self, vals):
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1
        return super(CrushingValueLine, self).create(vals)

    def _reorder_serial_numbers(self):
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class DimensionLine(models.Model):
    _name = "burnt.clay.hollow.brick.dimension.line"
    parent_id = fields.Many2one('mechanical.burnt.clay.hollow.brick',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    length = fields.Float(string="Length")
    width = fields.Float(string="Width")
    height = fields.Float(string="Height")

    area = fields.Float(
    string="Cross Sectional Area",
    compute="_compute_area",
    store=True
)

    @api.depends('width', 'height')
    def _compute_area(self):
     for line in self:
        line.area = (line.width or 0.0) * (line.height or 0.0)


    
    @api.model
    def create(self, vals):
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1
        return super(DimensionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class BurntClayHollowBrickNotes(models.Model):
    _name = "mechanical.burnt.clay.hollow.brick.notes"

    parent_id = fields.Many2one('mechanical.burnt.clay.hollow.brick', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
