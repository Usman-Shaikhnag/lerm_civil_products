from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class AacBlockMechanical(models.Model):
    _name = "mechanical.aac.block1"
    _inherit = "lerm.eln"
    _description = 'mechanical.aac.block1'
    _rec_name = "name"


    name = fields.Char("Name",default="AAC Block")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)


    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.dimension_visible = False
            record.moisture_visible  = False  
            record.density_visible = False
            record.drying_shrinkage_visible = False
            record.compressive_strength_visible = False

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '12478fdr3w-ac79-4102-aeda-622dc0f973f6':
                    record.dimension_visible = True
                if sample.internal_id == '6478fde2-8097-4275-b80f-48ebdbcfe244':
                    record.moisture_visible = True
                if sample.internal_id == '254879sw-4ef4-4e51-abeb-57dd2abe29a4':
                    record.density_visible = True
                if sample.internal_id == '214578ews-b1a2-4dac-b8cb-e077770af52f':
                    record.drying_shrinkage_visible = True
                if sample.internal_id == '21457896dfe-cb61-45db-91c5-0167b27a9ab5':
                    record.compressive_strength_visible = True

    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
                    if result.parameter.internal_id == '6478fde2-8097-4275-b80f-48ebdbcfe244':
                        result.result_char = round(self.average_moisture_content,2)
                        if self.moisture_nabl == 'pass':
                            result.nabl_status = 'nabl'
                        else:
                            result.nabl_status = 'non-nabl'
                        continue

                    if result.parameter.internal_id == '254879sw-4ef4-4e51-abeb-57dd2abe29a4':
                        result.result_char = round(self.average_density,2)
                        if self.density_nabl == 'pass':
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

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['mechanical.aac.block1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    # Dimension
    dimension_name = fields.Char(default="Dimension")
    dimension_visible = fields.Boolean(compute="_compute_visible")
    

    dimension_table = fields.One2many('mech.aac.dimension.line1','parent_id')
    average_length = fields.Float('Average Length',compute="_compute_average_length")
    length_grade1 = fields.Char("Length pecification Grade - 1")
    length_grade2 = fields.Char("Length Specification Grade - 2")

    average_width = fields.Float('Average Width',compute="_compute_average_width")
    width_grade1 = fields.Char("Width Specification Grade - 1")
    width_grade2 = fields.Char("Width Specification Grade - 2")

    average_height = fields.Float('Average Height',compute="_compute_average_height")

    height_grade1 = fields.Char("Height Specification Grade - 1")
    height_grade2 = fields.Char("Height Specification Grade - 2")




    @api.depends('dimension_table.length')
    def _compute_average_length(self):
        for record in self:
            try:
                record.average_length = round(sum(record.dimension_table.mapped('length')) / len(
                    record.dimension_table),2)
            except:
                record.average_length = 0

    
    @api.depends('dimension_table.width')
    def _compute_average_width(self):
        for record in self:
            try:
                record.average_width = round(sum(record.dimension_table.mapped('width')) / len(
                    record.dimension_table),2)
            except:
                record.average_width = 0


    @api.depends('dimension_table.height')
    def _compute_average_height(self):
        for record in self:
            try:
                record.average_height = round(sum(record.dimension_table.mapped('height')) / len(
                    record.dimension_table),2)
            except:
                record.average_height = 0

    # Moisture Content
    moisture_name = fields.Char(default="Moisture Content")
    moisture_visible = fields.Boolean(compute="_compute_visible")
    moisture_grade1 = fields.Char("Specification Grade - 1")
    moisture_grade2 = fields.Char("Specification Grade - 2")

    moisture_content_table = fields.One2many('mech.aac.moisture.line1','parent_id')
    average_moisture_content = fields.Float("Average Moisture Content %",compute="_compute_average_moisture_content")
    moisture_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_moisture_confirmity")
    moisture_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', default='fail',compute="_compute_moisture_nabl")


    @api.depends('average_moisture_content','eln_ref','grade')
    def _compute_moisture_confirmity(self):
        for record in self:
            record.moisture_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6478fde2-8097-4275-b80f-48ebdbcfe244')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6478fde2-8097-4275-b80f-48ebdbcfe244')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_moisture_content - record.average_moisture_content*mu_value
                    upper = record.average_moisture_content + record.average_moisture_content*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.moisture_confirmity = 'pass'
                        break
                    else:
                        record.moisture_confirmity = 'fail'

    @api.depends('average_moisture_content','eln_ref','grade')
    def _compute_moisture_nabl(self):
        
        for record in self:
            record.moisture_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6478fde2-8097-4275-b80f-48ebdbcfe244')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6478fde2-8097-4275-b80f-48ebdbcfe244')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_moisture_content - record.average_moisture_content*mu_value
                    upper = record.average_moisture_content + record.average_moisture_content*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.moisture_nabl = 'pass'
                        break
                    else:
                        record.moisture_nabl = 'fail'

    @api.depends('moisture_content_table.moisture_content')
    def _compute_average_moisture_content(self):
        for record in self:
            try:
                record.average_moisture_content = round(sum(record.moisture_content_table.mapped('moisture_content')) / len(
                    record.moisture_content_table),2)
            except:
                record.average_moisture_content = 0

    # Density 
    density_name = fields.Char(default="Density")
    density_visible = fields.Boolean(compute="_compute_visible")

    density_grade1 = fields.Char("Specification Grade - 1")
    density_grade2 = fields.Char("Specification Grade - 2")

    density_unit = fields.Char("Unit",default="mm",readonly=True)

    density_table = fields.One2many('mech.aac.density.line1','parent_id')
    average_density = fields.Float("Average Density",compute="_compute_average_density")

    density_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_density_confirmity")
    density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', default='fail',compute="_compute_density_nabl")


    @api.depends('average_density','eln_ref','grade')
    def _compute_density_confirmity(self):
        for record in self:
            record.density_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_density - record.average_density*mu_value
                    upper = record.average_density + record.average_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.density_confirmity = 'pass'
                        break
                    else:
                        record.density_confirmity = 'fail'

    @api.depends('average_density','eln_ref','grade')
    def _compute_density_nabl(self):
        
        for record in self:
            record.density_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_density - record.average_density*mu_value
                    upper = record.average_density + record.average_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.density_nabl = 'pass'
                        break
                    else:
                        record.density_nabl = 'fail'

    @api.depends('density_table.density')
    def _compute_average_density(self):
        for record in self:
            try:
                record.average_density = round(sum(record.density_table.mapped('density')) / len(
                    record.density_table),2)
            except:
                record.average_density = 0

    # Drying Shrinkage
    drying_shrinkage_name = fields.Char(default="Drying Shrinkage")
    drying_shrinkage_visible = fields.Boolean(compute="_compute_visible")

    drying_shrinkage_table = fields.One2many('mech.aac.drying.shrinkage.line1','parent_id')
    average_drying_shrinkage = fields.Float("Average Drying Shrinkage",compute="_compute_average_drying_shrinkage",digits=(12,3))
    drying_grade1 = fields.Char("Specification Grade - 1")
    drying_grade2 = fields.Char("Specification Grade - 2")
    drying_shrinkage_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_drying_shrinkage_confirmity")
    

    drying_shrinkage_aac_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', default='fail',compute="_compute_drying_shrinkage_nabl")


    @api.depends('average_drying_shrinkage','eln_ref','grade')
    def _compute_drying_shrinkage_confirmity(self):
        for record in self:
            record.drying_shrinkage_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_drying_shrinkage - record.average_drying_shrinkage*mu_value
                    upper = record.average_drying_shrinkage + record.average_drying_shrinkage*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.drying_shrinkage_confirmity = 'pass'
                        break
                    else:
                        record.drying_shrinkage_confirmity = 'fail'


    @api.depends('average_drying_shrinkage','eln_ref','grade')
    def _compute_drying_shrinkage_nabl(self):
        
        for record in self:
            record.drying_shrinkage_aac_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_drying_shrinkage - record.average_drying_shrinkage*mu_value
                    upper = record.average_drying_shrinkage + record.average_drying_shrinkage*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.drying_shrinkage_aac_nabl = 'pass'
                        break
                    else:
                        record.drying_shrinkage_aac_nabl = 'fail'

    @api.depends('drying_shrinkage_table.drying_shrinkage')
    def _compute_average_drying_shrinkage(self):
        for record in self:
            try:
                record.average_drying_shrinkage = round(sum(record.drying_shrinkage_table.mapped('drying_shrinkage')) / len(
                    record.drying_shrinkage_table),2)
            except:
                record.average_drying_shrinkage = 0


    # Compressive Strength
    compressive_strength_name = fields.Char(default="Compressive Strength")
    compressive_strength_visible = fields.Boolean(compute="_compute_visible")

    compressive_strength_table = fields.One2many('mech.aac.compressive.strength.line1','parent_id')
    average_compressive_strength = fields.Float("Average Compressive Strength",compute="_compute_average_compressive_strength")
    compressive_grade1 = fields.Char("Specification Grade - 1")
    compressive_grade2 = fields.Char("Specification Grade - 2")
    compressive_strength_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_compressive_strength_confirmity")
    compressive_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', default='fail',compute="_compute_compressive_strength_nabl")


    @api.depends('average_compressive_strength','eln_ref','grade')
    def _compute_compressive_strength_confirmity(self):
        for record in self:
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

    
    @api.depends('compressive_strength_table.compressive_strength')
    def _compute_average_compressive_strength(self):
        for record in self:
            try:
                average_compressive_strength = sum(record.compressive_strength_table.mapped('compressive_strength')) / len(
                record.compressive_strength_table)
                record.average_compressive_strength = round(average_compressive_strength,2)
            except:
                record.average_compressive_strength = 0

class AacDimensionLine(models.Model):
    _name = "mech.aac.dimension.line1"
    parent_id = fields.Many2one('mechanical.aac.block1', string="Parent Id")

    length = fields.Float('Length')
    width = fields.Float('Width')
    height = fields.Float('Height')


class AacMoistureLine(models.Model):
    _name = "mech.aac.moisture.line1"
    parent_id = fields.Many2one('mechanical.aac.block1', string="Parent Id")

    wt_sample = fields.Float('Weight of sample W1 in gm')
    oven_wt = fields.Float('Oven dry Weight of sample W in gm')
    moisture_content = fields.Float('Moisture Content %',compute="_compute_moisture_content")

    @api.depends('wt_sample','oven_wt')
    def _compute_moisture_content(self):
        for record in self:
            if record.oven_wt != 0:
                moisture = (record.wt_sample - record.oven_wt)/record.oven_wt *100
                record.moisture_content = round(moisture,2)
            else:
                record.moisture_content = 0

class AacDensityLine(models.Model):
    _name = "mech.aac.density.line1"
    parent_id = fields.Many2one('mechanical.aac.block1', string="Parent Id")

    length = fields.Float(string='Length of Sample before Drying in mm', digits=(16, 3), help='Length of Sample before Drying in millimeters')
    width = fields.Float(string='Width of Sample before Drying in mm', digits=(16, 3),widget='text_wrap')
    height = fields.Float(string='Height of Sample before Drying in mm', digits=(16, 3),widget='text_wrap')
    volume = fields.Float(string='Volume of Sample mm3', compute="_compute_volume", digits=(16, 7))
    wt_sample = fields.Float(string='Weight of Sample after Drying in g', digits=(16, 3))
    density = fields.Float(string='Density of Sample Kg/mm3', compute="compute_density", digits=(16, 1))

    

    @api.depends('length','width','height')
    def _compute_volume(self):
        for record in self:
            record.volume = round((record.length * record.width * record.height),7)

    @api.depends('volume','wt_sample')
    def compute_density(self):
        for record in self:
            if record.volume != 0:
                density = (record.wt_sample / record.volume) * 1000000
                record.density = round(density,1)
            else:
                record.density = 0


class AacDryingShrinkageLine(models.Model):
    _name = "mech.aac.drying.shrinkage.line1"
    parent_id = fields.Many2one('mechanical.aac.block1', string="Parent Id")

    length = fields.Float('Length of Specimen')
    initial_length = fields.Float('Initial Length L1 in mm',digits=(12,3))
    final_length = fields.Float('Final Length L2 in mm',digits=(12,3))
    change_length = fields.Float('Change in Length in mm',compute="_compute_change_length",digits=(12,3))
    drying_shrinkage = fields.Float('Drying Shrinkage in %',compute="_compute_drying_shrinkage",digits=(12,3))

    @api.depends('initial_length','final_length')
    def _compute_change_length(self):
        for record in self:
            record.change_length = record.final_length - record.initial_length

    # @api.depends('change_length','length')
    # def _compute_drying_shrinkage(self):
    #     for record in self:
    #         if record.length != 0:
    #             record.drying_shrinkage = round(record.change_length / record.length * 100,2)
    #         else:
    #             record.drying_shrinkage = 0

    @api.depends('initial_length', 'final_length', 'length')
    def _compute_drying_shrinkage(self):
        for record in self:
            if record.length:  # Avoid division by zero
                record.drying_shrinkage = ((record.final_length - record.initial_length) / record.length) * 100
            else:
                record.drying_shrinkage = 0.0


class AacCompressiveStrengthLine(models.Model):
    _name = "mech.aac.compressive.strength.line1"
    parent_id = fields.Many2one('mechanical.aac.block1', string="Parent Id")

    crosssectional_area = fields.Float('Crosssectional Area Sqmm')
    aac_load = fields.Float('Load (p) kN')
    compressive_strength = fields.Float('Compressive Strength MPa',compute="_compute_compressive_strength")


    @api.depends('crosssectional_area','aac_load')
    def _compute_compressive_strength(self):
        for record in self:
            print("CrossSectional",record.crosssectional_area)
            if record.crosssectional_area != 0:
                compressive_strength = (record.aac_load/record.crosssectional_area)*1000
                record.compressive_strength = round(compressive_strength,2)
            else:
                record.compressive_strength = 0



