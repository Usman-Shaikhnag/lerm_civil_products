from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math



class Microsilica(models.Model):
    _name = "mechanical.microsilica1"
    _inherit = "lerm.eln"
    _description = 'mechanical.microsilica1'
    _rec_name = "name"


    name = fields.Char("Name",default="Microsilica")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")

   
    # 1 Accelerated pozzolanic activity index with portland cement , 7 Days in %

    # Compressive Strength of Test Mixture

    tests = fields.Many2many("mechanical.cement.test",string="Tests")

    # Compressive Strength 

    compressive_name = fields.Char("Name",default="Accelerated pozzolanic activity index with portland cement")
    compressive_visible = fields.Boolean("Compressive Visible",compute="_compute_visible")

    temp_percent_compressive = fields.Float("Temperature °c")
    humidity_percent_compressive = fields.Float("Humidity %")
    start_date_compressive = fields.Date("Start Date")
    end_date_compressive = fields.Date("End Date")
    
    high_range_compressive = fields.Integer(string="High Range water reducer (g)")
    wt_of_microsilica = fields.Integer(string="Weight of Microsilica (g)",default=50)
    wt_of_cement_compressive = fields.Integer(string="Weight of Cement (g",default=450)
    wt_of_standerd_comp1 = fields.Float(string="Weight of Standard Sand (g)Grade-I",default=458.33)
    wt_of_standerd_comp2 = fields.Float(string="Weight of Standard Sand (g)Grade-II",default=458.33)
    wt_of_standerd_comp3 = fields.Float(string="Weight of Standard Sand (g)Grade-III",default=458.33)
    quantity_water = fields.Integer(string="Quantity of Water (g)")
    
    measured_value1 = fields.Float(string="Measured Values")
    measured_value2 = fields.Float(string="Measured Values")
    measured_value3 = fields.Float(string="Measured Values")
    measured_value4 = fields.Float(string="Measured Values")

    average_measured = fields.Float(string="Average",compute="_compute_average")
    percent_flow = fields.Float(string="% Flow",compute="_compute_flow")

    @api.depends('measured_value1', 'measured_value2', 'measured_value3', 'measured_value4')
    def _compute_average(self):
        for record in self:
            measured_values = [
                record.measured_value1,
                record.measured_value2,
                record.measured_value3,
                record.measured_value4
            ]
            non_empty_values = [value for value in measured_values if value is not False]
            if non_empty_values:
                record.average_measured = sum(non_empty_values) / len(non_empty_values)
            else:
                record.average_measured = 0.0


    @api.depends('average_measured')
    def _compute_flow(self):
        for record in self:
            record.percent_flow = record.average_measured - 100
            
            
     # 7 Days Casting

    casting_7_name = fields.Char("Name",default="7 Days")
    # casting_7_visible = fields.Boolean("7 days Visible",compute="_compute_visible")

    casting_date_7days = fields.Date(string="Date of Casting")
    testing_date_7days = fields.Date(string="Date of Testing",compute="_compute_testing_date_7days")
    casting_7_days_tables = fields.One2many('microsilica.casting.7days.line1','parent_id',string="7 Days")
    average_casting_7days = fields.Float("Average",compute="_compute_average_7days")
    compressive_strength_7_days = fields.Float("Compressive Strength",compute="_compute_compressive_strength_7days")
    status_7days = fields.Boolean("Done")


    @api.depends('casting_7_days_tables.compressive_strength')
    def _compute_average_7days(self):
        for record in self:
            try:
                record.average_casting_7days = round((sum(record.casting_7_days_tables.mapped('compressive_strength'))/len(record.casting_7_days_tables)),2)
            except:
                record.average_casting_7days = 0

    @api.depends('casting_date_7days')
    def _compute_testing_date_7days(self):
        for record in self:
            if record.casting_date_7days:
                cast_date = fields.Datetime.from_string(record.casting_date_7days)
                testing_date = cast_date + timedelta(days=7)
                record.testing_date_7days = fields.Datetime.to_string(testing_date)
            else:
                record.testing_date_7days = False


    @api.depends('average_casting_7days')
    def _compute_compressive_strength_7days(self):
        for record in self:
            integer_part = math.floor(record.average_casting_7days)
            fractional_part = record.average_casting_7days - integer_part
            if fractional_part > 0 and fractional_part <= 0.25:
                record.compressive_strength_7_days = integer_part
            elif fractional_part > 0.25 and fractional_part <= 0.75:
                record.compressive_strength_7_days = integer_part + 0.5
            elif fractional_part > 0.75 and fractional_part <= 1:
                record.compressive_strength_7_days = integer_part + 1
            else:
                record.compressive_strength_7_days = 0
                
    # Compressive Strength of control Sample
    
    high_range_control_comp = fields.Integer(string="High Range water reducer (g)")
    wt_of_cement = fields.Integer(string="Weight of Cement (g)",default=500)
    wt_of_sand1 = fields.Float(string="Weight of Standard Sand (g)Grade-I",default=458.33)
    wt_of_sand2 = fields.Float(string="Weight of Standard Sand (g)Grade-II",default=458.33)
    wt_of_sand3 = fields.Float(string="Weight of Standard Sand (g)Grade-III",default=458.33)
    quanity_of_water = fields.Integer(string="Quantity of Water (g)")
    
    sample_measured_value1 = fields.Float(string="Measured Values")
    sample_measured_value2 = fields.Float(string="Measured Values")
    sample_measured_value3 = fields.Float(string="Measured Values")
    sample_measured_value4 = fields.Float(string="Measured Values")

    sample_average_measured = fields.Float(string="Average",compute="sample_compute_average")
    sample_percent_flow = fields.Float(string="% Flow",compute="sample_compute_flow")
    
    
    @api.depends('sample_measured_value1', 'sample_measured_value2', 'sample_measured_value3', 'sample_measured_value4')
    def sample_compute_average(self):
        for record in self:
            measured_values = [
                record.sample_measured_value1,
                record.sample_measured_value2,
                record.sample_measured_value3,
                record.sample_measured_value4
            ]
            non_empty_values = [value for value in measured_values if value is not False]
            if non_empty_values:
                record.sample_average_measured = sum(non_empty_values) / len(non_empty_values)
            else:
                record.sample_average_measured = 0.0


    @api.depends('sample_average_measured')
    def sample_compute_flow(self):
        for record in self:
            record.sample_percent_flow = record.sample_average_measured - 100
            
    # 7 Days

    control_casting_7_name = fields.Char("Name",default="7 Days")
    # casting_7_visible = fields.Boolean("7 days Visible",compute="_compute_visible")

    control_casting_date_7days = fields.Date(string="Date of Casting")
    control_testing_date_7days = fields.Date(string="Date of Testing",compute="compute_controltesting_date_7days")
    control_casting_7_days_tables = fields.One2many('microsilica.control.casting.7days.line1','parent_id',string="7 Days")
    control_average_casting_7days = fields.Float("Average",compute="_compute_control_average_casting_7days")
    control_compressive_strength_7_days = fields.Float("Accelerated pozzolanic activity index with portland cement , 7 Days in %",compute="_compute_control_compressive_strength_7_days")
    control_status_7days = fields.Boolean("Done")


    @api.depends('control_casting_7_days_tables.control_compressive_strength')
    def _compute_control_average_casting_7days(self):
        for record in self:
            try:
                record.control_average_casting_7days = round((sum(record.control_casting_7_days_tables.mapped('control_compressive_strength'))/len(record.control_casting_7_days_tables)),2)
            except:
                record.control_average_casting_7days = 0

    @api.depends('control_casting_date_7days')
    def compute_controltesting_date_7days(self):
        for record in self:
            if record.control_casting_date_7days:
                cast_date = fields.Datetime.from_string(record.control_casting_date_7days)
                testing_date = cast_date + timedelta(days=7)
                record.control_testing_date_7days = fields.Datetime.to_string(testing_date)
            else:
                record.control_testing_date_7days = False
    
    @api.depends('average_casting_7days','control_average_casting_7days')
    def _compute_control_compressive_strength_7_days(self):
        for record in self:
            try:
                record.control_compressive_strength_7_days = round(((record.average_casting_7days/record.control_average_casting_7days)*100),2)
            except:
                record.control_compressive_strength_7_days = 0


    accelerated_pozzolanic_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        
    ], string='Confirmity', default='fail',compute="_compute_accelerated_pozzolanic_conformity")

    accelerated_pozzolanic_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_accelerated_pozzolanic_nabl",store=True)



    @api.depends('control_compressive_strength_7_days','eln_ref')
    def _compute_accelerated_pozzolanic_conformity(self):
        for record in self:
            record.accelerated_pozzolanic_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ddd2525aw-19f0-48b6-8e09-e7076a4b04b5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ddd2525aw-19f0-48b6-8e09-e7076a4b04b5')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.control_compressive_strength_7_days - record.control_compressive_strength_7_days*mu_value
                    upper = record.control_compressive_strength_7_days + record.control_compressive_strength_7_days*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.accelerated_pozzolanic_conformity = 'pass'
                        break
                    else:
                        record.accelerated_pozzolanic_conformity = 'fail'
           

    @api.depends('control_compressive_strength_7_days','eln_ref')
    def _compute_accelerated_pozzolanic_nabl(self):
        
        for record in self:
            record.accelerated_pozzolanic_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ddd2525aw-19f0-48b6-8e09-e7076a4b04b5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ddd2525aw-19f0-48b6-8e09-e7076a4b04b5')]).parameter_table
            # for material in materials:
                
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.control_compressive_strength_7_days - record.control_compressive_strength_7_days*mu_value
            upper = record.control_compressive_strength_7_days + record.control_compressive_strength_7_days*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.accelerated_pozzolanic_nabl = 'pass'
                break
            else:
                record.accelerated_pozzolanic_nabl = 'fail'



     #start 2--Oversize % Retained on 45 Micron IS sieve
 

    oversize_name = fields.Char("Name",default="Oversize % Retained on 45 Micron IS sieve")
    oversize_retain_visible = fields.Boolean("Oversize Visible",compute="_compute_visible")

    # temp_percent_oversize = fields.Float("Temperature °c")
    # humidity_percent_oversize = fields.Float("Humidity %")
    # start_date_oversize = fields.Date("Start Date")
    # end_date_oversize = fields.Date("End Date")
    
    
    oversize_retained_tables = fields.One2many('oversize.retail.line1','parent_id',string="Oversize % Retained on 45 Micron IS sieve")
    # avrg_retain_wt = fields.Float(string="Average",compute="_compute_avrg_retain_wt")
    retain_wt_avrg = fields.Float(string="Average",compute="_compute_retain_wt_avrg")
    retain_wt_rounded = fields.Float(string="% Weight Retained",compute="_compute_retain_wt_rounded",digits=(16, 1))

    oversize_retained_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_oversize_retained_conformity")

    oversize_retained_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_oversize_retained_nabl",store=True)



    @api.depends('retain_wt_rounded','eln_ref')
    def _compute_oversize_retained_conformity(self):
        for record in self:
            record.oversize_retained_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','52147fgtre-5f8c-44a2-984b-6ad2a17d250c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','52147fgtre-5f8c-44a2-984b-6ad2a17d250c')]).parameter_table
            for material in materials:
                
                req_min = material.req_min
                req_max = material.req_max
                mu_value = line.mu_value
                
                lower = record.retain_wt_rounded - record.retain_wt_rounded*mu_value
                upper = record.retain_wt_rounded + record.retain_wt_rounded*mu_value
                if lower >= req_min and upper <= req_max:
                    record.oversize_retained_conformity = 'pass'
                    break
                else:
                    record.oversize_retained_conformity = 'fail'

    @api.depends('retain_wt_rounded','eln_ref')
    def _compute_oversize_retained_nabl(self):
        
        for record in self:
            record.oversize_retained_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','52147fgtre-5f8c-44a2-984b-6ad2a17d250c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','52147fgtre-5f8c-44a2-984b-6ad2a17d250c')]).parameter_table
            # for material in materials:
                
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.retain_wt_rounded - record.retain_wt_rounded*mu_value
            upper = record.retain_wt_rounded + record.retain_wt_rounded*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.oversize_retained_nabl = 'pass'
                break
            else:
                record.oversize_retained_nabl = 'fail'


    
    @api.depends('oversize_retained_tables.retained_percent_wt')
    def _compute_retain_wt_avrg(self):
        for record in self:
            retained_percent_wt = record.oversize_retained_tables.mapped('retained_percent_wt')
            if retained_percent_wt:
                record.retain_wt_avrg = sum(retained_percent_wt) / len(retained_percent_wt)
            else:
                record.retain_wt_avrg = 0.0
                
    @api.depends('retain_wt_avrg')
    def _compute_retain_wt_rounded(self):
        
        for record in self:
            if 0.40 <= record.retain_wt_avrg < 0.50:
                record.retain_wt_rounded = 0.4
            elif 0.50 <= record.retain_wt_avrg < 0.60:
                record.retain_wt_rounded = 0.6
            else:
                record.retain_wt_rounded = round(record.retain_wt_avrg, 1)
                    
    #Start 3 Specific Gravity
    
    specific_gravity_name = fields.Char("Name",default="Specific Gravity")
    specific_gravity_visible = fields.Boolean("Specific Visible",compute="_compute_visible")

    # temp_percent_specific = fields.Float("Temperature °c")
    # humidity_percent_specific = fields.Float("Humidity %")
    # start_date_specific = fields.Date("Start Date")
    # end_date_specific = fields.Date("End Date")
    
    
    specific_gravity_tables = fields.One2many('specific.gravity.line1','parent_id',string="Specific Gravity")
    specific_gravity_avrg = fields.Float(string="Average",compute="_compute_specific_gravity_avrg")

    specific_gravity_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_specific_gravity_conformity")

    specific_gravity_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_specific_gravity_nabl",store=True)



    @api.depends('specific_gravity_avrg','eln_ref')
    def _compute_specific_gravity_conformity(self):
        for record in self:
            record.specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658fgtrcd-80ef-4de0-96ba-a279f27b9ede')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658fgtrcd-80ef-4de0-96ba-a279f27b9ede')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.specific_gravity_avrg - record.specific_gravity_avrg*mu_value
                    upper = record.specific_gravity_avrg + record.specific_gravity_avrg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.specific_gravity_conformity = 'fail'

    @api.depends('specific_gravity_avrg','eln_ref')
    def _compute_specific_gravity_nabl(self):
        
        for record in self:
            record.specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658fgtrcd-80ef-4de0-96ba-a279f27b9ede')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658fgtrcd-80ef-4de0-96ba-a279f27b9ede')]).parameter_table
            # for material in materials:
                
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.specific_gravity_avrg - record.specific_gravity_avrg*mu_value
            upper = record.specific_gravity_avrg + record.specific_gravity_avrg*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.specific_gravity_nabl = 'pass'
                break
            else:
                record.specific_gravity_nabl = 'fail'

 

    
   
    @api.depends('specific_gravity_tables.spe_gravt_microsilica')
    def _compute_specific_gravity_avrg(self):
        for record in self:
            spe_gravt_microsilica = record.specific_gravity_tables.mapped('spe_gravt_microsilica')
            if spe_gravt_microsilica:
                record.specific_gravity_avrg = sum(spe_gravt_microsilica) / len(spe_gravt_microsilica)
            else:
                record.specific_gravity_avrg = 0.0

    
    
    #Start 4--Compressive Strength
    
    compressive_strength_name = fields.Char("Name",default="Compressive Strength")
    compressive_strength_visible = fields.Boolean("Compressive Visible",compute="_compute_visible")

    # temp_percent_cmp_strngth = fields.Float("Temperature °c")
    # humidity_percent_cmp_strngth = fields.Float("Humidity %")
    # start_date_cmp_strngth = fields.Date("Start Date")
    # end_date_cmp_strngth = fields.Date("End Date")
    
    n_is = fields.Integer(string="N (as per IS 15388)",default=1)
    microsilica_wt = fields.Integer(string="Weight of Microsilica (100*N)",default=100)
    cement_wt = fields.Integer(string="Weight of Cement (g)",default=400)
    wt_of_standerd_sand1 = fields.Integer(string="Weight of Standard Sand (g)Grade-I",default=500)
    wt_of_standerd_sand2 = fields.Integer(string="Weight of Standard Sand (g)Grade-II",default=500)
    wt_of_standerd_sand3 = fields.Integer(string="Weight of Standard Sand (g)Grade-III",default=500)
    water_quantity = fields.Integer(string="Quantity of Water (g)")
    
    comp_measured_value1 = fields.Float(string="Measured Values")
    comp_measured_value2 = fields.Float(string="Measured Values")
    comp_measured_value3 = fields.Float(string="Measured Values")
    comp_measured_value4 = fields.Float(string="Measured Values")

    comp_average_measured = fields.Float(string="Average",compute="_compute_comp_average")
    comp_percent_flow = fields.Float(string="% Flow",compute="_compute_comp_flow")

    @api.depends('comp_measured_value1', 'comp_measured_value2', 'comp_measured_value3', 'comp_measured_value4')
    def _compute_comp_average(self):
        for record in self:
            measured_values = [
                record.comp_measured_value1,
                record.comp_measured_value2,
                record.comp_measured_value3,
                record.comp_measured_value4
            ]
            non_empty_values = [value for value in measured_values if value is not False]
            if non_empty_values:
                record.comp_average_measured = sum(non_empty_values) / len(non_empty_values)
            else:
                record.comp_average_measured = 0.0


    @api.depends('comp_average_measured')
    def _compute_comp_flow(self):
        for record in self:
            record.comp_percent_flow = record.comp_average_measured - 100
            
    
    # 7 Days Casting

    comp_casting_7_name = fields.Char("Name",default="7 Days")
    # casting_7_visible = fields.Boolean("7 days Visible",compute="_compute_visible")

    comp_casting_date_7days = fields.Date(string="Date of Casting")
    comp_testing_date_7days = fields.Date(string="Date of Testing",compute="_compute_comp_testing_date_7days")
    comp_casting_7_days_tables = fields.One2many('microsilica.compressive.casting.7days.line1','parent_id',string="7 Days")
    comp_average_casting_7days = fields.Float("Average",compute="_compute_comp_average_casting_7days")
    comp_strngth_7_days = fields.Float("Compressive Strength",compute="_compute_compute_comp_strngth_7_days")
    comp_status_7days = fields.Boolean("Done")


    @api.depends('comp_casting_7_days_tables.comp_strength')
    def _compute_comp_average_casting_7days(self):
        for record in self:
            try:
                record.comp_average_casting_7days = round((sum(record.comp_casting_7_days_tables.mapped('comp_strength'))/len(record.comp_casting_7_days_tables)),2)
            except:
                record.comp_average_casting_7days = 0

    @api.depends('comp_casting_date_7days')
    def _compute_comp_testing_date_7days(self):
        for record in self:
            if record.comp_casting_date_7days:
                cast_date = fields.Datetime.from_string(record.comp_casting_date_7days)
                testing_date = cast_date + timedelta(days=7)
                record.comp_testing_date_7days = fields.Datetime.to_string(testing_date)
            else:
                record.comp_testing_date_7days = False


    @api.depends('comp_average_casting_7days')
    def _compute_compute_comp_strngth_7_days(self):
        for record in self:
            integer_part = math.floor(record.comp_average_casting_7days)
            fractional_part = record.comp_average_casting_7days - integer_part
            if fractional_part > 0 and fractional_part <= 0.25:
                record.comp_strngth_7_days = integer_part
            elif fractional_part > 0.25 and fractional_part <= 0.75:
                record.comp_strngth_7_days = integer_part + 0.5
            elif fractional_part > 0.75 and fractional_part <= 1:
                record.comp_strngth_7_days = integer_part + 1
            else:
                record.comp_strngth_7_days = 0
                
    # comp strength of control sample
    
    
    comp_control_cement_wt = fields.Integer(string="Weight of Cement (g)",default=500)
    comp_control_wt_of_standerd_sand1 = fields.Integer(string="Weight of Standard Sand (g)Grade-I",default=500)
    comp_control_wt_standerd_sand2 = fields.Integer(string="Weight of Standard Sand (g)Grade-II",default=500)
    comp_control_wt_standerd_sand3 = fields.Integer(string="Weight of Standard Sand (g)Grade-III",default=500)
    comp_control_total_wt = fields.Integer(string="Total Weight (g)",default=2000)
    comp_control_water_quantity = fields.Integer(string="Quantity of Water (g)")
    
    
    comp_control_measured_value1 = fields.Float(string="Measured Values")
    comp_control_measured_value2 = fields.Float(string="Measured Values")
    comp_control_measured_value3 = fields.Float(string="Measured Values")
    comp_control_measured_value4 = fields.Float(string="Measured Values")

    comp_control_average_measured = fields.Float(string="Average",compute="_compute_comp_control_average")
    comp_control_percent_flow = fields.Float(string="% Flow",compute="_compute_comp_control_flow")

    @api.depends('comp_control_measured_value1', 'comp_control_measured_value2', 'comp_control_measured_value3', 'comp_control_measured_value4')
    def _compute_comp_control_average(self):
        for record in self:
            measured_values = [
                record.comp_control_measured_value1,
                record.comp_control_measured_value2,
                record.comp_control_measured_value3,
                record.comp_control_measured_value4
            ]
            non_empty_values = [value for value in measured_values if value is not False]
            if non_empty_values:
                record.comp_control_average_measured = sum(non_empty_values) / len(non_empty_values)
            else:
                record.comp_control_average_measured = 0.0


    @api.depends('comp_control_average_measured')
    def _compute_comp_control_flow(self):
        for record in self:
            record.comp_control_percent_flow = record.comp_control_average_measured - 100
            
            
    # 7 Days Casting

    comp_control_casting_7name = fields.Char("Name",default="7 Days")
    # casting_7_visible = fields.Boolean("7 days Visible",compute="_compute_visible")

    comp_control_castingdate_7days = fields.Date(string="Date of Casting")
    # comp_control_testingdate_7days = fields.Date(string="Date of Testing",compute="_compute_comp_control_testingdate_7days")
    comp_control_testingdate_7days = fields.Date(string="Date of Testing",compute="_compute_comp_control_testingdate_7days")
    comp_control_casting_7days_tables = fields.One2many('microsilica.comp.control.casting.7days.line1','parent_id',string="7 Days")
    comp_control_average_casting_7days = fields.Float("Average",compute="_compute_comp_control_average_casting_7days")
    comp_control_strngth_7_days = fields.Float("Compressive Strength of  Sample (%)",compute="_compute_strength_7_days")
    comp_control_status_7days = fields.Boolean("Done")


    comp_strngth_7_days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_comp_strngth_7_days_conformity")

    comp_strngth_7_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_comp_strngth_7_days_nabl",store=True)



    @api.depends('comp_control_strngth_7_days','eln_ref')
    def _compute_comp_strngth_7_days_conformity(self):
        for record in self:
            record.comp_strngth_7_days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658798cvfd-889b-477c-a355-0476f6bcd0d7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658798cvfd-889b-477c-a355-0476f6bcd0d7')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.comp_control_strngth_7_days - record.comp_control_strngth_7_days*mu_value
                    upper = record.comp_control_strngth_7_days + record.comp_control_strngth_7_days*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.comp_strngth_7_days_conformity = 'pass'
                        break
                    else:
                        record.comp_strngth_7_days_conformity = 'fail'

    @api.depends('comp_control_strngth_7_days','eln_ref')
    def _compute_comp_strngth_7_days_nabl(self):
        
        for record in self:
            record.comp_strngth_7_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658798cvfd-889b-477c-a355-0476f6bcd0d7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658798cvfd-889b-477c-a355-0476f6bcd0d7')]).parameter_table
            # for material in materials:
                
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.comp_control_strngth_7_days - record.comp_control_strngth_7_days*mu_value
            upper = record.comp_control_strngth_7_days + record.comp_control_strngth_7_days*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.comp_strngth_7_days_nabl = 'pass'
                break
            else:
                record.comp_strngth_7_days_nabl = 'fail'


    @api.depends('comp_control_casting_7days_tables.comp_control_strength')
    def _compute_comp_control_average_casting_7days(self):
        for record in self:
            try:
                record.comp_control_average_casting_7days = round((sum(record.comp_control_casting_7days_tables.mapped('comp_control_strength'))/len(record.comp_control_casting_7days_tables)),2)
            except:
                record.comp_control_average_casting_7days = 0

    @api.depends('comp_control_castingdate_7days')
    def _compute_comp_control_testingdate_7days(self):
        for record in self:
            if record.comp_control_castingdate_7days:
                cast_date = fields.Datetime.from_string(record.comp_control_castingdate_7days)
                testing_date = cast_date + timedelta(days=7)
                record.comp_control_testingdate_7days = fields.Datetime.to_string(testing_date)
            else:
                record.comp_control_testingdate_7days = False


    @api.depends('comp_average_casting_7days','comp_control_average_casting_7days')
    def _compute_strength_7_days(self):
        for record in self:
            if record.comp_control_average_casting_7days != 0:
                record.comp_control_strngth_7_days = round(((record.comp_average_casting_7days / record.comp_control_average_casting_7days)*100),2)
            else:
                record.comp_control_strngth_7_days = 0
                
                
    
    #5---Start -- Oversize Percent Retained on 45 Micron IS sieve variation from Avg. %
    
    
    oversize_percent_name = fields.Char("Name",default="Oversize Percent Retained on 45 Micron IS sieve variation from Avg. %")
    oversize_percent_retain_visible = fields.Boolean("Oversize Percent Visible",compute="_compute_visible")

    # oversize_temp_percent = fields.Float("Temperature °c")
    # oversize_humidity_percent_specific = fields.Float("Humidity %")
    # oversize_start_date_specific = fields.Date("Start Date")
    # oversize_end_date_specific = fields.Date("End Date")
    
    
    oversize_percent_tables = fields.One2many('oversize.retain.percent.line1','parent_id',string="Oversize 45 Grain Micron")
    avrg_oversize_percent = fields.Float(string="Average",compute="_compute_avrg_oversize_percent",digits=(16, 3))
    # added
    variation_from_avg_percent = fields.Float(string="Variation from Avg.(%)", compute="_compute_variation_from_avg_percent", digits=(16, 2))
    # uptill



    @api.depends('oversize_percent_tables.retain_wt_percent')
    def _compute_avrg_oversize_percent(self):
        for record in self:
            retain_wt_percent = record.oversize_percent_tables.mapped('retain_wt_percent')
            if retain_wt_percent:
                record.avrg_oversize_percent = sum(retain_wt_percent) / len(retain_wt_percent)
            else:
                record.avrg_oversize_percent = 0.0

    # added

    @api.depends('oversize_percent_tables.variation_from_avrg')
    def _compute_variation_from_avg_percent(self):
        for record in self:
            variations = record.oversize_percent_tables.mapped('variation_from_avrg')
            positive_variations = [v for v in variations if v > 0]
            record.variation_from_avg_percent = max(positive_variations) if positive_variations else 0.0

    # uptill


    oversize_percent_retain_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_oversize_percent_retain_conformity")

    oversize_percent_retain_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_oversize_percent_retain_nabl",store=True)



    @api.depends('avrg_oversize_percent','eln_ref')
    def _compute_oversize_percent_retain_conformity(self):
        for record in self:
            record.oversize_percent_retain_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658874seqa-bfaf-4667-aca6-b69c321af63b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658874seqa-bfaf-4667-aca6-b69c321af63b')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avrg_oversize_percent - record.avrg_oversize_percent*mu_value
                    upper = record.avrg_oversize_percent + record.avrg_oversize_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.oversize_percent_retain_conformity = 'pass'
                        break
                    else:
                        record.oversize_percent_retain_conformity = 'fail'

    @api.depends('avrg_oversize_percent','eln_ref')
    def _compute_oversize_percent_retain_nabl(self):
        
        for record in self:
            record.oversize_percent_retain_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658874seqa-bfaf-4667-aca6-b69c321af63b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','658874seqa-bfaf-4667-aca6-b69c321af63b')]).parameter_table
            # for material in materials:
                
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avrg_oversize_percent - record.avrg_oversize_percent*mu_value
            upper = record.avrg_oversize_percent + record.avrg_oversize_percent*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.oversize_percent_retain_nabl = 'pass'
                break
            else:
                record.oversize_percent_retain_nabl = 'fail'

    
     #6---Start -- Dry Loose Bulk Density

    bulk_density_name = fields.Char("Name",default="Dry Loose Bulk Density")
    bulk_density_visible = fields.Boolean("Dry Bulk Density Visible",compute="_compute_visible")

    # bulk_density_temp_percent = fields.Float("Temperature °c")
    # bulk_density_humidity_percent = fields.Float("Humidity %")
    # bulk_density_start_date = fields.Date("Start Date")
    # bulk_density_end_date = fields.Date("End Date")
    
    
    bulk_density_tables = fields.One2many('dry.loose.bulk.density.line1','parent_id',string="Dry Loose Bulk Density")
    avrg_bulk_density = fields.Float(string="Average Dry Loose Bulk Density (kg/m³)",compute="_compute_avrg_bulk_density")

    bulk_density_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_bulk_density_conformity")

    bulk_density_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_bulk_density_nabl",store=True)



    @api.depends('avrg_bulk_density','eln_ref')
    def _compute_bulk_density_conformity(self):
        for record in self:
            record.bulk_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14785dfrte-42b6-4d86-9ac7-a2758b3f4e5a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14785dfrte-42b6-4d86-9ac7-a2758b3f4e5a')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avrg_bulk_density - record.avrg_bulk_density*mu_value
                    upper = record.avrg_bulk_density + record.avrg_bulk_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.bulk_density_conformity = 'pass'
                        break
                    else:
                        record.bulk_density_conformity = 'fail'

    @api.depends('avrg_bulk_density','eln_ref')
    def _compute_bulk_density_nabl(self):
        
        for record in self:
            record.bulk_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14785dfrte-42b6-4d86-9ac7-a2758b3f4e5a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14785dfrte-42b6-4d86-9ac7-a2758b3f4e5a')]).parameter_table
            # for material in materials:
                
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avrg_bulk_density - record.avrg_bulk_density*mu_value
            upper = record.avrg_bulk_density + record.avrg_bulk_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.bulk_density_nabl = 'pass'
                break
            else:
                record.bulk_density_nabl = 'fail'

    
    @api.depends('bulk_density_tables.dryloose_bulk_density')
    def _compute_avrg_bulk_density(self):
        for record in self:
            dryloose_bulk_density = record.bulk_density_tables.mapped('dryloose_bulk_density')
            if dryloose_bulk_density:
                record.avrg_bulk_density = sum(dryloose_bulk_density) / len(dryloose_bulk_density)
            else:
                record.avrg_bulk_density = 0.0
    

### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.compressive_visible = False
        for record in self:
            record.oversize_retain_visible = False
        for record in self:
            record.specific_gravity_visible = False
        for record in self:
            record.compressive_strength_visible = False
        for record in self:
            record.oversize_percent_retain_visible = False
        for record in self:
            record.bulk_density_visible = False
          
    #     compressive_test = self.env['mechanical.cement.test'].sudo().search([('name', '=', 'Accelerated pozzolanic activity index with portland cement')])
    #     oversize_retain_test = self.env['mechanical.cement.test'].sudo().search([('name', '=', 'Oversize % Retained on 45 Micron IS sieve')])
    #     specific_gravity_test = self.env['mechanical.cement.test'].sudo().search([('name', '=', 'Specific Gravity')])
    #     compressive_strength_test = self.env['mechanical.cement.test'].sudo().search([('name', '=', 'Compressive Strength')])
    #     oversize_percent_retain_test = self.env['mechanical.cement.test'].sudo().search([('name', '=', 'Oversize Percent Retained on 45 Micron IS sieve variation from Avg. %')])
    #     bulk_density_test = self.env['mechanical.cement.test'].sudo().search([('name', '=', 'Dry Loose Bulk Density')])


   
          
           
            # if compressive_test in record.tests:
            #     record.compressive_visible = True
            # if oversize_retain_test in record.tests:
            #     record.compressive_visible = True
            # if specific_gravity_test in record.tests:
            #     record.specific_gravity_visible = True
            # if compressive_strength_test in record.tests:
            #     record.compressive_strength_visible = True
            # if oversize_percent_retain_test in record.tests:
            #     record.oversize_percent_retain_visible = True
            # if bulk_density_test in record.tests:
            #     record.bulk_density_visible = True

        for sample in record.sample_parameters:
            print("Samples internal id",sample.internal_id)
            # accelerated 
            if sample.internal_id == 'ddd2525aw-19f0-48b6-8e09-e7076a4b04b5':
                record.compressive_visible = True
            # oversize % 
            if sample.internal_id == '52147fgtre-5f8c-44a2-984b-6ad2a17d250c':
                record.oversize_retain_visible = True
            # specific gravity
            if sample.internal_id == '658fgtrcd-80ef-4de0-96ba-a279f27b9ede':
                record.specific_gravity_visible = True
            # compressive strength
            if sample.internal_id == '658798cvfd-889b-477c-a355-0476f6bcd0d7':
                record.compressive_strength_visible = True
            # oversize percent retained
            if sample.internal_id == '658874seqa-bfaf-4667-aca6-b69c321af63b':
                record.oversize_percent_retain_visible = True
                print("oversize percent retained",record.oversize_percent_retain_visible)
            # bulk density
            if sample.internal_id == '14785dfrte-42b6-4d86-9ac7-a2758b3f4e5a':
                record.bulk_density_visible = True

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
        record = super(Microsilica, self).create(vals)
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
        record = self.env['mechanical.microsilica1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    
class CementTest(models.Model):
    _name = "mechanical.cement.test"
    _rec_name = "name"
    name = fields.Char("Name")
    
    
    
class Casting7DaysLine(models.Model):
    _name = "microsilica.casting.7days.line1"

    parent_id = fields.Many2one('mechanical.microsilica1')

    length = fields.Float("Length in mm")
    width = fields.Float("Width in mm")
    crosssectional_area = fields.Float("Crosssectional Area",compute="_compute_crosssectional_area")
    wt_of_cement_cube = fields.Float("wt of Cube in gm")
    crushing_load = fields.Float("Crushing Load in KN")
    compressive_strength = fields.Float("Compressive Strength (N/mm²)",compute="_compute_compressive_strength")

    @api.depends('length','width')
    def _compute_crosssectional_area(self):
        for record in self:
            record.crosssectional_area = record.length * record.width

    @api.depends('crosssectional_area','crushing_load')
    def _compute_compressive_strength(self):
        for record in self:
            if record.crosssectional_area != 0:
                record.compressive_strength = (record.crushing_load / record.crosssectional_area)*1000
            else:
                record.compressive_strength = 0
                
                
class ControlCasting7DaysLine(models.Model):
    _name = "microsilica.control.casting.7days.line1"

    parent_id = fields.Many2one('mechanical.microsilica1')

    control_length = fields.Float("Length in mm")
    control_width = fields.Float("Width in mm")
    control_crosssectional_area = fields.Float("Crosssectional Area",compute="_compute_control_crosssectional_area")
    control_wt_of_cement_cube = fields.Float("wt of Cube in gm")
    control_crushing_load = fields.Float("Crushing Load in KN")
    control_compressive_strength = fields.Float("Compressive Strength (N/mm²)",compute="_compute_control_compressive_strength")

    @api.depends('control_length','control_width')
    def _compute_control_crosssectional_area(self):
        for record in self:
            record.control_crosssectional_area = record.control_length * record.control_width

    @api.depends('control_crosssectional_area','control_crushing_load')
    def _compute_control_compressive_strength(self):
        for record in self:
            if record.control_crosssectional_area != 0:
                record.control_compressive_strength = (record.control_crushing_load / record.control_crosssectional_area)*1000
            else:
                record.control_compressive_strength = 0
                
class OversizeRetainLine(models.Model):
    _name = "oversize.retail.line1"
    
    parent_id = fields.Many2one('mechanical.microsilica1')
    
    sr_no = fields.Integer("S.No",readonly=True, copy=False, default=1)
    wt_sample = fields.Integer("Sample Weight (g)",default=100)
    wt_retain = fields.Float("Retained Weight on 45 Micron Sieve (g)")
    retained_percent_wt = fields.Float("% Weight Retained",compute="_compute_retained_percent_wt")

    
    @api.depends('wt_sample','wt_retain')
    def _compute_retained_percent_wt(self):
        for record in self:
            if record.wt_retain != 0:
                record.retained_percent_wt = (record.wt_retain / record.wt_sample)*100
            else:
                record.retained_percent_wt = 0
                
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(OversizeRetainLine, self).create(vals)
    
    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1
                
class SpecificGravityLine(models.Model):
    _name = "specific.gravity.line1"
    
    parent_id = fields.Many2one('mechanical.microsilica1')
    
    sr_no = fields.Integer("Trial",readonly=True, copy=False, default=1)
    mass_of_microsilica = fields.Integer("Mass of Micrsilica (g)",default=64)
    initial_vol_kerosine = fields.Float("Initial Volume of kerosine (ml)V1")
    final_vol_kero_cement = fields.Float("Final Volume of kerosine and Cement V2")
    displaced_volume = fields.Float("Displaced volume (cm³)",compute="compute_displaced_volume")
    # specific_gravity = fields.Float("Specific Gravity",compute="_compute_spc_gravity")
    spe_gravt_microsilica= fields.Float("Specific Gravity",compute="_compute_spe_gravt_microsilica")


    
    
    @api.depends('final_vol_kero_cement','displaced_volume')
    def compute_displaced_volume(self):
        for record in self:
            try:
                record.displaced_volume = record.final_vol_kero_cement-record.initial_vol_kerosine
            except ZeroDivisionError:
                record.displaced_volume = 0
                
    @api.depends('mass_of_microsilica','displaced_volume')
    def _compute_spe_gravt_microsilica(self):
        for record in self:
            if record.displaced_volume != 0:
                record.spe_gravt_microsilica = record.mass_of_microsilica/record.displaced_volume
            else:
                record.spe_gravt_microsilica = 0.0
                
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(SpecificGravityLine, self).create(vals)
    
    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1
                
    
                
class CompressiveCasting7DaysLine(models.Model):
    _name = "microsilica.compressive.casting.7days.line1"

    parent_id = fields.Many2one('mechanical.microsilica1')

    compressive_length = fields.Float("Length in mm")
    compressive_width = fields.Float("Width in mm")
    compressive_crosssectional_area = fields.Float("Crosssectional Area",compute="_compute_compressive_crosssectional_area")
    compressive_wt_of_cement_cube = fields.Float("wt of Cube in gm")
    compressive_crushing_load = fields.Float("Crushing Load in KN")
    comp_strength = fields.Float("Compressive Strength (N/mm²)",compute="_compute_compr_strngth")

    @api.depends('compressive_length','compressive_width')
    def _compute_compressive_crosssectional_area(self):
        for record in self:
            record.compressive_crosssectional_area = record.compressive_length * record.compressive_width

    @api.depends('compressive_crosssectional_area','compressive_crushing_load')
    def _compute_compr_strngth(self):
        for record in self:
            if record.compressive_crosssectional_area != 0:
                record.comp_strength = (record.compressive_crushing_load / record.compressive_crosssectional_area)*1000
            else:
                record.comp_strength = 0
                
class CompControlCasting7DaysLine(models.Model):
    _name = "microsilica.comp.control.casting.7days.line1"

    parent_id = fields.Many2one('mechanical.microsilica1')

    comp_control_length = fields.Float("Length in mm")
    comp_control_width = fields.Float("Width in mm")
    comp_control_crosssectional_area = fields.Float("Crosssectional Area",compute="_compute_comp_control_crosssectional_area")
    comp_control_wt_cement_cube = fields.Float("wt of Cube in gm")
    comp_control_crushing_load = fields.Float("Crushing Load in KN")
    comp_control_strength = fields.Float("Compressive Strength (N/mm²)",compute="_compute_compr_strngth")

    @api.depends('comp_control_length','comp_control_width')
    def _compute_comp_control_crosssectional_area(self):
        for record in self:
            record.comp_control_crosssectional_area = record.comp_control_length * record.comp_control_width

    @api.depends('comp_control_crosssectional_area','comp_control_crushing_load')
    def _compute_compr_strngth(self):
        for record in self:
            if record.comp_control_crosssectional_area != 0:
                record.comp_control_strength = (record.comp_control_crushing_load / record.comp_control_crosssectional_area)*1000
            else:
                record.comp_control_strength = 0
                
                
class OverSizePercentLine(models.Model):
    _name = "oversize.retain.percent.line1"
    
    parent_id = fields.Many2one('mechanical.microsilica1')
    
    sr_no = fields.Integer("S.No",readonly=True, copy=False, default=1)
    sample_wt_g = fields.Integer("Sample Weight (g)",default=100)
    retain_wt_45micron = fields.Float("Retained Weight on 45 Micron Sieve (g)")
    retain_wt_percent = fields.Float("% Retained Weight ",compute="compute_retain_wt_percent")
    variation_from_avrg = fields.Float("Variation from Avg. %",compute="_compute_retain_wt_percent")


    
    
    @api.depends('retain_wt_45micron','sample_wt_g')
    def compute_retain_wt_percent(self):
        for record in self:
            try:
                record.retain_wt_percent = (record.retain_wt_45micron/record.sample_wt_g)*100
            except ZeroDivisionError:
                record.retain_wt_percent = 0
                
    @api.depends('retain_wt_45micron', 'sample_wt_g', 'parent_id.avrg_oversize_percent')
    def _compute_retain_wt_percent(self):
        for record in self:
            try:
                record.retain_wt_percent = (record.retain_wt_45micron / record.sample_wt_g) * 100
                record.variation_from_avrg = (record.retain_wt_percent - record.parent_id.avrg_oversize_percent) / record.parent_id.avrg_oversize_percent * 100
            except ZeroDivisionError:
                record.retain_wt_percent = 0
                record.variation_from_avrg = 0
                
    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(OverSizePercentLine, self).create(vals)
    
    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1
             
             
           
                
class LooseBulkDensityLine(models.Model):
    _name = "dry.loose.bulk.density.line1"
    
    parent_id = fields.Many2one('mechanical.microsilica1')
    
    sr_no = fields.Integer("S.No",readonly=True, copy=False, default=1)
    wt_empty_cylinder_dry_density = fields.Float("Weight of empty Cylinder (w1) (gm)")
    wt_cylinder_microsilica_dry_density = fields.Float("Weight of empty Cylinder  + Microsilica (w2) (gm)")
    wt_microsilica_dry_density = fields.Float("weight of the microsilica (w3) (gm)",compute="compute_wt_microsilica")
    vlm_of_cylinder = fields.Float("Volume of Cylinder (m³)",default=0.00025,digits=(12,5))
    dryloose_bulk_density = fields.Float("Dry Loose Bulk Density (kg/m³)",compute="compute_dryloose_bulk_density")


    @api.depends('wt_cylinder_microsilica_dry_density','wt_empty_cylinder_dry_density')
    def compute_wt_microsilica(self):
        for record in self:
            try:
                record.wt_microsilica_dry_density = record.wt_cylinder_microsilica_dry_density-record.wt_empty_cylinder_dry_density
            except ZeroDivisionError:
                record.wt_microsilica_dry_density = 0
                
    @api.depends('wt_microsilica_dry_density','vlm_of_cylinder')
    def compute_dryloose_bulk_density(self):
        for record in self:
            try:
                record.dryloose_bulk_density = (record.wt_microsilica_dry_density/record.vlm_of_cylinder)/1000
            except ZeroDivisionError:
                record.dryloose_bulk_density = 0
                
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(LooseBulkDensityLine, self).create(vals)
    
    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1