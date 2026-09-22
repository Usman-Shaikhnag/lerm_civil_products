from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class MechanicalDryingShrinkage(models.Model):
    _name = "drying.shrinkage"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Concrete - Drying Shrinkage")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    notes_id = fields.One2many('drying.shrinkage.notes', 'parent_id', string="Notes")

    @api.model
    def default_get(self, fields):
        res = super(MechanicalDryingShrinkage, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The Test Report(s) is/are valid only to the sample submitted to the laboratory.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'Sample(s) was/were not drawn by laboratory.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'This Report may not be reproduced in except full/ part without the permission of the Lab Head of the Laboratory.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': '# - Information provided by the customer.',
            }),
        ]

        res['notes_id'] = default_notes
        return res


    # Drying Shrinkage
    drying_shrinkage_name = fields.Char("Name", default="Drying Shrinkage")
    drying_shrinkage_visible = fields.Boolean("Drying Shrinkage", compute="_compute_visible")

    drying_child_lines = fields.One2many('drying.shrinkage.line','parent_id',string="Parameter" )
   

    average1 = fields.Float("Average %",compute="_compute_average_initial_drying",digits=(16, 3))

    @api.depends('drying_child_lines.initial_drying')
    def _compute_average_initial_drying(self):
        for record in self:
            initial_drying_values = record.drying_child_lines.mapped('initial_drying')
            if initial_drying_values:
                record.average1 = sum(initial_drying_values) / len(initial_drying_values)
            else:
                record.average1 = 0


    
    

    drying_shrinkage_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')
            ], string="Conformity", compute="_compute_drying_shrinkage_conformity", store=True)

    @api.depends('average1','eln_ref','grade')
    def _compute_drying_shrinkage_conformity(self):
        
        for record in self:
            record.drying_shrinkage_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','20246345-407d-4ce8-ae0d-566bd4e3b52f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','20246345-407d-4ce8-ae0d-566bd4e3b52f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.drying_shrinkage_conformity = '--'
                        break


                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average1 - record.average1*mu_value
                    upper = record.average1 + record.average1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.drying_shrinkage_conformity = 'pass'
                        break
                    else:
                        record.drying_shrinkage_conformity = 'fail'

    drying_shrinkage_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_drying_shrinkage_nabl", store=True)

    @api.depends('average1','eln_ref','grade')
    def _compute_drying_shrinkage_nabl(self):
        
        for record in self:
            record.drying_shrinkage_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','20246345-407d-4ce8-ae0d-566bd4e3b52f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','20246345-407d-4ce8-ae0d-566bd4e3b52f')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:

            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average1 - record.average1*mu_value
            upper = record.average1 + record.average1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.drying_shrinkage_nabl = 'pass'
                break
            else:
                record.drying_shrinkage_nabl = 'fail'







    # Moisture Moment

    moisture_movement_name = fields.Char("Name", default="Moisture Movement")
    moisture_movement_visible = fields.Boolean("Moisture Movement", compute="_compute_visible")

    moisture_child_lines = fields.One2many('moisture.movment.line','parent_id',string="Parameter")
    
   
    average2 = fields.Float("Average %",compute="_compute_average_moisture_movement",digits=(16, 3))

    @api.depends('moisture_child_lines.moisture_movement')
    def _compute_average_moisture_movement(self):
        for record in self:
            moisture_movement_values = record.moisture_child_lines.mapped('moisture_movement')
            if moisture_movement_values:
                record.average2 = sum(moisture_movement_values) / len(moisture_movement_values)
            else:
                record.average2 = 0

    
    
    moisture_movement_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('--', '--')
        ], string="Conformity", compute="_compute_moisture_movement_conformity", store=True)

    @api.depends('average2','eln_ref','grade')
    def _compute_moisture_movement_conformity(self):
        
        for record in self:
            record.moisture_movement_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3e59cd18-c281-4737-aa89-5b1190808804')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3e59cd18-c281-4737-aa89-5b1190808804')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.moisture_movement_conformity = '--'
                        break


                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average2 - record.average2*mu_value
                    upper = record.average2 + record.average2*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.moisture_movement_conformity = 'pass'
                        break
                    else:
                        record.moisture_movement_conformity = 'fail'

    moisture_movement_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_moisture_movement_nabl", store=True)

    @api.depends('average2','eln_ref','grade')
    def _compute_moisture_movement_nabl(self):
        
        for record in self:
            record.moisture_movement_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3e59cd18-c281-4737-aa89-5b1190808804')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3e59cd18-c281-4737-aa89-5b1190808804')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average2 - record.average2*mu_value
            upper = record.average2 + record.average2*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.moisture_movement_nabl = 'pass'
                break
            else:
                record.moisture_movement_nabl = 'fail'
    




   
     ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.drying_shrinkage_visible = False
            record.moisture_movement_visible = False
           

            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
                if sample.internal_id == "20246345-407d-4ce8-ae0d-566bd4e3b52f":
                    record.drying_shrinkage_visible = True

                if sample.internal_id == "3e59cd18-c281-4737-aa89-5b1190808804":
                    record.drying_shrinkage_visible = True
                    record.moisture_movement_visible = True


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:


             # Drying Shrinkage
            if result.parameter.internal_id == '20246345-407d-4ce8-ae0d-566bd4e3b52f':
                result.result_char = round(self.average1,2)
                result.calculated = True
                if self.drying_shrinkage_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Moisture Movement
            if result.parameter.internal_id == '3e59cd18-c281-4737-aa89-5b1190808804':
                result.result_char = round(self.average2,2)
                result.calculated = True
                if self.moisture_movement_nabl == 'pass':
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
        record = super(MechanicalDryingShrinkage, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record
    
    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     # records = self.env['lerm.eln'].sudo().search([('id','=', record.eln_id.id)]).parameters_result
    #     # print("records",records)
    #     # self.sample_parameters = records
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)


    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    def _compute_sample_parameters(self):
        # parameter_based_assignment
        current_user = self.env.user
        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            # filter parameter results by current user
            user_param_results = record.eln_ref.parameters_result.filtered(
                lambda r: r.technician and r.technician.id == current_user.id
            )

            # map to parameter master IDs
            parameter_ids = user_param_results.mapped('parameter').ids

            record.sample_parameters = [(6, 0, parameter_ids)]



    def get_all_fields(self):
        record = self.env['drying.shrinkage'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values





    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


class MechanicalDryingShrinkageLine(models.Model):
    _name = "drying.shrinkage.line"
    parent_id = fields.Many2one('drying.shrinkage',string="Parent Id")

    sr_no = fields.Integer(string="Sample No.", readonly=True, copy=False, default=1)
   
    # sr_no = fields.Char(string="Sample No.")
    id_mark = fields.Char(string="ID Mark/Location")
    original_length = fields.Float("original length measurment W1",digits=(16, 3))
    dry_mesurment = fields.Float("Dry measurement ,W2",digits=(16, 3))
    dry_length = fields.Float("Dry length , W3",digits=(16, 3))
    initial_drying = fields.Float("Initial drying shrinkage",compute="_compute_initial_drying",digits=(16, 3))

    @api.depends('original_length', 'dry_mesurment', 'dry_length')
    def _compute_initial_drying(self):
        for record in self:
            if record.dry_length != 0:
                record.initial_drying = ((record.original_length - record.dry_mesurment) / record.dry_length) * 100
            else:
                record.initial_drying = 0


   



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalDryingShrinkageLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        for record in self:
            parent = record.parent_id.sudo()
            sample_id = parent.eln_ref.sample_id.client_sample_id
            if sample_id:
                record.id_mark = sample_id
            else:
                record.id_mark = ""

    @api.onchange('id_mark')
    def _onchange_id_mark(self):
        for record in self:
            if record.id_mark and not record.parent_id.eln_ref.sample_id.client_sample_id:
                record.parent_id.eln_ref.sample_id.client_sample_id = record.id_mark



class MoistureMovementLine(models.Model):
    _name = "moisture.movment.line"
    parent_id = fields.Many2one('drying.shrinkage',string="Parent Id")

    sr_no = fields.Integer(string="Sample No.", readonly=True, copy=False, default=1)
   
    # sr_no = fields.Char(string="Sample No.")
    id_mark = fields.Char(string="ID Mark/Location")

    final_wet = fields.Float("Final wet measurment W4",digits=(16, 3))
   
    moisture_movement = fields.Float("Moisture Movement in %",compute="_compute_moisture_movement",digits=(16, 3))

    # @api.depends('final_wet', 'parent_id.drying_child_lines.dry_mesurment', 'parent_id.drying_child_lines.dry_length')
    # def _compute_moisture_movement(self):
    #     for record in self:
    #         drying_shrinkage_line = record.parent_id.drying_child_lines.filtered(lambda x: x.sr_no == record.sr_no)
    #         if drying_shrinkage_line:
    #             dry_measurement = drying_shrinkage_line.dry_mesurment
    #             dry_length = drying_shrinkage_line.dry_length
    #             if dry_length != 0:
    #                 record.moisture_movement = ((dry_measurement - record.final_wet) / dry_length) * 100
    #             else:
    #                 record.moisture_movement = 0
    #         else:
    #             record.moisture_movement = 0

    @api.depends('final_wet', 'parent_id.drying_child_lines.dry_mesurment', 'parent_id.drying_child_lines.dry_length')
    def _compute_moisture_movement(self):
        for record in self:
            drying_shrinkage_line = record.parent_id.drying_child_lines.filtered(lambda x: x.sr_no == record.sr_no)
            if drying_shrinkage_line:
                dry_mesurment = drying_shrinkage_line.dry_mesurment
                dry_length = drying_shrinkage_line.dry_length
                if dry_length != 0:
                    record.moisture_movement = ((record.final_wet - dry_mesurment) / dry_length) * 100
                else:
                    record.moisture_movement = 0
            else:
                record.moisture_movement = 0



    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        for record in self:
            parent = record.parent_id.sudo()
            sample_id = parent.eln_ref.sample_id.client_sample_id
            if sample_id:
                record.id_mark = sample_id
            else:
                record.id_mark = ""

    @api.onchange('id_mark')
    def _onchange_id_mark(self):
        for record in self:
            if record.id_mark and not record.parent_id.eln_ref.sample_id.client_sample_id:
                record.parent_id.eln_ref.sample_id.client_sample_id = record.id_mark

   



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MoistureMovementLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class MechanicalDryingShrinkageNotes(models.Model):
    _name = "drying.shrinkage.notes"

    parent_id = fields.Many2one('drying.shrinkage',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
    