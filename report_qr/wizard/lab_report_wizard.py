from odoo import models, fields

class LabReportWizard(models.TransientModel):
    _name = "lab.report.wizard"
    _description = "Wizard to create Lab Report"

    date = fields.Date(string="Date", default=fields.Date.context_today)
    partner_id = fields.Many2one("res.partner", string="Customer")
    material = fields.Many2one("product.template", string="Material")
    ulr = fields.Char(string="ULR")
    nabl_scope_id = fields.Many2one("lerm.lab.master", string="Lab")
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
    left_qr_boolean = fields.Boolean(string="Nabl Scope Link",default=True)
    right_qr_boolean = fields.Boolean(string="Report Link",default=True)

    def action_create_report(self):
        self.ensure_one()

        report = self.env["lab.report"].create(
            {
                "date": self.date,
                "partner_id": self.partner_id.id,
                "material": self.material.id,
                "ulr": self.ulr,
                "nabl_scope_id": self.nabl_scope_id.id,
                "qr_position": self.qr_position,
                "original_pdf": self.original_pdf,
                "original_pdf_filename": self.original_pdf_filename,
                "left_qr_boolean": self.left_qr_boolean,
                "right_qr_boolean": self.right_qr_boolean,
            }
        )

        # Immediately push original file to SFTP and clear the binary
        report._upload_original_to_ftp()

        # Just close the wizard; the list behind will refresh
        return {"type": "ir.actions.act_window_close"}
