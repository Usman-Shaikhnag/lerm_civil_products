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
from decimal import Decimal, ROUND_HALF_UP


from matplotlib.ticker import MultipleLocator, StrMethodFormatter

import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from odoo import models, fields, api
from odoo.exceptions import UserError
import math

from odoo import api, fields, models
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
import io
import base64
from matplotlib.ticker import MultipleLocator





class Soil(models.Model):
    _name = "mechanical.soil1"
    _inherit = "lerm.eln"
    _rec_name = "name_soil"


    name_soil = fields.Char("Name",default="Soil")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    temprature = fields.Float("Temperature (°C)", digits=(10,2))
    humidity = fields.Float("Humidity (%)", digits=(10,2))

    condition = fields.Char("Condition")




    # remark

    notes_id = fields.One2many('soil.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(Soil, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The report shall not be reproduced in full or partially without written approval of the laboratory HOD/CEO/Maganement.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'Sampling is not done by us unless mentioned otherwide.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'without a QR Code and hologram this report is considered invalid.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'The Result listed refer only to tested samples & applicable parameter Endorsement of product is neither interred nor inplied.',
            }),

            (0, 0, {
                'sr_no': 'e',
                'notes': 'The use or report for arbitration, publicity & evidence in legal dispute is forbidden except with prior written consent NBML Lab.',
            }),
             (0, 0, {
                'sr_no': 'f',
                'notes': 'All disputed are subject to Raipur jurisdiction 7 days correction to this report invalidates this report.',
            }),

             (0, 0, {
                'sr_no': 'g',
                'notes': 'Sample will be destroyed after 30-days from the date of test report unless otherwise Specified.',
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
    sieve_report_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )
 
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
        


    

    d60 = fields.Float(string="D60 (mm)", compute="_compute_d_values", digits=(18,14))
    d30 = fields.Float(string="D30 (mm)", compute="_compute_d_values", digits=(16,14))
    d10 = fields.Float(string="D10 (mm)", compute="_compute_d_values", digits=(18,16))

    cu = fields.Float(string="Cu = D60/D10", compute="_compute_cu", digits=(12,2))
    cc = fields.Float(string="Cc = D30²/(D10×D60)", compute="_compute_cc_slive", digits=(12,2))

    # @api.depends('sieve_analysis_child_lines.sieve_size',
    #          'sieve_analysis_child_lines.passing_percent')
    # def _compute_d_values(self):
    #  for record in self:

    #     data = []

    #     # -------------------------
    #     # Prepare (size, passing %)
    #     # -------------------------
    #     for line in record.sieve_analysis_child_lines:
    #         try:
    #             size_str = str(line.sieve_size).lower().strip()

    #             if 'pan' in size_str:
    #                 size = 0.0
    #             else:
    #                 size = float(size_str.replace('mm', '').replace('µ', '').replace('um', ''))

    #             passing = line.passing_percent or 0.0

    #             data.append((size, passing))
    #         except:
    #             continue

    #     # -------------------------
    #     # SORT (VERY IMPORTANT)
    #     # -------------------------
    #     data = sorted(data, key=lambda x: x[0], reverse=True)

    #     # DEBUG (remove later)
    #     print("DATA:", data)

    #     # -------------------------
    #     # INTERPOLATION FUNCTION
    #     # -------------------------
    #     def get_d(target):
    #         for i in range(len(data) - 1):
    #             x1, y1 = data[i]
    #             x2, y2 = data[i + 1]

    #             if y1 >= target >= y2:
    #                 if y2 != y1:
    #                     return x1 + (x2 - x1) * ((target - y1) / (y2 - y1))
    #         return 0.0

    #     # -------------------------
    #     # COMPUTE
    #     # -------------------------
    #     record.d10 = get_d(10)
    #     record.d30 = get_d(30)
    #     record.d60 = get_d(60)




    
    @api.depends(
    'sieve_analysis_child_lines.sieve_size',
    'sieve_analysis_child_lines.passing_percent'
    )
    def _compute_d_values(self):

        for record in self:

            data = []

            # -----------------------------------------
            # PREPARE DATA
            # -----------------------------------------
            for line in record.sieve_analysis_child_lines:

                try:
                    size_str = str(line.sieve_size).lower().strip()

                    # Ignore PAN
                    if 'pan' in size_str:
                        continue

                    size = float(
                        size_str.replace('mm', '')
                                .replace('µ', '')
                                .replace('um', '')
                                .strip()
                    )

                    passing = float(line.passing_percent or 0.0)

                    data.append((size, passing))

                except Exception:
                    continue

            # -----------------------------------------
            # SORT BY PASSING %
            # -----------------------------------------
            data = sorted(data, key=lambda x: x[1], reverse=True)

            print("DATA =", data)

            # -----------------------------------------
            # EXCEL TREND STYLE INTERPOLATION
            # -----------------------------------------
            def get_d(target):

                if not data:
                    return 0.0

                for i in range(len(data) - 1):

                    d1, p1 = data[i]
                    d2, p2 = data[i + 1]

                    # exact match
                    if p1 == target:
                        return d1

                    if p2 == target:
                        return d2

                    # interpolation / extrapolation zone
                    if (p1 >= target >= p2) or (p1 <= target <= p2):

                        # ---------------------------------
                        # SAFE GUARD (avoid division by zero)
                        # ---------------------------------
                        if abs(p2 - p1) < 1e-9:
                            return d1

                        result = d1 + (
                            (target - p1)
                            * (d2 - d1)
                            / (p2 - p1)
                        )

                        return result

                # -----------------------------------------
                # EXTRAPOLATION (Excel TREND style)
                # -----------------------------------------
                if len(data) >= 2:

                    d1, p1 = data[-2]
                    d2, p2 = data[-1]

                    if abs(p2 - p1) < 1e-9:
                        return d1

                    result = d1 + (
                        (target - p1)
                        * (d2 - d1)
                        / (p2 - p1)
                    )

                    return result

                return 0.0

            # -----------------------------------------
            # COMPUTE D VALUES
            # -----------------------------------------
            record.d10 = get_d(10)
            record.d30 = get_d(30)
            record.d60 = get_d(60)

            # -----------------------------------------
            # OPTIONAL: Cu (commented safe version)
            # -----------------------------------------
            # if record.d10:
            #     record.cu = record.d60 / record.d10
            # else:
            #     record.cu = 0.0

            # -----------------------------------------
            # OPTIONAL: Cc (commented safe version)
            # -----------------------------------------
            # if record.d10 and record.d60:
            #     record.cc = (record.d30 ** 2) / (record.d10 * record.d60)
            # else:
            #     record.cc = 0.0


    # @api.depends('d60','d10')
    # def _compute_cu(self):
    #  for record in self:
    #     record.cu = (record.d60 / record.d10) if record.d10 else 0.0

    @api.depends('d60', 'd10')
    def _compute_cu(self):
 
     for record in self:

        d60 = round(record.d60 or 0.0, 10)
        d10 = round(record.d10 or 0.0, 16)

        record.cu = round((d60 / d10), 2) if d10 else 0.0


    @api.depends('d30','d10','d60')
    def _compute_cc_slive(self):
     for record in self:
        if record.d10 and record.d60:
            r = (record.d60 / record.d10)
            record.cc = (record.d30 ** 2) / r
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




    # def generate_line_chart_slive(self):
   
    #     x_value = []
    #     y_value = []
    #     x_labels = []

    #     for line in self.sieve_analysis_child_lines:
    #         if line.sieve_size and line.passing_percent is not None:
    #             sieve_str = str(line.sieve_size).strip().lower()
    #             try:
    #                 if 'mm' in sieve_str:
    #                     sieve_val = float(sieve_str.replace('mm', '').strip())
    #                     label = f"{int(sieve_val)} mm"
    #                 elif 'µ' in sieve_str or 'micron' in sieve_str:
    #                     sieve_val = float(sieve_str.replace('µ', '').replace('micron', '').strip()) / 1000
    #                     label = f"{int(float(line.sieve_size.replace('µ', '').replace('micron', '').strip()))} µm"
    #                 else:
    #                     sieve_val = float(sieve_str)
    #                     label = f"{sieve_val} mm"

    #                 x_value.append(sieve_val)
    #                 y_value.append(float(line.passing_percent))
    #                 x_labels.append(label)
    #             except ValueError:
    #                 continue

    #     if not x_value or not y_value:
    #         return False

    #     # Sort ascending
    #     sorted_data = sorted(zip(x_value, y_value, x_labels))
    #     x_value, y_value, x_labels = zip(*sorted_data)

    #     plt.figure(figsize=(12, 5))
    #     plt.xscale('log')

    #     # Main curve
    #     plt.plot(x_value, y_value, color='blue', linestyle='-', linewidth=2)
    #     plt.scatter(x_value, y_value, color='red', edgecolors='black', s=60, zorder=5)

    #     plt.xlabel('Sieve Size', fontsize=12)
    #     plt.ylabel('Passing %', fontsize=12)
    #     plt.title('Grain Size Analysis', fontsize=14)

    #     ax = plt.gca()
    #     plt.xticks(ticks=x_value, labels=x_labels, rotation=45, ha='right')
    #     ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(1.0, 10.0)*0.1, numticks=200))
    #     ax.yaxis.set_minor_locator(MultipleLocator(2))
    #     plt.grid(True, which='both', axis='both', linestyle='--', linewidth=0.3, color='gray', alpha=0.8)

    #     plt.xlim(left=min(x_value)/1.5, right=max(x_value)*1.5)
    #     plt.ylim(bottom=0, top=100)

    #     # --- D-points: D10, D30, D60 ---
    #     d_points = [
    #         (getattr(self, 'd10', None), 10, 'black'),
    #         (getattr(self, 'd30', None), 30, 'yellow'),
    #         (getattr(self, 'd60', None), 60, 'orange')
    #     ]

    #     for dx, dy, color in d_points:
    #         if dx:
    #             # Solid point
    #             plt.scatter(dx, dy, color=color, s=80, zorder=10)
    #             # Draw X and Y guide lines only to intersection
    #             plt.plot([dx, dx], [0, dy], color=color, linestyle='-', linewidth=1.2)
    #             plt.plot([0, dx], [dy, dy], color=color, linestyle='-', linewidth=1.2)

    #     # Save figure
    #     buffer = io.BytesIO()
    #     plt.tight_layout()
    #     plt.savefig(buffer, format='png')
    #     plt.close()
    #     buffer.seek(0)

    #     return base64.b64encode(buffer.read())

    def generate_line_chart_slive(self):

     x_value = []
     y_value = []
     x_labels = []

    # -----------------------------------
    # PREPARE DATA
    # -----------------------------------
     for line in self.sieve_analysis_child_lines:

        if line.sieve_size and line.passing_percent is not None:

            sieve_str = str(line.sieve_size).strip().lower()

            try:
                # mm values
                if 'mm' in sieve_str:

                    sieve_val = float(
                        sieve_str.replace('mm', '').strip()
                    )

                    label = f"{sieve_val:g} mm"

                # micron values
                elif 'µ' in sieve_str or 'micron' in sieve_str or 'um' in sieve_str:

                    micron_val = float(
                        sieve_str.replace('µ', '')
                                 .replace('micron', '')
                                 .replace('um', '')
                                 .strip()
                    )

                    sieve_val = micron_val / 1000

                    label = f"{micron_val:g} µm"

                else:

                    sieve_val = float(sieve_str)
                    label = f"{sieve_val:g} mm"

                x_value.append(sieve_val)
                y_value.append(float(line.passing_percent))
                x_labels.append(label)

            except Exception:
                continue

    # -----------------------------------
    # NO DATA
    # -----------------------------------
     if not x_value or not y_value:
        return False

    # -----------------------------------
    # SORT ASCENDING
    # -----------------------------------
     sorted_data = sorted(zip(x_value, y_value, x_labels))

     x_value, y_value, x_labels = zip(*sorted_data)

    # Convert to numpy arrays
     x_value = np.array(x_value)
     y_value = np.array(y_value)

    # -----------------------------------
    # CREATE SMOOTH CURVE
    # -----------------------------------
     x_log = np.log10(x_value)

    # Smooth X points
     x_smooth_log = np.linspace(
        x_log.min(),
        x_log.max(),
        300
    )

    # Cubic spline interpolation
     spline = make_interp_spline(
        x_log,
        y_value,
        k=3
    )

     y_smooth = spline(x_smooth_log)

    # Convert back to actual scale
     x_smooth = 10 ** x_smooth_log

    # -----------------------------------
    # CREATE FIGURE
    # -----------------------------------
     plt.figure(figsize=(12, 5))

     plt.xscale('log')

    # Smooth curve
     plt.plot(
        x_smooth,
        y_smooth,
        color='blue',
        linewidth=2.5,
        linestyle='-'
    )

    # Original points
     plt.scatter(
        x_value,
        y_value,
        color='red',
        edgecolors='black',
        s=60,
        zorder=5
    )

    # -----------------------------------
    # LABELS
    # -----------------------------------
     plt.xlabel('Sieve Size', fontsize=12)
     plt.ylabel('Passing %', fontsize=12)
     plt.title('Grain Size Analysis', fontsize=14)

    # -----------------------------------
    # GRID & AXIS
    # -----------------------------------
     ax = plt.gca()

     plt.xticks(
        ticks=x_value,
        labels=x_labels,
        rotation=45,
        ha='right'
    )

     ax.xaxis.set_minor_locator(
        LogLocator(
            base=10.0,
            subs=np.arange(1.0, 10.0) * 0.1,
            numticks=200
        )
    )

     ax.yaxis.set_minor_locator(
        MultipleLocator(2)
    )

     plt.grid(
        True,
        which='both',
        axis='both',
        linestyle='--',
        linewidth=0.3,
        color='gray',
        alpha=0.8
    )

     plt.xlim(
        left=min(x_value) / 1.5,
        right=max(x_value) * 1.5
    )

     plt.ylim(
        bottom=0,
        top=100
    )

    # -----------------------------------
    # D-VALUES
    # -----------------------------------
     d_points = [
        (getattr(self, 'd10', None), 10, 'black', 'D10'),
        (getattr(self, 'd30', None), 30, 'black', 'D30'),
        (getattr(self, 'd60', None), 60, 'black', 'D60')
    ]

     for dx, dy, color, label in d_points:

        if dx:

            # D-point
            plt.scatter(
                dx,
                dy,
                color=color,
                s=80,
                zorder=10
            )

            # Vertical guide line
            plt.plot(
                [dx, dx],
                [0, dy],
                color=color,
                linestyle='-',
                linewidth=1.2
            )

            # Horizontal guide line
            plt.plot(
                [min(x_value), dx],
                [dy, dy],
                color=color,
                linestyle='-',
                linewidth=1.2
            )

            # Text label
            plt.text(
                dx,
                dy + 3,
                f"{label} = {dx:.3f}",
                fontsize=9,
                ha='center'
            )

    # -----------------------------------
    # SAVE IMAGE
    # -----------------------------------
     buffer = io.BytesIO()

     plt.tight_layout()

     plt.savefig(
        buffer,
        format='png',
        dpi=300
    )

     plt.close()

     buffer.seek(0)

     return base64.b64encode(buffer.read())


    show_sieve_graph = fields.Boolean(string="Show Sieve Graph in Report")
    


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
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_moisture_content_conformity", store=True)

    @api.depends('avg_moisture_content','eln_ref','grade')
    def _compute_avg_moisture_content_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_moisture_content_conformity = 'na'
                continue

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
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_specific_gravity_conformity", store=True)

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_specific_gravity_conformity = 'na'
                continue


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
    atterberg_visible = fields.Boolean("Atterberg Visible",compute="_compute_visible")


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
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_liquid_limit_conformity", store=True)

    @api.depends('liquid_limit','eln_ref','grade')
    def _compute_liquid_limit_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.liquid_limit_conformity = 'na'
                continue

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
    show_liquid_graph1 = fields.Boolean(string="Show Liquid Limit Graph")

    def action_generate_graphl(self):
     import numpy as np
     import matplotlib.pyplot as plt
     from matplotlib.ticker import LogLocator, ScalarFormatter, MultipleLocator
     import io
     import base64

     for rec in self:

        rec.water_line_ids._compute_values()

        # -------------------------------
        # DATA
        # -------------------------------
        blows = np.array([float(l.blows or 0) for l in rec.water_line_ids])
        water = np.array([float(l.water_content or 0) for l in rec.water_line_ids])

        mask = (blows > 0) & (water > 0)
        blows = blows[mask]
        water = water[mask]

        if len(blows) < 2:
            continue

        print("POINTS:", list(zip(blows, water)))  # DEBUG

        # Sort
        idx = np.argsort(blows)
        blows = blows[idx]
        water = water[idx]

        # -------------------------------
        # LOG FIT
        # -------------------------------
        log_b = np.log10(blows)
        coeffs = np.polyfit(log_b, water, 1)
        fit = np.poly1d(coeffs)

        log_x = np.linspace(np.log10(min(blows)*0.8), np.log10(max(blows)*1.5), 200)
        x_smooth = 10 ** log_x
        y_smooth = fit(log_x)

        # -------------------------------
        # GRAPH
        # -------------------------------
        fig, ax = plt.subplots(figsize=(10, 5))

        ax.set_xscale('log')

        # Dynamic limits
        x_min = max(1, min(blows)*0.8)
        x_max = max(blows)*1.5
        ax.set_xlim(x_min, x_max)

        y_min = min(water) - 2
        y_max = max(water) + 2
        ax.set_ylim(y_min, y_max)

        # -------------------------------
        # GRID (GRAPH PAPER STYLE)
        # -------------------------------
        ax.xaxis.set_major_locator(LogLocator(base=10))
        ax.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10)*0.1))

        ax.yaxis.set_major_locator(MultipleLocator(1))
        ax.yaxis.set_minor_locator(MultipleLocator(0.5))

        ax.grid(which='major', linewidth=1, color='black')
        ax.grid(which='minor', linewidth=0.5, color='gray')

        # -------------------------------
        # ✅ EXCEL-LIKE X AXIS (KEY FIX)
        # -------------------------------
        xticks = sorted(set([
            10, 15, 18, 20, 22, 25, 30, 40, 50, 100
        ] + list(blows.astype(int))))

        xticks = [x for x in xticks if x_min <= x <= x_max]

        ax.set_xticks(xticks)

        ax.get_xaxis().set_major_formatter(ScalarFormatter())
        ax.ticklabel_format(style='plain', axis='x')

        # -------------------------------
        # FIT LINE
        # -------------------------------
        ax.plot(x_smooth, y_smooth, color='orange', linewidth=2)

        # -------------------------------
        # POINTS + LABELS
        # -------------------------------
        for i, (x, y) in enumerate(zip(blows, water)):
            ax.scatter(x, y,
                       color='#1f77b4',
                       s=80,
                       edgecolors='black',
                       zorder=6)

            # Smart label position
            offset = 0.5 if y < (y_max - 1) else -0.5
            ax.text(x, y + offset,
                    f"P{i+1}",
                    fontsize=8,
                    ha='center')

        # -------------------------------
        # LIQUID LIMIT (25 BLOWS)
        # -------------------------------
        ll_x = 25
        ll_y = float(fit(np.log10(ll_x)))

        if x_min < ll_x < x_max:
            ax.axvline(ll_x, color='#2c6db2', linewidth=2)

        if y_min < ll_y < y_max:
            ax.axhline(ll_y, color='#6aa84f', linewidth=2)

        ax.scatter(ll_x, ll_y, color='#2c6db2', s=120, zorder=10)

        # -------------------------------
        # LABELS
        # -------------------------------
        ax.set_title("LIQUID LIMIT TEST GRAPH (CASAGRANDE)")
        ax.set_xlabel("No. of Blows")
        ax.set_ylabel("Water Content (%)")

        # -------------------------------
        # SAVE
        # -------------------------------
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        plt.close()

        rec.graph_image = base64.b64encode(buffer.getvalue())

      


    graph_image1 = fields.Binary(string="Flow Curve Graph")
    show_liquid_graph2 = fields.Boolean(string="Show Liquid Limit Graph")

  

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
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Plastic Limit Conformity", compute="_compute_plastic_limit_conformity", store=True)

    @api.depends('plastic_limit','eln_ref','grade')
    def _compute_plastic_limit_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.plastic_limit_conformity = 'na'
                continue

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
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Plasticity Index Conformity", compute="_compute_plasticity_index_conformity", store=True)

    @api.depends('plasticity_index','eln_ref','grade')
    def _compute_plasticity_index_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.plasticity_index_conformity = 'na'
                continue

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
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_fsi_conformity", store=True)

    @api.depends('avg_fsi','eln_ref','grade')
    def _compute_avg_fsi_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_fsi_conformity = 'na'
                continue

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
    light_comp_omc_visible = fields.Boolean("Light Compaction Test",compute="_compute_visible")
    light_comp_mdd_visible = fields.Boolean("Light Compaction Test",compute="_compute_visible")


    
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

   

    light_optimum_moisture = fields.Float(
        "Optimum Moisture Content (%)",
        digits=(16, 2),
        compute="_compute_light_omc_mdd",
        store=True
    )

    light_max_dry_density = fields.Float(
        "Maximum Dry Density (g/cc)",
        digits=(16, 3),
        compute="_compute_light_omc_mdd",
        store=True
    )

    @api.depends('light_line_ids.water_content', 'light_line_ids.dry_density')
    def _compute_light_omc_mdd(self):
        for rec in self:

            x = []
            y = []

            # -----------------------------
            # COLLECT DATA
            # -----------------------------
            for line in rec.light_line_ids:
                if line.water_content and line.dry_density:
                    x.append(float(line.water_content))
                    y.append(float(line.dry_density))

            if len(x) < 3:
                rec.light_optimum_moisture = 0
                rec.light_max_dry_density = 0
                continue

            # -----------------------------
            # SORT DATA
            # -----------------------------
            data = sorted(zip(x, y))
            x, y = zip(*data)

            x = np.array(x)
            y = np.array(y)

            # -----------------------------
            # INTERPOLATION (BEST METHOD)
            # -----------------------------
            interp = PchipInterpolator(x, y)

            x_smooth = np.linspace(min(x), max(x), 300)
            y_smooth = interp(x_smooth)

            # -----------------------------
            # FIND PEAK (OMC & MDD)
            # -----------------------------
            idx = np.argmax(y_smooth)
            omc = float(x_smooth[idx])
            mdd = float(y_smooth[idx])

            # -----------------------------
            # SAVE VALUES
            # -----------------------------
            rec.light_optimum_moisture = round(omc, 2)
            rec.light_max_dry_density = round(mdd, 3)


    light_graph_image = fields.Binary("Graph", readonly=True)
    show_light_graph1 = fields.Boolean(string="Show Light Compaction Graph")

    def action_generate_graph1(self):
     import numpy as np
     import matplotlib.pyplot as plt
     from scipy.interpolate import PchipInterpolator
     import io, base64

     for rec in self:

        x = []
        y = []

        # -----------------------------
        # COLLECT DATA
        # -----------------------------
        for line in rec.light_line_ids:
            if line.water_content and line.dry_density:
                x.append(float(line.water_content))
                y.append(float(line.dry_density))

        if len(x) < 3:
            rec.light_optimum_moisture = 0
            rec.light_max_dry_density = 0
            continue

        # -----------------------------
        # SORT DATA
        # -----------------------------
        data = sorted(zip(x, y))
        x, y = zip(*data)

        x = np.array(x)
        y = np.array(y)

        # -----------------------------
        # INTERPOLATION
        # -----------------------------
        interp = PchipInterpolator(x, y)

        x_smooth = np.linspace(min(x), max(x), 300)
        y_smooth = interp(x_smooth)

        # -----------------------------
        # FIND OMC & MDD
        # -----------------------------
        idx = np.argmax(y_smooth)
        omc = float(x_smooth[idx])
        mdd = float(y_smooth[idx])

        # ✅ SAVE VALUES (IMPORTANT)
        rec.light_optimum_moisture = round(omc, 2)
        rec.light_max_dry_density = round(mdd, 3)

        # -----------------------------
        # PLOT
        # -----------------------------
        plt.figure(figsize=(12, 5))

        plt.plot(x_smooth, y_smooth, color='blue', linewidth=2)
        plt.scatter(x, y, color='orange', s=60, zorder=5)

        plt.axvline(x=omc, color='black', linewidth=2)
        plt.axhline(y=mdd, color='black', linewidth=2)

        plt.scatter([omc], [mdd], color='black', s=70, zorder=10)

        plt.title('Light Compaction Test')
        plt.xlabel('Optimum Moisture Content (%)')
        plt.ylabel('Maximum Dry Density (gm/cc)')

        ax = plt.gca()
        ax.set_facecolor('#f5fff5')
        ax.minorticks_on()
        ax.grid(which='major', color='black', linewidth=0.8)
        ax.grid(which='minor', color='green', linestyle='--', linewidth=0.4)

        plt.xlim(0, max(x) + 2)
        plt.ylim(min(y) - 0.1, max(y) + 0.1)

        plt.tight_layout()

        # -----------------------------
        # SAVE IMAGE
        # -----------------------------
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=120)
        plt.close()
        buffer.seek(0)

        rec.light_graph_image = base64.b64encode(buffer.read())



    light1_graph_image = fields.Binary("Graph", readonly=True)
    show_light_graph2 = fields.Boolean(string="Show Light Compaction Graph")

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


    light_optimum_moisture_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_light_optimum_moisture_conformity", store=True)

    @api.depends('light_optimum_moisture','eln_ref','grade')
    def _compute_light_optimum_moisture_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.light_optimum_moisture_conformity = 'na'
                continue

            record.light_optimum_moisture_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7606fd1e-91b2-4433-a4df-c717bd8283be')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7606fd1e-91b2-4433-a4df-c717bd8283be')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.light_optimum_moisture - record.light_optimum_moisture*mu_value
                    upper = record.light_optimum_moisture + record.light_optimum_moisture*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.light_optimum_moisture_conformity = 'pass'
                        break
                    else:
                        record.light_optimum_moisture_conformity = 'fail'

    light_optimum_moisture_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_light_optimum_moisture_nabl", store=True)

    @api.depends('light_optimum_moisture','eln_ref','grade')
    def _compute_light_optimum_moisture_nabl(self):
        
        for record in self:
            record.light_optimum_moisture_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7606fd1e-91b2-4433-a4df-c717bd8283be')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7606fd1e-91b2-4433-a4df-c717bd8283be')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.light_optimum_moisture - record.light_optimum_moisture*mu_value
            upper = record.light_optimum_moisture + record.light_optimum_moisture*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.light_optimum_moisture_nabl = 'pass'
                break
            else:
                record.light_optimum_moisture_nabl = 'fail'

    light_max_dry_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_light_max_dry_density_conformity", store=True)

    @api.depends('light_max_dry_density','eln_ref','grade')
    def _compute_light_max_dry_density_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.light_max_dry_density_conformity = 'na'
                continue

            record.light_max_dry_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','90c1d609-0e28-4989-b840-9604bcfbfac2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','90c1d609-0e28-4989-b840-9604bcfbfac2')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.light_max_dry_density - record.light_max_dry_density*mu_value
                    upper = record.light_max_dry_density + record.light_max_dry_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.light_max_dry_density_conformity = 'pass'
                        break
                    else:
                        record.light_max_dry_density_conformity = 'fail'

    light_max_dry_density_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_light_max_dry_density_nabl", store=True)

    @api.depends('light_max_dry_density','eln_ref','grade')
    def _compute_light_max_dry_density_nabl(self):
        
        for record in self:
            record.light_max_dry_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','90c1d609-0e28-4989-b840-9604bcfbfac2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','90c1d609-0e28-4989-b840-9604bcfbfac2')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.light_max_dry_density - record.light_max_dry_density*mu_value
            upper = record.light_max_dry_density + record.light_max_dry_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.light_max_dry_density_nabl = 'pass'
                break
            else:
                record.light_max_dry_density_nabl = 'fail'

    



    # Heavy Compaction Test

    heavy_name1 = fields.Char("Name",default="Heavy Compaction Test ")
    heavy_visible = fields.Boolean("Heavy Compaction-MDD Visible",compute="_compute_visible")
    heavy_omc_visible = fields.Boolean("Heavy Compaction-MDD Visible",compute="_compute_visible")
    heavy_mdd_visible = fields.Boolean("Heavy Compaction-MDD Visible",compute="_compute_visible")


    heavy_mould_weight = fields.Float(string="Weight of Mould (w1)", required=True)
    heavy_mould_volume = fields.Float(string="Volume of Mould in cc (V)", required=True)

    heavy_line_ids = fields.One2many('heavy.compaction.test.line', 'parent_id', string="Trials")

    max_dry_density = fields.Float(string="Maximum Dry Density", compute="_compute_mdd")
    optimum_moisture = fields.Float(string="Optimum Moisture Content", compute="_compute_mdd")

    heavy_graph_image = fields.Binary("Graph", attachment=True)
    show_heavy_graph2 = fields.Boolean(string="Show Heavy Compaction Graph")

    

    # ---------------------------------------------------------
    # 1. COMPUTE METHOD (Fields la values denyasathi)
    # ---------------------------------------------------------
    @api.depends('heavy_line_ids.water_content', 'heavy_line_ids.dry_density')
    def _compute_mdd(self):
        for rec in self:
            x = []
            y = []
            for line in rec.heavy_line_ids:
                if line.water_content and line.dry_density:
                    x.append(float(line.water_content))
                    y.append(float(line.dry_density))

            if len(x) < 3:
                rec.optimum_moisture = 0.0
                rec.max_dry_density = 0.0
                continue

            x = np.array(x)
            y = np.array(y)

            # Handle duplicate X values
            unique_x = np.unique(x)
            if len(unique_x) < len(x):
                y = np.array([np.mean(y[x == ux]) for ux in unique_x])
                x = unique_x

            # Sort data
            idx = np.argsort(x)
            x = x[idx]
            y = y[idx]

            # Find max point
            max_idx = np.argmax(y)
            rec.optimum_moisture = float(x[max_idx])
            rec.max_dry_density = float(y[max_idx])


    # ---------------------------------------------------------
    # 2. GRAPH GENERATION METHOD
    # ---------------------------------------------------------
    def generate_line_chart_light_omc(self):
        for rec in self:
            x = []
            y = []

            for line in rec.heavy_line_ids:
                if line.water_content and line.dry_density:
                    x.append(float(line.water_content))
                    y.append(float(line.dry_density))

            if len(x) < 3:
                rec.heavy_graph_image = False
                continue

            x = np.array(x)
            y = np.array(y)

            # Handle duplicate X values
            unique_x = np.unique(x)
            if len(unique_x) < len(x):
                y = np.array([np.mean(y[x == ux]) for ux in unique_x])
                x = unique_x

            idx = np.argsort(x)
            x = x[idx]
            y = y[idx]

            # Computed field varun values ghene (direct max_x & max_y)
            max_x = rec.optimum_moisture
            max_y = rec.max_dry_density

            if not max_x or not max_y:
                continue

            # Add peak into curve data
            if max_x not in x:
                x_aug = np.append(x, max_x)
                y_aug = np.append(y, max_y)
                idx = np.argsort(x_aug)
                x_aug = x_aug[idx]
                y_aug = y_aug[idx]
            else:
                x_aug = x
                y_aug = y

            # Spline curve
            k_val = min(2, len(x_aug) - 1)
            x_smooth = np.linspace(min(x_aug), max(x_aug), 300)
            spline = make_interp_spline(x_aug, y_aug, k=k_val)
            y_smooth = spline(x_smooth)

            # Plotting
            plt.figure(figsize=(10, 5))
            plt.plot(x_smooth, y_smooth, color='blue', linewidth=2)
            plt.scatter(x, y, color='orange', s=50, zorder=5)

            plt.axhline(y=max_y, color='black', linewidth=1, linestyle='--')
            plt.axvline(x=max_x, color='black', linewidth=1, linestyle='--')

            # Peak point & Annotation
            plt.scatter(max_x, max_y, color='red', s=80, zorder=6)
            
            peak_text = f"OMC: {max_x:.2f}%\nMDD: {max_y:.3f} gm/cc"
            plt.annotate(
                peak_text,
                xy=(max_x, max_y),
                xytext=(20, 20),
                textcoords='offset points',
                fontsize=9,
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', edgecolor='black', alpha=0.9),
                arrowprops=dict(facecolor='black', arrowstyle='->', lw=1)
            )

            # Grid & Layout
            ax = plt.gca()
            ax.xaxis.set_minor_locator(MultipleLocator(0.2))
            ax.yaxis.set_minor_locator(MultipleLocator(0.01))

            plt.grid(which='major', color='black', linewidth=0.6)
            plt.grid(which='minor', color='green', linestyle='--', linewidth=0.3)

            plt.xlim(min(x) - 0.5, max(x) + 1)
            plt.ylim(min(y) - 0.05, max(y) + 0.05)

            plt.title("MODIFIED PROCTOR TEST", fontsize=14)
            plt.xlabel("Optimum Moisture Content (%)")
            plt.ylabel("Maximum Dry Density (gm/cc)")

            plt.tight_layout()

            # Save image
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=120)
            plt.close()
            buf.seek(0)

            rec.heavy_graph_image = base64.b64encode(buf.read())


    

    # def generate_line_chart_light_omc(self):
    #     import numpy as np
    #     import matplotlib.pyplot as plt
    #     from scipy.interpolate import make_interp_spline
    #     import io
    #     import base64
    #     from matplotlib.ticker import MultipleLocator

    #     for rec in self:

    #         x = []
    #         y = []

    #         # -------------------------------
    #         # DATA
    #         # -------------------------------
    #         for line in rec.heavy_line_ids:
    #             if line.water_content and line.dry_density:
    #                 x.append(float(line.water_content))
    #                 y.append(float(line.dry_density))

    #         if len(x) < 3:
    #             rec.heavy_graph_image = False
    #             continue

    #         x = np.array(x)
    #         y = np.array(y)

    #         # -------------------------------
    #         # ✅ HANDLE DUPLICATE X VALUES
    #         # -------------------------------
    #         # If multiple rows have the same water content, average their dry densities
    #         unique_x = np.unique(x)
    #         if len(unique_x) < len(x):
    #             y = np.array([np.mean(y[x == ux]) for ux in unique_x])
    #             x = unique_x

    #         # Sort data
    #         idx = np.argsort(x)
    #         x = x[idx]
    #         y = y[idx]

    #         # -------------------------------
    #         # ✅ EXACT MAX POINT (DATA MADHLI HIGHEST VALUE)
    #         # -------------------------------
    #         max_idx = np.argmax(y)
    #         max_x = float(x[max_idx])
    #         max_y = float(y[max_idx])

    #         # -------------------------------
    #         # ✅ ADD PEAK INTO CURVE DATA (Ensure no duplicate if max_x already exists)
    #         # -------------------------------
    #         if max_x not in x:
    #             x_aug = np.append(x, max_x)
    #             y_aug = np.append(y, max_y)
    #             idx = np.argsort(x_aug)
    #             x_aug = x_aug[idx]
    #             y_aug = y_aug[idx]
    #         else:
    #             x_aug = x
    #             y_aug = y

    #         # -------------------------------
    #         # ✅ SPLINE (PASS THROUGH ALL POINTS)
    #         # -------------------------------
    #         # Note: k must be less than the number of unique points
    #         k_val = min(2, len(x_aug) - 1)
    #         x_smooth = np.linspace(min(x_aug), max(x_aug), 300)
    #         spline = make_interp_spline(x_aug, y_aug, k=k_val)
    #         y_smooth = spline(x_smooth)

    #         # -------------------------------
    #         # PLOT
    #         # -------------------------------
    #         plt.figure(figsize=(10, 5))

    #         # Curve
    #         plt.plot(x_smooth, y_smooth, color='blue', linewidth=2)

    #         # Data points
    #         plt.scatter(x, y, color='orange', s=50, zorder=5)

    #         # Peak lines
    #         plt.axhline(y=max_y, color='black', linewidth=1, linestyle='--')
    #         plt.axvline(x=max_x, color='black', linewidth=1, linestyle='--')

    #         # -------------------------------
    #         # ✅ PEAK POINT & VALUE ANNOTATION
    #         # -------------------------------
    #         plt.scatter(max_x, max_y, color='red', s=80, zorder=6)
            
    #         peak_text = f"OMC: {max_x:.2f}%\nMDD: {max_y:.3f} gm/cc"
    #         plt.annotate(
    #             peak_text,
    #             xy=(max_x, max_y),
    #             xytext=(20, 20),
    #             textcoords='offset points',
    #             fontsize=9,
    #             fontweight='bold',
    #             bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', edgecolor='black', alpha=0.9),
    #             arrowprops=dict(facecolor='black', arrowstyle='->', lw=1)
    #         )

    #         # -------------------------------
    #         # GRID (LAB STYLE)
    #         # -------------------------------
    #         ax = plt.gca()
    #         ax.xaxis.set_minor_locator(MultipleLocator(0.2))
    #         ax.yaxis.set_minor_locator(MultipleLocator(0.01))

    #         plt.grid(which='major', color='black', linewidth=0.6)
    #         plt.grid(which='minor', color='green', linestyle='--', linewidth=0.3)

    #         # -------------------------------
    #         # AXIS LIMITS (DYNAMIC)
    #         # -------------------------------
    #         plt.xlim(min(x) - 0.5, max(x) + 1)
    #         plt.ylim(min(y) - 0.05, max(y) + 0.05)

    #         # -------------------------------
    #         # LABELS
    #         # -------------------------------
    #         plt.title("MODIFIED PROCTOR TEST", fontsize=14)
    #         plt.xlabel("Optimum Moisture Content (%)")
    #         plt.ylabel("Maximum Dry Density (gm/cc)")

    #         plt.tight_layout()

    #         # -------------------------------
    #         # SAVE IMAGE
    #         # -------------------------------
    #         buf = io.BytesIO()
    #         plt.savefig(buf, format='png', dpi=120)
    #         plt.close()
    #         buf.seek(0)

    #         rec.heavy_graph_image = base64.b64encode(buf.read())

    max_dry_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_max_dry_density_conformity", store=True)

    @api.depends('max_dry_density','eln_ref','grade')
    def _compute_max_dry_density_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.max_dry_density_conformity = 'na'
                continue

            record.max_dry_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7fdc8311-213d-4f77-9bc0-9095a7ff265c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7fdc8311-213d-4f77-9bc0-9095a7ff265c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.max_dry_density - record.max_dry_density*mu_value
                    upper = record.max_dry_density + record.max_dry_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.max_dry_density_conformity = 'pass'
                        break
                    else:
                        record.max_dry_density_conformity = 'fail'

    max_dry_density_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_max_dry_density_nabl", store=True)

    @api.depends('max_dry_density','eln_ref','grade')
    def _compute_max_dry_density_nabl(self):
        
        for record in self:
            record.max_dry_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7fdc8311-213d-4f77-9bc0-9095a7ff265c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7fdc8311-213d-4f77-9bc0-9095a7ff265c')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.max_dry_density - record.max_dry_density*mu_value
            upper = record.max_dry_density + record.max_dry_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.max_dry_density_nabl = 'pass'
                break
            else:
                record.max_dry_density_nabl = 'fail'

    optimum_moisture_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_optimum_moisture_conformity", store=True)

    @api.depends('optimum_moisture','eln_ref','grade')
    def _compute_optimum_moisture_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.optimum_moisture_conformity = 'na'
                continue

            record.optimum_moisture_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','dc97b59a-3514-4e1b-8754-5ecfc43bd1a5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','dc97b59a-3514-4e1b-8754-5ecfc43bd1a5')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.optimum_moisture - record.optimum_moisture*mu_value
                    upper = record.optimum_moisture + record.optimum_moisture*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.optimum_moisture_conformity = 'pass'
                        break
                    else:
                        record.optimum_moisture_conformity = 'fail'

    optimum_moisture_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_optimum_moisture_nabl", store=True)

    @api.depends('optimum_moisture','eln_ref','grade')
    def _compute_optimum_moisture_nabl(self):
        
        for record in self:
            record.optimum_moisture_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','dc97b59a-3514-4e1b-8754-5ecfc43bd1a5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','dc97b59a-3514-4e1b-8754-5ecfc43bd1a5')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.optimum_moisture - record.optimum_moisture*mu_value
            upper = record.optimum_moisture + record.optimum_moisture*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.optimum_moisture_nabl = 'pass'
                break
            else:
                record.optimum_moisture_nabl = 'fail'




    # California Bearing Test (CBR)
    cbr_name = fields.Char("Name",default="California Bearing Ratio")
    cbr_visible = fields.Boolean("California Bearing Ratio Visible",compute="_compute_visible")


    cbr_line_ids = fields.One2many('california.bearing.test','parent_id',string="CBR",default=lambda self: self._default_cbr_line_ids())

    plunger_area = fields.Float(string="Plunger Area",digits=(10,3),default=19.625)
    div_load = fields.Float(string="1 division Load",digits=(10,3),default=1.246)

    condition_cbr = fields.Selection([('soaked','Soaked'),('unsoaked','Unsoaked')],string="Condition")

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
    show_cbr = fields.Boolean(string="Show CBR Graph")


    # def action_generate_cbr_chart(self):
    #  for rec in self:
    #     lines = self.env[''].search([
    #         ('parent_id', '=', rec.id)
    #     ], order='penetration asc')

    #     penetration = [l.penetration for l in lines]

    #     s1 = [l.sample1_load for l in lines]
    #     s2 = [l.sample2_load for l in lines]
    #     s3 = [l.sample3_load for l in lines]

    #     # ✅ Increase width only (width=12, height=5)
    #     plt.figure(figsize=(12, 5))

    #     plt.plot(penetration, s1, marker='o', label='Sample-1')
    #     plt.plot(penetration, s2, marker='o', label='Sample-2')
    #     plt.plot(penetration, s3, marker='o', label='Sample-3')

    #     plt.xlabel('Penetration (mm)')
    #     plt.ylabel('Load (Kg/cm²)')
    #     plt.title('CBR Test Graph')

    #     # ✅ Major grid (big squares)
    #     plt.grid(which='major', linestyle='-', linewidth=0.8)

    #     # ✅ Minor grid (small squares inside)
    #     ax = plt.gca()
    #     ax.xaxis.set_minor_locator(AutoMinorLocator(5))
    #     ax.yaxis.set_minor_locator(AutoMinorLocator(5))
    #     plt.grid(which='minor', linestyle=':', linewidth=0.5)

    #     plt.legend()

    #     # Save image
    #     buffer = io.BytesIO()
    #     plt.savefig(buffer, format='png', bbox_inches='tight')
    #     plt.close()

    #     image = base64.b64encode(buffer.getvalue())
    #     buffer.close()

    #     rec.cbr_chart_image = image
    #     rec.cbr_chart_filename = "cbr_chart.png"

    def action_generate_cbr_chart(self):
        for rec in self:

            lines = self.env['california.bearing.test'].search([
                ('parent_id', '=', rec.id)
            ], order='penetration asc')

            # ----------------------------------------
            # Data
            # ----------------------------------------
            penetration = [float(l.penetration) for l in lines]

            s1 = [l.sample1_load or 0 for l in lines]
            s2 = [l.sample2_load or 0 for l in lines]
            s3 = [l.sample3_load or 0 for l in lines]

            # ----------------------------------------
            # Helper
            # ----------------------------------------
            def get_value(sample_list, x_val):
                for i, pen in enumerate(penetration):
                    if abs(pen - x_val) < 0.01:
                        return sample_list[i]
                return 0

            x_points = [2.5, 5]

            # ----------------------------------------
            # Graph
            # ----------------------------------------
            plt.figure(figsize=(12, 5))

            # 👉 IMPORTANT: capture line colors
            line1, = plt.plot(penetration, s1, marker='o', label='Sample-1')
            line2, = plt.plot(penetration, s2, marker='o', label='Sample-2')
            line3, = plt.plot(penetration, s3, marker='o', label='Sample-3')

            colors = [line1.get_color(), line2.get_color(), line3.get_color()]
            samples = [s1, s2, s3]

            # ----------------------------------------
            # Projection lines + values
            # ----------------------------------------
            for sample, color in zip(samples, colors):

                for x in x_points:

                    y = get_value(sample, x)

                    # Vertical line
                    plt.vlines(x=x, ymin=0, ymax=y,
                            colors=color, linewidth=1.5)

                    # Horizontal line
                    plt.hlines(y=y, xmin=0, xmax=x,
                            colors=color, linewidth=1.5)

                    # Point
                    plt.scatter([x], [y], color=color, s=60, zorder=5)

                    # ✅ VALUE DISPLAY (important)
                    plt.text(x + 0.1, y + 0.2,
                            f"{y:.2f}",
                            color=color,
                            fontsize=9,
                            fontweight='bold')

            # ----------------------------------------
            # Labels & grid
            # ----------------------------------------
            plt.xlabel('Penetration in mm', fontweight='bold')
            plt.ylabel('Load (Kg/cm²)', fontweight='bold')
            plt.title('CBR Test Graph')

            plt.grid(which='major', linestyle='-', linewidth=0.8)

            ax = plt.gca()
            ax.xaxis.set_minor_locator(AutoMinorLocator(5))
            ax.yaxis.set_minor_locator(AutoMinorLocator(5))
            plt.grid(which='minor', linestyle=':', linewidth=0.5)

            plt.legend()

            # ----------------------------------------
            # Save
            # ----------------------------------------
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            plt.close()

            image = base64.b64encode(buffer.getvalue())
            buffer.close()

            rec.cbr_chart_image = image
            rec.cbr_chart_filename = "cbr_chart.png"

   

    
    


    cbr_max_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_cbr_max_conformity")

    cbr_max_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_cbr_max_nabl")


    @api.depends('cbr_max','eln_ref','grade')
    def _compute_cbr_max_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.cbr_max_conformity = 'na'
                continue
            record.cbr_max_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15247gtr-2065-4532-814a-3a4c1e884305')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15247gtr-2065-4532-814a-3a4c1e884305')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.cbr_max - record.cbr_max*mu_value
                    upper = record.cbr_max + record.cbr_max*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.cbr_max_conformity = 'pass'
                        break
                    else:
                        record.cbr_max_conformity = 'fail'

    @api.depends('cbr_max','eln_ref','grade')
    def _compute_cbr_max_nabl(self):
        
        for record in self:
            
            record.cbr_max_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15247gtr-2065-4532-814a-3a4c1e884305')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15247gtr-2065-4532-814a-3a4c1e884305')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.cbr_max - record.cbr_max*mu_value
            upper = record.cbr_max + record.cbr_max*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.cbr_max_nabl = 'pass'
                break
            else:
                record.cbr_max_nabl = 'fail'

    cbr_5_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_cbr_5_avg_conformity", store=True)

    @api.depends('cbr_5_avg','eln_ref','grade')
    def _compute_cbr_5_avg_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.cbr_5_avg_conformity = 'na'
                continue

            record.cbr_5_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','775d7276-e9a9-44e6-93d9-b4ee6236298e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','775d7276-e9a9-44e6-93d9-b4ee6236298e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.cbr_5_avg - record.cbr_5_avg*mu_value
                    upper = record.cbr_5_avg + record.cbr_5_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.cbr_5_avg_conformity = 'pass'
                        break
                    else:
                        record.cbr_5_avg_conformity = 'fail'

    cbr_5_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_cbr_5_avg_nabl", store=True)

    @api.depends('cbr_5_avg','eln_ref','grade')
    def _compute_cbr_5_avg_nabl(self):
        
        for record in self:
            record.cbr_5_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','775d7276-e9a9-44e6-93d9-b4ee6236298e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','775d7276-e9a9-44e6-93d9-b4ee6236298e')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.cbr_5_avg - record.cbr_5_avg*mu_value
            upper = record.cbr_5_avg + record.cbr_5_avg*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.cbr_5_avg_nabl = 'pass'
                break
            else:
                record.cbr_5_avg_nabl = 'fail'

    
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
    show_graph_consolidation = fields.Boolean(string="Show Consolidation Graph")

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


    constant_avg_k27_1000_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_constant_avg_k27_1000_conformity", store=True)

    @api.depends('constant_avg_k27_1000','eln_ref','grade')
    def _compute_constant_avg_k27_1000_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.constant_avg_k27_1000_conformity = 'na'
                continue

            record.constant_avg_k27_1000_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b2a605ac-6eb0-4101-a020-0b6b3f6304db')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b2a605ac-6eb0-4101-a020-0b6b3f6304db')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.constant_avg_k27_1000 - record.constant_avg_k27_1000*mu_value
                    upper = record.constant_avg_k27_1000 + record.constant_avg_k27_1000*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.constant_avg_k27_1000_conformity = 'pass'
                        break
                    else:
                        record.constant_avg_k27_1000_conformity = 'fail'

    constant_avg_k27_1000_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_constant_avg_k27_1000_nabl", store=True)

    @api.depends('constant_avg_k27_1000','eln_ref','grade')
    def _compute_constant_avg_k27_1000_nabl(self):
        
        for record in self:
            record.constant_avg_k27_1000_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b2a605ac-6eb0-4101-a020-0b6b3f6304db')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b2a605ac-6eb0-4101-a020-0b6b3f6304db')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.constant_avg_k27_1000 - record.constant_avg_k27_1000*mu_value
            upper = record.constant_avg_k27_1000 + record.constant_avg_k27_1000*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.constant_avg_k27_1000_nabl = 'pass'
                break
            else:
                record.constant_avg_k27_1000_nabl = 'fail'


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

    permeability_avg_k27_1000_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="NABL", compute="_compute_permeability_avg_k27_1000_conformity", store=True)


    @api.depends('permeability_avg_k27_1000','eln_ref','grade')
    def _compute_permeability_avg_k27_1000_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.permeability_avg_k27_1000_conformity = 'na'
                continue

            record.permeability_avg_k27_1000_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5487gt21-ca64-44dd-b0ae-228aacf04965')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5487gt21-ca64-44dd-b0ae-228aacf04965')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.permeability_avg_k27_1000 - record.permeability_avg_k27_1000*mu_value
                    upper = record.permeability_avg_k27_1000 + record.permeability_avg_k27_1000*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.permeability_avg_k27_1000_conformity = 'pass'
                        break
                    else:
                        record.permeability_avg_k27_1000_conformity = 'fail'

    permeability_avg_k27_1000_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_permeability_avg_k27_1000_nabl", store=True)

    @api.depends('permeability_avg_k27_1000','eln_ref','grade')
    def _compute_permeability_avg_k27_1000_nabl(self):
        
        for record in self:
            record.permeability_avg_k27_1000_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5487gt21-ca64-44dd-b0ae-228aacf04965')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5487gt21-ca64-44dd-b0ae-228aacf04965')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.permeability_avg_k27_1000 - record.permeability_avg_k27_1000*mu_value
            upper = record.permeability_avg_k27_1000 + record.permeability_avg_k27_1000*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.permeability_avg_k27_1000_nabl = 'pass'
                break
            else:
                record.permeability_avg_k27_1000_nabl = 'fail'



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

    

    # Direct Shear Test

    direct_shear_name = fields.Char("Name",default="Direct Shear Test")
    direct_shear_visible = fields.Boolean("Direct Shear Test Visible",compute="_compute_visible")
    direct_shear_phi_visible = fields.Boolean("Direct Shear Test Visible",compute="_compute_visible")
    direct_shear_cohesion_visible = fields.Boolean("Direct Shear Test Visible",compute="_compute_visible")

    proving_ring_least = fields.Float(string="Proving Ring Least Count", digits=(12,3),default=0.002)

    least_dial_gauge = fields.Float(string="Least Count of Dial Gauge", digits=(12,2),default=0.01)

    direct_area_specimen = fields.Float(string="Area of Specimen (cm2)", digits=(12,2),default=36.00)

    direct_cp_proving_ring = fields.Float(string="Capacity of Proving Ring", digits=(12,1),default=2.5)

    proving_ring_factor = fields.Float(string="Proving Ring Factor", digits=(12,3),default=0.260)
    proving_ring_num = fields.Integer(string="Proving Ring Number",default=1936)


    direct_shear_ids = fields.One2many("mechanical.direct.shear.test.line", "parent_id", string="Test Readings",default=lambda self: self._default_direct_shear_ids())


    @api.model
    def _default_direct_shear_ids(self):
        default_lines = [
            (0, 0, {'displace_dial_read': '20'}),
            (0, 0, {'displace_dial_read': '40 '}),
            (0, 0, {'displace_dial_read': '60'}),
            (0, 0, {'displace_dial_read': '80'}),
            (0, 0, {'displace_dial_read': '100'}),
            (0, 0, {'displace_dial_read': '120'}),
            (0, 0, {'displace_dial_read': '140'}),
            (0, 0, {'displace_dial_read': '160'}),
            (0, 0, {'displace_dial_read': '180'}),
            (0, 0, {'displace_dial_read': '200'}),
            (0, 0, {'displace_dial_read': '220'}),
            (0, 0, {'displace_dial_read': '240'}),
            (0, 0, {'displace_dial_read': '260'}),
            (0, 0, {'displace_dial_read': '280'}),
            (0, 0, {'displace_dial_read': '300'}),
            (0, 0, {'displace_dial_read': '320'}),
            (0, 0, {'displace_dial_read': '340 '}),
            (0, 0, {'displace_dial_read': '360'}),
            (0, 0, {'displace_dial_read': '380'}),
            (0, 0, {'displace_dial_read': '400'}),
            (0, 0, {'displace_dial_read': '420'}),
            (0, 0, {'displace_dial_read': '440'}),
            (0, 0, {'displace_dial_read': '460'}),
            (0, 0, {'displace_dial_read': '480'}),
            (0, 0, {'displace_dial_read': '500'}),
            (0, 0, {'displace_dial_read': '520'}),
            (0, 0, {'displace_dial_read': '540'}),
            (0, 0, {'displace_dial_read': '560'}),
            (0, 0, {'displace_dial_read': '580'}),
            (0, 0, {'displace_dial_read': '600'}),
            (0, 0, {'displace_dial_read': '620'}),
            (0, 0, {'displace_dial_read': '640 '}),
            (0, 0, {'displace_dial_read': '660'}),
            (0, 0, {'displace_dial_read': '680'}),
            (0, 0, {'displace_dial_read': '700'}),
            (0, 0, {'displace_dial_read': '720'}),
            (0, 0, {'displace_dial_read': '740'}),
            (0, 0, {'displace_dial_read': '760'}),
            (0, 0, {'displace_dial_read': '780'}),
            (0, 0, {'displace_dial_read': '800'}),
            (0, 0, {'displace_dial_read': '820'}),
            (0, 0, {'displace_dial_read': '840'}),
            (0, 0, {'displace_dial_read': '860'}),
            (0, 0, {'displace_dial_read': '880'}),
            (0, 0, {'displace_dial_read': '900'}),
            (0, 0, {'displace_dial_read': '920'}),
            (0, 0, {'displace_dial_read': '940 '}),
            (0, 0, {'displace_dial_read': '960'}),
            (0, 0, {'displace_dial_read': '980'}),
            (0, 0, {'displace_dial_read': '1000'}),
            (0, 0, {'displace_dial_read': '1020'}),
            (0, 0, {'displace_dial_read': '1040'}),
            (0, 0, {'displace_dial_read': '1060'}),
            (0, 0, {'displace_dial_read': '1080'}),
            (0, 0, {'displace_dial_read': '1100'}),
            (0, 0, {'displace_dial_read': '1120'}),
            (0, 0, {'displace_dial_read': '1140'}),
            (0, 0, {'displace_dial_read': '1160'}),
            (0, 0, {'displace_dial_read': '1180'}),
            (0, 0, {'displace_dial_read': '1200'}),
        ]
        return default_lines
    


    # Max shear stress (Kg/cm²)
    max_shear_0_5 = fields.Float("Max Shear Stress 0.5", compute="_compute_final", store=True)
    max_shear_1_0 = fields.Float("Max Shear Stress 1.0", compute="_compute_final", store=True)
    max_shear_1_5 = fields.Float("Max Shear Stress 1.5", compute="_compute_final", store=True)

    # Converted (Ton/m²)
    normal_stress_0_5 = fields.Float(string="Normal Stress (Ton/m2)", compute="_compute_final",digits=(10,1))  # 5.5
    normal_stress_1_0 = fields.Float(string="Normal Stress (Ton/m2)", compute="_compute_final",digits=(10,1))  # 11
    normal_stress_1_5 = fields.Float(string="Normal Stress (Ton/m2)", compute="_compute_final",digits=(10,1))  # 16.5

    shear_ton_0_5 = fields.Float("Max. Shear Stress (Ton/m2) ", store=True,digits=(10,1), compute="_compute_final")
    shear_ton_1_0 = fields.Float("Max. Shear Stress (Ton/m2) ", store=True,digits=(10,1), compute="_compute_final")
    shear_ton_1_5 = fields.Float("Max. Shear Stress (Ton/m2) ", store=True,digits=(10,1), compute="_compute_final")

    # Final results
    tan_phi = fields.Float("tanφ", compute="_compute_final", store=True,digits=(10,4))
    angle_phi = fields.Float("Angle of Internal Friction (φ) (deg) ",compute="_compute_final",digits=(10,1))
    cohesion = fields.Float("Cohesion (Ton/m²)",  compute="_compute_final",digits=(10,1))


    angle_phi_kg_cm2 = fields.Float("Angle of Internal Friction (φ) (deg) ",digits=(10,1),compute="_compute_final")
    cohesion_kg_cm2 = fields.Float("Cohesion (kg/cm²)",  digits=(10,1),compute="_compute_final")


    # @api.depends(
    #     'normal_stress_0_5',
    #     'normal_stress_1_0',
    #     'normal_stress_1_5',
    #     'shear_ton_0_5',
    #     'shear_ton_1_0',
    #     'shear_ton_1_5'
    # )
    # def _compute_final(self):
    #     for rec in self:
    #         try:
    #             n = 3

    #             # ---------------------------------
    #             # ✅ SLOPE (Excel: =SLOPE(P,Q))
    #             # P = normal (Y), Q = shear (X)
    #             # ---------------------------------
    #             x1 = [
    #                 rec.shear_ton_0_5,
    #                 rec.shear_ton_1_0,
    #                 rec.shear_ton_1_5
    #             ]

    #             y1 = [
    #                 rec.normal_stress_0_5,
    #                 rec.normal_stress_1_0,
    #                 rec.normal_stress_1_5
    #             ]

    #             sum_x1 = sum(x1)
    #             sum_y1 = sum(y1)
    #             sum_xy1 = sum(x1[i] * y1[i] for i in range(n))
    #             sum_x1_2 = sum(val * val for val in x1)

    #             denom1 = (n * sum_x1_2) - (sum_x1 ** 2)

    #             if denom1 != 0:
    #                 rec.tan_phi = ((n * sum_xy1) - (sum_x1 * sum_y1)) / denom1
    #             else:
    #                 rec.tan_phi = 0.0

    #             # ---------------------------------
    #             # ✅ ANGLE φ
    #             # ---------------------------------
    #             rec.angle_phi = math.degrees(math.atan(rec.tan_phi))

    #             # ---------------------------------
    #             # ✅ INTERCEPT (Excel: =INTERCEPT(Q,P))
    #             # Q = shear (Y), P = normal (X)
    #             # ---------------------------------
    #             x2 = [
    #                 rec.normal_stress_0_5,
    #                 rec.normal_stress_1_0,
    #                 rec.normal_stress_1_5
    #             ]

    #             y2 = [
    #                 rec.shear_ton_0_5,
    #                 rec.shear_ton_1_0,
    #                 rec.shear_ton_1_5
    #             ]

    #             sum_x2 = sum(x2)
    #             sum_y2 = sum(y2)
    #             sum_xy2 = sum(x2[i] * y2[i] for i in range(n))
    #             sum_x2_2 = sum(val * val for val in x2)

    #             denom2 = (n * sum_x2_2) - (sum_x2 ** 2)

    #             if denom2 != 0:
    #                 m2 = ((n * sum_xy2) - (sum_x2 * sum_y2)) / denom2
    #                 rec.cohesion = (sum_y2 - m2 * sum_x2) / n
    #             else:
    #                 rec.cohesion = 0.0

    #         except:
    #             rec.tan_phi = 0.0
    #             rec.angle_phi = 0.0
    #             rec.cohesion = 0.0

    

    
    # @api.depends('direct_shear_ids.shear_stress_0_5',
    #          'direct_shear_ids.shear_stress_1_0',
    #          'direct_shear_ids.shear_stress_1_5','shear_ton_0_5',
    # 'shear_ton_1_0',
    # 'shear_ton_1_5')
    # def _compute_final(self):
    #  for rec in self:

    #     # 1. Get MAX shear stress from lines
    #     rec.max_shear_0_5 = max(rec.direct_shear_ids.mapped('shear_stress_0_5') or [0])
    #     rec.max_shear_1_0 = max(rec.direct_shear_ids.mapped('shear_stress_1_0') or [0])
    #     rec.max_shear_1_5 = max(rec.direct_shear_ids.mapped('shear_stress_1_5') or [0])

      
       

    #     x = np.array([
    #         rec.normal_stress_0_5,
    #         rec.normal_stress_1_0,
    #         rec.normal_stress_1_5
    #     ])

    #     y = np.array([
    #         rec.shear_ton_0_5,
    #         rec.shear_ton_1_0,
    #         rec.shear_ton_1_5
    #     ])

    #     if len(x) >= 2 and all(y):
    #         m, c = np.polyfit(x, y, 1)

    #         rec.tan_phi = m          # → 3.3312 ✅
    #         rec.cohesion = c         # → 1.5 ✅
    #     else:
    #         rec.tan_phi = 0
    #         rec.cohesion = 0

    #     rec.angle_phi = math.degrees(math.atan(rec.tan_phi)) if rec.tan_phi else 0

    # @api.depends(
    # 'direct_shear_ids.shear_stress_0_5',
    # 'direct_shear_ids.shear_stress_1_0',
    # 'direct_shear_ids.shear_stress_1_5'
    # )
    # def _compute_final(self):
    #     for rec in self:

    #         # ----------------------------------------
    #         # MAX SHEAR
    #         # ----------------------------------------
    #         rec.max_shear_0_5 = max(rec.direct_shear_ids.mapped('shear_stress_0_5') or [0])
    #         rec.max_shear_1_0 = max(rec.direct_shear_ids.mapped('shear_stress_1_0') or [0])
    #         rec.max_shear_1_5 = max(rec.direct_shear_ids.mapped('shear_stress_1_5') or [0])

    #         # ----------------------------------------
    #         # ✅ NORMAL STRESS (CONVERT)
    #         # ----------------------------------------
    #         rec.normal_stress_0_5 = (0.5 * 9.807)
    #         rec.normal_stress_1_0 = (1.0 * 9.807)
    #         rec.normal_stress_1_5 = (1.5 * 9.807)

    #         # ----------------------------------------
    #         # ✅ SHEAR STRESS (CONVERT)
    #         # ----------------------------------------
    #         rec.shear_ton_0_5 = (rec.max_shear_0_5 or 0) * 9.807
    #         rec.shear_ton_1_0 = (rec.max_shear_1_0 or 0) * 9.807
    #         rec.shear_ton_1_5 = (rec.max_shear_1_5 or 0) * 9.807

    #         # ----------------------------------------
    #         # LINE FIT
    #         # ----------------------------------------
    #         x = np.array([
    #             rec.normal_stress_0_5,
    #             rec.normal_stress_1_0,
    #             rec.normal_stress_1_5
    #         ])

    #         y = np.array([
    #             rec.shear_ton_0_5,
    #             rec.shear_ton_1_0,
    #             rec.shear_ton_1_5
    #         ])

    #         # CLEAN DATA
    #         data = [(xi, yi) for xi, yi in zip(x, y) if xi > 0 and yi > 0]

    #         if len(data) < 2:
    #             rec.tan_phi = 0
    #             rec.cohesion = 0
    #             rec.angle_phi = 0
    #             continue

    #         x_clean = np.array([d[0] for d in data])
    #         y_clean = np.array([d[1] for d in data])

    #         if len(set(x_clean)) < 2:
    #             rec.tan_phi = 0
    #             rec.cohesion = 0
    #             rec.angle_phi = 0
    #             continue

    #         try:
    #             m, c = np.polyfit(x_clean, y_clean, 1)

    #             rec.tan_phi = m
    #             rec.cohesion = c
    #             rec.angle_phi = math.degrees(math.atan(m))

    #         except Exception:
    #             rec.tan_phi = 0
    #             rec.cohesion = 0
    #             rec.angle_phi = 0

    @api.depends(
        'direct_shear_ids.shear_stress_0_5',
        'direct_shear_ids.shear_stress_1_0',
        'direct_shear_ids.shear_stress_1_5'
    )
    def _compute_final(self):
        for rec in self:

            # ----------------------------------------
            # DEFAULT VALUES (NO ERROR 🔥)
            # ----------------------------------------
            rec.normal_stress_0_5 = 0
            rec.normal_stress_1_0 = 0
            rec.normal_stress_1_5 = 0

            rec.max_shear_0_5 = 0
            rec.max_shear_1_0 = 0
            rec.max_shear_1_5 = 0

            rec.shear_ton_0_5 = 0
            rec.shear_ton_1_0 = 0
            rec.shear_ton_1_5 = 0

            rec.tan_phi = 0
            rec.cohesion = 0
            rec.angle_phi = 0

            rec.angle_phi_kg_cm2 = 0
            rec.cohesion_kg_cm2 = 0

            # ----------------------------------------
            # 1. MAX SHEAR
            # ----------------------------------------
            rec.max_shear_0_5 = max(rec.direct_shear_ids.mapped('shear_stress_0_5') or [0])
            rec.max_shear_1_0 = max(rec.direct_shear_ids.mapped('shear_stress_1_0') or [0])
            rec.max_shear_1_5 = max(rec.direct_shear_ids.mapped('shear_stress_1_5') or [0])

            # ----------------------------------------
            # 2. NORMAL STRESS
            # ----------------------------------------
            rec.normal_stress_0_5 = 0.5 * 9.807
            rec.normal_stress_1_0 = 1.0 * 9.807
            rec.normal_stress_1_5 = 1.5 * 9.807

            # ----------------------------------------
            # 3. SHEAR CONVERT
            # ----------------------------------------
            rec.shear_ton_0_5 = rec.max_shear_0_5 * 9.807
            rec.shear_ton_1_0 = rec.max_shear_1_0 * 9.807
            rec.shear_ton_1_5 = rec.max_shear_1_5 * 9.807

            # ----------------------------------------
            # 4. ENGINEERING (polyfit)
            # ----------------------------------------
            x = np.array([
                rec.normal_stress_0_5,
                rec.normal_stress_1_0,
                rec.normal_stress_1_5
            ])

            y = np.array([
                rec.shear_ton_0_5,
                rec.shear_ton_1_0,
                rec.shear_ton_1_5
            ])

            data = [(xi, yi) for xi, yi in zip(x, y) if xi > 0 and yi > 0]

            if len(data) >= 2 and len(set([d[0] for d in data])) >= 2:
                try:
                    m, c = np.polyfit(x, y, 1)
                    rec.tan_phi = m
                    rec.cohesion = c
                    rec.angle_phi = math.degrees(math.atan(m))
                except Exception:
                    pass

            # ----------------------------------------
            # 5. EXCEL EXACT (🔥 FINAL)
            # ----------------------------------------
            x_excel = [0.5, 1.0, 1.5]
            y_excel = [
                rec.max_shear_0_5,
                rec.max_shear_1_0,
                rec.max_shear_1_5
            ]

            data_excel = [(xi, yi) for xi, yi in zip(x_excel, y_excel) if yi > 0]

            if len(data_excel) >= 2:

                x_vals = [d[0] for d in data_excel]
                y_vals = [d[1] for d in data_excel]

                n = len(x_vals)

                sum_x = sum(x_vals)
                sum_y = sum(y_vals)
                sum_xy = sum(xi * yi for xi, yi in zip(x_vals, y_vals))
                sum_x2 = sum(xi * xi for xi in x_vals)

                denominator = (n * sum_x2) - (sum_x ** 2)

                if denominator != 0:
                    m_excel = ((n * sum_xy) - (sum_x * sum_y)) / denominator
                    c_excel = (sum_y - (m_excel * sum_x)) / n

                    angle = math.degrees(math.atan(m_excel))

                    # ✅ Excel rounding
                    rec.angle_phi_kg_cm2 = float(
                        Decimal(angle).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                    )

                    rec.cohesion_kg_cm2 = float(
                        Decimal(c_excel).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                    )


    



    

   

        


    direct_graph_image = fields.Binary("Shear Test Graph", readonly=True)
    graph_filename = fields.Char("Filename")

    show_direct_graph = fields.Boolean(string="Show Direct Shear Graph")

  
    # def action_generate_direct_graph(self):
     
    #  for rec in self:

    #         x = np.array([
    #             rec.normal_stress_0_5,
    #             rec.normal_stress_1_0,
    #             rec.normal_stress_1_5
    #         ])

    #         y = np.array([
    #             rec.shear_ton_0_5,
    #             rec.shear_ton_1_0,
    #             rec.shear_ton_1_5
    #         ])

    #         plt.figure(figsize=(8, 5))

    #         # Scatter
    #         plt.scatter(x, y)

    #         # Line (correct)
    #         m = rec.tan_phi
    #         c = rec.cohesion

    #         x_line = np.linspace(0, 20, 100)
    #         y_line = m * x_line + c
    #         plt.plot(x_line, y_line, color='red')

    #         # Dotted backward
    #         x_back = np.linspace(0, min(x), 50)
    #         y_back = m * x_back + c
    #         plt.plot(x_back, y_back, linestyle='dotted', color='blue')

    #         # Labels
    #         plt.title("DIRECT SHEAR TEST GRAPH")
    #         plt.xlabel("Normal Stress (Ton/m²)")
    #         plt.ylabel("Max Shear Stress (Ton/m²)")

    #         plt.xlim(0, 20)
    #         plt.ylim(0, 10)

    #         # Excel-style grid
    #         plt.minorticks_on()
    #         plt.grid(which='major', color='green', linewidth=0.5)
    #         plt.grid(which='minor', color='green', linewidth=0.2)

    #         # Save image
    #         buffer = io.BytesIO()
    #         plt.savefig(buffer, format='png')
    #         buffer.seek(0)

    #         rec.direct_graph_image = base64.b64encode(buffer.read())
    #         rec.graph_filename = "shear_graph.png"

    #         buffer.close()
    #         plt.close()


    def action_generate_direct_graph(self):

        for rec in self:

            x = np.array([
                rec.normal_stress_0_5,
                rec.normal_stress_1_0,
                rec.normal_stress_1_5
            ])

            y = np.array([
                rec.shear_ton_0_5,
                rec.shear_ton_1_0,
                rec.shear_ton_1_5
            ])

            plt.figure(figsize=(8, 5))

            # Scatter
            plt.scatter(x, y)

            # ✅ BEST FIT LINE (AUTO TANGENT)
            m, c = np.polyfit(x, y, 1)

            x_line = np.linspace(0, 20, 100)
            y_line = m * x_line + c
            plt.plot(x_line, y_line, color='red')

            # Dotted backward
            x_back = np.linspace(0, min(x), 50)
            y_back = m * x_back + c
            plt.plot(x_back, y_back, linestyle='dotted', color='blue')

            # Labels
            plt.title("DIRECT SHEAR TEST GRAPH")
            plt.xlabel("Normal Stress (Ton/m²)")
            plt.ylabel("Max Shear Stress (Ton/m²)")

            plt.xlim(0, 20)
            plt.ylim(0, 10)

            # Grid
            plt.minorticks_on()
            plt.grid(which='major', color='green', linewidth=0.5)
            plt.grid(which='minor', color='green', linewidth=0.2)

            # Save image
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)

            rec.direct_graph_image = base64.b64encode(buffer.read())
            rec.graph_filename = "shear_graph.png"

            buffer.close()
            plt.close()

    

    angle_phi_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_angle_phi_conformity", store=True)

    @api.depends('angle_phi','eln_ref','grade')
    def _compute_angle_phi_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.angle_phi_conformity = 'na'
                continue

            record.angle_phi_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','946ba303-bb07-48c6-981e-dcd4d7a6b1eb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','946ba303-bb07-48c6-981e-dcd4d7a6b1eb')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.angle_phi - record.angle_phi*mu_value
                    upper = record.angle_phi + record.angle_phi*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.angle_phi_conformity = 'pass'
                        break
                    else:
                        record.angle_phi_conformity = 'fail'

    angle_phi_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_angle_phi_nabl", store=True)

    @api.depends('angle_phi','eln_ref','grade')
    def _compute_angle_phi_nabl(self):
        
        for record in self:
            record.angle_phi_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','946ba303-bb07-48c6-981e-dcd4d7a6b1eb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','946ba303-bb07-48c6-981e-dcd4d7a6b1eb')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.angle_phi - record.angle_phi*mu_value
            upper = record.angle_phi + record.angle_phi*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.angle_phi_nabl = 'pass'
                break
            else:
                record.angle_phi_nabl = 'fail'

    cohesion_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_cohesion_conformity", store=True)

    @api.depends('cohesion','eln_ref','grade')
    def _compute_cohesion_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.cohesion_conformity = 'na'
                continue

            record.cohesion_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','91fabf52-7b42-4544-9125-495d98fe4d6a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','91fabf52-7b42-4544-9125-495d98fe4d6a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.cohesion - record.cohesion*mu_value
                    upper = record.cohesion + record.cohesion*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.cohesion_conformity = 'pass'
                        break
                    else:
                        record.cohesion_conformity = 'fail'

    cohesion_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_cohesion_nabl", store=True)

    @api.depends('cohesion','eln_ref','grade')
    def _compute_cohesion_nabl(self):
        
        for record in self:
            record.cohesion_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','91fabf52-7b42-4544-9125-495d98fe4d6a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','91fabf52-7b42-4544-9125-495d98fe4d6a')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.cohesion - record.cohesion*mu_value
            upper = record.cohesion + record.cohesion*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.cohesion_nabl = 'pass'
                break
            else:
                record.cohesion_nabl = 'fail'







    

    





    
   

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
            record.atterberg_visible = False
            record.plastic_limit_visible = False
            record.light_comp_visible = False
            record.light_comp_omc_visible = False
            record.light_comp_mdd_visible = False
            record.heavy_omc_visible = False
            record.heavy_mdd_visible = False
            record.heavy_visible = False
            record.cbr_visible = False
            record.constant_head_visible = False
            record.permeability_visible = False
            record.sand_replace_visible = False
            record.core_cutter_visible = False
            record.consolidation_visible  = False
            record.direct_shear_visible  = False
            record.direct_shear_phi_visible  = False
            record.direct_shear_cohesion_visible  = False
            
            


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
                
                if sample.internal_id == '7606fd1e-91b2-4433-a4df-c717bd8283be':
                    record.light_comp_omc_visible = True

                if sample.internal_id == '90c1d609-0e28-4989-b840-9604bcfbfac2':
                    record.light_comp_mdd_visible = True

                if sample.internal_id == '3210vbf-20fb-4843-aa0e-2ee981be0d7c':
                    record.heavy_visible = True

                if sample.internal_id == 'dc97b59a-3514-4e1b-8754-5ecfc43bd1a5':
                    record.heavy_omc_visible = True
                
                if sample.internal_id == '7fdc8311-213d-4f77-9bc0-9095a7ff265c':
                    record.heavy_mdd_visible = True

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

                if sample.internal_id == '21457888hhhllly1-ca64-44dd-b0ae-3214hhhtr':
                    record.direct_shear_visible = True

                if sample.internal_id == '946ba303-bb07-48c6-981e-dcd4d7a6b1eb':
                    record.direct_shear_phi_visible = True

                if sample.internal_id == '91fabf52-7b42-4544-9125-495d98fe4d6a':
                    record.direct_shear_cohesion_visible = True

                if sample.internal_id == '582ac73a-3f86-4c7a-8dda-04357ade5617':
                    record.atterberg_visible = True

                

                    
                
                

    
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

            # Direct Shear Test
            if result.parameter.internal_id == '21457888hhhllly1-ca64-44dd-b0ae-3214hhhtr':
                result.calculated = True
            
            # Direct Shear Test -- Angle of Internal Friction
            if result.parameter.internal_id == '946ba303-bb07-48c6-981e-dcd4d7a6b1eb':
                result.calculated = True
                result.result_char = round(self.angle_phi,2)
                if self.angle_phi_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Direct Shear Test -- Cohesion
            if result.parameter.internal_id == '91fabf52-7b42-4544-9125-495d98fe4d6a':
                result.calculated = True
                result.result_char = round(self.cohesion,2)
                if self.cohesion_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

                # Texture
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

            # Light Compaction Test -- OMC
            if result.parameter.internal_id == '7606fd1e-91b2-4433-a4df-c717bd8283be':
                result.calculated = True
                result.result_char = round(self.light_optimum_moisture,2)
                if self.light_optimum_moisture_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Light Compaction Test -- MDD
            if result.parameter.internal_id == '90c1d609-0e28-4989-b840-9604bcfbfac2':
                result.calculated = True
                result.result_char = round(self.light_max_dry_density,2)
                if self.light_max_dry_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Heavy Compaction
            if result.parameter.internal_id == '3210vbf-20fb-4843-aa0e-2ee981be0d7c':
                result.calculated = True

            # Heavy Compaction -- OMC
            if result.parameter.internal_id == 'dc97b59a-3514-4e1b-8754-5ecfc43bd1a5':
                result.calculated = True
                result.result_char = round(self.optimum_moisture,2)
                if self.optimum_moisture_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Heavy Compaction -- MDD
            if result.parameter.internal_id == '7fdc8311-213d-4f77-9bc0-9095a7ff265c':
                result.calculated = True
                result.result_char = round(self.max_dry_density,2)
                if self.max_dry_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # California Bearing Test 
           
             # California Bearing Test 2.5mm
            if result.parameter.internal_id == '15247gtr-2065-4532-814a-3a4c1e884305':
                result.calculated = True
                result.result_char = round(self.cbr_max,2)
                if self.cbr_max_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # California Bearing Test 5mm
            # if result.parameter.internal_id == '775d7276-e9a9-44e6-93d9-b4ee6236298e':
            #     result.calculated = True
            #     result.result_char = round(self.cbr_5_avg,2)
            #     if self.cbr_5_avg_nabl == 'pass':
            #         result.nabl_status = 'nabl'
            #     else:
            #         result.nabl_status = 'non-nabl'
            #     continue

            # Constant Head
            if result.parameter.internal_id == 'b2a605ac-6eb0-4101-a020-0b6b3f6304db':
                result.calculated = True
                result.result_char = round(self.constant_avg_k27_1000,3)
                if self.constant_avg_k27_1000_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Permeability Falling Head
            if result.parameter.internal_id == '5487gt21-ca64-44dd-b0ae-228aacf04965':
                result.calculated = True
                result.result_char = round(self.permeability_avg_k27_1000,6)
                if self.permeability_avg_k27_1000_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Sand Replacement
            if result.parameter.internal_id == 'a4e6c3fa-e760-425a-a09f-e66cb6bb4c52':
                result.calculated = True

            # Core Cutter Test
            if result.parameter.internal_id == '183134ba-9616-467f-acb9-af738740d86e':
                result.calculated = True

            # Atterberg's Limit
            if result.parameter.internal_id == '582ac73a-3f86-4c7a-8dda-04357ade5617':
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
        current_user = self.env.user

        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            # Check if user is in Lerm Admin group
            if (
                current_user.has_group('lerm_civil.kes_admin_access_group')
                or current_user.has_group('lerm_civil.lerm_sample_verification')
                or current_user.has_group('lerm_civil.lerm_sample_approval')
            ):
                # Admin sees all parameters
                parameter_ids = record.eln_ref.parameters_result.mapped('parameter').ids
            else:
                # Other users only see parameters assigned to them
                user_param_results = record.eln_ref.parameters_result.filtered(
                    lambda r: r.technician and r.technician.id == current_user.id
                )
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
    wt_retained = fields.Float(string="Wt. Retained in gms",digits=(10,3))
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


class DirectShearTestLine(models.Model):
    _name = "mechanical.direct.shear.test.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="Sr.No",readonly=True, copy=False, default=1)

    displace_dial_read = fields.Float(string="Displacement Dial Reading", digits=(12,1))
    direct_displacement = fields.Float(string="Displacment (δ) mm", digits=(12,2))
    area_corrected = fields.Float(string="Area Correction",digits=(12, 2),compute="_compute_values",store=True)



    shear_load_0_5_div = fields.Float(string="Division 0.5 Shear Load",digits=(12, 2))

    shear_load_0_5_kg = fields.Float(string="Kg 0.5 Shear Load",digits=(12, 3),compute="_compute_values",store=True)

    shear_stress_0_5 = fields.Float(string="Shear Stress (Kg/cm2) - 0.5",digits=(12, 2),compute="_compute_values",store=True)

    @api.depends(
    'displace_dial_read',
    'shear_load_0_5_div',
    'parent_id.proving_ring_least',
    'parent_id.direct_area_specimen',
    'parent_id.proving_ring_factor'
)
    def _compute_values(self):
     for rec in self:

        # 1. Displacement
        if rec.parent_id.proving_ring_least:
            rec.direct_displacement = (
                rec.displace_dial_read * rec.parent_id.proving_ring_least
            )
        else:
            rec.direct_displacement = 0.0

        # 2. Area Correction
        if rec.parent_id.direct_area_specimen:
            rec.area_corrected = (
                rec.parent_id.direct_area_specimen *
                (1 - (rec.direct_displacement / 6))
            )
        else:
            rec.area_corrected = 0.0

        # 3. Shear Load (Kg)
        if rec.parent_id.proving_ring_factor:
            rec.shear_load_0_5_kg = (
                rec.shear_load_0_5_div * rec.parent_id.proving_ring_factor
            )
        else:
            rec.shear_load_0_5_kg = 0.0

        # 4. Shear Stress (Kg/cm²)
        if rec.area_corrected:
            rec.shear_stress_0_5 = (
                rec.shear_load_0_5_kg / rec.area_corrected
            )
        else:
            rec.shear_stress_0_5 = 0.0


    shear_load_1_0_div = fields.Float(string="Division 1.0 Shear Load",digits=(12, 2))

    shear_load_1_0_kg = fields.Float(string="Kg 1.0 Shear Load",digits=(12, 3),compute="_compute_values1",store=True)

    shear_stress_1_0 = fields.Float(string="Shear Stress (Kg/cm2) - 1.0",digits=(12, 4),compute="_compute_values1",store=True)

    @api.depends(
    'displace_dial_read',
    'shear_load_1_0_div',
    'parent_id.proving_ring_least',
    'parent_id.direct_area_specimen',
    'parent_id.proving_ring_factor'
)
    def _compute_values1(self):
     for rec in self:

        # 1. Displacement
        if rec.parent_id.proving_ring_least:
            rec.direct_displacement = (
                rec.displace_dial_read * rec.parent_id.proving_ring_least
            )
        else:
            rec.direct_displacement = 0.0

        # 2. Area Correction
        if rec.parent_id.direct_area_specimen:
            rec.area_corrected = (
                rec.parent_id.direct_area_specimen *
                (1 - (rec.direct_displacement / 6))
            )
        else:
            rec.area_corrected = 0.0

        # 3. Shear Load (Kg)
        if rec.parent_id.proving_ring_factor:
            rec.shear_load_1_0_kg = (
                rec.shear_load_1_0_div * rec.parent_id.proving_ring_factor
            )
        else:
            rec.shear_load_1_0_kg = 0.0

        # 4. Shear Stress (Kg/cm²)
        if rec.area_corrected:
            rec.shear_stress_1_0 = (
                rec.shear_load_1_0_kg / rec.area_corrected
            )
        else:
            rec.shear_stress_1_0 = 0.0


    shear_load_1_5_div = fields.Float(string="Division 1.5 Shear Load",digits=(12, 2))

    shear_load_1_5_kg = fields.Float(string="Kg 1.5 Shear Load",digits=(12, 3),compute="_compute_values2",store=True)

    shear_stress_1_5 = fields.Float(string="Shear Stress (Kg/cm2) - 1.5",digits=(12, 4),compute="_compute_values2",store=True)

    @api.depends(
    'displace_dial_read',
    'shear_load_1_5_div',
    'parent_id.proving_ring_least',
    'parent_id.direct_area_specimen',
    'parent_id.proving_ring_factor'
)
    def _compute_values2(self):
     for rec in self:

        # 1. Displacement
        if rec.parent_id.proving_ring_least:
            rec.direct_displacement = (
                rec.displace_dial_read * rec.parent_id.proving_ring_least
            )
        else:
            rec.direct_displacement = 0.0

        # 2. Area Correction
        if rec.parent_id.direct_area_specimen:
            rec.area_corrected = (
                rec.parent_id.direct_area_specimen *
                (1 - (rec.direct_displacement / 6))
            )
        else:
            rec.area_corrected = 0.0

        # 3. Shear Load (Kg)
        if rec.parent_id.proving_ring_factor:
            rec.shear_load_1_5_kg = (
                rec.shear_load_1_5_div * rec.parent_id.proving_ring_factor
            )
        else:
            rec.shear_load_1_5_kg = 0.0

        # 4. Shear Stress (Kg/cm²)
        if rec.area_corrected:
            rec.shear_stress_1_5 = (
                rec.shear_load_1_5_kg / rec.area_corrected
            )
        else:
            rec.shear_stress_1_5 = 0.0

    

    

   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(DirectShearTestLine, self).create(vals)

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