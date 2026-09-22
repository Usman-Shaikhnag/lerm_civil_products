# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from pytz import timezone

class EquipmentSelectionWizard(models.TransientModel):
    _name = 'equipment.selection.wizard'
    _description = 'Equipment Selection Wizard'

    parameter_id = fields.Many2one('lerm.parameter.master', string='Parameter', required=True)
    parameter_result = fields.Many2one(
        'eln.parameters.result', 
        string='Equipment'
    )
    equipment_ids = fields.Many2many(
        'maintenance.equipment', 
        string='Available Equipments',
        compute='_compute_available_equipments'
    )
    selected_equipment_id = fields.Many2one(
        'maintenance.equipment', 
        string='Select Equipment',
        domain="[('id', 'in', equipment_ids)]"
    )
    machine_start_time = fields.Datetime(string='Start Time')
    machine_end_time = fields.Datetime(string='End Time')

    @api.depends('parameter_id')
    def _compute_available_equipments(self):
        for wizard in self:
            if wizard.parameter_id:
                wizard.equipment_ids = wizard.parameter_id.equipment_ids.filtered(
                    lambda e: e.lerm_equipment
                )
            else:
                wizard.equipment_ids = False

    def action_confirm(self):
        self.ensure_one()
        if not self.selected_equipment_id or not self.machine_start_time or not self.machine_end_time:
            raise UserError("Please select equipment and specify both start and end times")
            
        if self.machine_start_time >= self.machine_end_time:
            raise UserError("End time must be after start time")
            
        # Check for overlapping time slots
        overlapping_records = self.env['eln.parameters.result'].search([
            ('equipment_id', '=', self.selected_equipment_id.id),
            ('id', '!=', self.parameter_result.id if self.parameter_result else False),
            ('start_time', '<', self.machine_end_time),
            ('end_time', '>', self.machine_start_time)
        ])
        
        if overlapping_records:
            ist = timezone('Asia/Kolkata')

            raise UserError(
                f"Time slot conflicts with existing records for this equipment:\n"
                f"Existing: {overlapping_records[0].start_time.astimezone(ist).strftime('%Y-%m-%d %H:%M IST')} to {overlapping_records[0].end_time.astimezone(ist).strftime('%Y-%m-%d %H:%M IST')}\n"
                f"New: {self.machine_start_time.astimezone(ist).strftime('%Y-%m-%d %H:%M IST')} to {self.machine_end_time.astimezone(ist).strftime('%Y-%m-%d %H:%M IST')}"
            )
        
        self.parameter_result.write({
            "equipment_id":self.selected_equipment_id,
            "start_time":self.machine_start_time ,
            "end_time":self.machine_end_time
            })
            
        return {
            'type': 'ir.actions.act_window_close',
            'effect': {'fadeout': 'fast'}
        }