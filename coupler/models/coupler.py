from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re



class MechanicalCoupler(models.Model):
    _name = "mechanical.coupler"
    _inherit = "lerm.eln"
    _rec_name = "name"
   
    
    Id_no = fields.Char("ID No")
    name = fields.Char("Name",default="COUPLER")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    diameter = fields.Float(string="Outer Diameter")
    crossectional_area = fields.Float(string="Nominal Cross Sectional Area mm²",compute="_compute_crossectional_area")
    gauge_length = fields.Float(string="Gauge Length L, mm",store=True)
    elongated_gauge_length = fields.Float(string="Gauge Length  at Maximum Force, mm")
    ultimate_load = fields.Float(string="Ultimate Tensile Load, KN")
    distance = fields.Float(string="Distance of fracture From center of Coupler")
    ult_tens_strgth = fields.Float(string="Ultimate Tensile Strength, N/mm2",compute="_compute_ult_tens_strgth",store=True)
    total_elongation = fields.Float(string="Total Elongation at maximum force(%)",compute="_compute_elongation_percent",store=True)
 
    # fracture = fields.Char("Fracture (Within Gauge Length)",default="W.G.L")
    eln_ref = fields.Many2one('lerm.eln',string="ELN")
  
    requirement_ult_tens_strgth = fields.Float(string="Requirement",compute="_compute_requirement_utl",store=True)
    requirement_total_elongation = fields.Float(string="Requirement",compute="_compute_requirement_yield",store=True)
   
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    # tests = fields.Many2many("mechanical.tmt.test",string="Tests")
  

    location_of_failure = fields.Char("Location of failure",default="Outside the length of the mechanical splice")
    result_test = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non-satisfactory', 'Non-Satisfactory')],"Result",store=True)
    
    # re_bend_test = fields.Selection([
    #     ('satisfactory', 'Satisfactory'),
    #     ('non-satisfactory', 'Non-Satisfactory')],"Re-Bend Test",store=True)
    
      

    # @api.depends('bend_test')
    # def _compute_bend_test_text(self):
    #     for record in self:
    #         if record.bend_test == '1':
    #             record.bend_test_text = 'Satisfactory'
    #         elif record.bend_test == '2':
    #             record.bend_test_text = 'Non-Satisfactory'
    #         else:
    #             record.bend_test_text = 'Undefined'
    


  
    # location_of_failure_visible = fields.Boolean("Location of failure",compute="_compute_visible")
    # result_test_visible = fields.Boolean("Result",compute="_compute_visible")

  
   

    # @api.depends('eln_ref','sample_parameters')
    # def _compute_visible(self):
    #     for record in self:
    #         record.location_of_failure_visible = False
    #         record.result_test_visible  = False  
          
    #         for sample in record.sample_parameters:
    #             print("Samples internal id",sample.internal_id)
    #             if sample.internal_id == 'c3b7e054-bafc-40bf-82ad-82063feabfb8':
    #                 record.location_of_failure_visible = True
    #             if sample.internal_id == 'dceffc67-d195-4991-8e28-e35eb27ecc34':
    #                 record.result_test_visible = True
               

    # @api.depends('diameter')
    # def _compute_crossectional_area(self):
    #     for record in self:
    #         if record.diameter:
    #             record.crossectional_area = 3.14 * (record.diameter ** 2) / 4
    #         else:
    #             record.crossectional_area = 0.0 

    @api.depends('diameter')
    def _compute_crossectional_area(self):
        for record in self:
            if record.diameter:
                record.crossectional_area = (record.diameter * record.diameter * 3.1416) / 4
            else:
                record.crossectional_area = 0.0

    # @api.depends('diameter')
    # def _compute_gauge_length(self):
    #     for record in self:
    #         record.gauge_length = record.diameter * 10 + 50

    @api.depends('ultimate_load', 'crossectional_area')
    def _compute_ult_tens_strgth(self):
        for coupler in self:
            if coupler.crossectional_area != 0:
                coupler.ult_tens_strgth = coupler.ultimate_load / coupler.crossectional_area * 1000
            else:
                coupler.ult_tens_strgth = 0

    @api.depends('elongated_gauge_length', 'gauge_length')
    def _compute_elongation_percent(self):
        for record in self:
            if record.gauge_length != 0:
                record.total_elongation = ((record.elongated_gauge_length - record.gauge_length) / record.gauge_length) * 100
            else:
                record.total_elongation = 0


    ult_tens_strgth_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="compute_ult_tens_strgth_conformity", store=True)

    @api.depends('ult_tens_strgth','eln_ref','grade')
    def compute_ult_tens_strgth_conformity(self):
        
        for record in self:
            record.ult_tens_strgth_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78a837cc-25e3-460d-802f-7dd858984087')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78a837cc-25e3-460d-802f-7dd858984087')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.ult_tens_strgth - record.ult_tens_strgth*mu_value
                    upper = record.ult_tens_strgth + record.ult_tens_strgth*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.ult_tens_strgth_conformity = 'pass'
                        break
                    else:
                        record.ult_tens_strgth_conformity = 'fail'

    ult_tens_strgth_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_ult_tens_strgth_nabl", store=True)

    @api.depends('ult_tens_strgth','eln_ref','grade')
    def _compute_ult_tens_strgth_nabl(self):
        
        for record in self:
            record.ult_tens_strgth_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78a837cc-25e3-460d-802f-7dd858984087')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78a837cc-25e3-460d-802f-7dd858984087')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.ult_tens_strgth - record.ult_tens_strgth*mu_value
            upper = record.ult_tens_strgth + record.ult_tens_strgth*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.ult_tens_strgth_nabl = 'pass'
                break
            else:
                record.ult_tens_strgth_nabl = 'fail'


    total_elongation_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="compute_total_elongation_conformity", store=True)

    @api.depends('total_elongation','eln_ref','grade')
    def compute_total_elongation_conformity(self):
        
        for record in self:
            record.total_elongation_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','73e5f596-972c-46f8-8d2c-3149b00c57df')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','73e5f596-972c-46f8-8d2c-3149b00c57df')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.total_elongation - record.total_elongation*mu_value
                    upper = record.total_elongation + record.total_elongation*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.total_elongation_conformity = 'pass'
                        break
                    else:
                        record.total_elongation_conformity = 'fail'

    total_elongation_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_total_elongation_nabl", store=True)

    @api.depends('total_elongation','eln_ref','grade')
    def _compute_total_elongation_nabl(self):
        
        for record in self:
            record.total_elongation_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','73e5f596-972c-46f8-8d2c-3149b00c57df')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','73e5f596-972c-46f8-8d2c-3149b00c57df')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.total_elongation - record.total_elongation*mu_value
            upper = record.total_elongation + record.total_elongation*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.total_elongation_nabl = 'pass'
                break
            else:
                record.total_elongation_nabl = 'fail'


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
        record = super(CouplerLine, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

        
    def get_all_fields(self):
        record = self.env['mechanical.coupler'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
    

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size = self.eln_ref.size_id.id

  

    

    



    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

