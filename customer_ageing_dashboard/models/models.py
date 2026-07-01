from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    lerm_customer = fields.Boolean(string="Is LERM Customer", default=True)

    ageing_total_due = fields.Monetary(
        string="Ageing Total Due",
        compute="_compute_ageing_fields",
        currency_field="currency_id",
    )
    ageing_invoice_count = fields.Integer(
        string="Ageing Invoice Count",
        compute="_compute_ageing_fields",
    )

    @api.depends_context("company")
    def _compute_ageing_fields(self):
        Invoice = self.env["account.move"].sudo()
        for partner in self:
            invoices = Invoice.search([
                ("move_type", "in", ["out_invoice", "out_refund"]),
                ("state", "=", "posted"),
                ("payment_state", "not in", ["paid", "reversed", "in_payment"]),
                ("partner_id", "=", partner.id),
            ])
            partner.ageing_total_due = sum(invoices.mapped("amount_residual_signed")) or 0.0
            partner.ageing_invoice_count = len(invoices)

    def action_open_ageing_detail(self):
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "customer_ageing_detail_report",
            "params": {
                "partner_id": self.id,
                "partner_name": self.display_name,
            },
        }
