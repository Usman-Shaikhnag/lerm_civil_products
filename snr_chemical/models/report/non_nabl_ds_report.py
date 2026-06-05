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




class NBMLNONNABLReport(models.AbstractModel):
    _name = 'report.snr_chemical.snr_nbml_nonnabl_report'
    _description = 'Opc Cement Report'
    
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

        if not eln:
            raise ValueError("ELN record not found")

        # Static QR
        qr_static = qrcode.QRCode(box_size=6, border=2)
        qr_static.add_data("https://nablwp.qci.org.in/CertificateScopenew?x=4Rf+3mOSznNeFNvAasH49g==&a=MTI0NDAx")
        qr_static.make(fit=True)
        buf_static = BytesIO()
        qr_static.make_image(fill_color="black", back_color="white").save(buf_static, format="PNG")
        qr_static_b64 = base64.b64encode(buf_static.getvalue()).decode()

        # 🧩 QR Code तयार करा
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        report_url = f"{base_url}/download_report/opc/{'nabl' if nabl else 'nonnabl'}/{eln.id}"

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
            'nbml' : general_data,
            'notes_list': general_data.notes_id if hasattr(general_data, 'notes_id') and general_data.notes_id else [],
            'qrcode': qr_code,
            'nabl' : nabl,
            'qrcode_static': qr_static_b64,
            # 'stamp' : inreport_value,
        }







# class NBMLNONNABLReport(models.AbstractModel):
#     _name = 'report.nbml_nonnabl.nbml_nonnabl_report'
#     _description = 'NON NABL Report'

#     @api.model
#     def _get_report_values(self, docids, data=None):
#         data = data or {}
#         nabl = data.get('nabl', False)

#         # ================= RECORD FETCH =================
#         active_ids = self.env.context.get('active_ids') or docids
#         records = self.env['nbml.nonnabl'].sudo().browse(active_ids)

#         if not records:
#             raise ValueError(f"Record not found | docids={docids} | context={self.env.context}")

#         record = records[0]

#         # ================= ELN =================
#         eln = record

#         # ================= 🔥 SRF SAMPLE FETCH (FINAL FIX) =================
#         srf_sample = False

#         if record.sample_id:
#             # CASE 1: direct relation
#             if record.sample_id._name == 'lerm.srf.sample':
#                 srf_sample = record.sample_id

#             # CASE 2: via lerm.sample → srf_id
#             elif hasattr(record.sample_id, 'srf_id') and record.sample_id.srf_id:
#                 srf_sample = record.sample_id.srf_id

#             # CASE 3: via अन्य field (fallback)
#             elif hasattr(record.sample_id, 'srf_sample_id') and record.sample_id.srf_sample_id:
#                 srf_sample = record.sample_id.srf_sample_id

#         # ================= QR STATIC =================
#         qr_static = qrcode.QRCode(box_size=6, border=2)
#         qr_static.add_data("https://nablwp.qci.org.in/CertificateScopenew?x=4Rf+3mOSznNeFNvAasH49g==&a=MTI0NDAx")
#         qr_static.make(fit=True)

#         buf_static = BytesIO()
#         qr_static.make_image(fill_color="black", back_color="white").save(buf_static, format="PNG")
#         qr_static_b64 = base64.b64encode(buf_static.getvalue()).decode()

#         # ================= QR DYNAMIC =================
#         base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
#         report_url = f"{base_url}/download_report/opc/{'nabl' if nabl else 'nonnabl'}/{record.id}"

#         qr = qrcode.QRCode(box_size=10, border=4)
#         qr.add_data(report_url)
#         qr.make(fit=True)

#         buffer = BytesIO()
#         qr.make_image().save(buffer, format="PNG")
#         qr_code = base64.b64encode(buffer.getvalue()).decode()

#         # ================= RETURN =================
#         return {
#             'docs': records,
#             'eln': eln,
#             'nbml': record,
#             'srf_sample': srf_sample,   # 🔥 IMPORTANT
#             'qrcode': qr_code,
#             'qrcode_static': qr_static_b64,
#             'nabl': nabl,
#         }