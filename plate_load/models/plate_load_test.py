from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math
import matplotlib.pyplot as plt
import io
import base64
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline





class PlateLoad(models.Model):
    _name = "mechanical.plate.test1"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="PLATE LOAD TEST ")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)


    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id





            # remark

    notes_id = fields.One2many('plateload.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(PlateLoad, self).default_get(fields)

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
    





      # Dimensions

    plate_load_name = fields.Char("Name",default="PLATE LOAD TEST CALCULATIONS")
    plate_load_visible = fields.Boolean("Dimensions Visible",compute="_compute_visible")   

    client_name = fields.Char(string="Client Name")
    site_add = fields.Char(string="Site Address")
    months = fields.Char(string="Months")
    bearing_plate = fields.Char(string="Bearing plate")
    jack_capacity = fields.Char(string="Jack  capacity ")
    reaction_load = fields.Char(string="Reaction load is applied using")
    bearing_dead = fields.Char(string="bearing dead weight ")
    no_cycle1 = fields.Char(string="No. of Cycle")
    factor_safty = fields.Char(string="factor of safety")
    allowable_net = fields.Char(string="The net allowable safe bearing capacity")

    introdution = fields.Text(string="Introdution")

    objective = fields.Text(string="Objective")

    apparatus = fields.Text(string="Apparatus")

    test_procedure = fields.Text(string="Setup & Test Procedure")


  
   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_plate_load = fields.One2many('mechanical.plate.test.line','parent_id',string="Parameter")

    # def action_calculate_cumulative_settlement(self):
    #     for rec in self:
    #         lines = rec.child_lines_plate_load.sorted(key=lambda l: l.sr_no)

    #         # Reset all values
    #         for l in lines:
    #             l.cumulative_sett1 = 0.0

    #         # Get only applied pressure lines (pressure steps)
    #         pressure_lines = [l for l in lines if l.applied_pressure and l.applied_pressure > 0]

    #         for idx, pline in enumerate(pressure_lines):
    #             current_line = pline

    #             # Find next pressure line
    #             if idx + 1 < len(pressure_lines):
    #                 next_pressure_line = pressure_lines[idx + 1]

    #                 # Take last line BEFORE next pressure
    #                 ref_line = next(
    #                     (l for l in reversed(lines)
    #                     if l.sr_no < next_pressure_line.sr_no),
    #                     None
    #                 )
    #             else:
    #                 # Last pressure → take last line in table
    #                 ref_line = lines[-1] if lines else None

    #             if not ref_line:
    #                 continue

    #             # FINAL CALCULATION
    #             current_line.cumulative_sett1 = (
    #                 ref_line.avg_sett - current_line.avg_sett
    #             )

    def action_calculate_cumulative_settlement(self):
        for rec in self:
            lines = rec.child_lines_plate_load.sorted(key=lambda l: l.sr_no)

            # Reset all values
            for l in lines:
                l.cumulative_sett1 = 0.0

            # Get only applied pressure lines (> 0)
            pressure_lines = [l for l in lines if l.applied_pressure and l.applied_pressure > 0]

            for idx, current_line in enumerate(pressure_lines):

                # ---------- FIRST PRESSURE ----------
                if idx == 0:
                    # Find next pressure line
                    if idx + 1 < len(pressure_lines):
                        next_pressure_line = pressure_lines[idx + 1]

                        # Take last line BEFORE next pressure
                        ref_line = next(
                            (l for l in reversed(lines)
                            if l.sr_no < next_pressure_line.sr_no),
                            None
                        )
                    else:
                        ref_line = lines[-1] if lines else None

                    if not ref_line:
                        continue

                    # Base calculation (difference)
                    current_line.cumulative_sett1 = (
                        ref_line.avg_sett - current_line.avg_sett
                    )

                # ---------- SECOND & NEXT PRESSURES ----------
                else:
                    prev_pressure_line = pressure_lines[idx - 1]

                    current_line.cumulative_sett1 = (
                        (prev_pressure_line.cumulative_sett1 or 0.0)
                        + (current_line.avg_sett or 0.0)
                    )





    # def action_calculate_settlement(self):
    #     for rec in self:
    #         lines = rec.child_lines_plate_load.sorted(key=lambda l: l.sr_no)
    #         pressure_lines = [line for line in lines if line.applied_pressure]

    #         # Step 1: Clear all avg_sett and cumulative_sett1
    #         for line in lines:
    #             line.avg_sett = 0.0
    #             line.cumulative_sett1 = 0.0

    #         # Step 2: Calculate avg_sett
    #         for i in range(len(pressure_lines)):
    #             first_pressure = pressure_lines[i]

    #             if i + 1 < len(pressure_lines):
    #                 # Normal case: next applied_pressure exists
    #                 second_pressure = pressure_lines[i + 1]
    #                 ref_sr_no = second_pressure.sr_no - 1
    #                 ref_line = next((l for l in lines if l.sr_no == ref_sr_no), None)
    #             else:
    #                 # Last applied_pressure: use last line after current
    #                 ref_line = next((l for l in reversed(lines) if l.sr_no > first_pressure.sr_no), None)

    #             if not ref_line:
    #                 continue

    #             # Calculate avg_sett = ref - current
    #             d1 = ref_line.d1 - first_pressure.d1
    #             d2 = ref_line.d2 - first_pressure.d2
    #             d3 = ref_line.d3 - first_pressure.d3
    #             d4 = ref_line.d4 - first_pressure.d4
    #             avg = (d1 + d2 + d3 + d4) / 4.0

    #             first_pressure.avg_sett = avg

    #         # Step 3: Calculate cumulative_sett1
    #         cumulative = 0.0
    #         for line in lines:
    #             if line.avg_sett and line.avg_sett > 0.0:
    #                 cumulative += line.avg_sett
    #                 line.cumulative_sett1 = cumulative
    #             else:
    #                 line.cumulative_sett1 = 0.0






    child_lines_plate_unload = fields.One2many('mechanical.unload.test.line1','parent_id',string="UNLOADING LINE")


    
    def action_calculate_unload_settlement_and_cumulative(self):
        for rec in self:
            running_total = 0.0

            # Start with last loading cumulative
            if rec.child_lines_plate_load:
                last_line = rec.child_lines_plate_load.sorted('sr_no')[-1]
                running_total = last_line.cumulative_sett1 or 0.0

            # Now unloading lines
            for line in rec.child_lines_plate_unload.sorted('sr_no'):
                running_total = running_total + (line.avg_sett1 or 0.0)
                line.cumulative_sett11 = running_total


    





    child_lines_loadand_cumilitive = fields.One2many('mechanical.load.cumilitive.line1','parent_id')

    child_lines_loadand_cumilitive1 = fields.One2many('mechanical.load.cumilitive.line2','parent_id')

    chart_pressure_line = fields.Binary("Line Chart", compute="_compute_pressure_line_chart", store=True)





    def generate_pressure_line_chart(self):
  

        x_vals = []
        y_vals = []

        for line in self.child_lines_loadand_cumilitive1:
            if line.pressure_plate3 is not None and line.settlement3 is not None:
                x_vals.append(line.pressure_plate3)
                y_vals.append(line.settlement3)

        if len(x_vals) < 3:
            return ""

        max_idx = np.argmax(x_vals)

        # 1. Loading part
        x_up = x_vals[:max_idx + 1]
        y_up = y_vals[:max_idx + 1]

        x_last = x_up[-1]
        y_last = y_up[-1]

        # 2. Actual Unloading values (user provided, after max_idx)
        raw_unloading_x = x_vals[max_idx + 1:]
        raw_unloading_y = y_vals[max_idx + 1:]

        # 3. Prepare unloading with side shift
        shift_x = 6  # 🔁 shift the unloading X values leftwards
        x_down = []
        y_down = []

        if raw_unloading_x and len(raw_unloading_x) >= 1:
            # Add loading last point as the first point of unloading
            x_down.append(x_last)
            y_down.append(y_last)

            for i in range(len(raw_unloading_x)):
                x_shifted = raw_unloading_x[i] - shift_x
                x_down.append(x_shifted)
                y_down.append(raw_unloading_y[i])

        def smooth(x, y):
            if len(x) < 3:
                return x, y
            x_np = np.array(x)
            y_np = np.array(y)
            sorted_idx = np.argsort(x_np)
            x_np = x_np[sorted_idx]
            y_np = y_np[sorted_idx]
            x_s = np.linspace(x_np.min(), x_np.max(), 150)
            spline = make_interp_spline(x_np, y_np, k=2)
            y_s = spline(x_s)
            return x_s, y_s

        # Smooth lines
        x_up_s, y_up_s = smooth(x_up, y_up)
        x_down_s, y_down_s = smooth(x_down, y_down) if len(x_down) >= 3 else (x_down, y_down)

        # Plotting
        plt.figure(figsize=(7, 4))
        plt.plot(x_up_s, y_up_s,color="blue", linewidth=2 ) 
        

        if x_down and len(x_down) >= 2:
            plt.plot(x_down_s, y_down_s, color="blue", linewidth=2)
            

        # Show raw points
        plt.scatter(x_up, y_up, color='black', s=30, marker='D')
        if x_down:
            plt.scatter(x_down, y_down, color='gray', s=30, marker='D')

        plt.gca().invert_yaxis()
        plt.xlabel('Applied Load (T/m²)', fontsize=10)
        plt.ylabel('Settlement (mm)', fontsize=10)
        plt.title('LOAD SETTLEMENT CURVE', fontsize=14, fontweight='bold')
        plt.grid(True, linestyle='--', alpha=0.4)
        plt.legend()
        plt.tight_layout()

        # Convert to image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')


    












        
    @api.depends('child_lines_loadand_cumilitive1')
    def _compute_pressure_line_chart(self):
        for record in self:
            try:
                record.chart_pressure_line = record.generate_pressure_line_chart()
            except:
                record.chart_pressure_line = ""


    plate_report_upload = fields.Many2many(
        'ir.attachment',
        'plate_report_upload_rel',
        'sample_id',
        'attachment_id',
        string='Report Upload',
        help='Attach multiple reports or PDFs to the sample',
    )


   

    

    # @api.onchange('child_lines_plate_load')
    # def _onchange_child_lines_pressure_fill(self):
    #     for rec in self:
    #         for i, line in enumerate(rec.child_lines_plate_load):
    #             if i == 0:
    #                 line.applied_pressure = rec.pressure_3
    #                 line.load_plate = (line.applied_pressure * (rec.ram_area)) / 1000
    #                 line.pressure_plate = (line.load_plate / (rec.lenght_plate * rec.width_plate)) 
    #             elif i == 1:
    #                 line.time = 2.25
    #             elif i == 2:
    #                 line.time = 4
    #             elif i == 3:
    #                 line.time = 6.25
    #             elif i == 4:
    #                 line.time = 9
    #             elif i == 5:
    #                 line.time = 12
    #             elif i == 6:
    #                 line.time = 16
    #             elif i == 7:
    #                 line.time = 25
    #             elif i == 8:
    #                 line.time = 36
    #             elif i == 9:
    #                 line.time = 64
    #             elif i == 10:
    #                 line.time = 90
    #             elif i == 11:
    #                 line.time = 120
                  
    #             elif i == 12:
    #                 line.applied_pressure = rec.pressure_3 * 2
    #                 line.load_plate = (line.applied_pressure * (rec.ram_area)) / 1000
    #                 line.pressure_plate = (line.load_plate / (rec.lenght_plate * rec.width_plate)) 
    #             elif i == 13:
    #                 line.time = 2.25
    #             elif i == 14:
    #                 line.time = 4
    #             elif i == 15:
    #                 line.time = 6.25
    #             elif i == 16:
    #                 line.time = 9
    #             elif i == 17:
    #                 line.time = 12
    #             elif i == 18:
    #                 line.time = 16
    #             elif i == 19:
    #                 line.time = 25
    #             elif i == 20:
    #                 line.time = 36
    #             elif i == 21:
    #                 line.time = 64
    #             elif i == 22:
    #                 line.time = 90
    #             elif i == 23:
    #                 line.time = 120
    #             elif i == 24:
    #                 line.applied_pressure = rec.pressure_3 * 3
    #                 line.load_plate = (line.applied_pressure * (rec.ram_area)) / 1000
    #                 line.pressure_plate = (line.load_plate / (rec.lenght_plate * rec.width_plate)) 
    #             elif i == 25:
    #                 line.time = 2.25
    #             elif i == 26:
    #                 line.time = 4
    #             elif i == 27:
    #                 line.time = 6.25
    #             elif i == 28:
    #                 line.time = 9
    #             elif i == 29:
    #                 line.time = 12
    #             elif i == 30:
    #                 line.time = 16
    #             elif i == 31:
    #                 line.time = 25
    #             elif i == 32:
    #                 line.time = 36
    #             elif i == 33:
    #                 line.time = 64
    #             elif i == 34:
    #                 line.time = 90
    #             elif i == 35:
    #                 line.time = 120

    #             elif i == 36:
    #                 line.applied_pressure = rec.pressure_3 * 4
    #                 line.load_plate = (line.applied_pressure * (rec.ram_area)) / 1000
    #                 line.pressure_plate = (line.load_plate / (rec.lenght_plate * rec.width_plate)) 
    #             elif i == 37:
    #                 line.time = 2.25
    #             elif i == 38:
    #                 line.time = 4
    #             elif i == 39:
    #                 line.time = 6.25
    #             elif i == 40:
    #                 line.time = 9
    #             elif i == 41:
    #                 line.time = 12
    #             elif i == 42:
    #                 line.time = 16
    #             elif i == 43:
    #                 line.time = 25
    #             elif i == 44:
    #                 line.time = 36
    #             elif i == 45:
    #                 line.time = 64
    #             elif i == 46:
    #                 line.time = 90
    #             elif i == 47:
    #                 line.time = 120

    #             elif i == 48:
    #                 line.applied_pressure = rec.pressure_3 * 5
    #                 line.load_plate = (line.applied_pressure * (rec.ram_area)) / 1000
    #                 line.pressure_plate = (line.load_plate / (rec.lenght_plate * rec.width_plate)) 
    #             elif i == 49:
    #                 line.time = 2.25
    #             elif i == 50:
    #                 line.time = 4
    #             elif i == 51:
    #                 line.time = 6.25
    #             elif i == 52:
    #                 line.time = 9
    #             elif i == 53:
    #                 line.time = 12
    #             elif i == 54:
    #                 line.time = 16
    #             elif i == 55:
    #                 line.time = 25
    #             elif i == 56:
    #                 line.time = 36
    #             elif i == 57:
    #                 line.time = 64
    #             elif i == 58:
    #                 line.time = 90
    #             elif i == 59:
    #                 line.time = 120

    #             elif i == 60:
    #                 line.applied_pressure = rec.pressure_3 * 6
    #                 line.load_plate = (line.applied_pressure * (rec.ram_area)) / 1000
    #                 line.pressure_plate = (line.load_plate / (rec.lenght_plate * rec.width_plate)) 
    #             elif i == 61:
    #                 line.time = 2.25
    #             elif i == 62:
    #                 line.time = 4
    #             elif i == 63:
    #                 line.time = 6.25
    #             elif i == 64:
    #                 line.time = 9
    #             elif i == 65:
    #                 line.time = 12
    #             elif i == 66:
    #                 line.time = 16
    #             elif i == 67:
    #                 line.time = 25
    #             elif i == 68:
    #                 line.time = 36
    #             elif i == 69:
    #                 line.time = 64
    #             elif i == 70:
    #                 line.time = 90
    #             elif i == 71:
    #                 line.time = 120

    #             elif i == 72:
    #                 line.applied_pressure = rec.pressure_3 * 7
    #                 line.load_plate = (line.applied_pressure * (rec.ram_area)) / 1000
    #                 line.pressure_plate = (line.load_plate / (rec.lenght_plate * rec.width_plate)) 
    #             elif i == 73:
    #                 line.time = 2.25
    #             elif i == 74:
    #                 line.time = 4
    #             elif i == 75:
    #                 line.time = 6.25
    #             elif i == 76:
    #                 line.time = 9
    #             elif i == 77:
    #                 line.time = 12
    #             elif i == 78:
    #                 line.time = 16
    #             elif i == 79:
    #                 line.time = 25
    #             elif i == 80:
    #                 line.time = 36
    #             elif i == 81:
    #                 line.time = 64
    #             elif i == 82:
    #                 line.time = 90
    #             elif i == 83:
    #                 line.time = 120

    #             elif i == 84:
    #                 line.applied_pressure = rec.pressure_3 * 8
    #                 line.load_plate = (line.applied_pressure * (rec.ram_area)) / 1000
    #                 line.pressure_plate = (line.load_plate / (rec.lenght_plate * rec.width_plate)) 
    #             elif i == 85:
    #                 line.time = 2.25
    #             elif i ==  86:
    #                 line.time = 4
    #             elif i == 87:
    #                 line.time = 6.25
    #             elif i == 88:
    #                 line.time = 9
    #             elif i == 89:
    #                 line.time = 12
    #             elif i == 90:
    #                 line.time = 16
    #             elif i == 91:
    #                 line.time = 25
    #             elif i == 92:
    #                 line.time = 36
    #             elif i == 93:
    #                 line.time = 64
    #             elif i == 94:
    #                 line.time = 90
    #             elif i == 95:
    #                 line.time = 120

    #             elif i == 96:
    #                 line.applied_pressure = rec.pressure_3 * 9
    #                 line.load_plate = (line.applied_pressure * (rec.ram_area)) / 1000
    #                 line.pressure_plate = (line.load_plate / (rec.lenght_plate * rec.width_plate)) 
    #             elif i == 97:
    #                 line.time = 2.25
    #             elif i == 98:
    #                 line.time = 4
    #             elif i == 99:
    #                 line.time = 6.25
    #             elif i == 100:
    #                 line.time = 9
    #             elif i == 101:
    #                 line.time = 12
    #             elif i == 102:
    #                 line.time = 16
    #             elif i == 103:
    #                 line.time = 25
    #             elif i == 104:
    #                 line.time = 36
    #             elif i == 105:
    #                 line.time = 64
    #             elif i == 106:
    #                 line.time = 90
    #             elif i == 107:
    #                 line.time = 120

    #             elif i == 108:
    #                 line.applied_pressure = rec.pressure_3 * 10
    #                 line.load_plate = (line.applied_pressure * (rec.ram_area)) / 1000
    #                 line.pressure_plate = (line.load_plate / (rec.lenght_plate * rec.width_plate)) 
    #             elif i == 109:
    #                 line.time = 2.25
    #             elif i == 110:
    #                 line.time = 4
    #             elif i == 111:
    #                 line.time = 6.25
    #             elif i == 112:
    #                 line.time = 9
    #             elif i == 113:
    #                 line.time = 12
    #             elif i == 114:
    #                 line.time = 16
    #             elif i == 115:
    #                 line.time = 25
    #             elif i == 116:
    #                 line.time = 36
    #             elif i == 117:
    #                 line.time = 64
    #             elif i == 118:
    #                 line.time = 90
    #             elif i == 119:
    #                 line.time = 120

    #             elif i == 120:
    #                 line.applied_pressure = rec.pressure_3 * 11
    #                 line.load_plate = (line.applied_pressure * (rec.ram_area)) / 1000
    #                 line.pressure_plate = (line.load_plate / (rec.lenght_plate * rec.width_plate)) 
    #             elif i == 121:
    #                 line.time = 2.25
    #             elif i ==  122:
    #                 line.time = 4
    #             elif i == 123:
    #                 line.time = 6.25
    #             elif i == 124:
    #                 line.time = 9
    #             elif i == 125:
    #                 line.time = 12
    #             elif i == 126:
    #                 line.time = 16
    #             elif i == 127:
    #                 line.time = 25
    #             elif i == 128:
    #                 line.time = 36
    #             elif i == 129:
    #                 line.time = 64
    #             elif i == 130:
    #                 line.time = 90
    #             elif i == 131:
    #                 line.time = 120

    #             elif i == 132:
    #                 line.applied_pressure = rec.pressure_3 * 12
    #                 line.load_plate = (line.applied_pressure * (rec.ram_area)) / 1000
    #                 line.pressure_plate = (line.load_plate / (rec.lenght_plate * rec.width_plate)) 
    #             elif i == 133:
    #                 line.time = 2.25
    #             elif i == 134:
    #                 line.time = 4
    #             elif i == 135:
    #                 line.time = 6.25
    #             elif i == 136:
    #                 line.time = 9
    #             elif i == 137:
    #                 line.time = 12
    #             elif i == 138:
    #                 line.time = 16
    #             elif i == 139:
    #                 line.time = 25
    #             elif i == 140:
    #                 line.time = 36
    #             elif i == 141:
    #                 line.time = 64
    #             elif i == 142:
    #                 line.time = 90
    #             elif i == 143:
    #                 line.time = 120

              
    #             elif i == 144:
    #                 line.applied_pressure = rec.pressure_3 * 13
    #                 line.load_plate = (line.applied_pressure * (rec.ram_area)) / 1000
    #                 line.pressure_plate = (line.load_plate / (rec.lenght_plate * rec.width_plate)) 

    #             elif i == 145:
    #                 line.time = 2.25
    #             elif i == 146:
    #                 line.time = 4
    #             elif i == 147:
    #                 line.time = 6.25
    #             elif i == 148:
    #                 line.time = 9
    #             elif i == 149:
    #                 line.time = 12
    #             elif i == 150:
    #                 line.time = 16
    #             elif i == 151:
    #                 line.time = 25
    #             elif i == 152:
    #                 line.time = 36
    #             elif i == 153:
    #                 line.time = 64
    #             elif i == 154:
    #                 line.time = 90
    #             elif i == 155:
    #                 line.time = 120
                
                # else:
                #     line.applied_pressure = 0.0



   
    design_load = fields.Float(string="Design Load (T/m²)",digits=(12,3))
    factore = fields.Float(string="Factor of safety(FOS)",digits=(12,3))
    ultimate = fields.Float(string="Ultimate Load  (T/m²)",digits=(12,3),compute="_compute_ultimate")
    lenght_plate = fields.Float(string="Length of Plate (m)",digits=(12,2))
    width_plate = fields.Float(string="Width of Plate (m)",digits=(12,2))
    area_plate = fields.Float(string="Area of Plate (m²)",digits=(12,4),compute="_compute_area_plate")
    ram_area = fields.Float(string="RAM Area (cm²)",digits=(12,3))
    load_intergity = fields.Float(string="Load Intensity (T)",digits=(12,3),compute="_compute_load_intergity")
    pressure = fields.Float(string="Pressure (kg/m²)",digits=(12,2),compute="_compute_pressure")

    pressure_1 = fields.Float(string="Pressure (kg/m²)",digits=(12,2),compute="_compute_pressure1")
    no_cycle = fields.Float(string="No. of cycle")
    pressure_2 = fields.Float(string="Pressure",digits=(12,2),compute="_compute_pressure_values")
    pressure_3 = fields.Float(string="Pressure (Roundoff)",digits=(12,2),compute="_compute_pressure_values")
    total_pressure = fields.Float(string="Total Applied Pressure  (kg/m²)",digits=(12,2),compute="_compute_pressure_values")

    

    @api.depends('pressure')
    def _compute_pressure1(self):
        for record in self:
            record.pressure_1 = record.pressure or 0.0

    @api.depends('pressure_1', 'no_cycle')
    def _compute_pressure_values(self):
        for record in self:
            cycle = record.no_cycle or 1.0  # Prevent divide by zero
            pressure_base = record.pressure_1 or 0.0

            # Step 1: pressure_2 = pressure_1 / no_cycle
            record.pressure_2 = pressure_base / cycle

            # Step 2: pressure_3 = CEILING(pressure_2, no_cycle)
            if cycle > 0:
                record.pressure_3 = math.ceil(record.pressure_2 / cycle) * cycle
            else:
                record.pressure_3 = 0.0

            # Step 3: total_pressure = pressure_3 * no_cycle
            record.total_pressure = record.pressure_3 * cycle

  

    



    @api.depends('design_load', 'factore')
    def _compute_ultimate(self):
        for record in self:
            record.ultimate = (record.design_load or 0.0) * (record.factore or 0.0)

    @api.depends('lenght_plate', 'width_plate')
    def _compute_area_plate(self):
        for record in self:
            record.area_plate = (record.lenght_plate or 0.0) * (record.width_plate or 0.0)

    @api.depends('ultimate', 'area_plate')
    def _compute_load_intergity(self):
        for record in self:
            record.load_intergity = (record.ultimate or 0.0) * (record.area_plate or 0.0)

    @api.depends('load_intergity', 'ram_area')
    def _compute_pressure(self):
        for record in self:
            if record.ram_area:
                record.pressure = (record.load_intergity or 0.0) / record.ram_area * 1000
            else:
                record.pressure = 0.0

    # Summary of test

    bearing_capacity = fields.Float(string="Safe Bearing Capacity  t/m²",digits=(12,1))
    factore_safty = fields.Float(string="Factor of Safety",digits=(12,1))
    ultimate_bearing = fields.Float(string="Ultimate Bearing Capacity  t/m²",digits=(12,1))
    maximum_load = fields.Float(string="Maximum load Intensity on plate , t/m²",digits=(12,2),compute="_compute_maximum_load")
    allowable = fields.Float(string="Allowable Bearing Capacity of soil , t/m²",digits=(12,2),compute="_compute_allowable_bearing_capacity")
    total_settlement = fields.Float(string="Total Settlement of plate ,mm",digits=(12,3),compute="_compute_settlement_load")

    @api.depends('child_lines_loadand_cumilitive.pressure_plate2')
    def _compute_maximum_load(self):
        for rec in self:
            pressures = [line.pressure_plate2 for line in rec.child_lines_loadand_cumilitive if line.pressure_plate2]
            rec.maximum_load = max(pressures) if pressures else 0.0

    @api.depends('child_lines_loadand_cumilitive.cumulative_sett2')
    def _compute_settlement_load(self):
        for rec in self:
            settlement = [line.cumulative_sett2 for line in rec.child_lines_loadand_cumilitive if line.cumulative_sett2]
            rec.total_settlement = max(settlement) if settlement else 0.0
    
    @api.depends('maximum_load', 'factore_safty')
    def _compute_allowable_bearing_capacity(self):
        for rec in self:
            if rec.factore_safty:
                rec.allowable = rec.maximum_load / rec.factore_safty
            else:
                rec.allowable = 0.0


# CALCULATION FOR ALLOWABLE BEARING CAPACITY BASED ON RESULT OF PLATE LOAD TEST

    size_footing = fields.Float(string="Bf=Size of footing in metre",digits=(12,1))
    size_plate = fields.Float(string="Bp=Size of plate in metre",digits=(12,2))
    settlement_test = fields.Float(string="Sp=Settlement  of test plate in mm",digits=(12,2))
    settlement_below = fields.Float(string="Settlement Below PCC, Sf",digits=(12,2),compute="_compute_settlement_below")

    observation = fields.Text(string="Observation")

    @api.depends('settlement_test', 'size_footing', 'size_plate')
    def _compute_settlement_below(self):
        for rec in self:
            if rec.settlement_test and rec.size_footing and rec.size_plate:
                try:
                    numerator = rec.size_footing * (rec.size_plate + 0.3)
                    denominator = rec.size_plate * (rec.size_footing + 0.3)
                    ratio = numerator / denominator if denominator else 0.0
                    rec.settlement_below = rec.settlement_test * (ratio ** 2)
                except ZeroDivisionError:
                    rec.settlement_below = 0.0
            else:
                rec.settlement_below = 0.0
  


    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.plate_load_visible = False
          
            
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
                if sample.internal_id == "261b79c2-47c9-4662-9298-6230145555fd":
                    record.plate_load_visible = True
                
               
               



    def open_eln_page(self):
        # import wdb; wdb.set_trace()

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
        record = super(PlateLoad, self).create(vals)
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
        record = self.env['mechanical.plate.test1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values




class PlateLoadLine(models.Model):
    _name = "mechanical.plate.test.line"
    parent_id = fields.Many2one('mechanical.plate.test1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

   
    applied_pressure = fields.Float(string="Applied Pressure kg/cm2",digits=(12,1))
    load_plate = fields.Float(string="Load on  Plate",digits=(12,2),compute="_compute_load_plate",store=True)
    pressure_plate = fields.Float(string="Pressure under Plate (T/m²)",digits=(12,2),compute="_compute_pressure_plate",store=True)
    time = fields.Float(string="Time",digits=(12,2))

    d1 = fields.Float(string="D1",digits=(12,2))
    d2 = fields.Float(string="D2",digits=(12,2))
    d3 = fields.Float(string="D3",digits=(12,2))
    d4 = fields.Float(string="D4",digits=(12,2))

    avg_sett = fields.Float(string="Average Settlement mm",digits=(12,3),compute='_compute_avg_sett',store=True)
    cumulative_sett1 = fields.Float(string="Cumulative Settlement",digits=(12,3))

    @api.depends('applied_pressure', 'parent_id.ram_area')
    def _compute_load_plate(self):
        for line in self:
            if line.applied_pressure and line.parent_id.ram_area:
                line.load_plate = (line.applied_pressure * line.parent_id.ram_area) / 1000
            else:
                line.load_plate = 0.0

    @api.depends(
    'load_plate',
    'parent_id.lenght_plate',
    'parent_id.width_plate'
    )
    def _compute_pressure_plate(self):
        for line in self:
            area = line.parent_id.lenght_plate * line.parent_id.width_plate
            if line.load_plate and area:
                line.pressure_plate = line.load_plate / area
            else:
                line.pressure_plate = 0.0

    # 🔹 COMPUTE METHOD
    @api.depends('d1', 'd2', 'd3', 'd4')
    def _compute_avg_sett(self):
        for rec in self:
            values = [rec.d1, rec.d2, rec.d3, rec.d4]
            valid = [v for v in values if v not in (None, False)]

            if valid:
                rec.avg_sett = sum(valid) / len(valid)
            else:
                rec.avg_sett = 0.0
    @api.depends(
        'd1', 'd2', 'd3', 'd4', 'applied_pressure',
        'parent_id.child_lines_plate_load.d1',
        'parent_id.child_lines_plate_load.d2',
        'parent_id.child_lines_plate_load.d3',
        'parent_id.child_lines_plate_load.d4',
        'parent_id.child_lines_plate_load.applied_pressure'
    )
    def _compute_avg_sett(self):
        for rec in self:
            rec.avg_sett = 0.0

            # avg फक्त applied_pressure line वर
            if not rec.parent_id or not rec.applied_pressure:
                continue

            # All lines sorted
            lines = rec.parent_id.child_lines_plate_load.sorted(
                key=lambda l: l.sr_no
            )

            if not lines:
                continue

            # Applied pressure lines BEFORE current line
            prev_pressure_lines = lines.filtered(
                lambda l: l.applied_pressure and l.sr_no < rec.sr_no
            )

            # 🔹 Reference line
            if prev_pressure_lines:
                # Just previous applied_pressure line
                base = prev_pressure_lines[-1]
            else:
                # First applied_pressure → base = first row (0 load)
                base = lines[0]

            diffs = [
                (rec.d1 or 0.0) - (base.d1 or 0.0),
                (rec.d2 or 0.0) - (base.d2 or 0.0),
                (rec.d3 or 0.0) - (base.d3 or 0.0),
                (rec.d4 or 0.0) - (base.d4 or 0.0),
            ]

            rec.avg_sett = round(sum(diffs) / 4, 3)

    

    
    









        @api.onchange('applied_pressure')
        def _onchange_applied_pressure_copy_previous(self):
            for rec in self:
                if not rec.parent_id or not rec.applied_pressure:
                    return

                # Get immediate previous line based on sr_no
                prev_line = rec.parent_id.child_lines_plate_load.filtered(
                    lambda l: l.sr_no < rec.sr_no
                ).sorted(key=lambda l: l.sr_no, reverse=True)[:1]

                if prev_line:
                    rec.d1 = prev_line.d1
                    rec.d2 = prev_line.d2
                    rec.d3 = prev_line.d3
                    rec.d4 = prev_line.d4



   
    

    # @api.depends('d1', 'd2', 'd3', 'd4')
    # def _compute_avg_sett(self):
    #     for rec in self:
    #         values = [rec.d1, rec.d2, rec.d3, rec.d4]
    #         non_empty = [v for v in values if v is not None]
    #         rec.avg_sett = sum(non_empty) / len(non_empty) if non_empty else 0.0

   




    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(PlateLoadLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1

class UnLoadLine(models.Model):
    _name = "mechanical.unload.test.line1"
    parent_id = fields.Many2one('mechanical.plate.test1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

   
    applied_pressure1 = fields.Float(string="Applied Pressure kg/cm2",digits=(12,1),compute="_compute_unload_line_values")
    load_plate1 = fields.Float(string="Load on  Plate",digits=(12,2),compute="_compute_unload_line_values")
    pressure_plate1 = fields.Float(string="Pressure under Plate (T/m²)",digits=(12,2))
    time1 = fields.Float(string="Time",digits=(12,2))

    d11 = fields.Float(string="D1",digits=(12,2))
    d22 = fields.Float(string="D2",digits=(12,2))
    d33 = fields.Float(string="D3",digits=(12,2))
    d44 = fields.Float(string="D4",digits=(12,2))

    avg_sett1 = fields.Float(string="Average Settlement mm",digits=(12,2),compute="_compute_avg_sett1",store=True)
    cumulative_sett11 = fields.Float(string="Cumulative Settlement",digits=(12,3))

    @api.depends('d11', 'd22', 'd33', 'd44')
    def _compute_avg_sett1(self):
        for rec in self:
            values = [rec.d11, rec.d22, rec.d33, rec.d44]
            valid = [v for v in values if v not in (None, False)]
            rec.avg_sett1 = sum(valid) / len(valid) if valid else 0.0

   
    

    
    @api.depends(
    'parent_id.child_lines_plate_load.applied_pressure',
    'parent_id.child_lines_plate_load.load_plate',
    'parent_id.child_lines_plate_load.pressure_plate',
    'parent_id.child_lines_plate_unload.sr_no'
    )
    def _compute_unload_line_values(self):
        for line in self:
            line.applied_pressure1 = 0.0
            line.load_plate1 = 0.0
            line.pressure_plate1 = 0.0

            parent = line.parent_id
            if not parent:
                continue

            # 🔹 SAME: sort by applied_pressure DESCENDING
            load_lines = sorted(
                [l for l in parent.child_lines_plate_load if l.applied_pressure],
                key=lambda l: l.applied_pressure,
                reverse=True
            )

            # ❌ DO NOT SKIP highest value
            # (removed load_lines = load_lines[1:])

            # 🔹 SAME: unload lines by sr_no
            unload_lines = list(
                parent.child_lines_plate_unload.sorted(
                    key=lambda l: l.sr_no or 0
                )
            )

            # 🔹 SAME mapping logic
            for idx, ul in enumerate(unload_lines):
                if ul.id != line.id:
                    continue

                if idx < len(load_lines):
                    match = load_lines[idx]
                    line.applied_pressure1 = match.applied_pressure or 0.0
                    line.load_plate1 = match.load_plate or 0.0
                    line.pressure_plate1 = match.pressure_plate or 0.0
                break







    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(UnLoadLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class LoadAndCumilitiveLine(models.Model):
    _name = "mechanical.load.cumilitive.line1"
    parent_id = fields.Many2one('mechanical.plate.test1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

   
   
    pressure_plate2 = fields.Float(string="Pressure under Plate (T/m²)",digits=(12,2),compute="_compute_pressure_line_values")
  
    cumulative_sett2 = fields.Float(string="Cumulative Settlement",digits=(12,3),compute="_compute_pressure_line_values")

   
    

   

    @api.depends(
        'parent_id.child_lines_plate_load.pressure_plate',
        'parent_id.child_lines_plate_load.cumulative_sett1',
        'parent_id.child_lines_loadand_cumilitive.sr_no'
    )
    def _compute_pressure_line_values(self):
        for line in self:
            line.pressure_plate2 = 0.0
            line.cumulative_sett2 = 0.0

            parent = line.parent_id
            if not parent:
                continue

            # Sort plate load lines by applied_pressure or sr_no
            plate_lines = sorted(
                [pl for pl in parent.child_lines_plate_load if pl.pressure_plate or pl.cumulative_sett1],
                key=lambda l: l.sr_no or 0
            )

            # Sort current cumulative lines by sr_no
            cumulative_lines = list(parent.child_lines_loadand_cumilitive.sorted(key=lambda l: l.sr_no or 0))

            if line in cumulative_lines:
                idx = cumulative_lines.index(line)
                if idx == 0:
                    line.pressure_plate2 = 0.0
                    line.cumulative_sett2 = 0.0
                elif idx - 1 < len(plate_lines):
                    source = plate_lines[idx - 1]
                    line.pressure_plate2 = source.pressure_plate or 0.0
                    line.cumulative_sett2 = source.cumulative_sett1 or 0.0




    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(LoadAndCumilitiveLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class LoadAndCumilitiveLine1(models.Model):
    _name = "mechanical.load.cumilitive.line2"
    parent_id = fields.Many2one('mechanical.plate.test1',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

   
   
    pressure_plate3 = fields.Float(string="Applied  load in T/m2",digits=(12,2),compute="_compute_pressure_line_values1")
  
    settlement3 = fields.Float(string="Settlement in mm",digits=(12,3),compute="_compute_pressure_line_values1")

   

    @api.depends(
        'parent_id.child_lines_plate_load.pressure_plate',
        'parent_id.child_lines_plate_load.cumulative_sett1',
        'parent_id.child_lines_loadand_cumilitive1.sr_no'
    )
    def _compute_pressure_line_values1(self):
        for line in self:
            line.pressure_plate3 = 0.0
            line.settlement3 = 0.0

            parent = line.parent_id
            if not parent:
                continue

            # Get valid load lines
            plate_lines = [
                pl for pl in parent.child_lines_plate_load
                if pl.pressure_plate or pl.cumulative_sett1
            ]

            # Sort ascending
            asc_lines = sorted(plate_lines, key=lambda l: l.pressure_plate or 0.0)
            # Mirror (excluding peak)
            desc_lines = list(reversed(asc_lines[:-1]))
            combined_lines = asc_lines + desc_lines  # Final pattern

            # Sort cumilitive lines by sr_no
            cumulative_lines = list(parent.child_lines_loadand_cumilitive1.sorted(key=lambda l: l.sr_no or 0))

            if line in cumulative_lines:
                idx = cumulative_lines.index(line)

                if idx == 0:
                    # First line always 0
                    line.pressure_plate3 = 0.0
                    line.settlement3 = 0.0
                elif idx - 1 < len(combined_lines):
                    # Fetch values starting from 2nd line (index 1)
                    source = combined_lines[idx - 1]
                    line.pressure_plate3 = source.pressure_plate or 0.0
                    line.settlement3 = source.cumulative_sett1 or 0.0





    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(LoadAndCumilitiveLine1, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1




class plateloadNotes(models.Model):
    _name = "plateload.notes"

    parent_id = fields.Many2one('mechanical.plate.test1',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")





