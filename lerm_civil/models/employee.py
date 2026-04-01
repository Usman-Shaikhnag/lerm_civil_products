from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError


class EmployeeInherited(models.Model):
    _inherit = "hr.employee"

    signature = fields.Binary(string="Signature", attachment=True)
    signature_name = fields.Char(string="Signature Name")
    
    lab_ids = fields.Many2many('lerm.lab.master',string="Lab")
    company_ids = fields.Many2many('res.company', string='Companies')
    department_ids = fields.Many2many('hr.department', string='Departments')

    def write(self, vals):
        res = super().write(vals)
        if 'department_ids' in vals:
            self.env['ir.rule'].clear_caches()
        return res

