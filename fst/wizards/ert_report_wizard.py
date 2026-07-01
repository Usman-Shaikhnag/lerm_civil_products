from odoo import models, fields, api
import io
import zipfile
import base64


class ERTReportWizard(models.TransientModel):
    _name = "ert.report.wizard"
    _description = "ERT Report Wizard"

    parent_id = fields.Many2one("lerm.ert.parent", string="Parent", required=True)
    line_ids = fields.One2many("ert.report.wizard.line", "wizard_id", string="ERT Lines")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        parent_id = self.env.context.get("active_id")
        if parent_id:
            parent = self.env["lerm.ert.parent"].browse(parent_id)
            res["parent_id"] = parent.id
            res["line_ids"] = [
                (0, 0, {"line_id": line.id, "selected": True})
                for line in parent.ert_lines
            ]
        return res

    def action_print_reports(self):
        selected_lines = self.line_ids.filtered("selected").mapped("line_id")
        soil_resistivity_records = selected_lines.mapped("soil_resistivity_id")
        if not soil_resistivity_records:
            return

        if len(soil_resistivity_records) == 1:
            return self.env.ref(
                "fst.soil_resistivity_report_py3o"
            ).report_action(soil_resistivity_records)

        # multiple → zip
        import io, zipfile, base64
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for rec in soil_resistivity_records:
                file_content, _ = self.env["ir.actions.report"]._render_py3o(
                    "fst.soil_resistivity_report_py3o",
                    [rec.id],
                    data=None,
                )
                zipf.writestr(f"{rec.name or rec.id}.docx", file_content)

        zip_buffer.seek(0)

        attachment = self.env["ir.attachment"].create({
            "name": f"{self.parent_id.name}_ERT_Reports.zip",
            "type": "binary",
            "datas": base64.b64encode(zip_buffer.getvalue()),
            "res_model": "lerm.ert.parent",
            "res_id": self.parent_id.id,
            "mimetype": "application/zip",
        })

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }


class ERTReportWizardLine(models.TransientModel):
    _name = "ert.report.wizard.line"
    _description = "ERT Report Wizard Line"

    wizard_id = fields.Many2one("ert.report.wizard", ondelete="cascade")
    line_id = fields.Many2one("ert.lines", string="ERT Line", required=True)
    selected = fields.Boolean("Include")

    soil_resistivity_id = fields.Many2one(related="line_id.soil_resistivity_id", string="Soil Resistivity", readonly=True)