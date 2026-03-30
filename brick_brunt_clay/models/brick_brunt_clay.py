from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class MechanicalBricksBurntClay(models.Model):
    _name = "mechanical.bricks.burnt.clay"
    _inherit = "lerm.eln"
    _rec_name = "name2"

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    name2 = fields.Char("Name",default="Clay Bricks")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")

    compressive_strength_unit = fields.Char(
    compute="_compute_units", store=False
    )
    water_absorption_unit = fields.Char(
        compute="_compute_units", store=False
    )

    lab_id = fields.Many2one(
    'lerm.lab.master',
    string="Lab",
    default=lambda self: self.env['lerm.lab.master'].search([], limit=1)
)
    

    notes_id = fields.One2many('bricks.burnt.clay.notes','parent_id',string="Notes")


    @api.model
    def default_get(self, fields):
        res = super(MechanicalBricksBurntClay, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The results relate only to the items tested ',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'This test report should not be reproduced except in full, without written approval of this Laboratory ',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'Any corrections invalidate the test reports ',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'Any Query regarding the report must be reported immediately.',
            }),
            (0, 0, {
                'sr_no': 'e',
                'notes': '* mark indicate tests which are not in the scope of NABL.',
            }),
            (0, 0, {
                'sr_no': 'f',
                'notes': '# mark indicates Details given by Client.',
            }),
        ]

        res['notes_id'] = default_notes
        return res

    def to_roman(self, num):
      val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4, 1
    ]
      syb = [
        "m", "cm", "d", "cd",
        "c", "xc", "l", "xl",
        "x", "ix", "v", "iv", "i"
    ]
      roman = ''
      i = 0
      while num > 0:
        for _ in range(num // val[i]):
            roman += syb[i]
            num -= val[i]
        i += 1
      return roman

    def _compute_units(self):
        for rec in self:
            comp_param = self.env['lerm.parameter.master'].search([
                ('internal_id', '=', '97928829-9b1f-4091-aa7f-4b76f98eb47f')
            ], limit=1)
            water_param = self.env['lerm.parameter.master'].search([
                ('internal_id', '=', '1ddc7095-da2d-44a2-a70a-ab97216aee77')
            ], limit=1)

            rec.compressive_strength_unit = comp_param.unit.name if comp_param.unit else ""
            rec.water_absorption_unit = water_param.unit.name if water_param.unit else ""

    length_in_mm = fields.Float(string="Length in mm")
    width_in_mm = fields.Float(string="Width in mm")
    height_in_mm = fields.Float(string="Height in mm")

        #1------------ Compressive Strength

    compressive_strength_visible = fields.Boolean("Compressive Strengt Visible",compute="_compute_visible")
    compressive_strength_name = fields.Char("Name",default="Compressive Strength")


    compressive_strength_lines = fields.One2many('mechanical.bricks.clay.compressive.line','parent_id',string="Parameter")

    avrg_compressive_strength = fields.Float(string="Average Compressive Strength",compute="_compute_avrg_compressive_strength")

    comp_strength_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_comp_strength_conformity")

    comp_strength_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_comp_strength_nabl",store=True)



    @api.depends('avrg_compressive_strength','eln_ref')
    def _compute_comp_strength_conformity(self):
        for record in self:
            record.comp_strength_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','97928829-9b1f-4091-aa7f-4b76f98eb47f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','97928829-9b1f-4091-aa7f-4b76f98eb47f')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avrg_compressive_strength - record.avrg_compressive_strength*mu_value
                    upper = record.avrg_compressive_strength + record.avrg_compressive_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.comp_strength_confirmity = 'pass'
                        break
                    else:
                        record.comp_strength_confirmity = 'fail'

    @api.depends('avrg_compressive_strength','eln_ref')
    def _compute_comp_strength_nabl(self):
        
        for record in self:
            record.comp_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','97928829-9b1f-4091-aa7f-4b76f98eb47f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','97928829-9b1f-4091-aa7f-4b76f98eb47f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avrg_compressive_strength - record.avrg_compressive_strength*mu_value
                    upper = record.avrg_compressive_strength + record.avrg_compressive_strength*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.comp_strength_nabl = 'pass'
                        break
                    else:
                        record.comp_strength_nabl = 'fail'

    

    

    @api.depends('compressive_strength_lines.comp_strength_1')
    def _compute_avrg_compressive_strength(self):
        for rec in self:
            comp_strength_1s = rec.compressive_strength_lines.filtered(lambda l: l.comp_strength_1 is not None)
            total = sum(line.comp_strength_1 for line in comp_strength_1s)
            count = len(comp_strength_1s)
            rec.avrg_compressive_strength = total / count if count > 0 else 0.0

      


        #-2----------Efflorescence Visual Observation 
    efflorescence_visible = fields.Boolean("Efflorescence Visible",compute="_compute_visible")
    visual_observation_name_efflorescence = fields.Char("Name",default="Efflorescence")
    visual_observation_1 = fields.Selection([('light', 'Light'), ('nil', 'Nil'), ('slight', 'Slight'), ('moderate', 'Moderate'), ('heavy', 'Heavy'), ('serious', 'Serious')],string='Visual observation')
    visual_observation_2 = fields.Selection([('light', 'Light'), ('nil', 'Nil'), ('slight', 'Slight'), ('moderate', 'Moderate'), ('heavy', 'Heavy'), ('serious', 'Serious')],string='Visual observation')
    visual_observation_3 = fields.Selection([('light', 'Light'), ('nil', 'Nil'), ('slight', 'Slight'), ('moderate', 'Moderate'), ('heavy', 'Heavy'), ('serious', 'Serious')],string='Visual observation')
    visual_observation_4 = fields.Selection([('light', 'Light'), ('nil', 'Nil'), ('slight', 'Slight'), ('moderate', 'Moderate'), ('heavy', 'Heavy'), ('serious', 'Serious')],string='Visual observation')
    visual_observation_5 = fields.Selection([('light', 'Light'), ('nil', 'Nil'), ('slight', 'Slight'), ('moderate', 'Moderate'), ('heavy', 'Heavy'), ('serious', 'Serious')],string='Visual observation')


         #-3----------  Dimension As per IS: IS : 1077 -1992 

    dimension_visible = fields.Boolean("Efflorescence Visible",compute="_compute_visible")
    dimension_name1 = fields.Char("Name",default="Dimension (mm)")
    avrg_length = fields.Float(string="Average length")
    avrg_width = fields.Float(string="Average Width")
    avrg_height = fields.Float(string="Average Height")

    

    #-4--------------  Water Absorption

    water_absorbtion_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")
    wt_absorption_name = fields.Char("Name",default="Water Absorption")
    water_absorption_lines = fields.One2many('mechanical.bricks.clay.water.absorption.line','parent_id',string="Parameter")
   
    avrg_water_absorption = fields.Float(string="Average Water Absorption, %", compute="_compute_avrg_water_absorption")
    @api.depends('water_absorption_lines.water_absorption')
    def _compute_avrg_water_absorption(self):
        for rec in self:
            water_absorptions = rec.water_absorption_lines.filtered(lambda l: l.water_absorption is not None)
            total = sum(line.water_absorption for line in water_absorptions)
            count = len(water_absorptions)
            rec.avrg_water_absorption = total / count if count > 0 else 0.0

    water_absorption_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_water_absorption_confirmity")

    water_absorption_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_water_absorption_nabl",store=True)


    @api.depends('avrg_water_absorption','eln_ref')
    def _compute_water_absorption_confirmity(self):
        for record in self:
            record.water_absorption_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1ddc7095-da2d-44a2-a70a-ab97216aee77')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1ddc7095-da2d-44a2-a70a-ab97216aee77')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avrg_water_absorption - record.avrg_water_absorption*mu_value
                    upper = record.avrg_water_absorption + record.avrg_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.water_absorption_confirmity = 'pass'
                        break
                    else:
                        record.water_absorption_confirmity = 'fail'

    @api.depends('avrg_water_absorption','eln_ref')
    def _compute_water_absorption_nabl(self):
        
        for record in self:
            record.water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1ddc7095-da2d-44a2-a70a-ab97216aee77')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1ddc7095-da2d-44a2-a70a-ab97216aee77')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avrg_water_absorption - record.avrg_water_absorption*mu_value
                    upper = record.avrg_water_absorption + record.avrg_water_absorption*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.water_absorption_nabl = 'pass'
                        break
                    else:
                        record.water_absorption_nabl = 'fail'

    

    

    confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail')


    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.compressive_strength_visible = False
            record.water_absorbtion_visible = False
            record.efflorescence_visible = False
            record.dimension_visible = False

            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
                if sample.internal_id == "97928829-9b1f-4091-aa7f-4b76f98eb47f":
                    record.compressive_strength_visible = True
                if sample.internal_id == "1ddc7095-da2d-44a2-a70a-ab97216aee77":
                    record.water_absorbtion_visible = True
                if sample.internal_id == "9dda88ca-75fa-4e60-bcac-3cf6609386ce":
                    record.efflorescence_visible = True
                if sample.internal_id == "9f1689be-107d-4e30-9d3d-2aff6292264d":
                    record.dimension_visible = True 

                
     
    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        current_user = self.env.user
            # 🔹 Only results assigned to current technician
        if current_user.has_group('lerm_civil.lerm_discipline_group'):
            technician_results = self.eln_ref.parameters_result
        else:
            technician_results = self.eln_ref.parameters_result.filtered(
                lambda r: r.technician == current_user
            )

        for result in technician_results:

           # Compressive Strength
            if result.parameter.internal_id == '97928829-9b1f-4091-aa7f-4b76f98eb47f':
                result.result_char = round(self.avrg_compressive_strength,2)
                result.calculated = True
                if self.comp_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             #  Efforescence
            if result.parameter.internal_id == '1ddc7095-da2d-44a2-a70a-ab97216aee77':
                result.result_char = round(self.avrg_water_absorption,2)
                result.calculated = True
                if self.water_absorption_nabl == 'pass':
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
        record = super(MechanicalBricksBurntClay, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
    

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
        record = self.env['mechanical.bricks.burnt.clay'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



class CompressiveLine(models.Model):
    _name = "mechanical.bricks.clay.compressive.line"
    parent_id = fields.Many2one('mechanical.bricks.burnt.clay',string="Parent Id")

    serial_no = fields.Integer(string="sample", readonly=True, copy=False, default=1)
    identification_mark = fields.Char(string="Identification Mark")
    length = fields.Float(string="Length mm")
    width = fields.Float(string="Width mm")
    height = fields.Float(string="Height mm")
    area = fields.Float(string="Area (mm²)", digits=(12,4),compute="_compute_area")
    load = fields.Float(string=" Load in, Kn", digits=(12,1))
    comp_strength_1 = fields.Float(string="Compressive strength MPa",compute="_compute_comp_strength_1")




    @api.depends('length', 'width')
    def _compute_area(self):
        for record in self:
            record.area = record.length * record.width

    @api.depends('load', 'area')
    def _compute_comp_strength_1(self):
        for record in self:
            if record.area != 0:
                record.comp_strength_1 = record.load / record.area * 1000
            else:
                record.comp_strength_1 = 0.0
   
   
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CompressiveLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class WaterAbsorptionLine(models.Model):
    _name = "mechanical.bricks.clay.water.absorption.line"
    parent_id = fields.Many2one('mechanical.bricks.burnt.clay',string="Parent Id")

    serial_no = fields.Integer(string="sample", readonly=True, copy=False, default=1)
    identification_mark = fields.Char(string="Identification Mark")
    initial_wt = fields.Float(string="Initial wt after 24 hr emersion water)")
    final_wt = fields.Float(string="Final wt after 24 hr oven")
    water_absorption = fields.Float(string="Water Absorption %", compute="_compute_water_absorption")

    @api.depends('initial_wt' , 'final_wt')
    def _compute_water_absorption(self):
        for record in self:
            if record.final_wt != 0:
                record.water_absorption = (record.initial_wt - record.final_wt) / record.final_wt * 100
            else:
                record.water_absorption = 0
    



   
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(WaterAbsorptionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class BricksBurntClayNotes(models.Model):
    _name = "bricks.burnt.clay.notes"

    parent_id = fields.Many2one('mechanical.bricks.burnt.clay',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
