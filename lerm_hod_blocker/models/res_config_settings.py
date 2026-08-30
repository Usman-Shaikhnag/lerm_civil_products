from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    hod_blocker_enabled = fields.Boolean(
        string='Enable HOD Sample Allotment Popup',
        config_parameter='hod_blocker.enabled',
        default=False,
    )
    hod_blocker_check_interval_minutes = fields.Integer(
        string='Check Interval (minutes)',
        config_parameter='hod_blocker.check_interval_minutes',
        default=120,
    )
