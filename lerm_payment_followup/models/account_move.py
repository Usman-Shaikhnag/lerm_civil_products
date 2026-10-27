from odoo import _, api, fields, models
from odoo.exceptions import AccessError

DISPUTE_REASONS = [
    ("rate", "Rate / Pricing"),
    ("result", "Test Result"),
    ("report", "Report Correction"),
    ("po", "PO / Work Order Missing"),
    ("duplicate", "Duplicate Invoice"),
    ("other", "Other"),
]


class AccountMove(models.Model):
    _inherit = "account.move"

    followup_disputed = fields.Boolean(string="Disputed", copy=False, tracking=True)
    followup_dispute_reason = fields.Selection(
        DISPUTE_REASONS, string="Dispute Reason", copy=False, tracking=True
    )
    followup_dispute_note = fields.Text(string="Dispute Note", copy=False)
    # Sent with payment reminders instead of the generated invoice PDF
    followup_invoice_copy = fields.Binary(string="Invoice Copy for Customer", attachment=True, copy=False)
    followup_invoice_copy_name = fields.Char(string="Invoice Copy Filename", copy=False)
    followup_days_overdue = fields.Integer(
        string="Days Overdue", compute="_compute_followup_days_overdue"
    )

    def _compute_followup_days_overdue(self):
        today = fields.Date.context_today(self)
        for move in self:
            due = move.invoice_date_due or move.invoice_date
            move.followup_days_overdue = max((today - due).days, 0) if due else 0

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves._followup_check_credit_limit()
        return moves

    def write(self, vals):
        res = super().write(vals)
        if "partner_id" in vals:
            self._followup_check_credit_limit()
        return res

    def action_post(self):
        # Lines may have changed since the invoice was created
        self._followup_check_credit_limit()
        return super().action_post()

    def _followup_check_credit_limit(self):
        # Credit notes and posted invoices are never blocked; the invoice's own amount counts
        for invoice in self.filtered(lambda m: m.move_type == "out_invoice" and m.state == "draft"):
            invoice.partner_id._followup_check_credit_limit(_("invoice"), invoice.amount_total_signed)

    @api.onchange("partner_id")
    def _onchange_partner_id_followup_credit(self):
        if self.move_type == "out_invoice" and self.partner_id:
            message = self.partner_id._followup_credit_hold_message(_("invoice"), self.amount_total_signed)
            if message:
                return {"warning": {"title": _("Credit Limit Exceeded"), "message": message}}

    def action_followup_mark_disputed(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Mark Invoice Disputed"),
            "res_model": "lerm.followup.log.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": self.commercial_partner_id.id,
                "default_action": "note",
                "default_outcome": "disputed",
                "default_invoice_ids": [self.id],
            },
        }

    def action_followup_resolve_dispute(self):
        if not self.env.user.has_group("lerm_payment_followup.group_followup_manager"):
            raise AccessError(_("Only a Payment Follow-up Manager can resolve disputes."))
        disputed = self.filtered("followup_disputed")
        for move in disputed:
            move.commercial_partner_id._followup_log(
                "dispute_resolved",
                invoices=move,
                note=_("Dispute resolved (%s).", dict(DISPUTE_REASONS).get(move.followup_dispute_reason, "")),
            )
        disputed.sudo().write({"followup_disputed": False, "followup_dispute_reason": False})
