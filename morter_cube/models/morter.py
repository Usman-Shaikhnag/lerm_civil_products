from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
from datetime import datetime , timedelta


class MechanicalMorterCube(models.Model):
    _name = "mechanical.morter.cube1"
    _inherit = "lerm.eln"
    _description = 'mechanical.morter.cube1'
    _rec_name = "name"

    name = fields.Char("Name",default="Morter Cube")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="ELN")



      # Dimension

    morter_cube_name1 = fields.Char("Name",default="Morter Cube")
    morter_cube_visible = fields.Boolean("Chequered Visible",compute="_compute_visible")   

    morter_cube_child_lines = fields.One2many('mechanical.morter.cube1.line','parent_id',string="Parameter")
    average_morter_cube = fields.Float(string="Average Compressive Strength in N/mm2",compute="_compute_average_morter_cube", digits=(12,2))

    @api.depends('morter_cube_child_lines.compressive_strength')
    def _compute_average_morter_cube(self):
        for record in self:
            total_strength = sum(line.compressive_strength for line in record.morter_cube_child_lines)
            record.average_morter_cube = total_strength / len(record.morter_cube_child_lines) if len(record.morter_cube_child_lines) > 0 else 0.0


    average_morter_cube_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_average_morter_cube_conformity", store=True)

    age_of_days = fields.Selection([
        ('3days', '3 Days'),
        ('7days', '7 Days'),
        ('14days', '14 Days'),
        ('21days', '21 Days'),
        ('28days', '28 Days'),
        ('45days', '45 Days'),
        ('56days', '56 Days'),
        ('112days', '112 Days'),
    ], string='Age', default='28days',required=True,compute="_compute_age_of_days")
    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")
    date_of_testing = fields.Date(string="Date of Testing")

    age_of_test = fields.Integer("Age of Test, days",compute="compute_age_of_test")
    difference = fields.Integer("Difference",compute="compute_difference")

    @api.depends('age_of_test','age_of_days')
    def compute_difference(self):
        for record in self:
            age_of_days = 0
            if record.age_of_days == '3days':
                age_of_days = 3
            elif record.age_of_days == '7days':
                age_of_days = 7
            elif record.age_of_days == '14days':
                age_of_days = 14
            elif record.age_of_days == '21days':
                age_of_days = 21
            elif record.age_of_days == '28days':
                age_of_days = 28
            elif record.age_of_days == '45days':
                age_of_days = 45
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
                if sample_record == '3':
                    record.age_of_days = '3days'
                elif sample_record == '7':
                    record.age_of_days = '7days'
                elif sample_record == '14':
                    record.age_of_days = '14days'
                elif sample_record == '21':
                    record.age_of_days = '21days'
                elif sample_record == '28':
                    record.age_of_days = '28days'
                elif sample_record == '45':
                    record.age_of_days = '45days'
                elif sample_record == '56':
                    record.age_of_days = '56days'
                elif sample_record == '112':
                    record.age_of_days = '112days'
                else:
                    record.age_of_days = None
            else:
                record.age_of_days = None

    @api.depends('average_morter_cube','eln_ref','grade','age_of_days','difference')
    def _compute_confirmity(self):
        for record in self:
            record.confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12547kluy-8d45-416c-b5e0-c9533235f188')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12547kluy-8d45-416c-b5e0-c9533235f188')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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
                    lower = record.average_morter_cube - record.average_morter_cube*mu_value
                    upper = record.average_morter_cube + record.average_morter_cube*mu_value
                    
                    if record.difference == 0:
                        if lower >= req_min and upper <= req_max :
                            record.confirmity = 'pass'
                            break
                        else:
                            record.confirmity = 'fail'
                    else:
                        record.confirmity = 'not_applicable'



    @api.depends('average_morter_cube','eln_ref','grade')
    def _compute_average_morter_cube_conformity(self):
        
        for record in self:
            record.average_morter_cube_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12547kluy-8d45-416c-b5e0-c9533235f188')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12547kluy-8d45-416c-b5e0-c9533235f188')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_morter_cube - record.average_morter_cube*mu_value
                    upper = record.average_morter_cube + record.average_morter_cube*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_morter_cube_conformity = 'pass'
                        break
                    else:
                        record.average_morter_cube_conformity = 'fail'

    average_morter_cube_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_morter_cube_nabl", store=True)

    @api.depends('average_morter_cube','eln_ref','grade')
    def _compute_average_morter_cube_nabl(self):
        
        for record in self:
            record.average_morter_cube_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12547kluy-8d45-416c-b5e0-c9533235f188')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12547kluy-8d45-416c-b5e0-c9533235f188')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_morter_cube - record.average_morter_cube*mu_value
                    upper = record.average_morter_cube + record.average_morter_cube*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_morter_cube_nabl = 'pass'
                        break
                    else:
                        record.average_morter_cube_nabl = 'fail'



      ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.morter_cube_visible = False
        
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
                if sample.internal_id == "12547kluy-8d45-416c-b5e0-c9533235f188":
                    record.morter_cube_visible = True

               





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
        record = super(MechanicalMorterCube, self).create(vals)
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
        record = self.env['mechanical.morter.cube1'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values




class MechanicalMorterCubeLine(models.Model):
    _name = "mechanical.morter.cube1.line"
    parent_id = fields.Many2one('mechanical.morter.cube1',string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.",readonly=True, copy=False, default=1)
    length = fields.Float(string="Length (mm)")
    width = fields.Float(string="Width (mm)")
    area = fields.Float(string="Area (mm²)",compute="_compute_morter_cube_area" ,digits=(12,2))
    id_mark = fields.Char(string="ID Mark/Location")
    wt_sample = fields.Float(string="Weight of Sample in kgs",digits=(16,3))
    crushing_load = fields.Float(string="Crushing Load in kN")
    compressive_strength = fields.Float(string="Compressive Strength N/mm²",compute="_compute_morter_cube_compressive_strength",digits=(12,2))


    @api.depends('length', 'width')
    def _compute_morter_cube_area(self):
        for record in self:
            record.area = round((record.length * record.width) , 4)


    @api.depends('crushing_load', 'area')
    def _compute_morter_cube_compressive_strength(self):
        for record in self:
            if record.area != 0:
                record.compressive_strength = record.crushing_load / record.area * 1000
            else:
                record.compressive_strength = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalMorterCubeLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in chequered_tiles_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1
