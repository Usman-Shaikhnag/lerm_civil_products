from odoo import models, fields, api
import matplotlib.pyplot as plt
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
from matplotlib.patches import RegularPolygon
from matplotlib.spines import Spine
from matplotlib.path import Path
from matplotlib.transforms import Affine2D
import matplotlib
import numpy as np
import io, base64

class SoilResistivity(models.Model):
    _name = "soil.resistivity"
    _inherit = "lerm.eln"
    # _description = "Soil Resistivity Test"

    name= fields.Char("Name",default="Soil")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    graph_images = fields.One2many('soil.resistivity.line', 'parent_id',string="Graphs")
    line_ids = fields.One2many("soil.resistivity.line", "parent_id", string="Resistivity Table")

    temperature_site = fields.Char(string="Temperature At Site :")
    last_weather = fields.Char(string="Last 2 Days Weather :")
    voltage = fields.Char(string="Voltage :")
    present_weather = fields.Char(string="Present Weather :")

    pin_line_ids = fields.One2many("soil.resistivity.pin.line", "parent_id", string="Resistivity Table")

    avg_equivalent_radius = fields.Float(string="Average Equivalent Radius", compute="_compute_avg_equivalent_radius", store=True)

    @api.depends('pin_line_ids.equivalent_radius')
    def _compute_avg_equivalent_radius(self):
        for rec in self:
            if rec.pin_line_ids:
                total = sum(line.equivalent_radius for line in rec.pin_line_ids if line.equivalent_radius)
                count = len([line for line in rec.pin_line_ids if line.equivalent_radius])
                rec.avg_equivalent_radius = total / count if count > 0 else 0.0
            else:
                rec.avg_equivalent_radius = 0.0
   
    def action_generate_graph(self):
        for rec in self:
            for line in rec.line_ids:
                line.action_generate_graph()


    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(SoilResistivity, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

class SoilResistivityLine(models.Model):
    _name = "soil.resistivity.line"
    _description = "Soil Resistivity Line"

    parent_id = fields.Many2one("soil.resistivity", string="Test Point")
    spacing = fields.Float("Pin Spacing (m)")
    resistivity_n  = fields.Float("North (0°)")
    resistivity_ne = fields.Float("North-East (45°)")
    resistivity_e  = fields.Float("East (90°)")
    resistivity_se = fields.Float("South-East (135°)")
    resistivity_s  = fields.Float("South (180°)")
    resistivity_sw = fields.Float("South-West (225°)")
    resistivity_w  = fields.Float("West (270°)")
    resistivity_nw = fields.Float("North-West (315°)")

    graph_image = fields.Binary("Graph", readonly=True)

    def action_generate_graph(self):
        def _radar_factory(num_vars, frame='polygon', proj_name='radar_poly'):
            theta_vars = np.linspace(0, 2*np.pi, num_vars, endpoint=False)

            class RadarAxes(PolarAxes):
                name = proj_name

                def _gen_axes_patch(self):
                    if frame == 'polygon':
                        return RegularPolygon((0.5, 0.5), num_vars, radius=.5, edgecolor="0.5")
                    return super()._gen_axes_patch()

                def _gen_axes_spines(self):
                    if frame == 'polygon':
                        spine = Spine(axes=self, spine_type='circle',
                                    path=Path.unit_regular_polygon(num_vars))
                        spine.set_transform(Affine2D().scale(.5).translate(.5, .5) + self.transAxes)
                        return {'polar': spine}
                    return super()._gen_axes_spines()

                def set_varlabels(self, labels):
                    self.set_thetagrids(np.degrees(theta_vars), labels)

            register_projection(RadarAxes)
            return theta_vars, proj_name

        for rec in self:
            labels = ["N","NE","E","SE","S","SW","W","NW"]

            # Take values from this line only
            values = [
                rec.resistivity_n,
                rec.resistivity_ne,
                rec.resistivity_e,
                rec.resistivity_se,
                rec.resistivity_s,
                rec.resistivity_sw,
                rec.resistivity_w,
                rec.resistivity_nw,
            ]

            # Equivalent avg resistivity (exclude zeros)
            nonzero = [v for v in values if v]
            equivalent_resistivity = (sum(nonzero)/len(nonzero)) if nonzero else 0

            theta_vars, proj_name = _radar_factory(8, frame='polygon')
            theta_closed = np.r_[theta_vars, theta_vars[0]]

            scale = 0.50
            values_scaled = [v * scale for v in values]
            values_scaled_closed = values_scaled + [values_scaled[0]]

            fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(projection=proj_name))

            ax.set_theta_zero_location("N")
            ax.set_theta_direction(-1)
            ax.set_xticks(theta_vars)
            ax.set_xticklabels(labels, fontsize=10)
            for t in ax.get_xticklabels():
                t.set_rotation(0); t.set_ha("center"); t.set_va("center")
            ax.set_rlabel_position(0)
            ax.grid(True, linewidth=0.6, alpha=0.6)

            ax.plot(theta_closed, values_scaled_closed, color="blue", linewidth=1.5, label="Measured Resistivity")
            ax.scatter(theta_vars, values_scaled, color="blue", s=30, zorder=5)

            for ang, val_s, val in zip(theta_vars, values_scaled, values):
                if val:
                    rotation = np.degrees(ang)
                    if rotation > 90 and rotation < 270:
                        rotation += 180  # flip text to stay upright
                    elif rotation == 90:
                        rotation = 0
                    elif rotation == 270:
                        rotation = 0

                    ax.text(
                        ang, val_s * 0.80, f"{val:.2f}",
                        ha="center", va="center", fontsize=8,
                        rotation=rotation,rotation_mode="anchor",
                        )

            circle_theta = np.linspace(0, 2*np.pi, 360)
            circle_radius = equivalent_resistivity * scale
            ax.plot(circle_theta, [circle_radius] * len(circle_theta),
                    color="red", linewidth=2.5, alpha=0.9, label="Equivalent Resistivity")

            ax.set_ylim(0, max(values_scaled) * 1.2 if any(values_scaled) else 1)

            plt.figtext(0.10, 0.02, f"Equivalent radius (i.e., avg. Resistivity) = {equivalent_resistivity:.2f} Ωm",
                        ha="left", fontsize=10)
            plt.figtext(0.10, 0.00, "Corrosion assessment = Very mild corrosive",
                        ha="left", fontsize=10)

            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            plt.close(fig)
            buf.seek(0)
            rec.graph_image = base64.b64encode(buf.read()).decode("utf-8")



class SoilResistivityPinLine(models.Model):
    _name = "soil.resistivity.pin.line"
    _description = "Soil Resistivity Line"

    parent_id = fields.Many2one("soil.resistivity", string="Test Point")
    pin_spacing = fields.Float("Pin Spacing (m)")
    equivalent_radius = fields.Float("Equivalent Radius")
    class_of_soil = fields.Char("Class of Soil")