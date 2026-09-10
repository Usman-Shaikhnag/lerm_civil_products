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

from matplotlib.ticker import MultipleLocator, StrMethodFormatter



class GsbReport1(models.AbstractModel):
    _name = 'report.gsb.gsb_mec_report'
    _description = 'GSB Report '
    
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

        graph_cbr = False
        if getattr(general_data, 'show_cbr', False):
            graph_cbr = self.generate_cbr_chart(general_data)


        graph_liquid = False
        if getattr(general_data, 'show_liquid_graph', False):
            graph_liquid = self.generate_line_chart_liquid(general_data)


        
        
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
            'graphcbr' : graph_cbr,
            'graphliquid': graph_liquid,
        }



    def generate_line_chart_liquid(self, data):

      data.ensure_one()

      x_value = []
      y_value = []

    # =========================================================
    # GET METHOD
    # =========================================================
      method = data.liquid_limit_method
 
    # =========================================================
    # GET DATA
    # =========================================================
      for line in data.child_liness:

          try:

              if line.moisture_content is None:
                  continue

              moisture = float(line.moisture_content)

            # -------------------------------------------------
            # CASAGRANDE
            # X = Number of blows
            # -------------------------------------------------
              if method == 'casagrande':

                  if line.penetration is None:
                      continue

                  x = float(line.penetration)

                # log10() cannot accept 0 or negative values
                  if x <= 0:
                      continue

            # -------------------------------------------------
            # CONE
            # X = Penetration (mm)
            # -------------------------------------------------
              else:

                  if line.penetration is None:
                    continue

                  x = float(line.penetration)

                  if x <= 0:
                    continue

              x_value.append(x)
              y_value.append(moisture)

          except (ValueError, TypeError):
              continue

    # =========================================================
    # MINIMUM 2 POINTS
    # =========================================================
      if len(x_value) < 2:
          return False

    # =========================================================
    # SORT DATA
    # =========================================================
      data = sorted(
        zip(x_value, y_value),
        key=lambda x: x[0]
    )

      x_value = [d[0] for d in data]
      y_value = [d[1] for d in data]

    # =========================================================
    # REGRESSION
    # =========================================================

      n = len(x_value)

      if method == 'casagrande':

        # =====================================================
        # CASAGRANDE
        # w = a * log10(N) + b
        # =====================================================

          x_log = [
            math.log10(x)
            for x in x_value
        ]

          sum_x = sum(x_log)
          sum_y = sum(y_value)

          sum_xy = sum(
            x * y
            for x, y in zip(x_log, y_value)
        )

          sum_x2 = sum(
            x * x
            for x in x_log
        )

          denominator = (
            n * sum_x2
            - sum_x ** 2
        )

          if abs(denominator) < 1e-12:
            return False

          a = (
            n * sum_xy
            - sum_x * sum_y
        ) / denominator

          b = (
            sum_y
            - a * sum_x
        ) / n

        # LL at 25 blows
          ll_x = 25.0

          ll_value = (
            a * math.log10(ll_x)
            + b
        )

        # Smooth logarithmic regression curve
          x_fit = np.logspace(
            math.log10(min(x_value)),
            math.log10(max(x_value)),
            500
        )

          y_fit = [
            a * math.log10(x) + b
            for x in x_fit
        ]

          x_label = 'Number of Blows (Log Scale)'
          graph_title = 'LIQUID LIMIT - CASAGRANDE METHOD'

      else:

        # =====================================================
        # CONE METHOD
        # w = a * penetration + b
        # =====================================================

          sum_x = sum(x_value)
          sum_y = sum(y_value)

          sum_xy = sum(
            x * y
            for x, y in zip(x_value, y_value)
        )

          sum_x2 = sum(
            x * x
            for x in x_value
        )

          denominator = (
            n * sum_x2
            - sum_x ** 2
        )

          if abs(denominator) < 1e-12:
            return False

          a = (
            n * sum_xy
            - sum_x * sum_y
        ) / denominator

          b = (
            sum_y
            - a * sum_x
        ) / n

        # LL at 20 mm penetration
          ll_x = 20.0

          ll_value = (
            a * ll_x
            + b
        )

        # Smooth linear regression curve
          x_fit = np.linspace(
            min(x_value),
            max(x_value),
            500
        )

          y_fit = (
            a * x_fit
            + b
        )

          x_label = 'Penetration (mm)'
          graph_title = 'LIQUID LIMIT - CONE METHOD'

    # =========================================================
    # CREATE GRAPH
    # =========================================================
 
      fig, ax = plt.subplots(
        figsize=(10, 4)
    )

    # =========================================================
    # X AXIS
    # =========================================================

      if method == 'casagrande':
        ax.set_xscale('log')
      else:
        ax.set_xscale('linear')

    # =========================================================
    # REGRESSION / FLOW CURVE
    # =========================================================

      ax.plot(
        x_fit,
        y_fit,
        color='blue',
        linewidth=2,
        label='Flow Curve'
    )

    # =========================================================
    # ACTUAL TEST POINTS
    # =========================================================

      ax.scatter(
        x_value,
        y_value,
        color='red',
        edgecolors='black',
        s=80,
        zorder=5,
        label='Test Points'
    )

    # =========================================================
    # LIQUID LIMIT VERTICAL LINE
    # =========================================================

      ax.axvline(
        x=ll_x,
        color='green',
        linestyle='--',
        linewidth=1.2
    )

    # =========================================================
    # LIQUID LIMIT HORIZONTAL LINE
    # =========================================================

      ax.axhline(
        y=ll_value,
        color='green',
        linestyle='--',
        linewidth=1.2
    )

    # =========================================================
    # LL POINT
    # =========================================================

      ax.scatter(
        [ll_x],
        [ll_value],
        color='green',
        s=120,
        zorder=10
    )

    # =========================================================
    # LL LABEL
    # =========================================================

      if method == 'casagrande':

        ax.annotate(
            f'LL = {ll_value:.2f}%\n(25 blows)',
            xy=(ll_x, ll_value),
            xytext=(26, ll_value + 2),
            color='green',
            fontsize=12,
            fontweight='bold'
        )

      else:

        ax.annotate(
            f'LL = {ll_value:.2f}%\n(20 mm)',
            xy=(ll_x, ll_value),
            xytext=(ll_x + 1, ll_value + 2),
            color='green',
            fontsize=12,
            fontweight='bold'
        )

    # =========================================================
    # TITLE
    # =========================================================

      ax.set_title(
        graph_title,
        fontsize=18,
        fontweight='bold'
    )

    # =========================================================
    # LABELS
    # =========================================================

      ax.set_xlabel(
        x_label,
        fontsize=12
    )

      ax.set_ylabel(
        'Water Content (%)',
        fontsize=12
    )

    # =========================================================
    # X LIMITS
    # =========================================================

      if method == 'casagrande':

        ax.set_xlim(
            min(x_value) * 0.8,
            max(x_value) * 1.2
        )

      else:

        ax.set_xlim(
            min(x_value) * 0.8,
            max(x_value) * 1.2
        )

    # =========================================================
    # Y LIMITS
    # =========================================================

      y_min = min(
        min(y_value),
        ll_value
    )

      y_max = max(
        max(y_value),
        ll_value
    )

      y_range = y_max - y_min

      if y_range == 0:
        y_range = 10

      ax.set_ylim(
        max(0, y_min - y_range * 0.10),
        y_max + y_range * 0.15
    )

    # =========================================================
    # GRID
    # =========================================================

      if method == 'casagrande':

        # Major logarithmic grid
        ax.xaxis.set_major_locator(
            LogLocator(base=10)
        )

        # Minor logarithmic grid
        ax.xaxis.set_minor_locator(
            LogLocator(
                base=10,
                subs=np.arange(2, 10) * 0.1
            )
        )

      else:

        # Linear cone axis
        ax.xaxis.set_major_locator(
            MultipleLocator(2)
        )

        ax.xaxis.set_minor_locator(
            MultipleLocator(0.5)
        )

    # Y axis
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

    
    # LEGEND
      ax.legend()

   
    # LAYOUT
      plt.tight_layout()

    # SAVE PNG
      buffer = io.BytesIO()

      plt.savefig(
        buffer,
        format='png',
        dpi=100,
        bbox_inches='tight'
    )

      plt.close(fig)
 
      buffer.seek(0)

    # RETURN BASE64
      return base64.b64encode(
        buffer.read()
    ).decode('utf-8')





    def generate_cbr_chart(self, data):

      lines = self.env['mechanical.gsb.cbr.line'].search(
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