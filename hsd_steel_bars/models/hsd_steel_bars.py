from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math
from odoo.tools.float_utils import float_round
import io
import numpy as np
import logging
_logger = logging.getLogger(__name__)
import base64



class HSDSteelBarsMechanical(models.Model):
    _name = "mechanical.hsd.steel.bars"
    _inherit = "lerm.eln"
    _description = 'mechanical.hsd.steel.bars'
    _rec_name = "name"


    name = fields.Char("Name",default="High Strength Deformed Steel Bars")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")
    size_id = fields.Many2one('lerm.size.line',compute="_compute_size_id")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    temp = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)

    @api.depends("eln_ref")
    def _compute_size_id(self):
        for record in self:
            print("Size iD",record.eln_ref.size_id)
            record.size_id = record.eln_ref.size_id.id

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'aac.block.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }
    




    # Mass Per Meter Of High Strength Deformed Steel Bars
    mass_per_meter_name = fields.Char("Name",default="Mass Per Meter Of High Strength Deformed Steel Bars")
    mass_per_meter_visible = fields.Boolean("Mass Per Meter Visible",compute="_compute_visible")

    mass_per_meter_line_ids = fields.One2many(
        'mass.per.meter.line',
        'parent_id',
        string="Mass Per Meter"
    )


    avg_standard_mass = fields.Float(
        string="Average Standard Mass (kg/m)",
        compute="_compute_avg_standard_mass",
        store=True,digits=(10,3)
    )

    @api.depends('mass_per_meter_line_ids.standard_mass')
    def _compute_avg_standard_mass(self):
        for rec in self:
            values = rec.mass_per_meter_line_ids.mapped('standard_mass')
            rec.avg_standard_mass = sum(values) / len(values) if values else 0.0


    avg_standard_mass_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_standard_mass_confirmity")
    
    @api.depends('avg_standard_mass','eln_ref','grade')
    def _compute_avg_standard_mass_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_standard_mass_confirmity = 'na'
                continue
            record.avg_standard_mass_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','90d59fb9-f6ee-487a-adfd-3ed027f75eff')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','90d59fb9-f6ee-487a-adfd-3ed027f75eff')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_standard_mass - record.avg_standard_mass*mu_value
                    upper = record.avg_standard_mass + record.avg_standard_mass*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_standard_mass_confirmity = 'pass'
                        break
                    else:
                        record.avg_standard_mass_confirmity = 'fail'

    avg_standard_mass_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_standard_mass_nabl",store=True)

    @api.depends('avg_standard_mass','eln_ref','grade')
    def _compute_avg_standard_mass_nabl(self):
        
        for record in self:
            record.avg_standard_mass_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','90d59fb9-f6ee-487a-adfd-3ed027f75eff')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','90d59fb9-f6ee-487a-adfd-3ed027f75eff')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_standard_mass - record.avg_standard_mass*mu_value
                    upper = record.avg_standard_mass + record.avg_standard_mass*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_standard_mass_nabl = 'pass'
                        break
                    else:
                        record.avg_standard_mass_nabl = 'fail'


    standard_mass_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    standard_mass_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_standard_mass_final_report", store=True)

    @api.depends('avg_standard_mass_nabl', 'standard_mass_report_type')
    def _compute_standard_mass_final_report(self):
     for rec in self:

        # Manual override
        if rec.standard_mass_report_type == 'nabl':
            rec.standard_mass_final_report = 'nabl'

        elif rec.standard_mass_report_type == 'non_nabl':
            rec.standard_mass_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_standard_mass_nabl == 'pass':
                rec.standard_mass_final_report = 'nabl'
            else:
                rec.standard_mass_final_report = 'non_nabl'

                





    
    

    





    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

        
    def get_all_fields(self):
        record = self.env['mechanical.hsd.steel.bars'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.mass_per_meter_visible = False
            
            

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                
                if sample.internal_id == '90d59fb9-f6ee-487a-adfd-3ed027f75eff':
                    record.mass_per_meter_visible = True

                

                

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
            # Dry Gradation
            if result.parameter.internal_id == '90d59fb9-f6ee-487a-adfd-3ed027f75eff':
                result.calculated = True
                # if self.avg_binder_content_nabl == 'pass':
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
        record = super(HSDSteelBarsMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record
    
    

    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

    def get_all_fields(self):
        record = self.env['mechanical.hsd.steel.bars'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

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



    
    


    


    

    

    


    notes_id = fields.One2many('mechanical.hsd.steel.bars.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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
    


class MassPerMeterLine(models.Model):
    _name = "mass.per.meter.line"
    parent_id = fields.Many2one('mechanical.hsd.steel.bars', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)


    bar_dia = fields.Float(
        string="Bar Dia (mm)"
    )

    sample_length = fields.Float(
        string="Length of Sample (m)"
    )

    mass = fields.Float(
        string="Mass (kg)"
    )

    standard_mass = fields.Float(
        string="Standard Mass (kg/m)",
        compute="_compute_standard_mass",
        store=True,
        digits=(16, 2),
    )

    remark = fields.Char(
        string="Remark"
    )

    @api.depends("bar_dia")
    def _compute_standard_mass(self):
        for rec in self:
            rec.standard_mass = (
                (rec.bar_dia ** 2) / 162
                if rec.bar_dia
                else 0.0
            )




    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(MassPerMeterLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class HSDSteelBarsMechanicalNotes(models.Model):
    _name = "mechanical.hsd.steel.bars.notes"

    parent_id = fields.Many2one('mechanical.hsd.steel.bars', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
