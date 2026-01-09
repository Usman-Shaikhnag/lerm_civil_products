from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math
from statistics import mean
from decimal import Decimal, ROUND_HALF_UP





class FlyaschNormalConsistency(models.Model):
    _name = "mechanical.flyasch.normalconsistency"
    _inherit = "lerm.eln"
    _description = 'mechanical.flyasch.normalconsistency'
    _rec_name = "name_fly"


    name_fly = fields.Char("Name",default="Fly Ash")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")

    notes_id = fields.One2many('flyash.notes','parent_id',string="Notes")

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

    lab_fly_ash_ids = fields.One2many(
        'fly.ash.lab.line', 
        'parent_id', 
        string="Generated Options"
    )



    def action_generate_options_fly_ash(self):
        for record in self:
            # Step 1: Check if lab_id exists and has hyphen
            if record.lab_id and '-' in record.lab_id:
                try:
                    # Step 2: Clear old lines first
                    lines_command = [(5, 0, 0)]
                    
                    # Step 3: String Parsing
                    parts = record.lab_id.split(' - ')
                    
                    if len(parts) >= 2:
                        start_part = parts[0].strip() # Example: "S-25-001"
                        end_part = parts[-1].strip()  # Example: "S-25-006"

                        prefix = start_part.rsplit('-', 1)[0]
                        
                        # --- CHANGE START ---
                        # Number cha string part vegla kara length check karnya sathi
                        start_num_str = start_part.split('-')[-1] # "001" milnar
                        end_num_str = end_part.split('-')[-1]     # "006" milnar
                        
                        # Length calculate kara (Example: "001" chi length 3 ahe)
                        padding_length = len(start_num_str)

                        start_num = int(start_num_str) # Integer madhe convert: 1
                        end_num = int(end_num_str)     # Integer madhe convert: 6
                        # --- CHANGE END ---

                        # Step 4: Loop ani Create Lines
                        for num in range(start_num, end_num + 1):
                            # zfill use karun zero add kara
                            # Jar num=1 ahe ani padding_length=3 ahe, tar "001" banel
                            formatted_num = str(num).zfill(padding_length)
                            
                            val = f"{prefix}-{formatted_num}"
                            lines_command.append((0, 0, {'lab': val}))

                        # Step 5: Assign to One2many field
                        record.lab_fly_ash_ids = lines_command
                        
                except Exception as e:
                    pass
            else:
                if record.lab_id:
                    record.lab_fly_ash_ids = [(5, 0, 0), (0, 0, {'lab': record.lab_id})]


   

    calc_mode = fields.Boolean(default=True)     
    submit_mode = fields.Boolean(default=False)


    @api.model
    def default_get(self, fields):
        res = super(FlyaschNormalConsistency, self).default_get(fields)

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
            'res_model': 'flyash.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }


    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None

    


     ## Normal Consistency

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    normal_consistency_name = fields.Char("Name",default="Consistency - %")
    normal_consistency_visible = fields.Boolean("Normal Consistency Visible",compute="_compute_visible")

    selected_lab_normal_consistency1 = fields.Many2one(
        'fly.ash.lab.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_fly_ash_ids)]"
    )

    is_lab_normal_consistency = fields.Boolean(
        string="Lab Fine Selected",
    )

    @api.onchange('selected_lab_normal_consistency1')
    def _onchange_selected_lab_normal_consistency1(self):
        for rec in self:
            if rec.selected_lab_normal_consistency1:
                rec.is_lab_normal_consistency = True
            else:
                rec.is_lab_normal_consistency = False


    temp_percent_consistency = fields.Char("Temp °c" )
    humidity_percent_consistency = fields.Char("Humidity %" )

    consistency_child_lines = fields.One2many('consistency.line','parent_id' ,string="Parameter")


    consistency_percent = fields.Float(
    string="Consistency (%)", compute="_compute_consistency_percent", store=True, digits=(12, 2))

    @api.depends('consistency_child_lines.water_percent')
    def _compute_consistency_percent(self):
     for rec in self:
        water_values = [line.water_percent for line in rec.consistency_child_lines if line.water_percent]
        rec.consistency_percent = sum(water_values) / len(water_values) if water_values else 0.0


    normal_consistency_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_normal_consistency_conformity", store=True)

    @api.depends('consistency_percent','eln_ref','grade')
    def _compute_normal_consistency_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.normal_consistency_conformity = 'na'
                continue
            record.normal_consistency_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','124fgrt3-1b3c-43ae-9c20-5421b6d6edf9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','124fgrt3-1b3c-43ae-9c20-5421b6d6edf9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.consistency_percent - record.consistency_percent*mu_value
                    upper = record.consistency_percent + record.consistency_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.normal_consistency_conformity = 'pass'
                        break
                    else:
                        record.normal_consistency_conformity = 'fail'

    normal_consistency_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_normal_consistency_nabl", store=True)

    @api.depends('consistency_percent','eln_ref','grade')
    def _compute_normal_consistency_nabl(self):
        
        for record in self:
            record.normal_consistency_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','124fgrt3-1b3c-43ae-9c20-5421b6d6edf9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','124fgrt3-1b3c-43ae-9c20-5421b6d6edf9')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.consistency_percent - record.consistency_percent*mu_value
            upper = record.consistency_percent + record.consistency_percent*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.normal_consistency_nabl = 'pass'
                break
            else:
                record.normal_consistency_nabl = 'fail'





    # Setting Time

    


    initial_setting_time_visible = fields.Boolean("Setting Time Visible",compute="_compute_visible")
    initial_setting_time_name = fields.Char("Name",default="Setting Time")

    selected_lab_setting_time1 = fields.Many2one(
        'fly.ash.lab.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_fly_ash_ids)]"
    )

    is_lab_setting_time = fields.Boolean(
        string="Lab Fine Selected",
    )

    @api.onchange('selected_lab_setting_time1')
    def _onchange_selected_lab_setting_time1(self):
        for rec in self:
            if rec.selected_lab_setting_time1:
                rec.is_lab_setting_time = True
            else:
                rec.is_lab_setting_time = False

    final_setting_time_visible = fields.Boolean("Setting Time Visible",compute="_compute_visible")
    final_setting_time_name = fields.Char("Name",default="Setting Time")


    temp_setting_time = fields.Char("Temp °c" )
    humidity_setting_time = fields.Char("Humidity %" )

    intial_time_lines = fields.One2many('setting.time.line','parent_id',string="Initial Time")

    initial_time_set = fields.Float('Average Initial Setting Time',compute="_compute_initial_time_set")

    final_time_set = fields.Float('Average Final Setting Time',compute="_compute_final_time_set")


    @api.depends('intial_time_lines.initial_setting')
    def _compute_initial_time_set(self):
        for record in self:
            if record.intial_time_lines:
              record.initial_time_set = sum(record.intial_time_lines.mapped('initial_setting'))/ len(record.intial_time_lines)
            else:
                record.initial_time_set = 0.0

    @api.depends('intial_time_lines.final_setting')
    def _compute_final_time_set(self):
        for record in self:
            if record.intial_time_lines:
              record.final_time_set = sum(record.intial_time_lines.mapped('final_setting'))/ len(record.intial_time_lines)
            else:
                record.final_time_set = 0.0

  


    # Soundness By Le-Chatelier Test

    soundness_visible = fields.Boolean("Soundness By Le-Chatelier Test",compute="_compute_visible")
    soundness_name = fields.Char("Name",default="Soundness By Le-Chatelier Test")

    selected_lab_soundness1 = fields.Many2one(
        'fly.ash.lab.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_fly_ash_ids)]"
    )

    is_lab_soundness = fields.Boolean(
        string="Lab Fine Selected",
    )

    @api.onchange('selected_lab_soundness1')
    def _onchange_selected_lab_soundness1(self):
        for rec in self:
            if rec.selected_lab_soundness1:
                rec.is_lab_soundness = True
            else:
                rec.is_lab_soundness = False


    temp_soundness = fields.Char("Temp °c" )
    humidity_soundness = fields.Char("Humidity %" )

    soundness_child_lines = fields.One2many('soundness.le.chatelier.line','parent_id',string="Soundness By Le-Chatelier Test")

    avg_expansion = fields.Float('Average Expansion (mm)',compute="_compute_avg_expansion")


    @api.depends('soundness_child_lines.expansion')
    def _compute_avg_expansion(self):
        for record in self:
            if record.soundness_child_lines:
              record.avg_expansion = round(sum(record.soundness_child_lines.mapped('expansion'))/ len(record.soundness_child_lines),1)
            else:
                record.avg_expansion = 0.0


    avg_expansion_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_avg_expansion_conformity", store=True)

    @api.depends('avg_expansion','eln_ref','grade')
    def _compute_avg_expansion_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_expansion_conformity = 'na'
                continue
            record.avg_expansion_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210ght7-91b0-4153-87ef-11b6954a9837')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210ght7-91b0-4153-87ef-11b6954a9837')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_expansion - record.avg_expansion*mu_value
                    upper = record.avg_expansion + record.avg_expansion*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_expansion_conformity = 'pass'
                        break
                    else:
                        record.avg_expansion_conformity = 'fail'

    avg_expansion_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_expansion_nabl", store=True)

    @api.depends('avg_expansion','eln_ref','grade')
    def _compute_avg_expansion_nabl(self):
        
        for record in self:
            record.avg_expansion_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210ght7-91b0-4153-87ef-11b6954a9837')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3210ght7-91b0-4153-87ef-11b6954a9837')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_expansion - record.avg_expansion*mu_value
                    upper = record.avg_expansion + record.avg_expansion*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_expansion_nabl = 'pass'
                        break
                    else:
                        record.avg_expansion_nabl = 'fail'

    # Soundness By AutoClave Test

    sound_auto_visible = fields.Boolean("Soundness By AutoClave Test",compute="_compute_visible")
    sound_auto_name = fields.Char("Name",default="Soundness By AutoClave Test")

    selected_lab_sound_auto1 = fields.Many2one(
        'fly.ash.lab.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_fly_ash_ids)]"
    )

    is_lab_sound_auto = fields.Boolean(
        string="Lab Fine Selected",
    )

    @api.onchange('selected_lab_sound_auto1')
    def _onchange_selected_lab_sound_auto1(self):
        for rec in self:
            if rec.selected_lab_sound_auto1:
                rec.is_lab_sound_auto = True
            else:
                rec.is_lab_sound_auto = False


    temp_sound_auto = fields.Char("Temp °c" )
    humidity_sound_auto = fields.Char("Humidity %" )

    sound_auto_child_lines = fields.One2many('soundness.autoclave.line','parent_id',string="AutoClave Test")

    avg_autoclave_expansion = fields.Float('Average Expansion %',compute="_compute_avg_autoclave_expansion")


    @api.depends('sound_auto_child_lines.autoclave_expansion')
    def _compute_avg_autoclave_expansion(self):
        for record in self:
            if record.sound_auto_child_lines:
              record.avg_autoclave_expansion = sum(record.sound_auto_child_lines.mapped('autoclave_expansion'))/ len(record.sound_auto_child_lines)
            else:
                record.avg_autoclave_expansion = 0.0






    avg_autoclave_expansion_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_avg_autoclave_expansion_conformity", store=True)

    @api.depends('avg_autoclave_expansion','eln_ref','grade')
    def _compute_avg_autoclave_expansion_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_autoclave_expansion_conformity = 'na'
                continue
            record.avg_autoclave_expansion_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b0e2437d-514b-4875-9f3a-203d5fad1d83')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b0e2437d-514b-4875-9f3a-203d5fad1d83')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_autoclave_expansion - record.avg_autoclave_expansion*mu_value
                    upper = record.avg_autoclave_expansion + record.avg_autoclave_expansion*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_autoclave_expansion_conformity = 'pass'
                        break
                    else:
                        record.avg_autoclave_expansion_conformity = 'fail'

    avg_autoclave_expansion_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_autoclave_expansion_nabl", store=True)

    @api.depends('avg_autoclave_expansion','eln_ref','grade')
    def _compute_avg_autoclave_expansion_nabl(self):
        
        for record in self:
            record.avg_autoclave_expansion_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b0e2437d-514b-4875-9f3a-203d5fad1d83')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b0e2437d-514b-4875-9f3a-203d5fad1d83')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_autoclave_expansion - record.avg_autoclave_expansion*mu_value
                    upper = record.avg_autoclave_expansion + record.avg_autoclave_expansion*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_autoclave_expansion_nabl = 'pass'
                        break
                    else:
                        record.avg_autoclave_expansion_nabl = 'fail'





    
       
    # Specific Gravity Test

    specific_gravity_name = fields.Char("Name",default="Specific Gravity Test")
    specific_gravity_visible = fields.Boolean("Specific Gravity Test",compute="_compute_visible")

    selected_lab_specific_gravity1 = fields.Many2one(
        'fly.ash.lab.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_fly_ash_ids)]"
    )

    is_lab_specific_gravity = fields.Boolean(
        string="Lab Fine Selected",
    )

    @api.onchange('selected_lab_specific_gravity1')
    def _onchange_selected_lab_specific_gravity1(self):
        for rec in self:
            if rec.selected_lab_specific_gravity1:
                rec.is_lab_specific_gravity = True
            else:
                rec.is_lab_specific_gravity = False
       
    temp_specific_gravity = fields.Char("Temp °c" )
    humidity_specific_gravity = fields.Char("Humidity %" )  

    temp_water_1 = fields.Float("Temperature of Water Bath  when Flask kept in bath – 0°C")
    temp_water_2 = fields.Float("Temperature of Water Bath  when Flask kept in bath – 0°C")

    temp_water_after_1 = fields.Float("Temperature of Water Bath  after One Hour when Flask kept in bath – 0°C")
    temp_water_after_2 = fields.Float("Temperature of Water Bath  after One Hour when Flask kept in bath – 0°C")

    initial_kerosene_1 = fields.Float("Initial Level of Kerosene after one hour kept in Water Bath(A) – ml")
    initial_kerosene_2 = fields.Float("Initial Level of Kerosene after one hour kept in Water Bath(A) – ml")

    mass_flyash_1 = fields.Float("Mass of Flyash Sample Added in Flask (M) – gms")
    mass_flyash_2 = fields.Float("Mass of Flyash Sample Added in Flask (M) – gms")

    temp_waterflask_1 = fields.Float("Temperature of water bath  when Flask kept in bath after Adding Flyash – 0°C")
    temp_waterflask_2 = fields.Float("Temperature of water bath  when Flask kept in bath after Adding Flyash – 0°C")

    temp_waterflask_after_1 = fields.Float("Temperature of water bath  after one hour when Flask kept in bath after Adding Flyash – 0°C")
    temp_waterflask_after_2 = fields.Float("Temperature of water bath  after one hour when Flask kept in bath after Adding Flyash – 0°C")

    final_kerosene_1 = fields.Float("Final Level of Kerosene after one hour kept in water bath(B) – ml")
    final_kerosene_2 = fields.Float("Final Level of Kerosene after one hour kept in water bath(B) – ml")

    displaced_vol_1 = fields.Float("Displaced Volume after Adding Flyash (V) = (B – A) – cm3", store=True, digits=(12, 1),compute="_compute_values")
    displaced_vol_2 = fields.Float("Displaced Volume after Adding Flyash (V) = (B – A) – cm3", store=True, digits=(12, 1),compute="_compute_values")

    density_fly_l = fields.Float("Density of Flyash Sample (    ) – gms/ cm3", store=True, digits=(12, 2),compute="_compute_values")
    density_fly_2 = fields.Float("Density of Flyash Sample (    ) – gms/ cm3", store=True, digits=(12, 2),compute="_compute_values")

										


    @api.depends('initial_kerosene_1','final_kerosene_1','mass_flyash_1','initial_kerosene_2','final_kerosene_2','mass_flyash_2')
    def _compute_values(self):
        for rec in self:
            # --- Displaced volume calculations ---
            rec.displaced_vol_1 = (rec.final_kerosene_1 or 0.0) - (rec.initial_kerosene_1 or 0.0)
            rec.displaced_vol_2 = (rec.final_kerosene_2 or 0.0) - (rec.initial_kerosene_2 or 0.0)

            # --- Density calculations ---
            rec.density_fly_l = (rec.mass_flyash_1 / rec.displaced_vol_1) if rec.displaced_vol_1 else 0.0
            rec.density_fly_2 = (rec.mass_flyash_2 / rec.displaced_vol_2) if rec.displaced_vol_2 else 0.0

    										


    avg_density_fly = fields.Float("Average Density of Flyash Sample – gms/ cm3", store=True, digits=(12, 2),compute="_compute_avg_density_fly")



    @api.depends('density_fly_l', 'density_fly_2')
    def _compute_avg_density_fly(self):
     for rec in self:
        d1 = rec.density_fly_l
        d2 = rec.density_fly_2
        def truncate(f, n):
         s = str(f)
         if '.' in s:
            integer_part, decimal_part = s.split('.')
            truncated_decimal = decimal_part[:n]
            return float(f"{integer_part}.{truncated_decimal}")
         else:
            return f
        
     for rec in self:
        d1 = rec.density_fly_l
        d2 = rec.density_fly_2
        values = [v for v in (d1, d2) if v is not None]

        if values:
            avg = sum(values) / len(values)
            rec.avg_density_fly = truncate(avg, 2)
        else:
            rec.avg_density_fly = 0.0
    

										
    avg_density_fly_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_avg_density_fly_conformity", store=True)

    @api.depends('avg_density_fly','eln_ref','grade')
    def _compute_avg_density_fly_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_density_fly_conformity = 'na'
                continue
            record.avg_density_fly_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214fgrt-1d2c-4d3b-9ebe-ecb0b5e1221e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214fgrt-1d2c-4d3b-9ebe-ecb0b5e1221e')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_density_fly - record.avg_density_fly*mu_value
                    upper = record.avg_density_fly + record.avg_density_fly*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_density_fly_conformity = 'pass'
                        break
                    else:
                        record.avg_density_fly_conformity = 'fail'

    avg_density_fly_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_density_fly_nabl", store=True)

    @api.depends('avg_density_fly','eln_ref','grade')
    def _compute_avg_density_fly_nabl(self):
        
        for record in self:
            record.avg_density_fly_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214fgrt-1d2c-4d3b-9ebe-ecb0b5e1221e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214fgrt-1d2c-4d3b-9ebe-ecb0b5e1221e')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_density_fly - record.avg_density_fly*mu_value
                    upper = record.avg_density_fly + record.avg_density_fly*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_density_fly_nabl = 'pass'
                        break
                    else:
                        record.avg_density_fly_nabl = 'fail'										
									

    # Fineness By Blain Air

    fineness_blain_name = fields.Char("Name",default="Fineness by Blaines Air Permeability Method")
    fineness_blain_visible = fields.Boolean("Fineness by Blaines Air Permeability Method Visible",compute="_compute_visible")

    selected_lab_fineness_blain1 = fields.Many2one(
        'fly.ash.lab.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_fly_ash_ids)]"
    )

    is_lab_fineness_blain = fields.Boolean(
        string="Lab Fine Selected",
    )

    @api.onchange('selected_lab_fineness_blain1')
    def _onchange_selected_lab_fineness_blain1(self):
        for rec in self:
            if rec.selected_lab_fineness_blain1:
                rec.is_lab_fineness_blain = True
            else:
                rec.is_lab_fineness_blain = False
       

    temp_fineness_blain = fields.Char("Temp °c" )
    humidity_fineness_blain = fields.Char("Humidity %" ) 

    density_pozzolana = fields.Float(string="Density of pozzolana (ƍ) – gm/cc", digits=(12, 3))

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

    specific_surface = fields.Float(string="Specific Surface at (S)– cm2/gm",compute="_compute_specific_surface_m2kg", store=True ,digits=(12, 0))

    specific_surface_m2kg = fields.Float(string="Specific Surface at (S)– m2/kg",compute="_compute_specific_surface_m2kg", store=True, digits=(12, 0))

    @api.depends('avg_time_first', 'density_pozzolana')
    def _compute_specific_surface_m2kg(self):
        # Fixed standard constants (from Excel / test standard)
        ss = 4090.0      # Standard specific surface (cm²/g)
        es = 0.5         # Porosity of standard bed
        e = 0.5          # Porosity of sample bed
        ts = 25.48       # Time for manometer drop (standard)
        ys = 2.33        # Density of standard sample (gm/cc)
        vs = 0.125       # Volume of standard bed
        v = 0.125        # Volume of sample bed

        for rec in self:
            # try:
                if rec.avg_time_first and rec.density_pozzolana:
                    S = (
                        (ss * ys * (1 - es) * math.sqrt(v) * math.sqrt(rec.avg_time_first))
                        / (rec.density_pozzolana * (1 - e) * math.sqrt(vs) * math.sqrt(ts))
                    )
                    rec.specific_surface = round(S, 1)
                    rec.specific_surface_m2kg = round(S / 10, 1)  # cm²/g → m²/kg
                else:
                    rec.specific_surface = 0.0
                    rec.specific_surface_m2kg = 0.0
            # except Exception:
            #     rec.specific_surface = 0.0
            #     rec.specific_surface_m2kg = 0.0

        

    specific_surface_m2kg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_specific_surface_m2kg_conformity", store=True)

    @api.depends('specific_surface_m2kg','eln_ref','grade')
    def _compute_specific_surface_m2kg_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.specific_surface_m2kg_conformity = 'na'
                continue
            record.specific_surface_m2kg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03c1a445-e599-4ba9-ac67-f186a7c6dd61')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03c1a445-e599-4ba9-ac67-f186a7c6dd61')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.specific_surface_m2kg - record.specific_surface_m2kg*mu_value
                    upper = record.specific_surface_m2kg + record.specific_surface_m2kg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.specific_surface_m2kg_conformity = 'pass'
                        break
                    else:
                        record.specific_surface_m2kg_conformity = 'fail'

    specific_surface_m2kg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_specific_surface_m2kg_nabl", store=True)

    @api.depends('specific_surface_m2kg','eln_ref','grade')
    def _compute_specific_surface_m2kg_nabl(self):
        
        for record in self:
            record.specific_surface_m2kg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03c1a445-e599-4ba9-ac67-f186a7c6dd61')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03c1a445-e599-4ba9-ac67-f186a7c6dd61')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.specific_surface_m2kg - record.specific_surface_m2kg*mu_value
                    upper = record.specific_surface_m2kg + record.specific_surface_m2kg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.specific_surface_m2kg_nabl = 'pass'
                        break
                    else:
                        record.specific_surface_m2kg_nabl = 'fail'









        
        
       # Particles retained on 45 micron IS sieve (wet sieving) - %

    fineness_name = fields.Char("Name",default="Particles retained on 45 micron IS sieve (wet sieving) - %")
    fineness_visible = fields.Boolean("Particles retained on 45 micron IS sieve (wet sieving) - %",compute="_compute_visible")

    selected_lab_fineness1 = fields.Many2one(
        'fly.ash.lab.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_fly_ash_ids)]"
    )

    is_lab_fineness = fields.Boolean(
        string="Lab Fine Selected",
    )

    @api.onchange('selected_lab_fineness1')
    def _onchange_selected_lab_fineness1(self):
        for rec in self:
            if rec.selected_lab_fineness1:
                rec.is_lab_fineness = True
            else:
                rec.is_lab_fineness = False
       
       
    temp_fineness = fields.Char("Temp °c" )
    humidity_fineness = fields.Char("Humidity %" ) 

    fineness_child_lines = fields.One2many('particles.retained.line','parent_id',string="Fineness By Sieving Test") 

    avg_particle_retained = fields.Float("Average Particles retained on 45 micron IS sieve (wet sieving) - %",compute="_compute_avg_particle_retained")

    @api.depends('fineness_child_lines.particle_retained')
    def _compute_avg_particle_retained(self):
        for record in self:
            if record.fineness_child_lines:
                record.avg_particle_retained = sum(record.fineness_child_lines.mapped('particle_retained'))/len(record.fineness_child_lines)
            else:
                record.avg_particle_retained = 0.0
    

    avg_particle_retained_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        ], string="Conformity", compute="_compute_avg_particle_retained_conformity", store=True)

    @api.depends('avg_particle_retained','eln_ref','grade')
    def _compute_avg_particle_retained_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_particle_retained_conformity = 'na'
                continue
            record.avg_particle_retained_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104fvdr-6047-4781-9885-0b8b29050fda')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104fvdr-6047-4781-9885-0b8b29050fda')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_particle_retained - record.avg_particle_retained*mu_value
                    upper = record.avg_particle_retained + record.avg_particle_retained*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_particle_retained_conformity = 'pass'
                        break
                    else:
                        record.avg_particle_retained_conformity = 'fail'

    avg_particle_retained_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_particle_retained_nabl", store=True)

    @api.depends('avg_particle_retained','eln_ref','grade')
    def _compute_avg_particle_retained_nabl(self):
        
        for record in self:
            record.avg_particle_retained_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104fvdr-6047-4781-9885-0b8b29050fda')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104fvdr-6047-4781-9885-0b8b29050fda')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_particle_retained - record.avg_particle_retained*mu_value
                    upper = record.avg_particle_retained + record.avg_particle_retained*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_particle_retained_nabl = 'pass'
                        break
                    else:
                        record.avg_particle_retained_nabl = 'fail'


	# Compressive Strength Test
    compressive_strength_visible = fields.Boolean("Compressive Strength Fly Ash",compute="_compute_visible")
    compressive_strength_name = fields.Char("Name",default="Compressive Strength Fly Ash")
    compressive_cement_name = fields.Char("Name",default="Compressive Strength Of Cement")

    compressive_strength7_visible = fields.Boolean("Compressive Strength Fly Ash",compute="_compute_visible")
    compressive_strength7_name = fields.Char("Name",default="Compressive Strength Fly Ash")


    is_compressive_strength = fields.Boolean(
        string="Lab Fine Selected",
        
    )

    
    show_sieve = fields.Boolean(default=False)

    def action_generate_opc_compressive_strength(self):
        for record in self:

            record.is_compressive_strength = True

            if record.lab_id and ' - ' in record.lab_id:
                start_str, end_str = record.lab_id.split(' - ')
                prefix = '-'.join(start_str.split('-')[:2])
                start = int(start_str.split('-')[2])
                end = int(end_str.split('-')[2])

                lines = []
                for i in range(start, end + 1):
                    lab_id = f"{prefix}-{str(i).zfill(3)}"
                    lines.append((0, 0, {'lab_id': lab_id}))

                record.compressive_strength_child_lines = lines
                record.is_compressive_strength = True

            # 🔹 Set flag to show sieve analysis
            if record.compressive_strength_child_lines:
                record.show_sieve = True

            # 🔹 Reload the current record in form view
            return {
                'type': 'ir.actions.act_window',
                'name': 'OPC Form',
                'res_model': 'mechanical.flyasch.normalconsistency',
                'res_id': record.id,  # ✅ Use record.id instead of self.id
                'view_mode': 'form',
                'target': 'current',
            }


    is_compressive_strength1 = fields.Boolean(
        string="Lab Fine Selected",
        
    )

    
    show_sieve = fields.Boolean(default=False)

    def action_generate_opc_compressive_strength1(self):
        for record in self:

            record.is_compressive_strength1 = True

            if record.lab_id and ' - ' in record.lab_id:
                start_str, end_str = record.lab_id.split(' - ')
                prefix = '-'.join(start_str.split('-')[:2])
                start = int(start_str.split('-')[2])
                end = int(end_str.split('-')[2])

                lines = []
                for i in range(start, end + 1):
                    lab_id = f"{prefix}-{str(i).zfill(3)}"
                    lines.append((0, 0, {'lab_id': lab_id}))

                record.compressive_cement_child_lines = lines
                record.is_compressive_strength1 = True

            # 🔹 Set flag to show sieve analysis
            if record.compressive_cement_child_lines:
                record.show_sieve = True

            # 🔹 Reload the current record in form view
            return {
                'type': 'ir.actions.act_window',
                'name': 'OPC Form',
                'res_model': 'mechanical.flyasch.normalconsistency',
                'res_id': record.id,  # ✅ Use record.id instead of self.id
                'view_mode': 'form',
                'target': 'current',
            }




    temp_compressive_strength = fields.Char("Temp °c" )
    humidity_compressive_strength = fields.Char("Humidity %" )

    compressive_strength_child_lines = fields.One2many('flyash.compressive.strength.line','parent_id',string="Compressive Strength Test")\
    

    # selected_lab_flyash1 = fields.Many2one(
    #     'flyash.lab.line',
    #     string="Select Lab ID",
    #     domain="[('id', 'in', lab_flyash_ids)]"
    # )

    
    # is_compressive_strength = fields.Boolean(
    #     string="Compacted Density Selected",
        
    # )

    # @api.onchange('selected_lab_flyash1')
    # def _onchange_selected_lab_flyash1(self):
    #     for rec in self:
    #         if rec.selected_lab_flyash1:
    #             rec.is_compressive_strength = True
    #         else:
    #             rec.is_compressive_strength= False





    def action_calculate_avg_strength(self):
        for rec in self:

          

            lines = rec.compressive_strength_child_lines.sorted(key=lambda l: l.serial_no) 
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
         

        


            
    


   # Compressive Strength Test
    

    compressive_cement_child_lines = fields.One2many('flyash.compressive.cement.line','parent_id',string="Compressive Strength Cement Test")

    def action_calculate_avg_cement_strength(self):
        for rec in self:

            rec.calc_mode = True
            rec.submit_mode = False
            lines = rec.compressive_cement_child_lines.sorted(key=lambda l: l.serial_no) 
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




   

    avg_7_days1 = fields.Float(string="Avg Strength (7 Days)", compute="_compute_avg_strengths1", store=True)

    avg_28_days1 = fields.Float(string="Avg Strength (28 Days)", compute="_compute_avg_strengths1", store=True)

    @api.depends('compressive_strength_child_lines.days', 'compressive_strength_child_lines.avg_compressive_strength')
    def _compute_avg_strengths1(self):
        for rec in self:
            strengths_7 = [line.avg_compressive_strength for line in rec.compressive_strength_child_lines if line.days == 7 and line.avg_compressive_strength]
            strengths_28 = [line.avg_compressive_strength for line in rec.compressive_strength_child_lines if line.days == 28 and line.avg_compressive_strength]

            
            rec.avg_7_days1 = mean(strengths_7) if strengths_7 else 0.0
            rec.avg_28_days1 = mean(strengths_28) if strengths_28 else 0.0


    avg_7_days2 = fields.Float(string="Avg Strength (7 Days)", compute="_compute_avg_strengths2", store=True)

    avg_28_days2 = fields.Float(string="Avg Strength (28 Days)", compute="_compute_avg_strengths2", store=True)

    @api.depends('compressive_cement_child_lines.days', 'compressive_cement_child_lines.avg_compressive_strength')
    def _compute_avg_strengths2(self):
        for rec in self:
            strengths_7 = [line.avg_compressive_strength for line in rec.compressive_cement_child_lines if line.days == 7 and line.avg_compressive_strength]
            strengths_28 = [line.avg_compressive_strength for line in rec.compressive_cement_child_lines if line.days == 28 and line.avg_compressive_strength]

            
            rec.avg_7_days2 = mean(strengths_7) if strengths_7 else 0.0
            rec.avg_28_days2 = mean(strengths_28) if strengths_28 else 0.0


    average_28_days = fields.Float(string="Avg. Strength MPa (28 Days)", compute="_compute_average_28_days", store=True)

    @api.depends('avg_28_days1','avg_28_days2')
    def _compute_average_28_days(self):
        for record in self:
            if record.avg_28_days2 != 0:
                record.average_28_days = (record.avg_28_days1 / record.avg_28_days2)  * 100
            else:
                record.average_28_days = 0.0

    average_7_days = fields.Float(string="Avg. Strength MPa (7 Days)", compute="_compute_average_7_days", store=True)

    @api.depends('avg_7_days1','avg_7_days2')
    def _compute_average_7_days(self):
        for record in self:
            if record.avg_7_days2 != 0:
                record.average_7_days = (record.avg_7_days1 / record.avg_7_days2)  * 100
            else:
                record.average_7_days = 0.0   


    average_7_days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity', default='fail',compute="_compute_average_7_days_conformity")

    average_7_days_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_average_7_days_nabl")


    @api.depends('average_7_days','eln_ref','grade')
    def _compute_average_7_days_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_7_days_conformity = 'na'
                continue
            record.average_7_days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4c16fe35-cd02-4d12-ba13-aa95bf000d73')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4c16fe35-cd02-4d12-ba13-aa95bf000d73')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.average_7_days - record.average_7_days*mu_value
                    upper = record.average_7_days + record.average_7_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_7_days_conformity = 'pass'
                        break
                    else:
                        record.average_7_days_conformity = 'fail'

    @api.depends('average_7_days','eln_ref','grade')
    def _compute_average_7_days_nabl(self):
        
        for record in self:
            record.average_7_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4c16fe35-cd02-4d12-ba13-aa95bf000d73')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4c16fe35-cd02-4d12-ba13-aa95bf000d73')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_7_days - record.average_7_days*mu_value
            upper = record.average_7_days + record.average_7_days*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_7_days_nabl = 'pass'
                break
            else:
                record.average_7_days_nabl = 'fail'                    



    average_28_days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity', default='fail',compute="_compute_average_28_days_conformity")

    average_28_days_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_average_28_days_nabl")


    @api.depends('average_28_days','eln_ref','grade')
    def _compute_average_28_days_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_28_days_conformity = 'na'
                continue
            record.average_28_days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3201vfg-98f0-419e-94cd-1844af4393f5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3201vfg-98f0-419e-94cd-1844af4393f5')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.average_28_days - record.average_28_days*mu_value
                    upper = record.average_28_days + record.average_28_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_28_days_conformity = 'pass'
                        break
                    else:
                        record.average_28_days_conformity = 'fail'

    @api.depends('average_28_days','eln_ref','grade')
    def _compute_average_28_days_nabl(self):
        
        for record in self:
            record.average_28_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3201vfg-98f0-419e-94cd-1844af4393f5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3201vfg-98f0-419e-94cd-1844af4393f5')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_28_days - record.average_28_days*mu_value
            upper = record.average_28_days + record.average_28_days*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_28_days_nabl = 'pass'
                break
            else:
                record.average_28_days_nabl = 'fail'


   



    #  Determination of Lime Reactivity of Flyash	
    
    lime_visible = fields.Boolean("Determination of Lime Reactivity of Flyash",compute="_compute_visible")
    lime_name = fields.Char("Name",default="Determination of Lime Reactivity of Flyash")

    is_lime = fields.Boolean(
        string="Lab Fine Selected",
        
    )

    
    show_sieve = fields.Boolean(default=False)

    def action_generate_opc_lime(self):
        for record in self:

            record.is_lime = True

            if record.lab_id and ' - ' in record.lab_id:
                start_str, end_str = record.lab_id.split(' - ')
                prefix = '-'.join(start_str.split('-')[:2])
                start = int(start_str.split('-')[2])
                end = int(end_str.split('-')[2])

                lines = []
                for i in range(start, end + 1):
                    lab_id = f"{prefix}-{str(i).zfill(3)}"
                    lines.append((0, 0, {'lab_id': lab_id}))

                record.lime_child_lines = lines
                record.is_lime = True

            # 🔹 Set flag to show sieve analysis
            if record.lime_child_lines:
                record.show_sieve = True

            # 🔹 Reload the current record in form view
            return {
                'type': 'ir.actions.act_window',
                'name': 'OPC Form',
                'res_model': 'mechanical.flyasch.normalconsistency',
                'res_id': record.id,  # ✅ Use record.id instead of self.id
                'view_mode': 'form',
                'target': 'current',
            }





    temp_lime = fields.Char("Temp °c" )
    humidity_lime = fields.Char("Humidity %" )

    lime_child_lines = fields.One2many('flyash.lime.line','parent_id',string="Lime Reactivity of Flyash")	

    def action_calculate_avg_strengthss(self):
        for rec in self:


            rec.calc_mode = True
            rec.submit_mode = False

            lines = rec.lime_child_lines.sorted(key=lambda l: l.serial_no) 
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

    avg_10_days = fields.Float(string="Avg Strength (10 Days)", compute="_compute_avg_10_days", store=True)

    @api.depends('lime_child_lines.days', 'lime_child_lines.avg_compressive_strength')
    def _compute_avg_10_days(self):
        for rec in self:
            strengths_10 = [line.avg_compressive_strength for line in rec.lime_child_lines if line.days == 10 and line.avg_compressive_strength]

            rec.avg_10_days = mean(strengths_10) if strengths_10 else 0.0



    avg_10_days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity', default='fail',compute="_compute_avg_10_days_conformity")

    avg_10_days_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_10_days_nabl")


    @api.depends('avg_10_days','eln_ref','grade')
    def _compute_avg_10_days_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_10_days_conformity = 'na'
                continue
            record.avg_10_days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','320147vbfd-c97d-4d83-a9f2-2eb112eae116')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','320147vbfd-c97d-4d83-a9f2-2eb112eae116')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_10_days - record.avg_10_days*mu_value
                    upper = record.avg_10_days + record.avg_10_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_10_days_conformity = 'pass'
                        break
                    else:
                        record.avg_10_days_conformity = 'fail'

    @api.depends('avg_10_days','eln_ref','grade')
    def _compute_avg_10_days_nabl(self):
        
        for record in self:
            record.avg_10_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','320147vbfd-c97d-4d83-a9f2-2eb112eae116')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','320147vbfd-c97d-4d83-a9f2-2eb112eae116')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_10_days - record.avg_10_days*mu_value
            upper = record.avg_10_days + record.avg_10_days*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_10_days_nabl = 'pass'
                break
            else:
                record.avg_10_days_nabl = 'fail'       





    # Drying shrinkage Test

    drying_shrinkage_visible = fields.Boolean("Drying shrinkage Test",compute="_compute_visible")
    drying_shrinkage_name = fields.Char("Name",default="Drying shrinkage Test")


    selected_lab_drying_shrinkage1 = fields.Many2one(
        'fly.ash.lab.line',
        string="Select Lab ID",
        domain="[('id', 'in', lab_fly_ash_ids)]"
    )

    is_lab_drying_shrinkage = fields.Boolean(
        string="Lab Fine Selected",
    )

    @api.onchange('selected_lab_drying_shrinkage1')
    def _onchange_selected_lab_drying_shrinkage1(self):
        for rec in self:
            if rec.selected_lab_drying_shrinkage1:
                rec.is_lab_drying_shrinkage = True
            else:
                rec.is_lab_drying_shrinkage = False
       


    temp_drying_shrinkage = fields.Char("Temp °c" )
    humidity_drying_shrinkage = fields.Char("Humidity %" )

    drying_shrinkage_child_lines = fields.One2many('drying.shrinkage.line','parent_id',string="AutoClave Test")

    avg_dry_autoclave_expansion = fields.Float('Average Expansion %',compute="_compute_avg_dry_autoclave_expansion")


    @api.depends('drying_shrinkage_child_lines.dry_autoclave_expansion')
    def _compute_avg_dry_autoclave_expansion(self):
        for record in self:
            if record.drying_shrinkage_child_lines:
              record.avg_dry_autoclave_expansion = sum(record.drying_shrinkage_child_lines.mapped('dry_autoclave_expansion'))/ len(record.drying_shrinkage_child_lines)
            else:
                record.avg_dry_autoclave_expansion = 0.0






    avg_dry_autoclave_expansion_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),], string="Conformity", compute="_compute_avg_dry_autoclave_expansion_conformity", store=True)

    @api.depends('avg_dry_autoclave_expansion','eln_ref','grade')
    def _compute_avg_dry_autoclave_expansion_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_dry_autoclave_expansion_conformity = 'na'
                continue
            record.avg_dry_autoclave_expansion_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214vbfsd-0da6-4ec4-a91e-d41c44f5edb5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214vbfsd-0da6-4ec4-a91e-d41c44f5edb5')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_dry_autoclave_expansion - record.avg_dry_autoclave_expansion*mu_value
                    upper = record.avg_dry_autoclave_expansion + record.avg_dry_autoclave_expansion*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_dry_autoclave_expansion_conformity = 'pass'
                        break
                    else:
                        record.avg_dry_autoclave_expansion_conformity = 'fail'

    avg_dry_autoclave_expansion_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_dry_autoclave_expansion_nabl", store=True)

    @api.depends('avg_dry_autoclave_expansion','eln_ref','grade')
    def _compute_avg_dry_autoclave_expansion_nabl(self):
        
        for record in self:
            record.avg_dry_autoclave_expansion_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214vbfsd-0da6-4ec4-a91e-d41c44f5edb5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214vbfsd-0da6-4ec4-a91e-d41c44f5edb5')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_dry_autoclave_expansion - record.avg_dry_autoclave_expansion*mu_value
                    upper = record.avg_dry_autoclave_expansion + record.avg_dry_autoclave_expansion*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_dry_autoclave_expansion_nabl = 'pass'
                        break
                    else:
                        record.avg_dry_autoclave_expansion_nabl = 'fail'

	
			




    


    




    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
 
        for record in self:
            record.normal_consistency_visible = False
            record.final_setting_time_visible  = False  
            record.initial_setting_time_visible  = False 
            record.soundness_visible = False
            record.sound_auto_visible = False
            record.specific_gravity_visible = False
            record.fineness_visible = False
            record.drying_shrinkage_visible = False
            record.compressive_strength_visible = False
            record.compressive_strength7_visible = False
            record.lime_visible = False
            record.fineness_blain_visible = False

            

            


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                # import wdb;wdb.set_trace()

                # Normal consistency
                if sample.internal_id == '124fgrt3-1b3c-43ae-9c20-5421b6d6edf9':
                    record.normal_consistency_visible = True
                # Initial setting time
                if sample.internal_id == '2014fgr32-6bbe-4fdf-9571-a5a099be0293':
                    record.initial_setting_time_visible  = True
                # Final setting time
                if sample.internal_id == '32145grte8-6526-4fcc-a5ec-18cc1ae10857':  
                    record.final_setting_time_visible  = True
                # Soundness By LeChatelier Test
                if sample.internal_id == '3210ght7-91b0-4153-87ef-11b6954a9837':
                    record.soundness_visible = True
                # Soundness By AutoClave Test
                if sample.internal_id == 'b0e2437d-514b-4875-9f3a-203d5fad1d83':
                    record.sound_auto_visible = True
            
                # specific gravity
                if sample.internal_id == '3214fgrt-1d2c-4d3b-9ebe-ecb0b5e1221e':
                    record.specific_gravity_visible = True    

                    
                if sample.internal_id == '2104fvdr-6047-4781-9885-0b8b29050fda':
                    record.fineness_visible = True


                # Drying shrinkage Test
                if sample.internal_id == '3214vbfsd-0da6-4ec4-a91e-d41c44f5edb5':
                    record.drying_shrinkage_visible = True


                # compressive strength 7 days
                if sample.internal_id == '4c16fe35-cd02-4d12-ba13-aa95bf000d73':
                    record.compressive_strength7_visible = True
                
                # compressive strength
                if sample.internal_id == '3201vfg-98f0-419e-94cd-1844af4393f5':
                    record.compressive_strength_visible = True


                
                # lime reactivity
                if sample.internal_id == '320147vbfd-c97d-4d83-a9f2-2eb112eae116':
                    record.lime_visible = True




                # Fineness By Blain Air
                if sample.internal_id == '03c1a445-e599-4ba9-ac67-f186a7c6dd61':
                    record.fineness_blain_visible = True
               

    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
                lambda r: r.technician == current_user
            )

        for result in technician_results:

             # Consistency
            if result.parameter.internal_id == '124fgrt3-1b3c-43ae-9c20-5421b6d6edf9':
                result.result_char = round(self.consistency_percent,2)
                result.calculated = True
                if self.normal_consistency_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Initial Setting
            if result.parameter.internal_id == '2014fgr32-6bbe-4fdf-9571-a5a099be0293':
                result.result_char = round(self.initial_time_set,2)
                result.calculated = True
                # if self.initial_time_set_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue

            # Final Setting
            if result.parameter.internal_id == '32145grte8-6526-4fcc-a5ec-18cc1ae10857':
                result.result_char = round(self.final_time_set,2)
                result.calculated = True
                # if self.final_time_set_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue

            # Soundness By Le-Chatelier Test
            if result.parameter.internal_id == '3210ght7-91b0-4153-87ef-11b6954a9837':
                result.result_char = round(self.avg_expansion,2)
                result.calculated = True
                if self.avg_expansion_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Soundness By AutoClave Test
            if result.parameter.internal_id == 'b0e2437d-514b-4875-9f3a-203d5fad1d83':
                result.result_char = round(self.avg_autoclave_expansion,2)
                result.calculated = True
                if self.avg_autoclave_expansion_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Specific Gravity Test
            if result.parameter.internal_id == '3214fgrt-1d2c-4d3b-9ebe-ecb0b5e1221e':
                result.result_char = round(self.avg_density_fly,2)
                result.calculated = True
                if self.avg_density_fly_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Particles retained on 45 micron IS sieve (wet sieving) - %
            if result.parameter.internal_id == '2104fvdr-6047-4781-9885-0b8b29050fda':
                result.result_char = round(self.avg_particle_retained,2)
                result.calculated = True
                if self.avg_particle_retained_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Drying shrinkage Test
            if result.parameter.internal_id == '3214vbfsd-0da6-4ec4-a91e-d41c44f5edb5':
                result.result_char = round(self.avg_dry_autoclave_expansion,2)
                result.calculated = True
                if self.avg_dry_autoclave_expansion_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Compressive Strength
            if result.parameter.internal_id == '3201vfg-98f0-419e-94cd-1844af4393f5':
                result.result_char = round(self.average_28_days,2)
                result.calculated = True
                if self.average_28_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Determination of Lime Reactivity of Flyash
            if result.parameter.internal_id == '320147vbfd-c97d-4d83-a9f2-2eb112eae116':
                result.result_char = round(self.avg_10_days,2)
                result.calculated = True
                if self.avg_10_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

             # Fineness By Blain Air
            if result.parameter.internal_id == '03c1a445-e599-4ba9-ac67-f186a7c6dd61':
                result.result_char = round(self.specific_surface_m2kg,2)
                result.calculated = True
                if self.specific_surface_m2kg == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            
            if result.parameter.internal_id == '4c16fe35-cd02-4d12-ba13-aa95bf000d73':
                result.calculated = True
            
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
        record = super(FlyaschNormalConsistency, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







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
        record = self.env['mechanical.flyasch.normalconsistency'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values








class ConsistencyLine(models.Model):
    _name= "consistency.line"
    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency',string="Parent Id")

    sr_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)
    # trail_no = fields.Integer(string="Trial No")
    mass_cement = fields.Float("Mass of Cement Taken (gms)")
    water_added = fields.Float("Water Added (ml)")
    water_percent = fields.Float("Water (%)",compute="_compute_water_percent")
    penetration_mould = fields.Float("Penetration from Bottom of Mould (mm)")

    @api.depends('mass_cement','water_added')
    def _compute_water_percent(self):
        for record in self:
            if record.mass_cement != 0:
                record.water_percent = (record.water_added / record.mass_cement) * 100
            else:
             record.water_percent = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(ConsistencyLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1

            

class SettingTimeLine(models.Model):
    _name= "setting.time.line"
    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency',string="Parent Id")

    sr_no = fields.Integer(string="Trial NO", readonly=True, copy=False, default=1)
   
    time_water_t1 = fields.Datetime(string="Time at which water is first added to cement, t1, mins")
    time_needle_fails_t2 = fields.Datetime(string="Time when needle fails to penetrate 5 +/-0.5 mm from bottom of the mould, t2 ,mins")
    time_needle_attach_t3 = fields.Datetime(string="Time when the needle makes an impression but the attachment fails to do so, t3, mins")

    initial_setting = fields.Float("Initial setting time, min (t2-t1)",compute="_compute_setting_times")

    final_setting = fields.Float("Final setting time, min (t3-t1)",compute="_compute_setting_times")


    @api.depends('time_water_t1', 'time_needle_fails_t2', 'time_needle_attach_t3')
    def _compute_setting_times(self):
        for rec in self:
            rec.initial_setting = 0.0
            rec.final_setting = 0.0
            if rec.time_water_t1 and rec.time_needle_fails_t2:
                t1 = rec.time_water_t1
                t2 = rec.time_needle_fails_t2
                # Handle midnight crossover
                if t1 > t2:
                    t2 = t2.replace(day=t2.day + 1)
                rec.initial_setting = (t2 - t1).total_seconds() / 60  # Convert seconds to minutes

            if rec.time_water_t1 and rec.time_needle_attach_t3:
                t1 = rec.time_water_t1
                t3 = rec.time_needle_attach_t3
                # Handle midnight crossover
                if t1 > t3:
                    t3 = t3.replace(day=t3.day + 1)
                rec.final_setting = (t3 - t1).total_seconds() / 60



	

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(SettingTimeLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1




class SoundnessLeChatelierLine(models.Model):	
    _name= "soundness.le.chatelier.line"
    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency',string="Parent Id")

    sr_no = fields.Integer(string="Sr.NO", readonly=True, copy=False, default=1)

    mould_no = fields.Char("Mould No.")
    initial_read = fields.Float("Initial Reading of Indicator Point Before Boiling (A) in mm")
    final_read = fields.Float("Final Reading of Indicator Point After 3 Hrs. Boiling (B) in mm")
    expansion = fields.Float(string="Expansion (B – A) mm",compute="_compute_expansion")


    @api.depends('initial_read','final_read')
    def _compute_expansion(self):
        for record in self:
            record.expansion = (record.final_read - record.initial_read)


		



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(SoundnessLeChatelierLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1





class SoundnessAutoclaveLine(models.Model):	
    _name= "soundness.autoclave.line"
    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency',string="Parent Id")

    sr_no = fields.Integer(string="Mould No.", readonly=True, copy=False, default=1)
    initial_reference_read = fields.Float("Reference Bar Reading (R1)")
    initial_read = fields.Float("Initial Reading (Ri)")
    initial_read_a = fields.Float("A (Ri – R1)",compute="_compute_initial_read_a",store=True)

    final_reference_read = fields.Float("Reference Bar Reading (R2)")
    final_read = fields.Float("Final Reading (Rf)")
    final_read_b = fields.Float("B (Rf – R2)",compute="_compute_final_read_b",store=True)

    autoclave_expansion = fields.Float(string="Autoclave Expansion (B-A)/250 x 100 %",compute="_compute_autoclave_expansion",store=True)

    @api.depends('initial_read','initial_reference_read')
    def _compute_initial_read_a(self):
        for record in self:
            record.initial_read_a = (record.initial_read - record.initial_reference_read)

    @api.depends('final_read','final_reference_read')
    def _compute_final_read_b(self):
        for record in self:
            record.final_read_b = (record.final_read - record.final_reference_read)


    @api.depends('initial_read_a','final_read_b')
    def _compute_autoclave_expansion(self):
        for record in self:
            record.autoclave_expansion = ((record.final_read_b - record.initial_read_a)/250 ) * 100

    



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(SoundnessAutoclaveLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class ParticlesRetainedLine(models.Model):
    _name= "particles.retained.line"
    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency',string="Parent Id")

    sr_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)
    sample_taken = fields.Float("Sample Taken (gm)")
    sieve_size = fields.Float("Sieve Size (µ)")
    weight_retained = fields.Float("Weight Retained (gm)")
    particle_retained = fields.Float("Particles retained on 45 micron IS sieve (wet sieving) - %",compute="_compute_particle_retained",store=True)

    @api.depends('weight_retained')
    def _compute_particle_retained(self):
        for record in self:
                record.particle_retained = record.weight_retained 


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(ParticlesRetainedLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1           


class DryingShrinkageLine(models.Model):	
    _name= "drying.shrinkage.line"
    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency',string="Parent Id")

    sr_no = fields.Integer(string="Mould No.", readonly=True, copy=False, default=1)
    initial_reference_read = fields.Float("Reference Bar Reading (R1)")
    initial_read = fields.Float("Initial Reading (Ri)")
    initial_read_a = fields.Float("A (Ri – R1)",compute="_compute_initial_read_a",store=True)

    final_reference_read = fields.Float("Reference Bar Reading (R2)")
    final_read = fields.Float("Final Reading (Rf)")
    final_read_b = fields.Float("B (Rf – R2)",compute="_compute_final_read_b",store=True)

    dry_autoclave_expansion = fields.Float(string="Autoclave Expansion (B-A)/250 x 100 %",compute="_compute_dry_autoclave_expansion",store=True)

    @api.depends('initial_read','initial_reference_read')
    def _compute_initial_read_a(self):
        for record in self:
            record.initial_read_a = (record.initial_read - record.initial_reference_read)

    @api.depends('final_read','final_reference_read')
    def _compute_final_read_b(self):
        for record in self:
            record.final_read_b = (record.final_read - record.final_reference_read)


    @api.depends('initial_read_a','final_read_b')
    def _compute_dry_autoclave_expansion(self):
        for record in self:
            record.dry_autoclave_expansion = ((record.final_read_b - record.initial_read_a)/250 ) * 100

    



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(DryingShrinkageLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class FlyashCompressiveStrengthLine(models.Model):
    _name = "flyash.compressive.strength.line"

    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency')

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    lab_id = fields.Char("Lab Id")
    testing_period = fields.Selection([
        ('day7', '168±2 hr (7 Days)'),
        ('day28', '672±4 hr (28 Days)'),
        
    ], string='Testing Period')
    # testing_period = fields.Char("Testing Period")
    casting_details = fields.Date("Casting Details Date",compute="_compute_dt_of_casting")
    days = fields.Integer(string="No.of Days",store=True)

    testing_details = fields.Date("Testing Details Date",compute="_compute_dt_of_testing")
    cube_im = fields.Char("Cube I/M")

    length1 = fields.Float("Length")
    
    width1 = fields.Float("Width")

    height1 = fields.Float("Height")
   

   

    load_failure = fields.Float("Load at Failure (P) kN",digits=(12,3))
    compressive_strength = fields.Float("Compressive Strength  MPa",compute="_compute_compressive_strength",store=True,digits=(12,1))
    avg_compressive_strength = fields.Float("Avg. Strength MPa",digits=(12,1))

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

        return super(FlyashCompressiveStrengthLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in opc_compressive_ids
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class FlyashCompressiveCementLine(models.Model):
    _name = "flyash.compressive.cement.line"

    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency')

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    lab_id = fields.Char("Lab Id")
    testing_period = fields.Selection([
        ('day7', '168±2 hr (7 Days)'),
        ('day28', '672±4 hr (28 Days)'),
        
    ], string='Testing Period')
    # testing_period = fields.Char("Testing Period")
    casting_details = fields.Date("Casting Details Date",compute="_compute_dt_of_casting")
    days = fields.Integer(string="No.of Days",store=True)

    testing_details = fields.Date("Testing Details Date",compute="_compute_dt_of_testing")
    cube_im = fields.Char("Cube I/M")

    length1 = fields.Float("Length (L)")
    
    width1 = fields.Float("Width")

    height1 = fields.Float("Height")
   

   

    load_failure = fields.Float("Load at Failure (P) kN",digits=(12,3))
    compressive_strength = fields.Float("Compressive Strength  MPa",compute="_compute_compressive_strength",store=True,digits=(12,1))
    avg_compressive_strength = fields.Float("Avg. Strength MPa",digits=(12,1))

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

        return super(FlyashCompressiveCementLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in opc_compressive_ids
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class FlyashLimeLine(models.Model):
    _name = "flyash.lime.line"

    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency')

    serial_no = fields.Integer(string="Sr No",readonly=True, copy=False, default=1)

    lab_id = fields.Char("Lab Id")
    testing_period = fields.Char("Testing Period")
    casting_details = fields.Date("Casting Details Date",compute="_compute_dt_of_casting")
    days = fields.Integer(string="No.of Days",store=True)

    testing_details = fields.Date("Testing Details Date",compute="_compute_dt_of_testing")
    cube_im = fields.Char("Cube I/M")

    length1 = fields.Float("Length (L)")
    
    width1 = fields.Float("Width")

    height1 = fields.Float("Height")
   

   

    load_failure = fields.Float("Load at Failure (P) kN",digits=(12,3))
    compressive_strength = fields.Float("Compressive Strength  MPa",compute="_compute_compressive_strength",store=True,digits=(12,1))
    avg_compressive_strength = fields.Float("Avg. Strength MPa",digits=(12,1))

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

        return super(FlyashLimeLine, self).create(vals)


class FlyashNotes(models.Model):
    _name = "flyash.notes"

    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")



class LabOptionLine(models.Model):
    _name = 'fly.ash.lab.line'
    _description = 'Lab Options'
    _rec_name = 'lab'  # Dropdown मध्ये हे नाव दिसेल

    lab = fields.Char(string="Lab ID")
    parent_id = fields.Many2one('mechanical.flyasch.normalconsistency', string="Parent")











