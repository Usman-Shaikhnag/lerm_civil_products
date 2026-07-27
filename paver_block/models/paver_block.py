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

    

    # Plan Area
    paver_name = fields.Char("Name",default=" Plan Area")
    paver_visible = fields.Boolean("Plan Area Visible",compute="_compute_visible")

    thickness2 = fields.Float(string="Thickness of Paver Block:",compute="_compute_thickness2")

    @api.depends('size_id')
    def _compute_thickness2(self):
        for rec in self:
            rec.thickness2 = rec.size_id.size if rec.size_id and rec.size_id.size else 0.0

    gms1 = fields.Float(string="Gms:")
    n1 = fields.Float(string="N:",digits=(12,6))
    gms2 = fields.Float(string="Gms:")
    n2 = fields.Float(string="N:",digits=(12,6))

    @api.onchange('gms1')
    def _onchange_gms1(self):
        for rec in self:
            rec.n1 = rec.gms1 * 0.00981 if rec.gms1 else 0.0

    @api.onchange('gms2')
    def _onchange_gms2(self):
        for rec in self:
            rec.n2 = rec.gms2 * 0.00981 if rec.gms2 else 0.0


    mass_specimen = fields.Float(string=" Mass of the Specimen Shaped Cardboard Sheet, Msp ",compute="_compute_mass_values",digits=(12,6))
    mass_size = fields.Float(string="Mass of the 200 X 100 mm size shaped Cardboard Sheet, Mst:",compute="_compute_mass_values",digits=(12,6))
    area_paver = fields.Float(string="Plan Area of Paver Block, Asp",compute="_compute_area_paver")

    area_paver_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_area_paver_conformity", store=True)

    @api.depends('area_paver','eln_ref','grade')
    def _compute_area_paver_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.area_paver_conformity = 'na'
                continue
            record.area_paver_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23547trew-199c-497a-b3a7-45023c604673')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23547trew-199c-497a-b3a7-45023c604673')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.area_paver - record.area_paver*mu_value
                    upper = record.area_paver + record.area_paver*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.area_paver_conformity = 'pass'
                        break
                    else:
                        record.area_paver_conformity = 'fail'

    area_paver_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_area_paver_nabl", store=True)

    @api.depends('area_paver','eln_ref','grade')
    def _compute_area_paver_nabl(self):
        
        for record in self:
            record.area_paver_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23547trew-199c-497a-b3a7-45023c604673')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23547trew-199c-497a-b3a7-45023c604673')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.area_paver - record.area_paver*mu_value
                    upper = record.area_paver + record.area_paver*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.area_paver_nabl = 'pass'
                        break
                    else:
                        record.area_paver_nabl = 'fail'

    thickness_child_lines = fields.One2many('paver.thickness.line','parent_id',string="Thickness",default=lambda self: self._default_thickness_child_lines())


    @api.model
    def _default_thickness_child_lines(self):
        default_lines = [
            (0, 0, {'thickness1': 50, 'Correction_factore': 1.03}),
            (0, 0, {'thickness1': 60, 'Correction_factore': 1.06}),
            (0, 0, {'thickness1': 80, 'Correction_factore': 1.18}),
            (0, 0, {'thickness1': 100, 'Correction_factore': 1.24}),
            (0, 0, {'thickness1': 120, 'Correction_factore': 1.34}),
        ]
        return default_lines

    @api.depends('gms1', 'gms2')
    def _compute_mass_values(self):
        for rec in self:
            rec.n1 = rec.gms1 * 0.00981 if rec.gms1 else 0.0
            rec.n2 = rec.gms2 * 0.00981 if rec.gms2 else 0.0
            rec.mass_specimen = rec.n1
            rec.mass_size = rec.n2

    @api.depends('mass_specimen', 'mass_size')
    def _compute_area_paver(self):
        for rec in self:
            if rec.mass_specimen and rec.mass_size:
                rec.area_paver = (20000 * rec.mass_specimen) / rec.mass_size
            else:
                rec.area_paver = 0.0

    # Compressive Strength 
    commpressive_name = fields.Char("Name",default="Compressive Strength")
    commpressive_visible = fields.Boolean("Plan Area Visible",compute="_compute_visible")

    commpressive_child_lines = fields.One2many('paver.compressive.line','parent_id',string="Compressive Line")

    avg_commpressive = fields.Float(
        string="Avg. Compressive Strength (N/mm2)",compute="_compute_avg_commpressive")

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

    @api.depends('commpressive_child_lines.compressive_strenght')
    def _compute_avg_commpressive(self):
        for rec in self:
            lines = rec.commpressive_child_lines
            if lines:
                total = sum(line.compressive_strenght for line in lines)
                rec.avg_commpressive = round(total / len(lines), 2)
            else:
                rec.avg_commpressive = 0.0

    avg_thickness = fields.Float(
        string="Avg Thickness",compute="_compute_avg_thickness")

    @api.depends('commpressive_child_lines.thickness')
    def _compute_avg_thickness(self):
        for rec in self:
            lines = rec.commpressive_child_lines
            if lines:
                total = sum(line.thickness for line in lines)
                rec.avg_thickness = round(total / len(lines), 2)
            else:
                rec.avg_thickness = 0.0

    avg_thickness_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Thickness Conformity", compute="_compute_avg_thickness_conformity", store=True)

    @api.depends('avg_thickness','eln_ref','grade')
    def _compute_avg_thickness_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_thickness_conformity = 'na'
                continue
            record.avg_thickness_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457fgrtt-5dc9-4a2a-8bf0-121045278hty')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457fgrtt-5dc9-4a2a-8bf0-121045278hty')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_thickness - record.avg_thickness*mu_value
                    upper = record.avg_thickness + record.avg_thickness*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_thickness_conformity = 'pass'
                        break
                    else:
                        record.avg_thickness_conformity = 'fail'

    avg_thickness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Thickness NABL", compute="_compute_avg_thickness_nabl", store=True)

    @api.depends('avg_thickness','eln_ref','grade')
    def _compute_avg_thickness_nabl(self):
        
        for record in self:
            record.avg_thickness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457fgrtt-5dc9-4a2a-8bf0-121045278hty')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457fgrtt-5dc9-4a2a-8bf0-121045278hty')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_thickness - record.avg_thickness*mu_value
                    upper = record.avg_thickness + record.avg_thickness*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_thickness_nabl = 'pass'
                        break
                    else:
                        record.avg_thickness_nabl = 'fail'


    # 3. Water Absorption

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


    








 ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.paver_visible = False
            record.commpressive_visible = False
            record.water_absorption_visible = False
            record.dimension_visible = False
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                if sample.internal_id == "23547trew-199c-497a-b3a7-45023c604673":
                    record.paver_visible = True

                if sample.internal_id == "1457fgrtt-5dc9-4a2a-8bf0-1281d1865a11":
                    record.paver_visible = True
                    record.commpressive_visible = True
                
                if sample.internal_id == "2147fgrr-eba3-4f15-b33d-679b39f7372e":
                    record.water_absorption_visible = True

                if sample.internal_id == "058b7e8d-c146-409f-8e75-e574960c5208":
                    record.dimension_visible = True

               



    # def open_eln_page(self):
    #     # import wdb; wdb.set_trace()

    #     return {
    #             'view_mode': 'form',
    #             'res_model': "lerm.eln",
    #             'type': 'ir.actions.act_window',
    #             'target': 'current',
    #             'res_id': self.eln_ref.id,
                
    #         }           

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()
            


            if result.parameter.internal_id == '058b7e8d-c146-409f-8e75-e574960c5208':
                result.calculated = True

            if result.parameter.internal_id == '5017ba7f-4c47-47a4-a592-ae725639d748':
                result.calculated = True

            if result.parameter.internal_id == 'cd59c3c7-0fe0-4bba-89f8-73ee2f5220fe':
                result.calculated = True

            if result.parameter.internal_id == 'a2c29ed3-a821-49ff-a1d1-a6553782600e':
                result.calculated = True

            if result.parameter.internal_id == '5dbec664-682a-400a-bdc6-c3c2435671ae':
                result.calculated = True


            if result.parameter.internal_id == '23547trew-199c-497a-b3a7-45023c604673':
                result.calculated = True
                result.result_char = round(self.area_paver,2)
                if self.area_paver_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '2147fgrr-eba3-4f15-b33d-679b39f7372e':
                result.calculated = True
                result.result_char = round(self.avg_water_absorption,2)
                if self.avg_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '1457fgrtt-5dc9-4a2a-8bf0-1281d1865a11':
                result.calculated = True
                result.result_char = round(self.avg_commpressive,2)
                if self.avg_commpressive_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '1457fgrtt-5dc9-4a2a-8bf0-121045278hty':
                result.calculated = True
                result.result_char = round(self.avg_thickness,2)
                if self.avg_thickness_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '4609c439-2ee4-4e3e-b40c-334e95b2bbda':
                result.calculated = True

            if result.parameter.internal_id == 'f079957b-608f-40c0-aebd-0db011ab0f2c':
                result.calculated = True

            # if result.parameter.internal_id == '549532ef-08e1-46f7-9565-bf034ce334f4':
            #     result.calculated = True
            

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

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample_identification = fields.Char(string="Sample Identification")
    dry_wt_w1 = fields.Float(string="Dry wt (W1)")
    wet_w2 = fields.Float(string="Wet wt (W2)")
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
    sample_identification_com = fields.Char(string="Sample Identification")
    wt_block = fields.Float(string="Weight of Block (gms)")
    correction_factor = fields.Float(string="Correction Factor",store=True)
    load = fields.Float(string=" Load (kN)")
    compressive_strenght = fields.Float(string=" Compressive Strength (N/mm2)",compute="_compute_compressive_strength")
    thickness = fields.Float(string=" Thickness mm")

    

    @api.depends('load', 'correction_factor', 'parent_id.area_paver')
    def _compute_compressive_strength(self):
        for line in self:
            area = line.parent_id.area_paver
            if area > 0:
                line.compressive_strenght = (line.load * line.correction_factor * 1000) / area
            else:
                line.compressive_strenght = 0.0


    # @api.depends('parent_id.thickness2', 'parent_id.thickness_child_lines')
    # def _compute_correction_factor(self):
    #     for line in self:
    #         correction = 0.0
    #         core_dia_value = line.parent_id.thickness2
    #         if core_dia_value and line.parent_id.thickness_child_lines:
    #             matched_line = line.parent_id.thickness_child_lines.filtered(
    #                 lambda l: float(l.thickness1) == float(core_dia_value)
    #             )
    #             if matched_line:
    #                 correction = matched_line[0].Correction_factore
    #         line.correction_factor = correction

    
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






class ThicknesscorrectionLine(models.Model):
    _name = "paver.thickness.line"
    parent_id = fields.Many2one('mechanical.paver.block',string="Parent Id")

   
    Correction_factore = fields.Float(string=" Correction Factor")
    thickness1 = fields.Float(string="Thickness")

   
   

    # @api.model
    # def create(self, vals):
    #     # Set the serial_no based on the existing records for the same parent
    #     if vals.get('parent_id'):
    #         existing_records = self.search([('parent_id', '=', vals['parent_id'])])
    #         if existing_records:
    #             max_serial_no = max(existing_records.mapped('serial_no'))
    #             vals['serial_no'] = max_serial_no + 1

    #     return super(ThicknesscorrectionLine, self).create(vals)

    # def _reorder_serial_numbers(self):
    #     # Reorder the serial numbers based on the positions of the records in child_lines
    #     records = self.sorted('id')
    #     for index, record in enumerate(records):
    #         record.serial_no = index + 1


class PaverBlockNotes(models.Model):
    _name = "mechanical.paver.block.notes"

    parent_id = fields.Many2one('mechanical.paver.block', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
