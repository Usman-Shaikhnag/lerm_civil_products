from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math

import logging
_logger = logging.getLogger(__name__)



class Stones(models.Model):
    _name = "mechanical.stones"
    _inherit = "lerm.eln"
    _rec_name = "name_stones"


    name_stones = fields.Char("Name",default="Stones")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id






    


#        # 3. Water Absorption

#     water_absorption_name = fields.Char("Name",default="Water Absorption ")
#     water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")

#     water_absorption_child_lines = fields.One2many('paver.water.absorption.line','parent_id',string="Water Line")

#     avg_water_absorption = fields.Float(
#         string="Avg. Water Absorption (%)",
#         compute="_compute_avg_water_absorption", store=True
#     )

#     @api.depends('water_absorption_child_lines.water_absorption')
#     def _compute_avg_water_absorption(self):
#         for rec in self:
#             lines = rec.water_absorption_child_lines
#             if lines:
#                 total = sum(line.water_absorption for line in lines)
#                 rec.avg_water_absorption = round(total / len(lines), 2)
#             else:
#                 rec.avg_water_absorption = 0.0

#     avg_water_absorption_conformity = fields.Selection([
#             ('pass', 'Pass'),
#             ('fail', 'Fail')], string="Conformity", compute="_compute_avg_water_absorption_conformity", store=True)

#     @api.depends('avg_water_absorption','eln_ref','grade')
#     def _compute_avg_water_absorption_conformity(self):
        
#         for record in self:
#             record.avg_water_absorption_conformity = 'fail'
#             line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147fgrr-eba3-4f15-b33d-679b39f7372e')])
#             materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147fgrr-eba3-4f15-b33d-679b39f7372e')]).parameter_table
#             for material in materials:
#                 if material.grade.id == record.grade.id:
#                     req_min = material.req_min
#                     req_max = material.req_max
#                     mu_value = line.mu_value
                    
#                     lower = record.avg_water_absorption - record.avg_water_absorption*mu_value
#                     upper = record.avg_water_absorption + record.avg_water_absorption*mu_value
#                     if lower >= req_min and upper <= req_max:
#                         record.avg_water_absorption_conformity = 'pass'
#                         break
#                     else:
#                         record.avg_water_absorption_conformity = 'fail'

#     avg_water_absorption_nabl = fields.Selection([
#         ('pass', 'NABL'),
#         ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_water_absorption_nabl", store=True)

#     @api.depends('avg_water_absorption','eln_ref','grade')
#     def _compute_avg_water_absorption_nabl(self):
        
#         for record in self:
#             record.avg_water_absorption_nabl = 'fail'
#             line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147fgrr-eba3-4f15-b33d-679b39f7372e')])
#             materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147fgrr-eba3-4f15-b33d-679b39f7372e')]).parameter_table
#             for material in materials:
#                 if material.grade.id == record.grade.id:
#                     lab_min = line.lab_min_value
#                     lab_max = line.lab_max_value
#                     mu_value = line.mu_value
                    
#                     lower = record.avg_water_absorption - record.avg_water_absorption*mu_value
#                     upper = record.avg_water_absorption + record.avg_water_absorption*mu_value
#                     if lower >= lab_min and upper <= lab_max:
#                         record.avg_water_absorption_nabl = 'pass'
#                         break
#                     else:
#                         record.avg_water_absorption_nabl = 'fail'







#  ### Compute Visible
#     @api.depends('sample_parameters')
#     def _compute_visible(self):
        
#         for record in self:
#             record.water_absorption_visible = False
            
#             for sample in record.sample_parameters:
#                 print("Internal Ids",sample.internal_id)
                
#                 if sample.internal_id == "2147fgrr-eba3-4f15-b33d-679b39f7372e":
#                     record.water_absorption_visible = True

               
##########################


    # def open_eln_page(self):
    #     # import wdb; wdb.set_trace()

    #     return {
    #             'view_mode': 'form',
    #             'res_model': "lerm.eln",
    #             'type': 'ir.actions.act_window',
    #             'target': 'current',
    #             'res_id': self.eln_ref.id,
                
    #         }   
    # 
    # 
    # #################################        

    # def open_eln_page(self):
    # # import wdb; wdb.set_trace()
    #     for result in self.eln_ref.parameters_result:
    #         if result.parameter.internal_id == '2147fgrr-eba3-4f15-b33d-679b39f7372e':
    #             result.result_char = round(self.avg_water_absorption,2)
    #             if self.avg_water_absorption_nabl == 'pass':
    #                 result.nabl_status = 'nabl'
    #             else:
    #                 result.nabl_status = 'non-nabl'
    #             continue
            

    #     return {
    #             'view_mode': 'form',
    #             'res_model': "lerm.eln",
    #             'type': 'ir.actions.act_window',
    #             'target': 'current',
    #             'res_id': self.eln_ref.id,
                
    #         }
            
    

    # @api.model
    # def create(self, vals):
    #     # import wdb;wdb.set_trace()
    #     record = super(Stones, self).create(vals)
    #     # record.get_all_fields()
    #     record.eln_ref.write({'model_id':record.id})
    #     return record







    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     # records = self.env['lerm.eln'].sudo().search([('id','=', record.eln_id.id)]).parameters_result
    #     # print("records",records)
    #     # self.sample_parameters = records
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)



    # def get_all_fields(self):
    #     record = self.env['mechanical.stones'].browse(self.ids[0])
    #     field_values = {}
    #     for field_name, field in record._fields.items():
    #         field_value = record[field_name]
    #         field_values[field_name] = field_value

    #     return field_values

    # @api.depends('eln_ref')
    # def _compute_grade_id(self):
    #     if self.eln_ref:
    #         self.grade = self.eln_ref.grade_id.id










   

   

  



    


   



   
   

   
