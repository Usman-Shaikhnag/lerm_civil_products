from odoo import models , fields,api
import json



class SaleOrderReport(models.AbstractModel):
    _name = 'report.lerm_civil_inv.report_nbml_quotation'
    _description = 'NBML Quotation Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
        }