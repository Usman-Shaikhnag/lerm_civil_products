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
from math import sqrt, pi
import math

class ERTSoilResistivity(models.Model):
    _name = "ert.soil.resistivity"
    # _description = "Soil Resistivity Test"

    # name= fields.Char("Name",default="Soil")
    name = fields.Char(string="Name", required=True, copy=False, readonly=True, default='New')

    ert_parent_id = fields.Many2one('lerm.ert.parent') 
    

    graph_images = fields.One2many('ert.soil.resistivity.line', 'parent_id',string="Graphs")
    line_ids = fields.One2many("ert.soil.resistivity.line", "parent_id", string="Resistivity Table")

    @api.model
    def create(self, vals):
        if vals.get("name", "New") == "New":
            vals["name"] = self.env["ir.sequence"].next_by_code("ert.soil.resistivity.seq") or "New"
            
        record = super().create(vals)
        if record.ert_parent_id:
            self.env['ert.lines'].sudo().create({
                'parent_id': record.ert_parent_id.id,
                'soil_resistivity_id': record.id
            })
        return record
        
    
    
    def save_ert(self):
        # ert_parent = self.env['lerm.ert.parent'].sudo().search([('id','=',self.ert_parent_id.id)])
        # # import wdb; wdb.set_trace()
        # ert_parent.ert_lines.sudo().create({
        #     'parent_id':ert_parent.id,
        #     'soil_resistivity_id':self.id
        # })
        return {
            'view_mode': 'form',
            'res_model': "lerm.ert.parent",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.ert_parent_id.id,
            
        }
    
    def action_print_soil_resistivity_report(self):
        report = self.env.ref('fst.soil_resistivity_report_py3o')
        filename = f"{self.name or 'ERT'}"
        return report.report_action(self, config={'report_name': filename})


    # def button_add_footer(self):
    #     for rec in self:
    #         # Delete previous footer
    #         footer = rec.line_ids.filtered(lambda l: l.sr_no_label == "Avg. Resistivity")
    #         footer.unlink()

    #         # Data lines only
    #         lines = rec.line_ids.filtered(lambda l: l.sr_no_label != "Avg. Resistivity")
    #         if not lines:
    #             continue

    #         radius_vals = []
    #         for i, line in enumerate(lines, start=1):
    #             line.sr_no_label = str(i)

    #             # Ensure area is defined
    #             if not line.area:
    #                 line.area = 0  # Or compute it here if formula exists

    #             # ----- Auto compute Correct Resistance (*_2) from Site Reading (*_1) -----
    #             line.resistivity_n2 = line.resistivity_n1 * 1 if line.resistivity_n1 else 0
    #             line.resistivity_ne2 = line.resistivity_ne1 * 1 if line.resistivity_ne1 else 0
    #             line.resistivity_e2 = line.resistivity_e1 * 1 if line.resistivity_e1 else 0
    #             line.resistivity_se2 = line.resistivity_se1 * 1 if line.resistivity_se1 else 0
    #             line.resistivity_s2 = line.resistivity_s1 * 1 if line.resistivity_s1 else 0
    #             line.resistivity_sw2 = line.resistivity_sw1 * 1 if line.resistivity_sw1 else 0
    #             line.resistivity_w2 = line.resistivity_w1 * 1 if line.resistivity_w1 else 0
    #             line.resistivity_nw2 = line.resistivity_nw1 * 1 if line.resistivity_nw1 else 0

    #             # ----- Original resistivity calculations -----
    #             line.resistivity_n  = 2 * pi * line.resistivity_n2 * line.spacing if line.resistivity_n2 and line.spacing else 0
    #             line.resistivity_ne = 2 * pi * line.resistivity_ne2 * line.spacing if line.resistivity_ne2 and line.spacing else 0
    #             line.resistivity_e  = 2 * pi * line.resistivity_e2 * line.spacing if line.resistivity_e2 and line.spacing else 0
    #             line.resistivity_se = 2 * pi * line.resistivity_se2 * line.spacing if line.resistivity_se2 and line.spacing else 0
    #             line.resistivity_s  = 2 * pi * line.resistivity_s2 * line.spacing if line.resistivity_s2 and line.spacing else 0
    #             line.resistivity_sw = 2 * pi * line.resistivity_sw2 * line.spacing if line.resistivity_sw2 and line.spacing else 0
    #             line.resistivity_w  = 2 * pi * line.resistivity_w2 * line.spacing if line.resistivity_w2 and line.spacing else 0
    #             line.resistivity_nw = 2 * pi * line.resistivity_nw2 * line.spacing if line.resistivity_nw2 and line.spacing else 0

    #             # Compute radius from area
    #             line.radius = sqrt(line.area / pi) if line.area else 0
    #             radius_vals.append(line.radius)

    #         # Footer average
    #         avg_vals = {
    #             'resistivity_n':  sum([l.resistivity_n for l in lines]) / len(lines),
    #             'resistivity_ne': sum([l.resistivity_ne for l in lines]) / len(lines),
    #             'resistivity_e':  sum([l.resistivity_e for l in lines]) / len(lines),
    #             'resistivity_se': sum([l.resistivity_se for l in lines]) / len(lines),
    #             'resistivity_s':  sum([l.resistivity_s for l in lines]) / len(lines),
    #             'resistivity_sw': sum([l.resistivity_sw for l in lines]) / len(lines),
    #             'resistivity_w':  sum([l.resistivity_w for l in lines]) / len(lines),
    #             'resistivity_nw': sum([l.resistivity_nw for l in lines]) / len(lines),
    #             'radius': sum(radius_vals) / len(radius_vals),
    #         }

    #         # Add footer line
    #         self.env['ert.soil.resistivity.line'].create({
    #             'sr_no': len(lines) + 1,
    #             'sr_no_label': "Avg. Resistivity",
    #             'parent_id': rec.id,
    #             **avg_vals
    #         })

    def button_add_footer(self):
        for rec in self:
            # Delete previous footer
            footer = rec.line_ids.filtered(lambda l: l.sr_no_label == "Avg. Resistivity")
            footer.unlink()

            # Data lines only
            lines = rec.line_ids.filtered(lambda l: l.sr_no_label != "Avg. Resistivity")
            if not lines:
                continue

            radius_vals = []
            for i, line in enumerate(lines, start=1):
                line.sr_no_label = str(i)

                # Ensure area is defined
                if not line.area:
                    line.area = 0  # Or compute it here if formula exists

                # ----- Auto compute Correct Resistance (*_2) from Site Reading (*_1) -----
                line.resistivity_n2  = round(line.resistivity_n1  * rec.factor_multiplied, 2) if line.resistivity_n1  else 0
                line.resistivity_ne2 = round(line.resistivity_ne1 * rec.factor_multiplied, 2) if line.resistivity_ne1 else 0
                line.resistivity_e2  = round(line.resistivity_e1  * rec.factor_multiplied, 2) if line.resistivity_e1  else 0
                line.resistivity_se2 = round(line.resistivity_se1 * rec.factor_multiplied, 2) if line.resistivity_se1 else 0
                line.resistivity_s2  = round(line.resistivity_s1  * rec.factor_multiplied, 2) if line.resistivity_s1  else 0
                line.resistivity_sw2 = round(line.resistivity_sw1 * rec.factor_multiplied, 2) if line.resistivity_sw1 else 0
                line.resistivity_w2  = round(line.resistivity_w1  * rec.factor_multiplied, 2) if line.resistivity_w1  else 0
                line.resistivity_nw2 = round(line.resistivity_nw1 * rec.factor_multiplied, 2) if line.resistivity_nw1 else 0

                # ----- Original resistivity calculations -----
                line.resistivity_n  = round(2 * pi * line.resistivity_n2  * line.spacing, 2) if line.resistivity_n2  and line.spacing else 0
                line.resistivity_ne = round(2 * pi * line.resistivity_ne2 * line.spacing, 2) if line.resistivity_ne2 and line.spacing else 0
                line.resistivity_e  = round(2 * pi * line.resistivity_e2  * line.spacing, 2) if line.resistivity_e2  and line.spacing else 0
                line.resistivity_se = round(2 * pi * line.resistivity_se2 * line.spacing, 2) if line.resistivity_se2 and line.spacing else 0
                line.resistivity_s  = round(2 * pi * line.resistivity_s2  * line.spacing, 2) if line.resistivity_s2  and line.spacing else 0
                line.resistivity_sw = round(2 * pi * line.resistivity_sw2 * line.spacing, 2) if line.resistivity_sw2 and line.spacing else 0
                line.resistivity_w  = round(2 * pi * line.resistivity_w2  * line.spacing, 2) if line.resistivity_w2  and line.spacing else 0
                line.resistivity_nw = round(2 * pi * line.resistivity_nw2 * line.spacing, 2) if line.resistivity_nw2 and line.spacing else 0

                # Compute radius from area
                line.radius = round(sqrt(line.area / pi), 2) if line.area else 0
                radius_vals.append(line.radius)

            # Footer average
            avg_vals = {
                        'resistivity_n':  round(sum([l.resistivity_n  for l in lines]) / len(lines), 2),
                        'resistivity_ne': round(sum([l.resistivity_ne for l in lines]) / len(lines), 2),
                        'resistivity_e':  round(sum([l.resistivity_e  for l in lines]) / len(lines), 2),
                        'resistivity_se': round(sum([l.resistivity_se for l in lines]) / len(lines), 2),
                        'resistivity_s':  round(sum([l.resistivity_s  for l in lines]) / len(lines), 2),
                        'resistivity_sw': round(sum([l.resistivity_sw for l in lines]) / len(lines), 2),
                        'resistivity_w':  round(sum([l.resistivity_w  for l in lines]) / len(lines), 2),
                        'resistivity_nw': round(sum([l.resistivity_nw for l in lines]) / len(lines), 2),
                        'radius':        round(sum(radius_vals) / len(radius_vals), 2),
                    }

            # Add footer line
            self.env['ert.soil.resistivity.line'].create({
                'sr_no': len(lines) + 1,
                'sr_no_label': "Avg. Resistivity",
                'parent_id': rec.id,
                **avg_vals
            })

        

    ert_point = fields.Char(string="ERT")
    factor_multiplied = fields.Float(
        string="Multiplication Factor"    )

    temperature_site = fields.Char(string="Temperature At Site")
    last_weather = fields.Char(string="Last 2 Days Weather")
    current = fields.Char(string="Current")
    voltage = fields.Char(string="Voltage")
    present_weather = fields.Char(string="Present Weather")

    pin_line_ids = fields.One2many("ert.soil.resistivity.pin.line", "parent_id", string="Resistivity Table")

    ert_recommended = fields.Char(string="Recommended ERT")


    avg_equivalent_radius = fields.Float(
        string="Average Equivalent Radius",
       
        store=True
    )

    class_of_soil = fields.Char(
        string="Class Of Soil As Per IS 3043:2018",
      
        store=True
    )

    def action_copy_spacing_to_pin(self):
        for rec in self:
            # Clear old lines
            rec.pin_line_ids.unlink()

            vals_list = []
            for line in rec.line_ids[:-1]:  # last line skip
                vals_list.append({
                    "parent_id": rec.id,
                    "pin_spacing": line.spacing,
                    "equivalent_radius": line.radius,
                })
            if vals_list:
                self.env["ert.soil.resistivity.pin.line"].create(vals_list)

            # ----- Calculate avg_equivalent_radius, ert_recommended & class_of_soil -----
            if rec.pin_line_ids:
                total = sum(rec.pin_line_ids.mapped("equivalent_radius"))
                avg = total / len(rec.pin_line_ids)

                # Average set kar
                rec.avg_equivalent_radius = round(avg, 2)

                # Recommended ERT set kar (rounded + text)
                rec.ert_recommended = f"Approx. {round(avg)} Ω m"

                # Classification logic
                if avg < 25:
                    rec.class_of_soil = "Severely Corrosive"
                elif 25 <= avg < 50:
                    rec.class_of_soil = "Moderately Corrosive"
                elif 50 <= avg <= 100:
                    rec.class_of_soil = "Mildly Corrosive"
                else:
                    rec.class_of_soil = "Very Mild Corrosive"
            else:
                rec.avg_equivalent_radius = 0.0
                rec.ert_recommended = False
                rec.class_of_soil = False

   
    def action_generate_graph(self):
        for rec in self:
        # Collect all values from all lines
            all_values = []
            for line in rec.line_ids:
                if line.sr_no_label != "Avg. Resistivity":
                    all_values.extend([
                        line.resistivity_n, line.resistivity_ne, line.resistivity_e,
                        line.resistivity_se, line.resistivity_s, line.resistivity_sw,
                        line.resistivity_w, line.resistivity_nw
                    ])

            if not all_values:
                continue

            # Compute global ymax
            data_max = max(all_values)

            def round_up_nice(x):
                if x <= 10:
                    return 10
                order = 10 ** int(math.floor(math.log10(x)))
                return math.ceil(x / order) * order

            ymax_global = round_up_nice(data_max)

            for line in rec.line_ids:
                if line.sr_no_label != "Avg. Resistivity":
                    line.action_generate_graph(ymax=ymax_global)



class ERTSoilResistivityLine(models.Model):
    _name = "ert.soil.resistivity.line"
    _description = "Soil Resistivity Line"

    parent_id = fields.Many2one("ert.soil.resistivity", string="Test Point")
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)
    spacing = fields.Float("Pin Spacing (m)")

    resistivity_n1  = fields.Float("North (0°) Resistance (Ω)(site reading)",digits=(16, 2))
    resistivity_n2  = fields.Float("North (0°) Correct Resistance (Ω)", digits=(16, 2))
    resistivity_n  = fields.Float("North (0°) Resistivity", digits=(16, 2))


    resistivity_ne1 = fields.Float("North-East (45°) Resistance (Ω)(site reading)", digits=(16, 2))
    resistivity_ne2 = fields.Float("North-East (45°) Correct Resistance (Ω)", digits=(16, 2))
    resistivity_ne = fields.Float("North-East (45°) Resistivity", digits=(16, 2))

    resistivity_e1  = fields.Float("East (90°) Resistance (Ω)(site reading)", digits=(16, 2))
    resistivity_e2  = fields.Float("East (90°) Correct Resistance (Ω)", digits=(16, 2))
    resistivity_e  = fields.Float("East (90°) Resistivity", digits=(16, 2))

    resistivity_se1 = fields.Float("South-East (135°) Resistance (Ω)(site reading)", digits=(16, 2))
    resistivity_se2 = fields.Float("South-East (135°) Correct Resistance (Ω)", digits=(16, 2))
    resistivity_se = fields.Float("South-East (135°) Resistivity", digits=(16, 2))

    resistivity_s1  = fields.Float("South (180°) Resistance (Ω)(site reading)", digits=(16, 2))
    resistivity_s2  = fields.Float("South (180°) Correct Resistance (Ω)", digits=(16, 2))
    resistivity_s  = fields.Float("South (180°) Resistivity", digits=(16, 2))

    resistivity_sw1 = fields.Float("South-West (225°) Resistance (Ω)(site reading)", digits=(16, 2))
    resistivity_sw2 = fields.Float("South-West (225°) Correct Resistance (Ω)", digits=(16, 2))
    resistivity_sw = fields.Float("South-West (225°) Resistivity", digits=(16, 2))

    resistivity_w1  = fields.Float("West (270°) Resistance (Ω)(site reading)", digits=(16, 2))
    resistivity_w2  = fields.Float("West (270°) Correct Resistance (Ω)", digits=(16, 2))
    resistivity_w  = fields.Float("West (270°) Resistivity", digits=(16, 2))

    resistivity_nw1 = fields.Float("North-West (315°) Resistance (Ω)(site reading)", digits=(16, 2))
    resistivity_nw2 = fields.Float("North-West (315°) Correct Resistance (Ω)", digits=(16, 2))
    resistivity_nw = fields.Float("North-West (315°) Resistivity", digits=(16, 2))

    area = fields.Float("Area",digits=(12,4))
    radius = fields.Float("Radius")


    sr_no_label = fields.Char(string="Sr No Label")


    
    

   

    graph_image = fields.Binary("Graph", readonly=True)
    
    def action_generate_graph(self, ymax=None):
        
        # Example data
        categories = ['N', 'NE', 'E', 'SE', 'S','SW','W','NW']
        values = [self.resistivity_n, self.resistivity_ne, self.resistivity_e, self.resistivity_se, self.resistivity_s, self.resistivity_sw, self.resistivity_w, self.resistivity_nw]
        
        # Compute min and max dynamically
        data_min = min(values)
        data_max = max(values)
        
        # def round_up_nice(x):
        #     """Round up to a 'nice' number like 10, 20, 50, 100, 200, 500, 1000"""
        #     if x <= 10:
        #         return 10
        #     order = 10 ** int(math.floor(math.log10(x)))   # base scale
        #     if x <= 2 * order:
        #         return 2 * order
        #     elif x <= 5 * order:
        #         return 5 * order
        #     else:
        #         return 10 * order
        def round_up_nice(x):
            if x <= 10:
                return 10
            order = 10 ** int(math.floor(math.log10(x)))
            return math.ceil(x / order) * order

        ymin = 0
        if ymax is None:
            ymax = round_up_nice(data_max)
        
        N = len(categories)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles += angles[:1]   # close loop
        values += values[:1]   # close loop

        # Angles (rotate so N is at top, and go clockwise)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles = [np.pi/2 - a for a in angles]   # start at top, then go clockwise
        angles += angles[:1]   # close loop



        fig, ax = plt.subplots(figsize=(8, 8))

        # --- Draw polygon grid (manual Cartesian conversion) ---
        steps = 5
        yticks = np.linspace(ymin, ymax, steps + 1)

        for y in yticks[1:]:  # skip center
            xs = [y * np.cos(a) for a in angles]
            ys = [y * np.sin(a) for a in angles]
            ax.plot(xs, ys, color="gray", linewidth=0.8)

        # Add radial lines
        for a in angles[:-1]:
            ax.plot([0, ymax * np.cos(a)], [0, ymax * np.sin(a)], 
                    color="gray", linewidth=0.8)
        
        # Plot actual values (convert polar to cartesian)
        xs = [v * np.cos(a) for v, a in zip(values, angles)]
        ys = [v * np.sin(a) for v, a in zip(values, angles)]

        ax.plot(xs, ys, color='blue', linewidth=2, label="Actual")
        
        
        def classify_soil(resistivity):
            if resistivity < 25:
                return "Severely corrosive"
            elif 25 <= resistivity <= 50:
                return "Moderately corrosive"
            elif 50 < resistivity <= 100:
                return "Mildly corrosive"
            else:  # resistivity > 100
                return "Very mild corrosive"

        # --- Compute polygon area using shoelace formula ---
        def polygon_area(x, y):
            return 0.5 * abs(sum(x[i] * y[i+1] - x[i+1] * y[i] for i in range(len(x)-1)))

        area = polygon_area(xs, ys)
        print(f"Area of polygon = {area:.2f}")

        # --- Equivalent radius of polygon area ---
        radius_equiv = math.sqrt(area / math.pi)
        print(f"Equivalent radius = {radius_equiv:.2f}")

        # Add value labels
        # Add value labels (exact decimals)
        # for v, a in zip(values[:-1], angles[:-1]):
        #     x, y = v * np.cos(a), v * np.sin(a)
        #     ax.text(x*1.05, y*1.05, str(v), ha='center', va='center', fontsize=9)
        
        for v, a in zip(values[:-1], angles[:-1]):
            x, y = v * np.cos(a), v * np.sin(a)

            # Convert angle to degrees
            angle_deg = np.degrees(a)
            if angle_deg < -90 or angle_deg > 90:
                angle_deg += 180

            # push labels outward (adjust factor if still overlapping)
            offset = 0.8
            
            ax.text(
                x * offset- 0.08 * ymax, y * offset, f"{v:.2f}",
                ha='center', va='center',
                fontsize=11,
                rotation=angle_deg,
                rotation_mode='anchor'
            )


        
        # Category labels (place slightly beyond ymax)
        for cat, a in zip(categories, angles[:-1]):
            x, y = (ymax*1.1) * np.cos(a), (ymax*1.1) * np.sin(a)
            ax.text(x, y, cat, ha='center', va='center', fontsize=10, fontweight="bold")

        # --- Add diagonal radial labels dynamically ---
        label_angle = np.pi / 2.05   # 90 degrees
        for y in yticks[1:]:
            x, yy = y * np.cos(label_angle), y * np.sin(label_angle)
            ax.text(x*1.5, yy*1, f"{int(y)}", ha='left', va='bottom', fontsize=10, fontweight="bold")
        
        # Add red circle at outer radius
        circle = plt.Circle((0, 0), radius_equiv, color='red', fill=False, linewidth=2)
        ax.add_patch(circle)

        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect('equal')

        # Remove the border/spines
        for spine in ax.spines.values():
            spine.set_visible(False)
            
        
        soil_type = classify_soil(radius_equiv)

        
        
        fig.text(0.05, 0.05, f"Corrosion Assessment = {soil_type}", 
         ha='left', va='bottom', fontsize=10, color="black")

        fig.text(0.05, 0.09, f"Equivalent Radius (i.e. av. Resistivity) = {radius_equiv:.2f}", 
                ha='left', va='bottom', fontsize=10, color="black")

        
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)

        self.graph_image = base64.b64encode(buf.read()).decode("utf-8")
        self.area = round(area, 2)
        self.radius = round(radius_equiv, 2)


    # def action_generate_graph(self):
    #     def _radar_factory(num_vars, frame='polygon', proj_name='radar_poly'):
    #         theta_vars = np.linspace(0, 2*np.pi, num_vars, endpoint=False)

    #         class RadarAxes(PolarAxes):
    #             name = proj_name

    #             def _gen_axes_patch(self):
    #                 if frame == 'polygon':
    #                     return RegularPolygon((0.5, 0.5), num_vars, radius=.5, edgecolor="0.5")
    #                 return super()._gen_axes_patch()

    #             def _gen_axes_spines(self):
    #                 if frame == 'polygon':
    #                     spine = Spine(axes=self, spine_type='circle',
    #                                 path=Path.unit_regular_polygon(num_vars))
    #                     spine.set_transform(Affine2D().scale(.5).translate(.5, .5) + self.transAxes)
    #                     return {'polar': spine}
    #                 return super()._gen_axes_spines()

    #             def set_varlabels(self, labels):
    #                 self.set_thetagrids(np.degrees(theta_vars), labels)

    #         register_projection(RadarAxes)
    #         return theta_vars, proj_name

    #     for rec in self:
    #         labels = ["N","NE","E","SE","S","SW","W","NW"]

    #         # Take values from this line only
    #         values = [
    #             rec.resistivity_n,
    #             rec.resistivity_ne,
    #             rec.resistivity_e,
    #             rec.resistivity_se,
    #             rec.resistivity_s,
    #             rec.resistivity_sw,
    #             rec.resistivity_w,
    #             rec.resistivity_nw,
    #         ]

    #         # Equivalent avg resistivity (exclude zeros)
    #         nonzero = [v for v in values if v]
    #         equivalent_resistivity = (sum(nonzero)/len(nonzero)) if nonzero else 0

    #         theta_vars, proj_name = _radar_factory(8, frame='polygon')
    #         theta_closed = np.r_[theta_vars, theta_vars[0]]

    #         scale = 0.50
    #         values_scaled = [v * scale for v in values]
    #         values_scaled_closed = values_scaled + [values_scaled[0]]

    #         fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(projection=proj_name))

    #         ax.set_theta_zero_location("N")
    #         ax.set_theta_direction(-1)
    #         ax.set_xticks(theta_vars)
    #         ax.set_xticklabels(labels, fontsize=10)
    #         for t in ax.get_xticklabels():
    #             t.set_rotation(0); t.set_ha("center"); t.set_va("center")
    #         ax.set_rlabel_position(0)
    #         ax.grid(True, linewidth=0.6, alpha=0.6)

    #         ax.plot(theta_closed, values_scaled_closed, color="blue", linewidth=1.5, label="Measured Resistivity")
    #         ax.scatter(theta_vars, values_scaled, color="blue", s=30, zorder=5)

    #         for ang, val_s, val in zip(theta_vars, values_scaled, values):
    #             if val:
    #                 rotation = np.degrees(ang)
    #                 if rotation > 90 and rotation < 270:
    #                     rotation += 180  # flip text to stay upright
    #                 elif rotation == 90:
    #                     rotation = 0
    #                 elif rotation == 270:
    #                     rotation = 0

    #                 ax.text(
    #                     ang, val_s * 0.80, f"{val:.2f}",
    #                     ha="center", va="center", fontsize=8,
    #                     rotation=rotation,rotation_mode="anchor",
    #                     )

    #         circle_theta = np.linspace(0, 2*np.pi, 360)
    #         circle_radius = equivalent_resistivity * scale
    #         ax.plot(circle_theta, [circle_radius] * len(circle_theta),
    #                 color="red", linewidth=2.5, alpha=0.9, label="Equivalent Resistivity")

    #         ax.set_ylim(0, max(values_scaled) * 1.2 if any(values_scaled) else 1)

    #         plt.figtext(0.10, 0.02, f"Equivalent radius (i.e., avg. Resistivity) = {equivalent_resistivity:.2f} Ωm",
    #                     ha="left", fontsize=10)
    #         plt.figtext(0.10, 0.00, "Corrosion assessment = Very mild corrosive",
    #                     ha="left", fontsize=10)

    #         buf = io.BytesIO()
    #         plt.savefig(buf, format="png")
    #         plt.close(fig)
    #         buf.seek(0)
    #         rec.graph_image = base64.b64encode(buf.read()).decode("utf-8")

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(ERTSoilResistivityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class ERTSoilResistivityPinLine(models.Model):
    _name = "ert.soil.resistivity.pin.line"
    _description = "Soil Resistivity Line"

    parent_id = fields.Many2one("ert.soil.resistivity", string="Test Point")
    pin_spacing = fields.Float("Pin Spacing (m)")
    equivalent_radius = fields.Float("Equivalent Radius")
    # class_of_soil = fields.Char("Class of Soil")