from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re


class UpvInDirct(models.Model):
    _name = "ndt.upv.indirect"
    _inherit = "lerm.eln"
    _rec_name = "name"


    eln_ref = fields.Many2one("lerm.eln")
    name = fields.Char("Name",default="UPV IN-DIRECT")
    
    structure = fields.Char("Approximate Age of structure  Years")
    temperature = fields.Float("Concrete Temp °C",required=True)
    concrete_grade = fields.Char("Concrete Grade")
    instrument = fields.Char("Instrument")
    structure = fields.Char("Structure")
    grade_id = fields.Many2one('lerm.grade.line',compute="_compute_grade", string="Grade")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")
    child_lines = fields.One2many('ndt.upv.indirect.line', 'parent_id', string="Parameter")
    average = fields.Float("Average km/s",digits=(16,2))
    minimum = fields.Float("Min km/s",digits=(16,2))
    maximum = fields.Float("Max km/s",digits=(16,2))
    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")


    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None

    # notes = fields.One2many('ndt.upv.notes','parent_id',string="Notes")
    eln_ref = fields.Many2one('lerm.eln',string="Eln")

    notes_id = fields.One2many('ndt.upv.indirect.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(UpvInDirct, self).default_get(fields)

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
            if result.parameter.internal_id == '461de996-b69d-436b-803f-59f4b37d52eb':
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

    # @api.depends('child_lines.velocity')
    # def _compute_velocity_stats(self):
    #     for record in self:
    #         velocities = record.child_lines.mapped('velocity')
    #         if velocities:
    #             average = sum(velocities) / len(velocities)
    #             average = round(average,2)
    #             record.average = average
    #             minimum = min(velocities)
    #             minimum = round(minimum,2)
    #             record.minimum = minimum
    #             maximum = max(velocities)
    #             maximum = max(maximum,2)
    #             record.maximum = maximum
               
    #             # import wdb;wdb.set_trace()

    #         else:
    #             record.average = 0.0
    #             record.minimum = 0.0
    #             record.maximum = 0.0



    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(UpvInDirct, self).create(vals)
        record.parameter_id.write({'model_id':record.id})
        return record


class UpvInDirectLine(models.Model):
    _name = "ndt.upv.indirect.line"
    parent_id = fields.Many2one('ndt.upv.indirect',string="Parent Id")

    # element_type = fields.Char("Element Type")
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    level_id = fields.Char("LOCATION")
    casting_date = fields.Date("DATE OF CASTING",compute="_compute_dt_of_casting", store=True)
    path = fields.Char("PATH")
    dist = fields.Float("DISTANCE [MM]",digits=(16,2))
    time = fields.Float("TIME [µs]",digits=(16,2))
    slope = fields.Float("SLOPE",digits=(16,4),compute="_compute_slope", store=True)
    actual_velocity = fields.Float("ACTUAL VELOCITY [Km/s]",compute="_compute_slope", store=True)
    corrected_velocity = fields.Float("CORRECTED VELOCITY [Km/s]")
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
    ],"QUALITY OF CONCRETE")

    # @api.depends('parent_id.date_of_casting')
    # def _compute_dt_of_casting(self):
    #     for record in self:
    #         record.casting_date = record.parent_id.date_of_casting

    @api.depends('parent_id.date_of_casting')
    def _compute_dt_of_casting(self):
        for record in self:
            # आधी बेसिक चेक: जर पॅरेंट किंवा चाईल्ड लाईन्स नसतील तर तारीख रिकामी ठेवा
            if not record.parent_id or not record.parent_id.child_lines:
                record.casting_date = False
                continue

            all_lines = list(record.parent_id.child_lines)
            
            try:
                current_index = all_lines.index(record)
            except ValueError:
                record.casting_date = False
                continue

            base_index = (current_index // 3) * 3

            if base_index < len(all_lines):
                base_line = all_lines[base_index]
                record.casting_date = base_line.parent_id.date_of_casting
            else:
                record.casting_date = False


    @api.depends('parent_id.child_lines', 'parent_id.child_lines.dist', 'parent_id.child_lines.time')
    def _compute_slope(self):
        for record in self:
            if not record.parent_id or not record.parent_id.child_lines:
                record.slope = 0.0
                record.actual_velocity = 0.0
                record.corrected_velocity = 0.0
                record.quality = False
                continue

            all_lines = list(record.parent_id.child_lines)
            
            try:
                current_index = all_lines.index(record)
            except ValueError:
                record.slope = 0.0
                record.actual_velocity = 0.0
                record.corrected_velocity = 0.0
                record.quality = False
                continue

            if current_index % 3 == 0:
                first_line_index = current_index
                third_line_index = current_index + 2
                
                if third_line_index < len(all_lines):
                    line_1 = all_lines[first_line_index] 
                    line_3 = all_lines[third_line_index] 
                    
                    dist_diff = line_1.dist - line_3.dist
                    
                    if dist_diff != 0:
                        calculated_slope = (line_1.time - line_3.time) / dist_diff
                        record.slope = calculated_slope
                        
                        if calculated_slope != 0:
                            calculated_velocity = 1.0 / calculated_slope
                            record.actual_velocity = calculated_velocity
                            
                            if calculated_velocity >= 3.0:
                                final_corrected = calculated_velocity + 0.5
                            else:
                                final_corrected = calculated_velocity
                            record.corrected_velocity = final_corrected
                            
                            if final_corrected > 4.5:
                                record.quality = 'excellent'
                            elif 3.75 <= final_corrected <= 4.5:
                                record.quality = 'good'
                            elif 0.0 < final_corrected < 3.75:
                                record.quality = 'doubtful'
                            else:
                                record.quality = False
                        else:
                            record.actual_velocity = 0.0
                            record.corrected_velocity = 0.0
                            record.quality = False
                    else:
                        record.slope = 0.0
                        record.actual_velocity = 0.0
                        record.corrected_velocity = 0.0
                        record.quality = False
                else:
                    record.slope = 0.0
                    record.actual_velocity = 0.0
                    record.corrected_velocity = 0.0
                    record.quality = False
            else:
                record.slope = 0.0
                record.actual_velocity = 0.0
                record.corrected_velocity = 0.0
                record.quality = False

    is_editable_line = fields.Boolean(compute="_compute_editable_line", store=False)

    @api.depends('serial_no')
    def _compute_editable_line(self):
        for record in self:
           
            if record.serial_no and (record.serial_no - 1) % 3 == 0:
                record.is_editable_line = True
            else:
                record.is_editable_line = False
    # method = fields.Selection([
    #     ('direct', 'Direct'),
    #     ('indirect', 'In-Direct'),
    #     ('semi_direct', 'Semi-Direct')],"Method")

    # @api.depends('dist', 'time')
    # def _compute_velocities(self):
    #     for record in self:
    #         if record.dist > 0 and record.time > 0:
    #             # 1. VELOCITY [m/s] -> (170 / 100) / (4.09 / 1000000) = 415,647.92
    #             v_m_s = (record.dist / 100) / (record.time / 1000000)
    #             record.velocity = v_m_s
                
    #             # 2. ACTUAL VELOCITY [Km/s] -> 415,647.92 / 100000 = 4.16
    #             # Tumchya accurate formatsathi ithe 100000 ne divide kele ahe
    #             v_km_s = v_m_s / 10000
    #             record.actual_velocity = v_km_s
                
    #             # 3. CORRECTED VELOCITY [Km/s] -> 4.16 + 0.5 = 4.66
    #             if v_km_s >= 3.0:
    #                 corrected_v = v_km_s + 0.5
    #             else:
    #                 corrected_v = v_km_s
    #             record.corrected_velocity = corrected_v
                
    #             # 4. QUALITY OF CONCRETE
    #             if corrected_v > 4.4:
    #                 record.quality = 'excellent'
    #             elif 3.75 <= corrected_v <= 4.4:
    #                 record.quality = 'good'
    #             elif 3.0 <= corrected_v < 3.75:
    #                 record.quality = 'doubtful'
    #             else:
    #                 record.quality = 'poor'
    #         else:
    #             record.velocity = 0.0
    #             record.actual_velocity = 0.0
    #             record.corrected_velocity = 0.0
    #             record.quality = False
    
   
   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(UpvInDirectLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class UpvInDirectNotes(models.Model):
    _name = "ndt.upv.indirect.notes"

    parent_id = fields.Many2one('ndt.upv.indirect',string="Parent Id")

    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
