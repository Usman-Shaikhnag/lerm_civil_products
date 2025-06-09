from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class GgbsMechanical(models.Model):
    _name = "mechanical.ggbs1"
    _inherit = "lerm.eln"
    _description = 'mechanical.ggbs1'
    _rec_name = "name"


    name = fields.Char("Name",default="GGBS")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.ggbs.test1",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)


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
    slag_7days_table = fields.One2many("ggbs.slag.7days.line1",'parent_id',string="7 days")
    slag_28days_table = fields.One2many("ggbs.slag.28days.line1",'parent_id',string="28 days")
    
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

    slag_7days_table_opc = fields.One2many("ggbs.slag.opc.7days.line1",'parent_id',string="7 days")
    slag_28days_table_opc = fields.One2many("ggbs.slag.opc.28days.line1",'parent_id',string="28 days")
    
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
        ('not_applicable', 'Not Applicable'),
    ], string='Conformity', default='fail',compute="_compute_slag_7days_conformity")

    slag_7days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_slag_7days_nabl")


    @api.depends('slag_activity_index_7days','eln_ref','grade')
    def _compute_slag_7days_conformity(self):
        for record in self:
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
        ('not_applicable', 'Not Applicable'),
    ], string='Conformity', default='fail',compute="_compute_slag_28days_conformity")

    slag_28days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_slag_28days_nabl")

    @api.depends('slag_activity_index_28days','eln_ref','grade')
    def _compute_slag_28days_conformity(self):
        for record in self:
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
        ('not_applicable', 'Not Applicable'),
    ], string='Confirmity', default='fail',compute="_compute_fineness_confirmity")
    fineness_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_fineness_nabl")


    @api.depends('fineness_air_permeability','eln_ref','grade')
    def _compute_fineness_confirmity(self):
        for record in self:
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


    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
                    if result.parameter.internal_id == '21457801hg-b44a-48cc-9d41-198f55346af0':
                        result.result_char = self.normal_consistency
                        continue
                    if result.parameter.internal_id == '210bgf54-baa4-466f-a6a7-044da708f265':
                        result.result_char = self.average_specific_gravity
                        if self.specific_gravity_nabl == 'pass':
                            result.nabl_status = 'nabl'
                        else:
                            result.nabl_status = 'non-nabl'
                        continue
                    if result.parameter.internal_id == '1452fgr0-8e67-4e94-86ea-98d9472f5c71':
                        result.result_char = self.slag_activity_index_7days
                        if self.specific_gravity_nabl == 'pass':
                            result.nabl_status = 'nabl'
                        else:
                            result.nabl_status = 'non-nabl'
                        continue
                    if result.parameter.internal_id == '5214hgtb-c526-4092-a3a7-6b0ff7e69c0a':
                        result.result_char = self.fineness_air_permeability
                        if self.fineness_nabl == 'pass':
                            result.nabl_status = 'nabl'
                        else:
                            result.nabl_status = 'non-nabl'
                        continue
                    if result.parameter.internal_id == 'bg21hy20-f42a-4405-b127-b5d84fe78485':
                        result.result_char = self.slag_activity_index_28days
                        if self.slag_28days_nabl == 'pass':
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
        # import wdb;wdb.set_trace()
        record = super(GgbsMechanical, self).create(vals)
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
        record = self.env['mechanical.ggbs1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

class GgbsTest(models.Model):
    _name = "mechanical.ggbs.test1"
    _rec_name = "name"
    name = fields.Char("Name")


class GgbsSlag7DaysLine(models.Model):
    _name = "ggbs.slag.7days.line1"

    parent_id = fields.Many2one('mechanical.ggbs1')

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
    _name = "ggbs.slag.28days.line1"

    parent_id = fields.Many2one('mechanical.ggbs1')

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
    _name = "ggbs.slag.opc.7days.line1"

    parent_id = fields.Many2one('mechanical.ggbs1')

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
    _name = "ggbs.slag.opc.28days.line1"

    parent_id = fields.Many2one('mechanical.ggbs1')

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
