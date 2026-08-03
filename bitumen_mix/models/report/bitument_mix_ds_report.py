from odoo import models , fields,api
import json
import base64
import qrcode
from io import BytesIO
from lxml import etree

class BitumenMixDatasheet(models.AbstractModel):
        _name = 'report.bitumen_mix.bitumen_mix_datasheet_sm'
        _description = 'Bitumen Mix Datasheet'
    
        @api.model
        def _get_report_values(self, docids, data):
            # if 'active_id' in data['context']:
            #     eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
            # else:
            #     eln = self.env['lerm.eln'].sudo().browse(docids) 
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
            print(eln.material.parameter_table1[0].parameter_name , 'parameter')
            parameter_data = self.env['lerm.parameter.master'].sudo().search([('internal_id','=',eln.material.parameter_table1[0].internal_id)])
            model_id = eln.model_id
            model_name = eln.material.product_based_calculation[0].ir_model.name 
            if model_name:
                general_data = self.env[model_name].sudo().browse(model_id)
            else:
                general_data = self.env['lerm.eln'].sudo().browse(docids)
            return {
                'eln': eln,
                'data' : general_data,
                'parameter' : parameter_data
            }
        



class BitumenMixReport(models.AbstractModel):
    _name = 'report.bitumen_mix.bitumen_mix_report_sm'
    _description = 'Bitumen Mix Report'


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

        # ✅ QR LINK 
        qr_link = lab.nabl_scope_link or ""

        qrcode_static = False  
        if qr_link:
            # 🔳 QR Generate 
            qr = qrcode.QRCode(box_size=6, border=2)
            qr.add_data(qr_link)
            qr.make(fit=True)

            buffer = BytesIO()
            qr.make_image(fill_color="black", back_color="white").save(
                buffer, format="PNG"
            )
            qrcode_static = base64.b64encode(buffer.getvalue()).decode()

        # Odoo Report Download QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        report_url = f"{base_url}/download_report/bitumen_mix/{'nabl' if nabl else 'nonnabl'}/{eln.id}"

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
            if eln.material.product_based_calculation
            else False
        )
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env["lerm.eln"].sudo().browse(docids)

        return {
            "eln": eln,
            "data": general_data,
            "qrcode": qr_code,  
            "qrcode_static": qrcode_static,
            "nabl": nabl,
        }

    
    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     data = data or {}
    #     nabl = data.get('nabl', False)

    #     # 🧩 ELN Record मिळवा
    #     if data.get('report_wizard'):
    #         eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data.get('sample'))])
    #     elif 'active_id' in data.get('context', {}):
    #         eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data['context']['active_id'])])
    #     else:
    #         eln = self.env['lerm.eln'].sudo().browse(docids)

    #     if not eln:
    #         raise ValueError("ELN record not found")

    #     # Static QR
    #     qr_static = qrcode.QRCode(box_size=6, border=2)
    #     qr_static.add_data("https://www.lerm.in")
    #     qr_static.make(fit=True)
    #     buf_static = BytesIO()
    #     qr_static.make_image(fill_color="black", back_color="white").save(buf_static, format="PNG")
    #     qr_static_b64 = base64.b64encode(buf_static.getvalue()).decode()

    #     # 🧩 QR Code तयार करा
    #     qr = qrcode.QRCode(
    #         version=1,
    #         error_correction=qrcode.constants.ERROR_CORRECT_L,
    #         box_size=10,
    #         border=4,
    #     )
    #     base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     report_url = f"{base_url}/download_report/bitumenm/{'nabl' if nabl else 'nonnabl'}/{eln.id}"

    #     qr.add_data(report_url)
    #     qr.make(fit=True)
    #     qr_image = qr.make_image()
    #     buffered = BytesIO()
    #     qr_image.save(buffered, format="PNG")
    #     qr_code = base64.b64encode(buffered.getvalue()).decode()

    #      # ✅ General Data मिळवा
    #     model_id = eln.model_id
    #     model_name = (
    #         eln.material.product_based_calculation[0].ir_model.name
    #         if eln.material.product_based_calculation else False
    #     )
    #     if model_name:
    #         general_data = self.env[model_name].sudo().browse(model_id)
    #     else:
    #         general_data = self.env['lerm.eln'].sudo().browse(docids)
        
    #     return {
    #         'eln': eln,
    #         'data' : general_data,
    #         'qrcode': qr_code,
    #         'nabl' : nabl,
    #         'qrcode_static': qr_static_b64,
    #         # 'stamp' : inreport_value,
    #         'nabl' : nabl
    #     }
