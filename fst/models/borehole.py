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
# Helper function for Interpolation
def interpolate_d_value(percent_passing, sieve_size_log, target_percent):
    """Interpolates the particle size (D value) corresponding to a target percent passing."""
    try:
        # np.interp performs linear interpolation on the provided arrays
        log_d_value = np.interp(
            target_percent, 
            percent_passing, 
            sieve_size_log
        )
        # Convert back from log scale to linear size (mm)
        return np.exp10(log_d_value)
    except Exception:
        return 0.0
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
    direct_shear_graph = fields.Binary("Direct Shear Graph", store=True)
    cohesion = fields.Float(
        string='Cohesion (C) (Kg/cm²)', 
        # compute='_compute_shear_parameters', 
        store=True,
        digits=(16, 3)
    )
    angle_of_internal_friction = fields.Float(
        string='Angle of Internal Friction (\u03C6) (\u00b0)', 
        # compute='_compute_shear_parameters', 
        store=True,
        digits=(16, 2)
    )

    # Link to the Grain Size Analysis test records (One2many)
    grain_size_ids = fields.One2many("grain.size.analysis", "borehole_id", string="Grain Size Analysis Tests")

    # Fields to store the calculated results and the graph
    d10 = fields.Float(string='D10 (mm)', store=True, digits=(16, 3))
    d30 = fields.Float(string='D30 (mm)', store=True, digits=(16, 3))
    d60 = fields.Float(string='D60 (mm)', store=True, digits=(16, 3))
    cu = fields.Float(string='Coefficient of Uniformity (Cu)', store=True, digits=(16, 2))
    cc = fields.Float(string='Coefficient of Curvature (Cc)', store=True, digits=(16, 2))
    
    grain_size_graph = fields.Binary("Grain Size Graph", store=True)

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

    # @api.depends('direct_shear_ids.applied_normal_stress', 'direct_shear_ids.shear_stress')
    def generate_shear_parameters(self):
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
            ax.set_title(f'Direct Shear Test Results ({borehole.name})', pad=20)
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

    # Dependency changed to rely on the final output field: passing_percent
    # @api.depends('grain_size_ids.line_ids.passing_percent', 'grain_size_ids.line_ids.sieve_size')
    def generate_grain_size_parameters(self):
        for borehole in self:
            # Reset parameters for the current borehole
            borehole.d10 = borehole.d30 = borehole.d60 = borehole.cu = borehole.cc = 0.0
            borehole.grain_size_graph = False

            if not borehole.grain_size_ids:
                continue
            
            # --- 1. D-Value and Cu/Cc Calculation (Using the FIRST valid analysis) ---
            # Find the first valid analysis to calculate D-values and Cu/Cc
            first_valid_analysis = None
            for analysis_candidate in borehole.grain_size_ids:
                # Data Collection and Validation for calculation
                if not analysis_candidate.line_ids or len(analysis_candidate.line_ids) < 2:
                    continue

                valid_lines_calc = []
                for line in analysis_candidate.line_ids:
                    try:
                        sieve_size_mm = float(line.sieve_size)
                        if sieve_size_mm > 0:
                            valid_lines_calc.append(line)
                    except ValueError:
                        continue

                if len(valid_lines_calc) >= 2:
                    first_valid_analysis = analysis_candidate
                    break
            
            if not first_valid_analysis:
                continue

            valid_lines_calc.sort(key=lambda r: float(r.sieve_size), reverse=True)

            sieve_sizes_calc = np.array([float(r.sieve_size) for r in valid_lines_calc])
            percent_passing_calc = np.array([r.passing_percent for r in valid_lines_calc])
            
            # D-Value Calculation Setup
            sort_indices = np.argsort(percent_passing_calc)
            sorted_percent_passing = percent_passing_calc[sort_indices]
            sorted_sieve_sizes = sieve_sizes_calc[sort_indices]
            log_sorted_sieve_sizes = np.log10(sorted_sieve_sizes)

            # Calculate D-values
            d10 = interpolate_d_value(sorted_percent_passing, log_sorted_sieve_sizes, 10.0)
            d30 = interpolate_d_value(sorted_percent_passing, log_sorted_sieve_sizes, 30.0)
            d60 = interpolate_d_value(sorted_percent_passing, log_sorted_sieve_sizes, 60.0)

            # Calculate Cu and Cc
            cu = d60 / d10 if d10 > 0 and d60 > 0 else 0
            cc = (d30**2) / (d60 * d10) if d60 * d10 > 0 and d30 > 0 else 0

            # Store the calculated values
            borehole.d10 = d10
            borehole.d30 = d30
            borehole.d60 = d60
            borehole.cu = cu
            borehole.cc = cc

            # --- 2. Generate the Graph (Plotting ALL valid analyses) ---
            plt.style.use('seaborn-v0_8-whitegrid')
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # List to store all collected data for multi-curve plotting
            all_sieve_data = []

            # Iterate through all analyses to collect and plot data
            for analysis in borehole.grain_size_ids:
                # Re-run data validation for each analysis
                if not analysis.line_ids or len(analysis.line_ids) < 2:
                    continue
                
                valid_lines = []
                for line in analysis.line_ids:
                    try:
                        sieve_size_mm = float(line.sieve_size)
                        if sieve_size_mm > 0:
                            valid_lines.append(line)
                    except ValueError:
                        continue

                if len(valid_lines) < 2: continue
                    
                valid_lines.sort(key=lambda r: float(r.sieve_size), reverse=True)

                sieve_sizes = np.array([float(r.sieve_size) for r in valid_lines])
                percent_passing = np.array([r.passing_percent for r in valid_lines])
                
                # PLOT THE CONNECTED POINTS (Line graph) FOR THE CURRENT ANALYSIS
                ax.semilogx(sieve_sizes, percent_passing, marker='o', linestyle='-',
                            label=f'Sample: {analysis.sample_name}')

            # --- Formatting and Axis Settings ---
            
            # 1. Y-axis limit increased to 110 to provide padding for the 100% line
            ax.set_ylim(0, 110) 
            ax.set_ylabel('Percent Passing (%)')
            
            # X-axis (Log Scale, setting custom ticks and limits)
            custom_xticks = np.array([0.001, 0.01, 0.1, 1.0, 10.0, 100.0])
            ax.set_xlim(custom_xticks.min(), custom_xticks.max()) 
            ax.set_xticks(custom_xticks)
            
            ax.get_xaxis().set_major_formatter(plt.ScalarFormatter()) 
            ax.set_xlabel('Sieve Size (mm) [Log Scale]')
            
            # 2. Grid lines increased density: set Y-axis minor ticks and enable minor grid on both axes
            
            # Y-axis Major Ticks (every 10%)
            ax.set_yticks(np.arange(0, 101, 10), minor=False) 
            # Y-axis Minor Ticks (every 5%)
            ax.set_yticks(np.arange(0, 101, 5), minor=True) 

            # Enable both major and minor grids on both axes
            ax.grid(True, which="major", axis="both", ls="-", linewidth=0.8)
            ax.grid(True, which="minor", axis="both", ls="--", linewidth=0.5)

            # Add Legend to differentiate the curves
            ax.legend(
                    loc='upper center', # Use 'upper center' as the anchor point *on the legend*
                    bbox_to_anchor=(0.5, -0.15), # Coordinates (x, y) relative to the axis (0,0 is bottom left)
                    ncol=len(borehole.grain_size_ids), # Optional: Display legends in one row
                    fancybox=True,
                    shadow=True,
                    fontsize=9
                )

            # --- Annotations (D-Values) ---
            # Horizontal guidelines for D-values (10%, 30%, 60%)
            ax.axhline(y=10, color='red', linestyle='--', linewidth=0.8)
            ax.axhline(y=30, color='red', linestyle='--', linewidth=0.8)
            ax.axhline(y=60, color='red', linestyle='--', linewidth=0.8)
            
            # Vertical projection lines calculated D-values (from the FIRST valid analysis)
            if d10 > 0: ax.axvline(x=d10, color='red', linestyle=':', linewidth=0.8)
            if d30 > 0: ax.axvline(x=d30, color='red', linestyle=':', linewidth=0.8)
            if d60 > 0: ax.axvline(x=d60, color='red', linestyle=':', linewidth=0.8)

            # Adjust text annotation position to fit in the new Y-axis range
            ax.text(custom_xticks.min() * 1.5, 105, f'Cu: {cu:.2f}', fontsize=10, color='k')
            ax.text(custom_xticks.min() * 1.5, 100, f'Cc: {cc:.2f}', fontsize=10, color='k')

            ax.set_title(f'Grain Size Distribution Curve ({borehole.name})', pad=20)
            
            plt.tight_layout()

            # --- 3. Save and Store the Graph ---
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            plt.close(fig)

            borehole.grain_size_graph = base64.b64encode(buffer.getvalue())
            buffer.close()


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
            record.shear_load = round(
                (record.proving_ring_correction_factor or 0.0) * (record.no_of_divisions or 0), 
                2
            )

    @api.depends('displacement_dial')
    def _compute_displacement(self):
        for record in self:
            record.displacement = round((record.displacement_dial or 0) / 1000, 3)

    @api.depends('area_of_specimen','displacement')
    def _compute_corrected_area(self):
        for record in self:
            if record.area_of_specimen:
                record.corrected_area = round(
                    record.area_of_specimen * (1 - (record.displacement or 0) / 6), 
                    2
                )
            else:
                record.corrected_area = 0.0

    @api.depends('shear_load', 'corrected_area')
    def _compute_shear_stress(self):
        for record in self:
            if record.corrected_area:  # not zero or None
                record.shear_stress = round(record.shear_load / record.corrected_area, 3)
            else:
                record.shear_stress = 0.0


class GrainSizeAnalysisLine(models.Model):
    _name = 'grain.size.analysis.line'
    
    analysis_id = fields.Many2one('grain.size.analysis', string='Analysis', ondelete='cascade')
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size mm")
    percent_retained = fields.Float(string='% of Weight Retained')
    wt_retained = fields.Float(string="Wt. Retained in gms",compute="_compute_wt_retained")
    cumulative_retained = fields.Float(string="% of Cumulative Wt. Retained",compute="_compute_cumulative_retained")
    passing_percent = fields.Float(string="% of wt passing",compute="_compute_passing_percent")

    @api.model
    def create(self, vals):
        if vals.get('analysis_id'):
            existing_records = self.search([('analysis_id', '=', vals['analysis_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(GrainSizeAnalysisLine, self).create(vals)

    def _reorder_serial_numbers(self):
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(GrainSizeAnalysisLine, self).unlink()

        if parent_id:
            parent_id.line_ids._reorder_serial_numbers()

        return res

    @api.depends('percent_retained')
    def _compute_wt_retained(self):
        for record in self:
            record.wt_retained = (record.percent_retained*200)/100

    @api.depends('percent_retained', 'analysis_id.line_ids.percent_retained')
    def _compute_cumulative_retained(self):
        for record in self:
            record.cumulative_retained = 0.0  # ✅ default, ensures all records get a value
            if not record.analysis_id:
                continue

            # Get all lines of same analysis ordered by serial_no
            lines = record.analysis_id.line_ids.sorted('serial_no')
            cumulative = 0.0
            for line in lines:
                cumulative += line.percent_retained
                if line.id == record.id:
                    record.cumulative_retained = cumulative
                    break


    @api.depends('cumulative_retained')
    def _compute_passing_percent(self):
        for record in self:
            record.passing_percent = max(0.0, 100 - record.cumulative_retained)


class GrainSizeAnalysis(models.Model):
    _name = 'grain.size.analysis'
    _description = 'Grain Size Analysis Test'
    
    borehole_id = fields.Many2one('soil.borehole', string='Borehole', ondelete='cascade')
    sample_name = fields.Char(string='Sample ID/Depth', required=True) 
    
    line_ids = fields.One2many("grain.size.analysis.line", "analysis_id", string="Sieve Analysis Data")


    # 1. Define the specific Sieve Sizes (in mm)
    STANDARD_SIEVE_SIZES = [
        100.0, 75.0, 19.0, 4.75, 2.0, 0.425, 0.075, 0.001
    ]

    @api.onchange('sample_name')
    def _onchange_sample_name_populate_lines(self):
        """
        Automatically populates line_ids with the 8 standard sieve sizes 
        when the user starts a new record by entering the sample name.
        """
        # Only proceed if:
        # 1. The record is new (self.id is False in onchange context) OR has no lines.
        # 2. A sample_name has been provided (to use as a trigger).
        if not self.line_ids and self.sample_name:
            new_lines_commands = []
            
            # Create a command (0, 0, {values}) for each standard sieve size
            for sieve_size in self.STANDARD_SIEVE_SIZES:
                new_lines_commands.append(
                    # Command (0, 0, {values}) is the Odoo instruction to "create a new record"
                    (0, 0, {
                        'sieve_size': sieve_size,
                        'passing_percent': 0.0, 
                    })
                )
            
            # Assigning this list of commands makes the rows appear in the view instantly.
            self.line_ids = new_lines_commands