from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math




class FineAggregate(models.Model):
    _name = "mechanical.fine.aggregate"
    _inherit = "lerm.eln"
    _rec_name = "name_aggregate"
    

    name_aggregate = fields.Char("Name",default="Fine Aggregate")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    avg_compacted_unit  = fields.Char("Compacted Density", compute="_compute_units", store=False)

    notes_id = fields.One2many('fine.notes','parent_id',string="Notes")


    calc_mode = fields.Boolean(default=True)     
    submit_mode = fields.Boolean(default=False)

    @api.model
    def default_get(self, fields):
        res = super(FineAggregate, self).default_get(fields)

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
            'res_model': 'fine.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }


    # ---- helper method
    def _get_unit(self, internal_id):
        param = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', internal_id)
        ], limit=1)
        return param.unit.name if param.unit else ""


        # ---- compute fields (unit बदलल्यावर update)
    def _compute_units(self):
        for rec in self:
            
            rec.avg_compacted_unit     = rec._get_unit("357f579d-a310-4015-bc11-28a85c53ac83")
          

          

# Sieve Analysis 
    sieve_analysis_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")



    temp_sieve_analysis = fields.Char(string="Temp.°C" ,required=True)
    humidity_sieve_analysis= fields.Char(string="Humidity %" ,required=True)


    sieve_analysis_child_lines = fields.One2many('mechanical.fine.agg.sieve.analysis.ssl.line','parent_id',string="Parameter",
                                                  default=lambda self: self._default_sieve_analysis_child_lines())
    total_sieve_analysis = fields.Float(string="Total",compute="_compute_total_sieve")
    # cumulative = fields.Float(string="Cumulative",compute="_compute_cumulative")
    wt_of_sample = fields.Float(string="Weight of Sample, gms")
    zone_type = fields.Selection(
    selection=[
        ('zone_i', 'Zone I'),
        ('zone_ii', 'Zone II'),
        ('zone_iii', 'Zone III'),
        ('zone_iv', 'Zone IV'),
    ],
    string="Zone",
    required=False  
)


    fineness_modulus = fields.Float(string="Fineness Modulus", compute="_compute_fineness_modulus")
    grading = fields.Char(string="Grading",compute="_compute_zone_display_name")

    @api.depends('zone_type')
    def _compute_zone_display_name(self):
        for record in self:
            if record.zone_type:
                record.grading = dict(self._fields['zone_type'].selection).get(record.zone_type, '')
            else:
                record.grading = ''



  

    @api.depends('sieve_analysis_child_lines.cumulative_retained')
    def _compute_fineness_modulus(self):
        for record in self:
            # Exclude the last line (assumes order is important)
            lines = record.sieve_analysis_child_lines[:-1]  # all except last
            fineness_modulus = sum(line.cumulative_retained for line in lines) / 100
            record.fineness_modulus = fineness_modulus



    @api.model
    def _default_sieve_analysis_child_lines(self):
        default_lines = [
            (0, 0, {'sieve_size': '10 mm'}),
            (0, 0, {'sieve_size': '4.75 mm'}),
            (0, 0, {'sieve_size': '2.36 mm'}),
            (0, 0, {'sieve_size': '1.18 mm'}),
            (0, 0, {'sieve_size': '600 micron'}),
            (0, 0, {'sieve_size': '300 micron'}),
            (0, 0, {'sieve_size': '150 micron'}),
            (0, 0, {'sieve_size': 'Pan'})
            
        ]
        return default_lines

    @api.onchange('zone_type')
    def _onchange_zone_type(self):
        zone_limits = {
            'zone_i': {
                '10 mm': '100',
                '4.75 mm': '90 - 100',
                '2.36 mm': '60 - 95',
                '1.18 mm': '30 - 70',
                '600 micron': '15 - 34',
                '300 micron': '5 - 20',
                '150 micron': '0 - 10',
                'Pan': '-',
            },
            'zone_ii': {
                '10 mm': '100',
                '4.75 mm': '90 - 100',
                '2.36 mm': '75 - 100',
                '1.18 mm': '55 - 90',
                '600 micron': '35 - 59',
                '300 micron': '8 - 30',
                '150 micron': '0 - 10',
                'Pan': '-',
            },
            'zone_iii': {
                '10 mm': '100',
                '4.75 mm': '90 - 100',
                '2.36 mm': '85 - 100',
                '1.18 mm': '75 - 100',
                '600 micron': '60 - 79',
                '300 micron': '12 - 40',
                '150 micron': '0 - 10',
                'Pan': '-',
            },
            'zone_iv': {
                '10 mm': '100',
                '4.75 mm': '95 - 100',
                '2.36 mm': '95 - 100',
                '1.18 mm': '90 - 100',
                '600 micron': '80 - 100',
                '300 micron': '15 - 50',
                '150 micron': '0 - 5',
                'Pan': '-',
            }
        }

        limits = zone_limits.get(self.zone_type)
        if limits:
            for line in self.sieve_analysis_child_lines:
                line.specific_limt = limits.get(line.sieve_size, '')





    @api.onchange('sieve_analysis_child_lines')
    def _onchange_sieve_analysis_child_lines(self):
        for rec in self:
            pan_line = None
            total_retained = 0.0
            target_sieves = ['10 mm','4.75 mm','2.36 mm','1.18 mm', '600 micron', '300 micron', '150 micron']

            for line in rec.sieve_analysis_child_lines:
                if line.sieve_size and line.sieve_size.lower() == 'pan':
                    pan_line = line
                elif line.sieve_size in target_sieves:
                    total_retained += line.wt_retained or 0.0

            if pan_line:
                pan_line.wt_retained = (rec.wt_of_sample or 0.0) - total_retained



    # corrected(added)
    def calculate_sieve1(self): 
        for record in self:

            record.calc_mode = True
            record.submit_mode = False

            previous_cumulative = 0  
            for line in record.sieve_analysis_child_lines:
                print("Rows", str(line.percent_retained))
                previous_line = line.serial_no - 1
                if previous_line == 0:
                    cumulative_retained = line.percent_retained
                else:
                    previous_line_record = self.env['mechanical.fine.agg.sieve.analysis.ssl.line'].sudo().search([("serial_no", "=", previous_line),("parent_id", "=", record.id)], limit=1)
                    
                    if previous_line_record:
                        previous_cumulative = previous_line_record.cumulative_retained
                    cumulative_retained = previous_cumulative + line.percent_retained

                passing_percent = 100 - cumulative_retained

                line.write({
                    'cumulative_retained': round(cumulative_retained, 2),
                    'passing_percent': round(passing_percent, 2),
                })
                
                print("Updated Cumulative Retained:", cumulative_retained)
                print("Updated Passing Percent:", passing_percent)

                previous_cumulative = cumulative_retained
            
     
    
    @api.depends('sieve_analysis_child_lines.wt_retained')
    def _compute_total_sieve(self):
        for record in self:
            print("recordd",record)
            record.total_sieve_analysis = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))





# Deleterious Content Material Finer than 75 Micron

    name_finer75 = fields.Char("Name",default="Material Finer than 75 Micron")
    finer75_visible = fields.Boolean("Finer 75 Visible",compute="_compute_visible")

      
    temp_finer75_visible = fields.Char(string="Temp.°C")
    humidity_finer75_visible = fields.Char(string="Humidity %")

    water_absorption_name = fields.Char("Name",default="Specific Gravity & Water Absorption")
    water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")

    wt_sample_finer75 = fields.Float("Weight of Sample in gms")
    wt_dry_sample_finer75 = fields.Float("Weight of dry sample after retained in 75 microns")
    material_finer75 = fields.Float("Material finer than 75 micron in %",compute="_compute_finer75")

    material_finer75_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
        
           ],string="Conformity", compute="_compute_material_finer75_conformity", store=True)

    @api.depends('material_finer75','eln_ref','grade')
    def _compute_material_finer75_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.material_finer75_conformity = 'na'
                continue

            
            record.material_finer75_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','988f5bf6-c865-453c-9cd6-993a5a59ad95')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','988f5bf6-c865-453c-9cd6-993a5a59ad95')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.material_finer75 - record.material_finer75*mu_value
                    upper = record.material_finer75 + record.material_finer75*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.material_finer75_conformity = 'pass'
                        break
                    else:
                        record.material_finer75_conformity = 'fail'

    material_finer75_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_material_finer75_nabl", store=True)

    @api.depends('material_finer75','eln_ref','grade')
    def _compute_material_finer75_nabl(self):
        
        for record in self:
            record.material_finer75_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','988f5bf6-c865-453c-9cd6-993a5a59ad95')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','988f5bf6-c865-453c-9cd6-993a5a59ad95')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.material_finer75 - record.material_finer75*mu_value
            upper = record.material_finer75 + record.material_finer75*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.material_finer75_nabl = 'pass'
                break
            else:
                record.material_finer75_nabl = 'fail'

    @api.depends('wt_sample_finer75','wt_dry_sample_finer75')
    def _compute_finer75(self):
        for record in self:
            if record.wt_sample_finer75 != 0:
                record.material_finer75 = ((record.wt_sample_finer75 - record.wt_dry_sample_finer75)/record.wt_sample_finer75 * 100)
            else:
                record.material_finer75 = 0


    # Specific Gravety 
    specific_gravity_name = fields.Char("Name",default="Specific Gravity & Water Absorption")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    water_absorption_name = fields.Char("Name",default="Specific Gravity & Water Absorption")
    water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")

    temp_specific_gravity_water_absorption = fields.Char(string="Temp.°C" ,required=True)
    humidity_temp_specific_gravity_water_absorption= fields.Char(string="Humidity %" ,required=True)

    # wt_basket_and_sample = fields.Float(string="Weight of basket and the sample while suspended in water (A1) gm")
    
    wt_sample_inwater = fields.Float(string="Weight of saturated surface dry sample (gm) A")
    wt_surface_dry = fields.Float(string="Weight of surface dried aggregate (B) gm")
    
    oven_dried_wt = fields.Float(string="Weight of  oven dried aggregates (C) gm")
    wt_oven_dry_d= fields.Float(string="Weight of Oven dry sample (gm) D")

 
    wt_surface_dry_2 = fields.Float(string="Weight of surface dried aggregate (B) gm [Trial 2]")
    wt_sample_inwater_2 = fields.Float(string="Weight of Saturated Aggregate  in Water (A) = (A1 – A2) – gms [Trial 2]")
    oven_dried_wt_2 = fields.Float(string="Weight of  oven dried aggregates (C) gm [Trial 2]")
    wt_oven_dry_d_2= fields.Float(string="Weight of Oven dry sample (gm) D")


    
    specific_gravity = fields.Float(string="Specific Gravity")
    water_absorption = fields.Float(string="Water absorption  %",compute="_compute_water_absorption")


    specific_gravity_1 = fields.Float(string="Specific Gravity",compute="_compute_specific_gravity_1",digits=(12,3))
    water_absorption_1 = fields.Float(string="Water absorption  %",compute="_compute_water_absorption_1")


    @api.depends('wt_oven_dry_d', 'wt_sample_inwater', 'wt_surface_dry', 'oven_dried_wt')
    def _compute_specific_gravity_1(self):
        for record in self:
            try:
                denominator = record.wt_sample_inwater - (record.wt_surface_dry - record.oven_dried_wt)
                if denominator != 0:
                    value = record.wt_oven_dry_d / denominator
                    record.specific_gravity_1 = round(value, 3)
                else:
                    record.specific_gravity_1 = 0.0
            except Exception:
                record.specific_gravity_1 = 0.0
            # line.specific_gravity_1 = round(sg1, 2)

    @api.depends('wt_sample_inwater', 'wt_oven_dry_d')
    def _compute_water_absorption_1(self):
        for record in self:
            try:
                if record.wt_oven_dry_d != 0:
                    value = 100 * ((record.wt_sample_inwater - record.wt_oven_dry_d) / record.wt_oven_dry_d)
                    record.water_absorption_1 = round(value, 3)
                else:
                    record.water_absorption_1 = 0.0
            except Exception:
                record.water_absorption_1 = 0.0

    specific_gravity_2 = fields.Float(string="Specific Gravity",compute="_compute_specific_gravity_2",digits=(12,3))
    water_absorption_2 = fields.Float(string="Water absorption  %",compute="_compute_water_absorption_2")

    @api.depends('wt_oven_dry_d_2', 'wt_sample_inwater_2', 'wt_surface_dry_2', 'oven_dried_wt_2')
    def _compute_specific_gravity_2(self):
        for record in self:
            try:
                denominator = record.wt_sample_inwater_2 - (record.wt_surface_dry_2 - record.oven_dried_wt_2)
                if denominator != 0:
                    value = record.wt_oven_dry_d_2 / denominator
                    record.specific_gravity_2 = round(value, 3)
                else:
                    record.specific_gravity_2 = 0.0
            except Exception:
                record.specific_gravity_2 = 0.0
            # line.specific_gravity_1 = round(sg1, 2)

    @api.depends('wt_sample_inwater_2', 'wt_oven_dry_d_2')
    def _compute_water_absorption_2(self):
        for record in self:
            try:
                if record.wt_oven_dry_d_2 != 0:
                    value = 100 * ((record.wt_sample_inwater_2 - record.wt_oven_dry_d_2) / record.wt_oven_dry_d_2)
                    record.water_absorption_2 = round(value, 3)
                else:
                    record.water_absorption_2 = 0.0
            except Exception:
                record.water_absorption_2 = 0.0


    avg_specific_gravity= fields.Float(string="Average Specific Gravity",compute="_compute_avg_specific_gravity")
    avg_water_absorption = fields.Float(string="Average Water Absorption-%",compute="_compute_avg_water_absorption")

    @api.depends('specific_gravity_1','specific_gravity_2')
    def _compute_avg_specific_gravity(self):
        for line in self:
            line.avg_specific_gravity = (line.specific_gravity_1 + line.specific_gravity_1)/2
    
    @api.depends('water_absorption_1','water_absorption_2')
    def _compute_avg_water_absorption(self):
        for line in self:
            line.avg_water_absorption = (line.water_absorption_1 + line.water_absorption_2)/2

    @api.depends('wt_surface_dry', 'wt_sample_inwater', 'oven_dried_wt', 'wt_surface_dry_2', 'wt_sample_inwater_2', 'oven_dried_wt_2')
    def _compute_result(self):
        for line in self:
            line.result_wt_surface_dry = (line.wt_surface_dry + line.wt_surface_dry_2)/2
            line.result_wt_sample_inwater = (line.wt_sample_inwater + line.wt_sample_inwater_2)/2
            line.result_oven_dried_wt = (line.oven_dried_wt + line.oven_dried_wt_2)/2

    avg_specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),], string="Specific Gravity Conformity", compute="_compute_avg_specific_gravity_conformity", store=True)

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_specific_gravity_conformity = 'na'
                continue


            record.avg_specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')]).parameter_table
            for material in materials:
                    
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_specific_gravity - record.avg_specific_gravity*mu_value
                    upper = record.avg_specific_gravity + record.avg_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.avg_specific_gravity_conformity = 'fail'

    avg_specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string=" Specific Gravity NABL", compute="_compute_avg_specific_gravity_nabl", store=True)

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_nabl(self):
        
        for record in self:
            record.avg_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_specific_gravity - record.avg_specific_gravity*mu_value
                    upper = record.avg_specific_gravity + record.avg_specific_gravity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_specific_gravity_nabl = 'pass'
                        break
                    else:
                        record.avg_specific_gravity_nabl = 'fail'
    

    avg_water_absorption_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
        
          ], string="Water Absorption Conformity", compute="_compute_avg_water_absorption_conformity", store=True)

    @api.depends('avg_water_absorption_conformity','eln_ref','grade')
    def _compute_avg_water_absorption_conformity(self):
        
        for record in self:

        
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_water_absorption_conformity = 'na'
                continue


            record.avg_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4dbde30b-0cdc-4641-abdd-68a574fd7e1f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4dbde30b-0cdc-4641-abdd-68a574fd7e1f')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
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
        ('fail', 'Non-NABL')], string="Water Absorption NABL", compute="_compute_avg_water_absorption_nabl", store=True)

    @api.depends('avg_water_absorption','eln_ref','grade')
    def _compute_avg_water_absorption_nabl(self):
        
        for record in self:
            record.avg_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4dbde30b-0cdc-4641-abdd-68a574fd7e1f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4dbde30b-0cdc-4641-abdd-68a574fd7e1f')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
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

      
    


# Compacted  Or Rodded Density


    compacted_density_name = fields.Char("Name",default="Compacted Density ")
    compacted_density_visible = fields.Boolean("compacted density  Visible",compute="_compute_visible")


    
    temp_density = fields.Char(string="Temp.°C" ,required=True)
    humidity_density= fields.Char(string="Humidity %" ,required=True)



    capacity_of_cylinderr = fields.Float(string="Capacity of Cylinder Use for Test in litre (V)")
    wtt_of_empty_cylinder_compacted = fields.Float(string="Weight of empty cylinder (kg)")
    wtt_cylinder_aggregate_compacted = fields.Float(string="Weight of cylinder + aggregate (kg)")
    mass_of_compacted_aggregate = fields.Float("Mass of Compacted Aggregate in Cylinder (A) – Kg",compute="_compute_mass_of_compacted_aggregate")

    compacted_density = fields.Float("Compacted Density (Ƴ1) = (A/V) Kg/lit",compute="_compute_compacted_density")

    @api.depends('wtt_cylinder_aggregate_compacted', 'wtt_of_empty_cylinder_compacted')
    def _compute_mass_of_compacted_aggregate(self):
        for rec in self:
            rec.mass_of_compacted_aggregate = rec.wtt_cylinder_aggregate_compacted - rec.wtt_of_empty_cylinder_compacted
            

    @api.depends('capacity_of_cylinderr', 'mass_of_compacted_aggregate')
    def _compute_compacted_density(self):
        for rec in self:
            if rec.capacity_of_cylinderr !=0:
              rec.compacted_density = round(rec.mass_of_compacted_aggregate / rec.capacity_of_cylinderr,2)
            else:
             rec.compacted_density = 0.0


    compacted_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
             ('na', 'NA'),
        
           ], string="Conformity", compute="_compute_compacted_density_conformity", store=True)

    @api.depends('compacted_density','eln_ref','grade')
    def _compute_compacted_density_conformity(self):
        
        for record in self:


            if not record.eln_ref or not record.eln_ref.conformity:
                record.compacted_density_conformity = 'na'
                continue
             
             
            record.compacted_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d961c78a-9f5c-4e7f-9f03-86ab65740161')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d961c78a-9f5c-4e7f-9f03-86ab65740161')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.compacted_density - record.compacted_density*mu_value
                    upper = record.compacted_density + record.compacted_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.compacted_density_conformity = 'pass'
                        break
                    else:
                        record.compacted_density_conformity = 'fail'

    compacted_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_compacted_density_nabl", store=True)

    @api.depends('compacted_density','eln_ref','grade')
    def _compute_compacted_density_nabl(self):
        
        for record in self:
            record.compacted_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d961c78a-9f5c-4e7f-9f03-86ab65740161')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d961c78a-9f5c-4e7f-9f03-86ab65740161')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.compacted_density - record.compacted_density*mu_value
                    upper = record.compacted_density + record.compacted_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.compacted_density_nabl = 'pass'
                        break
                    else:
                        record.compacted_density_nabl = 'fail'


    # Loose Density
    loose_density_name = fields.Char("Name",default="Loose Density ")
    loose_density_visible = fields.Boolean("Loose density  Visible",compute="_compute_visible")

    temp_density = fields.Char(string="Temp.°C" ,required=True)
    humidity_density= fields.Char(string="Humidity %" ,required=True)


    capacity_of_cylinder_loose = fields.Float(string="Capacity of Cylinder Use for Test in litre (V)")
    wtt_of_empty_cylinder_loose = fields.Float(string="Weight of empty cylinder (kg)")
    wtt_cylinder_aggregate_loose = fields.Float(string="Weight of cylinder + aggregate (kg)")
    mass_of_loose_aggregate = fields.Float("Mass of Loose Aggregate in Cylinder (A) – Kg",compute="_compute_mass_of_loose_aggregate")

    loose_density = fields.Float("Loose Density (Ƴ1) = (A/V) Kg/lit",compute="_compute_loose_density")

    @api.depends('wtt_cylinder_aggregate_loose', 'wtt_of_empty_cylinder_loose')
    def _compute_mass_of_loose_aggregate(self):
        for rec in self:
            rec.mass_of_loose_aggregate = rec.wtt_cylinder_aggregate_loose - rec.wtt_of_empty_cylinder_loose
            

    @api.depends('capacity_of_cylinder_loose', 'mass_of_loose_aggregate')
    def _compute_loose_density(self):
        for rec in self:
            if rec.capacity_of_cylinder_loose !=0:
              rec.loose_density = round(rec.mass_of_loose_aggregate / rec.capacity_of_cylinder_loose,2)
            else:
             rec.loose_density = 0.0


    loose_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
        
    ], string="Conformity", compute="_compute_loose_density_conformity", store=True)

    @api.depends('loose_density','eln_ref','grade')
    def _compute_loose_density_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.loose_density_conformity = 'na'
                continue
              

            record.loose_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8a944a9b-4d7d-44a3-a82c-6d8bacc07846')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8a944a9b-4d7d-44a3-a82c-6d8bacc07846')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.loose_density - record.loose_density*mu_value
                    upper = record.loose_density + record.loose_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.loose_density_conformity = 'pass'
                        break
                    else:
                        record.loose_density_conformity = 'fail'

    loose_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_loose_density_nabl", store=True)

    @api.depends('loose_density','eln_ref','grade')
    def _compute_loose_density_nabl(self):
        
        for record in self:
            record.loose_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8a944a9b-4d7d-44a3-a82c-6d8bacc07846')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8a944a9b-4d7d-44a3-a82c-6d8bacc07846')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.loose_density - record.loose_density*mu_value
                    upper = record.loose_density + record.loose_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.loose_density_nabl = 'pass'
                        break
                    else:
                        record.loose_density_nabl = 'fail'
                        
                        


    # Void Loose density And Void Compacted Density

    voids_loose_and_compacted_name = fields.Char("Name",default="Void In Compacted Density & Voids In Loose Density ")
    # void_loose_compacted_visible = fields.Boolean("Void In Compacted Density & Voids In Loose Density ",compute="_compute_visible")

    voids_compacted_density_name = fields.Char("Name",default="Void In Compacted Density ")
    voids_compacted_density_visible = fields.Boolean("Void In Compacted Visible",compute="_compute_visible")


    temp_density = fields.Char(string="Temp.°C" ,required=True)
    humidity_density= fields.Char(string="Humidity %",required=True)


    voids_loose_density_name = fields.Char("Name",default="Void In Loose Density ")
    voids_loose_density_visible = fields.Boolean("Void Loose density Visible",compute="_compute_visible")

    specific_gravity_voids = fields.Float(string="Sp. Gravity of Material (Gs)")

    voids_compacted_density = fields.Float(string="Percent Voids in Compacted Density = (Gs - Ƴ1 )/Gs x 100",compute="_compute_voids_compacted_density")
    voids_loose_density = fields.Float(string="Percent Voids in Loose Density = (Gs – Ƴ2 )/Gs x 100",compute="_compute_voids_loose_density")






    @api.depends('specific_gravity_voids', 'compacted_density')
    def _compute_voids_compacted_density(self):
        for rec in self:
            if rec.specific_gravity_voids !=0:
              rec.voids_compacted_density = round(((rec.specific_gravity_voids - rec.compacted_density)/rec.specific_gravity_voids * 100),2)
            else:
             rec.voids_compacted_density = 0.0
             

    @api.depends('specific_gravity_voids', 'loose_density')
    def _compute_voids_loose_density(self):
        for rec in self:
            if rec.specific_gravity_voids !=0:
              rec.voids_loose_density = round(((rec.specific_gravity_voids - rec.loose_density)/rec.specific_gravity_voids * 100),2)
            else:
             rec.voids_loose_density = 0.0  


    voids_compacted_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
             ('na', 'NA'),
        
    ],string="Void In Compacted Density Conformity", compute="_compute_voids_compacted_density_conformity", store=True)

    @api.depends('voids_compacted_density','eln_ref','grade')
    def _compute_voids_compacted_density_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.voids_compacted_density_conformity = 'na'
                continue
              
            record.voids_compacted_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.voids_compacted_density - record.voids_compacted_density*mu_value
                    upper = record.voids_compacted_density + record.voids_compacted_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.voids_compacted_density_conformity = 'pass'
                        break
                    else:
                        record.voids_compacted_density_conformity = 'fail'

    voids_compacted_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Void In Compacted Density NABL", compute="_compute_voids_compacted_density_nabl", store=True)

    @api.depends('voids_compacted_density','eln_ref','grade')
    def _compute_voids_compacted_density_nabl(self):
        
        for record in self:
            record.voids_compacted_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.voids_compacted_density - record.voids_compacted_density*mu_value
                    upper = record.voids_compacted_density + record.voids_compacted_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.voids_compacted_density_nabl = 'pass'
                        break
                    else:
                        record.voids_compacted_density_nabl = 'fail'  

    voids_loose_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
        ('na', 'NA'),
        
    ],string="Void In Loose Density Conformity", compute="_compute_voids_loose_density_conformity", store=True)

    @api.depends('voids_loose_density','eln_ref','grade')
    def _compute_voids_loose_density_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.voids_loose_density_conformity = 'na'
                continue


            record.voids_loose_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.voids_loose_density - record.voids_loose_density*mu_value
                    upper = record.voids_loose_density + record.voids_loose_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.voids_loose_density_conformity = 'pass'
                        break
                    else:
                        record.voids_loose_density_conformity = 'fail'

    voids_loose_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Void In Loose Density NABL", compute="_compute_voids_loose_density_nabl", store=True)

    @api.depends('voids_loose_density','eln_ref','grade')
    def _compute_voids_loose_density_nabl(self):
        
        for record in self:
            record.voids_loose_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.voids_loose_density - record.voids_loose_density*mu_value
                    upper = record.voids_loose_density + record.voids_loose_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.voids_loose_density_nabl = 'pass'
                        break
                    else:
                        record.voids_loose_density_nabl = 'fail'






    #  Soudness Test 
    soudness_name = fields.Char("Name",default="Soudness Test ")
    soudness_visible = fields.Boolean("Soudness Test",compute="_compute_visible")
    magnesium_visible = fields.Boolean("Soudness Test",compute="_compute_visible")

    soudness_child_lines = fields.One2many('fine.soudness.line','parent_id',string="Parameter")

    
    temp_soudness = fields.Char(string="Temp.°C" ,required=True)
    humidity_soudness = fields.Char(string="Humidity %" ,required=True)



    sieve_name = fields.Char("Name",default="Gradation of Sample")
  
    wt_of_sample = fields.Float(string="Wt. Of Sample Taken For Analysis (gms) = ", digits=(8,3))
 
    sieve_analysis_soundness_lines = fields.One2many('mechanical.soudness.sieve.analysis.line','parent_id',string="Sieve Analysis",default=lambda self: self._default_sieve_analysis_soundness_lines())

    total_percent_retained = fields.Float(
        string="Total % Retained",
        compute="_compute_total_percent_retained",
        store=True
    )

    @api.depends('sieve_analysis_soundness_lines.percent_retained')
    def _compute_total_percent_retained(self):
        for rec in self:
            rec.total_percent_retained = sum(
                line.percent_retained for line in rec.sieve_analysis_soundness_lines
            )

    
    @api.model
    def _default_sieve_analysis_soundness_lines(self):
        default_lines = [
            (0, 0, {'sieve_size': '10', 'particle_size': '4.75'}),
            (0, 0, {'sieve_size': '4.75', 'particle_size': '2.36'}),
            (0, 0, {'sieve_size': '2.36', 'particle_size': '1.18'}),
            (0, 0, {'sieve_size': '1.18', 'particle_size': '0.6'}),
            (0, 0, {'sieve_size': '0.6', 'particle_size': '0.3'}),
            (0, 0, {'sieve_size': '0.3', 'particle_size': '0.15'}),
            (0, 0, {'sieve_size': '0.15', 'particle_size': 'Pan'}),
        ]
        return default_lines



    def calculate_sieve(self): 
        for record in self:

            record.calc_mode = True
            record.submit_mode = False

            previous_cumulative = 0  
            for line in record.sieve_analysis_soundness_lines:
                print("Rows", str(line.percent_retained))
                previous_line = line.serial_no - 1

               
                # Normal sieve calculation
                if previous_line == 0:
                    cumulative_retained = line.percent_retained
                else:
                    previous_line_record = self.env['mechanical.soudness.sieve.analysis.line'].sudo().search([
                        ("serial_no", "=", previous_line),
                        ("parent_id", "=", record.id)
                    ], limit=1)
                    
                    if previous_line_record:
                        previous_cumulative = previous_line_record.cumulative_retained
                    cumulative_retained = previous_cumulative + line.percent_retained

                passing_percent = 100 - cumulative_retained

                # Write updated values
                line.write({
                    'cumulative_retained': round(cumulative_retained, 2),
                    'passing_percent': round(passing_percent, 2),
                })

                print("Updated Cumulative Retained:", cumulative_retained)
                print("Updated Passing Percent:", passing_percent)

                previous_cumulative = cumulative_retained


    ouantitative_name = fields.Char("Name",default="Quantitatively Examination :-")

    ouantitative_soundness_lines = fields.One2many('fine.ouantitative.line','parent_id',string="Sieve Analysis",default=lambda self: self._default_ouantitative_soundness_lines())

    
    @api.model
    def _default_ouantitative_soundness_lines(self):
        default_lines = [
            (0, 0, {'size': '10mm to 4.75mm'}),
            (0, 0, {'size': '4.75mm to 2.36mm'}),
            (0, 0, {'size': '2.36mm to 1.18mm'}),
            (0, 0, {'size': '1.18mm to 0.6mm'}),
            (0, 0, {'size': '0.6mm to 0.3mm'})
            
        ]
        return default_lines


    quantitative_name = fields.Char("Name",default="Quantitatively Examination")

    quantitative_soundness_lines = fields.One2many('fine.quantitative.line','parent_id',string="Sieve Analysis",default=lambda self: self._default_quantitative_soundness_lines())

    
    @api.model
    def _default_quantitative_soundness_lines(self):
        default_lines = [
            (0, 0, {'passing': '10mm', 'retained': '4.75mm', 'sieve_magnesium':'4.75mm'}),
            (0, 0, {'passing': '4.75mm', 'retained': '2.36mm' , 'sieve_magnesium':'2.36mm'}),
            (0, 0, {'passing': '2.36mm', 'retained': '1.18mm', 'sieve_magnesium':'1.18mm'}),
            (0, 0, {'passing': '1.18mm', 'retained': '0.6mm', 'sieve_magnesium':'0.6mm'}),
            (0, 0, {'passing': '0.6mm', 'retained': '0.3mm', 'sieve_magnesium':'0.3mm'}),
            (0, 0, {'passing': '0.3mm', 'retained': '0.15mm', 'sieve_magnesium':'0.15mm'}),
            (0, 0, {'passing': '0.15mm', 'retained': 'Pan', 'sieve_magnesium':'pan'}),
        ]
        return default_lines


    total_grading_sulphate = fields.Float(string="Total Grading of Original Sample  (%)s.Sodium Sulphate", digits=(8,2),compute="_compute_total_grading_sulphate",store=True)

    total_finalloss_sulphae= fields.Float(string="Total Final loss (%) Sulphate", digits=(8,2),compute="_compute_total_finalloss_sulphae",store=True)

    total_final_loss_manesium= fields.Float(string="Total Final loss (%) Magnesium", digits=(8,2),compute="_compute_total_final_loss_manesium",store=True)

    total_wt_fraction_sulhate= fields.Float(string="Total Weight of test Fraction  (retained) after test (gm) Sodium Sulphate", digits=(8,2),compute="_compute_total_wt_fraction_sulhate",store=True)

    total_wt_fraction_manesium= fields.Float(string="Total Weight of test Fraction  (retained) after test  (gm) Magnesium ", digits=(8,2),compute="_compute_total_wt_fraction_manesium",store=True)

    total_avg_sulphae= fields.Float(string="Total Weighted Average  (Corrected % loss) Sulphate", digits=(8,2),compute="_compute_total_avg_sulphae",store=True)

    total_avg_manesium= fields.Float(string="Total Weighted Average  (Corrected % loss) Magnesium ", digits=(8,2),compute="_compute_total_avg_manesium",store=True)




    @api.depends('quantitative_soundness_lines.grading_sulphate')
    def _compute_total_grading_sulphate(self):
        for record in self:
            record.total_grading_sulphate = sum(record.quantitative_soundness_lines.mapped('grading_sulphate'))


    @api.depends('quantitative_soundness_lines.finalloss_sulphae')
    def _compute_total_finalloss_sulphae(self):
        for record in self:
            record.total_finalloss_sulphae = sum(record.quantitative_soundness_lines.mapped('finalloss_sulphae'))

    @api.depends('quantitative_soundness_lines.final_loss_manesium')
    def _compute_total_final_loss_manesium(self):
        for record in self:
            record.total_final_loss_manesium = sum(record.quantitative_soundness_lines.mapped('final_loss_manesium'))

    @api.depends('quantitative_soundness_lines.wt_fraction_sulhate')
    def _compute_total_wt_fraction_sulhate(self):
        for record in self:
            record.total_wt_fraction_sulhate = sum(record.quantitative_soundness_lines.mapped('wt_fraction_sulhate'))
            
    @api.depends('quantitative_soundness_lines.wt_fraction_manesium')
    def _compute_total_wt_fraction_manesium(self):
        for record in self:
            record.total_wt_fraction_manesium = sum(record.quantitative_soundness_lines.mapped('wt_fraction_manesium'))

    @api.depends('quantitative_soundness_lines.avg_sulphae')
    def _compute_total_avg_sulphae(self):
        for record in self:
            record.total_avg_sulphae = sum(record.quantitative_soundness_lines.mapped('avg_sulphae'))



    @api.depends('quantitative_soundness_lines.avg_manesium')
    def _compute_total_avg_manesium(self):
        for record in self:
            record.total_avg_manesium = sum(record.quantitative_soundness_lines.mapped('avg_manesium'))


    total_avg_sulphae_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
             ('na', 'NA'),
        
    ], string="Conformity", compute="_compute_total_avg_sulphae_conformity", store=True)

    @api.depends('total_avg_sulphae','eln_ref','grade')
    def _compute_total_avg_sulphae_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.total_avg_sulphae_conformity = 'na'
                continue
            
            record.total_avg_sulphae_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c8cd69bd-1f89-4f22-bae6-b81de73e6c2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c8cd69bd-1f89-4f22-bae6-b81de73e6c2')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.total_avg_sulphae - record.total_avg_sulphae*mu_value
                    upper = record.total_avg_sulphae + record.total_avg_sulphae*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.total_avg_sulphae_conformity = 'pass'
                        break
                    else:
                        record.total_avg_sulphae_conformity = 'fail'

    total_avg_sulphae_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')],
        
    string="NABL", compute="_compute_total_avg_sulphae_nabl", store=True)

    @api.depends('total_avg_sulphae','eln_ref','grade')
    def _compute_total_avg_sulphae_nabl(self):
        
        for record in self:

            
            record.total_avg_sulphae_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c8cd69bd-1f89-4f22-bae6-b81de73e6c2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c8cd69bd-1f89-4f22-bae6-b81de73e6c2')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.total_avg_sulphae - record.total_avg_sulphae*mu_value
                    upper = record.total_avg_sulphae + record.total_avg_sulphae*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.total_avg_sulphae_nabl = 'pass'
                        break
                    else:
                        record.total_avg_sulphae_nabl = 'fail'



    @api.depends('total_avg_manesium','eln_ref','grade')
    def _compute_total_avg_manesium_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.total_avg_manesium_conformity = 'na'
                continue
            
            record.total_avg_manesium_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ff9f86ce-1f7a-4e3f-83b4-284a413745df')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ff9f86ce-1f7a-4e3f-83b4-284a413745df')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.total_avg_manesium - record.total_avg_manesium*mu_value
                    upper = record.total_avg_manesium + record.total_avg_manesium*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.total_avg_manesium_conformity = 'pass'
                        break
                    else:
                        record.total_avg_manesium_conformity = 'fail'

    total_avg_manesium_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')],
        
    string="NABL", compute="_compute_total_avg_manesium_nabl", store=True)

    @api.depends('total_avg_manesium','eln_ref','grade')
    def _compute_total_avg_manesium_nabl(self):
        
        for record in self:

            
            record.total_avg_manesium_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ff9f86ce-1f7a-4e3f-83b4-284a413745df')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ff9f86ce-1f7a-4e3f-83b4-284a413745df')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.total_avg_manesium - record.total_avg_manesium*mu_value
                    upper = record.total_avg_manesium + record.total_avg_manesium*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.total_avg_manesium_nabl = 'pass'
                        break
                    else:
                        record.total_avg_manesium_nabl = 'fail'



     ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
      
            record.sieve_visible = False
            record.specific_gravity_visible = False
            record.water_absorption_visible = False
            record.loose_density_visible = False
           
            record.finer75_visible = False
            record.compacted_density_visible = False
            record.voids_compacted_density_visible = False
            record.voids_loose_density_visible = False
            record.soudness_visible = False
            record.magnesium_visible = False
            
           
          
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
               
                if sample.internal_id == "318d72a1-7188-4086-b132-62b50e63f5d1":
                    record.sieve_visible = True

                if sample.internal_id == "4dbde30b-0cdc-4641-abdd-68a574fd7e1f":
                    record.water_absorption_visible = True

                if sample.internal_id == "45875ght-7188-4086-b132-62b50e63f1245gt":
                    record.specific_gravity_visible = True

                if sample.internal_id == "4587tyhloos-3fa3-4b83-ae31-9d281767188c":
                    record.loose_density_visible = True
                    

                if sample.internal_id == '988f5bf6-c865-453c-9cd6-993a5a59ad95':
                    record.finer75_visible = True
                
                if sample.internal_id == 'd961c78a-9f5c-4e7f-9f03-86ab65740161':
                    record.compacted_density_visible  = True

                if sample.internal_id == 'a699d9fd-57f5-4044-97ea-2bea87bf9c44':
                    record.voids_compacted_density_visible = True
                
                if sample.internal_id == '8a944a9b-4d7d-44a3-a82c-6d8bacc07846':
                    record.voids_loose_density_visible = True

                if sample.internal_id == 'a0e7aaf3-68ff-4e75-830d-91ae04c98f5796':
                    record.soudness_visible = True
                
                if sample.internal_id == 'ff9f86ce-1f7a-4e3f-83b4-284a413745df':
                    record.magnesium_visible = True

              


    def open_eln_page(self):

        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
                lambda r: r.technician == current_user
            )

        for result in technician_results:
            internal_id = result.parameter.internal_id

            # Sieve analysis
            if internal_id == "318d72a1-7188-4086-b132-62b50e63f5d1":
                result.calculated = True

            # Specific gravity
            elif internal_id == "45875ght-7188-4086-b132-62b50e63f1245gt":
                result.calculated = True

            # Water absorption
            elif internal_id == "4dbde30b-0cdc-4641-abdd-68a574fd7e1f":
                result.result_char = round(self.avg_water_absorption, 2)
                result.calculated = True
                result.nabl_status = (
                    'nabl' if self.avg_water_absorption_nabl == 'pass' else 'non-nabl'
                )

            # Loose density
            elif internal_id == "4587tyhloos-3fa3-4b83-ae31-9d281767188c":
                result.result_char = round(self.loose_density, 2)
                result.calculated = True
                result.nabl_status = (
                    'nabl' if self.loose_density_nabl == 'pass' else 'non-nabl'
                )

            # Finer than 75 micron
            elif internal_id == "988f5bf6-c865-453c-9cd6-993a5a59ad95":
                result.calculated = True

            # Compacted density
            elif internal_id == "d961c78a-9f5c-4e7f-9f03-86ab65740161":
                result.result_char = round(self.compacted_density, 2)
                result.calculated = True
                result.nabl_status = (
                    'nabl' if self.compacted_density_nabl == 'pass' else 'non-nabl'
                )

            # Voids – compacted density
            elif internal_id == "a699d9fd-57f5-4044-97ea-2bea87bf9c44":
                result.calculated = True

            # Voids – loose density
            elif internal_id == "8a944a9b-4d7d-44a3-a82c-6d8bacc07846":
                result.calculated = True

            # Soundness
            elif internal_id == "a0e7aaf3-68ff-4e75-830d-91ae04c98f5796":
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
        record = super(FineAggregate, self).create(vals)
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
        record = self.env['mechanical.fine.aggregate'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id




class SieveAnalysisLine(models.Model):
    _name = "mechanical.fine.agg.sieve.analysis.ssl.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size")
    wt_retained = fields.Float(string="Wt. Retained in gms",digits=(12,3))
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained",digits=(12,3))
    cumulative_retained = fields.Float(string="Cum. Retained %", compute="_compute_cum_retained", store=True,digits=(12,3))
    passing_percent = fields.Float(string="Passing %",digits=(12,3))
    specific_limt = fields.Char(string="Specified Limits")

    blue_input = fields.Boolean(default=True,invisible=True)



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SieveAnalysisLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

    def write(self, vals):
        # Handle row deletions and adjust serial numbers
        if 'parent_id' in vals or 'wt_retained' in vals:
            for record in self:
                if record.parent_id and record.parent_id == vals.get('parent_id') and 'wt_retained' in vals:
                    record.percent_retained = vals['wt_retained'] / record.parent_id.total * 100 if record.parent_id.total else 0

            new_self = super(SieveAnalysisLine, self).write(vals)

            if 'wt_retained' in vals:
                for record in self:
                    # record.parent_id._compute_total()
                    pass

            return new_self

        return super(SieveAnalysisLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(SieveAnalysisLine, self).unlink()

        if parent_id:
            parent_id.sieve_analysis_child_lines._reorder_serial_numbers()

        return res



    @api.depends('wt_retained', 'parent_id.wt_of_sample')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = (record.wt_retained / record.parent_id.wt_of_sample) * 100 if record.parent_id.wt_of_sample else 0.0
            except ZeroDivisionError:
                record.percent_retained = 0.0





    @api.depends('percent_retained', 'parent_id.sieve_analysis_child_lines.percent_retained')
    def _compute_cum_retained(self):
        for record in self:
            cumulative = 0.0
            found = False

            for line in sorted(record.parent_id.sieve_analysis_child_lines, key=lambda l: l.serial_no):
                cumulative += line.percent_retained or 0.0
                if line.id == record.id:
                    found = True
                    record.cumulative_retained = cumulative
                    break

            if not found:
                record.cumulative_retained = 0.0




    def get_previous_record(self):
        for record in self:
           
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines, key=lambda r: r.id)
      



class SpecificAndWaterLine(models.Model):
    _name = "fine.specific.and.water.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    wt_of_staurated_a = fields.Float(string="Wt of Saturated surface dry  Aggregate in Air:- (A)")
    wt_of_pycnometer_b = fields.Float(string="Wt of Pycnometer containing sample and Water:- (B)")
    wt_of_pycnometer_c = fields.Float(string="Wt of Pycnometer containing Water:- (C)")
    wt_of_oven_d = fields.Float(string="Wt of Oven Dried Aggregate :- ( D )")
    blue_input = fields.Boolean(default=True,invisible=True)

 

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SpecificAndWaterLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class SoudnessLine(models.Model):
    _name = "fine.soudness.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    serial_no = fields.Integer(string="Cycle No", readonly=True, copy=False, default=1)

    immersed_datetime = fields.Datetime(string="Date & Time of Sample immersed in Solution for 16 to 18 hrs.")
    temp_solution = fields.Float(string="Temp. of Solution (°C)", digits=(6,2))
    specific_gravity_solution = fields.Float(string="Specific Gravity of Solution", digits=(8,3))
    removed_datetime = fields.Datetime(string="Date & Time of Sample Removed from Solution")
    oven_datetime = fields.Datetime(string="Date & Time of Sample Kept in Oven (105 to 1100C) for Drying ")

    hours_1 = fields.Char(string="Hours 1",compute="_compute_hours_1",store=True)
    hours_2 = fields.Char(string="Hours 2",compute="_compute_hours_2",store=True)
    hours_3 = fields.Char(string="Hours 3",compute="_compute_hours_3",store=True)
    blue_input = fields.Boolean(default=True,invisible=True)

    @api.depends('oven_datetime', 'parent_id.soudness_child_lines.immersed_datetime')
    def _compute_hours_1(self):
        """
        Compute hours_1 = (Next line's immersed_datetime) - (Current line's oven_datetime)
        """
        for rec in self:
            rec.hours_1 = False
            if not rec.oven_datetime or not rec.parent_id:
                continue

            lines = rec.parent_id.soudness_child_lines.sorted(key=lambda l: l.serial_no)
            line_list = list(lines)

            if rec in line_list:
                current_index = line_list.index(rec)
                # check next line exists
                if current_index + 1 < len(line_list):
                    next_line = line_list[current_index + 1]
                    if next_line.immersed_datetime:
                        diff = next_line.immersed_datetime - rec.oven_datetime
                        total_seconds = diff.total_seconds()
                        if total_seconds > 0:
                            hours = int(total_seconds // 3600)
                            minutes = int((total_seconds % 3600) // 60)
                            seconds = int(total_seconds % 60)
                            rec.hours_1 = f"{hours:02}:{minutes:02}:{seconds:02}"
                        else:
                            rec.hours_1 = "00:00:00"

    # ---------------- HOURS 2 -----------------
    @api.depends('immersed_datetime', 'removed_datetime')
    def _compute_hours_2(self):
        """Compute Hours 2 = removed_datetime - immersed_datetime"""
        for rec in self:
            rec.hours_2 = False
            if rec.immersed_datetime and rec.removed_datetime:
                diff = rec.removed_datetime - rec.immersed_datetime
                total_seconds = diff.total_seconds()
                if total_seconds > 0:
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    seconds = int(total_seconds % 60)
                    rec.hours_2 = f"{hours:02}:{minutes:02}:{seconds:02}"
                else:
                    rec.hours_2 = "00:00:00"


    @api.depends('removed_datetime', 'oven_datetime')
    def _compute_hours_3(self):
        """Compute Hours 2 = oven_datetime - removed_datetime"""
        for rec in self:
            rec.hours_3 = False
            if rec.removed_datetime and rec.oven_datetime:
                diff = rec.oven_datetime - rec.removed_datetime
                total_seconds = diff.total_seconds()
                if total_seconds > 0:
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    seconds = int(total_seconds % 60)
                    rec.hours_3 = f"{hours:02}:{minutes:02}:{seconds:02}"
                else:
                    rec.hours_3 = "00:00:00"

    



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SoudnessLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class SieveAnalysisSoudnesLine(models.Model):
    _name = "mechanical.soudness.sieve.analysis.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size")
    particle_size = fields.Char(string="Retained")
    wt_retained = fields.Float(string="Wt. Retained before test(gm)")
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained")
    wt_sample_testing = fields.Char(string="Weight of sample for testing (gm)",compute="_compute_wt_sample_testing_display")
    actual_wt = fields.Float(string="Actual Weight of sample taken (gm)")
    cumulative_retained = fields.Float(string="Cum. Retained %",compute="_compute_cum_retained" , store=True)
    passing_percent = fields.Float(string="% Passing ")
    blue_input = fields.Boolean(default=True,invisible=True)


    @api.depends('percent_retained')
    def _compute_wt_sample_testing_display(self):
        for rec in self:
            if rec.percent_retained < 5:
                rec.wt_sample_testing = "-"
            else:
                rec.wt_sample_testing = "100"


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SieveAnalysisSoudnesLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

    def write(self, vals):
        # Handle row deletions and adjust serial numbers
        if 'parent_id' in vals or 'wt_retained' in vals:
            for record in self:
                if record.parent_id and record.parent_id == vals.get('parent_id') and 'wt_retained' in vals:
                    record.percent_retained = vals['wt_retained'] / record.parent_id.total * 100 if record.parent_id.total else 0

            new_self = super(SieveAnalysisSoudnesLine, self).write(vals)

            if 'wt_retained' in vals:
                for record in self:
                    # record.parent_id._compute_total()
                    pass

            return new_self

        return super(SieveAnalysisSoudnesLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(SieveAnalysisSoudnesLine, self).unlink()

        if parent_id:
            parent_id.sieve_analysis_soundness_lines._reorder_serial_numbers()

        return res


    @api.depends('wt_retained', 'parent_id.wt_of_sample')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = (record.wt_retained / record.parent_id.wt_of_sample) * 100 if record.parent_id.wt_of_sample else 0.0
            except ZeroDivisionError:
                record.percent_retained = 0.0



    # @api.depends('cumulative_retained')
    # def _compute_cum_retained(self):
    #     self.cumulative_retained=0

    @api.depends('percent_retained', 'parent_id.sieve_analysis_soundness_lines.percent_retained')
    def _compute_cum_retained(self):
        for record in self:
            cumulative = 0.0
            found = False

            for line in sorted(record.parent_id.sieve_analysis_soundness_lines, key=lambda l: l.serial_no):
                cumulative += line.percent_retained or 0.0
                if line.id == record.id:
                    found = True
                    record.cumulative_retained = cumulative
                    break

            if not found:
                record.cumulative_retained = 0.0

        
    


    def get_previous_record(self):
        for record in self:
        
            sorted_lines = sorted(record.parent_id.sieve_analysis_soundness_lines, key=lambda r: r.id)
           

class OuantitativelyExaminationLine(models.Model):
    _name = "fine.ouantitative.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    serial_no = fields.Integer(string="Cycle No", readonly=True, copy=False, default=1)

    size = fields.Char(string="Size")
    cycle = fields.Float(string="Test Cycle ")
    original_sulphate = fields.Float(string="Original wt. of Sample-gms.Sodium Sulphate", digits=(8,3),compute="_compute_original_sulphate",store=True)
    original_magnesiu = fields.Float(string="Original wt. of Sample-gms.Magnesium ", digits=(8,3))
    wt_sulhate = fields.Float(string="Weight Retained After  5 Cycle-gms Sodium Sulphate")
    wt_manesium = fields.Float(string="Weight Retained After  5 Cycle-gms Magnesium ")
    loss_sulphae = fields.Float(string="% Loss Sodium Sulphate",compute="_compute_loss_sulphae",digits=(12,1))
    loss_manesium = fields.Float(string="% Loss Magnesium ")
    blue_input = fields.Boolean(default=True,invisible=True)

    @api.depends('serial_no', 'parent_id.sieve_analysis_soundness_lines')
    def _compute_original_sulphate(self):
        for rec in self:
            rec.original_sulphate = 0.0
            if rec.parent_id and rec.serial_no:
                line = rec.parent_id.sieve_analysis_soundness_lines.filtered(
                    lambda l: l.serial_no == rec.serial_no
                )
                # Take only the first matching line to avoid singleton error
                if line:
                    rec.original_sulphate = line[0].actual_wt or 0.0

    @api.depends('original_sulphate', 'wt_sulhate')
    def _compute_loss_sulphae(self):
        """Compute % Loss Sodium Sulphate"""
        for rec in self:
            if not rec.original_sulphate or rec.wt_sulhate == 0:
                rec.loss_sulphae = 0.0
            else:
                rec.loss_sulphae = round(((rec.original_sulphate - rec.wt_sulhate) / rec.wt_sulhate) * 100, 2)


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(OuantitativelyExaminationLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class QuantitativelyExaminationLine(models.Model):
    _name = "fine.quantitative.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    serial_no = fields.Integer(string="Cycle No", readonly=True, copy=False, default=1)

    passing = fields.Char(string="Sieve Size-mm Passing")
    retained = fields.Char(string="Sieve Size-mm Retained")
    grading_sulphate = fields.Float(string="Grading of Original Sample  (%)s.Sodium Sulphate", digits=(8,2),compute="_compute_grading_sulphate",store=True)
    sieve_magnesium = fields.Char(string="Sieve Used For Loss  Determination.Magnesium ")
    wt_fraction_sulhate = fields.Float(string="Weight of test Fraction  (retained) after test (gm) Sodium Sulphate",compute="_compute_wt_fraction_sulhate",store=True)
    wt_fraction_manesium = fields.Float(string="Weight of test Fraction  (retained) after test  (gm) Magnesium ")
    finalloss_sulphae = fields.Float(string="Final loss (%) Sulphate",compute="_compute_finalloss_sulphae",store="_compute_finalloss_sulphae")
    final_loss_manesium = fields.Float(string="Final loss (%) Magnesium ")

    avg_sulphae = fields.Float(string="Weighted Average  (Corrected % loss) Sulphate",compute="_compute_avg_sulphae",store=True)
    avg_manesium = fields.Float(string="Weighted Average  (Corrected % loss) Magnesium ")
    blue_input = fields.Boolean(default=True,invisible=True)

    @api.depends('finalloss_sulphae', 'grading_sulphate')
    def _compute_avg_sulphae(self):
        for rec in self:
            rec.avg_sulphae = (rec.finalloss_sulphae * rec.grading_sulphate) / 100 if rec.grading_sulphate else 0.0





    @api.depends('parent_id.sieve_analysis_soundness_lines', 'parent_id.ouantitative_soundness_lines')
    def _compute_finalloss_sulphae(self):
      for rec in self:
        sieve_lines = rec.parent_id.sieve_analysis_soundness_lines.sorted('serial_no')
        quant_lines = rec.parent_id.ouantitative_soundness_lines.sorted('serial_no')
        percent_ret = 0.0
        loss_sulphae_val = 0.0

        # Find matching line based on serial_no
        sieve_line = next((l for l in sieve_lines if l.serial_no == rec.serial_no), None)
        quant_line = next((l for l in quant_lines if l.serial_no == rec.serial_no), None)

        if sieve_line:
            percent_ret = sieve_line.percent_retained
        if quant_line:
            loss_sulphae_val = quant_line.loss_sulphae

        # Determine index of current line in quant_lines (if exists)
        quant_index = next((i for i, l in enumerate(quant_lines) if l.serial_no == rec.serial_no), None)

        if quant_index is not None:
            prev_loss_val = quant_lines[quant_index - 1].loss_sulphae if quant_index > 0 else None
            next_loss_val = quant_lines[quant_index + 1].loss_sulphae if quant_index + 1 < len(quant_lines) else None

            if quant_index == 0:  # First item
                avg_val = next_loss_val or loss_sulphae_val
            elif quant_index == len(quant_lines) - 1:  # Last item
                avg_val = prev_loss_val or loss_sulphae_val
            else:  # Middle
                if prev_loss_val is not None and next_loss_val is not None:
                    avg_val = (prev_loss_val + next_loss_val) / 2
                else:
                    avg_val = loss_sulphae_val
        else:
            avg_val = loss_sulphae_val

        # Apply condition
        rec.finalloss_sulphae = avg_val if 0 < percent_ret < 5 else loss_sulphae_val






    @api.depends('serial_no', 'parent_id.sieve_analysis_soundness_lines')
    def _compute_grading_sulphate(self):
        for rec in self:
            rec.grading_sulphate = 0.0
            if rec.parent_id and rec.serial_no:
                line = rec.parent_id.sieve_analysis_soundness_lines.filtered(
                    lambda l: l.serial_no == rec.serial_no
                )
                if line:
                    # Take the first matching record to avoid singleton error
                    rec.grading_sulphate = line[0].percent_retained or 0.0

    @api.depends('serial_no', 'parent_id.ouantitative_soundness_lines')
    def _compute_wt_fraction_sulhate(self):
        for rec in self:
            rec.wt_fraction_sulhate = 0.0
            if rec.parent_id and rec.serial_no:
                line = rec.parent_id.ouantitative_soundness_lines.filtered(
                    lambda l: l.serial_no == rec.serial_no
                )
                if line:
                    # Safely pick the first record to avoid singleton issue
                    rec.wt_fraction_sulhate = line[0].wt_sulhate or 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(QuantitativelyExaminationLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class fineNotes(models.Model):
    _name = "fine.notes"

    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")



            



