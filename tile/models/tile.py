from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math



class Tile(models.Model):
    _name = "mechanical.tile1"
    _inherit = "lerm.eln"
    _description = 'mechanical.tile1'
    _rec_name = "name"

    name = fields.Char("Name",default="TILE")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)


    product_id = fields.Many2one('product.template', string="Product", compute="_compute_product_id",store=True)



    @api.depends('eln_ref')
    def _compute_product_id(self):
        if self.eln_ref:
            self.product_id = self.eln_ref.material.id

  
    

    size = fields.Many2one('lerm.size.line',string="Type of group",store=True,domain="[('product_id', '=', product_id)]")

    tile_type = fields.Char(string="Type Of Tile")

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    # Dimension

    dimension_name1 = fields.Char("Name",default="Dimension")
    dimension_visible = fields.Boolean("Dimension Visible",compute="_compute_visible")   

    # name = fields.Char("Name",default="DIMENSION")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines = fields.One2many('mechanical.dimension.tile.line1','parent_id',string="Parameter")

    length = fields.Float(string="Length(mm)",digits=(16,3))
    width = fields.Float(string="Width(mm)",digits=(16,3))
    thickness = fields.Float(string="Thickness(mm)",digits=(16,3))
    diagonal = fields.Float(string="Diagonal (mm)")
    average_length = fields.Float(string="Average Length", compute="_compute_average_length",digits=(16,3))
    average_width = fields.Float(string="Average Width", compute="_compute_average_width",digits=(16,3))
    # plan_area = fields.Float(string="Plan Area", compute="_compute_plan_area", digits=(16, 1))
    average_thickness = fields.Float(string="Average Thickness",compute="_compute_average_thickness", digits=(16, 3))


    @api.depends('child_lines.length1', 'child_lines.length2', 'child_lines.length3', 'child_lines.length4')
    def _compute_average_length(self):
        for record in self:
            if record.child_lines:
                # Calculate the average length per child line
                total = sum((line.length1 + line.length2 + line.length3 + line.length4) / 4 for line in record.child_lines)
                record.average_length = total / len(record.child_lines)  # Average across all child lines
            else:
                record.average_length = 0.0

    @api.depends('child_lines.width1', 'child_lines.width2', 'child_lines.width3', 'child_lines.width4')
    def _compute_average_width(self):
        for record in self:
            if record.child_lines:
                # Calculate the average length per child line
                total = sum((line.width1 + line.width2 + line.width3 + line.width4) / 4 for line in record.child_lines)
                record.average_width = total / len(record.child_lines)  # Average across all child lines
            else:
                record.average_width = 0.0

    @api.depends('child_lines.thickness1', 'child_lines.thickness2', 'child_lines.thickness3', 'child_lines.thickness4','child_lines.thickness5','child_lines.thickness6')
    def _compute_average_thickness(self):
        for record in self:
            if record.child_lines:
                # Calculate the average length per child line
                total = sum((line.thickness1 + line.thickness2 + line.thickness3 + line.thickness4 +line.thickness5 + line.thickness6) / 6 for line in record.child_lines)
                record.average_thickness = total / len(record.child_lines)  # Average across all child lines
            else:
                record.average_thickness = 0.0


    deviation_length = fields.Float(string="Deviation in Length %", compute="_compute_deviation_length",digits=(16,2))
    deviation_width = fields.Float(string="Deviation in Width %", compute="_compute_deviation_width",digits=(16,2))
    deviation_length_width = fields.Float(string="Deviation in Length & Width %", compute="_compute_deviation_length_width",digits=(16,2))

    deviation_thickness_visible = fields.Boolean("Dimension Visible",compute="_compute_visible") 
    deviation_thickness = fields.Float(string="Deviation in Thickness %", compute="_compute_deviation_thickness",digits=(16,2))

    deviation_length_width_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Deviation in Length & Width Conformity", compute="_compute_deviation_length_width_conformity", store=True)

    @api.depends('deviation_length_width','eln_ref','grade')
    def _compute_deviation_length_width_conformity(self):
        
        for record in self:
            record.deviation_length_width_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25888f82-79c0-44a8-9379-f40dd33235bb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25888f82-79c0-44a8-9379-f40dd33235bb')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.deviation_length_width - record.deviation_length_width*mu_value
                    upper = record.deviation_length_width + record.deviation_length_width*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.deviation_length_width_conformity = 'pass'
                        break
                    else:
                        record.deviation_length_width_conformity = 'fail'

    deviation_length_width_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Deviation in Length & Width NABL", compute="_compute_deviation_length_width_nabl", store=True)

    @api.depends('deviation_length_width','eln_ref','grade')
    def _compute_deviation_length_width_nabl(self):
        
        for record in self:
            record.deviation_length_width_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25888f82-79c0-44a8-9379-f40dd33235bb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25888f82-79c0-44a8-9379-f40dd33235bb')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.deviation_length_width - record.deviation_length_width*mu_value
                    upper = record.deviation_length_width + record.deviation_length_width*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.deviation_length_width_nabl = 'pass'
                        break
                    else:
                        record.deviation_length_width_nabl = 'fail'

    deviation_thickness_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Deviation in Thickness Conformity", compute="_compute_deviation_thickness_conformity", store=True)


    @api.depends('deviation_thickness','eln_ref','grade')
    def _compute_deviation_thickness_conformity(self):
        
        for record in self:
            record.deviation_thickness_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35777f82-79c0-44a8-9379-f40dd33235uyt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35777f82-79c0-44a8-9379-f40dd33235uyt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.deviation_thickness - record.deviation_thickness*mu_value
                    upper = record.deviation_thickness + record.deviation_thickness*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.deviation_thickness_conformity = 'pass'
                        break
                    else:
                        record.deviation_thickness_conformity = 'fail'

    deviation_thickness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Deviation in Thickness NABL", compute="_compute_deviation_thickness_nabl", store=True)

    @api.depends('deviation_thickness','eln_ref','grade')
    def _compute_deviation_thickness_nabl(self):
        
        for record in self:
            record.deviation_thickness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35777f82-79c0-44a8-9379-f40dd33235uyt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35777f82-79c0-44a8-9379-f40dd33235uyt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.deviation_thickness - record.deviation_thickness*mu_value
                    upper = record.deviation_thickness + record.deviation_thickness*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.deviation_thickness_nabl = 'pass'
                        break
                    else:
                        record.deviation_thickness_nabl = 'fail'

    requirement_length_width = fields.Char(string="Requirement ,Deviation in Length & Width, %",compute="_compute_requirement_length_width")
    requirement_thickness = fields.Char(string="Requirement ,Deviation in Thickness,%",compute="_compute_requirement_thickness")

    @api.depends('size')
    def _compute_requirement_length_width(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '25888f82-79c0-44a8-9379-f40dd33235bb')
        ], limit=1)

        for record in self:
            record.requirement_length_width = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_length_width = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)


    @api.depends('size')
    def _compute_requirement_thickness(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '35777f82-79c0-44a8-9379-f40dd33235uyt')
        ], limit=1)

        for record in self:
            record.requirement_thickness = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_thickness = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)

    @api.depends('average_length','length')
    def _compute_deviation_length(self):
        for record in self:
            if record.length:  # Avoid division by zero
                record.deviation_length = ((record.average_length - record.length) / record.length) * 100
            else:
                record.deviation_length = 0.0

    @api.depends('average_width', 'width')
    def _compute_deviation_width(self):
        for record in self:
            if record.width:  # Ensure denominator is not zero
                record.deviation_width = round(((record.average_width - record.width) /record.width) * 100, 2)
            else:
                record.deviation_width = 0.0

   

    @api.depends('deviation_length','deviation_width')
    def _compute_deviation_length_width(self):
        for record in self:
            if record.deviation_length and record.deviation_width:  # Avoid division by zero
                record.deviation_length_width = (record.deviation_length + record.deviation_width) / 2
            else:
                record.deviation_length_width = 0.0

    @api.depends('average_thickness','thickness')
    def _compute_deviation_thickness(self):
        for record in self:
            if record.thickness:  # Avoid division by zero
                record.deviation_thickness = round(((record.average_thickness - record.thickness) / record.thickness) * 100, 2) 
            else:
                record.deviation_thickness = 0.0


     # Straightness

    straightness_name = fields.Char("Name",default="Straightness")
    straightness_visible = fields.Boolean("Straightness Visible",compute="_compute_visible")   

    sample_size = fields.Integer(string="Sample Size, mm")

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_straightness = fields.One2many('mechanical.straightness.tile.line1','parent_id',string="Parameter")

    average_straightness = fields.Float(string="Average", compute="_compute_average_straightness",digits=(16,3))

    maximum_straightness = fields.Float(string="Maximum Straightness mm",compute="_compute_maximum_straightness",store=True,digits=(16,3))

    deviation_straightness = fields.Float(string="Deviation from Straightness, %",compute="_compute_deviation_straightness", digits=(16,3))

    requirement_straightness = fields.Char(string="Requirement ,Deviation from Straightness, %",compute="_compute_requirement_straightness")

    @api.depends('child_lines_straightness.straightness1', 'child_lines_straightness.straightness2',
                 'child_lines_straightness.straightness3', 'child_lines_straightness.straightness4')
    def _compute_maximum_straightness(self):
        for tile in self:
            max_value = 0.0
            for line in tile.child_lines_straightness:
                max_in_line = max(line.straightness1, line.straightness2, line.straightness3, line.straightness4)
                if max_in_line > max_value:
                    max_value = max_in_line
            tile.maximum_straightness = max_value


    @api.depends('size')
    def _compute_requirement_straightness(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '19999f82-79c0-44a8-9379-f40dd33235aa')
        ], limit=1)

        for record in self:
            record.requirement_straightness = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_straightness = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)


    @api.depends('child_lines_straightness.straightness1',  'child_lines_straightness.straightness2',  'child_lines_straightness.straightness3',  'child_lines_straightness.straightness4' )
    def _compute_average_straightness(self):
        for record in self:
            if record.child_lines_straightness:
                # Calculate the total sum of all straightness fields across child lines
                total = sum(
                    line.straightness1 + line.straightness2 + line.straightness3 + line.straightness4
                    for line in record.child_lines_straightness
                )
                # Calculate the total number of straightness values
                count = len(record.child_lines_straightness) * 4  # 4 straightness fields per line
                record.average_straightness = total / count if count > 0 else 0.0
            else:
                record.average_straightness = 0.0

    @api.depends('maximum_straightness', 'sample_size')
    def _compute_deviation_straightness(self):
        for record in self:
            if record.sample_size and record.sample_size > 0:
                record.deviation_straightness = (record.maximum_straightness / record.sample_size) * 100
            else:
                record.deviation_straightness = 0.0


    deviation_straightness_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_deviation_straightness_conformity", store=True)



    @api.depends('deviation_straightness','eln_ref','grade')
    def _compute_deviation_straightness_conformity(self):
        
        for record in self:
            record.deviation_straightness_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','19999f82-79c0-44a8-9379-f40dd33235aa')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','19999f82-79c0-44a8-9379-f40dd33235aa')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.deviation_straightness - record.deviation_straightness*mu_value
                    upper = record.deviation_straightness + record.deviation_straightness*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.deviation_straightness_conformity = 'pass'
                        break
                    else:
                        record.deviation_straightness_conformity = 'fail'

    deviation_straightness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_deviation_straightness_nabl", store=True)

    @api.depends('deviation_straightness','eln_ref','grade')
    def _compute_deviation_straightness_nabl(self):
        
        for record in self:
            record.deviation_straightness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','19999f82-79c0-44a8-9379-f40dd33235aa')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','19999f82-79c0-44a8-9379-f40dd33235aa')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.deviation_straightness - record.deviation_straightness*mu_value
                    upper = record.deviation_straightness + record.deviation_straightness*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.deviation_straightness_nabl = 'pass'
                        break
                    else:
                        record.deviation_straightness_nabl = 'fail'


        # Rectangularity

    rectangularity_name = fields.Char("Name",default="Rectangularity")
    rectangularity_visible = fields.Boolean("Rectangularity Visible",compute="_compute_visible")   

    rectangularity_sample_size = fields.Integer(string="Sample Size, mm")

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_rectangularity = fields.One2many('mechanical.rectangularity.tile.line1','parent_id',string="Parameter")

    average_rectangularity = fields.Float(string="Average ", compute="_compute_average_rectangularity",digits=(16,3))

    deviation_rectangularity = fields.Float(string="Deviation from Rectangularity  %",compute="_compute_deviation_rectangularity", digits=(16,3))
    requirement_rectangularity = fields.Char(string="Requirement ,Deviation from Rectangularity, %",compute="_compute_requirement_rectangularity")

    maximum_rectangularity = fields.Float(string="Maximum Rectangularity mm",compute="_compute_maximum_rectangularity",store=True,digits=(16,3))

    @api.depends('child_lines_rectangularity.rectangularity1', 'child_lines_rectangularity.rectangularity2',
                 'child_lines_rectangularity.rectangularity3', 'child_lines_rectangularity.rectangularity4')
    def _compute_maximum_rectangularity(self):
        for tile in self:
            max_value = 0.0
            for line in tile.child_lines_rectangularity:
                max_in_line = max(line.rectangularity1, line.rectangularity2, line.rectangularity3, line.rectangularity4)
                if max_in_line > max_value:
                    max_value = max_in_line
            tile.maximum_rectangularity = max_value


    @api.depends('size')
    def _compute_requirement_rectangularity(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '4e209b70-f6b9-49b9-bab6-f38292f64b1c')
        ], limit=1)

        for record in self:
            record.requirement_rectangularity = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_rectangularity = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)


    @api.depends('child_lines_rectangularity.rectangularity1',  'child_lines_rectangularity.rectangularity2',  'child_lines_rectangularity.rectangularity3',  'child_lines_rectangularity.rectangularity4' )
    def _compute_average_rectangularity(self):
        for record in self:
            if record.child_lines_rectangularity:
                # Calculate the total sum of all rectangularity fields across child lines
                total = sum(
                    line.rectangularity1 + line.rectangularity2 + line.rectangularity3 + line.rectangularity4
                    for line in record.child_lines_rectangularity
                )
                # Calculate the total number of rectangularity values
                count = len(record.child_lines_rectangularity) * 4  # 4 rectangularity fields per line
                record.average_rectangularity = total / count if count > 0 else 0.0
            else:
                record.average_rectangularity = 0.0

    @api.depends('maximum_rectangularity', 'rectangularity_sample_size')
    def _compute_deviation_rectangularity(self):
        for record in self:
            if record.rectangularity_sample_size and record.rectangularity_sample_size > 0:
                record.deviation_rectangularity = (record.maximum_rectangularity / record.rectangularity_sample_size) * 100
            else:
                record.deviation_rectangularity = 0.0


    deviation_rectangularity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_deviation_rectangularity_conformity", store=True)



    @api.depends('deviation_rectangularity','eln_ref','grade')
    def _compute_deviation_rectangularity_conformity(self):
        
        for record in self:
            record.deviation_rectangularity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4e209b70-f6b9-49b9-bab6-f38292f64b1c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4e209b70-f6b9-49b9-bab6-f38292f64b1c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.deviation_rectangularity - record.deviation_rectangularity*mu_value
                    upper = record.deviation_rectangularity + record.deviation_rectangularity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.deviation_rectangularity_conformity = 'pass'
                        break
                    else:
                        record.deviation_rectangularity_conformity = 'fail'

    deviation_rectangularity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_deviation_rectangularity_nabl", store=True)

    @api.depends('deviation_rectangularity','eln_ref','grade')
    def _compute_deviation_rectangularity_nabl(self):
        
        for record in self:
            record.deviation_rectangularity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4e209b70-f6b9-49b9-bab6-f38292f64b1c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4e209b70-f6b9-49b9-bab6-f38292f64b1c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.deviation_rectangularity - record.deviation_rectangularity*mu_value
                    upper = record.deviation_rectangularity + record.deviation_rectangularity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.deviation_rectangularity_nabl = 'pass'
                        break
                    else:
                        record.deviation_rectangularity_nabl = 'fail'




      # Centre Curvature

    centre_curvature_name = fields.Char("Name",default="Centre Curvature")
    centre_curvature_visible = fields.Boolean("Centre Curvature Visible",compute="_compute_visible")   

    centre_curvature_sample_size = fields.Integer(string="Sample Size, mm")
    centre_curvature_diagonal  = fields.Integer(string="Diagonal, mm")

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_centre_curvature = fields.One2many('mechanical.centre.curvature.tile.line1','parent_id',string="Parameter")

    average_centre_curvature = fields.Float(string="Average ", compute="_compute_average_centre_curvature",digits=(16,3))

    deviation_centre_curvature = fields.Float(string="Maximum Centre Curvature, mm ",compute="_compute_deviation_centre_curvature", digits=(16,3))
    requirement_centre_curvature = fields.Char(string="Requirement ,Maximum Centre Curvature,%",compute="_compute_requirement_centre_curvature")

    maximum_centre_curvature = fields.Float(string="Maximum Centre Curvature,mm",compute="_compute_maximum_centre_curvature",store=True,digits=(16,3))

    @api.depends('child_lines_centre_curvature.centre_curvature1', 'child_lines_centre_curvature.centre_curvature2',
                 'child_lines_centre_curvature.centre_curvature3', 'child_lines_centre_curvature.centre_curvature4')
    def _compute_maximum_centre_curvature(self):
        for tile in self:
            max_value = 0.0
            for line in tile.child_lines_centre_curvature:
                max_in_line = max(line.centre_curvature1, line.centre_curvature2, line.centre_curvature3, line.centre_curvature4)
                if max_in_line > max_value:
                    max_value = max_in_line
            tile.maximum_centre_curvature = max_value



    @api.depends('size')
    def _compute_requirement_centre_curvature(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '873e02d1-db08-43d8-a88f-f6de09d41955')
        ], limit=1)

        for record in self:
            record.requirement_centre_curvature = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_centre_curvature = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)


    @api.depends('child_lines_centre_curvature.centre_curvature1',  'child_lines_centre_curvature.centre_curvature2',  'child_lines_centre_curvature.centre_curvature3',  'child_lines_centre_curvature.centre_curvature4' )
    def _compute_average_centre_curvature(self):
        for record in self:
            if record.child_lines_centre_curvature:
                # Calculate the total sum of all centre_curvature fields across child lines
                total = sum(
                    line.centre_curvature1 + line.centre_curvature2 + line.centre_curvature3 + line.centre_curvature4
                    for line in record.child_lines_centre_curvature
                )
                # Calculate the total number of centre_curvature values
                count = len(record.child_lines_centre_curvature) * 4  # 4 centre_curvature fields per line
                record.average_centre_curvature = total / count if count > 0 else 0.0
            else:
                record.average_centre_curvature = 0.0

    @api.depends('maximum_centre_curvature', 'centre_curvature_diagonal')
    def _compute_deviation_centre_curvature(self):
        for record in self:
            if record.centre_curvature_diagonal and record.centre_curvature_diagonal > 0:
                record.deviation_centre_curvature = (record.maximum_centre_curvature / record.centre_curvature_diagonal) * 100
            else:
                record.deviation_centre_curvature = 0.0


    deviation_centre_curvature_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_deviation_centre_curvature_conformity", store=True)



    @api.depends('deviation_centre_curvature','eln_ref','grade')
    def _compute_deviation_centre_curvature_conformity(self):
        
        for record in self:
            record.deviation_centre_curvature_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','873e02d1-db08-43d8-a88f-f6de09d41955')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','873e02d1-db08-43d8-a88f-f6de09d41955')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.deviation_centre_curvature - record.deviation_centre_curvature*mu_value
                    upper = record.deviation_centre_curvature + record.deviation_centre_curvature*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.deviation_centre_curvature_conformity = 'pass'
                        break
                    else:
                        record.deviation_centre_curvature_conformity = 'fail'

    deviation_centre_curvature_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_deviation_centre_curvature_nabl", store=True)

    @api.depends('deviation_centre_curvature','eln_ref','grade')
    def _compute_deviation_centre_curvature_nabl(self):
        
        for record in self:
            record.deviation_centre_curvature_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','873e02d1-db08-43d8-a88f-f6de09d41955')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','873e02d1-db08-43d8-a88f-f6de09d41955')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.deviation_centre_curvature - record.deviation_centre_curvature*mu_value
                    upper = record.deviation_centre_curvature + record.deviation_centre_curvature*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.deviation_centre_curvature_nabl = 'pass'
                        break
                    else:
                        record.deviation_centre_curvature_nabl = 'fail'




      # Edge Curvature

    edge_curvature_name = fields.Char("Name",default="Edge Curvature")
    edge_curvature_visible = fields.Boolean("Edge Curvature Visible",compute="_compute_visible")   

    edge_curvature_sample_size = fields.Integer(string="Sample Size, mm")
    edge_curvature_diagonal  = fields.Integer(string="Diagonal, mm")

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_edge_curvature = fields.One2many('mechanical.edge.curvature.tile.line1','parent_id',string="Parameter")

    average_edge_curvature = fields.Float(string="Average ", compute="_compute_average_edge_curvature",digits=(16,3))

    deviation_edge_curvature = fields.Float(string="Maximum Edge Curvature, mm ",compute="_compute_deviation_edge_curvature", digits=(16,3))
    requirement_edge_curvature = fields.Char(string="Requirement, Maximum Edge Curvature,%",compute="_compute_requirement_edge_curvature")

    maximum_edge_curvature = fields.Float(string="Maximum edge Curvature,mm",compute="_compute_maximum_edge_curvature",store=True,digits=(16,3))

    @api.depends('child_lines_edge_curvature.edge_curvature1', 'child_lines_edge_curvature.edge_curvature2',
                 'child_lines_edge_curvature.edge_curvature3', 'child_lines_edge_curvature.edge_curvature4')
    def _compute_maximum_edge_curvature(self):
        for tile in self:
            max_value = 0.0
            for line in tile.child_lines_edge_curvature:
                max_in_line = max(line.edge_curvature1, line.edge_curvature2, line.edge_curvature3, line.edge_curvature4)
                if max_in_line > max_value:
                    max_value = max_in_line
            tile.maximum_edge_curvature = max_value

    @api.depends('size')
    def _compute_requirement_edge_curvature(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '2c4efee6-d22a-4eec-afbb-5435f3041f3f')
        ], limit=1)

        for record in self:
            record.requirement_edge_curvature = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_edge_curvature = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)


    @api.depends('child_lines_edge_curvature.edge_curvature1',  'child_lines_edge_curvature.edge_curvature2',  'child_lines_edge_curvature.edge_curvature3',  'child_lines_edge_curvature.edge_curvature4' )
    def _compute_average_edge_curvature(self):
        for record in self:
            if record.child_lines_edge_curvature:
                # Calculate the total sum of all edge_curvature fields across child lines
                total = sum(
                    line.edge_curvature1 + line.edge_curvature2 + line.edge_curvature3 + line.edge_curvature4
                    for line in record.child_lines_edge_curvature
                )
                # Calculate the total number of edge_curvature values
                count = len(record.child_lines_edge_curvature) * 4  # 4 edge_curvature fields per line
                record.average_edge_curvature = total / count if count > 0 else 0.0
            else:
                record.average_edge_curvature = 0.0

    @api.depends('maximum_edge_curvature', 'edge_curvature_sample_size')
    def _compute_deviation_edge_curvature(self):
        for record in self:
            if record.edge_curvature_sample_size and record.edge_curvature_sample_size > 0:
                record.deviation_edge_curvature = (record.maximum_edge_curvature / record.edge_curvature_sample_size) * 100
            else:
                record.deviation_edge_curvature = 0.0

    deviation_edge_curvature_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_deviation_edge_curvature_conformity", store=True)



    @api.depends('deviation_edge_curvature','eln_ref','grade')
    def _compute_deviation_edge_curvature_conformity(self):
        
        for record in self:
            record.deviation_edge_curvature_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2c4efee6-d22a-4eec-afbb-5435f3041f3f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2c4efee6-d22a-4eec-afbb-5435f3041f3f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.deviation_edge_curvature - record.deviation_edge_curvature*mu_value
                    upper = record.deviation_edge_curvature + record.deviation_edge_curvature*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.deviation_edge_curvature_conformity = 'pass'
                        break
                    else:
                        record.deviation_edge_curvature_conformity = 'fail'

    deviation_edge_curvature_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_deviation_edge_curvature_nabl", store=True)

    @api.depends('deviation_edge_curvature','eln_ref','grade')
    def _compute_deviation_edge_curvature_nabl(self):
        
        for record in self:
            record.deviation_edge_curvature_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2c4efee6-d22a-4eec-afbb-5435f3041f3f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2c4efee6-d22a-4eec-afbb-5435f3041f3f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.deviation_edge_curvature - record.deviation_edge_curvature*mu_value
                    upper = record.deviation_edge_curvature + record.deviation_edge_curvature*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.deviation_edge_curvature_nabl = 'pass'
                        break
                    else:
                        record.deviation_edge_curvature_nabl = 'fail'



       # warpage

    warpage_name = fields.Char("Name",default="Warpage")
    warpage_visible = fields.Boolean("Warpage Visible",compute="_compute_visible")   

    warpage_sample_size = fields.Integer(string="Sample Size, mm")
    warpage_diagonal  = fields.Integer(string="Diagonal, mm ")

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_warpage = fields.One2many('mechanical.warpage.tile.line1','parent_id',string="Parameter")

    average_warpage = fields.Float(string="Average ", compute="_compute_average_warpage",digits=(16,3))

    deviation_warpage = fields.Float(string="Maximum warpage, % ",compute="_compute_deviation_warpage", digits=(16,3))
    requirement_warpage = fields.Char(string="Requirement, Maximum Warpage, %",compute="_compute_requirement_warpage")

    maximum_warpage = fields.Float(string="Maximum Warpage mm",compute="_compute_maximum_warpage",store=True,digits=(16,3))

    @api.depends('child_lines_warpage.warpage1', 'child_lines_warpage.warpage2',
                 'child_lines_warpage.warpage3', 'child_lines_warpage.warpage4')
    def _compute_maximum_warpage(self):
        for tile in self:
            max_value = 0.0
            for line in tile.child_lines_warpage:
                max_in_line = max(line.warpage1, line.warpage2, line.warpage3, line.warpage4)
                if max_in_line > max_value:
                    max_value = max_in_line
            tile.maximum_warpage = max_value


    @api.depends('size')
    def _compute_requirement_warpage(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '91fc2258-6bd7-40d4-82d8-404af0928ae9')
        ], limit=1)

        for record in self:
            record.requirement_warpage = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_warpage = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)


    @api.depends('child_lines_warpage.warpage1',  'child_lines_warpage.warpage2',  'child_lines_warpage.warpage3',  'child_lines_warpage.warpage4' )
    def _compute_average_warpage(self):
        for record in self:
            if record.child_lines_warpage:
                # Calculate the total sum of all warpage fields across child lines
                total = sum(
                    line.warpage1 + line.warpage2 + line.warpage3 + line.warpage4
                    for line in record.child_lines_warpage
                )
                # Calculate the total number of warpage values
                count = len(record.child_lines_warpage) * 4  # 4 warpage fields per line
                record.average_warpage = total / count if count > 0 else 0.0
            else:
                record.average_warpage = 0.0

    @api.depends('maximum_warpage', 'warpage_diagonal')
    def _compute_deviation_warpage(self):
        for record in self:
            if record.warpage_diagonal and record.warpage_diagonal > 0:
                record.deviation_warpage = (record.maximum_warpage / record.warpage_diagonal) * 100
            else:
                record.deviation_warpage = 0.0


    deviation_warpage_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_deviation_warpage_conformity", store=True)



    @api.depends('deviation_warpage','eln_ref','grade')
    def _compute_deviation_warpage_conformity(self):
        
        for record in self:
            record.deviation_warpage_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','91fc2258-6bd7-40d4-82d8-404af0928ae9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','91fc2258-6bd7-40d4-82d8-404af0928ae9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.deviation_warpage - record.deviation_warpage*mu_value
                    upper = record.deviation_warpage + record.deviation_warpage*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.deviation_warpage_conformity = 'pass'
                        break
                    else:
                        record.deviation_warpage_conformity = 'fail'

    deviation_warpage_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_deviation_warpage_nabl", store=True)

    @api.depends('deviation_warpage','eln_ref','grade')
    def _compute_deviation_warpage_nabl(self):
        
        for record in self:
            record.deviation_warpage_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','91fc2258-6bd7-40d4-82d8-404af0928ae9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','91fc2258-6bd7-40d4-82d8-404af0928ae9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.deviation_warpage - record.deviation_warpage*mu_value
                    upper = record.deviation_warpage + record.deviation_warpage*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.deviation_warpage_nabl = 'pass'
                        break
                    else:
                        record.deviation_warpage_nabl = 'fail'




     # water absorption and bulk density

    water_ab_bulk_name1 = fields.Char("Name",default="Water Absorption")
    water_bulk_visible = fields.Boolean("water absorption and bulk density Visible",compute="_compute_visible")   

   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_water_bulk = fields.One2many('mechanical.water.bulk.tile.line1','parent_id',string="Parameter")

    average_water_bulk = fields.Float(string="Water Absorption, % (average) ",compute="_compute_average_water_bulk",digits=(16,1))


    average_water_bulk_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Water Absorption, % (average) Conformity", compute="_compute_average_water_bulk_conformity", store=True)



    @api.depends('average_water_bulk','eln_ref','grade')
    def _compute_average_water_bulk_conformity(self):
        
        for record in self:
            record.average_water_bulk_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1578liop-ed58-4374-bda7-2825e12f307c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1578liop-ed58-4374-bda7-2825e12f307c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_water_bulk - record.average_water_bulk*mu_value
                    upper = record.average_water_bulk + record.average_water_bulk*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_water_bulk_conformity = 'pass'
                        break
                    else:
                        record.average_water_bulk_conformity = 'fail'

    average_water_bulk_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Water Absorption, % (average) NABL", compute="_compute_average_water_bulk_nabl", store=True)

    @api.depends('average_water_bulk','eln_ref','grade')
    def _compute_average_water_bulk_nabl(self):
        
        for record in self:
            record.average_water_bulk_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1578liop-ed58-4374-bda7-2825e12f307c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1578liop-ed58-4374-bda7-2825e12f307c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_water_bulk - record.average_water_bulk*mu_value
                    upper = record.average_water_bulk + record.average_water_bulk*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_water_bulk_nabl = 'pass'
                        break
                    else:
                        record.average_water_bulk_nabl = 'fail'

    individual_water_bulk = fields.Float(string="Water Absorption, % (Individual) ",compute="_compute_individual_water_bulk",digits=(16,1),store=True)

    individual_water_bulk_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Water Absorption, % (Individual) Conformity", compute="_compute_individual_water_bulk_conformity", store=True)



    @api.depends('individual_water_bulk','eln_ref','grade')
    def _compute_individual_water_bulk_conformity(self):
        
        for record in self:
            record.individual_water_bulk_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4211b8db-2bb3-4821-958d-ec2c81db5698')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4211b8db-2bb3-4821-958d-ec2c81db5698')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.individual_water_bulk - record.individual_water_bulk*mu_value
                    upper = record.individual_water_bulk + record.individual_water_bulk*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.individual_water_bulk_conformity = 'pass'
                        break
                    else:
                        record.individual_water_bulk_conformity = 'fail'

    individual_water_bulk_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Water Absorption, % (Individual) NABL", compute="_compute_individual_water_bulk_nabl", store=True)

    @api.depends('individual_water_bulk','eln_ref','grade')
    def _compute_individual_water_bulk_nabl(self):
        
        for record in self:
            record.individual_water_bulk_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4211b8db-2bb3-4821-958d-ec2c81db5698')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4211b8db-2bb3-4821-958d-ec2c81db5698')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.individual_water_bulk - record.individual_water_bulk*mu_value
                    upper = record.individual_water_bulk + record.individual_water_bulk*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.individual_water_bulk_nabl = 'pass'
                        break
                    else:
                        record.individual_water_bulk_nabl = 'fail'


    #    Bulk Density
    bulk_name1 = fields.Char("Name",default="Bulk Density")
    bulk_visible = fields.Boolean(" bulk density Visible",compute="_compute_visible")   

   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_bulk = fields.One2many('mechanical.bulk.tile.line1','parent_id',string="Parameter")
    bulk_density = fields.Float(string="Bulk Density, g/cc",compute="_compute_bulk_density1",digits=(16,2))

    requirement_water = fields.Char(string="Requirement, Water Absorption, % (Average)",compute="_compute_requirement_water")
    requirement_water_individual = fields.Char(string="Requirement, Water Absorption, % (Individual)",compute="_compute_requirement_water_individual")
    requirement_bulk = fields.Char(string="Requirement, Bulk Density, g/cc",compute="_compute_requirement_bulk")

    water_group = fields.Selection([
            ('bia', 'Group BIa'),
            ('bib', 'Group BIb'),
            ('biia', 'Group BIIa'),
            ('biib', 'Group BIIb'),
            ('biii', 'Group BIII')
        ], string="Group")


    # @api.depends('child_lines_water_bulk.water_obsorption')
    # def _compute_average_water_bulk(self):
    #     for record in self:
    #         # Calculate the average of water_obsorption across child lines
    #         total = sum(line.water_obsorption for line in record.child_lines_water_bulk if line.water_obsorption)
    #         count = len(record.child_lines_water_bulk)
    #         record.average_water_bulk = total / count if count > 0 else 0.0

 


    @api.depends('child_lines_water_bulk.water_obsorption')
    def _compute_average_water_bulk(self):
        for record in self:
            total = sum(line.water_obsorption for line in record.child_lines_water_bulk if line.water_obsorption)
            count = len(record.child_lines_water_bulk)
            record.average_water_bulk = total / count if count > 0 else 0.0

            # Assign the appropriate water group based on the calculated average
            if 0.00 <= record.average_water_bulk <= 0.008:
                record.water_group = 'bia'  # Group BIa
            elif 0.008 < record.average_water_bulk <= 3.00:
                record.water_group = 'bib'  # Group BIb
            elif 3.00 < record.average_water_bulk <= 6.00:
                record.water_group = 'biia'  # Group BIIa
            elif 6.00 < record.average_water_bulk <= 10.00:
                record.water_group = 'biib'  # Group BIIb
            else:
                record.water_group = 'biii'  # Group BIII

  

    @api.depends('size')
    def _compute_requirement_water(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '1578liop-ed58-4374-bda7-2825e12f307c')
        ], limit=1)

        for record in self:
            record.requirement_water = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_water = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)


    # @api.depends('child_lines_water_bulk.water_obsorption')
    # def _compute_individual_water_bulk(self):
    #     for record in self:
    #         # Fetch the maximum water_obsorption value from child lines
    #         max_value = max(
    #             (line.water_obsorption for line in record.child_lines_water_bulk if line.water_obsorption), 
    #             default=0.0
    #         )
    #         record.individual_water_bulk = max_value


    @api.depends('child_lines_water_bulk.water_obsorption', 'water_group')
    def _compute_individual_water_bulk(self):
        for record in self:
            values = [line.water_obsorption for line in record.child_lines_water_bulk if line.water_obsorption is not None]
            if not values:
                record.individual_water_bulk = 0.0
            elif record.water_group in ['bia', 'bib', 'biia', 'biib']:
                record.individual_water_bulk = max(values)
            elif record.water_group == 'biii':
                record.individual_water_bulk = min(values)
            else:
                record.individual_water_bulk = 0.0

    @api.depends('size')
    def _compute_requirement_water_individual(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '4211b8db-2bb3-4821-958d-ec2c81db5698')
        ], limit=1)

        for record in self:
            record.requirement_water_individual = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_water_individual = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)



    @api.depends('size')
    def _compute_requirement_bulk(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '25489lku-2bb3-4821-958d-ec2c81db5698')
        ], limit=1)

        for record in self:
            record.requirement_bulk = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_bulk = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)


    @api.depends('child_lines_bulk.bulk_density')
    def _compute_bulk_density1(self):
        for record in self:
            # Calculate the average of bulk_density across child lines
            total = sum(line.bulk_density for line in record.child_lines_bulk if line.bulk_density)
            count = len(record.child_lines_bulk)
            record.bulk_density = total / count if count > 0 else 0.0


    bulk_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Bulk Density Conformity", compute="_compute_bulk_density_conformity", store=True)



    @api.depends('bulk_density','eln_ref','grade')
    def _compute_bulk_density_conformity(self):
        
        for record in self:
            record.bulk_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25489lku-2bb3-4821-958d-ec2c81db5698')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25489lku-2bb3-4821-958d-ec2c81db5698')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.bulk_density - record.bulk_density*mu_value
                    upper = record.bulk_density + record.bulk_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.bulk_density_conformity = 'pass'
                        break
                    else:
                        record.bulk_density_conformity = 'fail'

    bulk_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Bulk Density NABL", compute="_compute_bulk_density_nabl", store=True)

    @api.depends('bulk_density','eln_ref','grade')
    def _compute_bulk_density_nabl(self):
        
        for record in self:
            record.bulk_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25489lku-2bb3-4821-958d-ec2c81db5698')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25489lku-2bb3-4821-958d-ec2c81db5698')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.bulk_density - record.bulk_density*mu_value
                    upper = record.bulk_density + record.bulk_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.bulk_density_nabl = 'pass'
                        break
                    else:
                        record.bulk_density_nabl = 'fail'




    

      # Modulus and rupture and breaking strength

    modulus_rupture_name = fields.Char("Name",default="Modulus Of Rupture And Breaking Strength")
    modulus_visible = fields.Boolean("Modulus Of Rupture And Breaking Strength Visible",compute="_compute_visible")   

   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_modulus = fields.One2many('mechanical.modulus.tile.line1','parent_id',string="Parameter")

    average_modulus = fields.Float(string="Modulus of Rupture, N/mm2 (Average)",compute="_compute_average_modulus",digits=(16,2))

    average_modulus_thickness = fields.Float(string="Thickness,mm",compute="_compute_average_modulus_thickness",digits=(16,2))


    @api.depends('child_lines_modulus.thickness')
    def _compute_average_modulus_thickness(self):
        for record in self:
            # Calculate the average of thickness across child lines
            total = sum(line.thickness for line in record.child_lines_modulus if line.thickness)
            count = len(record.child_lines_modulus)
            record.average_modulus_thickness = total / count if count > 0 else 0.0

    modulus_group = fields.Selection([
            ('bia', 'Group BIa'),
            ('bib', 'Group BIb'),
            ('biia', 'Group BIIa'),
            ('biib', 'Group BIIb'),
            ('biii', 'Group BIII')
        ], string="Group", compute="_compute_modulus_group", store=True)


    @api.depends('average_modulus', 'average_modulus_thickness')
    def _compute_modulus_group(self):
        for record in self:
            if record.average_modulus_thickness:
                thickness = record.average_modulus_thickness
                modulus = record.average_modulus

                if thickness <= 7.5:
                    if modulus >= 35:
                        record.modulus_group = 'bia'
                    elif modulus >= 30:
                        record.modulus_group = 'bib'
                    elif modulus >= 22:
                        record.modulus_group = 'biia'
                    elif modulus >= 18:
                        record.modulus_group = 'biib'
                    elif modulus >= 15:
                        record.modulus_group = 'biii'
                    else:
                        record.modulus_group = False  # No group assigned if below 15
                else:  # thickness > 7.5
                    if modulus >= 35:
                        record.modulus_group = 'bia'
                    elif modulus >= 30:
                        record.modulus_group = 'bib'
                    elif modulus >= 22:
                        record.modulus_group = 'biia'
                    elif modulus >= 18:
                        record.modulus_group = 'biib'
                    elif modulus >= 15:
                        record.modulus_group = 'biii'
                    else:
                        record.modulus_group = False  # No group assigned if below 15


    average_modulus_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Modulus of Rupture, N/mm2 (Average) Conformity", compute="_compute_average_modulus_conformity", store=True)



    @api.depends('average_modulus','eln_ref','grade')
    def _compute_average_modulus_conformity(self):
        
        for record in self:
            record.average_modulus_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5879opff-6bd7-40d4-82d8-404af0928ae9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5879opff-6bd7-40d4-82d8-404af0928ae9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_modulus - record.average_modulus*mu_value
                    upper = record.average_modulus + record.average_modulus*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_modulus_conformity = 'pass'
                        break
                    else:
                        record.average_modulus_conformity = 'fail'

    average_modulus_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Modulus of Rupture, N/mm2 (Average) NABL", compute="_compute_average_modulus_nabl", store=True)

    @api.depends('average_modulus','eln_ref','grade')
    def _compute_average_modulus_nabl(self):
        
        for record in self:
            record.average_modulus_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5879opff-6bd7-40d4-82d8-404af0928ae9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5879opff-6bd7-40d4-82d8-404af0928ae9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_modulus - record.average_modulus*mu_value
                    upper = record.average_modulus + record.average_modulus*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_modulus_nabl = 'pass'
                        break
                    else:
                        record.average_modulus_nabl = 'fail'


    individual_modulus = fields.Float(string="Modulus of Rupture, N/mm2 (Individual)",compute="_compute_individual_modulus",digits=(16,2))

    individual_modulus_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Modulus of Rupture, N/mm2 (Individual) Conformity", compute="_compute_individual_modulus_conformity", store=True)



    @api.depends('individual_modulus','eln_ref','grade')
    def _compute_individual_modulus_conformity(self):
        
        for record in self:
            record.individual_modulus_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5687pkf-6bd7-40d4-82d8-404af0928ae9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5687pkf-6bd7-40d4-82d8-404af0928ae9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.individual_modulus - record.individual_modulus*mu_value
                    upper = record.individual_modulus + record.individual_modulus*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.individual_modulus_conformity = 'pass'
                        break
                    else:
                        record.individual_modulus_conformity = 'fail'

    individual_modulus_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Modulus of Rupture, N/mm2 (Individual) NABL", compute="_compute_individual_modulus_nabl", store=True)

    @api.depends('individual_modulus','eln_ref','grade')
    def _compute_individual_modulus_nabl(self):
        
        for record in self:
            record.individual_modulus_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5687pkf-6bd7-40d4-82d8-404af0928ae9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5687pkf-6bd7-40d4-82d8-404af0928ae9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.individual_modulus - record.individual_modulus*mu_value
                    upper = record.individual_modulus + record.individual_modulus*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.individual_modulus_nabl = 'pass'
                        break
                    else:
                        record.individual_modulus_nabl = 'fail'


    breaking_strenght = fields.Float(string="Breaking Strength, N",compute="_compute_breaking_strenght",digits=(16,1))

    requirement_modulus = fields.Char(string="Requirement ,Modulus of Rupture, N/mm2 (Average)",compute="_compute_requirement_modulus")

    @api.depends('size')
    def _compute_requirement_modulus(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '5879opff-6bd7-40d4-82d8-404af0928ae9')
        ], limit=1)

        for record in self:
            record.requirement_modulus = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_modulus = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)

    requirement_modulus_individual = fields.Char(string="Requirement ,Modulus of rupture, N/mm2 (Individual)",compute="_compute_requirement_modulus_individual")

    @api.depends('size')
    def _compute_requirement_modulus_individual(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '5687pkf-6bd7-40d4-82d8-404af0928ae9')
        ], limit=1)

        for record in self:
            record.requirement_modulus_individual = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_modulus_individual = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)


    requirement_modulus_breaking = fields.Char(string="Requirement ,Breaking Strength, N",compute="_compute_requirement_modulus_breaking")



    @api.depends('size')
    def _compute_requirement_modulus_breaking(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '3257lhdg-6bd7-40d4-82d8-404af0928ae9')
        ], limit=1)

        for record in self:
            record.requirement_modulus_breaking = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_modulus_breaking = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)



    @api.depends('child_lines_modulus.mor')
    def _compute_average_modulus(self):
        for record in self:
            # Calculate the average of mor across child lines
            total = sum(line.mor for line in record.child_lines_modulus if line.mor)
            count = len(record.child_lines_modulus)
            record.average_modulus = total / count if count > 0 else 0.0


    @api.depends('child_lines_modulus.mor')
    def _compute_individual_modulus(self):
        for record in self:
            # Fetch the maximum mor value from child lines
            max_value = min(
                (line.mor for line in record.child_lines_modulus if line.mor), 
                default=0.0
            )
            record.individual_modulus = max_value


    @api.depends('child_lines_modulus.bs')
    def _compute_breaking_strenght(self):
        for record in self:
            # Calculate the average of bs across child lines
            total = sum(line.bs for line in record.child_lines_modulus if line.bs)
            count = len(record.child_lines_modulus)
            record.breaking_strenght = total / count if count > 0 else 0.0

    breaking_strenght_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Breaking Strength Conformity", compute="_compute_breaking_strenght_conformity", store=True)



    @api.depends('breaking_strenght','eln_ref','grade')
    def _compute_breaking_strenght_conformity(self):
        
        for record in self:
            record.breaking_strenght_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3257lhdg-6bd7-40d4-82d8-404af0928ae9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3257lhdg-6bd7-40d4-82d8-404af0928ae9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.breaking_strenght - record.breaking_strenght*mu_value
                    upper = record.breaking_strenght + record.breaking_strenght*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.breaking_strenght_conformity = 'pass'
                        break
                    else:
                        record.breaking_strenght_conformity = 'fail'

    breaking_strenght_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Breaking Strength NABL", compute="_compute_breaking_strenght_nabl", store=True)

    @api.depends('breaking_strenght','eln_ref','grade')
    def _compute_breaking_strenght_nabl(self):
        
        for record in self:
            record.breaking_strenght_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3257lhdg-6bd7-40d4-82d8-404af0928ae9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3257lhdg-6bd7-40d4-82d8-404af0928ae9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.breaking_strenght - record.breaking_strenght*mu_value
                    upper = record.breaking_strenght + record.breaking_strenght*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.breaking_strenght_nabl = 'pass'
                        break
                    else:
                        record.breaking_strenght_nabl = 'fail'


        # crazing resistance test

    crazing_resistance_name = fields.Char("Name",default="Crazing Resistance Test")
    crazing_visible = fields.Boolean("crazing resistance test Visible",compute="_compute_visible")  

    requirement_crazing = fields.Char(string="Requirement, Crazing Resistance Test",compute="_compute_requirement_crazing")


    @api.depends('size')
    def _compute_requirement_crazing(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '0157651d-76f3-428a-9a89-f47593d1fd42')
        ], limit=1)

        for record in self:
            record.requirement_crazing = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_crazing = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)


    observations = fields.Selection(
        [
            ('crazing_observed', 'Crazing effect was observed'),
            ('crazing_observed1st', 'Crazing Effect was Observed in 1st Cycle @7.5 Bar'),
            ('crazing_observed2nd', 'Crazing Effect was Observed in 2nd Cycle @7.5 Bar'),
            ('crazing_observed3rd', 'Crazing Effect was Observed in 3rd Cycle @7.5 Bar'),
            ('crazing_observed4th', 'Crazing Effect was Observed in 4th Cycle @7.5 Bar'),
            ('no_crazing_observed', 'No Crazing Effect was Observed After 4th Cycle @ 7.5 Bar')
            
        ],
        string="Observations",
         # Default to "No crazing effect was observed"
    ) 



        # chemical resistance test

    chemical_resistance_name1 = fields.Char("Name",default="Resistance to Staining")
    chemical_visible = fields.Boolean("chemical resistance test Visible",compute="_compute_visible")  

    observations_alkalis = fields.Char(string="Observations")
    requirement_alkalis = fields.Char(string="Requirement",compute="_compute_requirement_alkalis")

    @api.depends('size')
    def _compute_requirement_alkalis(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', 'daa5edf4-4f0a-4625-a1b8-4b365204be34')
        ], limit=1)

        for record in self:
            record.requirement_alkalis = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_alkalis = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)





      #Resistanceto acidsand alkalis Un Glazed tiles

    observations_alkalis_name1 = fields.Char("Name",default="Resistance to household Chemicals and swimming pool water cleansers except to cleasing agent containing hydroflouric acids and its compounds.")
    observations_alkalis_visible = fields.Boolean("chemical resistance test Visible",compute="_compute_visible")  

    observations_alkalis_un = fields.Char(string="Observations")
    requirement_alkalis_un = fields.Char(string="Requirement",compute="_compute_requirement_alkalis_un")


    @api.depends('size')
    def _compute_requirement_alkalis_un(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '65eefe82-1c17-43d6-8d24-31cad21f017a')
        ], limit=1)

        for record in self:
            record.requirement_alkalis_un = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_alkalis_un = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)
 

#  Scratch hardness According to Moh's Scale
    
    scratch_hardness_name = fields.Char("Name",default="Scratch hardness According to Moh's Scale")
    scratch_hardness_visible = fields.Boolean("Surface Quality",compute="_compute_visible") 

    observations1 = fields.Float(string="Observations")
    observations2 = fields.Float(string="Observations")
    observations3 = fields.Float(string="Observations")
    observations4 = fields.Float(string="Observations")
    observations5 = fields.Float(string="Observations")

    scratch_hardness_avg = fields.Float(string="Scratch hardness According to Moh's Scale",compute="_compute_scratch_hardness_avg")

    requirement_scratch_hardness = fields.Char(string="Requirement ,Scratch hardness According to Moh's Scale",compute="_compute_requirement_scratch_hardness")


    @api.depends('size')
    def _compute_requirement_scratch_hardness(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', 'ecfb0b0b-0774-4296-af7b-6151fbf4f968')
        ], limit=1)

        for record in self:
            record.requirement_scratch_hardness = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_scratch_hardness = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)

    @api.depends('observations1', 'observations2', 'observations3', 'observations4', 'observations5')
    def _compute_scratch_hardness_avg(self):
        for record in self:
            values = [record.observations1, record.observations2, record.observations3, record.observations4, record.observations5]
            total = sum(value for value in values if value)
            count = sum(1 for value in values if value)
            record.scratch_hardness_avg = total / count if count > 0 else 0
            


    surface_quality_name = fields.Char("Name",default="Surface Quality")
    surface_quality_visible = fields.Boolean("Surface Quality",compute="_compute_visible")  

    observations_surface_quality = fields.Char(string="Observations")
    requirement_surface_quality = fields.Char(string="Requirement, Surface Quality",compute="_compute_requirement_surface_quality")


    @api.depends('size')
    def _compute_requirement_surface_quality(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', '56f97e43-cd99-458c-9bce-4c72ba6d7e84')
        ], limit=1)

        for record in self:
            record.requirement_surface_quality = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_surface_quality = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)







   ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.dimension_visible = False
            record.straightness_visible = False
            record.rectangularity_visible = False
            record.centre_curvature_visible = False
            record.edge_curvature_visible = False
            record.warpage_visible = False
            record.water_bulk_visible = False
            record.modulus_visible = False
            record.crazing_visible = False
            record.chemical_visible = False
            record.observations_alkalis_visible = False
            record.surface_quality_visible = False
            record.scratch_hardness_visible = False
            record.deviation_thickness_visible = False
            record.bulk_visible = False
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
                if sample.internal_id == "1db41e6d-550e-4c5d-a923-7510a616beb5":
                    record.dimension_visible = True

                if sample.internal_id == "19999f82-79c0-44a8-9379-f40dd33235aa":
                    record.straightness_visible = True

                if sample.internal_id == "4e209b70-f6b9-49b9-bab6-f38292f64b1c":
                    record.rectangularity_visible = True

                if sample.internal_id == "873e02d1-db08-43d8-a88f-f6de09d41955":
                    record.centre_curvature_visible = True


                if sample.internal_id == "2c4efee6-d22a-4eec-afbb-5435f3041f3f":
                    record.edge_curvature_visible = True
               
                if sample.internal_id == "91fc2258-6bd7-40d4-82d8-404af0928ae9":
                    record.warpage_visible = True

                if sample.internal_id == "5d81b405-ed58-4374-bda7-2825e12f307c":
                    record.water_bulk_visible = True

                if sample.internal_id == "f9fb0d98-1891-496f-9ef3-4745c5598085":
                    record.modulus_visible = True

                if sample.internal_id == "0157651d-76f3-428a-9a89-f47593d1fd42":
                    record.crazing_visible = True

                if sample.internal_id == "daa5edf4-4f0a-4625-a1b8-4b365204be34":
                    record.chemical_visible = True

                if sample.internal_id == "65eefe82-1c17-43d6-8d24-31cad21f017a":
                    record.observations_alkalis_visible = True

                if sample.internal_id == "56f97e43-cd99-458c-9bce-4c72ba6d7e84":
                    record.surface_quality_visible = True

                if sample.internal_id == "ecfb0b0b-0774-4296-af7b-6151fbf4f968":
                    record.scratch_hardness_visible = True
                
                if sample.internal_id == "35777f82-79c0-44a8-9379-f40dd33235uyt":
                    record.deviation_thickness_visible = True

                if sample.internal_id == "25489lku-2bb3-4821-958d-ec2c81db5698":
                    record.bulk_visible = True






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
        record = super(Tile, self).create(vals)
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
        record = self.env['mechanical.tile1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


class DimensionTile(models.Model):
    _name = "mechanical.dimension.tile.line1"
    parent_id = fields.Many2one('mechanical.tile1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)
    length1 = fields.Float(string="Length, mm 1",digits=(12,3))
    length2 = fields.Float(string="Length, mm 2",digits=(12,3))
    length3 = fields.Float(string="Length, mm 3",digits=(12,3))
    length4 = fields.Float(string="Length, mm 4",digits=(12,3))

    width1 = fields.Float(string="Width, mm 1",digits=(12,3))
    width2 = fields.Float(string="Width, mm 2",digits=(12,3))
    width3 = fields.Float(string="Width, mm 3",digits=(12,3))
    width4 = fields.Float(string="Width, mm 4",digits=(12,3))

    thickness1 = fields.Float(string="Thickness, mm 1",digits=(12,3))
    thickness2 = fields.Float(string="Thickness, mm 2",digits=(12,3))
    thickness3 = fields.Float(string="Thickness, mm 3",digits=(12,3))
    thickness4 = fields.Float(string="Thickness, mm 4",digits=(12,3))
    thickness5 = fields.Float(string="Thickness, mm 5",digits=(12,3))
    thickness6 = fields.Float(string="Thickness, mm 6",digits=(12,3))

  



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(DimensionTile, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class StraightnessTile(models.Model):
    _name = "mechanical.straightness.tile.line1"
    parent_id = fields.Many2one('mechanical.tile1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    straightness1 = fields.Float(string="Straightness 1",digits=(12,3))
    straightness2 = fields.Float(string="Straightness 2",digits=(12,3))
    straightness3 = fields.Float(string="Straightness 3",digits=(12,3))
    straightness4 = fields.Float(string="Straightness 4",digits=(12,3))

   

  



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(StraightnessTile, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class RectangularityTile(models.Model):
    _name = "mechanical.rectangularity.tile.line1"
    parent_id = fields.Many2one('mechanical.tile1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    rectangularity1 = fields.Float(string="Rectangularity 1",digits=(12,3))
    rectangularity2 = fields.Float(string="Rectangularity 2",digits=(12,3))
    rectangularity3 = fields.Float(string="Rectangularity 3",digits=(12,3))
    rectangularity4 = fields.Float(string="Rectangularity 4",digits=(12,3))

   

  



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(RectangularityTile, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class CentreCurvatureTile(models.Model):
    _name = "mechanical.centre.curvature.tile.line1"
    parent_id = fields.Many2one('mechanical.tile1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    centre_curvature1 = fields.Float(string="Centre Curvature 1",digits=(12,3))
    centre_curvature2 = fields.Float(string="Centre Curvature 2",digits=(12,3))
    centre_curvature3 = fields.Float(string="Centre Curvature 3",digits=(12,3))
    centre_curvature4 = fields.Float(string="Centre Curvature 4",digits=(12,3))

   

  



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(CentreCurvatureTile, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class EdgeCurvatureTile(models.Model):
    _name = "mechanical.edge.curvature.tile.line1"
    parent_id = fields.Many2one('mechanical.tile1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    edge_curvature1 = fields.Float(string="Edge Curvature 1",digits=(12,3))
    edge_curvature2 = fields.Float(string="Edge Curvature 2",digits=(12,3))
    edge_curvature3 = fields.Float(string="Edge Curvature 3",digits=(12,3))
    edge_curvature4 = fields.Float(string="Edge Curvature 4",digits=(12,3))

   

  



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(EdgeCurvatureTile, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class WarpageTile(models.Model):
    _name = "mechanical.warpage.tile.line1"
    parent_id = fields.Many2one('mechanical.tile1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    warpage1 = fields.Float(string="Warpage 1",digits=(12,3))
    warpage2 = fields.Float(string="Warpage 2",digits=(12,3))
    warpage3 = fields.Float(string="Warpage 3",digits=(12,3))
    warpage4 = fields.Float(string="Warpage 4",digits=(12,3))

   

  



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(WarpageTile, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class WaterAndBulkTile(models.Model):
    _name = "mechanical.water.bulk.tile.line1"
    parent_id = fields.Many2one('mechanical.tile1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    mass_dry = fields.Float(string="Mass of the dry tile M1 (g)",digits=(12,1))
    mass_wet = fields.Float(string="Mass of the wet tile  M2(g)",digits=(12,1))
    water_obsorption = fields.Float(string="water absorption  ((M2-M1)/M1)*100  (%)",compute="_compute_water_absorption",digits=(12,2),store=True)
    # oven_dry = fields.Float(string="Oven Dry Weight, g",digits=(12,3))
    # wet_weight = fields.Float(string="Wet Weight, g",digits=(12,3))
    # water_obsorption = fields.Float(string="Water Absorption , %",compute="_compute_water_absorption",digits=(12,3))
    # bulk_density = fields.Float(string="Bulk Density ,g/cc",compute="_compute_bulk_density",digits=(12,3))


    # @api.depends('wet_weight', 'oven_dry')
    # def _compute_water_absorption(self):
    #     for record in self:
    #         if record.oven_dry and record.oven_dry > 0:  # Ensure oven_dry is not zero to avoid division by zero
    #             record.water_obsorption = ((record.wet_weight - record.oven_dry) / record.oven_dry) * 100
    #         else:
    #             record.water_obsorption = 0.0  # Default to 0 if calculation is invalid

    # @api.depends('oven_dry', 'lenght', 'width', 'thickness')
    # def _compute_bulk_density(self):
    #     for record in self:
    #         if record.lenght > 0 and record.width > 0 and record.thickness > 0:  # Ensure dimensions are valid
    #             volume = record.lenght * record.width * record.thickness
    #             record.bulk_density = (record.oven_dry / volume) * 1000
    #         else:
    #             record.bulk_density = 0.0  # Default to 0 if dimensions are invalid



    @api.depends('mass_dry', 'mass_wet')
    def _compute_water_absorption(self):
        for record in self:
            if record.mass_dry:
                record.water_obsorption = ((record.mass_wet - record.mass_dry) / record.mass_dry) * 100
            else:
                record.water_obsorption = 0.0

   

  



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(WaterAndBulkTile, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1





class BulkTile(models.Model):
    _name = "mechanical.bulk.tile.line1"
    parent_id = fields.Many2one('mechanical.tile1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    mass_dry1 = fields.Float(string="Mass of the dry tile(g) (m1)",digits=(12,2))
    mass_wet1 = fields.Float(string="Mass of the wet tile(g) (m2)",digits=(12,2))
    mass_suspended = fields.Float(string="Mass of suspended tile (g) (m3)",digits=(12,2))
    exterior_volume = fields.Float(string="V = exterior volume, in cm3 (m2-m3)",digits=(12,2),compute="_compute_exterior_volume")
    bulk_density = fields.Float(string="Bulk Density ,g/cc",compute="_compute_bulk_density",digits=(12,2))


    @api.depends('mass_wet1', 'mass_suspended')
    def _compute_exterior_volume(self):
        for record in self:
            record.exterior_volume = record.mass_wet1 - record.mass_suspended if record.mass_wet1 and record.mass_suspended else 0.0

    @api.depends('mass_dry1', 'exterior_volume')
    def _compute_bulk_density(self):
        for record in self:
            if record.exterior_volume:
                record.bulk_density = record.mass_dry1 / record.exterior_volume
            else:
                record.bulk_density = 0.0



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(BulkTile, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class ModulusTile(models.Model):
    _name = "mechanical.modulus.tile.line1"
    parent_id = fields.Many2one('mechanical.tile1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

   
    width = fields.Float(string="Width",digits=(12,2))
    span = fields.Float(string="Span",digits=(12,2))
    thickness = fields.Float(string="Thickness",digits=(12,2))
    peak_load = fields.Float(string="PEAK LOAD (N)",digits=(12,2))
    mor = fields.Float(string="MOR (N/mm2)",compute="_compute_mor_and_bs",digits=(12,2))
    bs = fields.Float(string="BS (N)",compute="_compute_mor_and_bs",digits=(12,1))


    @api.depends('peak_load', 'span', 'width', 'thickness')
    def _compute_mor_and_bs(self):
        for record in self:
            # Calculate MOR
            if record.width > 0 and record.thickness > 0:  # Ensure valid inputs
                record.mor = (3 * record.peak_load * record.span) / (2 * record.width * (record.thickness ** 2))
            else:
                record.mor = 0.0  # Default to 0 if inputs are invalid

            # Calculate BS
            if record.width > 0:  # Ensure valid input
                record.bs = (record.peak_load * record.span) / record.width
            else:
                record.bs = 0.0  # Default to 0 if width is invalid

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(ModulusTile, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1