from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class CrackWidth(models.Model):
    _name = "ndt.crack.width"
    _inherit = "lerm.eln"
    _rec_name = "name"
    name = fields.Char("Name",default="Crack Width")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    temperature = fields.Float("Temperature °C")
    child_lines = fields.One2many('ndt.crack.width.line','parent_id',string="Parameter")
    average = fields.Float(string='Average (mm)', digits=(16, 2), compute='_compute_average')
    min = fields.Float(string='Min (mm)', digits=(16, 2), compute='_compute_min_max')
    max = fields.Float(string='Max (mm)', digits=(16, 2), compute='_compute_min_max')
    structure = fields.Char("Structure")

    notes = fields.One2many('ndt.crack.width.notes','parent_id',string="Notes")



    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(CrackWidth, self).create(vals)
        record.parameter_id.write({'model_id':record.id})
        return record

    @api.depends('child_lines.crack_width_mm')
    def _compute_average(self):
        for record in self:
            total_crack_width = sum(record.child_lines.mapped('crack_width_mm'))
            num_records = len(record.child_lines)

            if num_records > 0:
                record.average = total_crack_width / num_records
            else:
                record.average = 0.0

    @api.depends('child_lines.crack_width_mm')
    def _compute_min_max(self):
        for record in self:
            crack_width_values = record.child_lines.mapped('crack_width_mm')
            if crack_width_values:
                minimum = round(min(crack_width_values),2)
                record.min = minimum
                maximum = round(max(crack_width_values),2)
                record.max = maximum
            else:
                record.min = 0.0
                record.max = 0.0


class CrackWidthLine(models.Model):
    _name = "ndt.crack.width.line"
    parent_id = fields.Many2one('ndt.crack.width',string="Parent Id")
    member = fields.Char("Element Type")
    location = fields.Char("Location")
    crack_width_mm = fields.Float("Crack Width in mm")

    

class CrackWidthNotes(models.Model):
    _name = "ndt.crack.width.notes"

    parent_id = fields.Many2one('ndt.crack.width',string="Parent Id")
    notes = fields.Char("Notes")