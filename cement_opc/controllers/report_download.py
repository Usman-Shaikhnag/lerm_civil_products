from odoo import http
from odoo.http import request

class DownloadReportController(http.Controller):

    @http.route('/download_report/nabl/<int:eln_id>', type='http', auth='public', website=True)
    def download_report_nabl(self, eln_id, **kw):
        eln = request.env['lerm.eln'].sudo().browse(eln_id)
        if not eln.exists():
            return request.not_found()
        try:
            pdf = request.env.ref('cement_opc.opc_report')._render_qweb_pdf([eln_id], data={'nabl': True})[0]
            headers = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf)),
                ('Content-Disposition', f'inline; filename="nabl_report_{eln_id}.pdf"')
            ]
            return request.make_response(pdf, headers=headers)
        except Exception as e:
            return f"<h3 style='color:red'>Error generating NABL report:</h3><pre>{str(e)}</pre>"

    @http.route('/download_report/nonnabl/<int:eln_id>', type='http', auth='public', website=True)
    def download_report_non_nabl(self, eln_id, **kw):
        eln = request.env['lerm.eln'].sudo().browse(eln_id)
        if not eln.exists():
            return request.not_found()
        try:
            pdf = request.env.ref('cement_opc.opc_report')._render_qweb_pdf([eln_id], data={'nabl': False})[0]
            headers = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf)),
                ('Content-Disposition', f'inline; filename="non_nabl_report_{eln_id}.pdf"')
            ]
            return request.make_response(pdf, headers=headers)
        except Exception as e:
            return f"<h3 style='color:red'>Error generating Non-NABL report:</h3><pre>{str(e)}</pre>"
