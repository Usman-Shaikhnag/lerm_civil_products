from odoo import models , fields,api
import json

class KesCustomInvoiceReport(models.AbstractModel):
    _name = 'report.lerm_civil_inv.kes_custom_invoice'
    _description = 'Kes Custom Invoice Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs1 = self.env['account.move'].sudo().browse(docids)
        print(docs1 , 'afzal khan ')
        tax_totals_json = docs1.tax_totals_json

        # Parse the tax_totals_json string into a Python object
        tax_totals = json.loads(tax_totals_json)
        # Pass the tax_totals to the report context
        report_data = {'tax_totals': tax_totals}
        amount_total = 0
        for i in docs1:
            for product in i.invoice_line_ids:
                if product.product_id:
                    amount_total = amount_total + product.price_subtotal
                else:
                    print('no product id found')

        return {
              'doc_ids': docids,
              'doc_model': 'account.move',
              'total_amount_line' : amount_total,
              'data': docs1,
              'report_data': report_data,
        }

class KesCustomInvoiceReportWithoutHeader(models.AbstractModel):
    _name = 'report.lerm_civil_inv.kes_custom_invoice_no_header'
    _description = 'Kes Custom Invoice Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs1 = self.env['account.move'].sudo().browse(docids)
        print(docs1 , 'afzal khan ')
        tax_totals_json = docs1.tax_totals_json

        # Parse the tax_totals_json string into a Python object
        tax_totals = json.loads(tax_totals_json)
        # Pass the tax_totals to the report context
        report_data = {'tax_totals': tax_totals}
        amount_total = 0
        for i in docs1:
            for product in i.invoice_line_ids:
                if product.product_id:
                    amount_total = amount_total + product.price_subtotal
                else:
                    print('no product id found')

        return {
              'doc_ids': docids,
              'doc_model': 'account.move',
              'total_amount_line' : amount_total,
              'data': docs1,
              'report_data': report_data,
        }
