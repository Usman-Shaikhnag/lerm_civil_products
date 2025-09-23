from odoo import models, fields, api
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
from matplotlib.patches import RegularPolygon
from matplotlib.spines import Spine
from matplotlib.path import Path
from matplotlib.transforms import Affine2D
import matplotlib
import numpy as np
import io, base64
from math import sqrt, pi
import math

class ERTBorehole(models.Model):
    _name = "soil.borehole"

    name = fields.Char(string="Name", required=True, copy=False, readonly=True, default='New')
    parent_id = fields.Many2one('soil.borehole.parent')

    line_ids = fields.One2many("soil.borehole.line", "borehole_id", string="SBC Lines")
    nvalue_ids = fields.One2many("soil.borehole.nvalue", "borehole_id", string="N-Vlaues")
    graph_image = fields.Binary("Borehole Graph", compute="_compute_graph", store=False)

    @api.depends('nvalue_ids.top_depth','nvalue_ids.bottom_depth','nvalue_ids.n_value','nvalue_ids.soil_pattern','nvalue_ids.classification')
    def _compute_graph(self):
        for borehole in self:
            if not borehole.nvalue_ids:
                borehole.graph_image = False
                continue

            # Sort lines by top_depth
            lines = sorted(borehole.nvalue_ids, key=lambda r: r.top_depth or 0)

            # Determine max depth for plotting
            max_depth = 0.0
            for ln in lines:
                if ln.bottom_depth and ln.bottom_depth > max_depth:
                    max_depth = ln.bottom_depth
            if max_depth == 0.0:
                max_depth = 6.0

            # Create figure (depth vertical)
            fig, ax = plt.subplots(figsize=(2.5, 7))   # tweak size as needed

            # Draw each layer as a rectangle (with hatch if requested)
            for ln in lines:
                top = ln.top_depth or 0.0
                bot = ln.bottom_depth or top
                height = max(0.001, bot - top)

                hatch_style = {"dots": "..", "hatch": "//", "solid": None}.get(ln.soil_pattern, None)
                rect = patches.Rectangle((0.0, top),    # x, y
                                        1.0,           # width
                                        height,        # height
                                        facecolor='none' if hatch_style else 'white',
                                        hatch=hatch_style,
                                        edgecolor='brown',
                                        linewidth=0.7)
                ax.add_patch(rect)

                # classification text inside block (centered)
                if ln.classification:
                    ax.text(0.5, top + height/2.0, str(ln.classification),
                            va='center', ha='center', fontsize=6, wrap=True)

                # N-value on left at middle of layer
                if ln.n_value is not None and ln.n_value != '':
                    ax.text(-0.05, top + height/2.0, str(ln.n_value),
                            va='center', ha='right', fontsize=8)

                # sample type at left small
                if ln.sample_type:
                    ax.text(-0.4, top + height/2.0, str(ln.sample_type),
                            va='center', ha='right', fontsize=7, color='gray')

            # Depth labels to the right
            step = 0.5 if max_depth <= 6 else 1
            d = 0.0
            while d <= max_depth + 0.0001:
                ax.text(1.15, d, f"{d:.2f}m" if step<1 else f"{int(d)}.0m",
                        va='center', ha='left', fontsize=7)
                d += step

            # Invert Y so depth increases downward
            ax.set_ylim(max_depth, 0)
            ax.set_xlim(-0.6, 1.4)

            ax.axis('off')
            ax.set_title(borehole.name or '', color='red', fontsize=10)

            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
            plt.close(fig)
            buf.seek(0)
            borehole.graph_image = base64.b64encode(buf.getvalue()).decode('ascii')


    

    @api.model
    def create(self, vals):
        if vals.get("name", "New") == "New":
            vals["name"] = self.env["ir.sequence"].next_by_code("soil.borehole.seq") or "New"
            
        record = super().create(vals)
        if record.parent_id:
            self.env['soil.borehole.lines'].sudo().create({
                'parent_id': record.parent_id.id,
                'soil_borehole_id': record.id
            })
        return record
class SoilBoreholeParent(models.Model):
    _name = "soil.borehole.line.parent"
    _description = "Borehole Parent Details"

    name = fields.Char("Project / Site Name", required=True)
    location = fields.Char("Location")
    client = fields.Char("Client")
    boring_type = fields.Char("Type of boring")
    machine = fields.Char("Drilling Machine")
    bore_diameter = fields.Float("Bore Diameter (mm)")
    date_started = fields.Date("Date Started")
    date_completed = fields.Date("Date Completed")

    borehole_ids = fields.One2many("soil.borehole", "parent_id", string="Boreholes")

    
class SoilBoreholeLine(models.Model):
    _name = "soil.borehole.line"
    _description = "Borehole Line Data"

    borehole_id = fields.Many2one("soil.borehole", ondelete="cascade")
    depth = fields.Float("Depth (m)")
    footing_size = fields.Char("Size of footing (m)")
    shear_criteria = fields.Float("Shear criteria (T/m²)")
    settlement_criteria = fields.Float("Settlement criteria (T/m²)")
    recommended_sbc = fields.Float("Recommended SBC (T/m²)")


class SoilBoreholeNValue(models.Model):
    _name = "soil.borehole.nvalue"
    _description = "Borehole N-Values"

    borehole_id = fields.Many2one("soil.borehole", ondelete="cascade")
    sample_type = fields.Char("Sample Type")       # e.g., SPT-1, UDS-1, DRILLING
    symbol = fields.Char("Symbol")                 # e.g., SP, CL, etc.
    classification = fields.Text("Soil Classification / Description")
    remarks = fields.Text("Remarks")

    top_depth = fields.Float("Top Depth (m)")
    bottom_depth = fields.Float("Bottom Depth (m)")
    n15 = fields.Integer("N @ 15 cm")
    n30 = fields.Integer("N @ 30 cm")
    n45 = fields.Integer("N @ 45 cm")
    n_value = fields.Integer("Total N Value")
    core_recovery = fields.Float("Core Recovery (%)")
    rqd = fields.Float("RQD (%)")

    soil_pattern = fields.Selection([
        ("dots", "Dots"),
        ("hatch", "Hatch"),
        ("solid", "Solid"),
    ], string="Soil Pattern")
