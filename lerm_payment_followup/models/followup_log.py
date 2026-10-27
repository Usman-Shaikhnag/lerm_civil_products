from odoo import fields, models

LOG_ACTIONS = [
    ("email", "Email"),
    ("call", "Phone Call"),
    ("meeting", "Meeting"),
    ("note", "Note"),
    ("task", "Task Scheduled"),
    ("dispute_resolved", "Dispute Resolved"),
    ("promise_kept", "Promise Kept"),
    ("reset", "Reset"),
]

LOG_OUTCOMES = [
    ("sent", "Sent"),
    ("reached", "Reached"),
    ("no_answer", "No Answer"),
    ("promised", "Promised to Pay"),
    ("disputed", "Disputed"),
    ("other", "Other"),
]


class FollowupLog(models.Model):
    _name = "lerm.followup.log"
    _description = "Payment Follow-up Log"
    _order = "date desc, id desc"
    _rec_name = "partner_id"

    date = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True)
    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True, ondelete="cascade", index=True
    )
    responsible_id = fields.Many2one(
        related="partner_id.followup_responsible_id", string="Responsible", store=True
    )
    level_id = fields.Many2one("lerm.followup.level", string="Step", ondelete="set null")
    action = fields.Selection(LOG_ACTIONS, required=True)
    outcome = fields.Selection(LOG_OUTCOMES)
    invoice_ids = fields.Many2many("account.move", string="Invoices")
    note = fields.Text()
    currency_id = fields.Many2one(related="partner_id.currency_id")
    promise_date = fields.Date()
    promise_amount = fields.Monetary(currency_field="currency_id")
    user_id = fields.Many2one(
        "res.users", string="Done By", default=lambda self: self.env.user
    )
    auto = fields.Boolean(string="Automatic")
