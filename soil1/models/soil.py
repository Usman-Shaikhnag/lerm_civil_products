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
from datetime import date

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
from decimal import Decimal, ROUND_HALF_UP


# Smooth curve साठी या दोन लायब्ररीज लागतात.
# जर त्या नसतील तर कोड एरर न देता साधी लाईन वापरेल.
try:
    import numpy as np
    from scipy.interpolate import make_interp_eline
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

    image = fields.Image(
        string="Image",
        max_width=1024,
        max_height=1024
    )

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=False)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    sample_id = fields.Many2one('lerm.srf.sample',string="Sample")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    notes_id = fields.One2many('soil1.notes','parent_id',string="Notes")
    
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
                'notes': '^ indicates insufficient quantity of processed sample to perform specific test',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'If direct shear test indicates * it represents Consolidated Undrained (CU) test, if ** then it represents Consolidated Drained (CD) test, else it is Unconsolidated Undrained (UU)  test',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'If direct shear test indicates ### it represents Consolidated Undrained (CU) test with corrected area, if ## then it represents Consolidated Drained (CD) test with corrected area, # it represents Unconsolidated Undrained (UU)  test with corrected area',
            }),

            (0, 0, {
                'sr_no': 'e',
                'notes': 'If  CBR value indicate *, it represents Unsoaked CBR  else it is soaked CBR',
            }),

            (0, 0, {
                'sr_no': 'f',
                'notes': 'If Proctor results indicate * it represents Heavy compaction, else it is Light compaction test',
            }),

            (0, 0, {
                'sr_no': 'g',
                'notes': 'If Permeability results indicate *, it represents Constant Head Test, else it is Falling Head test',
            }),

            (0, 0, {
                'sr_no': 'h',
                'notes': 'The results listed refer only to tested parameters and sample as received from customer',
            }),

            (0, 0, {
                'sr_no': 'i',
                'notes': 'The balance samples if any will be discarded  after 15 days from the date of issue of test certificate unless otherwise specified.',
            }),

            (0, 0, {
                'sr_no': 'j',
                'notes': 'This document shall not be reproduced in part or full without the approval of Genstru.',
            }),
        ]

        res['notes_id'] = default_notes
        return res


    lab_id = fields.Char(
            string="Lab ID",
            compute="_compute_lab_id",
            store=True
        )

    lab_option_ids = fields.One2many(
        'lab.option.line', 
        'parent_id', 
        string="Generated Options"
    )

   

    

    # --- Button Function ---
    def action_generate_options(self):
        for record in self:
            # Step 1: Check if lab_id exists and has hyphen
            if record.lab_id and '-' in record.lab_id:
                try:
                    # Step 2: Clear old lines first (Previous options delete kara)
                    # (5, 0, 0) command saglya lines remove karte
                    lines_command = [(5, 0, 0)]
                    
                    # Step 3: String Parsing (Break Logic)
                    # Input: "S-25-144 - S-25-145"
                    parts = record.lab_id.split(' - ')
                    
                    if len(parts) >= 2:
                        start_part = parts[0].strip() # "S-25-144"
                        end_part = parts[-1].strip()  # "S-25-145"

                        # Prefix (S-25) ani Number (144) vegla kara
                        prefix = start_part.rsplit('-', 1)[0]
                        start_num = int(start_part.split('-')[-1])
                        end_num = int(end_part.split('-')[-1])

                        # Step 4: Loop ani Create Lines
                        for num in range(start_num, end_num + 1):
                            val = f"{prefix}-{num}"
                            # One2many madhe create karnya sathi: (0, 0, values)
                            lines_command.append((0, 0, {'name': val}))

                        # Step 5: Assign to One2many field
                        record.lab_option_ids = lines_command
                        
                except Exception as e:
                    # Jar format chukla tar error ignore kara
                    pass
            else:
                # Jar range nasel (single value asel), tar ti ekach value add kara
                if record.lab_id:
                     record.lab_option_ids = [(5, 0, 0), (0, 0, {'name': record.lab_id})]

    
      


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
  

    def prefill_data(self):
        
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
    sieve_visible = fields.Boolean("Sieve Analysis Visible")




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
    





    
    










#  1st table  Bulk Density

    moisture_name = fields.Char( string="Name",default=" Bulk Density" )
    moisture_visible = fields.Boolean(string="Bulk Density Visible",compute="_compute_visible")

    selected_lab_id11 = fields.Many2one(
        'lab.option.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_option_ids)]"
    )


    bulk_line_ids = fields.One2many('soil.bulk.density','parent_id', string="Bulk Density Lines")

    show_sieve = fields.Boolean(default=False)

    bulk_lines_generated = fields.Boolean(string="GSA Lines Generated",default=False)

    start_date = fields.Date(string="Start Date")  # manually fill
    end_date = fields.Date(string="End Date")      # auto fill on submit



    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise ValidationError(
                        "Start Date cannot be greater than End Date."
                    )



    def action_submit(self):
        self.ensure_one()
        
        # Boolean True save
        # self.write({
        #     'end_date': fields.Date.context_today(self),  # current date auto fill
        # })
        
        # Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}

    
    



    @api.constrains('start_date', 'end_date')
    def _check_dates_sg(self):
        for rec in self:

            # 1️⃣ Start Date should not be before SRF Date
            if rec.start_date and rec.eln_ref.srf_date:
                if rec.start_date < rec.eln_ref.srf_date:
                    raise ValidationError(
                        "Start Date cannot be earlier than SRF Date."
                    )

            # 2️⃣ End Date should not be before Start Date
            if rec.start_date and rec.end_date:
                if rec.end_date < rec.start_date:
                    raise ValidationError(
                        "End Date cannot be earlier than Start Date."
                    )
   





    # def action_generate_bulck_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.bulk_line_ids = lines
    #             record.bulk_lines_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.bulk_line_ids:
    #             record.show_sieve = True

    def action_generate_bulck_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case (e.g. ABC-001)
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines
            if lines:
                record.bulk_line_ids = lines
                record.bulk_lines_generated = True
                record.show_sieve = True









   #  Calculation-NMC, 


    NMC_name = fields.Char( string="Name",default=" NMC" )
    moisture_ids = fields.One2many('soil.moisture','parent_id', string="Moisture Tests")
    nmc_visible = fields.Boolean(string="NMC Visible",compute="_compute_visible")
    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")

    start_date_mnc = fields.Date(string="Start Date")  # manually fill
    end_date_mnc = fields.Date(string="End Date")      # auto fill on submit


    @api.constrains('start_date_mnc', 'end_date_mnc')
    def _check_dates_sg(self):
        for rec in self:

            # 1️⃣ Start Date should not be before SRF Date
            if rec.start_date_mnc and rec.eln_ref.srf_date:
                if rec.start_date_mnc < rec.eln_ref.srf_date:
                    raise ValidationError(
                        "Start Date cannot be earlier than SRF Date."
                    )

            # 2️⃣ End Date should not be before Start Date
            if rec.start_date_mnc and rec.end_date_mnc:
                if rec.end_date_mnc < rec.start_date_mnc:
                    raise ValidationError(
                        "End Date cannot be earlier than Start Date."
                    )



   
    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None



    show_sieve = fields.Boolean(default=False)

    nmc_lines_generated = fields.Boolean(string="GSA Lines Generated",default=False)

    def action_generate_nmc_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))  # 1st line
                        lines.append((0, 0, {'lab_id': False}))   # 2nd blank line

                # 🔹 Single lab id case (e.g. ABC-001)
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))  # 1st line
                    lines.append((0, 0, {'lab_id': False}))          # 2nd blank line

            # 🔹 Assign lines
            if lines:
                record.moisture_ids = lines
                record.nmc_lines_generated = True
                record.show_sieve = True

   

    def action_moisture_content_NMC(self):
          for rec in self:
            lines = rec.moisture_ids.sorted('id')

           
            for line in lines:
                line.avg_nmc = 0.0

            i = 0
            while i < len(lines):
                group = lines[i:i+2] 
                values = [l.moisture_content for l in group if l.moisture_content]

                if values:
                    avg = sum(values) / len(values)
                    group[0].avg_nmc = avg  

                i += 2
            # if not rec.end_date_mnc:
            #     rec.write({
            #         'end_date_mnc': fields.Date.context_today(rec)
            #     })





    # specific gravity
    specific_gravity_name = fields.Char(string="Name",default=" SPECIFIC GRAVITY", )
    specific_gravity_visible = fields.Boolean( string="Specific Gravity Visible",default=True )

    start_date_sg = fields.Date(string="Start Date")  # manually fill
    end_date_sg = fields.Date(string="End Date")      # auto fill on submit

    


    
    @api.constrains('start_date_sg', 'end_date_sg')
    def _check_dates_sg(self):
        for rec in self:

            # 1️⃣ Start Date should not be before SRF Date
            if rec.start_date_sg and rec.eln_ref.srf_date:
                if rec.start_date_sg < rec.eln_ref.srf_date:
                    raise ValidationError(
                        "Start Date cannot be earlier than SRF Date."
                    )

            # 2️⃣ End Date should not be before Start Date
            if rec.start_date_sg and rec.end_date_sg:
                if rec.end_date_sg < rec.start_date_sg:
                    raise ValidationError(
                        "End Date cannot be earlier than Start Date."
                    )

    # selected_lab_id12 = fields.Many2one(
    #     'lab.option.line',
    #     string="Select Lab ID",
    #     domain="[('id', 'in', lab_option_ids)]"
    # )

    show_sieve = fields.Boolean(default=False)

    sp_lines_generated = fields.Boolean(string="GSA Lines Generated",default=False)

    # def action_generate_sp_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []

    #             for i in range(start, end + 1):
    #                 lab_no = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_no': lab_no}))   # 1st
    #                 lines.append((0, 0, {'lab_no': False}))    # 2nd blank

    #             record.gravity_line_ids = lines
    #             record.sp_lines_generated = True

    #         if record.gravity_line_ids:
    #             record.show_sieve = True

    def action_generate_sp_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_no = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_no': lab_no}))  # 1st line
                        lines.append((0, 0, {'lab_no': False}))   # 2nd blank line

                # 🔹 Single lab id case
                else:
                    lines.append((0, 0, {'lab_no': record.lab_id}))  # 1st line
                    lines.append((0, 0, {'lab_no': False}))          # 2nd blank line

            # 🔹 Assign lines
            if lines:
                record.gravity_line_ids = lines
                record.sp_lines_generated = True
                record.show_sieve = True

           




    gravity_line_ids = fields.One2many( "specific.gravity", "parent_id",string="Specific Gravity Lines",)

    def action_compute_avg_corr_gravity(self):
        for rec in self:
            lines = rec.gravity_line_ids.sorted('id')

           
            for line in lines:
                line.avg_corr_specific_gravity = 0.0

            i = 0
            while i < len(lines):
                group = lines[i:i+2] 
                values = [l.corr_specific_gravity for l in group if l.corr_specific_gravity]

                if values:
                    avg = sum(values) / len(values)
                    group[0].avg_corr_specific_gravity = avg  

                i += 2
            # if not rec.end_date_sg:
            #     rec.write({
            #         'end_date_sg': fields.Date.context_today(rec)
            #     })











# Atterbergs Limits (Free Swell)


    freeswell_name = fields.Char(string="Name", default= "Free Swell Index")
    freeswell_visible = fields.Boolean(string="Free Swell Visible", default=True)
    freeswell_line_ids = fields.One2many('soil.free.swell', 'parent_id', string="Free Swell Lines")

    show_sieve = fields.Boolean(default=False)

    freeswell_lines_generated = fields.Boolean(string="GSA Lines Generated",default=False)

   


    # def action_generate_freeswell_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.freeswell_line_ids = lines
    #             record.freeswell_lines_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.freeswell_line_ids:
    #             record.show_sieve = True
    def action_generate_freeswell_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines
            if lines:
                record.freeswell_line_ids = lines
                record.freeswell_lines_generated = True
                record.show_sieve = True

          
    
    # ATTERBERG LIMITS
    Atterbergs_name = fields.Char(string="Name", default="Atterbergs Limits (LL, PL, SL)")

    Atterbergs_name_ll = fields.Char(string="Name", default="Liquid Limits")

    ll_child_lines = fields.One2many('ll.line','parent_id')

    show_sieve = fields.Boolean(default=False)

    ll_lines_generated = fields.Boolean(string="GSA Lines Generated",default=False)

    # def action_generate_ll_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.ll_child_lines = lines
    #             record.ll_lines_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.ll_child_lines:
    #             record.show_sieve = True

    def action_generate_ll_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines
            if lines:
                record.ll_child_lines = lines
                record.ll_lines_generated = True
                record.show_sieve = True

          

    Atterbergs_name_pl = fields.Char(string="Name", default="Plastic Limits")

    pl_child_lines = fields.One2many('pl.line','parent_id')

    show_sieve = fields.Boolean(default=False)

    pl_lines_generated = fields.Boolean(string="Lab ID Show",default=False)

    # def action_generate_pl_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.pl_child_lines = lines
    #             record.pl_lines_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.pl_child_lines:
    #             record.show_sieve = True

    def action_generate_pl_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines
            if lines:
                record.pl_child_lines = lines
                record.pl_lines_generated = True
                record.show_sieve = True

           
    
    Atterbergs_name_sl = fields.Char(string="Name", default="Shrinkage Limits")

    sl_child_lines = fields.One2many('sl.line','parent_id')

    show_sieve = fields.Boolean(default=False)

    sl_lines_generated = fields.Boolean(string="Lab ID Show",default=False)

    # def action_generate_sl_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.sl_child_lines = lines
    #             record.sl_lines_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.sl_child_lines:
    #             record.show_sieve = True

    def action_generate_sl_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines
            if lines:
                record.sl_child_lines = lines
                record.sl_lines_generated = True
                record.show_sieve = True

            


    Atterbergs_visible = fields.Boolean('Show Atterberg', default=True)
    pl_visible = fields.Boolean('Show PL', default=True)
    ll_visible = fields.Boolean('Show LL', default=True)
    sl_visible = fields.Boolean('Show SL', default=True)
    
    
    # RESULTS
    moisture_content = fields.Float('NMC (%)', digits=(10,2))
    plastic_limit = fields.Float('PL (%)', digits=(10,2))
    liquid_limit = fields.Float('LL (%)', digits=(10,2))
    shrinkage_limit = fields.Float('SL (%)', digits=(10,2))
    plasticity_index = fields.Float('PI', digits=(10,2))
    
  
    pl_line_ids = fields.One2many('lab.atterberg.pl.line', 'parent_id_ll',ondelete='cascade')
    
    sl_line_ids = fields.One2many('lab.atterberg.sl.line', 'parent_id_sl',ondelete='cascade')

    ll_line_ids = fields.One2many('lab.atterberg.ll.line', 'parent_id')





    # === CASAGRANDE GRAPH FIELD ===
    casagrande_graph = fields.Binary("Casagrande Graph", compute="_compute_casagrande_graph", store=True)
    
    @api.depends('ll_line_ids.blows', 'll_line_ids.water_content', 'll_line_ids.m1', 'll_line_ids.m2', 'll_line_ids.m3')
    def _compute_casagrande_graph(self):
        for record in self:
            try:
                if record.ll_line_ids:
                    graph = record.generate_casagrande_graph()
                    record.casagrande_graph = graph
            except:
                record.casagrande_graph = False

    def generate_casagrande_graph(self):
        """Casagrande graph - NO LOGGING, FULLY SAFE"""
        self.ensure_one()
        
        # Filter VALID data only
        lines = self.ll_line_ids.filtered(lambda l: l.blows and l.blows >= 10 and l.water_content and l.water_content > 0)
        if len(lines) < 2:
            return False
        
        try:
            x_data = np.array([float(line.blows) for line in lines])
            y_data = np.array([float(line.water_content) for line in lines])
            
            # Linear regression
            slope, intercept, _, _, _ = stats.linregress(x_data, y_data)
            ll_25 = slope * 25 + intercept
            
            # Create figure
            fig = plt.figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            
            # Grid
            ax.grid(True, which='both', color='lightgray', linestyle='-', linewidth=0.8, alpha=0.7)
            
            # Red points
            ax.scatter(x_data, y_data, s=120, color='red', edgecolors='darkred', 
                      linewidth=1.5, zorder=5, label='Test Points')
            
            # Blue line
            x_line = np.linspace(max(8, min(x_data)-2), max(x_data)+3, 100)
            y_line = slope * x_line + intercept
            ax.plot(x_line, y_line, color='blue', linewidth=3, zorder=4)
            
            # N=25 reference
            ax.axvline(x=25, color='green', linestyle='--', linewidth=2, alpha=0.8)
            ax.plot(25, ll_25, marker='*', markersize=15, color='green', 
                   markeredgecolor='darkgreen', markeredgewidth=2, zorder=10)
            
            # Labels
            ax.set_xlabel('No. of Blows', fontsize=12, fontweight='bold')
            ax.set_ylabel('Moisture Content (%)', fontsize=12, fontweight='bold')
            ax.set_title(f'Liquid Limit Determination (LL={ll_25:.1f}%)', fontsize=14, fontweight='bold')
            ax.legend(loc='upper right')
            
            # Axis limits
            ax.set_xlim(8, max(x_data) + 5)
            ax.set_ylim(0, max(y_data) + 3)
            
            # Save to buffer
            buffer = io.BytesIO()
            fig.tight_layout()
            fig.savefig(buffer, format='png', dpi=100, facecolor='white', bbox_inches='tight')
            plt.close(fig)
            buffer.seek(0)
            
            return base64.b64encode(buffer.read())
            
        except Exception:
            plt.close('all')
            return False

   



    liquid_limit_graph = fields.Binary("Liquid Limit Flow Curve")


    selected_lab_id6 = fields.Many2one(
        'lab.option.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_option_ids)]"
    )

   





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
            # if material.grade.id == record.grade.id:
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

    def action_print_cbr(self):
        return self.env.ref('soil1.action_report_cbr').report_action(self)

    selected_lab_id = fields.Many2one(
        'lab.option.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_option_ids)]"
    )
    doc_name1 = fields.Char("Doc Name",default="Laboratory test results- California bearing ratio test (CBR)")

    cbr_generated = fields.Boolean(string="GSA Lines Generated",default=False)
    cbr_ids = fields.One2many('cbr.line', 'parent_id',ondelete='cascade')

 

    def action_generate_cbr_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case (e.g. ABC-001)
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines
            if lines:
                record.cbr_ids = lines
                record.cbr_generated = True
                record.show_sieve = True

          
   

       # FSI
    fsi_name = fields.Char("Name",default="Free Swell Index")
    fsi_visible = fields.Boolean("Free Swell Index Visible",compute="_compute_visible")

    selected_lab_id2 = fields.Many2one(
        'lab.option.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_option_ids)]"
    )
  
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

            if not lines or len(lines) < 2:
                rec.phi_deg_uu_triaxial_cohesion = 0.0
                rec.cohesion_uu_triaxial_cohesion = 0.0
                continue

            slopes = []
            intercepts = []

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

    doc_name = fields.Char("Doc Name",default="Grain Size Analysis (GSA)")

    gsa_child_lines = fields.One2many('mechanical.gsa.line','parent_id')

    def action_print_gsa(self):
        return self.env.ref('soil1.action_report_gsa').report_action(self)

   

    # def action_fetch_review_details(self):
       
    #     for line in self.gsa_child_lines:
    #         if line.lab_no:
               
    #             source_line = self.env['sample.request.review.lines'].search([
    #                 ('lab_id', '=', line.lab_no)
    #             ], limit=1)

    #             if source_line:
    #                 line.bh_id = source_line.source
    #                 line.sample_depth = source_line.depth
    #                 line.sample_details = source_line.sample_details
    #                 line.wt_of_samp = source_line.weight

               
    #             sg_record = self.env['specific.gravity'].search([
    #                 ('lab_no', '=', line.lab_no) 
    #             ], limit=1)

    #             if sg_record:
    #                 fetched_sg = sg_record.avg_corr_specific_gravity
                    
                   
    #                 line.specific_gravity = fetched_sg

                   
    #                 if line.hydrometer_analysis_lines_gsa:
    #                     for hydro_line in line.hydrometer_analysis_lines_gsa:
    #                         hydro_line.specific_gravity = fetched_sg
                            
    #                 print(f"Updated SG for Lab {line.lab_no}: {fetched_sg}")
    #             else:
    #                 print(f"SG Not Found for {line.lab_no}")

    
    


    gsa_visible = fields.Boolean("Grain Size Analysis (GSA) Visible",compute="_compute_visible")

    show_sieve = fields.Boolean(default=False)

    gsa_particle_child_lines = fields.One2many('mechanical.gsa.particle.line','parent_id')

   

    gsa_lines_generated = fields.Boolean(string="GSA Lines Generated",default=False)



    import re


#     def action_calc_d_values(self):
#        """Button to Calculate and Fetch Values"""
#        self._calculate_all_d_values()
#        return True


#     def _calculate_all_d_values(self):
#      for record in self:

#         # Remove old values
#         record.gsa_particle_child_lines.unlink()

#         lines_list = []

#         for gsa in record.gsa_child_lines:

#             val_d10 = 0.0
#             val_d30 = 0.0
#             val_d60 = 0.0
#             val_cu = 0.0
#             val_cc = 0.0

#             if gsa.sieve_analysis_child_lines_gsa:

#                 clean_data = []

#                 for line in gsa.sieve_analysis_child_lines_gsa:
#                     try:
#                         sz_str = re.sub(
#                             r"[^0-9.]",
#                             "",
#                             str(line.sieve_size or "")
#                         )

#                         size_val = float(sz_str) if sz_str else 0.0
#                         pass_val = float(line.passing_percent or 0.0)

#                         clean_data.append({
#                             'size': size_val,
#                             'passing': pass_val,
#                         })

#                     except Exception:
#                         continue

#                 # Sort by Passing %
#                 clean_data.sort(
#                     key=lambda x: x['passing'],
#                     reverse=True
#                 )

#                 # D-values
#                 val_d10 = self._get_interpolated_value(
#                     clean_data, 10
#                 )

#                 val_d30 = self._get_interpolated_value(
#                     clean_data, 30
#                 )

#                 val_d60 = self._get_interpolated_value(
#                     clean_data, 60
#                 )

#                 # Cu & Cc
#                 if val_d10 > 0 and val_d60 > 0:

#                     val_cu = val_d60 / val_d10

#                     val_cc = (
#                         (val_d30 ** 2)
#                         / (val_d60 * val_d10)
#                     )

#             fetched_meniscus = getattr(
#                 gsa,
#                 'meniscus_corre',
#                 0.5
#             )

#             fetched_dispersion = getattr(
#                 gsa,
#                 'dispersion',
#                 1.575
#             )

#             fetched_temp_corre = getattr(
#                 gsa,
#                 'temp_corre',
#                 0.0
#             )

#             lines_list.append({

#                 'parent_id': record.id,
#                 'bh_id': gsa.bh_id,
#                 'sample_depth': gsa.sample_depth,

#                 'd_10': round(val_d10, 4),
#                 'd_30': round(val_d30, 4),
#                 'd_60': round(val_d60, 4),

#                 'c_u': round(val_cu, 2),
#                 'c_c': round(val_cc, 2),

#                 'meniscus_corre': fetched_meniscus,
#                 'dispersion': fetched_dispersion,
#                 'temp_corre': fetched_temp_corre,
#             })

#         if lines_list:
#             self.env[
#                 'mechanical.gsa.particle.line'
#             ].create(lines_list)


#     def _get_interpolated_value(
#     self,
#     data_list,
#     target_percent
# ):
#       """
#       Logarithmic interpolation for grain size analysis.
#       """

#       upper = None
#       lower = None

#       for i in range(len(data_list) - 1):

#         curr = data_list[i]
#         nxt = data_list[i + 1]

#         if (
#             curr['passing'] >= target_percent
#             and nxt['passing'] <= target_percent
#         ):
#             upper = curr
#             lower = nxt
#             break

#       if not upper or not lower:
#         return 0.0

#       size2 = upper['size']
#       size1 = lower['size']

#       pass2 = upper['passing']
#       pass1 = lower['passing']

#       if (
#         size1 <= 0
#         or size2 <= 0
#         or (pass2 - pass1) == 0
#     ):
#         return 0.0

#     # Log interpolation
#       log_size1 = math.log10(size1)
#       log_size2 = math.log10(size2)

#       log_result = (
#         log_size2
#         - (
#             (pass2 - target_percent)
#             * (log_size2 - log_size1)
#             / (pass2 - pass1)
#         )
#     )

#       return 10 ** log_result


    def action_calc_d_values(self):
      """Button to Calculate and Fetch Values"""
      self._calculate_all_d_values()
      return True


    def _calculate_all_d_values(self):

     for record in self:

        # Remove old values
        record.gsa_particle_child_lines.unlink()

        lines_list = []

        for gsa in record.gsa_child_lines:

            val_d10 = 0.0
            val_d30 = 0.0
            val_d60 = 0.0
            val_cu = 0.0
            val_cc = 0.0

            if gsa.sieve_analysis_child_lines_gsa:

                clean_data = []

                for line in gsa.sieve_analysis_child_lines_gsa:

                    try:
                        size_match = re.search(
                            r'(\d+\.?\d*)',
                            str(line.sieve_size or '')
                        )

                        size_val = (
                            float(size_match.group(1))
                            if size_match
                            else 0.0
                        )

                        pass_val = float(
                            line.passing_percent or 0.0
                        )

                        clean_data.append({
                            'size': size_val,
                            'passing': pass_val,
                        })

                    except Exception:
                        continue

                # Sort by passing percentage descending
                clean_data.sort(
                    key=lambda x: x['passing'],
                    reverse=True
                )

                # Calculate D-values
                val_d10 = self._get_interpolated_value(
                    clean_data,
                    10
                )

                val_d30 = self._get_interpolated_value(
                    clean_data,
                    30
                )

                val_d60 = self._get_interpolated_value(
                    clean_data,
                    60
                )

                # Calculate Cu and Cc
                if val_d10 > 0 and val_d60 > 0:

                    val_cu = val_d60 / val_d10

                    val_cc = (
                        (val_d30 ** 2)
                        / (val_d60 * val_d10)
                    )

            fetched_meniscus = getattr(
                gsa,
                'meniscus_corre',
                0.5
            )

            fetched_dispersion = getattr(
                gsa,
                'dispersion',
                1.575
            )

            fetched_temp_corre = getattr(
                gsa,
                'temp_corre',
                0.0
            )

            lines_list.append({

                'parent_id': record.id,
                'bh_id': gsa.bh_id,
                'sample_depth': gsa.sample_depth,

                'd_10': round(val_d10, 4),
                'd_30': round(val_d30, 4),
                'd_60': round(val_d60, 4),

                'c_u': round(val_cu, 2),
                'c_c': round(val_cc, 2),

                'meniscus_corre': fetched_meniscus,
                'dispersion': fetched_dispersion,
                'temp_corre': fetched_temp_corre,
            })

        if lines_list:
            self.env[
                'mechanical.gsa.particle.line'
            ].create(lines_list)


    def _get_interpolated_value(
    self,
    data_list,
    target_percent
):
      """
      Logarithmic interpolation for
      D10, D30 and D60.
      """

      if not data_list:
        return 0.0

      upper = None
      lower = None

      for i in range(len(data_list) - 1):

        current = data_list[i]
        next_row = data_list[i + 1]

        if (
            current['passing'] >= target_percent >=
            next_row['passing']
        ):
            upper = current
            lower = next_row
            break

      if not upper or not lower:
        return 0.0

      d1 = upper['size']
      d2 = lower['size']

      p1 = upper['passing']
      p2 = lower['passing']

      if d1 <= 0 or d2 <= 0 or p1 == p2:
        return 0.0

      log_d1 = math.log10(d1)
      log_d2 = math.log10(d2)

    # Standard logarithmic interpolation
      log_d = log_d1 + (
        (target_percent - p1)
        * (log_d2 - log_d1)
        / (p2 - p1)
    )

      return 10 ** log_d



    

















   


#     def action_calc_d_values(self):
#      """Button Action"""

#      self._calculate_all_d_values()

#      return True


#     def _calculate_all_d_values(self):

#      for record in self:

#         # DELETE OLD RECORDS
#         record.gsa_particle_child_lines.unlink()

#         lines_list = []

#         for gsa in record.gsa_child_lines:

#             # ==========================================
#             # DEFAULT VALUES
#             # ==========================================
#             val_d10 = 0.0
#             val_d30 = 0.0
#             val_d60 = 0.0

#             val_cu = 0.0
#             val_cc = 0.0

#             # ==========================================
#             # TAKE HYDROMETER DATA
#             # ==========================================
#             clean_data = []

#             for line in gsa.hydrometer_analysis_lines_gsa:

#                 try:

#                     # DIAMETER OF SOIL
#                     size_val = float(
#                         line.diameter_soil or 0.0
#                     )

#                     # N % CORRECTED
#                     pass_val = float(
#                         line.n_corrected or 0.0
#                     )

#                     if (
#                         size_val > 0
#                         and pass_val > 0
#                     ):

#                         clean_data.append({

#                             'size': size_val,

#                             'passing': pass_val
#                         })

#                 except:
#                     continue

#             # ==========================================
#             # SORT BY PASSING %
#             # ==========================================
#             clean_data.sort(
#                 key=lambda x: x['passing'],
#                 reverse=True
#             )

#             # ==========================================
#             # D VALUES
#             # ==========================================
#             val_d10 = self._get_interpolated_value(
#                 clean_data,
#                 10
#             )

#             val_d30 = self._get_interpolated_value(
#                 clean_data,
#                 30
#             )

#             val_d60 = self._get_interpolated_value(
#                 clean_data,
#                 60
#             )

#             # ==========================================
#             # MATCH EXCEL GRAPH CURVE
#             # ==========================================

#             # D10
#             if val_d10 > 0:
#                 val_d10 = val_d10 * 0.635

#             # D30
#             if val_d30 > 0:
#                 val_d30 = val_d30 * 0.792

#             # D60
#             if val_d60 > 0:
#                 val_d60 = val_d60 *  0.608

#             # ==========================================
#             # Cu
#             # ==========================================
#             if val_d10 > 0:

#                 val_cu = (
#                     val_d60 / val_d10
#                 )

#             # ==========================================
#             # Cc
#             # ==========================================
#             if (
#                 val_d10 > 0
#                 and val_d60 > 0
#             ):

#                 val_cc = (
#                     (val_d30 ** 2)
#                     /
#                     (val_d60 * val_d10)
#                 )

#             # ==========================================
#             # FETCH OTHER VALUES
#             # ==========================================
#             fetched_meniscus = getattr(
#                 gsa,
#                 'meniscus_corre',
#                 0.5
#             )

#             fetched_dispersion = getattr(
#                 gsa,
#                 'dispersion',
#                 1.575
#             )

#             fetched_temp_corre = getattr(
#                 gsa,
#                 'temp_corre',
#                 0.0
#             )

#             # ==========================================
#             # APPEND VALUES
#             # ==========================================
#             lines_list.append({

#                 'parent_id': record.id,

#                 'bh_id': gsa.bh_id,

#                 'sample_depth': gsa.sample_depth,

#                 # DISPLAY VALUES
#                 'd_10': round(val_d10, 3),

#                 'd_30': round(val_d30, 3),

#                 'd_60': round(val_d60, 3),

#                 'c_u': round(val_cu, 2),

#                 'c_c': round(val_cc, 2),

#                 'meniscus_corre': fetched_meniscus,

#                 'dispersion': fetched_dispersion,

#                 'temp_corre': fetched_temp_corre,
#             })

#         # ==========================================
#         # CREATE RECORDS
#         # ==========================================
#         if lines_list:

#             self.env[
#                 'mechanical.gsa.particle.line'
#             ].create(lines_list)


# # =====================================================
# # EXACT EXCEL INTERPOLATION
# # =====================================================

#     def _get_interpolated_value(
#     self,
#     data_list,
#     target_percent
# ):

#      if not data_list:
#         return 0.0

#      upper = None
#      lower = None

#     # ==========================================
#     # FIND SURROUNDING ROWS
#     # ==========================================
#      for i in range(len(data_list) - 1):

#         curr = data_list[i]

#         next_one = data_list[i + 1]

#         if (
#             curr['passing'] >= target_percent
#             and next_one['passing'] <= target_percent
#         ):

#             upper = curr
#             lower = next_one

#             break

#      if not upper or not lower:
#         return 0.0

#     # PASSING %
#      P1 = upper['passing']
#      P2 = lower['passing']

#     # DIAMETER
#      D1 = upper['size']
#      D2 = lower['size']

#     # SAFETY
#      if (P1 - P2) == 0:
#         return 0.0

#     # EXACT EXCEL FORMULA
#      result = D1 - (
#         (
#             P1 - target_percent
#         )
#         *
#         (
#             D1 - D2
#         )
#         /
#         (
#             P1 - P2
#         )
#     )

#      return result
    
    
    
    def action_generate_gsa_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines
            if lines:
                record.gsa_child_lines = lines
                record.gsa_lines_generated = True
                record.show_sieve = True

           

    

    gsa_graph_image = fields.Binary(
        string="GSA Graph Image",
        attachment=True,
        help="Grain Size Analysis चा तयार केलेला आलेख."
    )
    gsa_graph_filename = fields.Char(
        string="Graph Filename",
        default="gsa_curve.png"
    )


    
    import matplotlib.pyplot as plt
    import itertools


    def action_generate_gsa_graph(self):

     import matplotlib.pyplot as plt
     import matplotlib.ticker as ticker
     import io
     import base64
     import numpy as np
     from scipy.interpolate import PchipInterpolator

     for record in self:

        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)

        ax.set_xscale('log')
        ax.set_xlim(0.001, 100)
        ax.set_ylim(0, 110)

        ax.set_xlabel("Particle Diameter (mm)", fontsize=10, fontweight='bold')
        ax.set_ylabel("Percentage Finer (%)", fontsize=10, fontweight='bold')

        ax.grid(True, which='major', linestyle='-', linewidth=0.8, color='#404040', alpha=0.6)
        ax.grid(True, which='minor', linestyle='-', linewidth=0.5, color='#a0a0a0', alpha=0.4)

        locmaj = ticker.LogLocator(base=10.0, subs=(1.0,), numticks=100)
        ax.xaxis.set_major_locator(locmaj)

        def nice_log_formatter(x, pos):
            if x in [0.001, 0.01, 0.1, 1, 10, 100]:
                return f"{x:g}"
            return ""

        ax.xaxis.set_major_formatter(ticker.FuncFormatter(nice_log_formatter))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(10))

        markers = ['^','*','D','x','o','s','v','+','p','h','1','2','3','4','8','H','X','d','|','_']

        colors = [
            "#1f77b4","#2ca02c","#ff7f0e","#d62728","#9467bd",
            "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf",
            "#393b79","#637939","#8c6d31","#843c39","#7b4173"
        ]

        marker_unicode = {
            '^': '▲',
            '*': '★',
            'D': '◆',
            'x': '✕',
            'o': '●',
            's': '■',
            'v': '▼',
            '+': '+'
        }

        plot_index = 0
        data_plotted = False

        if record.gsa_child_lines:

            for sample in record.gsa_child_lines:

                data_pairs = []

                for line in sample.sieve_analysis_child_lines_gsa:

                    if line.sieve_size and line.passing_percent is not None:

                        try:
                            size_str = str(line.sieve_size).lower().replace('mm', '').strip()

                            if 'pan' in size_str:
                                continue

                            size_val = round(float(size_str), 5)
                            pass_val = line.passing_percent

                            if 0.001 <= size_val <= 100:
                                data_pairs.append((size_val, pass_val))

                        except ValueError:
                            continue

                data_pairs.sort(key=lambda x: x[0])

                if data_pairs:

                    marker = markers[plot_index % len(markers)]
                    color = colors[plot_index % len(colors)]

                    sizes = np.array([x[0] for x in data_pairs])
                    passing = np.array([x[1] for x in data_pairs])

                    # -------- PERFECT SMOOTH CURVE (PCHIP) --------
                    if len(sizes) >= 3:

                        x_smooth = np.logspace(
                            np.log10(min(sizes)),
                            np.log10(max(sizes)),
                            120
                        )

                        pchip = PchipInterpolator(sizes, passing)
                        y_smooth = pchip(x_smooth)

                        # safety clamp
                        y_smooth = np.clip(y_smooth, 0, 100)

                        ax.plot(
                            x_smooth,
                            y_smooth,
                            color=color,
                            linewidth=2,
                            label=sample.lab_id or "Sample"
                        )
                    else:
                        ax.plot(
                            sizes,
                            passing,
                            color=color,
                            linewidth=2,
                            label=sample.lab_id or "Sample"
                        )

                    # Original points (important)
                    ax.scatter(
                        sizes,
                        passing,
                        marker=marker,
                        color=color,
                        s=40
                    )

                    # Legend symbol
                    symbol = marker_unicode.get(marker, marker)

                    sample.symbol_html = f"""
<svg width="60" height="22">
    <line x1="0" y1="11" x2="60" y2="11"
          stroke="{color}"
          stroke-width="3"
          stroke-linecap="round"/>

    <text x="30" y="15"
          text-anchor="middle"
          font-size="16"
          fill="{color}"
          font-weight="bold">
        {symbol}
    </text>
</svg>
"""

                    plot_index += 1
                    data_plotted = True

            if data_plotted:
                ax.legend(loc='lower right', fontsize=9)

            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            plt.close(fig)

            buffer.seek(0)
            record.gsa_graph_image = base64.b64encode(buffer.read())
            buffer.close()
    
    

       


   

         # DETERMINATION OF CONSOLIDATION PROPERTIES		
    consolidation_name = fields.Char("Name",default="DETERMINATION OF CONSOLIDATION PROPERTIES")
    consolidation_visible = fields.Boolean("DETERMINATION OF CONSOLIDATION PROPERTIES",compute="_compute_visible")	

    doc_consolidation_name = fields.Char("Doc Name",default="CONSOLIDATION TEST")

    selected_lab_id7 = fields.Many2one(
        'lab.option.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_option_ids)]"
    )

    consolidation_generated = fields.Boolean(string="GSA Lines Generated",default=False)
    consolidation_lines = fields.One2many('consolidation.line', 'parent_id',ondelete='cascade')

    # def action_generate_consolidation_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.consolidation_lines = lines
    #             record.consolidation_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.consolidation_lines:
    #             record.show_sieve = True

    def action_generate_consolidation_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines
            if lines:
                record.consolidation_lines = lines
                record.consolidation_generated = True
                record.show_sieve = True

           



     # DETERMINATION OF SWELLING PRESSURE OF SOILS BY CONSOLIDOMETER METHOD				
    
    swelling_pressure_name = fields.Char("Name",default="DETERMINATION OF SWELLING PRESSURE OF SOILS BY CONSOLIDOMETER METHOD")
    swelling_pressure_visible = fields.Boolean("DETERMINATION OF SWELLING PRESSURE OF SOILS BY CONSOLIDOMETER METHOD",compute="_compute_visible")

    swelling_pressure_doc_name = fields.Char("Doc. Name",default="DETERMINATION OF SWELLING PRESSURE OF SOILS BY CONSOLIDOMETER METHOD")

    selected_lab_id5 = fields.Many2one(
        'lab.option.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_option_ids)]"
    )

    swelling_pressure_generated = fields.Boolean(string="GSA Lines Generated",default=False)
    swelling_pressure_ids = fields.One2many('swelling.pressure.line', 'parent_id',ondelete='cascade')

    # def action_generate_swelling_pressure_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.swelling_pressure_ids = lines
    #             record.swelling_pressure_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.swelling_pressure_ids:
    #             record.show_sieve = True

    def action_generate_swelling_pressure_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines
            if lines:
                record.swelling_pressure_ids = lines
                record.swelling_pressure_generated = True
                record.show_sieve = True

           






    #  DETERMINE PERMEABILITY OF SOIL - BY FALLING HEAD			

    permeability_falling_name = fields.Char("Name",default="Permeability Falling Head Test")
    permeability_falling_visible = fields.Boolean("Permeability Falling Head Test",compute="_compute_visible")

    selected_lab_id3 = fields.Many2one(
        'lab.option.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_option_ids)]"
    )

    show_sieve = fields.Boolean(default=False)

    permeability_falling_generated = fields.Boolean(string="GSA Lines Generated",default=False)
    permeability_falling_ids = fields.One2many('perm.head.line', 'parent_id',ondelete='cascade')

    # def action_generate_permeability_falling_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.permeability_falling_ids = lines
    #             record.permeability_falling_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.permeability_falling_ids:
    #             record.show_sieve = True

    def action_generate_permeability_falling_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case (e.g. ABC-001)
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines
            if lines:
                record.permeability_falling_ids = lines
                record.permeability_falling_generated = True
                record.show_sieve = True

    

            




    # DETERMINE THE SHEAR STRENGTH BY TRIAXIAL SHEAR TEST 
    triaxial_test_name = fields.Char("Name",default="DETERMINE THE SHEAR STRENGTH BY TRIAXIAL SHEAR TEST")
    triaxial_test_visible = fields.Boolean("DETERMINE THE SHEAR STRENGTH BY TRIAXIAL SHEAR TEST",compute="_compute_visible")

    triaxial_doc_name = fields.Char("Doc. Name",default="Triaxial Shear Test (UU)")



    selected_lab_id1 = fields.Many2one(
        'lab.option.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_option_ids)]"
    )


    show_sieve = fields.Boolean(default=False)

    triaxial_test_generated = fields.Boolean(string="GSA Lines Generated",default=False)
    triaxial_test_ids = fields.One2many('triaxial.shear.line', 'parent_id',ondelete='cascade')

    

    # def action_generate_triaxial_test_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.triaxial_test_ids = lines
    #             record.triaxial_test_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.triaxial_test_ids:
    #             record.show_sieve = True

    def action_generate_triaxial_test_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case (e.g. ABC-001)
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines and flags
            if lines:
                record.triaxial_test_ids = lines
                record.triaxial_test_generated = True
                record.show_sieve = True

          

    







    #  DETERMINATION OF WATER CONTENT–DRY DENSITY RELATION USING LIGHT/HEAVY COMPACTION	

    soil_light_heavy_name = fields.Char("Name",default="DETERMINATION OF WATER CONTENT–DRY DENSITY RELATION USING LIGHT/HEAVY COMPACTION")
    soil_light_heavy_visible = fields.Boolean("DETERMINATION OF WATER CONTENT–DRY DENSITY RELATION USING LIGHT/HEAVY COMPACTION",compute="_compute_visible")

    doc_name_proctor = fields.Char("Doc Name",default="Proctor test on soil")

    selected_lab_id8 = fields.Many2one(
        'lab.option.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_option_ids)]"
    )

    show_sieve = fields.Boolean(default=False)

    soil_light_heavy_generated = fields.Boolean(string="GSA Lines Generated",default=False)
    soil_light_heavy_ids = fields.One2many('heavy.compaction.line', 'parent_id',ondelete='cascade')

    # def action_generate_soil_light_heavy_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.soil_light_heavy_ids = lines
    #             record.soil_light_heavy_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.soil_light_heavy_ids:
    #             record.show_sieve = True

    def action_generate_soil_light_heavy_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case (e.g. ABC-001)
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines and flags
            if lines:
                record.soil_light_heavy_ids = lines
                record.soil_light_heavy_generated = True
                record.show_sieve = True




    # DETERMINE THE UNCONFINED COMPRESSIVE STRENGTH		

    ucs_name = fields.Char("Name",default="Unconfined Compressive Strength (UCS) Test")
    ucs_visible = fields.Boolean("Unconfined Compressive Strength (UCS) Test Visible",compute="_compute_visible")

    selected_lab_id9 = fields.Many2one(
        'lab.option.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_option_ids)]"
    )

    show_sieve = fields.Boolean(default=False)

    ucs_generated = fields.Boolean(string="GSA Lines Generated",default=False)
    ucs_ids = fields.One2many('ucs.line', 'parent_id',ondelete='cascade')

    # def action_generate_ucs_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.ucs_ids = lines
    #             record.ucs_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.ucs_ids:
    #             record.show_sieve = True

    def action_generate_ucs_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case (e.g. ABC-001)
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines and flags
            if lines:
                record.ucs_ids = lines
                record.ucs_generated = True
                record.show_sieve = True

    
    


    # DETERMINE SHEAR STRENGTH BY DIRECT SHEAR TEST									

    direct_shear_name = fields.Char("Name",default="DETERMINE SHEAR STRENGTH BY DIRECT SHEAR TEST")

    direct_shear_doc_name = fields.Char("Doc.Name",default="Direct Shear Test (DST)")
    direct_shear_visible = fields.Boolean("Direct Shear Test Visible",compute="_compute_visible")

    selected_lab_id10 = fields.Many2one(
        'lab.option.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_option_ids)]"
    )

    show_sieve = fields.Boolean(default=False)

    direct_shear_generated = fields.Boolean(string="GSA Lines Generated",default=False)
    direct_shear_line = fields.One2many('direct.shear.line', 'parent_id',ondelete='cascade')

    # def action_generate_direct_shear_lines(self):
    #     for record in self:
    #         if record.lab_id and ' - ' in record.lab_id:
    #             start_str, end_str = record.lab_id.split(' - ')
    #             prefix = '-'.join(start_str.split('-')[:2])
    #             start = int(start_str.split('-')[2])
    #             end = int(end_str.split('-')[2])

    #             lines = []
    #             for i in range(start, end + 1):
    #                 lab_id = f"{prefix}-{str(i).zfill(3)}"
    #                 lines.append((0, 0, {'lab_id': lab_id}))

    #             record.direct_shear_line = lines
    #             record.direct_shear_generated = True

    #         # 🔹 Set flag to show sieve analysis
    #         if record.direct_shear_line:
    #             record.show_sieve = True

    def action_generate_direct_shear_lines(self):
        for record in self:
            lines = []

            if record.lab_id:
                # 🔹 Range case (e.g. ABC-001 - ABC-005)
                if ' - ' in record.lab_id:
                    start_str, end_str = record.lab_id.split(' - ')
                    prefix = '-'.join(start_str.split('-')[:2])
                    start = int(start_str.split('-')[2])
                    end = int(end_str.split('-')[2])

                    for i in range(start, end + 1):
                        lab_id = f"{prefix}-{str(i).zfill(3)}"
                        lines.append((0, 0, {'lab_id': lab_id}))

                # 🔹 Single lab id case (e.g. ABC-001)
                else:
                    lines.append((0, 0, {'lab_id': record.lab_id}))

            # 🔹 Assign lines and flags
            if lines:
                record.direct_shear_line = lines
                record.direct_shear_generated = True
                record.show_sieve = True




   

     ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
      
        for record in self:
            record.sieve_visible = False
            
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
            # record.specific_gravity_visible  = False 
            record.direct_shear_visible  = False 
            record.ucs_visible  = False 
            record.consolidation_visible  = False 
            # record.consolidation_pc_visible  = False 
            # record.angle_shear_visible  = False 
            record.swelling_pressure_visible  = False 
            record.uu_triaxial_angle_visible  = False
            record.uu_triaxial_cohesion_visible  = False

            record.triaxial_test_visible  = False



            record.moisture_visible  = False
            record.gsa_visible = False

            record.specific_gravity_visible = False
            record.freeswell_visible = False

            record.soil_light_heavy_visible = False
            record.nmc_visible = False
            record.pl_visible = False
            record.ll_visible = False
            record.sl_visible = False

           





            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == '12014fgr-5c56-475b-9a89-93a59c9ee3a2':
                    record.sieve_visible = True

               
                # if sample.internal_id == '23fg21gh-7202-4d62-864b-8efa58b6b61f':
                #     record.liquid_limit_visible = True

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

                # if sample.internal_id == '214hhj6gt21-ca64-44dd-b0ae-6587gghty':
                #     record.specific_gravity_visible = True

                if sample.internal_id == '21457888hhhllly1-ca64-44dd-b0ae-3214hhhtr':
                    record.direct_shear_visible = True

                if sample.internal_id == '321456ki8hhhllly1-ca64-44dd-b0ae-3214654lk':
                    record.direct_shear_visible = True


                if sample.internal_id == 't4y57888hhhllly1-ca64-44dd-b0ae-1234567rt':
                    record.ucs_visible = True
                
                if sample.internal_id == '78957888hhhllly1-ca64-44dd-b0ae-2314780ty':
                    record.consolidation_visible = True

               

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

                if sample.internal_id == '318214f8-0d92-46e8-aabf-f27ff8556a82':
                    record.gsa_visible = True

                if sample.internal_id == '26a889da-3ab8-40e9-af69-2399b62dce9f':
                    record.specific_gravity_visible = True

                if sample.internal_id == '3825ec57-11f8-4249-9fa8-d99f64ffd396':
                    record.freeswell_visible = True



                if sample.internal_id == 'yt25ec57-11f8-4249-9fa8-788889999rtt':
                    record.triaxial_test_visible = True

                if sample.internal_id == 'c800e59a-b847-4049-9e2b-673fcd1fcde5':
                    record.soil_light_heavy_visible = True

                if sample.internal_id == 'yoptr557-11f8-4249-9fa8-78888993214g':
                    record.pl_visible = True
                if sample.internal_id == 'uitefc57-11f8-4249-9fa8-788889923147':
                    record.ll_visible = True
                if sample.internal_id == 'yt28uj5t-11f8-4249-9fa8-78888993214t':
                    record.sl_visible = True
                
               









    def open_eln_page(self):
    # import wdb; wdb.set_trace()
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        if current_user.has_group('lerm_civil.lerm_discipline_group'):
            technician_results = self.eln_ref.parameters_result
        else:
            technician_results = self.eln_ref.parameters_result.filtered(
                lambda r: r.technician == current_user
            )

        for result in technician_results:
            if result.parameter.internal_id == '23fg21gh-7202-4d62-864b-8efa58b6b61f':
                result.result_char = round(self.liquid_limit,2)
                result.calculated = True
                if self.liquid_limit_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '120vbf14-2ff0-4b81-aca1-0e07dab7cd87':
                result.result_char = round(self.plastic_limit,2)
                result.calculated = True
                if self.plastic_limit_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '1045789654-2ff0-4b81-aca1-0e07dab7cd87':
                result.result_char = round(self.plasticity_index,2)
                result.calculated = True
                if self.plasticity_index_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '3210vbf-20fb-4843-aa0e-2ee981be0d7c':
                result.result_char = round(self.max_dry_density,2)
                result.calculated = True
                if self.heavy_table_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '3210vbf-20fb-4843-aa0e-142578bgtyu':
                result.result_char = round(self.omc1,2)
                result.calculated = True
                if self.omc_table_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == 'ght4125-ca64-44dd-b0ae-228aacf04998':
                result.result_char = round(self.fsi,2)
                result.calculated = True
                if self.fsi_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '5487gt21-ca64-44dd-b0ae-228aacf04965':
                result.result_char = round(self.permeability,2)
                result.calculated = True
                if self.permeability_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '3210vbf-20fb-4843-aa0e-145ght27854l':
                result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                if self.area_triaxial_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue




            if result.parameter.internal_id == 'tyer4fgr-5c56-475b-9arty156878965uut':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '3825ec57-11f8-4249-9fa8-d99f64ffd396':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '214hhj6gt21-ca64-44dd-b0ae-6587gghty':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '26a889da-3ab8-40e9-af69-2399b62dce9f':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '9521yt88hhhllly1-ca64-44dd-b0ae-8974578ghtr2':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '7abb5a01-2fa7-4c4a-ab6e-0f4112e3aea9':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '12014fgr-5c56-475b-9a89-93a59c9ee3a2':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '120vbf14-2ff0-4b81-aca1-0e07dab7cd87':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '3210vbf-20fb-4843-aa0e-2ee981be0d7c':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '3210vbf-20fb-4843-aa0e-142578bgtyu':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '3210vbf-20fb-4843-aa0e-145ght27854l':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '14578nhy87-20fb-4843-aa0e-145ght27854l':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '15247gtr-2065-4532-814a-3a4c1e884305':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'ght4125-ca64-44dd-b0ae-228aacf04998':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '5487gt21-ca64-44dd-b0ae-228aacf04965':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '5487gt21-ca64-44dd-b0ae-278954ggh114':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '897546gt21-ca64-44dd-b0ae-22145687':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '21457888hhhllly1-ca64-44dd-b0ae-3214hhhtr':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 't4y57888hhhllly1-ca64-44dd-b0ae-1234567rt':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '78957888hhhllly1-ca64-44dd-b0ae-2314780ty':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '78957888hhhllly1-ca64-44dd-b0ae-2314780ty':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue
            
            if result.parameter.internal_id == 'yt25ec57-11f8-4249-9fa8-788889999rtt':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'c800e59a-b847-4049-9e2b-673fcd1fcde5':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '32145888hhhllly1-ca64-44dd-b0ae-2578886oopp':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '321456ki8hhhllly1-ca64-44dd-b0ae-3214654lk':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '318214f8-0d92-46e8-aabf-f27ff8556a82':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'jkt56888hhhllly1-ca64-44dd-b0ae-23120147g':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'po567888hhhllly1-ca64-44dd-b0ae-23120114r':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'poty7888hhhllly1-ca64-44dd-b0ae-23141478h':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '214578255hhhllly1-ca64-44dd-b0ae-231421457':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'yt25ec57-11f8-4249-9fa8-78888921457r':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'uitefc57-11f8-4249-9fa8-788889923147':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'yt2okplt-11f8-4249-9fa8-78888993214t':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'yoptr557-11f8-4249-9fa8-78888993214g':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'yt28uj5t-11f8-4249-9fa8-78888993214t':
                # result.result_char = round(self.area_triaxial,2)
                result.calculated = True
                # if self.area_triaxial_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
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







    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    @api.depends_context('uid')
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
    container_no = fields.Char(string="Container No.")
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
    parent_id_cbr = fields.Many2one('cbr.line',string="Parent Id")

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

   

    @api.depends('no_division', 'parent_id_cbr.m', 'parent_id_cbr.c')
    def _compute_applied_force(self):
     for rec in self:
        m = rec.parent_id_cbr.m or 0.0
        c = rec.parent_id_cbr.c or 0.0
        n = rec.no_division or 0.0

        if n == 0:
            rec.applied_force = 0.0
        else:
            rec.applied_force = (m * n) + c

    

    @api.depends('applied_force', 'parent_id_cbr.rise_force')
    def _compute_avg_load(self):
     for rec in self:
        rise_force = rec.parent_id_cbr.rise_force or 0.0

        if rec.applied_force == 0:
            rec.avg_load = 0.0
        else:
            rec.avg_load = rec.applied_force + (rec.applied_force * rise_force)

   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id_cbr'):
            existing_records = self.search([('parent_id_cbr', '=', vals['parent_id_cbr'])])
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
  
    parent_id = fields.Many2one('mechanical.soil1',  string="Parent Id", ondelete='cascade', )

    serial_no = fields.Integer(string='Sr.No')

    date = fields.Date(string="Date")
    lab_id = fields.Char(string='Lab ID')

    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")

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

    review_line_id = fields.Many2one(
    'sample.request.review.lines',
    string="Sample Review Line"
)

    is_checked = fields.Boolean(
        string="Calculated",
        default=False
    )
    start_date = fields.Date(string="Start Date")  # manually fill
    end_date = fields.Date(string="End Date")      # auto fill on submit


    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise ValidationError(
                        "Start Date cannot be greater than End Date."
                    )

    

    def action_submit(self):
        self.ensure_one()
        
        # Boolean True save
        # self.write({
        #     'is_checked': True,
        #     'end_date': fields.Date.context_today(self),  # current date auto fill
        # })
        
        # Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}


   
    


    sr_no = fields.Integer(string="Sr NO.")
    #  readonly=True, copy=False, default=1
    
    # symbol = fields.Char(string="Symbol")
    symbol = fields.Char(string="Symbol", readonly=True)

    

    symbol_html = fields.Html(string="Symbol",sanitize=False,readonly=True)

    symbol_color = fields.Char(string="Symbol Color", readonly=True)


    bh_id = fields.Char(string="BH ID",compute="_compute_gsa",store=True)
    lab_id = fields.Char(string="LAB ID")
    sample_depth = fields.Char(string="Sample Depth (m)",compute="_compute_gsa",store=True)
    sample_details = fields.Char(string="Sample Details",compute="_compute_gsa",store=True)

    

    water_content = fields.Char(string="Water Content (%)")

    wt_of_samp = fields.Float(string="Weight of total sample (gm)")

    temp = fields.Float("Temp °c" )
    humidity = fields.Float("Humidity %" )

    wt_of_samp1 = fields.Float(string="Weight of total sample (gm)")

    sample_id = fields.Many2one(
        related='parent_id.sample_id',
        store=True,
        readonly=True
    )

    @api.depends('lab_id')
    def _compute_gsa(self):
        ReviewLine = self.env['sample.request.review.lines']

        for line in self:
            line.bh_id = False
            line.sample_depth = False
            line.sample_details = False

            if not line.lab_id:
                continue

            review_line = ReviewLine.search(
                [('lab_id', '=', line.lab_id)],
                order='id desc',
                limit=1
            )

            if review_line:
                line.bh_id = review_line.source        # BH ID / Location
                line.sample_depth = review_line.depth         # Depth (m)
                line.sample_details = review_line.sample_details         # Depth (m)

    

    soil_classification = fields.Selection([
        ('poorly_graded', 'Poorly Graded'),
        ('well_graded', 'Well Graded'),
        ('well_graded_gravel', 'Well-Graded Gravel'),
        ('poorly_graded_gravel', 'Poorly-Graded-Gravel'),
        ('silty_gravel', 'Silty-Gravel'),
        ('clayey_gravel', 'Clayey-Gravel'),
        ('silty_sand', 'Silty-Sand'),
        ('clayey_sand', 'Clayey-Sand'),
        ('inorganic_silt_fs', 'Inorganic-Silt-FS'),
        ('inorganic_clays_lm', 'Inorganic-Clays-LM'),
        ('organic_silt', 'Organic-Silt'),
        ('inorganic_silt', 'Inorganic-Silt'),
        ('inorganic_clay', 'Inorganic-Clay'),
        ('organic_clay', 'Organic-Clay'),
        ('peat', 'Peat'),
        ('hard_rock', 'Hard-Rock'),
        ('soft_rock', 'Soft-Rock'),
        ('inorganic_silt_m', 'Inorganic-Silt-M'),
        ('inorganic_clay_m', 'Inorganic-Clay-M'),
        ('silty_clay_border', 'Silty-Clay-Border'),
        ('fine_grained_soil', 'Fine Grained Soil'),
    ], string="Classification")

    meniscus_corre = fields.Float(string="Meniscus Correction, Cm", digits=(12,1),default=0.5)
    vescosity_water = fields.Float(string="Viscosity of Water at Room Temperature in poise",digits=(12,9),store=True,default=0.0093885959)
    dispersion = fields.Float(string="Dispersion Agent Correction, x",default=1.575,digits=(12,3))
    temp_corre = fields.Float(string="Temperature Correction, Mt",compute="_compute_temp_corre",digits=(12,4))
    specific_gravity = fields.Float(string="Specific gravity",digits=(12,3))

    m_4 = fields.Float(string="M",digits=(12,4))
    c_4 = fields.Float(string="C",digits=(12,4))

    after_m_4 = fields.Float(string="M",digits=(12,4))
    after_c_4 = fields.Float(string="C",digits=(12,4))


    

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



#     @api.depends(
#     'sieve_analysis_child_lines_gsa.passing_percent',
#     'sieve_analysis_child_lines_gsa.sieve_size'
# )
#     def _compute_silt_clay(self):

#      for rec in self:

#         clay_val = 0.0

#         data_points = []

#         for line in rec.sieve_analysis_child_lines_gsa:

#             try:

#                 size = float(str(line.sieve_size).strip())

#                 passing = line.passing_percent

#                 data_points.append({
#                     'size': size,
#                     'passing': passing
#                 })

#             except:
#                 continue

#         # SORT DESC
#         data_points.sort(
#             key=lambda x: x['size'],
#             reverse=True
#         )

#         upper = None
#         lower = None

#         # FIND POINTS AROUND 0.002
#         for i in range(len(data_points) - 1):

#             p1 = data_points[i]
#             p2 = data_points[i + 1]

#             if p1['size'] >= 0.002 >= p2['size']:

#                 upper = p1
#                 lower = p2

#                 break

#         if upper and lower:

#             x1 = upper['size']
#             y1 = upper['passing']

#             x2 = lower['size']
#             y2 = lower['passing']

#             # LOG INTERPOLATION
#             if x1 > 0 and x2 > 0:

#                 clay_val = y1 + (
#                     (y2 - y1)
#                     *
#                     (
#                         (math.log10(0.002) - math.log10(x1))
#                         /
#                         (math.log10(x2) - math.log10(x1))
#                     )
#                 )

#         # rec.silt_clay = round(clay_val)
#         rec.silt_clay = math.ceil(clay_val)




   


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


    # def action_add_n_corrected(self):
    #     for record in self:

    #         # 1️⃣ 0.075 sieve exists?
    #         sieve_075 = record.sieve_analysis_child_lines_gsa.filtered(
    #             lambda l: l.sieve_size == '0.075'
    #         )
    #         if not sieve_075:
    #             raise UserError("0.075 sieve line not found")

    #         # 2️⃣ Take ALL hydrometer lines AS-IS (order preserved)
    #         hydro_lines = record.hydrometer_analysis_lines_gsa.filtered(
    #             lambda h: h.n_corrected is not False
    #         )

    #         if not hydro_lines:
    #             raise UserError("No Hydrometer data found")

    #         # 3️⃣ Delete old < 0.075 sieve rows
    #         for line in record.sieve_analysis_child_lines_gsa:
    #             try:
    #                 if float(line.sieve_size) < 0.075:
    #                     line.unlink()
    #             except Exception:
    #                 pass

    #         # 4️⃣ Insert EXACT hydrometer values (duplicates + 0.00 included)
    #         for h in hydro_lines:
    #             self.env['gsa.lab.sieve.analysis.line'].create({
    #                 'parent_id_gsa': record.id,
    #                 'sieve_size': f"{h.diameter_soil:.4f}",   # 0.05, 0.04 ... 0.00
    #                 'passing_percent': h.n_corrected,         # 65.05 ... 6.58
                    
    #             })


    def action_add_n_corrected(self):

     for record in self:

        # GET HYDROMETER LINES
        hydro_lines = record.hydrometer_analysis_lines_gsa.filtered(
            lambda h: h.n_corrected not in (False, None)
        )

        if not hydro_lines:
            raise UserError("No Hydrometer data found")

        # DELETE OLD HYDROMETER ROWS
        old_lines = record.sieve_analysis_child_lines_gsa.filtered(
            lambda l: l.is_hydrometer
        )

        old_lines.unlink()

        # CREATE NEW ROWS
        for h in hydro_lines:

            self.env['gsa.lab.sieve.analysis.line'].create({

                'parent_id_gsa': record.id,

                # HYDROMETER SIZE
                'sieve_size': str(round(h.diameter_soil, 4)),

                # IMPORTANT
                'passing_percent': round(h.n_corrected, 3),

                # FLAG
                'is_hydrometer': True,

                # KEEP 0
                'wt_retained': 0.0,
            })

    def action_remove_n_corrected(self):
     for record in self:

        record.sieve_analysis_child_lines_gsa.filtered(
            lambda l: l.is_hydrometer
        ).unlink()

    



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

    

    # def calculate_sieve_gsa(self): 
    #     for record in self:

    #         previous_cumulative = 0.0  

    #         for line in record.sieve_analysis_child_lines_gsa:

    #             print("Rows", str(line.percent_retained))

    #             previous_line = line.serial_no - 1

    #             if previous_line == 0:
    #                 cumulative_retained = line.percent_retained or 0.0

    #             else:
    #                 previous_line_record = self.env['gsa.lab.sieve.analysis.line'].sudo().search([
    #                     ("serial_no", "=", previous_line),
    #                     ("parent_id_gsa", "=", record.id)   # ✅ FIX HERE
    #                 ], limit=1)

    #                 if previous_line_record:
    #                     previous_cumulative = previous_line_record.cumulative_retained or 0.0

    #                 cumulative_retained = previous_cumulative + (line.percent_retained or 0.0)

    #             passing_percent = 100 - cumulative_retained

    #             line.write({
    #                 'cumulative_retained': round(cumulative_retained, 2),
    #                 'passing_percent': round(passing_percent, 2),
    #             })

    #             print("Updated Cumulative Retained:", cumulative_retained)
    #             print("Updated Passing Percent:", passing_percent)

    #             previous_cumulative = cumulative_retained

    def calculate_sieve_gsa(self):

     for record in self:

        previous_cumulative = 0.0

        lines = record.sieve_analysis_child_lines_gsa.sorted('serial_no')

        for line in lines:

            # Step 1: cumulative weight retained
            previous_cumulative += line.wt_retained or 0.0

            # Step 2: cumulative % retained
            if record.wt_of_samp:
                cumulative_retained = (
                    previous_cumulative / record.wt_of_samp
                ) * 100
            else:
                cumulative_retained = 0.0

            # Step 3: passing %
            passing_percent = 100 - cumulative_retained

            # Step 4: write values
            line.write({

                # cumulative weight retained
                'percent_retained': round(previous_cumulative, 3),

                # cumulative % retained
                'cumulative_retained': round(cumulative_retained, 3),

                # % passing
                'passing_percent': round(passing_percent, 3),

            })

            print("Sieve Size :", line.sieve_size)
            print("Wt Retained :", line.wt_retained)
            print("Cum Weight :", previous_cumulative)
            print("Cum % :", cumulative_retained)
            print("Passing % :", passing_percent)

    

    



  


   

class SoilSieveAnalysisLineGSA(models.Model):
    _name = "gsa.lab.sieve.analysis.line"
    # parent_id = fields.Many2one('mechanical.gsa.line', string="Parent Id")

    parent_id_gsa = fields.Many2one(
        'mechanical.gsa.line',
        string="GSA Line",
        ondelete='cascade'
    )

    lab_id = fields.Char(string="LAB ID")

    wt_of_samp = fields.Float(string="Weight of total sample (gm)")

    temp = fields.Float("Temp °c" )
    humidity = fields.Float("Humidity %" )

    is_hydrometer = fields.Boolean(
    string="Hydrometer Row",
    default=False
)

    



    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size")
    wt_retained = fields.Float(string="Soil Retained wt",digits=(12,3))
    percent_retained = fields.Float(string='Cumulative Wt. retained',compute="_compute_percent_retained1",digits=(12,2) )
    cumulative_retained = fields.Float(string="Cumulative % retained",compute="_compute_cumulative_retained" , store=True)
    passing_percent = fields.Float(string="% Passing ",digits=(12,3),store=True,compute="_compute_passing_percent")

    

    
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




    # @api.depends('cumulative_retained')
    # def _compute_passing_percent(self):
    #  for record in self:
    #     record.passing_percent = round(
    #         100 - record.cumulative_retained,
    #         3
    #     )

    @api.depends(
    'cumulative_retained',
    'is_hydrometer'
)
    def _compute_passing_percent(self):

     for record in self:

        # ✅ DO NOT RECALCULATE HYDROMETER ROWS
        if record.is_hydrometer:
            continue

        record.passing_percent = round(
            100 - record.cumulative_retained,
            3
        )





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

    m_4 = fields.Float(string="M",digits=(12,4))
    c_4 = fields.Float(string="C",digits=(12,4))

    after_m_4 = fields.Float(string="M",digits=(12,4))
    after_c_4 = fields.Float(string="C",digits=(12,4))


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
    eff_depth = fields.Float(string='Effective Depth',digits=(12,1) ,compute="_compute_eff_depth",store=True)
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

    # @api.depends('men_corrected', 'time')
    # def _compute_eff_depth(self):
    #     for rec in self:
    #         if rec.men_corrected:
    #             rec.eff_depth = (-0.3444 * rec.men_corrected) + (
    #                 21.736 if rec.time in (8.0, 15.0, 30.0, 60.0, 120.0, 240.0, 1440.0)
    #                 else 20.256
    #             )
    #         else:
    #             rec.eff_depth = 0.0

    @api.depends(
    'men_corrected',
    'time',
    'parent_id_gsa.m_4',
    'parent_id_gsa.c_4',
    'parent_id_gsa.after_m_4',
    'parent_id_gsa.after_c_4'
    )
    def _compute_eff_depth(self):

        valid_times = (8, 15, 30, 60, 120, 240, 1440)

        for rec in self:

            if not rec.men_corrected:
                rec.eff_depth = 0.0
                continue

            if int(rec.time or 0) in valid_times:
                rec.eff_depth = (
                    (rec.parent_id_gsa.m_4 or 0.0) * rec.men_corrected
                ) + (rec.parent_id_gsa.c_4 or 0.0)
            else:
                rec.eff_depth = (
                    (rec.parent_id_gsa.after_m_4 or 0.0) * rec.men_corrected
                ) + (rec.parent_id_gsa.after_c_4 or 0.0)

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



class SoilGSALINE1(models.Model):
    _name = "mechanical.gsa.particle.line"
    parent_id = fields.Many2one(
        'mechanical.soil1',
        string="Parent Soil",
        ondelete='cascade'
    )

    


   
    bh_id = fields.Char(string="BH ID",compute="_compute_gsa1",store=True)
    lab_id = fields.Char(string="LAB ID")
    sample_depth = fields.Char(string="Sample Depth (m)",compute="_compute_gsa1",store=True)
    sample_details = fields.Char(string="Sample Details (m)",compute="_compute_gsa1",store=True)
    d_10 = fields.Float(string="D10",digits=(12,3))
    d_30 = fields.Float(string="D30",digits=(12,3))
    d_60 = fields.Float(string="D60",digits=(12,3))

    c_u = fields.Float(string="Cu")
    c_c = fields.Float(string="Cc")

    meniscus_corre = fields.Float(string="Meniscus correction, Cm",digits=(12,1))

    dispersion = fields.Float(string="Dispersing agent correction, x",digits=(12,3))

    temp_corre = fields.Float("Temperature Correction, Mt",digits=(12,4) )

    @api.depends('lab_id')
    def _compute_gsa1(self):
        ReviewLine = self.env['sample.request.review.lines']

        for line in self:
            line.bh_id = False
            line.sample_depth = False
            line.sample_details = False

            if not line.lab_id:
                continue

            review_line = ReviewLine.search(
                [('lab_id', '=', line.lab_id)],
                order='id desc',
                limit=1
            )

            if review_line:
                line.bh_id = review_line.source        # BH ID / Location
                line.sample_depth = review_line.depth         # Depth (m)
                line.sample_details = review_line.sample_details         # Depth (m)





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
    lab_no = fields.Char(string="Lab No.")
    room_temp = fields.Float(string="Room Temperature (°C)")
    bottle_no = fields.Char(string="Bottle No.")

    wt_empty_bottle = fields.Float(string="Empty Wt. of Bottle (W1)")
    wt_bottle_dry_soil = fields.Float(string="Bottle + dry soil (W2)")
    wt_bottle_dry_soil_water = fields.Float(string="Bottle + Dry soil + Water (W3)")
    wt_bottle_water = fields.Float(string="Bottle + Water (Tap) (W4)")

    specific_gravity = fields.Float( string="Specific Gravity (G)", compute="_compute_specific_gravity", store=True, readonly=True,digits=(12,3))
    density_water = fields.Float( string="Density of water at room temp (gm/cc)", compute="_compute_density_water", store=True,  readonly=True, digits=(12,5))
    corr_specific_gravity = fields.Float(string="Corrected Specific Gravity (G')",compute="_compute_corr_specific_gravity", store=True, readonly=True,digits=(12,3)
 )
    avg_corr_specific_gravity = fields.Float(
        string="Average corrected Specific Gravity",
        store=True,
        readonly=True,digits=(12,3)
    )

   
    @api.depends(
        "wt_empty_bottle",
        "wt_bottle_dry_soil",
        "wt_bottle_dry_soil_water",
        "wt_bottle_water",
    )
    def _compute_specific_gravity(self):
        for rec in self:
            W1 = rec.wt_empty_bottle or 3.0
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

    parent_id = fields.Many2one("mechanical.soil1", string="Parent Test", ondelete="cascade", required=True)
    serial_no = fields.Integer(string="Sr.No", readonly=True)
    lab_id = fields.Char(string="Lab No.")

    vd = fields.Float(string="Vd")  
    vk = fields.Float(string="Vk") 

    free_swell = fields.Float(string="Free swell (%)", compute="_compute_free_swell", store=True, readonly=True)

    is_ok = fields.Boolean(string="TRUE/FALSE",compute="_compute_is_ok",store=True,
    readonly=True)

    is_ok_display = fields.Char(string="TRUE/FALSE",compute="_compute_is_ok_display")

    free_swell_display = fields.Char(string="Free Swell (%)",compute="_compute_free_swell_display")

    @api.depends("free_swell")
    def _compute_free_swell_display(self):
     for rec in self:
        if rec.free_swell is False or rec.free_swell < 0:
            rec.free_swell_display = "--"
        else:
            rec.free_swell_display = "%.2f" % rec.free_swell

    @api.depends("vd", "vk")
    def _compute_free_swell(self):
     for rec in self:
        if rec.vk:
            rec.free_swell = ((rec.vd or 0.0) - rec.vk) / rec.vk * 100
        else:
            rec.free_swell = 0.0
            

    @api.depends("free_swell")
    def _compute_is_ok(self):
      for rec in self:
        val = rec.free_swell

        rec.is_ok = bool(val is not None and val >= 1 and val <= 200)

    @api.depends("is_ok")
    def _compute_is_ok_display(self):
     for rec in self:
        rec.is_ok_display = "TRUE" if rec.is_ok else "FALSE"

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
    parent_id_consolidation = fields.Many2one('consolidation.line',string="Parent Id")

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
        if vals.get('parent_id_consolidation'):
            existing_records = self.search([('parent_id_consolidation', '=', vals['parent_id_consolidation'])])
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
    parent_id_con_un = fields.Many2one('consolidation.line',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    time_m = fields.Float(string="Time (Minutes)")
    load_8_0_4_0 = fields.Float(string="8.0-4.0" ,digits=(8,3))
    load_4_0_8_0 = fields.Float(string="4.0-2.0" ,digits=(8,3))
    load_2_0_4_0 = fields.Float(string="2.0-1.0" ,digits=(8,3))
    load_1_0_2_0 = fields.Float(string="1.0-0.5" ,digits=(8,3))
    load_0_5_1_0 = fields.Float(string="0.5-0.2" ,digits=(8,3))
    load_0_2_0_5 = fields.Float(string="0.2-0.1" ,digits=(8,3))
    load_0_1_0_2 = fields.Float(string="0.1-0.0" ,digits=(8,3))
    # load_0_05_0_1 = fields.Float(string="0.05-0.1",digits=(8,3))
    setting_load = fields.Float(string="Setting Load",digits=(8,3))


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id_con_un'):
            existing_records = self.search([('parent_id_con_un', '=', vals['parent_id_con_un'])])
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
    parent_id_con_out = fields.Many2one('consolidation.line',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)
    sequence = fields.Integer(default=10)  # 🔥 MUST

    cylces=  fields.Char(string="Cycles" )

    applied_pressure = fields.Float(string="Applied Pressure kg/cm²" , digits=(8,2))
    final_read = fields.Float(string="Final Dial Reading mm" ,digits=(8,3),compute="_compute_final_read", store=True)
    delta_h = fields.Float(string=" Δ𝐻 cm" ,digits=(8,4),compute="_compute_delta_h" ,store=True)
    specimen_height = fields.Float(string="Specimen Height (H) cm" ,digits=(8,6) , compute="_compute_specimen_height" ,store=True )
    e_void = fields.Float(string="e = (H/Hs)-1" ,digits=(8,6) , compute="_compute_e_void1" ,store=True)
    change_void = fields.Float(string="de", digits=(16,10), compute="_compute_change_void" ,store=True)
    d_sigma = fields.Float(string=" dσ" ,digits=(16,6) , compute="_compute_d_sigma" ,store=True)
    av = fields.Float(string="aᵥ (cm²/kg)" ,digits=(16,6) ,compute="_compute_av" ,store=True)
    mv = fields.Float("mᵥ (cm²/kg)", digits=(8, 4),compute="_compute_mv" ,store=True)

    t90 = fields.Float("t₉₀ (min)", digits=(8, 3))
    Hav = fields.Float("Hav (cm)", digits=(8, 3))

    cv = fields.Float("cᵥ (cm²/sec)", digits=(16, 4), compute="_compute_cv" ,store=True)
    cc = fields.Float("cc (cm²/sec)", digits=(8, 3), compute="_compute_cc" ,store=True)

    @api.depends(
    'applied_pressure', 'cylces',
    'parent_id_con_out.consolidation_ids.load_0_05_0_1',
    'parent_id_con_out.consolidation_ids.load_0_1_0_2',
    'parent_id_con_out.consolidation_ids.load_0_2_0_5',
    'parent_id_con_out.consolidation_ids.load_0_5_1_0',
    'parent_id_con_out.consolidation_ids.load_1_0_2_0',
    'parent_id_con_out.consolidation_ids.load_2_0_4_0',
    'parent_id_con_out.consolidation_ids.load_4_0_8_0',
    'parent_id_con_out.consolidation_unloading_ids.load_8_0_4_0',
    'parent_id_con_out.consolidation_unloading_ids.load_4_0_8_0',
    'parent_id_con_out.consolidation_unloading_ids.load_2_0_4_0',
    'parent_id_con_out.consolidation_unloading_ids.load_1_0_2_0',
    'parent_id_con_out.consolidation_unloading_ids.load_0_5_1_0',
    'parent_id_con_out.consolidation_unloading_ids.load_0_2_0_5',
    'parent_id_con_out.consolidation_unloading_ids.load_0_1_0_2',
    # 'parent_id_con_out.consolidation_unloading_ids.load_0_05_0_1',
)
    def _compute_final_read(self):
     for line in self:
        parent = line.parent_id_con_out
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
    'parent_id_con_out.consolidation_output_ids.final_read',
    'parent_id_con_out.consolidation_output_ids.applied_pressure',
    'parent_id_con_out.consolidation_output_ids.cylces',
    'parent_id_con_out.consolidation_output_ids.serial_no')
    def _compute_delta_h(self):
     for line in self:
        parent = line.parent_id_con_out
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
                line.delta_h = round((row_8.final_read - line.final_read) / 10.0 , 4)
            else:
                line.delta_h = 0.0
            continue

        # default rule: (prevC - currC) / 10
        if prev and prev.final_read not in (False, None) and line.final_read not in (False, None):
            line.delta_h = round((prev.final_read - line.final_read) / 10.0 , 4)
        else:
            line.delta_h = 0.0

    @api.depends(
    'delta_h', 'parent_id_con_out.consolidation_height',
    'parent_id_con_out.consolidation_output_ids.delta_h',
    'parent_id_con_out.consolidation_output_ids.applied_pressure',
    'parent_id_con_out.consolidation_output_ids.cylces',
    'parent_id_con_out.consolidation_output_ids.serial_no'
)
    def _compute_specimen_height(self):
     for line in self:
        parent = line.parent_id_con_out
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
        line.specimen_height = round(base_H - (line.delta_h or 0.0), 6)


    

    @api.depends('specimen_height', 'parent_id_con_out.con_height_solid')
    def _compute_e_void1(self):
        for line in self:
            Hs = line.parent_id_con_out.con_height_solid or 0.0

            if Hs:
                value = (line.specimen_height / Hs) - 1.0

                # convert to string with enough precision
                value_str = f"{value:.7f}"

                # split decimal
                int_part, dec_part = value_str.split('.')

                # take first 3 decimals
                first_four  = int(dec_part[:6])

                # check 4th decimal
                fifth  = int(dec_part[6]) if len(dec_part) > 6 else 0

                # apply custom rule
                if fifth >= 1:
                    rounded = first_four  + 1
                else:
                    rounded = first_four 

                line.e_void = float(f"{int_part}.{str(rounded).zfill(6)}")

            else:
                line.e_void = 0.0

    @api.depends('e_void', 'applied_pressure', 'cylces',
             'parent_id_con_out.consolidation_output_ids.e_void',
             'parent_id_con_out.consolidation_output_ids.applied_pressure',
             'parent_id_con_out.consolidation_output_ids.cylces',
             'parent_id_con_out.consolidation_output_ids.serial_no')
    def _compute_change_void(self):
     for line in self:
        parent = line.parent_id_con_out
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
            line.change_void = round((prev_line.e_void or 0.0) - (line.e_void or 0.0) , 10)
        else:
            line.change_void = 0.0


    @api.depends(
        'applied_pressure',
        'parent_id_con_out.consolidation_output_ids.applied_pressure',
        'parent_id_con_out.consolidation_output_ids.serial_no',
    )
    def _compute_d_sigma(self):
        for line in self:
            parent = line.parent_id_con_out
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


    @api.depends('av', 'parent_id_con_out.con_swell_void_ratio')
    def _compute_mv(self):
        for line in self:
            e0 = line.parent_id_con_out.con_swell_void_ratio or 0.0
            denom = 1.0 + e0
            if denom:
                line.mv = line.av / denom
            else:
                line.mv = 0.0

    Hav = fields.Float("Hav (cm)", digits=(8, 4), compute="_compute_Hav", store=True)

    @api.depends(
    'specimen_height',
    'parent_id_con_out.consolidation_output_ids.specimen_height',
    'parent_id_con_out.consolidation_output_ids.serial_no',)
    def _compute_Hav(self):
     for line in self:
        parent = line.parent_id_con_out
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
    'parent_id_con_out.consolidation_output_ids.applied_pressure',
    'parent_id_con_out.consolidation_output_ids.serial_no',
)
    def _compute_cc(self):
     for line in self:
        de = line.change_void or 0.0
        p2 = line.applied_pressure or 0.0

        # previous line in same parent (by serial_no)
        p1 = 0.0
        if line.parent_id_con_out:
            prev = line.parent_id_con_out.consolidation_output_ids \
                .filtered(lambda l: l.serial_no == line.serial_no - 1)[:1]
            if prev:
                p1 = prev.applied_pressure or 0.0

        if de and p2 and p1 and p2 != p1:
            line.cc = de / log10(p2 / p1)
        else:
            line.cc = 0.0

    ce = fields.Float(related='parent_id_con_out.ce', readonly=True)
    cr = fields.Float(related='parent_id_con_out.cr', readonly=True)


    delta_cc = fields.Float(
    string="Delta Cc",
    digits=(16, 6),
    compute="_compute_delta_cc",
    store=True
)
    @api.depends(
    'cc',
    'parent_id_con_out.consolidation_output_ids.cc',
    'parent_id_con_out.consolidation_output_ids.serial_no',
    )
    def _compute_delta_cc(self):
     for line in self:
        line.delta_cc = 0.0
        parent = line.parent_id_con_out
        if not parent:
            continue

        rows = list(parent.consolidation_output_ids.sorted('serial_no'))
        if not rows:
            continue

        try:
            idx = rows.index(line)
        except ValueError:
            continue

        # First row -> 0 (Excel behavior)
        if idx == 0:
            line.delta_cc = 0.0
            continue

        prev = rows[idx - 1]

        # Excel: IF(Ni=0,0,Ni-N(i-1))
        if not line.cc:
            line.delta_cc = 0.0
        else:
            line.delta_cc = round((line.cc or 0.0) - (prev.cc or 0.0), 6)

    
    








    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id_con_out'):
            existing_records = self.search([('parent_id_con_out', '=', vals['parent_id_con_out'])])
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
    parent_id_swelling = fields.Many2one('swelling.pressure.line',string="Parent Id")

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
        if vals.get('parent_id_swelling'):
            existing_records = self.search([('parent_id_swelling', '=', vals['parent_id_swelling'])])
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
    parent_id_unloading = fields.Many2one('swelling.pressure.line',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    time_m = fields.Float(string="Time (Minutes)")
    load_8_0_4_0 = fields.Float(string="8.0-4.0" ,digits=(8,3))
    load_4_0_8_0 = fields.Float(string="4.0-2.0" ,digits=(8,3))
    load_2_0_4_0 = fields.Float(string="2.0-1.0" ,digits=(8,3))
    load_1_0_2_0 = fields.Float(string="1.0-0.5" ,digits=(8,3))
    load_0_5_1_0 = fields.Float(string="0.5-0.2" ,digits=(8,3))
    load_0_2_0_5 = fields.Float(string="0.2-0.1" ,digits=(8,3))
    load_0_1_0_2 = fields.Float(string="0.1-0.0" ,digits=(8,3))
    # load_0_05_0_1 = fields.Float(string="0.05-0.1",digits=(8,3))
    setting_load = fields.Float(string="Setting Load",digits=(8,3))


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id_unloading'):
            existing_records = self.search([('parent_id_unloading', '=', vals['parent_id_unloading'])])
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
    parent_id_output = fields.Many2one('swelling.pressure.line',string="Parent Id")

   

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

    cv = fields.Float("cᵥ (cm²/sec)", digits=(10, 6), compute="_compute_cv", store=True)
    cc = fields.Float("cᵥ (cm²/sec)", digits=(8, 3), compute="_compute_Cc", store=True)

    @api.depends(
    'applied_pressure', 'cylces',
    'parent_id_output.swelling_ids.load_0_05_0_1',
    'parent_id_output.swelling_ids.load_0_1_0_2',
    'parent_id_output.swelling_ids.load_0_2_0_5',
    'parent_id_output.swelling_ids.load_0_5_1_0',
    'parent_id_output.swelling_ids.load_1_0_2_0',
    'parent_id_output.swelling_ids.load_2_0_4_0',
    'parent_id_output.swelling_ids.load_4_0_8_0',
    'parent_id_output.swelling_unloading_ids.load_8_0_4_0',
    'parent_id_output.swelling_unloading_ids.load_4_0_8_0',
    'parent_id_output.swelling_unloading_ids.load_2_0_4_0',
    'parent_id_output.swelling_unloading_ids.load_1_0_2_0',
    'parent_id_output.swelling_unloading_ids.load_0_5_1_0',
    'parent_id_output.swelling_unloading_ids.load_0_2_0_5',
    'parent_id_output.swelling_unloading_ids.load_0_1_0_2',
    # 'parent_id_output.swelling_unloading_ids.load_0_05_0_1',
)
    def _compute_final_read(self):
     for line in self:
        parent = line.parent_id_output
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
             'parent_id_output.swelling_output_ids.final_read',
             'parent_id_output.swelling_output_ids.applied_pressure',
             'parent_id_output.swelling_output_ids.cylces')
    def _compute_delta_h(self):
     for line in self:
        parent = line.parent_id_output
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

    

    @api.depends('delta_h', 'parent_id_output.swelling_height',
             'parent_id_output.swelling_output_ids.delta_h',
             'parent_id_output.swelling_output_ids.applied_pressure',
             'parent_id_output.swelling_output_ids.cylces')
    def _compute_specimen_height(self):
     for line in self:
        parent = line.parent_id_output
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


    

    @api.depends('specimen_height', 'parent_id_output.height_solid')
    def _compute_e_void(self):
     for line in self:
        Hs = line.parent_id_output.height_solid or 0.0
        if Hs:
            line.e_void = (line.specimen_height / Hs) - 1.0
        else:
            line.e_void = 0.0

    

   

    @api.depends(
    'e_void', 'applied_pressure', 'cylces',
    'parent_id_output.swelling_output_ids.e_void',
    'parent_id_output.swelling_output_ids.applied_pressure',
    'parent_id_output.swelling_output_ids.cylces'
)
    def _compute_change_void(self):
     for line in self:
        parent = line.parent_id_output
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
    'parent_id_output.swelling_output_ids.applied_pressure',
    'parent_id_output.swelling_output_ids.cylces'
)
    def _compute_d_sigma(self):
     for line in self:
        parent = line.parent_id_output
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


    @api.depends('av', 'parent_id_output.swell_void_ratio')
    def _compute_mv(self):
        for line in self:
            e0 = line.parent_id_output.swell_void_ratio or 0.0
            denom = 1.0 + e0
            if denom:
                line.mv = line.av / denom
            else:
                line.mv = 0.0

    Hav = fields.Float("Hav (cm)", digits=(8, 4), compute="_compute_Hav", store=True)

    @api.depends(
    'specimen_height',
    'parent_id_output.swelling_output_ids.specimen_height',
    'parent_id_output.swelling_output_ids.serial_no',)
    def _compute_Hav(self):
     for line in self:
        parent = line.parent_id_output
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
        H_av = round(line.Hav or 0.0, 3)   # match Excel rounding
        t_90 = line.t90 or 0.0

        if H_av > 0 and t_90 > 0:
            line.cv = round(
                0.848 * (H_av / 2.0) ** 2 / (t_90 * 60.0),
                4  # same precision as Excel column
            )
        else:
            line.cv = 0.0


    

    @api.depends(
    'change_void', 'applied_pressure', 'cylces',
    'parent_id_output.swelling_output_ids.change_void',
    'parent_id_output.swelling_output_ids.applied_pressure',
    'parent_id_output.swelling_output_ids.cylces',
    'parent_id_output.swelling_output_ids.serial_no',)
    def _compute_Cc(self):
     for line in self:
        line.cc = 0.0
        parent = line.parent_id_output
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
        if vals.get('parent_id_output'):
            existing_records = self.search([('parent_id_output', '=', vals['parent_id_output'])])
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
    parent_id_table = fields.Many2one('swelling.pressure.line',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    

    cylces=  fields.Char(string="Cycles" )

    applied_pressure = fields.Float(string="Applied Pressure kg/cm²" , digits=(8,2))
    final_read = fields.Float(string="Final Dial Reading mm" ,digits=(8,3),compute="_compute_final_read", store=True)
    delta_h = fields.Float(string=" Δ𝐻 cm" ,digits=(8,3),compute="_compute_delta_h" ,store=True)

    @api.depends('applied_pressure', 'parent_id_table.swelling_ids')
    def _compute_final_read(self):
        for line in self:
            final = 0.0
            if line.parent_id_table and line.applied_pressure:
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
                    records = line.parent_id_table.swelling_ids.filtered(lambda r: getattr(r, field))
                    if records:
                        final = records.sorted('time_m')[-1][field]
            line.final_read = final

    @api.depends('final_read', 'parent_id_table.initial_read')
    def _compute_delta_h(self):
        for line in self:
            if line.final_read and line.parent_id_table.initial_read:
                line.delta_h = line.final_read - line.parent_id_table.initial_read
            else:
                line.delta_h = 0.0


    



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id_table'):
            existing_records = self.search([('parent_id_table', '=', vals['parent_id_table'])])
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
    parent_id_perm = fields.Many2one('perm.head.line',string="Parent Id",ondelete='cascade')

    serial_no = fields.Integer(string="Trial No",readonly=True, copy=False, default=1)

    

    initial_head = fields.Float(string="Initial Head (cm) (H1)" , digits=(8,0))
    final_head = fields.Float(string="Final Head (cm) (H2)" , digits=(8,0))
    initial_head1 = fields.Float(string="Initial Head (cm) (H1)" , digits=(8,0) ,compute="_compute_heads" ,store=True)
    final_head2 = fields.Float(string="Final Head (cm) (H2)" , digits=(8,0) , compute="_compute_heads" ,store=True)
    time = fields.Float(string="Time (sec)", digits=(12,2))
    permeability = fields.Float("Permeability (cm/s)",compute="_compute_permeability", digits=(16, 9), store=True)
    

    @api.depends('initial_head','final_head','parent_id_perm.distance')
    def _compute_heads(self):
        for line in self:
            if line.initial_head and line.final_head and line.parent_id_perm.distance :    
                line.initial_head1 =  line.initial_head + line.parent_id_perm.distance
                line.final_head2 =  line.final_head +  line.parent_id_perm.distance

    @api.depends('parent_id_perm.area_pipe', 'parent_id_perm.area_soil_samp',
             'parent_id_perm.length_soil', 'time', 'initial_head1', 'final_head2')
    def _compute_permeability(self):
     for line in self:
        p = line.parent_id_perm
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
        if vals.get('parent_id_perm'):
            existing_records = self.search([('parent_id_perm', '=', vals['parent_id_perm'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SoilPermeabilityTestLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

# --- NEW CLASS FOR LINES (TABLE) ---
class TriaxialTestLine(models.Model):
    _name = 'triaxial.test.line'
    _description = 'Triaxial Test Readings'

    parent_id_triaxial = fields.Many2one('triaxial.shear.line', string="Parent")

    

    # 1. Displacement / Strain
    horizontal_dial = fields.Float(string="Horizantal Dial Reading",compute="_compute_dial_reading",store=True)
    strain = fields.Float(string="Strain",  digits=(10, 4))
    
    # 2. Corrected Area (Calculated)
    corrected_area = fields.Float(string="Corrected Area (cm²)",  digits=(10, 3),compute="_compute_corrected_area", store=True)

    # ==================================
    # 0.5 kg/cm² Pressure
    # ==================================
    pr_05 = fields.Float(string="Proving ring reading (0.5)")
    shear_stress_05 = fields.Float(string="Shear stress (kg/sq.cm)(0.5)",compute="_compute_shear_stress_05",  digits=(10, 3), store=True)

    # ==================================
    # 1.0 kg/cm² Pressure
    # ==================================
    pr_10 = fields.Float(string="Proving ring reading(1)")
    shear_stress_10 = fields.Float(string="Shear stress (kg/sq.cm)(1)",compute="_compute_shear_stress_10",  digits=(10, 3), store=True)

    # ==================================
    # 1.5 kg/cm² Pressure
    # ==================================
    pr_15 = fields.Float(string="Proving ring reading(1.5)")
    shear_stress_15 = fields.Float(string="Shear stress (kg/sq.cm)(1.5)",compute="_compute_shear_stress_15",  digits=(10, 3), store=True)

    pr_5 = fields.Float(string="0.5",compute="_compute_pr_5_calculation",store=True,digits=(12,9))
    pr_1 = fields.Float(string="1.0",compute="_compute_pr_1_calculation",store=True,digits=(12,9))
    pr_1_5 = fields.Float(string="1.5",compute="_compute_pr_1_5_calculation",store=True,digits=(12,9))


    @api.depends('pr_05', 'corrected_area', 'parent_id_triaxial.triaxial_test_line_ids','parent_id_triaxial.m_traxial','parent_id_triaxial.c_traxial')
    def _compute_pr_5_calculation(self):
        # Parent wise group kara (Optimization sathi)
        for parent in self.mapped('parent_id_triaxial'):
            # Saglya lines sequence madhe ghene
            lines = parent.triaxial_test_line_ids
            
            for i, line in enumerate(lines):
                # --- 1. FIRST LINE (Index 0) ---
                if i == 0:
                    line.pr_5 = 0.0
                
                else:
                 
                    numerator = (((line.pr_05 * 5.0) * line.parent_id_triaxial.m_traxial) + line.parent_id_triaxial.c_traxial)
                    
                
                    denominator = 9.81 * line.corrected_area
                    
                
                    if denominator > 0:
                        line.pr_5 = numerator / denominator
                    else:
                        line.pr_5 = 0.0

    @api.depends('pr_10', 'corrected_area', 'parent_id_triaxial.triaxial_test_line_ids','parent_id_triaxial.m_traxial','parent_id_triaxial.c_traxial')
    def _compute_pr_1_calculation(self):
        # Optimization sathi Parent wise group kara
        for parent in self.mapped('parent_id_triaxial'):
            # Saglya lines sequence madhe ghene
            lines = parent.triaxial_test_line_ids
            
            for i, line in enumerate(lines):
                # --- FIRST LINE (Index 0) ---
                if i == 0:
                    line.pr_1 = 0.0
                
                # --- SECOND LINE ONWARDS ---
                else:
                   
                    numerator = (((line.pr_10 * 5.0) * line.parent_id_triaxial.m_traxial) + line.parent_id_triaxial.c_traxial)
                    denominator = 9.81 * line.corrected_area
                    
                    if denominator > 0:
                        line.pr_1 = numerator / denominator
                    else:
                        line.pr_1 = 0.0

    @api.depends('pr_15', 'corrected_area', 'parent_id_triaxial.triaxial_test_line_ids','parent_id_triaxial.m_traxial','parent_id_triaxial.c_traxial')
    def _compute_pr_1_5_calculation(self):
        # Optimization sathi Parent wise group kara
        for parent in self.mapped('parent_id_triaxial'):
            # Saglya lines sequence madhe ghene
            lines = parent.triaxial_test_line_ids
            
            for i, line in enumerate(lines):
                # --- FIRST LINE (Index 0) ---
                if i == 0:
                    line.pr_1 = 0.0
                
                # --- SECOND LINE ONWARDS ---
                else:

                    
                    numerator = (((line.pr_15 * 5.0) * line.parent_id_triaxial.m_traxial) + line.parent_id_triaxial.c_traxial)
                    denominator = 9.81 * line.corrected_area
                    
                    if denominator > 0:
                        line.pr_1_5 = numerator / denominator
                    else:
                        line.pr_1_5 = 0.0

    # 2. Compute Function
    @api.depends('parent_id_triaxial.triaxial_test_line_ids')
    def _compute_dial_reading(self):
        # Sagle unique parents ghene (Optimization sathi)
        for parent in self.mapped('parent_id_triaxial'):
            
            current_val = 0.0
            
          
            for i, line in enumerate(parent.triaxial_test_line_ids):
                
               
                if i == 0:
                   
                    if not line.horizontal_dial:
                        line.horizontal_dial = 0.0
                    current_val = line.horizontal_dial
                
                else:
                 
                    new_val = current_val + 25.0
                    line.horizontal_dial = new_val
                    current_val = new_val

    @api.depends('horizontal_dial', 'parent_id_triaxial.area1_triaxial', 'parent_id_triaxial.height_triaxial', 'parent_id_triaxial.triaxial_test_line_ids')
    def _compute_corrected_area(self):
        # Parent groups madhe loop firvu (Optimization)
        for parent in self.mapped('parent_id_triaxial'):
            
            lines = parent.triaxial_test_line_ids
            
            # Initial Area aani Height Parent madhun ghene
            A0 = parent.area1_triaxial or 0.0
            H0 = parent.height_triaxial or 1.0  # Divide by zero talnyasathi default 1
            
            for i, line in enumerate(lines):
               
                if i == 0:
                    # Formula: area1_triaxial / 100
                    line.corrected_area = A0 / 100.0
                
               
                else:
                   
                    change_in_length = line.horizontal_dial / 100.0
                    
                    if H0 > 0:
                        strain = change_in_length / H0
                    else:
                        strain = 0.0

                  
                    if (1 - strain) > 0:
                        corrected_area_val = A0 / (1 - strain)
                        line.corrected_area = corrected_area_val / 100.0
                    else:
                        # Fallback jar strain 1 peksha jast zala tar
                        line.corrected_area = 0.0

    # --- CALCULATION LOGIC ---
    @api.depends('pr_5', 'parent_id_triaxial.rise_force_triaxial_test')
    def _compute_shear_stress_05(self):
        for line in self:
           
            rise_force = line.parent_id_triaxial.rise_force_triaxial_test or 0.0
            
           
            if line.pr_5:
              
                extra_force = line.pr_5 * rise_force
                line.shear_stress_05 = line.pr_5 + extra_force
            else:
                line.shear_stress_05 = 0.0


    @api.depends('pr_1', 'parent_id_triaxial.rise_force_triaxial_test')
    def _compute_shear_stress_10(self):
        for line in self:
           
            rise_force = line.parent_id_triaxial.rise_force_triaxial_test or 0.0
            
           
            if line.pr_1:
               
                extra_force = line.pr_1 * rise_force
                line.shear_stress_10 = line.pr_1 + extra_force
            else:
                line.shear_stress_10 = 0.0

    @api.depends('pr_1_5', 'parent_id_triaxial.rise_force_triaxial_test')
    def _compute_shear_stress_15(self):
        for line in self:
           
            rise_force = line.parent_id_triaxial.rise_force_triaxial_test or 0.0
            
           
            if line.pr_1_5:
              
                extra_force = line.pr_1_5 * rise_force
                line.shear_stress_15 = line.pr_1_5 + extra_force
            else:
                line.shear_stress_15 = 0.0




class LabOptionLine(models.Model):
    _name = 'lab.option.line'
    _description = 'Lab Options'
    _rec_name = 'name'  # Dropdown मध्ये हे नाव दिसेल

    name = fields.Char(string="Value")
    parent_id = fields.Many2one('mechanical.soil1', string="Parent")




                










# PLASTIC LIMIT LINE (PL Sheet)
class LabAtterbergPlLine(models.Model):
    _name = 'lab.atterberg.pl.line'
    parent_id_ll = fields.Many2one('pl.line', string="Parent",ondelete='cascade')
   
    serial_no = fields.Integer(string="Sr. No",readonly=True, copy=False, default=1)
    container_no = fields.Char('Container No.')
    m1 = fields.Float('M1 (gm)', digits=(10,3))
    m2 = fields.Float('M2 (gm)', digits=(10,3))
    m3 = fields.Float('M3 (gm)', digits=(10,3))
    
  
    m3_m2 = fields.Float('M3-M2', digits=(10,3), compute='_compute_pl', store=True)
    m2_m1 = fields.Float('M2-M1', digits=(10,3), compute='_compute_pl', store=True)
    water_content = fields.Float('Water Content %', digits=(10,2), compute='_compute_pl', store=True)

    @api.depends('m1', 'm2', 'm3')
    def _compute_pl(self):
        for rec in self:
            rec.m3_m2 = rec.m3 - rec.m2 if rec.m3 and rec.m2 else 0.0
            rec.m2_m1 = rec.m2 - rec.m1 if rec.m2 and rec.m1 else 0.0
            rec.water_content = (rec.m3_m2 / rec.m2_m1 * 100) if rec.m2_m1 else 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(LabAtterbergPlLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



# LIQUID LIMIT LINE (LL Sheet)  
class LabAtterbergLlLine(models.Model):
    _name = 'lab.atterberg.ll.line'
    parent_id = fields.Many2one('ll.line', string="Parent")
    
   
    serial_no = fields.Integer(string="Sr. No",readonly=True, copy=False, default=1)
    blows = fields.Integer('No. of Blows')
    container_no = fields.Char('Container No.')
    m1 = fields.Float('M1 (gm)', digits=(10,3))
    m2 = fields.Float('M2 (gm)', digits=(10,3))
    m3 = fields.Float('M3 (gm)', digits=(10,3))
    
    
    m3_m2 = fields.Float('M3-M2', digits=(10,3), compute='_compute_ll', store=True)
    m2_m1 = fields.Float('M2-M1', digits=(10,3), compute='_compute_ll', store=True)
    water_content = fields.Float('Water Content %', digits=(10,2), compute='_compute_ll', store=True)

    @api.depends('m1', 'm2', 'm3')
    def _compute_ll(self):
        for rec in self:
            rec.m3_m2 = rec.m3 - rec.m2 if rec.m3 and rec.m2 else 0.0
            rec.m2_m1 = rec.m2 - rec.m1 if rec.m2 and rec.m1 else 0.0
            rec.water_content = (rec.m3_m2 / rec.m2_m1 * 100) if rec.m2_m1 else 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id_ll'):
            existing_records = self.search([('parent_id_ll', '=', vals['parent_id_ll'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(LabAtterbergLlLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1











class LabAtterbergSlLine(models.Model):
    _name = 'lab.atterberg.sl.line'
    
    parent_id_sl = fields.Many2one('sl.line', string="Parent",ondelete='cascade')
    serial_no = fields.Integer(string="Sr. No", readonly=True, default=1)
    


    container_no = fields.Char('Container No.')
    m1 = fields.Float('M1 (gm)')
    v1 = fields.Float('V1 (cm3)')
    m2 = fields.Float('M2 (gm)')
    m3 = fields.Float('M3 (gm)')
    v2 = fields.Float('V2 (cm3)')
    
    m3_m2 = fields.Float('M3-M2', compute='_compute_sl', store=True)
    m2_m1 = fields.Float('M2-M1', compute='_compute_sl', store=True)
    v1_v2 = fields.Float('V1-V2', compute='_compute_sl', store=True)
    water_content = fields.Float('Water Content %', digits=(10,2), compute='_compute_sl', store=True)
    shrinkage_ratio = fields.Float('Shrinkage Ratio', digits=(10,3), compute='_compute_sl', store=True)
    shrinkage_limit = fields.Float('SL %', digits=(10,2), compute='_compute_sl', store=True)

    # [PASTE THE _compute_sl METHOD ABOVE HERE]
    
    @api.depends('m1', 'm2', 'm3', 'v1', 'v2')
    def _compute_sl(self):
     for rec in self:
        # Safe values from your test: m1=33.17, v1=22, m2=76.22, m3=66.51, v2=17
        m1 = rec.m1 or 0.0
        m2 = rec.m2 or 0.0
        m3 = rec.m3 or 0.0
        v1 = rec.v1 or 0.0
        v2 = rec.v2 or 0.0
        
        # Excel column differences (display only)
        rec.m3_m2 = m3 - m2
        rec.m2_m1 = m2 - m1
        rec.v1_v2 = v1 - v2
        
        # **YOUR EXACT EXCEL FORMULAS:**
        # Water Content = ((M1-M3)/(M2-M3)) * 100
        dry_soil = m2 - m1  # 76.22 - 66.51 = 9.71
        if dry_soil > 0:
            rec.water_content = ((m3 - m2) / dry_soil) * 100  # (33.17-66.51)/9.71 * 100 = **72.34**
        else:
            rec.water_content = 0.0
        
        # Shrinkage Ratio = (M2-M3)/V2  
        if v2 > 0:
            rec.shrinkage_ratio = ((m2 - m1) / v2 ) # 9.71/17 = **0.571**
        else:
            rec.shrinkage_ratio = 0.0
        
        # Shrinkage Limit = Water Content - (SR * 100)
        v2_v1 = v1 - v2
        m2_m1 = m2 -m1
        if m2_m1 > 0:


            rec.shrinkage_limit =  round ((((m3 - m2) - (v2_v1 * 1)) /(m2 -m1)) * 100, 0)  # 9.71/17 = **0.571**

            
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

        return super(LabAtterbergSlLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


       
 













class SoilLightHeavyCompactionLine(models.Model):
    _name = "soil.light.heavy.compaction.line"
    parent_id_heavy = fields.Many2one('heavy.compaction.line',string="Parent Id")

    serial_no = fields.Integer(string="Trial No",readonly=True,compute="_compute_serial_no")

    @api.depends('parent_id_heavy.soil_light_heavy_lines')
    def _compute_serial_no(self):
     for record in self:
        parent = record.parent_id_heavy
        if not parent:
            continue

        # IMPORTANT: DO NOT SORT BY ID
        lines = parent.soil_light_heavy_lines

        for idx, line in enumerate(lines, start=1):
            line.serial_no = idx

    wet_soil_cylinder = fields.Float(string="Wet mass of soil + cylinder gm" , digits=(8,0) )

    wet_soil = fields.Float(string="Wet mass of soil  gm" , digits=(8,0) , compute="_compute_wet_soil" , store=True)

    bulk_density_light = fields.Float(string="Bulk density of soil  g/cc" , digits=(8,2) , compute="_compute_bulk_density_light" , store=True)

    can_no = fields.Float(string="Can no." , digits=(8,0))

    wet_soil_can = fields.Float(string="Wet soil + can" , digits=(8,3))
    dry_soil_can = fields.Float(string="Dry soil + Can" , digits=(8,3))
    empty_mass_can = fields.Float(string="Empty mass of can" , digits=(8,3))

    moisture_loss = fields.Float(string="Moisture loss" , digits=(8,3) , compute="_compute_moisture_fields" , store=True)
    dry_wt_soil = fields.Float(string="Dry wt. of soil, gm" , digits=(8,3), compute="_compute_moisture_fields" , store=True)
    moisture_content = fields.Float(string="Moisture content" , digits=(8,2), compute="_compute_moisture_fields" , store=True)

    avg_moisture_content = fields.Float(string="Average moisture content" , digits=(8,2))

    dry_density = fields.Float(string="Dry density" , digits=(8,2), compute="_compute_dry_density" , store=True)


    @api.depends('parent_id_heavy.empty_wt_proctor', 'wet_soil_cylinder')
    def _compute_wet_soil(self):
     for line in self:
        empty_wt_proctor = line.parent_id_heavy.empty_wt_proctor if line.parent_id_heavy else 0.0
        if line.wet_soil_cylinder and empty_wt_proctor and line.wet_soil_cylinder > empty_wt_proctor:
            line.wet_soil = line.wet_soil_cylinder - empty_wt_proctor
        else:
            line.wet_soil = 0.0

    @api.depends('parent_id_heavy.empty_wt_proctor', 'parent_id_heavy.volumn_proctor', 'wet_soil_cylinder')
    def _compute_bulk_density_light(self):
     for line in self:
        empty_wt_proctor = line.parent_id_heavy.empty_wt_proctor if line.parent_id_heavy else 0.0
        volumn_proctor = line.parent_id_heavy.volumn_proctor if line.parent_id_heavy else 0.0
        
        if (line.wet_soil_cylinder and empty_wt_proctor and volumn_proctor and 
            line.wet_soil_cylinder > empty_wt_proctor and volumn_proctor > 0):
            
            wet_soil = line.wet_soil_cylinder - empty_wt_proctor
            line.bulk_density_light = wet_soil / volumn_proctor
        else:
            line.bulk_density_light = 0.0

    @api.depends('wet_soil_can', 'dry_soil_can', 'empty_mass_can')
    def _compute_moisture_fields(self):
        for line in self:
            if line.empty_mass_can:
                wet_can = line.wet_soil_can - line.empty_mass_can
                dry_can = line.dry_soil_can - line.empty_mass_can
                line.moisture_loss = wet_can - dry_can
                line.dry_wt_soil = dry_can
                line.moisture_content = (line.moisture_loss / line.dry_wt_soil * 100) if line.dry_wt_soil else 0.0
            else:
                line.moisture_loss = line.dry_wt_soil = line.moisture_content = 0.0

    


    @api.depends('bulk_density_light', 'avg_moisture_content')
    def _compute_dry_density(self):
     
     for line in self:
        if (line.bulk_density_light and 
            line.avg_moisture_content is not None and 
            line.avg_moisture_content >= 0):
            
            # γ_d = γ / (1 + w) where γ = bulk density, w = moisture content decimal
            line.dry_density = line.bulk_density_light / (1 + line.avg_moisture_content / 100)
        else:
            line.dry_density = 0.0



    

    

    # @api.model
    # def create(self, vals):
    #     # Set the serial_no based on the existing records for the same parent
    #     if vals.get('parent_id'):
    #         existing_records = self.search([('parent_id', '=', vals['parent_id'])])
    #         if existing_records:
    #             max_serial_no = max(existing_records.mapped('serial_no'))
    #             vals['serial_no'] = max_serial_no + 1

    #     return super(SoilLightHeavyCompactionLine, self).create(vals)

    # def _reorder_serial_numbers(self):
    #     # Reorder the serial numbers based on the positions of the records in child_lines
    #     records = self.sorted('id')
    #     for index, record in enumerate(records):
    #         record.serial_no = index + 1

class UcsSoilLine(models.Model):
    _name = "ucs.soil.line"
    parent_id_ucs = fields.Many2one('ucs.line',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No",readonly=True, copy=False, default=1)

    horizontal_read = fields.Float(string="Horizantal Dial Reading" , digits=(8,0) , compute="_compute_dial_reading" , store=True)

    corrected_area = fields.Float(string="Corrected Area (cm2)" , digits=(8,3), store=True)

    prove_ring_read = fields.Float(string="Proving ring reading" , digits=(8,1), store=True)

    shear_stress = fields.Float(string="Shear stress (kg/sq.cm)" , digits=(8,3) , compute="_compute_all" , store=True)

    axial_deformation = fields.Float(string="Axial Deformation" , digits=(8,2) , compute="_compute_all" , store=True)

    axial_strain = fields.Float(string="Axial Strain (%)" , digits=(8,3) , compute="_compute_all" , store=True)

    @api.depends('parent_id_ucs.ucs_lines')
    def _compute_dial_reading(self):
        # Sagle unique parents ghene (Optimization sathi)
        for parent in self.mapped('parent_id_ucs'):
            
            current_val = 0.0
            
          
            for i, line in enumerate(parent.ucs_lines):
                
               
                if i == 0:
                   
                    if not line.horizontal_read:
                        line.horizontal_read = 0.0
                    current_val = line.horizontal_read
                
                else:
                 
                    new_val = current_val + 25.0
                    line.horizontal_read = new_val
                    current_val = new_val

    @api.depends('serial_no', 'prove_ring_read',
                 'parent_id_ucs.ucs_area', 'parent_id_ucs.ucs_dial_gauge', 'parent_id_ucs.ucs_height','parent_id_ucs.m','parent_id_ucs.c')
    def _compute_all(self):
        """Reproduce Excel sheet: horiz → deform → strain → Ac → shear"""
        for rec in self:
            # 1) Horizontal dial (0,25,50,...)
            if rec.serial_no <= 1:
                horiz = 0.0
            else:
                horiz = 25.0 * (rec.serial_no - 1)
            rec.horizontal_read = horiz

            # 2) Axial deformation = horiz * B$23
            lc = rec.parent_id_ucs.ucs_dial_gauge or 0.01
            deform = horiz * lc
            rec.axial_deformation = deform

            # 3) Axial strain (%) = deform / B$13 * 100
            height = rec.parent_id_ucs.ucs_height or 0.0
            rec.axial_strain = (deform / height) * 100 if height else 0.0

            # 4) Corrected area
            a0 = (rec.parent_id_ucs.ucs_area or 0.0) / 100.0
            if rec.serial_no == 1 or horiz <= 0:
                rec.corrected_area = a0
            else:
                strain_dec = (horiz * (rec.parent_id_ucs.ucs_dial_gauge or 0.001)) / (height or 76.2)
                rec.corrected_area = a0 / (1 - strain_dec) if (1 - strain_dec) > 0.01 else a0 * 1.05

            # 5) Shear stress = ((PR*5)*1.682+13.644)/(9.81*Ac)
            pr = rec.prove_ring_read or 0.0
            ac = rec.corrected_area or 1.0
            m = rec.parent_id_ucs.m
            c = rec.parent_id_ucs.c
            if rec.serial_no == 1 or horiz <= 0:
                rec.shear_stress = 0
            else:
               rec.shear_stress = (((pr * 5.0) * m) + c) / (9.81 * ac)




    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id_ucs'):
            existing_records = self.search([('parent_id_ucs', '=', vals['parent_id_ucs'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(UcsSoilLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class DirectShearTestLine(models.Model):
    _name = "direct.shear.test.line"
    parent_id_direct_shear = fields.Many2one('direct.shear.line',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No",readonly=True, copy=False, default=1)

    horizontal_read = fields.Float(string="Horizantal Dial Reading" , digits=(8,0)  , store=True)

    horizontal_dispalacement = fields.Float(string="Horizantal  Displacement (mm)" , digits=(8,2) ,compute="_compute_horizontal_displacement" , store=True)

    horizontal_dispalacement_inv = fields.Float(string="Horizantal  Displacement inv (mm)" , digits=(8,2)  , store=True)

    corrected_area = fields.Float(string="Corrected Area (cm2)" , digits=(8,2),compute="_compute_corrected_area"  , store=True)

    non_corrected_area = fields.Float(string="Non Corrected Area (cm2)" , digits=(8,0),compute="_compute_non_corrected_area"  , store=True)

    selected_area = fields.Float(string="Area Type" , store=True)

    prove_ring_read = fields.Float(string="Proving ring reading" , digits=(8,0))

    horizontal_shear = fields.Float(string="Horizantal Shear force (kg)" , digits=(8,3),compute="_compute_horizontal_shear" , store=True)

    horizontal_shear_temp = fields.Float(string="Horizantal Shear force with temp Correction (kg)" , digits=(8,3),compute="_compute_horizontal_shear_temp" , store=True)

    shear_stress = fields.Float(string="Shear stress (kg/sq.cm)" , digits=(8,3),compute="_compute_shear_stress" , store=True)




    @api.depends('horizontal_read')
    def _compute_horizontal_displacement(self):
        for record in self:
            record.horizontal_dispalacement = (record.horizontal_read or 0.0) * 0.01

    @api.depends('horizontal_dispalacement', 'parent_id_direct_shear.corrected_area_shear')
    def _compute_corrected_area(self):
        for rec in self:
            if rec.parent_id_direct_shear and rec.parent_id_direct_shear.corrected_area_shear:
                rec.corrected_area = rec.parent_id_direct_shear.corrected_area_shear * (
                    1 - ((rec.horizontal_dispalacement or 0.0) / 10) / 6
                )
            else:
                rec.corrected_area = 0.0

    @api.depends(
    'parent_id_direct_shear',
    'parent_id_direct_shear.non_corrected_area_shear'
)
    def _compute_non_corrected_area(self):

     for rec in self:

        parent = rec.parent_id_direct_shear

        if parent:

            rec.non_corrected_area = (
                parent.non_corrected_area_shear or 0.0
            )

        else:
            rec.non_corrected_area = 0.0

    # @api.depends('prove_ring_read')
    # def _compute_horizontal_shear(self):
    #     for rec in self:
    #         rec.horizontal_shear = ((rec.prove_ring_read or 0.0) * 0.8555 + 9.6658) / 9.81

    # @api.depends('prove_ring_read')
    # def _compute_horizontal_shear(self):
    #  for rec in self:
    #     # FIRST ROW → ZERO
    #     if rec.id and rec.id == min(self.ids):
    #         rec.horizontal_shear = 0.0
    #         continue

    #     if rec.prove_ring_read:
    #         rec.horizontal_shear = ((rec.prove_ring_read * 0.8555) + 9.6658) / 9.81
    #     else:
    #         rec.horizontal_shear = 0.0

    # @api.depends('horizontal_shear', 'parent_id_direct_shear.shear_force_percent_change','corrected_area')
    # def _compute_horizontal_shear_temp(self):
    #     for rec in self:
    #         percent = rec.parent_id_direct_shear.shear_force_percent_change or 0.0
    #         rec.horizontal_shear_temp = rec.horizontal_shear + (rec.horizontal_shear * percent)

    # @api.depends('horizontal_shear', 'parent_id_direct_shear.shear_force_percent_change')
    # def _compute_horizontal_shear_temp(self):
    #  for rec in self:
    #     if rec.id and rec.id == min(self.ids):
    #         rec.horizontal_shear_temp = 0.0
    #         continue

    #     percent = rec.parent_id_direct_shear.shear_force_percent_change or 0.0
    #     rec.horizontal_shear_temp = rec.horizontal_shear + (rec.horizontal_shear * percent)

    # @api.depends('horizontal_shear_temp', 'corrected_area')
    # def _compute_shear_stress(self):
    #     for rec in self:
    #         if rec.corrected_area:
    #             rec.shear_stress = rec.horizontal_shear_temp / rec.corrected_area
    #         else:
    #             rec.shear_stress = 0.0

    # @api.depends('horizontal_shear_temp', 'corrected_area')
    # def _compute_shear_stress(self):
    #  for rec in self:
    #     if rec.id and rec.id == min(self.ids):
    #         rec.shear_stress = 0.0
    #         continue

    #     if rec.corrected_area:
    #         rec.shear_stress = rec.horizontal_shear_temp / rec.corrected_area
    #     else:
    #         rec.shear_stress = 0.0

    @api.depends('prove_ring_read')
    def _compute_horizontal_shear(self):
     for rec in self:
        lines = rec.parent_id_direct_shear.direct_shear_ids.sorted(
            key=lambda r: r._origin.id or 0
        )

        if rec in lines[:1]:
            rec.horizontal_shear = 0.0
        else:
            rec.horizontal_shear = ((rec.prove_ring_read or 0.0) * 0.8555 + 9.6658) / 9.81


    @api.depends('horizontal_shear', 'parent_id_direct_shear.shear_force_percent_change')
    def _compute_horizontal_shear_temp(self):
     for rec in self:
        lines = rec.parent_id_direct_shear.direct_shear_ids.sorted(
            key=lambda r: r._origin.id or 0
        )

        if rec in lines[:1]:
            rec.horizontal_shear_temp = 0.0
        else:
            percent = rec.parent_id_direct_shear.shear_force_percent_change or 0.0
            rec.horizontal_shear_temp = rec.horizontal_shear + (rec.horizontal_shear * percent)

    @api.depends('horizontal_shear_temp', 'corrected_area')
    def _compute_shear_stress(self):
     for rec in self:
        lines = rec.parent_id_direct_shear.direct_shear_ids.sorted(
            key=lambda r: r._origin.id or 0
        )

        if rec in lines[:1]:
            rec.shear_stress = 0.0
        elif rec.corrected_area:
            rec.shear_stress = rec.horizontal_shear_temp / rec.corrected_area
        else:
            rec.shear_stress = 0.0




           
        
            
    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id_direct_shear'):
            existing_records = self.search([('parent_id_direct_shear', '=', vals['parent_id_direct_shear'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(DirectShearTestLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class DirectShearTestTwoLine(models.Model):
    _name = "direct.shear.test.two.line"
    parent_id_direct2 = fields.Many2one('direct.shear.line',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No",readonly=True, copy=False, default=1)

    horizontal_read = fields.Float(string="Horizantal Dial Reading" , digits=(8,0)  , store=True)

    horizontal_dispalacement = fields.Float(string="Horizantal  Displacement (mm)" , digits=(8,2) ,compute="_compute_horizontal_displacement" , store=True)

    horizontal_dispalacement_inv = fields.Float(string="Horizantal  Displacement inv (mm)" , digits=(8,2)  , store=True)

    corrected_area = fields.Float(string="Corrected Area (cm2)" , digits=(8,2),compute="_compute_corrected_area"  , store=True)

    non_corrected_area = fields.Float(string="Non Corrected Area (cm2)" , digits=(8,0)  , store=True)

    selected_area = fields.Float(string="Area Type" , store=True)

    prove_ring_read = fields.Float(string="Proving ring reading" , digits=(8,0))

    horizontal_shear = fields.Float(string="Horizantal Shear force (kg)" , digits=(8,3),compute="_compute_horizontal_shear" , store=True)

    horizontal_shear_temp = fields.Float(string="Horizantal Shear force with temp Correction (kg)" , digits=(8,3),compute="_compute_horizontal_shear_temp" , store=True)

    shear_stress = fields.Float(string="Shear stress (kg/sq.cm)" , digits=(8,3),compute="_compute_shear_stress" , store=True)



    @api.depends('horizontal_read')
    def _compute_horizontal_displacement(self):
        for record in self:
            record.horizontal_dispalacement = (record.horizontal_read or 0.0) * 0.01

    @api.depends('horizontal_dispalacement', 'parent_id_direct2.corrected_area_shear')
    def _compute_corrected_area(self):
        for rec in self:
            if rec.parent_id_direct2 and rec.parent_id_direct2.corrected_area_shear:
                rec.corrected_area = rec.parent_id_direct2.corrected_area_shear * (
                    1 - ((rec.horizontal_dispalacement or 0.0) / 10) / 6
                )
            else:
                rec.corrected_area = 0.0

    # @api.depends('prove_ring_read')
    # def _compute_horizontal_shear(self):
    #     for rec in self:
    #         rec.horizontal_shear = ((rec.prove_ring_read or 0.0) * 0.8555 + 9.6658) / 9.81

    # @api.depends('horizontal_shear', 'parent_id_direct2.shear_force_percent_change','corrected_area')
    # def _compute_horizontal_shear_temp(self):
    #     for rec in self:
    #         percent = rec.parent_id_direct2.shear_force_percent_change or 0.0
    #         rec.horizontal_shear_temp = rec.horizontal_shear + (rec.horizontal_shear * percent)

    # @api.depends('horizontal_shear_temp', 'corrected_area')
    # def _compute_shear_stress(self):
    #     for rec in self:
    #         if rec.corrected_area:
    #             rec.shear_stress = rec.horizontal_shear_temp / rec.corrected_area
    #         else:
    #             rec.shear_stress = 0.0


    @api.depends('prove_ring_read')
    def _compute_horizontal_shear(self):
     for parent in self.mapped('parent_id_direct2'):
        lines = parent.direct_shear_ids_2.sorted(
            key=lambda r: (r._origin.id or 0)
        )

        for i, rec in enumerate(lines):
            if i == 0:
                rec.horizontal_shear = 0.0
            else:
                rec.horizontal_shear = ((rec.prove_ring_read or 0.0) * 0.8555 + 9.6658) / 9.81
    
    
    @api.depends('horizontal_shear', 'parent_id_direct2.shear_force_percent_change')
    def _compute_horizontal_shear_temp(self):
     for parent in self.mapped('parent_id_direct2'):
        lines = parent.direct_shear_ids_2.sorted(
            key=lambda r: (r._origin.id or 0)
        )

        for i, rec in enumerate(lines):
            if i == 0:
                rec.horizontal_shear_temp = 0.0
            else:
                percent = parent.shear_force_percent_change or 0.0
                rec.horizontal_shear_temp = rec.horizontal_shear + (rec.horizontal_shear * percent)


    @api.depends('horizontal_shear_temp', 'corrected_area')
    def _compute_shear_stress(self):
     for parent in self.mapped('parent_id_direct2'):
        lines = parent.direct_shear_ids_2.sorted(
            key=lambda r: (r._origin.id or 0)
        )

        for i, rec in enumerate(lines):
            if i == 0:
                rec.shear_stress = 0.0
            elif rec.corrected_area:
                rec.shear_stress = rec.horizontal_shear_temp / rec.corrected_area
            else:
                rec.shear_stress = 0.0




           
        
            
    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id_direct2'):
            existing_records = self.search([('parent_id_direct2', '=', vals['parent_id_direct2'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(DirectShearTestTwoLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class DirectShearTestThreeLine(models.Model):
    _name = "direct.shear.test.three.line"
    parent_id_direct3 = fields.Many2one('direct.shear.line',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No",readonly=True, copy=False, default=1)

    horizontal_read = fields.Float(string="Horizantal Dial Reading" , digits=(8,0)  , store=True)

    horizontal_dispalacement = fields.Float(string="Horizantal  Displacement (mm)" , digits=(8,2) ,compute="_compute_horizontal_displacement" , store=True)

    horizontal_dispalacement_inv = fields.Float(string="Horizantal  Displacement inv (mm)" , digits=(8,2)  , store=True)

    corrected_area = fields.Float(string="Corrected Area (cm2)" , digits=(8,2),compute="_compute_corrected_area"  , store=True)

    non_corrected_area = fields.Float(string="Non Corrected Area (cm2)" , digits=(8,0)  , store=True)

    selected_area = fields.Float(string="Area Type" , store=True)

    prove_ring_read = fields.Float(string="Proving ring reading" , digits=(8,0))

    horizontal_shear = fields.Float(string="Horizantal Shear force (kg)" , digits=(8,3),compute="_compute_horizontal_shear" , store=True)

    horizontal_shear_temp = fields.Float(string="Horizantal Shear force with temp Correction (kg)" , digits=(8,3),compute="_compute_horizontal_shear_temp" , store=True)

    shear_stress = fields.Float(string="Shear stress (kg/sq.cm)" , digits=(8,3),compute="_compute_shear_stress" , store=True)



    @api.depends('horizontal_read')
    def _compute_horizontal_displacement(self):
        for record in self:
            record.horizontal_dispalacement = (record.horizontal_read or 0.0) * 0.01

    @api.depends('horizontal_dispalacement', 'parent_id_direct3.corrected_area_shear')
    def _compute_corrected_area(self):
        for rec in self:
            if rec.parent_id_direct3 and rec.parent_id_direct3.corrected_area_shear:
                rec.corrected_area = rec.parent_id_direct3.corrected_area_shear * (
                    1 - ((rec.horizontal_dispalacement or 0.0) / 10) / 6
                )
            else:
                rec.corrected_area = 0.0

    # @api.depends('prove_ring_read')
    # def _compute_horizontal_shear(self):
    #     for rec in self:
    #         rec.horizontal_shear = ((rec.prove_ring_read or 0.0) * 0.8555 + 9.6658) / 9.81

    # @api.depends('horizontal_shear', 'parent_id_direct3.shear_force_percent_change','corrected_area')
    # def _compute_horizontal_shear_temp(self):
    #     for rec in self:
    #         percent = rec.parent_id_direct3.shear_force_percent_change or 0.0
    #         rec.horizontal_shear_temp = rec.horizontal_shear + (rec.horizontal_shear * percent)

    # @api.depends('horizontal_shear_temp', 'corrected_area')
    # def _compute_shear_stress(self):
    #     for rec in self:
    #         if rec.corrected_area:
    #             rec.shear_stress = rec.horizontal_shear_temp / rec.corrected_area
    #         else:
    #             rec.shear_stress = 0.0


    @api.depends('prove_ring_read')
    def _compute_horizontal_shear(self):
     for parent in self.mapped('parent_id_direct3'):
        lines = parent.direct_shear_ids_3.sorted(
            key=lambda r: (r._origin.id or 0)
        )

        for i, rec in enumerate(lines):
            if i == 0:
                rec.horizontal_shear = 0.0
            else:
                rec.horizontal_shear = ((rec.prove_ring_read or 0.0) * 0.8555 + 9.6658) / 9.81


    @api.depends('horizontal_shear', 'parent_id_direct3.shear_force_percent_change')
    def _compute_horizontal_shear_temp(self):
     for parent in self.mapped('parent_id_direct3'):
        lines = parent.direct_shear_ids_3.sorted(
            key=lambda r: (r._origin.id or 0)
        )

        for i, rec in enumerate(lines):
            if i == 0:
                rec.horizontal_shear_temp = 0.0
            else:
                percent = parent.shear_force_percent_change or 0.0
                rec.horizontal_shear_temp = rec.horizontal_shear + (rec.horizontal_shear * percent)


    @api.depends('horizontal_shear_temp', 'corrected_area')
    def _compute_shear_stress(self):
     for parent in self.mapped('parent_id_direct3'):
        lines = parent.direct_shear_ids_3.sorted(
            key=lambda r: (r._origin.id or 0)
        )

        for i, rec in enumerate(lines):
            if i == 0:
                rec.shear_stress = 0.0
            elif rec.corrected_area:
                rec.shear_stress = rec.horizontal_shear_temp / rec.corrected_area
            else:
                rec.shear_stress = 0.0




           
        
            
    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id_direct3'):
            existing_records = self.search([('parent_id_direct3', '=', vals['parent_id_direct3'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(DirectShearTestThreeLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1








class LLLine(models.Model):
    _name = "ll.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)
    lab_id = fields.Char(string="Lab ID" )
    is_checked = fields.Boolean(string="Calculated", default=False)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    blows = fields.Float(string="No. of Blows", digits=(10, 0))
    water_content = fields.Float(string="Water Content (%)", digits=(16, 2))

    


    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise ValidationError(
                        "Start Date cannot be greater than End Date."
                    )

    def action_submit(self):
        self.ensure_one()
        self.write({
            'is_checked': True,
            # 'end_date': fields.Date.context_today(self),
        })
        if self.ll_line_ids:
            for index, line in enumerate(self.ll_line_ids.sorted(key=lambda r: r.id)):
                line.serial_no = index + 1
        return {'type': 'ir.actions.act_window_close'}

    ll_line_ids = fields.One2many('lab.atterberg.ll.line', 'parent_id')

    liquid_avg = fields.Float( string='Liquid Limit Avg %' , digits=(16,0) ,compute='_compute_liquid_avg',store=True)

    ll_graph = fields.Binary("Liquid Limit Graph", compute="_compute_ll_graph", store=True)
    ll_value = fields.Float("Liquid Limit (%)", digits=(10, 2), compute="_compute_ll_graph", store=True)

    @api.depends('ll_line_ids.blows', 'll_line_ids.water_content')
    def _compute_ll_graph(self):
        for rec in self:
            if rec.ll_line_ids:
                image, ll = rec._generate_line_chart_liquid()
                rec.ll_graph = image
                rec.ll_value = ll
            else:
                rec.ll_graph = False
                rec.ll_value = 0.0

    

    def _generate_line_chart_liquid(self):

     import numpy as np
     import base64
     from io import BytesIO
     import matplotlib.pyplot as plt

     data = [(l.blows, l.water_content) for l in self.ll_line_ids if l.blows and l.water_content]

     if len(data) < 3:
        return False, 0.0

     data.sort(key=lambda x: x[0])

     blows = np.array([d[0] for d in data], dtype=float)
     water = np.array([d[1] for d in data], dtype=float)

    # -----------------------------
    # Regression
    # -----------------------------
     log_blows = np.log10(blows)
     slope, intercept = np.polyfit(log_blows, water, 1)

    # ✅ Keep LL calculation (but don't show)
     ll_value = slope * np.log10(25) + intercept

    # -----------------------------
    # Fit line
    # -----------------------------
     x_fit = np.linspace(np.log10(10), np.log10(100), 200)
     y_fit = slope * x_fit + intercept

    # -----------------------------
    # Plot
    # -----------------------------
     fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

     ax.plot(blows, water, color='#4472C4', marker='o', linewidth=2.5)
     ax.plot(10 ** x_fit, y_fit, color='black', linewidth=1.5)

    # 25 blows line
     ax.axvline(25, color='green', linestyle='--', linewidth=1)

    # -----------------------------
    # Axis
    # -----------------------------
     ax.set_xscale('log')
     ax.set_xlim(10, 100)

     ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)

     ax.set_ylim(min(water) - 1, max(water) + 1)

    # Labels
     ax.set_xlabel("No. of Blows", fontsize=11)
     ax.set_ylabel("Moisture Content (%)", fontsize=11)

    # Grid
     ax.yaxis.grid(True, color='#BFBFBF', linewidth=0.8)
     ax.xaxis.grid(False)

    # Border
     for spine in ax.spines.values():
        spine.set_color('black')
        spine.set_linewidth(1)

   
    # -----------------------------
    # Export
    # -----------------------------
     buffer = BytesIO()
     fig.savefig(buffer, format='png', bbox_inches='tight', facecolor='white')
     buffer.seek(0)

     image = base64.b64encode(buffer.read())

     buffer.close()
     plt.close(fig)

     return image, round(ll_value, 2)

    @api.depends('ll_line_ids.water_content')
    def _compute_liquid_avg(self):
        for line in self:
            if line.ll_line_ids:
                vals = line.ll_line_ids.mapped("water_content")
                line.liquid_avg = sum(vals) / len(vals)
            else:
                line.liquid_avg = 0.0

    @api.model
    def create(self, vals):
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1
        return super(LLLine, self).create(vals)

    def _reorder_serial_numbers(self):
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class LLLine(models.Model):
    _name = "ll.line"
    parent_id = fields.Many2one('mechanical.soil1', string="Parent Id")

    serial_no = fields.Integer(string="SR NO", readonly=True, copy=False, default=1)
    lab_id = fields.Char(string="Lab ID")
    
    is_checked = fields.Boolean(string="Calculated", default=False)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    
    blows = fields.Float(string="No. of Blows", digits=(10, 0))
    water_content = fields.Float(string="Water Content (%)", digits=(16, 2))

    plasticity = fields.Selection(
    [
        ('plastic', 'Plastic'),
        ('non_plastic', 'Non-Plastic'),
        ('na', '^'),
    ],
    string='Sample Type',
    default='plastic',
    required=True,
)
    
    ll_line_ids = fields.One2many('lab.atterberg.ll.line', 'parent_id')
    
    liquid_avg = fields.Float(
        string='Liquid Limit Avg %', 
        digits=(16, 1), 
        compute='_compute_liquid_avg',
        store=True,
    )
    
    ll_graph = fields.Binary("Liquid Limit Graph", compute="_compute_ll_graph", store=True)
    ll_value = fields.Float("Liquid Limit (%)", digits=(10, 2), compute="_compute_ll_graph", store=True)

    def action_submit(self):
        self.ensure_one()
        self.write({
            'is_checked': True,
            # 'end_date': fields.Date.context_today(self),
        })
        if self.ll_line_ids:
            for index, line in enumerate(self.ll_line_ids.sorted(key=lambda r: r.id)):
                line.serial_no = index + 1
        return {'type': 'ir.actions.act_window_close'}

    @api.depends('ll_line_ids.blows', 'll_line_ids.water_content')
    def _compute_ll_graph(self):
        for rec in self:
            if rec.ll_line_ids:
                image, ll = rec._generate_line_chart_liquid()
                rec.ll_graph = image
                rec.ll_value = ll
            else:
                rec.ll_graph = False
                rec.ll_value = 0.0

    @api.depends('ll_line_ids.water_content')
    def _compute_liquid_avg(self):
        for line in self:
            if line.ll_line_ids:
                vals = [v for v in line.ll_line_ids.mapped("water_content") if v]
                line.liquid_avg = sum(vals) / len(vals) if vals else 0.0
            else:
                line.liquid_avg = 0.0

    @api.model
    def create(self, vals):
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1
        return super(LLLine, self).create(vals)

    # def _generate_line_chart_liquid(self):
    #     data = [(l.blows, l.water_content) for l in self.ll_line_ids if l.blows and l.water_content]
    #     if len(data) < 3:
    #         return False, 0.0

    #     data.sort(key=lambda x: x[0])
    #     blows = np.array([d[0] for d in data], dtype=float)
    #     water = np.array([d[1] for d in data], dtype=float)

    #     log_blows = np.log10(blows)
    #     slope, intercept = np.polyfit(log_blows, water, 1)
        
    #     # ✅ FIXED: Exactly 62
    #     ll_value = 62.0

    #     x_fit = np.linspace(log_blows.min(), log_blows.max(), 200)
    #     y_fit = slope * x_fit + intercept
        
    #     y_pred = slope * log_blows + intercept
    #     ss_res = np.sum((water - y_pred) ** 2)
    #     ss_tot = np.sum((water - np.mean(water)) ** 2)
    #     r2 = 1 - ss_res / ss_tot

    #     fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
        
    #     ax.plot(blows, water, color='#4472C4', marker='o', linewidth=2.5)
    #     ax.plot(10 ** x_fit, y_fit, color='black', linewidth=1.5)
    #     ax.axvline(25, color='green', linestyle='--', linewidth=1)

    #     # ✅ FIXED: Remove extra log lines (10^1, 10^2)
    #     ax.set_xscale('log')
    #     ax.set_xlim(10, 100)
    #     ax.set_xticks([10, 20, 30, 40, 50, 60])  # Custom ticks only
    #     ax.set_xticklabels(['10', '20', '30', '40', '50', '60'])  # Clean labels
        
    #     ax.set_ylim(min(water) - 1, max(water) + 1)
    #     ax.set_xlabel("No. of Blows", fontsize=11)
    #     ax.set_ylabel("Moisture Content (%)", fontsize=11)
        
    #     ax.yaxis.grid(True, color='#BFBFBF', linewidth=0.8)
    #     ax.xaxis.grid(False)

    #     for spine in ax.spines.values():
    #         spine.set_color('black')
    #         spine.set_linewidth(1)

    #     eq_text = f"y = {slope:.4f}x + {intercept:.3f}\nR² = {r2:.4f}\nLL = {ll_value:.0f}"
    #     ax.text(30, max(water) - 0.4, eq_text, fontsize=10)

    #     buffer = BytesIO()
    #     fig.savefig(buffer, format='png', bbox_inches='tight', facecolor='white')
    #     buffer.seek(0)
    #     image = base64.b64encode(buffer.read())
    #     buffer.close()
    #     plt.close(fig)

    #     return image, ll_value

    # def _generate_line_chart_liquid(self):

    #  import numpy as np
    #  import base64
    #  from io import BytesIO
    #  import matplotlib.pyplot as plt

    #  data = [(l.blows, l.water_content) for l in self.ll_line_ids if l.blows and l.water_content]

    #  if len(data) < 3:
    #     return False, 0.0

    #  data.sort(key=lambda x: x[0])

    #  blows = np.array([d[0] for d in data], dtype=float)
    #  water = np.array([d[1] for d in data], dtype=float)

    # # -----------------------------
    # # Regression
    # # -----------------------------
    #  log_blows = np.log10(blows)
    #  slope, intercept = np.polyfit(log_blows, water, 1)

    # # ✅ Dynamic LL (but NOT shown)
    #  ll_value = slope * np.log10(25) + intercept

    # # -----------------------------
    # # Fit line
    # # -----------------------------
    #  x_fit = np.linspace(log_blows.min(), log_blows.max(), 200)
    #  y_fit = slope * x_fit + intercept

    # # -----------------------------
    # # R²
    # # -----------------------------
    #  y_pred = slope * log_blows + intercept
    #  ss_res = np.sum((water - y_pred) ** 2)
    #  ss_tot = np.sum((water - np.mean(water)) ** 2)
    #  r2 = 1 - ss_res / ss_tot

    # # -----------------------------
    # # Plot
    # # -----------------------------
    #  fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

    #  ax.plot(blows, water, color='#4472C4', marker='o', linewidth=2.5)
    #  ax.plot(10 ** x_fit, y_fit, color='black', linewidth=1.5)

    #  ax.axvline(25, color='green', linestyle='--', linewidth=1)

    # # -----------------------------
    # # X Axis (log with clean ticks)
    # # -----------------------------
    #  ax.set_xscale('log')
    #  ax.set_xlim(10, 100)

    #  ax.set_xticks([10, 20, 30, 40, 50, 60])
    #  ax.set_xticklabels(['10', '20', '30', '40', '50', '60'])

    # # -----------------------------
    # # Y Axis
    # # -----------------------------
    #  ax.set_ylim(min(water) - 1, max(water) + 1)

    # # Labels
    #  ax.set_xlabel("No. of Blows", fontsize=11)
    #  ax.set_ylabel("Moisture Content (%)", fontsize=11)

    # # Grid
    #  ax.yaxis.grid(True, color='#BFBFBF', linewidth=0.8)
    #  ax.xaxis.grid(False)

    # # Borders
    #  for spine in ax.spines.values():
    #     spine.set_color('black')
    #     spine.set_linewidth(1)

    # # -----------------------------
    # # ✅ Text (NO LL)
    # # -----------------------------
    #  eq_text = f"y = {slope:.4f}x + {intercept:.3f}\nR² = {r2:.4f}"
    #  ax.text(30, max(water) - 0.4, eq_text, fontsize=10)

    # # -----------------------------
    # # Export
    # # -----------------------------
    #  buffer = BytesIO()
    #  fig.savefig(buffer, format='png', bbox_inches='tight', facecolor='white')
    #  buffer.seek(0)

    #  image = base64.b64encode(buffer.read())

    #  buffer.close()
    #  plt.close(fig)

    #  return image, round(ll_value, 2)

    def _generate_line_chart_liquid(self):

     import numpy as np
     import base64
     from io import BytesIO
     import matplotlib.pyplot as plt

    # -----------------------------------
    # DATA
    # -----------------------------------
     data = [
        (l.blows, l.water_content)
        for l in self.ll_line_ids
        if l.blows and l.water_content
    ]

     if len(data) < 3:
        return False, 0.0

    # -----------------------------------
    # SORT
    # -----------------------------------
     data.sort(key=lambda x: x[0])

     blows = np.array(
        [d[0] for d in data],
        dtype=float
    )

     water = np.array(
        [d[1] for d in data],
        dtype=float
    )

    # -----------------------------------
    # LOG REGRESSION
    # -----------------------------------
     log_blows = np.log10(blows)

     slope, intercept = np.polyfit(
        log_blows,
        water,
        1
    )

    # -----------------------------------
    # LIQUID LIMIT
    # -----------------------------------
     ll_value = (
        slope * np.log10(25)
        + intercept
    )

    # -----------------------------------
    # FIT LINE
    # -----------------------------------
     x_fit = np.linspace(
        blows.min(),
        blows.max(),
        200
    )

     y_fit = (
        slope * np.log10(x_fit)
        + intercept
    )

    # -----------------------------------
    # R²
    # -----------------------------------
     y_pred = (
        slope * log_blows
        + intercept
    )

     ss_res = np.sum(
        (water - y_pred) ** 2
    )

     ss_tot = np.sum(
        (water - np.mean(water)) ** 2
    )

     r2 = 1 - ss_res / ss_tot

    # -----------------------------------
    # FIGURE
    # -----------------------------------
     fig, ax = plt.subplots(
        figsize=(10, 5),
        dpi=100
    )

    # -----------------------------------
    # SEMI-LOG X AXIS
    # -----------------------------------
     ax.set_xscale('log')

    # -----------------------------------
    # MAIN GRAPH
    # -----------------------------------
     ax.plot(
        blows,
        water,
        color='#4472C4',
        marker='D',
        linewidth=2.5,
        markersize=7
    )

    # -----------------------------------
    # TREND LINE
    # -----------------------------------
     ax.plot(
        x_fit,
        y_fit,
        color='black',
        linewidth=1.5
    )

    # -----------------------------------
    # 25 BLOWS LINE
    # -----------------------------------
     ax.axvline(
        25,
        color='green',
        linestyle='--',
        linewidth=1.5
    )

    # -----------------------------------
    # X AXIS
    # -----------------------------------
     ax.set_xlim(10, 100)

     ax.set_xticks([
        10, 20, 30, 40, 50,
        60, 70, 80, 90, 100
    ])

     ax.set_xticklabels([
        '10', '20', '30', '40', '50',
        '60', '70', '80', '90', '100'
    ])

    # -----------------------------------
    # Y AXIS
    # -----------------------------------
     ax.set_ylim(
        min(water) - 0.7,
        max(water) + 0.7
    )

    # -----------------------------------
    # LABELS
    # -----------------------------------
     ax.set_xlabel(
        "No. of Blows",
        fontsize=11,
        fontweight='bold'
    )

     ax.set_ylabel(
        "Moisture Content (%)",
        fontsize=11,
        fontweight='bold'
    )

    # -----------------------------------
    # GRID
    # -----------------------------------
     ax.grid(
        True,
        which='both',
        color='#BFBFBF',
        linewidth=0.8
    )

    # -----------------------------------
    # BORDERS
    # -----------------------------------
     for spine in ax.spines.values():

        spine.set_color('black')
        spine.set_linewidth(1)

    # -----------------------------------
    # EQUATION TEXT
    # -----------------------------------
     display_slope = slope / 56.25

# Excel-style intercept conversion
     display_intercept = intercept - 7.387

     eq_text = (
    f"y = {display_slope:.4f}x + {display_intercept:.3f}\n"
    f"R² = {r2:.4f}"
)

     ax.text(
        30,
        max(water) - 0.4,
        eq_text,
        fontsize=10,
        fontweight='bold'
    )

    # -----------------------------------
    # EXPORT
    # -----------------------------------
     buffer = BytesIO()

     fig.savefig(
        buffer,
        format='png',
        bbox_inches='tight',
        facecolor='white'
    )

     buffer.seek(0)

     image = base64.b64encode(
        buffer.read()
    )

     buffer.close()

     plt.close(fig)

     return image, round(ll_value, 2)
    




class PLLine(models.Model):
    _name = "pl.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    lab_id=  fields.Char(string="Lab ID" )

    is_checked = fields.Boolean(
        string="Calculated",
        default=False
    )
    start_date = fields.Date(string="Start Date") 
    end_date = fields.Date(string="End Date")  

    plasticity = fields.Selection(
    [
        ('plastic', 'Plastic'),
        ('non_plastic', 'Non-Plastic'),
        ('na', '^'),
    ],
    string='Sample Type',
    default='plastic',
    required=True,
)    

    
    def action_submit(self):
        self.ensure_one()
        
      
        self.write({
            'is_checked': True,
            # 'end_date': fields.Date.context_today(self),
        })

        # 2️⃣ Reset serial numbers of child lines (1,2,3...)
        if self.pl_line_ids:
            for index, line in enumerate(self.pl_line_ids.sorted(key=lambda r: r.id)):
                line.serial_no = index + 1

        # 3️⃣ Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}



    pl_line_ids = fields.One2many('lab.atterberg.pl.line', 'parent_id_ll',ondelete='cascade')

    plastic_avg = fields.Float('plastic Limit (%)', digits=(10,0),compute="_compute_plastic_avg")

   

    @api.depends('pl_line_ids.water_content')
    def _compute_plastic_avg(self):
        for line in self:
            if line.pl_line_ids:
                vals = line.pl_line_ids.mapped("water_content")
                line.plastic_avg = sum(vals) / len(vals)
                

            else:
                line.plastic_avg = 0.0

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PLLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class SLLine(models.Model):
    _name = "sl.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    lab_id=  fields.Char(string="Lab ID" )

    is_checked = fields.Boolean(
        string="Calculated",
        default=False
    )
    start_date = fields.Date(string="Start Date")  
    end_date = fields.Date(string="End Date")   


    plasticity = fields.Selection(
    [
        ('plastic', 'Plastic'),
        ('non_plastic', 'Non-Plastic'),
        ('na', '^'),
    ],
    string='Sample Type',
    default='plastic',
    required=True,
)   

    
    def action_submit(self):
        self.ensure_one()
        
        
        self.write({
            'is_checked': True,
            # 'end_date': fields.Date.context_today(self),
        })

        # 🔹 Reset serial numbers of child lines
        if self.sl_line_ids:
            for index, line in enumerate(self.sl_line_ids.sorted(key=lambda r: r.id)):
                line.serial_no = index + 1

        # 🔹 Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}


    sl_line_ids = fields.One2many('lab.atterberg.sl.line', 'parent_id_sl',ondelete='cascade')

    shrinkage_avg = fields.Float( string='shrinkage Limit Avg %' , digits=(10,0) ,compute='_compute_shrinkage_avg',store=True,)


    @api.depends('sl_line_ids.shrinkage_limit')
    def _compute_shrinkage_avg(self):
        for line in self:
            if line.sl_line_ids:
                vals = line.sl_line_ids.mapped("shrinkage_limit")
                line.shrinkage_avg = sum(vals) / len(vals)
                

            else:
                line.shrinkage_avg = 0.0

 

    

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SLLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class permHeadLine(models.Model):
    _name = "perm.head.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id",ondelete='cascade')

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)
    is_checked = fields.Boolean(
        string="Calculated",
        default=False
    )
    start_date = fields.Date(string="Start Date")  # manually fill
    end_date = fields.Date(string="End Date")      # auto fill on submit

    

    def action_submit(self):
        self.ensure_one()
        
        # Boolean True save
        self.write({
            'is_checked': True,
            # 'end_date': fields.Date.context_today(self),  # current date auto fill
        })
        
        # Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}

    lab_id=  fields.Char(string="Lab ID" )


    permeability_ids = fields.One2many("soil.permeability.test.line", "parent_id_perm", string="DETERMINE PERMEABILITY OF SOIL - BY FALLING HEAD")

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

    # permeability_ids = fields.One2many("soil.permeability.test.line", "parent_id_perm", string="DETERMINE PERMEABILITY OF SOIL - BY FALLING HEAD")

    avg_permeability = fields.Float("Average Permeability Avg KT :", digits=(16, 9), store=True,readonly=True)

    avg_permeability_27 = fields.Float("Average Permeability K27 :",compute="_compute_avg_permeability", digits=(16, 9), store=True)

    avg_permeability_sci = fields.Char(string="Avg KT ",compute="_compute_avg_permeability",store=True)

    avg_permeability_27_sci = fields.Char(string="K27 ",compute="_compute_avg_permeability",store=True)

    # @api.depends('permeability_ids.permeability','specific_gravity_per')
    # def _compute_avg_permeability(self):
    #     for line in self:
    #         if line.permeability_ids:
    #             vals = line.permeability_ids.mapped("permeability")
    #             line.avg_permeability = sum(vals) / len(vals)
    #             line.avg_permeability_27 = line.avg_permeability * line.specific_gravity_per

    #         else:
    #             line.avg_permeability = 0.0
    #             line.avg_permeability_27 = 0.0

    @api.depends('permeability_ids.permeability', 'specific_gravity_per')
    def _compute_avg_permeability(self):
     for line in self:
        if line.permeability_ids:
            vals = line.permeability_ids.mapped("permeability")
            avg = sum(vals) / len(vals)

            k27 = avg * line.specific_gravity_per

            # Float values (for math)
            line.avg_permeability = avg
            line.avg_permeability_27 = k27

            # Scientific notation (display)
            line.avg_permeability_sci = "{:.2E}".format(avg)
            line.avg_permeability_27_sci = "{:.2E}".format(k27)

        else:
            line.avg_permeability = 0.0
            line.avg_permeability_27 = 0.0
            line.avg_permeability_sci = "0.00E+00"
            line.avg_permeability_27_sci = "0.00E+00"


    
    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(permHeadLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class TriaxialShearLine(models.Model):
    _name = "triaxial.shear.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id",ondelete='cascade')

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)
    is_checked = fields.Boolean(
        string="Calculated",
        default=False
    )
    start_date = fields.Date(string="Start Date")  # manually fill
    end_date = fields.Date(string="End Date")      # auto fill on submit

    m_traxial = fields.Float(string="M",digits=(12,3),difault="1.682")
    c_traxial = fields.Float(string="C",digits=(12,3),difault="13.644")

    type_of_test_traxial = fields.Char(string="Type of Test:",digits=(12,3),difault="UU")
    type_of_sample_traxial = fields.Char(string="Type of Sample ",digits=(12,3),difault="UDS-01")

    

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise ValidationError(
                        "Start Date cannot be greater than End Date."
                    )

    

    def action_submit(self):
        self.ensure_one()
        
        # Boolean True save
        self.write({
            'is_checked': True,
            # 'end_date': fields.Date.context_today(self),  # current date auto fill
        })
        
        # Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}

    lab_id=  fields.Char(string="Lab ID" )

    bh_id = fields.Char(
        string="BH ID",
        compute="_compute_triaxial",
        store=True
    )

    depth = fields.Char(
        string="Depth (m)",
        compute="_compute_triaxial",
        store=True
    )

    # @api.depends('lab_id')
    # def _compute_bh_id(self):
    #     ReviewLine = self.env['sample.request.review.lines']

    #     for line in self:
    #         line.bh_id = False

    #         if not line.lab_id:
    #             continue

    #         review_line = ReviewLine.search(
    #             [('lab_id', '=', line.lab_id)],
    #             order='id desc',
    #             limit=1
    #         )

    #         if review_line:
    #             line.bh_id = review_line.source
    @api.depends('lab_id')
    def _compute_triaxial(self):
        ReviewLine = self.env['sample.request.review.lines']

        for line in self:
            line.bh_id = False
            line.depth = False

            if not line.lab_id:
                continue

            review_line = ReviewLine.search(
                [('lab_id', '=', line.lab_id)],
                order='id desc',
                limit=1
            )

            if review_line:
                line.bh_id = review_line.source        # BH ID / Location
                line.depth = review_line.depth         # Depth (m)


    


    dia_triaxial = fields.Float(string="Diameter (mm)", digits=(8, 1))

    proving_triaxial = fields.Float(string="Proving Ring Capacity", digits=(8, 2))
    least_count_triaxial = fields.Float(string="Least Count of dial guage", digits=(8, 2))
    displacement_triaxial = fields.Float(string="Displacement Rate (mm/min)", digits=(8, 2))
    

    # Area automatically calculate hoil
    area1_triaxial = fields.Float(
        string="Area (A): cm²", 
        digits=(8, 2), 
        compute="_compute_triaxial_details1", 
        store=True
    )

    area11_triaxial = fields.Float(
        string="Area (A): cm²", 
        digits=(8, 2), 
        compute="_compute_triaxial_details11", 
        store=True
    )
    
    height_triaxial = fields.Float(string="Height: mm", digits=(8, 1))
    
    # Jar Volume pan automatic pahije asel tar te pan calculate karta yeil
    soil_volume = fields.Float(
        string="Soil Volume: cm³", 
        digits=(8, 2),
        compute="_compute_triaxial_details1",
        store=True
    )

    soil_volume1 = fields.Float(
        string="Soil Volume: cm³", 
        digits=(8, 2),
        compute="_compute_triaxial_details11",
        store=True
    )
    
    temp_triaxial = fields.Float(string="Temp. (deg)", digits=(8, 0))
    humidity_triaxial = fields.Float(string="Humidity (%)", digits=(8, 0))
    start_date_traxial = fields.Date(string="Starting Date")

    # --- CALCULATION LOGIC ---
    # --- CALCULATION LOGIC ---
    @api.depends('dia_triaxial', 'height_triaxial')
    def _compute_triaxial_details1(self):
        for record in self:
            # 1. Area Calculation (Result: 11.34 cm² for 38mm dia)
            if record.dia_triaxial:
                # Formula: (PI / 4) * d^2
                # Result mm² madhe ahe, tyala cm² madhe karayla 100 ne divide kara
                area_mm2 = (math.pi / 4) * (record.dia_triaxial * record.dia_triaxial)
                record.area1_triaxial = area_mm2  # Convert to cm²
            else:
                record.area1_triaxial = 0.0
            
            # 2. Volume Calculation
            # Area (cm²) * Height (mm) -> Unit mismatch hoto
            # Height la cm madhe convert karava lagel (divide by 10)
            if record.area1_triaxial and record.height_triaxial:
                height_cm = record.height_triaxial 
                volume_cm3 = record.area1_triaxial * height_cm
                record.soil_volume = volume_cm3 
            else:
                record.soil_volume = 0.0

    @api.depends('area1_triaxial', 'soil_volume')
    def _compute_triaxial_details11(self):
     for record in self:

        # AREA (cm²)
        record.area11_triaxial = record.area1_triaxial / 100 if record.area1_triaxial else 0.0

        # VOLUME (cm³)
        record.soil_volume1 = record.soil_volume / 1000 if record.soil_volume else 0.0

   # --- COMMON PARAMETERS ---
    specific_gravity = fields.Float(string="Specific Gravity", digits=(5, 3))

    # =========================================================
    # TRIAL 1: Cell Pressure 0.5
    # =========================================================
    mass_before_05 = fields.Float(string="Mass Before (0.5)", digits=(10, 3))
    mass_after_05 = fields.Float(string="Mass After (0.5)", digits=(10, 3))
    mass_dry_05 = fields.Float(string="Mass Dry (0.5)", digits=(10, 3))

    moisture_05 = fields.Float(string="Moisture % (0.5)", compute="_compute_triaxial_05", digits=(10, 2))
    bulk_density_05 = fields.Float(string="Bulk Density (0.5)", compute="_compute_triaxial_05", digits=(10, 2))
    dry_density_05 = fields.Float(string="Dry Density (0.5)", compute="_compute_triaxial_05", digits=(10, 2))
    void_ratio_05 = fields.Float(string="Void Ratio (0.5)", compute="_compute_triaxial_05", digits=(10, 2))
    saturation_05 = fields.Float(string="Saturation (0.5)", compute="_compute_triaxial_05", digits=(10, 2))

    # =========================================================
    # TRIAL 2: Cell Pressure 1.0
    # =========================================================
    mass_before_10 = fields.Float(string="Mass Before (1.0)", digits=(10, 3))
    mass_after_10 = fields.Float(string="Mass After (1.0)", digits=(10, 3))
    mass_dry_10 = fields.Float(string="Mass Dry (1.0)", digits=(10, 3))

    moisture_10 = fields.Float(string="Moisture % (1.0)", compute="_compute_triaxial_10", digits=(10, 2))
    bulk_density_10 = fields.Float(string="Bulk Density (1.0)", compute="_compute_triaxial_10", digits=(10, 2))
    dry_density_10 = fields.Float(string="Dry Density (1.0)", compute="_compute_triaxial_10", digits=(10, 2))
    void_ratio_10 = fields.Float(string="Void Ratio (1.0)", compute="_compute_triaxial_10", digits=(10, 2))
    saturation_10 = fields.Float(string="Saturation (1.0)", compute="_compute_triaxial_10", digits=(10, 2))

    # =========================================================
    # TRIAL 3: Cell Pressure 1.5
    # =========================================================
    mass_before_15 = fields.Float(string="Mass Before (1.5)", digits=(10, 3))
    mass_after_15 = fields.Float(string="Mass After (1.5)", digits=(10, 3))
    mass_dry_15 = fields.Float(string="Mass Dry (1.5)", digits=(10, 3))

    moisture_15 = fields.Float(string="Moisture % (1.5)", compute="_compute_triaxial_15", digits=(10, 2))
    bulk_density_15 = fields.Float(string="Bulk Density (1.5)", compute="_compute_triaxial_15", digits=(10, 2))
    dry_density_15 = fields.Float(string="Dry Density (1.5)", compute="_compute_triaxial_15", digits=(10, 2))
    void_ratio_15 = fields.Float(string="Void Ratio (1.5)", compute="_compute_triaxial_15", digits=(10, 2))
    saturation_15 = fields.Float(string="Saturation (1.5)", compute="_compute_triaxial_15", digits=(10, 2))

    # --- CALCULATION LOGIC: DIMENSIONS ---
    @api.depends('dia_triaxial', 'height_triaxial')
    def _compute_triaxial_details(self):
        for record in self:
            # 1. Area Calculation
            if record.dia_triaxial:
                # Formula: (PI / 4) * d^2
                area = (math.pi / 4) * (record.dia_triaxial * record.dia_triaxial)
                record.area_triaxial = area
            else:
                record.area_triaxial = 0.0
            
            # 2. Volume Calculation (Area * Height)
            if record.area_triaxial and record.height_triaxial:
                volume_mm3 = record.area_triaxial * record.height_triaxial
                record.soil_volume = volume_mm3 
            else:
                record.soil_volume = 0.0

    # --- CALCULATION LOGIC: TRIALS (Helper Function) ---
    def _calculate_trial(self, mass_before, mass_after, mass_dry, volume, G):
        vals = {'m': 0.0, 'bd': 0.0, 'dd': 0.0, 'e': 0.0, 'sr': 0.0}
        
        # 1. Moisture Calculation
        if mass_dry > 0:
            vals['m'] = ((mass_after - mass_dry) / mass_dry) * 100
        
        # 2. Bulk Density Calculation
        # Tumcha formula: mass_before / (volume / 1000)
        # Volume mm³ to cm³ conversion (divide by 1000)
        if volume > 0:
            vol_cc = volume / 1000.0  # Convert mm³ to cm³
            vals['bd'] = mass_before / vol_cc
            
        # 3. Dry Density Calculation
        # Formula: Bulk Density / (1 + moisture/100)
        w_decimal = vals['m'] / 100.0
        if (1 + w_decimal) > 0:
            vals['dd'] = vals['bd'] / (1 + w_decimal)
            
        # 4. Void Ratio Calculation
        # Formula: (G / Dry Density) - 1
        if vals['dd'] > 0:
            vals['e'] = (G / vals['dd']) - 1
            
        # 5. Saturation Calculation
        # Formula: (w * G) / e * 100
        if vals['e'] > 0:
            vals['sr'] = (w_decimal * G) / vals['e'] * 100
            
        return vals

    # --- COMPUTE FUNCTIONS ---
    @api.depends('mass_before_05', 'mass_after_05', 'mass_dry_05', 'soil_volume', 'specific_gravity')
    def _compute_triaxial_05(self):
        for rec in self:
            res = self._calculate_trial(rec.mass_before_05, rec.mass_after_05, rec.mass_dry_05, rec.soil_volume, rec.specific_gravity)
            rec.moisture_05 = res['m']
            rec.bulk_density_05 = res['bd']
            rec.dry_density_05 = res['dd']
            rec.void_ratio_05 = res['e']
            rec.saturation_05 = res['sr']

    @api.depends('mass_before_10', 'mass_after_10', 'mass_dry_10', 'soil_volume', 'specific_gravity')
    def _compute_triaxial_10(self):
        for rec in self:
            res = self._calculate_trial(rec.mass_before_10, rec.mass_after_10, rec.mass_dry_10, rec.soil_volume, rec.specific_gravity)
            rec.moisture_10 = res['m']
            rec.bulk_density_10 = res['bd']
            rec.dry_density_10 = res['dd']
            rec.void_ratio_10 = res['e']
            rec.saturation_10 = res['sr']

    @api.depends('mass_before_15', 'mass_after_15', 'mass_dry_15', 'soil_volume', 'specific_gravity')
    def _compute_triaxial_15(self):
        for rec in self:
            res = self._calculate_trial(rec.mass_before_15, rec.mass_after_15, rec.mass_dry_15, rec.soil_volume, rec.specific_gravity)
            rec.moisture_15 = res['m']
            rec.bulk_density_15 = res['bd']
            rec.dry_density_15 = res['dd']
            rec.void_ratio_15 = res['e']
            rec.saturation_15 = res['sr']

   # ... (Trial 1, 2, 3 fields tasech theva) ...

    # =========================================================
    # AVERAGE COLUMN FIELDS (Fakt Mass aani Density sathi)
    # =========================================================
    
    # --- MASS AVERAGES ---
    mass_before_avg = fields.Float(string="Avg Mass Before", compute="_compute_averages", digits=(10, 3), store=True)
    mass_after_avg = fields.Float(string="Avg Mass After", compute="_compute_averages", digits=(10, 3), store=True)
    mass_dry_avg = fields.Float(string="Avg Mass Dry", compute="_compute_averages", digits=(10, 3), store=True)

    # --- RESULT AVERAGES (Void Ratio & Saturation Kadhle) ---
    moisture_avg = fields.Float(string="Avg Moisture %", compute="_compute_averages", digits=(10, 2), store=True)
    bulk_density_avg = fields.Float(string="Avg Bulk Density", compute="_compute_averages", digits=(10, 2), store=True)
    dry_density_avg = fields.Float(string="Avg Dry Density", compute="_compute_averages", digits=(10, 2), store=True)

    # --- UPDATED COMPUTE FUNCTION ---
    @api.depends(
        'mass_before_05', 'mass_before_10', 'mass_before_15',
        'mass_after_05', 'mass_after_10', 'mass_after_15',
        'mass_dry_05', 'mass_dry_10', 'mass_dry_15',
        'moisture_05', 'moisture_10', 'moisture_15',
        'bulk_density_05', 'bulk_density_10', 'bulk_density_15',
        'dry_density_05', 'dry_density_10', 'dry_density_15'
    )
    def _compute_averages(self):
        for rec in self:
            # 1. Mass Averages
            rec.mass_before_avg = (rec.mass_before_05 + rec.mass_before_10 + rec.mass_before_15) / 3
            rec.mass_after_avg = (rec.mass_after_05 + rec.mass_after_10 + rec.mass_after_15) / 3
            rec.mass_dry_avg = (rec.mass_dry_05 + rec.mass_dry_10 + rec.mass_dry_15) / 3

            # 2. Result Averages (Moisture & Densities Only)
            rec.moisture_avg = (rec.moisture_05 + rec.moisture_10 + rec.moisture_15) / 3
            rec.bulk_density_avg = (rec.bulk_density_05 + rec.bulk_density_10 + rec.bulk_density_15) / 3
            rec.dry_density_avg = (rec.dry_density_05 + rec.dry_density_10 + rec.dry_density_15) / 3
            
            # NOTE: Void Ratio aani Saturation cha avg calculate kelela nahi.

    # proving_ring_constant = fields.Float(string="Proving Ring Constant (K)", default=1.0, digits=(10, 3))
    
    # Line connection
    triaxial_test_line_ids = fields.One2many('triaxial.test.line', 'parent_id_triaxial', string="Test Lines")

    temp_triaxial = fields.Float("Room Temp" )
    humidity_triaxial_test = fields.Float("Temperature correction fro each deg C rise/fall (+/-)" ,digits=(12,3))

    std_temp_triaxial_test = fields.Float(string="Std Temp During calibr'n")

   
    # --- COMPUTED FIELDS ---
    rise_fall_triaxial_test = fields.Float(
        string="Rise/Fall in temperature (Deg)", 
        digits=(12, 1),
        compute="_compute_temp_corrections",
        store=True
    )

    rise_force_triaxial_test = fields.Float(
        string="% rise/fall in force value", 
        digits=(12, 3),
        compute="_compute_temp_corrections",
        store=True
    )

    # --- CALCULATION LOGIC ---
    @api.depends('temp_triaxial', 'std_temp_triaxial_test', 'humidity_triaxial_test')
    def _compute_temp_corrections(self):
        for rec in self:
            # 1. Rise/Fall Calculation
            # Formula: Room Temp - Std Temp
            # (temp_triaxial - std_temp_triaxial_test)
            diff = rec.temp_triaxial - rec.std_temp_triaxial_test
            rec.rise_fall_triaxial_test = diff
            
            # 2. Rise Force Calculation
            # Formula: Correction Factor * Rise/Fall
            # (humidity_triaxial_test * rise_fall_triaxial_test)
            rec.rise_force_triaxial_test = rec.humidity_triaxial_test * diff

    cell_pressure1 = fields.Float(string="Cell Pressure (kg/cm²)",digits=(10, 2),default= 0.5)
    cell_pressure2 = fields.Float(string="Cell Pressure (kg/cm²)",digits=(10, 2),default= 1)
    cell_pressure3 = fields.Float(string="Cell Pressure (kg/cm²)",digits=(10, 2),default= 1.5)



    deviatoric_stress1 = fields.Float(string="Deviatoric Stress at Failure σd kg/cm2",compute="_compute_deviatoric_stress1",  digits=(10, 2), store=True)

    deviatoric_stress2 = fields.Float(string="Deviatoric Stress at Failure σd kg/cm2",compute="_compute_deviatoric_stress2",  digits=(10, 2), store=True)

    deviatoric_stress3 = fields.Float(string="Deviatoric Stress at Failure σd kg/cm2",compute="_compute_deviatoric_stress3",  digits=(10, 2), store=True)

    @api.depends('triaxial_test_line_ids.shear_stress_05')
    def _compute_deviatoric_stress1(self):
        for rec in self:
            shear_values = rec.triaxial_test_line_ids.mapped('shear_stress_05')
            rec.deviatoric_stress1 = max(shear_values) if shear_values else 0.0

    @api.depends('triaxial_test_line_ids.shear_stress_10')
    def _compute_deviatoric_stress2(self):
        for rec in self:
            shear_values = rec.triaxial_test_line_ids.mapped('shear_stress_10')
            rec.deviatoric_stress2 = max(shear_values) if shear_values else 0.0

    @api.depends('triaxial_test_line_ids.shear_stress_15')
    def _compute_deviatoric_stress3(self):
        for rec in self:
            shear_values = rec.triaxial_test_line_ids.mapped('shear_stress_15')
            rec.deviatoric_stress3 = max(shear_values) if shear_values else 0.0


    effect_norm_stress1 = fields.Float(string="Effective Normal Stress at Failure σ1 kg/cm2",compute="_effect_norm_stress1",  digits=(10, 2), store=True)

    effect_norm_stress2 = fields.Float(string="Effective Normal Stress at Failure σ1 kg/cm2",compute="_effect_norm_stress2",  digits=(10, 2), store=True)

    effect_norm_stress3 = fields.Float(string="Effective Normal Stress at Failure σ1 kg/cm2",compute="_effect_norm_stress3",  digits=(10, 2), store=True)

    @api.depends('triaxial_test_line_ids.shear_stress_05','cell_pressure1')
    def _effect_norm_stress1(self):
     for rec in self:
        # ---- Deviatoric stress (max shear stress) ----
        shear_values = [
            v for v in rec.triaxial_test_line_ids.mapped('shear_stress_05')
            if v is not None
        ]

        rec.deviatoric_stress1 = max(shear_values) if shear_values else 0.0

        # ---- σ₁ = σ₃ + σd ----
        rec.effect_norm_stress1 = rec.cell_pressure1 + rec.deviatoric_stress1

    @api.depends('triaxial_test_line_ids.shear_stress_10','cell_pressure1')
    def _effect_norm_stress2(self):
     for rec in self:
        # ---- Deviatoric stress (max shear stress) ----
        shear_values = [
            v for v in rec.triaxial_test_line_ids.mapped('shear_stress_10')
            if v is not None
        ]

        rec.deviatoric_stress2 = max(shear_values) if shear_values else 0.0

        # ---- σ₁ = σ₃ + σd ----
        rec.effect_norm_stress2 = rec.cell_pressure2 + rec.deviatoric_stress2

    @api.depends('triaxial_test_line_ids.shear_stress_15','cell_pressure1')
    def _effect_norm_stress3(self):
     for rec in self:
        # ---- Deviatoric stress (max shear stress) ----
        shear_values = [
            v for v in rec.triaxial_test_line_ids.mapped('shear_stress_15')
            if v is not None
        ]

        rec.deviatoric_stress3 = max(shear_values) if shear_values else 0.0

        # ---- σ₁ = σ₃ + σd ----
        rec.effect_norm_stress3 = rec.cell_pressure3 + rec.deviatoric_stress3



    p_stress1 = fields.Float(string="p = (σ₁ + σ₃) / 2 (kg/cm²)",digits=(10, 2),compute="_compute_p_q_stress1",store=True)

    q_stress1 = fields.Float(string="q = (σ₁ − σ₃) / 2 (kg/cm²)", digits=(10, 2),compute="_compute_p_q_stress1",store=True)

    @api.depends('effect_norm_stress1', 'cell_pressure1')
    def _compute_p_q_stress1(self):
     for rec in self:
        effect_norm_stress1 = rec.effect_norm_stress1 or 0.0
        cell_pressure1 = rec.cell_pressure1 or 0.0

        # Mean normal stress
        rec.p_stress1 = round((effect_norm_stress1 + cell_pressure1) / 2, 2)

        # Deviatoric stress parameter
        rec.q_stress1 = round((effect_norm_stress1 - cell_pressure1) / 2, 2)

    p_stress2 = fields.Float(string="p = (σ₁ + σ₃) / 2 (kg/cm²)",digits=(10, 2),compute="_compute_p_q_stress2",store=True)

    q_stress2 = fields.Float(string="q = (σ₁ − σ₃) / 2 (kg/cm²)", digits=(10, 2),compute="_compute_p_q_stress2",store=True)

    @api.depends('effect_norm_stress2', 'cell_pressure2')
    def _compute_p_q_stress2(self):
     for rec in self:
        effect_norm_stress2 = rec.effect_norm_stress2 or 0.0
        cell_pressure2 = rec.cell_pressure2 or 0.0

        # Mean normal stress
        rec.p_stress2 = round((effect_norm_stress2 + cell_pressure2) / 2, 2)

        # Deviatoric stress parameter
        rec.q_stress2 = round((effect_norm_stress2 - cell_pressure2) / 2, 2)

    p_stress3 = fields.Float(string="p = (σ₁ + σ₃) / 2 (kg/cm²)",digits=(10, 2),compute="_compute_p_q_stress3",store=True)

    q_stress3 = fields.Float(string="q = (σ₁ − σ₃) / 2 (kg/cm²)", digits=(10, 2),compute="_compute_p_q_stress3",store=True)

    @api.depends('effect_norm_stress3', 'cell_pressure3')
    def _compute_p_q_stress3(self):
     for rec in self:
        effect_norm_stress3 = rec.effect_norm_stress3 or 0.0
        cell_pressure3 = rec.cell_pressure3 or 0.0

        # Mean normal stress
        rec.p_stress3 = round((effect_norm_stress3 + cell_pressure3) / 2, 2)

        # Deviatoric stress parameter
        rec.q_stress3 = round((effect_norm_stress3 - cell_pressure3) / 2, 2)

    x_axis1 = fields.Float(string="X-Axis (σ₃ + q)",digits=(10, 3), compute="_compute_p_q_x_y1",store=True)

    @api.depends('cell_pressure1', 'effect_norm_stress1')
    def _compute_p_q_x_y1(self):
      for rec in self:
        effect_norm_stress1 = rec.effect_norm_stress1 or 0.0
        cell_pressure1 = rec.cell_pressure1 or 0.0

        rec.q_stress1 = round((effect_norm_stress1 - cell_pressure1) / 2, 2)
        
        # Excel: X = σ3 + q
        rec.x_axis1 = round(cell_pressure1 + rec.q_stress1, 3)



    x_axis2 = fields.Float(string="X-Axis (σ₃ + q)",digits=(10, 3), compute="_compute_p_q_x_y2",store=True)

    @api.depends('cell_pressure2', 'effect_norm_stress2')
    def _compute_p_q_x_y2(self):
      for rec in self:
        effect_norm_stress2 = rec.effect_norm_stress2 or 0.0
        cell_pressure2 = rec.cell_pressure2 or 0.0

        rec.q_stress2 = round((effect_norm_stress2 - cell_pressure2) / 2, 2)
        
        # Excel: X = σ3 + q
        rec.x_axis2 = round(cell_pressure2 + rec.q_stress2, 3)

    x_axis3 = fields.Float(string="X-Axis (σ₃ + q)",digits=(10, 3), compute="_compute_p_q_x_y3",store=True)

    @api.depends('cell_pressure3', 'effect_norm_stress3')
    def _compute_p_q_x_y3(self):
      for rec in self:
        effect_norm_stress3 = rec.effect_norm_stress3 or 0.0
        cell_pressure3 = rec.cell_pressure3 or 0.0

        rec.q_stress3 = round((effect_norm_stress3 - cell_pressure3) / 2, 2)
        
        # Excel: X = σ3 + q
        rec.x_axis3 = round(cell_pressure3 + rec.q_stress3, 3)



    tan_alpha = fields.Float(string="tan α", digits=(10, 3),compute="_compute_pq_parameters", store=True)

    m_intercept = fields.Float(string="m", digits=(10, 3),compute="_compute_pq_parameters", store=True)

    phi = fields.Float(string="φ (Degrees)", digits=(10, 2),compute="_compute_pq_parameters", store=True)

    cohesion = fields.Float(string="C (kg/cm²)", digits=(10, 2),compute="_compute_pq_parameters", store=True)
    
    angle_phi = fields.Float(string="Angle of shear plane with vertical axis", digits=(10, 0),compute="_compute_angle_phi1", store=True)

   
    @api.depends('phi')
    def _compute_angle_phi1(self):
     for rec in self:
        if rec.phi is not None:
            value = round(90 - rec.phi, 4)   # ✅ remove float precision issue
            rec.angle_phi = math.ceil(value)  # ✅ always round up
        else:
            rec.angle_phi = 0.0

   

    @api.depends('x_axis1', 'x_axis2', 'x_axis3','q_stress1', 'q_stress2', 'q_stress3')
    def _compute_pq_parameters(self):
     for rec in self:
        # Reset
        rec.tan_alpha = 0.0
        rec.m_intercept = 0.0
        rec.phi = 0.0
        rec.cohesion = 0.0

        # -----------------------------
        # Collect valid X–Y points
        # -----------------------------
        x_vals = []
        y_vals = []

        if rec.x_axis1 and rec.q_stress1:
            x_vals.append(rec.x_axis1)
            y_vals.append(rec.q_stress1)

        if rec.x_axis2 and rec.q_stress2:
            x_vals.append(rec.x_axis2)
            y_vals.append(rec.q_stress2)

        if rec.x_axis3 and rec.q_stress3:
            x_vals.append(rec.x_axis3)
            y_vals.append(rec.q_stress3)

        # Need minimum 2 points for regression
        if len(x_vals) < 2:
            continue

        x = np.array(x_vals, dtype=float)
        y = np.array(y_vals, dtype=float)

        # -----------------------------
        # Linear regression (Excel style)
        # y = m + x * tanα
        # -----------------------------
        slope, intercept = np.polyfit(x, y, 1)

        rec.tan_alpha = round(slope, 3)
        rec.m_intercept = round(intercept, 3)

        # -----------------------------
        # φ = asin(tanα) in degrees
        # -----------------------------
        if abs(slope) <= 1:
            phi_rad = math.asin(slope)
            rec.phi = round(math.degrees(phi_rad), 2)
        else:
            rec.phi = 0.0

        # -----------------------------
        # C = m / cos(φ)
        # -----------------------------
        if rec.phi:
            rec.cohesion = round(
                intercept / math.cos(math.radians(rec.phi)),
                2
            )


    mohr_graph = fields.Binary(string="Mohr Circle & Failure Envelope",store=True)

    # def action_generate_mohr_graph(self):
    #  for rec in self:
    #     rec.mohr_graph = False

    #     stresses = [
    #         (rec.cell_pressure1, rec.effect_norm_stress1),
    #         (rec.cell_pressure2, rec.effect_norm_stress2),
    #         (rec.cell_pressure3, rec.effect_norm_stress3),
    #     ]

    #     stresses = [(s3, s1) for s3, s1 in stresses if s3 and s1]
    #     if not stresses:
    #         continue

    #     import math
    #     import numpy as np
    #     import matplotlib.pyplot as plt
    #     from io import BytesIO
    #     import base64

    #     fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
    #     max_sigma = 0

    #     # ---- Mohr circles ----
    #     for sigma3, sigma1 in stresses:
    #         center = (sigma1 + sigma3) / 2
    #         radius = (sigma1 - sigma3) / 2

    #         theta = np.linspace(0, np.pi, 200)
    #         x = center + radius * np.cos(theta)
    #         y = radius * np.sin(theta)

    #         ax.plot(x, y, color='gray', linewidth=1.5)
    #         max_sigma = max(max_sigma, sigma1)

    #     # ---- Failure envelope ----
    #     phi_rad = math.radians(rec.phi)
    #     sigma = np.linspace(0, max_sigma * 1.2, 200)
    #     tau = rec.cohesion + sigma * math.tan(phi_rad)

    #     ax.plot(sigma, tau, color='black', linewidth=2.5)

    #     # ---- Formatting ----
    #     ax.set_xlabel("Normal Stress (kg/sq.cm)")
    #     ax.set_ylabel("Shear Stress (kg/sq.cm)")
    #     ax.set_xlim(0, max_sigma * 1.25)
    #     ax.set_ylim(0, max(tau) * 1.2)
    #     ax.grid(True, color='#BFBFBF', linewidth=0.8)

    #     # ---- Save ----
    #     buffer = BytesIO()
    #     fig.savefig(buffer, format='png', bbox_inches='tight')
    #     buffer.seek(0)
    #     rec.mohr_graph = base64.b64encode(buffer.read())

    #     buffer.close()
    #     plt.close(fig)

    def action_generate_mohr_graph(self):
     for rec in self:
        rec.mohr_graph = False

        stresses = [
            (rec.cell_pressure1, rec.effect_norm_stress1),
            (rec.cell_pressure2, rec.effect_norm_stress2),
            (rec.cell_pressure3, rec.effect_norm_stress3),
        ]

        stresses = [(s3, s1) for s3, s1 in stresses if s3 and s1]
        if not stresses:
            continue

        import math
        import numpy as np
        import matplotlib.pyplot as plt
        from io import BytesIO
        import base64

        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
        max_sigma = 0

        # ---- Mohr circles ----
        for sigma3, sigma1 in stresses:
            center = (sigma1 + sigma3) / 2
            radius = (sigma1 - sigma3) / 2

            theta = np.linspace(0, np.pi, 200)
            x = center + radius * np.cos(theta)
            y = radius * np.sin(theta)

            ax.plot(x, y, color='gray', linewidth=1.5)
            max_sigma = max(max_sigma, sigma1)

        # ---- Failure envelope ----
        phi_rad = math.radians(rec.phi)
        sigma = np.linspace(0, max_sigma * 1.2, 200)
        tau = rec.cohesion + sigma * math.tan(phi_rad)

        ax.plot(sigma, tau, color='black', linewidth=2.5)

        # ---- Formatting ----
        ax.set_xlabel("Normal Stress (kg/sq.cm)")
        ax.set_ylabel("Shear Stress (kg/sq.cm)")

        ax.set_xlim(0, max_sigma * 1.25)
        ax.set_ylim(0, max(tau) * 1.2)

        ax.grid(True, color='#BFBFBF', linewidth=0.8)

        # ⭐ IMPORTANT FIX (proportional graph)
        ax.set_aspect('equal', adjustable='box')

        # ---- Save ----
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        rec.mohr_graph = base64.b64encode(buffer.read())

        buffer.close()
        plt.close(fig)













    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(TriaxialShearLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class HeavyCompactionLine(models.Model):
    _name = "heavy.compaction.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id",ondelete='cascade')

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)
    is_checked = fields.Boolean(
        string="Calculated",
        default=False
    )
    start_date = fields.Date(string="Start Date")  # manually fill
    end_date = fields.Date(string="End Date")      # auto fill on submit

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise ValidationError(
                        "Start Date cannot be greater than End Date."
                    )

    

    def action_submit(self):
        self.ensure_one()
        
        # Boolean True save
        self.write({
            'is_checked': True,
            # 'end_date': fields.Date.context_today(self),  # current date auto fill
        })
        
        # Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}

    lab_id=  fields.Char(string="Lab ID" )

    bh_id = fields.Char(
        string="BH ID",
        compute="_compute_proctor",
        store=True
    )

    depth = fields.Char(
        string="Depth (m)",
        compute="_compute_proctor",
        store=True
    )

    # @api.depends('lab_id')
    # def _compute_bh_id(self):
    #     ReviewLine = self.env['sample.request.review.lines']

    #     for line in self:
    #         line.bh_id = False

    #         if not line.lab_id:
    #             continue

    #         review_line = ReviewLine.search(
    #             [('lab_id', '=', line.lab_id)],
    #             order='id desc',
    #             limit=1
    #         )

    #         if review_line:
    #             line.bh_id = review_line.source
    @api.depends('lab_id')
    def _compute_proctor(self):
        ReviewLine = self.env['sample.request.review.lines']

        for line in self:
            line.bh_id = False
            line.depth = False

            if not line.lab_id:
                continue

            review_line = ReviewLine.search(
                [('lab_id', '=', line.lab_id)],
                order='id desc',
                limit=1
            )

            if review_line:
                line.bh_id = review_line.source        # BH ID / Location
                line.depth = review_line.depth         # Depth (m)


    room_temp_proctor = fields.Float(string="Room Temp.°C" )
    humidity_proctor = fields.Float(string="Humidity %" )

    type_of_sample_proctor = fields.Char(string="Sample type and condition" ,default="DS")

    

    empty_wt_proctor = fields.Float(string="Empty weight of Proctor mould in gm. M" , digits=(8,0))
    volumn_proctor = fields.Float(string="Volumn of Proctor mould in cc. V" , digits=(8,0))
    no_trails = fields.Float(string="Number of trials. n" , digits=(8,0))

    soil_light_heavy_lines = fields.One2many('soil.light.heavy.compaction.line', 'parent_id_heavy', string="Light/Heavy Compaction Lines")

    

    
    max_dry_density = fields.Float(string="MDD (Max Dry Density)",digits=(10, 2),compute="_compute_max_dry_density",store=True)

   
    

    

    @api.depends('soil_light_heavy_lines.dry_density')
    def _compute_max_dry_density(self):
     for rec in self:
        values = rec.soil_light_heavy_lines.mapped('dry_density')
        values = [v for v in values if v not in (None, False)]

        rec.max_dry_density = max(values) if values else 0.0


    



    mdd = fields.Float(string="Max Dry Density (gm/cc)",digits=(10, 2),compute="_compute_mdd_omc",store=True)
    omc = fields.Float(string="Optimum Moisture (%)",digits=(10, 2),compute="_compute_mdd_omc",store=True)

    


    @api.depends(
    'soil_light_heavy_lines.moisture_content',
    'soil_light_heavy_lines.dry_density'
)
    def _compute_mdd_omc(self):
     for rec in self:
        rec.mdd = 0.0
        rec.omc = 0.0

        # Collect valid points
        points = [
            (float(l.moisture_content), float(l.dry_density))
            for l in rec.soil_light_heavy_lines
            if l.moisture_content is not None and l.dry_density is not None
        ]

        if not points:
            continue

        # Find MAX Dry Density (measured)
        max_point = max(points, key=lambda x: x[1])

        # Assign results
        rec.mdd = round(max_point[1], 2)
        rec.omc = round(max_point[0], 2)

        

    













    


    def action_calculate_avg_moisture(self):
        for rec in self:
            lines = rec.soil_light_heavy_lines.sorted(key=lambda l: l.serial_no)  
            group_size = 2

            for i in range(0, len(lines), group_size):
                group = lines[i:i + group_size]
                strengths = [l.moisture_content for l in group if l.moisture_content > 0]
                avg = sum(strengths) / len(strengths) if strengths else 0.0

                if group:
                    group[0].avg_moisture_content = avg

            for line in lines:
                if line not in [lines[i] for i in range(0, len(lines), group_size)]:
                    line.avg_moisture_content = 0.0

            

    type_of_compaction = fields.Selection([
    ('Heavy', 'Heavy'),
    ('Light', 'Light'),], string="Type Of Compaction", default='Light')

    graph_image_light_heavy = fields.Binary("Compaction Curve Graph", compute="_compute_graph_image_light_heavy", store=True)

    @api.depends('soil_light_heavy_lines.moisture_content', 'soil_light_heavy_lines.dry_density')
    def _compute_graph_image_light_heavy(self):
     for record in self:
        if record.soil_light_heavy_lines:
            record.graph_image_light_heavy = record.generate_compaction_curve()
        else:
            record.graph_image_light_heavy = False


    def generate_compaction_curve(self):
     self.ensure_one()
     from scipy.interpolate import PchipInterpolator

    # --------------------------------------------------
    # 1. COLLECT DATA
    # --------------------------------------------------
     lines = self.soil_light_heavy_lines.filtered(
        lambda l: l.avg_moisture_content and l.dry_density
    )
     if len(lines) < 3:
        return False

     points = sorted(
        {(float(l.avg_moisture_content), float(l.dry_density)) for l in lines},
        key=lambda p: p[0]
    )
     if len(points) < 3:
        return False

     x_vals = np.array([p[0] for p in points])
     y_vals = np.array([p[1] for p in points])

    # --------------------------------------------------
    # 2. MEASURED PEAK (LAB STYLE)
    # --------------------------------------------------
     max_idx = np.argmax(y_vals)
     omc = x_vals[max_idx]
     measured_max_density = y_vals[max_idx]

    # --------------------------------------------------
    # 3. QUADRATIC CURVE (FORCED THROUGH PEAK)
    # --------------------------------------------------
     from scipy.interpolate import PchipInterpolator

     interp = PchipInterpolator(x_vals, y_vals)

     x_smooth = np.linspace(x_vals.min(), x_vals.max(), 400)
     y_smooth = interp(x_smooth)

    # --------------------------------------------------
    # 4. PLOT
    # --------------------------------------------------
   
     fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

    # Smooth curve ONLY
     ax.plot(
        x_smooth,
        y_smooth,
        color='#0b2c5d',
        linewidth=2
    )

    # ❌ REMOVE BLUE POINTS (DO NOT PLOT THEM)
    # ax.scatter(x_vals, y_vals, ...)
     ax.scatter(x_vals, y_vals,color='#0b2c5d',s=40,zorder=5)

    # --------------------------------------------------
    # 5. REFERENCE LINES & PEAK
    # --------------------------------------------------
     ax.axhline(
        y=measured_max_density,
        color='#f1c232',
        linewidth=2
    )

     ax.axvline(
        x=omc,
        color='#00a651',
        linewidth=2
    )

     ax.scatter(
        [omc],
        [measured_max_density],
        marker='^',
        s=130,
        color='red',
        zorder=6
    )

    # --------------------------------------------------
    # 6. AXES & STYLE
    # --------------------------------------------------

    

    # Padding (5%)
     x_pad = (x_vals.max() - x_vals.min()) * 0.05
     y_pad = (y_vals.max() - y_vals.min()) * 0.05

     xmin = x_vals.min() - x_pad
     xmax = x_vals.max() + x_pad
     ymin = y_vals.min() - y_pad
     ymax = y_vals.max() + y_pad

    # Round nicely
     xmin = np.floor(xmin / 2) * 2
     xmax = np.ceil(xmax / 2) * 2
     ymin = np.floor(ymin * 10) / 10
     ymax = np.ceil(ymax * 10) / 10

     ax.set_xlim(xmin, xmax)
     ax.set_ylim(ymin, ymax)

    # Automatic ticks
     ax.set_xticks(np.arange(xmin, xmax + 0.1, 5))
    #  ax.set_yticks(np.arange(ymin, ymax + 0.001, 0.05))
     # Smart Y tick spacing
     y_range = ymax - ymin

     if y_range <= 0.5:
       y_step = 0.1
     elif y_range <= 1.5:
       y_step = 0.2
     elif y_range <= 3:
       y_step = 0.4
     else:
      y_step = 1.0

     ax.set_yticks(np.arange(ymin, ymax + y_step, y_step))

     ax.set_xlabel('Moisture Content (%)', fontsize=11, fontweight='bold')
     ax.set_ylabel('Dry Density (gm/cc)', fontsize=11, fontweight='bold')

     ax.set_title(
     'Moisture Density Test Results',
     fontsize=13,
     fontweight='bold',
     pad=15)
    
     ax.grid(False)

     for spine in ax.spines.values():
        spine.set_linewidth(2)
        spine.set_color('black')

    # --------------------------------------------------
    # 7. EXPORT
    # --------------------------------------------------
     buf = BytesIO()
     fig.tight_layout()
     fig.savefig(
        buf,
        format='png',
        dpi=110,
        bbox_inches='tight',
        facecolor='white'
    )
     plt.close(fig)

     buf.seek(0)
     return base64.b64encode(buf.read())


    # def generate_compaction_curve(self):
    #  self.ensure_one()

    #  import numpy as np
    #  import matplotlib.pyplot as plt
    #  from io import BytesIO
    #  import base64

    # # --------------------------------------------------
    # # 1. COLLECT DATA (IGNORE ZERO ROWS)
    # # --------------------------------------------------
    #  lines = self.soil_light_heavy_lines.filtered(
    #     lambda l: l.avg_moisture_content and l.dry_density
    # )

    #  if len(lines) < 3:
    #     return False

    #  points = sorted(
    #     [(float(l.avg_moisture_content), float(l.dry_density)) for l in lines if l.dry_density > 0],
    #     key=lambda p: p[0]
    # )

    #  x_vals = np.array([p[0] for p in points])
    #  y_vals = np.array([p[1] for p in points])

    # # --------------------------------------------------
    # # 2. PEAK (EXCEL STYLE)
    # # --------------------------------------------------
    #  max_idx = np.argmax(y_vals)
    #  omc = x_vals[max_idx]
    #  max_density = y_vals[max_idx]

    # # --------------------------------------------------
    # # 3. PLOT (STRAIGHT THROUGH POINTS)
    # # --------------------------------------------------
    #  x0 = omc
    #  y0 = max_density

    #  X = (x_vals - x0) ** 2
    #  a = np.sum((y_vals - y0) * X) / np.sum(X ** 2)

    #  def poly(x):
    #     return a * (x - x0) ** 2 + y0

    #  x_smooth = np.linspace(x_vals.min(), x_vals.max(), 400)
    #  y_smooth = poly(x_smooth)

    #  fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

    # # Line through points (EXCEL BEHAVIOUR)
    #  ax.plot(
    #     x_vals,
    #     y_vals,
    #     color='#0b2c5d',
    #     linewidth=2,
    #     marker='o',
    #     markersize=6
    # )

    # # --------------------------------------------------
    # # 4. REFERENCE LINES
    # # --------------------------------------------------
    #  ax.axhline(max_density, color='#f1c232', linewidth=2)
    #  ax.axvline(omc, color='#00a651', linewidth=2)

    #  ax.scatter([omc], [max_density], marker='^', s=140, color='red', zorder=6)

    # # --------------------------------------------------
    # # 5. AUTO AXES (FROM DATA)
    # # --------------------------------------------------
    #  x_pad = (x_vals.max() - x_vals.min()) * 0.1
    #  y_pad = (y_vals.max() - y_vals.min()) * 0.1

    #  xmin = np.floor((x_vals.min() - x_pad) / 2) * 2
    #  xmax = np.ceil((x_vals.max() + x_pad) / 2) * 2

    #  ymin = np.floor((y_vals.min() - y_pad) * 10) / 10
    #  ymax = np.ceil((y_vals.max() + y_pad) * 10) / 10

    #  ax.set_xlim(xmin, xmax)
    #  ax.set_ylim(ymin, ymax)
 
    #  ax.set_xticks(np.arange(xmin, xmax + 1, 5))
    #  ax.set_yticks(np.arange(ymin, ymax + 0.01, 0.1))

    # # --------------------------------------------------
    # # 6. LABELS
    # # --------------------------------------------------
    #  ax.set_xlabel('Moisture Content (%)', fontsize=11, fontweight='bold')
    #  ax.set_ylabel('Dry Density (gm/cc)', fontsize=11, fontweight='bold')

    #  ax.set_title('Moisture Density Test Results', fontsize=13, fontweight='bold', pad=15)

    #  ax.grid(False)

    #  for spine in ax.spines.values():
    #     spine.set_linewidth(2)
    #     spine.set_color('black')

    # # --------------------------------------------------
    # # 7. EXPORT IMAGE
    # # --------------------------------------------------
    #  buf = BytesIO()
    #  fig.tight_layout()
    #  fig.savefig(buf, format='png', dpi=110, bbox_inches='tight', facecolor='white')
    #  plt.close(fig)

    #  buf.seek(0)
    #  return base64.b64encode(buf.read())


    



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(HeavyCompactionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



    
    

class USCNewLine(models.Model):
    _name = "ucs.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id",ondelete='cascade')

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)
    is_checked = fields.Boolean(
        string="Calculated",
        default=False
    )
    start_date = fields.Date(string="Start Date")  # manually fill
    end_date = fields.Date(string="End Date")      # auto fill on submit

    

    def action_submit(self):
        self.ensure_one()
        
        # Boolean True save
        self.write({
            'is_checked': True,
            # 'end_date': fields.Date.context_today(self),  # current date auto fill
        })
        
        # Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}

    lab_id=  fields.Char(string="Lab ID" )

    ucs_diameter = fields.Float(string="Diameter (mm): ", digits=(12,0))
    ucs_area = fields.Float(string="Area (A):mm2", digits=(18,11), compute="_compute_ucs_area", store=True)
    ucs_height = fields.Float(string="Height:  mm", digits=(12,0))
    ucs_volumn = fields.Float(string="Soil Volume: cm3", digits=(18,10) , compute="_compute_ucs_volumn", store=True )

    @api.depends('ucs_diameter')
    def _compute_ucs_area(self):
        for line in self:
            if line.ucs_diameter:    
                line.ucs_area =  (pi / 4) * line.ucs_diameter * line.ucs_diameter
            else:
                line.ucs_area = 0.0


    @api.depends('ucs_diameter', 'ucs_height')
    def _compute_ucs_volumn(self):
        for line in self:
            if line.ucs_diameter and line.ucs_height:
              radius_sq = line.ucs_diameter ** 2
              area = (pi / 4) * radius_sq
              line.ucs_volumn = area * line.ucs_height
            else:
              line.ucs_volumn = 0.0

    trail_no_cell = fields.Float(string="Trial No/Cell Pressure.")
    initial_mass_bt = fields.Float(string="Initial mass of soil (before testing) (g):", digits=(12,3))
    initial_mass_at = fields.Float(string="Initial mass of soil (after testing) (g): ", digits=(12,3))
    mass_dry_soil = fields.Float(string="Mass of dry soil (g)", digits=(12,3))


    ucs_moisture_con_at = fields.Float(string="mositure content after test (%):", digits=(16,12) , compute="_compute_ucs_moisture_con_at", store=True )
    ucs_bulk_density = fields.Float(string="Bulk Density of soil (g/cc)", digits=(16,13) , compute="_compute_ucs_bulk_density", store=True ) 
    ucs_dry_density = fields.Float(string="Dry density of soil (g/cc)	", digits=(16,13) , compute="_compute_ucs_dry_density", store=True )

    ucs_specific_gravity = fields.Float(string="Specific Gravity", digits=(12,3))

    ucs_initial_moist_con = fields.Float(string="Initial Moisture content", digits=(16,12) , compute="_compute_ucs_initial_moist_con", store=True )  

    @api.depends('initial_mass_at', 'mass_dry_soil')
    def _compute_ucs_moisture_con_at(self):
        for line in self:
            if line.initial_mass_at and line.mass_dry_soil:
              water_mass  = line.initial_mass_at - line.mass_dry_soil
              line.ucs_moisture_con_at = (water_mass / line.mass_dry_soil) * 100
            else:
              line.ucs_moisture_con_at = 0.0 

    @api.depends('initial_mass_bt','ucs_diameter', 'ucs_height')
    def _compute_ucs_bulk_density(self):
        for line in self:
            if line.initial_mass_bt and line.ucs_diameter and line.ucs_height:
              radius_sq = line.ucs_diameter ** 2
              area = (pi / 4) * radius_sq
              volumn = area * line.ucs_height
              
              line.ucs_bulk_density = line.initial_mass_bt / (volumn/1000)
            else:
              line.ucs_bulk_density = 0.0  

    @api.depends('initial_mass_bt','ucs_diameter', 'ucs_height','initial_mass_at', 'mass_dry_soil',)
    def _compute_ucs_dry_density(self):
        for line in self:
            if line.initial_mass_bt and line.ucs_diameter and line.ucs_height and line.initial_mass_at and line.mass_dry_soil:
              radius_sq = line.ucs_diameter ** 2
              area = (pi / 4) * radius_sq
              volumn = area * line.ucs_height
              ucs_bulk_density = line.initial_mass_bt / (volumn/1000)
              water_mass  = line.initial_mass_at - line.mass_dry_soil
              ucs_moisture_con_at = (water_mass / line.mass_dry_soil) * 100

              line.ucs_dry_density = ucs_bulk_density /(1 + ucs_moisture_con_at/100)
            else:
              line.ucs_dry_density = 0.0  

    @api.depends('initial_mass_bt', 'mass_dry_soil')
    def _compute_ucs_initial_moist_con(self):
        for line in self:
            if line.initial_mass_bt and line.mass_dry_soil:
              water_mass  = line.initial_mass_bt - line.mass_dry_soil
              line.ucs_initial_moist_con = (water_mass / line.mass_dry_soil) * 100
            else:
              line.ucs_initial_moist_con = 0.0        

    ucs_proving_ring = fields.Float(string="Proving Ring Capacity", digits=(12,0))   

    ucs_dial_gauge = fields.Float(string="Least Count of dial guage", digits=(12,2))

    ucs_rate_dis = fields.Float(string="Displacement Rate (mm/min)", digits=(12,2))  

    ucs_room_temp = fields.Float(string="Room Temperature", digits=(12,0))
    ucs_std_temp = fields.Float(string="Std Calibration Temp")
    ucs_temp_correction = fields.Float(string="Temp correction per °C", digits=(12,3))

    temp_diff = fields.Float(string="Rise/Fall in Temperature (°C)" , compute="_compute_temp_effect",store=True)

    force_percent_change = fields.Float(string="% Rise/Fall in Force Value",compute="_compute_temp_effect",store=True)

    @api.depends('ucs_room_temp', 'ucs_std_temp', 'ucs_temp_correction')
    def _compute_temp_effect(self):
        for line in self:
            if line.ucs_room_temp and line.ucs_std_temp:
                line.temp_diff = line.ucs_room_temp - line.ucs_std_temp
                line.force_percent_change = (line.temp_diff * line.ucs_temp_correction)
            else:
                line.temp_diff = 0.0
                line.force_percent_change = 0.0  
                
    w_value = fields.Float(string="w", digits=(18,14),   compute="_compute_soil_parameters", store=True)

    gamma_ratio = fields.Float(string="γw / γd", digits=(18,15),compute="_compute_soil_parameters", store=True)

    inv_specific_gravity = fields.Float(string="1 / Gs", digits=(18,15),compute="_compute_soil_parameters", store=True)

    degree_saturation = fields.Float(string="S (%)", digits=(12,2),compute="_compute_soil_parameters", store=True) 

    

    @api.depends(
        'ucs_moisture_con_at',
        'ucs_bulk_density',
        'ucs_dry_density',
        'ucs_specific_gravity'
    )
    def _compute_soil_parameters(self):

        for line in self:

            # ---------------------------------
            # w value
            # ---------------------------------

            if line.ucs_initial_moist_con:

                # w = (
                #     line.ucs_initial_moist_con / 100
                # )
                w = (line.ucs_initial_moist_con * 0.01)

                line.w_value = w

            else:

                w = 0.0
                line.w_value = 0.0


            # ---------------------------------
            # gamma_w / gamma_d
            # ---------------------------------

            if line.ucs_dry_density:

                gamma_ratio = (
                    1.0 / line.ucs_dry_density)

                line.gamma_ratio = gamma_ratio

            else:

                gamma_ratio = 0.0
                line.gamma_ratio = 0.0


            # ---------------------------------
            # 1 / Gs
            # ---------------------------------

            if line.ucs_specific_gravity:

                inv_gs = round(
                    1.0 / line.ucs_specific_gravity,5
                )

                line.inv_specific_gravity = inv_gs

            else:

                inv_gs = 0.0
                line.inv_specific_gravity = 0.0


            # ---------------------------------
            # Degree of Saturation
            # ---------------------------------

            denominator = gamma_ratio - inv_gs

            if denominator != 0:

                line.degree_saturation = (
                    (w / denominator) * 100
                )

            else:

                line.degree_saturation = 0.0

    
    m = fields.Float(string=" (m)",default=1.6820, digits=(10,4))
    c = fields.Float(string=" (c)",default=13.644 , digits=(10,4))
  
    ucs_lines = fields.One2many('ucs.soil.line', 'parent_id_ucs',  string="DETERMINE THE UNCONFINED COMPRESSIVE STRENGTH",default=lambda self: self.default_ucs_reading())	

    @api.model
    def default_ucs_reading(self):
        default_lines = [
            (0, 0, {'horizontal_read':'0' ,'shear_stress': '0.000','axial_deformation':'0' ,'axial_strain': '0.000',}),
            
        ]
        return default_lines


    def action_compute_ucs(self):
     """Compute and SAVE UCS line values and max PR values."""
     for rec in self:
        # 1) Compute horizontal readings for each line
        for line in rec.ucs_lines:
            if line.serial_no <= 1:
                horiz = 0.0
            else:
                horiz = 25.0 * (line.serial_no - 1)
            line.horizontal_read = horiz

        # 2) MAX PR + VLOOKUP-like behaviour (once per record)
        lines = rec.ucs_lines.sorted(lambda l: l.horizontal_read)

        if not lines:
            rec.ucs_max_pr = 0.0
            rec.ucs_max_pr_horiz = 0.0
            rec.ucs_max_pr_area = 0.0
            continue

        # Excel range starts from row with horiz > 0 (skip first row with 0)
        data_lines = lines.filtered(lambda l: l.horizontal_read > 0)

        if not data_lines:
            rec.ucs_max_pr = 0.0
            rec.ucs_max_pr_horiz = 0.0
            rec.ucs_max_pr_area = 0.0
            continue

        # MAX(M22:M105)
        max_pr = max(data_lines.mapped('prove_ring_read'))
        rec.ucs_max_pr = max_pr

        # VLOOKUP(BM21, M22:BN…, 2, FALSE) → first row (top-down) with that PR
        line_max = False
        for l in data_lines:
            if l.prove_ring_read == max_pr:
                line_max = l
                break

        if line_max:
            rec.ucs_max_pr_horiz = line_max.horizontal_read   # e.g. 525
            rec.ucs_max_pr_area = line_max.corrected_area     # e.g. 12.183
        else:
            rec.ucs_max_pr_horiz = 0.0
            rec.ucs_max_pr_area = 0.0

     return True



    ucs_max_pr = fields.Float(string="Max. PR Reading", digits=(12, 2))
    ucs_max_pr_horiz = fields.Float(string="Horizontal dial @ Max PR", digits=(12, 2))
    ucs_max_pr_area = fields.Float(string="Corrected area @ Max PR", digits=(12, 3))


    axial_deform_ucs = fields.Float(string="Axial Deformation, mm" , digits=(8,1) , compute="_compute_axial_deform_ucs" , store=True)

    @api.depends('ucs_max_pr_horiz', 'ucs_dial_gauge')
    def _compute_axial_deform_ucs(self):
     for line in self:
        if line.ucs_max_pr_horiz and line.ucs_dial_gauge :
            line.axial_deform_ucs = line.ucs_max_pr_horiz * line.ucs_dial_gauge
        else:
            line.axial_deform_ucs = 0.0


    axial_strain_ucs = fields.Float(string="Axial strain %" , digits=(8,2) , compute="_compute_axial_strain_ucs" , store=True)

    @api.depends('ucs_max_pr_horiz', 'ucs_dial_gauge','ucs_height')
    def _compute_axial_strain_ucs(self):
     for line in self:
        if line.ucs_max_pr_horiz and line.ucs_dial_gauge and line.ucs_height :
            axial_deform_ucs = line.ucs_max_pr_horiz * line.ucs_dial_gauge
            line.axial_strain_ucs = (axial_deform_ucs / line.ucs_height) * 100
        else:
            line.axial_strain_ucs = 0.0

    axial_force_ucs = fields.Float(string="Axial force, kN" , digits=(8,2) , compute="_compute_axial_force_ucs" , store=True)

    @api.depends('ucs_max_pr')
    def _compute_axial_force_ucs(self):
     for line in self:
        if line.ucs_max_pr :
            line.axial_force_ucs = (((line.ucs_max_pr * 5) * 1.6825) + 14.258) / 1000
        else:
            line.axial_force_ucs = 0.0
            

    ucs_compressive_stress = fields.Float("Compressive stress (kg/cm²)", digits=(12, 2), compute="_compute_ucs_compressive_stress" , store=True)

    @api.depends('ucs_max_pr','ucs_max_pr_area','force_percent_change')
    def _compute_ucs_compressive_stress(self):
     for line in self:
        if line.ucs_max_pr and line.ucs_max_pr_area and line.force_percent_change :
            axial_force_ucs = (((line.ucs_max_pr * 5) * 1.6825) + 14.258) / 1000
            line.ucs_compressive_stress = (((axial_force_ucs * 1000) / 9.81)/ line.ucs_max_pr_area) + ((((axial_force_ucs*1000/9.81)/9.81)/line.ucs_max_pr_area) * line.force_percent_change)
        else:
            line.ucs_compressive_stress = 0.0


    graph_image_ucs = fields.Binary("Compaction Curve Graph", compute="_compute_graph_image_ucs", store=True)

    @api.depends('ucs_lines.shear_stress', 'ucs_lines.axial_strain')
    def _compute_graph_image_ucs(self):
     for record in self:
        if record.ucs_lines:
            record.graph_image_ucs = record._generate_ucs_graph()
        else:
            record.graph_image_ucs = False

    def _generate_ucs_graph(self):
     """Generate smooth UCS curve  (Axial Stress vs Axial Strain)."""
     self.ensure_one()

     # 1) Collect data (allow zero first point)
     lines = self.ucs_lines.filtered(
        lambda l: (l.shear_stress is not None) and (l.axial_strain is not None)
     )
     if len(lines) < 3:
        return False

     strain = np.array(lines.mapped('axial_strain'), dtype=float)
     stress = np.array(lines.mapped('shear_stress'), dtype=float)

     # 2) Ensure origin (0,0) is present
     if not np.any((strain == 0.0) & (stress == 0.0)):
        strain = np.insert(strain, 0, 0.0)
        stress = np.insert(stress, 0, 0.0)

     # Sort by strain
     order = np.argsort(strain)
     strain = strain[order]
     stress = stress[order]

     # 3) Cut at peak stress (remove tail)
     peak_idx = int(np.argmax(stress))
     strain_peak = strain[:peak_idx + 1]
     stress_peak = stress[:peak_idx + 1]

     # 4) Rescale strain so last point ≈ 9 %
     if strain_peak[-1] > 0:
        scale = 9.0 / strain_peak[-1]
        strain_scaled = strain_peak * scale
     else:
        strain_scaled = strain_peak

     # 5) Cubic spline on unique X
     x_unique, idx_unique = np.unique(strain_scaled, return_index=True)
     y_unique = stress_peak[idx_unique]
     if len(x_unique) < 3:
        return False

     cs = CubicSpline(x_unique, y_unique, bc_type='natural')
     x_smooth = np.linspace(x_unique.min(), x_unique.max(), 400)
     y_smooth = cs(x_smooth)

     # 6) Plot
     fig, ax = plt.subplots(figsize=(10, 5), dpi=110)

     ax.plot(x_smooth, y_smooth, color='#86b93b', linewidth=2.5)
     ax.scatter(strain_scaled, stress_peak, color='#86b93b', s=20, zorder=5)

     ax.set_xlabel('Axial Strain (%)', fontsize=11, fontweight='bold')
     ax.set_ylabel('Axial Stress (kg/sq.cm)', fontsize=11, fontweight='bold')
     ax.set_title('Unconfined Compression Test', fontsize=13, fontweight='bold')

     # Axes 0–9 and 0–1, ticks every 1 and 0.1
     ax.set_xlim(0, 10.0)
     ax.set_xticks(np.arange(0, 9.1, 1.0))
     ax.set_xticklabels([f'{v:.0f}' for v in np.arange(0, 9.1, 1.0)])

     ax.set_ylim(0, 1.0)
     ax.set_yticks(np.arange(0, 1.01, 0.1))
     ax.set_yticklabels([f'{v:.1f}' for v in np.arange(0, 1.01, 0.1)])

     ax.grid(True, alpha=0.3)

     buf = BytesIO()
     fig.tight_layout()
     fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white')
     plt.close(fig)
     buf.seek(0)
     return base64.b64encode(buf.read())

   
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(USCNewLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class DrirectShearLine(models.Model):
    _name = "direct.shear.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id",ondelete='cascade')

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)
    is_checked = fields.Boolean(
        string="Calculated",
        default=False
    )
    start_date = fields.Date(string="Start Date")  # manually fill
    end_date = fields.Date(string="End Date")      # auto fill on submit
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise ValidationError(
                        "Start Date cannot be greater than End Date."
                    )

    

    def action_submit(self):
        self.ensure_one()
        
        # Boolean True save
        self.write({
            'is_checked': True,
            # 'end_date': fields.Date.context_today(self),  # current date auto fill
        })
        
        # Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}

    lab_id=  fields.Char(string="Lab ID" )

    bh_id = fields.Char(
        string="BH ID",
        compute="_compute_direct",
        store=True
    )

    depth = fields.Char(
        string="Depth (m)",
        compute="_compute_direct",
        store=True
    )


    proving_ring_capacity = fields.Float(string="Proving ring capacity (kN)", digits=(10,0))

    dimension_sample = fields.Char(string="Dimesnions of sample (mm)",default="60 x 60 x 25") 

    sample_type = fields.Char(string="Sample Type",default="Remolded")

    type_compact = fields.Char(string="Type of compaction")

    soil_fract_20mm = fields.Char(string="Soil fraction above 20mm replaced, (Kg)")

    period_soaked = fields.Float(string="Period of soaking(days)", digits=(10,0))

    surcharge_weight = fields.Float(string="Surcharge weight (kg)", digits=(10,2))

    
    @api.depends('lab_id')
    def _compute_direct(self):
        ReviewLine = self.env['sample.request.review.lines']

        for line in self:
            line.bh_id = False
            line.depth = False

            if not line.lab_id:
                continue

            review_line = ReviewLine.search(
                [('lab_id', '=', line.lab_id)],
                order='id desc',
                limit=1
            )

            if review_line:
                line.bh_id = review_line.source        # BH ID / Location
                line.depth = review_line.depth         # Depth (m)


    



    shear_box_dimension = fields.Float(string="Shear Box Inside Dimension:", digits=(12,0))
    shear_area = fields.Float(string="Area (A):cm2", digits=(12,0) , compute="_compute_shear_area", store=True)

    @api.depends('shear_box_dimension')
    def _compute_shear_area(self):
        for line in self:
            if line.shear_box_dimension:    
                line.shear_area =  line.shear_box_dimension ** 2 
            else:
                line.shear_area = 0.0

    shear_height = fields.Float(string="Shear Box Height:  cm", digits=(12,1))
    shear_volumn = fields.Float(string="Soil Volume: cm3", digits=(12,0) , compute="_compute_shear_volumn", store=True )

    @api.depends('shear_box_dimension', 'shear_height')
    def _compute_shear_volumn(self):
        for line in self:
            if line.shear_box_dimension and line.shear_height:
              area = line.shear_box_dimension ** 2
              line.shear_volumn = area * line.shear_height
            else:
              line.shear_volumn = 0.0

    initial_mass_soil_cutter = fields.Float(string="Initial mass of soil and cutter: ", digits=(12,2))
    wt_empty_cutter = fields.Float(string="Empty Weight of cutter: ", digits=(12,3))

    initial_mass_soil = fields.Float(string="initial Mass of soil:(g)", digits=(12,3) , compute="_compute_initial_mass_soil", store=True )

    @api.depends('initial_mass_soil_cutter', 'wt_empty_cutter')
    def _compute_initial_mass_soil(self):
        for line in self:
            if line.initial_mass_soil_cutter and line.wt_empty_cutter:
              line.initial_mass_soil = line.initial_mass_soil_cutter - line.wt_empty_cutter
            else:
              line.initial_mass_soil = 0.0 

    initial_moisture_content= fields.Float(string="Initial mositure content:", digits=(12,2) , compute="_compute_initial_moisture_content", store=True )

    mass_dry_soil = fields.Float(string="Mass of dry soil at shear zone (g)", digits=(12,1) )

    @api.depends('initial_mass_soil_cutter', 'wt_empty_cutter','mass_dry_soil')
    def _compute_initial_moisture_content(self):
        for line in self:
            if line.initial_mass_soil_cutter and line.wt_empty_cutter and line.mass_dry_soil:
              initial_mass_soil = line.initial_mass_soil_cutter - line.wt_empty_cutter
              line.initial_moisture_content = ((initial_mass_soil - line.mass_dry_soil) / line.mass_dry_soil ) * 100
            else:
              line.initial_moisture_content = 0.0 

    final_wt_soil_cutter = fields.Float(string="Final wt of soil + cutter at shear zone", digits=(12,3))
    final_mass_soil = fields.Float(string="Final Mass of soil:(g) ", digits=(12,2) , compute="_compute_final_mass_soil", store=True)

    @api.depends('final_wt_soil_cutter', 'wt_empty_cutter')
    def _compute_final_mass_soil(self):
        for line in self:
            if line.final_wt_soil_cutter and line.wt_empty_cutter:
              line.final_mass_soil = line.final_wt_soil_cutter - line.wt_empty_cutter
            else:
              line.final_mass_soil = 0.0 
    

    moisture_content_shear = fields.Float(string="Moisture content at shear zone (%)", digits=(12,2) , compute="_compute_moisture_content_shear", store=True)

    @api.depends('final_wt_soil_cutter', 'wt_empty_cutter','mass_dry_soil')
    def _compute_moisture_content_shear(self):
        for line in self:
            if line.final_wt_soil_cutter and line.wt_empty_cutter and line.mass_dry_soil:
              final_mass_soil = line.final_wt_soil_cutter - line.wt_empty_cutter
              line.moisture_content_shear = ((final_mass_soil - line.mass_dry_soil) / line.mass_dry_soil ) * 100
            else:
              line.moisture_content_shear = 0.0


    density_soil_shear = fields.Float(string="Density of soil (g/cc)", digits=(12,2) , compute="_compute_density_soil_shear", store=True)

    @api.depends('shear_box_dimension', 'shear_height','initial_mass_soil_cutter', 'wt_empty_cutter')
    def _compute_density_soil_shear(self):
        for line in self:
            if line.shear_box_dimension and line.shear_height and line.initial_mass_soil_cutter and line.wt_empty_cutter:
              shear_volumn = line.shear_box_dimension ** 2 * line.shear_height
              initial_mass_soil = line.initial_mass_soil_cutter - line.wt_empty_cutter
              if shear_volumn > 0:
                line.density_soil_shear = initial_mass_soil / shear_volumn
              else:
                line.density_soil_shear = 0.0
            else:
                line.density_soil_shear = 0.0

    dry_density_soil_shear = fields.Float(string="Dry density of soil (g/cc)", digits=(12,2) , compute="_compute_dry_density_soil_shear", store=True)

    @api.depends('shear_box_dimension', 'shear_height','initial_mass_soil_cutter', 'wt_empty_cutter','mass_dry_soil')
    def _compute_dry_density_soil_shear(self):
        for line in self:
              shear_volumn = line.shear_box_dimension ** 2 * line.shear_height

              initial_mass_soil = line.initial_mass_soil_cutter - line.wt_empty_cutter

              
              if shear_volumn > 0 and line.mass_dry_soil > 0 and initial_mass_soil >= line.mass_dry_soil:

                initial_moisture_content = ((initial_mass_soil - line.mass_dry_soil) / line.mass_dry_soil ) * 100

                density_soil_shear = initial_mass_soil / shear_volumn

                line.dry_density_soil_shear = density_soil_shear / (1 + initial_moisture_content / 100)
              else:
                line.dry_density_soil_shear = 0.0

    

    normal_stress_settle = fields.Float(string="Settelement after normal stress:", digits=(12,2) )

    dry_density_stress_settle = fields.Float(string="Dry density of soil after normal stress:", digits=(12,3) , 
    compute="_compute_dry_density_stress_settle", store=True)

    @api.depends('mass_dry_soil', 'shear_area', 'shear_height', 'normal_stress_settle')
    def _compute_dry_density_stress_settle(self):
     for line in self:
        # Make sure all values are positive and valid
        if (
            line.mass_dry_soil > 0 and
            line.shear_area > 0 and
            line.shear_height > 0 and
            line.normal_stress_settle >= 0 and
            line.shear_height > (line.normal_stress_settle / 10)  # Height must be greater than settlement in cm
        ):
            # Adjusted height after settlement (cm)
            adjusted_height = line.shear_height - (line.normal_stress_settle / 10)

            # New volume = area * adjusted height
            shear_volumn = line.shear_area * adjusted_height

            # Dry density after settlement = dry mass / adjusted volume
            line.dry_density_stress_settle = line.mass_dry_soil / shear_volumn
        else:
            line.dry_density_stress_settle = 0.0


    drainage_condition = fields.Selection([
    ('UU', 'UU'),
    ('CU', 'CU'),
    ('CD', 'CD'),], string="Drainage Condition", default='UU')

    displacement_rate = fields.Float(string="Displacement rate: mm/min", digits=(12,2) , compute="_compute_displacement_rate", store=True )
    normal_stress = fields.Float(string="Normal stress: kg/cm2", digits=(12,1))

    @api.depends('drainage_condition')  # or any fields that affect displacement_rate
    def _compute_displacement_rate(self):
        for record in self:
            if record.drainage_condition == 'UU':
                record.displacement_rate = 1.25
            elif record.drainage_condition == 'CU':
                record.displacement_rate = 0.5
            else:
                record.displacement_rate = 0.25

    shear_room_temp = fields.Float(string="Room Temperature", digits=(12,1))
    direct_humidity = fields.Float(string="Humidity %" )
    shear_std_temp = fields.Float(string="Std Temp During calibr'n")
    shear_temp_correction = fields.Float(string="Temperature correction fro each deg C rise/fall (+/-)", digits=(12,3))

    shear_temp_diff = fields.Float(string="Rise/Fall in Temperature (°C)" , compute="_compute_shear_temp_effect",store=True)

    shear_force_percent_change = fields.Float(string="% Rise/Fall in Force Value",digits=(12,3) ,compute="_compute_shear_temp_effect",store=True)

    @api.depends('shear_room_temp', 'shear_std_temp', 'shear_temp_correction')
    def _compute_shear_temp_effect(self):
     for line in self:
        if line.shear_room_temp is not None and line.shear_std_temp is not None:
            line.shear_temp_diff = line.shear_room_temp - line.shear_std_temp
            line.shear_force_percent_change = line.shear_temp_diff * line.shear_temp_correction
        else:
            line.shear_temp_diff = 0.0
            line.shear_force_percent_change = 0.0



    direct_shear_ids = fields.One2many("direct.shear.test.line", "parent_id_direct_shear", string="Test Readings",default=lambda self: self.default_shear_reading())		

    @api.model
    def default_shear_reading(self):
        default_lines = [
            (0, 0, {'horizontal_read':'0','horizontal_dispalacement' : '0' ,'horizontal_shear': '0.000','horizontal_shear_temp':'0' ,'shear_stress': '0.000',}),
            (0, 0, {'horizontal_read':'25',}),
            (0, 0, {'horizontal_read':'50',}),
            (0, 0, {'horizontal_read':'75',}),
            (0, 0, {'horizontal_read':'100',}),
            (0, 0, {'horizontal_read':'125',}),
            (0, 0, {'horizontal_read':'150',}),
            (0, 0, {'horizontal_read':'175',}),
            (0, 0, {'horizontal_read':'200',}),
            (0, 0, {'horizontal_read':'225',}),
            (0, 0, {'horizontal_read':'250',}),
            (0, 0, {'horizontal_read':'275',}),
            (0, 0, {'horizontal_read':'300',}),
            (0, 0, {'horizontal_read':'325',}),
            (0, 0, {'horizontal_read':'350',}),
            (0, 0, {'horizontal_read':'375',}),
            (0, 0, {'horizontal_read':'400',}),
            (0, 0, {'horizontal_read':'425',}),
            (0, 0, {'horizontal_read':'450',}),
            (0, 0, {'horizontal_read':'475',}),
            (0, 0, {'horizontal_read':'500',}),
            (0, 0, {'horizontal_read':'525',}),
            (0, 0, {'horizontal_read':'550',}),
            (0, 0, {'horizontal_read':'575',}),
            (0, 0, {'horizontal_read':'600',}),
            (0, 0, {'horizontal_read':'625',}),
            (0, 0, {'horizontal_read':'650',}),
            (0, 0, {'horizontal_read':'675',}),
            (0, 0, {'horizontal_read':'700',}),
            (0, 0, {'horizontal_read':'725',}),
            (0, 0, {'horizontal_read':'750',}),
            (0, 0, {'horizontal_read':'775',}),
            (0, 0, {'horizontal_read':'800',}),
            (0, 0, {'horizontal_read':'825',}),
            (0, 0, {'horizontal_read':'850',}),
            (0, 0, {'horizontal_read':'875',}),
            (0, 0, {'horizontal_read':'900',}),
            (0, 0, {'horizontal_read':'925',}),
            (0, 0, {'horizontal_read':'950',}),
            (0, 0, {'horizontal_read':'975',}),
            (0, 0, {'horizontal_read':'1000',}),
            (0, 0, {'horizontal_read':'1025',}),
            (0, 0, {'horizontal_read':'1050',}),
            (0, 0, {'horizontal_read':'1075',}),
            (0, 0, {'horizontal_read':'1100',}),

            
        ]
        return default_lines

    area_type = fields.Selection([
        ('corrected', 'Corrected Area'),
        ('non_corrected', 'Non Corrected Area')
    ], string='Area Type', default='corrected')

    non_corrected_area_shear = fields.Float(string="Non Corrected Area (cm2)" , digits=(8,0))

    corrected_area_shear = fields.Float(string="Corrected Area (cm2)" , digits=(8,0))

    show_corrected_area = fields.Boolean(compute="_compute_area_visibility", store=False)
    show_non_corrected_area = fields.Boolean(compute="_compute_area_visibility", store=False)

    @api.depends('area_type')
    def _compute_area_visibility(self):
        for rec in self:
            rec.show_corrected_area = rec.area_type == 'corrected'
            rec.show_non_corrected_area = rec.area_type == 'non_corrected'

    


  
    
    shear_graph_image = fields.Binary("Shear Stress Graph")

    


    def action_generate_shear_graph(self):
     import numpy as np
     from scipy.interpolate import PchipInterpolator
     import matplotlib.pyplot as plt
     from matplotlib.ticker import MultipleLocator
     from io import BytesIO
     import base64

     for rec in self:
        strain_vals = []
        shear_vals = []

        # Collect only rows with proving ring input
        for line in rec.direct_shear_ids:
            if line.prove_ring_read and line.prove_ring_read > 0:
                strain_vals.append(line.horizontal_dispalacement or 0.0)
                shear_vals.append(line.shear_stress or 0.0)

        if not strain_vals:
            return

        # Add origin (0,0)
        strain_vals.insert(0, 0.0)
        shear_vals.insert(0, 0.0)

        # Remove negative shear values
        clean = [(x, y) for x, y in zip(strain_vals, shear_vals) if y >= 0]
        strain_vals, shear_vals = zip(*clean)

        # Convert to numpy
        x = np.array(strain_vals)
        y = np.array(shear_vals)

        # Sort by strain
        idx = np.argsort(x)
        x = x[idx]
        y = y[idx]

        # Excel-like monotonic smoothing
        interp = PchipInterpolator(x, y)
        xnew = np.linspace(x.min(), x.max(), 300)
        ynew = interp(xnew)

        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

        # Axes crossing at (0,0)
        ax.spines['left'].set_position(('data', 0))
        ax.spines['bottom'].set_position(('data', 0))
        ax.spines['right'].set_color('none')
        ax.spines['top'].set_color('none')

        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        ax.margins(x=0, y=0)

        # Plot (bold + visible)
        ax.plot(xnew, ynew, linewidth=2.5, zorder=3)
        ax.scatter(x, y, s=30, zorder=4)

        # Force X axis to stop at last point
        ax.set_xlim(left=0, right=x.max())

        ax.set_xlabel("Strain")
        ax.set_ylabel("Shear Stress")
        ax.set_ylim(bottom=0, top=y.max() * 1.05)

        # Dense ticks (lab style)
        ax.xaxis.set_major_locator(MultipleLocator(0.5))
        ax.xaxis.set_minor_locator(MultipleLocator(0.25))

        ax.yaxis.set_major_locator(MultipleLocator(0.02))
        ax.yaxis.set_minor_locator(MultipleLocator(0.01))

        # Grid behind curve
        ax.grid(which='major', alpha=0.4, zorder=0)
        ax.grid(which='minor', alpha=0.2, zorder=0)

        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read())
        buffer.close()
        plt.close(fig)

        rec.shear_graph_image = image_base64


    


    # input 2

    shear_box_dimension_2 = fields.Float(string="Shear Box Inside Dimension:", digits=(12,0))
    shear_area_2 = fields.Float(string="Area (A):cm2", digits=(12,0) , compute="_compute_shear_area_2", store=True)

    @api.depends('shear_box_dimension_2')
    def _compute_shear_area_2(self):
        for line in self:
            if line.shear_box_dimension_2:    
                line.shear_area_2 =  line.shear_box_dimension_2 ** 2 
            else:
                line.shear_area_2 = 0.0

    shear_height_2 = fields.Float(string="Shear Box Height:  cm", digits=(12,1))
    shear_volumn_2 = fields.Float(string="Soil Volume: cm3", digits=(12,0) , compute="_compute_shear_volumn_2", store=True )

    @api.depends('shear_box_dimension_2', 'shear_height_2')
    def _compute_shear_volumn_2(self):
        for line in self:
            if line.shear_box_dimension_2 and line.shear_height_2:
              area = line.shear_box_dimension_2 ** 2
              line.shear_volumn_2 = area * line.shear_height_2
            else:
              line.shear_volumn_2 = 0.0

    initial_mass_soil_cutter_2 = fields.Float(string="Initial mass of soil and cutter: ", digits=(12,2))
    wt_empty_cutter_2 = fields.Float(string="Empty Weight of cutter: ", digits=(12,3))

    initial_mass_soil_2 = fields.Float(string="initial Mass of soil:(g)", digits=(12,3) , compute="_compute_initial_mass_soil_2", store=True )

    @api.depends('initial_mass_soil_cutter_2', 'wt_empty_cutter_2')
    def _compute_initial_mass_soil_2(self):
        for line in self:
            if line.initial_mass_soil_cutter_2 and line.wt_empty_cutter_2:
              line.initial_mass_soil_2 = line.initial_mass_soil_cutter_2 - line.wt_empty_cutter_2
            else:
              line.initial_mass_soil_2 = 0.0 

    initial_moisture_content_2= fields.Float(string="Initial mositure content:", digits=(12,2) , compute="_compute_initial_moisture_content_2", store=True )

    mass_dry_soil_2 = fields.Float(string="Mass of dry soil at shear zone (g)", digits=(12,1) )

    @api.depends('initial_mass_soil_cutter_2', 'wt_empty_cutter_2','mass_dry_soil_2')
    def _compute_initial_moisture_content_2(self):
        for line in self:
            if line.initial_mass_soil_cutter_2 and line.wt_empty_cutter_2 and line.mass_dry_soil_2:
              initial_mass_soil_2 = line.initial_mass_soil_cutter_2 - line.wt_empty_cutter_2
              line.initial_moisture_content_2 = ((initial_mass_soil_2 - line.mass_dry_soil_2) / line.mass_dry_soil_2 ) * 100
            else:
              line.initial_moisture_content_2 = 0.0 

    final_wt_soil_cutter_2 = fields.Float(string="Final wt of soil + cutter at shear zone", digits=(12,3))
    final_mass_soil_2 = fields.Float(string="Final Mass of soil:(g) ", digits=(12,2) , compute="_compute_final_mass_soil_2", store=True)

    @api.depends('final_wt_soil_cutter_2', 'wt_empty_cutter_2')
    def _compute_final_mass_soil_2(self):
        for line in self:
            if line.final_wt_soil_cutter_2 and line.wt_empty_cutter_2:
              line.final_mass_soil_2 = line.final_wt_soil_cutter_2 - line.wt_empty_cutter_2
            else:
              line.final_mass_soil_2 = 0.0 
    

    moisture_content_shear_2 = fields.Float(string="Moisture content at shear zone (%)", digits=(12,2) , compute="_compute_moisture_content_shear_2", store=True)

    @api.depends('final_wt_soil_cutter_2', 'wt_empty_cutter_2','mass_dry_soil_2')
    def _compute_moisture_content_shear_2(self):
        for line in self:
            if line.final_wt_soil_cutter_2 and line.wt_empty_cutter_2 and line.mass_dry_soil_2:
              final_mass_soil_2 = line.final_wt_soil_cutter_2 - line.wt_empty_cutter_2
              line.moisture_content_shear_2 = ((final_mass_soil_2 - line.mass_dry_soil_2) / line.mass_dry_soil_2 ) * 100
            else:
              line.moisture_content_shear_2 = 0.0


    density_soil_shear_2 = fields.Float(string="Density of soil (g/cc)", digits=(12,2) , compute="_compute_density_soil_shear_2", store=True)

    @api.depends('shear_box_dimension_2', 'shear_height_2','initial_mass_soil_cutter_2', 'wt_empty_cutter_2')
    def _compute_density_soil_shear_2(self):
        for line in self:
            if line.shear_box_dimension_2 and line.shear_height_2 and line.initial_mass_soil_cutter_2 and line.wt_empty_cutter_2:
              shear_volumn_2 = line.shear_box_dimension_2 ** 2 * line.shear_height_2
              initial_mass_soil_2 = line.initial_mass_soil_cutter_2 - line.wt_empty_cutter_2
              if shear_volumn_2 > 0:
                line.density_soil_shear_2 = initial_mass_soil_2 / shear_volumn_2
              else:
                line.density_soil_shear_2 = 0.0
            else:
                line.density_soil_shear_2 = 0.0

    dry_density_soil_shear_2 = fields.Float(string="Dry density of soil (g/cc)", digits=(12,2) , compute="_compute_dry_density_soil_shear_2", store=True)

    @api.depends('shear_box_dimension_2', 'shear_height_2','initial_mass_soil_cutter_2', 'wt_empty_cutter_2','mass_dry_soil_2')
    def _compute_dry_density_soil_shear_2(self):
        for line in self:
              shear_volumn_2 = line.shear_box_dimension_2 ** 2 * line.shear_height_2

              initial_mass_soil_2 = line.initial_mass_soil_cutter_2 - line.wt_empty_cutter_2

              
              if shear_volumn_2 > 0 and line.mass_dry_soil_2 > 0 and initial_mass_soil_2 >= line.mass_dry_soil_2:

                initial_moisture_content_2 = ((initial_mass_soil_2 - line.mass_dry_soil_2) / line.mass_dry_soil_2 ) * 100

                density_soil_shear_2 = initial_mass_soil_2 / shear_volumn_2

                line.dry_density_soil_shear_2 = density_soil_shear_2 / (1 + initial_moisture_content_2 / 100)
              else:
                line.dry_density_soil_shear_2 = 0.0

    

    normal_stress_settle_2 = fields.Float(string="Settelement after normal stress:", digits=(12,2) )

    dry_density_stress_settle_2 = fields.Float(string="Dry density of soil after normal stress:", digits=(12,3) , 
    compute="_compute_dry_density_stress_settle_2", store=True)

    @api.depends('mass_dry_soil_2', 'shear_area_2', 'shear_height_2', 'normal_stress_settle_2')
    def _compute_dry_density_stress_settle_2(self):
     for line in self:
        # Make sure all values are positive and valid
        if (
            line.mass_dry_soil_2 > 0 and
            line.shear_area_2 > 0 and
            line.shear_height_2 > 0 and
            line.normal_stress_settle_2 >= 0 and
            line.shear_height_2 > (line.normal_stress_settle_2 / 10)  # Height must be greater than settlement in cm
        ):
            # Adjusted height after settlement (cm)
            adjusted_height = line.shear_height_2 - (line.normal_stress_settle_2 / 10)

            # New volume = area * adjusted height
            shear_volumn_2 = line.shear_area_2 * adjusted_height

            # Dry density after settlement = dry mass / adjusted volume
            line.dry_density_stress_settle_2 = line.mass_dry_soil_2 / shear_volumn_2
        else:
            line.dry_density_stress_settle_2 = 0.0


    
    normal_stress_2 = fields.Float(string="Normal stress: kg/cm2", digits=(12,1))


    direct_shear_ids_2 = fields.One2many("direct.shear.test.two.line", "parent_id_direct2", string="Test Readings",default=lambda self: self.default_shear_reading_2())		

    @api.model
    def default_shear_reading_2(self):
        default_lines = [
            (0, 0, {'horizontal_read':'0','horizontal_dispalacement' : '0' ,'horizontal_shear': '0.000','horizontal_shear_temp':'0' ,'shear_stress': '0.000',}),
            (0, 0, {'horizontal_read':'25',}),
            (0, 0, {'horizontal_read':'50',}),
            (0, 0, {'horizontal_read':'75',}),
            (0, 0, {'horizontal_read':'100',}),
            (0, 0, {'horizontal_read':'125',}),
            (0, 0, {'horizontal_read':'150',}),
            (0, 0, {'horizontal_read':'175',}),
            (0, 0, {'horizontal_read':'200',}),
            (0, 0, {'horizontal_read':'225',}),
            (0, 0, {'horizontal_read':'250',}),
            (0, 0, {'horizontal_read':'275',}),
            (0, 0, {'horizontal_read':'300',}),
            (0, 0, {'horizontal_read':'325',}),
            (0, 0, {'horizontal_read':'350',}),
            (0, 0, {'horizontal_read':'375',}),
            (0, 0, {'horizontal_read':'400',}),
            (0, 0, {'horizontal_read':'425',}),
            (0, 0, {'horizontal_read':'450',}),
            (0, 0, {'horizontal_read':'475',}),
            (0, 0, {'horizontal_read':'500',}),
            (0, 0, {'horizontal_read':'525',}),
            (0, 0, {'horizontal_read':'550',}),
            (0, 0, {'horizontal_read':'575',}),
            (0, 0, {'horizontal_read':'600',}),
            (0, 0, {'horizontal_read':'625',}),
            (0, 0, {'horizontal_read':'650',}),
            (0, 0, {'horizontal_read':'675',}),
            (0, 0, {'horizontal_read':'700',}),
            (0, 0, {'horizontal_read':'725',}),
            (0, 0, {'horizontal_read':'750',}),
            (0, 0, {'horizontal_read':'775',}),
            (0, 0, {'horizontal_read':'800',}),
            (0, 0, {'horizontal_read':'825',}),
            (0, 0, {'horizontal_read':'850',}),
            (0, 0, {'horizontal_read':'875',}),
            (0, 0, {'horizontal_read':'900',}),
            (0, 0, {'horizontal_read':'925',}),
            (0, 0, {'horizontal_read':'950',}),
            (0, 0, {'horizontal_read':'975',}),
            (0, 0, {'horizontal_read':'1000',}),
            (0, 0, {'horizontal_read':'1025',}),
            (0, 0, {'horizontal_read':'1050',}),
            (0, 0, {'horizontal_read':'1075',}),
            (0, 0, {'horizontal_read':'1100',}),

            
        ]
        return default_lines
    

    shear_graph_image_2 = fields.Binary("Shear Stress Graph")

  

    import base64
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from io import BytesIO

    # def action_generate_shear_graph_2(self):
    #  for rec in self:
    #     data = []

    #     # 🔴 FORCE ORIGIN POINT (0,0)
    #     data.append((0.0, 0.0))

    #     for line in rec.direct_shear_ids_2:
    #         if line.horizontal_dispalacement is not None and line.shear_stress is not None:
    #             data.append((line.horizontal_dispalacement, line.shear_stress))

    #     if len(data) <= 1:
    #         rec.shear_graph_image_2 = False
    #         continue

    #     # SORT BY STRAIN
    #     data.sort(key=lambda x: x[0])

    #     # CUT AT PEAK SHEAR STRESS (NO POST-FAILURE)
    #     shear_vals_all = [y for _, y in data]
    #     peak_index = shear_vals_all.index(max(shear_vals_all))
    #     data = data[:peak_index + 1]

    #     strain_vals, shear_vals = zip(*data)

    #     # FIGURE SIZE LIKE EXCEL
    #     fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

    #     # EXCEL BLUE SMOOTH LINE
    #     ax.plot(
    #         strain_vals,
    #         shear_vals,
    #         color='#4472C4',
    #         linewidth=2.2
    #     )

    #     # LABELS (EXACT)
    #     ax.set_xlabel("Strain", fontsize=11)
    #     ax.set_ylabel("Shear stress, τ", fontsize=11)

    #     # AXIS LIMITS (MATCH IMAGE)
    #     ax.set_xlim(0, 6)
    #     ax.set_ylim(0, 0.30)

    #     # HORIZONTAL GRID ONLY
    #     ax.yaxis.grid(True, color='#BFBFBF', linewidth=0.6)
    #     ax.xaxis.grid(False)

    #     # EXCEL-LIKE BORDER
    #     for spine in ax.spines.values():
    #         spine.set_color('#808080')
    #         spine.set_linewidth(0.8)

    #     ax.tick_params(labelsize=9)

    #     buffer = BytesIO()
    #     fig.savefig(buffer, format='png', bbox_inches='tight', facecolor='white')
    #     buffer.seek(0)

    #     rec.shear_graph_image_2 = base64.b64encode(buffer.read())

    #     buffer.close()
    #     plt.close(fig)

    def action_generate_shear_graph_2(self):
     import numpy as np
     from scipy.interpolate import PchipInterpolator
     import matplotlib.pyplot as plt
     from matplotlib.ticker import MultipleLocator, MaxNLocator
     from io import BytesIO
     import base64
     from collections import defaultdict

     for rec in self:
        strain_vals = []
        shear_vals = []

        # ✅ Collect only actual input rows
        for line in rec.direct_shear_ids_2:
            if line.horizontal_dispalacement is not None and line.shear_stress is not None:
                strain_vals.append(line.horizontal_dispalacement or 0.0)
                shear_vals.append(line.shear_stress or 0.0)

        if not strain_vals:
            rec.shear_graph_image_2 = False
            continue

        # ✅ Add origin
        strain_vals.insert(0, 0.0)
        shear_vals.insert(0, 0.0)

        # ✅ Remove negative values
        clean = [(x, y) for x, y in zip(strain_vals, shear_vals) if y >= 0]
        if not clean:
            rec.shear_graph_image_2 = False
            continue

        strain_vals, shear_vals = zip(*clean)

        x = np.array(strain_vals)
        y = np.array(shear_vals)

        # ✅ Sort
        idx = np.argsort(x)
        x = x[idx]
        y = y[idx]

        # ✅ Remove duplicate X (important for interpolation)
        temp = defaultdict(list)
        for xi, yi in zip(x, y):
            temp[xi].append(yi)

        x = np.array(sorted(temp.keys()))
        y = np.array([sum(vals)/len(vals) for vals in temp.values()])

        # ✅ Safety check
        if len(x) < 2:
            rec.shear_graph_image_2 = False
            continue

        # ✅ CUT AFTER PEAK (removes vertical drop)
        peak_index = np.argmax(y)
        x = x[:peak_index + 1]
        y = y[:peak_index + 1]

        # ✅ Smooth curve (OPTIONAL but nice)
        interp = PchipInterpolator(x, y)
        xnew = np.linspace(x.min(), x.max(), 300)
        ynew = interp(xnew)

        # ---------------- PLOT ---------------- #
        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

        # Axes at origin
        ax.spines['left'].set_position(('data', 0))
        ax.spines['bottom'].set_position(('data', 0))
        ax.spines['right'].set_color('none')
        ax.spines['top'].set_color('none')

        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        ax.margins(x=0, y=0)

        # ✅ Smooth curve
        ax.plot(xnew, ynew, linewidth=2.5, zorder=2)

        # ✅ ONLY real input points (IMPORTANT)
        ax.scatter(x, y, s=35, zorder=3)

        # Limits
        ax.set_xlim(left=0, right=x.max())
        ax.set_ylim(bottom=0, top=y.max() * 1.05)

        # Labels
        ax.set_xlabel("Strain")
        ax.set_ylabel("Shear Stress")

        # ✅ CLEAN Y AXIS (no crowding)
        ax.yaxis.set_major_locator(MaxNLocator(6))   # max 6 labels
        ax.yaxis.set_minor_locator(MultipleLocator(0.05))

        ax.xaxis.set_major_locator(MultipleLocator(0.5))
        ax.xaxis.set_minor_locator(MultipleLocator(0.25))

        # Grid
        ax.grid(which='major', alpha=0.4, zorder=0)
        ax.grid(which='minor', alpha=0.2, zorder=0)

        # Save image
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)

        rec.shear_graph_image_2 = base64.b64encode(buffer.read())

        buffer.close()
        plt.close(fig)




    # input 3

    shear_box_dimension_3 = fields.Float(string="Shear Box Inside Dimension:", digits=(12,0))
    shear_area_3 = fields.Float(string="Area (A):cm2", digits=(12,0) , compute="_compute_shear_area_3", store=True)

    @api.depends('shear_box_dimension_3')
    def _compute_shear_area_3(self):
        for line in self:
            if line.shear_box_dimension_3:    
                line.shear_area_3 =  line.shear_box_dimension_3 ** 2 
            else:
                line.shear_area_3 = 0.0

    shear_height_3 = fields.Float(string="Shear Box Height:  cm", digits=(12,1))
    shear_volumn_3 = fields.Float(string="Soil Volume: cm3", digits=(12,0) , compute="_compute_shear_volumn_3", store=True )

    @api.depends('shear_box_dimension_3', 'shear_height_3')
    def _compute_shear_volumn_3(self):
        for line in self:
            if line.shear_box_dimension_3 and line.shear_height_3:
              area = line.shear_box_dimension_3 ** 2
              line.shear_volumn_3 = area * line.shear_height_3
            else:
              line.shear_volumn_3 = 0.0

    initial_mass_soil_cutter_3 = fields.Float(string="Initial mass of soil and cutter: ", digits=(12,2))
    wt_empty_cutter_3 = fields.Float(string="Empty Weight of cutter: ", digits=(12,3))

    initial_mass_soil_3 = fields.Float(string="initial Mass of soil:(g)", digits=(12,3) , compute="_compute_initial_mass_soil_3", store=True )

    @api.depends('initial_mass_soil_cutter_3', 'wt_empty_cutter_3')
    def _compute_initial_mass_soil_3(self):
        for line in self:
            if line.initial_mass_soil_cutter_3 and line.wt_empty_cutter_3:
              line.initial_mass_soil_3 = line.initial_mass_soil_cutter_3 - line.wt_empty_cutter_3
            else:
              line.initial_mass_soil_3 = 0.0 

    initial_moisture_content_3= fields.Float(string="Initial mositure content:", digits=(12,2) , compute="_compute_initial_moisture_content_3", store=True )

    mass_dry_soil_3 = fields.Float(string="Mass of dry soil at shear zone (g)", digits=(12,1) )

    @api.depends('initial_mass_soil_cutter_3', 'wt_empty_cutter_3','mass_dry_soil_3')
    def _compute_initial_moisture_content_3(self):
        for line in self:
            if line.initial_mass_soil_cutter_3 and line.wt_empty_cutter_3 and line.mass_dry_soil_3:
              initial_mass_soil_3 = line.initial_mass_soil_cutter_3 - line.wt_empty_cutter_3
              line.initial_moisture_content_3 = ((initial_mass_soil_3 - line.mass_dry_soil_3) / line.mass_dry_soil_3 ) * 100
            else:
              line.initial_moisture_content_3 = 0.0  

    final_wt_soil_cutter_3 = fields.Float(string="Final wt of soil + cutter at shear zone", digits=(12,3))
    final_mass_soil_3 = fields.Float(string="Final Mass of soil:(g) ", digits=(12,2) , compute="_compute_final_mass_soil_3", store=True)

    @api.depends('final_wt_soil_cutter_3', 'wt_empty_cutter_3')
    def _compute_final_mass_soil_3(self):
        for line in self:
            if line.final_wt_soil_cutter_3 and line.wt_empty_cutter_3:
              line.final_mass_soil_3 = line.final_wt_soil_cutter_3 - line.wt_empty_cutter_3
            else:
              line.final_mass_soil_3 = 0.0 
    

    moisture_content_shear_3 = fields.Float(string="Moisture content at shear zone (%)", digits=(12,2) , compute="_compute_moisture_content_shear_3", store=True)

    @api.depends('final_wt_soil_cutter_3', 'wt_empty_cutter_3','mass_dry_soil_3')
    def _compute_moisture_content_shear_3(self):
        for line in self:
            if line.final_wt_soil_cutter_3 and line.wt_empty_cutter_3 and line.mass_dry_soil_3:
              final_mass_soil_3 = line.final_wt_soil_cutter_3 - line.wt_empty_cutter_3
              line.moisture_content_shear_3 = ((final_mass_soil_3 - line.mass_dry_soil_3) / line.mass_dry_soil_3 ) * 100
            else:
              line.moisture_content_shear_3 = 0.0


    density_soil_shear_3 = fields.Float(string="Density of soil (g/cc)", digits=(12,2) , compute="_compute_density_soil_shear_3", store=True)

    @api.depends('shear_box_dimension_3', 'shear_height_3','initial_mass_soil_cutter_3', 'wt_empty_cutter_3')
    def _compute_density_soil_shear_3(self):
        for line in self:
            if line.shear_box_dimension_3 and line.shear_height_3 and line.initial_mass_soil_cutter_3 and line.wt_empty_cutter_3:
              shear_volumn_3 = line.shear_box_dimension_3 ** 2 * line.shear_height_3
              initial_mass_soil_3 = line.initial_mass_soil_cutter_3 - line.wt_empty_cutter_3
              if shear_volumn_3 > 0:
                line.density_soil_shear_2 = initial_mass_soil_3 / shear_volumn_3
              else:
                line.density_soil_shear_3 = 0.0
            else:
                line.density_soil_shear_3 = 0.0

    dry_density_soil_shear_3 = fields.Float(string="Dry density of soil (g/cc)", digits=(12,2) , compute="_compute_dry_density_soil_shear_3", store=True)

    @api.depends('shear_box_dimension_3', 'shear_height_3','initial_mass_soil_cutter_3', 'wt_empty_cutter_3','mass_dry_soil_3')
    def _compute_dry_density_soil_shear_3(self):
        for line in self:
              shear_volumn_3 = line.shear_box_dimension_3 ** 2 * line.shear_height_3

              initial_mass_soil_3 = line.initial_mass_soil_cutter_3 - line.wt_empty_cutter_3

              
              if shear_volumn_3 > 0 and line.mass_dry_soil_3 > 0 and initial_mass_soil_3 >= line.mass_dry_soil_3:

                initial_moisture_content_3 = ((initial_mass_soil_3 - line.mass_dry_soil_3) / line.mass_dry_soil_3 ) * 100

                density_soil_shear_3 = initial_mass_soil_3 / shear_volumn_3

                line.dry_density_soil_shear_3 = density_soil_shear_3 / (1 + initial_moisture_content_3 / 100)
              else:
                line.dry_density_soil_shear_3 = 0.0

    

    normal_stress_settle_3 = fields.Float(string="Settelement after normal stress:", digits=(12,2) )

    dry_density_stress_settle_3 = fields.Float(string="Dry density of soil after normal stress:", digits=(12,3) , 
    compute="_compute_dry_density_stress_settle_3", store=True)

    @api.depends('mass_dry_soil_3', 'shear_area_3', 'shear_height_3', 'normal_stress_settle_3')
    def _compute_dry_density_stress_settle_3(self):
     for line in self:
        # Make sure all values are positive and valid
        if (
            line.mass_dry_soil_3 > 0 and
            line.shear_area_3 > 0 and
            line.shear_height_3 > 0 and
            line.normal_stress_settle_3 >= 0 and
            line.shear_height_3 > (line.normal_stress_settle_3 / 10)  # Height must be greater than settlement in cm
        ):
            # Adjusted height after settlement (cm)
            adjusted_height = line.shear_height_3 - (line.normal_stress_settle_3 / 10)

            # New volume = area * adjusted height
            shear_volumn_3 = line.shear_area_3 * adjusted_height

            # Dry density after settlement = dry mass / adjusted volume
            line.dry_density_stress_settle_3 = line.mass_dry_soil_3 / shear_volumn_3
        else:
            line.dry_density_stress_settle_3 = 0.0


    
    normal_stress_3 = fields.Float(string="Normal stress: kg/cm2", digits=(12,1))

    direct_shear_ids_3 = fields.One2many("direct.shear.test.three.line", "parent_id_direct3", string="Test Readings",default=lambda self: self.default_shear_reading_3())		

    @api.model
    def default_shear_reading_3(self):
        default_lines = [
            (0, 0, {'horizontal_read':'0','horizontal_dispalacement' : '0' ,'horizontal_shear': '0.000','horizontal_shear_temp':'0' ,'shear_stress': '0.000',}),
            (0, 0, {'horizontal_read':'25',}),
            (0, 0, {'horizontal_read':'50',}),
            (0, 0, {'horizontal_read':'75',}),
            (0, 0, {'horizontal_read':'100',}),
            (0, 0, {'horizontal_read':'125',}),
            (0, 0, {'horizontal_read':'150',}),
            (0, 0, {'horizontal_read':'175',}),
            (0, 0, {'horizontal_read':'200',}),
            (0, 0, {'horizontal_read':'225',}),
            (0, 0, {'horizontal_read':'250',}),
            (0, 0, {'horizontal_read':'275',}),
            (0, 0, {'horizontal_read':'300',}),
            (0, 0, {'horizontal_read':'325',}),
            (0, 0, {'horizontal_read':'350',}),
            (0, 0, {'horizontal_read':'375',}),
            (0, 0, {'horizontal_read':'400',}),
            (0, 0, {'horizontal_read':'425',}),
            (0, 0, {'horizontal_read':'450',}),
            (0, 0, {'horizontal_read':'475',}),
            (0, 0, {'horizontal_read':'500',}),
            (0, 0, {'horizontal_read':'525',}),
            (0, 0, {'horizontal_read':'550',}),
            (0, 0, {'horizontal_read':'575',}),
            (0, 0, {'horizontal_read':'600',}),
            (0, 0, {'horizontal_read':'625',}),
            (0, 0, {'horizontal_read':'650',}),
            (0, 0, {'horizontal_read':'675',}),
            (0, 0, {'horizontal_read':'700',}),
            (0, 0, {'horizontal_read':'725',}),
            (0, 0, {'horizontal_read':'750',}),
            (0, 0, {'horizontal_read':'775',}),
            (0, 0, {'horizontal_read':'800',}),
            (0, 0, {'horizontal_read':'825',}),
            (0, 0, {'horizontal_read':'850',}),
            (0, 0, {'horizontal_read':'875',}),
            (0, 0, {'horizontal_read':'900',}),
            (0, 0, {'horizontal_read':'925',}),
            (0, 0, {'horizontal_read':'950',}),
            (0, 0, {'horizontal_read':'975',}),
            (0, 0, {'horizontal_read':'1000',}),
            (0, 0, {'horizontal_read':'1025',}),
            (0, 0, {'horizontal_read':'1050',}),
            (0, 0, {'horizontal_read':'1075',}),
            (0, 0, {'horizontal_read':'1100',}),

            
        ]
        return default_lines
    

    shear_graph_image_3 = fields.Binary("Shear Stress Graph")

    import base64
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from io import BytesIO
    import math

    # def action_generate_shear_graph_3(self):
    #  for rec in self:
    #     data = []

    #     # 1️⃣ FORCE ORIGIN
    #     data.append((0.0, 0.0))

    #     # 2️⃣ COLLECT DATA
    #     for line in rec.direct_shear_ids_3:
    #         if line.horizontal_dispalacement is not None and line.shear_stress is not None:
    #             data.append((line.horizontal_dispalacement, line.shear_stress))

    #     if len(data) <= 1:
    #         rec.shear_graph_image_3 = False
    #         continue

    #     # 3️⃣ SORT BY STRAIN
    #     data.sort(key=lambda x: x[0])

    #     # 4️⃣ CUT AT PEAK SHEAR STRESS
    #     shear_vals_all = [y for _, y in data]
    #     peak_index = shear_vals_all.index(max(shear_vals_all))
    #     data = data[:peak_index + 1]

    #     strain_vals, shear_vals = zip(*data)

    #     # 5️⃣ AXIS LIMITS (MATCH EXCEL IMAGE)
    #     x_max = 7
    #     y_max = 0.40

    #     # 6️⃣ CREATE FIGURE
    #     fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

    #     # 7️⃣ PLOT — LINE WITH DIAMOND MARKERS (🔥 KEY CHANGE 🔥)
    #     ax.plot(
    #         strain_vals,
    #         shear_vals,
    #         color='#4472C4',        # Excel blue
    #         linewidth=2.2,
    #         marker='D',             # Diamond marker
    #         markersize=4,
    #         markerfacecolor='#4472C4',
    #         markeredgewidth=0
    #     )

    #     # 8️⃣ LABELS (EXACT)
    #     ax.set_xlabel("Strain", fontsize=11)
    #     ax.set_ylabel("Shear stress, τ", fontsize=11)

    #     # 9️⃣ AXIS LIMITS
    #     ax.set_xlim(0, x_max)
    #     ax.set_ylim(0, y_max)

    #     # 🔟 GRID — HORIZONTAL ONLY
    #     ax.yaxis.grid(True, color='#BFBFBF', linewidth=0.6)
    #     ax.xaxis.grid(False)

    #     # 1️⃣1️⃣ BORDER (EXCEL STYLE)
    #     for spine in ax.spines.values():
    #         spine.set_color('#808080')
    #         spine.set_linewidth(0.8)

    #     ax.tick_params(labelsize=9)

    #     # SAVE IMAGE
    #     buffer = BytesIO()
    #     fig.savefig(buffer, format='png', bbox_inches='tight', facecolor='white')
    #     buffer.seek(0)

    #     rec.shear_graph_image_3 = base64.b64encode(buffer.read())

    #     buffer.close()
    #     plt.close(fig)


    def action_generate_shear_graph_3(self):
     import numpy as np
     from scipy.interpolate import PchipInterpolator
     import matplotlib.pyplot as plt
     from matplotlib.ticker import MultipleLocator, MaxNLocator
     from io import BytesIO
     import base64
     from collections import defaultdict

     for rec in self:
        strain_vals = []
        shear_vals = []

        # ✅ Collect data
        for line in rec.direct_shear_ids_3:
            if line.horizontal_dispalacement is not None and line.shear_stress is not None:
                strain_vals.append(line.horizontal_dispalacement or 0.0)
                shear_vals.append(line.shear_stress or 0.0)

        if not strain_vals:
            rec.shear_graph_image_3 = False
            continue

        # ✅ Add origin
        strain_vals.insert(0, 0.0)
        shear_vals.insert(0, 0.0)

        # ✅ Remove negative
        clean = [(x, y) for x, y in zip(strain_vals, shear_vals) if y >= 0]
        if not clean:
            rec.shear_graph_image_3 = False
            continue

        strain_vals, shear_vals = zip(*clean)

        x = np.array(strain_vals)
        y = np.array(shear_vals)

        # ✅ Sort
        idx = np.argsort(x)
        x = x[idx]
        y = y[idx]

        # ✅ Remove duplicates (IMPORTANT)
        temp = defaultdict(list)
        for xi, yi in zip(x, y):
            temp[xi].append(yi)

        x = np.array(sorted(temp.keys()))
        y = np.array([sum(vals)/len(vals) for vals in temp.values()])

        # Safety
        if len(x) < 2:
            rec.shear_graph_image_3 = False
            continue

        # ✅ CUT AT PEAK
        peak_index = np.argmax(y)
        x = x[:peak_index + 1]
        y = y[:peak_index + 1]

        # ✅ Smooth curve
        interp = PchipInterpolator(x, y)
        xnew = np.linspace(x.min(), x.max(), 300)
        ynew = interp(xnew)

        # ---------------- PLOT ---------------- #
        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

        # Axes at origin
        ax.spines['left'].set_position(('data', 0))
        ax.spines['bottom'].set_position(('data', 0))
        ax.spines['right'].set_color('none')
        ax.spines['top'].set_color('none')

        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        ax.margins(x=0, y=0)

        # ✅ Smooth line
        ax.plot(xnew, ynew, linewidth=2.5, zorder=2)

        # ✅ ONLY real input points
        ax.scatter(x, y, s=35, zorder=3)

        # Limits
        ax.set_xlim(left=0, right=x.max())
        ax.set_ylim(bottom=0, top=y.max() * 1.05)

        # Labels
        ax.set_xlabel("Strain")
        ax.set_ylabel("Shear Stress")

        # ✅ Clean axis
        ax.yaxis.set_major_locator(MaxNLocator(6))
        ax.yaxis.set_minor_locator(MultipleLocator(0.05))

        ax.xaxis.set_major_locator(MultipleLocator(0.5))
        ax.xaxis.set_minor_locator(MultipleLocator(0.25))

        # Grid
        ax.grid(which='major', alpha=0.4, zorder=0)
        ax.grid(which='minor', alpha=0.2, zorder=0)

        # Save
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)

        rec.shear_graph_image_3 = base64.b64encode(buffer.read())

        buffer.close()
        plt.close(fig)


    # Shear Stress Vs Normal Stress			
    shear_test_final1 = fields.Float( string='Shear stress kg/cm2 ' , digits=(10,3) ,compute='_compute_shear_test_final1',store=True,)

    @api.depends('direct_shear_ids.shear_stress')
    def _compute_shear_test_final1(self):
        for rec in self:
            shear_values = rec.direct_shear_ids.mapped('shear_stress')
            rec.shear_test_final1 = max(shear_values) if shear_values else 0.0

    shear_test_final2 = fields.Float( string='Shear stress kg/cm2 ' , digits=(10,3) ,compute='_compute_shear_test_final2',store=True,)

    @api.depends('direct_shear_ids_2.shear_stress')
    def _compute_shear_test_final2(self):
        for rec in self:
            shear_values = rec.direct_shear_ids_2.mapped('shear_stress')
            rec.shear_test_final2 = max(shear_values) if shear_values else 0.0

    shear_test_final3 = fields.Float( string='Shear stress kg/cm2 ' , digits=(10,3) ,compute='_compute_shear_test_final3',store=True,)

    @api.depends('direct_shear_ids_3.shear_stress')
    def _compute_shear_test_final3(self):
        for rec in self:
            shear_values = rec.direct_shear_ids_3.mapped('shear_stress')
            rec.shear_test_final3 = max(shear_values) if shear_values else 0.0


    mass_of_soil_finals1 = fields.Float( string='Shear stress kg/cm2 ' , digits=(10,3) ,compute='_compute_mass_of_soil_finals',store=True,)

    mass_of_soil_finals = fields.Float( string='Shear stress kg/cm2 ' , digits=(10,2) ,compute='_compute_mass_of_soil_finals',store=True,)

    @api.depends('initial_mass_soil', 'initial_mass_soil_2','initial_mass_soil_3')
    def _compute_mass_of_soil_finals(self):
        for line in self:
            mass_of_soil_finals1 = 0.0
            if line.initial_mass_soil and line.initial_mass_soil_2 and line.initial_mass_soil_3:
               mass_of_soil_finals1 = line.initial_mass_soil + line.initial_mass_soil_2 + line.initial_mass_soil_3
               line.mass_of_soil_finals1 = mass_of_soil_finals1
               line.mass_of_soil_finals = mass_of_soil_finals1 / 3

            else:
              line.mass_of_soil_finals = 0.0

    dry_wt_soil_final1 = fields.Float( string='DRY WT SOIL ' , digits=(10,3) ,compute='_compute_dry_wt_soil_final',store=True,)

    dry_wt_soil_final = fields.Float( string='DRY WT SOIL ' , digits=(10,2) ,compute='_compute_dry_wt_soil_final',store=True,)

    @api.depends('mass_dry_soil', 'mass_dry_soil_2','mass_dry_soil_3')
    def _compute_dry_wt_soil_final(self):
        for line in self:
            dry_wt_soil_final1 = 0.0
            if line.mass_dry_soil and line.mass_dry_soil_2 and line.mass_dry_soil_3:
               dry_wt_soil_final1 = line.mass_dry_soil + line.mass_dry_soil_2 + line.mass_dry_soil_3
               line.dry_wt_soil_final1 = dry_wt_soil_final1
               line.dry_wt_soil_final = dry_wt_soil_final1 / 3

            else:
              line.dry_wt_soil_final = 0.0

    dry_wt_soil_final1 = fields.Float( string='DRY WT SOIL ' , digits=(10,3) ,compute='_compute_dry_wt_soil_final',store=True,)

    dry_wt_soil_final = fields.Float( string='DRY WT SOIL ' , digits=(10,2) ,compute='_compute_dry_wt_soil_final',store=True,)

    @api.depends('mass_dry_soil', 'mass_dry_soil_2','mass_dry_soil_3')
    def _compute_dry_wt_soil_final(self):
        for line in self:
            dry_wt_soil_final1 = 0.0
            if line.mass_dry_soil and line.mass_dry_soil_2 and line.mass_dry_soil_3:
               dry_wt_soil_final1 = line.mass_dry_soil + line.mass_dry_soil_2 + line.mass_dry_soil_3
               line.dry_wt_soil_final1 = dry_wt_soil_final1
               line.dry_wt_soil_final = dry_wt_soil_final1 / 3

            else:
              line.dry_wt_soil_final = 0.0

    initial_mc_final1 = fields.Float( string='NMC ' , digits=(16,8) ,compute='_compute_initial_mc_final',store=True,)

    initial_mc_final = fields.Float( string='NMC ' , digits=(10,2) ,compute='_compute_initial_mc_final',store=True,)

    @api.depends('initial_moisture_content', 'initial_moisture_content_2','initial_moisture_content_3')
    def _compute_initial_mc_final(self):
        for line in self:
            initial_mc_final1 = 0.0
            if line.initial_moisture_content and line.initial_moisture_content_2 and line.initial_moisture_content_3:
               initial_mc_final1 = line.initial_moisture_content + line.initial_moisture_content_2 + line.initial_moisture_content_3
               line.initial_mc_final1 = initial_mc_final1
               line.initial_mc_final = initial_mc_final1 / 3

            else:
              line.initial_mc_final = 0.0

    dry_density_final1 = fields.Float( string='DRY DENSITY ' , digits=(16,2) ,compute='_compute_dry_density_final',store=True,)

    dry_density_final = fields.Float( string='DRY DENSITY ' , digits=(10,2) ,compute='_compute_dry_density_final',store=True,)

    @api.depends('dry_density_soil_shear', 'dry_density_soil_shear_2','dry_density_soil_shear_3')
    def _compute_dry_density_final(self):
        for line in self:
            dry_density_final1 = 0.0
            if line.dry_density_soil_shear and line.dry_density_soil_shear_2 and line.dry_density_soil_shear_3:
               dry_density_final1 = line.dry_density_soil_shear + line.dry_density_soil_shear_2 + line.dry_density_soil_shear_3
               line.dry_density_final1 = dry_density_final1
               line.dry_density_final = dry_density_final1 / 3

            else:
              line.dry_density_final = 0.0

 

    bulk_density_final1 = fields.Float( string='BULK DENSITY ' , digits=(10,2) ,compute='_compute_bulk_density_finals',store=True,)

    bulk_density_final = fields.Float( string='BULK DENSITY ' , digits=(10,2) ,compute='_compute_bulk_density_finals',store=True,)

    @api.depends('density_soil_shear', 'density_soil_shear_2', 'density_soil_shear_3')
    def _compute_bulk_density_finals(self):
     for line in self:
        # ✅ ALWAYS reset
        line.bulk_density_final1 = 0.0
        line.bulk_density_final = 0.0

        values = [
            line.density_soil_shear,
            line.density_soil_shear_2,
            line.density_soil_shear_3,
        ]

        values = [v for v in values if v not in (None, False)]

        if values:
            total = sum(values)
            line.bulk_density_final1 = total
            line.bulk_density_final = total / len(values)

    

    phi = fields.Float(string='Phi (°)',digits=(10, 3),compute='_compute_phi_cohesion',store=True)

    cohesion = fields.Float(string='Cohesion (kg/cm2)', digits=(10, 3),compute='_compute_phi_cohesion',store=True)

    

    @api.depends(
    'shear_test_final1', 'shear_test_final2', 'shear_test_final3',
    'normal_stress', 'normal_stress_2', 'normal_stress_3'
)
    def _compute_phi_cohesion(self):
     for rec in self:
        # 🔴 Always reset stored fields
        rec.phi = 0.0
        rec.cohesion = 0.0

        # X = Normal stress, Y = Shear stress
        x = [
            round(rec.normal_stress or 0.0, 3),
            round(rec.normal_stress_2 or 0.0, 3),
            round(rec.normal_stress_3 or 0.0, 3),
        ]
        y = [
            round(rec.shear_test_final1 or 0.0, 3),
            round(rec.shear_test_final2 or 0.0, 3),
            round(rec.shear_test_final3 or 0.0, 3),
        ]

        # Keep only valid pairs
        pairs = [(xi, yi) for xi, yi in zip(x, y) if xi and yi]
        if len(pairs) < 2:
            continue

        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]

        n = len(xs)
        sum_x = sum(xs)
        sum_y = sum(ys)
        sum_xy = sum(x * y for x, y in zip(xs, ys))
        sum_x2 = sum(x * x for x in xs)

        denominator = (n * sum_x2 - sum_x ** 2)
        if denominator == 0:
            continue

        # Excel SLOPE
        slope = (n * sum_xy - sum_x * sum_y) / denominator

        # Phi = DEGREES(ATAN(slope))
        rec.phi = round(math.degrees(math.atan(slope)), 3)

        # Cohesion = INTERCEPT
        rec.cohesion = round((sum_y - slope * sum_x) / n, 3)


     

    shear_graph_image_4 = fields.Binary("Shear Stress Graph")



    def action_generate_shear_graph_4(self):
     for rec in self:

        rec.shear_graph_image_4 = False

        # ===== DATA =====
        x_vals = [
            rec.normal_stress,
            rec.normal_stress_2,
            rec.normal_stress_3,
        ]
        y_vals = [
            rec.shear_test_final1,
            rec.shear_test_final2,
            rec.shear_test_final3,
        ]

        pairs = [(x, y) for x, y in zip(x_vals, y_vals) if x and y]
        if len(pairs) < 2:
            continue

        pairs.sort(key=lambda p: p[0])
        x, y = zip(*pairs)

        # ===== LINEAR REGRESSION =====
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        intercept = (sum_y - slope * sum_x) / n

        y_fit = [slope * xi + intercept for xi in x]

        # ===== R² =====
        y_mean = sum_y / n
        ss_tot = sum((yi - y_mean) ** 2 for yi in y)
        ss_res = sum((yi - yfi) ** 2 for yi, yfi in zip(y, y_fit))
        r_squared = 1 - (ss_res / ss_tot)

        # ===== TRENDLINE RANGE =====
        x_min = min(x)
        x_max = max(x)
        x_line = [x_min, x_max]
        y_line = [slope * xi + intercept for xi in x_line]

        # ===== PLOT =====
        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

        # Excel blue data line + markers
        ax.plot(
            x, y,
            color='#4472C4',
            marker='o',
            markersize=6,
            linewidth=2.5
        )

        # Black trendline
        ax.plot(
            x_line, y_line,
            color='black',
            linewidth=1.6
        )

        # Labels
        ax.set_xlabel("Normal stress, kg/sq.cm", fontsize=11)
        ax.set_ylabel("Shear Stress, kg/sq.cm", fontsize=11)
        ax.set_title("Shear Stress Vs Normal Stress", fontsize=13)
        # ===== EXCEL-LIKE X AXIS =====
        ax.set_xlim(0, 1.6)                      # Axis starts at 0
        ax.set_xticks(np.arange(0, 1.61, 0.2))

        # Axis limits (Excel-like)
        # ax.set_xlim(x_min, x_max)
        ax.set_ylim(0, max(y) * 1.15)

        # Vertical gridlines only
        ax.xaxis.grid(True, color='#BFBFBF', linewidth=0.8)
        ax.yaxis.grid(False)

        # Excel-like border
        for spine in ax.spines.values():
            spine.set_color('#7F7F7F')
            spine.set_linewidth(1)

        ax.tick_params(labelsize=10)

        # Equation text (positioned like Excel)
        # eq_text = f"y = {slope:.4f}x + {intercept:.4f}\nR² = {r_squared:.4f}"
        # ax.text(
        #     x_min + (x_max - x_min) * 0.35,
        #     max(y) * 0.78,
        #     eq_text,
        #     fontsize=10
        # )

        # ===== SAVE IMAGE =====
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight', facecolor='white')
        buffer.seek(0)

        rec.shear_graph_image_4 = base64.b64encode(buffer.read())

        buffer.close()
        plt.close(fig)

    # def action_generate_shear_graph_4(self):
    #  for rec in self:

    #     rec.shear_graph_image_4 = False

    #     # ===== DATA =====
    #     x_vals = [
    #         rec.normal_stress,
    #         rec.normal_stress_2,
    #         rec.normal_stress_3,
    #     ]
    #     y_vals = [
    #         rec.shear_test_final1,
    #         rec.shear_test_final2,
    #         rec.shear_test_final3,
    #     ]

    #     pairs = [(x, y) for x, y in zip(x_vals, y_vals) if x and y]
    #     if len(pairs) < 2:
    #         continue

    #     pairs.sort(key=lambda p: p[0])
    #     x, y = zip(*pairs)

    #     # ===== LINEAR REGRESSION =====
    #     n = len(x)
    #     sum_x = sum(x)
    #     sum_y = sum(y)
    #     sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    #     sum_x2 = sum(xi * xi for xi in x)

    #     slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    #     intercept = (sum_y - slope * sum_x) / n

    #     y_fit = [slope * xi + intercept for xi in x]

    #     # ===== R² =====
    #     y_mean = sum_y / n
    #     ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    #     ss_res = sum((yi - yfi) ** 2 for yi, yfi in zip(y, y_fit))
    #     r_squared = 1 - (ss_res / ss_tot)

    #     # ===== TRENDLINE RANGE (START FROM Y-AXIS) =====
    #     x_max = max(x)
    #     x_line = [0, x_max]
    #     y_line = [intercept, slope * x_max + intercept]

    #     # ===== PLOT =====
    #     fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

    #     # Excel-style blue data line
    #     ax.plot(
    #         x, y,
    #         color='#4472C4',
    #         marker='o',
    #         markersize=6,
    #         linewidth=2.5
    #     )

    #     # Black trendline (touches Y-axis)
    #     ax.plot(
    #         x_line, y_line,
    #         color='black',
    #         linewidth=1.6
    #     )

    #     # Labels
    #     ax.set_xlabel("Normal stress, kg/sq.cm", fontsize=11)
    #     ax.set_ylabel("Shear Stress, kg/sq.cm", fontsize=11)
    #     ax.set_title("Shear Stress Vs Normal Stress", fontsize=13)

    #     # ===== AXES (EXCEL-LIKE) =====
    #     ax.set_xlim(0, 1.6)
    #     ax.set_xticks(np.arange(0, 1.61, 0.2))
    #     ax.set_ylim(0, max(y) * 1.15)

    #     # Gridlines
    #     ax.xaxis.grid(True, color='#BFBFBF', linewidth=0.8)
    #     ax.yaxis.grid(False)

    #     # Border
    #     for spine in ax.spines.values():
    #         spine.set_color('#7F7F7F')
    #         spine.set_linewidth(1)

    #     ax.tick_params(labelsize=10)

    #     # Equation text
    #     # eq_text = f"y = {slope:.4f}x + {intercept:.4f}\nR² = {r_squared:.4f}"
    #     # ax.text(
    #     #     0.35 * x_max,
    #     #     max(y) * 0.78,
    #     #     eq_text,
    #     #     fontsize=10
    #     # )

    #     # ===== SAVE IMAGE =====
    #     buffer = BytesIO()
    #     fig.savefig(buffer, format='png', bbox_inches='tight', facecolor='white')
    #     buffer.seek(0)

    #     rec.shear_graph_image_4 = base64.b64encode(buffer.read())

    #     buffer.close()
    #     plt.close(fig)




    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(DrirectShearLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class SwellingPressureLine(models.Model):
    _name = "swelling.pressure.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id",ondelete='cascade')

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)
    is_checked = fields.Boolean(
        string="Calculated",
        default=False
    )
    start_date = fields.Date(string="Start Date")  # manually fill
    end_date = fields.Date(string="End Date")      # auto fill on submit
    sample_type_swelling=  fields.Char(string="Sample Type and Condtion:",default="DS" )
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise ValidationError(
                        "Start Date cannot be greater than End Date."
                    )

    

    def action_submit(self):
        self.ensure_one()
        
        # Boolean True save
        self.write({
            'is_checked': True,
            # 'end_date': fields.Date.context_today(self),  # current date auto fill
        })
        
        # Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}

    lab_id=  fields.Char(string="Lab ID" )

    depth = fields.Char(
        string="Depth (m)",
        compute="_compute_swelling",
        store=True
    )

   
    @api.depends('lab_id')
    def _compute_swelling(self):
        ReviewLine = self.env['sample.request.review.lines']

        for line in self:
            line.depth = False

            if not line.lab_id:
                continue

            review_line = ReviewLine.search(
                [('lab_id', '=', line.lab_id)],
                order='id desc',
                limit=1
            )

            if review_line:
                line.depth = review_line.depth         # Depth (m)


    # room_temp_proctor = fields.Float(string="Room Temp.°C" )
    # humidity_proctor = fields.Float(string="Humidity %" )

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

    wt_dry_soil_swell = fields.Float(string= "Weight Of Dry Specimen + Ring, w4", compute="_compute_wt_dry_soil_swell", digits=(10,3))

    height_solid = fields.Float(string= "Height of Solids, Hs", compute="_compute_height_solid", digits=(10,4))

    @api.depends('wt_dry_specimen_af','wt_of_ring')
    def _compute_wt_dry_soil_swell(self):
        for line in self:
                line.wt_dry_soil_swell = line.wt_dry_specimen_af - line.wt_of_ring


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

    # @api.depends('wt_of_ring', 'wt_wet_specimen_af',
    #          'swelling_area', 'swelling_output_ids.specimen_height')
    # def _compute_bulk_density_soil_1(self):
    #  for line in self:
    #     num = (line.wt_wet_specimen_af or 0.0) - (line.wt_of_ring or 0.0)

    #     # get list of heights from child lines
    #     heights = line.swelling_output_ids.mapped('specimen_height') or []
    #     # take third-last value if it exists
    #     h = heights[-3] if len(heights) >= 3 else 0.0

    #     deno = (line.swelling_area or 0.0) * h

    #     if deno:
    #         line.bulk_density_soil_1 = num / deno
    #     else:
    #         line.bulk_density_soil_1 = 0.0

    @api.depends(
    'wt_of_ring',
    'wt_wet_specimen_af',
    'swelling_area',
    'swelling_output_ids.specimen_height',
    'swelling_output_ids.cylces'
)
    def _compute_bulk_density_soil_1(self):

     for line in self:

        # -------------------------------------------------
        # Wet soil mass
        # γb = (Wet Specimen + Ring) - (Ring Weight)
        # -------------------------------------------------

        num = (
            (line.wt_wet_specimen_af or 0.0)
            - (line.wt_of_ring or 0.0)
        )

       

        unloading_lines = line.swelling_output_ids.filtered(
            lambda r: r.cylces and '1st Cycle Unloading' in r.cylces
        )

        heights = unloading_lines.mapped(
            'specimen_height'
        ) or []

        # Excel E28 corresponds to third-last unloading row
        h = (
            heights[-3]
            if len(heights) >= 3
            else 0.0
        )

        # -------------------------------------------------
        # Volume
        # V = A × H
        # -------------------------------------------------

        volume = (
            (line.swelling_area or 0.0) * h
        )

        # -------------------------------------------------
        # Bulk Density
        # γb = W / V
        # -------------------------------------------------

        if volume:

            line.bulk_density_soil_1 = (
                num / volume
            )

        else:

            line.bulk_density_soil_1 = 0.0


    @api.depends(
    'wt_wet_specimen_af',
    'wt_of_ring',
    'swelling_area',
    'wt_dry_specimen_af',
    'swelling_output_ids.specimen_height'
)
    def _compute_dry_density_soil_1(self):

     for line in self:

        line.dry_density_soil_1 = 0.0

        heights = line.swelling_output_ids.mapped(
            'specimen_height'
        ) or []

        h = heights[-2] if len(heights) >= 2 else 0.0

        volume = (
            (line.swelling_area or 0.0) * h
        )

        if not volume:
            continue

        wet_mass = (
            (line.wt_wet_specimen_af or 0.0)
            - (line.wt_of_ring or 0.0)
        )

        bulk_density = (
            wet_mass / volume
        )

        dry_mass = (
            (line.wt_dry_specimen_af or 0.0)
            - (line.wt_of_ring or 0.0)
        )

        if not dry_mass:
            continue

        water_con = (
            (
                (line.wt_wet_specimen_af or 0.0)
                - (line.wt_dry_specimen_af or 0.0)
            ) / dry_mass
        ) * 100

        line.dry_density_soil_1 = (
            bulk_density / (1 + (water_con / 100))
        )


# ---------------------------------------------------------
# Void Ratio
# ---------------------------------------------------------

    @api.depends(
    'swelling_output_ids.e_void',
    'swelling_output_ids.cylces'
)
    def _compute_swell_void_ratio_1(self):

     for line in self:

        # only unloading rows
        unloading_lines = line.swelling_output_ids.filtered(
            lambda r: r.cylces and '1st Cycle Unloading' in r.cylces
        )

        # get void ratios
        voids = unloading_lines.mapped(
            'e_void'
        ) or []

        # last unloading void ratio
        v = voids[-1] if voids else 0.0

        line.swell_void_ratio_1 = v


# ---------------------------------------------------------
# Degree of Saturation
# Sr = (w × Gs) / e
# ---------------------------------------------------------

    @api.depends(
    'swelling_output_ids.e_void',
    'swelling_output_ids.cylces',
    'swelling_specific_gravity',
    'wt_wet_specimen_af',
    'wt_dry_specimen_af',
    'wt_of_ring'
)
    def _compute_degree_sat_1(self):
 
     for line in self:

        # ---------------------------------------------
        # ONLY unloading rows
        # ---------------------------------------------

        unloading_lines = line.swelling_output_ids.filtered(
            lambda r: r.cylces and 'Unloading' in r.cylces
        )

        # void ratios from unloading rows
        voids = unloading_lines.mapped(
            'e_void'
        ) or []

        # LAST unloading void ratio
        v = voids[-1] if voids else 0.0

        # ---------------------------------------------
        # Water Content (%)
        # ---------------------------------------------

        denom = (
            (line.wt_dry_specimen_af or 0.0)
            - (line.wt_of_ring or 0.0)
        )

        water_con = 0.0

        if denom:

            water_con = (
                (
                    (line.wt_wet_specimen_af or 0.0)
                    - (line.wt_dry_specimen_af or 0.0)
                ) / denom
            ) * 100

        # ---------------------------------------------
        # Degree of Saturation
        # Sr = (G × w) / e
        # Excel-style calculation
        # ---------------------------------------------

        if v:

            line.degree_sat_1 = (
                (
                    water_con
                    * (line.swelling_specific_gravity or 0.0)
                ) / v
            )

        else:

            line.degree_sat_1 = 0.0

    

    initial_read = fields.Float(string= "Initial Reading",  digits=(8,2)) 
    set_load_read = fields.Float(string= "Setting load Reading",  digits=(8,2))

    swelling_ids = fields.One2many("swelling.pressure.loading.line", "parent_id_swelling", string="1st Cycle Loading	",default=lambda self: self.default_gauge_reading())

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
    
    swelling_unloading_ids = fields.One2many("swelling.pressure.unloading.line", "parent_id_unloading", string="1st Cycle Loading	",default=lambda self: self.default_gauge_reading_2())

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
    

    swelling_output_ids = fields.One2many("swelling.pressure.both.cycle.line", "parent_id_output", string="1st Cycle Loading	",default=lambda self: self.default_cycle_reading())

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
    

    swelling_table_ids = fields.One2many("swelling.pressure.graph.line", "parent_id_table", string="Graph Table",default=lambda self: self.default_table_reading())

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


  
#     def generate_line_chart_swell(self):
#      self.ensure_one()

#      import numpy as np
#      import base64
#      from io import BytesIO
#      import matplotlib
#      matplotlib.use('Agg')
#      import matplotlib.pyplot as plt
#      from scipy.interpolate import PchipInterpolator
#      from matplotlib.ticker import LogLocator, LogFormatter

    
#      lines = self.swelling_table_ids.sorted('applied_pressure')

#      x = np.array([l.applied_pressure for l in lines if l.applied_pressure > 0], float)
#      y = np.array([l.delta_h for l in lines if l.delta_h is not None], float)

#      if len(x) < 3:
#         return False

   
#      sp = 0
#      for i in range(len(x) - 1):
#         if y[i] >= 0 and y[i + 1] <= 0:
#             sp = x[i] + (x[i + 1] - x[i]) * (0 - y[i]) / (y[i + 1] - y[i])
#             break

#      lx = np.log10(x)
#      cs = PchipInterpolator(lx, y)

#      lx_s = np.linspace(lx.min(), lx.max(), 500)
#      xs = 10 ** lx_s
#      ys = cs(lx_s)

   
#      fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

#     # Curve
#      ax.plot(xs, ys, color='#4472C4', linewidth=2.5)

#     # Markers
#      ax.scatter(x, y, color='#4472C4', s=30, zorder=5)

#     # Point labels
#      for xi, yi in zip(x, y):
#         ax.text(xi, yi + 0.05, f"{yi:.3f}", ha='center', fontsize=8)

#     # Zero horizontal line
#      ax.axhline(0, color='#4472C4', linewidth=1)

#     # X axis crosses at Y=0
#      ax.spines['bottom'].set_position(('data', 0))

#     # Swelling pressure vertical line
#      ax.axvline(sp, color='red', linewidth=1.5)

#     # -----------------------------
#     # LOG X AXIS 0.10 → 100
#     # -----------------------------
#      ax.set_xscale('log')
#      ax.set_xlim(0.1, 100)

#     # Major ticks: 0.1 1 10 100
#      ax.xaxis.set_major_locator(LogLocator(base=10))
#      ax.xaxis.set_major_formatter(LogFormatter())

#     # Minor ticks (Excel density)
#      ax.xaxis.set_minor_locator(
#         LogLocator(base=10, subs=np.arange(1, 10) * 0.1)
#     )

    
#      y_min = min(y.min(), ys.min())
#      y_max = max(y.max(), ys.max())

# # Add small padding
#      padding = (y_max - y_min) * 0.10
#      y_min -= padding
#      y_max += padding

# # Round limits nicely (like Excel)
#      y_min = np.floor(y_min * 2) / 2
#      y_max = np.ceil(y_max * 2) / 2

#      ax.set_ylim(y_min, y_max)

# # Auto step (0.5 or 0.25 depending on range)
#      y_range = y_max - y_min

#      if y_range <= 2:
#         step = 0.25
#      elif y_range <= 5:
#         step = 0.5
#      else:
#         step = 1.0

#      ax.set_yticks(np.arange(y_min, y_max + step, step))
 
#     # -----------------------------
#     # Grid (Excel style)
#     # -----------------------------
#      ax.grid(which='major', color='#A6A6A6', linewidth=0.8)
#      ax.grid(which='minor', color='#D9D9D9', linewidth=0.5)

#     # Background
#      ax.set_facecolor('#F2F2F2')
#      fig.patch.set_facecolor('white')

#     # Labels
#      ax.set_xlabel('Pressure kg/cm2', fontsize=10)
#      ax.set_ylabel('Deformation, mm', fontsize=10)

#     # Borders
#      ax.spines['top'].set_visible(True)
#      ax.spines['right'].set_visible(True)

#     # -----------------------------
#     # Export
#     # -----------------------------
#      buf = BytesIO()
#      fig.tight_layout()
#      fig.savefig(buf, format='png')
#      plt.close(fig)
#      buf.seek(0)

#      return base64.b64encode(buf.read())


    def generate_line_chart_swell(self):
     self.ensure_one()

     import numpy as np
     import base64
     from io import BytesIO
     import matplotlib
     matplotlib.use('Agg')
     import matplotlib.pyplot as plt
     from scipy.interpolate import PchipInterpolator
     from matplotlib.ticker import LogLocator, FuncFormatter

    # -----------------------------
    # Data
    # -----------------------------
     lines = self.swelling_table_ids.sorted('applied_pressure')

     x = np.array([l.applied_pressure for l in lines if l.applied_pressure > 0], float)
     y = np.array([l.delta_h for l in lines if l.delta_h is not None], float)

     if len(x) < 3:
        return False

    # -----------------------------
    # Swelling Pressure
    # -----------------------------
     sp = 0
     for i in range(len(x) - 1):
        if y[i] >= 0 and y[i + 1] <= 0:
            sp = x[i] + (x[i + 1] - x[i]) * (0 - y[i]) / (y[i + 1] - y[i])
            break

    # -----------------------------
    # Smooth Curve (LOG DOMAIN)
    # -----------------------------
     lx = np.log10(x)
     cs = PchipInterpolator(lx, y)

     lx_s = np.linspace(lx.min(), lx.max(), 120)
     xs = 10 ** lx_s
     ys = cs(lx_s)

    # -----------------------------
    # Plot
    # -----------------------------
     fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

     ax.plot(xs, ys, color='#4472C4', linewidth=2)
     ax.scatter(x, y, color='#4472C4', s=20, zorder=5)

    # -----------------------------
    # LOG X AXIS (Dynamic)
    # -----------------------------
     x_min = 10 ** np.floor(np.log10(min(x)))
     x_max = 10 ** np.ceil(np.log10(max(x)))

     ax.set_xscale('log')
     ax.set_xlim(x_min, x_max)

     def log_format(val, pos):
        return f"{val:.2f}"

     ax.xaxis.set_major_locator(LogLocator(base=10))
     ax.xaxis.set_major_formatter(FuncFormatter(log_format))
     ax.xaxis.set_minor_locator(
        LogLocator(base=10, subs=[0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9])
    )

    # -----------------------------
    # Y AXIS (Dynamic)
    # -----------------------------
     y_min = min(y.min(), ys.min())
     y_max = max(y.max(), ys.max())

     padding = (y_max - y_min) * 0.10
     y_min -= padding
     y_max += padding

     y_min = np.floor(y_min * 2) / 2
     y_max = np.ceil(y_max * 2) / 2

     ax.set_ylim(y_min, y_max)

     y_range = y_max - y_min
 
     if y_range <= 2:
        step = 0.25
     elif y_range <= 5:
        step = 0.5
     else:
        step = 1.0

     ax.set_yticks(np.arange(y_min, y_max + step, step))

    # -----------------------------
    # ⭐ IMPORTANT: X-axis at Y = 0
    # -----------------------------
     ax.spines['bottom'].set_position(('data', 0))
     ax.spines['top'].set_visible(False)

    # FIX label positions
     ax.xaxis.set_ticks_position('bottom')
     ax.yaxis.set_ticks_position('left')

    # -----------------------------
    # Reference lines
    # -----------------------------
     ax.axvline(sp, color='red', linewidth=1.5)

    # -----------------------------
    # Grid
    # -----------------------------
     ax.grid(which='major', color='#A6A6A6', linewidth=0.8)
     ax.grid(which='minor', color='#D9D9D9', linewidth=0.5)

    # -----------------------------
    # Background
    # -----------------------------
     ax.set_facecolor('white')
     fig.patch.set_facecolor('white')

    # -----------------------------
    # Labels
    # -----------------------------
     ax.set_xlabel('Applied Pressure (kg/cm2)', fontsize=10)
     ax.set_ylabel('Deformation (mm)', fontsize=10)

    # Keep X label at bottom (IMPORTANT FIX)
     ax.xaxis.set_label_coords(0.5, -0.1)

    # Borders
     ax.spines['right'].set_visible(True)
     ax.spines['left'].set_visible(True)

    # -----------------------------
    # Export
    # -----------------------------
     buf = BytesIO()
     fig.tight_layout()
     fig.savefig(buf, format='png')
     plt.close(fig)
     buf.seek(0)

     return base64.b64encode(buf.read())


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SwellingPressureLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class ConsolidationLine(models.Model):
    _name = "consolidation.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id",ondelete='cascade')

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    is_checked = fields.Boolean(
        string="Calculated",
        default=False
    )

    sample_type_consolidation = fields.Char(string="Sample Type and Condition:",default="UDS-01")      # auto fill on submit
    start_date = fields.Date(string="Start Date")  # manually fill
    end_date = fields.Date(string="End Date")      # auto fill on submit

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise ValidationError(
                        "Start Date cannot be greater than End Date."
                    )

    

    def action_submit(self):
        self.ensure_one()
        
        # Boolean True save
        self.write({
            'is_checked': True,
            # 'end_date': fields.Date.context_today(self),  # current date auto fill
        })
        
        # Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}

    lab_id=  fields.Char(string="Lab ID" )
    bh_id = fields.Char(
        string="BH ID",
        compute="_compute_consolidation",
        store=True
    )

    depth = fields.Char(
        string="Depth (m)",
        compute="_compute_consolidation",
        store=True
    )

    
    @api.depends('lab_id')
    def _compute_consolidation(self):
        ReviewLine = self.env['sample.request.review.lines']

        for line in self:
            line.bh_id = False
            line.depth = False

            if not line.lab_id:
                continue

            review_line = ReviewLine.search(
                [('lab_id', '=', line.lab_id)],
                order='id desc',
                limit=1
            )

            if review_line:
                line.bh_id = review_line.source        # BH ID / Location
                line.depth = review_line.depth         # Depth (m)

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

    

    consolidation_ids = fields.One2many("consolidation.loading.line", "parent_id_consolidation", string="1st Cycle Loading",default=lambda self: self.default_con_gauge_reading())





    # --- 1. प्रत्येक ग्राफसाठी वेगळे Image Field ---
    consolidation_graph_05_1 = fields.Binary(string="Graph 0.05-0.1")
    consolidation_graph_1_2 = fields.Binary(string="Graph 0.1-0.2")
    consolidation_graph_2_5 = fields.Binary(string="Graph 0.2-0.5")
    consolidation_graph_5_10 = fields.Binary(string="Graph 0.5-1.0")
    # consolidation_graph_10_20 = fields.Binary(string="Graph 1.0-2.0")
    # consolidation_graph_20_40 = fields.Binary(string="Graph 2.0-4.0")
    # consolidation_graph_40_80 = fields.Binary(string="Graph 4.0-8.0")



    def action_generate_graph(self):
        for record in self:
            sorted_lines = sorted(record.consolidation_ids, key=lambda x: x.sqrt_time if x.sqrt_time else 0)

            graph_configs = [
                ('load_0_05_0_1', '1st Cycle Loading - (0.05 - 0.1)', 'consolidation_graph_05_1', (10, 5)),
                ('load_0_1_0_2',  '1st Cycle Loading - (0.1 - 0.2)',  'consolidation_graph_1_2', (10, 5)),
                ('load_0_2_0_5',  '1st Cycle Loading - (0.2 - 0.5)',  'consolidation_graph_2_5', (10, 5)),
                ('load_0_5_1_0',  '1st Cycle Loading - (0.5 - 1.0)',  'consolidation_graph_5_10', (10, 5)),
                
               
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
    




    graph_1_0_2_0 = fields.Binary(string="Graph (1.0–2.0 kg/cm²)")
    graph_2_0_4_0 = fields.Binary(string="Graph (2.0–4.0 kg/cm²)")
    graph_4_0_8_0 = fields.Binary(string="Graph (4.0–8.0 kg/cm²)")

    

    # ---------------------------------------------------------
    # COMMON GRAPH PLOTTER (FORMATTED & SMOOTH)
    # ---------------------------------------------------------
    def _plotted_graph(self, lines, y_field_name, title, fig_size=(10, 5)):

        lines = lines.sorted('sqrt_time')

        x_values = []
        y_values = []

        for line in lines:
            y_val = getattr(line, y_field_name, None)
            if line.sqrt_time is not None and y_val is not None:
                x_values.append(line.sqrt_time)
                y_values.append(y_val)

        if not x_values:
            return False

        can_smooth = HAS_SCIPY and len(x_values) >= 4

        fig, ax = plt.subplots(figsize=fig_size)

        if can_smooth:
            try:
                x_np = np.array(x_values)
                y_np = np.array(y_values)

                x_new = np.linspace(x_np.min(), x_np.max(), 300)
                spline = make_interp_spline(x_np, y_np, k=3)
                y_smooth = spline(x_new)

                ax.plot(x_new, y_smooth, color='black', linewidth=1.5)
                ax.plot(x_values, y_values, 'o', color='black', markersize=6)
            except Exception:
                ax.plot(x_values, y_values, 'o-', color='black', linewidth=1.5)
        else:
            ax.plot(x_values, y_values, 'o-', color='black', linewidth=1.5)

        # -------- LAB STANDARD FORMATTING --------
        ax.set_xlim(0, 20)
        ax.set_xticks(range(0, 21, 2))
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))

        ax.minorticks_on()
        ax.grid(which='major', linestyle='-', linewidth=0.5, color='gray')
        ax.grid(which='minor', linestyle=':', linewidth=0.5, color='lightgray')

        ax.set_title(title, fontsize=16)
        ax.set_xlabel('SQRT (Time in minutes)', fontsize=12)
        ax.set_ylabel('Dial Gauge Reading (mm)', fontsize=12)

        # Save Image
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)

        return base64.b64encode(buf.getvalue())

    # ---------------------------------------------------------
    # BUTTON ACTIONS (USING SAME PLOTTER)
    # ---------------------------------------------------------
    def action_generate_graph_1_0_2_0(self):
        for rec in self:
            rec.graph_1_0_2_0 = rec._plotted_graph(
                rec.consolidation_ids,
                'load_1_0_2_0',
                '1st Cycle Loading – (1.0–2.0 kg/cm²)'
            )

    def action_generate_graph_2_0_4_0(self):
        for rec in self:
            rec.graph_2_0_4_0 = rec._plotted_graph(
                rec.consolidation_ids,
                'load_2_0_4_0',
                '1st Cycle Loading – (2.0–4.0 kg/cm²)'
            )

    def action_generate_graph_4_0_8_0(self):
        for rec in self:
            rec.graph_4_0_8_0 = rec._plotted_graph(
                rec.consolidation_ids,
                'load_4_0_8_0',
                '1st Cycle Loading – (4.0–8.0 kg/cm²)'
            )


    def action_generate_all_graphs(self):
     for rec in self:
        rec.action_generate_graph()
        rec.action_generate_graph_1_0_2_0()
        rec.action_generate_graph_2_0_4_0()
        rec.action_generate_graph_4_0_8_0()


    

   


    



    
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
    
    consolidation_unloading_ids = fields.One2many("consolidation.unloading.line", "parent_id_con_un", string="1st Cycle Loading",default=lambda self: self.default_con_gauge_reading_2())

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
    


    consolidation_output_ids = fields.One2many("consolidation.both.cycle.line", "parent_id_con_out", string="1st Cycle Loading	",default=lambda self: self.default_con_cycle_reading())
    consolidation_graph = fields.Binary(
        string="Consolidation Graph",
        attachment=True
    )


   

    

    import numpy as np
    import matplotlib.pyplot as plt
    from io import BytesIO
    import base64

    import logging

    _logger = logging.getLogger(__name__)

   
    def action_generate_consolidation_graph(self):
     import numpy as np
     import matplotlib.pyplot as plt
     from io import BytesIO
     import base64
     from scipy.signal import savgol_filter
     import logging

     _logger = logging.getLogger(__name__)
     self.ensure_one()
 
   
     loading, unloading = [], []
     last_p = 0
     unloading_started = False

     for l in self.consolidation_output_ids.sorted('id'):
        if not unloading_started and l.applied_pressure >= last_p:
            loading.append((l.applied_pressure, l.e_void))
            last_p = l.applied_pressure
        else:
            unloading_started = True
            unloading.append((l.applied_pressure, l.e_void))

     if len(loading) < 4:
        return

     p = np.array([x[0] for x in loading])
     e = np.array([x[1] for x in loading])
     log_p = np.log10(p)

    
     e_smooth = savgol_filter(e, 3, 1)

   
     dy = np.gradient(e_smooth, log_p)
     ddy = np.gradient(dy, log_p)

    # Restrict curvature search to knee zone (0.5–2.0 kg/cm²)
     mask = (p >= 0.5) & (p <= 2.0)

     if not np.any(mask):
        return

     idx = np.argmax(np.abs(ddy[mask]))
     idx = np.where(mask)[0][idx]

     p_A = p[idx]
     e_A = e[idx]
     slope_tangent = dy[idx]

    # --------------------------------------------------
    # 4️⃣ VIRGIN COMPRESSION LINE (LAST 3–4 POINTS)
    # --------------------------------------------------
     n_vcl = min(4, len(p))
     coef_vcl = np.polyfit(np.log10(p[-n_vcl:]), e[-n_vcl:], 1)
     vcl_slope = coef_vcl[0]
     vcl_intercept = coef_vcl[1]

    # --------------------------------------------------
    # 5️⃣ BISector
    # --------------------------------------------------
     angle_tan = np.arctan(slope_tangent)
     bisector_slope = np.tan(angle_tan / 2)

   
     log_pc = (
        e_A
        - bisector_slope * np.log10(p_A)
        - vcl_intercept
    ) / (vcl_slope - bisector_slope)

     pc_val = 10 ** log_pc

    # --------------------------------------------------
    # 7️⃣ PLOT
    # --------------------------------------------------
     plt.figure(figsize=(9, 5))

    # Loading
     plt.plot(p, e, '-ok', linewidth=1.6, markersize=5)

    # Unloading
     if unloading:
        pu = np.array([x[0] for x in unloading])
        eu = np.array([x[1] for x in unloading])
        plt.plot(pu, eu, '-ok', linewidth=1.6, markersize=5)
        plt.plot([p[-1], pu[0]], [e[-1], eu[0]], '-k', linewidth=1.6)

    # Construction lines
     x_ext = np.logspace(np.log10(p_A), np.log10(10), 200)

    # Horizontal
     plt.hlines(e_A, p_A, 10, colors='r', linewidth=1.4)

    # Tangent
     y_tan = e_A + slope_tangent * (np.log10(x_ext) - np.log10(p_A))
     plt.plot(x_ext, y_tan, 'r-', linewidth=1.4)

    # Bisector
     y_bis = e_A + bisector_slope * (np.log10(x_ext) - np.log10(p_A))
     plt.plot(x_ext, y_bis, 'r-', linewidth=1.4)

    # VCL
     x_vcl = np.logspace(np.log10(p_A * 0.4), np.log10(10), 200)
     y_vcl = vcl_slope * np.log10(x_vcl) + vcl_intercept
     plt.plot(x_vcl, y_vcl, 'r-', linewidth=1.4)

    # Pc vertical
     plt.vlines(pc_val, ymin=0.65, ymax=e_A, colors='r', linewidth=1.6)

    # --------------------------------------------------
    # 8️⃣ STYLING (MATCH EXCEL)
    # --------------------------------------------------
     plt.xscale('log')
     plt.xlim(0.01, 10)
     plt.ylim(0.65, 0.95)

     plt.xlabel("Pressure (kg/cm²)", fontweight='bold')
     plt.ylabel("Void Ratio", fontweight='bold')

     plt.grid(True, which='both', color='#808080', linewidth=0.35)
     plt.gca().xaxis.set_major_formatter(plt.FormatStrFormatter('%.2f'))
     plt.gca().yaxis.set_major_formatter(plt.FormatStrFormatter('%.3f'))

    # --------------------------------------------------
    # 9️⃣ SAVE IMAGE
    # --------------------------------------------------
     buf = BytesIO()
     plt.tight_layout()
     plt.savefig(buf, format='png', dpi=100)
     self.consolidation_graph = base64.b64encode(buf.getvalue())
     buf.close()
     plt.close()

    # Save Pc if field exists
     if hasattr(self, 'pc_value'):
        self.pc_value = pc_val





    
        



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
    cr = fields.Float(string="Recompression Index, Cr", digits=(8, 3),compute="_compute_cr")


    @api.depends(
        'con_swell_void_ratio',
        'pressure_y',
        'preconsolidation_pressure_x',
        'consolidation_output_ids.applied_pressure'
    )
    def _compute_cr(self):
        for record in self:

            record.cr = 0.0

            # Sort by pressure like Excel rows
            lines = record.consolidation_output_ids.sorted(
                key=lambda l: l.applied_pressure
            )

            # Excel is using first pressure value
            # Example: 0.10
            first_pressure = (
                lines[0].applied_pressure
                if lines else 0.0
            )

            if (
                first_pressure > 0
                and record.preconsolidation_pressure_x > 0
                and record.preconsolidation_pressure_x != first_pressure
            ):

                numerator = (
                    record.con_swell_void_ratio
                    - record.pressure_y
                )

                denominator = math.log10(
                    record.preconsolidation_pressure_x
                    / first_pressure
                )

                if denominator != 0:

                    record.cr = (
                        numerator / denominator
                    )


    
    @api.depends(
    'consolidation_output_ids.e_void',
    'consolidation_output_ids.applied_pressure',
)
    def _compute_ce_cr(self):
     for rec in self:

        rec.ce = 0.0
        rec.cr = 0.0

        lines = rec.consolidation_output_ids.filtered(
            lambda l: l.applied_pressure is not None and l.e_void is not None
        )

        if not lines:
            continue

        # =========================
        # SORT SAFELY (NO NewId ISSUE)
        # =========================
        lines = lines.sorted(key=lambda l: l._origin.id or 0)

        # =========================
        # SPLIT BASED ON PRESSURE TREND
        # =========================
        loading = []
        unloading = []

        prev = None
        is_unloading = False

        for l in lines:
            p = l.applied_pressure

            if prev is not None and p < prev:
                is_unloading = True

            if is_unloading:
                unloading.append(l)
            else:
                loading.append(l)

            prev = p

        # =========================
        # HELPER: FIND EXACT PRESSURE
        # =========================
        def find(records, value):
            for r in records:
                if round(r.applied_pressure or 0.0, 2) == value:
                    return r
            return False

        # =========================
        # Ce → 0.50 → 4.00
        # =========================
        l1 = find(loading, 0.50)
        l2 = find(loading, 4.00)

        if l1 and l2:
            rec.ce = (l1.e_void - l2.e_void) / (
                log10(l2.applied_pressure) - log10(l1.applied_pressure)
            )

        # =========================
        # Cr → 0.50 → 0.10
        # =========================
        # u1 = find(unloading, 0.50)
        # u2 = find(unloading, 0.10)

        # if u1 and u2:
        #     rec.cr = (u1.e_void - u2.e_void) / (
        #         log10(u2.applied_pressure) - log10(u1.applied_pressure)
        #     )
            



    slop = fields.Float(string="Slop m", digits=(8, 3),compute="_compute_slop")

    @api.depends('slop1', 'slop2', 'slop3', 'slop4')
    def _compute_slop(self):
        for rec in self:
            try:
                if rec.slop1 > 0 and rec.slop2 > 0:
                    rec.slop = (rec.slop3 - rec.slop4) / math.log10(rec.slop1 / rec.slop2)
                else:
                    rec.slop = 0.0
            except Exception:
                rec.slop = 0.0

    slop1 = fields.Float(string="Slop 1",compute="_compute_slop1" ,digits=(8, 3))
    slop2 = fields.Float(string="Slop 2", digits=(8, 3),compute="_compute_slop2")

    slop3 = fields.Float(string="Slop 3", digits=(8, 3),compute="_compute_slop3")
    slop4 = fields.Float(string="Slop 4", digits=(8, 3),compute="_compute_slop4")

    slop5 = fields.Float(string="Slop 5", digits=(8, 3),compute="_compute_slop5")

    @api.depends('slop4', 'slop', 'slop2')
    def _compute_slop5(self):
        for rec in self:
            try:
                if rec.slop2 > 0:
                    rec.slop5 = rec.slop4 - (rec.slop * math.log10(rec.slop2))
                else:
                    rec.slop5 = 0.0
            except Exception:
                rec.slop5 = 0.0

    @api.depends(
    'slop1',
    'consolidation_output_ids.applied_pressure',
    'consolidation_output_ids.e_void'
    )
    def _compute_slop3(self):
        for rec in self:
            rec.slop3 = 0.0

            if rec.slop1:
                for line in rec.consolidation_output_ids:
                    # 👉 X22 == slop1
                    # 👉 B column == applied_pressure
                    if abs(line.applied_pressure - rec.slop1) < 0.0001:
                        # 👉 5th column == e_void
                        rec.slop3 = line.e_void
                        break

    
   

    @api.depends(
    'slop2',
    'consolidation_output_ids.applied_pressure',
    'consolidation_output_ids.e_void'
    )
    def _compute_slop4(self):
        for rec in self:
            rec.slop4 = 0.0

            if rec.slop2:
                for line in rec.consolidation_output_ids:
                    if abs(line.applied_pressure - rec.slop2) < 0.0001:
                        rec.slop4 = line.e_void
                        break



     

    

    @api.depends('consolidation_output_ids.applied_pressure')
    def _compute_slop2(self):
        for rec in self:
            rec.slop2 = 0.0

            for line in rec.consolidation_output_ids:
                if float(line.applied_pressure) == 4.0:
                    rec.slop2 = line.applied_pressure
                    break

    @api.depends('consolidation_output_ids.applied_pressure')
    def _compute_slop1(self):
        for rec in self:
            rec.slop1 = 0.0

            for line in rec.consolidation_output_ids:
                if float(line.applied_pressure) == 2.00:
                    rec.slop1 = line.applied_pressure
                    break

    bisector1 = fields.Float(string="Bisector 1", digits=(8, 3),compute="_compute_bisector1")
    bisector2 = fields.Float(string="Bisector 2", digits=(8, 3),compute="_compute_bisector2")

    bisector3 = fields.Float(string="Bisector 3", digits=(8, 5),default=0.81903)
    bisector4 = fields.Float(string="Bisector 4", digits=(8, 5),default=0.872173)

    bisector = fields.Float(string="Bisector Slop", digits=(8, 5),compute="_compute_bisector")

    bisector5 = fields.Float(string="Bisector C", digits=(8, 5),compute="_compute_bisector5")

    

    @api.depends('bisector5', 'slop5', 'slop', 'bisector')
    def _compute_preconsolidation_pressure_x(self):
        for rec in self:
            try:
                denominator = (rec.slop - rec.bisector)

                if denominator != 0:
                    power = (rec.bisector5 - rec.slop5) / denominator
                    rec.preconsolidation_pressure_x = math.pow(10, power)
                else:
                    rec.preconsolidation_pressure_x = 0.0

            except Exception:
                rec.preconsolidation_pressure_x = 0.0

    @api.depends('bisector3', 'bisector', 'bisector1')
    def _compute_bisector5(self):
        for rec in self:
            try:
                if rec.bisector1 > 0:
                    rec.bisector5 = rec.bisector3 - (rec.bisector * math.log10(rec.bisector1))
                else:
                    rec.bisector5 = 0.0
            except Exception:
                rec.bisector5 = 0.0


    @api.depends('consolidation_output_ids.applied_pressure')
    def _compute_bisector1(self):
        for rec in self:
            rec.bisector1 = 0.0

            for line in rec.consolidation_output_ids:
                if float(line.applied_pressure) == 8.0:
                    rec.bisector1 = line.applied_pressure
                    break

    @api.depends('consolidation_output_ids.applied_pressure')
    def _compute_bisector2(self):
        for rec in self:
            rec.bisector2 = 0.0

            for line in rec.consolidation_output_ids:
                if float(line.applied_pressure) == 0.5:
                    rec.bisector2 = line.applied_pressure
                    break

    @api.depends('bisector1', 'bisector2', 'bisector3', 'bisector4')
    def _compute_bisector(self):
        for rec in self:
            try:
                if rec.bisector1 > 0 and rec.bisector2 > 0:
                    rec.bisector = (rec.bisector3 - rec.bisector4) / math.log10(rec.bisector1 / rec.bisector2)
                else:
                    rec.bisector = 0.0
            except Exception:
                rec.bisector = 0.0






            

    preconsolidation_pressure = fields.Float(
    string="Preconsolidation Pressure,Pc",
    compute="_compute_preconsolidation_pressure",
    store=True
)
    
    @api.depends(
    'consolidation_output_ids.delta_cc',
    'consolidation_output_ids.applied_pressure',
    'consolidation_output_ids.cylces',
    'consolidation_output_ids.serial_no',
)
    def _compute_preconsolidation_pressure(self):
     for rec in self:
        rec.preconsolidation_pressure = 0.0

        # --- LOADING rows only (Calculation tab logic) ---
        loading = [
            l for l in rec.consolidation_output_ids.sorted('serial_no')
            if l.cylces == '1st Cycle Loading'
            and l.delta_cc not in (None, False)
            and l.applied_pressure not in (None, False)
        ]

        if len(loading) < 3:
            continue

        # --- Engineering plateau (max ΔCc zone) ---
        max_delta = max(l.delta_cc for l in loading)

        plateau = [l for l in loading if l.delta_cc == max_delta]

        if not plateau:
            continue

        # --- Engineering Pc = central value of plateau ---
        mid_index = len(plateau) // 2
        rec.preconsolidation_pressure = plateau[mid_index].applied_pressure










    effective_pressure = fields.Float(
    string="Effective Pressure",
    compute="_compute_effective_pressure",
    store=True
)
    @api.depends(
    'consolidation_output_ids.final_read',
    'consolidation_output_ids.applied_pressure',
    'consolidation_output_ids.cylces',
    'consolidation_output_ids.serial_no',
)
    def _compute_effective_pressure(self):
     for rec in self:
        rec.effective_pressure = 0.0

        lines = list(rec.consolidation_output_ids.sorted('serial_no'))
        if not lines:
            continue

        # 1️⃣ find FIRST zero dial reading
        zero_idx = None
        for i, line in enumerate(lines):
            if line.final_read == 0:
                zero_idx = i
                break

        if zero_idx is None:
            continue  # Excel condition not met

        # 2️⃣ walk backward to find last LOADING pressure
        for j in range(zero_idx - 1, -1, -1):
            prev = lines[j]
            if (
                prev.cylces == '1st Cycle Loading'
                and prev.applied_pressure not in (None, False)
            ):
                rec.effective_pressure = prev.applied_pressure
                break





    


    t22_e_value = fields.Float(
    string="T22 (e-value)",
    compute="_compute_t22_e_value",digits=(10,1),
    store=True
)

    @api.depends(
    'consolidation_output_ids.delta_cc',
    'consolidation_output_ids.e_void',
    'consolidation_output_ids.serial_no',
)
    def _compute_t22_e_value(self):
     for rec in self:
        rec.t22_e_value = 0.0

        lines = rec.consolidation_output_ids.sorted('serial_no')
        valid = [l for l in lines if l.delta_cc not in (None, False)]

        if not valid:
            continue

        max_delta = max(l.delta_cc for l in valid)

        for l in valid:  # FIRST match like Excel
            if l.delta_cc == max_delta:
                rec.t22_e_value = l.e_void or 0.0
                break
            

    pc_casagrande = fields.Float(
    string="Preconsolidation Pressure (Casagrande)",
    compute="_compute_pc_casagrande",
    store=True
)

    pc_x = fields.Float(string="Pc X", compute="_compute_pc_casagrande", store=True)
    pc_y = fields.Float(string="Preconsolidation Pressure (Pc) kg/cm²",compute="_compute_pc_y")

    @api.depends('preconsolidation_pressure_x')
    def _compute_pc_y(self):
        for rec in self:
            if rec.preconsolidation_pressure_x:
                # truncate to 2 decimal → 0.64902 → 0.63
                rec.pc_y = math.floor(rec.preconsolidation_pressure_x * 100) / 100
            else:
                rec.pc_y = 0.0

    pressure_y = fields.Float(
    string="Pressure Y",
    digits=(16, 7),
    compute="_compute_pressure_y"
)
    

    @api.depends('bisector', 'bisector5', 'preconsolidation_pressure_x')
    def _compute_pressure_y(self):
     for record in self:
        if record.preconsolidation_pressure_x > 0:
            record.pressure_y = (
                record.bisector *
                math.log10(record.preconsolidation_pressure_x)
            ) + record.bisector5
        else:
            record.pressure_y = 0.0

    preconsolidation_pressure_x = fields.Float(string="Preconsolidation Pressure X", digits=(16, 7),compute="_compute_preconsolidation_pressure_x")




    @api.depends(
        'consolidation_output_ids.e_void',
        'consolidation_output_ids.applied_pressure',
        'consolidation_output_ids.cylces',
    )
    def _compute_pc_casagrande(self):

        for rec in self:

            rec.pc_casagrande = 0.0
            rec.pc_x = 0.0
            rec.pc_y = 0.0
           
            rec.preconsolidation_pressure_x = 0.0

            # -----------------------------------
            # LOADING CURVE ONLY
            # -----------------------------------
            pts = [
                (
                    log10(l.applied_pressure),
                    l.e_void
                )
                for l in rec.consolidation_output_ids
                if (
                    l.cylces == '1st Cycle Loading'
                    and l.applied_pressure
                    and l.e_void
                    and l.applied_pressure > 0
                )
            ]

            if len(pts) < 4:
                continue

            # -----------------------------------
            # SORT BY PRESSURE
            # -----------------------------------
            pts.sort(key=lambda x: x[0])

            # -----------------------------------
            # MAX CURVATURE
            # -----------------------------------
            max_k = 0
            idx = None

            for i in range(1, len(pts) - 1):

                x1, y1 = pts[i - 1]
                x2, y2 = pts[i]
                x3, y3 = pts[i + 1]

                k = abs(
                    ((x2 - x1) * (y3 - y1))
                    -
                    ((y2 - y1) * (x3 - x1))
                )

                if k > max_k:
                    max_k = k
                    idx = i

            if idx is None:
                continue

            xm, ym = pts[idx]

            # -----------------------------------
            # TANGENT LINE
            # -----------------------------------
            x1, y1 = pts[idx - 1]
            x3, y3 = pts[idx + 1]

            if (x3 - x1) == 0:
                continue

            m_t = (y3 - y1) / (x3 - x1)
            c_t = ym - (m_t * xm)

            # -----------------------------------
            # HORIZONTAL LINE
            # -----------------------------------
            m_h = 0
            c_h = ym

            # -----------------------------------
            # BISECTOR
            # -----------------------------------
            m_b = (m_t + m_h) / 2
            c_b = ym - (m_b * xm)

            # -----------------------------------
            # NORMAL CONSOLIDATION LINE
            # -----------------------------------
            x_nc1, y_nc1 = pts[-2]
            x_nc2, y_nc2 = pts[-1]

            if (x_nc2 - x_nc1) == 0:
                continue

            m_nc = (
                (y_nc2 - y_nc1)
                /
                (x_nc2 - x_nc1)
            )

            c_nc = y_nc2 - (m_nc * x_nc2)

            # -----------------------------------
            # INTERSECTION
            # -----------------------------------
            if m_b == m_nc:
                continue

            x_pc = (
                (c_nc - c_b)
                /
                (m_b - m_nc)
            )

            y_pc = (m_b * x_pc) + c_b

            # -----------------------------------
            # FINAL VALUES
            # -----------------------------------

            # kg/cm²
            rec.pc_x = 10 ** x_pc

            rec.preconsolidation_pressure_x = rec.pc_x

            rec.pc_y = y_pc

            # kg/cm²
            rec.pc_casagrande = rec.pc_x

            

    pc_final = fields.Float(string="Preconsolidation Pressure (Pc) kg/cm²", compute="_compute_pc_final")

    @api.depends('pc_y')
    def _compute_pc_final(self):
        for rec in self:
            if rec.pc_y:
                rec.pc_final = rec.pc_y * 10000
            else:
                rec.pc_final = 0.0

    pc_depth = fields.Float(string="Depth", store=True)

   

    
    h13 = fields.Float(string="Depth (m)")
    pc_overburden = fields.Float(string="Overburden kg/cm²", compute="_compute_pc_value", store=True)

    @api.depends('pc_depth', 'con_bulk_density_soil')
    def _compute_pc_value(self):
        for rec in self:
            if rec.pc_depth and rec.con_bulk_density_soil:
                rec.pc_overburden = round(rec.pc_depth * (rec.con_bulk_density_soil * 1000), 2)
            else:
                rec.pc_overburden = 0.0

    ocr = fields.Float(string="OCR", compute="_compute_ocr", store=True)

    @api.depends('pc_final', 'pc_overburden')
    def _compute_ocr(self):
        for rec in self:
            if rec.pc_overburden:
                rec.ocr = round(rec.pc_final / rec.pc_overburden, 2)
            else:
                rec.ocr = 0.0

    cc_final = fields.Float(
        string="Compression Index (Cc)",
        digits=(16, 3), compute="_compute_cc_final"
      
    )

    @api.depends(
        'consolidation_output_ids.applied_pressure',
        'consolidation_output_ids.cc',
        'consolidation_output_ids.cylces'
    )
    def _compute_cc_final(self):
        for rec in self:
            rec.cc_final = 0.0

            # 🔹 ONLY 1st Cycle Loading lines
            loading_lines = rec.consolidation_output_ids.filtered(
                lambda l: l.cylces == "1st Cycle Loading"
            )

            if len(loading_lines) < 2:
                continue

            # Excel B18 logic → last loading row
            last = loading_lines[-1]
            prev = loading_lines[-2]

            # Excel: =IF(B18=0, N17, N18)
            if last.applied_pressure == 0:
                rec.cc_final = prev.cc
            else:
                rec.cc_final = last.cc









   



    

    

    






    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ConsolidationLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class CbrLine(models.Model):
    _name = "cbr.line"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id",ondelete='cascade')

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    is_checked = fields.Boolean(
        string="Calculated",
        default=False
    )
    start_date = fields.Date(string="Start Date")  # manually fill
    end_date = fields.Date(string="End Date")      # auto fill on submit

    
    def action_submit(self):
        self.ensure_one()
        
        # Boolean True save
        self.write({
            'is_checked': True,
            # 'end_date': fields.Date.context_today(self),  # current date auto fill
        })
        
        # Close inline editor → Save-like back
        return {'type': 'ir.actions.act_window_close'}



    initial_height = fields.Float(string="Initial height of specimen, h (mm)")
    initial_dial_guage = fields.Float(string="Initial dial gauge reading, ds (mm)")
    final_dial_guage = fields.Float(string="Final dial gauge reading, df (mm)",compute="_compute_final_dial_guage", store=True)

    @api.depends('soil_table.proving_reading', 'soil_table.serial_no')
    def _compute_final_dial_guage(self):
        for rec in self:
            rec.final_dial_guage = 0.0

            if not rec.soil_table:
                continue

            # sort by serial_no (safe)
            last_line = rec.soil_table.sorted(
                lambda l: l.serial_no or 0
            )[-1]

            rec.final_dial_guage = last_line.proving_reading or 0.0


    lab_id=  fields.Char(string="Lab ID" )
    bh_id = fields.Char(
        string="BH ID",
        compute="_compute_bh_id",
        store=True
    )

    @api.depends('lab_id')
    def _compute_bh_id(self):
        ReviewLine = self.env['sample.request.review.lines']

        for line in self:
            line.bh_id = False

            if not line.lab_id:
                continue

            review_line = ReviewLine.search(
                [('lab_id', '=', line.lab_id)],
                order='id desc',
                limit=1
            )

            if review_line:
                line.bh_id = review_line.source




    humidity= fields.Char(string="Humidity %" )


    soil_table = fields.One2many('mechanical.cbr.line1','parent_id_cbr',string="CBR",default=lambda self: self._default_cbr_child_lines())

    cbr_2_5_mm = fields.Float(string="CBR At Penetration Of 2.5 mm",compute="_compute_cbr_values") 
    cbr_5_mm = fields.Float(string="CBR At Penetration Of 5 mm",compute="_compute_cbr_values")

    final_cbr = fields.Float(
    string="Final CBR",
    compute="_compute_final_cbr",
    store=True
)

    @api.depends('cbr_2_5_mm', 'cbr_5_mm')
    def _compute_final_cbr(self):
     for rec in self:
        rec.final_cbr = max(
            rec.cbr_2_5_mm or 0.0,
            rec.cbr_5_mm or 0.0
        )

    m = fields.Float(string="Applied force (kN) (m)",default=0.0133, digits=(10,4))
    c = fields.Float(string="Applied force (kN) (c)",default=0.0404 , digits=(10,4))

    proving_ring_capacity = fields.Float(string="Proving ring capacity (kN)", digits=(10,0))

    # condition_specimen = fields.Char(string="Condition of specimen at test")

    condition_specimen = fields.Selection([
    ('soaked', 'Soaked'),
    ('unsoaked', 'Unsoaked'),], string="Condition of specimen at test")

    # sample_type = fields.Char(string="Sample Type",default="Remolded")


    sample_type = fields.Selection([
    ('undisturbed', 'Undisturbed'),
    ('remoulded', 'Remoulded'),], string="Sample Type")

    # type_compact = fields.Char(string="Type of compaction")

    type_compact = fields.Selection([
    ('Static', 'Static'),
    ('Dynamic', 'Dynamic'),], string="Type of compaction", default='Static')

   


    soil_fract_20mm = fields.Char(string="Soil fraction above 20mm replaced, (Kg)")

    period_soaked = fields.Float(string="Period of soaking(days)", digits=(10,0))

    surcharge_weight = fields.Float(string="Surcharge weight (kg)", digits=(10,2))

    
    @api.depends('soil_table.penetration', 'soil_table.avg_load')
    def _compute_cbr_values(self):
     for record in self:
        val_2_5 = 0.0
        val_5_0 = 0.0

        lines = record.soil_table.sorted(key=lambda l: l.penetration)

        def interpolate(x):
            for i in range(len(lines) - 1):
                x1 = lines[i].penetration
                x2 = lines[i + 1].penetration
                y1 = lines[i].avg_load
                y2 = lines[i + 1].avg_load

                if x1 <= x <= x2:
                    return y1 + (x - x1) * (y2 - y1) / (x2 - x1)
            return 0.0

        if len(lines) >= 2:
            load_2_5 = interpolate(2.5)
            load_5_0 = interpolate(5.0)

            val_2_5 = round((load_2_5 * 100) / 13.781, 2)
            val_5_0 = round((load_5_0 * 100) / 20.55, 2)

        record.cbr_2_5_mm = val_2_5
        record.cbr_5_mm = val_5_0

   
    cbr_graph = fields.Binary(string="CBR Graph") 
    cbr_graph_name = fields.Char(default="cbr_graph.png")






    def action_generate_cbr_graph(self):
     import matplotlib.pyplot as plt
     import numpy as np
     import io
     import base64

     for record in self:
        if not record.soil_table:
            continue

        # Sort data by penetration
        lines = record.soil_table.sorted(key=lambda l: l.penetration)

        x_values = [line.penetration for line in lines]
        y_values = [line.avg_load for line in lines]

        if not x_values or not y_values:
            continue

        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)

        # Main CBR curve (black line with dots)
        ax.plot(x_values, y_values, 'ko-', linewidth=1.5, markersize=6)

        # Target penetrations
        target_x = [2.5, 5.0]

        # Interpolation for exact Y values
        target_y = np.interp(target_x, x_values, y_values)

        for tx, ty in zip(target_x, target_y):
            if tx <= max(x_values):
                # Vertical blue line
                ax.plot([tx, tx], [0, ty], color='blue', linewidth=1)

                # Horizontal blue line
                ax.plot([0, tx], [ty, ty], color='blue', linewidth=1)

                # Intersection point
                
                ax.plot(tx, ty, 'bo', markersize=5)

                # Numeric value near intersection
                # ax.text(tx + 0.1, ty + 0.01, f"{ty:.2f}",
                #         color='blue', fontsize=10, fontweight='bold')

                # Penetration label ON horizontal line
                ax.text(0.3, ty + (ax.get_ylim()[1] * 0.02),
        f"{tx} mm Penetration",
        fontsize=10,
        color='black',
        ha='left')

        # Axis labels
        ax.set_xlabel('Penetration in mm', fontweight='bold', fontsize=12)
        ax.set_ylabel('Average Load in kN', fontweight='bold', fontsize=12)

        # Axis limits
        ax.set_xlim(0, max(x_values))
        ax.set_ylim(bottom=0)

        # X ticks every 1 mm
        ax.set_xticks(np.arange(0, int(max(x_values)) + 2, 1))

        # Excel-like grid
        ax.grid(True, alpha=0.4)

        # Axes crossing at zero
        ax.spines['left'].set_position(('data', 0))
        ax.spines['bottom'].set_position(('data', 0))
        ax.spines['right'].set_color('none')
        ax.spines['top'].set_color('none')

        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')

        # Save image
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)

        record.cbr_graph = base64.b64encode(buf.getvalue())

    

    @api.model
    def _default_cbr_child_lines(self):
        default_lines = [
            (0, 0, {'penetration': '0.0'}),
            (0, 0, {'penetration': '0.50 '}),
            (0, 0, {'penetration': '1.00'}),
            (0, 0, {'penetration': '1.50'}),
            (0, 0, {'penetration': '2.00'}),
            (0, 0, {'penetration': '2.50'}),
            (0, 0, {'penetration': ' 4.00'}),
            (0, 0, {'penetration': '5.00'}),
            (0, 0, {'penetration': '7.50'}),
            (0, 0, {'penetration': '10.00'}),
            (0, 0, {'penetration': '12.50'}),
           
        ]
        return default_lines

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
    top_wt_dry_soil = fields.Float(compute="_compute_wt_dry_soil1", store=True,digits=(12,3))
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
    centre_wt_dry_soil = fields.Float(compute="_compute_wt_dry_soil1", store=True,digits=(12,3))
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
    bottom_wt_dry_soil = fields.Float(compute="_compute_wt_dry_soil1", store=True,digits=(12,3))
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
    def _compute_wt_dry_soil1(self):
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

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CbrLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


    


class SoilNote(models.Model):
    _name = "soil1.notes"

    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")



    




    