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
    
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.name} ({record.code})" if record.code else record.name
    
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
    
    
    
    