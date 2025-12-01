from odoo import models, fields

class LabReportWizard(models.TransientModel):
    _name = "lab.report.wizard"
    _description = "Wizard to create Lab Report"

    date = fields.Date(string="Date", default=fields.Date.context_today)
    partner_id = fields.Many2one("res.partner", string="Customer")
    material = fields.Char(string="Material")
    ulr = fields.Char(string="ULR")
    nabl_scope_id = fields.Many2one("lerm.lab.master", string="NABL Scope")
    qr_position = fields.Selection(
        [
            ("top", "Top corners"),
            ("bottom", "Bottom corners"),
        ],
        string="QR Position",
        default="bottom",
    )
    original_pdf = fields.Binary(string="Upload PDF", required=True)
    original_pdf_filename = fields.Char(string="Filename")

    def action_create_report(self):
        self.ensure_one()
        # Build URLs (dummy now, you’ll adjust later)
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")

        # left QR: NABL scope URL (you’ll take from nabl_scope_id)
        left_url = ""
        if self.nabl_scope_id and self.nabl_scope_id.nabl_scope_link:
            left_url = self.nabl_scope_id.nabl_scope_link
        else:
            left_url = base_url  # fallback

        # right QR: link to this report's public page (we'll implement later)
        # we don't yet have access_token because we haven't created the record.
        # we will create the report first, then compute qr_right_url later, for now store base_url.
        report = self.env["lab.report"].create(
            {
                "date": self.date,
                "partner_id": self.partner_id.id,
                "material": self.material,
                "ulr": self.ulr,
                "nabl_scope_id": self.nabl_scope_id.id,
                "qr_position": self.qr_position,
                "original_pdf": self.original_pdf,
                "qr_left_url": left_url,
                # qr_right_url will be updated after we know access_token
            }
        )

        # now compute qr_right_url using access_token
        report.qr_right_url = f"{base_url}/my/report/{report.access_token}/pdf"

        # optionally generate final pdf immediately
        # report.action_generate_qr_pdf()

        return {
            "type": "ir.actions.act_window",
            "res_model": "lab.report",
            "view_mode": "tree,form",
            "target": "current",
        }
