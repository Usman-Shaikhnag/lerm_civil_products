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



class GsbReport1(models.AbstractModel):
    _name = 'report.gsb.gsb_mec_report'
    _description = 'GSB Report '


    @api.model
    def _get_report_values(self, docids, data=None):
      data = data or {}
      inreport_value = data.get('inreport', None)
      nabl = data.get("nabl", False)

        # ✅ ELN Fetch
      if data.get("report_wizard"):
            eln = (
                self.env["lerm.eln"]
                .sudo()
                .search([("sample_id", "=", data.get("sample"))], limit=1)
            )
      elif data.get("context", {}).get("active_id"):
            eln = (
                self.env["lerm.eln"]
                .sudo()
                .search([("sample_id", "=", data["context"]["active_id"])], limit=1)
            )
      else:
            eln = self.env["lerm.eln"].sudo().browse(docids)

      if not eln or not eln.exists():
            raise ValueError("ELN record not found")

        # ✅ LAB FETCH
      lab = eln.sample_id.lab_location if eln.sample_id else False

        # ✅ QR LINK 
      qr_link = lab.nabl_scope_link or ""

      qrcode_static = False  
      if qr_link:
            # 🔳 QR Generate 
            qr = qrcode.QRCode(box_size=6, border=2)
            qr.add_data(qr_link)
            qr.make(fit=True)

            buffer = BytesIO()
            qr.make_image(fill_color="black", back_color="white").save(
                buffer, format="PNG"
            )
            qrcode_static = base64.b64encode(buffer.getvalue()).decode()

        # Odoo Report Download QR Code
      qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
      base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
      report_url = f"{base_url}/download_report/gsb/{'nabl' if nabl else 'nonnabl'}/{eln.id}"

      qr.add_data(report_url)
      qr.make(fit=True)
      qr_image = qr.make_image()
      buffered = BytesIO()
      qr_image.save(buffered, format="PNG")
      qr_code = base64.b64encode(buffered.getvalue()).decode()

        # ✅ General Data मिळवा
      model_id = eln.model_id
      model_name = (
            eln.material.product_based_calculation[0].ir_model.name
            if eln.material.product_based_calculation
            else False
        )
      if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
      else:
            general_data = self.env["lerm.eln"].sudo().browse(docids)

      graph_liquid = False
      if getattr(general_data, 'show_liquid_graph', False):
            graph_liquid = self.generate_line_chart_liquid(general_data)

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

      graph_cbr = False
      if getattr(general_data, 'show_cbr', False):
            graph_cbr = self.generate_cbr_chart(general_data)


        
        
      return {
            'eln': eln,
            'data' : general_data,
            'qrcode': qr_code,
            'qrcode_static': qrcode_static,
            'stamp' : inreport_value,
            'nabl' : nabl,
            'graphliquid': graph_liquid,  
            'graphHeavy' : graph_heavy,
            'heavyomc' : heavy_omc,
            'heavymdd' : heavy_mdd,
            'graphlight' : graph_light,
            'lightomc' : light_omc,
            'lightmdd' : light_mdd,
            'graphcbr' : graph_cbr,
        }
    
    # @api.model
    # def _get_report_values(self, docids, data):
    #     # eln = self.env['lerm.eln'].sudo().browse(docids)
    #     inreport_value = data.get('inreport', None)
    #     nabl = data.get('nabl')
    #     fromEln = data.get('fromEln')
    #     if data.get('report_wizard') == True:
    #         eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['sample'])])
    #     elif fromEln == False:
    #         if 'active_id' in data['context']:
    #             eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
    #         else:
    #             eln = self.env['lerm.eln'].sudo().browse(docids)
    #     else:
    #         if 'active_id' in data['context']:
    #             eln = self.env['lerm.eln'].sudo().search([('id','=',data['context']['active_id'])])
    #         else:
    #             eln = self.env['lerm.eln'].sudo().browse(docids)

    #     qr_static = qrcode.QRCode(box_size=6, border=2)
    #     qr_static.add_data("https://www.lerm.in")
    #     qr_static.make(fit=True)
    #     buf_static = BytesIO()
    #     qr_static.make_image(fill_color="black", back_color="white").save(buf_static, format="PNG")
    #     qr_static_b64 = base64.b64encode(buf_static.getvalue()).decode()

    #     qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    #     qr.add_data(eln.kes_no)
    #     qr.make(fit=True)
    #     qr_image = qr.make_image()

    #     # Convert the QR code image to base64 string
    #     buffered = BytesIO()
    #     qr_image.save(buffered, format="PNG")
    #     qr_image_base64 = base64.b64encode(buffered.getvalue()).decode()

    #     # Assign the base64 string to a field in the 'srf' object
    #     qr_code = qr_image_base64
    #     model_id = eln.model_id
    #     # differnt location for product based
    #     model_name = eln.material.product_based_calculation[0].ir_model.name 
    #     if model_name:
    #         general_data = self.env[model_name].sudo().browse(model_id)
    #     else:
    #         general_data = self.env['lerm.eln'].sudo().browse(docids)


        
    

    def generate_cbr_chart(self, data):

    #   lines = self.env['gsb.cbr.line'].search(
    #     [('parent_id', '=', data.id)],
    #     order='penetration asc'
    # )

      lines = data.sudo().soil_table

      import io
      import base64
      import matplotlib.pyplot as plt
      from matplotlib.ticker import AutoMinorLocator

    #   lines = data.mechanical_cbr_line_ids.sorted(
    #     key=lambda r: r.penetration or 0
    # )

      penetration = [l.penetration for l in lines]

      s1 = [l.sample1_load for l in lines]
      s2 = [l.sample2_load for l in lines]
      s3 = [l.sample3_load for l in lines]

      if not penetration:
        return False

      fig, ax = plt.subplots(figsize=(12, 5))

      ax.plot(
        penetration,
        s1,
        marker='o',
        label='Sample-1'
    )

      ax.plot(
        penetration,
        s2,
        marker='o',
        label='Sample-2'
    )

      ax.plot(
        penetration,
        s3,
        marker='o',
        label='Sample-3'
    )

      ax.set_xlabel('Penetration (mm)')
      ax.set_ylabel('Load (Kg/cm²)')
      ax.set_title('CBR Test Graph')

      ax.grid(
        which='major',
        linestyle='-',
        linewidth=0.8
    )

      ax.xaxis.set_minor_locator(
        AutoMinorLocator(5)
    )

      ax.yaxis.set_minor_locator(
        AutoMinorLocator(5)
    )

      ax.grid(
        which='minor',
        linestyle=':',
        linewidth=0.5
    )

      ax.legend()

      plt.tight_layout()

      buffer = io.BytesIO()

      plt.savefig(
        buffer,
        format='png',
        dpi=150,
        bbox_inches='tight'
    )

      plt.close(fig)

      buffer.seek(0)

      return base64.b64encode(
        buffer.read()
    ).decode('utf-8')
    



#     def generate_line_chart_light_omc(self, data):

#       x_value = []
#       y_value = []

#       for line in data.heavy_table:
#         if line.water_content and line.dry_density:
#             x_value.append(float(line.water_content))
#             y_value.append(float(line.dry_density))

#       if len(x_value) < 3:
#           return False

#       data_points = sorted(zip(x_value, y_value))

#       x = np.array([d[0] for d in data_points])
#       y = np.array([d[1] for d in data_points])

#       coeff = np.polyfit(x, y, 2)
#       poly = np.poly1d(coeff)

#       x_smooth = np.linspace(x.min(), x.max(), 500)
#       y_smooth = poly(x_smooth)

#       omc = -coeff[1] / (2 * coeff[0])
#       mdd = poly(omc)

#       fig, ax = plt.subplots(figsize=(15, 5))

#       ax.plot(
#         x_smooth,
#         y_smooth,
#         color='blue',
#         linewidth=2.5
#     )

#       y_curve_points = poly(x)

#       ax.scatter(
#         x,
#         y_curve_points,
#         color='red',
#         s=40,
#         zorder=5
#     )

#       ax.scatter(
#         omc,
#         mdd,
#         color='red',
#         s=120,
#         zorder=10
#     )

#       ax.axhline(
#         y=mdd,
#         color='red',
#         linestyle='--',
#         linewidth=1
#     )

#       ax.axvline(
#         x=omc,
#         color='red',
#         linestyle='--',
#         linewidth=1
#     )

#       ax.text(
#         omc + 0.2,
#         mdd + 0.002,
#         f"OMC: {omc:.2f}%\nMDD: {mdd:.2f}",
#         color='red',
#         fontsize=11,
#         fontweight='bold'
#     )

#       ax.set_xlabel('Water Content (%)')
#       ax.set_ylabel('Dry Density (g/cc)')
#       ax.set_title('DETERMINATION OF COMPACTION OMC / MDD')

#       ax.set_xlim(
#         left=0,
#         right=max(x) + 2
#     )

#       ax.set_ylim(
#         bottom=min(y) - 0.03,
#         top=max(y_smooth) + 0.03
#     )

#       ax.xaxis.set_major_locator(MultipleLocator(1))
#       ax.xaxis.set_minor_locator(MultipleLocator(0.1))

#       ax.yaxis.set_major_locator(MultipleLocator(0.05))
#       ax.yaxis.set_minor_locator(MultipleLocator(0.001))

#       ax.grid(
#         which='major',
#         color='green',
#         linestyle='-',
#         linewidth=0.5,
#         alpha=0.55
#     )

#       ax.grid(
#         which='minor',
#         color='green',
#         linestyle=':',
#         linewidth=0.3,
#         alpha=0.45
#     )

#       plt.tight_layout()
 
#       buffer = io.BytesIO()

#       plt.savefig(
#         buffer,
#         format='png',
#         dpi=150,
#         bbox_inches='tight'
#     )

#       plt.close(fig)

#       buffer.seek(0)

#       image_data = base64.b64encode(
#     buffer.read()
# ).decode('utf-8')

#       return (
#     image_data,
#     round(float(omc), 2),
#     round(float(mdd), 3)
# )


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

    # def generate_line_chart_light_omc1(self, data):
  
    #   x_value = []
    #   y_value = []
  
    #   for line in data.omc_table:
    #     if line.water_content1 and line.dry_density1:
    #         x_value.append(float(line.water_content1))
    #         y_value.append(float(line.dry_density1))

    #   if len(x_value) < 3:
    #     return False

    #   data_points = sorted(zip(x_value, y_value))

    #   x = np.array([d[0] for d in data_points])
    #   y = np.array([d[1] for d in data_points])

    #   coeff = np.polyfit(x, y, 2)
    #   poly = np.poly1d(coeff)

    #   x_smooth = np.linspace(x.min(), x.max(), 500)
    #   y_smooth = poly(x_smooth)

    #   omc = -coeff[1] / (2 * coeff[0])
    #   mdd = poly(omc)

    #   fig, ax = plt.subplots(figsize=(15, 5))

    #   ax.plot(
    #     x_smooth,
    #     y_smooth,
    #     color='blue',
    #     linewidth=2.5
    # )

    #   y_curve_points = poly(x)

    #   ax.scatter(
    #     x,
    #     y_curve_points,
    #     color='red',
    #     s=40,
    #     zorder=5
    # )

    #   ax.scatter(
    #     omc,
    #     mdd,
    #     color='red',
    #     s=120,
    #     zorder=10
    # )

    #   ax.axhline(
    #     y=mdd,
    #     color='red',
    #     linestyle='--',
    #     linewidth=1
    # )

    #   ax.axvline(
    #     x=omc,
    #     color='red',
    #     linestyle='--',
    #     linewidth=1
    # )

    #   ax.text(
    #     omc + 0.2,
    #     mdd + 0.002,
    #     f"OMC: {omc:.2f}%\nMDD: {mdd:.2f}",
    #     color='red',
    #     fontsize=11,
    #     fontweight='bold'
    # )

    #   ax.set_xlabel('Water Content (%)')
    #   ax.set_ylabel('Dry Density (g/cc)')
    #   ax.set_title('DETERMINATION OF COMPACTION OMC / MDD')

    #   ax.set_xlim(
    #     left=0,
    #     right=max(x) + 2
    # )

    #   ax.set_ylim(
    #     bottom=min(y) - 0.03,
    #     top=max(y_smooth) + 0.03
    # )

    #   ax.xaxis.set_major_locator(MultipleLocator(1))
    #   ax.xaxis.set_minor_locator(MultipleLocator(0.1))

    #   ax.yaxis.set_major_locator(MultipleLocator(0.05))
    #   ax.yaxis.set_minor_locator(MultipleLocator(0.001))

    #   ax.grid(
    #     which='major',
    #     color='green',
    #     linestyle='-',
    #     linewidth=0.5,
    #     alpha=0.55
    # )

    #   ax.grid(
    #     which='minor',
    #     color='green',
    #     linestyle=':',
    #     linewidth=0.3,
    #     alpha=0.45
    # )

    #   plt.tight_layout()

    #   buffer = io.BytesIO()

    #   plt.savefig(
    #     buffer,
    #     format='png',
    #     dpi=150,
    #     bbox_inches='tight'
    # )

    #   plt.close(fig)

    #   buffer.seek(0)

    #   image_data = base64.b64encode(
    #     buffer.read()
    # ).decode('utf-8')

    #   return (
    #     image_data,
    #     round(float(omc), 2),
    #     round(float(mdd), 3)
    # )



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
    


    def generate_line_chart_liquid(self, data):

      import io
      import math
      import base64
      import numpy as np
      import matplotlib.pyplot as plt

      from matplotlib.ticker import LogLocator, MultipleLocator

      x_value = []
      y_value = []

      for line in data.child_liness:

        if line.blwo_no1 and line.moisture_content is not None:
            x_value.append(float(line.blwo_no1))
            y_value.append(float(line.moisture_content))

      if len(x_value) < 2:
        return False

      data = sorted(zip(x_value, y_value), key=lambda x: x[0])

      x_value = [d[0] for d in data]
      y_value = [d[1] for d in data]

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

      ll_value = a * math.log10(25) + b

      x_fit = np.linspace(min(x_value), max(x_value), 500)
      y_fit = [a * math.log10(x) + b for x in x_fit]

      fig, ax = plt.subplots(figsize=(10, 4))

      ax.set_xscale('log')

      ax.plot(
        x_fit,
        y_fit,
        color='blue',
        linewidth=2,
        label='Flow Curve'
    )

      ax.scatter(
        x_value,
        y_value,
        color='red',
        edgecolors='black',
        s=80,
        zorder=5,
        label='Test Points'
    )

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

      ax.xaxis.set_major_locator(LogLocator(base=10))

      ax.xaxis.set_minor_locator(
        LogLocator(
            base=10,
            subs=np.arange(2, 10) * 0.1
        )
    )

      ax.yaxis.set_minor_locator(
        MultipleLocator(1)
    )

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

      plt.close(fig)

      buffer.seek(0)

      return base64.b64encode(
        buffer.read()
    ).decode('utf-8')
        
      
  

class GsbDatasheet1(models.AbstractModel):
    _name = 'report.gsb.gsb_mech_datasheet'
    _description = 'GSB DataSheet '
    
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