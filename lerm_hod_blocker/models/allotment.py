from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AllotSampleWizard(models.TransientModel):
    _inherit = 'sample.allotment.wizard'

    report_due_date = fields.Date(string='Report Due Date')

    @api.model
    def _get_max_testing_days_due_date(self, sample_ids):
        samples = self.env['lerm.srf.sample'].browse(sample_ids)
        params = samples.mapped('parameters')
        if not params:
            return False
        max_days = max(params.mapped('testing_days') or [0])
        return fields.Date.today() + timedelta(days=max_days)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids') or []
        if len(active_ids) > 1:
            # The base wizard forces 'parameter' mode when the first sample
            # already has an ELN (partially alloted samples). Parameter mode
            # only supports one sample, so bulk allotment must use 'sample'
            # mode where a single technician is applied to all parameters.
            res['allocation_type'] = 'sample'
            res['line_ids'] = []
        if active_ids:
            due_date = self._get_max_testing_days_due_date(active_ids)
            if due_date:
                res['report_due_date'] = due_date
        return res

    @api.onchange('sample_id')
    def _onchange_sample_compute_due_date(self):
        if self.sample_id:
            due_date = self._get_max_testing_days_due_date([self.sample_id.id])
            if due_date:
                self.report_due_date = due_date

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
