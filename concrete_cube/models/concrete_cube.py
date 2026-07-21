from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
from datetime import datetime , timedelta
import re
import logging
_logger = logging.getLogger(__name__)


class MechanicalConcreteCube(models.Model):
    _name = "mechanical.concrete.cube"
    _inherit = "lerm.eln"
    _description = 'mechanical.concrete.cube'
    _rec_name = "name"

    name = fields.Char("Name",default="Compressive Strength of Concrete Cube")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    child_lines = fields.One2many('mechanical.concrete.cube.line','parent_id',string="Parameter")
    
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="ELN")

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    

    sample_id = fields.Many2one('lerm.srf.sample',string='Sample')

    nature_work = fields.Char(string="Nature of Work")
    curing_condition = fields.Char(string="Curing Conditions")
    machine_testing = fields.Char(string="Machine used for testing / Loading range")


    cube_name = fields.Char("Name",default=" Cube")
    cube_visible = fields.Boolean("Chequered Visible",compute="_compute_visible")   
    type_of_failure = fields.Selection(
        [('satisfactory','Satisfactory'),
        ('non_satisfactory','Non Satisfactory')],
        string="Type of Failure")    
    temp = fields.Float(string="Temperature")
    humidity = fields.Float(string="Humidity")
    date_of_calibration = fields.Date(string="Date of Calibration",compute="_compute_date_of_calibration",store=True)
    condition_of_sample = fields.Char(string="Condition of Sample")
    notes_id = fields.One2many('concrete.cube.notes', 'parent_id', string="Notes")


    @api.depends('eln_ref.instrument')
    def _compute_date_of_calibration(self):
        for rec in self:
            if rec.eln_ref.instrument and rec.eln_ref.instrument.calibration_lines:
                lines = rec.eln_ref.instrument.calibration_lines.filtered(lambda l: l.last_calibration_date)
                if lines:
                    latest_line = lines.sorted(key=lambda l: l.last_calibration_date, reverse=True)[0]
                    rec.date_of_calibration = latest_line.last_calibration_date
                else:
                    rec.date_of_calibration = False
            else:
                rec.date_of_calibration = False

    @api.model
    def default_get(self, fields):
        res = super(MechanicalConcreteCube, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'i',
                'notes': 'The results stated in this report apply only to the tested sample(s) and are based on the conditions and parameters at the time of testing.',
            }),
            (0, 0, {
                'sr_no': 'ii',
                'notes': 'This report is invalid without the official paper seal of Make Infracon.',
            }),
            (0, 0, {
                'sr_no': 'iii',
                'notes': 'All test results are confidential and will not be disclosed to any third party without written consent of the client, except where required by law.',
            }),
            (0, 0, {
                'sr_no': 'iv',
                'notes': 'The # points mentioned in the report which information is given by Client/Customer.',
            }),

            (0, 0, {
                'sr_no': 'v',
                'notes': 'Any disputes shall be subject to jurisdiction of Nashik courts only.',
            }),
        ]

        res['notes_id'] = default_notes
        return res

    def action_calculate_avg_strength(self):
        for rec in self:
            lines = rec.child_lines.sorted(key=lambda l: l.sr_no)  # sr_no ने sort करायचं
            group_size = 3

            for i in range(0, len(lines), group_size):
                group = lines[i:i + group_size]
                strengths = [l.compressive_strength for l in group if l.compressive_strength > 0]
                avg = sum(strengths) / len(strengths) if strengths else 0.0

                if group:
                    group[0].avg_compressive_strength = avg

            for line in lines:
                if line not in [lines[i] for i in range(0, len(lines), group_size)]:
                    line.avg_compressive_strength = 0.0


    average_strength = fields.Float(string="Average Compressive Strength in N/mm2",compute="_compute_average_strength",digits=(12,2))

    def prefill_data(self):
        wizard_action = self.env.ref('concrete_cube.action_cube_prefill_data_wizard')
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'concrete.cube.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }
    
    @api.depends('child_lines.compressive_strength')
    def _compute_average_strength(self):
        for rec in self:
            strengths = [line.compressive_strength for line in rec.child_lines if line.compressive_strength]
            rec.average_strength = sum(strengths) / len(strengths) if strengths else 0.0

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    area_of_cube = fields.Float(string="Area of Cube",compute="_compute_area_cube",store=True)

    @api.depends('size_id.size')
    def _compute_area_cube(self):
        import re
        for record in self:
            size_str = record.size_id.size
            if size_str:
                match = re.search(r'\d+', str(size_str))
                if match:
                    side = int(match.group())
                    record.area_of_cube = side * side  # or whatever formula
                else:
                    record.area_of_cube = 0
            else:
                record.area_of_cube = 0



    days_7_kmm = fields.Float(string="7 Days",compute="_compute_days_7_kmm")
    days_7_n = fields.Float(string="7 Days",compute="_compute_days_7_n")

    @api.depends('days_28_kmm')
    def _compute_days_7_kmm(self):
        for rec in self:
            rec.days_7_kmm = rec.days_28_kmm * 0.67 if rec.days_28_kmm else 0.0

    @api.depends('days_7_kmm')
    def _compute_days_7_n(self):
        for rec in self:
            rec.days_7_n = rec.days_7_kmm * 22.5 if rec.days_7_kmm else 0.0

    days_28_kmm = fields.Float(string="28 Days",compute="_compute_days_28_kmm",store=True)
    days_28_n = fields.Float(string="28 Days",compute="_compute_days_28_n")

    @api.depends('days_28_kmm')
    def _compute_days_28_n(self):
        for rec in self:
            rec.days_28_n = rec.days_28_kmm * 22.5 if rec.days_28_kmm else 0.0


  
    @api.depends('grade.grade', 'grade_child_lines.grade1', 'grade_child_lines.sd')
    def _compute_days_28_kmm(self):
        for rec in self:
            rec.days_28_kmm = 0.0

            if not rec.grade2:
                continue

            grade2_str = rec.grade2.strip().lower()

            # Match grade2 with grade1 in lines
            matching_line = rec.grade_child_lines.filtered(
                lambda l: l.grade1 and l.grade1.strip().lower() == grade2_str
            )

            if matching_line:
                line = matching_line[0]
                # Extract number from grade2 (e.g., from "M25" → 25)
                number_part = ''.join(filter(str.isdigit, rec.grade2))
                try:
                    grade_val = float(number_part)
                    rec.days_28_kmm = grade_val + (1.65 * line.sd)
                except (ValueError, TypeError):
                    rec.days_28_kmm = 0.0






    grade2 = fields.Char(string="Grade",compute="_compute_grade2",store=True)

    @api.depends('grade')
    def _compute_grade2(self):
        for rec in self:
            rec.grade2 = rec.grade.grade if rec.grade and rec.grade.grade else ''


    grade_child_lines = fields.One2many('mechanical.concrete.cube.grade.line','parent_id',string="Parameter",default=lambda self: self._default_grade_child_lines())

    # @api.model
    # def _default_grade_child_lines(self):
    #     default_lines = [
    #         (0, 0, {'grade1': M10, 'sd': 3.5}),
    #         (0, 0, {'grade1': M15, 'sd': 3.5}),
    #         (0, 0, {'grade1': M20, 'sd': 4}),
    #         (0, 0, {'grade1': M25, 'sd': 4}),
    #         (0, 0, {'grade1': M30, 'sd': 5}),
    #         (0, 0, {'grade1': M35, 'sd': 5}),
    #         (0, 0, {'grade1': M40, 'sd': 5}),
    #         (0, 0, {'grade1': M45, 'sd': 5})
    #     ]
    #     return default_lines

    @api.model
    def _default_grade_child_lines(self):

        default_lines = [
            (0, 0, {'grade1': 'M10', 'sd': 3.5}),
            (0, 0, {'grade1': 'M15', 'sd': 3.5}),
            (0, 0, {'grade1': 'M20', 'sd': 4}),
            (0, 0, {'grade1': 'M25', 'sd': 4}),
            (0, 0, {'grade1': 'M30', 'sd': 5}),
            (0, 0, {'grade1': 'M35', 'sd': 5}),
            (0, 0, {'grade1': 'M40', 'sd': 5}),
            (0, 0, {'grade1': 'M45', 'sd': 5}),
        ]
        return default_lines


    
    
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
        else:
            self.date_of_testing = ''
            

    # confirmity = fields.Selection([
    #     ('pass', 'Pass'),
    #     ('fail', 'Fail'),
    #     ('not_applicable', 'Not Applicable'),

    # ], string='Confirmity', default='fail',compute="_compute_confirmity")
    age_of_test = fields.Integer("Age of Test, days",compute="compute_age_of_test")
    difference = fields.Integer("Difference",compute="compute_difference")

    # grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    # nabl = fields.Selection([
    #     ('pass', 'Pass'),
    #     ('fail', 'Fail'),

    # ], string='NABL', default='fail',compute="_compute_nabl")


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


    avg_compressive_strength = fields.Float(string="Avg. Compressive Strength (N/mm2)",compute="_compute_avg_compressive_strength",store=True)

    @api.depends('child_lines.avg_compressive_strength')
    def _compute_avg_compressive_strength(self):
     for record in self:
        selected_lines = record.child_lines[::3]
        values = selected_lines.mapped('avg_compressive_strength')
        record.avg_compressive_strength = (
            sum(values) / len(values) if values else 0.0
        )





    avg_compressive_strength_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_compressive_strength_conformity", store=True)

    @api.depends('avg_compressive_strength','eln_ref','grade')
    def _compute_avg_compressive_strength_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_compressive_strength_conformity = 'na'
                continue
            record.avg_compressive_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23545tur-17c1-48ac-8462-9671e4d3d09f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23545tur-17c1-48ac-8462-9671e4d3d09f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_compressive_strength - record.avg_compressive_strength*mu_value
                    upper = record.avg_compressive_strength + record.avg_compressive_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_compressive_strength_conformity = 'pass'
                        break
                    else:
                        record.avg_compressive_strength_conformity = 'fail'

    avg_compressive_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_compressive_strength_nabl", store=True)

    @api.depends('avg_compressive_strength','eln_ref','grade')
    def _compute_avg_compressive_strength_nabl(self):
        
        for record in self:
            record.avg_compressive_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23545tur-17c1-48ac-8462-9671e4d3d09f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23545tur-17c1-48ac-8462-9671e4d3d09f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_compressive_strength - record.avg_compressive_strength*mu_value
                    upper = record.avg_compressive_strength + record.avg_compressive_strength*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_compressive_strength_nabl = 'pass'
                        break
                    else:
                        record.avg_compressive_strength_nabl = 'fail'


    compressive_strength_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    compressive_strength_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_compressive_strength_final_report", store=True)

    @api.depends('avg_compressive_strength_nabl', 'compressive_strength_report_type')
    def _compute_compressive_strength_final_report(self):
     for rec in self:

        # Manual override
        if rec.compressive_strength_report_type == 'nabl':
            rec.compressive_strength_final_report = 'nabl'

        elif rec.compressive_strength_report_type == 'non_nabl':
            rec.compressive_strength_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_compressive_strength_nabl == 'pass':
                rec.compressive_strength_final_report = 'nabl'
            else:
                rec.compressive_strength_final_report = 'non_nabl'


    
    # Water Permeability 					

    water_permeability_name = fields.Char(default="Water Permeability")
    water_permeability_visible = fields.Boolean(compute="_compute_visible")

    water_permeability_table = fields.One2many('mechanical.cube.wpt.line','parent_id',string="Water Permeability")


    average_depth = fields.Float(
        string="Average Depth of Penetration (mm)",
        compute="_compute_average",
        store=True,
    )

    @api.depends("water_permeability_table.average_depth")
    def _compute_average(self):
        for rec in self:
            if rec.water_permeability_table:
                rec.average_depth = sum(
                    rec.water_permeability_table.mapped("average_depth")
                ) / len(rec.water_permeability_table)
            else:
                rec.average_depth = 0.0


    average_depth_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_average_depth_confirmity")

    average_depth_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_average_depth_nabl",store=True)


    @api.depends('average_depth','eln_ref')
    def _compute_average_depth_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_depth_confirmity = 'na'
                continue
            record.average_depth_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1023457-0268-46ef-ba88-9c0453210lkit1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1023457-0268-46ef-ba88-9c0453210lkit1')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_depth - record.average_depth*mu_value
                    upper = record.average_depth + record.average_depth*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_depth_confirmity = 'pass'
                        break
                    else:
                        record.average_depth_confirmity = 'fail'

    @api.depends('average_depth','eln_ref')
    def _compute_average_depth_nabl(self):
        
        for record in self:
            record.average_depth_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1023457-0268-46ef-ba88-9c0453210lkit1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1023457-0268-46ef-ba88-9c0453210lkit1')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.average_depth - record.average_depth*mu_value
                  upper = record.average_depth + record.average_depth*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.average_depth_nabl = 'pass'
                      break
                  else:
                      record.average_depth_nabl = 'fail'

    
    water_permeability_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    water_permeability_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_water_permeability_final_report", store=True)

    @api.depends('average_depth_nabl', 'water_permeability_report_type')
    def _compute_water_permeability_final_report(self):
     for rec in self:

        # Manual override
        if rec.water_permeability_report_type == 'nabl':
            rec.water_permeability_final_report = 'nabl'

        elif rec.water_permeability_report_type == 'non_nabl':
            rec.water_permeability_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.average_depth_nabl == 'pass':
                rec.water_permeability_final_report = 'nabl'
            else:
                rec.water_permeability_final_report = 'non_nabl'


    # Compressive Strength By ACT									
					

    act_compressive_name = fields.Char(default="Compressive Strength By ACT")
    act_compressive_visible = fields.Boolean(compute="_compute_visible")

    act_compressive_line_ids = fields.One2many('compressive.by.act.line','parent_id',string="Compressive Strength By ACT")


    average_act_compressive = fields.Float(
        string="Average 28-Day Strength (N/mm²)",
        compute="_compute_average_act_compressive",
        store=True
    )

    @api.depends('act_compressive_line_ids.strength_28')
    def _compute_average_act_compressive(self):
        for rec in self:
            strengths = rec.act_compressive_line_ids.mapped('strength_28')
            rec.average_act_compressive = sum(strengths) / len(strengths) if strengths else 0.0


    average_act_compressive_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_average_act_compressive_confirmity")

    average_act_compressive_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_average_act_compressive_nabl",store=True)


    @api.depends('average_act_compressive','eln_ref')
    def _compute_average_act_compressive_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_act_compressive_confirmity = 'na'
                continue
            record.average_act_compressive_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24b7a3b3-55c6-4b1b-84a6-d6cc986a7715')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24b7a3b3-55c6-4b1b-84a6-d6cc986a7715')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_act_compressive - record.average_act_compressive*mu_value
                    upper = record.average_act_compressive + record.average_act_compressive*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_act_compressive_confirmity = 'pass'
                        break
                    else:
                        record.average_act_compressive_confirmity = 'fail'

    @api.depends('average_act_compressive','eln_ref')
    def _compute_average_act_compressive_nabl(self):
        
        for record in self:
            record.average_act_compressive_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24b7a3b3-55c6-4b1b-84a6-d6cc986a7715')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24b7a3b3-55c6-4b1b-84a6-d6cc986a7715')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.average_act_compressive - record.average_act_compressive*mu_value
                  upper = record.average_act_compressive + record.average_act_compressive*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.average_act_compressive_nabl = 'pass'
                      break
                  else:
                      record.average_act_compressive_nabl = 'fail'


    act_compressive_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    act_compressive_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_act_compressive_final_report", store=True)

    @api.depends('average_act_compressive_nabl', 'act_compressive_report_type')
    def _compute_act_compressive_final_report(self):
     for rec in self:

        # Manual override
        if rec.act_compressive_report_type == 'nabl':
            rec.act_compressive_final_report = 'nabl'

        elif rec.act_compressive_report_type == 'non_nabl':
            rec.act_compressive_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.average_act_compressive_nabl == 'pass':
                rec.act_compressive_final_report = 'nabl'
            else:
                rec.act_compressive_final_report = 'non_nabl'


    # Density								
    density_name = fields.Char(default="Density Of Concrete Cube")
    density_visible = fields.Boolean(compute="_compute_visible")

    density_line_ids = fields.One2many('cube.density.line','parent_id',string="Density Of Concrete Cube",default=lambda self: self.density_line_ids_sizes()
    )

    @api.model
    def density_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'age_of_cube': '3 Days','cube_identification': 'Cube-1'}),
            (0, 0, {'age_of_cube': '3 Days','cube_identification': 'Cube-2'}),
            (0, 0, {'age_of_cube': '3 Days','cube_identification': 'Cube-3'}),
            (0, 0, {'age_of_cube': '7 Days','cube_identification': 'Cube-1'}),
            (0, 0, {'age_of_cube': '7 Days','cube_identification': 'Cube-2'}),
            (0, 0, {'age_of_cube': '7 Days','cube_identification': 'Cube-3'}),
            (0, 0, {'age_of_cube': '14 Days','cube_identification': 'Cube-1'}),
            (0, 0, {'age_of_cube': '14 Days','cube_identification': 'Cube-2'}),
            (0, 0, {'age_of_cube': '14 Days','cube_identification': 'Cube-3'}),
            (0, 0, {'age_of_cube': '28 Days','cube_identification': 'Cube-1'}),
            (0, 0, {'age_of_cube': '28 Days','cube_identification': 'Cube-2'}),
            (0, 0, {'age_of_cube': '28 Days','cube_identification': 'Cube-3'}),
            
        ]
        return default_lines 


    avg_3_days = fields.Float(
        string="3 Days Average",
        compute="_compute_aaverage",
        store=True
    )
    avg_7_days = fields.Float(
        string="7 Days Average",
        compute="_compute_aaverage",
        store=True
    )
    avg_14_days = fields.Float(
        string="14 Days Average",
        compute="_compute_aaverage",
        store=True
    )
    avg_28_days = fields.Float(
        string="28 Days Average",
        compute="_compute_aaverage",
        store=True
    )

    @api.depends('density_line_ids.age_of_cube', 'density_line_ids.density')
    def _compute_aaverage(self):
        for rec in self:
            rec.avg_3_days = 0.0
            rec.avg_7_days = 0.0
            rec.avg_14_days = 0.0
            rec.avg_28_days = 0.0

            age_map = {
                '3 Days': 'avg_3_days',
                '7 Days': 'avg_7_days',
                '14 Days': 'avg_14_days',
                '28 Days': 'avg_28_days',
            }

            for age, field in age_map.items():
                lines = rec.density_line_ids.filtered(
                    lambda l: (l.age_of_cube or '').strip().lower() == age.lower()
                )
                if lines:
                    setattr(
                        rec,
                        field,
                        round(sum(lines.mapped('density')) / len(lines), 2)
                    )

    avg_3_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_avg_3_days_confirmity")

    avg_3_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_avg_3_days_nabl",store=True)


    @api.depends('avg_3_days','eln_ref')
    def _compute_avg_3_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_3_days_confirmity = 'na'
                continue
            record.avg_3_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f336e8b-f38d-40f4-a82f-876b7d590050')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f336e8b-f38d-40f4-a82f-876b7d590050')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_3_days - record.avg_3_days*mu_value
                    upper = record.avg_3_days + record.avg_3_days*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_3_days_confirmity = 'pass'
                        break
                    else:
                        record.avg_3_days_confirmity = 'fail'

    @api.depends('avg_3_days','eln_ref')
    def _compute_avg_3_days_nabl(self):
        
        for record in self:
            record.avg_3_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f336e8b-f38d-40f4-a82f-876b7d590050')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f336e8b-f38d-40f4-a82f-876b7d590050')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.avg_3_days - record.avg_3_days*mu_value
                  upper = record.avg_3_days + record.avg_3_days*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.avg_3_days_nabl = 'pass'
                      break
                  else:
                      record.avg_3_days_nabl = 'fail'

    avg_3_days_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_3_days_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_3_days_final_report", store=True)

    @api.depends('avg_3_days_nabl', 'avg_3_days_report_type')
    def _compute_avg_3_days_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_3_days_report_type == 'nabl':
            rec.avg_3_days_final_report = 'nabl'

        elif rec.avg_3_days_report_type == 'non_nabl':
            rec.avg_3_days_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_3_days_nabl == 'pass':
                rec.avg_3_days_final_report = 'nabl'
            else:
                rec.avg_3_days_final_report = 'non_nabl'


    avg_7_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_avg_7_days_confirmity")

    avg_7_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_avg_7_days_nabl",store=True)


    @api.depends('avg_7_days','eln_ref')
    def _compute_avg_7_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_7_days_confirmity = 'na'
                continue
            record.avg_7_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5cc67a03-39a1-4760-99fe-d4297da73177')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5cc67a03-39a1-4760-99fe-d4297da73177')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_7_days - record.avg_7_days*mu_value
                    upper = record.avg_7_days + record.avg_7_days*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_7_days_confirmity = 'pass'
                        break
                    else:
                        record.avg_7_days_confirmity = 'fail'

    @api.depends('avg_7_days','eln_ref')
    def _compute_avg_7_days_nabl(self):
        
        for record in self:
            record.avg_7_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5cc67a03-39a1-4760-99fe-d4297da73177')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5cc67a03-39a1-4760-99fe-d4297da73177')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.avg_7_days - record.avg_7_days*mu_value
                  upper = record.avg_7_days + record.avg_7_days*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.avg_7_days_nabl = 'pass'
                      break
                  else:
                      record.avg_7_days_nabl = 'fail'

    avg_7_days_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_7_days_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_7_days_final_report", store=True)

    @api.depends('avg_7_days_nabl', 'avg_7_days_report_type')
    def _compute_avg_7_days_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_7_days_report_type == 'nabl':
            rec.avg_7_days_final_report = 'nabl'

        elif rec.avg_7_days_report_type == 'non_nabl':
            rec.avg_7_days_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_7_days_nabl == 'pass':
                rec.avg_7_days_final_report = 'nabl'
            else:
                rec.avg_7_days_final_report = 'non_nabl'



    avg_14_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_avg_14_days_confirmity")

    avg_14_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_avg_14_days_nabl",store=True)


    @api.depends('avg_14_days','eln_ref')
    def _compute_avg_14_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_14_days_confirmity = 'na'
                continue
            record.avg_14_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0d6db366-2435-4676-be4f-1a1b5aec490d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0d6db366-2435-4676-be4f-1a1b5aec490d')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_14_days - record.avg_14_days*mu_value
                    upper = record.avg_14_days + record.avg_14_days*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_14_days_confirmity = 'pass'
                        break
                    else:
                        record.avg_14_days_confirmity = 'fail'

    @api.depends('avg_14_days','eln_ref')
    def _compute_avg_14_days_nabl(self):
        
        for record in self:
            record.avg_14_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0d6db366-2435-4676-be4f-1a1b5aec490d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0d6db366-2435-4676-be4f-1a1b5aec490d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.avg_14_days - record.avg_14_days*mu_value
                  upper = record.avg_14_days + record.avg_14_days*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.avg_14_days_nabl = 'pass'
                      break
                  else:
                      record.avg_14_days_nabl = 'fail'


    avg_14_days_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_14_days_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_14_days_final_report", store=True)

    @api.depends('avg_14_days_nabl', 'avg_14_days_report_type')
    def _compute_avg_14_days_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_14_days_report_type == 'nabl':
            rec.avg_14_days_final_report = 'nabl'

        elif rec.avg_14_days_report_type == 'non_nabl':
            rec.avg_14_days_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_14_days_nabl == 'pass':
                rec.avg_14_days_final_report = 'nabl'
            else:
                rec.avg_14_days_final_report = 'non_nabl'



    avg_28_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_avg_28_days_confirmity")

    avg_28_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_avg_28_days_nabl",store=True)


    @api.depends('avg_28_days','eln_ref')
    def _compute_avg_28_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_28_days_confirmity = 'na'
                continue
            record.avg_28_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a02bef3e-f698-4cb0-a542-2dd61ccb9ed4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a02bef3e-f698-4cb0-a542-2dd61ccb9ed4')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_28_days - record.avg_28_days*mu_value
                    upper = record.avg_28_days + record.avg_28_days*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_28_days_confirmity = 'pass'
                        break
                    else:
                        record.avg_28_days_confirmity = 'fail'

    @api.depends('avg_28_days','eln_ref')
    def _compute_avg_28_days_nabl(self):
        
        for record in self:
            record.avg_28_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a02bef3e-f698-4cb0-a542-2dd61ccb9ed4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a02bef3e-f698-4cb0-a542-2dd61ccb9ed4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.avg_28_days - record.avg_28_days*mu_value
                  upper = record.avg_28_days + record.avg_28_days*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.avg_28_days_nabl = 'pass'
                      break
                  else:
                      record.avg_28_days_nabl = 'fail'


    avg_28_days_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_28_days_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_28_days_final_report", store=True)

    @api.depends('avg_28_days_nabl', 'avg_28_days_report_type')
    def _compute_avg_28_days_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_28_days_report_type == 'nabl':
            rec.avg_28_days_final_report = 'nabl'

        elif rec.avg_28_days_report_type == 'non_nabl':
            rec.avg_28_days_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_28_days_nabl == 'pass':
                rec.avg_28_days_final_report = 'nabl'
            else:
                rec.avg_28_days_final_report = 'non_nabl'


    # Weight								
    weight_name = fields.Char(default="Weight Of Concrete Cube")
    weight_visible = fields.Boolean(compute="_compute_visible")

    weight_line_ids = fields.One2many('cube.weight.line','parent_id',string="Weight Of Concrete Cube",default=lambda self: self.weight_line_ids_sizes()
    )

    @api.model
    def weight_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'age_of_cube': '3 Days','cube_identification': 'Cube-1'}),
            (0, 0, {'age_of_cube': '3 Days','cube_identification': 'Cube-2'}),
            (0, 0, {'age_of_cube': '3 Days','cube_identification': 'Cube-3'}),
            (0, 0, {'age_of_cube': '7 Days','cube_identification': 'Cube-1'}),
            (0, 0, {'age_of_cube': '7 Days','cube_identification': 'Cube-2'}),
            (0, 0, {'age_of_cube': '7 Days','cube_identification': 'Cube-3'}),
            (0, 0, {'age_of_cube': '14 Days','cube_identification': 'Cube-1'}),
            (0, 0, {'age_of_cube': '14 Days','cube_identification': 'Cube-2'}),
            (0, 0, {'age_of_cube': '14 Days','cube_identification': 'Cube-3'}),
            (0, 0, {'age_of_cube': '28 Days','cube_identification': 'Cube-1'}),
            (0, 0, {'age_of_cube': '28 Days','cube_identification': 'Cube-2'}),
            (0, 0, {'age_of_cube': '28 Days','cube_identification': 'Cube-3'}),
            
        ]
        return default_lines 


    weight_avg_3_days = fields.Float(
        string="3 Days Average",
        compute="_compute_aaaverage",
        store=True,digits=(16,3)
    )
    weight_avg_7_days = fields.Float(
        string="7 Days Average",
        compute="_compute_aaaverage",
        store=True,digits=(16,3)
    )
    weight_avg_14_days = fields.Float(
        string="14 Days Average",
        compute="_compute_aaaverage",
        store=True,digits=(16,3)
    )
    weight_avg_28_days = fields.Float(
        string="28 Days Average",
        compute="_compute_aaaverage",
        store=True,digits=(16,3)
    )

    @api.depends('weight_line_ids.age_of_cube', 'weight_line_ids.weight')
    def _compute_aaaverage(self):
        for rec in self:
            rec.weight_avg_3_days = 0.0
            rec.weight_avg_7_days = 0.0
            rec.weight_avg_14_days = 0.0
            rec.weight_avg_28_days = 0.0

            age_map = {
                '3 Days': 'weight_avg_3_days',
                '7 Days': 'weight_avg_7_days',
                '14 Days': 'weight_avg_14_days',
                '28 Days': 'weight_avg_28_days',
            }

            for age, field in age_map.items():
                lines = rec.weight_line_ids.filtered(
                    lambda l: (l.age_of_cube or '').strip().lower() == age.lower()
                )
                if lines:
                    setattr(
                        rec,
                        field,
                        round(sum(lines.mapped('weight')) / len(lines), 2)
                    )

    weight_avg_3_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_weight_avg_3_days_confirmity")

    weight_avg_3_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_weight_avg_3_days_nabl",store=True)


    @api.depends('weight_avg_3_days','eln_ref')
    def _compute_weight_avg_3_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.weight_avg_3_days_confirmity = 'na'
                continue
            record.weight_avg_3_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e520f639-09eb-4673-9d7c-c39f296d50a8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e520f639-09eb-4673-9d7c-c39f296d50a8')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.weight_avg_3_days - record.weight_avg_3_days*mu_value
                    upper = record.weight_avg_3_days + record.weight_avg_3_days*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.weight_avg_3_days_confirmity = 'pass'
                        break
                    else:
                        record.weight_avg_3_days_confirmity = 'fail'
                        

    @api.depends('weight_avg_3_days','eln_ref')
    def _compute_weight_avg_3_days_nabl(self):
        
        for record in self:
            record.weight_avg_3_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e520f639-09eb-4673-9d7c-c39f296d50a8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e520f639-09eb-4673-9d7c-c39f296d50a8')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.weight_avg_3_days - record.weight_avg_3_days*mu_value
                  upper = record.weight_avg_3_days + record.weight_avg_3_days*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.weight_avg_3_days_nabl = 'pass'
                      break
                  else:
                      record.weight_avg_3_days_nabl = 'fail'


    weight_avg_3_days_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    weight_avg_3_days_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_weight_avg_3_days_final_report", store=True)

    @api.depends('weight_avg_3_days_nabl', 'weight_avg_3_days_report_type')
    def _compute_weight_avg_3_days_final_report(self):
     for rec in self:

        # Manual override
        if rec.weight_avg_3_days_report_type == 'nabl':
            rec.weight_avg_3_days_final_report = 'nabl'

        elif rec.weight_avg_3_days_report_type == 'non_nabl':
            rec.weight_avg_3_days_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.weight_avg_3_days_nabl == 'pass':
                rec.weight_avg_3_days_final_report = 'nabl'
            else:
                rec.weight_avg_3_days_final_report = 'non_nabl'


    weight_avg_7_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_weight_avg_7_days_confirmity")

    weight_avg_7_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_weight_avg_7_days_nabl",store=True)


    @api.depends('weight_avg_7_days','eln_ref')
    def _compute_weight_avg_7_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.weight_avg_7_days_confirmity = 'na'
                continue
            record.weight_avg_7_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ab9f1c0e-0d0b-4f49-9d05-b1205b709846')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ab9f1c0e-0d0b-4f49-9d05-b1205b709846')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.weight_avg_7_days - record.weight_avg_7_days*mu_value
                    upper = record.weight_avg_7_days + record.weight_avg_7_days*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.weight_avg_7_days_confirmity = 'pass'
                        break
                    else:
                        record.weight_avg_7_days_confirmity = 'fail'

    @api.depends('weight_avg_7_days','eln_ref')
    def _compute_weight_avg_7_days_nabl(self):
        
        for record in self:
            record.weight_avg_7_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ab9f1c0e-0d0b-4f49-9d05-b1205b709846')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ab9f1c0e-0d0b-4f49-9d05-b1205b709846')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.weight_avg_7_days - record.weight_avg_7_days*mu_value
                  upper = record.weight_avg_7_days + record.weight_avg_7_days*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.weight_avg_7_days_nabl = 'pass'
                      break
                  else:
                      record.weight_avg_7_days_nabl = 'fail'


    weight_avg_7_days_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    weight_avg_7_days_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_weight_avg_7_days_final_report", store=True)

    @api.depends('weight_avg_7_days_nabl', 'weight_avg_7_days_report_type')
    def _compute_weight_avg_7_days_final_report(self):
     for rec in self:

        # Manual override
        if rec.weight_avg_7_days_report_type == 'nabl':
            rec.weight_avg_7_days_final_report = 'nabl'

        elif rec.weight_avg_7_days_report_type == 'non_nabl':
            rec.weight_avg_7_days_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.weight_avg_7_days_nabl == 'pass':
                rec.weight_avg_7_days_final_report = 'nabl'
            else:
                rec.weight_avg_7_days_final_report = 'non_nabl'



    weight_avg_14_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_weight_avg_14_days_confirmity")

    weight_avg_14_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_weight_avg_14_days_nabl",store=True)


    @api.depends('weight_avg_14_days','eln_ref')
    def _compute_weight_avg_14_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.weight_avg_14_days_confirmity = 'na'
                continue
            record.weight_avg_14_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9f4b7532-2cec-45c1-bdd1-a8c91f7892ee')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9f4b7532-2cec-45c1-bdd1-a8c91f7892ee')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.weight_avg_14_days - record.weight_avg_14_days*mu_value
                    upper = record.weight_avg_14_days + record.weight_avg_14_days*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.weight_avg_14_days_confirmity = 'pass'
                        break
                    else:
                        record.weight_avg_14_days_confirmity = 'fail'

    @api.depends('weight_avg_14_days','eln_ref')
    def _compute_weight_avg_14_days_nabl(self):
        
        for record in self:
            record.weight_avg_14_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9f4b7532-2cec-45c1-bdd1-a8c91f7892ee')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9f4b7532-2cec-45c1-bdd1-a8c91f7892ee')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.weight_avg_14_days - record.weight_avg_14_days*mu_value
                  upper = record.weight_avg_14_days + record.weight_avg_14_days*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.weight_avg_14_days_nabl = 'pass'
                      break
                  else:
                      record.weight_avg_14_days_nabl = 'fail'


    weight_avg_14_days_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    weight_avg_14_days_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_weight_avg_14_days_final_report", store=True)

    @api.depends('weight_avg_14_days_nabl', 'weight_avg_14_days_report_type')
    def _compute_weight_avg_14_days_final_report(self):
     for rec in self:

        # Manual override
        if rec.weight_avg_14_days_report_type == 'nabl':
            rec.weight_avg_14_days_final_report = 'nabl'

        elif rec.weight_avg_14_days_report_type == 'non_nabl':
            rec.weight_avg_14_days_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.weight_avg_14_days_nabl == 'pass':
                rec.weight_avg_14_days_final_report = 'nabl'
            else:
                rec.weight_avg_14_days_final_report = 'non_nabl'



    weight_avg_28_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_weight_avg_28_days_confirmity")

    weight_avg_28_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_weight_avg_28_days_nabl",store=True)


    @api.depends('weight_avg_28_days','eln_ref')
    def _compute_weight_avg_28_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.weight_avg_28_days_confirmity = 'na'
                continue
            record.weight_avg_28_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6933466b-7f6b-4ae1-acaf-45664966b3fd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6933466b-7f6b-4ae1-acaf-45664966b3fd')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.weight_avg_28_days - record.weight_avg_28_days*mu_value
                    upper = record.weight_avg_28_days + record.weight_avg_28_days*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.weight_avg_28_days_confirmity = 'pass'
                        break
                    else:
                        record.weight_avg_28_days_confirmity = 'fail'

    @api.depends('weight_avg_28_days','eln_ref')
    def _compute_weight_avg_28_days_nabl(self):
        
        for record in self:
            record.weight_avg_28_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6933466b-7f6b-4ae1-acaf-45664966b3fd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6933466b-7f6b-4ae1-acaf-45664966b3fd')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.weight_avg_28_days - record.weight_avg_28_days*mu_value
                  upper = record.weight_avg_28_days + record.weight_avg_28_days*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.weight_avg_28_days_nabl = 'pass'
                      break
                  else:
                      record.weight_avg_28_days_nabl = 'fail'


    weight_avg_28_days_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    weight_avg_28_days_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_weight_avg_28_days_final_report", store=True)

    @api.depends('weight_avg_28_days_nabl', 'weight_avg_28_days_report_type')
    def _compute_weight_avg_28_days_final_report(self):
     for rec in self:

        # Manual override
        if rec.weight_avg_28_days_report_type == 'nabl':
            rec.weight_avg_28_days_final_report = 'nabl'

        elif rec.weight_avg_28_days_report_type == 'non_nabl':
            rec.weight_avg_28_days_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.weight_avg_28_days_nabl == 'pass':
                rec.weight_avg_28_days_final_report = 'nabl'
            else:
                rec.weight_avg_28_days_final_report = 'non_nabl'



    

    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.cube_visible = False
            record.water_permeability_visible = False
            record.act_compressive_visible = False
            record.density_visible = False
            record.weight_visible = False
           
            
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
               
                if sample.internal_id == "23545tur-17c1-48ac-8462-9671e4d3d09f":
                    record.cube_visible = True

                if sample.internal_id == "1023457-0268-46ef-ba88-9c0453210lkit1":
                    record.water_permeability_visible = True

                if sample.internal_id == "24b7a3b3-55c6-4b1b-84a6-d6cc986a7715":
                    record.act_compressive_visible = True


                if sample.internal_id == "30214iu-eba3-4f15-b33d-679b39f73301":
                    record.density_visible = True

                if sample.internal_id == "8d3d7fd8-9294-4390-89a2-bb21ac06aeca":
                    record.weight_visible = True

                    

                



    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
         
  
            if result.parameter.internal_id == '23545tur-17c1-48ac-8462-9671e4d3d09f':
                result.calculated = True
                result.result_char = round(self.average_strength,2)
                if self.average_depth_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            
            # Water Permeaility
            if result.parameter.internal_id == '1023457-0268-46ef-ba88-9c0453210lkit1':
                result.calculated = True
                result.result_char = round(self.average_depth,2)
                if self.average_depth_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


             # Compressive Strength By ACT
            if result.parameter.internal_id == '24b7a3b3-55c6-4b1b-84a6-d6cc986a7715':
                result.calculated = True
                result.result_char = round(self.average_act_compressive,2)
                if self.average_act_compressive_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Density
            if result.parameter.internal_id == '30214iu-eba3-4f15-b33d-679b39f73301':
                result.calculated = True
            

            # Density (3 days)
            if result.parameter.internal_id == '5f336e8b-f38d-40f4-a82f-876b7d590050':
                result.calculated = True
                result.result_char = round(self.avg_3_days,2)
                if self.avg_3_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Density (7 days)
            if result.parameter.internal_id == '5cc67a03-39a1-4760-99fe-d4297da73177':
                result.calculated = True
                result.result_char = round(self.avg_7_days,2)
                if self.avg_7_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Density (14 days)
            if result.parameter.internal_id == '0d6db366-2435-4676-be4f-1a1b5aec490d':
                result.calculated = True
                result.result_char = round(self.avg_14_days,2)
                if self.avg_14_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Density (28 days)
            if result.parameter.internal_id == 'a02bef3e-f698-4cb0-a542-2dd61ccb9ed4':
                result.calculated = True
                result.result_char = round(self.avg_28_days,2)
                if self.avg_28_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Weight
            if result.parameter.internal_id == '8d3d7fd8-9294-4390-89a2-bb21ac06aeca':
                result.calculated = True
            

            # Weight (3 days)
            if result.parameter.internal_id == 'e520f639-09eb-4673-9d7c-c39f296d50a8':
                result.calculated = True
                result.result_char = round(self.weight_avg_3_days,2)
                if self.weight_avg_3_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Weight (7 days)
            if result.parameter.internal_id == 'ab9f1c0e-0d0b-4f49-9d05-b1205b709846':
                result.calculated = True
                result.result_char = round(self.weight_avg_7_days,2)
                if self.weight_avg_7_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Weight (14 days)
            if result.parameter.internal_id == '9f4b7532-2cec-45c1-bdd1-a8c91f7892ee':
                result.calculated = True
                result.result_char = round(self.weight_avg_14_days,2)
                if self.weight_avg_14_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Weight (28 days)
            if result.parameter.internal_id == '6933466b-7f6b-4ae1-acaf-45664966b3fd':
                result.calculated = True
                result.result_char = round(self.weight_avg_28_days,2)
                if self.weight_avg_28_days_nabl == 'pass':
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
        # return {'type': 'ir.actions.client', 'tag': 'history_back'}

            

    # @api.depends('eln_ref')
    # def _compute_grade_id(self):
    #     if self.eln_ref:
    #         self.grade = self.eln_ref.grade_id.id


    # @api.depends('average_strength','eln_ref','grade')
    # def _compute_nabl(self):
        
    #     for record in self:
    #         record.nabl = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23545tur-17c1-48ac-8462-9671e4d3d09f')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23545tur-17c1-48ac-8462-9671e4d3d09f')]).parameter_table
    #         # for material in materials:
    #         #     if material.grade.id == record.grade.id:
    #         lab_min = line.lab_min_value
    #         lab_max = line.lab_max_value
    #         mu_value = line.mu_value
            
    #         lower = record.average_strength - record.average_strength*mu_value
    #         upper = record.average_strength + record.average_strength*mu_value
    #         if lower >= lab_min and upper <= lab_max:
    #             record.nabl = 'pass'
    #             break
    #         else:
    #             record.nabl = 'fail'


    # @api.depends('average_strength','eln_ref','grade','age_of_days','difference')
    # def _compute_confirmity(self):
    #     for record in self:
    #         record.confirmity = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23545tur-17c1-48ac-8462-9671e4d3d09f')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23545tur-17c1-48ac-8462-9671e4d3d09f')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 req_min = material.req_min
    #                 req_max = material.req_max
    #                 mu_value = line.mu_value
    #                 if record.age_of_days == "3days":
    #                     req_min = req_min * 0.5
    #                     req_max = req_max* 0.5
    #                 if record.age_of_days == "7days":
    #                     req_min = req_min * 0.7
    #                     req_max = req_max* 0.7
    #                 if record.age_of_days == "14days":
    #                     req_min = req_min * 0.9
    #                     req_max = req_max* 0.9
    #                 if record.age_of_days == "28days":
    #                     req_min = req_min
    #                     req_max = req_max
    #                 lower = record.average_strength - record.average_strength*mu_value
    #                 upper = record.average_strength + record.average_strength*mu_value
                    
    #                 if record.difference == 0:
    #                     if lower >= req_min and upper <= req_max :
    #                         record.confirmity = 'pass'
    #                         break
    #                     else:
    #                         record.confirmity = 'fail'
    #                 else:
    #                     record.confirmity = 'not_applicable'


    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    
    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(MechanicalConcreteCube, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record
    

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
        record = self.env['mechanical.concrete.cube'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()
        self.default_get(fields)

        return super(MechanicalConcreteCube, self).read(fields=fields, load=load)

class MechanicalConcreteCubeLine(models.Model):
    _name = "mechanical.concrete.cube.line"
    parent_id = fields.Many2one('mechanical.concrete.cube',string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.",readonly=True, copy=False, default=1)
  
    id_mark = fields.Char(string="Sample Identification",store=True)
    wt_sample = fields.Float(string="Weight of  Specimen (gms)",digits=(16,3))

    dt_of_casting = fields.Date(string="Date of casting",compute="_compute_dt_of_casting",store=True)
    days = fields.Integer(string="No.of Days",compute="_compute_days",store=True)
    dt_of_testing1 = fields.Date(string="Date of Testing",compute="_compute_dt_of_testing",store=True)

    load = fields.Float(string="Maximum Load (KN)")
    compressive_strength = fields.Float(string="Compressive Strength (N/mm2)",compute="_compute_strength",store=True)

    avg_compressive_strength = fields.Float(string="Avg. Compressive Strength (N/mm2)")
    area = fields.Float(string="Area (cm²)",compute="_compute_area",store=True)
    dimension = fields.Char(string="Dimension (mm)",compute="_compute_dimension",store=True)
    volume = fields.Float(string="Volume (cc)")
    density = fields.Float(string="Density (gms/cc)",compute="_compute_density",store=True,digits=(16,3))

    @api.depends('parent_id.size_id') 
    def _compute_area(self):
        for rec in self:
            rec.area = rec.parent_id.area_of_cube / 1000

    @api.depends('parent_id.size_id') 
    def _compute_dimension(self):
        for rec in self:
            rec.dimension = rec.parent_id.size_id.size
            
    @api.depends('wt_sample','volume')
    def _compute_density(self):
        for rec in self:
            if rec.wt_sample and rec.volume:
                rec.density = round((rec.wt_sample) / rec.volume,3)
            else:
                rec.density = 0.0

    # @api.depends('parent_id', 'parent_id.child_lines.compressive_strength')
    # def _compute_avg_strength(self):
    #     for rec in self:
    #         if rec.parent_id and rec.parent_id.child_lines:
    #             strengths = rec.parent_id.child_lines.mapped('compressive_strength')
    #             values = [s for s in strengths if s > 0]
    #             rec.avg_compressive_strength = sum(values) / len(values) if values else 0.0
    #         else:
    #             rec.avg_compressive_strength = 0.0

    @api.depends('load', 'area')
    def _compute_strength(self):
        for record in self:
            if record.area:
                record.compressive_strength = record.load / record.area
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
                    # Extract number from string like '3days', '28days'
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

   
    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        for record in self:
            client_sample_id = ""
            if record.parent_id:
                eln_ref = record.parent_id.eln_ref
                if eln_ref:
                    sample = eln_ref.sample_id
                    if sample:
                        client_sample_id = sample.client_sample_id
            record.id_mark = client_sample_id or ""

    # @api.onchange('id_mark')
    # def _onchange_id_mark(self):
    #     for record in self:
    #         if record.id_mark:
    #             if record.parent_id and record.parent_id.eln_ref and record.parent_id.eln_ref.sample_id:
    #                 # Only update if client_sample_id is not set
    #                 if not record.parent_id.eln_ref.sample_id.client_sample_id:
    #                     record.parent_id.eln_ref.sample_id.client_sample_id = record.id_mark
    #             else:
    #                 _logger.info("Sample or references not set.")
    #         else:
    #             _logger.info("id_mark is empty.")

    @api.depends('parent_id.eln_ref.sample_id.client_sample_id')
    def _compute_id_mark(self):
        for record in self:
            record.id_mark = (
                record.parent_id.eln_ref.sample_id.client_sample_id
                if record.parent_id and record.parent_id.eln_ref and record.parent_id.eln_ref.sample_id
                else ""
            )






  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalConcreteCubeLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1




class MechanicalConcreteCubeGradeLine(models.Model):
    _name = "mechanical.concrete.cube.grade.line"
    parent_id = fields.Many2one('mechanical.concrete.cube',string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.",readonly=True, copy=False, default=1)
  
    grade1 = fields.Char(string="Grade")
    sd = fields.Float(string="SD")


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalConcreteCubeGradeLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class WptMechanicalLine(models.Model):
    _name = "mechanical.cube.wpt.line"
    parent_id = fields.Many2one('mechanical.concrete.cube',string="Parent Id")

    serial_no = fields.Integer(string="Trial.No", readonly=True, copy=False, default=1)



    pressure = fields.Float(
        string="Water Pressure Applied (bar/kg/cm²)"
    )

    duration = fields.Float(
        string="Duration of Test (hrs)"
    )

    maximum_depth = fields.Float(
        string="Maximum Depth of Water Penetration (mm)"
    )

    average_depth = fields.Float(
        string="Average Depth of Penetration (mm)"
    )


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(WptMechanicalLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class CompressiveByACTLine(models.Model):
    _name = 'compressive.by.act.line'
    _description = 'Accelerated Test Line'

    parent_id = fields.Many2one('mechanical.concrete.cube',string="Parent Id")

    serial_no = fields.Integer(string="Trial.No", readonly=True, copy=False, default=1)

    age_start = fields.Float(
        string="Age at Start of Accelerated Curing (23 ± 0.25 hrs)"
    )

    boiling_duration = fields.Float(
        string="Boiling Water Curing Duration (3.5 ± 0.08 hrs)"
    )

    cooling_period = fields.Float(
        string="Cooling Period at 27 ± 2°C (Minimum 1 hr)"
    )

    failure_load = fields.Float(string="Failure Load (kN)")

    loaded_area = fields.Float(
        string="Loaded Area (mm²)",compute="_loaded_area",
        store=True
    )

    ra = fields.Float(
        string="Accelerated Compressive Strength, Ra (N/mm²)",
        compute="_compute_ra",
        store=True
    )

    strength_28 = fields.Float(
        string="Estimated 28-Day Strength, (N/mm²) =(8.09+1.64Ra)",
        compute="_compute_strength",
        store=True
    )

    @api.depends('parent_id.size_id.size')
    def _loaded_area(self):
        import re
        for record in self:
            size_str = record.parent_id.size_id.size
            if size_str:
                match = re.search(r'\d+', str(size_str))
                if match:
                    side = int(match.group())
                    record.loaded_area = side * side  # or whatever formula
                else:
                    record.loaded_area = 0
            else:
                record.loaded_area = 0

    @api.depends('failure_load', 'loaded_area')
    def _compute_ra(self):
        for rec in self:
            if rec.loaded_area:
                rec.ra = (rec.failure_load * 1000) / rec.loaded_area
            else:
                rec.ra = 0

    @api.depends('ra')
    def _compute_strength(self):
        for rec in self:
            rec.strength_28 = 8.09 + (1.64 * rec.ra)


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CompressiveByACTLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class CubeDensityLine(models.Model):
    _name = 'cube.density.line'

    parent_id = fields.Many2one('mechanical.concrete.cube',string="Parent Id")

    age_of_cube = fields.Char(string="Age of Cube")

    cube_identification = fields.Char(string="Cube Identification No.")

    length = fields.Float(string="Length, L (mm)",
        compute="_compute_dimensions",
        store=True
    )

    breadth = fields.Float(string="Breadth, B (mm)",
        compute="_compute_dimensions",
        store=True
    )

    height = fields.Float(string="Height, H (mm)",
        compute="_compute_dimensions",
        store=True
    )

    volume = fields.Float(string="Volume, V (m³)",
        compute="_compute_volume",
        store=True,digits=(16,6)
    )

    mass = fields.Float(string="Mass of Cube, M (kg)",digits=(16,3))

    density = fields.Float(string="Density, ρ = M/V (kg/m³)",
        compute="_compute_density",
        store=True
    )

    @api.depends('parent_id.size_id.size')
    def _compute_dimensions(self):
        for rec in self:
            rec.length = 0
            rec.breadth = 0
            rec.height = 0

            size = rec.parent_id.size_id.size
            if size:
                nums = re.findall(r'\d+', size)

                if len(nums) >= 3:
                    rec.length = float(nums[0])
                    rec.breadth = float(nums[1])
                    rec.height = float(nums[2])

                elif len(nums) == 1:
                    side = float(nums[0])
                    rec.length = side
                    rec.breadth = side
                    rec.height = side

    @api.depends('length', 'breadth', 'height')
    def _compute_volume(self):
        for rec in self:
            if rec.length and rec.breadth and rec.height:
                # Convert mm³ to m³
                rec.volume = (rec.length * rec.breadth * rec.height) / 1000000000
            else:
                rec.volume = 0

    @api.depends('mass', 'volume')
    def _compute_density(self):
        for rec in self:
            if rec.volume:
                rec.density = rec.mass / rec.volume
            else:
                rec.density = 0


class CubeWeightLine(models.Model):
    _name = 'cube.weight.line'

    parent_id = fields.Many2one('mechanical.concrete.cube',string="Parent Id")

    age_of_cube = fields.Char(string="Age of Cube")

    cube_identification = fields.Char(string="Cube Identification No.")

    length = fields.Float(string="Length, L (mm)",
        compute="_compute_dimensions",
        store=True
    )

    breadth = fields.Float(string="Breadth, B (mm)",
        compute="_compute_dimensions",
        store=True
    )

    height = fields.Float(string="Height, H (mm)",
        compute="_compute_dimensions",
        store=True
    )

    volume = fields.Float(string="Volume, V (m³)",
        compute="_compute_volume",
        store=True,digits=(16,6)
    )

    # mass = fields.Float(string="Mass of Cube, M (kg)",digits=(16,3))

    weight = fields.Float(string="Weight of Cube, W (kg)",digits=(16,3)
    )

    @api.depends('parent_id.size_id.size')
    def _compute_dimensions(self):
        for rec in self:
            rec.length = 0
            rec.breadth = 0
            rec.height = 0

            size = rec.parent_id.size_id.size
            if size:
                nums = re.findall(r'\d+', size)

                if len(nums) >= 3:
                    rec.length = float(nums[0])
                    rec.breadth = float(nums[1])
                    rec.height = float(nums[2])

                elif len(nums) == 1:
                    side = float(nums[0])
                    rec.length = side
                    rec.breadth = side
                    rec.height = side

    @api.depends('length', 'breadth', 'height')
    def _compute_volume(self):
        for rec in self:
            if rec.length and rec.breadth and rec.height:
                # Convert mm³ to m³
                rec.volume = (rec.length * rec.breadth * rec.height) / 1000000000
            else:
                rec.volume = 0

    




class ConcreteCubeNotes(models.Model):
    _name = "concrete.cube.notes"

    parent_id = fields.Many2one('mechanical.concrete.cube',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
