from odoo import api, fields, models,_
from odoo.exceptions import UserError
import logging



class UlrReportsWizard(models.TransientModel):
    _name = "ulr.reports.wizard"

    ulr = fields.Char("ULR")


    def print_ulr_reports(self):

        template_name = self.env['ir.actions.report'].search([('report_name','=','	lerm_civil.ulr_wizard_report_template')]).report_name
        
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': 'lerm_civil.ulr_wizard_report_template',
            # 'report_name': template_name,
            'report_file': template_name,
            'data' : {'ulr': self.ulr}
        }

    def discard_print(self):
        return {'type': 'ir.actions.act_window_close'}