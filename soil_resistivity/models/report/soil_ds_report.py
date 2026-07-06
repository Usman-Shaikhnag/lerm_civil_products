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
    _name = 'report.soil_resistivity.soil_resistivity_datasheet'
    _description = 'Soil Resistivity DataSheet'
    
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
        stamp_image = False
        if eln.sample_id and eln.sample_id.lab_location:
            stamp_image = eln.sample_id.lab_location.stamp_image
        return {
            'eln': eln,
            'data' : general_data,
            'parameter' : parameter_data,
            'stamp_image': stamp_image,
        }




class SoilReport(models.AbstractModel):
    _name = 'report.soil_resistivity.soil_resistivity_report'
    _description = 'Soil Resistivity Report'
    
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

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        # qr.add_data(eln.kes_no)
        url = self.env['ir.config_parameter'].sudo().search([('key','=','web.base.url')]).value
        if nabl:
            url = url +'/download_report/nabl/'+ str(eln.id)
        else:
            url = url +'/download_report/nonnabl/'+ str(eln.id)
        qr.add_data(url)
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

        graph_sieve = self._generate_sieve_log_chart(general_data)
        graph_liquid = self.generate_line_chart_liquid(general_data)

        plt.figure(figsize=(12, 6))
        x_values = []
        y_values = []
        # import wdb;wdb.set_trace()
        for line in general_data.heavy_table:
            x_values.append(line.water_content)
            y_values.append(line.dry_density)


        if general_data.heavy_table:
            try:
                max_y = max(y_values)
            except:
                max_y = 100
            try:
                min_y = round(min(y_values),2)
            except:
                min_y = 0
            try:
                # max_x = round(max(x_values),2)
                max_x = x_values[y_values.index(max_y)]
            except:
                max_x = 100
            try:
                min_x = round(min(x_values),2)
            except:
                min_x = 0 
            
            


            # Format max_y and max_x to display 2 digits after the decimal point
            max_y = round(max_y , 2)
            max_x = round(max_x, 2)

    

        
            # Perform cubic spline interpolation
            x_smooth = np.linspace(min(x_values), max(x_values), 100)
            # cs = CubicSpline(x_values, y_values,1)
            # cs = interp1d(x_values, y_values,kind='cubic')
            cs = Akima1DInterpolator(x_values, y_values)

            # Create the line chart with a connected smooth line and markers
            plt.plot(x_smooth, cs(x_smooth), color='red', label='Smooth Curve')
            plt.scatter(x_values, y_values, marker='o', color='blue', s=30, label='Data Points')

            
            # Add a horizontal line with a label(, linestyle='--', label=f'Max Y = {max_y}', linestyle='--', label=f'Max X = {max_x}')
            plt.axhline(y=max_y, color='green',linestyle='--')

            # Add a vertical line with a label
            plt.axvline(x=max_x, color='orange',linestyle='--')

            
            # Set the grid
            ax = plt.gca()
            ax.grid(which='both', linestyle='--', linewidth=0.5)

            # Set the x-axis major and minor tick marks
            ax.xaxis.set_major_locator(ticker.MultipleLocator(1))  # Major gridlines every 1 unit
            ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))  # Minor gridlines every 0.1 unit

            # Set the y-axis tick marks
            # plt.yticks([1.60, 1.62, 1.64, 1.66, 1.68, 1.70, 1.72, 1.74, 1.76, 1.78, 1.80])

            # edit range here
            plt.yticks(np.arange(min_y , round(max_y,2) + 0.2 , (max_y - min_y) / 5))


            if max_x != min_x:
                plt.xticks(np.arange(min_x, round(max(x_values),2) + 1.0, (max_x - min_x) / 5))
            
            plt.gca().yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))
            plt.xlabel('% Water Content ')
            plt.ylabel('Dry density in gm/cc')
            plt.title('% Water Content vs Dry density in gm/cc')
            plt.legend()

            # Save the Matplotlib plot to a BytesIO object
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            graph_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

            # Close the Matplotlib plot to free up resources
            plt.close()
        else:
            graph_image = None
            max_y = 0
            max_x = 0
        
      
 
        plt.figure(figsize=(12, 6))
        cbrx_values = []
        cbry_values = []

        # Check if cbr_table exists and populate cbrx_values and cbry_values
        if general_data.soil_table:
            for line in general_data.soil_table:
                cbrx_values.append(line.penetration)
                cbry_values.append(line.load)

            try:
                max_y = max(cbry_values)
            except ValueError:
                max_y = 100  # Default value if cbry_values is empty
            try:
                min_y = round(min(cbry_values), 2)
            except ValueError:
                min_y = 0
            try:
                max_x = cbrx_values[cbry_values.index(max_y)]
            except ValueError:
                max_x = 100
            try:
                min_x = round(min(cbrx_values), 2)
            except ValueError:
                min_x = 0

            # Format max_y and max_x to display 2 digits after the decimal point
            max_y = round(max_y, 2)
            max_x = round(max_x, 2)

            # Perform cubic spline interpolation if there are enough data points
            if len(cbrx_values) > 1 and len(cbry_values) > 1:
                cbrx_smooth = np.linspace(min(cbrx_values), max(cbrx_values), 100)
                cbrcs = CubicSpline(cbrx_values, cbry_values)

                # Create the line chart with a connected smooth line and markers
                plt.plot(cbrx_smooth, cbrcs(cbrx_smooth), color='red', label='Smooth Curve')
                plt.scatter(cbrx_values, cbry_values, marker='o', color='blue', s=30, label='Data Points')

                # Add horizontal lines with labels
                if len(cbry_values) > 8:  # Ensure indices 5 and 8 exist
                    plt.axhline(y=cbry_values[5], color='green', linestyle='--', label=f'Load at 2.5 mm = {cbry_values[5]}')
                    plt.axhline(y=cbry_values[8], color='green', linestyle='--', label=f'Load at 5 mm = {cbry_values[8]}')

                # Add vertical lines at specific penetration values
                plt.axvline(x=2.5, color='orange', linestyle='--')
                plt.axvline(x=5.0, color='orange', linestyle='--')

                # Set the grid
                ax = plt.gca()
                ax.grid(which='both', linestyle='--', linewidth=0.5)

                # Set the x-axis major and minor tick marks
                ax.xaxis.set_major_locator(ticker.MultipleLocator(1))  # Major gridlines every 1 unit
                ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))  # Minor gridlines every 0.1 unit

                # Set the y-axis tick marks
                plt.yticks(np.arange(min_y, max_y + 0.2, (max_y - min_y) / 5))

                # Set the x-axis tick marks
                if max_x != min_x:
                    plt.xticks(np.arange(min_x, max_x + 1.0, (max_x - min_x) / 5))

                # Set labels and title
                plt.xlabel('Penetration in mm')
                plt.ylabel('Load')
                plt.title('Penetration in mm vs Load')
                plt.legend()

            # Save the Matplotlib plot to a BytesIO object
            buffer2 = BytesIO()
            plt.savefig(buffer2, format='png')
            cbr_graph_image = base64.b64encode(buffer2.getvalue()).decode('utf-8')
            plt.close()
        else:
            cbr_graph_image = None
            cbry_values = []  # Reset to empty list
            cbrx_values = []

        plt.figure(figsize=(12, 6))
        x_values = []
        y_values = []
        # import wdb;wdb.set_trace()
        for line in general_data.omc_table:
            x_values.append(line.water_content1)
            y_values.append(line.dry_density1)


        if general_data.omc_table:
            try:
                max_y = max(y_values)
            except:
                max_y = 100
            try:
                min_y = round(min(y_values),2)
            except:
                min_y = 0
            try:
                # max_x = round(max(x_values),2)
                max_x = x_values[y_values.index(max_y)]
            except:
                max_x = 100
            try:
                min_x = round(min(x_values),2)
            except:
                min_x = 0 
            
            


            # Format max_y and max_x to display 2 digits after the decimal point
            max_y = round(max_y , 2)
            max_x = round(max_x, 2)

    

        
            # Perform cubic spline interpolation
            x_smooth = np.linspace(min(x_values), max(x_values), 100)
            # cs = CubicSpline(x_values, y_values,1)
            # cs = interp1d(x_values, y_values,kind='cubic')
            cs = Akima1DInterpolator(x_values, y_values)

            # Create the line chart with a connected smooth line and markers
            plt.plot(x_smooth, cs(x_smooth), color='red', label='Smooth Curve')
            plt.scatter(x_values, y_values, marker='o', color='blue', s=30, label='Data Points')

            
            # Add a horizontal line with a label(, linestyle='--', label=f'Max Y = {max_y}', linestyle='--', label=f'Max X = {max_x}')
            plt.axhline(y=max_y, color='green',linestyle='--')

            # Add a vertical line with a label
            plt.axvline(x=max_x, color='orange',linestyle='--')

            
            # Set the grid
            ax = plt.gca()
            ax.grid(which='both', linestyle='--', linewidth=0.5)

            # Set the x-axis major and minor tick marks
            ax.xaxis.set_major_locator(ticker.MultipleLocator(1))  # Major gridlines every 1 unit
            ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))  # Minor gridlines every 0.1 unit

            # Set the y-axis tick marks
            # plt.yticks([1.60, 1.62, 1.64, 1.66, 1.68, 1.70, 1.72, 1.74, 1.76, 1.78, 1.80])

            # edit range here
            plt.yticks(np.arange(min_y , round(max_y,2) + 0.2 , (max_y - min_y) / 5))


            if max_x != min_x:
                plt.xticks(np.arange(min_x, round(max(x_values),2) + 1.0, (max_x - min_x) / 5))
            
            plt.gca().yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))
            plt.xlabel('Water Content (%) ')
            plt.ylabel('Dry density in gm/cc')
            plt.title('% DETERMINATION OF COMPACTION OMC / MDD')
            plt.legend()

            # Save the Matplotlib plot to a BytesIO object
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            graph_image1 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            # Close the Matplotlib plot to free up resources
            plt.close()
        else:
            graph_image1 = None
            max_y = 0
            max_x = 0

        stamp_image = False
        if eln.sample_id and eln.sample_id.lab_location:
            stamp_image = eln.sample_id.lab_location.stamp_image
        return {
            'eln': eln,
            'data' : general_data,
            'qrcode': qr_code,
            'stamp_image': stamp_image,
            'nabl' : nabl,
            'graphHeavy' : graph_image,
            'graphSieve': graph_sieve,  # ✅ Added
            'graphliquid': graph_liquid,  # ✅ Added
            'graphLight' : graph_image1,
            
            'mdd': max_y if cbry_values else 0,
            'omc': max_x if cbrx_values else 0,
            'graphCbr': cbr_graph_image,
            'load2': cbry_values[5] if len(cbry_values) > 5 else 0,
            'load5': cbry_values[8] if len(cbry_values) > 8 else 0,
        }



    def _generate_sieve_log_chart(self, data):
        x_values = []
        y_values = []

        for line in data.child_lines:
            if line.cumulative_retained and line.cumulative_retained > 0 and line.passing_percent is not None:
                x_values.append(line.cumulative_retained)
                y_values.append(line.passing_percent)

        if not x_values or not y_values:
            return None

        plt.figure(figsize=(10, 5))
        ax = plt.gca()
        
        # ✅ Log scale X-axis
        ax.set_xscale('log')

        # ✅ Main plot
        ax.plot(x_values, y_values, color='blue', marker='o', linestyle='-', linewidth=2)
        ax.scatter(x_values, y_values, color='red', edgecolors='black', s=60, zorder=5)

        # ✅ Axis labels
        ax.set_xlabel('Cumulative % Weight Retained (Log Scale)', fontsize=12)
        ax.set_ylabel('Passing %', fontsize=12)
        ax.set_title('WET SIEVE ANALYSIS OF SOIL SAMPLE', fontsize=14)

        # ✅ Grid with minor ticks
        ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(1.0, 10.0)*0.1, numticks=100))
        ax.yaxis.set_minor_locator(MultipleLocator(2))
        ax.grid(True, which='both', linestyle='--', linewidth=0.3, color='gray', alpha=0.8)

        # ✅ X-ticks formatting
        ticks = sorted(set(x_values))
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(round(t, 2)) for t in ticks])

        # ✅ Axis limits
        ax.set_xlim(left=min(x_values) / 1.5, right=max(x_values) * 1.5)
        ax.set_ylim(0, 100)

        # ✅ Highlight max passing %
        max_index = y_values.index(max(y_values))
        max_x = x_values[max_index]
        max_y = y_values[max_index]

        ax.axhline(y=max_y, color='red', linestyle='--', linewidth=1)
        ax.axvline(x=max_x, color='red', linestyle='--', linewidth=1)
        ax.plot(max_x, max_y, marker='o', color='red', markersize=8)
        ax.text(max_x * 1.1, max_y + 2, f"{max_x:.2f}, {max_y:.2f}%", color='red')

        # ✅ Save to base64
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode('utf-8')
        


   

    def generate_line_chart_liquid(self,general_data):
        x_value = []
        y_value = []
        for line in general_data.child_liness:
            if line.blwo_no1 and line.water_content is not None:
                x_value.append(line.blwo_no1)
                y_value.append(line.water_content)

        if not x_value or not y_value:
            return False

        plt.figure(figsize=(10, 5))
        ax = plt.gca()

        # ✅ Blue curve with red dots
        ax.plot(x_value, y_value, color='blue', linestyle='-', linewidth=2, label='Curve')
        ax.scatter(x_value, y_value, color='red', edgecolors='black', s=60, zorder=5, label='Points')

        # ✅ Title and axis labels
        ax.set_title('LIQUID LIMIT', fontsize=14)
        ax.set_xlabel('No. of Blows', fontsize=12)
        ax.set_ylabel('Water Content (%)', fontsize=12)

        # ✅ X & Y limits
        max_y = max(y_value)
        y_limit = (int(max_y / 10) + 1) * 10
        ax.set_ylim(bottom=0, top=y_limit)

        max_x = max(x_value)
        x_limit = (int(max_x / 10) + 1) * 10
        ax.set_xlim(left=0, right=x_limit)

        # ✅ Minor ticks: fine spacing
        ax.xaxis.set_minor_locator(MultipleLocator(1))
        ax.yaxis.set_minor_locator(MultipleLocator(1))

        # ✅ Dense grid
        ax.grid(True, which='both', linestyle='--', linewidth=0.3, color='gray', alpha=0.8)

        # ✅ Highlight highest water content
        max_index = y_value.index(max_y)
        highlight_x = x_value[max_index]
        highlight_y = y_value[max_index]

        ax.axhline(y=highlight_y, color='red', linestyle='--', linewidth=1)
        ax.axvline(x=highlight_x, color='red', linestyle='--', linewidth=1)
        ax.plot(highlight_x, highlight_y, marker='o', color='red', markersize=8)
        ax.text(highlight_x + 1, highlight_y + 1, f"{highlight_y:.2f}%", color='red')

        # ✅ Save to image buffer
        buffer = io.BytesIO()
        plt.tight_layout()
        ax.legend()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)

        return base64.b64encode(buffer.read()).decode('utf-8')
