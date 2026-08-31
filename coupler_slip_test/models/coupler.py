from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re



class CouplerSlipTest(models.Model):
    _name = "coupler.slip.test"
    _inherit = "lerm.eln"
    _rec_name = "name"
   
    
    Id_no = fields.Char("ID No")
    name = fields.Char("Name",default="COUPLER")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    diameter = fields.Float(string="Outer Diameter")
    crossectional_area = fields.Float(string="Nominal Cross Sectional Area mm²",compute="_compute_crossectional_area")
    gauge_length = fields.Float(string="Gauge Length L, mm",store=True)
    ultimate_load = fields.Float(string="Ultimate Tensile Load, KN")
    eln_ref = fields.Many2one('lerm.eln',string="ELN")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
  

    result_test = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non-satisfactory', 'Non-Satisfactory')],"Result",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    
    slip_strength = fields.Float(string="Slip Strength, N/mm2",compute="_compute_slip_strength",store=True)
    ext_at_20 = fields.Float(string="Ext At 20 N/MM2",store=True)



    @api.depends('ultimate_load', 'crossectional_area')
    def _compute_slip_strength(self):
        for record in self:
            if record.crossectional_area != 0:
                record.slip_strength = record.ultimate_load / record.crossectional_area * 1000
            else:
                record.slip_strength = 0

    @api.depends('diameter')
    def _compute_crossectional_area(self):
        for record in self:
            if record.diameter:
                record.crossectional_area = (record.diameter * record.diameter * 3.1416) / 4
            else:
                record.crossectional_area = 0.0


    slip_strength_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="compute_slip_strength_conformity", store=True)

    @api.depends('slip_strength','eln_ref','grade')
    def compute_slip_strength_conformity(self):
        
        for record in self:
            record.slip_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b4e7f2a1-8c3d-4e5f-9a6b-d1c2e3f4a5b6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b4e7f2a1-8c3d-4e5f-9a6b-d1c2e3f4a5b6')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.slip_strength - record.slip_strength*mu_value
                    upper = record.slip_strength + record.slip_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.slip_strength_conformity = 'pass'
                        break
                    else:
                        record.slip_strength_conformity = 'fail'

    slip_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_slip_strength_nabl", store=True)

    @api.depends('slip_strength','eln_ref','grade')
    def _compute_slip_strength_nabl(self):
        
        for record in self:
            record.slip_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b4e7f2a1-8c3d-4e5f-9a6b-d1c2e3f4a5b6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b4e7f2a1-8c3d-4e5f-9a6b-d1c2e3f4a5b6')]).parameter_table
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.slip_strength - record.slip_strength*mu_value
            upper = record.slip_strength + record.slip_strength*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.slip_strength_nabl = 'pass'
                break
            else:
                record.slip_strength_nabl = 'fail'


    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        current_user = self.env.user
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

            if result.parameter.internal_id == 'b4e7f2a1-8c3d-4e5f-9a6b-d1c2e3f4a5b6':
                result.result_char = round(self.slip_strength,2)
                result.calculated = True
                if self.slip_strength_nabl == 'pass':
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
        record = super(CouplerSlipTest, self).create(vals)
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

