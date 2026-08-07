from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math

import logging
_logger = logging.getLogger(__name__)



class PaverBlock(models.Model):
    _name = "mechanical.paver.block"
    _inherit = "lerm.eln"
    _rec_name = "name_paver"


    name_paver = fields.Char("Name",default="Paver Block")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    temp = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    

    # Compressive Strength 
    commpressive_name = fields.Char("Name",default="Compressive Strength")
    commpressive_visible = fields.Boolean("Plan Area Visible",compute="_compute_visible")

    commpressive_child_lines = fields.One2many('paver.compressive.line','parent_id',string="Compressive Line")

    avg_commpressive = fields.Float(
        string="Average Corrected Strength",
        compute="_compute_avg_commpressive",
        store=True
    )

    @api.depends('commpressive_child_lines.corrected_strength')
    def _compute_avg_commpressive(self):
        for rec in self:
            values = rec.commpressive_child_lines.mapped('corrected_strength')
            rec.avg_commpressive = sum(values) / len(values) if values else 0

    

    avg_commpressive_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Compressive Strength Conformity", compute="_compute_avg_commpressive_conformity", store=True)

    @api.depends('avg_commpressive','eln_ref','grade')
    def _compute_avg_commpressive_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_commpressive_conformity = 'na'
                continue
            record.avg_commpressive_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457fgrtt-5dc9-4a2a-8bf0-1281d1865a11')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457fgrtt-5dc9-4a2a-8bf0-1281d1865a11')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_commpressive - record.avg_commpressive*mu_value
                    upper = record.avg_commpressive + record.avg_commpressive*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_commpressive_conformity = 'pass'
                        break
                    else:
                        record.avg_commpressive_conformity = 'fail'

    avg_commpressive_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Compressive Strength NABL", compute="_compute_avg_commpressive_nabl", store=True)

    @api.depends('avg_commpressive','eln_ref','grade')
    def _compute_avg_commpressive_nabl(self):
        
        for record in self:
            record.avg_commpressive_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457fgrtt-5dc9-4a2a-8bf0-1281d1865a11')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457fgrtt-5dc9-4a2a-8bf0-1281d1865a11')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_commpressive - record.avg_commpressive*mu_value
                    upper = record.avg_commpressive + record.avg_commpressive*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_commpressive_nabl = 'pass'
                        break
                    else:
                        record.avg_commpressive_nabl = 'fail'

    commpressive_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    commpressive_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_commpressive_final_report", store=True)

    @api.depends('avg_commpressive_nabl', 'commpressive_report_type')
    def _compute_commpressive_final_report(self):
     for rec in self:

        # Manual override
        if rec.commpressive_report_type == 'nabl':
            rec.commpressive_final_report = 'nabl'

        elif rec.commpressive_report_type == 'non_nabl':
            rec.commpressive_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_commpressive_nabl == 'pass':
                rec.commpressive_final_report = 'nabl'
            else:
                rec.commpressive_final_report = 'non_nabl'

    

    #  Water Absorption

    water_absorption_name = fields.Char("Name",default="Water Absorption ")
    water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")

    water_absorption_child_lines = fields.One2many('paver.water.absorption.line','parent_id',string="Water Line")

    avg_water_absorption = fields.Float(
        string="Avg. Water Absorption (%)",
        compute="_compute_avg_water_absorption", store=True
    )

    @api.depends('water_absorption_child_lines.water_absorption')
    def _compute_avg_water_absorption(self):
        for rec in self:
            lines = rec.water_absorption_child_lines
            if lines:
                total = sum(line.water_absorption for line in lines)
                rec.avg_water_absorption = round(total / len(lines), 2)
            else:
                rec.avg_water_absorption = 0.0

    avg_water_absorption_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_water_absorption_conformity", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_water_absorption_conformity = 'na'
                continue
            record.avg_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147fgrr-eba3-4f15-b33d-679b39f7372e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147fgrr-eba3-4f15-b33d-679b39f7372e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_water_absorption - record.avg_water_absorption*mu_value
                    upper = record.avg_water_absorption + record.avg_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_water_absorption_conformity = 'pass'
                        break
                    else:
                        record.avg_water_absorption_conformity = 'fail'

    avg_water_absorption_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_water_absorption_nabl", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_nabl(self):
        
        for record in self:
            record.avg_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147fgrr-eba3-4f15-b33d-679b39f7372e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147fgrr-eba3-4f15-b33d-679b39f7372e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_water_absorption - record.avg_water_absorption*mu_value
                    upper = record.avg_water_absorption + record.avg_water_absorption*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_water_absorption_nabl = 'pass'
                        break
                    else:
                        record.avg_water_absorption_nabl = 'fail'


    water_absorption_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    water_absorption_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_water_absorption_final_report", store=True)

    @api.depends('avg_water_absorption_nabl', 'water_absorption_report_type')
    def _compute_water_absorption_final_report(self):
     for rec in self:

        # Manual override
        if rec.water_absorption_report_type == 'nabl':
            rec.water_absorption_final_report = 'nabl'

        elif rec.water_absorption_report_type == 'non_nabl':
            rec.water_absorption_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_water_absorption_nabl == 'pass':
                rec.water_absorption_final_report = 'nabl'
            else:
                rec.water_absorption_final_report = 'non_nabl'


    # Plan Area
    plan_area_name = fields.Char("Name",default="Plan Area")
    plan_area_visible = fields.Boolean("Plan Area Visible",compute="_compute_visible")

    plan_area_child_lines = fields.One2many('mechanical.plan.area.paver.line','parent_id',string="Dimension")


    average_plan_area = fields.Float(
        string="Average Plan Area (mm²)",
        compute="_compute_average_plan_area",
        store=True,
    )

    @api.depends("plan_area_child_lines.plan_area")
    def _compute_average_plan_area(self):
        for rec in self:
            values = rec.plan_area_child_lines.mapped("plan_area")
            rec.average_plan_area = (
                sum(values) / len(values) if values else 0.0
            )

    average_plan_area_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_average_plan_area_conformity", store=True)

    @api.depends('average_plan_area','eln_ref','grade')
    def _compute_average_plan_area_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_plan_area_conformity = 'na'
                continue
            record.average_plan_area_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23547trew-199c-497a-b3a7-45023c604673')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23547trew-199c-497a-b3a7-45023c604673')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_plan_area - record.average_plan_area*mu_value
                    upper = record.average_plan_area + record.average_plan_area*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_plan_area_conformity = 'pass'
                        break
                    else:
                        record.average_plan_area_conformity = 'fail'

    average_plan_area_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_plan_area_nabl", store=True)

    @api.depends('average_plan_area','eln_ref','grade')
    def _compute_average_plan_area_nabl(self):
        
        for record in self:
            record.average_plan_area_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23547trew-199c-497a-b3a7-45023c604673')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23547trew-199c-497a-b3a7-45023c604673')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_plan_area - record.average_plan_area*mu_value
                    upper = record.average_plan_area + record.average_plan_area*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_plan_area_nabl = 'pass'
                        break
                    else:
                        record.average_plan_area_nabl = 'fail'

    plan_area_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    plan_area_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_plan_area_final_report", store=True)

    @api.depends('average_plan_area_nabl', 'plan_area_report_type')
    def _compute_plan_area_final_report(self):
     for rec in self:

        # Manual override
        if rec.plan_area_report_type == 'nabl':
            rec.plan_area_final_report = 'nabl'

        elif rec.plan_area_report_type == 'non_nabl':
            rec.plan_area_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.average_plan_area_nabl == 'pass':
                rec.plan_area_final_report = 'nabl'
            else:
                rec.plan_area_final_report = 'non_nabl'


    # Dimension
    dimension_name = fields.Char("Name",default=" Dimension")
    dimension_visible = fields.Boolean("Dimension Visible",compute="_compute_visible")

    dimension_child_lines = fields.One2many('paver.dimension.line','parent_id',string="Dimension")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5017ba7f-4c47-47a4-a592-ae725639d748')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5017ba7f-4c47-47a4-a592-ae725639d748')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5017ba7f-4c47-47a4-a592-ae725639d748')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5017ba7f-4c47-47a4-a592-ae725639d748')]).parameter_table
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

    avg_length_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_length_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_length_final_report", store=True)

    @api.depends('avg_length_nabl', 'avg_length_report_type')
    def _compute_avg_length_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_length_report_type == 'nabl':
            rec.avg_length_final_report = 'nabl'

        elif rec.avg_length_report_type == 'non_nabl':
            rec.avg_length_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_length_nabl == 'pass':
                rec.avg_length_final_report = 'nabl'
            else:
                rec.avg_length_final_report = 'non_nabl'

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cd59c3c7-0fe0-4bba-89f8-73ee2f5220fe')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cd59c3c7-0fe0-4bba-89f8-73ee2f5220fe')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cd59c3c7-0fe0-4bba-89f8-73ee2f5220fe')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cd59c3c7-0fe0-4bba-89f8-73ee2f5220fe')]).parameter_table
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

    avg_width_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_width_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_width_final_report", store=True)

    @api.depends('avg_width_nabl', 'avg_width_report_type')
    def _compute_avg_width_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_width_report_type == 'nabl':
            rec.avg_width_final_report = 'nabl'

        elif rec.avg_width_report_type == 'non_nabl':
            rec.avg_width_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_width_nabl == 'pass':
                rec.avg_width_final_report = 'nabl'
            else:
                rec.avg_width_final_report = 'non_nabl'

    
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a2c29ed3-a821-49ff-a1d1-a6553782600e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a2c29ed3-a821-49ff-a1d1-a6553782600e')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a2c29ed3-a821-49ff-a1d1-a6553782600e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a2c29ed3-a821-49ff-a1d1-a6553782600e')]).parameter_table
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

    avg_height_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_height_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_height_final_report", store=True)

    @api.depends('avg_height_nabl', 'avg_height_report_type')
    def _compute_avg_height_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_height_report_type == 'nabl':
            rec.avg_height_final_report = 'nabl'

        elif rec.avg_height_report_type == 'non_nabl':
            rec.avg_height_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_height_nabl == 'pass':
                rec.avg_height_final_report = 'nabl'
            else:
                rec.avg_height_final_report = 'non_nabl'


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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5dbec664-682a-400a-bdc6-c3c2435671ae')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5dbec664-682a-400a-bdc6-c3c2435671ae')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5dbec664-682a-400a-bdc6-c3c2435671ae')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5dbec664-682a-400a-bdc6-c3c2435671ae')]).parameter_table
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


    avg_area_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_area_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_area_final_report", store=True)

    @api.depends('avg_area_nabl', 'avg_area_report_type')
    def _compute_avg_area_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_area_report_type == 'nabl':
            rec.avg_area_final_report = 'nabl'

        elif rec.avg_area_report_type == 'non_nabl':
            rec.avg_area_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_area_nabl == 'pass':
                rec.avg_area_final_report = 'nabl'
            else:
                rec.avg_area_final_report = 'non_nabl'


    








 ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.commpressive_visible = False
            record.water_absorption_visible = False
            record.plan_area_visible = False
            record.dimension_visible = False
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                

                if sample.internal_id == "1457fgrtt-5dc9-4a2a-8bf0-1281d1865a11":
                    record.commpressive_visible = True
                
                if sample.internal_id == "2147fgrr-eba3-4f15-b33d-679b39f7372e":
                    record.water_absorption_visible = True

                if sample.internal_id == "23547trew-199c-497a-b3a7-45023c604673":
                    record.plan_area_visible = True

                if sample.internal_id == "058b7e8d-c146-409f-8e75-e574960c5208":
                    record.dimension_visible = True

               

      

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()
            


           
             # Compressive Strength
            if result.parameter.internal_id == '1457fgrtt-5dc9-4a2a-8bf0-1281d1865a11':
                result.calculated = True
                result.result_char = round(self.avg_commpressive,2)
                if self.avg_commpressive_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            
            # Water Absorption
            if result.parameter.internal_id == '2147fgrr-eba3-4f15-b33d-679b39f7372e':
                result.calculated = True
                result.result_char = round(self.avg_water_absorption,2)
                if self.avg_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Plan Area
            if result.parameter.internal_id == '23547trew-199c-497a-b3a7-45023c604673':
                result.calculated = True
                result.result_char = round(self.average_plan_area,2)
                if self.average_plan_area_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Dimension
            if result.parameter.internal_id == '058b7e8d-c146-409f-8e75-e574960c5208':
                result.calculated = True

            # Length
            if result.parameter.internal_id == '5017ba7f-4c47-47a4-a592-ae725639d748':
                result.calculated = True
                result.result_char = round(self.avg_length,2)
                if self.avg_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Width
            if result.parameter.internal_id == 'cd59c3c7-0fe0-4bba-89f8-73ee2f5220fe':
                result.calculated = True
                result.result_char = round(self.avg_width,2)
                if self.avg_width_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Height
            if result.parameter.internal_id == 'a2c29ed3-a821-49ff-a1d1-a6553782600e':
                result.calculated = True
                result.result_char = round(self.avg_height,2)
                if self.avg_height_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Cross Sectional Area
            if result.parameter.internal_id == '5dbec664-682a-400a-bdc6-c3c2435671ae':
                result.calculated = True
                result.result_char = round(self.avg_area,2)
                if self.avg_area_nabl == 'pass':
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
        record = super(PaverBlock, self).create(vals)
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
        record = self.env['mechanical.paver.block'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    notes_id = fields.One2many('mechanical.paver.block.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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








class WaterLine(models.Model):
    _name = "paver.water.absorption.line"
    parent_id = fields.Many2one('mechanical.paver.block',string="Parent Id")

    serial_no = fields.Integer(string="Specimen. No", readonly=True, copy=False, default=1)

    wet_w2 = fields.Float(string="Weight of the specimen after 24-hour immersion Ww (g)")
    dry_wt_w1 = fields.Float(string="Dry Weight Wd (g)")
    water_absorption = fields.Float(string="  Water Absorption %",compute="_compute_water_absorption")

    @api.depends('dry_wt_w1', 'wet_w2')
    def _compute_water_absorption(self):
        for rec in self:
            if rec.dry_wt_w1:  # avoid division by zero
                rec.water_absorption = round(((rec.wet_w2 - rec.dry_wt_w1) / rec.dry_wt_w1) * 100, 2)
            else:
                rec.water_absorption = 0.0

   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(WaterLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class CompressiveLine(models.Model):
    _name = "paver.compressive.line"
    parent_id = fields.Many2one('mechanical.paver.block',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)

    plan_area = fields.Float("Plan Area (mm²)")
    max_load = fields.Float("Max Load (kN)")

    apparent_strength = fields.Float(
        string="Apparent Strength (MPa)",
        compute="_compute_strength",
        store=True
    )

    correction_factor = fields.Float(
        string="Correction Factor"
    )

    corrected_strength = fields.Float(
        string="Corrected Strength (MPa)",
        compute="_compute_strength",
        store=True
    )

    @api.depends('plan_area', 'max_load', 'correction_factor')
    def _compute_strength(self):
        for rec in self:
            if rec.plan_area:
                # Same formula as Excel:
                # Apparent Strength = Max Load × 1000 / Plan Area
                rec.apparent_strength = (rec.max_load * 1000) / rec.plan_area
            else:
                rec.apparent_strength = 0

            rec.corrected_strength = (
                rec.apparent_strength * rec.correction_factor
            )

    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CompressiveLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class PlanAreaPaverBlockLine(models.Model):
    _name = "mechanical.plan.area.paver.line"
    _description = "Plan Area Paver Block Line"

    parent_id = fields.Many2one('mechanical.paver.block',string="Parent Id")

    serial_no = fields.Integer(string="Block No", readonly=True, copy=False, default=1)

    mass_cutout = fields.Float(
        string="Mass of Cutout, msp (g)"
    )

    mass_standard = fields.Float(
        string="Mass of Standard, mstd (g)"
    )

    plan_area = fields.Float(
        string="Plan Area, Asp (mm²)",
        compute="_compute_plan_area",
        store=True,
    )

    remark = fields.Char("Remark")

    @api.depends("mass_cutout", "mass_standard")
    def _compute_plan_area(self):
        for rec in self:
            if rec.mass_standard:
                rec.plan_area = (
                    20000 * rec.mass_cutout
                ) / rec.mass_standard
            else:
                rec.plan_area = 0.0

    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PlanAreaPaverBlockLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class PaverDimensionLine(models.Model):
    _name = "paver.dimension.line"
    parent_id = fields.Many2one('mechanical.paver.block',string="Parent Id")

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
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PaverDimensionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class PaverBlockNotes(models.Model):
    _name = "mechanical.paver.block.notes"

    parent_id = fields.Many2one('mechanical.paver.block', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
