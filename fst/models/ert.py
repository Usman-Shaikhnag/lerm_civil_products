from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import zipfile
from PIL import Image,ImageDraw
import io, base64, math, logging

_logger = logging.getLogger(__name__)

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

    combined_images = fields.One2many('soil.borehole.parent.image', 'parent_id', string="Combined Images", compute="_compute_combined_images", store=True)


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
    def _compute_combined_images(self):
        for record in self:
            # Clear existing records
            record.combined_images.unlink()

            images = []
            for line in record.borehole_lines:
                borehole = line.soil_borehole_id
                if borehole and borehole.graph_image:
                    try:
                        img_data = base64.b64decode(borehole.graph_image)
                        img = Image.open(io.BytesIO(img_data))
                        images.append(img)
                    except Exception as e:
                        _logger.warning(f"Skipping invalid image: {e}")

            if not images:
                continue

            grid_cols = 5
            grid_rows = 4
            thumb_w, thumb_h = 200, 200
            max_per_image = grid_cols * grid_rows

            # Split into groups of 20
            chunks = [images[i:i + max_per_image] for i in range(0, len(images), max_per_image)]

            ImageModel = self.env['soil.borehole.parent.image']

            for idx, group in enumerate(chunks, start=1):
                cols = min(grid_cols, len(group))
                rows = math.ceil(len(group) / grid_cols)
                combined_w = cols * thumb_w
                combined_h = rows * thumb_h
                combined_img = Image.new('RGB', (combined_w, combined_h), color=(255, 255, 255))

                # Paste thumbnails
                for i, img in enumerate(group):
                    img = img.copy()
                    
                    img.thumbnail((thumb_w, thumb_h))
                    
                    final_thumbnail = Image.new('RGB', (thumb_w, thumb_h), color=(255, 255, 255))
                    
                    x_offset = (thumb_w - img.width) // 2
                    y_offset = (thumb_h - img.height) // 2
                    
                    final_thumbnail.paste(img, (x_offset, y_offset))
                    
                    row, col = divmod(i, grid_cols)
                    x = col * thumb_w
                    y = row * thumb_h
                    
                    combined_img.paste(final_thumbnail, (x, y))
                # draw = ImageDraw.Draw(combined_img)
                # border_width = 4
                # draw.rectangle(
                #     [
                #         border_width - 1, 
                #         border_width - 1, 
                #         combined_img.width - (border_width), 
                #         combined_img.height - (border_width)
                #     ],
                #     outline="black",
                #     width=border_width
                # )

                # Save to binary
                buffer = io.BytesIO()
                combined_img.save(buffer, format="PNG")
                img_base64 = base64.b64encode(buffer.getvalue())

                ImageModel.create({
                    'parent_id': record.id,
                    'sequence': idx,
                    'image': img_base64,
                })


class SoilBoreholeParentImage(models.Model):
    _name = "soil.borehole.parent.image"
    _description = "Grouped Combined Images"

    parent_id = fields.Many2one('soil.borehole.parent', ondelete='cascade')
    sequence = fields.Integer("Page")
    image = fields.Binary("Combined Graph Image")


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
    