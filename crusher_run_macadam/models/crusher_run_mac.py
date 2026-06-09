from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re

class CrusherRunMacadamMechanical(models.Model):
    _name = "mechanical.crusher.run.macadam"
    _inherit = "lerm.eln"
    _description = 'mechanical.crusher.run.macadam'
    _rec_name = "name"

    name = fields.Char("Name",default="Crusher Run Macadam")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    size_id = fields.Many2one('lerm.size.line',compute="_compute_size_id")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    avg_compacted_unit  = fields.Char("Compacted Density", compute="_compute_units", store=False)


   


# remark

    notes_id = fields.One2many('crusher.run.macadam.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(CrusherRunMacadamMechanical, self).default_get(fields)

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
    





    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'coarse.aggregate.prefill.data',
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
            # rec.average_impact_value_unit = rec._get_unit("fbf04a49-ea53-4b14-acd4-1797e06669ae")
            rec.avg_compacted_unit     = rec._get_unit("357f579d-a310-4015-bc11-28a85c53ac83")
            # rec.avg_bulk_density_unit   = rec._get_unit("65a41d1f-d557-438e-8fd1-2c619a334d02")
            # rec.aggregate_elongation_unit   = rec._get_unit("70ef993d-d2f8-424c-9729-4e081d647bb1")
            # rec.aggregate_flakiness_unit   = rec._get_unit("c8a5f37e-1449-4794-a854-cdb169493a1a")
            # rec.avg_specific_gravity_unit   = rec._get_unit("2113f38a-d129-4efe-bac4-ff5826dface8")
            # rec.avg_water_absorption_unit   = rec._get_unit("22ee804f-41a3-4fd1-a301-a8d9180fba10")

    # ---- default values (create mode मध्ये दिसण्यासाठी)
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res.update({
            # 'average_crushing_value_unit':   self._get_unit("ee2d3ead-3bf8-4ae5-8e5d-dfe983111f71"),
            # 'average_impact_value_unit': self._get_unit("fbf04a49-ea53-4b14-acd4-1797e06669ae"),
            'avg_compacted_unit':     self._get_unit("357f579d-a310-4015-bc11-28a85c53ac83"),
            # 'avg_bulk_density_unit':   self._get_unit("65a41d1f-d557-438e-8fd1-2c619a334d02"),
            # 'aggregate_elongation_unit':   self._get_unit("70ef993d-d2f8-424c-9729-4e081d647bb1"),
            # 'aggregate_flakiness_unit':   self._get_unit("c8a5f37e-1449-4794-a854-cdb169493a1a"),
            # 'avg_water_absorption_unit':   self._get_unit("2113f38a-d129-4efe-bac4-ff5826dface8"),
        })
        return res


    @api.depends("eln_ref")
    def _compute_size_id(self):
        for record in self:
            print("Size iD",record.eln_ref.size_id)
            record.size_id = record.eln_ref.size_id.id




        
    def get_all_fields(self):
        record = self.env['mechanical.crusher.run.macadam'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



    

    

    # Abrasion Value
    abrasion_value_name = fields.Char("Name",default="Los Angeles Abrasion Value")
    abrasion_visible = fields.Boolean("Abrasion Visible",compute="_compute_visible")

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    total_weight_sample_abrasion = fields.Float(string="Total weight of Sample in gms")
    weight_passing_sample_abrasion = fields.Float(string="Weight of Passing sample in 1.70 mm IS sieve in gms")
    weight_retain_sample_abrasion = fields.Integer(string="Weight of Retain sample in 1.70 mm IS sieve in gms",compute="_compute_weight_retain_sample_abrasion")
    abrasion_value_percentage = fields.Float(string="Abrasion Value (%)",compute="_compute_sample_weight")

    abrasion_value_percentage_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_abrasion_value_percentager_conformity", store=True)

    @api.depends('abrasion_value_percentage','eln_ref','grade')
    def _compute_abrasion_value_percentager_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.abrasion_value_percentage_conformity = 'na'
                continue

            record.abrasion_value_percentage_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b22b1917-4510-4422-9869-d75f6e8893db')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b22b1917-4510-4422-9869-d75f6e8893db')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.abrasion_value_percentage - record.abrasion_value_percentage*mu_value
                    upper = record.abrasion_value_percentage + record.abrasion_value_percentage*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.abrasion_value_percentage_conformity = 'pass'
                        break
                    else:
                        record.abrasion_value_percentage_conformity = 'fail'

    abrasion_value_percentage_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_abrasion_value_percentage_nabl", store=True)

    @api.depends('abrasion_value_percentage','eln_ref','grade')
    def _compute_abrasion_value_percentage_nabl(self):
        
        for record in self:
            record.abrasion_value_percentage_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b22b1917-4510-4422-9869-d75f6e8893db')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b22b1917-4510-4422-9869-d75f6e8893db')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.abrasion_value_percentage - record.abrasion_value_percentage*mu_value
                    upper = record.abrasion_value_percentage + record.abrasion_value_percentage*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.abrasion_value_percentage_nabl = 'pass'
                        break
                    else:
                        record.abrasion_value_percentage_nabl = 'fail'




    @api.depends('total_weight_sample_abrasion', 'weight_passing_sample_abrasion')
    def _compute_weight_retain_sample_abrasion(self):
        for line in self:
            line.weight_retain_sample_abrasion = line.total_weight_sample_abrasion - line.weight_passing_sample_abrasion


    @api.depends('total_weight_sample_abrasion', 'weight_passing_sample_abrasion')
    def _compute_sample_weight(self):
        for line in self:
            if line.total_weight_sample_abrasion != 0:
                line.abrasion_value_percentage = (line.weight_passing_sample_abrasion / line.total_weight_sample_abrasion) * 100
            else:
                line.abrasion_value_percentage = 0.0


    # Specific Gravety 
    water_absorp_name = fields.Char("Name",default="Water Absorption")
    water_absorp_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")


    wt_surface_dry = fields.Float(string="Wt of Saturated surface dry  Aggregate in Air:- (B)")
    wt_sample_inwater = fields.Float(string="Wt of Saturated Aggregate in Water:- (A)")
    oven_dried_wt = fields.Float(string="Wt of Oven Dried Aggregate in Air :- ( C )")

    # Trial 2 (new)
    wt_surface_dry_2 = fields.Float(string="Wt of Saturated surface dry  Aggregate in Air:- (B) [Trial 2]")
    wt_sample_inwater_2 = fields.Float(string="Wt of Saturated Aggregate in Water:- (A) [Trial 2]")
    oven_dried_wt_2 = fields.Float(string="Wt of Oven Dried Aggregate in Air :- (C) [Trial 2]")

    result_wt_surface_dry = fields.Float(string="Wt of Saturated surface dry  Aggregate in Air:- (B)",compute="_compute_result")
    result_wt_sample_inwater = fields.Float(string="Wt of Saturated Aggregate in Water:- (A)",compute="_compute_result")
    result_oven_dried_wt = fields.Float(string="Wt of Oven Dried Aggregate in Air :- (C)",compute="_compute_result")

    specific_gravity = fields.Float(string="Specific Gravity",compute="_compute_specific_gravity")
    water_absorption = fields.Float(string="Water absorption  %",compute="_compute_water_absorption")

    @api.depends('wt_surface_dry', 'wt_sample_inwater', 'oven_dried_wt', 'wt_surface_dry_2', 'wt_sample_inwater_2', 'oven_dried_wt_2')
    def _compute_result(self):
        for line in self:
            line.result_wt_surface_dry = (line.wt_surface_dry + line.wt_surface_dry_2)/2
            line.result_wt_sample_inwater = (line.wt_sample_inwater + line.wt_sample_inwater_2)/2
            line.result_oven_dried_wt = (line.oven_dried_wt + line.oven_dried_wt_2)/2

    water_absorp_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_water_absorp_conformity", store=True)

    @api.depends('water_absorption','eln_ref','grade')
    def _compute_water_absorp_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.water_absorp_conformity = 'na'
                continue

            record.water_absorp_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2113f38a-d129-4efe-bac4-ff5826dface8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2113f38a-d129-4efe-bac4-ff5826dface8')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.water_absorption - record.water_absorption*mu_value
                    upper = record.water_absorption + record.water_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.water_absorp_conformity = 'pass'
                        break
                    else:
                        record.water_absorp_conformity = 'fail'

    water_absorp_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_water_absorp_nabl", store=True)

    @api.depends('water_absorption','eln_ref','grade')
    def _compute_water_absorp_nabl(self):
        
        for record in self:
            record.water_absorp_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2113f38a-d129-4efe-bac4-ff5826dface8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2113f38a-d129-4efe-bac4-ff5826dface8')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.water_absorption - record.water_absorption*mu_value
                    upper = record.water_absorption + record.water_absorption*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.water_absorp_nabl = 'pass'
                        break
                    else:
                        record.water_absorp_nabl = 'fail'



    @api.depends('wt_surface_dry', 'wt_sample_inwater', 'oven_dried_wt', 'wt_surface_dry_2', 'wt_sample_inwater_2', 'oven_dried_wt_2')
    def _compute_specific_gravity(self):
        for line in self:
            sg1 = 0.0
            if line.result_wt_surface_dry - line.result_wt_sample_inwater != 0:
                sg1 = line.result_oven_dried_wt / (line.result_wt_surface_dry - line.result_wt_sample_inwater)
            line.specific_gravity = round(sg1, 2)


    @api.depends('wt_surface_dry', 'oven_dried_wt','wt_surface_dry_2', 'oven_dried_wt_2')
    def _compute_water_absorption(self):
        for line in self:
            wa1 = 0.0
            if line.result_oven_dried_wt != 0:
                wa1 = ((line.result_wt_surface_dry - line.result_oven_dried_wt) / line.result_oven_dried_wt) * 100
            line.water_absorption = round(wa1, 2)


   

     # Flakiness and Elongation 
    elongation_name = fields.Char(default="Elongation and Flakiness Index")
    elongation_visible = fields.Boolean(compute="_compute_visible")

    flakiness_name = fields.Char(default=" Flakiness Index")
    flakiness_visible = fields.Boolean(compute="_compute_visible")

    elongation_table = fields.One2many('mechanical.elongation.flakiness.crusher.line','parent_id',string="Elongation Flakiness Index",default=lambda self: self.default_flakiness_sizes())

    total_wt_retained_fl_el = fields.Float('Total',compute="_compute_total_el_fl")
    total_elongated_retained = fields.Float('Total Elongation',compute="_compute_total_elongation")
    total_flakiness_retained = fields.Float('Total Flakiness',compute="_compute_total_flakiness")

    aggregate_elongation = fields.Float('Aggregate Elongation Value in %',compute="_compute_aggregate_elongation")
    aggregate_flakiness = fields.Float('Aggregate Flakiness Value in %' ,compute="_compute_aggregate_flakiness")
    aggregate_combine = fields.Float('Aggregate Elongation & Flakiness Value in %',compute="_compute_aggregate_combine")


    aggregate_combine_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_aggregate_combine_conformity", store=True)

    @api.depends('aggregate_combine','eln_ref','grade')
    def _compute_aggregate_combine_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.aggregate_combine_conformity = 'na'
                continue

            record.aggregate_combine_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','70ef993d-d2f8-424c-9729-4e081d647bb1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','70ef993d-d2f8-424c-9729-4e081d647bb1')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.aggregate_combine - record.aggregate_combine*mu_value
                    upper = record.aggregate_combine + record.aggregate_combine*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.aggregate_combine_conformity = 'pass'
                        break
                    else:
                        record.aggregate_combine_conformity = 'fail'

    aggregate_combine_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_aggregate_combine_nabl", store=True)

    @api.depends('aggregate_combine','eln_ref','grade')
    def _compute_aggregate_combine_nabl(self):
        
        for record in self:
            record.aggregate_combine_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','70ef993d-d2f8-424c-9729-4e081d647bb1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','70ef993d-d2f8-424c-9729-4e081d647bb1')]).parameter_table
            # for material in materials:
                # if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.aggregate_combine - record.aggregate_combine*mu_value
            upper = record.aggregate_combine + record.aggregate_combine*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.aggregate_combine_nabl = 'pass'
                break
            else:
                record.aggregate_combine_nabl = 'fail'


    @api.depends('elongation_table.wt_retained')
    def _compute_total_el_fl(self):
        for record in self:
            record.total_wt_retained_fl_el = sum(record.elongation_table.mapped('wt_retained'))

    @api.depends('elongation_table.elongated_retained')
    def _compute_total_elongation(self):
        for record in self:
            record.total_elongated_retained = sum(record.elongation_table.mapped('elongated_retained'))

    @api.depends('elongation_table.flakiness_retained')
    def _compute_total_flakiness(self):
        for record in self:
            record.total_flakiness_retained = sum(record.elongation_table.mapped('flakiness_retained'))

    @api.depends('total_wt_retained_fl_el','total_elongated_retained')
    def _compute_aggregate_elongation(self):
        for record in self:
            if record.total_elongated_retained != 0:
                record.aggregate_elongation = record.total_elongated_retained/record.total_wt_retained_fl_el * 100
            else:
                record.aggregate_elongation = 0

    @api.depends('total_wt_retained_fl_el','total_flakiness_retained')
    def _compute_aggregate_flakiness(self):
        for record in self:
            if record.total_flakiness_retained != 0:
                record.aggregate_flakiness = record.total_flakiness_retained/record.total_wt_retained_fl_el*100
            else:
                record.aggregate_flakiness = 0
    

    @api.depends('total_wt_retained_fl_el','total_flakiness_retained')
    def _compute_aggregate_combine(self):
        for record in self:
            record.aggregate_combine = round(record.aggregate_elongation+record.aggregate_flakiness,2)
            



   
    @api.model
    def default_flakiness_sizes(self):
        default_lines = [
            (0, 0, {'sieve_size': '40 - 31.5'}),
            (0, 0, {'sieve_size': '31.5 - 25'}),
            (0, 0, {'sieve_size': '25 - 20'}),
            (0, 0, {'sieve_size': '20 - 16'}),
            (0, 0, {'sieve_size': '16 - 12.5'}),
            (0, 0, {'sieve_size': '12.5 - 10'}),
            (0, 0, {'sieve_size': '10 - 6.3'}),
            (0, 0, {'sieve_size': 'Pan'}),
            
        ]
        return default_lines   



    # Sieve Analysis 
    weight_of_sample = fields.Float(string="Weight of Sample in gms")
    sieve_analysis_name = fields.Char("Name",default="Sieve Analysis")
    sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

    sieve_analysis_child_lines = fields.One2many('mechanical.crusher.run.macadam.sieve.analysis.line','parent_id',string="Parameter")
    total_sieve_analysis = fields.Float(string="Total",compute="_compute_total_sieve")


    def default_get(self, fields):
        print("From Default Value")
        res = super(CrusherRunMacadamMechanical, self).default_get(fields)
        default_sieve_sizes = []
        
        # Safely get eln_ref with default None if not exists
        eln_ref = res.get('eln_ref') 
        
        if eln_ref:
            eln = self.env['lerm.eln'].sudo().browse(eln_ref)
            if not eln.exists():
                return res
                
            size_str = eln.size_id.size or ''
            grade_str = (eln.grade_id.grade or '').lower()
            
            # Define mappings
            if grade_str == 'single sized aggregate':
                sieve_mapping = {
                    63: ['80 mm', '63 mm', '40 mm', '20 mm', '10 mm', 'pan'],
                    40: ['63 mm', '40 mm', '20 mm', '10 mm', 'pan'],
                    20: ['40 mm', '20 mm', '10 mm', '4.75 mm', 'pan'],
                    16: ['20 mm', '16 mm', '10 mm', '4.75 mm', 'pan'],
                    12: ['16 mm', '12.5 mm', '10 mm', '4.75 mm', 'pan'],
                    10: ['12.5 mm', '10 mm', '4.75 mm', '2.36 mm', 'pan'],
                }
                specific_limits_mapping = {
                    63: ['100', '85 - 100', '0 - 30', '0 - 5', '0 - 5', '0'],
                    40: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                    20: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                    16: ['100', '85 - 100', '0 - 30', '0 - 5', '0'],
                    12: ['100', '85 - 100', '0 - 45', '0 - 10', '0'],
                    10: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                }
            elif grade_str == 'graded aggregate':
                sieve_mapping = {
                    40: ['80 mm', '40 mm', '20 mm', '10 mm','4.75 mm','pan'],
                    20: ['40 mm', '20 mm', '10 mm', '4.75 mm','pan'],
                    16: ['20 mm', '16 mm', '10 mm', '4.75 mm', 'pan'],
                    12: ['16 mm', '12.5 mm', '10 mm', '4.75 mm', 'pan'],
                }
                specific_limits_mapping = {
                    40: ['100', '95 - 100', '30 - 70', '10 - 35','0 - 5', '0'],
                    20: ['100', '95 - 100', '25 - 55', '0 - 10', '0'],
                    16: ['100', '90 - 100', '30 - 70', '0 - 10', '0'],
                    12: ['100', '90 - 100', '40 - 85', '0 - 10', '0'],
                }
            else:
                return res

            # Extract numeric part
            match = re.search(r'\d+', size_str)
            if match:
                number = int(match.group())
                sieve_list = sieve_mapping.get(number, [])
                specific_limits = specific_limits_mapping.get(number, [])
                
                # Check if lists have same length
                # if len(sieve_list) != len(specific_limits):
                #     _logger.warning(f"Mismatch in sieve sizes and limits for size {number}")
                #     return res
                    
                # Create sieve analysis lines
                for sieve_size, specific_limit in zip(sieve_list, specific_limits):
                    size = {
                        'sieve_size': sieve_size,
                        'specific_limits': specific_limit,
                    }
                    default_sieve_sizes.append((0, 0, size))
                
                res['sieve_analysis_child_lines'] = default_sieve_sizes

        return res
    
    def populate_sieve_analysis_lines(self):
        self.ensure_one()

        eln = self.eln_ref
        if not eln:
            return

        size_str = eln.size_id.size or ''
        grade_str = (eln.grade_id.grade or '').lower()

        if grade_str == 'single sized aggregate':
            specific_limits_mapping = {
                63: ['100', '85 - 100', '0 - 30', '0 - 5', '0 - 5', '0'],
                40: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                20: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
                16: ['100', '85 - 100', '0 - 30', '0 - 5', '0'],
                12: ['100', '85 - 100', '0 - 45', '0 - 10', '0'],
                10: ['100', '85 - 100', '0 - 20', '0 - 5', '0'],
            }
        elif grade_str == 'graded aggregate':
            specific_limits_mapping = {
                40: ['100', '95 - 100', '30 - 70', '10 - 35', '0 - 5', '0'],
                20: ['100', '95 - 100', '25 - 55', '0 - 10', '0'],
                16: ['100', '90 - 100', '30 - 70', '0 - 10', '0'],
                12: ['100', '90 - 100', '40 - 85', '0 - 10', '0'],
            }
        else:
            return

        match = re.search(r'\d+', size_str)
        if match:
            number = int(match.group())
            specific_limits = specific_limits_mapping.get(number, [])

            # Only update specific_limits of existing lines
            for line, specific_limit in zip(self.sieve_analysis_child_lines, specific_limits):
                line.specific_limits = specific_limit




    def calculate_sieve(self): 
        for record in self:
            # import wdb; wdb.set_trace()
            record.populate_sieve_analysis_lines()  # replace default_get call
            for line in record.sieve_analysis_child_lines:
                # print("Rows",str(line.percent_retained))
                previous_line = line.serial_no - 1
                if previous_line == 0:
                    if line.percent_retained == 0:
                        line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2),
                                    'passing_percent': 100 ,})
                    else:
                        line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2),
                                    'passing_percent': round(100 -line.percent_retained - line.percent_retained,2),})
                else:
                    previous_line_record = self.env['mechanical.crusher.run.macadam.sieve.analysis.line'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
                    line.write({'cumulative_retained': previous_line_record + line.percent_retained,
                                'passing_percent': round(100-(previous_line_record + line.percent_retained),2),})
                    
                    # print("Previous Cumulative",previous_line_record)
                    

    
    @api.depends('sieve_analysis_child_lines.wt_retained')
    def _compute_total_sieve(self):
        for record in self:
            print("recordd",record)
            record.total_sieve_analysis = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))

    @api.onchange('sieve_analysis_child_lines')
    def _onchange_sieve_analysis_child_lines(self):
        for rec in self:
            pan_line = None
            total_retained = 0.0            
            # Find all unique sieve sizes except pan
            all_sieves = set()
            for line in rec.sieve_analysis_child_lines:
                if line.sieve_size and line.sieve_size.lower() != 'pan':
                    all_sieves.add(line.sieve_size.strip())
            
            # Calculate total retained for all non-pan sieves
            for line in rec.sieve_analysis_child_lines:
                if line.sieve_size and line.sieve_size.lower() == 'pan':
                    pan_line = line
                elif line.sieve_size in all_sieves:  # Include all non-pan sieves
                    total_retained += line.wt_retained or 0.0

            # Update pan weight if pan exists and we have a sample weight
            if pan_line and rec.weight_of_sample:
                pan_line.wt_retained = rec.weight_of_sample - total_retained


    # @api.depends('sieve_analysis_child_lines.wt_retained')
    # def _compute_cumulative_sieve(self):
    #     for record in self:
    #         print("recordd",record)
    #         record.cumulative = sum(record.sieve_analysis_child_lines.mapped('wt_retained'))


    # # Aggregate grading  

    # aggregate_grading_name = fields.Char("Name",default="All in Aggregate Grading")
    # aggregate_grading_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

    # aggregate_grading_child_lines = fields.One2many('mechanical.aggregate.grading.line','parent_id',string="Parameter")
    # total_aggregate_grading = fields.Integer(string="Total",compute="_compute_total_aggregate_grading")
    # # cumulative_aggregate_grading = fields.Float(string="Cumulative",compute="_compute_cumulative_aggregate_grading")


    # def calculate_aggregate(self): 
    #     for record in self:
    #         for line in record.aggregate_grading_child_lines:
    #             print("Rows",str(line.percent_retained))
    #             previous_line = line.serial_no - 1
    #             if previous_line == 0:
    #                 if line.percent_retained == 0:
    #                     # print("Percent retained 0",line.percent_retained)
    #                     line.write({'cumulative_retained': line.percent_retained})
    #                     line.write({'passing_percent': 100 })
    #                 else:
    #                     # print("Percent retained else",line.percent_retained)
    #                     line.write({'cumulative_retained': line.percent_retained})
    #                     line.write({'passing_percent': 100 -line.percent_retained})
    #             else:
    #                 previous_line_record = self.env['mechanical.aggregate.grading.line'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
    #                 line.write({'cumulative_retained': previous_line_record + line.percent_retained})
    #                 line.write({'passing_percent': 100-(previous_line_record + line.percent_retained)})
    #                 print("Previous Cumulative",previous_line_record)
                    

 

    # # @api.depends('aggregate_grading_child_lines.wt_retained')
    # # def _compute_cumulative_aggregate_grading(self):
    # #     for record in self:
    # #         print("recordd",record)
    # #         record.cumulative_aggregate_grading = sum(record.aggregate_grading_child_lines.mapped('wt_retained'))


    # @api.depends('aggregate_grading_child_lines.wt_retained')
    # def _compute_total_aggregate_grading(self):
    #     for record in self:
    #         print("recordd",record)
    #         record.total_aggregate_grading = sum(record.aggregate_grading_child_lines.mapped('wt_retained'))

    # Impact Value 
    impact_value_name = fields.Char("Name",default="Aggregate Impact Value")
    impact_visible = fields.Boolean("Impact Visible",compute="_compute_visible")

    impact_value_child_lines = fields.One2many('mechanical.impact.value.crusher.run.macadam.line','parent_id',string="Parameter")

    average_impact_value = fields.Float(string="Average Aggregate Impact Value", compute="_compute_average_impact_value")


    average_impact_value_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_average_impact_value_conformity", store=True)

    @api.depends('average_impact_value','eln_ref','grade')
    def _compute_average_impact_value_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_impact_value_conformity = 'na'
                continue

            record.average_impact_value_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fbf04a49-ea53-4b14-acd4-1797e06669ae')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fbf04a49-ea53-4b14-acd4-1797e06669ae')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_impact_value - record.average_impact_value*mu_value
                    upper = record.average_impact_value + record.average_impact_value*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_impact_value_conformity = 'pass'
                        break
                    else:
                        record.average_impact_value_conformity = 'fail'

    impact_value_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_impact_value_nabl", store=True)

    @api.depends('average_impact_value','eln_ref','grade')
    def _compute_average_impact_value_nabl(self):
        
        for record in self:
            record.impact_value_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fbf04a49-ea53-4b14-acd4-1797e06669ae')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fbf04a49-ea53-4b14-acd4-1797e06669ae')]).parameter_table
            # for material in materials:
                # if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_impact_value - record.average_impact_value*mu_value
            upper = record.average_impact_value + record.average_impact_value*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.impact_value_nabl = 'pass'
                break
            else:
                record.impact_value_nabl = 'fail'


    @api.depends('impact_value_child_lines.impact_value')
    def _compute_average_impact_value(self):
        for record in self:
            if record.impact_value_child_lines:
                sum_impact_value = sum(record.impact_value_child_lines.mapped('impact_value'))
                record.average_impact_value = ((sum_impact_value / len(record.impact_value_child_lines)))
            else:
                record.average_impact_value = 0.0



    



    
    
    








    @api.depends('eln_ref')
    def _compute_visible(self):
        for record in self:
            
            record.abrasion_visible = False
            record.water_absorp_visible = False
            
            
            record.elongation_visible = False
            record.flakiness_visible = False
            
            record.sieve_visible = False
            # record.aggregate_grading_visible = False
            
            record.impact_visible = False




            for sample in record.sample_parameters:
                if sample.internal_id == 'b22b1917-4510-4422-9869-d75f6e8893db':
                    record.abrasion_visible = True
                if sample.internal_id == '2113f38a-d129-4efe-bac4-ff5826dface8':
                    record.water_absorp_visible = True
                if sample.internal_id == 'fbf04a49-ea53-4b14-acd4-1797e06669ae':
                    record.impact_visible = True

                if sample.internal_id == '70ef993d-d2f8-424c-9729-4e081d647bb1':
                    record.elongation_visible = True
                    # record.flakiness_visible = True

                if sample.internal_id == 'c8a5f37e-1449-4794-a854-cdb169493a1a':
                    record.flakiness_visible = True
                    # record.elongation_visible = True
                
                if sample.internal_id == '1bb99b27-9599-4754-9d70-6097e17ea5b0':
                    record.sieve_visible = True
                # if sample.internal_id == '240dfed8-a5d1-44fb-a485-3930fdbca7a7':
                #     record.aggregate_grading_visible = True
                

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()
            # Elongation
            if result.parameter.internal_id == '1bb99b27-9599-4754-9d70-6097e17ea5b0':
                result.calculated = True
            
            if result.parameter.internal_id == '70ef993d-d2f8-424c-9729-4e081d647bb1':
                result.result_char = round(self.aggregate_elongation,2)
                result.calculated = True
                if self.aggregate_combine_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Flakiness
            if result.parameter.internal_id == 'c8a5f37e-1449-4794-a854-cdb169493a1a':
                result.result_char = round(self.aggregate_flakiness,2)
                result.calculated = True
                if self.aggregate_combine_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            

            # # specific gravity 
            # if result.parameter.internal_id == '2113f38a-d129-4efe-bac4-ff5826dface8':
            #     result.calculated = True
            #     result.result_char = round(self.specific_gravity,2)
            #     if self.water_absorp_nabl == 'pass':
            #         result.nabl_status = 'nabl'
            #     else:
            #         result.nabl_status = 'non-nabl'
            #     continue

            # water absorbtion
            if result.parameter.internal_id == '2113f38a-d129-4efe-bac4-ff5826dface8':
                result.calculated = True
                result.result_char = round(self.water_absorption,2)
                if self.water_absorp_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            # impact value 
            if result.parameter.internal_id == 'fbf04a49-ea53-4b14-acd4-1797e06669ae':
                result.calculated = True
                result.result_char = round(self.average_impact_value,2)
                if self.impact_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

           

            

           

            # Los Angeles Abrasion Value
            if result.parameter.internal_id == 'b22b1917-4510-4422-9869-d75f6e8893db':
                result.calculated = True
                result.result_char = round(self.abrasion_value_percentage,2)
                if self.abrasion_value_percentage_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            

            # All-in-Aggregate Grading (Size,80 mm,40 mm,20 mm,4.75 mm,600 µm,150 µm )
            if result.parameter.internal_id == '240dfed8-a5d1-44fb-a485-3930fdbca7a7':
                result.calculated = True
                

            

            # Angularity Number
            if result.parameter.internal_id == '5c163fc2-c88c-4233-921e-1eae56c3ba23':
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
        record = super(CrusherRunMacadamMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()
        self.default_get(fields)

        return super(CrusherRunMacadamMechanical, self).read(fields=fields, load=load)

   
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
        record = self.env['mechanical.crusher.run.macadam'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id






class SieveAnalysisRunLine(models.Model):
    _name = "mechanical.crusher.run.macadam.sieve.analysis.line"
    parent_id = fields.Many2one('mechanical.crusher.run.macadam', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size mm")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    percent_retained = fields.Float(string='% of Weight Retained', compute="_compute_percent_retained",digits=(16,2))
    cumulative_retained = fields.Float(string="% of Cumulative Wt. Retained ", store=True,digits=(16,2))
    passing_percent = fields.Float(string="% of wt passing",digits=(16,2))
    specific_limits = fields.Char(string="Specified Limits",store=True)



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(SieveAnalysisRunLine, self).create(vals)

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

            new_self = super(SieveAnalysisRunLine, self).write(vals)

            if 'wt_retained' in vals:
                for record in self:
                    # record.parent_id._compute_total()
                    pass

            return new_self

        return super(SieveAnalysisRunLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(SieveAnalysisRunLine, self).unlink()

        if parent_id:
            parent_id.sieve_analysis_child_lines._reorder_serial_numbers()

        return res





    @api.depends('wt_retained', 'parent_id.weight_of_sample')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = (record.wt_retained / self.parent_id.weight_of_sample) * 100
            except ZeroDivisionError:
                record.percent_retained = 0


    @api.depends('cumulative_retained')
    def _compute_cum_retained(self):
        self.cumulative_retained=0
        


    def get_previous_record(self):
        for record in self:
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_child_lines, key=lambda r: r.id)
            # index = sorted_lines.index(record)
            # print("Working")



       




class ElongationFlaknessLine(models.Model):
    _name = "mechanical.elongation.flakiness.crusher.line"
    parent_id = fields.Many2one('mechanical.crusher.run.macadam', string="Parent Id")

    sieve_size = fields.Char(string="IS Sieve Size")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    elongated_retained = fields.Float(string="Elongated Retained in gms")
    flakiness_retained = fields.Float(string="Flakiness Retained in gms")



    
class ImpactValueLine(models.Model):
    _name = "mechanical.impact.value.crusher.run.macadam.line"
    parent_id = fields.Many2one('mechanical.crusher.run.macadam',string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)
    total_wt_aggregate = fields.Float(string="Wt of Aggregate Passing I.S Sieve 12.5 mm but retained in I.S. Sieve 10 mm Gms (W1)")
    wt_of_aggregate_retained = fields.Float(string="Wt of Aggregate Retained on  I.S Sieve 2.36  mm after the test Gms (W2)")
    wt_of_aggregate_passing = fields.Float(string="Wt of Stone Pieces Passing I.S Sieve 2.36 mm after the test ( W3)", compute="_compute_wt_of_aggregate_retained")
    impact_value = fields.Float(string="Aggregate Impact value", compute="_compute_impact_value")

    @api.depends('total_wt_aggregate', 'wt_of_aggregate_retained')
    def _compute_wt_of_aggregate_retained(self):
        for rec in self:
            rec.wt_of_aggregate_passing = rec.total_wt_aggregate - rec.wt_of_aggregate_retained



    @api.depends('wt_of_aggregate_passing', 'total_wt_aggregate')
    def _compute_impact_value(self):
        for rec in self:
            if rec.total_wt_aggregate != 0:
                rec.impact_value = (rec.wt_of_aggregate_passing / rec.total_wt_aggregate) * 100
            else:
                rec.impact_value = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(ImpactValueLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class crusherRunMacadamNotes(models.Model):
    _name = "crusher.run.macadam.notes"

    parent_id = fields.Many2one('mechanical.crusher.run.macadam',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")


