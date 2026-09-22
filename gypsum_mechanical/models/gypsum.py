from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class GypsumMechanical(models.Model):
    _name = "mechanical.gypsum"
    _inherit = "lerm.eln"
    _rec_name = "name"


    name = fields.Char("Name",default="Gypsum")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")

    
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    # Normal Consistency 

    normal_consistency_name = fields.Char("Name",default="Normal Consistency")
    normal_consistency_visible = fields.Boolean("Normal Consistency Visible",compute="_compute_visible")

    temp_normal = fields.Float("Temperature °C")
    humidity_normal = fields.Float("Humidity")
    start_date_normal = fields.Date("Start Date")
    end_date_normal = fields.Date("End Date")



    wt_gypsum_plaster = fields.Float("Wt. of  Gypsum Plaster (g)",default=400)
    wt_water_req = fields.Float("Wt.of water required (g)")
    penetration_vicat = fields.Float("Penetraion of vicat's Plunger (mm)")
    normal_consistency = fields.Float("Normal Consistency %",compute="compute_normal_consistency",store=True)

    @api.depends('wt_gypsum_plaster','wt_water_req')
    def compute_normal_consistency(self):
        for record in self:
            record.normal_consistency = record.wt_water_req / record.wt_gypsum_plaster *100



    
    # Setting Time 

    setting_time_visible = fields.Boolean("Setting Time Visible",compute="_compute_visible")
    setting_time_name = fields.Char("Name",default="Setting Time")

    temp_setting = fields.Float("Temperature °C")
    humidity_setting = fields.Float("Humidity %")
    start_date_setting = fields.Date("Start Date")
    end_date_setting = fields.Date("End Date")

    time_water_added = fields.Datetime("The Time When water is added to cement (t1)")
    time_needle_penetrate = fields.Datetime("The time at which needle fails to penetrate the test block (t2)")
    setting_time_minutes = fields.Float("Setting Time (Minutes)", compute="_compute_initial_setting_time")


    @api.depends('time_water_added', 'time_needle_penetrate')
    def _compute_initial_setting_time(self):
        for record in self:
            if record.time_water_added and record.time_needle_penetrate:
                t1 = record.time_water_added
                t2 = record.time_needle_penetrate
                time_difference = t2 - t1

                # Convert time difference to seconds and then to minutes
                time_difference_minutes = time_difference.total_seconds() / 60
                record.setting_time_minutes = time_difference_minutes

                # record.initial_setting_time_hours = time_difference.total_seconds() / 3600
                # if time_difference_minutes % 5 == 0:
                #     record.initial_setting_time_minutes = time_difference_minutes
                # else:
                #     record.initial_setting_time_minutes = round(time_difference_minutes / 5) * 5

            else:
                # record.initial_setting_time_hours = False
                record.setting_time_minutes = False


    # Dry Bulk Density 

    dry_bulk_visible = fields.Boolean("Dry Bulk Density Visible",compute="_compute_visible")
    dry_bulk_name = fields.Char("Name",default="Dry Bulk Density")

    temp_dry_bulk = fields.Float("Temperature °C")
    humidity_dry_bulk = fields.Float("Humidity %")
    start_date_dry_bulk = fields.Date("Start Date")
    end_date_dry_bulk = fields.Date("End Date")

    wt_empty_cylinder_trial1 = fields.Float("Wt of Empty Cylinder w1")
    wt_empty_cylinder_trial2 = fields.Float("Wt of Empty Cylinder w1")
    wt_empty_cylinder_trial3 = fields.Float("Wt of Empty Cylinder w1")

    wt_empty_gypsum_trial1 = fields.Float("Wt of Gypsum w1" ,compute="_compute_wt_empty_cylinder1")
    wt_empty_gypsum_trial2 = fields.Float("Wt of Gypsum w1",compute="_compute_wt_empty_cylinder2")
    wt_empty_gypsum_trial3 = fields.Float("Wt of Gypsum w1",compute="_compute_wt_empty_cylinder3")

    wt_empty_cylinder_gypsum_trial1 = fields.Float("Weight of empty Cylinder  + Gypsum (w2)")
    wt_empty_cylinder_gypsum_trial2 = fields.Float("Weight of empty Cylinder  + Gypsum (w2)")
    wt_empty_cylinder_gypsum_trial3 = fields.Float("Weight of empty Cylinder  + Gypsum (w2)")

    volume_of_cylinder_trial1 = fields.Float("Volume of Cylinder",digits=(16,5),default=0.00025)
    volume_of_cylinder_trial2 = fields.Float("Volume of Cylinder",digits=(16,5),default=0.00025)
    volume_of_cylinder_trial3 = fields.Float("Volume of Cylinder",digits=(16,5),default=0.00025)

    dry_loose_bulf_density_trial1 = fields.Float("Dry Bulk Density (kg/m³)",compute="_compute_bulk_density_trial1")
    dry_loose_bulf_density_trial2 = fields.Float("Dry Bulk Density (kg/m³)",compute="_compute_bulk_density_trial2")
    dry_loose_bulf_density_trial3 = fields.Float("Dry Bulk Density (kg/m³)",compute="_compute_bulk_density_trial3")

    average_dry_loose_bulk_density = fields.Float("Average Dry Bulk Density (kg/m³)",compute="_compute_average_bulk_density")


    @api.depends('wt_empty_gypsum_trial1','volume_of_cylinder_trial1')
    def _compute_bulk_density_trial1(self):
        for record in self:
            if record.volume_of_cylinder_trial1 != 0:
                record.dry_loose_bulf_density_trial1 =  (record.wt_empty_gypsum_trial1 / record.volume_of_cylinder_trial1)/1000
            else:
                record.dry_loose_bulf_density_trial1 = 0

    @api.depends('wt_empty_gypsum_trial2','volume_of_cylinder_trial2')
    def _compute_bulk_density_trial2(self):
        for record in self:
            if record.volume_of_cylinder_trial2 != 0:
                record.dry_loose_bulf_density_trial2 =  (record.wt_empty_gypsum_trial2 / record.volume_of_cylinder_trial2)/1000
            else:
                record.dry_loose_bulf_density_trial2 = 0

    @api.depends('wt_empty_gypsum_trial3','volume_of_cylinder_trial3')
    def _compute_bulk_density_trial3(self):
        for record in self:
            if record.volume_of_cylinder_trial3 != 0:
                record.dry_loose_bulf_density_trial3 =  (record.wt_empty_gypsum_trial3 / record.volume_of_cylinder_trial3)/1000
            else:
                record.dry_loose_bulf_density_trial3 = 0

    @api.depends('wt_empty_cylinder_trial1','wt_empty_cylinder_gypsum_trial1')
    def _compute_wt_empty_cylinder1(self):
        for record in self:
            record.wt_empty_gypsum_trial1 = record.wt_empty_cylinder_gypsum_trial1 - record.wt_empty_cylinder_trial1


    @api.depends('wt_empty_cylinder_trial2','wt_empty_cylinder_gypsum_trial2')
    def _compute_wt_empty_cylinder2(self):
        for record in self:
            record.wt_empty_gypsum_trial2 = record.wt_empty_cylinder_gypsum_trial2 - record.wt_empty_cylinder_trial2


    @api.depends('wt_empty_cylinder_trial3','wt_empty_cylinder_gypsum_trial3')
    def _compute_wt_empty_cylinder3(self):
        for record in self:
            record.wt_empty_gypsum_trial3 = record.wt_empty_cylinder_gypsum_trial3 - record.wt_empty_cylinder_trial3

    @api.depends('dry_loose_bulf_density_trial1','dry_loose_bulf_density_trial2','dry_loose_bulf_density_trial3')
    def _compute_average_bulk_density(self):
        for record in self:
            record.average_dry_loose_bulk_density = (record.dry_loose_bulf_density_trial1 + record.dry_loose_bulf_density_trial2 + record.dry_loose_bulf_density_trial3)/3



    # Free From Coarse Particle

    coarse_particle_visible = fields.Boolean("Free From Coarse Particle Visible",compute="_compute_visible")
    coarse_particle_name = fields.Char("Name",default="Free From Coarse Particle")

    temp_coarse_particle = fields.Float("Temperature °C")
    humidity_coarse_particle = fields.Float("Humidity %")
    start_date_coarse_particle = fields.Date("Start Date")
    end_date_coarse_particle = fields.Date("End Date")

    coarse_particle_table = fields.One2many('mechanical.coarse.particle.line','parent_id',string="Coarse Particle Table")
    average_coarse_particle = fields.Float("Average",compute="_compute_average_coarse")

    @api.depends('coarse_particle_table.coarse_particle')
    def _compute_average_coarse(self):
        for record in self:
            try:
                record.average_coarse_particle = sum(record.coarse_particle_table.mapped('coarse_particle'))/len(record.coarse_particle_table)
            except:
                record.average_coarse_particle = 0



    # Compressive Strength 

    compressive_name = fields.Char("Name",default="Compressive Strength")
    compressive_visible = fields.Boolean("Compressive Visible",compute="_compute_visible")

    temp_percent_compressive = fields.Float("Temperature °C")
    humidity_percent_compressive = fields.Float("Humidity %")
    start_date_compressive = fields.Date("Start Date")
    end_date_compressive = fields.Date("End Date")

    wt_of_gypsum_compressive = fields.Float("Wt. of Gypsum(g)",default=50)
    wt_of_standard_sand_grade1 = fields.Float("Weight of Standard Sand (g) Grade-I",default=80)
    wt_of_standard_sand_grade2 = fields.Float("Weight of Standard Sand (g) Grade-II",default=80)
    wt_of_standard_sand_grade3 = fields.Float("Weight of Standard Sand (g) Grade-III",default=80)
    total_weight = fields.Float("Total Weight",compute="compute_total_weight_compressive")
    quantity_of_water = fields.Float("Quantity of Water")

    @api.depends('wt_of_gypsum_compressive','wt_of_standard_sand_grade1','wt_of_standard_sand_grade2','wt_of_standard_sand_grade3')
    def compute_total_weight_compressive(self):
        self.total_weight = self.wt_of_gypsum_compressive + self.wt_of_standard_sand_grade1 + self.wt_of_standard_sand_grade2 + self.wt_of_standard_sand_grade3 

    @api.depends('normal_consistency','total_weight')
    def _compute_quantity_of_water(self):
        self.quantity_of_water = ((self.normal_consistency/4 +3)/100)*self.total_weight


    # 1 days Casting
    casting_1_name = fields.Char("Name",default="1 Days")
    days_1_done = fields.Boolean("Done")

    # casting_3_visible = fields.Boolean("3 days Visible",compute="_compute_visible")

    casting_date_1days = fields.Date(string="Date of Casting")
    testing_date_1days = fields.Date(string="Date of Testing",compute="_compute_testing_date_1days")
    casting_1_days_tables = fields.One2many('gypsum.casting.1days.line','parent_id',string="1 Days")
    average_casting_1days = fields.Float("Average",compute="_compute_average_1days")
    compressive_strength_1_days = fields.Float("Compressive Strength")
    status_1days = fields.Boolean("Done")


    @api.depends('casting_1_days_tables.compressive_strength')
    def _compute_average_1days(self):
        for record in self:
            try:
                record.average_casting_1days = sum(record.casting_1_days_tables.mapped('compressive_strength'))/len(record.casting_1_days_tables)
            except:
                record.average_casting_1days = 0
    
    @api.depends('casting_date_1days')
    def _compute_testing_date_1days(self):
        for record in self:
            if record.casting_date_1days:
                cast_date = fields.Datetime.from_string(record.casting_date_1days)
                testing_date = cast_date + timedelta(days=1)
                record.testing_date_1days = fields.Datetime.to_string(testing_date)
            else:
                record.testing_date_1days = False


     # 7 Days Casting

    casting_7_name = fields.Char("Name",default="7 Days")
    # compressive_7_visible = fields.Boolean("7 days Visible",compute="_compute_visible")
    days_7_done = fields.Boolean("Done")


    casting_date_7days = fields.Date(string="Date of Casting")
    testing_date_7days = fields.Date(string="Date of Testing",compute="_compute_testing_date_7days")
    casting_7_days_tables = fields.One2many('gypsum.casting.7days.line','parent_id',string="7 Days")
    average_casting_7days = fields.Float("Average",compute="_compute_average_7days")
    status_7days = fields.Boolean("Done")
    # compressive_strength_7_days = fields.Float("Compressive Strength",compute="_compute_compressive_strength_7days" ,digits=(16,1))

    # compressive_7days_conformity = fields.Selection([
    #     ('pass', 'Pass'),
    #     ('fail', 'Fail'),
    # ], string='Conformity', default='fail',compute="_compute_compressive_7days_conformity")

    # compressive_7days_nabl = fields.Selection([
    #     ('pass', 'Pass'),
    #     ('fail', 'Fail'),
    # ], string='NABL', default='fail',compute="_compute_compressive_7days_nabl")


    # @api.depends('compressive_strength_7_days','eln_ref','grade')
    # def _compute_compressive_7days_conformity(self):
    #     for record in self:
    #         record.compressive_7days_conformity = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a267dec2-59df-4c9d-827b-69778c31c29b')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a267dec2-59df-4c9d-827b-69778c31c29b')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 req_min = material.req_min
    #                 req_max = material.req_max
    #                 mu_value = line.mu_value
    #                 lower = record.compressive_strength_7_days - record.compressive_strength_7_days*mu_value
    #                 upper = record.compressive_strength_7_days + record.compressive_strength_7_days*mu_value
    #                 if lower >= req_min and upper <= req_max :
    #                     record.compressive_7days_conformity = 'pass'
    #                     break
    #                 else:
    #                     record.compressive_7days_conformity = 'fail'

    # @api.depends('compressive_strength_7_days','eln_ref','grade')
    # def _compute_compressive_7days_nabl(self):
        
    #     for record in self:
    #         record.compressive_7days_nabl = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a267dec2-59df-4c9d-827b-69778c31c29b')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a267dec2-59df-4c9d-827b-69778c31c29b')]).parameter_table
            
    #         lab_min = line.lab_min_value
    #         lab_max = line.lab_max_value
    #         mu_value = line.mu_value
            
    #         lower = record.compressive_strength_7_days - record.compressive_strength_7_days*mu_value
    #         upper = record.compressive_strength_7_days + record.compressive_strength_7_days*mu_value
    #         if lower >= lab_min and upper <= lab_max:
    #             record.compressive_7days_nabl = 'pass'
    #             break
    #         else:
    #             record.compressive_7days_nabl = 'fail'
    

    @api.depends('casting_7_days_tables.compressive_strength')
    def _compute_average_7days(self):
        for record in self:
            try:
                record.average_casting_7days = sum(record.casting_7_days_tables.mapped('compressive_strength'))/len(record.casting_7_days_tables)
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


    # @api.depends('average_casting_7days')
    # def _compute_compressive_strength_7days(self):
    #     for record in self:
    #         integer_part = math.floor(record.average_casting_7days)
    #         fractional_part = record.average_casting_7days - integer_part
    #         if fractional_part > 0 and fractional_part <= 0.25:
    #             compressive_strength_7_days = round(integer_part,1)
    #             record.compressive_strength_7_days = compressive_strength_7_days
    #         elif fractional_part > 0.25 and fractional_part <= 0.75:
    #             compressive_strength_7_days = round(integer_part + 0.5,1)
    #             record.compressive_strength_7_days = compressive_strength_7_days
    #         elif fractional_part > 0.75 and fractional_part <= 1:
    #             compressive_strength_7_days = round(integer_part + 1,1)
    #             record.compressive_strength_7_days = compressive_strength_7_days
    #         else:
    #             record.compressive_strength_7_days = 0



    @api.depends('tests', 'sample_parameters')
    def _compute_visible(self):
        normal_consistency_test = self.env['mechanical.gypsum.test'].sudo().search([('name', '=', 'Normal Consistency')])
        setting_time_test = self.env['mechanical.gypsum.test'].sudo().search([('name', '=', 'Setting Time')])
        bulk_density_test = self.env['mechanical.gypsum.test'].sudo().search([('name', '=', 'Dry Bulk Density')])
        coarse_particle_test = self.env['mechanical.gypsum.test'].sudo().search([('name', '=', 'Free From Coarse Particle')])
        compressive_test = self.env['mechanical.gypsum.test'].sudo().search([('name', '=', 'Compressive Strength')])



        for record in self:
            record.normal_consistency_visible = False
            record.setting_time_visible  = False  
            record.dry_bulk_visible = False
            record.coarse_particle_visible = False
            record.compressive_visible = False


            
            if normal_consistency_test in record.tests:
                record.normal_consistency_visible = True
            if setting_time_test in record.tests:
                record.setting_time_visible = True
            if bulk_density_test in record.tests:
                record.dry_bulk_visible = True
            if coarse_particle_test in record.tests:
                record.coarse_particle_visible = True
            if compressive_test in record.tests:
                record.compressive_visible = True
                record.normal_consistency_visible = True


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '04efc0bd-63e2-4e23-9436-51cde4fe2c57':
                    record.normal_consistency_visible = True
                if sample.internal_id == '8e7282a0-3e80-4cee-b520-128b5a5f2015':
                    record.setting_time_visible = True
                if sample.internal_id == '2d915d3b-0324-40f1-a2b9-e385a7cdc90d':
                    record.dry_bulk_visible = True
                if sample.internal_id == 'ec5fa471-0e2a-411a-b1de-72cc41aed2d5':
                    record.coarse_particle_visible = True
                if sample.internal_id == '65321ea8-98e6-4d73-8941-5ac65d2504a9':
                    record.compressive_visible = True
                    record.normal_consistency_visible = True

    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == '04efc0bd-63e2-4e23-9436-51cde4fe2c57':
                result.result_char = round(self.normal_consistency,2)
                continue
            if result.parameter.internal_id == '8e7282a0-3e80-4cee-b520-128b5a5f2015':
                result.result_char = round(self.setting_time_minutes,2)
                continue
            if result.parameter.internal_id == '2d915d3b-0324-40f1-a2b9-e385a7cdc90d':
                result.result_char = round(self.average_dry_loose_bulk_density,2)
                continue
            if result.parameter.internal_id == 'ec5fa471-0e2a-411a-b1de-72cc41aed2d5':
                result.result_char = round(self.average_coarse_particle,2)
                continue
            if result.parameter.internal_id == '65321ea8-98e6-4d73-8941-5ac65d2504a9':
                result.result_char = round(self.normal_consistency,2)
                continue
            

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
        record = super(GypsumMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    def get_all_fields(self):
        record = self.env['mechanical.gypsum'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

class CoarseParticleTable(models.Model):
    _name= "mechanical.coarse.particle.line"

    parent_id = fields.Many2one('mechanical.gypsum')

    sample_weight = fields.Float("Sample Weight",default=100)
    retained_weight = fields.Float("Retained Weight on 150 mic sieve (g)")
    coarse_particle = fields.Float("Free From Coarse Particle %",compute="_compute_coarse_particle")

    @api.depends('sample_weight','retained_weight')
    def _compute_coarse_particle(self):
        for record in self:
            if record.retained_weight != 0:
                record.coarse_particle = (record.retained_weight / record.sample_weight)*100
            else:
                record.coarse_particle = 0


class Casting1DaysLineGypsum(models.Model):
    _name = "gypsum.casting.1days.line"

    parent_id = fields.Many2one('mechanical.gypsum',string="Parent Id")
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
                record.compressive_strength = round(((record.crushing_load / record.crosssectional_area)*1000),3)
            else:
                record.compressive_strength = 0



class Casting7DaysLine(models.Model):
    _name = "gypsum.casting.7days.line"

    parent_id = fields.Many2one('mechanical.gypsum')

    length = fields.Float("Length in mm")
    width = fields.Float("Width in mm")
    crosssectional_area = fields.Float("Crosssectional Area",compute="_compute_crosssectional_area")
    wt_of_cement_cube = fields.Float("wt of Cement Cube in gm")
    crushing_load = fields.Float("Crushing Load in KN")
    compressive_strength = fields.Float("Compressive Strength (N/mm²)",compute="_compute_compressive_strength")

    @api.depends('length','width')
    def _compute_crosssectional_area(self):
        for record in self:
            record.crosssectional_area = round(record.length * record.width,2)

    @api.depends('crosssectional_area','crushing_load')
    def _compute_compressive_strength(self):
        for record in self:
            if record.crosssectional_area != 0:
                record.compressive_strength = round((record.crushing_load / record.crosssectional_area)*1000,2)
            else:
                record.compressive_strength = 0



class MechanicalTmtTest(models.Model):
    _name = "mechanical.gypsum.test"
    _rec_name = "name"
    name = fields.Char("Name")