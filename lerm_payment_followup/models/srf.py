from odoo import _, api, models


class LermCivilSrf(models.Model):
    _inherit = "lerm.civil.srf"

    # Same single-vals signature as lerm_civil's create
    @api.model
    def create(self, vals):
        srf = super().create(vals)
        srf._followup_check_credit_limit()
        return srf

    def write(self, vals):
        res = super().write(vals)
        if {"customer", "billing_customer", "samples"} & set(vals):
            self._followup_check_credit_limit()
        return res

    def confirm_srf(self):
        # Samples are usually added after the SRF is saved
        self._followup_check_credit_limit()
        return super().confirm_srf()

    def _followup_srf_amount(self):
        """Price of the samples not invoiced yet; invoiced ones are already in the outstanding amount."""
        self.ensure_one()
        samples = self.samples.filtered(lambda s: s.invoice_status != "2-invoiced" and s.state != "6-cancelled")
        return sum(samples.mapped("price"))

    def _followup_check_credit_limit(self):
        for srf in self:
            (srf.customer | srf.billing_customer)._followup_check_credit_limit(_("SRF"), srf._followup_srf_amount())

    @api.onchange("customer", "billing_customer", "samples")
    def _onchange_customer_followup_credit(self):
        message = (self.customer | self.billing_customer)._followup_credit_hold_message(
            _("SRF"), self._followup_srf_amount()
        )
        if message:
            return {"warning": {"title": _("Credit Limit Exceeded"), "message": message}}
