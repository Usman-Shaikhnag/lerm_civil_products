# from odoo import http
# from odoo.http import request, content_disposition
# import json
# import werkzeug
# import re
# import time
# from werkzeug.urls import url_decode
# from odoo.tools.safe_eval import safe_eval

# class ReportDownloadControllerOPC(http.Controller):
#     @http.route(['/download_report/opcc/nabl/<int:eln_id>'], type='http', auth='public', website=True, csrf=False)
#     def download_report_nabl_opc(self, eln_id, **kw):
#         try:
#             eln = request.env['lerm.eln'].sudo().browse(eln_id)
#             if not eln.exists():
#                 return werkzeug.exceptions.NotFound("ELN record not found")

#             report_name = 'cement_opc.opc_report'
#             pdf_content, _ = request.env['ir.actions.report']._render_qweb_pdf(
#                 report_name, res_ids=[eln.id], data={'nabl': True}
#             )

#             filename = f"{eln.kes_no or 'report'}_NABL.pdf"
#             headers = [
#                 ('Content-Type', 'application/pdf'),
#                 ('Content-Length', len(pdf_content)),
#                 ('Content-Disposition', content_disposition(filename)),
#             ]
#             return request.make_response(pdf_content, headers=headers)
#         except Exception as e:
#             return request.make_response(
#                 f"Internal Server Error (NABL): {str(e)}",
#                 headers=[('Content-Type', 'text/plain')],
#                 status=500,
#             )

#     @http.route(['/download_report/opcc/nonnabl/<int:eln_id>'], type='http', auth='public', website=True, csrf=False)
#     def download_report_nonnabl_opc(self, eln_id, **kw):
#         try:
#             eln = request.env['lerm.eln'].sudo().browse(eln_id)
#             if not eln.exists():
#                 return werkzeug.exceptions.NotFound("ELN record not found")

#             report_name = 'cement_opc.opc_report'
#             pdf_content, _ = request.env['ir.actions.report']._render_qweb_pdf(
#                 report_name, res_ids=[eln.id], data={'nabl': False}
#             )

#             filename = f"{eln.kes_no or 'report'}_NonNABL.pdf"
#             headers = [
#                 ('Content-Type', 'application/pdf'),
#                 ('Content-Length', len(pdf_content)),
#                 ('Content-Disposition', content_disposition(filename)),
#             ]
#             return request.make_response(pdf_content, headers=headers)
#         except Exception as e:
#             return request.make_response(
#                 f"Internal Server Error (Non-NABL): {str(e)}",
#                 headers=[('Content-Type', 'text/plain')],
#                 status=500,
#             )