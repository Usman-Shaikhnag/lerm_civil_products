from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math
import matplotlib.pyplot as plt
import io
import base64
import matplotlib.ticker as ticker
import numpy as np
import math
from scipy.interpolate import CubicSpline , interp1d , Akima1DInterpolator
from scipy.optimize import minimize_scalar
from io import BytesIO
from scipy.interpolate import make_interp_spline
from matplotlib.ticker import LogLocator, MultipleLocator



class Soil(models.Model):
    _name = "mechanical.soil"
    _inherit = "lerm.eln"
    _rec_name = "name_soil"


    name_soil = fields.Char("Name",default="Soil")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    soil_child_lines = fields.One2many('mechanical.soil.line','parent_id',string="Parameter")
    soil_visible = fields.Boolean("USC Visible",compute="_compute_visible")


   

    


   

     ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
      
        for record in self:
            record.soil_visible = False
         
            

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == '12014fgr-5c56-475b-9arty12457866yyyjj':
                    record.soil_visible = True

            

                

    # def open_eln_page(self):
    #     # import wdb; wdb.set_trace()

    #     return {
    #             'view_mode': 'form',
    #             'res_model': "lerm.eln",
    #             'type': 'ir.actions.act_window',
    #             'target': 'current',
    #             'res_id': self.eln_ref.id,
                
    #         }
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
        record = super(Soil, self).create(vals)
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
        record = self.env['mechanical.soil'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id




class SoilLINE(models.Model):
    _name = "mechanical.soil.line"
    parent_id = fields.Many2one('mechanical.soil',string="Parent Id")

    sr_no = fields.Integer(string="Sr NO.", readonly=True, copy=False, default=1)
    
    sample_type = fields.Char(string="Sample Type") 
    depth = fields.Char(string="Depth")
    gsa_g = fields.Float(string="GSA G")
    gsa_s = fields.Float(string="GSA S")
    gsa_m = fields.Float(string="GSA M")
    gsa_c = fields.Float(string="GSA C")
    atterbergs_ll = fields.Float(string="Atterbergs Limit LL")
    atterbergs_pl = fields.Float(string="Atterbergs Limit PL")
    atterbergs_sl = fields.Float(string="Atterbergs Limit SL")
    is_classification = fields.Float(string="IS Classification")
    spesific_gravity = fields.Float(string="Specific Gravity ",digits=(16, 2))
    fsi = fields.Float(string="Free Swell Index ",digits=(16, 2))
    nmc = fields.Float(string="Natural moisture content",digits=(16, 2))
    bulk_density = fields.Float(string="Bulk Density ",digits=(16, 2))
    proctor_mdd = fields.Float(string=" Proctor MDD",digits=(16, 2))
    proctor_omc = fields.Float(string=" Proctor OMC",digits=(16, 2))
    ucs = fields.Float(string="UCS")
    direct_shear_c = fields.Float(string="Direct Shear  C ",digits=(16, 2))
    direct_shear_ɸ = fields.Float(string="Direct Shear ɸ",digits=(16, 2))
    Triaxial_test_c = fields.Float(string="Triaxial Test (UU) C",digits=(16, 2))
    Triaxial_test_ɸ = fields.Float(string="Triaxial Test (UU) ɸ",digits=(16, 2))
    consolidation_pc = fields.Float(string="Consolidation PC")
    consolidation_cc = fields.Float(string="Consolidation CC")
    cbr = fields.Float(string="California bearing ratio")
    sp = fields.Float(string="Swelling pressure")
    permeability = fields.Float(string="Permeability ",digits=(16, 2))
    

    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(LIQUIDLIMITLINE, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




