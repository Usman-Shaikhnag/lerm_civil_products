from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class AcilCrackDepth(models.Model):
    _name = "ndt.acil.crack.depth"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Crack Depth")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines = fields.One2many('ndt.acil.crack.depth.line','parent_id',string="Parameter")

    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(AcilCrackDepth, self).create(vals)
        record.parameter_id.write({'model_id':record.id})
        return record

class AcilCrackDepthLine(models.Model):
    _name = "ndt.acil.crack.depth.line"
    parent_id = fields.Many2one('ndt.acil.crack.depth',string="Parent Id")
    member = fields.Char(string="Member")
    location = fields.Char(string="Location")
    level = fields.Char(string="Level")
    tc = fields.Float(string='TC µs')
    ts = fields.Float(string='TS µs')
    depth = fields.Float(string="Depth in mm")


                


