from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class PrecastKerbMechanical(models.Model):
    _name = "mechanical.precast.kerb"
    _inherit = "lerm.eln"
    _rec_name = "name"


    name = fields.Char("Name",default="Precast Kerb Stone")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")





    # remark

    notes_id = fields.One2many('kerb.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(PrecastKerbMechanical, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The report shall not be reproduced in full or partially without written approval of the laboratory HOD/CEO/Maganement.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'Sampling is not done by us unless mentioned otherwide.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'without a QR Code and hologram this report is considered invalid.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'The Result listed refer only to tested samples & applicable parameter Endorsement of product is neither interred nor inplied.',
            }),

            (0, 0, {
                'sr_no': 'e',
                'notes': 'The use or report for arbitration, publicity & evidence in legal dispute is forbidden except with prior written consent NBML Lab.',
            }),
             (0, 0, {
                'sr_no': 'f',
                'notes': 'All disputed are subject to Raipur jurisdiction 7 days correction to this report invalidates this report.',
            }),

             (0, 0, {
                'sr_no': 'g',
                'notes': 'Sample will be destroyed after 30-days from the date of test report unless otherwise Specified.',
            }),
        ]

        res['notes_id'] = default_notes
        return res

       

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

    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

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
        record = self.env['mechanical.precast.kerb'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    # Transverse Strength
    transverse_name = fields.Char(default="Transverse Strength")
    transverse_visible = fields.Boolean(compute="_compute_visible")

    transverse_table = fields.One2many('mech.precast.transverse.line','parent_id')
    

    # Water Absorbtion
    water_absorbtion_name = fields.Char(default="Water Absorbtion")
    water_absorbtion_visible = fields.Boolean(compute="_compute_visible")

    water_absorbtion_table = fields.One2many('mech.precast.water.absorbtion.line','parent_id')


   

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











class kerb(models.Model):
    _name = "kerb.notes"

    parent_id = fields.Many2one('mechanical.precast.kerb',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")






    

    