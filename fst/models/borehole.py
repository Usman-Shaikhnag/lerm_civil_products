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
    graph_image = fields.Binary("Borehole Graph")

    # Add these three One2many fields
    spt_n_value_ids = fields.One2many("spt.n.value", "borehole_id", string="Corrected SPT N-Values")
    direct_shear_ids = fields.One2many("direct.shear.test", "borehole_id", string="Direct Shear Tests")
    grain_size_ids = fields.One2many("grain.size.analysis", "borehole_id", string="Grain Size Analysis")

    corrected_spt_graph = fields.Binary("Correct SPT Graph")
    direct_shear_graph = fields.Binary("Direct Shear Graph", compute="_compute_direct_shear_graph", store=False)
    grain_size_graph = fields.Binary("Grain Size Graph")


    def generate_borehole_graph(self):
        for borehole in self:
            if not borehole.nvalue_ids:
                borehole.graph_image = False
                continue

            fig, ax = plt.subplots(figsize=(2, 4))
            lines = sorted(borehole.nvalue_ids, key=lambda l: l.top_depth)
            min_depth, max_depth = 0, 6.0

            # Draw log rectangle outline with high zorder to be on top
            ax.plot([0, 0], [min_depth, max_depth], color="black", zorder=3)
            ax.plot([1, 1], [min_depth, max_depth], color="black", zorder=3)
            ax.plot([0, 1], [min_depth, min_depth], color="black", zorder=3)
            ax.plot([0, 1], [max_depth, max_depth], color="black", zorder=3)

            # Map classification to hatches
            hatch_map = {
                "poorly_graded": ".....",
                "well_graded": "\\\\\\\\\\",
            }
            
            # Draw a placeholder segment from 0.0 if the first data point starts later
            if lines and lines[0].top_depth > min_depth:
                rect = patches.Rectangle(
                    (0, min_depth),
                    1.0,
                    lines[0].top_depth - min_depth,
                    edgecolor="none",
                    facecolor="white",
                    linewidth=0,
                    zorder=2
                )
                ax.add_patch(rect)
                # Draw the top and bottom black lines that extend slightly
                ax.plot([-0.05, 1.05], [min_depth, min_depth], color="black", linewidth=0.5, zorder=3)
                ax.plot([-0.05, 1.05], [lines[0].top_depth, lines[0].top_depth], color="black", linewidth=0.5, zorder=3)
            
            # Soil segments and patterns
            for line in lines:
                hatch_style = hatch_map.get(line.classification, None)
                
                rect = patches.Rectangle(
                    (0, line.top_depth),
                    1.0,
                    line.bottom_depth - line.top_depth,
                    edgecolor="darkgoldenrod",  # Change this to "none" to remove full border
                    facecolor="white" if hatch_style else "lightgrey",
                    hatch=hatch_style,
                    linewidth=0,
                    zorder=2
                )
                ax.add_patch(rect)
                
                # Draw black horizontal lines at the top and bottom of each segment
                # The lines extend from -0.05 to 1.05 on the x-axis
                ax.plot([-0.05, 1.05], [line.top_depth, line.top_depth], color="black", linewidth=0.5, zorder=3)
                ax.plot([-0.05, 1.05], [line.bottom_depth, line.bottom_depth], color="black", linewidth=0.5, zorder=3)

            for line in lines:
                # Place N-Value labels at the top depth
                if line.n_value:
                    ax.text(-0.15, line.top_depth, str(line.n_value), ha="right", va="center",
                            fontsize=9, color="brown", fontweight="bold")
                
                # Place UDS label at the top depth, checking for "UDS" as a substring
                if line.sample_type and "UDS" in line.sample_type.strip().upper():
                    ax.text(-0.15, line.top_depth, "UDS", ha="right", va="center",
                            fontsize=9, color="black")

            # Depth labels on right
            for d in np.arange(min_depth, max_depth + 0.5, 0.5):
                ax.text(1.05, d, f"{d:.1f}m", fontsize=8, ha="left", va="center")

            # N-Value label + straight arrow
            ax.text(-0.20, -0.4, "N-Value", color="blue", fontsize=10,
                    ha="center", fontweight="bold")
            ax.annotate("",
                        xy=(-0.20, 0.1), xytext=(-0.20, -0.35),
                        arrowprops=dict(facecolor='red', arrowstyle="->"))

            # Borehole name top center
            ax.text(0.5, -0.45, borehole.name or "", color="red", fontsize=12,
                    ha="center", va="bottom", fontweight="bold")

            ax.set_xlim(-0.3, 1.3)
            ax.set_ylim(max_depth, -0.5)
            ax.axis("off")

            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight", dpi=180)
            plt.close(fig)
            borehole.graph_image = base64.b64encode(buf.getvalue())


    def generate_corrected_spt_graph(self):
        pass

    # @api.depends('direct_shear_ids.shear_stress', 'direct_shear_ids.applied_normal_stress')
    def _compute_direct_shear_graph(self):
        for borehole in self:
            if not borehole.direct_shear_ids:
                borehole.direct_shear_graph = False
                continue

            # Data extraction
            # normal_stress = [l.applied_normal_stress for l in borehole.direct_shear_ids]
            # shear_stress = [l.shear_stress for l in borehole.direct_shear_ids]
            
            # # Matplotlib code for Direct Shear Graph (as previously provided)
            # # Make sure to handle potential empty lists if there is no data
            
            # # Save to buffer and encode
            # buf = io.BytesIO()
            # plt.savefig(buf, format="png", bbox_inches="tight", dpi=180)
            # plt.close(fig)
            # borehole.direct_shear_graph = base64.b64encode(buf.getvalue())

    # @api.depends('grain_size_ids.percent_passing') # You'll need to define this field
    def _compute_grain_size_graph(self):
        for borehole in self:
            if not borehole.grain_size_ids:
                borehole.grain_size_graph = False
                continue

            # # Data extraction
            # # This is more complex, so you'll need to handle the data format from your model...
            
            # # Matplotlib code for Grain Size Analysis Graph (as previously provided)...

            # # Save to buffer and encode
            # buf = io.BytesIO()
            # plt.savefig(buf, format="png", bbox_inches="tight", dpi=180)
            # plt.close(fig)
            # borehole.grain_size_graph = base64.b64encode(buf.getvalue())

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
    sample_type = fields.Char("Sample Type")
    symbol = fields.Char("Symbol")                
    classification = fields.Selection([
        ('poorly_graded','Poorly Graded Sand'),
        ('well_graded','Well Graded Sand')
    ])

    top_depth = fields.Float("Top Depth (m)")
    bottom_depth = fields.Float("Bottom Depth (m)")
    n15 = fields.Integer("N @ 15 cm")
    n30 = fields.Integer("N @ 30 cm")
    n45 = fields.Integer("N @ 45 cm")
    # This field is now computed automatically
    n_value = fields.Integer("Total N Value", compute="_compute_n_value", store=True)

    @api.depends('n30', 'n45')
    def _compute_n_value(self):
        for record in self:
            record.n_value = record.n30 + record.n45



class CorrectedSptNValue(models.Model):
    _name = 'spt.n.value'
    _description = 'Corrected SPT (N) Value'

    borehole_id = fields.Many2one('soil.borehole', string='Borehole', ondelete='cascade')
    sr_no = fields.Integer(string="Sr.No", readonly=True, copy=False, default=1)
    depth = fields.Float(string='Depth (m)')
    bulk_den = fields.Float(string='Bulk Density (T/m2)')
    overburden_pressure = fields.Float(string='Overburden Pressure (T/m2)',compute="_compute_overburden_pressure")
    effective_overburden_pressure = fields.Float(string='Effective Overburden Pressure (T/m2)')
    observed_n_value = fields.Integer(string='Observed SPT N Value')
    corrected_n_value = fields.Float(string='Corrected SPT (N\') Value')
    
    
    @api.model
    def create(self, vals):
        if vals.get('borehole_id'):
            existing_records = self.search([('borehole_id', '=', vals['borehole_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1
        return super().create(vals)  # ✅ must return



    @api.depends('depth', 'bulk_den', 'borehole_id')
    def _compute_overburden_pressure(self):
        for record in self:
            # default
            record.overburden_pressure = 0.0  

            # skip if no borehole or invalid values
            if not record.borehole_id or record.depth is None or record.bulk_den is None:
                continue

            # fetch all records of this borehole sorted by depth
            borehole_records = self.search(
                [('borehole_id', '=', record.borehole_id.id)],
                order="depth asc"
            )

            cumulative_pressure = 0.0
            prev_depth = 0.0

            for rec in borehole_records:
                if rec.id == record.id:
                    if prev_depth == 0:  # first record
                        record.overburden_pressure = rec.depth * rec.bulk_den
                    else:  # subsequent record
                        record.overburden_pressure = cumulative_pressure + ((rec.depth - prev_depth) * rec.bulk_den)
                    break
                else:
                    if prev_depth == 0:
                        cumulative_pressure = rec.depth * rec.bulk_den
                    else:
                        cumulative_pressure += (rec.depth - prev_depth) * rec.bulk_den
                    prev_depth = rec.depth



class DirectShearTest(models.Model):
    _name = 'direct.shear.test'
    _description = 'Direct Shear Test'

    borehole_id = fields.Many2one('soil.borehole', string='Borehole', ondelete='cascade')
    applied_normal_stress = fields.Float(string='Applied Normal Stress (Kg/cm²)')
    no_of_divisions = fields.Integer(string='No. of Divisions of Proving ring dial Gauge')
    shear_load = fields.Float(string='Shear Load (kg)')
    corrected_area = fields.Float(string='Corrected Area (cm2)')
    shear_stress = fields.Float(string='Shear Stress (Kg/cm²)')

class GrainSizeAnalysis(models.Model):
    _name = 'grain.size.analysis'
    _description = 'Grain Size Analysis'

    borehole_id = fields.Many2one('soil.borehole', string='Borehole', ondelete='cascade')
    depth = fields.Float(string='Depth (m)')
    sample_type = fields.Char(string='Sample Type')
    gravel_percentage = fields.Float(string='Gravel (%)')
    coarse_sand_percentage = fields.Float(string='Coarse Sand (%)')
    medium_sand_percentage = fields.Float(string='Medium Sand (%)')
    fine_sand_percentage = fields.Float(string='Fine Sand (%)')
    silt_percentage = fields.Float(string='Silt (%)')
    clay_percentage = fields.Float(string='Clay (%)')
    total_percentage = fields.Float(string='Total (%)')