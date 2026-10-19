from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PrintReportsWizard(models.TransientModel):
    _name = 'print.reports.wizard'
    _description = "Sample Print Reports Wizard"

    kes_no = fields.Char(string="Sample No.")

    def _get_sample_eln(self):
        self.ensure_one()
        kes_no = (self.kes_no or '').strip()
        if not kes_no:
            raise UserError(_("Please enter the Sample No."))
        if '/' not in kes_no:
            kes_no = 'KES/' + kes_no
        pattern = kes_no.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        sample = self.env['lerm.srf.sample'].sudo().search([('kes_no', '=ilike', pattern)], limit=1)
        if not sample:
            raise UserError(_("No sample found with Sample No. %s.", kes_no))
        eln = self.env["lerm.eln"].sudo().search([('sample_id', '=', sample.id)], limit=1)
        if not eln:
            raise UserError(_("Sample %s has no ELN, so there is nothing to print.", kes_no))
        return sample, eln

    def _get_template(self, eln, field_name):
        if eln.is_product_based_calculation:
            template = eln.material.product_based_calculation[:1][field_name]
        else:
            template = eln.parameters_result.parameter[:1][field_name]
        if not template:
            raise UserError(_("No report template is configured for this sample."))
        return template.report_name

    def _print_report(self, nabl):
        sample, eln = self._get_sample_eln()
        template_name = self._get_template(eln, 'main_report_template')
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': template_name,
            'report_file': template_name,
            'data': {'sample': sample.id, 'nabl': nabl, 'fromEln': False, 'report_wizard': True},
        }

    def print_nabl_report(self):
        return self._print_report(True)

    def print_non_nabl_report(self):
        return self._print_report(False)

    def print_datasheet(self):
        sample, eln = self._get_sample_eln()
        template_name = self._get_template(eln, 'datasheet_report_template')
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': template_name,
            'report_file': template_name,
            'data': {'fromsample': False, 'sample': sample.id, 'eln': eln.id, 'report_wizard': True},
        }

    def discard_print(self):
        return {'type': 'ir.actions.act_window_close'}
