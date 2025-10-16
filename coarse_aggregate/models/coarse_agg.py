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
            ('fail', 'Fail')], string="Conformity", compute="_compute_average_crushing_value_conformity", store=True)

    @api.depends('average_crushing_value','eln_ref','grade')
    def _compute_average_crushing_value_conformity(self):
        
        for record in self:
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


    

    # Abrasion Value
    abrasion_value_name = fields.Char("Name",default="Los Angeles Abrasion Value")
    abrasion_visible = fields.Boolean("Abrasion Visible",compute="_compute_visible")

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    total_weight_sample_abrasion = fields.Float(string="Total weight of Sample in gms")
    weight_passing_sample_abrasion = fields.Float(string="Weight of Passing sample in 1.70 mm IS sieve in gms")
    weight_retain_sample_abrasion = fields.Integer(string="Weight of Retain sample in 1.70 mm IS sieve in gms",compute="_compute_weight_retain_sample_abrasion")
    abrasion_value_percentage = fields.Float(string="Abrasion Value (%)",compute="_compute_sample_weight")

    abrasion_value_percentage_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_abrasion_value_percentager_conformity", store=True)

    @api.depends('abrasion_value_percentage','eln_ref','grade')
    def _compute_abrasion_value_percentager_conformity(self):
        
        for record in self:
            record.abrasion_value_percentage_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37f2161e-5cc0-413f-b76c-10478c65baf9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37f2161e-5cc0-413f-b76c-10478c65baf9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.abrasion_value_percentage - record.abrasion_value_percentage*mu_value
                    upper = record.abrasion_value_percentage + record.abrasion_value_percentage*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.abrasion_value_percentage_conformity = 'pass'
                        break
                    else:
                        record.abrasion_value_percentage_conformity = 'fail'

    abrasion_value_percentage_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_abrasion_value_percentage_nabl", store=True)

    @api.depends('abrasion_value_percentage','eln_ref','grade')
    def _compute_abrasion_value_percentage_nabl(self):
        
        for record in self:
            record.abrasion_value_percentage_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37f2161e-5cc0-413f-b76c-10478c65baf9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','37f2161e-5cc0-413f-b76c-10478c65baf9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.abrasion_value_percentage - record.abrasion_value_percentage*mu_value
                    upper = record.abrasion_value_percentage + record.abrasion_value_percentage*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.abrasion_value_percentage_nabl = 'pass'
                        break
                    else:
                        record.abrasion_value_percentage_nabl = 'fail'




    @api.depends('total_weight_sample_abrasion', 'weight_passing_sample_abrasion')
    def _compute_weight_retain_sample_abrasion(self):
        for line in self:
            line.weight_retain_sample_abrasion = line.total_weight_sample_abrasion - line.weight_passing_sample_abrasion


    @api.depends('total_weight_sample_abrasion', 'weight_passing_sample_abrasion')
    def _compute_sample_weight(self):
        for line in self:
            if line.total_weight_sample_abrasion != 0:
                line.abrasion_value_percentage = (line.weight_passing_sample_abrasion / line.total_weight_sample_abrasion) * 100
            else:
                line.abrasion_value_percentage = 0.0


    # Specific Gravety 
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


    specific_gravity_1 = fields.Float(string="Specific Gravity",compute="_compute_specific_gravity_1")
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

    specific_gravity_2 = fields.Float(string="Specific Gravity",compute="_compute_specific_gravity_2")
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
            line.avg_specific_gravity = (line.specific_gravity_1 + line.specific_gravity_1)/2
    
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
            ('fail', 'Fail')], string="Specific Gravity Conformity", compute="_compute_avg_specific_gravity_conformity", store=True)

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_conformity(self):
        
        for record in self:
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
            ('fail', 'Fail')], string="Water Absorption Conformity", compute="_compute_avg_water_absorption_conformity", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_conformity(self):
        
        for record in self:
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
            ('fail', 'Fail')], string="Conformity", compute="_compute_average_impact_value_conformity", store=True)

    @api.depends('average_impact_value','eln_ref','grade')
    def _compute_average_impact_value_conformity(self):
        
        for record in self:
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


    # @api.depends('impact_value_child_lines.impact_value')
    # def _compute_average_impact_value(self):
    #     for record in self:
    #         if record.impact_value_child_lines:
    #             sum_impact_value = sum(record.impact_value_child_lines.mapped('impact_value'))
    #             record.average_impact_value = ((sum_impact_value / len(record.impact_value_child_lines)))
    #         else:
    #             record.average_impact_value = 0.0

    # @api.model
    # def create(self, vals):
    #     # import wdb;wdb.set_trace()
    #     record = super(coarseAggregateMechanical, self).create(vals)
    #     record.parameter_id.write({'model_id':record.id})
    #     return record
   
    # !0% Fine Value
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


    @api.depends('wt_of_aggregate_passing_sieve_10fine', 'wt_of_aggregate_crush_10fine')
    def _compute_load_for_10fine(self):
        for rec in self:
              rec.load_for_10fine = round( ((14 * rec.load_for_penetration_tonnes )/ (rec.percent_fine_passing_sieve + 4)) ,2)



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


    @api.depends('wt_of_aggregate_passing_sieve_10fine_2', 'wt_of_aggregate_crush_10fine_2')
    def _compute_load_for_10fine_2(self):
        for rec in self:
              rec.load_for_10fine_2 = round( ((14 * rec.load_for_penetration_tonnes_2 )/ (rec.percent_fine_passing_sieve_2 + 4)) ,2)   




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
            ('fail', 'Fail')], string="Conformity", compute="_compute_compacted_density_conformity", store=True)

    @api.depends('avg_load_for_10fine','eln_ref','grade')
    def _compute_avg_load_for_10fine_conformity(self):
        
        for record in self:
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

    
    

    # Soundness Na2SO4
    soundness_na2so4_name = fields.Char("Name",default="Soundness Na2SO4")
    soundness_na2so4_visible = fields.Boolean("Soundness Na2SO4 Visible",compute="_compute_visible")

    soundness_na2so4_child_lines = fields.One2many('mechanical.soundness.na2so4.line','parent_id',string="Parameter",default=lambda self: self._default_soundness_na2so4_child_lines())
    total_na2so4 = fields.Integer(string="Total",compute="_compute_total_na2so4")
    soundness_na2so4 = fields.Float(string="Soundness",compute="_compute_soundness_na2so4")

    total_grading = fields.Float(string="Total Grading of Original sample in %", compute="_compute_total_grading")

    @api.depends('soundness_na2so4_child_lines.grading_original_sample')
    def _compute_total_grading(self):
        for record in self:
            total_grading = sum(line.grading_original_sample for line in record.soundness_na2so4_child_lines)
            record.total_grading = total_grading


    total_weight_before = fields.Float(string="Total Weight of test fraction before test in gm", compute="_compute_total_weight")

    @api.depends('soundness_na2so4_child_lines.weight_before_test')
    def _compute_total_weight(self):
        for record in self:
            total_weight_before = sum(line.weight_before_test for line in record.soundness_na2so4_child_lines)
            record.total_weight_before = total_weight_before

    total_weight_after = fields.Float(string="Total Weight of test feaction Passing Finer Sieve After ", compute="_compute_total_weight_after")

    @api.depends('soundness_na2so4_child_lines.weight_after_test')
    def _compute_total_weight_after(self):
        for record in self:
            total_weight_after = sum(line.weight_after_test for line in record.soundness_na2so4_child_lines)
            record.total_weight_after = total_weight_after

    total_commulative = fields.Float(string="Total Commulative percentage Loss", compute="_compute_total_cumulative")

    @api.depends('soundness_na2so4_child_lines.cumulative_loss_percent')
    def _compute_total_cumulative(self):
        for record in self:
            total_commulative = sum(line.cumulative_loss_percent for line in record.soundness_na2so4_child_lines)
            record.total_commulative = total_commulative
    

    @api.depends('soundness_na2so4_child_lines.weight_before_test')
    def _compute_total_na2so4(self):
        for record in self:
            record.total_na2so4 = sum(record.soundness_na2so4_child_lines.mapped('weight_before_test'))
    

    @api.depends('soundness_na2so4_child_lines.cumulative_loss_percent')
    def _compute_soundness_na2so4(self):
        for record in self:
            record.soundness_na2so4 = round((sum(record.soundness_na2so4_child_lines.mapped('cumulative_loss_percent'))),2)


    @api.model
    def _default_soundness_na2so4_child_lines(self):
        default_lines = [
            (0, 0, {'sieve_size_passing': '63 mm', 'sieve_size_retained': '40 mm'}),
            (0, 0, {'sieve_size_passing': '40 mm', 'sieve_size_retained': '20 mm'}),
            (0, 0, {'sieve_size_passing': '20 mm', 'sieve_size_retained': '10 mm'}),
            (0, 0, {'sieve_size_passing': '10 mm', 'sieve_size_retained': '4.75 mm'})
           
        ]
        return default_lines


    soundness_na2so4_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_soundness_na2so4_conformity", store=True)

    @api.depends('soundness_na2so4','eln_ref','grade')
    def _compute_soundness_na2so4_conformity(self):
        
        for record in self:
            record.soundness_na2so4_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','153f3c8b-6ccb-4db0-b89d-02db61f61e81')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','153f3c8b-6ccb-4db0-b89d-02db61f61e81')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.soundness_na2so4 - record.soundness_na2so4*mu_value
                    upper = record.soundness_na2so4 + record.soundness_na2so4*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.soundness_na2so4_conformity = 'pass'
                        break
                    else:
                        record.soundness_na2so4_conformity = 'fail'

    soundness_na2so4_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_soundness_na2so4_nabl", store=True)

    @api.depends('soundness_na2so4','eln_ref','grade')
    def _compute_soundness_na2so4_nabl(self):
        
        for record in self:
            record.soundness_na2so4_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','153f3c8b-6ccb-4db0-b89d-02db61f61e81')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','153f3c8b-6ccb-4db0-b89d-02db61f61e81')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.soundness_na2so4 - record.soundness_na2so4*mu_value
            upper = record.soundness_na2so4 + record.soundness_na2so4*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.soundness_na2so4_nabl = 'pass'
                break
            else:
                record.soundness_na2so4_nabl = 'fail'


    # Soundness MgSO4
    soundness_mgso4_name = fields.Char("Name",default="Soundness MgSO4")
    soundness_mgso4_visible = fields.Boolean("Soundness MgSO4 Visible",compute="_compute_visible")

    soundness_mgso4_child_lines = fields.One2many('mechanical.soundness.mgso4.line','parent_id',string="Parameter",default=lambda self: self._default_soundness_mgso4_child_lines())
    total_mgso4 = fields.Integer(string="Total",compute="_compute_total_mgso4")
    soundness_mgso4 = fields.Float(string="Soundness",compute="_compute_soundness_mgso4")


    total_grading1 = fields.Float(string="Total Grading of Original sample in %", compute="_compute_total_grading1")

    @api.depends('soundness_mgso4_child_lines.grading_original_sample')
    def _compute_total_grading1(self):
        for record in self:
            total_grading1 = sum(line.grading_original_sample for line in record.soundness_mgso4_child_lines)
            record.total_grading1 = total_grading1

    total_weight_before_test1 = fields.Float(string="Total Weight of test fraction before test in gm.", compute="_compute_total_weight_before_test1")

    @api.depends('soundness_mgso4_child_lines.weight_before_test')
    def _compute_total_weight_before_test1(self):
        for record in self:
            total_weight_before_test1 = sum(line.weight_before_test for line in record.soundness_mgso4_child_lines)
            record.total_weight_before_test1 = total_weight_before_test1


    total_weight_before1 = fields.Float(string="Total Weight of test fraction before test in gm", compute="_compute_total_weight1")

    @api.depends('soundness_mgso4_child_lines.weight_before_test')
    def _compute_total_weight1(self):
        for record in self:
            total_weight_before1 = sum(line.weight_before_test for line in record.soundness_mgso4_child_lines)
            record.total_weight_before1 = total_weight_before1

    total_weight_after1 = fields.Float(string="Total Weight of test feaction Passing Finer Sieve After ", compute="_compute_total_weight_after1")

    @api.depends('soundness_mgso4_child_lines.weight_after_test')
    def _compute_total_weight_after1(self):
        for record in self:
            total_weight_after1 = sum(line.weight_after_test for line in record.soundness_mgso4_child_lines)
            record.total_weight_after1 = total_weight_after1

    total_commulative1 = fields.Float(string="Total Commulative percentage Loss", compute="_compute_total_cumulative1")

    @api.depends('soundness_mgso4_child_lines.cumulative_loss_percent')
    def _compute_total_cumulative1(self):
        for record in self:
            total_commulative1 = sum(line.cumulative_loss_percent for line in record.soundness_mgso4_child_lines)
            record.total_commulative1 = total_commulative1
    
    

    @api.depends('soundness_mgso4_child_lines.weight_before_test')
    def _compute_total_mgso4(self):
        for record in self:
            record.total_mgso4 = sum(record.soundness_mgso4_child_lines.mapped('weight_before_test'))
    

    @api.depends('soundness_mgso4_child_lines.cumulative_loss_percent')
    def _compute_soundness_mgso4(self):
        for record in self:
            record.soundness_mgso4 = round((sum(record.soundness_mgso4_child_lines.mapped('cumulative_loss_percent'))),2)
    

    @api.model
    def _default_soundness_mgso4_child_lines(self):
        default_lines = [
            (0, 0, {'sieve_size_passing': '63 mm', 'sieve_size_retained': '40 mm'}),
            (0, 0, {'sieve_size_passing': '40 mm', 'sieve_size_retained': '20 mm'}),
            (0, 0, {'sieve_size_passing': '20 mm', 'sieve_size_retained': '10 mm'}),
            (0, 0, {'sieve_size_passing': '10 mm', 'sieve_size_retained': '4.75 mm'})
           
        ]
        return default_lines

    soundness_mgso4_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_soundness_mgso4_conformity", store=True)


    @api.depends('soundness_mgso4','eln_ref','grade')
    def _compute_soundness_mgso4_conformity(self):
        
        for record in self:
            record.soundness_mgso4_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','89650e58-11a6-42af-8eb7-187467443a79')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','89650e58-11a6-42af-8eb7-187467443a79')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.soundness_mgso4 - record.soundness_mgso4*mu_value
                    upper = record.soundness_mgso4 + record.soundness_mgso4*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.soundness_mgso4_conformity = 'pass'
                        break
                    else:
                        record.soundness_mgso4_conformity = 'fail'

    soundness_mgso4_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_soundness_mgso4_nabl", store=True)

    @api.depends('soundness_mgso4','eln_ref','grade')
    def _compute_soundness_mgso4_nabl(self):
        
        for record in self:
            record.soundness_mgso4_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','89650e58-11a6-42af-8eb7-187467443a79')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','89650e58-11a6-42af-8eb7-187467443a79')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.soundness_mgso4 - record.soundness_mgso4*mu_value
                    upper = record.soundness_mgso4 + record.soundness_mgso4*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.soundness_mgso4_nabl = 'pass'
                        break
                    else:
                        record.soundness_mgso4_nabl = 'fail'
    


    # #Elongation Index
    # elongation_name = fields.Char("Name",default="Elongation Index")
    # elongation_visible = fields.Boolean("Elongation Visible",compute="_compute_visible")

    # parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    # wt_retained_total_elongation = fields.Float(string="Wt Retained Total",compute="_compute_wt_retained_total_elongation")
    # elongated_retain_total = fields.Float(string="Elongated Retained Total",compute="_compute_elongated_retain")
    # flaky_passing_total = fields.Float(string="Flaky Passing Total",compute="_compute_flaky_passing")
    # aggregate_elongation = fields.Float(string="Aggregate Elongation Value in %",compute="_compute_aggregate_elongation")
    # aggregate_flakiness = fields.Float(string="Aggregate Flakiness Value in %",compute="_compute_aggregate_flakiness")
    # # combine_elongation_flakiness = fields.Float(string="Combine Elongation & Flakiness Value in %",compute="_compute_combine_elongation_flakiness")


    # @api.depends('elongation_child_lines.wt_retained')
    # def _compute_wt_retained_total_elongation(self):
    #     for record in self:
    #         record.wt_retained_total_elongation = sum(record.elongation_child_lines.mapped('wt_retained'))

    # @api.depends('elongation_child_lines.elongated_retain')
    # def _compute_elongated_retain(self):
    #     for record in self:
    #         record.elongated_retain_total = sum(record.elongation_child_lines.mapped('elongated_retain'))

    # # @api.depends('elongation_child_lines.flaky_passing')
    # # def _compute_flaky_passing(self):
    # #     for record in self:
    # #         record.flaky_passing_total = sum(record.elongation_child_lines.mapped('flaky_passing'))

    # @api.depends('wt_retained_total_elongation','elongated_retain_total')
    # def _compute_aggregate_elongation(self):
    #     for record in self:
    #         if record.elongated_retain_total != 0:
    #             record.aggregate_elongation = round((record.elongated_retain_total / record.wt_retained_total_elongation * 100),1)
    #         else:
    #             record.aggregate_elongation = 0.0

    # @api.model
    # def default_elongation_sizes(self):
    #     default_lines = [
    #         (0, 0, {'sieve_size': '63 mm'}),
    #         (0, 0, {'sieve_size': '50 mm'}),
    #         (0, 0, {'sieve_size': '40 mm'}),
    #         (0, 0, {'sieve_size': '31.5 mm'}),
    #         (0, 0, {'sieve_size': '25 mm'}),
    #         (0, 0, {'sieve_size': '20 mm'}),
    #         (0, 0, {'sieve_size': '16 mm'}),
    #         (0, 0, {'sieve_size': '12.5 mm'}),
    #         (0, 0, {'sieve_size': '10 mm'}),
    #         (0, 0, {'sieve_size': '6.3 mm'}),
    #         (0, 0, {'sieve_size': '4.75 mm'}),
    #         (0, 0, {'sieve_size': '2.36 mm'}),
    #         (0, 0, {'sieve_size': '1.18 mm'}),
    #         (0, 0, {'sieve_size': 'Pan'}),
            
    #     ]
    #     return default_lines   




    # @api.depends('wt_retained_total','flaky_passing_total')
    # def _compute_aggregate_flakiness(self):
    #     for record in self:
    #         if record.flaky_passing_total != 0:
    #             record.aggregate_flakiness = record.flaky_passing_total / record.wt_retained_total * 100
    #         else:
    #             record.aggregate_flakiness = 0.0

    # @api.depends('aggregate_elongation','aggregate_flakiness')
    # def _compute_combine_elongation_flakiness(self):
    #     for record in self:
    #         if record.aggregate_flakiness != 0:
    #             record.combine_elongation_flakiness = record.aggregate_elongation + record.aggregate_flakiness
    #         else:
    #             record.combine_elongation_flakiness = 0.0


    # # Flakiness Index 
    # flakiness_name = fields.Char("Name",default="Flakiness Index")
    # flakiness_visible = fields.Boolean("Flakiness Visible",compute="_compute_visible")

    # parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    # wt_retained_total_flakiness = fields.Float(string="Wt Retained Total",compute="_compute_wt_retained_total_flakiness")
    # flaky_passing_total = fields.Float(string="Flaky Passing Total",compute="_compute_flaky_passing")
    # aggregate_flakiness = fields.Float(string="Aggregate Flakiness Value in %",compute="_compute_aggregate_flakiness")
    # combine_elongation_flakiness = fields.Float(string="Combine Elongation & Flakiness Value in %",compute="_compute_combine_elongation_flakiness")
    # # elongated_retain_total = fields.Float(string="Elongated Retained Total",compute="_compute_elongated_retain")
    # # aggregate_elongation = fields.Float(string="aggregate Elongation Value in %",compute="_compute_aggregate_elongation")

    # @api.depends('flakiness_child_lines.wt_retained')
    # def _compute_wt_retained_total_flakiness(self):
    #     for record in self:
    #         record.wt_retained_total_flakiness = sum(record.flakiness_child_lines.mapped('wt_retained'))

    # @api.depends('flakiness_child_lines.flaky_passing')
    # def _compute_flaky_passing(self):
    #     for record in self:
    #         record.flaky_passing_total = sum(record.flakiness_child_lines.mapped('flaky_passing'))


    # @api.depends('wt_retained_total_flakiness','flaky_passing_total')
    # def _compute_aggregate_flakiness(self):
    #     for record in self:
    #         if record.flaky_passing_total != 0:
    #             record.aggregate_flakiness = round((record.flaky_passing_total / record.wt_retained_total_flakiness * 100),1)
    #         else:
    #             record.aggregate_flakiness = 0.0

    # @api.depends('aggregate_elongation','aggregate_flakiness')
    # def _compute_combine_elongation_flakiness(self):
    #     for record in self:
    #         if record.aggregate_flakiness != 0:
    #             record.combine_elongation_flakiness = record.aggregate_elongation + record.aggregate_flakiness
    #         else:
    #             record.combine_elongation_flakiness = 0.0

     # Flakiness and Elongation 
    elongation_name = fields.Char(default="Elongation and Flakiness Index")
    elongation_visible = fields.Boolean(compute="_compute_visible")

    flakiness_name = fields.Char(default=" Flakiness Index")
    flakiness_visible = fields.Boolean(compute="_compute_visible")

    elongation_table = fields.One2many('mechanical.elongation.flakiness.line','parent_id',string="Elongation Flakiness Index",default=lambda self: self.default_flakiness_sizes())

    total_wt_retained_fl_el = fields.Float('Total',compute="_compute_total_el_fl")
    total_elongated_retained = fields.Float('Total Elongation',compute="_compute_total_elongation")
    total_flakiness_retained = fields.Float('Total Flakiness',compute="_compute_total_flakiness")

    aggregate_elongation = fields.Float('Aggregate Elongation Value in %',compute="_compute_aggregate_elongation")
    aggregate_flakiness = fields.Float('Aggregate Flakiness Value in %' ,compute="_compute_aggregate_flakiness")
    aggregate_combine = fields.Float('Aggregate Elongation & Flakiness Value in %',compute="_compute_aggregate_combine")


    aggregate_combine_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_aggregate_combine_conformity", store=True)

    @api.depends('aggregate_combine','eln_ref','grade')
    def _compute_aggregate_combine_conformity(self):
        
        for record in self:
            record.aggregate_combine_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9effe915-e5a3-45a7-aaeb-10caababd667')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9effe915-e5a3-45a7-aaeb-10caababd667')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.aggregate_combine - record.aggregate_combine*mu_value
                    upper = record.aggregate_combine + record.aggregate_combine*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.aggregate_combine_conformity = 'pass'
                        break
                    else:
                        record.aggregate_combine_conformity = 'fail'

    aggregate_combine_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_aggregate_combine_nabl", store=True)

    @api.depends('aggregate_combine','eln_ref','grade')
    def _compute_aggregate_combine_nabl(self):
        
        for record in self:
            record.aggregate_combine_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9effe915-e5a3-45a7-aaeb-10caababd667')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9effe915-e5a3-45a7-aaeb-10caababd667')]).parameter_table
            # for material in materials:
                # if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.aggregate_combine - record.aggregate_combine*mu_value
            upper = record.aggregate_combine + record.aggregate_combine*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.aggregate_combine_nabl = 'pass'
                break
            else:
                record.aggregate_combine_nabl = 'fail'


    @api.depends('elongation_table.wt_retained')
    def _compute_total_el_fl(self):
        for record in self:
            record.total_wt_retained_fl_el = sum(record.elongation_table.mapped('wt_retained'))

    @api.depends('elongation_table.elongated_retained')
    def _compute_total_elongation(self):
        for record in self:
            record.total_elongated_retained = sum(record.elongation_table.mapped('elongated_retained'))

    @api.depends('elongation_table.flakiness_retained')
    def _compute_total_flakiness(self):
        for record in self:
            record.total_flakiness_retained = sum(record.elongation_table.mapped('flakiness_retained'))

    @api.depends('total_wt_retained_fl_el','total_elongated_retained')
    def _compute_aggregate_elongation(self):
        for record in self:
            if record.total_elongated_retained != 0:
                record.aggregate_elongation = record.total_elongated_retained/record.total_wt_retained_fl_el * 100
            else:
                record.aggregate_elongation = 0

    @api.depends('total_wt_retained_fl_el','total_flakiness_retained')
    def _compute_aggregate_flakiness(self):
        for record in self:
            if record.total_flakiness_retained != 0:
                record.aggregate_flakiness = record.total_flakiness_retained/record.total_wt_retained_fl_el*100
            else:
                record.aggregate_flakiness = 0
    

    @api.depends('total_wt_retained_fl_el','total_flakiness_retained')
    def _compute_aggregate_combine(self):
        for record in self:
            record.aggregate_combine = round(record.aggregate_elongation+record.aggregate_flakiness,2)
            



   
    @api.model
    def default_flakiness_sizes(self):
        default_lines = [
            (0, 0, {'sieve_size': '40 - 31.5'}),
            (0, 0, {'sieve_size': '31.5 - 25'}),
            (0, 0, {'sieve_size': '25 - 20'}),
            (0, 0, {'sieve_size': '20 - 16'}),
            (0, 0, {'sieve_size': '16 - 12.5'}),
            (0, 0, {'sieve_size': '12.5 - 10'}),
            (0, 0, {'sieve_size': '10 - 6.3'}),
            (0, 0, {'sieve_size': 'Pan'}),
            
        ]
        return default_lines   



    # Deleterious Content

    name_finer75 = fields.Char("Name",default="Material Finer than 75 Micron")
    finer75_visible = fields.Boolean("Finer 75 Visible",compute="_compute_visible")

    wt_sample_finer75 = fields.Float("Weight of Sample in gms")
    wt_dry_sample_finer75 = fields.Float("Weight of dry sample after retained in 75 microns")
    material_finer75 = fields.Float("Material finer than 75 micron in %",compute="_compute_finer75")

    material_finer75_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_material_finer75_conformity", store=True)

    @api.depends('material_finer75','eln_ref','grade')
    def _compute_material_finer75_conformity(self):
        
        for record in self:
            record.material_finer75_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','988f5bf6-c865-453c-9cd6-993a5a59ad95')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','988f5bf6-c865-453c-9cd6-993a5a59ad95')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.material_finer75 - record.material_finer75*mu_value
                    upper = record.material_finer75 + record.material_finer75*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.material_finer75_conformity = 'pass'
                        break
                    else:
                        record.material_finer75_conformity = 'fail'

    material_finer75_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_material_finer75_nabl", store=True)

    @api.depends('material_finer75','eln_ref','grade')
    def _compute_material_finer75_nabl(self):
        
        for record in self:
            record.material_finer75_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','988f5bf6-c865-453c-9cd6-993a5a59ad95')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','988f5bf6-c865-453c-9cd6-993a5a59ad95')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.material_finer75 - record.material_finer75*mu_value
            upper = record.material_finer75 + record.material_finer75*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.material_finer75_nabl = 'pass'
                break
            else:
                record.material_finer75_nabl = 'fail'

    @api.depends('wt_sample_finer75','wt_dry_sample_finer75')
    def _compute_finer75(self):
        for record in self:
            if record.wt_sample_finer75 != 0:
                record.material_finer75 = ((record.wt_sample_finer75 - record.wt_dry_sample_finer75)/record.wt_sample_finer75 * 100)
            else:
                record.material_finer75 = 0

    
    name_clay_lumps = fields.Char("Name",default="Determination of Clay Lumps")
    clay_lump_visible = fields.Boolean("Clay Lump Visible",compute="_compute_visible")

    wt_sample_clay_lumps = fields.Float("Weight of Sample in gms")
    wt_dry_sample_clay_lumps = fields.Float("Weight of dry sample after retained in 75 microns")
    clay_lumps_percent = fields.Float("Clay Lumps in %",compute="_compute_clay_lumps")

    clay_lumps_percent_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_clay_lumps_percent_conformity", store=True)

    @api.depends('clay_lumps_percent','eln_ref','grade')
    def _compute_clay_lumps_percent_conformity(self):
        
        for record in self:
            record.clay_lumps_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d7e389bc-21ad-41eb-a602-f448f996eb2f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d7e389bc-21ad-41eb-a602-f448f996eb2f')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d7e389bc-21ad-41eb-a602-f448f996eb2f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d7e389bc-21ad-41eb-a602-f448f996eb2f')]).parameter_table
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

    @api.depends('wt_sample_clay_lumps','wt_dry_sample_clay_lumps')
    def _compute_clay_lumps(self):
        for record in self:
            if record.wt_sample_clay_lumps != 0:
                record.clay_lumps_percent = ((record.wt_sample_clay_lumps - record.wt_dry_sample_clay_lumps)/record.wt_sample_clay_lumps * 100)
            else:
                record.clay_lumps_percent = 0


    name_light_weight = fields.Char("Name",default="Determination of Light Weight Particles")
    light_weight_visible = fields.Boolean("Light Weight Visible",compute="_compute_visible")

    wt_sample_light_weight = fields.Float("Weight of Sample in gms")
    wt_dry_sample_light_weight = fields.Float("Weight of dry sample after retained in 75 microns")
    light_weight_percent = fields.Float("Light Weight Particle in %",compute="_compute_light_weight")

    light_weight_percent_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_light_weight_percent_conformity", store=True)

    @api.depends('light_weight_percent','eln_ref','grade')
    def _compute_light_weight_percent_conformity(self):
        
        for record in self:
            record.light_weight_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e7cc6b68-2550-4e1e-a28e-8526295e733f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e7cc6b68-2550-4e1e-a28e-8526295e733f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.light_weight_percent - record.light_weight_percent*mu_value
                    upper = record.light_weight_percent + record.light_weight_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.light_weight_percent_conformity = 'pass'
                        break
                    else:
                        record.light_weight_percent_conformity = 'fail'

    light_weight_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_light_weight_percent_nabl", store=True)

    @api.depends('light_weight_percent','eln_ref','grade')
    def _compute_light_weight_percent_nabl(self):
        
        for record in self:
            record.light_weight_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e7cc6b68-2550-4e1e-a28e-8526295e733f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e7cc6b68-2550-4e1e-a28e-8526295e733f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.light_weight_percent - record.light_weight_percent*mu_value
                    upper = record.light_weight_percent + record.light_weight_percent*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.light_weight_percent_nabl = 'pass'
                        break
                    else:
                        record.light_weight_percent_nabl = 'fail'

    @api.depends('wt_sample_light_weight','wt_dry_sample_light_weight')
    def _compute_light_weight(self):
        for record in self:
            if record.wt_sample_light_weight != 0:
                record.light_weight_percent = record.wt_dry_sample_light_weight/record.wt_sample_light_weight*100
            else:
                record.light_weight_percent = 0




    # Compacted  Or Rodded Density


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
            ('fail', 'Fail')], string="Conformity", compute="_compute_compacted_density_conformity", store=True)

    @api.depends('compacted_density','eln_ref','grade')
    def _compute_compacted_density_conformity(self):
        
        for record in self:
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
            ('fail', 'Fail')], string="Conformity", compute="_compute_loose_density_conformity", store=True)

    @api.depends('loose_density','eln_ref','grade')
    def _compute_loose_density_conformity(self):
        
        for record in self:
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


    @api.depends('specific_gravity_voids', 'compacted_density')
    def _compute_voids_compacted_density(self):
        for rec in self:
            if rec.specific_gravity_voids !=0:
              rec.voids_compacted_density = round(((rec.specific_gravity_voids - rec.compacted_density)/rec.specific_gravity_voids * 100),2)
            else:
             rec.voids_compacted_density = 0.0
             

    @api.depends('specific_gravity_voids', 'loose_density')
    def _compute_voids_loose_density(self):
        for rec in self:
            if rec.specific_gravity_voids !=0:
              rec.voids_loose_density = round(((rec.specific_gravity_voids - rec.loose_density)/rec.specific_gravity_voids * 100),2)
            else:
             rec.voids_loose_density = 0.0  


    voids_compacted_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Void In Compacted Density Conformity", compute="_compute_voids_compacted_density_conformity", store=True)

    @api.depends('voids_compacted_density','eln_ref','grade')
    def _compute_voids_compacted_density_conformity(self):
        
        for record in self:
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
            ('fail', 'Fail')], string="Void In Loose Density Conformity", compute="_compute_voids_loose_density_conformity", store=True)

    @api.depends('voids_loose_density','eln_ref','grade')
    def _compute_voids_loose_density_conformity(self):
        
        for record in self:
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













    

    # Sieve Analysis 
    weight_of_sample = fields.Float(string="Weight of Sample in gms")
    sieve_analysis_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

    sieve_analysis_child_lines = fields.One2many('mechanical.coarse.aggregate.sieve.analysis.line','parent_id',string="Parameter")
    total_sieve_analysis = fields.Float(string="Total",compute="_compute_total_sieve")


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
                    63: ['80 mm', '63 mm', '40 mm', '20 mm', '10 mm', 'pan'],
                    40: ['63 mm', '40 mm', '20 mm', '10 mm', 'pan'],
                    20: ['40 mm', '20 mm', '10 mm', '4.75 mm', 'pan'],
                    16: ['20 mm', '16 mm', '10 mm', '4.75 mm', 'pan'],
                    12: ['16 mm', '12.5 mm', '10 mm', '4.75 mm', 'pan'],
                    10: ['12.5 mm', '10 mm', '4.75 mm', '2.36 mm', 'pan'],
                }
                specific_limits_mapping = {
                    63: ['100', '85 - 100', '0 - 30', '0 - 5', '0 - 5', '0'],
                    40: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                    20: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                    16: ['100', '85 - 100', '0 - 30', '0 - 5', '0'],
                    12: ['100', '85 - 100', '0 - 45', '0 - 10', '0'],
                    10: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                }
            elif grade_str == 'graded aggregate':
                sieve_mapping = {
                    40: ['80 mm', '40 mm', '20 mm', '10 mm','4.75 mm','pan'],
                    20: ['40 mm', '20 mm', '10 mm', '4.75 mm','pan'],
                    16: ['20 mm', '16 mm', '10 mm', '4.75 mm', 'pan'],
                    12: ['16 mm', '12.5 mm', '10 mm', '4.75 mm', 'pan'],
                }
                specific_limits_mapping = {
                    40: ['100', '95 - 100', '30 - 70', '10 - 35','0 - 5', '0'],
                    20: ['100', '95 - 100', '25 - 55', '0 - 10', '0'],
                    16: ['100', '90 - 100', '30 - 70', '0 - 10', '0'],
                    12: ['100', '90 - 100', '40 - 85', '0 - 10', '0'],
                }
            else:
                return res

            # Extract numeric part
            match = re.search(r'\d+', size_str)
            if match:
                number = int(match.group())
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
                63: ['100', '85 - 100', '0 - 30', '0 - 5', '0 - 5', '0'],
                40: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                20: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                16: ['100', '85 - 100', '0 - 30', '0 - 5', '0'],
                12: ['100', '85 - 100', '0 - 45', '0 - 10', '0'],
                10: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
            }
        elif grade_str == 'graded aggregate':
            specific_limits_mapping = {
                40: ['100', '95 - 100', '30 - 70', '10 - 35', '0 - 5', '0'],
                20: ['100', '95 - 100', '25 - 55', '0 - 10', '0'],
                16: ['100', '90 - 100', '30 - 70', '0 - 10', '0'],
                12: ['100', '90 - 100', '40 - 85', '0 - 10', '0'],
            }
        else:
            return

        match = re.search(r'\d+', size_str)
        if match:
            number = int(match.group())
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
                    if line.percent_retained == 0:
                        line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2),
                                    'passing_percent': 100 ,})
                    else:
                        line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2),
                                    'passing_percent': round(100 -line.percent_retained - line.percent_retained,2),})
                else:
                    previous_line_record = self.env['mechanical.coarse.aggregate.sieve.analysis.line'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
                    line.write({'cumulative_retained': previous_line_record + line.percent_retained,
                                'passing_percent': round(100-(previous_line_record + line.percent_retained),2),})
                    
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



    graph_image_slive = fields.Binary("Sieve Graph", compute="_compute_graph_image_slive", store=True)

    @api.depends('sieve_analysis_child_lines.cumulative_retained', 'sieve_analysis_child_lines.passing_percent')
    def _compute_graph_image_slive(self):
        for record in self:
            if record.sieve_analysis_child_lines:
                record.graph_image_slive = record.generate_line_chart_slive()
            else:
                record.graph_image_slive = False

    





    def generate_line_chart_slive(self):
   
        x_value = []
        y_value = []
        x_labels = []

        for line in self.sieve_analysis_child_lines:
            if line.sieve_size and line.passing_percent is not None:
                sieve_str = str(line.sieve_size).strip().lower()
                try:
                    if 'mm' in sieve_str:
                        sieve_val = float(sieve_str.replace('mm', '').strip())
                        label = f"{int(sieve_val)} mm"
                    elif 'µ' in sieve_str or 'micron' in sieve_str:
                        sieve_val = float(sieve_str.replace('µ', '').replace('micron', '').strip()) / 1000
                        label = f"{int(float(line.sieve_size.replace('µ', '').replace('micron', '').strip()))} µm"
                    else:
                        sieve_val = float(sieve_str)
                        label = f"{sieve_val} mm"

                    x_value.append(sieve_val)
                    y_value.append(float(line.passing_percent))
                    x_labels.append(label)
                except ValueError:
                    continue

        if not x_value or not y_value:
            return False

        # Sort ascending
        sorted_data = sorted(zip(x_value, y_value, x_labels))
        x_value, y_value, x_labels = zip(*sorted_data)

        plt.figure(figsize=(12, 5))
        plt.xscale('log')

        # Main curve
        plt.plot(x_value, y_value, color='blue', linestyle='-', linewidth=2)
        plt.scatter(x_value, y_value, color='red', edgecolors='black', s=60, zorder=5)

        plt.xlabel('Sieve Size', fontsize=12)
        plt.ylabel('Passing %', fontsize=12)
        plt.title('Grain Size Analysis', fontsize=14)

        ax = plt.gca()
        plt.xticks(ticks=x_value, labels=x_labels, rotation=45, ha='right')
        ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(1.0, 10.0)*0.1, numticks=200))
        ax.yaxis.set_minor_locator(MultipleLocator(2))
        plt.grid(True, which='both', axis='both', linestyle='--', linewidth=0.3, color='gray', alpha=0.8)

        plt.xlim(left=min(x_value)/1.5, right=max(x_value)*1.5)
        plt.ylim(bottom=0, top=120)
        plt.yticks([0, 20, 40, 60, 80, 100, 120])

        # --- D-points: D10, D30, D60 ---
        d_points = [
            (getattr(self, 'd10', None), 10, 'black'),
            (getattr(self, 'd30', None), 30, 'yellow'),
            (getattr(self, 'd60', None), 60, 'orange')
        ]

        for dx, dy, color in d_points:
            if dx:
                # Solid point
                plt.scatter(dx, dy, color=color, s=80, zorder=10)
                # Draw X and Y guide lines only to intersection
                plt.plot([dx, dx], [0, dy], color=color, linestyle='-', linewidth=1.2)
                plt.plot([0, dx], [dy, dy], color=color, linestyle='-', linewidth=1.2)

        # Save figure
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)

        return base64.b64encode(buffer.read())

    

    wt_of_compact1 = fields.Float(string="Wt of compacted aggregrage +measuring cylinder(C) (Kg)")
    compact_bulk1 = fields.Float(string="Compacted bulk density= (C-A)/V)) (Kg)",compute="_compute_compact_bulk1",digits=(12,3))

    @api.depends('wt_of_compact1', 'weight_empty_bucket_loose', 'volume_of_bucket_loose')
    def _compute_compact_bulk1(self):
        for rec in self:
            if rec.volume_of_bucket_loose and rec.wt_of_compact1 and rec.weight_empty_bucket_loose:
                rec.compact_bulk1 = (rec.wt_of_compact1 - rec.weight_empty_bucket_loose) / rec.volume_of_bucket_loose
            else:
                rec.compact_bulk1 = 0.0

    avg_compacted = fields.Float(string="Avg Compacted Density",compute="_compute_avg_compacted",digits=(12,3))

    # Average
    @api.depends('compact_bulk', 'compact_bulk1')
    def _compute_avg_compacted(self):
        for rec in self:
            if rec.compact_bulk and rec.compact_bulk1:
                rec.avg_compacted = (rec.compact_bulk + rec.compact_bulk1) / 2
            else:
                rec.avg_compacted = 0.0


    specific_gravity2  = fields.Float(string="Specific Gravity")
    specific_gravity3  = fields.Float(string="Specific Gravity")


    

    @api.depends('specific_gravity2','compact_bulk')
    def _compute_void_compacted_density1(self):
        for record in self:
            if record.specific_gravity2:
            # if record.void_compacted_density1:
              record.void_compacted_density1 = ((record.specific_gravity2-record.compact_bulk) /record.specific_gravity2)*100
            else:
              record.void_compacted_density1 = 0.0
    
    @api.depends('specific_gravity3','compact_bulk1')
    def _compute_void_compacted_density2(self):
        for record in self:
            if record.specific_gravity3:
            # if record.void_compacted_density2:
              record.void_compacted_density2 = ((record.specific_gravity3-record.compact_bulk1) /record.specific_gravity3)*100
            else:
              record.void_compacted_density2 = 0.0

            

    # Average

    avg_void_compacted_density=fields.Float(string="Avg % Voids - Compacted Density",compute="_compute_avg_void_compacted_density",digits=(12,3))

    @api.depends('void_compacted_density1','void_compacted_density2')
    def _compute_avg_void_compacted_density(self):
        for rec in self:
            if rec.void_compacted_density1 and rec.void_compacted_density2 :
                rec.avg_void_compacted_density = (rec.void_compacted_density1 + rec.void_compacted_density2) / 2
            else:
                rec.avg_void_compacted_density= 0.0

    avg_void_compacted_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Compacted Bulk NABL", compute="_compute_avg_void_compacted_density_nabl", store=True)
    
    avg_void_compacted_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Compacted Bulk Conformity", compute="_compute_avg_void_compacted_density_conformity", store=True)
    
    @api.depends('avg_void_compacted_density','eln_ref','grade')
    def _compute_avg_void_compacted_density_conformity(self):
        
        for record in self:
            record.avg_void_compacted_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_void_compacted_density - record.avg_void_compacted_density*mu_value
                    upper = record.avg_void_compacted_density + record.avg_void_compacted_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_void_compacted_density_conformity = 'pass'
                        break
                    else:
                        record.avg_void_compacted_density_conformity = 'fail'

    @api.depends('avg_void_compacted_density','eln_ref','grade')
    def _compute_avg_void_compacted_density_nabl(self):
        
        for record in self:
            record.avg_void_compacted_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')]).parameter_table
            # for material in materials:
                # if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_void_compacted_density - record.avg_void_compacted_density*mu_value
            upper = record.avg_void_compacted_density + record.avg_void_compacted_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_void_compacted_density_nabl = 'pass'
                break
            else:
                record.avg_void_compacted_density_nabl = 'fail'




 # % Voids - Loose density
    void_loose_density_name = fields.Char("Name", default="% Voids - Loose density")
    void_loose_density_visible = fields.Boolean("% Voids - Loose density Visible",compute="_compute_visible")


    wt_of_loose = fields.Float(string="Wt of Loose aggregrage +measuring cylinder(C) (Kg)")
    loose_bulk = fields.Float(string="Loose bulk density= (C-A)/V)) (Kg)",compute="_compute_loose_bulk",digits=(12,3))
    wt_of_loose1 = fields.Float(string="Wt of Loose aggregrage +measuring cylinder(C) (Kg)")
    loose_bulk1 = fields.Float(string="Loose bulk density= (C-A)/V)) (Kg)",compute="_compute_loose_bulk1",digits=(12,3))

    @api.depends('wt_of_loose', 'weight_empty_bucket_loose', 'volume_of_bucket_loose')
    def _compute_loose_bulk(self):
        for rec in self:
            if rec.volume_of_bucket_loose and rec.wt_of_loose and rec.weight_empty_bucket_loose:
                rec.loose_bulk = (rec.wt_of_loose - rec.weight_empty_bucket_loose) / rec.volume_of_bucket_loose
            else:
                rec.loose_bulk = 0.0


    @api.depends('wt_of_loose1', 'weight_empty_bucket_loose', 'volume_of_bucket_loose')
    def _compute_loose_bulk1(self):
        for rec in self:
            if rec.volume_of_bucket_loose and rec.wt_of_loose1 and rec.weight_empty_bucket_loose:
                rec.loose_bulk1 = (rec.wt_of_loose1 - rec.weight_empty_bucket_loose) / rec.volume_of_bucket_loose
            else:
                rec.loose_bulk1 = 0.0


    # # Average
    # @api.depends('wt_of_loose', 'wt_of_loose1')
    # def _compute_avg_loose(self):
    #     for rec in self:
    #         if rec.wt_of_loose and rec.wt_of_loose1:
    #             rec.avg_loose = (rec.wt_of_loose + rec.wt_of_loose1) / 2
    #         else:
    #             rec.avg_loose = 0.0


    void_loose_density1=fields.Float(string="% Voids",compute="_compute_void_loose_density1")

    void_loose_density2=fields.Float(string="% Voids",compute="_compute_void_loose_density2")

    specific_gravity4  = fields.Float(string="Specific Gravity")
    specific_gravity5  = fields.Float(string="Specific Gravity")

    @api.depends('specific_gravity4','loose_bulk')
    def _compute_void_loose_density1(self):
        for record in self:
            if record.specific_gravity4:
            # if record.void_compacted_density1:
              record.void_loose_density1 = ((record.specific_gravity4-record.loose_bulk) /record.specific_gravity4)*100
            else:
              record.void_loose_density1 = 0.0
    
    @api.depends('specific_gravity5','loose_bulk1')
    def _compute_void_loose_density2(self):
        for record in self:
            if record.specific_gravity5:
            # if record.void_compacted_density2:
              record.void_loose_density2 = ((record.specific_gravity5-record.loose_bulk1) /record.specific_gravity5)*100
            else:
              record.void_loose_density2 = 0.0

            

    # Average

    avg_void_loose_density=fields.Float(string="Avg % Voids - Loose Density",compute="_compute_avg_void_loose_density",digits=(12,3))

    @api.depends('void_loose_density1','void_loose_density2')
    def _compute_avg_void_loose_density(self):
        for rec in self:
            if rec.void_loose_density1 and rec.void_loose_density2 :
                rec.avg_void_loose_density = (rec.void_loose_density1 + rec.void_loose_density2) / 2
            else:
                rec.avg_void_loose_density= 0.0

    avg_void_loose_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Loose Bulk NABL", compute="_compute_avg_void_loose_density_nabl", store=True)
    
    avg_void_loose_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Loose Bulk Conformity", compute="_compute_avg_void_loose_density_conformity", store=True)
    
    @api.depends('avg_void_loose_density','eln_ref','grade')
    def _compute_avg_void_loose_density_conformity(self):
        
        for record in self:
            record.avg_void_loose_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_void_loose_density - record.avg_void_loose_density*mu_value
                    upper = record.avg_void_loose_density + record.avg_void_loose_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_void_loose_density_conformity = 'pass'
                        break
                    else:
                        record.avg_void_loose_density_conformity = 'fail'

    @api.depends('avg_void_loose_density','eln_ref','grade')
    def _compute_avg_void_loose_density_nabl(self):
        
        for record in self:
            record.avg_void_loose_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')]).parameter_table
            # for material in materials:
                # if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_void_loose_density - record.avg_void_loose_density*mu_value
            upper = record.avg_void_loose_density + record.avg_void_loose_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_void_loose_density_nabl = 'pass'
                break
            else:
                record.avg_void_loose_density_nabl = 'fail'

    
    
    




    @api.depends('eln_ref')
    def _compute_visible(self):
        for record in self:
            record.crushing_visible = False
            record.abrasion_visible = False
            record.specific_gravity_visible = False
            record.water_absorption_visible = False
            record.impact_visible = False
            record.fine10_visible = False
            record.soundness_na2so4_visible = False
            record.soundness_mgso4_visible = False
            record.elongation_visible = False
            record.flakiness_visible = False
            record.finer75_visible = False
            record.clay_lump_visible = False
            record.light_weight_visible = False
            record.loose_density_visible = False
            record.sieve_visible = False
            record.compacted_density_visible = False
            record.voids_compacted_density_visible = False
            record.voids_loose_density_visible = False




            for sample in record.sample_parameters:
                if sample.internal_id == 'ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71':
                    record.crushing_visible = True
                if sample.internal_id == '37f2161e-5cc0-413f-b76c-10478c65baf9':
                    record.abrasion_visible = True
                if sample.internal_id == '3114db41-cfa7-49ad-9324-fcdbc9661038':
                    record.specific_gravity_visible = True
                if sample.internal_id == '22ee804f-41a3-4fd1-a301-a8d9180fba10':
                    record.water_absorption_visible = True
                if sample.internal_id == '2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2':
                    record.impact_visible = True
                if sample.internal_id == '5f506c08-4369-491d-93a6-030514c29661':
                    record.fine10_visible = True
                if sample.internal_id == '153f3c8b-6ccb-4db0-b89d-02db61f61e81':
                    record.soundness_na2so4_visible = True
                if sample.internal_id == '89650e58-11a6-42af-8eb7-187467443a79':
                    record.soundness_mgso4_visible = True
              

                if sample.internal_id == '9effe915-e5a3-45a7-aaeb-10caababd667':
                    record.elongation_visible = True
                    # record.flakiness_visible = True

                if sample.internal_id == 'be7a60bc-bb2c-410d-b91a-4f8730a4ac6f':
                    record.flakiness_visible = True
                    # record.elongation_visible = True
                if sample.internal_id == '988f5bf6-c865-453c-9cd6-993a5a59ad95':
                    record.finer75_visible = True
                if sample.internal_id == 'd7e389bc-21ad-41eb-a602-f448f996eb2f':
                    record.clay_lump_visible = True
                if sample.internal_id == 'e7cc6b68-2550-4e1e-a28e-8526295e733f':
                    record.light_weight_visible = True
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





    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:

            # Elongation
            if result.parameter.internal_id == '9effe915-e5a3-45a7-aaeb-10caababd667':
                result.result_char = round(self.aggregate_elongation,2)
                if self.aggregate_combine_conformity == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Flakiness
            if result.parameter.internal_id == 'be7a60bc-bb2c-410d-b91a-4f8730a4ac6f':
                result.result_char = round(self.aggregate_flakiness,2)
                if self.aggregate_combine_conformity == 'pass':
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





    @api.depends('wt_retained', 'parent_id.weight_of_sample')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = (record.wt_retained / self.parent_id.weight_of_sample) * 100
            except ZeroDivisionError:
                record.percent_retained = 0


    @api.depends('cumulative_retained')
    def _compute_cum_retained(self):
        self.cumulative_retained=0
        


    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines, key=lambda r: r.id)
            # index = sorted_lines.index(record)
            # print("Working")


   


# class ElongationIndexLine(models.Model):
#     _name = "mechanical.elongation.index.line"
#     parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")
   
#     sr_no = fields.Integer(string="Sr No", readonly=True, copy=False, default=1)
#     sieve_size = fields.Char(string="I.S Sieve Size")
#     wt_retained = fields.Integer(string="Wt Retained (in gms)")
#     elongated_retain = fields.Float(string="Elongated Retained (in gms)")
#     # flaky_passing = fields.Float(string="Flaky Passing (in gms)")
    

    

#     @api.model
#     def create(self, vals):
#         # Set the serial_no based on the existing records for the same parent
#         if vals.get('parent_id'):
#             existing_records = self.search([('parent_id', '=', vals['parent_id'])])
#             if existing_records:
#                 max_serial_no = max(existing_records.mapped('sr_no'))
#                 vals['sr_no'] = max_serial_no + 1

#         return super(ElongationIndexLine, self).create(vals)

#     def _reorder_serial_numbers(self):
#         # Reorder the serial numbers based on the positions of the records in child_lines
#         records = self.sorted('id')
#         for index, record in enumerate(records):
#             record.sr_no = index + 1

# class FlakinessIndexLine(models.Model):
#     _name = "mechanical.flakiness.index.line"
#     parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")
   
#     sr_no = fields.Integer(string="Sr No", readonly=True, copy=False, default=1)
#     sieve_size = fields.Char(string="I.S Sieve Size")
#     wt_retained = fields.Integer(string="Wt Retained (in gms)")
#     # elongated_retain = fields.Float(string="Elongated Retained (in gms)")
#     flaky_passing = fields.Float(string="Flaky Passing (in gms)")
    

    

   
#     @api.model
#     def create(self, vals):
#         # Set the serial_no based on the existing records for the same parent
#         if vals.get('parent_id'):
#             existing_records = self.search([('parent_id', '=', vals['parent_id'])])
#             if existing_records:
#                 max_serial_no = max(existing_records.mapped('sr_no'))
#                 vals['sr_no'] = max_serial_no + 1

#         return super(FlakinessIndexLine, self).create(vals)

#     def _reorder_serial_numbers(self):
#         # Reorder the serial numbers based on the positions of the records in child_lines
#         records = self.sorted('id')
#         for index, record in enumerate(records):
#             record.sr_no = index + 1

class ElongationFlacnessLine(models.Model):
    _name = "mechanical.elongation.flakiness.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate', string="Parent Id")

    sieve_size = fields.Char(string="IS Sieve Size")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    elongated_retained = fields.Float(string="Elongated Retained in gms")
    flakiness_retained = fields.Float(string="Flakiness Retained in gms")


class SoundnessNa2Line(models.Model):
    _name = "mechanical.soundness.na2so4.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate', string="Parent Id")
    
    sieve_size_passing = fields.Char(string="Sieve Size Passing")
    sieve_size_retained = fields.Char(string="Sieve Size Retained")
    weight_before_test = fields.Float(string="Weight of test fraction before test in gm.")
    weight_after_test = fields.Float(string="Weight of test feaction Passing Finer Sieve After test")
    grading_original_sample = fields.Float(string="Grading of Original sample in %", compute="_compute_grading")
    passing_percent = fields.Float(string="Percentage Passing Finer Sieve After test (Percentage Loss)",compute="_compute_passing_percent")
    cumulative_loss_percent = fields.Float(string="Commulative percentage Loss",compute="_compute_cumulative_na2so4")
    
    @api.depends('parent_id.total_na2so4','weight_before_test')
    def _compute_grading(self):
        for record in self:
            try:
                record.grading_original_sample = (record.weight_before_test/record.parent_id.total_na2so4)*100
            except ZeroDivisionError:
                record.grading_original_sample = 0

    @api.depends('weight_before_test','weight_after_test')
    def _compute_passing_percent(self):
        for record in self:
            try:
                record.passing_percent = (record.weight_after_test / record.weight_before_test)*100
            except:
                record.passing_percent = 0

    @api.depends('weight_after_test', 'parent_id.total_na2so4')
    def _compute_cumulative_na2so4(self):
        for record in self:
            try:
                record.cumulative_loss_percent = (record.weight_after_test / record.parent_id.total_na2so4) * 100
            except:
                record.cumulative_loss_percent = 0



    

class SoundnessMgLine(models.Model):
    _name = "mechanical.soundness.mgso4.line"
    parent_id = fields.Many2one('mechanical.coarse.aggregate', string="Parent Id")
    
    sieve_size_passing = fields.Char(string="Sieve Size Passing")
    sieve_size_retained = fields.Char(string="Sieve Size Retained")
    weight_before_test = fields.Float(string="Weight of test fraction before test in gm.")
    weight_after_test = fields.Float(string="Weight of test feaction Passing Finer Sieve After test")
    grading_original_sample = fields.Float(string="Grading of Original sample in %", compute="_compute_grading")
    passing_percent = fields.Float(string="Percentage Passing Finer Sieve After test (Percentage Loss)",compute="_compute_passing_percent")
    cumulative_loss_percent = fields.Float(string="Commulative percentage Loss",compute="_compute_cumulative_mgso4")
    
    @api.depends('parent_id.total_mgso4','weight_before_test')
    def _compute_grading(self):
        for record in self:
            try:
                record.grading_original_sample = (record.weight_before_test/record.parent_id.total_mgso4)*100
            except ZeroDivisionError:
                record.grading_original_sample = 0

    @api.depends('weight_before_test','weight_after_test')
    def _compute_passing_percent(self):
        for record in self:
            try:
                record.passing_percent = (record.weight_after_test / record.weight_before_test)*100
            except:
                record.passing_percent = 0

    @api.depends('weight_after_test', 'parent_id.total_mgso4')
    def _compute_cumulative_mgso4(self):
        for record in self:
            try:
                record.cumulative_loss_percent = (record.weight_after_test / record.parent_id.total_mgso4) * 100
            except:
                record.cumulative_loss_percent = 0






# class AbrasionValueCoarseAggregateLine(models.Model):
#     _name = "mechanical.abrasion.value.coarse.aggregate.line"
#     parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")
   
#     sr_no = fields.Integer(string="Test", readonly=True, copy=False, default=1)
#     total_weight_sample = fields.Integer(string="Total weight of Sample in gms")
#     weight_passing_sample = fields.Integer(string="Weight of Passing sample in 1.70 mm IS sieve in gms")
#     weight_retain_sample = fields.Integer(string="Weight of Retain sample in 1.70 mm IS sieve in gms",compute="_compute_weight_retain_sample")
#     abrasion_value_percentage = fields.Float(string="Abrasion Value (in %)",compute="_compute_sample_weight")


#     @api.depends('total_weight_sample', 'weight_passing_sample')
#     def _compute_weight_retain_sample(self):
#         for line in self:
#             line.weight_retain_sample = line.total_weight_sample - line.weight_passing_sample


#     @api.depends('total_weight_sample', 'weight_passing_sample')
#     def _compute_sample_weight(self):
#         for line in self:
#             if line.total_weight_sample != 0:
#                 line.abrasion_value_percentage = (line.weight_passing_sample / line.total_weight_sample) * 100
#             else:
#                 line.abrasion_value_percentage = 0.0


    # @api.model
    # def create(self, vals):
    #     # Set the serial_no based on the existing records for the same parent
    #     if vals.get('parent_id'):
    #         existing_records = self.search([('parent_id', '=', vals['parent_id'])])
    #         if existing_records:
    #             max_serial_no = max(existing_records.mapped('sr_no'))
    #             vals['sr_no'] = max_serial_no + 1

    #     return super(AbrasionValueCoarseAggregateLine, self).create(vals)

    # def _reorder_serial_numbers(self):
    #     # Reorder the serial numbers based on the positions of the records in child_lines
    #     records = self.sorted('id')
    #     for index, record in enumerate(records):
    #         record.sr_no = index + 1

