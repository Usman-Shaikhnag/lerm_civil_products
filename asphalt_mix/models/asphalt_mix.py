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



class AsphaltMixMechanical(models.Model):
    _name = "mechanical.asphalt.mix"
    _inherit = "lerm.eln"
    _description = 'mechanical.asphalt.mix'
    _rec_name = "name"


    name = fields.Char("Name",default="Asphalt Mix")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")
    size_id = fields.Many2one('lerm.size.line',compute="_compute_size_id")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    asphalt_temp = fields.Char("Temperature",store=True)
    asphalt_humidity = fields.Char("Humidity",store=True)

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
    




    # GRADATION OF EXTRACTED SAMPLE
    dry_gradation_name = fields.Char(default="GRADATION OF EXTRACTED SAMPLE	")
    dry_gradation_visible = fields.Boolean(compute="_compute_visible")

    weight_of_sample = fields.Float(string="Weight of Sample in gms")


    sieve_analysis_child_lines = fields.One2many('asphalt.gradation.line','parent_id',string="Parameter")
    total_sieve_analysis = fields.Float(string="Total",compute="_compute_total_sieve")


    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)

        default_lines = []

        eln_ref = res.get('eln_ref')
        if not eln_ref:
            return res

        eln = self.env['lerm.eln'].sudo().browse(eln_ref)
        if not eln.exists():
            return res

        grade = (eln.grade_id.grade or '').strip().lower()

        # Fixed sieve sizes
        sieve_sizes = [
            '45.0 mm',
            '37.5 mm',
            '26.5 mm',
            '19.0 mm',
            '13.2 mm',
            '9.5 mm',
            '4.75 mm',
            '2.36 mm',
            '1.18 mm',
            '600 mic',
            '300 mic',
            '150 mic',
            '75 mic',
            
        ]

        # Grade wise limits
        specific_limits_mapping = {
            'bm': [
                '100',
                '90-100',
                '75-100',
                '-',
                '35-61',
                '-',
                '13-22',
                '4-19',
                '-',
                '-',
                '2-10',
                '-',
                '0-8',
            ],
            'dbm': [
                '-',
                '100',
                '90-100',
                '71-95',
                '56-80',
                '-',
                '38-54',
                '28-42',
                '-',
                '-',
                '7-21',
                '-',
                '2-8',
            ],
            'bc': [
                '-',
                '-',
                '-',
                '100',
                '90-100',
                '70-88',
                '53-71',
                '42-58',
                '34-48',
                '26-38',
                '18-28',
                '12-20',
                '4-10',
            ],
        }

        limits = specific_limits_mapping.get(grade, [])

        for sieve, limit in zip(sieve_sizes, limits):
            default_lines.append((0, 0, {
                'sieve_size': sieve,
                'specific_limits': limit,
            }))

        res['sieve_analysis_child_lines'] = default_lines

        return res

    def populate_sieve_analysis_lines(self):
        self.ensure_one()

        if not self.eln_ref:
            return

        grade = (self.eln_ref.grade_id.grade or '').strip().lower()

        specific_limits_mapping = {
            'bm': [
                '100',
                '90-100',
                '75-100',
                '-',
                '35-61',
                '-',
                '13-22',
                '4-19',
                '-',
                '-',
                '2-10',
                '-',
                '0-8',
            ],
            'dbm': [
                '-',
                '100',
                '90-100',
                '71-95',
                '56-80',
                '-',
                '38-54',
                '28-42',
                '-',
                '-',
                '7-21',
                '-',
                '2-8',
            ],
            'bc': [
                '-',
                '-',
                '-',
                '100',
                '90-100',
                '70-88',
                '53-71',
                '42-58',
                '34-48',
                '26-38',
                '18-28',
                '12-20',
                '4-10',
            ],
        }

        limits = specific_limits_mapping.get(grade, [])

        for line, limit in zip(self.sieve_analysis_child_lines, limits):
            line.specific_limits = limit


    # def calculate_sieve(self):
    #  for record in self:
    #     record.populate_sieve_analysis_lines()

    #     for line in record.sieve_analysis_child_lines.sorted(key=lambda l: l.serial_no):

    #         previous_line = line.serial_no - 1

    #         if previous_line == 0:
    #             cumulative = float_round(
    #                 line.percent_retained,
    #                 precision_digits=2,
    #                 rounding_method='HALF-UP'
    #             )

    #         else:
    #             previous_line_record = self.env['asphalt.gradation.line'].search([
    #                 ('serial_no', '=', previous_line),
    #                 ('parent_id', '=', record.id)
    #             ], limit=1)

    #             cumulative = float_round(
    #                 previous_line_record.cumulative_retained + line.percent_retained,
    #                 precision_digits=2,
    #                 rounding_method='HALF-UP'
    #             )

    #         passing = float_round(
    #             100 - cumulative,
    #             precision_digits=2,
    #             rounding_method='HALF-UP'
    #         )

    #         line.write({
    #             'cumulative_retained': cumulative,
    #             'passing_percent': passing,
    #         })

    def calculate_sieve(self):
     for record in self:

        record.populate_sieve_analysis_lines()

        cumulative_weight = 0.0

        for line in record.sieve_analysis_child_lines.sorted('serial_no'):

            cumulative_weight += line.wt_retained or 0

            if record.weight_of_sample:
                cumulative = (cumulative_weight / record.weight_of_sample) * 100
                passing = 100 - cumulative
            else:
                cumulative = 0
                passing = 100

            line.write({
                'cumulative_percent': cumulative_weight,
                'cumulative_retained': round(cumulative, 2),
                'passing_percent': round(passing, 2),
            })



    
    @api.depends('sieve_analysis_child_lines.wt_retained')
    def _compute_total_sieve(self):
        for record in self:
            print("recordd",record)
            record.total_sieve_analysis = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))

    @api.onchange('sieve_analysis_child_lines')
    def _onchange_sieve_analysis_child_lines(self):
        for rec in self:
            pan_line = None
            total_retained = 0.0            
            # Find all unique sieve sizes except pan
            all_sieves = set()
            for line in rec.sieve_analysis_child_lines:
                if line.sieve_size and line.sieve_size.lower() != 'pan':
                    all_sieves.add(line.sieve_size.strip())
            
            # Calculate total retained for all non-pan sieves
            for line in rec.sieve_analysis_child_lines:
                if line.sieve_size and line.sieve_size.lower() == 'pan':
                    pan_line = line
                elif line.sieve_size in all_sieves:  # Include all non-pan sieves
                    total_retained += line.wt_retained or 0.0

            # Update pan weight if pan exists and we have a sample weight
            if pan_line and rec.weight_of_sample:
                pan_line.wt_retained = rec.weight_of_sample - total_retained


    # @api.depends('sieve_analysis_child_lines.wt_retained')
    # def _compute_cumulative_sieve(self):
    #     for record in self:
    #         print("recordd",record)
    #         record.cumulative = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))



    # Binder Content
    binder_content_name = fields.Char("Name",default="Binder Content")
    binder_content_visible = fields.Boolean("Binder Content Visible",compute="_compute_visible")

    binder_content_line_ids = fields.One2many(
        'mechanical.asphalt.extraction.line',
        'parent_id',
        string="Binder Content"
    )


    avg_binder_content = fields.Float(
        string="Average Binder Content (BC) =W5/W1*100 (%)",
        compute="_compute_avg_binder_content",
        store=True,digits=(10,3)
    )

    @api.depends('binder_content_line_ids.binder_content')
    def _compute_avg_binder_content(self):
        for rec in self:
            values = rec.binder_content_line_ids.mapped('binder_content')
            rec.avg_binder_content = sum(values) / len(values) if values else 0.0


    avg_binder_content_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_binder_content_confirmity")
    
    @api.depends('avg_binder_content','eln_ref','grade')
    def _compute_avg_binder_content_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_binder_content_confirmity = 'na'
                continue
            record.avg_binder_content_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ae96765d-e7ab-4c7d-b67e-5815f4788b03')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ae96765d-e7ab-4c7d-b67e-5815f4788b03')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_binder_content - record.avg_binder_content*mu_value
                    upper = record.avg_binder_content + record.avg_binder_content*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_binder_content_confirmity = 'pass'
                        break
                    else:
                        record.avg_binder_content_confirmity = 'fail'

    avg_binder_content_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_binder_content_nabl",store=True)

    @api.depends('avg_binder_content','eln_ref','grade')
    def _compute_avg_binder_content_nabl(self):
        
        for record in self:
            record.avg_binder_content_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ae96765d-e7ab-4c7d-b67e-5815f4788b03')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ae96765d-e7ab-4c7d-b67e-5815f4788b03')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_binder_content - record.avg_binder_content*mu_value
                    upper = record.avg_binder_content + record.avg_binder_content*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_binder_content_nabl = 'pass'
                        break
                    else:
                        record.avg_binder_content_nabl = 'fail'








    





    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

        
    def get_all_fields(self):
        record = self.env['mechanical.asphalt.mix'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.dry_gradation_visible = False
            record.binder_content_visible = False
            

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                
                if sample.internal_id == '1c05c0b0-c623-474c-918c-259f427eb9a0':
                    record.dry_gradation_visible = True

                if sample.internal_id == 'ae96765d-e7ab-4c7d-b67e-5815f4788b03':
                    record.binder_content_visible = True

                

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
            # Dry Gradation
            if result.parameter.internal_id == '1c05c0b0-c623-474c-918c-259f427eb9a0':
                result.calculated = True

            # Binder Content
            if result.parameter.internal_id == 'ae96765d-e7ab-4c7d-b67e-5815f4788b03':
                result.result_char = round(self.avg_binder_content,2)
                result.calculated = True
                if self.avg_binder_content_nabl == 'pass':
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
        record = super(AsphaltMixMechanical, self).create(vals)
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
        record = self.env['mechanical.asphalt.mix'].browse(self.ids[0])
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



    
    


    


    

    

    


    notes_id = fields.One2many('mechanical.asphalt.mix.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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
    


class AsphaltGradationLine(models.Model):
    _name = "asphalt.gradation.line"
    parent_id = fields.Many2one('mechanical.asphalt.mix', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)



    sieve_size = fields.Char(string="IS Sieve Size mm")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    cumulative_percent = fields.Float(string="Cum. Weight Retained (gm)",compute="_compute_cumulative_percent",
    store=True,)
    percent_retained = fields.Float(string='% of Weight Retained', compute="_compute_percent_retained",digits=(16,2))
    cumulative_retained = fields.Float(string="% of Cumulative Wt. Retained ", store=True,digits=(16,2))
    passing_percent = fields.Float(string="% of wt passing",digits=(16,2))
    specific_limits = fields.Char(string="Specified Limits",store=True)



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(AsphaltGradationLine, self).create(vals)

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

            new_self = super(AsphaltGradationLine, self).write(vals)
            if 'wt_retained' in vals:
                for record in self:
                    # record.parent_id._compute_total()
                    pass
            return new_self
        return super(AsphaltGradationLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id
        res = super(AsphaltGradationLine, self).unlink()
        if parent_id:
            parent_id.sieve_analysis_child_lines._reorder_serial_numbers()
        return res

    @api.depends('wt_retained', 'parent_id.weight_of_sample')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = (record.wt_retained / self.parent_id.weight_of_sample) * 100
            except ZeroDivisionError:
                record.percent_retained = 0

    @api.depends('wt_retained', 'parent_id.sieve_analysis_child_lines.wt_retained')
    def _compute_cumulative_percent(self):
        for parent in self.mapped('parent_id'):
            total = 0
            lines = parent.sieve_analysis_child_lines.sorted('serial_no')

            for line in lines:
                total += line.wt_retained or 0
                line.cumulative_percent = total


    @api.depends('cumulative_retained')
    def _compute_cum_retained(self):
        self.cumulative_retained=0
        

    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines, key=lambda r: r.id)



class AsphaltExtractionLine(models.Model):
    _name = "mechanical.asphalt.extraction.line"
    _description = "Asphalt Extraction Line"

    parent_id = fields.Many2one('mechanical.asphalt.mix', string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)

    w1 = fields.Float(string="Weight of Mix (W1)")
    w2 = fields.Float(string="Weight of Aggregate After Extraction (W2)")
    initial_filter_weight = fields.Float(
        string="Initial Weight of Filter Paper"
    )
    filter_after_extraction = fields.Float(
        string="Weight of Filter Paper After Extraction With Fine Materials (W3)"
    )

    w4 = fields.Float(
        string="Increased Weight of Filter Paper",
        compute="_compute_w4",
        store=True,
    )

    w5 = fields.Float(
        string="Weight of Binder (W5) =W1-(W2+W4)",
        compute="_compute_w5",
        store=True,
    )

    binder_content = fields.Float(
        string="Binder Content (BC) =W5/W1*100 (%)",
        compute="_compute_binder_content",
        store=True,
        digits=(16, 2),
    )

    @api.depends("filter_after_extraction", "initial_filter_weight")
    def _compute_w4(self):
        for rec in self:
            rec.w4 = rec.filter_after_extraction - rec.initial_filter_weight

    @api.depends("w1", "w2", "w4")
    def _compute_w5(self):
        for rec in self:
            rec.w5 = rec.w1 - (rec.w2 + rec.w4)

    @api.depends("w1", "w5")
    def _compute_binder_content(self):
        for rec in self:
            rec.binder_content = (
                (rec.w5 / rec.w1) * 100
                if rec.w1
                else 0.0
            )

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(AsphaltExtractionLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class AsphaltMixMechanicalNotes(models.Model):
    _name = "mechanical.asphalt.mix.notes"

    parent_id = fields.Many2one('mechanical.asphalt.mix', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
