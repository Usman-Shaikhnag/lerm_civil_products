from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math



class Tile(models.Model):
    _name = "mechanical.tile"
    _inherit = "lerm.eln"
    _description = 'mechanical.tile'
    _rec_name = "name"

    name = fields.Char("Name",default="TILE")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    temp = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)


    @api.depends("eln_ref")
    def _compute_size_id(self):
        for record in self:
            print("Size iD",record.eln_ref.size_id)
            record.size_id = record.eln_ref.size_id.id


    def get_all_fields(self):
        record = self.env['mechanical.tile'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



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

    dimension_name = fields.Char("Name",default="Dimension")
    dimension_visible = fields.Boolean("Dimension Visible",compute="_compute_visible") 

    
    dimension_child_lines = fields.One2many('mechanical.dimension.tile.line','parent_id',string="Parameter")


    avg_length = fields.Float(string="Average Length (mm)",compute="_compute_avg_dimensions",store=True,digits=(12,3))
    avg_width = fields.Float(string="Average Width (mm)",compute="_compute_avg_dimensions",store=True,digits=(12,3))
    avg_thickness = fields.Float(string="Average Thckness (mm)",compute="_compute_avg_dimensions",store=True,digits=(12,3))
    dimension_remarks = fields.Char(string="Remarks")

    @api.depends(
        'dimension_child_lines.length',
        'dimension_child_lines.width',
        'dimension_child_lines.thickness'
    )
    def _compute_avg_dimensions(self):
        for rec in self:
            lines = rec.dimension_child_lines

            if lines:
                rec.avg_length = sum(lines.mapped('length')) / len(lines)
                rec.avg_width = sum(lines.mapped('width')) / len(lines)
                rec.avg_thickness = sum(lines.mapped('thickness')) / len(lines)
            else:
                rec.avg_length = 0.0
                rec.avg_width = 0.0
                rec.avg_thickness = 0.0


    avg_length_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_length_confirmity")
    
    @api.depends('avg_length','eln_ref','grade')
    def _compute_avg_length_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_length_confirmity = 'na'
                continue
            record.avg_length_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4a2a0491-0292-4331-98ac-9f79d7fc8705')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4a2a0491-0292-4331-98ac-9f79d7fc8705')]).parameter_table
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
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_length_nabl",store=True)

    @api.depends('avg_length','eln_ref','grade')
    def _compute_avg_length_nabl(self):
        
        for record in self:
            record.avg_length_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4a2a0491-0292-4331-98ac-9f79d7fc8705')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4a2a0491-0292-4331-98ac-9f79d7fc8705')]).parameter_table
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


    avg_width_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_width_confirmity")
    
    @api.depends('avg_width','eln_ref','grade')
    def _compute_avg_width_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_width_confirmity = 'na'
                continue
            record.avg_width_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9163a2a2-d969-44f7-8455-66c0799cc61a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9163a2a2-d969-44f7-8455-66c0799cc61a')]).parameter_table
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
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_width_nabl",store=True)

    @api.depends('avg_width','eln_ref','grade')
    def _compute_avg_width_nabl(self):
        
        for record in self:
            record.avg_width_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9163a2a2-d969-44f7-8455-66c0799cc61a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9163a2a2-d969-44f7-8455-66c0799cc61a')]).parameter_table
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



    avg_thickness_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_thickness_confirmity")
    
    @api.depends('avg_thickness','eln_ref','grade')
    def _compute_avg_thickness_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_thickness_confirmity = 'na'
                continue
            record.avg_thickness_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9bf7c4a0-641f-4ea5-918a-313315486ad7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9bf7c4a0-641f-4ea5-918a-313315486ad7')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_thickness - record.avg_thickness*mu_value
                    upper = record.avg_thickness + record.avg_thickness*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_thickness_confirmity = 'pass'
                        break
                    else:
                        record.avg_thickness_confirmity = 'fail'

    avg_thickness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_thickness_nabl",store=True)

    @api.depends('avg_thickness','eln_ref','grade')
    def _compute_avg_thickness_nabl(self):
        
        for record in self:
            record.avg_thickness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9bf7c4a0-641f-4ea5-918a-313315486ad7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9bf7c4a0-641f-4ea5-918a-313315486ad7')]).parameter_table
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


    avg_thickness_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_thickness_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_thickness_final_report", store=True)

    @api.depends('avg_thickness_nabl', 'avg_thickness_report_type')
    def _compute_avg_thickness_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_thickness_report_type == 'nabl':
            rec.avg_thickness_final_report = 'nabl'

        elif rec.avg_thickness_report_type == 'non_nabl':
            rec.avg_thickness_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_thickness_nabl == 'pass':
                rec.avg_thickness_final_report = 'nabl'
            else:
                rec.avg_thickness_final_report = 'non_nabl'



    # Flatness

#     flatness_name = fields.Char("Name",default="Flatness")
#     flatness_visible = fields.Boolean("Flatness Visible",compute="_compute_visible") 

    
#     flat_concavity_child_lines = fields.One2many('tile.concavity.line','parent_id',string="Parameter")


#     sample_concavity = fields.Float(
#         string='Concavity of Sample = Maximum recorded gap among the six tiles = ',
#         compute='_compute_sample_concavity',
#         store=True
#     )

#     @api.depends('flat_concavity_child_lines.maximum_gap')
#     def _compute_sample_concavity(self):
#         for rec in self:
#             rec.sample_concavity = max(
#                 rec.flat_concavity_child_lines.mapped('maximum_gap') or [0.0]
#             )


#     flat_convexity_child_lines = fields.One2many('tile.convexity.line','parent_id',string="Parameter")

#     sample_convexity = fields.Float(
#         string='Convexity of Sample = Maximum recorded gap among the six tiles = ',
#         compute='_compute_sample_convexity',
#         store=True
#     )

#     @api.depends('flat_convexity_child_lines.maximum_gap')
#     def _compute_sample_convexity(self):
#         for rec in self:
#             rec.sample_convexity = max(
#                 rec.flat_convexity_child_lines.mapped('maximum_gap') or [0.0]
#             )


#     concavity_result = fields.Selection(
#     [('pass', 'PASS'), ('fail', 'FAIL')],
#     compute='_compute_concavity_result',
#     store=True
# )

#     @api.depends('sample_concavity')
#     def _compute_concavity_result(self):
#      for rec in self:
#         rec.concavity_result = (
#             'pass' if rec.sample_concavity <= 1.0 else 'fail'
#         )

#     convexity_result = fields.Selection(
#     [('pass', 'PASS'), ('fail', 'FAIL')],
#     compute='_compute_convexity_result',
#     store=True
# )

#     @api.depends('sample_convexity')
#     def _compute_convexity_result(self):
#      for rec in self:
#         rec.convexity_result = (
#             'pass' if rec.sample_convexity <= 1.0 else 'fail'
#         )



    # Perpendicularity

    # perpendicularity_name = fields.Char("Name",default="Perpendicularity")
    # perpendicularity_visible = fields.Boolean("Perpendicularity Visible",compute="_compute_visible") 


    # perpendicularity_line_ids = fields.One2many(
    #     'tile.perpendicularity.line',
    #     'parent_id',
    #     string='Perpendicularity Lines'
    # )

    # maximum_gap_observed = fields.Float(
    #     string='Maximum Gap Observed (mm)',
    #     compute='_compute_maximum_gap_observed',
    #     store=True
    # )

    # @api.depends('perpendicularity_line_ids.largest_gap')
    # def _compute_maximum_gap_observed(self):
    #  for rec in self:
    #     gaps = rec.perpendicularity_line_ids.mapped('largest_gap')
    #     rec.maximum_gap_observed = max(gaps) if gaps else 0.0


    # Straightness

    straightness_name = fields.Char("Name",default="Straightness")
    straightness_visible = fields.Boolean("Straightness Visible",compute="_compute_visible") 

    straightness_line_ids = fields.One2many(
        'mechanical.straightness.tile.line',
        'parent_id',
        string='Straightness Lines'
    )

    straightness_max_gap = fields.Float(
        string='Maximum Gap Observed (mm)',
        compute='_compute_straightness_max_gap',
        store=True
    )

    @api.depends('straightness_line_ids.maximum_gap_observed')
    def _compute_straightness_max_gap(self):
        for rec in self:
            gaps = rec.straightness_line_ids.mapped('maximum_gap_observed')
            rec.straightness_max_gap = max(gaps) if gaps else 0.0


    straightness_max_gap_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_straightness_max_gap_confirmity")
    
    @api.depends('straightness_max_gap','eln_ref','grade')
    def _compute_straightness_max_gap_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.straightness_max_gap_confirmity = 'na'
                continue
            record.straightness_max_gap_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','19999f82-79c0-44a8-9379-f40dd33235aa')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','19999f82-79c0-44a8-9379-f40dd33235aa')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.straightness_max_gap - record.straightness_max_gap*mu_value
                    upper = record.straightness_max_gap + record.straightness_max_gap*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.straightness_max_gap_confirmity = 'pass'
                        break
                    else:
                        record.straightness_max_gap_confirmity = 'fail'

    straightness_max_gap_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_straightness_max_gap_nabl",store=True)

    @api.depends('straightness_max_gap','eln_ref','grade')
    def _compute_straightness_max_gap_nabl(self):
        
        for record in self:
            record.straightness_max_gap_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','19999f82-79c0-44a8-9379-f40dd33235aa')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','19999f82-79c0-44a8-9379-f40dd33235aa')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.straightness_max_gap - record.straightness_max_gap*mu_value
                    upper = record.straightness_max_gap + record.straightness_max_gap*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.straightness_max_gap_nabl = 'pass'
                        break
                    else:
                        record.straightness_max_gap_nabl = 'fail'


    straightness_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    straightness_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_straightness_final_report", store=True)

    @api.depends('straightness_max_gap_nabl', 'straightness_report_type')
    def _compute_straightness_final_report(self):
     for rec in self:

        # Manual override
        if rec.straightness_report_type == 'nabl':
            rec.straightness_final_report = 'nabl'

        elif rec.straightness_report_type == 'non_nabl':
            rec.straightness_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.straightness_max_gap_nabl == 'pass':
                rec.straightness_final_report = 'nabl'
            else:
                rec.straightness_final_report = 'non_nabl'


    # Water Absorption
    water_absorption_name = fields.Char("Name",default="Water Absorption")
    water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")   
    
    water_absorption_line_ids = fields.One2many(
        'tile.water.absorption.line',
        'parent_id',
        string='Water Absorption Lines'
    )

    average_water_absorption = fields.Float(
        string='Average Water Absorption (%)',
        compute='_compute_average_absorption',
        store=True
    )

    @api.depends('water_absorption_line_ids.water_absorption')
    def _compute_average_absorption(self):
        for rec in self:
            values = rec.water_absorption_line_ids.mapped('water_absorption')
            rec.average_water_absorption = (
                sum(values) / len(values)
            ) if values else 0.0


    average_water_absorption_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_average_water_absorption_confirmity")
    
    @api.depends('average_water_absorption','eln_ref','grade')
    def _compute_average_water_absorption_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_water_absorption_confirmity = 'na'
                continue
            record.average_water_absorption_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d81b405-ed58-4374-bda7-2825e12f307c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d81b405-ed58-4374-bda7-2825e12f307c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_water_absorption - record.average_water_absorption*mu_value
                    upper = record.average_water_absorption + record.average_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_water_absorption_confirmity = 'pass'
                        break
                    else:
                        record.average_water_absorption_confirmity = 'fail'

    average_water_absorption_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_average_water_absorption_nabl",store=True)

    @api.depends('average_water_absorption','eln_ref','grade')
    def _compute_average_water_absorption_nabl(self):
        
        for record in self:
            record.average_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d81b405-ed58-4374-bda7-2825e12f307c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d81b405-ed58-4374-bda7-2825e12f307c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_water_absorption - record.average_water_absorption*mu_value
                    upper = record.average_water_absorption + record.average_water_absorption*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_water_absorption_nabl = 'pass'
                        break
                    else:
                        record.average_water_absorption_nabl = 'fail'


    water_absorption_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    water_absorption_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_water_absorption_final_report", store=True)

    @api.depends('average_water_absorption_nabl', 'water_absorption_report_type')
    def _compute_water_absorption_final_report(self):
     for rec in self:

        # Manual override
        if rec.water_absorption_report_type == 'nabl':
            rec.water_absorption_final_report = 'nabl'

        elif rec.water_absorption_report_type == 'non_nabl':
            rec.water_absorption_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.average_water_absorption_nabl == 'pass':
                rec.water_absorption_final_report = 'nabl'
            else:
                rec.water_absorption_final_report = 'non_nabl'

    

    # Bulk Density
    bulk_density_name = fields.Char("Name",default="Bulk Density")
    bulk_density_visible = fields.Boolean("Bulk Density Visible",compute="_compute_visible")   
    
    bulk_density_line_ids = fields.One2many(
        'mechanical.bulk.tile.line',
        'parent_id',
        string='Bulk Density Lines'
    )

    avg_bulk_density = fields.Float(
        string='Average Bulk Density (g/cc)',
        compute='_compute_avg_bulk_density',
        store=True
    )

    @api.depends('bulk_density_line_ids.bulk_density')
    def _compute_avg_bulk_density(self):
        for rec in self:
            lines = rec.bulk_density_line_ids.filtered(lambda l: l.bulk_density)
            rec.avg_bulk_density = (
                sum(lines.mapped('bulk_density')) / len(lines)
                if lines else 0.0
            )

    avg_bulk_density_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_bulk_density_confirmity")
    
    @api.depends('avg_bulk_density','eln_ref','grade')
    def _compute_avg_bulk_density_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_bulk_density_confirmity = 'na'
                continue
            record.avg_bulk_density_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25489lku-2bb3-4821-958d-ec2c81db5698')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25489lku-2bb3-4821-958d-ec2c81db5698')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_bulk_density - record.avg_bulk_density*mu_value
                    upper = record.avg_bulk_density + record.avg_bulk_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_bulk_density_confirmity = 'pass'
                        break
                    else:
                        record.avg_bulk_density_confirmity = 'fail'

    avg_bulk_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_bulk_density_nabl",store=True)

    @api.depends('avg_bulk_density','eln_ref','grade')
    def _compute_avg_bulk_density_nabl(self):
        
        for record in self:
            record.avg_bulk_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25489lku-2bb3-4821-958d-ec2c81db5698')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','25489lku-2bb3-4821-958d-ec2c81db5698')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_bulk_density - record.avg_bulk_density*mu_value
                    upper = record.avg_bulk_density + record.avg_bulk_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_bulk_density_nabl = 'pass'
                        break
                    else:
                        record.avg_bulk_density_nabl = 'fail'


    bulk_density_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    bulk_density_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_bulk_density_final_report", store=True)

    @api.depends('avg_bulk_density_nabl', 'bulk_density_report_type')
    def _compute_bulk_density_final_report(self):
     for rec in self:

        # Manual override
        if rec.bulk_density_report_type == 'nabl':
            rec.bulk_density_final_report = 'nabl'

        elif rec.bulk_density_report_type == 'non_nabl':
            rec.bulk_density_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_bulk_density_nabl == 'pass':
                rec.bulk_density_final_report = 'nabl'
            else:
                rec.bulk_density_final_report = 'non_nabl'



    # Rectangularity
    rectangularity_name = fields.Char("Name",default="Rectangularity")
    rectangularity_visible = fields.Boolean("Rectangularity Visible",compute="_compute_visible")   
    
    rectangularity_line_ids = fields.One2many(
        'mechanical.rectangularity.tile.line',
        'parent_id',
        string='Rectangularity Lines')

    average_rectangularity = fields.Float(
    string="Average Rectangularity (%)",
    compute="_compute_average_rectangularity",
    store=True,digits=(10,3))

    @api.depends('rectangularity_line_ids.rectangularity')
    def _compute_average_rectangularity(self):
        for rec in self:
            values = rec.rectangularity_line_ids.mapped('rectangularity')
            rec.average_rectangularity = (
                sum(values) / len(values)
            ) if values else 0.0


    average_rectangularity_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_average_rectangularity_confirmity")
    
    @api.depends('average_rectangularity','eln_ref','grade')
    def _compute_average_rectangularity_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_rectangularity_confirmity = 'na'
                continue
            record.average_rectangularity_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4e209b70-f6b9-49b9-bab6-f38292f64b1c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4e209b70-f6b9-49b9-bab6-f38292f64b1c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_rectangularity - record.average_rectangularity*mu_value
                    upper = record.average_rectangularity + record.average_rectangularity*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_rectangularity_confirmity = 'pass'
                        break
                    else:
                        record.average_rectangularity_confirmity = 'fail'

    average_rectangularity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_average_rectangularity_nabl",store=True)

    @api.depends('average_rectangularity','eln_ref','grade')
    def _compute_average_rectangularity_nabl(self):
        
        for record in self:
            record.average_rectangularity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4e209b70-f6b9-49b9-bab6-f38292f64b1c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4e209b70-f6b9-49b9-bab6-f38292f64b1c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_rectangularity - record.average_rectangularity*mu_value
                    upper = record.average_rectangularity + record.average_rectangularity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_rectangularity_nabl = 'pass'
                        break
                    else:
                        record.average_rectangularity_nabl = 'fail'


    rectangularity_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    rectangularity_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_rectangularity_final_report", store=True)

    @api.depends('average_rectangularity_nabl', 'rectangularity_report_type')
    def _compute_rectangularity_final_report(self):
     for rec in self:

        # Manual override
        if rec.rectangularity_report_type == 'nabl':
            rec.rectangularity_final_report = 'nabl'

        elif rec.rectangularity_report_type == 'non_nabl':
            rec.rectangularity_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.average_rectangularity_nabl == 'pass':
                rec.rectangularity_final_report = 'nabl'
            else:
                rec.rectangularity_final_report = 'non_nabl'


    # Deviation in Length and Width
    deviation_name = fields.Char("Name",default="Deviation in Length and Width")
    deviation_visible = fields.Boolean("Deviation in Length and Width Visible",compute="_compute_visible")   

    work_length = fields.Float(
        string='Work Length (mm)',
    )

    work_width = fields.Float(
        string='Work Width (mm)',
    )
    
    deviation_line_ids = fields.One2many(
        'tile.length.width.line',
        'parent_id',
        string='Deviation in Length and Width Lines')
    

    avg_length_deviation = fields.Float(
        string='Average Length Deviation (%)',
        compute='_compute_average_deviation',
        store=True,
        digits=(16, 3)
    )

    avg_width_deviation = fields.Float(
        string='Average Width Deviation (%)',
        compute='_compute_average_deviation',
        store=True,
        digits=(16, 3)
    )

    @api.depends(
        'deviation_line_ids.length_deviation',
        'deviation_line_ids.width_deviation'
    )
    def _compute_average_deviation(self):
        for rec in self:
            count = len(rec.deviation_line_ids)

            if count:
                rec.avg_length_deviation = (
                    sum(rec.deviation_line_ids.mapped('length_deviation')) / count
                )
                rec.avg_width_deviation = (
                    sum(rec.deviation_line_ids.mapped('width_deviation')) / count
                )
            else:
                rec.avg_length_deviation = 0.0
                rec.avg_width_deviation = 0.0

    
    avg_length_deviation_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_length_deviation_confirmity")
    
    @api.depends('avg_length_deviation','eln_ref','grade')
    def _compute_avg_length_deviation_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_length_deviation_confirmity = 'na'
                continue
            record.avg_length_deviation_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35777f82-79c0-44a8-9379-f40dd33235uyt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35777f82-79c0-44a8-9379-f40dd33235uyt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_length_deviation - record.avg_length_deviation*mu_value
                    upper = record.avg_length_deviation + record.avg_length_deviation*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_length_deviation_confirmity = 'pass'
                        break
                    else:
                        record.avg_length_deviation_confirmity = 'fail'

    avg_length_deviation_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_length_deviation_nabl",store=True)

    @api.depends('avg_length_deviation','eln_ref','grade')
    def _compute_avg_length_deviation_nabl(self):
        
        for record in self:
            record.avg_length_deviation_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35777f82-79c0-44a8-9379-f40dd33235uyt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35777f82-79c0-44a8-9379-f40dd33235uyt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_length_deviation - record.avg_length_deviation*mu_value
                    upper = record.avg_length_deviation + record.avg_length_deviation*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_length_deviation_nabl = 'pass'
                        break
                    else:
                        record.avg_length_deviation_nabl = 'fail'


    length_deviation_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    length_deviation_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_length_deviation_final_report", store=True)

    @api.depends('avg_length_deviation_nabl', 'length_deviation_report_type')
    def _compute_length_deviation_final_report(self):
     for rec in self:

        # Manual override
        if rec.length_deviation_report_type == 'nabl':
            rec.length_deviation_final_report = 'nabl'

        elif rec.length_deviation_report_type == 'non_nabl':
            rec.length_deviation_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_length_deviation_nabl == 'pass':
                rec.length_deviation_final_report = 'nabl'
            else:
                rec.length_deviation_final_report = 'non_nabl'


    avg_width_deviation_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_width_deviation_confirmity")
    
    @api.depends('avg_width_deviation','eln_ref','grade')
    def _compute_avg_width_deviation_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_width_deviation_confirmity = 'na'
                continue
            record.avg_width_deviation_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0b59cf75-9b95-4c36-8042-75e425c80e51')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0b59cf75-9b95-4c36-8042-75e425c80e51')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_width_deviation - record.avg_width_deviation*mu_value
                    upper = record.avg_width_deviation + record.avg_width_deviation*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_width_deviation_confirmity = 'pass'
                        break
                    else:
                        record.avg_width_deviation_confirmity = 'fail'

    avg_width_deviation_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_width_deviation_nabl",store=True)

    @api.depends('avg_width_deviation','eln_ref','grade')
    def _compute_avg_width_deviation_nabl(self):
        
        for record in self:
            record.avg_width_deviation_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0b59cf75-9b95-4c36-8042-75e425c80e51')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0b59cf75-9b95-4c36-8042-75e425c80e51')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_width_deviation - record.avg_width_deviation*mu_value
                    upper = record.avg_width_deviation + record.avg_width_deviation*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_width_deviation_nabl = 'pass'
                        break
                    else:
                        record.avg_width_deviation_nabl = 'fail'


    width_deviation_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    width_deviation_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_width_deviation_final_report", store=True)

    @api.depends('avg_width_deviation_nabl', 'width_deviation_report_type')
    def _compute_width_deviation_final_report(self):
     for rec in self:

        # Manual override
        if rec.width_deviation_report_type == 'nabl':
            rec.width_deviation_final_report = 'nabl'

        elif rec.width_deviation_report_type == 'non_nabl':
            rec.width_deviation_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_width_deviation_nabl == 'pass':
                rec.width_deviation_final_report = 'nabl'
            else:
                rec.width_deviation_final_report = 'non_nabl'


    










   ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.dimension_visible = False
            # record.flatness_visible = False
            # record.perpendicularity_visible = False
            record.straightness_visible = False
            record.water_absorption_visible = False
            record.bulk_density_visible = False
            record.rectangularity_visible = False
            record.deviation_visible = False
           
            
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
                if sample.internal_id == "1db41e6d-550e-4c5d-a923-7510a616beb5":
                    record.dimension_visible = True

                # if sample.internal_id == "db707c33-4b81-431a-9982-f28a825e612c":
                #     record.flatness_visible = True

                # if sample.internal_id == "0fda5ad4-7a03-4d87-9650-553d06555ee8":
                #     record.perpendicularity_visible = True

                if sample.internal_id == "19999f82-79c0-44a8-9379-f40dd33235aa":
                    record.straightness_visible = True

                if sample.internal_id == "5d81b405-ed58-4374-bda7-2825e12f307c":
                    record.water_absorption_visible = True

                if sample.internal_id == "25489lku-2bb3-4821-958d-ec2c81db5698":
                    record.bulk_density_visible = True

                if sample.internal_id == "4e209b70-f6b9-49b9-bab6-f38292f64b1c":
                    record.rectangularity_visible = True

                if sample.internal_id == "35777f82-79c0-44a8-9379-f40dd33235uyt":
                    record.deviation_visible = True

                

                






    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
             

             

            # Dimension
            if result.parameter.internal_id == '1db41e6d-550e-4c5d-a923-7510a616beb5':
                result.calculated = True

            
            # Length
            if result.parameter.internal_id == '4a2a0491-0292-4331-98ac-9f79d7fc8705':
                result.calculated = True
                result.result_char = round(self.avg_length,2)
                if self.avg_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Width
            if result.parameter.internal_id == '9163a2a2-d969-44f7-8455-66c0799cc61a':
                result.calculated = True
                result.result_char = round(self.avg_width,2)
                if self.avg_width_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Thickness
            if result.parameter.internal_id == '9bf7c4a0-641f-4ea5-918a-313315486ad7':
                result.calculated = True
                result.result_char = round(self.avg_thickness,2)
                if self.avg_thickness_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
                

            # Straightness
            if result.parameter.internal_id == '19999f82-79c0-44a8-9379-f40dd33235aa':
                result.calculated = True
                result.result_char = round(self.straightness_max_gap,2)
                if self.straightness_max_gap_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            
            # Water Absorption
            if result.parameter.internal_id == '5d81b405-ed58-4374-bda7-2825e12f307c':
                result.calculated = True
                result.result_char = round(self.average_water_absorption,2)
                if self.average_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Bulk Density
            if result.parameter.internal_id == '25489lku-2bb3-4821-958d-ec2c81db5698':
                result.calculated = True
                result.result_char = round(self.avg_bulk_density,2)
                if self.avg_bulk_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Rectangularity
            if result.parameter.internal_id == '4e209b70-f6b9-49b9-bab6-f38292f64b1c':
                result.calculated = True
                result.result_char = round(self.average_rectangularity,2)
                if self.average_rectangularity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Deviation in Length
            if result.parameter.internal_id == '35777f82-79c0-44a8-9379-f40dd33235uyt':
                result.calculated = True
                result.result_char = round(self.avg_length_deviation,2)
                if self.avg_length_deviation_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Deviation in Width
            if result.parameter.internal_id == '0b59cf75-9b95-4c36-8042-75e425c80e51':
                result.calculated = True
                result.result_char = round(self.avg_width_deviation,2)
                if self.avg_width_deviation_nabl == 'pass':
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
        record = super(Tile, self).create(vals)
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
        record = self.env['mechanical.tile'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    notes_id = fields.One2many('mechanical.tile.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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


class DimensionTile(models.Model):
    _name = "mechanical.dimension.tile.line"
    parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    length = fields.Float(string="Length, mm ",digits=(12,3))
    width = fields.Float(string="Width, mm ",digits=(12,3))
    thickness = fields.Float(string="Thickness, mm ",digits=(12,3))



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


# class TileConcavityLine(models.Model):
#     _name = 'tile.concavity.line'
#     _description = 'Tile Concavity Measurement'
#     parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
#     sr_no = fields.Integer(string="Tile ID",readonly=True, copy=False, default=1)

#     gap_diagonal_1 = fields.Float(string="Gap along Diagonal-1 (mm)")
#     gap_diagonal_2 = fields.Float(string="Gap along Diagonal-2 (mm)")

#     maximum_gap = fields.Float(string="Maximum Gap (mm)",compute="_compute_maximum_gap",store=True )

#     requirement = fields.Float(string="Requirement (<= 1 mm)",default=1.0)

#     result = fields.Selection(
#         [
#             ('pass', 'PASS'),
#             ('fail', 'FAIL')
#         ],
#         string="Result",
#         compute="_compute_result",
#         store=True
#     )

#     @api.depends('gap_diagonal_1', 'gap_diagonal_2')
#     def _compute_maximum_gap(self):
#         for rec in self:
#             rec.maximum_gap = max(
#                 rec.gap_diagonal_1 or 0.0,
#                 rec.gap_diagonal_2 or 0.0
#             )

#     @api.depends('maximum_gap')
#     def _compute_result(self):
#      for rec in self:
#         rec.result = 'pass' if rec.maximum_gap <= 1.0 else 'fail'


#     @api.model
#     def create(self, vals):
#         # Set the serial_no based on the existing records for the same parent
#         if vals.get('parent_id'):
#             existing_records = self.search([('parent_id', '=', vals['parent_id'])])
#             if existing_records:
#                 max_serial_no = max(existing_records.mapped('sr_no'))
#                 vals['sr_no'] = max_serial_no + 1

#         return super(TileConcavityLine, self).create(vals)

#     def _reorder_serial_numbers(self):
#         # Reorder the serial numbers based on the positions of the records in child_lines
#         records = self.sorted('id')
#         for index, record in enumerate(records):
#             record.sr_no = index + 1


# class TileConvexityLine(models.Model):
#     _name = 'tile.convexity.line'
#     _description = 'Tile Convexity Measurement'

#     parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
#     sr_no = fields.Integer(string="Tile ID",readonly=True, copy=False, default=1)

#     gap_diagonal_1 = fields.Float(
#         string='Gap along Diagonal-1 (mm)'
#     )

#     gap_diagonal_2 = fields.Float(
#         string='Gap along Diagonal-2 (mm)'
#     )

#     maximum_gap = fields.Float(
#         string='Maximum Gap (mm)',
#         compute='_compute_maximum_gap',
#         store=True
#     )

#     requirement = fields.Float(
#         string='Requirement (≤ 1 mm)',
#         default=1.0
#     )

#     result = fields.Selection(
#         [
#             ('pass', 'PASS'),
#             ('fail', 'FAIL')
#         ],
#         string="Result",
#         compute="_compute_result",
#         store=True
#     )

#     @api.depends('gap_diagonal_1', 'gap_diagonal_2')
#     def _compute_maximum_gap(self):
#         for rec in self:
#             rec.maximum_gap = max(
#                 rec.gap_diagonal_1 or 0.0,
#                 rec.gap_diagonal_2 or 0.0
#             )

#     @api.depends('maximum_gap')
#     def _compute_result(self):
#      for rec in self:
#         rec.result = 'pass' if rec.maximum_gap <= 1.0 else 'fail'


#     @api.model
#     def create(self, vals):
#         # Set the serial_no based on the existing records for the same parent
#         if vals.get('parent_id'):
#             existing_records = self.search([('parent_id', '=', vals['parent_id'])])
#             if existing_records:
#                 max_serial_no = max(existing_records.mapped('sr_no'))
#                 vals['sr_no'] = max_serial_no + 1

#         return super(TileConvexityLine, self).create(vals)

#     def _reorder_serial_numbers(self):
#         # Reorder the serial numbers based on the positions of the records in child_lines
#         records = self.sorted('id')
#         for index, record in enumerate(records):
#             record.sr_no = index + 1



# class TilePerpendicularityLine(models.Model):
#     _name = 'tile.perpendicularity.line'
#     _description = 'Tile Gap Inspection Line'

#     parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
#     sr_no = fields.Integer(string="Tile ID",readonly=True, copy=False, default=1)

#     edge_length = fields.Float(
#         string='Edge Length (mm)'
#     )

#     gap_side_1 = fields.Float(
#         string='Gap on Side 1 (mm)'
#     )

#     gap_opposite_side_1 = fields.Float(
#         string='Gap on Opposite Side-1 (mm)'
#     )

#     largest_gap = fields.Float(
#         string='Largest Gap (mm)',
#         compute='_compute_largest_gap',
#         store=True
#     )

#     permissible_gap = fields.Float(
#         string='Permissible Gap (mm)',
#         compute='_compute_permissible_gap',
#         store=True
#     )

#     maximum_gap_observed = fields.Float(
#         string='Maximum Gap Observed (mm)',
#         compute='_compute_maximum_gap_observed',
#         store=True
#     )

#     @api.depends('gap_side_1', 'gap_opposite_side_1')
#     def _compute_largest_gap(self):
#         for rec in self:
#             rec.largest_gap = max(
#                 rec.gap_side_1 or 0.0,
#                 rec.gap_opposite_side_1 or 0.0
#             )

#     @api.depends('edge_length')
#     def _compute_permissible_gap(self):
#         for rec in self:
#             rec.permissible_gap = (rec.edge_length or 0.0) * 0.02

#     @api.depends('largest_gap')
#     def _compute_maximum_gap_observed(self):
#         for rec in self:
#             rec.maximum_gap_observed = rec.largest_gap


#     @api.model
#     def create(self, vals):
#         # Set the serial_no based on the existing records for the same parent
#         if vals.get('parent_id'):
#             existing_records = self.search([('parent_id', '=', vals['parent_id'])])
#             if existing_records:
#                 max_serial_no = max(existing_records.mapped('sr_no'))
#                 vals['sr_no'] = max_serial_no + 1

#         return super(TilePerpendicularityLine, self).create(vals)

#     def _reorder_serial_numbers(self):
#         # Reorder the serial numbers based on the positions of the records in child_lines
#         records = self.sorted('id')
#         for index, record in enumerate(records):
#             record.sr_no = index + 1




class StraightnessTile(models.Model):
    _name = "mechanical.straightness.tile.line"
    parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Tile ID",readonly=True, copy=False, default=1)

    edge_length = fields.Float(
        string='Edge Length (mm)'
    )

    permissible_gap = fields.Float(
        string='Permissible Gap (mm)',
        compute='_compute_permissible_gap',
        store=True
    )

    edge_1_gap = fields.Float(string='Edge-1 Gap (mm)')
    edge_2_gap = fields.Float(string='Edge-2 Gap (mm)')
    edge_3_gap = fields.Float(string='Edge-3 Gap (mm)')
    edge_4_gap = fields.Float(string='Edge-4 Gap (mm)')

    maximum_gap_observed = fields.Float(
        string='Maximum Gap Observed (mm)',
        compute='_compute_maximum_gap_observed',
        store=True
    )

    @api.depends('edge_length')
    def _compute_permissible_gap(self):
        for rec in self:
            rec.permissible_gap = (rec.edge_length or 0.0) * 0.01

    @api.depends(
        'edge_1_gap',
        'edge_2_gap',
        'edge_3_gap',
        'edge_4_gap'
    )
    def _compute_maximum_gap_observed(self):
        for rec in self:
            rec.maximum_gap_observed = max([
                rec.edge_1_gap or 0.0,
                rec.edge_2_gap or 0.0,
                rec.edge_3_gap or 0.0,
                rec.edge_4_gap or 0.0,
            ])

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


class TileWaterAbsorptionLine(models.Model):
    _name = "tile.water.absorption.line"
    parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    dry_mass_w1 = fields.Float(
        string='Dry Mass, W1 (g)'
    )

    saturated_mass_w2 = fields.Float(
        string='Saturated Mass, W2 (g)'
    )

    gain_in_mass = fields.Float(
        string='Gain in Mass (g)',
        compute='_compute_values',
        store=True
    )

    water_absorption = fields.Float(
        string='Water Absorption (%)',
        compute='_compute_values',
        store=True,
        digits=(16, 2)
    )

    @api.depends('dry_mass_w1', 'saturated_mass_w2')
    def _compute_values(self):
        for rec in self:
            rec.gain_in_mass = rec.saturated_mass_w2 - rec.dry_mass_w1

            if rec.dry_mass_w1:
                rec.water_absorption = (
                    (rec.saturated_mass_w2 - rec.dry_mass_w1)
                    / rec.dry_mass_w1
                ) * 100
            else:
                rec.water_absorption = 0.0

   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(TileWaterAbsorptionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class RectangularityTile(models.Model):
    _name = "mechanical.rectangularity.tile.line"
    parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    
    corner_1 = fields.Float(string="Corner-1 δ (mm)")
    corner_2 = fields.Float(string="Corner-2 δ (mm)")
    corner_3 = fields.Float(string="Corner-3 δ (mm)")
    corner_4 = fields.Float(string="Corner-4 δ (mm)")

    max_delta = fields.Float(
        string="Maximum δ (mm)",
        compute="_compute_rectangularity",
        store=True
    )

    length_width = fields.Float(string="Length/Width L (mm)")

    rectangularity = fields.Float(
        string="Rectangularity (%)",
        compute="_compute_rectangularity",
        store=True,digits=(10,3))

    result = fields.Selection([
        ('pass', 'PASS'),
        ('fail', 'FAIL')
    ], string="Result", compute="_compute_rectangularity", store=True)

    @api.depends(
        'corner_1', 'corner_2', 'corner_3',
        'corner_4', 'length_width'
    )
    def _compute_rectangularity(self):
        for rec in self:
            rec.max_delta = max([
                rec.corner_1 or 0,
                rec.corner_2 or 0,
                rec.corner_3 or 0,
                rec.corner_4 or 0
            ])

            if rec.length_width:
                rec.rectangularity = (
                    rec.max_delta / rec.length_width
                ) * 100
            else:
                rec.rectangularity = 0

            # Example tolerance
            rec.result = 'pass' if rec.rectangularity <= 0.6 else 'fail'
  



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





class BulkTile(models.Model):
    _name = "mechanical.bulk.tile.line"
    parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    m1 = fields.Float("Mass of the dry tile(g) (m1)")
    m2 = fields.Float("Mass of the wet tile(g) (m2)")
    m3 = fields.Float("Mass of suspended tile (g) (m3)")

    volume = fields.Float(
        string="V = exterior volume, in cm³ (m2-m3)",
        compute="_compute_values",
        store=True
    )

    bulk_density = fields.Float(
        string="Bulk Density ,g/cc",
        compute="_compute_values",
        store=True
    )

    @api.depends('m1', 'm2', 'm3')
    def _compute_values(self):
        for rec in self:
            rec.volume = rec.m2 - rec.m3

            if rec.volume:
                rec.bulk_density = rec.m1 / rec.volume
            else:
                rec.bulk_density = 0.0



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


class TileLengthWidthLine(models.Model):
    _name = 'tile.length.width.line'
    _description = 'Deviation in Length and Width'

    parent_id = fields.Many2one('mechanical.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    length = fields.Float(string='Length (mm)', digits=(16, 2))
    width = fields.Float(string='Width (mm)', digits=(16, 2))

    length_deviation = fields.Float(
        string='Length Deviation (%)',
        compute='_compute_deviation',
        store=True,
        digits=(16, 3)
    )

    width_deviation = fields.Float(
        string='Width Deviation (%)',
        compute='_compute_deviation',
        store=True,
        digits=(16, 3)
    )

    result = fields.Selection([
        ('pass', 'PASS'),
        ('fail', 'FAIL')
    ], string='Result', compute='_compute_deviation', store=True)

    @api.depends(
        'length',
        'width',
        'parent_id.work_length',
        'parent_id.work_width'
    )
    def _compute_deviation(self):
        for rec in self:
            work_length = rec.parent_id.work_length or 0.0
            work_width = rec.parent_id.work_width or 0.0

            rec.length_deviation = (
                ((rec.length - work_length) / work_length) * 100
                if work_length else 0.0
            )

            rec.width_deviation = (
                ((rec.width - work_width) / work_width) * 100
                if work_width else 0.0
            )

            # Example tolerance ±0.5%
            rec.result = (
                'pass'
                if abs(rec.length_deviation) <= 0.5
                and abs(rec.width_deviation) <= 0.5
                else 'fail'
            )


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(TileLengthWidthLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1




class TileNotes(models.Model):
    _name = "mechanical.tile.notes"

    parent_id = fields.Many2one('mechanical.tile', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
