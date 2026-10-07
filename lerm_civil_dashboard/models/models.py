from odoo import fields, models


class Discipline(models.Model):
    _inherit = "lerm_civil.discipline"

    # Departments (as assigned on employees) that work under this discipline
    department_ids = fields.Many2many(
        'hr.department',
        'lerm_civil_discipline_hr_department_rel',
        'discipline_id',
        'department_id',
        string="Departments",
    )
