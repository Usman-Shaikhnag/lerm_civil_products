from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class CementPsc(models.Model):
    _name = "mechanical.cement.psc"
    _inherit = "lerm.eln"
    _rec_name = "name"


    name = fields.Char("Name",default="Cement")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    notes_id = fields.One2many('psc.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(CementPsc, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The Test Report(s) is/are valid only to the sample submitted to the laboratory.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'Sample(s) was/were not drawn by laboratory.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'This Report may not be reproduced in except full/ part without the permission of the Lab Head of the Laboratory.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': '# - Information provided by the customer.',
            }),
        ]

        res['notes_id'] = default_notes
        return res


    temp_percent_normal = fields.Float("Temperature °C",digits=(16,1))
    humidity_percent_normal = fields.Float("Humidity %")

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    ## Normal Consistency

    tests = fields.Many2many("mechanical.cement.test",string="Tests")

    normal_consistency_name = fields.Char("Name",default="Normal Consistency")
    normal_consistency_visible = fields.Boolean("Normal Consistency Visible",compute="_compute_visible")
    start_date_normal = fields.Date("Start Date")
    end_date_normal = fields.Date("End Date")

    wt_of_cement_trial1 = fields.Float("Wt. of Cement(g)",default=400)
    wt_of_cement_trial2 = fields.Float("Wt. of Cement(g)",default=400)
    wt_of_cement_trial3 = fields.Float("Wt. of Cement(g)",default=400)

    wt_of_water_req_trial1 = fields.Float("Wt.of water required (g)")
    wt_of_water_req_trial2 = fields.Float("Wt.of water required (g)")
    wt_of_water_req_trial3 = fields.Float("Wt.of water required (g)")

    penetration_of_vicat_plunger_trial1 = fields.Float("Penetraion of vicat's Plunger (mm)")
    penetration_of_vicat_plunger_trial2 = fields.Float("Penetraion of vicat's Plunger (mm)")
    penetration_of_vicat_plunger_trial3 = fields.Float("Penetraion of vicat's Plunger (mm)")

    normal_consistency_trial1 = fields.Float("Normal Consistency (%)",compute="_compute_normal_consistency",store=True)
    # normal_consistency_trial2 = fields.Float("Normal Consistency (%)",compute="_compute_normal_consistency",store=True)
    # normal_consistency_trial3 = fields.Float("Normal Consistency (%)",compute="_compute_normal_consistency",store=True)

    normal_consistency_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_normal_conformity")

    normal_consistency_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),

    ], string='NABL', default='fail',compute="_compute_normal_consistency_nabl")

    @api.depends('normal_consistency_trial1','eln_ref','grade')
    def _compute_normal_conformity(self):
        for record in self:
            record.normal_consistency_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','aba71b08-8839-4a61-a663-1d1e9da8f9a5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','aba71b08-8839-4a61-a663-1d1e9da8f9a5')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.normal_consistency_trial1 - record.normal_consistency_trial1*mu_value
                    upper = record.normal_consistency_trial1 + record.normal_consistency_trial1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.normal_consistency_conformity = 'pass'
                        break
                    else:
                        record.normal_consistency_conformity = 'fail'

    @api.depends('normal_consistency_trial1','eln_ref','grade')
    def _compute_normal_consistency_nabl(self):
        
        for record in self:
            record.normal_consistency_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','aba71b08-8839-4a61-a663-1d1e9da8f9a5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','aba71b08-8839-4a61-a663-1d1e9da8f9a5')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.normal_consistency_trial1 - record.normal_consistency_trial1*mu_value
            upper = record.normal_consistency_trial1 + record.normal_consistency_trial1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.normal_consistency_nabl = 'pass'
                break
            else:
                record.normal_consistency_nabl = 'fail'
    

    ### setting Time,Final Setting Time	

    initial_setting_time_visible = fields.Boolean("Initial Setting Time Visible",compute="_compute_visible")
    initial_setting_time_name = fields.Char("Name",default="Initial Setting Time")

    temp_percent_setting = fields.Float("Temperature °C",digits=(16,1))
    humidity_percent_setting = fields.Float("Humidity %")
    start_date_setting = fields.Date("Start Date")
    end_date_setting = fields.Date("End Date")

    wt_of_cement_setting_time = fields.Float("Wt. of Cement(g)",default=400)
    wt_of_water_required_setting_time = fields.Float("Wt.of water required (g) (0.85*P%)" , compute="_compute_wt_of_water_required",store=True )

    @api.depends('normal_consistency_trial1','wt_of_cement_setting_time')
    def _compute_wt_of_water_required(self):
        for record in self:
            record.wt_of_water_required_setting_time =  (((0.85 * record.normal_consistency_trial1) / 100) * record.wt_of_cement_setting_time)

    #Initial setting Time

    setting_time_name = fields.Char("Name", default="Setting Time")
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
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='pass',compute="_compute_initial_setting_nabl")


    @api.depends('initial_setting_time_minutes_unrounded','eln_ref','grade')
    def _compute_initial_setting_conformity(self):
        for record in self:
            record.initial_setting_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','40838d42-1926-4589-8a5e-88990875f55b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','40838d42-1926-4589-8a5e-88990875f55b')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','40838d42-1926-4589-8a5e-88990875f55b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','40838d42-1926-4589-8a5e-88990875f55b')]).parameter_table
            
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
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='pass',compute="_compute_final_setting_nabl")


    @api.depends('final_setting_time_minutes_unrounded','eln_ref','grade')
    def _compute_final_setting_conformity(self):
        for record in self:
            record.final_setting_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','671e0153-725b-46d5-9f0f-616a562a2b15')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','671e0153-725b-46d5-9f0f-616a562a2b15')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','671e0153-725b-46d5-9f0f-616a562a2b15')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','671e0153-725b-46d5-9f0f-616a562a2b15')]).parameter_table
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

                record.final_setting_time_hours = time_difference
                final_setting_time_decimal = time_difference.total_seconds() / 60
                final_setting_time = int(final_setting_time_decimal)
                if final_setting_time % 5 == 0:
                    final_setting_time_minutes = round(final_setting_time,0)
                    record.final_setting_time_minutes = final_setting_time_minutes
                else:
                    final_setting_time_minutes = round((final_setting_time / 5) * 5,0)
                    record.final_setting_time_minutes = final_setting_time_minutes


                record.final_setting_time_minutes_unrounded = final_setting_time
            else:
                record.final_setting_time_hours = False
                record.final_setting_time_minutes = False
                record.final_setting_time_minutes_unrounded = False


    #Density

    
    density_name = fields.Char("Name",default="Density")
    density_visible = fields.Boolean("Setting Time Visible",compute="_compute_visible")

    temp_percent_density = fields.Float("Temperature °C")
    humidity_percent_density = fields.Float("Humidity %")
    start_date_density = fields.Date("Start Date")
    end_date_density = fields.Date("End Date")

    wt_of_cement_density_trial1 = fields.Float("Wt. of Cement(g)",default=55)
    wt_of_cement_density_trial2 = fields.Float("Wt. of Cement(g)",default=55)

    initial_volume_kerosene_trial1 = fields.Float("Initial Volume of kerosine (ml)V1")
    initial_volume_kerosene_trial2 = fields.Float("Initial Volume of kerosine (ml)V1")

    final_volume_kerosene_trial1 = fields.Float("Final Volume of kerosine and Cement (After immersion in constant water bath) (ml) V2")
    final_volume_kerosene_trial2 = fields.Float("Final Volume of kerosine and Cement (After immersion in constant water bath) (ml) V2")

    displaced_volume_trial1 = fields.Float("Displaced volume (cm³)",compute="_compute_displaced_volume_trial1")
    displaced_volume_trial2 = fields.Float("Displaced volume (cm³)",compute="_compute_displaced_volume_trial2")

    density_trial1 = fields.Float("Density (g/cm³)",compute="_compute_density_trial1")
    density_trial2 = fields.Float("Density (g/cm³)",compute="_compute_density_trial2")

    average_density = fields.Float("Average",compute="_compute_density_average" ,digits=(16,2))

    density_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_density_conformity")

    density_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_density_nabl")


    @api.depends('average_density','eln_ref','grade')
    def _compute_density_conformity(self):
        for record in self:
            record.density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a524931-4407-4666-9465-007afbf0a510')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a524931-4407-4666-9465-007afbf0a510')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.average_density - record.average_density*mu_value
                    upper = record.average_density + record.average_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.density_conformity = 'pass'
                        break
                    else:
                        record.density_conformity = 'fail'

    @api.depends('average_density','eln_ref','grade')
    def _compute_density_nabl(self):
        
        for record in self:
            record.density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a524931-4407-4666-9465-007afbf0a510')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a524931-4407-4666-9465-007afbf0a510')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_density - record.average_density*mu_value
            upper = record.average_density + record.average_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.density_nabl = 'pass'
                break
            else:
                record.density_nabl = 'fail'

    @api.depends('initial_volume_kerosene_trial1','final_volume_kerosene_trial1')
    def _compute_displaced_volume_trial1(self):
        self.displaced_volume_trial1 = self.final_volume_kerosene_trial1 - self.initial_volume_kerosene_trial1

    @api.depends('initial_volume_kerosene_trial2','final_volume_kerosene_trial2')
    def _compute_displaced_volume_trial2(self):
         self.displaced_volume_trial2 = self.final_volume_kerosene_trial2 - self.initial_volume_kerosene_trial2


    @api.depends('wt_of_cement_density_trial1','displaced_volume_trial1')
    def _compute_density_trial1(self):
        try:
            self.density_trial1 = self.wt_of_cement_density_trial1 / self.displaced_volume_trial1
        except:
            self.density_trial1 = 0

    @api.depends('wt_of_cement_density_trial2','displaced_volume_trial2')
    def _compute_density_trial2(self):
        try:
            self.density_trial2 = self.wt_of_cement_density_trial2 / self.displaced_volume_trial2
        except:
            self.density_trial2 = 0

    

    @api.depends('density_trial1','density_trial2')
    def _compute_density_average(self):
        average_density = round((self.density_trial1 + self.density_trial2)/2,2)
        self.average_density = average_density

    # Density End  

    # Soundness Test
    soundness_name = fields.Char("Name",default="Soundness by le-chatelier")
    soundness_visible = fields.Boolean("Soundness Visible",compute="_compute_visible")

    temp_percent_soundness = fields.Float("Temperature °C")
    humidity_percent_soundness = fields.Float("Humidity %")
    start_date_soundness = fields.Date("Start Date")
    end_date_soundness = fields.Date("End Date")

    wt_of_cement_soundness = fields.Float("Weight of Cement(g)",default=100)
    wt_of_water_req_soundness = fields.Float("Weight of water required(g)",compute="_compute_water_weight_soundness")

    soundness_table = fields.One2many('cement.psc.soundness.line','parent_id',string="Soundness")
    average_soundness = fields.Float("Average",compute="_compute_average_soundness")
    expansion_soundness = fields.Float("Expansion(mm)",compute="_compute_expansion_soundness" ,digits=(16,1))

    soundness_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_soundness_conformity")

    soundness_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_soundness_nabl")


    @api.depends('expansion_soundness','eln_ref','grade')
    def _compute_soundness_conformity(self):
        for record in self:
            record.soundness_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d0de3979-1010-49ff-bed2-38872eb24bde')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d0de3979-1010-49ff-bed2-38872eb24bde')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    
                    lower = record.expansion_soundness - record.expansion_soundness*mu_value
                    upper = record.expansion_soundness + record.expansion_soundness*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.soundness_conformity = 'pass'
                        break
                    else:
                        record.soundness_conformity = 'fail'

    @api.depends('expansion_soundness','eln_ref','grade')
    def _compute_soundness_nabl(self):
        
        for record in self:
            record.soundness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d0de3979-1010-49ff-bed2-38872eb24bde')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d0de3979-1010-49ff-bed2-38872eb24bde')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.expansion_soundness - record.expansion_soundness*mu_value
            upper = record.expansion_soundness + record.expansion_soundness*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.soundness_nabl = 'pass'
                break
            else:
                record.soundness_nabl = 'fail'

    @api.depends('soundness_table.expansion')
    def _compute_average_soundness(self):
        for record in self:
            try:
                record.average_soundness = sum(record.soundness_table.mapped('expansion'))/len(record.soundness_table)
            except:
                record.average_soundness = 0

    @api.depends('wt_of_cement_soundness','normal_consistency_trial1')
    def _compute_water_weight_soundness(self):
        self.wt_of_water_req_soundness = (((0.78*self.normal_consistency_trial1)/100)*self.wt_of_cement_soundness)

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

    # @api.constrains('soundness_table')
    # def check_soundness_table_limit(self):
    #     max_limit = 2  # Set the maximum limit here
    #     for record in self:
    #         if len(record.soundness_table) > max_limit:
    #             raise ValidationError(f"Maximum limit of {max_limit} rows exceeded for Related Records.")


    #Dry Sieving 

    
    dry_sieving_name = fields.Char("Name",default="Dry Sieving")
    dry_sieving_visible = fields.Boolean("Dry Sieving Visible",compute="_compute_visible")

    temp_percent_dry_sieving = fields.Float("Temperature %")
    humidity_percent_dry_sieving = fields.Float("Humidity %")
    start_date_dry_sieving = fields.Date("Start Date")
    end_date_dry_sieving = fields.Date("End Date")

    dry_sieving_table = fields.One2many('cement.psc.dry.sieving.line','parent_id',string="Dry Sieving")
    average_fineness = fields.Float("Average",compute="_compute_average_fineness")
    fineness_dry_sieving = fields.Float("Fineness by dry sieving %",compute="_compute_fineness_dry_sieving" ,digits=(16,1))

    dry_seiving_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_dry_seiving_conformity")

    dry_seiving_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_dry_seiving_nabl")


    @api.depends('fineness_dry_sieving','eln_ref','grade')
    def _compute_dry_seiving_conformity(self):
        for record in self:
            record.dry_seiving_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bbc6029a-ce81-4ccf-8a69-522ac5daf4b0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bbc6029a-ce81-4ccf-8a69-522ac5daf4b0')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    
                    lower = record.fineness_dry_sieving - record.fineness_dry_sieving*mu_value
                    upper = record.fineness_dry_sieving + record.fineness_dry_sieving*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.dry_seiving_conformity = 'pass'
                        break
                    else:
                        record.dry_seiving_conformity = 'fail'

    @api.depends('fineness_dry_sieving','eln_ref','grade')
    def _compute_dry_seiving_nabl(self):
        
        for record in self:
            record.dry_seiving_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bbc6029a-ce81-4ccf-8a69-522ac5daf4b0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bbc6029a-ce81-4ccf-8a69-522ac5daf4b0')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.fineness_dry_sieving - record.fineness_dry_sieving*mu_value
            upper = record.fineness_dry_sieving + record.fineness_dry_sieving*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.dry_seiving_nabl = 'pass'
                break
            else:
                record.dry_seiving_nabl = 'fail'

    


    @api.depends('dry_sieving_table.fineness')
    def _compute_average_fineness(self):
        for record in self:
            try:
                record.average_fineness = sum(record.dry_sieving_table.mapped('fineness'))/len(record.dry_sieving_table)
            except:
                record.average_fineness = 0


    @api.depends('average_fineness')
    def _compute_fineness_dry_sieving(self):
        fineness_dry_sieving = round(self.average_fineness, 1)
        self.fineness_dry_sieving = fineness_dry_sieving

    # Compressive Strength 

    compressive_name = fields.Char("Name",default="Compressive Strength")
    # compressive_visible = fields.Boolean("Compressive Visible",compute="_compute_visible")

    temp_percent_compressive = fields.Float("Temperature °C")
    humidity_percent_compressive = fields.Float("Humidity %")
    start_date_compressive = fields.Date("Start Date")
    end_date_compressive = fields.Date("End Date")

    wt_of_cement_compressive = fields.Float("Wt. of Cement(g)",default=200)
    wt_of_standard_sand_grade1 = fields.Float("Weight of Standard Sand (g) Grade-I",default=200)
    wt_of_standard_sand_grade2 = fields.Float("Weight of Standard Sand (g) Grade-II",default=200)
    wt_of_standard_sand_grade3 = fields.Float("Weight of Standard Sand (g) Grade-III",default=200)
    total_weight = fields.Float("Total Weight",compute="compute_total_weight_compressive")
    quantity_of_water = fields.Float("Quantity of Water",compute="_compute_quantity_of_water")

    @api.depends('wt_of_cement_compressive','wt_of_standard_sand_grade1','wt_of_standard_sand_grade2','wt_of_standard_sand_grade3')
    def compute_total_weight_compressive(self):
        self.total_weight = self.wt_of_cement_compressive + self.wt_of_standard_sand_grade1 + self.wt_of_standard_sand_grade2 + self.wt_of_standard_sand_grade3 

    @api.depends('normal_consistency_trial1')
    def _compute_quantity_of_water(self):
        self.quantity_of_water = ((self.normal_consistency_trial1/4 +3)*8)
    
    # 3 days Casting
    casting_3_name = fields.Char("Name",default="3 Days")
    compressive_3_visible = fields.Boolean("3 days Visible",compute="_compute_visible")

    casting_date_3days = fields.Date(string="Date of Casting")
    testing_date_3days = fields.Date(string="Date of Testing",compute="_compute_testing_date_3days")
    casting_3_days_tables = fields.One2many('cement.psc.casting.3days.line','parent_id',string="3 Days")
    average_casting_3days = fields.Float("Average",compute="_compute_average_3days")
    compressive_strength_3_days = fields.Float("Compressive Strength",compute="_compute_compressive_strength_3days" ,digits=(16,1))
    status_3days = fields.Boolean("Done")

    compressive_3days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_compressive_3days_conformity")

    compressive_3days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_compressive_3days_nabl")


    @api.depends('compressive_strength_3_days','eln_ref','grade')
    def _compute_compressive_3days_conformity(self):
        for record in self:
            record.compressive_3days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c59e9080-f1e5-4ef5-8ced-f1232704ab2d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c59e9080-f1e5-4ef5-8ced-f1232704ab2d')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.compressive_strength_3_days - record.compressive_strength_3_days*mu_value
                    upper = record.compressive_strength_3_days + record.compressive_strength_3_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.compressive_3days_conformity = 'pass'
                        break
                    else:
                        record.compressive_3days_conformity = 'fail'

    @api.depends('compressive_strength_3_days','eln_ref','grade')
    def _compute_compressive_3days_nabl(self):
        
        for record in self:
            record.compressive_3days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c59e9080-f1e5-4ef5-8ced-f1232704ab2d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c59e9080-f1e5-4ef5-8ced-f1232704ab2d')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.compressive_strength_3_days - record.compressive_strength_3_days*mu_value
            upper = record.compressive_strength_3_days + record.compressive_strength_3_days*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.compressive_3days_nabl = 'pass'
                break
            else:
                record.compressive_3days_nabl = 'fail'


    @api.depends('casting_3_days_tables.compressive_strength')
    def _compute_average_3days(self):
        for record in self:
            try:
                record.average_casting_3days = sum(record.casting_3_days_tables.mapped('compressive_strength'))/len(record.casting_3_days_tables)
            except:
                record.average_casting_3days = 0
    
    @api.depends('casting_date_3days')
    def _compute_testing_date_3days(self):
        for record in self:
            if record.casting_date_3days:
                cast_date = fields.Datetime.from_string(record.casting_date_3days)
                testing_date = cast_date + timedelta(days=3)
                record.testing_date_3days = fields.Datetime.to_string(testing_date)
            else:
                record.testing_date_3days = False
    
    @api.depends('average_casting_3days')
    def _compute_compressive_strength_3days(self):
        for record in self:
            integer_part = math.floor(record.average_casting_3days)
            fractional_part = record.average_casting_3days - integer_part
            if fractional_part > 0 and fractional_part <= 0.25:
                compressive_strength_3_days = round(integer_part,1)
                record.compressive_strength_3_days = compressive_strength_3_days
            elif fractional_part > 0.25 and fractional_part <= 0.75:
                compressive_strength_3_days = round(integer_part + 0.5,1)
                record.compressive_strength_3_days = compressive_strength_3_days
            elif fractional_part > 0.75 and fractional_part <= 1:
                compressive_strength_3_days = round(integer_part + 1,1)
                record.compressive_strength_3_days = compressive_strength_3_days
            else:
                record.compressive_strength_3_days = 0
            
            

    # 7 Days Casting

    casting_7_name = fields.Char("Name",default="7 Days")
    compressive_7_visible = fields.Boolean("7 days Visible",compute="_compute_visible")

    casting_date_7days = fields.Date(string="Date of Casting")
    testing_date_7days = fields.Date(string="Date of Testing",compute="_compute_testing_date_7days")
    casting_7_days_tables = fields.One2many('cement.psc.casting.7days.line','parent_id',string="7 Days")
    average_casting_7days = fields.Float("Average",compute="_compute_average_7days")
    compressive_strength_7_days = fields.Float("Compressive Strength",compute="_compute_compressive_strength_7days" ,digits=(16,1))
    status_7days = fields.Boolean("Done")

    compressive_7days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_compressive_7days_conformity")

    compressive_7days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_compressive_7days_nabl")


    @api.depends('compressive_strength_7_days','eln_ref','grade')
    def _compute_compressive_7days_conformity(self):
        for record in self:
            record.compressive_7days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a221eadd-b067-41ed-9c64-3180b0d2f644')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a221eadd-b067-41ed-9c64-3180b0d2f644')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.compressive_strength_7_days - record.compressive_strength_7_days*mu_value
                    upper = record.compressive_strength_7_days + record.compressive_strength_7_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.compressive_7days_conformity = 'pass'
                        break
                    else:
                        record.compressive_7days_conformity = 'fail'

    @api.depends('compressive_strength_7_days','eln_ref','grade')
    def _compute_compressive_7days_nabl(self):
        
        for record in self:
            record.compressive_7days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a221eadd-b067-41ed-9c64-3180b0d2f644')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a221eadd-b067-41ed-9c64-3180b0d2f644')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.compressive_strength_7_days - record.compressive_strength_7_days*mu_value
            upper = record.compressive_strength_7_days + record.compressive_strength_7_days*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.compressive_7days_nabl = 'pass'
                break
            else:
                record.compressive_7days_nabl = 'fail'


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


    @api.depends('average_casting_7days')
    def _compute_compressive_strength_7days(self):
        for record in self:
            integer_part = math.floor(record.average_casting_7days)
            fractional_part = record.average_casting_7days - integer_part
            if fractional_part > 0 and fractional_part <= 0.25:
                compressive_strength_7_days = round(integer_part,1)
                record.compressive_strength_7_days = compressive_strength_7_days
            elif fractional_part > 0.25 and fractional_part <= 0.75:
                compressive_strength_7_days = round(integer_part + 0.5,1)
                record.compressive_strength_7_days = compressive_strength_7_days
            elif fractional_part > 0.75 and fractional_part <= 1:
                compressive_strength_7_days = round(integer_part + 1,1)
                record.compressive_strength_7_days = compressive_strength_7_days
            else:
                record.compressive_strength_7_days = 0

    #28 days Casting

    casting_28_name = fields.Char("Name",default="28 Days")
    compressive_28_visible = fields.Boolean("28 days Visible",compute="_compute_visible")

    casting_date_28days = fields.Date(string="Date of Casting")
    testing_date_28days = fields.Date(string="Date of Testing",compute="_compute_testing_date_28days")
    casting_28_days_tables = fields.One2many('cement.psc.casting.28days.line','parent_id',string="28 Days")
    average_casting_28days = fields.Float("Average",compute="_compute_average_28days")
    compressive_strength_28_days = fields.Float("Compressive Strength",compute="_compute_compressive_strength_28days" ,digits=(16,1))
    status_28days = fields.Boolean("Done")
    compressive_28days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_compressive_28days_conformity")

    compressive_28days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_compressive_28days_nabl")


    @api.depends('compressive_strength_28_days','eln_ref','grade')
    def _compute_compressive_28days_conformity(self):
        for record in self:
            record.compressive_28days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','734c18a7-e665-44bc-89b7-ed512432bc9c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','734c18a7-e665-44bc-89b7-ed512432bc9c')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.compressive_strength_28_days - record.compressive_strength_28_days*mu_value
                    upper = record.compressive_strength_28_days + record.compressive_strength_28_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.compressive_28days_conformity = 'pass'
                        break
                    else:
                        record.compressive_28days_conformity = 'fail'

    @api.depends('compressive_strength_28_days','eln_ref','grade')
    def _compute_compressive_28days_nabl(self):
        
        for record in self:
            record.compressive_28days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','734c18a7-e665-44bc-89b7-ed512432bc9c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','734c18a7-e665-44bc-89b7-ed512432bc9c')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.compressive_strength_28_days - record.compressive_strength_28_days*mu_value
            upper = record.compressive_strength_28_days + record.compressive_strength_28_days*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.compressive_28days_nabl = 'pass'
                break
            else:
                record.compressive_28days_nabl = 'fail'


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
                compressive_strength_28_days = round(integer_part,1)
                record.compressive_strength_28_days = compressive_strength_28_days
            elif fractional_part > 0.25 and fractional_part <= 0.75:
                compressive_strength_28_days = round(integer_part + 0.5,1)
                record.compressive_strength_28_days = compressive_strength_28_days
            elif fractional_part > 0.75 and fractional_part <= 1:
                compressive_strength_28_days = round(integer_part + 1,1)
                record.compressive_strength_28_days = compressive_strength_28_days
            else:
                record.compressive_strength_28_days = 0

    # Fineness Air Permeability Method

    fineness_blaine_name = fields.Char("Name",default="Fineness By Blaine Air Permeability Method")
    fineness_blaine_visible = fields.Boolean("Fineness Blaine Visible",compute="_compute_visible")

    temp_percent_fineness = fields.Float("Temperature °C")
    humidity_percent_fineness = fields.Float("Humidity %")
    start_date_fineness = fields.Date("Start Date")
    end_date_fineness = fields.Date("End Date")

    weight_of_mercury_before_trial1 = fields.Float("Weight of mercury before placing the sample in the permeability cell  (m₁),g." ,default=83.450,digits=(16, 3))
    weight_of_mercury_before_trial2 = fields.Float("Weight of mercury before placing the sample in the permeability cell  (m₁),g.",default=83.440,digits=(16, 3))
    

    weight_of_mercury_after_trail1 = fields.Float("Weight of mercury after placing the sample in the permeability cell  (m₂),g.",default=57.160,digits=(16, 3))
    weight_of_mercury_after_trail2 = fields.Float("Weight of mercury after placing the sample in the permeability cell  (m₂),g.",default=57.180,digits=(16, 3))

    density_of_mercury = fields.Float("Density of mercury , g/cm3",default=13.530,digits=(16, 3))

    bed_volume_trial1 = fields.Float("Bed Volume (V=m₂-m₁/D),cm3.",compute="_compute_bed_volume_trial1",digits=(16, 3))
    bed_volume_trial2 = fields.Float("Bed Volume (V=m₂-m₁/D),cm3.",compute="_compute_bed_volume_trial2",digits=(16, 3))

    average_bed_volume = fields.Float("Average Bed Volume (cm3)",compute="_compute_average_bed_volume",digits=(16, 3))

    difference_between_2_values = fields.Float("Difference between the two Values",compute="_compute_difference_bed_volume",digits=(16, 3))

    density_fineness_reference = fields.Float("Density" ,compute="_compute_density_fineness")
    mass_of_sample_taken_fineness_reference = fields.Float("mass of sample taken (g)" ,compute="_compute_mass_taken_reference")

    time_fineness_trial1 = fields.Float("Time(t),sec.",default=64.85)
    time_fineness_trial2 = fields.Float("Time(t),sec.",default=63.65)
    time_fineness_trial3 = fields.Float("Time(t),sec.",default=63.22)
    average_time_fineness = fields.Float("Average Time(tₒ),Sec",compute="_compute_time_average_fineness")

    specific_surface_of_reference_sample = fields.Float("S0 is the Specific surface of reference sample (m²/kg)",default=306) 
    air_viscosity_of_three_temp = fields.Float("ɳₒ is the Air viscosity at the mean of the three temperatures",default=0.001355,digits=(16, 6))
    density_of_reference_sample = fields.Float("ρ0 is the Density of reference sample  (g/cm3)",default=2.97)
    mean_of_three_measured_times = fields.Float("t0 is the Mean of three measured times (sec)",compute="_compute_mean_measured_time")
    apparatus_constant = fields.Float("Apparatus Constant(k)",compute="_compute_apparatus_constant")

    density_fineness_calculated = fields.Float("Density",compute="_compute_density_calculated")
    mass_of_sample_taken_fineness_calculated = fields.Float("mass of sample taken (g)",compute="_compute_mass_sample_calculated")

    time_sample_trial1 = fields.Float("Time(t),sec.")
    time_sample_trial2 = fields.Float("Time(t),sec.")
    time_sample_trial3 = fields.Float("Time(t),sec.")
    average_sample_time = fields.Float("Average Time(tₒ),Sec",compute="_compute_average_sample_time")

    fineness_of_sample = fields.Float("Fineness of Sample",compute="_compute_fineness_of_sample")
    fineness_air_permeability = fields.Integer("Fineness By Blaine Air Permeability Method (m2/kg)",compute="_compute_fineness_air_permeability")

    fineness_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_fineness_conformity")

    fineness_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_fineness_nabl")

    @api.depends('fineness_air_permeability','eln_ref','grade')
    def _compute_fineness_conformity(self):
        for record in self:
            record.fineness_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','104a9e28-7eb8-4d40-9d0a-8b05eed98c11')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','104a9e28-7eb8-4d40-9d0a-8b05eed98c11')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.fineness_air_permeability - record.fineness_air_permeability*mu_value
                    upper = record.fineness_air_permeability + record.fineness_air_permeability*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.fineness_conformity = 'pass'
                        break
                    else:
                        record.fineness_conformity = 'fail'

    @api.depends('fineness_air_permeability','eln_ref','grade')
    def _compute_fineness_nabl(self):
        
        for record in self:
            record.fineness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','104a9e28-7eb8-4d40-9d0a-8b05eed98c11')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','104a9e28-7eb8-4d40-9d0a-8b05eed98c11')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.fineness_air_permeability - record.fineness_air_permeability*mu_value
            upper = record.fineness_air_permeability + record.fineness_air_permeability*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.fineness_nabl = 'pass'
                break
            else:
                record.fineness_nabl = 'fail'
    
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

    @api.depends('density_of_reference_sample')
    def _compute_density_fineness(self):
        self.density_fineness_reference = self.density_of_reference_sample

    @api.depends('average_bed_volume','density_fineness_reference')
    def _compute_mass_taken_reference(self):
        self.mass_of_sample_taken_fineness_reference = 0.5*self.average_bed_volume*self.density_fineness_reference

    @api.depends('time_fineness_trial1','time_fineness_trial2','time_fineness_trial3')
    def _compute_time_average_fineness(self):
        self.average_time_fineness = (self.time_fineness_trial1 + self.time_fineness_trial2 + self.time_fineness_trial3)/3

    @api.depends('specific_surface_of_reference_sample','air_viscosity_of_three_temp','density_of_reference_sample','mean_of_three_measured_times')
    def _compute_apparatus_constant(self):
        if self.mean_of_three_measured_times != 0:
            self.apparatus_constant = round(1.414*self.specific_surface_of_reference_sample*self.density_of_reference_sample*((self.air_viscosity_of_three_temp)/(self.mean_of_three_measured_times**0.5)),2)
        else:
            self.apparatus_constant = 0

    @api.depends('average_density')
    def _compute_density_calculated(self):
        self.density_fineness_calculated = self.average_density

    @api.depends('average_bed_volume','density_fineness_calculated')
    def _compute_mass_sample_calculated(self):
        self.mass_of_sample_taken_fineness_calculated = 0.5*self.average_bed_volume*self.density_fineness_calculated

    @api.depends('time_sample_trial1','time_sample_trial2','time_sample_trial3')
    def _compute_average_sample_time(self):
        self.average_sample_time = (self.time_sample_trial1 + self.time_sample_trial2 + self.time_sample_trial3)/3

    @api.depends('apparatus_constant','average_sample_time','density_fineness_calculated')
    def _compute_fineness_of_sample(self):
        if self.density_fineness_calculated != 0:
            self.fineness_of_sample = (521.08*self.apparatus_constant*(self.average_sample_time**0.5))/self.density_fineness_calculated
        else:
            self.fineness_of_sample = 0
    
    @api.depends('fineness_of_sample')
    def _compute_fineness_air_permeability(self):
        for record in self:
            record.fineness_air_permeability = math.ceil(record.fineness_of_sample)

    @api.depends('average_time_fineness')
    def _compute_mean_measured_time(self):
        for record in self:
            record.mean_of_three_measured_times = record.average_time_fineness

       # added
    # Soundness by Autoclave Method
    opc_soundness_name = fields.Char("Name",default="Soundness by Autoclave Method")
    opc_soundness_visible = fields.Boolean("Soundness by Autoclave Method Visible",compute="_compute_visible")
  
    opc_soundness_table = fields.One2many('psc.soundness.autoclave.line','parent_id',string="Parameter")
    wt_cement_opc = fields.Float(string="Wt. of Cement (g)", store=True)
    water_required_opc = fields.Float(string="Wt.of water required (g)", store=True)
    avg_expantion_opc = fields.Float(string="Average Expansion %",compute="_compute_avg_expantion_opc",digits=(12,3))

    @api.depends('opc_soundness_table.expantion')
    def _compute_avg_expantion_opc(self):
        for record in self:
            expantion_values = record.opc_soundness_table.mapped('expantion')
            if expantion_values:
                avg_expantion_opc = sum(expantion_values) / len(expantion_values)
                record.avg_expantion_opc = avg_expantion_opc
            else:
                record.avg_expantion_opc = 0.0


    avg_expantion_opc_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_expantion_opc_conformity", store=True)



    @api.depends('avg_expantion_opc','eln_ref','grade')
    def _compute_avg_expantion_opc_conformity(self):
        
        for record in self:
            record.avg_expantion_opc_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a85138e1-99b3-40c5-a4aa-ffb96f2c9507')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a85138e1-99b3-40c5-a4aa-ffb96f2c9507')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_expantion_opc - record.avg_expantion_opc*mu_value
                    upper = record.avg_expantion_opc + record.avg_expantion_opc*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_expantion_opc_conformity = 'pass'
                        break
                    else:
                        record.avg_expantion_opc_conformity = 'fail'

    avg_expantion_opc_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_expantion_opc_nabl", store=True)

    @api.depends('avg_expantion_opc','eln_ref','grade')
    def _compute_avg_expantion_opc_nabl(self):
        
        for record in self:
            record.avg_expantion_opc_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a85138e1-99b3-40c5-a4aa-ffb96f2c9507')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a85138e1-99b3-40c5-a4aa-ffb96f2c9507')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_expantion_opc - record.avg_expantion_opc*mu_value
                    upper = record.avg_expantion_opc + record.avg_expantion_opc*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_expantion_opc_nabl = 'pass'
                        break
                    else:
                        record.avg_expantion_opc_nabl = 'fail'


            
    ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.normal_consistency_visible = False
            record.initial_setting_time_visible  = False 
            record.final_setting_time_visible  = False  
            record.density_visible = False
            record.soundness_visible = False
            record.dry_sieving_visible = False
            record.fineness_blaine_visible = False
            record.compressive_3_visible = False
            record.compressive_7_visible = False
            record.compressive_28_visible = False
            record.opc_soundness_visible = False

            

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == 'aba71b08-8839-4a61-a663-1d1e9da8f9a5':
                    record.normal_consistency_visible = True
                if sample.internal_id == '40838d42-1926-4589-8a5e-88990875f55b':
                    record.normal_consistency_visible = True
                    record.initial_setting_time_visible  = True
                if sample.internal_id == '671e0153-725b-46d5-9f0f-616a562a2b15':
                    record.normal_consistency_visible = True
                    record.initial_setting_time_visible  = True
                    record.final_setting_time_visible  = True
                if sample.internal_id == '3a524931-4407-4666-9465-007afbf0a510':
                    record.density_visible = True
                if sample.internal_id == 'd0de3979-1010-49ff-bed2-38872eb24bde':
                    record.normal_consistency_visible = True
                    record.soundness_visible = True
                if sample.internal_id == 'c59e9080-f1e5-4ef5-8ced-f1232704ab2d':
                    record.normal_consistency_visible = True
                    record.compressive_3_visible = True
                if sample.internal_id == 'a221eadd-b067-41ed-9c64-3180b0d2f644':
                    record.normal_consistency_visible = True
                    record.compressive_3_visible = True
                    record.compressive_7_visible = True
                if sample.internal_id == '734c18a7-e665-44bc-89b7-ed512432bc9c':
                    record.normal_consistency_visible = True
                    record.compressive_3_visible = True
                    record.compressive_7_visible = True
                    record.compressive_28_visible = True
                if sample.internal_id == 'bbc6029a-ce81-4ccf-8a69-522ac5daf4b0':
                    record.dry_sieving_visible = True
                if sample.internal_id == '104a9e28-7eb8-4d40-9d0a-8b05eed98c11':
                    record.fineness_blaine_visible = True
                    record.density_visible = True

                if sample.internal_id == 'a85138e1-99b3-40c5-a4aa-ffb96f2c9507':
                    record.opc_soundness_visible = True


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:


            if result.parameter.internal_id == 'aba71b08-8839-4a61-a663-1d1e9da8f9a5':
                result.result_char = round(self.normal_consistency_trial1,2)
                result.calculated = True
                if self.normal_consistency_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '40838d42-1926-4589-8a5e-88990875f55b':
                result.result_char = self.initial_setting_time_minutes_unrounded
                result.calculated = True
                if self.initial_setting_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '671e0153-725b-46d5-9f0f-616a562a2b15':
                result.result_char = self.final_setting_time_minutes
                result.calculated = True
                if self.final_setting_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '3a524931-4407-4666-9465-007afbf0a510':
                result.result_char = round(self.average_density,2)
                result.calculated = True
                if self.density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == 'd0de3979-1010-49ff-bed2-38872eb24bde':
                result.result_char = round(self.expansion_soundness,2)
                result.calculated = True
                if self.soundness_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

          
            if result.parameter.internal_id == 'c59e9080-f1e5-4ef5-8ced-f1232704ab2d':
                result.result_char = round(self.compressive_strength_3_days,2)
                result.calculated = True
                if self.compressive_3days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == 'a221eadd-b067-41ed-9c64-3180b0d2f644':
                result.result_char = round(self.compressive_strength_7_days,2)
                result.calculated = True
                if self.compressive_7days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '734c18a7-e665-44bc-89b7-ed512432bc9c':
                result.result_char = round(self.compressive_strength_28_days,2)
                result.calculated = True
                if self.compressive_28days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == 'bbc6029a-ce81-4ccf-8a69-522ac5daf4b0':
                result.result_char = round(self.fineness_dry_sieving)
                result.calculated = True
                if self.dry_seiving_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '104a9e28-7eb8-4d40-9d0a-8b05eed98c11':
                result.result_char = round(self.fineness_air_permeability)
                result.calculated = True
                if self.fineness_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'a85138e1-99b3-40c5-a4aa-ffb96f2c9507':
                result.result_char = round(self.avg_expantion_opc)
                result.calculated = True
                if self.avg_expantion_opc_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
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
        record = super(CementPsc, self).create(vals)
        
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    # @api.model 
    # def write(self, values):
    #     # Perform additional actions or validations before update
    #     result = super(CementNormalConsistency, self).write(values)
    #     # Perform additional actions or validations after update
    #     return result
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
        # import wdb;wdb.set_trace()
        record = self.env['mechanical.cement.psc'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends("wt_of_cement_trial1","wt_of_cement_trial2","wt_of_cement_trial3","wt_of_water_req_trial1","wt_of_water_req_trial2","wt_of_water_req_trial3")
    def _compute_normal_consistency(self):
        for record in self:
            if record.wt_of_water_req_trial1 and record.wt_of_cement_trial1:
                record.normal_consistency_trial1 = round((record.wt_of_water_req_trial1/record.wt_of_cement_trial1) * 100,2)
            else:
                record.normal_consistency_trial1 = 0
            
            # if record.wt_of_water_req_trial2 and record.wt_of_cement_trial2:
            #     record.normal_consistency_trial2 = (record.wt_of_water_req_trial2/record.wt_of_cement_trial2) * 100
            # else:
            #     record.normal_consistency_trial2 = 0

            # if record.wt_of_water_req_trial3 and record.wt_of_cement_trial3:
            #     record.normal_consistency_trial3 = (record.wt_of_water_req_trial3/record.wt_of_cement_trial3) * 100
            # else:
            #     record.normal_consistency_trial3 = 0
    


class CementTestPsc(models.Model):
    _name = "mechanical.cement.psc.test"
    _rec_name = "name"
    name = fields.Char("Name")


class SoundnessCementLinePsc(models.Model):
    _name= "cement.psc.soundness.line"

    parent_id = fields.Many2one('mechanical.cement.psc')
    initial_distance = fields.Float("Intial distance separating the indicator points (L1).mm")
    final_distance = fields.Float("Final distance separating the indicator points (L2).mm")
    expansion = fields.Float("Expansion",compute="_compute_expansion")

    @api.depends('initial_distance','final_distance')
    def _compute_expansion(self):
        for record in self:
            record.expansion = round(record.final_distance - record.initial_distance,2)

class DrySievingLinePsc(models.Model):
    _name = "cement.psc.dry.sieving.line"

    parent_id = fields.Many2one('mechanical.cement.psc')
    sample_weight_fineness = fields.Float("Sample Weight(g)",default=100)
    retained_weight = fields.Float("Retained Weight on 90 mic sieve (g)")
    fineness = fields.Float("Fineness by dry sieving %",compute="_compute_fineness")

    @api.depends('retained_weight','sample_weight_fineness')
    def _compute_fineness(self):
        for record in self:
            if record.sample_weight_fineness != 0:
                record.fineness = round((record.retained_weight / record.sample_weight_fineness )*100,2)
            else:
                record.fineness = 0


class Casting3DaysLinePsc(models.Model):
    _name = "cement.psc.casting.3days.line"

    parent_id = fields.Many2one('mechanical.cement.psc',string="Parent Id")
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

class Casting7DaysLinePsc(models.Model):
    _name = "cement.psc.casting.7days.line"

    parent_id = fields.Many2one('mechanical.cement.psc')

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

class Casting28DaysLinePsc(models.Model):
    _name = "cement.psc.casting.28days.line"

    parent_id = fields.Many2one('mechanical.cement.psc')

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

    @api.depends('crosssectional_area', 'crushing_load')
    def _compute_compressive_strength(self):
        for record in self:
            if record.crosssectional_area != 0:
                record.compressive_strength = round((record.crushing_load / record.crosssectional_area) * 1000,2)
            else:
                record.compressive_strength = 0


class SoundnessAutoclaveMethodpsc(models.Model):
    _name = "psc.soundness.autoclave.line"

    parent_id = fields.Many2one('mechanical.cement.psc')

    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    intial_length = fields.Float("Intial Length (L1)",digits=(12,3))
    final_length = fields.Float("Final Length (L2)",digits=(12,3))
    expantion = fields.Float("Expansion ((L2-L1)/L1)x 100, %",compute="_compute_expansion_opc",digits=(12,3))


    @api.depends('intial_length', 'final_length')
    def _compute_expansion_opc(self):
        for record in self:
            if record.intial_length:  # Avoid division by zero
                record.expantion = ((record.final_length - record.intial_length) / record.intial_length) * 100
            else:
                record.expantion = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(SoundnessAutoclaveMethodpsc, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class PscNotes(models.Model):
    _name = "psc.notes"

    parent_id = fields.Many2one('mechanical.cement.psc',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")