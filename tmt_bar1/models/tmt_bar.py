from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re

class TMTBAR(models.Model):
    _name = "mech.tmt.bar"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="TMT BAR")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    
    
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    temperature = fields.Float("Temperature °C")
    
   
    eln_ref = fields.Many2one('lerm.eln',string="Eln")


    mechanical_test_visible = fields.Boolean("Stainless Steel Visible",compute="_compute_visible")
    mechanical_test_name = fields.Char("Name",default="Mechanical Test")

    section_weight_visible = fields.Boolean("Stainless Steel Visible",compute="_compute_visible")
    section_weight_name = fields.Char("Name",default="Section Weight")

    section_weight_lines = fields.One2many('mech.section.line','parent_id',string="Parameter")



    chemical_test_visible = fields.Boolean("Stainless Steel Visible",compute="_compute_visible")
    chemical_test_name = fields.Char("Name",default="Section Weight")

    chemical_test_lines = fields.One2many('chemical.test.line','parent_id',string="Parameter")


   

    notes_id = fields.One2many('mech.tmt.bar.notes', 'parent_id', string="Notes")

    child_lines = fields.One2many('mech.tmt.bar.line','parent_id',string="Parameter")



    @api.model
    def default_get(self, fields):
        res = super(TMTBAR, self).default_get(fields)

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

            if result.parameter.internal_id == '9874562-c893-4991-a463-650b73987546':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
                # if self.avg_compaction_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '7da2578-4027-4d73-955e-ca7f7a2214578':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue


            if result.parameter.internal_id == '7d78548-4027-4d73-955e-ca7f7a22121458':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue

            if result.parameter.internal_id == '3214748-4027-4d73-955e-ca7f7a22122145':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue
            
            if result.parameter.internal_id == '3322148-4027-4d73-955e-ca7f7a22155447':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue
            
            if result.parameter.internal_id == '332214548-4027-4d73-955e-ca7f7a22155447':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue

            if result.parameter.internal_id == '99977854548-4027-4d73-955e-ca7f7a22122114':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue

            if result.parameter.internal_id == '3213245-4027-4d73-955e-ca7f7a22121457':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue

            if result.parameter.internal_id == '6547562-c893-4991-a463-650b73552147':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue

            if result.parameter.internal_id == '6662147-c893-4991-a463-650b73662145':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
              
                continue

            # chemical

            if result.parameter.internal_id == '66221447-c893-4991-a463-650b736666214':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
            
            if result.parameter.internal_id == '331241447-c893-4991-a463-650b7666214578':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
            
            if result.parameter.internal_id == '6614741447-c893-4991-a463-650b7661110047852':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
            
            if result.parameter.internal_id == '99978741447-c893-4991-a463-650b7661111478':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
            
            if result.parameter.internal_id == '22ffff41447-c893-4991-a463-650b7661999785':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True
            
            if result.parameter.internal_id == '99987241447-c893-4991-a463-650b76619996214':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True

            if result.parameter.internal_id == '999899958447-c893-4991-a463-650b76619889547':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True

            if result.parameter.internal_id == '9958447-c893-4991-a463-650b766199978541':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True

            if result.parameter.internal_id == '7777t447-c893-4991-a463-650b766155558777':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True

            
            if result.parameter.internal_id == '9978541447-c893-4991-a463-650b7661110099587':
                # result.result_char = round(self.average_mpa,2)
                result.calculated = True

           

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
        record = super(TMTBAR, self).create(vals)
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
        record = self.env['mech.tmt.bar'].browse(self.ids[0])
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
            record.mechanical_test_visible = False
            record.section_weight_visible = False
            record.chemical_test_visible = False


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == '9874562-c893-4991-a463-650b73987546':
                    record.mechanical_test_visible = True

                if sample.internal_id == '6547562-c893-4991-a463-650b73552147':
                    record.section_weight_visible = True

                if sample.internal_id == '6662147-c893-4991-a463-650b73662145':
                    record.chemical_test_visible = True

                


class TMTBARLine(models.Model):
    _name = "mech.tmt.bar.line"
    parent_id = fields.Many2one('mech.tmt.bar',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample_identity = fields.Char(string="Sample  Identity")
   
    # f10 = fields.Integer(string="10")
    uts = fields.Float(string="UTS (MPa)")

    proof_stress = fields.Float(string="0.2 % Proof Stress N/mm2")
    elongation = fields.Float(string="% Elongation On 5.65 √Area")
    total_elongation = fields.Float(string="% Total Elongation")
    ratio_uts_ys = fields.Float(string="Ratio of UTS/YS")

    
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

    re_bend = fields.Selection(
        [
            ('ok_3', 'OK (3Ø)'),
            ('ok_4', 'OK (4Ø)'),
            ('ok_5', 'OK (5Ø)'),
            ('ok_6', 'OK (6Ø)'),
            ('not_ok', 'NOT OK')
        ],
        string="Re-Bend Test"
    )


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(TMTBARLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class SectionWeightLine(models.Model):
    _name = "mech.section.line"
    parent_id = fields.Many2one('mech.tmt.bar',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample_identity = fields.Char(string="Sample  Identity")
   
    # f10 = fields.Integer(string="10")
    weight = fields.Float(string="Weight (Kg)")

    lenght = fields.Float(string="Length(mm)")
    unit_weight = fields.Float(string="Unit Weight Kg/meter")
    standard_weight = fields.Float(string="Standard Weight  as per IS 1786-2008")
    tolerance = fields.Char(string="Tolerance on the Nominal Mass, Percent Batch")

    
  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SectionWeightLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class ChemicalLine(models.Model):
    _name = "chemical.test.line"
    parent_id = fields.Many2one('mech.tmt.bar',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample_identity = fields.Char(string="Sample  Identity")
   
    # f10 = fields.Integer(string="10")
    c = fields.Float(string="C%")

    p = fields.Float(string="P%")
    s = fields.Float(string="S%")
    si = fields.Float(string="Si%")
    cr = fields.Float(string="Cr%")
    cu = fields.Float(string="Cu%")
    mo = fields.Float(string="Mo%")
    ni = fields.Float(string="Ni%")
    mn = fields.Float(string="Mn%")


    p_s = fields.Float(string="P + S", compute="_compute_p_s", store=True)

    @api.depends('p', 's')
    def _compute_p_s(self):
        for rec in self:
            rec.p_s = (rec.p or 0.0) + (rec.s or 0.0)

    
  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ChemicalLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1
   
   
                


class TMTBARNotes(models.Model):
    _name = "mech.tmt.bar.notes"

    parent_id = fields.Many2one('mech.tmt.bar',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")