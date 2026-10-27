from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..models.account_move import DISPUTE_REASONS


class FollowupLogWizard(models.TransientModel):
    _name = "lerm.followup.log.wizard"
    _description = "Log Payment Follow-up"

    partner_id = fields.Many2one("res.partner", string="Customer", required=True, readonly=True)
    currency_id = fields.Many2one(related="partner_id.currency_id")
    action = fields.Selection(
        [("call", "Phone Call"), ("meeting", "Meeting"), ("note", "Note")],
        string="Type",
        required=True,
        default="call",
    )
    outcome = fields.Selection(
        [
            ("reached", "Reached"),
            ("no_answer", "No Answer"),
            ("promised", "Promised to Pay"),
            ("disputed", "Disputed"),
            ("other", "Other"),
        ],
        required=True,
        default="reached",
    )
    note = fields.Text()
    promise_date = fields.Date(string="Promised Payment Date")
    promise_amount = fields.Monetary(
        string="Promised Amount",
        currency_field="currency_id",
        compute="_compute_promise_amount",
        store=True,
        readonly=False,
    )
    invoice_ids = fields.Many2many("account.move", string="Invoices")
    dispute_reason = fields.Selection(DISPUTE_REASONS, string="Dispute Reason")
    level_id = fields.Many2one(
        "lerm.followup.level", string="Follow-up Step", compute="_compute_level_id", store=True, readonly=False
    )
    advance_level = fields.Boolean(
        string="Mark Step as Done",
        compute="_compute_advance_level",
        store=True,
        readonly=False,
        help="Move the customer to this follow-up level.",
    )

    @api.depends("partner_id")
    def _compute_promise_amount(self):
        for wizard in self:
            wizard.promise_amount = wizard.partner_id.followup_total_overdue

    @api.depends("partner_id")
    def _compute_level_id(self):
        for wizard in self:
            level = wizard.partner_id.followup_next_level_id
            wizard.level_id = level if level.action_type in ("call", "manual") else False

    @api.depends("level_id", "outcome")
    def _compute_advance_level(self):
        for wizard in self:
            wizard.advance_level = bool(wizard.level_id) and wizard.outcome != "no_answer"

    def action_confirm(self):
        self.ensure_one()
        partner = self.partner_id
        today = fields.Date.context_today(self)
        log_vals = {}
        if self.outcome == "promised":
            if not self.promise_date or self.promise_date < today:
                raise UserError(_("Enter a promised payment date from today onwards."))
            if self.currency_id.compare_amounts(self.promise_amount, 0) <= 0:
                raise UserError(_("Enter the promised amount."))
            log_vals = {"promise_date": self.promise_date, "promise_amount": self.promise_amount}
        if self.outcome == "disputed" and (not self.invoice_ids or not self.dispute_reason):
            raise UserError(_("Select the disputed invoices and the reason."))

        # Advance first: it closes a broken promise, which must not clear a new one
        if self.advance_level and self.level_id:
            partner._followup_advance(self.level_id)
        if self.outcome == "promised":
            partner.sudo().write({
                "followup_promise_date": self.promise_date,
                "followup_promise_amount": self.promise_amount,
                "followup_promise_base_due": partner.followup_total_due,
            })
        if self.outcome == "disputed":
            self.invoice_ids.sudo().write({
                "followup_disputed": True,
                "followup_dispute_reason": self.dispute_reason,
                "followup_dispute_note": self.note,
            })

        partner._followup_log(
            self.action,
            level=self.level_id,
            outcome=self.outcome,
            invoices=self.invoice_ids,
            note=self.note,
            **log_vals,
        )
        if self.outcome != "no_answer":
            partner._followup_close_activities(self.note)
        return {"type": "ir.actions.act_window_close"}
