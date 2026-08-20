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
    _name = 'report.soil.soil_datasheet_ssl'
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
    _name = 'report.soil.soil_ssl_report1'
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

        # graph_sieve = self._generate_sieve_log_chart(general_data)
        # graph_liquid = self.generate_line_chart_liquid(general_data)

        graph_sieve = False
        if getattr(general_data, 'show_sieve_graph', False):
            graph_sieve = self.generate_line_chart_slive(general_data)

        graph_liquid = False
        if getattr(general_data, 'show_liquid_graph', False):
            graph_liquid = self.generate_line_chart_liquid(general_data)

        graph_shear = False
        if getattr(general_data, 'show_shear_graph', False):
            graph_shear = self.action_generate_shear_graph(general_data)

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
            'qrcode_static': qr_static_b64,
            'stamp' : inreport_value,
            'nabl' : nabl,
            'graphSieve': graph_sieve,  
            'graphliquid': graph_liquid,  
            'graphHeavy' : graph_heavy,
            'heavyomc' : heavy_omc,
            'heavymdd' : heavy_mdd,
            'graphlight' : graph_light,
            'lightomc' : light_omc,
            'lightmdd' : light_mdd,
            'graphcbr' : graph_cbr,
            'graph_shear' :graph_shear,
            
            
            # 'graphLight' : graph_image1,
            
            # 'mdd': max_y if cbry_values else 0,
            # 'omc': max_x if cbrx_values else 0,
            # 'graphCbr': cbr_graph_image,
            # 'load2': cbry_values[5] if len(cbry_values) > 5 else 0,
            # 'load5': cbry_values[8] if len(cbry_values) > 8 else 0,
        }



    def action_generate_shear_graph(self, data):

      import io
      import base64
      import math

      import numpy as np
      import matplotlib.pyplot as plt

    # ----------------------------------
    # Normal Stress
    # ----------------------------------
      x_value = [
        0.5,
        1.0,
        1.5
    ]

    # ----------------------------------
    # Maximum Shear Stress
    # ----------------------------------
      y_value = [
        data.max_shear_stress_05,
        data.max_shear_stress_10,
        data.max_shear_stress_15
    ]

    # ----------------------------------
    # Check values
    # ----------------------------------
      points = [
        (x, y)
        for x, y in zip(x_value, y_value)
        if y is not None
    ]

      if len(points) < 2:
        return False

      x_value = [
        p[0]
        for p in points
    ]

      y_value = [
        p[1]
        for p in points
    ]

    # ----------------------------------
    # Linear Regression
    #
    # y = mx + c
    # ----------------------------------
      n = len(x_value)

      sum_x = sum(x_value)
      sum_y = sum(y_value)

      sum_xy = sum(
        x * y
        for x, y in zip(
            x_value,
            y_value
        )
    )

      sum_x2 = sum(
        x * x
        for x in x_value
    )

      denominator = (
        n * sum_x2
        - sum_x ** 2
    )

      if denominator == 0:
        return False

    # ----------------------------------
    # Slope
    # ----------------------------------
      slope = (
        n * sum_xy
        - sum_x * sum_y
    ) / denominator

    # ----------------------------------
    # Intercept / Cohesion
    # ----------------------------------
      intercept = (
        sum_y
        - slope * sum_x
    ) / n

    # ----------------------------------
    # Phi
    # ----------------------------------
      phi_value = (
        math.atan(slope)
        * 180.0
        / math.pi
    )

    # ----------------------------------
    # Regression line
    # ----------------------------------
      x_fit = np.linspace(
        min(x_value),
        max(x_value),
        200
    )

      y_fit = (
        slope * x_fit
        + intercept
    )

    # ----------------------------------
    # Create Graph
    # ----------------------------------
      fig, ax = plt.subplots(
        figsize=(10, 5)
    )

    # ----------------------------------
    # Actual points + connecting line
    # ----------------------------------
      ax.plot(
        x_value,
        y_value,
        color='#4A90E2',
        linewidth=2,
        marker='o',
        markersize=7,
        markerfacecolor='#4A90E2',
        markeredgecolor='#4A90E2',
        zorder=5
    )

    # ----------------------------------
    # Trend line
    # ----------------------------------
      ax.plot(
        x_fit,
        y_fit,
        color='#4A90E2',
        linestyle=':',
        linewidth=1.5,
        zorder=2
    )

    # ----------------------------------
    # Labels
    # ----------------------------------
      ax.set_xlabel(
        'Normal Stress (kg/cm²)',
        fontsize=11,
        fontweight='bold'
    )

      ax.set_ylabel(
        'Shear Stress (kg/cm²)',
        fontsize=11,
        fontweight='bold'
    )

      ax.set_title(
        'Direct Shear Test',
        fontsize=14,
        fontweight='bold'
    )

    # ----------------------------------
    # X Axis
    # ----------------------------------
      ax.set_xlim(
        0,
        2
    )

      ax.set_xticks(
        np.arange(
            0,
            2.1,
            0.5
        )
    )

    # ----------------------------------
    # Y Axis
    # ----------------------------------
      ax.set_ylim(
        0,
        1.0
    )

      ax.set_yticks(
        np.arange(
            0,
            1.01,
            0.2
        )
    )

    # ----------------------------------
    # Grid
    # ----------------------------------
      ax.grid(
        True,
        linestyle='-',
        linewidth=0.5,
        alpha=0.5
    )

    # ----------------------------------
    # Layout
    # ----------------------------------
      plt.tight_layout()

    # ----------------------------------
    # Save PNG
    # ----------------------------------
      buffer = io.BytesIO()

      plt.savefig(
        buffer,
        format='png',
        dpi=100,
        bbox_inches='tight'
    )

      plt.close(fig)

      buffer.seek(0)

    # ----------------------------------
    # Return Base64
    # ----------------------------------
      return base64.b64encode(
        buffer.read()
    ).decode('utf-8')
    

    def generate_cbr_chart(self, data):

      lines = self.env['mechanical.cbr.line'].search(
        [('parent_id', '=', data.id)],
        order='penetration asc'
    )

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
    

    def generate_line_chart_light_omc(self, data):

      x_value = []
      y_value = []

      for line in data.heavy_table:
        if line.water_content and line.dry_density:
            x_value.append(float(line.water_content))
            y_value.append(float(line.dry_density))

      if len(x_value) < 3:
          return False

      data_points = sorted(zip(x_value, y_value))

      x = np.array([d[0] for d in data_points])
      y = np.array([d[1] for d in data_points])

      coeff = np.polyfit(x, y, 2)
      poly = np.poly1d(coeff)

      x_smooth = np.linspace(x.min(), x.max(), 500)
      y_smooth = poly(x_smooth)

      omc = -coeff[1] / (2 * coeff[0])
      mdd = poly(omc)

      fig, ax = plt.subplots(figsize=(15, 5))

      ax.plot(
        x_smooth,
        y_smooth,
        color='blue',
        linewidth=2.5
    )

      y_curve_points = poly(x)

      ax.scatter(
        x,
        y_curve_points,
        color='red',
        s=40,
        zorder=5
    )

      ax.scatter(
        omc,
        mdd,
        color='red',
        s=120,
        zorder=10
    )

      ax.axhline(
        y=mdd,
        color='red',
        linestyle='--',
        linewidth=1
    )

      ax.axvline(
        x=omc,
        color='red',
        linestyle='--',
        linewidth=1
    )

      ax.text(
        omc + 0.2,
        mdd + 0.002,
        f"OMC: {omc:.2f}%\nMDD: {mdd:.2f}",
        color='red',
        fontsize=11,
        fontweight='bold'
    )

      ax.set_xlabel('Water Content (%)')
      ax.set_ylabel('Dry Density (g/cc)')
      ax.set_title('DETERMINATION OF COMPACTION OMC / MDD')

      ax.set_xlim(
        left=0,
        right=max(x) + 2
    )

      ax.set_ylim(
        bottom=min(y) - 0.03,
        top=max(y_smooth) + 0.03
    )

      ax.xaxis.set_major_locator(MultipleLocator(1))
      ax.xaxis.set_minor_locator(MultipleLocator(0.1))

      ax.yaxis.set_major_locator(MultipleLocator(0.05))
      ax.yaxis.set_minor_locator(MultipleLocator(0.001))

      ax.grid(
        which='major',
        color='green',
        linestyle='-',
        linewidth=0.5,
        alpha=0.55
    )

      ax.grid(
        which='minor',
        color='green',
        linestyle=':',
        linewidth=0.3,
        alpha=0.45
    )

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

      image_data = base64.b64encode(
    buffer.read()
).decode('utf-8')

      return (
    image_data,
    round(float(omc), 2),
    round(float(mdd), 3)
)
    


    def generate_line_chart_light_omc1(self, data):
  
      x_value = []
      y_value = []
  
      for line in data.omc_table:
        if line.water_content1 and line.dry_density1:
            x_value.append(float(line.water_content1))
            y_value.append(float(line.dry_density1))

      if len(x_value) < 3:
        return False

      data_points = sorted(zip(x_value, y_value))

      x = np.array([d[0] for d in data_points])
      y = np.array([d[1] for d in data_points])

      coeff = np.polyfit(x, y, 2)
      poly = np.poly1d(coeff)

      x_smooth = np.linspace(x.min(), x.max(), 500)
      y_smooth = poly(x_smooth)

      omc = -coeff[1] / (2 * coeff[0])
      mdd = poly(omc)

      fig, ax = plt.subplots(figsize=(15, 5))

      ax.plot(
        x_smooth,
        y_smooth,
        color='blue',
        linewidth=2.5
    )

      y_curve_points = poly(x)

      ax.scatter(
        x,
        y_curve_points,
        color='red',
        s=40,
        zorder=5
    )

      ax.scatter(
        omc,
        mdd,
        color='red',
        s=120,
        zorder=10
    )

      ax.axhline(
        y=mdd,
        color='red',
        linestyle='--',
        linewidth=1
    )

      ax.axvline(
        x=omc,
        color='red',
        linestyle='--',
        linewidth=1
    )

      ax.text(
        omc + 0.2,
        mdd + 0.002,
        f"OMC: {omc:.2f}%\nMDD: {mdd:.2f}",
        color='red',
        fontsize=11,
        fontweight='bold'
    )

      ax.set_xlabel('Water Content (%)')
      ax.set_ylabel('Dry Density (g/cc)')
      ax.set_title('DETERMINATION OF COMPACTION OMC / MDD')

      ax.set_xlim(
        left=0,
        right=max(x) + 2
    )

      ax.set_ylim(
        bottom=min(y) - 0.03,
        top=max(y_smooth) + 0.03
    )

      ax.xaxis.set_major_locator(MultipleLocator(1))
      ax.xaxis.set_minor_locator(MultipleLocator(0.1))

      ax.yaxis.set_major_locator(MultipleLocator(0.05))
      ax.yaxis.set_minor_locator(MultipleLocator(0.001))

      ax.grid(
        which='major',
        color='green',
        linestyle='-',
        linewidth=0.5,
        alpha=0.55
    )

      ax.grid(
        which='minor',
        color='green',
        linestyle=':',
        linewidth=0.3,
        alpha=0.45
    )

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

      image_data = base64.b64encode(
        buffer.read()
    ).decode('utf-8')

      return (
        image_data,
        round(float(omc), 2),
        round(float(mdd), 3)
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
    


    def generate_line_chart_liquid(self, data):

      import io
      import base64
      import numpy as np
      import matplotlib.pyplot as plt

    # =========================================================
    # GET DATA
    # =========================================================

      x_value = []
      y_value = []

      for line in data.child_liness:

        if (
            line.penetration is not None
            and line.moisture_content is not None
        ):
            try:

                x_value.append(
                    float(line.penetration)
                )

                y_value.append(
                    float(line.moisture_content)
                )

            except (ValueError, TypeError):
                continue

    # =========================================================
    # MINIMUM 2 POINTS REQUIRED
    # =========================================================

      if len(x_value) < 2:
        return False

    # =========================================================
    # SORT DATA BY PENETRATION
    # =========================================================

      sorted_data = sorted(
        zip(x_value, y_value),
        key=lambda item: item[0]
    )

      x_value = [
        item[0]
        for item in sorted_data
    ]

      y_value = [
        item[1]
        for item in sorted_data
    ]

    # =========================================================
    # LINEAR REGRESSION
    #
    # y = a*x + b
    # =========================================================

      n = len(x_value)

      sum_x = sum(x_value)
      sum_y = sum(y_value)

      sum_xy = sum(
        x * y
        for x, y in zip(
            x_value,
            y_value
        )
    )

      sum_x2 = sum(
        x * x
        for x in x_value
    )

      denominator = (
        n * sum_x2
        - (sum_x ** 2)
    )

      if denominator == 0:
        return False

    # =========================================================
    # SLOPE
    # =========================================================

      a = (
        n * sum_xy
        - sum_x * sum_y
    ) / denominator

    # =========================================================
    # INTERCEPT
    # =========================================================

      b = (
        sum_y
        - a * sum_x
    ) / n

    # =========================================================
    # LIQUID LIMIT AT 20 mm
    #
    # NO ROUNDING
    # =========================================================

      ll_penetration = 20.0

      ll_value = (
        a * ll_penetration + b
    )

    # =========================================================
    # TRUE REGRESSION LINE
    #
    # Only draw between actual minimum
    # and maximum data points.
    # =========================================================

      x_fit = np.linspace(
        min(x_value),
        max(x_value),
        500
    )

      y_fit = (
        a * x_fit + b
    )

    # =========================================================
    # DYNAMIC AXIS DATA
    #
    # Include 20 mm and exact LL value.
    # =========================================================

      all_x_values = (
        x_value + [ll_penetration]
    )

      all_y_values = (
        y_value + [ll_value]
    )

      data_x_min = min(
        all_x_values
    )

      data_x_max = max(
        all_x_values
    )

      data_y_min = min(
        all_y_values
    )

      data_y_max = max(
        all_y_values
    )

    # =========================================================
    # DYNAMIC X AXIS
    #
    # Add 1 mm on both sides.
    #
    # Example:
    #
    # Data: 16 -> 26
    #
    # Graph: 15 -> 27
    # =========================================================

      x_min = np.floor(
        data_x_min - 1
    )

      x_max = np.ceil(
        data_x_max + 1
    )

    # =========================================================
    # DYNAMIC Y AXIS
    #
    # Add 10% padding.
    # =========================================================

      y_range = (
        data_y_max - data_y_min
    )

      if y_range == 0:
        y_range = 1

      y_padding = (
        y_range * 0.10
    )

      y_min = (
        data_y_min - y_padding
    )

      y_max = (
        data_y_max + y_padding
    )

    # =========================================================
    # CREATE FIGURE
    # =========================================================

      fig, ax = plt.subplots(
        figsize=(10, 5)
    )

    # =========================================================
    # LINEAR X AXIS
    # =========================================================

      ax.set_xscale(
        'linear'
    )

    # =========================================================
    # RED REGRESSION LINE
    # =========================================================

      ax.plot(
        x_fit,
        y_fit,
        color='#c64b47',
        linewidth=2.5,
        zorder=2
    )

    # =========================================================
    # RED TEST POINTS
    # =========================================================

      ax.scatter(
        x_value,
        y_value,
        color='#c64b47',
        edgecolors='#c64b47',
        marker='s',
        s=70,
        zorder=5
    )

    # =========================================================
    # BLACK VERTICAL LINE AT 20 mm
    #
    # IMPORTANT:
    #
    # It ends at the EXACT regression value.
    #
    # Therefore the vertical line intersects
    # the red regression line exactly.
    # =========================================================

      ax.plot(
        [
            ll_penetration,
            ll_penetration
        ],
        [
            y_min,
            ll_value
        ],
        color='black',
        linewidth=2,
        zorder=3
    )

    # =========================================================
    # DOWN ARROW AT 20 mm
    # =========================================================

      arrow_height = (
        y_range * 0.15
    )

      arrow_top = min(
        ll_value + arrow_height,
        y_max
    )

      ax.annotate(
        '',
        xy=(
            ll_penetration,
            y_min
        ),
        xytext=(
            ll_penetration,
            arrow_top
        ),
        arrowprops=dict(
            arrowstyle='->',
            color='black',
            linewidth=2
        ),
        zorder=4
    )

    # =========================================================
    # BLACK HORIZONTAL LINE AT LIQUID LIMIT
    #
    # NO ROUNDING
    # =========================================================

      horizontal_start = x_min

      horizontal_end = max(
        x_value
    )

      ax.plot(
        [
            horizontal_start,
            horizontal_end
        ],
        [
            ll_value,
            ll_value
        ],
        color='black',
        linewidth=2,
        zorder=3
    )

    # =========================================================
    # LEFT ARROW AT LIQUID LIMIT
    # =========================================================

      arrow_width = (
        horizontal_end
        - horizontal_start
    ) * 0.08

      ax.annotate(
        '',
        xy=(
            horizontal_start,
            ll_value
        ),
        xytext=(
            horizontal_start + arrow_width,
            ll_value
        ),
        arrowprops=dict(
            arrowstyle='->',
            color='black',
            linewidth=2
        ),
        zorder=4
    )

    # =========================================================
    # X AXIS LIMIT
    # =========================================================

      ax.set_xlim(
        x_min,
        x_max
    )

    # =========================================================
    # X MAJOR TICKS
    #
    # Every 2 mm
    #
    # Example:
    #
    # 16 18 20 22 24 26
    # =========================================================

      major_x_start = (
        np.ceil(x_min / 2) * 2
    )

      major_x_end = (
        np.floor(x_max / 2) * 2
    )

      ax.set_xticks(
        np.arange(
            major_x_start,
            major_x_end + 1,
            2
        )
    )

    # =========================================================
    # X MINOR TICKS
    #
    # Every 0.5 mm
    # =========================================================

      ax.set_xticks(
        np.arange(
            x_min,
            x_max + 0.5,
            0.5
        ),
        minor=True
    )

    # =========================================================
    # Y AXIS LIMIT
    # =========================================================

      ax.set_ylim(
        y_min,
        y_max
    )

    # =========================================================
    # Y MAJOR TICKS
    #
    # Every 1%
    # =========================================================

      y_major_start = np.ceil(
        y_min
    )

      y_major_end = np.floor(
        y_max
    )

      ax.set_yticks(
        np.arange(
            y_major_start,
            y_major_end + 1,
            1
        )
    )

    # =========================================================
    # Y MINOR TICKS
    #
    # Every 0.5%
    # =========================================================

      ax.set_yticks(
        np.arange(
            np.floor(y_min),
            np.ceil(y_max) + 0.5,
            0.5
        ),
        minor=True
    )

    # =========================================================
    # X LABEL
    # =========================================================

      ax.set_xlabel(
        'penetration(mm)',
        fontsize=12,
        fontweight='bold'
    )

    # =========================================================
    # Y LABEL
    # =========================================================

      ax.set_ylabel(
        'Moisture Content (%)',
        fontsize=12,
        fontweight='bold'
    )

    # =========================================================
    # MAJOR GRID
    # =========================================================

      ax.grid(
        which='major',
        color='black',
        linestyle='-',
        linewidth=0.5,
        alpha=0.7
    )

    # =========================================================
    # MINOR GRID
    # =========================================================

      ax.grid(
        which='minor',
        color='#d0d7df',
        linestyle='-',
        linewidth=0.4,
        alpha=0.7
    )

    # =========================================================
    # TICK LABELS
    # =========================================================

      ax.tick_params(
        axis='both',
        which='major',
        labelsize=10
    )

    # =========================================================
    # REMOVE LEGEND
    # =========================================================

      if ax.legend_:
        ax.legend_.remove()

    # =========================================================
    # LAYOUT
    # =========================================================

      plt.tight_layout()

    # =========================================================
    # CONVERT TO PNG
    # =========================================================

      buffer = io.BytesIO()

      plt.savefig(
        buffer,
        format='png',
        dpi=100,
        bbox_inches='tight'
    )

      plt.close(fig)

      buffer.seek(0)

    # =========================================================
    # RETURN BASE64
    # =========================================================

      return base64.b64encode(
        buffer.read()
    ).decode('utf-8')
        

      
        # plt.figure(figsize=(12, 6))
        # cbrx_values = []
        # cbry_values = []

        # # Check if cbr_table exists and populate cbrx_values and cbry_values
        # if general_data.soil_table:
        #     for line in general_data.soil_table:
        #         cbrx_values.append(line.penetration)
        #         cbry_values.append(line.load)

        #     try:
        #         max_y = max(cbry_values)
        #     except ValueError:
        #         max_y = 100  # Default value if cbry_values is empty
        #     try:
        #         min_y = round(min(cbry_values), 2)
        #     except ValueError:
        #         min_y = 0
        #     try:
        #         max_x = cbrx_values[cbry_values.index(max_y)]
        #     except ValueError:
        #         max_x = 100
        #     try:
        #         min_x = round(min(cbrx_values), 2)
        #     except ValueError:
        #         min_x = 0

        #     # Format max_y and max_x to display 2 digits after the decimal point
        #     max_y = round(max_y, 2)
        #     max_x = round(max_x, 2)

        #     # Perform cubic spline interpolation if there are enough data points
        #     if len(cbrx_values) > 1 and len(cbry_values) > 1:
        #         cbrx_smooth = np.linspace(min(cbrx_values), max(cbrx_values), 100)
        #         cbrcs = CubicSpline(cbrx_values, cbry_values)

        #         # Create the line chart with a connected smooth line and markers
        #         plt.plot(cbrx_smooth, cbrcs(cbrx_smooth), color='red', label='Smooth Curve')
        #         plt.scatter(cbrx_values, cbry_values, marker='o', color='blue', s=30, label='Data Points')

        #         # Add horizontal lines with labels
        #         if len(cbry_values) > 8:  # Ensure indices 5 and 8 exist
        #             plt.axhline(y=cbry_values[5], color='green', linestyle='--', label=f'Load at 2.5 mm = {cbry_values[5]}')
        #             plt.axhline(y=cbry_values[8], color='green', linestyle='--', label=f'Load at 5 mm = {cbry_values[8]}')

        #         # Add vertical lines at specific penetration values
        #         plt.axvline(x=2.5, color='orange', linestyle='--')
        #         plt.axvline(x=5.0, color='orange', linestyle='--')

        #         # Set the grid
        #         ax = plt.gca()
        #         ax.grid(which='both', linestyle='--', linewidth=0.5)

        #         # Set the x-axis major and minor tick marks
        #         ax.xaxis.set_major_locator(ticker.MultipleLocator(1))  # Major gridlines every 1 unit
        #         ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))  # Minor gridlines every 0.1 unit

        #         # Set the y-axis tick marks
        #         plt.yticks(np.arange(min_y, max_y + 0.2, (max_y - min_y) / 5))

        #         # Set the x-axis tick marks
        #         if max_x != min_x:
        #             plt.xticks(np.arange(min_x, max_x + 1.0, (max_x - min_x) / 5))

        #         # Set labels and title
        #         plt.xlabel('Penetration in mm')
        #         plt.ylabel('Load')
        #         plt.title('Penetration in mm vs Load')
        #         plt.legend()

        #     # Save the Matplotlib plot to a BytesIO object
        #     buffer2 = BytesIO()
        #     plt.savefig(buffer2, format='png')
        #     cbr_graph_image = base64.b64encode(buffer2.getvalue()).decode('utf-8')
        #     plt.close()
        # else:
        #     cbr_graph_image = None
        #     cbry_values = []  # Reset to empty list
        #     cbrx_values = []

        # plt.figure(figsize=(12, 6))
        # x_values = []
        # y_values = []
        # # import wdb;wdb.set_trace()
        # for line in general_data.omc_table:
        #     x_values.append(line.water_content1)
        #     y_values.append(line.dry_density1)


        # if general_data.omc_table:
        #     try:
        #         max_y = max(y_values)
        #     except:
        #         max_y = 100
        #     try:
        #         min_y = round(min(y_values),2)
        #     except:
        #         min_y = 0
        #     try:
        #         # max_x = round(max(x_values),2)
        #         max_x = x_values[y_values.index(max_y)]
        #     except:
        #         max_x = 100
        #     try:
        #         min_x = round(min(x_values),2)
        #     except:
        #         min_x = 0 
            
            


        #     # Format max_y and max_x to display 2 digits after the decimal point
        #     max_y = round(max_y , 2)
        #     max_x = round(max_x, 2)

    

        
        #     # Perform cubic spline interpolation
        #     x_smooth = np.linspace(min(x_values), max(x_values), 100)
        #     # cs = CubicSpline(x_values, y_values,1)
        #     # cs = interp1d(x_values, y_values,kind='cubic')
        #     cs = Akima1DInterpolator(x_values, y_values)

        #     # Create the line chart with a connected smooth line and markers
        #     plt.plot(x_smooth, cs(x_smooth), color='red', label='Smooth Curve')
        #     plt.scatter(x_values, y_values, marker='o', color='blue', s=30, label='Data Points')

            
        #     # Add a horizontal line with a label(, linestyle='--', label=f'Max Y = {max_y}', linestyle='--', label=f'Max X = {max_x}')
        #     plt.axhline(y=max_y, color='green',linestyle='--')

        #     # Add a vertical line with a label
        #     plt.axvline(x=max_x, color='orange',linestyle='--')

            
        #     # Set the grid
        #     ax = plt.gca()
        #     ax.grid(which='both', linestyle='--', linewidth=0.5)

        #     # Set the x-axis major and minor tick marks
        #     ax.xaxis.set_major_locator(ticker.MultipleLocator(1))  # Major gridlines every 1 unit
        #     ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))  # Minor gridlines every 0.1 unit

        #     # Set the y-axis tick marks
        #     # plt.yticks([1.60, 1.62, 1.64, 1.66, 1.68, 1.70, 1.72, 1.74, 1.76, 1.78, 1.80])

        #     # edit range here
        #     plt.yticks(np.arange(min_y , round(max_y,2) + 0.2 , (max_y - min_y) / 5))


        #     if max_x != min_x:
        #         plt.xticks(np.arange(min_x, round(max(x_values),2) + 1.0, (max_x - min_x) / 5))
            
        #     plt.gca().yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))
        #     plt.xlabel('Water Content (%) ')
        #     plt.ylabel('Dry density in gm/cc')
        #     plt.title('% DETERMINATION OF COMPACTION OMC / MDD')
        #     plt.legend()

        #     # Save the Matplotlib plot to a BytesIO object
        #     buffer = BytesIO()
        #     plt.savefig(buffer, format='png')
        #     graph_image1 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        #     # Close the Matplotlib plot to free up resources
        #     plt.close()
        # else:
        #     graph_image1 = None
        #     max_y = 0
        #     max_x = 0

        



    

            




    # def generate_line_chart_liquid(self, general_data):
    #     x_value = []
    #     y_value = []
    #     for line in general_data.child_liness:
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

    #     # 🔹 Highlight Liquid Limit point (general_data field वापरून)
    #     if general_data.liquid_limit:
    #         highlight_x = 25                        # Blows (fixed at 25)
    #         highlight_y = general_data.liquid_limit # Moisture content from record field

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

