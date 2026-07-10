from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math
from decimal import Decimal
import matplotlib.pyplot as plt
import io
import numpy as np
import logging
import base64
from matplotlib.ticker import LogLocator, MultipleLocator
from matplotlib.ticker import AutoMinorLocator
from scipy.interpolate import CubicSpline , interp1d , Akima1DInterpolator
from matplotlib.ticker import MultipleLocator, StrMethodFormatter

class WbmMechanical(models.Model):
    _name = "mechanical.wbm"
    _inherit = "lerm.eln"
    _description = 'mechanical.wbm'
    _rec_name = "name"

    name = fields.Char("Name",default="WBM")

    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)



    # Dry Gradation Sieve Analysis (Sieve Size: 53 mm to 75 micron)
    dry_gradation_name = fields.Char(default="Sieve Analysis (Sieve Size: 53 mm to 75 micron)")
    dry_gradation_visible = fields.Boolean(compute="_compute_visible")

    dry_gradation_table = fields.One2many('mech.wbm.dry.gradation.line','parent_id',string="Dry Gradation")
    total_sieve_analysis = fields.Integer(string="Total",compute="_compute_total_sieve")
    


    def calculate_sieve(self): 
        for record in self:
            for line in record.dry_gradation_table:
                print("Rows",str(line.percent_retained))
                previous_line = line.serial_no - 1
                if previous_line == 0:
                    if line.percent_retained == 0:
                        # print("Percent retained 0",line.percent_retained)
                        line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2)})
                        line.write({'passing_percent': 100 })
                    else:
                        # print("Percent retained else",line.percent_retained)
                        line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2)})
                        line.write({'passing_percent': round(100 -line.percent_retained - line.percent_retained,2)})
                else:
                    previous_line_record = self.env['mech.wbm.dry.gradation.line'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
                    line.write({'cumulative_retained': round(previous_line_record + line.percent_retained,2)})
                    line.write({'passing_percent': round(100-(previous_line_record + line.percent_retained),2)})
                    print("Previous Cumulative",previous_line_record)
                    

    


    @api.depends('dry_gradation_table.wt_retained')
    def _compute_total_sieve(self):
        for record in self:
            print("recordd",record)
            record.total_sieve_analysis = sum(record.dry_gradation_table.mapped('wt_retained'))

    def default_get(self, fields):
        print("From Default Value")
        res = super(WbmMechanical, self).default_get(fields)

        default_dry_sieve_sizes = []
        # default_elongated_sieve_sizes = []
        # corrected
        dry_sieve_sizes = ['75 mm','63 mm','53 mm','45 mm','22.4 mm','pan']    
        # elongation_sieve_sizes = ['63 mm', '50 mm', '40 mm', '31.5 mm', '25 mm','20 mm','16 mm','12.5 mm','10 mm','6.3 mm','4.75 mm','2.36 mm','1.18 mm','Pan']


        for i in range(6):  # You can change the number of default lines as needed
            size = {
                'sieve_size': dry_sieve_sizes[i] # Set the default product
                # Set the default quantity
            }
            default_dry_sieve_sizes.append((0, 0, size))
        res['dry_gradation_table'] = default_dry_sieve_sizes
        # for i in range(14):  # You can change the number of default lines as needed
        #     size = {
        #         'sieve_size': elongation_sieve_sizes[i] # Set the default product
        #         # Set the default quantity
        #     }
        #     default_elongated_sieve_sizes.append((0, 0, size))
        res['dry_gradation_table'] = default_dry_sieve_sizes
        # res['elongation_table'] = default_elongated_sieve_sizes

        return res

    # Water Absorbtion 
    water_absorbtion_name = fields.Char(default="Specific Gravity & Water Absorption")
    water_absorbtion_visible = fields.Boolean(compute="_compute_visible")

    specific_water_line_ids = fields.One2many('wbm.specific.gravity.water.absorption.line', 'parent_id', string="Observations")

    avg_specific_gravity = fields.Float("Average Specific Gravity", compute="_compute_avg_specific_water", store=True)
    avg_water_absorption = fields.Float("Average Water Absorption (%)", compute="_compute_avg_specific_water", store=True)

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','74bd8e9f-f04a-44fd-968c-b72e2cbdb21d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','74bd8e9f-f04a-44fd-968c-b72e2cbdb21d')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','74bd8e9f-f04a-44fd-968c-b72e2cbdb21d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','74bd8e9f-f04a-44fd-968c-b72e2cbdb21d')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42135869f-6974-4a89-9a32-2375ca190815')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42135869f-6974-4a89-9a32-2375ca190815')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42135869f-6974-4a89-9a32-2375ca190815')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42135869f-6974-4a89-9a32-2375ca190815')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
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

    
    # Crushing Value
    crushing_value_name = fields.Char("Name",default="Crushing Value")
    crushing_visible = fields.Boolean("Crushing Visible",compute="_compute_visible")
   
    crushing_value_child_lines = fields.One2many('wbm.crushing.value.line','parent_id',string="Parameter")

    average_crushing_value = fields.Float(string="Average Aggregate Crushing Value (%)", compute="_compute_average_crushing_value")


    @api.depends('crushing_value_child_lines.acv')
    def _compute_average_crushing_value(self):
        for rec in self:
            values = rec.crushing_value_child_lines.mapped('acv')
            rec.average_crushing_value = sum(values) / len(values) if values else 0.0

    
    average_crushing_value_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_average_crushing_value_conformity", store=True)

    @api.depends('average_crushing_value','eln_ref','grade')
    def _compute_average_crushing_value_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_crushing_value_conformity = 'na'
                continue
            record.average_crushing_value_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0dcd134f-ca44-43dc-aad3-17d8f5c89ad1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0dcd134f-ca44-43dc-aad3-17d8f5c89ad1')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_crushing_value - record.average_crushing_value*mu_value
                    upper = record.average_crushing_value + record.average_crushing_value*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_crushing_value_conformity = 'pass'
                        break
                    else:
                        record.average_crushing_value_conformity = 'fail'


    average_crushing_value_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_crushing_value_nabl", store=True)

    @api.depends('average_crushing_value','eln_ref','grade')
    def _compute_average_crushing_value_nabl(self):
        
        for record in self:
            record.average_crushing_value_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0dcd134f-ca44-43dc-aad3-17d8f5c89ad1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0dcd134f-ca44-43dc-aad3-17d8f5c89ad1')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_crushing_value - record.average_crushing_value*mu_value
                    upper = record.average_crushing_value + record.average_crushing_value*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_crushing_value_nabl = 'pass'
                        break
                    else:
                        record.average_crushing_value_nabl = 'fail'


    # Impact Value 
    impact_value_name = fields.Char("Name",default="Impact Value")
    impact_visible = fields.Boolean("Impact Visible",compute="_compute_visible")

    impact_value_child_lines = fields.One2many('mech.wbm.impact.line','parent_id',string="Parameter")

    average_impact_value = fields.Float(string="Average Impact Value", compute="_compute_average_impact_value")

    

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','gh124113-e282-488c-9dbb-16e9f14b065b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','gh124113-e282-488c-9dbb-16e9f14b065b')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','gh124113-e282-488c-9dbb-16e9f14b065b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','gh124113-e282-488c-9dbb-16e9f14b065b')]).parameter_table
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


    # Abrasion Value
    abrasion_value_name = fields.Char("Name",default="Los Angeles Abrasion Value")
    abrasion_visible = fields.Boolean("Los Angeles Abrasion Value Visible",compute="_compute_visible")

    abrasion_value_line_ids = fields.One2many('wbm.la.abrasion.line', 'parent_id', string="Observations")

    avg_abrasion_value = fields.Float(
        "Average Value of L.A. Abrasion Value (%)",
        compute="_compute_avg_abrasion_value",
        store=True
    )

    @api.depends('abrasion_value_line_ids.la_value')
    def _compute_avg_abrasion_value(self):
        for rec in self:
            lines = rec.abrasion_value_line_ids

            if lines:
                values = lines.mapped('la_value')
                rec.avg_abrasion_value = sum(values) / len(values)
            else:
                rec.avg_abrasion_value = 0.0 

    avg_abrasion_value_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_abrasion_value_conformity", store=True)

    @api.depends('avg_abrasion_value','eln_ref','grade')
    def _compute_avg_abrasion_value_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_abrasion_value_conformity = 'na'
                continue
            record.avg_abrasion_value_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14257scf-9ee6-4115-a8db-015d7cb6d5c7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14257scf-9ee6-4115-a8db-015d7cb6d5c7')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_abrasion_value - record.avg_abrasion_value*mu_value
                    upper = record.avg_abrasion_value + record.avg_abrasion_value*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_abrasion_value_conformity = 'pass'
                        break
                    else:
                        record.avg_abrasion_value_conformity = 'fail'

    avg_abrasion_value_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_abrasion_value_nabl", store=True)

    @api.depends('avg_abrasion_value','eln_ref','grade')
    def _compute_avg_abrasion_value_nabl(self):
        
        for record in self:
            record.avg_abrasion_value_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14257scf-9ee6-4115-a8db-015d7cb6d5c7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14257scf-9ee6-4115-a8db-015d7cb6d5c7')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_abrasion_value - record.avg_abrasion_value*mu_value
                    upper = record.avg_abrasion_value + record.avg_abrasion_value*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_abrasion_value_nabl = 'pass'
                        break
                    else:
                        record.avg_abrasion_value_nabl = 'fail'


    # Loose Bulk Density
    loose_bulk_density_name = fields.Char("Name",default="Loose Bulk Density")
    loose_bulk_density_visible = fields.Boolean("Loose Bulk Density Visible",compute="_compute_visible")

    loose_line_ids = fields.One2many(
        'wbm.loose.bulk.density.line',
        'parent_id',
        string="Loose Bulk Density Trials"
    )

    loose_avg = fields.Float(
        string="Average Loose Bulk Density",
        compute="_compute_loose_avg",
        store=True
    )

    @api.depends('loose_line_ids.loose_bulk_density')
    def _compute_loose_avg(self):
        for rec in self:
            values = rec.loose_line_ids.mapped('loose_bulk_density')
            rec.loose_avg = sum(values) / len(values) if values else 0.0


    loose_avg_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_loose_avg_confirmity")
    
    @api.depends('loose_avg','eln_ref','grade')
    def _compute_loose_avg_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.loose_avg_confirmity = 'na'
                continue
            record.loose_avg_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c922dab7-6b7c-4f56-bbfa-7b6af4c7bbcf')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c922dab7-6b7c-4f56-bbfa-7b6af4c7bbcf')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.loose_avg - record.loose_avg*mu_value
                    upper = record.loose_avg + record.loose_avg*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.loose_avg_confirmity = 'pass'
                        break
                    else:
                        record.loose_avg_confirmity = 'fail'

    loose_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_loose_avg_nabl",store=True)

    @api.depends('loose_avg','eln_ref','grade')
    def _compute_loose_avg_nabl(self):
        
        for record in self:
            record.loose_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c922dab7-6b7c-4f56-bbfa-7b6af4c7bbcf')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c922dab7-6b7c-4f56-bbfa-7b6af4c7bbcf')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.loose_avg - record.loose_avg*mu_value
                    upper = record.loose_avg + record.loose_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.loose_avg_nabl = 'pass'
                        break
                    else:
                        record.loose_avg_nabl = 'fail'



    # Rodded Bulk Density
    rodded_bulk_density_name = fields.Char("Name",default="Rodded Bulk Density")
    rodded_bulk_density_visible = fields.Boolean("Rodded Bulk Density Visible",compute="_compute_visible")

    rodded_line_ids = fields.One2many(
        'wbm.rodded.bulk.density.line',
        'parent_id',
        string="Rodded Bulk Density Trials"
    )

    rodded_avg = fields.Float(
        string="Average Rodded Bulk Density",
        compute="_compute_rodded_avg",
        store=True
    )

    @api.depends('rodded_line_ids.rodded_bulk_density')
    def _compute_rodded_avg(self):
        for rec in self:
            values = rec.rodded_line_ids.mapped('rodded_bulk_density')
            rec.rodded_avg = sum(values) / len(values) if values else 0.0

    
    rodded_avg_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity', compute="_compute_rodded_avg_confirmity")
    
    @api.depends('rodded_avg','eln_ref','grade')
    def _compute_rodded_avg_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.rodded_avg_confirmity = 'na'
                continue
            record.rodded_avg_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','485a26f9-2028-4c4e-a055-6dcecea5746f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','485a26f9-2028-4c4e-a055-6dcecea5746f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.rodded_avg - record.rodded_avg*mu_value
                    upper = record.rodded_avg + record.rodded_avg*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.rodded_avg_confirmity = 'pass'
                        break
                    else:
                        record.rodded_avg_confirmity = 'fail'

    rodded_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_rodded_avg_nabl" ,store=True)

    @api.depends('rodded_avg','eln_ref','grade')
    def _compute_rodded_avg_nabl(self):
        
        for record in self:
            record.rodded_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','485a26f9-2028-4c4e-a055-6dcecea5746f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','485a26f9-2028-4c4e-a055-6dcecea5746f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.rodded_avg - record.rodded_avg*mu_value
                    upper = record.rodded_avg + record.rodded_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.rodded_avg_nabl = 'pass'
                        break
                    else:
                        record.rodded_avg_nabl = 'fail'


    # DELETERIOUS MATERIAL (CLAY & LUMPS)
    
    name_clay_lumps = fields.Char("Name",default="DELETERIOUS MATERIAL (CLAY & LUMPS)")
    clay_lump_visible = fields.Boolean("DELETERIOUS MATERIAL (CLAY & LUMPS) Visible",compute="_compute_visible")

    clay_lumps_percent_line_ids = fields.One2many('wbm.deleterious.clay.line', 'parent_id', string="Trials")

    clay_lumps_percent = fields.Float(
        "Average Deleterious Material (%)",
        compute="_compute_clay_lumps_percent",
        store=True
    )

    @api.depends('clay_lumps_percent_line_ids.percent')
    def _compute_clay_lumps_percent(self):
        for rec in self:
            lines = rec.clay_lumps_percent_line_ids

            if lines:
                values = lines.mapped('percent')
                rec.clay_lumps_percent = sum(values) / len(values)
            else:
                rec.clay_lumps_percent = 0.0


    clay_lumps_percent_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_clay_lumps_percent_conformity", store=True)

    @api.depends('clay_lumps_percent','eln_ref','grade')
    def _compute_clay_lumps_percent_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.clay_lumps_percent_conformity = 'na'
                continue
            record.clay_lumps_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4d1b0191-829d-4443-b2b7-65f5d73f8279')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4d1b0191-829d-4443-b2b7-65f5d73f8279')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.clay_lumps_percent - record.clay_lumps_percent*mu_value
                    upper = record.clay_lumps_percent + record.clay_lumps_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.clay_lumps_percent_conformity = 'pass'
                        break
                    else:
                        record.clay_lumps_percent_conformity = 'fail'

    clay_lumps_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_clay_lumps_percent_nabl", store=True)

    @api.depends('clay_lumps_percent','eln_ref','grade')
    def _compute_clay_lumps_percent_nabl(self):
        
        for record in self:
            record.clay_lumps_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4d1b0191-829d-4443-b2b7-65f5d73f8279')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4d1b0191-829d-4443-b2b7-65f5d73f8279')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.clay_lumps_percent - record.clay_lumps_percent*mu_value
                    upper = record.clay_lumps_percent + record.clay_lumps_percent*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.clay_lumps_percent_nabl = 'pass'
                        break
                    else:
                        record.clay_lumps_percent_nabl = 'fail'


    # Deleterious Material (Fine Silt & Fine Dust)
    
    name_silt_dust = fields.Char("Name",default="Deleterious Material (Fine Silt & Fine Dust)")
    silt_dust_visible = fields.Boolean("Deleterious Material (Fine Silt & Fine Dust) Visible",compute="_compute_visible")

    silt_dust_ids = fields.One2many('wbm.deleterious.silt.dust.line', 'parent_id', string="Trials")

    silt_dust_percent = fields.Float(
        "Average Deleterious Material Fine Silt and Fine Dust (%)",
        compute="_compute_silt_dust_percent",
        store=True
    )

    @api.depends('silt_dust_ids.percent')
    def _compute_silt_dust_percent(self):
        for rec in self:
            lines = rec.silt_dust_ids

            if lines:
                values = lines.mapped('percent')
                rec.silt_dust_percent = sum(values) / len(values)
            else:
                rec.silt_dust_percent = 0.0


    silt_dust_percent_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_silt_dust_percent_conformity", store=True)

    @api.depends('silt_dust_percent','eln_ref','grade')
    def _compute_silt_dust_percent_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.silt_dust_percent_conformity = 'na'
                continue
            record.silt_dust_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','487c9d6f-edb4-44af-ab85-6caf36eadc90')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','487c9d6f-edb4-44af-ab85-6caf36eadc90')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.silt_dust_percent - record.silt_dust_percent*mu_value
                    upper = record.silt_dust_percent + record.silt_dust_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.silt_dust_percent_conformity = 'pass'
                        break
                    else:
                        record.silt_dust_percent_conformity = 'fail'

    silt_dust_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_silt_dust_percent_nabl", store=True)

    @api.depends('silt_dust_percent','eln_ref','grade')
    def _compute_silt_dust_percent_nabl(self):
        
        for record in self:
            record.silt_dust_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','487c9d6f-edb4-44af-ab85-6caf36eadc90')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','487c9d6f-edb4-44af-ab85-6caf36eadc90')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.silt_dust_percent - record.silt_dust_percent*mu_value
                    upper = record.silt_dust_percent + record.silt_dust_percent*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.silt_dust_percent_nabl = 'pass'
                        break
                    else:
                        record.silt_dust_percent_nabl = 'fail'

    # Deleterious Material (Soft Fragments)
    
    name_soft_fragments = fields.Char("Name",default="Deleterious Material (Soft Fragments)")
    soft_fragments_visible = fields.Boolean("Deleterious Material (Soft Fragments) Visible",compute="_compute_visible")

    soft_fragments_ids = fields.One2many('wbm.deleterious.soft.line', 'parent_id', string="Trials")

    soft_fragments_percent = fields.Float(
        "Average Deleterious Material Soft Fragments (%)",
        compute="_compute_soft_fragments_percent",
        store=True
    )

    @api.depends('soft_fragments_ids.percent')
    def _compute_soft_fragments_percent(self):
        for rec in self:
            lines = rec.soft_fragments_ids

            if lines:
                values = lines.mapped('percent')
                rec.soft_fragments_percent = sum(values) / len(values)
            else:
                rec.soft_fragments_percent = 0.0


    soft_fragments_percent_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_soft_fragments_percent_conformity", store=True)

    @api.depends('soft_fragments_percent','eln_ref','grade')
    def _compute_soft_fragments_percent_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.soft_fragments_percent_conformity = 'na'
                continue
            record.soft_fragments_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','59d19da1-53f2-4875-a317-ad6960c79dcf')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','59d19da1-53f2-4875-a317-ad6960c79dcf')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.soft_fragments_percent - record.soft_fragments_percent*mu_value
                    upper = record.soft_fragments_percent + record.soft_fragments_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.soft_fragments_percent_conformity = 'pass'
                        break
                    else:
                        record.soft_fragments_percent_conformity = 'fail'

    soft_fragments_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_soft_fragments_percent_nabl", store=True)

    @api.depends('soft_fragments_percent','eln_ref','grade')
    def _compute_soft_fragments_percent_nabl(self):
        
        for record in self:
            record.soft_fragments_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','59d19da1-53f2-4875-a317-ad6960c79dcf')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','59d19da1-53f2-4875-a317-ad6960c79dcf')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.soft_fragments_percent - record.soft_fragments_percent*mu_value
                    upper = record.soft_fragments_percent + record.soft_fragments_percent*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.soft_fragments_percent_nabl = 'pass'
                        break
                    else:
                        record.soft_fragments_percent_nabl = 'fail'


    # Material Finer than 75 Micron

    finer75_name = fields.Char("Name",default="Material Finer than 75 Micron")					
    finer75_visible = fields.Boolean("Material Finer than 75 Micron Visible",compute="_compute_visible")

    finer75_line_ids = fields.One2many('wbm.material.finer.75.line', 'parent_id', string="Observations")

    avg_finer_percent = fields.Float(
        "Average Value of % Material Finer than 75 micron",
        compute="_compute_avg_finer_percent",
        store=True
    )

    @api.depends('finer75_line_ids.finer_percent')
    def _compute_avg_finer_percent(self):
        for rec in self:
            lines = rec.finer75_line_ids

            if lines:
                values = lines.mapped('finer_percent')
                rec.avg_finer_percent = sum(values) / len(values)
            else:
                rec.avg_finer_percent = 0.0

    avg_finer_percent_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_finer_percent_conformity", store=True)

    @api.depends('avg_finer_percent','eln_ref','grade')
    def _compute_avg_finer_percent_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_finer_percent_conformity = 'na'
                continue
            record.avg_finer_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1ae83572-a29f-49ed-8d29-c0138cc2b15e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1ae83572-a29f-49ed-8d29-c0138cc2b15e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_finer_percent - record.avg_finer_percent*mu_value
                    upper = record.avg_finer_percent + record.avg_finer_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_finer_percent_conformity = 'pass'
                        break
                    else:
                        record.avg_finer_percent_conformity = 'fail'

    avg_finer_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_finer_percent_nabl", store=True)

    @api.depends('avg_finer_percent','eln_ref','grade')
    def _compute_avg_finer_percent_nabl(self):
        
        for record in self:
            record.avg_finer_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1ae83572-a29f-49ed-8d29-c0138cc2b15e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1ae83572-a29f-49ed-8d29-c0138cc2b15e')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_finer_percent - record.avg_finer_percent*mu_value
            upper = record.avg_finer_percent + record.avg_finer_percent*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_finer_percent_nabl = 'pass'
                break
            else:
                record.avg_finer_percent_nabl = 'fail'


    # TEN PERCENT FINES VALUE (10% FINE VALUE) OF COARSE AGGREGATE			

    name_10fine = fields.Char(default="10% Fine Value")
    fine10_visible = fields.Boolean("10% Fine Visible",compute="_compute_visible")		

    fine10_line_ids = fields.One2many('wbm.tfv.line', 'parent_id', string="Observations")

    load_10percent_fine_values = fields.Float(
        "Average Value of 10% Fines Value (kN)",
        compute="_compute_avged",
        store=True
    )

    @api.depends('fine10_line_ids.tfv')
    def _compute_avged(self):
        for rec in self:
            lines = rec.fine10_line_ids

            if lines:
                values = lines.mapped('tfv')
                rec.load_10percent_fine_values = sum(values) / len(values)
            else:
                rec.load_10percent_fine_values = 0.0	


    load_10percent_fine_values_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_load_10percent_fine_values_conformity", store=True)



    @api.depends('load_10percent_fine_values','eln_ref','grade')
    def _compute_load_10percent_fine_values_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.load_10percent_fine_values_conformity = 'na'
                continue
            record.load_10percent_fine_values_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03c9c391-5925-4311-9e96-4239b9fc481e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03c9c391-5925-4311-9e96-4239b9fc481e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.load_10percent_fine_values - record.load_10percent_fine_values*mu_value
                    upper = record.load_10percent_fine_values + record.load_10percent_fine_values*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.load_10percent_fine_values_conformity = 'pass'
                        break
                    else:
                        record.load_10percent_fine_values_conformity = 'fail'

    load_10percent_fine_values_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_load_10percent_fine_values_nabl", store=True)

    @api.depends('load_10percent_fine_values','eln_ref','grade')
    def _compute_load_10percent_fine_values_nabl(self):
        
        for record in self:
            record.load_10percent_fine_values_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03c9c391-5925-4311-9e96-4239b9fc481e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03c9c391-5925-4311-9e96-4239b9fc481e')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.load_10percent_fine_values - record.load_10percent_fine_values*mu_value
            upper = record.load_10percent_fine_values + record.load_10percent_fine_values*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.load_10percent_fine_values_nabl = 'pass'
                break
            else:
                record.load_10percent_fine_values_nabl = 'fail'


    # Wet Impact Value

    wet_impact_name = fields.Char("Name", default="Wet Impact Value")
    wet_impact_visible = fields.Boolean("Wet Impact Value",compute="_compute_visible")


    wet_impact_line_ids = fields.One2many(
        'wbm.wet.impact.value.line',
        'parent_id',
        string="Trials"
    )

    avg_impact = fields.Float(
        "Average Wet Impact Value (%)",
        compute="_compute_avg_impact",
        store=True
    )


    @api.depends('wet_impact_line_ids.impact_value')
    def _compute_avg_impact(self):
        for rec in self:
            lines = rec.wet_impact_line_ids

            if lines:
                values = lines.mapped('impact_value')
                rec.avg_impact = sum(values) / len(values)
            else:
                rec.avg_impact = 0.0


    avg_impact_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_impact_conformity", store=True)

    @api.depends('avg_impact','eln_ref','grade')
    def _compute_avg_impact_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_impact_conformity = 'na'
                continue
            record.avg_impact_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','486e5475-5ec7-4bc6-b644-28dbfcb9ee33')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','486e5475-5ec7-4bc6-b644-28dbfcb9ee33')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_impact - record.avg_impact*mu_value
                    upper = record.avg_impact + record.avg_impact*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_impact_conformity = 'pass'
                        break
                    else:
                        record.avg_impact_conformity = 'fail'

    avg_impact_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_impact_nabl", store=True)

    @api.depends('avg_impact','eln_ref','grade')
    def _compute_avg_impact_nabl(self):
        
        for record in self:
            record.avg_impact_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','486e5475-5ec7-4bc6-b644-28dbfcb9ee33')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','486e5475-5ec7-4bc6-b644-28dbfcb9ee33')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_impact - record.avg_impact*mu_value
                    upper = record.avg_impact + record.avg_impact*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_impact_nabl = 'pass'
                        break
                    else:
                        record.avg_impact_nabl = 'fail'


    # Soundness Na2SO4
    soundness_na2so4_name = fields.Char("Name",default="SOUNDNESS (SODIUM SULPHATE TEST)")
    soundness_na2so4_visible = fields.Boolean("SOUNDNESS (SODIUM SULPHATE TEST) Visible",compute="_compute_visible")

    soundness_sod_line_ids = fields.One2many(
        'wbm.sodium.sulphate.line',
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
        'wbm.sodium.sulphate.two.line',
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
    
    total1_grading = fields.Float("Total Grading %", compute="_compute_totally")
    total1_weight_before = fields.Float("Total Weight Before", compute="_compute_totally")
    total1_weight_after = fields.Float("Total Weight After", compute="_compute_totally")
    total1_percent_loss = fields.Float("Total % Loss (Not Used)", compute="_compute_totally")
    total1_weighted_avg = fields.Float("Final Result (Weighted Avg)", compute="_compute_totally")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e42f2db7-8343-42a9-a5ed-3af2e343a381')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e42f2db7-8343-42a9-a5ed-3af2e343a381')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e42f2db7-8343-42a9-a5ed-3af2e343a381')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e42f2db7-8343-42a9-a5ed-3af2e343a381')]).parameter_table
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


    # SOUNDNESS (MAGNESIUM SULPHATE TEST)
    soundness_mgso4_name = fields.Char("Name",default="SOUNDNESS (MAGNESIUM SULPHATE TEST)")
    soundness_mgso4_visible = fields.Boolean("SOUNDNESS (MAGNESIUM SULPHATE TEST) Visible",compute="_compute_visible")

    soundness_mag_line_ids = fields.One2many(
        'wbm.magnesium.sulphate.line',
        'parent_id',
        string="Soundness MgSO4",default=lambda self: self.soundness_mag_line_ids_sizes()
    )

    @api.model
    def soundness_mag_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '60mm','retained_sieve': '40mm'}),
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
        'wbm.magnesium.sulphate.two.line',
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
    
    mag_total1_grading = fields.Float("Total Grading %", compute="_compute_totallly")
    mag_total1_weight_before = fields.Float("Total Weight Before", compute="_compute_totallly")
    mag_total1_weight_after = fields.Float("Total Weight After", compute="_compute_totallly")
    mag_total1_percent_loss = fields.Float("Total % Loss (Not Used)", compute="_compute_totallly")
    mag_total1_weighted_avg = fields.Float("Final Result (Weighted Avg)", compute="_compute_totallly")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9fa4e854-b7cc-44f4-99c3-c7d9dc038fb7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9fa4e854-b7cc-44f4-99c3-c7d9dc038fb7')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9fa4e854-b7cc-44f4-99c3-c7d9dc038fb7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9fa4e854-b7cc-44f4-99c3-c7d9dc038fb7')]).parameter_table
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






    # Flakiness and Elongation 
    elongation_fl_name = fields.Char(default="FLAKINESS AND ELONGATION INDEX")
    elongation_fl_visible = fields.Boolean("FLAKINESS AND ELONGATION INDEX",compute="_compute_visible")


    elongation_fl_table = fields.One2many('mech.wbm.elongation.flakiness.line','parent_id',string="Elongation Flakiness Index",default=lambda self: self.elongation_fl_table_sizes())


    @api.model
    def elongation_fl_table_sizes(self):
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21045gh-638d-4e6f-b258-df8a2fc0ea5c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21045gh-638d-4e6f-b258-df8a2fc0ea5c')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21045gh-638d-4e6f-b258-df8a2fc0ea5c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21045gh-638d-4e6f-b258-df8a2fc0ea5c')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2103654tr-8125-4f5f-aa7c-f82d1416d5eb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2103654tr-8125-4f5f-aa7c-f82d1416d5eb')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2103654tr-8125-4f5f-aa7c-f82d1416d5eb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2103654tr-8125-4f5f-aa7c-f82d1416d5eb')]).parameter_table
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

    
    

    

               # Liquid Limit
    liquid_limit_name = fields.Char("Name",default="Liquid Limit")
    liquid_limit_visible = fields.Boolean("Liquid Limit Visible",compute="_compute_visible")


    child_liness = fields.One2many('wbm.liquid.limits.line','parent_id',string="Liquid Limit")
    liquid_limit = fields.Float('Liquid Limit %',compute="_compute_liquid_limit")


    import math

    @api.depends('child_liness.blwo_no1', 'child_liness.moisture_content')
    def _compute_liquid_limit(self):
     for record in self:
        lines = record.child_liness.filtered(
            lambda l: l.blwo_no1 and l.moisture_content
        )

        if len(lines) < 2:
            record.liquid_limit = 0.0
            continue

        x = [math.log10(float(l.blwo_no1)) for l in lines]
        y = [float(l.moisture_content) for l in lines]

        n = len(x)

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)

        denominator = n * sum_x2 - (sum_x ** 2)

        if denominator == 0:
            record.liquid_limit = 0.0
            continue

        a = (n * sum_xy - sum_x * sum_y) / denominator
        b = (sum_y - a * sum_x) / n

        ll = a * math.log10(25.0) + b

        record.liquid_limit = round(ll, 2)

    
    liquid_limit_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_liquid_limit_conformity", store=True)

    @api.depends('liquid_limit','eln_ref','grade')
    def _compute_liquid_limit_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.liquid_limit_conformity = 'na'
                continue
            record.liquid_limit_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','994ea292-0480-4525-aa0a-39d85cf7e110')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','994ea292-0480-4525-aa0a-39d85cf7e110')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.liquid_limit - record.liquid_limit*mu_value
                    upper = record.liquid_limit + record.liquid_limit*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.liquid_limit_conformity = 'pass'
                        break
                    else:
                        record.liquid_limit_conformity = 'fail'

    liquid_limit_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_liquid_limit_nabl", store=True)

    @api.depends('liquid_limit','eln_ref','grade')
    def _compute_liquid_limit_nabl(self):
        
        for record in self:
            record.liquid_limit_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','994ea292-0480-4525-aa0a-39d85cf7e110')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','994ea292-0480-4525-aa0a-39d85cf7e110')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.liquid_limit - record.liquid_limit*mu_value
            upper = record.liquid_limit + record.liquid_limit*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.liquid_limit_nabl = 'pass'
                break
            else:
                record.liquid_limit_nabl = 'fail'



    graph_image_liquid = fields.Binary("Line Chart", compute="_compute_graph_image_liquid", store=True)

    show_liquid_graph = fields.Boolean(string="Show Liquid Limit Graph")


    def generate_line_chart_liquid(self):

      x_value = []
      y_value = []

      for line in self.child_liness:
        if line.blwo_no1 and line.moisture_content is not None:
            x_value.append(float(line.blwo_no1))
            y_value.append(float(line.moisture_content))

      if len(x_value) < 2:
        return False

    # Sort data
      data = sorted(zip(x_value, y_value), key=lambda x: x[0])
      x_value = [d[0] for d in data]
      y_value = [d[1] for d in data]

    # ----------------------------------
    # Regression: w = a log(N) + b
    # ----------------------------------
      x_log = [math.log10(x) for x in x_value]

      n = len(x_log)

      sum_x = sum(x_log)
      sum_y = sum(y_value)
      sum_xy = sum(x * y for x, y in zip(x_log, y_value))
      sum_x2 = sum(x * x for x in x_log)

      denominator = n * sum_x2 - sum_x ** 2

      if denominator == 0:
        return False

      a = (n * sum_xy - sum_x * sum_y) / denominator
      b = (sum_y - a * sum_x) / n

      # LL at 25 blows
      ll_value = a * math.log10(25) + b

      # ----------------------------------
      # Create smooth regression line
      # ----------------------------------
      x_fit = np.linspace(min(x_value), max(x_value), 500)
      y_fit = [a * math.log10(x) + b for x in x_fit]

    # ----------------------------------
    # Plot
    # ----------------------------------
      fig, ax = plt.subplots(figsize=(10, 4))

      ax.set_xscale('log')

    # Regression line
      ax.plot(
        x_fit,
        y_fit,
        color='blue',
        linewidth=2,
        label='Flow Curve'
    )

    # Actual points
      ax.scatter(
        x_value,
        y_value,
        color='red',
        edgecolors='black',
        s=80,
        zorder=5,
        label='Test Points'
    )

    # ----------------------------------
    # LL Marker
    # ----------------------------------
      ax.axvline(
        x=25,
        color='green',
        linestyle='--',
        linewidth=1.2
    )

      ax.axhline(
        y=ll_value,
        color='green',
        linestyle='--',
        linewidth=1.2
    )

      ax.scatter(
        [25],
        [ll_value],
        color='green',
        s=120,
        zorder=10
    )

      ax.annotate(
        f'LL = {ll_value:.2f}%',
        xy=(25, ll_value),
        xytext=(26, ll_value + 2),
        color='green',
        fontsize=12,
        fontweight='bold'
    )

    # ----------------------------------
    # Labels
    # ----------------------------------
      ax.set_title(
        'LIQUID LIMIT',
        fontsize=18,
        fontweight='bold'
    )

      ax.set_xlabel(
        'Number of Blows (Log Scale)',
        fontsize=12
    )

      ax.set_ylabel(
        'Water Content (%)',
        fontsize=12
    )

    # ----------------------------------
    # Limits
    # ----------------------------------
      ax.set_xlim(
        min(x_value) * 0.8,
        max(x_value) * 1.2
    )

      y_min = min(y_value)
      y_max = max(y_value)

      ax.set_ylim(
        max(0, y_min - 5),
        ((int(y_max / 10) + 1) * 10)
    )

    # ----------------------------------
    # Grid
    # ----------------------------------
      ax.xaxis.set_major_locator(LogLocator(base=10))
      ax.xaxis.set_minor_locator(
        LogLocator(
            base=10,
            subs=np.arange(2, 10) * 0.1
        )
    )

      ax.yaxis.set_minor_locator(MultipleLocator(1))

      ax.grid(
        which='major',
        linestyle='-',
        linewidth=0.5,
        alpha=0.7
    )

      ax.grid(
        which='minor',
        linestyle='--',
        linewidth=0.3,
        alpha=0.5
    )

      ax.legend()

      plt.tight_layout()

      buffer = io.BytesIO()
      plt.savefig(
        buffer,
        format='png',
        dpi=100,
        bbox_inches='tight'
    )

      plt.close()

      buffer.seek(0)

      return base64.b64encode(
        buffer.read()
    ).decode('utf-8')


        
       
    

    @api.depends('child_liness')
    def _compute_graph_image_liquid(self):
        try:
            for record in self:
                chart_image_liquid = record.generate_line_chart_liquid()
                record.graph_image_liquid = chart_image_liquid
        except:
            pass 


      # Plastic Limit
    plastic_limit_name = fields.Char("Name",default="Plastic Limit")
    plastic_limit_visible = fields.Boolean("Plastic Limit Visible",compute="_compute_visible")
   
    plastic_limit_table = fields.One2many('wbm.plasticl.limit.line','parent_id',string="Parameter")

    plastic_limit = fields.Float(string="Average ",compute="_compute_plastic_limit")
   
    @api.depends('plastic_limit_table.water_content_pastic')
    def _compute_plastic_limit(self):
        for record in self:
            total_water_content_pastic = sum(record.plastic_limit_table.mapped('water_content_pastic'))
            record.plastic_limit = total_water_content_pastic / len(record.plastic_limit_table) if record.plastic_limit_table else 0.0
   

    plastic_limit_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Plastic Limit Conformity", compute="_compute_plastic_limit_conformity", store=True)

    @api.depends('plastic_limit','eln_ref','grade')
    def _compute_plastic_limit_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.plastic_limit_conformity = 'na'
                continue
            record.plastic_limit_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','eb7b3e8d-c721-4c7f-9194-490b7b1b5d0b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','eb7b3e8d-c721-4c7f-9194-490b7b1b5d0b')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.plastic_limit - record.plastic_limit*mu_value
                    upper = record.plastic_limit + record.plastic_limit*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.plastic_limit_conformity = 'pass'
                        break
                    else:
                        record.plastic_limit_conformity = 'fail'

    plastic_limit_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="Plastic Limit NABL", compute="_compute_plasticity_limi_nabl", store=True)

    @api.depends('plastic_limit','eln_ref','grade')
    def _compute_plasticity_limi_nabl(self):
        
        for record in self:
            record.plastic_limit_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','eb7b3e8d-c721-4c7f-9194-490b7b1b5d0b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','eb7b3e8d-c721-4c7f-9194-490b7b1b5d0b')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.plastic_limit - record.plastic_limit*mu_value
            upper = record.plastic_limit + record.plastic_limit*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.plastic_limit_nabl = 'pass'
                break
            else:
                record.plastic_limit_nabl = 'fail'

    plasticity_index = fields.Float(string="Plasticity Index", compute="_compute_plasticity_index")

    @api.depends('plastic_limit', 'liquid_limit')
    def _compute_plasticity_index(self):
        for record in self:
            if record.liquid_limit is not None and record.plastic_limit is not None:
                record.plasticity_index = record.liquid_limit - record.plastic_limit
            else:
                record.plasticity_index = 0.0



    plasticity_index_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Plasticity Index Conformity", compute="_compute_plasticity_index_conformity", store=True)

    @api.depends('plasticity_index','eln_ref','grade')
    def _compute_plasticity_index_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.plasticity_index_conformity = 'na'
                continue
            record.plasticity_index_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9f56f4a-6e7e-4d1c-a917-40eab9c895d1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9f56f4a-6e7e-4d1c-a917-40eab9c895d1')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.plasticity_index - record.plasticity_index*mu_value
                    upper = record.plasticity_index + record.plasticity_index*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.plasticity_index_conformity = 'pass'
                        break
                    else:
                        record.plasticity_index_conformity = 'fail'

    plasticity_index_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="Plasticity Index NABL", compute="_compute_plasticity_index_nabl", store=True)

    @api.depends('plasticity_index','eln_ref','grade')
    def _compute_plasticity_index_nabl(self):
        
        for record in self:
            record.plasticity_index_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9f56f4a-6e7e-4d1c-a917-40eab9c895d1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9f56f4a-6e7e-4d1c-a917-40eab9c895d1')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.plasticity_index - record.plasticity_index*mu_value
            upper = record.plasticity_index + record.plasticity_index*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.plasticity_index_nabl = 'pass'
                break
            else:
                record.plasticity_index_nabl = 'fail'


      # Heavy Compaction-MDD
    heavy_name = fields.Char("Name",default="DETERMINATION OF Heavy Compaction - OMC AND MDD ")
    heavy_visible = fields.Boolean("Heavy Compaction-MDD Visible",compute="_compute_visible")
    heavy_table = fields.One2many('wbm.heavy.compaction.line','parent_id',string="Heavy Compaction")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c743540a-9d21-460b-973b-06e4dc10c632')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c743540a-9d21-460b-973b-06e4dc10c632')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c743540a-9d21-460b-973b-06e4dc10c632')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c743540a-9d21-460b-973b-06e4dc10c632')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6ef4bb1a-cf2f-4cc4-8f5f-b0bdd115e4ad')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6ef4bb1a-cf2f-4cc4-8f5f-b0bdd115e4ad')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6ef4bb1a-cf2f-4cc4-8f5f-b0bdd115e4ad')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6ef4bb1a-cf2f-4cc4-8f5f-b0bdd115e4ad')]).parameter_table
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

    
    graph_image_density = fields.Binary("Line Chart", compute="_compute_graph_image_density_omc_light", store=True)

    show_heavy_graph = fields.Boolean(string="Show Compaction Graph")



    def generate_line_chart_light_omc(self):

     x_value = []
     y_value = []

     for line in self.heavy_table:
        if line.water_content and line.dry_density:
            x_value.append(float(line.water_content))
            y_value.append(float(line.dry_density))

     if len(x_value) < 3:
        return False

    # Sort data
     data = sorted(zip(x_value, y_value))
     x = np.array([d[0] for d in data])
     y = np.array([d[1] for d in data])

    # ==========================
    # Quadratic Compaction Curve
    # ==========================
     coeff = np.polyfit(x, y, 2)
     poly = np.poly1d(coeff)

     x_smooth = np.linspace(x.min(), x.max(), 500)
     y_smooth = poly(x_smooth)

    # OMC / MDD
     omc = -coeff[1] / (2 * coeff[0])
     mdd = poly(omc)

     plt.figure(figsize=(15, 5))

    # Smooth blue curve
     plt.plot(
        x_smooth,
        y_smooth,
        color='blue',
        linewidth=2.5
    )

    # Show points ON CURVE only
     y_curve_points = poly(x)
  
     plt.scatter(
        x,
        y_curve_points,
        color='red',
        edgecolors='none',
        s=40,
        zorder=5
    )

    # Peak point
     plt.scatter(
        omc,
        mdd,
        color='red',
        s=120,
        zorder=10
    )

    # OMC / MDD guide lines
     plt.axhline(
        y=mdd,
        color='red',
        linestyle='--',
        linewidth=1
    )

     plt.axvline(
        x=omc,
        color='red',
        linestyle='--',
        linewidth=1
    )

    # Annotation
     plt.text(
        omc + 0.2,
        mdd + 0.002,
        f"OMC: {omc:.2f}%\nMDD: {mdd:.2f}",
        color='red',
        fontsize=11,
        fontweight='bold'
    )

    # Labels
     plt.xlabel(
        'Water Content (%)',
        fontsize=12
    )

     plt.ylabel(
        'Dry Density (g/cc)',
        fontsize=12
    )

     plt.title(
        'DETERMINATION OF COMPACTION OMC / MDD',
        fontsize=16
    )

    # Limits
     plt.xlim(
        left=0,
        right=max(x) + 2
    )

     plt.ylim(
        bottom=min(y) - 0.03,
        top=max(y_smooth) + 0.03
    )

    # ==========================
    # Graph Paper Background
    # ==========================
     ax = plt.gca()

    # X-axis grid
     ax.xaxis.set_major_locator(MultipleLocator(1))
     ax.xaxis.set_minor_locator(MultipleLocator(0.1))

    # Y-axis grid
     ax.yaxis.set_major_locator(MultipleLocator(0.05))
     ax.yaxis.set_minor_locator(MultipleLocator(0.001))

    # Major Grid
     plt.grid(
        which='major',
        color='green',
        linestyle='-',
        linewidth=0.5,
        alpha=0.55
    )

    # Minor Grid
     plt.grid(
        which='minor',
        color='green',
        linestyle=':',
        linewidth=0.3,
        alpha=0.45
    )

     plt.tight_layout()

    # Save Image
     buffer = io.BytesIO()

     plt.savefig(
        buffer,
        format='png',
        dpi=150,
        bbox_inches='tight'
    )

     plt.close()

     buffer.seek(0)

     return base64.b64encode(
        buffer.read()
    ).decode('utf-8')
    


    



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
    omc_table = fields.One2many('wbm.omc.compaction.line','parent_id',string="OMC Compaction")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ce201d22-b557-4b19-8362-e49828b10d3e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ce201d22-b557-4b19-8362-e49828b10d3e')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ce201d22-b557-4b19-8362-e49828b10d3e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ce201d22-b557-4b19-8362-e49828b10d3e')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6e96e9c9-690b-4445-bd12-d56e9d347b9c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6e96e9c9-690b-4445-bd12-d56e9d347b9c')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6e96e9c9-690b-4445-bd12-d56e9d347b9c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6e96e9c9-690b-4445-bd12-d56e9d347b9c')]).parameter_table
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

    
    graph_image_density1 = fields.Binary("Line Chart", compute="_compute_graph_image_density_omc_light1", store=True)

    show_light_graph = fields.Boolean(string="Show Compaction Graph")




    def generate_line_chart_light_omc1(self):

     x_value = []
     y_value = []

     for line in self.omc_table:
        if line.water_content1 and line.dry_density1:
            x_value.append(float(line.water_content1))
            y_value.append(float(line.dry_density1))

     if len(x_value) < 3:
        return False

    # Sort data
     data = sorted(zip(x_value, y_value))
     x = np.array([d[0] for d in data])
     y = np.array([d[1] for d in data])

    # ==========================
    # Quadratic Compaction Curve
    # ==========================
     coeff = np.polyfit(x, y, 2)
     poly = np.poly1d(coeff)

     x_smooth = np.linspace(x.min(), x.max(), 500)
     y_smooth = poly(x_smooth)

    # OMC / MDD
     omc = -coeff[1] / (2 * coeff[0])
     mdd = poly(omc)

     plt.figure(figsize=(15, 5))

    # Smooth blue curve
     plt.plot(
        x_smooth,
        y_smooth,
        color='blue',
        linewidth=2.5
    )

    # Show points ON CURVE only
     y_curve_points = poly(x)
  
     plt.scatter(
        x,
        y_curve_points,
        color='red',
        edgecolors='none',
        s=40,
        zorder=5
    )

    # Peak point
     plt.scatter(
        omc,
        mdd,
        color='red',
        s=120,
        zorder=10
    )

    # OMC / MDD guide lines
     plt.axhline(
        y=mdd,
        color='red',
        linestyle='--',
        linewidth=1
    )

     plt.axvline(
        x=omc,
        color='red',
        linestyle='--',
        linewidth=1
    )

    # Annotation
     plt.text(
        omc + 0.2,
        mdd + 0.002,
        f"OMC: {omc:.2f}%\nMDD: {mdd:.2f}",
        color='red',
        fontsize=11,
        fontweight='bold'
    )

    # Labels
     plt.xlabel(
        'Water Content (%)',
        fontsize=12
    )

     plt.ylabel(
        'Dry Density (g/cc)',
        fontsize=12
    )

     plt.title(
        'DETERMINATION OF COMPACTION OMC / MDD',
        fontsize=16
    )

    # Limits
     plt.xlim(
        left=0,
        right=max(x) + 2
    )

     plt.ylim(
        bottom=min(y) - 0.03,
        top=max(y_smooth) + 0.03
    )

    # ==========================
    # Graph Paper Background
    # ==========================
     ax = plt.gca()

    # X-axis grid
     ax.xaxis.set_major_locator(MultipleLocator(1))
     ax.xaxis.set_minor_locator(MultipleLocator(0.1))

    # Y-axis grid
     ax.yaxis.set_major_locator(MultipleLocator(0.05))
     ax.yaxis.set_minor_locator(MultipleLocator(0.001))

    # Major Grid
     plt.grid(
        which='major',
        color='green',
        linestyle='-',
        linewidth=0.5,
        alpha=0.55
    )

    # Minor Grid
     plt.grid(
        which='minor',
        color='green',
        linestyle=':',
        linewidth=0.3,
        alpha=0.45
    )

     plt.tight_layout()

    # Save Image
     buffer = io.BytesIO()

     plt.savefig(
        buffer,
        format='png',
        dpi=150,
        bbox_inches='tight'
    )

     plt.close()

     buffer.seek(0)

     return base64.b64encode(
        buffer.read()
    ).decode('utf-8')

        

    @api.depends('omc_table')
    def _compute_graph_image_density_omc_light1(self):
        try:
            for record in self:
                chart_image_light_omc1 = record.generate_line_chart_light_omc1()
                record.graph_image_density1 = chart_image_light_omc1
        except:
            pass 



    


    # CBR

    soil_name = fields.Char("Name",default="California Bearing Ratio")
    soil_visible = fields.Boolean("California Bearing Ratio Visible",compute="_compute_visible")
   
    soil_table = fields.One2many('wbm.cbr.line','parent_id',string="CBR",default=lambda self: self._default_soil_table())

    proving_ring_cf = fields.Float(string="Proving Ring Calibration Factor",digits=(10,3))

    corrected_load_25_s1 = fields.Float(compute="_compute_cbr", store=True,digits=(12,3))
    corrected_load_25_s2 = fields.Float(compute="_compute_cbr", store=True,digits=(12,3))
    corrected_load_25_s3 = fields.Float(compute="_compute_cbr", store=True,digits=(12,3))

    corrected_load_5_s1 = fields.Float(compute="_compute_cbr", store=True,digits=(12,3))
    corrected_load_5_s2 = fields.Float(compute="_compute_cbr", store=True,digits=(12,3))
    corrected_load_5_s3 = fields.Float(compute="_compute_cbr", store=True,digits=(12,3))


    cbr_25_s1 = fields.Float("2.5mm", compute="_compute_cbr", store=True)
    cbr_25_s2 = fields.Float("2.5mm", compute="_compute_cbr", store=True)
    cbr_25_s3 = fields.Float("2.5mm ", compute="_compute_cbr", store=True)

    cbr_5_s1 = fields.Float("5mm", compute="_compute_cbr", store=True)
    cbr_5_s2 = fields.Float("5mm", compute="_compute_cbr", store=True)
    cbr_5_s3 = fields.Float("5mm", compute="_compute_cbr", store=True)

    cbr_25_avg = fields.Float("2.5mm", compute="_compute_cbr", store=True)

    # cbr_5_avg = fields.Float("5mm", compute="_compute_cbr", store=True)
    # cbr_max = fields.Float("CBR Max", compute="_compute_cbr", store=True)


    @api.depends('soil_table.sample1_load',
             'soil_table.sample2_load',
             'soil_table.sample3_load',
             'soil_table.penetration')
    def _compute_cbr(self):
     for rec in self:
        lines = rec.soil_table

        # Get 2.5 mm & 5 mm rows
        line_25 = lines.filtered(lambda l: l.penetration == 2.5)
        line_5 = lines.filtered(lambda l: l.penetration == 5.0)

        if line_25:
          l = line_25[0]
          rec.corrected_load_25_s1 = l.sample1_load
          rec.corrected_load_25_s2 = l.sample2_load
          rec.corrected_load_25_s3 = l.sample3_load

        if line_5:
          l = line_5[0]
          rec.corrected_load_5_s1 = l.sample1_load
          rec.corrected_load_5_s2 = l.sample2_load
          rec.corrected_load_5_s3 = l.sample3_load

        # Default values
        rec.cbr_25_s1 = rec.cbr_25_s2 = rec.cbr_25_s3 = 0.0
        rec.cbr_5_s1 = rec.cbr_5_s2 = rec.cbr_5_s3 = 0.0

        # -------- 2.5 mm --------
        if line_25:
            l = line_25[0]
            rec.cbr_25_s1 = (l.sample1_load / 1370)*100 if l.sample1_load else 0
            rec.cbr_25_s2 = (l.sample2_load / 1370)*100 if l.sample2_load else 0
            rec.cbr_25_s3 = (l.sample3_load / 1370*100) if l.sample3_load else 0

        # -------- 5 mm --------
        if line_5:
            l = line_5[0]
            rec.cbr_5_s1 = (l.sample1_load / 2055)*100 if l.sample1_load else 0
            rec.cbr_5_s2 = (l.sample2_load / 2055)*100 if l.sample2_load else 0
            rec.cbr_5_s3 = (l.sample3_load / 2055)*100 if l.sample3_load else 0

        # -------- AVERAGE --------
        rec.cbr_25_avg = (rec.cbr_25_s1 + rec.cbr_25_s2 + rec.cbr_25_s3) / 3
        # rec.cbr_5_avg = (rec.cbr_5_s1 + rec.cbr_5_s2 + rec.cbr_5_s3) / 3

        # # -------- MAX --------
        # rec.cbr_max = max(rec.cbr_25_avg, rec.cbr_5_avg)


    @api.model
    def _default_soil_table(self):
        default_lines = [
            (0, 0, {'penetration': '0.50'}),
            (0, 0, {'penetration': '1.0'}),
            (0, 0, {'penetration': '1.50'}),
            (0, 0, {'penetration': '2.00'}),
            (0, 0, {'penetration': '2.50'}),
            (0, 0, {'penetration': ' 3.00'}),
            (0, 0, {'penetration': '4.00'}),
            (0, 0, {'penetration': '5.00'}),
            (0, 0, {'penetration': '7.50'}),
            (0, 0, {'penetration': '10.00'}),
            (0, 0, {'penetration': '12.50'})
        ]
        return default_lines
    
    cbr_chart_image = fields.Binary("CBR Chart", readonly=True)
    cbr_chart_filename = fields.Char("Filename")
    show_cbr = fields.Boolean(string="Show CBR Graph")


    def action_generate_cbr_chart(self):
     for rec in self:
        lines = self.env['wbm.cbr.line'].search([
            ('parent_id', '=', rec.id)
        ], order='penetration asc')

        penetration = [l.penetration for l in lines]

        s1 = [l.sample1_load for l in lines]
        s2 = [l.sample2_load for l in lines]
        s3 = [l.sample3_load for l in lines]

        # ✅ Increase width only (width=12, height=5)
        plt.figure(figsize=(12, 5))

        plt.plot(penetration, s1, marker='o', label='Sample-1')
        plt.plot(penetration, s2, marker='o', label='Sample-2')
        plt.plot(penetration, s3, marker='o', label='Sample-3')

        plt.xlabel('Penetration (mm)')
        plt.ylabel('Load (Kg/cm²)')
        plt.title('CBR Test Graph')

        # ✅ Major grid (big squares)
        plt.grid(which='major', linestyle='-', linewidth=0.8)

        # ✅ Minor grid (small squares inside)
        ax = plt.gca()
        ax.xaxis.set_minor_locator(AutoMinorLocator(5))
        ax.yaxis.set_minor_locator(AutoMinorLocator(5))
        plt.grid(which='minor', linestyle=':', linewidth=0.5)

        plt.legend()

        # Save image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close()

        image = base64.b64encode(buffer.getvalue())
        buffer.close()

        rec.cbr_chart_image = image
        rec.cbr_chart_filename = "cbr_chart.png"


    cbr_25_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_cbr_25_avg_conformity", store=True)

    @api.depends('cbr_25_avg','eln_ref','grade')
    def _compute_cbr_25_avg_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.cbr_25_avg_conformity = 'na'
                continue

            record.cbr_25_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d44fea41-32eb-4bc0-b6ae-bbd3643c0e99')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d44fea41-32eb-4bc0-b6ae-bbd3643c0e99')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.cbr_25_avg - record.cbr_25_avg*mu_value
                    upper = record.cbr_25_avg + record.cbr_25_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.cbr_25_avg_conformity = 'pass'
                        break
                    else:
                        record.cbr_25_avg_conformity = 'fail'

    cbr_25_avg_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_cbr_25_avg_nabl", store=True)

    @api.depends('cbr_25_avg','eln_ref','grade')
    def _compute_cbr_25_avg_nabl(self):
        
        for record in self:
            record.cbr_25_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d44fea41-32eb-4bc0-b6ae-bbd3643c0e99')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d44fea41-32eb-4bc0-b6ae-bbd3643c0e99')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.cbr_25_avg - record.cbr_25_avg*mu_value
            upper = record.cbr_25_avg + record.cbr_25_avg*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.cbr_25_avg_nabl = 'pass'
                break
            else:
                record.cbr_25_avg_nabl = 'fail'





    


    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.dry_gradation_visible = False
            record.water_absorbtion_visible  = False
            record.crushing_visible = False
            record.impact_visible = False
            record.abrasion_visible = False
            record.loose_bulk_density_visible = False
            record.rodded_bulk_density_visible = False
            record.clay_lump_visible = False
            record.finer75_visible = False
            record.fine10_visible = False
            record.wet_impact_visible = False
            record.silt_dust_visible = False
            record.soft_fragments_visible = False
            record.soundness_na2so4_visible = False
            record.soundness_mgso4_visible = False
            record.elongation_fl_visible = False
            record.liquid_limit_visible = False
            record.plastic_limit_visible = False
            record.heavy_visible = False
            record.omc_visible = False
            record.soil_visible = False


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)


                if sample.internal_id == '4525465214-3497-4b7f-819a-a26f25c9848':
                    record.dry_gradation_visible = True

                if sample.internal_id == '42135869f-6974-4a89-9a32-2375ca190815':
                    record.water_absorbtion_visible  = True

                if sample.internal_id == '0dcd134f-ca44-43dc-aad3-17d8f5c89ad1':
                    record.crushing_visible = True

                if sample.internal_id == 'gh124113-e282-488c-9dbb-16e9f14b065b':
                    record.impact_visible = True

                if sample.internal_id == '14257scf-9ee6-4115-a8db-015d7cb6d5c7':
                    record.abrasion_visible = True

                if sample.internal_id == 'c922dab7-6b7c-4f56-bbfa-7b6af4c7bbcf':
                    record.loose_bulk_density_visible = True

                if sample.internal_id == '485a26f9-2028-4c4e-a055-6dcecea5746f':
                    record.rodded_bulk_density_visible = True


                if sample.internal_id == '4d1b0191-829d-4443-b2b7-65f5d73f8279':
                    record.clay_lump_visible = True

                if sample.internal_id == '1ae83572-a29f-49ed-8d29-c0138cc2b15e':
                    record.finer75_visible = True

                if sample.internal_id == '03c9c391-5925-4311-9e96-4239b9fc481e':
                    record.fine10_visible = True

                if sample.internal_id == '486e5475-5ec7-4bc6-b644-28dbfcb9ee33':
                    record.wet_impact_visible = True

                if sample.internal_id == '487c9d6f-edb4-44af-ab85-6caf36eadc90':
                    record.silt_dust_visible = True

                if sample.internal_id == '59d19da1-53f2-4875-a317-ad6960c79dcf':
                    record.soft_fragments_visible = True

                if sample.internal_id == 'e42f2db7-8343-42a9-a5ed-3af2e343a381':
                    record.soundness_na2so4_visible = True

                if sample.internal_id == '9fa4e854-b7cc-44f4-99c3-c7d9dc038fb7':
                    record.soundness_mgso4_visible = True

                if sample.internal_id == '21045gh-638d-4e6f-b258-df8a2fc0ea5c':
                    record.elongation_fl_visible = True


                if sample.internal_id == '994ea292-0480-4525-aa0a-39d85cf7e110':
                    record.liquid_limit_visible = True

                if sample.internal_id == 'eb7b3e8d-c721-4c7f-9194-490b7b1b5d0b':
                    record.plastic_limit_visible  = True 

                if sample.internal_id == 'c743540a-9d21-460b-973b-06e4dc10c632':
                    record.heavy_visible = True

                if sample.internal_id == '6e96e9c9-690b-4445-bd12-d56e9d347b9c':
                    record.omc_visible = True
                
                if sample.internal_id == 'd44fea41-32eb-4bc0-b6ae-bbd3643c0e99':
                    record.soil_visible = True



                    




                
                
                


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:



            # Sieve Analysis
            if result.parameter.internal_id == '4525465214-3497-4b7f-819a-a26f25c9848':
                result.calculated = True

            # Bulk Density
            if result.parameter.internal_id == '29f72178-f2d9-4590-9ca2-fd0a9be33bfe':
                result.calculated = True


             # Loose bulk Density
            if result.parameter.internal_id == 'c922dab7-6b7c-4f56-bbfa-7b6af4c7bbcf':
                result.result_char = round(self.loose_avg,2)
                result.calculated = True
                if self.loose_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Rodded bulk Density
            if result.parameter.internal_id == '485a26f9-2028-4c4e-a055-6dcecea5746f':
                result.calculated = True
                result.result_char = round(self.rodded_avg,2)
                if self.rodded_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # impact value 
            if result.parameter.internal_id == 'gh124113-e282-488c-9dbb-16e9f14b065b':
                result.calculated = True
                result.result_char = round(self.average_impact_value,2)
                if self.average_impact_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # specific gravity 
            if result.parameter.internal_id == '74bd8e9f-f04a-44fd-968c-b72e2cbdb21d':
                result.calculated = True
                result.result_char = round(self.avg_specific_gravity,2)
                if self.avg_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # water absorbtion
            if result.parameter.internal_id == '42135869f-6974-4a89-9a32-2375ca190815':
                result.calculated = True
                result.result_char = round(self.avg_water_absorption,2)
                if self.avg_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            # crushing value 
            if result.parameter.internal_id == '0dcd134f-ca44-43dc-aad3-17d8f5c89ad1':
                result.calculated = True
                result.result_char = round(self.average_crushing_value,2)
                if self.average_crushing_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Los Angeles Abrasion Value
            if result.parameter.internal_id == '14257scf-9ee6-4115-a8db-015d7cb6d5c7':
                result.calculated = True
                result.result_char = round(self.avg_abrasion_value,2)
                if self.avg_abrasion_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Material finer than 75 micron
            if result.parameter.internal_id == '1ae83572-a29f-49ed-8d29-c0138cc2b15e':
                result.calculated = True
                result.result_char = round(self.avg_finer_percent,2)
                if self.avg_finer_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 10 % Fine Value
            if result.parameter.internal_id == '03c9c391-5925-4311-9e96-4239b9fc481e':
                result.calculated = True
                result.result_char = round(self.load_10percent_fine_values,2)
                if self.load_10percent_fine_values_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # DELETERIOUS MATERIAL (CLAY & LUMPS)
            if result.parameter.internal_id == '4d1b0191-829d-4443-b2b7-65f5d73f8279':
                result.calculated = True
                result.result_char = round(self.clay_lumps_percent,2)
                if self.clay_lumps_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Deleterious Material (Fine Silt & Fine Dust)
            if result.parameter.internal_id == '487c9d6f-edb4-44af-ab85-6caf36eadc90':
                result.calculated = True
                result.result_char = round(self.silt_dust_percent,2)
                if self.silt_dust_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Deleterious Material (Soft Fragments)
            if result.parameter.internal_id == '59d19da1-53f2-4875-a317-ad6960c79dcf':
                result.calculated = True
                result.result_char = round(self.soft_fragments_percent,2)
                if self.soft_fragments_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Wet Impact Value
            if result.parameter.internal_id == '486e5475-5ec7-4bc6-b644-28dbfcb9ee33':
                result.calculated = True
                result.result_char = round(self.avg_impact,2)
                if self.avg_impact_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Soundness - Na2SO4
            if result.parameter.internal_id == 'e42f2db7-8343-42a9-a5ed-3af2e343a381':
                result.calculated = True
                result.result_char = round(self.total_weighted_avg,2)
                if self.total_weighted_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Soundness - MgSO4
            if result.parameter.internal_id == '9fa4e854-b7cc-44f4-99c3-c7d9dc038fb7':
                result.calculated = True
                result.result_char = round(self.mag_total_weighted_avg,2)
                if self.mag_total_weighted_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Elongation
            if result.parameter.internal_id == '21045gh-638d-4e6f-b258-df8a2fc0ea5c':
                result.calculated = True

            # Flakiness
            if result.parameter.internal_id == '2103654tr-8125-4f5f-aa7c-f82d1416d5eb':
                result.calculated = True

            # Atterberg's Limit
            if result.parameter.internal_id == '2d901fdf-2da5-45bc-b066-9731f6b95555':
                result.calculated = True
            

            # Liquid Limit
            if result.parameter.internal_id == '994ea292-0480-4525-aa0a-39d85cf7e110':
                result.calculated = True
                result.result_char = round(self.liquid_limit,2)
                if self.liquid_limit_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Plastic Limit
            if result.parameter.internal_id == 'eb7b3e8d-c721-4c7f-9194-490b7b1b5d0b':
                result.calculated = True
                result.result_char = round(self.plastic_limit,2)
                if self.plastic_limit_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Plasticity Index
            if result.parameter.internal_id == 'e9f56f4a-6e7e-4d1c-a917-40eab9c895d1':
                result.calculated = True
                result.result_char = round(self.plasticity_index,2)
                if self.plasticity_index_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Heavy Visible
            if result.parameter.internal_id == 'c743540a-9d21-460b-973b-06e4dc10c632':
                result.calculated = True
                result.result_char = round(self.max_dry_density,2)
                if self.max_dry_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Heavy Visible
            if result.parameter.internal_id == '6ef4bb1a-cf2f-4cc4-8f5f-b0bdd115e4ad':
                result.calculated = True
                result.result_char = round(self.omc,2)
                if self.omc_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # OMC
            if result.parameter.internal_id == 'ce201d22-b557-4b19-8362-e49828b10d3e':
                result.calculated = True
                result.result_char = round(self.max_dry_density1,2)
                if self.max_dry_density1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # OMC
            if result.parameter.internal_id == '6e96e9c9-690b-4445-bd12-d56e9d347b9c':
                result.calculated = True
                result.result_char = round(self.omc1,2)
                if self.omc1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # CBR
            if result.parameter.internal_id == 'd44fea41-32eb-4bc0-b6ae-bbd3643c0e99':
                result.calculated = True
                result.result_char = round(self.cbr_25_avg,2)
                if self.cbr_25_avg_nabl == 'pass':
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
        record = super(WbmMechanical, self).create(vals)
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
        record = self.env['mechanical.wbm'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
        
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)
                

    


    notes_id = fields.One2many('mechanical.wbm.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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




class WbmDryGradationLine(models.Model):
    _name = "mech.wbm.dry.gradation.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size" )
    wt_retained = fields.Float(string="Wt. Retained in gms")
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained")
    cumulative_retained = fields.Float(string="Cum. Retained %", store=True)
    passing_percent = fields.Float(string="Passing %")



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(WbmDryGradationLine, self).create(vals)

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
                    record.percent_retained = round((vals['wt_retained'] / record.parent_id.total * 100),2) if record.parent_id.total else 0

            new_self = super(WbmDryGradationLine, self).write(vals)

            if 'wt_retained' in vals:
                for record in self:
                    record.parent_id._compute_total_sieve()

            return new_self

        return super(WbmDryGradationLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(WbmDryGradationLine, self).unlink()

        

        return res


    @api.depends('wt_retained', 'parent_id.total_sieve_analysis')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = record.wt_retained / self.parent_id.total_sieve_analysis * 100
            except ZeroDivisionError:
                record.percent_retained = 0


class WbmSpecificGravityWaterAbsorptionLine(models.Model):
    _name = "wbm.specific.gravity.water.absorption.line"
    _description = "Specific Gravity And Water Absorption Test"

    parent_id = fields.Many2one('mechanical.wbm',string="Parent Id")

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

        return super(WbmSpecificGravityWaterAbsorptionLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class WbmCrushingValueLine(models.Model):
    _name = "wbm.crushing.value.line"
    parent_id = fields.Many2one('mechanical.wbm',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)


    w1 = fields.Float("Weight of Mould + Aggregate (W1)")
    w2 = fields.Float("Weight of Empty Mould (W2)")
    w3 = fields.Float("Weight Passing 2.36 mm Sieve (W3)")

    acv = fields.Float(
        string="Crushing Value = W3/(W1-W2)x 100",
        compute="_compute_acv",
        store=True
    )

    @api.depends('w1', 'w2', 'w3')
    def _compute_acv(self):
        for rec in self:
            if (rec.w1 - rec.w2) != 0:
                rec.acv = (rec.w3 / (rec.w1 - rec.w2)) * 100
            else:
                rec.acv = 0.0


    @api.depends('total_wt_aggregate', 'wt_of_aggregate_retained')
    def _compute_wt_of_aggregate_retained(self):
        for rec in self:
            rec.wt_of_aggregate_passing = rec.total_wt_aggregate - rec.wt_of_aggregate_retained


    @api.depends('wt_of_aggregate_passing', 'total_wt_aggregate')
    def _compute_crushing_value(self):
        for rec in self:
            if rec.total_wt_aggregate != 0:
                rec.crushing_value = (rec.wt_of_aggregate_passing / rec.total_wt_aggregate) * 100
            else:
                rec.crushing_value = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(WbmCrushingValueLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class WbmImpactValueLine(models.Model):
    _name = "mech.wbm.impact.line"
    parent_id = fields.Many2one('mechanical.wbm',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

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

        return super(WbmImpactValueLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1



class WbmLAAbrasionLine(models.Model):
    _name = "wbm.la.abrasion.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of oven dry sample before test (W1)")
    w2 = fields.Float("Weight retained on 1.7 mm sieve after test (W2)")

    w3 = fields.Float(
        "Weight passing 1.7 mm sieve (W1 - W2)",
        compute="_compute_values",
        store=True
    )

    la_value = fields.Float(
        "L.A. Abrasion Value (%)",
        compute="_compute_values",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_values(self):
        for rec in self:
            rec.w3 = rec.w1 - rec.w2

            if rec.w1:
                rec.la_value = ((rec.w1 - rec.w2) / rec.w1) * 100
            else:
                rec.la_value = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(WbmLAAbrasionLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class WbmLooseBulkDensityLine(models.Model):
    _name = "wbm.loose.bulk.density.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")
   
    serial_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)

    container_with_material = fields.Float("Weight of Material in Container after pouring, W  (Kg)")

    volume_of_cont = fields.Float(string="Volume of calibrating container ,V (Lit)")
    loose_bulk_density = fields.Float(string="Loose Bulk Density of Material,W/V (Kg/Lit)",compute="_compute_loose_bulk_density")

 

    @api.depends('container_with_material', 'volume_of_cont')
    def _compute_loose_bulk_density(self):
        for record in self:
            if record.volume_of_cont:
                record.loose_bulk_density = record.container_with_material / record.volume_of_cont
            else:
                record.loose_bulk_density = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(WbmLooseBulkDensityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class WbmRoddedBulkDensityLine(models.Model):
    _name = "wbm.rodded.bulk.density.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")
   
    serial_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)

    container_with_material = fields.Float("Weight of Material in Container after pouring, W  (Kg)")

    
    volume_of_cont = fields.Float(string="Volume of calibrating container ,V (Lit)")
    rodded_bulk_density = fields.Float(string="Rodded Bulk Density of Material,W/V (Kg/Lit)",compute="_compute_rodded_bulk_density")

   
    @api.depends('container_with_material', 'volume_of_cont')
    def _compute_rodded_bulk_density(self):
        for record in self:
            if record.volume_of_cont:
                record.rodded_bulk_density = record.container_with_material / record.volume_of_cont
            else:
                record.rodded_bulk_density = 0.0

   
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(WbmRoddedBulkDensityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class WbmDeleteriousClayLine(models.Model):
    _name = "wbm.deleterious.clay.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of total sample (W1)")
    w2 = fields.Float("Weight of clay & lumps separated (W₂)")

    percent = fields.Float(
        "Deleterious Material (%)",
        compute="_compute_percent",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_percent(self):
        for rec in self:
            rec.percent = (rec.w2 / rec.w1) * 100 if rec.w1 else 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(WbmDeleteriousClayLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class WbmDeleteriousSiltDustLine(models.Model):
    _name = "wbm.deleterious.silt.dust.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of total sample (W1)")
    w2 = fields.Float("Weight of Fine Silt and Fine Dust separated (W₂)")

    percent = fields.Float(
        "Deleterious Material (%)",
        compute="_compute_percent",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_percent(self):
        for rec in self:
            rec.percent = (rec.w2 / rec.w1) * 100 if rec.w1 else 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(WbmDeleteriousSiltDustLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class WbmDeleteriousSoftLine(models.Model):
    _name = "wbm.deleterious.soft.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of total sample (W1)")
    w2 = fields.Float("Weight of Fine Soft Fragments (W₂)")

    percent = fields.Float(
        "Deleterious Material (%)",
        compute="_compute_percent",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_percent(self):
        for rec in self:
            rec.percent = (rec.w2 / rec.w1) * 100 if rec.w1 else 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(WbmDeleteriousSoftLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class WbmMaterialFiner75Line(models.Model):
    _name = "wbm.material.finer.75.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of oven dry sample taken (W1)")
    w2 = fields.Float("Weight retained on 75 micron sieve (W2)")

    w3 = fields.Float(
        "Weight passing 75 micron sieve (W1 - W2)",
        compute="_compute_values",
        store=True
    )

    finer_percent = fields.Float(
        "Material Finer than 75 micron (%)",
        compute="_compute_values",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_values(self):
        for rec in self:
            rec.w3 = rec.w1 - rec.w2

            if rec.w1:
                rec.finer_percent = ((rec.w1 - rec.w2) / rec.w1) * 100
            else:
                rec.finer_percent = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(WbmMaterialFiner75Line, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1



class WbmTFVLine(models.Model):
    _name = "wbm.tfv.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    # Inputs
    a = fields.Float("Weight of Saturated surface dry Sample passing IS Sieve 14mm and retained on IS Sieve 10mm (A)")
    retained = fields.Float("Weight retained on 2.36 mm sieve")
    b = fields.Float("WEIGHT PASSING 2.36 MM SIEVE (B) = Weight of Saturated surface dry Sample passing IS Sieve 14 mm and retained on IS Sieve 10mm (A) - Weight Retained on 2.36 mm sieve")
    x = fields.Float("Maximum Force X (kN)")

    # Computed
    y = fields.Float("% Passing (Y)", compute="_compute_values", store=True)
    tfv = fields.Float("10% Fines Value (kN)", compute="_compute_values", store=True)

    @api.depends('a', 'b', 'x')
    def _compute_values(self):
        for rec in self:
            # % Passing
            rec.y = (rec.b / rec.a) * 100 if rec.a else 0.0

            # TFV
            rec.tfv = (14 * rec.x) / (rec.y + 4) if (rec.y + 4) else 0.0

    @api.constrains('a', 'b', 'retained')
    def _check_weights(self):
        for rec in self:
            if rec.a and (rec.retained + rec.b) != rec.a:
                raise ValidationError(
                    "Retained + Passing must equal Total Sample (A)"
                )
            

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(WbmTFVLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class WbmWetImpactValueLine(models.Model):
    _name = "wbm.wet.impact.value.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    # Inputs
    w1 = fields.Float("Weight before soaking (W1)")
    w_ssd = fields.Float("Weight after soaking (SSD)")
    w2 = fields.Float("WEIGHT PASSING ON 2.36 MM = (WIGHT AFTER SOAKING SSD) – (WEIGHT PASSING 2.36 MM (W2))")

    retained = fields.Float(
        "Weight retained on 2.36 mm",
        compute="_compute_values",
        store=True
    )

    impact_value = fields.Float(
        "Wet Impact Value (%)",
        compute="_compute_values",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_values(self):
        for rec in self:
            # Retained (optional calculation)
            rec.retained = rec.w1 - rec.w2

            # Impact Value
            rec.impact_value = (rec.w2 / rec.w1) * 100 if rec.w1 else 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(WbmWetImpactValueLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class WbmSodiumSulphateLine(models.Model):
    _name = "wbm.sodium.sulphate.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

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


class WbmSodiumSulphateTwoLine(models.Model):
    _name = "wbm.sodium.sulphate.two.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

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


class WbmMagnesiumSulphateLine(models.Model):
    _name = "wbm.magnesium.sulphate.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

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


class WbmMagnesiumSulphateTwoLine(models.Model):
    _name = "wbm.magnesium.sulphate.two.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

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






class WbmElongationLine(models.Model):
    _name = "mech.wbm.elongation.flakiness.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

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


class WBMLIQUIDLIMITLINE(models.Model):
    _name = "wbm.liquid.limits.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)
    container_no1 = fields.Char(string="Container No.")
    blwo_no1 = fields.Float(string="No. of Blows")
    wt_of_con_wet = fields.Float(string="Wt. of Container + Wet Soil")
    wt_of_con_dry = fields.Float(string="Wt. of Container + dry Soil")   
    loss_of_moisture = fields.Float(string="Loss of Moisture (gm)",compute="_compute_loss_of_moisture")
    wt_containner = fields.Float(string="Weight of Container")
    wt_of_dry= fields.Float(string="Weight of Dry Soil",compute="_compute_wt_of_dry")
    moisture_content = fields.Float(string="Moisture Content %",compute="_compute_moisture_content")

    @api.depends('wt_of_con_wet', 'wt_of_con_dry')
    def _compute_loss_of_moisture(self):
        for line in self:
            line.loss_of_moisture = line.wt_of_con_wet - line.wt_of_con_dry

    @api.depends('wt_of_con_dry', 'wt_containner')
    def _compute_wt_of_dry(self):
        for line in self:
            line.wt_of_dry = line.wt_of_con_dry - line.wt_containner

    @api.depends('loss_of_moisture', 'wt_of_dry')
    def _compute_moisture_content(self):
        for line in self:
            if line.wt_of_dry != 0:
                line.moisture_content = line.loss_of_moisture / line.wt_of_dry * 100
            else:
                line.moisture_content = 0.0
    

   


    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(WBMLIQUIDLIMITLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class WBMPLASTICLIMITLINE(models.Model):
    _name = "wbm.plasticl.limit.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")


    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)
    container_no = fields.Integer(string="Container No")   
    wt_of_con = fields.Float(string="Weight of container (gm)")
    wt_of_con_wet = fields.Float(string="Weight of container + wet soil (gm)")
    wt_of_con_dry = fields.Float(string="Weight of container + Dry soil (gm)")
    wt_of_water = fields.Float(string="Weight of water in (gm)",compute="_compute_wt_of_water")
    wt_of_oven = fields.Float(string="Weight of ovendry soil (gm)",compute="_compute_wt_of_oven")
    water_content_pastic = fields.Float(string="Water Content (%)",compute="_compute_water_content")


    @api.depends('wt_of_con_wet', 'wt_of_con_dry')
    def _compute_wt_of_water(self):
        for line in self:
            line.wt_of_water = line.wt_of_con_wet - line.wt_of_con_dry


    @api.depends('wt_of_con', 'wt_of_con_dry')
    def _compute_wt_of_oven(self):
        for line in self:
            line.wt_of_oven = line.wt_of_con_dry - line.wt_of_con


    @api.depends('wt_of_water', 'wt_of_oven')
    def _compute_water_content(self):
        for line in self:
            if line.wt_of_oven != 0:
                line.water_content_pastic = line.wt_of_water / line.wt_of_oven * 100
            else:
                line.water_content_pastic = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(WBMPLASTICLIMITLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class WBMHEAVYCOMPACTIONLINE(models.Model):
    _name = "wbm.heavy.compaction.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    amount_soil = fields.Float(string="Amount of soil (gm)")
    amount_water = fields.Integer(string="Amount of water added (%)")
    empty_wt_mould = fields.Integer(string="Empty weight of mould without collar, W1 (gm)")
    wt_soil = fields.Float(string="Weight of soil compacted + mould, W2 (gm)")
    wt_of_wet = fields.Integer(string="Weight of wet soil (W2-W1) (gm)",compute="_compute_wt_of_wet")
    volume_mould = fields.Float(string="Volume of mould (V) (cm3)")
    bulk_density = fields.Float(string=" Bulk density (ρ) (g/cc)",compute="_compute_bulk_density")
    con_no = fields.Float(string="Container Number")
    empty_wt = fields.Float(string="Empty weight of container (M1) (gm)")
    wet_con_ovenwet= fields.Float(string="Weight of container + wet soil (M2) (gm)")
    wet_con_ovendry= fields.Float(string="Weight of container + Weight of oven dry soil (M3) (gm)")
    water_content = fields.Float(string="Water Content (%)",compute="_compute_water_and_dry_density")
    dry_density = fields.Float(string="Dry Density (γd ) (g/cc)",compute="_compute_water_and_dry_density")


    @api.depends('wt_soil', 'empty_wt_mould')
    def _compute_wt_of_wet(self):
        for line in self:
            line.wt_of_wet = line.wt_soil - line.empty_wt_mould



    @api.depends('wt_of_wet', 'volume_mould')
    def _compute_bulk_density(self):
        for line in self:
            if line.volume_mould != 0:
                line.bulk_density = line.wt_of_wet / line.volume_mould
            else:
                line.bulk_density = 0.0


    @api.depends('wet_con_ovendry', 'wet_con_ovenwet', 'empty_wt', 'bulk_density')
    def _compute_water_and_dry_density(self):
        for rec in self:
            m2 = rec.wet_con_ovenwet     # container + wet soil
            m3 = rec.wet_con_ovendry         # container + oven dry soil
            m1 = rec.empty_wt        # empty container

            if m2 and m3 and m1 and (m3 - m1) != 0:
                rec.water_content = ((m2 - m3) / (m3 - m1)) * 100
            else:
                rec.water_content = 0.0

            if rec.bulk_density and rec.water_content is not None:
                rec.dry_density = rec.bulk_density / (1 + (rec.water_content / 100))
            else:
                rec.dry_density = 0.0


  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(WBMHEAVYCOMPACTIONLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class WbmCBRLine(models.Model):
    _name = "wbm.cbr.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    penetration = fields.Float(string="Penetration (mm)")

    

    
    # SAMPLE 1
    sample1_reading = fields.Float(string="Proving ring Reading	1")
    sample1_load = fields.Float(string="Corrected load (Kg) 1", compute="_compute_loads", store=True,digits=(12,3))


    # SAMPLE 2
    sample2_reading = fields.Float(string="Proving ring Reading	2")
    sample2_load = fields.Float(string="Corrected load (Kg) 2", compute="_compute_loads", store=True,digits=(12,3))

    
    # SAMPLE 3
    sample3_reading = fields.Float(string="Proving ring Reading	3")
    sample3_load = fields.Float(string="Corrected load (Kg) 3", compute="_compute_loads", store=True,digits=(12,3))

    
    @api.depends(
        'sample1_reading', 'sample2_reading', 'sample3_reading','parent_id', 'parent_id.proving_ring_cf'
    )
    def _compute_loads(self):
        for rec in self:
            proving_ring_cf = rec.parent_id.proving_ring_cf if rec.parent_id else 0

            if proving_ring_cf:
                rec.sample1_load = (rec.sample1_reading * proving_ring_cf) 
                rec.sample2_load = (rec.sample2_reading * proving_ring_cf) 
                rec.sample3_load = (rec.sample3_reading * proving_ring_cf) 
            else:
                rec.sample1_load = 0.0
                rec.sample2_load = 0.0
                rec.sample3_load = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(WbmCBRLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class WBMLIGHTCOMPACTIONLINE(models.Model):
    _name = "wbm.omc.compaction.line"
    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    amount_soil1 = fields.Float(string="Amount of soil (gm)")
    amount_water1 = fields.Integer(string="Amount of water added (%)")
    empty_wt_mould1 = fields.Integer(string="Empty weight of mould without collar, W1 (gm)")
    wt_soil1 = fields.Float(string="Weight of soil compacted + mould, W2 (gm)")
    wt_of_wet1 = fields.Integer(string="Weight of wet soil (W2-W1) (gm)",compute="_compute_wt_of_wet1")
    volume_mould1 = fields.Float(string="Volume of mould (V) (cm3)")
    bulk_density1 = fields.Float(string=" Bulk density (ρ) (g/cc)",compute="_compute_bulk_density1")
    con_no1 = fields.Float(string="Container Number")
    empty_wt1 = fields.Float(string="Empty weight of container (M1) (gm)")
    wet_con_ovenwet1 = fields.Float(string="Weight of container + wet soil (M2) (gm)")
    wet_con_ovendry1 = fields.Float(string="Weight of container + Weight of oven dry soil (M3) (gm)")
    water_content1 = fields.Float(string="Water Content (%)",compute="_compute_water_and_dry_density1")
    dry_density1 = fields.Float(string="Dry Density (γd ) (g/cc)",compute="_compute_water_and_dry_density1")


    @api.depends('wt_soil1', 'empty_wt_mould1')
    def _compute_wt_of_wet1(self):
        for line in self:
            line.wt_of_wet1 = line.wt_soil1 - line.empty_wt_mould1



    @api.depends('wt_of_wet1', 'volume_mould1')
    def _compute_bulk_density1(self):
        for line in self:
            if line.volume_mould1 != 0:
                line.bulk_density1 = line.wt_of_wet1 / line.volume_mould1
            else:
                line.bulk_density1 = 0.0


    @api.depends('wet_con_ovendry1', 'wet_con_ovenwet1', 'empty_wt1', 'bulk_density1')
    def _compute_water_and_dry_density1(self):
        for rec in self:
            m2 = rec.wet_con_ovenwet1     # container + wet soil
            m3 = rec.wet_con_ovendry1         # container + oven dry soil
            m1 = rec.empty_wt1        # empty container

            if m2 and m3 and m1 and (m3 - m1) != 0:
                rec.water_content1 = ((m2 - m3) / (m3 - m1)) * 100
            else:
                rec.water_content1 = 0.0

            if rec.bulk_density1 and rec.water_content1 is not None:
                rec.dry_density1 = rec.bulk_density1 / (1 + (rec.water_content1 / 100))
            else:
                rec.dry_density1 = 0.0


  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(WBMLIGHTCOMPACTIONLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class WbmMechanicalNotes(models.Model):
    _name = "mechanical.wbm.notes"

    parent_id = fields.Many2one('mechanical.wbm', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
