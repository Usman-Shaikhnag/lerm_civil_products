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
from scipy import stats
import numpy as np
import io, base64
from math import sqrt, pi
import math

class ERTBorehole(models.Model):
    _name = "soil.borehole"

    name = fields.Char(string="Name", required=True, copy=False, readonly=True, default='New')
    parent_id = fields.Many2one('soil.borehole.parent')

    # line_ids = fields.One2many("soil.borehole.line", "borehole_id", string="SBC Lines")
    nvalue_ids = fields.One2many("soil.borehole.nvalue", "borehole_id", string="N-Vlaues")
    graph_image = fields.Binary("Borehole Graph")

    # Add these three One2many fields
    spt_n_value_ids = fields.One2many("spt.n.value", "borehole_id", string="Corrected SPT N-Values")
    corrected_spt_graph = fields.Binary("Correct SPT Graph")
    
    direct_shear_ids = fields.One2many("direct.shear.test", "borehole_id", string="Direct Shear Tests")
    direct_shear_graph = fields.Binary("Direct Shear Graph", compute="_compute_shear_parameters", store=False)
    cohesion = fields.Float(
        string='Cohesion (C) (Kg/cm²)', 
        compute='_compute_shear_parameters', 
        store=True,
        digits=(16, 3)
    )
    angle_of_internal_friction = fields.Float(
        string='Angle of Internal Friction (\u03C6) (\u00b0)', 
        compute='_compute_shear_parameters', 
        store=True,
        digits=(16, 2)
    )

    grain_size_ids = fields.One2many("grain.size.analysis", "borehole_id", string="Grain Size Analysis")
    grain_size_graph = fields.Binary("Grain Size Graph")


    # ... other fields and methods ...

    def generate_corrected_spt_graph(self):
        self.ensure_one()

        if not self.spt_n_value_ids:
            self.corrected_spt_graph = False
            return

        sorted_spt_values = sorted(self.spt_n_value_ids, key=lambda r: r.depth)

        depths = [r.depth for r in sorted_spt_values]
        observed_n_values = [r.observed_n_value for r in sorted_spt_values]
        corrected_n_values = [r.corrected_n_value for r in sorted_spt_values]

        # Create the plot
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(10, 8))

        # Plot the data
        ax.plot(observed_n_values, depths, marker='D', linestyle='-', color='b', label='Observed N value')
        ax.plot(corrected_n_values, depths, marker='s', linestyle='-', color='r', label='Corrected N value')

        # Format the plot
        ax.set_xlabel('SPT BLOWS PER 30 CM PENETRATION')
        ax.set_ylabel('DEPTH BELOW GROUND LEVEL m.')
        ax.set_title('SPT BLOWS PER 30 CM PENETRATION', y=1.05)
        ax.invert_yaxis()
        ax.set_xlim(left=0)
        ax.set_xticks(range(0, 180, 10))
        ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.15), fancybox=True, shadow=True, ncol=2)
        plt.tight_layout(rect=[0, 0.1, 1, 1])

        # Save the plot to a BytesIO object
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close(fig)

        # Store the graph as base64-encoded binary data
        self.corrected_spt_graph = base64.b64encode(buffer.getvalue())
        buffer.close()

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




    @api.depends('direct_shear_ids.applied_normal_stress', 'direct_shear_ids.shear_stress')
    def _compute_shear_parameters(self):
        for borehole in self:
            # 1. Collect Data Points
            if not borehole.direct_shear_ids or len(borehole.direct_shear_ids) < 2:
                # Need at least 2 points to draw a line, 3 is standard for reliability
                borehole.cohesion = 0.0
                borehole.angle_of_internal_friction = 0.0
                borehole.direct_shear_graph = False
                continue

            # Assuming all direct_shear_ids records belong to a single failure envelope
            normal_stresses = [test.applied_normal_stress for test in borehole.direct_shear_ids]
            shear_stresses = [test.shear_stress for test in borehole.direct_shear_ids]
            
            x = np.array(normal_stresses)
            y = np.array(shear_stresses)

            # 2. Perform Linear Regression (y = m*x + c)
            # slope (m) = tan(phi), intercept (c) = cohesion
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # 3. Calculate Cohesion (c) and Angle of Internal Friction (phi)
            cohesion = intercept
            angle_phi_radians = math.atan(slope)
            angle_phi_degrees = round(math.degrees(angle_phi_radians),2)
            
            # Store the calculated values
            borehole.cohesion = cohesion
            borehole.angle_of_internal_friction = angle_phi_degrees

            # 4. Generate the Plot
            plt.style.use('seaborn-v0_8-whitegrid')
            fig, ax = plt.subplots(figsize=(8, 6))

            # Plot the raw data points
            ax.scatter(x, y, color='red', marker='s', label='Observed Test Points')

            # Plot the best-fit line (Failure Envelope)
            # Extend the line slightly beyond the last point
            x_max = np.max(x)
            x_fit = np.linspace(0, x_max + (x_max * 0.1), 10) 
            y_fit = slope * x_fit + intercept
            
            ax.plot(x_fit, y_fit, color='blue', linestyle='-', 
                    label=f'Failure Envelope: C={cohesion:.2f} $\\frac{{kg}}{{cm^2}}$, $\\phi$={angle_phi_degrees:.2f}\u00b0')

            # Format the plot
            ax.set_title(f'Direct Shear Test Results (BH-{borehole.name})', pad=20)
            ax.set_xlabel('Normal Stress ($\u03C3$) [kg/cm\u00b2]')
            ax.set_ylabel('Shear Stress ($\u03C4$) [kg/cm\u00b2]')
            
            # Set the origin to (0,0)
            ax.set_xlim(left=0) 
            ax.set_ylim(bottom=0)
            
            ax.legend()
            ax.grid(True)
            plt.tight_layout()

            # 5. Save and Store the Graph
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            plt.close(fig)

            borehole.direct_shear_graph = base64.b64encode(buffer.getvalue())
            buffer.close()

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

    
# class SoilBoreholeLine(models.Model):
#     _name = "soil.borehole.line"
#     _description = "Borehole Line Data"

#     borehole_id = fields.Many2one("soil.borehole", ondelete="cascade")
#     depth = fields.Float("Depth (m)")
#     footing_size = fields.Char("Size of footing (m)")
#     shear_criteria = fields.Float("Shear criteria (T/m²)")
#     settlement_criteria = fields.Float("Settlement criteria (T/m²)")
#     recommended_sbc = fields.Float("Recommended SBC (T/m²)")


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
    overburden_pressure = fields.Float(string='Overburden Pressure (T/m2)',compute="_compute_overburden_pressure", digits=(16, 3))
    pore_water_pressure = fields.Float(string="Pore Water Pressure from layer",compute="_compute_pore_water_pressure", digits=(16, 3))
    total_pore_water_pressure = fields.Float(string="total pore water pressure",compute="_compute_total_pore_water_pressure", digits=(16, 3))
    effective_overburden_pressure = fields.Float(string='Effective Overburden Pressure (T/m2)', compute="_compute_effective_overburden_pressure", digits=(16, 3))
    effective_overburden_pressure_kg = fields.Float(string='Effective Overburden Pressure (kg/cm2)', compute="_compute_effective_overburden_pressure_kg", digits=(16, 3))
    overburden_correction_factor = fields.Float(string="OVERBURDEN CORRECTION FACTOR",compute="_compute_overburden_correction_factor", digits=(16, 3))
    observed_n_value = fields.Integer(string='Observed SPT N Value',compute="_compute_observed_n_value")
    corrected_n_value = fields.Integer(string='Corrected SPT (N\') Value',compute="_compute_corrected_n_value")
    
    @api.model
    def create(self, vals):
        if vals.get('borehole_id'):
            existing_records = self.search([('borehole_id', '=', vals['borehole_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1
        return super().create(vals)  # ✅ must return

    @api.depends('depth', 'borehole_id')
    def _compute_pore_water_pressure(self):
        for record in self:
            record.pore_water_pressure = 0.0  # default

            if not record.borehole_id or record.depth is None:
                continue

            # fetch all records of this borehole sorted by depth
            borehole_records = self.search(
                [('borehole_id', '=', record.borehole_id.id)],
                order="depth asc"
            )

            prev_depth = 0.0
            for rec in borehole_records:
                if rec.id == record.id:
                    record.pore_water_pressure = record.depth - prev_depth
                    break
                prev_depth = rec.depth


    @api.depends('pore_water_pressure', 'borehole_id')
    def _compute_total_pore_water_pressure(self):
        for record in self:
            record.total_pore_water_pressure = 0.0  # default

            if not record.borehole_id:
                continue

            # fetch all records for this borehole sorted by depth
            borehole_records = self.search(
                [('borehole_id', '=', record.borehole_id.id)],
                order="depth asc"
            )

            cumulative_pressure = 0.0
            for rec in borehole_records:
                cumulative_pressure += rec.pore_water_pressure or 0.0
                if rec.id == record.id:
                    record.total_pore_water_pressure = round(cumulative_pressure, 3)
                    break


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
                        record.overburden_pressure = round(rec.depth * rec.bulk_den, 3)
                    else:  # subsequent record
                        record.overburden_pressure = round(cumulative_pressure + ((rec.depth - prev_depth) * rec.bulk_den), 3)
                    break
                else:
                    if prev_depth == 0:
                        cumulative_pressure = rec.depth * rec.bulk_den
                    else:
                        cumulative_pressure += (rec.depth - prev_depth) * rec.bulk_den
                    prev_depth = rec.depth


    @api.depends('overburden_pressure', 'total_pore_water_pressure')
    def _compute_effective_overburden_pressure(self):
        for record in self:
            record.effective_overburden_pressure = round((record.overburden_pressure or 0.0) - (record.total_pore_water_pressure or 0.0), 3)

    @api.depends('effective_overburden_pressure')
    def _compute_effective_overburden_pressure_kg(self):
        for record in self:
            record.effective_overburden_pressure_kg = round(record.effective_overburden_pressure / 10, 3)
    
    @api.depends('borehole_id')
    def _compute_observed_n_value(self):
        for record in self:
            borehole_records = self.env["soil.borehole.nvalue"].search([('borehole_id', '=', record.borehole_id.id),("top_depth","=",record.depth)],limit=1)
            record.observed_n_value = borehole_records.n_value
    
    
    @api.depends('effective_overburden_pressure_kg')
    def _compute_overburden_correction_factor(self):
        for record in self:
            record.overburden_correction_factor = 0.0
            v = record.effective_overburden_pressure_kg
            # guard against zero/negative values
            if not v or v <= 0:
                continue
            # log base 10 and round to 3 decimals
            record.overburden_correction_factor = round(0.77 * math.log10(20.0 / v),3)
    
    
    @api.depends('overburden_correction_factor','observed_n_value')
    def _compute_corrected_n_value(self):
        for record in self:
            record.corrected_n_value = round(record.overburden_correction_factor * record.observed_n_value)



class DirectShearTest(models.Model):
    _name = 'direct.shear.test'
    _description = 'Direct Shear Test'

    borehole_id = fields.Many2one('soil.borehole', string='Borehole', ondelete='cascade')
    applied_normal_stress = fields.Integer(string='Applied Normal Stress (Kg/cm²)')
    no_of_divisions = fields.Integer(string='No. of Divisions of Proving ring dial Gauge')
    proving_ring_correction_factor = fields.Float(string='Proving ring correction factor (kg/division)')
    shear_load = fields.Float(string='Shear Load (kg)',compute="_compute_shear_load")
    area_of_specimen = fields.Float(string='Area of specimen before starting the test (cm2) (A0)')
    displacement_dial = fields.Integer(string='Displacement dial gauge reading')
    displacement = fields.Float(string='Displacement in cm (δ)',compute="_compute_displacement", digits=(16, 3))
    corrected_area = fields.Float(string='Corrected Area \n (A0-( δ *6)) or A0 (1- δ /6) in cm2 (A)',compute="_compute_corrected_area")
    shear_stress = fields.Float(string='Shear Stress (Kg/cm²)',compute="_compute_shear_stress")

    @api.depends('proving_ring_correction_factor','no_of_divisions')
    def _compute_shear_load(self):
        for record in self:
            record.shear_load = round(record.proving_ring_correction_factor * record.no_of_divisions,2)

    @api.depends('displacement_dial')
    def _compute_displacement(self):
        for record in self:
            record.displacement = round(record.displacement_dial/1000,3)

    @api.depends('area_of_specimen','displacement')
    def _compute_corrected_area(self):
        for record in self:
            record.corrected_area = round(record.area_of_specimen*(1-record.displacement/6),2)

    @api.depends('shear_load','corrected_area')
    def _compute_shear_stress(self):
        for record in self:
            record.shear_stress = record.shear_load / record.corrected_area

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