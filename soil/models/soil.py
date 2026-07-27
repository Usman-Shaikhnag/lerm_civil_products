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
from matplotlib.ticker import AutoMinorLocator
from scipy.interpolate import PchipInterpolator

from matplotlib.ticker import MultipleLocator, StrMethodFormatter




class Soil(models.Model):
    _name = "mechanical.soil"
    _inherit = "lerm.eln"
    _rec_name = "name_soil"


    name_soil = fields.Char("Name",default="Soil")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    temp = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)

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


    

    # Grain Sieve Analysis
    sieve_name = fields.Char("Name",default="Grain Sieve Analysis")
    sieve_visible = fields.Boolean("Grain Sieve Analysis Visible",compute="_compute_visible")


    report_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non NABL'),
        ],
        string="Report Type",
        default='nabl',
        required=True,
    )

    sieve_nabl = fields.Selection(
    [('pass', 'Pass'), ('fail', 'Fail')],
    compute="_compute_sieve_nabl",
    store=True
)

    @api.depends('report_type')
    def _compute_sieve_nabl(self):
     for rec in self:
        rec.sieve_nabl = 'pass' if rec.report_type == 'nabl' else 'fail'
 
    sieve_analysis_child_lines = fields.One2many('mechanical.soil.sieve.analysis.line','parent_id',string="Sieve Analysis",default=lambda self: self._default_sieve_analysis_child_lines())

    boulder = fields.Float(string="% Boulders ",compute="_compute_boulder")

    gravel = fields.Float(string="%Gravels",compute="_compute_gravel")
    sand = fields.Float(string="%Sand",compute="_compute_sand")
    silt_clay = fields.Float(string="%Clay",compute="_compute_clay_fraction")

    silt = fields.Float(string="%Silt",compute="_compute_silt")

    silt_clay_total = fields.Float(
    string="%Silt + Clay",
    compute="_compute_silt_clay_total",
    store=True
)
    
    wt_of_sample = fields.Float(string="Weight of Sample, gms")

    @api.depends('silt', 'silt_clay')
    def _compute_silt_clay_total(self):
     for record in self:
        record.silt_clay_total = (record.silt or 0.0) + (record.silt_clay or 0.0)

    @api.depends('sieve_analysis_child_lines.passing_percent', 'sieve_analysis_child_lines.sieve_size')
    def _compute_clay_fraction(self):
        for record in self:
            total = 0.0
            for line in record.sieve_analysis_child_lines:
                sieve_text = str(line.sieve_size).strip()
                match = re.search(r'([\d\.]+)', sieve_text)
                if not match:
                    continue
                try:
                    size_value = float(match.group(1))
                except ValueError:
                    continue

                # µ to mm conversion
                if 'µ' in sieve_text or 'mic' in sieve_text.lower():
                    size_mm = size_value / 1000.0
                else:
                    size_mm = size_value

                # range check for clay fraction (< 0.002 mm)
                if 0 <= size_mm < 0.002:
                    total += line.passing_percent or 0.0

            record.silt_clay = total  # Use a separate field for clay fraction


    @api.depends('sieve_analysis_child_lines.passing_percent', 'sieve_analysis_child_lines.sieve_size')
    def _compute_silt(self):
        for record in self:
            total = 0.0
            for line in record.sieve_analysis_child_lines:
                sieve_text = str(line.sieve_size).strip()
                match = re.search(r'([\d\.]+)', sieve_text)
                if not match:
                    continue
                try:
                    size_value = float(match.group(1))
                except ValueError:
                    continue

                # µ ते mm convert करा
                if 'µ' in sieve_text or 'mic' in sieve_text.lower():
                    size_mm = size_value / 1000.0
                else:
                    size_mm = size_value

                # range check (0.002 - 0.075 mm)
                if 0.002 <= size_mm <= 0.075:
                    total += line.passing_percent or 0.0

            record.silt = total

    # ---------- Gravel ----------
    @api.depends('sieve_analysis_child_lines.percent_retained', 'sieve_analysis_child_lines.sieve_size')
    def _compute_gravel(self):
        for record in self:
            total = 0.0
            for line in record.sieve_analysis_child_lines:
                sieve_text = str(line.sieve_size).strip()
                match = re.search(r'([\d\.]+)', sieve_text)
                if not match:
                    continue
                try:
                    size_value = float(match.group(1))
                except ValueError:
                    continue

                # µ ते mm convert करा
                if 'µ' in sieve_text or 'mic' in sieve_text.lower():
                    size_mm = size_value / 1000.0
                else:
                    size_mm = size_value

                # range check (4.75 - 80 mm)
                if 4.75 <= size_mm <= 79.99:
                    total += line.percent_retained or 0.0

            record.gravel = total

    @api.depends('sieve_analysis_child_lines.percent_retained')
    def _compute_boulder(self):
        for record in self:
            boulder_sum = 0.0

            for line in record.sieve_analysis_child_lines:
                size_str = str(line.sieve_size).replace("µ", "e-3").replace("mm", "")
                try:
                    # µm → mm conversion
                    if "e-3" in size_str:
                        size_val = float(size_str) * 0.001
                    else:
                        size_val = float(size_str)
                except ValueError:
                    size_val = 0.0

                # Boulder range: sieve size > 79.99 mm
                if size_val > 79.99:
                    boulder_sum += line.percent_retained or 0.0

            record.boulder = boulder_sum

    @api.depends('gravel', 'silt_clay')
    def _compute_sand(self):
        for record in self:
            record.sand = 100 - ((record.gravel or 0.0) + (record.silt or 0.0))

    d60 = fields.Float(string="D60 (mm)",compute="_compute_d60",digits=(12,5))
    d30 = fields.Float(string="D30 (mm)",compute="_compute_d30",digits=(12,5))
    d10 = fields.Float(string="D10 (mm)",compute="_compute_d10",digits=(12,5))
    cu = fields.Float(string="Cu = D60/D10",compute="_compute_cu",digits=(12,5))
    cc = fields.Float(string="Cc = D30^2/D10* D60",compute="_compute_cc_slive",digits=(12,5))


    import math

    def _get_sieve_mm(self, sieve):
     sieve = str(sieve).strip().replace('µ', 'μ')

     mapping = {
        '40mm': 40.0,
        '25mm': 25.0,
        '19mm': 19.0,
        '12.5mm': 12.5,
        '10mm': 10.0,
        '6.3mm': 6.3,
        '4.75mm': 4.75,
        '2.36mm': 2.36,
        '1.18mm': 1.18,
        '600μ': 0.600,
        '300μ': 0.300,
        '150μ': 0.150,
        '75μ': 0.075,
    }

     return mapping.get(sieve, 0.0)
 
    def _interpolate_d_value(self, target_percent):

      points = []

      for line in self.sieve_analysis_child_lines:
        size = self._get_sieve_mm(line.sieve_size)

        if size > 0:
            points.append({
                'size': size,
                'passing': float(line.passing_percent or 0)
            })

      points = sorted(points, key=lambda x: x['size'], reverse=True)

      for i in range(len(points) - 1):

        x1 = points[i]['size']
        x2 = points[i + 1]['size']

        y1 = points[i]['passing']
        y2 = points[i + 1]['passing']

        if y1 >= target_percent >= y2 and y1 != y2:

            log_d = (
                math.log10(x1)
                + ((target_percent - y1) / (y2 - y1))
                * (math.log10(x2) - math.log10(x1))
            )

            return round(10 ** log_d, 8)

      return 0.0



    @api.depends(
    'sieve_analysis_child_lines.particle_size',
    'sieve_analysis_child_lines.passing_percent')
    def _compute_d60(self):
     for rec in self:
        rec.d60 = rec._interpolate_d_value(60)


    @api.depends(
    'sieve_analysis_child_lines.particle_size',
    'sieve_analysis_child_lines.passing_percent')
    def _compute_d30(self):
     for rec in self:
        rec.d30 = rec._interpolate_d_value(30)

    @api.depends(
    'sieve_analysis_child_lines.particle_size',
    'sieve_analysis_child_lines.passing_percent')
    def _compute_d10(self):
     for rec in self:
        rec.d10 = rec._interpolate_d_value(10)

    @api.depends('d60', 'd10')
    def _compute_cu(self):
     for rec in self:
        rec.cu = round(rec.d60 / rec.d10, 4) if rec.d10 else 0.0

    @api.depends('d30', 'd10', 'd60')
    def _compute_cc_slive(self):
     for rec in self:
        if rec.d10 and rec.d60:
            rec.cc = round(
                (rec.d30 ** 2) / (rec.d10 * rec.d60),
                4
            )
        else:
            rec.cc = 0.0


    # @api.depends('sieve_analysis_child_lines.sieve_size', 'sieve_analysis_child_lines.passing_percent')
    # def _compute_d60(self):
    #     for record in self:
    #         # extract 16mm and 10mm lines
    #         line_16 = next((l for l in record.sieve_analysis_child_lines if '16' in str(l.sieve_size)), None)
    #         line_10 = next((l for l in record.sieve_analysis_child_lines if '10' in str(l.sieve_size)), None)

    #         if line_16 and line_10 and line_16.passing_percent is not None and line_10.passing_percent is not None:
    #             try:
    #                 x1 = 16.0
    #                 x2 = 10.0
    #                 y1 = float(line_16.passing_percent)
    #                 y2 = float(line_10.passing_percent)

    #                 # Check to avoid division by zero
    #                 if y2 != y1:
    #                     # Linear interpolation to find D60
    #                     d60_value = x1 + (x2 - x1) * ((60 - y1) / (y2 - y1))
    #                 else:
    #                     d60_value = 0.0

    #                 record.d60 = d60_value
    #             except Exception:
    #                 record.d60 = 0.0
    #         else:
    #             record.d60 = 0.0

    # @api.depends('sieve_analysis_child_lines.sieve_size', 'sieve_analysis_child_lines.passing_percent')
    # def _compute_d30(self):
    #     for record in self:
    #         # extract 4.75mm and 2.00mm lines
    #         line_4_75 = next((l for l in record.sieve_analysis_child_lines if '4.75' in str(l.sieve_size)), None)
    #         line_2_36 = next((l for l in record.sieve_analysis_child_lines if '2.00' in str(l.sieve_size)), None)

    #         if line_4_75 and line_2_36 and line_4_75.passing_percent is not None and line_2_36.passing_percent is not None:
    #             try:
    #                 x1 = 4.75
    #                 x2 = 2.00
    #                 y1 = float(line_4_75.passing_percent)
    #                 y2 = float(line_2_36.passing_percent)

    #                 # Linear interpolation for target percent = 10%
    #                 target_percent = 30.0

    #                 if y2 != y1:
    #                     d30_value = x1 + (x2 - x1) * ((target_percent - y1) / (y2 - y1))
    #                 else:
    #                     d30_value = 0.0

    #                 record.d30 = d30_value
    #             except Exception:
    #                 record.d30 = 0.0
    #         else:
    #             record.d30 = 0.0

    # @api.depends('sieve_analysis_child_lines.sieve_size', 'sieve_analysis_child_lines.passing_percent')
    # def _compute_d10(self):
    #     for record in self:
    #         # find lines 1.18 mm and 600 µ
    #         line_1_18 = next((l for l in record.sieve_analysis_child_lines if '1.18' in str(l.sieve_size)), None)
    #         line_600um = next((l for l in record.sieve_analysis_child_lines if '600' in str(l.sieve_size)), None)

    #         if line_1_18 and line_600um and line_1_18.passing_percent is not None and line_600um.passing_percent is not None:
    #             try:
    #                 # Convert sieve sizes to mm
    #                 x1 = 1.18
    #                 x2 = 0.6  # 600 µm = 0.6 mm
    #                 y1 = float(line_1_18.passing_percent)
    #                 y2 = float(line_600um.passing_percent)

    #                 target_percent = 10.0  # D10 corresponds to 10% passing

    #                 if y2 != y1:
    #                     d10_value = x1 + (x2 - x1) * ((target_percent - y1) / (y2 - y1))
    #                 else:
    #                     d10_value = 0.0

    #                 record.d10 = d10_value
    #             except Exception:
    #                 record.d10 = 0.0
    #         else:
    #             record.d10 = 0.0


    # # --- Compute Cu ---
    # @api.depends('d60','d10')
    # def _compute_cu(self):
    #     for record in self:
    #         if record.d10 and record.d10 != 0:
    #             record.cu = record.d60 / record.d10
    #         else:
    #             record.cu = 0.0

    # # --- Compute Cc ---
    # @api.depends('d30','d10','d60')
    # def _compute_cc_slive(self):
    #     for record in self:
    #         if record.d10 and record.d10 != 0 and record.d60 and record.d60 != 0:
    #             record.cc = (record.d30 ** 2) / (record.d10 * record.d60)
    #         else:
    #             record.cc = 0.0
    



    @api.model
    def _default_sieve_analysis_child_lines(self):
        default_lines = [
            (0, 0, {'sieve_size': '40mm '}),
            (0, 0, {'sieve_size': '25mm'}),
            (0, 0, {'sieve_size': '19mm'}),
            (0, 0, {'sieve_size': '12.5mm'}),
            (0, 0, {'sieve_size': '10mm'}),
            (0, 0, {'sieve_size': '6.3mm'}),
            (0, 0, {'sieve_size': '4.75mm'}),
            (0, 0, {'sieve_size': ' 2.36mm'}),
            (0, 0, {'sieve_size': '1.18mm'}),
            (0, 0, {'sieve_size': '600µ'}),
            (0, 0, {'sieve_size': '300µ'}),
            (0, 0, {'sieve_size': '150µ'}),
            (0, 0, {'sieve_size': '75µ'}),
            (0, 0, {'sieve_size': 'Pan'})
        ]
        return default_lines


    @api.onchange('sieve_analysis_child_lines')
    def _onchange_sieve_analysis_child_lines(self):
        for rec in self:
            # pan_line = None
            # total_retained = 0.0
            # target_sieves = ['40mm','25mm','19mm','12.5mm','10mm','6.3mm', '4.75mm', '2.36mm','1.18mm','600µ','300µ','150µ','75µ']

            # for line in rec.sieve_analysis_child_lines:
            #     if line.sieve_size and line.sieve_size.lower() == 'pan':
            #         pan_line = line
            #     elif line.sieve_size in target_sieves:
            #         total_retained += line.wt_retained or 0.0

            # if pan_line:
            #     pan_line.wt_retained = (rec.wt_of_sample or 0.0) - total_retained

            target_sieves = [
                '40mm', '25mm', '19mm', '12.5mm',
                '10mm', '6.3mm', '4.75mm',
                '2.36mm', '1.18mm',
                '600µ', '300µ', '150µ', '75µ']

            pan_line = None
            total_retained = 0.0

            for line in rec.sieve_analysis_child_lines:
               sieve = (line.sieve_size or '').strip().lower()
 
               if sieve == 'pan':
                 pan_line = line
               elif sieve in [s.lower() for s in target_sieves]:
                total_retained += line.wt_retained or 0.0

            if pan_line:
              pan_line.wt_retained = (rec.wt_of_sample or 0.0) - total_retained




    def calculate_sieve(self): 
        for record in self:
            previous_cumulative = 0  
            for line in record.sieve_analysis_child_lines:
                print("Rows", str(line.percent_retained))
                previous_line = line.serial_no - 1

                # If this line is 'Pan', directly assign fixed values
                if line.sieve_size and line.sieve_size.lower() == 'pan':
                    line.write({
                        'cumulative_retained': 100.00,
                        'passing_percent': 0.00,
                    })
                    print("PAN LINE: cumulative_retained=100, passing_percent=0")
                    continue  # skip rest of logic for pan

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

    graph_image_slive = fields.Binary("Sieve Graph", store=True)
    graph_filename = fields.Char(
        string="Graph Filename",
        readonly=True
    )

    show_sieve_graph = fields.Boolean(string="Show Sieve Graph",default=False)

    def action_generate_graph(self):
        for rec in self:
            rec.graph_image_slive = rec.generate_line_chart_slive()
            rec.graph_filename = "grain_size_analysis.png"


    # def generate_line_chart_slive(self):

    #     self.ensure_one()

    #     x_value = []
    #     y_value = []
    #     x_labels = []

    #     for line in self.sieve_analysis_child_lines:

    #         if not line.sieve_size:
    #             continue

    #         try:
    #             sieve_str = str(line.sieve_size).strip().lower()

    #             if 'mm' in sieve_str:
    #                 sieve_val = float(
    #                     sieve_str.replace('mm', '').strip()
    #                 )
    #                 label = f"{sieve_val:g} mm"

    #             elif 'µ' in sieve_str or 'μ' in sieve_str:
    #                 micron = float(
    #                     sieve_str.replace('µ', '')
    #                     .replace('μ', '')
    #                     .strip()
    #                 )

    #                 sieve_val = micron / 1000.0
    #                 label = f"{int(micron)} µm"

    #             else:
    #                 continue

    #             x_value.append(sieve_val)
    #             y_value.append(float(line.passing_percent or 0))
    #             x_labels.append(label)

    #         except Exception:
    #             continue

    #     if not x_value:
    #         return False

    #     sorted_data = sorted(
    #         zip(x_value, y_value, x_labels),
    #         key=lambda x: x[0]
    #     )

    #     x_value, y_value, x_labels = zip(*sorted_data)

    #     fig, ax = plt.subplots(figsize=(10, 5))

    #     ax.set_xscale('log')

    #     ax.plot(
    #         x_value,
    #         y_value,
    #         color='blue',
    #         linewidth=2
    #     )

    #     ax.scatter(
    #         x_value,
    #         y_value,
    #         color='red',
    #         s=60,
    #         zorder=5
    #     )

    #     ax.set_xlabel("Particle Size (mm)")
    #     ax.set_ylabel("% Passing")
    #     ax.set_title("Grain Size Distribution Curve")

    #     ax.set_xticks(x_value)
    #     ax.set_xticklabels(
    #         x_labels,
    #         rotation=45,
    #         ha='right'
    #     )

    #     ax.xaxis.set_minor_locator(
    #         LogLocator(
    #             base=10.0,
    #             subs=np.arange(1, 10) * 0.1,
    #             numticks=100
    #         )
    #     )

    #     ax.yaxis.set_minor_locator(
    #         MultipleLocator(2)
    #     )

    #     ax.grid(
    #         True,
    #         which='both',
    #         linestyle='--',
    #         linewidth=0.4
    #     )

    #     ax.set_xlim(
    #         left=min(x_value) / 1.5,
    #         right=max(x_value) * 1.5
    #     )

    #     ax.set_ylim(0, 110)

    #     d_points = [
    #         (self.d10, 10, 'black', 'D10'),
    #         (self.d30, 30, 'green', 'D30'),
    #         (self.d60, 60, 'orange', 'D60'),
    #     ]

    #     for dx, dy, color, label in d_points:

    #         if dx and dx > 0:

    #             ax.scatter(
    #                 dx,
    #                 dy,
    #                 color=color,
    #                 s=90,
    #                 zorder=10
    #             )

    #             ax.plot(
    #                 [dx, dx],
    #                 [0, dy],
    #                 color=color,
    #                 linewidth=1.2
    #             )

    #             ax.plot(
    #                 [min(x_value), dx],
    #                 [dy, dy],
    #                 color=color,
    #                 linewidth=1.2
    #             )

    #             ax.annotate(
    #                 f"{label}={dx:.4f}",
    #                 (dx, dy)
    #             )

    #     plt.tight_layout()

    #     buffer = io.BytesIO()

    #     plt.savefig(
    #         buffer,
    #         format='png',
    #         dpi=100,
    #         bbox_inches='tight'
    #     )

    #     plt.close(fig)

    #     buffer.seek(0)

    #     return base64.b64encode(
    #         buffer.read()
    #     )


    def generate_line_chart_slive(self):

   
     from matplotlib.ticker import LogLocator, MultipleLocator

     self.ensure_one()

     x_value = []
     y_value = []
     x_labels = []

    # ---------------------------------
    # Read Data
    # ---------------------------------
     for line in self.sieve_analysis_child_lines:

        if not line.sieve_size:
            continue

        try:
            sieve_str = str(line.sieve_size).strip().lower()

            if 'mm' in sieve_str:
                sieve_val = float(
                    sieve_str.replace('mm', '').strip()
                )
                label = f"{sieve_val:g} mm"

            elif 'µ' in sieve_str or 'μ' in sieve_str:

                micron = float(
                    sieve_str.replace('µ', '')
                    .replace('μ', '')
                    .strip()
                )

                sieve_val = micron / 1000.0
                label = f"{int(micron)} µm"

            else:
                continue

            x_value.append(sieve_val)
            y_value.append(float(line.passing_percent or 0))
            x_labels.append(label)

        except Exception:
            continue

     if not x_value:
        return False

    # ---------------------------------
    # Sort Data
    # ---------------------------------
     sorted_data = sorted(
        zip(x_value, y_value, x_labels),
        key=lambda x: x[0]
    )

     x_value, y_value, x_labels = zip(*sorted_data)

    # ---------------------------------
    # Figure
    # ---------------------------------
     fig, ax = plt.subplots(figsize=(10, 5))

     fig.patch.set_facecolor("white")
     ax.set_facecolor("white")

     ax.set_axisbelow(True)

    # ---------------------------------
    # Log Scale
    # ---------------------------------
     ax.set_xscale('log')

    # ---------------------------------
    # Plot Line
    # ---------------------------------
     ax.plot(
        x_value,
        y_value,
        color='blue',
        linewidth=2,
        zorder=3
    )

    # ---------------------------------
    # Scatter Points
    # ---------------------------------
     ax.scatter(
        x_value,
        y_value,
        color='red',
        s=70,
        zorder=4
    )

    # ---------------------------------
    # Labels
    # ---------------------------------
     ax.set_xlabel("Particle Size (mm)", fontsize=12)
     ax.set_ylabel("% Passing", fontsize=12)
     ax.set_title("Grain Size Distribution Curve", fontsize=16)

    # ---------------------------------
    # X Ticks
    # ---------------------------------
     from matplotlib.ticker import FuncFormatter


     ax.set_xticks([0.01, 0.1, 1, 10, 100])

     ax.xaxis.set_major_formatter(
    FuncFormatter(lambda x, pos: f"{x:g}"))

    # ---------------------------------
    # Major & Minor Locators
    # ---------------------------------
     ax.xaxis.set_major_locator(
        LogLocator(base=10)
    )

     ax.xaxis.set_minor_locator(
        LogLocator(
            base=10,
            subs=np.arange(2, 10) * 0.1,
            numticks=100
        )
    )

     ax.yaxis.set_major_locator(
        MultipleLocator(10)
    )

     ax.yaxis.set_minor_locator(
        MultipleLocator(2)
    )

    # ---------------------------------
    # Excel Style Grid
    # ---------------------------------
     ax.grid(
        which='major',
        color='#8c8c8c',
        linewidth=0.8,
        linestyle='-'
    )

     ax.grid(
        which='minor',
        color='#d9d9d9',
        linewidth=0.4,
        linestyle='-'
    )

    # ---------------------------------
    # Limits
    # ---------------------------------
     ax.set_xlim(0.01, 100)
     ax.set_ylim(0, 110)

    # ---------------------------------
    # Border
    # ---------------------------------
     for spine in ax.spines.values():
        spine.set_color("black")
        spine.set_linewidth(1)

    # ---------------------------------
    # D10 D30 D60
    # ---------------------------------
     d_points = [
        (self.d10, 10, 'black', 'D10'),
        (self.d30, 30, 'green', 'D30'),
        (self.d60, 60, 'orange', 'D60'),
    ]

     for dx, dy, color, label in d_points:

        if dx and dx > 0:

            ax.scatter(
                dx,
                dy,
                color=color,
                s=120,
                zorder=10
            )

            ax.plot(
                [dx, dx],
                [0, dy],
                color=color,
                linewidth=1.5
            )

            ax.plot(
                [min(x_value), dx],
                [dy, dy],
                color=color,
                linewidth=1.5
            )

            ax.annotate(
                f"{label}={dx:.4f}",
                (dx, dy),
                xytext=(5, 0),
                textcoords="offset points",
                fontsize=12
            )

     plt.tight_layout()

    # ---------------------------------
    # Save Image
    # ---------------------------------
     buffer = io.BytesIO()

     plt.savefig(
        buffer,
        format='png',
        dpi=100,
        bbox_inches='tight'
    )

     plt.close(fig)

     buffer.seek(0)

     return base64.b64encode(
        buffer.read()
    )





   




               # Liquid Limit
    liquid_limit_name = fields.Char("Name",default="Liquid Limit")
    liquid_limit_visible = fields.Boolean("Liquid Limit Visible",compute="_compute_visible")
    # job_no_liquid_limit = fields.Char(string="Job No")
    # material_liquid_limit = fields.Char(String="Material")
    # start_date_liquid_limit = fields.Date("Start Date")
    # end_date_liquid_limit = fields.Date("End Date")
    child_liness = fields.One2many('mechanical.liquid.limits.line','parent_id',string="Liquid Limit")
    liquid_limit = fields.Float('Liquid Limit %',compute="_compute_liquid_limit")

   
   

    # @api.depends('child_liness.blwo_no1', 'child_liness.moisture_content')
    # def _compute_liquid_limit(self):
    #     for record in self:
    #         lines = record.child_liness.filtered(lambda l: l.blwo_no1 is not None and l.moisture_content is not None)
    #         if not lines or len(lines) < 2:
    #             record.liquid_limit = 0.0
    #             continue

    #         # Sort by blwo_no1 ascending
    #         lines_sorted = sorted(lines, key=lambda l: l.blwo_no1)
    #         target = 25.0

    #         # Find the two points around target (just below and just above)
    #         lower = None
    #         upper = None
    #         for i, line in enumerate(lines_sorted):
    #             if line.blwo_no1 < target:
    #                 lower = line
    #             elif line.blwo_no1 >= target and lower:
    #                 upper = line
    #                 break

    #         if lower and upper:
    #             x1, x2 = lower.blwo_no1, upper.blwo_no1
    #             y1, y2 = lower.moisture_content, upper.moisture_content

    #             if x2 != x1:
    #                 # Linear interpolation
    #                 ll_value = y1 + (y2 - y1) * (target - x1) / (x2 - x1)
    #             else:
    #                 ll_value = y1
    #             record.liquid_limit = ll_value
    #         elif lower:
    #             # If target above highest value
    #             record.liquid_limit = lower.moisture_content
    #         else:
    #             record.liquid_limit = 0.0

    import math

    @api.depends('child_liness.blwo_no1', 'child_liness.moisture_content')
    def _compute_liquid_limit(self):
     for record in self:
        lines = record.child_liness.filtered(
            lambda l: l.blwo_no1 and l.moisture_content
        )

        if len(lines) < 2:
            record.liquid_limit = 0.0
            continue

        x = [math.log10(float(l.blwo_no1)) for l in lines]
        y = [float(l.moisture_content) for l in lines]

        n = len(x)

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)

        denominator = n * sum_x2 - (sum_x ** 2)

        if denominator == 0:
            record.liquid_limit = 0.0
            continue

        a = (n * sum_xy - sum_x * sum_y) / denominator
        b = (sum_y - a * sum_x) / n

        ll = a * math.log10(25.0) + b

        record.liquid_limit = round(ll, 2)

    
    liquid_limit_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_liquid_limit_conformity", store=True)

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


    liquid_limit_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    liquid_limit_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_liquid_limit_final_report", store=True)
        
    @api.depends('liquid_limit_nabl', 'liquid_limit_report_type')
    def _compute_liquid_limit_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.liquid_limit_report_type == 'nabl':
                    rec.liquid_limit_final_report = 'nabl'
        
                elif rec.liquid_limit_report_type == 'non_nabl':
                    rec.liquid_limit_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.liquid_limit_nabl == 'pass':
                        rec.liquid_limit_final_report = 'nabl'
                    else:
                        rec.liquid_limit_final_report = 'non_nabl'


    graph_image_liquid = fields.Binary("Line Chart", compute="_compute_graph_image_liquid", store=True)

    show_liquid_graph = fields.Boolean(string="Show Liquid Limit Graph")

    



   

    # def generate_line_chart_liquid(self):
    #     x_value = []
    #     y_value = []
    #     for line in self.child_liness:
    #         if line.blwo_no1 and line.moisture_content is not None:
    #             x_value.append(line.blwo_no1)
    #             y_value.append(line.moisture_content)

    #     if not x_value or not y_value:
    #         return False

    #     plt.figure(figsize=(10, 5))

    #     # ✅ Blue line with red points
    #     plt.plot(x_value, y_value, color='blue', linestyle='-', linewidth=2, label='Curve')
    #     plt.scatter(x_value, y_value, color='red', edgecolors='black', s=60, zorder=5, label='Points')

    #     # ✅ Labels and title
    #     plt.xlabel('No. of Blows', fontsize=12)
    #     plt.ylabel('Water Content (%)', fontsize=12)
    #     plt.title('LIQUID LIMIT', fontsize=14)

    #     # ✅ Axis limits (rounded)
    #     max_y = max(y_value)
    #     y_limit = (int(max_y / 10) + 1) * 10
    #     plt.ylim(bottom=0, top=y_limit)

    #     max_x = max(x_value)
    #     x_limit = (int(max_x / 10) + 1) * 10
    #     plt.xlim(left=0, right=x_limit)

    #     # ✅ Minor ticks for fine grid lines
    #     ax = plt.gca()
    #     ax.xaxis.set_minor_locator(MultipleLocator(1))
    #     ax.yaxis.set_minor_locator(MultipleLocator(1))

    #     # ✅ Fine grid
    #     plt.grid(True, which='both', axis='both', linestyle='--', linewidth=0.3, color='gray', alpha=0.8)

    #     # 🔹 Highlight Liquid Limit point (DB field value वापरून)
    #     if self.liquid_limit:
    #         highlight_x = 25                # Blows (fixed at 25)
    #         highlight_y = self.liquid_limit # Moisture content from field

    #         # Dotted guide lines
    #         plt.axhline(y=highlight_y, color='green', linestyle='--', linewidth=1)
    #         plt.axvline(x=highlight_x, color='green', linestyle='--', linewidth=1)

    #         # Point mark
    #         plt.plot(highlight_x, highlight_y, marker='o', color='green', markersize=8)

    #         # Label
    #         plt.text(highlight_x + 1, highlight_y + 1, f"LL = {highlight_y:.2f}%", color='green')

    #     # ✅ Save to buffer
    #     buffer = io.BytesIO()
    #     plt.tight_layout()
    #     plt.legend()
    #     plt.savefig(buffer, format='png')
    #     plt.close()
    #     buffer.seek(0)

    #     return base64.b64encode(buffer.read()).decode('utf-8')


    def generate_line_chart_liquid(self):

      x_value = []
      y_value = []

      for line in self.child_liness:
        if line.blwo_no1 and line.moisture_content is not None:
            x_value.append(float(line.blwo_no1))
            y_value.append(float(line.moisture_content))

      if len(x_value) < 2:
        return False

    # Sort data
      data = sorted(zip(x_value, y_value), key=lambda x: x[0])
      x_value = [d[0] for d in data]
      y_value = [d[1] for d in data]

    # ----------------------------------
    # Regression: w = a log(N) + b
    # ----------------------------------
      x_log = [math.log10(x) for x in x_value]

      n = len(x_log)

      sum_x = sum(x_log)
      sum_y = sum(y_value)
      sum_xy = sum(x * y for x, y in zip(x_log, y_value))
      sum_x2 = sum(x * x for x in x_log)

      denominator = n * sum_x2 - sum_x ** 2

      if denominator == 0:
        return False

      a = (n * sum_xy - sum_x * sum_y) / denominator
      b = (sum_y - a * sum_x) / n

      # LL at 25 blows
      ll_value = a * math.log10(25) + b

      # ----------------------------------
      # Create smooth regression line
      # ----------------------------------
      x_fit = np.linspace(min(x_value), max(x_value), 500)
      y_fit = [a * math.log10(x) + b for x in x_fit]

    # ----------------------------------
    # Plot
    # ----------------------------------
      fig, ax = plt.subplots(figsize=(10, 4))

      ax.set_xscale('log')

    # Regression line
      ax.plot(
        x_fit,
        y_fit,
        color='blue',
        linewidth=2,
        label='Flow Curve'
    )

    # Actual points
      ax.scatter(
        x_value,
        y_value,
        color='red',
        edgecolors='black',
        s=80,
        zorder=5,
        label='Test Points'
    )

    # ----------------------------------
    # LL Marker
    # ----------------------------------
      ax.axvline(
        x=25,
        color='green',
        linestyle='--',
        linewidth=1.2
    )

      ax.axhline(
        y=ll_value,
        color='green',
        linestyle='--',
        linewidth=1.2
    )

      ax.scatter(
        [25],
        [ll_value],
        color='green',
        s=120,
        zorder=10
    )

      ax.annotate(
        f'LL = {ll_value:.2f}%',
        xy=(25, ll_value),
        xytext=(26, ll_value + 2),
        color='green',
        fontsize=12,
        fontweight='bold'
    )

    # ----------------------------------
    # Labels
    # ----------------------------------
      ax.set_title(
        'LIQUID LIMIT',
        fontsize=18,
        fontweight='bold'
    )

      ax.set_xlabel(
        'Number of Blows (Log Scale)',
        fontsize=12
    )

      ax.set_ylabel(
        'Water Content (%)',
        fontsize=12
    )

    # ----------------------------------
    # Limits
    # ----------------------------------
      ax.set_xlim(
        min(x_value) * 0.8,
        max(x_value) * 1.2
    )

      y_min = min(y_value)
      y_max = max(y_value)

      ax.set_ylim(
        max(0, y_min - 5),
        ((int(y_max / 10) + 1) * 10)
    )

    # ----------------------------------
    # Grid
    # ----------------------------------
      ax.xaxis.set_major_locator(LogLocator(base=10))
      ax.xaxis.set_minor_locator(
        LogLocator(
            base=10,
            subs=np.arange(2, 10) * 0.1
        )
    )

      ax.yaxis.set_minor_locator(MultipleLocator(1))

      ax.grid(
        which='major',
        linestyle='-',
        linewidth=0.5,
        alpha=0.7
    )

      ax.grid(
        which='minor',
        linestyle='--',
        linewidth=0.3,
        alpha=0.5
    )

      ax.legend()

      plt.tight_layout()

      buffer = io.BytesIO()
      plt.savefig(
        buffer,
        format='png',
        dpi=100,
        bbox_inches='tight'
    )

      plt.close()

      buffer.seek(0)

      return base64.b64encode(
        buffer.read()
    ).decode('utf-8')


        
       
    

    @api.depends('child_liness')
    def _compute_graph_image_liquid(self):
        try:
            for record in self:
                chart_image_liquid = record.generate_line_chart_liquid()
                record.graph_image_liquid = chart_image_liquid
        except:
            pass 


      # Plastic Limit
    plastic_limit_name = fields.Char("Name",default="Plastic Limit")
    plastic_limit_visible = fields.Boolean("Plastic Limit Visible",compute="_compute_visible")
   
    plastic_limit_table = fields.One2many('mechanical.plasticl.limit.line','parent_id',string="Parameter")

    plastic_limit = fields.Float(string="Average ",compute="_compute_plastic_limit")
   
    @api.depends('plastic_limit_table.water_content_pastic')
    def _compute_plastic_limit(self):
        for record in self:
            total_water_content_pastic = sum(record.plastic_limit_table.mapped('water_content_pastic'))
            record.plastic_limit = total_water_content_pastic / len(record.plastic_limit_table) if record.plastic_limit_table else 0.0
   

    plastic_limit_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Plastic Limit Conformity", compute="_compute_plastic_limit_conformity", store=True)

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


    plastic_limit_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    plastic_limit_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_plastic_limit_final_report", store=True)
        
    @api.depends('plastic_limit_nabl', 'plastic_limit_report_type')
    def _compute_plastic_limit_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.plastic_limit_report_type == 'nabl':
                    rec.plastic_limit_final_report = 'nabl'
        
                elif rec.plastic_limit_report_type == 'non_nabl':
                    rec.plastic_limit_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.plastic_limit_nabl == 'pass':
                        rec.plastic_limit_final_report = 'nabl'
                    else:
                        rec.plastic_limit_final_report = 'non_nabl'



    plasticity_index = fields.Float(string="Plasticity Index", compute="_compute_plasticity_index")

    @api.depends('plastic_limit', 'liquid_limit')
    def _compute_plasticity_index(self):
        for record in self:
            if record.liquid_limit is not None and record.plastic_limit is not None:
                record.plasticity_index = record.liquid_limit - record.plastic_limit
            else:
                record.plasticity_index = 0.0



    plasticity_index_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Plasticity Index Conformity", compute="_compute_plasticity_index_conformity", store=True)

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

    plasticity_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    plasticity_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_plasticity_final_report", store=True)
        
    @api.depends('plasticity_index_nabl', 'plasticity_report_type')
    def _compute_plasticity_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.plasticity_report_type == 'nabl':
                    rec.plasticity_final_report = 'nabl'
        
                elif rec.plasticity_report_type == 'non_nabl':
                    rec.plasticity_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.plasticity_index_nabl == 'pass':
                        rec.plasticity_final_report = 'nabl'
                    else:
                        rec.plasticity_final_report = 'non_nabl'




     # Shrinkage limit (%)
    shrinkage_limit_name = fields.Char("Name",default="Shrinkage limit")
    shrinkage_limit_visible = fields.Boolean("Shrinkage limit Visible",compute="_compute_visible")

    shrinkage_limit_table = fields.One2many('mechanical.shrinkage.limit.line','parent_id',string="Parameter")

    shrinkage_limit1 = fields.Float(string="Shrinkage limit (%)",digits=(12,3),compute="_compute_shrinkage_limit1")

    shrinkage_limit1_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_shrinkage_limit1_conformity", store=True)

    @api.depends('shrinkage_limit1','eln_ref','grade')
    def _compute_shrinkage_limit1_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.shrinkage_limit1_conformity = 'na'
                continue
            record.shrinkage_limit1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5487gt21-ca64-44dd-b0ae-278954ggh114')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5487gt21-ca64-44dd-b0ae-278954ggh114')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.shrinkage_limit1 - record.shrinkage_limit1*mu_value
                    upper = record.shrinkage_limit1 + record.shrinkage_limit1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.shrinkage_limit1_conformity = 'pass'
                        break
                    else:
                        record.shrinkage_limit1_conformity = 'fail'

    shrinkage_limit1_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_shrinkage_limit1_nabl", store=True)

    @api.depends('shrinkage_limit1','eln_ref','grade')
    def _compute_shrinkage_limit1_nabl(self):
        
        for record in self:
            record.shrinkage_limit1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5487gt21-ca64-44dd-b0ae-278954ggh114')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5487gt21-ca64-44dd-b0ae-278954ggh114')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.shrinkage_limit1 - record.shrinkage_limit1*mu_value
            upper = record.shrinkage_limit1 + record.shrinkage_limit1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.shrinkage_limit1_nabl = 'pass'
                break
            else:
                record.shrinkage_limit1_nabl = 'fail'


    shrinkage_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    shrinkage_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_shrinkage_final_report", store=True)
        
    @api.depends('shrinkage_limit1_nabl', 'shrinkage_report_type')
    def _compute_shrinkage_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.shrinkage_report_type == 'nabl':
                    rec.shrinkage_final_report = 'nabl'
        
                elif rec.shrinkage_report_type == 'non_nabl':
                    rec.shrinkage_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.shrinkage_limit1_nabl == 'pass':
                        rec.shrinkage_final_report = 'nabl'
                    else:
                        rec.shrinkage_final_report = 'non_nabl'



    @api.depends('shrinkage_limit_table.shrinkage_limit')
    def _compute_shrinkage_limit1(self):
        for record in self:
            if record.shrinkage_limit_table:
                total_shrinkage_limit = sum(record.shrinkage_limit_table.mapped('shrinkage_limit'))
                average = total_shrinkage_limit / len(record.shrinkage_limit_table)
                record.shrinkage_limit1 = (average)  # ⬅️ Rounds to nearest integer
            else:
                record.shrinkage_limit1 = 0.0

   
    volume_dry_table = fields.One2many('mechanical.volume.dry.line','parent_id',string="Parameter")
    volume_dry_name = fields.Char("Name",default="Volume of dry Pat(V2)")

    volume_wet_table = fields.One2many('mechanical.volume.wet.line','parent_id',string="Parameter")
    volume_wet_name = fields.Char("Name",default="Volume of wet soil(V1)")


   

      # Havy Compaction-MDD
    heavy_name = fields.Char("Name",default="DETERMINATION OF MDD & OMC BY PROCTOR TEST ")
    heavy_visible = fields.Boolean("Heavy Compaction-MDD Visible",compute="_compute_visible")
    heavy_table = fields.One2many('mechanical.heavy.compaction.line','parent_id',string="Heavy Compaction")

    max_dry_density = fields.Float(string="Max Dry Density (g/cc)", compute="_compute_max_dry_density", store=True)

    omc = fields.Float(string="Optimum Moisture Content (OMC)", compute="_compute_max_density_and_omc", store=True)

    @api.depends('heavy_table.dry_density', 'heavy_table.water_content')
    def _compute_max_density_and_omc(self):
        for rec in self:
            max_density = 0.0
            omc_value = 0.0
            for line in rec.heavy_table:
                if line.dry_density > max_density:
                    max_density = line.dry_density
                    omc_value = line.water_content
            rec.max_dry_density = max_density
            rec.omc = omc_value

    @api.depends('heavy_table.dry_density')
    def _compute_max_dry_density(self):
        for rec in self:
            densities = rec.heavy_table.mapped('dry_density')
            rec.max_dry_density = max(densities) if densities else 0.0
 
   


    max_dry_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_max_dry_density_conformity", store=True)

    @api.depends('max_dry_density','eln_ref','grade')
    def _compute_max_dry_density_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.max_dry_density_conformity = 'na'
                continue
            record.max_dry_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-2ee981be0d7c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-2ee981be0d7c')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-2ee981be0d7c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-2ee981be0d7c')]).parameter_table
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


    dry_density_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    dry_density_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_dry_density_final_report", store=True)
        
    @api.depends('max_dry_density_nabl', 'dry_density_report_type')
    def _compute_dry_density_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.dry_density_report_type == 'nabl':
                    rec.dry_density_final_report = 'nabl'
        
                elif rec.dry_density_report_type == 'non_nabl':
                    rec.dry_density_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.max_dry_density_nabl == 'pass':
                        rec.dry_density_final_report = 'nabl'
                    else:
                        rec.dry_density_final_report = 'non_nabl'


    omc_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_omc_conformity", store=True)

    @api.depends('omc','eln_ref','grade')
    def _compute_omc_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.omc_conformity = 'na'
                continue
            record.omc_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','po567888hhhllly1-ca64-44dd-b0ae-23120114r')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','po567888hhhllly1-ca64-44dd-b0ae-23120114r')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.omc - record.omc*mu_value
                    upper = record.omc + record.omc*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.omc_conformity = 'pass'
                        break
                    else:
                        record.omc_conformity = 'fail'

    omc_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_omc_nabl", store=True)

    @api.depends('omc','eln_ref','grade')
    def _compute_omc_nabl(self):
        
        for record in self:
            record.omc_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','po567888hhhllly1-ca64-44dd-b0ae-23120114r')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','po567888hhhllly1-ca64-44dd-b0ae-23120114r')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.omc - record.omc*mu_value
            upper = record.omc + record.omc*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.omc_nabl = 'pass'
                break
            else:
                record.omc_nabl = 'fail'


    omc_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    omc_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_omc_final_report", store=True)
        
    @api.depends('omc_nabl', 'omc_report_type')
    def _compute_omc_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.omc_report_type == 'nabl':
                    rec.omc_final_report = 'nabl'
        
                elif rec.omc_report_type == 'non_nabl':
                    rec.omc_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.omc_nabl == 'pass':
                        rec.omc_final_report = 'nabl'
                    else:
                        rec.omc_final_report = 'non_nabl'

    
    graph_image_density = fields.Binary("Line Chart", compute="_compute_graph_image_density_omc_light", store=True)

    show_heavy_graph = fields.Boolean(string="Show Compaction Graph")





    def generate_line_chart_light_omc(self):


      x = []
      y = []

      for line in self.heavy_table:
        if line.water_content and line.dry_density:
            x.append(float(line.water_content))
            y.append(float(line.dry_density))

      if len(x) < 3:
        return False

    # ---------------------------------------
    # Sort data
    # ---------------------------------------
      data = sorted(zip(x, y))
      x = np.array([i[0] for i in data], dtype=float)
      y = np.array([i[1] for i in data], dtype=float)

      omc = float(self.omc)
      mdd = float(self.max_dry_density)

    # ---------------------------------------
    # Create parabola through:
    # First Point
    # OMC/MDD
    # Last Point
    # ---------------------------------------

      x1 = x[0]
      y1 = y[0]

      x2 = omc
      y2 = mdd

      x3 = x[-1]
      y3 = y[-1]

      A = np.array([
        [x1**2, x1, 1],
        [x2**2, x2, 1],
        [x3**2, x3, 1]
    ], dtype=float)

      B = np.array([
        y1,
        y2,
        y3
    ], dtype=float)

      a, b, c = np.linalg.solve(A, B)

      def curve(xx):
          return a * xx**2 + b * xx + c

      x_smooth = np.linspace(x1, x3, 500)
      y_smooth = curve(x_smooth)

    # ---------------------------------------
    # Plot
    # ---------------------------------------

      plt.figure(figsize=(15, 5))

      plt.plot(
        x_smooth,
        y_smooth,
        color="blue",
        linewidth=2.8,
        zorder=2
    )

      plt.scatter(
        x,
        y,
        color="red",
        s=45,
        zorder=5
    )

      plt.scatter(
        omc,
        mdd,
        color="red",
        s=160,
        zorder=10
    )

      plt.axhline(
        y=mdd,
        color="red",
        linestyle="--",
        linewidth=1
    )

      plt.axvline(
        x=omc,
        color="red",
        linestyle="--",
        linewidth=1
    )

      plt.text(
        omc + 0.15,
        mdd + 0.002,
        f"OMC: {omc:.2f}%\nMDD: {mdd:.2f}",
        fontsize=12,
        color="red",
        fontweight="bold"
    )

      plt.xlabel(
        "Water Content (%)",
        fontsize=16
    )

      plt.ylabel(
        "Dry Density (g/cc)",
        fontsize=16
    )

      plt.title(
        "DETERMINATION OF COMPACTION OMC / MDD",
        fontsize=22
    )

      plt.xlim(0, max(x) + 2)

      ymin = min(min(y), min(y_smooth))
      ymax = max(max(y), max(y_smooth), mdd)

      plt.ylim(
        ymin - 0.02,
        ymax + 0.03
    )

        # ---------------------------------------
    # Graph paper background
    # ---------------------------------------

      ax = plt.gca()

      ax.set_facecolor("#f8fff8")

      ax.xaxis.set_major_locator(MultipleLocator(1))
      ax.xaxis.set_minor_locator(MultipleLocator(0.1))

      ax.yaxis.set_major_locator(MultipleLocator(0.05))
      ax.yaxis.set_minor_locator(MultipleLocator(0.005))

      ax.grid(
        which="major",
        color="green",
        linewidth=0.5,
        alpha=0.45
    )

      ax.grid(
        which="minor",
        color="green",
        linestyle=":",
        linewidth=0.3,
        alpha=0.35
    )

    # Make border thicker
      for spine in ax.spines.values():
        spine.set_linewidth(1.2)

      plt.tight_layout()

    # ---------------------------------------
    # Save Image
    # ---------------------------------------

      buffer = io.BytesIO()

      plt.savefig(
        buffer,
        format="png",
        dpi=100,
        bbox_inches="tight"
    )

      plt.close()

      buffer.seek(0)

      return base64.b64encode(
        buffer.read()
    ).decode("utf-8")




    @api.depends('heavy_table')
    def _compute_graph_image_density_omc_light(self):
        try:
            for record in self:
                chart_image_light_omc = record.generate_line_chart_light_omc()
                record.graph_image_density = chart_image_light_omc
        except:
            pass 



    # Light Compaction-MDD
    omc_name = fields.Char("Name",default="DETERMINATION  OMC AND MDD BY PROCTOR TEST ")
    omc_visible = fields.Boolean("omc Compaction-MDD Visible",compute="_compute_visible")
    omc_table = fields.One2many('mechanical.omc.compaction.line','parent_id',string="OMC Compaction")

    max_dry_density1 = fields.Float(string="Max Dry Density (g/cc)", compute="_compute_max_dry_density1", store=True)

    omc1 = fields.Float(string="Optimum Moisture Content (OMC)", compute="_compute_max_density_and_omc1", store=True)

    @api.depends('omc_table.dry_density1', 'omc_table.water_content1')
    def _compute_max_density_and_omc1(self):
        for rec in self:
            max_density1 = 0.0
            omc_value1 = 0.0
            for line in rec.omc_table:
                if line.dry_density1 > max_density1:
                    max_density1 = line.dry_density1
                    omc_value1 = line.water_content1
            rec.max_dry_density1 = max_density1
            rec.omc1 = omc_value1

    @api.depends('omc_table.dry_density1')
    def _compute_max_dry_density1(self):
        for rec in self:
            densities = rec.omc_table.mapped('dry_density1')
            rec.max_dry_density1 = max(densities) if densities else 0.0
 
   


    max_dry_density1_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_max_dry_density1_conformity", store=True)

    @api.depends('max_dry_density1','eln_ref','grade')
    def _compute_max_dry_density1_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.max_dry_density1_conformity = 'na'
                continue
            record.max_dry_density1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poty7888hhhllly1-ca64-44dd-b0ae-23141478h')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poty7888hhhllly1-ca64-44dd-b0ae-23141478h')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.max_dry_density1 - record.max_dry_density1*mu_value
                    upper = record.max_dry_density1 + record.max_dry_density1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.max_dry_density1_conformity = 'pass'
                        break
                    else:
                        record.max_dry_density1_conformity = 'fail'

    max_dry_density1_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_max_dry_density1_nabl", store=True)

    @api.depends('max_dry_density1','eln_ref','grade')
    def _compute_max_dry_density1_nabl(self):
        
        for record in self:
            record.max_dry_density1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poty7888hhhllly1-ca64-44dd-b0ae-23141478h')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poty7888hhhllly1-ca64-44dd-b0ae-23141478h')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.max_dry_density1 - record.max_dry_density1*mu_value
            upper = record.max_dry_density1 + record.max_dry_density1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.max_dry_density1_nabl = 'pass'
                break
            else:
                record.max_dry_density1_nabl = 'fail'

    dry_density1_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    dry_density1_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_dry_density1_final_report", store=True)
        
    @api.depends('max_dry_density1_nabl', 'dry_density1_report_type')
    def _compute_dry_density1_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.dry_density1_report_type == 'nabl':
                    rec.dry_density1_final_report = 'nabl'
        
                elif rec.dry_density1_report_type == 'non_nabl':
                    rec.dry_density1_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.max_dry_density1_nabl == 'pass':
                        rec.dry_density1_final_report = 'nabl'
                    else:
                        rec.dry_density1_final_report = 'non_nabl'


    omc1_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_omc1_conformity", store=True)

    @api.depends('omc1','eln_ref','grade')
    def _compute_omc1_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.omc1_conformity = 'na'
                continue
            record.omc1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-142578bgtyu')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-142578bgtyu')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.omc1 - record.omc1*mu_value
                    upper = record.omc1 + record.omc1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.omc1_conformity = 'pass'
                        break
                    else:
                        record.omc1_conformity = 'fail'

    omc1_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_omc1_nabl", store=True)

    @api.depends('omc1','eln_ref','grade')
    def _compute_omc1_nabl(self):
        
        for record in self:
            record.omc1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-142578bgtyu')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-142578bgtyu')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.omc1 - record.omc1*mu_value
            upper = record.omc1 + record.omc1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.omc1_nabl = 'pass'
                break
            else:
                record.omc1_nabl = 'fail'

    omc1_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    omc1_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_omc1_final_report", store=True)
        
    @api.depends('omc1_nabl', 'omc1_report_type')
    def _compute_omc1_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.omc1_report_type == 'nabl':
                    rec.omc1_final_report = 'nabl'
        
                elif rec.omc1_report_type == 'non_nabl':
                    rec.omc1_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.omc1_nabl == 'pass':
                        rec.omc1_final_report = 'nabl'
                    else:
                        rec.omc1_final_report = 'non_nabl'


    
    graph_image_density1 = fields.Binary("Line Chart", compute="_compute_graph_image_density_omc_light1", store=True)

    show_light_graph = fields.Boolean(string="Show Compaction Graph")





    def generate_line_chart_light_omc1(self):


      x = []
      y = []

      for line in self.omc_table:
        if line.water_content1 and line.dry_density1:
            x.append(float(line.water_content1))
            y.append(float(line.dry_density1))

      if len(x) < 3:
        return False

    # ---------------------------------------
    # Sort data
    # ---------------------------------------
      data = sorted(zip(x, y))
      x = np.array([i[0] for i in data], dtype=float)
      y = np.array([i[1] for i in data], dtype=float)

      omc = float(self.omc1)
      mdd = float(self.max_dry_density1)

    # ---------------------------------------
    # Create parabola through:
    # First Point
    # OMC/MDD
    # Last Point
    # ---------------------------------------

      x1 = x[0]
      y1 = y[0]

      x2 = omc
      y2 = mdd

      x3 = x[-1]
      y3 = y[-1]

      A = np.array([
        [x1**2, x1, 1],
        [x2**2, x2, 1],
        [x3**2, x3, 1]
    ], dtype=float)

      B = np.array([
        y1,
        y2,
        y3
    ], dtype=float)

      a, b, c = np.linalg.solve(A, B)

      def curve(xx):
          return a * xx**2 + b * xx + c

      x_smooth = np.linspace(x1, x3, 500)
      y_smooth = curve(x_smooth)

    # ---------------------------------------
    # Plot
    # ---------------------------------------

      plt.figure(figsize=(15, 5))

      plt.plot(
        x_smooth,
        y_smooth,
        color="blue",
        linewidth=2.8,
        zorder=2
    )

      plt.scatter(
        x,
        y,
        color="red",
        s=45,
        zorder=5
    )

      plt.scatter(
        omc,
        mdd,
        color="red",
        s=160,
        zorder=10
    )

      plt.axhline(
        y=mdd,
        color="red",
        linestyle="--",
        linewidth=1
    )

      plt.axvline(
        x=omc,
        color="red",
        linestyle="--",
        linewidth=1
    )

      plt.text(
        omc + 0.15,
        mdd + 0.002,
        f"OMC: {omc:.2f}%\nMDD: {mdd:.2f}",
        fontsize=12,
        color="red",
        fontweight="bold"
    )

      plt.xlabel(
        "Water Content (%)",
        fontsize=16
    )

      plt.ylabel(
        "Dry Density (g/cc)",
        fontsize=16
    )

      plt.title(
        "DETERMINATION OF COMPACTION OMC / MDD",
        fontsize=22
    )

      plt.xlim(0, max(x) + 2)

      ymin = min(min(y), min(y_smooth))
      ymax = max(max(y), max(y_smooth), mdd)

      plt.ylim(
        ymin - 0.02,
        ymax + 0.03
    )

        # ---------------------------------------
    # Graph paper background
    # ---------------------------------------

      ax = plt.gca()

      ax.set_facecolor("#f8fff8")

      ax.xaxis.set_major_locator(MultipleLocator(1))
      ax.xaxis.set_minor_locator(MultipleLocator(0.1))

      ax.yaxis.set_major_locator(MultipleLocator(0.05))
      ax.yaxis.set_minor_locator(MultipleLocator(0.005))

      ax.grid(
        which="major",
        color="green",
        linewidth=0.5,
        alpha=0.45
    )

      ax.grid(
        which="minor",
        color="green",
        linestyle=":",
        linewidth=0.3,
        alpha=0.35
    )

    # Make border thicker
      for spine in ax.spines.values():
        spine.set_linewidth(1.2)

      plt.tight_layout()

    # ---------------------------------------
    # Save Image
    # ---------------------------------------

      buffer = io.BytesIO()

      plt.savefig(
        buffer,
        format="png",
        dpi=100,
        bbox_inches="tight"
    )

      plt.close()

      buffer.seek(0)

      return base64.b64encode(
        buffer.read()
    ).decode("utf-8")


        

    @api.depends('omc_table')
    def _compute_graph_image_density_omc_light1(self):
        try:
            for record in self:
                chart_image_light_omc1 = record.generate_line_chart_light_omc1()
                record.graph_image_density1 = chart_image_light_omc1
        except:
            pass 



    


    # CBR

    soil_name = fields.Char("Name",default="California Bearing Ratio")
    soil_visible = fields.Boolean("California Bearing Ratio Visible",compute="_compute_visible")
   
    soil_table = fields.One2many('mechanical.cbr.line','parent_id',string="CBR",default=lambda self: self._default_soil_table())

    proving_ring_cf = fields.Float(string="Proving Ring Calibration Factor",digits=(10,3))

    corrected_load_25_s1 = fields.Float(compute="_compute_cbr", store=True,digits=(12,3))
    corrected_load_25_s2 = fields.Float(compute="_compute_cbr", store=True,digits=(12,3))
    corrected_load_25_s3 = fields.Float(compute="_compute_cbr", store=True,digits=(12,3))

    corrected_load_5_s1 = fields.Float(compute="_compute_cbr", store=True,digits=(12,3))
    corrected_load_5_s2 = fields.Float(compute="_compute_cbr", store=True,digits=(12,3))
    corrected_load_5_s3 = fields.Float(compute="_compute_cbr", store=True,digits=(12,3))


    cbr_25_s1 = fields.Float("2.5mm", compute="_compute_cbr", store=True)
    cbr_25_s2 = fields.Float("2.5mm", compute="_compute_cbr", store=True)
    cbr_25_s3 = fields.Float("2.5mm ", compute="_compute_cbr", store=True)

    cbr_5_s1 = fields.Float("5mm", compute="_compute_cbr", store=True)
    cbr_5_s2 = fields.Float("5mm", compute="_compute_cbr", store=True)
    cbr_5_s3 = fields.Float("5mm", compute="_compute_cbr", store=True)

    cbr_25_avg = fields.Float("2.5mm", compute="_compute_cbr", store=True)

    # cbr_5_avg = fields.Float("5mm", compute="_compute_cbr", store=True)
    # cbr_max = fields.Float("CBR Max", compute="_compute_cbr", store=True)


    @api.depends('soil_table.sample1_load',
             'soil_table.sample2_load',
             'soil_table.sample3_load',
             'soil_table.penetration')
    def _compute_cbr(self):
     for rec in self:
        lines = rec.soil_table

        # Get 2.5 mm & 5 mm rows
        line_25 = lines.filtered(lambda l: l.penetration == 2.5)
        line_5 = lines.filtered(lambda l: l.penetration == 5.0)

        if line_25:
          l = line_25[0]
          rec.corrected_load_25_s1 = l.sample1_load
          rec.corrected_load_25_s2 = l.sample2_load
          rec.corrected_load_25_s3 = l.sample3_load

        if line_5:
          l = line_5[0]
          rec.corrected_load_5_s1 = l.sample1_load
          rec.corrected_load_5_s2 = l.sample2_load
          rec.corrected_load_5_s3 = l.sample3_load

        # Default values
        rec.cbr_25_s1 = rec.cbr_25_s2 = rec.cbr_25_s3 = 0.0
        rec.cbr_5_s1 = rec.cbr_5_s2 = rec.cbr_5_s3 = 0.0

        # -------- 2.5 mm --------
        if line_25:
            l = line_25[0]
            rec.cbr_25_s1 = (l.sample1_load / 1370)*100 if l.sample1_load else 0
            rec.cbr_25_s2 = (l.sample2_load / 1370)*100 if l.sample2_load else 0
            rec.cbr_25_s3 = (l.sample3_load / 1370*100) if l.sample3_load else 0

        # -------- 5 mm --------
        if line_5:
            l = line_5[0]
            rec.cbr_5_s1 = (l.sample1_load / 2055)*100 if l.sample1_load else 0
            rec.cbr_5_s2 = (l.sample2_load / 2055)*100 if l.sample2_load else 0
            rec.cbr_5_s3 = (l.sample3_load / 2055)*100 if l.sample3_load else 0

        # -------- AVERAGE --------
        # rec.cbr_25_avg = (rec.cbr_25_s1 + rec.cbr_25_s2 + rec.cbr_25_s3) / 3

        # --------MAX 2.5 mm --------
        rec.cbr_25_avg = max(rec.cbr_25_s1,rec.cbr_25_s2,rec.cbr_25_s3)

        
        # -------- 5 mm --------
        # rec.cbr_5_avg = max(rec.cbr_5_s1,rec.cbr_5_s2,rec.cbr_5_s3)

        # rec.cbr_5_avg = (rec.cbr_5_s1 + rec.cbr_5_s2 + rec.cbr_5_s3) / 3

        # # -------- MAX --------
        # rec.cbr_max = max(rec.cbr_25_avg, rec.cbr_5_avg)


    @api.model
    def _default_soil_table(self):
        default_lines = [
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
    #     lines = self.env['mechanical.cbr.line'].search([
    #         ('parent_id', '=', rec.id)
    #     ], order='penetration asc')

    #     penetration = [l.penetration for l in lines]

    #     s1 = [l.sample1_load for l in lines]
    #     s2 = [l.sample2_load for l in lines]
    #     s3 = [l.sample3_load for l in lines]

    #     # ✅ Increase width only (width=12, height=5)
    #     plt.figure(figsize=(10, 7))

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

     import io
     import base64
     import numpy as np
     import matplotlib.pyplot as plt

     from scipy.interpolate import CubicHermiteSpline
     from matplotlib.ticker import MultipleLocator

     for rec in self:

        # ---------------------------------------
        # Read CBR Data
        # ---------------------------------------

        lines = self.env['mechanical.cbr.line'].search(
            [('parent_id', '=', rec.id)],
            order='penetration asc'
        )

        if len(lines) < 2:
            continue

        penetration = np.array(
            [float(x.penetration or 0) for x in lines],
            dtype=float
        )

        sample1 = np.array(
            [float(x.sample1_load or 0) for x in lines],
            dtype=float
        )

        sample2 = np.array(
            [float(x.sample2_load or 0) for x in lines],
            dtype=float
        )

        sample3 = np.array(
            [float(x.sample3_load or 0) for x in lines],
            dtype=float
        )

        # Remove duplicate penetration values
        penetration, idx = np.unique(
            penetration,
            return_index=True
        )

        sample1 = sample1[idx]
        sample2 = sample2[idx]
        sample3 = sample3[idx]

        # ---------------------------------------
        # Excel Style Curve
        # ---------------------------------------

        def create_curve(x, y):

            # Excel control points
            ctrl_points = [0.5, 2.5, 5.0, 12.5]

            cx = []
            cy = []

            for p in ctrl_points:

                idx = np.where(np.isclose(x, p))[0]

                if len(idx):

                    cx.append(x[idx[0]])
                    cy.append(y[idx[0]])

            cx = np.array(cx)
            cy = np.array(cy)

            if len(cx) < 2:
                return x, y

            # -------------------------------
            # Excel-like tangent calculation
            # -------------------------------

            d = np.zeros(len(cx))

            # First point
            d[0] = (cy[1] - cy[0]) / (cx[1] - cx[0])

            # Middle point (2.5 mm)
            d[1] = (
                (cy[2] - cy[0]) /
                (cx[2] - cx[0])
            )

            # 5 mm becomes flatter
            slope = (
                (cy[3] - cy[1]) /
                (cx[3] - cx[1])
            )

            d[2] = slope * 0.45

            # End almost straight
            d[3] = (
                (cy[3] - cy[2]) /
                (cx[3] - cx[2])
            ) * 0.10

            spline = CubicHermiteSpline(
                cx,
                cy,
                d
            )

            # Curved part
            xs1 = np.linspace(
                cx[0],
                cx[2],
                350
            )

            ys1 = spline(xs1)

            # Nearly straight part
            xs2 = np.linspace(
                cx[2],
                cx[3],
                350
            )

            ys2 = np.interp(
                xs2,
                [cx[2], cx[3]],
                [cy[2], cy[3]]
            )

            xs = np.concatenate([xs1, xs2])
            ys = np.concatenate([ys1, ys2])

            return xs, ys

        # ---------------------------------------
        # Generate Curves
        # ---------------------------------------

        x1, y1 = create_curve(
            penetration,
            sample1
        )

        x2, y2 = create_curve(
            penetration,
            sample2
        )

        x3, y3 = create_curve(
            penetration,
            sample3
        )

                # ---------------------------------------
        # Create Figure
        # ---------------------------------------

        fig, ax = plt.subplots(
            figsize=(8, 8),
            dpi=100
        )

        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        # ---------------------------------------
        # Plot Excel Style Curves
        # ---------------------------------------

        ax.plot(
            x1,
            y1,
            color="#4472C4",
            linewidth=1.6,
            solid_capstyle="round",
            label="Sample-1"
        )

        ax.plot(
            x2,
            y2,
            color="#ED7D31",
            linewidth=1.6,
            solid_capstyle="round",
            label="Sample-2"
        )

        ax.plot(
            x3,
            y3,
            color="#70AD47",
            linewidth=1.6,
            solid_capstyle="round",
            label="Sample-3"
        )

        # ---------------------------------------
        # Plot Original Data Points
        # ---------------------------------------

        ax.scatter(
            penetration,
            sample1,
            s=24,
            color="#4472C4",
            edgecolors="white",
            linewidths=0.6,
            zorder=10
        )

        ax.scatter(
            penetration,
            sample2,
            s=24,
            color="#ED7D31",
            edgecolors="white",
            linewidths=0.6,
            zorder=10
        )

        ax.scatter(
            penetration,
            sample3,
            s=24,
            color="#70AD47",
            edgecolors="white",
            linewidths=0.6,
            zorder=10
        )

        # ---------------------------------------
        # Title
        # ---------------------------------------

        ax.set_title(
            "CBR Graph",
            fontsize=20,
            fontweight="normal",
            pad=14
        )

        # ---------------------------------------
        # Axis Labels
        # ---------------------------------------

        ax.set_xlabel(
            "Penetration (mm)",
            fontsize=16
        )

        ax.set_ylabel(
            "Corrected Load (Kg)",
            fontsize=16
        )

        # ---------------------------------------
        # Limits
        # ---------------------------------------

        ax.set_xlim(0, 14)
        ax.set_ylim(40, 340)

        # ---------------------------------------
        # Tick Spacing
        # ---------------------------------------

        ax.xaxis.set_major_locator(
            MultipleLocator(1)
        )

        ax.xaxis.set_minor_locator(
            MultipleLocator(0.5)
        )

        ax.yaxis.set_major_locator(
            MultipleLocator(20)
        )

        ax.yaxis.set_minor_locator(
            MultipleLocator(10)
        )

        # ---------------------------------------
        # Excel Grid
        # ---------------------------------------

        ax.grid(
            which="major",
            color="#D0D0D0",
            linewidth=0.8
        )

        ax.grid(
            which="minor",
            color="#ECECEC",
            linewidth=0.4
        )

        ax.set_axisbelow(True)

        # ---------------------------------------
        # Border
        # ---------------------------------------

        for spine in ax.spines.values():
            spine.set_color("black")
            spine.set_linewidth(1)

        # ---------------------------------------
        # Tick Font
        # ---------------------------------------

        ax.tick_params(
            axis="both",
            labelsize=10
        )

        # ---------------------------------------
        # Legend
        # ---------------------------------------

        ax.legend(
            loc="upper left",
            fontsize=11,
            frameon=True
        )

        plt.tight_layout()

                # ---------------------------------------
        # Save Chart
        # ---------------------------------------

        buffer = io.BytesIO()

        plt.savefig(
            buffer,
            format="png",
            dpi=100,
            facecolor="white",
            bbox_inches="tight"
        )

        plt.close(fig)

        buffer.seek(0)

        image_data = base64.b64encode(
            buffer.read()
        )

        buffer.close()

        # ---------------------------------------
        # Save to Odoo
        # ---------------------------------------

        rec.write({
            "cbr_chart_image": image_data,
            "cbr_chart_filename": "cbr_chart.png",
            "show_cbr": True,
        })

     return True
    



    cbr_25_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_cbr_25_avg_conformity", store=True)

    @api.depends('cbr_25_avg','eln_ref','grade')
    def _compute_cbr_25_avg_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.cbr_25_avg_conformity = 'na'
                continue

            record.cbr_25_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15247gtr-2065-4532-814a-3a4c1e884305')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15247gtr-2065-4532-814a-3a4c1e884305')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.cbr_25_avg - record.cbr_25_avg*mu_value
                    upper = record.cbr_25_avg + record.cbr_25_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.cbr_25_avg_conformity = 'pass'
                        break
                    else:
                        record.cbr_25_avg_conformity = 'fail'

    cbr_25_avg_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_cbr_25_avg_nabl", store=True)

    @api.depends('cbr_25_avg','eln_ref','grade')
    def _compute_cbr_25_avg_nabl(self):
        
        for record in self:
            record.cbr_25_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15247gtr-2065-4532-814a-3a4c1e884305')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15247gtr-2065-4532-814a-3a4c1e884305')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.cbr_25_avg - record.cbr_25_avg*mu_value
            upper = record.cbr_25_avg + record.cbr_25_avg*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.cbr_25_avg_nabl = 'pass'
                break
            else:
                record.cbr_25_avg_nabl = 'fail'


    cbr_25_avg_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    cbr_25_avg_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_cbr_25_avg_final_report", store=True)
        
    @api.depends('cbr_25_avg_nabl', 'cbr_25_avg_report_type')
    def _compute_cbr_25_avg_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.cbr_25_avg_report_type == 'nabl':
                    rec.cbr_25_avg_final_report = 'nabl'
        
                elif rec.cbr_25_avg_report_type == 'non_nabl':
                    rec.cbr_25_avg_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.cbr_25_avg_nabl == 'pass':
                        rec.cbr_25_avg_final_report = 'nabl'
                    else:
                        rec.cbr_25_avg_final_report = 'non_nabl'






    # chart_image_cbr = fields.Binary("Line Chart", compute="_compute_chart_image_cbr", store=True)

    # ps_2mm = fields.Float("PS for 2.5mm",compute="_compute_ps_2mm")
    # pt_2mm = fields.Float("PT at 2.5mm",default=1370)
    # cbr_2mm = fields.Float("CBR at 2.5mm",compute="_compute_cbr_2mm")

    # ps_5mm = fields.Float("PS for 5mm",compute="_compute_ps_5mm")
    # pt_5mm = fields.Float("PT at 5mm",default=2055)
    # cbr_5mm = fields.Float("CBR at 5mm",compute="_compute_cbr_5mm")

    # cbr_result = fields.Float("CBR",compute="_compute_final_cbr")

    # @api.depends('soil_table')
    # def _compute_ps_2mm(self):
    #     for record in self:
    #         if record.soil_table and len(record.soil_table) >= 6:
    #             fifth_row = record.soil_table[5] 
    #             record.ps_2mm = fifth_row.load
    #         else:
    #             record.ps_2mm = 0


    # @api.depends('soil_table')
    # def _compute_ps_5mm(self):
    #     for record in self:
    #         if record.soil_table and len(record.soil_table) >= 9:
    #             fifth_row = record.soil_table[8] 
    #             record.ps_5mm = fifth_row.load
    #         else:
    #             record.ps_5mm = 0

    # @api.depends('pt_2mm','ps_2mm')
    # def _compute_cbr_2mm(self):
    #     for record in self:
    #         if record.pt_2mm != 0:
    #             record.cbr_2mm = round((record.ps_2mm/record.pt_2mm)*100,2)
    #         else:
    #             record.cbr_2mm = 0

    # @api.depends('pt_5mm','ps_5mm')
    # def _compute_cbr_5mm(self):
    #     for record in self:
    #         if record.pt_5mm != 0:
    #             record.cbr_5mm = round((record.ps_5mm/record.pt_5mm)*100,2)
    #         else:
    #             record.cbr_5mm = 0

    # @api.depends('cbr_5mm','cbr_2mm')
    # def _compute_final_cbr(self):
    #     for record in self:
    #         if record.cbr_5mm > record.cbr_2mm:
    #             record.cbr_result = record.cbr_5mm
    #         else:
    #             record.cbr_result = record.cbr_2mm


   

    # chart_image_cbr = fields.Binary(
    # "Line Chart",
    # compute="_compute_chart_image_cbr",
    # store=True
    #   )

    # def generate_line_chart_cbr(self):
    #     # Prepare data
    #     x_values = []
    #     y_values = []
    #     for line in self.soil_table:
    #         x_values.append(line.penetration)
    #         y_values.append(line.load)

    #     if not x_values or not y_values:
    #         return False

    #     plt.figure(figsize=(10, 5))

    #     # ✅ Blue curve with red points
    #     plt.plot(x_values, y_values, color='blue', linestyle='-', linewidth=2, label='Curve')
    #     plt.scatter(x_values, y_values, color='red', edgecolors='black', s=60, zorder=5, label='Points')

    #     # ✅ Axis labels and title
    #     plt.xlabel('Penetration (mm)', fontsize=12)
    #     plt.ylabel('Load (kg)', fontsize=12)
    #     plt.title('CBR (California Bearing Ratio)', fontsize=14)

    #     # ✅ Axis range
    #     plt.xlim(left=0, right=max(x_values) + 2)
    #     plt.ylim(bottom=0, top=max(y_values) + (max(y_values) * 0.1))

    #     # ✅ Grid (major + minor)
    #     ax = plt.gca()
    #     ax.xaxis.set_minor_locator(MultipleLocator(0.5))
    #     ax.yaxis.set_minor_locator(MultipleLocator(5))
    #     plt.grid(True, which='both', linestyle='--', linewidth=0.3, color='gray', alpha=0.8)

    #     # ✅ Save image
    #     buffer = io.BytesIO()
    #     plt.tight_layout()
    #     plt.legend()
    #     plt.savefig(buffer, format='png')
    #     plt.close()
    #     buffer.seek(0)

    #     return base64.b64encode(buffer.read()).decode('utf-8')


    # @api.depends('soil_table')
    # def _compute_chart_image_cbr(self):
    #     try:
    #         for record in self:
    #             chart_image = record.generate_line_chart_cbr()
    #             record.chart_image_cbr = chart_image
    #     except:
    #         pass





       # FSI
    fsi_name = fields.Char("Name",default="Free Swell Index")
    fsi_visible = fields.Boolean("Free Swell Index Visible",compute="_compute_visible")
  
    wt_sample = fields.Float(string="Weight of the soil sample")
    valume_water = fields.Float(string="The volume of soil specimen read from the graduated cylinder containing distilled water")
    valime_kerosen = fields.Float(string="The volume of soil specimen read from the graduated cylinder containing kerosene")
    fsi = fields.Float(string="Free Swell Index (%)", compute="_compute_fsi", store=True)


    @api.depends('valume_water', 'valime_kerosen')
    def _compute_fsi(self):
        for rec in self:
            if rec.valime_kerosen:
                rec.fsi = ((rec.valume_water - rec.valime_kerosen) / rec.valime_kerosen) * 100
            else:
                rec.fsi = 0.0  # Avoid division by zero

    fsi_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_fsi_conformity", store=True)

    @api.depends('fsi','eln_ref','grade')
    def _compute_fsi_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.fsi_conformity = 'na'
                continue
            record.fsi_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ght4125-ca64-44dd-b0ae-228aacf04998')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ght4125-ca64-44dd-b0ae-228aacf04998')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.fsi - record.fsi*mu_value
                    upper = record.fsi + record.fsi*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.fsi_conformity = 'pass'
                        break
                    else:
                        record.fsi_conformity = 'fail'

    fsi_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_fsi_nabl", store=True)

    @api.depends('fsi','eln_ref','grade')
    def _compute_fsi_nabl(self):
        
        for record in self:
            record.fsi_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ght4125-ca64-44dd-b0ae-228aacf04998')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ght4125-ca64-44dd-b0ae-228aacf04998')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.fsi - record.fsi*mu_value
            upper = record.fsi + record.fsi*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.fsi_nabl = 'pass'
                break
            else:
                record.fsi_nabl = 'fail'

    fsi_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    fsi_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_fsi_final_report", store=True)
        
    @api.depends('fsi_nabl', 'fsi_report_type')
    def _compute_fsi_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.fsi_report_type == 'nabl':
                    rec.fsi_final_report = 'nabl'
        
                elif rec.fsi_report_type == 'non_nabl':
                    rec.fsi_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.fsi_nabl == 'pass':
                        rec.fsi_final_report = 'nabl'
                    else:
                        rec.fsi_final_report = 'non_nabl'


     # Specific Gravity
    specific_gravity_name = fields.Char("Name",default="Specific Gravity")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    m1 = fields.Float(string="Mass of Density Bottle (M1) ", digits=(12,2))
    m2 = fields.Float(string="Mass of Bottle & Dry Soil (M2) ", digits=(12,2))
    m3 = fields.Float(string="Mass of Bottle, Soil & Liquid (M3) ", digits=(12,2))
    m4 = fields.Float(string="Mass of Bottle Full of Liquid (M4) ", digits=(12,2))

    specific_gravity = fields.Float(
        string="Specific Gravity (G)",
        compute="_compute_specific_gravity",
        store=True,
        digits=(12,2)
    )

    @api.depends("m1","m2","m3","m4")
    def _compute_specific_gravity(self):
        for rec in self:
            try:
                numerator = rec.m2 - rec.m1
                denominator = (rec.m4 - rec.m1) - (rec.m3 - rec.m2)
                if denominator != 0:
                    rec.specific_gravity = round(numerator / denominator, 2)
                else:
                    rec.specific_gravity = 0.0
            except Exception:
                rec.specific_gravity = 0.0

    specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_specific_gravity_conformity", store=True)

    @api.depends('specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.specific_gravity_conformity = 'na'
                continue
            record.specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','26a889da-3ab8-40e9-af69-2399b62dce9f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','26a889da-3ab8-40e9-af69-2399b62dce9f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.specific_gravity - record.specific_gravity*mu_value
                    upper = record.specific_gravity + record.specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.specific_gravity_conformity = 'fail'

    specific_gravity_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_specific_gravity_nabl", store=True)

    @api.depends('specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_nabl(self):
        
        for record in self:
            record.specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','26a889da-3ab8-40e9-af69-2399b62dce9f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','26a889da-3ab8-40e9-af69-2399b62dce9f')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.specific_gravity - record.specific_gravity*mu_value
            upper = record.specific_gravity + record.specific_gravity*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.specific_gravity_nabl = 'pass'
                break
            else:
                record.specific_gravity_nabl = 'fail'


    specific_gravity_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    specific_gravity_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_specific_gravity_final_report", store=True)
        
    @api.depends('specific_gravity_nabl', 'specific_gravity_report_type')
    def _compute_specific_gravity_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.specific_gravity_report_type == 'nabl':
                    rec.specific_gravity_final_report = 'nabl'
        
                elif rec.specific_gravity_report_type == 'non_nabl':
                    rec.specific_gravity_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.specific_gravity_nabl == 'pass':
                        rec.specific_gravity_final_report = 'nabl'
                    else:
                        rec.specific_gravity_final_report = 'non_nabl'


     # Direct Shear Test
    direct_shear_name = fields.Char("Name",default="Direct Shear Test")
    direct_shear_visible = fields.Boolean("Direct Shear Test Visible",compute="_compute_visible")

    sample_length = fields.Float(default=6)
    sample_width = fields.Float(default=6)
    sample_height = fields.Float(default=2.5)

    

    direct_proving_ring_factor = fields.Float(string="Proving Ring Factor (Kgf/Div)")

    direct_strain_rate = fields.Float(default=1.25)

    direct_area = fields.Float(
        string="Cross Sectional Area cm2"
    )

    direct_line_ids = fields.One2many(
        "mechanical.direct.shear.test.line",
        "parent_id",
        string="Observations",default=lambda self: self._default_direct_child_lines())
    

    @api.model
    def _default_direct_child_lines(self):
        default_lines = [
            (0, 0, {'horizontal_dial': 0.0}),
            (0, 0, {'horizontal_dial': 0.2}),
            (0, 0, {'horizontal_dial': 0.4}),
            (0, 0, {'horizontal_dial': 0.6}),
            (0, 0, {'horizontal_dial': 0.8}),
            (0, 0, {'horizontal_dial': 1.0}),
            (0, 0, {'horizontal_dial': 1.2}),
            (0, 0, {'horizontal_dial': 1.4}),
            (0, 0, {'horizontal_dial': 1.6}),
            (0, 0, {'horizontal_dial': 1.8}),
            (0, 0, {'horizontal_dial': 2.0}),
            (0, 0, {'horizontal_dial': 2.2}),
            (0, 0, {'horizontal_dial': 2.4}),
            (0, 0, {'horizontal_dial': 2.6}),
            (0, 0, {'horizontal_dial': 2.8}),
            (0, 0, {'horizontal_dial': 3.0}),
            
        ]
        return default_lines
    

    # Bottom Table

    failure_reading_05 = fields.Float(string="Horizontal Dial Gauge Reading At Failure (mm)",compute="_compute_results", store=True)
    failure_reading_10 = fields.Float(string="Horizontal Dial Gauge Reading At Failure (mm)",compute="_compute_results", store=True)
    failure_reading_15 = fields.Float(string="Horizontal Dial Gauge Reading At Failure (mm)",compute="_compute_results", store=True)

    proving_failure_05 = fields.Float(string="Proving Ring Reading at Failure (mm)",compute="_compute_results", store=True)
    proving_failure_10 = fields.Float(string="Proving Ring Reading at Failure (mm)",compute="_compute_results", store=True)
    proving_failure_15 = fields.Float(string="Proving Ring Reading at Failure (mm)",compute="_compute_results", store=True)

    displacement_05 = fields.Float(string="Displacement (δ ) in cm",compute="_compute_results", store=True)
    displacement_10 = fields.Float(string="Displacement (δ ) in cm",compute="_compute_results", store=True)
    displacement_15 = fields.Float(string="Displacement (δ ) in cm",compute="_compute_results", store=True)

    corrected_area_05 = fields.Float(string="Corrected Area sq.cm = A (1-δ/6)",compute="_compute_results", store=True)
    corrected_area_10 = fields.Float(string="Corrected Area sq.cm = A (1-δ/6)",compute="_compute_results", store=True)
    corrected_area_15 = fields.Float(string="Corrected Area sq.cm = A (1-δ/6)",compute="_compute_results", store=True)

    shear_force_05 = fields.Float(string="Shear Force (kg)",compute="_compute_results", store=True)
    shear_force_10 = fields.Float(string="Shear Force (kg)",compute="_compute_results", store=True)
    shear_force_15 = fields.Float(string="Shear Force (kg)",compute="_compute_results", store=True)

    shear_stress_05 = fields.Float(string="Shear Stress (Kg/cm2 )",compute="_compute_results", store=True)
    shear_stress_10 = fields.Float(string="Shear Stress (Kg/cm2 )",compute="_compute_results", store=True)
    shear_stress_15 = fields.Float(string="Shear Stress (Kg/cm2 )",compute="_compute_results", store=True)

    @api.depends(
        'direct_line_ids.pr05',
        'direct_line_ids.pr10',
        'direct_line_ids.pr15',
        'direct_line_ids.horizontal_dial',
        'direct_line_ids.corrected_area',
        'direct_line_ids.sf05',
        'direct_line_ids.sf10',
        'direct_line_ids.sf15',
        'direct_line_ids.ss05',
        'direct_line_ids.ss10',
        'direct_line_ids.ss15'
    )
    def _compute_results(self):

        for rec in self:

            # ---------------- 0.5 ----------------

            if rec.direct_line_ids:
                line = max(rec.direct_line_ids, key=lambda l: l.pr05 or 0)

                rec.failure_reading_05 = line.horizontal_dial
                rec.proving_failure_05 = line.pr05
                rec.displacement_05 = line.horizontal_dial / 10
                rec.corrected_area_05 = line.corrected_area
                rec.shear_force_05 = line.sf05
                rec.shear_stress_05 = line.ss05

            # ---------------- 1.0 ----------------

            if rec.direct_line_ids:
                line = max(rec.direct_line_ids, key=lambda l: l.pr10 or 0)

                rec.failure_reading_10 = line.horizontal_dial
                rec.proving_failure_10 = line.pr10
                rec.displacement_10 = line.horizontal_dial / 10
                rec.corrected_area_10 = line.corrected_area
                rec.shear_force_10 = line.sf10
                rec.shear_stress_10 = line.ss10

            # ---------------- 1.5 ----------------

            if rec.direct_line_ids:
                line = max(rec.direct_line_ids, key=lambda l: l.pr15 or 0)

                rec.failure_reading_15 = line.horizontal_dial
                rec.proving_failure_15 = line.pr15
                rec.displacement_15 = line.horizontal_dial / 10
                rec.corrected_area_15 = line.corrected_area
                rec.shear_force_15 = line.sf15
                rec.shear_stress_15 = line.ss15


    direct_graph_image = fields.Binary("Direct Shear Graph", store=True)

    show_direct_graph = fields.Boolean(string="Show Direct Shear Graph")
    

    cohesion = fields.Float("Cohesion")

    internal_friction = fields.Float("Angle of Internal Friction")



    def generate_line_chart_direct_shear(self):

      for rec in self:

        # -------------------------------
        # Data
        # -------------------------------

        normal_stress = []
        shear_stress = []

        if rec.shear_stress_05:
            normal_stress.append(0.5)
            shear_stress.append(rec.shear_stress_05)

        if rec.shear_stress_10:
            normal_stress.append(1.0)
            shear_stress.append(rec.shear_stress_10)

        if rec.shear_stress_15:
            normal_stress.append(1.5)
            shear_stress.append(rec.shear_stress_15)

        if len(normal_stress) < 2:
            rec.direct_graph_image = False
            continue

        x = np.array(normal_stress)
        y = np.array(shear_stress)

        # Cohesion and Friction Angle

        slope, intercept = np.polyfit(x, y, 1)

        cohesion = intercept
        friction_angle = math.degrees(math.atan(slope))

        rec.cohesion = round(cohesion, 2)
        rec.internal_friction = round(friction_angle, 2)

        # -------------------------------
        # Figure
        # -------------------------------

        fig = plt.figure(figsize=(10, 5), dpi=100)

        ax = fig.add_subplot(111)

        # Excel Graph Paper

        ax.set_facecolor("white")

        ax.set_xlim(0, 2.0)
        ax.set_ylim(0, 1.6)

        ax.set_axisbelow(True)

        ax.minorticks_on()

        # Major Grid

        ax.grid(
            which="major",
            color="#84B7A0",
            linewidth=1.0
        )

        # Minor Grid

        ax.grid(
            which="minor",
            color="#C8E1D4",
            linewidth=0.35
        )

        # Grid spacing

        ax.xaxis.set_major_locator(MultipleLocator(0.5))
        ax.xaxis.set_minor_locator(MultipleLocator(0.05))

        ax.yaxis.set_major_locator(MultipleLocator(0.25))
        ax.yaxis.set_minor_locator(MultipleLocator(0.025))

        # Border

        for spine in ax.spines.values():
            spine.set_linewidth(1.0)

        # Plot ONLY actual observations (like Excel)

        ax.plot(
            x,
            y,
            color="blue",
            linewidth=1.2,
            marker="o",
            markersize=4
        )

        # Axis Labels

        ax.set_title(
        "Direct Shear Test Graph",
        fontsize=20,
        fontweight="bold")

        ax.set_xlabel(
            "Penetration (mm)",
            fontsize=10
        )

        ax.set_ylabel("Load (KG)",fontsize=10,rotation=0,labelpad=70,      va="center")

                # Tick formatting

        ax.tick_params(
            axis='both',
            which='major',
            labelsize=8
        )

        # X-axis ticks

        ax.set_xticks([0, 0.5, 1.0, 1.5, 2.0])
        ax.set_xticklabels(
            ['0', '0.5', '1', '1.5', '2']
        )

        # Y-axis ticks

        ax.set_yticks(
            np.arange(0, 1.75, 0.25)
        )

        ax.set_yticklabels([
            "0.00",
            "0.25",
            "0.50",
            "0.75",
            "1.00",
            "1.25",
            "1.50",
        ])

        # Remove extra padding

        plt.subplots_adjust(
    left=0.18,
    right=0.98,
    bottom=0.15,
    top=1.00
)

        # Save graph

        buffer = io.BytesIO()

        plt.savefig(
            buffer,
            format="png",
            dpi=100,
            bbox_inches=None,
            facecolor="white"
        )

        buffer.seek(0)

        rec.direct_graph_image = base64.b64encode(
            buffer.read()
        )

        buffer.close()

        plt.close(fig)

      return True
    

    cohesion1 = fields.Float(
    string="Cohesion (Kg/Sqcm)",
    compute="_compute_cohesion_friction",
    store=True,)

    internal_friction1 = fields.Float(
    string="Internal Friction (°)",
    compute="_compute_cohesion_friction",
    store=True,)


    @api.depends(
    'shear_force_05',
    'shear_force_10',
    'shear_force_15',
    'corrected_area_05',
    'corrected_area_10',
    'corrected_area_15'
)
    def _compute_cohesion_friction(self):

     for rec in self:

        rec.cohesion1 = 0.0
        rec.internal_friction1 = 0.0

        if not (
            rec.corrected_area_05 and
            rec.corrected_area_10 and
            rec.corrected_area_15
        ):
            continue

        sigma1 = 0.5
        sigma2 = 1.5

        # Use FULL precision (not rounded values)
        tau1 = rec.shear_force_05 / rec.corrected_area_05
        tau2 = rec.shear_force_15 / rec.corrected_area_15

        slope = (tau2 - tau1) / (sigma2 - sigma1)

        rec.internal_friction1 = math.degrees(math.atan(slope))

        rec.cohesion1 = tau1 - sigma1 * slope


    cohesion1_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_cohesion1_conformity", store=True)

    @api.depends('cohesion1','eln_ref','grade')
    def _compute_cohesion1_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.cohesion1_conformity = 'na'
                continue
            record.cohesion1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457888hhhllly1-ca64-44dd-b0ae-3214hhhtr')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457888hhhllly1-ca64-44dd-b0ae-3214hhhtr')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.cohesion1 - record.cohesion1*mu_value
                    upper = record.cohesion1 + record.cohesion1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.cohesion1_conformity = 'pass'
                        break
                    else:
                        record.cohesion1_conformity = 'fail'

    cohesion1_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_cohesion1_nabl", store=True)

    @api.depends('cohesion1','eln_ref','grade')
    def _compute_cohesion1_nabl(self):
        
        for record in self:
            record.cohesion1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457888hhhllly1-ca64-44dd-b0ae-3214hhhtr')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457888hhhllly1-ca64-44dd-b0ae-3214hhhtr')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.cohesion1 - record.cohesion1*mu_value
            upper = record.cohesion1 + record.cohesion1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.cohesion1_nabl = 'pass'
                break
            else:
                record.cohesion1_nabl = 'fail'


    cohesion1_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    cohesion1_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_cohesion1_final_report", store=True)
        
    @api.depends('cohesion1_nabl', 'cohesion1_report_type')
    def _compute_cohesion1_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.cohesion1_report_type == 'nabl':
                    rec.cohesion1_final_report = 'nabl'
        
                elif rec.cohesion1_report_type == 'non_nabl':
                    rec.cohesion1_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.cohesion1_nabl == 'pass':
                        rec.cohesion1_final_report = 'nabl'
                    else:
                        rec.cohesion1_final_report = 'non_nabl'


    internal_friction1_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_internal_friction1_conformity", store=True)

    @api.depends('internal_friction1','eln_ref','grade')
    def _compute_internal_friction1_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.internal_friction1_conformity = 'na'
                continue
            record.internal_friction1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','00fh7888hhhllly1-ca64-44dd-b0ae-897456ghtr')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','00fh7888hhhllly1-ca64-44dd-b0ae-897456ghtr')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.internal_friction1 - record.internal_friction1*mu_value
                    upper = record.internal_friction1 + record.internal_friction1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.internal_friction1_conformity = 'pass'
                        break
                    else:
                        record.internal_friction1_conformity = 'fail'

    internal_friction1_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_internal_friction1_nabl", store=True)

    @api.depends('internal_friction1','eln_ref','grade')
    def _compute_internal_friction1_nabl(self):
        
        for record in self:
            record.internal_friction1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','00fh7888hhhllly1-ca64-44dd-b0ae-897456ghtr')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','00fh7888hhhllly1-ca64-44dd-b0ae-897456ghtr')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.internal_friction1 - record.internal_friction1*mu_value
            upper = record.internal_friction1 + record.internal_friction1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.internal_friction1_nabl = 'pass'
                break
            else:
                record.internal_friction1_nabl = 'fail'


    internal_friction1_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    internal_friction1_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_internal_friction1_final_report", store=True)
        
    @api.depends('internal_friction1_nabl', 'internal_friction1_report_type')
    def _compute_internal_friction1_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.internal_friction1_report_type == 'nabl':
                    rec.internal_friction1_final_report = 'nabl'
        
                elif rec.internal_friction1_report_type == 'non_nabl':
                    rec.internal_friction1_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.internal_friction1_nabl == 'pass':
                        rec.internal_friction1_final_report = 'nabl'
                    else:
                        rec.internal_friction1_final_report = 'non_nabl'


    

     # Moisture Content
    moisture_content_name = fields.Char("Name",default="Moisture Content")
    moisture_content_visible = fields.Boolean("Moisture Content Visible",compute="_compute_visible")

    moisture_content_ids = fields.One2many("soil.moisture.content.line", "parent_id", string="Test Readings")

    avg_moisture_content = fields.Float(
        string="Average Moisture Content % ",
        compute="_compute_avg_moisture_content",
        store=True,
        digits=(12,2))

    @api.depends("moisture_content_ids.moisture_content")
    def _compute_avg_moisture_content(self):
        for rec in self:
            vals = [line.moisture_content for line in rec.moisture_content_ids if line.moisture_content is not None]
            rec.avg_moisture_content = round(sum(vals)/len(vals), 2) if vals else 0.0
    
    avg_moisture_content_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_moisture_content_conformity", store=True)

    @api.depends('avg_moisture_content','eln_ref','grade')
    def _compute_avg_moisture_content_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_moisture_content_conformity = 'na'
                continue
            record.avg_moisture_content_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7abb5a01-2fa7-4c4a-ab6e-0f4112e3aea9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7abb5a01-2fa7-4c4a-ab6e-0f4112e3aea9')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7abb5a01-2fa7-4c4a-ab6e-0f4112e3aea9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7abb5a01-2fa7-4c4a-ab6e-0f4112e3aea9')]).parameter_table
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

    avg_moisture_report_type = fields.Selection([
            ('auto', 'Auto'),
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')
        
    avg_moisture_final_report = fields.Selection([
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),], compute="_compute_avg_moisture_final_report", store=True)
        
    @api.depends('avg_moisture_content_nabl', 'avg_moisture_report_type')
    def _compute_avg_moisture_final_report(self):
        for rec in self:
        
                # Manual override
                if rec.avg_moisture_report_type == 'nabl':
                    rec.avg_moisture_final_report = 'nabl'
        
                elif rec.avg_moisture_report_type == 'non_nabl':
                    rec.avg_moisture_final_report = 'non_nabl'
        
                # Automatic
                else:
                    if rec.avg_moisture_content_nabl == 'pass':
                        rec.avg_moisture_final_report = 'nabl'
                    else:
                        rec.avg_moisture_final_report = 'non_nabl'

     

     ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
      
        for record in self:
            record.sieve_visible = False
            # water_content_visible = False
            record.liquid_limit_visible = False
            record.plastic_limit_visible = False
            record.shrinkage_limit_visible  = False 
            record.heavy_visible = False
            record.omc_visible = False
            record.soil_visible = False
            record.fsi_visible  = False 
            record.specific_gravity_visible  = False 
            record.direct_shear_visible  = False 
            record.moisture_content_visible = False



            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == '12014fgr-5c56-475b-9a89-93a59c9ee3a2':
                    record.sieve_visible = True

                # if sample.internal_id == '800a2dc9-49fe-4dab-83e8-63758c7f351a':
                #     record.water_content_visible = True
                
                if sample.internal_id == '7abb5a01-2fa7-4c4a-ab6e-0f4112e3aea9':
                    record.moisture_content_visible = True

                if sample.internal_id == '23fg21gh-7202-4d62-864b-8efa58b6b61f':
                    record.liquid_limit_visible = True

                if sample.internal_id == '120vbf14-2ff0-4b81-aca1-0e07dab7cd87':
                    record.plastic_limit_visible = True

                if sample.internal_id == '5487gt21-ca64-44dd-b0ae-278954ggh114':
                    record.shrinkage_limit_visible = True

                if sample.internal_id == '3210vbf-20fb-4843-aa0e-2ee981be0d7c':
                    record.heavy_visible = True

                if sample.internal_id == '3210vbf-20fb-4843-aa0e-142578bgtyu':
                    record.omc_visible = True
                
                if sample.internal_id == '15247gtr-2065-4532-814a-3a4c1e884305':
                    record.soil_visible = True

                if sample.internal_id == 'ght4125-ca64-44dd-b0ae-228aacf04998':
                    record.fsi_visible = True
                

                if sample.internal_id == '26a889da-3ab8-40e9-af69-2399b62dce9f':
                    record.specific_gravity_visible = True

                if sample.internal_id == '21457888hhhllly1-ca64-44dd-b0ae-3214hhhtr':
                    record.direct_shear_visible = True

                if sample.internal_id == '00fh7888hhhllly1-ca64-44dd-b0ae-897456ghtr':
                    record.direct_shear_visible = True


    
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

            # Moisture Content
            if result.parameter.internal_id == '7abb5a01-2fa7-4c4a-ab6e-0f4112e3aea9':
                result.calculated = True
                result.result_char = round(self.avg_moisture_content,2)
                if self.avg_moisture_content_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Atterberg Limit
            if result.parameter.internal_id == '582ac73a-3f86-4c7a-8dda-04357ade5617':
                result.calculated = True

            
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


            # Heavy Visible
            if result.parameter.internal_id == '3210vbf-20fb-4843-aa0e-2ee981be0d7c':
                result.calculated = True
                result.result_char = round(self.max_dry_density,2)
                if self.max_dry_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Heavy Visible
            if result.parameter.internal_id == 'po567888hhhllly1-ca64-44dd-b0ae-23120114r':
                result.calculated = True
                result.result_char = round(self.omc,2)
                if self.omc_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # OMC
            if result.parameter.internal_id == 'poty7888hhhllly1-ca64-44dd-b0ae-23141478h':
                result.calculated = True
                result.result_char = round(self.max_dry_density1,2)
                if self.max_dry_density1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # OMC
            if result.parameter.internal_id == '3210vbf-20fb-4843-aa0e-142578bgtyu':
                result.calculated = True
                result.result_char = round(self.omc1,2)
                if self.omc1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Free Swell Index
            if result.parameter.internal_id == 'ght4125-ca64-44dd-b0ae-228aacf04998':
                result.calculated = True
                result.result_char = round(self.fsi,2)
                if self.fsi_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

         
            
            # California Bearing Ratio
            if result.parameter.internal_id == '15247gtr-2065-4532-814a-3a4c1e884305':
                result.calculated = True
                result.result_char = round(self.cbr_25_avg,2)
                if self.cbr_25_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Shrinkage limit Visible
            if result.parameter.internal_id == '5487gt21-ca64-44dd-b0ae-278954ggh114':
                result.calculated = True
                result.result_char = round(self.shrinkage_limit1,2)
                if self.shrinkage_limit1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Specific Gravity
            if result.parameter.internal_id == '26a889da-3ab8-40e9-af69-2399b62dce9f':
                result.calculated = True
                result.result_char = round(self.specific_gravity,2)
                if self.specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Direct Shear Test
            if result.parameter.internal_id == '21457888hhhllly1-ca64-44dd-b0ae-3214hhhtr':
                result.calculated = True
                result.result_char = round(self.cohesion1,2)
                if self.cohesion1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


           
            
            # Direct Shear Test (Angle of Friction)
            if result.parameter.internal_id == '00fh7888hhhllly1-ca64-44dd-b0ae-897456ghtr':
                result.calculated = True
                result.result_char = round(self.internal_friction1,2)
                if self.internal_friction1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue





            
            

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
        record = self.env['mechanical.soil'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    notes_id = fields.One2many('mechanical.soil.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

    @api.model
    def _default_notes_lines(self):
        return [
            (0, 0, {'sr_no': 'i', 'notes': 'The results stated in this report apply only to the tested sample(s) and are based on the conditions and parameters at the time of testing.'}),
            (0, 0, {'sr_no': 'ii', 'notes': 'This report is invalid without the official paper seal of Make Infracon.'}),
            (0, 0, {'sr_no': 'iii', 'notes': 'All test results are confidential and will not be disclosed to any third party without written consent of the client, except where required by law.'}),
            (0, 0, {'sr_no': 'iv', 'notes': 'Any discrepancies or complaints regarding this report must be communicated in writing within 7 days from the date of issue.'}),
            (0, 0, {'sr_no': 'v', 'notes': 'This report shall not be reproduced, except in full, without the prior written approval of Make Infracon.'}),
            (0, 0, {'sr_no': 'vi', 'notes': 'The laboratory assumes no responsibility for the purpose for which the test results are used or for any subsequent actions taken based on these results.'}),
        ]



class SoilMoistureContentLine(models.Model):
    _name = 'soil.moisture.content.line'
    _description = 'Moisture Content Line'

    parent_id = fields.Many2one('mechanical.soil', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)

    wet_weight = fields.Float(
        string='Weight of wet soil + container (gm)'
    )

    dry_weight = fields.Float(
        string='Weight of oven dry soil + container (gm)'
    )

    container_weight = fields.Float(
        string='Weight of container (gm)'
    )

    moisture_content = fields.Float(
        string='Moisture Content %',
        compute='_compute_moisture_content',
        store=True
    )

    @api.depends('wet_weight', 'dry_weight', 'container_weight')
    def _compute_moisture_content(self):
        for rec in self:
            moisture_soil = rec.dry_weight - rec.container_weight

            if moisture_soil > 0:
                rec.moisture_content = (
                    (rec.wet_weight - rec.dry_weight)
                    / moisture_soil
                ) * 100
            else:
                rec.moisture_content = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SoilMoistureContentLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class SoilSieveAnalysisLine(models.Model):
    _name = "mechanical.soil.sieve.analysis.line"
    parent_id = fields.Many2one('mechanical.soil', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size")
    particle_size = fields.Char(string="Particle Size  (mm)")
    wt_retained = fields.Float(string="Wt. Retained in gms")

    cumulative_percent = fields.Float(string="Cum. Weight Retained (gm)",compute="_compute_cumulative_percent",
    store=True,)

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

    @api.depends('wt_retained', 'parent_id.sieve_analysis_child_lines.wt_retained')
    def _compute_cumulative_percent(self):
        for parent in self.mapped('parent_id'):
            total = 0
            lines = parent.sieve_analysis_child_lines.sorted('serial_no')

            for line in lines:
                total += line.wt_retained or 0
                line.cumulative_percent = total



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




class LIQUIDLIMITLINE(models.Model):
    _name = "mechanical.liquid.limits.line"
    parent_id = fields.Many2one('mechanical.soil',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)
    container_no1 = fields.Char(string="Container No.")
    blwo_no1 = fields.Float(string="No. of Blows")
    wt_of_con_wet = fields.Float(string="Wt. of Container + Wet Soil")
    wt_of_con_dry = fields.Float(string="Wt. of Container + dry Soil")   
    loss_of_moisture = fields.Float(string="Loss of Moisture (gm)",compute="_compute_loss_of_moisture")
    wt_containner = fields.Float(string="Weight of Container")
    wt_of_dry= fields.Float(string="Weight of Dry Soil",compute="_compute_wt_of_dry")
    moisture_content = fields.Float(string="Moisture Content %",compute="_compute_moisture_content")

    @api.depends('wt_of_con_wet', 'wt_of_con_dry')
    def _compute_loss_of_moisture(self):
        for line in self:
            line.loss_of_moisture = line.wt_of_con_wet - line.wt_of_con_dry

    @api.depends('wt_of_con_dry', 'wt_containner')
    def _compute_wt_of_dry(self):
        for line in self:
            line.wt_of_dry = line.wt_of_con_dry - line.wt_containner

    @api.depends('loss_of_moisture', 'wt_of_dry')
    def _compute_moisture_content(self):
        for line in self:
            if line.wt_of_dry != 0:
                line.moisture_content = line.loss_of_moisture / line.wt_of_dry * 100
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

        return super(LIQUIDLIMITLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


# class WATERCONTENTLINE(models.Model):
#     _name = "mechanical.water.content.line"
#     parent_id = fields.Many2one('mechanical.soil',string="Parent Id")

#     serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)
#     container_noo = fields.Integer(string="Container No") 
#     wt_of_cont = fields.Float(string="Weight of container,(gms)")
#     wet_sample_cont = fields.Float(string="Weight of wet sample + container (gm)")
#     dry_sample_cont = fields.Float(string="Weigth of dry sample + Container (gms)")
#     mass_dry_soil= fields.Float(string="Mass of dry soil")
#     water_contentss = fields.Float(string="Water content (W)=(W1-W2)(W1-Wc)/100%",compute="_compute_water_contentss")
#     w1_w2 = fields.Float(string="(W1-W2)",compute="_compute_w1_w2")
#     W1_Wc = fields.Float(string="(W1_Wc)",compute="_compute_W1_Wc")



#     @api.depends('wet_sample_cont', 'dry_sample_cont')
#     def _compute_w1_w2(self):
#         for line in self:
#             line.w1_w2 = line.wet_sample_cont - line.dry_sample_cont


#     @api.depends('wet_sample_cont', 'wt_of_cont')
#     def _compute_W1_Wc(self):
#         for line in self:
#             line.W1_Wc = line.wet_sample_cont - line.wt_of_cont


 
#     @api.depends('w1_w2', 'W1_Wc')
#     def _compute_water_contentss(self):
#         for line in self:
#             if line.W1_Wc != 0:
#                 line.water_contentss = line.w1_w2 / line.W1_Wc *100
#             else:
#                 line.water_contentss = 0.0

#     @api.model
#     def create(self, vals):
#         # Set the serial_no based on the existing records for the same parent
#         if vals.get('parent_id'):
#             existing_records = self.search([('parent_id', '=', vals['parent_id'])])
#             if existing_records:
#                 max_serial_no = max(existing_records.mapped('serial_no'))
#                 vals['serial_no'] = max_serial_no + 1

       # return super(WATERCONTENTLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class PLASTICLIMITLINE(models.Model):
    _name = "mechanical.plasticl.limit.line"
    parent_id = fields.Many2one('mechanical.soil',string="Parent Id")


    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)
    container_no = fields.Integer(string="Container No")   
    wt_of_con = fields.Float(string="Weight of container (gm)")
    wt_of_con_wet = fields.Float(string="Weight of container + wet soil (gm)")
    wt_of_con_dry = fields.Float(string="Weight of container + Dry soil (gm)")
    wt_of_water = fields.Float(string="Weight of water in (gm)",compute="_compute_wt_of_water")
    wt_of_oven = fields.Float(string="Weight of ovendry soil (gm)",compute="_compute_wt_of_oven")
    water_content_pastic = fields.Float(string="Water Content (%)",compute="_compute_water_content")


    @api.depends('wt_of_con_wet', 'wt_of_con_dry')
    def _compute_wt_of_water(self):
        for line in self:
            line.wt_of_water = line.wt_of_con_wet - line.wt_of_con_dry


    @api.depends('wt_of_con', 'wt_of_con_dry')
    def _compute_wt_of_oven(self):
        for line in self:
            line.wt_of_oven = line.wt_of_con_dry - line.wt_of_con


    @api.depends('wt_of_water', 'wt_of_oven')
    def _compute_water_content(self):
        for line in self:
            if line.wt_of_oven != 0:
                line.water_content_pastic = line.wt_of_water / line.wt_of_oven * 100
            else:
                line.water_content_pastic = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PLASTICLIMITLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class HEAVYCOMPACTIONLINE(models.Model):
    _name = "mechanical.heavy.compaction.line"
    parent_id = fields.Many2one('mechanical.soil',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    amount_soil = fields.Float(string="Amount of soil (gm)")
    amount_water = fields.Integer(string="Amount of water added (%)")
    empty_wt_mould = fields.Integer(string="Empty weight of mould without collar, W1 (gm)")
    wt_soil = fields.Float(string="Weight of soil compacted + mould, W2 (gm)")
    wt_of_wet = fields.Integer(string="Weight of wet soil (W2-W1) (gm)",compute="_compute_wt_of_wet")
    volume_mould = fields.Float(string="Volume of mould (V) (cm3)")
    bulk_density = fields.Float(string=" Bulk density (ρ) (g/cc)",compute="_compute_bulk_density")
    con_no = fields.Float(string="Container Number")
    empty_wt = fields.Float(string="Empty weight of container (M1) (gm)")
    wet_con_ovenwet= fields.Float(string="Weight of container + wet soil (M2) (gm)")
    wet_con_ovendry= fields.Float(string="Weight of container + Weight of oven dry soil (M3) (gm)")
    water_content = fields.Float(string="Water Content (%)",compute="_compute_water_and_dry_density")
    dry_density = fields.Float(string="Dry Density (γd ) (g/cc)",compute="_compute_water_and_dry_density")


    @api.depends('wt_soil', 'empty_wt_mould')
    def _compute_wt_of_wet(self):
        for line in self:
            line.wt_of_wet = line.wt_soil - line.empty_wt_mould



    @api.depends('wt_of_wet', 'volume_mould')
    def _compute_bulk_density(self):
        for line in self:
            if line.volume_mould != 0:
                line.bulk_density = line.wt_of_wet / line.volume_mould
            else:
                line.bulk_density = 0.0


    @api.depends('wet_con_ovendry', 'wet_con_ovenwet', 'empty_wt', 'bulk_density')
    def _compute_water_and_dry_density(self):
        for rec in self:
            m2 = rec.wet_con_ovenwet     # container + wet soil
            m3 = rec.wet_con_ovendry         # container + oven dry soil
            m1 = rec.empty_wt        # empty container

            if m2 and m3 and m1 and (m3 - m1) != 0:
                rec.water_content = ((m2 - m3) / (m3 - m1)) * 100
            else:
                rec.water_content = 0.0

            if rec.bulk_density and rec.water_content is not None:
                rec.dry_density = rec.bulk_density / (1 + (rec.water_content / 100))
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

        return super(HEAVYCOMPACTIONLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class SoilCBRLine(models.Model):
    _name = "mechanical.cbr.line"
    parent_id = fields.Many2one('mechanical.soil',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    penetration = fields.Float(string="Penetration (mm)")

    

    
    # SAMPLE 1
    sample1_reading = fields.Float(string="Proving ring Reading	1")
    sample1_load = fields.Float(string="Corrected load (Kg) 1", compute="_compute_loads", store=True,digits=(12,3))


    # SAMPLE 2
    sample2_reading = fields.Float(string="Proving ring Reading	2")
    sample2_load = fields.Float(string="Corrected load (Kg) 2", compute="_compute_loads", store=True,digits=(12,3))

    
    # SAMPLE 3
    sample3_reading = fields.Float(string="Proving ring Reading	3")
    sample3_load = fields.Float(string="Corrected load (Kg) 3", compute="_compute_loads", store=True,digits=(12,3))

    
    @api.depends(
        'sample1_reading', 'sample2_reading', 'sample3_reading','parent_id', 'parent_id.proving_ring_cf'
    )
    def _compute_loads(self):
        for rec in self:
            proving_ring_cf = rec.parent_id.proving_ring_cf if rec.parent_id else 0

            if proving_ring_cf:
                rec.sample1_load = (rec.sample1_reading * proving_ring_cf) 
                rec.sample2_load = (rec.sample2_reading * proving_ring_cf) 
                rec.sample3_load = (rec.sample3_reading * proving_ring_cf) 
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

        return super(SoilCBRLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class LIGHTCOMPACTIONLINE(models.Model):
    _name = "mechanical.omc.compaction.line"
    parent_id = fields.Many2one('mechanical.soil',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    amount_soil1 = fields.Float(string="Amount of soil (gm)")
    amount_water1 = fields.Integer(string="Amount of water added (%)")
    empty_wt_mould1 = fields.Integer(string="Empty weight of mould without collar, W1 (gm)")
    wt_soil1 = fields.Float(string="Weight of soil compacted + mould, W2 (gm)")
    wt_of_wet1 = fields.Integer(string="Weight of wet soil (W2-W1) (gm)",compute="_compute_wt_of_wet1")
    volume_mould1 = fields.Float(string="Volume of mould (V) (cm3)")
    bulk_density1 = fields.Float(string=" Bulk density (ρ) (g/cc)",compute="_compute_bulk_density1")
    con_no1 = fields.Float(string="Container Number")
    empty_wt1 = fields.Float(string="Empty weight of container (M1) (gm)")
    wet_con_ovenwet1 = fields.Float(string="Weight of container + wet soil (M2) (gm)")
    wet_con_ovendry1 = fields.Float(string="Weight of container + Weight of oven dry soil (M3) (gm)")
    water_content1 = fields.Float(string="Water Content (%)",compute="_compute_water_and_dry_density1")
    dry_density1 = fields.Float(string="Dry Density (γd ) (g/cc)",compute="_compute_water_and_dry_density1")


    @api.depends('wt_soil1', 'empty_wt_mould1')
    def _compute_wt_of_wet1(self):
        for line in self:
            line.wt_of_wet1 = line.wt_soil1 - line.empty_wt_mould1



    @api.depends('wt_of_wet1', 'volume_mould1')
    def _compute_bulk_density1(self):
        for line in self:
            if line.volume_mould1 != 0:
                line.bulk_density1 = line.wt_of_wet1 / line.volume_mould1
            else:
                line.bulk_density1 = 0.0


    @api.depends('wet_con_ovendry1', 'wet_con_ovenwet1', 'empty_wt1', 'bulk_density1')
    def _compute_water_and_dry_density1(self):
        for rec in self:
            m2 = rec.wet_con_ovenwet1     # container + wet soil
            m3 = rec.wet_con_ovendry1         # container + oven dry soil
            m1 = rec.empty_wt1        # empty container

            if m2 and m3 and m1 and (m3 - m1) != 0:
                rec.water_content1 = ((m2 - m3) / (m3 - m1)) * 100
            else:
                rec.water_content1 = 0.0

            if rec.bulk_density1 and rec.water_content1 is not None:
                rec.dry_density1 = rec.bulk_density1 / (1 + (rec.water_content1 / 100))
            else:
                rec.dry_density1 = 0.0


  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(LIGHTCOMPACTIONLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class ShrinkagelimitLINE(models.Model):
    _name = "mechanical.shrinkage.limit.line"
    parent_id = fields.Many2one('mechanical.soil',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    container_no = fields.Char(string="Container No.")
    shrinkage_mass = fields.Float(string="Mass of container (M1) ",digits=(12,3))

    shrinkage_wet = fields.Float(string="Mass of container + Wet soil (M2)",digits=(12,3))

    wt_dry = fields.Float(string="Mass of container + Dry soil (M3)",digits=(12,3))

    mass_dry = fields.Float(string="Mass of Dry soil (M3-M1),Ms",digits=(12,3),compute="_compute_mass_dry")
    mass_water = fields.Float(string="Mass of Water( M2-M3) , Mw",digits=(12,3),compute="_compute_mass_water")


    moisture_content_shri = fields.Float(string="Water Content %",digits=(12,3),compute="_compute_moisture_content_shri")

    volume_wet_shri = fields.Float(string="Volume of Wet Soil ,V1 (CC)",digits=(12,3))

    volume_dry_shir = fields.Float(string="Volume of Dry Soil ,V2 (CC)",digits=(12,3))

    shrinkage_limit = fields.Float(string="Shrinkage limit (%)",digits=(12,3),compute="_compute_shrinkage_limit")

    shrinkage_ratio = fields.Float(string="Shrinkage ratio (Ms/V2)",digits=(12,3),compute="_compute_values")

    @api.depends("mass_dry", "volume_dry_shir")
    def _compute_values(self):
        for rec in self:
            if rec.volume_dry_shir:
                rec.shrinkage_ratio = rec.mass_dry / rec.volume_dry_shir
            else:
                rec.shrinkage_ratio = 0.0

    @api.depends('wt_dry', 'shrinkage_mass')
    def _compute_mass_dry(self):
        for rec in self:
            if rec.wt_dry is not None and rec.shrinkage_mass is not None:
                rec.mass_dry = rec.wt_dry - rec.shrinkage_mass
            else:
                rec.mass_dry = 0.0

    @api.depends('shrinkage_wet', 'wt_dry')
    def _compute_mass_water(self):
        for rec in self:
            if rec.shrinkage_wet is not None and rec.wt_dry is not None:
                rec.mass_water = rec.shrinkage_wet - rec.wt_dry
            else:
                rec.mass_water = 0.0

    @api.depends('mass_water', 'mass_dry')
    def _compute_moisture_content_shri(self):
        for rec in self:
            if rec.mass_dry:
                rec.moisture_content_shri = (rec.mass_water / rec.mass_dry) * 100
            else:
                rec.moisture_content_shri = 0.0

    

    @api.depends('moisture_content_shri', 'volume_wet_shri', 'volume_dry_shir', 'mass_dry')
    def _compute_shrinkage_limit(self):
        for rec in self:
            if rec.mass_dry:
                rec.shrinkage_limit = rec.moisture_content_shri - ((rec.volume_wet_shri - rec.volume_dry_shir) / rec.mass_dry) * 100
            else:
                rec.shrinkage_limit = 0.0


   

  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ShrinkagelimitLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class VolumeDryLINE(models.Model):
    _name = "mechanical.volume.dry.line"
    parent_id = fields.Many2one('mechanical.soil',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    container_no_dry = fields.Char(string="Container No.")
    shrinkage_dry_before = fields.Float(string="Wt. of shrinkage dish + Mercury(before)",digits=(12,3))
    shrinkage_dry_after = fields.Float(string="Wt. of shrinkage dish + Mercury(After)",digits=(12,3))
    mass_mercury_dry = fields.Float(string="mass of mercury displaced by dry soil pat",compute="_compute_mass_mercury_dry",digits=(12,3))
    density_dry = fields.Float(string="density of mercury (g/cc)",digits=(12,3))
    volume_dry = fields.Float(string="Volume of dry Pat(V2)CC",compute="_compute_volume_dry",digits=(12,3))


    @api.depends('shrinkage_dry_before', 'shrinkage_dry_after')
    def _compute_mass_mercury_dry(self):
        for rec in self:
            if rec.shrinkage_dry_before is not None and rec.shrinkage_dry_after is not None:
                rec.mass_mercury_dry = rec.shrinkage_dry_before - rec.shrinkage_dry_after
            else:
                rec.mass_mercury_dry = 0.0

    @api.depends('mass_mercury_dry', 'density_dry')
    def _compute_volume_dry(self):
        for rec in self:
            if rec.density_dry:
                rec.volume_dry = rec.mass_mercury_dry / rec.density_dry
            else:
                rec.volume_dry = 0.0

   
   


  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(VolumeDryLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class VolumeWetLINE(models.Model):
    _name = "mechanical.volume.wet.line"
    parent_id = fields.Many2one('mechanical.soil',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    container_no_wet = fields.Char(string="Container No.")
    shrinkage_wet_before = fields.Float(string="Wt. of empty shrinkage dish ",digits=(12,3))
    shrinkage_wet_after = fields.Float(string="Wt. of shrinkage dish + Mercury",digits=(12,3))
    mass_mercury_wet = fields.Float(string="Wt. of  Mercury in dish ",compute="_compute_mass_mercury_wet",digits=(12,3))
    density_wet = fields.Float(string="density of mercury (g/cc))",digits=(12,3))
    volume_wet = fields.Float(string="Volume of wet Soil(V1)CC",compute="_compute_volume_wet",digits=(12,3))


    @api.depends('shrinkage_wet_before', 'shrinkage_wet_after')
    def _compute_mass_mercury_wet(self):
        for rec in self:
            if rec.shrinkage_wet_before is not None and rec.shrinkage_wet_after is not None:
                rec.mass_mercury_wet = rec.shrinkage_wet_after - rec.shrinkage_wet_before
            else:
                rec.mass_mercury_wet = 0.0

    @api.depends('mass_mercury_wet', 'density_wet')
    def _compute_volume_wet(self):
        for rec in self:
            if rec.density_wet:
                rec.volume_wet = rec.mass_mercury_wet / rec.density_wet
            else:
                rec.volume_wet = 0.0
   


  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(VolumeWetLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class DirectShearTestLine(models.Model):
    _name = "mechanical.direct.shear.test.line"
    parent_id = fields.Many2one('mechanical.soil',string="Parent Id")

    serial_no = fields.Integer(string="Test",readonly=True, copy=False, default=1)


    horizontal_dial = fields.Float(string="Horizontal Dial Reading (mm)")

    corrected_area = fields.Float(string="Corrected Area sq.cm = A (1-δ/6)",compute="_compute_corrected_area",store=True)

    # ---------------- 0.5 ----------------

    pr05 = fields.Float("Proving Ring Reading 0.5")

    sf05 = fields.Float(string="Shear Force ,kg",
        compute="_compute_shear_force",
        store=True
    )

    ss05 = fields.Float(string="Shear Stress kg/cm2",
        compute="_compute_shear_stress",
        store=True
    )

    # ---------------- 1.0 ----------------

    pr10 = fields.Float(string="Proving Ring Reading 1.0",)

    sf10 = fields.Float(string="Shear Force ,kg",
        compute="_compute_shear_force",
        store=True
    )

    ss10 = fields.Float(string="Shear Stress kg/cm2",
        compute="_compute_shear_stress",
        store=True
    )

    # ---------------- 1.5 ----------------

    pr15 = fields.Float(string="Proving Ring Reading 1.5",)

    sf15 = fields.Float(string="Shear Force ,kg",
        compute="_compute_shear_force",
        store=True
    )

    ss15 = fields.Float(string="Shear Stress kg/cm2",
        compute="_compute_shear_stress",
        store=True
    )

    @api.depends('horizontal_dial', 'parent_id.direct_area')
    def _compute_corrected_area(self):

        for line in self:
            area = line.parent_id.direct_area or 36
            line.corrected_area = area * (1 - line.horizontal_dial / 60)

    @api.depends(
        'pr05',
        'pr10',
        'pr15',
        'parent_id.direct_proving_ring_factor'
    )
    def _compute_shear_force(self):

        for line in self:

            factor = line.parent_id.direct_proving_ring_factor or 0

            line.sf05 = round(line.pr05 * factor, 2)
            line.sf10 = round(line.pr10 * factor, 2)
            line.sf15 = round(line.pr15 * factor, 2)

    @api.depends(
        'sf05',
        'sf10',
        'sf15',
        'corrected_area'
    )
    def _compute_shear_stress(self):

        for line in self:

            if line.corrected_area:

                line.ss05 = round(
                    line.sf05 / line.corrected_area,
                    2
                )

                line.ss10 = round(
                    line.sf10 / line.corrected_area,
                    2
                )

                line.ss15 = round(
                    line.sf15 / line.corrected_area,
                    2
                )

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




# class DirectShearLine(models.Model):
#     _name = "mechanical.soil.direct.shear.line"
#     parent_id = fields.Many2one('mechanical.soil',string="Parent Id")

#     serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

#     normal_stress = fields.Float(string="Normal stress σ (kPa)")
#     shear_strength = fields.Float(string="Shear stress τ (kPa)")

   

    
#     @api.model
#     def create(self, vals):
#         # Set the serial_no based on the existing records for the same parent
#         if vals.get('parent_id'):
#             existing_records = self.search([('parent_id', '=', vals['parent_id'])])
#             if existing_records:
#                 max_serial_no = max(existing_records.mapped('serial_no'))
#                 vals['serial_no'] = max_serial_no + 1

#         return super(DirectShearLine, self).create(vals)

#     def _reorder_serial_numbers(self):
#         # Reorder the serial numbers based on the positions of the records in child_lines
#         records = self.sorted('id')
#         for index, record in enumerate(records):
#             record.serial_no = index + 1


class SoilNotes(models.Model):
    _name = "mechanical.soil.notes"

    parent_id = fields.Many2one('mechanical.soil', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
