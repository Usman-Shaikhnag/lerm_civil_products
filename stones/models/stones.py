from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math
from decimal import Decimal, ROUND_UP

# import logging
# _logger = logging.getLogger(__name__)


class Stones(models.Model):
    _name = "mechanical.stones"
    _inherit = "lerm.eln"
    _rec_name = "name_stones"


    name_stones = fields.Char("Name",default="Stones")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)


    notes_id = fields.One2many('stone.notes','parent_id',string="Notes")
    


    @api.model
    def default_get(self, fields):
        res = super(Stones, self).default_get(fields)

        default_notes = [
           (0, 0, {'sr_no': 'i', 
                   'notes': 'The results stated in this report apply only to the tested sample(s) and are based on the conditions and parameters at the time of testing.'}),
            (0, 0, {'sr_no': 'ii', 
                    'notes': 'This report is invalid without the official paper seal of Make Infracon.'}),
            (0, 0, {'sr_no': 'iii', 
                    'notes': 'All test results are confidential and will not be disclosed to any third party without written consent of the client, except where required by law.'}),
            (0, 0, {'sr_no': 'iv', 
                    'notes': 'Any discrepancies or complaints regarding this report must be communicated in writing within 7 days from the date of issue.'}),
            (0, 0, {'sr_no': 'v', 
                    'notes': 'This report shall not be reproduced, except in full, without the prior written approval of Make Infracon.'}),
            (0, 0, {'sr_no': 'vi', 
                    'notes': 'The laboratory assumes no responsibility for the purpose for which the test results are used or for any subsequent actions taken based on these results.'}),
        ]

        res['notes_id'] = default_notes
        return res

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'stone.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }


     
    

     # Compressive Strength in dry condition

    compressive_dry_name = fields.Char("Name",default="Compressive Strength in dry condition  ")
    compressive_dry_visible = fields.Boolean("Compressive Strength in dry condition   Visible",compute="_compute_visible")

    compressive_dry_ids = fields.One2many("mechanical.compressive.dry.line", "parent_id", string="Test Readings")

    
    
    @api.onchange('compressive_dry_ids')
    def _onchange_limit_lines(self):
        if len(self.compressive_dry_ids) > 5:
            raise ValidationError("You cannot add more than 5 Test Reading lines.")

    factor_a = fields.Float(string="Constant Factor A",  digits=(12, 4))
    factor_b = fields.Float(string="Constant Factor B",  digits=(12, 4))

    compressive_perpendiculer_avg = fields.Float(
        string="Average Compressive Strength Perpendicular Dry (N/mm²)",
        compute="_compute_average_strengths",
        store=True,
        digits=(12, 2)
    )

    compressive_parallel_avg = fields.Float(
        string="Average Compressive Strength Parallel Dry (N/mm²)",
        compute="_compute_average_strengths",
        store=True,
        digits=(12, 2)
    )

    @api.depends('compressive_dry_ids.compressive_perpendiculer1', 'compressive_dry_ids.compressive_parallel1')
    def _compute_average_strengths(self):
        for record in self:
            perpend_vals = record.compressive_dry_ids.mapped('compressive_perpendiculer1')
            parallel_vals = record.compressive_dry_ids.mapped('compressive_parallel1')

            record.compressive_perpendiculer_avg = (
                sum(perpend_vals) / len(perpend_vals)
                if perpend_vals else 0.0
            )
            record.compressive_parallel_avg = (
                sum(parallel_vals) / len(parallel_vals)
                if parallel_vals else 0.0
            )

    compressive_perpendiculer_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_compressive_perpendiculer_avg_conformity", store=True)

    @api.depends('compressive_perpendiculer_avg','eln_ref','grade')
    def _compute_compressive_perpendiculer_avg_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.compressive_perpendiculer_avg_conformity = 'na'
                continue
            record.compressive_perpendiculer_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5478ttr5-41c5-4cb5-843a-e09590c7c5789hh')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5478ttr5-41c5-4cb5-843a-e09590c7c5789hh')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.compressive_perpendiculer_avg - record.compressive_perpendiculer_avg*mu_value
                    upper = record.compressive_perpendiculer_avg + record.compressive_perpendiculer_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.compressive_perpendiculer_avg_conformity = 'pass'
                        break
                    else:
                        record.compressive_perpendiculer_avg_conformity = 'fail'

    compressive_perpendiculer_avg_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_compressive_perpendiculer_avg_nabl", store=True)

    @api.depends('compressive_perpendiculer_avg','eln_ref')
    def _compute_compressive_perpendiculer_avg_nabl(self):
        
        for record in self:
            record.compressive_perpendiculer_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5478ttr5-41c5-4cb5-843a-e09590c7c5789hh')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5478ttr5-41c5-4cb5-843a-e09590c7c5789hh')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.compressive_perpendiculer_avg - record.compressive_perpendiculer_avg*mu_value
            upper = record.compressive_perpendiculer_avg + record.compressive_perpendiculer_avg*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.compressive_perpendiculer_avg_nabl = 'pass'
                break
            else:
                record.compressive_perpendiculer_avg_nabl = 'fail'




    compressive_parallel_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_compressive_parallel_avg_conformity", store=True)

    @api.depends('compressive_parallel_avg','eln_ref','grade')
    def _compute_compressive_parallel_avg_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.compressive_parallel_avg_conformity = 'na'
                continue
            record.compressive_parallel_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4f05fc75-0c6b-4f83-8380-621838762fb3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4f05fc75-0c6b-4f83-8380-621838762fb3')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.compressive_parallel_avg - record.compressive_parallel_avg*mu_value
                    upper = record.compressive_parallel_avg + record.compressive_parallel_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.compressive_parallel_avg_conformity = 'pass'
                        break
                    else:
                        record.compressive_parallel_avg_conformity = 'fail'

    compressive_parallel_avg_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_compressive_parallel_avg_nabl", store=True)

    @api.depends('compressive_parallel_avg','eln_ref')
    def _compute_compressive_parallel_avg_nabl(self):
        
        for record in self:
            record.compressive_parallel_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4f05fc75-0c6b-4f83-8380-621838762fb3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4f05fc75-0c6b-4f83-8380-621838762fb3')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.compressive_parallel_avg - record.compressive_parallel_avg*mu_value
            upper = record.compressive_parallel_avg + record.compressive_parallel_avg*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.compressive_parallel_avg_nabl = 'pass'
                break
            else:
                record.compressive_parallel_avg_nabl = 'fail'


    # Compressive Strength in Satuarted Condition
    compressive_wet_name = fields.Char("Name",default=" Compressive Strength in Satuarted Condition")
    compressive_wet_visible = fields.Boolean(" Compressive Strength in Satuarted Condition Visible",compute="_compute_visible")

    compressive_wet_ids = fields.One2many("mechanical.compressive.wet.line", "parent_id", string="Test Readings")

    
    @api.onchange('compressive_wet_ids')
    def _onchange_limits_lines(self):
        if len(self.compressive_wet_ids) > 5:
            raise ValidationError("You cannot add more than 5 Test Reading lines.")

    wet_factor_a = fields.Float(string="Constant Factor A",  digits=(12, 4))
    wet_factor_b = fields.Float(string="Constant Factor B",  digits=(12, 4))

    compressive_perpendiculer_wet_avg = fields.Float(
        string="Average Compressive Strength Perpendicular Wet (N/mm²)",
        compute="_compute_average_strengths_wet",
        store=True,
        digits=(12, 2)
    )

    compressive_parallel_wet_avg = fields.Float(
        string="Average Compressive Strength Parallel Wet (N/mm²)",
        compute="_compute_average_strengths_wet",
        store=True,
        digits=(12, 2)
    )

    @api.depends('compressive_wet_ids.compressive_perpendiculer1', 'compressive_wet_ids.compressive_parallel1')
    def _compute_average_strengths_wet(self):
        for record in self:
            perpend_vals = record.compressive_wet_ids.mapped('compressive_perpendiculer1')
            parallel_vals = record.compressive_wet_ids.mapped('compressive_parallel1')

            record.compressive_perpendiculer_wet_avg = (
                sum(perpend_vals) / len(perpend_vals)
                if perpend_vals else 0.0
            )
            record.compressive_parallel_wet_avg = (
                sum(parallel_vals) / len(parallel_vals)
                if parallel_vals else 0.0
            )

    compressive_perpendiculer_wet_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_compressive_perpendiculer_wet_avg_conformity", store=True)

    @api.depends('compressive_perpendiculer_wet_avg','eln_ref','grade')
    def _compute_compressive_perpendiculer_wet_avg_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.compressive_perpendiculer_wet_avg_conformity = 'na'
                continue
            record.compressive_perpendiculer_wet_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','547896rg-41c5-4cb5-843a-e09590c7c57878tt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','547896rg-41c5-4cb5-843a-e09590c7c57878tt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.compressive_perpendiculer_wet_avg - record.compressive_perpendiculer_wet_avg*mu_value
                    upper = record.compressive_perpendiculer_wet_avg + record.compressive_perpendiculer_wet_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.compressive_perpendiculer_wet_avg_conformity = 'pass'
                        break
                    else:
                        record.compressive_perpendiculer_wet_avg_conformity = 'fail'

    compressive_perpendiculer_wet_avg_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_compressive_perpendiculer_wet_avg_nabl", store=True)

    @api.depends('compressive_perpendiculer_wet_avg','eln_ref')
    def _compute_compressive_perpendiculer_wet_avg_nabl(self):
        
        for record in self:
            record.compressive_perpendiculer_wet_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','547896rg-41c5-4cb5-843a-e09590c7c57878tt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','547896rg-41c5-4cb5-843a-e09590c7c57878tt')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.compressive_perpendiculer_wet_avg - record.compressive_perpendiculer_wet_avg*mu_value
            upper = record.compressive_perpendiculer_wet_avg + record.compressive_perpendiculer_wet_avg*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.compressive_perpendiculer_wet_avg_nabl = 'pass'
                break
            else:
                record.compressive_perpendiculer_wet_avg_nabl = 'fail'


    compressive_parallel_wet_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_compressive_parallel_wet_avg_conformity", store=True)

    @api.depends('compressive_parallel_wet_avg','eln_ref','grade')
    def _compute_compressive_parallel_wet_avg_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.compressive_parallel_wet_avg_conformity = 'na'
                continue
            record.compressive_parallel_wet_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','592c1732-40d8-41da-8d57-002c86390370')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','592c1732-40d8-41da-8d57-002c86390370')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.compressive_parallel_wet_avg - record.compressive_parallel_wet_avg*mu_value
                    upper = record.compressive_parallel_wet_avg + record.compressive_parallel_wet_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.compressive_parallel_wet_avg_conformity = 'pass'
                        break
                    else:
                        record.compressive_parallel_wet_avg_conformity = 'fail'

    compressive_parallel_wet_avg_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_compressive_parallel_wet_avg_nabl", store=True)

    @api.depends('compressive_parallel_wet_avg','eln_ref')
    def _compute_compressive_parallel_wet_avg_nabl(self):
        
        for record in self:
            record.compressive_parallel_wet_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','592c1732-40d8-41da-8d57-002c86390370')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','592c1732-40d8-41da-8d57-002c86390370')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.compressive_parallel_wet_avg - record.compressive_parallel_wet_avg*mu_value
            upper = record.compressive_parallel_wet_avg + record.compressive_parallel_wet_avg*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.compressive_parallel_wet_avg_nabl = 'pass'
                break
            else:
                record.compressive_parallel_wet_avg_nabl = 'fail'





                
    # Water Absorption

    water_absorption_name = fields.Char("Name",default="Water Absorption")
    water_absorption_visible = fields.Boolean("Water Absorption",compute="_compute_visible")

    # SAMPLE 1
    sample1_oven_weight = fields.Float(
        string="Oven Dried Weight",
        digits=(12, 4)
    )

    sample1_saturated_weight = fields.Float(
        string="Saturated Surface Dry Weight",
        digits=(12, 4)
    )

    sample1_water_absorption = fields.Float(
        string="Water Absorption (%)",
        digits=(12, 2),
        compute="_compute_water_absorption",
        store=True
    )

    # SAMPLE 2
    sample2_oven_weight = fields.Float(
        string="Oven Dried Weight",
        digits=(12, 4)
    )

    sample2_saturated_weight = fields.Float(
        string="Saturated Surface Dry Weight",
        digits=(12, 4)
    )

    sample2_water_absorption = fields.Float(
        string="Water Absorption (%)",
        digits=(12, 2),
        compute="_compute_water_absorption",
        store=True
    )

   
    # SAMPLE 3
    sample3_oven_weight = fields.Float(
        string="Oven Dried Weight",
        digits=(12, 4)
    )

    sample3_saturated_weight = fields.Float(
        string="Saturated Surface Dry Weight",
        digits=(12, 4)
    )

    sample3_water_absorption = fields.Float(
        string="Water Absorption (%)",
        digits=(12, 2),
        compute="_compute_water_absorption",
        store=True
    )

   
    # AVERAGE
    avg_water_absorption = fields.Float(
        string="Average Water Absorption (%)",
        digits=(12, 2),
        compute="_compute_avg_water_absorption",
        store=True
    )

    
    # WATER ABSORPTION 
    @api.depends(
        'sample1_oven_weight',
        'sample1_saturated_weight',
        'sample2_oven_weight',
        'sample2_saturated_weight',
        'sample3_oven_weight',
        'sample3_saturated_weight'
    )
    def _compute_water_absorption(self):

        def calculate_absorption(oven, saturated):
            if oven > 0:
                result = ((saturated - oven) / oven) * 100

                return float(
                    Decimal(str(result)).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_UP
                    )
                )
            return 0.0

        for rec in self:

            rec.sample1_water_absorption = calculate_absorption(
                rec.sample1_oven_weight or 0.0,
                rec.sample1_saturated_weight or 0.0
            )

            rec.sample2_water_absorption = calculate_absorption(
                rec.sample2_oven_weight or 0.0,
                rec.sample2_saturated_weight or 0.0
            )

            rec.sample3_water_absorption = calculate_absorption(
                rec.sample3_oven_weight or 0.0,
                rec.sample3_saturated_weight or 0.0
            )

    
    # AVERAGE COMPUTE
    @api.depends(
        'sample1_water_absorption',
        'sample2_water_absorption',
        'sample3_water_absorption'
    )
    def _compute_avg_water_absorption(self):

        for rec in self:

            avg = (
                (rec.sample1_water_absorption or 0.0) +
                (rec.sample2_water_absorption or 0.0) +
                (rec.sample3_water_absorption or 0.0)
            ) / 3

            rec.avg_water_absorption = float(
                Decimal(str(avg)).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_UP
                )
            )

    avg_water_absorption_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_water_absorption_conformity", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_water_absorption_conformity = 'na'
                continue
            record.avg_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57r7896rg-41c5-4cb5-843a-e09590c74578trew8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57r7896rg-41c5-4cb5-843a-e09590c74578trew8')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_water_absorption - record.avg_water_absorption*mu_value
                    upper = record.avg_water_absorption + record.avg_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_water_absorption_conformity = 'pass'
                        break
                    else:
                        record.avg_water_absorption_conformity = 'fail'

    avg_water_absorption_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_water_absorption_nabl", store=True)

    @api.depends('avg_water_absorption','eln_ref')
    def _compute_avg_water_absorption_nabl(self):
        
        for record in self:
            record.avg_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57r7896rg-41c5-4cb5-843a-e09590c74578trew8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57r7896rg-41c5-4cb5-843a-e09590c74578trew8')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_water_absorption - record.avg_water_absorption*mu_value
            upper = record.avg_water_absorption + record.avg_water_absorption*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_water_absorption_nabl = 'pass'
                break
            else:
                record.avg_water_absorption_nabl = 'fail'


    # Apparent Specific Gravity

    app_specific_name = fields.Char("Name",default="Apparent Specific Gravity")
    app_specific_visible = fields.Boolean("Apparent Specific Gravity",compute="_compute_visible")

    
    # SAMPLE 1
    sample1_dry_weight = fields.Float(string="Dry Weight")
    sample1_suspended_weight = fields.Float(string="Suspended Weight")
    sample11_saturated_weight = fields.Float(string="Saturated Weight")

    sample1_apparent_specific_gravity = fields.Float(
        string="Apparent Specific Gravity",
        compute="_compute_apparent_specific_gravity",
        store=True
    )

    # SAMPLE 2
    sample2_dry_weight = fields.Float(string="Dry Weight")
    sample2_suspended_weight = fields.Float(string="Suspended Weight")
    sample22_saturated_weight = fields.Float(string="Saturated Weight")

    sample2_apparent_specific_gravity = fields.Float(
        string="Apparent Specific Gravity",
        compute="_compute_apparent_specific_gravity",
        store=True
    )

    # SAMPLE 3
    sample3_dry_weight = fields.Float(string="Dry Weight")
    sample3_suspended_weight = fields.Float(string="Suspended Weight")
    sample33_saturated_weight = fields.Float(string="Saturated Weight")

    sample3_apparent_specific_gravity = fields.Float(
        string="Apparent Specific Gravity",
        compute="_compute_apparent_specific_gravity",
        store=True
    )

    # AVERAGE
    avg_apparent_specific_gravity = fields.Float(
        string="Average Apparent Specific Gravity",
        compute="_compute_avg_apparent_specific_gravity",
        store=True
    )

    # COMPUTE
    @api.depends(
        'sample1_dry_weight',
        'sample1_suspended_weight',
        'sample11_saturated_weight',

        'sample2_dry_weight',
        'sample2_suspended_weight',
        'sample22_saturated_weight',

        'sample3_dry_weight',
        'sample3_suspended_weight',
        'sample33_saturated_weight',
    )
    def _compute_apparent_specific_gravity(self):

        def calculate(dry, suspended, saturated):

            denominator = dry - (saturated - suspended)

            if denominator != 0:
                result = dry / denominator

                return float(
                    Decimal(str(result)).quantize(
                        Decimal("0.0001"),
                        rounding=ROUND_UP
                    )
                )

            return 0.0

        for rec in self:

            rec.sample1_apparent_specific_gravity = calculate(
                rec.sample1_dry_weight,
                rec.sample1_suspended_weight,
                rec.sample11_saturated_weight
            )

            rec.sample2_apparent_specific_gravity = calculate(
                rec.sample2_dry_weight,
                rec.sample2_suspended_weight,
                rec.sample22_saturated_weight
            )

            rec.sample3_apparent_specific_gravity = calculate(
                rec.sample3_dry_weight,
                rec.sample3_suspended_weight,
                rec.sample33_saturated_weight
            )

   
    # AVERAGE
    @api.depends(
        'sample1_apparent_specific_gravity',
        'sample2_apparent_specific_gravity',
        'sample3_apparent_specific_gravity'
    )
    def _compute_avg_apparent_specific_gravity(self):

        for rec in self:

            avg = (
                rec.sample1_apparent_specific_gravity +
                rec.sample2_apparent_specific_gravity +
                rec.sample3_apparent_specific_gravity
            ) / 3

            rec.avg_apparent_specific_gravity = float(
                Decimal(str(avg)).quantize(
                    Decimal("0.0001"),
                    rounding=ROUND_UP
                )
            )


    avg_apparent_specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_apparent_specific_gravity_conformity", store=True)

    @api.depends('avg_apparent_specific_gravity','eln_ref','grade')
    def _compute_avg_apparent_specific_gravity_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_apparent_specific_gravity_conformity = 'na'
                continue
            record.avg_apparent_specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57r7896rg-41c5-4cb5-843a-e09590c7789rte143q')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57r7896rg-41c5-4cb5-843a-e09590c7789rte143q')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_apparent_specific_gravity - record.avg_apparent_specific_gravity*mu_value
                    upper = record.avg_apparent_specific_gravity + record.avg_apparent_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_apparent_specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.avg_apparent_specific_gravity_conformity = 'fail'

    avg_apparent_specific_gravity_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_apparent_specific_gravity_nabl", store=True)

    @api.depends('avg_apparent_specific_gravity','eln_ref')
    def _compute_avg_apparent_specific_gravity_nabl(self):
        
        for record in self:
            record.avg_apparent_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57r7896rg-41c5-4cb5-843a-e09590c7789rte143q')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57r7896rg-41c5-4cb5-843a-e09590c7789rte143q')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_apparent_specific_gravity - record.avg_apparent_specific_gravity*mu_value
            upper = record.avg_apparent_specific_gravity + record.avg_apparent_specific_gravity*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_apparent_specific_gravity_nabl = 'pass'
                break
            else:
                record.avg_apparent_specific_gravity_nabl = 'fail'


    # True Specific Gravity

    true_specific_name = fields.Char("Name",default="True Specific Gravity")
    true_specific_visible = fields.Boolean("True Specific Gravity",compute="_compute_visible")

    # SAMPLE 1
    sample1_w1 = fields.Float(
        string="Empty Bottle Weight (W1)",
        digits=(12, 4)
    )

    sample1_w2 = fields.Float(
        string="Bottle + Powder Weight (W2)",
        digits=(12, 4)
    )

    sample1_w3 = fields.Float(
        string="Bottle + Powder + Water Weight (W3)",
        digits=(12, 4)
    )

    sample1_w4 = fields.Float(
        string="Bottle + Water Weight (W4)",
        digits=(12, 4)
    )

    sample1_true_specific_gravity = fields.Float(
        string="True Specific Gravity",
        digits=(12, 4),
        compute="_compute_true_specific_gravity",
        store=True
    )

  
    # SAMPLE 2
    sample2_w1 = fields.Float(
        string="Empty Bottle Weight (W1)",
        digits=(12, 4)
    )

    sample2_w2 = fields.Float(
        string="Bottle + Powder Weight (W2)",
        digits=(12, 4)
    )

    sample2_w3 = fields.Float(
        string="Bottle + Powder + Water Weight (W3)",
        digits=(12, 4)
    )

    sample2_w4 = fields.Float(
        string="Bottle + Water Weight (W4)",
        digits=(12, 4)
    )

    sample2_true_specific_gravity = fields.Float(
        string="True Specific Gravity",
        digits=(12, 4),
        compute="_compute_true_specific_gravity",
        store=True
    )

    # SAMPLE 3
    sample3_w1 = fields.Float(
        string="Empty Bottle Weight (W1)",
        digits=(12, 4)
    )

    sample3_w2 = fields.Float(
        string="Bottle + Powder Weight (W2)",
        digits=(12, 4)
    )

    sample3_w3 = fields.Float(
        string="Bottle + Powder + Water Weight (W3)",
        digits=(12, 4)
    )

    sample3_w4 = fields.Float(
        string="Bottle + Water Weight (W4)",
        digits=(12, 4)
    )

    sample3_true_specific_gravity = fields.Float(
        string="True Specific Gravity",
        digits=(12, 4),
        compute="_compute_true_specific_gravity",
        store=True
    )

    # AVERAGE
    avg_true_specific_gravity = fields.Float(
        string="Average True Specific Gravity",
        digits=(12, 4),
        compute="_compute_avg_true_specific_gravity",
        store=True
    )

    # COMPUTE TRUE SPECIFIC GRAVITY
    @api.depends(
        'sample1_w1', 'sample1_w2', 'sample1_w3', 'sample1_w4',
        'sample2_w1', 'sample2_w2', 'sample2_w3', 'sample2_w4',
        'sample3_w1', 'sample3_w2', 'sample3_w3', 'sample3_w4'
    )
    def _compute_true_specific_gravity(self):

        def calculate(w1, w2, w3, w4):

            denominator = ((w4 - w1) - (w3 - w2))

            if denominator != 0:

                result = (w2 - w1) / denominator

                return float(
                    Decimal(str(result)).quantize(
                        Decimal("0.000001"),
                        rounding=ROUND_UP
                    )
                )

            return 0.0

        for rec in self:

            # SAMPLE 1
            rec.sample1_true_specific_gravity = calculate(
                rec.sample1_w1,
                rec.sample1_w2,
                rec.sample1_w3,
                rec.sample1_w4
            )

            # SAMPLE 2
            rec.sample2_true_specific_gravity = calculate(
                rec.sample2_w1,
                rec.sample2_w2,
                rec.sample2_w3,
                rec.sample2_w4
            )

            # SAMPLE 3
            rec.sample3_true_specific_gravity = calculate(
                rec.sample3_w1,
                rec.sample3_w2,
                rec.sample3_w3,
                rec.sample3_w4
            )

    # COMPUTE AVERAGE
    @api.depends(
        'sample1_true_specific_gravity',
        'sample2_true_specific_gravity',
        'sample3_true_specific_gravity'
    )
    def _compute_avg_true_specific_gravity(self):

        for rec in self:

            avg = (
                (rec.sample1_true_specific_gravity or 0.0) +
                (rec.sample2_true_specific_gravity or 0.0) +
                (rec.sample3_true_specific_gravity or 0.0)
            ) / 3

            rec.avg_true_specific_gravity = float(
                Decimal(str(avg)).quantize(
                    Decimal("0.000001"),
                    rounding=ROUND_UP
                )
            )


    avg_true_specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_true_specific_gravity_conformity", store=True)

    @api.depends('avg_true_specific_gravity','eln_ref','grade')
    def _compute_avg_true_specific_gravity_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_true_specific_gravity_conformity = 'na'
                continue
            record.avg_true_specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57r7896rg-41c5-4cb5-843a-e09590c77832547ewrv')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57r7896rg-41c5-4cb5-843a-e09590c77832547ewrv')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_true_specific_gravity - record.avg_true_specific_gravity*mu_value
                    upper = record.avg_true_specific_gravity + record.avg_true_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_true_specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.avg_true_specific_gravity_conformity = 'fail'

    avg_true_specific_gravity_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_true_specific_gravity_nabl", store=True)

    @api.depends('avg_true_specific_gravity','eln_ref')
    def _compute_avg_true_specific_gravity_nabl(self):
        
        for record in self:
            record.avg_true_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57r7896rg-41c5-4cb5-843a-e09590c77832547ewrv')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','57r7896rg-41c5-4cb5-843a-e09590c77832547ewrv')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_true_specific_gravity - record.avg_true_specific_gravity*mu_value
            upper = record.avg_true_specific_gravity + record.avg_true_specific_gravity*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_true_specific_gravity_nabl = 'pass'
                break
            else:
                record.avg_true_specific_gravity_nabl = 'fail'


                





 ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.compressive_dry_visible = False
            record.compressive_wet_visible = False
            record.water_absorption_visible = False
            record.app_specific_visible = False
            record.true_specific_visible = False

            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                if sample.internal_id == "5478ttr5-41c5-4cb5-843a-e09590c7c5789hh":
                    record.compressive_dry_visible = True

                if sample.internal_id == "547896rg-41c5-4cb5-843a-e09590c7c57878tt":
                    record.compressive_wet_visible = True

                if sample.internal_id == "57r7896rg-41c5-4cb5-843a-e09590c74578trew8":
                    record.water_absorption_visible = True

                if sample.internal_id == "57r7896rg-41c5-4cb5-843a-e09590c7789rte143q":
                    record.app_specific_visible = True

                if sample.internal_id == "57r7896rg-41c5-4cb5-843a-e09590c77832547ewrv":
                    record.true_specific_visible = True







    def open_eln_page(self):
    # import wdb; wdb.set_trace()
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        if current_user.has_group('lerm_civil.lerm_discipline_group'):
            technician_results = self.eln_ref.parameters_result
        else:
            technician_results = self.eln_ref.parameters_result.filtered(
                lambda r: r.technician == current_user
            )

        for result in technician_results:
            
            # Compressive dry - Perpendicular
            if result.parameter.internal_id == '5478ttr5-41c5-4cb5-843a-e09590c7c5789hh':
                result.result_char = round(self.compressive_perpendiculer_avg,2)
                result.calculated = True
                if self.compressive_perpendiculer_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Compressive dry - Parallel
            if result.parameter.internal_id == '4f05fc75-0c6b-4f83-8380-621838762fb3':
                result.result_char = round(self.compressive_parallel_avg,2)
                result.calculated = True
                if self.compressive_parallel_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Compressive wet - Perpendicular
            if result.parameter.internal_id == '547896rg-41c5-4cb5-843a-e09590c7c57878tt':
                result.result_char = round(self.compressive_perpendiculer_wet_avg,2)
                result.calculated = True
                if self.compressive_perpendiculer_wet_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Compressive wet - Parallel
            if result.parameter.internal_id == '592c1732-40d8-41da-8d57-002c86390370':
                result.result_char = round(self.compressive_parallel_wet_avg,2)
                result.calculated = True
                if self.compressive_parallel_wet_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
                

            # Water Absorption
            if result.parameter.internal_id == '57r7896rg-41c5-4cb5-843a-e09590c74578trew8':
                result.result_char = round(self.avg_water_absorption,2)
                result.calculated = True
                if self.avg_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Apparent Specific Gravity
            if result.parameter.internal_id == '57r7896rg-41c5-4cb5-843a-e09590c7789rte143q':
                result.result_char = round(self.avg_apparent_specific_gravity,2)
                result.calculated = True
                if self.avg_apparent_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # True Specific Gravity
            if result.parameter.internal_id == '57r7896rg-41c5-4cb5-843a-e09590c77832547ewrv':
                result.result_char = round(self.avg_true_specific_gravity,2)
                result.calculated = True
                if self.avg_true_specific_gravity_nabl == 'pass':
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
        record = super(Stones, self).create(vals)
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
        record = self.env['mechanical.stones'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id






class CompressiveDryLine(models.Model):
    _name = "mechanical.compressive.dry.line"
    parent_id = fields.Many2one('mechanical.stones',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    # sr_no = fields.Integer(string="Test", readonly=True, copy=False, default=1)
    blue_input = fields.Boolean(default=True,invisible=True)
    date = fields.Date(string="Date")
    room_temp = fields.Float(string="Room temperature (deg)", digits=(12,2))
    relative_humidity = fields.Float(string="Relative Humidity (%) ", digits=(12,2))
    functional_check = fields.Char(string="Functional Checks ")
    stone_type = fields.Char(string="Type of stone) ")
    shape_stone = fields.Char(string="Shape of test piece (Cube/Cylinder) ")
    height_shape = fields.Float(string="Height of sample(H), mm ", digits=(12,2))
    width_stone = fields.Float(string="Width/Diameter of sample(D), mm ", digits=(12,2))
    test_conditin = fields.Char(string="Test condition (Dry/Saturated) ",default="Dry")
    load_perpendiculer = fields.Float(string="Load Perpendicular to plane of Anisotropy KN", digits=(12,2))
    load_parallel = fields.Float(string="Load Parallel to plane of Anisotropy KN ", digits=(12,2))
    load_perpendiculer_n = fields.Float(string="Load  Perpendicular to plane of Anisotropy N ", digits=(12,2),compute="_compute_loads_in_newton",store=True)
    load_parallel_n = fields.Float(string="Load  Parallel to plane of Anisotropy N ", digits=(12,2),compute="_compute_loads_in_newton",store=True)
    duration_test = fields.Float(string="Duration of test (sec) ", digits=(12,2))
    appearance_stone = fields.Float(string="Appearance/any unusual features at failure ", digits=(12,2))
    hd_stone = fields.Float(string="H/d ", digits=(12,2),compute="_compute_stone_values",store=True)
    area_stone = fields.Float(string="Area of sample (mm2) ", digits=(12,2),compute="_compute_stone_values",store=True)
    compressive_perpendiculer = fields.Float(string="Compressive Strength Perpendicular to plane of Anisotropy (N/mm2)  ", digits=(12,2), compute="_compute_compressive_strength",store=True)
    compressive_parallel = fields.Float(string="Compressive Parallel to plane of Anisotropy (N/mm2)  ", digits=(12,2),compute="_compute_compressive_strength",store=True)
    stress_perpendiculer = fields.Float(string="Stress rate Perpendicular to plane of Anisotropy(MPa/s)  ",digits=(12,2),compute="_compute_stress_rate",store=True)
    stress_parallel = fields.Float(string="Stress rate Parallel to plane of Anisotropy(MPa/s)   ", digits=(12,2),compute="_compute_stress_rate",store=True)

    compressive_perpendiculer1 = fields.Float(string="Compressive Strength Perpendicular to plane of Anisotropy (N/mm2)  ",compute="_compute_corrected_strength", digits=(12,4),store=True)
    compressive_parallel1 = fields.Float(string="Compressive Parallel to plane of Anisotropy (N/mm2)  ",compute="_compute_corrected_strength", digits=(12,4),store=True)

   


    @api.depends('load_perpendiculer', 'load_parallel')
    def _compute_loads_in_newton(self):
        for record in self:
            record.load_perpendiculer_n = (record.load_perpendiculer or 0.0) * 1000
            record.load_parallel_n = (record.load_parallel or 0.0) * 1000

    @api.depends('height_shape', 'width_stone')
    def _compute_stone_values(self):
        for record in self:
            if record.width_stone:
                record.hd_stone = record.height_shape / record.width_stone
            else:
                record.hd_stone = 0.0

            record.area_stone = (record.height_shape or 0.0) * (record.width_stone or 0.0)


    @api.depends('load_perpendiculer_n', 'load_parallel_n', 'area_stone')
    def _compute_compressive_strength(self):
        for record in self:
            if record.area_stone:
                record.compressive_perpendiculer = record.load_perpendiculer_n / record.area_stone
                record.compressive_parallel = record.load_parallel_n / record.area_stone
            else:
                record.compressive_perpendiculer = 0.0
                record.compressive_parallel = 0.0

    @api.depends('compressive_perpendiculer', 'compressive_parallel', 'duration_test')
    def _compute_stress_rate(self):
        for record in self:
            if record.duration_test:
                record.stress_perpendiculer = record.compressive_perpendiculer / record.duration_test
                record.stress_parallel = record.compressive_parallel / record.duration_test
            else:
                record.stress_perpendiculer = 0.0
                record.stress_parallel = 0.0


    @api.depends(
        'compressive_perpendiculer',
        'compressive_parallel',
        'hd_stone',
        'width_stone',
        'height_shape',
        'parent_id.factor_a',
        'parent_id.factor_b'
    )
    def _compute_corrected_strength(self):
        for rec in self:
            # सुरक्षितपणे parent factors घ्या
            a = rec.parent_id.factor_a
            b = rec.parent_id.factor_b

            ratio = (a + b * (rec.width_stone / rec.height_shape)) if rec.height_shape else 1

            if rec.hd_stone == 1:
                rec.compressive_perpendiculer1 = rec.compressive_perpendiculer
                rec.compressive_parallel1 = rec.compressive_parallel
            else:
                rec.compressive_perpendiculer1 = rec.compressive_perpendiculer / ratio if ratio else 0.0
                rec.compressive_parallel1 = rec.compressive_parallel / ratio if ratio else 0.0


    
    
    


   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CompressiveDryLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class CompressiveWetLine(models.Model):
    _name = "mechanical.compressive.wet.line"
    parent_id = fields.Many2one('mechanical.stones',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)
    blue_input = fields.Boolean(default=True,invisible=True)

    # sr_no = fields.Integer(string="Test", readonly=True, copy=False, default=1)
    date = fields.Date(string="Date")
    room_temp = fields.Float(string="Room temperature (deg)", digits=(12,2))
    relative_humidity = fields.Float(string="Relative Humidity (%) ", digits=(12,2))
    functional_check = fields.Char(string="Functional Checks ")
    stone_type = fields.Char(string="Type of stone) ")
    shape_stone = fields.Char(string="Shape of test piece (Cube/Cylinder) ")
    height_shape = fields.Float(string="Height of sample(H), mm ", digits=(12,2))
    width_stone = fields.Float(string="Width/Diameter of sample(D), mm ", digits=(12,2))
    test_conditin = fields.Char(string="Test condition (Dry/Saturated) ",default="Saturated")
    load_perpendiculer = fields.Float(string="Load Perpendicular to plane of Anisotropy KN", digits=(12,2))
    load_parallel = fields.Float(string="Load Parallel to plane of Anisotropy KN ", digits=(12,2))
    load_perpendiculer_n = fields.Float(string="Load  Perpendicular to plane of Anisotropy N ", digits=(12,2),compute="_compute_loads_in_newton",store=True)
    load_parallel_n = fields.Float(string="Load  Parallel to plane of Anisotropy N ", digits=(12,2),compute="_compute_loads_in_newton",store=True)
    duration_test = fields.Float(string="Duration of test (sec) ", digits=(12,2))
    appearance_stone = fields.Float(string="Appearance/any unusual features at failure ", digits=(12,2))
    hd_stone = fields.Float(string="H/d ", digits=(12,2),compute="_compute_stone_values",store=True)
    area_stone = fields.Float(string="Area of sample (mm2) ", digits=(12,2),compute="_compute_stone_values",store=True)
    compressive_perpendiculer = fields.Float(string="Compressive Strength Perpendicular to plane of Anisotropy (N/mm2)  ", digits=(12,2), compute="_compute_compressive_strength",store=True)
    compressive_parallel = fields.Float(string="Compressive Parallel to plane of Anisotropy (N/mm2)  ", digits=(12,2),compute="_compute_compressive_strength",store=True)
    stress_perpendiculer = fields.Float(string="Stress rate Perpendicular to plane of Anisotropy(MPa/s)  ",digits=(12,2),compute="_compute_stress_rate",store=True)
    stress_parallel = fields.Float(string="Stress rate Parallel to plane of Anisotropy(MPa/s)   ", digits=(12,2),compute="_compute_stress_rate",store=True)

    compressive_perpendiculer1 = fields.Float(string="Compressive Strength Perpendicular to plane of Anisotropy (N/mm2)  ",compute="_compute_corrected_strength", digits=(12,4),store=True)
    compressive_parallel1 = fields.Float(string="Compressive Parallel to plane of Anisotropy (N/mm2)  ",compute="_compute_corrected_strength", digits=(12,4),store=True)



    @api.depends('load_perpendiculer', 'load_parallel')
    def _compute_loads_in_newton(self):
        for record in self:
            record.load_perpendiculer_n = (record.load_perpendiculer or 0.0) * 1000
            record.load_parallel_n = (record.load_parallel or 0.0) * 1000

    @api.depends('height_shape', 'width_stone')
    def _compute_stone_values(self):
        for record in self:
            if record.width_stone:
                record.hd_stone = record.height_shape / record.width_stone
            else:
                record.hd_stone = 0.0

            record.area_stone = (record.height_shape or 0.0) * (record.width_stone or 0.0)


    @api.depends('load_perpendiculer_n', 'load_parallel_n', 'area_stone')
    def _compute_compressive_strength(self):
        for record in self:
            if record.area_stone:
                record.compressive_perpendiculer = record.load_perpendiculer_n / record.area_stone
                record.compressive_parallel = record.load_parallel_n / record.area_stone
            else:
                record.compressive_perpendiculer = 0.0
                record.compressive_parallel = 0.0

    @api.depends('compressive_perpendiculer', 'compressive_parallel', 'duration_test')
    def _compute_stress_rate(self):
        for record in self:
            if record.duration_test:
                record.stress_perpendiculer = record.compressive_perpendiculer / record.duration_test
                record.stress_parallel = record.compressive_parallel / record.duration_test
            else:
                record.stress_perpendiculer = 0.0
                record.stress_parallel = 0.0

    @api.depends(
        'compressive_perpendiculer',
        'compressive_parallel',
        'hd_stone',
        'width_stone',
        'height_shape',
        'parent_id.wet_factor_a',
        'parent_id.wet_factor_b'
    )
    def _compute_corrected_strength(self):
        for rec in self:
            # सुरक्षितपणे parent factors घ्या
            a = rec.parent_id.wet_factor_a
            b = rec.parent_id.wet_factor_b

            ratio = (a + b * (rec.width_stone / rec.height_shape)) if rec.height_shape else 1

            if rec.hd_stone == 1:
                rec.compressive_perpendiculer1 = rec.compressive_perpendiculer
                rec.compressive_parallel1 = rec.compressive_parallel
            else:
                rec.compressive_perpendiculer1 = rec.compressive_perpendiculer / ratio if ratio else 0.0
                rec.compressive_parallel1 = rec.compressive_parallel / ratio if ratio else 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CompressiveWetLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class StoneNotes(models.Model):
    _name = "stone.notes"

    parent_id = fields.Many2one('mechanical.stones',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
















   

   

  



    


   



   
   

   
