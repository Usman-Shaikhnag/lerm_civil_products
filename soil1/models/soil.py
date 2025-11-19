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

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id


    

    # Sieve Analysis
    sieve_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")
 
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
    cc = fields.Float(string="Cc = D30^2/D10* D60",compute="_compute_cc",digits=(12,4))


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
    def _compute_cc(self):
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


     # Water Content
    water_content_name = fields.Char("Name",default="Water Content")
    water_content_visible = fields.Boolean("Water Content Visible",compute="_compute_visible")
   
    water_content_table = fields.One2many('mechanical.water.content.line1','parent_id',string="Parameter")

    water_content = fields.Float(string="Water Content % ",compute="_compute_water_content")
   
    @api.depends('water_content_table.water_content_pastic')
    def _compute_water_content(self):
        for record in self:
            total_water_content_pastic = sum(record.water_content_table.mapped('water_content_pastic'))
            record.water_content = total_water_content_pastic / len(record.water_content_table) if record.water_content_table else 0.0
   

    water_content_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string=" Conformity", compute="_compute_water_content_conformity", store=True)

    @api.depends('water_content','eln_ref','grade')
    def _compute_water_content_conformity(self):
        
        for record in self:
            record.water_content_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','120vbf14-2ff0-4b81-aca1-365ghtyr78ww')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','120vbf14-2ff0-4b81-aca1-365ghtyr78ww')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.water_content - record.water_content*mu_value
                    upper = record.water_content + record.water_content*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.water_content_conformity = 'pass'
                        break
                    else:
                        record.water_content_conformity = 'fail'

    water_content_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_water_content_nabl", store=True)

    @api.depends('water_content','eln_ref','grade')
    def _compute_water_content_nabl(self):
        
        for record in self:
            record.water_content_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','120vbf14-2ff0-4b81-aca1-365ghtyr78ww')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','120vbf14-2ff0-4b81-aca1-365ghtyr78ww')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.water_content - record.water_content*mu_value
            upper = record.water_content + record.water_content*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.water_content_nabl = 'pass'
                break
            else:
                record.water_content_nabl = 'fail'


   

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





    # def generate_line_chart_light_omc(self):
    #     x_value = []
    #     y_value = []
    #     for line in self.heavy_table:
    #         if line.water_content and line.dry_density:
    #             x_value.append(line.water_content)
    #             y_value.append(line.dry_density)

    #     if not x_value or not y_value:
    #         return False

    #     x = np.array(x_value)
    #     y = np.array(y_value)

    #     # Sort data
    #     sorted_indices = np.argsort(x)
    #     x = x[sorted_indices]
    #     y = y[sorted_indices]

    #     # Gentle smooth curve (quadratic)
    #     x_smooth = np.linspace(x.min(), x.max(), 200)
    #     spline = make_interp_spline(x, y, k=2)
    #     y_smooth = spline(x_smooth)

    #     # Find smooth curve peak (OMC/MDD from smooth curve)
    #     smooth_max_index = np.argmax(y_smooth)
    #     smooth_max_x = x_smooth[smooth_max_index]
    #     smooth_max_y = y_smooth[smooth_max_index]

    #     # ✅ Trim curve so it never goes above MDD
    #     y_smooth = np.minimum(y_smooth, smooth_max_y)

    #     # Figure size
    #     plt.figure(figsize=(15, 5))

    #     # Plot curve and points
    #     plt.plot(x_smooth, y_smooth, color='blue', linewidth=2, label='Smooth Curve')
    #     plt.scatter(x, y, color='red', edgecolors='black', s=60, zorder=5, label='Data Points')

    #     # Labels and title
    #     plt.xlabel('Water Content (%)', fontsize=12)
    #     plt.ylabel('Dry Density (g/cc)', fontsize=12)
    #     plt.title('DETERMINATION OF COMPACTION OMC / MDD', fontsize=14)

    #     # Extend y-axis
    #     plt.xlim(left=0, right=max(x) + 2)
    #     bottom_margin = min(y) - 0.05
    #     plt.ylim(bottom=bottom_margin, top=smooth_max_y + 0.05)

    #     # Grid
    #     ax = plt.gca()
    #     ax.xaxis.set_minor_locator(MultipleLocator(0.5))
    #     ax.yaxis.set_minor_locator(MultipleLocator(0.005))
    #     plt.grid(True, which='both', linestyle='--', linewidth=0.3, color='gray', alpha=0.8)

    #     # ✅ Highlight OMC/MDD from smooth curve (shifted peak)
    #     plt.axhline(y=smooth_max_y, color='red', linestyle='--', linewidth=1)
    #     plt.axvline(x=smooth_max_x, color='red', linestyle='--', linewidth=1)
    #     plt.plot(smooth_max_x, smooth_max_y, marker='o', color='red', markersize=8)
    #     plt.text(smooth_max_x + 0.3, smooth_max_y + 0.005,
    #             f"OMC: {smooth_max_x:.2f}%\nMDD: {smooth_max_y:.2f}",
    #             color='red')

    #     # Final touches
    #     plt.tight_layout()
    #     plt.legend()

    #     # Save to base64
    #     buffer = io.BytesIO()
    #     plt.savefig(buffer, format='png')
    #     plt.close()
    #     buffer.seek(0)
    #     return base64.b64encode(buffer.read()).decode('utf-8')


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
   
    soil_table = fields.One2many('mechanical.cbr.line1','parent_id',string="CBR",default=lambda self: self._default_cbr_child_lines())
    # chart_image_cbr = fields.Binary("Line Chart", compute="_compute_chart_image_cbr", store=True)

    @api.model
    def _default_cbr_child_lines(self):
        default_liness = [
            (0, 0, {'penetration': '0.00'}),
            (0, 0, {'penetration': '0.50 '}),
            (0, 0, {'penetration': '1.00'}),
            (0, 0, {'penetration': '1.50'}),
            (0, 0, {'penetration': '2.00'}),
            (0, 0, {'penetration': '2.50'}),
            (0, 0, {'penetration': ' 3.00'}),
            (0, 0, {'penetration': '4.00'}),
            (0, 0, {'penetration': '5.00'}),
            (0, 0, {'penetration': '7.50'}),
            (0, 0, {'penetration': '10.00'}),
            (0, 0, {'penetration': '12.50'}),
          
        ]
        return default_liness

    ps_2mm = fields.Float("PS for 2.5mm",compute="_compute_ps_2mm")
    pt_2mm = fields.Float("PT at 2.5mm",default=1370)
    cbr_2mm = fields.Float("CBR at 2.5mm",compute="_compute_cbr_2mm")

    ps_5mm = fields.Float("PS for 5mm",compute="_compute_ps_5mm")
    pt_5mm = fields.Float("PT at 5mm",default=2055)
    cbr_5mm = fields.Float("CBR at 5mm",compute="_compute_cbr_5mm")

    cbr_result = fields.Float("CBR",compute="_compute_final_cbr")

    @api.depends('soil_table')
    def _compute_ps_2mm(self):
        for record in self:
            if record.soil_table and len(record.soil_table) >= 6:
                fifth_row = record.soil_table[5] 
                record.ps_2mm = fifth_row.load
            else:
                record.ps_2mm = 0


    @api.depends('soil_table')
    def _compute_ps_5mm(self):
        for record in self:
            if record.soil_table and len(record.soil_table) >= 9:
                fifth_row = record.soil_table[8] 
                record.ps_5mm = fifth_row.load
            else:
                record.ps_5mm = 0

    @api.depends('pt_2mm','ps_2mm')
    def _compute_cbr_2mm(self):
        for record in self:
            if record.pt_2mm != 0:
                record.cbr_2mm = round((record.ps_2mm/record.pt_2mm)*100,2)
            else:
                record.cbr_2mm = 0

    @api.depends('pt_5mm','ps_5mm')
    def _compute_cbr_5mm(self):
        for record in self:
            if record.pt_5mm != 0:
                record.cbr_5mm = round((record.ps_5mm/record.pt_5mm)*100,2)
            else:
                record.cbr_5mm = 0

    @api.depends('cbr_5mm','cbr_2mm')
    def _compute_final_cbr(self):
        for record in self:
            if record.cbr_5mm > record.cbr_2mm:
                record.cbr_result = record.cbr_5mm
            else:
                record.cbr_result = record.cbr_2mm


   

    chart_image_cbr = fields.Binary(
    "Line Chart",
    compute="_compute_chart_image_cbr",
    store=True
      )

    def generate_line_chart_cbr(self):
        # Prepare data
        x_values = []
        y_values = []
        for line in self.soil_table:
            x_values.append(line.penetration)
            y_values.append(line.load)

        if not x_values or not y_values:
            return False

        plt.figure(figsize=(10, 5))

        # ✅ Blue curve with red points
        plt.plot(x_values, y_values, color='blue', linestyle='-', linewidth=2, label='Curve')
        plt.scatter(x_values, y_values, color='red', edgecolors='black', s=60, zorder=5, label='Points')

        # ✅ Axis labels and title
        plt.xlabel('Penetration (mm)', fontsize=12)
        plt.ylabel('Load (kg)', fontsize=12)
        plt.title('CBR (California Bearing Ratio)', fontsize=14)

        # ✅ Axis range
        plt.xlim(left=0, right=max(x_values) + 2)
        plt.ylim(bottom=0, top=max(y_values) + (max(y_values) * 0.1))

        # ✅ Grid (major + minor)
        ax = plt.gca()
        ax.xaxis.set_minor_locator(MultipleLocator(0.5))
        ax.yaxis.set_minor_locator(MultipleLocator(5))
        plt.grid(True, which='both', linestyle='--', linewidth=0.3, color='gray', alpha=0.8)

        # ✅ Save image
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.legend()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode('utf-8')


    @api.depends('soil_table')
    def _compute_chart_image_cbr(self):
        try:
            for record in self:
                chart_image = record.generate_line_chart_cbr()
                record.chart_image_cbr = chart_image
        except:
            pass





       # FSI
    fsi_name = fields.Char("Name",default="Free Swell Index")
    fsi_visible = fields.Boolean("Free Swell Index Visible",compute="_compute_visible")
  
    wt_sample = fields.Float(string="Volume in Water - Vd ")
    valume_water = fields.Float(string=" Volume in Kerosene - Vk ")
    valime_kerosen = fields.Float(string="Swell (Vd - Vk) ")

    fsi1 = fields.Float(string="Swell Index = (Vd - Vk) / Vk X 100 (%) ",compute="_compute_swell", store=True,digits=(12,4))

    @api.depends('wt_sample', 'valume_water')
    def _compute_swell(self):
        for rec in self:
            if rec.wt_sample is not None and rec.valume_water not in (None, 0):
                rec.valime_kerosen = rec.wt_sample - rec.valume_water
                rec.fsi1 = (rec.valime_kerosen / rec.valume_water) * 100
            else:
                rec.valime_kerosen = 0
                rec.fsi1 = 0

    

    fsi = fields.Float(string="Free Swell Index (%)", compute="_compute_fsi_avg", store=True,digits=(12,4))

    wt_sample1 = fields.Float(string="Volume in Water - Vd")
    valume_water1 = fields.Float(string=" Volume in Kerosene - Vk ")
    valime_kerosen1 = fields.Float(string="Swell (Vd - Vk) ")

    fsi2 = fields.Float(string="Swell Index = (Vd - Vk) / Vk X 100 (%) ", compute="_compute_fsi2", store=True,digits=(12,4))

    @api.depends('wt_sample1', 'valume_water1')
    def _compute_fsi2(self):
        for rec in self:
            if rec.wt_sample1 is not None and rec.valume_water1 not in (None, 0):
                rec.valime_kerosen1 = rec.wt_sample1 - rec.valume_water1
                rec.fsi2 = (rec.valime_kerosen1 / rec.valume_water1) * 100
            else:
                rec.valime_kerosen1 = 0
                rec.fsi2 = 0

    @api.depends('fsi1', 'fsi2')
    def _compute_fsi_avg(self):
        for rec in self:
            values = []
            if rec.fsi1:
                values.append(rec.fsi1)
            if rec.fsi2:
                values.append(rec.fsi2)
            rec.fsi = sum(values) / len(values) if values else 0.0


    # @api.depends('valume_water', 'valime_kerosen')
    # def _compute_fsi(self):
    #     for rec in self:
    #         if rec.valime_kerosen:
    #             rec.fsi = ((rec.valume_water - rec.valime_kerosen) / rec.valime_kerosen) * 100
    #         else:
    #             rec.fsi = 0.0  # Avoid division by zero

    # @api.depends('valume_water', 'valime_kerosen', 'valume_water1', 'valime_kerosen1')
    # def _compute_fsi(self):
    #     for rec in self:
    #         fsi_values = []

    #         # First measurement
    #         if rec.valime_kerosen and rec.valime_kerosen != 0:
    #             fsi_values.append(((rec.valume_water - rec.valime_kerosen) / rec.valime_kerosen) * 100)

    #         # Second measurement
    #         if rec.valime_kerosen1 and rec.valime_kerosen1 != 0:
    #             fsi_values.append(((rec.valume_water1 - rec.valime_kerosen1) / rec.valime_kerosen1) * 100)

    #         if fsi_values:
    #             # ✅ Average of both measurements
    #             rec.fsi = sum(fsi_values) / len(fsi_values)
    #         else:
    #             rec.fsi = 0.0

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

    def fetch_volumes_to_shrinkage(self):
        for rec in self:
            volume_wet = 0.0
            volume_dry = 0.0

            # Get first wet/dry line from self
            wet_line = rec.volume_wet_table[:1] if hasattr(rec, 'volume_wet_table') else None
            dry_line = rec.volume_dry_table[:1] if hasattr(rec, 'volume_dry_table') else None

            if wet_line:
                volume_wet = wet_line.volume_wet
            if dry_line:
                volume_dry = dry_line.volume_dry

            # Check if a shrinkage line already exists
            if rec.shrinkage_limit_table:
                # Update the first line
                line = rec.shrinkage_limit_table[0]
                line.volume_wet_shri = volume_wet
                line.volume_dry_shir = volume_dry
            else:
                # Create a new line
                rec.shrinkage_limit_table = [(0, 0, {
                    'volume_wet_shri': volume_wet,
                    'volume_dry_shir': volume_dry,
                })]

    


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

    
    
   

     ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
      
        for record in self:
            record.sieve_visible = False
            record.liquid_limit_visible = False
            record.plastic_limit_visible = False
            record.water_content_visible = False
            record.heavy_visible = False
            record.omc_visible = False
            record.triaxial_visible = False
            record.internal_fraction_visible = False
            record.soil_visible = False
            record.fsi_visible  = False 
            record.determination_visible  = False 
            record.shrinkage_limit_visible  = False 


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == '12014fgr-5c56-475b-9a89-93a59c9ee3a2':
                    record.sieve_visible = True
                
                if sample.internal_id == '23fg21gh-7202-4d62-864b-8efa58b6b61f':
                    record.liquid_limit_visible = True

                if sample.internal_id == '120vbf14-2ff0-4b81-aca1-0e07dab7cd87':
                    record.plastic_limit_visible = True

                if sample.internal_id == '120vbf14-2ff0-4b81-aca1-365ghtyr78ww':
                    record.water_content_visible = True

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


    # def open_eln_page(self):
    #     # import wdb; wdb.set_trace()

    #     return {
    #             'view_mode': 'form',
    #             'res_model': "lerm.eln",
    #             'type': 'ir.actions.act_window',
    #             'target': 'current',
    #             'res_id': self.eln_ref.id,
                
    #         }
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



class WaterContentLINE(models.Model):
    _name = "mechanical.water.content.line1"
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

        return super(WaterContentLINE, self).create(vals)

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
    proving_reading = fields.Float(string="Load on Piston in KN")
    load = fields.Float(string="Load on Piston in Kg", compute="_compute_load",digits=(12,4))


    @api.depends('proving_reading')
    def _compute_load(self):
        for record in self:
            record.load = record.proving_reading * 101.97

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
    volume_wet_shri = fields.Float(string="Volume of wet soil (V1)",digits=(12,3))
    volume_dry_shir = fields.Float(string="Volume of dry Soil pat (V2)",digits=(12,3))
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