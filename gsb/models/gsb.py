from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math
from decimal import Decimal
import matplotlib.pyplot as plt
import io
import base64
from odoo.tools.float_utils import float_round

class GsbMechanical(models.Model):
    _name = "mechanical.gsb"
    _inherit = "lerm.eln"
    _description = 'mechanical.gsb'
    _rec_name = "name"



    name = fields.Char("Name",default="GSB")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    temprature = fields.Integer("Temperature (°C)", digits=(10,2))
    humidity = fields.Integer("Humidity (%)", digits=(10,2))

    week_no = fields.Char("Week No")

    other_details = fields.Char("Other Details")

    condition = fields.Char("Condition")

    description_work = fields.Text("Description Of Work")



    # remark

    notes_id = fields.One2many('gsb.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(GsbMechanical, self).default_get(fields)

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
            'res_model': 'gsb.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }
    
    

    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(GsbMechanical, self).create(vals)
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
        record = self.env['mechanical.gsb'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)
            
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.dry_gradation_visible = False
            record.water_absorbtion_visible  = False  
            record.elongation_visible = False
            record.flakiness_visible = False
            record.abrasion_visible = False
            record.impact_visible = False
            record.plastic_visible = False
            record.liquid_limit_visible = False
            record.plasticity_index_visible = False
            record.density_relation_visible = False
            record.cbr_visible = False
            record.loose_density_visible = False

            record.crushing_visible = False
            record.specigic_gravity_visible = False

            record.clay_lump_visible = False
            record.light_weight_visible = False
            record.finer75_visible = False
            record.fine10_visible = False

            record.soudness_magnesium_visible = False
            record.soudness_visible = False


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '214578fgtr-560e-41f9-9f7e-3455c9b2925d':
                    record.dry_gradation_visible = True
                if sample.internal_id == '216587ghtr-4e73-44ca-93ed-442f74cd1e9b':
                    record.water_absorbtion_visible  = True  
                if sample.internal_id == '32147hgv4-599e-4569-8cd2-48e1dc120714':
                    record.elongation_visible = True
                    record.flakiness_visible = True
                if sample.internal_id == '56482hgt1-70fb-4c47-baec-9880be12d765':
                    record.flakiness_visible = True
                    record.elongation_visible = True
                if sample.internal_id == '2145hgt1-3f1c-4aca-ac94-3c2bb0f034e2':
                    record.abrasion_visible = True
                if sample.internal_id == '21457gtr4-a55f-47ac-aee6-9f37d733ccca':
                    record.impact_visible = True
                if sample.internal_id == '14527gthy-f86e-4a5f-bd15-a5b0c173b5ed':
                    record.plastic_visible  = True  
                if sample.internal_id == '12547ftd4-3ed1-4021-90a2-47651f0ed81d':
                    record.liquid_limit_visible = True
                if sample.internal_id == '24584fgrt-1611-4790-9410-ef5db6233932':
                    record.liquid_limit_visible = True
                    record.plasticity_index_visible = True
                if sample.internal_id == 'm21547tyu-0579-4221-8a82-bbfadcd3131f':
                    record.density_relation_visible = True
                if sample.internal_id == 'rt14752hyt-b27e-48c6-81b8-900521446761':
                    record.cbr_visible = True

                if sample.internal_id == '657hgt1f-d557-438e-8fd1-2c619a334d02':
                    record.loose_density_visible = True

                if sample.internal_id == '2547832k-3bf8-4ae5-8e5d-dfe983111f71':
                    record.crushing_visible = True

                if sample.internal_id == '2147jjhy-1d2c-4d3b-9ebe-ecb0b5e1221e':
                    record.specigic_gravity_visible = True

                if sample.internal_id == '3214ytre-21ad-41eb-a602-f448f996eb2f':
                    record.clay_lump_visible = True
                if sample.internal_id == 'ii2145y-2550-4e1e-a28e-8526295e733f':
                    record.light_weight_visible = True

                if sample.internal_id == '3214ytre-c865-453c-9cd6-993a5a59ad95':
                    record.finer75_visible = True

                if sample.internal_id == '3244uuyy-4369-491d-93a6-030514c29661':
                    record.fine10_visible = True

                if sample.internal_id == '6547ytre-4369-491d-93a6-030514c29663':
                    record.soudness_magnesium_visible = True
                if sample.internal_id == 'c8c32457-2457-4f22-bae6-b81de73e6c2':
                    record.soudness_visible = True


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

            # Dry Gradation
            if result.parameter.internal_id == '214578fgtr-560e-41f9-9f7e-3455c9b2925d':
                result.calculated = True
            
            # Water Absorbtion
            if result.parameter.internal_id == '216587ghtr-4e73-44ca-93ed-442f74cd1e9b':
                result.result_char = round(self.water_absorbtion,2)
                result.calculated = True
                if self.water_absorbtion_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '3214ytre-21ad-41eb-a602-f448f996eb2f':
                result.result_char = round(self.clay_lumps_percent,2)
                result.calculated = True
                if self.clay_lumps_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '2147jjhy-1d2c-4d3b-9ebe-ecb0b5e1221e':
                result.result_char = round(self.average_specific_gravity,2)
                result.calculated = True
                if self.average_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '2547832k-3bf8-4ae5-8e5d-dfe983111f71':
                result.result_char = round(self.average_crushing_value,2)
                result.calculated = True
                if self.average_crushing_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Elongation and Flakiness Index
            if result.parameter.internal_id == '32147hgv4-599e-4569-8cd2-48e1dc120714':
                result.result_char = round(self.aggregate_elongation,2)
                result.calculated = True
                if self.aggregate_elongation_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Elongation and Flakiness Index
            if result.parameter.internal_id == '56482hgt1-70fb-4c47-baec-9880be12d765':
                result.result_char = round(self.aggregate_flakiness,2)
                result.calculated = True
                if self.aggregate_flakiness_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Abrasion Value
            if result.parameter.internal_id == '2145hgt1-3f1c-4aca-ac94-3c2bb0f034e2':
                result.result_char = round(self.abrasion_value_percentage,2)
                result.calculated = True
                if self.abrasion_value_percentage_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Impact Value
            if result.parameter.internal_id == '21457gtr4-a55f-47ac-aee6-9f37d733ccca':
                result.result_char = round(self.average_impact_value,2)
                result.calculated = True
                if self.average_impact_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Plastic Limit
            if result.parameter.internal_id == '14527gthy-f86e-4a5f-bd15-a5b0c173b5ed':
                result.result_char = round(self.average_plastic_moisture,2)
                result.calculated = True
                if self.average_plastic_moisture_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Liquid Limit
            if result.parameter.internal_id == '12547ftd4-3ed1-4021-90a2-47651f0ed81d':
                result.result_char = round(self.liquid_limit,2)
                result.calculated = True
                if self.liquid_limit_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Plasticity Index Visible
            if result.parameter.internal_id == '24584fgrt-1611-4790-9410-ef5db6233932':
                result.result_char = round(self.plasticity_index,2)
                result.calculated = True
                if self.plasticity_index_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '657hgt1f-d557-438e-8fd1-2c619a334d02':
                result.result_char = round(self.loose_density,2)
                result.calculated = True
                if self.loose_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'ii2145y-2550-4e1e-a28e-8526295e733f':
                result.result_char = round(self.light_weight_percent,2)
                result.calculated = True
                if self.light_weight_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '3214ytre-c865-453c-9cd6-993a5a59ad95':
                result.result_char = round(self.material_finer75,2)
                result.calculated = True
                if self.material_finer75_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '3244uuyy-4369-491d-93a6-030514c29661':
                result.result_char = round(self.load_10percent_fine_values,2)
                result.calculated = True
                if self.load_10percent_fine_values_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'c8c32457-2457-4f22-bae6-b81de73e6c2':
                result.result_char = round(self.total_avg_sulphae,2)
                result.calculated = True
                if self.total_avg_sulphae_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            

            # Density Relation Using Heavy Compaction
            if result.parameter.internal_id == 'm21547tyu-0579-4221-8a82-bbfadcd3131f':
                # result.result_char = round(self.aggregate_elongation,2)
                result.calculated = True
                # if self.aggregate_combine_conformity == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue

            # CBR
            if result.parameter.internal_id == 'rt14752hyt-b27e-48c6-81b8-900521446761':
                # result.result_char = round(self.aggregate_elongation,2)
                result.calculated = True
                # if self.aggregate_combine_conformity == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue


           
            if result.parameter.internal_id == '6547ytre-4369-491d-93a6-030514c29663':
                # result.result_char = round(self.aggregate_elongation,2)
                result.calculated = True
                # if self.aggregate_combine_conformity == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue







        return {
                'view_mode': 'form',
                'res_model': "lerm.eln",
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.eln_ref.id,
                
            }

    soudness_magnesium_name = fields.Char("Name",default="Soundness  Test ")
    soudness_magnesium_visible = fields.Boolean("Soundness Test",compute="_compute_visible")
    soudness_visible = fields.Boolean("Soundness Test",compute="_compute_visible")

    soudness_child_lines = fields.One2many('gsb.soudness.line','parent_id',string="Parameter")

    sieve_name = fields.Char("Name",default="Gradation Of Original Sample")
    # sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

    wt_of_sample = fields.Float(string="Wt. Of Sample Taken For Analysis (gms) = ", digits=(8,3))
 
    sieve_analysis_soundness_lines = fields.One2many('mechanical.gsb.sieve.analysis.line','parent_id',string="Sieve Analysis",default=lambda self: self._default_sieve_analysis_soundness_lines())

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
            (0, 0, {'sieve_size': 'Above 80mm', 'particle_size': '80mm'}),
            (0, 0, {'sieve_size': '80mm', 'particle_size': '63mm'}),
            (0, 0, {'sieve_size': '63mm', 'particle_size': '40mm'}),
            (0, 0, {'sieve_size': '40mm', 'particle_size': '20mm'}),
            (0, 0, {'sieve_size': '20mm', 'particle_size': '10mm'}),
            (0, 0, {'sieve_size': '10mm', 'particle_size': '4.75mm'}),
        ]
        return default_lines


   


    def calculate_sound_sieve(self): 
        for record in self:
            record.calc_mode = True
            record.submit_mode = False
            # import wdb; wdb.set_trace()
            previous_cumulative = 0  
            for line in record.sieve_analysis_soundness_lines:
                print("Rows", str(line.percent_retained))
                previous_line = line.serial_no - 1

               

                # Normal sieve calculation
                if previous_line == 0:
                    cumulative_retained = line.percent_retained
                else:
                    previous_line_record = self.env['mechanical.gsb.sieve.analysis.line'].sudo().search([
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
        record.submit_mode_soudness = True


    ouantitative_name = fields.Char("Name",default="Quantitatively Examination :-")
    # sieve_visible = fields.Boolean("Sieve Analysis Visible",compute="_compute_visible")

 
    ouantitative_soundness_lines = fields.One2many('gsb.ouantitative.line','parent_id',string="Sieve Analysis",default=lambda self: self._default_ouantitative_soundness_lines())

    
    @api.model
    def _default_ouantitative_soundness_lines(self):
        default_lines = [
            (0, 0, {'size': '+80mm'}),
            (0, 0, {'size': '80mm to 63mm'}),
            (0, 0, {'size': '63mm to 40mm'}),
            (0, 0, {'size': '40mm to 20mm'}),
            (0, 0, {'size': '20mm to 10mm'}),
            (0, 0, {'size': '10mm to 4.75mm'})
            
            
        ]
        return default_lines


    quantitative_name = fields.Char("Name",default="Quantitatively Examination")

    quantitative_soundness_lines = fields.One2many('gsb.quantitative.line','parent_id',string="Sieve Analysis",default=lambda self: self._default_quantitative_soundness_lines())

    
    @api.model
    def _default_quantitative_soundness_lines(self):
        default_lines = [
            (0, 0, {'passing': 'Above 80mm', 'retained': '80mm', 'sieve_magnesium': '80mm'}),
            (0, 0, {'passing': '80mm', 'retained': '63mm', 'sieve_magnesium': '63mm'}),
            (0, 0, {'passing': '63mm', 'retained': '40mm', 'sieve_magnesium': '31.5mm'}),
            (0, 0, {'passing': '40mm', 'retained': '20mm', 'sieve_magnesium': '16.0mm'}),
            (0, 0, {'passing': '20mm', 'retained': '10mm', 'sieve_magnesium': '8mm'}),
            (0, 0, {'passing': '10mm', 'retained': '4.75mm', 'sieve_magnesium': '4mm'}),
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c8c32457-2457-4f22-bae6-b81de73e6c2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c8c32457-2457-4f22-bae6-b81de73e6c2')]).parameter_table
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
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_total_avg_sulphae_nabl", store=True)

    @api.depends('total_avg_sulphae','eln_ref','grade')
    def _compute_total_avg_sulphae_nabl(self):
        
        for record in self:
            record.total_avg_sulphae_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c8c32457-2457-4f22-bae6-b81de73e6c2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c8c32457-2457-4f22-bae6-b81de73e6c2')]).parameter_table
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
    

    name_10fine = fields.Char(default="10% Fine Value")
    fine10_visible = fields.Boolean("10% Fine Visible",compute="_compute_visible")

    wt_sample_10fine = fields.Float("Weight of Sample taken in gms, A")
    wt_sample_passing_10fine = fields.Float("Weight of sample passing 2.36 mm IS sieve after applying load in 10 min, B")
    percent_of_fines = fields.Float("Percentage of Fines",compute="_compute_percent_fines")
    load_applied_10fine = fields.Float("Load applied in 10 min, X kN")
    load_10percent_fine_values = fields.Float("Load for 10 percent fines value",compute="_compute_load_10percent_fine_values")

    @api.depends('wt_sample_10fine','wt_sample_passing_10fine')
    def _compute_percent_fines(self):
        for record in self:
            if record.wt_sample_10fine != 0:
                record.percent_of_fines = (record.wt_sample_passing_10fine / record.wt_sample_10fine )*100
            else:
                record.percent_of_fines = 0

    @api.depends('percent_of_fines','load_applied_10fine')
    def _compute_load_10percent_fine_values(self):
        for record in self:
            if record.percent_of_fines != 0:
                record.load_10percent_fine_values = (14 * record.load_applied_10fine)/(record.percent_of_fines + 4)
            else:
                record.load_10percent_fine_values = 0


    load_10percent_fine_values_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_load_10percent_fine_values_conformity", store=True)



    @api.depends('load_10percent_fine_values','eln_ref','grade')
    def _compute_load_10percent_fine_values_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.load_10percent_fine_values_conformity = 'na'
                continue

            record.load_10percent_fine_values_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3244uuyy-4369-491d-93a6-030514c29661')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3244uuyy-4369-491d-93a6-030514c29661')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.load_10percent_fine_values - record.load_10percent_fine_values*mu_value
                    upper = record.load_10percent_fine_values + record.load_10percent_fine_values*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.load_10percent_fine_values_conformity = 'pass'
                        break
                    else:
                        record.load_10percent_fine_values_conformity = 'fail'

    load_10percent_fine_values_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_load_10percent_fine_values_nabl", store=True)

    @api.depends('load_10percent_fine_values','eln_ref','grade')
    def _compute_load_10percent_fine_values_nabl(self):
        
        for record in self:
            record.load_10percent_fine_values_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3244uuyy-4369-491d-93a6-030514c29661')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3244uuyy-4369-491d-93a6-030514c29661')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.load_10percent_fine_values - record.load_10percent_fine_values*mu_value
            upper = record.load_10percent_fine_values + record.load_10percent_fine_values*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.load_10percent_fine_values_nabl = 'pass'
                break
            else:
                record.load_10percent_fine_values_nabl = 'fail'


    name_finer75 = fields.Char("Name",default="Material Finer than 75 Micron")
    finer75_visible = fields.Boolean("Finer 75 Visible",compute="_compute_visible")

    wt_sample_finer75 = fields.Float("Weight of Sample in gms")
    wt_dry_sample_finer75 = fields.Float("Weight of dry sample after retained in 75 microns")
    material_finer75 = fields.Float("Material finer than 75 micron in %",compute="_compute_finer75")

    material_finer75_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_material_finer75_conformity", store=True)

    @api.depends('material_finer75','eln_ref','grade')
    def _compute_material_finer75_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.material_finer75_conformity = 'na'
                continue

            record.material_finer75_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214ytre-c865-453c-9cd6-993a5a59ad95')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214ytre-c865-453c-9cd6-993a5a59ad95')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214ytre-c865-453c-9cd6-993a5a59ad95')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214ytre-c865-453c-9cd6-993a5a59ad95')]).parameter_table
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


    name_light_weight = fields.Char("Name",default="Deleterious Material (Light Weight Pieces)")
    light_weight_visible = fields.Boolean("Light Weight Visible",compute="_compute_visible")

    wt_sample_light_weight = fields.Float("Weight of Sample in gms")
    wt_dry_sample_light_weight = fields.Float("Weight of dry sample after retained in 75 microns")
    light_weight_percent = fields.Float("Light Weight Particle in %",compute="_compute_light_weight")

    light_weight_percent_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_light_weight_percent_conformity", store=True)

    @api.depends('light_weight_percent','eln_ref','grade')
    def _compute_light_weight_percent_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.light_weight_percent_conformity = 'na'
                continue

            record.light_weight_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ii2145y-2550-4e1e-a28e-8526295e733f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ii2145y-2550-4e1e-a28e-8526295e733f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.light_weight_percent - record.light_weight_percent*mu_value
                    upper = record.light_weight_percent + record.light_weight_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.light_weight_percent_conformity = 'pass'
                        break
                    else:
                        record.light_weight_percent_conformity = 'fail'

    light_weight_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_light_weight_percent_nabl", store=True)

    @api.depends('light_weight_percent','eln_ref','grade')
    def _compute_light_weight_percent_nabl(self):
        
        for record in self:
            record.light_weight_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ii2145y-2550-4e1e-a28e-8526295e733f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ii2145y-2550-4e1e-a28e-8526295e733f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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


    name_clay_lumps = fields.Char("Name",default="Deleterious Material (Clay Lumps)")
    clay_lump_visible = fields.Boolean("Clay Lump Visible",compute="_compute_visible")

    wt_sample_clay_lumps = fields.Float("Weight of Sample in gms")
    wt_dry_sample_clay_lumps = fields.Float("Weight of dry sample after retained in 75 microns")
    clay_lumps_percent = fields.Float("Clay Lumps in %",compute="_compute_clay_lumps")

    clay_lumps_percent_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_clay_lumps_percent_conformity", store=True)

    @api.depends('clay_lumps_percent','eln_ref','grade')
    def _compute_clay_lumps_percent_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.clay_lumps_percent_conformity = 'na'
                continue

            record.clay_lumps_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214ytre-21ad-41eb-a602-f448f996eb2f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214ytre-21ad-41eb-a602-f448f996eb2f')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214ytre-21ad-41eb-a602-f448f996eb2f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214ytre-21ad-41eb-a602-f448f996eb2f')]).parameter_table
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

    @api.depends('wt_sample_clay_lumps','wt_dry_sample_clay_lumps')
    def _compute_clay_lumps(self):
        for record in self:
            if record.wt_sample_clay_lumps != 0:
                record.clay_lumps_percent = ((record.wt_sample_clay_lumps - record.wt_dry_sample_clay_lumps)/record.wt_sample_clay_lumps * 100)
            else:
                record.clay_lumps_percent = 0



     #  Specigic Gravity
    specigic_gravity_fly = fields.Char("Name",default="Specific Gravity")
    specigic_gravity_visible = fields.Boolean("Specigic Gravity Visible",compute="_compute_visible")

    temp_percent_specific = fields.Float("Temperature °c")
    humidity_percent_specific = fields.Float("Humidity %")
    start_date_specific = fields.Date("Start Date")
    end_date_specific = fields.Date("End Date")


    wt_of_flyash_specific1 = fields.Float(string="Weight of Flyash (g)",default=45)
    wt_of_flyash_specific2 = fields.Float(string="Weight of Flyash (g)",default=45)

    intial_volume_specific1 = fields.Float(string="Initial Volume of kerosine (ml)")
    intial_volume_specific2 = fields.Float(string="Initial Volume of kerosine (ml)")

    final_volume_specific1 = fields.Float(string="Final Volume of kerosine and Flyash (After immersion in constant water bath) (ml)")
    final_volume_specific2 = fields.Float(string="Final Volume of kerosine and Flyash (After immersion in constant water bath) (ml)")
    
    displaced_volume1 = fields.Float(string="Displaced volume (cm³)",compute="_compute_volume1",digits=(12,1))
    displaced_volume2 = fields.Float(string="Displaced volume (cm³)",compute="_compute_volume2",digits=(12,1))

    specific_gravity1 = fields.Float(string="Specific Gravity",compute="_compute_specific1")
    specific_gravity2 = fields.Float(string="Specific Gravity",compute="_compute_specific2")

    average_specific_gravity = fields.Float(
        string="Average",
        compute="_compute_average_specific_gravity")

    @api.depends('final_volume_specific1','intial_volume_specific1')
    def _compute_volume1(self):
        for record in self:
            record.displaced_volume1 = record.final_volume_specific1 - record.intial_volume_specific1

    @api.depends('final_volume_specific2','intial_volume_specific2')
    def _compute_volume2(self):
        for record in self:
            record.displaced_volume2 = record.final_volume_specific2 - record.intial_volume_specific2

    @api.depends('wt_of_flyash_specific1','displaced_volume1')
    def _compute_specific1(self):
        for record in self:
            if record.displaced_volume1 != 0:
                record.specific_gravity1 = record.wt_of_flyash_specific1 / record.displaced_volume1
            else:
                record.specific_gravity1 = 0.0

    @api.depends('wt_of_flyash_specific2','displaced_volume2')
    def _compute_specific2(self):
        for record in self:
            if record.displaced_volume2 != 0:
                record.specific_gravity2 = record.wt_of_flyash_specific2 / record.displaced_volume2
            else:
                record.specific_gravity2 = 0.0

    

    @api.depends('specific_gravity1', 'specific_gravity2')
    def _compute_average_specific_gravity(self):
        for record in self:
            average = (record.specific_gravity1 + record.specific_gravity2) / 2
            record.average_specific_gravity = average


    average_specific_gravity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_average_specific_gravity_conformity", store=True)

    @api.depends('average_specific_gravity','eln_ref','grade')
    def _compute_average_specific_gravity_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_specific_gravity_conformity = 'na'
                continue

            record.average_specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147jjhy-1d2c-4d3b-9ebe-ecb0b5e1221e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147jjhy-1d2c-4d3b-9ebe-ecb0b5e1221e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_specific_gravity - record.average_specific_gravity*mu_value
                    upper = record.average_specific_gravity + record.average_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.average_specific_gravity_conformity = 'fail'

    average_specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_specific_gravity_nabl", store=True)
    
    @api.depends('average_specific_gravity','eln_ref','grade')
    def _compute_average_specific_gravity_nabl(self):
        
        for record in self:
            record.average_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147jjhy-1d2c-4d3b-9ebe-ecb0b5e1221e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2147jjhy-1d2c-4d3b-9ebe-ecb0b5e1221e')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_specific_gravity - record.average_specific_gravity*mu_value
            upper = record.average_specific_gravity + record.average_specific_gravity*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_specific_gravity_nabl = 'pass'
                break
            else:
                record.average_specific_gravity_nabl = 'fail'

    # Loose Density
    loose_density_name = fields.Char("Name",default="Loose Density ")
    loose_density_visible = fields.Boolean("Loose density  Visible",compute="_compute_visible")


    capacity_of_cylinder_loose = fields.Float(string="Capacity of Cylinder Use for Test in litre (V)")
    wtt_of_empty_cylinder_loose = fields.Float(string="Weight of empty cylinder (kg)")
    wtt_cylinder_aggregate_loose = fields.Float(string="Weight of cylinder + aggregate (kg)")
    mass_of_loose_aggregate = fields.Float("Mass of Loose Aggregate in Cylinder (A) – Kg",compute="_compute_mass_of_loose_aggregate")

    loose_density = fields.Float("Loose Buck Density (Ƴ1) = (A/V) Kg/lit",compute="_compute_loose_density")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','657hgt1f-d557-438e-8fd1-2c619a334d02')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','657hgt1f-d557-438e-8fd1-2c619a334d02')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','657hgt1f-d557-438e-8fd1-2c619a334d02')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','657hgt1f-d557-438e-8fd1-2c619a334d02')]).parameter_table
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


    # Crushing Value 

    temp_crushing_value = fields.Char(string="Temp.°C")
    humidity_crushing_value= fields.Char(string="Humidity %" )

    crushing_value_name = fields.Char("Name",default="Crushing Value")
    crushing_visible = fields.Boolean("Crushing Visible",compute="_compute_visible")

    
    wt_of_empty_cylinder = fields.Float(string="Weight of Empty Cylinder (W1) – gms.")
    wt_of_cylinder_aggregate = fields.Float(string="Weight of Cylinder + Aggregate (W2) – gms.")

    wt_of_aggregate_crush = fields.Float(string="Weight of Aggregate (A) = (W2 – W1) – gms",compute="_compute_wt_of_aggregate_crush")

    wt_of_aggregate_passing_sieve = fields.Float(string="Weight of Aggregate Passing Sieve (B) – gms.")

    aggregate_crushing_value = fields.Float(string="Aggregate Crushing Value in % = (B/A)x100",compute="_compute_aggregate_crushing_value",store=True)


    @api.depends('wt_of_empty_cylinder', 'wt_of_cylinder_aggregate')
    def _compute_wt_of_aggregate_crush(self):
        for rec in self:
            rec.wt_of_aggregate_crush = rec.wt_of_cylinder_aggregate - rec.wt_of_empty_cylinder

    @api.depends('wt_of_aggregate_passing_sieve', 'wt_of_aggregate_crush')
    def _compute_aggregate_crushing_value(self):
        for rec in self:
            if rec.wt_of_aggregate_crush != 0:
              rec.aggregate_crushing_value = (rec.wt_of_aggregate_passing_sieve / rec.wt_of_aggregate_crush) * 100
            else:
              rec.aggregate_crushing_value =0.0



    wt_of_empty_cylinder_2 = fields.Float(string="Weight of Empty Cylinder (W1) – gms.")
    wt_of_cylinder_aggregate_2 = fields.Float(string="Weight of Cylinder + Aggregate (W2) – gms.")

    wt_of_aggregate_crush_2 = fields.Float(string="Weight of Aggregate (A) = (W2 – W1) – gms",compute="_compute_wt_of_aggregate_crush_2")

    wt_of_aggregate_passing_sieve_2 = fields.Float(string="Weight of Aggregate Passing Sieve (B) – gms.")

    aggregate_crushing_value_2 = fields.Float(string="Aggregate Crushing Value in % = (B/A)x100",compute="_compute_aggregate_crushing_value_2",store=True)


    @api.depends('wt_of_empty_cylinder_2', 'wt_of_cylinder_aggregate_2')
    def _compute_wt_of_aggregate_crush_2(self):
        for rec in self:
            rec.wt_of_aggregate_crush_2 = rec.wt_of_cylinder_aggregate_2 - rec.wt_of_empty_cylinder_2

    @api.depends('wt_of_aggregate_crush_2', 'wt_of_aggregate_passing_sieve_2')
    def _compute_aggregate_crushing_value_2(self):
        for rec in self:
            if rec.wt_of_aggregate_crush_2 != 0:
              rec.aggregate_crushing_value_2 = (rec.wt_of_aggregate_passing_sieve_2 / rec.wt_of_aggregate_crush_2) * 100
            else:
               rec.aggregate_crushing_value_2 =0.0

    average_crushing_value = fields.Float(string="Average Aggregate Crushing Value", compute="_compute_average_crushing_value",digits=(10,2),store=True)

    # @api.depends('aggregate_crushing_value', 'aggregate_crushing_value_2')
    # def _compute_average_crushing_value(self):
    #     for rec in self:
    #           rec.average_crushing_value = round((rec.aggregate_crushing_value + rec.aggregate_crushing_value_2) /2,2)

    

    @api.depends('aggregate_crushing_value', 'aggregate_crushing_value_2')
    def _compute_average_crushing_value(self):
     for rec in self:
        avg = (rec.aggregate_crushing_value + rec.aggregate_crushing_value_2) / 2
        rec.average_crushing_value = float_round(avg, precision_digits=2)

    



    average_crushing_value_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),], string="Conformity", compute="_compute_average_crushing_value_conformity", store=True)

    @api.depends('average_crushing_value','eln_ref','grade')
    def _compute_average_crushing_value_conformity(self):
        
        for record in self:
            
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_crushing_value_conformity = 'na'
                continue
            record.average_crushing_value_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2547832k-3bf8-4ae5-8e5d-dfe983111f71')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2547832k-3bf8-4ae5-8e5d-dfe983111f71')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_crushing_value - record.average_crushing_value*mu_value
                    upper = record.average_crushing_value + record.average_crushing_value*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_crushing_value_conformity = 'pass'
                        break
                    else:
                        record.average_crushing_value_conformity = 'fail'

    average_crushing_value_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_crushing_value_nabl", store=True)

    @api.depends('average_crushing_value','eln_ref','grade')
    def _compute_average_crushing_value_nabl(self):
        
        for record in self:
            record.average_crushing_value_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2547832k-3bf8-4ae5-8e5d-dfe983111f71')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2547832k-3bf8-4ae5-8e5d-dfe983111f71')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_crushing_value - record.average_crushing_value*mu_value
                    upper = record.average_crushing_value + record.average_crushing_value*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_crushing_value_nabl = 'pass'
                        break
                    else:
                        record.average_crushing_value_nabl = 'fail'

             
                

    # Dry Gradation
    dry_gradation_name = fields.Char(default="Dry Gradation")
    dry_gradation_visible = fields.Boolean(compute="_compute_visible")

    dry_gradation_table = fields.One2many('mech.gsb.dry.gradation.line','parent_id',string="Dry Gradation")
    total_sieve_analysis = fields.Float(string="Total",compute="_compute_total_sieve")
    


    def calculate_sieve(self): 
        for record in self:
            for line in record.dry_gradation_table:
                print("Rows",str(line.percent_retained))
                previous_line = line.serial_no - 1
                if previous_line == 0:
                    if line.percent_retained == 0:
                        # print("Percent retained 0",line.percent_retained)
                        line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2)})
                        line.write({'passing_percent': 100 })
                    else:
                        # print("Percent retained else",line.percent_retained)
                        line.write({'cumulative_retained': round(line.percent_retained + line.percent_retained,2)})
                        line.write({'passing_percent': round(100 -line.percent_retained - line.percent_retained,2)})
                else:
                    previous_line_record = self.env['mech.gsb.dry.gradation.line'].sudo().search([("serial_no", "=", previous_line),("parent_id","=",self.id)]).cumulative_retained
                    line.write({'cumulative_retained': round(previous_line_record + line.percent_retained,2)})
                    line.write({'passing_percent': round(100-(previous_line_record + line.percent_retained),2)})
                    print("Previous Cumulative",previous_line_record)
                    

    


    # @api.depends('dry_gradation_table.wt_retained')
    # def _compute_total_sieve(self):
    #     for record in self:
    #         print("recordd",record)
    #         record.total_sieve_analysis = sum(record.dry_gradation_table.mapped('wt_retained'))
                    
    # @api.depends('dry_gradation_table.wt_retained')
    # def _compute_total_sieve(self):
    #     for record in self:
    #         total = sum(record.dry_gradation_table.mapped('wt_retained'))
    #         record.total_sieve_analysis = Decimal(str(total))
    @api.depends('dry_gradation_table.wt_retained')
    def _compute_total_sieve(self):
        for record in self:
            total = sum(record.dry_gradation_table.mapped('wt_retained'))
            record.total_sieve_analysis = round(total)


   

    def default_get(self, fields):
        print("From Default Value")
        res = super(GsbMechanical, self).default_get(fields)

        default_dry_sieve_sizes = []
        default_elongated_sieve_sizes = []
        dry_sieve_sizes = ['75.0 mm','53.0 mm','26.5 mm', '9.50 mm', '4.75 mm','2.36 mm','425 mic','75 mic']
        elongation_sieve_sizes = ['63 mm', '50 mm', '40 mm', '31.5 mm', '25 mm','20 mm','16 mm','12.5 mm','10 mm','6.3 mm']


        for i in range(8):  # You can change the number of default lines as needed
            size = {
                'sieve_size': dry_sieve_sizes[i] # Set the default product
                # Set the default quantity
            }
            default_dry_sieve_sizes.append((0, 0, size))
        res['dry_gradation_table'] = default_dry_sieve_sizes
        for i in range(10):  # You can change the number of default lines as needed
            size = {
                'sieve_size': elongation_sieve_sizes[i] # Set the default product
                # Set the default quantity
            }
            default_elongated_sieve_sizes.append((0, 0, size))
        res['dry_gradation_table'] = default_dry_sieve_sizes
        res['elongation_table'] = default_elongated_sieve_sizes

        return res

    # Water Absorbtion 
    water_absorbtion_name = fields.Char(default="Water Absorbtion")
    water_absorbtion_visible = fields.Boolean(compute="_compute_visible")

    wt_ssd_sample = fields.Integer('Weight of saturated surface dry (SSD) sample in air in gms, A')
    oven_dried_wt = fields.Float('Oven dried weight of sample in gms, C')
    water_absorbtion = fields.Float('Water absorption  %',compute="_compute_water_absorbtion")

    @api.depends('wt_ssd_sample','oven_dried_wt')
    def _compute_water_absorbtion(self):
        for record in self:
            if record.oven_dried_wt != 0:
                record.water_absorbtion = round((record.wt_ssd_sample - record.oven_dried_wt)/record.oven_dried_wt * 100,2)
            else:
                record.water_absorbtion = 0

    water_absorbtion_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_water_absorbtion_conformity", store=True)



    @api.depends('water_absorbtion','eln_ref','grade')
    def _compute_water_absorbtion_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.water_absorbtion_conformity = 'na'
                continue

            record.water_absorbtion_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','216587ghtr-4e73-44ca-93ed-442f74cd1e9b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','216587ghtr-4e73-44ca-93ed-442f74cd1e9b')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.water_absorbtion - record.water_absorbtion*mu_value
                    upper = record.water_absorbtion + record.water_absorbtion*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.water_absorbtion_conformity = 'pass'
                        break
                    else:
                        record.water_absorbtion_conformity = 'fail'

    water_absorbtion_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_water_absorbtion_nabl", store=True)

    @api.depends('water_absorbtion','eln_ref','grade')
    def _compute_water_absorbtion_nabl(self):
        
        for record in self:
            record.water_absorbtion_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','216587ghtr-4e73-44ca-93ed-442f74cd1e9b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','216587ghtr-4e73-44ca-93ed-442f74cd1e9b')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.water_absorbtion - record.water_absorbtion*mu_value
                    upper = record.water_absorbtion + record.water_absorbtion*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.water_absorbtion_nabl = 'pass'
                        break
                    else:
                        record.water_absorbtion_nabl = 'fail'


    # Flakiness and Elongation 
    elongation_name = fields.Char(default="Elongation and Flakiness Index")
    elongation_visible = fields.Boolean(compute="_compute_visible")

    flakiness_name = fields.Char(default=" Flakiness Index")
    flakiness_visible = fields.Boolean(compute="_compute_visible")

    elongation_table = fields.One2many('mech.gsb.elongation.flakiness.line','parent_id',string="Elongation Flakiness Index")

    total_wt_retained_fl_el = fields.Float('Total',compute="_compute_total_el_fl")
    total_elongated_retained = fields.Float('Total Elongation',compute="_compute_total_elongation")
    total_flakiness_retained = fields.Float('Total Flakiness',compute="_compute_total_flakiness")

    aggregate_elongation = fields.Float('Aggregate Elongation Value in %',compute="_compute_aggregate_elongation")
    aggregate_flakiness = fields.Float('Aggregate Flakiness Value in %' ,compute="_compute_aggregate_flakiness")
    aggregate_combine = fields.Float('Aggregate Elongation & Flakiness Value in %',compute="_compute_aggregate_combine")


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
                record.aggregate_flakiness = record.total_flakiness_retained/record.total_wt_retained_fl_el * 100
            else:
                record.aggregate_flakiness = 0

    @api.depends('total_wt_retained_fl_el','total_flakiness_retained')
    def _compute_aggregate_combine(self):
        for record in self:
            record.aggregate_combine = record.aggregate_elongation+record.aggregate_flakiness

    aggregate_flakiness_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_aggregate_flakiness_conformity", store=True)




    @api.depends('aggregate_flakiness','eln_ref','grade')
    def _compute_aggregate_flakiness_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.aggregate_flakiness_conformity = 'na'
                continue

            record.aggregate_flakiness_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','56482hgt1-70fb-4c47-baec-9880be12d765')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','56482hgt1-70fb-4c47-baec-9880be12d765')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.aggregate_flakiness - record.aggregate_flakiness*mu_value
                    upper = record.aggregate_flakiness + record.aggregate_flakiness*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.aggregate_flakiness_conformity = 'pass'
                        break
                    else:
                        record.aggregate_flakiness_conformity = 'fail'

    aggregate_flakiness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_aggregate_flakiness_nabl", store=True)

    @api.depends('aggregate_flakiness','eln_ref','grade')
    def _compute_aggregate_flakiness_nabl(self):
        
        for record in self:
            record.aggregate_flakiness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','56482hgt1-70fb-4c47-baec-9880be12d765')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','56482hgt1-70fb-4c47-baec-9880be12d765')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.aggregate_flakiness - record.aggregate_flakiness*mu_value
                    upper = record.aggregate_flakiness + record.aggregate_flakiness*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.aggregate_flakiness_nabl = 'pass'
                        break
                    else:
                        record.aggregate_flakiness_nabl = 'fail'



    aggregate_elongation_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_aggregate_elongation_conformity", store=True)



    @api.depends('aggregate_elongation','eln_ref','grade')
    def _compute_aggregate_elongation_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.aggregate_elongation_conformity = 'na'
                continue

            record.aggregate_elongation_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32147hgv4-599e-4569-8cd2-48e1dc120714')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32147hgv4-599e-4569-8cd2-48e1dc120714')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.aggregate_elongation - record.aggregate_elongation*mu_value
                    upper = record.aggregate_elongation + record.aggregate_elongation*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.aggregate_elongation_conformity = 'pass'
                        break
                    else:
                        record.aggregate_elongation_conformity = 'fail'

    aggregate_elongation_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_aggregate_elongation_nabl", store=True)

    @api.depends('aggregate_elongation','eln_ref','grade')
    def _compute_aggregate_elongation_nabl(self):
        
        for record in self:
            record.aggregate_elongation_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32147hgv4-599e-4569-8cd2-48e1dc120714')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32147hgv4-599e-4569-8cd2-48e1dc120714')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.aggregate_elongation - record.aggregate_elongation*mu_value
                    upper = record.aggregate_elongation + record.aggregate_elongation*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.aggregate_elongation_nabl = 'pass'
                        break
                    else:
                        record.aggregate_elongation_nabl = 'fail'
            



    # Abrasion Value
    abrasion_value_name = fields.Char("Name",default="Abrasion Value")
    abrasion_visible = fields.Boolean("Abrasion Visible",compute="_compute_visible")

    total_weight_sample_abrasion = fields.Integer(string="Total weight of Sample in gms")
    weight_passing_sample_abrasion = fields.Integer(string="Weight of Passing sample in 1.70 mm IS sieve in gms")
    weight_retain_sample_abrasion = fields.Integer(string="Weight of Retain sample in 1.70 mm IS sieve in gms",compute="_compute_weight_retain_sample_abrasion")
    abrasion_value_percentage = fields.Float(string="Abrasion Value (%)",compute="_compute_sample_weight")


    @api.depends('total_weight_sample_abrasion', 'weight_passing_sample_abrasion')
    def _compute_weight_retain_sample_abrasion(self):
        for line in self:
            line.weight_retain_sample_abrasion = line.total_weight_sample_abrasion - line.weight_passing_sample_abrasion


    @api.depends('total_weight_sample_abrasion', 'weight_passing_sample_abrasion')
    def _compute_sample_weight(self):
        for line in self:
            if line.total_weight_sample_abrasion != 0:
                line.abrasion_value_percentage = round((line.weight_passing_sample_abrasion / line.total_weight_sample_abrasion) * 100,2)
            else:
                line.abrasion_value_percentage = 0.0

    abrasion_value_percentage_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_abrasion_value_percentage_conformity", store=True)



    @api.depends('abrasion_value_percentage','eln_ref','grade')
    def _compute_abrasion_value_percentage_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.abrasion_value_percentage_conformity = 'na'
                continue

            record.abrasion_value_percentage_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2145hgt1-3f1c-4aca-ac94-3c2bb0f034e2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2145hgt1-3f1c-4aca-ac94-3c2bb0f034e2')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2145hgt1-3f1c-4aca-ac94-3c2bb0f034e2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2145hgt1-3f1c-4aca-ac94-3c2bb0f034e2')]).parameter_table
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

    # Impact Value 
    impact_value_name = fields.Char("Name",default="Impact Value")
    impact_visible = fields.Boolean("Impact Visible",compute="_compute_visible")

    impact_value_child_lines = fields.One2many('mech.gsb.impact.line','parent_id',string="Parameter")

    average_impact_value = fields.Float(string="Average Impact Value", compute="_compute_average_impact_value")

    

    @api.depends('impact_value_child_lines.impact_value')
    def _compute_average_impact_value(self):
        for record in self:
            if record.impact_value_child_lines:
                sum_impact_value = sum(record.impact_value_child_lines.mapped('impact_value'))
                record.average_impact_value = round((sum_impact_value / len(record.impact_value_child_lines)),1)
            else:
                record.average_impact_value = 0.0

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457gtr4-a55f-47ac-aee6-9f37d733ccca')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457gtr4-a55f-47ac-aee6-9f37d733ccca')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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

    average_impact_value_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_impact_value_nabl", store=True)

    @api.depends('average_impact_value','eln_ref','grade')
    def _compute_average_impact_value_nabl(self):
        
        for record in self:
            record.average_impact_value_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457gtr4-a55f-47ac-aee6-9f37d733ccca')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457gtr4-a55f-47ac-aee6-9f37d733ccca')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_impact_value - record.average_impact_value*mu_value
                    upper = record.average_impact_value + record.average_impact_value*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_impact_value_nabl = 'pass'
                        break
                    else:
                        record.average_impact_value_nabl = 'fail'

    # Liquid Limit
    liquid_limit_name = fields.Char("Name",default="Liquid Limit")
    liquid_limit_visible = fields.Boolean("Liquid Limit Visible",compute="_compute_visible")

    liquid_limit_table = fields.One2many('mech.gsb.liquid.limit.line','parent_id',string="Liquid Limit")
    liquid_limit = fields.Float("Liquid Limit",digits=(12,2))
    remarks_liquid_limit = fields.Selection([
        ('plastic', 'Plastic'),
        ('non-plastic', 'Non-Plastic')],"Remarks",store=True)
    
    liquid_limit_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_liquid_limit_conformity", store=True)
    


      # def calculate_result(self):
    are_child_lines_filled = fields.Boolean(compute='_compute_are_child_lines_filled',string='child lines',store=False)

    @api.depends('liquid_limit_table.moisture_percent', 'liquid_limit_table.mass_dry_sample')  # Replace with actual field names
    def _compute_are_child_lines_filled(self):
        for record in self:
            all_lines_filled = all(line.moisture_percent and line.mass_dry_sample for line in record.liquid_limit_table)
            record.are_child_lines_filled = all_lines_filled

    

    def liquid_calculation(self):
        print('<<<<<<<<<<<<')
        for record in self:
            # import wdb;wdb.set_trace()
            data = self.liquid_limit_table
            
            result = 0  # Initialize result before the loop
            container=[]
            blows = []
            for i in data:
                container.append(i.moisture_percent)
                blows.append(i.blows)

                # print(container)
                # results=(container[1]*100-((container[2]-container[3])*100*(25-blows[1]))/(blows[2]-blows[1]))/100
                # print (results,'final result')
                print('Moisture:', container)
                print('Blows:', blows)

            if len(container) == 1:
              # Only one point, no interpolation possible
              result = container[0]
              print('Only one data point, result:', result)
            elif len(container) >= 3 and len(blows) >= 3:
              # Use your interpolation formula (adjust indexes as needed)
              result = (container[1]*100 - ((container[1] - container[2]) * 100 * (25 - blows[1])) / (blows[2] - blows[1])) / 100
              print('Interpolated result:', result)
            else:
              print('Not enough data points to calculate result')
              result = 0  # or handle differently

        record.write({'liquid_limit': result})
                
                

            # print(data, 'data')

            # container2Moisture = data[1].moisture_percent
            # container1Moisture = data[0].moisture_percent
            # container3Moisture = data[2].moisture_percent
            # cont2blow = data[1].blows
            # cont3blow = data[2].blows
            # result = (container2Moisture * 100 - ((container2Moisture - container3Moisture) * 100 * (25 - cont2blow)) / (cont3blow - cont2blow)) / 100
            # print(result, 'final result')
        # self.write({'liquid_limit': results})





    @api.depends('liquid_limit','eln_ref','grade')
    def _compute_liquid_limit_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.liquid_limit_conformity = 'na'
                continue

            record.liquid_limit_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12547ftd4-3ed1-4021-90a2-47651f0ed81d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12547ftd4-3ed1-4021-90a2-47651f0ed81d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.liquid_limit - record.liquid_limit*mu_value
                    upper = record.liquid_limit + record.liquid_limit*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.liquid_limit_conformity = 'pass'
                        break
                    else:
                        record.liquid_limit_conformity = 'fail'

    liquid_limit_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_liquid_limit_value_nabl", store=True)

    @api.depends('liquid_limit','eln_ref','grade')
    def _compute_liquid_limit_value_nabl(self):
        
        for record in self:
            record.liquid_limit_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12547ftd4-3ed1-4021-90a2-47651f0ed81d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12547ftd4-3ed1-4021-90a2-47651f0ed81d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.liquid_limit - record.liquid_limit*mu_value
                    upper = record.liquid_limit + record.liquid_limit*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.liquid_limit_nabl = 'pass'
                        break
                    else:
                        record.liquid_limit_nabl = 'fail'


    # Plastic Limit
    plastic_name = fields.Char("Name",default="Plastic Limit")
    plastic_visible = fields.Boolean("Plastic Limit Visible",compute="_compute_visible")

    plastic_table = fields.One2many('mech.gsb.plastic.limit.line','parent_id',string="Plastic Limit")
    average_plastic_moisture = fields.Float("Average",compute="_compute_plastic_average")
    remarks_plastic = fields.Selection([
        ('plastic', 'Plastic'),
        ('non-plastic', 'Non-Plastic')],"Remarks",store=True)

   

    
    @api.depends('plastic_table.moisture_percent')
    def _compute_plastic_average(self):
        for record in self:
            if record.plastic_table:
                sum_moisture_percent = sum(record.plastic_table.mapped('moisture_percent'))
                record.average_plastic_moisture = round((sum_moisture_percent / len(record.plastic_table)),2)
            else:
                record.average_plastic_moisture = 0.0

    average_plastic_moisture_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_average_plastic_moisture_conformity", store=True)



    @api.depends('average_plastic_moisture','eln_ref','grade')
    def _compute_average_plastic_moisture_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_plastic_moisture_conformity = 'na'
                continue

            record.average_plastic_moisture_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14527gthy-f86e-4a5f-bd15-a5b0c173b5ed')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14527gthy-f86e-4a5f-bd15-a5b0c173b5ed')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_plastic_moisture - record.average_plastic_moisture*mu_value
                    upper = record.average_plastic_moisture + record.average_plastic_moisture*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_plastic_moisture_conformity = 'pass'
                        break
                    else:
                        record.average_plastic_moisture_conformity = 'fail'

    average_plastic_moisture_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_plastic_moisture_nabl", store=True)

    @api.depends('average_plastic_moisture','eln_ref','grade')
    def _compute_average_plastic_moisture_nabl(self):
        
        for record in self:
            record.average_plastic_moisture_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14527gthy-f86e-4a5f-bd15-a5b0c173b5ed')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','14527gthy-f86e-4a5f-bd15-a5b0c173b5ed')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_plastic_moisture - record.average_plastic_moisture*mu_value
                    upper = record.average_plastic_moisture + record.average_plastic_moisture*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_plastic_moisture_nabl = 'pass'
                        break
                    else:
                        record.average_plastic_moisture_nabl = 'fail'

    # Plasticity Index
    plasticity_index_visible = fields.Boolean("Plasticity Index Visible",compute="_compute_visible")
    plasticity_index = fields.Float("Plasticity Index",compute="_compute_plasticity_limit")
    remarks_plasticity_index = fields.Selection([
        ('plastic', 'Plastic'),
        ('non-plastic', 'Non-Plastic')],"Remarks",store=True)

    @api.depends('average_plastic_moisture','liquid_limit')
    def _compute_plasticity_limit(self):
        for record in self:
            record.plasticity_index = record.liquid_limit - record.average_plastic_moisture

    plasticity_index_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_plasticity_index_conformity", store=True)




    @api.depends('plasticity_index','eln_ref','grade')
    def _compute_plasticity_index_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.plasticity_index_conformity = 'na'
                continue

            record.plasticity_index_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24584fgrt-1611-4790-9410-ef5db6233932')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24584fgrt-1611-4790-9410-ef5db6233932')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.plasticity_index - record.plasticity_index*mu_value
                    upper = record.plasticity_index + record.plasticity_index*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.plasticity_index_conformity = 'pass'
                        break
                    else:
                        record.plasticity_index_conformity = 'fail'

    plasticity_index_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_plasticity_index_nabl", store=True)

    @api.depends('plasticity_index','eln_ref','grade')
    def _compute_plasticity_index_nabl(self):
        
        for record in self:
            record.plasticity_index_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24584fgrt-1611-4790-9410-ef5db6233932')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24584fgrt-1611-4790-9410-ef5db6233932')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.plasticity_index - record.plasticity_index*mu_value
                    upper = record.plasticity_index + record.plasticity_index*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.plasticity_index_nabl = 'pass'
                        break
                    else:
                        record.plasticity_index_nabl = 'fail'

    # Density Relation Heavy Compaction
    density_relation_name = fields.Char("Name",default="Density Relation Using Heavy Compaction")
    density_relation_visible = fields.Boolean("Density Relation Visible",compute="_compute_visible")

    density_relation_table = fields.One2many('mech.gsb.density.relation.line','parent_id',string="Density Relation")
    wt_of_modul = fields.Float('Weight of Mould in gm')
    vl_of_modul = fields.Float('Volume of Mould in cc')
    chart_image_density = fields.Binary("Line Chart", compute="_compute_chart_image_density", store=True)

    mmd = fields.Float(string="MMD gm/cc", compute="_compute_max_dry_density_heavy", store=True)
    omc = fields.Float(string="OMC %", compute="_compute_max_omc_heavy", store=True)

    @api.depends('density_relation_table.dry_density')
    def _compute_max_dry_density_heavy(self):
        for record in self:
            max_dry_density_heavy = max(record.density_relation_table.mapped('dry_density'), default=0.0)
            record.mmd = max_dry_density_heavy

    @api.depends('density_relation_table.dry_density', 'density_relation_table.moisture', 'mmd')
    def _compute_max_omc_heavy(self):
        for record in self:
            max_dry_density_light_omc = record.mmd
            corresponding_moisture_heavy = next((line.moisture for line in record.density_relation_table if line.dry_density == max_dry_density_light_omc), 0.0)
            record.omc = corresponding_moisture_heavy



    def generate_line_chart_density(self):
        # Prepare data for the chart
        x_values = []
        y_values = []
        for line in self.density_relation_table:
            x_values.append(line.moisture)
            y_values.append(line.dry_density)
        
        # Create the line chart
        plt.plot(x_values, y_values, marker='o')
        plt.xlabel('% Moisture')
        plt.ylabel('Dry Density')
        plt.title('Density Relation Using Heavy Compaction')


        plt.ylim(bottom=0, top=max(y_values) + 10)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()  # Close the figure to free up resources
        buffer.seek(0)
    
        # Convert the chart image to base64
        chart_image = base64.b64encode(buffer.read()).decode('utf-8')  
        return chart_image
    
    @api.depends('density_relation_table')
    def _compute_chart_image_density(self):
        try:
            for record in self:
                chart_image = record.generate_line_chart_density()
                record.chart_image_density = chart_image
        except:
            pass 



    # CBR
    cbr_name = fields.Char("Name",default="CBR")
    cbr_visible = fields.Boolean("CBR Visible",compute="_compute_visible")

    cbr_table = fields.One2many('mechanical.gsb.cbr.line','parent_id',string="CBR")
    chart_image_cbr = fields.Binary("Line Chart", compute="_compute_chart_image_cbr", store=True)


    def generate_line_chart_cbr(self):
        # Prepare data for the chart
        x_values = []
        y_values = []
        for line in self.cbr_table:
            x_values.append(line.penetration)
            y_values.append(line.load)
        
        # Create the line chart
        plt.plot(x_values, y_values, marker='o')
        plt.xlabel('Penetration')
        plt.ylabel('Load')
        plt.title('CBR')


        plt.ylim(bottom=0, top=max(y_values) + 10)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()  # Close the figure to free up resources
        buffer.seek(0)
    
        # Convert the chart image to base64
        chart_image = base64.b64encode(buffer.read()).decode('utf-8')  
        return chart_image
    
    @api.depends('cbr_table')
    def _compute_chart_image_cbr(self):
        try:
            for record in self:
                chart_image = record.generate_line_chart_cbr()
                record.chart_image_cbr = chart_image
        except:
            pass 



class GsbDensityRelationLine(models.Model):
    _name = "mech.gsb.density.relation.line"
    parent_id = fields.Many2one('mechanical.gsb',string="Parent Id")

    determination_no = fields.Float(string="Determination No")
    wt_of_modul_compact = fields.Integer(string="Weight of Mould + Compacted sample in gm")
    wt_of_compact = fields.Integer(string="Weight of compacted sample in gm", compute="_compute_wt_of_compact")
    bulk_density = fields.Float(string="Bulk Density of sample in gm/cc", compute="_compute_bulk_density")
    container_no = fields.Integer(string="Container No")
    wt_of_container = fields.Float(string="Weight of Container in gm")
    wt_of_container_wet = fields.Float(string="Weight of Container + wet sample in gm")
    wt_of_container_dry = fields.Float(string="Weight of Container + dry sample in gm")
    wt_of_dry_sample = fields.Float(string="Weight of dry sample in gm", compute="_compute_wt_of_dry_sample")
    wt_of_moisture = fields.Float(string="Weight of moisture in gm", compute="_compute_wt_of_moisture")
    moisture = fields.Float(string="% Moisture", compute="_compute_moisture")
    dry_density = fields.Float(string="Dry density in gm/cc", compute="_compute_dry_density")


    @api.depends('wt_of_modul_compact', 'parent_id.wt_of_modul')
    def _compute_wt_of_compact(self):
        for line in self:
            line.wt_of_compact = round(line.wt_of_modul_compact - line.parent_id.wt_of_modul,2)



    @api.depends('wt_of_compact', 'parent_id.vl_of_modul')
    def _compute_bulk_density(self):
        for line in self:
            if line.parent_id.vl_of_modul != 0:
                line.bulk_density = round(line.wt_of_compact / line.parent_id.vl_of_modul,2)
            else:
                line.bulk_density = 0.0



    @api.depends('wt_of_container_dry', 'wt_of_container')
    def _compute_wt_of_dry_sample(self):
        for line in self:
            line.wt_of_dry_sample = round(line.wt_of_container_dry - line.wt_of_container,2)


    @api.depends('wt_of_container_wet','wt_of_container_dry')
    def _compute_wt_of_moisture(self):
        for record in self:
            record.wt_of_moisture = round((record.wt_of_container_wet - record.wt_of_container_dry),2)


    @api.depends('wt_of_moisture', 'wt_of_dry_sample')
    def _compute_moisture(self):
        for line in self:
            if line.wt_of_dry_sample != 0:
                line.moisture = round(line.wt_of_moisture / line.wt_of_dry_sample * 100,2)
            else:
                line.moisture = 0.0


    @api.depends('bulk_density', 'moisture')
    def _compute_dry_density(self):
        for line in self:
            line.dry_density = round((100 * line.bulk_density) / (100 + line.moisture),2)


 



class GsbCBRLine(models.Model):
    _name = "mechanical.gsb.cbr.line"
    parent_id = fields.Many2one('mechanical.gsb',string="Parent Id")

    penetration = fields.Float(string="Penetration in mm")
    proving_reading = fields.Float(string="Proving Ring Reading")
    load = fields.Float(string="Load in Kg", compute="_compute_load")


    @api.depends('proving_reading')
    def _compute_load(self):
        for record in self:
            record.load = record.proving_reading * 6.96



class GsbLiquidLimitLine(models.Model):
    _name = "mech.gsb.liquid.limit.line"
    parent_id = fields.Many2one('mechanical.gsb', string="Parent Id")
    
    container_no = fields.Char("Container No.")
    blows = fields.Integer(string="No of Blows")
    mass_wet_sample_container = fields.Float(string="Mass of wet sample+container, (M1) in gms")
    mass_dry_sample_container = fields.Float(string="Mass of dry sample+container, (M2) in gms")
    mass_container = fields.Float(string="Mass of container, (M3) in gms")
    mass_moisture = fields.Float(string="Mass of Moisture, (M1-M2) in gms",compute="_compute_mass_moisture")
    mass_dry_sample = fields.Float(string="Mass of dry sample, (M2-M3) in gms",compute="_compute_mass_dry_sample")
    moisture_percent = fields.Float(string="% Moisture",compute="_compute_moisture_percent")


    @api.depends('mass_dry_sample_container','mass_wet_sample_container')
    def _compute_mass_moisture(self):
        for record in self:
            record.mass_moisture = record.mass_wet_sample_container - record.mass_dry_sample_container


    @api.depends('mass_dry_sample_container','mass_container')
    def _compute_mass_dry_sample(self):
        for record in self:
            record.mass_dry_sample = record.mass_dry_sample_container - record.mass_container

    @api.depends('mass_moisture','mass_dry_sample')
    def _compute_moisture_percent(self):
        for record in self:
            if record.mass_dry_sample != 0:
                record.moisture_percent = round((record.mass_moisture /record.mass_dry_sample) *100,2)
            else:
                record.moisture_percent = 0



class GsbPlasticLimitLine(models.Model):
    _name = "mech.gsb.plastic.limit.line"
    parent_id = fields.Many2one('mechanical.gsb', string="Parent Id")
    
    container_no = fields.Char("Container No.")
    mass_wet_sample_container = fields.Float(string="Mass of wet sample+container, (M1) in gms")
    mass_dry_sample_container = fields.Float(string="Mass of dry sample+container, (M2) in gms")
    mass_container = fields.Float(string="Mass of container, (M3) in gms")
    mass_moisture = fields.Float(string="Mass of Moisture, (M1-M2) in gms",compute="_compute_mass_moisture")
    mass_dry_sample = fields.Float(string="Mass of dry sample, (M2-M3) in gms",compute="_compute_mass_dry_sample")
    moisture_percent = fields.Float(string="% Moisture",compute="_compute_moisture_percent")


    @api.depends('mass_dry_sample_container','mass_wet_sample_container')
    def _compute_mass_moisture(self):
        for record in self:
            record.mass_moisture = record.mass_wet_sample_container - record.mass_dry_sample_container


    @api.depends('mass_dry_sample_container','mass_container')
    def _compute_mass_dry_sample(self):
        for record in self:
            record.mass_dry_sample = record.mass_dry_sample_container - record.mass_container

    @api.depends('mass_moisture','mass_dry_sample')
    def _compute_moisture_percent(self):
        for record in self:
            if record.mass_dry_sample != 0:
                record.moisture_percent = round((record.mass_moisture /record.mass_dry_sample) *100,2)
            else:
                record.moisture_percent = 0


class GsbDryGradationLine(models.Model):
    _name = "mech.gsb.dry.gradation.line"
    parent_id = fields.Many2one('mechanical.gsb', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size" )
    wt_retained = fields.Float(string="Wt. Retained in gms")
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained")
    cumulative_retained = fields.Float(string="Cum. Retained %", store=True)
    passing_percent = fields.Float(string="Passing %")



    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(GsbDryGradationLine, self).create(vals)

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
                    record.percent_retained = round((vals['wt_retained'] / record.parent_id.total * 100),2) if record.parent_id.total else 0

            new_self = super(GsbDryGradationLine, self).write(vals)

            if 'wt_retained' in vals:
                for record in self:
                    record.parent_id._compute_total_sieve()

            return new_self

        return super(GsbDryGradationLine, self).write(vals)

    def unlink(self):
        # Get the parent_id before the deletion
        parent_id = self[0].parent_id

        res = super(GsbDryGradationLine, self).unlink()

        # if parent_id:
        #     parent_id.sieve_analysis_child_lines._reorder_serial_numbers()

        return res


    @api.depends('wt_retained', 'parent_id.total_sieve_analysis')
    def _compute_percent_retained(self):
        for record in self:
            try:
                record.percent_retained = record.wt_retained / self.parent_id.total_sieve_analysis * 100
            except ZeroDivisionError:
                record.percent_retained = 0


class GsbElongationLine(models.Model):
    _name = "mech.gsb.elongation.flakiness.line"
    parent_id = fields.Many2one('mechanical.gsb', string="Parent Id")

    sieve_size = fields.Char(string="IS Sieve Size")
    wt_retained = fields.Float(string="Wt. Retained in gms")
    elongated_retained = fields.Float(string="Elongated Retained in gms")
    flakiness_retained = fields.Float(string="Flakiness Retained in gms")



# class FlakinessLine(models.Model):
#     _name = "mech.flakiness.line"
#     parent_id = fields.Many2one('mechanical.gsb', string="Parent Id")

#     sieve_size = fields.Char(string="IS Sieve Size")
#     wt_retained = fields.Float(string="Wt. Retained in gms")
#     flakiness_retained = fields.Float(string="Flakiness Retained in gms")


class GsbImpactValueLine(models.Model):
    _name = "mech.gsb.impact.line"
    parent_id = fields.Many2one('mechanical.gsb',string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)
    wt_of_cylinder = fields.Integer(string="Weight of cylindrical measure in gms")
    total_wt_of_dried = fields.Integer(string="Total Wt. of Oven dried (4 hrs) aggregate sample + cylindrical measure in gms")
    total_wt_aggregate = fields.Float(string="Total Wt. of Oven dried (4 hrs) aggregate sample filling the cylindrical measure in gms", compute="_compute_total_wt_aggregate")
    wt_of_aggregate_passing = fields.Float(string="Wt. of aggregate passing 2.36 mm sieve after the test in gms")
    wt_of_aggregate_retained = fields.Float(string="Wt. of aggregate retained on 2.36 mm sieve after the test in gms", compute="_compute_wt_of_aggregate_retained")
    impact_value = fields.Float(string="Impact value", compute="_compute_impact_value")


    @api.depends('total_wt_of_dried', 'wt_of_cylinder')
    def _compute_total_wt_aggregate(self):
        for rec in self:
            rec.total_wt_aggregate = rec.total_wt_of_dried - rec.wt_of_cylinder


    @api.depends('total_wt_aggregate', 'wt_of_aggregate_passing')
    def _compute_wt_of_aggregate_retained(self):
        for rec in self:
            rec.wt_of_aggregate_retained = rec.total_wt_aggregate - rec.wt_of_aggregate_passing


    @api.depends('wt_of_aggregate_passing', 'total_wt_aggregate')
    def _compute_impact_value(self):
        for rec in self:
            if rec.total_wt_aggregate != 0:
                rec.impact_value = (rec.wt_of_aggregate_passing / rec.total_wt_aggregate) * 100
            else:
                rec.impact_value = 0.0


class SoudnessLine(models.Model):
    _name = "gsb.soudness.line"
    parent_id = fields.Many2one('mechanical.gsb',string="Parent Id")

    serial_no = fields.Integer(string="Cycle No", readonly=True, copy=False, default=1)

    immersed_datetime = fields.Datetime(string="Date & Time of Sample immersed in Solution for 16 to 18 hrs.")
    temp_solution = fields.Float(string="Temp. of Solution (°C)", digits=(6,2))
    specific_gravity_solution = fields.Float(string="Specific Gravity of Solution", digits=(8,3))
    removed_datetime = fields.Datetime(string="Date & Time of Sample Removed from Solution")
    oven_datetime = fields.Datetime(string="Date & Time of Sample Kept in Oven (105 to 1100C) for Drying ")

    hours_1 = fields.Char(string="Hours 1",compute="_compute_hours_1",store=True)
    hours_2 = fields.Char(string="Hours 2",compute="_compute_hours_2",store=True)
    hours_3 = fields.Char(string="Hours 3",compute="_compute_hours_3",store=True)

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
    _name = "mechanical.gsb.sieve.analysis.line"
    parent_id = fields.Many2one('mechanical.gsb', string="Parent Id")
    
    serial_no = fields.Integer(string="Sr. No", readonly=True, copy=False, default=1)
    sieve_size = fields.Char(string="IS Sieve Size")
    particle_size = fields.Char(string="Retained")
    wt_retained = fields.Float(string="Wt. Retained before test(gm)")
    percent_retained = fields.Float(string='% Retained', compute="_compute_percent_retained")
    wt_sample_testing = fields.Char(string="Weight of sample for testing (gm)",compute="_compute_wt_sample_testing_display")
    actual_wt = fields.Float(string="Actual Weight of sample taken (gm)")
    cumulative_retained = fields.Float(string="Cum. Retained %",compute="_compute_cum_retained" , store=True)
    passing_percent = fields.Float(string="% Passing ")

  

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
            # import wdb; wdb.set_trace()
            sorted_lines = sorted(record.parent_id.sieve_analysis_soundness_lines, key=lambda r: r.id)
            # index = sorted_lines.index(record)
            # print("Working")

class OuantitativelyExaminationLine(models.Model):
    _name = "gsb.ouantitative.line"
    parent_id = fields.Many2one('mechanical.gsb',string="Parent Id")

    serial_no = fields.Integer(string="Cycle No", readonly=True, copy=False, default=1)

    size = fields.Char(string="Size")
    cycle = fields.Float(string="Test Cycle ")
    original_sulphate = fields.Float(string="Original wt. of Sample-gms.Sodium Sulphate", digits=(8,3),compute="_compute_original_sulphate",store=True)
    original_magnesiu = fields.Float(string="Original wt. of Sample-gms.Magnesium ", digits=(8,3))
    wt_sulhate = fields.Float(string="Weight Retained After  5 Cycle-gms Sodium Sulphate")
    wt_manesium = fields.Float(string="Weight Retained After  5 Cycle-gms Magnesium ")
    loss_sulphae = fields.Float(string="% Loss Sodium Sulphate",compute="_compute_loss_sulphae",digits=(12,2))
    loss_manesium = fields.Float(string="% Loss Magnesium ")

    @api.depends('serial_no', 'parent_id.sieve_analysis_soundness_lines')
    def _compute_original_sulphate(self):
        for rec in self:
            if rec.parent_id:
                line = rec.parent_id.sieve_analysis_soundness_lines.filtered(
                    lambda l: l.serial_no == rec.serial_no
                )[:1]
                rec.original_sulphate = line.actual_wt if line else 0.0
            else:
                rec.original_sulphate = 0.0

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
    _name = "gsb.quantitative.line"
    parent_id = fields.Many2one('mechanical.gsb',string="Parent Id")

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

    @api.depends('finalloss_sulphae', 'grading_sulphate')
    def _compute_avg_sulphae(self):
        for rec in self:
            rec.avg_sulphae = (rec.finalloss_sulphae * rec.grading_sulphate) / 100 if rec.grading_sulphate else 0.0

   

    @api.depends('parent_id.sieve_analysis_soundness_lines', 'parent_id.ouantitative_soundness_lines')
    def _compute_finalloss_sulphae(self):
     for idx, rec in enumerate(self):
        sieve_lines = rec.parent_id.sieve_analysis_soundness_lines.sorted('serial_no')
        quant_lines = rec.parent_id.ouantitative_soundness_lines.sorted('serial_no')
        percent_ret = 0.0
        loss_sulphae_val = 0.0

        # Find the matching sieve and quantitative line
        sieve_line = next((l for l in sieve_lines if l.serial_no == rec.serial_no), None)
        if sieve_line:
            percent_ret = sieve_line.percent_retained

        quant_line = next((l for l in quant_lines if l.serial_no == rec.serial_no), None)
        if quant_line:
            loss_sulphae_val = quant_line.loss_sulphae

        # Boundary logic
        if idx == 0:  # First item
            next_loss_val = quant_lines[idx+1].loss_sulphae if len(quant_lines) > idx+1 else loss_sulphae_val
            avg_val = next_loss_val  # Use next value only
        elif idx == len(self)-1:  # Last item
            prev_loss_val = quant_lines[idx-1].loss_sulphae if idx > 0 else loss_sulphae_val
            avg_val = prev_loss_val  # Use previous value only
        else:  # Middle items
            prev_loss_val = quant_lines[idx-1].loss_sulphae
            next_loss_val = quant_lines[idx+1].loss_sulphae
            avg_val = (prev_loss_val + next_loss_val) / 2 if (prev_loss_val is not None and next_loss_val is not None) else loss_sulphae_val

        if 0 < percent_ret < 5:
            rec.finalloss_sulphae = avg_val
        else:
            rec.finalloss_sulphae = loss_sulphae_val

            

    @api.depends('serial_no', 'parent_id.sieve_analysis_soundness_lines')
    def _compute_grading_sulphate(self):
        for rec in self:
            if rec.parent_id:
                line = rec.parent_id.sieve_analysis_soundness_lines.filtered(
                    lambda l: l.serial_no == rec.serial_no
                )[:1] 
                rec.grading_sulphate = line.percent_retained if line else 0.0
            else:
                rec.grading_sulphate = 0.0

    @api.depends('serial_no', 'parent_id.ouantitative_soundness_lines')
    def _compute_wt_fraction_sulhate(self):
        for rec in self:
            if rec.parent_id:
                line = rec.parent_id.ouantitative_soundness_lines.filtered(
                    lambda l: l.serial_no == rec.serial_no
                )[:1]
                rec.wt_fraction_sulhate = line.wt_sulhate if line else 0.0
            else:
                rec.wt_fraction_sulhate = 0.0


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



class gsbNotes(models.Model):
    _name = "gsb.notes"

    parent_id = fields.Many2one('mechanical.gsb',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")


