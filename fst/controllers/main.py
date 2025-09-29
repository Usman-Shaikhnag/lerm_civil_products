# -*- coding: utf-8 -*-
import io
import zipfile
from odoo import http
from odoo.http import request


class SoilResistivityReportController(http.Controller):

    @http.route(
        "/soil_resistivity/reports/zip/<int:parent_id>",
        type="http",
        auth="user",
    )
    def download_zip(self, parent_id, **kwargs):
        parent = request.env["lerm.ert.parent"].browse(parent_id)
        if not parent.exists():
            return request.not_found()

        soil_resistivity_records = parent.mapped("ert_lines.soil_resistivity_id")
        if not soil_resistivity_records:
            return request.not_found()

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for rec in soil_resistivity_records:
                report_action = request.env.ref("fst.soil_resistivity_report_py3o")
                report_content, file_type = report_action._render_py3o([rec.id], data=None)

                file_name = f"Soil_Resistivity_{rec.name or rec.id}.docx"
                zipf.writestr(file_name, report_content)

        buffer.seek(0)
        headers = [
            ("Content-Type", "application/zip"),
            ("Content-Disposition", f'attachment; filename="Soil_Resistivity_Reports.zip"'),
        ]
        return request.make_response(buffer.getvalue(), headers=headers)
