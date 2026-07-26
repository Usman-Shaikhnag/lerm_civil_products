from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math



class ChequeredCementTile(models.Model):
    _name = "mechanical.cement.chequered.tile"
    _inherit = "lerm.eln"
    _description = 'mechanical.cement.chequered.tile'
    _rec_name = "name"

    name = fields.Char("Name",default="Cement Concrete flooring Tiles")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    temperature = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    # Dimension

    dimension_name = fields.Char("Name",default="Dimension")
    dimension_visible = fields.Boolean("Dimension Visible",compute="_compute_visible") 

    
    dimension_child_lines = fields.One2many('cement.chequered.dimension.tile.line','parent_id',string="Parameter")


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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','20f5379b-dac0-491f-88d7-e7dacf0e889c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','20f5379b-dac0-491f-88d7-e7dacf0e889c')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','20f5379b-dac0-491f-88d7-e7dacf0e889c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','20f5379b-dac0-491f-88d7-e7dacf0e889c')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c86695b0-2d1d-4340-95a6-e518b8a09b85')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c86695b0-2d1d-4340-95a6-e518b8a09b85')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c86695b0-2d1d-4340-95a6-e518b8a09b85')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c86695b0-2d1d-4340-95a6-e518b8a09b85')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5b0138de-c8c3-4c53-abbc-726bf248158f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5b0138de-c8c3-4c53-abbc-726bf248158f')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5b0138de-c8c3-4c53-abbc-726bf248158f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5b0138de-c8c3-4c53-abbc-726bf248158f')]).parameter_table
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

    flatness_name = fields.Char("Name",default="Flatness")
    flatness_visible = fields.Boolean("Flatness Visible",compute="_compute_visible") 

    
    flat_concavity_child_lines = fields.One2many('cement.chequered.concavity.line','parent_id',string="Parameter")


    sample_concavity = fields.Float(
        string='Concavity of Sample = Maximum recorded gap among the six tiles = ',
        compute='_compute_sample_concavity',
        store=True
    )

    @api.depends('flat_concavity_child_lines.maximum_gap')
    def _compute_sample_concavity(self):
        for rec in self:
            rec.sample_concavity = max(
                rec.flat_concavity_child_lines.mapped('maximum_gap') or [0.0]
            )


    flat_convexity_child_lines = fields.One2many('cement.chequered.convexity.line','parent_id',string="Parameter")

    sample_convexity = fields.Float(
        string='Convexity of Sample = Maximum recorded gap among the six tiles = ',
        compute='_compute_sample_convexity',
        store=True
    )

    @api.depends('flat_convexity_child_lines.maximum_gap')
    def _compute_sample_convexity(self):
        for rec in self:
            rec.sample_convexity = max(
                rec.flat_convexity_child_lines.mapped('maximum_gap') or [0.0]
            )


    concavity_result = fields.Selection(
    [('pass', 'PASS'), ('fail', 'FAIL')],
    compute='_compute_concavity_result',
    store=True
)

    @api.depends('sample_concavity')
    def _compute_concavity_result(self):
     for rec in self:
        rec.concavity_result = (
            'pass' if rec.sample_concavity <= 1.0 else 'fail'
        )

    convexity_result = fields.Selection(
    [('pass', 'PASS'), ('fail', 'FAIL')],
    compute='_compute_convexity_result',
    store=True
)

    @api.depends('sample_convexity')
    def _compute_convexity_result(self):
     for rec in self:
        rec.convexity_result = (
            'pass' if rec.sample_convexity <= 1.0 else 'fail'
        )


    sample_concavity_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Concavity Confirmity',compute="_compute_sample_concavity_confirmity")
    
    @api.depends('sample_concavity','eln_ref','grade')
    def _compute_sample_concavity_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.sample_concavity_confirmity = 'na'
                continue
            record.sample_concavity_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6812d5b4-4e99-4c08-aa50-d62041af9a43')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6812d5b4-4e99-4c08-aa50-d62041af9a43')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.sample_concavity - record.sample_concavity*mu_value
                    upper = record.sample_concavity + record.sample_concavity*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.sample_concavity_confirmity = 'pass'
                        break
                    else:
                        record.sample_concavity_confirmity = 'fail'

    sample_concavity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='Concavity NABL', compute="_compute_sample_concavity_nabl",store=True)

    @api.depends('sample_concavity','eln_ref','grade')
    def _compute_sample_concavity_nabl(self):
        
        for record in self:
            record.sample_concavity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6812d5b4-4e99-4c08-aa50-d62041af9a43')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6812d5b4-4e99-4c08-aa50-d62041af9a43')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.sample_concavity - record.sample_concavity*mu_value
                    upper = record.sample_concavity + record.sample_concavity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.sample_concavity_nabl = 'pass'
                        break
                    else:
                        record.sample_concavity_nabl = 'fail'


    sample_concavity_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    sample_concavity_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_sample_concavity_final_report", store=True)

    @api.depends('sample_concavity_nabl', 'sample_concavity_report_type')
    def _compute_sample_concavity_final_report(self):
     for rec in self:

        # Manual override
        if rec.sample_concavity_report_type == 'nabl':
            rec.sample_concavity_final_report = 'nabl'

        elif rec.sample_concavity_report_type == 'non_nabl':
            rec.sample_concavity_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.sample_concavity_nabl == 'pass':
                rec.sample_concavity_final_report = 'nabl'
            else:
                rec.sample_concavity_final_report = 'non_nabl'


    sample_convexity_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Convexity Confirmity',compute="_compute_sample_convexity_confirmity")
    
    @api.depends('sample_convexity','eln_ref','grade')
    def _compute_sample_convexity_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.sample_convexity_confirmity = 'na'
                continue
            record.sample_convexity_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f2bef3d2-5af5-4585-a81d-cda90b1a0e63')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f2bef3d2-5af5-4585-a81d-cda90b1a0e63')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.sample_convexity - record.sample_convexity*mu_value
                    upper = record.sample_convexity + record.sample_convexity*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.sample_convexity_confirmity = 'pass'
                        break
                    else:
                        record.sample_convexity_confirmity = 'fail'

    sample_convexity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='Convexity NABL', compute="_compute_sample_convexity_nabl",store=True)

    @api.depends('sample_convexity','eln_ref','grade')
    def _compute_sample_convexity_nabl(self):
        
        for record in self:
            record.sample_convexity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f2bef3d2-5af5-4585-a81d-cda90b1a0e63')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f2bef3d2-5af5-4585-a81d-cda90b1a0e63')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.sample_convexity - record.sample_convexity*mu_value
                    upper = record.sample_convexity + record.sample_convexity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.sample_convexity_nabl = 'pass'
                        break
                    else:
                        record.sample_convexity_nabl = 'fail'

    sample_convexity_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    sample_convexity_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_sample_convexity_final_report", store=True)

    @api.depends('sample_convexity_nabl', 'sample_convexity_report_type')
    def _compute_sample_convexity_final_report(self):
     for rec in self:

        # Manual override
        if rec.sample_convexity_report_type == 'nabl':
            rec.sample_convexity_final_report = 'nabl'

        elif rec.sample_convexity_report_type == 'non_nabl':
            rec.sample_convexity_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.sample_convexity_nabl == 'pass':
                rec.sample_convexity_final_report = 'nabl'
            else:
                rec.sample_convexity_final_report = 'non_nabl'



    # Perpendicularity

    perpendicularity_name = fields.Char("Name",default="Perpendicularity")
    perpendicularity_visible = fields.Boolean("Perpendicularity Visible",compute="_compute_visible") 


    perpendicularity_line_ids = fields.One2many(
        'cement.chequered.perpendicularity.line',
        'parent_id',
        string='Perpendicularity Lines'
    )

    largest_gap_average = fields.Float(
    string="Largest Gap (mm)",
    compute="_compute_largest_gap_average",
    store=True
)

    @api.depends('perpendicularity_line_ids.largest_gap')
    def _compute_largest_gap_average(self):
     for rec in self:
        lines = rec.perpendicularity_line_ids
        if lines:
            rec.largest_gap_average = sum(lines.mapped('largest_gap')) / len(lines)
        else:
            rec.largest_gap_average = 0.0


    largest_gap_average_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_largest_gap_average_confirmity")
    
    @api.depends('largest_gap_average','eln_ref','grade')
    def _compute_largest_gap_average_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.largest_gap_average_confirmity = 'na'
                continue
            record.largest_gap_average_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3fc2d248-89bd-47c4-846a-e734e1918817')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3fc2d248-89bd-47c4-846a-e734e1918817')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.largest_gap_average - record.largest_gap_average*mu_value
                    upper = record.largest_gap_average + record.largest_gap_average*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.largest_gap_average_confirmity = 'pass'
                        break
                    else:
                        record.largest_gap_average_confirmity = 'fail'

    largest_gap_average_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_largest_gap_average_nabl",store=True)

    @api.depends('largest_gap_average','eln_ref','grade')
    def _compute_largest_gap_average_nabl(self):
        
        for record in self:
            record.largest_gap_average_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3fc2d248-89bd-47c4-846a-e734e1918817')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3fc2d248-89bd-47c4-846a-e734e1918817')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.largest_gap_average - record.largest_gap_average*mu_value
                    upper = record.largest_gap_average + record.largest_gap_average*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.largest_gap_average_nabl = 'pass'
                        break
                    else:
                        record.largest_gap_average_nabl = 'fail'

    largest_gap_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    largest_gap_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_largest_gap_final_report", store=True)

    @api.depends('largest_gap_average_nabl', 'largest_gap_report_type')
    def _compute_largest_gap_final_report(self):
     for rec in self:

        # Manual override
        if rec.largest_gap_report_type == 'nabl':
            rec.largest_gap_final_report = 'nabl'

        elif rec.largest_gap_report_type == 'non_nabl':
            rec.largest_gap_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.largest_gap_average_nabl == 'pass':
                rec.largest_gap_final_report = 'nabl'
            else:
                rec.largest_gap_final_report = 'non_nabl'



    # Straightness

    straightness_name = fields.Char("Name",default="Straightness")
    straightness_visible = fields.Boolean("Straightness Visible",compute="_compute_visible") 

    straightness_line_ids = fields.One2many(
        'cement.chequered.straightness.tile.line',
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b2fec3de-ae1e-499c-8191-1eff44a8bd63')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b2fec3de-ae1e-499c-8191-1eff44a8bd63')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b2fec3de-ae1e-499c-8191-1eff44a8bd63')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b2fec3de-ae1e-499c-8191-1eff44a8bd63')]).parameter_table
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
        'cement.chequered.water.absorption.line',
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1d4b2168-dc52-42ef-bd64-a492d8bd1b28')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1d4b2168-dc52-42ef-bd64-a492d8bd1b28')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1d4b2168-dc52-42ef-bd64-a492d8bd1b28')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1d4b2168-dc52-42ef-bd64-a492d8bd1b28')]).parameter_table
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

     


     
      ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.dimension_visible = False
            record.flatness_visible = False
            record.perpendicularity_visible = False
            record.straightness_visible = False
            record.water_absorption_visible = False
            
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

        
                if sample.internal_id == "ff7acf76-50c7-4863-86e2-23b93e2cbfc3":
                    record.dimension_visible = True

                if sample.internal_id == "6812d5b4-4e99-4c08-aa50-d62041af9a43":
                    record.flatness_visible = True

                if sample.internal_id == "3fc2d248-89bd-47c4-846a-e734e1918817":
                    record.perpendicularity_visible = True

                if sample.internal_id == "b2fec3de-ae1e-499c-8191-1eff44a8bd63":
                    record.straightness_visible = True

                if sample.internal_id == "1d4b2168-dc52-42ef-bd64-a492d8bd1b28":
                    record.water_absorption_visible = True



               





    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()

            
            # Dimension
            if result.parameter.internal_id == 'ff7acf76-50c7-4863-86e2-23b93e2cbfc3':
                result.calculated = True

            # Length
            if result.parameter.internal_id == '20f5379b-dac0-491f-88d7-e7dacf0e889c':
                result.calculated = True
                result.result_char = round(self.avg_length,2)
                if self.avg_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Width
            if result.parameter.internal_id == 'c86695b0-2d1d-4340-95a6-e518b8a09b85':
                result.calculated = True
                result.result_char = round(self.avg_width,2)
                if self.avg_width_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Thickness
            if result.parameter.internal_id == '5b0138de-c8c3-4c53-abbc-726bf248158f':
                result.calculated = True
                result.result_char = round(self.avg_thickness,2)
                if self.avg_thickness_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Flatness Concavity
            if result.parameter.internal_id == '6812d5b4-4e99-4c08-aa50-d62041af9a43':
                result.calculated = True
                result.result_char = round(self.sample_concavity,2)
                if self.sample_concavity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Flatness Convexity
            if result.parameter.internal_id == 'f2bef3d2-5af5-4585-a81d-cda90b1a0e63':
                result.calculated = True
                result.result_char = round(self.sample_concavity,2)
                if self.sample_concavity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Perpendicularity
            if result.parameter.internal_id == '3fc2d248-89bd-47c4-846a-e734e1918817':
                result.calculated = True
                result.result_char = round(self.largest_gap_average,2)
                if self.largest_gap_average_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Straightness
            if result.parameter.internal_id == 'b2fec3de-ae1e-499c-8191-1eff44a8bd63':
                result.calculated = True
                result.result_char = round(self.straightness_max_gap,2)
                if self.straightness_max_gap_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            
            # Water Absorption
            if result.parameter.internal_id == '1d4b2168-dc52-42ef-bd64-a492d8bd1b28':
                result.calculated = True
                result.result_char = round(self.average_water_absorption,2)
                if self.average_water_absorption_nabl == 'pass':
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
        record = super(ChequeredCementTile, self).create(vals)
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
        record = self.env['mechanical.cement.chequered.tile'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    notes_id = fields.One2many('mechanical.cement.chequered.tile.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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



class CementChequeredDimensionTile(models.Model):
    _name = "cement.chequered.dimension.tile.line"
    parent_id = fields.Many2one('mechanical.cement.chequered.tile',string="Parent Id")
   
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

        return super(CementChequeredDimensionTile, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class CementChequeredConcavityLine(models.Model):
    _name = 'cement.chequered.concavity.line'
    _description = 'Tile Concavity Measurement'

    parent_id = fields.Many2one('mechanical.cement.chequered.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Tile ID",readonly=True, copy=False, default=1)

    gap_diagonal_1 = fields.Float(string="Gap along Diagonal-1 (mm)")
    gap_diagonal_2 = fields.Float(string="Gap along Diagonal-2 (mm)")

    maximum_gap = fields.Float(string="Maximum Gap (mm)",compute="_compute_maximum_gap",store=True )

    requirement = fields.Float(string="Requirement (<= 1 mm)",default=1.0)

    result = fields.Selection(
        [
            ('pass', 'PASS'),
            ('fail', 'FAIL')
        ],
        string="Result",
        compute="_compute_result",
        store=True
    )

    @api.depends('gap_diagonal_1', 'gap_diagonal_2')
    def _compute_maximum_gap(self):
        for rec in self:
            rec.maximum_gap = max(
                rec.gap_diagonal_1 or 0.0,
                rec.gap_diagonal_2 or 0.0
            )

    @api.depends('maximum_gap')
    def _compute_result(self):
     for rec in self:
        rec.result = 'pass' if rec.maximum_gap <= 1.0 else 'fail'


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(CementChequeredConcavityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class CementChequeredConvexityLine(models.Model):
    _name = 'cement.chequered.convexity.line'
    _description = 'Tile Convexity Measurement'

    parent_id = fields.Many2one('mechanical.cement.chequered.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Tile ID",readonly=True, copy=False, default=1)

    gap_diagonal_1 = fields.Float(
        string='Gap along Diagonal-1 (mm)'
    )

    gap_diagonal_2 = fields.Float(
        string='Gap along Diagonal-2 (mm)'
    )

    maximum_gap = fields.Float(
        string='Maximum Gap (mm)',
        compute='_compute_maximum_gap',
        store=True
    )

    requirement = fields.Float(
        string='Requirement (≤ 1 mm)',
        default=1.0
    )

    result = fields.Selection(
        [
            ('pass', 'PASS'),
            ('fail', 'FAIL')
        ],
        string="Result",
        compute="_compute_result",
        store=True
    )

    @api.depends('gap_diagonal_1', 'gap_diagonal_2')
    def _compute_maximum_gap(self):
        for rec in self:
            rec.maximum_gap = max(
                rec.gap_diagonal_1 or 0.0,
                rec.gap_diagonal_2 or 0.0
            )

    @api.depends('maximum_gap')
    def _compute_result(self):
     for rec in self:
        rec.result = 'pass' if rec.maximum_gap <= 1.0 else 'fail'


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(CementChequeredConvexityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class CementChequeredPerpendicularityLine(models.Model):
    _name = 'cement.chequered.perpendicularity.line'
    _description = 'Tile Gap Inspection Line'

    parent_id = fields.Many2one('mechanical.cement.chequered.tile',string="Parent Id")
   
    sr_no = fields.Integer(string="Tile ID",readonly=True, copy=False, default=1)

    edge_length = fields.Float(
        string='Edge Length (mm)'
    )

    gap_side_1 = fields.Float(
        string='Gap on Side 1 (mm)'
    )

    gap_opposite_side_1 = fields.Float(
        string='Gap on Opposite Side-1 (mm)'
    )

    largest_gap = fields.Float(
        string='Largest Gap (mm)',
        compute='_compute_largest_gap',
        store=True
    )

    permissible_gap = fields.Float(
        string='Permissible Gap (mm)',
        compute='_compute_permissible_gap',
        store=True
    )

    # maximum_gap_observed = fields.Float(
    #     string='Maximum Gap Observed (mm)',
    #     compute='_compute_maximum_gap_observed',
    #     store=True
    # )

    @api.depends('gap_side_1', 'gap_opposite_side_1')
    def _compute_largest_gap(self):
        for rec in self:
            rec.largest_gap = max(
                rec.gap_side_1 or 0.0,
                rec.gap_opposite_side_1 or 0.0
            )

    @api.depends('edge_length')
    def _compute_permissible_gap(self):
        for rec in self:
            rec.permissible_gap = (rec.edge_length or 0.0) * 0.02

    # @api.depends('largest_gap')
    # def _compute_maximum_gap_observed(self):
    #     for rec in self:
    #         rec.maximum_gap_observed = rec.largest_gap


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(CementChequeredPerpendicularityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1




class CementChequeredStraightnessTile(models.Model):
    _name = "cement.chequered.straightness.tile.line"
    parent_id = fields.Many2one('mechanical.cement.chequered.tile',string="Parent Id")
   
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

        return super(CementChequeredStraightnessTile, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class CementChequeredWaterAbsorptionLine(models.Model):
    _name = "cement.chequered.water.absorption.line"
    parent_id = fields.Many2one('mechanical.cement.chequered.tile',string="Parent Id")
   
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

        return super(CementChequeredWaterAbsorptionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1




class ChequeredCementTileNotes(models.Model):
    _name = "mechanical.cement.chequered.tile.notes"

    parent_id = fields.Many2one('mechanical.cement.chequered.tile', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
