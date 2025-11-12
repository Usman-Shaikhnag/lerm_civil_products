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



class GgbsDataSheet(models.AbstractModel):
    _name = 'report.ggbs.ggbs_datasheet'
    _description = 'GGBS DataSheet '
    
    @api.model
    def _get_report_values(self, docids, data):
        if data['fromsample'] == True:
            if 'active_id' in data['context']:
                eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
            else:
                eln = self.env['lerm.eln'].sudo().browse(docids) 
        else:
            if data['report_wizard'] == True:
                eln = self.env['lerm.eln'].sudo().search([('id','=',data['eln'])])
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




# class GgbsReport(models.AbstractModel):
#     _name = 'report.ggbs.lerm_ggbs_report'
#     _description = 'GGBS Report '
    
    
#     @api.model
#     def _get_report_values(self, docids, data=None):
#         data = data or {}
#         nabl = data.get('nabl', False)

#         # 🧩 ELN Record मिळवा
#         if data.get('report_wizard'):
#             eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data.get('sample'))])
#         elif 'active_id' in data.get('context', {}):
#             eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data['context']['active_id'])])
#         else:
#             eln = self.env['lerm.eln'].sudo().browse(docids)

#         if not eln:
#             raise ValueError("ELN record not found")

#         # 🧩 QR Code तयार करा
#         qr = qrcode.QRCode(
#             version=1,
#             error_correction=qrcode.constants.ERROR_CORRECT_L,
#             box_size=10,
#             border=4,
#         )
#         base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
#         report_url = f"{base_url}/download_report/ggbs/{'nabl' if nabl else 'nonnabl'}/{eln.id}"

#         qr.add_data(report_url)
#         qr.make(fit=True)
#         qr_image = qr.make_image()
#         buffered = BytesIO()
#         qr_image.save(buffered, format="PNG")
#         qr_code = base64.b64encode(buffered.getvalue()).decode()
            
#         model_id = eln.model_id
#         # differnt location for product based
#         model_name = eln.material.product_based_calculation[0].ir_model.name 
#         if model_name:
#             general_data = self.env[model_name].sudo().browse(model_id)
#         else:
#             general_data = self.env['lerm.eln'].sudo().browse(docids)

#         return {
#             'eln': eln,
#             'ggbs': general_data,
#             'qrcode': qr_code,
#             'nabl':nabl,
#         }

# class GgbsReport(models.AbstractModel):
#     _name = 'report.ggbs.lerm_ggbs_report'
#     _description = 'GGBS Report '

#     @api.model
#     def _get_report_values(self, docids, data=None):
#         data = data or {}
#         nabl = data.get('nabl', False)

#         # ELN Record मिळवा
#         if data.get('report_wizard'):
#             eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data.get('sample'))])
#         elif 'active_id' in data.get('context', {}):
#             eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data['context']['active_id'])])
#         else:
#             eln = self.env['lerm.eln'].sudo().browse(docids)

#         if not eln:
#             raise ValueError("ELN record not found")

#         # ✅ sudo वापरून parameter fetch
#         parameter_record = self.env['lerm.parameter.master'].sudo().search([
#             ('internal_id', '=', '210bgf54-baa4-466f-a6a7-044da708f265')
#         ], limit=1)

#         # QR Code
#         qr = qrcode.QRCode(
#             version=1,
#             error_correction=qrcode.constants.ERROR_CORRECT_L,
#             box_size=10,
#             border=4,
#         )
#         base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
#         report_url = f"{base_url}/download_report/ggbs/{'nabl' if nabl else 'nonnabl'}/{eln.id}"
#         qr.add_data(report_url)
#         qr.make(fit=True)

#         buffered = BytesIO()
#         qr.make_image().save(buffered, format="PNG")
#         qr_code = base64.b64encode(buffered.getvalue()).decode()

#         model_id = eln.model_id
#         model_name = eln.material.product_based_calculation[0].ir_model.name 
#         if model_name:
#             general_data = self.env[model_name].sudo().browse(model_id)
#         else:
#             general_data = self.env['lerm.eln'].sudo().browse(docids)

#         return {
#             'eln': eln,
#             'ggbs': general_data,
#             'qrcode': qr_code,
#             'nabl': nabl,
#             'parameter_record': parameter_record,  # ✅ safe access
#         }

class GgbsReport(models.AbstractModel):
    _name = 'report.ggbs.lerm_ggbs_report'
    _description = 'GGBS Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        nabl = data.get('nabl', False)

        # ✅ ELN Record मिळवा
        if data.get('report_wizard'):
            eln = self.env['lerm.eln'].sudo().search([
                ('sample_id', '=', data.get('sample'))
            ])
        elif 'active_id' in data.get('context', {}):
            eln = self.env['lerm.eln'].sudo().search([
                ('sample_id', '=', data['context']['active_id'])
            ])
        else:
            eln = self.env['lerm.eln'].sudo().browse(docids)

        if not eln:
            raise ValueError("ELN record not found")

        # ✅ सर्व unique internal_ids एकदाच define करा
        internal_ids = [
            '5214hgtb-c526-4092-a3a7-6b0ff7e69c0a',  # Fineness
            '1452fgr0-8e67-4e94-86ea-98d9472f5c71',  # Slag Activity (Header)
            '5214hgtb-c526-4092-a3a7-321478658',     # 7-day Activity
            '5214hgtb-c526-4092-a3a7-3214855pp',     # 28-day Activity
            '210bgf54-baa4-466f-a6a7-044da708f265',  # Extra Parameter
        ]

        # ✅ सर्व parameter.master records dictionary मध्ये साठवा
        ParamMaster = self.env['lerm.parameter.master'].sudo()
        parameters = {}
        for iid in internal_ids:
            record = ParamMaster.search([('internal_id', '=', iid)], limit=1)
            parameters[iid] = record

        # ✅ QR Code तयार करा
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        report_url = f"{base_url}/download_report/ggbs/{'nabl' if nabl else 'nonnabl'}/{eln.id}"
        qr.add_data(report_url)
        qr.make(fit=True)

        buffered = BytesIO()
        qr.make_image().save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()

        # ✅ General Data मिळवा
        model_id = eln.model_id
        model_name = (
            eln.material.product_based_calculation[0].ir_model.name
            if eln.material.product_based_calculation else False
        )
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)

        # ✅ सर्व data return करा
        return {
            'eln': eln,
            'ggbs': general_data,
            'qrcode': qr_code,
            'nabl': nabl,
            'parameters': parameters,  # ← dictionary QWeb मध्ये वापरण्यासाठी
        }

