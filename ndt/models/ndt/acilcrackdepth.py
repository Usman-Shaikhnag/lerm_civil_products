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
    eln_ref = fields.Many2one('lerm.eln',string="Eln")


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

          

            if result.parameter.internal_id == 'fe045780-c893-4991-a463-650b73245786':
                # result.result_char = round(self.average,2)
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


                


