from odoo import api, fields, models,_
from odoo.exceptions import UserError
import logging



class SampleReportsWizard(models.TransientModel):
    _name = "sample.reports.wizard"

    customer = fields.Many2one('res.partner',string="Customer")
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    state = fields.Selection([
        ('1-allotment_pending', 'Assignment Pending'),
        ('2-alloted', 'Alloted'),
        ('3-pending_verification','Pending Verification'),
        ('5-pending_approval','Pending Approval'),
        ('4-in_report', 'In-Report'),
        ('6-cancelled', 'Cancelled'),
    ], string='State',default='4-in_report')


    def print_srf_reports(self):

        template_name = self.env['ir.actions.report'].search([('report_name','=','	lerm_civil.sample_wizard_report_template')]).report_name
        samples = self.env['lerm.srf.sample'].sudo().search([('customer_id','=',self.customer.id),('srf_id.srf_date','>=',self.from_date),('srf_id.srf_date','<=',self.to_date)])
        
        # import wdb ; wdb.set_trace()
        customer = self.customer
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': 'lerm_civil.sample_wizard_report_template',
            # 'report_name': template_name,
            'report_file': template_name,
            'data' : {'customer': customer.id,'from_date':self.from_date,'to_date':self.to_date}
        }

    def discard_print(self):
        return {'type': 'ir.actions.act_window_close'}

    def action_view_samples(self):
        # Search domain
        domain = [
            ('srf_id.srf_date', '>=', self.from_date),
            ('srf_id.srf_date', '<=', self.to_date),
            ('state', '=', self.state),

        ]
        if self.customer:
            domain.append(('srf_id.customer','=',self.customer.id))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered Samples',
            'res_model': 'lerm.srf.sample',
            'view_mode': 'tree,form',
            'domain': domain,
            'target': 'current',
        }