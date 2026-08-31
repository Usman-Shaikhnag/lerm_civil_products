from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class ActCompressiveStrength(models.Model):
    _name = "mechanical.act.compressive"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name", default="ACT Compressive")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")
    child_lines = fields.One2many('mechanical.act.compressive.line', 'parent_id', string="Parameter")
    average_compr_strength = fields.Float(string="Average Compressive Strength in N/mm2", compute="_compute_average_compr_strength",digits=(12,2))
    act_compressive = fields.Float(string="ACT Compressive", compute="_compute_act_compressive",digits=(12,2))
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="ELN")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    @api.depends('child_lines.compressive_strength')
    def _compute_average_compr_strength(self):
        for record in self:
            compressive_strengths = record.child_lines.mapped('compressive_strength')
            if compressive_strengths:
                record.average_compr_strength = sum(compressive_strengths) / len(compressive_strengths)
            else:
                record.average_compr_strength = 0.0


    notes_id = fields.One2many('mechanical.act.compressive.notes', 'parent_id', string="Notes")

    @api.model
    def default_get(self, fields):
        res = super(ActCompressiveStrength, self).default_get(fields)

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



    # @api.depends('average_compr_strength')
    # def _compute_act_average(self):
    #     for record in self:
    #         record.act_compressive = record.average_compr_strength * 1.64 + 8.09

    @api.depends('average_compr_strength')
    def _compute_act_compressive(self):
        for record in self:
            record.act_compressive = (record.average_compr_strength) * (1.64) + (8.09)



    age_of_days = fields.Selection([
        ('1days', '1 Days'),
        ('3days', '3 Days'),
        ('7days', '7 Days'),
        ('14days', '14 Days'),
        ('21days', '21 Days'),
        ('28days', '28 Days'),
        ('56days', '56 Days'),
        ('112days', '112 Days'),
    ], string='Age', default='28days',required=True,compute="_compute_age_of_days")
    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")
    date_of_testing = fields.Date(string="Date of Testing")


    confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('--', '--'),

    ], string='Confirmity', default='fail',compute="_compute_confirmity")

    @api.depends('act_compressive','eln_ref','grade','age_of_days','difference')
    def _compute_confirmity(self):
        for record in self:
            record.confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6cded77a-f7af-4f1c-BBAD-c33d0e18cdf1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6cded77a-f7af-4f1c-BBAD-c33d0e18cdf1')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.confirmity = '--'
                        break


                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    if record.age_of_days == "3days":
                        req_min = req_min * 0.5
                        req_max = req_max* 0.5
                    if record.age_of_days == "7days":
                        req_min = req_min * 0.7
                        req_max = req_max* 0.7
                    if record.age_of_days == "14days":
                        req_min = req_min * 0.9
                        req_max = req_max* 0.9
                    if record.age_of_days == "28days":
                        req_min = req_min
                        req_max = req_max
                    lower = record.act_compressive - record.act_compressive*mu_value
                    upper = record.act_compressive + record.act_compressive*mu_value
                    
                    if record.difference == 0:
                        if lower >= req_min and upper <= req_max :
                            record.confirmity = 'pass'
                            break
                        else:
                            record.confirmity = 'fail'
                    else:
                        record.confirmity = '--'


    age_of_test = fields.Integer("Age of Test, days",compute="compute_age_of_test")
    difference = fields.Integer("Difference",compute="compute_difference")

    # grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),

    ], string='NABL', default='fail',compute="_compute_nabl")


    @api.depends('act_compressive','eln_ref','grade')
    def _compute_nabl(self):
        
        for record in self:
            record.nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6cded77a-f7af-4f1c-BBAD-c33d0e18cdf1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6cded77a-f7af-4f1c-BBAD-c33d0e18cdf1')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.act_compressive - record.act_compressive*mu_value
            upper = record.act_compressive + record.act_compressive*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.nabl = 'pass'
                break
            else:
                record.nabl = 'fail'



    @api.depends('age_of_test','age_of_days')
    def compute_difference(self):
        for record in self:
            age_of_days = 0
            if record.age_of_days == '1days':
                age_of_days = 1
            elif record.age_of_days == '3days':
                age_of_days = 3
            elif record.age_of_days == '7days':
                age_of_days = 7
            elif record.age_of_days == '14days':
                age_of_days = 14
            elif record.age_of_days == '21days':
                age_of_days = 21
            elif record.age_of_days == '28days':
                age_of_days = 28
            elif record.age_of_days == '56days':
                age_of_days = 56
            elif record.age_of_days == '112days':
                age_of_days = 112
            else:
                age_of_days = 0
            record.difference = record.age_of_test - age_of_days

        


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

    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None



    @api.onchange('eln_ref')
    def _compute_age_of_days(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).days_casting
                if sample_record == '1':
                    record.age_of_days = '1days'
                elif sample_record == '3':
                    record.age_of_days = '3days'
                elif sample_record == '7':
                    record.age_of_days = '7days'
                elif sample_record == '14':
                    record.age_of_days = '14days'
                elif sample_record == '21':
                    record.age_of_days = '21days'
                elif sample_record == '28':
                    record.age_of_days = '28days'
                elif sample_record == '56':
                    record.age_of_days = '56days'
                elif sample_record == '112':
                    record.age_of_days = '112days'
                else:
                    record.age_of_days = None
            else:
                record.age_of_days = None


    def open_eln_page(self):
            # parameter_based_assignment
            current_user = self.env.user
            # 🔹 Only results assigned to current technician
            technician_results = self.eln_ref.parameters_result.filtered(
                lambda r: r.technician == current_user
            )
    
            for result in technician_results:
    
                if result.parameter.internal_id == '6cded77a-f7af-4f1c-BBAD-c33d0e18cdf1':
                    result.result_char = round(self.act_compressive,2)
                    result.calculated = True
                    if self.nabl == 'pass':
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
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
                    
    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(ActCompressiveStrength, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['mechanical.act.compressive'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

  

  


class ActCompressiveStrengthLine(models.Model):
    _name = "mechanical.act.compressive.line"
    parent_id = fields.Many2one('mechanical.act.compressive', string="Parent Id")

    sr_no = fields.Integer(string="Sr No", readonly=True, copy=False, default=1)
    length = fields.Float(string="Length")
    width = fields.Float(string="Width")
    area = fields.Float(string="Area mm2", compute="_compute_area", store=True,digits=(12,2))  # Added store=True
    id_mark = fields.Char(string="ID Mark/Location")
    weight_sample = fields.Float(string="Weight of Sample in kgs",digits=(12,3))
    crushing_load = fields.Float(string="Crushing Load in kN",digits=(12,1))
    compressive_strength = fields.Float(string="Compressive Strength in N/mm2", compute="_compute_compressive_strength",digits=(12,2))

   
    @api.depends('length', 'width')
    def _compute_area(self):
        for record in self:
            record.area = record.length * record.width

    @api.depends('crushing_load', 'area')
    def _compute_compressive_strength(self):
        for record in self:
            if record.area != 0:
                record.compressive_strength = record.crushing_load / record.area * 1000
            else:
                record.compressive_strength = 0.0

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        for record in self:
            sample_id = record.parent_id.eln_ref.sample_id.client_sample_id
            if sample_id:
                record.id_mark = sample_id
            else:
                record.id_mark = ""

    @api.onchange('id_mark')
    def _onchange_id_mark(self):
        for record in self:
            if record.id_mark and not record.parent_id.eln_ref.sample_id.client_sample_id:
                record.parent_id.eln_ref.sample_id.client_sample_id = record.id_mark
            else:
                print("Either id_mark is empty or sample_id is already set")


    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(ActCompressiveStrengthLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class ActCompressiveStrengthNotes(models.Model):
    _name = "mechanical.act.compressive.notes"

    parent_id = fields.Many2one('mechanical.act.compressive',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")


   

