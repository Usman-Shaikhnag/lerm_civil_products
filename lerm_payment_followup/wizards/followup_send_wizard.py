from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FollowupSendWizard(models.TransientModel):
    _name = "lerm.followup.send.wizard"
    _description = "Send Payment Reminder"

    partner_id = fields.Many2one("res.partner", string="Customer", required=True, readonly=True)
    level_id = fields.Many2one(
        "lerm.followup.level",
        string="Follow-up Step",
        compute="_compute_level_id",
        store=True,
        readonly=False,
        precompute=True,
        domain=[("action_type", "=", "email")],
    )
    recipient_ids = fields.Many2many(
        "res.partner", string="Recipients", compute="_compute_recipients", store=True, readonly=False, precompute=True
    )
    invoice_ids = fields.Many2many(
        "account.move", string="Invoices", compute="_compute_recipients", store=True, readonly=False, precompute=True
    )
    subject = fields.Char(compute="_compute_content", store=True, readonly=False, precompute=True, required=True)
    body = fields.Html(compute="_compute_content", store=True, readonly=False, precompute=True)
    attach_invoices = fields.Boolean(
        string="Attach Invoice PDFs", compute="_compute_content", store=True, readonly=False, precompute=True
    )
    advance_level = fields.Boolean(
        string="Mark Step as Done",
        compute="_compute_content",
        store=True,
        readonly=False,
        precompute=True,
        help="Move the customer to this follow-up level after sending.",
    )

    @api.depends("partner_id")
    def _compute_level_id(self):
        for wizard in self:
            level = wizard.partner_id.followup_next_level_id
            wizard.level_id = level if level.action_type == "email" else False

    @api.depends("partner_id")
    def _compute_recipients(self):
        for wizard in self:
            partner = wizard.partner_id
            wizard.recipient_ids = partner._followup_default_recipients() if partner else False
            wizard.invoice_ids = partner.sudo()._followup_open_invoices() if partner else False

    @api.depends("partner_id", "level_id")
    def _compute_content(self):
        default_template = self.env.ref("lerm_payment_followup.mail_template_followup_reminder")
        for wizard in self:
            if not wizard.partner_id:
                continue
            template = wizard.level_id.mail_template_id or default_template
            wizard.subject, wizard.body = wizard.partner_id._followup_render_template(template)
            wizard.attach_invoices = wizard.level_id.attach_invoices if wizard.level_id else True
            wizard.advance_level = bool(wizard.level_id) and wizard.level_id == wizard.partner_id.followup_next_level_id

    def action_send(self):
        self.ensure_one()
        if not self.recipient_ids:
            raise UserError(_("Add at least one recipient."))
        missing = self.recipient_ids.filtered(lambda p: not p.email)
        if missing:
            raise UserError(_("These recipients have no email address: %s", ", ".join(missing.mapped("display_name"))))
        self.partner_id._followup_send_email(
            self.level_id,
            self.recipient_ids,
            self.subject,
            self.body,
            self.invoice_ids,
            attach_invoices=self.attach_invoices,
            advance=self.advance_level,
        )
        self.partner_id._followup_close_activities(_("Payment reminder sent."))
        return {"type": "ir.actions.act_window_close"}
