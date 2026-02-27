from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math



class ConcreteCore(models.Model):
    _name = "mechanical.concrete.core"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Concrete Core")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'concrete.core.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    age_of_days = fields.Selection([
        ('3days', '3 Days'),
        ('7days', '7 Days'),
        ('14days', '14 Days'),
        ('28days', '28 Days'),
    ], string='Age', default='28days',required=True,compute="_compute_age_of_days")
    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")
    date_of_testing = fields.Date(string="Date of Testing",compute="_compute_date_testing")

    @api.depends('eln_ref')
    def _compute_date_testing(self):
        if self.eln_ref:
            self.date_of_testing = self.eln_ref.date_testing

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

    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None



    
      # Dimensions

    concrete_visible = fields.Boolean("Dimensions Visible",compute="_compute_visible")   


    dia_lines = fields.One2many('mechanical.concrete.core.dia.line','parent_id',string="Dia Line",default=lambda self: self._default_dia_lines())

    @api.model
    def _default_dia_lines(self):
        default_lines = [
            (0, 0, {'dia_core': 143, 'correction_dia': 1}),
            (0, 0, {'dia_core': 94, 'correction_dia': 1.08}),
            
        ]
        return default_lines


    thickness2 = fields.Float(string="Thickness of Paver Block:",compute="_compute_thickness2")

    @api.depends('size_id')
    def _compute_thickness2(self):
        for rec in self:
            rec.thickness2 = rec.size_id.size if rec.size_id and rec.size_id.size else 0.0

   


   
    child_lines = fields.One2many('mechanical.concrete.core.line','parent_id',string="Concrete Core Line")
   

    # dia_core = fields.Float("Dia of core:")
  
    area_core = fields.Float("Area mm2 :",compute="_compute_area_core")

    @api.depends('thickness2')
    def _compute_area_core(self):
        for record in self:
            record.area_core = (3.14 * record.thickness2 * record.thickness2) / 4 if record.thickness2 else 0


    type_of_sample = fields.Char("Type of Sample:")


    area_equvalent_cube = fields.Float(string="The Average Equivalent Cube strength of core is equal to atleast 85 % of  Cube strength of the grade of concrete specified :",compute="_compute_area_equivalent_cube")
    any_individual_cube = fields.Float(string="Any individual Cube strength computed not less than 75% of the grade of Concrete specified :  ",compute="_compute_any_individual_cube")

    @api.depends('grade.grade')
    def _compute_area_equivalent_cube(self):
        for rec in self:
            try:
                grade_num = float(rec.grade.grade.strip('Mm'))  # 'M25' → 25
                rec.area_equvalent_cube = grade_num * 0.85
            except:
                rec.area_equvalent_cube = 0.0

    @api.depends('grade.grade')
    def _compute_any_individual_cube(self):
        for rec in self:
            try:
                grade_val = float(rec.grade.grade.strip('Mm'))  # 'M25' → 25
                rec.any_individual_cube = grade_val * 0.75
            except:
                rec.any_individual_cube = 0.0

    


    # @api.depends('child_lines.final_cube_strength')
    # def _compute_average(self):
    #     for record in self:
    #         total_value = sum(record.child_lines.mapped('final_cube_strength'))
    #         record.average = round((total_value / len(record.child_lines) if record.child_lines else 0.0),2)





            ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.concrete_visible = False
          
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
                if sample.internal_id == "254187-47c9-4662-9298-3095ac900ffc":
                    record.concrete_visible = True
                
             

               
               



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
        record = super(ConcreteCore, self).create(vals)
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
        record = self.env['mechanical.concrete.core'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    def open_eln_page(self):
        # import wdb; wdb.set_trace()

        return {
                'view_mode': 'form',
                'res_model': "lerm.eln",
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.eln_ref.id,
                
            }



class ConcreteCoreLine(models.Model):
    _name = "mechanical.concrete.core.line"
    parent_id = fields.Many2one('mechanical.concrete.core',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    location = fields.Char(string="Location")
    grade_con = fields.Date(string="Grade of  Concrite")
    depth = fields.Float(string="Depth after Trimming in mm")
    actual_depth = fields.Float(string="Actual Depth of Core in mm")
    load = fields.Float(string="Load kN")
    ld_ratio = fields.Float(string=" L /D RATIO  ",compute="_compute_ld_ratio")
    load_n = fields.Float(string="Load in N ",compute="_compute_load_n")
    core_comp = fields.Float(string="Core Comp., strength N/ mm2",compute="_compute_core_comp")
    correction_factor_ld = fields.Float(string="Correction Factor LD",compute="_compute_correction_factor_ld")
    correction_factor_dia = fields.Float(string="Correction Factor Dia",compute="_compute_correction_factor")
    correct_comp = fields.Float(string="Corrected Cyl.Comp.strength  N/ mm2",compute="_compute_corrected_compression")
    equivalent_cube = fields.Float(string="Equivalent Cube.Comp Strength  (N/ mm2)",compute="_compute_equivalent_cube")

    @api.depends('parent_id.thickness2', 'parent_id.dia_lines')
    def _compute_correction_factor(self):
        for line in self:
            correction = 0.0
            core_dia_value = line.parent_id.thickness2
            if core_dia_value and line.parent_id.dia_lines:
                matched_line = line.parent_id.dia_lines.filtered(
                    lambda l: float(l.dia_core) == float(core_dia_value)
                )
                if matched_line:
                    correction = matched_line[0].correction_dia
            line.correction_factor_dia = correction



    # @api.depends('parent_id.dia_core', 'parent_id.dia_lines')
    # def _compute_correction_factor_dia(self):
    #     for line in self:
    #         correction = ''
    #         core_dia_value = line.parent_id.dia_core
    #         if core_dia_value and line.parent_id.dia_lines:
    #             matched_line = line.parent_id.dia_lines.filtered(lambda l: float(l.dia_core) == core_dia_value)
    #             if matched_line:
    #                 correction = matched_line[0].correction_dia
    #         line.correction_factor_dia = correction


    @api.depends('depth', 'parent_id.thickness2')
    def _compute_ld_ratio(self):
        for record in self:
            if record.parent_id.thickness2:
                record.ld_ratio = record.depth / record.parent_id.thickness2
            else:
                record.ld_ratio = 0

    @api.depends('load')
    def _compute_load_n(self):
        for record in self:
            record.load_n = record.load * 1000 if record.load else 0

    @api.depends('load_n', 'parent_id.area_core')
    def _compute_core_comp(self):
        for record in self:
            if record.parent_id.area_core:
                record.core_comp = record.load_n / record.parent_id.area_core
            else:
                record.core_comp = 0

    @api.depends('ld_ratio')
    def _compute_correction_factor_ld(self):
        for record in self:
            if record.ld_ratio:
                record.correction_factor_ld = (0.11 * record.ld_ratio) + 0.78
            else:
                record.correction_factor_ld = 0

    @api.depends('core_comp', 'correction_factor_ld', 'correction_factor_dia')
    def _compute_corrected_compression(self):
        for rec in self:
            try:
                rec.correct_comp = rec.core_comp * rec.correction_factor_ld * rec.correction_factor_dia
            except:
                rec.correct_comp = 0

    @api.depends('correct_comp')
    def _compute_equivalent_cube(self):
        for rec in self:
            rec.equivalent_cube = rec.correct_comp * 1.25 if rec.correct_comp else 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ConcreteCoreLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class ConcreteCoreDiaLine(models.Model):
    _name = "mechanical.concrete.core.dia.line"
    parent_id = fields.Many2one('mechanical.concrete.core',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    dia_core = fields.Char(string="Dia of Core, mm")
    correction_dia = fields.Char(string="Correction Factor for dia")

   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ConcreteCoreDiaLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1
   