from odoo import api, fields, models, _
from odoo.exceptions import UserError


class UlrReportsWizard(models.TransientModel):
    _name = "ulr.reports.wizard"
    _description = "ULR Reports Wizard"

    ulr = fields.Char("ULR")

    def print_ulr_reports(self):
        self.ensure_one()
        if not self.ulr or not self.ulr.strip():
            raise UserError(_("Please enter a ULR number."))
        report_name = 'lerm_civil.ulr_wizard_report_template'
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': report_name,
            'report_file': report_name,
            'data': {'ulr': self.ulr.strip()},
        }

    def discard_print(self):
        return {'type': 'ir.actions.act_window_close'}
