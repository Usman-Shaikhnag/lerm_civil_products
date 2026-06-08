from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class PrecastKerbMechanical(models.Model):
    _name = "mechanical.precast.kerb"
    _inherit = "lerm.eln"
    _rec_name = "name"


    name = fields.Char("Name",default="Precast Kerb Stone")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
       
    #    Dimension

    dimension_name = fields.Char(default="Dimension")
    dimension_visible = fields.Boolean(compute="_compute_visible")
    length = fields.Float('Length')
    thickness = fields.Float('Thickness')
    width = fields.Float('Width')

    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.transverse_visible = False
            record.water_absorbtion_visible  = False  
            record.dimension_visible  = False

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '0b48abe6-07a4-4345-bcc1-30ff6e4830af':
                    record.transverse_visible = True
                if sample.internal_id == 'f913fc79-eeb4-4e16-a7fc-75608384d9b0':
                    record.water_absorbtion_visible = True
                if sample.internal_id == 'klrt1230t-eeb4-4e16-a7fc-7560838410lo':
                    record.dimension_visible = True

    # def open_eln_page(self):
        # import wdb; wdb.set_trace()




    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
          
            
            if result.parameter.internal_id == '0b48abe6-07a4-4345-bcc1-30ff6e4830af':
                # result.result_char = round(self.average_density,2)
                result.calculated = True
                # if self.average_density_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue

            if result.parameter.internal_id == 'f913fc79-eeb4-4e16-a7fc-75608384d9b0':
                # result.result_char = round(self.average_density,2)
                result.calculated = True
                # if self.average_density_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue


            if result.parameter.internal_id == 'klrt1230t-eeb4-4e16-a7fc-7560838410lo':
                # result.result_char = round(self.average_density,2)
                result.calculated = True
                # if self.average_density_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue



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
        record = super(PrecastKerbMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    def get_all_fields(self):
        record = self.env['mechanical.precast.kerb'].browse(self.ids[0])
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
    transverse_name = fields.Char(default="Transverse Strength")
    transverse_visible = fields.Boolean(compute="_compute_visible")

    transverse_table = fields.One2many('mech.precast.transverse.line','parent_id')
    

    # Water Absorbtion
    water_absorbtion_name = fields.Char(default="Water Absorbtion")
    water_absorbtion_visible = fields.Boolean(compute="_compute_visible")

    water_absorbtion_table = fields.One2many('mech.precast.water.absorbtion.line','parent_id')


    notes_id = fields.One2many('mechanical.precast.kerb.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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


   

class PrecastTransverseLine(models.Model):
    _name = "mech.precast.transverse.line"
    parent_id = fields.Many2one('mechanical.precast.kerb', string="Parent Id")

    trial_no = fields.Integer('Trial no')
    required_load = fields.Float('Required Load in (Ton)')
    observed_test_result = fields.Char('Observed Test Result')
    protocol = fields.Char('Protocol')
    requirement = fields.Char('Requirement')


class PrecastWaterAbsorbtionLine(models.Model):
    _name = "mech.precast.water.absorbtion.line"
    parent_id = fields.Many2one('mechanical.precast.kerb', string="Parent Id")

    dry_wt_oven = fields.Float('Dry Weight (after 24 hour in oven)')
    wt_10_min = fields.Float('Weight (wt. after 10 minutes emersion in water)')
    wt_24_hr = fields.Float('Weight (wt. after 24 hour emersion in water)')
    initial_water_absorbtion = fields.Float("Initial Water Absorption, %")
    final_water_absorbtion = fields.Float("Final Water Absorption, %")
    protocol = fields.Char('Protocol')





    

    
class PrecastKerbMechanicalNotes(models.Model):
    _name = "mechanical.precast.kerb.notes"

    parent_id = fields.Many2one('mechanical.precast.kerb', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
