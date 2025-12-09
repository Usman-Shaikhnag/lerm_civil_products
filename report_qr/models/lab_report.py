from odoo import models, fields, api
import secrets
import io
import base64
import qrcode
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfFileReader, PdfFileWriter
import paramiko
from werkzeug.utils import url_quote


class LabReport(models.Model):
    _name = "lab.report"
    _description = "Lab Report with QR codes"

    name = fields.Char(string="Name", required=True, default="New Report")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    partner_id = fields.Many2one("res.partner", string="Customer")
    material = fields.Many2one("product.template", string="Material")
    ulr = fields.Char(string="ULR")

    # NABL scope (from lerm_civil)
    nabl_scope_id = fields.Many2one(
        "lerm.lab.master",
        string="Lab",
    )

    # Original uploaded PDF (we will push to FTP)
    original_pdf = fields.Binary(string="Original PDF")
    original_pdf_filename = fields.Char(string="Original PDF Filename")

    # Path of original PDF on FTP
    original_pdf_ftp_path = fields.Char(string="Original PDF FTP Path")

    # Final PDF with both QRs embedded
    final_pdf = fields.Binary(string="Final PDF")
    final_pdf_filename = fields.Char(string="Final PDF Filename")

    # QR settings / URLs
    qr_position = fields.Selection(
        [
            ("top", "Top corners"),
            ("bottom", "Bottom corners"),
        ],
        string="QR Position",
        default="bottom",
    )

    qr_left_url = fields.Char(
        string="Left QR URL", compute="_compute_qr_urls", store=True
    )
    qr_right_url = fields.Char(
        string="Right QR URL", compute="_compute_qr_urls", store=True
    )

    left_qr_image = fields.Binary(string="Left QR Image", readonly=True)
    right_qr_image = fields.Binary(string="Right QR Image", readonly=True)

    access_token = fields.Char(string="Access Token", readonly=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("ready", "Ready"),
        ],
        default="draft",
        string="Status",
    )

    # ---------------------------------------------------------------------
    # COMPUTE URLS
    # ---------------------------------------------------------------------
    @api.depends("nabl_scope_id", "nabl_scope_id.nabl_scope_link", "final_pdf_filename","ulr","name","original_pdf",)
    def _compute_qr_urls(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        db_name = self.env.cr.dbname
        for report in self:
            # Left QR = NABL scope link
            if report.nabl_scope_id and report.nabl_scope_id.nabl_scope_link:
                report.qr_left_url = report.nabl_scope_id.nabl_scope_link
            else:
                report.qr_left_url = ""

            # Right QR = same URL as the Download button
            if base_url and report.id:
                # predict filename same as in action_generate_qr_pdf
                filename = report.final_pdf_filename or (report.ulr or report.name or "report") + "-with-qr.pdf"
                safe_filename = url_quote(filename)
                report.qr_right_url = (f"{base_url}/lab_report_qr/download/{report.id}"
                f"?db={db_name}&filename={safe_filename}")
            else:
                report.qr_right_url = ""


    # ---------------------------------------------------------------------
    # CREATE: ensure access_token
    # ---------------------------------------------------------------------
    @api.model
    def create(self, vals):
        if not vals.get("access_token"):
            vals["access_token"] = secrets.token_urlsafe(24)
        return super().create(vals)

    # ---------------------------------------------------------------------
    # FTP helpers
    # ---------------------------------------------------------------------
    def _upload_original_to_ftp(self):
        """
        Upload original_pdf to SFTP and store its path in original_pdf_ftp_path.
        Optionally clear original_pdf to avoid filestore usage.
        """
        for report in self:
            if not report.original_pdf:
                continue

            storage = self.env["ftp.storage"].sudo().search(
                [("active", "=", True)], limit=1
            )
            if not storage:
                continue

            try:
                file_binary = base64.b64decode(report.original_pdf)
            except Exception:
                continue

            filename = (
                report.original_pdf_filename
                or (report.ulr or report.name or "report") + ".pdf"
            )

            clean_filename = filename.replace(" ", "_")
            remote_dir = f"/home/{storage.name}/reports"
            remote_path = f"{remote_dir}/{clean_filename}"

            transport = paramiko.Transport((storage.host, storage.port or 22))
            transport.connect(username=storage.username, password=storage.password)
            sftp = paramiko.SFTPClient.from_transport(transport)

            try:
                sftp.stat(f"/home/{storage.name}")
            except FileNotFoundError:
                sftp.close()
                transport.close()
                continue

            try:
                sftp.stat(remote_dir)
            except FileNotFoundError:
                sftp.mkdir(remote_dir, mode=0o755)

            with BytesIO(file_binary) as f:
                sftp.putfo(f, remote_path)
            sftp.chmod(remote_path, 0o644)

            sftp.close()
            transport.close()

            report.original_pdf_ftp_path = f"{storage.name}/reports/{clean_filename}"
            # clear to avoid storing in filestore
            report.original_pdf = False

    def _get_original_pdf_bytes(self):
        """
        Return original PDF bytes either from filestore (if still present)
        or from FTP using original_pdf_ftp_path.
        """
        storage = self.env["ftp.storage"].sudo().search(
            [("active", "=", True)], limit=1
        )

        for report in self:
            # 1) From filestore
            if report.original_pdf:
                try:
                    return base64.b64decode(report.original_pdf)
                except Exception:
                    pass

            # 2) From FTP
            if report.original_pdf_ftp_path and storage:
                # if you stored "storagename/reports/file.pdf"
                relative_path = report.original_pdf_ftp_path
                if relative_path.startswith("/home/"):
                    remote_path = relative_path
                else:
                    remote_path = f"/home/{relative_path}"

                transport = paramiko.Transport((storage.host, storage.port or 22))
                transport.connect(
                    username=storage.username, password=storage.password
                )
                sftp = paramiko.SFTPClient.from_transport(transport)

                try:
                    with sftp.file(remote_path, "rb") as f:
                        data = f.read()
                finally:
                    sftp.close()
                    transport.close()

                return data

        return None

    # ---------------------------------------------------------------------
    # QR PNG helper
    # ---------------------------------------------------------------------
    def _generate_qr_png(self, data: str) -> bytes:
        """Return PNG bytes for a QR code of 'data'."""
        if not data:
            return b""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    # ---------------------------------------------------------------------
    # Generate QR + embed into PDF
    # ---------------------------------------------------------------------
    def action_generate_qr_pdf(self):
        """
        Generate QR images for qr_left_url & qr_right_url,
        embed them into original PDF on each page,
        and store result in final_pdf.
        """
        for report in self:
            original_pdf_bytes = report._get_original_pdf_bytes()
            if not original_pdf_bytes:
                continue

            left_qr_bytes = report._generate_qr_png(report.qr_left_url)
            right_qr_bytes = report._generate_qr_png(report.qr_right_url)

            if left_qr_bytes:
                report.left_qr_image = base64.b64encode(left_qr_bytes)
            if right_qr_bytes:
                report.right_qr_image = base64.b64encode(right_qr_bytes)

            if not left_qr_bytes and not right_qr_bytes:
                report.final_pdf = report.original_pdf
                report.final_pdf_filename = (
                    report.ulr or report.name or "report"
                ) + ".pdf"
                report.state = "ready"
                continue

            reader = PdfFileReader(io.BytesIO(original_pdf_bytes))
            writer = PdfFileWriter()

            num_pages = reader.getNumPages()
            for page_idx in range(num_pages):
                page = reader.getPage(page_idx)
                width = float(page.mediaBox.getWidth())
                height = float(page.mediaBox.getHeight())

                overlay_buf = io.BytesIO()
                c = canvas.Canvas(overlay_buf, pagesize=(width, height))

                qr_width = 50
                qr_height = 50
                margin = 15

                if report.qr_position == "top":
                    y = height - qr_height - margin
                else:
                    y = margin

                if left_qr_bytes:
                    left_img = ImageReader(io.BytesIO(left_qr_bytes))
                    c.drawImage(
                        left_img,
                        margin,
                        y,
                        width=qr_width,
                        height=qr_height,
                        preserveAspectRatio=True,
                        mask="auto",
                    )

                if right_qr_bytes:
                    right_img = ImageReader(io.BytesIO(right_qr_bytes))
                    c.drawImage(
                        right_img,
                        width - qr_width - margin,
                        y,
                        width=qr_width,
                        height=qr_height,
                        preserveAspectRatio=True,
                        mask="auto",
                    )

                c.showPage()
                c.save()

                overlay_buf.seek(0)
                overlay_pdf = PdfFileReader(overlay_buf)
                overlay_page = overlay_pdf.getPage(0)

                page.mergePage(overlay_page)
                writer.addPage(page)

            output_buf = io.BytesIO()
            writer.write(output_buf)
            merged_bytes = output_buf.getvalue()

            report.final_pdf = base64.b64encode(merged_bytes)
            report.final_pdf_filename = (
                report.ulr or report.name or "report"
            ) + "-with-qr.pdf"
            report.state = "ready"

    # ---------------------------------------------------------------------
    # Download
    # ---------------------------------------------------------------------
    def action_download_pdf(self):
        """
        Called from button in tree view.
        Always regenerate based on current settings, then download.
        """
        self.ensure_one()

        if self.original_pdf or self.original_pdf_ftp_path:
            self.action_generate_qr_pdf()

        if not self.final_pdf:
            return

        filename = self.final_pdf_filename or "report.pdf"
        return {
            "type": "ir.actions.act_url",
            "url": f"/lab_report_qr/download/{self.id}?filename={filename}",
            "target": "self",
        }


    def action_save_and_back(self):
        self.ensure_one()

        if self.original_pdf or self.original_pdf_ftp_path:
            self.action_generate_qr_pdf()

        # return {
        #     "type": "ir.actions.act_window",
        #     "res_model": "lab.report",
        #     "view_mode": "tree,form",
        #     "target": "current",
        #     "name": "Lab Reports",
        # }
        # Return the lab.report list action
        action = self.env.ref("report_qr.action_lab_report").read()[0]
        # Just to be explicit: open in list, not on this record
        action["res_id"] = False
        return action
