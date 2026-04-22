from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math
import matplotlib.pyplot as plt
import io
import base64
import matplotlib.ticker as ticker
import numpy as np
import math
from scipy.interpolate import CubicSpline , interp1d , Akima1DInterpolator
from scipy.optimize import minimize_scalar
from io import BytesIO
from scipy.interpolate import make_interp_spline
from matplotlib.ticker import LogLocator, MultipleLocator
import re
from matplotlib.ticker import LogLocator, ScalarFormatter
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d
from matplotlib.ticker import AutoMinorLocator
from decimal import Decimal, getcontext


from matplotlib.ticker import MultipleLocator, StrMethodFormatter





class Soil(models.Model):
    _name = "mechanical.soil1"
    _inherit = "lerm.eln"
    _rec_name = "name_soil"


    name_soil = fields.Char("Name",default="Soil")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)




    # remark

    notes_id = fields.One2many('soil.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(Soil, self).default_get(fields)

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
    




    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'soil.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id


    # Sieve Analysis
    sieve_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")
 
    sieve_analysis_child_lines = fields.One2many('mechanical.soil.sieve.analysis.line','parent_id',string="Sieve Analysis",default=lambda self: self._default_sieve_analysis_child_lines())

    boulder = fields.Float(string="% Boulders ",compute="_compute_boulder")

    # gravel = fields.Float(string="%Gravels",compute="_compute_gravel")
    # sand = fields.Float(string="%Sand",compute="_compute_sand")
    # silt_clay = fields.Float(string="%Clay",compute="_compute_clay_fraction")

    # silt = fields.Float(string="%Silt",compute="_compute_silt")
    
    wt_of_sample = fields.Float(string="Weight of Sample, gms")

    gravel = fields.Float(string="% Gravel", compute="_compute_soil_fraction", store=True)
    sand = fields.Float(string="% Sand", compute="_compute_soil_fraction", store=True)
    silt_clay = fields.Float(string="% Silt & Clay", compute="_compute_soil_fraction", store=True)
    total_percent = fields.Float(string="Total (%)", compute="_compute_soil_fraction", store=True)

  

    @api.depends('sieve_analysis_child_lines.passing_percent',
             'sieve_analysis_child_lines.percent_retained',
             'sieve_analysis_child_lines.sieve_size')
    def _compute_soil_fraction(self):
     for record in self:

        gravel = 0.0
        passing_475 = 0.0
        passing_0075 = None   # important

        smallest_passing = None

        for line in record.sieve_analysis_child_lines:
            sieve_text = str(line.sieve_size).strip().lower()

            if 'pan' in sieve_text:
                continue

            match = re.search(r'([\d\.]+)', sieve_text)
            if not match:
                continue

            size_value = float(match.group(1))

            # µ → mm
            if 'µ' in sieve_text:
                size_mm = size_value / 1000.0
            else:
                size_mm = size_value

            # Track smallest (fallback)
            if smallest_passing is None or size_mm < smallest_passing[0]:
                smallest_passing = (size_mm, line.passing_percent or 0.0)

            # Gravel boundary
            if abs(size_mm - 4.75) < 0.001:
                gravel = line.percent_retained or 0.0
                passing_475 = line.passing_percent or 0.0

            # Correct silt/clay boundary
            if abs(size_mm - 0.075) < 0.001:
                passing_0075 = line.passing_percent or 0.0

        # -----------------------------
        # FINAL VALUES
        # -----------------------------
        if passing_0075 is not None:
            silt_clay = passing_0075
        elif smallest_passing:
            silt_clay = smallest_passing[1]   # fallback
        else:
            silt_clay = 0.0

        sand = passing_475 - silt_clay

        record.gravel = gravel
        record.sand = sand
        record.silt_clay = silt_clay
        record.total_percent = gravel + sand + silt_clay

    total_weight = fields.Float(
    string="Total Weight Retained (gms)",
    compute="_compute_total_weight",
    store=True)

    @api.depends('sieve_analysis_child_lines.wt_retained')
    def _compute_total_weight(self):
     for rec in self:
        total = sum(rec.sieve_analysis_child_lines.mapped('wt_retained'))
        rec.total_weight = total
        


    # @api.depends('sieve_analysis_child_lines.passing_percent', 'sieve_analysis_child_lines.sieve_size')
    # def _compute_clay_fraction(self):
    #     for record in self:
    #         total = 0.0
    #         for line in record.sieve_analysis_child_lines:
    #             sieve_text = str(line.sieve_size).strip()
    #             match = re.search(r'([\d\.]+)', sieve_text)
    #             if not match:
    #                 continue
    #             try:
    #                 size_value = float(match.group(1))
    #             except ValueError:
    #                 continue

    #             # µ to mm conversion
    #             if 'µ' in sieve_text or 'mic' in sieve_text.lower():
    #                 size_mm = size_value / 1000.0
    #             else:
    #                 size_mm = size_value

    #             # range check for clay fraction (< 0.002 mm)
    #             # if 0 <= size_mm < 0.002:
    #             if abs(size_mm - 0.075) < 0.0001:
                
    #                 total += line.passing_percent or 0.0

    #         record.silt_clay = total  # Use a separate field for clay fraction


    # @api.depends('sieve_analysis_child_lines.passing_percent', 'sieve_analysis_child_lines.sieve_size')
    # def _compute_silt(self):
    #     for record in self:
    #         total = 0.0
    #         for line in record.sieve_analysis_child_lines:
    #             sieve_text = str(line.sieve_size).strip()
    #             match = re.search(r'([\d\.]+)', sieve_text)
    #             if not match:
    #                 continue
    #             try:
    #                 size_value = float(match.group(1))
    #             except ValueError:
    #                 continue

    #             # µ ते mm convert करा
    #             if 'µ' in sieve_text or 'mic' in sieve_text.lower():
    #                 size_mm = size_value / 1000.0
    #             else:
    #                 size_mm = size_value

    #             # range check (0.002 - 0.075 mm)
    #             if 0.002 <= size_mm <= 0.075:
                
    #                 total += line.passing_percent or 0.0

    #         record.silt = total

    # # ---------- Gravel ----------
    # @api.depends('sieve_analysis_child_lines.percent_retained', 'sieve_analysis_child_lines.sieve_size')
    # def _compute_gravel(self):
    #     for record in self:
    #         total = 0.0
    #         for line in record.sieve_analysis_child_lines:
    #             sieve_text = str(line.sieve_size).strip()
    #             match = re.search(r'([\d\.]+)', sieve_text)
    #             if not match:
    #                 continue
    #             try:
    #                 size_value = float(match.group(1))
    #             except ValueError:
    #                 continue

    #             # µ ते mm convert करा
    #             if 'µ' in sieve_text or 'mic' in sieve_text.lower():
    #                 size_mm = size_value / 1000.0
    #             else:
    #                 size_mm = size_value

    #             # range check (4.75 - 80 mm)
    #             if 4.75 <= size_mm <= 79.99:
    #                 total += line.percent_retained or 0.0

    #         record.gravel = total

    # @api.depends('sieve_analysis_child_lines.percent_retained')
    # def _compute_boulder(self):
    #     for record in self:
    #         boulder_sum = 0.0

    #         for line in record.sieve_analysis_child_lines:
    #             size_str = str(line.sieve_size).replace("µ", "e-3").replace("mm", "")
    #             try:
    #                 # µm → mm conversion
    #                 if "e-3" in size_str:
    #                     size_val = float(size_str) * 0.001
    #                 else:
    #                     size_val = float(size_str)
    #             except ValueError:
    #                 size_val = 0.0

    #             # Boulder range: sieve size > 79.99 mm
    #             if size_val > 79.99:
    #                 boulder_sum += line.percent_retained or 0.0

    #         record.boulder = boulder_sum

    # @api.depends('gravel', 'silt_clay')
    # def _compute_sand(self):
    #     for record in self:
    #         record.sand = 100 - ((record.gravel or 0.0) + (record.silt_clay or 0.0))

    d60 = fields.Float(string="D60 (mm)",compute="_compute_d60",digits=(12,4))
    d30 = fields.Float(string="D30 (mm)",compute="_compute_d30",digits=(12,4))
    d10 = fields.Float(string="D10 (mm)",compute="_compute_d10",digits=(12,4))
    cu = fields.Float(string="Cu = D60/D10",compute="_compute_cu",digits=(12,4))
    cc = fields.Float(string="Cc = D30^2/D10* D60",compute="_compute_cc_slive",digits=(12,4))


    @api.depends('sieve_analysis_child_lines.sieve_size', 'sieve_analysis_child_lines.passing_percent')
    def _compute_d60(self):
        for record in self:
            # extract 16mm and 10mm lines
            line_16 = next((l for l in record.sieve_analysis_child_lines if '16' in str(l.sieve_size)), None)
            line_10 = next((l for l in record.sieve_analysis_child_lines if '10' in str(l.sieve_size)), None)

            if line_16 and line_10 and line_16.passing_percent is not None and line_10.passing_percent is not None:
                try:
                    x1 = 16.0
                    x2 = 10.0
                    y1 = float(line_16.passing_percent)
                    y2 = float(line_10.passing_percent)

                    # Check to avoid division by zero
                    if y2 != y1:
                        # Linear interpolation to find D60
                        d60_value = x1 + (x2 - x1) * ((60 - y1) / (y2 - y1))
                    else:
                        d60_value = 0.0

                    record.d60 = d60_value
                except Exception:
                    record.d60 = 0.0
            else:
                record.d60 = 0.0

    @api.depends('sieve_analysis_child_lines.sieve_size', 'sieve_analysis_child_lines.passing_percent')
    def _compute_d30(self):
        for record in self:
            # extract 4.75mm and 2.36mm lines
            line_4_75 = next((l for l in record.sieve_analysis_child_lines if '4.75' in str(l.sieve_size)), None)
            line_2_36 = next((l for l in record.sieve_analysis_child_lines if '2.36' in str(l.sieve_size)), None)

            if line_4_75 and line_2_36 and line_4_75.passing_percent is not None and line_2_36.passing_percent is not None:
                try:
                    x1 = 4.75
                    x2 = 2.36
                    y1 = float(line_4_75.passing_percent)
                    y2 = float(line_2_36.passing_percent)

                    # Linear interpolation for target percent = 10%
                    target_percent = 30.0

                    if y2 != y1:
                        d30_value = x1 + (x2 - x1) * ((target_percent - y1) / (y2 - y1))
                    else:
                        d30_value = 0.0

                    record.d30 = d30_value
                except Exception:
                    record.d30 = 0.0
            else:
                record.d30 = 0.0

    @api.depends('sieve_analysis_child_lines.sieve_size', 'sieve_analysis_child_lines.passing_percent')
    def _compute_d10(self):
        for record in self:
            # find lines 1.18 mm and 600 µ
            line_1_18 = next((l for l in record.sieve_analysis_child_lines if '1.18' in str(l.sieve_size)), None)
            line_600um = next((l for l in record.sieve_analysis_child_lines if '600' in str(l.sieve_size)), None)

            if line_1_18 and line_600um and line_1_18.passing_percent is not None and line_600um.passing_percent is not None:
                try:
                    # Convert sieve sizes to mm
                    x1 = 1.18
                    x2 = 0.6  # 600 µm = 0.6 mm
                    y1 = float(line_1_18.passing_percent)
                    y2 = float(line_600um.passing_percent)

                    target_percent = 10.0  # D10 corresponds to 10% passing

                    if y2 != y1:
                        d10_value = x1 + (x2 - x1) * ((target_percent - y1) / (y2 - y1))
                    else:
                        d10_value = 0.0

                    record.d10 = d10_value
                except Exception:
                    record.d10 = 0.0
            else:
                record.d10 = 0.0


    # --- Compute Cu ---
    @api.depends('d60','d10')
    def _compute_cu(self):
        for record in self:
            if record.d10 and record.d10 != 0:
                record.cu = record.d60 / record.d10
            else:
                record.cu = 0.0

    # --- Compute Cc ---
    @api.depends('d30','d10','d60')
    def _compute_cc_slive(self):
        for record in self:
            if record.d10 and record.d10 != 0 and record.d60 and record.d60 != 0:
                record.cc = (record.d30 ** 2) / (record.d10 * record.d60)
            else:
                record.cc = 0.0
    



    @api.model
    def _default_sieve_analysis_child_lines(self):
        default_lines = [
            # (0, 0, {'sieve_size': '80mm'}),
            # (0, 0, {'sieve_size': '40mm '}),
            # (0, 0, {'sieve_size': '20mm'}),
            # (0, 0, {'sieve_size': '16mm'}),
            # (0, 0, {'sieve_size': '10mm'}),
            # (0, 0, {'sieve_size': '4.75mm'}),
            # (0, 0, {'sieve_size': ' 2.36mm'}),
            # (0, 0, {'sieve_size': '1.18mm'}),
            # (0, 0, {'sieve_size': '600 µ'}),
            # (0, 0, {'sieve_size': '425 µ'}),
            # (0, 0, {'sieve_size': '300µ'}),
            # (0, 0, {'sieve_size': '212µ'}),
            # (0, 0, {'sieve_size': '150µ'}),
            # (0, 0, {'sieve_size': '75µ'}),
            # (0, 0, {'sieve_size': 'Pan'})

          
            (0, 0, {'sieve_size': '4.750mm'}),
            (0, 0, {'sieve_size': '2.000mm'}),
            (0, 0, {'sieve_size': '0.425mm'}),
            (0, 0, {'sieve_size': '0.075mm'}),
            (0, 0, {'sieve_size': 'Pan'})
        ]
        return default_lines


    # @api.onchange('sieve_analysis_child_lines')
    # def _onchange_sieve_analysis_child_lines(self):
    #     for rec in self:
    #         pan_line = None
    #         total_retained = 0.0
    #         target_sieves = ['80mm','40mm','20mm','16mm', '10mm', '4.75mm', '2.36mm','1.18mm','600 µ','425 µ','300µ','212µ','150µ','75µ']

    #         for line in rec.sieve_analysis_child_lines:
    #             if line.sieve_size and line.sieve_size.lower() == 'pan':
    #                 pan_line = line
    #             elif line.sieve_size in target_sieves:
    #                 total_retained += line.wt_retained or 0.0

    #         if pan_line:
    #             pan_line.wt_retained = (rec.wt_of_sample or 0.0) - total_retained




    def calculate_sieve(self): 
        for record in self:
            previous_cumulative = 0  
            for line in record.sieve_analysis_child_lines:
                print("Rows", str(line.percent_retained))
                previous_line = line.serial_no - 1

                # If this line is 'Pan', directly assign fixed values
                # if line.sieve_size and line.sieve_size.lower() == 'pan':
                #     line.write({
                #         'cumulative_retained': 100.00,
                #         'passing_percent': 0.00,
                #     })
                #     print("PAN LINE: cumulative_retained=100, passing_percent=0")
                #     continue  # skip rest of logic for pan

                # Normal sieve calculation
                if previous_line == 0:
                    cumulative_retained = line.percent_retained
                else:
                    previous_line_record = self.env['mechanical.soil.sieve.analysis.line'].sudo().search([
                        ("serial_no", "=", previous_line),
                        ("parent_id", "=", record.id)
                    ], limit=1)
                    
                    if previous_line_record:
                        previous_cumulative = previous_line_record.cumulative_retained
                    cumulative_retained = previous_cumulative + line.percent_retained

                passing_percent = 100 - cumulative_retained

                # Write updated values
                line.write({
                    'cumulative_retained': round(cumulative_retained, 2),
                    'passing_percent': round(passing_percent, 2),
                })

                print("Updated Cumulative Retained:", cumulative_retained)
                print("Updated Passing Percent:", passing_percent)

                previous_cumulative = cumulative_retained



                   

   

    
    
    # @api.depends('sieve_analysis_child_lines.wt_retained')
    # def _compute_total_sieve(self):
    #     for record in self:
    #         print("recordd",record)
    #         record.total_sieve_analysis = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))

    graph_image_slive = fields.Binary("Sieve Graph", compute="_compute_graph_image_slive", store=True)

    @api.depends('sieve_analysis_child_lines.cumulative_retained', 'sieve_analysis_child_lines.passing_percent')
    def _compute_graph_image_slive(self):
        for record in self:
            if record.sieve_analysis_child_lines:
                record.graph_image_slive = record.generate_line_chart_slive()
            else:
                record.graph_image_slive = False




    def generate_line_chart_slive(self):
   
        x_value = []
        y_value = []
        x_labels = []

        for line in self.sieve_analysis_child_lines:
            if line.sieve_size and line.passing_percent is not None:
                sieve_str = str(line.sieve_size).strip().lower()
                try:
                    if 'mm' in sieve_str:
                        sieve_val = float(sieve_str.replace('mm', '').strip())
                        label = f"{int(sieve_val)} mm"
                    elif 'µ' in sieve_str or 'micron' in sieve_str:
                        sieve_val = float(sieve_str.replace('µ', '').replace('micron', '').strip()) / 1000
                        label = f"{int(float(line.sieve_size.replace('µ', '').replace('micron', '').strip()))} µm"
                    else:
                        sieve_val = float(sieve_str)
                        label = f"{sieve_val} mm"

                    x_value.append(sieve_val)
                    y_value.append(float(line.passing_percent))
                    x_labels.append(label)
                except ValueError:
                    continue

        if not x_value or not y_value:
            return False

        # Sort ascending
        sorted_data = sorted(zip(x_value, y_value, x_labels))
        x_value, y_value, x_labels = zip(*sorted_data)

        plt.figure(figsize=(12, 5))
        plt.xscale('log')

        # Main curve
        plt.plot(x_value, y_value, color='blue', linestyle='-', linewidth=2)
        plt.scatter(x_value, y_value, color='red', edgecolors='black', s=60, zorder=5)

        plt.xlabel('Sieve Size', fontsize=12)
        plt.ylabel('Passing %', fontsize=12)
        plt.title('Grain Size Analysis', fontsize=14)

        ax = plt.gca()
        plt.xticks(ticks=x_value, labels=x_labels, rotation=45, ha='right')
        ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(1.0, 10.0)*0.1, numticks=200))
        ax.yaxis.set_minor_locator(MultipleLocator(2))
        plt.grid(True, which='both', axis='both', linestyle='--', linewidth=0.3, color='gray', alpha=0.8)

        plt.xlim(left=min(x_value)/1.5, right=max(x_value)*1.5)
        plt.ylim(bottom=0, top=100)

        # --- D-points: D10, D30, D60 ---
        d_points = [
            (getattr(self, 'd10', None), 10, 'black'),
            (getattr(self, 'd30', None), 30, 'yellow'),
            (getattr(self, 'd60', None), 60, 'orange')
        ]

        for dx, dy, color in d_points:
            if dx:
                # Solid point
                plt.scatter(dx, dy, color=color, s=80, zorder=10)
                # Draw X and Y guide lines only to intersection
                plt.plot([dx, dx], [0, dy], color=color, linestyle='-', linewidth=1.2)
                plt.plot([0, dx], [dy, dy], color=color, linestyle='-', linewidth=1.2)

        # Save figure
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)

        return base64.b64encode(buffer.read())
    


    # Texture
    texture_name = fields.Char("Name",default="Texture")
    texture_visible = fields.Boolean("Texture Visible",compute="_compute_visible")
 
    texture_lines = fields.One2many('texture.soil.line','parent_id',string="Sieve Analysis")

    avg_sand = fields.Float(string="Average Sand",compute="_compute_totals")
    avg_silt = fields.Float(string="Average Silt",compute="_compute_totals")
    avg_clay = fields.Float(string="Average Clay",compute="_compute_totals")

    @api.depends('texture_lines.percent_sand', 'texture_lines.percent_silt', 'texture_lines.percent_clay')
    def _compute_totals(self):
     for rec in self:
        total_sand = total_silt = total_clay = 0.0
        count = len(rec.texture_lines)

        if count > 0:
            for line in rec.texture_lines:
                total_sand += line.percent_sand
                total_silt += line.percent_silt
                total_clay += line.percent_clay

            rec.avg_sand = total_sand / count
            rec.avg_silt = total_silt / count
            rec.avg_clay = total_clay / count
        else:
            rec.avg_sand = rec.avg_silt = rec.avg_clay = 0.0


    # Sand Equivalent
    sandeq_name = fields.Char("Name",default="Sand Equivalent")
    sandeq_line_ids = fields.One2many(
        'sand.equivalent.line',
        'parent_id',
        string="Samples"
    )

    average_se = fields.Float(
        "Average Sand Equivalent",
        compute="_compute_average",
        store=True
    )

    requirement = fields.Char(
        default="Requirement "
    )

    @api.depends('sandeq_line_ids.sand_equivalent')
    def _compute_average(self):
        for rec in self:
            total = 0.0
            count = len(rec.sandeq_line_ids)

            if count > 0:
                for line in rec.sandeq_line_ids:
                    total += line.sand_equivalent

                rec.average_se = total / count
            else:
                rec.average_se = 0.0


    



    # Moisture Content

    moisture_content_name = fields.Char("Name",default="Moisture Content")
    moisture_content_visible = fields.Boolean("Moisture Content Visible", compute="_compute_visible")

    moisture_content_lines = fields.One2many('moisture.content.line','parent_id',string="Water Content")

    avg_moisture_content = fields.Float('Average Moisture Content (%)',compute="_compute_avg_moisture_content")

    @api.onchange('moisture_content_lines')
    def _onchange_moisture_content_lines(self):
     for rec in self:
        for index, line in enumerate(rec.moisture_content_lines):
            line.serial_no = index + 1

    @api.depends("moisture_content_lines.moisture_content")
    def _compute_avg_moisture_content(self):
        for rec in self:
            if rec.moisture_content_lines:
                vals = rec.moisture_content_lines.mapped("moisture_content")
                rec.avg_moisture_content = sum(vals) / len(vals)
            else:
                rec.avg_moisture_content = 0.0

    avg_moisture_content_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_moisture_content_conformity", store=True)

    @api.depends('avg_moisture_content','eln_ref','grade')
    def _compute_avg_moisture_content_conformity(self):
        
        for record in self:
            record.avg_moisture_content_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','800a2dc9-49fe-4dab-83e8-63758c7f351a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','800a2dc9-49fe-4dab-83e8-63758c7f351a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_moisture_content - record.avg_moisture_content*mu_value
                    upper = record.avg_moisture_content + record.avg_moisture_content*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_moisture_content_conformity = 'pass'
                        break
                    else:
                        record.avg_moisture_content_conformity = 'fail'

    avg_moisture_content_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_moisture_content_nabl", store=True)

    @api.depends('avg_moisture_content','eln_ref','grade')
    def _compute_avg_moisture_content_nabl(self):
        
        for record in self:
            record.avg_moisture_content_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','800a2dc9-49fe-4dab-83e8-63758c7f351a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','800a2dc9-49fe-4dab-83e8-63758c7f351a')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_moisture_content - record.avg_moisture_content*mu_value
            upper = record.avg_moisture_content + record.avg_moisture_content*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_moisture_content_nabl = 'pass'
                break
            else:
                record.avg_moisture_content_nabl = 'fail'


    # Specific Gravity

    specific_gravity_name = fields.Char("Name",default="Specific Gravity")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    specific_gravity_lines = fields.One2many('specific.gravity.line','parent_id',string="Specific Gravity")

    avg_specific_gravity = fields.Float('Average Specific Gravity',compute="_compute_avg_specific_gravity",digits=(10,3))


    @api.onchange('specific_gravity_lines')
    def _onchange_specific_gravity_lines(self):
     for rec in self:
        for index, line in enumerate(rec.specific_gravity_lines):
            line.serial_no = index + 1

    @api.depends("specific_gravity_lines.specific_gravity")
    def _compute_avg_specific_gravity(self):
        for rec in self:
            if rec.specific_gravity_lines:
                vals = rec.specific_gravity_lines.mapped("specific_gravity")
                rec.avg_specific_gravity = sum(vals) / len(vals)
            else:
                rec.avg_specific_gravity = 0.0

    avg_specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_specific_gravity_conformity", store=True)

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_conformity(self):
        
        for record in self:
            record.avg_specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214hhj6gt21-ca64-44dd-b0ae-6587gghty')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214hhj6gt21-ca64-44dd-b0ae-6587gghty')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_specific_gravity - record.avg_specific_gravity*mu_value
                    upper = record.avg_specific_gravity + record.avg_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.avg_specific_gravity_conformity = 'fail'

    avg_specific_gravity_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_specific_gravity_nabl", store=True)

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_nabl(self):
        
        for record in self:
            record.avg_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214hhj6gt21-ca64-44dd-b0ae-6587gghty')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214hhj6gt21-ca64-44dd-b0ae-6587gghty')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_specific_gravity - record.avg_specific_gravity*mu_value
            upper = record.avg_specific_gravity + record.avg_specific_gravity*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_specific_gravity_nabl = 'pass'
                break
            else:
                record.avg_specific_gravity_nabl = 'fail'


    # Liquid Limit

    liquid_limit_name = fields.Char("Name",default="Liquid Limit")
    liquid_limit_visible = fields.Boolean("Liquid Limit Visible",compute="_compute_visible")


    water_line_ids = fields.One2many(
        'water.content.line',
        'parent_id',
        string="Water Content"
    )

    liquid_limit = fields.Float(
        string="Liquid Limit (LL)",
        compute="_compute_liquid_limit",
        store=True
    )

   
    @api.depends('water_line_ids.blows', 'water_line_ids.water_content')
    def _compute_liquid_limit(self):
     for record in self:

        # 🔥 Force compute
        record.water_line_ids._compute_values()

        lines = record.water_line_ids.filtered(
            lambda l: l.blows and l.water_content > 0
        )

        if len(lines) < 2:
            record.liquid_limit = 0.0
            continue

        lines_sorted = sorted(lines, key=lambda l: l.blows)
        target = 25.0

        lower = None
        upper = None

        for line in lines_sorted:
            if line.blows < target:
                lower = line
            elif line.blows >= target and lower:
                upper = line
                break

        if lower and upper:
            x1, x2 = lower.blows, upper.blows
            y1, y2 = lower.water_content, upper.water_content

            if x2 != x1:
                ll_value = y1 + (y2 - y1) * (target - x1) / (x2 - x1)
            else:
                ll_value = y1

            record.liquid_limit = ll_value
        else:
            record.liquid_limit = 0.0

    

    

    @api.onchange('water_line_ids')
    def _onchange_water_line_ids(self):
     for rec in self:
        for index, line in enumerate(rec.water_line_ids):
            line.serial_no = index + 1


    liquid_limit_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_liquid_limit_conformity", store=True)

    @api.depends('liquid_limit','eln_ref','grade')
    def _compute_liquid_limit_conformity(self):
        
        for record in self:
            record.liquid_limit_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23fg21gh-7202-4d62-864b-8efa58b6b61f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23fg21gh-7202-4d62-864b-8efa58b6b61f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.liquid_limit - record.liquid_limit*mu_value
                    upper = record.liquid_limit + record.liquid_limit*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.liquid_limit_conformity = 'pass'
                        break
                    else:
                        record.liquid_limit_conformity = 'fail'

    liquid_limit_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_liquid_limit_nabl", store=True)

    @api.depends('liquid_limit','eln_ref','grade')
    def _compute_liquid_limit_nabl(self):
        
        for record in self:
            record.liquid_limit_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23fg21gh-7202-4d62-864b-8efa58b6b61f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23fg21gh-7202-4d62-864b-8efa58b6b61f')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.liquid_limit - record.liquid_limit*mu_value
            upper = record.liquid_limit + record.liquid_limit*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.liquid_limit_nabl = 'pass'
                break
            else:
                record.liquid_limit_nabl = 'fail'

    graph_image = fields.Binary(string="Flow Curve Graph")




    def action_generate_graph(self):
     for rec in self:

        rec.water_line_ids._compute_values()

        # -------------------------------
        # 🔥 FORCE ALL DATA (NO FILTER)
        # -------------------------------
        blows = np.array([float(l.blows or 0) for l in rec.water_line_ids])
        water = np.array([float(l.water_content or 0) for l in rec.water_line_ids])

        # Remove only invalid (0)
        mask = (blows > 0) & (water > 0)
        blows = blows[mask]
        water = water[mask]

        print("DATA USED:", list(zip(blows, water)))  # DEBUG

        if len(blows) < 2:
            continue

        # -------------------------------
        # SORT
        # -------------------------------
        idx = np.argsort(blows)
        blows = blows[idx]
        water = water[idx]

        # -------------------------------
        # LOG REGRESSION
        # -------------------------------
        log_b = np.log10(blows)
        coeffs = np.polyfit(log_b, water, 1)
        fit = np.poly1d(coeffs)

        # FULL EXTENDED LINE
        log_x = np.linspace(np.log10(1), np.log10(100), 200)
        x_smooth = 10 ** log_x
        y_smooth = fit(log_x)

        # -------------------------------
        # GRAPH
        # -------------------------------
        fig, ax = plt.subplots(figsize=(10, 5))

        ax.set_xscale('log')
        ax.set_axisbelow(True)

        # GRID
        ax.xaxis.set_major_locator(LogLocator(base=10))
        ax.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10)*0.1))

        ax.grid(which='major', linewidth=1)
        ax.grid(which='minor', linewidth=0.5)

        ax.set_xlim(1, 100)
        ax.set_ylim(25, 40)

        # -------------------------------
        # LINE
        # -------------------------------
        ax.plot(x_smooth, y_smooth,
                color='orange',
                linewidth=1.5,
                zorder=2)

        # -------------------------------
        # 🔥 PLOT EACH POINT SEPARATELY (KEY FIX)
        # -------------------------------
        for x, y in zip(blows, water):
            ax.scatter(x, y,
                       color='blue',
                       s=90,
                       edgecolors='black',
                       zorder=5)

        # -------------------------------
        # LL LINES
        # -------------------------------
        ax.axvline(25, color='blue', linewidth=2)

        if rec.liquid_limit:
            ax.axhline(rec.liquid_limit, color='green', linewidth=2)

        # -------------------------------
        # LABELS
        # -------------------------------
        ax.set_title("LIQUID LIMIT TEST GRAPH (CASAGRANDE)")
        ax.set_xlabel("No. of Blows")
        ax.set_ylabel("Water Content (%)")

        ax.xaxis.set_major_formatter(ScalarFormatter())

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        plt.close()

        rec.graph_image = base64.b64encode(buffer.getvalue())

      


    graph_image1 = fields.Binary(string="Flow Curve Graph")

  

    def action_generate_cone_graph(self):
     for rec in self:

        # -------------------------------
        # 🔥 FORCE COMPUTE
        # -------------------------------
        rec.water_line_ids._compute_values()

        # -------------------------------
        # GET DATA (NO LOSS)
        # -------------------------------
        blows = []
        water = []

        for l in rec.water_line_ids:
            if l.blows and l.water_content > 0:
                blows.append(float(l.blows))
                water.append(float(l.water_content))

        blows = np.array(blows)
        water = np.array(water)

        if len(blows) < 2:
            continue

        # -------------------------------
        # SORT
        # -------------------------------
        idx = np.argsort(blows)
        blows = blows[idx]
        water = water[idx]

        # -------------------------------
        # REGRESSION
        # -------------------------------
        coeffs = np.polyfit(blows, water, 1)
        fit = np.poly1d(coeffs)

        x_smooth = np.linspace(min(blows), max(blows), 100)
        y_smooth = fit(x_smooth)

        # -------------------------------
        # GRAPH
        # -------------------------------
        fig, ax = plt.subplots(figsize=(10, 5))

        ax.set_axisbelow(True)

        # -------------------------------
        # GRID (EXCEL STYLE)
        # -------------------------------
        ax.grid(which='major', linewidth=1)
        ax.minorticks_on()
        ax.grid(which='minor', linewidth=0.5)

        # -------------------------------
        # ✅ DYNAMIC AXIS (FIXED ISSUE)
        # -------------------------------
        x_min = min(blows)
        x_max = max(blows)

        y_min = min(water)
        y_max = max(water)

        ax.set_xlim(x_min - 5, x_max + 5)
        ax.set_ylim(y_min - 2, y_max + 2)

        # Prevent clipping
        ax.margins(x=0.1, y=0.1)

        # -------------------------------
        # LINE
        # -------------------------------
        ax.plot(x_smooth, y_smooth,
                color='black',
                linewidth=1.5,
                zorder=2)

        # -------------------------------
        # POINTS (ALL VISIBLE)
        # -------------------------------
        ax.scatter(blows, water,
                   color='blue',
                   s=70,
                   edgecolors='black',
                   zorder=5)

        # -------------------------------
        # LABELS
        # -------------------------------
        ax.set_title("LIQUID LIMIT GRAPH\n(CONE PENETRATION)", fontsize=14)
        ax.set_xlabel("NO. BLOWS")
        ax.set_ylabel("WATER CONTENT (%)")

        # -------------------------------
        # SAVE
        # -------------------------------
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        plt.close()

        rec.graph_image1 = base64.b64encode(buffer.getvalue())




    # Platic Limit

    plastic_limit_name = fields.Char("Name",default="Plastic Limit")
    plastic_limit_visible = fields.Boolean("Plastic Limit Visible",compute="_compute_visible")

    plastic_line_ids = fields.One2many('plastic.limit.line','parent_id',string="Plastic Limit")


    plastic_limit = fields.Float(string="Plastic Limit (PL)",compute="_compute_pl",store=True)

    @api.depends('plastic_line_ids.water_content')
    def _compute_pl(self):
     for rec in self:
        values = rec.plastic_line_ids.mapped('water_content')
        rec.plastic_limit = round(sum(values) / len(values), 2) if values else 0.0

    @api.onchange('plastic_line_ids')
    def _onchange_plastic_line_ids(self):
     for rec in self:
        for index, line in enumerate(rec.plastic_line_ids):
            line.serial_no = index + 1

    plastic_limit_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Plastic Limit Conformity", compute="_compute_plastic_limit_conformity", store=True)

    @api.depends('plastic_limit','eln_ref','grade')
    def _compute_plastic_limit_conformity(self):
        
        for record in self:
            record.plastic_limit_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','120vbf14-2ff0-4b81-aca1-0e07dab7cd87')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','120vbf14-2ff0-4b81-aca1-0e07dab7cd87')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.plastic_limit - record.plastic_limit*mu_value
                    upper = record.plastic_limit + record.plastic_limit*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.plastic_limit_conformity = 'pass'
                        break
                    else:
                        record.plastic_limit_conformity = 'fail'

    plastic_limit_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="Plastic Limit NABL", compute="_compute_plasticity_limi_nabl", store=True)

    @api.depends('plastic_limit','eln_ref','grade')
    def _compute_plasticity_limi_nabl(self):
        
        for record in self:
            record.plastic_limit_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','120vbf14-2ff0-4b81-aca1-0e07dab7cd87')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','120vbf14-2ff0-4b81-aca1-0e07dab7cd87')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.plastic_limit - record.plastic_limit*mu_value
            upper = record.plastic_limit + record.plastic_limit*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.plastic_limit_nabl = 'pass'
                break
            else:
                record.plastic_limit_nabl = 'fail'

    # Plasticity Index
    plasticity_index = fields.Float(string="Plasticity Index (PI)",compute="_compute_pi",store=True)

    @api.depends('liquid_limit', 'plastic_limit')
    def _compute_pi(self):
     for rec in self:
        rec.plasticity_index = rec.liquid_limit - rec.plastic_limit

    
    plasticity_index_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Plasticity Index Conformity", compute="_compute_plasticity_index_conformity", store=True)

    @api.depends('plasticity_index','eln_ref','grade')
    def _compute_plasticity_index_conformity(self):
        
        for record in self:
            record.plasticity_index_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1045789654-2ff0-4b81-aca1-0e07dab7cd87')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1045789654-2ff0-4b81-aca1-0e07dab7cd87')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.plasticity_index - record.plasticity_index*mu_value
                    upper = record.plasticity_index + record.plasticity_index*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.plasticity_index_conformity = 'pass'
                        break
                    else:
                        record.plasticity_index_conformity = 'fail'

    plasticity_index_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="Plasticity Index NABL", compute="_compute_plasticity_index_nabl", store=True)

    @api.depends('plasticity_index','eln_ref','grade')
    def _compute_plasticity_index_nabl(self):
        
        for record in self:
            record.plasticity_index_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1045789654-2ff0-4b81-aca1-0e07dab7cd87')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1045789654-2ff0-4b81-aca1-0e07dab7cd87')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.plasticity_index - record.plasticity_index*mu_value
            upper = record.plasticity_index + record.plasticity_index*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.plasticity_index_nabl = 'pass'
                break
            else:
                record.plasticity_index_nabl = 'fail'



    # Free Swell Index

    fsi_name = fields.Char("Name",default="Free Swell Index")
    fsi_visible = fields.Boolean("Free Swell Index Visible",compute="_compute_visible")

    free_swell_ids = fields.One2many('free.swell.line', 'parent_id')

    avg_fsi = fields.Float(
        string="Average Free Swell Index (%)",
        compute="_compute_avg_fsi",
        store=True
    )

    @api.onchange('free_swell_ids')
    def _onchange_free_swell_ids(self):
     for rec in self:
        for index, line in enumerate(rec.free_swell_ids):
            line.serial_no = index + 1

    @api.depends('free_swell_ids.free_swell_index')
    def _compute_avg_fsi(self):
        for rec in self:
            values = rec.free_swell_ids.mapped('free_swell_index')
            if values:
                rec.avg_fsi = sum(values) / len(values)
            else:
                rec.avg_fsi = 0.0

    avg_fsi_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_fsi_conformity", store=True)

    @api.depends('avg_fsi','eln_ref','grade')
    def _compute_avg_fsi_conformity(self):
        
        for record in self:
            record.avg_fsi_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ght4125-ca64-44dd-b0ae-228aacf04998')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ght4125-ca64-44dd-b0ae-228aacf04998')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_fsi - record.avg_fsi*mu_value
                    upper = record.avg_fsi + record.avg_fsi*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_fsi_conformity = 'pass'
                        break
                    else:
                        record.avg_fsi_conformity = 'fail'

    avg_fsi_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_fsi_nabl", store=True)

    @api.depends('avg_fsi','eln_ref','grade')
    def _compute_avg_fsi_nabl(self):
        
        for record in self:
            record.avg_fsi_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ght4125-ca64-44dd-b0ae-228aacf04998')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ght4125-ca64-44dd-b0ae-228aacf04998')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_fsi - record.avg_fsi*mu_value
            upper = record.avg_fsi + record.avg_fsi*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_fsi_nabl = 'pass'
                break
            else:
                record.avg_fsi_nabl = 'fail'


    # Light Compaction Test

    light_comp_name = fields.Char("Name",default="Light Compaction Test ")
    light_comp_visible = fields.Boolean("Light Compaction Test",compute="_compute_visible")


    
    mould_weight = fields.Float(string="Weight of Mould (gm)")
    mould_volume = fields.Float(string="Volume of Mould (cc)")

    G = fields.Float(string="Specific Gravity",digits=(10,3))
    gamma_w = fields.Float(string="ρw Unit Weight of Water",digits=(10,0))

    light_line_ids = fields.One2many('light.compaction.test.line', 'parent_id', string="Observations")

    @api.onchange('light_line_ids')
    def _onchange_light_line_ids(self):
     for rec in self:
        for index, line in enumerate(rec.light_line_ids):
            line.serial_no = index + 1

    light_graph_image = fields.Binary("Graph", readonly=True)

    def action_generate_graph1(self):
        for rec in self:

            x = []
            y = []

            # Collect data
            for line in rec.light_line_ids:
                if line.water_content and line.dry_density:
                    x.append(line.water_content)
                    y.append(line.dry_density)

            if len(x) < 4:
                continue

            # Sort
            data = sorted(zip(x, y))
            x, y = zip(*data)

            x = np.array(x)
            y = np.array(y)

            # ✅ Parabolic fit
            z = np.polyfit(x, y, 2)
            p = np.poly1d(z)

            # 🔥 FILTER POINTS CLOSE TO CURVE
            threshold = 0.01  # tolerance (adjust if needed)

            x_filtered = []
            y_filtered = []

            for xi, yi in zip(x, y):
                y_fit = p(xi)
                if abs(yi - y_fit) <= threshold:
                    x_filtered.append(xi)
                    y_filtered.append(yi)

            x_filtered = np.array(x_filtered)
            y_filtered = np.array(y_filtered)

            # Smooth curve
            x_smooth = np.linspace(min(x), max(x), 200)
            y_smooth = p(x_smooth)

            # Peak
            max_idx = np.argmax(y_smooth)
            max_x = x_smooth[max_idx]
            max_y = y_smooth[max_idx]

            # Plot
            plt.figure(figsize=(10, 5))

            plt.plot(x_smooth, y_smooth, linewidth=2)

            # ✅ ONLY GOOD POINTS
            plt.scatter(x_filtered, y_filtered, color='blue', zorder=3)

            plt.xlabel('Moisture Content (%)')
            plt.ylabel('Dry Density (g/cc)')
            plt.title('Light Compaction Test')

            # Lines
            plt.axvline(max_x, color='black', linewidth=2)
            plt.axhline(max_y, color='black', linewidth=2)

            plt.scatter(max_x, max_y, color='orange', zorder=4)

            # Grid
            ax = plt.gca()
            ax.xaxis.set_minor_locator(MultipleLocator(0.5))
            ax.yaxis.set_minor_locator(MultipleLocator(0.01))
            plt.grid(True, which='both', linestyle='--', linewidth=0.3)

            plt.xlim(0, max(x) + 2)
            plt.ylim(min(y) - 0.05, max(y) + 0.05)

            plt.text(
                max_x + 0.2,
                max_y,
                f"OMC: {max_x:.2f}%\nMDD: {max_y:.3f}",
                fontsize=10
            )

            plt.tight_layout()

            # Save
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            plt.close()
            buffer.seek(0)

            rec.light_graph_image = base64.b64encode(buffer.read())



    light1_graph_image = fields.Binary("Graph", readonly=True)

    def action_generate_light1_graph_image(self):
        for rec in self:

            x = []
            y = []

            # Collect ALL points
            for line in rec.light_line_ids:
                if line.water_content and line.dry_density:
                    x.append(line.water_content)
                    y.append(line.dry_density)

            if len(x) < 3:
                continue

            # Sort data
            data = sorted(zip(x, y))
            x, y = zip(*data)

            x = np.array(x, dtype=float)
            y = np.array(y, dtype=float)

            # 🔥 Interpolation
            interp = PchipInterpolator(x, y)

            x_smooth = np.linspace(min(x), max(x), 300)
            y_smooth = interp(x_smooth)

            # 🔥 Global smoothing
            y_smooth = gaussian_filter1d(y_smooth, sigma=1.2)

            # 🔥 FIX FIRST SEGMENT (remove kink)
            if len(x) > 1:
                x1, x2 = x[0], x[1]

                mask = (x_smooth >= x1) & (x_smooth <= x2)

                y_start = y[0]
                y_end = y[1]

                t = (x_smooth[mask] - x1) / (x2 - x1)

                # Smooth cubic transition
                y_smooth[mask] = y_start + (y_end - y_start) * (3*t**2 - 2*t**3)

            # 📊 Plot
            plt.figure(figsize=(10, 4))

            plt.plot(x_smooth, y_smooth, linewidth=2)
            plt.scatter(x, y, s=45, zorder=5)

            plt.xlabel('Optimum Moisture Content (%)')
            plt.ylabel('Maximum Dry Density (gm/cc)')
            plt.title('Light Compaction Test')

            plt.grid(True, linestyle='-', linewidth=0.5, alpha=0.3)

            plt.xlim(0, max(x) + 2)
            plt.ylim(0, max(y) + 0.2)

            plt.tight_layout()

            # Save image
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            plt.close()
            buffer.seek(0)

            rec.light1_graph_image = base64.b64encode(buffer.read())


    # Heavy Compaction Test

    heavy_name = fields.Char("Name",default="DETERMINATION OF MDD & OMC BY PROCTOR TEST ")
    heavy_visible = fields.Boolean("Heavy Compaction-MDD Visible",compute="_compute_visible")


    heavy_mould_weight = fields.Float(string="Weight of Mould (w1)", required=True)
    heavy_mould_volume = fields.Float(string="Volume of Mould in cc (V)", required=True)

    heavy_line_ids = fields.One2many('heavy.compaction.test.line', 'parent_id', string="Trials")

    max_dry_density = fields.Float(string="Maximum Dry Density", compute="_compute_mdd")
    optimum_moisture = fields.Float(string="Optimum Moisture Content", compute="_compute_mdd")


    @api.depends('heavy_line_ids.dry_density', 'heavy_line_ids.water_content')
    def _compute_mdd(self):
     for rec in self:
        x = []
        y = []

        for line in rec.heavy_line_ids:
            if line.water_content and line.dry_density:
                x.append(line.water_content)
                y.append(line.dry_density)

        if len(x) < 3:
            rec.max_dry_density = 0
            rec.optimum_moisture = 0
            continue

        x = np.array(x)
        y = np.array(y)

        # Fit parabola
        coeffs = np.polyfit(x, y, 2)
        a, b, c = coeffs

        # Peak of parabola
        if a != 0:
            omc = -b / (2 * a)
            mdd = a * omc**2 + b * omc + c
        else:
            omc = 0
            mdd = max(y)

        rec.optimum_moisture = round(omc, 2)
        rec.max_dry_density = round(mdd, 3)


    heavy_graph_image = fields.Binary("Graph", attachment=True)

    def action_generate_heavy_graph(self):
        for rec in self:
            x_value = []
            y_value = []

            # Collect data
            for line in rec.heavy_line_ids:
                if line.water_content and line.dry_density:
                    x_value.append(line.water_content)
                    y_value.append(line.dry_density)

            if len(x_value) < 3:
                continue  # Need at least 3 points

            x = np.array(x_value)
            y = np.array(y_value)

            

            # Sort data
            sorted_indices = np.argsort(x)
            x = x[sorted_indices]
            y = y[sorted_indices]

            # ✅ Spline interpolation (passes through all points)
            x_smooth = np.linspace(x.min(), x.max(), 80)
            spline = make_interp_spline(x, y, k=2)
            y_smooth = spline(x_smooth)

            # ✅ Find peak (OMC & MDD)
            # max_y = float(np.max(y_smooth))
            # max_x = float(x_smooth[np.argmax(y_smooth)])

            max_y = float(np.max(y))
            max_x = float(x[np.argmax(y)])

            # Plot graph
            plt.figure(figsize=(10, 6))

            # Points
            plt.scatter(x, y)

            # Smooth curve
            plt.plot(x_smooth, y_smooth)

            # Peak lines
            plt.axvline(x=max_x)
            plt.axhline(y=max_y)

            # Highlight peak point
            plt.scatter([max_x], [max_y])

            # Labels
            plt.title("Modified Proctor Test")
            plt.xlabel("Optimum Moisture Content (%)")
            plt.ylabel("Maximum Dry Density (gm/cc)")
            plt.grid(True)

            # Optional: show values on graph
            plt.text(max_x, max_y,
                     f"OMC={round(max_x,2)}%\nMDD={round(max_y,3)}",
                     ha='left')

            # Save image
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plt.close()
            buf.seek(0)

            rec.heavy_graph_image = base64.b64encode(buf.read())


    # California Bearing Test (CBR)
    cbr_name = fields.Char("Name",default="California Bearing Ratio")
    cbr_visible = fields.Boolean("California Bearing Ratio Visible",compute="_compute_visible")


    cbr_line_ids = fields.One2many('california.bearing.test','parent_id',string="CBR",default=lambda self: self._default_cbr_line_ids())

    plunger_area = fields.Float(string="Plunger Area",digits=(10,3),default=19.625)
    div_load = fields.Float(string="1 division Load",digits=(10,3),default=1.246)

    cbr_25_s1 = fields.Float("2.5mm", compute="_compute_cbr", store=True)
    cbr_25_s2 = fields.Float("2.5mm", compute="_compute_cbr", store=True)
    cbr_25_s3 = fields.Float("2.5mm ", compute="_compute_cbr", store=True)

    cbr_5_s1 = fields.Float("5mm", compute="_compute_cbr", store=True)
    cbr_5_s2 = fields.Float("5mm", compute="_compute_cbr", store=True)
    cbr_5_s3 = fields.Float("5mm", compute="_compute_cbr", store=True)

    cbr_25_avg = fields.Float("2.5mm", compute="_compute_cbr", store=True)
    cbr_5_avg = fields.Float("5mm", compute="_compute_cbr", store=True)

    cbr_max = fields.Float("CBR Max", compute="_compute_cbr", store=True)


    @api.depends('cbr_line_ids.sample1_load',
             'cbr_line_ids.sample2_load',
             'cbr_line_ids.sample3_load',
             'cbr_line_ids.penetration')
    def _compute_cbr(self):
     for rec in self:
        lines = rec.cbr_line_ids

        # Get 2.5 mm & 5 mm rows
        line_25 = lines.filtered(lambda l: l.penetration == 2.5)
        line_5 = lines.filtered(lambda l: l.penetration == 5.0)

        # Default values
        rec.cbr_25_s1 = rec.cbr_25_s2 = rec.cbr_25_s3 = 0.0
        rec.cbr_5_s1 = rec.cbr_5_s2 = rec.cbr_5_s3 = 0.0

        # -------- 2.5 mm --------
        if line_25:
            l = line_25[0]
            rec.cbr_25_s1 = l.sample1_load / 0.7 if l.sample1_load else 0
            rec.cbr_25_s2 = l.sample2_load / 0.7 if l.sample2_load else 0
            rec.cbr_25_s3 = l.sample3_load / 0.7 if l.sample3_load else 0

        # -------- 5 mm --------
        if line_5:
            l = line_5[0]
            rec.cbr_5_s1 = l.sample1_load / 1.05 if l.sample1_load else 0
            rec.cbr_5_s2 = l.sample2_load / 1.05 if l.sample2_load else 0
            rec.cbr_5_s3 = l.sample3_load / 1.05 if l.sample3_load else 0

        # -------- AVERAGE --------
        rec.cbr_25_avg = (rec.cbr_25_s1 + rec.cbr_25_s2 + rec.cbr_25_s3) / 3
        rec.cbr_5_avg = (rec.cbr_5_s1 + rec.cbr_5_s2 + rec.cbr_5_s3) / 3

        # -------- MAX --------
        rec.cbr_max = max(rec.cbr_25_avg, rec.cbr_5_avg)


    @api.model
    def _default_cbr_line_ids(self):
        default_lines = [
            (0, 0, {'penetration': '0.00','sample1_reading' : '0.00','sample1_load' : '0.00','sample2_reading' : '0.00','sample2_load' : '0.00','sample3_reading' : '0.00','sample3_load' : '0.00'}),
            (0, 0, {'penetration': '0.50'}),
            (0, 0, {'penetration': '1.0'}),
            (0, 0, {'penetration': '1.50'}),
            (0, 0, {'penetration': '2.00'}),
            (0, 0, {'penetration': '2.50'}),
            (0, 0, {'penetration': ' 3.00'}),
            (0, 0, {'penetration': '4.00'}),
            (0, 0, {'penetration': '5.00'}),
            (0, 0, {'penetration': '7.50'}),
            (0, 0, {'penetration': '10.00'}),
            (0, 0, {'penetration': '12.50'})
        ]
        return default_lines
    
    cbr_chart_image = fields.Binary("CBR Chart", readonly=True)
    cbr_chart_filename = fields.Char("Filename")


    def action_generate_cbr_chart(self):
     for rec in self:
        lines = self.env['california.bearing.test'].search([
            ('parent_id', '=', rec.id)
        ], order='penetration asc')

        penetration = [l.penetration for l in lines]

        s1 = [l.sample1_load for l in lines]
        s2 = [l.sample2_load for l in lines]
        s3 = [l.sample3_load for l in lines]

        # ✅ Increase width only (width=12, height=5)
        plt.figure(figsize=(12, 5))

        plt.plot(penetration, s1, marker='o', label='Sample-1')
        plt.plot(penetration, s2, marker='o', label='Sample-2')
        plt.plot(penetration, s3, marker='o', label='Sample-3')

        plt.xlabel('Penetration (mm)')
        plt.ylabel('Load (Kg/cm²)')
        plt.title('CBR Test Graph')

        # ✅ Major grid (big squares)
        plt.grid(which='major', linestyle='-', linewidth=0.8)

        # ✅ Minor grid (small squares inside)
        ax = plt.gca()
        ax.xaxis.set_minor_locator(AutoMinorLocator(5))
        ax.yaxis.set_minor_locator(AutoMinorLocator(5))
        plt.grid(which='minor', linestyle=':', linewidth=0.5)

        plt.legend()

        # Save image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close()

        image = base64.b64encode(buffer.getvalue())
        buffer.close()

        rec.cbr_chart_image = image
        rec.cbr_chart_filename = "cbr_chart.png"

    
    # Consolidation Test
    consolidation_name = fields.Char("Name",default="Consolidation Test")
    consolidation_visible = fields.Boolean("Consolidation Test Visible",compute="_compute_visible")


    consolidation_line_ids = fields.One2many('mechanical.consolidation.test.line', 'parent_id', string="Test Lines",default=lambda self: self._default_consolidation_line_ids())

    @api.model
    def _default_consolidation_line_ids(self):
        default_lines = [
            (0, 0, {'time_interval': '0 sec'}),
            (0, 0, {'time_interval': '15 sec'}),
            (0, 0, {'time_interval': '30 sec'}),
            (0, 0, {'time_interval': '1 minutes'}),
            (0, 0, {'time_interval': '2 minutes'}),
            (0, 0, {'time_interval': '4 minutes'}),
            (0, 0, {'time_interval': '8 minutes'}),
            (0, 0, {'time_interval': '15 minutes'}),
            (0, 0, {'time_interval': '30 minutes'}),
            (0, 0, {'time_interval': '60 minutes'}),
            (0, 0, {'time_interval': '2 hours'}),
            (0, 0, {'time_interval': '4 hours'}),
            (0, 0, {'time_interval': '8 hours'}),
            (0, 0, {'time_interval': '24 hours'}),
        ]
        return default_lines
    
    mass_dry_soil_con = fields.Float("Mass of Dry Soil")
    area_con = fields.Float("Cross Section Area of Ring")
    height_con = fields.Float("Height of Solids, Hs")
    height_ini = fields.Float("Height")

    consolidation_two_line_ids = fields.One2many('mechanical.consolidation.two.test.line', 'parent_id', string="Test Lines",default=lambda self: self.default_consolidation_two_line_ids())

    @api.model
    def default_consolidation_two_line_ids(self):
      default_lines = [
        (0, 0, {'stage': '', 'pressure': 0.0,}),
        (0, 0, {'stage': 'Loading', 'pressure': 0.1,}),
        (0, 0, {'stage': 'Loading', 'pressure': 0.2,}),
        (0, 0, {'stage': 'Loading', 'pressure': 0.4, }),
        (0, 0, {'stage': 'Loading', 'pressure': 1,}),
        (0, 0, {'stage': 'Loading', 'pressure': 2,}),
        (0, 0, {'stage': 'Loading', 'pressure': 4,}),
        (0, 0, {'stage': 'Loading', 'pressure': 8,}),
        (0, 0, {'stage': 'Unloading', 'pressure': 4,}),
        (0, 0, {'stage': 'Unloading', 'pressure': 2,}),
        (0, 0, {'stage': 'Unloading', 'pressure': 1,}),
        (0, 0, {'stage': 'Unloading', 'pressure': 0.4,}),
        (0, 0, {'stage': 'Unloading', 'pressure': 0.2,}),
        (0, 0, {'stage': 'Unloading', 'pressure': 0.1,}),
    ]
      return default_lines
    
    consolidation_three_line_ids = fields.One2many('mechanical.consolidation.three.test.line', 'parent_id', string="Test Lines",default=lambda self: self.default_consolidation_three_line_ids())

    @api.model
    def default_consolidation_three_line_ids(self):
      default_lines = [
        (0, 0, {'time_min': '0', }),
        (0, 0, {'time_min': '0.25', }),
        (0, 0, {'time_min': '0.5', }),
        (0, 0, {'time_min': '1', }),
        (0, 0, {'time_min': '2', }),
        (0, 0, {'time_min': '4', }),
        (0, 0, {'time_min': '5', }),
        (0, 0, {'time_min': '15', }),
        (0, 0, {'time_min': '30', }),
        (0, 0, {'time_min': '60', }),
        (0, 0, {'time_min': '120', }),
        (0, 0, {'time_min': '240', }),
        (0, 0, {'time_min': '480', }),
        (0, 0, {'time_min': '1440', }),
    ]
      return default_lines
    
    con_graph_image = fields.Binary("Graph", readonly=True)

    def action_generate_graph(self):
        for rec in self:

            x_vals = []
            y_vals = []

            # Collect data
            for line in rec.consolidation_three_line_ids:
                if line.sqrt_t and line.int_pressure:
                    x_vals.append(line.sqrt_t)
                    y_vals.append(line.int_pressure)

            if not x_vals:
                return

            # ✅ REMOVE ZERO VALUES (important for proper graph)
            filtered = [(x, y) for x, y in zip(x_vals, y_vals) if x > 0]
            if not filtered:
                return

            x_vals, y_vals = zip(*filtered)

            # ✅ CREATE WIDE GRAPH
            plt.figure(figsize=(11, 5))

            plt.plot(x_vals, y_vals, marker='o')

            # Labels
            plt.xlabel("√t")
            plt.ylabel("Dial Reading (8 kg/cm²)")
            plt.title("Consolidation Graph")

            # ✅ USE LOG SCALE (like Excel)
            plt.xscale('log')

            # ✅ FIX LEFT SIDE GAP (main issue you had)
            min_x = min(x_vals)
            plt.xlim(left=min_x * 0.8)

            # ✅ GRID (Excel style)
            plt.grid(True, which='both', linestyle='--', linewidth=0.5)

            # Better layout
            plt.tight_layout()

            # Save image
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)

            rec.con_graph_image = base64.b64encode(buffer.read())

            plt.close()
    



    # Constant Head
    constant_head_name = fields.Char("Name",default="Constant Head")
    constant_head_visible = fields.Boolean("Constant Head Visible",compute="_compute_visible")


    constant_head_diameter = fields.Float("Diameter of Specimen (D),cm",digits=(10,3))
    constant_head_length = fields.Float("Length of Specimen (L),cm",digits=(10,3))
    constant_head_area = fields.Float("Cross Sectional Area (A),cm2", compute="_compute_constant_head_area", store=True,digits=(16,9))
    constant_head = fields.Float("Constant Head (h), cm",digits=(10,3))
    constant_head_temperature = fields.Float("Water Temperature (T), 0°C",digits=(10,3))
    constant_viscosity_t = fields.Float("Kinematic viscosity of Water (yt)",digits=(16,7))
    constant_viscosity_27 = fields.Float("Kinematic viscosity of Water 27°C",digits=(16,7))

    
    contant_line_ids = fields.One2many('constant.head.line', 'parent_id', string="Test Lines")

   
    constant_avg_k27 = fields.Float("Average K27", compute="_compute_avg", store=True,digits=(16,6))
    constant_avg_k27_1000 = fields.Float("Average K27 * 1000", compute="_compute_avg", store=True,digits=(16,3))

    @api.depends('constant_head_diameter')
    def _compute_constant_head_area(self):
        for rec in self:
            if rec.constant_head_diameter:
                rec.constant_head_area = round(3.14 * (rec.constant_head_diameter ** 2) / 4,3)
            else:
                rec.constant_head_area = 0.0

    @api.depends('contant_line_ids.k27')
    def _compute_avg(self):
     for rec in self:
        values = rec.contant_line_ids.mapped('k27')

        # Remove zero / False values (important ⚠️)
        values = [v for v in values if v]

        if values:
            avg = sum(values) / len(values)
        else:
            avg = 0.0

        rec.constant_avg_k27 = avg
        rec.constant_avg_k27_1000 = avg * 1000


    # Permeability Falling Head
    permeability_name = fields.Char("Name",default="Permeability Falling Head")
    permeability_visible = fields.Boolean("Permeability Falling Head Visible",compute="_compute_visible")


    permeability_diameter = fields.Float("Diameter of Specimen (D),cm",digits=(10,3))
    permeability_length = fields.Float("Length of Specimen (L),cm",digits=(10,3))
    permeability_area = fields.Float("Cross Sectional Area (A),cm2",digits=(10,3))
    permeability_constant_head = fields.Float("Constant Head (h), cm",digits=(10,3))

    permeability_stand = fields.Float("Dia of Stand Pipe (d) cm",digits=(10,3))

    permeability_standarea = fields.Float("Area of stand Pipe (a) cm2",compute="_compute_permeability_area", store=True,digits=(18,15))

    permeability_temperature = fields.Float("Water Temperature (T), 0°C",digits=(10,3))
    permeability_viscosity_t = fields.Float("Density of Water (yt)",digits=(16,7))
    permeability_viscosity_27 = fields.Float("Density of Water 27°C",digits=(16,7))

    # Lines
    permeability_line_ids = fields.One2many('permeability.head.line', 'parent_id', string="Test Lines")

    permeability_avg_k27 = fields.Float("Avg K27", compute="_compute_pavg", store=True, digits=(16,6))
    permeability_avg_k27_1000 = fields.Float("K27 x 1000", compute="_compute_pavg", store=True, digits=(16,6))


    @api.depends('permeability_stand')
    def _compute_permeability_area(self):
     for rec in self:
        if rec.permeability_stand:
            d = Decimal(str(rec.permeability_stand))
            area = (Decimal(str(math.pi)) * d * d) / Decimal('4')
            rec.permeability_standarea = float(area.quantize(Decimal('0.0000000001')))
        else:
            rec.permeability_standarea = 0.0
            

                

    @api.depends('permeability_line_ids.k27')
    def _compute_pavg(self):
     for rec in self:
        values = rec.permeability_line_ids.mapped('k27')

        # Remove zero / False values (important ⚠️)
        values = [v for v in values if v]

        if values:
            avg = sum(values) / len(values)
        else:
            avg = 0.0

        rec.permeability_avg_k27 = avg
        rec.permeability_avg_k27_1000 = avg * 1000



    # Sand Replacement Test

    sand_replace_name = fields.Char("Name",default="Sand Replacement")
    sand_replace_visible = fields.Boolean("Sand Replacement Visible",compute="_compute_visible")


    sand_line_ids = fields.One2many(
        'sand.replacement.line',
        'parent_id',
        string="Determination of Density"
    )



    # Core Cutter Test

    core_cutter_name = fields.Char("Name",default="Core Cutter Test")
    core_cutter_visible = fields.Boolean("Core Cutter Test Visible",compute="_compute_visible")

    core_cutter_line_ids = fields.One2many('core.cutter.line', 'parent_id', string="Determinations")

    avg_compaction = fields.Float(string="Average Compaction (%)", compute="_compute_avg_compaction")

    @api.depends('core_cutter_line_ids.compaction')
    def _compute_avg_compaction(self):
        for rec in self:
            values = rec.core_cutter_line_ids.mapped('compaction')
            rec.avg_compaction = sum(values) / len(values) if values else 0






    

    





    
   

     ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
      
        for record in self:
            record.sieve_visible = False
            record.texture_visible = False
            record.moisture_content_visible = False
            record.specific_gravity_visible = False
            record.fsi_visible = False
            record.liquid_limit_visible = False
            record.plastic_limit_visible = False
            record.light_comp_visible = False
            record.heavy_visible = False
            record.cbr_visible = False
            record.constant_head_visible = False
            record.permeability_visible = False
            record.sand_replace_visible = False
            record.core_cutter_visible = False
            record.consolidation_visible  = False
            
            


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                
                if sample.internal_id == '12014fgr-5c56-475b-9a89-93a59c9ee3a2':
                    record.sieve_visible = True

                if sample.internal_id == 'f7b5664a-b81a-4443-b797-b345fd57b9d8':
                    record.texture_visible = True


                if sample.internal_id == '800a2dc9-49fe-4dab-83e8-63758c7f351a':
                    record.moisture_content_visible = True

                if sample.internal_id == '214hhj6gt21-ca64-44dd-b0ae-6587gghty':
                    record.specific_gravity_visible = True

                if sample.internal_id == 'ght4125-ca64-44dd-b0ae-228aacf04998':
                    record.fsi_visible = True

                if sample.internal_id == '23fg21gh-7202-4d62-864b-8efa58b6b61f':
                    record.liquid_limit_visible = True

                if sample.internal_id == '120vbf14-2ff0-4b81-aca1-0e07dab7cd87':
                    record.plastic_limit_visible = True

                if sample.internal_id == '3210vbf-20fb-4843-aa0e-142578bgtyu':
                    record.light_comp_visible = True

                if sample.internal_id == '3210vbf-20fb-4843-aa0e-2ee981be0d7c':
                    record.heavy_visible = True

                if sample.internal_id == '15247gtr-2065-4532-814a-3a4c1e884305':
                    record.cbr_visible = True

                if sample.internal_id == '78957888hhhllly1-ca64-44dd-b0ae-2314780ty':
                    record.consolidation_visible = True

                if sample.internal_id == 'b2a605ac-6eb0-4101-a020-0b6b3f6304db':
                    record.constant_head_visible = True

                if sample.internal_id == '5487gt21-ca64-44dd-b0ae-228aacf04965':
                    record.permeability_visible = True

                if sample.internal_id == 'a4e6c3fa-e760-425a-a09f-e66cb6bb4c52':
                    record.sand_replace_visible = True

                if sample.internal_id == '183134ba-9616-467f-acb9-af738740d86e':
                    record.core_cutter_visible = True

                

                    
                
                

    
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:


            # Sieve Analysis
            if result.parameter.internal_id == '12014fgr-5c56-475b-9a89-93a59c9ee3a2':
                result.calculated = True

                # Sieve Analysis
            if result.parameter.internal_id == 'f7b5664a-b81a-4443-b797-b345fd57b9d8':
                result.calculated = True
                
            # Consolidation Test
            if result.parameter.internal_id == '78957888hhhllly1-ca64-44dd-b0ae-2314780ty':
                result.calculated = True

        
            # Moisture Content
            if result.parameter.internal_id == '800a2dc9-49fe-4dab-83e8-63758c7f351a':
                result.calculated = True
                result.result_char = round(self.avg_moisture_content,2)
                if self.avg_moisture_content_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Specific Gravity
            if result.parameter.internal_id == '214hhj6gt21-ca64-44dd-b0ae-6587gghty':
                result.calculated = True
                result.result_char = round(self.avg_specific_gravity,3)
                if self.avg_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Liquid Limit
            if result.parameter.internal_id == '23fg21gh-7202-4d62-864b-8efa58b6b61f':
                result.calculated = True
                result.result_char = round(self.liquid_limit,2)
                if self.liquid_limit_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Plastic Limit
            if result.parameter.internal_id == '120vbf14-2ff0-4b81-aca1-0e07dab7cd87':
                result.calculated = True
                result.result_char = round(self.plastic_limit,2)
                if self.plastic_limit_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Plasticity Index
            if result.parameter.internal_id == '1045789654-2ff0-4b81-aca1-0e07dab7cd87':
                result.calculated = True
                result.result_char = round(self.plasticity_index,2)
                if self.plasticity_index_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Free Swell Index
            if result.parameter.internal_id == 'ght4125-ca64-44dd-b0ae-228aacf04998':
                result.calculated = True
                result.result_char = round(self.avg_fsi,2)
                if self.avg_fsi_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Light Compaction Test
            if result.parameter.internal_id == '3210vbf-20fb-4843-aa0e-142578bgtyu':
                result.calculated = True

            # Heavy Compaction
            if result.parameter.internal_id == '3210vbf-20fb-4843-aa0e-2ee981be0d7c':
                result.calculated = True

            # California Bearing Test
            if result.parameter.internal_id == '15247gtr-2065-4532-814a-3a4c1e884305':
                result.calculated = True

            # Constant Head
            if result.parameter.internal_id == 'b2a605ac-6eb0-4101-a020-0b6b3f6304db':
                result.calculated = True

            # Permeability Falling Head
            if result.parameter.internal_id == '5487gt21-ca64-44dd-b0ae-228aacf04965':
                result.calculated = True

            # Sand Replacement
            if result.parameter.internal_id == 'a4e6c3fa-e760-425a-a09f-e66cb6bb4c52':
                result.calculated = True

            # Core Cutter Test
            if result.parameter.internal_id == '183134ba-9616-467f-acb9-af738740d86e':
                result.calculated = True
            
            


            
            

        return {
                'view_mode': 'form',
                'res_model': "lerm.eln",
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.eln_ref.id,
                
            }
            
    

    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(Soil, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     # records = self.env['lerm.eln'].sudo().search([('id','=', record.eln_id.id)]).parameters_result
    #     # print("records",records)
    #     # self.sample_parameters = records
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    def _compute_sample_parameters(self):
        # parameter_based_assignment
        current_user = self.env.user
        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            # filter parameter results by current user
            user_param_results = record.eln_ref.parameters_result.filtered(
                lambda r: r.technician and r.technician.id == current_user.id
            )

            # map to parameter master IDs
            parameter_ids = user_param_results.mapped('parameter').ids

            record.sample_parameters = [(6, 0, parameter_ids)]



    def get_all_fields(self):
        record = self.env['mechanical.soil1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


class SoilSieveAnalysisLine(models.Model):
    _name = "mechanical.soil.sieve.analysis.line"
    parent_id = fields.Many2one('mechanical.soil1', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size")
    particle_size = fields.Char(string="Particle Size  (mm)")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained")
    cumulative_retained = fields.Float(string="Cum. Retained %",compute="_compute_cum_retained" , store=True)
    passing_percent = fields.Float(string="Cumulative % ")

    # @api.onchange('cumulative_retained')
    # def _compute_passing_percent(self):
    #     for record in self:
    #         record.passing_percent = 100 - record.cumulative_retained


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SoilSieveAnalysisLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

    def write(self, vals):
        # Handle row deletions and adjust serial numbers
        if 'parent_id' in vals or 'wt_retained' in vals:
            for record in self:
                if record.parent_id and record.parent_id == vals.get('parent_id') and 'wt_retained' in vals:
                    record.percent_retained = vals['wt_retained'] / record.parent_id.total * 100 if record.parent_id.total else 0

            new_self = super(SoilSieveAnalysisLine, self).write(vals)

            if 'wt_retained' in vals:
                for record in self:
                    # record.parent_id._compute_total()
                    pass

            return new_self

        return super(SoilSieveAnalysisLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(SoilSieveAnalysisLine, self).unlink()

        if parent_id:
            parent_id.sieve_analysis_child_lines._reorder_serial_numbers()

        return res


    @api.depends('wt_retained', 'parent_id.wt_of_sample')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = (record.wt_retained / record.parent_id.wt_of_sample) * 100 if record.parent_id.wt_of_sample else 0.0
            except ZeroDivisionError:
                record.percent_retained = 0.0



    # @api.depends('cumulative_retained')
    # def _compute_cum_retained(self):
    #     self.cumulative_retained=0

    @api.depends('percent_retained', 'parent_id.sieve_analysis_child_lines.percent_retained')
    def _compute_cum_retained(self):
        for record in self:
            cumulative = 0.0
            found = False

            for line in sorted(record.parent_id.sieve_analysis_child_lines, key=lambda l: l.serial_no):
                cumulative += line.percent_retained or 0.0
                if line.id == record.id:
                    found = True
                    record.cumulative_retained = cumulative
                    break

            if not found:
                record.cumulative_retained = 0.0

        
    


    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines, key=lambda r: r.id)
            # index = sorted_lines.index(record)
            # print("Working")


class TextureSoilLine(models.Model):
    _name = "texture.soil.line"
    parent_id = fields.Many2one('mechanical.soil1',string = "Parent Id")

    serial_no = fields.Integer(string="Sr No", readonly=True,store=True,default=1)

    sample = fields.Char("Sample")

    total_depth = fields.Float("Total Depth")
    sand_depth = fields.Float("Sand Depth")
    silt_depth = fields.Float("Silt Depth")
    clay_depth = fields.Float("Clay Depth")

    percent_sand = fields.Float(compute="_compute_percentages", store=True)
    percent_silt = fields.Float(compute="_compute_percentages", store=True)
    percent_clay = fields.Float(compute="_compute_percentages", store=True)


    @api.depends('total_depth', 'sand_depth', 'silt_depth', 'clay_depth')
    def _compute_percentages(self):
     for rec in self:
        if rec.total_depth:
            rec.percent_sand = (rec.sand_depth / rec.total_depth) * 100
            rec.percent_silt = (rec.silt_depth / rec.total_depth) * 100
            rec.percent_clay = (rec.clay_depth / rec.total_depth) * 100
        else:
            rec.percent_sand = 0.0
            rec.percent_silt = 0.0
            rec.percent_clay = 0.0

    soil_type = fields.Char(compute="_compute_soil_type", store=True)

    @api.depends('percent_sand', 'percent_silt', 'percent_clay')
    def _compute_soil_type(self):
     for rec in self:
        if rec.percent_sand > 60:
            rec.soil_type = 'Sandy'
        elif rec.percent_clay > 40:
            rec.soil_type = 'Clayey'
        elif rec.percent_silt > 40:
            rec.soil_type = 'Silty'
        else:
            rec.soil_type = 'Loamy'
    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(TextureSoilLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class SandEquivalentLine(models.Model):
    _name = "sand.equivalent.line"
    parent_id = fields.Many2one('mechanical.soil1',string = "Parent Id")

    serial_no = fields.Integer(string="Sample No", readonly=True,store=True,default=1)

    sample_name = fields.Char("Sample")  # Sample-1, Sample-2, etc.

    sand_reading = fields.Float("Sand Reading")
    clay_reading = fields.Float("Clay Reading")

    sand_equivalent = fields.Float(
        "Sand Equivalent (%)",
        compute="_compute_sand_equivalent",
        store=True
    )

    @api.depends('sand_reading', 'clay_reading')
    def _compute_sand_equivalent(self):
        for rec in self:
            if rec.clay_reading:
                rec.sand_equivalent = (rec.sand_reading / rec.clay_reading) * 100
            else:
                rec.sand_equivalent = 0.0
    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SandEquivalentLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class MoistureContentLine(models.Model):
    _name = "moisture.content.line"
    parent_id = fields.Many2one('mechanical.soil1',string = "Parent Id")

    serial_no = fields.Integer(string="Sample No", readonly=True,store=True,default=1)
    wt_empty_con = fields.Float(string="Wt. of empty container W1 (gm)")
    wt_cont_wet_soil = fields.Float(string="Wt. of container + wet soil W2 (gm)")
    wt_cont_dry_soil = fields.Float(string="Wt. of container + dry soil W3 (gm)")
    wt_water = fields.Float(string="Wt. of water (gm) (W4 =(W2-W3)",computer="_compute_all",store=True)
    wt_dry_soil = fields.Float(string="Wt. of Dry soil (gm) (W5=(W3-W1)",computer="_compute_all",store=True)
    moisture_content = fields.Float(string="Moisture Content (%) (W4/W5*100)",computer="_compute_all",store=True)

   
    @api.onchange('wt_empty_con', 'wt_cont_wet_soil', 'wt_cont_dry_soil')
    def _onchange_compute(self):
     for line in self:
        wet = line.wt_cont_wet_soil or 0.0
        dry = line.wt_cont_dry_soil or 0.0
        empty = line.wt_empty_con or 0.0

        line.wt_water = wet - dry
        line.wt_dry_soil = dry - empty

        if line.wt_dry_soil:
            line.moisture_content = (line.wt_water / line.wt_dry_soil) * 100
        else:
            line.moisture_content = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(MoistureContentLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class SpecificGracityLine(models.Model):
    _name = "specific.gravity.line"
    parent_id = fields.Many2one('mechanical.soil1',string = "Parent Id")


    serial_no = fields.Integer(string="Sample No", readonly=True,store=True,default=1)
    w1 = fields.Float(string="Weight of empty, clean Density Bottle (gm) (W1)", digits=(12,2))
    w2 = fields.Float(string="Weight of empty Density Bottle + dry soil (gm) (W2)", digits=(12,2))
    w3 = fields.Float(string="Weight of Density Bottle + dry soil + water (gm) (W3)", digits=(12,2))
    w4 = fields.Float(string="Weight of Density Bottle + water (gm) (W4)", digits=(12,2))

    specific_gravity = fields.Float(string="Specific Gravity (G)" ,compute="_compute_specific_gravity", store=True, digits=(12,3))


    @api.depends("w1","w2","w3","w4")
    def _compute_specific_gravity(self):
        for rec in self:
            try:
                numerator = rec.w2 - rec.w1
                denominator = (rec.w4 - rec.w1) - (rec.w3 - rec.w2)
                if denominator != 0:
                    rec.specific_gravity = round(numerator / denominator, 3)
                else:
                    rec.specific_gravity = 0.0
            except Exception:
                rec.specific_gravity = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SpecificGracityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class WaterContentLine(models.Model):
    _name = "water.content.line"
    parent_id = fields.Many2one('mechanical.soil1', string="Parent Id")

    serial_no = fields.Integer(string="Sr.No", readonly=True,store=True,default=1)
    

    blows = fields.Integer(string="Number of Blows (N)")
    container_nos = fields.Integer(string="Container No")

    m1 = fields.Float(string="Mass of empty can (M1)")
    m2 = fields.Float(string="Mass of can + wet soil (M2)")
    m3 = fields.Float(string="Mass of can + dry soil (M3)")

    mass_water = fields.Float(
        string="Mass of Water (M2-M3)",
        compute="_compute_values",
        store=True
    )

    mass_dry_soil = fields.Float(
        string="Mass of Dry Soil (M3-M1)",
        compute="_compute_values",
        store=True
    )

    water_content = fields.Float(
        string="Water Content (%)",
        compute="_compute_values",
        store=True,
        digits=(16, 2)
    )

    @api.depends('m1', 'm2', 'm3')
    def _compute_values(self):
        for rec in self:
            rec.mass_water = rec.m2 - rec.m3
            rec.mass_dry_soil = rec.m3 - rec.m1

            if rec.mass_dry_soil:
                rec.water_content = (rec.mass_water / rec.mass_dry_soil) * 100
            else:
                rec.water_content = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(WaterContentLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class PlasticLimitLine(models.Model):
    _name = "plastic.limit.line"
    _description = "Plastic Limit Line"

    parent_id = fields.Many2one('mechanical.soil1', string="Parent Id")

    serial_no = fields.Integer(string="Sr.No", readonly=True,store=True,default=1)

    container_no = fields.Integer(string="Container No")

    m1 = fields.Float(string="Mass of empty container (M1)")
    m2 = fields.Float(string="Mass of container + wet soil (M2)")
    m3 = fields.Float(string="Mass of container + dry soil (M3)")

    mass_water = fields.Float(
        string="Mass of Water (M2-M3)",
        compute="_compute_values",
        store=True
    )

    mass_dry_soil = fields.Float(
        string="Mass of Dry Soil (M3-M1)",
        compute="_compute_values",
        store=True
    )

    water_content = fields.Float(
        string="Water Content (%)",
        compute="_compute_values",
        store=True,
        digits=(16, 2)
    )

    @api.depends('m1', 'm2', 'm3')
    def _compute_values(self):
        for rec in self:
            rec.mass_water = rec.m2 - rec.m3
            rec.mass_dry_soil = rec.m3 - rec.m1

            if rec.mass_dry_soil:
                rec.water_content = (rec.mass_water / rec.mass_dry_soil) * 100
            else:
                rec.water_content = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PlasticLimitLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1
            


class FreeSwellLine(models.Model):
    _name = "free.swell.line"
    _description = "Free Swell Index Line"

    parent_id = fields.Many2one('mechanical.soil1', string="Parent")

    serial_no = fields.Integer(string="Sample No",readonly=True,default=1)

    vk_initial = fields.Float(string="Kerosene (Vk)")
    vd_initial = fields.Float(string="Distilled Water (Vd)")

    vk_final = fields.Float(string="Kerosene After 24h")
    vd_final = fields.Float(string="Distilled Water After 24h")

    free_swell_index = fields.Float(
        string="Free Swell Index (%)",
        compute="_compute_fsi",
        store=True
    )

    @api.depends('vk_final', 'vd_final')
    def _compute_fsi(self):
        for rec in self:
            if rec.vk_final:
                rec.free_swell_index = ((rec.vd_final - rec.vk_final) / rec.vk_final) * 100
            else:
                rec.free_swell_index = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(FreeSwellLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class LightCompactionTestLine(models.Model):
    _name = 'light.compaction.test.line'
    _description = 'Compaction Test Line'

    parent_id = fields.Many2one('mechanical.soil1', string="Parent")

    serial_no = fields.Integer(string="Sample No",readonly=True,default=1)

   
    mass_mould = fields.Float(string="Mass of Empty Mould",compute="_compute_values", store=True)
    mass_total = fields.Float(string="Mass of mould, compacted soil and base plate")

  
    mass_soil = fields.Float(string="Mass of Compacted Soil", compute="_compute_values", store=True)
    wet_density = fields.Float(string="Wet Density", compute="_compute_values", store=True,digits=(10,3))

   
    w6 = fields.Float(string="Wt. of wet soil +cont.w6  (gm)")
    w7 = fields.Float(string="Wt. of dry soil +cont.w7  (gm)")
    w5 = fields.Float(string="Wt.of container, w5 (gm)")

    water = fields.Float(string="Weight of the Water", compute="_compute_values", store=True)
    dry_soil = fields.Float(string="Dry Soil Weight", compute="_compute_values", store=True)
    water_content = fields.Float(string="Water Content (%)", compute="_compute_values", store=True)

    dry_density = fields.Float(string="Dry Density", compute="_compute_values", store=True,digits=(10,3))


    @api.depends('mass_mould','parent_id.mould_weight', 'mass_total', 'w6', 'w7', 'w5', 'parent_id.mould_volume')
    def _compute_values(self):
        for rec in self:

            rec.mass_mould = rec.parent_id.mould_weight 


            # Mass of compacted soil
            rec.mass_soil = rec.mass_total - rec.mass_mould

            # Wet density
            if rec.parent_id.mould_volume:
                rec.wet_density = rec.mass_soil / rec.parent_id.mould_volume
            else:
                rec.wet_density = 0

            # Water weight
            rec.water = rec.w6 - rec.w7

            # Dry soil
            rec.dry_soil = rec.w7 - rec.w5

            # Water content %
            if rec.dry_soil != 0:
                rec.water_content = (rec.water / rec.dry_soil) * 100
            else:
                rec.water_content = 0

            # Dry density
            if rec.water_content:
                rec.dry_density = rec.wet_density / (1 + rec.water_content / 100)
            else:
                rec.dry_density = 0

    void_ratio = fields.Float(string="Void Ratio", compute="_compute_extra", store=True)
    dry_density_100 = fields.Float(string="Dry Density (100% Sat)", compute="_compute_extra", store=True ,digits=(12,5))
    degree_saturation = fields.Float(string="Degree of Saturation (%)", compute="_compute_extra", store=True)


    @api.depends('dry_density', 'water_content', 'parent_id.G', 'parent_id.gamma_w')
    def _compute_extra(self):
     for rec in self:
        G = rec.parent_id.G or 2.65
        gamma_w = rec.parent_id.gamma_w or 1
        

        w = rec.water_content if rec.water_content else 0
        w1 = rec.water_content/100 if rec.water_content else 0
        gamma_d = rec.dry_density

        # Void Ratio
        if gamma_d:
            rec.void_ratio = (G * gamma_w / gamma_d) - 1
        else:
            rec.void_ratio = 0

        # Dry Density at 100% Saturation
        if (1 + w * G) != 0:
            rec.dry_density_100 = (G * gamma_w) / (1 + w * G)
        else:
            rec.dry_density_100 = 0

        # Degree of Saturation
        if rec.void_ratio:
            rec.degree_saturation = (w1 * G / rec.void_ratio) * 100
        else:
            rec.degree_saturation = 0



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(LightCompactionTestLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class HeavyCompactionTestLine(models.Model):
    _name = 'heavy.compaction.test.line'
    _description = 'Heavy Compaction Test Line'

    parent_id = fields.Many2one('mechanical.soil1', string="Parent")

    serial_no = fields.Integer(string="Trial No",readonly=True,default=1)

    w2 = fields.Float(string="Wt of Wet Soil + Mould")
    w3 = fields.Float(string="Wt of Wet Soil (w3)", compute="_compute_w3", store=True)

    container_no = fields.Integer(string="Container No")
    w5 = fields.Float(string="Weight of Container (w5)")

    wet_density = fields.Float(string="Wet Density (γb)", compute="_compute_wet_density", store=True,digits=(10,3))

    w6 = fields.Float(string="Wet Soil + Container")
    w7 = fields.Float(string="Dry Soil + Container")

    w8 = fields.Float(string="Wt of Water", compute="_compute_water", store=True)
    w9 = fields.Float(string="Wt of Dry Soil", compute="_compute_water", store=True)

    water_content = fields.Float(string="Water Content (%)", compute="_compute_water_content", store=True)

    dry_density = fields.Float(string="Dry Density", compute="_compute_dry_density", store=True,digits=(10,3))


    @api.depends('w2', 'parent_id.heavy_mould_weight')
    def _compute_w3(self):
     for rec in self:
        rec.w3 = rec.w2 - rec.parent_id.heavy_mould_weight


    @api.depends('w3', 'parent_id.heavy_mould_volume')
    def _compute_wet_density(self):
     for rec in self:
        if rec.parent_id.heavy_mould_volume:
            rec.wet_density = rec.w3 / rec.parent_id.heavy_mould_volume
        else:
            rec.wet_density = 0.0


    @api.depends('w6', 'w7', 'w5')
    def _compute_water(self):
     for rec in self:
        rec.w8 = rec.w6 - rec.w7  # water
        rec.w9 = rec.w7 - rec.w5  # dry soil (corrected)


    @api.depends('w8', 'w9')
    def _compute_water_content(self):
     for rec in self:
        if rec.w9 and rec.w9 > 0:
            rec.water_content = (rec.w8 / rec.w9) * 100
        else:
            rec.water_content = 0.0


    @api.depends('wet_density', 'water_content')
    def _compute_dry_density(self):
     for rec in self:
        if rec.water_content is not None:
            rec.dry_density = (rec.wet_density / (1 + rec.water_content/100))
        else:
            rec.dry_density = 0.0

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(HeavyCompactionTestLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class CaliforniaBearingTest(models.Model):
    _name = 'california.bearing.test'
    _description = 'CBR Test Data'

    parent_id = fields.Many2one('mechanical.soil1', string="Parent")

    serial_no = fields.Integer(string="Trial No",readonly=True,default=1)

    penetration = fields.Float(string="Penetration")

    

    
    # SAMPLE 1
    sample1_reading = fields.Float(string="Reading1")
    sample1_load = fields.Float(string="Load1 (Kg/cm²)", compute="_compute_loads", store=True)


    # SAMPLE 2
    sample2_reading = fields.Float(string="Reading2")
    sample2_load = fields.Float(string="Load2 (Kg/cm²)", compute="_compute_loads", store=True)

    
    # SAMPLE 3
    sample3_reading = fields.Float(string="Reading3")
    sample3_load = fields.Float(string="Load2 (Kg/cm²)", compute="_compute_loads", store=True)

    
    @api.depends(
        'sample1_reading', 'sample2_reading', 'sample3_reading','parent_id',
        'parent_id.plunger_area', 'parent_id.div_load'
    )
    def _compute_loads(self):
        for rec in self:
            plunger_area = rec.parent_id.plunger_area if rec.parent_id else 0
            div_load = rec.parent_id.div_load if rec.parent_id else 0

            if plunger_area and div_load:
                rec.sample1_load = (rec.sample1_reading * div_load) / plunger_area
                rec.sample2_load = (rec.sample2_reading * div_load) / plunger_area
                rec.sample3_load = (rec.sample3_reading * div_load) / plunger_area
            else:
                rec.sample1_load = 0.0
                rec.sample2_load = 0.0
                rec.sample3_load = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CaliforniaBearingTest, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class ConsolidationTestLine(models.Model):
    _name = "mechanical.consolidation.test.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    time_interval = fields.Char(string="Time Interval (vertical)")
    load_0_1 = fields.Float(string="0.1")
    load_0_2 = fields.Float(string="0.2")
    load_0_4 = fields.Float(string="0.4")
    load_1 = fields.Float(string="1")
    load_2 = fields.Float(string="2")
    load_4 = fields.Float(string="4")
    load_8 = fields.Float(string="8")
    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ConsolidationTestLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class ConsolidationTwoTestLine(models.Model):
    _name = "mechanical.consolidation.two.test.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

   
    stage = fields.Char("Stage")
    pressure = fields.Float("Intensity Pressure (kg/cm²)")

    initial_reading = fields.Float("Initial Dial Reading")
    final_reading = fields.Float("Final Dial Reading")

    # ΔH
    dial_gauge_change = fields.Float(
        compute="_compute_dial_change",
        store=True
    )

    # ✅ FINAL computed
    specimen_height = fields.Float(
        compute="_compute_specimen_height",
        store=True
    )

    

    height_voids = fields.Float(
        compute="_compute_values", store=True
    )

    void_ratio = fields.Float(
        compute="_compute_values", store=True,digits=(10,6)
    )

    @api.depends('initial_reading', 'final_reading')
    def _compute_dial_change(self):
     for rec in self:
        rec.dial_gauge_change = (rec.initial_reading or 0.0) - (rec.final_reading or 0.0)

   

    @api.depends('dial_gauge_change', 'parent_id.height_ini')
    def _compute_specimen_height(self):
     for rec in self:

        h1 = rec.parent_id.height_ini or 0.0
        delta_h = rec.dial_gauge_change or 0.0

        # ✅ FINAL FORMULA
        rec.specimen_height = h1 - delta_h



    @api.depends('specimen_height', 'parent_id.height_con')
    def _compute_values(self):
     for rec in self:

        hs = rec.parent_id.height_con or 0.0
        h = rec.specimen_height or 0.0

        # 1️⃣ Height of Voids
        rec.height_voids = h - hs

        # 2️⃣ Void Ratio (avoid division error)
        if hs:
            rec.void_ratio = rec.height_voids / hs
        else:
            rec.void_ratio = 0.0



   
    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ConsolidationTwoTestLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class ConsolidationThreeTestLine(models.Model):
    _name = "mechanical.consolidation.three.test.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

   
    time_min = fields.Float("Time (min)")
    sqrt_t = fields.Float(
        string="√t",
        compute="_compute_sqrt_t",
        store=True
    )

    int_pressure = fields.Float(
    string="Intensity Pressure (8 kg/cm²)",
    compute="_compute_int_pressure",
    store=True
)
    
    @api.depends('parent_id.consolidation_line_ids.load_8')
    def _compute_int_pressure(self):
     for rec in self:

        parent = rec.parent_id
        if not parent:
            rec.int_pressure = 0.0
            continue

        lines = parent.consolidation_line_ids
        current_lines = parent.consolidation_three_line_ids

        # Convert to list (important)
        lines_list = list(lines)
        current_list = list(current_lines)

        if rec in current_list:
            index = current_list.index(rec)

            if index < len(lines_list):
                rec.int_pressure = lines_list[index].load_8 or 0.0
            else:
                rec.int_pressure = 0.0


    @api.depends('time_min')
    def _compute_sqrt_t(self):
     for rec in self:
        rec.sqrt_t = math.sqrt(rec.time_min) if rec.time_min else 0.0
   
    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ConsolidationThreeTestLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1






class ConstantHeadLine(models.Model):
    _name = 'constant.head.line'
    _description = 'Constant Head Test Line'

    parent_id = fields.Many2one('mechanical.soil1', string="Parent")

    serial_no = fields.Integer(string="Sr.No",readonly=True,default=1)

    time = fields.Float(string="Elapsed Time t (sec)")
    volume = fields.Float(string="Outflow Volume Q")
    temperature = fields.Float(string="Water Temperature (°C)")

    kt = fields.Float(string="Kt (cm/sec)", compute="_compute_values", store=True,digits=(16,10))
    k27 = fields.Float(string="K27 (cm/sec)", compute="_compute_values", store=True,digits=(16,10))

    @api.depends(
        'time', 'volume', 'temperature',
        'parent_id.constant_head_length', 'parent_id.constant_head_area',
        'parent_id.constant_head', 'parent_id.constant_viscosity_t',
        'parent_id.constant_viscosity_27'
    )
    def _compute_values(self):
        for rec in self:
            A = rec.parent_id.constant_head_area
            L = rec.parent_id.constant_head_length
            h = rec.parent_id.constant_head
            yt = rec.parent_id.constant_viscosity_t
            y27 = rec.parent_id.constant_viscosity_27

            if rec.time and A and h:
                rec.kt = round((rec.volume * L) / (A * rec.time * h),6)
            else:
                rec.kt = 0.0

            if rec.kt and yt and y27:
                rec.k27 = round(rec.kt * (yt / y27),6)
            else:
                rec.k27 = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ConstantHeadLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class PermeabilityHeadLine(models.Model):
    _name = 'permeability.head.line'

    parent_id = fields.Many2one('mechanical.soil1', string="Parent")

    serial_no = fields.Integer(string="Sr.No",readonly=True,default=1)

    initial_time = fields.Float("Initial Time ti (sec)")
    final_time = fields.Float("Final time tf (sec)")

    h1 = fields.Float("Initial Head h1 (cm)")
    h2 = fields.Float("Final Head h2 (cm)")

    kt = fields.Float("Kt (cm/sec)", compute="_compute_values", digits=(16,10))
    k27 = fields.Float("K27 (cm/sec)", compute="_compute_values", digits=(16,10))

    @api.depends(
    'initial_time', 'final_time', 'h1', 'h2',
    'parent_id.permeability_length',
    'parent_id.permeability_area',
    'parent_id.permeability_standarea',
    'parent_id.permeability_viscosity_t',
    'parent_id.permeability_viscosity_27'
)
    def _compute_values(self):
     for rec in self:

        try:
            L = Decimal(str(rec.parent_id.permeability_length or 0))
            A = Decimal(str(rec.parent_id.permeability_area or 0))
            a = Decimal(str(rec.parent_id.permeability_standarea or 0))
            yt = Decimal(str(rec.parent_id.permeability_viscosity_t or 0))
            y27 = Decimal(str(rec.parent_id.permeability_viscosity_27 or 0))

            ti = Decimal(str(rec.initial_time or 0))
            tf = Decimal(str(rec.final_time or 0))

            h1 = Decimal(str(rec.h1 or 0))
            h2 = Decimal(str(rec.h2 or 0))

            t = tf - ti

            # -------- Kt --------
            if t > 0 and h1 > 0 and h2 > 0 and A > 0 and a > 0 and L > 0:
                log_term = Decimal(str(math.log10(float(h1 / h2))))
                kt = (Decimal('2.303') * a * L / (A * t)) * log_term

                rec.kt = float(kt.quantize(Decimal('0.0000000001')))  # 10 decimal stable
            else:
                rec.kt = 0.0

            # -------- K27 --------
            if rec.kt and yt > 0 and y27 > 0:
                k27 = Decimal(str(rec.kt)) * (yt / y27)
                rec.k27 = float(k27.quantize(Decimal('0.0000000001')))
            else:
                rec.k27 = 0.0

        except Exception:
            rec.kt = 0.0
            rec.k27 = 0.0


    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PermeabilityHeadLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class SandReplacementLine(models.Model):
    _name = 'sand.replacement.line'
    _description = 'Sand Replacement Line'

    parent_id = fields.Many2one('mechanical.soil1', string="Parent")

    serial_no = fields.Integer(string="Sr.No",readonly=True,default=1)

    w2 = fields.Float("Mean Weight of sand in cone (of pouring cylinder) W2 in gm.", digits=(16, 0))
    ys = fields.Float("Bulk Density of sand Ys (gm/cc)", digits=(16, 6))

    m = fields.Float("Maximum Dry Density, gm/cc (M)", digits=(16, 6))

    # --- INPUTS ---
    wn = fields.Float("Weight sample of hole (Ww) in gm.", digits=(16, 0))
    w1 = fields.Float("Weight of sand + cylinder before pouring (W1) gm.", digits=(16, 0))
    w4 = fields.Float("Weight of sand + cylinder after pouring (W4) in gm.", digits=(16, 0))
    w = fields.Float("Moisture Content (W), (%)", digits=(16, 2))

    # --- COMPUTED VALUES ---
    wb = fields.Float("Weight of sand in hole, (Wb = W1 – W4 –W2) in gm.", compute="_compute_values", store=True, digits=(16, 0))
    yb = fields.Float("Bulk Density, Yb= (Ww/Wb) x Ys (gm/cc)", compute="_compute_values", store=True, digits=(16, 11))
    yd = fields.Float("Dry Density Yd = (100 Yb / 100 + W) gm/cc.", compute="_compute_values", store=True, digits=(16, 11))
    m1 = fields.Float("% of Compaction M1 = (Yd/M) *100", compute="_compute_values", store=True, digits=(16, 10))

    @api.depends('wn', 'w1', 'w4', 'w', 'w2', 'ys', 'm')
    def _compute_values(self):
        for rec in self:
            w2 = rec.w2 or 0
            ys = rec.ys or 0
            m = rec.m or 0

            # Wb = W1 - W4 - W2
            rec.wb = rec.w1 - rec.w4 - w2

            # Yb = (Wn / Wb) * Ys
            rec.yb = (rec.wn / rec.wb) * ys if rec.wb else 0

            # Yd = (100 * Yb) / (100 + W)
            rec.yd = (100 * rec.yb) / (100 + rec.w) if (100 + rec.w) else 0

            # % Compaction = (Yd / M) * 100
            rec.m1 = (rec.yd / m) * 100 if m else 0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SandReplacementLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class CoreCutterLine(models.Model):
    _name = 'core.cutter.line'
    _description = 'Core Cutter Test Line'

    parent_id = fields.Many2one('mechanical.soil1', string="Parent")

    serial_no = fields.Integer(string="Sr.No",readonly=True,default=1)

    # Input fields
    diameter = fields.Float(string="Internal diameter of core cutter (cm)")
    height = fields.Float(string="Internal height of core cutter (cm)")
    empty_weight = fields.Float(string="Mass of empty core cutter (gm)")
    full_weight = fields.Float(string="Mass of core cutter + Soil (gm)")
    wet_weight = fields.Float(string="Mass of Wet Soil (gm)")


    rapid_moisture = fields.Float(string="Rapid Moisture Meter Reading")

    moisture_content = fields.Float(string="Moisture Content (%)",compute="_compute_moisture_content", store=True,digits=(16,12))

    max_dry_density = fields.Float(string="Max Dry Density (gm/cc)")
    optimum_moisture = fields.Float(string="Optimum Moisture (%)")

    # Computed fields
    volume = fields.Float(string="Volume of Core Cutter (cc)", compute="_compute_volume", store=True,digits=(10,2))
    bulk_density = fields.Float(string="Bulk Density of Material (gm/cc)", compute="_compute_bulk", store=True,digits=(16,13))

    dry_density = fields.Float(string="Field max. Dry Density (gm/cc)", compute="_compute_dry", store=True,digits=(16,11))
    compaction = fields.Float(string="Compaction (%)", compute="_compute_compaction", store=True)

    @api.depends('diameter', 'height')
    def _compute_volume(self):
        for rec in self:
            rec.volume = 3.14 * ((rec.diameter  ** 2)/4) * rec.height

    @api.depends('wet_weight', 'volume')
    def _compute_bulk(self):
        for rec in self:
            rec.bulk_density = rec.wet_weight / rec.volume if rec.volume else 0

    @api.depends('bulk_density', 'moisture_content')
    def _compute_dry(self):
        for rec in self:
            rec.dry_density = rec.bulk_density / (1 + rec.moisture_content / 100) if rec.moisture_content else rec.bulk_density

    @api.depends('dry_density', 'max_dry_density')
    def _compute_compaction(self):
        for rec in self:
            rec.compaction = (rec.dry_density / rec.max_dry_density * 100) if rec.max_dry_density else 0

    @api.depends('rapid_moisture')
    def _compute_moisture_content(self):
        for rec in self:
            rec.moisture_content = (rec.rapid_moisture / (100 - rec.rapid_moisture)) * 100 if rec.rapid_moisture else 0


    m3 = fields.Float(string="Mass of can + dry soil (W3)")
    wet_weight = fields.Float(
        string="Wet Soil Weight (M = M2 - M1)",
        compute="_compute_moisture",
        store=True
    )
    water_weight = fields.Float(
        string="Weight of Water",
        compute="_compute_moisture",
        digits=(16, 12),
        store=True
    )
    volume_dry = fields.Float(
        string="Volume of Core Cutter (cc)",
        compute="_compute_moisture",
        store=True,
        digits=(16, 14)
    )


    water_content = fields.Float(
        string="Water content (%)",
        compute="_compute_moisture",
        digits=(16, 13),
        store=True
    )
    dry_density2 = fields.Float(
        string="Dry density (gm/cc)",
        compute="_compute_moisture",
        store=True,
        digits=(16, 12)
    )



    @api.depends('empty_weight', 'full_weight', 'm3','rapid_moisture','diameter','height')
    def _compute_moisture(self):
        for rec in self:
            wet_soil = rec.full_weight - rec.empty_weight      # M2 - M1
            moisture_content = (rec.rapid_moisture / (100 - rec.rapid_moisture)) * 100 if rec.rapid_moisture else 0    
            rec.water_weight =  rec.moisture_content  - rec.m3 

            rec.wet_weight = rec.full_weight - rec.empty_weight 
            rec.volume_dry = (3.1416 * ((rec.diameter / 2) ** 2) * rec.height) / 1000

            ww = rec.m3 - rec.rapid_moisture

            if ww!=0:
                rec.water_content = ((moisture_content- rec.m3) / (rec.m3 - rec.rapid_moisture)) * 100
            else:
                rec.water_content= 0.0

            if rec.volume_dry:
                rec.dry_density2 = ((rec.wet_weight / rec.volume_dry) / (1 + rec.water_content))
            else:
                rec.dry_density2 = 0.0
  
            


            
           

            
            
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CoreCutterLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1






    

    

            
class soilNotes(models.Model):
    _name = "soil.notes"

    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")