from odoo import models , fields,api
import json
import base64
import qrcode
from odoo.tools.float_utils import float_round
import io
import numpy as np
from io import BytesIO
from lxml import etree
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import math
from scipy.interpolate import CubicSpline , interp1d , Akima1DInterpolator
from scipy.optimize import minimize_scalar

from matplotlib.ticker import LogLocator, MultipleLocator
from matplotlib.ticker import AutoMinorLocator
from scipy.interpolate import CubicSpline , interp1d , Akima1DInterpolator
from matplotlib.ticker import MultipleLocator, StrMethodFormatter


from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import io
import base64



class DLCReport(models.AbstractModel):
    _name = 'report.dlc.dlc_report'
    _description = 'Dry Lean Concrete Report '
    
    @api.model
    def _get_report_values(self, docids, data):
        # eln = self.env['lerm.eln'].sudo().browse(docids)
        inreport_value = data.get('inreport', None)
        nabl = data.get('nabl')
        fromEln = data.get('fromEln')
        if data.get('report_wizard') == True:
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['sample'])])
        elif fromEln == False:
            if 'active_id' in data['context']:
                eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
            else:
                eln = self.env['lerm.eln'].sudo().browse(docids)
        else:
            if 'active_id' in data['context']:
                eln = self.env['lerm.eln'].sudo().search([('id','=',data['context']['active_id'])])
            else:
                eln = self.env['lerm.eln'].sudo().browse(docids)

        qr_static = qrcode.QRCode(box_size=6, border=2)
        qr_static.add_data("https://www.lerm.in")
        qr_static.make(fit=True)
        buf_static = BytesIO()
        qr_static.make_image(fill_color="black", back_color="white").save(buf_static, format="PNG")
        qr_static_b64 = base64.b64encode(buf_static.getvalue()).decode()

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(eln.kes_no)
        qr.make(fit=True)
        qr_image = qr.make_image()

        # Convert the QR code image to base64 string
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_image_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Assign the base64 string to a field in the 'srf' object
        qr_code = qr_image_base64
        model_id = eln.model_id
        # differnt location for product based
        model_name = eln.material.product_based_calculation[0].ir_model.name 
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)


        

        graph_heavy = False
        heavy_omc = 0
        heavy_mdd = 0

        if getattr(general_data, 'show_heavy_graph', False):
            result = self.generate_line_chart_light_omc(general_data)
            if result:
              graph_heavy, heavy_omc, heavy_mdd = result

        graph_light = False
        light_omc = 0
        light_mdd = 0

        if getattr(general_data, 'show_light_graph', False):
            result = self.generate_line_chart_light_omc1(general_data)
            if result:
              graph_light, light_omc, light_mdd = result

        


        
        
        return {
            'eln': eln,
            'data' : general_data,
            'qrcode': qr_code,
            'qrcode_static': qr_static_b64,
            'stamp' : inreport_value,
            'nabl' : nabl,
            'graphHeavy' : graph_heavy,
            'heavyomc' : heavy_omc,
            'heavymdd' : heavy_mdd,
            'graphlight' : graph_light,
            'lightomc' : light_omc,
            'lightmdd' : light_mdd,
        }
    

    


    def generate_line_chart_light_omc(self, data):


      x = []
      y = []

      for line in data.heavy_table:
        if line.water_content and line.dry_density:
            x.append(float(line.water_content))
            y.append(float(line.dry_density))

      if len(x) < 3:
        return False

    # ---------------------------------------
    # Sort Data
    # ---------------------------------------
      data_points = sorted(zip(x, y))

      x = np.array([i[0] for i in data_points], dtype=float)
      y = np.array([i[1] for i in data_points], dtype=float)

      omc = float(data.omc)
      mdd = float(data.max_dry_density)

    # ---------------------------------------
    # Create parabola through
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

      fig, ax = plt.subplots(figsize=(15,5))

      ax.plot(
        x_smooth,
        y_smooth,
        color="blue",
        linewidth=2.8,
        zorder=2
    )

      ax.scatter(
        x,
        y,
        color="red",
        s=45,
        zorder=5
    )

      ax.scatter(
        omc,
        mdd,
        color="red",
        s=160,
        zorder=10
    )

      ax.axhline(
        y=mdd,
        color="red",
        linestyle="--",
        linewidth=1
    )

      ax.axvline(
        x=omc,
        color="red",
        linestyle="--",
        linewidth=1
    )

      ax.text(
        omc + 0.15,
        mdd + 0.002,
        f"OMC: {omc:.2f}%\nMDD: {mdd:.2f}",
        fontsize=12,
        color="red",
        fontweight="bold"
    )

      ax.set_xlabel(
        "Water Content (%)",
        fontsize=16
    )

      ax.set_ylabel(
        "Dry Density (g/cc)",
        fontsize=16
    )

      ax.set_title(
        "DETERMINATION OF COMPACTION OMC / MDD",
        fontsize=22
    )

      ax.set_xlim(
        0,
        max(x) + 2
    )

      ymin = min(min(y), min(y_smooth))
      ymax = max(max(y), max(y_smooth), mdd)
 
      ax.set_ylim(
        ymin - 0.02,
        ymax + 0.03
    )

    # ---------------------------------------
    # Graph Paper
    # ---------------------------------------

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

      plt.close(fig)

      buffer.seek(0)

      image_data = base64.b64encode(
        buffer.read()
    ).decode("utf-8")

      return (
        image_data,
        round(omc, 2),
        round(mdd, 2)
    )

    def generate_line_chart_light_omc1(self, data):


      x = []
      y = []

      for line in data.omc_table:
        if line.water_content1 and line.dry_density1:
            x.append(float(line.water_content1))
            y.append(float(line.dry_density1))

      if len(x) < 3:
        return False

    # ---------------------------------------
    # Sort Data
    # ---------------------------------------
      data_points = sorted(zip(x, y))

      x = np.array([i[0] for i in data_points], dtype=float)
      y = np.array([i[1] for i in data_points], dtype=float)

      omc = float(data.omc1)
      mdd = float(data.max_dry_density1)

    # ---------------------------------------
    # Create parabola through
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

      fig, ax = plt.subplots(figsize=(15,5))

      ax.plot(
        x_smooth,
        y_smooth,
        color="blue",
        linewidth=2.8,
        zorder=2
    )

      ax.scatter(
        x,
        y,
        color="red",
        s=45,
        zorder=5
    )

      ax.scatter(
        omc,
        mdd,
        color="red",
        s=160,
        zorder=10
    )

      ax.axhline(
        y=mdd,
        color="red",
        linestyle="--",
        linewidth=1
    )

      ax.axvline(
        x=omc,
        color="red",
        linestyle="--",
        linewidth=1
    )

      ax.text(
        omc + 0.15,
        mdd + 0.002,
        f"OMC: {omc:.2f}%\nMDD: {mdd:.2f}",
        fontsize=12,
        color="red",
        fontweight="bold"
    )

      ax.set_xlabel(
        "Water Content (%)",
        fontsize=16
    )

      ax.set_ylabel(
        "Dry Density (g/cc)",
        fontsize=16
    )

      ax.set_title(
        "DETERMINATION OF COMPACTION OMC / MDD",
        fontsize=22
    )

      ax.set_xlim(
        0,
        max(x) + 2
    )

      ymin = min(min(y), min(y_smooth))
      ymax = max(max(y), max(y_smooth), mdd)
 
      ax.set_ylim(
        ymin - 0.02,
        ymax + 0.03
    )

    # ---------------------------------------
    # Graph Paper
    # ---------------------------------------

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

      plt.close(fig)

      buffer.seek(0)

      image_data = base64.b64encode(
        buffer.read()
    ).decode("utf-8")

      return (
        image_data,
        round(omc, 2),
        round(mdd, 2)
    )

   


    def generate_line_chart_slive(self, data):

        x_value = []
        y_value = []
        x_labels = []

        for line in data.sieve_analysis_child_lines:

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

        sorted_data = sorted(
        zip(x_value, y_value, x_labels),
        key=lambda x: x[0]
    )

        x_value, y_value, x_labels = zip(*sorted_data)

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.set_xscale('log')

        ax.plot(x_value,
        y_value,
        color='blue',
        linewidth=2
    )

        ax.scatter(
        x_value,
        y_value,
        color='red',
        s=60,
        zorder=5
    )

        ax.set_xlabel("Particle Size (mm)")
        ax.set_ylabel("% Passing")
        ax.set_title("Grain Size Distribution Curve")  
        ax.set_xticks(x_value)

        ax.set_xticklabels(
        x_labels,
        rotation=45,
        ha='right'
    )

        ax.xaxis.set_minor_locator(
        LogLocator(
            base=10.0,
            subs=np.arange(1, 10) * 0.1,
            numticks=100
        )
    )

        ax.yaxis.set_minor_locator(
        MultipleLocator(2)
    )

        ax.grid(
        True,
        which='both',
        linestyle='--',
        linewidth=0.4
    )

        ax.set_xlim(
        left=min(x_value) / 1.5,
        right=max(x_value) * 1.5
    )

        ax.set_ylim(0, 110)

        d_points = [
        (data.d10, 10, 'black', 'D10'),
        (data.d30, 30, 'green', 'D30'),
        (data.d60, 60, 'orange', 'D60'),
    ]

        for dx, dy, color, label in d_points:

             if dx and dx > 0:

                ax.scatter(
                dx,
                dy,
                color=color,
                s=90,
                zorder=10
            )

                ax.plot(
                [dx, dx],
                [0, dy],
                color=color,
                linewidth=1.2
            )

                ax.plot(
                [min(x_value), dx],
                [dy, dy],
                color=color,
                linewidth=1.2
            )

                ax.annotate(
                f"{label}={dx:.4f}",
                (dx, dy),
                fontsize=9
            )

        plt.tight_layout()

        buffer = io.BytesIO()

        plt.savefig(
        buffer,
        format='png',
        dpi=100,
        bbox_inches='tight'
    )

        plt.close(fig)
 
        buffer.seek(0)

        image_data = base64.b64encode(buffer.read()).decode('utf-8')

        return image_data
    


    
  

class DLCDatasheet(models.AbstractModel):
    _name = 'report.dlc.dlc_datasheet'
    _description = 'Dry Lean Concrete DataSheet '
    
    @api.model
    def _get_report_values(self, docids, data):
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
        model_id = eln.model_id
        # differnt location for product based
        # model_name = eln.material.product_based_calculation[0].ir_model.name 
        model_name = eln.material.product_based_calculation.filtered(lambda record: record.grade.id == eln.grade_id.id).ir_model.name
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        return {
            'eln': eln,
            'data' : general_data
        }