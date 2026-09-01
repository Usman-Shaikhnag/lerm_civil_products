from odoo import models
# from PyPDF2 import PdfMerger
from PyPDF2 import PdfFileMerger
import io

class ReportMerge(models.AbstractModel):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):

        if report_ref == 'soil1.soil_report1':


            pdf1, _ = super()._render_qweb_pdf('lerm_civil.soil_report_first_action', res_ids, data=data)
            pdf2, _ = super()._render_qweb_pdf('lerm_civil.soil_report_rest_action', res_ids, data=data)
            merger = PdfFileMerger()
            merger.append(io.BytesIO(pdf1))
            merger.append(io.BytesIO(pdf2))

            output = io.BytesIO()
            merger.write(output)
            merger.close()

            return output.getvalue(), 'pdf'

        return super()._render_qweb_pdf(report_ref, res_ids, data=data)