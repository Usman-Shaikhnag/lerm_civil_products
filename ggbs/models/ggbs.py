from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class GgbsMechanical(models.Model):
    _name = "mechanical.ggbs"
    _inherit = "lerm.eln"
    _description = 'mechanical.ggbs'
    _rec_name = "name"


    name = fields.Char("Name",default="GGBS")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.ggbs.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)


    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    ## Normal Consistency


    normal_consistency_name = fields.Char("Name",default="Normal Consistency of GGBS")
    normal_consistency_visible = fields.Boolean("Normal Consistency Visible",compute="_compute_visible")


    wt_of_cement_trial1 = fields.Float("Wt. of Cement(g)",default=200)
    wt_of_ggbs_trial1 = fields.Float("Wt. of GGBS(g)",default=200)
    total_wt_sample = fields.Float("Total Wt. of Sample",compute="_compute_total_wt_sample",store=True)
    wt_water_req = fields.Float("Wt. of water required")
    penetration_vicat = fields.Float("Penetration of vicat's Plunger(mm)")
    normal_consistency = fields.Float("Normal Consistency",compute="_compute_normal_consistency",store=True)

    # normal_consistency_conformity = fields.Selection([
    #     ('pass', 'Pass'),
    #     ('fail', 'Fail'),
    # ], string='Conformity', default='fail',compute="_compute_normal_conformity")

    # normal_consistency_nabl = fields.Selection([
    #     ('pass', 'Pass'),
    #     ('fail', 'Fail'),

    # ], string='NABL', default='fail',compute="_compute_normal_consistency_nabl")


    # @api.depends('normal_consistency','eln_ref','grade')
    # def _compute_normal_conformity(self):
    #     for record in self:
    #         record.normal_consistency_conformity = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457801hg-b44a-48cc-9d41-198f55346af0')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457801hg-b44a-48cc-9d41-198f55346af0')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 req_min = material.req_min
    #                 req_max = material.req_max
    #                 mu_value = line.mu_value
    #                 lower = record.normal_consistency - record.normal_consistency*mu_value
    #                 upper = record.normal_consistency + record.normal_consistency*mu_value
    #                 if lower >= req_min and upper <= req_max :
    #                     record.normal_consistency_conformity = 'pass'
    #                     break
    #                 else:
    #                     record.normal_consistency_conformity = 'fail'

    # @api.depends('normal_consistency','eln_ref','grade')
    # def _compute_normal_consistency_nabl(self):
        
    #     for record in self:
    #         record.normal_consistency_nabl = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457801hg-b44a-48cc-9d41-198f55346af0')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457801hg-b44a-48cc-9d41-198f55346af0')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 lab_min = line.lab_min_value
    #                 lab_max = line.lab_max_value
    #                 mu_value = line.mu_value
                    
    #                 lower = record.normal_consistency - record.normal_consistency*mu_value
    #                 upper = record.normal_consistency + record.normal_consistency*mu_value
    #                 if lower >= lab_min and upper <= lab_max:
    #                     record.normal_consistency_nabl = 'pass'
    #                     break
    #                 else:
    #                     record.normal_consistency_nabl = 'fail'


    @api.depends('wt_of_cement_trial1','wt_of_ggbs_trial1')
    def _compute_total_wt_sample(self):
        for record in self:
            record.total_wt_sample = record.wt_of_cement_trial1 + record.wt_of_ggbs_trial1

    @api.depends('wt_water_req','total_wt_sample')
    def _compute_normal_consistency(self):
        for record in self:
            if record.total_wt_sample != 0:
                record.normal_consistency = (record.wt_water_req / record.total_wt_sample ) *100



    # Normal Consistency Cement

    normal_consistency_cement_name = fields.Char("Name",default="Normal Consistency Cement")
    normal_consistency_cement_visible = fields.Boolean("Normal Consistency Visible",compute="_compute_visible")

    temp_normal_cement = fields.Float("Temperature °C")
    humidity_normal_cement = fields.Float("Humidity")
    start_date_normal_cement = fields.Date("Start Date")
    end_date_normal_cement = fields.Date("End Date")


    wt_cement = fields.Float("Wt. of  Cement (g)",default=400)
    wt_water_req_cement = fields.Float("Wt.of water required (g)")
    penetration_vicat_cement = fields.Float("Penetraion of vicat's Plunger (mm)")
    normal_consistency_cement = fields.Float("Normal Consistency %",compute="compute_normal_consistency_cement",store=True)

    @api.depends('wt_cement','wt_water_req_cement')
    def compute_normal_consistency_cement(self):
        for record in self:
            if record.wt_cement != 0:
                record.normal_consistency_cement = (record.wt_water_req_cement / record.wt_cement)*100
                
            else:
                record.normal_consistency_cement = 0


# Specific Gravity

    specific_gravity_name = fields.Char("Name",default="Specific Gravity")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    wt_of_ggbs_sg_trial1 = fields.Float("Wt. of GGBS(g)")
    wt_of_ggbs_sg_trial2 = fields.Float("Wt. of GGBS(g)")
    initial_volume_kerosine_trial1 = fields.Float("Initial Volume of kerosine (ml)V1")
    initial_volume_kerosine_trial2 = fields.Float("Initial Volume of kerosine (ml)V1)")
    final_volume_kerosine_trial1 = fields.Float("Final Volume of kerosine and GGBS (After immersion in constant water bath)(ml) V2")
    final_volume_kerosine_trial2 = fields.Float("Final Volume of kerosine and GGBS (After immersion in constant water bath)(ml) V2")
    displaced_volume_trial1 = fields.Float("Displaced Volume (cm³)",compute="_compute_displaced_volume_trail1",store=True)
    displaced_volume_trial2 = fields.Float("Displaced Volume (cm³)",compute="_compute_displaced_volume_trail2",store=True)
    specific_gravity_trial1 = fields.Float("Specific Gravity",compute="_compute_specific_gravity_trail1",store=True)
    specific_gravity_trial2 = fields.Float("Specific Gravity",compute="_compute_specific_gravity_trail2",store=True)
    average_specific_gravity = fields.Float("Average",compute="_compute_sg_average",store=True)
    specific_gravity_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('not_applicable', 'Not Applicable'),
    ], string='Confirmity', default='fail',compute="_compute_specific_gravity_confirmity")
    specific_gravity_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_specific_gravity_nabl")


    @api.depends('average_specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_confirmity(self):
        for record in self:
            record.specific_gravity_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','210bgf54-baa4-466f-a6a7-044da708f265')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','210bgf54-baa4-466f-a6a7-044da708f265')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_specific_gravity - record.average_specific_gravity*mu_value
                    upper = record.average_specific_gravity + record.average_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.specific_gravity_confirmity = 'pass'
                        break
                    else:
                        record.specific_gravity_confirmity = 'fail'
    
    @api.depends('average_specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_nabl(self):
        
        for record in self:
            record.specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','210bgf54-baa4-466f-a6a7-044da708f265')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','210bgf54-baa4-466f-a6a7-044da708f265')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_specific_gravity - record.average_specific_gravity*mu_value
                    upper = record.average_specific_gravity + record.average_specific_gravity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.specific_gravity_nabl = 'pass'
                        break
                    else:
                        record.specific_gravity_nabl = 'fail'

    @api.depends('initial_volume_kerosine_trial1','final_volume_kerosine_trial1')
    def _compute_displaced_volume_trail1(self):
        for record in self:
            record.displaced_volume_trial1 = record.final_volume_kerosine_trial1 - record.initial_volume_kerosine_trial1

    
    @api.depends('initial_volume_kerosine_trial2','final_volume_kerosine_trial2')
    def _compute_displaced_volume_trail2(self):
        for record in self:
            record.displaced_volume_trial2 = record.final_volume_kerosine_trial2 - record.initial_volume_kerosine_trial2


    @api.depends('wt_of_ggbs_sg_trial1','displaced_volume_trial1')
    def _compute_specific_gravity_trail1(self):
        for record in self:
            if record.displaced_volume_trial1 != 0:
                specific_gravity_trial1 = record.wt_of_ggbs_sg_trial1 / record.displaced_volume_trial1
                record.specific_gravity_trial1 = round(specific_gravity_trial1,2)

    
    @api.depends('wt_of_ggbs_sg_trial2','displaced_volume_trial2')
    def _compute_specific_gravity_trail2(self):
        for record in self:
            if record.displaced_volume_trial2 != 0:
                specific_gravity_trial2 = record.wt_of_ggbs_sg_trial2 / record.displaced_volume_trial2
                record.specific_gravity_trial2 = round(specific_gravity_trial2,2)



    @api.depends('specific_gravity_trial1','specific_gravity_trial2')
    def _compute_sg_average(self):
        for record in self:
            average_specific_gravity = (record.specific_gravity_trial1 + record.specific_gravity_trial2)/2
            record.average_specific_gravity = round(average_specific_gravity,2)


    # Slag Activity Index

    slag_activity_name = fields.Char("Name",default="Slag Activity Index (SAI)")
    slag_activity_7_visible = fields.Boolean("Slag Activity Visible",compute="_compute_visible")
    slag_activity_28_visible = fields.Boolean("Slag Activity Visible",compute="_compute_visible")



    wt_of_cement_slag = fields.Float("Wt. of Cement(g)",default=100)
    wt_of_ggbs_slag = fields.Float("Wt. of GGBS(g)",default=100)
    wt_of_standard_sand_grade1 = fields.Float("Weight of Standard Sand (g) Grade-I",default=200)
    wt_of_standard_sand_grade2 = fields.Float("Weight of Standard Sand (g) Grade-II",default=200)
    wt_of_standard_sand_grade3 = fields.Float("Weight of Standard Sand (g) Grade-III",default=200)
    total_weight_sand = fields.Float("Total Weight",compute="compute_total_weight_sand")
    quantity_of_water = fields.Float("Quantity of Water",compute="_compute_quantity_of_water")
    slag_7days_table = fields.One2many("ggbs.slag.7days.line",'parent_id',string="7 days")
    slag_28days_table = fields.One2many("ggbs.slag.28days.line",'parent_id',string="28 days")
    
    average_7days_slag = fields.Float("Average",compute="_compute_average_7days",store=True)
    average_28days_slag = fields.Float("Average",compute="_compute_average_28days",store=True)


    
    casting_28_name = fields.Char("Name",default="28 Days")
    status_28days = fields.Boolean("Done")
    casting_date_28days = fields.Date(string="Date of Casting")
    testing_date_28days = fields.Date(string="Date of Testing",compute="_compute_testing_date_28days")

    casting_7_name = fields.Char("Name",default="7 Days")
    status_7days = fields.Boolean("Done")
    casting_date_7days = fields.Date(string="Date of Casting")
    testing_date_7days = fields.Date(string="Date of Testing",compute="_compute_testing_date_7days")
    

    @api.depends('slag_7days_table.compressive_strength')
    def _compute_average_7days(self):
        for record in self:
            try:
                record.average_7days_slag = round((sum(record.slag_7days_table.mapped('compressive_strength')) / len(
                    record.slag_7days_table)),2)
            except:
                record.average_7days_slag = 0

    @api.depends('slag_28days_table.compressive_strength')
    def _compute_average_28days(self):
        for record in self:
            try:
                record.average_28days_slag = round((sum(record.slag_28days_table.mapped('compressive_strength')) / len(
                    record.slag_28days_table)),2)
            except:
                record.average_28days_slag = 0



    @api.depends('wt_of_cement_slag','wt_of_ggbs_slag','wt_of_standard_sand_grade1','wt_of_standard_sand_grade2','wt_of_standard_sand_grade3')
    def compute_total_weight_sand(self):
        for record in self:
            record.total_weight_sand = record.wt_of_cement_slag + record.wt_of_ggbs_slag + record.wt_of_standard_sand_grade1 + record.wt_of_standard_sand_grade2 + record.wt_of_standard_sand_grade3


    @api.depends('normal_consistency','total_weight_sand')
    def _compute_quantity_of_water(self):
        for record in self:
            record.quantity_of_water = (((record.normal_consistency/4)+3)/100)*record.total_weight_sand

    @api.depends('casting_date_28days')
    def _compute_testing_date_28days(self):
        for record in self:
            if record.casting_date_28days:
                cast_date = fields.Datetime.from_string(record.casting_date_28days)
                testing_date = cast_date + timedelta(days=28)
                record.testing_date_28days = fields.Datetime.to_string(testing_date)
            else:
                record.testing_date_28days = False

    @api.depends('casting_date_7days')
    def _compute_testing_date_7days(self):
        for record in self:
            if record.casting_date_7days:
                cast_date = fields.Datetime.from_string(record.casting_date_7days)
                testing_date = cast_date + timedelta(days=7)
                record.testing_date_7days = fields.Datetime.to_string(testing_date)
            else:
                record.testing_date_7days = False



    # opc mortar cube 
    wt_of_cement_slag_opc = fields.Float("Wt. of Cement(g)",default=200)
    wt_of_standard_sand_grade1_opc = fields.Float("Weight of Standard Sand (g) Grade-I",default=200)
    wt_of_standard_sand_grade2_opc = fields.Float("Weight of Standard Sand (g) Grade-II",default=200)
    wt_of_standard_sand_grade3_opc = fields.Float("Weight of Standard Sand (g) Grade-III",default=200)
    total_weight_sand_opc = fields.Float("Total Weight",compute="compute_total_weight_sand_opc")
    quantity_of_water_opc = fields.Float("Quantity of Water",compute="_compute_quantity_of_water_opc")

    slag_7days_table_opc = fields.One2many("ggbs.slag.opc.7days.line",'parent_id',string="7 days")
    slag_28days_table_opc = fields.One2many("ggbs.slag.opc.28days.line",'parent_id',string="28 days")
    
    average_7days_slag_opc = fields.Float("Average",compute="_compute_average_7days_opc",store=True)


    average_28days_slag_opc = fields.Float("Average",compute="_compute_average_28days_opc",store=True)
    
    casting_28_name_opc = fields.Char("Name",default="28 Days")
    status_28days_opc = fields.Boolean("Done")
    casting_date_28days_opc = fields.Date(string="Date of Casting")
    testing_date_28days_opc = fields.Date(string="Date of Testing",compute="_compute_testing_date_28days_opc")

    casting_7_name_opc = fields.Char("Name",default="7 Days")
    status_7days_opc = fields.Boolean("Done")
    casting_date_7days_opc = fields.Date(string="Date of Casting")
    testing_date_7days_opc = fields.Date(string="Date of Testing",compute="_compute_testing_date_7days_opc")

    @api.depends('slag_7days_table_opc.compressive_strength')
    def _compute_average_7days_opc(self):
        for record in self:
            try:
                record.average_7days_slag_opc = round((sum(record.slag_7days_table_opc.mapped('compressive_strength')) / len(
                    record.slag_7days_table_opc)),2)
            except:
                record.average_7days_slag_opc = 0

    @api.depends('slag_28days_table_opc.compressive_strength')
    def _compute_average_28days_opc(self):
        for record in self:
            try:
                record.average_28days_slag_opc = round((sum(record.slag_28days_table_opc.mapped('compressive_strength')) / len(
                    record.slag_28days_table_opc)),2)
            except:
                record.average_28days_slag_opc = 0



    @api.depends('wt_of_cement_slag_opc','wt_of_standard_sand_grade1_opc','wt_of_standard_sand_grade2_opc','wt_of_standard_sand_grade3_opc')
    def compute_total_weight_sand_opc(self):
        for record in self:
            record.total_weight_sand_opc = record.wt_of_cement_slag_opc + record.wt_of_standard_sand_grade1_opc + record.wt_of_standard_sand_grade2_opc + record.wt_of_standard_sand_grade3_opc

    @api.depends('normal_consistency_cement','total_weight_sand_opc')
    def _compute_quantity_of_water_opc(self):
        for record in self:
            record.quantity_of_water_opc = (((record.normal_consistency_cement/4)+3)/100)*record.total_weight_sand_opc

    @api.depends('casting_date_28days_opc')
    def _compute_testing_date_28days_opc(self):
        for record in self:
            if record.casting_date_28days_opc:
                cast_date = fields.Datetime.from_string(record.casting_date_28days_opc)
                testing_date = cast_date + timedelta(days=28)
                record.testing_date_28days_opc = fields.Datetime.to_string(testing_date)
            else:
                record.testing_date_28days_opc = False

    @api.depends('casting_date_7days_opc')
    def _compute_testing_date_7days_opc(self):
        for record in self:
            if record.casting_date_7days_opc:
                cast_date = fields.Datetime.from_string(record.casting_date_7days_opc)
                testing_date = cast_date + timedelta(days=7)
                record.testing_date_7days_opc = fields.Datetime.to_string(testing_date)
            else:
                record.testing_date_7days_opc = False

    # conformity field 
    slag_activity_index_7days = fields.Float("Slag Activity Index (SAI) 7 days",compute="_compute_slag_index_7days")
    slag_7days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),
    ], string='Conformity', default='fail',compute="_compute_slag_7days_conformity")

    slag_7days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_slag_7days_nabl")


    @api.depends('slag_activity_index_7days','eln_ref','grade')
    def _compute_slag_7days_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.slag_7days_conformity = 'na'
                continue
            record.slag_7days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1452fgr0-8e67-4e94-86ea-98d9472f5c71')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1452fgr0-8e67-4e94-86ea-98d9472f5c71')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.slag_activity_index_7days - record.slag_activity_index_7days*mu_value
                    upper = record.slag_activity_index_7days + record.slag_activity_index_7days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.slag_7days_conformity = 'pass'
                        break
                    else:
                        record.slag_7days_conformity = 'fail'

    @api.depends('slag_activity_index_7days','eln_ref','grade')
    def _compute_slag_7days_nabl(self):
        
        for record in self:
            record.slag_7days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1452fgr0-8e67-4e94-86ea-98d9472f5c71')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1452fgr0-8e67-4e94-86ea-98d9472f5c71')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.slag_activity_index_7days - record.slag_activity_index_7days*mu_value
                    upper = record.slag_activity_index_7days + record.slag_activity_index_7days*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.slag_7days_nabl = 'pass'
                        break
                    else:
                        record.slag_7days_nabl = 'fail'
    

    slag_activity_index_28days = fields.Float("Slag Activity Index (SAI) 28 days",compute="_compute_slag_index_28days")
    slag_28days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity', default='fail',compute="_compute_slag_28days_conformity")

    slag_28days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_slag_28days_nabl")

    @api.depends('slag_activity_index_28days','eln_ref','grade')
    def _compute_slag_28days_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.slag_28days_conformity = 'na'
                continue
            record.slag_28days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bg21hy20-f42a-4405-b127-b5d84fe78485')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bg21hy20-f42a-4405-b127-b5d84fe78485')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.slag_activity_index_28days - record.slag_activity_index_28days*mu_value
                    upper = record.slag_activity_index_28days + record.slag_activity_index_28days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.slag_28days_conformity = 'pass'
                        break
                    else:
                        record.slag_28days_conformity = 'fail'

    @api.depends('slag_activity_index_28days','eln_ref','grade')
    def _compute_slag_28days_nabl(self):
        
        for record in self:
            record.slag_28days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bg21hy20-f42a-4405-b127-b5d84fe78485')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bg21hy20-f42a-4405-b127-b5d84fe78485')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.slag_activity_index_28days - record.slag_activity_index_28days*mu_value
                    upper = record.slag_activity_index_28days + record.slag_activity_index_28days*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.slag_28days_nabl = 'pass'
                        break
                    else:
                        record.slag_28days_nabl = 'fail'

    @api.depends('average_7days_slag_opc','average_7days_slag')
    def _compute_slag_index_7days(self):
        for record in self:
            if self.average_7days_slag_opc != 0:
                record.slag_activity_index_7days = round(((record.average_7days_slag/record.average_7days_slag_opc)*100),2)
            else:
                record.slag_activity_index_7days = 0


    @api.depends('average_28days_slag_opc','average_28days_slag')
    def _compute_slag_index_28days(self):
        for record in self:
            if self.average_28days_slag_opc != 0:
                record.slag_activity_index_28days = round(((record.average_28days_slag/record.average_28days_slag_opc)*100),2)
            else:
                record.slag_activity_index_28days = 0


    # Fineness by Blaines 

    fineness_name = fields.Char("Name",default="Fineness by Blaines Air Permeability Method")
    fineness_visible = fields.Boolean("Fineness by Blaines Air Permeability Method Visible",compute="_compute_visible")

    fineness_temp = fields.Float("Testing Temperature")

    weight_of_mercury_before_trial1 = fields.Float("Weight of mercury before placing the sample in the permeability cell  (m₁),g." ,default=83.320,digits=(16, 3))
    weight_of_mercury_before_trial2 = fields.Float("Weight of mercury before placing the sample in the permeability cell  (m₁),g.",default=83.340,digits=(16, 3))
    
    weight_of_mercury_after_trail1 = fields.Float("Weight of mercury after placing the sample in the permeability cell  (m₂),g.",default=54.000,digits=(16, 3))
    weight_of_mercury_after_trail2 = fields.Float("Weight of mercury after placing the sample in the permeability cell  (m₂),g.",default=53.990,digits=(16, 3))

    density_of_mercury = fields.Float("Density of mercury , g/cm3",default=13.53,digits=(16, 3))

    bed_volume_trial1 = fields.Float("Bed Volume (V=m₂-m₁/D),cm3.",compute="_compute_bed_volume_trial1",digits=(16, 3))
    bed_volume_trial2 = fields.Float("Bed Volume (V=m₂-m₁/D),cm3.",compute="_compute_bed_volume_trial2",digits=(16, 3))

    average_bed_volume = fields.Float("Average Bed Volume (cm3)",compute="_compute_average_bed_volume",digits=(16, 3))

    difference_between_2_values = fields.Float("Difference between the two Values",compute="_compute_difference_bed_volume",digits=(16, 3))

    mass_of_sample_taken_fineness_reference = fields.Float("mass of sample taken (g)" ,compute="_compute_mass_taken_reference")


    
    time_fineness_trial1 = fields.Float("Time(t),sec.",default=48)
    time_fineness_trial2 = fields.Float("Time(t),sec.",default=47)
    time_fineness_trial3 = fields.Float("Time(t),sec.",default=49)
    # temp_fineness_trial1 = fields.Float("Temp")
    # temp_fineness_trial2 = fields.Float("Temp")
    # temp_fineness_trial3 = fields.Float("Temp")
    average_time_fineness = fields.Float("Average Time(tₒ),Sec",compute="_compute_time_average_fineness")


    specific_surface_of_reference_sample = fields.Float("S0 is the Specific surface of reference sample (m²/kg)",default=274) 
    air_viscosity_of_three_temp = fields.Float("ɳₒ is the Air viscosity at the mean of the three temperatures",default=0.001359,digits=(16, 6))
    density_of_reference_sample = fields.Float("ρ0 is the Density of reference sample  (g/cm3)",default=3.16)
    mean_of_three_measured_times = fields.Float("t0 is the Mean of three measured times (sec)",compute="_compute_mean_measured_time")
    apparatus_constant = fields.Float("Apparatus Constant(k)",compute="_compute_apparatus_constant",digits=(16, 3))

    sg_fineness_calculated = fields.Float("Specific Gravity",compute="_compute_specific_gravity_calculated")
    mass_of_sample_taken_fineness_calculated = fields.Float("mass of sample taken (g)",compute="_compute_mass_sample_calculated")


    time_sample_trial1 = fields.Float("Time(t),sec.")
    time_sample_trial2 = fields.Float("Time(t),sec.")
    time_sample_trial3 = fields.Float("Time(t),sec.")
    temp_fineness_calculated_trial1 = fields.Float("Temp")
    temp_fineness_calculated_trial2 = fields.Float("Temp")
    temp_fineness_calculated_trial3 = fields.Float("Temp")
    average_sample_time = fields.Float("Average Time(tₒ),Sec",compute="_compute_average_sample_time")

    fineness_of_sample = fields.Float("Fineness of Sample",compute="_compute_fineness_of_sample")
    fineness_air_permeability = fields.Float("Fineness By Blaine Air Permeability Method (m2/kg)",compute="_compute_fineness_air_permeability")

    fineness_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Confirmity', default='fail',compute="_compute_fineness_confirmity")
    fineness_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_fineness_nabl")


    @api.depends('fineness_air_permeability','eln_ref','grade')
    def _compute_fineness_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.fineness_confirmity = 'na'
                continue
            record.fineness_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-6b0ff7e69c0a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-6b0ff7e69c0a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.fineness_air_permeability - record.fineness_air_permeability*mu_value
                    upper = record.fineness_air_permeability + record.fineness_air_permeability*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.fineness_confirmity = 'pass'
                        break
                    else:
                        record.fineness_confirmity = 'fail'
    
    @api.depends('fineness_air_permeability','eln_ref','grade')
    def _compute_fineness_nabl(self):
        
        for record in self:
            record.fineness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-6b0ff7e69c0a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-6b0ff7e69c0a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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


    @api.depends('average_bed_volume','density_of_reference_sample')
    def _compute_mass_taken_reference(self):
        self.mass_of_sample_taken_fineness_reference = 0.5*self.average_bed_volume*self.density_of_reference_sample

    @api.depends('time_fineness_trial1','time_fineness_trial2','time_fineness_trial3')
    def _compute_time_average_fineness(self):
        self.average_time_fineness = (self.time_fineness_trial1 + self.time_fineness_trial2 + self.time_fineness_trial3)/3

    @api.depends('specific_surface_of_reference_sample','air_viscosity_of_three_temp','density_of_reference_sample','mean_of_three_measured_times')
    def _compute_apparatus_constant(self):
        if self.mean_of_three_measured_times != 0:
            self.apparatus_constant = round(1.414*self.specific_surface_of_reference_sample*self.density_of_reference_sample*((self.air_viscosity_of_three_temp)/(self.mean_of_three_measured_times**0.5)),3)
        else:
            self.apparatus_constant = 0

    @api.depends('average_specific_gravity')
    def _compute_specific_gravity_calculated(self):
        self.sg_fineness_calculated = self.average_specific_gravity

    @api.depends('average_bed_volume','sg_fineness_calculated')
    def _compute_mass_sample_calculated(self):
        mass_of_sample_taken_fineness_calculated = 0.5*self.average_bed_volume*self.sg_fineness_calculated
        self.mass_of_sample_taken_fineness_calculated = round(mass_of_sample_taken_fineness_calculated,2)

    @api.depends('time_sample_trial1','time_sample_trial2','time_sample_trial3')
    def _compute_average_sample_time(self):
        self.average_sample_time = (self.time_sample_trial1 + self.time_sample_trial2 + self.time_sample_trial3)/3

    @api.depends('apparatus_constant','average_sample_time','sg_fineness_calculated')
    def _compute_fineness_of_sample(self):
        for record in self:
            if record.sg_fineness_calculated != 0:
                print("Apparatus constant",record.apparatus_constant)
                print("Average time",record.average_sample_time)
                print("sg",record.sg_fineness_calculated)
                fineness_of_sample = (521.08*record.apparatus_constant*math.sqrt(record.average_sample_time))/record.sg_fineness_calculated
                record.fineness_of_sample = round(fineness_of_sample,2)
            else:
                record.fineness_of_sample = 0
    
    @api.depends('fineness_of_sample')
    def _compute_fineness_air_permeability(self):
        for record in self:
            record.fineness_air_permeability = math.ceil(record.fineness_of_sample)

    @api.depends('average_time_fineness')
    def _compute_mean_measured_time(self):
        for record in self:
            record.mean_of_three_measured_times = record.average_time_fineness


      ### setting Time,Final Setting Time	

    setting_time_name = fields.Char("Name", default="Setting Time")

    intial_time_lines = fields.One2many('ggbs.initial.time.line','parent_id',string="Initial Time")

    final_time_lines = fields.One2many('ggbs.final.time.line','parent_id',string="Initial Time")

    initial_setting_time_visible = fields.Boolean("Initial Setting Time Visible",compute="_compute_visible")
    initial_setting_time_name = fields.Char("Name",default="Initial Setting Time")

    temp_percent_setting = fields.Float("Temperature °C",digits=(16,1))
    humidity_percent_setting = fields.Float("Humidity %")
    start_date_setting = fields.Date("Start Date")
    end_date_setting = fields.Date("End Date")

    # wt_of_cement_setting_time = fields.Float("Wt. of Cement(g)",default=400)
    # wt_of_water_required_setting_time = fields.Float("Wt.of water required (g) (0.85*P%)" , compute="_compute_wt_of_water_required",store=True )

    # @api.depends('normal_consistency_trial1','wt_of_cement_setting_time')
    # def _compute_wt_of_water_required(self):
    #     for record in self:
    #         record.wt_of_water_required_setting_time =  (((0.85 * record.normal_consistency_trial1) / 100) * record.wt_of_cement_setting_time)

    #Initial setting Time

    
    time_water_added = fields.Datetime("The Time When water is added to cement (t1)",compute="_compute_initial_times",store=True)
    time_needle_fails = fields.Datetime("The time at which needle fails to penetrate the test block to a point 5 ± 0.5 mm (t2)",compute="_compute_initial_times",store=True)
    initial_setting_time_hours = fields.Char("Initial Setting Time (t2-t1) (Hours)", compute="_compute_initial_setting_time")
    initial_setting_time_minutes = fields.Integer("Initial Setting Time Rounded", compute="_compute_initial_setting_time")
    initial_setting_time_minutes_unrounded = fields.Char("Initial Setting Time",compute="_compute_initial_setting_time")

    @api.depends("intial_time_lines.clock_time", "intial_time_lines.serial_no")
    def _compute_initial_times(self):
        for rec in self:
            if rec.intial_time_lines:
                sorted_lines = rec.intial_time_lines.sorted("serial_no")
                rec.time_water_added = sorted_lines[0].clock_time if sorted_lines else False
                rec.time_needle_fails = sorted_lines[-1].clock_time if sorted_lines else False
            else:
                rec.time_water_added = False
                rec.time_needle_fails = False

    initial_setting_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Conformity', default='fail',compute="_compute_initial_setting_conformity")

    initial_setting_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL' ,compute="_compute_initial_setting_nabl" ,store=True)


    @api.depends('initial_setting_time_minutes_unrounded','eln_ref','grade')
    def _compute_initial_setting_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.initial_setting_conformity = 'na'
                continue
            record.initial_setting_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ytre147-30fe-4043-b518-015f5c60d916')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ytre147-30fe-4043-b518-015f5c60d916')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ytre147-30fe-4043-b518-015f5c60d916')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ytre147-30fe-4043-b518-015f5c60d916')]).parameter_table
            
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

    time_needle_make_impression = fields.Datetime("The Time at which the needle make an impression on the surface of test block while attachment fails to do (t3)",compute="_compute_final_time",store=True)
    final_setting_time_hours = fields.Char("Final Setting Time (t3-t1) (Hours)",compute="_compute_final_setting_time")
    final_setting_time_minutes_unrounded = fields.Char("Final Setting Time",compute="_compute_final_setting_time")
    final_setting_time_minutes = fields.Char("Final Setting Time Rounded",compute="_compute_final_setting_time")

    @api.depends("final_time_lines.clock_time1", "final_time_lines.serial_no")
    def _compute_final_time(self):
        for rec in self:
            if rec.final_time_lines:
                # Sort lines by serial_no
                sorted_lines = rec.final_time_lines.sorted("serial_no")
                rec.time_needle_make_impression = sorted_lines[-1].clock_time1
            else:
                rec.time_needle_make_impression = False

    final_setting_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'), ('na', 'NA'),], string='Conformity', default='fail',compute="_compute_final_setting_conformity")

    final_setting_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', compute="_compute_final_setting_nabl")


    @api.depends('final_setting_time_minutes_unrounded','eln_ref','grade')
    def _compute_final_setting_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.final_setting_conformity = 'na'
                continue
            record.final_setting_conformity = 'fail'
            line = self.env['lerm.parameter.master'].search([('internal_id','=','yy1475u-5e9c-4335-9ea2-2d87624c3061')])
            materials = self.env['lerm.parameter.master'].search([('internal_id','=','yy1475u-5e9c-4335-9ea2-2d87624c3061')]).parameter_table
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
            line = self.env['lerm.parameter.master'].search([('internal_id','=','yy1475u-5e9c-4335-9ea2-2d87624c3061')])
            materials = self.env['lerm.parameter.master'].search([('internal_id','=','yy1475u-5e9c-4335-9ea2-2d87624c3061')]).parameter_table
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
                final_setting_time_decimal = time_difference.total_seconds() / 60
                final_setting_time = int(final_setting_time_decimal)
                if final_setting_time % 5 == 0:
                    record.final_setting_time_minutes = final_setting_time
                else:
                    record.final_setting_time_minutes =  round(final_setting_time / 5) * 5
                record.final_setting_time_minutes_unrounded = final_setting_time
            else:
                record.final_setting_time_hours = False
                record.final_setting_time_minutes = False
                record.final_setting_time_minutes_unrounded = False


     # 6. Moisture Content

    moisture_content_name1 = fields.Char("Name",default="Moisture Content")
    moisture_content_visible = fields.Boolean("Silt Content",compute="_compute_visible")

    moisture_content_child_lines = fields.One2many('ggbs.moisture.content.line','parent_id',string="Parameter")

    wet_sand = fields.Float(string="Weight of Wet Sand Sample, (W1)", compute="_compute_avg_moisture_content_lines")
    wet_dry = fields.Float(string="Weight of Dry Sand Sample, (W2)", compute="_compute_avg_moisture_content_lines")
    diff_wd = fields.Float(string="Diff. Between Wet and Dry Sand:- (W1-W2)", compute="_compute_avg_moisture_content_lines")

    @api.depends('moisture_content_child_lines')
    def _compute_avg_moisture_content_lines(self):
        for rec in self:
            # Sort for consistent line order
            lines = rec.moisture_content_child_lines.sorted(key=lambda l: l.serial_no)

            # For wet_sand and wet_dry → only first 2 lines
            selected_lines = lines[:2]
            count_selected = len(selected_lines)

            if count_selected:
                rec.wet_sand = sum(line.wt_sand for line in selected_lines) / count_selected
                rec.wet_dry = sum(line.wt_dry for line in selected_lines) / count_selected
            else:
                rec.wet_sand = rec.wet_dry = 0.0

            # For diff_wd → use all lines
            count_all = len(lines)
            if count_all:
                rec.diff_wd = sum(line.diff_wet_sand for line in lines) / count_all
            else:
                rec.diff_wd = 0.0



    avg_moisture = fields.Float(
        string="Average Moisture Content (%)",
        compute="_compute_avg_moisture",
        store=True )


    @api.depends('diff_wd', 'wet_dry')
    def _compute_avg_moisture(self):
        for rec in self:
            if rec.wet_dry:
                rec.avg_moisture = ((rec.diff_wd  / rec.wet_dry) * 100)
            else:
                rec.avg_moisture = 0.0


    avg_moisture_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_moisture_conformity", store=True)

    @api.depends('avg_moisture','eln_ref','grade')
    def _compute_avg_moisture_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_moisture_conformity = 'na'
                continue
            record.avg_moisture_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4578nhgrr245-3fa3-4b83-ae31-9d281457457hy')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4578nhgrr245-3fa3-4b83-ae31-9d281457457hy')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_moisture - record.avg_moisture*mu_value
                    upper = record.avg_moisture + record.avg_moisture*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_moisture_conformity = 'pass'
                        break
                    else:
                        record.avg_moisture_conformity = 'fail'

    avg_moisture_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_moisture_nabl", store=True)

    @api.depends('avg_moisture','eln_ref','grade')
    def _compute_avg_moisture_nabl(self):
        
        for record in self:
            record.avg_moisture_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4578nhgrr245-3fa3-4b83-ae31-9d281457457hy')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4578nhgrr245-3fa3-4b83-ae31-9d281457457hy')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_moisture - record.avg_moisture*mu_value
                    upper = record.avg_moisture + record.avg_moisture*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_moisture_nabl = 'pass'
                        break
                    else:
                        record.avg_moisture_nabl = 'fail'

    # Soundness By Le-Chatelier Test

    soundness_visible = fields.Boolean("Soundness By Le-Chatelier Test",compute="_compute_visible")
    soundness_name = fields.Char("Name",default="Soundness By Le-Chatelier Test")

    
    temp_soundness = fields.Char("Temp °c" )
    humidity_soundness = fields.Char("Humidity %" )

    soundness_child_lines = fields.One2many('ggbs.soundness.le.chatelier.line','parent_id',string="Soundness By Le-Chatelier Test")

    avg_expansion = fields.Float('Average Expansion (mm)',compute="_compute_avg_expansion")


    @api.depends('soundness_child_lines.expansion')
    def _compute_avg_expansion(self):
        for record in self:
            if record.soundness_child_lines:
              record.avg_expansion = round(sum(record.soundness_child_lines.mapped('expansion'))/ len(record.soundness_child_lines),1)
            else:
                record.avg_expansion = 0.0


    avg_expansion_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_avg_expansion_conformity", store=True)

    @api.depends('avg_expansion','eln_ref','grade')
    def _compute_avg_expansion_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_expansion_conformity = 'na'
                continue
            record.avg_expansion_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78luytr-91b0-4153-87ef-11b6954a9837')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78luytr-91b0-4153-87ef-11b6954a9837')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_expansion - record.avg_expansion*mu_value
                    upper = record.avg_expansion + record.avg_expansion*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_expansion_conformity = 'pass'
                        break
                    else:
                        record.avg_expansion_conformity = 'fail'

    avg_expansion_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_expansion_nabl", store=True)

    @api.depends('avg_expansion','eln_ref','grade')
    def _compute_avg_expansion_nabl(self):
        
        for record in self:
            record.avg_expansion_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78luytr-91b0-4153-87ef-11b6954a9837')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78luytr-91b0-4153-87ef-11b6954a9837')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_expansion - record.avg_expansion*mu_value
                    upper = record.avg_expansion + record.avg_expansion*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_expansion_nabl = 'pass'
                        break
                    else:
                        record.avg_expansion_nabl = 'fail'

    

    ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        

        for record in self:
            record.normal_consistency_visible = False
            record.normal_consistency_cement_visible = False
            record.specific_gravity_visible = False
            record.slag_activity_7_visible = False
            record.slag_activity_28_visible = False

            record.fineness_visible = False
            record.final_setting_time_visible = False
            record.initial_setting_time_visible = False
            record.moisture_content_visible = False
            record.soundness_visible = False

            
            
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '21457801hg-b44a-48cc-9d41-198f55346af0':
                    record.normal_consistency_visible = True
                    record.normal_consistency_cement_visible = True
                if sample.internal_id == '210bgf54-baa4-466f-a6a7-044da708f265':
                    record.specific_gravity_visible = True
                if sample.internal_id == '1452fgr0-8e67-4e94-86ea-98d9472f5c71':
                    record.slag_activity_7_visible = True
                if sample.internal_id == '5214hgtb-c526-4092-a3a7-6b0ff7e69c0a':
                    record.fineness_visible = True
                if sample.internal_id == 'bg21hy20-f42a-4405-b127-b5d84fe78485':
                    record.slag_activity_7_visible = True
                    record.slag_activity_28_visible = True

                if sample.internal_id == 'yy1475u-5e9c-4335-9ea2-2d87624c3061':
                    record.final_setting_time_visible = True
                if sample.internal_id == 'ytre147-30fe-4043-b518-015f5c60d916':
                    record.initial_setting_time_visible = True

                if sample.internal_id == '4578nhgrr245-3fa3-4b83-ae31-9d281457457hy':
                    record.moisture_content_visible = True
                if sample.internal_id == '78luytr-91b0-4153-87ef-11b6954a9837':
                    record.soundness_visible = True


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
        
                    if result.parameter.internal_id == '21457801hg-b44a-48cc-9d41-198f55346af0':
                        result.result_char = self.normal_consistency
                        result.calculated = True
                        continue


                    if result.parameter.internal_id == '210bgf54-baa4-466f-a6a7-044da708f265':
                        result.result_char = self.average_specific_gravity
                        result.calculated = True
                        if self.specific_gravity_nabl == 'pass':
                            result.nabl_status = 'nabl'
                        else:
                            result.nabl_status = 'non-nabl'
                        continue

                    
                    if result.parameter.internal_id == '1452fgr0-8e67-4e94-86ea-98d9472f5c71':
                        result.result_char = self.slag_activity_index_7days
                        result.calculated = True
                        if self.specific_gravity_nabl == 'pass':
                            result.nabl_status = 'nabl'
                        else:
                            result.nabl_status = 'non-nabl'
                        continue


                    if result.parameter.internal_id == '5214hgtb-c526-4092-a3a7-6b0ff7e69c0a':
                        result.result_char = self.fineness_air_permeability
                        result.calculated = True
                        if self.fineness_nabl == 'pass':
                            result.nabl_status = 'nabl'
                        else:
                            result.nabl_status = 'non-nabl'
                        continue


                    if result.parameter.internal_id == 'bg21hy20-f42a-4405-b127-b5d84fe78485':
                        result.result_char = self.slag_activity_index_28days
                        result.calculated = True
                        if self.slag_28days_nabl == 'pass':
                            result.nabl_status = 'nabl'
                        else:
                            result.nabl_status = 'non-nabl'
                        continue

                    if result.parameter.internal_id == '4578nhgrr245-3fa3-4b83-ae31-9d281457457hy':
                        result.result_char = self.avg_moisture
                        result.calculated = True
                        if self.avg_moisture_nabl == 'pass':
                            result.nabl_status = 'nabl'
                        else:
                            result.nabl_status = 'non-nabl'
                        continue

                    if result.parameter.internal_id == 'ytre147-30fe-4043-b518-015f5c60d916':
                        result.result_char = self.initial_setting_time_minutes_unrounded
                        result.calculated = True
                        if self.initial_setting_nabl == 'pass':
                            result.nabl_status = 'nabl'
                        else:
                            result.nabl_status = 'non-nabl'
                        continue

                    if result.parameter.internal_id == 'yy1475u-5e9c-4335-9ea2-2d87624c3061':
                        result.result_char = self.final_setting_time_minutes_unrounded
                        result.calculated = True
                        if self.final_setting_nabl == 'pass':
                            result.nabl_status = 'nabl'
                        else:
                            result.nabl_status = 'non-nabl'
                        continue

                    if result.parameter.internal_id == '78luytr-91b0-4153-87ef-11b6954a9837':
                        result.result_char = self.avg_expansion
                        result.calculated = True
                        if self.avg_expansion_nabl == 'pass':
                            result.nabl_status = 'nabl'
                        else:
                            result.nabl_status = 'non-nabl'
                        continue

                    if result.parameter.internal_id == '5214hgtb-c526-4092-a3a7-321478658':
                        # result.result_char = self.slag_activity_index_28days
                        result.calculated = True

                    if result.parameter.internal_id == '5214hgtb-c526-4092-a3a7-3214855pp':
                        # result.result_char = self.slag_activity_index_28days
                        result.calculated = True



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
        record = super(GgbsMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    def _compute_sample_parameters(self):
        current_user = self.env.user

        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            # Check if user is in Lerm Admin group
            if (
                current_user.has_group('lerm_civil.kes_admin_access_group')
                or current_user.has_group('lerm_civil.lerm_sample_verification')
                or current_user.has_group('lerm_civil.lerm_sample_approval')
            ):
                # Admin sees all parameters
                parameter_ids = record.eln_ref.parameters_result.mapped('parameter').ids
            else:
                # Other users only see parameters assigned to them
                user_param_results = record.eln_ref.parameters_result.filtered(
                    lambda r: r.technician and r.technician.id == current_user.id
                )
                parameter_ids = user_param_results.mapped('parameter').ids

            record.sample_parameters = [(6, 0, parameter_ids)]
    def get_all_fields(self):
        record = self.env['mechanical.ggbs'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    notes_id = fields.One2many('mechanical.ggbs.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

    @api.model
    def _default_notes_lines(self):
        return [
            (0, 0, {
                'sr_no': 'i',
                'notes': 'Attention is drawn to the limitations of liability, indemnification, and jurisdiction provisions applicable to this report. The information contained herein reflects the findings of Geonyms India Private Limited at the time of testing and only within the scope of work and instructions received from the Client, where applicable',
            }),
            (0, 0, {
                'sr_no': 'ii',
                'notes': 'The Companys responsibility is limited to the Client for whom this report has been issued. This report does not relieve any party from exercising its rights and fulfilling its obligations under any contract, agreement, or applicable statutory requirements. Unless otherwise stated, the results reported herein relate only to the sample(s) tested and do not necessarily indicate the quality of the entire lot, batch, or material from which the sample(s) were drawn. ',
            }),
            (0, 0, {
                'sr_no': 'iii',
                'notes': 'The sample(s) tested shall be retained for a period of ninety (90) days from the date of issue of this report unless otherwise agreed with the Client. This report shall not be reproduced, except in full, without the prior written approval of Geonyms India Private Limited. ',
            }),
            (0, 0, {
                'sr_no': 'iv',
                'notes': 'Partial reproduction, unauthorized alteration, forgery, falsification, or misuse of this report is prohibited and may result in legal action.',
            }),

            (0, 0, {
                'sr_no': 'v',
                'notes': ' Any complaint concerning this report shall be submitted in writing within fifteen (15) days from the date of issue of the report. The use of this report or extracts thereof in advertisements, promotional material, media publications, or any public disclosure requires prior written approval from Geonyms India Private Limited',
            }),
        ]

class GgbsTest(models.Model):
    _name = "mechanical.ggbs.test"
    _rec_name = "name"
    name = fields.Char("Name")


class GgbsSlag7DaysLine(models.Model):
    _name = "ggbs.slag.7days.line"

    parent_id = fields.Many2one('mechanical.ggbs')

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
                compressive_strength = ((record.crushing_load / record.crosssectional_area)*1000)
                record.compressive_strength = round(compressive_strength,3)
            else:
                record.compressive_strength = 0


class GgbsSlag28DaysLine(models.Model):
    _name = "ggbs.slag.28days.line"

    parent_id = fields.Many2one('mechanical.ggbs')

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
                compressive_strength = ((record.crushing_load / record.crosssectional_area)*1000)
                record.compressive_strength = round(compressive_strength,3)
            else:
                record.compressive_strength = 0


class GgbsSlagOpc7DaysLine(models.Model):
    _name = "ggbs.slag.opc.7days.line"

    parent_id = fields.Many2one('mechanical.ggbs')

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
                compressive_strength = ((record.crushing_load / record.crosssectional_area)*1000)
                record.compressive_strength = round(compressive_strength,3)
            else:
                record.compressive_strength = 0


class GgbsSlagOpc28DaysLine(models.Model):
    _name = "ggbs.slag.opc.28days.line"

    parent_id = fields.Many2one('mechanical.ggbs')

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
                compressive_strength = ((record.crushing_load / record.crosssectional_area)*1000)
                record.compressive_strength = round(compressive_strength,3)
            else:
                record.compressive_strength = 0


class InitialTimeLine(models.Model):
    _name = "ggbs.initial.time.line"
    parent_id = fields.Many2one('mechanical.ggbs',string="Parent Id")

    serial_no = fields.Integer(string="Sr.No", readonly=True, copy=False, default=1)

   
    
    clock_time = fields.Datetime(string="Date & Time")
    penetration_intial = fields.Float(string="Penetration Of Needle")

    


    

   


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(InitialTimeLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class FinalTimeLine(models.Model):
    _name = "ggbs.final.time.line"
    parent_id = fields.Many2one('mechanical.ggbs',string="Parent Id")

    serial_no = fields.Integer(string="Sr.No", readonly=True, copy=False, default=1)

   
    
    clock_time1 = fields.Datetime(string="Date & Time")
    impression_intial1 = fields.Float(string="Impression Of Needle")

    


    

   


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(FinalTimeLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class MoistureContentLine(models.Model):
    _name = "ggbs.moisture.content.line"
    parent_id = fields.Many2one('mechanical.ggbs',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    wt_sand = fields.Float(string="Weight of Wet Sand Sample, (W1)")
    wt_dry = fields.Float(string="Weight of Dry Sand Sample, (W2)")
    diff_wet_sand = fields.Float(string="Diff. Between Wet and Dry Sand:- (W1-W2)",compute="_compute_moisture_content")
    # moisture_content = fields.Float(string="Moisture ContentLine % = ((W1-W2)/W2) x 100",compute="_compute_moisture_content")

    @api.depends('wt_sand', 'wt_dry')
    def _compute_moisture_content(self):
        for rec in self:
            A = rec.wt_sand
            B = rec.wt_dry

            if A and B:
                rec.diff_wet_sand = A - B
            else:
                rec.diff_wet_sand = 0.0

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(MoistureContentLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class SoundnessLeChatelierLine(models.Model):	
    _name= "ggbs.soundness.le.chatelier.line"
    parent_id = fields.Many2one('mechanical.ggbs',string="Parent Id")

    sr_no = fields.Integer(string="Sr.NO", readonly=True, copy=False, default=1)

    mould_no = fields.Char("Mould No.")
    initial_read = fields.Float("Initial Reading of Indicator Point Before Boiling (A) in mm")
    final_read = fields.Float("Final Reading of Indicator Point After 3 Hrs. Boiling (B) in mm")
    expansion = fields.Float(string="Expansion (B – A) mm",compute="_compute_expansion")


    @api.depends('initial_read','final_read')
    def _compute_expansion(self):
        for record in self:
            record.expansion = (record.final_read - record.initial_read)


		



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(SoundnessLeChatelierLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1





    

class GgbsMechanicalNotes(models.Model):
    _name = "mechanical.ggbs.notes"

    parent_id = fields.Many2one('mechanical.ggbs', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
