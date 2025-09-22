from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError


class EmployeeInherited(models.Model):
    _inherit = "hr.employee"

    signature = fields.Binary(string="Signature", attachment=True)
    signature_name = fields.Char(string="Signature Name")