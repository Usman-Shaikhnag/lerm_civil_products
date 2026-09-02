from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math




class SolidConcreteBlock(models.Model):
    _name = "mechanical.solid.concrete.block"
    _inherit = "lerm.eln"
    _rec_name = "name"


    name = fields.Char("Name",default="Solid Concrete Block")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    notes_id = fields.One2many('solid.concrete.block.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(SolidConcreteBlock, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The Test Report(s) is/are valid only to the sample submitted to the laboratory.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'Sample(s) was/were not drawn by laboratory.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'This Report may not be reproduced in except full/ part without the permission of the Lab Head of the Laboratory.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': '# - Information provided by the customer.',
            }),
        ]

        res['notes_id'] = default_notes
        return res

    
    # Block Density
    block_density_name = fields.Char("Name",default="Block Density")
    block_density_visible = fields.Boolean("Block Density Visible",compute="_compute_visible")

    block_density_child_lines = fields.One2many('mechanical.solid.block.density.line','parent_id',string="Parameter")


    average_block = fields.Float(string="Average Block Density", compute="_compute_average_block",digits=(16,1))

    average_length1 = fields.Float(string="Average Length", compute="_compute_average_length1",digits=(16,1))

    averag_height1 = fields.Float(string="Average Height",compute="_compute_average_hight1", digits=(16, 1))

    average_thickness = fields.Float(string="Average Thickness", compute="_compute_average_width1",digits=(16,1))


    @api.depends('block_density_child_lines.block_density')
    def _compute_average_block(self):
        for record in self:
            block_densities = record.block_density_child_lines.mapped('block_density')
            if block_densities:
                record.average_block = sum(block_densities) / len(block_densities)
            else:
                record.average_block = 0.0


    @api.depends('block_density_child_lines.length')
    def _compute_average_length1(self):
        for record in self:
            if record.block_density_child_lines:
                lengths = [line.length for line in record.block_density_child_lines]
                record.average_length1 = sum(lengths) / len(lengths)
            else:
                record.average_length1 = 0.0

                
    @api.depends('block_density_child_lines.heigth')
    def _compute_average_hight1(self):
        for record in self:
            if record.block_density_child_lines:
                heights = [line.heigth for line in record.block_density_child_lines]
                record.averag_height1 = sum(heights) / len(heights)
            else:
                record.averag_height1 = 0.0

    @api.depends('block_density_child_lines.thickness')
    def _compute_average_width1(self):
        for record in self:
            if record.block_density_child_lines:
                thicknesss = [line.thickness for line in record.block_density_child_lines]
                record.average_thickness = sum(thicknesss) / len(thicknesss)
            else:
                record.average_thickness = 0.0


    block_density_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('--', '--')
        ],string="Conformity",compute="_compute_block_conformity",store=True)

    @api.depends('average_block','eln_ref','grade')
    def _compute_block_conformity(self):
        
        for record in self:
            record.block_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e2190504-cc89-4334-a001-4766f9c65e24')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e2190504-cc89-4334-a001-4766f9c65e24')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.block_density_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_block - record.average_block*mu_value
                    upper = record.average_block + record.average_block*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.block_density_conformity = 'pass'
                        break
                    else:
                        record.block_density_conformity = 'fail'


    block_density_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_block_density_nabl",store=True)

    @api.depends('average_block','eln_ref','grade')
    def _compute_block_density_nabl(self):
        
        for record in self:
            record.block_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e2190504-cc89-4334-a001-4766f9c65e24')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e2190504-cc89-4334-a001-4766f9c65e24')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_block - record.average_block*mu_value
            upper = record.average_block + record.average_block*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.block_density_nabl = 'pass'
                break
            else:
                record.block_density_nabl = 'fail'


    
    # Moisture Movment
    moisture_movment_name = fields.Char("Name",default="Moisture Movement")
    moisture_movment_visible = fields.Boolean("Moisture Movment Visible",compute="_compute_visible")

    moisture_movment_child_lines = fields.One2many('mechanical.solid.moisture.movement.line','parent_id',string="Parameter")


    average_moisture_movment = fields.Float(string="Average",compute="_compute_average_moisture_movment", digits=(12, 3))
    
    @api.depends('moisture_movment_child_lines.moisture_movment')
    def _compute_average_moisture_movment(self):
        for record in self:
            moisture_movments = record.moisture_movment_child_lines.mapped('moisture_movment')
            record.average_moisture_movment = sum(moisture_movments) / len(moisture_movments) if len(moisture_movments) > 0 else 0.0

    moisture_movment_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('--', '--')
        ],string="Conformity",compute="_compute_moisture_movment_conformity",store=True)

    @api.depends('average_moisture_movment','eln_ref','grade')
    def _compute_moisture_movment_conformity(self):
        
        for record in self:
            record.moisture_movment_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','89acdd9a-0b60-4ab4-92fa-3b7756bab153')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','89acdd9a-0b60-4ab4-92fa-3b7756bab153')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.moisture_movment_conformity = '--'
                        break


                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_moisture_movment - record.average_moisture_movment*mu_value
                    upper = record.average_moisture_movment + record.average_moisture_movment*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.moisture_movment_conformity = 'pass'
                        break
                    else:
                        record.moisture_movment_conformity = 'fail'



    moisture_movment_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_moisture_movment_nabl",store=True)

    @api.depends('average_moisture_movment','eln_ref','grade')
    def _compute_moisture_movment_nabl(self):
        
        for record in self:
            record.moisture_movment_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','89acdd9a-0b60-4ab4-92fa-3b7756bab153')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','89acdd9a-0b60-4ab4-92fa-3b7756bab153')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_moisture_movment - record.average_moisture_movment*mu_value
            upper = record.average_moisture_movment + record.average_moisture_movment*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.moisture_movment_nabl = 'pass'
                break
            else:
                record.moisture_movment_nabl = 'fail'


     
    # Drying shrinkage
    drying_shrinkage_name = fields.Char("Name",default="Drying Shrinkage")
    drying_shrinkage_visible = fields.Boolean("Drying Shrinkage Visible",compute="_compute_visible")

    drying_shrinkage_child_lines = fields.One2many('mechanical.solid.drying.shrinkage.line','parent_id',string="Parameter")
    average_drying_shrinkage = fields.Float(string="Average", compute="_compute_average_drying_shrinkage",digits=(12,3))


    @api.depends('drying_shrinkage_child_lines.drying_shrinkage')
    def _compute_average_drying_shrinkage(self):
        for record in self:
            total_drying_shrinkage = sum(record.drying_shrinkage_child_lines.mapped('drying_shrinkage'))
            count_lines = len(record.drying_shrinkage_child_lines)
            record.average_drying_shrinkage = total_drying_shrinkage / count_lines if count_lines else 0.0


    drying_shrinkage_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('--', '--')
        ],string="Conformity",compute="_compute_drying_shrinkage_conformity",store=True)

    @api.depends('average_drying_shrinkage','eln_ref','grade')
    def _compute_drying_shrinkage_conformity(self):
        
        for record in self:
            record.drying_shrinkage_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32aee782-8018-4833-a365-d72ccb6f47bd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32aee782-8018-4833-a365-d72ccb6f47bd')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.drying_shrinkage_conformity = '--'
                        break


                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_drying_shrinkage - record.average_drying_shrinkage*mu_value
                    upper = record.average_drying_shrinkage + record.average_drying_shrinkage*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.drying_shrinkage_conformity = 'pass'
                        break
                    else:
                        record.drying_shrinkage_conformity = 'fail'


    drying_shrinkage_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_drying_shrinkage_nabl",store=True)

    @api.depends('average_drying_shrinkage','eln_ref','grade')
    def _compute_drying_shrinkage_nabl(self):
        
        for record in self:
            record.drying_shrinkage_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32aee782-8018-4833-a365-d72ccb6f47bd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32aee782-8018-4833-a365-d72ccb6f47bd')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_drying_shrinkage - record.average_drying_shrinkage*mu_value
            upper = record.average_drying_shrinkage + record.average_drying_shrinkage*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.drying_shrinkage_nabl = 'pass'
                break
            else:
                record.drying_shrinkage_nabl = 'fail'


    # Water Absorption

    water_absorption_name = fields.Char("Name", default="Water Absorption")
    water_absorption_visible = fields.Boolean("Water Absorption Visible", compute="_compute_visible")


    water_absorption_child_lines = fields.One2many('mechanical.solid.water.absorption.line', 'parent_id', string="Parameter")

    average_water_absorption = fields.Float(string="Average", compute="_compute_average_water_absorption",digits=(12,3), store=True)


    @api.depends('water_absorption_child_lines.water_absorption')
    def _compute_average_water_absorption(self):
        for record in self:
            total_water_absorption = 0.0
            count_lines = len(record.water_absorption_child_lines)
            for line in record.water_absorption_child_lines:
                total_water_absorption += line.water_absorption
            record.average_water_absorption = total_water_absorption / count_lines if count_lines else 0.0


    water_absorption_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('--', '--')
        ], string="Conformity", compute="_compute_water_absorption_conformity", store=True)

    @api.depends('average_water_absorption', 'eln_ref', 'grade')
    def _compute_water_absorption_conformity(self):
        for record in self:
            record.water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', '0faf6556-4902-4926-a6bd-ed0024dc5929')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', '0faf6556-4902-4926-a6bd-ed0024dc5929')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.water_absorption_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_water_absorption - record.average_water_absorption * mu_value
                    upper = record.average_water_absorption + record.average_water_absorption * mu_value
                    if lower >= req_min and upper <= req_max:
                        record.water_absorption_conformity = 'pass'
                        break
                    else:
                        record.water_absorption_conformity = 'fail'

    water_absorption_nabl = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="NABL", compute="_compute_water_absorption_nabl", store=True)

    @api.depends('average_water_absorption', 'eln_ref', 'grade')
    def _compute_water_absorption_nabl(self):
        for record in self:
            record.water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', '0faf6556-4902-4926-a6bd-ed0024dc5929')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', '0faf6556-4902-4926-a6bd-ed0024dc5929')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_water_absorption - record.average_water_absorption * mu_value
            upper = record.average_water_absorption + record.average_water_absorption * mu_value
            if lower >= lab_min and upper <= lab_max:
                record.water_absorption_nabl = 'pass'
                break
            else:
                record.water_absorption_nabl = 'fail'


    # Dimension
    dimension_name1 = fields.Char("Name",default="Dimension")
    dimension_visible = fields.Boolean("Dimension Visible",compute="_compute_visible")   

    dimension_child_lines = fields.One2many('mechanical.solid.dimension.line','parent_id',string="Parameter")
 
    average_length = fields.Float(string="Average Length", compute="_compute_average_length",digits=(16,1))


    average_length_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')
            ], string="Length Conformity", compute="_compute_average_length_conformity", store=True)



    @api.depends('average_length','eln_ref','grade')
    def _compute_average_length_conformity(self):
        
        for record in self:
            record.average_length_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','085e1df4-a0fd-40bc-ac92-b6118328c2e8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','085e1df4-a0fd-40bc-ac92-b6118328c2e8')]).parameter_table
            for material in materials:

                if material.grade.id == record.grade.id:
                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.average_length_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_length - record.average_length*mu_value
                    upper = record.average_length + record.average_length*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_length_conformity = 'pass'
                        break
                    else:
                        record.average_length_conformity = 'fail'

    average_length_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Length NABL", compute="_compute_average_length_nabl", store=True)

    @api.depends('average_length','eln_ref','grade')
    def _compute_average_length_nabl(self):
        
        for record in self:
            record.average_length_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','085e1df4-a0fd-40bc-ac92-b6118328c2e8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','085e1df4-a0fd-40bc-ac92-b6118328c2e8')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_length - record.average_length*mu_value
                    upper = record.average_length + record.average_length*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_length_nabl = 'pass'
                        break
                    else:
                        record.average_length_nabl = 'fail'

    avreage_height2 = fields.Float(string="Average Thickness",compute="_compute_average_hight", digits=(16, 1))

    avreage_height2_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')
            ], string="Thickness Conformity", compute="_compute_avreage_height2_conformity", store=True)



    @api.depends('avreage_height2','eln_ref','grade')
    def _compute_avreage_height2_conformity(self):
        
        for record in self:
            record.avreage_height2_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e237cad-9411-4b06-b9f3-26e96747a582')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e237cad-9411-4b06-b9f3-26e96747a582')]).parameter_table
            for material in materials:

                if material.grade.id == record.grade.id:
                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.avreage_height2_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avreage_height2 - record.avreage_height2*mu_value
                    upper = record.avreage_height2 + record.avreage_height2*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avreage_height2_conformity = 'pass'
                        break
                    else:
                        record.avreage_height2_conformity = 'fail'

    avreage_height2_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Thickness NABL", compute="_compute_avreage_height2_nabl", store=True)

    @api.depends('avreage_height2','eln_ref','grade')
    def _compute_avreage_height2_nabl(self):
        
        for record in self:
            record.avreage_height2_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e237cad-9411-4b06-b9f3-26e96747a582')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e237cad-9411-4b06-b9f3-26e96747a582')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avreage_height2 - record.avreage_height2*mu_value
                    upper = record.avreage_height2 + record.avreage_height2*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avreage_height2_nabl = 'pass'
                        break
                    else:
                        record.avreage_height2_nabl = 'fail'


    average_width = fields.Float(string="Average Width", compute="_compute_average_width",digits=(16,1))


    average_width_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')
            ], string="Width Conformity", compute="_compute_average_width_conformity", store=True)



    @api.depends('average_width','eln_ref','grade')
    def _compute_average_width_conformity(self):
        
        for record in self:
            record.average_width_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5630893a-6e66-4825-8fbb-f92c897025d3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5630893a-6e66-4825-8fbb-f92c897025d3')]).parameter_table
            for material in materials:

                if material.grade.id == record.grade.id:
                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.average_width_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_width - record.average_width*mu_value
                    upper = record.average_width + record.average_width*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_width_conformity = 'pass'
                        break
                    else:
                        record.average_width_conformity = 'fail'

    average_width_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Width NABL", compute="_compute_average_width_nabl", store=True)

    @api.depends('average_width','eln_ref','grade')
    def _compute_average_width_nabl(self):
        
        for record in self:
            record.average_width_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5630893a-6e66-4825-8fbb-f92c897025d3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5630893a-6e66-4825-8fbb-f92c897025d3')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_width - record.average_width*mu_value
                    upper = record.average_width + record.average_width*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_width_nabl = 'pass'
                        break
                    else:
                        record.average_width_nabl = 'fail'


    

    @api.depends('dimension_child_lines.length')
    def _compute_average_length(self):
        for record in self:
            if record.dimension_child_lines:
                lengths = [line.length for line in record.dimension_child_lines]
                record.average_length = sum(lengths) / len(lengths)
            else:
                record.average_length = 0.0

                
    @api.depends('dimension_child_lines.hight')
    def _compute_average_hight(self):
        for record in self:
            if record.dimension_child_lines:
                heights = [line.hight for line in record.dimension_child_lines]
                record.avreage_height2 = sum(heights) / len(heights)
            else:
                record.avreage_height2 = 0.0

  

    @api.depends('dimension_child_lines.width')
    def _compute_average_width(self):
        for record in self:
            if record.dimension_child_lines:
                widths = [line.width for line in record.dimension_child_lines]
                record.average_width = sum(widths) / len(widths)
            else:
                record.average_width = 0.0



     # Compressive Strength

    compressive_name = fields.Char("Name",default="Compressive Strength")
    compressive_visible = fields.Boolean("Compressive Strength Visible",compute="_compute_visible")   

    compressive_child_lines = fields.One2many('mechanical.solid.compressive.strength.line','parent_id',string="Parameter")
    avg_compressive_strength = fields.Float(string="Average",compute="compute_avg_compressive_strength",digits=(16,2))


    @api.depends('compressive_child_lines.compressiv_strength')
    def compute_avg_compressive_strength(self):
        for record in self:
            total_strength = sum(line.compressiv_strength for line in record.compressive_child_lines)
            num_lines = len(record.compressive_child_lines)
            record.avg_compressive_strength = total_strength / num_lines if num_lines > 0 else 0.0


    compressive_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('--', '--')
        ],string="Conformity",compute="_compressive_conformity",store=True)


    @api.depends('avg_compressive_strength','eln_ref','grade')
    def _compressive_conformity(self):
        
        for record in self:
            record.compressive_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3402d345-b96e-4ed1-a545-dd5b2a6e259a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3402d345-b96e-4ed1-a545-dd5b2a6e259a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.compressive_conformity = '--'
                        break


                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_compressive_strength - record.avg_compressive_strength*mu_value
                    upper = record.avg_compressive_strength + record.avg_compressive_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.compressive_conformity = 'pass'
                        break
                    else:
                        record.compressive_conformity = 'fail'


    compressive_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_compressive_nabl",store=True)

    @api.depends('avg_compressive_strength','eln_ref','grade')
    def _compute_compressive_nabl(self):
        
        for record in self:
            record.compressive_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3402d345-b96e-4ed1-a545-dd5b2a6e259a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3402d345-b96e-4ed1-a545-dd5b2a6e259a')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_compressive_strength - record.avg_compressive_strength*mu_value
            upper = record.avg_compressive_strength + record.avg_compressive_strength*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.compressive_nabl = 'pass'
                break
            else:
                record.compressive_nabl = 'fail'







    ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.block_density_visible = False
            record.moisture_movment_visible = False
            record.drying_shrinkage_visible = False
            record.water_absorption_visible = False
            record.dimension_visible = False
            record.compressive_visible = False
           
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                if sample.internal_id == "e2190504-cc89-4334-a001-4766f9c65e24":
                    record.block_density_visible = True

                if sample.internal_id == "89acdd9a-0b60-4ab4-92fa-3b7756bab153":
                    record.moisture_movment_visible = True

                if sample.internal_id == "32aee782-8018-4833-a365-d72ccb6f47bd":
                    record.drying_shrinkage_visible = True

                if sample.internal_id == "0faf6556-4902-4926-a6bd-ed0024dc5929":
                    record.water_absorption_visible = True

                if sample.internal_id == "68e3da78-7440-44b3-8f19-2f7e3c0de618":
                    record.dimension_visible = True


                if sample.internal_id == "3402d345-b96e-4ed1-a545-dd5b2a6e259a":
                    record.compressive_visible = True





                




               
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:


             # Block Density
            if result.parameter.internal_id == 'e2190504-cc89-4334-a001-4766f9c65e24':
                result.result_char = round(self.average_block,2)
                result.calculated = True
                if self.block_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


             # Moisture Movment
            if result.parameter.internal_id == '89acdd9a-0b60-4ab4-92fa-3b7756bab153':
                result.result_char = round(self.average_moisture_movment,2)
                result.calculated = True
                if self.moisture_movment_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


             # Drying Shrinkage
            if result.parameter.internal_id == '32aee782-8018-4833-a365-d72ccb6f47bd':
                result.result_char = round(self.average_drying_shrinkage,2)
                result.calculated = True
                if self.drying_shrinkage_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


             # DWater Absorption
            if result.parameter.internal_id == '0faf6556-4902-4926-a6bd-ed0024dc5929':
                result.result_char = round(self.average_water_absorption,2)
                result.calculated = True
                if self.water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            
            # Dimension
            if result.parameter.internal_id == '68e3da78-7440-44b3-8f19-2f7e3c0de618':
                result.calculated = True


             # Length
            if result.parameter.internal_id == '085e1df4-a0fd-40bc-ac92-b6118328c2e8':
                result.result_char = round(self.average_length,2)
                result.calculated = True
                if self.average_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue



             # Thickness
            if result.parameter.internal_id == '8e237cad-9411-4b06-b9f3-26e96747a582':
                result.result_char = round(self.avreage_height2,2)
                result.calculated = True
                if self.avreage_height2_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue



             # Width
            if result.parameter.internal_id == '5630893a-6e66-4825-8fbb-f92c897025d3':
                result.result_char = round(self.average_width,2)
                result.calculated = True
                if self.average_width_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            


             # Compressive Strength
            if result.parameter.internal_id == '3402d345-b96e-4ed1-a545-dd5b2a6e259a':
                result.result_char = round(self.avg_compressive_strength,2)
                result.calculated = True
                if self.compressive_nabl == 'pass':
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
        record = super(SolidConcreteBlock, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     # records = self.env['lerm.eln'].sudo().search([('id','=', record.eln_id.id)]).parameters_result
    #     # print("records",records)
    #     # self.sample_parameters = records
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    def _compute_sample_parameters(self):
        # parameter_based_assignment
        current_user = self.env.user
        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            # filter parameter results by current user
            user_param_results = record.eln_ref.parameters_result.filtered(
                lambda r: r.technician and r.technician.id == current_user.id
            )

            # map to parameter master IDs
            parameter_ids = user_param_results.mapped('parameter').ids

            record.sample_parameters = [(6, 0, parameter_ids)]



    def get_all_fields(self):
        record = self.env['mechanical.solid.concrete.block'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
    


class SolidBlockDensityLine(models.Model):
    _name = "mechanical.solid.block.density.line"
    parent_id = fields.Many2one('mechanical.solid.concrete.block',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    length = fields.Float(string="Length (mm)")
    heigth = fields.Float(string="Height (mm)")
    thickness = fields.Float(string="Thickness (mm)")
    volume = fields.Float(string="Volume (Cm3)", compute="_compute_volume")
    intial_wt = fields.Float(string="Initial Weight of the Specimen (kg)")
    final_wt = fields.Float(string="Final Weight of the Specimen after Oven Dry (kg) (Constant)")
    block_density = fields.Float(string="Block Density (kg/M³)", compute="_compute_block_density")



    @api.depends('length','heigth','thickness')
    def _compute_volume(self):
        for record in self:
            record.volume = record.length * record.heigth * record.thickness


    @api.depends('final_wt','volume')
    def _compute_block_density(self):
        for record in self:
            if record.volume != 0:
                record.block_density = record.final_wt / record.volume * 1000000
            else:
                record.block_density = 0.0

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(SolidBlockDensityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class SolidMoistureMovementLine(models.Model):
    _name = "mechanical.solid.moisture.movement.line"
    parent_id = fields.Many2one('mechanical.solid.concrete.block',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    dry_length = fields.Float(string="Dry Length of the Block")
    wet_length = fields.Float(string="Wet Length of the Block")
    moisture_movment = fields.Float(string="Moisture Movement %", compute="_compute_moisture_movement", digits=(12, 3))



    @api.depends('dry_length', 'wet_length')
    def _compute_moisture_movement(self):
        for record in self:
            if record.wet_length != 0:
                record.moisture_movment = (record.wet_length - record.dry_length) / record.wet_length * 100
            else:
                record.moisture_movment = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(SolidMoistureMovementLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class SolidDryingShrinkageLine(models.Model):
    _name = "mechanical.solid.drying.shrinkage.line"
    parent_id = fields.Many2one('mechanical.solid.concrete.block',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    wet_measurment = fields.Float(string="Wet measurement of the Block",digits=(12, 3))
    dry_measurment = fields.Float(string="Dry Measurement of the Block",digits=(12, 3))
    dry_lengths = fields.Float(string="Dry Length")
    drying_shrinkage = fields.Float(string="Drying Shrinkage %", compute="_compute_drying_shrinkage1",digits=(12, 4))



    @api.depends('wet_measurment', 'dry_measurment', 'dry_lengths')
    def _compute_drying_shrinkage1(self):
        for record in self:
            if record.dry_lengths != 0:
                record.drying_shrinkage = (record.wet_measurment - record.dry_measurment) / record.dry_lengths * 100
            else:
                record.drying_shrinkage = 0.0

  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(SolidDryingShrinkageLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class SolidWaterAbsorptionLine(models.Model):
    _name = "mechanical.solid.water.absorption.line"
    parent_id = fields.Many2one('mechanical.solid.concrete.block',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    wet_mass = fields.Float(string="Wet Mass of the Block (kg)")
    dry_mass = fields.Float(string="Dry Mass of the Block (kg)")
    water_absorption = fields.Float(string="Water Absorption %", compute="_compute_water_absorption",digits=(12,3))


    @api.depends('wet_mass', 'dry_mass')
    def _compute_water_absorption(self):
        for record in self:
            if record.dry_mass != 0:
                record.water_absorption = (record.wet_mass - record.dry_mass) / record.dry_mass * 100
            else:
                record.water_absorption = 0.0



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(SolidWaterAbsorptionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1




class SolidDimensionSolidBlock(models.Model):
    _name = "mechanical.solid.dimension.line"
    parent_id = fields.Many2one('mechanical.solid.concrete.block',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)
    length = fields.Float(string="Length in mm")
    hight = fields.Float(string="Thickness in mm")
    width = fields.Float(string="Width in mm")



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(SolidDimensionSolidBlock, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class SolidCompressiveStrengthSolidBlock(models.Model):
    _name = "mechanical.solid.compressive.strength.line"
    parent_id = fields.Many2one('mechanical.solid.concrete.block',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)
    length = fields.Float(string="Length in mm")
    width = fields.Float(string="Width in mm")
    thickness = fields.Float(string="Thickness (mm)")
    # hight = fields.Float(string="Thickness in mm")
    area = fields.Float(string="Area (mm²)",compute="compute_area")
    load = fields.Float(string="Load (N)")
    compressiv_strength = fields.Float(string="Compressive Strength N/mm²",compute="compute_compressive_strength")


    @api.depends('length','width')
    def compute_area(self):
        for record in self:
            record.area = record.length * record.width
    

    @api.depends('load', 'area')
    def compute_compressive_strength(self):
        for record in self:
            if record.area != 0:
                record.compressiv_strength = (record.load / record.area) * 1000
            else:
                record.compressiv_strength = 0.0



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(SolidCompressiveStrengthSolidBlock, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1





class SolidConcreteBlockNotes(models.Model):
    _name = "solid.concrete.block.notes"

    parent_id = fields.Many2one('mechanical.solid.concrete.block',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
