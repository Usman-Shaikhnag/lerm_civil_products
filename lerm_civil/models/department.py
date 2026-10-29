from odoo import models


class DepartmentInherited(models.Model):
    _inherit = "hr.department"

    def _compute_total_employee(self):
        # Employees are assigned through hr.employee.department_ids (the native
        # department_id is hidden), so count membership through the m2m.
        Employee = self.env['hr.employee'].sudo()
        for department in self:
            department.total_employee = Employee.search_count([
                '|',
                ('department_ids', 'in', department.id),
                ('department_id', '=', department.id),
            ])
