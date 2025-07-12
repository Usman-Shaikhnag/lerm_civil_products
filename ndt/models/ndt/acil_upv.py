from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class AcilUPV(models.Model):
    _name = "ndt.acil.upv"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="ACIL UPV")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")
    child_lines = fields.One2many('ndt.acil.upv.line', 'parent_id', string="Parameter")
    average = fields.Float("Average", compute="_compute_velocity_stats")
    min = fields.Float("Min", compute="_compute_velocity_stats")
    max = fields.Float("Max", compute="_compute_velocity_stats")

    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(AcilUPV, self).create(vals)
        record.parameter_id.write({'model_id':record.id})
        return record

    @api.depends('child_lines.velocity')
    def _compute_velocity_stats(self):
        for record in self:
            velocities = record.child_lines.mapped('velocity')
            if velocities:
                record.average = sum(velocities) / len(velocities)
                record.min = min(velocities)
                record.max = max(velocities)
            else:
                record.average = 0.0
                record.min = 0.0
                record.max = 0.0



class AcilUPVLine(models.Model):
    _name = "ndt.acil.upv.line"
    parent_id = fields.Many2one('ndt.acil.upv',string="Parent Id")
    member = fields.Char("Member")
    location = fields.Char("Location")
    level = fields.Char("Level")
    dist = fields.Float("Dist. (m)")
    time = fields.Float("Time. (μs)")
    velocity = fields.Float("Velocity(km/sec)",compute="_compute_velocity")
    concrete_condition = fields.Char("Condition of Concrete")
    quality = fields.Char("Quality")
    method = fields.Char("Method")

    @api.depends('dist', 'time')
    def _compute_velocity(self):
        for record in self:
            if record.dist and record.time:
                velocity = (record.dist / record.time) * 1000  # Convert time from μs to seconds
                record.velocity = velocity
            else:
                record.velocity = 0.0


