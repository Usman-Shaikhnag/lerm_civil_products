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




# class OPCReport(models.AbstractModel):
#     _name = 'report.cement_opc.opc_report'
#     _description = 'OPC Cement Report'

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
#         report_url = f"{base_url}/download_report/opcc/{'nabl' if nabl else 'nonnabl'}/{eln.id}"

#         qr.add_data(report_url)
#         qr.make(fit=True)
#         qr_image = qr.make_image()
#         buffered = BytesIO()
#         qr_image.save(buffered, format="PNG")
#         qr_code = base64.b64encode(buffered.getvalue()).decode()

#         # 🧩 Product Based Model मिळवा
#         product_data = {
#             "material_id": eln.material.id,
#             "grade_id": eln.grade_id.id,
#         }
#         model_name = eln.get_product_base_calc_line(product_data).ir_model.model
#         cement_data = self.env[model_name].sudo().browse(eln.model_id)

#         return {
#             'eln': eln,
#             'cement': cement_data,
#             'qrcode': qr_code,
#             'nabl': nabl,
#         }

class OPCReport(models.AbstractModel):
    _name = 'report.cement_opc.opc_report'
    _description = 'OPC Cement Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        nabl = data.get('nabl', False)

        # 🧩 ELN Record मिळवा
        if data.get('report_wizard'):
            eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data.get('sample'))])
        elif 'active_id' in data.get('context', {}):
            eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data['context']['active_id'])])
        else:
            eln = self.env['lerm.eln'].sudo().browse(docids)

        # Static QR
        qr_static = qrcode.QRCode(box_size=6, border=2)
        qr_static.add_data("https://nablwp.qci.org.in/CertificateScopenew?x=VnSUYFrXOFAdSMq5zAgzIw==&p=1&src=P&LS=balhcraes")
        qr_static.make(fit=True)
        buf_static = BytesIO()
        qr_static.make_image(fill_color="black", back_color="white").save(buf_static, format="PNG")
        qr_static_b64 = base64.b64encode(buf_static.getvalue()).decode()

        if not eln:
            raise ValueError("ELN record not found")

        # 🧩 QR Code तयार करा
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        report_url = f"{base_url}/download_report/opcc/{'nabl' if nabl else 'nonnabl'}/{eln.id}"
        qr.add_data(report_url)
        qr.make(fit=True)
        qr_image = qr.make_image()
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()

        # 🧩 Product Based Model मिळवा
        product_data = {
            "material_id": eln.material.id,
            "grade_id": eln.grade_id.id,
        }
        model_name = eln.get_product_base_calc_line(product_data).ir_model.model
        cement_data = self.env[model_name].sudo().browse(eln.model_id)

        # 🧩 Parameters dict तयार करा
        internal_ids = [
            '3214578nbhgt2-372f-4775-9bcb-e9dd723547htui',  # consistency
            '3214578nbhgt2-372f-4775-9bcb-e9dd321456yytr',  # initial setting
            '3214578nbhgt2-372f-4775-9bcb-e9dd654789nnghh',  # final setting
            '254gt2547-372f-4775-9bcb-e9dd70e3587g',        # density
            '87ye7425-30fe-4043-b518-987456321r',           # autoclave
            '87ye7425-30fe-4043-b518-32145698jj',           # le-chatelier
            '63te7425-30fe-4043-b518-0102147hhytr',         # fineness
            '87ye7425-30fe-4043-b518-4578tyre0',            # compressive header
            '147frrt012-372f-4775-9bcb-e9dd651478trew',     # 3 days
            '1236547ffv-372f-4775-9bcb-e9dd987ytre14g',     # 7 days
            '00rrrttt887-372f-4775-9bcb-e9dd987nnhtre1',    # 28 days
        ]

        parameters = {}
        for pid in internal_ids:
            param = self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', pid)], limit=1)
            parameters[pid] = param

        return {
            'eln': eln,
            'cement': cement_data,
            'qrcode': qr_code,
            'qrcode_static': qr_static_b64,
            'nabl': nabl,
            'parameters': parameters,
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