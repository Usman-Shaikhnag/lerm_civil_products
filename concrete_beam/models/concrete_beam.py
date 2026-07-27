from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
from datetime import datetime , timedelta
import re
import logging


class FlexuralStrengthConcreteBeam(models.Model):
    _name = "mechanical.concrete.beam"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Concrete Beam")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines = fields.One2many('mechanical.concrete.beam.line','parent_id',string="Parameter")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="ELN")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    temp = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)
    
    
    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")
    date_of_testing = fields.Date(string="Date of Testing")

    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None


    @api.depends('eln_ref')
    def _compute_grade_id(self):
        for record in self:
            if record.eln_ref:
                grade = record.eln_ref.grade_id.id
                print("Grade beam",grade)
                record.grade = record.eln_ref.grade_id.id

    notes_id = fields.One2many('mechanical.concrete.beam.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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
    







    # Flexural Strength
    flexural_strength_name = fields.Char(default="Flexural Strength")
    flexural_strength_visible = fields.Boolean(string="Flexural Strength Visible" ,compute="_compute_visible")

    flexural_strength_line_ids = fields.One2many('mechanical.concrete.beam.line','parent_id',string='Flexural Strength Test Lines', default=lambda self: self._default_flexural_strength_lines())

    flex_size_id = fields.Selection([
    ('600 x 150 x 150 mm', '600 x 150 x 150 mm'),
    ('700 x 150 x 150 mm', '700 x 150 x 150 mm'),
     ], string="Size")

    @api.model
    def _default_flexural_strength_lines(self):
        default_lines = [
            (0, 0, {'age': '3 Days'}),
            (0, 0, {'age': '3 Days'}),
            (0, 0, {'age': '3 Days'}),
            (0, 0, {'age': '7 Days'}),
            (0, 0, {'age': '7 Days'}),
            (0, 0, {'age': '7 Days'}),
            (0, 0, {'age': '14 Days'}),
            (0, 0, {'age': '14 Days'}),
            (0, 0, {'age': '14 Days'}),
            (0, 0, {'age': '28 Days'}),
            (0, 0, {'age': '28 Days'}),
            (0, 0, {'age': '28 Days'}),
        ]
        return default_lines
    
   
    
    

    avg_3_days_flexural = fields.Float(string="Avg 3 Days Flexural Strength",compute='_compute_flexural_avg',store=True)

    avg_7_days_flexural = fields.Float(string="Avg 7 Days Flexural Strength",compute='_compute_flexural_avg',store=True)

    avg_14_days_flexural = fields.Float(string="Avg 14 Days Flexural Strength",compute='_compute_flexural_avg',store=True)

    avg_28_days_flexural = fields.Float(string="Avg 28 Days Flexural Strength",compute='_compute_flexural_avg',store=True)


    @api.depends('flexural_strength_line_ids.flexural_strength','flexural_strength_line_ids.age')
    def _compute_flexural_avg(self):
     for rec in self:

        rec.avg_3_days_flexural = 0.0
        rec.avg_7_days_flexural = 0.0
        rec.avg_14_days_flexural = 0.0
        rec.avg_28_days_flexural = 0.0

        for age, field_name in [
            ('3 Days', 'avg_3_days_flexural'),
            ('7 Days', 'avg_7_days_flexural'),
            ('14 Days', 'avg_14_days_flexural'),
            ('28 Days', 'avg_28_days_flexural')
        ]:

            lines = rec.flexural_strength_line_ids.filtered(
                lambda l: l.age == age
            )

            avg = (
                sum(lines.mapped('flexural_strength')) / len(lines)
                if lines else 0.0
            )

            setattr(rec, field_name, avg)

    span_length = fields.Float(string="Span Length")

    avg_3_days_flexural_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_3_days_flexural_confirmity")

    @api.depends('avg_3_days_flexural','eln_ref','grade')
    def _compute_avg_3_days_flexural_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_3_days_flexural_confirmity = 'na'
                continue
            record.avg_3_days_flexural_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ace70b39-15b5-4c58-8d7b-915d978c0a1a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ace70b39-15b5-4c58-8d7b-915d978c0a1a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_3_days_flexural - record.avg_3_days_flexural*mu_value
                    upper = record.avg_3_days_flexural + record.avg_3_days_flexural*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_3_days_flexural_confirmity = 'pass'
                        break
                    else:
                        record.avg_3_days_flexural_confirmity = 'fail'

    avg_3_days_flexural_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_3_days_flexural_nabl")

    @api.depends('avg_3_days_flexural','eln_ref','grade')
    def _compute_avg_3_days_flexural_nabl(self):
        
        for record in self:
            record.avg_3_days_flexural_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ace70b39-15b5-4c58-8d7b-915d978c0a1a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ace70b39-15b5-4c58-8d7b-915d978c0a1a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_3_days_flexural - record.avg_3_days_flexural*mu_value
                    upper = record.avg_3_days_flexural + record.avg_3_days_flexural*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_3_days_flexural_nabl = 'pass'
                        break
                    else:
                        record.avg_3_days_flexural_nabl = 'fail'


    avg_3_days_flexural_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_3_days_flexural_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_3_days_flexural_final_report", store=True)

    @api.depends('avg_3_days_flexural_nabl', 'avg_3_days_flexural_report_type')
    def _compute_avg_3_days_flexural_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_3_days_flexural_report_type == 'nabl':
            rec.avg_3_days_flexural_final_report = 'nabl'

        elif rec.avg_3_days_flexural_report_type == 'non_nabl':
            rec.avg_3_days_flexural_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_3_days_flexural_nabl == 'pass':
                rec.avg_3_days_flexural_final_report = 'nabl'
            else:
                rec.avg_3_days_flexural_final_report = 'non_nabl'

    
    avg_7_days_flexural_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_7_days_flexural_confirmity")

    @api.depends('avg_7_days_flexural','eln_ref','grade')
    def _compute_avg_7_days_flexural_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_7_days_flexural_confirmity = 'na'
                continue
            record.avg_7_days_flexural_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2fd3a24a-a5e6-4496-a4d3-3f9cc78cac57')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2fd3a24a-a5e6-4496-a4d3-3f9cc78cac57')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_7_days_flexural - record.avg_7_days_flexural*mu_value
                    upper = record.avg_7_days_flexural + record.avg_7_days_flexural*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_7_days_flexural_confirmity = 'pass'
                        break
                    else:
                        record.avg_7_days_flexural_confirmity = 'fail'

    avg_7_days_flexural_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_7_days_flexural_nabl")

    @api.depends('avg_7_days_flexural','eln_ref','grade')
    def _compute_avg_7_days_flexural_nabl(self):
        
        for record in self:
            record.avg_7_days_flexural_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2fd3a24a-a5e6-4496-a4d3-3f9cc78cac57')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2fd3a24a-a5e6-4496-a4d3-3f9cc78cac57')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_7_days_flexural - record.avg_7_days_flexural*mu_value
                    upper = record.avg_7_days_flexural + record.avg_7_days_flexural*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_7_days_flexural_nabl = 'pass'
                        break
                    else:
                        record.avg_7_days_flexural_nabl = 'fail'


    avg_7_days_flexural_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_7_days_flexural_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_7_days_flexural_final_report", store=True)

    @api.depends('avg_7_days_flexural_nabl', 'avg_7_days_flexural_report_type')
    def _compute_avg_7_days_flexural_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_7_days_flexural_report_type == 'nabl':
            rec.avg_7_days_flexural_final_report = 'nabl'

        elif rec.avg_7_days_flexural_report_type == 'non_nabl':
            rec.avg_7_days_flexural_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_7_days_flexural_nabl == 'pass':
                rec.avg_7_days_flexural_final_report = 'nabl'
            else:
                rec.avg_7_days_flexural_final_report = 'non_nabl'

    
    avg_14_days_flexural_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_14_days_flexural_confirmity")

    @api.depends('avg_14_days_flexural','eln_ref','grade')
    def _compute_avg_14_days_flexural_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_14_days_flexural_confirmity = 'na'
                continue
            record.avg_14_days_flexural_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','846557b2-3403-4b12-a698-33987d6fb835')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','846557b2-3403-4b12-a698-33987d6fb835')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_14_days_flexural - record.avg_14_days_flexural*mu_value
                    upper = record.avg_14_days_flexural + record.avg_14_days_flexural*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_14_days_flexural_confirmity = 'pass'
                        break
                    else:
                        record.avg_14_days_flexural_confirmity = 'fail'

    avg_14_days_flexural_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_14_days_flexural_nabl")

    @api.depends('avg_14_days_flexural','eln_ref','grade')
    def _compute_avg_14_days_flexural_nabl(self):
        
        for record in self:
            record.avg_14_days_flexural_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','846557b2-3403-4b12-a698-33987d6fb835')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','846557b2-3403-4b12-a698-33987d6fb835')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_14_days_flexural - record.avg_14_days_flexural*mu_value
                    upper = record.avg_14_days_flexural + record.avg_14_days_flexural*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_14_days_flexural_nabl = 'pass'
                        break
                    else:
                        record.avg_14_days_flexural_nabl = 'fail'

    avg_14_days_flexural_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_14_days_flexural_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_14_days_flexural_final_report", store=True)

    @api.depends('avg_14_days_flexural_nabl', 'avg_14_days_flexural_report_type')
    def _compute_avg_14_days_flexural_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_14_days_flexural_report_type == 'nabl':
            rec.avg_14_days_flexural_final_report = 'nabl'

        elif rec.avg_14_days_flexural_report_type == 'non_nabl':
            rec.avg_14_days_flexural_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_14_days_flexural_nabl == 'pass':
                rec.avg_14_days_flexural_final_report = 'nabl'
            else:
                rec.avg_14_days_flexural_final_report = 'non_nabl'


    avg_28_days_flexural_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_28_days_flexural_confirmity")

    @api.depends('avg_28_days_flexural','eln_ref','grade')
    def _compute_avg_28_days_flexural_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_28_days_flexural_confirmity = 'na'
                continue
            record.avg_28_days_flexural_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','73312b11-7690-40ce-82f1-dfe8a51e57dc')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','73312b11-7690-40ce-82f1-dfe8a51e57dc')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_28_days_flexural - record.avg_28_days_flexural*mu_value
                    upper = record.avg_28_days_flexural + record.avg_28_days_flexural*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_28_days_flexural_confirmity = 'pass'
                        break
                    else:
                        record.avg_28_days_flexural_confirmity = 'fail'

    avg_28_days_flexural_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_28_days_flexural_nabl")

    @api.depends('avg_28_days_flexural','eln_ref','grade')
    def _compute_avg_28_days_flexural_nabl(self):
        
        for record in self:
            record.avg_28_days_flexural_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','73312b11-7690-40ce-82f1-dfe8a51e57dc')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','73312b11-7690-40ce-82f1-dfe8a51e57dc')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_28_days_flexural - record.avg_28_days_flexural*mu_value
                    upper = record.avg_28_days_flexural + record.avg_28_days_flexural*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_28_days_flexural_nabl = 'pass'
                        break
                    else:
                        record.avg_28_days_flexural_nabl = 'fail'

    
    avg_28_days_flexural_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_28_days_flexural_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_28_days_flexural_final_report", store=True)

    @api.depends('avg_28_days_flexural_nabl', 'avg_28_days_flexural_report_type')
    def _compute_avg_28_days_flexural_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_28_days_flexural_report_type == 'nabl':
            rec.avg_28_days_flexural_final_report = 'nabl'

        elif rec.avg_28_days_flexural_report_type == 'non_nabl':
            rec.avg_28_days_flexural_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_28_days_flexural_nabl == 'pass':
                rec.avg_28_days_flexural_final_report = 'nabl'
            else:
                rec.avg_28_days_flexural_final_report = 'non_nabl'
    

    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.flexural_strength_visible = False


            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                if sample.internal_id == "19edc74f-c7b2-45b6-8696-e97c19e81993":
                    record.flexural_strength_visible = True
    



    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:


            # Flexural Strength
            if result.parameter.internal_id == '19edc74f-c7b2-45b6-8696-e97c19e81993':
                result.calculated = True

            # 3 Days Flexural Strength
            if result.parameter.internal_id == 'ace70b39-15b5-4c58-8d7b-915d978c0a1a':
                result.result_char = round(self.avg_3_days_flexural,2)
                result.calculated = True
                if self.avg_3_days_flexural_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 7 Days Flexural Strength
            if result.parameter.internal_id == '2fd3a24a-a5e6-4496-a4d3-3f9cc78cac57':
                result.result_char = round(self.avg_7_days_flexural,2)
                result.calculated = True
                if self.avg_7_days_flexural_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 14 Days Flexural Strength
            if result.parameter.internal_id == '846557b2-3403-4b12-a698-33987d6fb835':
                result.result_char = round(self.avg_14_days_flexural,2)
                result.calculated = True
                if self.avg_14_days_flexural_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 28 Days Flexural Strength
            if result.parameter.internal_id == '73312b11-7690-40ce-82f1-dfe8a51e57dc':
                result.result_char = round(self.avg_28_days_flexural,2)
                result.calculated = True
                if self.avg_28_days_flexural_nabl == 'pass':
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
        # import wdb;wdb.set_trace()
        record = super(FlexuralStrengthConcreteBeam, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        test = record.eln_ref
        print("test",test)

        return record

    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    def _compute_sample_parameters(self):
        current_user = self.env.user

        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            # Check if user is in Lerm Admin group
            if (
                current_user.has_group('lerm_civil.kes_admin_access_group')
                or current_user.has_group('lerm_civil.lerm_sample_verification')
                or current_user.has_group('lerm_civil.lerm_sample_approval')
            ):
                # Admin sees all parameters
                parameter_ids = record.eln_ref.parameters_result.mapped('parameter').ids
            else:
                # Other users only see parameters assigned to them
                user_param_results = record.eln_ref.parameters_result.filtered(
                    lambda r: r.technician and r.technician.id == current_user.id
                )
                parameter_ids = user_param_results.mapped('parameter').ids

            record.sample_parameters = [(6, 0, parameter_ids)]


    def get_all_fields(self):
        record = self.env['mechanical.concrete.beam'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    
    




    
class FlexuralStrengthConcreteBeamLine(models.Model):
    _name = "mechanical.concrete.beam.line"
    parent_id = fields.Many2one('mechanical.concrete.beam',string="Parent Id")


    age = fields.Char(string='Age Of Beam')

    weight = fields.Float(string='Weight (Kg)')
    volume = fields.Float(string='Volume (cm³)',compute='_compute_volume',
    store=True,digits=(16,0))

    fail_point = fields.Char(string='Failure At Point')

    density = fields.Float(
        string='Density (g/cc)',
        compute='_compute_density',
        store=True
    )

    test_area = fields.Float(string="Test Area (mm²)",compute="_compute_test_area",store=True,digits=(16,0))

    # @api.depends('parent_id.beam_width', 'parent_id.beam_depth')
    # def _compute_test_area(self):
    #  for rec in self:
    #     rec.test_area = (
    #         rec.parent_id.beam_width *
    #         rec.parent_id.beam_depth
    #     )

    load_kn = fields.Float(string='Load Observed (kN)')

    flexural_strength = fields.Float(
        string='Flexural Strength (N/mm²)',
        compute='_compute_flexural_strength',
        store=True
    )

    @api.depends('weight', 'volume')
    def _compute_density(self):
     for rec in self:
        rec.density = (
            (rec.weight * 1000) / rec.volume
            if rec.volume else 0.0
        )

    @api.depends('parent_id.flex_size_id')
    def _compute_volume(self):
     for rec in self:
        rec.volume = 0.0

        size = rec.parent_id.flex_size_id
        if size:
            # Extract numbers from "700 x 150 x 150 mm"
            values = [float(x) for x in re.findall(r'\d+', size)]

            if len(values) == 3:
                length, width, depth = values

                # mm³ -> cm³
                rec.volume = (length * width * depth) / 1000.0


    @api.depends('parent_id.flex_size_id')
    def _compute_test_area(self):
     for rec in self:
        rec.test_area = 0.0

        size_str = rec.parent_id.flex_size_id

        if size_str:
            # Extract all numbers from the size string
            values = [float(x) for x in re.findall(r'\d+', size_str)]

            if len(values) == 3:
                length, width, depth = values

                # Cross-sectional area = Width × Depth
                rec.test_area = width * depth

    @api.depends(
    'load_kn',
    'test_area',
    'parent_id.span_length',
    'parent_id.flex_size_id'
)
    def _compute_flexural_strength(self):
     import re

     for rec in self:
        rec.flexural_strength = 0.0

        size_str = rec.parent_id.flex_size_id

        if size_str:
            values = [float(x) for x in re.findall(r'\d+', size_str)]

            if len(values) == 3:
                _, width, depth = values

                P = rec.load_kn * 1000
                L = rec.parent_id.span_length
                A = rec.test_area

                if P and L and A and depth:
                    rec.flexural_strength = (P * L) / (A * depth)

                    
class FlexuralStrengthConcreteBeamNotes(models.Model):
    _name = "mechanical.concrete.beam.notes"

    parent_id = fields.Many2one('mechanical.concrete.beam', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
