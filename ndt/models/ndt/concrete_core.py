from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class ConcreteCore(models.Model):
    _name = "ndt.concrete.core"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Concrete Core")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    temperature = fields.Float("Temperature °C")
    child_lines = fields.One2many('ndt.concrete.core.line','parent_id',string="Parameter")
    average = fields.Float(string="Average Compressive Strength in Mpa",compute="_compute_average")
    structure = fields.Char("Structure")

    notes = fields.One2many('ndt.concrete.core.notes','parent_id',string="Notes")


    




    @api.depends('child_lines.final_cube_strength')
    def _compute_average(self):
        for record in self:
            total_value = sum(record.child_lines.mapped('final_cube_strength'))
            record.average = round((total_value / len(record.child_lines) if record.child_lines else 0.0),2)

   
    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(ConcreteCore, self).create(vals)
        record.parameter_id.write({'model_id':record.id})
        return record

class ConcreteCoreLine(models.Model):
    _name = "ndt.concrete.core.line"
    parent_id = fields.Many2one('ndt.concrete.core',string="Parent Id")
    member = fields.Char(string="Member / Element Type")
    date_testing = fields.Date(string="Date of Testing")
    dia = fields.Float(string="dia d mm")
    length = fields.Float(string="length h mm")
    ld = fields.Float(string="L/D",compute="_compute_ld")
    area = fields.Float(string="Area mm2",compute="_compute_area")
    dry = fields.Float(string="Dry wt kg",digits=(16,3))
    failure_load = fields.Float(string="Failure Load kN")
    measured_comp_str = fields.Float(string="Measured compressive strength, Mpa",compute="_compute_measured_compressive_strength")
    core_factor_ld = fields.Float(string="Corr Factor as per IS-516(If L/D ratio ≤ Two)",compute="_compute_core_ld",digits=(16,3))
    core_factor_dia = fields.Float(string="Corr Factor as per IS-516(If Dia is 75±5 MM Or <70MM)",compute="_compute_core_dia")
    core_factor_cube = fields.Float(string="Corr Factor for Eqv.150 mm Cube Strength, as per IS 516",default=1.25)
    final_cube_strength = fields.Float(string="Final Eqv.150 mm Cube Strength, Mpa",compute="_compute_final_cube_strength",store=True)
    


    @api.depends('dia')
    def _compute_area(self):
        for record in self:
            try:
                record.area = (3.14/4)*record.dia*record.dia
            except ZeroDivisionError:
                record.area = 0

    @api.depends('dia','length')
    def _compute_ld(self):
        for record in self:
            try:
                record.ld = record.length / record.dia
            except ZeroDivisionError:
                # print("From Zero ld")
                
                record.ld = 0


    @api.depends('area','failure_load')
    def _compute_measured_compressive_strength(self):
        for record in self:
            try:
                record.measured_comp_str = (record.failure_load / record.area )*1000
            except ZeroDivisionError:
                print("From Zero cs")
                record.measured_comp_str = 0

    @api.depends('ld')
    def _compute_core_ld(self):
        for record in self:
            record.core_factor_ld = 0.11*record.ld  + 0.78

    @api.depends('dia')
    def _compute_core_dia(self):
        for record in self:
            if record.dia < 70:
                record.core_factor_dia = 1.06
            elif record.dia > 70 and record.dia < 80 :
                record.core_factor_dia = 1.03
            else:
                record.core_factor_dia = 1.0

    @api.depends('core_factor_ld','core_factor_dia','measured_comp_str','core_factor_cube')
    def _compute_final_cube_strength(self):
        for record in self:
            final_cube_strength = record.measured_comp_str * record.core_factor_dia * record.core_factor_ld * record.core_factor_cube
            print("Final Cube Strength",final_cube_strength)
            record.final_cube_strength = final_cube_strength



class ConcreteCoreNotes(models.Model):
    _name = "ndt.concrete.core.notes"

    parent_id = fields.Many2one('ndt.concrete.core',string="Parent Id")
    notes = fields.Char("Notes")