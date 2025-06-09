from odoo import models , fields,api
import json
import base64
import qrcode
from io import BytesIO




class ElnReport(models.AbstractModel):
    _name = 'report.lerm_civil.10per_fine_coarse_agg_mechanical'
    _description = '10per Fine Value Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        report_data = self.env['lerm.srf.sample'].sudo().browse(docids)
        
        return {
            'report_data': report_data
        }

