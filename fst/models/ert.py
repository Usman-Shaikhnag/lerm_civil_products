from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import io
import zipfile
import base64
from PIL import Image


class LermErtParent(models.Model):
    _name = "lerm.ert.parent"
    _rec_name = "name"

    name = fields.Char("Project Name")
    ert_lines = fields.One2many('ert.lines','parent_id',"ERT Lines")
    rec_date  = fields.Date("Date")

    def create_ert(self):
        
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'ert.soil.resistivity',   # must match the target model's _name
            'target': 'current',
            'context': {
                'default_ert_parent_id':self.id
            }
        }

    # def action_print_soil_resistivity_report(self):
    #     report = self.env.ref('fst.soil_resistivity_report_py3o')
    #     filename = f"{self.name or 'ERT'}"
    #     return report.report_action(self, config={'report_name': filename})

    def print_report(self):
        report = self.env.ref('fst.soil_resistivity_report_py3o1')
        filename = f"{self.name or 'ERT'}"
        return report.report_action(self, config={'report_name': filename})
      
    # def print_report(self):
    #     # Collect soil resistivity records
    #     soil_resistivity_records = self.mapped("ert_lines.soil_resistivity_id")
    #     if not soil_resistivity_records:
    #         return

    #     # If only 1 record → download directly
    #     if len(soil_resistivity_records) == 1:
    #         return self.env.ref(
    #             'fst.soil_resistivity_report_py3o'
    #         ).report_action(soil_resistivity_records)

    #     # Else → generate all and zip them
    #     zip_buffer = io.BytesIO()
    #     with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
    #         for rec in soil_resistivity_records:
    #             report = self.env.ref("fst.soil_resistivity_report_py3o")
    #             file_content, _ = self.env['ir.actions.report']._render_py3o(
    #                 "fst.soil_resistivity_report_py3o",
    #                 [rec.id],
    #                 data=None
    #             )
    #             zipf.writestr(f"{rec.name or rec.id}.docx", file_content)

    #     zip_buffer.seek(0)

    #     # Save as attachment
    #     attachment = self.env["ir.attachment"].create({
    #         "name": rec.name +".zip",
    #         "type": "binary",
    #         "datas": base64.b64encode(zip_buffer.getvalue()),
    #         "res_model": self._name,
    #         "res_id": self.id,
    #         "mimetype": "application/zip",
    #     })

    #     # Return download action
    #     return {
    #         "type": "ir.actions.act_url",
    #         "url": f"/web/content/{attachment.id}?download=true",
    #         "target": "self",
    #     }

class SoilBoreholeParent(models.Model):
    _name = "soil.borehole.parent"
    _rec_name = "name"

    name = fields.Char("Project Name")
    borehole_lines = fields.One2many('soil.borehole.lines','parent_id',"ERT Lines")
    rec_date  = fields.Date("Date")

    combined_image = fields.Binary("Combined Graph Image", compute="_compute_combined_image", store=True)
    def create_ert(self):
        
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'soil.borehole',   # must match the target model's _name
            'target': 'current',
            'context': {
                'default_parent_id':self.id
            }
        }
    
    def print_report(self):
        report = self.env.ref('fst.borehole_report_py3o')
        filename = f"{self.name or 'ERT'}"
        return report.report_action(self, config={'report_name': filename})
    
    @api.depends('borehole_lines.soil_borehole_id.graph_image')
    def _compute_combined_image(self):
        for record in self:
            images = []
            # Loop through borehole lines
            for line in record.borehole_lines:
                borehole = line.soil_borehole_id
                if borehole and borehole.graph_image:
                    img_data = base64.b64decode(borehole.graph_image)
                    img = Image.open(io.BytesIO(img_data))
                    images.append(img)

            if images:
                # Grid setup
                grid_cols = 5
                thumb_width = 200
                thumb_height = 200

                # Resize thumbnails
                thumbs = []
                for img in images:
                    img = img.copy()
                    img.thumbnail((thumb_width, thumb_height))
                    thumbs.append(img)

                cols = min(grid_cols, len(thumbs))
                rows = math.ceil(len(thumbs) / grid_cols)

                combined_width = cols * thumb_width
                combined_height = rows * thumb_height

                # Create blank image
                combined_img = Image.new('RGB', (combined_width, combined_height), color=(255, 255, 255))

                # Paste images
                for idx, thumb in enumerate(thumbs):
                    row = idx // grid_cols
                    col = idx % grid_cols
                    x = col * thumb_width
                    y = row * thumb_height
                    combined_img.paste(thumb, (x, y))

                # Save to binary
                buffer = io.BytesIO()
                combined_img.save(buffer, format="PNG")
                record.combined_image = base64.b64encode(buffer.getvalue())
            else:
                record.combined_image = False


class LermErtLines(models.Model):
    _name = "ert.lines"  

    parent_id = fields.Many2one('lerm.ert.parent') 
    soil_resistivity_id = fields.Many2one('ert.soil.resistivity')

class SoilBoreholeLines(models.Model):
    _name = "soil.borehole.lines" 

    parent_id = fields.Many2one('soil.borehole.parent') 
    soil_borehole_id = fields.Many2one('soil.borehole')

class ERTDashboard(models.Model):
    _name = "lerm.ert.dashboard"
    _description = "ERT Dashboard"

    def search(self, args, offset=0, limit=None, order=None, count=False):
    # always show 1 record
        res = super(ERTDashboard, self).search(args, offset=offset, limit=limit, order=order, count=count)
        if not res and not count:
            return self.create({})
        return res
    