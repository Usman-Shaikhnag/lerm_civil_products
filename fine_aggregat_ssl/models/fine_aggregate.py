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


    

    # specific_gravity_unit = fields.Char(
    #     string="Specific Gravity Unit",
    #     compute="_compute_units",
    #     store=False
    #     )
    # bulk_density_unit = fields.Char(
    #     string="Bulk Density Unit",
    #     compute="_compute_units",
    #     store=False
    # )
    # avg_compacted_unit = fields.Char(
    #     string="Avg Compacted Unit",
    #     compute="_compute_units",
    #     store=False
    # )

    # avg_bulking_of_sand_unit = fields.Char(
    #     string="Avg Compacted Unit",
    #     compute="_compute_units",
    #     store=False
    # )

    # silt_contect_unit = fields.Char(
    #     string="Avg Compacted Unit",
    #     compute="_compute_units",
    #     store=False
    # )

    # avg_moisture_unit = fields.Char(
    #     string="Avg Compacted Unit",
    #     compute="_compute_units",
    #     store=False
    # )


    # def _compute_units(self):
    #     for rec in self:
    #         # Specific Gravity
    #         specific_param = self.env['lerm.parameter.master'].search([
    #             ('internal_id', '=', '45875ght-7188-4086-b132-62b50e63f1245gt')
    #         ], limit=1)
    #         rec.specific_gravity_unit = specific_param.unit.name if specific_param.unit else ""

    #         # Bulk Density
    #         density_param = self.env['lerm.parameter.master'].search([
    #             ('internal_id', '=', '4587tyhloos-3fa3-4b83-ae31-9d281767188c')
    #         ], limit=1)
    #         rec.bulk_density_unit = density_param.unit.name if density_param.unit else ""

    #         # Avg Compacted
    #         avg_param = self.env['lerm.parameter.master'].search([
    #             ('internal_id', '=', '6987456gg-a310-4015-bc11-28a85c53ac83')
    #         ], limit=1)
    #         rec.avg_compacted_unit = avg_param.unit.name if avg_param.unit else ""

    #          # avg_bulking_of_sand_unit
    #         bulkn_param = self.env['lerm.parameter.master'].search([
    #             ('internal_id', '=', '45789bhgt25-3fa3-4b83-ae31-9d28176718457')
    #         ], limit=1)
    #         rec.avg_bulking_of_sand_unit = bulkn_param.unit.name if bulkn_param.unit else ""

    #         slite_param = self.env['lerm.parameter.master'].search([
    #             ('internal_id', '=', '2547ghty124m-3fa3-4b83-ae31-9d281457nhy14')
    #         ], limit=1)
    #         rec.silt_contect_unit = slite_param.unit.name if slite_param.unit else ""

    #         moisure_param = self.env['lerm.parameter.master'].search([
    #             ('internal_id', '=', '1457htyu1245-3fa3-4b83-ae31-9d281457457hy')
    #         ], limit=1)
    #         rec.avg_moisture_unit = moisure_param.unit.name if moisure_param.unit else ""

    specific_gravity_unit    = fields.Char("Specific Gravity Unit",    compute="_compute_units", store=False)
    bulk_density_unit        = fields.Char("Bulk Density Unit",        compute="_compute_units", store=False)
    avg_compacted_unit       = fields.Char("Avg Compacted Unit",       compute="_compute_units", store=False)
    avg_bulking_of_sand_unit = fields.Char("Avg Bulking of Sand Unit", compute="_compute_units", store=False)
    silt_contect_unit        = fields.Char("Silt Content Unit",        compute="_compute_units", store=False)
    avg_moisture_unit        = fields.Char("Avg Moisture Unit",        compute="_compute_units", store=False)

    # ---- helper method
    def _get_unit(self, internal_id):
        param = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', internal_id)
        ], limit=1)
        return param.unit.name if param.unit else ""

    # ---- compute + default values
    def _compute_units(self):
        for rec in self:
            rec.specific_gravity_unit    = rec._get_unit("45875ght-7188-4086-b132-62b50e63f1245gt")
            rec.bulk_density_unit        = rec._get_unit("4587tyhloos-3fa3-4b83-ae31-9d281767188c")
            rec.avg_compacted_unit       = rec._get_unit("6987456gg-a310-4015-bc11-28a85c53ac83")
            rec.avg_bulking_of_sand_unit = rec._get_unit("45789bhgt25-3fa3-4b83-ae31-9d28176718457")
            rec.silt_contect_unit        = rec._get_unit("2547ghty124m-3fa3-4b83-ae31-9d281457nhy14")
            rec.avg_moisture_unit        = rec._get_unit("1457htyu1245-3fa3-4b83-ae31-9d281457457hy")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res.update({
            'specific_gravity_unit':    self._get_unit("45875ght-7188-4086-b132-62b50e63f1245gt"),
            'bulk_density_unit':        self._get_unit("4587tyhloos-3fa3-4b83-ae31-9d281767188c"),
            'avg_compacted_unit':       self._get_unit("6987456gg-a310-4015-bc11-28a85c53ac83"),
            'avg_bulking_of_sand_unit': self._get_unit("45789bhgt25-3fa3-4b83-ae31-9d28176718457"),
            'silt_contect_unit':        self._get_unit("2547ghty124m-3fa3-4b83-ae31-9d281457nhy14"),
            'avg_moisture_unit':        self._get_unit("1457htyu1245-3fa3-4b83-ae31-9d281457457hy"),
        })
        return res

  


    # Sieve Analysis 
    sieve_analysis_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

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


      # Specific Gravity

    specific_gravity_name = fields.Char("Name",default="Specific Gravity & Water Absorption")
    specific_gravity_visible = fields.Boolean("Specific Gravity Visible",compute="_compute_visible")

    specific_gravity_child_lines = fields.One2many('fine.specific.and.water.ssl.line','parent_id',string="Parameter")

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

    @api.depends('avg_staurated_a', 'avg_oven_d')
    def _compute_water_absorption(self):
        for rec in self:
            if rec.avg_oven_d:
                rec.water_absorption = ((rec.avg_staurated_a - rec.avg_oven_d) / rec.avg_oven_d) * 100
            else:
                rec.water_absorption = 0.0

   

  

    specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_specific_gravity_conformity", store=True)

    @api.depends('specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_conformity(self):
        
        for record in self:
            record.specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.specific_gravity - record.specific_gravity*mu_value
                    upper = record.specific_gravity + record.specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.specific_gravity_conformity = 'fail'

    specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_specific_gravity_nabl", store=True)

    @api.depends('specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_nabl(self):
        
        for record in self:
            record.specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','45875ght-7188-4086-b132-62b50e63f1245gt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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


     # Loose Bulk Density (LBD)

    loose_bulk_name = fields.Char("Name",default=" Bulk Density")
    loose_bulk_visible = fields.Boolean("Bulk Density Visible",compute="_compute_visible")

    volume_of_cylender = fields.Float(string="Volume of measuring cylinder (v) (lit)")
    weight_empty_cylender = fields.Float(string="Wt of empty measuring cylinder (A) (Kg)")
    loose_measuring_cylender = fields.Float(string="Wt of loose aggregrage +measuring cylinder(B) (Kg)")

    loose_bulk_density = fields.Float(string="Loose Bulk Density (Kg)",compute="_compute_loose_bulk_density",digits=(12,3))

    @api.depends('loose_measuring_cylender', 'weight_empty_cylender', 'volume_of_cylender')
    def _compute_loose_bulk_density(self):
        for rec in self:
            if rec.volume_of_cylender > 0:
                rec.loose_bulk_density = (rec.loose_measuring_cylender - rec.weight_empty_cylender) / rec.volume_of_cylender
            else:
                rec.loose_bulk_density = 0.0


    volume_of_cylender1 = fields.Float(string="Volume of measuring cylinder (v) (lit)")
    weight_empty_cylender1 = fields.Float(string="Wt of empty measuring cylinder (A) (Kg)")
    loose_measuring_cylender1 = fields.Float(string="Wt of loose aggregrage +measuring cylinder(B) (Kg)")

    loose_bulk_density1 = fields.Float(string="Loose Bulk Density (Kg)",compute="_compute_loose_bulk_density1",digits=(12,3))

    @api.depends('loose_measuring_cylender1', 'weight_empty_cylender1', 'volume_of_cylender1')
    def _compute_loose_bulk_density1(self):
        for rec in self:
            if rec.volume_of_cylender1 > 0:
                rec.loose_bulk_density1 = (rec.loose_measuring_cylender1 - rec.weight_empty_cylender1) / rec.volume_of_cylender1
            else:
                rec.loose_bulk_density1 = 0.0

    avg_bulk_density = fields.Float(string="Avg loose density ",compute="_compute_avg_bulk_density",digits=(12,3))

    # Average
    @api.depends('loose_bulk_density', 'loose_bulk_density1')
    def _compute_avg_bulk_density(self):
        for rec in self:
            if rec.loose_bulk_density and rec.loose_bulk_density1:
                rec.avg_bulk_density = (rec.loose_bulk_density + rec.loose_bulk_density1) / 2
            else:
                rec.avg_bulk_density = 0.0

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
            ('fail', 'Fail')], string="Conformity", compute="_compute_loose_bulk_density_conformity", store=True)

    @api.depends('avg_bulk_density','eln_ref','grade')
    def _compute_loose_bulk_density_conformity(self):
        
        for record in self:
            record.loose_bulk_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4587tyhloos-3fa3-4b83-ae31-9d281767188c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4587tyhloos-3fa3-4b83-ae31-9d281767188c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_bulk_density - record.avg_bulk_density*mu_value
                    upper = record.avg_bulk_density + record.avg_bulk_density*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.loose_bulk_density_conformity = 'pass'
                        break
                    else:
                        record.loose_bulk_density_conformity = 'fail'

    loose_bulk_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_loose_bulk_density_nabl", store=True)

    @api.depends('avg_bulk_density','eln_ref','grade')
    def _compute_loose_bulk_density_nabl(self):
        
        for record in self:
            record.loose_bulk_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4587tyhloos-3fa3-4b83-ae31-9d281767188c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4587tyhloos-3fa3-4b83-ae31-9d281767188c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_bulk_density - record.avg_bulk_density*mu_value
                    upper = record.avg_bulk_density + record.avg_bulk_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.loose_bulk_density_nabl = 'pass'
                        break
                    else:
                        record.loose_bulk_density_nabl = 'fail'

    compacted_density_name1 = fields.Char("Name",default="Compacted Density ")
    compacted_density_visible = fields.Boolean("compacted density  Visible",compute="_compute_visible")

    wt_of_compact = fields.Float(string="Wt of compacted aggregrage +measuring cylinder(C) (Kg)")
    compact_bulk = fields.Float(string="Compacted bulk density= (C-A)/V)) (Kg)",compute="_compute_compact_bulk",digits=(12,3))

    @api.depends('wt_of_compact', 'weight_empty_cylender', 'volume_of_cylender')
    def _compute_compact_bulk(self):
        for rec in self:
            if rec.volume_of_cylender and rec.wt_of_compact and rec.weight_empty_cylender:
                rec.compact_bulk = (rec.wt_of_compact - rec.weight_empty_cylender) / rec.volume_of_cylender
            else:
                rec.compact_bulk = 0.0

    

    wt_of_compact1 = fields.Float(string="Wt of compacted aggregrage +measuring cylinder(C) (Kg)")
    compact_bulk1 = fields.Float(string="Compacted bulk density= (C-A)/V)) (Kg)",compute="_compute_compact_bulk1",digits=(12,3))

    @api.depends('wt_of_compact1', 'weight_empty_cylender1', 'volume_of_cylender1')
    def _compute_compact_bulk1(self):
        for rec in self:
            if rec.volume_of_cylender1 and rec.wt_of_compact1 and rec.weight_empty_cylender1:
                rec.compact_bulk1 = (rec.wt_of_compact1 - rec.weight_empty_cylender1) / rec.volume_of_cylender1
            else:
                rec.compact_bulk1 = 0.0

    avg_compacted = fields.Float(string="Avg Compacted Density ",compute="_compute_avg_compacted",digits=(12,3))

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
            ('fail', 'Fail')], string="Compacted Bulk Conformity", compute="_compute_avg_compacted_conformity", store=True)

    @api.depends('avg_compacted','eln_ref','grade')
    def _compute_avg_compacted_conformity(self):
        
        for record in self:
            record.avg_compacted_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6987456gg-a310-4015-bc11-28a85c53ac83')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6987456gg-a310-4015-bc11-28a85c53ac83')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6987456gg-a310-4015-bc11-28a85c53ac83')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6987456gg-a310-4015-bc11-28a85c53ac83')]).parameter_table
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


    specific_gravity1  = fields.Float(string="Specific Gravity")
    voids_ratio = fields.Float(
        string="Voids Ratio (%)",
        compute="_compute_voids_ratio",
        store=True,
        digits=(12, 2)
    )

    @api.depends('specific_gravity1', 'avg_bulk_density')
    def _compute_voids_ratio(self):
        for rec in self:
            if rec.specific_gravity1:
                rec.voids_ratio = ((rec.specific_gravity1 - rec.avg_bulk_density) / rec.specific_gravity1) * 100
            else:
                rec.voids_ratio = 0.0




    # @api.depends('sample_plus_bucket', 'weight_empty_bucket')
    # def _compute_sample_weight(self):
    #     for record in self:
    #         record.sample_weight = record.sample_plus_bucket - record.weight_empty_bucket

    

    # @api.depends('sample_weight', 'weight_bucket')
    # def _compute_loose_bulk_density(self):
    #     for record in self:
    #         if record.weight_bucket:
    #             record.loose_bulk_density = record.sample_weight / record.weight_bucket
    #         else:
    #             record.loose_bulk_density = 0.0


      # 4. Bulking of Sand

    bulking_sand_name = fields.Char("Name",default="Bulking of Sand")
    bulking_sand_visible = fields.Boolean("Bulking of Sand",compute="_compute_visible")

    bulking_sand_child_lines = fields.One2many('fine.bulking.sand.ssl.line','parent_id',string="Parameter")

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
        string="Average Bulking of Sand",
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
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_bulking_of_sand_conformity", store=True)

    @api.depends('avg_bulking_of_sand','eln_ref','grade')
    def _compute_avg_bulking_of_sand_conformity(self):
        
        for record in self:
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

    site_content_child_lines = fields.One2many('fine.silt.content.ssl.line','parent_id',string="Parameter")

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
        string="Silt Contect ",
        compute="_compute_bulking_of_sand1" )

    @api.depends('content_slit_c', 'content_height_sand_b')
    def _compute_bulking_of_sand1(self):
        for rec in self:
            if rec.content_slit_c:
                rec.avg_bulking_of_sand1 = (rec.content_height_sand_b / rec.content_slit_c) * 100
            else:
                rec.avg_bulking_of_sand1 = 0.0


    avg_bulking_of_sand1_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_bulking_of_sand1_conformity", store=True)

    @api.depends('avg_bulking_of_sand1','eln_ref','grade')
    def _compute_avg_bulking_of_sand1_conformity(self):
        
        for record in self:
            record.avg_bulking_of_sand1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2547ghty124m-3fa3-4b83-ae31-9d281457nhy14')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2547ghty124m-3fa3-4b83-ae31-9d281457nhy14')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_bulking_of_sand1 - record.avg_bulking_of_sand1*mu_value
                    upper = record.avg_bulking_of_sand1 + record.avg_bulking_of_sand1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_bulking_of_sand1_conformity = 'pass'
                        break
                    else:
                        record.avg_bulking_of_sand1_conformity = 'fail'

    avg_bulking_of_sand1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_bulking_of_sand1_nabl", store=True)

    @api.depends('avg_bulking_of_sand1','eln_ref','grade')
    def _compute_avg_bulking_of_sand1_nabl(self):
        
        for record in self:
            record.avg_bulking_of_sand1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2547ghty124m-3fa3-4b83-ae31-9d281457nhy14')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2547ghty124m-3fa3-4b83-ae31-9d281457nhy14')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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

    moisture_content_child_lines = fields.One2many('fine.moisture.content.ssl.line','parent_id',string="Parameter")

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
        string="Average Moisture Content",
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
            ('fail', 'Fail')], string="Conformity", compute="_compute_avg_moisture_conformity", store=True)

    @api.depends('avg_moisture','eln_ref','grade')
    def _compute_avg_moisture_conformity(self):
        
        for record in self:
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




 

     ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
      
            record.sieve_visible = False
            record.specific_gravity_visible = False
            record.loose_bulk_visible = False
            record.compacted_density_visible = False
            record.bulking_sand_visible = False
            record.site_content_visible = False
            record.moisture_content_visible = False
          
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
               
                if sample.internal_id == "318d72a1-7188-4086-b132-62b50e63f5d1":
                    record.sieve_visible = True

                if sample.internal_id == "45875ght-7188-4086-b132-62b50e63f1245gt":
                    record.specific_gravity_visible = True

                if sample.internal_id == "4587tyhloos-3fa3-4b83-ae31-9d281767188c":
                    record.loose_bulk_visible = True

                if sample.internal_id == "6987456gg-a310-4015-bc11-28a85c53ac83":
                    record.compacted_density_visible = True

                if sample.internal_id == "45789bhgt25-3fa3-4b83-ae31-9d28176718457":
                    record.bulking_sand_visible = True

                if sample.internal_id == "2547ghty124m-3fa3-4b83-ae31-9d281457nhy14":
                    record.site_content_visible = True

                if sample.internal_id == "1457htyu1245-3fa3-4b83-ae31-9d281457457hy":
                    record.moisture_content_visible = True

            
              
    # def open_eln_page(self):
    #     # import wdb; wdb.set_trace()

    #     return {
    #             'view_mode': 'form',
    #             'res_model': "lerm.eln",
    #             'type': 'ir.actions.act_window',
    #             'target': 'current',
    #             'res_id': self.eln_ref.id,
                
    #         }

    def open_eln_page(self):
    # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == '45875ght-7188-4086-b132-62b50e63f1245gt':
                result.result_char = round(self.specific_gravity,2)
                if self.specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '4587tyhloos-3fa3-4b83-ae31-9d281767188c':
                result.result_char = round(self.loose_bulk_density,2)
                if self.loose_bulk_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '45789bhgt25-3fa3-4b83-ae31-9d28176718457':
                result.result_char = round(self.avg_bulking_of_sand,2)
                if self.avg_bulking_of_sand_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '2547ghty124m-3fa3-4b83-ae31-9d281457nhy14':
                result.result_char = round(self.avg_bulking_of_sand1,2)
                if self.avg_bulking_of_sand1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '1457htyu1245-3fa3-4b83-ae31-9d281457457hy':
                result.result_char = round(self.avg_moisture,2)
                if self.avg_moisture_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '6987456gg-a310-4015-bc11-28a85c53ac83':
                result.result_char = round(self.avg_compacted,2)
                if self.avg_compacted_nabl == 'pass':
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







    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        # records = self.env['lerm.eln'].sudo().search([('id','=', record.eln_id.id)]).parameters_result
        # print("records",records)
        # self.sample_parameters = records
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)



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
    wt_retained = fields.Float(string="Wt. Retained in gms")
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained",digits=(12,2))
    cumulative_retained = fields.Float(string="Cum. Retained %", compute="_compute_cum_retained", store=True,digits=(12,2))
    passing_percent = fields.Float(string="Passing %",digits=(12,2))
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

# wt_of_sample
    # @api.depends('wt_retained', 'parent_id.total_sieve_analysis')
    # def _compute_percent_retained(self):
    #     for record in self:
    #         try:
    #             record.percent_retained = record.wt_retained / self.parent_id.total_sieve_analysis * 100
    #         except ZeroDivisionError:
    #             record.percent_retained = 0 

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
    _name = "fine.specific.and.water.ssl.line"
    parent_id = fields.Many2one('mechanical.fine.aggregate',string="Parent Id")

    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    wt_of_staurated_a = fields.Float(string="Wt of Saturated surface dry  Aggregate in Air:- (A)")
    wt_of_pycnometer_b = fields.Float(string="Wt of Pycnometer containing sample and Water:- (B)")
    wt_of_pycnometer_c = fields.Float(string="Wt of Pycnometer containing Water:- (C)")
    wt_of_oven_d = fields.Float(string="Wt of Oven Dried Aggregate :- ( D )")

    # specific_gravity = fields.Float(string="Specific Gravity", compute="_compute_values", store=True)
    # water_absorption = fields.Float(string="Water Absorption (%)", compute="_compute_values", store=True)

    # @api.depends('wt_of_staurated_a', 'wt_of_pycnometer_b', 'wt_of_pycnometer_c', 'wt_of_oven_d')
    # def _compute_values(self):
    #     for rec in self:
    #         A = rec.wt_of_staurated_a
    #         B = rec.wt_of_pycnometer_b
    #         C = rec.wt_of_pycnometer_c
    #         D = rec.wt_of_oven_d

    #         if D and ((A - D) - (B - C)):
    #             rec.specific_gravity = D / ((A - D) - (B - C))
    #         else:
    #             rec.specific_gravity = 0.0

    #         if D:
    #             rec.water_absorption = ((A - D) / D) * 100
    #         else:
    #             rec.water_absorption = 0.0
   

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
    _name = "fine.bulking.sand.ssl.line"
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
    _name = "fine.silt.content.ssl.line"
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
    _name = "fine.moisture.content.ssl.line"
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