from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    technician_blocker_enabled = fields.Boolean(
        string='Enable Technician New Work Popup',
        config_parameter='technician_blocker.enabled',
        default=False,
    )
    technician_blocker_due_enabled = fields.Boolean(
        string='Enable Due-Date Popup',
        config_parameter='technician_blocker.due_enabled',
        default=False,
    )
    technician_blocker_window_times = fields.Char(
        string='Notification Windows (HH:MM, comma separated)',
        config_parameter='technician_blocker.window_times',
        default='13:00,15:00,18:00',
        help='Daily times at which each technician is sent a consolidated '
             'digest of their new work. Example: 13:00,15:00,18:00',
    )
    technician_blocker_morning_time = fields.Char(
        string='Morning Notification Time',
        config_parameter='technician_blocker.morning_time',
        default='09:00',
        help='Daily time at which each technician is sent the report '
             'due-tomorrow / due-today notifications. Example: 09:00',
    )
    technician_blocker_tz = fields.Char(
        string='Notification Timezone',
        config_parameter='technician_blocker.tz',
        help='IANA timezone in which the windows are interpreted '
             '(e.g. Asia/Kolkata). Empty uses the running user timezone.',
    )
