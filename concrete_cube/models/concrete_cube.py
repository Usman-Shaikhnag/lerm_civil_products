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
    cube_visible_14 = fields.Boolean("Compressive Strength of Concrete Cube",compute="_compute_visible")
    cube_visible_28= fields.Boolean("Compressive Strength of Concrete Cube",compute="_compute_visible")

    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master', string="Parameters", compute="_compute_sample_parameters", store=True)
    child_lines = fields.One2many('mechanical.concrete.cube.line','parent_id',string="Parameter")

    

    lab_id = fields.Char(
            string="Lab ID",
            compute="_compute_lab_id",
            store=True
        )

    @api.depends('eln_ref')
    def _compute_lab_id(self):
        for rec in self:
            if rec.eln_ref:
                rec.lab_id = rec.eln_ref.lab_id
            else:
                rec.lab_id = False


    days_casting1 = fields.Char(
        string='Days of Casting',
        compute="_compute_days_casting",
        store=True,
    )

    @api.depends('eln_ref')
    def _compute_days_casting(self):
        for rec in self:
            if rec.eln_ref:
                rec.days_casting1 = rec.eln_ref.days_casting
            else:
                rec.days_casting1 = False

    lab_cube_ids = fields.One2many(
        'cube.lab.line', 
        'parent_id', 
        string="Generated Options"
    )

     # --- Button Function ---
    def action_generate_options_cube(self):
        for record in self:
            # Step 1: Check if lab_id exists and has hyphen
            if record.lab_id and '-' in record.lab_id:
                try:
                    # Step 2: Clear old lines first (Previous options delete kara)
                    # (5, 0, 0) command saglya lines remove karte
                    lines_command = [(5, 0, 0)]
                    
                    # Step 3: String Parsing (Break Logic)
                    # Input: "S-25-144 - S-25-145"
                    parts = record.lab_id.split(' - ')
                    
                    if len(parts) >= 2:
                        start_part = parts[0].strip() # "S-25-144"
                        end_part = parts[-1].strip()  # "S-25-145"

                        # Prefix (S-25) ani Number (144) vegla kara
                        prefix = start_part.rsplit('-', 1)[0]
                        start_num = int(start_part.split('-')[-1])
                        end_num = int(end_part.split('-')[-1])

                        # Step 4: Loop ani Create Lines
                        for num in range(start_num, end_num + 1):
                            val = f"{prefix}-{num}"
                            # One2many madhe create karnya sathi: (0, 0, values)
                            lines_command.append((0, 0, {'lab': val}))

                        # Step 5: Assign to One2many field
                        record.lab_cube_ids = lines_command
                        
                except Exception as e:
                    # Jar format chukla tar error ignore kara
                    pass
            else:
                # Jar range nasel (single value asel), tar ti ekach value add kara
                if record.lab_id:
                     record.lab_cube_ids = [(5, 0, 0), (0, 0, {'lab': record.lab_id})]

    casting_7_name = fields.Char("Name",default="7 Days")
    # casting_28_visible = fields.Boolean("28 days Visible",compute="_compute_visible")

    casting_date_7days = fields.Date(string="Date of Casting")
    testing_date_7days = fields.Date(string="Date of Testing",compute="_compute_testing_date_7days")
    status_7days = fields.Boolean("Done",store=True)

    # show_7days = fields.Boolean(compute="_compute_visible_days")
    # show_14days = fields.Boolean(compute="_compute_visible_days")
    # show_28days = fields.Boolean(compute="_compute_visible_days")

    # @api.depends('days_casting')
    # def _compute_visible_days(self):
    #     for rec in self:
    #         days = int(rec.days_casting or 0)

    #         rec.show_7days = days >= 7
    #         rec.show_14days = days >= 14
    #         rec.show_28days = days >= 28



    selected_lab_cube1 = fields.Many2one(
        'cube.lab.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_cube_ids)]"
    )

    calc_mode = fields.Boolean(default=True)     
    submit_mode = fields.Boolean(default=False)



    is_lab_casting_7 = fields.Boolean(
        string="Lab Fine Selected",
        
    )

    @api.onchange('selected_lab_cube1')
    def _onchange_selected_lab_cube1(self):
        for rec in self:
            if rec.selected_lab_cube1:
                rec.is_lab_casting_7 = True
            else:
                rec.is_lab_casting_7 = False




    @api.depends('casting_date_7days')
    def _compute_testing_date_7days(self):
        for record in self:
            if record.casting_date_7days:
                cast_date = fields.Datetime.from_string(record.casting_date_7days)
                testing_date = cast_date + timedelta(days=7)
                record.testing_date_7days = fields.Datetime.to_string(testing_date)
            else:
                record.testing_date_7days = False


            

    child_lines14day = fields.One2many('mechanical.concrete.cube.line14','parent_id',string="Parameter")


    casting_14_name = fields.Char("Name",default="14 Days")
    # casting_28_visible = fields.Boolean("28 days Visible",compute="_compute_visible")

    casting_date_14days = fields.Date(string="Date of Casting")
    testing_date_14days = fields.Date(string="Date of Testing",compute="_compute_testing_date_14days")
    status_14days = fields.Boolean("Done",store=True)

    room_temperature14 = fields.Char(string="Room Temperature (°C)" ,required=True)
    relative_humidity14 = fields.Char(string="Relative Humidity (%)" ,required=True)


    # is_lab_casting_14 = fields.Boolean(
    #     string="Lab Fine Selected",
        
    # )

    # @api.onchange('selected_lab_cube1')
    # def _onchange_selected_lab_cube1(self):
    #     for rec in self:
    #         if rec.selected_lab_cube1:
    #             rec.is_lab_casting_14 = True
    #         else:
    #             rec.is_lab_casting_14 = False



    @api.depends('casting_date_14days')
    def _compute_testing_date_14days(self):
        for record in self:
            if record.casting_date_14days:
                cast_date = fields.Datetime.from_string(record.casting_date_14days)
                testing_date = cast_date + timedelta(days=14)
                record.testing_date_14days = fields.Datetime.to_string(testing_date)
            else:
                record.testing_date_14days = False

    def action_calculate_avg_strength14(self):
        for rec in self:


            rec.calc_mode = True
            rec.submit_mode = False

            lines = rec.child_lines14day.sorted(key=lambda l: l.sr_no)
            group_size = 3

            for i in range(0, len(lines), group_size):
                group = lines[i:i + group_size]
                strengths = [l.compressive_strength14 for l in group if l.compressive_strength14 > 0]
                avg = sum(strengths) / len(strengths) if strengths else 0.0

                # Set average for first line in each group
                # if group:
                #     group[0].average_strength14 = avg
                # Reset average for other lines in group
                # for j in range(1, len(group)):
                #     group[j].average_strength14 = 0.0

               


                # rec.submit_mode = True

    average_strength14 = fields.Float(string="Average Compressive Strength in N/mm2", compute="_compute_average_strength14", digits=(12,2))

    @api.depends('child_lines14day.compressive_strength14')
    def _compute_average_strength14(self):
        for rec in self:
            strengths = [line.compressive_strength14 for line in rec.child_lines14day if line.compressive_strength14]
            rec.average_strength14 = sum(strengths) / len(strengths) if strengths else 0.0

    average_strength14_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
        
    ], string='Conformity', compute="_compute_average_strength14_conformity")

    average_strength14_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_average_strength14_nabl")


    @api.depends('average_strength14','eln_ref','grade')
    def _compute_average_strength14_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_strength14_conformity = 'na'
                continue

            record.average_strength14_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6c89613-885c-4af1-bf19-f523bb56e0d9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6c89613-885c-4af1-bf19-f523bb56e0d9')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.average_strength14 - record.average_strength14*mu_value
                    upper = record.average_strength14 + record.average_strength14*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_strength14_conformity = 'pass'
                        break
                    else:
                        record.average_strength14_conformity = 'fail'

                    

    @api.depends('average_strength14','eln_ref','grade')
    def _compute_average_strength14_nabl(self):
        
        for record in self:
            record.average_strength14_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6c89613-885c-4af1-bf19-f523bb56e0d9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6c89613-885c-4af1-bf19-f523bb56e0d9')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_strength14 - record.average_strength14*mu_value
            upper = record.average_strength14 + record.average_strength14*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_strength14_nabl = 'pass'
                break
            else:
                record.average_strength14_nabl = 'fail'



    child_lines28day = fields.One2many('mechanical.concrete.cube.line28','parent_id',string="Parameter")


    casting_28_name = fields.Char("Name",default="28 Days")
    # casting_28_visible = fields.Boolean("28 days Visible",compute="_compute_visible")

    casting_date_28days = fields.Date(string="Date of Casting")
    testing_date_28days = fields.Date(string="Date of Testing",compute="_compute_testing_date_28days")
    status_28days = fields.Boolean("Done",store=True)

    room_temperature28 = fields.Char(string="Room Temperature (°C)" ,required=True)
    relative_humidity28 = fields.Char(string="Relative Humidity (%)" ,required=True)


    # is_lab_casting_28 = fields.Boolean(
    #     string="Lab Fine Selected",
        
    # )

    # @api.onchange('selected_lab_cube1')
    # def _onchange_selected_lab_cube1(self):
    #     for rec in self:
    #         if rec.selected_lab_cube1:
    #             rec.is_lab_casting_28 = True
    #         else:
    #             rec.is_lab_casting_28 = False


                

    @api.depends('casting_date_28days')
    def _compute_testing_date_28days(self):
        for record in self:
            if record.casting_date_28days:
                cast_date = fields.Datetime.from_string(record.casting_date_28days)
                testing_date = cast_date + timedelta(days=28)
                record.testing_date_28days = fields.Datetime.to_string(testing_date)
            else:
                record.testing_date_28days = False

    def action_calculate_avg_strength28(self):
        for rec in self:

            rec.calc_mode = True
            rec.submit_mode = False

            lines = rec.child_lines28day.sorted(key=lambda l: l.sr_no)
            group_size = 3

            for i in range(0, len(lines), group_size):
                group = lines[i:i + group_size]
                strengths = [l.compressive_strength28 for l in group if l.compressive_strength28 > 0]
                avg = sum(strengths) / len(strengths) if strengths else 0.0

                # Set average for first line in each group
                # if group:
                #     group[0].average_strength28 = avg
                # Reset average for other lines in group
                # for j in range(1, len(group)):
                #     group[j].average_strength28 = 0.0

                # rec.submit_mode = True

    average_strength28 = fields.Float(string="Average Compressive Strength in N/mm2", compute="_compute_average_strength28", digits=(12,2))

    @api.depends('child_lines28day.compressive_strength28')
    def _compute_average_strength28(self):
        for rec in self:
            strengths = [line.compressive_strength28 for line in rec.child_lines28day if line.compressive_strength28]
            rec.average_strength28 = sum(strengths) / len(strengths) if strengths else 0.0

   
    average_strength28_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
        
    ], string='Conformity', compute="_compute_average_strength28_conformity")

    average_strength28_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_average_strength28_nabl")


    @api.depends('average_strength28','eln_ref','grade')
    def _compute_average_strength28_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_strength28_conformity = 'na'
                continue

            record.average_strength28_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6c89613-885c-4af1-bf19-f523bb56e0d9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6c89613-885c-4af1-bf19-f523bb56e0d9')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.average_strength28 - record.average_strength28*mu_value
                    upper = record.average_strength28 + record.average_strength28*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_strength28_conformity = 'pass'
                        break
                    else:
                        record.average_strength28_conformity = 'fail'

    @api.depends('average_strength28','eln_ref','grade')
    def _compute_average_strength28_nabl(self):
        
        for record in self:
            record.average_strength28_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6c89613-885c-4af1-bf19-f523bb56e0d9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d6c89613-885c-4af1-bf19-f523bb56e0d9')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_strength28 - record.average_strength28*mu_value
            upper = record.average_strength28 + record.average_strength28*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_strength28_nabl = 'pass'
                break
            else:
                record.average_strength28_nabl = 'fail'

    
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    eln_ref = fields.Many2one('lerm.eln',string="ELN")

    notes_id = fields.One2many('cube.notes','parent_id',string="Notes")

    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")

    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:

                record.date_of_casting = None






    @api.model
    def default_get(self, fields):
        res = super(MechanicalConcreteCube, self).default_get(fields)

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
                'notes': 'This document shall not be reproduced in part or full without the approval of Genstru.',
            }),
        ]

        res['notes_id'] = default_notes
        return res




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
    room_temperature = fields.Char(string="Room Temperature (°C)")
    relative_humidity = fields.Char(string="Relative Humidity (%)")

    
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
                # if group:
                #     group[0].avg_compressive_strength = avg
                # Reset average for other lines in group
                # for j in range(1, len(group)):
                #     group[j].avg_compressive_strength = 0.0


                   # Jar Button Visible ahe (True), tar Submit Mode 'False' ch theva.
                # if rec. cube_visible_14:
                #  rec.submit_mode = False


                # elif rec. cube_visible_28:
                #  rec.submit_mode = False
            
            
            # Jar Button Invisible ahe (False), tar automatic 'True' kara.
                # else:
              
                

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
    
    # age_of_test = fields.Integer("Age of Test, days", compute="_compute_age_of_test")
    # difference = fields.Integer("Difference", compute="_compute_difference")

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

    @api.depends('average_strength', 'eln_ref', 'grade', )
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
                        # if record.age_of_days == "3days":
                        #     req_min = req_min * 0.5
                        #     req_max = req_max * 0.5
                        # elif record.age_of_days == "7days":
                        #     req_min = req_min * 0.7
                        #     req_max = req_max * 0.7
                        # elif record.age_of_days == "14days":
                        #     req_min = req_min * 0.9
                        #     req_max = req_max * 0.9
                        # 28 days uses full values
                        
                        lower = record.average_strength - record.average_strength * mu_value
                        upper = record.average_strength + record.average_strength * mu_value
                        
                        # if record.difference == 0:
                        if lower >= req_min and upper <= req_max:
                                record.confirmity = 'pass'
                                break
                        else:
                                record.confirmity = 'fail'
                        # else:
                        #     record.confirmity = 'not_applicable'

     ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        

        for record in self:
            record.cube_visible = False
            record.cube_visible_14 = False
            record.cube_visible_28 = False
         

            
            
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                
                if sample.internal_id == 'd6c89613-885c-4af1-bf19-f523bb56e0d9':
                    record.cube_visible = True
              
               


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
                   
            if result.parameter.internal_id == 'd6c89613-885c-4af1-bf19-f523bb56e0d9':
                result.result_char = round(self.average_strength,2)
                result.calculated = True
                if self.average_strength_nabl == 'pass':
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


    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    def _compute_sample_parameters(self):
        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            current_user = self.env.user

            # ✅ Discipline group can see all parameters
            if current_user.has_group('lerm_civil.lerm_discipline_group'):
                parameter_ids = record.eln_ref.parameters_result.mapped('parameter').ids
            else:
                # 🔒 Only parameters assigned to current technician
                user_param_results = record.eln_ref.parameters_result.filtered(
                    lambda r: r.technician and r.technician.id == current_user.id
                )
                parameter_ids = user_param_results.mapped('parameter').ids

            record.sample_parameters = [(6, 0, parameter_ids)]

        
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
    width = fields.Float(string="width (mm)")
    



    dt_of_casting = fields.Date(string="Date of casting", compute="_compute_dt_of_casting", store=True)
    dt_of_casting_formatted = fields.Char(string="Casting Date (DD-MM-YYYY)", compute="_compute_dt_of_casting_formatted")

    @api.depends('dt_of_casting')
    def _compute_dt_of_casting_formatted(self):
        for rec in self:
            if rec.dt_of_casting:
                rec.dt_of_casting_formatted = rec.dt_of_casting.strftime('%d-%m-%Y')
            else:
                rec.dt_of_casting_formatted = ''
    days = fields.Integer(string="No.of Days",compute="_compute_days_difference", store=True)
    dt_of_testing1 = fields.Date(string="Date of Testing", compute="_compute_dt_of_testing", store=True)
    dt_of_testing1_formatted = fields.Char(string="Date (DD-MM-YYYY)", compute="_compute_dt_of_testing1_formatted")

    @api.depends('dt_of_testing1')
    def _compute_dt_of_testing1_formatted(self):
        for rec in self:
            if rec.dt_of_testing1:
                rec.dt_of_testing1_formatted = rec.dt_of_testing1.strftime('%d-%m-%Y')
            else:
                rec.dt_of_testing1_formatted = ''


    @api.depends('dt_of_casting', 'parent_id')
    def _compute_dt_of_testing(self):
        for rec in self:
            if rec.dt_of_casting and rec.parent_id:
                # Find all lines of this parent ordered by ID (creation order)
                all_lines = self.search(
                    [('parent_id', '=', rec.parent_id.id)],
                    order='id asc'
                )
                # Get position (1-based index)
                position = all_lines.ids.index(rec.id) + 1 if rec.id in all_lines.ids else len(all_lines) + 1

                # Apply day rule
                if position <= 3:
                    rec.dt_of_testing1 = rec.dt_of_casting + timedelta(days=7)
                else:
                    rec.dt_of_testing1 = rec.dt_of_casting + timedelta(days=28)
            else:
                rec.dt_of_testing1 = False

    @api.depends('parent_id.casting_date_7days')
    def _compute_dt_of_casting(self):
        for record in self:
            record.dt_of_casting = record.parent_id.casting_date_7days

    @api.depends('parent_id.testing_date_7days')
    def _compute_dt_of_testing(self):
        for record in self:
            record.dt_of_testing1 = record.parent_id.testing_date_7days

    @api.depends('dt_of_casting', 'dt_of_testing1')
    def _compute_days_difference(self):
        for record in self:
            if record.dt_of_casting and record.dt_of_testing1:
                record.days = (record.dt_of_testing1 - record.dt_of_casting).days
            else:
                record.days = 0

    # @api.depends('dt_of_casting', 'days')
    # def _compute_dt_of_testing(self):
    #     for record in self:
    #         if record.dt_of_casting and record.days:
    #             record.dt_of_testing1 = record.dt_of_casting + timedelta(days=record.days)
    #         else:
    #             record.dt_of_testing1 = False
    
    # Environmental conditions per sample
    room_temp = fields.Char(string="Room Temperature (°C)",compute = "_compute_room_temp")
    relative_humidity = fields.Char(string="Relative Humidity (%)" ,compute = "_compute_relative_humidity")
    
    load = fields.Float(string="Load (kN)")
    cross_sectional_area = fields.Float(string="Cross Sectional Area (mm²)", compute="_compute_cross_sectional_area")
    compressive_strength = fields.Float(string="Compressive Strength (N/mm²)", compute="_compute_strength", store=True)
    avg_compressive_strength = fields.Float(string="Avg. Compressive Strength (N/mm²)")
    
    # Type of Failure
    type_of_failure = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('unsatisfactory', 'Unsatisfactory'),
    ], string="Type of Failure", default='satisfactory')

    @api.depends('parent_id.room_temperature')
    def _compute_room_temp(self):
        for rec in self:
           rec.room_temp = rec.parent_id.room_temperature

    @api.depends('parent_id.relative_humidity')
    def _compute_relative_humidity(self):
        for rec in self:
           rec.relative_humidity = rec.parent_id.relative_humidity



           
    @api.depends('length', 'width', 'diameter', 'parent_id.type_of_sample')
    def _compute_cross_sectional_area(self):
     for record in self:

        # Identify sample type safely
        sample_type = record.parent_id.type_of_sample if record.parent_id else False

        # CASE 1: CUBE → Area = Length × Width
        if sample_type == 'cube':
            record.cross_sectional_area = (record.length or 0.0) * (record.width or 0.0)

        # CASE 2: CYLINDER → Area = π × (Diameter/2)^2
        elif sample_type == 'cylinder':
            if record.diameter and record.diameter > 0:
                record.cross_sectional_area = math.pi * ((record.diameter / 2) ** 2)
            else:
                record.cross_sectional_area = 0.0

        # If type not selected or unknown
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

class MechanicalConcreteCubeLine14(models.Model):
    _name = "mechanical.concrete.cube.line14"
    parent_id = fields.Many2one('mechanical.concrete.cube', string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    id_mark = fields.Char(string="Sample Identification", compute="_compute_id_mark",inverse="_inverse_id_mark", store=True)
    wt_sample = fields.Float(string="Weight of Cube (gms)", digits=(16, 3))
    
    # Dimensions
    length = fields.Float(string="Length (mm)")
    diameter = fields.Float(string="Diameter (mm)")
    width = fields.Float(string="width (mm)")
    



    dt_of_casting = fields.Date(string="Date of casting", compute="_compute_dt_of_casting", store=True)
    dt_of_casting_formatted = fields.Char(string="Casting Date (DD-MM-YYYY)", compute="_compute_dt_of_casting_formatted")

    @api.depends('dt_of_casting')
    def _compute_dt_of_casting_formatted(self):
        for rec in self:
            if rec.dt_of_casting:
                rec.dt_of_casting_formatted = rec.dt_of_casting.strftime('%d-%m-%Y')
            else:
                rec.dt_of_casting_formatted = ''
    days = fields.Integer(string="No.of Days",compute="_compute_days_difference", store=True)
    dt_of_testing1 = fields.Date(string="Date of Testing", compute="_compute_dt_of_testing", store=True)
    dt_of_testing1_formatted = fields.Char(string="Date (DD-MM-YYYY)", compute="_compute_dt_of_testing1_formatted")

    @api.depends('dt_of_testing1')
    def _compute_dt_of_testing1_formatted(self):
        for rec in self:
            if rec.dt_of_testing1:
                rec.dt_of_testing1_formatted = rec.dt_of_testing1.strftime('%d-%m-%Y')
            else:
                rec.dt_of_testing1_formatted = ''


    @api.depends('dt_of_casting', 'parent_id')
    def _compute_dt_of_testing(self):
        for rec in self:
            if rec.dt_of_casting and rec.parent_id:
                # Find all lines of this parent ordered by ID (creation order)
                all_lines = self.search(
                    [('parent_id', '=', rec.parent_id.id)],
                    order='id asc'
                )
                # Get position (1-based index)
                position = all_lines.ids.index(rec.id) + 1 if rec.id in all_lines.ids else len(all_lines) + 1

                # Apply day rule
                if position <= 3:
                    rec.dt_of_testing1 = rec.dt_of_casting + timedelta(days=7)
                else:
                    rec.dt_of_testing1 = rec.dt_of_casting + timedelta(days=28)
            else:
                rec.dt_of_testing1 = False

    @api.depends('parent_id.casting_date_14days')
    def _compute_dt_of_casting(self):
        for record in self:
            record.dt_of_casting = record.parent_id.casting_date_14days

    @api.depends('parent_id.testing_date_14days')
    def _compute_dt_of_testing(self):
        for record in self:
            record.dt_of_testing1 = record.parent_id.testing_date_14days

    @api.depends('dt_of_casting', 'dt_of_testing1')
    def _compute_days_difference(self):
        for record in self:
            if record.dt_of_casting and record.dt_of_testing1:
                record.days = (record.dt_of_testing1 - record.dt_of_casting).days
            else:
                record.days = 0

    
    
    # Environmental conditions per sample
    room_temp = fields.Char(string="Room Temperature (°C)",compute = "_compute_room_temp")
    relative_humidity = fields.Char(string="Relative Humidity (%)" ,compute = "_compute_relative_humidity")
    
    load = fields.Float(string="Load (kN)")
    cross_sectional_area = fields.Float(string="Cross Sectional Area (mm²)", compute="_compute_cross_sectional_area")
    compressive_strength14 = fields.Float(string="Compressive Strength (N/mm²)", compute="_compute_strength", store=True)
    average_strength14 = fields.Float(string="Avg. Compressive Strength (N/mm²)")
    
    # Type of Failure
    type_of_failure = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('unsatisfactory', 'Unsatisfactory'),
    ], string="Type of Failure", default='satisfactory')

    @api.depends('parent_id.room_temperature14')
    def _compute_room_temp(self):
        for rec in self:
           rec.room_temp = rec.parent_id.room_temperature14

    @api.depends('parent_id.relative_humidity14')
    def _compute_relative_humidity(self):
        for rec in self:
           rec.relative_humidity = rec.parent_id.relative_humidity14



           
    @api.depends('length', 'width', 'diameter', 'parent_id.type_of_sample')
    def _compute_cross_sectional_area(self):
     for record in self:

        # Identify sample type safely
        sample_type = record.parent_id.type_of_sample if record.parent_id else False

        # CASE 1: CUBE → Area = Length × Width
        if sample_type == 'cube':
            record.cross_sectional_area = (record.length or 0.0) * (record.width or 0.0)

        # CASE 2: CYLINDER → Area = π × (Diameter/2)^2
        elif sample_type == 'cylinder':
            if record.diameter and record.diameter > 0:
                record.cross_sectional_area = math.pi * ((record.diameter / 2) ** 2)
            else:
                record.cross_sectional_area = 0.0

        # If type not selected or unknown
        else:
            record.cross_sectional_area = 0.0


   

    @api.depends('load', 'cross_sectional_area')
    def _compute_strength(self):
        for record in self:
            if record.cross_sectional_area and record.load:
                # Compressive strength = (Load in kN * 1000) / Area in mm² = N/mm²
                record.compressive_strength14 = (record.load * 1000) / record.cross_sectional_area
            else:
                record.compressive_strength14 = 0.0

    

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
        return super(MechanicalConcreteCubeLine14, self).create(vals)

    def _reorder_serial_numbers(self):
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class MechanicalConcreteCubeLine28(models.Model):
    _name = "mechanical.concrete.cube.line28"
    parent_id = fields.Many2one('mechanical.concrete.cube', string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.", readonly=True, copy=False, default=1)
    id_mark = fields.Char(string="Sample Identification", compute="_compute_id_mark",inverse="_inverse_id_mark", store=True)
    wt_sample = fields.Float(string="Weight of Cube (gms)", digits=(16, 3))
    
    # Dimensions
    length = fields.Float(string="Length (mm)")
    diameter = fields.Float(string="Diameter (mm)")
    width = fields.Float(string="width (mm)")
    



    dt_of_casting = fields.Date(string="Date of casting", compute="_compute_dt_of_casting", store=True)
    dt_of_casting_formatted = fields.Char(string="Casting Date (DD-MM-YYYY)", compute="_compute_dt_of_casting_formatted")

    @api.depends('dt_of_casting')
    def _compute_dt_of_casting_formatted(self):
        for rec in self:
            if rec.dt_of_casting:
                rec.dt_of_casting_formatted = rec.dt_of_casting.strftime('%d-%m-%Y')
            else:
                rec.dt_of_casting_formatted = ''
    days = fields.Integer(string="No.of Days",compute="_compute_days_difference", store=True)
    dt_of_testing1 = fields.Date(string="Date of Testing", compute="_compute_dt_of_testing", store=True)
    dt_of_testing1_formatted = fields.Char(string="Date (DD-MM-YYYY)", compute="_compute_dt_of_testing1_formatted")

    @api.depends('dt_of_testing1')
    def _compute_dt_of_testing1_formatted(self):
        for rec in self:
            if rec.dt_of_testing1:
                rec.dt_of_testing1_formatted = rec.dt_of_testing1.strftime('%d-%m-%Y')
            else:
                rec.dt_of_testing1_formatted = ''


    @api.depends('dt_of_casting', 'parent_id')
    def _compute_dt_of_testing(self):
        for rec in self:
            if rec.dt_of_casting and rec.parent_id:
                # Find all lines of this parent ordered by ID (creation order)
                all_lines = self.search(
                    [('parent_id', '=', rec.parent_id.id)],
                    order='id asc'
                )
                # Get position (1-based index)
                position = all_lines.ids.index(rec.id) + 1 if rec.id in all_lines.ids else len(all_lines) + 1

                # Apply day rule
                if position <= 3:
                    rec.dt_of_testing1 = rec.dt_of_casting + timedelta(days=7)
                else:
                    rec.dt_of_testing1 = rec.dt_of_casting + timedelta(days=28)
            else:
                rec.dt_of_testing1 = False

    @api.depends('parent_id.casting_date_28days')
    def _compute_dt_of_casting(self):
        for record in self:
            record.dt_of_casting = record.parent_id.casting_date_28days

    @api.depends('parent_id.testing_date_28days')
    def _compute_dt_of_testing(self):
        for record in self:
            record.dt_of_testing1 = record.parent_id.testing_date_28days

    @api.depends('dt_of_casting', 'dt_of_testing1')
    def _compute_days_difference(self):
        for record in self:
            if record.dt_of_casting and record.dt_of_testing1:
                record.days = (record.dt_of_testing1 - record.dt_of_casting).days
            else:
                record.days = 0

    
    
    # Environmental conditions per sample
    room_temp = fields.Float(string="Room Temperature (°C)",compute = "_compute_room_temp")
    relative_humidity = fields.Float(string="Relative Humidity (%)" ,compute = "_compute_relative_humidity")
    
    load = fields.Float(string="Load (kN)")
    cross_sectional_area = fields.Float(string="Cross Sectional Area (mm²)", compute="_compute_cross_sectional_area")
    compressive_strength28 = fields.Float(string="Compressive Strength (N/mm²)", compute="_compute_strength", store=True)
    average_strength28 = fields.Float(string="Avg. Compressive Strength (N/mm²)")
    
    # Type of Failure
    type_of_failure = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('unsatisfactory', 'Unsatisfactory'),
    ], string="Type of Failure", default='satisfactory')

    @api.depends('parent_id.room_temperature28')
    def _compute_room_temp(self):
        for rec in self:
           rec.room_temp = rec.parent_id.room_temperature28

    @api.depends('parent_id.relative_humidity28')
    def _compute_relative_humidity(self):
        for rec in self:
           rec.relative_humidity = rec.parent_id.relative_humidity28



           
    @api.depends('length', 'width', 'diameter', 'parent_id.type_of_sample')
    def _compute_cross_sectional_area(self):
     for record in self:

        # Identify sample type safely
        sample_type = record.parent_id.type_of_sample if record.parent_id else False

        # CASE 1: CUBE → Area = Length × Width
        if sample_type == 'cube':
            record.cross_sectional_area = (record.length or 0.0) * (record.width or 0.0)

        # CASE 2: CYLINDER → Area = π × (Diameter/2)^2
        elif sample_type == 'cylinder':
            if record.diameter and record.diameter > 0:
                record.cross_sectional_area = math.pi * ((record.diameter / 2) ** 2)
            else:
                record.cross_sectional_area = 0.0

        # If type not selected or unknown
        else:
            record.cross_sectional_area = 0.0


   

    @api.depends('load', 'cross_sectional_area')
    def _compute_strength(self):
        for record in self:
            if record.cross_sectional_area and record.load:
                # Compressive strength = (Load in kN * 1000) / Area in mm² = N/mm²
                record.compressive_strength28 = (record.load * 1000) / record.cross_sectional_area
            else:
                record.compressive_strength28 = 0.0

    

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
        return super(MechanicalConcreteCubeLine28, self).create(vals)

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


class CubeNotes(models.Model):
    _name = "cube.notes"

    parent_id = fields.Many2one('mechanical.concrete.cube',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")


class LabOptionLine(models.Model):
    _name = 'cube.lab.line'
    _description = 'Lab Options'
    _rec_name = 'lab'  # Dropdown मध्ये हे नाव दिसेल

    lab = fields.Char(string="Lab ID")
    parent_id = fields.Many2one('mechanical.concrete.cube', string="Parent")