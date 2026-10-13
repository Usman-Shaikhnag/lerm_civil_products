from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging


class SampleCancellationWizard(models.TransientModel):
    _name = "sample.cancellation.wizard"
    _description = "Sample Cancellation Wizard"

    sample = fields.Many2one('lerm.srf.sample')
    cancellation_reason = fields.Selection([
        ('software_error', 'Software Error'),
        ('work_cancelled', 'Work has been Cancelled'),
        ('out_of_scope', 'Out of Scope'),
        ('other', 'Other'),
    ], string="Reason", required=True)
    other_cancellation_reason = fields.Text("Cancellation Reason")

    def cancel_current_sample(self):
        sample = self.sample
        if self.cancellation_reason == 'other' and not self.other_cancellation_reason:
            raise UserError(_("Please provide the cancellation reason."))
        sample.write({
            'state': '6-cancelled',
            'cancellation_reason': self.cancellation_reason,
            'other_cancellation_reason': self.other_cancellation_reason,
        })
        elns = self.env['lerm.eln'].sudo().search([('sample_id', '=', sample.id)])
        if elns:
            elns.write({'state': '5-cancelled'})
        return {'type': 'ir.actions.act_window_close'}

    def discard_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
