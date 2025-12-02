from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import zipfile
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import io, base64, math, logging

_logger = logging.getLogger(__name__)

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
    
        
    # @api.model
    # def get_react_base_url(self):
    #     """Detect React app URL dynamically."""
    #     # Check system parameter if set, fallback to localhost:3000
    #     param = self.env['ir.config_parameter'].sudo().get_param('react_app_url', 'http://localhost:3000')
    #     return param

    # def action_open_react(self):
    #     base_url = self.get_react_base_url()
    #     for rec in self:
    #         url = f"{base_url}/borehole/{rec.id}"
    #         return {
    #             'type': 'ir.actions.act_url',
    #             'target': 'new',
    #             'url': url,
    #         }
        

    
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

    @api.depends('borehole_lines.soil_borehole_id.graph_image',
                'borehole_lines.soil_borehole_id.nvalue_ids.classification',
                'borehole_lines.soil_borehole_id.nvalue_ids.symbol')
    def _compute_combined_images(self):
        
        # Same soil color scheme as in generate_borehole_graph (pattern_map)
        SYMBOL_COLOR_MAP = {
            "GW": "#B8B8A0",
            "GP": "#B8B8A0",
            "GM": "#A0A080",
            "GC": "#909070",
            "SW": "#FFFF99",
            "SP": "#FFFF66",
            "SM": "#E0E0A0",
            "SC": "#DDAA88",
            "ML": "#D3D3D3",
            "CL": "#ADD8E6",
            "OL": "#7B68EE",
            "MH": "#B0C4DE",
            "CH": "#5D8AA8",
            "OH": "#4B371C",
            "PT": "#556B2F",
        }

        # Classification code -> human-friendly name + symbol for legend
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
            'Inorganic-Clays-LM': ("Inorganic clays (low–med plasticity)", "CL"),
            'Organic-Silt': ("Organic silts", "OL"),
            'Inorganic-Silt': ("Inorganic silts", "MH"),
            'Inorganic-Clay': ("Inorganic clays (high plasticity)", "CH"),
            'Organic-Clay': ("Organic clays", "OH"),
            'Peat': ("Peat", "PT"),
        }
        ImageModel = self.env['soil.borehole.parent.image']

        for record in self:
            # Clear existing combined images for this parent
            record.combined_images.unlink()

            # --- 1. Collect all borehole thumbnails and the classifications used ---
            images = []
            used_classifications = set()

            for line in record.borehole_lines:
                borehole = line.soil_borehole_id
                if not borehole:
                    continue

                # Collect classification info from N-values for legend
                for nv in borehole.nvalue_ids:
                    if nv.classification:
                        used_classifications.add(nv.classification)
                    elif nv.symbol:
                        # Fallback: map symbol -> classification like your SYMBOL_TO_CLASSIFICATION logic
                        # Adjust if your actual mapping keys differ.
                        symbol = nv.symbol
                        # try to infer classification name from your CLASSIFICATION_INFO
                        for cls_code, (_, info_symbol) in CLASSIFICATION_INFO.items():
                            if info_symbol == symbol:
                                used_classifications.add(cls_code)
                                break

                # Collect graph image thumbnails
                if borehole.graph_image:
                    try:
                        img_data = base64.b64decode(borehole.graph_image)
                        img = Image.open(io.BytesIO(img_data))
                        images.append(img)
                    except Exception as e:
                        _logger.warning(f"Skipping invalid image: {e}")

            if not images:
                continue

            # --- 2. Build pages of thumbnails (same as your original logic) ---
            grid_cols = 5
            grid_rows = 4
            thumb_w, thumb_h = 400, 400
            max_per_image = grid_cols * grid_rows

            chunks = [images[i:i + max_per_image] for i in range(0, len(images), max_per_image)]

            # Prepare legend data once per parent (one legend for all combined boreholes)
            legend_items = []
            for cls_code in sorted(used_classifications):  # sort for stable ordering
                friendly, symbol = CLASSIFICATION_INFO.get(cls_code, (cls_code, None))
                color = SYMBOL_COLOR_MAP.get(symbol, "white")
                # label text: e.g. "CL – Inorganic clays (low–med plasticity)"
                if symbol:
                    label = f"{symbol} – {friendly}"
                else:
                    label = friendly
                legend_items.append((color, label))

            # If there is no classification data, we will simply not draw a legend.
            for idx, group in enumerate(chunks, start=1):
                cols = min(grid_cols, len(group))
                rows = math.ceil(len(group) / grid_cols)
                combined_w = cols * thumb_w
                combined_h = rows * thumb_h

                # --- 3. First, compose the main grid image ---
                combined_img = Image.new('RGB', (combined_w, combined_h), color=(255, 255, 255))

                for i, img in enumerate(group):
                    img = img.copy()
                    img.thumbnail((thumb_w, thumb_h))
                    enhancer = ImageEnhance.Sharpness(img)
                    img = enhancer.enhance(1.3)

                    final_thumbnail = Image.new('RGB', (thumb_w, thumb_h), color=(255, 255, 255))

                    x_offset = (thumb_w - img.width) // 2
                    y_offset = (thumb_h - img.height) // 2
                    final_thumbnail.paste(img, (x_offset, y_offset))

                    row, col = divmod(i, grid_cols)
                    x = col * thumb_w
                    y = row * thumb_h

                    combined_img.paste(final_thumbnail, (x, y))

                # --- 4. Add legend at the bottom-right (only used classifications) ---
                if legend_items:
                    # Estimate legend height: one row per item
                    line_height = 22
                    top_padding = 8
                    bottom_padding = 8
                    legend_height = top_padding + bottom_padding + line_height * len(legend_items)

                    # Extend canvas downward to fit legend
                    final_h = combined_h + legend_height
                    final_img = Image.new('RGB', (combined_w, final_h), color=(255, 255, 255))
                    final_img.paste(combined_img, (0, 0))

                    draw = ImageDraw.Draw(final_img)
                    font = ImageFont.load_default()

                    margin = 10
                    swatch_size = 16
                    spacing = 6

                    # Legend box area (anchored to bottom-right)
                    box_width = min(420, combined_w - 2 * margin)  # cap width
                    box_left = combined_w - box_width - margin
                    box_top = combined_h + (legend_height - (line_height * len(legend_items) + top_padding + bottom_padding)) // 2
                    box_right = combined_w - margin
                    box_bottom = final_h - margin

                    # Background & border
                    draw.rectangle(
                        [box_left, box_top, box_right, box_bottom],
                        fill="white",
                        outline="black",
                        width=1,
                    )

                    # Draw each legend line
                    y = box_top + top_padding
                    x_swatch = box_left + 8
                    x_text = x_swatch + swatch_size + spacing

                    for color, label in legend_items:
                        # Color swatch
                        draw.rectangle(
                            [x_swatch, y, x_swatch + swatch_size, y + swatch_size],
                            fill=color,
                            outline="black",
                            width=1,
                        )
                        # Text
                        draw.text((x_text, y), label, fill="black", font=font)
                        y += line_height

                else:
                    # No legend → final image is just the combined grid
                    final_img = combined_img

                # --- 5. Save to Binary and create record ---
                buffer = io.BytesIO()
                final_img.save(buffer, format="PNG")
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

    def search(self, args, offset=0, limit=None, order=None, count=False):
    # always show 1 record
        res = super(ERTDashboard, self).search(args, offset=offset, limit=limit, order=order, count=count)
        if not res and not count:
            return self.create({})
        return res
    