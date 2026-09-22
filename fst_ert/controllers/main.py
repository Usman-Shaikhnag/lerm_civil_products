import json
import hmac
import hashlib
from io import BytesIO
import zipfile
import base64

from odoo import http
from odoo.http import request


class SoilResistivityReportController(http.Controller):

    @http.route("/soil_resistivity/reports/zip/<int:parent_id>", type="http", auth="user")
    def download_zip(self, parent_id):
        parent = request.env["lerm.ert.parent"].browse(parent_id)
        if not parent.exists():
            return request.not_found()

        soil_resistivity_records = parent.mapped("ert_lines.soil_resistivity_id")
        if not soil_resistivity_records:
            return request.not_found()

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for rec in soil_resistivity_records:
                report = request.env.ref("fst_ert.soil_resistivity_report_py3o1")
                file_content, _ = report._render(rec.ids)
                zipf.writestr(f"{rec.name or rec.id}.docx", file_content)

        zip_buffer.seek(0)

        attachment = request.env["ir.attachment"].create({
            "name": f"{parent.name}_ERT_Reports.zip",
            "type": "binary",
            "datas": base64.b64encode(zip_buffer.getvalue()),
            "res_model": "lerm.ert.parent",
            "res_id": parent.id,
            "mimetype": "application/zip",
        })

        return request.make_response(
            zip_buffer.getvalue(),
            headers=[
                ("Content-Type", "application/zip"),
                ("Content-Disposition", f'attachment; filename="{parent.name}_ERT_Reports.zip"'),
            ],
        )

    @http.route("/api/get-form", type="json", methods=["POST"], auth="user")
    def get_form(self):
        token = request.params.get("token", "")
        expected_hmac = hmac.new(
            b"your-secret-key",
            token.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(token, expected_hmac):
            return {"error": "Invalid token"}
        return {"form": request.env["lerm.ert.parent"].search([]).read()}
