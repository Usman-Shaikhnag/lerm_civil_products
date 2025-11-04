from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math
from statistics import mean
from math import sqrt
from decimal import Decimal, ROUND_HALF_UP


class PPCCementNormalConsistency(models.Model):
    _name = "cement.ppc"
    _inherit = "lerm.eln"
    _rec_name = "name"
    fineness_cement_name = fields.Char(string="Fineness Cement Name")

    name = fields.Char("Name",default="Cement")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")

    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id
    start_date = fields.Date(string="Start Date", compute="_compute_start_date", store=True)

    @api.depends('eln_ref.start_date')
    def _compute_start_date(self):
        for rec in self:
            rec.start_date = rec.eln_ref.start_date


  
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


   

        ## Density of Cement (Le-Chatlier Flask)

    density_cement_name = fields.Char("Name",default="Density of Cement (Le-Chatlier Flask)")
    density_cement_visible = fields.Boolean("Density of Cement (Le-Chatlier Flask) Visible",compute="_compute_visible")

    temp_specific = fields.Float("Temp.°C")
    humidity_specific= fields.Float("Humidity %")

    temp_water1 = fields.Float("Temperature of Water Bath  when Flask kept in bath – 0C")
    temp_water2 = fields.Float("Temperature of Water Bath  when Flask kept in bath – 0C")

    temp_water_after1 = fields.Float("Temperature of Water Bath  after One Hour when Flask kept in bath – 0C  ")
    temp_water_after2 = fields.Float("Temperature of Water Bath  after One Hour when Flask kept in bath – 0C  )")

    initial_kerosene1 = fields.Float("Initial Level of Kerosene after one hour kept in Water Bath(A) – ml")
    initial_kerosene2 = fields.Float("Initial Level of Kerosene after one hour kept in Water Bath(A) – ml")

    mass1 = fields.Float("Mass of Cement Sample Added in Flask (M) – gms")
    mass2 = fields.Float("Mass of Cement Sample Added in Flask (M) – gms")

    temp_water_flask1 = fields.Float("Temperature of water bath  when Flask kept in bath after Adding Cement – 0C")
    temp_water_flask2 = fields.Float("Temperature of water bath  when Flask kept in bath after Adding Cement – 0C")

    temp_water_one1 = fields.Float("Temperature of water bath  after one hour when Flask kept in bath after Adding Cement – 0C")
    temp_water_one2 = fields.Float("Temperature of water bath  after one hour when Flask kept in bath after Adding Cement – 0C")


    final_kerosene1 = fields.Float("Final Level of Kerosene after one hour kept in water bath(B) – ml")
    final_kerosene2 = fields.Float("Final Level of Kerosene after one hour kept in water bath(B) – ml")

    displaced1 = fields.Float("Displaced Volume after Adding Cement (V) = (B – A) – cm3", store=True, digits=(12, 2))
    displaced2 = fields.Float("Displaced Volume after Adding Cement (V) = (B – A) – cm3", store=True, digits=(12, 2))

    density1 = fields.Float("Density of Cement Sample (    ) – gms/ cm3", store=True, digits=(12, 2),compute="_compute_values")
    density2 = fields.Float("Density of Cement Sample (    ) – gms/ cm3", store=True, digits=(12, 2),compute="_compute_values")


    avg_density = fields.Float(string="Average Density of Cement Sample – gms/ cm3",compute="_compute_avg_density",store=True)

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
                rec.avg_density = (d1 + d2) / 2
            else:
                rec.avg_density = 0.0

    # specific_gravity = fields.Float(string="Specific Gravity of Cement",compute="_compute_cement_specific")

    avg_density_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_avg_density_conformity")

    avg_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_density_nabl")


    @api.depends('avg_density','eln_ref','grade')
    def _compute_avg_density_conformity(self):
        for record in self:
            record.avg_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be88a13b-8bc0-4d32-b8c0-43032c0cdd86')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be88a13b-8bc0-4d32-b8c0-43032c0cdd86')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_density - record.avg_density*mu_value
                    upper = record.avg_density + record.avg_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_density_conformity = 'pass'
                        break
                    else:
                        record.avg_density_conformity = 'fail'

    @api.depends('avg_density','eln_ref','grade')
    def _compute_avg_density_nabl(self):
        
        for record in self:
            record.avg_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be88a13b-8bc0-4d32-b8c0-43032c0cdd86')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','be88a13b-8bc0-4d32-b8c0-43032c0cdd86')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_density - record.avg_density*mu_value
            upper = record.avg_density + record.avg_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_density_nabl = 'pass'
                break
            else:
                record.avg_density_nabl = 'fail'

  


  
        ## Consistency of cement

    consistency_cement_name = fields.Char("Name",default="Consistency of cement")
    consistency_cement_visible = fields.Boolean("Consistency of cement Visible",compute="_compute_visible")

    temp_consistency = fields.Float("Temp.°C")
    humidity_consistency= fields.Float("Humidity %")

    consistency_cement_lines = fields.One2many('ppc.consistensy.cement.line','parent_id',string="Consistency")

    avg_consistency = fields.Float("Average consistency",compute="_compute_avg_consistency",store=True,digits=(12,4))

    @api.depends('consistency_cement_lines.water_mix')
    def _compute_avg_consistency(self):
        for rec in self:
            if rec.consistency_cement_lines:
                total = sum(line.water_mix for line in rec.consistency_cement_lines)
                count = len(rec.consistency_cement_lines)
                rec.avg_consistency = total / count if count else 0
            else:
                rec.avg_consistency = 0

    avg_consistency_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('not_applicable', 'Not Applicable'),
    ], string='Confirmity', default='fail',compute="_compute_avg_consistency_confirmity")
    avg_consistency_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_consistency_nabl")


    @api.depends('avg_consistency','eln_ref','grade')
    def _compute_avg_consistency_confirmity(self):
        for record in self:
            record.avg_consistency_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','64616a30-801e-40aa-abba-32dcd71b7c37')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','64616a30-801e-40aa-abba-32dcd71b7c37')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_consistency - record.avg_consistency*mu_value
                    upper = record.avg_consistency + record.avg_consistency*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_consistency_confirmity = 'pass'
                        break
                    else:
                        record.avg_consistency_confirmity = 'fail'
    
    @api.depends('avg_consistency','eln_ref','grade')
    def _compute_avg_consistency_nabl(self):
        
        for record in self:
            record.avg_consistency_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','64616a30-801e-40aa-abba-32dcd71b7c37')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','64616a30-801e-40aa-abba-32dcd71b7c37')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_consistency - record.avg_consistency*mu_value
                    upper = record.avg_consistency + record.avg_consistency*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_consistency_nabl = 'pass'
                        break
                    else:
                        record.avg_consistency_nabl = 'fail'

   


     ### setting Time,Final Setting Time	


    intial_time_lines = fields.One2many('ppc.initial.time.line','parent_id',string="Initial Time")


    initial_setting_time_visible = fields.Boolean("Setting Time Visible",compute="_compute_visible")
    initial_setting_time_name = fields.Char("Name",default="Setting Time")

  
    temp_time = fields.Float("Temp.°C")
    humidity_time= fields.Float("Humidity %")
    avg_initial_time = fields.Float("Average Intial Time",compute="_compute_avg_initial_time",store=True,digits=(12,4))

    @api.depends('intial_time_lines.initial')
    def _compute_avg_initial_time(self):
        for rec in self:
            if rec.intial_time_lines:
                total1 = sum(line.initial for line in rec.intial_time_lines)
                count = len(rec.intial_time_lines)
                rec.avg_initial_time = total1 / count if count else 0
            else:
                rec.avg_initial_time = 0

    temp_time_final = fields.Float("Temp.°C")
    humidity_time_final = fields.Float("Humidity %")

    avg_final_time = fields.Float("Average Final Time",compute="_compute_avg_final_time",store=True,digits=(12,4))

    @api.depends('intial_time_lines.final')
    def _compute_avg_final_time(self):
        for rec in self:
            if rec.intial_time_lines:
                total2 = sum(line.final for line in rec.intial_time_lines)
                count = len(rec.intial_time_lines)
                rec.avg_final_time = total2 / count if count else 0
            else:
                rec.avg_final_time = 0

    avg_initial_time_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('not_applicable', 'Not Applicable'),
    ], string='Initial Time Confirmity', default='fail',compute="_compute_avg_initial_time_confirmity")
    avg_initial_time_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Initial Time NABL', default='fail',compute="_compute_avg_initial_time_nabl")


    @api.depends('avg_initial_time','eln_ref','grade')
    def _compute_avg_initial_time_confirmity(self):
        for record in self:
            record.avg_initial_time_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d1fcbd33-f315-4290-a309-74acc90bc3f8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d1fcbd33-f315-4290-a309-74acc90bc3f8')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_initial_time - record.avg_initial_time*mu_value
                    upper = record.avg_initial_time + record.avg_initial_time*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_initial_time_confirmity = 'pass'
                        break
                    else:
                        record.avg_initial_time_confirmity = 'fail'
    
    @api.depends('avg_initial_time','eln_ref','grade')
    def _compute_avg_initial_time_nabl(self):
        
        for record in self:
            record.avg_initial_time_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d1fcbd33-f315-4290-a309-74acc90bc3f8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d1fcbd33-f315-4290-a309-74acc90bc3f8')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_initial_time - record.avg_initial_time*mu_value
                    upper = record.avg_initial_time + record.avg_initial_time*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_initial_time_nabl = 'pass'
                        break
                    else:
                        record.avg_initial_time_nabl = 'fail'

    avg_final_time_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('not_applicable', 'Not Applicable'),
    ], string='Final Time Confirmity', default='fail',compute="_compute_avg_final_time_confirmity")
    avg_final_time_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Final Time NABL', default='fail',compute="_compute_avg_final_time_nabl")


    @api.depends('avg_final_time','eln_ref','grade')
    def _compute_avg_final_time_confirmity(self):
        for record in self:
            record.avg_final_time_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e87e5708-bead-453a-90d5-4ec142545c52')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e87e5708-bead-453a-90d5-4ec142545c52')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_final_time - record.avg_final_time*mu_value
                    upper = record.avg_final_time + record.avg_final_time*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_final_time_confirmity = 'pass'
                        break
                    else:
                        record.avg_final_time_confirmity = 'fail'
    
    @api.depends('avg_final_time','eln_ref','grade')
    def _compute_avg_final_time_nabl(self):
        
        for record in self:
            record.avg_final_time_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e87e5708-bead-453a-90d5-4ec142545c52')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e87e5708-bead-453a-90d5-4ec142545c52')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_final_time - record.avg_final_time*mu_value
                    upper = record.avg_final_time + record.avg_final_time*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_final_time_nabl = 'pass'
                        break
                    else:
                        record.avg_final_time_nabl = 'fail'


    # Fineness by Blaines 

    fineness_name = fields.Char("Name",default="Fineness by Blaines Air Permeability Method")
    fineness_visible = fields.Boolean("Fineness by Blaines Air Permeability Method Visible",compute="_compute_visible")

    temp_fineness = fields.Float("Temp.°C")
    humidity_fineness= fields.Float("Humidity %")

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

    specific_surface_first = fields.Float(string="Specific Surface (First)",compute="_compute_specific_surface_first", store=True, digits=(12, 3))

  
   

    @api.depends('avg_time_first', 'apparatus_constant_first', 'density_cement')
    def _compute_specific_surface_first(self):
        for rec in self:
            if rec.avg_time_first and rec.apparatus_constant_first and rec.density_cement:
                value = (521.08 * rec.apparatus_constant_first * sqrt(rec.avg_time_first)) / rec.density_cement / 10
                rec.specific_surface_first = value  # No rounding
            else:
                rec.specific_surface_first = 0.0

    
    
    fineness_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('not_applicable', 'Not Applicable'),
    ], string='Confirmity', default='fail',compute="_compute_fineness_confirmity")
    fineness_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_fineness_nabl")


    @api.depends('specific_surface_first','eln_ref','grade')
    def _compute_fineness_confirmity(self):
        for record in self:
            record.fineness_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7797b1a6-d753-41ea-85f3-eaa37aebf08b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7797b1a6-d753-41ea-85f3-eaa37aebf08b')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7797b1a6-d753-41ea-85f3-eaa37aebf08b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7797b1a6-d753-41ea-85f3-eaa37aebf08b')]).parameter_table
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

    


   

                ## Cement Compressive Strength

    compressive_name = fields.Char("Name",default="Cement Compressive Strength")
    compressive_visible = fields.Boolean("Cement Compressive Strength Visible",compute="_compute_visible")

    ppc_compressive_ids = fields.One2many("mechanical.ppc.compressive.line", "parent_id", string="Test Readings")

    def action_calculate_avg_strength(self):
        for rec in self:
            lines = rec.ppc_compressive_ids.sorted(key=lambda l: l.serial_no)  # serial_no ने sort करायचं
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

    avg_3_days = fields.Float(string="Avg Strength (3 Days)", compute="_compute_avg_strengths", store=True)

    temp_3_days = fields.Float("Temp.°C")
    humidity_3_days= fields.Float("Humidity %")


    avg_3_days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_avg_3_days_conformity")

    avg_3_days_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_3_days_nabl")


    @api.depends('avg_3_days','eln_ref','grade')
    def _compute_avg_3_days_conformity(self):
        for record in self:
            record.avg_3_days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36905ff2-60e5-4e3f-a003-4f12cf03ebe9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36905ff2-60e5-4e3f-a003-4f12cf03ebe9')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_3_days - record.avg_3_days*mu_value
                    upper = record.avg_3_days + record.avg_3_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_3_days_conformity = 'pass'
                        break
                    else:
                        record.avg_3_days_conformity = 'fail'

    @api.depends('avg_3_days','eln_ref','grade')
    def _compute_avg_3_days_nabl(self):
        
        for record in self:
            record.avg_3_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36905ff2-60e5-4e3f-a003-4f12cf03ebe9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36905ff2-60e5-4e3f-a003-4f12cf03ebe9')]).parameter_table
            
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

    avg_7_days = fields.Float(string="Avg Strength (7 Days)", compute="_compute_avg_strengths", store=True)

    temp_7_days = fields.Float("Temp.°C")
    humidity_7_days= fields.Float("Humidity %")

    avg_7_days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_avg_7_days_conformity")

    avg_7_days_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_7_days_nabl")


    @api.depends('avg_7_days','eln_ref','grade')
    def _compute_avg_7_days_conformity(self):
        for record in self:
            record.avg_7_days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e2e1d8e6-d831-4b2b-8cb2-aa074dce7fc6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e2e1d8e6-d831-4b2b-8cb2-aa074dce7fc6')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_7_days - record.avg_7_days*mu_value
                    upper = record.avg_7_days + record.avg_7_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_7_days_conformity = 'pass'
                        break
                    else:
                        record.avg_7_days_conformity = 'fail'

    @api.depends('avg_7_days','eln_ref','grade')
    def _compute_avg_7_days_nabl(self):
        
        for record in self:
            record.avg_7_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e2e1d8e6-d831-4b2b-8cb2-aa074dce7fc6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e2e1d8e6-d831-4b2b-8cb2-aa074dce7fc6')]).parameter_table
            
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


    avg_28_days = fields.Float(string="Avg Strength (28 Days)", compute="_compute_avg_strengths", store=True)

    temp_28_days = fields.Float("Temp.°C")
    humidity_28_days= fields.Float("Humidity %")

    avg_28_days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_avg_28_days_conformity")

    avg_28_days_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_28_days_nabl")


    @api.depends('avg_28_days','eln_ref','grade')
    def _compute_avg_28_days_conformity(self):
        for record in self:
            record.avg_28_days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fd34def6-d5cf-47c5-87e2-72c7b59dd2c3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fd34def6-d5cf-47c5-87e2-72c7b59dd2c3')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_28_days - record.avg_28_days*mu_value
                    upper = record.avg_28_days + record.avg_28_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_28_days_conformity = 'pass'
                        break
                    else:
                        record.avg_28_days_conformity = 'fail'

    @api.depends('avg_28_days','eln_ref','grade')
    def _compute_avg_28_days_nabl(self):
        
        for record in self:
            record.avg_28_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fd34def6-d5cf-47c5-87e2-72c7b59dd2c3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fd34def6-d5cf-47c5-87e2-72c7b59dd2c3')]).parameter_table
            
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

    @api.depends('ppc_compressive_ids.days', 'ppc_compressive_ids.avg_compressive_strength')
    def _compute_avg_strengths(self):
        for rec in self:
            strengths_3 = [line.avg_compressive_strength for line in rec.ppc_compressive_ids if line.days == 3 and line.avg_compressive_strength]
            strengths_7 = [line.avg_compressive_strength for line in rec.ppc_compressive_ids if line.days == 7 and line.avg_compressive_strength]
            strengths_28 = [line.avg_compressive_strength for line in rec.ppc_compressive_ids if line.days == 28 and line.avg_compressive_strength]

            rec.avg_3_days = mean(strengths_3) if strengths_3 else 0.0
            rec.avg_7_days = mean(strengths_7) if strengths_7 else 0.0
            rec.avg_28_days = mean(strengths_28) if strengths_28 else 0.0

      ## Soundness by Autoclave Test

    soundness_autoclave_name = fields.Char("Name",default="Soundness by Autoclave Test")
    soundness_autoclave_visible = fields.Boolean("Soundness by Autoclave Test Visible",compute="_compute_visible")

    temp_soundness_autoclave = fields.Float("Temp.°C")
    humidity_soundness_autoclave= fields.Float("Humidity %")

    ppc_autoclave_ids = fields.One2many("mechanical.ppc.autoclave.line", "parent_id", string="Test Readings")

    avg_expantion = fields.Float("Average Expansion %",compute="_compute_avg_expansion",store=True,digits=(12,4))

    @api.depends('ppc_autoclave_ids.autoclave')
    def _compute_avg_expansion(self):
        for rec in self:
            if rec.ppc_autoclave_ids:
                total = sum(line.autoclave for line in rec.ppc_autoclave_ids)
                count = len(rec.ppc_autoclave_ids)
                rec.avg_expantion = total / count if count else 0
            else:
                rec.avg_expantion = 0


    avg_expantion_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_avg_expantion_conformity")

    avg_expantion_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_expantion_nabl")


    @api.depends('avg_expantion','eln_ref','grade')
    def _compute_avg_expantion_conformity(self):
        for record in self:
            record.avg_expantion_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf78dd87-02e2-4c6d-9463-a04f434d25c6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf78dd87-02e2-4c6d-9463-a04f434d25c6')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_expantion - record.avg_expantion*mu_value
                    upper = record.avg_expantion + record.avg_expantion*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_expantion_conformity = 'pass'
                        break
                    else:
                        record.avg_expantion_conformity = 'fail'

    @api.depends('avg_expantion','eln_ref','grade')
    def _compute_avg_expantion_nabl(self):
        
        for record in self:
            record.avg_expantion_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf78dd87-02e2-4c6d-9463-a04f434d25c6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bf78dd87-02e2-4c6d-9463-a04f434d25c6')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_expantion - record.avg_expantion*mu_value
            upper = record.avg_expantion + record.avg_expantion*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_expantion_nabl = 'pass'
                break
            else:
                record.avg_expantion_nabl = 'fail'

    #  Soundness of Cement By Le-Chattelier Method
    soundness_le_method_name = fields.Char("Name",default="Soundness of Cement By Le-Chattelier Method")
    soundness_le_method_visible = fields.Boolean("Soundness of Cement By Le-Chattelier Method Visible",compute="_compute_visible")

    temp_soundness_le_method = fields.Float("Temp.°C")
    humidity_soundness_le_method= fields.Float("Humidity %")

    ppc_le_method_ids = fields.One2many("mechanical.ppc.lemethod.line", "parent_id", string="Test Readings")

    avg_expantion1 = fields.Float("Average Expansion %",compute="_compute_avg_expansion1",store=True,digits=(12,4))

    @api.depends('ppc_le_method_ids.avg_expansion')
    def _compute_avg_expansion1(self):
        for rec in self:
            if rec.ppc_le_method_ids:
                total = sum(line.avg_expansion for line in rec.ppc_le_method_ids)
                count = len(rec.ppc_le_method_ids)
                rec.avg_expantion1 = total / count if count else 0
            else:
                rec.avg_expantion1 = 0

    def action_calculate_avg_expansion(self):
        for rec in self:
            lines = rec.ppc_le_method_ids.sorted(key=lambda l: l.serial_no)  # serial_no ने sort करायचं
            group_size = 2

            for i in range(0, len(lines), group_size):
                group = lines[i:i + group_size]
                strength = [l.expansion for l in group if l.expansion > 0]
                avg = sum(strength) / len(strength) if strength else 0.0

                if group:
                    group[0].avg_expansion = avg

            for line in lines:
                if line not in [lines[i] for i in range(0, len(lines), group_size)]:
                    line.avg_expansion = 0.0

    avg_expantion1_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_avg_expantion1_conformity")

    avg_expantion1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_expantion1_nabl")


    @api.depends('avg_expantion1','eln_ref','grade')
    def _compute_avg_expantion1_conformity(self):
        for record in self:
            record.avg_expantion1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d72cba69-a44e-406a-b621-8344c3716275')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d72cba69-a44e-406a-b621-8344c3716275')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_expantion1 - record.avg_expantion1*mu_value
                    upper = record.avg_expantion1 + record.avg_expantion1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_expantion1_conformity = 'pass'
                        break
                    else:
                        record.avg_expantion1_conformity = 'fail'

    @api.depends('avg_expantion1','eln_ref','grade')
    def _compute_avg_expantion1_nabl(self):
        
        for record in self:
            record.avg_expantion1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d72cba69-a44e-406a-b621-8344c3716275')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d72cba69-a44e-406a-b621-8344c3716275')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_expantion1 - record.avg_expantion1*mu_value
            upper = record.avg_expantion1 + record.avg_expantion1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_expantion1_nabl = 'pass'
                break
            else:
                record.avg_expantion1_nabl = 'fail'



   
      

            
    ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:


            record.density_cement_visible = False
            record.consistency_cement_visible = False
            record.initial_setting_time_visible = False
            record.fineness_visible = False
            record.compressive_visible = False
            record.soundness_autoclave_visible = False
            record.soundness_le_method_visible = False
         
            

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == 'be88a13b-8bc0-4d32-b8c0-43032c0cdd86':
                    record.density_cement_visible = True

            
                if sample.internal_id == '64616a30-801e-40aa-abba-32dcd71b7c37':
                    record.consistency_cement_visible = True





                if sample.internal_id == '08c223af-a906-47c5-a15c-176ff5c9332d':
                    record.initial_setting_time_visible = True





                if sample.internal_id == '7797b1a6-d753-41ea-85f3-eaa37aebf08b':
                    record.fineness_visible = True





                if sample.internal_id == '99d735e6-2076-4770-b5e1-f5b8399e5a27':
                    record.compressive_visible = True




                if sample.internal_id == 'bf78dd87-02e2-4c6d-9463-a04f434d25c6':
                    record.soundness_autoclave_visible = True

                if sample.internal_id == 'd72cba69-a44e-406a-b621-8344c3716275':
                    record.soundness_le_method_visible = True

               

             
             

    def open_eln_page(self):
    # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
         
            if result.parameter.internal_id == '254gt2547-372f-4775-9bcb-e9dd70e3587g':
                result.result_char = round(self.avg_density,2)
                if self.avg_density_nabl == 'pass':
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
      
        record = super(PPCCementNormalConsistency, self).create(vals)
        record.eln_ref.write({'model_id':record.id})
        return record

   
    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
     
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['cement.ppc'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value
        return field_values








class PPCConsistencyCementLine(models.Model):
    _name = "ppc.consistensy.cement.line"
    parent_id = fields.Many2one('cement.ppc',string="Parent Id")

    serial_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    lab_id = fields.Char(string="Lab ID ")

    # trial_no = fields.Integer(string="Trial No.")

   
    
    mass_of_cement = fields.Float(string="Mass of Cement Taken gms.")
    water_added = fields.Float(string="Water Added ml")
    water_mix = fields.Float(string="% Water",compute="_compute_water_mix",store=True)
    needle_penitration = fields.Float(string="Penetration from Bottom of Mould mm")

    @api.depends('mass_of_cement', 'water_added')
    def _compute_water_mix(self):
        for rec in self:
            if rec.mass_of_cement:
                rec.water_mix = (rec.water_added / rec.mass_of_cement) * 100
            else:
                rec.water_mix = 0.0


    

   


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PPCConsistencyCementLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1






class PPCInitialTimeLine(models.Model):
    _name = "ppc.initial.time.line"
    parent_id = fields.Many2one('cement.ppc',string="Parent Id")

    serial_no = fields.Integer(string="Sr.No", readonly=True, copy=False, default=1)

    lab_id = fields.Char(string="LAB ID")

   
    
    time_water_t1 = fields.Datetime(string="Time at which water is first added to cement, t1, mins")
    time_needle_t2 = fields.Datetime(string="Time when needle fails to penetrate 5 +/-0.5 mm from bottom of the mould, t2 ,mins")
    time_needle_t3 = fields.Datetime(string="Time when the needle makes an impression but the attachment fails to do so, t3, mins")
    initial = fields.Float(string="Initial setting time, min (t2-t1)",compute="_compute_setting_times",store=True)
    final = fields.Float(string="Final setting time, min (t3-t1)",compute="_compute_setting_times",store=True)


    @api.depends('time_water_t1', 'time_needle_t2', 'time_needle_t3')
    def _compute_setting_times(self):
        for rec in self:
            rec.initial = 0.0
            rec.final = 0.0
            if rec.time_water_t1 and rec.time_needle_t2:
                t1 = rec.time_water_t1
                t2 = rec.time_needle_t2
                # Handle midnight crossover
                if t1 > t2:
                    t2 = t2.replace(day=t2.day + 1)
                rec.initial = (t2 - t1).total_seconds() / 60  # Convert seconds to minutes

            if rec.time_water_t1 and rec.time_needle_t3:
                t1 = rec.time_water_t1
                t3 = rec.time_needle_t3
                # Handle midnight crossover
                if t1 > t3:
                    t3 = t3.replace(day=t3.day + 1)
                rec.final = (t3 - t1).total_seconds() / 60

    


    

   


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PPCInitialTimeLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class PPCCementCompressiveLine(models.Model):
    _name = "mechanical.ppc.compressive.line"

    parent_id = fields.Many2one('cement.ppc')

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)


    lab_id = fields.Char("Lab Id")
    testing_period = fields.Char("Testing Period")
    casting_details = fields.Date("Casting Details Date",compute="_compute_dt_of_casting")
    days = fields.Integer(string="No.of Days",store=True)
    testing_details = fields.Date("Testing Details Date",compute="_compute_dt_of_testing")
    cube_im = fields.Integer("Cube I/M")

    length1 = fields.Float("Length (L)")
    
    width1 = fields.Float("Width")
   

   

    load_failure = fields.Float("Load at Failure (P) kN")
    compressive_strength = fields.Float("Compressive Strength  MPa",compute="_compute_compressive_strength",store=True,digits=(12,1))
    avg_compressive_strength = fields.Float("Avg. Strength Mpa",digits=(12,1))

    @api.depends('load_failure', 'length1', 'width1')
    def _compute_compressive_strength(self):
        for rec in self:
            if rec.load_failure and rec.length1 and rec.width1:
                rec.compressive_strength = round((rec.load_failure * 1000) / (rec.length1 * rec.width1), 1)
            else:
                rec.compressive_strength = 0


    


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

        return super(PPCCementCompressiveLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in ppc_compressive_ids
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class PPCSoundnessAutocalveLine(models.Model):
    _name = "mechanical.ppc.autoclave.line"

    parent_id = fields.Many2one('cement.ppc')

    serial_no = fields.Integer(string="Mould No",readonly=True, copy=False, default=1)


    # mould_no = fields.Integer("Mould No")
    intial_ref = fields.Float("Initial Reference Bar Reading (R1)",digits=(12,3))
    initial_reading = fields.Float("Initial Reading (Ri)",digits=(12,3))
    intial_a = fields.Float(string="Initial A (Ri – R1)" ,compute="_compute_values",store=True,digits=(12,3))
    final_ref = fields.Float("Final Reference Bar Reading (R2)",digits=(12,3))
    final_reading = fields.Float("Final Reading (Rf)",digits=(12,3))

    final_b = fields.Float("Final B (Rf – R2)",compute="_compute_values",store=True,digits=(12,3))
    
    autoclave = fields.Float("Autoclave Expansion (B-A)/250 x 100 %",compute="_compute_values",store=True,digits=(12,4))

    @api.depends('intial_ref', 'initial_reading', 'final_ref', 'final_reading')
    def _compute_values(self):
        for rec in self:
            rec.intial_a = (rec.initial_reading or 0) - (rec.intial_ref or 0)
            rec.final_b = (rec.final_reading or 0) - (rec.final_ref or 0)
            rec.autoclave = ((rec.final_b - rec.intial_a) / 250) * 100 if rec.final_b and rec.intial_a else 0
  
   
   

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PPCSoundnessAutocalveLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in ppc_compressive_ids
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class PPCSoundnessLeMethodLine(models.Model):
    _name = "mechanical.ppc.lemethod.line"

    parent_id = fields.Many2one('cement.ppc')

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)


    lab_id = fields.Char("Lab ID No.")
    mould_no = fields.Char("Mould No")
    intial_ref = fields.Float("Initial Reading of Indicator Point Before Boiling (A) in mm)",digits=(12,3))
    final_reading = fields.Float("Final Reading of Indicator Point After 3 Hrs. Boiling (B) in mm",digits=(12,3))
    expansion = fields.Float(string="Expansion (B – A) mm" ,compute="_compute_values",store=True,digits=(12,3))

    avg_expansion = fields.Float(string="Average Expansion mm" ,digits=(12,2))

    @api.depends('intial_ref', 'final_reading')
    def _compute_values(self):
        for rec in self:
            rec.expansion = (rec.final_reading or 0) - (rec.intial_ref or 0)


   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PPCSoundnessLeMethodLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in ppc_compressive_ids
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

