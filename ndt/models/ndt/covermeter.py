from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class CoverMeter(models.Model):
    _name = "ndt.cover.meter"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Cover Depth")
    # name = fields.Char("Name",compute="_compute_name")

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    
    temperature = fields.Float("Temperature °C")
    child_lines = fields.One2many('ndt.cover.meter.line','parent_id',string="Parameter")
    average = fields.Float(string='Average (mm)', digits=(16, 2), compute='_compute_average')
    average_min = fields.Float(string='Average Min (mm)', digits=(16, 2), compute='_compute_average')
    average_max = fields.Float(string='Average Max (mm)', digits=(16, 2), compute='_compute_average')
    notes = fields.One2many('ndt.cover.meter.notes','parent_id',string="Notes")
    structure = fields.Char("Structure")





    # @api.depends('parameter_id')
    # def _compute_name(self):
    #     for record in self:
    #         try:
    #             record.name = record.parameter_id.parameter.parameter_name
    #         except:
    #             record.name = "Cover Depth"


    @api.depends('child_lines.cover')
    def _compute_average(self):
        for record in self:
            total_cover = sum(record.child_lines.mapped('cover'))
            num_records = len(record.child_lines)

            if num_records > 0:
                average = total_cover / num_records
                average = round(average,2)
                record.average = average
                cover_values = record.child_lines.mapped('cover')
                average_min = round(min(cover_values),2)
                record.average_min = average_min
                average_max = max(cover_values)
                record.average_max = average_max
            else:
                record.average = 0.0
                record.average_min = 0.0
                record.average_max = 0.0


    eln_ref = fields.Many2one('lerm.eln',string="Eln")

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            if result.parameter.internal_id == 'f2bf001e-675f-44b0-8fa6-ac002a201826':
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


    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(CoverMeter, self).create(vals)
        record.parameter_id.write({'model_id':record.id})
        return record
    
    
    

class CoverMeterLine(models.Model):
    _name = "ndt.cover.meter.line"
    parent_id = fields.Many2one('ndt.cover.meter',string="Parent Id")
    member = fields.Char(string="Element Type")
    location = fields.Char(string="Location")
    level = fields.Char(string="Level")
    cover = fields.Float(string='Cover in mm',digits=(16, 2))
    

class CoverMeterNotes(models.Model):
    _name = "ndt.cover.meter.notes"

    parent_id = fields.Many2one('ndt.cover.meter',string="Parent Id")
    notes = fields.Char("Notes")
                


