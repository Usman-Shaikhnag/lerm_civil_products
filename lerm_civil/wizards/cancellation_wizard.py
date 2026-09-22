from odoo import api, fields, models,_
from odoo.exceptions import UserError
import logging



class SampleCancellationWizard(models.TransientModel):
    _name = "sample.cancellation.wizard"


    sample = fields.Many2one('lerm.srf.sample')

    cancellation_reason = fields.Selection([
        ('software_error', 'Software Error'),
        ('work_cancelled', 'Work has been Cancelled'),
        ('out_of_scope', 'Out of Scope'),
        ('other', 'Other'),


    ])
    other_cancellation_reason = fields.Text("Cancellation Reason")


    def cancel_current_sample(self):
        sample = self.sample
        sample.write({'state':'6-cancelled'})
        return {'type': 'ir.actions.act_window_close'}
    
    def discard_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
