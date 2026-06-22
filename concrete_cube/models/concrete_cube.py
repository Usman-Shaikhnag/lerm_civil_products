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
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    child_lines = fields.One2many('mechanical.concrete.cube.line','parent_id',string="Parameter")
    
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="ELN")

    sample_id = fields.Many2one('lerm.srf.sample',string='Sample')

    temprature = fields.Integer("Temperature (°C)", digits=(10,2))
    humidity = fields.Integer("Humidity (%)", digits=(10,2))

    week_no = fields.Char("Week No")

    other_details = fields.Char("Other Details")

    condition = fields.Char("Condition")

    description_work = fields.Text("Description Of Work")


    cube_name = fields.Char("Name",default=" Cube")
    cube_visible = fields.Boolean("Chequered Visible",compute="_compute_visible")   

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
            

    confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('not_applicable', 'Not Applicable'),

    ], string='Confirmity', default='fail',compute="_compute_confirmity")
    age_of_test = fields.Integer("Age of Test, days",compute="compute_age_of_test")
    difference = fields.Integer("Difference",compute="compute_difference")

    # grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),

    ], string='NABL', default='fail',compute="_compute_nabl")


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


    wpt_name = fields.Char("Name",default=" Water Permeability Test")
    wpt_visible = fields.Boolean("WPT Visible",compute="_compute_visible") 

    wpt_child_lines = fields.One2many('mechanical.cube.wpt.line','parent_id',string="Parameter")

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
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_wpt_conformity", store=True)

    @api.depends('average_of_wpt','eln_ref','grade')
    def _compute_wpt_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.wpt_conformity = 'na'
                continue

            record.wpt_conformity = 'fail'
            line = self.env['lerm.parameter.master'].search([('internal_id','=','1023457-0268-46ef-ba88-9c0453210lkit1')])
            materials = self.env['lerm.parameter.master'].search([('internal_id','=','1023457-0268-46ef-ba88-9c0453210lkit1')]).parameter_table
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
            line = self.env['lerm.parameter.master'].search([('internal_id','=','1023457-0268-46ef-ba88-9c0453210lkit1')])
            materials = self.env['lerm.parameter.master'].search([('internal_id','=','1023457-0268-46ef-ba88-9c0453210lkit1')]).parameter_table
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




    

# remark

    notes_id = fields.One2many('cube.notes', 'parent_id', string="Notes",default=lambda self: self._default_notes_lines())
    
    @api.model
    def _default_notes_lines(self):
        return [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The report shall not be reproduced in full or partially without written approval of the laboratory HOD/CEO/Maganement.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'Sampling is not done by us unless mentioned otherwide.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'without a QR Code and hologram this report is considered invalid.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'The Result listed refer only to tested samples & applicable parameter Endorsement of product is neither interred nor inplied.',
            }),

            (0, 0, {
                'sr_no': 'e',
                'notes': 'The use or report for arbitration, publicity & evidence in legal dispute is forbidden except with prior written consent NBML Lab.',
            }),
             (0, 0, {
                'sr_no': 'f',
                'notes': 'All disputed are subject to Raipur jurisdiction 7 days correction to this report invalidates this report.',
            }),

             (0, 0, {
                'sr_no': 'g',
                'notes': 'Sample will be destroyed after 30-days from the date of test report unless otherwise Specified.',
            }),
        ]






     # 3. Water Absorption

    water_absorption_name = fields.Char("Name",default="Water Absorption ")
    water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")

    water_absorption_child_lines = fields.One2many('cube.water.absorption.line','parent_id',string="Water Line")

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
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_water_absorption_conformity", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_water_absorption_conformity = 'na'
                continue

            record.avg_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30214iu-eba3-4f15-b33d-679b39f73301')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30214iu-eba3-4f15-b33d-679b39f73301')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30214iu-eba3-4f15-b33d-679b39f73301')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30214iu-eba3-4f15-b33d-679b39f73301')]).parameter_table
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


    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.cube_visible = False
            record.wpt_visible = False
            record.water_absorption_visible = False
            
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
               
                if sample.internal_id == "23545tur-17c1-48ac-8462-9671e4d3d09f":
                    record.cube_visible = True

                if sample.internal_id == "1023457-0268-46ef-ba88-9c0453210lkit1":
                    record.wpt_visible = True

                if sample.internal_id == "30214iu-eba3-4f15-b33d-679b39f73301":
                    record.water_absorption_visible = True




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
                if self.nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == '30214iu-eba3-4f15-b33d-679b39f73301':
                result.calculated = True
                result.result_char = round(self.avg_water_absorption,2)
                if self.nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue



        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == '1023457-0268-46ef-ba88-9c0453210lkit1':
                result.calculated = True
                result.result_char = round(self.average_of_wpt,2)
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
        # return {'type': 'ir.actions.client', 'tag': 'history_back'}

            

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    @api.depends('average_strength','eln_ref','grade')
    def _compute_nabl(self):
        
        for record in self:
            record.nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23545tur-17c1-48ac-8462-9671e4d3d09f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23545tur-17c1-48ac-8462-9671e4d3d09f')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_strength - record.average_strength*mu_value
            upper = record.average_strength + record.average_strength*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.nabl = 'pass'
                break
            else:
                record.nabl = 'fail'


    @api.depends('average_strength','eln_ref','grade','age_of_days','difference')
    def _compute_confirmity(self):
        for record in self:
            record.confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23545tur-17c1-48ac-8462-9671e4d3d09f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23545tur-17c1-48ac-8462-9671e4d3d09f')]).parameter_table
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
                    lower = record.average_strength - record.average_strength*mu_value
                    upper = record.average_strength + record.average_strength*mu_value
                    
                    if record.difference == 0:
                        if lower >= req_min and upper <= req_max :
                            record.confirmity = 'pass'
                            break
                        else:
                            record.confirmity = 'fail'
                    else:
                        record.confirmity = 'not_applicable'


    
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
    

    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     # records = self.env['lerm.eln'].search([('id','=', record.eln_id.id)]).parameters_result
    #     # print("records",records)
    #     # self.sample_parameters = records
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

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



class MechanicalConcreteCubeLine(models.Model):
    _name = "mechanical.concrete.cube.line"
    parent_id = fields.Many2one('mechanical.concrete.cube',string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.",readonly=True, copy=False, default=1)
    length = fields.Float(string="Length (mm)")
    breadth = fields.Float(string="Breadth (mm)")
    area = fields.Float(string="Area (sq.mm)", compute="_compute_area")

    @api.depends('length', 'breadth')
    def _compute_area(self):
        for rec in self:
            rec.area = rec.length * rec.breadth
  
    id_mark = fields.Char(string="Sample Identification",store=True)
    wt_sample = fields.Float(string="Weight of Cube (gms)",digits=(16,3))

    dt_of_casting = fields.Date(string="Date of casting",compute="_compute_dt_of_casting",store=True)
    days = fields.Integer(string="No.of Days",compute="_compute_days",store=True)
    dt_of_testing1 = fields.Date(string="Date of Testing",compute="_compute_dt_of_testing",store=True)


    load = fields.Float(string="Load (kN)")
    compressive_strength = fields.Float(string="Compressive Strength (N/mm2)",compute="_compute_strength",store=True)

    avg_compressive_strength = fields.Float(string="Avg. Compressive Strength (N/mm2)")

    # @api.depends('parent_id', 'parent_id.child_lines.compressive_strength')
    # def _compute_avg_strength(self):
    #     for rec in self:
    #         if rec.parent_id and rec.parent_id.child_lines:
    #             strengths = rec.parent_id.child_lines.mapped('compressive_strength')
    #             values = [s for s in strengths if s > 0]
    #             rec.avg_compressive_strength = sum(values) / len(values) if values else 0.0
    #         else:
    #             rec.avg_compressive_strength = 0.0

    @api.depends('load', 'parent_id.area_of_cube')
    def _compute_strength(self):
        for record in self:
            area = record.parent_id.area_of_cube
            if area:
                record.compressive_strength = (record.load * 1000) / area
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
    _name = "cube.water.absorption.line"
    parent_id = fields.Many2one('mechanical.concrete.cube',string="Parent Id")

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



class CubeNotes(models.Model):
    _name = "cube.notes"

    parent_id = fields.Many2one('mechanical.concrete.cube',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")

