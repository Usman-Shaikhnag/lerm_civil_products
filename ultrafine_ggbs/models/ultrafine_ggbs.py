from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class UltrafineGgbsMechanical(models.Model):
    _name = "mechanical.ultrafine.ggbs"
    _inherit = "lerm.eln"
    _rec_name = "name"


    name = fields.Char("Name",default="ULTRAFINE GGBS")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.ultrafine.ggbs.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)


    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    notes_id = fields.One2many('mechanical.ultrafine.ggbs.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(UltrafineGgbsMechanical, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The information marked with an # received from customer',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'The results listed refer only to tested parameters and sample as received from customer',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'The balance samples if any will be discarded after 15 days from the date of issue of test certificate unless otherwise specified.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'This document shall not be reproduced in part or full without the approval of Knack.',
            }),
        ]

        res['notes_id'] = default_notes
        return res


    # Normal Consistency
    normal_consistency_name = fields.Char("Name",default="Normal Consistency")
    normal_consistency_visible = fields.Boolean("Normal Consistency Visible",compute="_compute_visible")

    temp_percent_normal = fields.Float("Temperature °C")
    humidity_percent_normal = fields.Float("Humidity %")


    wt_of_cement_trial1 = fields.Float("Wt. of Cement(g)",default=200)
    wt_of_ggbs_trial1 = fields.Float("Wt. of UGGBS (g)",default=200)
    total_wt_sample = fields.Float("Total Wt. of Sample (g)",compute="_compute_total_wt_sample",store=True)
    wt_water_req = fields.Float("Wt. of water required")
    penetration_vicat = fields.Float("Penetration of vicat's Plunger(mm)")
    normal_consistency = fields.Float("Normal Consistency",compute="_compute_normal_consistency",store=True)

    @api.depends('wt_of_cement_trial1','wt_of_ggbs_trial1')
    def _compute_total_wt_sample(self):
        for record in self:
            record.total_wt_sample = record.wt_of_cement_trial1 + record.wt_of_ggbs_trial1

    @api.depends('wt_water_req','total_wt_sample')
    def _compute_normal_consistency(self):
        for record in self:
            if record.total_wt_sample != 0:
                record.normal_consistency = (record.wt_water_req / record.total_wt_sample ) *100

    normal_consistency_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')], string="Conformity", compute="_compute_normal_consistency_conformity", store=True)

    @api.depends('normal_consistency','eln_ref','grade')
    def _compute_normal_consistency_conformity(self):
        
        for record in self:
            record.normal_consistency_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fd51208d-6e49-4cf2-aa79-4c0afc6fce64')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fd51208d-6e49-4cf2-aa79-4c0afc6fce64')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.normal_consistency_conformity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.normal_consistency - record.normal_consistency*mu_value
                    upper = record.normal_consistency + record.normal_consistency*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.normal_consistency_conformity = 'pass'
                        break
                    else:
                        record.normal_consistency_conformity = 'fail'

    normal_consistency_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_normal_consistency_nabl", store=True)
    
    @api.depends('normal_consistency','eln_ref','grade')
    def _compute_normal_consistency_nabl(self):
        
        for record in self:
            record.normal_consistency_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fd51208d-6e49-4cf2-aa79-4c0afc6fce64')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fd51208d-6e49-4cf2-aa79-4c0afc6fce64')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.normal_consistency - record.normal_consistency*mu_value
            upper = record.normal_consistency + record.normal_consistency*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.normal_consistency_nabl = 'pass'
                break
            else:
                record.normal_consistency_nabl = 'fail'



    # Setting Time
    setting_time_name = fields.Char("Name",default="Setting Time")
    setting_time_visible = fields.Boolean("Setting Time Visible",compute="_compute_visible")

    temp_setting_time = fields.Float("Temperature °C")
    humidity_setting_time = fields.Float("Humidity %")
    
    blend_sample_weight = fields.Float(string='Wt. of Blend Sample (g)',default=400.0)

    st_normal_consistency = fields.Float(string='Normal Consistency of Blend (%)')

    # Calculated
    water_required = fields.Float(string='Wt. of water required (g) (0.85 * P %)',compute='_compute_water_required',store=True,digits=(16, 2)
    )

    # Times
    water_added_time = fields.Datetime(string='Time When water is added to sample (t1)' )

    initial_setting_time_input = fields.Datetime(string='Time when needle fails to penetrate 5±0.5mm (t2)')

    final_setting_time_input = fields.Datetime(string='Time when needle fails to make an impression (t3)')

    # Calculated setting times
    initial_setting_minutes = fields.Float(string='Initial Setting Time (Minutes)',compute='_compute_setting_times',store=True,digits=(16, 0)
    )

    final_setting_minutes = fields.Float(string='Final Setting Time (Minutes)',compute='_compute_setting_times',store=True,digits=(16, 0))

    @api.depends('blend_sample_weight','st_normal_consistency')
    def _compute_water_required(self):
        for record in self:
            record.water_required = (record.blend_sample_weight* 0.85* record.st_normal_consistency/ 100 )

    @api.depends('water_added_time','initial_setting_time_input','final_setting_time_input')
    def _compute_setting_times(self):
        for record in self:

            # Initial setting time
            if (record.water_added_time and record.initial_setting_time_input):
                difference = (record.initial_setting_time_input- record.water_added_time)

                record.initial_setting_minutes = (difference.total_seconds() / 60)
            else:
                record.initial_setting_minutes = 0

            # Final setting time
            if (record.water_added_time and record.final_setting_time_input):
                difference = (record.final_setting_time_input- record.water_added_time)

                record.final_setting_minutes = (difference.total_seconds() / 60)
            else:
                record.final_setting_minutes = 0


    initial_setting_minutes_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')], string="Conformity", compute="_compute_initial_setting_minutes_conformity", store=True)

    @api.depends('initial_setting_minutes','eln_ref','grade')
    def _compute_initial_setting_minutes_conformity(self):
        
        for record in self:
            record.initial_setting_minutes_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','795f0c38-2e3c-4f6b-a015-9572c07bcdf1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','795f0c38-2e3c-4f6b-a015-9572c07bcdf1')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.initial_setting_minutes_conformity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.initial_setting_minutes - record.initial_setting_minutes*mu_value
                    upper = record.initial_setting_minutes + record.initial_setting_minutes*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.initial_setting_minutes_conformity = 'pass'
                        break
                    else:
                        record.initial_setting_minutes_conformity = 'fail'

    initial_setting_minutes_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_initial_setting_minutes_nabl", store=True)
    
    @api.depends('initial_setting_minutes','eln_ref','grade')
    def _compute_initial_setting_minutes_nabl(self):
        
        for record in self:
            record.initial_setting_minutes_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','795f0c38-2e3c-4f6b-a015-9572c07bcdf1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','795f0c38-2e3c-4f6b-a015-9572c07bcdf1')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.initial_setting_minutes - record.initial_setting_minutes*mu_value
            upper = record.initial_setting_minutes + record.initial_setting_minutes*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.initial_setting_minutes_nabl = 'pass'
                break
            else:
                record.initial_setting_minutes_nabl = 'fail'



    final_setting_minutes_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')], string="Conformity", compute="_compute_final_setting_minutes_conformity", store=True)

    @api.depends('final_setting_minutes','eln_ref','grade')
    def _compute_final_setting_minutes_conformity(self):
        
        for record in self:
            record.final_setting_minutes_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c5e1bbce-de81-40d7-ae57-680133cf51f0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c5e1bbce-de81-40d7-ae57-680133cf51f0')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.final_setting_minutes_conformity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.final_setting_minutes - record.final_setting_minutes*mu_value
                    upper = record.final_setting_minutes + record.final_setting_minutes*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.final_setting_minutes_conformity = 'pass'
                        break
                    else:
                        record.final_setting_minutes_conformity = 'fail'

    final_setting_minutes_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_final_setting_minutes_nabl", store=True)
    
    @api.depends('final_setting_minutes','eln_ref','grade')
    def _compute_final_setting_minutes_nabl(self):
        
        for record in self:
            record.final_setting_minutes_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c5e1bbce-de81-40d7-ae57-680133cf51f0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c5e1bbce-de81-40d7-ae57-680133cf51f0')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.final_setting_minutes - record.final_setting_minutes*mu_value
            upper = record.final_setting_minutes + record.final_setting_minutes*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.final_setting_minutes_nabl = 'pass'
                break
            else:
                record.final_setting_minutes_nabl = 'fail'




    # Specific Gravity

    specific_gravity_name = fields.Char("Name",default="Specific Gravity")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    temp_specific_gravity = fields.Float("Temperature °C")
    humidity_specific_gravity = fields.Float("Humidity %")

    wt_of_ggbs_sg_trial1 = fields.Float("Weight of UGGBS Sample (g)")
    
    initial_volume_kerosine_trial1 = fields.Float("Initial Volume of Kerosine (ml) V1")
    
    final_volume_kerosine_trial1 = fields.Float("Final Volume of Kerosine + Sample (ml) V2")
    
    displaced_volume_trial1 = fields.Float("Displaced Volume of Sample (cm³)")
    
    specific_gravity_trial1 = fields.Float("Specific Gravity",compute="_compute_specific_gravity_trail1",store=True)
    
    # average_specific_gravity = fields.Float("Average",compute="_compute_sg_average",store=True)
    

    # @api.depends('initial_volume_kerosine_trial1','final_volume_kerosine_trial1')
    # def _compute_displaced_volume_trail1(self):
    #     for record in self:
    #         record.displaced_volume_trial1 = record.final_volume_kerosine_trial1 - record.initial_volume_kerosine_trial1


    @api.depends('wt_of_ggbs_sg_trial1','displaced_volume_trial1')
    def _compute_specific_gravity_trail1(self):
        for record in self:
            if record.displaced_volume_trial1 != 0:
                specific_gravity_trial1 = record.wt_of_ggbs_sg_trial1 / record.displaced_volume_trial1
                record.specific_gravity_trial1 = round(specific_gravity_trial1,2)


    # @api.depends('specific_gravity_trial1','specific_gravity_trial2')
    # def _compute_sg_average(self):
    #     for record in self:
    #         average_specific_gravity = (record.specific_gravity_trial1 + record.specific_gravity_trial2)/2
    #         record.average_specific_gravity = round(average_specific_gravity,2)

    
    specific_gravity_trial1_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')], string="Conformity", compute="_compute_specific_gravity_trial1_conformity", store=True)

    @api.depends('specific_gravity_trial1','eln_ref','grade')
    def _compute_specific_gravity_trial1_conformity(self):
        
        for record in self:
            record.specific_gravity_trial1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','962865c0-6609-4382-ac31-6286dc9b4c5a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','962865c0-6609-4382-ac31-6286dc9b4c5a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.specific_gravity_trial1_conformity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.specific_gravity_trial1 - record.specific_gravity_trial1*mu_value
                    upper = record.specific_gravity_trial1 + record.specific_gravity_trial1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.specific_gravity_trial1_conformity = 'pass'
                        break
                    else:
                        record.specific_gravity_trial1_conformity = 'fail'

    specific_gravity_trial1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_specific_gravity_trial1_nabl", store=True)
    
    @api.depends('specific_gravity_trial1','eln_ref','grade')
    def _compute_specific_gravity_trial1_nabl(self):
        
        for record in self:
            record.specific_gravity_trial1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','962865c0-6609-4382-ac31-6286dc9b4c5a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','962865c0-6609-4382-ac31-6286dc9b4c5a')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.specific_gravity_trial1 - record.specific_gravity_trial1*mu_value
            upper = record.specific_gravity_trial1 + record.specific_gravity_trial1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.specific_gravity_trial1_nabl = 'pass'
                break
            else:
                record.specific_gravity_trial1_nabl = 'fail'
    

    

    

    ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        

        for record in self:
            record.normal_consistency_visible = False
            record.setting_time_visible = False
            record.specific_gravity_visible = False
            
            
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == 'fd51208d-6e49-4cf2-aa79-4c0afc6fce64':
                    record.normal_consistency_visible = True

                if sample.internal_id == '795f0c38-2e3c-4f6b-a015-9572c07bcdf1':
                    record.setting_time_visible = True

                if sample.internal_id == 'c5e1bbce-de81-40d7-ae57-680133cf51f0':
                    record.setting_time_visible = True

                if sample.internal_id == '962865c0-6609-4382-ac31-6286dc9b4c5a':
                    record.specific_gravity_visible = True

                


    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:

            # Normal Consistency
            if result.parameter.internal_id == 'fd51208d-6e49-4cf2-aa79-4c0afc6fce64':
                result.result_char = round(self.normal_consistency,2)
                result.calculated = True
                if self.normal_consistency_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Initial Setting Time
            if result.parameter.internal_id == '795f0c38-2e3c-4f6b-a015-9572c07bcdf1':
                result.result_char = round(self.initial_setting_minutes,2)
                result.calculated = True
                if self.initial_setting_minutes_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Final Setting Time
            if result.parameter.internal_id == 'c5e1bbce-de81-40d7-ae57-680133cf51f0':
                result.result_char = round(self.final_setting_minutes,2)
                result.calculated = True
                if self.final_setting_minutes_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Specific Gravity
            if result.parameter.internal_id == '962865c0-6609-4382-ac31-6286dc9b4c5a':
                result.result_char = round(self.specific_gravity_trial1,2)
                result.calculated = True
                if self.specific_gravity_trial1_nabl == 'pass':
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
        record = super(UltrafineGgbsMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

        
    def get_all_fields(self):
        record = self.env['mechanical.ultrafine.ggbs'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values




class UltrafineFlyashNotes(models.Model):
    _name = "mechanical.ultrafine.ggbs.notes"

    parent_id = fields.Many2one('mechanical.ultrafine.ggbs',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")


