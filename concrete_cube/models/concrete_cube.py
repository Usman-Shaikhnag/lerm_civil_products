from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import math
from datetime import datetime, timedelta
import re
import logging

_logger = logging.getLogger(__name__)

class MechanicalConcreteCube(models.Model):
    _name = "mechanical.concrete.cube"
    _inherit = "lerm.eln"
    _description = 'mechanical.concrete.cube'
    _rec_name = "name"

    name = fields.Char("Name", default="Compressive Strength of Concrete Cube")
    cube_visible = fields.Boolean("Compressive Strength of Concrete Cube",compute="_compute_visible")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master', string="Parameters", compute="_compute_sample_parameters", store=True)
    child_lines = fields.One2many('mechanical.concrete.cube.line','parent_id',string="Parameter")
    
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="ELN")

    # Project Information
    project_name = fields.Char(string="Project Name")
    customer_address = fields.Char(string="Name and Address of Customer")
    report_no = fields.Char(string="Report No.")
    type_of_sample = fields.Selection([
        ('cube', 'Cast Concrete Cube'),
        ('cylinder', 'Cast Concrete Cylinder'),
    ], string="Type of Sample", default='cube')
    
    # Machine Details
    machine_details = fields.Char(string="Details of Machine", default="Automated")
    loading_capacity = fields.Float(string="Loading Capacity", default=2000)
    calibration_date = fields.Date(string="Calibration Date", default=fields.Date.today())
    
    # Environmental Conditions
    room_temperature = fields.Float(string="Room Temperature (°C)")
    relative_humidity = fields.Float(string="Relative Humidity (%)")
    curing_condition = fields.Selection([
        ('wet', 'Wet'),
        ('accelerated', 'Accelerated'),
    ], string="Curing Condition", default='wet')

    # Structure Details
    structure_details = fields.Char(string="Details of the structure", default="NA")

    def action_calculate_avg_strength(self):
        for rec in self:
            lines = rec.child_lines.sorted(key=lambda l: l.sr_no)
            group_size = 3

            for i in range(0, len(lines), group_size):
                group = lines[i:i + group_size]
                strengths = [l.compressive_strength for l in group if l.compressive_strength > 0]
                avg = sum(strengths) / len(strengths) if strengths else 0.0

                # Set average for first line in each group
                if group:
                    group[0].avg_compressive_strength = avg
                # Reset average for other lines in group
                for j in range(1, len(group)):
                    group[j].avg_compressive_strength = 0.0

    average_strength = fields.Float(string="Average Compressive Strength in N/mm2", compute="_compute_average_strength", digits=(12,2))

    @api.depends('child_lines.compressive_strength')
    def _compute_average_strength(self):
        for rec in self:
            strengths = [line.compressive_strength for line in rec.child_lines if line.compressive_strength]
            rec.average_strength = sum(strengths) / len(strengths) if strengths else 0.0

    @api.depends('eln_ref')
    def _compute_size_id(self):
        for record in self:
            if record.eln_ref:
                record.size_id = record.eln_ref.size_id.id
            else:
                record.size_id = False
                

    area_of_cube = fields.Float(string="Area of Cube", compute="_compute_area_cube", store=True)

    @api.depends('size_id.size')
    def _compute_area_cube(self):
        for record in self:
            size_str = record.size_id.size
            if size_str:
                match = re.search(r'\d+', str(size_str))
                if match:
                    side = int(match.group())
                    record.area_of_cube = side * side  # Area in mm²
                else:
                    record.area_of_cube = 0
            else:
                record.area_of_cube = 0

    days_7_kmm = fields.Float(string="7 Days", compute="_compute_days_7_kmm")
    days_7_n = fields.Float(string="7 Days", compute="_compute_days_7_n")
    

    @api.depends('days_28_kmm')
    def _compute_days_7_kmm(self):
        for rec in self:
            rec.days_7_kmm = rec.days_28_kmm * 0.67 if rec.days_28_kmm else 0.0

    @api.depends('days_7_kmm', 'area_of_cube')
    def _compute_days_7_n(self):
        for rec in self:
            # Convert N/mm² to kN: strength * area / 1000
            rec.days_7_n = (rec.days_7_kmm * rec.area_of_cube) / 1000 if rec.days_7_kmm and rec.area_of_cube else 0.0

    days_28_kmm = fields.Float(string="28 Days", compute="_compute_days_28_kmm", store=True)
    days_28_n = fields.Float(string="28 Days", compute="_compute_days_28_n")

    @api.depends('days_28_kmm', 'area_of_cube')
    def _compute_days_28_n(self):
        for rec in self:
            # Convert N/mm² to kN: strength * area / 1000
            rec.days_28_n = (rec.days_28_kmm * rec.area_of_cube) / 1000 if rec.days_28_kmm and rec.area_of_cube else 0.0

    @api.depends('grade2', 'grade_child_lines.grade1', 'grade_child_lines.sd')
    def _compute_days_28_kmm(self):
        for rec in self:
            rec.days_28_kmm = 0.0

            if not rec.grade2:
                continue

            grade2_str = rec.grade2.strip().lower()
            matching_line = rec.grade_child_lines.filtered(
                lambda l: l.grade1 and l.grade1.strip().lower() == grade2_str
            )

            if matching_line:
                line = matching_line[0]
                number_part = ''.join(filter(str.isdigit, rec.grade2))
                try:
                    grade_val = float(number_part)
                    rec.days_28_kmm = grade_val + (1.65 * line.sd)
                except (ValueError, TypeError):
                    rec.days_28_kmm = 0.0

    grade2 = fields.Char(string="Grade", compute="_compute_grade2", store=True)

    @api.depends('grade')
    def _compute_grade2(self):
        for rec in self:
            rec.grade2 = rec.grade.grade if rec.grade and rec.grade.grade else ''

    grade_child_lines = fields.One2many('mechanical.concrete.cube.grade.line','parent_id',string="Parameter",default=lambda self: self._default_grade_child_lines())

    @api.model
    def _default_grade_child_lines(self):
        default_lines = [
            (0, 0, {'grade1': 'M10', 'sd': 3.5}),
            (0, 0, {'grade1': 'M15', 'sd': 3.5}),
            (0, 0, {'grade1': 'M20', 'sd': 4.0}),
            (0, 0, {'grade1': 'M25', 'sd': 4.0}),
            (0, 0, {'grade1': 'M30', 'sd': 5.0}),
            (0, 0, {'grade1': 'M35', 'sd': 5.0}),
            (0, 0, {'grade1': 'M40', 'sd': 5.0}),
            (0, 0, {'grade1': 'M45', 'sd': 5.0}),
        ]
        return default_lines

    age_of_days = fields.Selection([
        ('3days', '3 Days'),
        ('7days', '7 Days'),
        ('14days', '14 Days'),
        ('28days', '28 Days'),
    ], string='Age', default='28days', required=True, compute="_compute_age_of_days")
    
    date_of_casting = fields.Date(string="Date of Casting", compute="_compute_date_of_casting")
    date_of_testing = fields.Date(string="Date of Testing", compute="_compute_date_testing")

    @api.depends('eln_ref')
    def _compute_date_testing(self):
        for record in self:
            if record.eln_ref:
                record.date_of_testing = record.eln_ref.date_testing
            else:
                record.date_of_testing = False

    confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
        
    ], 
   string='Conformity', default='fail', compute="_compute_confirmity")
    
    age_of_test = fields.Integer("Age of Test, days", compute="_compute_age_of_test")
    difference = fields.Integer("Difference", compute="_compute_difference")

    nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail', compute="_compute_nabl")



    average_strength_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
        
    ], string='Conformity', compute="_compute_average_strength_conformity")

    average_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_average_strength_nabl")


    @api.depends('average_strength','eln_ref','grade')
    def _compute_average_strength_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_strength_conformity = 'na'
                continue

            record.average_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6c89613-885c-4af1-bf19-f523bb56e0d9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6c89613-885c-4af1-bf19-f523bb56e0d9')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.average_strength - record.average_strength*mu_value
                    upper = record.average_strength + record.average_strength*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_strength_conformity = 'pass'
                        break
                    else:
                        record.average_strength_conformity = 'fail'

    @api.depends('average_strength','eln_ref','grade')
    def _compute_average_strength_nabl(self):
        
        for record in self:
            record.average_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6c89613-885c-4af1-bf19-f523bb56e0d9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6c89613-885c-4af1-bf19-f523bb56e0d9')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_strength - record.average_strength*mu_value
            upper = record.average_strength + record.average_strength*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_strength_nabl = 'pass'
                break
            else:
                record.average_strength_nabl = 'fail'

    @api.depends('age_of_test', 'age_of_days')
    def _compute_difference(self):
        for record in self:
            age_of_days = 0
            if record.age_of_days == '3days':
                age_of_days = 3
            elif record.age_of_days == '7days':
                age_of_days = 7
            elif record.age_of_days == '14days':
                age_of_days = 14
            elif record.age_of_days == '28days':
                age_of_days = 28
            else:
                age_of_days = 0
            record.difference = record.age_of_test - age_of_days

    @api.depends('date_of_testing', 'date_of_casting')
    def _compute_age_of_test(self):
        for record in self:
            if record.date_of_casting and record.date_of_testing:
                date1 = fields.Date.from_string(record.date_of_casting)
                date2 = fields.Date.from_string(record.date_of_testing)
                date_difference = (date2 - date1).days
                record.age_of_test = date_difference
            else:
                record.age_of_test = 0

    @api.depends('eln_ref')
    def _compute_date_of_casting(self):
        for record in self:
            if record.eln_ref and record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id', '=', record.eln_ref.sample_id.id)])
                record.date_of_casting = sample_record.date_casting
            else:
                record.date_of_casting = False

    @api.depends('eln_ref')
    def _compute_age_of_days(self):
        for record in self:
            if record.eln_ref and record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id', '=', record.eln_ref.sample_id.id)])
                days_casting = sample_record.days_casting
                if days_casting == '3':
                    record.age_of_days = '3days'
                elif days_casting == '7':
                    record.age_of_days = '7days'
                elif days_casting == '14':
                    record.age_of_days = '14days'
                elif days_casting == '28':
                    record.age_of_days = '28days'
                else:
                    record.age_of_days = '28days'  # default
            else:
                record.age_of_days = '28days'  # default

    def open_eln_page(self):
        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == 'd6c89613-885c-4af1-bf19-f523bb56e0d9':
                result.result_char = round(self.average_strength, 2)
                if self.nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                break

        return {
            'view_mode': 'form',
            'res_model': "lerm.eln",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.eln_ref.id,
        }

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        for record in self:
            if record.eln_ref:
                record.grade = record.eln_ref.grade_id.id
            else:
                record.grade = False

    @api.depends('average_strength', 'eln_ref', 'grade')
    def _compute_nabl(self):
        for record in self:
            record.nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', 'd6c89613-885c-4af1-bf19-f523bb56e0d9')])
            if line:
                lab_min = line.lab_min_value
                lab_max = line.lab_max_value
                mu_value = line.mu_value
                
                lower = record.average_strength - record.average_strength * mu_value
                upper = record.average_strength + record.average_strength * mu_value
                if lower >= lab_min and upper <= lab_max:
                    record.nabl = 'pass'
                else:
                    record.nabl = 'fail'

    @api.depends('average_strength', 'eln_ref', 'grade', 'age_of_days', 'difference')
    def _compute_confirmity(self):
        for record in self:

            for record in self:
             if not record.eln_ref or not record.eln_ref.conformity:
                record.confirmity = 'na'
                continue

            record.confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id', '=', 'd6c89613-885c-4af1-bf19-f523bb56e0d9')])
            if line:
                materials = line.parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        # Adjust requirements based on age
                        if record.age_of_days == "3days":
                            req_min = req_min * 0.5
                            req_max = req_max * 0.5
                        elif record.age_of_days == "7days":
                            req_min = req_min * 0.7
                            req_max = req_max * 0.7
                        elif record.age_of_days == "14days":
                            req_min = req_min * 0.9
                            req_max = req_max * 0.9
                        # 28 days uses full values
                        
                        lower = record.average_strength - record.average_strength * mu_value
                        upper = record.average_strength + record.average_strength * mu_value
                        
                        if record.difference == 0:
                            if lower >= req_min and upper <= req_max:
                                record.confirmity = 'pass'
                                break
                            else:
                                record.confirmity = 'fail'
                        else:
                            record.confirmity = 'not_applicable'

     ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        

        for record in self:
            record.cube_visible = False
            # record.slag_activity_7_visible = False

            # record.fineness_visible = False

            
            
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                
                if sample.internal_id == 'd6c89613-885c-4af1-bf19-f523bb56e0d9':
                    record.cube_visible = True
                # if sample.internal_id == '1452fgr0-8e67-4e94-86ea-98d9472f5c71':
                #     record.slag_activity_7_visible = True
                # if sample.internal_id == '5214hgtb-c526-4092-a3a7-6b0ff7e69c0a':
                #     record.fineness_visible = True
               


    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
                   
                    if result.parameter.internal_id == 'd6c89613-885c-4af1-bf19-f523bb56e0d9':
                        result.result_char = self.average_strength
                        if self._compute_average_strength_nabl == 'pass':
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
        record = super(MechanicalConcreteCube, self).create(vals)
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
        record = self.env['mechanical.ggbs'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    


class MechanicalConcreteCubeLine(models.Model):
    _name = "mechanical.concrete.cube.line"
    parent_id = fields.Many2one('mechanical.concrete.cube', string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    id_mark = fields.Char(string="Sample Identification", compute="_compute_id_mark",inverse="_inverse_id_mark", store=True)
    wt_sample = fields.Float(string="Weight of Cube (gms)", digits=(16, 3))
    
    # Dimensions
    length = fields.Float(string="Length (mm)")
    diameter = fields.Float(string="Diameter (mm)")
    
    dt_of_casting = fields.Date(string="Date of casting", compute="_compute_dt_of_casting", store=True)
    days = fields.Integer(string="No.of Days", compute="_compute_days", store=True)
    dt_of_testing1 = fields.Date(string="Date of Testing", compute="_compute_dt_of_testing", store=True)
    
    # Environmental conditions per sample
    room_temp = fields.Float(string="Room Temperature (°C)")
    relative_humidity = fields.Float(string="Relative Humidity (%)")
    
    load = fields.Float(string="Load (kN)")
    cross_sectional_area = fields.Float(string="Cross Sectional Area (mm²)", compute="_compute_cross_sectional_area")
    compressive_strength = fields.Float(string="Compressive Strength (N/mm²)", compute="_compute_strength", store=True)
    avg_compressive_strength = fields.Float(string="Avg. Compressive Strength (N/mm²)")
    
    # Type of Failure
    type_of_failure = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('unsatisfactory', 'Unsatisfactory'),
    ], string="Type of Failure", default='satisfactory')

    @api.depends('length', 'diameter', 'parent_id.type_of_sample')
    def _compute_cross_sectional_area(self):
        for record in self:
            if record.parent_id.type_of_sample == 'cube':
                # For cube: area = length * length (assuming square cross-section)
                record.cross_sectional_area = record.length * record.length
            else:
                # For cylinder: area = π * (diameter/2)^2
                if record.diameter:
                    record.cross_sectional_area = math.pi * (record.diameter / 2) ** 2
                else:
                    record.cross_sectional_area = 0.0

    @api.depends('load', 'cross_sectional_area')
    def _compute_strength(self):
        for record in self:
            if record.cross_sectional_area and record.load:
                # Compressive strength = (Load in kN * 1000) / Area in mm² = N/mm²
                record.compressive_strength = (record.load * 1000) / record.cross_sectional_area
            else:
                record.compressive_strength = 0.0

    @api.depends('parent_id.date_of_casting')
    def _compute_dt_of_casting(self):
        for record in self:
            record.dt_of_casting = record.parent_id.date_of_casting

    @api.depends('parent_id.age_of_days')
    def _compute_days(self):
        for record in self:
            if record.parent_id.age_of_days:
                try:
                    record.days = int(''.join(filter(str.isdigit, record.parent_id.age_of_days)))
                except Exception:
                    record.days = 0
            else:
                record.days = 0

    @api.depends('dt_of_casting', 'days')
    def _compute_dt_of_testing(self):
        for record in self:
            if record.dt_of_casting and record.days:
                record.dt_of_testing1 = record.dt_of_casting + timedelta(days=record.days)
            else:
                record.dt_of_testing1 = False

    @api.depends('parent_id.eln_ref.sample_id.client_sample_id')
    def _compute_id_mark(self):
        for record in self:
            if record.parent_id and record.parent_id.eln_ref and record.parent_id.eln_ref.sample_id:
                record.id_mark = record.parent_id.eln_ref.sample_id.client_sample_id
            else:
                record.id_mark = ""
    def _inverse_id_mark(self):
    # This allows manual editing
      for record in self:
        record.id_mark = record.id_mark
           

    @api.model
    def create(self, vals):
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1
            else:
                vals['sr_no'] = 1
        return super(MechanicalConcreteCubeLine, self).create(vals)

    def _reorder_serial_numbers(self):
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1

class MechanicalConcreteCubeGradeLine(models.Model):
    _name = "mechanical.concrete.cube.grade.line"
    parent_id = fields.Many2one('mechanical.concrete.cube', string="Parent Id")
    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    grade1 = fields.Char(string="Grade")
    sd = fields.Float(string="SD")

    @api.model
    def create(self, vals):
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1
            else:
                vals['sr_no'] = 1
        return super(MechanicalConcreteCubeGradeLine, self).create(vals)

    def _reorder_serial_numbers(self):
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1