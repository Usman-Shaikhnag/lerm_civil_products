from odoo import models , fields,api
import json
import base64
import qrcode
from io import BytesIO
from lxml import etree
from collections import defaultdict



class StainlessSteelTmtBar(models.AbstractModel):
    _name = 'report.ss_tmt_bar.stainless_steel_tmt_bar_report'
    _description = 'SS TMT Bar Report'
    
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

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(eln.kes_no)
        qr.make(fit=True)
        qr_image = qr.make_image()

        # Convert the QR code image to base64 string
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_image_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Assign the base64 string to a field in the 'srf' object
        qr_code = qr_image_base64
        model_id = eln.model_id
        # differnt location for product based
        model_name = eln.material.product_based_calculation[0].ir_model.name 
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        # Group lines by dia_of_bar
        grouped_lines = defaultdict(list)
        for line in general_data.bar_test_line_ids.filtered(lambda l: l.yield_stress > 0 and l.ultimate_tensile_stress > 0 and l.elongation > 0):
            grouped_lines[line.dia_of_bar].append(line)

        # Convert to list of tuples for sorted access in QWeb
        grouped_bar_lines = sorted(grouped_lines.items(), key=lambda x: x[0])  # sort by dia_of_bar
        # import wdb; wdb.set_trace()
        return {
            'eln': eln,
            'data' : general_data,
            'qrcode': qr_code,
             "qrcode_static": qrcode_static,
            # 'stamp' : inreport_value,
            'nabl' : nabl,
            'grouped_bar_lines': grouped_bar_lines,

        }

class StainlessSteelTmtBarDataSheet(models.AbstractModel):
    _name = 'report.ss_tmt_bar.stainless_steel_tmt_bar_datasheet'
    _description = 'SS TMT Bar DataSheet'
    
    @api.model
    def _get_report_values(self, docids, data):
        # import wdb ; wdb.set_trace()

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
        model_id = eln.model_id
        # differnt location for product based
        model_name = eln.material.product_based_calculation[0].ir_model.name 
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        return {
            'eln': eln,
            'data' : general_data
        }