from odoo import http
from odoo.http import request
import base64
from werkzeug.exceptions import NotFound
import logging
_logger = logging.getLogger(__name__)

class LabReportDownload(http.Controller):
    
    @http.route('/lab_report_qr/download/<int:report_id>', type='http', auth='public', website=True)
    def download_report(self, report_id, filename=None, **kwargs):
        """
        Internal download URL used by the Download button.
        Returns the final PDF with QRs for the given lab.report.
        """
        report = request.env['lab.report'].sudo().browse(report_id)
        if not report or not report.exists():
            return request.not_found()

        if not report.final_pdf:
            # optionally try to generate on the fly
            if report.original_pdf or report.original_pdf_ftp_path:
                report.action_generate_qr_pdf()
            if not report.final_pdf:
                return request.not_found()

        pdf_data = base64.b64decode(report.final_pdf)
        filename = filename or report.final_pdf_filename or "report.pdf"

        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'attachment; filename="{filename}"'),
        ]
        return request.make_response(pdf_data, headers=headers)
