from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re
import matplotlib.pyplot as plt
import io
import base64
import matplotlib.ticker as ticker
import numpy as np
import math
from scipy.interpolate import CubicSpline , interp1d , Akima1DInterpolator
from scipy.optimize import minimize_scalar
from io import BytesIO


import logging
_logger = logging.getLogger(__name__)

class ConcreteDesign(models.Model):
    _name = "mechanical.concrete.design1"
    _inherit = "lerm.eln"
    _description = 'mechanical.concrete.design1'
    _rec_name = "name"

    name = fields.Char("Name",default="CONCRETE MIX DESIGN FOR GRADE OF M-40")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    size_id = fields.Many2one('lerm.size.line',compute="_compute_size_id")


    @api.depends("eln_ref")
    def _compute_size_id(self):
        for record in self:
            print("Size iD",record.eln_ref.size_id)
            record.size_id = record.eln_ref.size_id.id

    
    # # Parameter Name = 1) CONCRETE MIX DESIGN FOR GRADE OF M-40

    child_lines_concrete_design = fields.One2many('mechanical.concrete.design.line1','parent_id',string=" CONCRETE MIX DESIGN",default=lambda self: self._default_concrete_child_lines())

    @api.model
    def _default_concrete_child_lines(self):
        default_lines = [
            (0, 0, { 'abstract': 'kg/m³'}),
            (0, 0, { 'abstract': 'Sp Gr.'}),
            (0, 0, { 'abstract': 'Mix Grade'}),  # Line 3 with display value
            (0, 0, {'abstract': 'Std Dev.'})
        ]
        return default_lines

    total_kg_per_m3 = fields.Float(string="Total Kg/M3", compute="_compute_total_kg_per_m3", store=True)
    sp_gr = fields.Float(string="Sp Gr")
    mix_grade = fields.Float(string="Mix Grade", compute="_compute_mix_grade", store=True,digits=(12,3))

    @api.depends('child_lines_concrete_design.kg_per_m3')
    def _compute_total_kg_per_m3(self):
        for record in self:
            record.total_kg_per_m3 = sum(line.kg_per_m3 for line in record.child_lines_concrete_design)

    @api.depends('sp_gr', 'total_kg_per_m3')
    def _compute_mix_grade(self):
        for record in self:
            # Ensure total_kg_per_m3 is not zero to avoid division by zero
            if record.total_kg_per_m3 != 0:
                record.mix_grade = record.sp_gr / record.total_kg_per_m3
            else:
                record.mix_grade = 0.0  # or set it to None if you prefer

   
    # kgm3_1 = fields.Float(string="Abstract") 
    # spgr_1 = fields.Float(string="Cement")
    # mixgrade_1 = fields.Float(string="Slag")
    # std_dev_1 = fields.Float(string="Mirosilica")
    # # wcf_1 = fields.Float(string="W/(C+F)")
    # # cf_1 = fields.Float(string="(C+F)")
    # # rsand_1 = fields.Float(string="R/SAND")
    # # csand_1 = fields.Float(string="C/SAND")
    # # 10_1 = fields.Float(string="10 MM")
    # # _1 = fields.Float(string="20 MM")
    # # csand_1 = fields.Float(string="C/SAND")

    # kgm3_2 = fields.Float(string="Abstract") 
    # kgm3_3 = fields.Float(string="Abstract") 
    # kgm3_4 = fields.Float(string="Abstract") 
    # kgm3_5 = fields.Float(string="Abstract") 
    # kgm3_6 = fields.Float(string="Abstract") 
    # kgm3_7 = fields.Float(string="Abstract") 
    # kgm3_8 = fields.Float(string="Abstract") 
    # kgm3_9 = fields.Float(string="Abstract") 

    # A. DESIGN STIPULATIONS.
 
    design_stipulations_name = fields.Char(default="A. DESIGN STIPULATIONS")
    design_stipulations_visible = fields.Boolean(compute="_compute_visible")

    design_stipulations_com = fields.Float('CHARACTERISTIC COMPRESSIVE STRENGTH AT 28 DAYS')
    design_stipulations_max_size = fields.Float('MAXIMUM SIZE OF AGGREGATE',compute="_compute_density_calculated")
    design_stipulations_work = fields.Char('WORKABILITY (SLUMP)')
    design_stipulations_exposure = fields.Char('TYPE OF EXPOSURE')
    design_stipulations_cement = fields.Float('MINIMUM CEMENT CONTENT')
    design_stipulations_water = fields.Float('MAXIMUM WATER - CEMENT RATIO')
    design_stipulations_tolerance = fields.Float('TOLERANCE FACTOR (t)')
    design_stipulations_admicture = fields.Char('CHEMICAL ADMIXTURE TYPE')



    @api.depends('child_lines_concrete_design.slag')
    def _compute_density_calculated(self):
        for record in self:
            if len(record.child_lines_concrete_design) >= 2:
                slag_value_str = record.child_lines_concrete_design[2].slag  # Fetch the string value of slag
                
                if slag_value_str:
                    match = re.search(r'\d+(\.\d+)?', slag_value_str)  # Match integer or float
                    if match:
                        slag_value = round(float(match.group()), 2)
                    else:
                        slag_value = 0.0
                else:
                    slag_value = 0.0

                record.design_stipulations_max_size = slag_value
            else:
                record.design_stipulations_max_size = 0.0


# B. TEST DATA FOR CONCRETE INGREDIENTS.

    test_data_name = fields.Char(default="B. TEST DATA FOR CONCRETE INGREDIENTS")
    test_data_visible = fields.Boolean(compute="_compute_visible")

    test_data_gravity_cement = fields.Float('SPECIFIC  GRAVITY OF CEMENT',compute="_compute_cement_fetch")
    test_data_gravity_flyash = fields.Float('SPECIFIC  GRAVITY OF FLYASH',compute="_compute_flyash_fetch")
    test_data_admixture = fields.Char('CHEMICAL ADMIXTURE ')
    test_data_flyash = fields.Char('FLYASH CONTENT PERCENTAGE',compute="_compute_flyash1_fetch")


    @api.depends('child_lines_concrete_design.cement_display')
    def _compute_cement_fetch(self):
        for record in self:
            if len(record.child_lines_concrete_design) >= 2:
                cement_display_value_str = record.child_lines_concrete_design[1].cement_display  # Fetch the string value of cement_display
                
                if cement_display_value_str:
                    match = re.search(r'\d+(\.\d+)?', cement_display_value_str)  # Match integer or float
                    if match:
                        cement_display_value = round(float(match.group()), 2)
                    else:
                        cement_display_value = 0.0
                else:
                    cement_display_value = 0.0

                record.test_data_gravity_cement = cement_display_value
            else:
                record.test_data_gravity_cement = 0.0

    @api.depends('child_lines_concrete_design.slag')
    def _compute_flyash_fetch(self):
        for record in self:
            if len(record.child_lines_concrete_design) >= 2:
                slag_value_str = record.child_lines_concrete_design[1].slag  # Fetch the string value of slag
                
                if slag_value_str:
                    match = re.search(r'\d+(\.\d+)?', slag_value_str)  # Match integer or float
                    if match:
                        slag_value = round(float(match.group()), 2)
                    else:
                        slag_value = 0.0
                else:
                    slag_value = 0.0

                record.test_data_gravity_flyash = slag_value
            else:
                record.test_data_gravity_flyash = 0.0




    @api.depends('child_lines_concrete_design.slag', 'total_kg_per_m3')
    def _compute_flyash1_fetch(self):
        for record in self:
            if len(record.child_lines_concrete_design) >= 2:
                slag_value_str = record.child_lines_concrete_design[0].slag  # Fetch the string value of slag

                # Parse and convert slag_value_str to a float
                if slag_value_str:
                    match = re.search(r'\d+(\.\d+)?', slag_value_str)
                    slag_value = round(float(match.group()), 2) if match else 0.0
                else:
                    slag_value = 0.0

                # Access total_kg_per_m3 directly from record
                total_kg_per_m3 = record.total_kg_per_m3

                # Calculate slag_value / total_kg_per_m3 and set in test_data_flyash as a percentage
                if total_kg_per_m3:
                    record.test_data_flyash = f"{round(slag_value / total_kg_per_m3 * 100, 2)}%"  # Format as percentage
                else:
                    record.test_data_flyash = "0.0%"  # Default to 0.0% if total_kg_per_m3 is 0 or None
            else:
                record.test_data_flyash = "0.0%"  # Default to 0.0% if there are not enough child lines



# SPECIFIC GRAVITY & WATER ABSORPTION OF COARSE & FINE AGGREGATE (SSD)

    child_lines_concrete_design_material = fields.One2many('mechanical.concrete.design.material.line1','parent_id',string="Material Table")

    material_name = fields.Char(default="SPECIFIC GRAVITY & WATER ABSORPTION OF COARSE & FINE AGGREGATE (SSD)")

    # def _default_material_lines(self):
    #     return []

      # Sieve Analysis 
    # sieve_analysis_name = fields.Char("Name",default=" C. SIEVE ANALYSIS OF COARSE & FINE  AGGREGATE")
    # sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")


    sieve_analysis_name = fields.Char("Name",default=" C. SIEVE ANALYSIS OF COARSE & FINE  AGGREGATE")
    sieve_visible20mm = fields.Boolean("Sieve Analysis Visible",compute="_compute_size_20mm")

    # Sieve size 20 MM
    sieve_analysis_child_lines_20mm = fields.One2many('mechanical.concrete.design.sieve.20mm.line1','parent_id',string="Parameter",default=lambda self: self._default_sieve_analysis_child_lines20mm())
    total_sieve_analysis20mm = fields.Float(string="Total",compute="_compute_total_sieve20mm")
    size_20mm = fields.Char(string="Aggregate Size",compute="_compute_size_20mm")



    @api.depends('child_lines_concrete_design_material.material')
    def _compute_size_20mm(self):
        for record in self:
            # Check if any child line has material set to "20MM"
            has_20mm_material = any(line.material == "20MM" for line in record.child_lines_concrete_design_material)
            
            # Set sieve_visible20mm to True if "20MM" material exists, else False
            record.sieve_visible20mm = has_20mm_material
            
            # Set size_20mm based on the value of sieve_visible20mm
            record.size_20mm = "20MM" if has_20mm_material else ""



    

    @api.model
    def _default_sieve_analysis_child_lines20mm(self):
        default_lines = [
            (0, 0, {'sieve_size': '40 '}),
            (0, 0, {'sieve_size': '20 '}),
            (0, 0, {'sieve_size': '10'}),
            (0, 0, {'sieve_size': '4.75 '}),
            (0, 0, {'sieve_size': 'Bal '})
           
        ]
        return default_lines



    def calculate20mm(self): 
        for record in self:
            for line in record.sieve_analysis_child_lines_20mm:
                print("Rows",str(line.percent_retained))
                previous_line = line.serial_no - 1
                if previous_line == 0:
                    line.write({'cumulative_retained': line.percent_retained})
                    line.write({'passing_percent': 100})

                else:
                    previous_line_record = self.env['mechanical.concrete.design.sieve.20mm.line1'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
                    line.write({'cumulative_retained': previous_line_record + line.percent_retained})
                    line.write({'passing_percent': 100-(previous_line_record + line.percent_retained)})
                    print("Previous Cumulative",previous_line_record)



    @api.depends('sieve_analysis_child_lines_20mm.wt_retained')
    def _compute_total_sieve20mm(self):
        for record in self:
            print("recordd",record)
            record.total_sieve_analysis20mm = sum(record.sieve_analysis_child_lines_20mm.mapped('wt_retained'))


    graph_image_20mm = fields.Binary("Line Chart", compute="_compute_graph_image_20mm", store=True)



    def generate_line_chart_20mm(self):
        # Sample data - Replace these lists with actual data from your model
        sieve_sizes20mm = []
        up_values20mm = []
        ll_values20mm = []
        passing_percent_values20mm = []

        for line in self.sieve_analysis_child_lines_20mm:
            sieve_sizes20mm.append(line.sieve_size)
            up_values20mm.append(line.up)
            ll_values20mm.append(line.ll)
            passing_percent_values20mm.append(line.passing_percent)

        # Ensure all lists have data and are of equal length
        if not (len(sieve_sizes20mm) == len(up_values20mm) == len(ll_values20mm) == len(passing_percent_values20mm)):
            print("Data lists have mismatched lengths or are empty")
            return None

        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(sieve_sizes20mm, up_values20mm, marker='o', label='UP', color='blue')
        ax.plot(sieve_sizes20mm, ll_values20mm, marker='o', label='LL', color='orange')
        ax.plot(sieve_sizes20mm, passing_percent_values20mm, marker='o', label='% Passing', color='green')

        # Set labels and title
        ax.set_xlabel('Size (mm)')
        ax.set_ylabel('% Passing')
        ax.set_title('Grading of 20 mm')

    
        ax.set_xlim(min(sieve_sizes20mm), max(sieve_sizes20mm))  # Set x-axis from min to max sieve sizes
        ax.set_ylim(0, 100)  # % Passing ranges from 0 to 100

        ax.grid(True)

        # Add legend
        ax.legend()

        ax.set_xticks(sieve_sizes20mm)

        # Create the table below the plot
        table_data = [
            ["UP"] + list(up_values20mm),
            ["LL"] + list(ll_values20mm),
            ["% Passing"] + list(passing_percent_values20mm)
        ]
        column_labels = ["Size (mm)"] + list(sieve_sizes20mm)

        table = ax.table(cellText=table_data, colLabels=column_labels, cellLoc='center', loc='bottom', bbox=[0, -0.4, 1, 0.2])

        table.auto_set_font_size(False)  # Disable automatic font size adjustment
        table.set_fontsize(8)  # Set a smaller font size for better readability

        # Adjust cell height and width if necessary
        for (i, j), cell in table.get_celld().items():
            if i == 0:  # Set the header row
                cell.set_text_props(weight='bold')
                cell.set_fontsize(9)
            else:
                cell.set_fontsize(8)
            cell.set_height(0.04)  # Adjust the height of the rows
            cell.set_width(0.1)  # Adjust the width of the columns

        # Adjust layout to make space for the table without overlapping the plot
        plt.subplots_adjust(bottom=0.35)  # Adjust the bottom space for the table


        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()  # Close the plot to free up resources
        buffer.seek(0)

        # Convert the chart image to base64
        chart_image20mm = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()  # Close the buffer to free up memory
        return chart_image20mm

    @api.depends('sieve_analysis_child_lines_20mm')
    def _compute_graph_image_20mm(self):
        try:
            for record in self:
                chart_image20mm = record.generate_line_chart_20mm()
                record.graph_image_20mm = chart_image20mm
        except:
            pass 


    
                
    # Sieve Analysis  10 MM
    
    sieve_analysis_child_lines = fields.One2many('mechanical.concrete.design.sieve.analysis.line1','parent_id',string="Parameter",default=lambda self: self._default_sieve_analysis_child_lines10mm())
    total_sieve_analysis = fields.Float(string="Total",compute="_compute_total_sieve")
    sieve_visible10mm = fields.Boolean("Sieve Analysis Visible",compute="_compute_size_10mm")
    size_10mm = fields.Char(string="Aggregate Size",compute="_compute_size_10mm")

    @api.depends('child_lines_concrete_design_material.material')
    def _compute_size_10mm(self):
        for record in self:
            # Check if any child line has material set to "20MM"
            has_20mm_material = any(line.material == "10MM" for line in record.child_lines_concrete_design_material)
            
            # Set sieve_visible20mm to True if "20MM" material exists, else False
            record.sieve_visible10mm = has_20mm_material
            
            # Set size_20mm based on the value of sieve_visible20mm
            record.size_10mm = "10MM" if has_20mm_material else ""


    @api.model
    def _default_sieve_analysis_child_lines10mm(self):
        default_lines = [
            (0, 0, {'sieve_size': '12.5 '}),
            (0, 0, {'sieve_size': '10 '}),
            (0, 0, {'sieve_size': '4.75'}),
            (0, 0, {'sieve_size': '2.36 '}),
            (0, 0, {'sieve_size': 'Bal '})
           
        ]
        return default_lines





    def calculate_sieve(self): 
        for record in self:
            for line in record.sieve_analysis_child_lines:
                print("Rows",str(line.percent_retained))
                previous_line = line.serial_no - 1
                if previous_line == 0:
                    if line.percent_retained == 0:
                        # print("Percent retained 0",line.percent_retained)
                        line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2)})
                        line.write({'passing_percent': 100 })
                    else:
                        # print("Percent retained else",line.percent_retained)
                        line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2)})
                        line.write({'passing_percent': round(100 -line.percent_retained - line.percent_retained,2)})
                else:
                    previous_line_record = self.env['mechanical.concrete.design.sieve.analysis.line1'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
                    line.write({'cumulative_retained': previous_line_record + line.percent_retained})
                    line.write({'passing_percent': round(100-(previous_line_record + line.percent_retained),2)})
                    print("Previous Cumulative",previous_line_record)


    @api.depends('sieve_analysis_child_lines.wt_retained')
    def _compute_total_sieve(self):
        for record in self:
            print("recordd",record)
            record.total_sieve_analysis = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))

    graph_image_10mm = fields.Binary("Line Chart", compute="_compute_graph_image_10mm", store=True)



    def generate_line_chart_10mm(self):
        # Sample data - Replace these lists with actual data from your model
        sieve_sizes = []
        up_values = []
        ll_values = []
        passing_percent_values = []

        for line in self.sieve_analysis_child_lines:
            sieve_sizes.append(line.sieve_size)
            up_values.append(line.up)
            ll_values.append(line.ll)
            passing_percent_values.append(line.passing_percent)

        # Ensure all lists have data and are of equal length
        if not (len(sieve_sizes) == len(up_values) == len(ll_values) == len(passing_percent_values)):
            print("Data lists have mismatched lengths or are empty")
            return None

        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(sieve_sizes, up_values, marker='o', label='UP', color='blue')
        ax.plot(sieve_sizes, ll_values, marker='o', label='LL', color='orange')
        ax.plot(sieve_sizes, passing_percent_values, marker='o', label='% Passing', color='green')

        # Set labels and title
        ax.set_xlabel('Size (mm)')
        ax.set_ylabel('% Passing')
        ax.set_title('Grading of 10 mm')

    
        ax.set_xlim(min(sieve_sizes), max(sieve_sizes))  # Set x-axis from min to max sieve sizes
        ax.set_ylim(0, 100)  # % Passing ranges from 0 to 100

        ax.grid(True)

        # Add legend
        ax.legend()

        ax.set_xticks(sieve_sizes)

        # Create the table below the plot
        table_data = [
            ["UP"] + list(up_values),
            ["LL"] + list(ll_values),
            ["% Passing"] + list(passing_percent_values)
        ]
        column_labels = ["Size (mm)"] + list(sieve_sizes)

        table = ax.table(cellText=table_data, colLabels=column_labels, cellLoc='center', loc='bottom', bbox=[0, -0.4, 1, 0.2])

        table.auto_set_font_size(False)  # Disable automatic font size adjustment
        table.set_fontsize(8)  # Set a smaller font size for better readability

        # Adjust cell height and width if necessary
        for (i, j), cell in table.get_celld().items():
            if i == 0:  # Set the header row
                cell.set_text_props(weight='bold')
                cell.set_fontsize(9)
            else:
                cell.set_fontsize(8)
            cell.set_height(0.04)  # Adjust the height of the rows
            cell.set_width(0.1)  # Adjust the width of the columns

        # Adjust layout to make space for the table without overlapping the plot
        plt.subplots_adjust(bottom=0.35)  # Adjust the bottom space for the table


        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()  # Close the plot to free up resources
        buffer.seek(0)

        # Convert the chart image to base64
        chart_image = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()  # Close the buffer to free up memory
        return chart_image

    @api.depends('sieve_analysis_child_lines')
    def _compute_graph_image_10mm(self):
        try:
            for record in self:
                chart_image = record.generate_line_chart_10mm()
                record.graph_image_10mm = chart_image
        except:
            pass 


    





     # Crush Sand
    sieve_name1 = fields.Char("Name",default="Crushed Sand")
    aggregate_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_aggregate_visible")
    child_lines = fields.One2many('mechanical.concrete.design.crush.sand.line1','parent_id',string="Sieve Analysis",default=lambda self: self._default_sieve_analysis_child_lines())
    total1 = fields.Integer(string="Total",compute="_compute_total")
    Aggregate_name = fields.Char("Aggregate",compute="_compute_aggregate_visible")

    @api.depends('child_lines_concrete_design_material.material')
    def _compute_aggregate_visible(self):
        for record in self:
            # Check if any child line has material set to "20MM"
            has_aggregate_visible = any(line.material == "C/Sand" for line in record.child_lines_concrete_design_material)
            
            # Set sieve_visible20mm to True if "20MM" material exists, else False
            record.aggregate_visible = has_aggregate_visible
            
            # Set size_20mm based on the value of sieve_visible20mm
            record.Aggregate_name = "C/Sand" if has_aggregate_visible else ""


    @api.model
    def _default_sieve_analysis_child_lines(self):
        default_lines = [
            (0, 0, {'sieve_size': '10 '}),
            (0, 0, {'sieve_size': '4.75 '}),
            (0, 0, {'sieve_size': '2.36 '}),
            (0, 0, {'sieve_size': '1.18 '}),
            (0, 0, {'sieve_size': '0.6 '}),
            (0, 0, {'sieve_size': '0.3 '}),
            (0, 0, {'sieve_size': '0.15 '}),
             (0, 0, {'sieve_size': '0.075 '}),
            (0, 0, {'sieve_size': 'Bal '})
        ]
        return default_lines


    def calculate(self): 
        for record in self:
            for line in record.child_lines:
                print("Rows",str(line.percent_retained))
                previous_line = line.serial_no - 1
                if previous_line == 0:
                    line.write({'cumulative_retained': line.percent_retained})
                    line.write({'passing_percent': 100})

                else:
                    previous_line_record = self.env['mechanical.concrete.design.crush.sand.line1'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
                    line.write({'cumulative_retained': previous_line_record + line.percent_retained})
                    line.write({'passing_percent': 100-(previous_line_record + line.percent_retained)})
                    print("Previous Cumulative",previous_line_record)

                    

                
    

   
    @api.depends('child_lines.wt_retained')
    def _compute_total(self):
        for record in self:
            print("recordd",record)
            record.total1 = sum(record.child_lines.mapped('wt_retained'))

    @api.onchange('total1')
    def _onchange_total(self):
        for line in self.child_lines:
            line._compute_percent_retained1()
            # line._compute_cumulative_retained()


    graph_image_crush_sand = fields.Binary("Line Chart", compute="_compute_graph_image_crush_sand", store=True)



    def generate_line_chart_crush_sand(self):
        # Sample data - Replace these lists with actual data from your model
        sieve_sizes_cs = []
        up_values_cs = []
        ll_values_cs = []
        passing_percent_values_cs = []

        for line in self.child_lines:
            sieve_sizes_cs.append(line.sieve_size)
            up_values_cs.append(line.cs_up)
            ll_values_cs.append(line.cs_ll)
            passing_percent_values_cs.append(line.passing_percent)
            # passing_percent_values_cs.append(f"{line.passing_percent:.2f}")

        # Ensure all lists have data and are of equal length
        if not (len(sieve_sizes_cs) == len(up_values_cs) == len(ll_values_cs) == len(passing_percent_values_cs)):
            print("Data lists have mismatched lengths or are empty")
            return None

        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(sieve_sizes_cs, up_values_cs, marker='o', label='UP', color='blue')
        ax.plot(sieve_sizes_cs, ll_values_cs, marker='o', label='LL', color='orange')
        ax.plot(sieve_sizes_cs, passing_percent_values_cs, marker='o', label='% Passing', color='green')

        # Set labels and title
        ax.set_xlabel('Size (mm)')
        ax.set_ylabel('% Passing')
        ax.set_title('Grading of  Crushed Sand')

    
        ax.set_xlim(min(sieve_sizes_cs), max(sieve_sizes_cs))  # Set x-axis from min to max sieve sizes
        ax.set_ylim(0, 100)  # % Passing ranges from 0 to 100

        ax.grid(True)

        # Add legend
        ax.legend()

        ax.set_xticks(sieve_sizes_cs)

        # Create the table below the plot
        # passing_percent_values_cs = [f"{value:.2f}" for value in passing_percent_values]  # Format values to two decimals

        table_data = [
            ["UP"] + list(up_values_cs),
            ["LL"] + list(ll_values_cs),
            ["% Passing"] + list(passing_percent_values_cs)
        ]
        column_labels = ["Size (mm)"] + list(sieve_sizes_cs)

        table = ax.table(cellText=table_data, colLabels=column_labels, cellLoc='center', loc='bottom', bbox=[0, -0.4, 1, 0.2])

        # Adjust the font size of the table to make it more compact
        table.auto_set_font_size(False)  # Disable automatic font size adjustment
        table.set_fontsize(8)  # Set a smaller font size for better readability

        # Adjust cell height and width if necessary
        for (i, j), cell in table.get_celld().items():
            if i == 0:  # Set the header row
                cell.set_text_props(weight='bold')
                cell.set_fontsize(9)
            else:
                cell.set_fontsize(8)
            cell.set_height(0.04)  # Adjust the height of the rows
            cell.set_width(0.1)  # Adjust the width of the columns

        # Adjust layout to make space for the table without overlapping the plot
        plt.subplots_adjust(bottom=0.35)  # Adjust the bottom space for the table


        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()  # Close the plot to free up resources
        buffer.seek(0)

        # Convert the chart image to base64
        chart_image_crush_sand = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()  # Close the buffer to free up memory
        return chart_image_crush_sand

    @api.depends('child_lines')
    def _compute_graph_image_crush_sand(self):
        try:
            for record in self:
                chart_image_crush_sand = record.generate_line_chart_crush_sand()
                record.graph_image_crush_sand = chart_image_crush_sand
        except:
            pass 


     #  D. COMBINATION AND ANALYSIS OF COARSE AGGREGATE FRACTIONS:

    combination10and20mm = fields.Char("Name",default="D. COMBINATION AND ANALYSIS OF COARSE AGGREGATE FRACTIONS")

    combination10and20mm_child_lines = fields.One2many('mechanical.combination.10and20.line1','parent_id',string="Sieve Analysis Combination",default=lambda self: self._default_combination10and20mm_child_lines())

    @api.model
    def _default_combination10and20mm_child_lines(self):
        default_lines = [
            (0, 0, {'sieve_size': '40 '}),
            (0, 0, {'sieve_size': '20 '}),
            (0, 0, {'sieve_size': '10'}),
            (0, 0, {'sieve_size': '4.75 '}),
            (0, 0, {'sieve_size': '2.36'})
           
        ]
        return default_lines

    
    graph_image_combination10and20mm = fields.Binary("Line Chart", compute="_compute_chart_image_combination10and20mm", store=True)



    def generate_line_chart_1combination10and20mm(self):
        # Sample data - Replace these lists with actual data from your model
        sieve_sizes_combine = []
        up_values_combine = []
        ll_values_combine = []
        combine_values = []

        for line in self.combination10and20mm_child_lines:
            sieve_sizes_combine.append(line.sieve_size)
            up_values_combine.append(line.combine_grading_up)
            ll_values_combine.append(line.combine_grading_ll)
            combine_values.append(line.combine_grading)

        # Ensure all lists have data and are of equal length
        if not (len(sieve_sizes_combine) == len(up_values_combine) == len(ll_values_combine) == len(combine_values)):
            print("Data lists have mismatched lengths or are empty")
            return None

        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(sieve_sizes_combine, up_values_combine, marker='o', label='UP', color='blue')
        ax.plot(sieve_sizes_combine, ll_values_combine, marker='o', label='LL', color='orange')
        ax.plot(sieve_sizes_combine, combine_values, marker='o', label='% Passing', color='green')

        # Set labels and title
        ax.set_xlabel('Size (mm)')
        ax.set_ylabel('% Passing')
        ax.set_title('Combined Granding Of  Coarse Agg')

    
        ax.set_xlim(max(sieve_sizes_combine) , min(sieve_sizes_combine) )  # Set x-axis from min to max sieve sizes
        ax.set_ylim(0, 100)  # % Passing ranges from 0 to 100

        ax.grid(True)

        # Add legend
        ax.legend()

        ax.set_xticks(sieve_sizes_combine)

        # Create the table below the plot
        table_data = [
            ["UP"] + list(up_values_combine),
            ["LL"] + list(ll_values_combine),
            ["% Passing"] + list(combine_values)
        ]
        column_labels = ["Size (mm)"] + list(sieve_sizes_combine)

        table = ax.table(cellText=table_data, colLabels=column_labels, cellLoc='center', loc='bottom', bbox=[0, -0.4, 1, 0.2])

        table.auto_set_font_size(False)  # Disable automatic font size adjustment
        table.set_fontsize(8)  # Set a smaller font size for better readability

        # Adjust cell height and width if necessary
        for (i, j), cell in table.get_celld().items():
            if i == 0:  # Set the header row
                cell.set_text_props(weight='bold')
                cell.set_fontsize(9)
            else:
                cell.set_fontsize(8)
            cell.set_height(0.04)  # Adjust the height of the rows
            cell.set_width(0.1)  # Adjust the width of the columns

        # Adjust layout to make space for the table without overlapping the plot
        plt.subplots_adjust(bottom=0.35)  # Adjust the bottom space for the table


        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()  # Close the plot to free up resources
        buffer.seek(0)

        # Convert the chart image to base64
        chart_image_combination10and20mm = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()  # Close the buffer to free up memory
        return chart_image_combination10and20mm

    @api.depends('combination10and20mm_child_lines')
    def _compute_chart_image_combination10and20mm(self):
        try:
            for record in self:
                chart_image_combination10and20mm = record.generate_line_chart_1combination10and20mm()
                record.graph_image_combination10and20mm = chart_image_combination10and20mm
        except:
            pass 


    #  E.  COMBINED GRADING :

    combine_granding = fields.Char("Name",default="E.  COMBINED GRADING ")

    combine_granding_child_lines = fields.One2many('mechanical.combined.granding.line1','parent_id',string="Sieve Analysis Combination",default=lambda self: self._default_combine_granding_child_lines())

    @api.model
    def _default_combine_granding_child_lines(self):
        default_lines = [
            (0, 0, {'sieve_size': '40 '}),
            (0, 0, {'sieve_size': '20 '}),
            (0, 0, {'sieve_size': '4.75 '}),
            (0, 0, {'sieve_size': '0.6'}),
            (0, 0, {'sieve_size': '0.15'}),
           
        ]
        return default_lines


    mix_proporation_name = fields.Char(default="Mix Proporation")

    mix_proporation_20mm = fields.Char('20MM',compute="_compute_mix_proporation_20mm")
    mix_proporation_10mm = fields.Char('10MM',compute="_compute_mix_proporation_10mm")
    mix_proporation_rsand = fields.Char('R/SAND',compute="_compute_mix_proporation_rsand")
    mix_proporation_csand = fields.Char('C/SAND',compute="_compute_mix_proporation_csand")


    @api.depends('child_lines_concrete_design.mm20')
    def _compute_mix_proporation_20mm(self):
        for record in self:
            if len(record.child_lines_concrete_design) >= 4:  # Ensure there are at least 4 child records
                mm20_value_str = record.child_lines_concrete_design[3].mm20  # Fetch the string value of mm20
                
                if mm20_value_str:
                    match = re.search(r'\d+(\.\d+)?', mm20_value_str)
                    if match:
                        mm20_value = float(match.group())
                        # rounded_value = math.ceil(mm20_value)  # Always rounds up (e.g., 30.50 becomes 31)
                    else:
                        mm20_value = 0  # Default to 0 if parsing fails
                else:
                    mm20_value = 0  # Default to 0 if mm20_value_str is empty or None

                record.mix_proporation_20mm = f"{mm20_value}%"
            else:
                record.mix_proporation_20mm = "0%"


    @api.depends('child_lines_concrete_design.mm10')
    def _compute_mix_proporation_10mm(self):
        for record in self:
            if len(record.child_lines_concrete_design) >= 4:  # Ensure there are at least 4 child records
                mm10_value_str = record.child_lines_concrete_design[3].mm10  # Fetch the string value of mm10
                
                if mm10_value_str:
                    match = re.search(r'\d+(\.\d+)?', mm10_value_str)
                    if match:
                        mm10_value = float(match.group())
                        # rounded_value = math.ceil(mm10_value)  # Always rounds up (e.g., 30.50 becomes 31)
                    else:
                        mm10_value = 0  # Default to 0 if parsing fails
                else:
                    mm10_value = 0  # Default to 0 if mm10_value_str is empty or None

                record.mix_proporation_10mm = f"{mm10_value}%"
            else:
                record.mix_proporation_10mm = "0%"


    @api.depends('child_lines_concrete_design.r_Sand')
    def _compute_mix_proporation_rsand(self):
        for record in self:
            if len(record.child_lines_concrete_design) >= 4:  # Ensure there are at least 4 child records
                r_Sand_value_str = record.child_lines_concrete_design[3].r_Sand  # Fetch the string value of r_Sand
                
                if r_Sand_value_str:
                    match = re.search(r'\d+(\.\d+)?', r_Sand_value_str)
                    if match:
                        r_Sand_value = float(match.group())
                        # rounded_value = math.ceil(r_Sand_value)  # Always rounds up (e.g., 30.50 becomes 31)
                    else:
                        r_Sand_value = 0  # Default to 0 if parsing fails
                else:
                    r_Sand_value = 0  # Default to 0 if r_Sand_value_str is empty or None

                record.mix_proporation_rsand = f"{r_Sand_value}%"
            else:
                record.mix_proporation_rsand = "0%"

    @api.depends('child_lines_concrete_design.c_Sand')
    def _compute_mix_proporation_csand(self):
        for record in self:
            if len(record.child_lines_concrete_design) >= 4:  # Ensure there are at least 4 child records
                c_Sand_value_str = record.child_lines_concrete_design[3].c_Sand  # Fetch the string value of c_Sand
                
                if c_Sand_value_str:
                    match = re.search(r'\d+(\.\d+)?', c_Sand_value_str)
                    if match:
                        c_Sand_value = float(match.group())
                        # rounded_value = math.ceil(c_Sand_value)  # Always rounds up (e.g., 30.50 becomes 31)
                    else:
                        c_Sand_value = 0  # Default to 0 if parsing fails
                else:
                    c_Sand_value = 0  # Default to 0 if c_Sand_value_str is empty or None

                record.mix_proporation_csand = f"{c_Sand_value}%"
            else:
                record.mix_proporation_csand = "0%"


  


      
    # F. TARGET MEAN STRENGTH

 
    target_mean_strength_name = fields.Char(default="F. TARGET MEAN STRENGTH  As per IS 456:2000 ")
    design_stipulations_visible = fields.Boolean(compute="_compute_visible")

    target_mean_strength_com = fields.Float('fek = target mean compressive strength at 28 days in N/mm2',compute="_compute_target_com_fetch")
    target_mean_strength_chara = fields.Float('fck = characteristic comprssive strength at 28 days in N/mm2',compute="_compute_target_mean_strength_chara")
    target_mean_strength_sd = fields.Float('s= standard deviation N/mm2',compute="_compute_target_mean_strength_sd")


    @api.depends('child_lines_concrete_design.cement_display')
    def _compute_target_com_fetch(self):
        for record in self:
            if len(record.child_lines_concrete_design) >= 2:
                cement_display_value_str = record.child_lines_concrete_design[2].cement_display  # Fetch the string value of cement_display
                
                if cement_display_value_str:
                    match = re.search(r'\d+(\.\d+)?', cement_display_value_str)  # Match integer or float
                    if match:
                        cement_display_value = round(float(match.group()), 2)
                    else:
                        cement_display_value = 0.0
                else:
                    cement_display_value = 0.0

                record.target_mean_strength_com = cement_display_value
            else:
                record.target_mean_strength_com = 0.0

    @api.depends('child_lines_concrete_design.cement_display')
    def _compute_target_mean_strength_chara(self):
        for record in self:
            if len(record.child_lines_concrete_design) >= 3:
                cement_display_value_str = record.child_lines_concrete_design[3].cement_display  # Fetch the string value of cement_display
                
                if cement_display_value_str:
                    match = re.search(r'\d+(\.\d+)?', cement_display_value_str)  # Match integer or float
                    if match:
                        cement_display_value = round(float(match.group()), 2)
                    else:
                        cement_display_value = 0.0
                else:
                    cement_display_value = 0.0

                record.target_mean_strength_chara = cement_display_value
            else:
                record.target_mean_strength_chara = 0.0

    @api.depends('target_mean_strength_com', 'target_mean_strength_chara', 'design_stipulations_tolerance')
    def _compute_target_mean_strength_sd(self):
        for record in self:
            if record.target_mean_strength_com and record.design_stipulations_tolerance and record.target_mean_strength_chara:
                record.target_mean_strength_sd = record.target_mean_strength_com + (record.design_stipulations_tolerance * record.target_mean_strength_chara)
            else:
                record.target_mean_strength_sd = 0.0


    # G. SELECTION OF WATER - CEMENT RATIO


 
    selection_water_cement_name = fields.Char(default="G. SELECTION OF WATER - CEMENT RATIO")
    selection_water_cement_visible = fields.Boolean(compute="_compute_visible")

    selection_maximum_water_cement = fields.Float('From table 5 of IS 456, Maximum Water - Cement Ratio = ',compute="_compute_selection_maximum_water_cement")
    selection_adopt_water_cement = fields.Float('Based on experience , adopt water - cement ratio as = ',compute="_compute_selection_adopt_water_cement",digits=(12,4))


    @api.depends('design_stipulations_water')
    def _compute_selection_maximum_water_cement(self):
        for record in self:
            # Fetch the value from design_stipulations_water
            record.selection_maximum_water_cement = record.design_stipulations_water

    @api.depends('child_lines_concrete_design.w_c_f')
    def _compute_selection_adopt_water_cement(self):
        for record in self:
            if len(record.child_lines_concrete_design) >= 0:
                w_c_f_value_str = record.child_lines_concrete_design[0].w_c_f  # Fetch the string value of w_c_f
                
                if w_c_f_value_str:
                    match = re.search(r'\d+(\.\d+)?', w_c_f_value_str)  # Match integer or float
                    if match:
                        w_c_f_value = float(match.group())
                    else:
                        w_c_f_value = 0.0
                else:
                    w_c_f_value = 0.0

                record.selection_adopt_water_cement = w_c_f_value
            else:
                record.selection_adopt_water_cement = 0.0
   

      # H.SELECTION OF WATER CONTENT


 
    selection_water_content_name = fields.Char(default="H. SELECTION OF WATER CONTENT")
    selection_water_content_visible = fields.Boolean(compute="_compute_visible")

    selection_water_content_maximum = fields.Float('From table 2,maximum water - cement content for 20 mm aggregate =')
    selection_water_content_superplasticizer = fields.Float('we are used superplasticizer & based on trial mix water adopted =',compute="_compute_selection_water_content_superplasticizer")

    @api.depends('sp_gr')
    def _compute_selection_water_content_superplasticizer(self):
        for record in self:
            # Fetch the value from design_stipulations_water
            record.selection_water_content_superplasticizer = record.sp_gr


     # I. CALCULATION OF CEMENT CONTENT

    calculation_cement_content_name = fields.Char(default="I. CALCULATION OF CEMENT CONTENT")
    calculation_cement_content_visible = fields.Boolean(compute="_compute_visible")

    calculation_cement_content_wc = fields.Float('Water - cement ratio =',compute="_compute_calculation_cement_content_wc",digits=(12,4))
    calculation_cement_content = fields.Float('Cement  content =',compute="_compute_calculation_cement_content")
    calculation_cement_content_minimum = fields.Float('From table 5 of IS 456 Minimum cement =',compute="_compute_calculation_cement_content_minimum")


    @api.depends('selection_adopt_water_cement')
    def _compute_calculation_cement_content_wc(self):
        for record in self:
            if record.selection_adopt_water_cement:
                record.calculation_cement_content_wc = record.selection_adopt_water_cement
            else:
                record.calculation_cement_content_wc = 0.0

    @api.depends('selection_water_content_superplasticizer','calculation_cement_content_wc')
    def _compute_calculation_cement_content(self):
        for record in self:
            if record.selection_water_content_superplasticizer and record.calculation_cement_content_wc:
                record.calculation_cement_content = record.selection_water_content_superplasticizer /  record.calculation_cement_content_wc
            else:
                record.calculation_cement_content = 0.0

    @api.depends('design_stipulations_cement')
    def _compute_calculation_cement_content_minimum(self):
        for record in self:
            # Fetch the value from design_stipulations_water
            record.calculation_cement_content_minimum = record.design_stipulations_cement


    # K. BLENDING PROPORTION OF COARSE & FINE AGGREGATE

    blending_proportion_name = fields.Char(default="K. BLENDING PROPORTION OF COARSE & FINE AGGREGATE")
    blending_proportion_visible = fields.Boolean(compute="_compute_visible")

    blending_proportion_20mm = fields.Char('20MM',compute="_compute_blending_proportion_20mm")
    blending_proportion10mm = fields.Char('10MM',compute="_compute_blending_proportion10mm")
    blending_proportion_rsand = fields.Char('R/SAND',compute="_compute_blending_proportion_rsand")
    blending_proportion_csand = fields.Char('C/SAND',compute="_compute_blending_proportion_csand")



    @api.depends('child_lines_concrete_design.mm20')
    def _compute_blending_proportion_20mm(self):
        for record in self:
            if len(record.child_lines_concrete_design) >= 4:  # Ensure there are at least 4 child records
                mm20_value_str = record.child_lines_concrete_design[3].mm20  # Fetch the string value of mm20
                
                if mm20_value_str:
                    match = re.search(r'\d+(\.\d+)?', mm20_value_str)
                    if match:
                        mm20_value = float(match.group())
                        rounded_value = math.ceil(mm20_value)  # Always rounds up (e.g., 30.50 becomes 31)
                    else:
                        rounded_value = 0  # Default to 0 if parsing fails
                else:
                    rounded_value = 0  # Default to 0 if mm20_value_str is empty or None

                record.blending_proportion_20mm = f"{rounded_value}%"
            else:
                record.blending_proportion_20mm = "0%"

    @api.depends('child_lines_concrete_design.mm10')
    def _compute_blending_proportion10mm(self):
        for record in self:
            if len(record.child_lines_concrete_design) >= 4:  # Ensure there are at least 4 child records
                mm10_value_str = record.child_lines_concrete_design[3].mm10  # Fetch the string value of mm10
                
                if mm10_value_str:
                    match = re.search(r'\d+(\.\d+)?', mm10_value_str)
                    if match:
                        mm10_value = float(match.group())
                        rounded_value = math.ceil(mm10_value)  # Always rounds up (e.g., 30.50 becomes 31)
                    else:
                        rounded_value = 0  # Default to 0 if parsing fails
                else:
                    rounded_value = 0  # Default to 0 if mm10_value_str is empty or None

                record.blending_proportion10mm = f"{rounded_value}%"
            else:
                record.blending_proportion10mm = "0%"


    @api.depends('child_lines_concrete_design.r_Sand')
    def _compute_blending_proportion_rsand(self):
        for record in self:
            if len(record.child_lines_concrete_design) >= 4:  # Ensure there are at least 4 child records
                r_Sand_value_str = record.child_lines_concrete_design[3].r_Sand  # Fetch the string value of r_Sand
                
                if r_Sand_value_str:
                    match = re.search(r'\d+(\.\d+)?', r_Sand_value_str)
                    if match:
                        r_Sand_value = float(match.group())
                        rounded_value = math.ceil(r_Sand_value)  # Always rounds up (e.g., 30.50 becomes 31)
                    else:
                        rounded_value = 0  # Default to 0 if parsing fails
                else:
                    rounded_value = 0  # Default to 0 if r_Sand_value_str is empty or None

                record.blending_proportion_rsand = f"{rounded_value}%"
            else:
                record.blending_proportion_rsand = "0%"

    @api.depends('child_lines_concrete_design.c_Sand')
    def _compute_blending_proportion_csand(self):
        for record in self:
            if len(record.child_lines_concrete_design) >= 4:  # Ensure there are at least 4 child records
                c_Sand_value_str = record.child_lines_concrete_design[3].c_Sand  # Fetch the string value of c_Sand
                
                if c_Sand_value_str:
                    match = re.search(r'\d+(\.\d+)?', c_Sand_value_str)
                    if match:
                        c_Sand_value = float(match.group())
                        rounded_value = math.ceil(c_Sand_value)  # Always rounds up (e.g., 30.50 becomes 31)
                    else:
                        rounded_value = 0  # Default to 0 if parsing fails
                else:
                    rounded_value = 0  # Default to 0 if c_Sand_value_str is empty or None

                record.blending_proportion_csand = f"{rounded_value}%"
            else:
                record.blending_proportion_csand = "0%"
    
    




    


    # @api.depends('eln_ref')
    # def _compute_visible(self):
    #     for record in self:
          
    #         # record.sieve_visible = False
    #         # record.sieve_visible1 = False
         

    #         for sample in record.sample_parameters:
              
                # if sample.internal_id == '4c010f3d-0fc8-4231-9e1f-09d6d1b908b5':
                #     record.sieve_visible = True

                # if sample.internal_id == 'd2fceeb5-1d45-476d-a207-4c3d7673194f':
                #     record.sieve_visible1 = True
               

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id



    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(ConcreteDesign, self).create(vals)
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
        record = self.env['mechanical.concrete.design1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values





    


    
    
   



class SieveAnalysisLine(models.Model):
    _name = "mechanical.concrete.design.sieve.analysis.line1"
    parent_id = fields.Many2one('mechanical.concrete.design1', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size mm")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained",digits=(16,2))
    cumulative_retained = fields.Float(string="Cum. Retained %", store=True,digits=(16,2))
    passing_percent = fields.Float(string="Passing %",digits=(16,2))
    ll = fields.Float(string="LL",digits=(16,2))
    up = fields.Float(string="UP ",digits=(16,2))



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SieveAnalysisLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

    def write(self, vals):
        # Handle row deletions and adjust serial numbers
        if 'parent_id' in vals or 'wt_retained' in vals:
            for record in self:
                if record.parent_id and record.parent_id == vals.get('parent_id') and 'wt_retained' in vals:
                    record.percent_retained = vals['wt_retained'] / record.parent_id.total * 100 if record.parent_id.total else 0

            new_self = super(SieveAnalysisLine, self).write(vals)

            if 'wt_retained' in vals:
                for record in self:
                    # record.parent_id._compute_total()
                    pass

            return new_self

        return super(SieveAnalysisLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(SieveAnalysisLine, self).unlink()

        if parent_id:
            parent_id.sieve_analysis_child_lines._reorder_serial_numbers()

        return res


    @api.depends('wt_retained', 'parent_id.total_sieve_analysis')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = record.wt_retained / self.parent_id.total_sieve_analysis * 100
            except ZeroDivisionError:
                record.percent_retained = 0


    @api.depends('cumulative_retained')
    def _compute_cum_retained(self):
        self.cumulative_retained=0
        


    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines, key=lambda r: r.id)
            # index = sorted_lines.index(record)
            # print("Working")



class SieveAnalysisLine20mm(models.Model):
    _name = "mechanical.concrete.design.sieve.20mm.line1"
    parent_id = fields.Many2one('mechanical.concrete.design1', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size mm")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained20mm",digits=(16,2))
    cumulative_retained = fields.Float(string="Cum. Retained %", store=True,digits=(16,2))
    passing_percent = fields.Float(string="Passing %",digits=(16,2))
    ll = fields.Float(string="LL",digits=(16,2))
    up = fields.Float(string="UP ",digits=(16,2))



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SieveAnalysisLine20mm, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

    def write(self, vals):
        # Handle row deletions and adjust serial numbers
        if 'parent_id' in vals or 'wt_retained' in vals:
            for record in self:
                if record.parent_id and record.parent_id == vals.get('parent_id') and 'wt_retained' in vals:
                    record.percent_retained = vals['wt_retained'] / record.parent_id.total * 100 if record.parent_id.total else 0

            new_self = super(SieveAnalysisLine20mm, self).write(vals)

            if 'wt_retained' in vals:
                for record in self:
                    # record.parent_id._compute_total()
                    pass

            return new_self

        return super(SieveAnalysisLine20mm, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(SieveAnalysisLine20mm, self).unlink()

        if parent_id:
            parent_id.sieve_analysis_child_lines_20mm._reorder_serial_numbers()

        return res


    @api.depends('wt_retained', 'parent_id.total_sieve_analysis20mm')
    def _compute_percent_retained20mm(self):
        for record in self:
            try:
                record.percent_retained = record.wt_retained / self.parent_id.total_sieve_analysis20mm * 100
            except ZeroDivisionError:
                record.percent_retained = 0


    @api.depends('cumulative_retained')
    def _compute_cum_retained20(self):
        self.cumulative_retained=0
        


    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines_20mm, key=lambda r: r.id)
            # index = sorted_lines.index(record)
            # print("Working")

class CrushSandLine(models.Model):
    _name = "mechanical.concrete.design.crush.sand.line1"
    parent_id = fields.Many2one('mechanical.concrete.design1', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained1")
    cumulative_retained = fields.Float(string="Cum. Retained %",  store=True)
    passing_percent = fields.Float(string="Passing %",digits=(16,2))
    cs_ll = fields.Float(string="LL",digits=(16,2))
    cs_up = fields.Float(string="UP ",digits=(16,2))

    @api.onchange('cumulative_retained')
    def _compute_passing_percent(self):
        for record in self:
            # record.passing_percent = 107.86 - record.cumulative_retained
            record.passing_percent = 107.86 - 107.86


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CrushSandLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

    def write(self, vals):
        # Handle row deletions and adjust serial numbers
        if 'parent_id' in vals or 'wt_retained' in vals:
            for record in self:
                if record.parent_id and record.parent_id == vals.get('parent_id') and 'wt_retained' in vals:
                    record.percent_retained = vals['wt_retained'] / record.parent_id.total * 100 if record.parent_id.total else 0

            new_self = super(CrushSandLine, self).write(vals)

            if 'wt_retained' in vals:
                for record in self:
                    record.parent_id._compute_total()

            return new_self

        return super(CrushSandLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(CrushSandLine, self).unlink()

        if parent_id:
            parent_id.child_lines._reorder_serial_numbers()

        return res

    
   

    @api.depends('wt_retained', 'parent_id.total1')
    def _compute_percent_retained1(self):
        for record in self:
            try:
                record.percent_retained = record.wt_retained / 700 * 100
            except ZeroDivisionError:
                record.percent_retained = 0

    # @api.depends('wt_retained', 'parent_id.total1')
    # def _compute_percent_retained1(self):
    #     for record in self:
    #         try:
    #             result = record.wt_retained / record.parent_id.total1 * 100
    #             record.percent_retained = round(result, 2)  # rounding to 2 decimal places
    #         except ZeroDivisionError:
    #             record.percent_retained = 0


    @api.depends('parent_id.child_lines.cumulative_retained')
    def _compute_cum_retained(self):
        # self.get_previous_record()
        self.cumulative_retained=0
        # sorted_lines = self.sorted(lambda r: r.id)
        # cumulative_retained = 0.0
        # for line in sorted_lines:
        #     line.cumulative_retained = cumulative_retained + line.percent_retained
        #     cumulative_retained = line.cumulative_retained


    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.child_lines, key=lambda r: r.id)
            # index = sorted_lines.index(record)
            # print("Working")



class Concrete_Design_FLine(models.Model):
    _name = "mechanical.concrete.design.line1"
    parent_id = fields.Many2one('mechanical.concrete.design1', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    abstract = fields.Char(string="Abstract")
    # cement = fields.Float(string="Cement")
    cement_display = fields.Char(string="Cement")  # Display field for M-40
    slag = fields.Char(string='Slag')
    miro_silica = fields.Char(string="Miro silica")
    w_c_f = fields.Char(string="W/(C+F)")
    c_f = fields.Char(string="(C+F)")
    r_Sand = fields.Char(string="R/SAND",digits=(12,3))
    c_Sand = fields.Char(string="C/SAND",digits=(12,3))
    mm10 = fields.Char(string="10MM",digits=(12,3))
    mm20 = fields.Char(string="20MM",digits=(12,3))
    adm = fields.Char(string="ADM")

    kg_per_m3 = fields.Float(string="Kg/M3", compute="_compute_kg_per_m3", store=True)

    # @api.depends('cement', 'slag', 'miro_silica')
    # def _compute_kg_per_m3(self):
    #     for record in self:
    #         record.kg_per_m3 = record.cement + record.slag + record.miro_silica
    @api.depends('cement_display', 'slag', 'miro_silica', 'parent_id.child_lines_concrete_design')
    def _compute_kg_per_m3(self):
        for record in self:
            # Check if the current record is the first child in the parent record's child_lines_concrete_design
            child_lines = record.parent_id.child_lines_concrete_design  # Get the list of child lines
            if len(child_lines) > 0 and child_lines[0] == record:  # Check if it's the first child
                # Convert cement_display, slag, and miro_silica to float, defaulting to 0.0 if invalid
                try:
                    cement_value = float(record.cement_display) if record.cement_display else 0.0
                except ValueError:
                    cement_value = 0.0  # If it's not a valid number (e.g., "M-40"), set to 0.0

                try:
                    slag_value = float(record.slag) if record.slag else 0.0
                except ValueError:
                    slag_value = 0.0  # If it's not a valid number, set to 0.0

                try:
                    miro_silica_value = float(record.miro_silica) if record.miro_silica else 0.0
                except ValueError:
                    miro_silica_value = 0.0  # If it's not a valid number, set to 0.0

                # Now sum all numeric values
                record.kg_per_m3 = cement_value  + slag_value + miro_silica_value
            else:
                # For other lines, don't calculate or reset to 0 if needed
                record.kg_per_m3 = 0.0  # Or leave it unset if you prefer


class ConcreteDesignMaterialLine(models.Model):
    _name = "mechanical.concrete.design.material.line1"
    parent_id = fields.Many2one('mechanical.concrete.design1', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    material = fields.Char(string="Material")
    specific_gravity = fields.Float(string="Specific Gravity",compute="_compute_specific_gravity",store=True,digits=(12,3))
    water_absorption = fields.Float(string='Water Absorption (%)',compute="_compute_water_absorption",store=True,digits=(12,3))


    @api.depends('parent_id.child_lines_concrete_design')
    def _compute_specific_gravity(self):
        for record in self:
            if record.parent_id:
                if record == record.parent_id.child_lines_concrete_design_material[:1]:
                    if len(record.parent_id.child_lines_concrete_design) > 1:
                        record.specific_gravity = record.parent_id.child_lines_concrete_design[1].mm20
                    else:
                        record.specific_gravity = 0.0  # Default if the second line is not available

                elif record == record.parent_id.child_lines_concrete_design_material[1:2]:
                    if len(record.parent_id.child_lines_concrete_design) > 1:
                        record.specific_gravity = record.parent_id.child_lines_concrete_design[1].mm10
                    else:
                        record.specific_gravity = 0.0  # Default if the second line is not available

                elif record == record.parent_id.child_lines_concrete_design_material[2:3]:
                    if len(record.parent_id.child_lines_concrete_design) > 1:
                        record.specific_gravity = record.parent_id.child_lines_concrete_design[1].r_Sand
                    else:
                        record.specific_gravity = 0.0  # Default if the second line is not available

                elif record == record.parent_id.child_lines_concrete_design_material[3:4]:
                    if len(record.parent_id.child_lines_concrete_design) > 1:
                        record.specific_gravity = record.parent_id.child_lines_concrete_design[1].c_Sand
                    else:
                        record.specific_gravity = 0.0  # Default if the second line is not available

                else:
                    record.specific_gravity = 0.0
            else:
                record.specific_gravity = 0.0

   
    @api.depends('parent_id.child_lines_concrete_design')
    def _compute_water_absorption(self):
        for record in self:
            if record.parent_id:
                if record == record.parent_id.child_lines_concrete_design_material[:1]:
                    if len(record.parent_id.child_lines_concrete_design) > 1:
                        record.water_absorption = record.parent_id.child_lines_concrete_design[2].mm20
                    else:
                        record.water_absorption = 0.0  # Default if the second line is not available

                elif record == record.parent_id.child_lines_concrete_design_material[1:2]:
                    if len(record.parent_id.child_lines_concrete_design) > 1:
                        record.water_absorption = record.parent_id.child_lines_concrete_design[2].mm10
                    else:
                        record.water_absorption = 0.0  # Default if the second line is not available

                elif record == record.parent_id.child_lines_concrete_design_material[2:3]:
                    if len(record.parent_id.child_lines_concrete_design) > 1:
                        record.water_absorption = record.parent_id.child_lines_concrete_design[2].r_Sand
                    else:
                        record.water_absorption = 0.0  # Default if the second line is not available

                elif record == record.parent_id.child_lines_concrete_design_material[3:4]:
                    if len(record.parent_id.child_lines_concrete_design) > 1:
                        record.water_absorption = record.parent_id.child_lines_concrete_design[2].c_Sand
                    else:
                        record.water_absorption = 0.0  # Default if the second line is not available

                else:
                    record.water_absorption = 0.0
            else:
                record.water_absorption = 0.0

    @api.onchange('specific_gravity', 'water_absorption', 'parent_id')
    def _onchange_specific_gravity_water_absorption(self):
        if self.parent_id:
            child_lines_count = len(self.parent_id.child_lines_concrete_design_material)

            if child_lines_count == 1:
                if self.specific_gravity or self.water_absorption:
                    self.material = "20MM" 
                else:
                    self.material = "" 

            elif child_lines_count == 2:
                if self.specific_gravity or self.water_absorption:
                    self.material = "10MM" 
                else:
                    self.material = "" 

            elif child_lines_count == 3:
                if self.specific_gravity or self.water_absorption:
                    self.material = "R/Sand" 
                else:
                    self.material = "" 

            elif child_lines_count == 4:
                if self.specific_gravity or self.water_absorption:
                    self.material = "C/Sand" 
                else:
                    self.material = "" 

            else:
                self.material = "" 

    
class Combination10And20Line(models.Model):
    _name = "mechanical.combination.10and20.line1"
    parent_id = fields.Many2one('mechanical.concrete.design1', string="Parent Id")
    
    sieve_size = fields.Char(string="IS SIEVE (mm)")
    passing_10mm = fields.Float(string="% Passing Individual 10 MM",compute="_compute_passing_10mm")
    passing_20mm = fields.Float(string='% Passing Individual 20 MM',compute="_compute_passing_20mm")

    passing_combined38 = fields.Float(string="% Passing combined 38",compute="_compute_passing_combined38")
    passing_combined62 = fields.Float(string='% Passing Individual 62',compute="_compute_passing_combined62")

    combine_grading = fields.Float(string='Combined Grading',compute="_compute_passing_combined_granding")
    combine_grading_ll = fields.Float(string='LL')
    combine_grading_up = fields.Float(string='UP')


    @api.depends('parent_id.sieve_analysis_child_lines_20mm')
    def _compute_passing_20mm(self):
        for record in self:
        
            if record.parent_id:
                if record == record.parent_id.combination10and20mm_child_lines[0]:
                    if len(record.parent_id.sieve_analysis_child_lines_20mm) > 0:
                        record.passing_20mm = record.parent_id.sieve_analysis_child_lines_20mm[0].passing_percent
                    else:
                        record.passing_20mm = 0.0  

                elif record == record.parent_id.combination10and20mm_child_lines[1]:
                    if len(record.parent_id.sieve_analysis_child_lines_20mm) > 1:
                        record.passing_20mm = record.parent_id.sieve_analysis_child_lines_20mm[1].passing_percent
                    else:
                        record.passing_20mm = 0.0  # Default if the second line is not available
                
                elif record == record.parent_id.combination10and20mm_child_lines[2]:
                    if len(record.parent_id.sieve_analysis_child_lines_20mm) > 2:
                        record.passing_20mm = record.parent_id.sieve_analysis_child_lines_20mm[2].passing_percent
                    else:
                        record.passing_20mm = 0.0  # Default if the second line is not available

                elif record == record.parent_id.combination10and20mm_child_lines[3]:
                    if len(record.parent_id.sieve_analysis_child_lines_20mm) > 3:
                        record.passing_20mm = record.parent_id.sieve_analysis_child_lines_20mm[3].passing_percent
                    else:
                        record.passing_20mm = 0.0  # Default if the second line is not available

                else:
                    record.passing_20mm = 0.0
            else:
                record.passing_20mm = 0.0


    @api.depends('parent_id.sieve_analysis_child_lines')
    def _compute_passing_10mm(self):
        for record in self:
        
            if record.parent_id:
                if record == record.parent_id.combination10and20mm_child_lines[0]:
                    if len(record.parent_id.sieve_analysis_child_lines) > 0:
                        record.passing_10mm = record.parent_id.sieve_analysis_child_lines[0].passing_percent
                    else:
                        record.passing_10mm = 0.0  

                elif record == record.parent_id.combination10and20mm_child_lines[1]:
                    if len(record.parent_id.sieve_analysis_child_lines) > 0:
                        record.passing_10mm = record.parent_id.sieve_analysis_child_lines[0].passing_percent
                    else:
                        record.passing_10mm = 0.0  # Default if the second line is not available
                
                elif record == record.parent_id.combination10and20mm_child_lines[2]:
                    if len(record.parent_id.sieve_analysis_child_lines) > 1:
                        record.passing_10mm = record.parent_id.sieve_analysis_child_lines[1].passing_percent
                    else:
                        record.passing_10mm = 0.0  # Default if the second line is not available

                elif record == record.parent_id.combination10and20mm_child_lines[3]:
                    if len(record.parent_id.sieve_analysis_child_lines) > 2:
                        record.passing_10mm = record.parent_id.sieve_analysis_child_lines[2].passing_percent
                    else:
                        record.passing_10mm = 0.0  # Default if the second line is not available

                elif record == record.parent_id.combination10and20mm_child_lines[4]:
                    if len(record.parent_id.sieve_analysis_child_lines) > 3:
                        record.passing_10mm = record.parent_id.sieve_analysis_child_lines[3].passing_percent
                    else:
                        record.passing_10mm = 0.0  # Default if the second line is not available

                else:
                    record.passing_10mm = 0.0
            else:
                record.passing_10mm = 0.0

    @api.depends('parent_id.combination10and20mm_child_lines')
    def _compute_passing_combined38(self):
        for record in self:
            if record.parent_id and record.parent_id.combination10and20mm_child_lines:
                combination_lines = record.parent_id.combination10and20mm_child_lines

                if record == combination_lines[0]:
                    record.passing_combined38 = record.passing_20mm * 38 / 100
                
                elif record == combination_lines[1]:
                    record.passing_combined38 = record.passing_20mm * 38 / 100

                elif record == combination_lines[2]:
                    record.passing_combined38 = record.passing_20mm * 38 / 100

                elif record == combination_lines[3]:
                    record.passing_combined38 = record.passing_20mm * 38 / 100
                
                else:
                    record.passing_combined38 = 0.0

            else:
                record.passing_combined38 = 0.0


    @api.depends('parent_id.combination10and20mm_child_lines')
    def _compute_passing_combined62(self):
        for record in self:
            if record.parent_id and record.parent_id.combination10and20mm_child_lines:
                combination_lines = record.parent_id.combination10and20mm_child_lines

                if record == combination_lines[0]:
                    record.passing_combined62 = record.passing_10mm * 62 / 100
                
                elif record == combination_lines[1]:
                    record.passing_combined62 = record.passing_10mm * 62 / 100

                elif record == combination_lines[2]:
                    record.passing_combined62 = record.passing_10mm * 62 / 100

                elif record == combination_lines[3]:
                    record.passing_combined62 = record.passing_10mm * 62 / 100
                
                else:
                    record.passing_combined62 = 0.0

            else:
                record.passing_combined62 = 0.0



    @api.depends('parent_id.combination10and20mm_child_lines')
    def _compute_passing_combined_granding(self):
        for record in self:
            if record.parent_id and record.parent_id.combination10and20mm_child_lines:
                combination_lines = record.parent_id.combination10and20mm_child_lines

                if record == combination_lines[0]:
                    record.combine_grading = record.passing_combined38 + record.passing_combined62
                
                elif record == combination_lines[1]:
                   record.combine_grading = record.passing_combined38 + record.passing_combined62

                elif record == combination_lines[2]:
                   record.combine_grading = record.passing_combined38 + record.passing_combined62

                elif record == combination_lines[3]:
                   record.combine_grading = record.passing_combined38 + record.passing_combined62
                
                else:
                    record.combine_grading = 0.0

            else:
                record.combine_grading = 0.0

class CombinedGrandingLine(models.Model):
    _name = "mechanical.combined.granding.line1"
    parent_id = fields.Many2one('mechanical.concrete.design1', string="Parent Id")
    
    sieve_size = fields.Char(string="IS SIEVE (mm)")
    combine_grading_10mm = fields.Float(string="10 mm",compute="_compute_combine_grading_10mm")
    combine_grading_20mm = fields.Float(string='20 mm',compute="_compute_combine_grading_20mm")

    combine_grading_csand = fields.Float(string="C/Sand",compute="_compute_combine_grading_csand")
    combine_grading_nsand = fields.Float(string='N/Sand')

    combine_grading_all = fields.Float(string='Combined Grading',compute="_compute_combined_granding")
    combine_grading_ll_all = fields.Float(string='LL')
    combine_grading_up_all = fields.Float(string='UP')


  

  




    @api.depends('parent_id.sieve_analysis_child_lines_20mm')
    def _compute_combine_grading_20mm(self):
        for record in self:
        
            if record.parent_id:
                if record == record.parent_id.combine_granding_child_lines[0]:
                    if len(record.parent_id.sieve_analysis_child_lines_20mm) > 0:
                        record.combine_grading_20mm = record.parent_id.sieve_analysis_child_lines_20mm[0].passing_percent
                    else:
                        record.combine_grading_20mm = 0.0  

                elif record == record.parent_id.combine_granding_child_lines[1]:
                    if len(record.parent_id.sieve_analysis_child_lines_20mm) > 1:
                        record.combine_grading_20mm = record.parent_id.sieve_analysis_child_lines_20mm[1].passing_percent
                    else:
                        record.combine_grading_20mm = 0.0  # Default if the second line is not available
                
             
                elif record == record.parent_id.combine_granding_child_lines[2]:
                    if len(record.parent_id.sieve_analysis_child_lines_20mm) > 3:
                        record.combine_grading_20mm = record.parent_id.sieve_analysis_child_lines_20mm[3].passing_percent
                    else:
                        record.combine_grading_20mm = 0.0  # Default if the second line is not available

                else:
                    record.combine_grading_20mm = 0.0
            else:
                record.combine_grading_20mm = 0.0


    @api.depends('parent_id.sieve_analysis_child_lines')
    def _compute_combine_grading_10mm(self):
        for record in self:
        
            if record.parent_id:
                if record == record.parent_id.combine_granding_child_lines[0]:
                    if len(record.parent_id.sieve_analysis_child_lines) > 0:
                        record.combine_grading_10mm = record.parent_id.sieve_analysis_child_lines[0].passing_percent
                    else:
                        record.combine_grading_10mm = 0.0  

                elif record == record.parent_id.combine_granding_child_lines[1]:
                    if len(record.parent_id.sieve_analysis_child_lines) > 0:
                        record.combine_grading_10mm = record.parent_id.sieve_analysis_child_lines[0].passing_percent
                    else:
                        record.combine_grading_10mm = 0.0  # Default if the second line is not available
                
                elif record == record.parent_id.combine_granding_child_lines[2]:
                    if len(record.parent_id.sieve_analysis_child_lines) > 2:
                        record.combine_grading_10mm = record.parent_id.sieve_analysis_child_lines[2].passing_percent
                    else:
                        record.combine_grading_10mm = 0.0  # Default if the second line is not available

              

                else:
                    record.combine_grading_10mm = 0.0
            else:
                record.combine_grading_10mm = 0.0



    @api.depends('parent_id.child_lines')
    def _compute_combine_grading_csand(self):
        for record in self:
        
            if record.parent_id:
                if record == record.parent_id.combine_granding_child_lines[0]:
                    if len(record.parent_id.child_lines) > 0:
                        record.combine_grading_csand = record.parent_id.child_lines[0].passing_percent
                    else:
                        record.combine_grading_csand = 0.0  

                elif record == record.parent_id.combine_granding_child_lines[1]:
                    if len(record.parent_id.child_lines) > 0:
                        record.combine_grading_csand = record.parent_id.child_lines[0].passing_percent
                    else:
                        record.combine_grading_csand = 0.0  # Default if the second line is not available
                
                elif record == record.parent_id.combine_granding_child_lines[2]:
                    if len(record.parent_id.child_lines) > 1:
                        record.combine_grading_csand = record.parent_id.child_lines[1].passing_percent
                    else:
                        record.combine_grading_csand = 0.0  # Default if the second line is not available

                elif record == record.parent_id.combine_granding_child_lines[3]:
                    if len(record.parent_id.child_lines) > 4:
                        record.combine_grading_csand = record.parent_id.child_lines[4].passing_percent
                    else:
                        record.combine_grading_csand = 0.0  # Default if the second line is not available
                
                elif record == record.parent_id.combine_granding_child_lines[4]:
                    if len(record.parent_id.child_lines) > 6:
                        record.combine_grading_csand = record.parent_id.child_lines[6].passing_percent
                    else:
                        record.combine_grading_csand = 0.0  # Default if the second line is not available

              

                else:
                    record.combine_grading_csand = 0.0
            else:
                record.combine_grading_csand = 0.0



    # @api.depends('parent_id.combine_granding_child_lines')
    # def _compute_combined_granding(self):
    #     for record in self:
    #         if record.parent_id and record.parent_id.combine_granding_child_lines:
    #             combination_lines = record.parent_id.combine_granding_child_lines

    #             if record == combination_lines[0 ] or record == combination_lines[1] or record == combination_lines[2 ] or record == combination_lines[3] or record == combination_lines[4]:
    #                 # Remove '%' and convert to float
    #                 mix_20mm = float(record.parent_id.mix_proporation_20mm.replace('%', '').strip() or 0)
    #                 mix_10mm = float(record.parent_id.mix_proporation_10mm.replace('%', '').strip() or 0)
    #                 mix_csand = float(record.parent_id.mix_proporation_csand.replace('%', '').strip() or 0)
    #                 mix_rsand = float(record.parent_id.mix_proporation_rsand.replace('%', '').strip() or 0)

    #                 record.combine_grading_all = (
    #                     record.combine_grading_20mm * mix_20mm +
    #                     record.combine_grading_10mm * mix_10mm +
    #                     record.combine_grading_csand * mix_csand +
    #                     record.combine_grading_nsand * mix_rsand
    #                 )
    #             else:
    #                 record.combine_grading_all = 0.0
    #         else:
    #             record.combine_grading_all = 0.0

    @api.depends('parent_id.combine_granding_child_lines')
    def _compute_combined_granding(self):
        for record in self:
            if record.parent_id and record.parent_id.combine_granding_child_lines:
                combination_lines = record.parent_id.combine_granding_child_lines

                if record in combination_lines[:5]:  # Simplified condition to check the first 5 records
                    # Safely handle 'None' or 'False' values
                    mix_20mm = float((record.parent_id.mix_proporation_20mm or '').replace('%', '').strip() or 0)
                    mix_10mm = float((record.parent_id.mix_proporation_10mm or '').replace('%', '').strip() or 0)
                    mix_csand = float((record.parent_id.mix_proporation_csand or '').replace('%', '').strip() or 0)
                    mix_rsand = float((record.parent_id.mix_proporation_rsand or '').replace('%', '').strip() or 0)

                    record.combine_grading_all = (
                        record.combine_grading_20mm * mix_20mm +
                        record.combine_grading_10mm * mix_10mm +
                        record.combine_grading_csand * mix_csand +
                        record.combine_grading_nsand * mix_rsand
                    )
                else:
                    record.combine_grading_all = 0.0
            else:
                record.combine_grading_all = 0.0



   



   

