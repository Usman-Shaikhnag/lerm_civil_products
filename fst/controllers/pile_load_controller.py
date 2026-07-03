import base64
import os
import shutil
import subprocess
import tempfile

from odoo import http
from odoo.http import request


class PileLoadReportController(http.Controller):

    @http.route("/pile_load/pdf/<int:record_id>",type="http",auth="user",)
    def download_pdf(self, record_id, **kw):

        report = request.env.ref("fst.vertical_pile_load_report_py3o_pdf")

        pdf_content, filetype = report._render_py3o(
            report.report_name,
            [record_id],
        )

        # import wdb;wdb.set_trace()

        assert filetype == "pdf"

        return request.make_response(
            pdf_content,
            headers=[
                ("Content-Type", "application/pdf"),
                (
                    "Content-Disposition",
                    'attachment; filename="Vertical_Pile_Load_Report.pdf"',
                ),
            ],
        )