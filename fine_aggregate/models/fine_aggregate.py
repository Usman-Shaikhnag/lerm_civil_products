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

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'fine.aggregate.prefill.data',
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
            # rec.average_crushing_value_unit = rec._get_unit("ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71")
            # rec.average_impact_value_unit = rec._get_unit("2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2")
            rec.avg_compacted_unit     = rec._get_unit("357f579d-a310-4015-bc11-28a85c53ac83")
            # rec.avg_bulk_density_unit   = rec._get_unit("65a41d1f-d557-438e-8fd1-2c619a334d02")
            # rec.aggregate_elongation_unit   = rec._get_unit("9effe915-e5a3-45a7-aaeb-10caababd667")
            # rec.aggregate_flakiness_unit   = rec._get_unit("be7a60bc-bb2c-410d-b91a-4f8730a4ac6f")
            # rec.avg_specific_gravity_unit   = rec._get_unit("3114db41-cfa7-49ad-9324-fcdbc9661038")
            # rec.avg_water_absorption_unit   = rec._get_unit("22ee804f-41a3-4fd1-a301-a8d9180fba10")

    # ---- default values (create mode मध्ये दिसण्यासाठी)
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res.update({
            # 'average_crushing_value_unit':   self._get_unit("ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71"),
            # 'average_impact_value_unit': self._get_unit("2bd241bd-4bc3-4fe0-bea2-c1c15ff867a2"),
            'avg_compacted_unit':     self._get_unit("357f579d-a310-4015-bc11-28a85c53ac83"),
            # 'avg_bulk_density_unit':   self._get_unit("65a41d1f-d557-438e-8fd1-2c619a334d02"),
            # 'aggregate_elongation_unit':   self._get_unit("9effe915-e5a3-45a7-aaeb-10caababd667"),
            # 'aggregate_flakiness_unit':   self._get_unit("be7a60bc-bb2c-410d-b91a-4f8730a4ac6f"),
            # 'avg_specific_gravity_unit':   self._get_unit("3114db41-cfa7-49ad-9324-fcdbc9661038"),
            # 'avg_water_absorption_unit':   self._get_unit("22ee804f-41a3-4fd1-a301-a8d9180fba10"),
        })
        return res

  


    # Sieve Analysis 
    sieve_analysis_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

    sieve_analysis_child_lines = fields.One2many('mechanical.fine.agg.sieve.analysis.line','parent_id',string="Parameter",default=lambda self: self._default_sieve_analysis_child_lines())
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



    # @api.depends('sieve_analysis_child_lines.cumulative_retained')
    # def _compute_fineness_modulus(self):
    #     for record in self:
    #         fineness_modulus = sum(line.cumulative_retained for line in record.sieve_analysis_child_lines)/100
    #         record.fineness_modulus = fineness_modulus

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
    def calculate_sieve(self): 
        for record in self:
            previous_cumulative = 0  
            for line in record.sieve_analysis_child_lines:
                print("Rows", str(line.percent_retained))
                previous_line = line.serial_no - 1
                if previous_line == 0:
                    cumulative_retained = line.percent_retained
                else:
                    previous_line_record = self.env['mechanical.fine.agg.sieve.analysis.line'].sudo().search([("serial_no", "=", previous_line),("parent_id", "=", record.id)], limit=1)
                    
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



      # Specific Gravity

    specific_gravity_name = fields.Char("Name",default="Specific Gravity & Water Absorption")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    water_absorption_name = fields.Char("Name",default="Specific Gravity & Water Absorption")
    water_absorption_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")

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
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_specific_gravity_conformity", store=True)

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
                if material.grade.id == record.grade.id:
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
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_specific_gravity_nabl", store=True)

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_nabl(self):
        
        for record in self:
            record.avg_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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


    # Soundness Na2SO4
    soundness_na2so4_name = fields.Char("Name",default="SOUNDNESS (SODIUM SULPHATE TEST)")
    soundness_na2so4_visible = fields.Boolean("SOUNDNESS OF COARSE AGGREGATE (SODIUM SULPHATE TEST) Visible",compute="_compute_visible")

    soundness_sod_line_ids = fields.One2many(
        'fine.sodium.sulphate.line',
        'parent_id',
        string="Soundness Na2SO4",default=lambda self: self.soundness_sod_line_ids_sizes()
    )

    @api.model
    def soundness_sod_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '60mm','retained_sieve': '40mm'}),
            (0, 0, {'passing_sieve': '40mm','retained_sieve': '20mm'}),
            (0, 0, {'passing_sieve': '20mm','retained_sieve': '10mm'}),
            (0, 0, {'passing_sieve': '10mm','retained_sieve': '4.75mm'}),
        ]
        return default_lines 
    


    total_grading = fields.Float("Total Grading %", compute="_compute_totaled")
    total_weight_before = fields.Float("Total Weight Before", compute="_compute_totaled")
    total_weight_after = fields.Float("Total Weight After", compute="_compute_totaled")
    total_percent_loss = fields.Float("Total % Loss (Not Used)", compute="_compute_totaled")
    total_weighted_avg = fields.Float("Final Result (Weighted Avg)", compute="_compute_totaled")

    @api.depends(
        'soundness_sod_line_ids.grading_percent',
        'soundness_sod_line_ids.weight_before',
        'soundness_sod_line_ids.weight_after',
        'soundness_sod_line_ids.percent_loss',
        'soundness_sod_line_ids.weighted_avg'
    )
    def _compute_totaled(self):
        for rec in self:
            rec.total_grading = sum(rec.soundness_sod_line_ids.mapped('grading_percent'))
            rec.total_weight_before = sum(rec.soundness_sod_line_ids.mapped('weight_before'))
            rec.total_weight_after = sum(rec.soundness_sod_line_ids.mapped('weight_after'))
            rec.total_percent_loss = sum(rec.soundness_sod_line_ids.mapped('percent_loss'))
            rec.total_weighted_avg = sum(rec.soundness_sod_line_ids.mapped('weighted_avg'))

    soundness_sodtwo_line_ids = fields.One2many(
        'fine.sodium.sulphate.two.line',
        'parent_id',
        string="Soundness Na2SO4",default=lambda self: self.soundness_sodtwo_line_ids_sizes()
    )

    @api.model
    def soundness_sodtwo_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '600mic','retained_sieve': '300mic'}),
            (0, 0, {'passing_sieve': '1.18mm','retained_sieve': '600mic'}),
            (0, 0, {'passing_sieve': '2.36mm','retained_sieve': '1.18mm'}),
            (0, 0, {'passing_sieve': '4.75mm','retained_sieve': '2.36mm'}),
            (0, 0, {'passing_sieve': '10mm','retained_sieve': '4.75mm'}),
            
        ]
        return default_lines 
    
    total1_grading = fields.Float("Total Grading %", compute="_compute_totally")
    total1_weight_before = fields.Float("Total Weight Before", compute="_compute_totally")
    total1_weight_after = fields.Float("Total Weight After", compute="_compute_totally")
    total1_percent_loss = fields.Float("Total % Loss (Not Used)", compute="_compute_totally")
    total1_weighted_avg = fields.Float("Final Result (Weighted Avg)", compute="_compute_totally")

    @api.depends(
        'soundness_sodtwo_line_ids.grading_percent',
        'soundness_sodtwo_line_ids.weight_before',
        'soundness_sodtwo_line_ids.weight_after',
        'soundness_sodtwo_line_ids.percent_loss',
        'soundness_sodtwo_line_ids.weighted_avg'
    )
    def _compute_totally(self):
        for rec in self:
            rec.total1_grading = sum(rec.soundness_sodtwo_line_ids.mapped('grading_percent'))
            rec.total1_weight_before = sum(rec.soundness_sodtwo_line_ids.mapped('weight_before'))
            rec.total1_weight_after = sum(rec.soundness_sodtwo_line_ids.mapped('weight_after'))
            rec.total1_percent_loss = sum(rec.soundness_sodtwo_line_ids.mapped('percent_loss'))
            rec.total1_weighted_avg = sum(rec.soundness_sodtwo_line_ids.mapped('weighted_avg'))

    total_weighted_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_total_weighted_avg_conformity", store=True)

    @api.depends('total_weighted_avg','eln_ref','grade')
    def _compute_total_weighted_avg_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.total_weighted_avg_conformity = 'na'
                continue
            record.total_weighted_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a0e7aaf3-68ff-4e75-830d-91ae04c98f5796')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a0e7aaf3-68ff-4e75-830d-91ae04c98f5796')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.total_weighted_avg - record.total_weighted_avg*mu_value
                    upper = record.total_weighted_avg + record.total_weighted_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.total_weighted_avg_conformity = 'pass'
                        break
                    else:
                        record.total_weighted_avg_conformity = 'fail'

    total_weighted_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_total_weighted_avg_nabl", store=True)

    @api.depends('total_weighted_avg','eln_ref','grade')
    def _compute_total_weighted_avg_nabl(self):
        
        for record in self:
            record.total_weighted_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a0e7aaf3-68ff-4e75-830d-91ae04c98f5796')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a0e7aaf3-68ff-4e75-830d-91ae04c98f5796')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                 lab_min = line.lab_min_value
                 lab_max = line.lab_max_value
                 mu_value = line.mu_value
            
                lower = record.total_weighted_avg - record.total_weighted_avg*mu_value
                upper = record.total_weighted_avg + record.total_weighted_avg*mu_value
                if lower >= lab_min and upper <= lab_max:
                   record.total_weighted_avg_nabl = 'pass'
                   break
                else:
                   record.total_weighted_avg_nabl = 'fail'


    # SOUNDNESS (MAGNESIUM SULPHATE TEST)
    soundness_mgso4_name = fields.Char("Name",default="SOUNDNESS (MAGNESIUM SULPHATE TEST)")
    soundness_mgso4_visible = fields.Boolean("SOUNDNESS (MAGNESIUM SULPHATE TEST) Visible",compute="_compute_visible")

    soundness_mag_line_ids = fields.One2many(
        'fine.magnesium.sulphate.line',
        'parent_id',
        string="Soundness MgSO4",default=lambda self: self.soundness_mag_line_ids_sizes()
    )

    @api.model
    def soundness_mag_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '60mm','retained_sieve': '40mm'}),
            (0, 0, {'passing_sieve': '40mm','retained_sieve': '20mm'}),
            (0, 0, {'passing_sieve': '20mm','retained_sieve': '10mm'}),
            (0, 0, {'passing_sieve': '10mm','retained_sieve': '4.75mm'}),
        ]
        return default_lines 
    


    mag_total_grading = fields.Float("Total Grading %", compute="_compute_totalled")
    mag_total_weight_before = fields.Float("Total Weight Before", compute="_compute_totalled")
    mag_total_weight_after = fields.Float("Total Weight After", compute="_compute_totalled")
    mag_total_percent_loss = fields.Float("Total % Loss (Not Used)", compute="_compute_totalled")
    mag_total_weighted_avg = fields.Float("Final Result (Weighted Avg)", compute="_compute_totalled")

    @api.depends(
        'soundness_mag_line_ids.grading_percent',
        'soundness_mag_line_ids.weight_before',
        'soundness_mag_line_ids.weight_after',
        'soundness_mag_line_ids.percent_loss',
        'soundness_mag_line_ids.weighted_avg'
    )
    def _compute_totalled(self):
        for rec in self:
            rec.mag_total_grading = sum(rec.soundness_mag_line_ids.mapped('grading_percent'))
            rec.mag_total_weight_before = sum(rec.soundness_mag_line_ids.mapped('weight_before'))
            rec.mag_total_weight_after = sum(rec.soundness_mag_line_ids.mapped('weight_after'))
            rec.mag_total_percent_loss = sum(rec.soundness_mag_line_ids.mapped('percent_loss'))
            rec.mag_total_weighted_avg = sum(rec.soundness_mag_line_ids.mapped('weighted_avg'))

    soundness_magtwo_line_ids = fields.One2many(
        'fine.magnesium.sulphate.two.line',
        'parent_id',
        string="Soundness MgSO4",default=lambda self: self.soundness_magtwo_line_ids_sizes()
    )

    @api.model
    def soundness_magtwo_line_ids_sizes(self):
        default_lines = [
            (0, 0, {'passing_sieve': '600mic','retained_sieve': '300mic'}),
            (0, 0, {'passing_sieve': '1.18mm','retained_sieve': '600mic'}),
            (0, 0, {'passing_sieve': '2.36mm','retained_sieve': '1.18mm'}),
            (0, 0, {'passing_sieve': '4.75mm','retained_sieve': '2.36mm'}),
            (0, 0, {'passing_sieve': '10mm','retained_sieve': '4.75mm'}),
            
        ]
        return default_lines 
    
    mag_total1_grading = fields.Float("Total Grading %", compute="_compute_totallly")
    mag_total1_weight_before = fields.Float("Total Weight Before", compute="_compute_totallly")
    mag_total1_weight_after = fields.Float("Total Weight After", compute="_compute_totallly")
    mag_total1_percent_loss = fields.Float("Total % Loss (Not Used)", compute="_compute_totallly")
    mag_total1_weighted_avg = fields.Float("Final Result (Weighted Avg)", compute="_compute_totallly")

    @api.depends(
        'soundness_magtwo_line_ids.grading_percent',
        'soundness_magtwo_line_ids.weight_before',
        'soundness_magtwo_line_ids.weight_after',
        'soundness_magtwo_line_ids.percent_loss',
        'soundness_magtwo_line_ids.weighted_avg'
    )
    def _compute_totallly(self):
        for rec in self:
            rec.mag_total1_grading = sum(rec.soundness_magtwo_line_ids.mapped('grading_percent'))
            rec.mag_total1_weight_before = sum(rec.soundness_magtwo_line_ids.mapped('weight_before'))
            rec.mag_total1_weight_after = sum(rec.soundness_magtwo_line_ids.mapped('weight_after'))
            rec.mag_total1_percent_loss = sum(rec.soundness_magtwo_line_ids.mapped('percent_loss'))
            rec.mag_total1_weighted_avg = sum(rec.soundness_magtwo_line_ids.mapped('weighted_avg'))


    mag_total_weighted_avg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_mag_total_weighted_avg_conformity", store=True)


    @api.depends('mag_total_weighted_avg','eln_ref','grade')
    def _compute_mag_total_weighted_avg_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.mag_total_weighted_avg_conformity = 'na'
                continue
            record.mag_total_weighted_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ace97d80-fdf8-45ed-8762-8ec73805ea68')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ace97d80-fdf8-45ed-8762-8ec73805ea68')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.mag_total_weighted_avg - record.mag_total_weighted_avg*mu_value
                    upper = record.mag_total_weighted_avg + record.mag_total_weighted_avg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.mag_total_weighted_avg_conformity = 'pass'
                        break
                    else:
                        record.mag_total_weighted_avg_conformity = 'fail'


    mag_total_weighted_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_mag_total_weighted_avg_nabl", store=True)

    @api.depends('mag_total_weighted_avg','eln_ref','grade')
    def _compute_mag_total_weighted_avg_nabl(self):
        
        for record in self:
            record.mag_total_weighted_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ace97d80-fdf8-45ed-8762-8ec73805ea68')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ace97d80-fdf8-45ed-8762-8ec73805ea68')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.mag_total_weighted_avg - record.mag_total_weighted_avg*mu_value
                    upper = record.mag_total_weighted_avg + record.mag_total_weighted_avg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.mag_total_weighted_avg_nabl = 'pass'
                        break
                    else:
                        record.mag_total_weighted_avg_nabl = 'fail'




    # Material Finer than 75 Micron

    name_finer75 = fields.Char("Name",default="Material Finer than 75 Micron")
    finer75_visible = fields.Boolean("Finer 75 Visible",compute="_compute_visible")

    finer75_line_ids = fields.One2many('fine.material.finer.75.line', 'parent_id', string="Observations")

    avg_finer_percent = fields.Float(
        "Average Value of % Material Finer than 75 micron",
        compute="_compute_avg_finer_percent",
        store=True
    )

    @api.depends('finer75_line_ids.finer_percent')
    def _compute_avg_finer_percent(self):
        for rec in self:
            lines = rec.finer75_line_ids

            if lines:
                values = lines.mapped('finer_percent')
                rec.avg_finer_percent = sum(values) / len(values)
            else:
                rec.avg_finer_percent = 0.0


    avg_finer_percent_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_finer_percent_conformity", store=True)

    @api.depends('avg_finer_percent','eln_ref','grade')
    def _compute_avg_finer_percent_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_finer_percent_conformity = 'na'
                continue
            record.avg_finer_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d49f6725-5779-42b1-ac6e-44ba24926649')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d49f6725-5779-42b1-ac6e-44ba24926649')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_finer_percent - record.avg_finer_percent*mu_value
                    upper = record.avg_finer_percent + record.avg_finer_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_finer_percent_conformity = 'pass'
                        break
                    else:
                        record.avg_finer_percent_conformity = 'fail'

    avg_finer_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_finer_percent_nabl", store=True)

    @api.depends('avg_finer_percent','eln_ref','grade')
    def _compute_avg_finer_percent_nabl(self):
        
        for record in self:
            record.avg_finer_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d49f6725-5779-42b1-ac6e-44ba24926649')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d49f6725-5779-42b1-ac6e-44ba24926649')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_finer_percent - record.avg_finer_percent*mu_value
            upper = record.avg_finer_percent + record.avg_finer_percent*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_finer_percent_nabl = 'pass'
                break
            else:
                record.avg_finer_percent_nabl = 'fail'



    # DELETERIOUS MATERIAL (CLAY & LUMPS)
    
    name_clay_lumps = fields.Char("Name",default="DELETERIOUS MATERIAL (CLAY & LUMPS)")
    clay_lump_visible = fields.Boolean("DELETERIOUS MATERIAL (CLAY & LUMPS) Visible",compute="_compute_visible")

    clay_lumps_percent_line_ids = fields.One2many('fine.deleterious.clay.line', 'parent_id', string="Trials")

    clay_lumps_percent = fields.Float(
        "Average Deleterious Material (%)",
        compute="_compute_clay_lumps_percent",
        store=True
    )

    @api.depends('clay_lumps_percent_line_ids.percent')
    def _compute_clay_lumps_percent(self):
        for rec in self:
            lines = rec.clay_lumps_percent_line_ids

            if lines:
                values = lines.mapped('percent')
                rec.clay_lumps_percent = sum(values) / len(values)
            else:
                rec.clay_lumps_percent = 0.0


    clay_lumps_percent_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_clay_lumps_percent_conformity", store=True)

    @api.depends('clay_lumps_percent','eln_ref','grade')
    def _compute_clay_lumps_percent_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.clay_lumps_percent_conformity = 'na'
                continue
            record.clay_lumps_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee680f62-91d0-4ffd-bb0c-ecfcd75e13eb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee680f62-91d0-4ffd-bb0c-ecfcd75e13eb')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.clay_lumps_percent - record.clay_lumps_percent*mu_value
                    upper = record.clay_lumps_percent + record.clay_lumps_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.clay_lumps_percent_conformity = 'pass'
                        break
                    else:
                        record.clay_lumps_percent_conformity = 'fail'

    clay_lumps_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_clay_lumps_percent_nabl", store=True)

    @api.depends('clay_lumps_percent','eln_ref','grade')
    def _compute_clay_lumps_percent_nabl(self):
        
        for record in self:
            record.clay_lumps_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee680f62-91d0-4ffd-bb0c-ecfcd75e13eb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ee680f62-91d0-4ffd-bb0c-ecfcd75e13eb')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.clay_lumps_percent - record.clay_lumps_percent*mu_value
                    upper = record.clay_lumps_percent + record.clay_lumps_percent*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.clay_lumps_percent_nabl = 'pass'
                        break
                    else:
                        record.clay_lumps_percent_nabl = 'fail'


    # DELETERIOUS MATERIAL (COAL & LIGNITE)

    deleterious_coal_lignite_name = fields.Char("Name",default="DELETERIOUS MATERIAL (COAL & LIGNITE)")
    deleterious_coal_lignite_visible = fields.Boolean("DELETERIOUS MATERIAL (COAL & LIGNITE) Visible",compute="_compute_visible")

    deleterious_coal_lignite_line_ids = fields.One2many('fine.deleterious.material.coal.lignite.line', 'parent_id', string="Observations")

    avg_deleterious_coal_lignite = fields.Float(
        "Average Percentage of Deleterious Material (%)",
        compute="_compute_avg_deleterious_coal_lignite",
        store=True
    )

    @api.depends('deleterious_coal_lignite_line_ids.deleterious_percent')
    def _compute_avg_deleterious_coal_lignite(self):
        for rec in self:
            lines = rec.deleterious_coal_lignite_line_ids

            if lines:
                values = lines.mapped('deleterious_percent')
                rec.avg_deleterious_coal_lignite = sum(values) / len(values)
            else:
                rec.avg_deleterious_coal_lignite = 0.0


    avg_deleterious_coal_lignite_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_deleterious_coal_lignite_conformity", store=True)

    @api.depends('avg_deleterious_coal_lignite','eln_ref','grade')
    def _compute_avg_deleterious_coal_lignite_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_deleterious_coal_lignite_conformity = 'na'
                continue
            record.avg_deleterious_coal_lignite_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','efc370df-e45d-43a8-a4fa-e1139b59b134')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','efc370df-e45d-43a8-a4fa-e1139b59b134')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_deleterious_coal_lignite - record.avg_deleterious_coal_lignite*mu_value
                    upper = record.avg_deleterious_coal_lignite + record.avg_deleterious_coal_lignite*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_deleterious_coal_lignite_conformity = 'pass'
                        break
                    else:
                        record.avg_deleterious_coal_lignite_conformity = 'fail'

    avg_deleterious_coal_lignite_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_deleterious_coal_lignite_nabl", store=True)

    @api.depends('avg_deleterious_coal_lignite','eln_ref','grade')
    def _compute_avg_deleterious_coal_lignite_nabl(self):
        
        for record in self:
            record.avg_deleterious_coal_lignite_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','efc370df-e45d-43a8-a4fa-e1139b59b134')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','efc370df-e45d-43a8-a4fa-e1139b59b134')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_deleterious_coal_lignite - record.avg_deleterious_coal_lignite*mu_value
                    upper = record.avg_deleterious_coal_lignite + record.avg_deleterious_coal_lignite*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_deleterious_coal_lignite_nabl = 'pass'
                        break
                    else:
                        record.avg_deleterious_coal_lignite_nabl = 'fail'




       # Moisture Content
    moisture_content_name1 = fields.Char("Name",default="Moisture Content")
    moisture_content_visible = fields.Boolean("Silt Content",compute="_compute_visible")

    moisture_content_child_lines = fields.One2many('fine.moisture.content.line','parent_id',string="Parameter")

    wet_sand = fields.Float(string="Weight of Wet Sand Sample, (W1)", compute="_compute_avg_moisture_content_lines")
    wet_dry = fields.Float(string="Weight of Dry Sand Sample, (W2)", compute="_compute_avg_moisture_content_lines")
    diff_wd = fields.Float(string="Diff. Between Wet and Dry Sand:- (W1-W2)", compute="_compute_avg_moisture_content_lines")

    @api.depends('moisture_content_child_lines')
    def _compute_avg_moisture_content_lines(self):
        for rec in self:
            # Sort for consistent line order
            lines = rec.moisture_content_child_lines.sorted(key=lambda l: l.serial_no)

            # For wet_sand and wet_dry → only first 2 lines
            selected_lines = lines[:2]
            count_selected = len(selected_lines)

            if count_selected:
                rec.wet_sand = sum(line.wt_sand for line in selected_lines) / count_selected
                rec.wet_dry = sum(line.wt_dry for line in selected_lines) / count_selected
            else:
                rec.wet_sand = rec.wet_dry = 0.0

            # For diff_wd → use all lines
            count_all = len(lines)
            if count_all:
                rec.diff_wd = sum(line.diff_wet_sand for line in lines) / count_all
            else:
                rec.diff_wd = 0.0



    avg_moisture = fields.Float(
        string="Average Moisture Content (%)",
        compute="_compute_avg_moisture",
        store=True )


    @api.depends('diff_wd', 'wet_dry')
    def _compute_avg_moisture(self):
        for rec in self:
            if rec.wet_dry:
                rec.avg_moisture = ((rec.diff_wd  / rec.wet_dry) * 100)
            else:
                rec.avg_moisture = 0.0


    avg_moisture_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_moisture_conformity", store=True)

    @api.depends('avg_moisture','eln_ref','grade')
    def _compute_avg_moisture_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_moisture_conformity = 'na'
                continue
            record.avg_moisture_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457htyu1245-3fa3-4b83-ae31-9d281457457hy')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457htyu1245-3fa3-4b83-ae31-9d281457457hy')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_moisture - record.avg_moisture*mu_value
                    upper = record.avg_moisture + record.avg_moisture*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_moisture_conformity = 'pass'
                        break
                    else:
                        record.avg_moisture_conformity = 'fail'

    avg_moisture_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_moisture_nabl", store=True)

    @api.depends('avg_moisture','eln_ref','grade')
    def _compute_avg_moisture_nabl(self):
        
        for record in self:
            record.avg_moisture_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457htyu1245-3fa3-4b83-ae31-9d281457457hy')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457htyu1245-3fa3-4b83-ae31-9d281457457hy')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_moisture - record.avg_moisture*mu_value
                    upper = record.avg_moisture + record.avg_moisture*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_moisture_nabl = 'pass'
                        break
                    else:
                        record.avg_moisture_nabl = 'fail'


    # Deleterious Material - Soft Particle

    deleterious_soft_par_name = fields.Char("Name", default="Deleterious Material - Soft Particles")
    deleterious_soft_par_visible = fields.Boolean("Deleterious Material - Soft Particles",compute="_compute_visible")

    soft_particles_percent_line_ids = fields.One2many('fine.soft.particles.line', 'parent_id', string="Trials")

    avg_soft_particles_percent = fields.Float(
        "Average Deleterious Material (%)",
        compute="_compute_avg_soft_particles_percent",
        store=True
    )

    @api.depends('soft_particles_percent_line_ids.soft_particles_percent')
    def _compute_avg_soft_particles_percent(self):
        for rec in self:
            lines = rec.soft_particles_percent_line_ids

            if lines:
                values = lines.mapped('soft_particles_percent')
                rec.avg_soft_particles_percent = sum(values) / len(values)
            else:
                rec.avg_soft_particles_percent = 0.0


    avg_soft_particles_percent_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),('na', 'NA'),], string="Conformity", compute="_compute_avg_soft_particles_percent_conformity", store=True)

    @api.depends('avg_soft_particles_percent','eln_ref','grade')
    def _compute_avg_soft_particles_percent_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_soft_particles_percent_conformity = 'na'
                continue
            record.avg_soft_particles_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03d66a05-767f-4e4f-9f09-b1a3af00af76')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03d66a05-767f-4e4f-9f09-b1a3af00af76')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_soft_particles_percent - record.avg_soft_particles_percent*mu_value
                    upper = record.avg_soft_particles_percent + record.avg_soft_particles_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_soft_particles_percent_conformity = 'pass'
                        break
                    else:
                        record.avg_soft_particles_percent_conformity = 'fail'

    avg_soft_particles_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_soft_particles_percent_nabl", store=True)

    @api.depends('avg_soft_particles_percent','eln_ref','grade')
    def _compute_avg_soft_particles_percent_nabl(self):
        
        for record in self:
            record.avg_soft_particles_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03d66a05-767f-4e4f-9f09-b1a3af00af76')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','03d66a05-767f-4e4f-9f09-b1a3af00af76')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_soft_particles_percent - record.avg_soft_particles_percent*mu_value
                    upper = record.avg_soft_particles_percent + record.avg_soft_particles_percent*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_soft_particles_percent_nabl = 'pass'
                        break
                    else:
                        record.avg_soft_particles_percent_nabl = 'fail'
    




    # Deleterious Material - Organic Impurities

    organic_impurities_name = fields.Char( "Name", default="Deleterious Material - Organic Impurities")
    organic_impurities_visible = fields.Boolean( "Deleterious Material - Organic Impurities",compute="_compute_visible")

    sample_color = fields.Selection([
    ('lighter', 'Lighter than Standard'),
    ('same', 'Same as Standard'),
    ('darker', 'Darker than Standard')
      ], string="Sample Color")


    organic_impurities_result = fields.Selection([
    ('pass', 'Pass'),
    ('fail', 'Fail')
        ], string="Organic Impurities Result",
   compute="_compute_organic_impurities",
   store=True
         )


    @api.depends('sample_color')
    def _compute_organic_impurities(self):
      for rec in self:
        if rec.sample_color in ['lighter', 'same']:
            rec.organic_impurities_result = 'pass'
        elif rec.sample_color == 'darker':
            rec.organic_impurities_result = 'fail'
        else:
            rec.organic_impurities_result = False



    #  Bulking of Sand

    bulking_sand_name = fields.Char("Name",default="Bulking of Sand")
    bulking_sand_visible = fields.Boolean("Bulking of Sand",compute="_compute_visible")

    bulking_sand_child_lines = fields.One2many('fine.bulking.sand.line','parent_id',string="Parameter")

    avg_height_sand_a = fields.Float(string="Height of Sand in Cylinder:- (A)", compute="_compute_avg_bulking_lines")
    avg_height_sattled_b = fields.Float(string="Height of Settled Sand:- (B)", compute="_compute_avg_bulking_lines")
    avg_loss_c = fields.Float(string="Loss of Height of Sand:- (A-B)", compute="_compute_avg_bulking_lines")

   

    @api.depends('bulking_sand_child_lines')
    def _compute_avg_bulking_lines(self):
        for rec in self:
            lines = rec.bulking_sand_child_lines
            all_count = len(lines)
            selected_lines = lines[:2]  # Only first two lines (0 and 1)
            selected_count = len(selected_lines)

            # Compute avg from 1st two lines
            if selected_count:
                rec.avg_height_sand_a = sum(line.height_of_sand for line in selected_lines) / selected_count
                rec.avg_height_sattled_b = sum(line.height_of_settled for line in selected_lines) / selected_count
            else:
                rec.avg_height_sand_a = 0.0
                rec.avg_height_sattled_b = 0.0

            # Compute avg of loss_c from all lines
            if all_count:
                rec.avg_loss_c = sum(line.loss_off_height for line in lines) / all_count
            else:
                rec.avg_loss_c = 0.0


  
                

    avg_bulking_of_sand = fields.Float(
        string="Average Bulking of Sand (%)",
        compute="_compute_avg_bulking_percent",
        store=True )
    
    @api.depends('avg_loss_c', 'avg_height_sattled_b')
    def _compute_avg_bulking_percent(self):
        for rec in self:
            if rec.avg_height_sattled_b:
                rec.avg_bulking_of_sand = (rec.avg_loss_c / rec.avg_height_sattled_b) * 100
            else:
                rec.avg_bulking_of_sand = 0.0

   


    avg_bulking_of_sand_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_avg_bulking_of_sand_conformity", store=True)

    @api.depends('avg_bulking_of_sand','eln_ref','grade')
    def _compute_avg_bulking_of_sand_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_bulking_of_sand_conformity = 'na'
                continue
            record.avg_bulking_of_sand_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45789bhgt25-3fa3-4b83-ae31-9d28176718457')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45789bhgt25-3fa3-4b83-ae31-9d28176718457')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_bulking_of_sand - record.avg_bulking_of_sand*mu_value
                    upper = record.avg_bulking_of_sand + record.avg_bulking_of_sand*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_bulking_of_sand_conformity = 'pass'
                        break
                    else:
                        record.avg_bulking_of_sand_conformity = 'fail'

    avg_bulking_of_sand_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_bulking_of_sand_nabl", store=True)

    @api.depends('avg_bulking_of_sand','eln_ref','grade')
    def _compute_avg_bulking_of_sand_nabl(self):
        
        for record in self:
            record.avg_bulking_of_sand_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45789bhgt25-3fa3-4b83-ae31-9d28176718457')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45789bhgt25-3fa3-4b83-ae31-9d28176718457')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_bulking_of_sand - record.avg_bulking_of_sand*mu_value
                    upper = record.avg_bulking_of_sand + record.avg_bulking_of_sand*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_bulking_of_sand_nabl = 'pass'
                        break
                    else:
                        record.avg_bulking_of_sand_nabl = 'fail'

     



            


      


    






    












     ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
      
            record.sieve_visible = False
            record.specific_gravity_visible = False
            record.water_absorption_visible = False
            record.loose_density_visible = False
            record.compacted_density_visible = False
            record.voids_compacted_density_visible = False
            record.voids_loose_density_visible = False
            record.soundness_na2so4_visible = False
            record.soundness_mgso4_visible = False
            record.finer75_visible = False
            record.clay_lump_visible = False  
            record.moisture_content_visible = False
            record.deleterious_soft_par_visible = False
            record.organic_impurities_visible  = False
            record.bulking_sand_visible = False
            record.deleterious_coal_lignite_visible = False






          
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
               
                if sample.internal_id == "318d72a1-7188-4086-b132-62b50e63f5d1":
                    record.sieve_visible = True

                if sample.internal_id == "45875ght-7188-4086-b132-62b50e63f1245gt":
                    record.specific_gravity_visible = True

                if sample.internal_id == "4dbde30b-0cdc-4641-abdd-68a574fd7e1f":
                    record.water_absorption_visible = True

                if sample.internal_id == "4587tyhloos-3fa3-4b83-ae31-9d281767188c":
                    record.loose_density_visible = True
                    
                
                if sample.internal_id == 'd961c78a-9f5c-4e7f-9f03-86ab65740161':
                    record.compacted_density_visible  = True

                if sample.internal_id == '04a95dc1-4b45-4817-a9b2-dd722bbe6281':
                    record.voids_compacted_density_visible = True
                
                if sample.internal_id == '919587f2-5b45-4da1-bb73-10164b861833':
                    record.voids_loose_density_visible = True

                if sample.internal_id == 'a0e7aaf3-68ff-4e75-830d-91ae04c98f5796':
                    record.soundness_na2so4_visible = True

                if sample.internal_id == 'ace97d80-fdf8-45ed-8762-8ec73805ea68':
                    record.soundness_mgso4_visible = True

                if sample.internal_id == 'd49f6725-5779-42b1-ac6e-44ba24926649':
                    record.finer75_visible = True

                if sample.internal_id == 'ee680f62-91d0-4ffd-bb0c-ecfcd75e13eb':
                    record.clay_lump_visible = True

                if sample.internal_id == 'efc370df-e45d-43a8-a4fa-e1139b59b134':
                    record.deleterious_coal_lignite_visible = True


                if sample.internal_id == "1457htyu1245-3fa3-4b83-ae31-9d281457457hy":
                    record.moisture_content_visible = True
               
                if sample.internal_id == '03d66a05-767f-4e4f-9f09-b1a3af00af76':
                    record.deleterious_soft_par_visible = True

                if sample.internal_id == '0363075f-a3f2-440a-b634-76f469d220c7':
                    record.organic_impurities_visible = True

                if sample.internal_id == "45789bhgt25-3fa3-4b83-ae31-9d28176718457":
                    record.bulking_sand_visible = True

               
                

            
   
    

    def open_eln_page(self):

        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        if current_user.has_group('lerm_civil.lerm_discipline_group'):
            technician_results = self.eln_ref.parameters_result
        else:
            technician_results = self.eln_ref.parameters_result.filtered(
                lambda r: r.technician == current_user
            )

        for result in technician_results:
            internal_id = result.parameter.internal_id

            # Sieve Analysis
            if result.parameter.internal_id == '318d72a1-7188-4086-b132-62b50e63f5d1':
                result.calculated = True

            # Specific Gravity
            if result.parameter.internal_id == '45875ght-7188-4086-b132-62b50e63f1245gt':
                result.result_char = round(self.avg_specific_gravity,2)
                result.calculated = True
                if self.avg_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Water Absorption
            if result.parameter.internal_id == '4dbde30b-0cdc-4641-abdd-68a574fd7e1f':
                result.result_char = round(self.avg_water_absorption,2)
                result.calculated = True
                if self.avg_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Bulk Density
            if result.parameter.internal_id == 'f2c6222e-e761-4b65-844a-fb882948c47f':
                result.calculated = True


            # Loose density
            if internal_id == "4587tyhloos-3fa3-4b83-ae31-9d281767188c":
                result.result_char = round(self.loose_density, 2)
                result.calculated = True
                if self.loose_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Compacted density
            if internal_id == "d961c78a-9f5c-4e7f-9f03-86ab65740161":
                result.result_char = round(self.compacted_density, 2)
                result.calculated = True
                if self.compacted_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Voids – compacted density
            if internal_id == "04a95dc1-4b45-4817-a9b2-dd722bbe6281":
                result.result_char = round(self.voids_compacted_density, 2)
                result.calculated = True
                if self.voids_compacted_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Voids – loose density
            if internal_id == "919587f2-5b45-4da1-bb73-10164b861833":
                result.result_char = round(self.voids_loose_density, 2)
                result.calculated = True
                if self.voids_loose_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Soundness na2so4
            if internal_id == "a0e7aaf3-68ff-4e75-830d-91ae04c98f5796":
                result.result_char = round(self.total_weighted_avg, 2)
                result.calculated = True
                if self.total_weighted_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Soundness mgso4
            if internal_id == "ace97d80-fdf8-45ed-8762-8ec73805ea68":
                result.result_char = round(self.mag_total_weighted_avg, 2)
                result.calculated = True
                if self.mag_total_weighted_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Material Finer than 75 Micron
            if internal_id == "d49f6725-5779-42b1-ac6e-44ba24926649":
                result.result_char = round(self.avg_finer_percent, 2)
                result.calculated = True
                if self.avg_finer_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # DELETERIOUS MATERIAL (CLAY & LUMPS)
            if result.parameter.internal_id == 'ee680f62-91d0-4ffd-bb0c-ecfcd75e13eb':
                result.calculated = True
                result.result_char = round(self.clay_lumps_percent,2)
                if self.clay_lumps_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Deleterious Material - Lightweight Pieces (Coal & Lignite)
            if result.parameter.internal_id == 'efc370df-e45d-43a8-a4fa-e1139b59b134':
                result.calculated = True
                result.result_char = round(self.avg_deleterious_coal_lignite,2)
                if self.avg_deleterious_coal_lignite_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Moisture Content
            if result.parameter.internal_id == '1457htyu1245-3fa3-4b83-ae31-9d281457457hy':
                result.result_char = round(self.avg_moisture,2)
                result.calculated = True
                if self.avg_moisture_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Deleterious Material (Soft Fragments)
            if result.parameter.internal_id == '03d66a05-767f-4e4f-9f09-b1a3af00af76':
                result.calculated = True
                result.result_char = round(self.avg_soft_particles_percent,2)
                if self.avg_soft_particles_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            #  Deleterious Material - Organic Impurities
            if result.parameter.internal_id == '0363075f-a3f2-440a-b634-76f469d220c7':
                result.calculated = True

            # Bulking Sand
            if result.parameter.internal_id == '45789bhgt25-3fa3-4b83-ae31-9d28176718457':
                result.calculated = True
                result.result_char = round(self.avg_bulking_of_sand,2)
                if self.avg_bulking_of_sand_nabl == 'pass':
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
        record = super(FineAggregate, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(FineAggregate, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()
        self.default_get(fields)

        return super(FineAggregate, self).read(fields=fields, load=load)

   
    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
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
        record = self.env['mechanical.coarse.aggregate'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id



    notes_id = fields.One2many('mechanical.fine.aggregate.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

    @api.model
    def _default_notes_lines(self):
        return [
            (0, 0, {'sr_no': 'i', 'notes': 'The results stated in this report apply only to the tested sample(s) and are based on the conditions and parameters at the time of testing.'}),
            (0, 0, {'sr_no': 'ii', 'notes': 'This report is invalid without the official paper seal of Make Infracon.'}),
            (0, 0, {'sr_no': 'iii', 'notes': 'All test results are confidential and will not be disclosed to any third party without written consent of the client, except where required by law.'}),
            (0, 0, {'sr_no': 'iv', 'notes': 'Any discrepancies or complaints regarding this report must be communicated in writing within 7 days from the date of issue.'}),
            (0, 0, {'sr_no': 'v', 'notes': 'This report shall not be reproduced, except in full, without the prior written approval of Make Infracon.'}),
            (0, 0, {'sr_no': 'vi', 'notes': 'The laboratory assumes no responsibility for the purpose for which the test results are used or for any subsequent actions taken based on these results.'}),
        ]






class SieveAnalysisLine(models.Model):
    _name = "mechanical.fine.agg.sieve.analysis.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained",digits=(12,1))
    cumulative_retained = fields.Float(string="Cum. Retained %", compute="_compute_cum_retained", store=True,digits=(12,1))
    passing_percent = fields.Float(string="Passing %",digits=(12,1))
    specific_limt = fields.Char(string="Specified Limits")



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
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines, key=lambda r: r.id)
            # index = sorted_lines.index(record)
            # print("Working")



class FineSodiumSulphateLine(models.Model):
    _name = "fine.sodium.sulphate.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id",ondelete='cascade')

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size")
    retained_sieve = fields.Char("Retained Sieve Size")

    grading_percent = fields.Float("Grading of Original Sample (%)")

    weight_before = fields.Float("Weight Before Test (gm)")
    weight_after = fields.Float("Weight After Test (gm)")

    percent_loss = fields.Float(
        "Percent Loss",
        compute="_compute_loss",
        store=True
    )

    weighted_avg = fields.Float(
        "Weighted Average",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before > 0:
            rec.percent_loss = (
                (rec.weight_before - rec.weight_after)
                / rec.weight_before
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


class FineSodiumSulphateTwoLine(models.Model):
    _name = "fine.sodium.sulphate.two.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size")
    retained_sieve = fields.Char("Retained Sieve Size")

    grading_percent = fields.Float("Grading of Original Sample (%)")

    weight_before = fields.Float("Weight Before Test (gm)")
    weight_after = fields.Float("Weight After Test (gm)")

    percent_loss = fields.Float(
        "Percent Loss",
        compute="_compute_loss",
        store=True
    )

    weighted_avg = fields.Float(
        "Weighted Average",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before > 0:
            rec.percent_loss = (
                (rec.weight_before - rec.weight_after)
                / rec.weight_before
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


class FineMagnesiumSulphateLine(models.Model):
    _name = "fine.magnesium.sulphate.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size")
    retained_sieve = fields.Char("Retained Sieve Size")

    grading_percent = fields.Float("Grading of Original Sample (%)")

    weight_before = fields.Float("Weight Before Test (gm)")
    weight_after = fields.Float("Weight After Test (gm)")

    percent_loss = fields.Float(
        "Percent Loss",
        compute="_compute_loss",
        store=True
    )

    weighted_avg = fields.Float(
        "Weighted Average",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before > 0:
            rec.percent_loss = (
                (rec.weight_before - rec.weight_after)
                / rec.weight_before
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


class FineMagnesiumSulphateTwoLine(models.Model):
    _name = "fine.magnesium.sulphate.two.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    passing_sieve = fields.Char("Passing Sieve Size")
    retained_sieve = fields.Char("Retained Sieve Size")

    grading_percent = fields.Float("Grading of Original Sample (%)")

    weight_before = fields.Float("Weight Before Test (gm)")
    weight_after = fields.Float("Weight After Test (gm)")

    percent_loss = fields.Float(
        "Percent Loss",
        compute="_compute_loss",
        store=True
    )

    weighted_avg = fields.Float(
        "Weighted Average",
        compute="_compute_weighted_avg",
        store=True
    )

    @api.depends('weight_before', 'weight_after')
    def _compute_loss(self):
     for rec in self:
        if rec.weight_before > 0:
            rec.percent_loss = (
                (rec.weight_before - rec.weight_after)
                / rec.weight_before
            ) * 100
        else:
            rec.percent_loss = 0

    @api.depends('grading_percent', 'percent_loss')
    def _compute_weighted_avg(self):
     for rec in self:
        rec.weighted_avg = (
            rec.grading_percent * rec.percent_loss
        ) / 100


class FineMaterialFiner75Line(models.Model):
    _name = "fine.material.finer.75.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of oven dry sample taken (W1)")
    w2 = fields.Float("Weight retained on 75 micron sieve (W2)")

    w3 = fields.Float(
        "Weight passing 75 micron sieve (W1 - W2)",
        compute="_compute_values",
        store=True
    )

    finer_percent = fields.Float(
        "Material Finer than 75 micron (%)",
        compute="_compute_values",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_values(self):
        for rec in self:
            rec.w3 = rec.w1 - rec.w2

            if rec.w1:
                rec.finer_percent = ((rec.w1 - rec.w2) / rec.w1) * 100
            else:
                rec.finer_percent = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(FineMaterialFiner75Line, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1



class FineDeleteriousClayLine(models.Model):
    _name = "fine.deleterious.clay.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of total sample (W1)")
    w2 = fields.Float("Weight of clay & lumps separated (W₂)")

    percent = fields.Float(
        "Deleterious Material (%)",
        compute="_compute_percent",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_percent(self):
        for rec in self:
            rec.percent = (rec.w2 / rec.w1) * 100 if rec.w1 else 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(FineDeleteriousClayLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1



class FineDeleteriousMaterialCoalLigniteLine(models.Model):
    _name = "fine.deleterious.material.coal.lignite.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    sample_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

    w1 = fields.Float("Weight of total sample taken (W1)")
    w2 = fields.Float("Weight of coal & lignite particles (W2)")

    deleterious_percent = fields.Float(
        "Deleterious Material (%)",
        compute="_compute_percent",
        store=True
    )

    @api.depends('w1', 'w2')
    def _compute_percent(self):
        for rec in self:
            if rec.w1:
                rec.deleterious_percent = (rec.w2 / rec.w1) * 100
            else:
                rec.deleterious_percent = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(FineDeleteriousMaterialCoalLigniteLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1

class MoistureContentLine(models.Model):
    _name = "fine.moisture.content.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    wt_sand = fields.Float(string="Weight of Wet Sand Sample, (W1)")
    wt_dry = fields.Float(string="Weight of Dry Sand Sample, (W2)")
    diff_wet_sand = fields.Float(string="Diff. Between Wet and Dry Sand:- (W1-W2)",compute="_compute_moisture_content")
    # moisture_content = fields.Float(string="Moisture ContentLine % = ((W1-W2)/W2) x 100",compute="_compute_moisture_content")

    @api.depends('wt_sand', 'wt_dry')
    def _compute_moisture_content(self):
        for rec in self:
            A = rec.wt_sand
            B = rec.wt_dry

            if A and B:
                rec.diff_wet_sand = A - B
            else:
                rec.diff_wet_sand = 0.0

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(MoistureContentLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class FineSoftParticlesLine(models.Model):
    _name = "fine.soft.particles.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    par_sample_weight = fields.Float( string="Total Sample Weight (W) g" )
    soft_particles_weight = fields.Float( string="Weight of Soft Particles (Ws) g" )

    soft_particles_percent = fields.Float(
        string="Soft Particles %",
        compute="_compute_soft_particles",
        store=True
    )

    @api.depends('par_sample_weight', 'soft_particles_weight')
    def _compute_soft_particles(self):
        for rec in self:
            if rec.par_sample_weight:
                rec.soft_particles_percent = (
                    rec.soft_particles_weight / rec.par_sample_weight
                ) * 100
            else:
                rec.soft_particles_percent = 0

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(FineSoftParticlesLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1





class BulkingSandLine(models.Model):
    _name = "fine.bulking.sand.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    height_of_sand = fields.Float(string="Height of Sand in Cylinder:- (A)")
    height_of_settled = fields.Float(string="Height of Settled Sand:- (B)")
    loss_off_height = fields.Float(string="Loss of Height of Sand:- (A-B)",compute="_compute_bulking_values")
    # bulking_of_sand = fields.Float(string="Bulking of Sand % = ((A-B)/B) x 100",compute="_compute_bulking_values")

    @api.depends('height_of_sand', 'height_of_settled')
    def _compute_bulking_values(self):
        for rec in self:
            A = rec.height_of_sand
            B = rec.height_of_settled

            if A and B:
                rec.loss_off_height = A - B
            else:
                rec.loss_off_height = 0.0

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(BulkingSandLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class SiltContentLine(models.Model):
    _name = "fine.silt.content.line"
    parent_id = fields.Many2one('mechanical.fine.aggregatel',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    heigh_sand_silt = fields.Float(string="Height of Sand + Silt in the glass Cylinder:- (A)")
    height_of_sand = fields.Float(string="Height of Sand:- (B)")
    height_silt = fields.Float(string="Height of Silt:- (A-B)",compute="_compute_bulking_values1")
    # bulking_of_sand1 = fields.Float(string="Bulking of Sand % = ((A-B)/B) x 100",compute="_compute_bulking_values1")

    @api.depends('heigh_sand_silt', 'height_of_sand')
    def _compute_bulking_values1(self):
        for rec in self:
            A = rec.heigh_sand_silt
            B = rec.height_of_sand

            if A and B:
                rec.height_silt = A - B
            else:
                rec.height_silt = 0.0

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SiltContentLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


   




class FineAggregateNotes(models.Model):
    _name = "mechanical.fine.aggregate.notes"

    parent_id = fields.Many2one('mechanical.fine.aggregate', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
