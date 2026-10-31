from odoo import models, api
import base64
import qrcode
import datetime
from io import BytesIO


class ManholeCoverReport(models.AbstractModel):
    _name = 'report.manhole_cover.manhole_report'
    _description = 'Manhole Cover Frame Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        nabl = data.get('nabl', False)

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
        qr_static.add_data("https://www.lerm.in")
        qr_static.make(fit=True)
        buf_static = BytesIO()
        qr_static.make_image(fill_color="black", back_color="white").save(buf_static, format="PNG")
        qr_static_b64 = base64.b64encode(buf_static.getvalue()).decode()

        # QR of the report itself
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        report_url = f"{base_url}/report/pdf/manhole_cover.manhole_report/{eln.id}"

        qr.add_data(report_url)
        qr.make(fit=True)
        qr_image = qr.make_image()
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()

        # General Data
        general_data = self.env['manhole.cover.frame'].sudo().browse(eln.model_id) if eln.model_id else eln

        return {
            'eln': eln,
            'data': general_data,
            'qrcode': qr_code,
            'qrcode_static': qr_static_b64,
            'nabl': nabl,
        }


class ManholeCoverDatasheet(models.AbstractModel):
    _name = 'report.manhole_cover.manhole_datasheet'
    _description = 'Manhole Cover Frame DataSheet'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        context = data.get('context', {})
        eln = self.env['lerm.eln'].sudo()
        if data.get('fromsample') and 'active_id' in context:
            eln = eln.search([('sample_id', '=', context['active_id'])], limit=1)
        elif data.get('report_wizard'):
            eln = eln.search([('id', '=', data.get('eln'))], limit=1)
        elif data.get('eln_id'):
            eln = eln.browse(data.get('eln_id'))
        else:
            eln = eln.browse(docids)

        general_data = self.env['manhole.cover.frame'].sudo().browse(eln.model_id) if eln.model_id else eln

        return {
            'eln': eln,
            'data': general_data,
        }
