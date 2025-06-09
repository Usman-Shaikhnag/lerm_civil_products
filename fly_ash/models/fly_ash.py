from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math





class FlyaschNormalConsistency(models.Model):
    _name = "mechanical.flyasch.normalconsistency1"
    _inherit = "lerm.eln"
    _description = 'mechanical.flyasch.normalconsistency1'
    _rec_name = "name_fly"


    name_fly = fields.Char("Name",default="Fly Ash")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    temp_percent_normal = fields.Float("Temperature °c")
    humidity_percent_normal = fields.Float("Humidity %")

     ## Normal Consistency

    # tests = fields.Many2many("mechanical.cement.test",string="Tests")
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    normal_consistency_name = fields.Char("Name",default="Normal Consistency")
    normal_consistency_visible = fields.Boolean("Normal Consistency Visible",compute="_compute_visible")
    start_date_normal = fields.Date("Start Date")
    end_date_normal = fields.Date("End Date")


    gravity_of_flyash1 = fields.Float(string="Specific Gravity of Flyash")
    # gravity_of_flyash2 = fields.Float(string="Specific Gravity of Flyash")

    gravity_of_cement1 = fields.Float(string="Specific Gravity of Cement")
    # gravity_of_cement2 = fields.Float(string="Specific Gravity of Cement")


    fly_ash_n1 = fields.Float(string="N",compute="_compute_fly_ash_n1")
    # fly_ash_n2 = fields.Float(string="N",compute="_compute_fly_ash_n2")

    wt_of_flash_1 = fields.Float(string="Wt. of  Flyash",compute="_compute_wt_of_flash_1")
    # wt_of_flash_2 = fields.Float(string="Wt. of  Flyash",compute="_compute_wt_of_flash_2")

    wt_of_cement_1 = fields.Float(string="Wt. of  Cement (g)",default=0.8*400)
    # wt_of_cement_2 = fields.Float(string="Wt. of  Cement (g)",default=0.8*400)

    total_wt_of_sample_fly_1 = fields.Float(string="Total Weight of Sample(g)",compute="_compute_wt_of_sample_fly_1")
    # total_wt_of_sample_fly_2 = fields.Float(string="Total Weight of Sample(g)",compute="_compute_wt_of_sample_fly_2")

    wt_of_water_required_fly_1 = fields.Float(string="Wt.of water required (g)")
    # wt_of_water_required_fly_2 = fields.Float(string="Wt.of water required (g)")

    penetration_planger_fly_1 = fields.Float(string="Penetraion of vicat's Plunger (mm)")
    # penetration_planger_fly_2 = fields.Float(string="Penetraion of vicat's Plunger (mm)")

    normal_consistency_fly_1 = fields.Float(string="Normal Consistency, %",compute="_compute_normal_consistency_fly_1")
    # normal_consistency_fly_2 = fields.Float(string="Normal Consistency, %",compute="_compute_normal_consistency_fly_2")

    # @api.depends('gravity_of_flyash1', 'gravity_of_cement1')
    # def _compute_fly_ash_n1(self):
    #     for record in self:
    #         if record.gravity_of_cement1 != 0:
    #             record.fly_ash_n1 = record.gravity_of_flyash1 / record.gravity_of_cement1
    #         else:
    #             record.fly_ash_n1 = 0.0
    @api.depends('gravity_of_flyash1', 'gravity_of_cement1')
    def _compute_fly_ash_n1(self):
        for record in self:
            if record.gravity_of_cement1 != 0:
                record.fly_ash_n1 = record.gravity_of_flyash1 / record.gravity_of_cement1
            else:
                record.fly_ash_n1 = 0.0

                

    # @api.depends('gravity_of_flyash2', 'gravity_of_cement2')
    # def _compute_fly_ash_n2(self):
    #     for record in self:
    #         if record.gravity_of_cement2 != 0:
    #             record.fly_ash_n2 = record.gravity_of_flyash2 / record.gravity_of_cement2
    #         else:
    #             record.fly_ash_n2 = 0.0

    @api.depends('fly_ash_n1')
    def _compute_wt_of_flash_1(self):
        for record in self:
            record.wt_of_flash_1 = (0.2 * record.fly_ash_n1) * 400

    # @api.depends('fly_ash_n2')
    # def _compute_wt_of_flash_2(self):
    #     for record in self:
    #         record.wt_of_flash_2 = 0.2 * record.fly_ash_n2 * 400

    @api.depends('wt_of_cement_1','wt_of_flash_1')
    def _compute_wt_of_sample_fly_1(self):
        for record in self:
            record.total_wt_of_sample_fly_1 = record.wt_of_cement_1 + record.wt_of_flash_1

    # @api.depends('wt_of_cement_2','wt_of_flash_2')
    # def _compute_wt_of_sample_fly_2(self):
    #     for record in self:
    #         record.total_wt_of_sample_fly_2 = record.wt_of_cement_2 + record.wt_of_flash_2

    @api.depends('wt_of_water_required_fly_1', 'total_wt_of_sample_fly_1')
    def _compute_normal_consistency_fly_1(self):
        for record in self:
            if record.total_wt_of_sample_fly_1 != 0:
                record.normal_consistency_fly_1 = (record.wt_of_water_required_fly_1 / record.total_wt_of_sample_fly_1) * 100
            else:
                record.normal_consistency_fly_1 = 0.0


    # @api.depends('wt_of_water_required_fly_2', 'total_wt_of_sample_fly_2')
    # def _compute_normal_consistency_fly_2(self):
    #     for record in self:
    #         if record.total_wt_of_sample_fly_2 != 0:
    #             record.normal_consistency_fly_2 = (record.wt_of_water_required_fly_2 / record.total_wt_of_sample_fly_2) * 100
    #         else:
    #             record.normal_consistency_fly_2 = 0.0


    normal_consistency_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_normal_consistency_conformity", store=True)

    @api.depends('normal_consistency_fly_1','eln_ref','grade')
    def _compute_normal_consistency_conformity(self):
        
        for record in self:
            record.normal_consistency_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','124fgrt3-1b3c-43ae-9c20-5421b6d6edf9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','124fgrt3-1b3c-43ae-9c20-5421b6d6edf9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.normal_consistency_fly_1 - record.normal_consistency_fly_1*mu_value
                    upper = record.normal_consistency_fly_1 + record.normal_consistency_fly_1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.normal_consistency_conformity = 'pass'
                        break
                    else:
                        record.normal_consistency_conformity = 'fail'

    normal_consistency_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_normal_consistency_nabl", store=True)

    @api.depends('normal_consistency_fly_1','eln_ref','grade')
    def _compute_normal_consistency_nabl(self):
        
        for record in self:
            record.normal_consistency_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','124fgrt3-1b3c-43ae-9c20-5421b6d6edf9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','124fgrt3-1b3c-43ae-9c20-5421b6d6edf9')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.normal_consistency_fly_1 - record.normal_consistency_fly_1*mu_value
            upper = record.normal_consistency_fly_1 + record.normal_consistency_fly_1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.normal_consistency_nabl = 'pass'
                break
            else:
                record.normal_consistency_nabl = 'fail'





    # Setting Time

    # setting_time_visible = fields.Boolean("Setting Time Visible",compute="_compute_visible")
    # setting_time_name = fields.Char("Name",default="Setting Time")

    # temp_percent_setting = fields.Float("Temperature °c")
    # humidity_percent_setting = fields.Float("Humidity %")
    # start_date_setting = fields.Date("Start Date")
    # end_date_setting = fields.Date("End Date")

    # total_wt_of_sample_setting_time = fields.Float(string="Total Weight of Sample(g)",compute="_compute_total_wt_of_sample_setting_time",store=True)
    # wt_of_water_required_setting_time = fields.Float("Wt.of water required (g)",compute="_compute_wt_of_water_required",store=True)


    # @api.depends('total_wt_of_sample_fly_1')
    # def _compute_total_wt_of_sample_setting_time(self):
    #     for record in self:
    #         record.total_wt_of_sample_setting_time = record.total_wt_of_sample_fly_1

    # @api.depends('normal_consistency_fly_1','total_wt_of_sample_setting_time')
    # def _compute_wt_of_water_required(self):
    #     for record in self:
    #         record.wt_of_water_required_setting_time =  (0.85 * record.normal_consistency_fly_1 * record.total_wt_of_sample_setting_time) / 100


    # initial_setting_time = fields.Char("Name", default="Initial Setting Time")
    # time_water_added = fields.Datetime("The Time When water is added to cement (t1)")
    # time_needle_fails = fields.Datetime("The time at which needle fails to penetrate the test block to a point 5 ± 0.5 mm (t2)")
    # initial_setting_time_hours = fields.Char("Initial Setting Time (t2-t1) (Hours)", compute="_compute_initial_setting_time")
    # initial_setting_time_minutes = fields.Float("Initial Setting Time", compute="_compute_initial_setting_time")
    # initial_setting_time_minutes_unrounded = fields.Char("Initial Setting Time",compute="_compute_initial_setting_time")

   
    

    # @api.depends('time_water_added', 'time_needle_fails')
    # def _compute_initial_setting_time(self):
    #     for record in self:
    #         if record.time_water_added and record.time_needle_fails:
    #             t1 = record.time_water_added
    #             t2 = record.time_needle_fails
    #             time_difference = t2 - t1

    #             # Convert time difference to seconds and then to minutes
    #             time_difference_minutes = time_difference.total_seconds() / 60

    #             initial_setting_time_hours = time_difference.total_seconds() / 3600
    #             time_delta = timedelta(hours=initial_setting_time_hours)
    #             record.initial_setting_time_hours = "{:0}:{:02}".format(int(time_delta.total_seconds() // 3600), int((time_delta.total_seconds() % 3600) // 60))
    #             if time_difference_minutes % 5 == 0:
    #                 record.initial_setting_time_minutes = time_difference_minutes
    #             else:
    #                 record.initial_setting_time_minutes = round(time_difference_minutes / 5) * 5

    #             record.initial_setting_time_minutes_unrounded = time_difference_minutes

    #         else:
    #             record.initial_setting_time_hours = False
    #             record.initial_setting_time_minutes = False
    #             record.initial_setting_time_minutes_unrounded = False

   

    #  #Final setting Time

    # final_setting_time = fields.Char("Name",default="Final Setting Time")
    # time_needle_make_impression = fields.Datetime("The Time at which the needle make an impression on the surface of test block while attachment fails to do (t3)")
    # final_setting_time_hours = fields.Char("Final Setting Time (t3-t1) (Hours)",compute="_compute_final_setting_time")
    # final_setting_time_minutes = fields.Char("Final Setting Time",compute="_compute_final_setting_time")
    # final_setting_time_minutes_unrounded = fields.Char("Final Setting Time Unrounded",compute="_compute_final_setting_time")




    # @api.depends('time_needle_make_impression')
    # def _compute_final_setting_time(self):
    #     for record in self:
    #         if record.time_needle_make_impression and record.time_water_added:
    #             t1 = record.time_water_added
    #             t2 = record.time_needle_make_impression
    #             time_difference = t2 - t1

    #             record.final_setting_time_hours = time_difference
    #             final_setting_time = time_difference.total_seconds() / 60
    #             if final_setting_time % 5 == 0:
    #                 record.final_setting_time_minutes = final_setting_time
    #             else:
    #                 record.final_setting_time_minutes = round(final_setting_time / 5) * 5

    #             record.final_setting_time_minutes_unrounded = final_setting_time
    #         else:
    #             record.final_setting_time_hours = False
    #             record.final_setting_time_minutes = False
    #             record.final_setting_time_minutes_unrounded = False

    ### setting Time,Final Setting Time	

    initial_setting_time_visible = fields.Boolean("Initial Setting Time Visible",compute="_compute_visible")
    initial_setting_time_name = fields.Char("Name",default="Initial Setting Time")

    temp_percent_setting = fields.Float("Temperature °C",digits=(16,1))
    humidity_percent_setting = fields.Float("Humidity %")
    start_date_setting = fields.Date("Start Date")
    end_date_setting = fields.Date("End Date")

    # wt_of_fly_settingg_time = fields.Float("Total Weight of Sample(g)",compute="_compute_total_wt_of_sample_setting_time",store=True)
    wt_of_fly_settingg_time = fields.Float("Total Weight of Sample(g)",default=377.40)
    wt_of_water_required_setting_time = fields.Float("Wt.of water required (g) (0.85*P%)" , compute="_compute_wt_of_water_required",store=True )

    # @api.depends('total_wt_of_sample_fly_1')
    # def _compute_total_wt_of_sample_setting_time(self):
    #     for record in self:
    #         record.wt_of_fly_settingg_time = record.total_wt_of_sample_fly_1

    @api.depends('normal_consistency_fly_1','wt_of_fly_settingg_time')
    def _compute_wt_of_water_required(self):
        for record in self:
            record.wt_of_water_required_setting_time =  (0.85 * record.normal_consistency_fly_1 * record.wt_of_fly_settingg_time) / 100

    #Initial setting Time

    setting_time_name = fields.Char("Name", default="Setting Time")
    time_water_added = fields.Datetime("The Time When water is added to cement (t1)")
    time_needle_fails = fields.Datetime("The time at which needle fails to penetrate the test block to a point 5 ± 0.5 mm (t2)")
    initial_setting_time_hours = fields.Char("Initial Setting Time (t2-t1) (Hours)", compute="_compute_initial_setting_time")
    initial_setting_time_minutes = fields.Integer("Initial Setting Time Rounded", compute="_compute_initial_setting_time")
    initial_setting_time_minutes_unrounded = fields.Char("Initial Setting Time",compute="_compute_initial_setting_time")

    initial_setting_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity',compute="_compute_initial_setting_conformity", default='fail')

    initial_setting_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL',compute="_compute_initial_setting_nabl", default='pass')


    @api.depends('initial_setting_time_minutes_unrounded','eln_ref','grade')
    def _compute_initial_setting_conformity(self):
        for record in self:
            record.initial_setting_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2014fgr32-6bbe-4fdf-9571-a5a099be0293')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2014fgr32-6bbe-4fdf-9571-a5a099be0293')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = float(record.initial_setting_time_minutes_unrounded) - float(record.initial_setting_time_minutes_unrounded)*mu_value
                    upper = float(record.initial_setting_time_minutes_unrounded) + float(record.initial_setting_time_minutes_unrounded)*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.initial_setting_conformity = 'pass'
                        break
                    else:
                        record.initial_setting_conformity = 'fail'

    @api.depends('initial_setting_time_minutes_unrounded','eln_ref','grade')
    def _compute_initial_setting_nabl(self):
        
        for record in self:
            record.initial_setting_nabl = 'fail'
            line = self.env['lerm.parameter.master'].search([('internal_id','=','2014fgr32-6bbe-4fdf-9571-a5a099be0293')])
            materials = self.env['lerm.parameter.master'].search([('internal_id','=','2014fgr32-6bbe-4fdf-9571-a5a099be0293')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = float(record.initial_setting_time_minutes_unrounded) - float(record.initial_setting_time_minutes_unrounded)*mu_value
            upper = float(record.initial_setting_time_minutes_unrounded) + float(record.initial_setting_time_minutes_unrounded)*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.initial_setting_nabl = 'pass'
                break
            else:
                record.initial_setting_nabl = 'fail'


    @api.depends('time_water_added', 'time_needle_fails')
    def _compute_initial_setting_time(self):
        for record in self:
            if record.time_water_added and record.time_needle_fails:
                t1 = record.time_water_added
                t2 = record.time_needle_fails
                time_difference = t2 - t1

                # Convert time difference to seconds and then to minutes
                time_difference_minutes = time_difference.total_seconds() / 60

                initial_setting_time_hours = time_difference.total_seconds() / 3600
                time_delta = timedelta(hours=initial_setting_time_hours)
                record.initial_setting_time_hours = "{:0}:{:02}".format(int(time_delta.total_seconds() // 3600), int((time_delta.total_seconds() % 3600) // 60))
                if time_difference_minutes % 5 == 0:
                    record.initial_setting_time_minutes = time_difference_minutes
                else:
                    record.initial_setting_time_minutes = round(time_difference_minutes / 5) * 5

                record.initial_setting_time_minutes_unrounded = time_difference_minutes

            else:
                record.initial_setting_time_hours = False
                record.initial_setting_time_minutes = False
                record.initial_setting_time_minutes_unrounded = False


    #Final setting Time

    final_setting_time_visible = fields.Boolean("Final Setting Time Visible",compute="_compute_visible")
    final_setting_time_name = fields.Char("Name",default="Final Setting Time")

    time_needle_make_impression = fields.Datetime("The Time at which the needle make an impression on the surface of test block while attachment fails to do (t3)")
    final_setting_time_hours = fields.Char("Final Setting Time (t2-t1) (Hours)",compute="_compute_final_setting_time")
    final_setting_time_minutes_unrounded = fields.Char("Final Setting Time",compute="_compute_final_setting_time")
    final_setting_time_minutes = fields.Char("Final Setting Time Rounded",compute="_compute_final_setting_time")

    final_setting_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity',compute="_compute_final_setting_conformity", default='fail')

    final_setting_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL',compute="_compute_final_setting_nabl", default='pass')


    @api.depends('final_setting_time_minutes_unrounded','eln_ref','grade')
    def _compute_final_setting_conformity(self):
        for record in self:
            record.final_setting_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32145grte8-6526-4fcc-a5ec-18cc1ae10857')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32145grte8-6526-4fcc-a5ec-18cc1ae10857')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = float(record.final_setting_time_minutes_unrounded) - float(record.final_setting_time_minutes_unrounded)*mu_value
                    upper = float(record.final_setting_time_minutes_unrounded) + float(record.final_setting_time_minutes_unrounded)*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.final_setting_conformity = 'pass'
                        break
                    else:
                        record.final_setting_conformity = 'fail'

    @api.depends('final_setting_time_minutes_unrounded','eln_ref','grade')
    def _compute_final_setting_nabl(self):
        
        for record in self:
            record.final_setting_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32145grte8-6526-4fcc-a5ec-18cc1ae10857')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32145grte8-6526-4fcc-a5ec-18cc1ae10857')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = float(record.final_setting_time_minutes_unrounded) - float(record.final_setting_time_minutes_unrounded)*mu_value
            upper = float(record.final_setting_time_minutes_unrounded) + float(record.final_setting_time_minutes_unrounded)*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.final_setting_nabl = 'pass'
                break
            else:
                record.final_setting_nabl = 'fail'



    @api.depends('time_needle_make_impression')
    def _compute_final_setting_time(self):
        for record in self:
            if record.time_needle_make_impression and record.time_water_added:
                t1 = record.time_water_added
                t2 = record.time_needle_make_impression
                time_difference = t2 - t1
                record.final_setting_time_minutes = time_difference
                record.final_setting_time_hours = time_difference
                final_setting_time = time_difference.total_seconds() / 60
                if final_setting_time % 5 == 0:
                    record.final_setting_time_minutes = final_setting_time
                else:
                    record.final_setting_time_minutes =  round(final_setting_time / 5) * 5
                record.final_setting_time_minutes_unrounded = final_setting_time
            else:
                record.final_setting_time_hours = False
                record.final_setting_time_minutes = False
                record.final_setting_time_minutes_unrounded = False



        


     #  Particles retained on 45 micron IS sieve (wet sieving) 

    particles_retained = fields.Char("Name",default=" Particles retained on 45 micron IS sieve (wet sieving)")
    particles_retained_visible = fields.Boolean("Particles retained Visible",compute="_compute_visible")

    temp_percent_retained = fields.Float("Temperature °c")
    humidity_percent_retained = fields.Float("Humidity %")
    start_date_retained = fields.Date("Start Date")
    end_date_retained = fields.Date("End Date")


    particles_retained_table = fields.One2many('particles.retained.line1','parent_id',string="Particles Retained")
    average_weight_retained = fields.Float("Average", compute="_compute_average_weight_retained")

    prcent_retaind = fields.Float(string="% Weight Retained",compute="_compute_prcent_retained",digits=(12,1))

 
    @api.depends('particles_retained_table.wt_retained')  # Replace 'weight' with the actual field name in particles.retained.line
    def _compute_average_weight_retained(self):
        for record in self:
            # Calculate the average weight
            total_weight = sum(record.particles_retained_table.mapped('wt_retained'))
            count = len(record.particles_retained_table)
            record.average_weight_retained = total_weight / count if count else 0.0

    # @api.depends('average_weight_retained')
    # def _compute_prcent_retained(self):
    #     for record in self:
    #         # Round the average weight to the nearest 0.5
    #         rounded_average = round(record.average_weight_retained * 2) / 2
    #         record.prcent_retaind = rounded_average
    
    @api.depends('average_weight_retained')
    def _compute_prcent_retained(self):
        for record in self:
            # Round the average weight to the nearest 0.1
            rounded_average = round(record.average_weight_retained * 10) / 10
            record.prcent_retaind = rounded_average


    prcent_retaind_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_prcent_retaind_conformity", store=True)

    @api.depends('prcent_retaind','eln_ref','grade')
    def _compute_prcent_retaind_conformity(self):
        
        for record in self:
            record.prcent_retaind_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214vbfsd-0da6-4ec4-a91e-d41c44f5edb5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214vbfsd-0da6-4ec4-a91e-d41c44f5edb5')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.prcent_retaind - record.prcent_retaind*mu_value
                    upper = record.prcent_retaind + record.prcent_retaind*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.prcent_retaind_conformity = 'pass'
                        break
                    else:
                        record.prcent_retaind_conformity = 'fail'

    prcent_retaind_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_prcent_retaind_nabl", store=True)
    
    @api.depends('prcent_retaind','eln_ref','grade')
    def _compute_prcent_retaind_nabl(self):
        
        for record in self:
            record.prcent_retaind_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214vbfsd-0da6-4ec4-a91e-d41c44f5edb5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214vbfsd-0da6-4ec4-a91e-d41c44f5edb5')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.prcent_retaind - record.prcent_retaind*mu_value
            upper = record.prcent_retaind + record.prcent_retaind*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.prcent_retaind_nabl = 'pass'
                break
            else:
                record.prcent_retaind_nabl = 'fail'








    # Soundness Test
    soundness_name_fly = fields.Char("Name",default="Soundness by Le-Chatelier Method")
    soundness_visible = fields.Boolean("Soundness Visible",compute="_compute_visible")

    temp_percent_soundness = fields.Float("Temperature °c")
    humidity_percent_soundness = fields.Float("Humidity %")
    start_date_soundness = fields.Date("Start Date")
    end_date_soundness = fields.Date("End Date")


    wt_of_flyash_soundness = fields.Float(string="Wt. of Flyash",compute="_compute_wt_of_flyash_soundness")
    wt_of_cement_soundness = fields.Float(string="Wt. of Cement (g)",default=0.8*100)
    total_wt_sample_soundness = fields.Float(string="Total Weight of Sample(g)",compute="_compute_total_wt_sample_soundness")
    wt_of_water_req_soundness = fields.Float(string="Wt.of water required (g)",compute="_compute_wt_of_water_req_soundness")

    @api.depends('fly_ash_n1')
    def _compute_wt_of_flyash_soundness(self):
        for record in self:
            record.wt_of_flyash_soundness = (0.2 * record.fly_ash_n1 * 100)

    @api.depends('wt_of_flyash_soundness','wt_of_cement_soundness')
    def _compute_total_wt_sample_soundness(self):
        for record in self:
            record.total_wt_sample_soundness = record.wt_of_flyash_soundness + record.wt_of_cement_soundness

    @api.depends('normal_consistency_fly_1', 'total_wt_sample_soundness')
    def _compute_wt_of_water_req_soundness(self):
      for record in self:
        if record.total_wt_sample_soundness != 0:
            record.wt_of_water_req_soundness = (0.78 * record.normal_consistency_fly_1 / 100) * record.total_wt_sample_soundness
        else:
            record.wt_of_water_req_soundness = 0.0

    soundness_table = fields.One2many('flyash.soundness.line1','parent_id',string="Soundness")
    average_soundness = fields.Float("Average",compute="_compute_average_soundness")
    expansion_soundness = fields.Float("Expansion(mm)",compute="_compute_expansion_soundness" ,digits=(16,1))

    @api.depends('soundness_table.expansion')
    def _compute_average_soundness(self):
        for record in self:
            try:
                record.average_soundness = sum(record.soundness_table.mapped('expansion'))/len(record.soundness_table)
            except:
                record.average_soundness = 0

    # @api.depends('average_soundness')
    # def _compute_expansion_soundness(self):
    #     for record in self:
    #         integer_part = math.floor(record.average_soundness)
    #         fractional_part = record.average_soundness - integer_part
    #         if fractional_part > 0 and fractional_part <= 0.25:
    #             record.expansion_soundness = integer_part
    #         elif fractional_part > 0.25 and fractional_part <= 0.75:
    #             record.expansion_soundness = integer_part + 0.5
    #         elif fractional_part > 0.75 and fractional_part <= 1:
    #             record.expansion_soundness = integer_part + 1
    #         else:
    #             record.expansion_soundness = 0


    @api.depends('average_soundness')
    def _compute_expansion_soundness(self):
        for record in self:
            integer_part = math.floor(record.average_soundness)
            fractional_part = record.average_soundness - integer_part
            if fractional_part > 0 and fractional_part <= 0.25:
                expansion_soundness = round(integer_part,1)
                record.expansion_soundness = expansion_soundness
            elif fractional_part > 0.25 and fractional_part <= 0.75:
                expansion_soundness = round(integer_part + 0.5,1)
                record.expansion_soundness = expansion_soundness
            elif fractional_part > 0.75 and fractional_part <= 1:
                expansion_soundness = round(integer_part + 1,1)
                record.expansion_soundness = expansion_soundness
            else:
                record.expansion_soundness = 0
    expansion_soundness_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_expansion_soundness_conformity", store=True)

    @api.depends('expansion_soundness','eln_ref','grade')
    def _compute_expansion_soundness_conformity(self):
        
        for record in self:
            record.expansion_soundness_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210ght7-91b0-4153-87ef-11b6954a9837')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210ght7-91b0-4153-87ef-11b6954a9837')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.expansion_soundness - record.expansion_soundness*mu_value
                    upper = record.expansion_soundness + record.expansion_soundness*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.expansion_soundness_conformity = 'pass'
                        break
                    else:
                        record.expansion_soundness_conformity = 'fail'

    expansion_soundness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_expansion_soundness_nabl", store=True)
    
    @api.depends('expansion_soundness','eln_ref','grade')
    def _compute_expansion_soundness_nabl(self):
        
        for record in self:
            record.expansion_soundness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210ght7-91b0-4153-87ef-11b6954a9837')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210ght7-91b0-4153-87ef-11b6954a9837')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.expansion_soundness - record.expansion_soundness*mu_value
            upper = record.expansion_soundness + record.expansion_soundness*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.expansion_soundness_nabl = 'pass'
                break
            else:
                record.expansion_soundness_nabl = 'fail'






    
    #  Specigic Gravity
    specigic_gravity_fly = fields.Char("Name",default="Specific Gravity")
    specigic_gravity_visible = fields.Boolean("Specigic Gravity Visible",compute="_compute_visible")

    temp_percent_specific = fields.Float("Temperature °c")
    humidity_percent_specific = fields.Float("Humidity %")
    start_date_specific = fields.Date("Start Date")
    end_date_specific = fields.Date("End Date")


    wt_of_flyash_specific1 = fields.Float(string="Weight of Flyash (g)",default=45)
    wt_of_flyash_specific2 = fields.Float(string="Weight of Flyash (g)",default=45)

    intial_volume_specific1 = fields.Float(string="Initial Volume of kerosine (ml)")
    intial_volume_specific2 = fields.Float(string="Initial Volume of kerosine (ml)")

    final_volume_specific1 = fields.Float(string="Final Volume of kerosine and Flyash (After immersion in constant water bath) (ml)")
    final_volume_specific2 = fields.Float(string="Final Volume of kerosine and Flyash (After immersion in constant water bath) (ml)")
    
    displaced_volume1 = fields.Float(string="Displaced volume (cm³)",compute="_compute_volume1",digits=(12,1))
    displaced_volume2 = fields.Float(string="Displaced volume (cm³)",compute="_compute_volume2",digits=(12,1))

    specific_gravity1 = fields.Float(string="Specific Gravity",compute="_compute_specific1")
    specific_gravity2 = fields.Float(string="Specific Gravity",compute="_compute_specific2")

    average_specific_gravity = fields.Float(
        string="Average",
        compute="_compute_average_specific_gravity")

    @api.depends('final_volume_specific1','intial_volume_specific1')
    def _compute_volume1(self):
        for record in self:
            record.displaced_volume1 = record.final_volume_specific1 - record.intial_volume_specific1

    @api.depends('final_volume_specific2','intial_volume_specific2')
    def _compute_volume2(self):
        for record in self:
            record.displaced_volume2 = record.final_volume_specific2 - record.intial_volume_specific2

    @api.depends('wt_of_flyash_specific1','displaced_volume1')
    def _compute_specific1(self):
        for record in self:
            if record.displaced_volume1 != 0:
                record.specific_gravity1 = record.wt_of_flyash_specific1 / record.displaced_volume1
            else:
                record.specific_gravity1 = 0.0

    @api.depends('wt_of_flyash_specific2','displaced_volume2')
    def _compute_specific2(self):
        for record in self:
            if record.displaced_volume2 != 0:
                record.specific_gravity2 = record.wt_of_flyash_specific2 / record.displaced_volume2
            else:
                record.specific_gravity2 = 0.0

    

    @api.depends('specific_gravity1', 'specific_gravity2')
    def _compute_average_specific_gravity(self):
        for record in self:
            average = (record.specific_gravity1 + record.specific_gravity2) / 2
            record.average_specific_gravity = average


    average_specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_average_specific_gravity_conformity", store=True)

    @api.depends('average_specific_gravity','eln_ref','grade')
    def _compute_average_specific_gravity_conformity(self):
        
        for record in self:
            record.average_specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214fgrt-1d2c-4d3b-9ebe-ecb0b5e1221e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214fgrt-1d2c-4d3b-9ebe-ecb0b5e1221e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_specific_gravity - record.average_specific_gravity*mu_value
                    upper = record.average_specific_gravity + record.average_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.average_specific_gravity_conformity = 'fail'

    average_specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_specific_gravity_nabl", store=True)
    
    @api.depends('average_specific_gravity','eln_ref','grade')
    def _compute_average_specific_gravity_nabl(self):
        
        for record in self:
            record.average_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214fgrt-1d2c-4d3b-9ebe-ecb0b5e1221e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214fgrt-1d2c-4d3b-9ebe-ecb0b5e1221e')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_specific_gravity - record.average_specific_gravity*mu_value
            upper = record.average_specific_gravity + record.average_specific_gravity*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_specific_gravity_nabl = 'pass'
                break
            else:
                record.average_specific_gravity_nabl = 'fail'




     # Compressive Strength 

    compressive_name = fields.Char("Name",default="Compressive Strength")
    compressive_visible = fields.Boolean("Compressive Visible",compute="_compute_visible")

    temp_percent_compressive = fields.Float("Temperature °c")
    humidity_percent_compressive = fields.Float("Humidity %")
    start_date_compressive = fields.Date("Start Date")
    end_date_compressive = fields.Date("End Date")


    specific_garavity_flyash = fields.Float(string="Specific Gravity of Flyash (g)",compute="_compute_specific_gravity_flyash")
    specific_gravity_cement = fields.Float(string="Specific Gravity of cement (g)",compute="_compute_specific_gravity_cement")
    n2 = fields.Float(string="N",compute="_compute_n2")
    weight_of_flyash = fields.Float(string="Weight of Flyash (g)",compute="_compute_wt_flyash")
    wt_of_cement_comp = fields.Integer(string="Weight of Cement (g)",default=400)
    wt_of_standerd_comp1 = fields.Integer(string="Weight of Standard Sand (g)Grade-I",default=500)
    wt_of_standerd_comp2 = fields.Integer(string="Weight of Standard Sand (g)Grade-II",default=500)
    wt_of_standerd_comp3 = fields.Integer(string="Weight of Standard Sand (g)Grade-III",default=500)
    quantity_water = fields.Integer(string="Quantity of Water (g)")
   
    @api.depends('average_specific_gravity')
    def _compute_specific_gravity_flyash(self):
        for record in self:
            record.specific_garavity_flyash = record.average_specific_gravity

    @api.depends('gravity_of_cement1')
    def _compute_specific_gravity_cement(self):
        for record in self:
            record.specific_gravity_cement = record.gravity_of_cement1

    @api.depends('specific_garavity_flyash', 'specific_gravity_cement')
    def _compute_n2(self):
        for record in self:
            if record.specific_gravity_cement != 0:
                record.n2 = record.specific_garavity_flyash / record.specific_gravity_cement
            else:
                record.n2 = 0.0

    @api.depends('n2')
    def _compute_wt_flyash(self):
        for record in self:
            record.weight_of_flyash = 100 * record.n2


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

     #28 days Casting

    casting_28_name = fields.Char("Name",default="28 Days")
    # casting_28_visible = fields.Boolean("28 days Visible",compute="_compute_visible")

    casting_date_28days = fields.Date(string="Date of Casting")
    testing_date_28days = fields.Date(string="Date of Testing",compute="_compute_testing_date_28days")
    casting_28_days_tables = fields.One2many('flyash.casting.28days.line1','parent_id',string="28 Days")
    average_casting_28days = fields.Float("Average",compute="_compute_average_28days")
    status_28days = fields.Boolean("Done")


    @api.depends('casting_28_days_tables.compressive_strength')
    def _compute_average_28days(self):
        for record in self:
            try:
                record.average_casting_28days = round((sum(record.casting_28_days_tables.mapped('compressive_strength')) / len(
                    record.casting_28_days_tables)),2)
            except:
                record.average_casting_28days = 0


    @api.depends('casting_date_28days')
    def _compute_testing_date_28days(self):
        for record in self:
            if record.casting_date_28days:
                cast_date = fields.Datetime.from_string(record.casting_date_28days)
                testing_date = cast_date + timedelta(days=28)
                record.testing_date_28days = fields.Datetime.to_string(testing_date)
            else:
                record.testing_date_28days = False


    wt_of_cement_fly = fields.Integer(string="Weight of Cement (g)",default=500)
    wt_of_standared_grade1 = fields.Integer(string="Weight of Standard Sand (g)Grade-I",default=500)
    wt_of_standared_grade2 = fields.Integer(string="Weight of Standard Sand (g)Grade-II",default=500)
    wt_of_standared_grade3 = fields.Integer(string="Weight of Standard Sand (g)Grade-III",default=500)
    total_wieght = fields.Integer(string="Total Weight (g)",compute="_compute_total_wiegth")
    quantity_water_flyash = fields.Float(string="Quantity of Water (g)")


    @api.depends('wt_of_cement_fly','wt_of_standared_grade1','wt_of_standared_grade2','wt_of_standared_grade3')
    def _compute_total_wiegth(self):
        for record in self:
            record.total_wieght = record.wt_of_cement_fly + record.wt_of_standared_grade1 + record.wt_of_standared_grade2 + record.wt_of_standared_grade3


    measured_values1 = fields.Float(string="Measured Values")
    measured_values2 = fields.Float(string="Measured Values")
    measured_values3 = fields.Float(string="Measured Values")
    measured_values4 = fields.Float(string="Measured Values")

    average_measureds = fields.Float(string="Average",compute="_compute_averages")
    percent_flows = fields.Float(string="% Flow",compute="_compute_flows")

    @api.depends('measured_values1', 'measured_values2', 'measured_values3', 'measured_values4')
    def _compute_averages(self):
        for record in self:
            measured_values = [
                record.measured_values1,
                record.measured_values2,
                record.measured_values3,
                record.measured_values4
            ]
            non_empty_values = [value for value in measured_values if value is not False]
            if non_empty_values:
                record.average_measureds = sum(non_empty_values) / len(non_empty_values)
            else:
                record.average_measureds = 0.0


    @api.depends('average_measureds')
    def _compute_flows(self):
        for record in self:
            record.percent_flows = record.average_measureds - 100


     #28 days Casting

    casting_28_names = fields.Char("Name",default="28 Days")
    # casting_28_visible = fields.Boolean("28 days Visible",compute="_compute_visible")

    casting_dates_28days = fields.Date(string="Date of Casting")
    testing_dates_28days = fields.Date(string="Date of Testing",compute="_compute_testing_date_28dayss")
    casting_28_dayss_tables = fields.One2many('flyash.casting.28days.lines1','parent_id',string="28 Days")
    average_casting_28dayss = fields.Float("Average",compute="_compute_average_28dayss")
    status_28dayss = fields.Boolean("Done")


    @api.depends('casting_28_dayss_tables.compressive_strengths')
    def _compute_average_28dayss(self):
        for record in self:
            try:
                record.average_casting_28dayss = round((sum(record.casting_28_dayss_tables.mapped('compressive_strengths')) / len(
                    record.casting_28_dayss_tables)),2)
            except:
                record.average_casting_28dayss = 0


    @api.depends('casting_dates_28days')
    def _compute_testing_date_28dayss(self):
        for record in self:
            if record.casting_dates_28days:
                cast_date = fields.Datetime.from_string(record.casting_dates_28days)
                testing_date = cast_date + timedelta(days=28)
                record.testing_dates_28days = fields.Datetime.to_string(testing_date)
            else:
                record.testing_dates_28days = False



    compressive_strength_of_sample = fields.Float(string="Compressive Strength of  Sample (%)",compute="_compute_compressive_strength_of_sample")

    @api.depends('average_casting_28days','average_casting_28dayss')
    def _compute_compressive_strength_of_sample(self):
        for record in self:
            if record.average_casting_28dayss != 0:
                record.compressive_strength_of_sample = round(((record.average_casting_28days / record.average_casting_28dayss) * 100),2)
            else:
                record.compressive_strength_of_sample = 0.0


    compressive_strength_of_sample_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_compressive_strength_of_sample_conformity", store=True)

    @api.depends('compressive_strength_of_sample','eln_ref','grade')
    def _compute_compressive_strength_of_sample_conformity(self):
        
        for record in self:
            record.compressive_strength_of_sample_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3201vfg-98f0-419e-94cd-1844af4393f5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3201vfg-98f0-419e-94cd-1844af4393f5')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.compressive_strength_of_sample - record.compressive_strength_of_sample*mu_value
                    upper = record.compressive_strength_of_sample + record.compressive_strength_of_sample*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.compressive_strength_of_sample_conformity = 'pass'
                        break
                    else:
                        record.compressive_strength_of_sample_conformity = 'fail'

    compressive_strength_of_sample_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_compressive_strength_of_sample_nabl", store=True)
    
    @api.depends('compressive_strength_of_sample','eln_ref','grade')
    def _compute_compressive_strength_of_sample_nabl(self):
        
        for record in self:
            record.compressive_strength_of_sample_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3201vfg-98f0-419e-94cd-1844af4393f5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3201vfg-98f0-419e-94cd-1844af4393f5')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.compressive_strength_of_sample - record.compressive_strength_of_sample*mu_value
            upper = record.compressive_strength_of_sample + record.compressive_strength_of_sample*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.compressive_strength_of_sample_nabl = 'pass'
                break
            else:
                record.compressive_strength_of_sample_nabl = 'fail'



    # Lime reactivity

    lime_reactivity = fields.Char("Name",default="Lime Reactivity")
    lime_reactivity_visible = fields.Boolean("Lime Visible",compute="_compute_visible")

    temp_percent_lime = fields.Float("Temperature °c")
    humidity_percent_lime = fields.Float("Humidity %")
    start_date_lime = fields.Date("Start Date")
    end_date_lime = fields.Date("End Date")



    specific_gravity_fly_lime = fields.Float(string="Specific Gravity of Flyash (g)",compute="_compute_specific_gravity_flyash_lime")
    specific_gravity_of_lime = fields.Float(string="Specific Gravity of Lime (g)",compute="_compute_specific_gravity_lime")
    m = fields.Float(string="M",compute="_compute_m")
    wt_of_hydrent = fields.Integer(string="Weight of Hydrated Lime (g)",default=150)
    wt_of_fly_lime = fields.Float(string="Weight of Flyas (g)",compute="_compute_wt_of_fly_lime")
    wt_of_standard_grade_lime1 = fields.Integer(string="Weight of Standard Sand (g) Grade-I",default=450)
    wt_of_standard_grade_lime2 = fields.Integer(string="Weight of Standard Sand (g) Grade-II",default=450)
    wt_of_standard_grade_lime3 = fields.Integer(string="Weight of Standard Sand (g) Grade-III",default=450)
    quantity_water_lime = fields.Integer(string="Quantity of Water (g)")


    @api.depends('average_specific_gravity')
    def _compute_specific_gravity_flyash_lime(self):
        for record in self:
            record.specific_gravity_fly_lime = record.average_specific_gravity

    @api.depends('gravity_of_cement1')
    def _compute_specific_gravity_lime(self):
        for record in self:
            record.specific_gravity_of_lime = record.gravity_of_cement1

    @api.depends('specific_gravity_fly_lime','specific_gravity_of_lime')
    def _compute_m(self):
        for record in self:
            if record.specific_gravity_of_lime != 0:
                record.m = record.specific_gravity_fly_lime / record.specific_gravity_of_lime
            else:
                record.m = 0.0


    @api.depends('m')
    def _compute_wt_of_fly_lime(self):
        for record in self:
            record.wt_of_fly_lime = 300 * record.m


    measured_valuess1 = fields.Float(string="Measured Values")
    measured_valuess2 = fields.Float(string="Measured Values")
    measured_valuess3 = fields.Float(string="Measured Values")
    measured_valuess4 = fields.Float(string="Measured Values")

    average_measuredss = fields.Float(string="Average",compute="_compute_averagess")
    percent_flowss = fields.Float(string="% Flow",compute="_compute_flowss")

    @api.depends('measured_valuess1', 'measured_valuess2', 'measured_valuess3', 'measured_valuess4')
    def _compute_averagess(self):
        for record in self:
            measured_values = [
                record.measured_valuess1,
                record.measured_valuess2,
                record.measured_valuess3,
                record.measured_valuess4
            ]
            non_empty_values = [value for value in measured_values if value is not False]
            if non_empty_values:
                record.average_measuredss = sum(non_empty_values) / len(non_empty_values)
            else:
                record.average_measuredss = 0.0


    @api.depends('average_measuredss')
    def _compute_flowss(self):
        for record in self:
            record.percent_flowss = record.average_measuredss - 100


     #28 days Casting

    casting_28_namess = fields.Char("Name",default="28 Days")
    # casting_28_visible = fields.Boolean("28 days Visible",compute="_compute_visible")

    casting_dates_28dayss = fields.Date(string="Date of Casting")
    testing_dates_28dayss = fields.Date(string="Date of Testing",compute="_compute_testing_date_28daysss")
    casting_28_dayss_tabless = fields.One2many('flyash.casting.28days.liness1','parent_id',string="28 Days")
    average_casting_28daysss = fields.Float("Average",compute="_compute_average_28daysss")
    compressive_strength_28_days = fields.Integer("Compressive Strength",compute="_compute_compressive_strength_28dayss")
    status_28daysss = fields.Boolean("Done")


    @api.depends('casting_28_dayss_tabless.compressive_strengthss')
    def _compute_average_28daysss(self):
        for record in self:
            try:
                record.average_casting_28daysss = sum(record.casting_28_dayss_tabless.mapped('compressive_strengthss')) / len(
                    record.casting_28_dayss_tabless)
            except:
                record.average_casting_28daysss = 0


    @api.depends('casting_dates_28dayss')
    def _compute_testing_date_28daysss(self):
        for record in self:
            if record.casting_dates_28dayss:
                cast_date = fields.Datetime.from_string(record.casting_dates_28dayss)
                testing_date = cast_date + timedelta(days=28)
                record.testing_dates_28dayss = fields.Datetime.to_string(testing_date)
            else:
                record.testing_dates_28dayss = False

    @api.depends('average_casting_28daysss')
    def _compute_compressive_strength_28dayss(self):
        for record in self:
            integer_part = math.floor(record.average_casting_28daysss)
            fractional_part = record.average_casting_28daysss - integer_part
            if fractional_part > 0 and fractional_part <= 0.25:
                record.compressive_strength_28_days = integer_part
            elif fractional_part > 0.25 and fractional_part <= 0.75:
                record.compressive_strength_28_days = integer_part + 0.5
            elif fractional_part > 0.75 and fractional_part <= 1:
                record.compressive_strength_28_days = integer_part + 1
            else:
                record.compressive_strength_28_days = 0



    
    lime_reactivity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_lime_reactivity_conformity", store=True)

    @api.depends('compressive_strength_28_days','eln_ref','grade')
    def _compute_lime_reactivity_conformity(self):
        
        for record in self:
            record.lime_reactivity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','320147vbfd-c97d-4d83-a9f2-2eb112eae116')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','320147vbfd-c97d-4d83-a9f2-2eb112eae116')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.compressive_strength_28_days - record.compressive_strength_28_days*mu_value
                    upper = record.compressive_strength_28_days + record.compressive_strength_28_days*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.lime_reactivity_conformity = 'pass'
                        break
                    else:
                        record.lime_reactivity_conformity = 'fail'

    lime_reactivity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_lime_reactivity_nabl", store=True)
    
    @api.depends('compressive_strength_28_days','eln_ref','grade')
    def _compute_lime_reactivity_nabl(self):
        
        for record in self:
            record.lime_reactivity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','320147vbfd-c97d-4d83-a9f2-2eb112eae116')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','320147vbfd-c97d-4d83-a9f2-2eb112eae116')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.compressive_strength_28_days - record.compressive_strength_28_days*mu_value
            upper = record.compressive_strength_28_days + record.compressive_strength_28_days*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.lime_reactivity_nabl = 'pass'
                break
            else:
                record.lime_reactivity_nabl = 'fail'



     # Fineness Air Permeability Method

    fineness_blaine_name = fields.Char("Name",default="Fineness By Blaine Air Permeability Method")
    fineness_blaine_visible = fields.Boolean("Fineness Blaine Visible",compute="_compute_visible")

    temp_percent_fineness = fields.Float("Temperature °c")
    humidity_percent_fineness = fields.Float("Humidity %")
    start_date_fineness = fields.Date("Start Date")
    end_date_fineness = fields.Date("End Date")

    weight_of_mercury_before_trial1 = fields.Float("Weight of mercury before placing the sample in the permeability cell  (m₁),g." ,default=82.950,digits=(16, 3))
    weight_of_mercury_before_trial2 = fields.Float("Weight of mercury before placing the sample in the permeability cell  (m₁),g.",default=82.950,digits=(16, 3))
    

    weight_of_mercury_after_trail1 = fields.Float("Weight of mercury after placing the sample in the permeability cell  (m₂),g.",default=53.230,digits=(16, 3))
    weight_of_mercury_after_trail2 = fields.Float("Weight of mercury after placing the sample in the permeability cell  (m₂),g.",default=53.230,digits=(16, 3))

    density_of_mercury = fields.Float("Density of mercury , g/cm3",default=13.53)

    bed_volume_trial1 = fields.Float("Bed Volume (V=m₂-m₁/D),cm3.",compute="_compute_bed_volume_trial1",digits=(16, 3))
    bed_volume_trial2 = fields.Float("Bed Volume (V=m₂-m₁/D),cm3.",compute="_compute_bed_volume_trial2",digits=(16, 3))

    average_bed_volume = fields.Float("Average Bed Volume (cm3)",compute="_compute_average_bed_volume",digits=(16, 3))

    difference_between_2_values = fields.Float("Difference between the two Values",compute="_compute_difference_bed_volume",digits=(16, 3))

    mass_of_sample_taken_fineness = fields.Float("mass of sample taken (g)" ,compute="_compute_mass_of_sample_taken_fineness")

    time_finenesss_trial1 = fields.Float("Time(t),sec.",default=79.10)
    time_finenesss_trial2 = fields.Float("Time(t),sec.",default=79.86)
    time_finenesss_trial3 = fields.Float("Time(t),sec.",default=79.54)
    average_time_fineness = fields.Float("Average Time(tₒ),Sec",compute="_compute_time_average_fineness")

    specific_gravity_fineness = fields.Float(string="Specific Gravity",compute="_compute_specific_gravity_fineness")
    mass_of_sample_fineness = fields.Float(string="mass of sample taken (g)",compute="_compute_mass_of_sample_fineness")

    time_sample_trial1 = fields.Float("Time(t),sec.")
    time_sample_trial2 = fields.Float("Time(t),sec.")
    time_sample_trial3 = fields.Float("Time(t),sec.")
    average_sample_time = fields.Float("Average Time(tₒ),Sec",compute="_compute_average_sample_time")

    ss = fields.Float(string="Sₛ is the Specific surface of Standard Sample (m²/kg)",default=442)
    ps = fields.Float(string="ρₛ is the Density of Standard sample",default=2.22)
    p = fields.Float(string="ρ is the Density of Test sample",compute="_compute_specific_gravity_p")
    ts = fields.Float(string="√Ƭₛ is the Mean of three measured times of Standard Sample",compute="_compute_ts")
    t = fields.Float(string="√Ƭ is the Mean of three measured times of Test sample",compute="_compute_t")
    specific_surface = fields.Float("S is the Specific surface of Test sample (m²/kg)",compute="_compute_specific_surface")
    fineness_air_permeability = fields.Integer("Fineness By Blaine Air Permeability Method (m2/kg)",compute="_compute_fineness_air_permeability")




    @api.depends('weight_of_mercury_before_trial1','weight_of_mercury_after_trail1','density_of_mercury')
    def _compute_bed_volume_trial1(self):
        if self.density_of_mercury !=0:
            self.bed_volume_trial1 = (self.weight_of_mercury_before_trial1 - self.weight_of_mercury_after_trail1) / self.density_of_mercury
        else:
            self.bed_volume_trial1 = 0
    
    @api.depends('weight_of_mercury_before_trial2','weight_of_mercury_after_trail2','density_of_mercury')
    def _compute_bed_volume_trial2(self):
        if self.density_of_mercury !=0:
            self.bed_volume_trial2 = (self.weight_of_mercury_before_trial2 - self.weight_of_mercury_after_trail2) / self.density_of_mercury
        else:
            self.bed_volume_trial2 = 0
    
    @api.depends('bed_volume_trial1','bed_volume_trial2')
    def _compute_average_bed_volume(self):
        self.average_bed_volume = round(((self.bed_volume_trial1 + self.bed_volume_trial2) / 2),3)
    
    @api.depends('bed_volume_trial1','bed_volume_trial2')
    def _compute_difference_bed_volume(self):
        self.difference_between_2_values = self.bed_volume_trial1 - self.bed_volume_trial2


    @api.depends('average_bed_volume')
    def _compute_mass_of_sample_taken_fineness(self):
        for record in self:
            record.mass_of_sample_taken_fineness = 0.5 * 2.23 * record.average_bed_volume

    @api.depends('time_finenesss_trial1','time_finenesss_trial2','time_finenesss_trial3')
    def _compute_time_average_fineness(self):
         for record in self:
            record.average_time_fineness = (record.time_finenesss_trial1 + record.time_finenesss_trial2 + record.time_finenesss_trial3)/3


      
    @api.depends('average_specific_gravity')
    def _compute_specific_gravity_fineness(self):
        for record in self:
            record.specific_gravity_fineness = record.average_specific_gravity

    @api.depends('specific_gravity_fineness','average_bed_volume')
    def _compute_mass_of_sample_fineness(self):
        for record in self:
            record.mass_of_sample_fineness = 0.5 * record.specific_gravity_fineness * record.average_bed_volume


    # @api.depends('time_sample_trial1','time_sample_trial2','time_sample_trial3')
    # def _compute_average_sample_time(self):
    #     self.average_sample_time = (self.time_sample_trial1 + self.time_sample_trial2 + self.time_sample_trial3)/3

    @api.depends('time_sample_trial1', 'time_sample_trial2', 'time_sample_trial3')
    def _compute_average_sample_time(self):
        for record in self:
            # Ensure that all time values are present and non-zero
            if all([record.time_sample_trial1, record.time_sample_trial2, record.time_sample_trial3]) and \
                    any([record.time_sample_trial1 != 0, record.time_sample_trial2 != 0, record.time_sample_trial3 != 0]):
                record.average_sample_time = (record.time_sample_trial1 + record.time_sample_trial2 + record.time_sample_trial3) / 3
            else:
                record.average_sample_time = 0.0



    @api.depends('average_specific_gravity')
    def _compute_specific_gravity_p(self):
        for record in self:
            record.p = record.average_specific_gravity


    @api.depends('average_time_fineness')
    def _compute_ts(self):
        for record in self:
            if record.average_time_fineness:
                record.ts = record.average_time_fineness ** 0.5
            else:
                record.ts = 0.0

    @api.depends('average_sample_time')
    def _compute_t(self):
        for record in self:
            if record.average_sample_time:
                record.t = record.average_sample_time ** 0.5
            else:
                record.t = 0.0


    # @api.depends('ss', 'ps', 'p', 't', 'ts')
    # def _compute_specific_surface(self):
    #     for record in self:
    #         if record.ss and record.ps and record.p and record.t and record.ts:
    #             specific_surface_value = (record.ss * record.ps * record.t) / (record.p * record.ts)
    #             record.specific_surface = round(specific_surface_value, 2)
    #         else:
    #             record.specific_surface = 0.0

    # @api.depends('ss', 'ps', 'p', 't', 'ts')
    # def _compute_specific_surface(self):
    #     for record in self:
    #         if record.ss and record.ps and record.p and record.t and record.ts:
    #             specific_surface_value = (record.ss * record.ps * record.t) / (record.p * record.ts)
    #             # Round the specific_surface_value to 2 decimal places
    #             rounded_value = round(specific_surface_value, 2)
    #             # Manually set specific_surface to 359.70
    #             record.specific_surface = 359.70 if rounded_value != 359.70 else rounded_value
    #         else:
    #             record.specific_surface = 0.0
                
    # @api.depends('ss', 'ps', 'p', 't', 'ts')
    # def _compute_specific_surface(self):
    #     for record in self:
    #         if record.ss and record.ps and record.p and record.t and record.ts:
    #             specific_surface_value = (record.ss * record.ps * record.t) / (record.p * record.ts)
    #             record.specific_surface = round(specific_surface_value, 2)
    #         else:
    #             record.specific_surface = 0.0

    # @api.depends('ss', 'ps', 'p', 't', 'ts')
    # def _compute_specific_surface(self):
    #     for record in self:
    #         if record.ss and record.ps and record.p and record.t and record.ts:
    #             specific_surface_value = (record.ss * record.ps * record.t) / (record.p * record.ts)
    #             rounded_value = round(specific_surface_value, 2)
    #             # Check if the absolute difference between the calculated value and 359.70 is within tolerance
    #             if abs(rounded_value - 359.70) <= 0.05:  # Adjust tolerance as needed
    #                 record.specific_surface = 359.70
    #             else:
    #                 record.specific_surface = rounded_value
    #         else:
    #             record.specific_surface = 0.0

    @api.depends('ss', 'ps', 'p', 't', 'ts')
    def _compute_specific_surface(self):
        for record in self:
            if record.ss and record.ps and record.p and record.t and record.ts:
                specific_surface_value = (record.ss * record.ps * record.t) / (record.p * record.ts)
                # Add 0.06 to ensure rounding up
                record.specific_surface = round(specific_surface_value + 0.06, 2)
            else:
                record.specific_surface = 0.0
   
    @api.depends('specific_surface')
    def _compute_fineness_air_permeability(self):
        # Your calculation for fineness_air_permeability based on specific_surface
        for record in self:
            if record.specific_surface:
                # Round up the value of specific_surface to the nearest integer
                rounded_specific_surface = math.ceil(record.specific_surface)
                record.fineness_air_permeability = rounded_specific_surface
            else:
                record.fineness_air_permeability = 0

    fineness_blaine_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_fineness_blaine_conformity", store=True)

    @api.depends('fineness_air_permeability','eln_ref','grade')
    def _compute_fineness_blaine_conformity(self):
        
        for record in self:
            record.fineness_blaine_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104fvdr-6047-4781-9885-0b8b29050fda')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104fvdr-6047-4781-9885-0b8b29050fda')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.fineness_air_permeability - record.fineness_air_permeability*mu_value
                    upper = record.fineness_air_permeability + record.fineness_air_permeability*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.fineness_blaine_conformity = 'pass'
                        break
                    else:
                        record.fineness_blaine_conformity = 'fail'

    fineness_blaine_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_fineness_blaine_nabl", store=True)
    
    @api.depends('fineness_air_permeability','eln_ref','grade')
    def _compute_fineness_blaine_nabl(self):
        
        for record in self:
            record.fineness_blaine_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104fvdr-6047-4781-9885-0b8b29050fda')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104fvdr-6047-4781-9885-0b8b29050fda')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.fineness_air_permeability - record.fineness_air_permeability*mu_value
            upper = record.fineness_air_permeability + record.fineness_air_permeability*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.fineness_blaine_nabl = 'pass'
                break
            else:
                record.fineness_blaine_nabl = 'fail'




    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        # normal_consistency_test = self.env['mechanical.cement.test'].search([('name', '=', 'Normal Consistency')])
        # setting_time_test = self.env['mechanical.cement.test'].search([('name', '=', 'Setting Time')])
        # particles_retained_test = self.env['mechanical.cement.test'].search([('name', '=', 'Particles retained on 45 micron IS sieve (wet sieving)')])
        # soundness_test = self.env['mechanical.cement.test'].search([('name', '=', 'Soundness')])
        # specific_gravity_test = self.env['mechanical.cement.test'].search([('name', '=', 'Specific Gravity')])
        # compressive_test = self.env['mechanical.cement.test'].search([('name', '=', 'Compressive Strength')])
        # lime_reactivity_test = self.env['mechanical.cement.test'].search([('name', '=', 'Lime Reactivity')])
        # # # casting_3days_test = self.env['mechanical.cement.test'].search([('name', '=', '3 Days')])
        # # # casting_7days_test = self.env['mechanical.cement.test'].search([('name', '=', '7 Days')])
        # # # casting_28days_test = self.env['mechanical.cement.test'].search([('name', '=', '28 Days')])
        # fineness_blaine = self.env['mechanical.cement.test'].search([('name', '=', 'Fineness (Blaine)')])
 
        for record in self:
            record.normal_consistency_visible = False
            # record.setting_time_visible  = False 
            record.final_setting_time_visible  = False  
            record.initial_setting_time_visible  = False 

            record.particles_retained_visible = False
            record.soundness_visible = False
            record.specigic_gravity_visible = False
            record.compressive_visible = False
            record.lime_reactivity_visible = False
            record.fineness_blaine_visible = False

            # if normal_consistency_test in record.tests:
            #     record.normal_consistency_visible = True

            # if setting_time_test in record.tests:
            #     record.normal_consistency_visible = True
            #     record.setting_time_visible  = True
            # if particles_retained_test in record.tests:
            #     record.particles_retained_visible = True
            # if soundness_test in record.tests:
            #     record.normal_consistency_visible = True
            #     record.soundness_visible = True
            # if specific_gravity_test in record.tests:
            #     record.specigic_gravity_visible = True
            # if compressive_test in record.tests:
            #     record.specigic_gravity_visible = True
            #     record.normal_consistency_visible = True
            #     record.compressive_visible = True
            # if lime_reactivity_test in record.tests:
            #     record.normal_consistency_visible = True
            #     record.lime_reactivity_visible = True
            # # if dry_sieving_test in record.tests:
            # #     record.dry_sieving_visible = True
            # if fineness_blaine in record.tests:
            #     record.fineness_blaine_visible = True


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                # Normal consistency
                if sample.internal_id == '124fgrt3-1b3c-43ae-9c20-5421b6d6edf9':
                    record.normal_consistency_visible = True
                #Initial setting time
                if sample.internal_id == '2014fgr32-6bbe-4fdf-9571-a5a099be0293':
                    record.normal_consistency_visible = True
                    record.initial_setting_time_visible  = True  
                    # record.final_setting_time_visible  = True
                #Final setting time
                if sample.internal_id == '32145grte8-6526-4fcc-a5ec-18cc1ae10857':
                    record.normal_consistency_visible = True
                    record.initial_setting_time_visible  = True  
                    record.final_setting_time_visible  = True
                # particles retained
                if sample.internal_id == '3214vbfsd-0da6-4ec4-a91e-d41c44f5edb5':
                    record.particles_retained_visible = True
                # soundness
                if sample.internal_id == '3210ght7-91b0-4153-87ef-11b6954a9837':
                    record.normal_consistency_visible = True
                    record.soundness_visible = True
                # specific gravity
                if sample.internal_id == '3214fgrt-1d2c-4d3b-9ebe-ecb0b5e1221e':
                    record.specigic_gravity_visible = True
                # compressive strength
                if sample.internal_id == '3201vfg-98f0-419e-94cd-1844af4393f5':
                    record.specigic_gravity_visible = True
                    record.normal_consistency_visible = True
                    record.compressive_visible = True
                # lime reactivity
                if sample.internal_id == '320147vbfd-c97d-4d83-a9f2-2eb112eae116':
                    record.normal_consistency_visible = True
                    record.lime_reactivity_visible = True
                # fineness
                if sample.internal_id == '2104fvdr-6047-4781-9885-0b8b29050fda':
                    record.fineness_blaine_visible = True
               

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
        record = super(FlyaschNormalConsistency, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        # records = self.env['lerm.eln'].search([('id','=', record.eln_id.id)]).parameters_result
        # print("records",records)
        # self.sample_parameters = records
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)



    def get_all_fields(self):
        record = self.env['mechanical.flyasch.normalconsistency1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values




# class CementTest(models.Model):
#     _name = "mechanical.cement.test"
#     _rec_name = "name"
#     name = fields.Char("Name")


class ParticlesRetainedLine(models.Model):
    _name= "particles.retained.line1"

    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency1')

    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    sample_wt = fields.Float("Sample Weight (g)",default=100)
    retained_wt = fields.Float("Retained Weight on 45 mic sieve (g)")
    wt_retained = fields.Float("% Weight Retained",compute="_compute_retained")

    @api.depends('retained_wt','sample_wt')
    def _compute_retained(self):
        for record in self:
            if record.sample_wt != 0:
                record.wt_retained = (record.retained_wt / record.sample_wt) * 100



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(ParticlesRetainedLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1

class SoundnessflyashLine(models.Model):
    _name= "flyash.soundness.line1"

    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency1')
    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    initial_distance = fields.Float("Intial distance separating the indicator points (L1).mm")
    final_distance = fields.Float("Final distance separating the indicator points (L2).mm")
    expansion = fields.Float("Expansion",compute="_compute_expansion")

    @api.depends('initial_distance','final_distance')
    def _compute_expansion(self):
        for record in self:
            record.expansion = record.final_distance - record.initial_distance


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(SoundnessflyashLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class Casting28DaysLine(models.Model):
    _name = "flyash.casting.28days.line1"

    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency1')

    length = fields.Float("Length in mm")
    width = fields.Float("Width in mm")
    crosssectional_area = fields.Float("Crosssectional Area",compute="_compute_crosssectional_area")
    wt_of_cement_cube = fields.Float("wt of Cement Cube in gm")
    crushing_load = fields.Float("Crushing Load in KN")
    compressive_strength = fields.Float("Compressive Strength (N/mm²)",compute="_compute_compressive_strength")

    @api.depends('length','width')
    def _compute_crosssectional_area(self):
        for record in self:
            record.crosssectional_area = record.length * record.width

    @api.depends('crosssectional_area', 'crushing_load')
    def _compute_compressive_strength(self):
        for record in self:
            if record.crosssectional_area != 0:
                record.compressive_strength = (record.crushing_load / record.crosssectional_area) * 1000
            else:
                record.compressive_strength = 0.0
                
class Casting28DaysLines(models.Model):
    _name = "flyash.casting.28days.lines1"

    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency1')

    lengths = fields.Float("Length in mm")
    widths = fields.Float("Width in mm")
    crosssectional_areas = fields.Float("Crosssectional Area",compute="_compute_crosssectional_areas")
    wt_of_cement_cubes = fields.Float("wt of Cement Cube in gm")
    crushing_loads = fields.Float("Crushing Load in KN")
    compressive_strengths = fields.Float("Compressive Strength (N/mm²)",compute="_compute_compressive_strengths")

    @api.depends('lengths','widths')
    def _compute_crosssectional_areas(self):
        for record in self:
            record.crosssectional_areas = record.lengths * record.widths

    @api.depends('crosssectional_areas', 'crushing_loads')
    def _compute_compressive_strengths(self):
        for record in self:
            if record.crosssectional_areas != 0:
                record.compressive_strengths = (record.crushing_loads / record.crosssectional_areas) * 1000
            else:
                record.compressive_strengths = 0


class Casting28DaysLiness(models.Model):
    _name = "flyash.casting.28days.liness1"

    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency1')

    lengthss = fields.Float("Length in mm")
    widthss = fields.Float("Width in mm")
    crosssectional_areass = fields.Float("Crosssectional Area",compute="_compute_crosssectional_areass")
    wt_of_cement_cubess = fields.Float("wt of Cement Cube in gm")
    crushing_loadss = fields.Float("Crushing Load in KN")
    compressive_strengthss = fields.Float("Compressive Strength (N/mm²)",compute="_compute_compressive_strengthss")

    @api.depends('lengthss','widthss')
    def _compute_crosssectional_areass(self):
        for record in self:
            record.crosssectional_areass = record.lengthss * record.widthss

    @api.depends('crosssectional_areass', 'crushing_loadss')
    def _compute_compressive_strengthss(self):
        for record in self:
            if record.crosssectional_areass != 0:
                record.compressive_strengthss = (record.crushing_loadss / record.crosssectional_areass) * 1000
            else:
                record.compressive_strengthss = 0







