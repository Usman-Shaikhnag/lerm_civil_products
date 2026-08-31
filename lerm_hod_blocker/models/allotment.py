from odoo import _, fields, models
from odoo.exceptions import UserError


class AllotSampleWizard(models.TransientModel):
    _inherit = 'sample.allotment.wizard'

    report_due_date = fields.Date(string='Report Due Date')

    def allot_sample(self):
        active_ids = self.env.context.get('active_ids') or []
        require_due_date = self.env.context.get(
            'hod_blocker_require_due_date', False)
        if active_ids and require_due_date and not self.report_due_date:
            raise UserError(
                _('Please set a report due date before allotting samples.'))
        if active_ids and self.report_due_date:
            # Set the due date first so task deadlines created by the base
            # allotment logic pick it up.
            self.env['lerm.srf.sample'].browse(active_ids).sudo().write({
                'report_due_date': self.report_due_date,
            })
        return super().allot_sample()
