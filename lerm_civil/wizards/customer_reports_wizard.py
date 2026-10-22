from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SampleReportsWizard(models.TransientModel):
    _name = "sample.reports.wizard"
    _description = "Customer Sample Reports Wizard"

    customer = fields.Many2one('res.partner', string="Customer")
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    state = fields.Selection([
        ('1-allotment_pending', 'Assignment Pending'),
        ('2-alloted', 'Alloted'),
        ('3-pending_verification', 'Pending Verification'),
        ('5-pending_approval', 'Pending Approval'),
        ('4-in_report', 'In-Report'),
        ('6-cancelled', 'Cancelled'),
    ], string='State', default='4-in_report')

    def _get_sample_domain(self):
        self.ensure_one()
        domain = [('state', '=', self.state)]
        if self.from_date:
            domain.append(('srf_id.srf_date', '>=', self.from_date))
        if self.to_date:
            domain.append(('srf_id.srf_date', '<=', self.to_date))
        if self.customer:
            domain.append(('srf_id.customer', '=', self.customer.id))
        return domain

    def print_srf_reports(self):
        self.ensure_one()
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise UserError(_("From Date cannot be after To Date."))
        report_name = 'lerm_civil.sample_wizard_report_template'
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': report_name,
            'report_file': report_name,
            'data': {
                'domain': self._get_sample_domain(),
                'customer': self.customer.name or '',
                'from_date': self.from_date and self.from_date.strftime('%d/%m/%Y') or '',
                'to_date': self.to_date and self.to_date.strftime('%d/%m/%Y') or '',
            },
        }

    def discard_print(self):
        return {'type': 'ir.actions.act_window_close'}

    def action_view_samples(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered Samples',
            'res_model': 'lerm.srf.sample',
            'view_mode': 'tree,form',
            'domain': self._get_sample_domain(),
            'target': 'current',
        }
