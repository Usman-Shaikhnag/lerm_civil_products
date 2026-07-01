from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
import re
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
import matplotlib.pyplot as plt
from math import ceil



class PileIntegrity(models.Model):
    _name = "pile.integrity"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Pile Integrity")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

  


    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(PileIntegrity, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['pile.integrity'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    # def open_eln_page(self):
    #     # import wdb; wdb.set_trace()

    #     return {
    #             'view_mode': 'form',
    #             'res_model': "lerm.eln",
    #             'type': 'ir.actions.act_window',
    #             'target': 'current',
    #             'res_id': self.eln_ref.id,
                
    #         }

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

          

            if result.parameter.internal_id == '2ab20108-d96d-4acf-bda5-6b71762ae4bb':
                # result.result_char = round(self.average,2)
                result.calculated = True
               
                continue

           

        return {
                'view_mode': 'form',
                'res_model': "lerm.eln",
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.eln_ref.id,
                
            }

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    

        # PILE INTEGRITY TEST
    pile_integrity_name = fields.Char(default="1) PILE INTEGRITY DESCRIPTIONS")

    code_ref = fields.Char(string="Code of Reference :",default="ASTM D5882-16")
    principle_details = fields.Text(string="Principle ",default="The test is based on wave propagation theory.(Wave propagation is any of the ways in which waves travel.) In the sonic test, the top of the pile is hit is heat with the plastic hammer and the reflected waves are recorded by a suitable computerized equipment. From the resulting signal, or reflectogram, one can determine the continuity of the pile.")
    instrument_image = fields.Binary(string="Instrument Image")
    
 
    # procedure_id = fields.One2many('lerm.procedure.master','parent_id')

    procedure = fields.Text(
        string="Procedure",
        default="1. Take 5 points on pile center, north, south, east, and west side\n"
                "2. A small metal/hard rubber hammer is used to\n"
                "3. The shock reflected is recorded through a transducer in a computer disk.\n"
                "4. More than one recording of signals is done until the repeatability of signals is the average of blows."
    )

    influences_result = fields.Text(
        string="Influences Of Test Result",
        default="The top of the pile should consist of clean concrete and free of debris, laitance and bentonite.\n"
                "The test requires the surface preparation to be done properly. For the test to be effective, the top of the pile should\n"
                "consist of clean concrete and free of debris, laitance and bentonite. Testing a pile with a head which was not\n"
                "properly prepared may yield misleading results.\n"
                "For larger diameter piles, it is recommended that the test be carried out at multiple locations on the pile head to\n"
                "accurately determine the results.\n"
                "If pile records are available like bore-logs, cut length, then the results can be fine tuned for greater & more\n"
                "reliable information."
    )

                                                        
    interpretation_result = fields.Text(string="Interpretation Of Test Result",
                                                  default="""This indicates reduction in cross section at a particular area of the pile. If this happens, it means a reduction of the
                                                                        pile load carrying capacity & exposed reinforcements that could get corroded due to ground water and soil
                                                                        chemical attacks. This is indicated by “reduction in impedance” noting in the report. A correlation with the soil
                                                                        investigation report indicated if the reduction in
                                                                        Impedance due to soil strata change or due to change in the diameter of the pile. When a serious reduction is
                                                                        observed, the pile is termed as doubtful.""")

    instrument_description_image = fields.Binary(string="Instrument Description Image")


    pile_integrity_test_name = fields.Char(default=" PILE INTEGRITY TEST")
    pile_integrity_test_table = fields.One2many('pile.integrity.line','parent_id')
    temperature = fields.Float("Temperature °C")
    instrument = fields.Char("Instrument")



    pile_report_upload = fields.Many2many(
        'ir.attachment',
        'temprature_upload_rel1',
        'sample_id',
        'attachment_id',
        string='Report Upload',
        help='Attach multiple reports or PDFs to the sample',
    )



    test_result = fields.Text(string="TEST RESULT:",
     default="""The test results for the 08 Piles tested are attached above. In Annexure- II report is in Tabular form, the detailed
                            test graphs are attached in Annexure- III. Generally following conclusions can be derived from integrity tests which
                            are conducted on the pile shafts.<br></br>
                            1. Total 08 Numbers of piles were tested at site.<br></br>
                            2. This report has been prepared with generally accepted engineering practices and the results of integrity
                            testing as per ASTM- D5882. No other warranty, expressed or implied, is made the findings provided in this
                            report are based on the result of the individual pile tested and information made available to us.""")

    # name = fields.Char(string="Name", default="Default Pile Graph")
    # graph_image = fields.Binary("Graph Image", attachment=True)


    # @api.model
    # def generate_pile_graph(self):
    #     """
    #     Generate an accurate graph with dynamic spacing and proper annotations for each pile.
    #     """
    #     piles = [
    #         {"name": "C2A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.347,
    #         "details": "L/D=6.7 (D=60cm)", "peak": 0.347, "freq": "566.0 Hz", "time": "15:27:42"},
    #         {"name": "C2B", "x": np.linspace(0, 7, 100), "y": np.sin(np.linspace(0, 7, 100)) * 0.463,
    #         "details": "L/D=6.7 (D=60cm)", "peak": 0.463, "freq": "943.3 Hz", "time": "15:25:14"},
    #         {"name": "C5", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.351,
    #         "details": "L/D=7.5 (D=60cm)", "peak": 0.351, "freq": "490.3 Hz", "time": "16:09:40"},
    #         {"name": "C6A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.344,
    #         "details": "L/D=6.8 (D=60cm)", "peak": 0.344, "freq": "513.2 Hz", "time": "15:23:19"},
    #         {"name": "C6B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.377,
    #         "details": "L/D=6.9 (D=60cm)", "peak": 0.377, "freq": "515.9 Hz", "time": "15:23:19"},
    #         {"name": "C8", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.669,
    #         "details": "L/D=11 (D=60cm)", "peak": 0.669, "freq": "1010.7 Hz","time": "15:23:19"},
    #         {"name": "C9A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.540,
    #         "details": "L/D=6.7 (D=60cm)", "peak": 0.540, "freq": "600.3 Hz","time": "15:23:19"},
    #         {"name": "C9B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.453,
    #         "details": "L/D=7.2 (D=60cm)", "peak": 0.453, "freq": "434.4 Hz","time": "15:23:19"},
    #         {"name": "C9D", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.488,
    #         "details": "L/D=7.2 (D=60cm)", "peak": 0.488, "freq": "604.0 Hz","time": "15:23:19"},
    #         {"name": "C10B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.415,
    #         "details": "L/D=7 (D=60cm)", "peak": 0.415, "freq": "1088.5 Hz","time": "15:23:19"},
    #         {"name": "C10C", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.346,
    #         "details": "L/D=6.9 (D=60cm)", "peak": 0.346, "freq": "401.0 Hz","time": "15:23:19"},
    #         {"name": "C13A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.287,
    #         "details": "L/D=8.5 (D=60cm)", "peak": 0.287, "freq": "432.5 Hz","time": "15:23:19"},
    #         {"name": "C14A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.664,
    #         "details": "L/D=7 (D=60cm)", "peak": 0.664, "freq": "575.9 Hz","time": "15:23:19"},
    #         {"name": "C14B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.282,
    #         "details": "L/D=6.7 (D=60cm)", "peak": 0.282, "freq": "467.2 Hz","time": "15:23:19"},
    #         {"name": "C14C", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.774,
    #         "details": "L/D=7.2 (D=60cm)", "peak": 0.774, "freq": "589.6 Hz","time": "15:23:19"},
    #         {"name": "C17A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.617,
    #         "details": "L/D=8.5 (D=60cm)", "peak": 0.617, "freq": "467.2 Hz","time": "15:23:19"},
    #         {"name": "C18A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.378,
    #         "details": "L/D=6.8 (D=60cm)", "peak": 0.378, "freq": "448.2 Hz","time": "15:23:19"},
    #         {"name": "C20A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.454,
    #         "details": "L/D=9.7 (D=60cm)", "peak": 0.454, "freq": "385.4 Hz","time": "15:23:19"},
    #         {"name": "C20B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.720,
    #         "details": "L/D=7 (D=60cm)", "peak": 0.720, "freq": "739.2 Hz","time": "15:23:19"},
    #         {"name": "C20C", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.528,
    #         "details": "L/D=9.7 (D=60cm)", "peak": 0.528, "freq": "811.9 Hz","time": "15:23:19"},
    #         {"name": "C21B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.330,
    #         "details": "L/D=6.7 (D=60cm)", "peak": 0.330, "freq": "660.3 Hz","time": "15:23:19"},
    #         {"name": "C21C", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.322,
    #         "details": "L/D=6.5 (D=60cm)", "peak": 0.322, "freq": "593.1 Hz","time": "15:23:19"},
    #         # Add more pile data here if needed
    #     ]

    #     # Dynamically adjust figure height based on the number of piles
    #     num_piles = len(piles)
    #     fig_height = num_piles * 1.30  # Adjust height scaling factor as needed

    #     # Set up the figure with subplots
    #     fig, axes = plt.subplots(num_piles, 1, figsize=(8, fig_height), sharex=True)
    #     fig.subplots_adjust(hspace=0.8)  # Increase space between plots

    #     for ax, pile in zip(axes, piles):
    #         # Plot the data
    #         ax.plot(pile["x"], pile["y"], label=pile["name"], color='black')

    #         # Get current y-limits
    #         y_min, y_max = ax.get_ylim()

    #         # Add dashed lines for the limits, within the y-axis limits
    #         ax.axhline(y=min(max(pile["peak"], y_min), y_max), color='red', linestyle='--', linewidth=0.8)
    #         ax.axhline(0, color='red', linestyle='--', linewidth=0.8)

    #         # Extend the blue line to the x limits
    #         ax.set_xlim(0, max(pile["x"]))  # Ensure the blue line spans the x-axis range

    #         # Annotate the graph
    #         ax.set_title(f"Pile: {pile['name']} - {pile['details']}", fontsize=10, weight='bold')
    #         ax.annotate(f"L/D={pile['details']}\n{pile['peak']} cm/s ({pile['freq']})",
    #                     xy=(max(pile["x"]) * 0.7, pile['peak'] - 0.1), xycoords='data',
    #                     fontsize=8, color='black', ha='center')
    #         ax.text(max(pile["x"]) * 0.05, -pile["peak"] * 0.9, f"{pile['time']}", fontsize=8, va='top', ha='left')

    #         # Axis labels and grid
    #         ax.set_ylabel("cm/s")
    #         ax.grid(True, linestyle='--', alpha=0.6)

    #     # Shared X-axis label
    #     axes[-1].set_xlabel("Time (s)")

    #     # Optimize layout
    #     plt.tight_layout()

    #     # Save the graph to a binary field
    #     buf = BytesIO()
    #     plt.savefig(buf, format='png', dpi=300)
    #     buf.seek(0)
    #     graph_image_base64 = base64.b64encode(buf.read()).decode()
    #     buf.close()
    #     plt.close()

    #     # Create a record with the graph
    #     self.write({
    #         'graph_image': graph_image_base64,
    #     })
    
    
  
    
    # def regenerate_graph(self):
    #     """
    #     Regenerate the pile graph manually.
    #     """
    #     self.generate_pile_graph()




# class ProcedureMaster(models.Model):
#     _name = "lerm.procedure.master"
#     _description = "Procedure Master"

#     parent_id = fields.Many2one('pile.integrity', string="Parent Id")

#     name = fields.Char(string="Procedure")
#     serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)

#     @api.model
#     def create(self, vals):
#         # Set the serial_no based on the existing records for the same parent
#         if vals.get('parent_id'):
#             existing_records = self.search([('parent_id', '=', vals['parent_id'])])
#             if existing_records:
#                 max_serial_no = max(existing_records.mapped('serial_no'))
#                 vals['serial_no'] = max_serial_no + 1

#         return super(ProcedureMaster, self).create(vals)

#     def _reorder_serial_numbers(self):
#         # Reorder the serial numbers based on the positions of the records in child_lines
#         records = self.sorted('id')
#         for index, record in enumerate(records):
#             record.serial_no = index + 1

class PileIntegrityLine(models.Model):
    _name = "pile.integrity.line"
    _description = "Pile Integrity Line"

    parent_id = fields.Many2one('pile.integrity', string="Parent Id")

    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    pile_id = fields.Char(string="Pile ID")
    doc = fields.Date(string="DOC")
    pile_dia = fields.Integer(string="Dia (MM)")
    cut_off  = fields.Float(string="Cut Off Length (M)")
    shaft_cross  = fields.Char(string="Shaft Cross-Section & soil Changes")

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PileIntegrityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class PileIntegrityReport(models.AbstractModel):
    _name = 'report.pile_integrity.pile_integrity_report'
    _description = 'Steel TMT Bar'
    
    @api.model
    def _get_report_values(self, docids, data):
        inreport_value = data.get('inreport', None)
        nabl = data.get('nabl')
        
        if data.get('report_wizard') == True:
            eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data['sample'])])
        elif 'active_id' in data['context']:
            eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data['context']['active_id'])])
        else:
            eln = self.env['lerm.eln'].sudo().browse(docids)
        
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(eln.kes_no)
        qr.make(fit=True)
        qr_image = qr.make_image()

        # Convert the QR code image to base64 string
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_image_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Generate the graph
        # piles = [
        #     {"name": "C2A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.347,
        #     "details": "L/D=6.7 (D=60cm)", "peak": 0.347, "freq": "566.0 Hz", "time": "15:27:42"},
        #     {"name": "C2B", "x": np.linspace(0, 7, 100), "y": np.sin(np.linspace(0, 7, 100)) * 0.463,
        #     "details": "L/D=6.7 (D=60cm)", "peak": 0.463, "freq": "943.3 Hz", "time": "15:25:14"},
        #     {"name": "C5", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.351,
        #     "details": "L/D=7.5 (D=60cm)", "peak": 0.351, "freq": "490.3 Hz", "time": "16:09:40"},
        #     {"name": "C6A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.344,
        #     "details": "L/D=6.8 (D=60cm)", "peak": 0.344, "freq": "513.2 Hz", "time": "15:23:19"},
        #     {"name": "C6B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.377,
        #     "details": "L/D=6.9 (D=60cm)", "peak": 0.377, "freq": "515.9 Hz", "time": "15:23:19"},
        #     {"name": "C8", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.669,
        #     "details": "L/D=11 (D=60cm)", "peak": 0.669, "freq": "1010.7 Hz","time": "15:23:19"},
        #     {"name": "C9A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.540,
        #     "details": "L/D=6.7 (D=60cm)", "peak": 0.540, "freq": "600.3 Hz","time": "15:23:19"},
        #     {"name": "C9B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.453,
        #     "details": "L/D=7.2 (D=60cm)", "peak": 0.453, "freq": "434.4 Hz","time": "15:23:19"},
        #     {"name": "C9D", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.488,
        #     "details": "L/D=7.2 (D=60cm)", "peak": 0.488, "freq": "604.0 Hz","time": "15:23:19"},
        #     {"name": "C10B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.415,
        #     "details": "L/D=7 (D=60cm)", "peak": 0.415, "freq": "1088.5 Hz","time": "15:23:19"},
        #     {"name": "C10C", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.346,
        #     "details": "L/D=6.9 (D=60cm)", "peak": 0.346, "freq": "401.0 Hz","time": "15:23:19"},
        #     {"name": "C13A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.287,
        #     "details": "L/D=8.5 (D=60cm)", "peak": 0.287, "freq": "432.5 Hz","time": "15:23:19"},
        #     {"name": "C14A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.664,
        #     "details": "L/D=7 (D=60cm)", "peak": 0.664, "freq": "575.9 Hz","time": "15:23:19"},
        #     {"name": "C14B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.282,
        #     "details": "L/D=6.7 (D=60cm)", "peak": 0.282, "freq": "467.2 Hz","time": "15:23:19"},
        #     {"name": "C14C", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.774,
        #     "details": "L/D=7.2 (D=60cm)", "peak": 0.774, "freq": "589.6 Hz","time": "15:23:19"},
        #     {"name": "C17A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.617,
        #     "details": "L/D=8.5 (D=60cm)", "peak": 0.617, "freq": "467.2 Hz","time": "15:23:19"},
        #     {"name": "C18A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.378,
        #     "details": "L/D=6.8 (D=60cm)", "peak": 0.378, "freq": "448.2 Hz","time": "15:23:19"},
        #     {"name": "C20A", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.454,
        #     "details": "L/D=9.7 (D=60cm)", "peak": 0.454, "freq": "385.4 Hz","time": "15:23:19"},
        #     {"name": "C20B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.720,
        #     "details": "L/D=7 (D=60cm)", "peak": 0.720, "freq": "739.2 Hz","time": "15:23:19"},
        #     {"name": "C20C", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.528,
        #     "details": "L/D=9.7 (D=60cm)", "peak": 0.528, "freq": "811.9 Hz","time": "15:23:19"},
        #     {"name": "C21B", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.330,
        #     "details": "L/D=6.7 (D=60cm)", "peak": 0.330, "freq": "660.3 Hz","time": "15:23:19"},
        #     {"name": "C21C", "x": np.linspace(0, 5, 100), "y": np.sin(np.linspace(0, 5, 100)) * 0.322,
        #     "details": "L/D=6.5 (D=60cm)", "peak": 0.322, "freq": "593.1 Hz","time": "15:23:19"},
        #     # Add more pile data here if needed
        # ]

        # # Dynamically adjust figure height based on the number of piles
        # num_piles = len(piles)
        # fig_height = num_piles * 1.30  # Adjust height scaling factor as needed

        # # Set up the figure with subplots
        # fig, axes = plt.subplots(num_piles, 1, figsize=(8, fig_height), sharex=True)
        # fig.subplots_adjust(hspace=0.8)  # Increase space between plots

        # for ax, pile in zip(axes, piles):
        #     # Plot the data
        #     ax.plot(pile["x"], pile["y"], label=pile["name"], color='black')

        #     # Get current y-limits
        #     y_min, y_max = ax.get_ylim()

        #     # Add dashed lines for the limits, within the y-axis limits
        #     ax.axhline(y=min(max(pile["peak"], y_min), y_max), color='red', linestyle='--', linewidth=0.8)
        #     ax.axhline(0, color='red', linestyle='--', linewidth=0.8)

        #     # Extend the blue line to the x limits
        #     ax.set_xlim(0, max(pile["x"]))  # Ensure the blue line spans the x-axis range

        #     # Annotate the graph
        #     ax.set_title(f"Pile: {pile['name']} - {pile['details']}", fontsize=10, weight='bold')
        #     ax.annotate(f"L/D={pile['details']}\n{pile['peak']} cm/s ({pile['freq']})",
        #                 xy=(max(pile["x"]) * 0.7, pile['peak'] - 0.1), xycoords='data',
        #                 fontsize=8, color='black', ha='center')
        #     ax.text(max(pile["x"]) * 0.05, -pile["peak"] * 0.9, f"{pile['time']}", fontsize=8, va='top', ha='left')

        #     # Axis labels and grid
        #     ax.set_ylabel("cm/s")
        #     ax.grid(True, linestyle='--', alpha=0.6)

        # # Shared X-axis label
        # axes[-1].set_xlabel("Time (s)")

        # # Optimize layout
        # plt.tight_layout()

        # Save the graph to a binary field
  
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300)
        buf.seek(0)
        graph_image_base64 = base64.b64encode(buf.read()).decode()
        buf.close()
        plt.close()
        

        model_id = eln.model_id
        model_name = eln.material.product_based_calculation[0].ir_model.name if eln.material.product_based_calculation else None

        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)



        return {
            'eln': eln,
            'data': general_data,
            'qrcode': qr_image_base64,
            # 'graph': graph_image_base64,
            'stamp': inreport_value,
            'nabl': nabl,
           
        }
    