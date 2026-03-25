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


    wpt_name = fields.Char("Name",default=" Water Permeability Test")
    wpt_visible = fields.Boolean("WPT Visible",compute="_compute_visible") 

    wpt_child_lines = fields.One2many('mechanical.core.wpt.line','parent_id',string="Parameter")

    average_of_wpt = fields.Float(string="Average of WPT", compute="_compute_average_of_averages")

    @api.depends('wpt_child_lines.average')
    def _compute_average_of_averages(self):
        for record in self:
            if record.wpt_child_lines:
                record.average_of_wpt = round(sum(line.average for line in record.wpt_child_lines) / len(record.wpt_child_lines), 3)
            else:
                record.average_of_wpt = 0.0


    wpt_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_wpt_conformity", store=True)

    @api.depends('average_of_wpt','eln_ref','grade')
    def _compute_wpt_conformity(self):
        
        for record in self:
            record.wpt_conformity = 'fail'
            line = self.env['lerm.parameter.master'].search([('internal_id','=','30214uy-0268-46ef-ba88-9c04532103012t')])
            materials = self.env['lerm.parameter.master'].search([('internal_id','=','30214uy-0268-46ef-ba88-9c04532103012t')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_of_wpt - record.average_of_wpt*mu_value
                    upper = record.average_of_wpt + record.average_of_wpt*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.wpt_conformity = 'pass'
                        break
                    else:
                        record.wpt_conformity = 'fail'


    wpt_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL')], string="NABL", default='fail',compute="_compute_wpt_nabl", store=True)

    @api.depends('average_of_wpt','eln_ref','grade')
    def _compute_wpt_nabl(self):
        
        for record in self:
            record.wpt_nabl = 'fail'
            line = self.env['lerm.parameter.master'].search([('internal_id','=','30214uy-0268-46ef-ba88-9c04532103012t')])
            materials = self.env['lerm.parameter.master'].search([('internal_id','=','30214uy-0268-46ef-ba88-9c04532103012t')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_of_wpt - record.average_of_wpt*mu_value
            upper = record.average_of_wpt + record.average_of_wpt*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.wpt_nabl = 'pass'
                break
            else:
                record.wpt_nabl = 'fail'



    temp_wpt = fields.Float("Temperature °C")
    humidity_percent_wpt = fields.Float("Humidity %")
    quantity = fields.Char("Quantity")




    # 3. Water Absorption

    water_absorption_name = fields.Char("Name",default="Water Absorption ")
    water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")

    water_absorption_child_lines = fields.One2many('core.water.absorption.line','parent_id',string="Water Line")

    avg_water_absorption = fields.Float(
        string="Avg. Water Absorption (%)",
        compute="_compute_avg_water_absorption", store=True
    )

    @api.depends('water_absorption_child_lines.water_absorption')
    def _compute_avg_water_absorption(self):
        for rec in self:
            lines = rec.water_absorption_child_lines
            if lines:
                total = sum(line.water_absorption for line in lines)
                rec.avg_water_absorption = round(total / len(lines), 2)
            else:
                rec.avg_water_absorption = 0.0

    avg_water_absorption_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_water_absorption_conformity", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_conformity(self):
        
        for record in self:
            record.avg_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','02145jj-eba3-4f15-b33d-679b39f73301')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','02145jj-eba3-4f15-b33d-679b39f73301')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','02145jj-eba3-4f15-b33d-679b39f73301')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','02145jj-eba3-4f15-b33d-679b39f73301')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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






            ### Compute Visible
    @api.depends('eln_ref')
    def _compute_visible(self):
        
        for record in self:

            record.concrete_visible = False
            record.wpt_visible = False
            record.water_absorption_visible = False
          
            
            for sample in record.sample_parameters:

                if sample.internal_id == "254187-47c9-4662-9298-3095ac900ffc":
                    record.concrete_visible = True

                if sample.internal_id == "30214uy-0268-46ef-ba88-9c04532103012t":
                    record.wpt_visible = True

                if sample.internal_id == "02145jj-eba3-4f15-b33d-679b39f73301":
                    record.water_absorption_visible = True
                
             

               
               



    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()
        
            
            if result.parameter.internal_id == '254187-47c9-4662-9298-3095ac900ffc':
                # result.result_char = round(self.aggregate_elongation,2)
                result.calculated = True
                # if self.aggregate_combine_conformity == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue

            if result.parameter.internal_id == '30214uy-0268-46ef-ba88-9c04532103012t':
                result.result_char = round(self.average_of_wpt,2)
                result.calculated = True
                if self.wpt_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '02145jj-eba3-4f15-b33d-679b39f73301':
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
        record = super(ConcreteCore, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record
    

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()
        self.default_get(fields)

        return super(ConcreteCore, self).read(fields=fields, load=load)







    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
     
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
        record = self.env['mechanical.concrete.core'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

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


class WptMechanicalLine(models.Model):
    _name = "mechanical.core.wpt.line"
    parent_id = fields.Many2one('mechanical.concrete.core',string="Parent Id")

    sample = fields.Char(string="Sample")
    depth1 = fields.Float(string="Specimen 1")
    depth2 = fields.Float(string="Specimen 2")
    depth3 = fields.Float(string="Specimen 3")
    average = fields.Float(string="Average",compute="_compute_average")

    @api.depends('depth1','depth2','depth3')
    def _compute_average(self):
        for record in self:
            average = round(((record.depth1 + record.depth2 + record.depth3)/3),2)
            record.average = average


    # @api.depends('parent_id')
    # def _compute_sample_id(self):
    #     for record in self:
    #         try:
    #             record.sample = record.parent_id.eln_ref.sample_id.client_sample_id
    #         except:
    #             record.sample = None

    # @api.depends('parent_id')
    # def _compute_sample_id(self):
    #     for record in self:
    #         try:
    #             record.sample = record.parent_id.eln_ref.sample_id.client_sample_id
    #         except:
    #             record.sample = None


class WaterLine(models.Model):
    _name = "core.water.absorption.line"
    parent_id = fields.Many2one('mechanical.concrete.core',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sample_identification = fields.Float(string="Sample Identification")
    dry_wt_w1 = fields.Float(string="Dry wt (W1)")
    wet_w2 = fields.Float(string="Wet wt (W2)")
    water_absorption = fields.Float(string="  Water Absorption %",compute="_compute_water_absorption")

    @api.depends('dry_wt_w1', 'wet_w2')
    def _compute_water_absorption(self):
        for rec in self:
            if rec.dry_wt_w1:  # avoid division by zero
                rec.water_absorption = round(((rec.wet_w2 - rec.dry_wt_w1) / rec.dry_wt_w1) * 100, 2)
            else:
                rec.water_absorption = 0.0

   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(WaterLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

   