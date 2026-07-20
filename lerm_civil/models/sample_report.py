from odoo import models , fields,api
import json


class SampleReport(models.AbstractModel):
    _name = 'report.lerm_civil.sample_report_template'
    _description = 'Sample Report'

    @api.model
    def _get_report_values(self, docids, data=None):


        eln = self.env['lerm.eln'].sudo().search([("sample_id","=",docids[0])])
        # wdb.set_trace()

        print(eln,"ELN DATA")

        # data_json = json.loads(eln)
        # print(data_json , 'DATA')
        # docs1 = self.env['account.move'].sudo().browse(docids)
        # tax_totals_json = docs1.tax_totals_json

        # Parse the tax_totals_json string into a Python object
        # tax_totals = json.loads(tax_totals_json)
        # Pass the tax_totals to the report context
        # report_data = {'tax_totals': tax_totals}
#         data_mock = [
#             {
#                 "columns" : [
#                     {"name": "Particulars"},
#                     {"name": "Results"}
#                 ]
#             },
#             {
#             "rows": [
#                 {
#                 "row" : [
#                 {"value": "i) Mean weight of the aggregate in the cylinder in gm, W"},
#                 {"value": 21}
#                 ]
#                 },
#                 {
#                 "row" : [
#                 {"value": "i) M of the aggregate in the cylinder in gm, W"},
#                 {"value": 81}
#                 ]
#                 }
#         ]
#     }
           
# ]

        return {
            'eln': eln
        }
