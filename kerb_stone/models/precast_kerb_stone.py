from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class PrecastKerbMechanical(models.Model):
    _name = "mechanical.precast.kerb"
    _inherit = "lerm.eln"
    _rec_name = "name"


    name = fields.Char("Name",default="Precast Kerb Stone")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")
    
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    notes_id = fields.One2many('mechanical.precast.kerb.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(PrecastKerbMechanical, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The information marked with an # received from customer',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'The results listed refer only to tested parameters and sample as received from customer',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'The balance samples if any will be discarded after 15 days from the date of issue of test certificate unless otherwise specified.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'This document shall not be reproduced in part or full without the approval of Knack.',
            }),
        ]

        res['notes_id'] = default_notes
        return res


    # Dimension
    dimension_name = fields.Char(default="Dimension")
    dimension_visible = fields.Boolean(compute="_compute_visible")

    dimension_table = fields.One2many('kerb.dimension.line','parent_id')


    avg_length = fields.Float(string='Average Length',compute='_compute_averages',store=True)

    avg_width = fields.Float(string='Average Width',compute='_compute_averages',store=True)

    avg_height = fields.Float(string='Average Height',compute='_compute_averages',store=True)

    @api.depends('dimension_table.length','dimension_table.width','dimension_table.height')
    def _compute_averages(self):
        for record in self:
            specimens = record.dimension_table

            if specimens:
                record.avg_length = sum(specimens.mapped('length')) / len(specimens)

                record.avg_width = sum(specimens.mapped('width')) / len(specimens)

                record.avg_height = sum(specimens.mapped('height')) / len(specimens)
            else:
                record.avg_length = 0
                record.avg_width = 0
                record.avg_height = 0


    avg_length_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')], string="Conformity", compute="_compute_avg_length_conformity", store=True)

    @api.depends('avg_length','eln_ref','grade')
    def _compute_avg_length_conformity(self):
        
        for record in self:
            record.avg_length_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1d1f881d-7D75-40E1-BC34-fe8c1aedb001')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1d1f881d-7D75-40E1-BC34-fe8c1aedb001')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.avg_length_conformity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_length - record.avg_length*mu_value
                    upper = record.avg_length + record.avg_length*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_length_conformity = 'pass'
                        break
                    else:
                        record.avg_length_conformity = 'fail'

    avg_length_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_length_nabl", store=True)
    
    @api.depends('avg_length','eln_ref','grade')
    def _compute_avg_length_nabl(self):
        
        for record in self:
            record.avg_length_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1d1f881d-7D75-40E1-BC34-fe8c1aedb001')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1d1f881d-7D75-40E1-BC34-fe8c1aedb001')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_length - record.avg_length*mu_value
            upper = record.avg_length + record.avg_length*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_length_nabl = 'pass'
                break
            else:
                record.avg_length_nabl = 'fail'


    avg_width_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')], string="Conformity", compute="_compute_avg_width_conformity", store=True)

    @api.depends('avg_width','eln_ref','grade')
    def _compute_avg_width_conformity(self):
        
        for record in self:
            record.avg_width_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','81015601-E2DE-4D9C-8AFB-55b0c69a4582')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','81015601-E2DE-4D9C-8AFB-55b0c69a4582')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.avg_width_conformity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_width - record.avg_width*mu_value
                    upper = record.avg_width + record.avg_width*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_width_conformity = 'pass'
                        break
                    else:
                        record.avg_width_conformity = 'fail'

    avg_width_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_width_nabl", store=True)
    
    @api.depends('avg_width','eln_ref','grade')
    def _compute_avg_width_nabl(self):
        
        for record in self:
            record.avg_width_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','81015601-E2DE-4D9C-8AFB-55b0c69a4582')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','81015601-E2DE-4D9C-8AFB-55b0c69a4582')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_width - record.avg_width*mu_value
            upper = record.avg_width + record.avg_width*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_width_nabl = 'pass'
                break
            else:
                record.avg_width_nabl = 'fail'


    avg_height_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')], string="Conformity", compute="_compute_avg_height_conformity", store=True)

    @api.depends('avg_height','eln_ref','grade')
    def _compute_avg_height_conformity(self):
        
        for record in self:
            record.avg_height_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fb111d38-305A-40BF-B5AD-50c66529314c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fb111d38-305A-40BF-B5AD-50c66529314c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.avg_height_conformity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_height - record.avg_height*mu_value
                    upper = record.avg_height + record.avg_height*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_height_conformity = 'pass'
                        break
                    else:
                        record.avg_height_conformity = 'fail'

    avg_height_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_height_nabl", store=True)
    
    @api.depends('avg_height','eln_ref','grade')
    def _compute_avg_height_nabl(self):
        
        for record in self:
            record.avg_height_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fb111d38-305A-40BF-B5AD-50c66529314c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fb111d38-305A-40BF-B5AD-50c66529314c')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_height - record.avg_height*mu_value
            upper = record.avg_height + record.avg_height*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_height_nabl = 'pass'
                break
            else:
                record.avg_height_nabl = 'fail'


    # Transverse Strength
    transverse_name = fields.Char(default="Transverse Strength")
    transverse_visible = fields.Boolean("Transverse Strength Visible",compute="_compute_visible")

    transverse_tables = fields.One2many('mech.precast.transverse.line','parent_id')

    avg_failure_load = fields.Float(
        string='Average Failure Load (kN)',
        compute='_compute_transverse_average',
        store=True,
        digits=(16, 1)
    )

    avrg_transverse_strength = fields.Float(
        string='Average Transverse Strength (MPa)',
        compute='_compute_transverse_average',
        digits=(16, 2)
    )

    @api.depends(
        'transverse_tables.failure_load',
        'transverse_tables.transverse_strength'
    )
    def _compute_transverse_average(self):
        for record in self:
            lines = record.transverse_tables

            if lines:
                record.avg_failure_load = (
                    sum(lines.mapped('failure_load')) / len(lines)
                )

                record.avrg_transverse_strength = (
                    sum(lines.mapped('transverse_strength')) / len(lines)
                )
            else:
                record.avg_failure_load = 0.0
                record.avrg_transverse_strength = 0.0


    avrg_transverse_strength_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')], string="Conformity", compute="_compute_avrg_transverse_strength_conformity", store=True)

    @api.depends('avrg_transverse_strength','eln_ref','grade')
    def _compute_avrg_transverse_strength_conformity(self):
        
        for record in self:
            record.avrg_transverse_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1e56b2c9-e3fd-47e0-8908-2a813cc965e1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1e56b2c9-e3fd-47e0-8908-2a813cc965e1')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.avrg_transverse_strength_conformity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avrg_transverse_strength - record.avrg_transverse_strength*mu_value
                    upper = record.avrg_transverse_strength + record.avrg_transverse_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avrg_transverse_strength_conformity = 'pass'
                        break
                    else:
                        record.avrg_transverse_strength_conformity = 'fail'

    avrg_transverse_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avrg_transverse_strength_nabl", store=True)
    
    @api.depends('avrg_transverse_strength','eln_ref','grade')
    def _compute_avrg_transverse_strength_nabl(self):
        
        for record in self:
            record.avrg_transverse_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1e56b2c9-e3fd-47e0-8908-2a813cc965e1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1e56b2c9-e3fd-47e0-8908-2a813cc965e1')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avrg_transverse_strength - record.avrg_transverse_strength*mu_value
            upper = record.avrg_transverse_strength + record.avrg_transverse_strength*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avrg_transverse_strength_nabl = 'pass'
                break
            else:
                record.avrg_transverse_strength_nabl = 'fail'
    
    
    

    # Water Absorbtion
    water_absorbtion_name = fields.Char(default="Water Absorption")
    water_absorbtion_visible = fields.Boolean(compute="_compute_visible")

    water_absorbtion_table = fields.One2many('mech.precast.water.absorbtion.line','parent_id')

    avg_water_absorption = fields.Float(string='Average Water Absorption (%)',compute='_compute_water_absorption_average',digits=(16, 2))

    @api.depends(
        'water_absorbtion_table.water_absorption'
    )
    def _compute_water_absorption_average(self):
        for record in self:
            lines = record.water_absorbtion_table

            if lines:
                record.avg_water_absorption = (
                    sum(lines.mapped('water_absorption')) / len(lines)
                )
            else:
                record.avg_water_absorption = 0.0


    avg_water_absorption_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')], string="Conformity", compute="_compute_avg_water_absorption_conformity", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_conformity(self):
        for record in self:
            record.avg_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','29fc5579-2637-420d-91e6-b433d79f3584')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','29fc5579-2637-420d-91e6-b433d79f3584')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.avg_water_absorption_conformity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_water_absorption - record.avg_water_absorption*mu_value
                    upper = record.avg_water_absorption + record.avg_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_water_absorption_conformity = 'pass'
                        break
                    else:
                        record.avg_water_absorption_conformity = 'fail'

    avg_water_absorption_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_water_absorption_nabl", store=True)
    
    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_nabl(self):
        
        for record in self:
            record.avg_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','29fc5579-2637-420d-91e6-b433d79f3584')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','29fc5579-2637-420d-91e6-b433d79f3584')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_water_absorption - record.avg_water_absorption*mu_value
            upper = record.avg_water_absorption + record.avg_water_absorption*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_water_absorption_nabl = 'pass'
                break
            else:
                record.avg_water_absorption_nabl = 'fail'


    max_specimen_count = fields.Integer(
    compute="_compute_max_specimen_count",
    store=True)

    @api.depends('dimension_table','transverse_tables','water_absorbtion_table')
    def _compute_max_specimen_count(self):
     for record in self:
        record.max_specimen_count = max(
            len(record.dimension_table),
            len(record.transverse_tables),
            len(record.water_absorbtion_table)
        )




    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.dimension_visible = False
            record.transverse_visible = False
            record.water_absorbtion_visible = False  

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == '1d1f881d-7D75-40E1-BC34-fe8c1aedb001':
                    record.dimension_visible = True

                if sample.internal_id == '81015601-E2DE-4D9C-8AFB-55b0c69a4582':
                    record.dimension_visible = True

                if sample.internal_id == 'fb111d38-305A-40BF-B5AD-50c66529314c':
                    record.dimension_visible = True

                if sample.internal_id == '1e56b2c9-e3fd-47e0-8908-2a813cc965e1':
                    record.transverse_visible = True

                if sample.internal_id == '29fc5579-2637-420d-91e6-b433d79f3584':
                    record.water_absorbtion_visible = True

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

            if result.parameter.internal_id == '1d1f881d-7D75-40E1-BC34-fe8c1aedb001':
                result.result_char = round(self.avg_length,2)
                result.calculated = True
                if self.avg_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '81015601-E2DE-4D9C-8AFB-55b0c69a4582':
                result.result_char = round(self.avg_width,2)
                result.calculated = True
                if self.avg_width_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == 'fb111d38-305A-40BF-B5AD-50c66529314c':
                result.result_char = round(self.avg_height,2)
                result.calculated = True
                if self.avg_height_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '1e56b2c9-e3fd-47e0-8908-2a813cc965e1':
                result.result_char = round(self.avrg_transverse_strength,2)
                result.calculated = True
                if self.avrg_transverse_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '29fc5579-2637-420d-91e6-b433d79f3584':
                result.result_char = round(self.avg_water_absorption,2)
                result.calculated = True
                if self.avg_water_absorption_nabl == 'pass':
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
        record = super(PrecastKerbMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    
    def get_all_fields(self):
        record = self.env['mechanical.precast.kerb'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        # records = self.env['lerm.eln'].search([('id','=', record.eln_id.id)]).parameters_result
        # print("records",records)
        # self.sample_parameters = records
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)


class KerbDimensionLine(models.Model):
    _name = "kerb.dimension.line"
    parent_id = fields.Many2one('mechanical.precast.kerb', string="Parent Id")

    sr_no = fields.Integer(string="Specimen No.", readonly=True, copy=False, default=1)
    length = fields.Float("Length (mm)")
    width = fields.Float("Width (mm)")
    height = fields.Float("Height (mm)")
    remarks = fields.Char("Remarks / Tolerance Status")


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(KerbDimensionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class PrecastTransverseLine(models.Model):
    _name = "mech.precast.transverse.line"
    parent_id = fields.Many2one('mechanical.precast.kerb', string="Parent Id")

    sr_no = fields.Integer(string="Specimen No.", readonly=True, copy=False, default=1)

    width = fields.Float(string='Width b (mm)')

    height = fields.Float(string='Height d (mm)')

    span = fields.Float(string='Span L (mm)',default=400.0)

    failure_load = fields.Float(string='Failure Load P (kN)')

    transverse_strength = fields.Float(string='Transverse Strength (MPa)',compute='_compute_transverse_strength',store=True,digits=(16, 2))

    @api.depends('width','height','span','failure_load')
    def _compute_transverse_strength(self):
        for record in self:
            if record.width and record.height and record.span and record.failure_load:
                record.transverse_strength = (
                    1.5
                    * record.failure_load
                    * 1000
                    * record.span
                    / (
                        record.width
                        * record.height ** 2
                    )
                )
            else:
                record.transverse_strength = 0.0



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(PrecastTransverseLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1
   




class PrecastWaterAbsorbtionLine(models.Model):
    _name = "mech.precast.water.absorbtion.line"
    parent_id = fields.Many2one('mechanical.precast.kerb', string="Parent Id")

    sr_no = fields.Integer(string="Specimen No.", readonly=True, copy=False, default=1)
    
    dry_weight = fields.Float(
        string='Dry Weight Wd (kg)',
        digits=(16, 3)
    )

    wet_weight = fields.Float(
        string='Wet Weight Ww (kg)',
        digits=(16, 3)
    )

    water_absorbed = fields.Float(
        string='Water Absorbed (kg)',
        compute='_compute_water_absorption',
        store=True,
        digits=(16, 3)
    )

    water_absorption = fields.Float(
        string='Water Absorption (%)',
        compute='_compute_water_absorption',
        store=True,
        digits=(16, 2)
    )

    @api.depends('dry_weight', 'wet_weight')
    def _compute_water_absorption(self):
        for record in self:
            if record.dry_weight and record.wet_weight:
                record.water_absorbed = (
                    record.wet_weight - record.dry_weight
                )

                record.water_absorption = (
                    (record.wet_weight - record.dry_weight)
                    / record.dry_weight
                ) * 100
            else:
                record.water_absorbed = 0.0
                record.water_absorption = 0.0




    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(PrecastWaterAbsorbtionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class PrecastStoneNotes(models.Model):
    _name = "mechanical.precast.kerb.notes"

    parent_id = fields.Many2one('mechanical.precast.kerb',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")





    

    