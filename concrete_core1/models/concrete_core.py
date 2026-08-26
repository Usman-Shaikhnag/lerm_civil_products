from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math
from decimal import Decimal
import matplotlib.pyplot as plt
import io
import base64
import re

class ConcreteCoreMechanical(models.Model):
    _name = "mechanical.concrete.core1"
    _inherit = "lerm.eln"
    _rec_name = "name"



    name = fields.Char("Name",default="Core Cutter")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    temprature = fields.Float("Temperature (°C)", digits=(10,2))
    humidity = fields.Float("Humidity (%)", digits=(10,2))

    week_no = fields.Char("Week No")

    other_details = fields.Char("Other Details")

    condition = fields.Char("Condition")

    description_work = fields.Text("Description Of Work")

    # def prefill_data(self):
    #     # import wdb; wdb.set_trace()
    #     return {
    #         'name': 'Prefill Data',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'mechanical.concrete.core1.prefill.data',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_product_id': self.eln_ref.sample_id.material_id.id,
    #             'exclude_sample_id': self.eln_ref.sample_id.id,
    #             },
    #     }


    notes_id = fields.One2many('concrete.core1.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(ConcreteCoreMechanical, self).default_get(fields)

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

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

        

         
            if result.parameter.internal_id == '54b64e2d-1f6f-47e0-b5ce-5a19384bb093':
                # result.result_char = round(self.avg_compaction,2)
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
        record = super(ConcreteCoreMechanical, self).create(vals)
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
        record = self.env['mechanical.concrete.core1'].browse(self.ids[0])
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
            record.concrete_core_visible = False


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == '54b64e2d-1f6f-47e0-b5ce-5a19384bb093':
                    record.concrete_core_visible = True

               








   


    



    concrete_core_name = fields.Char("Name",default="Concrete Core")
    concrete_core_visible = fields.Boolean("Density Relation Visible",compute="_compute_visible")

    concrete_core_table = fields.One2many('mech.concrete.core1.line','parent_id',string="Density Relation")

    average_of_core = fields.Float(string="Average of  Core", compute="_compute_average_of_core")

    @api.depends('concrete_core_table.final_compressive_strength')
    def _compute_average_of_core(self):
        for record in self:
            if record.concrete_core_table:
                record.average_of_core = round(sum(line.final_compressive_strength for line in record.concrete_core_table) / len(record.concrete_core_table), 3)
            else:
                record.average_of_core = 0.0

    average_of_core_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_average_of_core_conformity")

    average_of_core_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_average_of_core_nabl")


    @api.depends('average_of_core','eln_ref','grade')
    def _compute_average_of_core_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_of_core_conformity = 'na'
                continue
            record.average_of_core_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','54b64e2d-1f6f-47e0-b5ce-5a19384bb093')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','54b64e2d-1f6f-47e0-b5ce-5a19384bb093')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.average_of_core - record.average_of_core*mu_value
                    upper = record.average_of_core + record.average_of_core*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_of_core_conformity = 'pass'
                        break
                    else:
                        record.average_of_core_conformity = 'fail'

    @api.depends('average_of_core','eln_ref','grade')
    def _compute_average_of_core_nabl(self):
        
        for record in self:
            
            record.average_of_core_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','54b64e2d-1f6f-47e0-b5ce-5a19384bb093')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','54b64e2d-1f6f-47e0-b5ce-5a19384bb093')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_of_core - record.average_of_core*mu_value
            upper = record.average_of_core + record.average_of_core*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_of_core_nabl = 'pass'
                break
            else:
                record.average_of_core_nabl = 'fail'
    
    



 


class CoreConcreteLine(models.Model):
    _name = "mech.concrete.core1.line"
    parent_id = fields.Many2one('mechanical.concrete.core1',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)

    location = fields.Char(string="Location")

    grade = fields.Char(
        string="Grade of Concrete",
        compute="_compute_grade",
    )

    characteristic_strength = fields.Integer(
        string="Characteristic Compressive Strength (N/mm²)",
        compute="_compute_characteristic_strength",
    )

    dia_core = fields.Float(
        string="Dia of Core (mm)"
    )

    height_core = fields.Float(
        string="Ht. of Core (mm)"
    )

    weight_core = fields.Float(
        string="Wt. of Core (gm)"
    )

    area = fields.Float(
        string="Area (mm²)",
        compute="_compute_area",
        store=True
    )

    load = fields.Float(
        string="Load (KN)"
    )

    core_strength = fields.Float(
        string="Core Strength (N/mm²)",
        compute="_compute_core_strength",
        store=True
    )

    ratio_n = fields.Float(
        string="n=L/D",
        compute="_compute_ratio_n",
        store=True
    )

    correction_factor = fields.Float(
        string="Correction Factor",
        compute="_compute_correction_factor",
        store=True
    )

    corrected_core_strength = fields.Float(
        string="Corrected Core Strength (N/mm²)",
        compute="_compute_corrected_core_strength",
        store=True
    )

    final_compressive_strength = fields.Float(
        string="Final Compressive Strength (N/mm²)",
        compute="_compute_final_compressive_strength",
        store=True
    )

    @api.depends('dia_core')
    def _compute_area(self):
        for rec in self:
            if rec.dia_core:
                rec.area = (3.14 * rec.dia_core * rec.dia_core) / 4
            else:
                rec.area = 0.0

    @api.depends('load', 'area')
    def _compute_core_strength(self):
        for rec in self:
            if rec.load and rec.area:
                rec.core_strength = (rec.load * 1000) / rec.area
            else:
                rec.core_strength = 0.0

    @api.depends('height_core', 'dia_core')
    def _compute_ratio_n(self):
        for rec in self:
            if rec.dia_core:
                rec.ratio_n = rec.height_core / rec.dia_core
            else:
                rec.ratio_n = 0.0

    @api.depends('ratio_n')
    def _compute_correction_factor(self):
        for rec in self:
            rec.correction_factor = (0.11 * rec.ratio_n) + 0.78

    @api.depends('core_strength', 'correction_factor')
    def _compute_corrected_core_strength(self):
        for rec in self:
            rec.corrected_core_strength = (
                rec.core_strength * rec.correction_factor
            )

    @api.depends('corrected_core_strength')
    def _compute_final_compressive_strength(self):
        for rec in self:
            rec.final_compressive_strength = (
                rec.corrected_core_strength * (5.0 / 4.0)
            )

    @api.depends('parent_id.grade')
    def _compute_grade(self):
        for rec in self:
            rec.grade = rec.parent_id.grade.grade if rec.parent_id.grade else False

    @api.depends('grade')
    def _compute_characteristic_strength(self):
        for record in self:
            if record.grade:
                # Grade madhun extraction (e.g., "M25" madhun 25 kadhne)
                numbers = re.findall(r'\d+', record.grade)
                if numbers:
                    record.characteristic_strength = int(numbers[0])
                else:
                    record.characteristic_strength = 0
            else:
                record.characteristic_strength = 0


   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CoreConcreteLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1





   


 





class CutterNotes(models.Model):
    _name = "concrete.core1.notes"

    parent_id = fields.Many2one('mechanical.concrete.core1',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")