from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math
from datetime import datetime , timedelta
import re
import logging



class HollowConcreteBlock(models.Model):
    _name = "hollow.concrete.block"
    _inherit = "lerm.eln"
    _description = 'hollow.concrete.block'
    _rec_name = "name"


    name = fields.Char("Name",default="Hollow And Solid Concrete Block")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    hollow_solid_temp = fields.Char("Temperature",store=True)
    hollow_solid_humidity = fields.Char("Humidity",store=True)

    @api.depends("eln_ref")
    def _compute_size_id(self):
        for record in self:
            print("Size iD",record.eln_ref.size_id)
            record.size_id = record.eln_ref.size_id.id

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'aac.block.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }

    
    

    # Compressive Strength
    compressive_strength_name = fields.Char(default="Compressive Strength")
    compressive_strength_visible = fields.Boolean(string="Compressive Strength Visible",compute="_compute_visible")

    compressive_strength_line_ids = fields.One2many('hs.compression.test.line','parent_id',string='Compressive Strength Test Line')

    average_compressive_strength = fields.Float(string="Average Compressive Strength (N/mm²)",compute='_compute_average_compressive_strength',store=True)

    @api.depends('compressive_strength_line_ids.compressive_strength')
    def _compute_average_compressive_strength(self):
        for rec in self:
            strengths = rec.compressive_strength_line_ids.mapped('compressive_strength')
            rec.average_compressive_strength = (
                sum(strengths) / len(strengths)
                if strengths else 0.0
            )

    compressive_strength_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('--', '--'),], string='Confirmity', default='fail',compute="_compute_compressive_strength_confirmity")
    
    @api.depends('average_compressive_strength','eln_ref','grade')
    def _compute_compressive_strength_confirmity(self):
        for record in self:
            record.compressive_strength_confirmity = 'fail'   
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','692bb4da-26eb-4701-9ad7-b341c974c8e8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','692bb4da-26eb-4701-9ad7-b341c974c8e8')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.compressive_strength_confirmity = '--'
                        break

                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_compressive_strength - record.average_compressive_strength*mu_value
                    upper = record.average_compressive_strength + record.average_compressive_strength*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.compressive_strength_confirmity = 'pass'
                        break
                    else:
                        record.compressive_strength_confirmity = 'fail'

    compressive_strength_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_compressive_strength_nabl")
    
    @api.depends('average_compressive_strength','eln_ref','grade')
    def _compute_compressive_strength_nabl(self):
        
        for record in self:
            record.compressive_strength_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','692bb4da-26eb-4701-9ad7-b341c974c8e8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','692bb4da-26eb-4701-9ad7-b341c974c8e8')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_compressive_strength - record.average_compressive_strength*mu_value
                    upper = record.average_compressive_strength + record.average_compressive_strength*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.compressive_strength_nabl = 'pass'
                        break
                    else:
                        record.compressive_strength_nabl = 'fail'

    
    #  Water Absorption
    water_absorbtion_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")
    wt_absorption_name = fields.Char("Name",default="Water Absorption")


    water_absorption_line_ids = fields.One2many(
        "hs.water.absorption.line",
        "parent_id",
        string="Water Absorption Specimens"
    )


    water_absorption = fields.Float(
        string="Average Water Absorption (%)",
        compute="_compute_water_absorption",
        store=True,
        digits=(16, 3),
    )


    # ========================================================
    # COMPUTE MEAN WATER ABSORPTION
    # ========================================================

    @api.depends(
        "water_absorption_line_ids.water_absorption",
        "water_absorption_line_ids.wet_mass",
        "water_absorption_line_ids.dry_mass",
    )
    def _compute_water_absorption(self):
        for rec in self:

            rec.water_absorption = 0.0

            valid_lines = rec.water_absorption_line_ids.filtered(
                lambda line: (
                    line.wet_mass > 0
                    and line.dry_mass > 0
                )
            )

            if valid_lines:
                rec.water_absorption = (
                    sum(
                        valid_lines.mapped(
                            "water_absorption"
                        )
                    )
                    / len(valid_lines)
                )


    water_absorption_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('--', '--'),], string='Confirmity', compute="_compute_water_absorption_confirmity")

    @api.depends('water_absorption','eln_ref')
    def _compute_water_absorption_confirmity(self):
        for record in self:
            record.water_absorption_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fc4c19c4-3a3a-45f3-a099-f33a4b8e57a9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fc4c19c4-3a3a-45f3-a099-f33a4b8e57a9')]).parameter_table
            for material in materials:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.water_absorption_confirmity = '--'
                        break
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.water_absorption - record.water_absorption*mu_value
                    upper = record.water_absorption + record.water_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.water_absorption_confirmity = 'pass'
                        break
                    else:
                        record.water_absorption_confirmity = 'fail'

    water_absorption_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_water_absorption_nabl",store=True)
    
    @api.depends('water_absorption','eln_ref')
    def _compute_water_absorption_nabl(self):
        
        for record in self:
            record.water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fc4c19c4-3a3a-45f3-a099-f33a4b8e57a9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fc4c19c4-3a3a-45f3-a099-f33a4b8e57a9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.water_absorption - record.water_absorption*mu_value
                  upper = record.water_absorption + record.water_absorption*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.water_absorption_nabl = 'pass'
                      break
                  else:
                      record.water_absorption_nabl = 'fail'


    # Moisture Movment
    moisture_movment_name = fields.Char("Name",default="Moisture Movement")
    moisture_movment_visible = fields.Boolean("Moisture Movment Visible",compute="_compute_visible")

    moisture_movment_child_lines = fields.One2many('hs.moisture.movement.line','parent_id',string="Parameter")


    average_moisture_movment = fields.Float(string="Average",compute="_compute_average_moisture_movment", digits=(12, 3))
    
    @api.depends('moisture_movment_child_lines.moisture_movment')
    def _compute_average_moisture_movment(self):
        for record in self:
            moisture_movments = record.moisture_movment_child_lines.mapped('moisture_movment')
            record.average_moisture_movment = sum(moisture_movments) / len(moisture_movments) if len(moisture_movments) > 0 else 0.0

    moisture_movment_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('--', '--')
        ],string="Conformity",compute="_compute_moisture_movment_conformity",store=True)

    @api.depends('average_moisture_movment','eln_ref','grade')
    def _compute_moisture_movment_conformity(self):
        
        for record in self:
            record.moisture_movment_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','916c70fe-57ff-4f2a-9361-41a687b54f85')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','916c70fe-57ff-4f2a-9361-41a687b54f85')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.moisture_movment_conformity = '--'
                        break


                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_moisture_movment - record.average_moisture_movment*mu_value
                    upper = record.average_moisture_movment + record.average_moisture_movment*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.moisture_movment_conformity = 'pass'
                        break
                    else:
                        record.moisture_movment_conformity = 'fail'



    moisture_movment_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_moisture_movment_nabl",store=True)

    @api.depends('average_moisture_movment','eln_ref','grade')
    def _compute_moisture_movment_nabl(self):
        
        for record in self:
            record.moisture_movment_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','916c70fe-57ff-4f2a-9361-41a687b54f85')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','916c70fe-57ff-4f2a-9361-41a687b54f85')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_moisture_movment - record.average_moisture_movment*mu_value
            upper = record.average_moisture_movment + record.average_moisture_movment*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.moisture_movment_nabl = 'pass'
                break
            else:
                record.moisture_movment_nabl = 'fail'


     
    # Drying shrinkage
    drying_shrinkage_name = fields.Char("Name",default="Drying Shrinkage")
    drying_shrinkage_visible = fields.Boolean("Drying Shrinkage Visible",compute="_compute_visible")

    drying_shrinkage_child_lines = fields.One2many('hs.drying.shrinkage.line','parent_id',string="Parameter")
    average_drying_shrinkage = fields.Float(string="Average", compute="_compute_average_drying_shrinkage",digits=(12,3))


    @api.depends('drying_shrinkage_child_lines.drying_shrinkage')
    def _compute_average_drying_shrinkage(self):
        for record in self:
            total_drying_shrinkage = sum(record.drying_shrinkage_child_lines.mapped('drying_shrinkage'))
            count_lines = len(record.drying_shrinkage_child_lines)
            record.average_drying_shrinkage = total_drying_shrinkage / count_lines if count_lines else 0.0


    drying_shrinkage_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('--', '--')
        ],string="Conformity",compute="_compute_drying_shrinkage_conformity",store=True)

    @api.depends('average_drying_shrinkage','eln_ref','grade')
    def _compute_drying_shrinkage_conformity(self):
        
        for record in self:
            record.drying_shrinkage_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6c0d4ef6-867f-4e79-baf1-690338654f26')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6c0d4ef6-867f-4e79-baf1-690338654f26')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.drying_shrinkage_conformity = '--'
                        break


                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_drying_shrinkage - record.average_drying_shrinkage*mu_value
                    upper = record.average_drying_shrinkage + record.average_drying_shrinkage*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.drying_shrinkage_conformity = 'pass'
                        break
                    else:
                        record.drying_shrinkage_conformity = 'fail'


    drying_shrinkage_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Pass')],string="NABL",compute="_compute_drying_shrinkage_nabl",store=True)

    @api.depends('average_drying_shrinkage','eln_ref','grade')
    def _compute_drying_shrinkage_nabl(self):
        
        for record in self:
            record.drying_shrinkage_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6c0d4ef6-867f-4e79-baf1-690338654f26')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6c0d4ef6-867f-4e79-baf1-690338654f26')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_drying_shrinkage - record.average_drying_shrinkage*mu_value
            upper = record.average_drying_shrinkage + record.average_drying_shrinkage*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.drying_shrinkage_nabl = 'pass'
                break
            else:
                record.drying_shrinkage_nabl = 'fail'




    
    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

        
    def get_all_fields(self):
        record = self.env['hollow.concrete.block'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
        
            record.compressive_strength_visible = False
            record.water_absorbtion_visible = False
            record.moisture_movment_visible = False
            record.drying_shrinkage_visible = False

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                
                
                
                if sample.internal_id == 'fc4c19c4-3a3a-45f3-a099-f33a4b8e57a9':
                    record.water_absorbtion_visible = True

                if sample.internal_id == '692bb4da-26eb-4701-9ad7-b341c974c8e8':
                    record.compressive_strength_visible = True


                if sample.internal_id == '916c70fe-57ff-4f2a-9361-41a687b54f85':
                    record.moisture_movment_visible = True

                if sample.internal_id == '6c0d4ef6-867f-4e79-baf1-690338654f26':
                    record.drying_shrinkage_visible = True

                


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
            

            

             # Compressive Strength
            if result.parameter.internal_id == '692bb4da-26eb-4701-9ad7-b341c974c8e8':
                result.result_char = round(self.average_compressive_strength,2)
                result.calculated = True
                if self.compressive_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Water Absorption
            if result.parameter.internal_id == 'fc4c19c4-3a3a-45f3-a099-f33a4b8e57a9':
                result.result_char = round(self.water_absorption,2)
                result.calculated = True
                if self.water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


             # Moisture Movment
            if result.parameter.internal_id == '916c70fe-57ff-4f2a-9361-41a687b54f85':
                result.result_char = round(self.average_moisture_movment,2)
                result.calculated = True
                if self.moisture_movment_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


             # Drying Shrinkage
            if result.parameter.internal_id == '6c0d4ef6-867f-4e79-baf1-690338654f26':
                result.result_char = round(self.average_drying_shrinkage,2)
                result.calculated = True
                if self.drying_shrinkage_nabl == 'pass':
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
        record = super(HollowConcreteBlock, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

    def get_all_fields(self):
        record = self.env['hollow.concrete.block'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
        
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

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



    
    


    


    

    

    


    notes_id = fields.One2many('hollow.concrete.block.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

    @api.model
    def _default_notes_lines(self):
        return [
            (0, 0, {'sr_no': 'i', 'notes': 'The results stated in this report apply only to the tested sample(s) and are based on the conditions and parameters at the time of testing.'}),
            (0, 0, {'sr_no': 'ii', 'notes': 'This report is invalid without the official paper seal of Make Infracon.'}),
            (0, 0, {'sr_no': 'iii', 'notes': 'All test results are confidential and will not be disclosed to any third party without written consent of the client, except where required by law.'}),
            (0, 0, {'sr_no': 'iv', 'notes': 'Any discrepancies or complaints regarding this report must be communicated in writing within 7 days from the date of issue.'}),
            (0, 0, {'sr_no': 'v', 'notes': 'This report shall not be reproduced, except in full, without the prior written approval of Make Infracon.'}),
            (0, 0, {'sr_no': 'vi', 'notes': 'The laboratory assumes no responsibility for the purpose for which the test results are used or for any subsequent actions taken based on these results.'}),
        ]
    




class HSCompressionTestLine(models.Model):
    _name = 'hs.compression.test.line'
    _description = 'Compressive Strength Test Line'

    parent_id = fields.Many2one('hollow.concrete.block', string="Parent Id")

    sample_no = fields.Integer(string="Cube No.", readonly=True, copy=False, default=1)

    length = fields.Float(string="Length (mm)")
    breadth = fields.Float(string="Breadth (mm)")
    thickness = fields.Float(string="Thickness (mm)")


    area = fields.Float(string="Gross Area (mm²)",compute="_compute_area",store=True,)

    load_kn = fields.Float(string="Load (kN)")

    compressive_strength = fields.Float(string="Compressive Strength (N/mm²)",compute='_compute_strength',store=True)

    @api.depends('length', 'breadth')
    def _compute_area(self):
        for rec in self:
            rec.area = rec.length * rec.breadth

    @api.depends('load_kn', 'area')
    def _compute_strength(self):
        for rec in self:
            if rec.area:
                rec.compressive_strength = (
                    rec.load_kn * 1000
                ) / rec.area
            else:
                rec.compressive_strength = 0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(HSCompressionTestLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1



class HSWaterAbsorptionLine(models.Model):
    _name = "hs.water.absorption.line"
    _description = "Hollow Solid Block Water Absorption Line"


    parent_id = fields.Many2one("hollow.concrete.block",string="Parent Id")


    sr_no = fields.Integer(string="Specimen No.", readonly=True, copy=False, default=1)


    # A_wet
    wet_mass = fields.Float(
        string="Wet Mass of Block (kg)",
        digits=(16, 2),
    )


    # B
    dry_mass = fields.Float(
        string="Dry Mass of Block (kg)",
        digits=(16, 2),
    )

    water_absorption = fields.Float(
        string="Water Absorption (%)",
        compute="_compute_water_absorption",
        store=True,
        digits=(16, 3),
    )


    @api.depends(
        "wet_mass",
        "dry_mass",
    )
    def _compute_water_absorption(self):
        for line in self:

            line.water_absorption = 0.0

            if line.dry_mass > 0:
                line.water_absorption = (
                    (
                        line.wet_mass
                        - line.dry_mass
                    )
                    / line.dry_mass
                ) * 100.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(HSWaterAbsorptionLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1




class HSMoistureMovementLine(models.Model):
    _name = "hs.moisture.movement.line"
    parent_id = fields.Many2one('hollow.concrete.block', string="Parent Id")
   
    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    dry_length = fields.Float(string="Dry Length of the Block")
    wet_length = fields.Float(string="Wet Length of the Block")
    moisture_movment = fields.Float(string="Moisture Movement %", compute="_compute_moisture_movement", digits=(12, 3))



    @api.depends('dry_length', 'wet_length')
    def _compute_moisture_movement(self):
        for record in self:
            if record.wet_length != 0:
                record.moisture_movment = (record.wet_length - record.dry_length) / record.wet_length * 100
            else:
                record.moisture_movment = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(HSMoistureMovementLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class HSDryingShrinkageLine(models.Model):
    _name = "hs.drying.shrinkage.line"
    parent_id = fields.Many2one('hollow.concrete.block', string="Parent Id")
   
    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    wet_measurment = fields.Float(string="Wet measurement of the Block",digits=(12, 3))
    dry_measurment = fields.Float(string="Dry Measurement of the Block",digits=(12, 3))
    dry_lengths = fields.Float(string="Dry Length")
    drying_shrinkage = fields.Float(string="Drying Shrinkage %", compute="_compute_drying_shrinkage1",digits=(12, 4))



    @api.depends('wet_measurment', 'dry_measurment', 'dry_lengths')
    def _compute_drying_shrinkage1(self):
        for record in self:
            if record.dry_lengths != 0:
                record.drying_shrinkage = (record.wet_measurment - record.dry_measurment) / record.dry_lengths * 100
            else:
                record.drying_shrinkage = 0.0

  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(HSDryingShrinkageLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1




class HollowConcreteBlockNotes(models.Model):
    _name = "hollow.concrete.block.notes"

    parent_id = fields.Many2one('hollow.concrete.block', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
