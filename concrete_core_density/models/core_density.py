from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
from datetime import datetime , timedelta


class MechanicalConcreteCoreDensity(models.Model):
    _name = "mechanical.concrete.core.density"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default=" Concrete Core Density")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="ELN")
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)


    notes_id = fields.One2many('mechanical.concrete.core.density.notes', 'parent_id', string="Notes",ondelete='cascade')
    
    @api.model
    def default_get(self, fields):
        res = super(MechanicalConcreteCoreDensity, self).default_get(fields)

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
    
    # age_of_days = fields.Selection([
    #     ('3days', '3 Days'),
    #     ('7days', '7 Days'),
    #     ('14days', '14 Days'),
    #     ('21days', '21 Days'),
    #     ('28days', '28 Days'),
    #     ('45days', '45 Days'),
    #     ('56days', '56 Days'),
    #     ('112days', '112 Days'),
    # ], string='Age', default='28days',required=True,compute="_compute_age_of_days")
    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")
    # date_of_testing = fields.Date(string="Date of Testing")

    child_lines_core_density = fields.One2many('concrete.core.density.line','parent_id',string="Parameter")

    average_core_density = fields.Float(string="Avg (kg/m3)",compute="_compute_average_core_density")


    average_core_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--'),
            ], string="Conformity", compute="_compute_average_core_density_conformity", store=True)



    @api.depends('average_core_density','eln_ref','grade')
    def _compute_average_core_density_conformity(self):
        
        for record in self:
            record.average_core_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35487lkt3-7a9c-4616-bad5-88eb1b29087y')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35487lkt3-7a9c-4616-bad5-88eb1b29087y')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                    # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.average_core_density_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_core_density - record.average_core_density*mu_value
                    upper = record.average_core_density + record.average_core_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_core_density_conformity = 'pass'
                        break
                    else:
                        record.average_core_density_conformity = 'fail'

    average_core_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_core_density_nabl", store=True)

    @api.depends('average_core_density','eln_ref','grade')
    def _compute_average_core_density_nabl(self):
        
        for record in self:
            record.average_core_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35487lkt3-7a9c-4616-bad5-88eb1b29087y')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','35487lkt3-7a9c-4616-bad5-88eb1b29087y')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_core_density - record.average_core_density*mu_value
                    upper = record.average_core_density + record.average_core_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_core_density_nabl = 'pass'
                        break
                    else:
                        record.average_core_density_nabl = 'fail'



    @api.depends('child_lines_core_density.density')
    def _compute_average_core_density(self):
        for record in self:
            total_value = sum(record.child_lines_core_density.mapped('density'))
            record.average_core_density = round((total_value / len(record.child_lines_core_density) if record.child_lines_core_density else 0.0),2)

   
   
    
    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None



    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

            if result.parameter.internal_id == '35487lkt3-7a9c-4616-bad5-88eb1b29087y':
                result.result_char = round(self.average_core_density,2)
                result.calculated = True
                if self.average_core_density_nabl == 'pass':
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
        record = super(MechanicalConcreteCoreDensity, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record
    

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        # records = self.env['lerm.eln'].search([('id','=', record.eln_id.id)]).parameters_result
        # print("records",records)
        # self.sample_parameters = records
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['mechanical.concrete.core.density'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values





class ConcreteCoreDensityLine(models.Model):
    _name = "concrete.core.density.line"
    parent_id = fields.Many2one('mechanical.concrete.core.density',string="Parent Id")

    sr_no = fields.Integer(string="Sample",readonly=True, copy=False, default=1)
    id_location = fields.Char(string="ID MARK/ Location")
    weight = fields.Float(string="Weight ( Kg )",digits=(12,3))
    daimeter = fields.Float(string="Daimeter ( mm )",digits=(12,2))
    height = fields.Float(string="Height  ( mm )" ,digits=(12,2))
    volume = fields.Float(string="Volume (mm3)",compute="_compute_volume_and_density", store=True,digits=(12,2))
    density = fields.Float(string="Density (Kg/m3 )",compute="_compute_volume_and_density", store=True,digits=(16,2))


    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        for record in self:
            parent = record.parent_id.sudo()
            sample_id = parent.eln_ref.sample_id.client_sample_id
            if sample_id:
                record.id_location = sample_id
            else:
                record.id_location = ""

    @api.onchange('id_location')
    def _onchange_id_location(self):
        for record in self:
            if record.id_location and not record.parent_id.eln_ref.sample_id.client_sample_id:
                record.parent_id.eln_ref.sample_id.client_sample_id = record.id_location


    @api.depends('daimeter', 'height', 'weight')
    def _compute_volume_and_density(self):
        for record in self:
            if record.daimeter and record.height:
                # Calculate volume in mm³ using the formula: π/4 * d^2 * h
                record.volume = 3.14 / 4 * (record.daimeter ** 2) * record.height
            else:
                record.volume = 0.0

            if record.volume > 0 and record.weight:
                # Convert volume from mm³ to m³ and compute density
                record.density = record.weight / (record.volume / 1e9)  # since 1 m³ = 1e9 mm³
            else:
                record.density = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(ConcreteCoreDensityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class ConcreteCoreDensityNotes(models.Model):
    _name = "mechanical.concrete.core.density.notes"

    parent_id = fields.Many2one('mechanical.concrete.core.density',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")