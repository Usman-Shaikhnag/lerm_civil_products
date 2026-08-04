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




    # remark

    notes_id = fields.One2many('soilresistivity.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(SoilResistivity, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The information marked with an # received from customer',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'The results listed refer only to tested parameters and sample as received from customer',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'The balance samples if any will be discarded after 15 days from the date of issue of test certificate unless otherwise specified.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'This document shall not be reproduced in part or full without the approval of Genstru.',
            }),
        ]

        res['notes_id'] = default_notes
        return res







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

                # Original resistivity calculations
                line.resistivity_n  = 2 * pi * line.resistivity_n2 * line.spacing if line.resistivity_n2 and line.spacing else 0
                line.resistivity_ne = 2 * pi * line.resistivity_ne2 * line.spacing if line.resistivity_ne2 and line.spacing else 0
                line.resistivity_e  = 2 * pi * line.resistivity_e2 * line.spacing if line.resistivity_e2 and line.spacing else 0
                line.resistivity_se = 2 * pi * line.resistivity_se2 * line.spacing if line.resistivity_se2 and line.spacing else 0
                line.resistivity_s  = 2 * pi * line.resistivity_s2 * line.spacing if line.resistivity_s2 and line.spacing else 0
                line.resistivity_sw = 2 * pi * line.resistivity_sw2 * line.spacing if line.resistivity_sw2 and line.spacing else 0
                line.resistivity_w  = 2 * pi * line.resistivity_w2 * line.spacing if line.resistivity_w2 and line.spacing else 0
                line.resistivity_nw = 2 * pi * line.resistivity_nw2 * line.spacing if line.resistivity_nw2 and line.spacing else 0

                # Compute radius from area
                line.radius = sqrt(line.area / pi)
                radius_vals.append(line.radius)

            # Footer average
            avg_vals = {
                'resistivity_n':  sum([2*pi*l.resistivity_n2*l.spacing for l in lines])/len(lines),
                'resistivity_ne': sum([2*pi*l.resistivity_ne2*l.spacing for l in lines])/len(lines),
                'resistivity_e':  sum([2*pi*l.resistivity_e2*l.spacing for l in lines])/len(lines),
                'resistivity_se': sum([2*pi*l.resistivity_se2*l.spacing for l in lines])/len(lines),
                'resistivity_s':  sum([2*pi*l.resistivity_s2*l.spacing for l in lines])/len(lines),
                'resistivity_sw': sum([2*pi*l.resistivity_sw2*l.spacing for l in lines])/len(lines),
                'resistivity_w':  sum([2*pi*l.resistivity_w2*l.spacing for l in lines])/len(lines),
                'resistivity_nw': sum([2*pi*l.resistivity_nw2*l.spacing for l in lines])/len(lines),
                'radius': sum(radius_vals)/len(radius_vals),
            }

            # Add footer line
            self.env['soil.resistivity.line'].create({
                'sr_no': len(lines) + 1,
                'sr_no_label': "Avg. Resistivity",
                'parent_id': rec.id,
                **avg_vals
            })
        

    ert_point = fields.Char(string="ERT POINT NO")

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
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)
    spacing = fields.Float("Pin Spacing (m)")

    resistivity_n1  = fields.Float("North (0°) Resistance (Ω)(site reading)")
    resistivity_n2  = fields.Float("North (0°) Correct Resistance (Ω)")
    resistivity_n  = fields.Float("North (0°) Resistivity")


    resistivity_ne1 = fields.Float("North-East (45°) Resistance (Ω)(site reading)")
    resistivity_ne2 = fields.Float("North-East (45°) Correct Resistance (Ω)")
    resistivity_ne = fields.Float("North-East (45°) Resistivity")

    resistivity_e1  = fields.Float("East (90°) Resistance (Ω)(site reading)")
    resistivity_e2  = fields.Float("East (90°) Correct Resistance (Ω)")
    resistivity_e  = fields.Float("East (90°) Resistivity")

    resistivity_se1 = fields.Float("South-East (135°) Resistance (Ω)(site reading)")
    resistivity_se2 = fields.Float("South-East (135°) Correct Resistance (Ω)")
    resistivity_se = fields.Float("South-East (135°) Resistivity")

    resistivity_s1  = fields.Float("South (180°) Resistance (Ω)(site reading)")
    resistivity_s2  = fields.Float("South (180°) Correct Resistance (Ω)")
    resistivity_s  = fields.Float("South (180°) Resistivity")

    resistivity_sw1 = fields.Float("South-West (225°) Resistance (Ω)(site reading)")
    resistivity_sw2 = fields.Float("South-West (225°) Correct Resistance (Ω)")
    resistivity_sw = fields.Float("South-West (225°) Resistivity")

    resistivity_w1  = fields.Float("West (270°) Resistance (Ω)(site reading)")
    resistivity_w2  = fields.Float("West (270°) Correct Resistance (Ω)")
    resistivity_w  = fields.Float("West (270°) Resistivity")

    resistivity_nw1 = fields.Float("North-West (315°) Resistance (Ω)(site reading)")
    resistivity_nw2 = fields.Float("North-West (315°) Correct Resistance (Ω)")
    resistivity_nw = fields.Float("North-West (315°) Resistivity")

    area = fields.Float("Area",digits=(12,4))
    radius = fields.Float("Radius")


    sr_no_label = fields.Char(string="Sr No Label")


    
    

   

    graph_image = fields.Binary("Graph", readonly=True)
    
    def action_generate_graph(self):
        
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
                x * offset, y * offset, f"{v:.2f}",
                ha='center', va='center',
                fontsize=11,
                rotation=angle_deg,
                rotation_mode='anchor'
            )


        
        # Category labels (place slightly beyond ymax)
        for cat, a in zip(categories, angles[:-1]):
            x, y = (ymax*1.1) * np.cos(a), (ymax*1.1) * np.sin(a)
            ax.text(x, y, cat, ha='center', va='center', fontsize=10,color="red", fontweight="bold")

        # # --- Add diagonal radial labels dynamically ---
        # label_angle = np.pi / 2   # 60 degrees
        # for y in yticks[1:]:
        #     x, yy = y * np.cos(label_angle), y * np.sin(label_angle)
        #     ax.text(x*1, yy*1, f"{int(y)}", ha='left', va='bottom', fontsize=9, color="black")
        
        label_angle = np.pi / 2  # 90 degrees (vertical)
        x_offset = 1.2  # Adjust this value to control how far to the right the labels move

        for y in yticks[1:]:
            x, yy = y * np.cos(label_angle), y * np.sin(label_angle)
            # Add x_offset to move labels to the right
            ax.text(x + x_offset, yy, f"{int(y)}", ha='left', va='bottom', fontsize=9, color="black")
        # --- Add diagonal radial labels dynamically ---
        # label_angle = angles[0]   # this corresponds to North
        # for y in yticks[1:]:
        #     x, yy = y * np.cos(label_angle), y * np.sin(label_angle)
        #     ax.text(
        #         x, yy + (0.05 * ymax), f"{int(y)}",
        #         ha='center', va='bottom',
        #         fontsize=11, fontweight="bold",
        #         color="blue",     # custom color works now
        #         rotation=0,
        #         rotation_mode='anchor'
        #     )


        
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
        self.area = area
        self.radius = radius_equiv

   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(SoilResistivityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class SoilResistivityPinLine(models.Model):
    _name = "soil.resistivity.pin.line"
    _description = "Soil Resistivity Line"

    parent_id = fields.Many2one("soil.resistivity", string="Test Point")
    pin_spacing = fields.Float("Pin Spacing (m)")
    equivalent_radius = fields.Float("Equivalent Radius")
    class_of_soil = fields.Char("Class of Soil")




    
class soilresistivityNotes(models.Model):
    _name = "soilresistivity.notes"

    parent_id = fields.Many2one('soil.resistivity',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")