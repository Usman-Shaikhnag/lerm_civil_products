from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math



class WOOD(models.Model):
    _name = "mechanical.wood"
    _inherit = "lerm.eln"
    _rec_name = "name_wood"



    name_wood = fields.Char("Name",default="WOOD")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

     # Moisture Content

    moisture_content_name = fields.Char("Name",default="Moisture Content")
    moisture_content_visible = fields.Boolean("Moisture Content Visible",compute="_compute_visible")
    
    wood_child_lines = fields.One2many('mechanical.moisture.line','parent_id',string="Moisture Line")
    average_moisture = fields.Float(string="Average Moisture Content",compute="_compute_average_moisture", digits=(12,2))

    @api.depends('wood_child_lines.per_moisture')
    def _compute_average_moisture(self):
        for record in self:
            total_strength = sum(line.per_moisture for line in record.wood_child_lines)
            record.average_moisture = total_strength / len(record.wood_child_lines) if len(record.wood_child_lines) > 0 else 0.0


    moisture_content_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_moisture_content_conformity", store=True)

    @api.depends('average_moisture','eln_ref','grade')
    def _compute_moisture_content_conformity(self):
        
        for record in self:
            record.moisture_content_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a90cdbd7-3fa3-4b83-ae31-9d28120458tyu32')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a90cdbd7-3fa3-4b83-ae31-9d28120458tyu32')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_moisture - record.average_moisture*mu_value
                    upper = record.average_moisture + record.average_moisture*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.moisture_content_conformity = 'pass'
                        break
                    else:
                        record.moisture_content_conformity = 'fail'

    moisture_content_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_moisture_content_nabl", store=True)

    @api.depends('average_moisture','eln_ref','grade')
    def _compute_moisture_content_nabl(self):
        
        for record in self:
            record.moisture_content_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a90cdbd7-3fa3-4b83-ae31-9d28120458tyu32')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a90cdbd7-3fa3-4b83-ae31-9d28120458tyu32')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_moisture - record.average_moisture*mu_value
                    upper = record.average_moisture + record.average_moisture*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.moisture_content_nabl = 'pass'
                        break
                    else:
                        record.moisture_content_nabl = 'fail'



    # Specific Gravity 

    specific_gravity_name = fields.Char("Name",default="Specific Gravity ")
    specific_gravity_visible = fields.Boolean("Specific Gravity  Visible",compute="_compute_visible")
    
    specific_gravity_child_lines = fields.One2many('mechanical.specific.gravity.line','parent_id',string="Specific Line")
    average_specific_gravity = fields.Float(string="Average Specific Gravity ",compute="_compute_average_specific_gravity", digits=(12,3))

    @api.depends('specific_gravity_child_lines.specific_gravity')
    def _compute_average_specific_gravity(self):
        for record in self:
            total_strength = sum(line.specific_gravity for line in record.specific_gravity_child_lines)
            record.average_specific_gravity = total_strength / len(record.specific_gravity_child_lines) if len(record.specific_gravity_child_lines) > 0 else 0.0


    specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_specific_gravity_conformity", store=True)

    @api.depends('average_specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_conformity(self):
        
        for record in self:
            record.specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','769b7052-d658-4d14-a5cc-c21dbe1487gbhjt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','769b7052-d658-4d14-a5cc-c21dbe1487gbhjt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_specific_gravity - record.average_specific_gravity*mu_value
                    upper = record.average_specific_gravity + record.average_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.specific_gravity_conformity = 'fail'

    specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_specific_gravity_nabl", store=True)

    @api.depends('average_specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_nabl(self):
        
        for record in self:
            record.specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','769b7052-d658-4d14-a5cc-c21dbe1487gbhjt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','769b7052-d658-4d14-a5cc-c21dbe1487gbhjt')]).parameter_table
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
    


   

     ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.moisture_content_visible = False
            record.specific_gravity_visible = False
         


            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
                if sample.internal_id == "a90cdbd7-3fa3-4b83-ae31-9d28120458tyu32":
                    record.moisture_content_visible = True

                if sample.internal_id == "769b7052-d658-4d14-a5cc-c21dbe1487gbhjt":
                    record.specific_gravity_visible = True

             


             
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
    
            if result.parameter.internal_id == 'a90cdbd7-3fa3-4b83-ae31-9d28120458tyu32':
                result.result_char = round(self.average_moisture,2)
                result.calculated = True
                if self.moisture_content_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


              
            if result.parameter.internal_id == '769b7052-d658-4d14-a5cc-c21dbe1487gbhjt':
                result.result_char = round(self.average_specific_gravity,2)
                result.calculated = True
                if self.specific_gravity_nabl == 'pass':
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
        record = super(WOOD, self).create(vals)
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
        record = self.env['mechanical.wood'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id



class MechanicalMoistureLine(models.Model):
    _name = "mechanical.moisture.line"
    parent_id = fields.Many2one('mechanical.wood',string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.",readonly=True, copy=False, default=1)
    initial_we = fields.Float(string="Initial Weight")
    oven_dry = fields.Float(string="Oven Dry Weight")
    per_moisture = fields.Float(string="Percentage of moisture content",digits=(12,2),compute="_compute_per_moisture")


    @api.depends('initial_we', 'oven_dry')
    def _compute_per_moisture(self):
        for record in self:
            if record.oven_dry:  # avoid division by zero
                record.per_moisture = ((record.initial_we - record.oven_dry) / record.oven_dry) * 100
            else:
                record.per_moisture = 0.0
   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalMoistureLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in chequered_tiles_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1




class MechanicalSpecificLine(models.Model):
    _name = "mechanical.specific.gravity.line"
    parent_id = fields.Many2one('mechanical.wood',string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.",readonly=True, copy=False, default=1)
    length = fields.Float(string="Length in mm")
    width = fields.Float(string="Width in mm")
    thickness = fields.Float(string="Thickness in mm")
    volume = fields.Float(string="volume",compute="_compute_volume",store=True)
    oven_dry = fields.Float(string="Oven Dry Weight")
    specific_gravity = fields.Float(string="Specific Gravity",digits=(12,3),compute="_compute_specific_gravity")

    @api.depends('length', 'width', 'thickness')
    def _compute_volume(self):
        for rec in self:
            if rec.length and rec.width and rec.thickness:
                rec.volume = rec.length * rec.width * rec.thickness
            else:
                rec.volume = 0.0

    @api.depends('oven_dry', 'volume')
    def _compute_specific_gravity(self):
        for record in self:
            if record.volume:  # avoid division by zero
                record.specific_gravity = record.oven_dry / record.volume
            else:
                record.specific_gravity = 0.0


    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalSpecificLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in chequered_tiles_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1