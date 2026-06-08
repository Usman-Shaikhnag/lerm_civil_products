from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
from datetime import datetime , timedelta
import re
import logging

_logger = logging.getLogger(__name__)

class MechanicalAdmixture(models.Model):
    _name = 'mechanical.admixture'
    _inherit = "lerm.eln"
    _rec_name = "name"


    name_admixture = fields.Char("Name",default="Admixture")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    admixture_temp = fields.Char("Temperature °C",store=True)
    admixture_humidity = fields.Char("Humidity °C",store=True)

    @api.depends("eln_ref")
    def _compute_size_id(self):
        for record in self:
            print("Size iD",record.eln_ref.size_id)
            record.size_id = record.eln_ref.size_id.id


    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")

    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None



    date_of_testing = fields.Date(string="Date of Testing",compute="_compute_date_testing")

    @api.depends('eln_ref')
    def _compute_date_testing(self):
        if self.eln_ref:
            self.date_of_testing = self.eln_ref.date_testing
        else:
            self.date_of_testing = ''



    
    notes_id = fields.One2many('mechanical.admixture.notes', 'parent_id',string="Notes",
    default=lambda self: self._default_notes_lines()
)
    
    @api.model
    def _default_notes_lines(self):
        return [
            (0, 0, {
                'sr_no': 'i',
                'notes': 'The results stated in this report apply only to the tested sample(s) and are based on the conditions and parameters at the time of testing.',
            }),
            (0, 0, {
                'sr_no': 'ii',
                'notes': 'This report is invalid without the official paper seal of Make Infracon.',
            }),
            (0, 0, {
                'sr_no': 'iii',
                'notes': 'All test results are confidential and will not be disclosed to any third party without written consent of the client, except where required by law.',
            }),
            (0, 0, {
                'sr_no': 'iv',
                'notes': 'The # points mentioned in the report which information is given by Client/Customer.',
            }),

            (0, 0, {
                'sr_no': 'v',
                'notes': 'Any disputes shall be subject to jurisdiction of Nashik courts only.',
            }),
        ]
    



    room_temp = fields.Char(string="Room Temp")
    room_rh = fields.Char(string="Room RH")

    # Bleeding
    bleeding_visible = fields.Boolean("Bleeding Test Visible",compute="_compute_visible")
    bleeding_name = fields.Char("Name",default="Bleeding Test")

    bleeding_lines_ids = fields.One2many('admixture.bleeding.test.line', 'parent_id', string="Parameter", default=lambda self: self._default_bleeding_lines_ids())

    @api.model
    def _default_bleeding_lines_ids(self):
        default_lines = [
            (0, 0, {'sample_no': '1'}),
            (0, 0, {'sample_no': '2'}),
            (0, 0, {'sample_no': '3'}),
        ]
        return default_lines
    
    avg_bleeding_percent = fields.Float(string="Average Bleeding (%)",compute='_compute_avg_bleeding',store=True)

    @api.depends('bleeding_lines_ids.bleeding_percent')
    def _compute_avg_bleeding(self):
      for rec in self:
        if rec.bleeding_lines_ids:
            rec.avg_bleeding_percent = (
                sum(rec.bleeding_lines_ids.mapped('bleeding_percent'))
                / len(rec.bleeding_lines_ids)
            )
        else:
            rec.avg_bleeding_percent = 0.0

    avg_bleeding_percent_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_bleeding_percent_confirmity")
    
    @api.depends('avg_bleeding_percent','eln_ref','grade')
    def _compute_avg_bleeding_percent_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_bleeding_percent_confirmity = 'na'
                continue
            record.avg_bleeding_percent_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f722fd9-5698-452d-90c1-a36e837d7805')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f722fd9-5698-452d-90c1-a36e837d7805')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_bleeding_percent - record.avg_bleeding_percent*mu_value
                    upper = record.avg_bleeding_percent + record.avg_bleeding_percent*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_bleeding_percent_confirmity = 'pass'
                        break
                    else:
                        record.avg_bleeding_percent_confirmity = 'fail'

    avg_bleeding_percent_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_bleeding_percent_nabl")
    
    @api.depends('avg_bleeding_percent','eln_ref','grade')
    def _compute_avg_bleeding_percent_nabl(self):
        
        for record in self:
            record.avg_bleeding_percent_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f722fd9-5698-452d-90c1-a36e837d7805')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f722fd9-5698-452d-90c1-a36e837d7805')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_bleeding_percent - record.avg_bleeding_percent*mu_value
                    upper = record.avg_bleeding_percent + record.avg_bleeding_percent*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_bleeding_percent_nabl = 'pass'
                        break
                    else:
                        record.avg_bleeding_percent_nabl = 'fail'

    # Slump Test
    slump_test_name = fields.Char(default="Slump Test")
    slump_test_visible = fields.Boolean(string="Slump Test Visible" ,compute="_compute_visible")

    slump_test_line_ids = fields.One2many('admixture.slump.test.line','parent_id',string='Admixture Slump Test Lines', default=lambda self: self._default_slump_test_lines_ids())

    @api.model
    def _default_slump_test_lines_ids(self):
        default_lines = [
            (0, 0, {'sample_no': '1'}),
            (0, 0, {'sample_no': '2'}),
            (0, 0, {'sample_no': '3'}),
        ]
        return default_lines

    avg_slump = fields.Float(
        string='Average Slump (mm)',
        compute='_compute_avg_slumps',
        store=True
    )

    @api.depends('slump_test_line_ids.slump_value')
    def _compute_avg_slumps(self):
        for rec in self:
            if rec.slump_test_line_ids:
                rec.avg_slump = sum(rec.slump_test_line_ids.mapped('slump_value')) / len(rec.slump_test_line_ids)
            else:
                rec.avg_slump = 0.0


    avg_slump_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_slump_confirmity")

    @api.depends('avg_slump','eln_ref','grade')
    def _compute_avg_slump_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_slump_confirmity = 'na'
                continue
            record.avg_slump_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98717d5e-562d-48b6-a969-d411229301de')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98717d5e-562d-48b6-a969-d411229301de')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_slump - record.avg_slump*mu_value
                    upper = record.avg_slump + record.avg_slump*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_slump_confirmity = 'pass'
                        break
                    else:
                        record.avg_slump_confirmity = 'fail'

    avg_slump_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_slump_nabl")

    @api.depends('avg_slump','eln_ref','grade')
    def _compute_avg_slump_nabl(self):
        
        for record in self:
            record.avg_slump_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98717d5e-562d-48b6-a969-d411229301de')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98717d5e-562d-48b6-a969-d411229301de')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_slump - record.avg_slump*mu_value
                    upper = record.avg_slump + record.avg_slump*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_slump_nabl = 'pass'
                        break
                    else:
                        record.avg_slump_nabl = 'fail'


    # Compressive Strength
    compressive_strength_name = fields.Char(default="Compressive Strength")
    compressive_strength_visible = fields.Boolean(string="Compressive Strength Visible" ,compute="_compute_visible")

    compressive_strength_line_ids = fields.One2many('admixture.compressive.strength.line','parent_id',string='Compressive Strength Test Lines', default=lambda self: self.default_compressive_strength_lines_ids())

    @api.model
    def default_compressive_strength_lines_ids(self):
        default_lines = [
            (0, 0, {'age': '3 Days','cube_no':'Cube-1'}),
            (0, 0, {'age': '3 Days','cube_no':'Cube-2'}),
            (0, 0, {'age': '3 Days','cube_no':'Cube-3'}),
            (0, 0, {'age': '7 Days','cube_no':'Cube-1'}),
            (0, 0, {'age': '7 Days','cube_no':'Cube-2'}),
            (0, 0, {'age': '7 Days','cube_no':'Cube-3'}),
            (0, 0, {'age': '14 Days','cube_no':'Cube-1'}),
            (0, 0, {'age': '14 Days','cube_no':'Cube-2'}),
            (0, 0, {'age': '14 Days','cube_no':'Cube-3'}),
            (0, 0, {'age': '28 Days','cube_no':'Cube-1'}),
            (0, 0, {'age': '28 Days','cube_no':'Cube-2'}),
            (0, 0, {'age': '28 Days','cube_no':'Cube-3'}),
        ]
        return default_lines
    

    avg_3_days = fields.Float(string="Avg 3 Days Compressive Strength",compute="_compute_agewise_avg",store=True)

    avg_7_days = fields.Float(string="Avg 7 Days Compressive Strength",compute="_compute_agewise_avg",store=True)

    avg_14_days = fields.Float(string="Avg 14 Days Compressive Strength",compute="_compute_agewise_avg",store=True)

    avg_28_days = fields.Float(string="Avg 28 Days Compressive Strength",compute="_compute_agewise_avg",store=True)
    
    @api.depends('compressive_strength_line_ids.compressive_strength',
             'compressive_strength_line_ids.age')
    def _compute_agewise_avg(self):
     for rec in self:

        rec.avg_3_days = 0.0
        rec.avg_7_days = 0.0
        rec.avg_14_days = 0.0
        rec.avg_28_days = 0.0

        age_3 = rec.compressive_strength_line_ids.filtered(
            lambda l: l.age in ['3', '3 Days']
        )

        age_7 = rec.compressive_strength_line_ids.filtered(
            lambda l: l.age in ['7', '7 Days']
        )

        age_14 = rec.compressive_strength_line_ids.filtered(
            lambda l: l.age in ['14', '14 Days']
        )

        age_28 = rec.compressive_strength_line_ids.filtered(
            lambda l: l.age in ['28', '28 Days']
        )

        if age_3:
            rec.avg_3_days = sum(age_3.mapped('compressive_strength')) / len(age_3)

        if age_7:
            rec.avg_7_days = sum(age_7.mapped('compressive_strength')) / len(age_7)

        if age_14:
            rec.avg_14_days = sum(age_14.mapped('compressive_strength')) / len(age_14)

        if age_28:
            rec.avg_28_days = sum(age_28.mapped('compressive_strength')) / len(age_28)


        


    avg_3_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_3_days_confirmity")

    @api.depends('avg_3_days','eln_ref','grade')
    def _compute_avg_3_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_3_days_confirmity = 'na'
                continue
            record.avg_3_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8ec2711d-3fb4-4ff7-b903-74b31b2a5c4b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8ec2711d-3fb4-4ff7-b903-74b31b2a5c4b')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_3_days - record.avg_3_days*mu_value
                    upper = record.avg_3_days + record.avg_3_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_3_days_confirmity = 'pass'
                        break
                    else:
                        record.avg_3_days_confirmity = 'fail'

    avg_3_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_3_days_nabl")

    @api.depends('avg_3_days','eln_ref','grade')
    def _compute_avg_3_days_nabl(self):
        
        for record in self:
            record.avg_3_days_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8ec2711d-3fb4-4ff7-b903-74b31b2a5c4b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8ec2711d-3fb4-4ff7-b903-74b31b2a5c4b')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_3_days - record.avg_3_days*mu_value
                    upper = record.avg_3_days + record.avg_3_days*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_3_days_nabl = 'pass'
                        break
                    else:
                        record.avg_3_days_nabl = 'fail'


    avg_7_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_7_days_confirmity")

    @api.depends('avg_7_days','eln_ref','grade')
    def _compute_avg_7_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_7_days_confirmity = 'na'
                continue
            record.avg_7_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57a1b1b7-ae7a-4c60-8974-ec3e3b70c3b3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57a1b1b7-ae7a-4c60-8974-ec3e3b70c3b3')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_7_days - record.avg_7_days*mu_value
                    upper = record.avg_7_days + record.avg_7_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_7_days_confirmity = 'pass'
                        break
                    else:
                        record.avg_7_days_confirmity = 'fail'

    avg_7_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_7_days_nabl")

    @api.depends('avg_7_days','eln_ref','grade')
    def _compute_avg_7_days_nabl(self):
        
        for record in self:
            record.avg_7_days_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57a1b1b7-ae7a-4c60-8974-ec3e3b70c3b3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57a1b1b7-ae7a-4c60-8974-ec3e3b70c3b3')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_7_days - record.avg_7_days*mu_value
                    upper = record.avg_7_days + record.avg_7_days*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_7_days_nabl = 'pass'
                        break
                    else:
                        record.avg_7_days_nabl = 'fail'


    avg_14_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_14_days_confirmity")

    @api.depends('avg_14_days','eln_ref','grade')
    def _compute_avg_14_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_14_days_confirmity = 'na'
                continue
            record.avg_14_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6927f8e-0aff-4cff-8be4-242d807fdd7b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6927f8e-0aff-4cff-8be4-242d807fdd7b')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_14_days - record.avg_14_days*mu_value
                    upper = record.avg_14_days + record.avg_14_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_14_days_confirmity = 'pass'
                        break
                    else:
                        record.avg_14_days_confirmity = 'fail'

    avg_14_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_14_days_nabl")

    @api.depends('avg_14_days','eln_ref','grade')
    def _compute_avg_14_days_nabl(self):
        
        for record in self:
            record.avg_14_days_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6927f8e-0aff-4cff-8be4-242d807fdd7b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6927f8e-0aff-4cff-8be4-242d807fdd7b')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_14_days - record.avg_14_days*mu_value
                    upper = record.avg_14_days + record.avg_14_days*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_14_days_nabl = 'pass'
                        break
                    else:
                        record.avg_14_days_nabl = 'fail'

    
    avg_28_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_28_days_confirmity")

    @api.depends('avg_28_days','eln_ref','grade')
    def _compute_avg_28_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_28_days_confirmity = 'na'
                continue
            record.avg_28_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','86419a8f-580c-4ee2-91aa-2904ce7a665a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','86419a8f-580c-4ee2-91aa-2904ce7a665a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_28_days - record.avg_28_days*mu_value
                    upper = record.avg_28_days + record.avg_28_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_28_days_confirmity = 'pass'
                        break
                    else:
                        record.avg_28_days_confirmity = 'fail'

    avg_28_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_28_days_nabl")

    @api.depends('avg_28_days','eln_ref','grade')
    def _compute_avg_28_days_nabl(self):
        
        for record in self:
            record.avg_28_days_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','86419a8f-580c-4ee2-91aa-2904ce7a665a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','86419a8f-580c-4ee2-91aa-2904ce7a665a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_28_days - record.avg_28_days*mu_value
                    upper = record.avg_28_days + record.avg_28_days*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_28_days_nabl = 'pass'
                        break
                    else:
                        record.avg_28_days_nabl = 'fail'



    # Flexural Strength
    flexural_strength_name = fields.Char(default="Flexural Strength")
    flexural_strength_visible = fields.Boolean(string="Flexural Strength Visible" ,compute="_compute_visible")

    flexural_strength_line_ids = fields.One2many('admixture.flexural.strength.line','parent_id',string='Flexural Strength Test Lines', default=lambda self: self._default_flexural_strength_lines())

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
    beam_width = fields.Float(string="Width of Specimen")
    beam_depth = fields.Float(string="Depth of Specimen")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e6c08fb2-dbd2-4e52-ba73-7d26a0b0a2b0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e6c08fb2-dbd2-4e52-ba73-7d26a0b0a2b0')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e6c08fb2-dbd2-4e52-ba73-7d26a0b0a2b0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e6c08fb2-dbd2-4e52-ba73-7d26a0b0a2b0')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ecdecc74-8383-4444-aed1-c7b814eeb4a7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ecdecc74-8383-4444-aed1-c7b814eeb4a7')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ecdecc74-8383-4444-aed1-c7b814eeb4a7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ecdecc74-8383-4444-aed1-c7b814eeb4a7')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bb6a5c21-8f60-4ad5-b421-7d7763c2e28a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bb6a5c21-8f60-4ad5-b421-7d7763c2e28a')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bb6a5c21-8f60-4ad5-b421-7d7763c2e28a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bb6a5c21-8f60-4ad5-b421-7d7763c2e28a')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','526191fe-36cf-4a90-ba82-2460a6661987')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','526191fe-36cf-4a90-ba82-2460a6661987')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','526191fe-36cf-4a90-ba82-2460a6661987')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','526191fe-36cf-4a90-ba82-2460a6661987')]).parameter_table
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

    
    # Loss Of Workability
    loss_work_name = fields.Char(default="Loss Of Workability")
    loss_work_visible = fields.Boolean(string="Loss Of Workability Visible" ,compute="_compute_visible")

    loss_work_line_ids = fields.One2many('admixture.workslump.test.line','parent_id',string='Flexural Strength Test Lines', default=lambda self: self._default_loss_work_line_ids())

    @api.model
    def _default_loss_work_line_ids(self):
        default_lines = [
            (0, 0, {'sample_no': '1'}),
            (0, 0, {'sample_no': '2'}),
            (0, 0, {'sample_no': '3'}),
        ]
        return default_lines
    

    avg_percentage_loss = fields.Float(
    string="Average % Loss of Workability",
    compute="_compute_avg_percentage_loss",
    store=True
)

    @api.depends('loss_work_line_ids.percentage_loss')
    def _compute_avg_percentage_loss(self):
     for rec in self:
        percentages = rec.loss_work_line_ids.mapped('percentage_loss')
        rec.avg_percentage_loss = (
            sum(percentages) / len(percentages)
            if percentages else 0.0
        )


    avg_percentage_loss_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_percentage_loss_confirmity")

    @api.depends('avg_percentage_loss','eln_ref','grade')
    def _compute_avg_percentage_loss_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_percentage_loss_confirmity = 'na'
                continue
            record.avg_percentage_loss_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e1b00302-8095-4db4-870a-42b431544440')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e1b00302-8095-4db4-870a-42b431544440')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_percentage_loss - record.avg_percentage_loss*mu_value
                    upper = record.avg_percentage_loss + record.avg_percentage_loss*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_percentage_loss_confirmity = 'pass'
                        break
                    else:
                        record.avg_percentage_loss_confirmity = 'fail'

    avg_percentage_loss_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_percentage_loss_nabl")

    @api.depends('avg_percentage_loss','eln_ref','grade')
    def _compute_avg_percentage_loss_nabl(self):
        
        for record in self:
            record.avg_percentage_loss_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e1b00302-8095-4db4-870a-42b431544440')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e1b00302-8095-4db4-870a-42b431544440')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_percentage_loss - record.avg_percentage_loss*mu_value
                    upper = record.avg_percentage_loss + record.avg_percentage_loss*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_percentage_loss_nabl = 'pass'
                        break
                    else:
                        record.avg_percentage_loss_nabl = 'fail'

    
    # Flow of Concrete of High Workability
    flowhigh_work_name = fields.Char(default="Flow of Concrete of High Workability")
    flowhigh_work_visible = fields.Boolean(string="Flow of Concrete of High Workability Visible" ,compute="_compute_visible")

    flowhigh_work_line_ids = fields.One2many('admixture.flow.diameter.test.line','parent_id',string='Flexural Strength Test Lines', default=lambda self: self._default_flowhigh_work_line_ids())

    @api.model
    def _default_flowhigh_work_line_ids(self):
        default_lines = [
            (0, 0, {'sample_no': '1'}),
            (0, 0, {'sample_no': '2'}),
            (0, 0, {'sample_no': '3'}),
        ]
        return default_lines
    

    avg_flow_diameter = fields.Float(
        string='Average Flow Diameter (mm)',
        compute='_compute_avg_flow_diameter',
        store=True
    )

    @api.depends('flowhigh_work_line_ids.average_flow')
    def _compute_avg_flow_diameter(self):
     for rec in self:
        flow_diameter = rec.flowhigh_work_line_ids.mapped('average_flow')
        rec.avg_flow_diameter = (
            sum(flow_diameter) / len(flow_diameter)
            if flow_diameter else 0.0
        )


    avg_flow_diameter_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_flow_diameter_confirmity")

    @api.depends('avg_flow_diameter','eln_ref','grade')
    def _compute_avg_flow_diameter_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_flow_diameter_confirmity = 'na'
                continue
            record.avg_flow_diameter_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','143209a1-768a-465e-9399-e7de8bfae482')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','143209a1-768a-465e-9399-e7de8bfae482')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_flow_diameter - record.avg_flow_diameter*mu_value
                    upper = record.avg_flow_diameter + record.avg_flow_diameter*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_flow_diameter_confirmity = 'pass'
                        break
                    else:
                        record.avg_flow_diameter_confirmity = 'fail'

    avg_flow_diameter_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_flow_diameter_nabl")

    @api.depends('avg_flow_diameter','eln_ref','grade')
    def _compute_avg_flow_diameter_nabl(self):
        
        for record in self:
            record.avg_flow_diameter_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','143209a1-768a-465e-9399-e7de8bfae482')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','143209a1-768a-465e-9399-e7de8bfae482')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_flow_diameter - record.avg_flow_diameter*mu_value
                    upper = record.avg_flow_diameter + record.avg_flow_diameter*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_flow_diameter_nabl = 'pass'
                        break
                    else:
                        record.avg_flow_diameter_nabl = 'fail'
    
    
    
    
    

    

    
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.bleeding_visible = False
            record.slump_test_visible = False
            record.compressive_strength_visible = False
            record.flexural_strength_visible = False
            record.loss_work_visible = False
            record.flowhigh_work_visible = False
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                if sample.internal_id == "5f722fd9-5698-452d-90c1-a36e837d7805":
                    record.bleeding_visible = True
                
                if sample.internal_id == "98717d5e-562d-48b6-a969-d411229301de":
                    record.slump_test_visible = True

                if sample.internal_id == "4775ab5c-6c11-4f8b-9115-7fed4a9783c9":
                    record.compressive_strength_visible = True

                if sample.internal_id == "fa874e16-57d4-4add-a60e-0916e8e7245b":
                    record.flexural_strength_visible = True

                if sample.internal_id == "e1b00302-8095-4db4-870a-42b431544440":
                    record.loss_work_visible = True

                if sample.internal_id == "143209a1-768a-465e-9399-e7de8bfae482":
                    record.flowhigh_work_visible = True

                


     
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
           # Bleeding Test
            if result.parameter.internal_id == '5f722fd9-5698-452d-90c1-a36e837d7805':
                result.result_char = round(self.avg_bleeding_percent,2)
                result.calculated = True
                if self.avg_bleeding_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Slump Test
            if result.parameter.internal_id == '98717d5e-562d-48b6-a969-d411229301de':
                result.result_char = round(self.avg_slump,2)
                result.calculated = True
                if self.avg_slump_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 3 Days Compressive Strength
            if result.parameter.internal_id == '8ec2711d-3fb4-4ff7-b903-74b31b2a5c4b':
                result.result_char = round(self.avg_3_days,2)
                result.calculated = True
                if self.avg_3_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 7 Days Compressive Strength
            if result.parameter.internal_id == '57a1b1b7-ae7a-4c60-8974-ec3e3b70c3b3':
                result.result_char = round(self.avg_7_days,2)
                result.calculated = True
                if self.avg_7_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 14 Days Compressive Strength
            if result.parameter.internal_id == 'd6927f8e-0aff-4cff-8be4-242d807fdd7b':
                result.result_char = round(self.avg_14_days,2)
                result.calculated = True
                if self.avg_14_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 28 Days Compressive Strength
            if result.parameter.internal_id == '86419a8f-580c-4ee2-91aa-2904ce7a665a':
                result.result_char = round(self.avg_28_days,2)
                result.calculated = True
                if self.avg_28_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Compressive Strength
            if result.parameter.internal_id == '4775ab5c-6c11-4f8b-9115-7fed4a9783c9':
                result.calculated = True

            # Flexural Strength
            if result.parameter.internal_id == 'fa874e16-57d4-4add-a60e-0916e8e7245b':
                result.calculated = True

            # 3 Days Flexural Strength
            if result.parameter.internal_id == 'e6c08fb2-dbd2-4e52-ba73-7d26a0b0a2b0':
                result.result_char = round(self.avg_3_days_flexural,2)
                result.calculated = True
                if self.avg_3_days_flexural_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 7 Days Flexural Strength
            if result.parameter.internal_id == 'ecdecc74-8383-4444-aed1-c7b814eeb4a7':
                result.result_char = round(self.avg_7_days_flexural,2)
                result.calculated = True
                if self.avg_7_days_flexural_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 14 Days Flexural Strength
            if result.parameter.internal_id == 'bb6a5c21-8f60-4ad5-b421-7d7763c2e28a':
                result.result_char = round(self.avg_14_days_flexural,2)
                result.calculated = True
                if self.avg_14_days_flexural_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 28 Days Flexural Strength
            if result.parameter.internal_id == '526191fe-36cf-4a90-ba82-2460a6661987':
                result.result_char = round(self.avg_28_days_flexural,2)
                result.calculated = True
                if self.avg_28_days_flexural_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Loss Of Workability
            if result.parameter.internal_id == 'e1b00302-8095-4db4-870a-42b431544440':
                result.result_char = round(self.avg_percentage_loss,2)
                result.calculated = True
                if self.avg_percentage_loss_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Flow of Concrete of High Workability
            if result.parameter.internal_id == '143209a1-768a-465e-9399-e7de8bfae482':
                result.result_char = round(self.avg_flow_diameter,2)
                result.calculated = True
                if self.avg_flow_diameter_nabl == 'pass':
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
        record = super(MechanicalAdmixture, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
    


    def get_all_fields(self):
        record = self.env['mechanical.bricks'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()

        return super(MechanicalAdmixture, self).read(fields=fields, load=load)
    
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




class AdmixtureBleedingTestLine(models.Model):
    _name = 'admixture.bleeding.test.line'
    _description = 'Admixture Bleeding Test Trial'

    parent_id = fields.Many2one('mechanical.admixture', string="Parent Id")

    sample_no = fields.Integer(string="Trial No.", readonly=True, copy=False, default=1)

    w1 = fields.Float(string="Weight of empty container, W₁ (kg)")
    w2 = fields.Float(string="Weight of container + fresh concrete, W₂ (kg)")

    net_weight = fields.Float(
        string="Net weight of concrete, W = W₂ − W₁ (kg)",
        compute='_compute_net_weight',
        store=True
    )

    volume = fields.Float(string="Volume of container, V (Lit)")
    mixing_water = fields.Float(string="Quantity of mixing water in sample (kg)")
    bleed_water_ml = fields.Float(string="Total bleed water collected, Vw (ml)")

    bleed_water_kg = fields.Float(
        string="Mass of bleed water collected (kg)",
        compute='_compute_bleed_water_kg',
        store=True,digits=(10,3)
    )

    bleeding_percent = fields.Float(
        string="Bleeding of concrete (%)",
        compute='_compute_bleeding_percent',
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_net_weight(self):
        for rec in self:
            rec.net_weight = rec.w2 - rec.w1

    @api.depends('bleed_water_ml')
    def _compute_bleed_water_kg(self):
        for rec in self:
            rec.bleed_water_kg = rec.bleed_water_ml / 1000.0

    @api.depends('bleed_water_kg', 'mixing_water')
    def _compute_bleeding_percent(self):
        for rec in self:
            rec.bleeding_percent = (
                (rec.bleed_water_kg * 100) / rec.mixing_water
                if rec.mixing_water else 0.0
            )


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(AdmixtureBleedingTestLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class AdmixtureSlumpTestLine(models.Model):
    _name = 'admixture.slump.test.line'
    _description = 'Admixture Slump Test Lines'

    parent_id = fields.Many2one('mechanical.admixture', string="Parent Id")

    sample_no = fields.Integer(string="Trial No.", readonly=True, copy=False, default=1)

    h1 = fields.Float(
        string='Height of slump cone, H₁ (mm)'
    )

    h2 = fields.Float(
        string='Height of concrete after subsidence, H₂ (mm)'
    )

    slump_value = fields.Float(
        string='Slump Value = H₁ − H₂ (mm)',
        compute='_compute_slump',
        store=True
    )

    slump_type = fields.Selection([
        ('true', 'True'),
        ('shear', 'Shear'),
        ('collapse', 'Collapse')
    ], string='Type of Slump')

    test_time = fields.Float(
        string='Time of Test after Water Addition (min)'
    )

    @api.depends('h1', 'h2')
    def _compute_slump(self):
        for rec in self:
            rec.slump_value = rec.h1 - rec.h2


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(AdmixtureSlumpTestLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1




class AdmixtureCompressiveStrengthLine(models.Model):
    _name = 'admixture.compressive.strength.line'
    _description = 'Compressive Strength Test Lines'

    parent_id = fields.Many2one('mechanical.admixture', string="Parent Id")

    sample_no = fields.Integer(string="Trial No.", readonly=True, copy=False, default=1)

    age = fields.Char(string='Age Of Cube.')

    cube_no = fields.Char(string='Cube Identification No.')

    date_casting = fields.Date(
        string='Date of Casting',
        compute='_compute_date_casting',
        store=True
    )

    date_testing = fields.Date(
        string='Date of Testing',
        compute='_compute_date_testing',
        store=True
    )

    weight = fields.Float(string='Weight (gms)')
    volume = fields.Float(string='Volume (cc)')

    density = fields.Float(
        string='Density (gm/cc)',
        compute='_compute_density',
        store=True
    )

    load_kn = fields.Float(string='Load (kN)')

    compressive_strength = fields.Float(
        string='Compressive Strength (N/mm²)',
        compute='_compute_strength',
        store=True
    )

    @api.depends('parent_id.date_of_casting')
    def _compute_date_casting(self):
     for rec in self:
        rec.date_casting = rec.parent_id.date_of_casting

    @api.depends('date_casting', 'age')
    def _compute_date_testing(self):
     for rec in self:
        rec.date_testing = False

        if rec.date_casting and rec.age:
            try:
                # "3 Days" -> 3
                days = int(rec.age.replace('Days', '').strip())
                rec.date_testing = rec.date_casting + timedelta(days=days)
            except ValueError:
                rec.date_testing = False



    @api.depends('weight', 'volume')
    def _compute_density(self):
        for rec in self:
            rec.density = (
                rec.weight / rec.volume
                if rec.volume else 0.0
            )

    # area_of_cube = fields.Float(string="Area of Cube",compute="_compute_area_cube",store=True)

    # @api.depends('parent_id.size_id.size')
    # def _compute_area_cube(self):
    #     import re
    #     for record in self:
    #         size_str = record.parent_id.size_id.size
    #         if size_str:
    #             match = re.search(r'\d+', str(size_str))
    #             if match:
    #                 side = int(match.group())
    #                 record.area_of_cube = side * side  # or whatever formula
    #             else:
    #                 record.area_of_cube = 0
    #         else:
    #             record.area_of_cube = 0

   

    @api.depends(
    'load_kn',
    'parent_id.eln_ref.size_id',
    'parent_id.eln_ref.size_id.size'
)
    def _compute_strength(self):
     import re

     for record in self:
        record.compressive_strength = 0.0

        size_str = record.parent_id.eln_ref.size_id.size

        if record.load_kn and size_str:
            match = re.search(r'(\d+)', str(size_str))
            if match:
                side = float(match.group(1))
                area = side * side
                record.compressive_strength = (
                    record.load_kn * 1000
                ) / area


class AdmixtureFlexuralStrengthLine(models.Model):
    _name = 'admixture.flexural.strength.line'
    _description = 'Flexural Strength Line'

    parent_id = fields.Many2one('mechanical.admixture',string='Parent')

    age = fields.Char(string='Age Of Beam')

    weight = fields.Float(string='Weight (Kg)')
    volume = fields.Float(string='Volume (cm³)')

    density = fields.Float(
        string='Density (g/cc)',
        compute='_compute_density',
        store=True
    )

    test_area = fields.Float(string="Test Area (mm²)",compute="_compute_test_area",store=True)

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

    @api.depends('parent_id.size_id.size')
    def _compute_test_area(self):
     import re

     for record in self:
        record.test_area = 0.0

        size_str = record.parent_id.size_id.size

        if size_str:
            match = re.search(r'\d+', str(size_str))

            if match:
                side = int(match.group())
                record.test_area = side * side




    @api.depends('load_kn', 'test_area', 'parent_id.span_length')
    def _compute_flexural_strength(self):
     import re

     for rec in self:
        rec.flexural_strength = 0.0

        size_str = rec.parent_id.size_id.size

        if size_str:
            match = re.search(r'\d+', str(size_str))

            if match:
                depth = float(match.group())  # 150

                P = rec.load_kn * 1000
                L = rec.parent_id.span_length
                A = rec.test_area

                if P and L and A:
                    rec.flexural_strength = (
                        P * L
                    ) / (
                        A * depth
                    )


    

    # @api.depends('load_kn','parent_id.span_length','parent_id.beam_width','parent_id.beam_depth')
    # def _compute_flexural_strength(self):
    #  for rec in self:

    #     P = rec.load_kn * 1000
    #     L = rec.parent_id.span_length
    #     B = rec.parent_id.beam_width
    #     D = rec.parent_id.beam_depth

    #     if P and L and B and D:
    #         rec.flexural_strength = (
    #             P * L
    #         ) / (
    #             B * (D ** 2)
    #         )
    #     else:
    #         rec.flexural_strength = 0.0


class AdmixtureWorkSlumpTestLine(models.Model):
    _name = 'admixture.workslump.test.line'
    _description = ' Work Slump Test Line'

    parent_id = fields.Many2one('mechanical.admixture', string="Parent Id")

    sample_no = fields.Integer(string="Trial No.", readonly=True, copy=False, default=1)

    slump_0 = fields.Float(string='Initial Slump at 0 Minutes (mm)')
    slump_30 = fields.Float(string='Slump at 30 Minutes (mm)')
    slump_60 = fields.Float(string='Slump at 60 Minutes (mm)')
    slump_90 = fields.Float(string='Slump at 90 Minutes (mm)')
    slump_120 = fields.Float(string='Slump at 120 Minutes (mm)')

    loss_workability = fields.Float(string="Loss of Workability (mm)	",
        compute='_compute_loss',
        store=True
    )

    percentage_loss = fields.Float(string="Percentage Loss of Workability (%)",
        compute='_compute_loss',
        store=True
    )

    @api.depends('slump_0', 'slump_120')
    def _compute_loss(self):
        for rec in self:
            rec.loss_workability = rec.slump_0 - rec.slump_120

            rec.percentage_loss = (
                ((rec.slump_0 - rec.slump_120) / rec.slump_0) * 100
                if rec.slump_0 else 0
            )


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(AdmixtureWorkSlumpTestLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class AdmixtureFlowDiameterTestLine(models.Model):
    _name = 'admixture.flow.diameter.test.line'
    _description = 'Flow of Concrete of High Workability Lines'

    parent_id = fields.Many2one('mechanical.admixture', string="Parent Id")

    sample_no = fields.Integer(string="Trial No.", readonly=True, copy=False, default=1)

    flow_0 = fields.Float('Initial Flow Diameter at 0 Minutes (mm)')
    flow_30 = fields.Float('Flow Diameter at 30 Minutes (mm)')
    flow_60 = fields.Float('Flow Diameter at 60 Minutes (mm)')
    flow_90 = fields.Float('Flow Diameter at 90 Minutes (mm)')
    flow_120 = fields.Float('Flow Diameter at 120 Minutes (mm)')

    average_flow = fields.Float(
        string="Average Flow Diameter (mm) ",
        compute="_compute_average_flow",
        store=True
    )

    @api.depends('flow_0', 'flow_30', 'flow_60', 'flow_90', 'flow_120')
    def _compute_average_flow(self):
        for rec in self:
            values = [
                rec.flow_0,
                rec.flow_30,
                rec.flow_60,
                rec.flow_90,
                rec.flow_120
            ]
            rec.average_flow = sum(values) / 5 if values else 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(AdmixtureFlowDiameterTestLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class MechanicalAdmixtureNotes(models.Model):
    _name = "mechanical.admixture.notes"

    parent_id = fields.Many2one('mechanical.admixture',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")


    