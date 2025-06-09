from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math



class ShutteringPlywood(models.Model):
    _name = "mechanical.shuttering.plywood1"
    _inherit = "lerm.eln"
    _description = 'mechanical.shuttering.plywood1'
    _rec_name = "name"

    name = fields.Char("Name",default="SHUTTERING PLYWOOD")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


      # Dimensions

    dimensions_shuttering_name = fields.Char("Name",default="Dimensions")
    dimensions_shuttering_visible = fields.Boolean("Dimensions Visible",compute="_compute_visible")   

   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_dimensions_shuttering = fields.One2many('mechanical.dimensions.shuttering.line1','parent_id',string="Parameter")


    average_length = fields.Float(string="Average Length, mm", compute="_compute_average_length_shuttering",digits=(12,1))

    average_width = fields.Float(string="Average Width, mm", compute="_compute_average_width_shuttering",digits=(12,3))
    average_thickness = fields.Float(string="Average Thickness, mm", compute="_compute_average_thickness_shuttering",digits=(12,2))
    average_squareness = fields.Float(string="Average Squareness, mm", compute="_compute_average_squareness_shuttering",digits=(12,4))
    average_edge_straightness = fields.Float(string="Average Edge Straightness, mm", compute="_compute_average_edge_straightness_shuttering",digits=(12,4))
 
    @api.depends('child_lines_dimensions_shuttering.lenght')
    def _compute_average_length_shuttering(self):
        for record in self:
            if record.child_lines_dimensions_shuttering:
                # Calculate the average length
                total = sum(line.lenght for line in record.child_lines_dimensions_shuttering)
                record.average_length = total / len(record.child_lines_dimensions_shuttering)  # Average across all child lines
            else:
                record.average_length = 0.0

    
    @api.depends('child_lines_dimensions_shuttering.width')
    def _compute_average_width_shuttering(self):
        for record in self:
            if record.child_lines_dimensions_shuttering:
                # Calculate the average length
                total = sum(line.width for line in record.child_lines_dimensions_shuttering)
                record.average_width = total / len(record.child_lines_dimensions_shuttering)  # Average across all child lines
            else:
                record.average_width = 0.0


    @api.depends('child_lines_dimensions_shuttering.thickness')
    def _compute_average_thickness_shuttering(self):
        for record in self:
            if record.child_lines_dimensions_shuttering:
                # Calculate the average length
                total = sum(line.thickness for line in record.child_lines_dimensions_shuttering)
                record.average_thickness = total / len(record.child_lines_dimensions_shuttering)  # Average across all child lines
            else:
                record.average_thickness = 0.0


    @api.depends('child_lines_dimensions_shuttering.squareness')
    def _compute_average_squareness_shuttering(self):
        for record in self:
            # Filter child lines with valid squareness values
            valid_squareness_values = [
                line.squareness for line in record.child_lines_dimensions_shuttering if line.squareness
            ]
            if valid_squareness_values:
                # Calculate the average of the valid values
                total = sum(valid_squareness_values)
                record.average_squareness = total / len(valid_squareness_values)
            else:
                record.average_squareness = 0.0


    

    @api.depends('child_lines_dimensions_shuttering.edge_straightness')
    def _compute_average_edge_straightness_shuttering(self):
        for record in self:
            # Filter child lines with valid edge_straightness values
            valid_edge_straightness_values = [
                line.edge_straightness for line in record.child_lines_dimensions_shuttering if line.edge_straightness
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3548tre-7a9c-4616-bad5-88eb1b294674')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3548tre-7a9c-4616-bad5-88eb1b294674')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3548tre-7a9c-4616-bad5-88eb1b294674')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3548tre-7a9c-4616-bad5-88eb1b294674')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3548gtre-7a9c-4616-bad5-88eb1b29247u2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3548gtre-7a9c-4616-bad5-88eb1b29247u2')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3548gtre-7a9c-4616-bad5-88eb1b29247u2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3548gtre-7a9c-4616-bad5-88eb1b29247u2')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','34587ght-7a9c-4616-bad5-88eb1b2923245t')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','34587ght-7a9c-4616-bad5-88eb1b2923245t')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','34587ght-7a9c-4616-bad5-88eb1b2923245t')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','34587ght-7a9c-4616-bad5-88eb1b2923245t')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35478hgtr-7a9c-4616-bad5-88eb1b29232354l')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35478hgtr-7a9c-4616-bad5-88eb1b29232354l')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35478hgtr-7a9c-4616-bad5-88eb1b29232354l')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35478hgtr-7a9c-4616-bad5-88eb1b29232354l')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35487kuy-7a9c-4616-bad5-88eb1b292323467t')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35487kuy-7a9c-4616-bad5-88eb1b292323467t')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35487kuy-7a9c-4616-bad5-88eb1b292323467t')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35487kuy-7a9c-4616-bad5-88eb1b292323467t')]).parameter_table
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


        # Adhesion of Plies

    adhesion_plies_name = fields.Char("Name",default="Adhesion of Plies")
    adhesion_plies_visible = fields.Boolean("Adhesion of Plies Visible",compute="_compute_visible") 

    adhesion_plies = fields.Char(string="Observation")


        #Resistance to dry heat

    resistance_heat_name = fields.Char("Name",default="Resistance to Dry Heat")
    resistance_heat_visible = fields.Boolean("Resistance to Dry Heat Visible",compute="_compute_visible") 

    resistance_heat = fields.Char(string="Observation")



    #Water Resistance Test

    water_resistance_name = fields.Char("Name",default="Water Resistance Test")
    water_resistance_visible = fields.Boolean("Water Resistance Test Visible",compute="_compute_visible") 

    water_resistance = fields.Char(string="Observation")



    #  density

    density_shuttering_name = fields.Char("Name",default="Density")
    density_shuttering_visible = fields.Boolean("density huttering Visible",compute="_compute_visible")   

   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_density_shuttering = fields.One2many('mechanical.density.huttering.line1','parent_id',string="Parameter")

    average_density_shuttering = fields.Float(string="Density, g/cm3 ",compute="_compute_average_gypsum_density_shuttering",digits=(12,3),store=True)

    @api.depends('child_lines_density_shuttering.density_shuttering')
    def _compute_average_gypsum_density_shuttering(self):
        for record in self:
            densities = record.child_lines_density_shuttering.mapped('density_shuttering')
            if densities:
                record.average_density_shuttering = sum(densities) / len(densities)
            else:
                record.average_density_shuttering = 0.0

   
   
    


    average_density_shuttering_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_average_density_shuttering_conformity", store=True)



    @api.depends('average_density_shuttering','eln_ref','grade')
    def _compute_average_density_shuttering_conformity(self):
        
        for record in self:
            record.average_density_shuttering_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','124578gte-7a9c-4616-bad5-88eb1b29087y')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','124578gte-7a9c-4616-bad5-88eb1b29087y')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_density_shuttering - record.average_density_shuttering*mu_value
                    upper = record.average_density_shuttering + record.average_density_shuttering*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_density_shuttering_conformity = 'pass'
                        break
                    else:
                        record.average_density_shuttering_conformity = 'fail'

    average_density_shuttering_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_density_shuttering_nabl", store=True)

    @api.depends('average_density_shuttering','eln_ref','grade')
    def _compute_average_density_shuttering_nabl(self):
        
        for record in self:
            record.average_density_shuttering_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','124578gte-7a9c-4616-bad5-88eb1b29087y')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','124578gte-7a9c-4616-bad5-88eb1b29087y')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_density_shuttering - record.average_density_shuttering*mu_value
                    upper = record.average_density_shuttering + record.average_density_shuttering*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_density_shuttering_nabl = 'pass'
                        break
                    else:
                        record.average_density_shuttering_nabl = 'fail'

    

    




        ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.dimensions_shuttering_visible = False
            record.adhesion_plies_visible = False
            record.resistance_heat_visible = False
            record.water_resistance_visible = False
            record.density_shuttering_visible = False
            
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
                if sample.internal_id == "12578trew3-7a9c-4616-bad5-88eb1b2607456":
                    record.dimensions_shuttering_visible = True

                if sample.internal_id == "35478tyus14-7a9b-4616-bad5-88eb1b26070834":
                    record.adhesion_plies_visible = True

                if sample.internal_id == "57896543fght-7a9b-4616-bad5-88eb1b260hj653":
                    record.resistance_heat_visible = True

                if sample.internal_id == "12547gtre2-7a7n-4616-bad5-88eb1b260tr878ng":
                    record.water_resistance_visible = True

                if sample.internal_id == "124578gte-7a9c-4616-bad5-88eb1b29087y":
                    record.density_shuttering_visible = True


               
               



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
        record = super(ShutteringPlywood, self).create(vals)
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
        record = self.env['mechanical.shuttering.plywood1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



class DimensionsLine(models.Model):
    _name = "mechanical.dimensions.shuttering.line1"
    parent_id = fields.Many2one('mechanical.shuttering.plywood1',string="Parent Id")
   
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

        return super(DimensionsLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class DensityLine(models.Model):
    _name = "mechanical.density.huttering.line1"
    parent_id = fields.Many2one('mechanical.shuttering.plywood1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    lenght = fields.Float(string="Length",digits=(12,2))
    width = fields.Float(string="Width",digits=(12,2))
    thickness = fields.Float(string="Thickness",digits=(12,2))
    initial_weight = fields.Float(string="Initial Weight",digits=(12,3))
    oven_dry_weight = fields.Float(string="Oven Dry Weight",digits=(12,3))
    density_shuttering = fields.Float(string="Density",compute="_compute_density_shuttering",digits=(12,3))


    @api.depends('oven_dry_weight', 'lenght', 'width', 'thickness')
    def _compute_density_shuttering(self):
        for record in self:
            if record.lenght > 0 and record.width > 0 and record.thickness > 0:
                volume = record.lenght * record.width * record.thickness
                record.density_shuttering = record.oven_dry_weight / volume * 1000
            else:
                record.density_shuttering = 0.0
    

  
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(DensityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1
