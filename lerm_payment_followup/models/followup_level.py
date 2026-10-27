from odoo import api, fields, models


class FollowupLevel(models.Model):
    _name = "lerm.followup.level"
    _description = "Payment Follow-up Level"
    _order = "delay, sequence, id"

    name = fields.Char(string="Step", required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    delay = fields.Integer(
        string="Days After Due Date",
        required=True,
        help="Days after the due date of the customer's oldest unpaid invoice "
             "when this step becomes due. Use a negative number to remind "
             "before the due date.",
    )
    action_type = fields.Selection(
        [("email", "Send Email"), ("call", "Phone Call"), ("manual", "Manual Task")],
        string="Action",
        required=True,
        default="email",
    )
    mail_template_id = fields.Many2one(
        "mail.template",
        string="Email Template",
        domain=[("model", "=", "res.partner")],
        help="Leave empty to use the default payment reminder template.",
    )
    attach_invoices = fields.Boolean(string="Attach Invoice PDFs", default=True)
    note = fields.Text(
        string="Instructions",
        help="Shown on the task created for phone call and manual steps.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        levels = super().create(vals_list)
        self.env["res.partner"]._followup_partners_to_refresh()._followup_recompute()
        return levels

    def write(self, vals):
        res = super().write(vals)
        if {"delay", "sequence", "active"} & set(vals):
            self.env["res.partner"]._followup_partners_to_refresh()._followup_recompute()
        return res

    def unlink(self):
        res = super().unlink()
        self.env["res.partner"]._followup_partners_to_refresh()._followup_recompute()
        return res
