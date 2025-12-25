from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
from math import pi

import io
import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import io
import base64
from math import log10

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import LogLocator, MultipleLocator, NullFormatter, ScalarFormatter
import itertools

# Matplotlib आणि NumPy इम्पोर्ट करण्याचा प्रयत्न करा
try:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    import numpy as np
except ImportError:
    plt = None
    np = None
    ticker = None
from matplotlib.ticker import FormatStrFormatter
from odoo import models, fields, api, _
from odoo.exceptions import UserError

# Smooth curve साठी या दोन लायब्ररीज लागतात.
# जर त्या नसतील तर कोड एरर न देता साधी लाईन वापरेल.
try:
    import numpy as np
    from scipy.interpolate import make_interp_spline
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False



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

    lab_id = fields.Char(
            string="Lab ID",
            compute="_compute_lab_id",
            store=True
        )

        # -----------------------------
        # Compute method
        # -----------------------------
    @api.depends('eln_ref')
    def _compute_lab_id(self):
        for rec in self:
            if rec.eln_ref:
                rec.lab_id = rec.eln_ref.lab_id
            else:
                rec.lab_id = False
    # material = fields.Many2one('product.template',string='Material',compute="_compute_material_id",store=True)

    # @api.depends('eln_ref.material')
    # def _compute_material_id(self):
    #     for rec in self:
    #         rec.material = rec.eln_ref.material if rec.eln_ref else False

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

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('force_sieve_visible'):
            res['sieve_visible'] = True
        return res

 
    sieve_analysis_child_lines = fields.One2many('mechanical.soil.sieve.analysis.line1','parent_id',string="Sieve Analysis",default=lambda self: self._default_sieve_analysis_child_lines())

    boulder = fields.Float(string="% Boulders ",compute="_compute_boulder")

    gravel = fields.Float(string="%Gravels",compute="_compute_gravel")
    sand = fields.Float(string="%Sand",compute="_compute_sand")
    silt_clay = fields.Float(string="%Clay",compute="_compute_clay_fraction")

    silt = fields.Float(string="%Silt",compute="_compute_silt")
    
    wt_of_sample = fields.Float(string="Weight of Sample, gms")

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
            record.sand = 100 - ((record.gravel or 0.0) + (record.silt_clay or 0.0))

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
            (0, 0, {'sieve_size': '80mm'}),
            (0, 0, {'sieve_size': '40mm '}),
            (0, 0, {'sieve_size': '20mm'}),
            (0, 0, {'sieve_size': '16mm'}),
            (0, 0, {'sieve_size': '10mm'}),
            (0, 0, {'sieve_size': '4.75mm'}),
            (0, 0, {'sieve_size': ' 2.36mm'}),
            (0, 0, {'sieve_size': '1.18mm'}),
            (0, 0, {'sieve_size': '600 µ'}),
            (0, 0, {'sieve_size': '425 µ'}),
            (0, 0, {'sieve_size': '300µ'}),
            (0, 0, {'sieve_size': '212µ'}),
            (0, 0, {'sieve_size': '150µ'}),
            (0, 0, {'sieve_size': '75µ'}),
            (0, 0, {'sieve_size': 'Pan'})
        ]
        return default_lines


    @api.onchange('sieve_analysis_child_lines')
    def _onchange_sieve_analysis_child_lines(self):
        for rec in self:
            pan_line = None
            total_retained = 0.0
            target_sieves = ['80mm','40mm','20mm','16mm', '10mm', '4.75mm', '2.36mm','1.18mm','600 µ','425 µ','300µ','212µ','150µ','75µ']

            for line in rec.sieve_analysis_child_lines:
                if line.sieve_size and line.sieve_size.lower() == 'pan':
                    pan_line = line
                elif line.sieve_size in target_sieves:
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
                    previous_line_record = self.env['mechanical.soil.sieve.analysis.line1'].sudo().search([
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








   




               # Liquid Limit
    liquid_limit_name = fields.Char("Name",default="Liquid Limit")
    liquid_limit_visible = fields.Boolean("Liquid Limit Visible",compute="_compute_visible")
    # job_no_liquid_limit = fields.Char(string="Job No")
    # material_liquid_limit = fields.Char(String="Material")
    # start_date_liquid_limit = fields.Date("Start Date")
    # end_date_liquid_limit = fields.Date("End Date")
    child_liness = fields.One2many('mechanical.liquid.limits.line1','parent_id',string="Liquid Limit")
    liquid_limit = fields.Float('Liquid Limit %',compute="_compute_liquid_limit")

   
   

    @api.depends('child_liness.blwo_no1', 'child_liness.moisture_content')
    def _compute_liquid_limit(self):
        for record in self:
            lines = record.child_liness.filtered(lambda l: l.blwo_no1 is not None and l.moisture_content is not None)
            if not lines or len(lines) < 2:
                record.liquid_limit = 0.0
                continue

            # Sort by blwo_no1 ascending
            lines_sorted = sorted(lines, key=lambda l: l.blwo_no1)
            target = 25.0

            # Find the two points around target (just below and just above)
            lower = None
            upper = None
            for i, line in enumerate(lines_sorted):
                if line.blwo_no1 < target:
                    lower = line
                elif line.blwo_no1 >= target and lower:
                    upper = line
                    break

            if lower and upper:
                x1, x2 = lower.blwo_no1, upper.blwo_no1
                y1, y2 = lower.moisture_content, upper.moisture_content

                if x2 != x1:
                    # Linear interpolation
                    ll_value = y1 + (y2 - y1) * (target - x1) / (x2 - x1)
                else:
                    ll_value = y1
                record.liquid_limit = ll_value
            elif lower:
                # If target above highest value
                record.liquid_limit = lower.moisture_content
            else:
                record.liquid_limit = 0.0

    
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


    graph_image_liquid = fields.Binary("Line Chart", compute="_compute_graph_image_liquid", store=True)

    



   

    def generate_line_chart_liquid(self):
        x_value = []
        y_value = []
        for line in self.child_liness:
            if line.blwo_no1 and line.moisture_content is not None:
                x_value.append(line.blwo_no1)
                y_value.append(line.moisture_content)

        if not x_value or not y_value:
            return False

        plt.figure(figsize=(10, 5))

        # ✅ Blue line with red points
        plt.plot(x_value, y_value, color='blue', linestyle='-', linewidth=2, label='Curve')
        plt.scatter(x_value, y_value, color='red', edgecolors='black', s=60, zorder=5, label='Points')

        # ✅ Labels and title
        plt.xlabel('No. of Blows', fontsize=12)
        plt.ylabel('Water Content (%)', fontsize=12)
        plt.title('LIQUID LIMIT', fontsize=14)

        # ✅ Axis limits (rounded)
        max_y = max(y_value)
        y_limit = (int(max_y / 10) + 1) * 10
        plt.ylim(bottom=0, top=y_limit)

        max_x = max(x_value)
        x_limit = (int(max_x / 10) + 1) * 10
        plt.xlim(left=0, right=x_limit)

        # ✅ Minor ticks for fine grid lines
        ax = plt.gca()
        ax.xaxis.set_minor_locator(MultipleLocator(1))
        ax.yaxis.set_minor_locator(MultipleLocator(1))

        # ✅ Fine grid
        plt.grid(True, which='both', axis='both', linestyle='--', linewidth=0.3, color='gray', alpha=0.8)

        # 🔹 Highlight Liquid Limit point (DB field value वापरून)
        if self.liquid_limit:
            highlight_x = 25                # Blows (fixed at 25)
            highlight_y = self.liquid_limit # Moisture content from field

            # Dotted guide lines
            plt.axhline(y=highlight_y, color='green', linestyle='--', linewidth=1)
            plt.axvline(x=highlight_x, color='green', linestyle='--', linewidth=1)

            # Point mark
            plt.plot(highlight_x, highlight_y, marker='o', color='green', markersize=8)

            # Label
            plt.text(highlight_x + 1, highlight_y + 1, f"LL = {highlight_y:.2f}%", color='green')

        # ✅ Save to buffer
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.legend()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode('utf-8')


        
       
    

    @api.depends('child_liness')
    def _compute_graph_image_liquid(self):
        try:
            for record in self:
                chart_image_liquid = record.generate_line_chart_liquid()
                record.graph_image_liquid = chart_image_liquid
        except:
            pass 











#  1st table  Bulk Density

    moisture_name = fields.Char( string="Name",default=" Bulk Density" )
    moisture_visible = fields.Boolean(string="Bulk Density Visible",compute="_compute_visible")
    bulk_line_ids = fields.One2many('soil.bulk.density','parent_id', string="Bulk Density Lines")



   #  Calculation-NMC, 
    

    # NMC_name = fields.Char( string="Name",default=" NMC" )
    moisture_ids = fields.One2many('soil.moisture','parent_id', string="Moisture Tests")


    # specific gravity
    gravity_name = fields.Char(string="Name",default=" SPECIFIC GRAVITY", )
    specific_gravity_visible = fields.Boolean( string="Specific Gravity Visible",default=True )
    gravity_line_ids = fields.One2many( "specific.gravity", "parent_id",string="Specific Gravity Lines",)









# Atterbergs Limits (Free Swell)

    freeswell_name = fields.Char(string="Name",default="Atterbergs Limits (Free Swell)",)
    freeswell_visible = fields.Boolean( string="Free Swell Visible",default=True,)
    freeswell_line_ids = fields.One2many( "soil.free.swell", "parent_id", string="Free Swell Lines",)

   
   






      # Plastic Limit
    plastic_limit_name = fields.Char("Name",default="Plastic Limit")
    plastic_limit_visible = fields.Boolean("Plastic Limit Visible",compute="_compute_visible")
   
    plastic_limit_table = fields.One2many('mechanical.plasticl.limit.line1','parent_id',string="Parameter")

    plastic_limit = fields.Float(string="Average ",compute="_compute_plastic_limit")
   
    @api.depends('plastic_limit_table.water_content_pastic')
    def _compute_plastic_limit(self):
        for record in self:
            total_water_content_pastic = sum(record.plastic_limit_table.mapped('water_content_pastic'))
            record.plastic_limit = total_water_content_pastic / len(record.plastic_limit_table) if record.plastic_limit_table else 0.0
   

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

    plasticity_index = fields.Float(string="Plasticity Index", compute="_compute_plasticity_index")

    @api.depends('plastic_limit', 'liquid_limit')
    def _compute_plasticity_index(self):
        for record in self:
            if record.liquid_limit is not None and record.plastic_limit is not None:
                record.plasticity_index = record.plastic_limit - record.liquid_limit
            else:
                record.plasticity_index = 0.0



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


   

      # Havy Compaction-MDD
    heavy_name = fields.Char("Name",default="DETERMINATION OF MDD & OMC BY PROCTOR TEST ")
    heavy_visible = fields.Boolean("Heavy Compaction-MDD Visible",compute="_compute_visible")
    heavy_table = fields.One2many('mechanical.heavy.compaction.line1','parent_id',string="Heavy Compaction")

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
 
   


    heavy_table_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_heavy_table_conformity", store=True)

    @api.depends('max_dry_density','eln_ref','grade')
    def _compute_heavy_table_conformity(self):
        
        for record in self:
            record.heavy_table_conformity = 'fail'
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
                        record.heavy_table_conformity = 'pass'
                        break
                    else:
                        record.heavy_table_conformity = 'fail'

    heavy_table_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_heavy_table_nabl", store=True)

    @api.depends('max_dry_density','eln_ref','grade')
    def _compute_heavy_table_nabl(self):
        
        for record in self:
            record.heavy_table_nabl = 'fail'
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
                record.heavy_table_nabl = 'pass'
                break
            else:
                record.heavy_table_nabl = 'fail'

    
    graph_image_density = fields.Binary("Line Chart", compute="_compute_graph_image_density_omc_light", store=True)








    def generate_line_chart_light_omc(self):
        x_value = []
        y_value = []
        for line in self.heavy_table:
            if line.water_content and line.dry_density:
                x_value.append(line.water_content)
                y_value.append(line.dry_density)

        if not x_value or not y_value:
            return False

        x = np.array(x_value)
        y = np.array(y_value)

        # Sort data
        sorted_indices = np.argsort(x)
        x = x[sorted_indices]
        y = y[sorted_indices]

        # Gentle smooth curve (quadratic)
        x_smooth = np.linspace(x.min(), x.max(), 200)
        spline = make_interp_spline(x, y, k=2)
        y_smooth = spline(x_smooth)

        # Find smooth curve peak (OMC/MDD)
        smooth_max_index = np.argmax(y_smooth)
        smooth_max_x = x_smooth[smooth_max_index]
        smooth_max_y = y_smooth[smooth_max_index]

        # Trim curve so it never goes above MDD
        y_smooth = np.minimum(y_smooth, smooth_max_y)

        # Figure size
        plt.figure(figsize=(15, 5))

        # Plot smooth curve
        plt.plot(x_smooth, y_smooth, color='blue', linewidth=2)

        # Plot points (smaller, subtle)
        plt.scatter(x, y, color='red', edgecolors='none', s=40, zorder=5)

        # Labels and title
        plt.xlabel('Water Content (%)', fontsize=12)
        plt.ylabel('Dry Density (g/cc)', fontsize=12)
        plt.title('DETERMINATION OF COMPACTION OMC / MDD', fontsize=14)

        # Extend y-axis
        plt.xlim(left=0, right=max(x) + 2)
        plt.ylim(bottom=min(y) - 0.03, top=smooth_max_y + 0.03)

        # Grid
        ax = plt.gca()
        ax.xaxis.set_minor_locator(MultipleLocator(0.2))
        ax.yaxis.set_minor_locator(MultipleLocator(0.005))
        plt.grid(True, which='both', linestyle='--', linewidth=0.3, color='darkgreen', alpha=0.9)

        # Highlight OMC/MDD (shifted peak)
        plt.axhline(y=smooth_max_y, color='red', linestyle='--', linewidth=1)
        plt.axvline(x=smooth_max_x, color='red', linestyle='--', linewidth=1)
        plt.plot(smooth_max_x, smooth_max_y, marker='o', color='red', markersize=6)
        plt.text(smooth_max_x + 0.2, smooth_max_y + 0.002,
                f"OMC: {smooth_max_x:.2f}%\nMDD: {smooth_max_y:.2f}",
                color='red', fontsize=10)

        plt.tight_layout()

        # Save to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150)
        plt.close()
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')


    



    @api.depends('heavy_table')
    def _compute_graph_image_density_omc_light(self):
        try:
            for record in self:
                chart_image_light_omc = record.generate_line_chart_light_omc()
                record.graph_image_density = chart_image_light_omc
        except:
            pass 



    # Light Compaction-MDD
    omc_name = fields.Char("Name",default="DETERMINATION  OMC BY PROCTOR TEST ")
    omc_visible = fields.Boolean("omc Compaction-MDD Visible",compute="_compute_visible")
    omc_table = fields.One2many('mechanical.omc.compaction.line1','parent_id',string="OMC Compaction")

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
 
   


    omc_table_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_omc_table_conformity", store=True)

    @api.depends('omc1','eln_ref','grade')
    def _compute_omc_table_conformity(self):
        
        for record in self:
            record.omc_table_conformity = 'fail'
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
                        record.omc_table_conformity = 'pass'
                        break
                    else:
                        record.omc_table_conformity = 'fail'

    omc_table_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_omc_table_nabl", store=True)

    @api.depends('omc1','eln_ref','grade')
    def _compute_omc_table_nabl(self):
        
        for record in self:
            record.omc_table_nabl = 'fail'
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
                record.omc_table_nabl = 'pass'
                break
            else:
                record.omc_table_nabl = 'fail'

    
    graph_image_density1 = fields.Binary("Line Chart", compute="_compute_graph_image_density_omc_light1", store=True)




    def generate_line_chart_light_omc1(self):
    # Prepare data
        x_value = []
        y_value = []
        for line in self.omc_table:
            x_value.append(line.water_content1)
            y_value.append(line.dry_density1)

        if not x_value or not y_value:
            return False

        plt.figure(figsize=(10, 5))

        # ✅ Blue curve with red points
        plt.plot(x_value, y_value, color='blue', linestyle='-', linewidth=2, label='Curve')
        plt.scatter(x_value, y_value, color='red', edgecolors='black', s=60, zorder=5, label='Points')

        # ✅ Axis labels and title
        plt.xlabel('Water Content (%)', fontsize=12)
        plt.ylabel('Dry Density (g/cc)', fontsize=12)
        plt.title('DETERMINATION OF COMPACTION OMC / MDD', fontsize=14)

        # ✅ Axis range
        plt.xlim(left=0, right=max(x_value) + 2)
        plt.ylim(bottom=min(y_value) - 0.02, top=max(y_value) + 0.02)

        # ✅ Minor ticks for fine grid
        ax = plt.gca()
        ax.xaxis.set_minor_locator(MultipleLocator(0.5))
        ax.yaxis.set_minor_locator(MultipleLocator(0.005))

        # ✅ Fine grid (major + minor)
        plt.grid(True, which='both', linestyle='--', linewidth=0.3, color='gray', alpha=0.8)

        # ✅ Highlight max dry density
        max_index = y_value.index(max(y_value))
        max_x = x_value[max_index]
        max_y = y_value[max_index]

        plt.axhline(y=max_y, color='red', linestyle='--', linewidth=1)
        plt.axvline(x=max_x, color='red', linestyle='--', linewidth=1)
        plt.plot(max_x, max_y, marker='o', color='red', markersize=8)
        plt.text(max_x + 0.3, max_y + 0.003, f"OMC: {max_x:.2f}%\nMDD: {max_y:.2f}", color='red')

        # ✅ Save image
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.legend()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode('utf-8')
        
       
    

    @api.depends('omc_table')
    def _compute_graph_image_density_omc_light1(self):
        try:
            for record in self:
                chart_image_light_omc1 = record.generate_line_chart_light_omc1()
                record.graph_image_density1 = chart_image_light_omc1
        except:
            pass 



     # TRIAXIAL SHEAR TEST (By LVDT Reading )
    triaxial_name = fields.Char("Name",default="TRIAXIAL SHEAR TEST (By LVDT Reading ) ")
    triaxial_visible = fields.Boolean("TRIAXIAL SHEAR TEST (By LVDT Reading )",compute="_compute_visible")
   
    observations = fields.Char(string="Observations")

    diameter_triaxial = fields.Float(string="Diameter of the specimen  (d) in  meters",digits=(12,3))
    length_triaxial = fields.Float(string="Length of the specimen (L) in meters",digits=(12,3))
    area_triaxial = fields.Float(string="Area of the specimen  in m2",compute="_compute_area_triaxial",digits=(12,3))

    area_triaxial_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_area_triaxial_conformity", store=True)

    @api.depends('area_triaxial','eln_ref','grade')
    def _compute_area_triaxial_conformity(self):
        
        for record in self:
            record.area_triaxial_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-145ght27854l')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-145ght27854l')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.area_triaxial - record.area_triaxial*mu_value
                    upper = record.area_triaxial + record.area_triaxial*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.area_triaxial_conformity = 'pass'
                        break
                    else:
                        record.area_triaxial_conformity = 'fail'

    area_triaxial_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_area_triaxial_nabl", store=True)

    @api.depends('area_triaxial','eln_ref','grade')
    def _compute_area_triaxial_nabl(self):
        
        for record in self:
            record.area_triaxial_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-145ght27854l')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-145ght27854l')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.area_triaxial - record.area_triaxial*mu_value
            upper = record.area_triaxial + record.area_triaxial*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.area_triaxial_nabl = 'pass'
                break
            else:
                record.area_triaxial_nabl = 'fail'

    @api.depends('diameter_triaxial')
    def _compute_area_triaxial(self):
        for rec in self:
            d = rec.diameter_triaxial or 0.0
            rec.area_triaxial = 0.7853 * (d ** 2)

    triaxial_table = fields.One2many('mechanical.lvdt.line1','parent_id',string="LVDT Reading ")


       # CALCULATIONS OF COHESION AND ANGLE OF INTERNAL FRICTION
    internal_fraction_name = fields.Char("Name",default="CALCULATIONS OF COHESION AND ANGLE OF INTERNAL FRICTION")
    internal_fraction_visible = fields.Boolean("CALCULATIONS OF COHESION AND ANGLE OF INTERNAL FRICTION",compute="_compute_visible")

    internal_fraction_table = fields.One2many('mechanical.cohesion.line1','parent_id',string="LVDT Reading ")


    # CBR

    soil_name = fields.Char("Name",default="California Bearing Ratio")
    soil_visible = fields.Boolean("California Bearing Ratio Visible",compute="_compute_visible")
   
    soil_table = fields.One2many('mechanical.cbr.line1','parent_id',string="CBR")

    room_temp = fields.Float(string="Room Temp.°C" )
    temp_correction= fields.Float(string="Temperature correction ",digits=(12,3) )
    std_temp = fields.Float(string="Std Temp During calibr'n")
    rise_temp = fields.Float(
        string="Rise/Fall in temperature (Deg)",
        compute="_compute_rise_values",
        store=True
    )
    rise_force = fields.Float(
        string="% rise/fall in force value",
        compute="_compute_rise_values",
        store=True,digits=(12,3)
    )

    @api.depends('room_temp', 'std_temp', 'temp_correction')
    def _compute_rise_values(self):
        for rec in self:
            if rec.room_temp and rec.std_temp:
                rec.rise_temp = rec.room_temp - rec.std_temp
            else:
                rec.rise_temp = 0.0

            if rec.temp_correction:
                rec.rise_force = rec.temp_correction * rec.rise_temp
            else:
                rec.rise_force = 0.0

# WATER CONTENT (Before Soaking)
    before_can_no = fields.Integer(string="Can No")
    before_can_wet_soil = fields.Float(string="Wt of Can + Wet Soil",digits=(12,3))
    before_can_dry_soil = fields.Float(string="Wt of Can + Dry Soil",digits=(12,3))

    before_wt_water = fields.Float(
        string="Wt of Water",
        compute="_compute_before_values",
        store=True,
    )

    before_wt_can = fields.Float(string="Wt of Can",digits=(12,3))
    before_wt_dry_soil = fields.Float(string="Wt of Dry Soil",compute="_compute_before_values",store=True,digits=(12,3))
    before_mc = fields.Float(string="Moisture Content %",compute="_compute_before_values",store=True,digits=(12,6))
    before_avg_mc = fields.Float(string="Avg MC %",compute="_compute_before_values",store=True,digits=(12,5))

    @api.depends('before_can_wet_soil', 'before_can_dry_soil', 'before_wt_can')
    def _compute_before_values(self):
        for rec in self:

            # (1) Wt of Water
            rec.before_wt_water = (rec.before_can_wet_soil or 0) - (rec.before_can_dry_soil or 0)

            # (2) Wt of Dry Soil
            rec.before_wt_dry_soil = (rec.before_can_dry_soil or 0) - (rec.before_wt_can or 0)

            # (3) Moisture Content %
            if rec.before_wt_dry_soil:
                rec.before_mc = (rec.before_wt_water / rec.before_wt_dry_soil) * 100
            else:
                rec.before_mc = 0

            # (4) Avg MC % = MC %
            rec.before_avg_mc = rec.before_mc


    # -----------------------------
    # WATER CONTENT (After Test)
    # TOP
    # -----------------------------
    top_can_no = fields.Integer()
    top_can_wet_soil = fields.Float(digits=(12,3))
    top_can_dry_soil = fields.Float(digits=(12,3))
    top_wt_water = fields.Float(
        string="Wt of Water (Top)",
        compute="_compute_water_values",
        store=True,
        digits=(12, 3),
    )
    top_wt_can = fields.Float(digits=(12,3))
    top_wt_dry_soil = fields.Float(compute="_compute_wt_dry_soil", store=True,digits=(12,3))
    top_mc = fields.Float(compute="_compute_mc", store=True, digits=(12, 6))

    # -----------------------------
    # CENTRE
    # -----------------------------
    centre_can_no = fields.Integer()
    centre_can_wet_soil = fields.Float(digits=(12,3))
    centre_can_dry_soil = fields.Float(digits=(12,3))
    centre_wt_water = fields.Float(
        string="Wt of Water (Centre)",
        compute="_compute_water_values",
        store=True,
        digits=(12, 1),
    )
    centre_wt_can = fields.Float(digits=(12,3))
    centre_wt_dry_soil = fields.Float(compute="_compute_wt_dry_soil", store=True,digits=(12,3))
    centre_mc = fields.Float(compute="_compute_mc", store=True, digits=(12, 6))

    # -----------------------------
    # BOTTOM
    # -----------------------------
    bottom_can_no = fields.Integer()
    bottom_can_wet_soil = fields.Float(digits=(12,3))
    bottom_can_dry_soil = fields.Float(digits=(12,3))
    bottom_wt_water = fields.Float(
        string="Wt of Water (Bottom)",
        compute="_compute_water_values",
        store=True,
        digits=(12, 3),
    )
    bottom_wt_can = fields.Float(digits=(12,3))
    bottom_wt_dry_soil = fields.Float(compute="_compute_wt_dry_soil", store=True,digits=(12,3))
    bottom_mc = fields.Float(compute="_compute_mc", store=True, digits=(12, 6))


    avg_mc = fields.Float(string="Avg MC %",compute="_compute_mc", store=True, digits=(12, 5))

    @api.depends(
        'top_can_wet_soil', 'top_can_dry_soil',
        'centre_can_wet_soil', 'centre_can_dry_soil',
        'bottom_can_wet_soil', 'bottom_can_dry_soil',
    )
    def _compute_water_values(self):
        for rec in self:
            rec.top_wt_water = (rec.top_can_wet_soil or 0) - (rec.top_can_dry_soil or 0)
            rec.centre_wt_water = (rec.centre_can_wet_soil or 0) - (rec.centre_can_dry_soil or 0)
            rec.bottom_wt_water = (rec.bottom_can_wet_soil or 0) - (rec.bottom_can_dry_soil or 0)

    @api.depends('top_can_dry_soil', 'top_wt_can',
             'centre_can_dry_soil', 'centre_wt_can',
             'bottom_can_dry_soil', 'bottom_wt_can')
    def _compute_wt_dry_soil(self):
        for rec in self:
            rec.top_wt_dry_soil = (rec.top_can_dry_soil or 0) - (rec.top_wt_can or 0)
            rec.centre_wt_dry_soil = (rec.centre_can_dry_soil or 0) - (rec.centre_wt_can or 0)
            rec.bottom_wt_dry_soil = (rec.bottom_can_dry_soil or 0) - (rec.bottom_wt_can or 0)

    @api.depends(
    'top_wt_water', 'top_wt_dry_soil',
    'centre_wt_water', 'centre_wt_dry_soil',
    'bottom_wt_water', 'bottom_wt_dry_soil'
    )
    def _compute_mc(self):
        for rec in self:

            # ----- TOP -----
            if rec.top_wt_dry_soil:
                rec.top_mc = (rec.top_wt_water / rec.top_wt_dry_soil) * 100
            else:
                rec.top_mc = 0.0

            # ----- CENTRE -----
            if rec.centre_wt_dry_soil:
                rec.centre_mc = (rec.centre_wt_water / rec.centre_wt_dry_soil) * 100
            else:
                rec.centre_mc = 0.0

            # ----- BOTTOM -----
            if rec.bottom_wt_dry_soil:
                rec.bottom_mc = (rec.bottom_wt_water / rec.bottom_wt_dry_soil) * 100
            else:
                rec.bottom_mc = 0.0

            # ----- AVERAGE -----
            total = rec.top_mc + rec.centre_mc + rec.bottom_mc
            rec.avg_mc = total / 3 if total else 0.0

    # -----------------------------
    # CONDITION OF SPECIMEN
    # -----------------------------
    before_mould_soil = fields.Float()
    before_mould = fields.Float()
    before_soil = fields.Float(compute="_compute_soil_weights", store=True)
    before_bulk_density = fields.Float(compute="_compute_density",store=True, digits=(12,6))
    before_dry_density = fields.Float(compute="_compute_density",store=True, digits=(12,6))

    after_mould_soil = fields.Float()
    after_mould = fields.Float()
    after_soil = fields.Float(compute="_compute_soil_weights", store=True)
    after_bulk_density = fields.Float(compute="_compute_density",store=True, digits=(12,6))
    after_dry_density = fields.Float(compute="_compute_density",store=True, digits=(12,6))


    @api.depends('before_mould', 'before_mould_soil', 'after_mould', 'after_mould_soil')
    def _compute_soil_weights(self):
        for rec in self:
            rec.before_soil = (rec.before_mould_soil or 0) - (rec.before_mould or 0)
            rec.after_soil  = (rec.after_mould_soil or 0)  - (rec.after_mould or 0)

    volume_specimen1 = fields.Float()
    volume_specimen2 = fields.Float()

    @api.depends('before_soil', 'after_soil', 'volume_specimen1', 'volume_specimen2',
             'before_avg_mc', 'avg_mc')
    def _compute_density(self):
        for rec in self:

            # Before Bulk Density
            if rec.volume_specimen1:
                rec.before_bulk_density = rec.before_soil / rec.volume_specimen1
            else:
                rec.before_bulk_density = 0.0

            # After Bulk Density
            if rec.volume_specimen2:
                rec.after_bulk_density = rec.after_soil / rec.volume_specimen2
            else:
                rec.after_bulk_density = 0.0

            # Before Dry Density
            rec.before_dry_density = rec.before_bulk_density / (1 + (rec.before_avg_mc or 0) * 0.01)

            # After Dry Density
            rec.after_dry_density = rec.after_bulk_density / (1 + (rec.avg_mc or 0) * 0.01)



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
            ('fail', 'Fail')], string="Conformity", compute="_compute_fsi_conformity", store=True)

    @api.depends('fsi','eln_ref','grade')
    def _compute_fsi_conformity(self):
        
        for record in self:
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


         # DETERMINATION OF 'K'
    determination_name = fields.Char("Name",default="DETERMINATION OF 'K'")
    determination_visible = fields.Boolean("DETERMINATION OF 'K' Visible",compute="_compute_visible")
  
    dia_burette = fields.Float(string="Dia Of Burette (d) ")
    dia_specimen = fields.Float(string="Dia of Specimen (D)")
    area_burrette = fields.Float(string="Area of Burrette")
    area_specimen = fields.Float(string="Area of Specimen A")
    lenght_specimen = fields.Float(string="Length of Specimen L ")
    initial_height = fields.Float(string="Initial height ho")
    final_height = fields.Float(string="Final height h1 ")
    permeability = fields.Float(string="PERMEABILITY 'k'")


    permeability_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_permeability_conformity", store=True)

    @api.depends('permeability','eln_ref','grade')
    def _compute_permeability_conformity(self):
        
        for record in self:
            record.permeability_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5487gt21-ca64-44dd-b0ae-228aacf04965')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5487gt21-ca64-44dd-b0ae-228aacf04965')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.permeability - record.permeability*mu_value
                    upper = record.permeability + record.permeability*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.permeability_conformity = 'pass'
                        break
                    else:
                        record.permeability_conformity = 'fail'

    permeability_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_permeability_nabl", store=True)

    @api.depends('permeability','eln_ref','grade')
    def _compute_permeability_nabl(self):
        
        for record in self:
            record.permeability_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5487gt21-ca64-44dd-b0ae-228aacf04965')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5487gt21-ca64-44dd-b0ae-228aacf04965')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.permeability - record.permeability*mu_value
            upper = record.permeability + record.permeability*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.permeability_nabl = 'pass'
                break
            else:
                record.permeability_nabl = 'fail'

     # Shrinkage limit (%)
    shrinkage_limit_name = fields.Char("Name",default="Shrinkage limit")
    shrinkage_limit_visible = fields.Boolean("Shrinkage limit Visible",compute="_compute_visible")

    shrinkage_limit_table = fields.One2many('mechanical.shrinkage.limit.line1','parent_id',string="Parameter")

    shrinkage_limit1 = fields.Float(string="Shrinkage limit (%)",digits=(12,3),compute="_compute_shrinkage_limit1")

    shrinkage_limit1_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_shrinkage_limit1_conformity", store=True)

    @api.depends('shrinkage_limit1','eln_ref','grade')
    def _compute_shrinkage_limit1_conformity(self):
        
        for record in self:
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


    @api.depends('shrinkage_limit_table.shrinkage_limit')
    def _compute_shrinkage_limit1(self):
        for record in self:
            if record.shrinkage_limit_table:
                total_shrinkage_limit = sum(record.shrinkage_limit_table.mapped('shrinkage_limit'))
                average = total_shrinkage_limit / len(record.shrinkage_limit_table)
                record.shrinkage_limit1 = (average)  # ⬅️ Rounds to nearest integer
            else:
                record.shrinkage_limit1 = 0.0

   
    volume_dry_table = fields.One2many('mechanical.volume.dry.line1','parent_id',string="Parameter")
    volume_dry_name = fields.Char("Name",default="Volume of dry Pat(V2)")

    volume_wet_table = fields.One2many('mechanical.volume.wet.line1','parent_id',string="Parameter")
    volume_wet_name = fields.Char("Name",default="Volume of wet soil(V1)")

    # Permeability Falling Head Test
    # permeability_falling_name = fields.Char("Name",default="Permeability Falling Head Test")
    # permeability_falling_visible = fields.Boolean("Permeability Falling Head Test Visible",compute="_compute_visible")

   
    # length = fields.Float(string="Length of Soil Specimen (L) [cm]", digits=(12,2))
    # diameter_mold = fields.Float(string="Diameter of Mold (D) [cm]", digits=(12,2))
    # diameter_standpipe = fields.Float(string="Diameter of Stand Pipe (d) [cm]", digits=(12,2))

    # # Child lines
    # test_line_ids = fields.One2many("mechanical.permeability.line1", "parent_id", string="Test Readings")

    # # Average K
    # avg_k = fields.Float(string="Average Permeability (k) [cm/s]", compute="_compute_avg_k", store=True, digits=(12,2))

    # @api.depends("test_line_ids.k_value")
    # def _compute_avg_k(self):
    #     for rec in self:
    #         if rec.test_line_ids:
    #             vals = rec.test_line_ids.mapped("k_value")
    #             rec.avg_k = sum(vals) / len(vals)
    #         else:
    #             rec.avg_k = 0.0

    # avg_k_conformity = fields.Selection([
    #         ('pass', 'Pass'),
    #         ('fail', 'Fail')], string="Conformity", compute="_compute_avg_k_conformity", store=True)

    # @api.depends('avg_k','eln_ref','grade')
    # def _compute_avg_k_conformity(self):
        
    #     for record in self:
    #         record.avg_k_conformity = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','897546gt21-ca64-44dd-b0ae-22145687')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','897546gt21-ca64-44dd-b0ae-22145687')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 req_min = material.req_min
    #                 req_max = material.req_max
    #                 mu_value = line.mu_value
                    
    #                 lower = record.avg_k - record.avg_k*mu_value
    #                 upper = record.avg_k + record.avg_k*mu_value
    #                 if lower >= req_min and upper <= req_max:
    #                     record.avg_k_conformity = 'pass'
    #                     break
    #                 else:
    #                     record.avg_k_conformity = 'fail'

    # avg_k_nabl = fields.Selection([
    #     ('pass', 'Pass'),
    #     ('fail', 'Fail')], string="NABL", compute="_compute_avg_k_nabl", store=True)

    # @api.depends('avg_k','eln_ref','grade')
    # def _compute_avg_k_nabl(self):
        
    #     for record in self:
    #         record.avg_k_nabl = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','897546gt21-ca64-44dd-b0ae-22145687')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','897546gt21-ca64-44dd-b0ae-22145687')]).parameter_table
    #         # for material in materials:
    #         #     if material.grade.id == record.grade.id:
    #         lab_min = line.lab_min_value
    #         lab_max = line.lab_max_value
    #         mu_value = line.mu_value
            
    #         lower = record.avg_k - record.avg_k*mu_value
    #         upper = record.avg_k + record.avg_k*mu_value
    #         if lower >= lab_min and upper <= lab_max:
    #             record.avg_k_nabl = 'pass'
    #             break
    #         else:
    #             record.avg_k_nabl = 'fail'

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
            ('fail', 'Fail')], string="Conformity", compute="_compute_specific_gravity_conformity", store=True)

    @api.depends('specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_conformity(self):
        
        for record in self:
            record.specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214hhj6gt21-ca64-44dd-b0ae-6587gghty')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214hhj6gt21-ca64-44dd-b0ae-6587gghty')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214hhj6gt21-ca64-44dd-b0ae-6587gghty')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214hhj6gt21-ca64-44dd-b0ae-6587gghty')]).parameter_table
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


     # Direct Shear Test
    direct_shear_name = fields.Char("Name",default="Direct Shear Test")
    direct_shear_visible = fields.Boolean("Direct Shear Test Visible",compute="_compute_visible")

    proving_ring_constant = fields.Float(string="Proving Ring Constant (k)", digits=(12,3))

    direct_shear_ids = fields.One2many("mechanical.direct.shear.test.line1", "parent_id", string="Test Readings")

    avg_shear_stress = fields.Float(
        string="Average Shear Stress (τ_avg) ",
        compute="_compute_avg_shear_stress",
        store=True,
        digits=(12,2))

    @api.depends("direct_shear_ids.shear_stress")
    def _compute_avg_shear_stress(self):
        for rec in self:
            vals = [line.shear_stress for line in rec.direct_shear_ids if line.shear_stress is not None]
            rec.avg_shear_stress = round(sum(vals)/len(vals), 2) if vals else 0.0
    
    avg_shear_stress_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_shear_stress_conformity", store=True)

    @api.depends('avg_shear_stress','eln_ref','grade')
    def _compute_avg_shear_stress_conformity(self):
        
        for record in self:
            record.avg_shear_stress_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457888hhhllly1-ca64-44dd-b0ae-3214hhhtr')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457888hhhllly1-ca64-44dd-b0ae-3214hhhtr')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_shear_stress - record.avg_shear_stress*mu_value
                    upper = record.avg_shear_stress + record.avg_shear_stress*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_shear_stress_conformity = 'pass'
                        break
                    else:
                        record.avg_shear_stress_conformity = 'fail'

    avg_shear_stress_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_shear_stress_nabl", store=True)

    @api.depends('avg_shear_stress','eln_ref','grade')
    def _compute_avg_shear_stress_nabl(self):
        
        for record in self:
            record.avg_shear_stress_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457888hhhllly1-ca64-44dd-b0ae-3214hhhtr')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457888hhhllly1-ca64-44dd-b0ae-3214hhhtr')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_shear_stress - record.avg_shear_stress*mu_value
            upper = record.avg_shear_stress + record.avg_shear_stress*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_shear_stress_nabl = 'pass'
                break
            else:
                record.avg_shear_stress_nabl = 'fail'


      # Unconfined Compressive Strength (UCS) Test
    ucs_name = fields.Char("Name",default="Unconfined Compressive Strength (UCS) Test")
    ucs_visible = fields.Boolean("Unconfined Compressive Strength (UCS) Test Visible",compute="_compute_visible")

    initial_diameter = fields.Float(string="Initial Diameter of Specimen (D0) ", digits=(12,3))
    initial_length = fields.Float(string="Initial Length of Specimen (L0) ", digits=(12,3))
    initial_density = fields.Float(string="Initial Density of Specimen ", digits=(12,3))
    proving_ring_constant = fields.Float(string="Proving Ring Constant (K) ", digits=(12,3))

    ucs_ids = fields.One2many("mechanical.ucs.test.line1", "parent_id", string="Test Readings")

    avg_stress = fields.Float(string="Average Stress", compute="_compute_avg_stress", store=True, digits=(12,3))
    avg_strain = fields.Float(string="Average Axial Strain", compute="_compute_avg_stress", store=True, digits=(12,3))

    @api.depends("ucs_ids.stress", "ucs_ids.axial_strain")
    def _compute_avg_stress(self):
        for rec in self:
            stresses = [line.stress for line in rec.ucs_ids if line.stress is not None]
            strains = [line.axial_strain for line in rec.ucs_ids if line.axial_strain is not None]
            rec.avg_stress = round(sum(stresses)/len(stresses),3) if stresses else 0.0
            rec.avg_strain = round(sum(strains)/len(strains),3) if strains else 0.0

    avg_stress_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_stress_conformity", store=True)

    @api.depends('avg_stress','eln_ref','grade')
    def _compute_avg_stress_conformity(self):
        
        for record in self:
            record.avg_stress_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','t4y57888hhhllly1-ca64-44dd-b0ae-1234567rt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','t4y57888hhhllly1-ca64-44dd-b0ae-1234567rt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_stress - record.avg_stress*mu_value
                    upper = record.avg_stress + record.avg_stress*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_stress_conformity = 'pass'
                        break
                    else:
                        record.avg_stress_conformity = 'fail'

    avg_stress_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_stress_nabl", store=True)

    @api.depends('avg_stress','eln_ref','grade')
    def _compute_avg_stress_nabl(self):
        
        for record in self:
            record.avg_stress_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','t4y57888hhhllly1-ca64-44dd-b0ae-1234567rt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','t4y57888hhhllly1-ca64-44dd-b0ae-1234567rt')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_stress - record.avg_stress*mu_value
            upper = record.avg_stress + record.avg_stress*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_stress_nabl = 'pass'
                break
            else:
                record.avg_stress_nabl = 'fail'

     # Consolidation Test (Cc) Test
    # consolidation_name = fields.Char("Name",default="Consolidation Test (Cc)")
    # consolidation_visible = fields.Boolean("Consolidation Test (Cc) Visible",compute="_compute_visible")

    # initial_height = fields.Float(string="Initial Height H0 ", digits=(12,3))
    # diameter = fields.Float(string="Diameter D0 ", digits=(12,3))
    # area = fields.Float(string="Area ", compute="_compute_area", store=True, digits=(12,3))
    # initial_void_ratio = fields.Float(string="Initial Void Ratio e0", digits=(12,3))

    # consolidation_name_ids = fields.One2many("mechanical.consolidation.test.line1", "parent_id", string="Test Lines")

    # compression_index = fields.Float(string="Compression Index Cc", compute="_compute_cc", store=True, digits=(12,3))

    # compression_index_conformity = fields.Selection([
    #         ('pass', 'Pass'),
    #         ('fail', 'Fail')], string="Conformity", compute="_compute_compression_index_conformity", store=True)

    # @api.depends('compression_index','eln_ref','grade')
    # def _compute_compression_index_conformity(self):
        
    #     for record in self:
    #         record.compression_index_conformity = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78957888hhhllly1-ca64-44dd-b0ae-2314780ty')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78957888hhhllly1-ca64-44dd-b0ae-2314780ty')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 req_min = material.req_min
    #                 req_max = material.req_max
    #                 mu_value = line.mu_value
                    
    #                 lower = record.compression_index - record.compression_index*mu_value
    #                 upper = record.compression_index + record.compression_index*mu_value
    #                 if lower >= req_min and upper <= req_max:
    #                     record.compression_index_conformity = 'pass'
    #                     break
    #                 else:
    #                     record.compression_index_conformity = 'fail'

    # compression_index_nabl = fields.Selection([
    #     ('pass', 'Pass'),
    #     ('fail', 'Fail')], string="NABL", compute="_compute_compression_index_nabl", store=True)

    # @api.depends('compression_index','eln_ref','grade')
    # def _compute_compression_index_nabl(self):
        
    #     for record in self:
    #         record.compression_index_nabl = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78957888hhhllly1-ca64-44dd-b0ae-2314780ty')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78957888hhhllly1-ca64-44dd-b0ae-2314780ty')]).parameter_table
    #         # for material in materials:
    #         #     if material.grade.id == record.grade.id:
    #         lab_min = line.lab_min_value
    #         lab_max = line.lab_max_value
    #         mu_value = line.mu_value
            
    #         lower = record.compression_index - record.compression_index*mu_value
    #         upper = record.compression_index + record.compression_index*mu_value
    #         if lower >= lab_min and upper <= lab_max:
    #             record.compression_index_nabl = 'pass'
    #             break
    #         else:
    #             record.compression_index_nabl = 'fail'

    # @api.depends("diameter")
    # def _compute_area(self):
    #     for rec in self:
    #         if rec.diameter:
    #             radius = rec.diameter / 2.0 / 10  # mm to cm
    #             rec.area = math.pi * radius**2
    #         else:
    #             rec.area = 0.0

    # @api.depends("consolidation_name_ids.void_ratio")
    # def _compute_cc(self):
    #     # Simple approximation: slope of virgin compression line
    #     for rec in self:
    #         lines = sorted(rec.consolidation_name_ids, key=lambda l: l.stress or 0)
    #         if len(lines) >= 2:
    #             e1, e2 = lines[0].void_ratio, lines[-1].void_ratio
    #             sigma1, sigma2 = lines[0].stress, lines[-1].stress
    #             if sigma1 > 0 and sigma2 > 0:
    #                 rec.compression_index = round((e1 - e2) / (math.log10(sigma2) - math.log10(sigma1)), 3)
    #             else:
    #                 rec.compression_index = 0.0
    #         else:
    #             rec.compression_index = 0.0

    # Consolidation Test (Pc) Test
    consolidation_pc_name = fields.Char("Name",default="Consolidation Test (Pc)")
    consolidation_pc_visible = fields.Boolean("Consolidation Test (Pc) Visible",compute="_compute_visible")

    initial_height_pc = fields.Float(string="Initial Height H0 ")
    diameter_pc = fields.Float(string="Diameter D0 ")
    area_pc = fields.Float(string="Area ", compute="_compute_area_pc", store=True)
    initial_void_ratio_pc = fields.Float(string="Initial Void Ratio e0")

    consolidation_pc_ids = fields.One2many("mechanical.consolidation.test.pc.line1", "parent_id", string="Test Lines")

    preconsolidation_pressure = fields.Float(string="Preconsolidation Pressure Pc ", compute="_compute_preconsolidation_pressure", store=True)

    preconsolidation_pressure_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_preconsolidation_pressure_conformity", store=True)

    @api.depends('preconsolidation_pressure','eln_ref','grade')
    def _compute_preconsolidation_pressure_conformity(self):
        
        for record in self:
            record.preconsolidation_pressure_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98ggh7888hhhllly1-ca64-44dd-b0ae-6547ggt0r')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98ggh7888hhhllly1-ca64-44dd-b0ae-6547ggt0r')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.preconsolidation_pressure - record.preconsolidation_pressure*mu_value
                    upper = record.preconsolidation_pressure + record.preconsolidation_pressure*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.preconsolidation_pressure_conformity = 'pass'
                        break
                    else:
                        record.preconsolidation_pressure_conformity = 'fail'

    preconsolidation_pressure_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_preconsolidation_pressure_nabl", store=True)

    @api.depends('preconsolidation_pressure','eln_ref','grade')
    def _compute_preconsolidation_pressure_nabl(self):
        
        for record in self:
            record.preconsolidation_pressure_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98ggh7888hhhllly1-ca64-44dd-b0ae-6547ggt0r')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98ggh7888hhhllly1-ca64-44dd-b0ae-6547ggt0r')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.preconsolidation_pressure - record.preconsolidation_pressure*mu_value
            upper = record.preconsolidation_pressure + record.preconsolidation_pressure*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.preconsolidation_pressure_nabl = 'pass'
                break
            else:
                record.preconsolidation_pressure_nabl = 'fail'

    @api.depends("diameter_pc")
    def _compute_area_pc(self):
        for rec in self:
            if rec.diameter_pc:
                radius = rec.diameter_pc / 2.0 / 10  # mm to cm
                rec.area_pc = math.pi * radius**2
            else:
                rec.area_pc = 0.0

    @api.depends('consolidation_pc_ids.void_ratio_pc')
    def _compute_preconsolidation_pressure(self):
        for record in self:
            if record.consolidation_pc_ids:
                total_preconsolidation_pressure = sum(record.consolidation_pc_ids.mapped('void_ratio_pc'))
                average = total_preconsolidation_pressure / len(record.consolidation_pc_ids)
                record.preconsolidation_pressure = (average)  # ⬅️ Rounds to nearest integer
            else:
                record.preconsolidation_pressure = 0.0


     # Direct Shear Test (Angle of Friction)
    angle_shear_name = fields.Char("Name",default="Direct Shear Test (Angle of Friction)")
    angle_shear_visible = fields.Boolean("Direct Shear Test (Angle of Friction) Visible",compute="_compute_visible")
     

    angleshear_line_ids = fields.One2many('mechanical.soil.direct.shear.line1', 'parent_id', string="Test lines")
    phi_deg = fields.Float(string="Angle of Internal Friction φ (°)", compute="_compute_phi_cohesion_direct", store=True)
    cohesion = fields.Float(string="Cohesion c (kPa)", compute="_compute_phi_cohesion_direct", store=True)

    phi_deg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_phi_deg_conformity", store=True)

    @api.depends('phi_deg','eln_ref','grade')
    def _compute_phi_deg_conformity(self):
        
        for record in self:
            record.phi_deg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','00fh7888hhhllly1-ca64-44dd-b0ae-897456ghtr')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','00fh7888hhhllly1-ca64-44dd-b0ae-897456ghtr')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.phi_deg - record.phi_deg*mu_value
                    upper = record.phi_deg + record.phi_deg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.phi_deg_conformity = 'pass'
                        break
                    else:
                        record.phi_deg_conformity = 'fail'

    phi_deg_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_phi_deg_nabl", store=True)

    @api.depends('phi_deg','eln_ref','grade')
    def _compute_phi_deg_nabl(self):
        
        for record in self:
            record.phi_deg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','00fh7888hhhllly1-ca64-44dd-b0ae-897456ghtr')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','00fh7888hhhllly1-ca64-44dd-b0ae-897456ghtr')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.phi_deg - record.phi_deg*mu_value
            upper = record.phi_deg + record.phi_deg*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.phi_deg_nabl = 'pass'
                break
            else:
                record.phi_deg_nabl = 'fail'

    @api.depends('angleshear_line_ids.normal_stress', 'angleshear_line_ids.shear_strength')
    def _compute_phi_cohesion_direct(self):
        for rec in self:
            lines = rec.angleshear_line_ids.filtered(lambda l: l.normal_stress is not None and l.shear_strength is not None)
            n = len(lines)
            if n < 2:
                rec.phi_deg = 0.0
                rec.cohesion = 0.0
                continue

            # Ordinary least squares for tau = c + m*sigma
            sigma = [l.normal_stress for l in lines]
            tau = [l.shear_strength for l in lines]

            sum_sigma = sum(sigma)
            sum_tau = sum(tau)
            sum_sigma_tau = sum(s * t for s, t in zip(sigma, tau))
            sum_sigma2 = sum(s * s for s in sigma)

            denom = (n * sum_sigma2) - (sum_sigma ** 2)
            if abs(denom) < 1e-12:
                # degenerate case: all sigma equal
                # fallback to two-point if possible
                rec.phi_deg = 0.0
                rec.cohesion = 0.0
                continue

            m = (n * sum_sigma_tau - sum_sigma * sum_tau) / denom  # m = tan(phi)
            c = (sum_tau - m * sum_sigma) / n

            # convert m to degrees
            phi_rad = math.atan(m)
            phi_deg = phi_rad * 180.0 / math.pi

            rec.phi_deg = phi_deg
            rec.cohesion = c

      # Swelling Pressure by Consolidometer Method
    # swelling_pressure_name = fields.Char("Name",default="Swelling Pressure by Consolidometer Method")
    # swelling_pressure_visible = fields.Boolean("Swelling Pressure by Consolidometer Method Visible",compute="_compute_visible")

    # swelling_pressure_line_ids = fields.One2many(
    #     'mechanical.swelling.line1',
    #     'parent_id',
    #     string="swelling_pressure Table"
    # )

    # # Final result (average swelling pressure)
    # avg_swelling_pressure = fields.Float(
    #     string="Average Swelling ",
    #     compute="_compute_avg_swelling_pressure",
    #     store=True
    # )


    # avg_swelling_pressure_conformity = fields.Selection([
    #         ('pass', 'Pass'),
    #         ('fail', 'Fail')], string="Conformity", compute="_compute_avg_swelling_pressure_conformity", store=True)

    # @api.depends('avg_swelling_pressure','eln_ref','grade')
    # def _compute_avg_swelling_pressure_conformity(self):
        
    #     for record in self:
    #         record.avg_swelling_pressure_conformity = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9521yt88hhhllly1-ca64-44dd-b0ae-8974578ghtr2')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9521yt88hhhllly1-ca64-44dd-b0ae-8974578ghtr2')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 req_min = material.req_min
    #                 req_max = material.req_max
    #                 mu_value = line.mu_value
                    
    #                 lower = record.avg_swelling_pressure - record.avg_swelling_pressure*mu_value
    #                 upper = record.avg_swelling_pressure + record.avg_swelling_pressure*mu_value
    #                 if lower >= req_min and upper <= req_max:
    #                     record.avg_swelling_pressure_conformity = 'pass'
    #                     break
    #                 else:
    #                     record.avg_swelling_pressure_conformity = 'fail'

    # avg_swelling_pressure_nabl = fields.Selection([
    #     ('pass', 'Pass'),
    #     ('fail', 'Fail')], string="NABL", compute="_compute_avg_swelling_pressure_nabl", store=True)

    # @api.depends('avg_swelling_pressure','eln_ref','grade')
    # def _compute_avg_swelling_pressure_nabl(self):
        
    #     for record in self:
    #         record.avg_swelling_pressure_nabl = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9521yt88hhhllly1-ca64-44dd-b0ae-8974578ghtr2')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9521yt88hhhllly1-ca64-44dd-b0ae-8974578ghtr2')]).parameter_table
    #         # for material in materials:
    #         #     if material.grade.id == record.grade.id:
    #         lab_min = line.lab_min_value
    #         lab_max = line.lab_max_value
    #         mu_value = line.mu_value
            
    #         lower = record.avg_swelling_pressure - record.avg_swelling_pressure*mu_value
    #         upper = record.avg_swelling_pressure + record.avg_swelling_pressure*mu_value
    #         if lower >= lab_min and upper <= lab_max:
    #             record.avg_swelling_pressure_nabl = 'pass'
    #             break
    #         else:
    #             record.avg_swelling_pressure_nabl = 'fail'

    # @api.depends('swelling_pressure_line_ids.swelling_pressure')
    # def _compute_avg_swelling_pressure(self):
    #     for rec in self:
    #         if rec.swelling_pressure_line_ids:
    #             total = sum(rec.swelling_pressure_line_ids.mapped('swelling_pressure'))
    #             rec.avg_swelling_pressure = total / len(rec.swelling_pressure_line_ids)
    #         else:
    #             rec.avg_swelling_pressure = 0.0

     # Unconsolidated Undrained Triaxial Test (Angle of Friction)
    uu_triaxial_angle_name = fields.Char("Name",default="Unconsolidated Undrained Triaxial Test (Angle of Friction)")
    uu_triaxial_angle_visible = fields.Boolean("Unconsolidated Undrained Triaxial Test (Angle of Friction) Visible",compute="_compute_visible")

    uu_triaxial_angle_line_ids = fields.One2many("mechanical.uu.triaxial.line1", "parent_id", string="Test Observations")

    phi_deg_uu_triaxial_angle = fields.Float(string="Angle of Friction φ (°)", compute="_compute_phi_c", store=True)
    cohesion_uu_triaxial_angle = fields.Float(string="Cohesion c (kPa)", compute="_compute_phi_c", store=True)

    phi_deg_uu_triaxial_angle_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_phi_deg_uu_triaxial_angle_conformity", store=True)

    @api.depends('phi_deg_uu_triaxial_angle','eln_ref','grade')
    def _compute_phi_deg_uu_triaxial_angle_conformity(self):
        
        for record in self:
            record.phi_deg_uu_triaxial_angle_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65478h88hhhllly1-ca64-44dd-b0ae-89745785gt41d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65478h88hhhllly1-ca64-44dd-b0ae-89745785gt41d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.phi_deg_uu_triaxial_angle - record.phi_deg_uu_triaxial_angle*mu_value
                    upper = record.phi_deg_uu_triaxial_angle + record.phi_deg_uu_triaxial_angle*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.phi_deg_uu_triaxial_angle_conformity = 'pass'
                        break
                    else:
                        record.phi_deg_uu_triaxial_angle_conformity = 'fail'

    phi_deg_uu_triaxial_angle_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_phi_deg_uu_triaxial_angle_nabl", store=True)

    @api.depends('phi_deg_uu_triaxial_angle','eln_ref','grade')
    def _compute_phi_deg_uu_triaxial_angle_nabl(self):
        
        for record in self:
            record.phi_deg_uu_triaxial_angle_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65478h88hhhllly1-ca64-44dd-b0ae-89745785gt41d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65478h88hhhllly1-ca64-44dd-b0ae-89745785gt41d')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.phi_deg_uu_triaxial_angle - record.phi_deg_uu_triaxial_angle*mu_value
            upper = record.phi_deg_uu_triaxial_angle + record.phi_deg_uu_triaxial_angle*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.phi_deg_uu_triaxial_angle_nabl = 'pass'
                break
            else:
                record.phi_deg_uu_triaxial_angle_nabl = 'fail'

    @api.depends("uu_triaxial_angle_line_ids.sigma", "uu_triaxial_angle_line_ids.tau")
    def _compute_phi_c(self):
        for rec in self:
            lines = rec.uu_triaxial_angle_line_ids

            # किमान 2 data points असले पाहिजेत
            if not lines or len(lines) < 2:
                rec.phi_deg_uu_triaxial_angle = 0.0
                rec.cohesion_uu_triaxial_angle = 0.0
                continue

            slopes = []
            intercepts = []

            # सर्व सलग points वरून slope व intercept काढा
            for i in range(len(lines) - 1):
                p1 = lines[i]
                p2 = lines[i + 1]

                if (p2.sigma - p1.sigma) == 0:
                    continue

                m = (p2.tau - p1.tau) / (p2.sigma - p1.sigma)
                c = p1.tau - m * p1.sigma
                slopes.append(m)
                intercepts.append(c)

            if not slopes:
                rec.phi_deg_uu_triaxial_angle = 0.0
                rec.cohesion_uu_triaxial_angle = 0.0
                continue

            avg_m = sum(slopes) / len(slopes)
            avg_c = sum(intercepts) / len(intercepts)

            phi_rad = math.atan(avg_m)
            phi_deg = phi_rad * 180.0 / math.pi

            rec.phi_deg_uu_triaxial_angle = round(phi_deg, 3)
            rec.cohesion_uu_triaxial_angle = round(avg_c, 3)

      # Unconsolidated Undrained Triaxial Test (Angle of Friction)
    uu_triaxial_cohesion_name = fields.Char("Name",default="Unconsolidated Undrained Triaxial Test (Cohesion)")
    uu_triaxial_cohesion_visible = fields.Boolean("Unconsolidated Undrained Triaxial Test (Cohesion) Visible",compute="_compute_visible")

    uu_triaxial_cohesion_line_ids = fields.One2many("mechanical.uu.triaxial.cohesion.line1", "parent_id", string="Test Observations")

    phi_deg_uu_triaxial_cohesion = fields.Float(string="Angle of Friction φ (°)", compute="_compute_phi_cohesion", store=True)
    cohesion_uu_triaxial_cohesion = fields.Float(string="Cohesion c (kPa)", compute="_compute_phi_cohesion", store=True)

    cohesion_uu_triaxial_cohesion_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_cohesion_uu_triaxial_cohesion_conformity", store=True)

    @api.depends('cohesion_uu_triaxial_cohesion','eln_ref','grade')
    def _compute_cohesion_uu_triaxial_cohesion_conformity(self):
        
        for record in self:
            record.cohesion_uu_triaxial_cohesion_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2r478h88hhhllly1-ca64-44dd-b0ae-897897gghtre0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2r478h88hhhllly1-ca64-44dd-b0ae-897897gghtre0')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.cohesion_uu_triaxial_cohesion - record.cohesion_uu_triaxial_cohesion*mu_value
                    upper = record.cohesion_uu_triaxial_cohesion + record.cohesion_uu_triaxial_cohesion*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.cohesion_uu_triaxial_cohesion_conformity = 'pass'
                        break
                    else:
                        record.cohesion_uu_triaxial_cohesion_conformity = 'fail'

    cohesion_uu_triaxial_cohesion_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_cohesion_uu_triaxial_cohesion_nabl", store=True)

    @api.depends('cohesion_uu_triaxial_cohesion','eln_ref','grade')
    def _compute_cohesion_uu_triaxial_cohesion_nabl(self):
        
        for record in self:
            record.cohesion_uu_triaxial_cohesion_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2r478h88hhhllly1-ca64-44dd-b0ae-897897gghtre0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2r478h88hhhllly1-ca64-44dd-b0ae-897897gghtre0')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.cohesion_uu_triaxial_cohesion - record.cohesion_uu_triaxial_cohesion*mu_value
            upper = record.cohesion_uu_triaxial_cohesion + record.cohesion_uu_triaxial_cohesion*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.cohesion_uu_triaxial_cohesion_nabl = 'pass'
                break
            else:
                record.cohesion_uu_triaxial_cohesion_nabl = 'fail'

    @api.depends("uu_triaxial_cohesion_line_ids.sigma", "uu_triaxial_cohesion_line_ids.tau")
    def _compute_phi_cohesion(self):
        for rec in self:
            lines = rec.uu_triaxial_cohesion_line_ids

            # किमान 2 data points असले पाहिजेत
            if not lines or len(lines) < 2:
                rec.phi_deg_uu_triaxial_cohesion = 0.0
                rec.cohesion_uu_triaxial_cohesion = 0.0
                continue

            slopes = []
            intercepts = []

            # सर्व सलग points वरून slope व intercept काढा
            for i in range(len(lines) - 1):
                p1 = lines[i]
                p2 = lines[i + 1]

                if (p2.sigma - p1.sigma) == 0:
                    continue

                m = (p2.tau - p1.tau) / (p2.sigma - p1.sigma)
                c = p1.tau - m * p1.sigma
                slopes.append(m)
                intercepts.append(c)

            if not slopes:
                rec.phi_deg_uu_triaxial_cohesion = 0.0
                rec.cohesion_uu_triaxial_cohesion = 0.0
                continue

            avg_m = sum(slopes) / len(slopes)
            avg_c = sum(intercepts) / len(intercepts)

            phi_rad = math.atan(avg_m)
            phi_deg = phi_rad * 180.0 / math.pi

            rec.phi_deg_uu_triaxial_cohesion = round(phi_deg, 3)
            rec.cohesion_uu_triaxial_cohesion = round(avg_c, 3)

#    Start GSA Parameter
    gsa_name = fields.Char("Name",default="Grain Size Analysis (GSA)")

    gsa_child_lines = fields.One2many('mechanical.gsa.line','parent_id')
    gsa_visible = fields.Boolean("Grain Size Analysis (GSA) Visible",compute="_compute_visible")

    show_sieve = fields.Boolean(default=False)

   

    gsa_lines_generated = fields.Boolean(string="GSA Lines Generated",default=False)

   

    def action_generate_gsa_lines(self):
        for record in self:
            if record.lab_id and ' - ' in record.lab_id:
                start_str, end_str = record.lab_id.split(' - ')
                prefix = '-'.join(start_str.split('-')[:2])
                start = int(start_str.split('-')[2])
                end = int(end_str.split('-')[2])

                lines = []
                for i in range(start, end + 1):
                    lab_no = f"{prefix}-{str(i).zfill(3)}"
                    lines.append((0, 0, {'lab_no': lab_no}))

                record.gsa_child_lines = lines
                record.gsa_lines_generated = True

            # 🔹 Set flag to show sieve analysis
            if record.gsa_child_lines:
                record.show_sieve = True

            # 🔹 Reload the current record in form view
            return {
                'type': 'ir.actions.act_window',
                'name': 'Soil Form',
                'res_model': 'mechanical.soil1',
                'res_id': record.id,  # ✅ Use record.id instead of self.id
                'view_mode': 'form',
                'target': 'current',
            }

    gsa_graph_image = fields.Binary(
        string="GSA Graph Image",
        attachment=True,
        help="Grain Size Analysis चा तयार केलेला आलेख."
    )
    gsa_graph_filename = fields.Char(
        string="Graph Filename",
        default="gsa_curve.png"
    )


    

    # def action_generate_gsa_graph(self):
    #     for record in self:
    #         # 1. Initialize Plot
    #         fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
            
    #         # 2. Configure Axes limits
    #         ax.set_xscale('log')
    #         ax.set_xlim(0.001, 100)  
    #         ax.set_ylim(0, 110)      

    #         # 3. Labels
    #         ax.set_xlabel("Particle Diameter (mm)", fontsize=10, fontweight='bold')
    #         ax.set_ylabel("Percentage Finer (%)", fontsize=10, fontweight='bold')

    #         # 4. Grid
    #         ax.grid(True, which='major', axis='both', linestyle='-', linewidth=0.8, color='#404040', alpha=0.6)
    #         ax.grid(True, which='minor', axis='both', linestyle='-', linewidth=0.5, color='#a0a0a0', alpha=0.4)

    #         # 5. Format X-Axis Ticks
    #         locmaj = ticker.LogLocator(base=10.0, subs=(1.0,), numticks=100)
    #         ax.xaxis.set_major_locator(locmaj)
            
    #         def nice_log_formatter(x, pos):
    #             if x in [0.001, 0.01, 0.1, 1, 10, 100]:
    #                 return f"{x:g}" 
    #             return ""
    #         ax.xaxis.set_major_formatter(ticker.FuncFormatter(nice_log_formatter))
    #         ax.yaxis.set_major_locator(ticker.MultipleLocator(10))

    #         # --- MARKER LIST (Vegvegle Symbols) ---
    #         # 'o' = Circle, '^' = Triangle Up, 's' = Square, 'D' = Diamond, 'x' = Cross, '*' = Star
    #         marker_cycle = itertools.cycle(['^', '*', 'D', 'x', 'o', 's', 'v', '+'])

    #         # 6. Plot Data
    #         data_plotted = False
            
    #         if record.gsa_child_lines:
    #             for sample in record.gsa_child_lines:
    #                 data_pairs = []

    #                 # Pratyek sample sathi navin symbol ghyaycha
    #                 current_marker = next(marker_cycle)

    #                 for line in sample.sieve_analysis_child_lines_gsa:
    #                     if line.sieve_size and line.passing_percent is not None:
    #                         try:
    #                             # String clean kara
    #                             size_str = str(line.sieve_size).lower().replace('mm', '').strip()
    #                             if 'pan' in size_str:
    #                                 continue 

    #                             # 5 digit rounding logic
    #                             size_val = round(float(size_str), 5)
    #                             pass_val = line.passing_percent

    #                             if 0.001 <= size_val <= 100:
    #                                 data_pairs.append((size_val, pass_val))
    #                         except ValueError:
    #                             continue
                    
    #                 # Sort: Smallest -> Largest
    #                 data_pairs.sort(key=lambda x: x[0]) 

    #                 if data_pairs:
    #                     sizes = [x[0] for x in data_pairs]
    #                     passing = [x[1] for x in data_pairs]

    #                     # --- CHANGE: marker=current_marker vaparla ahe ---
    #                     ax.plot(sizes, passing, marker=current_marker, markersize=6, linewidth=2, label=sample.lab_no or "Sample")
    #                     data_plotted = True

    #         # Legend
    #         if data_plotted:
    #             ax.legend(loc='lower right', fontsize=9)

    #         # 7. Save Image
    #         buffer = io.BytesIO()
    #         plt.savefig(buffer, format='png', bbox_inches='tight') 
    #         plt.close(fig)
    #         buffer.seek(0)
            
    #         record.gsa_graph_image = base64.b64encode(buffer.read())
    #         buffer.close()

    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Soil Form',
    #         'res_model': 'mechanical.soil1',
    #         'res_id': record.id,
    #         'view_mode': 'form',
    #         'target': 'current',
    #     }

    def action_generate_gsa_graph(self):
        for record in self:
            # 1. Initialize Plot
            fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
            
            # 2. Configure Axes limits
            ax.set_xscale('log')
            ax.set_xlim(0.001, 100)  
            ax.set_ylim(0, 110)      

            # 3. Labels
            ax.set_xlabel("Particle Diameter (mm)", fontsize=10, fontweight='bold')
            ax.set_ylabel("Percentage Finer (%)", fontsize=10, fontweight='bold')

            # 4. Grid
            ax.grid(True, which='major', axis='both', linestyle='-', linewidth=0.8, color='#404040', alpha=0.6)
            ax.grid(True, which='minor', axis='both', linestyle='-', linewidth=0.5, color='#a0a0a0', alpha=0.4)

            # 5. Format X-Axis Ticks
            locmaj = ticker.LogLocator(base=10.0, subs=(1.0,), numticks=100)
            ax.xaxis.set_major_locator(locmaj)
            
            def nice_log_formatter(x, pos):
                if x in [0.001, 0.01, 0.1, 1, 10, 100]:
                    return f"{x:g}" 
                return ""
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(nice_log_formatter))
            ax.yaxis.set_major_locator(ticker.MultipleLocator(10))

            # --- MARKER LIST ---
            # He symbols sequence ne vaparle jatil
            marker_cycle = itertools.cycle(['^', '*', 'D', 'x', 'o', 's', 'v', '+'])
         
            # 6. Plot Data
            data_plotted = False
            
            if record.gsa_child_lines:
                for sample in record.gsa_child_lines:
                    data_pairs = []

                    # 1. New Marker Select kara
                    current_marker = next(marker_cycle)

                    # --- CHANGE HERE: Save Symbol to Odoo Field ---
                    # Jo marker graph sathi niwdla ahe, to 'symbol' field madhe save kara
                    sample.symbol = current_marker
                    # ----------------------------------------------

                    for line in sample.sieve_analysis_child_lines_gsa:
                        if line.sieve_size and line.passing_percent is not None:
                            try:
                                # String clean kara
                                size_str = str(line.sieve_size).lower().replace('mm', '').strip()
                                if 'pan' in size_str:
                                    continue 

                                # 5 digit rounding
                                size_val = round(float(size_str), 5)
                                pass_val = line.passing_percent

                                if 0.001 <= size_val <= 100:
                                    data_pairs.append((size_val, pass_val))
                            except ValueError:
                                continue
                    
                    # Sort: Smallest -> Largest
                    data_pairs.sort(key=lambda x: x[0]) 

                    if data_pairs:
                        sizes = [x[0] for x in data_pairs]
                        passing = [x[1] for x in data_pairs]

                        # Plotting with the selected marker
                        ax.plot(sizes, passing, marker=current_marker, markersize=6, linewidth=2, label=sample.lab_no or "Sample")
                        data_plotted = True

            # Legend
            if data_plotted:
                ax.legend(loc='lower right', fontsize=9)

            # 7. Save Image
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight') 
            plt.close(fig)
            buffer.seek(0)
            
            record.gsa_graph_image = base64.b64encode(buffer.read())
            buffer.close()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Soil Form',
            'res_model': 'mechanical.soil1',
            'res_id': record.id,
            'view_mode': 'form',
            'target': 'current',
        }

    

         # DETERMINATION OF CONSOLIDATION PROPERTIES		
    consolidation_name = fields.Char("Name",default="DETERMINATION OF CONSOLIDATION PROPERTIES")
    consolidation_visible = fields.Boolean("DETERMINATION OF CONSOLIDATION PROPERTIES",compute="_compute_visible")	

    consolidation_specific_gravity = fields.Float(string="Specific Gravity, G" , digits=(8,3))
    consolidation_diameter = fields.Float(string="Diameter, D", digits=(8,1))
    consolidation_height = fields.Float(string="Height, H", digits=(8,1))
    consolidation_area = fields.Float(string="Area, A", compute="_compute_consolidation_area", digits=(8,3))
    consolidation_volume = fields.Float(string="Volume, Vol", compute="_compute_consolidation_volume", digits=(8,3))

    @api.depends('consolidation_diameter')
    def _compute_consolidation_area(self):
        for line in self:
            if line.consolidation_diameter:
                line.consolidation_area = (pi / 4) * (line.consolidation_diameter ** 2)
            else:
              line.consolidation_area = 0
    
    @api.depends('consolidation_height','consolidation_area','consolidation_diameter')
    def _compute_consolidation_volume(self):
        for line in self:
            area = (pi / 4) * (line.consolidation_diameter ** 2)
            if line.consolidation_height and line.consolidation_area:
                line.consolidation_volume = line.consolidation_height * area
            else:
              line.consolidation_volume = 0

    con_wt_of_ring = fields.Float(string="Weight Of Ring, w1" , digits=(10,3)) 
    con_wt_wet_specimen_bf = fields.Float(string="Weight Of Wet Specimen + Ring, w2" , digits=(10,3))  # before test
    con_wt_wet_specimen_af = fields.Float(string="Weight Of Wet Specimen + Ring, w5" , digits=(10,3))  # after test
    con_wt_dry_specimen_af = fields.Float(string="Weight Of Dry Specimen + Ring, w3" , digits=(10,3))  # after test

    con_wt_dry_soil = fields.Float(string= "Weight Of Dry Specimen + Ring, w4", compute="_compute_con_wt_dry_soil", digits=(10,3))

    con_height_solid = fields.Float(string= "Height of Solids, Hs", compute="_compute_con_height_solid", digits=(10,4))

    @api.depends('con_wt_dry_specimen_af','con_wt_of_ring')
    def _compute_con_wt_dry_soil(self):
        for line in self:
                line.con_wt_dry_soil = line.con_wt_dry_specimen_af - line.con_wt_of_ring


    @api.depends('con_wt_dry_specimen_af','con_wt_of_ring','consolidation_area','consolidation_specific_gravity')
    def _compute_con_height_solid(self):
        for line in self:
            dry_soil = line.con_wt_dry_specimen_af - line.con_wt_of_ring

            if line.consolidation_specific_gravity and line.consolidation_area:
                line.con_height_solid = dry_soil / (line.consolidation_area * line.consolidation_specific_gravity)
            else:
              line.con_height_solid = 0   

    con_water_content = fields.Float(string= "Water Content, wc", compute="_compute_con_water_content", digits=(8,2)) 
    con_bulk_density_soil = fields.Float(string= "Bulk Density of Soil, γb", compute="_compute_con_bulk_density_soil", digits=(8,2)) 
    con_dry_density_soil = fields.Float(string= "Dry Density of Soil, γd", compute="_compute_con_dry_density_soil", digits=(8,2)) 
    con_swell_void_ratio = fields.Float(string= "Void ratio, e", compute="_compute_con_swell_void_ratio", digits=(8,2)) 
    con_degree_sat = fields.Float(string= "Degree of Saturation, Sr", compute="_compute_con_degree_sat", digits=(8,2)) 


    @api.depends('con_wt_of_ring','con_wt_wet_specimen_bf','con_wt_dry_specimen_af')
    def _compute_con_water_content(self):
        for line in self:
            num = line.con_wt_wet_specimen_bf - line.con_wt_dry_specimen_af
            deno = line.con_wt_dry_specimen_af - line.con_wt_of_ring

            if deno != 0:
                line.con_water_content = (num / deno) * 100
            else:
              line.con_water_content = 0

    @api.depends('con_wt_wet_specimen_bf','con_wt_of_ring','consolidation_volume')
    def _compute_con_bulk_density_soil(self):
        for line in self:
            if line.consolidation_volume != 0:
                line.con_bulk_density_soil = (line.con_wt_wet_specimen_bf - line.con_wt_of_ring) / line.consolidation_volume
            else:
              line.con_bulk_density_soil = 0    

    @api.depends('con_wt_wet_specimen_bf', 'con_wt_of_ring', 'consolidation_volume', 'con_wt_dry_specimen_af')
    def _compute_con_dry_density_soil(self):
     for line in self:
        line.con_dry_density_soil = 0  
        
        if not line.consolidation_volume or not line.con_wt_dry_specimen_af or line.con_wt_dry_specimen_af == line.con_wt_of_ring:
            continue

        # Compute bulk density
        bulk_den = (line.con_wt_wet_specimen_bf - line.con_wt_of_ring) / line.consolidation_volume

        # Compute water content
        water_con = (
            (line.con_wt_wet_specimen_bf - line.con_wt_dry_specimen_af)
            / (line.con_wt_dry_specimen_af - line.con_wt_of_ring)
        ) * 100

        # Calculate dry density
        line.con_dry_density_soil = bulk_den / (1 + (water_con / 100))

    @api.depends('consolidation_height','con_height_solid')
    def _compute_con_swell_void_ratio(self):
        for line in self:
            if line.con_height_solid != 0:
                line.con_swell_void_ratio = (line.consolidation_height - line.con_height_solid) / line.con_height_solid
            else:
              line.con_swell_void_ratio = 0 

    @api.depends('consolidation_height','con_height_solid','consolidation_specific_gravity','con_wt_wet_specimen_bf','con_wt_dry_specimen_af','con_wt_of_ring')
    def _compute_con_degree_sat(self):
        for line in self:
            if not line.con_height_solid:
              line.con_degree_sat = 0
              continue
            void_ratio = (line.consolidation_height - line.con_height_solid) / line.con_height_solid 
            
            deno = line.con_wt_dry_specimen_af - line.con_wt_of_ring
            if deno == 0 or void_ratio == 0:
              line.con_degree_sat = 0
              continue

            water_con = ((line.con_wt_wet_specimen_bf - line.con_wt_dry_specimen_af) / deno) * 100

            line.con_degree_sat = (line.consolidation_specific_gravity * water_con) / void_ratio 

    evaluate_swell_pressure = fields.Char(
    string="Evaluate swell pressure ??",
    compute="_compute_evaluate_swell_pressure",
    store=True)

    @api.depends('con_initial_read', 'consolidation_ids.load_0_05_0_1')
    def _compute_evaluate_swell_pressure(self):
     for rec in self:
        c17 = rec.con_initial_read or 0.0   # corresponds to Excel C17
        d22 = rec.consolidation_ids.mapped('load_0_05_0_1') or []
        d = d22[0] if len(d22) >= 3 else 0.0


        rec.evaluate_swell_pressure = "YES" if (c17 - d) > 0 else "NO"

    con_initial_read = fields.Float(string= "Initial Reading",  digits=(8,3)) 
    con_set_load_read = fields.Float(string= "Setting load Reading",  digits=(8,2))

    

    consolidation_ids = fields.One2many("consolidation.loading.line", "parent_id", string="1st Cycle Loading",default=lambda self: self.default_con_gauge_reading())





    # --- 1. प्रत्येक ग्राफसाठी वेगळे Image Field ---
    consolidation_graph_05_1 = fields.Binary(string="Graph 0.05-0.1")
    consolidation_graph_1_2 = fields.Binary(string="Graph 0.1-0.2")
    consolidation_graph_2_5 = fields.Binary(string="Graph 0.2-0.5")
    consolidation_graph_5_10 = fields.Binary(string="Graph 0.5-1.0")
    consolidation_graph_10_20 = fields.Binary(string="Graph 1.0-2.0")
    consolidation_graph_20_40 = fields.Binary(string="Graph 2.0-4.0")
    consolidation_graph_40_80 = fields.Binary(string="Graph 4.0-8.0")



    def action_generate_graph(self):
        for record in self:
            sorted_lines = sorted(record.consolidation_ids, key=lambda x: x.sqrt_time if x.sqrt_time else 0)

            graph_configs = [
                ('load_0_05_0_1', '1st Cycle Loading - (0.05 - 0.1)', 'consolidation_graph_05_1', (10, 6)),
                ('load_0_1_0_2',  '1st Cycle Loading - (0.1 - 0.2)',  'consolidation_graph_1_2', (10, 6)),
                ('load_0_2_0_5',  '1st Cycle Loading - (0.2 - 0.5)',  'consolidation_graph_2_5', (10, 6)),
                ('load_0_5_1_0',  '1st Cycle Loading - (0.5 - 1.0)',  'consolidation_graph_5_10', (10, 6)),
                
                ('load_1_0_2_0',  '1st Cycle Loading - (1.0 - 2.0)',  'consolidation_graph_10_20', (20, 8)),
                ('load_2_0_4_0',  '1st Cycle Loading - (2.0 - 4.0)',  'consolidation_graph_20_40', (20, 8)),
                ('load_4_0_8_0',  '1st Cycle Loading - (4.0 - 8.0)',  'consolidation_graph_40_80', (20, 8)),
            ]

            for line_field, title, image_field, fig_size in graph_configs:
                image_data = self._plot_graph(sorted_lines, line_field, title, fig_size)
                record[image_field] = image_data

    def _plot_graph(self, lines, y_field_name, title, fig_size):
        """
        Input: Lines, Field Name, Title, and Figure Size
        """
        x_values = []
        y_values = []

        for line in lines:
            y_val = getattr(line, y_field_name, None)
            
            if line.sqrt_time is not None and y_val is not None:
                x_values.append(line.sqrt_time)
                y_values.append(y_val)

        if not x_values or not y_values:
            return False

        # --- Plotting Logic ---
        
        can_smooth = HAS_SCIPY and len(x_values) >= 3

        fig, ax = plt.subplots(figsize=fig_size)

        if can_smooth:
            try:
                x_np = np.array(x_values)
                y_np = np.array(y_values)
                x_new = np.linspace(x_np.min(), x_np.max(), 300)
                spl = make_interp_spline(x_np, y_np, k=3)
                y_smooth = spl(x_new)
                
                ax.plot(x_new, y_smooth, color='black', linestyle='-', linewidth=1.5)
                ax.plot(x_values, y_values, marker='o', markersize=6, color='black', linestyle='None')
            except Exception:
                ax.plot(x_values, y_values, marker='o', markersize=6, linestyle='-', color='black', linewidth=1.5)
        else:
            ax.plot(x_values, y_values, marker='o', markersize=6, linestyle='-', color='black', linewidth=1.5)

        # Formatting
        ax.set_xlim(0, 20)
        ax.set_xticks(range(0, 21, 2))
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
        
        ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
        ax.minorticks_on()
        ax.grid(which='minor', linestyle=':', linewidth='0.5', color='lightgray')

        ax.set_title(title, fontsize=16)
        ax.set_xlabel('SQRT (Time in minutes)', fontsize=12)
        ax.set_ylabel('Dial Gauge Reading (mm)', fontsize=12)

        # Save Image
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        
        return base64.b64encode(buf.getvalue())

    
    @api.model
    def default_con_gauge_reading(self):
        default_lines = [
            (0, 0, {'time_m': '0',}),
            (0, 0, {'time_m': '1',}),
            (0, 0, {'time_m': '4',}),
            (0, 0, {'time_m': '6',}),
            (0, 0, {'time_m': '16',}),
            (0, 0, {'time_m': '25',}),
            (0, 0, {'time_m': '36',}),
            (0, 0, {'time_m': '49',}),
            (0, 0, {'time_m': '64',}),
            (0, 0, {'time_m': '81',}),
            (0, 0, {'time_m': '100',}),
            (0, 0, {'time_m': '121',}),
            (0, 0, {'time_m': '141',}),
            (0, 0, {'time_m': '169',}),
            (0, 0, {'time_m': '196',}),
            (0, 0, {'time_m': '225',}),
            (0, 0, {'time_m': '256',}),
            (0, 0, {'time_m': '289',}),
            (0, 0, {'time_m': '361',}),
            
        ]
        return default_lines
    
    consolidation_unloading_ids = fields.One2many("consolidation.unloading.line", "parent_id", string="1st Cycle Loading",default=lambda self: self.default_con_gauge_reading_2())

    @api.model
    def default_con_gauge_reading_2(self):
        default_lines = [
            (0, 0, {'time_m': '0',}),
            (0, 0, {'time_m': '5',}),
            (0, 0, {'time_m': '10',}),
            (0, 0, {'time_m': '15',}),
            (0, 0, {'time_m': '20',}),
            (0, 0, {'time_m': '25',}),
            (0, 0, {'time_m': '30',}),
            (0, 0, {'time_m': '35',}),
            (0, 0, {'time_m': '40',}),
            (0, 0, {'time_m': '45',}),
            (0, 0, {'time_m': '50',}),
            (0, 0, {'time_m': '55',}),
            (0, 0, {'time_m': '60',}),
            
        ]
        return default_lines
    


    consolidation_output_ids = fields.One2many("consolidation.both.cycle.line", "parent_id", string="1st Cycle Loading	",default=lambda self: self.default_con_cycle_reading())

    @api.model
    def default_con_cycle_reading(self):
        default_lines = [
            (0, 0, {'cylces':'1st Cycle Loading' ,'applied_pressure': '0.05',}),
            (0, 0, {'cylces':'1st Cycle Loading' ,'applied_pressure': '0.10',}),
            (0, 0, {'cylces':'1st Cycle Loading', 'applied_pressure': '0.20',}),
            (0, 0, {'cylces':'1st Cycle Loading' ,'applied_pressure': '0.50',}),
            (0, 0, {'cylces':'1st Cycle Loading' ,'applied_pressure': '1.00',}),
            (0, 0, {'cylces':'1st Cycle Loading' ,'applied_pressure': '2.00',}),
            (0, 0, {'cylces':'1st Cycle Loading' ,'applied_pressure': '4.00',}),
            (0, 0, {'cylces':'1st Cycle Loading' ,'applied_pressure': '8.00',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '8.00',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '4.00',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '2.00',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '1.00',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '0.50',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '0.20',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '0.10',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '0.05',}),
            
        ]
        return default_lines
    

    ce = fields.Float(string="Ce", digits=(8, 3), compute="_compute_ce_cr", store=True)
    cr = fields.Float(string="Cr", digits=(8, 3), compute="_compute_ce_cr", store=True)


    @api.depends(
        'consolidation_output_ids.e_void',
        'consolidation_output_ids.applied_pressure',
        'consolidation_output_ids.cylces',
    )
    def _compute_ce_cr(self):
        for rec in self:
            rec.ce = 0.0
            rec.cr = 0.0

            lines = rec.consolidation_output_ids

            # --------- Ce from loading segment (choose same points as Excel) ---------
            # example: use loading rows at 0.50 and 4.00 kg/cm²
            l1 = lines.filtered(
                lambda l: l.cylces == '1st Cycle Loading' and l.applied_pressure == 0.50
            )[:1]
            l2 = lines.filtered(
                lambda l: l.cylces == '1st Cycle Loading' and l.applied_pressure == 4.00
            )[:1]

            if l1 and l2:
                e1, p1 = l1.e_void or 0.0, l1.applied_pressure or 0.0
                e2, p2 = l2.e_void or 0.0, l2.applied_pressure or 0.0
                if p1 and p2 and p2 != p1:
                    rec.ce = (e1 - e2) / log10(p2 / p1)

            # --------- Cr from unloading segment (same as Excel) ---------
            # example: use unloading rows at 0.50 and 0.10 kg/cm²
            u1 = lines.filtered(
                lambda l: l.cylces == '1st Cycle Unloading' and l.applied_pressure == 0.50
            )[:1]
            u2 = lines.filtered(
                lambda l: l.cylces == '1st Cycle Unloading' and l.applied_pressure == 0.10
            )[:1]

            if u1 and u2:
                e1, p1 = u1.e_void or 0.0, u1.applied_pressure or 0.0
                e2, p2 = u2.e_void or 0.0, u2.applied_pressure or 0.0
                if p1 and p2 and p2 != p1:
                    rec.cr = (e1 - e2) / log10(p2 / p1)




     # DETERMINATION OF SWELLING PRESSURE OF SOILS BY CONSOLIDOMETER METHOD				
    
    swelling_pressure_name = fields.Char("Name",default="DETERMINATION OF SWELLING PRESSURE OF SOILS BY CONSOLIDOMETER METHOD")
    swelling_pressure_visible = fields.Boolean("DETERMINATION OF SWELLING PRESSURE OF SOILS BY CONSOLIDOMETER METHOD",compute="_compute_visible")

    swelling_specific_gravity = fields.Float(string="Specific Gravity, G" , digits=(8,3))
    swelling_diameter = fields.Float(string="Diameter, D", digits=(8,1))
    swelling_height = fields.Float(string="Height, H", digits=(8,1))
    swelling_area = fields.Float(string="Area, A", compute="_compute_swelling_area", digits=(8,3))
    swelling_volume = fields.Float(string="Volume, Vol", compute="_compute_swelling_volume", digits=(8,3))

    @api.depends('swelling_diameter')
    def _compute_swelling_area(self):
        for line in self:
            if line.swelling_diameter:
                line.swelling_area = (pi / 4) * (line.swelling_diameter ** 2)
            else:
              line.swelling_area = 0
    
    @api.depends('swelling_height','swelling_area','swelling_diameter')
    def _compute_swelling_volume(self):
        for line in self:
            area = (pi / 4) * (line.swelling_diameter ** 2)
            if line.swelling_height and line.swelling_area:
                line.swelling_volume = line.swelling_height * area
            else:
              line.swelling_volume = 0

    wt_of_ring = fields.Float(string="Weight Of Ring, w1" , digits=(10,3)) 
    wt_wet_specimen_bf = fields.Float(string="Weight Of Wet Specimen + Ring, w2" , digits=(10,3))  # before test
    wt_wet_specimen_af = fields.Float(string="Weight Of Wet Specimen + Ring, w5" , digits=(10,2))  # after test
    wt_dry_specimen_af = fields.Float(string="Weight Of Dry Specimen + Ring, w3" , digits=(10,3))  # after test

    wt_dry_soil = fields.Float(string= "Weight Of Dry Specimen + Ring, w4", compute="_compute_wt_dry_soil", digits=(10,3))

    height_solid = fields.Float(string= "Dry weight of soil, w4", compute="_compute_height_solid", digits=(10,4))

    @api.depends('wt_dry_specimen_af','wt_of_ring')
    def _compute_wt_dry_soil(self):
        for line in self:
                line.wt_dry_soil = line.wt_dry_specimen_af - line.wt_of_ring


    @api.depends('wt_dry_specimen_af','wt_of_ring','swelling_area','swelling_specific_gravity')
    def _compute_height_solid(self):
        for line in self:
            dry_soil = line.wt_dry_specimen_af - line.wt_of_ring

            if line.swelling_specific_gravity and line.swelling_area:
                line.height_solid = dry_soil / (line.swelling_area * line.swelling_specific_gravity)
            else:
              line.height_solid = 0

    
    water_content = fields.Float(string= "Water Content, wc", compute="_compute_water_content", digits=(8,2)) 
    bulk_density_soil = fields.Float(string= "Bulk Density of Soil, γb", compute="_compute_bulk_density_soil", digits=(8,2)) 
    dry_density_soil = fields.Float(string= "Dry Density of Soil, γd", compute="_compute_dry_density_soil", digits=(8,2)) 
    swell_void_ratio = fields.Float(string= "Void ratio, e", compute="_compute_swell_void_ratio", digits=(8,2)) 
    degree_sat = fields.Float(string= "Degree of Saturation, Sr", compute="_compute_degree_sat", digits=(8,2)) 


    @api.depends('wt_of_ring','wt_wet_specimen_bf','wt_dry_specimen_af')
    def _compute_water_content(self):
        for line in self:
            num = line.wt_wet_specimen_bf - line.wt_dry_specimen_af
            deno = line.wt_dry_specimen_af - line.wt_of_ring

            if deno != 0:
                line.water_content = (num / deno) * 100
            else:
              line.water_content = 0

    @api.depends('wt_wet_specimen_bf','wt_of_ring','swelling_volume')
    def _compute_bulk_density_soil(self):
        for line in self:
            if line.swelling_volume != 0:
                line.bulk_density_soil = (line.wt_wet_specimen_bf - line.wt_of_ring) / line.swelling_volume
            else:
              line.bulk_density_soil = 0    

    @api.depends('wt_wet_specimen_bf', 'wt_of_ring', 'swelling_volume', 'wt_dry_specimen_af')
    def _compute_dry_density_soil(self):
     for line in self:
        line.dry_density_soil = 0  
        
        if not line.swelling_volume or not line.wt_dry_specimen_af or line.wt_dry_specimen_af == line.wt_of_ring:
            continue

        # Compute bulk density
        bulk_den = (line.wt_wet_specimen_bf - line.wt_of_ring) / line.swelling_volume

        # Compute water content
        water_con = (
            (line.wt_wet_specimen_bf - line.wt_dry_specimen_af)
            / (line.wt_dry_specimen_af - line.wt_of_ring)
        ) * 100

        # Calculate dry density
        line.dry_density_soil = bulk_den / (1 + (water_con / 100))

    @api.depends('swelling_height','height_solid')
    def _compute_swell_void_ratio(self):
        for line in self:
            if line.height_solid != 0:
                line.swell_void_ratio = (line.swelling_height - line.height_solid) / line.height_solid
            else:
              line.swell_void_ratio = 0 

    @api.depends('swelling_height','height_solid','swelling_specific_gravity','wt_wet_specimen_bf','wt_dry_specimen_af','wt_of_ring')
    def _compute_degree_sat(self):
        for line in self:
            if not line.height_solid:
              line.degree_sat = 0
              continue
            void_ratio = (line.swelling_height - line.height_solid) / line.height_solid 
            
            deno = line.wt_dry_specimen_af - line.wt_of_ring
            if deno == 0 or void_ratio == 0:
              line.degree_sat = 0
              continue

            water_con = ((line.wt_wet_specimen_bf - line.wt_dry_specimen_af) / deno) * 100

            line.degree_sat = (line.swelling_specific_gravity * water_con) / void_ratio


    water_content_1 = fields.Float(string= "Water Content, wc", compute="_compute_water_content_1", digits=(8,2)) 
    bulk_density_soil_1 = fields.Float(string= "Bulk Density of Soil, γb", compute="_compute_bulk_density_soil_1", digits=(8,2)) 
    dry_density_soil_1 = fields.Float(string= "Dry Density of Soil, γd", compute="_compute_dry_density_soil_1", digits=(8,2)) 
    swell_void_ratio_1 = fields.Float(string= "Void ratio, e", compute="_compute_swell_void_ratio_1", digits=(8,2)) 
    degree_sat_1 = fields.Float(string= "Degree of Saturation, Sr", compute="_compute_degree_sat_1", digits=(8,2)) 

    @api.depends('wt_of_ring','wt_wet_specimen_af','wt_dry_specimen_af')
    def _compute_water_content_1(self):
        for line in self:
            num = line.wt_wet_specimen_af - line.wt_dry_specimen_af
            deno = line.wt_dry_specimen_af - line.wt_of_ring

            if deno != 0:
                line.water_content_1 = (num / deno) * 100
            else:
              line.water_content_1 = 0

    @api.depends('wt_of_ring', 'wt_wet_specimen_af',
             'swelling_area', 'swelling_output_ids.specimen_height')
    def _compute_bulk_density_soil_1(self):
     for line in self:
        num = (line.wt_wet_specimen_af or 0.0) - (line.wt_of_ring or 0.0)

        # get list of heights from child lines
        heights = line.swelling_output_ids.mapped('specimen_height') or []
        # take third-last value if it exists
        h = heights[-3] if len(heights) >= 3 else 0.0

        deno = (line.swelling_area or 0.0) * h

        if deno:
            line.bulk_density_soil_1 = num / deno
        else:
            line.bulk_density_soil_1 = 0.0

    @api.depends('wt_wet_specimen_af', 'wt_of_ring', 'swelling_area','wt_dry_specimen_af', 'swelling_output_ids.specimen_height')
    def _compute_dry_density_soil_1(self):
     for line in self:
        line.dry_density_soil_1 = 0  
        
        if not line.swelling_area or not line.wt_dry_specimen_af or line.wt_dry_specimen_af == line.wt_of_ring:
            continue

        # Compute bulk density
        num = (line.wt_wet_specimen_af or 0.0) - (line.wt_of_ring or 0.0)

        # get list of heights from child lines
        heights = line.swelling_output_ids.mapped('specimen_height') or []
        # take third-last value if it exists
        h = heights[-3] if len(heights) >= 3 else 0.0

        deno = (line.swelling_area or 0.0) * h
        bulk_den =  num / deno

        # Compute water content
        water_con = (
            (line.wt_wet_specimen_af - line.wt_dry_specimen_af)
            / (line.wt_dry_specimen_af - line.wt_of_ring)
        ) * 100

        # Calculate dry density
        line.dry_density_soil_1 = bulk_den / (1 + (water_con / 100))


    @api.depends('swelling_output_ids.e_void')
    def _compute_swell_void_ratio_1(self):
        for line in self:
            # get list of heights from child lines
            void = line.swelling_output_ids.mapped('e_void') or []
            # take third-last value if it exists
            v = void[-1] if len(void) >= 3 else 0.0
            line.swell_void_ratio_1 = v

    @api.depends('swelling_output_ids.e_void',
             'swelling_specific_gravity',
             'wt_wet_specimen_af',
             'wt_dry_specimen_af',
             'wt_of_ring')
    def _compute_degree_sat_1(self):
     for line in self:
        # last void ratio from child lines (or 0 if no lines)
        voids = line.swelling_output_ids.mapped('e_void') or []
        v = voids[-1] if voids else 0.0

        # water content in %
        water_con = 0.0
        denom = (line.wt_dry_specimen_af or 0.0) - (line.wt_of_ring or 0.0)
        if denom:
            water_con = ((line.wt_wet_specimen_af or 0.0)
                         - (line.wt_dry_specimen_af or 0.0)) / denom * 100.0

        # S = (w * Gs) / e   (in % if w is in %)
        if v:
            line.degree_sat_1 = (line.swelling_specific_gravity or 0.0) * water_con / v
        else:
            line.degree_sat_1 = 0.0






    initial_read = fields.Float(string= "Initial Reading",  digits=(8,2)) 
    set_load_read = fields.Float(string= "Setting load Reading",  digits=(8,2))

    swelling_ids = fields.One2many("swelling.pressure.loading.line", "parent_id", string="1st Cycle Loading	",default=lambda self: self.default_gauge_reading())

    @api.model
    def default_gauge_reading(self):
        default_lines = [
            (0, 0, {'time_m': '0',}),
            (0, 0, {'time_m': '1',}),
            (0, 0, {'time_m': '4',}),
            (0, 0, {'time_m': '6',}),
            (0, 0, {'time_m': '16',}),
            (0, 0, {'time_m': '25',}),
            (0, 0, {'time_m': '36',}),
            (0, 0, {'time_m': '49',}),
            (0, 0, {'time_m': '64',}),
            (0, 0, {'time_m': '81',}),
            (0, 0, {'time_m': '100',}),
            (0, 0, {'time_m': '121',}),
            (0, 0, {'time_m': '141',}),
            (0, 0, {'time_m': '169',}),
            (0, 0, {'time_m': '196',}),
            (0, 0, {'time_m': '225',}),
            (0, 0, {'time_m': '256',}),
            (0, 0, {'time_m': '289',}),
            (0, 0, {'time_m': '361',}),
            
        ]
        return default_lines
    
    swelling_unloading_ids = fields.One2many("swelling.pressure.unloading.line", "parent_id", string="1st Cycle Loading	",default=lambda self: self.default_gauge_reading_2())

    @api.model
    def default_gauge_reading_2(self):
        default_lines = [
            (0, 0, {'time_m': '0',}),
            (0, 0, {'time_m': '5',}),
            (0, 0, {'time_m': '10',}),
            (0, 0, {'time_m': '15',}),
            (0, 0, {'time_m': '20',}),
            (0, 0, {'time_m': '25',}),
            (0, 0, {'time_m': '30',}),
            (0, 0, {'time_m': '35',}),
            (0, 0, {'time_m': '40',}),
            (0, 0, {'time_m': '45',}),
            (0, 0, {'time_m': '50',}),
            (0, 0, {'time_m': '55',}),
            (0, 0, {'time_m': '60',}),
            
        ]
        return default_lines
    

    swelling_output_ids = fields.One2many("swelling.pressure.both.cycle.line", "parent_id", string="1st Cycle Loading	",default=lambda self: self.default_cycle_reading())

    @api.model
    def default_cycle_reading(self):
        default_lines = [
            (0, 0, {'cylces':'1st Cycle Loading' ,'applied_pressure': '0.05',}),
            (0, 0, {'cylces':'1st Cycle Loading' ,'applied_pressure': '0.10',}),
            (0, 0, {'cylces':'1st Cycle Loading', 'applied_pressure': '0.20',}),
            (0, 0, {'cylces':'1st Cycle Loading' ,'applied_pressure': '0.40',}),
            (0, 0, {'cylces':'1st Cycle Loading' ,'applied_pressure': '0.80',}),
            (0, 0, {'cylces':'1st Cycle Loading' ,'applied_pressure': '1.60',}),
            (0, 0, {'cylces':'1st Cycle Loading' ,'applied_pressure': '3.20',}),
            (0, 0, {'cylces':'1st Cycle Loading' ,'applied_pressure': '6.40',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '6.40',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '3.20',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '1.60',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '0.80',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '0.40',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '0.20',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '0.10',}),
            (0, 0, {'cylces':'1st Cycle Unloading' ,'applied_pressure': '0.05',}),
            
        ]
        return default_lines
    

    swelling_table_ids = fields.One2many("swelling.pressure.graph.line", "parent_id", string="Graph Table",default=lambda self: self.default_table_reading())

    @api.model
    def default_table_reading(self):
        default_lines = [
            (0, 0, {'applied_pressure': '0.10',}),
            (0, 0, {'applied_pressure': '0.20',}),
            (0, 0, {'applied_pressure': '0.50',}),
            (0, 0, {'applied_pressure': '1.00',}),
            (0, 0, {'applied_pressure': '2.00',}),
            (0, 0, {'applied_pressure': '4.00',}),
            
        ]
        return default_lines
    

    swelling_pressure = fields.Float(
    string="Swelling Pressure (kg/cm²)",
    digits=(8, 3),
    compute="_compute_swelling_pressure",
    store=True)

    @api.depends('swelling_table_ids.applied_pressure',
             'swelling_table_ids.delta_h')
    def _compute_swelling_pressure(self):
     for rec in self:
        lines = rec.swelling_table_ids.sorted('applied_pressure')
        sp = 0.0
        # find first pair where ΔH changes sign (D49 > 0, D50 < 0)
        for i in range(len(lines) - 1):
            d1 = lines[i].delta_h
            d2 = lines[i + 1].delta_h
            if d1 >= 0 and d2 <= 0:
                p1 = lines[i].applied_pressure
                p2 = lines[i + 1].applied_pressure
                # linear interpolation at ΔH = 0
                if (d2 - d1) != 0:
                    sp = p1 + (p2 - p1) * (0.0 - d1) / (d2 - d1)
                break
        rec.swelling_pressure = round(sp, 2)



    graph_image_swell = fields.Binary("Swelling Pressure Graph", compute="_compute_graph_image_swell", store=True)

    @api.depends('swelling_table_ids.applied_pressure', 'swelling_table_ids.delta_h')
    def _compute_graph_image_swell(self):
        for record in self:
            if record.swelling_table_ids:
                record.graph_image_swell = record.generate_line_chart_swell()
            else:
                record.graph_image_swell = False



    def generate_line_chart_swell(self):
     self.ensure_one()

     lines = self.swelling_table_ids.sorted('applied_pressure')
     x_vals = np.array(
        [l.applied_pressure for l in lines if l.applied_pressure is not None],
        dtype=float
     )
     y_vals = np.array(
        [l.delta_h for l in lines if l.delta_h is not None],
        dtype=float
     )
     if x_vals.size < 3:
        return False    # need at least 3 points for a curve

     # swelling pressure (same as before) ...
     sp = 0.0
     for i in range(len(x_vals) - 1):
        d1 = y_vals[i]
        d2 = y_vals[i + 1]
        if d1 >= 0 and d2 <= 0 and (d2 - d1) != 0:
            p1 = x_vals[i]
            p2 = x_vals[i + 1]
            sp = p1 + (p2 - p1) * (0.0 - d1) / (d2 - d1)
            break

     # ---- cubic spline for smooth curve ----
     from scipy.interpolate import CubicSpline   # needs SciPy installed [web:72][web:74]
     cs = CubicSpline(x_vals, y_vals, bc_type='natural')
     x_smooth = np.linspace(x_vals.min(), x_vals.max(), 400)
     y_smooth = cs(x_smooth)

     import matplotlib
     matplotlib.use('Agg')
    

     fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

     # smooth cubic‑spline curve
     ax.plot(x_smooth, y_smooth, color='steelblue', linewidth=2)

     # original points
     ax.scatter(x_vals, y_vals, color='steelblue')
     for x, y in zip(x_vals, y_vals):
        ax.annotate(f"{y:.3f}", (x, y),
                    textcoords="offset points", xytext=(0, 5),
                    ha='center', fontsize=8)

     ax.axhline(0, color='tab:blue', linewidth=1)
     if sp:
        ax.axvline(sp, color='red', linewidth=1)

     ax.set_xlabel('Pressure kg/cm²')
     ax.set_ylabel('Deformation, mm')
     ax.set_ylim(-0.75, 2.50)
     ax.set_yticks([-0.75, 0.0, 0.75, 1.50, 2.25])
     ax.grid(True)

     buf = BytesIO()
     fig.tight_layout()
     fig.savefig(buf, format='png')
     plt.close(fig)
     buf.seek(0)
     return base64.b64encode(buf.read())





    #  DETERMINE PERMEABILITY OF SOIL - BY FALLING HEAD			

    permeability_falling_name = fields.Char("Name",default="Permeability Falling Head Test")
    permeability_falling_visible = fields.Boolean("Permeability Falling Head Test",compute="_compute_visible")

    dia_standpipe = fields.Float(string="Dia of Stand Pipe, d (cm)", digits=(8,1))
    dia_soil_sample = fields.Float(string="Dia of Soil Sample, D (cm)", digits=(8,1))
    length_soil = fields.Float(string="Length of Soil Sample, L (cm)", digits=(8,1))
    bt_wt_soil_mould = fields.Float(string="Weight of wet soil + mould specimen before test, Wt, gm:", digits=(8,0))
    at_wt_soil = fields.Float(string="Weight of wet soil specimen after test, Wt, gm:", digits=(8,0))

    wt_empty_mould = fields.Float(string="Empty weight of mould (gm)", digits=(8,0))
    wt_dry_soil = fields.Float(string="Dry weight of soil", digits=(8,0))

    distance = fields.Float(string="Distance between 0 of scale to the middle of the bottom opening, cm	", digits=(8,0))




    
    area_pipe = fields.Float(string="Area of Pipe (sq.cm)", compute="_compute_area_pipe", digits=(8,2), store=True)
    area_soil_samp = fields.Float(string="Area of Soil Sample (sq.cm)", compute="_compute_area_soil_samp", digits=(8,2), store=True)
    vol_per_mould = fields.Float(string="Volume of permeabiliy mould (cc)", compute="_compute_vol_per_mould", digits=(8,2), store=True)
    bulk_wt_soil = fields.Float(string="Bulk wt of soil (gm)", compute="_compute_bulk_wt_soil", digits=(8,2), store=True)
    bulk_density = fields.Float(string="Bulk density (gm/cc)", compute="_compute_bulk_density", digits=(8,2) ,store = True)

    moisture_con_bt = fields.Float(string="Moisture Content (before Test), %", compute="_compute_moisture_con_bt", digits=(8,2), store=True)
    moisture_con_at = fields.Float(string="Moisture Content (After Test), %", compute="_compute_moisture_con_at", digits=(8,2), store=True)

    dry_density = fields.Float(string="Dry density (gm/cc)", compute="_compute_dry_density", digits=(8,2), store=True)



    @api.depends('dia_standpipe')
    def _compute_area_pipe(self):
        for line in self:
            if line.dia_standpipe:
                line.area_pipe = 0.7853981634 * line.dia_standpipe * line.dia_standpipe
            else:
              line.area_pipe = 0.0

    @api.depends('dia_soil_sample')
    def _compute_area_soil_samp(self):
        for line in self:
            if line.dia_soil_sample:
                line.area_soil_samp = 0.7853981634 * line.dia_soil_sample * line.dia_soil_sample
            else:
              line.area_soil_samp = 0.0

    @api.depends('dia_soil_sample', 'length_soil')
    def _compute_vol_per_mould(self):
        for line in self:
            if line.dia_soil_sample and line.length_soil:
                soil_samp = 0.7853981634 * line.dia_soil_sample * line.dia_soil_sample
                line.vol_per_mould = line.length_soil * soil_samp
            else:
                line.vol_per_mould = 0.0
    
    @api.depends('bt_wt_soil_mould', 'wt_empty_mould')
    def _compute_bulk_wt_soil(self):
        for line in self:
            if line.bt_wt_soil_mould and line.wt_empty_mould:
                line.bulk_wt_soil = line.bt_wt_soil_mould - line.wt_empty_mould
            else:
                line.bulk_wt_soil = 0.0

    @api.depends('dia_soil_sample', 'length_soil', 'bt_wt_soil_mould', 'wt_empty_mould')
    def _compute_bulk_density(self):
      for line in self:
        if (
            line.dia_soil_sample
            and line.length_soil
            and line.bt_wt_soil_mould
            and line.wt_empty_mould
        ):
            soil_samp = 0.7853981634 * line.dia_soil_sample * line.dia_soil_sample
            vol_per_mould = line.length_soil * soil_samp
            if vol_per_mould:
                bulk_wt_soil = line.bt_wt_soil_mould - line.wt_empty_mould
                line.bulk_density = bulk_wt_soil / vol_per_mould
            else:
                line.bulk_density = 0.0
        else:
            line.bulk_density = 0.0


    @api.depends('bt_wt_soil_mould', 'wt_empty_mould', 'wt_dry_soil')
    def _compute_moisture_con_bt(self):
     for line in self:
        if line.bt_wt_soil_mould and line.wt_empty_mould and line.wt_dry_soil:
            bulk_wt_soil = line.bt_wt_soil_mould - line.wt_empty_mould
            water_mass = bulk_wt_soil - line.wt_dry_soil
            
            line.moisture_con_bt = (water_mass / line.wt_dry_soil) * 100
        else:
            line.moisture_con_bt = 0.0

    @api.depends('bt_wt_soil_mould', 'wt_empty_mould', 'wt_dry_soil', 'at_wt_soil')
    def _compute_moisture_con_at(self):
     for line in self:
        if line.at_wt_soil and line.wt_dry_soil:
            water_mass = line.at_wt_soil - line.wt_dry_soil
            line.moisture_con_at = (water_mass / line.wt_dry_soil) * 100
        else:
            line.moisture_con_at = 0.0


    

    @api.depends('dia_soil_sample', 'length_soil',
             'bt_wt_soil_mould', 'wt_empty_mould', 'wt_dry_soil')
    def _compute_dry_density(self):
     for line in self:
        if (line.dia_soil_sample and line.length_soil and
                line.bt_wt_soil_mould and line.wt_empty_mould and
                line.wt_dry_soil):

            # Volume of specimen (cc)
            soil_area = 0.7853981634 * line.dia_soil_sample * line.dia_soil_sample
            vol_per_mould = line.length_soil * soil_area

            # Bulk (wet) unit weight γ = W_wet / V
            bulk_wt_soil = line.bt_wt_soil_mould - line.wt_empty_mould
            if not vol_per_mould:
                line.dry_density = 0.0
                continue
            bulk_density = bulk_wt_soil / vol_per_mould

            # Moisture content w = (W_wet − W_dry)/W_dry
            water_mass = bulk_wt_soil - line.wt_dry_soil
            moisture_con = water_mass / line.wt_dry_soil if line.wt_dry_soil else 0.0  # in fraction

            # Dry density γ_d = γ / (1 + w)
            line.dry_density = bulk_density / (1.0 + moisture_con) if (1.0 + moisture_con) else 0.0
        else:
            line.dry_density = 0.0


    W1_soil = fields.Float(string="W1", digits=(8,3))
    W2_soil = fields.Float(string="W2", digits=(8,3))
    W3_soil = fields.Float(string="W3 = (W2-W1)", compute="_compute_W3_soil", digits=(8,3), store=True)
    volume_soil = fields.Float(string="Volume (V)", digits=(8,0))
    density_soils = fields.Float(string="Density (γ) g/cc", compute="_compute_density_soils", digits=(16,6), store=True)
    

    @api.depends('W2_soil','W1_soil')
    def _compute_W3_soil(self):
        for line in self:
                line.W3_soil =  line.W2_soil - line.W1_soil

    @api.depends('volume_soil', 'W2_soil', 'W1_soil')
    def _compute_density_soils(self):
      for line in self:
        # All inputs must exist and volume must be non‑zero
        if line.volume_soil not in (None, 0) and line.W2_soil is not None and line.W1_soil is not None:
            w3_soil = line.W2_soil - line.W1_soil
            line.density_soils = round(w3_soil / line.volume_soil, 6)
        else:
            line.density_soils = 0.0


    W1_soil_28 = fields.Float(string="W1", digits=(8,3))
    W2_soil_28 = fields.Float(string="W2", digits=(8,3))
    W3_soil_28 = fields.Float(string="W3 = (W2-W1)", compute="_compute_W3_soil_28", digits=(8,3), store=True)
    volume_soil_28 = fields.Float(string="Volume (V)", digits=(8,0))
    density_soils_28 = fields.Float(string="Density (γ) g/cc", compute="_compute_density_soils_28", digits=(16,6), store=True)
    specific_gravity_per = fields.Float(string="Specific Gravity", compute="_compute_specific_gravity_per_28", digits=(16,6), store=True)

    @api.depends('W2_soil_28','W1_soil_28')
    def _compute_W3_soil_28(self):
        for line in self:
                line.W3_soil_28 =  line.W2_soil_28 - line.W1_soil_28

    @api.depends('volume_soil_28', 'W2_soil_28', 'W1_soil_28')
    def _compute_density_soils_28(self):
      for line in self:
        # All inputs must exist and volume must be non‑zero
        if line.volume_soil_28 not in (None, 0) and line.W2_soil_28 is not None and line.W1_soil_28 is not None:
            w3_soil_28 = line.W2_soil_28 - line.W1_soil_28
            line.density_soils_28 = round(w3_soil_28 / line.volume_soil_28, 6)
        else:
            line.density_soils_28 = 0.0

    @api.depends('density_soils','density_soils_28')
    def _compute_specific_gravity_per_28(self):
        for line in self:
            if line.density_soils and line.density_soils_28 :    
                line.specific_gravity_per =  round(line.density_soils/line.density_soils_28,6)

    permeability_ids = fields.One2many("soil.permeability.test.line", "parent_id", string="DETERMINE PERMEABILITY OF SOIL - BY FALLING HEAD")

    avg_permeability = fields.Float("Average Permeability Avg KT :", digits=(16, 9), store=True)

    avg_permeability_27 = fields.Float("Average Permeability K27 :",compute="_compute_avg_permeability", digits=(16, 9), store=True)

    @api.depends('permeability_ids.permeability','specific_gravity_per')
    def _compute_avg_permeability(self):
        for line in self:
            if line.permeability_ids:
                vals = line.permeability_ids.mapped("permeability")
                line.avg_permeability = sum(vals) / len(vals)
                line.avg_permeability_27 = line.avg_permeability * line.specific_gravity_per

            else:
                line.avg_permeability = 0.0
                line.avg_permeability_27 = 0.0



















      
    


    

   

     ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
      
        for record in self:
            record.sieve_visible = False
            # water_content_visible = False
            record.liquid_limit_visible = False
            record.plastic_limit_visible = False
            record.heavy_visible = False
            record.omc_visible = False
            record.triaxial_visible = False
            record.internal_fraction_visible = False
            record.soil_visible = False
            record.fsi_visible  = False 
            record.determination_visible  = False 
            record.shrinkage_limit_visible  = False 
            record.permeability_falling_visible  = False 
            record.specific_gravity_visible  = False 
            record.direct_shear_visible  = False 
            record.ucs_visible  = False 
            record.consolidation_visible  = False 
            record.consolidation_pc_visible  = False 
            record.angle_shear_visible  = False 
            record.swelling_pressure_visible  = False 
            record.uu_triaxial_angle_visible  = False
            record.uu_triaxial_cohesion_visible  = False



            record.moisture_visible  = False
            record.gsa_visible = False

            record.specific_gravity_visible = False
            record.freeswell_visible = False






            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == '12014fgr-5c56-475b-9a89-93a59c9ee3a2':
                    record.sieve_visible = True

               
                if sample.internal_id == '23fg21gh-7202-4d62-864b-8efa58b6b61f':
                    record.liquid_limit_visible = True

                if sample.internal_id == '120vbf14-2ff0-4b81-aca1-0e07dab7cd87':
                    record.plastic_limit_visible = True

                if sample.internal_id == '3210vbf-20fb-4843-aa0e-2ee981be0d7c':
                    record.heavy_visible = True

                if sample.internal_id == '3210vbf-20fb-4843-aa0e-142578bgtyu':
                    record.omc_visible = True

                if sample.internal_id == '3210vbf-20fb-4843-aa0e-145ght27854l':
                    record.triaxial_visible = True

                if sample.internal_id == '14578nhy87-20fb-4843-aa0e-145ght27854l':
                    record.internal_fraction_visible = True
                
                if sample.internal_id == '15247gtr-2065-4532-814a-3a4c1e884305':
                    record.soil_visible = True

                if sample.internal_id == 'ght4125-ca64-44dd-b0ae-228aacf04998':
                    record.fsi_visible = True

                if sample.internal_id == '5487gt21-ca64-44dd-b0ae-228aacf04965':
                    record.determination_visible = True

                if sample.internal_id == '5487gt21-ca64-44dd-b0ae-278954ggh114':
                    record.shrinkage_limit_visible = True
                
                if sample.internal_id == '897546gt21-ca64-44dd-b0ae-22145687':
                    record.permeability_falling_visible = True

                if sample.internal_id == '214hhj6gt21-ca64-44dd-b0ae-6587gghty':
                    record.specific_gravity_visible = True

                if sample.internal_id == '21457888hhhllly1-ca64-44dd-b0ae-3214hhhtr':
                    record.direct_shear_visible = True

                if sample.internal_id == 't4y57888hhhllly1-ca64-44dd-b0ae-1234567rt':
                    record.ucs_visible = True
                
                if sample.internal_id == '78957888hhhllly1-ca64-44dd-b0ae-2314780ty':
                    record.consolidation_visible = True

                if sample.internal_id == '98ggh7888hhhllly1-ca64-44dd-b0ae-6547ggt0r':
                    record.consolidation_pc_visible = True

                if sample.internal_id == '00fh7888hhhllly1-ca64-44dd-b0ae-897456ghtr':
                    record.angle_shear_visible = True

                if sample.internal_id == '9521yt88hhhllly1-ca64-44dd-b0ae-8974578ghtr2':
                    record.swelling_pressure_visible = True

                if sample.internal_id == '65478h88hhhllly1-ca64-44dd-b0ae-89745785gt41d':
                    record.uu_triaxial_angle_visible = True
                
                if sample.internal_id == '2r478h88hhhllly1-ca64-44dd-b0ae-897897gghtre0':
                    record.uu_triaxial_cohesion_visible = True







                if sample.internal_id == '7abb5a01-2fa7-4c4a-ab6e-0f4112e3aea9':
                    record.moisture_visible = True
                if sample.internal_id == 'tyer4fgr-5c56-475b-9arty156878965uut':
                    record.gsa_visible = True

                if sample.internal_id == '26a889da-3ab8-40e9-af69-2399b62dce9f':
                    record.specific_gravity_visible = True

                if sample.internal_id == '3825ec57-11f8-4249-9fa8-d99f64ffd396':
                    record.freeswell_visible = True


   






    def open_eln_page(self):
    # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == '23fg21gh-7202-4d62-864b-8efa58b6b61f':
                result.result_char = round(self.liquid_limit,2)
                if self.liquid_limit_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '120vbf14-2ff0-4b81-aca1-0e07dab7cd87':
                result.result_char = round(self.plastic_limit,2)
                if self.plastic_limit_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '1045789654-2ff0-4b81-aca1-0e07dab7cd87':
                result.result_char = round(self.plasticity_index,2)
                if self.plasticity_index_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '3210vbf-20fb-4843-aa0e-2ee981be0d7c':
                result.result_char = round(self.max_dry_density,2)
                if self.heavy_table_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '3210vbf-20fb-4843-aa0e-142578bgtyu':
                result.result_char = round(self.omc1,2)
                if self.omc_table_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == 'ght4125-ca64-44dd-b0ae-228aacf04998':
                result.result_char = round(self.fsi,2)
                if self.fsi_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '5487gt21-ca64-44dd-b0ae-228aacf04965':
                result.result_char = round(self.permeability,2)
                if self.permeability_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '3210vbf-20fb-4843-aa0e-145ght27854l':
                result.result_char = round(self.area_triaxial,2)
                if self.area_triaxial_nabl == 'pass':
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







    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        # records = self.env['lerm.eln'].sudo().search([('id','=', record.eln_id.id)]).parameters_result
        # print("records",records)
        # self.sample_parameters = records
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)



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
    _name = "mechanical.soil.sieve.analysis.line1"
    parent_id = fields.Many2one('mechanical.soil1', string="Parent Id")

    

    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size")
    particle_size = fields.Char(string="Particle Size  (mm)")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained")
    cumulative_retained = fields.Float(string="Cum. Retained %",compute="_compute_cum_retained" , store=True)
    passing_percent = fields.Float(string="Cumulative % ")

    

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




class LIQUIDLIMITLINE(models.Model):
    _name = "mechanical.liquid.limits.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

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




    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class PLASTICLIMITLINE(models.Model):
    _name = "mechanical.plasticl.limit.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")


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
    _name = "mechanical.heavy.compaction.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

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


class LVDTLINE(models.Model):
    _name = "mechanical.lvdt.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    lvdt_triaxial = fields.Float(string="LVDT Reading in mm")
    load_triaxial31 = fields.Integer(string="Load in σ 31=50kN/m2")
    load_triaxial32 = fields.Integer(string="Load in σ 32=100kN/m2")
    al_l = fields.Float(string="AL/L")
    ac = fields.Integer(string="Ac = Ao/1 - c in mm2")
    deviatore_triaxial31 = fields.Float(string="Deviator Stress σ 31=50kN/m2")
    deviatore_triaxial32 = fields.Float(string=" Deviator Stress σ 32=100kN/m2")
    



  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(LVDTLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class INTERNALFRACTIONLINE(models.Model):
    _name = "mechanical.cohesion.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    normal_lbs = fields.Float(string=" Normal Load LBS")
    normal_kgs = fields.Integer(string=" Normal Load Kgs")
    load_5 = fields.Integer(string="(Load X 5)+Self Weight")
    shear_division = fields.Float(string="Shear Force at Failure Divisions")
    shear_lc = fields.Integer(string="Shear Force at Failure L.C X DIV")
    noraml_stress = fields.Float(string="Normal Stress ( kg / cm2 )")
    shear_stress = fields.Float(string=" Shear Stress ( kg / cm2 )")
    



  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(INTERNALFRACTIONLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class SoilCBRLine(models.Model):
    _name = "mechanical.cbr.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    penetration = fields.Float(string="Penetration in mm")
    proving_reading = fields.Float(string="Dial Guage Reading")
    no_division = fields.Float(string="Number of Division",compute="_compute_no_division", store=True,digits=(12,2))

    applied_force = fields.Float(string="Applied force (kN)", digits=(12,4),compute="_compute_applied_force")
    avg_load = fields.Float(string="Average Load in kN",digits=(12,2),compute="_compute_avg_load",store=True)

 

    @api.depends('proving_reading')
    def _compute_no_division(self):
        for rec in self:
            rec.no_division = rec.proving_reading * 5

    @api.depends('no_division')
    def _compute_applied_force(self):
        for rec in self:
            rec.applied_force = (0.0133 * rec.no_division) + 0.0404 if rec.no_division else 0.0404

    @api.depends('applied_force', 'parent_id.rise_force')
    def _compute_avg_load(self):
        for rec in self:
            rise_force = rec.parent_id.rise_force or 0.0
            rec.avg_load = rec.applied_force + (rec.applied_force * rise_force)

   

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
    _name = "mechanical.omc.compaction.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

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
    _name = "mechanical.shrinkage.limit.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    container_no = fields.Char(string="Container No.")
    shrinkage_mass = fields.Float(string="Mass of container (m1) ",digits=(12,3))
    shrinkage_wet = fields.Float(string="Wt. of Container + Wet Soil(m2)",digits=(12,3))
    wt_dry = fields.Float(string="Wt. of Container + dry Soil (m3)",digits=(12,3))
    mass_dry = fields.Float(string="mass of dry soil (Ms=m3-m1)",digits=(12,3),compute="_compute_mass_dry")
    mass_water = fields.Float(string="mass of water (Mw=m2-m3)",digits=(12,3),compute="_compute_mass_water")
    moisture_content_shri = fields.Float(string="Moisture Content %(Mw/Ms*100)",digits=(12,3),compute="_compute_moisture_content_shri")
    volume_wet_shri = fields.Float(string="Volume of wet soil (V1)",digits=(12,3),compute="_compute_volume_wet_shri")
    volume_dry_shir = fields.Float(string="Volume of dry Soil pat (V2)",digits=(12,3),compute="_compute_volume_dry_shir")
    shrinkage_limit = fields.Float(string="Shrinkage limit (%)",digits=(12,3),compute="_compute_shrinkage_limit")

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

    @api.depends("parent_id")
    def _compute_volume_wet_shri(self):
        for rec in self:
            volume = 0.0
            if rec.parent_id:
                # घेतो पहिला record volume wet lines मधून
                wet_line = rec.parent_id.volume_wet_table[:1]  
                if wet_line:
                    volume = wet_line.volume_wet
            rec.volume_wet_shri = volume

    @api.depends("parent_id")
    def _compute_volume_dry_shir(self):
        for rec in self:
            volume1 = 0.0
            if rec.parent_id:
                # घेतो पहिला record volume wet lines मधून
                wet_line1 = rec.parent_id.volume_dry_table[:1]  
                if wet_line1:
                    volume1 = wet_line1.volume_dry
            rec.volume_dry_shir = volume1

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
    _name = "mechanical.volume.dry.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

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
    _name = "mechanical.volume.wet.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

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

# class SoilPermeabilityLine(models.Model):
#     _name = "mechanical.permeability.line1"
#     parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

#     serial_no = fields.Integer(string="Test",readonly=True, copy=False, default=1)

#     h1 = fields.Float(string="Initial Head (h1) [cm]", digits=(12,2))
#     h2 = fields.Float(string="Final Head (h2) [cm]", digits=(12,2))
#     t = fields.Float(string="Time Interval (t) [s]", digits=(12,2))

#     k_value = fields.Float(string="Permeability (k) [cm/s]", compute="_compute_k_value", store=True, digits=(12,2))

#     @api.depends("h1","h2","t","parent_id.length","parent_id.diameter_mold","parent_id.diameter_standpipe")
#     def _compute_k_value(self):
#         for rec in self:
#             rec.k_value = 0.0
#             if all([rec.h1, rec.h2, rec.t, rec.parent_id.length, rec.parent_id.diameter_mold, rec.parent_id.diameter_standpipe]):
#                 # Areas
#                 A = math.pi * rec.parent_id.diameter_mold**2 / 4.0
#                 a = math.pi * rec.parent_id.diameter_standpipe**2 / 4.0
#                 L = rec.parent_id.length
#                 t = rec.t

#                 if rec.h1 != rec.h2 and A > 0 and a > 0 and L > 0 and t > 0:
#                     h1, h2 = rec.h1, rec.h2
#                     if h1 < h2:
#                         h1, h2 = h2, h1  # swap to ensure positive log
#                     k = (2.303 * a * L) / (A * t) * math.log10(h1 / h2)
#                     rec.k_value = round(k, 2)

    

#     @api.model
#     def create(self, vals):
#         # Set the serial_no based on the existing records for the same parent
#         if vals.get('parent_id'):
#             existing_records = self.search([('parent_id', '=', vals['parent_id'])])
#             if existing_records:
#                 max_serial_no = max(existing_records.mapped('serial_no'))
#                 vals['serial_no'] = max_serial_no + 1

#         return super(SoilPermeabilityLine, self).create(vals)

#     def _reorder_serial_numbers(self):
#         # Reorder the serial numbers based on the positions of the records in child_lines
#         records = self.sorted('id')
#         for index, record in enumerate(records):
#             record.serial_no = index + 1




class DirectShearTestLine(models.Model):
    _name = "mechanical.direct.shear.test.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="Test",readonly=True, copy=False, default=1)

    ao = fields.Float(string="Area of Sample (Ao) [cm²]", digits=(12,3))
    delta = fields.Float(string="Horizontal Dial Gauge (δ) [mm]", digits=(12,3))
    proving_ring_reading = fields.Float(string="Proving Ring Reading", digits=(12,3))
    normal_stress = fields.Float(string="Normal Stress [kg/cm²]", digits=(12,3))

    horizontal_load = fields.Float(string="Horizontal Load [kg]", compute="_compute_shear", store=True, digits=(12,3))
    corrected_area = fields.Float(string="Corrected Area [cm²]", compute="_compute_shear", store=True, digits=(12,3))
    shear_stress = fields.Float(string="Shear Stress (τ) [kg/cm²]", compute="_compute_shear", store=True, digits=(12,3))

    @api.depends("ao","delta","proving_ring_reading","parent_id.proving_ring_constant")
    def _compute_shear(self):
        for rec in self:
            k = rec.parent_id.proving_ring_constant or 0
            # Horizontal Load
            rec.horizontal_load = rec.proving_ring_reading * k
            # Corrected Area
            rec.corrected_area = rec.ao * (1 - rec.delta/100)
            # Shear Stress (sign preserved)
            if rec.corrected_area != 0:
                rec.shear_stress = rec.horizontal_load / rec.corrected_area
            else:
                rec.shear_stress = 0.0

   

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



class UCSTestLine(models.Model):
    _name = "mechanical.ucs.test.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)


    dial_gauge = fields.Float(string="Dial Gauge Reading [mm]", digits=(12,3))
    proving_ring_reading = fields.Float(string="Proving Ring Reading [Division]", digits=(12,3))
    deformation = fields.Float(string="Deformation [mm]", digits=(12,3))
    
    load = fields.Float(string="Load [Kg]")  # now user input
    corrected_area = fields.Float(string="Corrected Area [cm²]", compute="_compute_corrected_area", store=True, digits=(12,3))
    axial_strain = fields.Float(string="Axial Strain", compute="_compute_axial_strain", store=True, digits=(12,3))
    stress = fields.Float(string="Stress [Kg/cm²]", compute="_compute_stress", store=True, digits=(12,3))

    @api.depends("parent_id.initial_diameter")
    def _compute_corrected_area(self):
        for rec in self:
            if rec.parent_id.initial_diameter:
                radius = rec.parent_id.initial_diameter / 2.0
                rec.corrected_area = 3.1416 * radius * radius
            else:
                rec.corrected_area = 0.0

    @api.depends("deformation","parent_id.initial_length")
    def _compute_axial_strain(self):
        for rec in self:
            L0 = rec.parent_id.initial_length or 1
            rec.axial_strain = rec.deformation / L0

    @api.depends("load","corrected_area")
    def _compute_stress(self):
        for rec in self:
            if rec.corrected_area != 0:
                rec.stress = rec.load / rec.corrected_area
            else:
                rec.stress = 0.0
    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(UCSTestLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



# class ConsolidationTestLine(models.Model):
#     _name = "mechanical.consolidation.test.line1"
#     parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

#     serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

#     load = fields.Float(string="Load [Kg]")
#     dial_gauge = fields.Float(string="Dial Gauge δ [mm]")
#     delta_h = fields.Float(string="ΔH [mm]", compute="_compute_corrected_height", store=True)
#     corrected_height = fields.Float(string="Corrected Height H [mm]", compute="_compute_corrected_height", store=True)
#     stress = fields.Float(string="Stress σ [Kg/cm²]", compute="_compute_stress", store=True, digits=(12,3))
#     strain = fields.Float(string="Strain ε", compute="_compute_strain", store=True, digits=(12,3))
#     void_ratio = fields.Float(string="Void Ratio e", compute="_compute_void_ratio", store=True, digits=(12,3))

#     @api.depends("dial_gauge","parent_id.initial_height")
#     def _compute_corrected_height(self):
#         for rec in self:
#             H0 = rec.parent_id.initial_height or 1
#             rec.delta_h = rec.dial_gauge
#             rec.corrected_height = H0 - rec.delta_h

#     @api.depends("load","parent_id.area")
#     def _compute_stress(self):
#         for rec in self:
#             A = rec.parent_id.area or 1
#             rec.stress = rec.load / A if A !=0 else 0.0

#     @api.depends("delta_h","parent_id.initial_height")
#     def _compute_strain(self):
#         for rec in self:
#             H0 = rec.parent_id.initial_height or 1
#             rec.strain = rec.delta_h / H0 if H0 !=0 else 0.0

#     @api.depends("parent_id.initial_void_ratio","stress")
#     def _compute_void_ratio(self):
#         for rec in self:
#             e0 = rec.parent_id.initial_void_ratio or 0.0
#             sigma0 = 1.0  # reference stress (usually 1 Kg/cm²)
#             if rec.stress > 0:
#                 rec.void_ratio = e0 - 0.1 * math.log10(rec.stress/sigma0)  # factor 0.1 placeholder, modify as per standard
#             else:
#                 rec.void_ratio = e0


    
#     @api.model
#     def create(self, vals):
#         # Set the serial_no based on the existing records for the same parent
#         if vals.get('parent_id'):
#             existing_records = self.search([('parent_id', '=', vals['parent_id'])])
#             if existing_records:
#                 max_serial_no = max(existing_records.mapped('serial_no'))
#                 vals['serial_no'] = max_serial_no + 1

#         return super(ConsolidationTestLine, self).create(vals)

#     def _reorder_serial_numbers(self):
#         # Reorder the serial numbers based on the positions of the records in child_lines
#         records = self.sorted('id')
#         for index, record in enumerate(records):
#             record.serial_no = index + 1



class ConsolidationPCTestLine(models.Model):
    _name = "mechanical.consolidation.test.pc.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

   
    load_pc = fields.Float(string="Load [Kg]")
    dial_gauge_pc = fields.Float(string="Dial Gauge δ [mm]")
    delta_h_pc = fields.Float(string="ΔH [mm]", compute="_compute_corrected_height_pc", store=True)
    corrected_height_pc = fields.Float(string="Corrected Height H [mm]", compute="_compute_corrected_height_pc", store=True)
    stress_pc = fields.Float(string="Stress σ [Kg/cm²]", compute="_compute_stress_pc", store=True)
    strain_pc = fields.Float(string="Strain ε", compute="_compute_strain_pc", store=True)
    void_ratio_pc = fields.Float(string="Void Ratio e", compute="_compute_void_ratio_pc", store=True)

    @api.depends("dial_gauge_pc","parent_id.initial_height_pc")
    def _compute_corrected_height_pc(self):
        for rec in self:
            H0 = rec.parent_id.initial_height_pc or 1
            rec.delta_h_pc = rec.dial_gauge_pc
            rec.corrected_height_pc = H0 - rec.delta_h_pc

    @api.depends("load_pc","parent_id.area_pc")
    def _compute_stress_pc(self):
        for rec in self:
            A = rec.parent_id.area_pc or 1
            rec.stress_pc = rec.load_pc / A if A!=0 else 0.0

    @api.depends("delta_h_pc","parent_id.initial_height_pc")
    def _compute_strain_pc(self):
        for rec in self:
            H0 = rec.parent_id.initial_height_pc or 1
            rec.strain_pc = rec.delta_h_pc / H0 if H0 !=0 else 0.0


    @api.depends("parent_id.initial_void_ratio_pc","stress_pc")
    def _compute_void_ratio_pc(self):
        for rec in self:
            e0 = rec.parent_id.initial_void_ratio_pc or 0.0
            sigma0 = 1.0  # reference stress_pc (usually 1 Kg/cm²)
            if rec.stress_pc > 0:
                rec.void_ratio_pc = e0 - 0.1 * math.log10(rec.stress_pc / sigma0)  # factor can be adjusted per standard
            else:
                rec.void_ratio_pc = e0
    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ConsolidationPCTestLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class DirectShearLine(models.Model):
    _name = "mechanical.soil.direct.shear.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    normal_stress = fields.Float(string="Normal stress σ (kPa)")
    shear_strength = fields.Float(string="Shear stress τ (kPa)")

   

    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(DirectShearLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

# class SwellingPressureLine(models.Model):
#     _name = "mechanical.swelling.line1"
#     parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

#     serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

#     dial_gauge_reading = fields.Float(string="Dial Gauge Reading (mm)")
#     load_applied = fields.Float(string="Load Applied (kg)")
#     area_of_sample = fields.Float(string="Area of Sample (cm²)", required=True)

#     swelling_pressure = fields.Float(
#         string="Swelling Pressure (kg/cm²)",
#         compute="_compute_swelling_pressure",
#         store=True
#      )

#     @api.depends('load_applied', 'area_of_sample')
#     def _compute_swelling_pressure(self):
#         for line in self:
#             if line.area_of_sample > 0:
#                 line.swelling_pressure = line.load_applied / line.area_of_sample
#             else:
#                 line.swelling_pressure = 0.0

   

    
#     @api.model
#     def create(self, vals):
#         # Set the serial_no based on the existing records for the same parent
#         if vals.get('parent_id'):
#             existing_records = self.search([('parent_id', '=', vals['parent_id'])])
#             if existing_records:
#                 max_serial_no = max(existing_records.mapped('serial_no'))
#                 vals['serial_no'] = max_serial_no + 1

#         return super(SwellingPressureLine, self).create(vals)

#     def _reorder_serial_numbers(self):
#         # Reorder the serial numbers based on the positions of the records in child_lines
#         records = self.sorted('id')
#         for index, record in enumerate(records):
#             record.serial_no = index + 1


class UUTriaxialLine(models.Model):
    _name = "mechanical.uu.triaxial.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    confining_pressure = fields.Float(string="Minor Principal Stress σ3 (kPa)")   # cell pressure
    deviator_stress = fields.Float(string="Deviator Stress qf (kPa)")

    sigma1 = fields.Float(string="Major Principal Stress σ1 (kPa)", compute="_compute_sigma_tau", store=True)
    sigma = fields.Float(string="σ (Mohr center)", compute="_compute_sigma_tau", store=True)
    tau = fields.Float(string="τ (Mohr radius)", compute="_compute_sigma_tau", store=True)

    @api.depends("confining_pressure", "deviator_stress")
    def _compute_sigma_tau(self):
        for rec in self:
            if rec.confining_pressure and rec.deviator_stress:
                rec.sigma1 = rec.confining_pressure + rec.deviator_stress
                rec.sigma = (rec.sigma1 + rec.confining_pressure) / 2.0
                rec.tau = (rec.sigma1 - rec.confining_pressure) / 2.0
            else:
                rec.sigma1 = rec.sigma = rec.tau = 0.0


   

    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(UUTriaxialLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class UUTriaxialCohesionLine(models.Model):
    _name = "mechanical.uu.triaxial.cohesion.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    confining_pressure = fields.Float(string="Minor Principal Stress σ3 (kPa)")   # cell pressure
    deviator_stress = fields.Float(string="Deviator Stress qf (kPa)")

    sigma1 = fields.Float(string="Major Principal Stress σ1 (kPa)", compute="_compute_sigma_chausion", store=True)
    sigma = fields.Float(string="σ (Mohr center)", compute="_compute_sigma_chausion", store=True)
    tau = fields.Float(string="τ (Mohr radius)", compute="_compute_sigma_chausion", store=True)

    @api.depends("confining_pressure", "deviator_stress")
    def _compute_sigma_chausion(self):
        for rec in self:
            if rec.confining_pressure and rec.deviator_stress:
                rec.sigma1 = rec.confining_pressure + rec.deviator_stress
                rec.sigma = (rec.sigma1 + rec.confining_pressure) / 2.0
                rec.tau = (rec.sigma1 - rec.confining_pressure) / 2.0
            else:
                rec.sigma1 = rec.sigma = rec.tau = 0.0


   

    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(UUTriaxialCohesionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1





#bulk density


class SoilBulkDensity(models.Model):
    _name = 'soil.bulk.density'
    
    parent_id = fields.Many2one( 'mechanical.soil1',string="Parent Test",ondelete='cascade', )

    serial_no = fields.Integer(string="Sr.No")

    date = fields.Date( string="Date")

    lab_id = fields.Char(string='Lab ID')

    wt_uds_soil = fields.Float(string='Wt of UDS+Soil (gm)')
    wt_empty_uds = fields.Float(string='Wt of empty UDS (gm)')
    wt_soil = fields.Float(string='Wt of soil (gm)', compute='_compute_wt_soil',  store=True,)

    height = fields.Float(string='Ht of sample (cm)')
    diameter = fields.Float(string='Dia of UDS (cm)')
    volume = fields.Float(string='Volume of soil sample (cm³)', compute='_compute_volume', store=True, )
    bulk_density = fields.Float( string='Bulk density (gm/cm³)', compute='_compute_bulk_density', store=True,)

   

    @api.depends('wt_uds_soil', 'wt_empty_uds')
    def _compute_wt_soil(self):
        for rec in self:
            rec.wt_soil = (rec.wt_uds_soil or 0.0) - (rec.wt_empty_uds or 0.0)

    @api.depends('height', 'diameter')
    def _compute_volume(self):
        for rec in self:
            if rec.height and rec.diameter:
                r = rec.diameter / 2.0
                rec.volume = pi * r * r * rec.height    
            else:
                rec.volume = 0.0

    @api.depends('wt_soil', 'volume')
    def _compute_bulk_density(self):
        for rec in self:
            rec.bulk_density = rec.wt_soil / rec.volume if rec.volume else 0.0  

   

    @api.model
    def create(self, vals):
        if vals.get('parent_id') and not vals.get('serial_no'):
            existing = self.search(
                [('parent_id', '=', vals['parent_id'])],
                order='serial_no desc',
                limit=1,
            )
            vals['serial_no'] = (existing.serial_no or 0) + 1 if existing else 1
        return super().create(vals)

    def _reorder_serial_numbers(self):
        # Call this after manual delete/reorder if needed
        for parent in self.mapped('parent_id'):
            lines = parent.bulk_line_ids.sorted('id')
            for idx, line in enumerate(lines, start=1):
                line.serial_no = idx









#  Calculation-NMC, 

class SoilMoisture(models.Model):
    _name = 'soil.moisture'
  
    parent_id = fields.Many2one(   'mechanical.soil1',  string="Parent Id", ondelete='cascade', )

    serial_no = fields.Integer(string='Sr.No')

    date = fields.Date(string="Date")
    lab_id = fields.Char(string='Lab ID')

    wet_soil_container = fields.Float(string='Weight of wet soil + container (gm)' )
    dry_soil_container = fields.Float( string='Weight of oven dry soil + container (gm)' )
    container_weight = fields.Float( string='Weight of container (gm)' )
    moisture_content = fields.Float(  string='Moisture content %',  compute='_compute_moisture_content',  store=True,)

    avg_nmc = fields.Float( string='Avg NMC %', compute='_compute_avg_nmc', store=True,)

    is_ok = fields.Boolean( string='True/False',compute='_compute_is_ok',store=True,)

  
    @api.depends('wet_soil_container', 'dry_soil_container', 'container_weight')
    def _compute_moisture_content(self):
        for rec in self:
            w_wet = rec.wet_soil_container or 0.0
            w_dry = rec.dry_soil_container or 0.0
            w_cont = rec.container_weight or 0.0
            dry_soil = w_dry - w_cont
            if dry_soil > 0:
                water = w_wet - w_dry
                rec.moisture_content = (water / dry_soil) * 100.0
            else:
                rec.moisture_content = 0.0


    @api.depends('moisture_content', 'date', 'lab_id', 'parent_id')
    def _compute_avg_nmc(self):
        for rec in self:
            if not (rec.date and rec.lab_id and rec.parent_id):
                rec.avg_nmc = 0.0
                continue

            trials = self.search([
                ('parent_id', '=', rec.parent_id.id),
                ('date', '=', rec.date),
                ('lab_id', '=', rec.lab_id),
            ])

        
            values = [t.moisture_content for t in trials]
            rec.avg_nmc = sum(values) / len(values) if values else 0.0

 

    @api.depends('moisture_content', 'avg_nmc')
    def _compute_is_ok(self):
        for rec in self:
            mc = rec.moisture_content or 0.0
            avg = rec.avg_nmc or 0.0
            rec.is_ok = bool(avg and abs(mc - avg) <= 2.0)



    @api.model
    def create(self, vals):
        if vals.get('parent_id') and not vals.get('serial_no'):
            existing = self.search(
                [('parent_id', '=', vals['parent_id'])],
                order='serial_no desc',
                limit=1,
            )
            vals['serial_no'] = (existing.serial_no or 0) + 1 if existing else 1
        return super(SoilMoisture, self).create(vals)

    def _reorder_serial_numbers(self):
        for parent in self.mapped('parent_id'):
            records = self.search([('parent_id', '=', parent.id)], order='id')
            for index, record in enumerate(records, start=1):
                record.serial_no = index


    


class SoilGSALINE(models.Model):
    _name = "mechanical.gsa.line"
    parent_id = fields.Many2one(
        'mechanical.soil1',
        string="Parent Soil",
        ondelete='cascade'
    )

    
    


    sr_no = fields.Integer(string="Sr NO.")
    #  readonly=True, copy=False, default=1
    
    symbol = fields.Char(string="Symbol")
    bh_id = fields.Char(string="BH ID")
    lab_no = fields.Char(string="LAB ID")
    sample_depth = fields.Char(string="Sample Depth (m)")
    sample_details = fields.Char(string="Sample Details")

    water_content = fields.Char(string="Water Content (%)")

    wt_of_samp = fields.Float(string="Weight of total sample (gm)")

    temp = fields.Float("Temp °c" )
    humidity = fields.Float("Humidity %" )

    wt_of_samp1 = fields.Float(string="Weight of total sample (gm)")

    meniscus_corre = fields.Float(string="Meniscus Correction, Cm", digits=(12,1))
    vescosity_water = fields.Float(string="Viscosity of Water at Room Temperature in poise",digits=(12,6),store=True)
    dispersion = fields.Float(string="Dispersion Agent Correction, x")
    temp_corre = fields.Float(string="Temperature Correction, Mt",compute="_compute_temp_corre",digits=(12,4))
    specific_gravity = fields.Float(string="Specific gravity",digits=(12,3))


    

    # Silt Field Definition
    silt = fields.Float(
        string="% Silt", 
        compute='_compute_silt', 
        store=True, 
        digits=(12, 0)
    )

    @api.depends('silt_clay', 'sand', 'gravel')
    def _compute_silt(self):
        for rec in self:
            # Formula: 100 - (Clay + Sand + Gravel)
            # silt_clay variable madhe apan % Clay chi value store keli ahe
            total_other = rec.silt_clay + rec.sand + rec.gravel
            
            # Silt calculate kara
            rec.silt = 100 - total_other


    gravel = fields.Float(string="% Gravel", compute='_compute_gravel', store=True, digits=(12, 0)) # Digits 0 kele mhanje point disnar nahi

    @api.depends('sieve_analysis_child_lines_gsa.passing_percent', 'sieve_analysis_child_lines_gsa.sieve_size')
    def _compute_gravel(self):
        for record in self:
            val_top = 0.0
            val_bottom = 0.0

            if record.sieve_analysis_child_lines_gsa:
                for line in record.sieve_analysis_child_lines_gsa:
                    try:
                        # Value Extract Logic
                        txt = str(line.sieve_size).lower().replace('mm', '').strip()
                        size = float(txt)

                        if size >= 40:
                            val_top = line.passing_percent
                        
                        if size == 4.75:
                            val_bottom = line.passing_percent
                            
                    except ValueError:
                        continue

            # --- ROUNDING LOGIC ---
            # round() vaparlya mule 4.5 -> 4 hoil ani 4.6 -> 5 hoil.
            record.gravel = round(val_top - val_bottom)

    sand = fields.Float(string="% Sand", compute='_compute_sand', store=True, digits=(12, 0))

    @api.depends('sieve_analysis_child_lines_gsa.passing_percent',
                 'sieve_analysis_child_lines_gsa.sieve_size')
    def _compute_sand(self):
        # Change: 'rec' vaparla ahe, tar khali pan 'rec' vapra
        for rec in self:
            passing_475 = 0.0
            passing_0075 = 0.0

            # ERROR HERE FIXED: 'record' -> 'rec'
            if rec.sieve_analysis_child_lines_gsa:
                for line in rec.sieve_analysis_child_lines_gsa:
                    try:
                        # Value Extract Logic
                        txt = str(line.sieve_size).lower().replace('mm', '').strip()
                        size = float(txt)

                        # 4.75 mm value
                        if size == 4.75:
                            passing_475 = line.passing_percent
                        
                        # 0.075 mm value
                        if size == 0.075:
                            passing_0075 = line.passing_percent
                            
                    except ValueError:
                        continue

            # % Sand = Passing at 4.75 − Passing at 0.075
            # round() vaparla mhanje point nantar value yenar nahi (Integer)
            rec.sand = round(passing_475 - passing_0075)

    # Field Definition
    silt_clay = fields.Float(
        string="% Clay", 
        compute='_compute_silt_clay', 
        store=True, 
        digits=(12, 0) # Round 0 digits
    )

    @api.depends('sieve_analysis_child_lines_gsa.passing_percent', 'sieve_analysis_child_lines_gsa.sieve_size')
    def _compute_silt_clay(self):
        for rec in self:
            clay_val = 0.0
            
            # 1. Collect valid data points (Size, Passing)
            data_points = []
            if rec.sieve_analysis_child_lines_gsa:
                for line in rec.sieve_analysis_child_lines_gsa:
                    try:
                        txt = str(line.sieve_size).lower().replace('mm', '').strip()
                        if not txt: continue
                        size = float(txt)
                        passing = line.passing_percent
                        data_points.append({'size': size, 'passing': passing})
                    except ValueError:
                        continue
            
            # 2. Sort by Size Descending (Largest -> Smallest)
            # List: [4.75, ..., 0.005, 0.001]
            # Last = 0.001 (Smallest), Second Last = 0.005
            data_points.sort(key=lambda k: k['size'], reverse=True)

            # 3. Apply Formula if at least 2 points exist
            if len(data_points) >= 2:
                last = data_points[-1]        # x1, y1 (Last Value)
                second_last = data_points[-2] # x2, y2 (Second Last Value)

                x1 = last['size']
                y1 = last['passing']
                
                x2 = second_last['size']
                y2 = second_last['passing']

                # Formula:
                # ((y2 - y1) / (x2 - x1)) * (0.002 - x1) + y1
                if (x2 - x1) != 0:
                    clay_val = ((y2 - y1) / (x2 - x1)) * (0.002 - x1) + y1
            
            # 4. Round to 0 decimals (Integer)
            rec.silt_clay = round(clay_val)



   


    @api.depends('temp')
    def _compute_vescosity_water(self):
        for rec in self:
            t = rec.temp
            if t is not False and t < 19:
                rec.vescosity_water = (
                    (0.0000000053308 * (t ** 4))
                    - (0.00000045221 * (t ** 3))
                    + (0.000019001 * (t ** 2))
                    - (0.00063391 * t)
                    + 0.017937
                )
            else:
                rec.vescosity_water = 0.0


    @api.depends('temp')
    def _compute_temp_corre(self):
        for rec in self:
            if rec.temp is not False:
                rec.temp_corre = (-0.2109 * rec.temp) + 5.6814
            else:
                rec.temp_corre = 0.0


    sieve_analysis_child_lines_gsa = fields.One2many(
        'gsa.lab.sieve.analysis.line',
        'parent_id_gsa',
        string="Sieve Analysis"
    )

    hydrometer_analysis_lines_gsa = fields.One2many(
        'gsa.hydrometer.analysis.line',
        'parent_id_gsa',
        string="Sieve Analysis",default=lambda self: self._default_hydrometer_analysis_lines_gsa()
    )


    def action_add_n_corrected(self):
        for record in self:

            # 1️⃣ 0.075 sieve exists?
            sieve_075 = record.sieve_analysis_child_lines_gsa.filtered(
                lambda l: l.sieve_size == '0.075'
            )
            if not sieve_075:
                raise UserError("0.075 sieve line not found")

            # 2️⃣ Take ALL hydrometer lines AS-IS (order preserved)
            hydro_lines = record.hydrometer_analysis_lines_gsa.filtered(
                lambda h: h.n_corrected is not False
            )

            if not hydro_lines:
                raise UserError("No Hydrometer data found")

            # 3️⃣ Delete old < 0.075 sieve rows
            for line in record.sieve_analysis_child_lines_gsa:
                try:
                    if float(line.sieve_size) < 0.075:
                        line.unlink()
                except Exception:
                    pass

            # 4️⃣ Insert EXACT hydrometer values (duplicates + 0.00 included)
            for h in hydro_lines:
                self.env['gsa.lab.sieve.analysis.line'].create({
                    'parent_id_gsa': record.id,
                    'sieve_size': f"{h.diameter_soil:.4f}",   # 0.05, 0.04 ... 0.00
                    'passing_percent': h.n_corrected,         # 65.05 ... 6.58
                    
                })



    @api.model
    def _default_hydrometer_analysis_lines_gsa(self):
        return [
            (0, 0, {'time': 0.5}),
            (0, 0, {'time': 1}),
            (0, 0, {'time': 2}),
            (0, 0, {'time': 4}),
            (0, 0, {'time': 8}),
            (0, 0, {'time': 15}),
            (0, 0, {'time': 30}),
            (0, 0, {'time': 60}),
            (0, 0, {'time': 120}),
            (0, 0, {'time': 240}),
            (0, 0, {'time': 1440}),
        ]

    @api.model
    def create(self, vals):
        record = super().create(vals)

        # List of default IS sieve sizes
        default_sieve_sizes = [
            "50", "40", "25", "20", "16", "12.5", "10",
            "6.3", "4.75", "2.36", "1.18", "0.6", "0.425",
            "0.3", "0.15", "0.075"
        ]

        # Generate default child lines if none exist
        if not record.sieve_analysis_child_lines_gsa:
            lines = []
            for i, sieve in enumerate(default_sieve_sizes, start=1):
                lines.append((0, 0, {
                 
                    'sieve_size': sieve,
                  
                }))
            record.sieve_analysis_child_lines_gsa = lines

        return record

    def calculate_sieve_gsa(self): 
        for record in self:

        

            previous_cumulative = 0  
            for line in record.sieve_analysis_child_lines_gsa:
                print("Rows", str(line.percent_retained))
                previous_line = line.serial_no - 1
                if previous_line == 0:
                    cumulative_retained = line.percent_retained
                else:
                    previous_line_record = self.env['gsa.lab.sieve.analysis.line'].sudo().search([("serial_no", "=", previous_line),("parent_id", "=", record.id)], limit=1)
                    
                    if previous_line_record:
                        previous_cumulative = previous_line_record.cumulative_retained
                    cumulative_retained = previous_cumulative + line.percent_retained

                passing_percent = 100 - cumulative_retained

                line.write({
                    'cumulative_retained': round(cumulative_retained, 2),
                    'passing_percent': round(passing_percent, 2),
                })
                
                print("Updated Cumulative Retained:", cumulative_retained)
                print("Updated Passing Percent:", passing_percent)

                previous_cumulative = cumulative_retained

    








    


  


   

class SoilSieveAnalysisLineGSA(models.Model):
    _name = "gsa.lab.sieve.analysis.line"
    # parent_id = fields.Many2one('mechanical.gsa.line', string="Parent Id")

    parent_id_gsa = fields.Many2one(
        'mechanical.gsa.line',
        string="GSA Line",
        ondelete='cascade'
    )

    lab_no = fields.Char(string="LAB ID")

    wt_of_samp = fields.Float(string="Weight of total sample (gm)")

    temp = fields.Float("Temp °c" )
    humidity = fields.Float("Humidity %" )


   

    

    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size")
    wt_retained = fields.Float(string="Soil Retained wt",digits=(12,3))
    percent_retained = fields.Float(string='Cumulative Wt. retained',compute="_compute_percent_retained1",digits=(12,2) )
    cumulative_retained = fields.Float(string="Cumulative % retained",compute="_compute_cumulative_retained" , store=True)
    passing_percent = fields.Float(string="% Passing ",digits=(12,3),store=True)

    

    
    # --------------------------------------------------
    # SERIAL NUMBER AUTO ASSIGN
    # --------------------------------------------------
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SoilSieveAnalysisLineGSA, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

    # --------------------------------------------------
    # UNLINK HANDLING
    # --------------------------------------------------
    def unlink(self):
        parents = self.mapped('parent_id_gsa')
        res = super().unlink()
        for parent in parents:
            parent.sieve_analysis_child_lines_gsa._reorder_serial_numbers()
        return res

    

    @api.depends('wt_retained', 'parent_id_gsa.sieve_analysis_child_lines_gsa.wt_retained')
    def _compute_percent_retained1(self):
        for record in self:
            record.percent_retained = 0.0
            if not record.parent_id_gsa:
                continue

            # Use the recordset order directly; avoid sorting by id
            cumulative = 0.0
            for line in record.parent_id_gsa.sieve_analysis_child_lines_gsa:
                cumulative += line.wt_retained or 0.0
                if line == record:
                    record.percent_retained = round(cumulative, 3)
                    break


    # --------------------------------------------------
    # COMPUTE CUMULATIVE % RETAINED
    # --------------------------------------------------
    @api.depends(
    'percent_retained',
    'parent_id_gsa.wt_of_samp'
    )
    def _compute_cumulative_retained(self):
        for record in self:
            if record.parent_id_gsa and record.parent_id_gsa.wt_of_samp:
                record.cumulative_retained = round(
                    (record.percent_retained / record.parent_id_gsa.wt_of_samp) * 100,
                    3
                )
            else:
                record.cumulative_retained = 0.0


    # --------------------------------------------------
    # COMPUTE % PASSING
    # --------------------------------------------------
    # @api.depends('cumulative_retained')
    # def _compute_passing_percent(self):
    #     for record in self:
    #         record.passing_percent = round(
    #             100 - (record.cumulative_retained or 0.0),
    #             3
    #         )



class SoilHydrometerLineGSA(models.Model):
    _name = "gsa.hydrometer.analysis.line"
    # parent_id = fields.Many2one('mechanical.gsa.line', string="Parent Id")

    parent_id_gsa = fields.Many2one(
        'mechanical.gsa.line',
        string="GSA Line",
        ondelete='cascade'
    )


    wt_of_samp1 = fields.Float(string="Weight of total sample (gm)")

    meniscus_corre = fields.Float(string="Meniscus Correction, Cm",digits=(12,1))
    vescosity_water = fields.Float(string="Viscosity of Water at Room Temperature in poise",compute="_compute_vescosity_water",digits=(12,6),store=True)
    dispersion = fields.Float(string="Dispersion Agent Correction, x")
    temp_corre = fields.Float(string="Temperature Correction, Mt",compute="_compute_temp_corre",digits=(12,4))
    specific_gravity = fields.Float(string="Specific gravity",digits=(12,3))

    temp = fields.Float("Temp °c" )


    @api.depends('parent_id_gsa.temp')
    def _compute_vescosity_water(self):
        for rec in self:
            t = rec.parent_id_gsa.temp
            if t is not False and t < 19:
                rec.vescosity_water = (
                    (0.0000000053308 * (t ** 4))
                    - (0.00000045221 * (t ** 3))
                    + (0.000019001 * (t ** 2))
                    - (0.00063391 * t)
                    + 0.017937
                )
            else:
                rec.vescosity_water = 0.0


    @api.depends('parent_id_gsa.temp')
    def _compute_temp_corre(self):
        for rec in self:
            if rec.parent_id_gsa.temp is not False:
                rec.temp_corre = (-0.2109 * rec.parent_id_gsa.temp) + 5.6814
            else:
                rec.temp_corre = 0.0

    

    
    time = fields.Float(string="Time ")
    hydrometer_reading = fields.Float(string="Hydrometer Reading",digits=(12,1))
    men_corrected = fields.Float(string="Meniscus Corrected",digits=(12,1),compute="_compute_men_corrected")
    eff_depth = fields.Float(string='Effective Depth',digits=(12,1) ,compute="_compute_eff_depth")
    velocity = fields.Float(string="Velocity" , store=True,compute="_compute_velocity",digits=(12,2))
    temp_combined = fields.Float(string="Temp. + Dispersion Combined ",digits=(12,2),compute="_compute_temp_combined",store=True)

    root_velocity = fields.Float(string="Sq. root of Velocity ",digits=(12,2),compute="_compute_root_velocity",store=True)
    diameter_soil = fields.Float(string="Diameter of soil",digits=(12,4),compute="_compute_diameter_soil",store=True)
    n_finner = fields.Float(string="N% Finer than",digits=(12,2),compute="_compute_n_finner",store=True)
    n_corrected = fields.Float(string="N% corrected",digits=(12,2),store=True,compute="_compute_n_corrected")


    @api.depends('hydrometer_reading', 'parent_id_gsa.meniscus_corre')
    def _compute_men_corrected(self):
        for rec in self:
            rec.men_corrected = (
                (rec.hydrometer_reading or 0.0) +
                (rec.parent_id_gsa.meniscus_corre or 0.0)
            )

    @api.depends('men_corrected', 'time')
    def _compute_eff_depth(self):
        for rec in self:
            if rec.men_corrected:
                rec.eff_depth = (-0.3444 * rec.men_corrected) + (
                    21.736 if rec.time in (8.0, 15.0, 30.0, 60.0, 120.0, 240.0, 1440.0)
                    else 20.256
                )
            else:
                rec.eff_depth = 0.0

    @api.depends('eff_depth', 'time')
    def _compute_velocity(self):
        for rec in self:
            if rec.time:
                rec.velocity = rec.eff_depth / rec.time
            else:
                rec.velocity = 0.0

    @api.depends(
    'men_corrected',
    'parent_id_gsa.temp_corre',
    'parent_id_gsa.dispersion'
    )
    def _compute_temp_combined(self):
        for rec in self:
            rec.temp_combined = (
                (rec.men_corrected or 0.0)
                + (rec.parent_id_gsa.temp_corre or 0.0)
                - (rec.parent_id_gsa.dispersion or 0.0)
            )

    @api.depends('velocity')
    def _compute_root_velocity(self):
        for rec in self:
            if rec.velocity and rec.velocity > 0:
                rec.root_velocity = math.sqrt(rec.velocity)
            else:
                rec.root_velocity = 0.0

    @api.depends(
    'root_velocity',
    'parent_id_gsa.vescosity_water',
    'parent_id_gsa.specific_gravity'
    )
    def _compute_diameter_soil(self):
        for rec in self:
            v = rec.parent_id_gsa.vescosity_water
            sg = rec.parent_id_gsa.specific_gravity

            if rec.root_velocity and v and sg and sg > 1:
                constant_part = (18 / (981 * 60)) * (v / (sg - 1))
                rec.diameter_soil = 10 * math.sqrt(constant_part) * rec.root_velocity
            else:
                rec.diameter_soil = 0.0

    @api.depends(
    'temp_combined',
    'parent_id_gsa.specific_gravity',
    'parent_id_gsa.wt_of_samp1'
    )
    def _compute_n_finner(self):
        for rec in self:
            sg = rec.parent_id_gsa.specific_gravity
            wt = rec.parent_id_gsa.wt_of_samp1
            tc = rec.temp_combined

            if sg and sg > 1 and wt and tc:
                rec.n_finner = (
                    (sg / (sg - 1))
                    * (1 / wt)
                    * tc
                    * 100
                )
            else:
                rec.n_finner = 0.0

    @api.depends(
    'n_finner',
    'parent_id_gsa.sieve_analysis_child_lines_gsa.sieve_size',
    'parent_id_gsa.sieve_analysis_child_lines_gsa.passing_percent'
    )
    def _compute_n_corrected(self):
        for rec in self:
            passing_075 = 0.0

            # get passing_percent where sieve_size == '0.075'
            for line in rec.parent_id_gsa.sieve_analysis_child_lines_gsa:
                if line.sieve_size == '0.075':
                    passing_075 = line.passing_percent or 0.0
                    break

            if passing_075 and rec.n_finner:
                rec.n_corrected = (passing_075 * rec.n_finner) / 100
            else:
                rec.n_corrected = 0.0



# specific gravity




class SpecificGravity(models.Model):
    _name = "specific.gravity"
   

    parent_id = fields.Many2one(
        "mechanical.soil1",
        string="Parent Test",
        ondelete="cascade",
        required=True,
    )
    serial_no = fields.Integer(string="Sr.No", readonly=True)

  
    date = fields.Date(string="DATE TEST")
    lab_id = fields.Char(string="Lab No.")
    room_temp = fields.Float(string="Room Temperature (°C)")
    bottle_no = fields.Char(string="Bottle No.")

    wt_empty_bottle = fields.Float(string="Empty Wt. of Bottle (W1)")
    wt_bottle_dry_soil = fields.Float(string="Bottle + dry soil (W2)")
    wt_bottle_dry_soil_water = fields.Float(string="Bottle + Dry soil + Water (W3)")
    wt_bottle_water = fields.Float(string="Bottle + Water (Tap) (W4)")

    specific_gravity = fields.Float( string="Specific Gravity (G)", compute="_compute_specific_gravity", store=True, readonly=True,)
    density_water = fields.Float( string="Density of water at room temp (gm/cc)", compute="_compute_density_water", store=True,  readonly=True, )
    corr_specific_gravity = fields.Float(string="Corrected Specific Gravity (G')",compute="_compute_corr_specific_gravity", store=True, readonly=True,
 )
    avg_corr_specific_gravity = fields.Float(
        string="Average corrected Specific Gravity",
        compute="_compute_avg_corr_specific_gravity",
        store=True,
        readonly=True,
    )

   
    @api.depends(
        "wt_empty_bottle",
        "wt_bottle_dry_soil",
        "wt_bottle_dry_soil_water",
        "wt_bottle_water",
    )
    def _compute_specific_gravity(self):
        for rec in self:
            W1 = rec.wt_empty_bottle or 0.0
            W2 = rec.wt_bottle_dry_soil or 0.0
            W3 = rec.wt_bottle_dry_soil_water or 0.0
            W4 = rec.wt_bottle_water or 0.0
            denom = (W4 - W1) - (W3 - W2)
            rec.specific_gravity = (W2 - W1) / denom if denom else 0.0

  
    @api.depends("room_temp")
    def _compute_density_water(self):
        for rec in self:
            T = rec.room_temp or 27.0
          
            rec.density_water = 1.0 - 0.0003 * max(0.0, T - 4.0)

  
    @api.depends("specific_gravity", "density_water")
    def _compute_corr_specific_gravity(self):
        for rec in self:
            rho_27 = 1.0 - 0.0003 * (27.0 - 4.0)  
            rec.corr_specific_gravity = (
                rec.specific_gravity * (rec.density_water / rho_27) if rho_27 else 0.0
            )

  
    @api.depends("parent_id", "date", "lab_id", "corr_specific_gravity")
    def _compute_avg_corr_specific_gravity(self):
        for rec in self:
            if not rec.parent_id:
                rec.avg_corr_specific_gravity = 0.0
                continue
            siblings = self.search([
                ("parent_id", "=", rec.parent_id.id),
                ("date", "=", rec.date),
                ("lab_id", "=", rec.lab_id),
            ])
            vals = [l.corr_specific_gravity for l in siblings if l.corr_specific_gravity]
            rec.avg_corr_specific_gravity = sum(vals) / len(vals) if vals else 0.0

 

    @api.model
    def create(self, vals):
        if vals.get("parent_id") and not vals.get("serial_no"):
            last = self.search(
                [("parent_id", "=", vals["parent_id"])],
                order="serial_no desc",
                limit=1,
            )
            vals["serial_no"] = (last.serial_no or 0) + 1 if last else 1
        return super().create(vals)




# Atterbergs Limits (Free Swell)

 
class SoilFreeSwell(models.Model):
    _name = "soil.free.swell"


    parent_id = fields.Many2one( "mechanical.soil1", string="Parent Test", ondelete="cascade", required=True,)
    serial_no = fields.Integer(string="Sr.No", readonly=True)
    lab_id = fields.Char(string="Lab No.")

    vd = fields.Float(string="Vd")  
    vk = fields.Float(string="Vk") 

    free_swell = fields.Float( string="Free swell (%)", compute="_compute_free_swell", store=True, readonly=True,)
    is_ok = fields.Boolean( string="TRUE/FALSE",  compute="_compute_is_ok",  store=True, readonly=True,)

   
    @api.depends("vd", "vk")
    def _compute_free_swell(self):
        for rec in self:
            if rec.vk:
                rec.free_swell = (rec.vd - rec.vk) / rec.vk * 100.0
            else:
                rec.free_swell = 0.0

    
    @api.depends("free_swell")
    def _compute_is_ok(self):
        for rec in self:
            rec.is_ok = bool(rec.free_swell and rec.free_swell <= 50.0)

    @api.model
    def create(self, vals):
        if vals.get("parent_id") and not vals.get("serial_no"):
            last = self.search(
                [("parent_id", "=", vals["parent_id"])],
                order="serial_no desc",
                limit=1,
            )
            vals["serial_no"] = (last.serial_no or 0) + 1 if last else 1
        return super().create(vals)


class ConsolidationLoadingLine(models.Model):
    _name = "consolidation.loading.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    time_m = fields.Float(string="Time (Minutes)")
    sqrt_time = fields.Float(string="SQRT (t) min", compute="_compute_sqrt_time", store=True)
    load_0_05_0_1 = fields.Float(string="0.05-0.1 kg/cm²",digits=(8,3))
    load_0_1_0_2 = fields.Float(string="0.1-0.2 kg/cm²" ,digits=(8,3))
    load_0_2_0_5 = fields.Float(string="0.2-0.5 kg/cm²" ,digits=(8,3))
    load_0_5_1_0 = fields.Float(string="0.5-1.0 kg/cm²" ,digits=(8,3))
    load_1_0_2_0 = fields.Float(string="1.0-2.0 kg/cm²" ,digits=(8,3))
    load_2_0_4_0 = fields.Float(string="2.0-4.0 kg/cm²" ,digits=(8,3))
    load_4_0_8_0 = fields.Float(string="4.0-8.0 " ,digits=(8,3))

    @api.depends("time_m")
    def _compute_sqrt_time(self):
        for rec in self:
            if rec.time_m:
                rec.sqrt_time = rec.time_m ** 0.5
            else:
                rec.sqrt_time =  0.0


   

    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ConsolidationLoadingLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class ConsolidationUnloadingLine(models.Model):
    _name = "consolidation.unloading.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    time_m = fields.Float(string="Time (Minutes)")
    load_8_0_4_0 = fields.Float(string="8.0-4.0" ,digits=(8,3))
    load_4_0_8_0 = fields.Float(string="4.0-8.0" ,digits=(8,3))
    load_2_0_4_0 = fields.Float(string="2.0-4.0" ,digits=(8,3))
    load_1_0_2_0 = fields.Float(string="1.0-2.0" ,digits=(8,3))
    load_0_5_1_0 = fields.Float(string="0.5-1.0" ,digits=(8,3))
    load_0_2_0_5 = fields.Float(string="0.2-0.5" ,digits=(8,3))
    load_0_1_0_2 = fields.Float(string="0.1-0.2" ,digits=(8,3))
    # load_0_05_0_1 = fields.Float(string="0.05-0.1",digits=(8,3))
    setting_load = fields.Float(string="Setting Load",digits=(8,3))


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ConsolidationUnloadingLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class ConsolidationBothCycleLine(models.Model):
    _name = "consolidation.both.cycle.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    cylces=  fields.Char(string="Cycles" )

    applied_pressure = fields.Float(string="Applied Pressure kg/cm²" , digits=(8,2))
    final_read = fields.Float(string="Final Dial Reading mm" ,digits=(8,3),compute="_compute_final_read", store=True)
    delta_h = fields.Float(string=" Δ𝐻 cm" ,digits=(8,3),compute="_compute_delta_h" ,store=True)
    specimen_height = fields.Float(string="Specimen Height (H) cm" ,digits=(8,3) , compute="_compute_specimen_height" ,store=True )
    e_void = fields.Float(string="e = (H/Hs)-1" ,digits=(8,3) , compute="_compute_e_void" ,store=True)
    change_void = fields.Float(string="de", digits=(16,6), compute="_compute_change_void" ,store=True)
    d_sigma = fields.Float(string=" dσ" ,digits=(16,6) , compute="_compute_d_sigma" ,store=True)
    av = fields.Float(string="aᵥ (cm²/kg)" ,digits=(16,6) ,compute="_compute_av" ,store=True)
    mv = fields.Float("mᵥ (cm²/kg)", digits=(8, 3),compute="_compute_mv" ,store=True)

    t90 = fields.Float("t₉₀ (min)", digits=(8, 3))
    Hav = fields.Float("Hav (cm)", digits=(8, 3))

    cv = fields.Float("cᵥ (cm²/sec)", digits=(16, 4), compute="_compute_cv" ,store=True)
    cc = fields.Float("cc (cm²/sec)", digits=(8, 3), compute="_compute_cc" ,store=True)

    @api.depends(
    'applied_pressure', 'cylces',
    'parent_id.consolidation_ids.load_0_05_0_1',
    'parent_id.consolidation_ids.load_0_1_0_2',
    'parent_id.consolidation_ids.load_0_2_0_5',
    'parent_id.consolidation_ids.load_0_5_1_0',
    'parent_id.consolidation_ids.load_1_0_2_0',
    'parent_id.consolidation_ids.load_2_0_4_0',
    'parent_id.consolidation_ids.load_4_0_8_0',
    'parent_id.consolidation_unloading_ids.load_8_0_4_0',
    'parent_id.consolidation_unloading_ids.load_4_0_8_0',
    'parent_id.consolidation_unloading_ids.load_2_0_4_0',
    'parent_id.consolidation_unloading_ids.load_1_0_2_0',
    'parent_id.consolidation_unloading_ids.load_0_5_1_0',
    'parent_id.consolidation_unloading_ids.load_0_2_0_5',
    'parent_id.consolidation_unloading_ids.load_0_1_0_2',
    # 'parent_id.consolidation_unloading_ids.load_0_05_0_1',
)
    def _compute_final_read(self):
     for line in self:
        parent = line.parent_id
        line.final_read = 0.0
        if not parent:
            continue

        # helper to get min safely
        def _min(vals):
            vals = [v for v in vals if v not in (False, None)]
            return min(vals) if vals else 0.0

        # ------------- LOADING -------------
        if line.cylces == '1st Cycle Loading':
            if line.applied_pressure == 0.05:
                # Excel: =Input!D21 (first loading row, 0 min)
                recs = parent.consolidation_ids.sorted('time_m')
                line.final_read = recs[0].load_0_05_0_1 if recs else 0.0

            elif line.applied_pressure == 0.10:
                line.final_read = _min(parent.consolidation_ids.mapped('load_0_05_0_1'))

            elif line.applied_pressure == 0.20:
                line.final_read = _min(parent.consolidation_ids.mapped('load_0_1_0_2'))

            elif line.applied_pressure == 0.50:
                line.final_read = _min(parent.consolidation_ids.mapped('load_0_2_0_5'))

            elif line.applied_pressure == 1.00:
                line.final_read = _min(parent.consolidation_ids.mapped('load_0_5_1_0'))

            elif line.applied_pressure == 2.00:
                line.final_read = _min(parent.consolidation_ids.mapped('load_1_0_2_0'))

            elif line.applied_pressure == 4.00:
                line.final_read = _min(parent.consolidation_ids.mapped('load_2_0_4_0'))

            elif line.applied_pressure == 8.00:
                line.final_read = _min(parent.consolidation_ids.mapped('load_4_0_8_0'))

        # ------------- UNLOADING -------------
        elif line.cylces == '1st Cycle Unloading':
          if line.applied_pressure == 8.00:
            # C23 = first setting‑load reading (Input!N21)
            recs = parent.consolidation_unloading_ids.sorted('time_m')
            vals = [recs[0].load_8_0_4_0] if recs else []

          elif line.applied_pressure == 4.00:
             prev_line = parent.consolidation_output_ids.filtered(
              lambda l: l.cylces == '1st Cycle Unloading'
             and l.applied_pressure == 8.00
             )
             prev_line = prev_line[0] if prev_line else False
             c18 = prev_line.final_read if prev_line else 0.0

             if not c18:
               first = parent.consolidation_unloading_ids.sorted('time_m')[:1]
               first = first[0] if first else False
               vals = [first.load_4_0_8_0] if first else []
             else:
               vals = parent.consolidation_unloading_ids.mapped('load_8_0_4_0')
          elif line.applied_pressure == 2.00:
           vals = parent.consolidation_unloading_ids.mapped('load_4_0_8_0')
          elif line.applied_pressure == 1.00:
           vals = parent.consolidation_unloading_ids.mapped('load_2_0_4_0')
          elif line.applied_pressure == 0.50:
           vals = parent.consolidation_unloading_ids.mapped('load_1_0_2_0')
          elif line.applied_pressure == 0.20:
           vals = parent.consolidation_unloading_ids.mapped('load_0_5_1_0')
          elif line.applied_pressure == 0.10:
           vals = parent.consolidation_unloading_ids.mapped('load_0_2_0_5')
          elif line.applied_pressure == 0.05:
           vals = parent.consolidation_unloading_ids.mapped('load_0_1_0_2')
          else:
           vals = []

          vals = [v for v in vals if v not in (False, None)]
          line.final_read = max(vals) if vals else 0.0


    @api.depends(
    'final_read', 'applied_pressure', 'cylces', 'serial_no',
    'parent_id.consolidation_output_ids.final_read',
    'parent_id.consolidation_output_ids.applied_pressure',
    'parent_id.consolidation_output_ids.cylces',
    'parent_id.consolidation_output_ids.serial_no')
    def _compute_delta_h(self):
     for line in self:
        parent = line.parent_id
        line.delta_h = 0.0
        if not parent:
            continue

        lines = list(parent.consolidation_output_ids.sorted('serial_no'))
        if not lines:
            continue

        try:
            idx = lines.index(line)
        except ValueError:
            continue

        # first row → 0.000
        if idx == 0:
            line.delta_h = 0.0
            continue

        prev = lines[idx - 1]

        # last loading row: if dial = 0, reuse previous ΔH
        if line.cylces == '1st Cycle Loading' and line.applied_pressure == 8.00:
            if line.final_read == 0 and prev:
                line.delta_h = prev.delta_h
                continue

        # 4.00 unloading (Excel: IF(C18=0, D21, (C19-C20)/10))
        if line.cylces == '1st Cycle Unloading' and line.applied_pressure == 4.00:
            # row with 8.00 unloading (for C18 and C19)
            row_8 = next(
                (l for l in lines
                 if l.cylces == '1st Cycle Unloading' and l.applied_pressure == 8.00),
                None
            )
            # row with 2.00 unloading (for D21)
            row_2 = next(
                (l for l in lines
                 if l.cylces == '1st Cycle Unloading' and l.applied_pressure == 2.00),
                None
            )

            c18 = row_8.final_read if row_8 else 0.0
            if c18 == 0 and row_2:
                # use D21 (ΔH at 2.00 unloading)
                line.delta_h = row_2.delta_h
            elif row_8 and line.final_read not in (False, None):
                # (C19 - C20) / 10
                line.delta_h = (row_8.final_read - line.final_read) / 10.0
            else:
                line.delta_h = 0.0
            continue

        # default rule: (prevC - currC) / 10
        if prev and prev.final_read not in (False, None) and line.final_read not in (False, None):
            line.delta_h = round((prev.final_read - line.final_read) / 10.0 , 3)
        else:
            line.delta_h = 0.0

    @api.depends(
    'delta_h', 'parent_id.consolidation_height',
    'parent_id.consolidation_output_ids.delta_h',
    'parent_id.consolidation_output_ids.applied_pressure',
    'parent_id.consolidation_output_ids.cylces',
    'parent_id.consolidation_output_ids.serial_no'
)
    def _compute_specimen_height(self):
     for line in self:
        parent = line.parent_id
        line.specimen_height = 0.0
        if not parent:
            continue

        lines = list(parent.consolidation_output_ids.sorted('serial_no'))
        if not lines:
            continue

        try:
            idx = lines.index(line)
        except ValueError:
            continue

        # first row: initial specimen height from parent
        if idx == 0:
            line.specimen_height = parent.consolidation_height or 0.0
            continue

        prev_line = lines[idx - 1]

        base_H = prev_line.specimen_height or 0.0
        line.specimen_height = round(base_H - (line.delta_h or 0.0), 3)


    





    @api.depends('specimen_height', 'parent_id.con_height_solid')
    def _compute_e_void(self):
     for line in self:
        Hs = line.parent_id.con_height_solid or 0.0
        if Hs:
            line.e_void = (line.specimen_height / Hs) - 1.0
        else:
            line.e_void = 0.0

    @api.depends('e_void', 'applied_pressure', 'cylces',
             'parent_id.consolidation_output_ids.e_void',
             'parent_id.consolidation_output_ids.applied_pressure',
             'parent_id.consolidation_output_ids.cylces',
             'parent_id.consolidation_output_ids.serial_no')
    def _compute_change_void(self):
     for line in self:
        parent = line.parent_id
        line.change_void = 0.0
        if not parent:
            continue

        lines = list(parent.consolidation_output_ids.sorted('serial_no'))
        if not lines:
            continue

        try:
            idx = lines.index(line)
        except ValueError:
            continue

        prev_line = None

        # one formula for loading block
        if line.cylces == '1st Cycle Loading':
            if idx > 0:
                prev_line = lines[idx - 1]

        # one formula for unloading block
        elif line.cylces == '1st Cycle Unloading':
            if idx > 0:
                prev_line = lines[idx - 1]

        if prev_line:
            line.change_void = (prev_line.e_void or 0.0) - (line.e_void or 0.0)
        else:
            line.change_void = 0.0

    

#     @api.depends(
#     'applied_pressure',
#     'serial_no',
#     'parent_id.consolidation_output_ids.applied_pressure',
#     'parent_id.consolidation_output_ids.serial_no',
# )
#     def _compute_d_sigma(self):
#      for line in self:
#         line.d_sigma = 0.0

#         parent = line.parent_id
#         if not parent or not line.serial_no or line.serial_no == 1:
#             continue

#         # Previous row (Excel previous row)
#         prev = parent.consolidation_output_ids.filtered(
#             lambda l: l.serial_no == line.serial_no - 1
#         )[:1]

#         if prev:
#             line.d_sigma = (line.applied_pressure or 0.0) - (prev.applied_pressure or 0.0)

    @api.depends(
        'applied_pressure',
        'parent_id.consolidation_output_ids.applied_pressure',
        'parent_id.consolidation_output_ids.serial_no',
    )
    def _compute_d_sigma(self):
        for line in self:
            parent = line.parent_id
            line.d_sigma = 0.0
            if not parent:
                continue

            # get all lines for this parent in row order
            lines = list(parent.consolidation_output_ids.sorted('serial_no'))
            if not lines:
                continue

            try:
                idx = lines.index(line)
            except ValueError:
                continue

            # first row (0.05 loading) → 0
            if idx == 0:
                line.d_sigma = 0.0
                continue

            # all other rows: Bi − B(i−1)
            prev = lines[idx - 1]
            line.d_sigma = (line.applied_pressure or 0.0) - (prev.applied_pressure or 0.0)







    @api.depends('change_void', 'd_sigma')
    def _compute_av(self):
     for line in self:
        de = line.change_void or 0.0
        ds = line.d_sigma or 0.0
        if ds:
            line.av = round((de / ds),6)
        else:
            line.av = 0.0


    @api.depends('av', 'parent_id.con_swell_void_ratio')
    def _compute_mv(self):
        for line in self:
            e0 = line.parent_id.con_swell_void_ratio or 0.0
            denom = 1.0 + e0
            if denom:
                line.mv = line.av / denom
            else:
                line.mv = 0.0

    Hav = fields.Float("Hav (cm)", digits=(8, 4), compute="_compute_Hav", store=True)

    @api.depends(
    'specimen_height',
    'parent_id.consolidation_output_ids.specimen_height',
    'parent_id.consolidation_output_ids.serial_no',)
    def _compute_Hav(self):
     for line in self:
        parent = line.parent_id
        line.Hav = 0.0
        if not parent:
            continue

        lines = list(parent.consolidation_output_ids.sorted('serial_no'))
        if not lines:
            continue

        try:
            idx = lines.index(line)
        except ValueError:
            continue

        if idx == 0:
            # first row: Hav = H (same as Excel row 15)
            line.Hav = line.specimen_height or 0.0
        else:
            prev = lines[idx - 1]
            h1 = prev.specimen_height or 0.0
            h2 = line.specimen_height or 0.0
            line.Hav = (h1 + h2) / 2.0

   

    # @api.depends('Hav', 't90')
    # def _compute_cv(self):
    #  for line in self:
    #     # existing mv logic can stay here too, if any

    #     H_av = line.Hav or 0.0
    #     t_90 = line.t90 or 0.0

    #     if H_av and t_90:
    #         # 0.848 * (Hav/2)^2 / (t90 * 60)
    #         line.cv = 0.848 * (H_av / 2.0) ** 2 / (t_90 * 60.0)
    #     else:
    #         line.cv = 0.0

    @api.depends('Hav', 't90')
    def _compute_cv(self):
     for line in self:
        H_av = line.Hav or 0.0
        t_90 = line.t90 or 0.0

        if H_av != 0.0 and t_90 > 0.0:
            line.cv = 0.848 * (H_av / 2.0) ** 2 / (t_90 * 60.0)
        else:
            line.cv = 0.0

    @api.depends(
    'change_void',
    'applied_pressure',
    'parent_id.consolidation_output_ids.applied_pressure',
    'parent_id.consolidation_output_ids.serial_no',
)
    def _compute_cc(self):
     for line in self:
        de = line.change_void or 0.0
        p2 = line.applied_pressure or 0.0

        # previous line in same parent (by serial_no)
        p1 = 0.0
        if line.parent_id:
            prev = line.parent_id.consolidation_output_ids \
                .filtered(lambda l: l.serial_no == line.serial_no - 1)[:1]
            if prev:
                p1 = prev.applied_pressure or 0.0

        if de and p2 and p1 and p2 != p1:
            line.cc = de / log10(p2 / p1)
        else:
            line.cc = 0.0

    ce = fields.Float(related='parent_id.ce', readonly=True)
    cr = fields.Float(related='parent_id.cr', readonly=True)

    
    








    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ConsolidationBothCycleLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1





class SwellingPressureLoadingLine(models.Model):
    _name = "swelling.pressure.loading.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    time_m = fields.Float(string="Time (Minutes)")
    sqrt_time = fields.Float(string="SQRT (t) min", compute="_compute_sqrt_time", store=True)
    load_0_05_0_1 = fields.Float(string="0.05-0.1 kg/cm²",digits=(8,3))
    load_0_1_0_2 = fields.Float(string="0.1-0.2 kg/cm²" ,digits=(8,3))
    load_0_2_0_5 = fields.Float(string="0.2-0.5 kg/cm²" ,digits=(8,3))
    load_0_5_1_0 = fields.Float(string="0.5-1.0 kg/cm²" ,digits=(8,3))
    load_1_0_2_0 = fields.Float(string="1.0-2.0 kg/cm²" ,digits=(8,3))
    load_2_0_4_0 = fields.Float(string="2.0-4.0 kg/cm²" ,digits=(8,3))
    load_4_0_8_0 = fields.Float(string="4.0-8.0 " ,digits=(8,3))

    @api.depends("time_m")
    def _compute_sqrt_time(self):
        for rec in self:
            if rec.time_m:
                rec.sqrt_time = rec.time_m ** 0.5
            else:
                rec.sqrt_time =  0.0


   

    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SwellingPressureLoadingLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class SwellingPressureUnloadingLine(models.Model):
    _name = "swelling.pressure.unloading.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    time_m = fields.Float(string="Time (Minutes)")
    load_8_0_4_0 = fields.Float(string="8.0-4.0" ,digits=(8,3))
    load_4_0_8_0 = fields.Float(string="4.0-8.0" ,digits=(8,3))
    load_2_0_4_0 = fields.Float(string="2.0-4.0" ,digits=(8,3))
    load_1_0_2_0 = fields.Float(string="1.0-2.0" ,digits=(8,3))
    load_0_5_1_0 = fields.Float(string="0.5-1.0" ,digits=(8,3))
    load_0_2_0_5 = fields.Float(string="0.2-0.5" ,digits=(8,3))
    load_0_1_0_2 = fields.Float(string="0.1-0.2" ,digits=(8,3))
    # load_0_05_0_1 = fields.Float(string="0.05-0.1",digits=(8,3))
    setting_load = fields.Float(string="Setting Load",digits=(8,3))


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SwellingPressureUnloadingLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class SwellingPressureBothCycleLine(models.Model):
    _name = "swelling.pressure.both.cycle.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    cylces=  fields.Char(string="Cycles" )

    applied_pressure = fields.Float(string="Applied Pressure kg/cm²" , digits=(8,2))
    final_read = fields.Float(string="Final Dial Reading mm" ,digits=(8,3),compute="_compute_final_read", store=True)
    delta_h = fields.Float(string=" Δ𝐻 cm" ,digits=(8,3),compute="_compute_delta_h" ,store=True,)
    specimen_height = fields.Float(string="Specimen Height (H) cm" ,digits=(8,3) , compute="_compute_specimen_height",
    store=True,)
    e_void = fields.Float(string="e = (H/Hs)-1" ,digits=(8,3), compute="_compute_e_void", store=True)
    change_void = fields.Float(string="de", digits=(8, 3),
                           compute="_compute_change_void", store=True)
    d_sigma = fields.Float(string=" dσ" ,digits=(8,3), compute="_compute_d_sigma", store=True)
    av = fields.Float(string="aᵥ (cm²/kg)" ,digits=(16,6) ,compute="_compute_av", store=True)
    mv = fields.Float("mᵥ (cm²/kg)", digits=(8, 3), compute="_compute_mv", store=True)

    t90 = fields.Float("t₉₀ (min)", digits=(8, 3))
    Hav = fields.Float("Hav (cm)", digits=(8, 3),compute="_compute_Hav", store=True)

    cv = fields.Float("cᵥ (cm²/sec)", digits=(8, 3), compute="_compute_cv", store=True)
    cc = fields.Float("cᵥ (cm²/sec)", digits=(8, 3), compute="_compute_Cc", store=True)

    @api.depends(
    'applied_pressure', 'cylces',
    'parent_id.swelling_ids.load_0_05_0_1',
    'parent_id.swelling_ids.load_0_1_0_2',
    'parent_id.swelling_ids.load_0_2_0_5',
    'parent_id.swelling_ids.load_0_5_1_0',
    'parent_id.swelling_ids.load_1_0_2_0',
    'parent_id.swelling_ids.load_2_0_4_0',
    'parent_id.swelling_ids.load_4_0_8_0',
    'parent_id.swelling_unloading_ids.load_8_0_4_0',
    'parent_id.swelling_unloading_ids.load_4_0_8_0',
    'parent_id.swelling_unloading_ids.load_2_0_4_0',
    'parent_id.swelling_unloading_ids.load_1_0_2_0',
    'parent_id.swelling_unloading_ids.load_0_5_1_0',
    'parent_id.swelling_unloading_ids.load_0_2_0_5',
    'parent_id.swelling_unloading_ids.load_0_1_0_2',
    # 'parent_id.swelling_unloading_ids.load_0_05_0_1',
)
    def _compute_final_read(self):
     for line in self:
        parent = line.parent_id
        line.final_read = 0.0
        if not parent:
            continue

        # helper to get min safely
        def _min(vals):
            vals = [v for v in vals if v not in (False, None)]
            return min(vals) if vals else 0.0

        # ------------- LOADING -------------
        if line.cylces == '1st Cycle Loading':
            if line.applied_pressure == 0.05:
                # Excel: =Input!D21 (first loading row, 0 min)
                recs = parent.swelling_ids.sorted('time_m')
                line.final_read = recs[0].load_0_05_0_1 if recs else 0.0

            elif line.applied_pressure == 0.10:
                line.final_read = _min(parent.swelling_ids.mapped('load_0_05_0_1'))

            elif line.applied_pressure == 0.20:
                line.final_read = _min(parent.swelling_ids.mapped('load_0_1_0_2'))

            elif line.applied_pressure == 0.40:
                line.final_read = _min(parent.swelling_ids.mapped('load_0_2_0_5'))

            elif line.applied_pressure == 0.80:
                line.final_read = _min(parent.swelling_ids.mapped('load_0_5_1_0'))

            elif line.applied_pressure == 1.60:
                line.final_read = _min(parent.swelling_ids.mapped('load_1_0_2_0'))

            elif line.applied_pressure == 3.20:
                line.final_read = _min(parent.swelling_ids.mapped('load_2_0_4_0'))

            elif line.applied_pressure == 6.40:
                line.final_read = _min(parent.swelling_ids.mapped('load_4_0_8_0'))

        # ------------- UNLOADING -------------
        elif line.cylces == '1st Cycle Unloading':
          if line.applied_pressure == 6.40:
           # C23 = Input!N21 (first row only)
            recs = parent.swelling_unloading_ids.sorted('time_m')
            vals = [recs[0].load_8_0_4_0] if recs else []
          elif line.applied_pressure == 3.20:
           vals = parent.swelling_unloading_ids.mapped('load_8_0_4_0')
          elif line.applied_pressure == 1.60:
           vals = parent.swelling_unloading_ids.mapped('load_4_0_8_0')
          elif line.applied_pressure == 0.80:
           vals = parent.swelling_unloading_ids.mapped('load_2_0_4_0')
          elif line.applied_pressure == 0.40:
           vals = parent.swelling_unloading_ids.mapped('load_1_0_2_0')
          elif line.applied_pressure == 0.20:
           vals = parent.swelling_unloading_ids.mapped('load_0_5_1_0')
          elif line.applied_pressure == 0.10:
           vals = parent.swelling_unloading_ids.mapped('load_0_2_0_5')
          elif line.applied_pressure == 0.05:
           vals = parent.swelling_unloading_ids.mapped('load_0_1_0_2')
          else:
           vals = []

          vals = [v for v in vals if v not in (False, None)]
          line.final_read = max(vals) if vals else 0.0

    @api.depends('final_read', 'applied_pressure', 'cylces',
             'parent_id.swelling_output_ids.final_read',
             'parent_id.swelling_output_ids.applied_pressure',
             'parent_id.swelling_output_ids.cylces')
    def _compute_delta_h(self):
     for line in self:
        parent = line.parent_id
        line.delta_h = 0.0
        if not parent:
            continue

        lines = list(parent.swelling_output_ids.sorted('serial_no'))
        if not lines:
            continue

        try:
            idx = lines.index(line)
        except ValueError:
            continue

        prev = None

        # first row → 0.000
        if idx == 0:
            line.delta_h = 0.0
            continue

        # normal rule: previous row with different pressure
        prev = lines[idx - 1]

        # special case: 0.10 unloading (like Excel D29 = (C27-C29)/10)
        if line.cylces == '1st Cycle Unloading' and line.applied_pressure == 0.10:
            prev = next(
                (l for l in lines
                 if l.cylces == '1st Cycle Unloading' and l.applied_pressure == 0.40),
                prev,
            )

        # special case: 0.05 unloading (D30 = (C28-C30)/10, uses 0.20)
        if line.cylces == '1st Cycle Unloading' and line.applied_pressure == 0.05:
            prev = next(
                (l for l in lines
                 if l.cylces == '1st Cycle Unloading' and l.applied_pressure == 0.20),
                prev,
            )

        if prev and prev.final_read is not False and line.final_read is not False:
            line.delta_h = (prev.final_read - line.final_read) / 10.0
        else:
            line.delta_h = 0.0

    

    @api.depends('delta_h', 'parent_id.swelling_height',
             'parent_id.swelling_output_ids.delta_h',
             'parent_id.swelling_output_ids.applied_pressure',
             'parent_id.swelling_output_ids.cylces')
    def _compute_specimen_height(self):
     for line in self:
        parent = line.parent_id
        line.specimen_height = 0.0
        if not parent:
            continue

        lines = list(parent.swelling_output_ids.sorted('serial_no'))
        if not lines:
            continue

        try:
            idx = lines.index(line)
        except ValueError:
            continue

        # first row: initial specimen height
        if idx == 0:
            line.specimen_height = parent.swelling_height or 0.0
            continue

        prev_line = None

        # special case: 0.10 unloading  (E29 = E27 - D29)
        if line.cylces == '1st Cycle Unloading' and line.applied_pressure == 0.10:
            prev_line = next(
                (l for l in lines
                 if l.cylces == '1st Cycle Unloading' and l.applied_pressure == 0.40),
                None
            )

        # special case: 0.05 unloading  (E30 = E28 - D30)
        elif line.cylces == '1st Cycle Unloading' and line.applied_pressure == 0.05:
            prev_line = next(
                (l for l in lines
                 if l.cylces == '1st Cycle Unloading' and l.applied_pressure == 0.20),
                None
            )

        # normal case: previous row in sheet
        if not prev_line:
            prev_line = lines[idx - 1]

        base_H = prev_line.specimen_height or 0.0
        line.specimen_height = base_H - (line.delta_h or 0.0)


    

    @api.depends('specimen_height', 'parent_id.height_solid')
    def _compute_e_void(self):
     for line in self:
        Hs = line.parent_id.height_solid or 0.0
        if Hs:
            line.e_void = (line.specimen_height / Hs) - 1.0
        else:
            line.e_void = 0.0

    

   

    @api.depends(
    'e_void', 'applied_pressure', 'cylces',
    'parent_id.swelling_output_ids.e_void',
    'parent_id.swelling_output_ids.applied_pressure',
    'parent_id.swelling_output_ids.cylces'
)
    def _compute_change_void(self):
     for line in self:
        parent = line.parent_id
        line.change_void = 0.0
        if not parent:
            continue

        rs = parent.swelling_output_ids.sorted('serial_no')
        lines = list(rs)  # convert to plain Python list
        if not lines:
            continue

        try:
            idx = lines.index(line)
        except ValueError:
            continue

        prev_line = None

        # special: 0.10 unloading -> G29 = F27 - F29
        if line.cylces == '1st Cycle Unloading' and line.applied_pressure == 0.10:
            prev_line = next(
                (l for l in lines
                 if l.cylces == '1st Cycle Unloading' and l.applied_pressure == 0.40),
                None,
            )

        # special: 0.05 unloading -> G30 = F28 - F30
        elif line.cylces == '1st Cycle Unloading' and line.applied_pressure == 0.05:
            prev_line = next(
                (l for l in lines
                 if l.cylces == '1st Cycle Unloading' and l.applied_pressure == 0.20),
                None,
            )

        # normal case: immediate previous row
        else:
            if idx > 0:
                prev_line = lines[idx - 1]

        if prev_line:
            line.change_void = (prev_line.e_void or 0.0) - (line.e_void or 0.0)
        else:
            line.change_void = 0.0



    

    @api.depends(
    'applied_pressure', 'cylces',
    'parent_id.swelling_output_ids.applied_pressure',
    'parent_id.swelling_output_ids.cylces'
)
    def _compute_d_sigma(self):
     for line in self:
        parent = line.parent_id
        line.d_sigma = 0.0
        if not parent:
            continue

        lines = list(parent.swelling_output_ids.sorted('serial_no'))
        if not lines:
            continue

        try:
            idx = lines.index(line)
        except ValueError:
            continue

        prev = None

        # ---------- LOADING ----------
        if line.cylces == '1st Cycle Loading':
            # default: previous loading row
            if idx > 0:
                prev = lines[idx - 1]

            # special: 3.20 loading (H21 = B21-B19, previous = 0.80)
            if line.applied_pressure == 3.20:
                prev_080 = next(
                    (l for l in lines
                     if l.cylces == '1st Cycle Loading' and l.applied_pressure == 0.80),
                    None
                )
                if prev_080:
                    prev = prev_080

        # ---------- UNLOADING ----------
        elif line.cylces == '1st Cycle Unloading':
            # default: previous unloading row
            if idx > 0:
                prev = lines[idx - 1]

            # both last unloading rows subtract from 0.20 unloading
            if line.applied_pressure in (0.10, 0.05):
                prev_020 = next(
                    (l for l in lines
                     if l.cylces == '1st Cycle Unloading' and l.applied_pressure == 0.20),
                    None
                )
                if prev_020:
                    prev = prev_020

        # ---------- set value ----------
        if prev:
            line.d_sigma = (line.applied_pressure or 0.0) - (prev.applied_pressure or 0.0)
        else:
            line.d_sigma = 0.0


    @api.depends('change_void', 'd_sigma')
    def _compute_av(self):
     for line in self:
        de = line.change_void or 0.0
        ds = line.d_sigma or 0.0
        if ds:
            line.av = de / ds
        else:
            line.av = 0.0


    @api.depends('av', 'parent_id.swell_void_ratio')
    def _compute_mv(self):
        for line in self:
            e0 = line.parent_id.swell_void_ratio or 0.0
            denom = 1.0 + e0
            if denom:
                line.mv = line.av / denom
            else:
                line.mv = 0.0

    Hav = fields.Float("Hav (cm)", digits=(8, 4), compute="_compute_Hav", store=True)

    @api.depends(
    'specimen_height',
    'parent_id.swelling_output_ids.specimen_height',
    'parent_id.swelling_output_ids.serial_no',)
    def _compute_Hav(self):
     for line in self:
        parent = line.parent_id
        line.Hav = 0.0
        if not parent:
            continue

        lines = list(parent.swelling_output_ids.sorted('serial_no'))
        if not lines:
            continue

        try:
            idx = lines.index(line)
        except ValueError:
            continue

        if idx == 0:
            # first row: Hav = H (same as Excel row 15)
            line.Hav = line.specimen_height or 0.0
        else:
            prev = lines[idx - 1]
            h1 = prev.specimen_height or 0.0
            h2 = line.specimen_height or 0.0
            line.Hav = (h1 + h2) / 2.0

   

    @api.depends('Hav', 't90')
    def _compute_cv(self):
     for line in self:
        # existing mv logic can stay here too, if any

        H_av = line.Hav or 0.0
        t_90 = line.t90 or 0.0

        if H_av and t_90:
            # 0.848 * (Hav/2)^2 / (t90 * 60)
            line.cv = 0.848 * (H_av / 2.0) ** 2 / (t_90 * 60.0)
        else:
            line.cv = 0.0

    

    @api.depends(
    'change_void', 'applied_pressure', 'cylces',
    'parent_id.swelling_output_ids.change_void',
    'parent_id.swelling_output_ids.applied_pressure',
    'parent_id.swelling_output_ids.cylces',
    'parent_id.swelling_output_ids.serial_no',)
    def _compute_Cc(self):
     for line in self:
        line.cc = 0.0
        parent = line.parent_id
        if not parent:
            continue

        rows = list(parent.swelling_output_ids.sorted('serial_no'))
        if not rows:
            continue

        # find row by cycle + pressure with tolerance
        def _find(cycle, pressure):
            for r in rows:
                if (
                    r.cylces == cycle
                    and r.applied_pressure is not None
                    and abs(r.applied_pressure - pressure) < 1e-6
                ):
                    return r
            return None

        pair = None

        # Loading rows: N17, N18, N19, N20, N21
        if line.cylces == "1st Cycle Loading":
            p = line.applied_pressure or 0.0

            # N17 = G17 / LOG10(B17/B16)  -> 0.20 vs 0.10
            if abs(p - 0.20) < 1e-6:
                pair = _find("1st Cycle Loading", 0.10)

            # N18 = G18 / LOG10(B18/B17)  -> 0.40 vs 0.20
            elif abs(p - 0.40) < 1e-6:
                pair = _find("1st Cycle Loading", 0.20)

            # N19 = G19 / LOG10(B19/B18)  -> 0.80 vs 0.40
            elif abs(p - 0.80) < 1e-6:
                pair = _find("1st Cycle Loading", 0.40)

            # N20 = G20 / LOG10(B20/B19)  -> 1.60 vs 0.80
            elif abs(p - 1.60) < 1e-6:
                pair = _find("1st Cycle Loading", 0.80)

            # N21 = G21 / LOG10(B21/B19)  -> 3.20 vs 0.80
            elif abs(p - 3.20) < 1e-6:
                pair = _find("1st Cycle Loading", 0.80)

        # Unloading rows: N24, N25, N26, N27, N28, N29, N30
        elif line.cylces == "1st Cycle Unloading":
            p = line.applied_pressure or 0.0

            # N24 = G24 / LOG10(B24/B23)  -> 3.20 vs 6.40
            if abs(p - 3.20) < 1e-6:
                pair = _find("1st Cycle Unloading", 6.40)

            # N25 = G25 / LOG10(B25/B24)  -> 1.60 vs 3.20
            elif abs(p - 1.60) < 1e-6:
                pair = _find("1st Cycle Unloading", 3.20)

            # N26 = G26 / LOG10(B26/B25)  -> 0.80 vs 1.60
            elif abs(p - 0.80) < 1e-6:
                pair = _find("1st Cycle Unloading", 1.60)

            # N27 = G27 / LOG10(B27/B26)  -> 0.40 vs 0.80
            elif abs(p - 0.40) < 1e-6:
                pair = _find("1st Cycle Unloading", 0.80)

            # N28 = G28 / LOG10(B28/B27)  -> 0.20 vs 0.40
            elif abs(p - 0.20) < 1e-6:
                pair = _find("1st Cycle Unloading", 0.40)

            # N29 = G29 / LOG10(B29/B27)  -> 0.10 vs 0.40
            elif abs(p - 0.10) < 1e-6:
                pair = _find("1st Cycle Unloading", 0.40)

            # N30 = G30 / LOG10(B30/B28)  -> 0.05 vs 0.20
            elif abs(p - 0.05) < 1e-6:
                pair = _find("1st Cycle Unloading", 0.20)

        # compute 6.cc if pair found
        if pair and line.applied_pressure and pair.applied_pressure:
            de = line.change_void or 0.0
            ratio = (line.applied_pressure or 0.0) / (pair.applied_pressure or 1.0)
            if de and ratio > 0:
                line.cc = de / math.log10(ratio)
            else:
                line.cc = 0.0
        else:
            line.cc = 0.0

  



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SwellingPressureBothCycleLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class SwellingPressureGraphLine(models.Model):
    _name = "swelling.pressure.graph.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    cylces=  fields.Char(string="Cycles" )

    applied_pressure = fields.Float(string="Applied Pressure kg/cm²" , digits=(8,2))
    final_read = fields.Float(string="Final Dial Reading mm" ,digits=(8,3),compute="_compute_final_read", store=True)
    delta_h = fields.Float(string=" Δ𝐻 cm" ,digits=(8,3),compute="_compute_delta_h" ,store=True)

    @api.depends('applied_pressure', 'parent_id.swelling_ids')
    def _compute_final_read(self):
        for line in self:
            final = 0.0
            if line.parent_id and line.applied_pressure:
                # map pressure to column name
                field_map = {
                    0.10: 'load_0_05_0_1',
                    0.20: 'load_0_1_0_2',
                    0.50: 'load_0_2_0_5',
                    1.00: 'load_0_5_1_0',
                    2.00: 'load_1_0_2_0',
                    4.00: 'load_2_0_4_0',  # or load_4_0_8_0 depending on your design
                }
                field = field_map.get(round(line.applied_pressure, 2))
                if field:
                    # last non-zero reading for that pressure
                    records = line.parent_id.swelling_ids.filtered(lambda r: getattr(r, field))
                    if records:
                        final = records.sorted('time_m')[-1][field]
            line.final_read = final

    @api.depends('final_read', 'parent_id.initial_read')
    def _compute_delta_h(self):
        for line in self:
            if line.final_read and line.parent_id.initial_read:
                line.delta_h = line.final_read - line.parent_id.initial_read
            else:
                line.delta_h = 0.0


    



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SwellingPressureGraphLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class SoilPermeabilityTestLine(models.Model):
    _name = "soil.permeability.test.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="Trial No",readonly=True, copy=False, default=1)

    

    initial_head = fields.Float(string="Initial Head (cm) (H1)" , digits=(8,0))
    final_head = fields.Float(string="Final Head (cm) (H2)" , digits=(8,0))
    initial_head1 = fields.Float(string="Initial Head (cm) (H1)" , digits=(8,0) ,compute="_compute_heads" ,store=True)
    final_head2 = fields.Float(string="Final Head (cm) (H2)" , digits=(8,0) , compute="_compute_heads" ,store=True)
    time = fields.Float(string="Time (sec)", digits=(12,2))
    permeability = fields.Float("Permeability (cm/s)",compute="_compute_permeability", digits=(16, 9), store=True)
    

    @api.depends('initial_head','final_head','parent_id.distance')
    def _compute_heads(self):
        for line in self:
            if line.initial_head and line.final_head and line.parent_id.distance :    
                line.initial_head1 =  line.initial_head + line.parent_id.distance
                line.final_head2 =  line.final_head +  line.parent_id.distance

    @api.depends('parent_id.area_pipe', 'parent_id.area_soil_samp',
             'parent_id.length_soil', 'time', 'initial_head1', 'final_head2')
    def _compute_permeability(self):
     for line in self:
        p = line.parent_id
        if p.area_pipe and p.area_soil_samp and p.length_soil and line.time and line.initial_head1 and line.final_head2:
            num = p.area_pipe * p.length_soil
            den = p.area_soil_samp * line.time
            ln_term = math.log(line.initial_head1 / line.final_head2)
            line.permeability = (num / den) * ln_term
        else:
            line.permeability = 0.0




    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SoilPermeabilityTestLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




    











    


















