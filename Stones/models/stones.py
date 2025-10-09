from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math

# import logging
# _logger = logging.getLogger(__name__)



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





from odoo import api, fields, models

class MechanicalStonesLine(models.Model):
    _name = "mechanical.stones.line"
    _description = "Stone Test Line"

    parent_id = fields.Many2one('mechanical.stones', string='Parent Test')
    sample_id = fields.Char("Sample ID")
    oven_dry_weight = fields.Float("Oven Dry Wt (A, g)")
    sat_surf_dry_weight = fields.Float("Sat. Surf. Dry Wt (B, g)")
    water_added = fields.Float("Water Added (C, g)")
    
    water_absorption = fields.Float(
        "Water Absorption (%)",
        compute="_compute_values", store=True)
    apparent_spec_gravity = fields.Float(
        "Apparent Spec. Gravity",
        compute="_compute_values", store=True)
    apparent_porosity = fields.Float(
        "Apparent Porosity (%)",
        compute="_compute_values", store=True)
    remarks = fields.Char("Remarks")

    @api.depends('oven_dry_weight', 'sat_surf_dry_weight', 'water_added')
    def _compute_values(self):
        for rec in self:
            A = rec.oven_dry_weight
            B = rec.sat_surf_dry_weight
            C = rec.water_added
            if A:
                rec.water_absorption = ((B - A) / A) * 100
            else:
                rec.water_absorption = 0.0
            denom = (1000 - C) if C is not None else 0
            rec.apparent_spec_gravity = (A / denom) if denom else 0.0
            rec.apparent_porosity = ((B - A) / denom) * 100 if denom else 0.0


    # True Specific Gravity

    true_specific_gravity_name = fields.Char("Name",default="True Specific Gravity")
    true_specific_gravity_visible = fields.Boolean("True Specific Gravity Visible",compute="_compute_visible")

    true_specific_gravity_ids = fields.One2many("mechanical.true.specific.gravity.line", "parent_id", string="Test Readings")

    avg_true_specific_gravity = fields.Float(
        string="Average True Specific Gravity ",
        compute="_compute_avg_true_specific_gravity",
        store=True,
        digits=(12,2))

    @api.depends("true_specific_gravity_ids.true_specific_gravity")
    def _compute_avg_true_specific_gravity(self):
        for rec in self:
            vals = [line.true_specific_gravity for line in rec.true_specific_gravity_ids if line.true_specific_gravity is not None]
            rec.avg_true_specific_gravity = round(sum(vals)/len(vals), 2) if vals else 0.0

    avg_true_specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_true_specific_gravity_conformity", store=True)

    @api.depends('avg_true_specific_gravity','eln_ref','grade')
    def _compute_avg_true_specific_gravity_conformity(self):
        
        for record in self:
            record.avg_true_specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214hhj6gt21-ca64-44dd-b0ae-6587gghty')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214hhj6gt21-ca64-44dd-b0ae-6587gghty')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_true_specific_gravity - record.avg_true_specific_gravity*mu_value
                    upper = record.avg_true_specific_gravity + record.avg_true_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_true_specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.avg_true_specific_gravity_conformity = 'fail'

    avg_true_specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_true_specific_gravity_nabl", store=True)

    @api.depends('avg_true_specific_gravity','eln_ref','grade')
    def _compute_avg_true_specific_gravity_nabl(self):
        
        for record in self:
            record.avg_true_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214hhj6gt21-ca64-44dd-b0ae-6587gghty')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214hhj6gt21-ca64-44dd-b0ae-6587gghty')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_true_specific_gravity - record.avg_true_specific_gravity*mu_value
            upper = record.avg_true_specific_gravity + record.avg_true_specific_gravity*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_true_specific_gravity_nabl = 'pass'
                break
            else:
                record.avg_true_specific_gravity_nabl = 'fail'


            







 ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.true_specific_gravity_visible = False
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
                
                if sample.internal_id == "4bad1ffc-1874-4ebc-a9e9-acc9557d2fd2":
                    record.true_specific_gravity_visible = True

# water absorption


from odoo import api, fields, models

class MechanicalStones(models.Model):
    _name = "mechanical.stones"
    _description = "Water Absorption Test of Stones"

    name_stones = fields.Char("Name", default="Stones")
    test_line_ids = fields.One2many('mechanical.stones.line', 'parent_id', string="Test Samples")





               
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

    def open_eln_page(self):
    # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == '4bad1ffc-1874-4ebc-a9e9-acc9557d2fd2':
                result.result_char = round(self.avg_true_specific_gravity,2)
                if self.avg_true_specific_gravity_nabl == 'pass':
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
        record = super(Stones, self).create(vals)
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
        record = self.env['mechanical.stones'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id



class TrueSpecificGravityLine(models.Model):
    _name = "mechanical.true.specific.gravity.line"
    parent_id = fields.Many2one('mechanical.stones',string="Parent Id")

    serial_no = fields.Integer(string="Test",readonly=True, copy=False, default=1)

    # sr_no = fields.Integer(string="Test", readonly=True, copy=False, default=1)
    m1 = fields.Float(string="Mass of Density Bottle (M1) ", digits=(12,2))
    m2 = fields.Float(string="Mass of Bottle & Dry Soil (M2) ", digits=(12,2))
    m3 = fields.Float(string="Mass of Bottle, Soil & Liquid (M3) ", digits=(12,2))
    m4 = fields.Float(string="Mass of Bottle Full of Liquid (M4) ", digits=(12,2))


    true_specific_gravity = fields.Float(
        string="Specific Gravity (G)",
        compute="_compute_true_specific_gravity",
        store=True,
        digits=(12,2)
    )

    @api.depends("m1","m2","m3","m4")
    def _compute_true_specific_gravity(self):
        for rec in self:
            try:
                numerator = rec.m2 - rec.m1
                denominator = (rec.m4 - rec.m1) - (rec.m3 - rec.m2)
                if denominator != 0:
                    rec.true_specific_gravity = round(numerator / denominator, 2)
                else:
                    rec.true_specific_gravity = 0.0
            except Exception:
                rec.true_specific_gravity = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(TrueSpecificGravityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1














   

   

  



    


   



   
   

   
