from odoo import models
# from PyPDF2 import PdfMerger
from PyPDF2 import PdfFileMerger
import io

class ReportMerge(models.AbstractModel):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, docids=None, data=None):

        if report_ref == 'rock.rock_report':


            pdf1, _ = super()._render_qweb_pdf('lerm_civil.rock_report_first_action', docids, data=data)
            pdf2, _ = super()._render_qweb_pdf('lerm_civil.rock_report_rest_action', docids, data=data)
            merger = PdfFileMerger()
            merger.append(io.BytesIO(pdf1))
            merger.append(io.BytesIO(pdf2))

            output = io.BytesIO()
            merger.write(output)
            merger.close()

            return output.getvalue(), 'pdf'

        return super()._render_qweb_pdf(report_ref, docids, data=data)