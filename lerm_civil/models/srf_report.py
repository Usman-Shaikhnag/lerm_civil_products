from odoo import models , fields,api
import json
import base64
import qrcode
from io import BytesIO

class SrfReport(models.AbstractModel):
    _name = 'report.lerm_civil.srf_report_template'
    _description = 'SRF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # srf = self.env['lerm.civil.srf'].sudo().browse(srf_id)
        # import wdb;wdb.set_trace();

        srf = self.env['lerm.civil.srf'].sudo().browse(docids)
        sample = self.env["lerm.srf.sample"].search([('srf_id','=', srf.id)])
        # qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        # qr.add_data(srf.kes_number)
        # qr.make(fit=True)
        # qr_image = qr.make_image()

        # Convert the QR code image to base64 string
        # buffered = BytesIO()
        # qr_image.save(buffered, format="PNG")
        # qr_image_base64 = base64.b64encode(buffered.getvalue()).decode()
        # qr_code = qr_image_base64
        # eln_record = self.env['lerm.eln'].search([('srf_id', '=', self.srf_id)], limit=1)
        # print(eln_record , 'eln record')
        return {
                'srf': srf,
                'sample' : sample
            }
