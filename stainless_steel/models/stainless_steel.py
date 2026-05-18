from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re

class StatinlessSteel(models.Model):
    _name = "stainless.steel"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Stainless Steel")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    
    stainless_steel_visible = fields.Boolean("Stainless Steel Visible",compute="_compute_visible")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    temperature = fields.Float("Temperature °C")
    humidity = fields.Float("Humidity  %")
    child_lines = fields.One2many('stainless.steel.line','parent_id',string="Parameter")
   
    eln_ref = fields.Many2one('lerm.eln',string="Eln")

    blanck_lable = fields.Char("Blank Lable Name")


    requirement1 = fields.Char("Specification Yield Stress <20")
    requirement2 = fields.Char("Specification Yield Stress 20-40")
    requirement3 = fields.Char("Specification Yield Stress >40")

    

    notes_id = fields.One2many('stainless.steel.notes', 'parent_id', string="Notes")



    @api.model
    def default_get(self, fields):
        res = super(StatinlessSteel, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The report shall not be reproduced in fullor partially without written approval of the laboratory HOD/CEO/Maganement.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'ampling is not done by us unless mentioned otherwide.',
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
                'notes': 'Alldisputed are subject to Raipur jurisdiction 7 days correction to this report invalidates this report.',
            }),

             (0, 0, {
                'sr_no': 'g',
                'notes': 'Sample willbe destroyed after 30-days from the date of test report unless otherwise Specified.',
            }),
        ]

        res['notes_id'] = default_notes
        return res


   

 


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

        

            # if result.parameter.internal_id == '124578874gtre-372f-4775-9bcb-e999987hy':
            #     # result.result_char = self.avg_specific_gravity
            #     result.calculated = True

            if result.parameter.internal_id == '214578ty-c893-4991-a463-650b73268879':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
                # if self.avg_compaction_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '6987541-0268-46ef-ba88-9c045321055578':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
                # if self.avg_compaction_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '1023457-788-46ef-ba88-9c0453232147855':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
                # if self.avg_compaction_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '10238877-0268-46ef-ba88-9c0453210l69668755':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
                # if self.avg_compaction_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
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
        record = super(StatinlessSteel, self).create(vals)
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
        record = self.env['stainless.steel'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    # added
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


   

    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.stainless_steel_visible = False


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == '214578ty-c893-4991-a463-650b73268879':
                    record.stainless_steel_visible = True

                


class StainlessSteelLine(models.Model):
    _name = "stainless.steel.line"
    parent_id = fields.Many2one('stainless.steel',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample_identity = fields.Char(string="Sample  Identity")
    blank = fields.Char(string="")
   
    # f10 = fields.Integer(string="10")
    uts = fields.Float(string="UTS (MPa)")
    yield_sterss = fields.Float(string="Yield Stress (MPa)")
    elongation = fields.Float(string="% Elongation On 5.65 √Area")
    bend = fields.Selection(
        [
            ('ok_3', 'OK (3Ø)'),
            ('ok_4', 'OK (4Ø)'),
            ('ok_5', 'OK (5Ø)'),
            ('ok_6', 'OK (6Ø)'),
            ('not_ok', 'NOT OK')
        ],
        string="Bend Test 180° 2t"
    )


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(StainlessSteelLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1
   
                


class StatinlessSteelNotes(models.Model):
    _name = "stainless.steel.notes"

    parent_id = fields.Many2one('stainless.steel',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")