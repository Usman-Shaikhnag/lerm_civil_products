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

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'aac.block.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }

    # Dimension Length
    dimension_name = fields.Char(default="Dimension")
    dimension_visible = fields.Boolean(string="Dimension Visible" ,compute="_compute_visible")

    dimension_line_ids = fields.One2many('length.dimension.block.line','parent_id',string='Dimension Length Block Lines')

    avg_length = fields.Float(
    string="Average Length (mm)",
    compute="_compute_avg_length",
    store=True
)

    @api.depends('dimension_line_ids.length')
    def _compute_avg_length(self):
     for rec in self:
        lengths = rec.dimension_line_ids.mapped('length')
        rec.avg_length = (
            sum(lengths) / len(lengths)
            if lengths else 0.0
        )

    avg_length_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_length_confirmity")
    
    @api.depends('avg_length','eln_ref','grade')
    def _compute_avg_length_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_length_confirmity = 'na'
                continue
            record.avg_length_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42ea2fdb-c7be-4d19-8912-63f72c07574f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42ea2fdb-c7be-4d19-8912-63f72c07574f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_length - record.avg_length*mu_value
                    upper = record.avg_length + record.avg_length*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_length_confirmity = 'pass'
                        break
                    else:
                        record.avg_length_confirmity = 'fail'

    avg_length_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_length_nabl")
    
    @api.depends('avg_length','eln_ref','grade')
    def _compute_avg_length_nabl(self):
        
        for record in self:
            record.avg_length_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42ea2fdb-c7be-4d19-8912-63f72c07574f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42ea2fdb-c7be-4d19-8912-63f72c07574f')]).parameter_table
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

    

    avg_height = fields.Float(
    string="Average Height (mm)",
    compute="_compute_avg_height",
    store=True
)

    @api.depends('dimension_line_ids.height')
    def _compute_avg_height(self):
     for rec in self:
        heights = rec.dimension_line_ids.mapped('height')
        rec.avg_height = (
            sum(heights) / len(heights)
            if heights else 0.0
        )


    avg_height_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_height_confirmity")

    @api.depends('avg_height','eln_ref','grade')
    def _compute_avg_height_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_height_confirmity = 'na'
                continue
            record.avg_height_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f9bdf3df-9bb8-4cdd-8ff1-6bb6a2b23b34')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f9bdf3df-9bb8-4cdd-8ff1-6bb6a2b23b34')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_height - record.avg_height*mu_value
                    upper = record.avg_height + record.avg_height*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_height_confirmity = 'pass'
                        break
                    else:
                        record.avg_height_confirmity = 'fail'

    avg_height_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_height_nabl")

    @api.depends('avg_height','eln_ref','grade')
    def _compute_avg_height_nabl(self):
        
        for record in self:
            record.avg_height_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f9bdf3df-9bb8-4cdd-8ff1-6bb6a2b23b34')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f9bdf3df-9bb8-4cdd-8ff1-6bb6a2b23b34')]).parameter_table
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

    

    avg_width = fields.Float(
    string="Average Width (mm)",
    compute="_compute_avg_width",
    store=True
)

    @api.depends('dimension_line_ids.width')
    def _compute_avg_width(self):
     for rec in self:
        width = rec.dimension_line_ids.mapped('width')
        rec.avg_width = (
            sum(width) / len(width)
            if width else 0.0
        )


    avg_width_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_width_confirmity")
    
    @api.depends('avg_width','eln_ref','grade')
    def _compute_avg_width_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_width_confirmity = 'na'
                continue
            record.avg_width_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b3751088-d3ed-4e07-9546-de0e4bd26b0f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b3751088-d3ed-4e07-9546-de0e4bd26b0f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_width - record.avg_width*mu_value
                    upper = record.avg_width + record.avg_width*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_width_confirmity = 'pass'
                        break
                    else:
                        record.avg_width_confirmity = 'fail'

    avg_width_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_width_nabl")
    
    @api.depends('avg_width','eln_ref','grade')
    def _compute_avg_width_nabl(self):
        
        for record in self:
            record.avg_width_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b3751088-d3ed-4e07-9546-de0e4bd26b0f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b3751088-d3ed-4e07-9546-de0e4bd26b0f')]).parameter_table
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

    # Block Density 
    block_density_name = fields.Char(default="Block Density")
    block_density_visible = fields.Boolean(string="Block Density Visible",compute="_compute_visible")

    block_density_ids = fields.One2many('aac.block.density.line','parent_id',string='Block Density Lines')

    mean_block_density = fields.Float(string="Avg. Block Density",compute="_compute_mean_block_density",store=True,digits=(10,2))

    @api.depends('block_density_ids.block_density')
    def _compute_mean_block_density(self):
     for rec in self:
        if rec.block_density_ids:
            rec.mean_block_density = (
                sum(rec.block_density_ids.mapped('block_density'))
                / len(rec.block_density_ids)
            )
        else:
            rec.mean_block_density = 0.0

    mean_block_density_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_mean_block_density_confirmity")

    @api.depends('mean_block_density','eln_ref','grade')
    def _compute_mean_block_density_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.mean_block_density_confirmity = 'na'
                continue
            record.mean_block_density_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.mean_block_density - record.mean_block_density*mu_value
                    upper = record.mean_block_density + record.mean_block_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.mean_block_density_confirmity = 'pass'
                        break
                    else:
                        record.mean_block_density_confirmity = 'fail'

    mean_block_density_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_mean_block_density_nabl")
    
    @api.depends('mean_block_density','eln_ref','grade')
    def _compute_mean_block_density_nabl(self):
        
        for record in self:
            record.mean_block_density_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.mean_block_density - record.mean_block_density*mu_value
                    upper = record.mean_block_density + record.mean_block_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.mean_block_density_nabl = 'pass'
                        break
                    else:
                        record.mean_block_density_nabl = 'fail'


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


    drying_shrinkage_ids = fields.One2many(
        'aac.drying.shrinkage.line',
        'parent_id',
        string='Drying Shrinkage Test Lines'
    )

    avg_drying_shrinkage = fields.Float(string="Avg. Drying Shrinkage (%)",compute="_compute_avg_drying_shrinkage",store=True,digits=(10,8))

    @api.depends('drying_shrinkage_ids.drying_shrinkage')
    def _compute_avg_drying_shrinkage(self):
     for rec in self:
        if rec.drying_shrinkage_ids:
            rec.avg_drying_shrinkage = (
                sum(rec.drying_shrinkage_ids.mapped('drying_shrinkage'))
                / len(rec.drying_shrinkage_ids)
            )
        else:
            rec.avg_drying_shrinkage = 0.0


    avg_drying_shrinkage_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_drying_shrinkage_confirmity")

    @api.depends('avg_drying_shrinkage','eln_ref','grade')
    def _compute_avg_drying_shrinkage_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_drying_shrinkage_confirmity = 'na'
                continue
            record.avg_drying_shrinkage_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_drying_shrinkage - record.avg_drying_shrinkage*mu_value
                    upper = record.avg_drying_shrinkage + record.avg_drying_shrinkage*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_drying_shrinkage_confirmity = 'pass'
                        break
                    else:
                        record.avg_drying_shrinkage_confirmity = 'fail'


    avg_drying_shrinkage_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', default='fail',compute="_compute_drying_shrinkage_nabl")
    
    @api.depends('avg_drying_shrinkage','eln_ref','grade')
    def _compute_drying_shrinkage_nabl(self):
        
        for record in self:
            record.avg_drying_shrinkage_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_drying_shrinkage - record.avg_drying_shrinkage*mu_value
                    upper = record.avg_drying_shrinkage + record.avg_drying_shrinkage*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_drying_shrinkage_nabl = 'pass'
                        break
                    else:
                        record.avg_drying_shrinkage_nabl = 'fail'





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
            record.dimension_visible = False
            record.block_density_visible = False
            record.moisture_content_visible  = False 
            record.compressive_strength_visible = False
            record.drying_shrinkage_visible = False

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                

                if sample.internal_id == '12478fdr3w-ac79-4102-aeda-622dc0f973f6':
                    record.dimension_visible = True

                if sample.internal_id == '42ea2fdb-c7be-4d19-8912-63f72c07574f':
                    record.dimension_visible = True

                if sample.internal_id == 'f9bdf3df-9bb8-4cdd-8ff1-6bb6a2b23b34':
                    record.dimension_visible = True

                if sample.internal_id == 'b3751088-d3ed-4e07-9546-de0e4bd26b0f':
                    record.dimension_visible = True

                if sample.internal_id == '254879sw-4ef4-4e51-abeb-57dd2abe29a4':
                    record.block_density_visible = True
                
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
                result.result_char = round(self.avg_length,2)
                result.calculated = True
                if self.avg_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Height
            if result.parameter.internal_id == 'f9bdf3df-9bb8-4cdd-8ff1-6bb6a2b23b34':
                result.result_char = round(self.avg_height,2)
                result.calculated = True
                if self.avg_height_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Thickness
            if result.parameter.internal_id == 'b3751088-d3ed-4e07-9546-de0e4bd26b0f':
                result.result_char = round(self.avg_width,2)
                result.calculated = True
                if self.avg_width_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Block Density
            if result.parameter.internal_id == '254879sw-4ef4-4e51-abeb-57dd2abe29a4':
                result.result_char = round(self.mean_block_density,2)
                result.calculated = True
                if self.mean_block_density_nabl == 'pass':
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
                result.result_char = round(self.avg_drying_shrinkage,2)
                result.calculated = True
                if self.avg_drying_shrinkage_nabl == 'pass':
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



    
    


    


    

    

    


    notes_id = fields.One2many('mechanical.aac.block.notes', 'parent_id',string="Notes",
    default=lambda self: self._default_notes_lines()
)

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
    
class LengthDimensionBlockLine(models.Model):
    _name = 'length.dimension.block.line'
    _description = 'Dimension Length Block Lines'

    parent_id = fields.Many2one('mechanical.aac.block', string="Parent Id")

    sample_no = fields.Integer(string="Block No.", readonly=True, copy=False, default=1)

    length = fields.Float(string="Length (mm)")
    width = fields.Float(string="Width (mm)")
    height = fields.Float(string="Height (mm)")

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




class AACBlockkDensityLine(models.Model):
    _name = 'aac.block.density.line'
    _description = 'Block Density Lines'

    parent_id = fields.Many2one('mechanical.aac.block', string="Parent Id")

    sample_no = fields.Integer(string="Specimen No.", readonly=True, copy=False, default=1)

    length = fields.Float(string="Length (mm)")
    width = fields.Float(string="Width (mm)")
    height = fields.Float(string="Height (mm)")
    dry_weight = fields.Float(string="Weight (kg)",digits=(10,3))
    volume = fields.Float(string="Volume V (m³)",compute='_compute_volume',store=True,digits=(10,6))
    block_density = fields.Float(string="Block Density γ (kg/m³)",compute='_compute_block_density',store=True,digits=(10,3))

    

    @api.depends('length', 'width','height')
    def _compute_volume(self):
        for rec in self:
            rec.volume = (
                rec.length * rec.width * rec.height / 1000000000
            )

    @api.depends('dry_weight', 'volume')
    def _compute_block_density(self):
     for rec in self:
        if rec.volume:
            rec.block_density = rec.dry_weight / rec.volume
        else:
            rec.block_density = 0.0
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(AACBlockkDensityLine, self).create(vals)


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
    sample_length = fields.Float(
        string='Sample Length (mm)',
        digits=(16, 3)
    )

    length_l1 = fields.Float(
        string='Length L1',
        digits=(16, 3)
    )

    length_l2 = fields.Float(
        string='Length L2',
        digits=(16, 3)
    )

    drying_shrinkage = fields.Float(
        string='Drying Shrinkage %',
        compute='_compute_drying_shrinkage',
        store=True,
        digits=(16, 9)
    )

    @api.depends('sample_length', 'length_l1', 'length_l2')
    def _compute_drying_shrinkage(self):
        for rec in self:
            if rec.sample_length:
                rec.drying_shrinkage = (
                    (rec.length_l1 - rec.length_l2)
                    / rec.sample_length
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
