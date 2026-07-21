from odoo import api, fields, models
from PIL import Image, ImageEnhance
import io, base64, math, logging
from matplotlib import patches as mpatches
import matplotlib.pyplot as plt

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
    "HR": ("#666666", "xx"),
    "SR": ("#B0A080", "\\"),
    "MI": ("#B0C4DE", "|||"),
    "CI": ("#ADD8E6", "----"),
    "CL-ML": ("#ADD8E6", "----"),
    "Inorganic-Clays": ("#5D8AA8", "x"),
    "Organic-Clays": ("#4B371C", "/"),
    "Peat": ("#556B2F", "v"),
    "DEFAULT": ("white", None),
}


def make_legend_image(legend_items):
    if not legend_items:
        return None
    n = len(legend_items)
    row_h = 0.32
    fig_w = 3.6
    fig_h = max(1.2, row_h * n)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, n)
    for i, (facecolor, hatch, label) in enumerate(legend_items):
        y = n - 1 - i
        rect = mpatches.Rectangle(
            (0.04, y + 0.28), 0.10, 0.44,
            facecolor=facecolor, edgecolor='black',
            hatch=hatch or '', linewidth=0.8
        )
        ax.add_patch(rect)
        ax.text(0.27, y + 0.5, label, va='center', ha='left', fontsize=8.5)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert('RGB')


class SoilBoreholeParent(models.Model):
    _name = "soil.borehole.parent"
    _rec_name = "name"

    name = fields.Char("Project Name")
    borehole_lines = fields.One2many('soil.borehole.lines', 'parent_id', string="Borehole Lines", copy=False)
    rec_date = fields.Date("Date")

    combined_images = fields.One2many(
        'soil.borehole.parent.image',
        'parent_id',
        string="Combined Graph Image",
        compute="_compute_combined_images",
        store=True,
        copy=False,
    )

    def copy_data(self, default=None):
        data = super().copy_data(default)[0]
        data['borehole_lines'] = []
        return [data]

    def action_duplicate_parent(self):
        for record in self:
            new_parent = record.with_context(skip_auto_copy=True).copy({
                'name': f"{record.name} Copy",
                'borehole_lines': False,
            })
            for line in record.borehole_lines:
                borehole = line.soil_borehole_id
                if not borehole:
                    continue
                new_borehole = borehole.with_context(skip_auto_copy=True).copy({
                    'name': f"{borehole.name} Copy",
                })
                self.env['soil.borehole.lines'].create({
                    'parent_id': new_parent.id,
                    'soil_borehole_id': new_borehole.id,
                })
        return True

    def create_ert(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'soil.borehole',
            'target': 'current',
            'context': {
                'default_parent_id': self.id
            }
        }

    def print_report(self):
        report = self.env.ref('fst.borehole_report_py3o')
        return report.report_action(self, config={'report_name': self.name or 'ERT'})

    def print_cross_hatching(self):
        report = self.env.ref('fst.cross_hatching_report_py3o')
        return report.report_action(self, config={'report_name': self.name or 'Cross Hatching'})

    def print_corrected_spt(self):
        report = self.env.ref('fst.corrected_spt_report_py3o')
        return report.report_action(self, config={'report_name': self.name or 'Corrected N value'})

    def print_grain_size(self):
        report = self.env.ref('fst.grain_size_report_py3o')
        return report.report_action(self, config={'report_name': self.name or 'Grain Size'})

    def print_direct_shear(self):
        report = self.env.ref('fst.direct_shear_report_py3o')
        return report.report_action(self, config={'report_name': self.name or 'Direct Shear'})

    @api.depends('borehole_lines')
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
        GRID_COLS = 5
        TARGET_WIDTH = 350
        MAX_HEIGHT = 1400
        ROW_GAP = 20
        COL_GAP = 20
        for record in self:
            record.combined_images.unlink()
            images = []
            used_classifications = set()
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
            max_per_page = GRID_COLS * 4
            chunks = [images[i:i + max_per_page] for i in range(0, len(images), max_per_page)]
            for page_idx, group in enumerate(chunks, start=1):
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
                rows = math.ceil(len(resized) / GRID_COLS)
                row_heights = []
                for r in range(rows):
                    row_imgs = resized[r * GRID_COLS:(r + 1) * GRID_COLS]
                    row_heights.append(max(img.height for img in row_imgs))
                combined_w = GRID_COLS * TARGET_WIDTH + (GRID_COLS - 1) * COL_GAP
                combined_h = sum(row_heights) + (rows - 1) * ROW_GAP
                combined_img = Image.new("RGB", (combined_w, combined_h), (255, 255, 255))
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
                if legend_img:
                    lg_w, lg_h = legend_img.size
                    final_img = Image.new("RGB", (combined_w, combined_h + lg_h + 20), (255, 255, 255))
                    final_img.paste(combined_img, (0, 0))
                    final_img.paste(legend_img, (combined_w - lg_w - 10, combined_h + 10))
                else:
                    final_img = combined_img
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


class SoilBoreholeLines(models.Model):
    _name = "soil.borehole.lines"

    parent_id = fields.Many2one('soil.borehole.parent', copy=False)
    soil_borehole_id = fields.Many2one('soil.borehole', copy=False)

    def action_duplicate_borehole(self):
        for record in self:
            if not record.soil_borehole_id:
                raise models.ValidationError("No Borehole is linked to duplicate.")
            original_name = record.soil_borehole_id.name
            record.soil_borehole_id.copy({
                'name': f"{original_name} Copy",
                'parent_id': record.parent_id.id,
            })
        return True

    def action_delete_line(self):
        for rec in self:
            rec.unlink()
