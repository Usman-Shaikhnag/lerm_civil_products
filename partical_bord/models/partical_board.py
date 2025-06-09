from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math



class ParticleBoard(models.Model):
    _name = "mechanical.particle.board1"
    _inherit = "lerm.eln"
    _description = 'mechanical.particle.board1'
    _rec_name = "name"

    name = fields.Char("Name",default="Particle Board")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


      # Dimensions

    dimensions_particle_name = fields.Char("Name",default="Dimensions")
    dimensions_particle_visible = fields.Boolean("Dimensions Visible",compute="_compute_visible")   

   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_dimensions_particle = fields.One2many('mechanical.dimensions.particle.line1','parent_id',string="Parameter")


    average_length = fields.Float(string="Average Length, mm", compute="_compute_average_length_particle",digits=(12,1))

    average_width = fields.Float(string="Average Width, mm", compute="_compute_average_width_particle",digits=(12,3))
    average_thickness = fields.Float(string="Average Thickness, mm", compute="_compute_average_thickness_particle",digits=(12,2))
    average_squareness = fields.Float(string="Average Squareness, mm", compute="_compute_average_squareness_particle",digits=(12,4))
    average_edge_straightness = fields.Float(string="Average Edge Straightness, mm", compute="_compute_average_edge_straightness_particle",digits=(12,4))
 
    @api.depends('child_lines_dimensions_particle.lenght')
    def _compute_average_length_particle(self):
        for record in self:
            if record.child_lines_dimensions_particle:
                # Calculate the average length
                total = sum(line.lenght for line in record.child_lines_dimensions_particle)
                record.average_length = total / len(record.child_lines_dimensions_particle)  # Average across all child lines
            else:
                record.average_length = 0.0

    
    @api.depends('child_lines_dimensions_particle.width')
    def _compute_average_width_particle(self):
        for record in self:
            if record.child_lines_dimensions_particle:
                # Calculate the average length
                total = sum(line.width for line in record.child_lines_dimensions_particle)
                record.average_width = total / len(record.child_lines_dimensions_particle)  # Average across all child lines
            else:
                record.average_width = 0.0


    @api.depends('child_lines_dimensions_particle.thickness')
    def _compute_average_thickness_particle(self):
        for record in self:
            if record.child_lines_dimensions_particle:
                # Calculate the average length
                total = sum(line.thickness for line in record.child_lines_dimensions_particle)
                record.average_thickness = total / len(record.child_lines_dimensions_particle)  # Average across all child lines
            else:
                record.average_thickness = 0.0


    @api.depends('child_lines_dimensions_particle.squareness')
    def _compute_average_squareness_particle(self):
        for record in self:
            # Filter child lines with valid squareness values
            valid_squareness_values = [
                line.squareness for line in record.child_lines_dimensions_particle if line.squareness
            ]
            if valid_squareness_values:
                # Calculate the average of the valid values
                total = sum(valid_squareness_values)
                record.average_squareness = total / len(valid_squareness_values)
            else:
                record.average_squareness = 0.0


    

    @api.depends('child_lines_dimensions_particle.edge_straightness')
    def _compute_average_edge_straightness_particle(self):
        for record in self:
            # Filter child lines with valid edge_straightness values
            valid_edge_straightness_values = [
                line.edge_straightness for line in record.child_lines_dimensions_particle if line.edge_straightness
            ]
            if valid_edge_straightness_values:
                # Calculate the average of the valid values
                total = sum(valid_edge_straightness_values)
                record.average_edge_straightness = total / len(valid_edge_straightness_values)
            else:
                record.average_edge_straightness = 0.0

    average_length_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Length Conformity", compute="_compute_average_length_conformity", store=True)



    @api.depends('average_length','eln_ref','grade')
    def _compute_average_length_conformity(self):
        
        for record in self:
            record.average_length_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2578liy8-5dff-4e6c-97a2-2e2e51a83e02')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2578liy8-5dff-4e6c-97a2-2e2e51a83e02')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2578liy8-5dff-4e6c-97a2-2e2e51a83e02')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2578liy8-5dff-4e6c-97a2-2e2e51a83e02')]).parameter_table
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



    average_width_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Width Conformity", compute="_compute_average_width_conformity", store=True)



    @api.depends('average_width','eln_ref','grade')
    def _compute_average_width_conformity(self):
        
        for record in self:
            record.average_width_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','125789ly-0ae9-4369-bac5-983ba20d514f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','125789ly-0ae9-4369-bac5-983ba20d514f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','125789ly-0ae9-4369-bac5-983ba20d514f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','125789ly-0ae9-4369-bac5-983ba20d514f')]).parameter_table
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



    average_thickness_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Thickness Conformity", compute="_compute_average_thickness_conformity", store=True)



    @api.depends('average_thickness','eln_ref','grade')
    def _compute_average_thickness_conformity(self):
        
        for record in self:
            record.average_thickness_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25748lir-c96a-46e2-ab3d-0ee0a30a2f3a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25748lir-c96a-46e2-ab3d-0ee0a30a2f3a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_thickness - record.average_thickness*mu_value
                    upper = record.average_thickness + record.average_thickness*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_thickness_conformity = 'pass'
                        break
                    else:
                        record.average_thickness_conformity = 'fail'

    average_thickness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Thickness NABL", compute="_compute_average_thickness_nabl", store=True)

    @api.depends('average_thickness','eln_ref','grade')
    def _compute_average_thickness_nabl(self):
        
        for record in self:
            record.average_thickness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25748lir-c96a-46e2-ab3d-0ee0a30a2f3a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25748lir-c96a-46e2-ab3d-0ee0a30a2f3a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_thickness - record.average_thickness*mu_value
                    upper = record.average_thickness + record.average_thickness*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_thickness_nabl = 'pass'
                        break
                    else:
                        record.average_thickness_nabl = 'fail'



    average_squareness_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Squareness Conformity", compute="_compute_average_squareness_conformity", store=True)



    @api.depends('average_squareness','eln_ref','grade')
    def _compute_average_squareness_conformity(self):
        
        for record in self:
            record.average_squareness_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2546kuty-a064-4501-a638-e9fff7b109f6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2546kuty-a064-4501-a638-e9fff7b109f6')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_squareness - record.average_squareness*mu_value
                    upper = record.average_squareness + record.average_squareness*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_squareness_conformity = 'pass'
                        break
                    else:
                        record.average_squareness_conformity = 'fail'

    average_squareness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Squareness NABL", compute="_compute_average_squareness_nabl", store=True)

    @api.depends('average_squareness','eln_ref','grade')
    def _compute_average_squareness_nabl(self):
        
        for record in self:
            record.average_squareness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2546kuty-a064-4501-a638-e9fff7b109f6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2546kuty-a064-4501-a638-e9fff7b109f6')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_squareness - record.average_squareness*mu_value
                    upper = record.average_squareness + record.average_squareness*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_squareness_nabl = 'pass'
                        break
                    else:
                        record.average_squareness_nabl = 'fail'



    average_edge_straightness_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Edge Straightness Conformity", compute="_compute_average_edge_straightness_conformity", store=True)



    @api.depends('average_edge_straightness','eln_ref','grade')
    def _compute_average_edge_straightness_conformity(self):
        
        for record in self:
            record.average_edge_straightness_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','gt2548yt-f3e8-49d4-a56f-577e81e1d0e8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','gt2548yt-f3e8-49d4-a56f-577e81e1d0e8')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_edge_straightness - record.average_edge_straightness*mu_value
                    upper = record.average_edge_straightness + record.average_edge_straightness*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_edge_straightness_conformity = 'pass'
                        break
                    else:
                        record.average_edge_straightness_conformity = 'fail'

    average_edge_straightness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Edge Straightness NABL", compute="_compute_average_edge_straightness_nabl", store=True)

    @api.depends('average_edge_straightness','eln_ref','grade')
    def _compute_average_edge_straightness_nabl(self):
        
        for record in self:
            record.average_edge_straightness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','gt2548yt-f3e8-49d4-a56f-577e81e1d0e8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','gt2548yt-f3e8-49d4-a56f-577e81e1d0e8')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_edge_straightness - record.average_edge_straightness*mu_value
                    upper = record.average_edge_straightness + record.average_edge_straightness*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_edge_straightness_nabl = 'pass'
                        break
                    else:
                        record.average_edge_straightness_nabl = 'fail'

    
    #  Density and Moisture Content

    density_moisture_particale_name = fields.Char("Name",default="Density and Moisture Content")
    density_moisture_particale_visible = fields.Boolean("Density and Moisture Content Visible",compute="_compute_visible")   

   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_density_moisture_particale = fields.One2many('mechanical.density.moiture.particle.line1','parent_id',string="Parameter")

    average_density_particle = fields.Float(string="Density, g/cm3 ",compute="_compute_average_gypsum_density_particle",digits=(12,3),store=True)

    @api.depends('child_lines_density_moisture_particale.density_particle')
    def _compute_average_gypsum_density_particle(self):
        for record in self:
            densities = record.child_lines_density_moisture_particale.mapped('density_particle')
            if densities:
                record.average_density_particle = sum(densities) / len(densities)
            else:
                record.average_density_particle = 0.0

   
   
    


    average_density_particle_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Density Conformity", compute="_compute_average_density_particle_conformity", store=True)



    @api.depends('average_density_particle','eln_ref','grade')
    def _compute_average_density_particle_conformity(self):
        
        for record in self:
            record.average_density_particle_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2578gfet-6b54-40ea-b96e-313f38794876')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2578gfet-6b54-40ea-b96e-313f38794876')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_density_particle - record.average_density_particle*mu_value
                    upper = record.average_density_particle + record.average_density_particle*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_density_particle_conformity = 'pass'
                        break
                    else:
                        record.average_density_particle_conformity = 'fail'

    average_density_particle_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Density NABL", compute="_compute_average_density_particle_nabl", store=True)

    @api.depends('average_density_particle','eln_ref','grade')
    def _compute_average_density_particle_nabl(self):
        
        for record in self:
            record.average_density_particle_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2578gfet-6b54-40ea-b96e-313f38794876')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2578gfet-6b54-40ea-b96e-313f38794876')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_density_particle - record.average_density_particle*mu_value
                    upper = record.average_density_particle + record.average_density_particle*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_density_particle_nabl = 'pass'
                        break
                    else:
                        record.average_density_particle_nabl = 'fail'


    average_moisture_particle = fields.Float(string="Moisture Content, %",compute="_compute_average_gypsum_moisture_particle",digits=(12,1),store=True)

    @api.depends('child_lines_density_moisture_particale.moisture_particle')
    def _compute_average_gypsum_moisture_particle(self):
        for record in self:
            moisture = record.child_lines_density_moisture_particale.mapped('moisture_particle')
            if moisture:
                record.average_moisture_particle = sum(moisture) / len(moisture)
            else:
                record.average_moisture_particle = 0.0


    average_moisture_particle_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Moisture Content Conformity", compute="_compute_average_moisture_particle_conformity", store=True)



    @api.depends('average_moisture_particle','eln_ref','grade')
    def _compute_average_moisture_particle_conformity(self):
        
        for record in self:
            record.average_moisture_particle_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6578ghef-40f4-49bd-a490-3a001cded1c9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6578ghef-40f4-49bd-a490-3a001cded1c9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_moisture_particle - record.average_moisture_particle*mu_value
                    upper = record.average_moisture_particle + record.average_moisture_particle*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_moisture_particle_conformity = 'pass'
                        break
                    else:
                        record.average_moisture_particle_conformity = 'fail'

    average_moisture_particle_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Moisture Content NABL", compute="_compute_average_moisture_particle_nabl", store=True)

    @api.depends('average_moisture_particle','eln_ref','grade')
    def _compute_average_moisture_particle_nabl(self):
        
        for record in self:
            record.average_moisture_particle_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6578ghef-40f4-49bd-a490-3a001cded1c9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6578ghef-40f4-49bd-a490-3a001cded1c9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_moisture_particle - record.average_moisture_particle*mu_value
                    upper = record.average_moisture_particle + record.average_moisture_particle*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_moisture_particle_nabl = 'pass'
                        break
                    else:
                        record.average_moisture_particle_nabl = 'fail'


    #  Water Absorption

    water_absorption_particle_name = fields.Char("Name",default="Water Absorption")
    water_absorption_particle_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")   

   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_water_absorption_particle = fields.One2many('mechanical.particle.water.absorption.line1','parent_id',string="Parameter")

    average_water_absorption_particle = fields.Float(string="Water Absorption, %",compute="_compute_average_gypsum_water_absorption_particle",digits=(12,1),store=True)

    @api.depends('child_lines_water_absorption_particle.water_absorption_particle')
    def _compute_average_gypsum_water_absorption_particle(self):
        for record in self:
            absorption = record.child_lines_water_absorption_particle.mapped('water_absorption_particle')
            if absorption:
                record.average_water_absorption_particle = sum(absorption) / len(absorption)
            else:
                record.average_water_absorption_particle = 0.0

   
   
    


    average_water_absorption_particle_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_average_water_absorption_particle_conformity", store=True)



    @api.depends('average_water_absorption_particle','eln_ref','grade')
    def _compute_average_water_absorption_particle_conformity(self):
        
        for record in self:
            record.average_water_absorption_particle_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23587lit9-a5c2-49e0-bf58-40a077b6f408')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23587lit9-a5c2-49e0-bf58-40a077b6f408')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_water_absorption_particle - record.average_water_absorption_particle*mu_value
                    upper = record.average_water_absorption_particle + record.average_water_absorption_particle*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_water_absorption_particle_conformity = 'pass'
                        break
                    else:
                        record.average_water_absorption_particle_conformity = 'fail'

    average_water_absorption_particle_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_water_absorption_particle_nabl", store=True)

    @api.depends('average_water_absorption_particle','eln_ref','grade')
    def _compute_average_water_absorption_particle_nabl(self):
        
        for record in self:
            record.average_water_absorption_particle_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23587lit9-a5c2-49e0-bf58-40a077b6f408')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23587lit9-a5c2-49e0-bf58-40a077b6f408')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_water_absorption_particle - record.average_water_absorption_particle*mu_value
                    upper = record.average_water_absorption_particle + record.average_water_absorption_particle*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_water_absorption_particle_nabl = 'pass'
                        break
                    else:
                        record.average_water_absorption_particle_nabl = 'fail'



            ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.dimensions_particle_visible = False
            record.density_moisture_particale_visible = False
            record.water_absorption_particle_visible = False
            
            
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
                if sample.internal_id == "1254lku-47c9-4662-9298-3095ac900ffc":
                    record.dimensions_particle_visible = True
                
                if sample.internal_id == "12547lut-b637-4eb2-8d5e-7c0483f3938c":
                    record.density_moisture_particale_visible = True

                if sample.internal_id == "23587lit9-a5c2-49e0-bf58-40a077b6f408":
                    record.water_absorption_particle_visible = True

                

               
               



    def open_eln_page(self):
        # import wdb; wdb.set_trace()

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
        record = super(ParticleBoard, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        # records = self.env['lerm.eln'].sudo().search([('id','=', record.eln_id.id)]).parameters_result
        # print("records",records)
        # self.sample_parameters = records
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)



    def get_all_fields(self):
        record = self.env['mechanical.particle.board1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



class DimensionBoardsLine(models.Model):
    _name = "mechanical.dimensions.particle.line1"
    parent_id = fields.Many2one('mechanical.particle.board1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    lenght = fields.Float(string="Length, mm",digits=(12,2))
    width = fields.Float(string="Width, mm",digits=(12,2))
    thickness = fields.Float(string="Thickness, mm",digits=(12,2))
    squareness = fields.Float(string="Squareness, mm",digits=(12,2))
    edge_straightness = fields.Float(string="Edge Straightness, mm",digits=(12,2))


   


    

  
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(DimensionBoardsLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class DensityMoitureLine(models.Model):
    _name = "mechanical.density.moiture.particle.line1"
    parent_id = fields.Many2one('mechanical.particle.board1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    lenght = fields.Float(string="Length",digits=(12,2))
    width = fields.Float(string="Width",digits=(12,2))
    thickness = fields.Float(string="Thickness",digits=(12,2))
    initial_weight = fields.Float(string="Initial Weight",digits=(12,3))
    oven_dry_weight = fields.Float(string="Oven Dry Weight",digits=(12,3))
    density_particle = fields.Float(string="Density",compute="_compute_density_particle",digits=(12,3))
    moisture_particle = fields.Float(string="Moisture Content",compute="_compute_moisture_particle",digits=(12,3))


    @api.depends('oven_dry_weight', 'lenght', 'width', 'thickness')
    def _compute_density_particle(self):
        for record in self:
            if record.lenght > 0 and record.width > 0 and record.thickness > 0:
                volume = record.lenght * record.width * record.thickness
                record.density_particle = record.oven_dry_weight / volume * 1000
            else:
                record.density_particle = 0.0


    @api.depends('initial_weight', 'oven_dry_weight')
    def _compute_moisture_particle(self):
        for record in self:
            if record.oven_dry_weight:
                record.moisture_particle = (record.initial_weight - record.oven_dry_weight) / record.oven_dry_weight * 100
            else:
                record.moisture_particle = 0.0


    
    

  
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(DensityMoitureLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class WaterAbsorptionParticleLine(models.Model):
    _name = "mechanical.particle.water.absorption.line1"
    parent_id = fields.Many2one('mechanical.particle.board1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

   
    initial_weight = fields.Float(string="Initial Weight",digits=(12,3))
    oven_dry_weight = fields.Float(string="Oven Dry Weight",digits=(12,3))
    water_absorption_particle = fields.Float(string="Density",compute="_compute_particle_water_absorption_particle",digits=(12,3))

    @api.depends('initial_weight', 'oven_dry_weight')
    def _compute_particle_water_absorption_particle(self):
        for record in self:
            if record.oven_dry_weight > 0:  # Avoid division by zero
                record.water_absorption_particle = (
                    (record.initial_weight - record.oven_dry_weight) / record.oven_dry_weight
                ) * 100
            else:
                record.water_absorption_particle = 0.0


    
    

  
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(WaterAbsorptionParticleLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1

