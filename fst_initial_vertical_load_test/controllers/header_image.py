import base64

from odoo import http
from odoo.http import request


class InitialVerticalLoadHeaderImageController(http.Controller):

    @http.route(
        "/fst_initial_vertical_load_test/header_image/<int:lab_id>",
        type="http",
        auth="public",
        csrf=False,
    )
    def header_image(self, lab_id):
        lab = request.env["lerm.lab.master"].sudo().browse(lab_id)
        data = lab.header_image
        if not data:
            return request.not_found()
        raw = base64.b64decode(data) if isinstance(data, bytes) else data
        attachment = request.env["ir.attachment"].sudo().search([
            ("res_model", "=", "lerm.lab.master"),
            ("res_field", "=", "header_image"),
            ("res_id", "=", lab_id),
        ], limit=1)
        mimetype = attachment.mimetype or "image/png"
        return request.make_response(
            raw,
            headers=[("Content-Type", mimetype)],
        )
