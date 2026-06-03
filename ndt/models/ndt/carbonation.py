from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class CarbonationTest(models.Model):
    _name = "ndt.carbonation.test"
    _inherit = "lerm.eln"
    _rec_name = "name"

    
    name = fields.Char("Name",default="Carbonation Test")
    temperature = fields.Float("Temperature °C")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines = fields.One2many('ndt.carbonation.test.line','parent_id',string="Parameter")
    average = fields.Float(string="Average of Depth of Carbonation in mm",compute="_compute_average")
    min_depth = fields.Float(string="Min mm",compute="_compute_min_max")
    max_depth = fields.Float(string="Max mm",compute="_compute_min_max")
    structure = fields.Char("Structure")

    notes = fields.One2many('ndt.carbonation.test.notes','parent_id',string="Notes")
    eln_ref = fields.Many2one('lerm.eln',string="Eln")

    

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

          

            if result.parameter.internal_id == '889d7c7a-1d9e-42c9-a3db-e3d29551cb26':
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



    @api.depends('child_lines.depth')
    def _compute_average(self):
        for record in self:
            total_value = sum(record.child_lines.mapped('depth'))
            self.average = float(round(total_value / len(record.child_lines),2)) if record.child_lines else 0.0

    @api.depends('child_lines.depth')
    def _compute_min_max(self):
        for record in self:
            depth_values = record.child_lines.mapped('depth')
            # record.average = sum(depth_values) / len(depth_values) if depth_values else 0.0
            min_depth = round(min(depth_values, default=0.0),2)
            record.min_depth = min_depth
            max_depth = round(max(depth_values, default=0.0),2)
            record.max_depth = max_depth

    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(CarbonationTest, self).create(vals)
        record.parameter_id.write({'model_id':record.id})
        return record

class CarbonationnLine(models.Model):
    _name = "ndt.carbonation.test.line"
    parent_id = fields.Many2one('ndt.carbonation.test',string="Parent Id")
    member = fields.Char(string="Member / Element Type")
    level = fields.Char(string="Level")
    location = fields.Char(string="Location")
    condition_of_concrete = fields.Selection([
        ('carbonated', 'Carbonated'),
        ('uncarbonated', 'Uncarbonated')
    ], string='Condition of Concrete',default='carbonated')
    depth = fields.Float(string='Depth of Carbonation in mm')
    


                


class CarbonationTestNotes(models.Model):
    _name = "ndt.carbonation.test.notes"

    parent_id = fields.Many2one('ndt.carbonation.test',string="Parent Id")
    notes = fields.Char("Notes")