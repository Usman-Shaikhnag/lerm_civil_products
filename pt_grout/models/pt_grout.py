from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math



class PtGrout(models.Model):
    _name = "mechanical.pt.grout1"
    _inherit = "lerm.eln"
    _description = 'mechanical.pt.grout1'
    _rec_name = "name_fly"


    name_fly = fields.Char("Name",default="PT Grout")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        # records = self.env['lerm.eln'].sudo().search([('id','=', record.eln_id.id)]).parameters_result
        # print("records",records)
        # self.sample_parameters = records
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    eln_ref = fields.Many2one('lerm.eln',string="Eln")

    temp_percent_fluidity = fields.Float("Temperature °c")
    humidity_percent_fludity = fields.Float("Humidity %")


    tests = fields.Many2many("mechanical.grout.test1",string="Tests")

    # Fluidity

    fluidity_name = fields.Char("Name",default="Fluidity")
    fludity_visible = fields.Boolean("Fluidity Visible",compute="_compute_visible")
    start_date_fludity = fields.Date("Start Date")
    end_date_fludity = fields.Date("End Date")

    water_cement_ratio = fields.Float(string="Water Cement Ratio (w/c)",compute="_compute_ratio")
    wt_of_cement = fields.Float(string="Wt. of Cement (g)")
    wt_of_water = fields.Float(string="Wt.of water (g)")
    cebex = fields.Float(string="CEBEX 100 (g)")
    water_temperature = fields.Float(string="Water Temperature °c")
    grout_temperature = fields.Float(string="Grout Temperature °c")
    flow_sec = fields.Float(string="Flow (Sec)")


    @api.depends('wt_of_water', 'wt_of_cement')
    def _compute_ratio(self):
        for record in self:
            if record.wt_of_cement != 0:
                record.water_cement_ratio = record.wt_of_water / record.wt_of_cement
            else:
                record.water_cement_ratio = 0.

    fludity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')],string="NABL",compute="_compute_fluidity_nabl",store=True)



    @api.depends('water_cement_ratio','eln_ref')
    def _compute_fluidity_nabl(self):
        
        for record in self:
            record.fludity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321457gr-331a-4e71-8887-ef37cf38c7dd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321457gr-331a-4e71-8887-ef37cf38c7dd')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.water_cement_ratio - record.water_cement_ratio*mu_value
                    upper = record.water_cement_ratio + record.water_cement_ratio*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.fludity_nabl = 'pass'
                        break
                    else:
                        record.fludity_nabl = 'fail'




                        
     #Initial setting Time
    initial_setting_time_visible = fields.Boolean("Initial Setting Time Visible",compute="_compute_visible")
    initial_setting_time_name = fields.Char("Name",default="Initial Setting Time")

    setting_time_name = fields.Char("Name",default="Setting Time")
    time_water_added = fields.Datetime("The Time When water is added to cement (t1)")
    time_needle_fails = fields.Datetime("The time at which needle fails to penetrate the test block to a point 5 ± 0.5 mm (t2)")
    initial_setting_time_hours = fields.Char("Initial Setting Time (t2-t1) (Hours)",compute="_compute_initial_setting_time")
    initial_setting_time_minutes = fields.Char("Initial Setting Time Rounded",compute="_compute_initial_setting_time")
    initial_setting_time_minutes_unrounded = fields.Char("Initial Setting Time",compute="_compute_initial_setting_time")

    initial_setting_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_initial_setting_conformity")

    initial_setting_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='NABL',compute="_compute_initial_setting_nabl")


    @api.depends('initial_setting_time_minutes_unrounded','eln_ref','grade')
    def _compute_initial_setting_conformity(self):
        for record in self:
            record.initial_setting_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21047gfds1-7350-4597-8057-139ef15f07fe')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21047gfds1-7350-4597-8057-139ef15f07fe')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21047gfds1-7350-4597-8057-139ef15f07fe')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21047gfds1-7350-4597-8057-139ef15f07fe')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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
    final_setting_time_minutes = fields.Char("Final Setting Time Rounded",compute="_compute_final_setting_time")
    final_setting_time_minutes_unrounded = fields.Char("Final Setting Time",compute="_compute_final_setting_time")

    final_setting_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_final_setting_conformity")

    final_setting_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='NABL',compute="_compute_final_setting_nabl")


    @api.depends('final_setting_time_minutes_unrounded','eln_ref','grade')
    def _compute_final_setting_conformity(self):
        for record in self:
            record.final_setting_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214758bgfd-5cad-4cbe-a6f5-1cee158d2d0e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214758bgfd-5cad-4cbe-a6f5-1cee158d2d0e')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214758bgfd-5cad-4cbe-a6f5-1cee158d2d0e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214758bgfd-5cad-4cbe-a6f5-1cee158d2d0e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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
                        
    @api.depends('time_needle_make_impression')
    def _compute_final_setting_time(self):
        for record in self:
            if record.time_needle_make_impression and record.time_water_added:
                t1 = record.time_water_added
                t2 = record.time_needle_make_impression
                time_difference = t2 - t1

                # Convert time difference to seconds and then to minutes
                final_setting_time_minutes = time_difference.total_seconds() / 60

                final_setting_time_hours = time_difference.total_seconds() / 3600
                time_delta = timedelta(hours=final_setting_time_hours)

                # Format the time in a similar way as initial_setting_time_hours
                record.final_setting_time_hours = "{:0}:{:02}".format(int(time_delta.total_seconds() // 3600), int((time_delta.total_seconds() % 3600) // 60))

                if final_setting_time_minutes % 5 == 0:
                    record.final_setting_time_minutes = final_setting_time_minutes
                else:
                    record.final_setting_time_minutes = round(final_setting_time_minutes / 5) * 5

                record.final_setting_time_minutes_unrounded = final_setting_time_minutes
            else:
                record.final_setting_time_hours = False
                record.final_setting_time_minutes = False
                record.final_setting_time_minutes_unrounded = False



    


    




    # Bleeding
    bleeding_name = fields.Char("Name",default="Bleeding")
    bleeding_visible = fields.Boolean("Bleeding Visible",compute="_compute_visible")

    temp_percent_bleeding = fields.Float("Temperature °c")
    humidity_percent_bleeding = fields.Float("Humidity %")
    start_date_bleeding = fields.Date("Start Date")
    end_date_bleeding = fields.Date("End Date")

    vl_sample = fields.Float(string="Volume of sample at begning of test (mL)")
    vl_decanted = fields.Float(string="Volume of decanted bleed water (mL)")

    final_bleeding = fields.Float(string="Final Bleeding %",compute="_compute_final_bleeding")

    bleeding_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_bleeding_confirmity_confirmity")

    # bleedin_nabl_pt = fields.Selection([
    #     ('pass', 'NABL'),
    #     ('fail', 'Non-NABL')],default='NABL',compute="_compute_bleedin1_nabl",store=True)


    @api.depends('final_bleeding','eln_ref')
    def _compute_bleeding_confirmity_confirmity(self):
        for record in self:
            record.bleeding_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104789gfrty-9b4f-4025-b34c-75a33149cc6f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104789gfrty-9b4f-4025-b34c-75a33149cc6f')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.final_bleeding - record.final_bleeding*mu_value
                    upper = record.final_bleeding + record.final_bleeding*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.bleeding_confirmity = 'pass'
                        break
                    else:
                        record.bleeding_confirmity = 'fail'


    bleeding_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')],string="NABL",compute="_compute_bleeding_nabl",store=True)



    @api.depends('final_bleeding','eln_ref')
    def _compute_bleeding_nabl(self):
        
        for record in self:
            record.bleeding_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104789gfrty-9b4f-4025-b34c-75a33149cc6f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104789gfrty-9b4f-4025-b34c-75a33149cc6f')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.final_bleeding - record.final_bleeding*mu_value
                    upper = record.final_bleeding + record.final_bleeding*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.bleeding_nabl = 'pass'
                        break
                    else:
                        record.bleeding_nabl = 'fail'


    @api.depends('vl_decanted', 'vl_sample')
    def _compute_final_bleeding(self):
        for record in self:
            if record.vl_sample != 0:
                record.final_bleeding = (record.vl_decanted / record.vl_sample) * 100
            else:
                record.final_bleeding = 0.


    bleeding_table = fields.One2many('bleeding.line1','parent_id',string="Bleeding")


    # Volume Change

    volume_change_name = fields.Char("Name",default="Volume Change")
    volume_change_visible = fields.Boolean("Volume Change Visible",compute="_compute_visible")

    temp_percent_volume_change = fields.Float("Temperature °c")
    humidity_percent_volume_change = fields.Float("Humidity %")
    start_date_volume_change = fields.Date("Start Date")
    end_date_volume_change = fields.Date("End Date")
    thickness_of_glass_plate = fields.Float("Thickness of Glass Plate")
    volume_change_table = fields.One2many('volume.change.line1','parent_id',string="Height Change")

    height_change_average = fields.Float("Average Height Change", compute="_compute_height_change_average")

    volume_change_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_volume_change_confirmity")

  

    @api.depends('height_change_average','eln_ref')
    def _compute_volume_change_confirmity(self):
        for record in self:
            record.volume_change_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','456hgf45h-2c21-4a5d-beb8-366c6a3e4b93')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','456hgf45h-2c21-4a5d-beb8-366c6a3e4b93')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.height_change_average - record.height_change_average*mu_value
                    upper = record.height_change_average + record.height_change_average*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.volume_change_confirmity = 'pass'
                        break
                    else:
                        record.volume_change_confirmity = 'fail'

    volume_nabl_1 = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')],string="NABL",compute="_compute_volume_nabl_1",store=True)



    @api.depends('height_change_average','eln_ref')
    def _compute_volume_nabl_1(self):
        
        for record in self:
            record.volume_nabl_1 = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','456hgf45h-2c21-4a5d-beb8-366c6a3e4b93')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','456hgf45h-2c21-4a5d-beb8-366c6a3e4b93')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.height_change_average - record.height_change_average*mu_value
                    upper = record.height_change_average + record.height_change_average*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.volume_nabl_1 = 'pass'
                        break
                    else:
                        record.volume_nabl_1 = 'fail'


    @api.depends('volume_change_table.height_change')
    def _compute_height_change_average(self):
        for record in self:
            height_changes = record.volume_change_table.mapped('height_change')
            if height_changes:
                average_height_change = sum(height_changes) / len(height_changes)
                record.height_change_average = average_height_change
            else:
                record.height_change_average = 0.0

    #  Compressive Strength

    compressive_strength_name = fields.Char("Name",default="Compressive Strength")
    compressive_strength_visible = fields.Boolean("Compressive Strength Visible",compute="_compute_visible")
    start_date_compressive_strength = fields.Date("Start Date")
    end_date_compressive_strength = fields.Date("End Date")
    temp_percent_compressive = fields.Float("Temperature °c")
    humidity_percent_compressive = fields.Float("Humidity %")


    water_cement_ratio_1 = fields.Float(string="Water Cement Ratio (w/c)",compute="_compute_ratio_1")
    wt_of_cement_1 = fields.Float(string="Wt. of Cement (g)")
    wt_of_water_1 = fields.Float(string="Wt.of water (g)")
    cebex_1 = fields.Float(string="CEBEX 100 (g)")
    water_temperature_1 = fields.Float(string="Water Temperature °c")
    grout_temperature_1 = fields.Float(string="Grout Temperature °c")


    compressive_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')],string="NABL",compute="_compute_volume_nabl",store=True)



    @api.depends('water_cement_ratio_1','eln_ref')
    def _compute_volume_nabl(self):
        
        for record in self:
            record.compressive_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24578hgrt-39e1-4ca3-8c9d-f28fb1f9b12e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24578hgrt-39e1-4ca3-8c9d-f28fb1f9b12e')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.water_cement_ratio_1 - record.water_cement_ratio_1*mu_value
                    upper = record.water_cement_ratio_1 + record.water_cement_ratio_1*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.compressive_strength_nabl = 'pass'
                        break
                    else:
                        record.compressive_strength_nabl = 'fail'



    @api.depends('wt_of_water_1', 'wt_of_cement_1')
    def _compute_ratio_1(self):
        for record in self:
            if record.wt_of_cement_1 != 0:
                record.water_cement_ratio_1 = record.wt_of_water_1 / record.wt_of_cement_1
            else:
                record.water_cement_ratio_1 = 0.0

     #7 days Casting

    casting_7_name = fields.Char("Name",default="7 Days")
    # casting_28_visible = fields.Boolean("28 days Visible",compute="_compute_visible")

    casting_date_7days = fields.Date(string="Date of Casting")
    testing_date_7days = fields.Date(string="Date of Testing",compute="_compute_testing_date_7days")
    casting_7_days_tables = fields.One2many('grout.casting.7days.line1','parent_id',string="7 Days")
    average_casting_7days = fields.Float("Average",compute="_compute_average_7days")
    compressive_strength_7_days = fields.Float("Compressive Strength",compute="_compute_compressive_strength_7days")
    status_7days = fields.Boolean("Done")

    compressive_strength_7days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_compressive_strength_7days_confirmity")

  

    @api.depends('compressive_strength_7_days','eln_ref')
    def _compute_compressive_strength_7days_confirmity(self):
        for record in self:
            record.compressive_strength_7days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24578hgrt-39e1-4ca3-8c9d-f28fb1f9b12e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24578hgrt-39e1-4ca3-8c9d-f28fb1f9b12e')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.compressive_strength_7_days - record.compressive_strength_7_days*mu_value
                    upper = record.compressive_strength_7_days + record.compressive_strength_7_days*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.compressive_strength_7days_confirmity = 'pass'
                        break
                    else:
                        record.compressive_strength_7days_confirmity = 'fail'

    # @api.depends('compressive_strength_7_days','eln_ref')
    # def compressive_strength_7days_nabl_1(self):
        
    #     for record in self:
    #         record.compressive_strength_7days_nabl_pt = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24578hgrt-39e1-4ca3-8c9d-f28fb1f9b12e')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24578hgrt-39e1-4ca3-8c9d-f28fb1f9b12e')]).parameter_table
    #         for material in materials:
    #             # if material.grade.id == record.grade.id:
    #                 lab_min = line.lab_min_value
    #                 lab_max = line.lab_max_value
    #                 mu_value = line.mu_value
                    
    #                 lower = record.compressive_strength_7_days - record.compressive_strength_7_days*mu_value
    #                 upper = record.compressive_strength_7_days + record.compressive_strength_7_days*mu_value
    #                 if lower >= lab_min and upper <= lab_max:
    #                     record.compressive_strength_7days_nabl_pt = 'pass'
    #                     break
    #                 else:
    #                     record.compressive_strength_7days_nabl_pt = 'fail'
    days7_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')],string="NABL",compute="_compute_days7_nabl",store=True)



    @api.depends('compressive_strength_7_days','eln_ref')
    def _compute_days7_nabl(self):
        
        for record in self:
            record.days7_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24578hgrt-39e1-4ca3-8c9d-f28fb1f9b12e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24578hgrt-39e1-4ca3-8c9d-f28fb1f9b12e')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.compressive_strength_7_days - record.compressive_strength_7_days*mu_value
                    upper = record.compressive_strength_7_days + record.compressive_strength_7_days*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.days7_nabl = 'pass'
                        break
                    else:
                        record.days7_nabl = 'fail'



    @api.depends('casting_7_days_tables.compressive_strength')
    def _compute_average_7days(self):
        for record in self:
            try:
                record.average_casting_7days = sum(record.casting_7_days_tables.mapped('compressive_strength')) / len(
                    record.casting_7_days_tables)
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


    #28 days Casting

    casting_28_name = fields.Char("Name",default="28 Days")
    # casting_28_visible = fields.Boolean("28 days Visible",compute="_compute_visible")

    casting_date_28days = fields.Date(string="Date of Casting")
    testing_date_28days = fields.Date(string="Date of Testing",compute="_compute_testing_date_28days")
    casting_28_days_tables = fields.One2many('grout.casting.28days.line1','parent_id',string="28 Days")
    average_casting_28days = fields.Float("Average",compute="_compute_average_28days")
    compressive_strength_28_days = fields.Float("Compressive Strength",compute="_compute_compressive_strength_28days")
    status_28days = fields.Boolean("Done")

    compressive_strength_28days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_compressive_strength_28days_confirmity")

  

    @api.depends('compressive_strength_28_days','eln_ref')
    def _compute_compressive_strength_28days_confirmity(self):
        for record in self:
            record.compressive_strength_28days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24578hgrt-39e1-4ca3-8c9d-f28fb1f9b12e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24578hgrt-39e1-4ca3-8c9d-f28fb1f9b12e')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.compressive_strength_28_days - record.compressive_strength_28_days*mu_value
                    upper = record.compressive_strength_28_days + record.compressive_strength_28_days*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.compressive_strength_28days_confirmity = 'pass'
                        break
                    else:
                        record.compressive_strength_28days_confirmity = 'fail'

    # @api.depends('compressive_strength_28_days','eln_ref')
    # def compressive_strength_28days_nabl_1(self):
        
    #     for record in self:
    #         record.compressive_strength_28days_nabl_pt = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24578hgrt-39e1-4ca3-8c9d-f28fb1f9b12e')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24578hgrt-39e1-4ca3-8c9d-f28fb1f9b12e')]).parameter_table
    #         for material in materials:
    #             # if material.grade.id == record.grade.id:
    #                 lab_min = line.lab_min_value
    #                 lab_max = line.lab_max_value
    #                 mu_value = line.mu_value
                    
    #                 lower = record.compressive_strength_28_days - record.compressive_strength_28_days*mu_value
    #                 upper = record.compressive_strength_28_days + record.compressive_strength_28_days*mu_value
    #                 if lower >= lab_min and upper <= lab_max:
    #                     record.compressive_strength_28days_nabl_pt = 'pass'
    #                     break
    #                 else:
    #                     record.compressive_strength_28days_nabl_pt = 'fail'
    days28_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')],string="NABL",compute="_compute_days28_nabl",store=True)



    @api.depends('compressive_strength_28_days','eln_ref')
    def _compute_days28_nabl(self):
        
        for record in self:
            record.days28_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24578hgrt-39e1-4ca3-8c9d-f28fb1f9b12e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24578hgrt-39e1-4ca3-8c9d-f28fb1f9b12e')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.compressive_strength_28_days - record.compressive_strength_28_days*mu_value
                    upper = record.compressive_strength_28_days + record.compressive_strength_28_days*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.days28_nabl = 'pass'
                        break
                    else:
                        record.days28_nabl = 'fail'


    @api.depends('casting_28_days_tables.compressive_strength')
    def _compute_average_28days(self):
        for record in self:
            try:
                record.average_casting_28days = sum(record.casting_28_days_tables.mapped('compressive_strength')) / len(
                    record.casting_28_days_tables)
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

    @api.depends('average_casting_28days')
    def _compute_compressive_strength_28days(self):
        for record in self:
            integer_part = math.floor(record.average_casting_28days)
            fractional_part = record.average_casting_28days - integer_part
            if fractional_part > 0 and fractional_part <= 0.25:
                record.compressive_strength_28_days = integer_part
            elif fractional_part > 0.25 and fractional_part <= 0.75:
                record.compressive_strength_28_days = integer_part + 0.5
            elif fractional_part > 0.75 and fractional_part <= 1:
                record.compressive_strength_28_days = integer_part + 1
            else:
                record.compressive_strength_28_days = 0













    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        # fluidity_test = self.env['mechanical.grout.test'].sudo().search([('name', '=', 'Fluidity')])
        # setting_time_test = self.env['mechanical.grout.test'].sudo().search([('name', '=', 'Setting Time')])
        # bleeding_test = self.env['mechanical.grout.test'].sudo().search([('name', '=', 'Bleeding')])
        # volume_change_test = self.env['mechanical.grout.test'].sudo().search([('name', '=', 'Volume Change')])
        # compressive_strength_test = self.env['mechanical.grout.test'].sudo().search([('name', '=', 'Compressive Strength')])

        for record in self:
            record.fludity_visible = False
            record.initial_setting_time_visible = False
            record.final_setting_time_visible = False
            record.bleeding_visible = False
            record.volume_change_visible = False
            record.compressive_strength_visible = False

            # if fluidity_test in record.tests:
            #     record.fludity_visible = True
            # if setting_time_test in record.tests:
            #     record.setting_time_visible = True
            # if bleeding_test in record.tests:
            #     record.bleeding_visible = True
            # if volume_change_test in record.tests:
            #     record.volume_change_visible = True
            # if compressive_strength_test in record.tests:
            #     record.compressive_strength_visible = True
               
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                # Fluidity 
                if sample.internal_id == '321457gr-331a-4e71-8887-ef37cf38c7dd':
                    record.fludity_visible = True
                # Setting Time 
                if sample.internal_id == '21047gfds1-7350-4597-8057-139ef15f07fe':
                    record.initial_setting_time_visible = True
                if sample.internal_id == '214758bgfd-5cad-4cbe-a6f5-1cee158d2d0e':
                    record.final_setting_time_visible = True
                # Bleeding 
                if sample.internal_id == '2104789gfrty-9b4f-4025-b34c-75a33149cc6f':
                    record.bleeding_visible = True
                # Volume Change 
                if sample.internal_id == '456hgf45h-2c21-4a5d-beb8-366c6a3e4b93':
                    record.volume_change_visible = True
                # Compressive Strength 
                if sample.internal_id == '24578hgrt-39e1-4ca3-8c9d-f28fb1f9b12e':
                    record.compressive_strength_visible = True

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
        record = super(PtGrout, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

        
    def get_all_fields(self):
        record = self.env['mechanical.pt.grout1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values





class GgbsTest(models.Model):
    _name = "mechanical.grout.test1"
    _rec_name = "name"
    name = fields.Char("Name")


class BleedingLine(models.Model):
    _name= "bleeding.line1"

    parent_id = fields.Many2one('mechanical.pt.grout1')

    test = fields.Char(string="Test")
    vl_of_sample = fields.Float("Volume of sample at pescribed intervals measured at upper surface of water layer (mL)")
    vl_of_grout = fields.Float("Volume of grout portion of sample at prescribed intervals at upper surface of grout (mL)")
    bleeding_precent = fields.Float("Bleeding %",compute="_compute_bleeding_percent")

    @api.depends('vl_of_sample', 'vl_of_grout', 'parent_id.vl_sample')
    def _compute_bleeding_percent(self):
        for record in self:
            if record.parent_id.vl_sample != 0:
                bleeding_percent = ((record.vl_of_sample - record.vl_of_grout) / record.parent_id.vl_sample) * 100
                record.bleeding_precent = bleeding_percent
            else:
                record.bleeding_precent = 0.0


class VolumeChangeLine(models.Model):
    _name= "volume.change.line1"

    parent_id = fields.Many2one('mechanical.pt.grout1')

    initial_reading = fields.Float(string="INITIAL READING AT  24±1⁄2")
    days_3 = fields.Float("3 days± 1 h")
    days_14 = fields.Float("14 days± 6 h")
    days_28 = fields.Float("28 days± 12 h")
    height = fields.Float("H = Height 152 mm")
    height_change = fields.Float("V= Height Change",compute="_compute_height_change")

    @api.depends('initial_reading', 'days_28', 'height','parent_id.thickness_of_glass_plate')
    def _compute_height_change(self):
        for record in self:
            if record.height != 0:
                height_change = ((record.parent_id.thickness_of_glass_plate + record.initial_reading - record.days_28) / record.height) * 100
                record.height_change = height_change
            else:
                record.height_change = 0.0


class Casting7DaysLine(models.Model):
    _name = "grout.casting.7days.line1"

    parent_id = fields.Many2one('mechanical.pt.grout1')

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
                

class Casting28DaysLine(models.Model):
    _name = "grout.casting.28days.line1"

    parent_id = fields.Many2one('mechanical.pt.grout1')

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
                record.compressive_strength = 0