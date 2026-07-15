from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math



class FineAggregate(models.Model):
    _name = "mechanical.fine.aggregate"
    _inherit = "lerm.eln"
    _rec_name = "name_aggregate"


    name_aggregate = fields.Char("Name",default="Fine Aggregate")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    size_id = fields.Many2one('lerm.size.line',compute="_compute_size_id")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    avg_compacted_unit  = fields.Char("Compacted Density", compute="_compute_units", store=False)

    temprature = fields.Integer("Temperature (°C)", digits=(10,2))
    humidity = fields.Integer("Humidity (%)", digits=(10,2))

    week_no = fields.Char("Week No")

    other_details = fields.Char("Other Details")

    condition = fields.Char("Condition")

    description_work = fields.Text("Description Of Work")

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

    @api.depends("eln_ref")
    def _compute_size_id(self):
        for record in self:
            print("Size iD",record.eln_ref.size_id)
            record.size_id = record.eln_ref.size_id.id



    notes_id = fields.One2many('fine.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(FineAggregate, self).default_get(fields)

        default_notes = [
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

        res['notes_id'] = default_notes
        return res

  


    # Sieve Analysis 
    sieve_analysis_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

    sieve_analysis_child_lines = fields.One2many('mechanical.fine.agg.sieve.analysis.line','parent_id',string="Parameter",
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


# Deleterious Content

    name_finer75 = fields.Char("Name",default="Material Finer than 75 Micron")
    finer75_visible = fields.Boolean("Finer 75 Visible",compute="_compute_visible")

    wt_sample_finer75 = fields.Float("Weight of Sample in gms")
    wt_dry_sample_finer75 = fields.Float("Weight of dry sample after retained in 75 microns")
    material_finer75 = fields.Float("Material finer than 75 micron in %",compute="_compute_finer75")

    material_finer75_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
        
    ], string='Conformity', compute="_compute_material_finer75_conformity")

    material_finer75_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_material_finer75_nabl")


    @api.depends('material_finer75','eln_ref','grade')
    def _compute_material_finer75_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.material_finer75_conformity = 'na'
                continue

            record.material_finer75_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2047739e-9941-4bc0-af9b-839767be6e1c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2047739e-9941-4bc0-af9b-839767be6e1c')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.material_finer75 - record.material_finer75*mu_value
                    upper = record.material_finer75 + record.material_finer75*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.material_finer75_conformity = 'pass'
                        break
                    else:
                        record.material_finer75_conformity = 'fail'

    @api.depends('material_finer75','eln_ref','grade')
    def _compute_material_finer75_nabl(self):
        
        for record in self:
            record.material_finer75_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2047739e-9941-4bc0-af9b-839767be6e1c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2047739e-9941-4bc0-af9b-839767be6e1c')]).parameter_table
            
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







# Deleterious Material (Coal & Lignite)


    name_light_weight = fields.Char("Name",default="Deleterious Material Coal & Lignite")
    light_weight_visible = fields.Boolean("Light Weight Visible",compute="_compute_visible")

    wt_sample_light_weight = fields.Float("Weight of Sample in gms")
    wt_dry_sample_light_weight = fields.Float("Weight of dry sample after retained in 75 microns")
    light_weight_percent = fields.Float("Light Weight Particle in %",compute="_compute_light_weight")

    light_weight_percent_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            
        ], string='Conformity', compute="_compute_light_weight_percent_conformity")

    light_weight_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_light_weight_percent_nabl")


    @api.depends('light_weight_percent','eln_ref','grade')
    def _compute_light_weight_percent_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.light_weight_percent_conformity = 'na'
                continue

            record.light_weight_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6daf868e-c850-4c80-8cf2-c37941888888')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6daf868e-c850-4c80-8cf2-c37941888888')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.light_weight_percent - record.light_weight_percent*mu_value
                    upper = record.light_weight_percent + record.light_weight_percent*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.light_weight_percent_conformity = 'pass'
                        break
                    else:
                        record.light_weight_percent_conformity = 'fail'

    @api.depends('light_weight_percent','eln_ref','grade')
    def _compute_light_weight_percent_nabl(self):
        
        for record in self:
            record.light_weight_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6daf868e-c850-4c80-8cf2-c37941888888')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6daf868e-c850-4c80-8cf2-c37941888888')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.light_weight_percent - record.light_weight_percent*mu_value
            upper = record.light_weight_percent + record.light_weight_percent*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.light_weight_percent_nabl = 'pass'
                break
            else:
                record.light_weight_percent_nabl = 'fail'

    @api.depends('wt_sample_light_weight','wt_dry_sample_light_weight')
    def _compute_light_weight(self):
        for record in self:
            if record.wt_sample_light_weight != 0:
                record.light_weight_percent = record.wt_dry_sample_light_weight/record.wt_sample_light_weight*100
            else:
                record.light_weight_percent = 0











  #  Determination  clay and lump
    
    name_clay_lumps = fields.Char("Name",default="Determination of Clay Lumps")
    clay_lump_visible = fields.Boolean("Clay Lump Visible",compute="_compute_visible")

    wt_sample_clay_lumps = fields.Float("Weight of Sample in gms")
    wt_dry_sample_clay_lumps = fields.Float("Weight of dry sample after retained in 75 microns")
    clay_lumps_percent = fields.Float("Clay Lumps in %",compute="_compute_clay_lumps")

    clay_lumps_percent_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
        
    ], string='Conformity', compute="_compute_clay_lumps_percent_conformity")

    clay_lumps_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_clay_lumps_percent_nabl")


    @api.depends('clay_lumps_percent','eln_ref','grade')
    def _compute_clay_lumps_percent_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.clay_lumps_percent_conformity = 'na'
                continue

            record.clay_lumps_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6daf868e-c850-4c80-8cf2-c37941cfc075')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6daf868e-c850-4c80-8cf2-c37941cfc075')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.clay_lumps_percent - record.clay_lumps_percent*mu_value
                    upper = record.clay_lumps_percent + record.clay_lumps_percent*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.clay_lumps_percent_conformity = 'pass'
                        break
                    else:
                        record.clay_lumps_percent_conformity = 'fail'

    @api.depends('clay_lumps_percent','eln_ref','grade')
    def _compute_clay_lumps_percent_nabl(self):
        
        for record in self:
            record.clay_lumps_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6daf868e-c850-4c80-8cf2-c37941cfc075')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6daf868e-c850-4c80-8cf2-c37941cfc075')]).parameter_table
            
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

    @api.depends('wt_sample_clay_lumps','wt_dry_sample_clay_lumps')
    def _compute_clay_lumps(self):
        for record in self:
            if record.wt_sample_clay_lumps != 0:
                record.clay_lumps_percent = ((record.wt_sample_clay_lumps - record.wt_dry_sample_clay_lumps)/record.wt_sample_clay_lumps * 100)
            else:
                record.clay_lumps_percent = 0





    

     # Deleterious Material - Soft Particle

    deleterious_soft_par_name = fields.Char("Name", default="Deleterious Material - Soft Particles")
    deleterious_soft_par_visible = fields.Boolean("Deleterious Material - Soft Particles",compute="_compute_visible")
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








      # Specific Gravity

    specific_gravity_name = fields.Char("Name",default="Specific Gravity & Water Absorption")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    specific_gravity_child_lines = fields.One2many('fine.specific.and.water.line','parent_id',string="Parameter")

    avg_staurated_a = fields.Float(string="Wt of Saturated surface dry  Aggregate in Air:- (A)", compute="_compute_avg_lines")
    avg_pycnometer_b = fields.Float(string="Wt of Pycnometer containing sample and Water:- (B)", compute="_compute_avg_lines")
    avg_pycnometer_c = fields.Float(string="Wt of Pycnometer containing Water:- (C)", compute="_compute_avg_lines")
    avg_oven_d = fields.Float(string="Wt of Oven Dried Aggregate :- ( D )", compute="_compute_avg_lines")

    @api.depends('specific_gravity_child_lines')
    def _compute_avg_lines(self):
        for rec in self:
            lines = rec.specific_gravity_child_lines
            count = len(lines)
            if count:
                rec.avg_staurated_a = sum(line.wt_of_staurated_a for line in lines) / count
                rec.avg_pycnometer_b = sum(line.wt_of_pycnometer_b for line in lines) / count
                rec.avg_pycnometer_c = sum(line.wt_of_pycnometer_c for line in lines) / count
                rec.avg_oven_d = sum(line.wt_of_oven_d for line in lines) / count
            else:
                rec.avg_staurated_a = rec.avg_pycnometer_b = rec.avg_pycnometer_c = rec.avg_oven_d = 0.0

   

    specific_gravity = fields.Float(string="Avg Specific Gravity",compute="_compute_specific_gravity")

    @api.depends('avg_staurated_a', 'avg_pycnometer_b', 'avg_pycnometer_c', 'avg_oven_d')
    def _compute_specific_gravity(self):
        for rec in self:
            denominator = rec.avg_staurated_a - (rec.avg_pycnometer_b - rec.avg_pycnometer_c)
            rec.specific_gravity = rec.avg_oven_d / denominator if denominator else 0.0


    water_absorption = fields.Float(string="Water Absorption % ",compute="_compute_water_absorption")
    water_absorption_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    @api.depends('avg_staurated_a', 'avg_oven_d')
    def _compute_water_absorption(self):
        for rec in self:
            if rec.avg_oven_d:
                rec.water_absorption = ((rec.avg_staurated_a - rec.avg_oven_d) / rec.avg_oven_d) * 100
            else:
                rec.water_absorption = 0.0

   

  

    specific_gravity_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
        
    ], string='Specific Gravity Conformity', compute="_compute_specific_gravity_conformity")

    specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='Specific Gravity NABL', default='fail',compute="_compute_specific_gravity_nabl")


    @api.depends('specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.specific_gravity_conformity = 'na'
                continue

            record.specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.specific_gravity - record.specific_gravity*mu_value
                    upper = record.specific_gravity + record.specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.specific_gravity_conformity = 'fail'

    @api.depends('specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_nabl(self):
        
        for record in self:
            record.specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.specific_gravity - record.specific_gravity*mu_value
            upper = record.specific_gravity + record.specific_gravity*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.specific_gravity_nabl = 'pass'
                break
            else:
                record.specific_gravity_nabl = 'fail'


    water_absorption_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
        
    ], string='Water Absorption Conformity', compute="_compute_water_absorption_conformity")

    water_absorption_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='Water Absorption NABL', default='fail',compute="_compute_water_absorption_nabl")


    @api.depends('water_absorption','eln_ref','grade')
    def _compute_water_absorption_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.water_absorption_conformity = 'na'
                continue

            record.water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36666887952-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36666887952-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.water_absorption - record.water_absorption*mu_value
                    upper = record.water_absorption + record.water_absorption*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.water_absorption_conformity = 'pass'
                        break
                    else:
                        record.water_absorption_conformity = 'fail'

    @api.depends('water_absorption','eln_ref','grade')
    def _compute_water_absorption_nabl(self):
        
        for record in self:
            record.water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36666887952-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36666887952-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.water_absorption - record.water_absorption*mu_value
            upper = record.water_absorption + record.water_absorption*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.water_absorption_nabl = 'pass'
                break
            else:
                record.water_absorption_nabl = 'fail'



          
     # Loose Bulk Density (LBD)

    loose_bulk_name = fields.Char("Name",default=" Bulk Density")
    loose_bulk_visible = fields.Boolean("Bulk Density Visible",compute="_compute_visible")

    weight_bucket = fields.Float(string="Volume of Bucket V, ltrs",digits=(16,3))
    empty_bucket = fields.Float(string="Empty weight of bucket, M1 g",digits=(16,3))
    bucket_compact = fields.Float(string="Bucket + Compacted Aggregate g")
    bucket_loos = fields.Float(string="Bucket + Loose Aggregate g")

    loose_bulk_density = fields.Float(string="Loose Bulk Density kg/cu.m",compute="_compute_loose_bulk_density")

    @api.depends('bucket_loos', 'empty_bucket', 'weight_bucket')
    def _compute_loose_bulk_density(self):
        for rec in self:
            if rec.weight_bucket:
                rec.loose_bulk_density = (rec.bucket_loos - rec.empty_bucket) / rec.weight_bucket
            else:
                rec.loose_bulk_density = 0.0


    compact_bulk_density = fields.Float(string="Compacted Bulk Density kg/cu.m",compute="_compute_bulk_densities")

    @api.depends('bucket_loos', 'bucket_compact', 'empty_bucket', 'weight_bucket')
    def _compute_bulk_densities(self):
        for rec in self:
            if rec.weight_bucket:
                rec.loose_bulk_density = (rec.bucket_loos - rec.empty_bucket) / rec.weight_bucket
                rec.compact_bulk_density = (rec.bucket_compact - rec.empty_bucket) / rec.weight_bucket
            else:
                rec.loose_bulk_density = 0.0
                rec.compact_bulk_density = 0.0

    loose_bulk_density_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
        
    ], string='Conformity', compute="_compute_loose_bulk_density_conformity")

    loose_bulk_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_loose_bulk_density_nabl")


    @api.depends('loose_bulk_density','eln_ref','grade')
    def _compute_loose_bulk_density_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.loose_bulk_density_conformity = 'na'
                continue

            record.loose_bulk_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4587tyhloos-3fa3-4b83-ae31-9d281767188c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4587tyhloos-3fa3-4b83-ae31-9d281767188c')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.loose_bulk_density - record.loose_bulk_density*mu_value
                    upper = record.loose_bulk_density + record.loose_bulk_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.loose_bulk_density_conformity = 'pass'
                        break
                    else:
                        record.loose_bulk_density_conformity = 'fail'

    @api.depends('loose_bulk_density','eln_ref','grade')
    def _compute_loose_bulk_density_nabl(self):
        
        for record in self:
            record.loose_bulk_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4587tyhloos-3fa3-4b83-ae31-9d281767188c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4587tyhloos-3fa3-4b83-ae31-9d281767188c')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.loose_bulk_density - record.loose_bulk_density*mu_value
            upper = record.loose_bulk_density + record.loose_bulk_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.loose_bulk_density_nabl = 'pass'
                break
            else:
                record.loose_bulk_density_nabl = 'fail'




 


      # 4. Bulking of Sand

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
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_bulking_of_sand_conformity", store=True)

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
     



            


      # 5. Silt Content

    site_content_name = fields.Char("Name",default="Silt Content")
    site_content_visible = fields.Boolean("Silt Content",compute="_compute_visible")

    site_content_child_lines = fields.One2many('fine.silt.content.line','parent_id',string="Parameter")

    content_height_sand_a = fields.Float(string="Height of Sand + Silt in the glass Cylinder:- (A)", compute="_compute_avg_content_lines")
    content_height_sand_b = fields.Float(string="Height of Sand:- (B)", compute="_compute_avg_content_lines")
    content_slit_c = fields.Float(string="Height of Silt:- (A-B)", compute="_compute_avg_content_lines")

   
    @api.depends('site_content_child_lines')
    def _compute_avg_content_lines(self):
        for rec in self:
            lines = rec.site_content_child_lines
            all_count = len(lines)
            selected_lines = lines[:2]  # फक्त पहिल्या 2 lines (index 0 आणि 1)
            selected_count = len(selected_lines)

            if selected_count:
                rec.content_height_sand_a = sum(line.heigh_sand_silt for line in selected_lines) / selected_count
                rec.content_height_sand_b = sum(line.height_of_sand for line in selected_lines) / selected_count
            else:
                rec.content_height_sand_a = 0.0
                rec.content_height_sand_b = 0.0

            if all_count:
                rec.content_slit_c = sum(line.height_silt for line in lines) / all_count
            else:
                rec.content_slit_c = 0.0



    avg_bulking_of_sand1 = fields.Float(
        string="Silt Contect % ",
        compute="_compute_bulking_of_sand1" )

    @api.depends('content_height_sand_a', 'content_height_sand_b')
    def _compute_bulking_of_sand1(self):
        for rec in self:
            if rec.content_height_sand_a:
                rec.avg_bulking_of_sand1 = ((rec.content_height_sand_a - rec.content_height_sand_b) / rec.content_height_sand_a) * 100
            else:
                rec.avg_bulking_of_sand1 = 0.0


    avg_bulking_of_sand1_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
        
    ], string='Conformity', compute="_compute_avg_bulking_of_sand1_conformity")

    avg_bulking_of_sand1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_bulking_of_sand1_nabl")


    @api.depends('avg_bulking_of_sand1','eln_ref','grade')
    def _compute_avg_bulking_of_sand1_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_bulking_of_sand1_conformity = 'na'
                continue

            record.avg_bulking_of_sand1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2547ghty124m-3fa3-4b83-ae31-9d281457nhy14')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2547ghty124m-3fa3-4b83-ae31-9d281457nhy14')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_bulking_of_sand1 - record.avg_bulking_of_sand1*mu_value
                    upper = record.avg_bulking_of_sand1 + record.avg_bulking_of_sand1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_bulking_of_sand1_conformity = 'pass'
                        break
                    else:
                        record.avg_bulking_of_sand1_conformity = 'fail'

    @api.depends('avg_bulking_of_sand1','eln_ref','grade')
    def _compute_avg_bulking_of_sand1_nabl(self):
        
        for record in self:
            record.avg_bulking_of_sand1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2547ghty124m-3fa3-4b83-ae31-9d281457nhy14')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2547ghty124m-3fa3-4b83-ae31-9d281457nhy14')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_bulking_of_sand1 - record.avg_bulking_of_sand1*mu_value
            upper = record.avg_bulking_of_sand1 + record.avg_bulking_of_sand1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_bulking_of_sand1_nabl = 'pass'
                break
            else:
                record.avg_bulking_of_sand1_nabl = 'fail'


       # 6. Moisture Content

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
        ('na', 'NA'),
        
    ], string='Conformity', compute="_compute_avg_moisture_conformity")

    avg_moisture_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_moisture_nabl")


    @api.depends('avg_moisture','eln_ref','grade')
    def _compute_avg_moisture_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_moisture_conformity = 'na'
                continue

            record.avg_moisture_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457htyu1245-3fa3-4b83-ae31-9d281457457hy')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457htyu1245-3fa3-4b83-ae31-9d281457457hy')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_moisture - record.avg_moisture*mu_value
                    upper = record.avg_moisture + record.avg_moisture*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_moisture_conformity = 'pass'
                        break
                    else:
                        record.avg_moisture_conformity = 'fail'

    @api.depends('avg_moisture','eln_ref','grade')
    def _compute_avg_moisture_nabl(self):
        
        for record in self:
            record.avg_moisture_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457htyu1245-3fa3-4b83-ae31-9d281457457hy')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1457htyu1245-3fa3-4b83-ae31-9d281457457hy')]).parameter_table
            
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


 #   7  % Voids - Loose density
    void_loose_density_name = fields.Char("Name", default="% Voids - Loose density")
    void_loose_density_visible = fields.Boolean("% Voids - Loose density Visible",compute="_compute_visible")



    wt_of_loose = fields.Float(string="Wt of Loose aggregrage +measuring cylinder(C) (Kg)")
    loose_bulk = fields.Float(string="Loose bulk density= (C-A)/V)) (Kg)",compute="_compute_loose_bulk",digits=(12,3))
    wt_of_loose1 = fields.Float(string="Wt of Loose aggregrage +measuring cylinder(C) (Kg)")
    loose_bulk1 = fields.Float(string="Loose bulk density= (C-A)/V)) (Kg)",compute="_compute_loose_bulk1",digits=(12,3))

    @api.depends('wt_of_loose', 'empty_bucket', 'weight_bucket')
    def _compute_loose_bulk(self):
        for rec in self:
            if rec.weight_bucket and rec.wt_of_loose and rec.empty_bucket:
                rec.loose_bulk = (rec.wt_of_loose - rec.empty_bucket) / rec.weight_bucket
            else:
                rec.loose_bulk = 0.0


    @api.depends('wt_of_loose1', 'empty_bucket', 'weight_bucket')
    def _compute_loose_bulk1(self):
        for rec in self:
            if rec.weight_bucket and rec.wt_of_loose1 and rec.empty_bucket:
                rec.loose_bulk1 = (rec.wt_of_loose1 - rec.empty_bucket) / rec.weight_bucket
            else:
                rec.loose_bulk1 = 0.0
                 # Average

    avg_void_loose_density=fields.Float(string="Avg % Voids - Loose Density",compute="_compute_avg_void_loose_density",digits=(12,3))

    @api.depends('void_loose_density1','void_loose_density2')
    def _compute_avg_void_loose_density(self):
        for rec in self:
            if rec.void_loose_density1 and rec.void_loose_density2 :
                rec.avg_void_loose_density = (rec.void_loose_density1 + rec.void_loose_density2) / 2
            else:
                rec.avg_void_loose_density= 0.0

    avg_void_loose_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Loose Bulk NABL", compute="_compute_avg_void_loose_density_nabl", store=True)
    
    avg_void_loose_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Loose Bulk Conformity", compute="_compute_avg_void_loose_density_conformity", store=True)
    
    @api.depends('avg_void_loose_density','eln_ref','grade')
    def _compute_avg_void_loose_density_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_void_loose_density_conformity = 'na'
                continue

            record.avg_void_loose_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_void_loose_density - record.avg_void_loose_density*mu_value
                    upper = record.avg_void_loose_density + record.avg_void_loose_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_void_loose_density_conformity = 'pass'
                        break
                    else:
                        record.avg_void_loose_density_conformity = 'fail'

    @api.depends('avg_void_loose_density','eln_ref','grade')
    def _compute_avg_void_loose_density_nabl(self):
        
        for record in self:
            record.avg_void_loose_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','919587f2-5b45-4da1-bb73-10164b861833')]).parameter_table
            # for material in materials:
                # if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_void_loose_density - record.avg_void_loose_density*mu_value
            upper = record.avg_void_loose_density + record.avg_void_loose_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_void_loose_density_nabl = 'pass'
                break
            else:
                record.avg_void_loose_density_nabl = 'fail'


    # # Average
    # @api.depends('wt_of_loose', 'wt_of_loose1')
    # def _compute_avg_loose(self):
    #     for rec in self:
    #         if rec.wt_of_loose and rec.wt_of_loose1:
    #             rec.avg_loose = (rec.wt_of_loose + rec.wt_of_loose1) / 2
    #         else:
    #             rec.avg_loose = 0.0


    void_loose_density1=fields.Float(string="% Voids",compute="_compute_void_loose_density1")

    void_loose_density2=fields.Float(string="% Voids",compute="_compute_void_loose_density2")

    specific_gravity4  = fields.Float(string="Specific Gravity")
    specific_gravity5  = fields.Float(string="Specific Gravity")

    @api.depends('specific_gravity4','loose_bulk')
    def _compute_void_loose_density1(self):
        for record in self:
            if record.specific_gravity4:
            # if record.void_compacted_density1:
              record.void_loose_density1 = ((record.specific_gravity4-record.loose_bulk) /record.specific_gravity4)*100
            else:
              record.void_loose_density1 = 0.0
    
    @api.depends('specific_gravity5','loose_bulk1')
    def _compute_void_loose_density2(self):
        for record in self:
            if record.specific_gravity5:
            # if record.void_compacted_density2:
              record.void_loose_density2 = ((record.specific_gravity5-record.loose_bulk1) /record.specific_gravity5)*100
            else:
              record.void_loose_density2 = 0.0




          #  8 Bulk Density
    compacted_density_name1 = fields.Char("Name",default="Compacted Density ")
    compacted_density_visible = fields.Boolean("compacted density  Visible",compute="_compute_visible")

    wt_of_compact = fields.Float(string="Wt of compacted aggregrage +measuring cylinder(C) (Kg)")
    weight_empty_cylender = fields.Float(string="Wt of empty measuring cylinder (A) (Kg)")
    volume_of_cylender = fields.Float(string="Volume of measuring cylinder (v) (lit)")
    compact_bulk = fields.Float(string="Compacted bulk density= (C-A)/V)) (Kg)",compute="_compute_compact_bulk",digits=(12,3))
    volume_of_cylender1 = fields.Float(string="Volume of measuring cylinder (v) (lit)")
    weight_empty_cylender1 = fields.Float(string="Wt of empty measuring cylinder (A) (Kg)")

    avg_bulk_density = fields.Float(string="Avg bulk density ",compute="_compute_avg_bulk_density",digits=(12,3))

    @api.depends('wt_of_compact', 'empty_bucket', 'weight_bucket')
    def _compute_compact_bulk(self):
        for rec in self:
            if rec.weight_bucket and rec.wt_of_compact and rec.empty_bucket:
                rec.compact_bulk = (rec.wt_of_compact - rec.empty_bucket) / rec.weight_bucket
            else:
                rec.compact_bulk = 0.0

    

    wt_of_compact1 = fields.Float(string="Wt of compacted aggregrage +measuring cylinder(C) (Kg)")
    compact_bulk1 = fields.Float(string="Compacted bulk density= (C-A)/V)) (Kg)",compute="_compute_compact_bulk1",digits=(12,3))

    @api.depends('wt_of_compact1', 'empty_bucket', 'weight_bucket')
    def _compute_compact_bulk1(self):
        for rec in self:
            if rec.weight_bucket and rec.wt_of_compact1 and rec.empty_bucket:
                rec.compact_bulk1 = (rec.wt_of_compact1 - rec.empty_bucket) / rec.weight_bucket
            else:
                rec.compact_bulk1 = 0.0

    avg_compacted = fields.Float(string="Avg Compacted Density",compute="_compute_avg_compacted",digits=(12,3)) 

    # Average
    @api.depends('compact_bulk', 'compact_bulk1')
    def _compute_avg_compacted(self):
        for rec in self:
            if rec.compact_bulk and rec.compact_bulk1:
                rec.avg_compacted = (rec.compact_bulk + rec.compact_bulk1) / 2
            else:
                rec.avg_compacted = 0.0


       

   
    avg_compacted_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Compacted Bulk NABL", compute="_compute_avg_compacted_nabl", store=True)

    avg_compacted_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),], string="Compacted Bulk Conformity", compute="_compute_avg_compacted_conformity", store=True)

    @api.depends('avg_compacted','eln_ref','grade')
    def _compute_avg_compacted_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_compacted_conformity = 'na'
                continue

            record.avg_compacted_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_compacted - record.avg_compacted*mu_value
                    upper = record.avg_compacted + record.avg_compacted*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_compacted_conformity = 'pass'
                        break
                    else:
                        record.avg_compacted_conformity = 'fail'

    @api.depends('avg_compacted','eln_ref','grade')
    def _compute_avg_compacted_nabl(self):
        
        for record in self:
            record.avg_compacted_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','357f579d-a310-4015-bc11-28a85c53ac83')]).parameter_table
            # for material in materials:
                # if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_compacted - record.avg_compacted*mu_value
            upper = record.avg_compacted + record.avg_compacted*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_compacted_nabl = 'pass'
                break
            else:
                record.avg_compacted_nabl = 'fail'





        # 9 % Voids - Compacted density
    void_compacted_density_name = fields.Char("Name", default="% Voids - Compacted density")
    void_compacted_density_visible = fields.Boolean("% Voids - Compacted density Visible",compute="_compute_visible")

    void_compacted_density1=fields.Float(string="% Voids",compute="_compute_void_compacted_density1")

    void_compacted_density2=fields.Float(string="% Voids",compute="_compute_void_compacted_density2")

    wt_of_compact = fields.Float(string="Wt of compacted aggregrage +measuring cylinder(C) (Kg)")
    compact_bulk = fields.Float(string="Compacted bulk density= (C-A)/V)) (Kg)",compute="_compute_compact_bulk",digits=(12,3))

    avg_bulk_density = fields.Float(string="Avg bulk density ",compute="_compute_avg_bulk_density",digits=(12,3))

    @api.depends('wt_of_compact', 'empty_bucket', 'weight_bucket')
    def _compute_compact_bulk(self):
        for rec in self:
            if rec.weight_bucket and rec.wt_of_compact and rec.empty_bucket:
                rec.compact_bulk = (rec.wt_of_compact - rec.empty_bucket) / rec.weight_bucket
            else:
                rec.compact_bulk = 0.0

    

    wt_of_compact1 = fields.Float(string="Wt of compacted aggregrage +measuring cylinder(C) (Kg)")
    compact_bulk1 = fields.Float(string="Compacted bulk density= (C-A)/V)) (Kg)",compute="_compute_compact_bulk1",digits=(12,3))

    @api.depends('wt_of_compact1', 'empty_bucket', 'weight_bucket')
    def _compute_compact_bulk1(self):
        for rec in self:
            if rec.weight_bucket and rec.wt_of_compact1 and rec.empty_bucket:
                rec.compact_bulk1 = (rec.wt_of_compact1 - rec.empty_bucket) / rec.weight_bucket
            else:
                rec.compact_bulk1 = 0.0

    avg_compacted = fields.Float(string="Avg Compacted Density",compute="_compute_avg_compacted",digits=(12,3))

    # Average
    @api.depends('compact_bulk', 'compact_bulk1')
    def _compute_avg_compacted(self):
        for rec in self:
            if rec.compact_bulk and rec.compact_bulk1:
                rec.avg_compacted = (rec.compact_bulk + rec.compact_bulk1) / 2
            else:
                rec.avg_compacted = 0.0


    specific_gravity2  = fields.Float(string="Specific Gravity")
    specific_gravity3  = fields.Float(string="Specific Gravity")


    

    @api.depends('specific_gravity2','compact_bulk')
    def _compute_void_compacted_density1(self):
        for record in self:
            if record.specific_gravity2:
            # if record.void_compacted_density1:
              record.void_compacted_density1 = ((record.specific_gravity2-record.compact_bulk) /record.specific_gravity2)*100
            else:
              record.void_compacted_density1 = 0.0
    
    @api.depends('specific_gravity3','compact_bulk1')
    def _compute_void_compacted_density2(self):
        for record in self:
            if record.specific_gravity3:
            # if record.void_compacted_density2:
              record.void_compacted_density2 = ((record.specific_gravity3-record.compact_bulk1) /record.specific_gravity3)*100
            else:
              record.void_compacted_density2 = 0.0

            

    # Average

    avg_void_compacted_density=fields.Float(string="Avg % Voids - Compacted Density",compute="_compute_avg_void_compacted_density",digits=(12,3))

    @api.depends('void_compacted_density1','void_compacted_density2')
    def _compute_avg_void_compacted_density(self):
        for rec in self:
            if rec.void_compacted_density1 and rec.void_compacted_density2 :
                rec.avg_void_compacted_density = (rec.void_compacted_density1 + rec.void_compacted_density2) / 2
            else:
                rec.avg_void_compacted_density= 0.0

    avg_void_compacted_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Compacted Bulk NABL", compute="_compute_avg_void_compacted_density_nabl", store=True)
    
    avg_void_compacted_density_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Compacted Bulk Conformity", compute="_compute_avg_void_compacted_density_conformity", store=True)
    
    @api.depends('avg_void_compacted_density','eln_ref','grade')
    def _compute_avg_void_compacted_density_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_void_compacted_density_conformity = 'na'
                continue

            record.avg_void_compacted_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_void_compacted_density - record.avg_void_compacted_density*mu_value
                    upper = record.avg_void_compacted_density + record.avg_void_compacted_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_void_compacted_density_conformity = 'pass'
                        break
                    else:
                        record.avg_void_compacted_density_conformity = 'fail'

    @api.depends('avg_void_compacted_density','eln_ref','grade')
    def _compute_avg_void_compacted_density_nabl(self):
        
        for record in self:
            record.avg_void_compacted_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','04a95dc1-4b45-4817-a9b2-dd722bbe6281')]).parameter_table
            # for material in materials:
                # if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_void_compacted_density - record.avg_void_compacted_density*mu_value
            upper = record.avg_void_compacted_density + record.avg_void_compacted_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_void_compacted_density_nabl = 'pass'
                break
            else:
                record.avg_void_compacted_density_nabl = 'fail'

     # SOUNDNESS (MAGNESIUM SULPHATE TEST)
    soundness_mgso4_name = fields.Char("Name",default="Soundness MgSO4")
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
        ('fail', 'Fail'),
        ('na', 'NA'),
        
    ], string='Conformity', compute="_compute_mag_total_weighted_avg_conformity")

    mag_total_weighted_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_mag_total_weighted_avg_nabl")


    @api.depends('mag_total_weighted_avg','eln_ref','grade')
    def _compute_mag_total_weighted_avg_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.mag_total_weighted_avg_conformity = 'na'
                continue

            record.mag_total_weighted_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a0e7aaf3-68ff-4e75-830d-91ae04c98f32')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a0e7aaf3-68ff-4e75-830d-91ae04c98f32')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.mag_total_weighted_avg - record.mag_total_weighted_avg*mu_value
                    upper = record.mag_total_weighted_avg + record.mag_total_weighted_avg*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.mag_total_weighted_avg_conformity = 'pass'
                        break
                    else:
                        record.mag_total_weighted_avg_conformity = 'fail'

    @api.depends('mag_total_weighted_avg','eln_ref','grade')
    def _compute_mag_total_weighted_avg_nabl(self):
        
        for record in self:
            record.mag_total_weighted_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a0e7aaf3-68ff-4e75-830d-91ae04c98f32')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a0e7aaf3-68ff-4e75-830d-91ae04c98f32')]).parameter_table
            
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

        # Soundness Na2SO4
    soundness_na2so4_name = fields.Char("Name",default="Soundness by Na2SO4")
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
        ('fail', 'Fail'),
        ('na', 'NA'),
        
    ], string='Conformity', compute="_compute_total_weighted_avg_conformity")

    total_weighted_avg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_total_weighted_avg_nabl")


    @api.depends('total_weighted_avg','eln_ref','grade')
    def _compute_total_weighted_avg_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.total_weighted_avg_conformity = 'na'
                continue

            record.total_weighted_avg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7b921a25-4dc4-4752-a247-d8a223ffbec0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7b921a25-4dc4-4752-a247-d8a223ffbec0')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.total_weighted_avg - record.total_weighted_avg*mu_value
                    upper = record.total_weighted_avg + record.total_weighted_avg*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.total_weighted_avg_conformity = 'pass'
                        break
                    else:
                        record.total_weighted_avg_conformity = 'fail'

    @api.depends('total_weighted_avg','eln_ref','grade')
    def _compute_total_weighted_avg_nabl(self):
        
        for record in self:
            record.total_weighted_avg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7b921a25-4dc4-4752-a247-d8a223ffbec0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7b921a25-4dc4-4752-a247-d8a223ffbec0')]).parameter_table
            
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











     ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
      
            record.sieve_visible = False
            record.specific_gravity_visible = False
            record.water_absorption_visible = False
            record.loose_bulk_visible = False
            record.bulking_sand_visible = False
            record.site_content_visible = False
            record.moisture_content_visible = False
            record.finer75_visible = False
            record.compacted_density_visible = False
            record.void_compacted_density_visible = False
            record.void_loose_density_visible = False


            record.clay_lump_visible = False
            record.light_weight_visible = False
            record.deleterious_soft_par_visible = False
            record.organic_impurities_visible  = False
            record.soundness_mgso4_visible  = False
            record.soundness_na2so4_visible  = False






          
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
               
                if sample.internal_id == "318d72a1-7188-4086-b132-62b50e63f5d1":
                    record.sieve_visible = True

                if sample.internal_id == "45875ght-7188-4086-b132-62b50e63f1245gt":
                    record.specific_gravity_visible = True

                if sample.internal_id == "36666887952-372f-4775-9bcb-e9dd723547htui":
                    record.water_absorption_visible = True

                if sample.internal_id == "4587tyhloos-3fa3-4b83-ae31-9d281767188c":
                    record.loose_bulk_visible = True

                if sample.internal_id == "45789bhgt25-3fa3-4b83-ae31-9d28176718457":
                    record.bulking_sand_visible = True

                if sample.internal_id == "2547ghty124m-3fa3-4b83-ae31-9d281457nhy14":
                    record.site_content_visible = True

                if sample.internal_id == "1457htyu1245-3fa3-4b83-ae31-9d281457457hy":
                    record.moisture_content_visible = True

                if sample.internal_id == '2047739e-9941-4bc0-af9b-839767be6e1c':
                    record.finer75_visible = True
                

                if sample.internal_id == '3cf93161-4452-4aa5-a8e0-b24ffea753b3':
                    record.compacted_density_visible  = True

                if sample.internal_id == '58e8035f-76e4-4cfb-be47-c18c228fd1b0':
                    record.void_compacted_density_visible = True
                
                if sample.internal_id == 'a594196d-d59f-4044-a801-6388ba38a723':
                    record.void_loose_density_visible = True
            





                if sample.internal_id == '6daf868e-c850-4c80-8cf2-c37941cfc075':
                    record.clay_lump_visible = True
                if sample.internal_id == '6daf868e-c850-4c80-8cf2-c37941888888':
                    record.light_weight_visible = True
               
                if sample.internal_id == '03d66a05-767f-4e4f-9f09-b1a3af00af76':
                    record.deleterious_soft_par_visible = True
                if sample.internal_id == '0363075f-a3f2-440a-b634-76f469d220c7':
                    record.organic_impurities_visible = True

                if sample.internal_id == 'a0e7aaf3-68ff-4e75-830d-91ae04c98f32':
                    record.soundness_mgso4_visible = True
                
                if sample.internal_id == '7b921a25-4dc4-4752-a247-d8a223ffbec0':
                    record.soundness_na2so4_visible = True

            
   
    

    def open_eln_page(self):
    # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == '45875ght-7188-4086-b132-62b50e63f1245gt':
                result.result_char = round(self.specific_gravity,2)
                result.calculated = True
                if self.specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '4587tyhloos-3fa3-4b83-ae31-9d281767188c':
                result.result_char = round(self.loose_bulk_density,2)
                result.calculated = True
                if self.loose_bulk_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '45789bhgt25-3fa3-4b83-ae31-9d28176718457':
                result.result_char = round(self.avg_bulking_of_sand,2)
                result.calculated = True
                if self.avg_bulking_of_sand_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '2547ghty124m-3fa3-4b83-ae31-9d281457nhy14':
                result.result_char = round(self.avg_bulking_of_sand1,2)
                result.calculated = True
                if self.avg_bulking_of_sand1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '1457htyu1245-3fa3-4b83-ae31-9d281457457hy':
                result.result_char = round(self.avg_moisture,2)
                result.calculated = True
                if self.avg_moisture_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Compacted density
            if result.parameter.internal_id == '357f579d-a310-4015-bc11-28a85c53ac83':
                result.result_char = round(self.avg_compacted,2)
                result.calculated = True
                if self.avg_compacted_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            

            
            # % void Compacted density
            if result.parameter.internal_id == '04a95dc1-4b45-4817-a9b2-dd722bbe6281':
                result.result_char = round(self.avg_void_compacted_density,2)
                result.calculated = True
                if self.avg_void_compacted_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # % void Loose density
            if result.parameter.internal_id == '919587f2-5b45-4da1-bb73-10164b861833':
                result.result_char = round(self.avg_void_loose_density,2)
                result.calculated = True
                if self.avg_void_loose_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue







            # Deleterious Content - Clay Lumps
            if result.parameter.internal_id == '6daf868e-c850-4c80-8cf2-c37941cfc075':
                result.calculated = True
                result.result_char = round(self.clay_lumps_percent,2)
                if self.clay_lumps_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


             # Deleterious Material - Lightweight Pieces (Coal & Lignite)
            if result.parameter.internal_id == 'e7cc6b68-2550-4e1e-a28e-8526295e733f':
                result.calculated = True
                result.result_char = round(self.light_weight_percent,2)
                if self.light_weight_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'a0e7aaf3-68ff-4e75-830d-91ae04c98f32':
                result.calculated = True
                result.result_char = round(self.mag_total_weighted_avg,2)
                if self.mag_total_weighted_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '7b921a25-4dc4-4752-a247-d8a223ffbec0':
                result.calculated = True
                result.result_char = round(self.total_weighted_avg,2)
                if self.total_weighted_avg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '2047739e-9941-4bc0-af9b-839767be6e1c':
                result.calculated = True
                result.result_char = round(self.material_finer75,2)
                if self.material_finer75_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '6daf868e-c850-4c80-8cf2-c37941888888':
                result.calculated = True
                result.result_char = round(self.light_weight_percent,2)
                if self.light_weight_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '36666887952-372f-4775-9bcb-e9dd723547htui':
                result.calculated = True
                result.result_char = round(self.water_absorption,2)
                if self.water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue



              # Deleterious Material (Soft Fragments)
            if result.parameter.internal_id == '03d66a05-767f-4e4f-9f09-b1a3af00af76':
                result.calculated = True


             #  Deleterious Material - Organic Impurities
            if result.parameter.internal_id == '0363075f-a3f2-440a-b634-76f469d220c7':
                result.calculated = True

           

           
            if result.parameter.internal_id == '318d72a1-7188-4086-b132-62b50e63f5d1':
                result.calculated = True

            
            if result.parameter.internal_id == 'c0340cb7-3f4a-4c15-a453-d63694b71f1d':
                result.calculated = True


            #  Deleterious Material - Organic Impurities
            if result.parameter.internal_id == '237ca3ca-3db7-4782-b863-1dc33be92bc2':
                result.calculated = True


           

            #  Deleterious Material - Organic Impurities
            if result.parameter.internal_id == '3cf93161-4452-4aa5-a8e0-b24ffea753b3':
                result.calculated = True


            #  Deleterious Material - Organic Impurities
            if result.parameter.internal_id == '58e8035f-76e4-4cfb-be47-c18c228fd1b0':
                result.calculated = True

             #  Deleterious Material - Organic Impurities
            if result.parameter.internal_id == 'a594196d-d59f-4044-a801-6388ba38a723':
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


class SpecificAndWaterLine(models.Model):
    _name = "fine.specific.and.water.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    wt_of_staurated_a = fields.Float(string="Wt of Saturated surface dry  Aggregate in Air:- (A)")
    wt_of_pycnometer_b = fields.Float(string="Wt of Pycnometer containing sample and Water:- (B)")
    wt_of_pycnometer_c = fields.Float(string="Wt of Pycnometer containing Water:- (C)")
    wt_of_oven_d = fields.Float(string="Wt of Oven Dried Aggregate :- ( D )")

 
   

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
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

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


class fineNotes(models.Model):
    _name = "fine.notes"

    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")



class MagnesiumSulphateLine(models.Model):
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


class MagnesiumSulphateTwoLine(models.Model):
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



class SodiumSulphateLine(models.Model):
    _name = "fine.sodium.sulphate.line"
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


class SodiumSulphateTwoLine(models.Model):
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





