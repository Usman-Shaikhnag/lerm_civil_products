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

    notes = fields.One2many('ndt.rebound.hammer.notes','parent_id',string="Notes")


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


    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(ReboundHammer, self).create(vals)
        record.parameter_id.write({'model_id':record.id})
        return record

class CarbonationnLine(models.Model):
    _name = "ndt.rebound.hammer.line"
    parent_id = fields.Many2one('ndt.rebound.hammer',string="Parent Id")
    element = fields.Char(string="Member / Element Type")
    location = fields.Char(string="Location")
    f1 = fields.Integer(string="1")
    f2 = fields.Integer(string="2")
    f3 = fields.Integer(string="3")
    f4 = fields.Integer(string="4")
    f5 = fields.Integer(string="5")
    f6 = fields.Integer(string="6")
    # f7 = fields.Integer(string="7")
    # f8 = fields.Integer(string="8")
    # f9 = fields.Integer(string="9")
    # f10 = fields.Integer(string="10")
    avg = fields.Float(string="Average" ,compute="_compute_average")
    mpa = fields.Float(string="Mpa")
    direction = fields.Selection([
        ('horizontal', 'Horizontal'),
        ('vertical_up', 'Vertical Up'), 
        ('vertical_down', 'Vertical Down')], string='Direction')
    

    # @api.depends('f1','f2','f3','f4','f5','f6','f7','f8','f9','f10')
    # def _compute_average(self):
    #     for record in self:
    #         values = []
    #         median = 0
    #         median_first = 0
    #         median_third = 0
    #         values.append(record.f1)
    #         values.append(record.f2)
    #         values.append(record.f3)
    #         values.append(record.f4)
    #         values.append(record.f5)
    #         values.append(record.f6)
    #         values.append(record.f7)
    #         values.append(record.f8)
    #         values.append(record.f9)
    #         values.append(record.f10)

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
    #         lower_bound = median_first - 1.5*iqr
    #         upper_bound = median_third + 1.5*iqr

    #         filtered_array = [x for x in values if lower_bound <= x <= upper_bound]

    #         record.avg = sum(filtered_array) / len(filtered_array)


    @api.depends('f1', 'f2', 'f3', 'f4', 'f5', 'f6')
    def _compute_average(self):
        for record in self:
            values = [record.f1, record.f2, record.f3, record.f4, record.f5, record.f6]

            sorted_array = sorted(values)
            midpoint = len(sorted_array) // 2
            if len(sorted_array) % 2 == 0:
                median = (sorted_array[midpoint - 1] + sorted_array[midpoint]) / 2.0
            else:
                median = sorted_array[midpoint]

            first_quartile = sorted_array[:midpoint]
            third_quartile = sorted_array[midpoint:]
            midpoint = len(first_quartile) // 2
            if len(first_quartile) % 2 == 0:
                median_first = (first_quartile[midpoint - 1] + first_quartile[midpoint]) / 2.0
            else:
                median_first = first_quartile[midpoint]
            midpoint = len(third_quartile) // 2
            if len(third_quartile) % 2 == 0:
                median_third = (third_quartile[midpoint - 1] + third_quartile[midpoint]) / 2.0
            else:
                median_third = third_quartile[midpoint]
            iqr = median_third - median_first
            lower_bound = median_first - 1.5 * iqr
            upper_bound = median_third + 1.5 * iqr

            filtered_array = [x for x in values if lower_bound <= x <= upper_bound]

            record.avg = sum(filtered_array) / len(filtered_array)
                


class ReboundHammerNotes(models.Model):
    _name = "ndt.rebound.hammer.notes"

    parent_id = fields.Many2one('ndt.rebound.hammer',string="Parent Id")
    notes = fields.Char("Notes")