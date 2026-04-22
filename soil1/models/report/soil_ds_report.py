from odoo import models , fields,api
import json
import base64
import qrcode
from io import BytesIO
from lxml import etree
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import math
from scipy.interpolate import CubicSpline , interp1d , Akima1DInterpolator
from scipy.optimize import minimize_scalar
from matplotlib.ticker import MultipleLocator, StrMethodFormatter
import io
from matplotlib.ticker import LogLocator, MultipleLocator


class SoilDatasheet(models.AbstractModel):
    _name = 'report.soil1.soil1_datasheet'
    _description = 'Soil DataSheet SSL'
    
    @api.model
    def _get_report_values(self, docids, data):
        # if 'active_id' in data['context']:
        #     eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
        # else:
        #     eln = self.env['lerm.eln'].sudo().browse(docids) 
        if data['fromsample'] == True:
            if 'active_id' in data['context']:
                eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
            else:
                eln = self.env['lerm.eln'].sudo().browse(docids) 
        else:
            if data['report_wizard'] == True:
                eln = self.env['lerm.eln'].sudo().search([('id','=',data['eln'])])
            else:
                eln = self.env['lerm.eln'].sudo().browse(data['eln_id'])
        # differnt location for product based
        print(eln.material.parameter_table1[0].parameter_name , 'parameter')
        parameter_data = self.env['lerm.parameter.master'].sudo().search([('internal_id','=',eln.material.parameter_table1[0].internal_id)])
        model_id = eln.model_id
        model_name = eln.material.product_based_calculation[0].ir_model.name 
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        return {
            'eln': eln,
            'data' : general_data,
            'parameter' : parameter_data
        }




class SoilReport(models.AbstractModel):
    _name = 'report.soil1.soil1_report'
    _description = 'Soil Report SSL'
    
    @api.model
    def _get_report_values(self, docids, data):
        # eln = self.env['lerm.eln'].sudo().browse(docids)
        inreport_value = data.get('inreport', None)
        nabl = data.get('nabl')
        if data.get('report_wizard') == True:
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['sample'])])
        # elif 'active_id' in data['context']:
        elif 'active_id' in data.get('context', {}):
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
        else:
            eln = self.env['lerm.eln'].sudo().browse(docids)  
        # qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        # qr.add_data(eln.kes_no)
        # qr.make(fit=True)
        # qr_image = qr.make_image()
        # Static QR
        qr_static = qrcode.QRCode(box_size=6, border=2)
        qr_static.add_data("https://www.lerm.in")
        qr_static.make(fit=True)
        buf_static = BytesIO()
        qr_static.make_image(fill_color="black", back_color="white").save(buf_static, format="PNG")
        qr_static_b64 = base64.b64encode(buf_static.getvalue()).decode()

        # 🧩 QR Code तयार करा
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        report_url = f"{base_url}/download_report/soil/{'nabl' if nabl else 'nonnabl'}/{eln.id}"

        qr.add_data(report_url)
        qr.make(fit=True)
        qr_image = qr.make_image()
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()
        model_id = eln.model_id
        # differnt location for product based
        model_name = eln.material.product_based_calculation[0].ir_model.name 
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)

        # ✅ BOOLEAN CONTROL (IMPORTANT)
        graph_sieve = False
        if getattr(general_data, 'show_sieve_graph', False):
            graph_sieve = self.generate_line_chart_slive(general_data)

        graph_liquid1 = False
        if getattr(general_data, 'show_liquid_graph1', False):
            graph_liquid1 = self.action_generate_graphl(general_data)

        graph_liquid2 = False
        if getattr(general_data, 'show_liquid_graph2', False):
            graph_liquid2 = self.action_generate_cone_graph(general_data)

        graph_light1 = False
        omc = 0
        mdd = 0
        if getattr(general_data, 'show_light_graph1', False):
            result = self.action_generate_graph1(general_data)
            if result:
               graph_light1, omc, mdd = result
        
        
        graph_light2 = False
        if getattr(general_data, 'show_light_graph2', False):
            graph_light2 = self.action_generate_light1_graph_image(general_data)

        graph_heavy = False
        heavy_omc = 0
        heavy_mdd = 0

        if getattr(general_data, 'show_heavy_graph2', False):
            result = self.generate_line_chart_light_omc(general_data)
            if result:
              graph_heavy, heavy_omc, heavy_mdd = result

        graph_cbr = False
        if getattr(general_data, 'show_cbr', False):
            graph_cbr = self.action_generate_cbr_chart(general_data)

        graph_consolidation = False
        if getattr(general_data, 'show_graph_consolidation', False):
            graph_consolidation = self.action_generate_graph(general_data)

        graph_direct_shear = False
        if getattr(general_data, 'show_direct_graph', False):
            graph_direct_shear = self.action_generate_direct_graph(general_data)

        
    

        return {
            'eln': eln,
            'data' : general_data,
            'qrcode': qr_code,
            'qrcode_static': qr_static_b64,
            'stamp' : inreport_value,
            'nabl' : nabl,
            'graphSieve': graph_sieve,
            'graph_liquid1': graph_liquid1, 
            'graph_liquid2': graph_liquid2,
            'graph_light1': graph_light1, 
            'graph_light2': graph_light2,
            'omc': omc,
            'mdd': mdd,
            'graph_heavy':graph_heavy,
            'heavy_omc': heavy_omc,
            'heavy_mdd': heavy_mdd,
            'graph_cbr': graph_cbr,
            'graph_consolidation': graph_consolidation,
            'graph_direct_shear': graph_direct_shear, # ✅ Added
            
        }


    # ✅ GRAPH FUNCTION
    def generate_line_chart_slive(self, data):

        x_value = []
        y_value = []
        x_labels = []

        for line in data.sieve_analysis_child_lines:
            if line.sieve_size and line.passing_percent is not None:
                sieve_str = str(line.sieve_size).strip().lower()
                try:
                    if 'mm' in sieve_str:
                        sieve_val = float(sieve_str.replace('mm', '').strip())
                        label = f"{int(sieve_val)} mm"

                    elif 'µ' in sieve_str or 'micron' in sieve_str:
                        sieve_val = float(
                            sieve_str.replace('µ', '').replace('micron', '').strip()
                        ) / 1000
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

        # ✅ Sort data
        sorted_data = sorted(zip(x_value, y_value, x_labels))
        x_value, y_value, x_labels = zip(*sorted_data)

        plt.figure(figsize=(12, 5))
        plt.xscale('log')

        # ✅ Plot
        plt.plot(x_value, y_value, color='blue', linewidth=2)
        plt.scatter(x_value, y_value, color='red', s=50)

        plt.xlabel('Sieve Size')
        plt.ylabel('Passing %')
        plt.title('Grain Size Analysis')

        ax = plt.gca()
        plt.xticks(ticks=x_value, labels=x_labels, rotation=45)

        ax.xaxis.set_minor_locator(
            LogLocator(base=10.0, subs=np.arange(1.0, 10.0) * 0.1)
        )
        ax.yaxis.set_minor_locator(MultipleLocator(2))

        plt.grid(True, which='both', linestyle='--', linewidth=0.3)

        plt.xlim(left=min(x_value) / 1.5, right=max(x_value) * 1.5)
        plt.ylim(0, 100)

        # ✅ D10, D30, D60
        d_points = [
            (getattr(data, 'd10', None), 10, 'black'),
            (getattr(data, 'd30', None), 30, 'yellow'),
            (getattr(data, 'd60', None), 60, 'orange'),
        ]

        for dx, dy, color in d_points:
            if dx:
                plt.scatter(dx, dy, color=color, s=80)
                plt.plot([dx, dx], [0, dy], color=color)
                plt.plot([0, dx], [dy, dy], color=color)

        # ✅ Convert to base64
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode('utf-8')
    


    def action_generate_graphl(self, data):

     import numpy as np
     import matplotlib.pyplot as plt
     from matplotlib.ticker import LogLocator, ScalarFormatter, MultipleLocator
     import io
     import base64

     blows = np.array([float(l.blows or 0) for l in data.water_line_ids])
     water = np.array([float(l.water_content or 0) for l in data.water_line_ids])

     mask = (blows > 0) & (water > 0)
     blows = blows[mask]
     water = water[mask]

     if len(blows) < 2:
        return False

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

     x_min = max(1, min(blows)*0.8)
     x_max = max(blows)*1.5
     ax.set_xlim(x_min, x_max)

     y_min = min(water) - 2
     y_max = max(water) + 2
     ax.set_ylim(y_min, y_max)

    # Grid
     ax.xaxis.set_major_locator(LogLocator(base=10))
     ax.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10)*0.1))

     ax.yaxis.set_major_locator(MultipleLocator(1))
     ax.yaxis.set_minor_locator(MultipleLocator(0.5))

     ax.grid(which='major', linewidth=1, color='black')
     ax.grid(which='minor', linewidth=0.5, color='gray')

    # Excel-like ticks
     xticks = sorted(set([10, 15, 18, 20, 22, 25, 30, 40, 50, 100] + list(blows.astype(int))))
     xticks = [x for x in xticks if x_min <= x <= x_max]

     ax.set_xticks(xticks)
     ax.get_xaxis().set_major_formatter(ScalarFormatter())
     ax.ticklabel_format(style='plain', axis='x')

    # Fit line
     ax.plot(x_smooth, y_smooth, color='orange', linewidth=2)

    # Points
     for i, (x, y) in enumerate(zip(blows, water)):
        ax.scatter(x, y, color='#1f77b4', s=80, edgecolors='black', zorder=6)
        offset = 0.5 if y < (y_max - 1) else -0.5
        ax.text(x, y + offset, f"P{i+1}", fontsize=8, ha='center')

    # Liquid Limit (25 blows)
     ll_x = 25
     ll_y = float(fit(np.log10(ll_x)))

     if x_min < ll_x < x_max:
        ax.axvline(ll_x, color='#2c6db2', linewidth=2)

     if y_min < ll_y < y_max:
        ax.axhline(ll_y, color='#6aa84f', linewidth=2)

     ax.scatter(ll_x, ll_y, color='#2c6db2', s=120, zorder=10)

     ax.set_title("LIQUID LIMIT TEST GRAPH (CASAGRANDE)")
     ax.set_xlabel("No. of Blows")
     ax.set_ylabel("Water Content (%)")

    # Save
     buffer = io.BytesIO()
     plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
     plt.close()
     buffer.seek(0)

     return base64.b64encode(buffer.read()).decode('utf-8')
    

    def action_generate_cone_graph(self, data):

     import numpy as np
     import matplotlib.pyplot as plt
     import io
     import base64

    # -------------------------------
    # DATA
    # -------------------------------
     blows = []
     water = []

     for l in data.water_line_ids:
        if l.blows and l.water_content > 0:
            blows.append(float(l.blows))
            water.append(float(l.water_content))

     blows = np.array(blows)
     water = np.array(water)

     if len(blows) < 2:
        return False

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

    # Grid
     ax.grid(which='major', linewidth=1)
     ax.minorticks_on()
     ax.grid(which='minor', linewidth=0.5)

    # Dynamic axis
     x_min = min(blows)
     x_max = max(blows)
     y_min = min(water)
     y_max = max(water)

     ax.set_xlim(x_min - 5, x_max + 5)
     ax.set_ylim(y_min - 2, y_max + 2)

     ax.margins(x=0.1, y=0.1)

    # Line
     ax.plot(x_smooth, y_smooth, color='black', linewidth=1.5, zorder=2)

    # Points
     ax.scatter(blows, water,
               color='blue',
               s=70,
               edgecolors='black',
               zorder=5)

    # Labels
     ax.set_title("LIQUID LIMIT GRAPH (CONE PENETRATION)", fontsize=14)
     ax.set_xlabel("NO. BLOWS")
     ax.set_ylabel("WATER CONTENT (%)")

    # Save
     buffer = io.BytesIO()
     plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
     plt.close()
     buffer.seek(0)

     return base64.b64encode(buffer.read()).decode('utf-8')
    

    def action_generate_graph1(self, data):

      import numpy as np
      import matplotlib.pyplot as plt
      from scipy.interpolate import PchipInterpolator
      import io, base64

      x = []
      y = []

      # -----------------------------
      # COLLECT DATA
      # -----------------------------
      for line in data.light_line_ids:
          if line.water_content and line.dry_density:
              x.append(float(line.water_content))
              y.append(float(line.dry_density))

      if len(x) < 3:
          return False, 0, 0

      # -----------------------------
      # SORT
      # -----------------------------
      data_sorted = sorted(zip(x, y))
      x, y = zip(*data_sorted)
  
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
 
      # -----------------------------
      # GRAPH
      # -----------------------------
      plt.figure(figsize=(12, 5))

      plt.plot(x_smooth, y_smooth, color='blue', linewidth=2)
      plt.scatter(x, y, color='orange', s=60)

      plt.axvline(x=omc, color='black', linewidth=2)
      plt.axhline(y=mdd, color='black', linewidth=2)

      plt.scatter([omc], [mdd], color='black', s=70)

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
      # SAVE
      # -----------------------------
      buffer = io.BytesIO()
      plt.savefig(buffer, format='png', dpi=120)
      plt.close()
      buffer.seek(0)

      image = base64.b64encode(buffer.read()).decode('utf-8')

      return image, round(omc, 2), round(mdd, 3)
    

    def action_generate_light1_graph_image(self, data):

      import numpy as np
      import matplotlib.pyplot as plt
      from scipy.interpolate import PchipInterpolator
      from scipy.ndimage import gaussian_filter1d
      import io, base64

      x = []
      y = []

      # -----------------------------
      # COLLECT DATA
      # -----------------------------
      for line in data.light_line_ids:
          if line.water_content and line.dry_density:
              x.append(float(line.water_content))
              y.append(float(line.dry_density))

      if len(x) < 3:
          return False

      # -----------------------------
      # SORT
      # -----------------------------
      data_sorted = sorted(zip(x, y))
      x, y = zip(*data_sorted)

      x = np.array(x, dtype=float)
      y = np.array(y, dtype=float)

      # -----------------------------
      # INTERPOLATION
      # -----------------------------
      interp = PchipInterpolator(x, y)

      x_smooth = np.linspace(min(x), max(x), 300)
      y_smooth = interp(x_smooth)

      # -----------------------------
      # SMOOTHING
      # -----------------------------
      y_smooth = gaussian_filter1d(y_smooth, sigma=1.2)

      # -----------------------------
      # FIX FIRST SEGMENT (KINK FIX)
      # -----------------------------
      if len(x) > 1:
          x1, x2 = x[0], x[1]
          mask = (x_smooth >= x1) & (x_smooth <= x2)

          y_start = y[0]
          y_end = y[1]

          t = (x_smooth[mask] - x1) / (x2 - x1)
          y_smooth[mask] = y_start + (y_end - y_start) * (3*t**2 - 2*t**3)

      # -----------------------------
      # GRAPH
      # -----------------------------
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

      # -----------------------------
      # SAVE
      # -----------------------------
      buffer = io.BytesIO()
      plt.savefig(buffer, format='png', dpi=100)
      plt.close()
      buffer.seek(0)

      return base64.b64encode(buffer.read()).decode('utf-8')
    


    def generate_line_chart_light_omc(self, data):

      import numpy as np
      import matplotlib.pyplot as plt
      from scipy.interpolate import make_interp_spline
      from matplotlib.ticker import MultipleLocator
      import io, base64

      x = []
      y = []

      # -------------------------------
      # DATA
      # -------------------------------
      for line in data.heavy_line_ids:
          if line.water_content and line.dry_density:
            x.append(float(line.water_content))
            y.append(float(line.dry_density))

      if len(x) < 3:
        return False, 0, 0

      x = np.array(x)
      y = np.array(y)

      # Sort
      idx = np.argsort(x)
      x = x[idx]
      y = y[idx]

      # -------------------------------
      # PARABOLA (OMC/MDD)
      # -------------------------------
      coeffs = np.polyfit(x, y, 2)
      a, b, c = coeffs

      if a < 0:
        max_x = -b / (2 * a)
        max_y = a * max_x**2 + b * max_x + c
      else:
        max_y = float(np.max(y))
        max_x = float(x[np.argmax(y)])

      # -------------------------------
      # ADD PEAK INTO DATA
      # -------------------------------
      x_aug = np.append(x, max_x)
      y_aug = np.append(y, max_y)

      idx = np.argsort(x_aug)
      x_aug = x_aug[idx]
      y_aug = y_aug[idx]

      # -------------------------------
      # SPLINE
      # -------------------------------
      x_smooth = np.linspace(min(x_aug), max(x_aug), 300)
      spline = make_interp_spline(x_aug, y_aug, k=2)
      y_smooth = spline(x_smooth)

      # -------------------------------
      # GRAPH
      # -------------------------------
      plt.figure(figsize=(10, 5))

      plt.plot(x_smooth, y_smooth, color='blue', linewidth=2)
      plt.scatter(x, y, color='orange', s=50)

      plt.axhline(y=max_y, color='black')
      plt.axvline(x=max_x, color='black')

      plt.scatter(max_x, max_y, color='black')

      ax = plt.gca()
      ax.xaxis.set_minor_locator(MultipleLocator(0.2))
      ax.yaxis.set_minor_locator(MultipleLocator(0.01))

      plt.grid(which='major', color='black', linewidth=0.6)
      plt.grid(which='minor', color='green', linestyle='--', linewidth=0.3)

      plt.xlim(min(x) - 0.5, max(x) + 1)
      plt.ylim(min(y) - 0.05, max(y) + 0.05)

      plt.title("MODIFIED PROCTOR TEST")
      plt.xlabel("Optimum Moisture Content (%)")
      plt.ylabel("Maximum Dry Density (gm/cc)")

      plt.tight_layout()

      # -------------------------------
      # SAVE
      # -------------------------------
      buffer = io.BytesIO()
      plt.savefig(buffer, format='png', dpi=120)
      plt.close()
      buffer.seek(0)

      image = base64.b64encode(buffer.read()).decode('utf-8')

      return image, round(max_x, 2), round(max_y, 3)
    



    def action_generate_cbr_chart(self, data):

      import matplotlib.pyplot as plt
      from matplotlib.ticker import AutoMinorLocator
      import io, base64

      # -------------------------------
      # FETCH DATA
      # -------------------------------
      lines = self.env['california.bearing.test'].search([
        ('parent_id', '=', data.id)
    ], order='penetration asc')

      penetration = [l.penetration for l in lines]

      s1 = [l.sample1_load for l in lines]
      s2 = [l.sample2_load for l in lines]
      s3 = [l.sample3_load for l in lines]

      if not penetration:
          return False

      # -------------------------------
      # GRAPH
      # -------------------------------
      plt.figure(figsize=(12, 5))

      plt.plot(penetration, s1, marker='o', label='Sample-1')
      plt.plot(penetration, s2, marker='o', label='Sample-2')
      plt.plot(penetration, s3, marker='o', label='Sample-3')

      plt.xlabel('Penetration (mm)')
      plt.ylabel('Load (Kg/cm²)')
      plt.title('CBR Test Graph')

      # Major grid
      plt.grid(which='major', linestyle='-', linewidth=0.8)

      # Minor grid
      ax = plt.gca()
      ax.xaxis.set_minor_locator(AutoMinorLocator(5))
      ax.yaxis.set_minor_locator(AutoMinorLocator(5))
      plt.grid(which='minor', linestyle=':', linewidth=0.5)

      plt.legend()

      # -------------------------------
      # SAVE
      # -------------------------------
      buffer = io.BytesIO()
      plt.savefig(buffer, format='png', bbox_inches='tight')
      plt.close()
      buffer.seek(0)

      return base64.b64encode(buffer.read()).decode('utf-8')
    
    def action_generate_graph(self, data):

      import matplotlib.pyplot as plt
      import io, base64

      x_vals = []
      y_vals = []

      # -------------------------------
      # DATA
      # -------------------------------
      for line in data.consolidation_three_line_ids:
          if line.sqrt_t and line.int_pressure:
              if line.sqrt_t > 0:  # remove zero
                  x_vals.append(float(line.sqrt_t))
                  y_vals.append(float(line.int_pressure))

      if not x_vals:
          return False

      # -------------------------------
      # GRAPH
      # -------------------------------
      plt.figure(figsize=(11, 5))

      plt.plot(x_vals, y_vals, marker='o')

      plt.xlabel("√t")
      plt.ylabel("Dial Reading (8 kg/cm²)")
      plt.title("Consolidation Graph")

      # Log scale
      plt.xscale('log')

      # Fix left gap
      min_x = min(x_vals)
      plt.xlim(left=min_x * 0.8)

      # Grid
      plt.grid(True, which='both', linestyle='--', linewidth=0.5)

      plt.tight_layout()

      # -------------------------------
      # SAVE
      # -------------------------------
      buffer = io.BytesIO()
      plt.savefig(buffer, format='png')
      plt.close()
      buffer.seek(0)

      return base64.b64encode(buffer.read()).decode('utf-8')
    

    def action_generate_direct_graph(self, data):

      import numpy as np
      import matplotlib.pyplot as plt
      import io, base64

      # -------------------------------
      # DATA
      # -------------------------------
      x = np.array([
        data.normal_stress_0_5,
        data.normal_stress_1_0,
        data.normal_stress_1_5
    ], dtype=float)

      y = np.array([
        data.shear_ton_0_5,
        data.shear_ton_1_0,
        data.shear_ton_1_5
    ], dtype=float)

      # Remove invalid values
      mask = (x > 0) & (y > 0)
      x = x[mask]
      y = y[mask]
  
      if len(x) < 2:
          return False

      # -------------------------------
      # LINE (Mohr-Coulomb)
      # -------------------------------
      m = float(data.tan_phi or 0)
      c = float(data.cohesion or 0)

      # -------------------------------
      # GRAPH
      # -------------------------------
      plt.figure(figsize=(8, 5))

      # Scatter points
      plt.scatter(x, y, color='blue')

      # Main line
      x_line = np.linspace(0, max(x) + 5, 100)
      y_line = m * x_line + c
      plt.plot(x_line, y_line, color='red', label='Failure Envelope')

      # Back dotted line
      x_back = np.linspace(0, min(x), 50)
      y_back = m * x_back + c
      plt.plot(x_back, y_back, linestyle='dotted', color='blue')

      # Labels
      plt.title("DIRECT SHEAR TEST GRAPH")
      plt.xlabel("Normal Stress (Ton/m²)")
      plt.ylabel("Max Shear Stress (Ton/m²)")

      plt.xlim(0, max(x) + 5)
      plt.ylim(0, max(y) + 2)

      # Grid
      plt.minorticks_on()
      plt.grid(which='major', color='green', linewidth=0.5)
      plt.grid(which='minor', color='green', linewidth=0.2)

      plt.legend()
      plt.tight_layout()

      # -------------------------------
      # SAVE
      # -------------------------------
      buffer = io.BytesIO()
      plt.savefig(buffer, format='png')
      plt.close()
      buffer.seek(0)

      return base64.b64encode(buffer.read()).decode('utf-8')
  
