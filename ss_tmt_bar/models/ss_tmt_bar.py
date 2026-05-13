from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re
import json
import base64
import qrcode
from io import BytesIO
from lxml import etree
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import math
from scipy.interpolate import CubicSpline , interp1d , Akima1DInterpolator
from scipy.optimize import minimize_scalar
from matplotlib.ticker import MultipleLocator, StrMethodFormatter

class StainlessSteel(models.Model):
    _name = "mechanical.stainless.steel.tmt.bar"
    _inherit = "lerm.eln"
    _description = 'mechanical.stainless.steel.tmt.bar'
   


        
    bar_test_line_ids = fields.One2many('stainless.tmt.bar.line','parent_id',string='TMT Bar Test Lines')
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'stainless.steel.tmt.bar.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        default_lines = []

        bar_data = [
            (8, 0.395),
            (10, 0.617),
            (12, 0.888),
            (16, 1.580),
            (20, 2.470),
            (25, 3.850),
            (28, 4.830),
            (32, 6.330),
        ]

        for dia, weight in bar_data:
            for _ in range(3):  # Repeat 3 times
                default_lines.append((0, 0, {
                    'dia_of_bar': dia,
                    'weight_kg_min': weight,
                }))

        res['bar_test_line_ids'] = default_lines
        return res



    def open_add_bar_line_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add TMT Bar Line',
            'res_model': 'stainless.tmt.bar.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_parent_id': self.id,
            }
        }

    Id_no = fields.Char("ID No")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    name = fields.Char("Name",default="STEEL TMT BAR")
    size = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    diameter = fields.Integer(string="Dia. in mm",compute="_compute_dia")
    lentgh = fields.Float(string="Length in meter",digits=(10, 3))
    weight = fields.Float(string="Weight, in kg",digits=(10, 3))
    weight_per_meter = fields.Float(string="Weight per meter, kg/m",compute="_compute_weight_per_meter",store=True)
    crossectional_area = fields.Float(string="Area mm²",compute="_compute_crossectional_area")
    gauge_length = fields.Integer(string="Gauge Length mm",compute="_compute_gauge_length",store=True)
    elongated_gauge_length = fields.Float(string="Final Length, mm")
    percent_elongation = fields.Float(string="% Elongation",compute="_compute_elongation_percent",store=True)
    yeild_load = fields.Float(string="0.2% Proof Load / Yield Load, KN")
    ultimate_load = fields.Float(string="Ultimate Load, Kn")
    proof_yeid_stress = fields.Float(string="0.2% Proof Stress",compute="_compute_proof_yeid_stress",store=True)
    ult_tens_strgth = fields.Float(string="Ultimate Tensile Strength, N/mm2",compute="_compute_ult_tens_strgth",store=True)
    fracture = fields.Char("Fracture (Within Gauge Length)",default="W.G.L")
    eln_ref = fields.Many2one('lerm.eln',string="ELN")
    ts_ys_ratio = fields.Float(string="TS/YS Ratio",compute="_compute_ts_ys_ratio",store=True)
    weight_per_meter = fields.Float(string="Weight per meter",compute="_compute_weight_per_meter",store=True,digits=(10, 3))
    variation = fields.Float(string="Variation")

    requirement_utl = fields.Float(string="Requirement",compute="_compute_requirement_utl",store=True)
    requirement_yield = fields.Float(string="Requirement",compute="_compute_requirement_yield",store=True)
    requirement_ts_ys = fields.Float(string="Requirement",compute="_compute_requirement_ts_ys",store=True)
    requirement_elongation = fields.Float(string="Requirement",compute="_compute_requirement_elongation",store=True)
    requirement_weight_per_meter = fields.Float(string="Requirement",compute="_compute_requirement_weight_per_meter",digits=(16, 4),store=True)

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    # tests = fields.Many2many("mechanical.tmt.test",string="Tests")

    bend_test1 = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non-satisfactory', 'Non-Satisfactory')],"Bend Test",store=True)
    
    re_bend_test1 = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non-satisfactory', 'Non-Satisfactory')],"Re-Bend Test",store=True)

    uts_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="Conformity",compute="_compute_uts_conformity",store=True)

    yield_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="Conformity",compute="_compute_yield_conformity",store=True)

    elongation_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="Conformity",compute="_compute_elongation_conformity",store=True)

    ts_ys_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="Conformity",compute="_compute_ts_ys_conformity",store=True)

    weight_per_meter_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="Conformity",compute="_compute_weight_per_meter_conformity",store=True)

    fracture_visible = fields.Boolean("Fracture",compute="_compute_visible")
    bend_visible = fields.Boolean("Bend Test",compute="_compute_visible")
    rebend_visible = fields.Boolean("Rebend Test",compute="_compute_visible")

    uts_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_uts_nabl",store=True)

    yield_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_yield_nabl",store=True)

    elongation_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_elongation_nabl",store=True)

    ts_ys_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_ts_ys_nabl",store=True)
    
    

    weight_per_meter_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_weight_per_meter_nabl",store=True)

    uts_visible = fields.Boolean("Ultimate Tensile Strength",compute="_compute_visible")
    elongation_visible = fields.Boolean("Elongation",compute="_compute_visible")
    weight_per_meter_visible = fields.Boolean("Weight Per Meter",compute="_compute_visible")
    yield_visible = fields.Boolean("Yield",compute="_compute_visible")
    ts_ys_visible = fields.Boolean("TS/YS",compute="_compute_visible")

    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.fracture_visible = False
            record.bend_visible  = False  
            record.rebend_visible = False

            record.uts_visible = False
            record.elongation_visible  = False  
            record.weight_per_meter_visible = False
            record.yield_visible  = False  
            record.ts_ys_visible = False
            
            for sample in record.sample_parameters:
                # print("Samples internal id",sample.internal_id)
                if sample.internal_id == 'fafcb7b0-8df1-47d0-92a9-b6eb99af38e0':
                    record.fracture_visible = True
                if sample.internal_id == '25fcb167-68bc-48d0-880f-77ca213fd995':
                    record.bend_visible = True
                if sample.internal_id == '709c7024-d1b9-48bb-8c94-fc0742a3e080':
                    record.rebend_visible = True

                if sample.internal_id == 'ad88ad89-cb0b-4f51-88a5-1d1fbf5a31fe':
                    record.uts_visible = True
                if sample.internal_id == 'f244daa5-d08f-4336-bdbf-968dfc3c37dc':
                    record.elongation_visible = True
                if sample.internal_id == '51b0c744-b113-477a-8fde-b33cf309c1e3':
                    record.weight_per_meter_visible = True
                if sample.internal_id == 'd46dfca3-0395-4c5b-86a8-918bca950ef3':
                    record.yield_visible = True
                if sample.internal_id == 'c7908eda-7bf1-4fd4-aae6-f89c9fdab187':
                    record.ts_ys_visible = True


    @api.depends('weight','lentgh')
    def _compute_weight_per_meter(self):
        for record in self:
            if record.lentgh != 0:   
                record.weight_per_meter =  record.weight/record.lentgh
            else:
                record.weight_per_meter = 0

    @api.depends('weight_per_meter','eln_ref','size')
    def _compute_weight_per_meter_nabl(self):
      

        for record in self:
            record.weight_per_meter_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','51b0c744-b113-477a-8fde-b33cf309c1e3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','51b0c744-b113-477a-8fde-b33cf309c1e3')]).parameter_table
            # for material in materials:
            #     if material.size.id == record.size.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.weight_per_meter - record.weight_per_meter*mu_value
            upper = record.weight_per_meter + record.weight_per_meter*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.weight_per_meter_nabl = 'pass'
                break
            else:
                record.weight_per_meter_nabl = 'fail'

    @api.depends('weight_per_meter','eln_ref','size')
    def _compute_weight_per_meter_conformity(self):
        for record in self:
            record.weight_per_meter_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','51b0c744-b113-477a-8fde-b33cf309c1e3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','51b0c744-b113-477a-8fde-b33cf309c1e3')]).parameter_table
            for material in materials:
                if material.size.id == record.size.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.weight_per_meter - record.weight_per_meter*mu_value
                    upper = record.weight_per_meter + record.weight_per_meter*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.weight_per_meter_conformity = 'pass'
                        break
                    else:
                        record.weight_per_meter_conformity = 'fail'

    @api.depends('eln_ref','size')
    def _compute_requirement_weight_per_meter(self):
        for record in self:
            # record.requirement_yield = 0
            # line = self.env['eln.parameters.result'].sudo().search([('eln_id','=',record.eln_ref.id),('parameter.parameter_name','=','Yield Stress (TMT)')]).parameter
            # materials = self.env['lerm.parameter.master'].sudo().search([('id','=',line.id)]).parameter_table
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','51b0c744-b113-477a-8fde-b33cf309c1e3')]).parameter_table
            for material in materials:
                if material.size.id == record.size.id:
                    req_min = material.req_min
                    record.requirement_weight_per_meter = req_min
                    break
                else:
                    record.requirement_weight_per_meter = 0

    @api.depends('ult_tens_strgth','proof_yeid_stress')
    def _compute_ts_ys_ratio(self):
        for record in self:
            if record.proof_yeid_stress != 0:
                record.ts_ys_ratio = record.ult_tens_strgth / record.proof_yeid_stress
            else:
                record.ts_ys_ratio = 0


    @api.depends('ult_tens_strgth','eln_ref','grade')
    def _compute_uts_conformity(self):
        
        for record in self:
            record.uts_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ad88ad89-cb0b-4f51-88a5-1d1fbf5a31fe')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ad88ad89-cb0b-4f51-88a5-1d1fbf5a31fe')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.ult_tens_strgth - record.ult_tens_strgth*mu_value
                    upper = record.ult_tens_strgth + record.ult_tens_strgth*mu_value
           
                    if lower >= req_min and upper <= req_max:
                        record.uts_conformity = 'pass'
                        break
                    else:
                        record.uts_conformity = 'fail'

    @api.depends('ult_tens_strgth','eln_ref','grade')
    def _compute_uts_nabl(self):
        
        for record in self:
            # import wdb; wdb.set_trace()

            record.uts_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ad88ad89-cb0b-4f51-88a5-1d1fbf5a31fe')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ad88ad89-cb0b-4f51-88a5-1d1fbf5a31fe')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.ult_tens_strgth - record.ult_tens_strgth*mu_value
            upper = record.ult_tens_strgth + record.ult_tens_strgth*mu_value
            
            if lower >= lab_min and upper <= lab_max:
                record.uts_nabl = 'pass'
                break
            else:
                record.uts_nabl = 'fail'

    @api.depends('eln_ref','grade')
    def _compute_requirement_utl(self):
        for record in self:
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ad88ad89-cb0b-4f51-88a5-1d1fbf5a31fe')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    record.requirement_utl = req_min
                    break
                else:
                    record.requirement_utl = 0
                    


    @api.depends('percent_elongation','eln_ref','grade')
    def _compute_elongation_conformity(self):
       
        for record in self:
            record.elongation_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f244daa5-d08f-4336-bdbf-968dfc3c37dc')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f244daa5-d08f-4336-bdbf-968dfc3c37dc')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.percent_elongation - record.percent_elongation*mu_value
                    upper = record.percent_elongation + record.percent_elongation*mu_value
                    

                    if lower >= req_min and upper <= req_max:
                        record.elongation_conformity = 'pass'
                        break
                    else:
                        record.elongation_conformity = 'fail'

    @api.depends('percent_elongation','eln_ref','grade')
    def _compute_elongation_nabl(self):
       
        for record in self:
            record.elongation_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f244daa5-d08f-4336-bdbf-968dfc3c37dc')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f244daa5-d08f-4336-bdbf-968dfc3c37dc')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.percent_elongation - record.percent_elongation*mu_value
            upper = record.percent_elongation + record.percent_elongation*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.elongation_nabl = 'pass'
                break
            else:
                record.elongation_nabl = 'fail'

    @api.depends('eln_ref','grade')
    def _compute_requirement_elongation(self):
        for record in self:
            # record.requirement_elongation = 0
            # line = self.env['eln.parameters.result'].sudo().search([('eln_id','=',record.eln_ref.id),('parameter.parameter_name','=','% Elongation (TMT)')]).parameter
            # materials = self.env['lerm.parameter.master'].sudo().search([('id','=',line.id)]).parameter_table
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f244daa5-d08f-4336-bdbf-968dfc3c37dc')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    record.requirement_elongation = req_min
                    break
                else:
                    record.requirement_elongation = 0


    @api.depends('proof_yeid_stress','eln_ref','grade')
    def _compute_yield_conformity(self):
    
        for record in self:
            record.yield_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d46dfca3-0395-4c5b-86a8-918bca950ef3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d46dfca3-0395-4c5b-86a8-918bca950ef3')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.proof_yeid_stress - record.proof_yeid_stress*mu_value
                    upper = record.proof_yeid_stress + record.proof_yeid_stress*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.yield_conformity = 'pass'
                        break
                    else:
                        record.yield_conformity = 'fail'

    @api.depends('proof_yeid_stress','eln_ref','grade')
    def _compute_yield_nabl(self):
    
        for record in self:
            record.yield_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d46dfca3-0395-4c5b-86a8-918bca950ef3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d46dfca3-0395-4c5b-86a8-918bca950ef3')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.proof_yeid_stress - record.proof_yeid_stress*mu_value
            upper = record.proof_yeid_stress + record.proof_yeid_stress*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.yield_nabl = 'pass'
                break
            else:
                record.yield_nabl = 'fail'


    @api.depends('eln_ref','grade')
    def _compute_requirement_yield(self):
        for record in self:
            # record.requirement_yield = 0
            # line = self.env['eln.parameters.result'].sudo().search([('eln_id','=',record.eln_ref.id),('parameter.parameter_name','=','Yield Stress (TMT)')]).parameter
            # materials = self.env['lerm.parameter.master'].sudo().search([('id','=',line.id)]).parameter_table
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d46dfca3-0395-4c5b-86a8-918bca950ef3')]).parameter_table
            
            for material in materials:
                print("DATA ", material)
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    record.requirement_yield = req_min
                    break
                else:
                    record.requirement_yield = 0
        
    @api.depends('ts_ys_ratio','eln_ref','grade')
    def _compute_ts_ys_conformity(self):

        for record in self:
            record.ts_ys_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c7908eda-7bf1-4fd4-aae6-f89c9fdab187')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c7908eda-7bf1-4fd4-aae6-f89c9fdab187')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.proof_yeid_stress - record.proof_yeid_stress*mu_value
                    upper = record.proof_yeid_stress + record.proof_yeid_stress*mu_value
                    if lower >= req_min :
                        record.ts_ys_conformity = 'pass'
                        break
                    else:
                        record.ts_ys_conformity = 'fail'


    @api.depends('ts_ys_ratio','eln_ref','grade')
    def _compute_ts_ys_nabl(self):

        for record in self:
            record.ts_ys_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c7908eda-7bf1-4fd4-aae6-f89c9fdab187')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c7908eda-7bf1-4fd4-aae6-f89c9fdab187')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            req_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.proof_yeid_stress - record.proof_yeid_stress*mu_value
            upper = record.proof_yeid_stress + record.proof_yeid_stress*mu_value
            if lower >= lab_min :
                record.ts_ys_nabl = 'pass'
                break
            else:
                record.ts_ys_nabl = 'fail'

    @api.depends('eln_ref','grade')
    def _compute_requirement_ts_ys(self):
        for record in self:
            # record.requirement_yield = 0
            # line = self.env['eln.parameters.result'].sudo().search([('eln_id','=',record.eln_ref.id),('parameter.parameter_name','=','Yield Stress (TMT)')]).parameter
            # materials = self.env['lerm.parameter.master'].sudo().search([('id','=',line.id)]).parameter_table
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c7908eda-7bf1-4fd4-aae6-f89c9fdab187')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    record.requirement_ts_ys = req_min
                    break
                else:
                    record.requirement_ts_ys = 0
        


    @api.depends('weight', 'lentgh')
    def _compute_weight_per_meter(self):
        for record in self:
            if record.lentgh != 0:
                record.weight_per_meter = record.weight / record.lentgh
                # to be removed
                self._compute_sample_parameters()

            else:
                record.weight_per_meter = 0.0

    @api.depends('weight', 'lentgh')
    def _compute_crossectional_area(self):
        for record in self:
            if record.lentgh != 0:
                # print(record.weight / (0.00785 * record.lentgh))
                # record.crossectional_area = round((record.weight / (0.00785 * record.lentgh)),2)
                record.crossectional_area = round((record.weight / record.lentgh)/ (0.00774 ),2)
                
            else:
                record.crossectional_area = 0.0
    @api.depends('crossectional_area')
    def _compute_gauge_length(self):
        for record in self:
            gauge_length = math.sqrt(record.crossectional_area) * 5.65
            # Check if the decimal part is greater than or equal to 0.5
            if gauge_length - int(gauge_length) >= 0.5:
                rounded_gauge_length = math.ceil(gauge_length)
            else:
                rounded_gauge_length = math.floor(gauge_length)
            record.gauge_length = int(rounded_gauge_length)

    @api.depends('yeild_load','crossectional_area')
    def _compute_proof_yeid_stress(self):
        for record in self:
            if record.crossectional_area != 0:
                record.proof_yeid_stress = record.yeild_load / record.crossectional_area * 1000
            else:
                record.proof_yeid_stress = 0.0

    @api.depends('ultimate_load')
    def _compute_ult_tens_strgth(self):
        for record in self:
            if record.crossectional_area != 0:
                record.ult_tens_strgth = record.ultimate_load / record.crossectional_area * 1000
            else:
                record.ult_tens_strgth = 0.0


    @api.depends('gauge_length','elongated_gauge_length')
    def _compute_elongation_percent(self):
        for record in self:
            if record.gauge_length != 0:
                record.percent_elongation = ((record.elongated_gauge_length - record.gauge_length)/record.gauge_length)*100
            else:
                record.percent_elongation = 0


    @api.model
    def create(self, vals):
        record = super(StainlessSteel, self).create(vals)
        # import wdb;wdb.set_trace()
        # record.get_all_fields()
        self._compute_size_id()
        self._compute_grade_id()
        self._compute_sample_parameters()
        record.eln_ref.write({'model_id':record.id})
        return record

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()
        self._compute_size_id()
        self._compute_grade_id()
        self._compute_requirement_weight_per_meter()
        self._compute_requirement_elongation()
        self._compute_requirement_ts_ys()
        self._compute_requirement_yield()
        self._compute_requirement_utl()

        return super(StainlessSteel, self).read(fields=fields, load=load)


    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    # @api.onchange('bend_test1')
    # def _compute_wdb(self):
    #     import wdb; wdb.set_trace()
        
    

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size = self.eln_ref.size_id.id

    @api.depends('eln_ref')
    def _compute_dia(self):
        for record in self:
            pattern = r'\d+'
            match = re.search(pattern, str(record.eln_ref.size_id.size))
            if match:
                dia = int(match.group())
                record.diameter = int(match.group())
            else:
                record.diameter = 0
                 


    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == 'ad88ad89-cb0b-4f51-88a5-1d1fbf5a31fe':
                result.result_char = round(self.ult_tens_strgth,2)
                if self.uts_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == 'd46dfca3-0395-4c5b-86a8-918bca950ef3':
                result.result_char = round(self.proof_yeid_stress,2)
                if self.yield_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == 'f244daa5-d08f-4336-bdbf-968dfc3c37dc':
                result.result_char = self.percent_elongation
                if self.elongation_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == 'c7908eda-7bf1-4fd4-aae6-f89c9fdab187':
                result.result_char = round(self.ts_ys_ratio,2)
                if self.ts_ys_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '51b0c744-b113-477a-8fde-b33cf309c1e3':
                result.result_char = round(self.weight_per_meter,3)
                if self.weight_per_meter_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == 'fafcb7b0-8df1-47d0-92a9-b6eb99af38e0':
                result.result_char =self.fracture
                continue
            if result.parameter.internal_id == '25fcb167-68bc-48d0-880f-77ca213fd995':
                result.result_char = self.bend_test1
                continue
            if result.parameter.internal_id == '709c7024-d1b9-48bb-8c94-fc0742a3e080':
                result.result_char = self.re_bend_test1
                continue

        return {
                'view_mode': 'form',
                'res_model': "lerm.eln",
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.eln_ref.id,
                
            }

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

class StainlessTMTBarLine(models.Model):
    _name = 'stainless.tmt.bar.line'
    _description = 'TMT Bar Line'

    parent_id = fields.Many2one('mechanical.stainless.steel.tmt.bar',string='Parent Test')

    dia_of_bar = fields.Float(string="Dia of Bar (mm)")
    yield_stress = fields.Float(string="Yield Stress (N/mm²)")
    ultimate_tensile_stress = fields.Float(string="Ultimate Tensile Stress (N/mm²)")
    elongation = fields.Float(string="Elongation (%)")
    weight_per_meter = fields.Float(string="Weight / Meter (kg/m)", store=True)
    weight_kg_min = fields.Float(string="Weight kg/m (Min.)", store=True, digits=(12,3))
    bend_test = fields.Char("Bend Test",store=True)

    # @api.onchange('bend_test')
    # def _onchange_bend_test(self):
    #     if self.parent_id and self.dia_of_bar:
    #         for line in self.parent_id.bar_test_line_ids:
    #             if line != self and line.dia_of_bar == self.dia_of_bar:
    #                 line.bend_test = self.bend_test

    def write(self, vals):
        res = super().write(vals)

        if self._context.get('sync_bend_test'):
            return res  # Prevent recursion

        for record in self:
            if 'bend_test' in vals and record.dia_of_bar and record.parent_id:
                lines = self.search([
                    ('parent_id', '=', record.parent_id.id),
                    ('dia_of_bar', '=', record.dia_of_bar),
                    ('id', '!=', record.id),
                ])
                lines.with_context(sync_bend_test=True).write({'bend_test': vals['bend_test']})

        return res


class StainlessTMTBarWizard(models.TransientModel):
    _name = 'stainless.tmt.bar.wizard'
    _description = 'Wizard for adding TMT Bar Line'

    parent_id = fields.Many2one('mechanical.stainless.steel.tmt.bar', required=True)
    dia_of_bar = fields.Float(required=True)
    yield_stress = fields.Float(required=True)
    ultimate_tensile_stress = fields.Float(required=True)
    elongation = fields.Float(required=True)

    def action_add_bar_line(self):
        for wizard in self:
            self.env['stainless.tmt.bar.line'].create({
                'parent_id': wizard.parent_id.id,
                'dia_of_bar': wizard.dia_of_bar,
                'yield_stress': wizard.yield_stress,
                'ultimate_tensile_stress': wizard.ultimate_tensile_stress,
                'elongation': wizard.elongation,
            })


