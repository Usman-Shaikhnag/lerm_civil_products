from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re


class UpvDirct(models.Model):
    _name = "ndt.upv.direct"
    _inherit = "lerm.eln"
    _rec_name = "name"


    eln_ref = fields.Many2one("lerm.eln")
    name = fields.Char("Name",default="UPV DIRECT")
    
    structure = fields.Char("Approximate Age of structure  Years")
    temperature = fields.Float("Concrete Temp °C",required=True)
    concrete_grade = fields.Char("Concrete Grade")
    instrument = fields.Char("Instrument")
    structure = fields.Char("Structure")
    grade_id = fields.Many2one('lerm.grade.line',compute="_compute_grade", string="Grade")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")
    child_lines = fields.One2many('ndt.upv.direct.line', 'parent_id', string="Parameter")
    
    average = fields.Float("Average km/s", compute="_compute_velocity_stats",digits=(16,2))
    minimum = fields.Float("Min km/s", compute="_compute_velocity_stats",digits=(16,2))
    maximum = fields.Float("Max km/s", compute="_compute_velocity_stats",digits=(16,2))

    # notes = fields.One2many('ndt.upv.notes','parent_id',string="Notes")
    eln_ref = fields.Many2one('lerm.eln',string="Eln")

    notes_id = fields.One2many('ndt.upv.direct.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(UpvDirct, self).default_get(fields)

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
            if result.parameter.internal_id == '1e7a5df3-a897-4933-bd5a-27daee518ba7':
                result.result_char = round(self.average,2)
                result.calculated = True
                continue

        return {
                'view_mode': 'form',
                'res_model': "lerm.eln",
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.eln_ref.id,
                
            }

    @api.depends('eln_ref')
    def _compute_grade(self):
        for record in self:
            record.grade_id = record.eln_ref.grade_id.id

    @api.depends('child_lines.velocity')
    def _compute_velocity_stats(self):
        for record in self:
            velocities = record.child_lines.mapped('velocity')
            if velocities:
                average = sum(velocities) / len(velocities)
                average = round(average,2)
                record.average = average
                minimum = min(velocities)
                minimum = round(minimum,2)
                record.minimum = minimum
                maximum = max(velocities)
                maximum = max(maximum,2)
                record.maximum = maximum
               
                # import wdb;wdb.set_trace()

            else:
                record.average = 0.0
                record.minimum = 0.0
                record.maximum = 0.0



    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(UpvDirct, self).create(vals)
        record.parameter_id.write({'model_id':record.id})
        return record


class UpvDirectLine(models.Model):
    _name = "ndt.upv.direct.line"
    parent_id = fields.Many2one('ndt.upv.direct',string="Parent Id")

    # element_type = fields.Char("Element Type")
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    level_id = fields.Char("LOCATION")
    grid = fields.Char("GRID")
    path = fields.Char("PATH")
    dist = fields.Float("DISTANCE [MM]",digits=(16,2))
    time = fields.Float("TIME [µs]",digits=(16,2))
    velocity = fields.Float("VELOCITY [m/s]",digits=(16,2),compute="_compute_velocities")
    actual_velocity = fields.Float("ACTUAL VELOCITY [Km/s]",compute="_compute_velocities")
    corrected_velocity = fields.Float("CORRECTED VELOCITY [Km/s]",compute="_compute_velocities")
    # condition_concrete = fields.Selection([
    #     ('dry', 'Dry'),
    #     ('wet', 'Wet')],"Condition Of Concrete")
    
    # surface = fields.Selection([
    #     ('w/o_plaster', 'W/O Plaster')],"Surface",default='w/o_plaster')
    
    quality = fields.Selection([
        ('excellent','Excellent'),
        ('good','Good'),
        ('medium','Medium'),
        ('doubtful','Doubtful'),
        ('poor','Poor')
    ],"QUALITY OF CONCRETE",compute="_compute_velocities")

    # method = fields.Selection([
    #     ('direct', 'Direct'),
    #     ('indirect', 'In-Direct'),
    #     ('semi_direct', 'Semi-Direct')],"Method")

    @api.depends('dist', 'time')
    def _compute_velocities(self):
        for record in self:
            if record.dist > 0 and record.time > 0:
                # 1. VELOCITY [m/s] -> (170 / 100) / (4.09 / 1000000) = 415,647.92
                v_m_s = (record.dist / 100) / (record.time / 1000000)
                record.velocity = v_m_s
                
                # 2. ACTUAL VELOCITY [Km/s] -> 415,647.92 / 100000 = 4.16
                # Tumchya accurate formatsathi ithe 100000 ne divide kele ahe
                v_km_s = v_m_s / 10000
                record.actual_velocity = v_km_s
                
                # 3. CORRECTED VELOCITY [Km/s] -> 4.16 + 0.5 = 4.66
                if v_km_s >= 3.0:
                    corrected_v = v_km_s + 0.5
                else:
                    corrected_v = v_km_s
                record.corrected_velocity = corrected_v
                
                # 4. QUALITY OF CONCRETE
                if corrected_v > 4.4:
                    record.quality = 'excellent'
                elif 3.75 <= corrected_v <= 4.4:
                    record.quality = 'good'
                elif 3.0 <= corrected_v < 3.75:
                    record.quality = 'doubtful'
                else:
                    record.quality = 'poor'
            else:
                record.velocity = 0.0
                record.actual_velocity = 0.0
                record.corrected_velocity = 0.0
                record.quality = False
    
   
    # @api.depends('velocity')
    # def _compute_quality(self):
    #     for record in self:
    #         string1 = "M25"
    #         # string1 = self.parent_id.grade_id.grade
    #         string2 = self.parent_id.grade_id.grade
    #         print("String 2:", string2)  # Add this line for debugging
            
    #         if string2 and string2 != '--' :  # Check if string2 is not None or empty
    #             numeric_part1 = self.extract_number_from_string(string1)
    #             numeric_part2 = self.extract_number_from_string(string2)
    #             print("Numeric Part 2:", numeric_part2)  # Add this line for debugging
                
    #             print(type(numeric_part1))
    #             print(type(numeric_part2))
    #             print(type(record.velocity))                
                
    #             if record.velocity > 4.5:
    #                 record.quality = 'excellent'
            
    #             elif numeric_part1 >= numeric_part2 and 3.5 <= record.velocity <= 4.5:
    #                 record.quality = 'good'
    #             elif numeric_part1 < numeric_part2 and 3.75 <= record.velocity <= 4.5:
    #                 record.quality = 'good'
    #             else:
    #                 record.quality = 'doubtful'
    #         else:
    #             record.quality = 'doubtful'

    # def extract_number_from_string(self, string):
    #     if string:  # Ensure string is not None or empty
    #         pattern = r'\d+'  # Regular expression pattern to match one or more digits
    #         match = re.search(pattern, string)
    #         if match:
    #             return int(match.group())  # Convert the matched substring to an integer
    #     return None  # Return None if string is None or empty    
    # # def extract_numeric_part(s):
    # #     numeric_part = ''.join(filter(str.isdigit, s))
    # #     return int(numeric_part) if numeric_part else 0
    
    
    # @api.depends('dist', 'time','method','parent_id')
    # def _compute_velocity(self):
    #     for record in self:
    #         # import wdb; wdb.set_trace() 
    #         temp = float(record.parent_id.temperature)
    #         if record.dist and record.time and record.method != 'indirect':
    #             velocity = round((record.dist / record.time) * 1000 ,2) # Convert time from μs to seconds
    #             if temp > 30:
    #                 velocity = round(velocity + (velocity*0.05),2)
    #             record.velocity = velocity
    #         elif record.dist and record.time and record.method == 'indirect':
    #             velocity = ((record.dist / record.time) * 1000)  # Convert time from μs to seconds
    #             if velocity > 3:
    #                 velocity = round(velocity + 0.5,2)
    #             if temp > 30:
    #                 velocity = round(velocity + (velocity*0.05),2)
    #             record.velocity = velocity

    #         else:
    #             record.velocity = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(UpvDirectLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class UpvNotes(models.Model):
    _name = "ndt.upv.direct.notes"

    parent_id = fields.Many2one('ndt.upv.direct',string="Parent Id")

    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
