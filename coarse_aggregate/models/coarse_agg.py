from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import matplotlib.pyplot as plt
import io
import base64
import matplotlib.ticker as ticker
import numpy as np
import math
from scipy.interpolate import CubicSpline , interp1d , Akima1DInterpolator
from scipy.optimize import minimize_scalar
from io import BytesIO
from scipy.interpolate import make_interp_spline
from matplotlib.ticker import LogLocator, MultipleLocator
import re
from scipy.interpolate import PchipInterpolator



class CoarseAggregateMechanical(models.Model):
    _name = "mechanical.coarse.aggregate"
    _inherit = "lerm.eln"
    _description = 'mechanical.coarse.aggregate'
    _rec_name = "name"

    name = fields.Char("Name",default="Coarse Aggregate")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    size_id = fields.Many2one('lerm.size.line',compute="_compute_size_id")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    avg_compacted_unit  = fields.Char("Compacted Density", compute="_compute_units", store=False)

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'coarse.aggregate.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }
    


     # ---- helper method
    def _get_unit(self, internal_id):
        param = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', internal_id)
        ], limit=1)
        return param.unit.name if param.unit else ""


        # ---- compute fields (unit बदलल्यावर update)
    def _compute_units(self):
        for rec in self:
            # rec.average_crushing_value_unit = rec._get_unit("ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71")
            # rec.average_impact_value_unit = rec._get_unit("2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2")
            rec.avg_compacted_unit     = rec._get_unit("357f579d-a310-4015-bc11-28a85c53ac83")
            # rec.avg_bulk_density_unit   = rec._get_unit("65a41d1f-d557-438e-8fd1-2c619a334d02")
            # rec.aggregate_elongation_unit   = rec._get_unit("9effe915-e5a3-45a7-aaeb-10caababd667")
            # rec.aggregate_flakiness_unit   = rec._get_unit("be7a60bc-bb2c-410d-b91a-4f8730a4ac6f")
            # rec.avg_specific_gravity_unit   = rec._get_unit("3114db41-cfa7-49ad-9324-fcdbc9661038")
            # rec.avg_water_absorption_unit   = rec._get_unit("22ee804f-41a3-4fd1-a301-a8d9180fba10")

    # ---- default values (create mode मध्ये दिसण्यासाठी)
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res.update({
            # 'average_crushing_value_unit':   self._get_unit("ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71"),
            # 'average_impact_value_unit': self._get_unit("2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2"),
            'avg_compacted_unit':     self._get_unit("357f579d-a310-4015-bc11-28a85c53ac83"),
            # 'avg_bulk_density_unit':   self._get_unit("65a41d1f-d557-438e-8fd1-2c619a334d02"),
            # 'aggregate_elongation_unit':   self._get_unit("9effe915-e5a3-45a7-aaeb-10caababd667"),
            # 'aggregate_flakiness_unit':   self._get_unit("be7a60bc-bb2c-410d-b91a-4f8730a4ac6f"),
            # 'avg_specific_gravity_unit':   self._get_unit("3114db41-cfa7-49ad-9324-fcdbc9661038"),
            # 'avg_water_absorption_unit':   self._get_unit("22ee804f-41a3-4fd1-a301-a8d9180fba10"),
        })
        return res


    @api.depends("eln_ref")
    def _compute_size_id(self):
        for record in self:
            print("Size iD",record.eln_ref.size_id)
            record.size_id = record.eln_ref.size_id.id


    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

        
    def get_all_fields(self):
        record = self.env['mechanical.coarse.aggregate'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



    # Crushing Value 

    temp_crushing_value = fields.Char(string="Temp.°C")
    humidity_crushing_value= fields.Char(string="Humidity %")

    crushing_value_name = fields.Char("Name",default="Crushing Value")
    crushing_visible = fields.Boolean("Crushing Visible",compute="_compute_visible")


    wt_of_empty_cylinder = fields.Float(string="Weight of Empty Cylinder (W1) – gms.")
    wt_of_cylinder_aggregate = fields.Float(string="Weight of Cylinder + Aggregate (W2) – gms.")

    wt_of_aggregate_crush = fields.Float(string="Weight of Aggregate (A) = (W2 – W1) – gms",compute="_compute_wt_of_aggregate_crush")

    wt_of_aggregate_passing_sieve = fields.Float(string="Weight of Aggregate Passing Sieve (B) – gms.")

    aggregate_crushing_value = fields.Float(string="Aggregate Crushing Value in % = (B/A)x100",compute="_compute_aggregate_crushing_value")


    @api.depends('wt_of_empty_cylinder', 'wt_of_cylinder_aggregate')
    def _compute_wt_of_aggregate_crush(self):
        for rec in self:
            rec.wt_of_aggregate_crush = rec.wt_of_cylinder_aggregate - rec.wt_of_empty_cylinder

    @api.depends('wt_of_aggregate_passing_sieve', 'wt_of_aggregate_crush')
    def _compute_aggregate_crushing_value(self):
        for rec in self:
            if rec.wt_of_aggregate_crush != 0:
              rec.aggregate_crushing_value = (rec.wt_of_aggregate_passing_sieve / rec.wt_of_aggregate_crush) * 100
            else:
              rec.aggregate_crushing_value =0.0



    wt_of_empty_cylinder_2 = fields.Float(string="Weight of Empty Cylinder (W1) – gms.")
    wt_of_cylinder_aggregate_2 = fields.Float(string="Weight of Cylinder + Aggregate (W2) – gms.")

    wt_of_aggregate_crush_2 = fields.Float(string="Weight of Aggregate (A) = (W2 – W1) – gms",compute="_compute_wt_of_aggregate_crush_2")

    wt_of_aggregate_passing_sieve_2 = fields.Float(string="Weight of Aggregate Passing Sieve (B) – gms.")

    aggregate_crushing_value_2 = fields.Float(string="Aggregate Crushing Value in % = (B/A)x100",compute="_compute_aggregate_crushing_value_2")


    @api.depends('wt_of_empty_cylinder_2', 'wt_of_cylinder_aggregate_2')
    def _compute_wt_of_aggregate_crush_2(self):
        for rec in self:
            rec.wt_of_aggregate_crush_2 = rec.wt_of_cylinder_aggregate_2 - rec.wt_of_empty_cylinder_2

    @api.depends('wt_of_aggregate_crush_2', 'wt_of_aggregate_passing_sieve_2')
    def _compute_aggregate_crushing_value_2(self):
        for rec in self:
            if rec.wt_of_aggregate_crush_2 != 0:
              rec.aggregate_crushing_value_2 = (rec.wt_of_aggregate_passing_sieve_2 / rec.wt_of_aggregate_crush_2) * 100
            else:
               rec.aggregate_crushing_value_2 =0.0

    average_crushing_value = fields.Float(string="Average Aggregate Crushing Value", compute="_compute_average_crushing_value")

    @api.depends('aggregate_crushing_value', 'aggregate_crushing_value_2')
    def _compute_average_crushing_value(self):
        for rec in self:
              rec.average_crushing_value = (rec.aggregate_crushing_value + rec.aggregate_crushing_value_2) /2




    average_crushing_value_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),], string="Conformity", compute="_compute_average_crushing_value_conformity", store=True)

    @api.depends('average_crushing_value','eln_ref','grade')
    def _compute_average_crushing_value_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_crushing_value_conformity = 'na'
                continue
            record.average_crushing_value_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
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





    # Specific Gravity 
    temp_specific_water = fields.Char(string="Temp.°C")
    humidity_specific_water= fields.Char(string="Humidity %")

    specific_gravity_name = fields.Char("Name",default="Specific Gravity & Water Absorption")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    water_absorption_name = fields.Char("Name",default="Specific Gravity & Water Absorption")
    water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")



    wt_basket_and_sample = fields.Float(string="Weight of basket and the sample while suspended in water (A1) gm")
    wt_empty_basket= fields.Float(string="Weight of empty basket in water (A2) gm")

    wt_surface_dry = fields.Float(string="Weight of surface dried aggregate (B) gm")
    wt_sample_inwater = fields.Float(string="Weight of Saturated Aggregate  in Water (A) = (A1 – A2) – gms", compute="_compute_wt_sample_inwater")
    oven_dried_wt = fields.Float(string="Weight of  oven dried aggregates (C) gm")

    # Trial 2 (new)
    wt_basket_and_sample_2 = fields.Float(string="Weight of basket and the sample while suspended in water (A1) gm  [Trial 2]")
    wt_empty_basket_2= fields.Float(string="Weight of empty basket in water (A2) gm  [Trial 2]")

    wt_surface_dry_2 = fields.Float(string="Weight of surface dried aggregate (B) gm [Trial 2]")
    wt_sample_inwater_2 = fields.Float(string="Weight of Saturated Aggregate  in Water (A) = (A1 – A2) – gms [Trial 2]", compute="_compute_wt_sample_inwater_2")
    oven_dried_wt_2 = fields.Float(string="Weight of  oven dried aggregates (C) gm [Trial 2]")


    @api.depends('wt_basket_and_sample', 'wt_empty_basket')
    def _compute_wt_sample_inwater(self):
        for line in self:
            if line.wt_basket_and_sample and line.wt_empty_basket:
                line.wt_sample_inwater = line.wt_basket_and_sample - line.wt_empty_basket
            else:
              line.wt_sample_inwater = 0

    @api.depends('wt_basket_and_sample_2', 'wt_empty_basket_2')
    def _compute_wt_sample_inwater_2(self):
        for line in self:
            if line.wt_basket_and_sample_2 and line.wt_empty_basket_2:
                line.wt_sample_inwater_2 = line.wt_basket_and_sample_2 - line.wt_empty_basket_2
            else:
               line.wt_sample_inwater_2 = 0

    # result_wt_surface_dry = fields.Float(string="Wt of Saturated surface dry  Aggregate in Air:- (B)",compute="_compute_result")
    # result_wt_sample_inwater = fields.Float(string="Wt of Saturated Aggregate in Water:- (A)",compute="_compute_result")
    # result_oven_dried_wt = fields.Float(string="Wt of Oven Dried Aggregate in Air :- (C)",compute="_compute_result")

    specific_gravity = fields.Float(string="Specific Gravity",compute="_compute_specific_gravity")
    water_absorption = fields.Float(string="Water absorption  %",compute="_compute_water_absorption")


    specific_gravity_1 = fields.Float(string="Specific Gravity",compute="_compute_specific_gravity_1",digits=(16, 3))
    water_absorption_1 = fields.Float(string="Water absorption  %",compute="_compute_water_absorption_1")


    @api.depends('wt_surface_dry', 'wt_sample_inwater', 'oven_dried_wt')
    def _compute_specific_gravity_1(self):
        for line in self:
            if line.wt_surface_dry - line.wt_sample_inwater != 0:
                line.specific_gravity_1  = line.oven_dried_wt / (line.wt_surface_dry - line.wt_sample_inwater)
            else:
                line.specific_gravity_1 = 0

            # line.specific_gravity_1 = round(sg1, 2)

    @api.depends('wt_surface_dry', 'oven_dried_wt','wt_surface_dry_2', 'oven_dried_wt_2')
    def _compute_water_absorption_1(self):
        for line in self:
            if line.oven_dried_wt != 0:
                line.water_absorption_1 = ((line.wt_surface_dry - line.oven_dried_wt) / line.oven_dried_wt) * 100
            else:
                line.water_absorption_1 = 0
            # line.water_absorption = round(wa1, 2)

    specific_gravity_2 = fields.Float(string="Specific Gravity",compute="_compute_specific_gravity_2" ,digits=(16, 3))
    water_absorption_2 = fields.Float(string="Water absorption  %",compute="_compute_water_absorption_2")

    @api.depends('wt_surface_dry_2', 'wt_sample_inwater_2', 'oven_dried_wt_2')
    def _compute_specific_gravity_2(self):
        for line in self:
            if line.wt_surface_dry_2 - line.wt_sample_inwater_2 != 0:
                line.specific_gravity_2 = line.oven_dried_wt_2 / (line.wt_surface_dry_2 - line.wt_sample_inwater_2)
            else:
                line.specific_gravity_2 = 0
            # line.specific_gravity_2 = round(sg1, 2)

    @api.depends('wt_surface_dry_2', 'oven_dried_wt_2')
    def _compute_water_absorption_2(self):
        for line in self:
            if line.oven_dried_wt_2 != 0:
                line.water_absorption_2 = ((line.wt_surface_dry_2 - line.oven_dried_wt_2) / line.oven_dried_wt_2) * 100
            else:
                line.water_absorption_2 = 0
            # line.water_absorption = round(wa1, 2)


    avg_specific_gravity= fields.Float(string="Average Specific Gravity",compute="_compute_avg_specific_gravity")
    avg_water_absorption = fields.Float(string="Average Water Absorption-%",compute="_compute_avg_water_absorption")

    @api.depends('specific_gravity_1','specific_gravity_2')
    def _compute_avg_specific_gravity(self):
        for line in self:
            line.avg_specific_gravity = (line.specific_gravity_1 + line.specific_gravity_2)/2
    
    @api.depends('water_absorption_1','water_absorption_2')
    def _compute_avg_water_absorption(self):
        for line in self:
            line.avg_water_absorption = (line.water_absorption_1 + line.water_absorption_2)/2

    @api.depends('wt_surface_dry', 'wt_sample_inwater', 'oven_dried_wt', 'wt_surface_dry_2', 'wt_sample_inwater_2', 'oven_dried_wt_2')
    def _compute_result(self):
        for line in self:
            line.result_wt_surface_dry = (line.wt_surface_dry + line.wt_surface_dry_2)/2
            line.result_wt_sample_inwater = (line.wt_sample_inwater + line.wt_sample_inwater_2)/2
            line.result_oven_dried_wt = (line.oven_dried_wt + line.oven_dried_wt_2)/2

    avg_specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Specific Gravity Conformity", compute="_compute_avg_specific_gravity_conformity", store=True)

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_specific_gravity_conformity = 'na'
                continue
            record.avg_specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3114db41-cfa7-49ad-9324-fcdbc9661038')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3114db41-cfa7-49ad-9324-fcdbc9661038')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
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
        ('fail', 'Non-NABL')], string=" Specific Gravity NABL", compute="_compute_avg_specific_gravity_nabl", store=True)

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_nabl(self):
        
        for record in self:
            record.avg_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3114db41-cfa7-49ad-9324-fcdbc9661038')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3114db41-cfa7-49ad-9324-fcdbc9661038')]).parameter_table
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
            ('fail', 'Fail'),('na', 'NA'),
            ], string="Water Absorption Conformity", compute="_compute_avg_water_absorption_conformity", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_water_absorption_conformity = 'na'
                continue
            record.avg_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','22ee804f-41a3-4fd1-a301-a8d9180fba10')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','22ee804f-41a3-4fd1-a301-a8d9180fba10')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
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
        ('fail', 'Non-NABL')], string="Water Absorption NABL", compute="_compute_avg_water_absorption_nabl", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_nabl(self):
        
        for record in self:
            record.avg_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','22ee804f-41a3-4fd1-a301-a8d9180fba10')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','22ee804f-41a3-4fd1-a301-a8d9180fba10')]).parameter_table
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



    


    # Impact Value 

    temp_impact_value = fields.Char(string="Temp.°C")
    humidity_impact_value= fields.Char(string="Humidity %")

    impact_value_name = fields.Char("Name",default=" Impact Value")
    impact_visible = fields.Boolean("Impact Visible",compute="_compute_visible")


    wt_of_empty_cup = fields.Float(string="Weight of Empty Cup (W1) – gms.		")
    wt_of_cup_aggregate = fields.Float(string="Weight of Cup + Aggregate (W2) – gms.")

    wt_of_aggregate = fields.Float(string="Weight of Aggregate (A) = (W2 – W1) – gms", compute="_compute_wt_of_aggregate")

    wt_of_aggregate_passing = fields.Float(string="Weight of Aggregate Passing 2.36 mm Sieve (B) – gms.")
    wt_of_aggregate_retained = fields.Float(string="Weight of Aggregate Retained on 2.36 mm Sieve (C) – gms.(A-B)", compute="_compute_wt_of_aggregate_retained")

    total_wt_pass_retained = fields.Float(string="Total Weight Passing + Retained on 2.36 mm Sieve (B+C) – gms.", compute="_compute_total_wt_pass_retained")

    aggregate_impact_value = fields.Float(string="Aggregate Impact Value of Aggregate in % = (B/A)x100", compute="_compute_aggregate_impact_value")

    @api.depends('wt_of_empty_cup', 'wt_of_cup_aggregate')
    def _compute_wt_of_aggregate(self):
        for rec in self:
            rec.wt_of_aggregate = rec.wt_of_cup_aggregate - rec.wt_of_empty_cup
    
    @api.depends('wt_of_aggregate_passing', 'wt_of_aggregate')
    def _compute_wt_of_aggregate_retained(self):
        for rec in self:
            rec.wt_of_aggregate_retained = rec.wt_of_aggregate - rec.wt_of_aggregate_passing

    @api.depends('wt_of_aggregate_passing', 'wt_of_aggregate_retained')
    def _compute_total_wt_pass_retained(self):
        for rec in self:
            rec.total_wt_pass_retained = rec.wt_of_aggregate_passing + rec.wt_of_aggregate_retained

    @api.depends('wt_of_aggregate_passing', 'wt_of_aggregate')
    def _compute_aggregate_impact_value(self):
        for rec in self:
            if rec.wt_of_aggregate != 0 :
              rec.aggregate_impact_value = (rec.wt_of_aggregate_passing / rec.wt_of_aggregate) * 100
            else:
                rec.aggregate_impact_value = 0.0


    wt_of_empty_cup_2 = fields.Float(string="Weight of Empty Cup (W1) – gms.	")
    wt_of_cup_aggregate_2 = fields.Float(string="Weight of Cup + Aggregate (W2) – gms.")

    wt_of_aggregate_2 = fields.Float(string="Weight of Aggregate (A) = (W2 – W1) – gms", compute="_compute_wt_of_aggregate_2")

    wt_of_aggregate_passing_2 = fields.Float(string="Weight of Aggregate Passing 2.36 mm Sieve (B) – gms.")
    wt_of_aggregate_retained_2 = fields.Float(string="Weight of Aggregate Retained on 2.36 mm Sieve (C) – gms.(A-B)", compute="_compute_wt_of_aggregate_retained_2")

    total_wt_pass_retained_2 = fields.Float(string="Total Weight Passing + Retained on 2.36 mm Sieve (B+C) – gms.", compute="_compute_total_wt_pass_retained_2")

    aggregate_impact_value_2 = fields.Float(string="Aggregate Impact Value of Aggregate in % = (B/A)x100", compute="_compute_aggregate_impact_value_2")

    @api.depends('wt_of_empty_cup_2', 'wt_of_cup_aggregate_2')
    def _compute_wt_of_aggregate_2(self):
        for rec in self:
            rec.wt_of_aggregate_2 = rec.wt_of_cup_aggregate_2 - rec.wt_of_empty_cup_2
    
    @api.depends('wt_of_aggregate_passing_2', 'wt_of_aggregate_2')
    def _compute_wt_of_aggregate_retained_2(self):
        for rec in self:
            rec.wt_of_aggregate_retained_2 = rec.wt_of_aggregate_2 - rec.wt_of_aggregate_passing_2

    @api.depends('wt_of_aggregate_passing_2', 'wt_of_aggregate_retained_2')
    def _compute_total_wt_pass_retained_2(self):
        for rec in self:
            rec.total_wt_pass_retained_2 = rec.wt_of_aggregate_passing_2 + rec.wt_of_aggregate_retained_2

    @api.depends('wt_of_aggregate_passing_2', 'wt_of_aggregate_2')
    def _compute_aggregate_impact_value_2(self):
        for rec in self:
            if rec.wt_of_aggregate_2 != 0 :
              rec.aggregate_impact_value_2 = (rec.wt_of_aggregate_passing_2 / rec.wt_of_aggregate_2) * 100
            else:
                rec.aggregate_impact_value_2 = 0.0

    average_impact_value = fields.Float(string="Average Impact Value - %", compute="_compute_average_impact_value")



    @api.depends('aggregate_impact_value','aggregate_impact_value_2')
    def _compute_average_impact_value(self):
        for record in self:
            if record.aggregate_impact_value and record.aggregate_impact_value_2 :
                record.average_impact_value = (record.aggregate_impact_value + record.aggregate_impact_value_2)/2
            else:
                record.average_impact_value = 0.0



    average_impact_value_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_average_impact_value_conformity", store=True)

    @api.depends('average_impact_value','eln_ref','grade')
    def _compute_average_impact_value_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_impact_value_conformity = 'na'
                continue
            record.average_impact_value_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
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

    impact_value_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_impact_value_nabl", store=True)

    @api.depends('average_impact_value','eln_ref','grade')
    def _compute_average_impact_value_nabl(self):
        
        for record in self:
            record.impact_value_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2')]).parameter_table
            # for material in materials:
                # if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_impact_value - record.average_impact_value*mu_value
            upper = record.average_impact_value + record.average_impact_value*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.impact_value_nabl = 'pass'
                break
            else:
                record.impact_value_nabl = 'fail'


    
   
    # !0% Fine Value

    temp_fine_value = fields.Char(string="Temp.°C")
    humidity_fine_value= fields.Char(string="Humidity %")

    name_10fine = fields.Char(default="10% Fine Value")
    fine10_visible = fields.Boolean("10% Fine Visible",compute="_compute_visible")

    wt_of_empty_cylinder_10fine = fields.Float(string="Weight of Empty Cylinder (W1) – gms.")
    wt_of_cylinder_aggregate_10fine = fields.Float(string="Weight of Cylinder + Aggregate (W2) – gms.")
    wt_of_aggregate_crush_10fine = fields.Float(string="Weight of Aggregate (A) = (W2 – W1) – gms",compute="_compute_wt_of_aggregate_crush_10fine")
    wt_of_aggregate_passing_sieve_10fine = fields.Float(string="Weight of Aggregate Passing 2.36 mm Sieve (B) – gms.")
    
    percent_fine_passing_sieve = fields.Float(string="% Fines Passing Through Sieve (Y)  = (B/A)x100",compute="_compute_percent_fine_passing_sieve")

    load_for_penetration_kn = fields.Float(string="Load Required for Penetration (X) – kn")
    load_for_penetration_tonnes = fields.Float(string="Load Required for Penetration (X) – tonnes	",compute="_compute_load_for_penetration_tonnes")

    load_for_10fine = fields.Float(string="Load Required For 10 % Fines ",compute="_compute_load_for_10fine")

    @api.depends('wt_of_empty_cylinder_10fine','wt_of_cylinder_aggregate_10fine')
    def _compute_wt_of_aggregate_crush_10fine(self):
        for record in self:
            record.wt_of_aggregate_crush_10fine = record.wt_of_cylinder_aggregate_10fine - record.wt_of_empty_cylinder_10fine


    @api.depends('wt_of_aggregate_passing_sieve_10fine', 'wt_of_aggregate_crush_10fine')
    def _compute_percent_fine_passing_sieve(self):
        for rec in self:
            if rec.wt_of_aggregate_crush_10fine != 0:
              rec.percent_fine_passing_sieve = (rec.wt_of_aggregate_passing_sieve_10fine / rec.wt_of_aggregate_crush_10fine) * 100
            else:
              rec.percent_fine_passing_sieve =0.0

    @api.depends('load_for_penetration_kn')
    def _compute_load_for_penetration_tonnes(self):
        for record in self:
            record.load_for_penetration_tonnes =round (record.load_for_penetration_kn * 0.10197,2)


    # @api.depends('wt_of_aggregate_passing_sieve_10fine', 'wt_of_aggregate_crush_10fine')
    # def _compute_load_for_10fine(self):
    #     for rec in self:
    #         if (rec.percent_fine_passing_sieve + 4) != 0:
    #             rec.load_for_10fine = round( ((14 * rec.load_for_penetration_tonnes )/ (rec.percent_fine_passing_sieve + 4)) ,2)
 
    #         else:
    #             rec.load_for_10fine = 0.0

    @api.depends('load_for_penetration_kn', 'percent_fine_passing_sieve')
    def _compute_load_for_10fine(self):
      for rec in self:
        # use tonnes (but calculate live from kN to avoid lag)
        tonnes = rec.load_for_penetration_kn * 0.10197
        if (rec.percent_fine_passing_sieve + 4) != 0:
            rec.load_for_10fine = round((14 * tonnes) / (rec.percent_fine_passing_sieve + 4), 2)
        else:
            rec.load_for_10fine = 0.0




    wt_of_empty_cylinder_10fine_2 = fields.Float(string="Weight of Empty Cylinder (W1) – gms.")
    wt_of_cylinder_aggregate_10fine_2 = fields.Float(string="Weight of Cylinder + Aggregate (W2) – gms.")
    wt_of_aggregate_crush_10fine_2 = fields.Float(string="Weight of Aggregate (A) = (W2 – W1) – gms",compute="_compute_wt_of_aggregate_crush_10fine_2")
    wt_of_aggregate_passing_sieve_10fine_2 = fields.Float(string="Weight of Aggregate Passing 2.36 mm Sieve (B) – gms.")
    
    percent_fine_passing_sieve_2 = fields.Float(string="% Fines Passing Through Sieve (Y)  = (B/A)x100",compute="_compute_percent_fine_passing_sieve_2")

    load_for_penetration_kn_2 = fields.Float(string="Load Required for Penetration (X) – kn")
    load_for_penetration_tonnes_2 = fields.Float(string="Load Required for Penetration (X) – tonnes	",compute="_compute_load_for_penetration_tonnes_2")

    load_for_10fine_2 = fields.Float(string="Load Required For 10 % Fines ",compute="_compute_load_for_10fine_2")

    @api.depends('wt_of_empty_cylinder_10fine_2','wt_of_cylinder_aggregate_10fine_2')
    def _compute_wt_of_aggregate_crush_10fine_2(self):
        for record in self:
            record.wt_of_aggregate_crush_10fine_2 = record.wt_of_cylinder_aggregate_10fine_2 - record.wt_of_empty_cylinder_10fine_2


    @api.depends('wt_of_aggregate_passing_sieve_10fine_2', 'wt_of_aggregate_crush_10fine_2')
    def _compute_percent_fine_passing_sieve_2(self):
        for rec in self:
            if rec.wt_of_aggregate_crush_10fine_2 != 0:
              rec.percent_fine_passing_sieve_2 = (rec.wt_of_aggregate_passing_sieve_10fine_2 / rec.wt_of_aggregate_crush_10fine_2) * 100
            else:
              rec.percent_fine_passing_sieve_2 =0.0

    @api.depends('load_for_penetration_kn_2')
    def _compute_load_for_penetration_tonnes_2(self):
        for record in self:
            record.load_for_penetration_tonnes_2 =round (record.load_for_penetration_kn_2 * 0.10197,2)


    # @api.depends('wt_of_aggregate_passing_sieve_10fine_2', 'wt_of_aggregate_crush_10fine_2')
    # def _compute_load_for_10fine_2(self):
    #     for rec in self:
    #         if (rec.percent_fine_passing_sieve_2 + 4) != 0:
    #           rec.load_for_10fine_2 = round( ((14 * rec.load_for_penetration_tonnes_2 )/ (rec.percent_fine_passing_sieve_2 + 4)) ,2)

    #         else:
    #             rec.load_for_10fine_2 = 0.0     

    @api.depends('load_for_penetration_kn_2', 'percent_fine_passing_sieve_2')
    def _compute_load_for_10fine_2(self):
     for rec in self:
        tonnes_2 = rec.load_for_penetration_kn_2 * 0.10197
        if (rec.percent_fine_passing_sieve_2 + 4) != 0:
            rec.load_for_10fine_2 = round((14 * tonnes_2) / (rec.percent_fine_passing_sieve_2 + 4), 2)
        else:
            rec.load_for_10fine_2 = 0.0





    avg_load_for_10fine=  fields.Float(string="Average Load Required For 10 % Fines – tonnes ",compute="_compute_avg_load_for_10fine")

    @api.depends('load_for_10fine', 'load_for_10fine_2')
    def _compute_avg_load_for_10fine(self):
        for rec in self:
              rec.avg_load_for_10fine = (rec.load_for_10fine + rec.load_for_10fine_2) /2






    # @api.depends('percent_of_fines','load_applied_10fine')
    # def _compute_load_10percent_fine_values(self):
    #     for record in self:
    #         if record.percent_of_fines != 0:
    #             record.load_10percent_fine_values = (14 * record.load_applied_10fine)/(record.percent_of_fines + 4)
    #         else:
    #             record.load_10percent_fine_values = 0


    avg_load_for_10fine_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_avg_load_for_10fine_conformity", store=True)

    @api.depends('avg_load_for_10fine','eln_ref','grade')
    def _compute_avg_load_for_10fine_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_load_for_10fine_conformity = 'na'
                continue
            record.avg_load_for_10fine_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f506c08-4369-491d-93a6-030514c29661')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f506c08-4369-491d-93a6-030514c29661')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_load_for_10fine - record.avg_load_for_10fine*mu_value
                    upper = record.avg_load_for_10fine + record.avg_load_for_10fine*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_load_for_10fine_conformity = 'pass'
                        break
                    else:
                        record.avg_load_for_10fine_conformity = 'fail'

    avg_load_for_10fine_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_load_for_10fine_nabl", store=True)

    @api.depends('avg_load_for_10fine','eln_ref','grade')
    def _compute_avg_load_for_10fine_nabl(self):
        
        for record in self:
            record.avg_load_for_10fine_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f506c08-4369-491d-93a6-030514c29661')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f506c08-4369-491d-93a6-030514c29661')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_load_for_10fine - record.avg_load_for_10fine*mu_value
                    upper = record.avg_load_for_10fine + record.avg_load_for_10fine*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_load_for_10fine_nabl = 'pass'
                        break
                    else:
                        record.avg_load_for_10fine_nabl = 'fail'

    






     #  Elongation Index
    temp_elongation = fields.Char(string="Temp.°C")
    humidity_elongation= fields.Char(string="Humidity %")

    elongation_name = fields.Char(default="Elongation Index")
    elongation_visible = fields.Boolean(compute="_compute_visible")

    elongation_table = fields.One2many('mechanical.elongation.index.line','parent_id',string="Elongation Index",default=lambda self: self.default_elongation_sizes())

    total_weight_retained_el = fields.Float('Total Weight Retained on each Sieve (W’n) gms',compute="_compute_total_weight_retained_el",store=True)
    total_percent_retained_el = fields.Float('Total % Retained on each Sieve X’n',compute="_compute_total_percent_retained_el",store=True)

    total_weight_retained_mat_elongated = fields.Float('Total Weight Retained Elongated Material (P’n) gms',compute="_compute_total_weight_retained_mat_elongated",store=True)

    total_percent_retained_material = fields.Float('Total % Retained Material Y’n',compute="_compute_total_percent_retained_material", store=True)
    total_total_percent_retained_el = fields.Float('Total (X’n x Y’n)',compute="_compute_total_total_percent_retained_el" , store=True)

    elongation_index = fields.Float('Elongation Index (%)',compute="_compute_elongation_index")





    @api.model
    def default_elongation_sizes(self):
        default_lines = [
            (0, 0, {'sieve_size_passing': '63','sieve_size_retained':'50','length_gauge':'0','weight_retained_el_char':'--','percent_retained_el_char':'--','weight_retained_mat_elongated_char':'--','percent_retained_material_cha':'--'}),
            (0, 0, {'sieve_size_passing': '50','sieve_size_retained':'40','length_gauge':'81','weight_retained_el_char':'W’1','percent_retained_el_char':'X’1','weight_retained_mat_elongated_char':'P’1','percent_retained_material_cha':'Y’1'}),
            (0, 0, {'sieve_size_passing': '40','sieve_size_retained':'31.5','length_gauge':'64.4','weight_retained_el_char':'W’2','percent_retained_el_char':'X’2','weight_retained_mat_elongated_char':'P’2','percent_retained_material_cha':'Y’2'}),
            (0, 0, {'sieve_size_passing': '31.5','sieve_size_retained':'25','length_gauge':'0','weight_retained_el_char':'--','percent_retained_el_char':'--','weight_retained_mat_elongated_char':'--','percent_retained_material_cha':'--'}),
            (0, 0, {'sieve_size_passing': '25','sieve_size_retained':'20', 'length_gauge':'40.5','weight_retained_el_char':'W’3','percent_retained_el_char':'X’3','weight_retained_mat_elongated_char':'P’3','percent_retained_material_cha':'Y’3'}),
            (0, 0, {'sieve_size_passing': '20','sieve_size_retained':'16','length_gauge':'32.4','weight_retained_el_char':'W’4','percent_retained_el_char':'X’4','weight_retained_mat_elongated_char':'P’4','percent_retained_material_cha':'Y’4'}),
            (0, 0, {'sieve_size_passing': '16','sieve_size_retained':'12.5','length_gauge':'25.6','weight_retained_el_char':'W’5','percent_retained_el_char':'X’5','weight_retained_mat_elongated_char':'P’5','percent_retained_material_cha':'Y’5'}),
            (0, 0, {'sieve_size_passing': '12.5','sieve_size_retained':'10','length_gauge':'20.2','weight_retained_el_char':'W’6','percent_retained_el_char':'X’6','weight_retained_mat_elongated_char':'P’6','percent_retained_material_cha':'Y’6'}),
            (0, 0, {'sieve_size_passing': '10','sieve_size_retained':'6.3','length_gauge':'14.7','weight_retained_el_char':'W’7','percent_retained_el_char':'X’7','weight_retained_mat_elongated_char':'P’7','percent_retained_material_cha':'Y’7'}),
            
        ]
        return default_lines   

    @api.depends('elongation_table.weight_retained_el')
    def _compute_total_weight_retained_el(self):
        for record in self:
            record.total_weight_retained_el = sum(record.elongation_table.mapped('weight_retained_el'))

    @api.depends('elongation_table.percent_retained_el')
    def _compute_total_percent_retained_el(self):
        for record in self:
            record.total_percent_retained_el = sum(record.elongation_table.mapped('percent_retained_el'))

    
    @api.depends('elongation_table.weight_retained_mat_elongated')
    def _compute_total_weight_retained_mat_elongated(self):
        for record in self:
            record.total_weight_retained_mat_elongated = sum(record.elongation_table.mapped('weight_retained_mat_elongated'))

    @api.depends('elongation_table.percent_retained_material')
    def _compute_total_percent_retained_material(self):
        for record in self:
            record.total_percent_retained_material = sum(record.elongation_table.mapped('percent_retained_material'))

    @api.depends('elongation_table.total_percent_retained_el')
    def _compute_total_total_percent_retained_el(self):
        for record in self:
            record.total_total_percent_retained_el = sum(record.elongation_table.mapped('total_percent_retained_el'))

    

    @api.depends('total_total_percent_retained_el')
    def _compute_elongation_index(self):
        for record in self:
            record.elongation_index = round(record.total_total_percent_retained_el / 100,2)

    def action_compute_elongation_index(self):
     for record in self:
        if record.total_total_percent_retained_el:
            record.elongation_index = round(record.total_total_percent_retained_el / 100, 2)
        else:
            record.elongation_index = 0.0
    
    elongation_index_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_elongation_index_conformity", store=True)

    @api.depends('elongation_index','eln_ref','grade')
    def _compute_elongation_index_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.elongation_index_conformity = 'na'
                continue
            record.elongation_index_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9effe915-e5a3-45a7-aaeb-10caababd667')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9effe915-e5a3-45a7-aaeb-10caababd667')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
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
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_elongation_index_nabl", store=True)

    @api.depends('elongation_index','eln_ref','grade')
    def _compute_elongation_index_nabl(self):
        
        for record in self:
            record.elongation_index_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9effe915-e5a3-45a7-aaeb-10caababd667')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9effe915-e5a3-45a7-aaeb-10caababd667')]).parameter_table
            # for material in materials:
                # if material.grade.id == record.grade.id:
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


    # Flakiness Index 

    temp_flakiness = fields.Char(string="Temp.°C")
    humidity_flakiness= fields.Char(string="Humidity %")

    flakiness_name = fields.Char("Name",default="Flakiness Index")
    flakiness_visible = fields.Boolean("Flakiness Visible",compute="_compute_visible")

    flakiness_table = fields.One2many('mechanical.flakiness.index.line','parent_id',string="Flakiness Index",default=lambda self: self.default_flakiness_sizes())

    total_weight_retained_fl = fields.Float('Wt. Retained on each Sieve (Wn) gms',compute="_compute_total_weight_retained_fl",store=True)
    total_percent_retained_fl = fields.Float('% Retained on each Sieve Xn = (Wn/W)x100',compute="_compute_total_percent_retained_fl",store=True)

    total_weight_retained_mat_fl = fields.Float('Wt. Passing through Gauge (Pn) gms.',compute="_compute_total_weight_retained_mat_fl",store=True)

    total_percent_retained_material_fl = fields.Float('% Passing through Gauge Yn = (Pn/Wn)x100',compute="_compute_total_percent_retained_material_fl", store=True)
    total_total_percent_retained_fl = fields.Float('Total (X’n x Y’n)',compute="_compute_total_total_percent_retained_fl" , store=True)

    flakiness_index = fields.Float('Flakiness Index (%)',compute="_compute_flakiness_index")





    @api.model
    def default_flakiness_sizes(self):
        default_lines = [
            (0, 0, {'sieve_size_passing_fl': '63','sieve_size_retained_fl':'50','length_gauge_fl':'33.9','weight_retained_fl_char':'W1','percent_retained_fl_char':'X1','weight_retained_mat_fl_char':'P1','percent_retained_material_fl_char':'Y1'}),
            (0, 0, {'sieve_size_passing_fl': '50','sieve_size_retained_fl':'40','length_gauge_fl':'27','weight_retained_fl_char':'W2','percent_retained_fl_char':'X2','weight_retained_mat_fl_char':'P1','percent_retained_material_fl_char':'Y1'}),
            (0, 0, {'sieve_size_passing_fl': '40','sieve_size_retained_fl':'31.5','length_gauge_fl':'21.5','weight_retained_fl_char':'W3','percent_retained_fl_char':'X3','weight_retained_mat_fl_char':'P3','percent_retained_material_fl_char':'Y3'}),
            (0, 0, {'sieve_size_passing_fl': '31.5','sieve_size_retained_fl':'25','length_gauge_fl':'16.95','weight_retained_fl_char':'W4','percent_retained_fl_char':'X4','weight_retained_mat_fl_char':'P4','percent_retained_material_fl_char':'Y4'}),
            (0, 0, {'sieve_size_passing_fl': '25','sieve_size_retained_fl':'20', 'length_gauge_fl':'13.5','weight_retained_fl_char':'W5','percent_retained_fl_char':'X5','weight_retained_mat_fl_char':'P5','percent_retained_material_fl_char':'Y5'}),
            (0, 0, {'sieve_size_passing_fl': '20','sieve_size_retained_fl':'16','length_gauge_fl':'10.8','weight_retained_fl_char':'W6','percent_retained_fl_char':'X6','weight_retained_mat_fl_char':'P6','percent_retained_material_fl_char':'Y6'}),
            (0, 0, {'sieve_size_passing_fl': '16','sieve_size_retained_fl':'12.5','length_gauge_fl':'8.55','weight_retained_fl_char':'W7','percent_retained_fl_char':'X7','weight_retained_mat_fl_char':'P7','percent_retained_material_fl_char':'Y7'}),
            (0, 0, {'sieve_size_passing_fl': '12.5','sieve_size_retained_fl':'10','length_gauge_fl':'6.75','weight_retained_fl_char':'W8','percent_retained_fl_char':'X8','weight_retained_mat_fl_char':'P8','percent_retained_material_fl_char':'Y8'}),
            (0, 0, {'sieve_size_passing_fl': '10','sieve_size_retained_fl':'6.3','length_gauge_fl':'4.89','weight_retained_fl_char':'W9','percent_retained_fl_char':'X9','weight_retained_mat_fl_char':'P9','percent_retained_material_fl_char':'Y9'}),
            
        ]
        return default_lines   

    @api.depends('flakiness_table.weight_retained_fl')
    def _compute_total_weight_retained_fl(self):
        for record in self:
            record.total_weight_retained_fl = sum(record.flakiness_table.mapped('weight_retained_fl'))

    @api.depends('flakiness_table.percent_retained_fl')
    def _compute_total_percent_retained_fl(self):
        for record in self:
            record.total_percent_retained_fl = sum(record.flakiness_table.mapped('percent_retained_fl'))

    
    @api.depends('flakiness_table.weight_retained_mat_fl')
    def _compute_total_weight_retained_mat_fl(self):
        for record in self:
            record.total_weight_retained_mat_fl = sum(record.flakiness_table.mapped('weight_retained_mat_fl'))

    @api.depends('flakiness_table.percent_retained_material_fl')
    def _compute_total_percent_retained_material_fl(self):
        for record in self:
            record.total_percent_retained_material_fl = sum(record.flakiness_table.mapped('percent_retained_material_fl'))

    @api.depends('flakiness_table.total_percent_retained_fl')
    def _compute_total_total_percent_retained_fl(self):
        for record in self:
            record.total_total_percent_retained_fl = sum(record.flakiness_table.mapped('total_percent_retained_fl'))

            

    @api.depends('total_total_percent_retained_fl')
    def _compute_flakiness_index(self):
        for record in self:
            record.flakiness_index = round(record.total_total_percent_retained_fl / 100,2)

    def action_compute_flakiness_index(self):
     for record in self:
        if record.total_total_percent_retained_fl:
            record.flakiness_index = round(record.total_total_percent_retained_fl / 100, 2)
        else:
            record.elongation_index = 0.0
    
    flakiness_index_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_flakiness_index_conformity", store=True)

    @api.depends('flakiness_index','eln_ref','grade')
    def _compute_flakiness_index_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.flakiness_index_conformity = 'na'
                continue
            record.flakiness_index_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be7a60bc-bb2c-410d-b91a-4f8730a4ac6f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be7a60bc-bb2c-410d-b91a-4f8730a4ac6f')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be7a60bc-bb2c-410d-b91a-4f8730a4ac6f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be7a60bc-bb2c-410d-b91a-4f8730a4ac6f')]).parameter_table
            # for material in materials:
                # if material.grade.id == record.grade.id:
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



    




    # Compacted  Or Rodded Density

    temp_density = fields.Char(string="Temp.°C")
    humidity_density= fields.Char(string="Humidity %")


    compacted_density_name = fields.Char("Name",default="Compacted Density ")
    compacted_density_visible = fields.Boolean("compacted density  Visible",compute="_compute_visible")


    capacity_of_cylinderr = fields.Float(string="Capacity of Cylinder Use for Test in litre (V)")
    wtt_of_empty_cylinder_compacted = fields.Float(string="Weight of empty cylinder (kg)")
    wtt_cylinder_aggregate_compacted = fields.Float(string="Weight of cylinder + aggregate (kg)")
    mass_of_compacted_aggregate = fields.Float("Mass of Compacted Aggregate in Cylinder (A) – Kg",compute="_compute_mass_of_compacted_aggregate")

    compacted_density = fields.Float("Compacted Density (Ƴ1) = (A/V) Kg/lit",compute="_compute_compacted_density")

    @api.depends('wtt_cylinder_aggregate_compacted', 'wtt_of_empty_cylinder_compacted')
    def _compute_mass_of_compacted_aggregate(self):
        for rec in self:
            rec.mass_of_compacted_aggregate = rec.wtt_cylinder_aggregate_compacted - rec.wtt_of_empty_cylinder_compacted
            

    @api.depends('capacity_of_cylinderr', 'mass_of_compacted_aggregate')
    def _compute_compacted_density(self):
        for rec in self:
            if rec.capacity_of_cylinderr !=0:
              rec.compacted_density = round(rec.mass_of_compacted_aggregate / rec.capacity_of_cylinderr,2)
            else:
             rec.compacted_density = 0.0


    compacted_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_compacted_density_conformity", store=True)

    @api.depends('compacted_density','eln_ref','grade')
    def _compute_compacted_density_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.compacted_density_conformity = 'na'
                continue
            record.compacted_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.compacted_density - record.compacted_density*mu_value
                    upper = record.compacted_density + record.compacted_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.compacted_density_conformity = 'pass'
                        break
                    else:
                        record.compacted_density_conformity = 'fail'

    compacted_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_compacted_density_nabl", store=True)

    @api.depends('compacted_density','eln_ref','grade')
    def _compute_compacted_density_nabl(self):
        
        for record in self:
            record.compacted_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.compacted_density - record.compacted_density*mu_value
                    upper = record.compacted_density + record.compacted_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.compacted_density_nabl = 'pass'
                        break
                    else:
                        record.compacted_density_nabl = 'fail'


    # Loose Density
    loose_density_name = fields.Char("Name",default="Loose Density ")
    loose_density_visible = fields.Boolean("Loose density  Visible",compute="_compute_visible")


    capacity_of_cylinder_loose = fields.Float(string="Capacity of Cylinder Use for Test in litre (V)")
    wtt_of_empty_cylinder_loose = fields.Float(string="Weight of empty cylinder (kg)")
    wtt_cylinder_aggregate_loose = fields.Float(string="Weight of cylinder + aggregate (kg)")
    mass_of_loose_aggregate = fields.Float("Mass of Loose Aggregate in Cylinder (A) – Kg",compute="_compute_mass_of_loose_aggregate")

    loose_density = fields.Float("Loose Density (Ƴ1) = (A/V) Kg/lit",compute="_compute_loose_density")

    @api.depends('wtt_cylinder_aggregate_loose', 'wtt_of_empty_cylinder_loose')
    def _compute_mass_of_loose_aggregate(self):
        for rec in self:
            rec.mass_of_loose_aggregate = rec.wtt_cylinder_aggregate_loose - rec.wtt_of_empty_cylinder_loose
            

    @api.depends('capacity_of_cylinder_loose', 'mass_of_loose_aggregate')
    def _compute_loose_density(self):
        for rec in self:
            if rec.capacity_of_cylinder_loose !=0:
              rec.loose_density = round(rec.mass_of_loose_aggregate / rec.capacity_of_cylinder_loose,2)
            else:
             rec.loose_density = 0.0


    loose_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_loose_density_conformity", store=True)

    @api.depends('loose_density','eln_ref','grade')
    def _compute_loose_density_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.loose_density_conformity = 'na'
                continue
            record.loose_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65a41d1f-d557-438e-8fd1-2c619a334d02')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65a41d1f-d557-438e-8fd1-2c619a334d02')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.loose_density - record.loose_density*mu_value
                    upper = record.loose_density + record.loose_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.loose_density_conformity = 'pass'
                        break
                    else:
                        record.loose_density_conformity = 'fail'

    loose_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_loose_density_nabl", store=True)

    @api.depends('loose_density','eln_ref','grade')
    def _compute_loose_density_nabl(self):
        
        for record in self:
            record.loose_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65a41d1f-d557-438e-8fd1-2c619a334d02')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65a41d1f-d557-438e-8fd1-2c619a334d02')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.loose_density - record.loose_density*mu_value
                    upper = record.loose_density + record.loose_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.loose_density_nabl = 'pass'
                        break
                    else:
                        record.loose_density_nabl = 'fail'
                        
                        


    # Void Loose density And Void Compacted Density

    voids_loose_and_compacted_name = fields.Char("Name",default="Void In Compacted Density & Voids In Loose Density ")
    # void_loose_compacted_visible = fields.Boolean("Void In Compacted Density & Voids In Loose Density ",compute="_compute_visible")

    voids_compacted_density_name = fields.Char("Name",default="Void In Compacted Density ")
    voids_compacted_density_visible = fields.Boolean("Void In Compacted Visible",compute="_compute_visible")

    voids_loose_density_name = fields.Char("Name",default="Void In Loose Density ")
    voids_loose_density_visible = fields.Boolean("Void Loose density Visible",compute="_compute_visible")

    specific_gravity_voids = fields.Float(string="Sp. Gravity of Material (Gs)")

    voids_compacted_density = fields.Float(string="Percent Voids in Compacted Density = (Gs - Ƴ1 )/Gs x 100",compute="_compute_voids_compacted_density")
    voids_loose_density = fields.Float(string="Percent Voids in Loose Density = (Gs – Ƴ2 )/Gs x 100",compute="_compute_voids_loose_density")


    @api.depends('avg_specific_gravity', 'compacted_density')
    def _compute_voids_compacted_density(self):
        for rec in self:
            if rec.avg_specific_gravity:
              rec.voids_compacted_density = round(((rec.avg_specific_gravity - rec.compacted_density)/rec.avg_specific_gravity * 100),2)
            else:
             rec.voids_compacted_density = 0.0
             

    @api.depends('avg_specific_gravity', 'loose_density')
    def _compute_voids_loose_density(self):
        for rec in self:
            if rec.avg_specific_gravity:
              rec.voids_loose_density = round((((rec.avg_specific_gravity - rec.loose_density)/rec.avg_specific_gravity) * 100),2)
            else:
             rec.voids_loose_density = 0.0  


    voids_compacted_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Void In Compacted Density Conformity", compute="_compute_voids_compacted_density_conformity", store=True)

    @api.depends('voids_compacted_density','eln_ref','grade')
    def _compute_voids_compacted_density_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.voids_compacted_density_conformity = 'na'
                continue
            record.voids_compacted_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.voids_compacted_density - record.voids_compacted_density*mu_value
                    upper = record.voids_compacted_density + record.voids_compacted_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.voids_compacted_density_conformity = 'pass'
                        break
                    else:
                        record.voids_compacted_density_conformity = 'fail'

    voids_compacted_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Void In Compacted Density NABL", compute="_compute_voids_compacted_density_nabl", store=True)

    @api.depends('voids_compacted_density','eln_ref','grade')
    def _compute_voids_compacted_density_nabl(self):
        
        for record in self:
            record.voids_compacted_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.voids_compacted_density - record.voids_compacted_density*mu_value
                    upper = record.voids_compacted_density + record.voids_compacted_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.voids_compacted_density_nabl = 'pass'
                        break
                    else:
                        record.voids_compacted_density_nabl = 'fail'  

    voids_loose_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Void In Loose Density Conformity", compute="_compute_voids_loose_density_conformity", store=True)

    @api.depends('voids_loose_density','eln_ref','grade')
    def _compute_voids_loose_density_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.voids_loose_density_conformity = 'na'
                continue
            record.voids_loose_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.voids_loose_density - record.voids_loose_density*mu_value
                    upper = record.voids_loose_density + record.voids_loose_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.voids_loose_density_conformity = 'pass'
                        break
                    else:
                        record.voids_loose_density_conformity = 'fail'

    voids_loose_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Void In Loose Density NABL", compute="_compute_voids_loose_density_nabl", store=True)

    @api.depends('voids_loose_density','eln_ref','grade')
    def _compute_voids_loose_density_nabl(self):
        
        for record in self:
            record.voids_loose_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.voids_loose_density - record.voids_loose_density*mu_value
                    upper = record.voids_loose_density + record.voids_loose_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.voids_loose_density_nabl = 'pass'
                        break
                    else:
                        record.voids_loose_density_nabl = 'fail' 



  # Rate of Evaporation

    temp_evaporation = fields.Char(string="Temp.°C")
    humidity_evaporation= fields.Char(string="Humidity %")

    rate_of_evaporation_name = fields.Char(default="Rate of Evaporation")

    rate_of_evaporation_visible = fields.Boolean(compute="_compute_visible")

    rate_of_evaporation_table = fields.One2many('mechanical.rate.of.evaporation.line','parent_id',string="Rate of Evaporation")

    avg_rate_evaporation = fields.Float('Average Rate Of Evaporation',compute="_compute_avg_rate_evaporation")


    @api.depends('rate_of_evaporation_table.rate_evaporation')
    def _compute_avg_rate_evaporation(self):
        for record in self:
            if record.rate_of_evaporation_table:
              record.avg_rate_evaporation = sum(record.rate_of_evaporation_table.mapped('rate_evaporation'))/ len(record.rate_of_evaporation_table)
            else:
                record.avg_rate_evaporation = 0.0

    avg_rate_evaporation_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),], string="Conformity", compute="_compute_avg_rate_evaporation_conformity", store=True)

    @api.depends('avg_rate_evaporation','eln_ref','grade')
    def _compute_avg_rate_evaporation_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_rate_evaporation_conformity = 'na'
                continue
            record.avg_rate_evaporation_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e9d9c62-e634-47a2-a689-2c6c8538493c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e9d9c62-e634-47a2-a689-2c6c8538493c')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_rate_evaporation - record.avg_rate_evaporation*mu_value
                    upper = record.avg_rate_evaporation + record.avg_rate_evaporation*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_rate_evaporation_conformity = 'pass'
                        break
                    else:
                        record.avg_rate_evaporation_conformity = 'fail'

    avg_rate_evaporation_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_rate_evaporation_nabl", store=True)

    @api.depends('avg_rate_evaporation','eln_ref','grade')
    def _compute_avg_rate_evaporation_nabl(self):
        
        for record in self:
            record.avg_rate_evaporation_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e9d9c62-e634-47a2-a689-2c6c8538493c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e9d9c62-e634-47a2-a689-2c6c8538493c')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_rate_evaporation - record.avg_rate_evaporation*mu_value
                    upper = record.avg_rate_evaporation + record.avg_rate_evaporation*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_rate_evaporation_nabl = 'pass'
                        break
                    else:
                        record.avg_rate_evaporation_nabl = 'fail'









    # Abrasion Value

    temp_abrasion_value = fields.Char(string="Temp.°C")
    humidity_abrasion_value= fields.Char(string="Humidity %")


    abrasion_value_name = fields.Char("Name",default="Abrasion Value By Los Angeles+")
    abrasion_value_visible = fields.Boolean("Abrasion Value Visible",compute="_compute_visible")

    abrasion_value_child_lines = fields.One2many('mechanical.abrasion.value.line','parent_id',string="Parameter",default=lambda self: self._default_abrasion_value_child_lines())

    abrasion_value_child_lines_second = fields.One2many('mechanical.abrasion.value.second.line','parent_id',string="Second Parameter",default=lambda self: self._default_abrasion_value_child_lines_second())

    @api.model
    def _default_abrasion_value_child_lines(self):
        default_lines = [
            (0, 0, {'sieve_passing_ab': '80','sieve_retained_ab': '63','grade_a':'---','grade_b':'---','grade_c':'---','grade_d':'---','grade_e':'2500','grade_f':'---','grade_g':'---'}),
            (0, 0, {'sieve_passing_ab': '63','sieve_retained_ab': '50','grade_a':'---','grade_b':'---','grade_c':'---','grade_d':'---','grade_e':'2500','grade_f':'---','grade_g':'---'}),
            (0, 0, {'sieve_passing_ab': '50','sieve_retained_ab': '40','grade_a':'---','grade_b':'---','grade_c':'---','grade_d':'---','grade_e':'5000','grade_f':'5000','grade_g':'---'}),
            (0, 0, {'sieve_passing_ab': '40','sieve_retained_ab': '25','grade_a':'1250','grade_b':'---','grade_c':'---','grade_d':'---','grade_e':'---','grade_f':'5000','grade_g':'5000'}),
            (0, 0, {'sieve_passing_ab': '25','sieve_retained_ab': '20','grade_a':'1250','grade_b':'---','grade_c':'---','grade_d':'---','grade_e':'---','grade_f':'---','grade_g':'5000'}),
            (0, 0, {'sieve_passing_ab': '20','sieve_retained_ab': '12.5','grade_a':'1250','grade_b':'2500','grade_c':'---','grade_d':'---','grade_e':'---','grade_f':'---','grade_g':'---'}),
            (0, 0, {'sieve_passing_ab': '12.5','sieve_retained_ab': '10','grade_a':'1250','grade_b':'2500','grade_c':'---','grade_d':'---','grade_e':'---','grade_f':'---','grade_g':'---'}),
            (0, 0, {'sieve_passing_ab': '10','sieve_retained_ab': '6.3','grade_a':'---','grade_b':'---','grade_c':'2500','grade_d':'---','grade_e':'---','grade_f':'---','grade_g':'---'}),
            (0, 0, {'sieve_passing_ab': '6.3','sieve_retained_ab': '.75','grade_a':'---','grade_b':'---','grade_c':'2500','grade_d':'---','grade_e':'---','grade_f':'---','grade_g':'---'}),
            (0, 0, {'sieve_passing_ab': '4.75','sieve_retained_ab': '2.36','grade_a':'---','grade_b':'---','grade_c':'---','grade_d':'5000','grade_e':'---','grade_f':'---','grade_g':'---'})
            
        ]
        return default_lines
    

    @api.model
    def _default_abrasion_value_child_lines_second(self):
        default_lines = [
            (0, 0, {'grading_ab': 'No. Of Spheres','grade_a1':'12','grade_b2':'11','grade_c3':'8','grade_d4':'6','grade_e5':'12','grade_f6':'12','grade_g7':'12'}),
            (0, 0, {'grading_ab': 'Weight of Charge','grade_a1':'5000 ± 25','grade_b2':'4584 ± 25','grade_c3':'3330 ± 20','grade_d4':'2500 ± 15','grade_e5':'5000 ± 25','grade_f6':'5000 ± 25','grade_g7':'5000 ± 25'}),
            (0, 0, {'grading_ab': 'Machine Revolutions','grade_a1':'500','grade_b2':'500','grade_c3':'500','grade_d4':'500','grade_e5':'1000','grade_f6':'1000','grade_g7':'1000'})
            
        ]
        return default_lines
    
    wt_of_agg_ab = fields.Integer(string="Weight of Aggregate for Testing (A) – gms")
    wt_of_agg_retained_ab = fields.Integer(string="Weight of Aggregate Retained on 1.70 mm Sieve (B) - gms")
    wt_of_agg_passing_ab = fields.Float(string="Weight of Aggregate Passing 1.70 mm Sieve (C) – gms",compute="_compute_wt_of_agg_passing_ab")

    agg_abrasion_value = fields.Float(string="Aggregate Abrasion Value (Wear) in % = (C/A)x100",compute="_compute_agg_abrasion_value")

    @api.depends('wt_of_agg_ab', 'wt_of_agg_retained_ab')
    def _compute_wt_of_agg_passing_ab(self):
        for line in self:
            line.wt_of_agg_passing_ab = line.wt_of_agg_ab - line.wt_of_agg_retained_ab


    @api.depends('wt_of_agg_passing_ab', 'wt_of_agg_ab')
    def _compute_agg_abrasion_value(self):
        for line in self:
            if line.wt_of_agg_ab != 0:
                line.agg_abrasion_value = (line.wt_of_agg_passing_ab / line.wt_of_agg_ab) * 100
            else:
                line.agg_abrasion_value = 0.0



    wt_of_agg_ab_1 = fields.Integer(string="Weight of Aggregate for Testing (A) – gms")
    wt_of_agg_retained_ab_1 = fields.Integer(string="Weight of Aggregate Retained on 1.70 mm Sieve (B) - gms")
    wt_of_agg_passing_ab_1 = fields.Float(string="Weight of Aggregate Passing 1.70 mm Sieve (C) – gms",compute="_compute_wt_of_agg_passing_ab_1")

    agg_abrasion_value_1 = fields.Float(string="Aggregate Abrasion Value (Wear) in % = (C/A)x100",compute="_compute_agg_abrasion_value_1")

    @api.depends('wt_of_agg_ab_1', 'wt_of_agg_retained_ab_1')
    def _compute_wt_of_agg_passing_ab_1(self):
        for line in self:
            line.wt_of_agg_passing_ab_1 = line.wt_of_agg_ab_1 - line.wt_of_agg_retained_ab_1


    @api.depends('wt_of_agg_passing_ab_1', 'wt_of_agg_ab_1')
    def _compute_agg_abrasion_value_1(self):
        for line in self:
            if line.wt_of_agg_ab_1 != 0:
                line.agg_abrasion_value_1 = (line.wt_of_agg_passing_ab_1 / line.wt_of_agg_ab_1) * 100
            else:
                line.agg_abrasion_value_1 = 0.0
    


    avg_abrasion_value = fields.Float(string="Average Abrasion Value",compute="_compute_avg_abrasion_value")
    

    @api.depends('agg_abrasion_value', 'agg_abrasion_value_1')
    def _compute_avg_abrasion_value(self):
        for line in self:
                line.avg_abrasion_value = (line.agg_abrasion_value + line.agg_abrasion_value_1) /2



    avg_abrasion_value_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_avg_abrasion_value_conformity", store=True)

    @api.depends('avg_abrasion_value','eln_ref','grade')
    def _compute_avg_abrasion_value_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_abrasion_value_conformity = 'na'
                continue
            record.avg_abrasion_value_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37f2161e-5cc0-413f-b76c-10478c65baf9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37f2161e-5cc0-413f-b76c-10478c65baf9')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37f2161e-5cc0-413f-b76c-10478c65baf9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37f2161e-5cc0-413f-b76c-10478c65baf9')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
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
    


    # Sieve Analysis 
    temp_sieve_analysis = fields.Char(string="Temp.°C")
    humidity_sieve_analysis= fields.Char(string="Humidity %")
    
    weight_of_sample = fields.Float(string="Weight of Sample in gms")
    sieve_analysis_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

    sieve_analysis_child_lines = fields.One2many('mechanical.coarse.aggregate.sieve.analysis.line','parent_id',string="Parameter",default=lambda self: self._default_sieve_analysis_child_lines())
    total_sieve_analysis = fields.Float(string="Total",compute="_compute_total_sieve")


    @api.model
    def _default_sieve_analysis_child_lines(self):
        default_lines = [
            (0, 0, {'sieve_size': '80'}),
            (0, 0, {'sieve_size': '63'}),
            (0, 0, {'sieve_size': '40'}),
            (0, 0, {'sieve_size': '20'}),
            (0, 0, {'sieve_size': '16'}),
            (0, 0, {'sieve_size': '12.5'}),
            (0, 0, {'sieve_size': '10'}),
            (0, 0, {'sieve_size': '4.75'}),
            (0, 0, {'sieve_size': '2.36'}),
            (0, 0, {'sieve_size': 'Pan'})
            
        ]
        return default_lines




    def default_get(self, fields):
        print("From Default Value")
        res = super(CoarseAggregateMechanical, self).default_get(fields)
        default_sieve_sizes = []
        
        # Safely get eln_ref with default None if not exists
        eln_ref = res.get('eln_ref') 
        
        if eln_ref:
            eln = self.env['lerm.eln'].sudo().browse(eln_ref)
            if not eln.exists():
                return res
                
            size_str = eln.size_id.size or ''
            grade_str = (eln.grade_id.grade or '').lower()
            
            # Define mappings
            if grade_str == 'single sized aggregate':
                sieve_mapping = {
                    '63': ['80 mm', '63 mm', '40 mm', '20 mm', '10 mm', 'pan'],
                    '40': ['63 mm', '40 mm', '20 mm', '10 mm', 'pan'],
                    '20': ['40 mm', '20 mm', '10 mm', '4.75 mm', 'pan'],
                    '16': ['20 mm', '16 mm', '10 mm', '4.75 mm', 'pan'],
                    '12': ['16 mm', '12.5 mm', '10 mm', '4.75 mm', 'pan'],
                    '10': ['12.5 mm', '10 mm', '4.75 mm', '2.36 mm', 'pan'],
                    '31.5': ['37.5 mm', '31.5 mm', '16mm' , '4.75 mm', 'pan'],
                    '19': ['22.4 mm', '19 mm','13.2 mm', '4.75 mm',  'pan'],
                }
                specific_limits_mapping = {
                    '63': ['100', '85 - 100', '0 - 30', '0 - 5', '0 - 5', '0'],
                    '40': ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                    '20': ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                    '16': ['100', '85 - 100', '0 - 30', '0 - 5', '0'],
                    '12': ['100', '85 - 100', '0 - 45', '0 - 10', '0'],
                    '10': ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                    '31.5': ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                    '19': ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                }
            elif grade_str == 'graded aggregate':
                sieve_mapping = {
                    '40': ['80 mm', '40 mm', '20 mm', '10 mm','4.75 mm','pan'],
                    '20': ['40 mm', '20 mm', '10 mm', '4.75 mm','pan'],
                    '16': ['20 mm', '16 mm', '10 mm', '4.75 mm', 'pan'],
                    '12': ['16 mm', '12.5 mm', '10 mm', '4.75 mm', 'pan'],
                    '31.5': ['37.5 mm', '31.5 mm', '16mm' , '4.75 mm', 'pan'],
                    '19': ['22.4 mm', '19 mm','13.2 mm', '4.75 mm',  'pan'],
                }
                specific_limits_mapping = {
                    '40': ['100', '95 - 100', '30 - 70', '10 - 35','0 - 5', '0'],
                    '20': ['100', '95 - 100', '25 - 55', '0 - 10', '0'],
                    '16': ['100', '90 - 100', '30 - 70', '0 - 10', '0'],
                    '12': ['100', '90 - 100', '40 - 85', '0 - 10', '0'],
                    '31.5': ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                    '19': ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                }
            else:
                return res

            # Extract numeric part
            # match = re.search(r'\d+', size_str)
            match = re.search(r'\d+(\.\d+)?', size_str)
            if match:
                # number = int(match.group())
                number = match.group().strip()
                sieve_list = sieve_mapping.get(number, [])
                specific_limits = specific_limits_mapping.get(number, [])
                
                # Check if lists have same length
                # if len(sieve_list) != len(specific_limits):
                #     _logger.warning(f"Mismatch in sieve sizes and limits for size {number}")
                #     return res
                    
                # Create sieve analysis lines
                for sieve_size, specific_limit in zip(sieve_list, specific_limits):
                    size = {
                        'sieve_size': sieve_size,
                        'specific_limits': specific_limit,
                    }
                    default_sieve_sizes.append((0, 0, size))
                
                res['sieve_analysis_child_lines'] = default_sieve_sizes

        return res
    
    def populate_sieve_analysis_lines(self):
        self.ensure_one()

        eln = self.eln_ref
        if not eln:
            return

        size_str = eln.size_id.size or ''
        grade_str = (eln.grade_id.grade or '').lower()

        if grade_str == 'single sized aggregate':
            specific_limits_mapping = {
                '63': ['100', '85 - 100', '0 - 30', '0 - 5', '0 - 5', '0'],
                '40': ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                '20': ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                '16': ['100', '85 - 100', '0 - 30', '0 - 5', '0'],
                '12': ['100', '85 - 100', '0 - 45', '0 - 10', '0'],
                '10': ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                '31.5': ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                '19': ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
            }
        elif grade_str == 'graded aggregate':
            specific_limits_mapping = {
                '40': ['100', '95 - 100', '30 - 70', '10 - 35', '0 - 5', '0'],
                '20': ['100', '95 - 100', '25 - 55', '0 - 10', '0'],
                '16': ['100', '90 - 100', '30 - 70', '0 - 10', '0'],
                '12': ['100', '90 - 100', '40 - 85', '0 - 10', '0'],
                '31.5': ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                '19': ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
            }
        else:
            return

        # match = re.search(r'\d+', size_str)
        match = re.search(r'\d+(\.\d+)?', size_str)
        if match:
            # number = int(match.group())
            number = match.group().strip()
            specific_limits = specific_limits_mapping.get(number, [])

            # Only update specific_limits of existing lines
            for line, specific_limit in zip(self.sieve_analysis_child_lines, specific_limits):
                line.specific_limits = specific_limit


    
    





    def calculate_sieve(self): 
        for record in self:
            # import wdb; wdb.set_trace()
            record.populate_sieve_analysis_lines()  # replace default_get call
            for line in record.sieve_analysis_child_lines:
                # print("Rows",str(line.percent_retained))
                previous_line = line.serial_no - 1
                if previous_line == 0:
                #     if line.percent_retained == 0:
                #         line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2),
                #                     'passing_percent': 100 ,})
                #     else:
                #         line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2),
                #                     'passing_percent': round(100 -line.percent_retained - line.percent_retained,2),})
                # else:
                    previous_line_record = self.env['mechanical.coarse.aggregate.sieve.analysis.line'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
                    line.write({'cumulative_retained': previous_line_record + line.percent_retained,
                                'passing_percent': round(100-(previous_line_record + line.percent_retained),2),})
                
                    
                    # print("Previous Cumulative",previous_line_record)

    
   
            


    # def calculate_sieve(self): 
    #     for record in self:
    #         record.populate_sieve_analysis_lines()  # replace default_get call
            

            

                    

    
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



    graph_image_slive = fields.Binary("Sieve Graph", compute="_compute_graph_image_slive", store=True)

    @api.depends('sieve_analysis_child_lines.cumulative_retained', 'sieve_analysis_child_lines.passing_percent')
    def _compute_graph_image_slive(self):
        for record in self:
            if record.sieve_analysis_child_lines:
                record.graph_image_slive = record.generate_line_chart_slive()
            else:
                record.graph_image_slive = False

    





    # def generate_line_chart_slive(self):
   
    #     x_value = []
    #     y_value = []
    #     x_labels = []

    #     for line in self.sieve_analysis_child_lines:
    #         if line.sieve_size and line.passing_percent is not None:
    #             sieve_str = str(line.sieve_size).strip().lower()
    #             try:
    #                 if 'mm' in sieve_str:
    #                     sieve_val = float(sieve_str.replace('mm', '').strip())
    #                     label = f"{int(sieve_val)} mm"
    #                 elif 'µ' in sieve_str or 'micron' in sieve_str:
    #                     sieve_val = float(sieve_str.replace('µ', '').replace('micron', '').strip()) / 1000
    #                     label = f"{int(float(line.sieve_size.replace('µ', '').replace('micron', '').strip()))} µm"
    #                 else:
    #                     sieve_val = float(sieve_str)
    #                     label = f"{sieve_val} mm"

    #                 x_value.append(sieve_val)
    #                 y_value.append(float(line.passing_percent))
    #                 x_labels.append(label)
    #             except ValueError:
    #                 continue

    #     if not x_value or not y_value:
    #         return False

    #     # Sort ascending
    #     sorted_data = sorted(zip(x_value, y_value, x_labels))
    #     x_value, y_value, x_labels = zip(*sorted_data)

    #     plt.figure(figsize=(12, 5))
    #     plt.xscale('log')

    #     # Main curve
    #     plt.plot(x_value, y_value, color='blue', linestyle='-', linewidth=2)
    #     plt.scatter(x_value, y_value, color='red', edgecolors='black', s=60, zorder=5)

    #     plt.xlabel('Sieve Size', fontsize=12)
    #     plt.ylabel('Passing %', fontsize=12)
    #     plt.title('Grain Size Analysis', fontsize=14)

    #     ax = plt.gca()
    #     plt.xticks(ticks=x_value, labels=x_labels, rotation=45, ha='right')
    #     ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(1.0, 10.0)*0.1, numticks=200))
    #     ax.yaxis.set_minor_locator(MultipleLocator(2))
    #     plt.grid(True, which='both', axis='both', linestyle='--', linewidth=0.3, color='gray', alpha=0.8)

    #     plt.xlim(left=min(x_value)/1.5, right=max(x_value)*1.5)
    #     plt.ylim(bottom=0, top=120)
    #     plt.yticks([0, 20, 40, 60, 80, 100, 120])

    #     # --- D-points: D10, D30, D60 ---
    #     d_points = [
    #         (getattr(self, 'd10', None), 10, 'black'),
    #         (getattr(self, 'd30', None), 30, 'yellow'),
    #         (getattr(self, 'd60', None), 60, 'orange')
    #     ]

    #     for dx, dy, color in d_points:
    #         if dx:
    #             # Solid point
    #             plt.scatter(dx, dy, color=color, s=80, zorder=10)
    #             # Draw X and Y guide lines only to intersection
    #             plt.plot([dx, dx], [0, dy], color=color, linestyle='-', linewidth=1.2)
    #             plt.plot([0, dx], [dy, dy], color=color, linestyle='-', linewidth=1.2)

    #     # Save figure
    #     buffer = io.BytesIO()
    #     plt.tight_layout()
    #     plt.savefig(buffer, format='png')
    #     plt.close()
    #     buffer.seek(0)

    #     return base64.b64encode(buffer.read())



    # def generate_line_chart_slive(self):
    #   x_value = []
    #   y_value = []
    #   x_labels = []

    #   for line in self.sieve_analysis_child_lines:
    #      if line.sieve_size and line.passing_percent is not None:
    #         sieve_str = str(line.sieve_size).strip().lower()
    #         try:
    #               if 'mm' in sieve_str:
    #                 sieve_val = float(sieve_str.replace('mm', '').strip())
    #                 label = f"{int(sieve_val)} mm"
    #               elif 'µ' in sieve_str or 'micron' in sieve_str:
    #                 sieve_val = float(sieve_str.replace('µ', '').replace('micron', '').strip()) / 1000
    #                 label = f"{int(float(line.sieve_size.replace('µ', '').replace('micron', '').strip()))} µm"
    #               else:
    #                 sieve_val = float(sieve_str)
    #                 label = f"{sieve_val} mm"

    #               x_value.append(sieve_val)
    #               y_value.append(float(line.passing_percent))
    #               x_labels.append(label)
    #         except ValueError:
    #               continue

    #      if not x_value or not y_value:
    #        return False

    #   # Sort ascending
    #   sorted_data = sorted(zip(x_value, y_value, x_labels))
    #   x_value, y_value, x_labels = zip(*sorted_data)
    #   x_value = np.array(x_value)
    #   y_value = np.array(y_value)

      

    #   x_smooth = np.logspace(np.log10(min(x_value)), np.log10(max(x_value)), 500)
    #   pchip = PchipInterpolator(np.log10(x_value), y_value)
    #   y_smooth = pchip(np.log10(x_smooth))

    #   plt.figure(figsize=(13, 5))
    #   plt.xscale('log')

    #   # Smooth curve
    #   plt.plot(x_smooth, y_smooth, color='blue', linestyle='-', linewidth=2)
    #   # Original points
    #   plt.scatter(x_value, y_value, color='red', edgecolors='black', s=60, zorder=5)

    #   plt.xlabel('Sieve Size', fontsize=12)
    #   plt.ylabel('Passing %', fontsize=12)
    #   plt.title('Grain Size Analysis', fontsize=14)

    #   ax = plt.gca()
    #   plt.xticks(ticks=x_value, labels=x_labels, rotation=45, ha='right')
    #   ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(1.0, 10.0)*0.1, numticks=200))
    #   ax.yaxis.set_minor_locator(MultipleLocator(2))
    #   plt.grid(True, which='both', axis='both', linestyle='--', linewidth=0.3, color='gray', alpha=0.8)

    #   plt.xlim(left=min(x_value)/1.5, right=max(x_value)*1.5)
    #   plt.ylim(bottom=0, top=120)
    #   plt.yticks([0, 20, 40, 60, 80, 100, 120])

    #   # --- D-points: D10, D30, D60 ---
    #   d_points = [
    #      (getattr(self, 'd10', None), 10, 'black'),
    #      (getattr(self, 'd30', None), 30, 'yellow'),
    #      (getattr(self, 'd60', None), 60, 'orange')
    #     ]

    #   for dx, dy, color in d_points:
    #     if dx:
    #         plt.scatter(dx, dy, color=color, s=80, zorder=10)
    #         plt.plot([dx, dx], [0, dy], color=color, linestyle='-', linewidth=1.2)
    #         plt.plot([min(x_value)/1.5, dx], [dy, dy], color=color, linestyle='-', linewidth=1.2)

    #   buffer = io.BytesIO()
    #   plt.tight_layout()
    #   plt.savefig(buffer, format='png')
    #   plt.close()
    #   buffer.seek(0)
    #   return base64.b64encode(buffer.read())

    def generate_line_chart_slive(self):
      x_value = []
      y_value = []
      x_labels = []

     # -----------------------------
     # Extract and normalize data
     # -----------------------------
      for line in self.sieve_analysis_child_lines:
         if line.sieve_size and line.passing_percent is not None:
            sieve_str = str(line.sieve_size).strip().lower()
            try:
                # mm
                if 'mm' in sieve_str:
                    sieve_val = float(sieve_str.replace('mm', '').strip())
                    label = f"{int(sieve_val)} mm"

                # micron or µm
                elif 'µ' in sieve_str or 'micron' in sieve_str:
                    raw = float(sieve_str.replace('µ', '').replace('micron', '').strip())
                    sieve_val = raw / 1000.0  # µm → mm
                    label = f"{int(raw)} µm"

                # numbers only
                else:
                    sieve_val = float(sieve_str)
                    label = f"{sieve_val} mm"

                if sieve_val > 0:     # *** IMPORTANT for log10 ***
                    x_value.append(sieve_val)
                    y_value.append(float(line.passing_percent))
                    x_labels.append(label)

            except ValueError:
                continue

      # No data? Stop safely.
      if len(x_value) < 2:
        return False

     # -----------------------------
     # Sort
     # -----------------------------
      sorted_data = sorted(zip(x_value, y_value, x_labels))
      x_value, y_value, x_labels = zip(*sorted_data)

      x_value = np.array(x_value, dtype=float)
      y_value = np.array(y_value, dtype=float)

     # -----------------------------
     # Ensure unique X values
     # -----------------------------
      x_unique, idx = np.unique(x_value, return_index=True)
      x_value = x_unique
      y_value = y_value[idx]
      x_labels = [x_labels[i] for i in idx]

      # Need at least 2 distinct points
      if len(x_value) < 2:
        return False

    # -----------------------------
    # Compute log10(x)
    # -----------------------------
      log_x = np.log10(x_value)

     # Must be strictly increasing
      if not np.all(np.diff(log_x) > 0):
        return False  # avoid crash

    # -----------------------------
    # Interpolation
    # -----------------------------
      try:
         pchip = PchipInterpolator(log_x, y_value)
      except Exception:
        return False

      x_smooth = np.logspace(np.log10(min(x_value)),
                           np.log10(max(x_value)),
                           500)
      y_smooth = pchip(np.log10(x_smooth))

     # -----------------------------
     # Plot
     # -----------------------------
      plt.figure(figsize=(13, 5))
      plt.xscale('log')

      plt.plot(x_smooth, y_smooth, color='blue', linestyle='-',  linewidth=2)
      plt.scatter(x_value, y_value, color='red', edgecolors='black', s=60, zorder=5)

      plt.xlabel('Sieve Size', fontsize=12)
      plt.ylabel('Passing %', fontsize=12)
      plt.title('Grain Size Analysis', fontsize=14)

      ax = plt.gca()
      plt.xticks(ticks=x_value, labels=x_labels, rotation=45, ha='right')
      ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(1,10)*0.1))
      ax.yaxis.set_minor_locator(MultipleLocator(2))

      plt.grid(True, which='both', linestyle='--', linewidth=0.3, color='gray', alpha=0.8)
      plt.xlim(left=min(x_value)/1.5, right=max(x_value)*1.5)
      plt.ylim(bottom=0, top=120)
      plt.yticks([0, 20, 40, 60, 80, 100, 120])

    # -----------------------------
    # D10, D30, D60 annotations
    # -----------------------------
      d_points = [
        (getattr(self, 'd10', None), 10, 'black'),
        (getattr(self, 'd30', None), 30, 'yellow'),
        (getattr(self, 'd60', None), 60, 'orange')
      ]

      for dx, dy, color in d_points:
          if dx:
            plt.scatter(dx, dy, color=color, s=80, zorder=10)
            plt.plot([dx, dx], [0, dy], color=color, linewidth=1.2)
            plt.plot([min(x_value)/1.5, dx], [dy, dy], color=color, linewidth=1.2)

      # -----------------------------
      # Save to base64
      # -----------------------------
      buffer = io.BytesIO()
      plt.tight_layout()
      plt.savefig(buffer, format='png')
      plt.close()
      buffer.seek(0)
      return base64.b64encode(buffer.read())


    


     #  Soundness Test 

    temp_soudness = fields.Char(string="Temp.°C")
    humidity_soudness= fields.Char(string="Humidity %")

    soudness_name = fields.Char("Name",default="Soundness Test ")
    soudness_visible = fields.Boolean("Soundness Test",compute="_compute_visible")

    soudness_magnesium_name = fields.Char("Name",default="Soundness Magnesium Test ")
    soudness_magnesium_visible = fields.Boolean("Soundness Test",compute="_compute_visible")

    soudness_child_lines = fields.One2many('coarse.soudness.line','parent_id',string="Parameter")

    



    sieve_name = fields.Char("Name",default="Gradation Of Original Sample")
    # sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

    wt_of_sample = fields.Float(string="Wt. Of Sample Taken For Analysis (gms) = ", digits=(8,3))
 
    sieve_analysis_soundness_lines = fields.One2many('mechanical.sieve.analysis.line','parent_id',string="Sieve Analysis",default=lambda self: self._default_sieve_analysis_soundness_lines())

    total_percent_retained = fields.Float(
        string="Total % Retained",
        compute="_compute_total_percent_retained",
        store=True
    )

    @api.depends('sieve_analysis_soundness_lines.percent_retained')
    def _compute_total_percent_retained(self):
        for rec in self:
            rec.total_percent_retained = sum(
                line.percent_retained for line in rec.sieve_analysis_soundness_lines
            )

    
    @api.model
    def _default_sieve_analysis_soundness_lines(self):
        default_lines = [
            (0, 0, {'sieve_size': 'Above 80mm', 'particle_size': '80mm'}),
            (0, 0, {'sieve_size': '80mm', 'particle_size': '63mm'}),
            (0, 0, {'sieve_size': '63mm', 'particle_size': '40mm'}),
            (0, 0, {'sieve_size': '40mm', 'particle_size': '20mm'}),
            (0, 0, {'sieve_size': '20mm', 'particle_size': '10mm'}),
            (0, 0, {'sieve_size': '10mm', 'particle_size': '4.75mm'}),
        ]
        return default_lines


    # @api.onchange('sieve_analysis_child_lines')
    # def _onchange_sieve_analysis_child_lines(self):
    #     for rec in self:
    #         pan_line = None
    #         total_retained = 0.0
    #         target_sieves = ['80mm','40mm','20mm','16mm', '10mm', '4.75mm', '2.36mm','1.18mm','600 µ','425 µ','300µ','212µ','150µ','75µ']

    #         for line in rec.sieve_analysis_child_lines:
    #             if line.sieve_size and line.sieve_size.lower() == 'pan':
    #                 pan_line = line
    #             elif line.sieve_size in target_sieves:
    #                 total_retained += line.wt_retained or 0.0

    #         if pan_line:
    #             pan_line.wt_retained = (rec.wt_of_sample or 0.0) - total_retained




    def calculate_sound_sieve(self): 
        for record in self:
            # import wdb; wdb.set_trace()
            previous_cumulative = 0  
            for line in record.sieve_analysis_soundness_lines:
                print("Rows", str(line.percent_retained))
                previous_line = line.serial_no - 1

               

                # Normal sieve calculation
                if previous_line == 0:
                    cumulative_retained = line.percent_retained
                else:
                    previous_line_record = self.env['mechanical.sieve.analysis.line'].sudo().search([
                        ("serial_no", "=", previous_line),
                        ("parent_id", "=", record.id)
                    ], limit=1)
                    
                    if previous_line_record:
                        previous_cumulative = previous_line_record.cumulative_retained
                    cumulative_retained = previous_cumulative + line.percent_retained

                passing_percent = 100 - cumulative_retained

                # Write updated values
                line.write({
                    'cumulative_retained': round(cumulative_retained, 2),
                    'passing_percent': round(passing_percent, 2),
                })

                print("Updated Cumulative Retained:", cumulative_retained)
                print("Updated Passing Percent:", passing_percent)

                previous_cumulative = cumulative_retained


    ouantitative_name = fields.Char("Name",default="Quantitatively Examination :-")
    # sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

 
    ouantitative_soundness_lines = fields.One2many('coarse.ouantitative.line','parent_id',string="Sieve Analysis",default=lambda self: self._default_ouantitative_soundness_lines())

    
    @api.model
    def _default_ouantitative_soundness_lines(self):
        default_lines = [
            (0, 0, {'size': '+80mm'}),
            (0, 0, {'size': '80mm to 63mm'}),
            (0, 0, {'size': '63mm to 40mm'}),
            (0, 0, {'size': '40mm to 20mm'}),
            (0, 0, {'size': '20mm to 10mm'}),
            (0, 0, {'size': '10mm to 4.75mm'})
            
            
        ]
        return default_lines


    quantitative_name = fields.Char("Name",default="Quantitatively Examination")

    quantitative_soundness_lines = fields.One2many('coarse.quantitative.line','parent_id',string="Sieve Analysis",default=lambda self: self._default_quantitative_soundness_lines())

    
    @api.model
    def _default_quantitative_soundness_lines(self):
        default_lines = [
            (0, 0, {'passing': 'Above 80mm', 'retained': '80mm', 'sieve_magnesium': '80mm'}),
            (0, 0, {'passing': '80mm', 'retained': '63mm', 'sieve_magnesium': '63mm'}),
            (0, 0, {'passing': '63mm', 'retained': '40mm', 'sieve_magnesium': '31.5mm'}),
            (0, 0, {'passing': '40mm', 'retained': '20mm', 'sieve_magnesium': '16.0mm'}),
            (0, 0, {'passing': '20mm', 'retained': '10mm', 'sieve_magnesium': '8mm'}),
            (0, 0, {'passing': '10mm', 'retained': '4.75mm', 'sieve_magnesium': '4mm'}),
        ]
        return default_lines
    

    total_grading_sulphate = fields.Float(string="Total Grading of Original Sample  (%)s.Sodium Sulphate", digits=(8,2),compute="_compute_total_grading_sulphate",store=True)

    total_finalloss_sulphae= fields.Float(string="Total Final loss (%) Sulphate", digits=(8,2),compute="_compute_total_finalloss_sulphae",store=True)

    total_final_loss_manesium= fields.Float(string="Total Final loss (%) Magnesium", digits=(8,2),compute="_compute_total_final_loss_manesium",store=True)

    total_wt_fraction_sulhate= fields.Float(string="Total Weight of test Fraction  (retained) after test (gm) Sodium Sulphate", digits=(8,2),compute="_compute_total_wt_fraction_sulhate",store=True)

    total_wt_fraction_manesium= fields.Float(string="Total Weight of test Fraction  (retained) after test  (gm) Magnesium ", digits=(8,2),compute="_compute_total_wt_fraction_manesium",store=True)

    total_avg_sulphae= fields.Float(string="Total Weighted Average  (Corrected % loss) Sulphate", digits=(8,2),compute="_compute_total_avg_sulphae",store=True)

    total_avg_manesium= fields.Float(string="Total Weighted Average  (Corrected % loss) Magnesium ", digits=(8,2),compute="_compute_total_avg_manesium",store=True)




    @api.depends('quantitative_soundness_lines.grading_sulphate')
    def _compute_total_grading_sulphate(self):
        for record in self:
            record.total_grading_sulphate = sum(record.quantitative_soundness_lines.mapped('grading_sulphate'))


    @api.depends('quantitative_soundness_lines.finalloss_sulphae')
    def _compute_total_finalloss_sulphae(self):
        for record in self:
            record.total_finalloss_sulphae = sum(record.quantitative_soundness_lines.mapped('finalloss_sulphae'))

    @api.depends('quantitative_soundness_lines.final_loss_manesium')
    def _compute_total_final_loss_manesium(self):
        for record in self:
            record.total_final_loss_manesium = sum(record.quantitative_soundness_lines.mapped('final_loss_manesium'))

    @api.depends('quantitative_soundness_lines.wt_fraction_sulhate')
    def _compute_total_wt_fraction_sulhate(self):
        for record in self:
            record.total_wt_fraction_sulhate = sum(record.quantitative_soundness_lines.mapped('wt_fraction_sulhate'))
            
    @api.depends('quantitative_soundness_lines.wt_fraction_manesium')
    def _compute_total_wt_fraction_manesium(self):
        for record in self:
            record.total_wt_fraction_manesium = sum(record.quantitative_soundness_lines.mapped('wt_fraction_manesium'))

    @api.depends('quantitative_soundness_lines.avg_sulphae')
    def _compute_total_avg_sulphae(self):
        for record in self:
            record.total_avg_sulphae = sum(record.quantitative_soundness_lines.mapped('avg_sulphae'))



    @api.depends('quantitative_soundness_lines.avg_manesium')
    def _compute_total_avg_manesium(self):
        for record in self:
            record.total_avg_manesium = sum(record.quantitative_soundness_lines.mapped('avg_manesium'))


    total_avg_sulphae_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_total_avg_sulphae_conformity", store=True)

    @api.depends('total_avg_sulphae','eln_ref','grade')
    def _compute_total_avg_sulphae_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.total_avg_sulphae_conformity = 'na'
                continue
            record.total_avg_sulphae_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c8cd69bd-1f89-4f22-bae6-b81de73e6c2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c8cd69bd-1f89-4f22-bae6-b81de73e6c2')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.total_avg_sulphae - record.total_avg_sulphae*mu_value
                    upper = record.total_avg_sulphae + record.total_avg_sulphae*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.total_avg_sulphae_conformity = 'pass'
                        break
                    else:
                        record.total_avg_sulphae_conformity = 'fail'

    total_avg_sulphae_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_total_avg_sulphae_nabl", store=True)

    @api.depends('total_avg_sulphae','eln_ref','grade')
    def _compute_total_avg_sulphae_nabl(self):
        
        for record in self:
            record.total_avg_sulphae_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c8cd69bd-1f89-4f22-bae6-b81de73e6c2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c8cd69bd-1f89-4f22-bae6-b81de73e6c2')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.total_avg_sulphae - record.total_avg_sulphae*mu_value
                    upper = record.total_avg_sulphae + record.total_avg_sulphae*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.total_avg_sulphae_nabl = 'pass'
                        break
                    else:
                        record.total_avg_sulphae_nabl = 'fail'
    




    





    @api.depends('eln_ref')
    def _compute_visible(self):
        for record in self:
            record.crushing_visible = False
            record.abrasion_value_visible = False
            record.specific_gravity_visible = False
            record.water_absorption_visible = False
            record.impact_visible = False
            record.fine10_visible = False
            # record.soundness_na2so4_visible = False
            # record.soundness_mgso4_visible = False
            record.elongation_visible = False
            record.flakiness_visible = False
            # record.finer75_visible = False
            # record.clay_lump_visible = False
            # record.light_weight_visible = False
            record.loose_density_visible = False
            record.sieve_visible = False
            record.compacted_density_visible = False
            record.voids_compacted_density_visible = False
            record.voids_loose_density_visible = False
            record.rate_of_evaporation_visible = False
            record.soudness_visible = False
            record.soudness_magnesium_visible = False




            for sample in record.sample_parameters:
                if sample.internal_id == 'ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71':
                    record.crushing_visible = True
                if sample.internal_id == '37f2161e-5cc0-413f-b76c-10478c65baf9':
                    record.abrasion_value_visible = True
                if sample.internal_id == '3114db41-cfa7-49ad-9324-fcdbc9661038':
                    record.specific_gravity_visible = True
                if sample.internal_id == '22ee804f-41a3-4fd1-a301-a8d9180fba10':
                    record.water_absorption_visible = True
                if sample.internal_id == '2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2':
                    record.impact_visible = True
                if sample.internal_id == '5f506c08-4369-491d-93a6-030514c29661':
                    record.fine10_visible = True
                # if sample.internal_id == '153f3c8b-6ccb-4db0-b89d-02db61f61e81':
                #     record.soundness_na2so4_visible = True
                if sample.internal_id == '8b80bc59-f49e-483e-8ccd-2fb4b076620e':
                    record.soudness_magnesium_visible = True
                    
                if sample.internal_id == '9effe915-e5a3-45a7-aaeb-10caababd667':
                    record.elongation_visible = True
                    # record.flakiness_visible = True

                if sample.internal_id == 'be7a60bc-bb2c-410d-b91a-4f8730a4ac6f':
                    record.flakiness_visible = True
                    # record.elongation_visible = True
                # if sample.internal_id == '988f5bf6-c865-453c-9cd6-993a5a59ad95':
                #     record.finer75_visible = True
                # if sample.internal_id == 'd7e389bc-21ad-41eb-a602-f448f996eb2f':
                #     record.clay_lump_visible = True
                # if sample.internal_id == 'e7cc6b68-2550-4e1e-a28e-8526295e733f':
                #     record.light_weight_visible = True
                if sample.internal_id == '65a41d1f-d557-438e-8fd1-2c619a334d02':
                    record.loose_density_visible = True
                if sample.internal_id == 'c2168fff-e47c-4155-99ff-9d7dc223e768':
                    record.sieve_visible = True

                if sample.internal_id == '357f579d-a310-4015-bc11-28a85c53ac83':
                    record.compacted_density_visible  = True

                if sample.internal_id == '04a95dc1-4b45-4817-a9b2-dd722bbe6281':
                    record.voids_compacted_density_visible = True
                
                if sample.internal_id == '919587f2-5b45-4da1-bb73-10164b861833':
                    record.voids_loose_density_visible = True

                if sample.internal_id == '8e9d9c62-e634-47a2-a689-2c6c8538493c':
                    record.rate_of_evaporation_visible = True

                if sample.internal_id == 'c8cd69bd-1f89-4f22-bae6-b81de73e6c2':
                    record.soudness_visible = True




    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:

            # Elongation
            if result.parameter.internal_id == '9effe915-e5a3-45a7-aaeb-10caababd667':
                result.result_char = round(self.elongation_index,2)
                if self.elongation_index_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Flakiness
            if result.parameter.internal_id == 'be7a60bc-bb2c-410d-b91a-4f8730a4ac6f':
                result.result_char = round(self.flakiness_index,2)
                if self.flakiness_index_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # specific gravity 
            if result.parameter.internal_id == '3114db41-cfa7-49ad-9324-fcdbc9661038':
                result.result_char = round(self.avg_specific_gravity,2)
                if self.avg_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # water absorbtion
            if result.parameter.internal_id == '22ee804f-41a3-4fd1-a301-a8d9180fba10':
                result.result_char = round(self.avg_water_absorption,2)
                if self.avg_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            # impact value 
            if result.parameter.internal_id == '2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2':
                result.result_char = round(self.average_impact_value,2)
                if self.impact_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # crushing value 
            if result.parameter.internal_id == 'ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71':
                result.result_char = round(self.average_crushing_value,2)
                if self.average_crushing_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            

            # Abrasion Value
            if result.parameter.internal_id == '37f2161e-5cc0-413f-b76c-10478c65baf9':
                result.result_char = round(self.avg_abrasion_value,2)
                if self.avg_abrasion_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # 10 % fine Values
            if result.parameter.internal_id == '5f506c08-4369-491d-93a6-030514c29661':
                result.result_char = round(self.avg_load_for_10fine,2)
                if self.avg_load_for_10fine_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Compacted density
            if result.parameter.internal_id == '357f579d-a310-4015-bc11-28a85c53ac83':
                result.result_char = round(self.compacted_density,2)
                if self.compacted_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Loose Density
            if result.parameter.internal_id == '65a41d1f-d557-438e-8fd1-2c619a334d02':
                result.result_char = round(self.loose_density,2)
                if self.loose_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # % void Compacted density
            if result.parameter.internal_id == '04a95dc1-4b45-4817-a9b2-dd722bbe6281':
                result.result_char = round(self.voids_compacted_density,2)
                if self.voids_compacted_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # % void Loose density
            if result.parameter.internal_id == '919587f2-5b45-4da1-bb73-10164b861833':
                result.result_char = round(self.voids_loose_density,2)
                if self.voids_loose_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Rate Of Evaporation
            if result.parameter.internal_id == '8e9d9c62-e634-47a2-a689-2c6c8538493c':
                result.result_char = round(self.avg_rate_evaporation,2)
                if self.avg_rate_evaporation_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Soundness Test
            if result.parameter.internal_id == 'c8cd69bd-1f89-4f22-bae6-b81de73e6c2':
                result.result_char = round(self.total_avg_sulphae,2)
                if self.total_avg_sulphae_nabl == 'pass':
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
        record = super(CoarseAggregateMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()
        self.default_get(fields)

        return super(CoarseAggregateMechanical, self).read(fields=fields, load=load)

   
    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['mechanical.coarse.aggregate'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id






class SieveAnalysisLine(models.Model):
    _name = "mechanical.coarse.aggregate.sieve.analysis.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size mm")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    percent_retained = fields.Float(string='Cummulative Weight Retained in (gms)', compute="_compute_percent_retained",digits=(16,2))
    cumulative_retained = fields.Float(string="% of Cumulative Wt. Retained ", compute="_compute_cumulative__retained",  store=True,digits=(16,2))
    passing_percent = fields.Float(string="% of wt passing",compute="_compute_passing_percent",digits=(16,2))
    specific_limits = fields.Char(string="Specified Limits",store=True)



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SieveAnalysisLine, self).create(vals)

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

            new_self = super(SieveAnalysisLine, self).write(vals)

            if 'wt_retained' in vals:
                for record in self:
                    # record.parent_id._compute_total()
                    pass

            return new_self

        return super(SieveAnalysisLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(SieveAnalysisLine, self).unlink()

        if parent_id:
            parent_id.sieve_analysis_child_lines._reorder_serial_numbers()

        return res





    # @api.depends('wt_retained', 'parent_id.weight_of_sample')
    # def _compute_percent_retained(self):
    #     for record in self:
    #         try:
    #             record.percent_retained = (record.wt_retained / record.parent_id.weight_of_sample) * 100
    #         except ZeroDivisionError:
    #             record.percent_retained = 0


    # @api.depends('wt_retained')
    # def _compute_percent_retained(self):
    #     cumulative = 0
    #     for record in self:
    #         # Get all previous records with an ID less than or equal to this one (or in the same group)
    #         records_to_sum = self.search([('id', '<=', record.id)])
    #         cumulative = sum(r.wt_retained for r in records_to_sum)
    #         record.percent_retained = cumulative

    @api.depends('percent_retained', 'parent_id.weight_of_sample')
    def _compute_cumulative__retained(self):
        for record in self:
            try:
                # import wdb;wdb.set_trace()
                record.cumulative_retained = (record.percent_retained / record.parent_id.weight_of_sample) * 100
            except ZeroDivisionError:
                record.cumulative_retained = 0


    

    @api.depends('wt_retained', 'parent_id.sieve_analysis_child_lines.wt_retained')
    def _compute_percent_retained(self):
        for record in self:
            cumulative = 0.0
            found = False

            for line in sorted(record.parent_id.sieve_analysis_child_lines, key=lambda l: l.serial_no):
                cumulative += line.wt_retained or 0.0
                if line.id == record.id:
                    found = True
                    record.percent_retained = cumulative
                    break

            if not found:
                record.percent_retained = 0.0

    @api.onchange('cumulative_retained')
    def _compute_passing_percent(self):
        for record in self:
            record.passing_percent = 100 - record.cumulative_retained
        
    


    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines, key=lambda r: r.id)
            # index = sorted_lines.index(record)
            # print("Working")


    



    @api.depends('cumulative_retained')
    def _compute_cum_retained(self):
        self.cumulative_retained=0
        


    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines, key=lambda r: r.id)
            # index = sorted_lines.index(record)
            # print("Working")


class RateOfEvaporation(models.Model):
    _name = "mechanical.rate.of.evaporation.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    sr_no = fields.Integer(string="Beaker", readonly=True, copy=False, default=1)
    W1 = fields.Float(string="W1 = Weight of beaker + water before evaporation.")
    W2 = fields.Float(string="W2 = Weight of beaker + water after 4 hr evaporation.")
    W3 = fields.Float(string="W3 = ( W1 - W2 )",compute="_compute_W3")
    rate_evaporation = fields.Float(string="Rate of Evaporation (gm/h)",compute="_compute_rate_evaporation")

    @api.depends('W1','W2')
    def _compute_W3(self):
        for record in self:
            record.W3 = (record.W1 - record.W2)

    @api.depends('W3')
    def _compute_rate_evaporation(self):
        for record in self:
            record.rate_evaporation = (record.W3 / 4)


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(RateOfEvaporation, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1
    





   


class ElongationIndexLine(models.Model):
    _name = "mechanical.elongation.index.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No", readonly=True, copy=False, default=1)
    sieve_size_passing = fields.Float(string="Passing")
    sieve_size_retained = fields.Float(string="Retained")
    length_gauge = fields.Float(string="Length Gauge mm	")
    weight_retained_el_char = fields.Char(string="Weight Retained on each Sieve (W’n) gms")
    weight_retained_el = fields.Float(string="Weight Retained on each Sieve (W’n) gms") 
    percent_retained_el = fields.Float(string="% Retained on each Sieve X’n = (W’n/W’)x100",compute="_compute_percent_retained_el")
    percent_retained_el_char = fields.Char(string="% Retained on each Sieve X’n")
    weight_retained_mat_elongated = fields.Float(string="Weight Retained Elongated Material (P’n) gms	")
    weight_retained_mat_elongated_char = fields.Char(string="Weight Retained Elongated Material (P’n) gms")
    percent_retained_material =  fields.Float(string="% Retained Material Y’n = (P’n/W’n)x100",compute="_compute_percent_retained_material")
    percent_retained_material_cha = fields.Char(string="% Retained Material Y’n")
    total_percent_retained_el = fields.Float(string="(X’n x Y’n)",compute="_compute_total_percent_retained_el")
    # wt_retained = fields.Integer(string="Wt Retained (in gms)")
    # elongated_retain = fields.Float(string="Elongated Retained (in gms)")
    # flaky_passing = fields.Float(string="Flaky Passing (in gms)")
    



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(ElongationIndexLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



    @api.depends('parent_id.total_weight_retained_el','weight_retained_el')
    def _compute_percent_retained_el(self):
        for record in self:
            try:
                record.percent_retained_el = round((record.weight_retained_el /record.parent_id.total_weight_retained_el) * 100,2)
            except ZeroDivisionError:
                record.percent_retained_el = 0
    


    @api.depends('weight_retained_el','weight_retained_mat_elongated')
    def _compute_percent_retained_material(self):
        for record in self:
            try:
                record.percent_retained_material = round((record.weight_retained_mat_elongated/record.weight_retained_el)*100,2)
            except ZeroDivisionError:
                record.percent_retained_material = 0

    @api.depends('percent_retained_el','percent_retained_material')
    def _compute_total_percent_retained_el(self):
        for record in self:
            try:
                record.total_percent_retained_el = (record.percent_retained_el * record.percent_retained_material)
            except ZeroDivisionError:
                record.total_percent_retained_el = 0


class FlakinessIndexLine(models.Model):
    _name = "mechanical.flakiness.index.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No", readonly=True, copy=False, default=1)
    sieve_size_passing_fl = fields.Float(string="Passing")
    sieve_size_retained_fl = fields.Float(string="Retained")
    length_gauge_fl = fields.Float(string="Thickness Gauge-MM")

    weight_retained_fl_char = fields.Char(string="Wt. Retained on each Sieve (Wn) gms")
    weight_retained_fl = fields.Float(string="Wt. Retained on each Sieve (Wn) gms") 

    percent_retained_fl = fields.Float(string="% Retained on each Sieve Xn = (Wn/W)x100",compute="_compute_percent_retained_fl")
    percent_retained_fl_char = fields.Char(string="% Retained on each Sieve Xn = (Wn/W)x100")

    weight_retained_mat_fl = fields.Float(string="Wt. Passing through Gauge (Pn) gms.")
    weight_retained_mat_fl_char = fields.Char(string="Wt. Passing through Gauge (Pn) gms.")

    percent_retained_material_fl =  fields.Float(string="% Passing through Gauge Yn = (Pn/Wn)x100",compute="_compute_percent_retained_material_fl")
    percent_retained_material_fl_char = fields.Char(string="% Passing through Gauge Yn = (Pn/Wn)x100")

    total_percent_retained_fl = fields.Float(string="(X’n x Y’n)",compute="_compute_total_percent_retained_fl")
    # wt_retained = fields.Integer(string="Wt Retained (in gms)")
    # elongated_retain = fields.Float(string="Elongated Retained (in gms)")
    # flaky_passing = fields.Float(string="Flaky Passing (in gms)")
    



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(FlakinessIndexLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



    @api.depends('parent_id.total_weight_retained_fl','weight_retained_fl')
    def _compute_percent_retained_fl(self):
        for record in self:
            try:
                record.percent_retained_fl = round((record.weight_retained_fl /record.parent_id.total_weight_retained_fl) * 100,2)
            except ZeroDivisionError:
                record.percent_retained_fl = 0
    


    @api.depends('weight_retained_fl','weight_retained_mat_fl')
    def _compute_percent_retained_material_fl(self):
        for record in self:
            try:
                record.percent_retained_material_fl = round((record.weight_retained_mat_fl/record.weight_retained_fl)*100,2)
            except ZeroDivisionError:
                record.percent_retained_material_fl = 0

    @api.depends('percent_retained_fl','percent_retained_material_fl')
    def _compute_total_percent_retained_fl(self):
        for record in self:
            try:
                record.total_percent_retained_fl = (record.percent_retained_fl * record.percent_retained_material_fl)
            except ZeroDivisionError:
                record.total_percent_retained_fl = 0

   







class AbrasionValueLine(models.Model):
    _name = "mechanical.abrasion.value.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")
   
    sr_no = fields.Integer(string="Test", readonly=True, copy=False, default=1)
    sieve_passing_ab = fields.Float(string="Passing – mm")
    sieve_retained_ab = fields.Float(string="Retained -  mm")
    grade_a = fields.Char(string="A")
    grade_b = fields.Char(string="B")
    grade_c = fields.Char(string="C")
    grade_d = fields.Char(string="D")
    grade_e = fields.Char(string="E")
    grade_f = fields.Char(string="F")
    grade_g = fields.Char(string="G")


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(AbrasionValueLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1

class AbrasionValueSecondLine(models.Model):
    _name = "mechanical.abrasion.value.second.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")


    # Second table
    sr_no1 = fields.Integer(string="Test", readonly=True, copy=False, default=1)
    grading_ab = fields.Char(string="Grading")
    grade_a1 = fields.Char(string="A")
    grade_b2 = fields.Char(string="B")
    grade_c3 = fields.Char(string="C")
    grade_d4 = fields.Char(string="D")
    grade_e5 = fields.Char(string="E")
    grade_f6 = fields.Char(string="F")
    grade_g7 = fields.Char(string="G")







    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no1'))
                vals['sr_no1'] = max_serial_no + 1

        return super(AbrasionValueSecondLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no1 = index + 1




class SoudnessLine(models.Model):
    _name = "coarse.soudness.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    serial_no = fields.Integer(string="Cycle No", readonly=True, copy=False, default=1)

    immersed_datetime = fields.Datetime(string="Date & Time of Sample immersed in Solution for 16 to 18 hrs.")
    temp_solution = fields.Float(string="Temp. of Solution (°C)", digits=(6,2))
    specific_gravity_solution = fields.Float(string="Specific Gravity of Solution", digits=(8,3))
    removed_datetime = fields.Datetime(string="Date & Time of Sample Removed from Solution")
    oven_datetime = fields.Datetime(string="Date & Time of Sample Kept in Oven (105 to 1100C) for Drying ")

    hours_1 = fields.Char(string="Hours 1",compute="_compute_hours_1",store=True)
    hours_2 = fields.Char(string="Hours 2",compute="_compute_hours_2",store=True)
    hours_3 = fields.Char(string="Hours 3",compute="_compute_hours_3",store=True)

    @api.depends('oven_datetime', 'parent_id.soudness_child_lines.immersed_datetime')
    def _compute_hours_1(self):
        """
        Compute hours_1 = (Next line's immersed_datetime) - (Current line's oven_datetime)
        """
        for rec in self:
            rec.hours_1 = False
            if not rec.oven_datetime or not rec.parent_id:
                continue

            lines = rec.parent_id.soudness_child_lines.sorted(key=lambda l: l.serial_no)
            line_list = list(lines)

            if rec in line_list:
                current_index = line_list.index(rec)
                # check next line exists
                if current_index + 1 < len(line_list):
                    next_line = line_list[current_index + 1]
                    if next_line.immersed_datetime:
                        diff = next_line.immersed_datetime - rec.oven_datetime
                        total_seconds = diff.total_seconds()
                        if total_seconds > 0:
                            hours = int(total_seconds // 3600)
                            minutes = int((total_seconds % 3600) // 60)
                            seconds = int(total_seconds % 60)
                            rec.hours_1 = f"{hours:02}:{minutes:02}:{seconds:02}"
                        else:
                            rec.hours_1 = "00:00:00"

    # ---------------- HOURS 2 -----------------
    @api.depends('immersed_datetime', 'removed_datetime')
    def _compute_hours_2(self):
        """Compute Hours 2 = removed_datetime - immersed_datetime"""
        for rec in self:
            rec.hours_2 = False
            if rec.immersed_datetime and rec.removed_datetime:
                diff = rec.removed_datetime - rec.immersed_datetime
                total_seconds = diff.total_seconds()
                if total_seconds > 0:
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    seconds = int(total_seconds % 60)
                    rec.hours_2 = f"{hours:02}:{minutes:02}:{seconds:02}"
                else:
                    rec.hours_2 = "00:00:00"


    @api.depends('removed_datetime', 'oven_datetime')
    def _compute_hours_3(self):
        """Compute Hours 2 = oven_datetime - removed_datetime"""
        for rec in self:
            rec.hours_3 = False
            if rec.removed_datetime and rec.oven_datetime:
                diff = rec.oven_datetime - rec.removed_datetime
                total_seconds = diff.total_seconds()
                if total_seconds > 0:
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    seconds = int(total_seconds % 60)
                    rec.hours_3 = f"{hours:02}:{minutes:02}:{seconds:02}"
                else:
                    rec.hours_3 = "00:00:00"

    



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SoudnessLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class SieveAnalysisSoudnesLine(models.Model):
    _name = "mechanical.sieve.analysis.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size")
    particle_size = fields.Char(string="Retained")
    wt_retained = fields.Float(string="Wt. Retained before test(gm)")
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained")
    wt_sample_testing = fields.Char(string="Weight of sample for testing (gm)",compute="_compute_wt_sample_testing_display")
    actual_wt = fields.Float(string="Actual Weight of sample taken (gm)")
    cumulative_retained = fields.Float(string="Cum. Retained %",compute="_compute_cum_retained" , store=True)
    passing_percent = fields.Float(string="% Passing ")

    # @api.onchange('cumulative_retained')
    # def _compute_passing_percent(self):
    #     for record in self:
    #         record.passing_percent = 100 - record.cumulative_retained

    @api.depends('percent_retained')
    def _compute_wt_sample_testing_display(self):
        for rec in self:
            if rec.percent_retained < 5:
                rec.wt_sample_testing = "-"
            else:
                rec.wt_sample_testing = "100"


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SieveAnalysisSoudnesLine, self).create(vals)

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

            new_self = super(SieveAnalysisSoudnesLine, self).write(vals)

            if 'wt_retained' in vals:
                for record in self:
                    # record.parent_id._compute_total()
                    pass

            return new_self

        return super(SieveAnalysisSoudnesLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(SieveAnalysisSoudnesLine, self).unlink()

        if parent_id:
            parent_id.sieve_analysis_soundness_lines._reorder_serial_numbers()

        return res


    @api.depends('wt_retained', 'parent_id.wt_of_sample')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = (record.wt_retained / record.parent_id.wt_of_sample) * 100 if record.parent_id.wt_of_sample else 0.0
            except ZeroDivisionError:
                record.percent_retained = 0.0



    # @api.depends('cumulative_retained')
    # def _compute_cum_retained(self):
    #     self.cumulative_retained=0

    @api.depends('percent_retained', 'parent_id.sieve_analysis_soundness_lines.percent_retained')
    def _compute_cum_retained(self):
        for record in self:
            cumulative = 0.0
            found = False

            for line in sorted(record.parent_id.sieve_analysis_soundness_lines, key=lambda l: l.serial_no):
                cumulative += line.percent_retained or 0.0
                if line.id == record.id:
                    found = True
                    record.cumulative_retained = cumulative
                    break

            if not found:
                record.cumulative_retained = 0.0

        
    


    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_soundness_lines, key=lambda r: r.id)
            # index = sorted_lines.index(record)
            # print("Working")

class OuantitativelyExaminationLine(models.Model):
    _name = "coarse.ouantitative.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    serial_no = fields.Integer(string="Cycle No", readonly=True, copy=False, default=1)

    size = fields.Char(string="Size")
    cycle = fields.Float(string="Test Cycle ")
    original_sulphate = fields.Float(string="Original wt. of Sample-gms.Sodium Sulphate", digits=(8,3),compute="_compute_original_sulphate",store=True)
    original_magnesiu = fields.Float(string="Original wt. of Sample-gms.Magnesium ", digits=(8,3))
    wt_sulhate = fields.Float(string="Weight Retained After  5 Cycle-gms Sodium Sulphate")
    wt_manesium = fields.Float(string="Weight Retained After  5 Cycle-gms Magnesium ")
    loss_sulphae = fields.Float(string="% Loss Sodium Sulphate",compute="_compute_loss_sulphae",digits=(12,2))
    loss_manesium = fields.Float(string="% Loss Magnesium ")

    @api.depends('serial_no', 'parent_id.sieve_analysis_soundness_lines')
    def _compute_original_sulphate(self):
        for rec in self:
            if rec.parent_id:
                line = rec.parent_id.sieve_analysis_soundness_lines.filtered(
                    lambda l: l.serial_no == rec.serial_no
                )[:1]
                rec.original_sulphate = line.actual_wt if line else 0.0
            else:
                rec.original_sulphate = 0.0

    @api.depends('original_sulphate', 'wt_sulhate')
    def _compute_loss_sulphae(self):
        """Compute % Loss Sodium Sulphate"""
        for rec in self:
            if not rec.original_sulphate or rec.wt_sulhate == 0:
                rec.loss_sulphae = 0.0
            else:
                rec.loss_sulphae = round(((rec.original_sulphate - rec.wt_sulhate) / rec.wt_sulhate) * 100, 2)


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(OuantitativelyExaminationLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class QuantitativelyExaminationLine(models.Model):
    _name = "coarse.quantitative.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")

    serial_no = fields.Integer(string="Cycle No", readonly=True, copy=False, default=1)

    passing = fields.Char(string="Sieve Size-mm Passing")
    retained = fields.Char(string="Sieve Size-mm Retained")
    grading_sulphate = fields.Float(string="Grading of Original Sample  (%)s.Sodium Sulphate", digits=(8,2),compute="_compute_grading_sulphate",store=True)
    sieve_magnesium = fields.Char(string="Sieve Used For Loss  Determination.Magnesium ")
    wt_fraction_sulhate = fields.Float(string="Weight of test Fraction  (retained) after test (gm) Sodium Sulphate",compute="_compute_wt_fraction_sulhate",store=True)
    wt_fraction_manesium = fields.Float(string="Weight of test Fraction  (retained) after test  (gm) Magnesium ")
    finalloss_sulphae = fields.Float(string="Final loss (%) Sulphate",compute="_compute_finalloss_sulphae",store="_compute_finalloss_sulphae")
    final_loss_manesium = fields.Float(string="Final loss (%) Magnesium ")

    avg_sulphae = fields.Float(string="Weighted Average  (Corrected % loss) Sulphate",compute="_compute_avg_sulphae",store=True)
    avg_manesium = fields.Float(string="Weighted Average  (Corrected % loss) Magnesium ")

    @api.depends('finalloss_sulphae', 'grading_sulphate')
    def _compute_avg_sulphae(self):
        for rec in self:
            rec.avg_sulphae = (rec.finalloss_sulphae * rec.grading_sulphate) / 100 if rec.grading_sulphate else 0.0

    # @api.depends('parent_id.sieve_analysis_soundness_lines', 'parent_id.ouantitative_soundness_lines')
    # def _compute_finalloss_sulphae(self):
    #     for rec in self:
    #         # percent_retained from sieve_analysis_soundness_lines
    #         sieve_line = rec.parent_id.sieve_analysis_soundness_lines.filtered(lambda l: l.serial_no == rec.serial_no)[:1]
    #         percent_ret = sieve_line.percent_retained if sieve_line else 0.0

    #         # loss_sulphae from ouantitative_soundness_lines
    #         ou_line = rec.parent_id.ouantitative_soundness_lines.filtered(lambda l: l.serial_no == rec.serial_no)[:1]
    #         loss_sulphae_val = ou_line.loss_sulphae if ou_line else 0.0

    #         if 0 < percent_ret < 5:
    #             rec.finalloss_sulphae = 0.0  # किंवा आधीची value
    #         else:
    #             rec.finalloss_sulphae = loss_sulphae_val

    @api.depends('parent_id.sieve_analysis_soundness_lines', 'parent_id.ouantitative_soundness_lines')
    def _compute_finalloss_sulphae(self):
     for idx, rec in enumerate(self):
        sieve_lines = rec.parent_id.sieve_analysis_soundness_lines.sorted('serial_no')
        quant_lines = rec.parent_id.ouantitative_soundness_lines.sorted('serial_no')
        percent_ret = 0.0
        loss_sulphae_val = 0.0

        # Find the matching sieve and quantitative line
        sieve_line = next((l for l in sieve_lines if l.serial_no == rec.serial_no), None)
        if sieve_line:
            percent_ret = sieve_line.percent_retained

        quant_line = next((l for l in quant_lines if l.serial_no == rec.serial_no), None)
        if quant_line:
            loss_sulphae_val = quant_line.loss_sulphae

        # Boundary logic
        if idx == 0:  # First item
            next_loss_val = quant_lines[idx+1].loss_sulphae if len(quant_lines) > idx+1 else loss_sulphae_val
            avg_val = next_loss_val  # Use next value only
        elif idx == len(self)-1:  # Last item
            prev_loss_val = quant_lines[idx-1].loss_sulphae if idx > 0 else loss_sulphae_val
            avg_val = prev_loss_val  # Use previous value only
        else:  # Middle items
            prev_loss_val = quant_lines[idx-1].loss_sulphae
            next_loss_val = quant_lines[idx+1].loss_sulphae
            avg_val = (prev_loss_val + next_loss_val) / 2 if (prev_loss_val is not None and next_loss_val is not None) else loss_sulphae_val

        if 0 < percent_ret < 5:
            rec.finalloss_sulphae = avg_val
        else:
            rec.finalloss_sulphae = loss_sulphae_val

            

    @api.depends('serial_no', 'parent_id.sieve_analysis_soundness_lines')
    def _compute_grading_sulphate(self):
        for rec in self:
            if rec.parent_id:
                line = rec.parent_id.sieve_analysis_soundness_lines.filtered(
                    lambda l: l.serial_no == rec.serial_no
                )[:1] 
                rec.grading_sulphate = line.percent_retained if line else 0.0
            else:
                rec.grading_sulphate = 0.0

    @api.depends('serial_no', 'parent_id.ouantitative_soundness_lines')
    def _compute_wt_fraction_sulhate(self):
        for rec in self:
            if rec.parent_id:
                line = rec.parent_id.ouantitative_soundness_lines.filtered(
                    lambda l: l.serial_no == rec.serial_no
                )[:1]
                rec.wt_fraction_sulhate = line.wt_sulhate if line else 0.0
            else:
                rec.wt_fraction_sulhate = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(QuantitativelyExaminationLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



    
    

