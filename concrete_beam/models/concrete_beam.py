from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
from datetime import datetime , timedelta


class FlexuralStrengthConcreteBeam(models.Model):
    _name = "mechanical.concrete.beam"
    _inherit = "lerm.eln"
    _rec_name = "name"


    name = fields.Char("Name",default="Concrete Beam")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines = fields.One2many('mechanical.concrete.beam.line','parent_id',string="Parameter")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="ELN")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    
    average_flexural_strength = fields.Float(string="Average Flexural Strength in N/mm2",compute="_compute_average_flexural_strength")
    sample_id = fields.Many2one('lerm.srf.sample',string='Sample')

    temprature = fields.Float("Temperature (°C)", digits=(10,2))
    humidity = fields.Float("Humidity (%)", digits=(10,2))

    week_no = fields.Char("Week No")

    other_details = fields.Char("Other Details")

    condition = fields.Char("Condition")

    description_work = fields.Text("Description Of Work")


    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'mechanical.concrete.beam.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }




    
                # remark

    notes_id = fields.One2many('concretebeam.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(FlexuralStrengthConcreteBeam, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The report shall not be reproduced in full or partially without written approval of the laboratory HOD/CEO/Maganement.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'Sampling is not done by us unless mentioned otherwide.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'without a QR Code and hologram this report is considered invalid.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'The Result listed refer only to tested samples & applicable parameter Endorsement of product is neither interred nor inplied.',
            }),

            (0, 0, {
                'sr_no': 'e',
                'notes': 'The use or report for arbitration, publicity & evidence in legal dispute is forbidden except with prior written consent NBML Lab.',
            }),
             (0, 0, {
                'sr_no': 'f',
                'notes': 'All disputed are subject to Raipur jurisdiction 7 days correction to this report invalidates this report.',
            }),

             (0, 0, {
                'sr_no': 'g',
                'notes': 'Sample will be destroyed after 30-days from the date of test report unless otherwise Specified.',
            }),
        ]

        res['notes_id'] = default_notes
        return res

    

    

    # age_of_days = fields.Selection([
    #     ('3days', '3 Days'),
    #     ('7days', '7 Days'),
    #     ('14days', '14 Days'),
    #     ('28days', '28 Days'),
    # ], string='Age', default='28days',required=True)
    age_of_days = fields.Selection([
        ('3days', '3 Days'),
        ('7days', '7 Days'),
        ('14days', '14 Days'),
        ('28days', '28 Days'),
    ], string='Age', default='28days',required=True,compute="_compute_age_of_days")

    # date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")
    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")
    date_of_testing = fields.Date(string="Date of Testing")

    # age_of_test = fields.Integer("Age of Test, days",compute="compute_age_of_test")
    age_of_test = fields.Integer("Age of Test, days",compute="compute_age_of_test")

    

    @api.onchange('eln_ref')
    def _compute_age_of_days(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).days_casting
                if sample_record == '3':
                    record.age_of_days = '3days'
                elif sample_record == '7':
                    record.age_of_days = '7days'
                elif sample_record == '14':
                    record.age_of_days = '14days'
                elif sample_record == '28':
                    record.age_of_days = '28days'
                else:
                    record.age_of_days = None
            else:
                record.age_of_days = None


              


    # confirmity = fields.Selection([
    #     ('pass', 'Pass'),
    #     ('fail', 'Fail'),
    # ], string='Confirmity', default='fail',compute="_compute_average_flexural_strength_conformity")

    # @api.depends('date_of_testing','date_of_casting')
    # def compute_age_of_test(self):
    #     for record in self:
    #         if record.date_of_casting and record.date_of_testing:
    #             date1 = fields.Date.from_string(record.date_of_casting)
    #             date2 = fields.Date.from_string(record.date_of_testing)
    #             date_difference = (date2 - date1).days
    #             record.age_of_test = date_difference
    #         else:
    #             record.age_of_test = 0

    @api.depends('date_of_testing','date_of_casting')
    def compute_age_of_test(self):
        for record in self:
            if record.date_of_casting and record.date_of_testing:
                date1 = fields.Date.from_string(record.date_of_casting)
                date2 = fields.Date.from_string(record.date_of_testing)
                date_difference = (date2 - date1).days
                record.age_of_test = date_difference
            else:
                record.age_of_test = 0

    # @api.onchange('eln_ref')
    # def compute_date_of_casting(self):
    #     for record in self:
    #         if record.eln_ref.sample_id:
    #             sample_record = self.env['lerm.srf.sample'].search([('id','=', record.eln_ref.sample_id.id)]).date_casting
    #             record.date_of_casting = sample_record
    #         else:
    #             record.date_of_casting = None

    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None


    @api.depends('date_of_casting','age_of_days')
    def _compute_testing_date(self):
        for record in self:
            if record.date_of_casting:
                if record.age_of_days == "3days":
                    cast_date = fields.Datetime.from_string(record.date_of_casting)
                    testing_date = cast_date + timedelta(days=3)
                    record.date_of_testing = fields.Datetime.to_string(testing_date)
                elif record.age_of_days == "7days":
                    cast_date = fields.Datetime.from_string(record.date_of_casting)
                    testing_date = cast_date + timedelta(days=7)
                    record.date_of_testing = fields.Datetime.to_string(testing_date)
                elif record.age_of_days == "14days":
                    cast_date = fields.Datetime.from_string(record.date_of_casting)
                    testing_date = cast_date + timedelta(days=14)
                    record.date_of_testing = fields.Datetime.to_string(testing_date)
                elif record.age_of_days == "28days":
                    cast_date = fields.Datetime.from_string(record.date_of_casting)
                    testing_date = cast_date + timedelta(days=28)
                    record.date_of_testing = fields.Datetime.to_string(testing_date)
                else:
                    record.date_of_testing = False
            else:
                record.date_of_testing = False



    # @api.depends('average_flexural_strength','eln_ref')
    # def _compute_average_flexural_strength_conformity(self):
    #     for record in self:
    #         record.confirmity = 'fail'
    #         line = self.env['lerm.parameter.master'].search([('internal_id','=','19edc74f-c7b2-45b6-8696-e97c19e81993')])
    #         materials = self.env['lerm.parameter.master'].search([('internal_id','=','19edc74f-c7b2-45b6-8696-e97c19e81993')]).parameter_table
    #         for material in materials:
                
    #                 req_min = material.req_min
    #                 req_max = material.req_max
    #                 mu_value = line.mu_value
                    
    #                 lower = record.average_flexural_strength - record.average_flexural_strength*mu_value
    #                 upper = record.average_flexural_strength + record.average_flexural_strength*mu_value
    #                 if lower >= req_min and upper <= req_max:
    #                     record.confirmity = 'pass'
    #                     break
    #                 else:
    #                     record.confirmity = 'fail'


    @api.depends('eln_ref')
    def _compute_grade_id(self):
        for record in self:
            if record.eln_ref:
                grade = record.eln_ref.grade_id.id
                print("Grade beam",grade)
                record.grade = record.eln_ref.grade_id.id

    @api.depends('child_lines.flexural_strength')
    def _compute_average_flexural_strength(self):
        for record in self:
            total_strength = sum(line.flexural_strength for line in record.child_lines)
            total_lines = len(record.child_lines)
            record.average_flexural_strength = total_strength / total_lines if total_lines > 0 else 0.0


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:


            if result.parameter.internal_id == '19edc74f-c7b2-45b6-8696-e97c19e81993':
                result.calculated = True
                result.result_char = round(self.average_flexural_strength,2)
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
        record = super(FlexuralStrengthConcreteBeam, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        test = record.eln_ref
        print("test",test)

        return record

    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     # records = self.env['lerm.eln'].search([('id','=', record.eln_id.id)]).parameters_result
    #     # print("records",records)
    #     # self.sample_parameters = records
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

    def get_all_fields(self):
        record = self.env['mechanical.concrete.beam'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    




    
class FlexuralStrengthConcreteBeamLine(models.Model):
    _name = "mechanical.concrete.beam.line"
    parent_id = fields.Many2one('mechanical.concrete.beam',string="Parent Id")

    sr_no = fields.Integer(string="Sr No", readonly=True, copy=False, default=1)
    id_mark = fields.Char(string="ID MARK/ Location",compute="_onchange_parent_id",inverse="_onchange_id_mark",store=True)
    length = fields.Integer(string="Length of span ( L ) in mm")
    depth = fields.Float(string="Depth (d) in mm")
    width = fields.Float(string="Width (mm)")
    wt_of_sample = fields.Float(string="Weight of Sample in kgs")
    fracture_distance = fields.Float(string="Fracture Distance from neaere support in Cm")
    failure_load  = fields.Float(string="Failure Load in kN(p)")
    flexural_strength = fields.Float(string="Flexural Strength in N/mm2", compute="_compute_flexural_strength")
    # flexural_strength_3 = fields.Float(string="Flexural Strength in N/mm2", compute="_compute_flexural_strength_three")

    @api.depends('parent_id')
    def _onchange_parent_id(self):
        for record in self:
            parent = record.parent_id.sudo()
            sample_id = parent.eln_ref.sample_id.client_sample_id
            # import wdb; wdb.set_trace()

            if sample_id and record.id_mark == False:
                record.id_mark = sample_id
            # else:
            #     record.id_mark = ""

    @api.depends('id_mark')
    def _onchange_id_mark(self):
        for record in self:
            if record.id_mark and not record.parent_id.eln_ref.sample_id.client_sample_id:
                record.parent_id.sudo().eln_ref.sample_id.client_sample_id = record.id_mark

    # def read(self, fields=None, load='_classic_read'):

    #     self._onchange_parent_id()
    #     self._onchange_id_mark()
        
    #     return super(FlexuralStrengthConcreteBeamLine, self).read(fields=fields, load=load)
    
    @api.depends('failure_load', 'length', 'depth', 'width')
    def _compute_flexural_strength(self):
        for record in self:
            if record.length and record.depth and record.width and record.failure_load:
                record.flexural_strength = (record.failure_load * record.length) / (record.depth * record.width * record.width) * 1000
            else:
                record.flexural_strength = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(FlexuralStrengthConcreteBeamLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



            
class concretebeamNotes(models.Model):
    _name = "concretebeam.notes"

    parent_id = fields.Many2one('mechanical.concrete.beam',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
