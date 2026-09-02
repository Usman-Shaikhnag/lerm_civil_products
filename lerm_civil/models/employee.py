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

    # ── LERM Access Rights (synced with res.users) ──────────────
    lerm_group_ids = fields.Many2many(
        'res.groups',
        string="LERM Access Rights",
        compute='_compute_lerm_group_ids',
        inverse='_inverse_lerm_group_ids',
        store=False,
        domain=lambda self: [
            ('category_id', '=',
             self.env.ref('lerm_civil.kes_lerm_access_categories', raise_if_not_found=False).id)
        ],
        help="Select the LERM security groups for this employee. "
             "Changes are synced to the linked user automatically.",
    )

    @api.depends('user_id', 'user_id.groups_id')
    def _compute_lerm_group_ids(self):
        """Read the LERM groups currently assigned to the linked user."""
        lerm_category = self.env.ref(
            'lerm_civil.kes_lerm_access_categories', raise_if_not_found=False
        )
        for emp in self:
            if emp.user_id and lerm_category:
                emp.lerm_group_ids = emp.user_id.groups_id.filtered(
                    lambda g: g.category_id == lerm_category
                )
            else:
                emp.lerm_group_ids = False

    def _inverse_lerm_group_ids(self):
        """Write the selected LERM groups back to the linked user."""
        lerm_category = self.env.ref(
            'lerm_civil.kes_lerm_access_categories', raise_if_not_found=False
        )
        if not lerm_category:
            return
        for emp in self:
            if not emp.user_id:
                continue
            # Current LERM groups on the user
            current_lerm = emp.user_id.groups_id.filtered(
                lambda g: g.category_id == lerm_category
            )
            # Desired LERM groups from the employee form
            desired_lerm = emp.lerm_group_ids

            to_remove = current_lerm - desired_lerm
            to_add = desired_lerm - current_lerm

            if to_remove or to_add:
                cmds = []
                for g in to_remove:
                    cmds.append((3, g.id))     # unlink
                for g in to_add:
                    cmds.append((4, g.id))     # link
                emp.user_id.sudo().write({'groups_id': cmds})