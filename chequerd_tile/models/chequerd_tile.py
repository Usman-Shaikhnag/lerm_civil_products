from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import json
import base64
import qrcode
from io import BytesIO
from lxml import etree



class ChequeredTile(models.Model):
    _name = "mechanical.chequered.tiles"
    _inherit = "lerm.eln"
    _description = 'mechanical.chequered.tiles'
    _rec_name = "name"

    name = fields.Char("Name",default="CHEQUERED TILE")
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

    
    dimension_child_lines = fields.One2many('chequered.dimension.tile.line','parent_id',string="Parameter")


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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','def18047-ab17-42c4-9339-8cd7052f5355')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','def18047-ab17-42c4-9339-8cd7052f5355')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','def18047-ab17-42c4-9339-8cd7052f5355')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','def18047-ab17-42c4-9339-8cd7052f5355')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','eb1d005f-aa0a-4396-8d9b-86892d2c400f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','eb1d005f-aa0a-4396-8d9b-86892d2c400f')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','eb1d005f-aa0a-4396-8d9b-86892d2c400f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','eb1d005f-aa0a-4396-8d9b-86892d2c400f')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ee33d38-9043-4df0-9bf3-64bd9ffa49e8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ee33d38-9043-4df0-9bf3-64bd9ffa49e8')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ee33d38-9043-4df0-9bf3-64bd9ffa49e8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ee33d38-9043-4df0-9bf3-64bd9ffa49e8')]).parameter_table
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


    # Flatness

    flatness_name = fields.Char("Name",default="Flatness")
    flatness_visible = fields.Boolean("Flatness Visible",compute="_compute_visible") 

    
    flat_concavity_child_lines = fields.One2many('chequered.concavity.line','parent_id',string="Parameter")


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


    flat_convexity_child_lines = fields.One2many('chequered.convexity.line','parent_id',string="Parameter")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ff34a8e8-1e82-4f93-8a1d-dd0de56fc290')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ff34a8e8-1e82-4f93-8a1d-dd0de56fc290')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ff34a8e8-1e82-4f93-8a1d-dd0de56fc290')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ff34a8e8-1e82-4f93-8a1d-dd0de56fc290')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9ecdb30-7e5f-4021-a985-be01cf5e0ea1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9ecdb30-7e5f-4021-a985-be01cf5e0ea1')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9ecdb30-7e5f-4021-a985-be01cf5e0ea1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9ecdb30-7e5f-4021-a985-be01cf5e0ea1')]).parameter_table
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



    # Perpendicularity

    perpendicularity_name = fields.Char("Name",default="Perpendicularity")
    perpendicularity_visible = fields.Boolean("Perpendicularity Visible",compute="_compute_visible") 


    perpendicularity_line_ids = fields.One2many(
        'chequered.perpendicularity.line',
        'parent_id',
        string='Perpendicularity Lines'
    )

    maximum_gap_observed = fields.Float(
        string='Maximum Gap Observed (mm)',
        compute='_compute_maximum_gap_observed',
        store=True
    )

    @api.depends('perpendicularity_line_ids.largest_gap')
    def _compute_maximum_gap_observed(self):
     for rec in self:
        gaps = rec.perpendicularity_line_ids.mapped('largest_gap')
        rec.maximum_gap_observed = max(gaps) if gaps else 0.0


    maximum_gap_observed_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_maximum_gap_observed_confirmity")
    
    @api.depends('maximum_gap_observed','eln_ref','grade')
    def _compute_maximum_gap_observed_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.maximum_gap_observed_confirmity = 'na'
                continue
            record.maximum_gap_observed_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4ee01855-218f-48da-9729-82a54306a6c4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4ee01855-218f-48da-9729-82a54306a6c4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.maximum_gap_observed - record.maximum_gap_observed*mu_value
                    upper = record.maximum_gap_observed + record.maximum_gap_observed*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.maximum_gap_observed_confirmity = 'pass'
                        break
                    else:
                        record.maximum_gap_observed_confirmity = 'fail'

    maximum_gap_observed_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_maximum_gap_observed_nabl",store=True)

    @api.depends('maximum_gap_observed','eln_ref','grade')
    def _compute_maximum_gap_observed_nabl(self):
        
        for record in self:
            record.maximum_gap_observed_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4ee01855-218f-48da-9729-82a54306a6c4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4ee01855-218f-48da-9729-82a54306a6c4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.maximum_gap_observed - record.maximum_gap_observed*mu_value
                    upper = record.maximum_gap_observed + record.maximum_gap_observed*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.maximum_gap_observed_nabl = 'pass'
                        break
                    else:
                        record.maximum_gap_observed_nabl = 'fail'



    # Straightness

    straightness_name = fields.Char("Name",default="Straightness")
    straightness_visible = fields.Boolean("Straightness Visible",compute="_compute_visible") 

    straightness_line_ids = fields.One2many(
        'chequered.straightness.tile.line',
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','983a2d9a-3305-4adb-8a79-8842dd64103f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','983a2d9a-3305-4adb-8a79-8842dd64103f')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','983a2d9a-3305-4adb-8a79-8842dd64103f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','983a2d9a-3305-4adb-8a79-8842dd64103f')]).parameter_table
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


    # Water Absorption
    water_absorption_name = fields.Char("Name",default="Water Absorption")
    water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")   
    
    water_absorption_line_ids = fields.One2many(
        'chequered.water.absorption.line',
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b1ef0cc6-cb7d-48da-8c71-4b43f2d5d6f4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b1ef0cc6-cb7d-48da-8c71-4b43f2d5d6f4')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b1ef0cc6-cb7d-48da-8c71-4b43f2d5d6f4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b1ef0cc6-cb7d-48da-8c71-4b43f2d5d6f4')]).parameter_table
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

               
                if sample.internal_id == "ff2e1110-a492-40e9-959a-c989ce4c1903":
                    record.dimension_visible = True

                if sample.internal_id == "ff34a8e8-1e82-4f93-8a1d-dd0de56fc290":
                    record.flatness_visible = True

                if sample.internal_id == "4ee01855-218f-48da-9729-82a54306a6c4":
                    record.perpendicularity_visible = True

                if sample.internal_id == "983a2d9a-3305-4adb-8a79-8842dd64103f":
                    record.straightness_visible = True

                if sample.internal_id == "b1ef0cc6-cb7d-48da-8c71-4b43f2d5d6f4":
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
            if result.parameter.internal_id == 'ff2e1110-a492-40e9-959a-c989ce4c1903':
                result.calculated = True

            # Length
            if result.parameter.internal_id == 'def18047-ab17-42c4-9339-8cd7052f5355':
                result.calculated = True
                result.result_char = round(self.avg_length,2)
                if self.avg_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Width
            if result.parameter.internal_id == 'eb1d005f-aa0a-4396-8d9b-86892d2c400f':
                result.calculated = True
                result.result_char = round(self.avg_width,2)
                if self.avg_width_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Thickness
            if result.parameter.internal_id == '3ee33d38-9043-4df0-9bf3-64bd9ffa49e8':
                result.calculated = True
                result.result_char = round(self.avg_thickness,2)
                if self.avg_thickness_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Flatness Concavity
            if result.parameter.internal_id == 'ff34a8e8-1e82-4f93-8a1d-dd0de56fc290':
                result.calculated = True
                result.result_char = round(self.sample_concavity,2)
                if self.sample_concavity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Flatness Convexity
            if result.parameter.internal_id == 'e9ecdb30-7e5f-4021-a985-be01cf5e0ea1':
                result.calculated = True
                result.result_char = round(self.sample_concavity,2)
                if self.sample_concavity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Perpendicularity
            if result.parameter.internal_id == '4ee01855-218f-48da-9729-82a54306a6c4':
                result.calculated = True
                result.result_char = round(self.maximum_gap_observed,2)
                if self.maximum_gap_observed_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Straightness
            if result.parameter.internal_id == '983a2d9a-3305-4adb-8a79-8842dd64103f':
                result.calculated = True
                result.result_char = round(self.straightness_max_gap,2)
                if self.straightness_max_gap_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            
            # Water Absorption
            if result.parameter.internal_id == 'b1ef0cc6-cb7d-48da-8c71-4b43f2d5d6f4':
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
        record = super(ChequeredTile, self).create(vals)
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
        record = self.env['mechanical.chequered.tile'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    notes_id = fields.One2many('mechanical.chequered.tiles.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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






class ChequeredDimensionTile(models.Model):
    _name = "chequered.dimension.tile.line"
    parent_id = fields.Many2one('mechanical.chequered.tiles',string="Parent Id")
   
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

        return super(ChequeredDimensionTile, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class ChequeredConcavityLine(models.Model):
    _name = 'chequered.concavity.line'
    _description = 'Tile Concavity Measurement'

    parent_id = fields.Many2one('mechanical.chequered.tiles',string="Parent Id")
   
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

        return super(ChequeredConcavityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class ChequeredConvexityLine(models.Model):
    _name = 'chequered.convexity.line'
    _description = 'Tile Convexity Measurement'

    parent_id = fields.Many2one('mechanical.chequered.tiles',string="Parent Id")
   
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

        return super(ChequeredConvexityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class ChequeredPerpendicularityLine(models.Model):
    _name = 'chequered.perpendicularity.line'
    _description = 'Tile Gap Inspection Line'

    parent_id = fields.Many2one('mechanical.chequered.tiles',string="Parent Id")
   
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

    maximum_gap_observed = fields.Float(
        string='Maximum Gap Observed (mm)',
        compute='_compute_maximum_gap_observed',
        store=True
    )

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

    @api.depends('largest_gap')
    def _compute_maximum_gap_observed(self):
        for rec in self:
            rec.maximum_gap_observed = rec.largest_gap


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(ChequeredPerpendicularityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1




class ChequeredStraightnessTile(models.Model):
    _name = "chequered.straightness.tile.line"
    parent_id = fields.Many2one('mechanical.chequered.tiles',string="Parent Id")
   
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

        return super(ChequeredStraightnessTile, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class ChequeredWaterAbsorptionLine(models.Model):
    _name = "chequered.water.absorption.line"
    parent_id = fields.Many2one('mechanical.chequered.tiles',string="Parent Id")
   
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

        return super(ChequeredWaterAbsorptionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class ChequeredTileNotes(models.Model):
    _name = "mechanical.chequered.tiles.notes"

    parent_id = fields.Many2one('mechanical.chequered.tiles', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
