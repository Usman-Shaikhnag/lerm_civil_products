from odoo import api, fields, models

class ResUsers(models.Model):
    _inherit = 'res.users'

    department_ids = fields.Many2many(
        related='employee_id.department_ids',
        string="Departments",
        readonly=False,
    )

