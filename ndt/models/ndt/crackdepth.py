from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class CrackDepth(models.Model):
    _name = "ndt.crack.depth"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Crack Depth")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="ELN")
    temperature = fields.Float("Temperature °C")
    child_lines = fields.One2many('ndt.crack.depth.line','parent_id',string="Parameter")
    average = fields.Float(string='Average mm', digits=(16, 2), compute='_compute_average')
    # min_cd = fields.Float(string="Min mm")
    min_cd = fields.Float(string="Min mm", compute='_compute_min_cd', store=True)
    # max_cd = fields.Float(string="Max mm")
    max_cd = fields.Float(string="Max mm", compute='_compute_max_cd', store=True)
    structure = fields.Char("Structure")
    notes = fields.One2many('ndt.crack.depth.notes','parent_id',string="Notes")
    eln_ref = fields.Many2one('lerm.eln',string="Eln")

    def open_eln_page(self):
    # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == 'b6daa925-6296-4f2e-991e-6c4cb6e4da68':
                result.result_char = round(self.average,2)
                continue



   
        
    @api.depends('child_lines.cd')
    def _compute_average(self):
        for record in self:
            total_cd = sum(record.child_lines.mapped('cd'))
            num_records = len(record.child_lines)

            if num_records > 0:
                average = round(total_cd / num_records,2)
                record.average = average
            else:
                record.average = 0.0
    
    @api.depends('child_lines.cd')
    def _compute_min_cd(self):
        for record in self:
            min_cd_value = round(min(record.child_lines.mapped('cd'), default=0.0),2)
            record.min_cd = min_cd_value

    @api.depends('child_lines.cd')
    def _compute_max_cd(self):
        for record in self:
            max_cd_value = round(max(record.child_lines.mapped('cd'), default=0.0),2)
            record.max_cd = max_cd_value

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
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    def get_all_fields(self):
        record = self.env['ndt.crack.depth'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(CrackDepth, self).create(vals)
        record.parameter_id.write({'model_id':record.id})
        return record


    notes_id = fields.One2many('ndt.crack.depth.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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


class CrackDepthLine(models.Model):
    _name = "ndt.crack.depth.line"
    parent_id = fields.Many2one('ndt.crack.depth',string="Parent Id")
    member = fields.Char("Element Type")
    location = fields.Char("Location")
    tc = fields.Float("Tc")
    ts = fields.Float("Ts")
    distance = fields.Float("Distance")
    tc2 = fields.Float("Tc2",compute="_compute_square")
    ts2 = fields.Float("Ts2",compute="_compute_square")
    tc2_by_ts2 = fields.Float("Tc2/Ts2",compute="_compute_square")
    sqrt_Tc2_by_Ts2minus1 = fields.Float("√Tc2/Ts2-1",compute="_compute_square")
    cd = fields.Float("CD=√Tc2/Ts2-1 x 200",compute="_compute_square")

    @api.depends('tc','ts','tc2','ts2','tc2_by_ts2','distance')
    def _compute_square(self):
        for record in self:
            try:
                record.tc2 = record.tc**2
                record.ts2 = record.ts**2
                try:
                    record.tc2_by_ts2 = record.tc2/record.ts2
                except:
                    record.tc2_by_ts2 = 0 
                try:
                    record.sqrt_Tc2_by_Ts2minus1 = math.sqrt(record.tc2_by_ts2 - 1)
                except:
                    record.sqrt_Tc2_by_Ts2minus1 = 0
                try:
                    record.cd = record.sqrt_Tc2_by_Ts2minus1 * record.distance
                except:
                    record.cd = 0
            except:
                pass
                
                
class CrackDepthNotes(models.Model):
    _name = "ndt.crack.depth.notes"

    parent_id = fields.Many2one('ndt.crack.depth',string="Parent Id")
    notes = fields.Char("Notes")
class CrackDepthNotes(models.Model):
    _name = "ndt.crack.depth.notes"

    parent_id = fields.Many2one('ndt.crack.depth', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
