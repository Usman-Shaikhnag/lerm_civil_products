from odoo import api, fields, models,_
from odoo.exceptions import UserError
import logging



class PrintReportsWizard(models.TransientModel):
    _name = 'print.reports.wizard'

    kes_no = fields.Char(string="KES NO.")

    def print_nabl_report(self):
        # import wdb ; wdb.set_trace()
        sample = self.env['lerm.srf.sample'].sudo().search([('kes_no','=',self.kes_no)])
        eln = self.env["lerm.eln"].sudo().search([('sample_id','=', sample.id)])
        # template_name = self.env['ir.actions.report'].search([('report_name','=','	lerm_civil.sample_wizard_report_template')]).report_name
        is_product_based = eln.is_product_based_calculation
        if is_product_based == True:
            template_name = eln.material.product_based_calculation[0].main_report_template.report_name
        else:
            template_name = eln.parameters_result.parameter[0].main_report_template.report_name
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            # 'report_name': 'lerm_civil.sample_wizard_report_template',
            'report_name': template_name,
            'report_file': template_name,
            'data' : {'sample': sample.id,'nabl':True,'fromEln':False,'report_wizard':True}
        }
    
    def print_non_nabl_report(self):
        # import wdb ; wdb.set_trace()
        sample = self.env['lerm.srf.sample'].sudo().search([('kes_no','=',self.kes_no)])
        eln = self.env["lerm.eln"].sudo().search([('sample_id','=', sample.id)])
        # template_name = self.env['ir.actions.report'].search([('report_name','=','	lerm_civil.sample_wizard_report_template')]).report_name
        is_product_based = eln.is_product_based_calculation
        if is_product_based == True:
            template_name = eln.material.product_based_calculation[0].main_report_template.report_name
        else:
            template_name = eln.parameters_result.parameter[0].main_report_template.report_name
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            # 'report_name': 'lerm_civil.sample_wizard_report_template',
            'report_name': template_name,
            'report_file': template_name,
            'data' : {'sample': sample.id,'nabl':False,'fromEln':False,'report_wizard':True},
            
        }
    def print_datasheet(self):
        sample = self.env['lerm.srf.sample'].sudo().search([('kes_no','=',self.kes_no)])
        eln = self.env["lerm.eln"].sudo().search([('sample_id','=', sample.id)])
        # template_name = self.env['ir.actions.report'].search([('report_name','=','	lerm_civil.sample_wizard_report_template')]).report_name
        # import wdb ; wdb.set_trace()
        is_product_based = eln.is_product_based_calculation
        if is_product_based == True:
            template_name = eln.material.product_based_calculation[0].datasheet_report_template.report_name
        else:
            template_name = eln.parameters_result.parameter[0].datasheet_report_template.report_name
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            # 'report_name': 'lerm_civil.sample_wizard_report_template',
            'report_name': template_name,
            'report_file': template_name,
            'data' : {'fromsample' : False,'sample': sample.id,'eln':eln.id, 'report_wizard':True}
        }

    def discard_print(self):
        return {'type': 'ir.actions.act_window_close'}