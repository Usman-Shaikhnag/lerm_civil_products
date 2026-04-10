# -*- coding: utf-8 -*-
import io
import zipfile
from odoo import http
from odoo.http import request

import json
import hmac
import hashlib
import base64

SECRET_KEY = "MY_SUPER_SECRET_KEY"
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
    

    @http.route('/api/get-form', type='json', auth='user', methods=['POST'], csrf=False)
    def get_form(self, **kwargs):
        token_str = kwargs.get('token')
        if not token_str:
            return {"error": "Token missing"}

        try:
            token_data = json.loads(base64.urlsafe_b64decode(token_str).decode())
            payload = token_data["payload"]
            signature = token_data["signature"]

            # Verify signature
            expected_sig = hmac.new(SECRET_KEY.encode(), json.dumps(payload, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()
            if signature != expected_sig:
                return {"error": "Invalid token"}

            # Verify user
            if payload["user_id"] != request.env.user.id:
                return {"error": "Unauthorized"}

            # Fetch form from Odoo
            form_id = payload["form_id"]
            form = request.env['your.model'].sudo().browse(form_id)
            if not form.exists():
                return {"error": "Form not found"}

            return {
                "id": form.id,
                "name": form.name,
                "field_1": form.field_1,
                "field_2": form.field_2
            }

        except Exception as e:
            return {"error": str(e)}