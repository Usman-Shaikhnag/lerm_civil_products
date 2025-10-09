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


#  Scratch hardness According to Moh's Scale

    size = fields.Many2one('lerm.size.line',string="Type of group",store=True,domain="[('product_id', '=', product_id)]")
    product_id = fields.Many2one('product.template', string="Product", compute="_compute_product_id",store=True)

    @api.depends('eln_ref')
    def _compute_product_id(self):
        if self.eln_ref:
            self.product_id = self.eln_ref.material.id


    
    scratch_hardness_name = fields.Char("Name",default="Scratch hardness According to Moh's Scale")
    scratch_hardness_visible = fields.Boolean("Surface Quality",compute="_compute_visible") 

    observations1 = fields.Float(string="Observations")
    observations2 = fields.Float(string="Observations")
    observations3 = fields.Float(string="Observations")
    observations4 = fields.Float(string="Observations")
    observations5 = fields.Float(string="Observations")

    scratch_hardness_avg = fields.Float(string="Scratch hardness According to Moh's Scale",compute="_compute_scratch_hardness_avg")

    requirement_scratch_hardness = fields.Char(string="Requirement ,Scratch hardness According to Moh's Scale",compute="_compute_requirement_scratch_hardness")


    @api.depends('size')
    def _compute_requirement_scratch_hardness(self):
        """Fetch multiple permissable_limit values from lerm.parameter.master where internal_id matches"""
        param_master = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', 'cecda256-41c5-4cb5-843a-e09590c7c587')
        ], limit=1)

        for record in self:
            record.requirement_scratch_hardness = "0.0"  # Default value

            if record.size and param_master and param_master.parameter_table:
                # Find all matching records where size matches
                matching_params = param_master.parameter_table.filtered(lambda p: p.size.id == record.size.id)

                if matching_params:
                    # Collect all permissable_limit values and join them into a single string
                    record.requirement_scratch_hardness = ", ".join(str(p.permissable_limit or "0.0") for p in matching_params)

    @api.depends('observations1', 'observations2', 'observations3', 'observations4', 'observations5')
    def _compute_scratch_hardness_avg(self):
        for record in self:
            values = [record.observations1, record.observations2, record.observations3, record.observations4, record.observations5]
            total = sum(value for value in values if value)
            count = sum(1 for value in values if value)
            record.scratch_hardness_avg = total / count if count > 0 else 0


            







 ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.true_specific_gravity_visible = False
            record.scratch_hardness_visible = False
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
                
                if sample.internal_id == "4bad1ffc-1874-4ebc-a9e9-acc9557d2fd2":
                    record.true_specific_gravity_visible = True

                if sample.internal_id == "cecda256-41c5-4cb5-843a-e09590c7c587":
                    record.scratch_hardness_visible = True

                    

               
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