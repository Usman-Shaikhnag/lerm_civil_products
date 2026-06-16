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




class FlyashDatasheet(models.AbstractModel):
    _name = 'report.fly_ash.flyash_datasheet'
    _description = 'Fly Ash DataSheet'
    
    @api.model
    def _get_report_values(self, docids, data):
        # if 'active_id' in data['context']:
        #     eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
        # else:
        #     eln = self.env['lerm.eln'].sudo().browse(docids) 
        # model_id = eln.model_id

    
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




# class FlyashReport(models.AbstractModel):
#     _name = 'report.fly_ash.lerm_fly_report'
#     _description = 'Fly Ash Report'
    
#     @api.model
#     def _get_report_values(self, docids, data):
#         # eln = self.env['lerm.eln'].sudo().browse(docids)
#         fromEln = data.get('fromEln')
#         if data.get('report_wizard') == True:
#             eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['sample'])])
#         elif fromEln == False:
#             if 'active_id' in data.get('context',{}):
#                 eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
#             else:
#                 eln = self.env['lerm.eln'].sudo().browse(docids)
#         else:
#             if 'active_id' in data.get('context',{}):
#                 eln = self.env['lerm.eln'].sudo().search([('id','=',data['context']['active_id'])])
#             else:
#                 eln = self.env['lerm.eln'].sudo().browse(docids)
        
#         # qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
#         # qr.add_data(eln.kes_no)
#         # qr.make(fit=True)
#         # qr_image = qr.make_image()
#         qr_static = qrcode.QRCode(box_size=6, border=2)
#         qr_static.add_data("https://www.lerm.in")
#         qr_static.make(fit=True)
#         buf_static = BytesIO()
#         qr_static.make_image(fill_color="black", back_color="white").save(buf_static, format="PNG")
#         qr_static_b64 = base64.b64encode(buf_static.getvalue()).decode()

#         qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
#         # qr.add_data(eln.kes_no)
#         url = self.env['ir.config_parameter'].sudo().search([('key','=','web.base.url')]).value
#         nabl = data.get('nabl')
#         # import wdb;wdb.set_trace()

#         if nabl:
#             url = url +'/download_report/nabl/'+ str(eln.id)
#         else:
#             url = url +'/download_report/nonnabl/'+ str(eln.id)
#         qr.add_data(url)
#         qr.make(fit=True)
#         qr_image = qr.make_image()

#         # Convert the QR code image to base64 string
#         buffered = BytesIO()
#         qr_image.save(buffered, format="PNG")
#         qr_image_base64 = base64.b64encode(buffered.getvalue()).decode()

#         # Assign the base64 string to a field in the 'srf' object
#         qr_code = qr_image_base64
            
#         data = {
#             "material_id":eln.material.id,
#             "grade_id":eln.grade_id.id
#         }
#         model = eln.get_product_base_calc_line(data).ir_model.model
#         flyash_data = self.env[model].search([("id","=",eln.model_id)])
#         print(flyash_data.normal_consistency_fly_1)
#         return {
#             'eln': eln,
#             'flyash': flyash_data,
#             'qrcode': qr_code,
#             'qrcode_static': qr_static_b64,
#             'fromEln':fromEln,
#             'nabl':nabl
#         }


class FlyashReport(models.AbstractModel):
    _name = 'report.fly_ash.lerm_fly_report'
    _description = 'Fly Ash Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        nabl = data.get("nabl", False)

        # ✅ ELN Fetch
        if data.get("report_wizard"):
            eln = (
                self.env["lerm.eln"]
                .sudo()
                .search([("sample_id", "=", data.get("sample"))], limit=1)
            )
        elif data.get("context", {}).get("active_id"):
            eln = (
                self.env["lerm.eln"]
                .sudo()
                .search([("sample_id", "=", data["context"]["active_id"])], limit=1)
            )
        else:
            eln = self.env["lerm.eln"].sudo().browse(docids)

        if not eln or not eln.exists():
            raise ValueError("ELN record not found")

        # ✅ LAB FETCH
        lab = eln.sample_id.lab_location if eln.sample_id else False

        # ✅ QR LINK (थेट NABL ची मूळ लिंक QR मध्ये टाकणे)
        qr_link = lab.nabl_scope_link or ""

        qrcode_static = False  # <--- हे नाव खाली return मध्ये वापरले आहे
        if qr_link:
            # 🔳 QR Generate (NABL च्या लिंकचा QR)
            qr = qrcode.QRCode(box_size=6, border=2)
            qr.add_data(qr_link)
            qr.make(fit=True)

            buffer = BytesIO()
            qr.make_image(fill_color="black", back_color="white").save(
                buffer, format="PNG"
            )
            qrcode_static = base64.b64encode(buffer.getvalue()).decode()

        # 🧩 QR Code तयार करा
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        report_url = f"{base_url}/download_report/fly/{'nabl' if nabl else 'nonnabl'}/{eln.id}"

        qr.add_data(report_url)
        qr.make(fit=True)
        qr_image = qr.make_image()
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
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
        
        return {
            'eln': eln,
            'flyash' : general_data,
            'notes_list': general_data.notes_id if hasattr(general_data, 'notes_id') and general_data.notes_id else [],
            'qrcode': qr_code,
            'nabl' : nabl,
            "qrcode_static": qrcode_static,
        }
