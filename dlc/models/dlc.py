from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math
from decimal import Decimal
import matplotlib.pyplot as plt
import io
import base64
from odoo.tools.float_utils import float_round
import io
import numpy as np
import logging
import base64
from scipy.optimize import curve_fit

from scipy.interpolate import PchipInterpolator
from matplotlib.ticker import LogLocator, MultipleLocator
from matplotlib.ticker import AutoMinorLocator
from scipy.interpolate import CubicSpline , interp1d , Akima1DInterpolator
from matplotlib.ticker import MultipleLocator, StrMethodFormatter

class DLCMechanical(models.Model):
    _name = "mechanical.dlc"
    _inherit = "lerm.eln"
    _description = 'mechanical.dlc'
    _rec_name = "name"


    name = fields.Char("Name",default="Dry Lean Concrete (DLC)")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)


    temp = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'gsb.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }
    



    # Sieve Analysis
    dry_gradation_name = fields.Char(default="Sieve Analysis")
    dry_gradation_visible = fields.Boolean(compute="_compute_visible")

    weight_of_sample = fields.Float(string="Weight of Sample in gms")

    report_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non NABL'),
        ],
        string="Report Type",
        default='nabl',
        required=True,
    )

    sieve_nabl = fields.Selection(
    [('pass', 'Pass'), ('fail', 'Fail')],
    compute="_compute_sieve_nabl",
    store=True
)

    @api.depends('report_type')
    def _compute_sieve_nabl(self):
     for rec in self:
        rec.sieve_nabl = 'pass' if rec.report_type == 'nabl' else 'fail'


    sieve_analysis_child_lines = fields.One2many('dlc.dry.gradation.line','parent_id',string="Parameter")
    total_sieve_analysis = fields.Float(string="Total",compute="_compute_total_sieve")



    @api.model
    def default_get(self, fields_list):
      res = super().default_get(fields_list)

      sieve_sizes = [
        '26.50 mm',
        '19.00 mm',
        '9.50 mm',
        '4.75 mm',
        '2.36 mm',
        '600 mic',
        '300 mic',
        '150 mic',
        '75 mic',
    ]

      specific_limits = [
        '100',
        '75 - 95',
        '50 - 70',
        '30 - 55',
        '17 - 42',
        '8 - 22',
        '7 - 17',
        '2 - 12',
        '0 - 10',
    ]

      default_lines = []

      for sieve, limit in zip(sieve_sizes, specific_limits):
        default_lines.append((0, 0, {
            'sieve_size': sieve,
            'specific_limits': limit,
        }))

      res['sieve_analysis_child_lines'] = default_lines

      return res


    def populate_sieve_analysis_lines(self):
      self.ensure_one()

      specific_limits = [
        '100',
        '75 - 95',
        '50 - 70',
        '30 - 55',
        '17 - 42',
        '8 - 22',
        '7 - 17',
        '2 - 12',
        '0 - 10',
    ]

      for line, limit in zip(
        self.sieve_analysis_child_lines.sorted('serial_no'),
        specific_limits
    ):
        line.specific_limits = limit


    def calculate_sieve(self):
     for record in self:

        record.populate_sieve_analysis_lines()

        cumulative = 0.0

        for line in record.sieve_analysis_child_lines.sorted('serial_no'):

            # % retained = (weight retained / total sample weight) * 100
            if record.weight_of_sample:
                line.percent_retained = round(
                    (line.wt_retained / record.weight_of_sample) * 100,
                    2
                )
            else:
                line.percent_retained = 0

            cumulative += line.percent_retained

            line.cumulative_retained = round(cumulative, 2)
            line.passing_percent = round(100 - cumulative, 2)

#     @api.model
#     def default_get(self, fields):
#         res = super().default_get(fields)

#         default_lines = []

#         eln_ref = res.get('eln_ref')
#         if not eln_ref:
#             return res

#         eln = self.env['lerm.eln'].sudo().browse(eln_ref)
#         if not eln.exists():
#             return res

#         grade = (eln.grade_id.grade or '').strip().lower()

#         # Fixed sieve sizes
#         sieve_sizes = [
#             '26.50 mm',
#             '19.00 mm',
#             '9.50 mm',
#             '4.75 mm',
#             '2.36 mm',
#             '600 mic',
#             '300 mic',
#             '150 mic',
#             '75 mic',
#         ]



#         # Grade wise limits
#         specific_limits_mapping = [
#     '100',
#     '75 - 95',
#     '50 - 70',
#     '30 - 55',
#     '17 - 42',
#     '8 - 22',
#     '7 - 17',
#     '2 - 12',
#     '0 - 10',
# ]

#         limits = specific_limits_mapping.get(grade, [])

#         for sieve, limit in zip(sieve_sizes, limits):
#             default_lines.append((0, 0, {
#                 'sieve_size': sieve,
#                 'specific_limits': limit,
#             }))

#         res['sieve_analysis_child_lines'] = default_lines

#         return res

#     def populate_sieve_analysis_lines(self):
#         self.ensure_one()

#         if not self.eln_ref:
#             return

#         grade = (self.eln_ref.grade_id.grade or '').strip().lower()

#         specific_limits_mapping = [
#     '100',
#     '75 - 95',
#     '50 - 70',
#     '30 - 55',
#     '17 - 42',
#     '8 - 22',
#     '7 - 17',
#     '2 - 12',
#     '0 - 10',
# ]

#         limits = specific_limits_mapping.get(grade, [])

#         for line, limit in zip(self.sieve_analysis_child_lines, limits):
#             line.specific_limits = limit


    
#     def calculate_sieve(self): 
#         for record in self:
#             # import wdb; wdb.set_trace()
#             record.populate_sieve_analysis_lines()  # replace default_get call
#             for line in record.sieve_analysis_child_lines:
#                 # print("Rows",str(line.percent_retained))
#                 previous_line = line.serial_no - 1
#                 if previous_line == 0:
#                     if line.percent_retained == 0:
#                         line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2),
#                                     'passing_percent': 100 ,})
#                     else:
#                         line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2),
#                                     'passing_percent': round(100 -line.percent_retained - line.percent_retained,2),})
#                 else:
#                     previous_line_record = self.env['dlc.dry.gradation.line'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
#                     line.write({'cumulative_retained': previous_line_record + line.percent_retained,
#                                 'passing_percent': round(100-(previous_line_record + line.percent_retained),2),})
                    
                    # print("Previous Cumulative",previous_line_record)
                    

    
    @api.depends('sieve_analysis_child_lines.wt_retained')
    def _compute_total_sieve(self):
        for record in self:
            print("recordd",record)
            record.total_sieve_analysis = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))

    @api.onchange('sieve_analysis_child_lines')
    def _onchange_sieve_analysis_child_lines(self):
        for rec in self:
            pan_line = None
            total_retained = 0.0            
            # Find all unique sieve sizes except pan
            all_sieves = set()
            for line in rec.sieve_analysis_child_lines:
                if line.sieve_size and line.sieve_size.lower() != 'pan':
                    all_sieves.add(line.sieve_size.strip())
            
            # Calculate total retained for all non-pan sieves
            for line in rec.sieve_analysis_child_lines:
                if line.sieve_size and line.sieve_size.lower() == 'pan':
                    pan_line = line
                elif line.sieve_size in all_sieves:  # Include all non-pan sieves
                    total_retained += line.wt_retained or 0.0

            # Update pan weight if pan exists and we have a sample weight
            if pan_line and rec.weight_of_sample:
                pan_line.wt_retained = rec.weight_of_sample - total_retained


    # @api.depends('sieve_analysis_child_lines.wt_retained')
    # def _compute_cumulative_sieve(self):
    #     for record in self:
    #         print("recordd",record)
    #         record.cumulative = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))




    

    # Flakiness and Elongation 
    elongation_fl_name = fields.Char(default="FLAKINESS AND ELONGATION INDEX")
    elongation_fl_visible = fields.Boolean("FLAKINESS AND ELONGATION INDEX",compute="_compute_visible")


    elongation_fl_table = fields.One2many('dlc.elongation.flakiness.line','parent_id',string="Elongation Flakiness Index",default=lambda self: self.elongation_fl_table_sizess())


    @api.model
    def elongation_fl_table_sizess(self):
        default_lines = [
            (0, 0, {'passing_sieve': '63.0','retained_sieve': '50.0'}),
            (0, 0, {'passing_sieve': '50.0','retained_sieve': '40.0'}),
            (0, 0, {'passing_sieve': '40.0','retained_sieve': '31.5'}),
            (0, 0, {'passing_sieve': '31.5','retained_sieve': '25.0'}),
            (0, 0, {'passing_sieve': '25.0','retained_sieve': '20.0'}),
            (0, 0, {'passing_sieve': '20.0','retained_sieve': '16.0'}),
            (0, 0, {'passing_sieve': '16.0','retained_sieve': '12.5'}),
            (0, 0, {'passing_sieve': '12.5','retained_sieve': '10.0'}),
            (0, 0, {'passing_sieve': '10.0','retained_sieve': '6.3'}),
            
        ]
        return default_lines 


   

    total_total_weight = fields.Float("Total (Total Wt of Aggregate Retained (gm)) (A)", compute="_compute_totals", store=True)
    total_wt_passing_flakiness = fields.Float("Total (Wt Passing Flakiness Gauge (gm)) (B)", compute="_compute_totals", store=True)
    total_wt_retained_flakiness = fields.Float("Total (Wt. Retained on Flakiness gauge (gm) = [(Total Wt of aggregate Retained (gm)) - (Wt. Passing on Flakiness gauge (gm)] (C)", compute="_compute_totals", store=True)
    total_wt_retained_elongation = fields.Float("Total (Wt Retained Elongation Gauge (gm)) (D)", compute="_compute_totals", store=True)

    @api.depends(
        'elongation_fl_table.total_weight',
        'elongation_fl_table.wt_passing_flakiness',
        'elongation_fl_table.wt_retained_flakiness',
        'elongation_fl_table.wt_retained_elongation'
    )
    def _compute_totals(self):
        for rec in self:
            rec.total_total_weight = sum(rec.elongation_fl_table.mapped('total_weight'))
            rec.total_wt_passing_flakiness = sum(rec.elongation_fl_table.mapped('wt_passing_flakiness'))
            rec.total_wt_retained_flakiness = sum(rec.elongation_fl_table.mapped('wt_retained_flakiness'))
            rec.total_wt_retained_elongation = sum(rec.elongation_fl_table.mapped('wt_retained_elongation'))

    flakiness_index = fields.Float(
        string="Flakiness Index (FI=(B/A)*100) (%)",
        compute="_compute_indexes",
        store=True
    ) 

    elongation_index = fields.Float(
        string="Elongation Index (FI=(D/C)*100) (%)",
        compute="_compute_indexes",
        store=True
    )

    combined_index = fields.Float(
        string="Combined Flakiness  & Elongation Index (%)",
        compute="_compute_indexes",
        store=True
    )

    @api.depends('total_total_weight', 'total_wt_passing_flakiness', 'total_wt_retained_flakiness', 'total_wt_retained_elongation')
    def _compute_indexes(self):
        for rec in self:
            # FI = B/A * 100
            if rec.total_total_weight:
                rec.flakiness_index = (rec.total_wt_passing_flakiness / rec.total_total_weight) * 100
            else:
                rec.flakiness_index = 0.0

            # EI = D/C * 100
            if rec.total_wt_retained_flakiness:
                rec.elongation_index = (rec.total_wt_retained_elongation / rec.total_wt_retained_flakiness) * 100
            else:
                rec.elongation_index = 0.0

            # Combined
            rec.combined_index = rec.flakiness_index + rec.elongation_index


    elongation_index_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Elongation Index Conformity", compute="_compute_elongation_index_conformity", store=True)

    @api.depends('elongation_index','eln_ref','grade')
    def _compute_elongation_index_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.elongation_index_conformity = 'na'
                continue
            record.elongation_index_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3245a108-16bd-457a-961a-2698a91ff0c6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3245a108-16bd-457a-961a-2698a91ff0c6')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.elongation_index - record.elongation_index*mu_value
                    upper = record.elongation_index + record.elongation_index*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.elongation_index_conformity = 'pass'
                        break
                    else:
                        record.elongation_index_conformity = 'fail'

    elongation_index_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Elongation Index NABL", compute="_compute_elongation_index_nabl", store=True)

    @api.depends('elongation_index','eln_ref','grade')
    def _compute_elongation_index_nabl(self):
        
        for record in self:
            record.elongation_index_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3245a108-16bd-457a-961a-2698a91ff0c6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3245a108-16bd-457a-961a-2698a91ff0c6')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.elongation_index - record.elongation_index*mu_value
                    upper = record.elongation_index + record.elongation_index*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.elongation_index_nabl = 'pass'
                        break
                    else:
                        record.elongation_index_nabl = 'fail'

    elongation_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Elongation Report Type", default='auto')
    
    elongation_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_elongation_final_report", store=True)
    
    @api.depends('elongation_index_nabl', 'elongation_report_type')
    def _compute_elongation_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.elongation_report_type == 'nabl':
                rec.elongation_final_report = 'nabl'
    
            elif rec.elongation_report_type == 'non_nabl':
                rec.elongation_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.elongation_index_nabl == 'pass':
                    rec.elongation_final_report = 'nabl'
                else:
                    rec.elongation_final_report = 'non_nabl'

    flakiness_index_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Flakiness Index Conformity", compute="_compute_flakiness_index_conformity", store=True)

    @api.depends('flakiness_index','eln_ref','grade')
    def _compute_flakiness_index_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.flakiness_index_conformity = 'na'
                continue
            record.flakiness_index_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c79b6bab-8c9f-41cb-a568-8c044629d898')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c79b6bab-8c9f-41cb-a568-8c044629d898')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.flakiness_index - record.flakiness_index*mu_value
                    upper = record.flakiness_index + record.flakiness_index*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.flakiness_index_conformity = 'pass'
                        break
                    else:
                        record.flakiness_index_conformity = 'fail'

    flakiness_index_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_flakiness_index_nabl", store=True)

    @api.depends('flakiness_index','eln_ref','grade')
    def _compute_flakiness_index_nabl(self):
        
        for record in self:
            record.flakiness_index_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c79b6bab-8c9f-41cb-a568-8c044629d898')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c79b6bab-8c9f-41cb-a568-8c044629d898')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.flakiness_index - record.flakiness_index*mu_value
                    upper = record.flakiness_index + record.flakiness_index*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.flakiness_index_nabl = 'pass'
                        break
                    else:
                        record.flakiness_index_nabl = 'fail'


    flakiness_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Flakiness Report Type", default='auto')
    
    flakiness_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_flakiness_final_report", store=True)
    
    @api.depends('flakiness_index_nabl', 'flakiness_report_type')
    def _compute_flakiness_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.flakiness_report_type == 'nabl':
                rec.flakiness_final_report = 'nabl'
    
            elif rec.flakiness_report_type == 'non_nabl':
                rec.flakiness_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.flakiness_index_nabl == 'pass':
                    rec.flakiness_final_report = 'nabl'
                else:
                    rec.flakiness_final_report = 'non_nabl'



    # Impact Value 
    impact_value_name = fields.Char("Name",default="Aggregate Impact Value")
    impact_visible = fields.Boolean("Impact Visible",compute="_compute_visible")

    impact_value_child_lines = fields.One2many('dlc.impact.line','parent_id',string="Parameter")

    average_impact_value = fields.Float(string="Average Value of A.I.V", compute="_compute_average_impact_value")

    

    @api.depends('impact_value_child_lines.impact_value')
    def _compute_average_impact_value(self):
        for record in self:
            if record.impact_value_child_lines:
                sum_impact_value = sum(record.impact_value_child_lines.mapped('impact_value'))
                record.average_impact_value = round((sum_impact_value / len(record.impact_value_child_lines)),1)
            else:
                record.average_impact_value = 0.0

    average_impact_value_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_average_impact_value_conformity", store=True)



    @api.depends('average_impact_value','eln_ref','grade')
    def _compute_average_impact_value_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_impact_value_conformity = 'na'
                continue
            record.average_impact_value_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4db01f03-8c95-47dc-8a22-664ce4473864')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4db01f03-8c95-47dc-8a22-664ce4473864')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_impact_value - record.average_impact_value*mu_value
                    upper = record.average_impact_value + record.average_impact_value*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_impact_value_conformity = 'pass'
                        break
                    else:
                        record.average_impact_value_conformity = 'fail'

    average_impact_value_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_impact_value_nabl", store=True)

    @api.depends('average_impact_value','eln_ref','grade')
    def _compute_average_impact_value_nabl(self):
        
        for record in self:
            record.average_impact_value_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4db01f03-8c95-47dc-8a22-664ce4473864')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4db01f03-8c95-47dc-8a22-664ce4473864')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_impact_value - record.average_impact_value*mu_value
            upper = record.average_impact_value + record.average_impact_value*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_impact_value_nabl = 'pass'
                break
            else:
                record.average_impact_value_nabl = 'fail'


    impact_value_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    impact_value_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_impact_value_final_report", store=True)
    
    @api.depends('average_impact_value_nabl', 'impact_value_report_type')
    def _compute_impact_value_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.impact_value_report_type == 'nabl':
                rec.impact_value_final_report = 'nabl'
    
            elif rec.impact_value_report_type == 'non_nabl':
                rec.impact_value_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.average_impact_value_nabl == 'pass':
                    rec.impact_value_final_report = 'nabl'
                else:
                    rec.impact_value_final_report = 'non_nabl'


    

    # Water Absorbtion 
    water_absorbtion_name = fields.Char(default="Specific Gravity & Water Absorption")
    water_absorbtion_visible = fields.Boolean(compute="_compute_visible")

    specific_water_line_ids = fields.One2many('dlc.specific.gravity.water.absorption.line', 'parent_id', string="Observations")

    avg_specific_gravity = fields.Float("Average Specific Gravity", compute="_compute_avg_specific_water", store=True,digits=(10,3))
    avg_water_absorption = fields.Float("Average Water Absorption (%)", compute="_compute_avg_specific_water", store=True,digits=(10,3))

    @api.depends('specific_water_line_ids.specific_gravity', 'specific_water_line_ids.water_absorption')
    def _compute_avg_specific_water(self):
     for rec in self:
        lines = rec.specific_water_line_ids

        if lines:
            sg_list = lines.mapped('specific_gravity')
            wa_list = lines.mapped('water_absorption')

            rec.avg_specific_gravity = sum(sg_list) / len(sg_list) if sg_list else 0.0
            rec.avg_water_absorption = sum(wa_list) / len(wa_list) if wa_list else 0.0
        else:
            rec.avg_specific_gravity = 0.0
            rec.avg_water_absorption = 0.0


    avg_specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_specific_gravity_conformity", store=True)

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_specific_gravity_conformity = 'na'
                continue
            record.avg_specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3033da6d-4e25-4208-8df9-2de3f4ab0a8c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3033da6d-4e25-4208-8df9-2de3f4ab0a8c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_specific_gravity - record.avg_specific_gravity*mu_value
                    upper = record.avg_specific_gravity + record.avg_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.avg_specific_gravity_conformity = 'fail'

    avg_specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_specific_gravity_nabl", store=True)

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_nabl(self):
        
        for record in self:
            record.avg_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3033da6d-4e25-4208-8df9-2de3f4ab0a8c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3033da6d-4e25-4208-8df9-2de3f4ab0a8c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_specific_gravity - record.avg_specific_gravity*mu_value
                    upper = record.avg_specific_gravity + record.avg_specific_gravity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_specific_gravity_nabl = 'pass'
                        break
                    else:
                        record.avg_specific_gravity_nabl = 'fail'


    specific_gravity_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    specific_gravity_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_specific_gravity_final_report", store=True)
    
    @api.depends('avg_specific_gravity_nabl', 'specific_gravity_report_type')
    def _compute_specific_gravity_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.specific_gravity_report_type == 'nabl':
                rec.specific_gravity_final_report = 'nabl'
    
            elif rec.specific_gravity_report_type == 'non_nabl':
                rec.specific_gravity_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.avg_specific_gravity_nabl == 'pass':
                    rec.specific_gravity_final_report = 'nabl'
                else:
                    rec.specific_gravity_final_report = 'non_nabl'


    avg_water_absorption_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_water_absorption_conformity", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_water_absorption_conformity = 'na'
                continue
            record.avg_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a4a23f3-aff8-4a87-8ce9-19641ea88d75')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a4a23f3-aff8-4a87-8ce9-19641ea88d75')]).parameter_table
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
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_water_absorption_nabl", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_nabl(self):
        
        for record in self:
            record.avg_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a4a23f3-aff8-4a87-8ce9-19641ea88d75')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a4a23f3-aff8-4a87-8ce9-19641ea88d75')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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


    


    # Soundness Na2SO4
    soundness_na2so4_name = fields.Char("Name",default="SOUNDNESS (SODIUM SULPHATE TEST)")
    soundness_na2so4_visible = fields.Boolean("SOUNDNESS OF COARSE AGGREGATE (SODIUM SULPHATE TEST) Visible",compute="_compute_visible")

    soundness_sod_line_ids = fields.One2many(
        'dlc.sodium.sulphate.line',
        'parent_id',
        string="Soundness Na2SO4",default=lambda self: self.soundness_sod_line_ids_sizes()
    )

    @api.model
    def soundness_sod_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '60mm','retained_sieve': '40mm'}),
            (0, 0, {'passing_sieve': '40mm','retained_sieve': '20mm'}),
            (0, 0, {'passing_sieve': '20mm','retained_sieve': '10mm'}),
            (0, 0, {'passing_sieve': '10mm','retained_sieve': '4.75mm'}),
        ]
        return default_lines 
    


    total_grading = fields.Float("Total Grading %", compute="_compute_totaled")
    total_weight_before = fields.Float("Total Weight Before", compute="_compute_totaled")
    total_weight_after = fields.Float("Total Weight After", compute="_compute_totaled")
    total_percent_loss = fields.Float("Total % Loss (Not Used)", compute="_compute_totaled")
    total_weighted_avg = fields.Float("Final Result (Weighted Avg)", compute="_compute_totaled")

    @api.depends(
        'soundness_sod_line_ids.grading_percent',
        'soundness_sod_line_ids.weight_before',
        'soundness_sod_line_ids.weight_after',
        'soundness_sod_line_ids.percent_loss',
        'soundness_sod_line_ids.weighted_avg'
    )
    def _compute_totaled(self):
        for rec in self:
            rec.total_grading = sum(rec.soundness_sod_line_ids.mapped('grading_percent'))
            rec.total_weight_before = sum(rec.soundness_sod_line_ids.mapped('weight_before'))
            rec.total_weight_after = sum(rec.soundness_sod_line_ids.mapped('weight_after'))
            rec.total_percent_loss = sum(rec.soundness_sod_line_ids.mapped('percent_loss'))
            rec.total_weighted_avg = sum(rec.soundness_sod_line_ids.mapped('weighted_avg'))


    soundness_sodtwo_line_ids = fields.One2many(
        'dlc.sodium.sulphate.two.line',
        'parent_id',
        string="Soundness Na2SO4",default=lambda self: self.soundness_sodtwo_line_ids_sizes()
    )

    @api.model
    def soundness_sodtwo_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '600mic','retained_sieve': '300mic'}),
            (0, 0, {'passing_sieve': '1.18mm','retained_sieve': '600mic'}),
            (0, 0, {'passing_sieve': '2.36mm','retained_sieve': '1.18mm'}),
            (0, 0, {'passing_sieve': '4.75mm','retained_sieve': '2.36mm'}),
            (0, 0, {'passing_sieve': '10mm','retained_sieve': '4.75mm'}),
            
        ]
        return default_lines 
    
    total1_grading = fields.Float("Total (Grading of Original Sample (%)", compute="_compute_totally")
    total1_weight_before = fields.Float("Total (Weight of Test Fraction Before Test (gm))", compute="_compute_totally")
    total1_weight_after = fields.Float("Total (Weight of Test Fraction After Test (gm))", compute="_compute_totally")
    total1_percent_loss = fields.Float("Total (Percentage Passing Finer Sieve After Test (Actual Percentage Loss))", compute="_compute_totally")
    total1_weighted_avg = fields.Float("Final Result (Weighted Average  (Corrected Percent Loss))", compute="_compute_totally")

    @api.depends(
        'soundness_sodtwo_line_ids.grading_percent',
        'soundness_sodtwo_line_ids.weight_before',
        'soundness_sodtwo_line_ids.weight_after',
        'soundness_sodtwo_line_ids.percent_loss',
        'soundness_sodtwo_line_ids.weighted_avg'
    )
    def _compute_totally(self):
        for rec in self:
            rec.total1_grading = sum(rec.soundness_sodtwo_line_ids.mapped('grading_percent'))
            rec.total1_weight_before = sum(rec.soundness_sodtwo_line_ids.mapped('weight_before'))
            rec.total1_weight_after = sum(rec.soundness_sodtwo_line_ids.mapped('weight_after'))
            rec.total1_percent_loss = sum(rec.soundness_sodtwo_line_ids.mapped('percent_loss'))
            rec.total1_weighted_avg = sum(rec.soundness_sodtwo_line_ids.mapped('weighted_avg'))


    total_weighted_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_total_weighted_avg_conformity", store=True)

    @api.depends('total_weighted_avg','eln_ref','grade')
    def _compute_total_weighted_avg_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.total_weighted_avg_conformity = 'na'
                continue
            record.total_weighted_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0782fd41-b852-424a-92ed-7c91935df3bd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0782fd41-b852-424a-92ed-7c91935df3bd')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.total_weighted_avg - record.total_weighted_avg*mu_value
                    upper = record.total_weighted_avg + record.total_weighted_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.total_weighted_avg_conformity = 'pass'
                        break
                    else:
                        record.total_weighted_avg_conformity = 'fail'

    total_weighted_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_total_weighted_avg_nabl", store=True)

    @api.depends('total_weighted_avg','eln_ref','grade')
    def _compute_total_weighted_avg_nabl(self):
        
        for record in self:
            record.total_weighted_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0782fd41-b852-424a-92ed-7c91935df3bd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0782fd41-b852-424a-92ed-7c91935df3bd')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                 lab_min = line.lab_min_value
                 lab_max = line.lab_max_value
                 mu_value = line.mu_value
            
                 lower = record.total_weighted_avg - record.total_weighted_avg*mu_value
                 upper = record.total_weighted_avg + record.total_weighted_avg*mu_value
                 if lower >= lab_min and upper <= lab_max:
                   record.total_weighted_avg_nabl = 'pass'
                   break
                 else:
                   record.total_weighted_avg_nabl = 'fail'


    sodium_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    sodium_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_sodium_final_report", store=True)
    
    @api.depends('total_weighted_avg_nabl', 'sodium_report_type')
    def _compute_sodium_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.sodium_report_type == 'nabl':
                rec.sodium_final_report = 'nabl'
    
            elif rec.sodium_report_type == 'non_nabl':
                rec.sodium_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.total_weighted_avg_nabl == 'pass':
                    rec.sodium_final_report = 'nabl'
                else:
                    rec.sodium_final_report = 'non_nabl'


    # SOUNDNESS (MAGNESIUM SULPHATE TEST)
    soundness_mgso4_name = fields.Char("Name",default="SOUNDNESS (MAGNESIUM SULPHATE TEST)")
    soundness_mgso4_visible = fields.Boolean("SOUNDNESS (MAGNESIUM SULPHATE TEST) Visible",compute="_compute_visible")

    soundness_mag_line_ids = fields.One2many(
        'dlc.magnesium.sulphate.line',
        'parent_id',
        string="Soundness MgSO4",default=lambda self: self.soundness_mag_line_ids_sizes()
    )

    @api.model
    def soundness_mag_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '63mm','retained_sieve': '40mm'}),
            (0, 0, {'passing_sieve': '40mm','retained_sieve': '20mm'}),
            (0, 0, {'passing_sieve': '20mm','retained_sieve': '10mm'}),
            (0, 0, {'passing_sieve': '10mm','retained_sieve': '4.75mm'}),
        ]
        return default_lines 
    


    mag_total_grading = fields.Float("Total Grading %", compute="_compute_totalled")
    mag_total_weight_before = fields.Float("Total Weight Before", compute="_compute_totalled")
    mag_total_weight_after = fields.Float("Total Weight After", compute="_compute_totalled")
    mag_total_percent_loss = fields.Float("Total % Loss (Not Used)", compute="_compute_totalled")
    mag_total_weighted_avg = fields.Float("Final Result (Weighted Avg)", compute="_compute_totalled")

    @api.depends(
        'soundness_mag_line_ids.grading_percent',
        'soundness_mag_line_ids.weight_before',
        'soundness_mag_line_ids.weight_after',
        'soundness_mag_line_ids.percent_loss',
        'soundness_mag_line_ids.weighted_avg'
    )
    def _compute_totalled(self):
        for rec in self:
            rec.mag_total_grading = sum(rec.soundness_mag_line_ids.mapped('grading_percent'))
            rec.mag_total_weight_before = sum(rec.soundness_mag_line_ids.mapped('weight_before'))
            rec.mag_total_weight_after = sum(rec.soundness_mag_line_ids.mapped('weight_after'))
            rec.mag_total_percent_loss = sum(rec.soundness_mag_line_ids.mapped('percent_loss'))
            rec.mag_total_weighted_avg = sum(rec.soundness_mag_line_ids.mapped('weighted_avg'))


    soundness_magtwo_line_ids = fields.One2many(
        'dlc.magnesium.sulphate.two.line',
        'parent_id',
        string="Soundness MgSO4",default=lambda self: self.soundness_magtwo_line_ids_sizes()
    )

    @api.model
    def soundness_magtwo_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '600mic','retained_sieve': '300mic'}),
            (0, 0, {'passing_sieve': '1.18mm','retained_sieve': '600mic'}),
            (0, 0, {'passing_sieve': '2.36mm','retained_sieve': '1.18mm'}),
            (0, 0, {'passing_sieve': '4.75mm','retained_sieve': '2.36mm'}),
            (0, 0, {'passing_sieve': '10mm','retained_sieve': '4.75mm'}),
            
        ]
        return default_lines 
    
    mag_total1_grading = fields.Float("Total (Grading of Original Sample (%))", compute="_compute_totallly")
    mag_total1_weight_before = fields.Float("TTotal (Weight of Test Fraction Before Test (gm))", compute="_compute_totallly")
    mag_total1_weight_after = fields.Float("Total (Weight of Test Fraction After Test (gm))", compute="_compute_totallly")
    mag_total1_percent_loss = fields.Float("otal (Percentage Passing Finer Sieve After Test (Actual Percentage Loss))", compute="_compute_totallly")
    mag_total1_weighted_avg = fields.Float("Final Result (Weighted Average  (Corrected Percent Loss))", compute="_compute_totallly")

    @api.depends(
        'soundness_magtwo_line_ids.grading_percent',
        'soundness_magtwo_line_ids.weight_before',
        'soundness_magtwo_line_ids.weight_after',
        'soundness_magtwo_line_ids.percent_loss',
        'soundness_magtwo_line_ids.weighted_avg'
    )
    def _compute_totallly(self):
        for rec in self:
            rec.mag_total1_grading = sum(rec.soundness_magtwo_line_ids.mapped('grading_percent'))
            rec.mag_total1_weight_before = sum(rec.soundness_magtwo_line_ids.mapped('weight_before'))
            rec.mag_total1_weight_after = sum(rec.soundness_magtwo_line_ids.mapped('weight_after'))
            rec.mag_total1_percent_loss = sum(rec.soundness_magtwo_line_ids.mapped('percent_loss'))
            rec.mag_total1_weighted_avg = sum(rec.soundness_magtwo_line_ids.mapped('weighted_avg'))


    mag_total_weighted_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_mag_total_weighted_avg_conformity", store=True)


    @api.depends('mag_total_weighted_avg','eln_ref','grade')
    def _compute_mag_total_weighted_avg_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.mag_total_weighted_avg_conformity = 'na'
                continue
            record.mag_total_weighted_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f50ffb5e-99a5-437f-b9b0-9e1e4c7d7e72')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f50ffb5e-99a5-437f-b9b0-9e1e4c7d7e72')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.mag_total_weighted_avg - record.mag_total_weighted_avg*mu_value
                    upper = record.mag_total_weighted_avg + record.mag_total_weighted_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.mag_total_weighted_avg_conformity = 'pass'
                        break
                    else:
                        record.mag_total_weighted_avg_conformity = 'fail'


    mag_total_weighted_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_mag_total_weighted_avg_nabl", store=True)

    @api.depends('mag_total_weighted_avg','eln_ref','grade')
    def _compute_mag_total_weighted_avg_nabl(self):
        
        for record in self:
            record.mag_total_weighted_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f50ffb5e-99a5-437f-b9b0-9e1e4c7d7e72')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f50ffb5e-99a5-437f-b9b0-9e1e4c7d7e72')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.mag_total_weighted_avg - record.mag_total_weighted_avg*mu_value
                    upper = record.mag_total_weighted_avg + record.mag_total_weighted_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.mag_total_weighted_avg_nabl = 'pass'
                        break
                    else:
                        record.mag_total_weighted_avg_nabl = 'fail'


    magnesium_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    magnesium_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_magnesium_final_report", store=True)
    
    @api.depends('mag_total_weighted_avg_nabl', 'magnesium_report_type')
    def _compute_magnesium_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.magnesium_report_type == 'nabl':
                rec.magnesium_final_report = 'nabl'
    
            elif rec.magnesium_report_type == 'non_nabl':
                rec.magnesium_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.mag_total_weighted_avg_nabl == 'pass':
                    rec.magnesium_final_report = 'nabl'
                else:
                    rec.magnesium_final_report = 'non_nabl'


    


      # Heavy Compaction-MDD
    heavy_name = fields.Char("Name",default="DETERMINATION OF Heavy Compaction - OMC AND MDD ")
    heavy_visible = fields.Boolean("Heavy Compaction-MDD Visible",compute="_compute_visible")
    heavy_table = fields.One2many('dlc.heavy.compaction.line','parent_id',string="Heavy Compaction")

    heavy_mould_no = fields.Char(string="Mould No.")
    heavy_mould_weight = fields.Float(string="Wt. of Mould (A)")
    heavy_mould_volume = fields.Float(string="Volume of Mould (V)")

    max_dry_density = fields.Float(string="Max Dry Density (g/cc)", compute="_compute_max_dry_density", store=True)

    omc = fields.Float(string="Optimum Moisture Content (OMC)", compute="_compute_max_density_and_omc", store=True)

    @api.depends('heavy_table.dry_density', 'heavy_table.water_content')
    def _compute_max_density_and_omc(self):
        for rec in self:
            max_density = 0.0
            omc_value = 0.0
            for line in rec.heavy_table:
                if line.dry_density > max_density:
                    max_density = line.dry_density
                    omc_value = line.water_content
            rec.max_dry_density = max_density
            rec.omc = omc_value

    @api.depends('heavy_table.dry_density')
    def _compute_max_dry_density(self):
        for rec in self:
            densities = rec.heavy_table.mapped('dry_density')
            rec.max_dry_density = max(densities) if densities else 0.0
 
   


    max_dry_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_max_dry_density_conformity", store=True)

    @api.depends('max_dry_density','eln_ref','grade')
    def _compute_max_dry_density_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.max_dry_density_conformity = 'na'
                continue
            record.max_dry_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','411f6642-0ef2-4242-9410-bef505035c7e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','411f6642-0ef2-4242-9410-bef505035c7e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.max_dry_density - record.max_dry_density*mu_value
                    upper = record.max_dry_density + record.max_dry_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.max_dry_density_conformity = 'pass'
                        break
                    else:
                        record.max_dry_density_conformity = 'fail'

    max_dry_density_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_max_dry_density_nabl", store=True)

    @api.depends('max_dry_density','eln_ref','grade')
    def _compute_max_dry_density_nabl(self):
        
        for record in self:
            record.max_dry_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','411f6642-0ef2-4242-9410-bef505035c7e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','411f6642-0ef2-4242-9410-bef505035c7e')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.max_dry_density - record.max_dry_density*mu_value
            upper = record.max_dry_density + record.max_dry_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.max_dry_density_nabl = 'pass'
                break
            else:
                record.max_dry_density_nabl = 'fail'


    dry_density_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    dry_density_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_dry_density_final_report", store=True)
    
    @api.depends('max_dry_density_nabl', 'dry_density_report_type')
    def _compute_dry_density_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.dry_density_report_type == 'nabl':
                rec.dry_density_final_report = 'nabl'
    
            elif rec.dry_density_report_type == 'non_nabl':
                rec.dry_density_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.max_dry_density_nabl == 'pass':
                    rec.dry_density_final_report = 'nabl'
                else:
                    rec.dry_density_final_report = 'non_nabl'


    omc_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_omc_conformity", store=True)

    @api.depends('omc','eln_ref','grade')
    def _compute_omc_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.omc_conformity = 'na'
                continue
            record.omc_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','95af7fbd-ba6d-46ec-b51f-02b4813fd56e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','95af7fbd-ba6d-46ec-b51f-02b4813fd56e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.omc - record.omc*mu_value
                    upper = record.omc + record.omc*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.omc_conformity = 'pass'
                        break
                    else:
                        record.omc_conformity = 'fail'

    omc_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_omc_nabl", store=True)

    @api.depends('omc','eln_ref','grade')
    def _compute_omc_nabl(self):
        
        for record in self:
            record.omc_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','95af7fbd-ba6d-46ec-b51f-02b4813fd56e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','95af7fbd-ba6d-46ec-b51f-02b4813fd56e')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.omc - record.omc*mu_value
            upper = record.omc + record.omc*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.omc_nabl = 'pass'
                break
            else:
                record.omc_nabl = 'fail'

    omc_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    omc_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_omc_final_report", store=True)
    
    @api.depends('omc_nabl', 'omc_report_type')
    def _compute_omc_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.omc_report_type == 'nabl':
                rec.omc_final_report = 'nabl'
    
            elif rec.omc_report_type == 'non_nabl':
                rec.omc_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.omc_nabl == 'pass':
                    rec.omc_final_report = 'nabl'
                else:
                    rec.omc_final_report = 'non_nabl'

    
    graph_image_density = fields.Binary("Line Chart", compute="_compute_graph_image_density_omc_light", store=True)

    show_heavy_graph = fields.Boolean(string="Show Compaction Graph")



    # def generate_line_chart_light_omc(self):

    #  x_value = []
    #  y_value = []

    #  for line in self.heavy_table:
    #     if line.water_content and line.dry_density:
    #         x_value.append(float(line.water_content))
    #         y_value.append(float(line.dry_density))

    #  if len(x_value) < 3:
    #     return False

    # # Sort data
    #  data = sorted(zip(x_value, y_value))
    #  x = np.array([d[0] for d in data])
    #  y = np.array([d[1] for d in data])

    # # ==========================
    # # Quadratic Compaction Curve
    # # ==========================
    #  coeff = np.polyfit(x, y, 2)
    #  poly = np.poly1d(coeff)

    #  x_smooth = np.linspace(x.min(), x.max(), 500)
    #  y_smooth = poly(x_smooth)

    # # OMC / MDD
    #  omc = -coeff[1] / (2 * coeff[0])
    #  mdd = poly(omc)

    #  plt.figure(figsize=(15, 5))

    # # Smooth blue curve
    #  plt.plot(
    #     x_smooth,
    #     y_smooth,
    #     color='blue',
    #     linewidth=2.5
    # )

    # # Show points ON CURVE only
    #  y_curve_points = poly(x)
  
    #  plt.scatter(
    #     x,
    #     y_curve_points,
    #     color='red',
    #     edgecolors='none',
    #     s=40,
    #     zorder=5
    # )

    # # Peak point
    #  plt.scatter(
    #     omc,
    #     mdd,
    #     color='red',
    #     s=120,
    #     zorder=10
    # )

    # # OMC / MDD guide lines
    #  plt.axhline(
    #     y=mdd,
    #     color='red',
    #     linestyle='--',
    #     linewidth=1
    # )

    #  plt.axvline(
    #     x=omc,
    #     color='red',
    #     linestyle='--',
    #     linewidth=1
    # )

    # # Annotation
    #  plt.text(
    #     omc + 0.2,
    #     mdd + 0.002,
    #     f"OMC: {omc:.2f}%\nMDD: {mdd:.2f}",
    #     color='red',
    #     fontsize=11,
    #     fontweight='bold'
    # )

    # # Labels
    #  plt.xlabel(
    #     'Water Content (%)',
    #     fontsize=12
    # )

    #  plt.ylabel(
    #     'Dry Density (g/cc)',
    #     fontsize=12
    # )

    #  plt.title(
    #     'DETERMINATION OF COMPACTION OMC / MDD',
    #     fontsize=16
    # )

    # # Limits
    #  plt.xlim(
    #     left=0,
    #     right=max(x) + 2
    # )

    #  plt.ylim(
    #     bottom=min(y) - 0.03,
    #     top=max(y_smooth) + 0.03
    # )

    # # ==========================
    # # Graph Paper Background
    # # ==========================
    #  ax = plt.gca()

    # # X-axis grid
    #  ax.xaxis.set_major_locator(MultipleLocator(1))
    #  ax.xaxis.set_minor_locator(MultipleLocator(0.1))

    # # Y-axis grid
    #  ax.yaxis.set_major_locator(MultipleLocator(0.05))
    #  ax.yaxis.set_minor_locator(MultipleLocator(0.001))

    # # Major Grid
    #  plt.grid(
    #     which='major',
    #     color='green',
    #     linestyle='-',
    #     linewidth=0.5,
    #     alpha=0.55
    # )

    # # Minor Grid
    #  plt.grid(
    #     which='minor',
    #     color='green',
    #     linestyle=':',
    #     linewidth=0.3,
    #     alpha=0.45
    # )

    #  plt.tight_layout()

    # # Save Image
    #  buffer = io.BytesIO()

    #  plt.savefig(
    #     buffer,
    #     format='png',
    #     dpi=150,
    #     bbox_inches='tight'
    # )

    #  plt.close()

    #  buffer.seek(0)

    #  return base64.b64encode(
    #     buffer.read()
    # ).decode('utf-8')




    def generate_line_chart_light_omc(self):


      x = []
      y = []

      for line in self.heavy_table:
        if line.water_content and line.dry_density:
            x.append(float(line.water_content))
            y.append(float(line.dry_density))

      if len(x) < 3:
        return False

    # ---------------------------------------
    # Sort data
    # ---------------------------------------
      data = sorted(zip(x, y))
      x = np.array([i[0] for i in data], dtype=float)
      y = np.array([i[1] for i in data], dtype=float)

      omc = float(self.omc)
      mdd = float(self.max_dry_density)

    # ---------------------------------------
    # Create parabola through:
    # First Point
    # OMC/MDD
    # Last Point
    # ---------------------------------------

      x1 = x[0]
      y1 = y[0]

      x2 = omc
      y2 = mdd

      x3 = x[-1]
      y3 = y[-1]

      A = np.array([
        [x1**2, x1, 1],
        [x2**2, x2, 1],
        [x3**2, x3, 1]
    ], dtype=float)

      B = np.array([
        y1,
        y2,
        y3
    ], dtype=float)

      a, b, c = np.linalg.solve(A, B)

      def curve(xx):
          return a * xx**2 + b * xx + c

      x_smooth = np.linspace(x1, x3, 500)
      y_smooth = curve(x_smooth)

    # ---------------------------------------
    # Plot
    # ---------------------------------------

      plt.figure(figsize=(15, 5))

      plt.plot(
        x_smooth,
        y_smooth,
        color="blue",
        linewidth=2.8,
        zorder=2
    )

      plt.scatter(
        x,
        y,
        color="red",
        s=45,
        zorder=5
    )

      plt.scatter(
        omc,
        mdd,
        color="red",
        s=160,
        zorder=10
    )

      plt.axhline(
        y=mdd,
        color="red",
        linestyle="--",
        linewidth=1
    )

      plt.axvline(
        x=omc,
        color="red",
        linestyle="--",
        linewidth=1
    )

      plt.text(
        omc + 0.15,
        mdd + 0.002,
        f"OMC: {omc:.2f}%\nMDD: {mdd:.2f}",
        fontsize=12,
        color="red",
        fontweight="bold"
    )

      plt.xlabel(
        "Water Content (%)",
        fontsize=16
    )

      plt.ylabel(
        "Dry Density (g/cc)",
        fontsize=16
    )

      plt.title(
        "DETERMINATION OF COMPACTION OMC / MDD",
        fontsize=22
    )

      plt.xlim(0, max(x) + 2)

      ymin = min(min(y), min(y_smooth))
      ymax = max(max(y), max(y_smooth), mdd)

      plt.ylim(
        ymin - 0.02,
        ymax + 0.03
    )

        # ---------------------------------------
    # Graph paper background
    # ---------------------------------------

      ax = plt.gca()

      ax.set_facecolor("#f8fff8")

      ax.xaxis.set_major_locator(MultipleLocator(1))
      ax.xaxis.set_minor_locator(MultipleLocator(0.1))

      ax.yaxis.set_major_locator(MultipleLocator(0.05))
      ax.yaxis.set_minor_locator(MultipleLocator(0.005))

      ax.grid(
        which="major",
        color="green",
        linewidth=0.5,
        alpha=0.45
    )

      ax.grid(
        which="minor",
        color="green",
        linestyle=":",
        linewidth=0.3,
        alpha=0.35
    )

    # Make border thicker
      for spine in ax.spines.values():
        spine.set_linewidth(1.2)

      plt.tight_layout()

    # ---------------------------------------
    # Save Image
    # ---------------------------------------

      buffer = io.BytesIO()

      plt.savefig(
        buffer,
        format="png",
        dpi=100,
        bbox_inches="tight"
    )

      plt.close()

      buffer.seek(0)

      return base64.b64encode(
        buffer.read()
    ).decode("utf-8")



    @api.depends('heavy_table')
    def _compute_graph_image_density_omc_light(self):
        try:
            for record in self:
                chart_image_light_omc = record.generate_line_chart_light_omc()
                record.graph_image_density = chart_image_light_omc
        except:
            pass 



    # Light Compaction-MDD
    omc_name = fields.Char("Name",default="DETERMINATION OF Light Compaction - OMC AND MDD ")
    omc_visible = fields.Boolean("omc Compaction-MDD Visible",compute="_compute_visible")
    omc_table = fields.One2many('dlc.omc.compaction.line','parent_id',string="OMC Compaction")

    light_mould_no = fields.Char(string="Mould No.")
    light_mould_weight = fields.Float(string="Wt. of Mould (A)")
    light_mould_volume = fields.Float(string="Volume of Mould (V)")

    max_dry_density1 = fields.Float(string="Max Dry Density (g/cc)", compute="_compute_max_dry_density1", store=True)

    omc1 = fields.Float(string="Optimum Moisture Content (OMC)", compute="_compute_max_density_and_omc1", store=True)

    @api.depends('omc_table.dry_density1', 'omc_table.water_content1')
    def _compute_max_density_and_omc1(self):
        for rec in self:
            max_density1 = 0.0
            omc_value1 = 0.0
            for line in rec.omc_table:
                if line.dry_density1 > max_density1:
                    max_density1 = line.dry_density1
                    omc_value1 = line.water_content1
            rec.max_dry_density1 = max_density1
            rec.omc1 = omc_value1

    @api.depends('omc_table.dry_density1')
    def _compute_max_dry_density1(self):
        for rec in self:
            densities = rec.omc_table.mapped('dry_density1')
            rec.max_dry_density1 = max(densities) if densities else 0.0
 
   


    max_dry_density1_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_max_dry_density1_conformity", store=True)

    @api.depends('max_dry_density1','eln_ref','grade')
    def _compute_max_dry_density1_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.max_dry_density1_conformity = 'na'
                continue
            record.max_dry_density1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37ac17a7-840e-412a-99f8-bb98687318f2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37ac17a7-840e-412a-99f8-bb98687318f2')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.max_dry_density1 - record.max_dry_density1*mu_value
                    upper = record.max_dry_density1 + record.max_dry_density1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.max_dry_density1_conformity = 'pass'
                        break
                    else:
                        record.max_dry_density1_conformity = 'fail'

    max_dry_density1_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_max_dry_density1_nabl", store=True)

    @api.depends('max_dry_density1','eln_ref','grade')
    def _compute_max_dry_density1_nabl(self):
        
        for record in self:
            record.max_dry_density1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37ac17a7-840e-412a-99f8-bb98687318f2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37ac17a7-840e-412a-99f8-bb98687318f2')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.max_dry_density1 - record.max_dry_density1*mu_value
            upper = record.max_dry_density1 + record.max_dry_density1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.max_dry_density1_nabl = 'pass'
                break
            else:
                record.max_dry_density1_nabl = 'fail'


    dry_density1_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    dry_density1_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_dry_density1_final_report", store=True)
    
    @api.depends('max_dry_density1_nabl', 'dry_density1_report_type')
    def _compute_dry_density1_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.dry_density1_report_type == 'nabl':
                rec.dry_density1_final_report = 'nabl'
    
            elif rec.dry_density1_report_type == 'non_nabl':
                rec.dry_density1_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.max_dry_density1_nabl == 'pass':
                    rec.dry_density1_final_report = 'nabl'
                else:
                    rec.dry_density1_final_report = 'non_nabl'

    omc1_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_omc1_conformity", store=True)

    @api.depends('omc1','eln_ref','grade')
    def _compute_omc1_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.omc1_conformity = 'na'
                continue
            record.omc1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be3e26bd-d2ce-413b-b58a-42b5f843126d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be3e26bd-d2ce-413b-b58a-42b5f843126d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.omc1 - record.omc1*mu_value
                    upper = record.omc1 + record.omc1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.omc1_conformity = 'pass'
                        break
                    else:
                        record.omc1_conformity = 'fail'

    omc1_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_omc1_nabl", store=True)

    @api.depends('omc1','eln_ref','grade')
    def _compute_omc1_nabl(self):
        
        for record in self:
            record.omc1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be3e26bd-d2ce-413b-b58a-42b5f843126d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be3e26bd-d2ce-413b-b58a-42b5f843126d')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.omc1 - record.omc1*mu_value
            upper = record.omc1 + record.omc1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.omc1_nabl = 'pass'
                break
            else:
                record.omc1_nabl = 'fail'



    omc1_report_type = fields.Selection([
        ('auto', 'Auto'),
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
    
    omc1_final_report = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),], compute="_compute_omc1_final_report", store=True)
    
    @api.depends('omc1_nabl', 'omc1_report_type')
    def _compute_omc1_final_report(self):
        for rec in self:
    
            # Manual override
            if rec.omc1_report_type == 'nabl':
                rec.omc1_final_report = 'nabl'
    
            elif rec.omc1_report_type == 'non_nabl':
                rec.omc1_final_report = 'non_nabl'
    
            # Automatic
            else:
                if rec.omc1_nabl == 'pass':
                    rec.omc1_final_report = 'nabl'
                else:
                    rec.omc1_final_report = 'non_nabl'

    
    graph_image_density1 = fields.Binary("Line Chart", compute="_compute_graph_image_density_omc_light1", store=True)

    show_light_graph = fields.Boolean(string="Show Compaction Graph")




    # def generate_line_chart_light_omc1(self):

    #  x_value = []
    #  y_value = []

    #  for line in self.omc_table:
    #     if line.water_content1 and line.dry_density1:
    #         x_value.append(float(line.water_content1))
    #         y_value.append(float(line.dry_density1))

    #  if len(x_value) < 3:
    #     return False

    # # Sort data
    #  data = sorted(zip(x_value, y_value))
    #  x = np.array([d[0] for d in data])
    #  y = np.array([d[1] for d in data])

    # # ==========================
    # # Quadratic Compaction Curve
    # # ==========================
    #  coeff = np.polyfit(x, y, 2)
    #  poly = np.poly1d(coeff)

    #  x_smooth = np.linspace(x.min(), x.max(), 500)
    #  y_smooth = poly(x_smooth)

    # # OMC / MDD
    #  omc = -coeff[1] / (2 * coeff[0])
    #  mdd = poly(omc)

    #  plt.figure(figsize=(15, 5))

    # # Smooth blue curve
    #  plt.plot(
    #     x_smooth,
    #     y_smooth,
    #     color='blue',
    #     linewidth=2.5
    # )

    # # Show points ON CURVE only
    #  y_curve_points = poly(x)
  
    #  plt.scatter(
    #     x,
    #     y_curve_points,
    #     color='red',
    #     edgecolors='none',
    #     s=40,
    #     zorder=5
    # )

    # # Peak point
    #  plt.scatter(
    #     omc,
    #     mdd,
    #     color='red',
    #     s=120,
    #     zorder=10
    # )

    # # OMC / MDD guide lines
    #  plt.axhline(
    #     y=mdd,
    #     color='red',
    #     linestyle='--',
    #     linewidth=1
    # )

    #  plt.axvline(
    #     x=omc,
    #     color='red',
    #     linestyle='--',
    #     linewidth=1
    # )

    # # Annotation
    #  plt.text(
    #     omc + 0.2,
    #     mdd + 0.002,
    #     f"OMC: {omc:.2f}%\nMDD: {mdd:.2f}",
    #     color='red',
    #     fontsize=11,
    #     fontweight='bold'
    # )

    # # Labels
    #  plt.xlabel(
    #     'Water Content (%)',
    #     fontsize=12
    # )

    #  plt.ylabel(
    #     'Dry Density (g/cc)',
    #     fontsize=12
    # )

    #  plt.title(
    #     'DETERMINATION OF COMPACTION OMC / MDD',
    #     fontsize=16
    # )

    # # Limits
    #  plt.xlim(
    #     left=0,
    #     right=max(x) + 2
    # )

    #  plt.ylim(
    #     bottom=min(y) - 0.03,
    #     top=max(y_smooth) + 0.03
    # )

    # # ==========================
    # # Graph Paper Background
    # # ==========================
    #  ax = plt.gca()

    # # X-axis grid
    #  ax.xaxis.set_major_locator(MultipleLocator(1))
    #  ax.xaxis.set_minor_locator(MultipleLocator(0.1))

    # # Y-axis grid
    #  ax.yaxis.set_major_locator(MultipleLocator(0.05))
    #  ax.yaxis.set_minor_locator(MultipleLocator(0.001))

    # # Major Grid
    #  plt.grid(
    #     which='major',
    #     color='green',
    #     linestyle='-',
    #     linewidth=0.5,
    #     alpha=0.55
    # )

    # # Minor Grid
    #  plt.grid(
    #     which='minor',
    #     color='green',
    #     linestyle=':',
    #     linewidth=0.3,
    #     alpha=0.45
    # )

    #  plt.tight_layout()

    # # Save Image
    #  buffer = io.BytesIO()

    #  plt.savefig(
    #     buffer,
    #     format='png',
    #     dpi=150,
    #     bbox_inches='tight'
    # )

    #  plt.close()

    #  buffer.seek(0)

    #  return base64.b64encode(
    #     buffer.read()
    # ).decode('utf-8')

  


    # def generate_line_chart_light_omc1(self):

    #    x = []
    #    y = []

    #    for line in self.omc_table:
    #       if line.water_content1 and line.dry_density1:
    #         x.append(float(line.water_content1))
    #         y.append(float(line.dry_density1))

    #    if len(x) < 3:
    #        return False

    # # -------------------------
    # # Sort Data
    # # -------------------------
    #    data = sorted(zip(x, y))
    #    x = np.array([i[0] for i in data])
    #    y = np.array([i[1] for i in data])

    #    omc = float(self.omc1)
    #    mdd = float(self.max_dry_density1)

    # # ------------------------------------------------
    # # Calculate parabola passing through:
    # #   1. First data point
    # #   2. Vertex (OMC, MDD)
    # # ------------------------------------------------

    #    x1 = x[0]
    #    y1 = y[0]

    # # Prevent division by zero
    #    if abs(x1 - omc) < 1e-6:
    #        x1 = x[1]
    #        y1 = y[1]

    #    a = (y1 - mdd) / ((x1 - omc) ** 2)

    #    def compaction_curve(x):
    #        return a * (x - omc) ** 2 + mdd

    #    x_smooth = np.linspace(x.min(), x.max(), 500)
    #    y_smooth = compaction_curve(x_smooth)

    # # -------------------------
    # # Plot
    # # -------------------------
    #    plt.figure(figsize=(15, 5))

    #    plt.plot(
    #     x_smooth,
    #     y_smooth,
    #     color="blue",
    #     linewidth=2.8,
    # )

    #    plt.scatter(
    #     x,
    #     y,
    #     color="red",
    #     s=45,
    #     zorder=5,
    # )

    #    plt.scatter(
    #     omc,
    #     mdd,
    #     color="red",
    #     s=150,
    #     zorder=10,
    # )

    #    plt.axhline(
    #     y=mdd,
    #     color="red",
    #     linestyle="--",
    #     linewidth=1,
    # )

    #    plt.axvline(
    #     x=omc,
    #     color="red",
    #     linestyle="--",
    #     linewidth=1,
    # )

    #    plt.text(
    #     omc + 0.15,
    #     mdd + 0.002,
    #     f"OMC: {omc:.2f}%\nMDD: {mdd:.2f}",
    #     fontsize=12,
    #     color="red",
    #     fontweight="bold",
    # )

    #    plt.xlabel(
    #     "Water Content (%)",
    #     fontsize=16,
    # )

    #    plt.ylabel(
    #     "Dry Density (g/cc)",
    #     fontsize=16,
    # )

    #    plt.title(
    #     "DETERMINATION OF COMPACTION OMC / MDD",
    #     fontsize=22,
    # )

    #    plt.xlim(0, max(x) + 2)
    #    plt.ylim(min(y) - 0.04, max(mdd, max(y)) + 0.03)

    # # -------------------------
    # # Graph paper background
    # # -------------------------
    #    ax = plt.gca()

    #    ax.set_facecolor("#f8fff8")

    #    ax.xaxis.set_major_locator(MultipleLocator(1))
    #    ax.xaxis.set_minor_locator(MultipleLocator(0.1))

    #    ax.yaxis.set_major_locator(MultipleLocator(0.05))
    #    ax.yaxis.set_minor_locator(MultipleLocator(0.005))

    #    ax.grid(
    #     which="major",
    #     color="green",
    #     linewidth=0.5,
    #     alpha=0.45,
    # )

    #    ax.grid(
    #     which="minor",
    #     color="green",
    #     linestyle=":",
    #     linewidth=0.3,
    #     alpha=0.35,
    # )

    #    plt.tight_layout()

    #    buffer = io.BytesIO()

    #    plt.savefig(
    #     buffer,
    #     format="png",
    #     dpi=100,
    #     bbox_inches="tight",
    # )

    #    plt.close()

    #    buffer.seek(0)

    #    return base64.b64encode(buffer.read()).decode("utf-8")


    def generate_line_chart_light_omc1(self):


      x = []
      y = []

      for line in self.omc_table:
        if line.water_content1 and line.dry_density1:
            x.append(float(line.water_content1))
            y.append(float(line.dry_density1))

      if len(x) < 3:
        return False

    # ---------------------------------------
    # Sort data
    # ---------------------------------------
      data = sorted(zip(x, y))
      x = np.array([i[0] for i in data], dtype=float)
      y = np.array([i[1] for i in data], dtype=float)

      omc = float(self.omc1)
      mdd = float(self.max_dry_density1)

    # ---------------------------------------
    # Create parabola through:
    # First Point
    # OMC/MDD
    # Last Point
    # ---------------------------------------

      x1 = x[0]
      y1 = y[0]

      x2 = omc
      y2 = mdd

      x3 = x[-1]
      y3 = y[-1]

      A = np.array([
        [x1**2, x1, 1],
        [x2**2, x2, 1],
        [x3**2, x3, 1]
    ], dtype=float)

      B = np.array([
        y1,
        y2,
        y3
    ], dtype=float)

      a, b, c = np.linalg.solve(A, B)

      def curve(xx):
          return a * xx**2 + b * xx + c

      x_smooth = np.linspace(x1, x3, 500)
      y_smooth = curve(x_smooth)

    # ---------------------------------------
    # Plot
    # ---------------------------------------

      plt.figure(figsize=(15, 5))

      plt.plot(
        x_smooth,
        y_smooth,
        color="blue",
        linewidth=2.8,
        zorder=2
    )

      plt.scatter(
        x,
        y,
        color="red",
        s=45,
        zorder=5
    )

      plt.scatter(
        omc,
        mdd,
        color="red",
        s=160,
        zorder=10
    )

      plt.axhline(
        y=mdd,
        color="red",
        linestyle="--",
        linewidth=1
    )

      plt.axvline(
        x=omc,
        color="red",
        linestyle="--",
        linewidth=1
    )

      plt.text(
        omc + 0.15,
        mdd + 0.002,
        f"OMC: {omc:.2f}%\nMDD: {mdd:.2f}",
        fontsize=12,
        color="red",
        fontweight="bold"
    )

      plt.xlabel(
        "Water Content (%)",
        fontsize=16
    )

      plt.ylabel(
        "Dry Density (g/cc)",
        fontsize=16
    )

      plt.title(
        "DETERMINATION OF COMPACTION OMC / MDD",
        fontsize=22
    )

      plt.xlim(0, max(x) + 2)

      ymin = min(min(y), min(y_smooth))
      ymax = max(max(y), max(y_smooth), mdd)

      plt.ylim(
        ymin - 0.02,
        ymax + 0.03
    )

        # ---------------------------------------
    # Graph paper background
    # ---------------------------------------

      ax = plt.gca()

      ax.set_facecolor("#f8fff8")

      ax.xaxis.set_major_locator(MultipleLocator(1))
      ax.xaxis.set_minor_locator(MultipleLocator(0.1))

      ax.yaxis.set_major_locator(MultipleLocator(0.05))
      ax.yaxis.set_minor_locator(MultipleLocator(0.005))

      ax.grid(
        which="major",
        color="green",
        linewidth=0.5,
        alpha=0.45
    )

      ax.grid(
        which="minor",
        color="green",
        linestyle=":",
        linewidth=0.3,
        alpha=0.35
    )

    # Make border thicker
      for spine in ax.spines.values():
        spine.set_linewidth(1.2)

      plt.tight_layout()

    # ---------------------------------------
    # Save Image
    # ---------------------------------------

      buffer = io.BytesIO()

      plt.savefig(
        buffer,
        format="png",
        dpi=100,
        bbox_inches="tight"
    )

      plt.close()

      buffer.seek(0)

      return base64.b64encode(
        buffer.read()
    ).decode("utf-8")




    # @api.depends('omc_table')
    # def _compute_graph_image_density_omc_light1(self):
    #     try:
    #         for record in self:
    #             chart_image_light_omc1 = record.generate_line_chart_light_omc1()
    #             record.graph_image_density1 = chart_image_light_omc1
    #     except:
    #         pass 


    @api.depends('omc_table')
    def _compute_graph_image_density_omc_light1(self):
     for record in self:
        record.graph_image_density1 = record.generate_line_chart_light_omc1()



    # Compressive Strength Of Pavement Quality Concrete (PQC) 
    
    comp_strength_name = fields.Char("Name",default="Compressive Strength")
    comp_strength_visible = fields.Boolean("Compressive Strength Visible",compute="_compute_visible")

    comp_strength_line_ids = fields.One2many(
        'dlc.compressive.strength.line',
        'parent_id',
        string="Compressive Strength "
    )

    comp_size_cube = fields.Selection([
    ('150 x 150 x 150', '150 x 150 x 150'),], string="Size of Cube")

    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")
    date_of_testing = fields.Date(string="Date of Testing",compute="_compute_date_testing")



    @api.depends('eln_ref')
    def _compute_date_testing(self):
        if self.eln_ref:
            self.date_of_testing = self.eln_ref.date_testing
        else:
            self.date_of_testing = ''
            

    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None


    def action_calculate_avg_strength(self):
        for rec in self:
            lines = rec.comp_strength_line_ids.sorted(key=lambda l: l.sr_no)  
            group_size = 3

            for i in range(0, len(lines), group_size):
                group = lines[i:i + group_size]
                strengths = [l.compressive_strength for l in group if l.compressive_strength > 0]
                avg = sum(strengths) / len(strengths) if strengths else 0.0

                if group:
                    group[0].avg_compressive_strength = avg

            for line in lines:
                if line not in [lines[i] for i in range(0, len(lines), group_size)]:
                    line.avg_compressive_strength = 0.0


    avg_7_comp_strength = fields.Float(string="Max 7 Compressive Strength (MPa)",compute="_compute_max_strength",
    store=True,)

    avg_28_comp_strength = fields.Float(string="Max 28 Compressive Strength (MPa)",compute="_compute_max_strength",
    store=True,)

    

    @api.depends('comp_strength_line_ids.avg_compressive_strength',
             'comp_strength_line_ids.days')
    def _compute_max_strength(self):
     for rec in self:
        strength_7 = rec.comp_strength_line_ids.filtered(
            lambda l: l.days == '7'
        ).mapped('avg_compressive_strength')

        strength_28 = rec.comp_strength_line_ids.filtered(
            lambda l: l.days == '28'
        ).mapped('avg_compressive_strength')

        rec.avg_7_comp_strength = max(strength_7) if strength_7 else 0.0
        rec.avg_28_comp_strength = max(strength_28) if strength_28 else 0.0



    avg_7_comp_strength_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_7_comp_strength_conformity", store=True)

    @api.depends('avg_7_comp_strength','eln_ref','grade')
    def _compute_avg_7_comp_strength_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_7_comp_strength_conformity = 'na'
                continue
            record.avg_7_comp_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','63fcbd8d-236f-46c8-adfc-c4ede442f32f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','63fcbd8d-236f-46c8-adfc-c4ede442f32f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_7_comp_strength - record.avg_7_comp_strength*mu_value
                    upper = record.avg_7_comp_strength + record.avg_7_comp_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_7_comp_strength_conformity = 'pass'
                        break
                    else:
                        record.avg_7_comp_strength_conformity = 'fail'

    avg_7_comp_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_7_comp_strength_nabl", store=True)

    @api.depends('avg_7_comp_strength','eln_ref','grade')
    def _compute_avg_7_comp_strength_nabl(self):
        
        for record in self:
            record.avg_7_comp_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','63fcbd8d-236f-46c8-adfc-c4ede442f32f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','63fcbd8d-236f-46c8-adfc-c4ede442f32f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_7_comp_strength - record.avg_7_comp_strength*mu_value
                    upper = record.avg_7_comp_strength + record.avg_7_comp_strength*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_7_comp_strength_nabl = 'pass'
                        break
                    else:
                        record.avg_7_comp_strength_nabl = 'fail'


    avg_7_comp_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_7_comp_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_7_comp_final_report", store=True)

    @api.depends('avg_7_comp_strength_nabl', 'avg_7_comp_report_type')
    def _compute_avg_7_comp_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_7_comp_report_type == 'nabl':
            rec.avg_7_comp_final_report = 'nabl'

        elif rec.avg_7_comp_report_type == 'non_nabl':
            rec.avg_7_comp_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_7_comp_strength_nabl == 'pass':
                rec.avg_7_comp_final_report = 'nabl'
            else:
                rec.avg_7_comp_final_report = 'non_nabl'


    avg_28_comp_strength_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_28_comp_strength_conformity", store=True)

    @api.depends('avg_28_comp_strength','eln_ref','grade')
    def _compute_avg_28_comp_strength_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_28_comp_strength_conformity = 'na'
                continue
            record.avg_28_comp_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0c84c06c-b2ce-422a-9b11-79073955c2c2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0c84c06c-b2ce-422a-9b11-79073955c2c2')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_28_comp_strength - record.avg_28_comp_strength*mu_value
                    upper = record.avg_28_comp_strength + record.avg_28_comp_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_28_comp_strength_conformity = 'pass'
                        break
                    else:
                        record.avg_28_comp_strength_conformity = 'fail'

    avg_28_comp_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_28_comp_strength_nabl", store=True)

    @api.depends('avg_28_comp_strength','eln_ref','grade')
    def _compute_avg_28_comp_strength_nabl(self):
        
        for record in self:
            record.avg_28_comp_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0c84c06c-b2ce-422a-9b11-79073955c2c2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0c84c06c-b2ce-422a-9b11-79073955c2c2')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_28_comp_strength - record.avg_28_comp_strength*mu_value
                    upper = record.avg_28_comp_strength + record.avg_28_comp_strength*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_28_comp_strength_nabl = 'pass'
                        break
                    else:
                        record.avg_28_comp_strength_nabl = 'fail'


    avg_28_comp_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_28_comp_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_28_comp_final_report", store=True)

    @api.depends('avg_28_comp_strength_nabl', 'avg_28_comp_report_type')
    def _compute_avg_28_comp_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_28_comp_report_type == 'nabl':
            rec.avg_28_comp_final_report = 'nabl'

        elif rec.avg_28_comp_report_type == 'non_nabl':
            rec.avg_28_comp_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_28_comp_strength_nabl == 'pass':
                rec.avg_28_comp_final_report = 'nabl'
            else:
                rec.avg_28_comp_final_report = 'non_nabl'




    


    
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            
            record.elongation_fl_visible = False
            record.impact_visible = False
            record.water_absorbtion_visible  = False
            record.soundness_na2so4_visible = False
            record.soundness_mgso4_visible = False
            record.dry_gradation_visible = False
            record.heavy_visible = False
            record.omc_visible = False
            record.comp_strength_visible = False

            


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                
                if sample.internal_id == '3245a108-16bd-457a-961a-2698a91ff0c6':
                    record.elongation_fl_visible = True

                if sample.internal_id == '4db01f03-8c95-47dc-8a22-664ce4473864':
                    record.impact_visible = True

                

                if sample.internal_id == '3a4a23f3-aff8-4a87-8ce9-19641ea88d75':
                    record.water_absorbtion_visible  = True


                if sample.internal_id == '0782fd41-b852-424a-92ed-7c91935df3bd':
                    record.soundness_na2so4_visible = True


                if sample.internal_id == 'f50ffb5e-99a5-437f-b9b0-9e1e4c7d7e72':
                    record.soundness_mgso4_visible = True



                if sample.internal_id == '630fe87a-24e6-4eed-9f8f-3a4f901df10d':
                    record.dry_gradation_visible = True


                

                if sample.internal_id == '411f6642-0ef2-4242-9410-bef505035c7e':
                    record.heavy_visible = True

                if sample.internal_id == 'be3e26bd-d2ce-413b-b58a-42b5f843126d':
                    record.omc_visible = True

                if sample.internal_id == '7764a958-f88c-4141-b7c4-131dc572103d':
                    record.comp_strength_visible = True
                
                


             

              


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:


            

            # Elongation
            if result.parameter.internal_id == '3245a108-16bd-457a-961a-2698a91ff0c6':
                result.calculated = True

            # Flakiness
            if result.parameter.internal_id == 'c79b6bab-8c9f-41cb-a568-8c044629d898':
                result.calculated = True

            
            # impact value 
            if result.parameter.internal_id == '4db01f03-8c95-47dc-8a22-664ce4473864':
                result.calculated = True
                result.result_char = round(self.average_impact_value,2)
                if self.average_impact_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            

            # specific gravity 
            if result.parameter.internal_id == '3033da6d-4e25-4208-8df9-2de3f4ab0a8c':
                result.calculated = True
                result.result_char = round(self.avg_specific_gravity,2)
                if self.avg_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # water absorbtion
            if result.parameter.internal_id == '3a4a23f3-aff8-4a87-8ce9-19641ea88d75':
                result.calculated = True
                result.result_char = round(self.avg_water_absorption,2)
                if self.avg_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 


            

            # Soundness - Na2SO4
            if result.parameter.internal_id == '0782fd41-b852-424a-92ed-7c91935df3bd':
                result.calculated = True
                result.result_char = round(self.total_weighted_avg,2)
                if self.total_weighted_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Soundness - MgSO4
            if result.parameter.internal_id == 'f50ffb5e-99a5-437f-b9b0-9e1e4c7d7e72':
                result.calculated = True
                result.result_char = round(self.mag_total_weighted_avg,2)
                if self.mag_total_weighted_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Dry Gradation
            if result.parameter.internal_id == '630fe87a-24e6-4eed-9f8f-3a4f901df10d':
                result.calculated = True

            
            

            # Heavy Visible
            if result.parameter.internal_id == '411f6642-0ef2-4242-9410-bef505035c7e':
                result.calculated = True
                result.result_char = round(self.max_dry_density,2)
                if self.max_dry_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Heavy Visible
            if result.parameter.internal_id == '95af7fbd-ba6d-46ec-b51f-02b4813fd56e':
                result.calculated = True
                result.result_char = round(self.omc,2)
                if self.omc_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # OMC
            if result.parameter.internal_id == '37ac17a7-840e-412a-99f8-bb98687318f2':
                result.calculated = True
                result.result_char = round(self.max_dry_density1,2)
                if self.max_dry_density1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # OMC
            if result.parameter.internal_id == 'be3e26bd-d2ce-413b-b58a-42b5f843126d':
                result.calculated = True
                result.result_char = round(self.omc1,2)
                if self.omc1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Compressive Strength 
            if result.parameter.internal_id == '7764a958-f88c-4141-b7c4-131dc572103d':
                result.calculated = True

            # 7 Days Compressive Strength 
            if result.parameter.internal_id == '63fcbd8d-236f-46c8-adfc-c4ede442f32f':
                result.calculated = True
                result.result_char = round(self.avg_7_comp_strength,2)
                if self.avg_7_comp_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 28 Days Compressive Strength 
            if result.parameter.internal_id == '0c84c06c-b2ce-422a-9b11-79073955c2c2':
                result.calculated = True
                result.result_char = round(self.avg_28_comp_strength,2)
                if self.avg_28_comp_strength_nabl == 'pass':
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
        record = super(DLCMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    def get_all_fields(self):
        record = self.env['mechanical.dlc'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

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


    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    

    


    notes_id = fields.One2many('mechanical.dlc.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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
    





class DLCElongationLine(models.Model):
    _name = "dlc.elongation.flakiness.line"
    parent_id = fields.Many2one('mechanical.dlc',string="Parent Id")

    passing_sieve = fields.Float("Passing IS Sieve (mm)")
    retained_sieve = fields.Float("Retained IS Sieve (mm)")

    total_weight = fields.Float("Total Wt of Aggregate Retained (gm)")
    wt_passing_flakiness = fields.Float("Wt Passing Flakiness Gauge (gm)")
    wt_retained_flakiness = fields.Float("Wt. Retained on Flakiness gauge (gm) = [(Total Wt of aggregate Retained (gm)) - (Wt. Passing on Flakiness gauge (gm)]",compute="_compute_wt_retained_flakiness",store=True,)
    wt_retained_elongation = fields.Float("Wt Retained Elongation Gauge (gm)")

    @api.depends("total_weight", "wt_passing_flakiness")
    def _compute_wt_retained_flakiness(self):
        for rec in self:
            rec.wt_retained_flakiness = (
                rec.total_weight - rec.wt_passing_flakiness
            )



class DLCImpactValueLine(models.Model):
    _name = "dlc.impact.line"
    parent_id = fields.Many2one('mechanical.dlc', string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)
    w1 = fields.Float("Weight of surface dry sample passing 12.5mm and retained on 10mm IS sieves, W1. (gm)")
    w2 = fields.Float("Weight of fraction passing 2.36mm sieve after the test, W2. (gm) ")
    w3 = fields.Float("Weight of fraction retained on 2.36mm sieve after the test, W3 = [ (Weight of surface dry sample passing 12.5mm and retained on 10mm IS sieves, W1) - ( Weight of fraction passing2.36mm sieve after the test, W2)")

    w4 = fields.Float(
        string="W4 = W1 - (W2 + W3)	(gm)",
        compute="_compute_values",
        store=True
    )

    impact_value = fields.Float(
        string="Aggregate Impact Value (A.I.V) = (W2/W1) x 100	 (%)",
        compute="_compute_values",
        store=True
    )

    @api.depends('w1', 'w2', 'w3')
    def _compute_values(self):
        for rec in self:
            rec.w4 = rec.w1 - (rec.w2 + rec.w3)

            if rec.w1:
                rec.impact_value = (rec.w2 / rec.w1) * 100
            else:
                rec.impact_value = 0.0




    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(DLCImpactValueLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1




class DLCSpecificGravityWaterAbsorptionLine(models.Model):
    _name = "dlc.specific.gravity.water.absorption.line"
    _description = "Specific Gravity And Water Absorption Test"

    parent_id = fields.Many2one('mechanical.dlc', string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)

    # Input fields
    w1 = fields.Float("Weight of Saturated Aggregates + Basket in Water (W1) (gm)")
    w2 = fields.Float("Weight of Basket in Water (W2) (gm)")
    w3 = fields.Float("Weight of Saturated Surface Dry Aggregates in Air (W3) (gm)")
    w4 = fields.Float("Weight of Oven Dry Aggregates in Air (W4) (gm)")

    # Output fields
    specific_gravity = fields.Float("Specific Gravity", compute="_compute_values", store=True)
    apparent_specific_gravity = fields.Float("Apparent Specific Gravity", compute="_compute_values", store=True)
    water_absorption = fields.Float("Water Absorption (%)", compute="_compute_values", store=True)

    @api.depends('w1', 'w2', 'w3', 'w4')
    def _compute_values(self):
        for rec in self:
            try:
                denominator = rec.w3 - (rec.w1 - rec.w2)
                apparent_denominator = rec.w4 - (rec.w1 - rec.w2)

                # Specific Gravity
                rec.specific_gravity = rec.w4 / denominator if denominator else 0.0

                # Apparent Specific Gravity
                rec.apparent_specific_gravity = rec.w4 / apparent_denominator if apparent_denominator else 0.0

                # Water Absorption %
                rec.water_absorption = ((rec.w3 - rec.w4) / rec.w4) * 100 if rec.w4 else 0.0

            except Exception:
                rec.specific_gravity = 0.0
                rec.apparent_specific_gravity = 0.0
                rec.water_absorption = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(DLCSpecificGravityWaterAbsorptionLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1





class DLCSodiumSulphateLine(models.Model):
    _name = "dlc.sodium.sulphate.line"
    parent_id = fields.Many2one('mechanical.dlc', string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size")
    retained_sieve = fields.Char("Retained Sieve Size")

    grading_percent = fields.Float("Grading of Original Sample (%)")

    weight_before = fields.Float("Weight Before Test (gm)")
    weight_after = fields.Float("Weight After Test (gm)")

    percent_loss = fields.Float(
        "Percent Loss",
        compute="_compute_loss",
        store=True
    )

    weighted_avg = fields.Float(
        "Weighted Average",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before:
            rec.percent_loss = (
                (rec.weight_after / rec.weight_before)
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


class DLCSodiumSulphateTwoLine(models.Model):
    _name = "dlc.sodium.sulphate.two.line"
    parent_id = fields.Many2one('mechanical.dlc', string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size" )
    retained_sieve = fields.Char("Retained Sieve Size" )

    grading_percent = fields.Float("Grading of Original Sample (%)")

    weight_before = fields.Float("Weight of Test Fraction Before Test (gm)")
    weight_after = fields.Float("Weight of Test Fraction After Test (gm)")

    percent_loss = fields.Float(
        "Percentage Passing Finer Sieve After Test (Actual Percentage Loss)",
        compute="_compute_loss",
        store=True
    )

    weighted_avg = fields.Float(
        "Weighted Average  (Corrected Percent Loss)",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before:
            rec.percent_loss = (
                (rec.weight_after / rec.weight_before)
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


class DLCMagnesiumSulphateLine(models.Model):
    _name = "dlc.magnesium.sulphate.line"
    parent_id = fields.Many2one('mechanical.dlc', string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size")
    retained_sieve = fields.Char("Retained Sieve Size")

    grading_percent = fields.Float("Grading of Original Sample (%)")

    weight_before = fields.Float("Weight Before Test (gm)")
    weight_after = fields.Float("Weight After Test (gm)")

    percent_loss = fields.Float(
        "Percent Loss",
        compute="_compute_loss",
        store=True
    )

    weighted_avg = fields.Float(
        "Weighted Average",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before:
            rec.percent_loss = (
                (rec.weight_after / rec.weight_before)
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


class DLCMagnesiumSulphateTwoLine(models.Model):
    _name = "dlc.magnesium.sulphate.two.line"
    parent_id = fields.Many2one('mechanical.dlc', string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size" )
    retained_sieve = fields.Char("Retained Sieve Size" )

    grading_percent = fields.Float("Grading of Original Sample (%)")

    weight_before = fields.Float("Weight of Test Fraction Before Test (gm)")
    weight_after = fields.Float("Weight of Test Fraction After Test (gm)")

    percent_loss = fields.Float(
        "Percentage Passing Finer Sieve After Test (Actual Percentage Loss)",compute="_compute_loss",store=True)

    weighted_avg = fields.Float(
        "Weighted Average  (Corrected Percent Loss)",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before:
            rec.percent_loss = (
                (rec.weight_after / rec.weight_before)
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100







class DLCDryGradationLine(models.Model):
    _name = "dlc.dry.gradation.line"
    parent_id = fields.Many2one('mechanical.dlc', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)



    sieve_size = fields.Char(string="IS Sieve Size mm")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    cumulative_percent = fields.Float(string="Cum. Weight Retained (gm)",compute="_compute_cumulative_percent",
    store=True,)
    percent_retained = fields.Float(string='% of Weight Retained', compute="_compute_percent_retained",digits=(16,2))
    cumulative_retained = fields.Float(string="% of Cumulative Wt. Retained ", store=True,digits=(16,2))
    passing_percent = fields.Float(string="% of wt passing",digits=(16,2))
    specific_limits = fields.Char(string="Specified Limits",store=True)



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(DLCDryGradationLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

    def write(self, vals):
        # Handle row deletions and adjust serial numbers
        if 'parent_id' in vals or 'wt_retained' in vals:
            for record in self:
                if record.parent_id and record.parent_id == vals.get('parent_id') and 'wt_retained' in vals:
                    record.percent_retained = vals['wt_retained'] / record.parent_id.total * 100 if record.parent_id.total else 0

            new_self = super(DLCDryGradationLine, self).write(vals)
            if 'wt_retained' in vals:
                for record in self:
                    # record.parent_id._compute_total()
                    pass
            return new_self
        return super(DLCDryGradationLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id
        res = super(DLCDryGradationLine, self).unlink()
        if parent_id:
            parent_id.sieve_analysis_child_lines._reorder_serial_numbers()
        return res

    @api.depends('wt_retained', 'parent_id.weight_of_sample')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = (record.wt_retained / self.parent_id.weight_of_sample) * 100
            except ZeroDivisionError:
                record.percent_retained = 0

    @api.depends('wt_retained', 'parent_id.sieve_analysis_child_lines.wt_retained')
    def _compute_cumulative_percent(self):
        for parent in self.mapped('parent_id'):
            total = 0
            lines = parent.sieve_analysis_child_lines.sorted('serial_no')

            for line in lines:
                total += line.wt_retained or 0
                line.cumulative_percent = total


    @api.depends('cumulative_retained')
    def _compute_cum_retained(self):
        self.cumulative_retained=0
        

    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines, key=lambda r: r.id)





class DLCHEAVYCOMPACTIONLINE(models.Model):
    _name = "dlc.heavy.compaction.line"
    parent_id = fields.Many2one('mechanical.dlc', string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    wet_soil_mould = fields.Float(string="Wt. of Wet Soil + Mould")

    wet_soil = fields.Float(
        string="Wt. of Wet Soil (E)",
        compute="_compute_values",
        store=True,
    )

    wet_density = fields.Float(
        string="Wet Density (F)",
        compute="_compute_values",
        store=True,
    )

    container_no = fields.Float(string="Container No.")

    container_weight = fields.Float(string="Wt. of Container (H)")

    wet_soil_container = fields.Float(string="Wt. of Wet Soil + Container (I)")

    dry_soil_container = fields.Float(string="Wt. of Dry Soil + Container (J)")

    water_weight = fields.Float(
        string="Wt. of Water (K)",
        compute="_compute_values",
        store=True,
    )

    dry_soil = fields.Float(
        string="Wt. of Dry Soil (L)",
        compute="_compute_values",
        store=True,
    )

    water_content = fields.Float(
        string="Water Content (%)",
        compute="_compute_values",
        store=True,
    )

    dry_density = fields.Float(
        string="Dry Density",
        compute="_compute_values",
        store=True,
    )

    @api.depends(
    'wet_soil_mould',
    'container_weight',
    'wet_soil_container',
    'dry_soil_container',
    'parent_id.heavy_mould_weight',
    'parent_id.heavy_mould_volume',
)
    def _compute_values(self):
     for rec in self:

        # E
        rec.wet_soil = rec.wet_soil_mould - (rec.parent_id.heavy_mould_weight or 0.0)

        # F
        volume = rec.parent_id.heavy_mould_volume or 0.0
        rec.wet_density = rec.wet_soil / volume if volume else 0.0

        # K
        rec.water_weight = rec.wet_soil_container - rec.dry_soil_container

        # L
        rec.dry_soil = rec.dry_soil_container - rec.container_weight

        # M
        rec.water_content = (
            (100 * rec.water_weight / rec.dry_soil)
            if rec.dry_soil else 0.0
        )

        # N
        rec.dry_density = (
            (100 * rec.wet_density / (100 + rec.water_content))
            if (100 + rec.water_content) else 0.0)


  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(DLCHEAVYCOMPACTIONLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class DLCLIGHTCOMPACTIONLINE(models.Model):
    _name = "dlc.omc.compaction.line"
    parent_id = fields.Many2one('mechanical.dlc', string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    wet_soil_mould = fields.Float(string="Wt. of Wet Soil + Mould")

    wet_soil = fields.Float(
        string="Wt. of Wet Soil (E)",
        compute="_compute_values",
        store=True,
    )

    wet_density = fields.Float(
        string="Wet Density (F)",
        compute="_compute_values",
        store=True,
    )

    container_no = fields.Float(string="Container No.")

    container_weight = fields.Float(string="Wt. of Container (H)")

    wet_soil_container = fields.Float(string="Wt. of Wet Soil + Container (I)")

    dry_soil_container = fields.Float(string="Wt. of Dry Soil + Container (J)")

    water_weight = fields.Float(
        string="Wt. of Water (K)",
        compute="_compute_values",
        store=True,
    )

    dry_soil = fields.Float(
        string="Wt. of Dry Soil (L)",
        compute="_compute_values",
        store=True,
    )

    water_content1 = fields.Float(
        string="Water Content (%)",
        compute="_compute_values",
        store=True,
    )

    dry_density1 = fields.Float(
        string="Dry Density",
        compute="_compute_values",
        store=True,
    )

    @api.depends(
    'wet_soil_mould',
    'container_weight',
    'wet_soil_container',
    'dry_soil_container',
    'parent_id.light_mould_weight',
    'parent_id.light_mould_volume',
)
    def _compute_values(self):
     for rec in self:

        # E
        rec.wet_soil = rec.wet_soil_mould - (rec.parent_id.light_mould_weight or 0.0)

        # F
        volume = rec.parent_id.light_mould_volume or 0.0
        rec.wet_density = rec.wet_soil / volume if volume else 0.0

        # K
        rec.water_weight = rec.wet_soil_container - rec.dry_soil_container

        # L
        rec.dry_soil = rec.dry_soil_container - rec.container_weight

        # M
        rec.water_content1 = (
            (100 * rec.water_weight / rec.dry_soil)
            if rec.dry_soil else 0.0
        )

        # N
        rec.dry_density1 = (
            (100 * rec.wet_density / (100 + rec.water_content1))
            if (100 + rec.water_content1) else 0.0
        )

  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(DLCLIGHTCOMPACTIONLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class DLCCompressiveStrengthLine(models.Model):
    _name = "dlc.compressive.strength.line"
    parent_id = fields.Many2one('mechanical.dlc', string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.",readonly=True, copy=False, default=1)
  
    id_mark = fields.Char(string="Cube Identification No.",store=True)
    wt_sample = fields.Float(string="Weight (gms)",digits=(16,1))

    dt_of_casting = fields.Date(string="Date of casting",compute="_compute_dt_of_casting",store=True)

    # days = fields.Integer(string="No.of Days",compute="_compute_days",store=True)

    days = fields.Selection([
    ('7', '7 DAYS'),
    ('28', '28 DAYS'),], string="Age", required=True)

    dt_of_testing1 = fields.Date(string="Date of Testing",compute="_compute_dt_of_testing",store=True)

    load = fields.Float(string="Load (KN)")
    compressive_strength = fields.Float(string="Compressive Strength (MPa)",compute="_compute_strength",store=True)

    avg_compressive_strength = fields.Float(string="Avg. Compressive Strength (MPa)")

    

    dimension = fields.Char(string="Size of cube (mm)",compute="_compute_dimension",store=True)

    density = fields.Float(string="Density (gms/cc)",compute="_compute_density",store=True,digits=(16,3))



    @api.depends('parent_id.comp_size_cube') 
    def _compute_dimension(self):
        for rec in self:
            rec.dimension = rec.parent_id.comp_size_cube
            
    @api.depends('wt_sample')
    def _compute_density(self):
        for rec in self:
            if rec.wt_sample :
                rec.density = round((rec.wt_sample) / 3375,3)
            else:
                rec.density = 0.0

    

    @api.depends('load')
    def _compute_strength(self):
        for record in self:
            if record.load:
                record.compressive_strength = record.load / 22.5
            else:
                record.compressive_strength = 0.0


    @api.depends('parent_id.date_of_casting')
    def _compute_dt_of_casting(self):
        for record in self:
            record.dt_of_casting = record.parent_id.date_of_casting



    @api.depends('dt_of_casting', 'days')
    def _compute_dt_of_testing(self):
     for rec in self:
        if rec.dt_of_casting and rec.days:
            rec.dt_of_testing1 = rec.dt_of_casting + timedelta(days=int(rec.days))
        else:
            rec.dt_of_testing1 = False
   




  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(DLCCompressiveStrengthLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1







class DLCMechanicalNotes(models.Model):
    _name = "mechanical.dlc.notes"

    parent_id = fields.Many2one('mechanical.dlc', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
