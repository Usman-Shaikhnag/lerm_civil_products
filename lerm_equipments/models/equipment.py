# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date

class Equipment(models.Model):
    # _name = 'lerm.equipment'
    _inherit = 'maintenance.equipment'
    _description = 'Laboratory Equipment'

    code = fields.Char(string='Code')
    make = fields.Char(string='Make')
    available_from = fields.Float(string='Available From')
    available_to = fields.Float(string='Available To')
    parameter_ids = fields.Many2many('lerm.parameter.master', 'equipment_parameters_rel', 'equipment_id', 'parameter_id', string='Parameters')
    lerm_equipment = fields.Boolean(string='LERM Equipment')

    group = fields.Many2one('lerm_civil.group',string="Group")

    calibration_lines = fields.One2many('equipment.calibration.lines','parent_id',string="Calibration Data")

    fit_for_use = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ],string='Fit for Use', default='yes')


    
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.name} ({record.code})" if record.code else record.name

class CalibrationLines(models.Model):
    _name ="equipment.calibration.lines"

    parent_id = fields.Many2one('maintenance.equipment')
    equipment_name = fields.Char('NAME OF EQUIPMENT', related='parent_id.name', store=True)
    make = fields.Char('MAKE', related='parent_id.make', store=True)
    equipment_id_no = fields.Char('Equipment ID No', related='parent_id.code', store=True)
    serial_number = fields.Char('Serial muber', related='parent_id.serial_no', store=True)
    equipment_range = fields.Char('Range')
    date_of_calibration = fields.Date('Date of Calibration')
    mpe_accuracy = fields.Char('MPE/Accuracy')
    least_count = fields.Char('Least Count')
    calibration_certificate_no = fields.Char('Calibration Certificate Number')
    calibration_due_date = fields.Date("Due Date of Calibration")
    calibrated_by = fields.Char('Calibrated By')

    due_in_days_int  = fields.Integer(string="Due in Day(s)",compute="_compute_due_in_days",store=True)

    @api.depends('calibration_due_date')
    def _compute_due_in_days(self):
        today_date = date.today()
        for record in self:
            if record.calibration_due_date:
                record.due_in_days_int  = (record.calibration_due_date - today_date).days
            else:
                record.due_in_days_int  = False

    @api.model
    def create(self, vals):
        record = super(CalibrationLines, self).create(vals)
        record._update_equipment_register()
        return record

    def write(self, vals):
        res = super(CalibrationLines, self).write(vals)
        for rec in self:
            rec._update_equipment_register()
        return res

    # ---------------------------
    # Helper function
    # ---------------------------
    def _update_equipment_register(self):
        for line in self:
            if not line.parent_id:
                continue

            EquipmentRegister = self.env['equipment.register']
            equipment = line.parent_id

            # Check if a register already exists
            register = EquipmentRegister.search([('equipment', '=', equipment.id)], limit=1)

            register_vals = {
                'equipment': equipment.id,
                'code': equipment.code,
                'make': equipment.make,
                'serial_no': equipment.serial_no,
                'group': equipment.group.id if equipment.group else False,
                'equipment_range': line.equipment_range,
                'date_of_calibration': line.date_of_calibration,
                'mpe_accuracy': line.mpe_accuracy,
                'least_count': line.least_count,
                'calibration_certificate_no': line.calibration_certificate_no,
                'calibration_due_date': line.calibration_due_date,
                'calibrated_by': line.calibrated_by,
                'due_in_days_int': line.due_in_days_int,
            }

            if register:
                register.write(register_vals)
            else:
                EquipmentRegister.create(register_vals)
    
class ParameterMaster(models.Model):
    _inherit = 'lerm.parameter.master'
    
    requires_equipment = fields.Boolean(string='Requires Equipment')
    equipment_ids = fields.Many2many('maintenance.equipment', 'equipment_parameters_rel', 'parameter_id', 'equipment_id', string='Equipments')

class ELNParametersResultEquipment(models.Model):
    _inherit = 'eln.parameters.result'
    
    # equipment_id = fields.Many2one('lerm.equipment', string='Equipment', required=True)
    start_time = fields.Datetime(string='Start Time')
    end_time = fields.Datetime(string='End Time')
    requires_equipment = fields.Boolean(string='Requires Equipment',related="parameter.requires_equipment")
    equipment_id = fields.Many2one(
        'maintenance.equipment', 
        string='Equipment'
    )

    def action_open_equipment_wizard(self):
        return {
            'name': 'Select Equipment',
            'type': 'ir.actions.act_window',
            'res_model': 'equipment.selection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_parameter_result': self.id,
                'default_parameter_id': self.parameter.id,
                'default_start_time': self.start_time,
                'default_end_time': self.end_time
            }
        }
    
    
    
class EquipmentRegister(models.Model):
    _name = 'equipment.register' 
    _rec_name = 'equipment'

    equipment = fields.Many2one('maintenance.equipment',string="Equipment")

    code = fields.Char(string='Code')
    make = fields.Char(string='Make')
    serial_no = fields.Char(string='Serial Number')
    group = fields.Many2one('lerm_civil.group',string="Group")
    equipment_range = fields.Char('Range')
    date_of_calibration = fields.Date('Date of Calibration')
    mpe_accuracy = fields.Char('MPE/Accuracy')
    least_count = fields.Char('Least Count')
    calibration_certificate_no = fields.Char('Calibration Certificate Number')
    calibration_due_date = fields.Date("Due Date of Calibration")
    calibrated_by = fields.Char('Calibrated By')
    due_in_days_int  = fields.Integer(string="Due in Day(s)")

    _sql_constraints = [
        ('unique_category_code', 'unique(equipment)', 'The equipment must be unique!'),
    ]