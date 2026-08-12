from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math
from datetime import datetime , timedelta
import re
import logging



class HollowSolidConcreteBlock(models.Model):
    _name = "hollow.solid.concrete.block"
    _inherit = "lerm.eln"
    _description = 'hollow.solid.concrete.block'
    _rec_name = "name"


    name = fields.Char("Name",default="Hollow And Solid Concrete Block")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    hollow_solid_temp = fields.Char("Temperature",store=True)
    hollow_solid_humidity = fields.Char("Humidity",store=True)

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
    length_dimen_name = fields.Char(default="Dimension Length")
    length_dimen_visible = fields.Boolean(string="Dimension Length Visible" ,compute="_compute_visible")

    length_dimen_line_ids = fields.One2many('hs.length.dimension.block.line','parent_id',string='Dimension Length Block Lines')

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','916c70fe-57ff-4f2a-9361-41a687b54f85')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','916c70fe-57ff-4f2a-9361-41a687b54f85')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','916c70fe-57ff-4f2a-9361-41a687b54f85')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','916c70fe-57ff-4f2a-9361-41a687b54f85')]).parameter_table
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

    height_dimen_line_ids = fields.One2many('hs.height.dimension.block.line','parent_id',string='Dimension Height Block Lines')

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6c0d4ef6-867f-4e79-baf1-690338654f26')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6c0d4ef6-867f-4e79-baf1-690338654f26')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6c0d4ef6-867f-4e79-baf1-690338654f26')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6c0d4ef6-867f-4e79-baf1-690338654f26')]).parameter_table
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

    # Dimension Width
    width_dimen_name = fields.Char(default="Dimension Width")
    width_dimen_visible = fields.Boolean(string="Dimension Width Visible" ,compute="_compute_visible")

    width_dimen_line_ids = fields.One2many('hs.width.dimension.block.line','parent_id',string='Dimension Width Block Lines')

    avg_measured_width = fields.Float(
    string="Average Measured Width",
    compute="_compute_avg_measured_width",
    store=True
)

    @api.depends('width_dimen_line_ids.measured_width')
    def _compute_avg_measured_width(self):
     for rec in self:
        width = rec.width_dimen_line_ids.mapped('measured_width')
        rec.avg_measured_width = (
            sum(width) / len(width)
            if width else 0.0
        )


    avg_measured_width_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_measured_width_confirmity")
    
    @api.depends('avg_measured_width','eln_ref','grade')
    def _compute_avg_measured_width_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_measured_width_confirmity = 'na'
                continue
            record.avg_measured_width_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ffa13e28-aab7-400a-9885-22b12783ca07')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ffa13e28-aab7-400a-9885-22b12783ca07')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_measured_width - record.avg_measured_width*mu_value
                    upper = record.avg_measured_width + record.avg_measured_width*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_measured_width_confirmity = 'pass'
                        break
                    else:
                        record.avg_measured_width_confirmity = 'fail'

    avg_measured_width_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_measured_width_nabl")
    
    @api.depends('avg_measured_width','eln_ref','grade')
    def _compute_avg_measured_width_nabl(self):
        
        for record in self:
            record.avg_measured_width_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ffa13e28-aab7-400a-9885-22b12783ca07')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ffa13e28-aab7-400a-9885-22b12783ca07')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_measured_width - record.avg_measured_width*mu_value
                    upper = record.avg_measured_width + record.avg_measured_width*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_measured_width_nabl = 'pass'
                        break
                    else:
                        record.avg_measured_width_nabl = 'fail'

    # Block Density 
    block_density_name = fields.Char(default="Block Density")
    block_density_visible = fields.Boolean(string="Block Density Visible",compute="_compute_visible")

    block_density_ids = fields.One2many('hs.block.density.line','parent_id',string='Block Density Lines')

    mean_block_density = fields.Float(string="Mean Block Density",compute="_compute_mean_block_density",store=True,digits=(10,3))

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','eaea5db1-dda0-4516-a043-322050d93537')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','eaea5db1-dda0-4516-a043-322050d93537')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','eaea5db1-dda0-4516-a043-322050d93537')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','eaea5db1-dda0-4516-a043-322050d93537')]).parameter_table
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


    

    # Compressive Strength
    compressive_strength_name = fields.Char(default="Compressive Strength")
    compressive_strength_visible = fields.Boolean(string="Compressive Strength Visible",compute="_compute_visible")

    compressive_strength_line_ids = fields.One2many('hs.compression.test.line','parent_id',string='Compressive Strength Test Line')

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','692bb4da-26eb-4701-9ad7-b341c974c8e8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','692bb4da-26eb-4701-9ad7-b341c974c8e8')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','692bb4da-26eb-4701-9ad7-b341c974c8e8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','692bb4da-26eb-4701-9ad7-b341c974c8e8')]).parameter_table
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



    #  Water Absorption
    water_absorbtion_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")
    wt_absorption_name = fields.Char("Name",default="Water Absorption")


    water_absorption_line_ids = fields.One2many(
        "hs.water.absorption.line",
        "parent_id",
        string="Water Absorption Specimens"
    )


    mean_water_absorption = fields.Float(
        string="Mean Water Absorption (%)",
        compute="_compute_mean_water_absorption",
        store=True,
        digits=(16, 3),
    )


    # ========================================================
    # COMPUTE MEAN WATER ABSORPTION
    # ========================================================

    @api.depends(
        "water_absorption_line_ids.water_absorption",
        "water_absorption_line_ids.wet_mass",
        "water_absorption_line_ids.dry_mass",
    )
    def _compute_mean_water_absorption(self):
        for rec in self:

            rec.mean_water_absorption = 0.0

            valid_lines = rec.water_absorption_line_ids.filtered(
                lambda line: (
                    line.wet_mass > 0
                    and line.dry_mass > 0
                )
            )

            if valid_lines:
                rec.mean_water_absorption = (
                    sum(
                        valid_lines.mapped(
                            "water_absorption"
                        )
                    )
                    / len(valid_lines)
                )


    mean_water_absorption_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_mean_water_absorption_confirmity")

    mean_water_absorption_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_mean_water_absorption_nabl",store=True)


    @api.depends('mean_water_absorption','eln_ref')
    def _compute_mean_water_absorption_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.mean_water_absorption_confirmity = 'na'
                continue
            record.mean_water_absorption_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fc4c19c4-3a3a-45f3-a099-f33a4b8e57a9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fc4c19c4-3a3a-45f3-a099-f33a4b8e57a9')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.mean_water_absorption - record.mean_water_absorption*mu_value
                    upper = record.mean_water_absorption + record.mean_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.mean_water_absorption_confirmity = 'pass'
                        break
                    else:
                        record.mean_water_absorption_confirmity = 'fail'

    @api.depends('mean_water_absorption','eln_ref')
    def _compute_mean_water_absorption_nabl(self):
        
        for record in self:
            record.mean_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fc4c19c4-3a3a-45f3-a099-f33a4b8e57a9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fc4c19c4-3a3a-45f3-a099-f33a4b8e57a9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.mean_water_absorption - record.mean_water_absorption*mu_value
                  upper = record.mean_water_absorption + record.mean_water_absorption*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.mean_water_absorption_nabl = 'pass'
                      break
                  else:
                      record.mean_water_absorption_nabl = 'fail'

    


    
    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

        
    def get_all_fields(self):
        record = self.env['hollow.solid.concrete.block'].browse(self.ids[0])
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
            record.width_dimen_visible = False
            record.block_density_visible = False
            record.compressive_strength_visible = False
            record.water_absorbtion_visible = False

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                
                if sample.internal_id == '916c70fe-57ff-4f2a-9361-41a687b54f85':
                    record.length_dimen_visible = True

                if sample.internal_id == '6c0d4ef6-867f-4e79-baf1-690338654f26':
                    record.height_dimen_visible = True

                if sample.internal_id == 'ffa13e28-aab7-400a-9885-22b12783ca07':
                    record.width_dimen_visible = True

                if sample.internal_id == 'eaea5db1-dda0-4516-a043-322050d93537':
                    record.block_density_visible = True
                
                if sample.internal_id == 'fc4c19c4-3a3a-45f3-a099-f33a4b8e57a9':
                    record.water_absorbtion_visible = True

                if sample.internal_id == '692bb4da-26eb-4701-9ad7-b341c974c8e8':
                    record.compressive_strength_visible = True


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
            # Dimension
            if result.parameter.internal_id == '3f3a11ba-cedf-42af-8e84-a42de743b7e4':
                result.calculated = True

            # Length
            if result.parameter.internal_id == '916c70fe-57ff-4f2a-9361-41a687b54f85':
                result.result_char = round(self.avg_measured_length,2)
                result.calculated = True
                if self.avg_measured_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Height
            if result.parameter.internal_id == '6c0d4ef6-867f-4e79-baf1-690338654f26':
                result.result_char = round(self.avg_measured_height,2)
                result.calculated = True
                if self.avg_measured_height_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Width
            if result.parameter.internal_id == 'ffa13e28-aab7-400a-9885-22b12783ca07':
                result.result_char = round(self.avg_measured_width,2)
                result.calculated = True
                if self.avg_measured_width_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Block Density
            if result.parameter.internal_id == 'eaea5db1-dda0-4516-a043-322050d93537':
                result.result_char = round(self.mean_block_density,2)
                result.calculated = True
                if self.mean_block_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


             # Compressive Strength
            if result.parameter.internal_id == '692bb4da-26eb-4701-9ad7-b341c974c8e8':
                result.result_char = round(self.average_compressive_strength,2)
                result.calculated = True
                if self.compressive_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Water Absorption
            if result.parameter.internal_id == 'fc4c19c4-3a3a-45f3-a099-f33a4b8e57a9':
                result.result_char = round(self.mean_water_absorption,2)
                result.calculated = True
                if self.mean_water_absorption_nabl == 'pass':
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
        record = super(HollowSolidConcreteBlock, self).create(vals)
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
        record = self.env['hollow.solid.concrete.block'].browse(self.ids[0])
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



    
    


    


    

    

    


    notes_id = fields.One2many('hollow.solid.concrete.block.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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
    
class HSLengthDimensionBlockLine(models.Model):
    _name = 'hs.length.dimension.block.line'
    _description = 'Dimension Length Block Lines'

    parent_id = fields.Many2one('hollow.solid.concrete.block', string="Parent Id")

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

        return super(HSLengthDimensionBlockLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1

class HSHeightDimensionBlockLine(models.Model):
    _name = 'hs.height.dimension.block.line'
    _description = 'Dimension Height Block Lines'

    parent_id = fields.Many2one('hollow.solid.concrete.block', string="Parent Id")

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

        return super(HSHeightDimensionBlockLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class HSWidthDimensionBlockLine(models.Model):
    _name = 'hs.width.dimension.block.line'
    _description = 'Dimension Width Block Lines'

    parent_id = fields.Many2one('hollow.solid.concrete.block', string="Parent Id")

    sample_no = fields.Integer(string="Block No.", readonly=True, copy=False, default=1)

    nominal_width = fields.Float("Nominal Width (mm)",digits=(10,3))
    measured_width = fields.Float("Measured Width (mm)" ,digits=(10,3))
    deviation = fields.Float("Deviation (mm)",
        compute='_compute_deviation',digits=(10,3) ,
        store=True
    )
    result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')
    ], compute='_compute_result', store=True,digits=(10,3))

    remark = fields.Char("Remark")

    @api.depends('nominal_width', 'measured_width')
    def _compute_deviation(self):
        for rec in self:
            rec.deviation = rec.measured_width - rec.nominal_width

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

        return super(HSWidthDimensionBlockLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class HSBlockDensityLine(models.Model):
    _name = 'hs.block.density.line'
    _description = 'Block Density Lines'

    parent_id = fields.Many2one('hollow.solid.concrete.block', string="Parent Id")

    sample_no = fields.Integer(string="Specimen No.", readonly=True, copy=False, default=1)

    dry_weight = fields.Float(string="Dry Weight W (g)",digits=(10,3))
    volume = fields.Float(string="Volume V (cm³)",digits=(10,3))
    block_density = fields.Float(string="Block Density γ (g/cm³)",compute='_compute_block_density',store=True,digits=(10,3))

    @api.depends('dry_weight', 'volume')
    def _compute_block_density(self):
        for rec in self:
            rec.block_density = (
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

        return super(HSBlockDensityLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1






class HSCompressionTestLine(models.Model):
    _name = 'hs.compression.test.line'
    _description = 'Compressive Strength Test Line'

    parent_id = fields.Many2one('hollow.solid.concrete.block', string="Parent Id")

    sample_no = fields.Integer(string="Cube No.", readonly=True, copy=False, default=1)

    # dimension = fields.Char(string="Dimension (mm)",compute="_compute_dimension",store=True)

    # @api.depends('parent_id.size_id') 
    # def _compute_dimension(self):
    #     for rec in self:
    #         rec.dimension = rec.parent_id.size_id.size

    length = fields.Float(string="Length (mm)")
    width = fields.Float(string="Width (mm)")
    height = fields.Float(string="Height (mm)")

    # dimension = fields.Char(
    #     string="Dimension (mm) (L x B x H)",
    #     related="parent_id.eln_ref.size_id.size",
    #     store=True,
    #     readonly=True,
    # )

    area_pressure_face = fields.Float(string="Area (mm²)",compute="_compute_area",store=True,)

    weight_before_test = fields.Float(string="Weight Before Test (Kg)")

    max_load_failure = fields.Float(string="Max Load at Failure (KN)")

    compressive_strength = fields.Float(string="Compressive Strength (MPa)",compute='_compute_strength',store=True)

    @api.depends('length', 'width')
    def _compute_area(self):
        for rec in self:
            rec.area_pressure_face = rec.length * rec.width

    

    # @api.depends("dimension")
    # def _compute_area(self):
    #     for record in self:
    #         record.area_pressure_face = 0.0

    #         if not record.dimension:
    #             continue

    #         dimensions = re.findall(
    #             r"\d+(?:\.\d+)?",
    #             record.dimension,
    #         )

    #         if len(dimensions) >= 2:
    #             length = float(dimensions[0])
    #             breadth = float(dimensions[1])

    #             record.area_pressure_face = length * breadth

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

        return super(HSCompressionTestLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1



class HSWaterAbsorptionLine(models.Model):
    _name = "hs.water.absorption.line"
    _description = "Hollow Solid Block Water Absorption Line"


    parent_id = fields.Many2one("hollow.solid.concrete.block",string="Parent Id")


    sample_no = fields.Integer(string="Specimen No.", readonly=True, copy=False, default=1)


    # A_wet
    wet_mass = fields.Float(
        string="Wet Mass (kg) A_wet",
        digits=(16, 2),
    )


    # B
    dry_mass = fields.Float(
        string="Dry Mass (kg) B",
        digits=(16, 2),
    )


    # A_suspended
    suspended_mass = fields.Float(
        string="Suspended Mass (kg) A_suspended",
        digits=(16, 2),
    )


    water_absorption = fields.Float(
        string="Water Absorption (%) = ((A_wet - B)/B) × 100",
        compute="_compute_water_absorption",
        store=True,
        digits=(16, 3),
    )


    # ========================================================
    # COMPUTE WATER ABSORPTION
    #
    # ((A_wet - B) / B) × 100
    # ========================================================

    @api.depends(
        "wet_mass",
        "dry_mass",
    )
    def _compute_water_absorption(self):
        for line in self:

            line.water_absorption = 0.0

            if line.dry_mass > 0:
                line.water_absorption = (
                    (
                        line.wet_mass
                        - line.dry_mass
                    )
                    / line.dry_mass
                ) * 100.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(HSWaterAbsorptionLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1








class AacBlockMechanicalNotes(models.Model):
    _name = "hollow.solid.concrete.block.notes"

    parent_id = fields.Many2one('hollow.solid.concrete.block', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
