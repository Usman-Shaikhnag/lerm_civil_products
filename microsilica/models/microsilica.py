from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math
from statistics import mean
from math import sqrt



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


    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")
    date_of_testing = fields.Date(string="Date of Testing",compute="_compute_date_testing")

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    @api.depends('eln_ref')
    def _compute_date_testing(self):
        if self.eln_ref:
            self.date_of_testing = self.eln_ref.date_testing
        else:
            self.date_of_testing = ''

    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None


    temp = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)






    
    def prefill_data(self):
        # import wdb; wdb.set_trace()
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




     #  FINENESS BY WET SIEVING ( 45 MICRON ) 

    particles_retained_name = fields.Char("Name",default="Fineness By Wet Sieving (Sieve Size in mm-0.045mm)")
    particles_retained_visible = fields.Boolean("Particles retained Visible",compute="_compute_visible")

    particles_retained_line_ids = fields.One2many(
        "microsilica.particles.retained.line",
        "parent_id",
        string="Trials"
    )

    avg_percentage_passing = fields.Float(
        string="Average Percentage Passing",
        compute="_compute_avg_percentage_passing",
        store=True,
        digits=(16, 2)
    )

    @api.depends("particles_retained_line_ids.percentage_passing")
    def _compute_avg_percentage_passing(self):
        for rec in self:
            values = rec.particles_retained_line_ids.mapped("percentage_passing")
            rec.avg_percentage_passing = (
                round(sum(values) / len(values), 2)
                if values else 0.0
            )


    avg_percentage_passing_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_percentage_passing_conformity", store=True)

    @api.depends('avg_percentage_passing','eln_ref','grade')
    def _compute_avg_percentage_passing_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_percentage_passing_conformity = 'na'
                continue
            record.avg_percentage_passing_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','52147fgtre-5f8c-44a2-984b-6ad2a17d250c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','52147fgtre-5f8c-44a2-984b-6ad2a17d250c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_percentage_passing - record.avg_percentage_passing*mu_value
                    upper = record.avg_percentage_passing + record.avg_percentage_passing*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_percentage_passing_conformity = 'pass'
                        break
                    else:
                        record.avg_percentage_passing_conformity = 'fail'

    avg_percentage_passing_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_percentage_passing_nabl", store=True)
    
    @api.depends('avg_percentage_passing','eln_ref','grade')
    def _compute_avg_percentage_passing_nabl(self):
        
        for record in self:
            record.avg_percentage_passing_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','52147fgtre-5f8c-44a2-984b-6ad2a17d250c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','52147fgtre-5f8c-44a2-984b-6ad2a17d250c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.avg_percentage_passing - record.avg_percentage_passing*mu_value
                  upper = record.avg_percentage_passing + record.avg_percentage_passing*mu_value
                  if lower >= lab_min and upper <= lab_max:
                     record.avg_percentage_passing_nabl = 'pass'
                     break
                  else:
                     record.avg_percentage_passing_nabl = 'fail'


    percentage_passing_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    percentage_passing_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_percentage_passing_final_report", store=True)
    
    @api.depends('avg_percentage_passing_nabl', 'percentage_passing_report_type')
    def _compute_percentage_passing_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.percentage_passing_report_type == 'nabl':
                rec.percentage_passing_final_report = 'nabl'
    
            elif rec.percentage_passing_report_type == 'non_nabl':
                rec.percentage_passing_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.avg_percentage_passing_nabl == 'pass':
                    rec.percentage_passing_final_report = 'nabl'
                else:
                    rec.percentage_passing_final_report = 'non_nabl'



    # Compressive Strength Of Micro Silica

    compressive_name = fields.Char("Name",default="Compressive Strength Of Micro Silica")
    compressive_visible = fields.Boolean("Compressive Strength Of Micro Silica Visible",compute="_compute_visible")

    compressive_lines = fields.One2many('microsilica.compressive.line','parent_id',string="Compressive",default=lambda self: self.compressive_lines_days())

    @api.model
    def compressive_lines_days(self):
        default_lines = [
            
            (0, 0, {'days': '7 Days'}),
            (0, 0, {'days': '7 Days'}),
            (0, 0, {'days': '7 Days'}),
            (0, 0, {'days': '14 Days'}),
            (0, 0, {'days': '14 Days'}),
            (0, 0, {'days': '14 Days'}),
            (0, 0, {'days': '28 Days'}),
            (0, 0, {'days': '28 Days'}),
            (0, 0, {'days': '28 Days'}),
            
        ]
        return default_lines 

    @api.onchange('start_date', 'compressive_lines')
    def _onchange_start_date_or_lines(self):
        for line in self.compressive_lines:
            if not line.dt_of_casting:  
                line.dt_of_casting = self.start_date

    

    avg_7_days = fields.Float(string="Avg Compressive Strength (7 Days)", compute="_compute_avg_strengths", store=True)

    avg_14_days = fields.Float(string="Avg Compressive Strength (14 Days)", compute="_compute_avg_strengths", store=True)

    avg_28_days = fields.Float(string="Avg Compressive Strength (28 Days)", compute="_compute_avg_strengths", store=True)


    @api.depends('compressive_lines.days', 'compressive_lines.compressive_strength')
    def _compute_avg_strengths(self):
        for rec in self:
            
            strengths_7 = [line.compressive_strength for line in rec.compressive_lines if line.days == '7 Days' and line.compressive_strength]

            strengths_14 = [line.compressive_strength for line in rec.compressive_lines if line.days == '14 Days' and line.compressive_strength]
            
            strengths_28 = [line.compressive_strength for line in rec.compressive_lines if line.days == '28 Days' and line.compressive_strength]

            
            rec.avg_7_days = mean(strengths_7) if strengths_7 else 0.0
            rec.avg_14_days = mean(strengths_14) if strengths_14 else 0.0
            rec.avg_28_days = mean(strengths_28) if strengths_28 else 0.0

    

    

    avg_7_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_7_days_confirmity")
    
    @api.depends('avg_7_days','eln_ref','grade')
    def _compute_avg_7_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_7_days_confirmity = 'na'
                continue
            record.avg_7_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658874seqa-bfaf-4667-aca6-b69c321af63b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658874seqa-bfaf-4667-aca6-b69c321af63b')]).parameter_table
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
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_7_days_nabl",store=True)

    @api.depends('avg_7_days','eln_ref','grade')
    def _compute_avg_7_days_nabl(self):
        
        for record in self:
            record.avg_7_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658874seqa-bfaf-4667-aca6-b69c321af63b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658874seqa-bfaf-4667-aca6-b69c321af63b')]).parameter_table
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

    avg_7_days_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_7_days_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_7_days_final_report", store=True)

    @api.depends('avg_7_days_nabl', 'avg_7_days_report_type')
    def _compute_avg_7_days_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_7_days_report_type == 'nabl':
            rec.avg_7_days_final_report = 'nabl'

        elif rec.avg_7_days_report_type == 'non_nabl':
            rec.avg_7_days_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_7_days_nabl == 'pass':
                rec.avg_7_days_final_report = 'nabl'
            else:
                rec.avg_7_days_final_report = 'non_nabl'  


    avg_14_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_14_days_confirmity")
    
    @api.depends('avg_14_days','eln_ref','grade')
    def _compute_avg_14_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_14_days_confirmity = 'na'
                continue
            record.avg_14_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14785dfrte-42b6-4d86-9ac7-a2758b3f4e5a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14785dfrte-42b6-4d86-9ac7-a2758b3f4e5a')]).parameter_table
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
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_14_days_nabl",store=True)

    @api.depends('avg_14_days','eln_ref','grade')
    def _compute_avg_14_days_nabl(self):
        
        for record in self:
            record.avg_14_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14785dfrte-42b6-4d86-9ac7-a2758b3f4e5a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14785dfrte-42b6-4d86-9ac7-a2758b3f4e5a')]).parameter_table
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


    avg_14_days_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_14_days_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_14_days_final_report", store=True)

    @api.depends('avg_14_days_nabl', 'avg_14_days_report_type')
    def _compute_avg_14_days_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_14_days_report_type == 'nabl':
            rec.avg_14_days_final_report = 'nabl'

        elif rec.avg_14_days_report_type == 'non_nabl':
            rec.avg_14_days_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_14_days_nabl == 'pass':
                rec.avg_14_days_final_report = 'nabl'
            else:
                rec.avg_14_days_final_report = 'non_nabl'  


    avg_28_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_28_days_confirmity")
    
    @api.depends('avg_28_days','eln_ref','grade')
    def _compute_avg_28_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_28_days_confirmity = 'na'
                continue
            record.avg_28_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d62e47c1-64b1-4589-b412-677f1e21377b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d62e47c1-64b1-4589-b412-677f1e21377b')]).parameter_table
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
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_28_days_nabl",store=True)

    @api.depends('avg_28_days','eln_ref','grade')
    def _compute_avg_28_days_nabl(self):
        
        for record in self:
            record.avg_28_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d62e47c1-64b1-4589-b412-677f1e21377b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d62e47c1-64b1-4589-b412-677f1e21377b')]).parameter_table
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

            
    avg_28_days_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_28_days_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_28_days_final_report", store=True)

    @api.depends('avg_28_days_nabl', 'avg_28_days_report_type')
    def _compute_avg_28_days_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_28_days_report_type == 'nabl':
            rec.avg_28_days_final_report = 'nabl'

        elif rec.avg_28_days_report_type == 'non_nabl':
            rec.avg_28_days_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_28_days_nabl == 'pass':
                rec.avg_28_days_final_report = 'nabl'
            else:
                rec.avg_28_days_final_report = 'non_nabl'


    # SPECIFIC GRAVITY OF Micro Silica

    specific_gravity_name = fields.Char("Name",default="Specific Gravity of Micro Silica")
    specific_gravity_visible = fields.Boolean("Specific Gravity of Micro Silica Visible",compute="_compute_visible")

    specific_gravity_line_ids = fields.One2many(
        "microsilica.specific.gravity.line",
        "parent_id",
        string="Trial Lines",
    )

    average_specific_gravity = fields.Float(
        string="Average Specific Gravity",
        compute="_compute_average_specific_gravity",
        store=True,
    )

    @api.depends("specific_gravity_line_ids.specific_gravity")
    def _compute_average_specific_gravity(self):
        for rec in self:
            values = rec.specific_gravity_line_ids.mapped("specific_gravity")
            values = [v for v in values if v]

            if values:
                rec.average_specific_gravity = sum(values) / len(values)
            else:
                rec.average_specific_gravity = 0.0


    average_specific_gravity_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_average_specific_gravity_confirmity")
    
    @api.depends('average_specific_gravity','eln_ref','grade')
    def _compute_average_specific_gravity_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_specific_gravity_confirmity = 'na'
                continue
            record.average_specific_gravity_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658fgtrcd-80ef-4de0-96ba-a279f27b9ede')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658fgtrcd-80ef-4de0-96ba-a279f27b9ede')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_specific_gravity - record.average_specific_gravity*mu_value
                    upper = record.average_specific_gravity + record.average_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_specific_gravity_confirmity = 'pass'
                        break
                    else:
                        record.average_specific_gravity_confirmity = 'fail'

    average_specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_average_specific_gravity_nabl",store=True)

    @api.depends('average_specific_gravity','eln_ref','grade')
    def _compute_average_specific_gravity_nabl(self):
        
        for record in self:
            record.average_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658fgtrcd-80ef-4de0-96ba-a279f27b9ede')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658fgtrcd-80ef-4de0-96ba-a279f27b9ede')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_specific_gravity - record.average_specific_gravity*mu_value
                    upper = record.average_specific_gravity + record.average_specific_gravity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_specific_gravity_nabl = 'pass'
                        break
                    else:
                        record.average_specific_gravity_nabl = 'fail'

    specific_gravity_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    specific_gravity_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_specific_gravity_final_report", store=True)

    @api.depends('average_specific_gravity_nabl', 'specific_gravity_report_type')
    def _compute_specific_gravity_final_report(self):
     for rec in self:

        # Manual override
        if rec.specific_gravity_report_type == 'nabl':
            rec.specific_gravity_final_report = 'nabl'

        elif rec.specific_gravity_report_type == 'non_nabl':
            rec.specific_gravity_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.average_specific_gravity_nabl == 'pass':
                rec.specific_gravity_final_report = 'nabl'
            else:
                rec.specific_gravity_final_report = 'non_nabl'

   
    
    

    # Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):

        for record in self:
            record.particles_retained_visible = False
            record.compressive_visible = False
            record.specific_gravity_visible = False

        
    



        for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                # import wdb;wdb.set_trace()


                # particles retained
                if sample.internal_id == '52147fgtre-5f8c-44a2-984b-6ad2a17d250c':
                    record.particles_retained_visible = True

                if sample.internal_id == '658798cvfd-889b-477c-a355-0476f6bcd0d7':
                    record.compressive_visible = True

                if sample.internal_id == '658fgtrcd-80ef-4de0-96ba-a279f27b9ede':
                    record.specific_gravity_visible = True


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()


            # FINENESS BY WET SIEVING ( 45 MICRON ) 
            if result.parameter.internal_id == '52147fgtre-5f8c-44a2-984b-6ad2a17d250c':
                result.result_char = round(self.avg_percentage_passing,2)
                result.calculated = True
                if self.avg_percentage_passing_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            
            # Compressive Strength
            if result.parameter.internal_id == '658798cvfd-889b-477c-a355-0476f6bcd0d7':
                result.calculated = True

            # Compressive Strength (7 Days)
            if result.parameter.internal_id == '658874seqa-bfaf-4667-aca6-b69c321af63b':
                result.result_char = round(self.avg_7_days,2)
                result.calculated = True
                if self.avg_7_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Compressive Strength (14 Days)
            if result.parameter.internal_id == '14785dfrte-42b6-4d86-9ac7-a2758b3f4e5a':
                result.result_char = round(self.avg_14_days,2)
                result.calculated = True
                if self.avg_14_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Compressive Strength (28 Days)
            if result.parameter.internal_id == 'd62e47c1-64b1-4589-b412-677f1e21377b':
                result.result_char = round(self.avg_28_days,2)
                result.calculated = True
                if self.avg_28_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # SPECIFIC GRAVITY OF Micro Silica							
            if result.parameter.internal_id == '658fgtrcd-80ef-4de0-96ba-a279f27b9ede':
                result.result_char = round(self.average_specific_gravity,2)
                result.calculated = True
                if self.average_specific_gravity_nabl == 'pass':
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
        record = super(Microsilica, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
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
        record = self.env['mechanical.microsilica'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


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

    
class MSParticlesRetainedLine(models.Model):
    _name= "microsilica.particles.retained.line"

    parent_id = fields.Many2one('mechanical.microsilica', string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)

    weight_sample = fields.Float(
        string="Weight of Sample (Ws)"
    )

    weight_residue = fields.Float(
        string="Weight of Residue Retained (Wr)"
    )

    weight_material_passing = fields.Float(
        string="Weight of Material Passing (Ws - Wr)",
        compute="_compute_values",
        store=True,
        digits=(16, 2)
    )

    percentage_passing = fields.Float(
        string="Percentage of Material Passing",
        compute="_compute_values",
        store=True,
        digits=(16, 2)
    )

    @api.depends("weight_sample", "weight_residue")
    def _compute_values(self):
        for rec in self:

            rec.weight_material_passing = (
                rec.weight_sample - rec.weight_residue
            )

            if rec.weight_sample:
                rec.percentage_passing = round(
                    (rec.weight_material_passing / rec.weight_sample) * 100,
                    2
                )
            else:
                rec.percentage_passing = 0.0



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MSParticlesRetainedLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class MSCompressiveCementLine(models.Model):
    _name = "microsilica.compressive.line"
    parent_id = fields.Many2one('mechanical.microsilica', string="Parent Id")

    serial_no = fields.Integer(string="Specimen No", readonly=True, copy=False, default=1)

   
    
    dt_of_casting = fields.Date(string="Date of Casting ")
    days = fields.Char(string="Age in Days")
    dt_of_testing = fields.Date(string="Date of Testing")
    wt_of_cube = fields.Float(string="Weight (g)")
    density = fields.Float(string="Density (g/cc)",compute="_compute_density",store=True)
    area = fields.Float(string="Area",compute="_compute_area",store=True)
    load = fields.Float(string="Load at Failure (kN)")
    compressive_strength = fields.Float(string="Compressive Strength of Individual Sample (f1) in (N/mm2)",compute="_compute_strength")

    

    @api.onchange('days')
    def _onchange_days_set_testing_date(self):
        if self.dt_of_casting and self.days:
            self.dt_of_testing = self.dt_of_casting + timedelta(days=self.days)
        else:
            self.dt_of_testing = False

    @api.depends('parent_id')
    def _compute_area(self):
        for rec in self:
            rec.area = 70.6 * 70.6

    

    @api.depends('wt_of_cube')
    def _compute_density(self):
      volume = 7.06 * 7.06 * 7.06  

      for rec in self:
        rec.density = (rec.wt_of_cube or 0.0) / volume

    @api.depends('load', 'area')
    def _compute_strength(self):
        for rec in self:
            if rec.area:
                rec.compressive_strength = (rec.load * 1000) / rec.area
            else:
                rec.compressive_strength = 0.0




    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(MSCompressiveCementLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class MSSpecificGravityLine(models.Model):
    _name = "microsilica.specific.gravity.line"
    _description = "Specific Gravity Trial"

    parent_id = fields.Many2one('mechanical.microsilica', string="Parent Id")

    serial_no = fields.Integer(string="Trail No.", readonly=True, copy=False, default=1)

    weight_cement = fields.Float(string="Weight of Micro Silica Sample W1 in (g)")

    initial_reading = fields.Float(string="Initial Reading of Flask V1 in (ml)")

    final_reading = fields.Float(string="Final Reading of Flask V2 in (ml)")

    volume_cement = fields.Float(string="Volume of Micro Silica (V2 - V1)",compute="_compute_values",store=True,)

    weight_equal_volume_water = fields.Float(string="Weight of Equal Volume of water=(V2-V1)xSpecific gravity of Water	",compute="_compute_values",store=True,)

    specific_gravity = fields.Float(string="Sp. Gravity of Micro Silica =W1/Weight of equal volume of Water",compute="_compute_values",store=True,)

    @api.depends(
        "weight_cement",
        "initial_reading",
        "final_reading",
    )
    def _compute_values(self):
        for rec in self:

            rec.volume_cement = (
                rec.final_reading - rec.initial_reading
            )

            # Specific gravity of water = 1 g/ml
            rec.weight_equal_volume_water = rec.volume_cement * 1.0

            if rec.weight_equal_volume_water:
                rec.specific_gravity = (
                    rec.weight_cement /
                    rec.weight_equal_volume_water
                )
            else:
                rec.specific_gravity = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(MSSpecificGravityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1





class MicrosilicaNotes(models.Model):
    _name = "mechanical.microsilica.notes"

    parent_id = fields.Many2one('mechanical.microsilica', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
