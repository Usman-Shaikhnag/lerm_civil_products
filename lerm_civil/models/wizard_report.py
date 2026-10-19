from odoo import models, api


class SampleWizardReport(models.AbstractModel):
    _name = 'report.lerm_civil.sample_wizard_report_template'
    _description = 'Customer Sample Wizard Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        samples = self.env['lerm.srf.sample'].sudo().search(data.get('domain') or [('id', '=', 0)])
        return {
            'doc_ids': samples.ids,
            'doc_model': 'lerm.srf.sample',
            'docs': samples,
            'sample_ids': samples,
            'customer': data.get('customer'),
            'from_date': data.get('from_date'),
            'to_date': data.get('to_date'),
        }


class UlrWizardReport(models.AbstractModel):
    _name = 'report.lerm_civil.ulr_wizard_report_template'
    _description = 'ULR Wizard Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        ulr = data.get('ulr')
        samples = self.env['lerm.srf.sample'].sudo().search([('ulr_no', '=', ulr)]) if ulr else self.env['lerm.srf.sample']
        return {
            'doc_ids': samples.ids,
            'doc_model': 'lerm.srf.sample',
            'docs': samples,
            'sample_ids': samples,
            'ulr': ulr,
        }
