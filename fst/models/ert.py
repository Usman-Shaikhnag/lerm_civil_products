from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import zipfile
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import io, base64, math, logging
import matplotlib.pyplot as plt
from matplotlib import patches as mpatches

_logger = logging.getLogger(__name__)

PATTERN_MAP_FOR_LEGEND = {
    "GW": ("#B8B8A0", "."),
    "GP": ("#B8B8A0", "o"),
    "GM": ("#A0A080", "/."),
    "GC": ("#909070", "+"),

    "SW": ("#FFFF99", "\\\\"),
    "SP": ("#FFFF66", "....."),
    "SM": ("#E0E0A0", ".-"),
    "SC": ("#DDAA88", "-."),

    "ML": ("#D3D3D3", ":"),
    "CL": ("#ADD8E6", "----"),
    "OL": ("#7B68EE", "/-"),
    "MH": ("#B0C4DE", "|||"),
    "CH": ("#5D8AA8", "x"),
    "OH": ("#4B371C", "/"),

    "PT": ("#556B2F", "v"),

    "HR": ("#666666", "xx"),  # Hard Rock
    "SR": ("#B0A080", "\\"),  # Soft Rock
    "MI": ("#B0C4DE", "|||"),     # Same as MH
    "CI": ("#ADD8E6", "----"),    # Same as CL
    "CL-ML": ("#ADD8E6", "----"), # Same as CL
    "Inorganic-Clays": ("#5D8AA8", "x"),
    "Organic-Clays": ("#4B371C", "/"),
    "Peat": ("#556B2F", "v"),
    
    "DEFAULT": ("white", None),
}


def make_legend_image(legend_items):
    """
    legend_items: list of (facecolor, hatch, label)
    Returns a PIL.Image or None.
    """
    if not legend_items:
        return None

    n = len(legend_items)

    # ---- COMPACT, REPORT-FRIENDLY SIZE ----
    row_h = 0.32                # inches per row
    fig_w = 3.6                 # inches
    fig_h = max(1.2, row_h * n)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis('off')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, n)

    for i, (facecolor, hatch, label) in enumerate(legend_items):
        y = n - 1 - i

        # Smaller, cleaner rectangle
        rect = mpatches.Rectangle(
            (0.04, y + 0.28),   # x, y
            0.10,               # width
            0.44,               # height
            facecolor=facecolor,
            edgecolor='black',
            hatch=hatch or '',
            linewidth=0.8
        )
        ax.add_patch(rect)

        ax.text(
            0.27, y + 0.5,
            label,
            va='center',
            ha='left',
            fontsize=8.5,
        )

    buf = io.BytesIO()
    fig.savefig(
        buf,
        format='png',
        dpi=120,                # IMPORTANT: lower DPI
        bbox_inches='tight',
        facecolor='white'
    )
    plt.close(fig)

    buf.seek(0)
    return Image.open(buf).convert('RGB')



# def draw_hatch_pattern(base_img, bbox, hatch, line_color="black", spacing=4):
#     """Approximate matplotlib hatches inside bbox using Pillow, clipped to box."""
#     if not hatch:
#         return

#     x0, y0, x1, y1 = bbox
#     # Ensure integer coordinates for PIL
#     x0, y0, x1, y1 = map(int, (x0, y0, x1, y1))
#     w = x1 - x0
#     h = y1 - y0
#     if w <= 0 or h <= 0:
#         return

#     # Draw on a separate transparent layer (clipping to 0..w,0..h)
#     layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
#     d = ImageDraw.Draw(layer)

#     for ch in hatch:
#         if ch == '/':
#             for offset in range(-h, w, spacing):
#                 d.line((offset, h, offset + h, 0), fill=line_color, width=1)

#         elif ch == '\\':
#             for offset in range(-h, w, spacing):
#                 d.line((offset, 0, offset + h, h), fill=line_color, width=1)

#         elif ch == '-':
#             for y in range(0, h, spacing):
#                 d.line((0, y, w, y), fill=line_color, width=1)

#         elif ch == '|':
#             for x in range(0, w, spacing):
#                 d.line((x, 0, x, h), fill=line_color, width=1)

#         elif ch == 'x':
#             for offset in range(-h, w, spacing):
#                 d.line((offset, h, offset + h, 0), fill=line_color, width=1)
#                 d.line((offset, 0, offset + h, h), fill=line_color, width=1)

#         elif ch in ('.', ':'):
#             for y in range(0, h, spacing):
#                 for x in range(0, w, spacing):
#                     d.ellipse((x, y, x + 1, y + 1), fill=line_color)

#         elif ch == 'o':
#             r = 2
#             for y in range(0, h, spacing * 2):
#                 for x in range(0, w, spacing * 2):
#                     d.ellipse((x, y, x + r, y + r),
#                               outline=line_color, width=1)

#         elif ch == 'v':
#             for y in range(0, h, spacing * 2):
#                 for x in range(0, w, spacing * 2):
#                     d.line((x, y, x + 2, y + 3), fill=line_color, width=1)
#                     d.line((x + 4, y, x + 2, y + 3),
#                            fill=line_color, width=1)

#     # Paste pattern layer back onto the base image, clipped by its alpha
#     base_img.paste(layer, (x0, y0), layer)



class LermErtParent(models.Model):
    _name = "lerm.ert.parent"
    _rec_name = "name"

    name = fields.Char("Project Name")
    ert_lines = fields.One2many('ert.lines','parent_id',"ERT Lines", copy=False)
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
    
    def open_editor(self):
        self.ensure_one()
        frontend_base_url = "http://localhost:5173"  # your React app URL
        url = f'{frontend_base_url}/report?id={self.id}'
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',  # open in a new tab
        }

    # def action_print_soil_resistivity_report(self):
    #     report = self.env.ref('fst.soil_resistivity_report_py3o')
    #     filename = f"{self.name or 'ERT'}"
    #     return report.report_action(self, config={'report_name': filename})

    def print_report(self):
        report = self.env.ref('fst.soil_resistivity_report_py3o1')
        filename = f"{self.name or 'ERT'}"
        return report.report_action(self, config={'report_name': filename})
    

    
    def copy_data(self, default=None):
        """Prevent automatic copying of One2many lines"""
        data = super().copy_data(default)[0]
        data['ert_lines'] = []  # remove auto-copying of lines
        return [data]


    def action_duplicate_parent(self):
        for record in self:
            # 1️⃣ Create a clean new parent
            new_parent = record.with_context(skip_auto_copy=True).copy({
                'name': f"{record.name} Copy",
                'ert_lines': False,
            })

            # 2️⃣ Manually duplicate each ERT line and linked resistivity test
            for line in record.ert_lines:
                if line.soil_resistivity_id:
                    # Deep copy resistivity safely
                    new_res = line.soil_resistivity_id.with_context(skip_auto_copy=True).copy({
                        'ert_parent_id': new_parent.id,
                        'name': f"{line.soil_resistivity_id.name} Copy",
                    })

                    # Link new resistivity to new parent
                    self.env['ert.lines'].create({
                        'parent_id': new_parent.id,
                        'soil_resistivity_id': new_res.id,
                    })
                else:
                    # Empty line if no resistivity linked
                    self.env['ert.lines'].create({'parent_id': new_parent.id})

        return True

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
    borehole_lines = fields.One2many('soil.borehole.lines', 'parent_id', string="Borehole Lines", copy=False)
    rec_date = fields.Date("Date")


    # Optional computed field
    combined_images = fields.One2many(
        'soil.borehole.parent.image',
        'parent_id',
        string="Combined Graph Image",
        compute="_compute_combined_images",
        store=True,
        copy=False,
    )

    
    def copy_data(self, default=None):
        """Prevent automatic copying of One2many borehole lines"""
        data = super().copy_data(default)[0]
        data['borehole_lines'] = []  # Prevent auto-copy of child lines
        return [data]


    def action_duplicate_parent(self):
        """Duplicate the parent + all linked boreholes cleanly"""
        for record in self:
            # 1️⃣ Create clean new parent (no O2M auto copy)
            new_parent = record.with_context(skip_auto_copy=True).copy({
                'name': f"{record.name} Copy",
                'borehole_lines': False,
            })

            # 2️⃣ Manually duplicate each borehole + re-link it
            for line in record.borehole_lines:
                borehole = line.soil_borehole_id
                if not borehole:
                    continue

                # Copy borehole safely
                new_borehole = borehole.with_context(skip_auto_copy=True).copy({
                    'name': f"{borehole.name} Copy",
                })

                # Create linking line
                self.env['soil.borehole.lines'].create({
                    'parent_id': new_parent.id,
                    'soil_borehole_id': new_borehole.id,
                })

        return True

        # 4️⃣ Open the new parent form
        return True
        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': self._name,
        #     'res_id': new_parent.id,
        #     'view_mode': 'form',
        #     'target': 'current',
        # }


    

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
    
    def print_cross_hatching(self):
        report = self.env.ref('fst.cross_hatching_report_py3o')
        filename = f"{self.name or 'Cross Hatching'}"
        return report.report_action(self, config={'report_name': filename})
    
    def print_corrected_spt(self):
        report = self.env.ref('fst.corrected_spt_report_py3o')
        filename = f"{self.name or 'Corrected N value'}"
        return report.report_action(self, config={'report_name': filename})
    
    def print_grain_size(self):
        report = self.env.ref('fst.grain_size_report_py3o')
        filename = f"{self.name or 'Grain Size'}"
        return report.report_action(self, config={'report_name': filename})
    
    def print_direct_shear(self):
        report = self.env.ref('fst.direct_shear_report_py3o')
        filename = f"{self.name or 'Direct Shear'}"
        return report.report_action(self, config={'report_name': filename})
    
    
    # @api.depends('borehole_lines.soil_borehole_id.graph_image')
    # def _compute_combined_images(self):
    #     for record in self:
    #         # Clear existing records
    #         record.combined_images.unlink()

    #         images = []
    #         for line in record.borehole_lines:
    #             borehole = line.soil_borehole_id
    #             if borehole and borehole.graph_image:
    #                 try:
    #                     img_data = base64.b64decode(borehole.graph_image)
    #                     img = Image.open(io.BytesIO(img_data))
    #                     images.append(img)
    #                 except Exception as e:
    #                     _logger.warning(f"Skipping invalid image: {e}")

    #         if not images:
    #             continue

    #         grid_cols = 5
    #         grid_rows = 4
    #         thumb_w, thumb_h = 400, 400
    #         max_per_image = grid_cols * grid_rows

    #         # Split into groups of 20
    #         chunks = [images[i:i + max_per_image] for i in range(0, len(images), max_per_image)]

    #         ImageModel = self.env['soil.borehole.parent.image']

    #         for idx, group in enumerate(chunks, start=1):
    #             cols = min(grid_cols, len(group))
    #             rows = math.ceil(len(group) / grid_cols)
    #             combined_w = cols * thumb_w
    #             combined_h = rows * thumb_h
    #             combined_img = Image.new('RGB', (combined_w, combined_h), color=(255, 255, 255))

    #             # Paste thumbnails
    #             for i, img in enumerate(group):
    #                 img = img.copy()
                    
    #                 img.thumbnail((thumb_w, thumb_h))
    #                 enhancer = ImageEnhance.Sharpness(img)
    #                 img = enhancer.enhance(1.3)
                    
    #                 final_thumbnail = Image.new('RGB', (thumb_w, thumb_h), color=(255, 255, 255))
                    
    #                 x_offset = (thumb_w - img.width) // 2
    #                 y_offset = (thumb_h - img.height) // 2
                    
    #                 final_thumbnail.paste(img, (x_offset, y_offset))
                    
    #                 row, col = divmod(i, grid_cols)
    #                 x = col * thumb_w
    #                 y = row * thumb_h
                    
    #                 combined_img.paste(final_thumbnail, (x, y))
    #             # draw = ImageDraw.Draw(combined_img)
    #             # border_width = 4
    #             # draw.rectangle(
    #             #     [
    #             #         border_width - 1, 
    #             #         border_width - 1, 
    #             #         combined_img.width - (border_width), 
    #             #         combined_img.height - (border_width)
    #             #     ],
    #             #     outline="black",
    #             #     width=border_width
    #             # )

    #             # Save to binary
    #             buffer = io.BytesIO()
    #             combined_img.save(buffer, format="PNG")
    #             img_base64 = base64.b64encode(buffer.getvalue())

    #             ImageModel.create({
    #                 'parent_id': record.id,
    #                 'sequence': idx,
    #                 'image': img_base64,
    #             })

    @api.depends(
        'borehole_lines.soil_borehole_id.graph_image',
        'borehole_lines.soil_borehole_id.nvalue_ids.classification',
        'borehole_lines.soil_borehole_id.nvalue_ids.symbol')
    def _compute_combined_images(self):

        CLASSIFICATION_INFO = {
            'Poorly_Graded': ("Poorly graded sand", "SP"),
            'Well_Graded': ("Well graded sand", "SW"),
            'Well-Graded Gravel': ("Well-graded gravels", "GW"),
            'Poorly-Graded-Gravel': ("Poorly graded gravels", "GP"),
            'Silty-Gravel': ("Silty gravels", "GM"),
            'Clayey-Gravel': ("Clayey gravels", "GC"),
            'Silty-Sand': ("Silty sands", "SM"),
            'Clayey-Sand': ("Clayey sands", "SC"),
            'Inorganic-Silt-FS': ("Inorganic silts & very fine sands", "ML"),
            'Inorganic-Clays-LM': ("Inorganic clays (low - med plasticity)", "CL"),
            'Organic-Silt': ("Organic silts", "OL"),
            'Inorganic-Silt': ("Inorganic silts", "MH"),
            'Inorganic-Clay': ("Inorganic clays (high plasticity)", "CH"),
            'Organic-Clay': ("Organic clays", "OH"),
            'Peat': ("Peat", "PT"),
            'Hard-Rock': ("Hard Rock", "HR"),
            'Soft-Rock': ("Soft Rock", "SR"),
            'Inorganic-Silt-M': ("Inorganic silts of medium plasticity", "MI"),
            'Inorganic-Clay-M': ("Inorganic clays of medium plasticity", "CI"),
            'Silty-Clay-Border': ("Silty clay / clayey silt (CL-ML)", "CL-ML"),
        }

        ImageModel = self.env['soil.borehole.parent.image']

        # ---- Layout constants ----
        GRID_COLS = 5
        TARGET_WIDTH = 350
        MAX_HEIGHT = 1400
        ROW_GAP = 20
        COL_GAP = 20

        for record in self:
            record.combined_images.unlink()

            images = []
            used_classifications = set()

            # -----------------------------
            # 1. Collect borehole images + classifications
            # -----------------------------
            for line in record.borehole_lines:
                borehole = line.soil_borehole_id
                if not borehole:
                    continue

                for nv in borehole.nvalue_ids:
                    if nv.classification:
                        used_classifications.add(nv.classification)
                    elif nv.symbol:
                        for cls_code, (_, info_symbol) in CLASSIFICATION_INFO.items():
                            if info_symbol == nv.symbol:
                                used_classifications.add(cls_code)
                                break

                if borehole.graph_image:
                    try:
                        img_data = base64.b64decode(borehole.graph_image)
                        img = Image.open(io.BytesIO(img_data)).convert("RGB")
                        images.append(img)
                    except Exception as e:
                        _logger.warning(f"Skipping invalid image: {e}")

            if not images:
                continue

            # -----------------------------
            # 2. Prepare legend once
            # -----------------------------
            legend_items = []
            for cls_code in sorted(used_classifications):
                friendly, symbol = CLASSIFICATION_INFO.get(cls_code, (cls_code, None))
                if symbol:
                    facecolor, hatch = PATTERN_MAP_FOR_LEGEND.get(
                        symbol, PATTERN_MAP_FOR_LEGEND["DEFAULT"]
                    )
                    label = f"{symbol} - {friendly}"
                else:
                    facecolor, hatch = PATTERN_MAP_FOR_LEGEND["DEFAULT"]
                    label = friendly

                legend_items.append((facecolor, hatch, label))

            legend_img = make_legend_image(legend_items) if legend_items else None

            # -----------------------------
            # 3. Chunk images into pages
            # -----------------------------
            max_per_page = GRID_COLS * 4
            chunks = [
                images[i:i + max_per_page]
                for i in range(0, len(images), max_per_page)
            ]

            for page_idx, group in enumerate(chunks, start=1):

                # -----------------------------
                # 4. Resize images proportionally
                # -----------------------------
                resized = []
                for img in group:
                    orig_w, orig_h = img.size
                    scale = TARGET_WIDTH / orig_w
                    new_w = TARGET_WIDTH
                    new_h = int(orig_h * scale)

                    if new_h > MAX_HEIGHT:
                        new_h = MAX_HEIGHT
                        new_w = int(orig_w * (new_h / orig_h))

                    img = img.resize((new_w, new_h), Image.LANCZOS)
                    img = ImageEnhance.Sharpness(img).enhance(1.3)

                    resized.append(img)

                # -----------------------------
                # 5. Compute dynamic grid size
                # -----------------------------
                rows = math.ceil(len(resized) / GRID_COLS)

                row_heights = []
                for r in range(rows):
                    row_imgs = resized[r * GRID_COLS:(r + 1) * GRID_COLS]
                    row_heights.append(max(img.height for img in row_imgs))

                combined_w = GRID_COLS * TARGET_WIDTH + (GRID_COLS - 1) * COL_GAP
                combined_h = sum(row_heights) + (rows - 1) * ROW_GAP

                combined_img = Image.new("RGB", (combined_w, combined_h), (255, 255, 255))

                # -----------------------------
                # 6. Paste images
                # -----------------------------
                y_cursor = 0
                idx = 0

                for r, row_h in enumerate(row_heights):
                    x_cursor = 0
                    for c in range(GRID_COLS):
                        if idx >= len(resized):
                            break

                        img = resized[idx]
                        y_offset = y_cursor + (row_h - img.height) // 2
                        combined_img.paste(img, (x_cursor, y_offset))

                        x_cursor += TARGET_WIDTH + COL_GAP
                        idx += 1

                    y_cursor += row_h + ROW_GAP

                # -----------------------------
                # 7. Append legend (if any)
                # -----------------------------
                if legend_img:
                    lg_w, lg_h = legend_img.size
                    final_img = Image.new(
                        "RGB",
                        (combined_w, combined_h + lg_h + 20),
                        (255, 255, 255)
                    )
                    final_img.paste(combined_img, (0, 0))
                    final_img.paste(
                        legend_img,
                        (combined_w - lg_w - 10, combined_h + 10)
                    )
                else:
                    final_img = combined_img

                # -----------------------------
                # 8. Save
                # -----------------------------
                buffer = io.BytesIO()
                final_img.save(buffer, format="PNG")
                img_base64 = base64.b64encode(buffer.getvalue())

                ImageModel.create({
                    'parent_id': record.id,
                    'sequence': page_idx,
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

    parent_id = fields.Many2one('lerm.ert.parent',copy=False)
    soil_resistivity_id = fields.Many2one('ert.soil.resistivity',copy=False)
    
    
    def action_duplicate_ert(self):
        for record in self:
            if not record.soil_resistivity_id:
                raise UserError("No Borehole is linked to duplicate.")

            # 1. Read original name
            original_name = record.soil_resistivity_id.name

            # 2. Copy the borehole, giving the COPY a new name
            new_borehole = record.soil_resistivity_id.copy({
                'name': f"{original_name} Copy",
                'ert_parent_id': record.parent_id.id,
            })

        return True
    
    def action_delete_line(self):
        for rec in self:
            
            rec.unlink()

class SoilBoreholeLines(models.Model):
    _name = "soil.borehole.lines" 

    parent_id = fields.Many2one('soil.borehole.parent', copy=False)
    soil_borehole_id = fields.Many2one('soil.borehole', copy=False)
    
    def action_duplicate_borehole(self):
        for record in self:
            if not record.soil_borehole_id:
                raise UserError("No Borehole is linked to duplicate.")

            # 1. Read original name
            original_name = record.soil_borehole_id.name

            # 2. Copy the borehole, giving the COPY a new name
            new_borehole = record.soil_borehole_id.copy({
                'name': f"{original_name} Copy",
                'parent_id': record.parent_id.id,
            })

        return True

    def action_delete_line(self):
        for rec in self:
            rec.unlink()


class ERTDashboard(models.Model):
    _name = "lerm.ert.dashboard"
    _description = "ERT Dashboard"

    # def search(self, args, offset=0, limit=None, order=None, count=False):
    # # always show 1 record
    #     res = super(ERTDashboard, self).search(args, offset=offset, limit=limit, order=order, count=count)
    #     if not res and not count:
    #         return self.create({})
    #     return res
    