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

    temp = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)


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


     
    

     # Compressive Strength 

    compressive_name = fields.Char("Name",default="Compressive Strength   ")
    compressive_visible = fields.Boolean("Compressive Strength Visible",compute="_compute_visible")

    compressive_ids = fields.One2many("mechanical.compressive.dry.line", "parent_id", string="Test Readings")


    average_ucs = fields.Float(
        string="Average UCS (MPa)",
        compute="_compute_average_ucs",
        store=True,
    )

    @api.depends("compressive_ids.ucs")
    def _compute_average_ucs(self):
        for rec in self:
            ucs_values = rec.compressive_ids.mapped("ucs")
            rec.average_ucs = sum(ucs_values) / len(ucs_values) if ucs_values else 0.0


    average_ucs_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_average_ucs_conformity", store=True)

    @api.depends('average_ucs','eln_ref','grade')
    def _compute_average_ucs_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_ucs_conformity = 'na'
                continue
            record.average_ucs_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5478ttr5-41c5-4cb5-843a-e09590c7c5789hh')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5478ttr5-41c5-4cb5-843a-e09590c7c5789hh')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_ucs - record.average_ucs*mu_value
                    upper = record.average_ucs + record.average_ucs*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_ucs_conformity = 'pass'
                        break
                    else:
                        record.average_ucs_conformity = 'fail'

    average_ucs_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_average_ucs_nabl", store=True)

    @api.depends('average_ucs','eln_ref','grade')
    def _compute_average_ucs_nabl(self):
        
        for record in self:
            record.average_ucs_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5478ttr5-41c5-4cb5-843a-e09590c7c5789hh')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5478ttr5-41c5-4cb5-843a-e09590c7c5789hh')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_ucs - record.average_ucs*mu_value
            upper = record.average_ucs + record.average_ucs*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_ucs_nabl = 'pass'
                break
            else:
                record.average_ucs_nabl = 'fail'


    compressive_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    compressive_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_compressive_final_report", store=True)
        
    @api.depends('average_ucs_nabl', 'compressive_report_type')
    def _compute_compressive_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.compressive_report_type == 'nabl':
                    rec.compressive_final_report = 'nabl'
        
                elif rec.compressive_report_type == 'non_nabl':
                    rec.compressive_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.average_ucs_nabl == 'pass':
                        rec.compressive_final_report = 'nabl'
                    else:
                        rec.compressive_final_report = 'non_nabl'

    
    
    

    

                
    # Water Absorption

    water_absorption_name = fields.Char("Name",default="Water Absorption")
    water_absorption_visible = fields.Boolean("Water Absorption",compute="_compute_visible")

    water_absorption_ids = fields.One2many("stone.water.absorption.line", "parent_id", string="Test Readings")


    avg_water_absorption = fields.Float(
        string="Average Water Absorption (%)",
        compute="_compute_avg_water_absorption",
        store=True,
    )

    @api.depends("water_absorption_ids.water_absorption")
    def _compute_avg_water_absorption(self):
        for rec in self:
            values = rec.water_absorption_ids.mapped("water_absorption")
            rec.avg_water_absorption = sum(values) / len(values) if values else 0.0

    
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


    water_absorption_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    water_absorption_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_water_absorption_final_report", store=True)
        
    @api.depends('avg_water_absorption_nabl', 'water_absorption_report_type')
    def _compute_water_absorption_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.water_absorption_report_type == 'nabl':
                    rec.water_absorption_final_report = 'nabl'
        
                elif rec.water_absorption_report_type == 'non_nabl':
                    rec.water_absorption_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.avg_water_absorption_nabl == 'pass':
                        rec.water_absorption_final_report = 'nabl'
                    else:
                        rec.water_absorption_final_report = 'non_nabl'


    # True Specific Gravity

    true_specific_name = fields.Char("Name",default="True Specific Gravity")
    true_specific_visible = fields.Boolean("True Specific Gravity",compute="_compute_visible")

    true_specific_ids = fields.One2many("stone.true.specific.gravity.line", "parent_id", string="Test Readings")



    avg_true_specific_gravity = fields.Float(
        string="Average True Specific Gravity",
        compute="_compute_average",
        store=True,
    )

    @api.depends("true_specific_ids.true_specific_gravity")
    def _compute_average(self):
        for rec in self:
            values = rec.true_specific_ids.mapped("true_specific_gravity")
            values = [v for v in values if v]
            rec.avg_true_specific_gravity = (
                sum(values) / len(values)
                if values else 0.0
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


    true_specific_gravity_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    true_specific_gravity_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_true_specific_gravity_final_report", store=True)
        
    @api.depends('avg_true_specific_gravity_nabl', 'true_specific_gravity_report_type')
    def _compute_true_specific_gravity_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.true_specific_gravity_report_type == 'nabl':
                    rec.true_specific_gravity_final_report = 'nabl'
        
                elif rec.true_specific_gravity_report_type == 'non_nabl':
                    rec.true_specific_gravity_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.avg_true_specific_gravity_nabl == 'pass':
                        rec.true_specific_gravity_final_report = 'nabl'
                    else:
                        rec.true_specific_gravity_final_report = 'non_nabl'


                



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


    




 ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.compressive_visible = False
            record.water_absorption_visible = False
            record.true_specific_visible = False

            record.app_specific_visible = False

            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                if sample.internal_id == "5478ttr5-41c5-4cb5-843a-e09590c7c5789hh":
                    record.compressive_visible = True

               

                if sample.internal_id == "57r7896rg-41c5-4cb5-843a-e09590c74578trew8":
                    record.water_absorption_visible = True

                if sample.internal_id == "57r7896rg-41c5-4cb5-843a-e09590c77832547ewrv":
                    record.true_specific_visible = True



                if sample.internal_id == "57r7896rg-41c5-4cb5-843a-e09590c7789rte143q":
                    record.app_specific_visible = True

                







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
                result.result_char = round(self.average_ucs,2)
                result.calculated = True
                if self.average_ucs_nabl == 'pass':
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

    sr_no = fields.Integer(string="Sr.No")

    specimen_id = fields.Char(string="Specimen ID")

    diameter = fields.Float(string="Diameter (mm)")

    width = fields.Float(string="Width (mm)")

    thickness = fields.Float(string="Thickness/Height (mm)")

    cross_section_area = fields.Float(
        string="Cross-sectional Area  (mm²)",
        compute="_compute_area",
        store=True,
    )

    max_load = fields.Float(string="Maximum Load at Failure (kN)")

    ucs = fields.Float(
        string="UCS (MPa = Load × 1000 / Area)",
        compute="_compute_ucs",
        store=True,
    )

    failure_description = fields.Char(string="Failure Description")

    @api.depends("diameter")
    def _compute_area(self):
        for rec in self:
            if rec.diameter:
                rec.cross_section_area = (
                    3.1416 * rec.diameter * rec.diameter / 4
                )
            else:
                rec.cross_section_area = 0.0

    @api.depends("max_load", "cross_section_area")
    def _compute_ucs(self):
        for rec in self:
            if rec.cross_section_area:
                rec.ucs = (
                    rec.max_load * 1000
                ) / rec.cross_section_area
            else:
                rec.ucs = 0.0

   

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


class StonesWaterAbsorptionLine(models.Model):
    _name = "stone.water.absorption.line"
    parent_id = fields.Many2one('mechanical.stones',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    description = fields.Char("Description of Stone")

    oven_dry_weight = fields.Float(
        string="Oven Dry Weight, Wd (g)"
    )

    saturated_weight = fields.Float(
        string="Saturated Weight, Ws (g)"
    )

    water_absorption = fields.Float(
        string="Water Absorption (%)",
        compute="_compute_water_absorption",
        store=True,
    )

    remarks = fields.Char(string="Remarks")

    @api.depends("oven_dry_weight", "saturated_weight")
    def _compute_water_absorption(self):
        for rec in self:
            if rec.oven_dry_weight:
                rec.water_absorption = (
                    (rec.saturated_weight - rec.oven_dry_weight)
                    / rec.oven_dry_weight
                ) * 100
            else:
                rec.water_absorption = 0.0

   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(StonesWaterAbsorptionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class StonesTrueSpecificGravityLine(models.Model):
    _name = "stone.true.specific.gravity.line"
    parent_id = fields.Many2one('mechanical.stones',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    w1 = fields.Float(string="W1 Empty Bottle (g)")

    w2 = fields.Float(string="W2 Bottle + Powder (g)")

    w3 = fields.Float(string="W3 Bottle + Powder + Water (g)")

    w4 = fields.Float(string="W4 Bottle + Water (g)")

    true_specific_gravity = fields.Float(
        string="True Specific Gravity",
        compute="_compute_tsg",
        store=True,
        digits=(16, 2),
    )

    remarks = fields.Char(string="Remarks")

    @api.depends("w1", "w2", "w3", "w4")
    def _compute_tsg(self):
        for rec in self:

            numerator = rec.w2 - rec.w1
            denominator = (rec.w4 - rec.w1) - (rec.w3 - rec.w2)

            if denominator:
                rec.true_specific_gravity = numerator / denominator
            else:
                rec.true_specific_gravity = 0.0

   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(StonesTrueSpecificGravityLine, self).create(vals)

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
















   

   

  



    


   



   
   

   
