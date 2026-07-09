from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class FreshCementConcrete(models.Model):
    _name = "mechanical.fresh.cement.concrete"
    _inherit = "lerm.eln"
    _description = 'mechanical.fresh.cement.concrete'
    _rec_name = "name"


    name = fields.Char("Name",default="Fresh Cement Concrete")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    aac_temp = fields.Char("Temperature",store=True)
    aac_humidity = fields.Char("Humidity",store=True)

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

    # Slump Test
    slump_test_name = fields.Char(default="Slump Test")
    slump_test_visible = fields.Boolean(string="Slump Test Visible" ,compute="_compute_visible")

    slump_test_line_ids = fields.One2many('fcc.slump.test.line','parent_id',string='Slump Test Lines')

    
    measured_slump = fields.Float(
        string="Measured Slump (mm)",
        compute="_compute_measured_slump",
        store=True
    )

    required_slump = fields.Float(string="Required Slump (mm)")

    @api.depends('slump_test.slump_value')
    def _compute_measured_slump(self):
        for rec in self:
            if rec.slump_test:
                rec.measured_slump = sum(
                    rec.slump_test.mapped('slump_value')
                ) / len(rec.slump_test)
            else:
                rec.measured_slump = 0

    avg_measured_length_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_measured_length_confirmity")
    
    @api.depends('avg_measured_length','eln_ref','grade')
    def _compute_avg_measured_length_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_measured_length_confirmity = 'na'
                continue
            record.avg_measured_length_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42ea2fdb-c7be-4d19-8912-63f72c07574f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42ea2fdb-c7be-4d19-8912-63f72c07574f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_measured_length - record.avg_measured_length*mu_value
                    upper = record.avg_measured_length + record.avg_measured_length*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_measured_length_confirmity = 'pass'
                        break
                    else:
                        record.avg_measured_length_confirmity = 'fail'

    avg_measured_length_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_measured_length_nabl")
    
    @api.depends('avg_measured_length','eln_ref','grade')
    def _compute_avg_measured_length_nabl(self):
        
        for record in self:
            record.avg_measured_length_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42ea2fdb-c7be-4d19-8912-63f72c07574f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','42ea2fdb-c7be-4d19-8912-63f72c07574f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_measured_length - record.avg_measured_length*mu_value
                    upper = record.avg_measured_length + record.avg_measured_length*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_measured_length_nabl = 'pass'
                        break
                    else:
                        record.avg_measured_length_nabl = 'fail'





    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

        
    def get_all_fields(self):
        record = self.env['mechanical.fresh.cement.concrete'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.length_dimen_visible = False

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                
                if sample.internal_id == '42ea2fdb-c7be-4d19-8912-63f72c07574f':
                    record.length_dimen_visible = True

                

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
            # Length
            if result.parameter.internal_id == '42ea2fdb-c7be-4d19-8912-63f72c07574f':
                result.result_char = round(self.avg_measured_length,2)
                result.calculated = True
                if self.avg_measured_length_nabl == 'pass':
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
        record = super(FreshCementConcrete, self).create(vals)
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
        record = self.env['mechanical.fresh.cement.concrete'].browse(self.ids[0])
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



    
    


    


    

    

    


    notes_id = fields.One2many('mechanical.fresh.cement.concrete.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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
    



class FCCSlumpTestLine(models.Model):
    _name = "fcc.slump.test.line"
    _description = 'Slump Trial Line'

    parent_id = fields.Many2one('mechanical.fresh.cement.concrete', string="Parent Id")

    sample_no = fields.Integer(string="Specimen No.", readonly=True, copy=False, default=1)

    cone_height = fields.Float(
        string="Height of Cone (mm)",
    )

    height_after_slump = fields.Float(
        string="Height After Slump (mm)"
    )

    slump_value = fields.Float(
        string="Slump Value (mm)",
        compute="_compute_slump",
        store=True
    )

    slump_type = fields.Selection([
        ('true', 'True'),
        ('shear', 'Shear'),
        ('collapse', 'Collapse')
    ], string="Type of Slump")

    @api.depends('cone_height', 'height_after_slump')
    def _compute_slump(self):
        for rec in self:
            rec.slump_value = rec.cone_height - rec.height_after_slump


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(FCCSlumpTestLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1







class FreshCementConcreteNotes(models.Model):
    _name = "mechanical.fresh.cement.concrete.notes"

    parent_id = fields.Many2one('mechanical.fresh.cement.concrete', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
