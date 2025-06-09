from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math



class Door(models.Model):
    _name = "mechanical.door1"
    _inherit = "lerm.eln"
    _description = 'mechanical.door1'
    _rec_name = "name"

    name = fields.Char("Name",default="DOOR")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    #  Length
    
    door_length_name = fields.Char("Name",default="Length")
    door_length_visible = fields.Boolean("Surface Quality",compute="_compute_visible") 

    lenght_observations1 = fields.Float(string="Observations")
    lenght_observations2 = fields.Float(string="Observations")
    lenght_observations3 = fields.Float(string="Observations")
    lenght_observations4 = fields.Float(string="Observations")
    

    door_length_avg = fields.Float(string="Length, mm",compute="_compute_door_length_avg")


    @api.depends('lenght_observations1', 'lenght_observations2', 'lenght_observations3', 'lenght_observations4')
    def _compute_door_length_avg(self):
        for record in self:
            values = [record.lenght_observations1, record.lenght_observations2, record.lenght_observations3, record.lenght_observations4]
            total = sum(value for value in values if value)
            count = sum(1 for value in values if value)
            record.door_length_avg = total / count if count > 0 else 0

    door_length_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Length Conformity", compute="_compute_door_length_avg_conformity", store=True)



    @api.depends('door_length_avg','eln_ref','grade')
    def _compute_door_length_avg_conformity(self):
        
        for record in self:
            record.door_length_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cd31c1fa-aac8-4a92-b56e-37ace7f01f13')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cd31c1fa-aac8-4a92-b56e-37ace7f01f13')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.door_length_avg - record.door_length_avg*mu_value
                    upper = record.door_length_avg + record.door_length_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.door_length_avg_conformity = 'pass'
                        break
                    else:
                        record.door_length_avg_conformity = 'fail'

    door_length_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Length NABL", compute="_compute_door_length_avg_nabl", store=True)

    @api.depends('door_length_avg','eln_ref','grade')
    def _compute_door_length_avg_nabl(self):
        
        for record in self:
            record.door_length_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cd31c1fa-aac8-4a92-b56e-37ace7f01f13')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cd31c1fa-aac8-4a92-b56e-37ace7f01f13')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.door_length_avg - record.door_length_avg*mu_value
                    upper = record.door_length_avg + record.door_length_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.door_length_avg_nabl = 'pass'
                        break
                    else:
                        record.door_length_avg_nabl = 'fail'


     #  Width
    
    door_width_name = fields.Char("Name",default="Width")
    door_width_visible = fields.Boolean("Surface Quality",compute="_compute_visible") 

    width_observations1 = fields.Float(string="Observations")
    width_observations2 = fields.Float(string="Observations")
    width_observations3 = fields.Float(string="Observations")
    width_observations4 = fields.Float(string="Observations")
    

    door_width_avg = fields.Float(string="Width, mm",compute="_compute_door_width_avg")


    @api.depends('width_observations1', 'width_observations2', 'width_observations3', 'width_observations4')
    def _compute_door_width_avg(self):
        for record in self:
            values = [record.width_observations1, record.width_observations2, record.width_observations3, record.width_observations4]
            total = sum(value for value in values if value)
            count = sum(1 for value in values if value)
            record.door_width_avg = total / count if count > 0 else 0


    door_width_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Length Conformity", compute="_compute_door_width_avg_conformity", store=True)



    @api.depends('door_width_avg','eln_ref','grade')
    def _compute_door_width_avg_conformity(self):
        
        for record in self:
            record.door_width_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','426149cc-ee30-45bb-a7df-db54327c2de1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','426149cc-ee30-45bb-a7df-db54327c2de1')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.door_width_avg - record.door_width_avg*mu_value
                    upper = record.door_width_avg + record.door_width_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.door_width_avg_conformity = 'pass'
                        break
                    else:
                        record.door_width_avg_conformity = 'fail'

    door_width_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Length NABL", compute="_compute_door_width_avg_nabl", store=True)

    @api.depends('door_width_avg','eln_ref','grade')
    def _compute_door_width_avg_nabl(self):
        
        for record in self:
            record.door_width_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','426149cc-ee30-45bb-a7df-db54327c2de1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','426149cc-ee30-45bb-a7df-db54327c2de1')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.door_width_avg - record.door_width_avg*mu_value
                    upper = record.door_width_avg + record.door_width_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.door_width_avg_nabl = 'pass'
                        break
                    else:
                        record.door_width_avg_nabl = 'fail'


    #  Thickness
    
    door_thickess_name = fields.Char("Name",default="Thickness")
    door_thickess_visible = fields.Boolean("Surface Quality",compute="_compute_visible") 

    thickess_observations1 = fields.Float(string="Observations")
    thickess_observations2 = fields.Float(string="Observations")
    thickess_observations3 = fields.Float(string="Observations")
    thickess_observations4 = fields.Float(string="Observations")
    thickess_observations5 = fields.Float(string="Observations")
    thickess_observations6 = fields.Float(string="Observations")
    

    door_thickess_avg = fields.Float(string="Thickess, mm",compute="_compute_door_thickess_avg")


    @api.depends('thickess_observations1', 'thickess_observations2', 'thickess_observations3', 'thickess_observations4','thickess_observations5','thickess_observations6')
    def _compute_door_thickess_avg(self):
        for record in self:
            values = [record.thickess_observations1, record.thickess_observations2, record.thickess_observations3, record.thickess_observations4,record.thickess_observations5,record.thickess_observations6]
            total = sum(value for value in values if value)
            count = sum(1 for value in values if value)
            record.door_thickess_avg = total / count if count > 0 else 0

    door_thickess_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Length Conformity", compute="_compute_door_thickess_avg_conformity", store=True)



    @api.depends('door_thickess_avg','eln_ref','grade')
    def _compute_door_thickess_avg_conformity(self):
        
        for record in self:
            record.door_thickess_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','80bacb3a-e725-4651-b476-3b1cc3fdd405')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','80bacb3a-e725-4651-b476-3b1cc3fdd405')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.door_thickess_avg - record.door_thickess_avg*mu_value
                    upper = record.door_thickess_avg + record.door_thickess_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.door_thickess_avg_conformity = 'pass'
                        break
                    else:
                        record.door_thickess_avg_conformity = 'fail'

    door_thickess_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Length NABL", compute="_compute_door_thickess_avg_nabl", store=True)

    @api.depends('door_thickess_avg','eln_ref','grade')
    def _compute_door_thickess_avg_nabl(self):
        
        for record in self:
            record.door_thickess_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','80bacb3a-e725-4651-b476-3b1cc3fdd405')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','80bacb3a-e725-4651-b476-3b1cc3fdd405')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.door_thickess_avg - record.door_thickess_avg*mu_value
                    upper = record.door_thickess_avg + record.door_thickess_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.door_thickess_avg_nabl = 'pass'
                        break
                    else:
                        record.door_thickess_avg_nabl = 'fail'

       #  Squareness
    
    door_squareness_name = fields.Char("Name",default="Squareness")
    door_squareness_visible = fields.Boolean("Squareness",compute="_compute_visible") 

    squareness_observations1 = fields.Float(string="Observations")
    squareness_observations2 = fields.Float(string="Observations")
    squareness_observations3 = fields.Float(string="Observations")
    squareness_observations4 = fields.Float(string="Observations")
    

    door_squareness_avg = fields.Float(string="Squareness, mm",compute="_compute_door_squareness_avg")


    @api.depends('squareness_observations1', 'squareness_observations2', 'squareness_observations3', 'squareness_observations4')
    def _compute_door_squareness_avg(self):
        for record in self:
            values = [record.squareness_observations1, record.squareness_observations2, record.squareness_observations3, record.squareness_observations4]
            total = sum(value for value in values if value)
            count = sum(1 for value in values if value)
            record.door_squareness_avg = total / count if count > 0 else 0

    door_squareness_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Length Conformity", compute="_compute_door_squareness_avg_conformity", store=True)



    @api.depends('door_squareness_avg','eln_ref','grade')
    def _compute_door_squareness_avg_conformity(self):
        
        for record in self:
            record.door_squareness_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7f15645f-2d9f-4797-9a0f-978913968fd7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7f15645f-2d9f-4797-9a0f-978913968fd7')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.door_squareness_avg - record.door_squareness_avg*mu_value
                    upper = record.door_squareness_avg + record.door_squareness_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.door_squareness_avg_conformity = 'pass'
                        break
                    else:
                        record.door_squareness_avg_conformity = 'fail'

    door_squareness_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Length NABL", compute="_compute_door_squareness_avg_nabl", store=True)

    @api.depends('door_squareness_avg','eln_ref','grade')
    def _compute_door_squareness_avg_nabl(self):
        
        for record in self:
            record.door_squareness_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7f15645f-2d9f-4797-9a0f-978913968fd7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7f15645f-2d9f-4797-9a0f-978913968fd7')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.door_squareness_avg - record.door_squareness_avg*mu_value
                    upper = record.door_squareness_avg + record.door_squareness_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.door_squareness_avg_nabl = 'pass'
                        break
                    else:
                        record.door_squareness_avg_nabl = 'fail'



      # General Flatness Test
    
    door_general_flatness_name = fields.Char("Name",default="General Flatness Test")
    door_general_flatness_visible = fields.Boolean("General Flatness Test",compute="_compute_visible") 

    cupping_observations1 = fields.Float(string="Observations")
    cupping_observations2 = fields.Float(string="Observations")

    door_cupping_avg = fields.Float(string="General Flatness, Cupping ,mm",compute="_compute_door_cupping_avg",digits=(12,3))

    door_cupping_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Cupping Conformity", compute="_compute_door_cupping_avg_conformity", store=True)



    @api.depends('door_cupping_avg','eln_ref','grade')
    def _compute_door_cupping_avg_conformity(self):
        
        for record in self:
            record.door_cupping_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0a4af69d-a9b4-41f7-976b-0645cfb1d9fd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0a4af69d-a9b4-41f7-976b-0645cfb1d9fd')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.door_cupping_avg - record.door_cupping_avg*mu_value
                    upper = record.door_cupping_avg + record.door_cupping_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.door_cupping_avg_conformity = 'pass'
                        break
                    else:
                        record.door_cupping_avg_conformity = 'fail'

    door_cupping_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Cupping NABL", compute="_compute_door_cupping_avg_nabl", store=True)

    @api.depends('door_cupping_avg','eln_ref','grade')
    def _compute_door_cupping_avg_nabl(self):
        
        for record in self:
            record.door_cupping_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0a4af69d-a9b4-41f7-976b-0645cfb1d9fd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0a4af69d-a9b4-41f7-976b-0645cfb1d9fd')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.door_cupping_avg - record.door_cupping_avg*mu_value
                    upper = record.door_cupping_avg + record.door_cupping_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.door_cupping_avg_nabl = 'pass'
                        break
                    else:
                        record.door_cupping_avg_nabl = 'fail'


    @api.depends('cupping_observations1', 'cupping_observations2')
    def _compute_door_cupping_avg(self):
        for record in self:
            values = [record.cupping_observations1, record.cupping_observations2]
            total = sum(value for value in values if value)
            count = sum(1 for value in values if value)
            record.door_cupping_avg = total / count if count > 0 else 0

    warping_observations1 = fields.Float(string="Observations")
    warping_observations2 = fields.Float(string="Observations")

    door_warping_avg = fields.Float(string="General Flatness, Warping ,mm",compute="_compute_door_warping_avg",digits=(12,2))

    door_warping_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Warping Conformity", compute="_compute_door_warping_avg_conformity", store=True)



    @api.depends('door_warping_avg','eln_ref','grade')
    def _compute_door_warping_avg_conformity(self):
        
        for record in self:
            record.door_warping_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6e5bbea-ef22-4f8e-89cd-39a60007aced')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6e5bbea-ef22-4f8e-89cd-39a60007aced')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.door_warping_avg - record.door_warping_avg*mu_value
                    upper = record.door_warping_avg + record.door_warping_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.door_warping_avg_conformity = 'pass'
                        break
                    else:
                        record.door_warping_avg_conformity = 'fail'

    door_warping_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Warping NABL", compute="_compute_door_warping_avg_nabl", store=True)

    @api.depends('door_warping_avg','eln_ref','grade')
    def _compute_door_warping_avg_nabl(self):
        
        for record in self:
            record.door_warping_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6e5bbea-ef22-4f8e-89cd-39a60007aced')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6e5bbea-ef22-4f8e-89cd-39a60007aced')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.door_warping_avg - record.door_warping_avg*mu_value
                    upper = record.door_warping_avg + record.door_warping_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.door_warping_avg_nabl = 'pass'
                        break
                    else:
                        record.door_warping_avg_nabl = 'fail'


    @api.depends('warping_observations1', 'warping_observations2')
    def _compute_door_warping_avg(self):
        for record in self:
            values = [record.warping_observations1, record.warping_observations2]
            total = sum(value for value in values if value)
            count = sum(1 for value in values if value)
            record.door_warping_avg = total / count if count > 0 else 0

    twisting_observations1 = fields.Float(string="Observations")
    twisting_observations2 = fields.Float(string="Observations")

    door_twisting_avg = fields.Float(string="General Flatness, Twisting ,mm",compute="_compute_door_twisting_avg",digits=(12,1))

    door_twisting_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Twisting Conformity", compute="_compute_door_twisting_avg_conformity", store=True)



    @api.depends('door_twisting_avg','eln_ref','grade')
    def _compute_door_twisting_avg_conformity(self):
        
        for record in self:
            record.door_twisting_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','86105e60-82a1-4578-bc7b-286cae494b41')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','86105e60-82a1-4578-bc7b-286cae494b41')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.door_twisting_avg - record.door_twisting_avg*mu_value
                    upper = record.door_twisting_avg + record.door_twisting_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.door_twisting_avg_conformity = 'pass'
                        break
                    else:
                        record.door_twisting_avg_conformity = 'fail'

    door_twisting_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Twisting NABL", compute="_compute_door_twisting_avg_nabl", store=True)

    @api.depends('door_twisting_avg','eln_ref','grade')
    def _compute_door_twisting_avg_nabl(self):
        
        for record in self:
            record.door_twisting_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','86105e60-82a1-4578-bc7b-286cae494b41')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','86105e60-82a1-4578-bc7b-286cae494b41')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.door_twisting_avg - record.door_twisting_avg*mu_value
                    upper = record.door_twisting_avg + record.door_twisting_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.door_twisting_avg_nabl = 'pass'
                        break
                    else:
                        record.door_twisting_avg_nabl = 'fail'


    @api.depends('twisting_observations1', 'twisting_observations2')
    def _compute_door_twisting_avg(self):
        for record in self:
            values = [record.twisting_observations1, record.twisting_observations2]
            total = sum(value for value in values if value)
            count = sum(1 for value in values if value)
            record.door_twisting_avg = total / count if count > 0 else 0


       # Local Planeness Test
    
    door_local_planeness_name = fields.Char("Name",default="Local Planeness Test")
    door_local_planeness_visible = fields.Boolean("Local Planeness Test",compute="_compute_visible") 

    local_planeness_observations1 = fields.Float(string="Observations")
    local_planeness_observations2 = fields.Float(string="Observations")
    local_planeness_observations3 = fields.Float(string="Observations")
    local_planeness_observations4 = fields.Float(string="Observations")
    local_planeness_observations5 = fields.Float(string="Observations")
    local_planeness_observations6 = fields.Float(string="Observations")
    local_planeness_observations7 = fields.Float(string="Observations")
    local_planeness_observations8 = fields.Float(string="Observations")
    local_planeness_observations9 = fields.Float(string="Observations")
    local_planeness_observations10 = fields.Float(string="Observations")
    

    door_local_planeness_avg = fields.Float(string="Local Planeness, mm",compute="_compute_door_local_planeness_avg")

    door_local_planeness_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Local Planeness Conformity", compute="_compute_door_local_planeness_avg_conformity", store=True)



    @api.depends('door_local_planeness_avg','eln_ref','grade')
    def _compute_door_local_planeness_avg_conformity(self):
        
        for record in self:
            record.door_local_planeness_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0020e36c-0431-4859-8713-5e40c743e23b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0020e36c-0431-4859-8713-5e40c743e23b')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.door_local_planeness_avg - record.door_local_planeness_avg*mu_value
                    upper = record.door_local_planeness_avg + record.door_local_planeness_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.door_local_planeness_avg_conformity = 'pass'
                        break
                    else:
                        record.door_local_planeness_avg_conformity = 'fail'

    door_local_planeness_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Local Planeness NABL", compute="_compute_door_local_planeness_avg_nabl", store=True)

    @api.depends('door_local_planeness_avg','eln_ref','grade')
    def _compute_door_local_planeness_avg_nabl(self):
        
        for record in self:
            record.door_local_planeness_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0020e36c-0431-4859-8713-5e40c743e23b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0020e36c-0431-4859-8713-5e40c743e23b')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.door_local_planeness_avg - record.door_local_planeness_avg*mu_value
                    upper = record.door_local_planeness_avg + record.door_local_planeness_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.door_local_planeness_avg_nabl = 'pass'
                        break
                    else:
                        record.door_local_planeness_avg_nabl = 'fail'


    @api.depends('local_planeness_observations1', 'local_planeness_observations2', 'local_planeness_observations3', 'local_planeness_observations4','local_planeness_observations5','local_planeness_observations6','local_planeness_observations7','local_planeness_observations8','local_planeness_observations9','local_planeness_observations10')
    def _compute_door_local_planeness_avg(self):
        for record in self:
            values = [record.local_planeness_observations1, record.local_planeness_observations2, record.local_planeness_observations3, record.local_planeness_observations4,record.local_planeness_observations5,record.local_planeness_observations6,record.local_planeness_observations7,record.local_planeness_observations8,record.local_planeness_observations9,record.local_planeness_observations10]
            total = sum(value for value in values if value)
            count = sum(1 for value in values if value)
            record.door_local_planeness_avg = total / count if count > 0 else 0


     # Impact Indentation Test
    
    door_impact_name = fields.Char("Name",default="Impact Indentation Test")
    door_impact_visible = fields.Boolean("Impact Indentation Test",compute="_compute_visible") 

    impact_observations1 = fields.Float(string="Observations")
    impact_observations2 = fields.Float(string="Observations")
    impact_observations3 = fields.Float(string="Observations")
    impact_observations4 = fields.Float(string="Observations")
    impact_observations5 = fields.Float(string="Observations")
    impact_observations6 = fields.Float(string="Observations")
    impact_observations7 = fields.Float(string="Observations")
    impact_observations8 = fields.Float(string="Observations")
    impact_observations9 = fields.Float(string="Observations")
    impact_observations10 = fields.Float(string="Observations")
    

    door_impact_avg = fields.Float(string="Local Planeness, mm",compute="_compute_door_impact_avg")

    door_impact_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Impact Indentation Conformity", compute="_compute_door_impact_avg_conformity", store=True)



    @api.depends('door_impact_avg','eln_ref','grade')
    def _compute_door_impact_avg_conformity(self):
        
        for record in self:
            record.door_impact_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf8130ff-d00f-44c6-8216-da112646962c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf8130ff-d00f-44c6-8216-da112646962c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.door_impact_avg - record.door_impact_avg*mu_value
                    upper = record.door_impact_avg + record.door_impact_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.door_impact_avg_conformity = 'pass'
                        break
                    else:
                        record.door_impact_avg_conformity = 'fail'

    door_impact_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Impact Indentation NABL", compute="_compute_door_impact_avg_nabl", store=True)

    @api.depends('door_impact_avg','eln_ref','grade')
    def _compute_door_impact_avg_nabl(self):
        
        for record in self:
            record.door_impact_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf8130ff-d00f-44c6-8216-da112646962c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf8130ff-d00f-44c6-8216-da112646962c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.door_impact_avg - record.door_impact_avg*mu_value
                    upper = record.door_impact_avg + record.door_impact_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.door_impact_avg_nabl = 'pass'
                        break
                    else:
                        record.door_impact_avg_nabl = 'fail'


    @api.depends('impact_observations1', 'impact_observations2', 'impact_observations3', 'impact_observations4','impact_observations5','impact_observations6','impact_observations7','impact_observations8','impact_observations9','impact_observations10')
    def _compute_door_impact_avg(self):
        for record in self:
            values = [record.impact_observations1, record.impact_observations2, record.impact_observations3, record.impact_observations4,record.impact_observations5,record.impact_observations6,record.impact_observations7,record.impact_observations8,record.impact_observations9,record.impact_observations10]
            total = sum(value for value in values if value)
            count = sum(1 for value in values if value)
            record.door_impact_avg = total / count if count > 0 else 0


       # Edge Loading Test

    edge_loading_name = fields.Char("Name",default="Edge Loading Test")
    edge_loading_visible = fields.Boolean("Edge Loading Test",compute="_compute_visible")  

    edge_loading_obsrvetions1 = fields.Float(string="Edge Loading- Defelection at the loaded Edge after 15minutes of application of the load")
    edge_loading_obsrvetions2 = fields.Float(string="Edge Loading- Deflection at the Loaded edge at 3minutes after removal of the load")

    edge_loading_obsrvetions1_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Edge Loading Obsrvetions 1 Conformity", compute="_compute_edge_loading_obsrvetions1_conformity", store=True)



    @api.depends('edge_loading_obsrvetions1','eln_ref','grade')
    def _compute_edge_loading_obsrvetions1_conformity(self):
        
        for record in self:
            record.edge_loading_obsrvetions1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a90fc7e-17dc-4517-be7a-d94522ebb1bf')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a90fc7e-17dc-4517-be7a-d94522ebb1bf')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.edge_loading_obsrvetions1 - record.edge_loading_obsrvetions1*mu_value
                    upper = record.edge_loading_obsrvetions1 + record.edge_loading_obsrvetions1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.edge_loading_obsrvetions1_conformity = 'pass'
                        break
                    else:
                        record.edge_loading_obsrvetions1_conformity = 'fail'

    edge_loading_obsrvetions1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Edge Loading Obsrvetions 1 NABL", compute="_compute_edge_loading_obsrvetions1_nabl", store=True)

    @api.depends('edge_loading_obsrvetions1','eln_ref','grade')
    def _compute_edge_loading_obsrvetions1_nabl(self):
        
        for record in self:
            record.edge_loading_obsrvetions1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a90fc7e-17dc-4517-be7a-d94522ebb1bf')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a90fc7e-17dc-4517-be7a-d94522ebb1bf')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.edge_loading_obsrvetions1 - record.edge_loading_obsrvetions1*mu_value
                    upper = record.edge_loading_obsrvetions1 + record.edge_loading_obsrvetions1*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.edge_loading_obsrvetions1_nabl = 'pass'
                        break
                    else:
                        record.edge_loading_obsrvetions1_nabl = 'fail'

    edge_loading_obsrvetions2_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Edge Loading Obsrvetions 2 Conformity", compute="_compute_edge_loading_obsrvetions2_conformity", store=True)



    @api.depends('edge_loading_obsrvetions2','eln_ref','grade')
    def _compute_edge_loading_obsrvetions2_conformity(self):
        
        for record in self:
            record.edge_loading_obsrvetions2_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ffa12329-b217-4f34-87a4-f4cdd3f43d92')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ffa12329-b217-4f34-87a4-f4cdd3f43d92')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.edge_loading_obsrvetions2 - record.edge_loading_obsrvetions2*mu_value
                    upper = record.edge_loading_obsrvetions2 + record.edge_loading_obsrvetions2*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.edge_loading_obsrvetions2_conformity = 'pass'
                        break
                    else:
                        record.edge_loading_obsrvetions2_conformity = 'fail'

    edge_loading_obsrvetions2_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Edge Loading Obsrvetions 2 NABL", compute="_compute_edge_loading_obsrvetions2_nabl", store=True)

    @api.depends('edge_loading_obsrvetions2','eln_ref','grade')
    def _compute_edge_loading_obsrvetions2_nabl(self):
        
        for record in self:
            record.edge_loading_obsrvetions2_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ffa12329-b217-4f34-87a4-f4cdd3f43d92')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ffa12329-b217-4f34-87a4-f4cdd3f43d92')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.edge_loading_obsrvetions2 - record.edge_loading_obsrvetions2*mu_value
                    upper = record.edge_loading_obsrvetions2 + record.edge_loading_obsrvetions2*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.edge_loading_obsrvetions2_nabl = 'pass'
                        break
                    else:
                        record.edge_loading_obsrvetions2_nabl = 'fail'


      # Shock Resistance Test

    shock_resisrance_name = fields.Char("Name",default="Shock Resistance Test")
    shock_resisrance_visible = fields.Boolean("Shock Resistance Test",compute="_compute_visible")  

    shock_resisrance_obsrvetions1 = fields.Char(string="Soft and light body impact test")
    shock_resisrance_obsrvetions2 = fields.Char(string="soft and heavy body impact test")


       # Edge Loading Test

    bucklin_resistance_name = fields.Char("Name",default="Buckling Resistance Test")
    bucklin_resistance_visible = fields.Boolean("Buckling Resistance Test",compute="_compute_visible")  

    bucklin_resistance_obsrvetions1 = fields.Float(string="Buckling Resistance- Deflection at the lower free end after 5 minutes of the application of the load")
    bucklin_resistance_obsrvetions2 = fields.Float(string="Buckling Resistance- Deflection at the lower free end after 15 minutes of the Removal of the load, Residual deformation.")

    bucklin_resistance_obsrvetions1_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Buckling Resistance Obsrvetions 1 Conformity", compute="_compute_bucklin_resistance_obsrvetions1_conformity", store=True)



    @api.depends('bucklin_resistance_obsrvetions1','eln_ref','grade')
    def _compute_bucklin_resistance_obsrvetions1_conformity(self):
        
        for record in self:
            record.bucklin_resistance_obsrvetions1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14a75287-8e9d-48bb-a187-861b0c5e1dfa')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14a75287-8e9d-48bb-a187-861b0c5e1dfa')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.bucklin_resistance_obsrvetions1 - record.bucklin_resistance_obsrvetions1*mu_value
                    upper = record.bucklin_resistance_obsrvetions1 + record.bucklin_resistance_obsrvetions1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.bucklin_resistance_obsrvetions1_conformity = 'pass'
                        break
                    else:
                        record.bucklin_resistance_obsrvetions1_conformity = 'fail'

    bucklin_resistance_obsrvetions1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Buckling Resistance Obsrvetions 1 NABL", compute="_compute_bucklin_resistance_obsrvetions1_nabl", store=True)

    @api.depends('bucklin_resistance_obsrvetions1','eln_ref','grade')
    def _compute_bucklin_resistance_obsrvetions1_nabl(self):
        
        for record in self:
            record.bucklin_resistance_obsrvetions1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14a75287-8e9d-48bb-a187-861b0c5e1dfa')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14a75287-8e9d-48bb-a187-861b0c5e1dfa')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.bucklin_resistance_obsrvetions1 - record.bucklin_resistance_obsrvetions1*mu_value
                    upper = record.bucklin_resistance_obsrvetions1 + record.bucklin_resistance_obsrvetions1*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.bucklin_resistance_obsrvetions1_nabl = 'pass'
                        break
                    else:
                        record.bucklin_resistance_obsrvetions1_nabl = 'fail'

    bucklin_resistance_obsrvetions2_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Buckling Resistance Obsrvetions 2 Conformity", compute="_compute_bucklin_resistance_obsrvetions2_conformity", store=True)



    @api.depends('bucklin_resistance_obsrvetions2','eln_ref','grade')
    def _compute_bucklin_resistance_obsrvetions2_conformity(self):
        
        for record in self:
            record.bucklin_resistance_obsrvetions2_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cc6639db-457f-4959-b3e0-e280d9e7db7e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cc6639db-457f-4959-b3e0-e280d9e7db7e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.bucklin_resistance_obsrvetions2 - record.bucklin_resistance_obsrvetions2*mu_value
                    upper = record.bucklin_resistance_obsrvetions2 + record.bucklin_resistance_obsrvetions2*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.bucklin_resistance_obsrvetions2_conformity = 'pass'
                        break
                    else:
                        record.bucklin_resistance_obsrvetions2_conformity = 'fail'

    bucklin_resistance_obsrvetions2_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Buckling Resistance Obsrvetions 2 NABL", compute="_compute_bucklin_resistance_obsrvetions2_nabl", store=True)

    @api.depends('bucklin_resistance_obsrvetions2','eln_ref','grade')
    def _compute_bucklin_resistance_obsrvetions2_nabl(self):
        
        for record in self:
            record.bucklin_resistance_obsrvetions2_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cc6639db-457f-4959-b3e0-e280d9e7db7e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cc6639db-457f-4959-b3e0-e280d9e7db7e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.bucklin_resistance_obsrvetions2 - record.bucklin_resistance_obsrvetions2*mu_value
                    upper = record.bucklin_resistance_obsrvetions2 + record.bucklin_resistance_obsrvetions2*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.bucklin_resistance_obsrvetions2_nabl = 'pass'
                        break
                    else:
                        record.bucklin_resistance_obsrvetions2_nabl = 'fail'


     # Slamming test

    slamming_name = fields.Char("Name",default="Slamming test")
    slamming_visible = fields.Boolean("Slamming test",compute="_compute_visible")  

    slamming_obsrvetions1 = fields.Char(string="Slamming Test")


      # Misuse test

    misuse_name = fields.Char("Name",default="Misuse test")
    misuse_visible = fields.Boolean("Misuse test",compute="_compute_visible")  

    misuse_obsrvetions1 = fields.Char(string="Misuse test")


      # Varying Humidity test
    
    door_varying_humidity_name = fields.Char("Name",default="Varying Humidity test")
    door_varying_humidity_visible = fields.Boolean("Varying Humidity test",compute="_compute_visible") 

    varying_cupping_observations1 = fields.Float(string="Observations")
    varying_cupping_observations2 = fields.Float(string="Observations")

    door_varying_cupping_avg = fields.Float(string="General Flatness after varying humidity test, cupping",compute="_compute_door_varying_cupping_avg",digits=(12,3))

    door_varying_cupping_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Cupping Conformity", compute="_compute_door_varying_cupping_avg_conformity", store=True)



    @api.depends('door_varying_cupping_avg','eln_ref','grade')
    def _compute_door_varying_cupping_avg_conformity(self):
        
        for record in self:
            record.door_varying_cupping_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','58865fca-97fe-426d-aec7-ebf2ec20fedf')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','58865fca-97fe-426d-aec7-ebf2ec20fedf')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.door_varying_cupping_avg - record.door_varying_cupping_avg*mu_value
                    upper = record.door_varying_cupping_avg + record.door_varying_cupping_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.door_varying_cupping_avg_conformity = 'pass'
                        break
                    else:
                        record.door_varying_cupping_avg_conformity = 'fail'

    door_varying_cupping_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Cupping NABL", compute="_compute_door_varying_cupping_avg_nabl", store=True)

    @api.depends('door_varying_cupping_avg','eln_ref','grade')
    def _compute_door_varying_cupping_avg_nabl(self):
        
        for record in self:
            record.door_varying_cupping_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','58865fca-97fe-426d-aec7-ebf2ec20fedf')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','58865fca-97fe-426d-aec7-ebf2ec20fedf')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.door_varying_cupping_avg - record.door_varying_cupping_avg*mu_value
                    upper = record.door_varying_cupping_avg + record.door_varying_cupping_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.door_varying_cupping_avg_nabl = 'pass'
                        break
                    else:
                        record.door_varying_cupping_avg_nabl = 'fail'


    @api.depends('varying_cupping_observations1', 'varying_cupping_observations2')
    def _compute_door_varying_cupping_avg(self):
        for record in self:
            values = [record.varying_cupping_observations1, record.varying_cupping_observations2]
            total = sum(value for value in values if value)
            count = sum(1 for value in values if value)
            record.door_varying_cupping_avg = total / count if count > 0 else 0

    varying_warping_observations1 = fields.Float(string="Observations")
    varying_warping_observations2 = fields.Float(string="Observations")

    door_varying_warping_avg = fields.Float(string="General Flatness after varying humidity test, warping",compute="_compute_door_varying_warping_avg",digits=(12,2))

    door_varying_warping_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Warping Conformity", compute="_compute_door_varying_warping_avg_conformity", store=True)



    @api.depends('door_varying_warping_avg','eln_ref','grade')
    def _compute_door_varying_warping_avg_conformity(self):
        
        for record in self:
            record.door_varying_warping_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e970e60d-189f-4ebb-b1bd-9e0d8dc44d6f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e970e60d-189f-4ebb-b1bd-9e0d8dc44d6f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.door_varying_warping_avg - record.door_varying_warping_avg*mu_value
                    upper = record.door_varying_warping_avg + record.door_varying_warping_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.door_varying_warping_avg_conformity = 'pass'
                        break
                    else:
                        record.door_varying_warping_avg_conformity = 'fail'

    door_varying_warping_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Warping NABL", compute="_compute_door_varying_warping_avg_nabl", store=True)

    @api.depends('door_varying_warping_avg','eln_ref','grade')
    def _compute_door_varying_warping_avg_nabl(self):
        
        for record in self:
            record.door_varying_warping_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e970e60d-189f-4ebb-b1bd-9e0d8dc44d6f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e970e60d-189f-4ebb-b1bd-9e0d8dc44d6f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.door_varying_warping_avg - record.door_varying_warping_avg*mu_value
                    upper = record.door_varying_warping_avg + record.door_varying_warping_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.door_varying_warping_avg_nabl = 'pass'
                        break
                    else:
                        record.door_varying_warping_avg_nabl = 'fail'


    @api.depends('varying_warping_observations1', 'varying_warping_observations2')
    def _compute_door_varying_warping_avg(self):
        for record in self:
            values = [record.varying_warping_observations1, record.varying_warping_observations2]
            total = sum(value for value in values if value)
            count = sum(1 for value in values if value)
            record.door_varying_warping_avg = total / count if count > 0 else 0

    varying_twisting_observations1 = fields.Float(string="Observations")
    varying_twisting_observations2 = fields.Float(string="Observations")

    door_varying_twisting_avg = fields.Float(string="General flatness after varying humidity test, twisting",compute="_compute_door_varying_twisting_avg",digits=(12,1))
    door_varying_humidity = fields.Char(string="Varying humdity test")

    door_varying_twisting_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Twisting Conformity", compute="_compute_door_varying_twisting_avg_conformity", store=True)



    @api.depends('door_varying_twisting_avg','eln_ref','grade')
    def _compute_door_varying_twisting_avg_conformity(self):
        
        for record in self:
            record.door_varying_twisting_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','10bb9da6-4d70-4921-b062-ca61e0b32cf3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','10bb9da6-4d70-4921-b062-ca61e0b32cf3')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.door_varying_twisting_avg - record.door_varying_twisting_avg*mu_value
                    upper = record.door_varying_twisting_avg + record.door_varying_twisting_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.door_varying_twisting_avg_conformity = 'pass'
                        break
                    else:
                        record.door_varying_twisting_avg_conformity = 'fail'

    door_varying_twisting_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Twisting NABL", compute="_compute_door_varying_twisting_avg_nabl", store=True)

    @api.depends('door_varying_twisting_avg','eln_ref','grade')
    def _compute_door_varying_twisting_avg_nabl(self):
        
        for record in self:
            record.door_varying_twisting_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','10bb9da6-4d70-4921-b062-ca61e0b32cf3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','10bb9da6-4d70-4921-b062-ca61e0b32cf3')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.door_varying_twisting_avg - record.door_varying_twisting_avg*mu_value
                    upper = record.door_varying_twisting_avg + record.door_varying_twisting_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.door_varying_twisting_avg_nabl = 'pass'
                        break
                    else:
                        record.door_varying_twisting_avg_nabl = 'fail'


    @api.depends('varying_twisting_observations1', 'varying_twisting_observations2')
    def _compute_door_varying_twisting_avg(self):
        for record in self:
            values = [record.varying_twisting_observations1, record.varying_twisting_observations2]
            total = sum(value for value in values if value)
            count = sum(1 for value in values if value)
            record.door_varying_twisting_avg = total / count if count > 0 else 0


     # End Immersion test

    end_immpresion_name = fields.Char("Name",default="End Immersion test")
    end_immpresion_visible = fields.Boolean("End Immersion test",compute="_compute_visible")  

    end_immpresion_obsrvetions1 = fields.Char(string="End Immersion test")


     # Knife test

    knife_name = fields.Char("Name",default="Knife test")
    knife_visible = fields.Boolean("Knife test",compute="_compute_visible")  

    knife_obsrvetions1 = fields.Char(string="Knife test")

    # Glue adhesion test

    glue_adhesion_name = fields.Char("Name",default="Glue adhesion test")
    glue_adhesion_visible = fields.Boolean("Glue adhesion test",compute="_compute_visible")  

    glue_adhesion_obsrvetions1 = fields.Char(string="Glue adhesion test")
    
    
            





     ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.door_length_visible = False
            record.door_width_visible = False
            record.door_thickess_visible = False
            record.door_squareness_visible = False
            record.door_general_flatness_visible = False
            record.door_local_planeness_visible = False
            record.door_impact_visible = False
            record.edge_loading_visible = False
            record.shock_resisrance_visible = False
            record.bucklin_resistance_visible = False
            record.slamming_visible = False
            record.misuse_visible = False
            record.end_immpresion_visible = False
            record.knife_visible = False
            record.glue_adhesion_visible = False
            record.door_varying_humidity_visible = False
          
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
                if sample.internal_id == "cd31c1fa-aac8-4a92-b56e-37ace7f01f13":
                    record.door_length_visible = True

                if sample.internal_id == "426149cc-ee30-45bb-a7df-db54327c2de1":
                    record.door_width_visible = True

                if sample.internal_id == "80bacb3a-e725-4651-b476-3b1cc3fdd405":
                    record.door_thickess_visible = True

                if sample.internal_id == "7f15645f-2d9f-4797-9a0f-978913968fd7":
                    record.door_squareness_visible = True

                if sample.internal_id == "c3845764-c593-4ad2-a2a1-a8653c060b16":
                    record.door_general_flatness_visible = True

                if sample.internal_id == "0020e36c-0431-4859-8713-5e40c743e23b":
                    record.door_local_planeness_visible = True

                if sample.internal_id == "bf8130ff-d00f-44c6-8216-da112646962c":
                    record.door_impact_visible = True

                if sample.internal_id == "e3b8df2f-c7f4-4079-9c72-42fdab241896":
                    record.edge_loading_visible = True

                if sample.internal_id == "92d5ed97-f463-4129-a75a-091ebfc79eb3":
                    record.shock_resisrance_visible = True

                if sample.internal_id == "f38ae4bd-c6ac-4ebb-ac3f-ccb6c058d038":
                    record.bucklin_resistance_visible = True

                if sample.internal_id == "52613913-a010-4316-bed3-95e730833bcd":
                    record.slamming_visible = True

                if sample.internal_id == "ac04ae65-0ecf-41e3-a756-4a6f463bc7dd":
                    record.misuse_visible = True

                if sample.internal_id == "def7da26-83e4-4dac-9350-5a7985bdcbd7":
                    record.end_immpresion_visible = True

                if sample.internal_id == "bf807311-0de8-4c7d-a2b1-3c97c4a607b4":
                    record.knife_visible = True

                if sample.internal_id == "f473aa7e-7e07-4cbc-a2c2-cc5c2dabb650":
                    record.glue_adhesion_visible = True
                
                if sample.internal_id == "7bc503c2-a6d6-4ecb-a6d4-285a80e013c4":
                    record.door_varying_humidity_visible = True

              




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
        record = super(Door, self).create(vals)
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
        record = self.env['mechanical.door1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values