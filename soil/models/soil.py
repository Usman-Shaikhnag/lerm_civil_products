from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
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


class Soil(models.Model):
    _name = "mechanical.soil1"
    _inherit = "lerm.eln"
    _description = 'mechanical.soil1'
    _rec_name = "name_soil"


    name_soil = fields.Char("Name",default="Soil")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    # tests = fields.Many2many("mechanical.soil.test",string="Tests")

    # CBR

    soil_name = fields.Char("Name",default="California Bearing Ratio")
    soil_visible = fields.Boolean("California Bearing Ratio Visible",compute="_compute_visible")
    # job_no_soil = fields.Char(string="Job No")
    # material_soil = fields.Char(String="Material")
    # start_date_soil = fields.Date("Start Date")
    # end_date_soil = fields.Date("End Date")
    soil_table = fields.One2many('mechanical.soils.cbr.line1','parent_id',string="CBR")
    chart_image_cbr = fields.Binary("Line Chart", compute="_compute_chart_image_cbr", store=True)


    # def generate_line_chart_cbr(self):
    #     # Prepare data for the chart
    #     x_values = []
    #     y_values = []
    #     for line in self.soil_table:
    #         x_values.append(line.penetration)
    #         y_values.append(line.load)
        
    #     # Create the line chart
    #     plt.plot(x_values, y_values, marker='o')
    #     plt.xlabel('Penetration')
    #     plt.ylabel('Load')
    #     plt.title('CBR')


    #     plt.ylim(bottom=0, top=max(y_values) + 10)

    #     for i in range(len(x_values)):
    #         plt.plot([x_values[i], x_values[i]], [0, y_values[i]], color='black', linestyle='--', alpha=0.5)
    #         if i < len(x_values) - 1:
    #             plt.plot([x_values[i], x_values[i + 1]], [y_values[i], y_values[i + 1]], color='black', linestyle='-', alpha=0.5)


        
    #     buffer = io.BytesIO()
    #     plt.savefig(buffer, format='png')
    #     plt.close()  # Close the figure to free up resources
    #     buffer.seek(0)
    
    #     # Convert the chart image to base64
    #     chart_image = base64.b64encode(buffer.read()).decode('utf-8')  
    #     return chart_image
    
    # @api.depends('soil_table')
    # def _compute_chart_image_cbr(self):
    #     try:
    #         for record in self:
    #             chart_image = record.generate_line_chart_cbr()
    #             record.chart_image_cbr = chart_image
    #     except:
    #         pass 

    def generate_line_chart_cbr(self):
        # Prepare data for the chart
        x_values = []
        y_values = []
        for line in self.soil_table:
            x_values.append(line.penetration)
            y_values.append(line.load)
        
        # Create the line chart
        plt.plot(x_values, y_values, marker='o')
        plt.xlabel('Penetration')
        plt.ylabel('Load')
        plt.title('CBR')


        plt.ylim(bottom=0, top=max(y_values) + 10)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()  # Close the figure to free up resources
        buffer.seek(0)
    
        # Convert the chart image to base64
        chart_image = base64.b64encode(buffer.read()).decode('utf-8')  
        return chart_image
    
    @api.depends('soil_table')
    def _compute_chart_image_cbr(self):
        try:
            for record in self:
                chart_image = record.generate_line_chart_cbr()
                record.chart_image_cbr = chart_image
        except:
            pass


    # FSI
    fsi_name = fields.Char("Name",default="Free Swell Index")
    fsi_visible = fields.Boolean("Free Swell Index Visible",compute="_compute_visible")
    # job_no_fsi = fields.Char(string="Job No")
    # material_fsi = fields.Char(String="Material")
    # start_date_fsi = fields.Date("Start Date")
    # end_date_fsi = fields.Date("End Date")
    fsi_table = fields.One2many('mechanical.soil.free.swell.index.line1','parent_id',string="FSI")
    max_fsi = fields.Float(string="Max FSI", compute="_compute_max_fsi", store=True)

    @api.depends('fsi_table.fsi')
    def _compute_max_fsi(self):
        for record in self:
            if record.fsi_table:
                max_fsi = max(record.fsi_table.mapped('fsi'))
                record.max_fsi = max_fsi
            else:
                record.max_fsi = 0.0

    max_fsi_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_max_fsi_conformity", store=True)

    @api.depends('max_fsi','eln_ref','grade')
    def _compute_max_fsi_conformity(self):
        
        for record in self:
            record.max_fsi_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ght4125-ca64-44dd-b0ae-228aacf04998')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ght4125-ca64-44dd-b0ae-228aacf04998')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.max_fsi - record.max_fsi*mu_value
                    upper = record.max_fsi + record.max_fsi*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.max_fsi_conformity = 'pass'
                        break
                    else:
                        record.max_fsi_conformity = 'fail'

    max_fsi_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_max_fsi_nabl", store=True)

    @api.depends('max_fsi','eln_ref','grade')
    def _compute_max_fsi_nabl(self):
        
        for record in self:
            record.max_fsi_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ght4125-ca64-44dd-b0ae-228aacf04998')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ght4125-ca64-44dd-b0ae-228aacf04998')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.max_fsi - record.max_fsi*mu_value
            upper = record.max_fsi + record.max_fsi*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.max_fsi_nabl = 'pass'
                break
            else:
                record.max_fsi_nabl = 'fail'
    
    

    

    # Sieve Analysis
    sieve_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")
    # job_no_sieve = fields.Char(string="Job No")
    # material_sieve = fields.Char(String="Material")
    # start_date_sieve = fields.Date("Start Date")
    # end_date_sieve = fields.Date("End Date")
    child_lines = fields.One2many('mechanical.soil.sieve.analysis.line1','parent_id',string="Sieve Analysis",default=lambda self: self._default_sieve_analysis_child_lines())
    total1 = fields.Integer(string="Total",compute="_compute_total")
    # cumulative = fields.Float(string="Cumulative",compute="_compute_cumulative")


    @api.model
    def _default_sieve_analysis_child_lines(self):
        default_lines = [
            (0, 0, {'sieve_size': '75 mm'}),
            (0, 0, {'sieve_size': '19 mm'}),
            (0, 0, {'sieve_size': '4.75 mm'}),
            (0, 0, {'sieve_size': '2 mm'}),
            (0, 0, {'sieve_size': '425 mic'}),
            (0, 0, {'sieve_size': '75 mic'}),
            (0, 0, {'sieve_size': 'Pan'})
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
                    previous_line_record = self.env['mechanical.soil.sieve.analysis.line1'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
                    line.write({'cumulative_retained': previous_line_record + line.percent_retained})
                    line.write({'passing_percent': 100-(previous_line_record + line.percent_retained)})
                    print("Previous Cumulative",previous_line_record)
                    

                
    

   
    @api.depends('child_lines.wt_retained')
    def _compute_total(self):
        for record in self:
            print("recordd",record)
            record.total1 = sum(record.child_lines.mapped('wt_retained'))

    # @api.onchange('child_lines.wt_retained')
    # def _compute_cumulative(self):
    #     for record in self:
    #         record.total = sum(record.child_lines.mapped('wt_retained'))


    @api.onchange('total1')
    def _onchange_total(self):
        for line in self.child_lines:
            line._compute_percent_retained()
            # line._compute_cumulative_retained()


    # Havy Compaction-MDD
    heavy_name = fields.Char("Name",default="Heavy Compaction OMC/MDD")
    heavy_visible = fields.Boolean("Heavy Compaction-MDD Visible",compute="_compute_visible")
    heavy_table = fields.One2many('mechanical.heavy.compaction.line1','parent_id',string="Heavy Compaction")
    wt_of_modul = fields.Integer(string="Weight of Mould in gm")
    vl_of_modul = fields.Integer(string="Volume of Mould in cc")
    
    mmd = fields.Float(string="MMD gm/cc", compute="_compute_max_dry_density_heavy", store=True)
    omc = fields.Float(string="OMC %", compute="_compute_max_omc_heavy", store=True)

    @api.depends('heavy_table.dry_density')
    def _compute_max_dry_density_heavy(self):
        for record in self:
            max_dry_density_heavy = max(record.heavy_table.mapped('dry_density'), default=0.0)
            record.mmd = max_dry_density_heavy

    @api.depends('heavy_table.dry_density', 'heavy_table.moisture', 'mmd')
    def _compute_max_omc_heavy(self):
        for record in self:
            max_dry_density_light_omc = record.mmd
            corresponding_moisture_heavy = next((line.moisture for line in record.heavy_table if line.dry_density == max_dry_density_light_omc), 0.0)
            record.omc = corresponding_moisture_heavy


    heavy_table_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_heavy_table_conformity", store=True)

    @api.depends('mmd','eln_ref','grade')
    def _compute_heavy_table_conformity(self):
        
        for record in self:
            record.heavy_table_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-2ee981be0d7c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-2ee981be0d7c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.mmd - record.mmd*mu_value
                    upper = record.mmd + record.mmd*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.heavy_table_conformity = 'pass'
                        break
                    else:
                        record.heavy_table_conformity = 'fail'

    heavy_table_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_heavy_table_nabl", store=True)

    @api.depends('mmd','eln_ref','grade')
    def _compute_heavy_table_nabl(self):
        
        for record in self:
            record.heavy_table_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-2ee981be0d7c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210vbf-20fb-4843-aa0e-2ee981be0d7c')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.mmd - record.mmd*mu_value
            upper = record.mmd + record.mmd*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.heavy_table_nabl = 'pass'
                break
            else:
                record.heavy_table_nabl = 'fail'


    graph_image_density = fields.Binary("Line Chart", compute="_compute_graph_image_density", store=True)



    def generate_line_chart_density(self):
        # Prepare data for the chart
        plt.figure(figsize=(12, 6))
        x_values = []
        y_values = []
        for line in self.heavy_table:
            x_values.append(line.moisture)
            y_values.append(line.dry_density)



        plt.plot(x_values, y_values, marker='o')
        plt.xlabel('% Moisture')
        plt.ylabel('Dry Density')
        plt.title('Heavy Compaction OMC/MDD')

       
        # Adjust xlim to add space on both ends of the x-axis
        plt.xlim(left=5.0, right=max(x_values) )

        plt.ylim(bottom=0, top=max(y_values) + 1.0)

        for i in range(len(x_values)):
            plt.plot([x_values[i], x_values[i]], [0, y_values[i]], color='black', linestyle='--', alpha=0.5)
            if i < len(x_values) - 1:
                plt.plot([x_values[i], x_values[i + 1]], [y_values[i], y_values[i + 1]], color='black', linestyle='-', alpha=0.5)



        # Find the index of the maximum y value
        max_y_index = y_values.index(max(y_values))

        # Add a horizontal line at the maximum y value
        plt.axhline(y=y_values[max_y_index], color='red', linestyle='--')

        # Add a vertical line at the corresponding x value
        plt.axvline(x=x_values[max_y_index], color='red', linestyle='--')


        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()  # Close the figure to free up resources
        buffer.seek(0)
    
        # Convert the chart image to base64
        chart_image = base64.b64encode(buffer.read()).decode('utf-8')  
        return chart_image
        plt.close()
        
       
    

    @api.depends('heavy_table')
    def _compute_graph_image_density(self):
        try:
            for record in self:
                chart_image = record.generate_line_chart_density()
                record.graph_image_density = chart_image
        except:
            pass 


    # Light Compaction-OMC
    light_omc_name1 = fields.Char("Name",default="Light Compaction OMC/MDD")
    light_omc_visible = fields.Boolean("Light Compaction-OMC Visible",compute="_compute_visible")
    light_omc_table = fields.One2many('mechanical.light.omc.compaction.line1','parent_id',string="Heavy Compaction")
    wt_of_modul_light_omc = fields.Integer(string="Weight of Mould in gm")
    vl_of_modul_light_omc = fields.Integer(string="Volume of Mould in cc")

    mmd_light_omc = fields.Float(string="MMD gm/cc", compute="_compute_max_dry_density", store=True)
    omc_light_omc = fields.Float(string="OMC %", compute="_compute_max_omc", store=True)

    light_omc_table_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_light_omc_table_conformity", store=True)

    @api.depends('mmd_light_omc','eln_ref','grade')
    def _compute_light_omc_table_conformity(self):
        
        for record in self:
            record.light_omc_table_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32145bvfgr-d8ad-4000-9376-439ef2a64c70')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32145bvfgr-d8ad-4000-9376-439ef2a64c70')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.mmd_light_omc - record.mmd_light_omc*mu_value
                    upper = record.mmd_light_omc + record.mmd_light_omc*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.light_omc_table_conformity = 'pass'
                        break
                    else:
                        record.light_omc_table_conformity = 'fail'

    light_omc_table_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_light_omc_table_nabl", store=True)

    @api.depends('mmd_light_omc','eln_ref','grade')
    def _compute_light_omc_table_nabl(self):
        
        for record in self:
            record.light_omc_table_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32145bvfgr-d8ad-4000-9376-439ef2a64c70')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32145bvfgr-d8ad-4000-9376-439ef2a64c70')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.mmd_light_omc - record.mmd_light_omc*mu_value
            upper = record.mmd_light_omc + record.mmd_light_omc*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.light_omc_table_nabl = 'pass'
                break
            else:
                record.light_omc_table_nabl = 'fail'
    

    @api.depends('light_omc_table.dry_density')
    def _compute_max_dry_density(self):
        for record in self:
            max_dry_density_light_omc = max(record.light_omc_table.mapped('dry_density'), default=0.0)
            record.mmd_light_omc = max_dry_density_light_omc

    @api.depends('light_omc_table.dry_density', 'light_omc_table.moisture')
    def _compute_max_omc(self):
        for record in self:
            max_dry_density_light_omc = record.mmd_light_omc  # Using the max value from _compute_max_dry_density
            corresponding_moisture_light_omc = next((line.moisture for line in record.light_omc_table if line.dry_density == max_dry_density_light_omc), 0.0)
            record.omc_light_omc = corresponding_moisture_light_omc


    graph_image_light_omc = fields.Binary("Line Chart", compute="_compute_graph_image_density_omc_light", store=True)



    def generate_line_chart_light_omc (self):
        # Prepare data for the chart
        plt.figure(figsize=(12, 6))
        x_value = []
        y_value = []
        for line in self.light_omc_table:
            x_value.append(line.moisture)
            y_value.append(line.dry_density)



        plt.plot(x_value, y_value, marker='o')
        plt.xlabel('% Moisture')
        plt.ylabel('Dry Density')
        plt.title('Light Compaction OMC/MDD')

       
        # Adjust xlim to add space on both ends of the x-axis
        plt.xlim(left=5.0, right=max(x_value) + 1.5 )

        plt.ylim(bottom=0, top=max(y_value) + 1.0)

        for i in range(len(x_value)):
            plt.plot([x_value[i], x_value[i]], [0, y_value[i]], color='black', linestyle='--', alpha=0.5)
            if i < len(x_value) - 1:
                plt.plot([x_value[i], x_value[i + 1]], [y_value[i], y_value[i + 1]], color='black', linestyle='-', alpha=0.5)



        # Find the index of the maximum y value
        max_y_index = y_value.index(max(y_value))

        # Add a horizontal line at the maximum y value
        plt.axhline(y=y_value[max_y_index], color='red', linestyle='--')

        # Add a vertical line at the corresponding x value
        plt.axvline(x=x_value[max_y_index], color='red', linestyle='--')


        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()  # Close the figure to free up resources
        buffer.seek(0)
    
        # Convert the chart image to base64
        chart_image_light_omc = base64.b64encode(buffer.read()).decode('utf-8')  
        return chart_image_light_omc
        plt.close()
        
       
    

    @api.depends('light_omc_table')
    def _compute_graph_image_density_omc_light(self):
        try:
            for record in self:
                chart_image_light_omc = record.generate_line_chart_light_omc()
                record.graph_image_light_omc = chart_image_light_omc
        except:
            pass 


   

    # Liquid Limit
    liquid_limit_name = fields.Char("Name",default="Liquid Limit")
    liquid_limit_visible = fields.Boolean("Liquid Limit Visible",compute="_compute_visible")
    # job_no_liquid_limit = fields.Char(string="Job No")
    # material_liquid_limit = fields.Char(String="Material")
    # start_date_liquid_limit = fields.Date("Start Date")
    # end_date_liquid_limit = fields.Date("End Date")
    child_liness = fields.One2many('mechanical.liquid.limits.line1','parent_id',string="Liquid Limit")
    liquid_limit = fields.Float('Liquid Limit')

    remarks_liquid_limit = fields.Selection([
        ('plastic', 'Plastic'),
        ('non-plastic', 'Non-Plastic')],"Remarks",store=True)

    liquid_limit_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_liquid_limit_conformity", store=True)

    @api.depends('liquid_limit','eln_ref','grade')
    def _compute_liquid_limit_conformity(self):
        
        for record in self:
            record.liquid_limit_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23fg21gh-7202-4d62-864b-8efa58b6b61f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23fg21gh-7202-4d62-864b-8efa58b6b61f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.liquid_limit - record.liquid_limit*mu_value
                    upper = record.liquid_limit + record.liquid_limit*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.liquid_limit_conformity = 'pass'
                        break
                    else:
                        record.liquid_limit_conformity = 'fail'

    liquid_limit_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_liquid_limit_nabl", store=True)

    @api.depends('liquid_limit','eln_ref','grade')
    def _compute_liquid_limit_nabl(self):
        
        for record in self:
            record.liquid_limit_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23fg21gh-7202-4d62-864b-8efa58b6b61f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23fg21gh-7202-4d62-864b-8efa58b6b61f')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.liquid_limit - record.liquid_limit*mu_value
            upper = record.liquid_limit + record.liquid_limit*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.liquid_limit_nabl = 'pass'
                break
            else:
                record.liquid_limit_nabl = 'fail'
    
    
    # def calculate_result(self):
    are_child_lines_filled = fields.Boolean(compute='_compute_are_child_lines_filled',string='child lines',store=False)

    @api.depends('child_liness.moisture', 'child_liness.mass_of_dry_sample')  # Replace with actual field names
    def _compute_are_child_lines_filled(self):
        for record in self:
            all_lines_filled = all(line.moisture and line.mass_of_dry_sample for line in record.child_liness)
            record.are_child_lines_filled = all_lines_filled

    

    def liquid_calculation(self):
        print('<<<<<<<<<<<<')
        for record in self:
            data = self.child_liness
           
            result = 0  # Initialize result before the loop
            print(data, 'data')
            container2Moisture = data[1].moisture
            container1Moisture = data[0].moisture
            container3Moisture = data[2].moisture
            cont2blow = data[1].blwo_no
            cont3blow = data[2].blwo_no
            result = (container2Moisture * 100 - ((container2Moisture - container3Moisture) * 100 * (25 - cont2blow)) / (cont3blow - cont2blow)) / 100
            print(result, 'final result')
        self.write({'liquid_limit': result})

    
     # Plastic Limit
    plastic_limit_name = fields.Char("Name",default="Plastic Limit")
    plastic_limit_visible = fields.Boolean("Plastic Limit Visible",compute="_compute_visible")
    # job_no_plastic_limit = fields.Char(string="Job No")
    # material_plastic_limit = fields.Char(String="Material")
    # start_date_plastic_limit = fields.Date("Start Date")
    # end_date_plastic_limit = fields.Date("End Date")

    plastic_limit_table = fields.One2many('mechanical.plasticl.limit.line1','parent_id',string="Parameter")

    plastic_limit = fields.Float(string="Average of % Moisture", compute="_compute_plastic_limit")
    remarks_plastic = fields.Selection([
        ('plastic', 'Plastic'),
        ('non-plastic', 'Non-Plastic')],"Remarks",store=True)

    plasticity_index = fields.Char(string="Plasticity Index", compute="_compute_plasticity_index")

    plasticity_index_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_plasticity_limit_conformity", store=True)

    @api.depends('plastic_limit','eln_ref','grade')
    def _compute_plasticity_limit_conformity(self):
        
        for record in self:
            record.plasticity_index_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','120vbf14-2ff0-4b81-aca1-0e07dab7cd87')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','120vbf14-2ff0-4b81-aca1-0e07dab7cd87')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.plastic_limit - record.plastic_limit*mu_value
                    upper = record.plastic_limit + record.plastic_limit*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.plasticity_index_conformity = 'pass'
                        break
                    else:
                        record.plasticity_index_conformity = 'fail'

    plasticity_index_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_plasticity_limi_nabl", store=True)

    @api.depends('plastic_limit','eln_ref','grade')
    def _compute_plasticity_limi_nabl(self):
        
        for record in self:
            record.plasticity_index_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','120vbf14-2ff0-4b81-aca1-0e07dab7cd87')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','120vbf14-2ff0-4b81-aca1-0e07dab7cd87')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.plastic_limit - record.plastic_limit*mu_value
            upper = record.plastic_limit + record.plastic_limit*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.plasticity_index_nabl = 'pass'
                break
            else:
                record.plasticity_index_nabl = 'fail'




    @api.depends('plastic_limit_table.moisture')
    def _compute_plastic_limit(self):
        for record in self:
            total_moisture = sum(record.plastic_limit_table.mapped('moisture'))
            record.plastic_limit = total_moisture / len(record.plastic_limit_table) if record.plastic_limit_table else 0.0

    # @api.depends('plastic_limit')
    # def _compute_plasticity_index(self):
    #     for record in self:
    #         record.plasticity_index = 46.14 - record.plastic_limit

    # @api.depends('plastic_limit')
    # def _compute_plasticity_index(self):
    #     for record in self:
    #         if record.plastic_limit == 0.0:
    #             record.plasticity_index = 'Null'  # Use an empty string to represent null for a character field
    #         else:
    #             record.plasticity_index = str(46.14 - record.plastic_limit)  # Convert the result to a string if needed

    @api.depends('plastic_limit','liquid_limit')
    def _compute_plasticity_index(self):
        for record in self:
            if record.plastic_limit == 0.0:
                record.plasticity_index = 'Null'
            else:
                plasticity_value = record.liquid_limit - record.plastic_limit
                # Format the string representation with 2 decimal places
                record.plasticity_index = '{:.2f}'.format(plasticity_value)



    #  # Plasticity Index
    # plasticity_index_visible = fields.Boolean("Plasticity Index Visible",compute="_compute_visible")
    # plasticity_index1 = fields.Char("Plasticity Index",compute="_compute_plasticity_index1")
    # remarks_plasticity_index1 = fields.Selection([
    #     ('plastic', 'Plastic'),
    #     ('non-plastic', 'Non-Plastic')],"Remarks",store=True)

    # @api.depends('plastic_limit')
    # def _compute_plasticity_index1(self):
    #     for record in self:
    #         if record.plastic_limit == 0.0:
    #             record.plasticity_index1 = 'Null'
    #         else:
    #             plasticity_value = 46.14 - record.plastic_limit
    #             # Format the string representation with 2 decimal places
    #             record.plasticity_index1 = '{:.2f}'.format(plasticity_value)


    # plasticity_index_conformity1 = fields.Selection([
    #         ('pass', 'Pass'),
    #         ('fail', 'Fail')], string="Conformity", compute="_compute_plasticity_index_conformity1", store=True)



    # @api.depends('plasticity_index1','eln_ref','grade')
    # def _compute_plasticity_index_conformity1(self):
        
    #     for record in self:
    #         record.plasticity_index_conformity1 = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1411e90a-70ac-4f77-b544-26e5b8d6dd71')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1411e90a-70ac-4f77-b544-26e5b8d6dd71')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 req_min = material.req_min
    #                 req_max = material.req_max
    #                 mu_value = line.mu_value
                    
    #                 lower = record.plasticity_index1 - record.plasticity_index1*mu_value
    #                 upper = record.plasticity_index1 + record.plasticity_index1*mu_value
    #                 if lower >= req_min and upper <= req_max:
    #                     record.plasticity_index_conformity1 = 'pass'
    #                     break
    #                 else:
    #                     record.plasticity_index_conformity1 = 'fail'

    # plasticity_index_nabl1 = fields.Selection([
    #     ('pass', 'NABL'),
    #     ('fail', 'Non-NABL')], string="NABL", compute="_compute_plasticity_index_nabl1", store=True)

    # @api.depends('plasticity_index1','eln_ref','grade')
    # def _compute_plasticity_index_nabl1(self):
        
    #     for record in self:
    #         record.plasticity_index_nabl1 = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1411e90a-70ac-4f77-b544-26e5b8d6dd71')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1411e90a-70ac-4f77-b544-26e5b8d6dd71')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 lab_min = line.lab_min_value
    #                 lab_max = line.lab_max_value
    #                 mu_value = line.mu_value
                    
    #                 lower = record.plasticity_index1 - record.plasticity_index1*mu_value
    #                 upper = record.plasticity_index1 + record.plasticity_index1*mu_value
    #                 if lower >= lab_min and upper <= lab_max:
    #                     record.plasticity_index_nabl1 = 'pass'
    #                     break
    #                 else:
    #                     record.plasticity_index_nabl1 = 'fail'


     # Dry Density by Sand Replacement method
    dry_density_name = fields.Char("Name",default="Dry Density by Sand Replacement method")
    dry_density_visible = fields.Boolean("Dry Density by Sand Replacement method Visible",compute="_compute_visible")
    # job_no_dry_density = fields.Char(string="Job No")
    # material_dry_density = fields.Char(String="Material")
    # start_date_dry_density = fields.Date("Start Date")
    # end_date_dry_density = fields.Date("End Date")

    dry_density_table = fields.One2many('mechanical.dry.dencity.line1','parent_id',string="Parameter")
    mmd_drydencity = fields.Float(string="MMD gm/cc", store=True)
    omc_drydencity = fields.Float(string="OMC %", store=True)
    avg_degree_of_compaction = fields.Float(string="Degree of Compaction in %",compute="_compute_avg_degree_of_compaction")

    @api.depends('dry_density_table.degree_of_compaction')
    def _compute_avg_degree_of_compaction(self):
        for record in self:
            degree_of_compaction_values = record.dry_density_table.mapped('degree_of_compaction')
            if degree_of_compaction_values:
                avg_degree_of_compaction = sum(degree_of_compaction_values) / len(degree_of_compaction_values)
                record.avg_degree_of_compaction = avg_degree_of_compaction
            else:
                record.avg_degree_of_compaction = 0.0

    


   

   

    degree_of_compaction_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_degree_of_compaction_conformity", store=True)

    @api.depends('avg_degree_of_compaction','eln_ref','grade')
    def _compute_degree_of_compaction_conformity(self):
        
        for record in self:
            record.degree_of_compaction_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1204523se-0c28-4c8b-924f-7e6988a658ee')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1204523se-0c28-4c8b-924f-7e6988a658ee')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_degree_of_compaction - record.avg_degree_of_compaction*mu_value
                    upper = record.avg_degree_of_compaction + record.avg_degree_of_compaction*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.degree_of_compaction_conformity = 'pass'
                        break
                    else:
                        record.degree_of_compaction_conformity = 'fail'

    degree_of_compaction_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_degree_of_compaction_nabl", store=True)

    @api.depends('avg_degree_of_compaction','eln_ref','grade')
    def _compute_degree_of_compaction_nabl(self):
        
        for record in self:
            record.degree_of_compaction_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1204523se-0c28-4c8b-924f-7e6988a658ee')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1204523se-0c28-4c8b-924f-7e6988a658ee')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_degree_of_compaction - record.avg_degree_of_compaction*mu_value
            upper = record.avg_degree_of_compaction + record.avg_degree_of_compaction*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.degree_of_compaction_nabl = 'pass'
                break
            else:
                record.degree_of_compaction_nabl = 'fail'


    # added
    # field Density by Sand Replacement method
    field_density_name = fields.Char("Name",default="Field Density by Sand Replacement method")
    field_density_visible = fields.Boolean("Field Density by Sand Replacement method Visible",compute="_compute_visible")
    # job_no_dry_density = fields.Char(string="Job No")
    # material_dry_density = fields.Char(String="Material")
    # start_date_dry_density = fields.Date("Start Date")
    # end_date_dry_density = fields.Date("End Date")

    field_density_table = fields.One2many('mechanical.field.dencity.line1','parent_id',string="Parameter")
    mmd_fielddencity = fields.Float(string="MMD gm/cc", store=True)
    omc_fielddencity = fields.Float(string="OMC %", store=True)
    avg_degree_of_compaction = fields.Float(string="Degree of Compaction in %",compute="_compute_avg_degree_of_compaction")

    @api.depends('field_density_table.degree_of_compaction')
    def _compute_avg_degree_of_compaction(self):
        for record in self:
            degree_of_compaction_values = record.field_density_table.mapped('degree_of_compaction')
            if degree_of_compaction_values:
                avg_degree_of_compaction = sum(degree_of_compaction_values) / len(degree_of_compaction_values)
                record.avg_degree_of_compaction = avg_degree_of_compaction
            else:
                record.avg_degree_of_compaction = 0.0

    


   

   

    degree_of_compaction_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_degree_of_compaction_conformity", store=True)

    @api.depends('avg_degree_of_compaction','eln_ref','grade')
    def _compute_degree_of_compaction_conformity(self):
        
        for record in self:
            record.degree_of_compaction_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210fgr1-1ebd-4437-ba47-2633e8d9ec27')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210fgr1-1ebd-4437-ba47-2633e8d9ec27')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_degree_of_compaction - record.avg_degree_of_compaction*mu_value
                    upper = record.avg_degree_of_compaction + record.avg_degree_of_compaction*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.degree_of_compaction_conformity = 'pass'
                        break
                    else:
                        record.degree_of_compaction_conformity = 'fail'

    degree_of_compaction_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_degree_of_compaction_nabl", store=True)

    @api.depends('avg_degree_of_compaction','eln_ref','grade')
    def _compute_degree_of_compaction_nabl(self):
        
        for record in self:
            record.degree_of_compaction_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210fgr1-1ebd-4437-ba47-2633e8d9ec27')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210fgr1-1ebd-4437-ba47-2633e8d9ec27')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_degree_of_compaction - record.avg_degree_of_compaction*mu_value
            upper = record.avg_degree_of_compaction + record.avg_degree_of_compaction*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.degree_of_compaction_nabl = 'pass'
                break
            else:
                record.degree_of_compaction_nabl = 'fail'

    # uptill

  

    
   
    # Moisture Content

    moisture_content_name = fields.Char("Name",default="Moisture Content")
    moisture_content_visible = fields.Boolean("Moisture Content Visible",compute="_compute_visible")
    # job_no_moisture_content = fields.Char(string="Job No")
    # material_moisture_content = fields.Char(String="Material")
    # start_date_moisture_content = fields.Date("Start Date")
    # end_date_moisture_content = fields.Date("End Date")

    moisture_content_table = fields.One2many('mechanical.moisture.content.line1','parent_id',string="Parameter")
    average_block = fields.Float(string="Average",compute="_compute_average_moisture_content")

    moisture_content_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_moisture_contentconformity", store=True)

    @api.depends('average_block','eln_ref','grade')
    def _compute_moisture_contentconformity(self):
        
        for record in self:
            record.moisture_content_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','104ght24-72cb-40e8-be97-e17fc20ff3fa')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','104ght24-72cb-40e8-be97-e17fc20ff3fa')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_block - record.average_block*mu_value
                    upper = record.average_block + record.average_block*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.moisture_content_conformity = 'pass'
                        break
                    else:
                        record.moisture_content_conformity = 'fail'

    moisture_content_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_moisture_content_nabl", store=True)

    @api.depends('average_block','eln_ref','grade')
    def _compute_moisture_content_nabl(self):
        
        for record in self:
            record.moisture_content_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','104ght24-72cb-40e8-be97-e17fc20ff3fa')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','104ght24-72cb-40e8-be97-e17fc20ff3fa')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_block - record.average_block*mu_value
            upper = record.average_block + record.average_block*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.moisture_content_nabl = 'pass'
                break
            else:
                record.moisture_content_nabl = 'fail'



    @api.depends('moisture_content_table.moisture_content')
    def _compute_average_moisture_content(self):
        for record in self:
            total_moisture_content = sum(record.moisture_content_table.mapped('moisture_content'))
            num_lines = len(record.moisture_content_table)
            record.average_block = total_moisture_content / num_lines if num_lines else 0.0

     ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
      
        for record in self:
            record.soil_visible = False
            record.fsi_visible  = False  
            record.sieve_visible = False
            record.heavy_visible = False
            # record.heavy_omc_visible = False
            record.light_omc_visible = False
            # record.light_mdd_visible = False
            record.liquid_limit_visible = False
            record.plastic_limit_visible = False
            # record.plasticity_index_visible = False
            record.dry_density_visible = False
            # added
            record.field_density_visible = False
            record.moisture_content_visible = False

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '15247gtr-2065-4532-814a-3a4c1e884305':
                    record.soil_visible = True
                if sample.internal_id == 'ght4125-ca64-44dd-b0ae-228aacf04998':
                    record.fsi_visible = True
                if sample.internal_id == '12014fgr-5c56-475b-9a89-93a59c9ee3a2':
                    record.sieve_visible = True

                if sample.internal_id == '3210vbf-20fb-4843-aa0e-2ee981be0d7c':
                    record.heavy_visible = True

                # if sample.internal_id == '1204523se-0c28-4c8b-924f-7e6988a658ee':
                #     record.heavy_omc_visible = True

                if sample.internal_id == '32145bvfgr-d8ad-4000-9376-439ef2a64c70':
                    record.light_omc_visible = True

                # if sample.internal_id == '0eb532a8-7683-42b3-b9b2-36904ae2cd15':
                #     record.light_mdd_visible = True

                if sample.internal_id == '23fg21gh-7202-4d62-864b-8efa58b6b61f':
                    record.liquid_limit_visible = True
               
                if sample.internal_id == '120vbf14-2ff0-4b81-aca1-0e07dab7cd87':
                    record.plastic_limit_visible = True
                    
                # if sample.internal_id == '1411e90a-70ac-4f77-b544-26e5b8d6dd71':
                #     record.plasticity_index_visible = True


                if sample.internal_id == '1204523se-0c28-4c8b-924f-7e6988a658ee':
                    record.dry_density_visible = True
                
                # added
                if sample.internal_id == '3210fgr1-1ebd-4437-ba47-2633e8d9ec27':
                    record.field_density_visible = True

                if sample.internal_id == '104ght24-72cb-40e8-be97-e17fc20ff3fa':
                    record.moisture_content_visible = True

    def open_eln_page(self):
        # import wdb; wdb.set_trace()

        return {
                'view_mode': 'form',
                'res_model': "lerm.eln",
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.eln_ref.id,
                
            }

    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(Soil, self).create(vals)
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
        record = self.env['mechanical.soil1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

class SoilTest(models.Model):
    _name = "mechanical.soil.test"
    _rec_name = "name"
    name = fields.Char("Name")


class SoilCBRLine(models.Model):
    _name = "mechanical.soils.cbr.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    penetration = fields.Float(string="Penetration in mm")
    proving_reading = fields.Float(string="Proving Ring Reading")
    load = fields.Float(string="Load in Kg", compute="_compute_load")


    @api.depends('proving_reading')
    def _compute_load(self):
        for record in self:
            record.load = record.proving_reading * 6.96


class FreeSwellIndexLine(models.Model):
    _name = "mechanical.soil.free.swell.index.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    wt_sample = fields.Float(string="Mass of wet sample")
    dry_sample = fields.Float(string="Volume of dry sample in cc")
    v_sample_kerosin = fields.Float(string="Volume of sample after immersing in kerosin for 24 Hrs. in cc, V1")
    v_sample_water = fields.Float(string="Volume of sample after immersing in water for 24 Hrs. in cc, V2")
    increase_volume = fields.Float(string="Increase in Volume, (V2-V1) in cc", compute="_compute_volume")
    fsi = fields.Float(string="% FSI = (V2-V1)/V1 x 100", compute="_compute_fsi")


    @api.depends('v_sample_water', 'v_sample_kerosin')
    def _compute_volume(self):
        for record in self:
            record.increase_volume = record.v_sample_water - record.v_sample_kerosin


    @api.depends('v_sample_water', 'v_sample_kerosin')
    def _compute_volume(self):
        for record in self:
            record.increase_volume = record.v_sample_water - record.v_sample_kerosin

    @api.depends('increase_volume', 'v_sample_kerosin')
    def _compute_fsi(self):
        for record in self:
            if record.v_sample_kerosin != 0:
                record.fsi = (record.increase_volume / record.v_sample_kerosin) * 100
            else:
                record.fsi = 0.0

class SoilSieveAnalysisLine(models.Model):
    _name = "mechanical.soil.sieve.analysis.line1"
    parent_id = fields.Many2one('mechanical.soil1', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained")
    cumulative_retained = fields.Float(string="Cum. Retained %",  store=True)
    passing_percent = fields.Float(string="Passing %")

    # @api.onchange('cumulative_retained')
    # def _compute_passing_percent(self):
    #     for record in self:
    #         record.passing_percent = 100 - record.cumulative_retained


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SoilSieveAnalysisLine, self).create(vals)

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

            new_self = super(SoilSieveAnalysisLine, self).write(vals)

            if 'wt_retained' in vals:
                for record in self:
                    record.parent_id._compute_total()

            return new_self

        return super(SoilSieveAnalysisLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(SoilSieveAnalysisLine, self).unlink()

        if parent_id:
            parent_id.child_lines._reorder_serial_numbers()

        return res

    
   

    @api.depends('wt_retained', 'parent_id.total1')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = record.wt_retained / self.parent_id.total1 * 100
            except ZeroDivisionError:
                record.percent_retained = 0


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


class HEAVYCOMPACTIONLINE(models.Model):
    _name = "mechanical.heavy.compaction.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")

    determination_no = fields.Float(string="Determination No")
    wt_of_modul_compact = fields.Integer(string="Weight of Mould + Compacted sample in gm")
    wt_of_compact = fields.Integer(string="Weight of compacted sample in gm", compute="_compute_wt_of_compact")
    bulk_density = fields.Float(string="Bulk Density of sample in gm/cc", compute="_compute_bulk_density")
    container_no = fields.Integer(string="Container No")
    wt_of_container = fields.Float(string="Weight of Container in gm")
    wt_of_container_wet = fields.Float(string="Weight of Container + wet sample in gm")
    wt_of_container_dry = fields.Float(string="Weight of Container + dry sample in gm")
    wt_of_dry_sample = fields.Float(string="Weight of dry sample in gm", compute="_compute_wt_of_dry_sample")
    wt_of_moisture = fields.Float(string="Weight of moisture in gm", compute="_compute_wt_of_moisture")
    moisture = fields.Float(string="% Moisture", compute="_compute_moisture")
    dry_density = fields.Float(string="Dry density in gm/cc", compute="_compute_dry_density")

    @api.depends('wt_of_modul_compact', 'parent_id.wt_of_modul')
    def _compute_wt_of_compact(self):
        for line in self:
            line.wt_of_compact = line.wt_of_modul_compact - line.parent_id.wt_of_modul



    @api.depends('wt_of_compact', 'parent_id.vl_of_modul')
    def _compute_bulk_density(self):
        for line in self:
            if line.parent_id.vl_of_modul != 0:
                line.bulk_density = line.wt_of_compact / line.parent_id.vl_of_modul
            else:
                line.bulk_density = 0.0


    @api.depends('wt_of_container_dry', 'wt_of_container')
    def _compute_wt_of_dry_sample(self):
        for line in self:
            line.wt_of_dry_sample = line.wt_of_container_dry - line.wt_of_container


    @api.depends('wt_of_container_wet', 'wt_of_container_dry')
    def _compute_wt_of_moisture(self):
        for line in self:
            line.wt_of_moisture = line.wt_of_container_wet - line.wt_of_container_dry


    @api.depends('wt_of_moisture', 'wt_of_dry_sample')
    def _compute_moisture(self):
        for line in self:
            if line.wt_of_dry_sample != 0:
                line.moisture = line.wt_of_moisture / line.wt_of_dry_sample * 100
            else:
                line.moisture = 0.0


    @api.depends('bulk_density', 'moisture')
    def _compute_dry_density(self):
        for line in self:
            line.dry_density = (100 * line.bulk_density) / (100 + line.moisture)



class LIGHTOMCCOMPACTIONLINE(models.Model):
    _name = "mechanical.light.omc.compaction.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")


    determination_no = fields.Float(string="Determination No")
    wt_of_modul_compact = fields.Integer(string="Weight of Mould + Compacted sample in gm")
    wt_of_compact = fields.Integer(string="Weight of compacted sample in gm", compute="_compute_wt_of_compact")
    bulk_density = fields.Float(string="Bulk Density of sample in gm/cc", compute="_compute_bulk_density")
    container_no = fields.Integer(string="Container No")
    wt_of_container = fields.Float(string="Weight of Container in gm")
    wt_of_container_wet = fields.Float(string="Weight of Container + wet sample in gm")
    wt_of_container_dry = fields.Float(string="Weight of Container + dry sample in gm")
    wt_of_dry_sample = fields.Float(string="Weight of dry sample in gm", compute="_compute_wt_of_dry_sample")
    wt_of_moisture = fields.Float(string="Weight of moisture in gm", compute="_compute_wt_of_moisture")
    moisture = fields.Float(string="% Moisture", compute="_compute_moisture")
    dry_density = fields.Float(string="Dry density in gm/cc", compute="_compute_dry_density")


    @api.depends('wt_of_modul_compact', 'parent_id.wt_of_modul_light_omc')
    def _compute_wt_of_compact(self):
        for line in self:
            line.wt_of_compact = line.wt_of_modul_compact - line.parent_id.wt_of_modul_light_omc



    @api.depends('wt_of_compact', 'parent_id.vl_of_modul_light_omc')
    def _compute_bulk_density(self):
        for line in self:
            if line.parent_id.vl_of_modul_light_omc != 0:
                line.bulk_density = line.wt_of_compact / line.parent_id.vl_of_modul_light_omc
            else:
                line.bulk_density = 0.0


    @api.depends('wt_of_container_dry', 'wt_of_container')
    def _compute_wt_of_dry_sample(self):
        for line in self:
            line.wt_of_dry_sample = line.wt_of_container_dry - line.wt_of_container


    @api.depends('wt_of_container_wet', 'wt_of_container_dry')
    def _compute_wt_of_moisture(self):
        for line in self:
            line.wt_of_moisture = line.wt_of_container_wet - line.wt_of_container_dry


    @api.depends('wt_of_moisture', 'wt_of_dry_sample')
    def _compute_moisture(self):
        for line in self:
            if line.wt_of_dry_sample != 0:
                line.moisture = line.wt_of_moisture / line.wt_of_dry_sample * 100
            else:
                line.moisture = 0.0


    @api.depends('bulk_density', 'moisture')
    def _compute_dry_density(self):
        for line in self:
            line.dry_density = (100 * line.bulk_density) / (100 + line.moisture)

    
class LIQUIDLIMITLINE(models.Model):
    _name = "mechanical.liquid.limits.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")



    container_no = fields.Integer(string="Container No")   
    blwo_no = fields.Integer(string="No.of Blows")
    mass_of_wet = fields.Float(string="Mass of wet sample+container (M1) in gms")
    mass_of_dry = fields.Float(string="Mass of dry sample+container (M2) in gms")
    mass_of_container = fields.Float(string="Mass of container (M3) in gms")
    mass_of_moisture = fields.Float(string="Mass of Moisture (M1-M2) in gms", compute="_compute_mass_of_moisture")
    mass_of_dry_sample = fields.Float(string="Mass of dry sample (M2-M3) in gms", compute="_compute_mass_of_dry_sample")
    moisture = fields.Float(string="% Moisture", compute="_compute_moisture")

   


    @api.depends('mass_of_wet', 'mass_of_dry')
    def _compute_mass_of_moisture(self):
        for line in self:
            line.mass_of_moisture = line.mass_of_wet - line.mass_of_dry


    @api.depends('mass_of_dry', 'mass_of_container')
    def _compute_mass_of_dry_sample(self):
        for line in self:
            line.mass_of_dry_sample = line.mass_of_dry - line.mass_of_container


    @api.depends('mass_of_moisture', 'mass_of_dry_sample')
    def _compute_moisture(self):
        for line in self:
            if line.mass_of_dry_sample != 0:
                line.moisture = line.mass_of_moisture / line.mass_of_dry_sample * 100
            else:
                line.moisture = 0.0


class PLASTICLIMITLINE(models.Model):
    _name = "mechanical.plasticl.limit.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")



    container_no = fields.Integer(string="Container No")   
    mass_of_wet = fields.Float(string="Mass of wet sample+container (M1) in gms")
    mass_of_dry = fields.Float(string="Mass of dry sample+container (M2) in gms")
    mass_of_container = fields.Float(string="Mass of container (M3) in gms")
    mass_of_moisture = fields.Float(string="Mass of Moisture (M1-M2) in gms", compute="_compute_mass_of_moisture")
    mass_of_dry_sample = fields.Float(string="Mass of dry sample (M2-M3) in gms", compute="_compute_mass_of_dry_sample")
    moisture = fields.Float(string="% Moisture", compute="_compute_moisture")



    @api.depends('mass_of_wet', 'mass_of_dry')
    def _compute_mass_of_moisture(self):
        for line in self:
            line.mass_of_moisture = line.mass_of_wet - line.mass_of_dry


    @api.depends('mass_of_dry', 'mass_of_container')
    def _compute_mass_of_dry_sample(self):
        for line in self:
            line.mass_of_dry_sample = line.mass_of_dry - line.mass_of_container


    @api.depends('mass_of_moisture', 'mass_of_dry_sample')
    def _compute_moisture(self):
        for line in self:
            if line.mass_of_dry_sample != 0:
                line.moisture = line.mass_of_moisture / line.mass_of_dry_sample * 100
            else:
                line.moisture = 0.0


class MoistureContentLine(models.Model):
    _name = "mechanical.moisture.content.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")
   
    sr_no = fields.Integer(string="SR NO.", readonly=True, copy=False, default=1)
    wt_of_sample = fields.Float(string="Weight of sample W1 in gm")
    oven_dry_wt = fields.Float(string="Oven dry Weight of sample W in gm")
    moisture_content = fields.Float(string="% Moisture Content",compute="_compute_moisture_content")


    @api.depends('wt_of_sample', 'oven_dry_wt')
    def _compute_moisture_content(self):
        for record in self:
            if record.oven_dry_wt != 0:
                record.moisture_content = ((record.wt_of_sample - record.oven_dry_wt) / record.oven_dry_wt) * 100
            else:
                record.moisture_content = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MoistureContentLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class DryDencityLine(models.Model):
    _name = "mechanical.dry.dencity.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")
   
    determination_no = fields.Integer(string="Determination No",readonly=True, copy=False, default=1)
    wt_of_sample = fields.Integer(string="Weight of sample gm")
    water_of_sample = fields.Integer(string="Water content of sample RMM")
    wt_of_before_cylinder = fields.Integer(string="Weight of sand + Cylinder before pouring gm")
    wt_of_after_cylinder = fields.Integer(string="Weight of sand + Cylinder after pouring gm")
    wt_of_sand_cone = fields.Integer(string="Weight of sand in cone gm")
    wt_of_sand_hole = fields.Integer(string="Weight of sand in hole gm", compute="_compute_sand_hole")
    density_of_sand = fields.Float(string="Density of sand gm/cc")
    volume_of_hole = fields.Float(string="Volume of hole cc",compute="_compute_volume_of_hole")
    bulk_density_of_sample = fields.Float(string="Bulk Density of sample gm/cc",compute="_compute_bulk_density")
    dry_density_of_sample = fields.Float(string="Dry Density of sample",compute="_compute_dry_density")
    degree_of_compaction = fields.Float(string="Degree of Compaction %",compute="_compute_degree_of_compaction")

    


    @api.depends('wt_of_before_cylinder','wt_of_after_cylinder','wt_of_sand_cone')
    def _compute_sand_hole(self):
        for record in self:
            record.wt_of_sand_hole = record.wt_of_before_cylinder - record.wt_of_after_cylinder - record.wt_of_sand_cone


    @api.depends('wt_of_sand_hole', 'density_of_sand')
    def _compute_volume_of_hole(self):
        for record in self:
            if record.density_of_sand != 0:
                record.volume_of_hole = record.wt_of_sand_hole / record.density_of_sand
            else:
                record.volume_of_hole = 0.0

 


    @api.depends('wt_of_sample', 'volume_of_hole')
    def _compute_bulk_density(self):
        for record in self:
            if record.volume_of_hole != 0:  # Avoid division by zero
                record.bulk_density_of_sample = record.wt_of_sample / record.volume_of_hole
            else:
                record.bulk_density_of_sample = 0.0

    @api.depends('bulk_density_of_sample', 'water_of_sample')
    def _compute_dry_density(self):
        for record in self:
            if record.water_of_sample + 100 != 0:  # Avoid division by zero
                record.dry_density_of_sample = (100 * record.bulk_density_of_sample) / (record.water_of_sample + 100)
            else:
                record.dry_density_of_sample = 0.0

    @api.depends('dry_density_of_sample', 'parent_id.mmd_drydencity')
    def _compute_degree_of_compaction(self):
        for record in self:
            if record.parent_id.mmd_drydencity != 0:  # Access mmd_drydencity from parent_id
                record.degree_of_compaction = (record.dry_density_of_sample / record.parent_id.mmd_drydencity) * 100
            else:
                record.degree_of_compaction = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('determination_no'))
                vals['determination_no'] = max_serial_no + 1

        return super(DryDencityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.determination_no = index + 1

#added
class FieldDencityLine(models.Model):
    _name = "mechanical.field.dencity.line1"
    parent_id = fields.Many2one('mechanical.soil1',string="Parent Id")
   
    determination_no = fields.Integer(string="Determination No",readonly=True, copy=False, default=1)
    wt_of_sample = fields.Integer(string="Weight of sample gm")
    water_of_sample = fields.Integer(string="Water content of sample RMM")
    wt_of_before_cylinder = fields.Integer(string="Weight of sand + Cylinder before pouring gm")
    wt_of_after_cylinder = fields.Integer(string="Weight of sand + Cylinder after pouring gm")
    wt_of_sand_cone = fields.Integer(string="Weight of sand in cone gm")
    wt_of_sand_hole = fields.Integer(string="Weight of sand in hole gm", compute="_compute_sand_hole")
    density_of_sand = fields.Float(string="Density of sand gm/cc")
    volume_of_hole = fields.Float(string="Volume of hole cc",compute="_compute_volume_of_hole")
    bulk_density_of_sample = fields.Float(string="Bulk Density of sample gm/cc",compute="_compute_bulk_density")
    dry_density_of_sample = fields.Float(string="Dry Density of sample",compute="_compute_dry_density")
    degree_of_compaction = fields.Float(string="Degree of Compaction %",compute="_compute_degree_of_compaction")

    


    @api.depends('wt_of_before_cylinder','wt_of_after_cylinder','wt_of_sand_cone')
    def _compute_sand_hole(self):
        for record in self:
            record.wt_of_sand_hole = record.wt_of_before_cylinder - record.wt_of_after_cylinder - record.wt_of_sand_cone


    @api.depends('wt_of_sand_hole', 'density_of_sand')
    def _compute_volume_of_hole(self):
        for record in self:
            if record.density_of_sand != 0:
                record.volume_of_hole = record.wt_of_sand_hole / record.density_of_sand
            else:
                record.volume_of_hole = 0.0

 


    @api.depends('wt_of_sample', 'volume_of_hole')
    def _compute_bulk_density(self):
        for record in self:
            if record.volume_of_hole != 0:  # Avoid division by zero
                record.bulk_density_of_sample = record.wt_of_sample / record.volume_of_hole
            else:
                record.bulk_density_of_sample = 0.0

    @api.depends('bulk_density_of_sample', 'water_of_sample')
    def _compute_dry_density(self):
        for record in self:
            if record.water_of_sample + 100 != 0:  # Avoid division by zero
                record.dry_density_of_sample = (100 * record.bulk_density_of_sample) / (record.water_of_sample + 100)
            else:
                record.dry_density_of_sample = 0.0

    @api.depends('dry_density_of_sample', 'parent_id.mmd_fielddencity')
    def _compute_degree_of_compaction(self):
        for record in self:
            if record.parent_id.mmd_fielddencity != 0:  # Access mmd_fielddencity from parent_id
                record.degree_of_compaction = (record.dry_density_of_sample / record.parent_id.mmd_fielddencity) * 100
            else:
                record.degree_of_compaction = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('determination_no'))
                vals['determination_no'] = max_serial_no + 1

        return super(FieldDencityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.determination_no = index + 1


  