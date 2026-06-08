from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
from math import pi


class MechanicalRock(models.Model):
    _name = "mechanical.rock"
    _inherit = "lerm.eln"
    _rec_name = "name_rock"

    name_rock = fields.Char("Name",default="ROCK")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id


    # Specific Gravity
    specific_gravity_name = fields.Char("Name",default="Specific Gravity")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    # SAMPLE 1
    sample1_dry = fields.Float(string="Dry Weight (g)")
    sample1_wet = fields.Float(string="Wet/Saturated Weight (g)")
    sample1_suspended = fields.Float(string="Suspended Weight (g)")
    sample1_result = fields.Float(
        string="Specific Gravity",
        compute="_compute_results",
        store=True
    )

    # SAMPLE 2
    sample2_dry = fields.Float(string="Dry Weight (g)")
    sample2_wet = fields.Float(string="Wet/Saturated Weight (g)")
    sample2_suspended = fields.Float(string="Suspended Weight (g)")
    sample2_result = fields.Float(
        string="Specific Gravity",
        compute="_compute_results",
        store=True
    )

    # SAMPLE 3
    sample3_dry = fields.Float(string="Dry Weight (g)")
    sample3_wet = fields.Float(string="Wet/Saturated Weight (g)")
    sample3_suspended = fields.Float(string="Suspended Weight (g)")
    sample3_result = fields.Float(
        string="Specific Gravity",
        compute="_compute_results",
        store=True
    )

    avg_specific_gravity = fields.Float(
        string="Average Specific Gravity",
        compute="_compute_results",
        store=True
    )

    @api.depends(
        'sample1_dry', 'sample1_wet', 'sample1_suspended',
        'sample2_dry', 'sample2_wet', 'sample2_suspended',
        'sample3_dry', 'sample3_wet', 'sample3_suspended'
    )
    def _compute_results(self):

        for rec in self:

            # SAMPLE 1
            den1 = rec.sample1_wet - rec.sample1_suspended
            rec.sample1_result = (
                rec.sample1_dry / den1
                if den1 > 0 else 0.0
            )

            # SAMPLE 2
            den2 = rec.sample2_wet - rec.sample2_suspended
            rec.sample2_result = (
                rec.sample2_dry / den2
                if den2 > 0 else 0.0
            )

            # SAMPLE 3
            den3 = rec.sample3_wet - rec.sample3_suspended
            rec.sample3_result = (
                rec.sample3_dry / den3
                if den3 > 0 else 0.0
            )

            results = [
                r for r in [
                    rec.sample1_result,
                    rec.sample2_result,
                    rec.sample3_result
                ] if r > 0
            ]

            rec.avg_specific_gravity = (
                sum(results) / len(results)
                if results else 0.0
            )


    avg_specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_specific_gravity_conformity", store=True)

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_specific_gravity_conformity = 'na'
                continue
            record.avg_specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf5d3d97-9a52-4242-9a36-2e40e5fc8247')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf5d3d97-9a52-4242-9a36-2e40e5fc8247')]).parameter_table
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
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_specific_gravity_nabl", store=True)

    @api.depends('avg_specific_gravity','eln_ref')
    def _compute_avg_specific_gravity_nabl(self):
        
        for record in self:
            record.avg_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf5d3d97-9a52-4242-9a36-2e40e5fc8247')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf5d3d97-9a52-4242-9a36-2e40e5fc8247')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
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


    # Water Absorption
    water_absorption_name = fields.Char("Name",default="Water Absorption")
    water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")

    # SAMPLE 1
    water_sample1_dry = fields.Float(string="Dry Weight (g)")
    water_sample1_wet = fields.Float(string="Saturated Weight (g)")
    water_sample1_result = fields.Float(
        string="Water Absorption",
        compute="_compute_resultss",
        store=True
    )

    # SAMPLE 2
    water_sample2_dry = fields.Float(string="Dry Weight (g)")
    water_sample2_wet = fields.Float(string="Saturated Weight (g)")
    water_sample2_result = fields.Float(
        string="Water Absorption",
        compute="_compute_resultss",
        store=True
    )

    # SAMPLE 3
    water_sample3_dry = fields.Float(string="Dry Weight (g)")
    water_sample3_wet = fields.Float(string="Saturated Weight (g)")
    water_sample3_result = fields.Float(
        string="Water Absorption",
        compute="_compute_resultss",
        store=True
    )

    avg_water_absorption = fields.Float(
        string="Average Water Absorption",
        compute="_compute_resultss",
        store=True
    )

    @api.depends(
        'water_sample1_dry', 'water_sample1_wet',
        'water_sample2_dry', 'water_sample2_wet',
        'water_sample3_dry', 'water_sample3_wet'
    )
    def _compute_resultss(self):

        for rec in self:

            # SAMPLE 1
            rec.water_sample1_result = (
                ((rec.water_sample1_wet - rec.water_sample1_dry) / rec.water_sample1_dry) * 100
                if rec.water_sample1_dry > 0 else 0.0
            )

            # SAMPLE 2
            rec.water_sample2_result = (
                ((rec.water_sample2_wet - rec.water_sample2_dry) / rec.water_sample2_dry) * 100
                if rec.water_sample2_dry > 0 else 0.0
            )

            # SAMPLE 3
            rec.water_sample3_result = (
                ((rec.water_sample3_wet - rec.water_sample3_dry) / rec.water_sample3_dry) * 100
                if rec.water_sample3_dry > 0 else 0.0
            )

            results = [
                r for r in [
                    rec.water_sample1_result,
                    rec.water_sample2_result,
                    rec.water_sample3_result
                ] if r > 0
            ]

            rec.avg_water_absorption = (
                sum(results) / len(results)
                if results else 0.0
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-89d87312f3d6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-89d87312f3d6')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-89d87312f3d6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-89d87312f3d6')]).parameter_table
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

    # Water Content

    water_content_name = fields.Char("Name",default="Water Content")
    water_content_visible = fields.Boolean("Water Content Visible",compute="_compute_visible")

    # SAMPLE 1
    water_content_sample1_wet = fields.Float(string="Wet Weight (g)")
    water_content_sample1_dry = fields.Float(string="Dry Weight (g)")
    water_content_sample1_result = fields.Float(
    string="Water Content",
    compute="_compute_water_content",
    store=True
)

    # SAMPLE 2
    water_content_sample2_wet = fields.Float(string="Wet Weight (g)")
    water_content_sample2_dry = fields.Float(string="Dry Weight (g)")
    water_content_sample2_result = fields.Float(
    string="Water Content",
    compute="_compute_water_content",
    store=True
)

    # SAMPLE 3
    water_content_sample3_wet = fields.Float(string="Wet Weight (g)")
    water_content_sample3_dry = fields.Float(string="Dry Weight (g)")
    water_content_sample3_result = fields.Float(
    string="Water Content",
    compute="_compute_water_content",
    store=True)

    avg_water_content = fields.Float(
    string="Average Water Content",
    compute="_compute_water_content",
    store=True)

    @api.depends(
    'water_content_sample1_wet', 'water_content_sample1_dry',
    'water_content_sample2_wet', 'water_content_sample2_dry',
    'water_content_sample3_wet', 'water_content_sample3_dry')
    def _compute_water_content(self):

     for rec in self:

        # SAMPLE 1
        rec.water_content_sample1_result = (
            ((rec.water_content_sample1_wet - rec.water_content_sample1_dry)
             / rec.water_content_sample1_dry) * 100
            if rec.water_content_sample1_dry > 0 else 0.0
        )

        # SAMPLE 2
        rec.water_content_sample2_result = (
            ((rec.water_content_sample2_wet - rec.water_content_sample2_dry)
             / rec.water_content_sample2_dry) * 100
            if rec.water_content_sample2_dry > 0 else 0.0
        )

        # SAMPLE 3
        rec.water_content_sample3_result = (
            ((rec.water_content_sample3_wet - rec.water_content_sample3_dry)
             / rec.water_content_sample3_dry) * 100
            if rec.water_content_sample3_dry > 0 else 0.0
        )

        results = [
            r for r in [
                rec.water_content_sample1_result,
                rec.water_content_sample2_result,
                rec.water_content_sample3_result
            ] if r > 0
        ]

        rec.avg_water_content = (
            sum(results) / len(results)
            if results else 0.0
        )

    avg_water_content_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_water_content_conformity", store=True)

    @api.depends('avg_water_content','eln_ref','grade')
    def _compute_avg_water_content_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_water_content_conformity = 'na'
                continue
            record.avg_water_content_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_water_content - record.avg_water_content*mu_value
                    upper = record.avg_water_content + record.avg_water_content*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_water_content_conformity = 'pass'
                        break
                    else:
                        record.avg_water_content_conformity = 'fail'

    avg_water_content_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_water_content_nabl", store=True)

    @api.depends('avg_water_content','eln_ref','grade')
    def _compute_avg_water_content_nabl(self):
        
        for record in self:
            record.avg_water_content_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_water_content - record.avg_water_content*mu_value
            upper = record.avg_water_content + record.avg_water_content*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_water_content_nabl = 'pass'
                break
            else:
                record.avg_water_content_nabl = 'fail'
    
    

   
    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.specific_gravity_visible = False
            record.water_absorption_visible = False
            record.water_content_visible = False


            

          
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)


                if sample.internal_id == "bf5d3d97-9a52-4242-9a36-2e40e5fc8247":
                    record.specific_gravity_visible = True

                if sample.internal_id == "71e24ae1-b9a9-41cb-86a5-89d87312f3d6":
                    record.water_absorption_visible = True

                if sample.internal_id == "a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d":
                    record.water_content_visible = True

                
                

                
                
              
               

                
    
   
            
           

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()
            
            
            
            # Specific Gravity
            if result.parameter.internal_id == 'bf5d3d97-9a52-4242-9a36-2e40e5fc8247':
                result.calculated = True
                result.result_char = round(self.avg_specific_gravity,2)
                if self.avg_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Water Absorption
            if result.parameter.internal_id == '71e24ae1-b9a9-41cb-86a5-89d87312f3d6':
                result.result_char = round(self.avg_water_absorption,2)
                result.calculated = True
                if self.avg_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue



            # Water Content
            if result.parameter.internal_id == 'a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d':
                result.result_char = round(self.avg_water_content,2)
                result.calculated = True
                if self.avg_water_content_nabl == 'pass':
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
        record = super(MechanicalRock, self).create(vals)
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
        record = self.env['mechanical.rock'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    notes_id = fields.One2many('mechanical.rock.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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






class MechanicalRockNotes(models.Model):
    _name = "mechanical.rock.notes"

    parent_id = fields.Many2one('mechanical.rock', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
