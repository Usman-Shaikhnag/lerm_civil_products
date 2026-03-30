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

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['mechanical.precast.kerb'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

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





    

    