from odoo import models, fields, api


class AccountMoveInheritedLerm(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        self.invoice_user_id = self.partner_id.user_id.id
        super(AccountMoveInheritedLerm, self).action_post()
        for record in self.invoice_line_ids.report_no1:
            if record.invoice_number != self:
                record.sudo().write({'invoice_number': self.id})
            record.sudo()._compute_invoice_status()

    def button_draft(self):
        super(AccountMoveInheritedLerm, self).button_draft()
        for record in self.invoice_line_ids.report_no1:
            if not record.invoice_number:
                record.sudo().write({'invoice_number': self.id})
            record.sudo()._compute_invoice_status()
