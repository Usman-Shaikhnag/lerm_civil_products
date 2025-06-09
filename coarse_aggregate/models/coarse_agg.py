from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re

class CoarseAggregateMechanical(models.Model):
    _name = "mechanical.coarse.aggregate1"
    _inherit = "lerm.eln"
    _description = 'mechanical.coarse.aggregate1'
    _rec_name = "name"

    name = fields.Char("Name",default="Coarse Aggregate")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    size_id = fields.Many2one('lerm.size.line',compute="_compute_size_id")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)


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
        record = self.env['mechanical.coarse.aggregate1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



    # Crushing Value
    crushing_value_name = fields.Char("Name",default="Crushing Value")
    crushing_visible = fields.Boolean("Crushing Visible",compute="_compute_visible")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    crushing_value_child_lines = fields.One2many('mechanical.crushing.value.coarse.aggregate.line1','parent_id',string="Parameter")

    average_crushing_value = fields.Float(string="Average Aggregate Crushing Value", compute="_compute_average_crushing_value")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71')]).parameter_table
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




    @api.depends('crushing_value_child_lines.crushing_value')
    def _compute_average_crushing_value(self):
        for record in self:
            if record.crushing_value_child_lines:
                sum_crushing_values = sum(record.crushing_value_child_lines.mapped('crushing_value'))
                record.average_crushing_value = round((sum_crushing_values / len(record.crushing_value_child_lines)),1)
            else:
                record.average_crushing_value = 0.0
   

    

    # Abrasion Value
    abrasion_value_name = fields.Char("Name",default="Los Angeles Abrasion Value")
    abrasion_visible = fields.Boolean("Abrasion Visible",compute="_compute_visible")

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    # abrasion_value_child_lines = fields.One2many('mechanical.abrasion.value.coarse.aggregate.line','parent_id',string="Parameter")
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

    #  specific_gravity_child_lines = fields.One2many('mechanical.specific.gravity.and.water.absorption.line','parent_id',string="Parameter")

    wt_surface_dry = fields.Float(string="Weight of saturated surface dry (SSD) sample in air in gms")
    wt_sample_inwater = fields.Float(string="Weight of saturated sample in water in gms")
    oven_dried_wt = fields.Float(string="Oven dried weight of sample in gms")
    specific_gravity = fields.Float(string="Specific Gravity",compute="_compute_specific_gravity")
    water_absorption = fields.Float(string="Water absorption  %",compute="_compute_water_absorption")


    specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_specific_gravity_conformity", store=True)

    @api.depends('specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_conformity(self):
        
        for record in self:
            record.specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3114db41-cfa7-49ad-9324-fcdbc9661038')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3114db41-cfa7-49ad-9324-fcdbc9661038')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.specific_gravity - record.specific_gravity*mu_value
                    upper = record.specific_gravity + record.specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.specific_gravity_conformity = 'fail'

    specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_specific_gravity_nabl", store=True)

    @api.depends('specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_nabl(self):
        
        for record in self:
            record.specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3114db41-cfa7-49ad-9324-fcdbc9661038')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3114db41-cfa7-49ad-9324-fcdbc9661038')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.specific_gravity - record.specific_gravity*mu_value
                    upper = record.specific_gravity + record.specific_gravity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.specific_gravity_nabl = 'pass'
                        break
                    else:
                        record.specific_gravity_nabl = 'fail'



    @api.depends('wt_surface_dry', 'wt_sample_inwater', 'oven_dried_wt')
    def _compute_specific_gravity(self):
        for line in self:
            if line.wt_surface_dry - line.wt_sample_inwater != 0:
                line.specific_gravity = round((line.oven_dried_wt / (line.wt_surface_dry - line.wt_sample_inwater)),2)
            else:
                line.specific_gravity = 0.0



    @api.depends('wt_surface_dry', 'oven_dried_wt')
    def _compute_water_absorption(self):
        for line in self:
            if line.oven_dried_wt != 0:
                line.water_absorption = round((((line.wt_surface_dry - line.oven_dried_wt) / line.oven_dried_wt) * 100),2)
            else:
                line.water_absorption = 0.0


    # Impact Value 
    impact_value_name = fields.Char("Name",default="Aggregate Impact Value")
    impact_visible = fields.Boolean("Impact Visible",compute="_compute_visible")

    impact_value_child_lines = fields.One2many('mechanical.impact.value.coarse.aggregate.line1','parent_id',string="Parameter")

    average_impact_value = fields.Float(string="Average Aggregate Impact Value", compute="_compute_average_impact_value")


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

    impact_value_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_impact_value_nabl", store=True)

    @api.depends('average_impact_value','eln_ref','grade')
    def _compute_average_impact_value_nabl(self):
        
        for record in self:
            record.impact_value_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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


    @api.depends('impact_value_child_lines.impact_value')
    def _compute_average_impact_value(self):
        for record in self:
            if record.impact_value_child_lines:
                sum_impact_value = sum(record.impact_value_child_lines.mapped('impact_value'))
                record.average_impact_value = ((sum_impact_value / len(record.impact_value_child_lines)))
            else:
                record.average_impact_value = 0.0

    # @api.model
    # def create(self, vals):
    #     # import wdb;wdb.set_trace()
    #     record = super(coarseAggregateMechanical, self).create(vals)
    #     record.parameter_id.write({'model_id':record.id})
    #     return record
   
    # !0% Fine Value
    name_10fine = fields.Char(default="10% Fine Value")
    fine10_visible = fields.Boolean("10% Fine Visible",compute="_compute_visible")

    wt_sample_10fine = fields.Float("Weight of Sample taken in gms, A")
    wt_sample_passing_10fine = fields.Float("Weight of sample passing 2.36 mm IS sieve after applying load in 10 min, B")
    percent_of_fines = fields.Float("Percentage of Fines",compute="_compute_percent_fines")
    load_applied_10fine = fields.Float("Load applied in 10 min, X kN")
    load_10percent_fine_values = fields.Float("Load for 10 percent fines value",compute="_compute_load_10percent_fine_values")

    @api.depends('wt_sample_10fine','wt_sample_passing_10fine')
    def _compute_percent_fines(self):
        for record in self:
            if record.wt_sample_10fine != 0:
                record.percent_of_fines = (record.wt_sample_passing_10fine / record.wt_sample_10fine )*100
            else:
                record.percent_of_fines = 0

    @api.depends('percent_of_fines','load_applied_10fine')
    def _compute_load_10percent_fine_values(self):
        for record in self:
            if record.percent_of_fines != 0:
                record.load_10percent_fine_values = (14 * record.load_applied_10fine)/(record.percent_of_fines + 4)
            else:
                record.load_10percent_fine_values = 0


    load_10percent_fine_values_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_load_10percent_fine_values_conformity", store=True)



    @api.depends('load_10percent_fine_values','eln_ref','grade')
    def _compute_load_10percent_fine_values_conformity(self):
        
        for record in self:
            record.load_10percent_fine_values_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f506c08-4369-491d-93a6-030514c29661')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f506c08-4369-491d-93a6-030514c29661')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f506c08-4369-491d-93a6-030514c29661')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f506c08-4369-491d-93a6-030514c29661')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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

    
    

    # Soundness Na2SO4
    soundness_na2so4_name = fields.Char("Name",default="Soundness Na2SO4")
    soundness_na2so4_visible = fields.Boolean("Soundness Na2SO4 Visible",compute="_compute_visible")

    soundness_na2so4_child_lines = fields.One2many('mechanical.soundness.na2so4.line1','parent_id',string="Parameter",default=lambda self: self._default_soundness_na2so4_child_lines())
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
            for material in materials:
                if material.grade.id == record.grade.id:
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

    soundness_mgso4_child_lines = fields.One2many('mechanical.soundness.mgso4.line1','parent_id',string="Parameter",default=lambda self: self._default_soundness_mgso4_child_lines())
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
    # elongation_child_lines = fields.One2many('mechanical.elongation.index.line','parent_id',string="Parameter", default=lambda self: self.default_elongation_sizes())
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
    # flakiness_child_lines = fields.One2many('mechanical.flakiness.index.line','parent_id',string="Parameter", default=lambda self: self.default_flakiness_sizes())
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

    elongation_table = fields.One2many('mechanical.elongation.flakiness.line1','parent_id',string="Elongation Flakiness Index",default=lambda self: self.default_flakiness_sizes())

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
                if material.grade.id == record.grade.id:
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
            for material in materials:
                if material.grade.id == record.grade.id:
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
            (0, 0, {'sieve_size': '63 mm'}),
            (0, 0, {'sieve_size': '50 mm'}),
            (0, 0, {'sieve_size': '40 mm'}),
            (0, 0, {'sieve_size': '31.5 mm'}),
            (0, 0, {'sieve_size': '25 mm'}),
            (0, 0, {'sieve_size': '20 mm'}),
            (0, 0, {'sieve_size': '16 mm'}),
            (0, 0, {'sieve_size': '12.5 mm'}),
            (0, 0, {'sieve_size': '10 mm'}),
            (0, 0, {'sieve_size': '6.3 mm'}),
            (0, 0, {'sieve_size': '4.75 mm'}),
            (0, 0, {'sieve_size': '2.36 mm'}),
            (0, 0, {'sieve_size': '1.18 mm'}),
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
            for material in materials:
                if material.grade.id == record.grade.id:
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




    # Bulk Density
    loose_bulk_density_name = fields.Char("Name",default="Loose Bulk Density (LBD)")
    loose_bulk_visible = fields.Boolean("Loose Bulk Density Visible",compute="_compute_visible")

    # loose_bulk_density_child_lines = fields.One2many('coarse.aggregate.loose.bulk.density.line','parent_id',string="Parameter")
    weight_empty_bucket_loose = fields.Float(string="Weight of Empty Bucket in kg")
    volume_of_bucket_loose = fields.Float(string="Volume of Bucket in cubic meter")
    sample_plus_bucket_loose = fields.Float(string="[Sample Weight + Bucket  Weight] in kg")
    sample_weight_loose = fields.Float(string="Sample Weight in kg",compute="_compute_sample_weight_loose")
    loose_bulk_density = fields.Float(string="Loose Bulk Density in kg per cubic meter",compute="_compute_loose_bulk_density")


    @api.depends('sample_plus_bucket_loose', 'weight_empty_bucket_loose')
    def _compute_sample_weight_loose(self):
        for record in self:
            record.sample_weight_loose = record.sample_plus_bucket_loose - record.weight_empty_bucket_loose

    

    @api.depends('sample_weight_loose', 'volume_of_bucket_loose')
    def _compute_loose_bulk_density(self):
        for record in self:
            if record.volume_of_bucket_loose:
                record.loose_bulk_density = round((record.sample_weight_loose / record.volume_of_bucket_loose),2)
            else:
                record.loose_bulk_density = 0.0


    loose_bulk_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_loose_bulk_density_conformity", store=True)

    @api.depends('loose_bulk_density','eln_ref','grade')
    def _compute_loose_bulk_density_conformity(self):
        
        for record in self:
            record.loose_bulk_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65a41d1f-d557-438e-8fd1-2c619a334d02')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65a41d1f-d557-438e-8fd1-2c619a334d02')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.loose_bulk_density - record.loose_bulk_density*mu_value
                    upper = record.loose_bulk_density + record.loose_bulk_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.loose_bulk_density_conformity = 'pass'
                        break
                    else:
                        record.loose_bulk_density_conformity = 'fail'

    loose_bulk_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_loose_bulk_density_nabl", store=True)

    @api.depends('loose_bulk_density','eln_ref','grade')
    def _compute_loose_bulk_density_nabl(self):
        
        for record in self:
            record.loose_bulk_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65a41d1f-d557-438e-8fd1-2c619a334d02')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65a41d1f-d557-438e-8fd1-2c619a334d02')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.loose_bulk_density - record.loose_bulk_density*mu_value
                    upper = record.loose_bulk_density + record.loose_bulk_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.loose_bulk_density_nabl = 'pass'
                        break
                    else:
                        record.loose_bulk_density_nabl = 'fail'


    rodded_bulk_density_name = fields.Char("Name",default="Rodded Bulk Density (RBD)")
    rodded_bulk_visible = fields.Boolean("Rodded Bulk Density Visible",compute="_compute_visible")

    # rodded_bulk_density_child_lines = fields.One2many('coarse.aggregate.rodded.bulk.density.line','parent_id',string="Parameter")
    weight_empty_bucket_rodded = fields.Float(string="Weight of Empty Bucket in kg")
    volume_of_bucket_rodded = fields.Float(string="Volume of Bucket in cubic meter")
    sample_plus_bucket_rodded = fields.Float(string="[Sample Weight + Bucket  Weight] in kg")
    sample_weight_rodded = fields.Float(string="Sample Weight in kg",compute="_compute_sample_weight_rodded")
    rodded_bulk_density = fields.Float(string="Rodded Bulk Density in kg per cubic meter",compute="_compute_rodded_bulk_density")

    rodded_bulk_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_rodded_bulk_density_conformity", store=True)

    @api.depends('rodded_bulk_density','eln_ref','grade')
    def _compute_rodded_bulk_density_conformity(self):
        
        for record in self:
            record.rodded_bulk_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.rodded_bulk_density - record.rodded_bulk_density*mu_value
                    upper = record.rodded_bulk_density + record.rodded_bulk_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.rodded_bulk_density_conformity = 'pass'
                        break
                    else:
                        record.rodded_bulk_density_conformity = 'fail'

    rodded_bulk_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_rodded_bulk_density_nabl", store=True)

    @api.depends('rodded_bulk_density','eln_ref','grade')
    def _compute_rodded_bulk_density_nabl(self):
        
        for record in self:
            record.rodded_bulk_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.rodded_bulk_density - record.rodded_bulk_density*mu_value
                    upper = record.rodded_bulk_density + record.rodded_bulk_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.rodded_bulk_density_nabl = 'pass'
                        break
                    else:
                        record.rodded_bulk_density_nabl = 'fail'


    @api.depends('sample_plus_bucket_rodded', 'weight_empty_bucket_rodded')
    def _compute_sample_weight_rodded(self):
        for record in self:
            record.sample_weight_rodded = record.sample_plus_bucket_rodded - record.weight_empty_bucket_rodded

    

    @api.depends('sample_weight_rodded', 'volume_of_bucket_rodded')
    def _compute_rodded_bulk_density(self):
        for record in self:
            if record.volume_of_bucket_rodded:
                record.rodded_bulk_density = round((record.sample_weight_rodded / record.volume_of_bucket_rodded),2)
            else:
                record.rodded_bulk_density = 0.0

    # Sieve Analysis 
    sieve_analysis_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

    sieve_analysis_child_lines = fields.One2many('mechanical.coarse.aggregate.sieve.analysis.line1','parent_id',string="Parameter")
    total_sieve_analysis = fields.Float(string="Total",compute="_compute_total_sieve")


    def default_get(self, fields):
        print("From Default Value")
        res = super(CoarseAggregateMechanical, self).default_get(fields)

        coarse_sieve_20mm = ['40 mm', '20 mm', '10 mm', '4.75 mm', 'pan']
        coarse_sieve_10mm = ['12.5 mm', '10 mm', '4.75 mm', '2.36 mm', 'pan']

        default_sieve_sizes = []
        eln_ref = res['eln_ref']

        size_id = self.env['lerm.eln'].sudo().search([('id','=',eln_ref)]).size_id.size

        print("Size",size_id)
        pattern = r'\d+'
        match = re.search(pattern, size_id)
        if match:
            number = int(match.group())
            print("Number",number)
            if number == 10:
                for i in range(5):  # You can change the number of default lines as needed
                    size = {
                        'sieve_size': coarse_sieve_10mm[i] # Set the default product
                        # Set the default quantity
                    }
                    default_sieve_sizes.append((0, 0, size))
                res['sieve_analysis_child_lines'] = default_sieve_sizes
            elif number == 20:
                for i in range(5):  # You can change the number of default lines as needed
                    size = {
                        'sieve_size': coarse_sieve_20mm[i] # Set the default product
                        # Set the default quantity
                    }
                    default_sieve_sizes.append((0, 0, size))
                res['sieve_analysis_child_lines'] = default_sieve_sizes
            else :
                res['sieve_analysis_child_lines'] = default_sieve_sizes


        else:
            pass
        
        return res




    def calculate_sieve(self): 
        for record in self:
            for line in record.sieve_analysis_child_lines:
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
                    previous_line_record = self.env['mechanical.coarse.aggregate.sieve.analysis.line1'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
                    line.write({'cumulative_retained': previous_line_record + line.percent_retained})
                    line.write({'passing_percent': round(100-(previous_line_record + line.percent_retained),2)})
                    print("Previous Cumulative",previous_line_record)
                    

    
    @api.depends('sieve_analysis_child_lines.wt_retained')
    def _compute_total_sieve(self):
        for record in self:
            print("recordd",record)
            record.total_sieve_analysis = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))


    # @api.depends('sieve_analysis_child_lines.wt_retained')
    # def _compute_cumulative_sieve(self):
    #     for record in self:
    #         print("recordd",record)
    #         record.cumulative = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))


    # Aggregate grading  

    aggregate_grading_name = fields.Char("Name",default="All in Aggregate Grading")
    aggregate_grading_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

    aggregate_grading_child_lines = fields.One2many('mechanical.aggregate.grading.line1','parent_id',string="Parameter")
    total_aggregate_grading = fields.Integer(string="Total",compute="_compute_total_aggregate_grading")
    # cumulative_aggregate_grading = fields.Float(string="Cumulative",compute="_compute_cumulative_aggregate_grading")


    def calculate_aggregate(self): 
        for record in self:
            for line in record.aggregate_grading_child_lines:
                print("Rows",str(line.percent_retained))
                previous_line = line.serial_no - 1
                if previous_line == 0:
                    if line.percent_retained == 0:
                        # print("Percent retained 0",line.percent_retained)
                        line.write({'cumulative_retained': line.percent_retained})
                        line.write({'passing_percent': 100 })
                    else:
                        # print("Percent retained else",line.percent_retained)
                        line.write({'cumulative_retained': line.percent_retained})
                        line.write({'passing_percent': 100 -line.percent_retained})
                else:
                    previous_line_record = self.env['mechanical.aggregate.grading.line1'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
                    line.write({'cumulative_retained': previous_line_record + line.percent_retained})
                    line.write({'passing_percent': 100-(previous_line_record + line.percent_retained)})
                    print("Previous Cumulative",previous_line_record)
                    

 

    # @api.depends('aggregate_grading_child_lines.wt_retained')
    # def _compute_cumulative_aggregate_grading(self):
    #     for record in self:
    #         print("recordd",record)
    #         record.cumulative_aggregate_grading = sum(record.aggregate_grading_child_lines.mapped('wt_retained'))


    @api.depends('aggregate_grading_child_lines.wt_retained')
    def _compute_total_aggregate_grading(self):
        for record in self:
            print("recordd",record)
            record.total_aggregate_grading = sum(record.aggregate_grading_child_lines.mapped('wt_retained'))



    # Angularity 
    angularity_name = fields.Char("Name",default="Angularity Number")
    angularity_visible = fields.Boolean("Angularity",compute="_compute_visible")
    mean_wt_aggregate = fields.Float("Mean weight of the aggregate in the cylinder in gm , W")
    wt_water_required_angularity = fields.Float("Weight of water required to fill the cylinder in gm, C")
    specific_gravity_aggregate_angularity = fields.Float("Specific gravity of aggregate, GA")
    angularity_number = fields.Integer("Angularity number",compute="_compute_angularity_number")

    @api.depends('mean_wt_aggregate','wt_water_required_angularity','specific_gravity_aggregate_angularity')
    def _compute_angularity_number(self):
        for record in self:
            if (record.wt_water_required_angularity * record.specific_gravity_aggregate_angularity) != 0:
                record.angularity_number = round((67 - (100 * record.mean_wt_aggregate)/(record.wt_water_required_angularity * record.specific_gravity_aggregate_angularity)),2)
            else:
                record.angularity_number = 0


    angularity_number_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_angularity_number_conformity", store=True)

    @api.depends('angularity_number','eln_ref','grade')
    def _compute_angularity_number_conformity(self):
        
        for record in self:
            record.angularity_number_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5c163fc2-c88c-4233-921e-1eae56c3ba23')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5c163fc2-c88c-4233-921e-1eae56c3ba23')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.angularity_number - record.angularity_number*mu_value
                    upper = record.angularity_number + record.angularity_number*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.angularity_number_conformity = 'pass'
                        break
                    else:
                        record.angularity_number_conformity = 'fail'

    angularity_number_conformity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_angularity_number_conformity_nabl", store=True)

    @api.depends('angularity_number','eln_ref','grade')
    def _compute_angularity_number_conformity_nabl(self):
        
        for record in self:
            record.angularity_number_conformity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5c163fc2-c88c-4233-921e-1eae56c3ba23')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5c163fc2-c88c-4233-921e-1eae56c3ba23')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.angularity_number - record.angularity_number*mu_value
                    upper = record.angularity_number + record.angularity_number*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.angularity_number_conformity_nabl = 'pass'
                        break
                    else:
                        record.angularity_number_conformity_nabl = 'fail'


    @api.depends('eln_ref')
    def _compute_visible(self):
        for record in self:
            record.crushing_visible = False
            record.abrasion_visible = False
            record.specific_gravity_visible = False
            record.impact_visible = False
            record.fine10_visible = False
            record.soundness_na2so4_visible = False
            record.soundness_mgso4_visible = False
            record.elongation_visible = False
            record.flakiness_visible = False
            record.finer75_visible = False
            record.clay_lump_visible = False
            record.light_weight_visible = False
            record.loose_bulk_visible = False
            record.rodded_bulk_visible = False
            record.sieve_visible = False
            record.aggregate_grading_visible = False
            record.angularity_visible = False




            for sample in record.sample_parameters:
                if sample.internal_id == 'ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71':
                    record.crushing_visible = True
                if sample.internal_id == '37f2161e-5cc0-413f-b76c-10478c65baf9':
                    record.abrasion_visible = True
                if sample.internal_id == '3114db41-cfa7-49ad-9324-fcdbc9661038':
                    record.specific_gravity_visible = True
                if sample.internal_id == '2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2':
                    record.impact_visible = True
                if sample.internal_id == '5f506c08-4369-491d-93a6-030514c29661':
                    record.fine10_visible = True
                if sample.internal_id == '153f3c8b-6ccb-4db0-b89d-02db61f61e81':
                    record.soundness_na2so4_visible = True
                if sample.internal_id == '89650e58-11a6-42af-8eb7-187467443a79':
                    record.soundness_mgso4_visible = True
                # if sample.internal_id == '9effe915-e5a3-45a7-aaeb-10caababd667':
                #     record.elongation_visible = True
                # if sample.internal_id == 'be7a60bc-bb2c-410d-b91a-4f8730a4ac6f':
                #     record.flakiness_visible = True

                if sample.internal_id == '9effe915-e5a3-45a7-aaeb-10caababd667':
                    record.elongation_visible = True
                    record.flakiness_visible = True

                if sample.internal_id == 'be7a60bc-bb2c-410d-b91a-4f8730a4ac6f':
                    record.flakiness_visible = True
                    record.elongation_visible = True
                if sample.internal_id == '988f5bf6-c865-453c-9cd6-993a5a59ad95':
                    record.finer75_visible = True
                if sample.internal_id == 'd7e389bc-21ad-41eb-a602-f448f996eb2f':
                    record.clay_lump_visible = True
                if sample.internal_id == 'e7cc6b68-2550-4e1e-a28e-8526295e733f':
                    record.light_weight_visible = True
                if sample.internal_id == '65a41d1f-d557-438e-8fd1-2c619a334d02':
                    record.loose_bulk_visible = True
                if sample.internal_id == '357f579d-a310-4015-bc11-28a85c53ac83':
                    record.rodded_bulk_visible = True
                if sample.internal_id == 'c2168fff-e47c-4155-99ff-9d7dc223e768':
                    record.sieve_visible = True
                if sample.internal_id == '6976f6b5-5756-4ef7-a680-50b0c0dbccc8':
                    record.aggregate_grading_visible = True
                if sample.internal_id == '5c163fc2-c88c-4233-921e-1eae56c3ba23':
                    record.angularity_visible = True

    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            # crushing 
            if result.parameter.internal_id == 'ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71':
                result.result_char = round(self.average_crushing_value,2)
                if self.average_crushing_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # abrasion 
            if result.parameter.internal_id == '37f2161e-5cc0-413f-b76c-10478c65baf9':
                result.result_char = round(self.abrasion_value_percentage,2)
                if self.abrasion_value_percentage_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # specific gravity 
            if result.parameter.internal_id == '3114db41-cfa7-49ad-9324-fcdbc9661038':
                result.result_char = round(self.specific_gravity,2)
                if self.specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # water absorbtion
            if result.parameter.internal_id == '22ee804f-41a3-4fd1-a301-a8d9180fba10':
                result.result_char = round(self.water_absorption,2)
                continue 
            # impact value 
            if result.parameter.internal_id == '2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2':
                result.result_char = round(self.average_impact_value,2)
                if self.impact_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # fine 10
            if result.parameter.internal_id == '5f506c08-4369-491d-93a6-030514c29661':
                result.result_char = round(self.load_10percent_fine_values,2)
                if self.load_10percent_fine_values_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # soundness na2so4
            if result.parameter.internal_id == '153f3c8b-6ccb-4db0-b89d-02db61f61e81':
                result.result_char = round(self.soundness_na2so4,2)
                if self.soundness_na2so4_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # soundness mgso4
            if result.parameter.internal_id == '89650e58-11a6-42af-8eb7-187467443a79':
                result.result_char = round(self.soundness_mgso4,2)
                if self.soundness_mgso4_nabl == 'pass':
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

        return super(CoarseAggregateMechanical, self).read(fields=fields, load=load)

   
    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['mechanical.coarse.aggregate1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


class AggregateGradingLine(models.Model):
    _name = "mechanical.aggregate.grading.line1"
    parent_id = fields.Many2one('mechanical.coarse.aggregate1', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size")
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

        return super(AggregateGradingLine, self).create(vals)

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
                    record.percent_retained = vals['wt_retained'] / record.parent_id.total_aggregate_grading * 100 if record.parent_id.total_aggregate_grading else 0

            new_self = super(AggregateGradingLine, self).write(vals)

            if 'wt_retained' in vals:
                for record in self:
                    record.parent_id._compute_total_aggregate_grading()

            return new_self

        return super(AggregateGradingLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(AggregateGradingLine, self).unlink()

        if parent_id:
            parent_id.aggregate_grading_child_lines._reorder_serial_numbers()

        return res


    @api.depends('wt_retained', 'parent_id.total_aggregate_grading')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = record.wt_retained / self.parent_id.total_sieve_analysis * 100
            except ZeroDivisionError:
                record.percent_retained = 0


    @api.depends('cumulative_retained')
    def _compute_cum_retained(self):
        self.cumulative_retained=0
        


    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.aggregate_grading_child_lines, key=lambda r: r.id)
            # index = sorted_lines.index(record)
            # print("Working")

    




class SieveAnalysisLine(models.Model):
    _name = "mechanical.coarse.aggregate.sieve.analysis.line1"
    parent_id = fields.Many2one('mechanical.coarse.aggregate1', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size mm")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained",digits=(16,2))
    cumulative_retained = fields.Float(string="Cum. Retained %", store=True,digits=(16,2))
    passing_percent = fields.Float(string="Passing %",digits=(16,2))



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


    @api.depends('wt_retained', 'parent_id.total_sieve_analysis')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = record.wt_retained / self.parent_id.total_sieve_analysis * 100
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



       


# class LooseBulkDensityLine(models.Model):
#     _name = "coarse.aggregate.loose.bulk.density.line"
#     parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")
   
#     sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    # weight_empty_bucket = fields.Float(string="Weight of Empty Bucket in kg")
    # volume_of_bucket = fields.Float(string="Volume of Bucket in cubic meter")
    # sample_plus_bucket = fields.Float(string="[Sample Weight + Bucket  Weight] in kg")
    # sample_weight = fields.Float(string="Sample Weight in kg",compute="_compute_sample_weight")
    # loose_bulk_density = fields.Float(string="Loose Bulk Density in kg per cubic meter",compute="_compute_loose_bulk_density")


    # @api.depends('sample_plus_bucket', 'weight_empty_bucket')
    # def _compute_sample_weight(self):
    #     for record in self:
    #         record.sample_weight = record.sample_plus_bucket - record.weight_empty_bucket

    

    # @api.depends('sample_weight', 'volume_of_bucket')
    # def _compute_loose_bulk_density(self):
    #     for record in self:
    #         if record.volume_of_bucket:
    #             record.loose_bulk_density = record.sample_weight / record.volume_of_bucket
    #         else:
    #             record.loose_bulk_density = 0.0


    # @api.model
    # def create(self, vals):
    #     # Set the serial_no based on the existing records for the same parent
    #     if vals.get('parent_id'):
    #         existing_records = self.search([('parent_id', '=', vals['parent_id'])])
    #         if existing_records:
    #             max_serial_no = max(existing_records.mapped('sr_no'))
    #             vals['sr_no'] = max_serial_no + 1

    #     return super(LooseBulkDensityLine, self).create(vals)

    # def _reorder_serial_numbers(self):
    #     # Reorder the serial numbers based on the positions of the records in child_lines
    #     records = self.sorted('id')
    #     for index, record in enumerate(records):
    #         record.sr_no = index + 1

class RoddedBulkDensityLine(models.Model):
    _name = "coarse.aggregate.rodded.bulk.density.line1"
    parent_id = fields.Many2one('mechanical.coarse.aggregate1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    weight_empty_bucket = fields.Float(string="Weight of Empty Bucket in kg")
    volume_of_bucket = fields.Float(string="Volume of Bucket in cubic meter")
    sample_plus_bucket = fields.Float(string="[Sample Weight + Bucket  Weight] in kg")
    sample_weight = fields.Float(string="Sample Weight in kg",compute="_compute_sample_weight")
    rodded_bulk_density = fields.Float(string="Rodded Bulk Density in kg per cubic meter",compute="_compute_roddede_bulk_density")


    @api.depends('sample_plus_bucket', 'weight_empty_bucket')
    def _compute_sample_weight(self):
        for record in self:
            record.sample_weight = record.sample_plus_bucket - record.weight_empty_bucket

    

    @api.depends('sample_weight', 'volume_of_bucket')
    def _compute_roddede_bulk_density(self):
        for record in self:
            if record.volume_of_bucket:
                record.rodded_bulk_density = record.sample_weight / record.volume_of_bucket
            else:
                record.rodded_bulk_density = 0.0



    # @api.model
    # def create(self, vals):
    #     # Set the serial_no based on the existing records for the same parent
    #     if vals.get('parent_id'):
    #         existing_records = self.search([('parent_id', '=', vals['parent_id'])])
    #         if existing_records:
    #             max_serial_no = max(existing_records.mapped('sr_no'))
    #             vals['sr_no'] = max_serial_no + 1

    #     return super(RoddedBulkDensityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1

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
    _name = "mechanical.elongation.flakiness.line1"
    parent_id = fields.Many2one('mechanical.coarse.aggregate1', string="Parent Id")

    sieve_size = fields.Char(string="IS Sieve Size")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    elongated_retained = fields.Float(string="Elongated Retained in gms")
    flakiness_retained = fields.Float(string="Flakiness Retained in gms")


class SoundnessNa2Line(models.Model):
    _name = "mechanical.soundness.na2so4.line1"
    parent_id = fields.Many2one('mechanical.coarse.aggregate1', string="Parent Id")
    
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
    _name = "mechanical.soundness.mgso4.line1"
    parent_id = fields.Many2one('mechanical.coarse.aggregate1', string="Parent Id")
    
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



    
class ImpactValueLine(models.Model):
    _name = "mechanical.impact.value.coarse.aggregate.line1"
    parent_id = fields.Many2one('mechanical.coarse.aggregate1',string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)
    wt_of_cylinder = fields.Integer(string="Weight of cylindrical measure in gms")
    total_wt_of_dried = fields.Integer(string="Total Wt. of Oven dried (4 hrs) aggregate sample + cylindrical measure in gms")
    total_wt_aggregate = fields.Float(string="Total Wt. of Oven dried (4 hrs) aggregate sample filling the cylindrical measure in gms", compute="_compute_total_wt_aggregate")
    wt_of_aggregate_passing = fields.Float(string="Wt. of aggregate passing 2.36 mm sieve after the test in gms")
    wt_of_aggregate_retained = fields.Float(string="Wt. of aggregate retained on 2.36 mm sieve after the test in gms", compute="_compute_wt_of_aggregate_retained")
    impact_value = fields.Float(string="Aggregate Impact value", compute="_compute_impact_value")


    @api.depends('total_wt_of_dried', 'wt_of_cylinder')
    def _compute_total_wt_aggregate(self):
        for rec in self:
            rec.total_wt_aggregate = rec.total_wt_of_dried - rec.wt_of_cylinder


    @api.depends('total_wt_aggregate', 'wt_of_aggregate_passing')
    def _compute_wt_of_aggregate_retained(self):
        for rec in self:
            rec.wt_of_aggregate_retained = rec.total_wt_aggregate - rec.wt_of_aggregate_passing


    @api.depends('wt_of_aggregate_passing', 'total_wt_aggregate')
    def _compute_impact_value(self):
        for rec in self:
            if rec.total_wt_aggregate != 0:
                rec.impact_value = (rec.wt_of_aggregate_passing / rec.total_wt_aggregate) * 100
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

        return super(ImpactValueLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


    


class CrushingValueLine(models.Model):
    _name = "mechanical.crushing.value.coarse.aggregate.line1"
    parent_id = fields.Many2one('mechanical.coarse.aggregate1',string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)
    wt_of_cylinder = fields.Integer(string="Weight of the empty cylinder in gms")
    total_wt_of_dried = fields.Integer(string="Total weight of oven dried ( 4.0 hrs ) aggregate sample filling the cylindrical measure in gms")
    total_wt_aggregate = fields.Float(string="Total weight of aggeregate in the cylinder in gms", compute="_compute_total_wt_aggregate")
    wt_of_aggregate_passing = fields.Float(string="Weight of aggregate fines passing 2.36 mm sieve after  the application of Load gms")
    wt_of_aggregate_retained = fields.Float(string="Weight of aggregate retained on 2.36 mm sieve after the test in gms", compute="_compute_wt_of_aggregate_retained")
    crushing_value = fields.Float(string="Aggregate Crushing value", compute="_compute_crushing_value")


    @api.depends('total_wt_of_dried', 'wt_of_cylinder')
    def _compute_total_wt_aggregate(self):
        for rec in self:
            rec.total_wt_aggregate = rec.total_wt_of_dried - rec.wt_of_cylinder


    @api.depends('total_wt_aggregate', 'wt_of_aggregate_passing')
    def _compute_wt_of_aggregate_retained(self):
        for rec in self:
            rec.wt_of_aggregate_retained = rec.total_wt_aggregate - rec.wt_of_aggregate_passing


    @api.depends('wt_of_aggregate_passing', 'total_wt_aggregate')
    def _compute_crushing_value(self):
        for rec in self:
            if rec.total_wt_aggregate != 0:
                rec.crushing_value = (rec.wt_of_aggregate_passing / rec.total_wt_aggregate) * 100
            else:
                rec.crushing_value = 0.0


    # @api.model
    # def create(self, vals):
    #     # Set the serial_no based on the existing records for the same parent
    #     if vals.get('parent_id'):
    #         existing_records = self.search([('parent_id', '=', vals['parent_id'])])
    #         if existing_records:
    #             max_serial_no = max(existing_records.mapped('sample_no'))
    #             vals['sample_no'] = max_serial_no + 1

    #     return super(CrushingValueLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1



# class SpecificGravityAndWaterAbsorptionLine(models.Model):
#     _name = "mechanical.specific.gravity.and.water.absorption.line"
#     parent_id = fields.Many2one('mechanical.coarse.aggregate',string="Parent Id")
   
#     sr_no = fields.Integer(string="Test", readonly=True, copy=False, default=1)
#     wt_surface_dry = fields.Integer(string="Weight of saturated surface dry (SSD) sample in air in gms")
#     wt_sample_inwater = fields.Integer(string="Weight of saturated sample in water in gms")
#     oven_dried_wt = fields.Integer(string="Oven dried weight of sample in gms")
#     specific_gravity = fields.Float(string="Specific Gravity",compute="_compute_specific_gravity")
#     water_absorption = fields.Float(string="Water absorption  %",compute="_compute_water_absorption")


#     @api.depends('wt_surface_dry', 'wt_sample_inwater', 'oven_dried_wt')
#     def _compute_specific_gravity(self):
#         for line in self:
#             if line.wt_surface_dry - line.wt_sample_inwater != 0:
#                 line.specific_gravity = line.oven_dried_wt / (line.wt_surface_dry - line.wt_sample_inwater)
#             else:
#                 line.specific_gravity = 0.0



#     @api.depends('wt_surface_dry', 'oven_dried_wt')
#     def _compute_water_absorption(self):
#         for line in self:
#             if line.oven_dried_wt != 0:
#                 line.water_absorption = ((line.wt_surface_dry - line.oven_dried_wt) / line.oven_dried_wt) * 100
#             else:
#                 line.water_absorption = 0.0



    # @api.model
    # def create(self, vals):
    #     # Set the serial_no based on the existing records for the same parent
    #     if vals.get('parent_id'):
    #         existing_records = self.search([('parent_id', '=', vals['parent_id'])])
    #         if existing_records:
    #             max_serial_no = max(existing_records.mapped('sr_no'))
    #             vals['sr_no'] = max_serial_no + 1

    #     return super(SpecificGravityAndWaterAbsorptionLine, self).create(vals)

    # def _reorder_serial_numbers(self):
    #     # Reorder the serial numbers based on the positions of the records in child_lines
    #     records = self.sorted('id')
    #     for index, record in enumerate(records):
    #         record.sr_no = index + 1





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

