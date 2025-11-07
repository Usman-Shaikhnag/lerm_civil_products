from odoo import models , fields,api
import json
import base64
import qrcode
from io import BytesIO
from lxml import etree
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import math
from scipy.interpolate import CubicSpline , interp1d , Akima1DInterpolator
from scipy.optimize import minimize_scalar




# class OPCReport(models.AbstractModel):
#     _name = 'report.cement_opc.opc_report'
#     _description = 'Opc Cement Report'
    
#     @api.model
#     def _get_report_values(self, docids, data):
#         # eln = self.env['lerm.eln'].sudo().browse(docids)
#         nabl = data.get('nabl')
#         if data.get('report_wizard') == True:
#             eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['sample'])])
#         # elif 'active_id' in data['context']:
#         elif 'active_id' in data.get('context', {}):
#             eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
#         else:
#             eln = self.env['lerm.eln'].sudo().browse(docids)
        
#         qr = qrcode.QRCode(
#             version=1,
#             error_correction=qrcode.constants.ERROR_CORRECT_L,
#             box_size=10,
#             border=4
#         )

#         base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
#         if nabl:
#             url = f"{base_url}/download_report/nabl/{eln.id}"
#         else:
#             url = f"{base_url}/download_report/nonnabl/{eln.id}"

#         qr.add_data(url)
#         qr.make(fit=True)
#         qr_image = qr.make_image()

#         buffered = BytesIO()
#         qr_image.save(buffered, format="PNG")
#         qr_code = base64.b64encode(buffered.getvalue()).decode()

            
#         data = {
#             "material_id":eln.material.id,
#             "grade_id":eln.grade_id.id
#         }
#         model = eln.get_product_base_calc_line(data).ir_model.model
#         cement_data = self.env[model].search([("id","=",eln.model_id)])
#         return {
#             'eln': eln,
#            'cement': cement_data,
#             'qrcode': qr_code,
#             'nabl' : nabl
#         }



import logging

_logger = logging.getLogger(__name__)

class OPCReport(models.AbstractModel):
    _name = 'report.cement_opc.opc_report'
    _description = 'Opc Cement Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Generate OPC Cement report values safely"""
        # ✅ Fix: Ensure data is always a dict (avoid 'list object has no attribute split')
        if not data or not isinstance(data, dict):
            _logger.warning("⚠️ _get_report_values got non-dict data: %s", type(data))
            data = {}

        nabl = data.get('nabl', False)

        # ✅ Fetch ELN
        if data.get('report_wizard') is True:
            eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data.get('sample'))])
        elif 'active_id' in data.get('context', {}):
            eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data['context']['active_id'])])
        else:
            eln = self.env['lerm.eln'].sudo().browse(docids)

        # If multiple records, pick first
        eln = eln[0] if eln else False
        if not eln:
            raise ValueError("No ELN record found for report generation.")

        # ✅ Generate QR Code
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        url = f"{base_url}/download_report/nabl/{eln.id}" if nabl else f"{base_url}/download_report/nonnabl/{eln.id}"
        qr.add_data(url)
        qr.make(fit=True)

        buffered = BytesIO()
        qr.make_image().save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()

        # ✅ Handle missing relations gracefully
        material_id = eln.material.id if eln.material else False
        grade_id = eln.grade_id.id if eln.grade_id else False

        # ✅ Get linked test model
        data_line = {"material_id": material_id, "grade_id": grade_id}
        model_line = eln.get_product_base_calc_line(data_line)
        model_name = model_line.ir_model.model if model_line else False
        cement_data = self.env[model_name].search([("id", "=", eln.model_id)]) if model_name else False

        # ✅ Final return
        return {
            'eln': eln,
            'cement': cement_data,
            'qrcode': qr_code,
            'nabl': nabl,
        }




class OPCDataSheet(models.AbstractModel):
    _name = 'report.cement_opc.cement_datasheet'
    _description = 'Cement Opc DataSheet'
    
    @api.model
    def _get_report_values(self, docids, data):
        if data['fromsample'] == True:
            if 'active_id' in data['context']:
                eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
            else:
                eln = self.env['lerm.eln'].sudo().browse(docids) 
        else:
            if data['report_wizard']:
                if data['report_wizard'] == True:
                    eln = self.env['lerm.eln'].sudo().search([('id','=',data['eln'])])
                else:
                    eln = self.env['lerm.eln'].sudo().browse(data['eln_id'])
            else:
                eln = self.env['lerm.eln'].sudo().browse(data['eln_id'])
        # differnt location for product based
        # model_name = eln.material.product_based_calculation[0].ir_model.name 
        model_id = eln.model_id
        model_name = eln.material.product_based_calculation.filtered(lambda record: record.grade.id == eln.grade_id.id).ir_model.name
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        return {
            'eln': eln,
            'data' : general_data
        }