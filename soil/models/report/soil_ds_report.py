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

class SoilDatasheet(models.AbstractModel):
    _name = 'report.soil.soil_datasheet1'
    _description = 'Soil DataSheet 1'
    
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
    _name = 'report.soil.soil_report1'
    _description = 'Soil Report 1'
    
    @api.model
    def _get_report_values(self, docids, data):
        # eln = self.env['lerm.eln'].sudo().browse(docids)
        nabl = data.get('nabl')
        fromEln = data.get('fromEln')
        inreport_value = data.get('inreport', None)
        if data.get('report_wizard') == True:
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['sample'])])
        elif fromEln == False:
            if 'active_id' in data.get('context',{}):
                eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
            else:
                eln = self.env['lerm.eln'].sudo().browse(docids)
        else:
            if 'active_id' in data.get('context',{}):
                eln = self.env['lerm.eln'].sudo().search([('id','=',data['context']['active_id'])])
            else:
                eln = self.env['lerm.eln'].sudo().browse(docids)
        # if 'active_id' in data['context']:
        #     eln = self.env['lerm.eln'].sudo().search([('sample_id','=',data['context']['active_id'])])
        # else:
        #     eln = self.env['lerm.eln'].sudo().browse(docids) 
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
            
    



        plt.figure(figsize=(12, 6))
        x_values = []
        y_values = []
        # import wdb;wdb.set_trace()
        for line in general_data.heavy_table:
            x_values.append(line.moisture)
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
            plt.xlabel('% Moisture')
            plt.ylabel('Dry density in gm/cc')
            plt.title('% Moisture vs Dry density in gm/cc')
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
        
        return {
            'eln': eln,
            'data' : general_data,
            'qrcode': qr_code,
            'stamp' : inreport_value,
            'nabl' : nabl,
            'graphHeavy' : graph_image,
            # 'mdd' : max_y,
            # 'omc' : max_x,
            # 'graphCbr' : cbr_graph_image,
            # 'load2' : cbry_values[5] if cbry_values else 0,
            # 'load5' : cbry_values[8] if cbry_values else 0,
            'mdd': max_y if cbry_values else 0,
            'omc': max_x if cbrx_values else 0,
            'graphCbr': cbr_graph_image,
            'load2': cbry_values[5] if len(cbry_values) > 5 else 0,
            'load5': cbry_values[8] if len(cbry_values) > 8 else 0,
        }
