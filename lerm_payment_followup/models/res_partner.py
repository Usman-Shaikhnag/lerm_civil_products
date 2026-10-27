import logging
from datetime import timedelta

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import format_amount

_logger = logging.getLogger(__name__)

# Activities created by follow-up carry this prefix so logging an outcome can close them
ACTIVITY_PREFIX = "Payment follow-up: "

FOLLOWUP_STATES = [
    ("none", "No Action Needed"),
    ("waiting", "Waiting"),
    ("action", "Action Due"),
    ("promise", "Promised to Pay"),
    ("broken", "Broken Promise"),
    ("final", "Final Level Reached"),
]

STATUS_FIELDS = [
    "followup_total_due",
    "followup_total_overdue",
    "followup_oldest_due_date",
    "followup_next_level_id",
    "followup_next_date",
    "followup_state",
]


class ResPartner(models.Model):
    _inherit = "res.partner"

    followup_invoice_ids = fields.One2many(
        "account.move",
        "commercial_partner_id",
        string="Customer Invoices",
        domain=[("move_type", "in", ("out_invoice", "out_refund")), ("state", "=", "posted")],
    )
    followup_open_invoice_ids = fields.Many2many(
        "account.move", string="Open Invoices", compute="_compute_followup_invoices"
    )
    followup_disputed_invoice_ids = fields.Many2many(
        "account.move", string="Disputed Invoices", compute="_compute_followup_invoices"
    )
    followup_disputed_amount = fields.Monetary(
        string="Disputed Amount", compute="_compute_followup_invoices", currency_field="currency_id"
    )
    followup_level_id = fields.Many2one(
        "lerm.followup.level",
        string="Follow-up Level",
        copy=False,
        tracking=True,
        ondelete="restrict",
        help="Last follow-up step done for this customer.",
    )
    followup_last_date = fields.Date(string="Last Follow-up", copy=False)
    followup_next_level_id = fields.Many2one(
        "lerm.followup.level", string="Next Step", compute="_compute_followup_status", store=True
    )
    followup_next_date = fields.Date(
        string="Next Action Date", compute="_compute_followup_status", store=True
    )
    followup_state = fields.Selection(
        FOLLOWUP_STATES, string="Follow-up Status", compute="_compute_followup_status", store=True
    )
    followup_total_due = fields.Monetary(
        string="Follow-up Total Due", compute="_compute_followup_status", store=True, currency_field="currency_id"
    )
    followup_total_overdue = fields.Monetary(
        string="Follow-up Total Overdue", compute="_compute_followup_status", store=True, currency_field="currency_id"
    )
    followup_oldest_due_date = fields.Date(
        string="Oldest Due Date", compute="_compute_followup_status", store=True
    )
    followup_responsible_id = fields.Many2one(
        "res.users",
        string="Follow-up Responsible",
        compute="_compute_followup_responsible_id",
        store=True,
        readonly=False,
        tracking=True,
    )
    followup_exclude_auto = fields.Boolean(
        string="Exclude from Automatic Follow-up",
        help="The daily automatic run skips this customer. Manual follow-up still works.",
    )
    followup_promise_date = fields.Date(string="Promised Payment Date", copy=False, tracking=True)
    followup_promise_amount = fields.Monetary(
        string="Promised Amount", copy=False, currency_field="currency_id"
    )
    # Total due when the promise was made, so a later payment can be matched against it
    followup_promise_base_due = fields.Monetary(copy=False, currency_field="currency_id")
    followup_log_ids = fields.One2many(
        "lerm.followup.log",
        "partner_id",
        string="Follow-up Log",
        groups="lerm_payment_followup.group_followup_user",
    )
    followup_credit_block = fields.Boolean(
        string="Block on Credit Limit",
        tracking=True,
        help="Block new invoices and SRFs for this customer once the outstanding amount goes above the credit limit.",
    )
    followup_credit_limit = fields.Monetary(
        string="Allowed Credit",
        currency_field="currency_id",
        tracking=True,
        help="Outstanding amount allowed before new invoices and SRFs are blocked. "
        "0 = no credit: any unpaid invoice blocks.",
    )
    followup_credit_used = fields.Monetary(
        string="Credit Used",
        compute="_compute_followup_credit",
        currency_field="currency_id",
        help="Unpaid posted invoices, disputed ones included.",
    )
    followup_credit_hold = fields.Boolean(string="On Credit Hold", compute="_compute_followup_credit")
    followup_credit_can_edit = fields.Boolean(compute="_compute_followup_credit_can_edit")

    @api.model
    def _commercial_fields(self):
        return super()._commercial_fields() + ["followup_credit_block", "followup_credit_limit"]

    @api.model
    def _followup_credit_editable(self):
        return self.env.su or self.env.user.has_group("lerm_payment_followup.group_followup_manager")

    @api.depends_context("uid")
    def _compute_followup_credit_can_edit(self):
        self.followup_credit_can_edit = self._followup_credit_editable()

    def write(self, vals):
        # Children receive the company's values through the commercial-field sync; only guard the company itself
        if {"followup_credit_block", "followup_credit_limit"} & set(vals) and not self._followup_credit_editable():
            if self.filtered(lambda p: p.commercial_partner_id == p):
                raise AccessError(_("Only a Payment Follow-up Manager can change the credit limit."))
        return super().write(vals)

    @api.depends("user_id")
    def _compute_followup_responsible_id(self):
        for partner in self:
            partner.followup_responsible_id = partner.user_id

    def _followup_open_invoices(self, disputed=False):
        self.ensure_one()
        return self.followup_invoice_ids.filtered(
            lambda m: m.state == "posted"
            and m.move_type in ("out_invoice", "out_refund")
            and m.payment_state in ("not_paid", "partial")
            and m.followup_disputed == disputed
        ).sorted(lambda m: (m.invoice_date_due or m.invoice_date, m.id))

    def _compute_followup_invoices(self):
        for partner in self:
            invoices = partner.sudo()._followup_open_invoices()
            disputed = partner.sudo()._followup_open_invoices(disputed=True)
            partner.followup_open_invoice_ids = invoices
            partner.followup_disputed_invoice_ids = disputed
            partner.followup_disputed_amount = sum(disputed.mapped("amount_residual_signed"))

    # ------------------------------------------------------------------
    # Credit limit
    # ------------------------------------------------------------------

    def _followup_credit_used(self):
        """Outstanding amount on the commercial partner, disputed invoices included."""
        self.ensure_one()
        partner = self.commercial_partner_id.sudo()
        invoices = partner._followup_open_invoices() | partner._followup_open_invoices(disputed=True)
        return sum(invoices.mapped("amount_residual_signed"))

    def _followup_credit_exceeded(self, used):
        self.ensure_one()
        return self.followup_credit_block and self.currency_id.compare_amounts(used, self.followup_credit_limit) > 0

    def _compute_followup_credit(self):
        for partner in self:
            commercial = partner.commercial_partner_id
            used = commercial._followup_credit_used() if commercial else 0.0
            partner.followup_credit_used = used
            partner.followup_credit_hold = bool(commercial) and commercial._followup_credit_exceeded(used)

    def _followup_credit_hold_message(self, document, amount=0.0):
        """Why a new ``document`` (e.g. "invoice") worth ``amount`` is blocked for these customers, or False."""
        for partner in self.commercial_partner_id.filtered("followup_credit_block"):
            used = partner._followup_credit_used() + amount
            if partner._followup_credit_exceeded(used):
                if amount:
                    summary = _(
                        "%(partner)s would go over its credit limit: %(used)s outstanding with this %(document)s, "
                        "against an allowed credit of %(limit)s.",
                    )
                else:
                    summary = _("%(partner)s is over its credit limit: %(used)s outstanding against an allowed credit of %(limit)s.")
                return (summary + "\n" + _("Collect payment or raise the credit limit before creating a new %(document)s.")) % {
                    "partner": partner.display_name,
                    "used": format_amount(self.env, used, partner.currency_id),
                    "limit": format_amount(self.env, partner.followup_credit_limit, partner.currency_id),
                    "document": document,
                }
        return False

    def _followup_check_credit_limit(self, document, amount=0.0):
        message = self._followup_credit_hold_message(document, amount)
        if message:
            raise UserError(message)

    def _followup_next_level(self, levels, oldest, today):
        """Return the next level and its date.

        Levels already due are skipped up to the highest one, so a customer who is
        90 days overdue gets the 90-day step, not the friendly reminder.
        """
        self.ensure_one()
        current = self.followup_level_id
        if current:
            key = (current.delay, current.sequence, current.id)
            levels = levels.filtered(lambda lvl: (lvl.delay, lvl.sequence, lvl.id) > key)
        if not levels or not oldest:
            return levels[:1], False
        due = levels.filtered(lambda lvl: oldest + timedelta(days=lvl.delay) <= today)
        level = due[-1:] or levels[:1]
        next_date = oldest + timedelta(days=level.delay)
        if self.followup_last_date:
            # Never two steps on the same day
            next_date = max(next_date, self.followup_last_date + timedelta(days=1))
        return level, next_date

    def _followup_promise_kept(self, total_due):
        self.ensure_one()
        target = self.followup_promise_base_due - self.followup_promise_amount
        return self.currency_id.compare_amounts(total_due, target) <= 0

    @api.depends(
        "followup_invoice_ids.amount_residual_signed",
        "followup_invoice_ids.invoice_date_due",
        "followup_invoice_ids.payment_state",
        "followup_invoice_ids.state",
        "followup_invoice_ids.followup_disputed",
        "followup_level_id",
        "followup_last_date",
        "followup_promise_date",
        "followup_promise_amount",
        "followup_promise_base_due",
    )
    def _compute_followup_status(self):
        today = fields.Date.context_today(self)
        levels = self.env["lerm.followup.level"].sudo().search([])
        for partner in self:
            invoices = partner.sudo()._followup_open_invoices()
            overdue = invoices.filtered(lambda m: (m.invoice_date_due or m.invoice_date) < today)
            total_due = sum(invoices.mapped("amount_residual_signed"))
            total_overdue = sum(overdue.mapped("amount_residual_signed"))
            due_dates = [
                m.invoice_date_due or m.invoice_date
                for m in invoices
                if m.amount_residual_signed > 0
            ]
            oldest = min(due_dates) if due_dates else False

            next_level, next_date = partner._followup_next_level(levels, oldest, today)

            if partner.currency_id.compare_amounts(total_due, 0) <= 0 or not oldest:
                state, next_date = "none", False
            elif partner.followup_promise_date and not partner._followup_promise_kept(total_due):
                state = "promise" if partner.followup_promise_date >= today else "broken"
                next_date = partner.followup_promise_date + timedelta(days=1)
            elif not next_level:
                state = "final"
            elif next_date <= today:
                state = "action"
            else:
                state = "waiting"

            partner.followup_total_due = total_due
            partner.followup_total_overdue = total_overdue
            partner.followup_oldest_due_date = oldest
            partner.followup_next_level_id = next_level
            partner.followup_next_date = next_date
            partner.followup_state = state

    # ------------------------------------------------------------------
    # Refresh (status depends on today's date, so it is recomputed daily)
    # ------------------------------------------------------------------

    @api.model
    def _followup_partners_to_refresh(self):
        return self.with_context(active_test=False).search([
            "|", "|",
            ("followup_total_due", "!=", 0),
            ("followup_level_id", "!=", False),
            ("followup_promise_date", "!=", False),
        ])

    def _followup_recompute(self):
        for fname in STATUS_FIELDS:
            self.env.add_to_compute(self._fields[fname], self)
        self.flush_recordset(STATUS_FIELDS)

    def _followup_cleanup(self):
        """Reset customers who paid everything and close promises that were kept."""
        for partner in self:
            if partner.followup_state == "none":
                if partner.followup_level_id or partner.followup_promise_date:
                    partner._followup_log("reset", note=_("All invoices paid. Follow-up reset."), auto=True)
                    partner.sudo().write(partner._followup_reset_vals())
            elif partner.followup_promise_date and partner._followup_promise_kept(partner.followup_total_due):
                partner._followup_log(
                    "promise_kept",
                    promise_date=partner.followup_promise_date,
                    promise_amount=partner.followup_promise_amount,
                    auto=True,
                )
                partner.sudo().write(partner._followup_clear_promise_vals())

    @api.model
    def _cron_followup_refresh(self):
        partners = self._followup_partners_to_refresh()
        partners._followup_recompute()
        partners._followup_cleanup()

    @api.model
    def _cron_followup_auto(self):
        if not self.env["ir.config_parameter"].sudo().get_param("lerm_payment_followup.auto_enabled"):
            return
        self._cron_followup_refresh()
        partners = self.search([
            ("followup_state", "in", ("action", "broken")),
            ("followup_exclude_auto", "=", False),
        ])
        for partner in partners:
            try:
                with self.env.cr.savepoint():
                    partner._followup_execute(auto=True)
            except Exception:
                _logger.exception("Payment follow-up failed for partner %s", partner.id)

    # ------------------------------------------------------------------
    # Follow-up steps
    # ------------------------------------------------------------------

    @staticmethod
    def _followup_clear_promise_vals():
        return {
            "followup_promise_date": False,
            "followup_promise_amount": 0.0,
            "followup_promise_base_due": 0.0,
        }

    def _followup_reset_vals(self):
        return dict(self._followup_clear_promise_vals(), followup_level_id=False, followup_last_date=False)

    def _followup_user(self):
        self.ensure_one()
        if self.followup_responsible_id:
            return self.followup_responsible_id
        if self.env.uid != SUPERUSER_ID:
            return self.env.user
        return self.env.ref("base.user_admin")

    def _followup_log(self, action, level=None, outcome=False, invoices=None, note=False, auto=False, **vals):
        self.ensure_one()
        return self.env["lerm.followup.log"].sudo().create(dict(
            vals,
            partner_id=self.id,
            action=action,
            level_id=level.id if level else False,
            outcome=outcome,
            invoice_ids=[(6, 0, invoices.ids)] if invoices else [],
            note=note,
            auto=auto,
            user_id=self.env.uid,
        ))

    def _followup_advance(self, level):
        """Record ``level`` as done. A broken promise is closed by the next step."""
        self.ensure_one()
        vals = {"followup_level_id": level.id, "followup_last_date": fields.Date.context_today(self)}
        if self.followup_state == "broken":
            vals.update(self._followup_clear_promise_vals())
        self.sudo().write(vals)

    def _followup_schedule_activity(self, level, summary=None):
        self.ensure_one()
        summary = ACTIVITY_PREFIX + (summary or level.name)
        partner = self.sudo()
        if partner.activity_ids.filtered(lambda a: a.summary == summary):
            return
        act_type = "mail.mail_activity_data_call" if level.action_type == "call" else "mail.mail_activity_data_todo"
        partner.activity_schedule(
            act_type,
            date_deadline=fields.Date.context_today(self),
            summary=summary,
            note=level.note or "",
            user_id=self._followup_user().id,
        )

    def _followup_close_activities(self, feedback=False):
        activities = self.sudo().activity_ids.filtered(
            lambda a: (a.summary or "").startswith(ACTIVITY_PREFIX)
        )
        if activities:
            activities.action_feedback(feedback=feedback)

    def _followup_default_recipients(self):
        self.ensure_one()
        if self.email:
            return self
        return self.child_ids.filtered(lambda c: c.type == "contact" and c.email)[:1]

    def _followup_render_template(self, template):
        self.ensure_one()
        template = template.sudo()
        subject = template._render_field("subject", self.ids, compute_lang=True)[self.id]
        body = template._render_field("body_html", self.ids, compute_lang=True)[self.id]
        return subject, body

    def _followup_invoice_attachments(self, invoices):
        """Attach the uploaded invoice copy, or render the invoice PDF when none was uploaded.

        Returns (attachments, names of invoices that failed).
        """
        self.ensure_one()
        attachments = self.env["ir.attachment"]
        failed = []
        for invoice in invoices.filtered(lambda m: m.move_type == "out_invoice"):
            invoice = invoice.sudo().with_context(bin_size=False)
            if invoice.followup_invoice_copy:
                attachments |= self.env["ir.attachment"].sudo().create({
                    "name": invoice.followup_invoice_copy_name
                    or "%s.pdf" % (invoice.name or "Invoice").replace("/", "_"),
                    "type": "binary",
                    "datas": invoice.followup_invoice_copy,
                    "res_model": "res.partner",
                    "res_id": self.id,
                })
                continue
            try:
                pdf, _fmt = self.env["ir.actions.report"].sudo()._render_qweb_pdf(
                    "lerm_civil_inv.kes_invoice", invoice.ids
                )
            except Exception:
                # The invoice template reads `request`, so it cannot render in the cron
                _logger.warning("Could not render invoice PDF for %s", invoice.name, exc_info=True)
                failed.append(invoice.name)
                continue
            attachments |= self.env["ir.attachment"].sudo().create({
                "name": "%s.pdf" % (invoice.name or "Invoice").replace("/", "_"),
                "type": "binary",
                "raw": pdf,
                "mimetype": "application/pdf",
                "res_model": "res.partner",
                "res_id": self.id,
            })
        return attachments, failed

    def _followup_send_email(self, level, recipients, subject, body, invoices, attach_invoices=True, advance=True, auto=False):
        self.ensure_one()
        attachments, failed = self.env["ir.attachment"], []
        if attach_invoices:
            attachments, failed = self._followup_invoice_attachments(invoices)
        self.sudo().message_post(
            body=body,
            subject=subject,
            partner_ids=recipients.ids,
            attachment_ids=attachments.ids,
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
            email_layout_xmlid="mail.mail_notification_light",
        )
        note = _("Sent to %s", ", ".join(recipients.mapped("email")))
        if failed:
            note += "\n" + _("Invoice PDF not attached: %s", ", ".join(failed))
        self._followup_log("email", level=level, outcome="sent", invoices=invoices, note=note, auto=auto)
        if advance and level:
            self._followup_advance(level)

    def _followup_send_level_email(self, level, auto=False):
        self.ensure_one()
        recipients = self._followup_default_recipients()
        if not recipients:
            raise UserError(_("%s has no email address to send the payment reminder to.", self.display_name))
        template = level.mail_template_id or self.env.ref("lerm_payment_followup.mail_template_followup_reminder")
        subject, body = self._followup_render_template(template)
        self._followup_send_email(
            level, recipients, subject, body, self.sudo()._followup_open_invoices(),
            attach_invoices=level.attach_invoices, auto=auto,
        )

    def _followup_execute(self, auto=False):
        """Do the next due step for each customer. Returns the customers that moved up a level."""
        params = self.env["ir.config_parameter"].sudo()
        send_email = not auto or params.get_param("lerm_payment_followup.auto_send_email")
        create_task = not auto or params.get_param("lerm_payment_followup.auto_create_activity")
        done = self.browse()
        for partner in self:
            level = partner.followup_next_level_id
            if not level or partner.followup_state not in ("action", "broken"):
                continue
            if level.action_type == "email":
                if not partner._followup_default_recipients():
                    if not auto and len(self) == 1:
                        raise UserError(_("%s has no email address to send the payment reminder to.", partner.display_name))
                    partner._followup_schedule_activity(level, _("add an email address to send '%s'", level.name))
                elif send_email:
                    partner._followup_send_level_email(level, auto=auto)
                    done |= partner
                else:
                    # Emails need review: leave the step due and ask the responsible to send it
                    partner._followup_schedule_activity(level, _("review and send '%s'", level.name))
            elif create_task:
                partner._followup_schedule_activity(level)
                partner._followup_log("task", level=level, auto=auto)
                partner._followup_advance(level)
                done |= partner
        return done

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------

    def action_followup_process(self):
        todo = self.filtered(lambda p: p.followup_state in ("action", "broken"))
        if not todo:
            raise UserError(_("None of the selected customers has a follow-up step due."))
        done = todo._followup_execute()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": _("Follow-up step done for %(done)s of %(total)s customer(s).", done=len(done), total=len(todo)),
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }

    def _followup_wizard_action(self, name, model):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": model,
            "view_mode": "form",
            "target": "new",
            "context": {"default_partner_id": self.id},
        }

    def action_followup_send(self):
        return self._followup_wizard_action(_("Send Payment Reminder"), "lerm.followup.send.wizard")

    def action_followup_log(self):
        return self._followup_wizard_action(_("Log Follow-up"), "lerm.followup.log.wizard")

    def action_followup_reset(self):
        if not self.env.user.has_group("lerm_payment_followup.group_followup_manager"):
            raise AccessError(_("Only a Payment Follow-up Manager can reset follow-up."))
        for partner in self:
            partner._followup_log("reset", note=_("Follow-up reset manually."))
            partner.sudo().write(partner._followup_reset_vals())

    def action_open_followup(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Payment Follow-up"),
            "res_model": "res.partner",
            "res_id": self.commercial_partner_id.id,
            "view_mode": "form",
            "views": [(self.env.ref("lerm_payment_followup.view_partner_followup_form").id, "form")],
            "target": "current",
        }
