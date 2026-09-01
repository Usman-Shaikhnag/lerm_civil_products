# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Equipment(models.Model):
    # _name = 'lerm.equipment'
    _inherit = 'maintenance.equipment'
    _description = 'Laboratory Equipment'

    code = fields.Char(string='Code')
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
    range_least_count = fields.Char('Range And Least count')
    name_address_calibration_lab = fields.Char('Name & Address of Calibration Laboratory')
    calibration_method = fields.Char('Calibration Method/procedure')
    calibration_ulr_no = fields.Char('Calibration Certificate No. (ULR Number)')
    calibration_certificate_no = fields.Char('Calibration Certificate No.')
    traceability_certificate_no_valid_date = fields.Char('Traceability: (Certificate no /valid date)')
    traceability_nabl_certificate = fields.Char('Traceability: (NABL logo certificate No)')
    last_calibration_date = fields.Date('Date of Last Calibration')
    calibration_due_date = fields.Date("Calibration Due Date")
    accuracy_status_defined = fields.Char('Status of Accuracy Defined (+/-)')
    accuracy_status_reported = fields.Char('Status of Accuracy Reported')
    fit_for_use = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ],string='Fit for Use', default='yes')


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
                'group': equipment.group.id if equipment.group else False,
                'range_least_count': line.range_least_count,
                'name_address_calibration_lab': line.name_address_calibration_lab,
                'calibration_method': line.calibration_method,
                'calibration_ulr_no': line.calibration_ulr_no,
                'calibration_certificate_no': line.calibration_certificate_no,
                'traceability_certificate_no_valid_date': line.traceability_certificate_no_valid_date,
                'traceability_nabl_certificate': line.traceability_nabl_certificate,
                'last_calibration_date': line.last_calibration_date,
                'calibration_due_date': line.calibration_due_date,
                'accuracy_status_defined': line.accuracy_status_defined,
                'accuracy_status_reported': line.accuracy_status_reported,
                'fit_for_use': line.fit_for_use,
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
    group = fields.Many2one('lerm_civil.group',string="Group")
    range_least_count = fields.Char('Range And Least count')
    name_address_calibration_lab = fields.Char('Name & Address of Calibration Laboratory')
    calibration_method = fields.Char('Calibration Method/procedure')
    calibration_ulr_no = fields.Char('Calibration Certificate No. (ULR Number)')
    calibration_certificate_no = fields.Char('Calibration Certificate No.')
    traceability_certificate_no_valid_date = fields.Char('Traceability: (Certificate no /valid date)')
    traceability_nabl_certificate = fields.Char('Traceability: (NABL logo certificate No)')
    last_calibration_date = fields.Date('Date of Last Calibration')
    calibration_due_date = fields.Date("Calibration Due Date")
    accuracy_status_defined = fields.Char('Status of Accuracy Defined (+/-)')
    accuracy_status_reported = fields.Char('Status of Accuracy Reported')
    fit_for_use = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ],string='Fit for Use', default='yes')


    _sql_constraints = [
        ('unique_category_code', 'unique(equipment)', 'The equipment must be unique!'),
    ]