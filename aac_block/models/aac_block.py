from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class AacBlockMechanical(models.Model):
    _name = "mechanical.aac.block"
    _inherit = "lerm.eln"
    _description = 'mechanical.aac.block'
    _rec_name = "name"


    name = fields.Char("Name",default="AAC Block")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    aac_temp = fields.Char("Temperature",store=True)
    aac_humidity = fields.Char("Humidity",store=True)

    @api.depends("eln_ref")
    def _compute_size_id(self):
        for record in self:
            print("Size iD",record.eln_ref.size_id)
            record.size_id = record.eln_ref.size_id.id

    # Dimension Length
    length_dimen_name = fields.Char(default="Dimension Length")
    length_dimen_visible = fields.Boolean(string="Dimension Length Visible" ,compute="_compute_visible")

    length_dimen_line_ids = fields.One2many('length.dimension.block.line','parent_id',string='Dimension Length Block Lines')

    avg_measured_length = fields.Float(
    string="Average Measured Length",
    compute="_compute_avg_measured_length",
    store=True
)

    @api.depends('length_dimen_line_ids.measured_length')
    def _compute_avg_measured_length(self):
     for rec in self:
        lengths = rec.length_dimen_line_ids.mapped('measured_length')
        rec.avg_measured_length = (
            sum(lengths) / len(lengths)
            if lengths else 0.0
        )

    avg_measured_length_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_measured_length_confirmity")
    
    @api.depends('avg_measured_length','eln_ref','grade')
    def _compute_avg_measured_length_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_measured_length_confirmity = 'na'
                continue
            record.avg_measured_length_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42ea2fdb-c7be-4d19-8912-63f72c07574f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42ea2fdb-c7be-4d19-8912-63f72c07574f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_measured_length - record.avg_measured_length*mu_value
                    upper = record.avg_measured_length + record.avg_measured_length*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_measured_length_confirmity = 'pass'
                        break
                    else:
                        record.avg_measured_length_confirmity = 'fail'

    avg_measured_length_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_measured_length_nabl")
    
    @api.depends('avg_measured_length','eln_ref','grade')
    def _compute_avg_measured_length_nabl(self):
        
        for record in self:
            record.avg_measured_length_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42ea2fdb-c7be-4d19-8912-63f72c07574f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42ea2fdb-c7be-4d19-8912-63f72c07574f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_measured_length - record.avg_measured_length*mu_value
                    upper = record.avg_measured_length + record.avg_measured_length*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_measured_length_nabl = 'pass'
                        break
                    else:
                        record.avg_measured_length_nabl = 'fail'

    # Dimension Height
    height_dimen_name = fields.Char(default="Dimension Height")
    height_dimen_visible = fields.Boolean(string="Dimension Height Visible" ,compute="_compute_visible")

    height_dimen_line_ids = fields.One2many('height.dimension.block.line','parent_id',string='Dimension Height Block Lines')

    avg_measured_height = fields.Float(
    string="Average Measured Height",
    compute="_compute_avg_measured_height",
    store=True
)

    @api.depends('height_dimen_line_ids.measured_height')
    def _compute_avg_measured_height(self):
     for rec in self:
        heights = rec.height_dimen_line_ids.mapped('measured_height')
        rec.avg_measured_height = (
            sum(heights) / len(heights)
            if heights else 0.0
        )


    avg_measured_height_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_measured_height_confirmity")

    @api.depends('avg_measured_height','eln_ref','grade')
    def _compute_avg_measured_height_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_measured_height_confirmity = 'na'
                continue
            record.avg_measured_height_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f9bdf3df-9bb8-4cdd-8ff1-6bb6a2b23b34')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f9bdf3df-9bb8-4cdd-8ff1-6bb6a2b23b34')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_measured_height - record.avg_measured_height*mu_value
                    upper = record.avg_measured_height + record.avg_measured_height*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_measured_height_confirmity = 'pass'
                        break
                    else:
                        record.avg_measured_height_confirmity = 'fail'

    avg_measured_height_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_measured_height_nabl")

    @api.depends('avg_measured_height','eln_ref','grade')
    def _compute_avg_measured_height_nabl(self):
        
        for record in self:
            record.avg_measured_height_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f9bdf3df-9bb8-4cdd-8ff1-6bb6a2b23b34')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f9bdf3df-9bb8-4cdd-8ff1-6bb6a2b23b34')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_measured_height - record.avg_measured_height*mu_value
                    upper = record.avg_measured_height + record.avg_measured_height*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_measured_height_nabl = 'pass'
                        break
                    else:
                        record.avg_measured_height_nabl = 'fail'

    # Dimension Thickness
    thickness_dimen_name = fields.Char(default="Dimension Thickness")
    thickness_dimen_visible = fields.Boolean(string="Dimension Thickness Visible" ,compute="_compute_visible")

    thickness_dimen_line_ids = fields.One2many('thickness.dimension.block.line','parent_id',string='Dimension Thickness Block Lines')

    avg_measured_thickness = fields.Float(
    string="Average Measured Thickness",
    compute="_compute_avg_measured_thickness",
    store=True
)

    @api.depends('thickness_dimen_line_ids.measured_thickness')
    def _compute_avg_measured_thickness(self):
     for rec in self:
        thickness = rec.thickness_dimen_line_ids.mapped('measured_thickness')
        rec.avg_measured_thickness = (
            sum(thickness) / len(thickness)
            if thickness else 0.0
        )


    avg_measured_thickness_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_measured_thickness_confirmity")
    
    @api.depends('avg_measured_thickness','eln_ref','grade')
    def _compute_avg_measured_thickness_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_measured_thickness_confirmity = 'na'
                continue
            record.avg_measured_thickness_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b3751088-d3ed-4e07-9546-de0e4bd26b0f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b3751088-d3ed-4e07-9546-de0e4bd26b0f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_measured_thickness - record.avg_measured_thickness*mu_value
                    upper = record.avg_measured_thickness + record.avg_measured_thickness*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_measured_thickness_confirmity = 'pass'
                        break
                    else:
                        record.avg_measured_thickness_confirmity = 'fail'

    avg_measured_thickness_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_measured_thickness_nabl")
    
    @api.depends('avg_measured_thickness','eln_ref','grade')
    def _compute_avg_measured_thickness_nabl(self):
        
        for record in self:
            record.avg_measured_thickness_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b3751088-d3ed-4e07-9546-de0e4bd26b0f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b3751088-d3ed-4e07-9546-de0e4bd26b0f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_measured_thickness - record.avg_measured_thickness*mu_value
                    upper = record.avg_measured_thickness + record.avg_measured_thickness*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_measured_thickness_nabl = 'pass'
                        break
                    else:
                        record.avg_measured_thickness_nabl = 'fail'

    # Bulk Density 
    bulk_density_name = fields.Char(default="Bulk Density")
    bulk_density_visible = fields.Boolean(string="Bulk Density Visible",compute="_compute_visible")

    bulk_density_ids = fields.One2many('aac.bulk.density.line','parent_id',string='Bulk Density Lines')

    mean_bulk_density = fields.Float(string="Mean Bulk Density",compute="_compute_mean_bulk_density",store=True,digits=(10,3))

    @api.depends('bulk_density_ids.bulk_density')
    def _compute_mean_bulk_density(self):
     for rec in self:
        if rec.bulk_density_ids:
            rec.mean_bulk_density = (
                sum(rec.bulk_density_ids.mapped('bulk_density'))
                / len(rec.bulk_density_ids)
            )
        else:
            rec.mean_bulk_density = 0.0

    mean_bulk_density_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_mean_bulk_density_confirmity")

    @api.depends('mean_bulk_density','eln_ref','grade')
    def _compute_mean_bulk_density_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.mean_bulk_density_confirmity = 'na'
                continue
            record.mean_bulk_density_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.mean_bulk_density - record.mean_bulk_density*mu_value
                    upper = record.mean_bulk_density + record.mean_bulk_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.mean_bulk_density_confirmity = 'pass'
                        break
                    else:
                        record.mean_bulk_density_confirmity = 'fail'

    mean_bulk_density_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_mean_bulk_density_nabl")
    
    @api.depends('mean_bulk_density','eln_ref','grade')
    def _compute_mean_bulk_density_nabl(self):
        
        for record in self:
            record.mean_bulk_density_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.mean_bulk_density - record.mean_bulk_density*mu_value
                    upper = record.mean_bulk_density + record.mean_bulk_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.mean_bulk_density_nabl = 'pass'
                        break
                    else:
                        record.mean_bulk_density_nabl = 'fail'


    # Moisture Content
    moisture_content_name = fields.Char(default="Moisture Content")
    moisture_content_visible = fields.Boolean(string="Moisture Content Visible",compute="_compute_visible")

    moisture_content_line_ids = fields.One2many('aac.moisture.content.line','parent_id',string='AAC Moisture Content Line')

    mean_moisture_content = fields.Float(
        string='Mean Moisture Content (%)',
        compute='_compute_mean_moisture_content',
        store=True
    )

    @api.depends('moisture_content_line_ids.moisture_content')
    def _compute_mean_moisture_content(self):
        for rec in self:
            values = rec.moisture_content_line_ids.mapped('moisture_content')
            rec.mean_moisture_content = sum(values) / len(values) if values else 0.0

            
    mean_moisture_content_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_mean_moisture_content_confirmity")

    @api.depends('mean_moisture_content','eln_ref','grade')
    def _compute_mean_moisture_content_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.mean_moisture_content_confirmity = 'na'
                continue
            record.mean_moisture_content_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6478fde2-8097-4275-b80f-48ebdbcfe244')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6478fde2-8097-4275-b80f-48ebdbcfe244')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.mean_moisture_content - record.mean_moisture_content*mu_value
                    upper = record.mean_moisture_content + record.mean_moisture_content*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.mean_moisture_content_confirmity = 'pass'
                        break
                    else:
                        record.mean_moisture_content_confirmity = 'fail'

    mean_moisture_content_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', compute="_compute_mean_moisture_content_nabl")
    
    @api.depends('mean_moisture_content','eln_ref','grade')
    def _compute_mean_moisture_content_nabl(self):
        
        for record in self:
            record.mean_moisture_content_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6478fde2-8097-4275-b80f-48ebdbcfe244')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6478fde2-8097-4275-b80f-48ebdbcfe244')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.mean_moisture_content - record.mean_moisture_content*mu_value
                    upper = record.mean_moisture_content + record.mean_moisture_content*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.mean_moisture_content_nabl = 'pass'
                        break
                    else:
                        record.mean_moisture_content_nabl = 'fail'

    # Compressive Strength
    compressive_strength_name = fields.Char(default="Compressive Strength")
    compressive_strength_visible = fields.Boolean(string="Compressive Strength Visible",compute="_compute_visible")

    compressive_strength_line_ids = fields.One2many('aac.compression.test.line','parent_id',string='Compressive Strength Test Line')

    average_compressive_strength = fields.Float(string="Average Compressive Strength (MPa)",compute='_compute_average_compressive_strength',store=True)

    @api.depends('compressive_strength_line_ids.compressive_strength')
    def _compute_average_compressive_strength(self):
        for rec in self:
            strengths = rec.compressive_strength_line_ids.mapped('compressive_strength')
            rec.average_compressive_strength = (
                sum(strengths) / len(strengths)
                if strengths else 0.0
            )

    compressive_strength_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_compressive_strength_confirmity")
    
    @api.depends('average_compressive_strength','eln_ref','grade')
    def _compute_compressive_strength_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.compressive_strength_confirmity = 'na'
                continue
            record.compressive_strength_confirmity = 'fail'   
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896dfe-cb61-45db-91c5-0167b27a9ab5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896dfe-cb61-45db-91c5-0167b27a9ab5')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_compressive_strength - record.average_compressive_strength*mu_value
                    upper = record.average_compressive_strength + record.average_compressive_strength*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.compressive_strength_confirmity = 'pass'
                        break
                    else:
                        record.compressive_strength_confirmity = 'fail'

    compressive_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', default='fail',compute="_compute_compressive_strength_nabl")
    
    @api.depends('average_compressive_strength','eln_ref','grade')
    def _compute_compressive_strength_nabl(self):
        
        for record in self:
            record.compressive_strength_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896dfe-cb61-45db-91c5-0167b27a9ab5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896dfe-cb61-45db-91c5-0167b27a9ab5')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_compressive_strength - record.average_compressive_strength*mu_value
                    upper = record.average_compressive_strength + record.average_compressive_strength*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.compressive_strength_nabl = 'pass'
                        break
                    else:
                        record.compressive_strength_nabl = 'fail'

    


    # Drying Shrinkage
    drying_shrinkage_name = fields.Char(default="Drying Shrinkage")
    drying_shrinkage_visible = fields.Boolean(string="Drying Shrinkage Visible",compute="_compute_visible")


    drying_shrinkage_line_ids = fields.One2many(
        'aac.drying.shrinkage.line',
        'parent_id',
        string='Drying Shrinkage Test Lines'
    )

    mean_drying_shrinkage = fields.Float(string="Average Drying Shrinkage (%)",
        compute='_compute_mean_drying_shrinkage',
        store=True,digits=(10,3)
    )

    @api.depends('drying_shrinkage_line_ids.drying_shrinkage')
    def _compute_mean_drying_shrinkage(self):
        for rec in self:
            values = rec.drying_shrinkage_line_ids.mapped('drying_shrinkage')
            rec.mean_drying_shrinkage = sum(values) / len(values) if values else 0.0


    mean_drying_shrinkage_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_mean_drying_shrinkage_confirmity")

    @api.depends('mean_drying_shrinkage','eln_ref','grade')
    def _compute_mean_drying_shrinkage_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.mean_drying_shrinkage_confirmity = 'na'
                continue
            record.mean_drying_shrinkage_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.mean_drying_shrinkage - record.mean_drying_shrinkage*mu_value
                    upper = record.mean_drying_shrinkage + record.mean_drying_shrinkage*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.mean_drying_shrinkage_confirmity = 'pass'
                        break
                    else:
                        record.mean_drying_shrinkage_confirmity = 'fail'


    mean_drying_shrinkage_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', default='fail',compute="_compute_drying_shrinkage_nabl")
    
    @api.depends('mean_drying_shrinkage','eln_ref','grade')
    def _compute_drying_shrinkage_nabl(self):
        
        for record in self:
            record.mean_drying_shrinkage_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.mean_drying_shrinkage - record.mean_drying_shrinkage*mu_value
                    upper = record.mean_drying_shrinkage + record.mean_drying_shrinkage*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.mean_drying_shrinkage_nabl = 'pass'
                        break
                    else:
                        record.mean_drying_shrinkage_nabl = 'fail'





    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

        
    def get_all_fields(self):
        record = self.env['mechanical.aac.block'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.length_dimen_visible = False
            record.height_dimen_visible = False
            record.thickness_dimen_visible = False
            record.bulk_density_visible = False
            record.moisture_content_visible  = False 
            record.compressive_strength_visible = False
            record.drying_shrinkage_visible = False

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                
                if sample.internal_id == '42ea2fdb-c7be-4d19-8912-63f72c07574f':
                    record.length_dimen_visible = True

                if sample.internal_id == 'f9bdf3df-9bb8-4cdd-8ff1-6bb6a2b23b34':
                    record.height_dimen_visible = True

                if sample.internal_id == 'b3751088-d3ed-4e07-9546-de0e4bd26b0f':
                    record.thickness_dimen_visible = True

                if sample.internal_id == '254879sw-4ef4-4e51-abeb-57dd2abe29a4':
                    record.bulk_density_visible = True
                
                if sample.internal_id == '6478fde2-8097-4275-b80f-48ebdbcfe244':
                    record.moisture_content_visible = True

                if sample.internal_id == '21457896dfe-cb61-45db-91c5-0167b27a9ab5':
                    record.compressive_strength_visible = True

                if sample.internal_id == '214578ews-b1a2-4dac-b8cb-e077770af52f':
                    record.drying_shrinkage_visible = True
                

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
            # Dimension
            if result.parameter.internal_id == '12478fdr3w-ac79-4102-aeda-622dc0f973f6':
                result.calculated = True

            # Length
            if result.parameter.internal_id == '42ea2fdb-c7be-4d19-8912-63f72c07574f':
                result.result_char = round(self.avg_measured_length,2)
                result.calculated = True
                if self.avg_measured_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Height
            if result.parameter.internal_id == 'f9bdf3df-9bb8-4cdd-8ff1-6bb6a2b23b34':
                result.result_char = round(self.avg_measured_height,2)
                result.calculated = True
                if self.avg_measured_height_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Thickness
            if result.parameter.internal_id == 'b3751088-d3ed-4e07-9546-de0e4bd26b0f':
                result.result_char = round(self.avg_measured_thickness,2)
                result.calculated = True
                if self.avg_measured_thickness_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Bulk Density
            if result.parameter.internal_id == '254879sw-4ef4-4e51-abeb-57dd2abe29a4':
                result.result_char = round(self.mean_bulk_density,2)
                result.calculated = True
                if self.mean_bulk_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Moisture Content
            if result.parameter.internal_id == '6478fde2-8097-4275-b80f-48ebdbcfe244':
                result.result_char = round(self.mean_moisture_content,2)
                result.calculated = True
                if self.mean_moisture_content_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Compressive Strength
            if result.parameter.internal_id == '21457896dfe-cb61-45db-91c5-0167b27a9ab5':
                result.result_char = round(self.average_compressive_strength,2)
                result.calculated = True
                if self.compressive_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Drying Shrinkage
            if result.parameter.internal_id == '214578ews-b1a2-4dac-b8cb-e077770af52f':
                result.result_char = round(self.mean_drying_shrinkage,2)
                result.calculated = True
                if self.mean_drying_shrinkage_nabl == 'pass':
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
        record = super(AacBlockMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

    def get_all_fields(self):
        record = self.env['mechanical.aac.block'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
        
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

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



    
    


    


    

    

    


    notes_id = fields.One2many('mechanical.aac.block.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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
    
class LengthDimensionBlockLine(models.Model):
    _name = 'length.dimension.block.line'
    _description = 'Dimension Length Block Lines'

    parent_id = fields.Many2one('mechanical.aac.block', string="Parent Id")

    sample_no = fields.Integer(string="Block No.", readonly=True, copy=False, default=1)

    nominal_length = fields.Float("Nominal Length (mm)",digits=(10,3))
    measured_length = fields.Float("Measured Length (mm)" ,digits=(10,3))
    deviation = fields.Float("Deviation (mm)",
        compute='_compute_deviation',digits=(10,3) ,
        store=True
    )
    result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')
    ], compute='_compute_result', store=True,digits=(10,3))

    remark = fields.Char("Remark")

    @api.depends('nominal_length', 'measured_length')
    def _compute_deviation(self):
        for rec in self:
            rec.deviation = rec.measured_length - rec.nominal_length

    @api.depends('deviation')
    def _compute_result(self):
        for rec in self:
            rec.result = 'pass' if abs(rec.deviation) <= 5 else 'fail'

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(LengthDimensionBlockLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1

class HeightDimensionBlockLine(models.Model):
    _name = 'height.dimension.block.line'
    _description = 'Dimension Height Block Lines'

    parent_id = fields.Many2one('mechanical.aac.block', string="Parent Id")

    sample_no = fields.Integer(string="Block No.", readonly=True, copy=False, default=1)

    nominal_height = fields.Float("Nominal Height (mm)",digits=(10,3))
    measured_height = fields.Float("Measured Height (mm)" ,digits=(10,3))
    deviation = fields.Float("Deviation (mm)",
        compute='_compute_deviation',digits=(10,3) ,
        store=True
    )
    result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')
    ], compute='_compute_result', store=True,digits=(10,3))

    remark = fields.Char("Remark")

    @api.depends('nominal_height', 'measured_height')
    def _compute_deviation(self):
        for rec in self:
            rec.deviation = rec.measured_height - rec.nominal_height

    @api.depends('deviation')
    def _compute_result(self):
        for rec in self:
            rec.result = 'pass' if abs(rec.deviation) <= 3 else 'fail'

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(HeightDimensionBlockLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class ThicknessDimensionBlockLine(models.Model):
    _name = 'thickness.dimension.block.line'
    _description = 'Dimension Thickness Block Lines'

    parent_id = fields.Many2one('mechanical.aac.block', string="Parent Id")

    sample_no = fields.Integer(string="Block No.", readonly=True, copy=False, default=1)

    nominal_thickness = fields.Float("Nominal Thickness (mm)",digits=(10,3))
    measured_thickness = fields.Float("Measured Thickness (mm)" ,digits=(10,3))
    deviation = fields.Float("Deviation (mm)",
        compute='_compute_deviation',digits=(10,3) ,
        store=True
    )
    result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')
    ], compute='_compute_result', store=True,digits=(10,3))

    remark = fields.Char("Remark")

    @api.depends('nominal_thickness', 'measured_thickness')
    def _compute_deviation(self):
        for rec in self:
            rec.deviation = rec.measured_thickness - rec.nominal_thickness

    @api.depends('deviation')
    def _compute_result(self):
        for rec in self:
            rec.result = 'pass' if abs(rec.deviation) <= 3 else 'fail'

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(ThicknessDimensionBlockLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class AACBulkDensityLine(models.Model):
    _name = 'aac.bulk.density.line'
    _description = 'Bulk Density Lines'

    parent_id = fields.Many2one('mechanical.aac.block', string="Parent Id")

    sample_no = fields.Integer(string="Specimen No.", readonly=True, copy=False, default=1)

    dry_weight = fields.Float(string="Dry Weight W (g)",digits=(10,3))
    volume = fields.Float(string="Volume V (cm³)",digits=(10,3))
    bulk_density = fields.Float(string="Bulk Density γ (g/cm³)",compute='_compute_bulk_density',store=True,digits=(10,3))

    @api.depends('dry_weight', 'volume')
    def _compute_bulk_density(self):
        for rec in self:
            rec.bulk_density = (
                rec.dry_weight / rec.volume
                if rec.volume else 0.0
            )

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(AACBulkDensityLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1




class AacMoistureContentLine(models.Model):
    _name = 'aac.moisture.content.line'
    _description = 'AAC Moisture Content Line'

    parent_id = fields.Many2one('mechanical.aac.block', string="Parent Id")

    sample_no = fields.Integer(string="Specimen No.", readonly=True, copy=False, default=1)

    w1 = fields.Float(string="Weight of specimen before drying (W1)(g)")
    volume = fields.Float(string="Volume V (cm³)")
    w = fields.Float(string="Dry Weight W (g)")

    moisture_content = fields.Float(
        string="Moisture Content (%)",
        compute="_compute_moisture_content",
        store=True
    )

    @api.depends('w1', 'w')
    def _compute_moisture_content(self):
        for rec in self:
            rec.moisture_content = (
                ((rec.w1 - rec.w) / rec.w) * 100
                if rec.w else 0.0
            )

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(AacMoistureContentLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class AacCompressionTestLine(models.Model):
    _name = 'aac.compression.test.line'
    _description = 'Compressive Strength Test Line'

    parent_id = fields.Many2one('mechanical.aac.block', string="Parent Id")

    sample_no = fields.Integer(string="Cube No.", readonly=True, copy=False, default=1)

    length = fields.Float(string="Length")
    breadth = fields.Float(string="Breadth")
    # height = fields.Float(string="Specimen No.")

    area_pressure_face = fields.Float(string="Area of Pressure Face (mm²)",compute='_compute_area',store=True)

    weight_before_test = fields.Float(string="Weight Before Test (Kg)")

    max_load_failure = fields.Float(string="Max Load at Failure (KN)")

    compressive_strength = fields.Float(string="Compressive Strength (MPa)",compute='_compute_strength',store=True)

    @api.depends('length', 'breadth')
    def _compute_area(self):
        for rec in self:
            rec.area_pressure_face = rec.length * rec.breadth

    @api.depends('max_load_failure', 'area_pressure_face')
    def _compute_strength(self):
        for rec in self:
            if rec.area_pressure_face:
                rec.compressive_strength = (
                    rec.max_load_failure * 1000
                ) / rec.area_pressure_face
            else:
                rec.compressive_strength = 0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(AacCompressionTestLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1



class AacDryingShrinkageLine(models.Model):
    _name = "aac.drying.shrinkage.line"
    _description = 'Drying Shrinkage Test Line'

    parent_id = fields.Many2one('mechanical.aac.block', string="Parent Id")

    sample_no = fields.Integer(string="Specimen No.", readonly=True, copy=False, default=1)
    initial_length = fields.Float('Initial Length L1 in mm',digits=(10,2))
    final_length = fields.Float('Final Length L2 in mm',digits=(10,2))
    drying_shrinkage = fields.Float('Drying Shrinkage in %',compute="_compute_drying_shrinkage",digits=(10,3))

   

    @api.depends('initial_length', 'final_length')
    def _compute_drying_shrinkage(self):
        for rec in self:
            if rec.initial_length!=0:
                rec.drying_shrinkage = (
                    (rec.initial_length - rec.final_length)
                    / rec.initial_length
                ) * 100
            else:
                rec.drying_shrinkage = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(AacDryingShrinkageLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1







class AacBlockMechanicalNotes(models.Model):
    _name = "mechanical.aac.block.notes"

    parent_id = fields.Many2one('mechanical.aac.block', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
