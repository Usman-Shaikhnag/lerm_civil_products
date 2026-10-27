from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class ReboundHammer(models.Model):
    _name = "ndt.rebound.hammer"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Rebound Hammer")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    temperature = fields.Float("Temperature °C")
    child_lines = fields.One2many('ndt.rebound.hammer.line','parent_id',string="Parameter")
    average_mpa = fields.Float(string="Average Mpa",compute="_compute_average",store=True)
    minimum_mpa = fields.Float(string="Minimum Mpa",compute="_compute_average",store=True)
    maximum_mpa = fields.Float(string="Maximum Mpa",compute="_compute_average",store=True)
    structure = fields.Char("Structure")
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    surface_condition = fields.Char("Surface Condition")
    make = fields.Char("Make")
    model = fields.Char("Model")

    description_work = fields.Char("Description Of Work")
    no_points = fields.Char("No.Of. Points")
    sample_satus = fields.Char("Sample Status")

    notes_id = fields.One2many('ndt.rebound.hammer.notes','parent_id',string="Notes")

    @api.model
    def default_get(self, fields):
        res = super(ReboundHammer, self).default_get(fields)

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


    # @api.depends('child_lines.avg')
    # def _compute_average(self):
    #     for record in self:
    #         total_value = sum(record.child_lines.mapped('avg'))
    #         self.average = float(round(total_value / len(record.child_lines),2)) if record.child_lines else 0.0

    # @api.depends('child_lines.mpa')
    # def _compute_average(self):
    #     for record in self:
    #         mpa_values = record.child_lines.mapped('mpa')
    #         record.average_mpa = sum(mpa_values) / len(mpa_values) if len(mpa_values) > 0 else 0.0

    @api.depends('child_lines.mpa')
    def _compute_average(self):
        for record in self:
            mpa_values = record.child_lines.mapped('mpa')
            record.average_mpa = sum(mpa_values) / len(mpa_values) if len(mpa_values) > 0 else 0.0
            minimum_mpa = round(min(mpa_values, default=0.0),2)
            record.minimum_mpa = minimum_mpa
            maximum_mpa = round(max(mpa_values, default=0.0),2)
            record.maximum_mpa = maximum_mpa




    # @api.depends('child_lines.avg')
    # def _compute_min_max(self):
    #     for record in self:
    #         values = record.child_lines.mapped('avg')
    #         self.minimum = round(float(min(values)),2) if values else 0.0
    #         self.maximum = round(float(max(values)),2) if values else 0.0

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            if result.parameter.internal_id == 'ac8884d0-a4f0-4f4d-9da3-459ff8921289':
                result.result_char = round(self.average_mpa,2)
                result.calculated = True
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
        record = super(ReboundHammer, self).create(vals)
        record.parameter_id.write({'model_id':record.id})
        return record

class CarbonationnLine(models.Model):
    _name = "ndt.rebound.hammer.line"
    parent_id = fields.Many2one('ndt.rebound.hammer',string="Parent Id")
    # element = fields.Char(string="Member / Element Type")
    serial_no = fields.Integer(string="Test Point", readonly=True, copy=False, default=1)
    location = fields.Char(string="Location")
    impact_direction = fields.Char(string="Impact Direction")
    f1 = fields.Integer(string="1")
    f2 = fields.Integer(string="2")
    f3 = fields.Integer(string="3")
    f4 = fields.Integer(string="4")
    f5 = fields.Integer(string="5")
    f6 = fields.Integer(string="6")
    
    # f10 = fields.Integer(string="10")
    avg = fields.Float(string="Average" ,compute="_compute_average")
    mpa = fields.Float(string="Mpa",compute="_compute_mpa", store=True)
    direction = fields.Selection([
        ('horizontal', 'Horizontal'),
        ('vertical_up', 'Vertical Up'), 
        ('vertical_down', 'Vertical Down')], string='Direction')


    @api.depends('f1', 'f2', 'f3', 'f4', 'f5', 'f6')
    def _compute_average(self):
        for record in self:
            values = [
                record.f1, record.f2, record.f3,
                record.f4, record.f5, record.f6
            ]
            record.avg = sum(values) / len(values)

    
    
    # def _interpolate(self, x, x_table, y_table):
    #     """Linear interpolation equivalent to the Excel formula."""
    #     if not x_table or len(x_table) != len(y_table):
    #         return 0.0

    #     # Excel MATCH(..., 1) requires ascending lookup values.
    #     if x < x_table[0] or x > x_table[-1]:
    #         return 0.0

    #     for i in range(len(x_table) - 1):
    #         x1 = x_table[i]
    #         x2 = x_table[i + 1]
    #         y1 = y_table[i]
    #         y2 = y_table[i + 1]

    #         if x1 <= x <= x2:
    #             if x2 == x1:
    #                 return y1

    #             return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

    #     return y_table[-1]

    # @api.depends('avg', 'impact_direction')
    # def _compute_calibrated_value(self):
    #     # Replace these example arrays with your actual Excel data.
    #     table_0_x = []
    #     table_0_y = []

    #     table_neg90_x = []
    #     table_neg90_y = []

    #     table_90_x = []
    #     table_90_y = []

    #     for record in self:
    #         direction = record.impact_direction

    #         if direction == '0':
    #             result = self._interpolate(
    #                 record.avg, table_0_x, table_0_y
    #             )
    #         elif direction == '-90':
    #             result = self._interpolate(
    #                 record.avg, table_neg90_x, table_neg90_y
    #             )
    #         elif direction == '90':
    #             result = self._interpolate(
    #                 record.avg, table_90_x, table_90_y
    #             )
    #         else:
    #             result = 0.0

    #         record.mpa = result
    

    


    # @api.depends('f1', 'f2', 'f3', 'f4', 'f5', 'f6')
    # def _compute_average(self):
    #     for record in self:
    #         values = [record.f1, record.f2, record.f3, record.f4, record.f5, record.f6]

    #         sorted_array = sorted(values)
    #         midpoint = len(sorted_array) // 2
    #         if len(sorted_array) % 2 == 0:
    #             median = (sorted_array[midpoint - 1] + sorted_array[midpoint]) / 2.0
    #         else:
    #             median = sorted_array[midpoint]

    #         first_quartile = sorted_array[:midpoint]
    #         third_quartile = sorted_array[midpoint:]
    #         midpoint = len(first_quartile) // 2
    #         if len(first_quartile) % 2 == 0:
    #             median_first = (first_quartile[midpoint - 1] + first_quartile[midpoint]) / 2.0
    #         else:
    #             median_first = first_quartile[midpoint]
    #         midpoint = len(third_quartile) // 2
    #         if len(third_quartile) % 2 == 0:
    #             median_third = (third_quartile[midpoint - 1] + third_quartile[midpoint]) / 2.0
    #         else:
    #             median_third = third_quartile[midpoint]
    #         iqr = median_third - median_first
    #         lower_bound = median_first - 1.5 * iqr
    #         upper_bound = median_third + 1.5 * iqr

    #         filtered_array = [x for x in values if lower_bound <= x <= upper_bound]

    #         record.avg = sum(filtered_array) / len(filtered_array)

    @api.depends('avg')
    def _compute_mpa(self):
        for record in self:
            if record.avg > 0:
                # Standard Horizontal (0°) Hammer sathi standard polynomial regression formula:
                # Formula: MPa = 0.023 * (Avg^2) - 0.22 * Avg - 3.1
                # (Ha formula average chart chya trends varun banavla ahe)
                
                calculated_mpa = (0.023 * (record.avg ** 2)) - (0.22 * record.avg) - 3.1
                
                # Compressive strength negative madhye nahi jau shakat, mhanun check thevla ahe
                record.mpa = max(calculated_mpa, 0.0)
            else:
                record.mpa = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CarbonationnLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1
                


class ReboundHammerNotes(models.Model):
    _name = "ndt.rebound.hammer.notes"

    parent_id = fields.Many2one('ndt.rebound.hammer',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")