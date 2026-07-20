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
from scipy.interpolate import PchipInterpolator
from matplotlib.ticker import AutoMinorLocator
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

        
        graph_direct = False
        if getattr(general_data, 'show_direct_graph', False):
            graph_direct = self.generate_line_chart_direct_shear(general_data)

        

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
            'graphDirect': graph_direct,

            
            
            # 'graphLight' : graph_image1,
            
            # 'mdd': max_y if cbry_values else 0,
            # 'omc': max_x if cbrx_values else 0,
            # 'graphCbr': cbr_graph_image,
            # 'load2': cbry_values[5] if len(cbry_values) > 5 else 0,
            # 'load5': cbry_values[8] if len(cbry_values) > 8 else 0,
        }
    

    def generate_line_chart_direct_shear(self, data):

        normal_stress = []
        shear_stress = []

        if data.shear_stress_05:
            normal_stress.append(0.5)
            shear_stress.append(float(data.shear_stress_05))

        if data.shear_stress_10:
            normal_stress.append(1.0)
            shear_stress.append(float(data.shear_stress_10))

        if data.shear_stress_15:
            normal_stress.append(1.5)
            shear_stress.append(float(data.shear_stress_15))

        if len(normal_stress) < 2:
            return False

        x = np.array(normal_stress)
        y = np.array(shear_stress)

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.set_facecolor("white")

        ax.set_xlim(0, 2.0)
        ax.set_ylim(0, 1.6)

        ax.set_axisbelow(True)
        ax.minorticks_on()

        ax.grid(
        which="major",
        color="#84B7A0",
        linewidth=1.0)

        ax.grid(
        which="minor",
        color="#C8E1D4",
        linewidth=0.35)

        ax.xaxis.set_major_locator(MultipleLocator(0.5))
        ax.xaxis.set_minor_locator(MultipleLocator(0.05))

        ax.yaxis.set_major_locator(MultipleLocator(0.25))
        ax.yaxis.set_minor_locator(MultipleLocator(0.025))

        for spine in ax.spines.values():
            spine.set_linewidth(1)

        ax.plot(
        x,
        y,
        color="blue",
        linewidth=1.2,
        marker="o",
        markersize=4)

        ax.set_xlabel(
        "Penetration (mm)",
        fontsize=10)

        ax.set_ylabel(
        "Load (KG)",
        fontsize=10,
        rotation=0,
        labelpad=70,
        va="center")

        ax.tick_params(
        axis="both",
        which="major",
        labelsize=8)

        ax.set_xticks([0, 0.5, 1.0, 1.5, 2.0])

        ax.set_xticklabels(
        ["0", "0.5", "1", "1.5", "2"])

        ax.set_yticks(
        np.arange(0, 1.75, 0.25))

        ax.set_yticklabels([
        "0.00",
        "0.25",
        "0.50",
        "0.75",
        "1.00",
        "1.25",
        "1.50"  ])

        plt.tight_layout()

        buffer = io.BytesIO()

        plt.savefig(
        buffer,
        format="png",
        dpi=100,
        bbox_inches="tight",
        facecolor="white")

        plt.close(fig)

        buffer.seek(0)

        image_data = base64.b64encode(
        buffer.read()
    ).decode("utf-8")

        buffer.close()

        return image_data
    

    def generate_cbr_chart(self, data):

        # --------------------------------------
        # Read CBR Data
        # --------------------------------------

        lines = self.env['mechanical.cbr.line'].search(
        [('parent_id', '=', data.id)],
        order='penetration asc')

        if len(lines) < 2:
            return False

        penetration = np.array(
        [float(line.penetration or 0) for line in lines],
        dtype=float)

        sample1 = np.array(
        [float(line.sample1_load or 0) for line in lines],
        dtype=float)

        sample2 = np.array(
        [float(line.sample2_load or 0) for line in lines],
        dtype=float)

        sample3 = np.array(
        [float(line.sample3_load or 0) for line in lines],
        dtype=float)

        # --------------------------------------
        # Smooth Curve (Excel Style)
        # --------------------------------------

        x_new = np.linspace(
        penetration.min(),
        penetration.max(),
        500)

        curve1 = PchipInterpolator(
        penetration,
        sample1)

        curve2 = PchipInterpolator(
        penetration,
        sample2)

        curve3 = PchipInterpolator(
        penetration,
        sample3)

        y1 = curve1(x_new)
        y2 = curve2(x_new)
        y3 = curve3(x_new)

        # --------------------------------------
        # Create Figure
        # --------------------------------------

        fig, ax = plt.subplots(
        figsize=(10, 6))

        # --------------------------------------
        # Plot Smooth Curves
        # --------------------------------------

        ax.plot(
        x_new,
        y1,
        color="#1f77b4",
        linewidth=2.2,
        label="Sample-1")

        ax.plot(
        x_new,
        y2,
        color="#ff7f0e",
        linewidth=2.2,
        label="Sample-2")

        ax.plot(
        x_new,
        y3,
        color="#2ca02c",
        linewidth=2.2,
        label="Sample-3")

        # --------------------------------------
        # Original Data Points
        # --------------------------------------

        ax.scatter(
        penetration,
        sample1,
        color="#1f77b4",
        s=30,
        zorder=5)

        ax.scatter(
        penetration,
        sample2,
        color="#ff7f0e",
        s=30,
        zorder=5)

        ax.scatter(
        penetration,
        sample3,
        color="#2ca02c",
        s=30,
        zorder=5)

    # --------------------------------------
    # Labels
    # --------------------------------------

        ax.set_title(
        "CBR Test Graph",
        fontsize=20,
        fontweight="bold")

        ax.set_xlabel(
        "Penetration (mm)",
        fontsize=15)

        ax.set_ylabel(
        "Load (Kg/cm²)",
        fontsize=15)

        # --------------------------------------
        # Axis Limits
        # --------------------------------------

        ax.set_xlim(0, 14)
        ax.set_ylim(40, 320)

        ax.xaxis.set_major_locator(
        MultipleLocator(1))

        ax.xaxis.set_minor_locator(
        MultipleLocator(0.2))

        ax.yaxis.set_major_locator(
        MultipleLocator(20))

        ax.yaxis.set_minor_locator(
        MultipleLocator(5))

        # --------------------------------------
        # Graph Paper
        # --------------------------------------

        ax.set_facecolor("white")

        ax.grid(
        which="major",
        color="#9a9a9a",
        linewidth=0.7,
        alpha=0.6)

        ax.grid(
        which="minor",
        color="#d8d8d8",
        linestyle=":",
        linewidth=0.45)

        ax.set_axisbelow(True)

        # Border

        for spine in ax.spines.values():
            spine.set_linewidth(1.0)

        # Legend

        ax.legend(
        loc="upper left",
        fontsize=12)

        plt.tight_layout()


        # --------------------------------------
        # Save Image
        # --------------------------------------

        buffer = io.BytesIO()

        plt.savefig(
        buffer,
        format="png",
        dpi=100,
        bbox_inches="tight",
        facecolor="white")

        plt.close(fig)

        buffer.seek(0)

        image_data = base64.b64encode(
        buffer.read()
    ).decode("utf-8")

        buffer.close()

        return image_data
    

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

