from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math
from math import sqrt
from decimal import Decimal, ROUND_HALF_UP
from statistics import mean


class GgbsMechanical(models.Model):
    _name = "mechanical.ggbs"
    _inherit = "lerm.eln"
    _rec_name = "name"



    name = fields.Char("Name",default="GGBS")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.ggbs.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    notes_id = fields.One2many('ggbs.notes','parent_id',string="Notes")

    @api.model
    def default_get(self, fields):
        res = super(GgbsMechanical, self).default_get(fields)

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

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'ggbs.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }




    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")

    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None


   




# Specific Gravity

    specific_gravity_name1 = fields.Char("Name",default="Density Test")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    temp_specific = fields.Char("Temp.°C" ,required=True)
    humidity_specific= fields.Char("Humidity %")

    temp_water1 = fields.Float("Temperature of Water Bath  when Flask kept in bath – 0C")
    temp_water2 = fields.Float("Temperature of Water Bath  when Flask kept in bath – 0C")

    temp_water_after1 = fields.Float("Temperature of Water Bath  after One Hour when Flask kept in bath – 0C ")
    temp_water_after2 = fields.Float("Temperature of Water Bath  after One Hour when Flask kept in bath – 0C )")

    initial_kerosene1 = fields.Float("Initial Level of Kerosene after one hour kept in Water Bath(A) – ml")
    initial_kerosene2 = fields.Float("Initial Level of Kerosene after one hour kept in Water Bath(A) – ml")

    mass1 = fields.Float("Mass of GGBS Sample Added in Flask (M) – gms")
    mass2 = fields.Float("Mass of GGBS Sample Added in Flask (M) – gms")

    temp_water_flask1 = fields.Float("Temperature of water bath  when Flask kept in bath after Adding GGBS – 0C")
    temp_water_flask2 = fields.Float("Temperature of water bath  when Flask kept in bath after Adding GGBS – 0C")

    temp_water_one1 = fields.Float("Temperature of water bath  after one hour when Flask kept in bath after Adding GGBS – 0C")
    temp_water_one2 = fields.Float("Temperature of water bath  after one hour when Flask kept in bath after Adding GGBS – 0C")


    final_kerosene1 = fields.Float("Final Level of Kerosene after one hour kept in water bath(B) – ml")
    final_kerosene2 = fields.Float("Final Level of Kerosene after one hour kept in water bath(B) – ml")

    displaced1 = fields.Float("Displaced Volume after Adding GGBS (V) = (B – A) – cm3",compute="_compute_values", store=True, digits=(12, 2))
    displaced2 = fields.Float("Displaced Volume after Adding GGBS (V) = (B – A) – cm3",compute="_compute_values", store=True, digits=(12, 2))

    density1 = fields.Float("Density of GGBS Sample – gms/ cm3",compute="_compute_values", store=True, digits=(12, 2))
    density2 = fields.Float("Density of GGBS Sample – gms/ cm3",compute="_compute_values", store=True, digits=(12, 2))

    average_density = fields.Float("Average Density of GGBS Sample – gms/ cm3",compute="_compute_avg_density")

    @api.depends(
        'initial_kerosene1', 'final_kerosene1',
        'initial_kerosene2', 'final_kerosene2',
        'mass1', 'mass2'
    )
    def _compute_values(self):
        for rec in self:
            # --- Displaced volume calculations ---
            rec.displaced1 = (rec.final_kerosene1 or 0.0) - (rec.initial_kerosene1 or 0.0)
            rec.displaced2 = (rec.final_kerosene2 or 0.0) - (rec.initial_kerosene2 or 0.0)

            # --- Density calculations ---
            rec.density1 = (rec.mass1 / rec.displaced1) if rec.displaced1 else 0.0
            rec.density2 = (rec.mass2 / rec.displaced2) if rec.displaced2 else 0.0

    @api.depends('density1', 'density2')
    def _compute_avg_density(self):
        for rec in self:
            # ensure no division by zero
            d1 = rec.density1 or 0.0
            d2 = rec.density2 or 0.0

            # compute average only if at least one density exists
            if d1 and d2:
                rec.average_density = (d1 + d2) / 2
            else:
                rec.average_density = 0.0




    specific_gravity_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
        
   

    ], string='Confirmity', default='fail',compute="_compute_specific_gravity_confirmity")
    specific_gravity_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_specific_gravity_nabl")


    @api.depends('average_density','eln_ref','grade')
    def _compute_specific_gravity_confirmity(self):
       
       for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.specific_gravity_confirmity = 'na'
                continue

            record.specific_gravity_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','210bgf54-baa4-466f-a6a7-044da708f265')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','210bgf54-baa4-466f-a6a7-044da708f265')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_density - record.average_density*mu_value
                    upper = record.average_density + record.average_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.specific_gravity_confirmity = 'pass'
                        break
                    else:
                        record.specific_gravity_confirmity = 'fail'
    
    @api.depends('average_density','eln_ref','grade')
    def _compute_specific_gravity_nabl(self):
        
        for record in self:
            record.specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','210bgf54-baa4-466f-a6a7-044da708f265')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','210bgf54-baa4-466f-a6a7-044da708f265')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_density - record.average_density*mu_value
                    upper = record.average_density + record.average_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.specific_gravity_nabl = 'pass'
                        break
                    else:
                        record.specific_gravity_nabl = 'fail'

   

    # Slag Activity Index

    slag_activity_name1 = fields.Char("Name",default="Slag Activity Index")

    slag_activity_name = fields.Char("Name",default="Compressive Strength of GGBS+Cement Mortar")
    slag_activity_7_visible = fields.Boolean("Slag Activity Visible",compute="_compute_visible")

    slag_index_ids = fields.One2many("ggbs.cement.motor.line", "parent_id", string="Test Readings")




    def action_calculate_avg_strength(self):
        for rec in self:
            lines = rec.slag_index_ids.sorted(key=lambda l: l.serial_no)  # serial_no ने sort करायचं
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


   

    

    slag_activity_cement_name = fields.Char("Name",default="Compressive Strength of Cement")
    slag_index_cement_ids = fields.One2many("ggbs.compressie.cement.line", "parent_id", string="Test Readings")

    def action_calculate_avg_cemet_strength(self):
        for rec in self:
            lines = rec.slag_index_cement_ids.sorted(key=lambda l: l.serial_no)  # serial_no ने sort करायचं
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

    

    
    average_strength1 = fields.Float(string="Average Compressive Strength in N/mm2",digits=(12,2),compute="_compute_average_strengths")
    average_strength2 = fields.Float(string="Average Compressive Strength in N/mm2",digits=(12,2),compute="_compute_average_strengths")

    sai1 = fields.Float(string="Slag Activity Index",digits=(12,2),compute="_compute_slag_activity_index")

    temp_7day = fields.Char("7 Days Temp.°C" ,required=True)
    humidity_7day= fields.Char("7 Days Humidity %" ,required=True)

    day_7_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
        
    ], string='7 Days Confirmity', default='fail',compute="_compute_day_7_confirmity")
    day_7_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='7 Days NABL', default='fail',compute="_compute_day_7_nabl")


    @api.depends('sai1','eln_ref','grade')
    def _compute_day_7_confirmity(self):
         for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.day_7_confirmity = 'na'
                continue

            record.day_7_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-321478658')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-321478658')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.sai1 - record.sai1*mu_value
                    upper = record.sai1 + record.sai1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.day_7_confirmity = 'pass'
                        break
                    else:
                        record.day_7_confirmity = 'fail'
    
    @api.depends('sai1','eln_ref','grade')
    def _compute_day_7_nabl(self):
        
        for record in self:
            record.day_7_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-321478658')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-321478658')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.sai1 - record.sai1*mu_value
                    upper = record.sai1 + record.sai1*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.day_7_nabl = 'pass'
                        break
                    else:
                        record.day_7_nabl = 'fail'

    sai2 = fields.Float(string="Slag Activity Index",digits=(12,2),compute="_compute_slag_activity_index")
    temp_28day = fields.Char("28 Days Temp.°C" ,required=True)
    humidity_28day= fields.Char("28 Days Humidity %" ,required=True)

    day_28_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
        
    ], string='28 Days Confirmity', default='fail',compute="_compute_day_28_confirmity")
    day_28_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='28 Days NABL', default='fail',compute="_compute_day_28_nabl")


    @api.depends('sai2','eln_ref','grade')
    def _compute_day_28_confirmity(self):
         for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.day_28_confirmity = 'na'
                continue


            record.day_28_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-3214855pp')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-3214855pp')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.sai2 - record.sai2*mu_value
                    upper = record.sai2 + record.sai2*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.day_28_confirmity = 'pass'
                        break
                    else:
                        record.day_28_confirmity = 'fail'
    
    @api.depends('sai2','eln_ref','grade')
    def _compute_day_28_nabl(self):
        
        for record in self:
            record.day_28_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-3214855pp')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-3214855pp')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.sai2 - record.sai2*mu_value
                    upper = record.sai2 + record.sai2*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.day_28_nabl = 'pass'
                        break
                    else:
                        record.day_28_nabl = 'fail'

  
    @api.depends('average_strength1', 'average_cement_strength1', 'average_strength2', 'average_cement_strength2')
    def _compute_slag_activity_index(self):
        for rec in self:
            rec.sai1 = 0.0
            rec.sai2 = 0.0

            if rec.average_cement_strength1:
                value1 = (rec.average_strength1 / rec.average_cement_strength1) * 100
                rec.sai1 = round(value1 + 1e-9)  # ensures normal 0.5 rounding

            if rec.average_cement_strength2:
                value2 = (rec.average_strength2 / rec.average_cement_strength2) * 100
                rec.sai2 = round(value2 + 1e-9)  # ensures normal 0.5 rounding


    @api.depends('slag_index_ids.avg_compressive_strength', 'slag_index_ids.serial_no')
    def _compute_average_strengths(self):
        for rec in self:
            rec.average_strength1 = 0.0
            rec.average_strength2 = 0.0

            # Sort lines by serial_no
            lines = rec.slag_index_ids.sorted(key=lambda l: l.serial_no)

            # If line 1 exists → average_strength1 = that line’s avg_compressive_strength
            if len(lines) >= 1 and lines[0].avg_compressive_strength:
                rec.average_strength1 = lines[0].avg_compressive_strength

            # If line 4 exists → average_strength2 = that line’s avg_compressive_strength
            if len(lines) >= 4 and lines[3].avg_compressive_strength:
                rec.average_strength2 = lines[3].avg_compressive_strength

    average_cement_strength1 = fields.Float(string="Average Compressive Strength in N/mm2",compute="_compute_average_cement_strengths",digits=(12,2))
    average_cement_strength2 = fields.Float(string="Average Compressive Strength in N/mm2",compute="_compute_average_cement_strengths",digits=(12,2))

    @api.depends('slag_index_cement_ids.avg_compressive_strength', 'slag_index_cement_ids.serial_no')
    def _compute_average_cement_strengths(self):
        for rec in self:
            rec.average_cement_strength1 = 0.0
            rec.average_cement_strength2 = 0.0

            # Sort lines by serial_no
            lines = rec.slag_index_cement_ids.sorted(key=lambda l: l.serial_no)

            # If line 1 exists → average_cement_strength1 = that line’s avg_compressive_strength
            if len(lines) >= 1 and lines[0].avg_compressive_strength:
                rec.average_cement_strength1 = lines[0].avg_compressive_strength

            # If line 4 exists → average_cement_strength2 = that line’s avg_compressive_strength
            if len(lines) >= 4 and lines[3].avg_compressive_strength:
                rec.average_cement_strength2 = lines[3].avg_compressive_strength

    
    # Fineness by Blaines 

    fineness_name = fields.Char("Name",default="Fineness by Blaines Air Permeability Method")
    fineness_visible = fields.Boolean("Fineness by Blaines Air Permeability Method Visible",compute="_compute_visible")

    temp_fineness = fields.Char("Temp.°C" ,required=True)
    humidity_fineness= fields.Char("Humidity %" ,required=True)

    density_cement = fields.Float(string="Density of Cement (g/cc)", digits=(12, 3))
    
    # Time Required for Manometer Drop (Seconds)
    first_bed_reading1 = fields.Float(string="First Bed Reading 1", digits=(12, 2))
    first_bed_reading2 = fields.Float(string="First Bed Reading 2", digits=(12, 2))
    second_bed_reading1 = fields.Float(string="Second Bed Reading 1", digits=(12, 2))
    second_bed_reading2 = fields.Float(string="Second Bed Reading 2", digits=(12, 2))

    avg_time_first = fields.Float(string="Average Time for Manometer Drop (First)",compute="_compute_avg_time_first", store=True, digits=(12, 2))

    @api.depends('first_bed_reading1', 'first_bed_reading2', 'second_bed_reading1', 'second_bed_reading2')
    def _compute_avg_time_first(self):
        for rec in self:
            rec.avg_time_first = (
                rec.first_bed_reading1 + rec.first_bed_reading2 + rec.second_bed_reading1 + rec.second_bed_reading2
            ) / 4 if any([
                rec.first_bed_reading1, rec.first_bed_reading2, rec.second_bed_reading1, rec.second_bed_reading2
            ]) else 0.0

    apparatus_constant_first = fields.Float(string="Apparatus Constant (K) ", digits=(12, 4))

    specific_surface_first = fields.Float(string="Specific Surface (First)",compute="_compute_specific_surface_first", store=True, digits=(12, 0))

   

    @api.depends('avg_time_first', 'apparatus_constant_first', 'density_cement')
    def _compute_specific_surface_first(self):
        for rec in self:
            if rec.avg_time_first and rec.apparatus_constant_first and rec.density_cement:
                value = (521.08 * rec.apparatus_constant_first * sqrt(rec.avg_time_first)) / rec.density_cement / 10
                # Round to nearest integer with ROUND_HALF_UP
                rec.specific_surface_first = int(Decimal(value).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            else:
                rec.specific_surface_first = 0

    
    
    fineness_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
        
    ],  string='Confirmity', default='fail',compute="_compute_fineness_confirmity")
    fineness_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_fineness_nabl")


    @api.depends('specific_surface_first','eln_ref','grade')
    def _compute_fineness_confirmity(self):
          
          for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.fineness_confirmity = 'na'
                continue

            record.fineness_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-6b0ff7e69c0a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-6b0ff7e69c0a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.specific_surface_first - record.specific_surface_first*mu_value
                    upper = record.specific_surface_first + record.specific_surface_first*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.fineness_confirmity = 'pass'
                        break
                    else:
                        record.fineness_confirmity = 'fail'
    
    @api.depends('specific_surface_first','eln_ref','grade')
    def _compute_fineness_nabl(self):
        
        for record in self:
            record.fineness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-6b0ff7e69c0a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5214hgtb-c526-4092-a3a7-6b0ff7e69c0a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.specific_surface_first - record.specific_surface_first*mu_value
                    upper = record.specific_surface_first + record.specific_surface_first*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.fineness_nabl = 'pass'
                        break
                    else:
                        record.fineness_nabl = 'fail'

   
    

    ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        

        for record in self:
            record.specific_gravity_visible = False
            record.slag_activity_7_visible = False

            record.fineness_visible = False

            
            
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                
                if sample.internal_id == '210bgf54-baa4-466f-a6a7-044da708f265':
                    record.specific_gravity_visible = True
                if sample.internal_id == '1452fgr0-8e67-4e94-86ea-98d9472f5c71':
                    record.slag_activity_7_visible = True
                if sample.internal_id == '5214hgtb-c526-4092-a3a7-6b0ff7e69c0a':
                    record.fineness_visible = True
               


    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
                   
                    if result.parameter.internal_id == '210bgf54-baa4-466f-a6a7-044da708f265':
                        result.result_char = self.average_density
                        if self.specific_gravity_nabl == 'pass':
                            result.nabl_status = 'nabl'
                        else:
                            result.nabl_status = 'non-nabl'
                        continue
                    if result.parameter.internal_id == '5214hgtb-c526-4092-a3a7-321478658':
                        result.result_char = self.sai1
                        if self.day_7_nabl == 'pass':
                            result.nabl_status = 'nabl'
                        else:
                            result.nabl_status = 'non-nabl'
                        continue

                    if result.parameter.internal_id == '5214hgtb-c526-4092-a3a7-3214855pp':
                        result.result_char = self.sai2
                        if self.day_28_nabl == 'pass':
                            result.nabl_status = 'nabl'
                        else:
                            result.nabl_status = 'non-nabl'
                        continue
                    if result.parameter.internal_id == '5214hgtb-c526-4092-a3a7-6b0ff7e69c0a':
                        result.result_char = self.specific_surface_first
                        if self.fineness_nabl == 'pass':
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
        record = super(GgbsMechanical, self).create(vals)
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



class GgbsCementMotorLine(models.Model):
    _name = "ggbs.cement.motor.line"

    parent_id = fields.Many2one('mechanical.ggbs')

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)


    lab_id = fields.Char("Lab Id")
    # testing_period = fields.Char("Testing Period")
    testing_period = fields.Selection([
        ('day7', '168±2 hr (7 Days)'),
        ('day28', '672±4 hr (28 Days)'),
        
    ], string='Testing Period')
    casting_details = fields.Date("Casting Details Date",compute="_compute_dt_of_casting")
    days = fields.Integer(string="No.of Days",store=True)
    testing_details = fields.Date("Testing Details Date",compute="_compute_dt_of_testing")
    cube_im = fields.Integer("Cube I/M")

    length1 = fields.Float("Length (L)")
    length2 = fields.Float("Length (L)")

    avg_length = fields.Float("Avg. Length (L)",compute="_compute_avg_length")

    @api.depends('length1', 'length2')
    def _compute_avg_length(self):
        for record in self:
            if record.length1 or record.length2:
                record.avg_length = (record.length1 + record.length2) / 2
            else:
                record.avg_length = 0.0

    width1 = fields.Float("Width")
    width2 = fields.Float("Width")

    avg_width = fields.Float("Avg. Width",compute="_compute_avg_width")

    @api.depends('width1', 'width2')
    def _compute_avg_width(self):
        for record in self:
            if record.width1 or record.width2:
                record.avg_width = (record.width1 + record.width2) / 2
            else:
                record.avg_width = 0.0

    height = fields.Float("Height (H)")

    load_failure = fields.Float("Load at Failure (P) kN")
    compressive_strength = fields.Float("Compressive Strength  MPa",compute="_compute_compressive_strength")
    avg_compressive_strength = fields.Float("Avg. Strength Mpa")


    @api.depends('load_failure', 'avg_length', 'avg_width')
    def _compute_compressive_strength(self):
        for record in self:
            if record.avg_length and record.avg_width:
                record.compressive_strength = round((record.load_failure * 1000) / (record.avg_length * record.avg_width), 1)
            else:
                record.compressive_strength = 0.0


    @api.depends('casting_details', 'parent_id')
    def _compute_testing_details(self):
        for rec in self:
            if rec.casting_details and rec.parent_id:
                # Find all lines of this parent ordered by ID (creation order)
                all_lines = self.search(
                    [('parent_id', '=', rec.parent_id.id)],
                    order='id asc'
                )
                # Get position (1-based index)
                position = all_lines.ids.index(rec.id) + 1 if rec.id in all_lines.ids else len(all_lines) + 1

                # Apply day rule
                if position <= 3:
                    rec.testing_details = rec.casting_details + timedelta(days=7)
                else:
                    rec.testing_details = rec.casting_details + timedelta(days=28)
            else:
                rec.testing_details = False

    @api.depends('parent_id.date_of_casting')
    def _compute_dt_of_casting(self):
        for record in self:
            record.casting_details = record.parent_id.date_of_casting

    @api.depends('casting_details', 'days')
    def _compute_dt_of_testing(self):
        for record in self:
            if record.casting_details and record.days:
                record.testing_details = record.casting_details + timedelta(days=record.days)
            else:
                record.testing_details = False

    

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(GgbsCementMotorLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in slag_index_ids
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class GgbsCementLine(models.Model):
    _name = "ggbs.compressie.cement.line"

    parent_id = fields.Many2one('mechanical.ggbs')

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)


    lab_id = fields.Char("Lab Id")
    # testing_period = fields.Char("Testing Period")
    testing_period = fields.Selection([
        ('day7', '168±2 hr (7 Days)'),
        ('day28', '672±4 hr (28 Days)'),
        
    ], string='Testing Period')
    casting_details = fields.Date("Casting Details Date",compute="_compute_dt_of_casting")
    days = fields.Integer(string="No.of Days",store=True)
    testing_details = fields.Date("Testing Details Date",compute="_compute_dt_of_testing")
    cube_im = fields.Integer("Cube I/M")

    length1 = fields.Float("Length (L)")
    length2 = fields.Float("Length (L)")

    avg_length = fields.Float("Avg. Length (L)",compute="_compute_avg_length")

   

    @api.depends('length1', 'length2')
    def _compute_avg_length(self):
        for record in self:
            if record.length1 or record.length2:
                record.avg_length = (record.length1 + record.length2) / 2
            else:
                record.avg_length = 0.0

    width1 = fields.Float("Width")
    width2 = fields.Float("Width")

    avg_width = fields.Float("Avg. Width",compute="_compute_avg_width")

    @api.depends('width1', 'width2')
    def _compute_avg_width(self):
        for record in self:
            if record.width1 or record.width2:
                record.avg_width = (record.width1 + record.width2) / 2
            else:
                record.avg_width = 0.0

    height = fields.Float("Height (H)")

    load_failure = fields.Float("Load at Failure (P) kN")
    compressive_strength = fields.Float("Compressive Strength  MPa",compute="_compute_compressive_strength")
    avg_compressive_strength = fields.Float("Avg. Strength Mpa")


    @api.depends('load_failure', 'avg_length', 'avg_width')
    def _compute_compressive_strength(self):
        for record in self:
            if record.avg_length and record.avg_width:
                record.compressive_strength = round((record.load_failure * 1000) / (record.avg_length * record.avg_width), 1)
            else:
                record.compressive_strength = 0.0


    # @api.depends('casting_details', 'parent_id')
    # def _compute_testing_details(self):
    #     for rec in self:
    #         if rec.casting_details and rec.parent_id:
    #             # Find all lines of this parent ordered by ID (creation order)
    #             all_lines = self.search(
    #                 [('parent_id', '=', rec.parent_id.id)],
    #                 order='id asc'
    #             )
    #             # Get position (1-based index)
    #             position = all_lines.ids.index(rec.id) + 1 if rec.id in all_lines.ids else len(all_lines) + 1

    #             # Apply day rule
    #             if position <= 3:
    #                 rec.testing_details = rec.casting_details + timedelta(days=7)
    #             else:
    #                 rec.testing_details = rec.casting_details + timedelta(days=28)
    #         else:
    #             rec.testing_details = False

    @api.depends('parent_id.date_of_casting')
    def _compute_dt_of_casting(self):
        for record in self:
            record.casting_details = record.parent_id.date_of_casting

    @api.depends('casting_details', 'days')
    def _compute_dt_of_testing(self):
        for record in self:
            if record.casting_details and record.days:
                record.testing_details = record.casting_details + timedelta(days=record.days)
            else:
                record.testing_details = False


    


    

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(GgbsCementLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in slag_index_ids
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class GGBSNotes(models.Model):
    _name = "ggbs.notes"

    parent_id = fields.Many2one('mechanical.ggbs',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")