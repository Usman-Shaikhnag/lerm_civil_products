from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class ChemicalDrinkingWater(models.Model):
    _name = "chemical.drinking.water"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Drinking Water")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    notes_id = fields.One2many('chem.drinking.water.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(ChemicalDrinkingWater, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The report shall not be reproduced in fullor partially without written approval of the laboratory HOD/CEO/Maganement.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'ampling is not done by us unless mentioned otherwide.',
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
                'notes': 'Alldisputed are subject to Raipur jurisdiction 7 days correction to this report invalidates this report.',
            }),

             (0, 0, {
                'sr_no': 'g',
                'notes': 'Sample willbe destroyed after 30-days from the date of test report unless otherwise Specified.',
            }),
        ]

        res['notes_id'] = default_notes
        return res


    ph_name = fields.Char("Name",default="pH of 1 % Solution in water")
    ph_visible = fields.Boolean("pH",compute="_compute_visible")
    
    ph_1_percent_a = fields.Float("pH of 1 % Solution in water")
    ph_1_percent_b = fields.Float("pH of 1 % Solution in water")
    ph_1_percent_c = fields.Float("pH of 1 % Solution in water")
    ph_1_percent_d = fields.Float("pH of 1 % Solution in water")
    ph_1_percent_e = fields.Float("pH of 1 % Solution in water")
    ph_average = fields.Float("Average",compute="_compute_ph_average")

    @api.depends("ph_1_percent_a",'ph_1_percent_b','ph_1_percent_c','ph_1_percent_d','ph_1_percent_e')
    def _compute_ph_average(self):
        for record in self:
            record.ph_average = (record.ph_1_percent_a + record.ph_1_percent_b + record.ph_1_percent_c + record.ph_1_percent_d + record.ph_1_percent_e)/5

    ph_average_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_ph_average_conformity", store=True)

    @api.depends('ph_average','eln_ref','grade')
    def _compute_ph_average_conformity(self):
            # remove this first when making changes
            self.ph_average_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.ph_average_conformity = 'na'
                    continue

                record.ph_average_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62tyubg0d-645d-4794-a0fd-3daa01247jht')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62tyubg0d-645d-4794-a0fd-3daa01247jht')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.ph_average - record.ph_average*mu_value
                        upper = record.ph_average + record.ph_average*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.ph_average_conformity = 'pass'
                            break
                        else:
                            record.ph_average_conformity = 'fail'

    ph_average_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_ph_average_nabl", store=True)

    @api.depends('ph_average','eln_ref','grade')
    def _compute_ph_average_nabl(self):
        # remove this first
        self.ph_average_nabl = 'fail'
        
        for record in self:
            record.ph_average_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62tyubg0d-645d-4794-a0fd-3daa01247jht')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62tyubg0d-645d-4794-a0fd-3daa01247jht')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.ph_average - record.ph_average*mu_value
            upper = record.ph_average + record.ph_average*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.ph_average_nabl = 'pass'
                break
            else:
                record.ph_average_nabl = 'fail'





    conductivity_name = fields.Char("Name",default="Conductivity")
    conductivity_visible = fields.Boolean("pH",compute="_compute_visible")
    
    conductivity_1 = fields.Float("Observation")
    conductivity_2 = fields.Float("Observation")
    conductivity_3 = fields.Float("Observation")
    conductivity_4 = fields.Float("Observation")
    conductivity_5 = fields.Float("Observation")
    conductivity_average = fields.Float("Average",compute="_compute_conductivity_average")

    @api.depends("conductivity_1",'conductivity_2','conductivity_3','conductivity_4','conductivity_5')
    def _compute_conductivity_average(self):
        for record in self:
            record.conductivity_average = (record.conductivity_1 + record.conductivity_2 + record.conductivity_3 + record.conductivity_4 + record.conductivity_5)/5

    conductivity_average_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_conductivity_average_conformity", store=True)

    @api.depends('conductivity_average','eln_ref','grade')
    def _compute_conductivity_average_conformity(self):
            # remove this first when making changes
            self.conductivity_average_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.conductivity_average_conformity = 'na'
                    continue

                record.conductivity_average_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','j4578m-ba0b-4e64-84d1-e3b23ftyuio1')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','j4578m-ba0b-4e64-84d1-e3b23ftyuio1')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.conductivity_average - record.conductivity_average*mu_value
                        upper = record.conductivity_average + record.conductivity_average*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.conductivity_average_conformity = 'pass'
                            break
                        else:
                            record.conductivity_average_conformity = 'fail'

    conductivity_average_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_conductivity_average_nabl", store=True)

    @api.depends('conductivity_average','eln_ref','grade')
    def _compute_conductivity_average_nabl(self):
        # remove this first
        self.conductivity_average_nabl = 'fail'
        
        for record in self:
            record.conductivity_average_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','j4578m-ba0b-4e64-84d1-e3b23ftyuio1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','j4578m-ba0b-4e64-84d1-e3b23ftyuio1')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.conductivity_average - record.conductivity_average*mu_value
            upper = record.conductivity_average + record.conductivity_average*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.conductivity_average_nabl = 'pass'
                break
            else:
                record.conductivity_average_nabl = 'fail'


                # TOTAL DISSOLVED SOLIDS

    dissolved_solid_name = fields.Char("Name",default="Total Dissolved Solids")
    dissolved_solid_visible = fields.Boolean("DISSOLVED SOLIDS",compute="_compute_visible")

    sample_taken1 = fields.Float(string="Sample taken (V)")
    sample_taken2 = fields.Float(string="Sample taken (V)")
    sample_taken3 = fields.Float(string="Sample taken (V)")
    sample_taken4 = fields.Float(string="Sample taken (V)")
    sample_taken5 = fields.Float(string="Sample taken (V)")

    initial_dish1 = fields.Float(string="Initial wt. evaporating dish")
    initial_dish2 = fields.Float(string="Initial wt. evaporating dish")
    initial_dish3 = fields.Float(string="Initial wt. evaporating dish")
    initial_dish4 = fields.Float(string="Initial wt. evaporating dish")
    initial_dish5 = fields.Float(string="Initial wt. evaporating dish")

    final_dish1 = fields.Float(string="Final wt. of evaporating dish")
    final_dish2 = fields.Float(string="Final wt. of evaporating dish")
    final_dish3 = fields.Float(string="Final wt. of evaporating dish")
    final_dish4 = fields.Float(string="Final wt. of evaporating dish")
    final_dish5 = fields.Float(string="Final wt. of evaporating dish")

    mass_residue1 = fields.Float(string="Mass in mg of filterable residue ( M )")
    mass_residue2 = fields.Float(string="Mass in mg of filterable residue ( M )")
    mass_residue3 = fields.Float(string="Mass in mg of filterable residue ( M )")
    mass_residue4 = fields.Float(string="Mass in mg of filterable residue ( M )")
    mass_residue5 = fields.Float(string="Mass in mg of filterable residue ( M )")

    filterable1 = fields.Float(string="Result Filterable residue",compute="_compute_filterable", store=True)
    filterable2 = fields.Float(string="Result Filterable residue",compute="_compute_filterable", store=True)
    filterable3 = fields.Float(string="Result Filterable residue",compute="_compute_filterable", store=True)
    filterable4 = fields.Float(string="Result Filterable residue",compute="_compute_filterable", store=True)
    filterable5 = fields.Float(string="Result Filterable residue",compute="_compute_filterable", store=True)

    avg_dissolved_solid = fields.Float(string="Average",compute="_compute_avg_dissolved_solid",store=True)

    @api.depends(
        'sample_taken1','mass_residue1',
        'sample_taken2','mass_residue2',
        'sample_taken3','mass_residue3',
        'sample_taken4','mass_residue4',
        'sample_taken5','mass_residue5'
    )
    def _compute_filterable(self):
        for rec in self:
            rec.filterable1 = (rec.mass_residue1 * 1000 / rec.sample_taken1) if rec.sample_taken1 else 0.0
            rec.filterable2 = (rec.mass_residue2 * 1000 / rec.sample_taken2) if rec.sample_taken2 else 0.0
            rec.filterable3 = (rec.mass_residue3 * 1000 / rec.sample_taken3) if rec.sample_taken3 else 0.0
            rec.filterable4 = (rec.mass_residue4 * 1000 / rec.sample_taken4) if rec.sample_taken4 else 0.0
            rec.filterable5 = (rec.mass_residue5 * 1000 / rec.sample_taken5) if rec.sample_taken5 else 0.0

    @api.depends('filterable1','filterable2','filterable3','filterable4','filterable5')
    def _compute_avg_dissolved_solid(self):
        for rec in self:
            values = [
                rec.filterable1,
                rec.filterable2,
                rec.filterable3,
                rec.filterable4,
                rec.filterable5
            ]

            # Optional: None avoid + better average
            valid_values = [v for v in values if v]

            rec.avg_dissolved_solid = sum(valid_values) / len(valid_values) if valid_values else 0.0


    avg_dissolved_solid_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_dissolved_solid_conformity", store=True)

    @api.depends('avg_dissolved_solid','eln_ref','grade')
    def _compute_avg_dissolved_solid_conformity(self):
            # remove this first when making changes
            self.avg_dissolved_solid_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_dissolved_solid_conformity = 'na'
                    continue

                record.avg_dissolved_solid_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','j3214t-ba0b-4e64-84d1-e3b23ftyrty12')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','j3214t-ba0b-4e64-84d1-e3b23ftyrty12')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_dissolved_solid - record.avg_dissolved_solid*mu_value
                        upper = record.avg_dissolved_solid + record.avg_dissolved_solid*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_dissolved_solid_conformity = 'pass'
                            break
                        else:
                            record.avg_dissolved_solid_conformity = 'fail'

    avg_dissolved_solid_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_dissolved_solid_nabl", store=True)

    @api.depends('avg_dissolved_solid','eln_ref','grade')
    def _compute_avg_dissolved_solid_nabl(self):
        # remove this first
        self.avg_dissolved_solid_nabl = 'fail'
        
        for record in self:
            record.avg_dissolved_solid_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','j3214t-ba0b-4e64-84d1-e3b23ftyrty12')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','j3214t-ba0b-4e64-84d1-e3b23ftyrty12')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_dissolved_solid - record.avg_dissolved_solid*mu_value
            upper = record.avg_dissolved_solid + record.avg_dissolved_solid*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_dissolved_solid_nabl = 'pass'
                break
            else:
                record.avg_dissolved_solid_nabl = 'fail'


#    TURBIDITY

    turbidity_name = fields.Char("Name",default="Turbidity")
    turbidity_visible = fields.Boolean("pH",compute="_compute_visible")
    
    turbidity_1 = fields.Float("Observation")
    turbidity_2 = fields.Float("Observation")
    turbidity_3 = fields.Float("Observation")
    turbidity_4 = fields.Float("Observation")
    turbidity_5 = fields.Float("Observation")
    turbidity_average = fields.Float("Average",compute="_compute_turbidity_average")

    @api.depends("turbidity_1",'turbidity_2','turbidity_3','turbidity_4','turbidity_5')
    def _compute_turbidity_average(self):
        for record in self:
            record.turbidity_average = (record.turbidity_1 + record.turbidity_2 + record.turbidity_3 + record.turbidity_4 + record.turbidity_5)/5

    turbidity_average_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_turbidity_average_conformity", store=True)

    @api.depends('turbidity_average','eln_ref','grade')
    def _compute_turbidity_average_conformity(self):
            # remove this first when making changes
            self.turbidity_average_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.turbidity_average_conformity = 'na'
                    continue

                record.turbidity_average_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','654783-ba0b-4e64-84d1-e3b23ftty543')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','654783-ba0b-4e64-84d1-e3b23ftty543')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.turbidity_average - record.turbidity_average*mu_value
                        upper = record.turbidity_average + record.turbidity_average*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.turbidity_average_conformity = 'pass'
                            break
                        else:
                            record.turbidity_average_conformity = 'fail'

    turbidity_average_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_turbidity_average_nabl", store=True)

    @api.depends('turbidity_average','eln_ref','grade')
    def _compute_turbidity_average_nabl(self):
        # remove this first
        self.turbidity_average_nabl = 'fail'
        
        for record in self:
            record.turbidity_average_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','654783-ba0b-4e64-84d1-e3b23ftty543')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','654783-ba0b-4e64-84d1-e3b23ftty543')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.turbidity_average - record.turbidity_average*mu_value
            upper = record.turbidity_average + record.turbidity_average*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.turbidity_average_nabl = 'pass'
                break
            else:
                record.turbidity_average_nabl = 'fail'

     # CHLORIDE

    chloride_name = fields.Char("Name",default="Chloride")
    chloride_visible = fields.Boolean("Chloride",compute="_compute_visible")

    chloride_sample_taken1 = fields.Float(string="Volume of sample to be taken. (V)")
    chloride_sample_taken2 = fields.Float(string="Volume of sample to be taken. (V)")
    chloride_sample_taken3 = fields.Float(string="Volume of sample to be taken. (V)")
    chloride_sample_taken4 = fields.Float(string="Volume of sample to be taken. (V)")
    chloride_sample_taken5 = fields.Float(string="Volume of sample to be taken. (V)")

    chloride_normality1 = fields.Float(string="Normality of AgNo3   0.0141N")
    chloride_normality2 = fields.Float(string="Normality of AgNo3   0.0141N")
    chloride_normality3 = fields.Float(string="Normality of AgNo3   0.0141N")
    chloride_normality4 = fields.Float(string="Normality of AgNo3   0.0141N")
    chloride_normality5 = fields.Float(string="Normality of AgNo3   0.0141N")

    chloride_nitratev2_1 = fields.Float(string="Volume in ml of silver nitrate 0.0141 N used in the blank titration. (V2)")
    chloride_nitratev2_2 = fields.Float(string="Volume in ml of silver nitrate 0.0141 N used in the blank titration. (V2)")
    chloride_nitratev2_3 = fields.Float(string="Volume in ml of silver nitrate 0.0141 N used in the blank titration. (V2)")
    chloride_nitratev2_4 = fields.Float(string="Volume in ml of silver nitrate 0.0141 N used in the blank titration. (V2)")
    chloride_nitratev2_5 = fields.Float(string="Volume in ml of silver nitrate 0.0141 N used in the blank titration. (V2)")

    chloride_nitratev1_1 = fields.Float(string="Volume in ml of silver nitrate 0.0141 N used in the sample titration. (V1)")
    chloride_nitratev1_2 = fields.Float(string="Volume in ml of silver nitrate 0.0141 N used in the sample titration. (V1)")
    chloride_nitratev1_3 = fields.Float(string="Volume in ml of silver nitrate 0.0141 N used in the sample titration. (V1)")
    chloride_nitratev1_4 = fields.Float(string="Volume in ml of silver nitrate 0.0141 N used in the sample titration. (V1)")
    chloride_nitratev1_5 = fields.Float(string="Volume in ml of silver nitrate 0.0141 N used in the sample titration. (V1)")

    chloride1 = fields.Float(string="Chloride,(mg/l)",compute="_compute_chloride", store=True)
    chloride2 = fields.Float(string="Chloride,(mg/l)",compute="_compute_chloride", store=True)
    chloride3 = fields.Float(string="Chloride,(mg/l)",compute="_compute_chloride", store=True)
    chloride4 = fields.Float(string="Chloride,(mg/l)",compute="_compute_chloride", store=True)
    chloride5 = fields.Float(string="Chloride,(mg/l)",compute="_compute_chloride", store=True)

    avg_chloride = fields.Float(string="Average Chloride (mg/l)",compute="_compute_avg_chloride",store=True)


    @api.depends(
        'chloride_sample_taken1','chloride_normality1','chloride_nitratev1_1','chloride_nitratev2_1',
        'chloride_sample_taken2','chloride_normality2','chloride_nitratev1_2','chloride_nitratev2_2',
        'chloride_sample_taken3','chloride_normality3','chloride_nitratev1_3','chloride_nitratev2_3',
        'chloride_sample_taken4','chloride_normality4','chloride_nitratev1_4','chloride_nitratev2_4',
        'chloride_sample_taken5','chloride_normality5','chloride_nitratev1_5','chloride_nitratev2_5',
    )
    def _compute_chloride(self):
        for rec in self:

            rec.chloride1 = ((rec.chloride_nitratev1_1 - rec.chloride_nitratev2_1) * rec.chloride_normality1 * 35450 / rec.chloride_sample_taken1) if rec.chloride_sample_taken1 else 0.0

            rec.chloride2 = ((rec.chloride_nitratev1_2 - rec.chloride_nitratev2_2) * rec.chloride_normality2 * 35450 / rec.chloride_sample_taken2) if rec.chloride_sample_taken2 else 0.0

            rec.chloride3 = ((rec.chloride_nitratev1_3 - rec.chloride_nitratev2_3) * rec.chloride_normality3 * 35450 / rec.chloride_sample_taken3) if rec.chloride_sample_taken3 else 0.0

            rec.chloride4 = ((rec.chloride_nitratev1_4 - rec.chloride_nitratev2_4) * rec.chloride_normality4 * 35450 / rec.chloride_sample_taken4) if rec.chloride_sample_taken4 else 0.0

            rec.chloride5 = ((rec.chloride_nitratev1_5 - rec.chloride_nitratev2_5) * rec.chloride_normality5 * 35450 / rec.chloride_sample_taken5) if rec.chloride_sample_taken5 else 0.0

        
    @api.depends('chloride1','chloride2','chloride3','chloride4','chloride5')
    def _compute_avg_chloride(self):
        for rec in self:
            rec.avg_chloride = (
                rec.chloride1 +
                rec.chloride2 +
                rec.chloride3 +
                rec.chloride4 +
                rec.chloride5
            ) / 5

    avg_chloride_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_chloride_conformity", store=True)

    @api.depends('avg_chloride','eln_ref','grade')
    def _compute_avg_chloride_conformity(self):
            # remove this first when making changes
            self.avg_chloride_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_chloride_conformity = 'na'
                    continue

                record.avg_chloride_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32014y-ba0b-4e64-84d1-e3b23ft301yr')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32014y-ba0b-4e64-84d1-e3b23ft301yr')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_chloride - record.avg_chloride*mu_value
                        upper = record.avg_chloride + record.avg_chloride*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_chloride_conformity = 'pass'
                            break
                        else:
                            record.avg_chloride_conformity = 'fail'

    avg_chloride_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_chloride_nabl", store=True)

    @api.depends('avg_chloride','eln_ref','grade')
    def _compute_avg_chloride_nabl(self):
        # remove this first
        self.avg_chloride_nabl = 'fail'
        
        for record in self:
            record.avg_chloride_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32014y-ba0b-4e64-84d1-e3b23ft301yr')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32014y-ba0b-4e64-84d1-e3b23ft301yr')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_chloride - record.avg_chloride*mu_value
            upper = record.avg_chloride + record.avg_chloride*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_chloride_nabl = 'pass'
                break
            else:
                record.avg_chloride_nabl = 'fail'

    # HARDNESS

    hardness_name = fields.Char("Name",default="Hardness")
    hardness_visible = fields.Boolean("hardness",compute="_compute_visible")

    cf = fields.Float(string="Correction Factor (CF)")

    hardness_sample_takenv3_1 = fields.Float(string="Volume in ml of the sample taken for the test.(V3)")
    hardness_sample_takenv3_2 = fields.Float(string="Volume in ml of the sample taken for the test.(V3)")
    hardness_sample_takenv3_3 = fields.Float(string="Volume in ml of the sample taken for the test.(V3)")
    hardness_sample_takenv3_4 = fields.Float(string="Volume in ml of the sample taken for the test.(V3)")
    hardness_sample_takenv3_5 = fields.Float(string="Volume in ml of the sample taken for the test.(V3)")

    hardness_titrationv2_1 = fields.Float(string="Volume in ml of EDTA solution used in the titration for blank. (V2)")
    hardness_titrationv2_2 = fields.Float(string="Volume in ml of EDTA solution used in the titration for blank. (V2)")
    hardness_titrationv2_3 = fields.Float(string="Volume in ml of EDTA solution used in the titration for blank. (V2)")
    hardness_titrationv2_4 = fields.Float(string="Volume in ml of EDTA solution used in the titration for blank. (V2)")
    hardness_titrationv2_5 = fields.Float(string="Volume in ml of EDTA solution used in the titration for blank. (V2)")

    hardness_titrationv1_1 = fields.Float(string="Volume in ml of the EDTA standard solution0.02 N used in the titration for the sample, ( V1 )")
    hardness_titrationv1_2 = fields.Float(string="Volume in ml of the EDTA standard solution0.02 N used in the titration for the sample, ( V1 )")
    hardness_titrationv1_3 = fields.Float(string="Volume in ml of the EDTA standard solution0.02 N used in the titration for the sample, ( V1 )")
    hardness_titrationv1_4 = fields.Float(string="Volume in ml of the EDTA standard solution0.02 N used in the titration for the sample, ( V1 )")
    hardness_titrationv1_5 = fields.Float(string="Volume in ml of the EDTA standard solution0.02 N used in the titration for the sample, ( V1 )")

    
    hardness1 = fields.Float(string="Total Hardness as ( CaCO3 ), mg/l",compute="_compute_hardness", store=True)
    hardness2 = fields.Float(string="Total Hardness as ( CaCO3 ), mg/l",compute="_compute_hardness", store=True)
    hardness3 = fields.Float(string="Total Hardness as ( CaCO3 ), mg/l",compute="_compute_hardness", store=True)
    hardness4 = fields.Float(string="Total Hardness as ( CaCO3 ), mg/l",compute="_compute_hardness", store=True)
    hardness5 = fields.Float(string="Total Hardness as ( CaCO3 ), mg/l",compute="_compute_hardness", store=True)

    avg_hardness = fields.Float(string="Average Hardness (mg/l)",compute="_compute_avg_hardness", store=True)

    @api.depends('hardness1','hardness2','hardness3','hardness4','hardness5')
    def _compute_avg_hardness(self):
        for rec in self:
            rec.avg_hardness = (
                rec.hardness1 +
                rec.hardness2 +
                rec.hardness3 +
                rec.hardness4 +
                rec.hardness5
            ) / 5


    @api.depends(
    'cf',
    'hardness_sample_takenv3_1','hardness_titrationv1_1','hardness_titrationv2_1',
    'hardness_sample_takenv3_2','hardness_titrationv1_2','hardness_titrationv2_2',
    'hardness_sample_takenv3_3','hardness_titrationv1_3','hardness_titrationv2_3',
    'hardness_sample_takenv3_4','hardness_titrationv1_4','hardness_titrationv2_4',
    'hardness_sample_takenv3_5','hardness_titrationv1_5','hardness_titrationv2_5',
    )
    def _compute_hardness(self):
        for rec in self:

            rec.hardness1 = ((rec.hardness_titrationv1_1 - rec.hardness_titrationv2_1) * rec.cf * 1000 / rec.hardness_sample_takenv3_1) if rec.hardness_sample_takenv3_1 else 0.0

            rec.hardness2 = ((rec.hardness_titrationv1_2 - rec.hardness_titrationv2_2) * rec.cf * 1000 / rec.hardness_sample_takenv3_2) if rec.hardness_sample_takenv3_2 else 0.0

            rec.hardness3 = ((rec.hardness_titrationv1_3 - rec.hardness_titrationv2_3) * rec.cf * 1000 / rec.hardness_sample_takenv3_3) if rec.hardness_sample_takenv3_3 else 0.0

            rec.hardness4 = ((rec.hardness_titrationv1_4 - rec.hardness_titrationv2_4) * rec.cf * 1000 / rec.hardness_sample_takenv3_4) if rec.hardness_sample_takenv3_4 else 0.0

            rec.hardness5 = ((rec.hardness_titrationv1_5 - rec.hardness_titrationv2_5) * rec.cf * 1000 / rec.hardness_sample_takenv3_5) if rec.hardness_sample_takenv3_5 else 0.0


    avg_hardness_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_hardness_conformity", store=True)

    @api.depends('avg_hardness','eln_ref','grade')
    def _compute_avg_hardness_conformity(self):
            # remove this first when making changes
            self.avg_hardness_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_hardness_conformity = 'na'
                    continue

                record.avg_hardness_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30124t-ba0b-4e64-84d1-e3b23ft0147t')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30124t-ba0b-4e64-84d1-e3b23ft0147t')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_hardness - record.avg_hardness*mu_value
                        upper = record.avg_hardness + record.avg_hardness*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_hardness_conformity = 'pass'
                            break
                        else:
                            record.avg_hardness_conformity = 'fail'

    avg_hardness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_hardness_nabl", store=True)

    @api.depends('avg_hardness','eln_ref','grade')
    def _compute_avg_hardness_nabl(self):
        # remove this first
        self.avg_hardness_nabl = 'fail'
        
        for record in self:
            record.avg_hardness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30124t-ba0b-4e64-84d1-e3b23ft0147t')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30124t-ba0b-4e64-84d1-e3b23ft0147t')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_hardness - record.avg_hardness*mu_value
            upper = record.avg_hardness + record.avg_hardness*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_hardness_nabl = 'pass'
                break
            else:
                record.avg_hardness_nabl = 'fail'

   
    #  Alkalinity
    
    alkalinity_name = fields.Char("Name",default="Alkalinity")
    alkalinity_visible = fields.Boolean("alkalinity",compute="_compute_visible")


    alkalinity_sample_takenv3_1 = fields.Float(string="Volume in ml of the sample taken for the test.(V)")
    alkalinity_sample_takenv3_2 = fields.Float(string="Volume in ml of the sample taken for the test.(V)")
    alkalinity_sample_takenv3_3 = fields.Float(string="Volume in ml of the sample taken for the test.(V)")
    alkalinity_sample_takenv3_4 = fields.Float(string="Volume in ml of the sample taken for the test.(V)")
    alkalinity_sample_takenv3_5 = fields.Float(string="Volume in ml of the sample taken for the test.(V)")

    alkalinity_titrationx1_1 = fields.Float(string="Volume in ml of Sulphuric acid 0.02 N solution used in the titration. (X1))")
    alkalinity_titrationx1_2 = fields.Float(string="Volume in ml of Sulphuric acid 0.02 N solution used in the titration. (X1))")
    alkalinity_titrationx1_3 = fields.Float(string="Volume in ml of Sulphuric acid 0.02 N solution used in the titration. (X1))")
    alkalinity_titrationx1_4 = fields.Float(string="Volume in ml of Sulphuric acid 0.02 N solution used in the titration. (X1))")
    alkalinity_titrationx1_5 = fields.Float(string="Volume in ml of Sulphuric acid 0.02 N solution used in the titration. (X1))")

    alkalinity_normality_1 = fields.Float(string="Normality of H2SO4  (0.02 N)")
    alkalinity_normality_2 = fields.Float(string="Normality of H2SO4  (0.02 N)")
    alkalinity_normality_3 = fields.Float(string="Normality of H2SO4  (0.02 N)")
    alkalinity_normality_4 = fields.Float(string="Normality of H2SO4  (0.02 N)")
    alkalinity_normality_5 = fields.Float(string="Normality of H2SO4  (0.02 N)")

    
    alkalinity1 = fields.Float(string="Total Alkalinity", compute="_compute_alkalinity", store=True)
    alkalinity2 = fields.Float(string="Total Alkalinity", compute="_compute_alkalinity", store=True)
    alkalinity3 = fields.Float(string="Total Alkalinity", compute="_compute_alkalinity", store=True)
    alkalinity4 = fields.Float(string="Total Alkalinity", compute="_compute_alkalinity", store=True)
    alkalinity5 = fields.Float(string="Total Alkalinity", compute="_compute_alkalinity", store=True)

    avg_alkalinity = fields.Float(string="Average Alkalinity (mg/l)",compute="_compute_avg_alkalinity", store=True)


    @api.depends(
    'alkalinity_sample_takenv3_1','alkalinity_titrationx1_1','alkalinity_normality_1',
    'alkalinity_sample_takenv3_2','alkalinity_titrationx1_2','alkalinity_normality_2',
    'alkalinity_sample_takenv3_3','alkalinity_titrationx1_3','alkalinity_normality_3',
    'alkalinity_sample_takenv3_4','alkalinity_titrationx1_4','alkalinity_normality_4',
    'alkalinity_sample_takenv3_5','alkalinity_titrationx1_5','alkalinity_normality_5',
    )
    def _compute_alkalinity(self):
        for rec in self:

            rec.alkalinity1 = (rec.alkalinity_titrationx1_1 * rec.alkalinity_normality_1 * 50 * 1000 / rec.alkalinity_sample_takenv3_1) if rec.alkalinity_sample_takenv3_1 else 0.0

            rec.alkalinity2 = (rec.alkalinity_titrationx1_2 * rec.alkalinity_normality_2 * 50 * 1000 / rec.alkalinity_sample_takenv3_2) if rec.alkalinity_sample_takenv3_2 else 0.0

            rec.alkalinity3 = (rec.alkalinity_titrationx1_3 * rec.alkalinity_normality_3 * 50 * 1000 / rec.alkalinity_sample_takenv3_3) if rec.alkalinity_sample_takenv3_3 else 0.0

            rec.alkalinity4 = (rec.alkalinity_titrationx1_4 * rec.alkalinity_normality_4 * 50 * 1000 / rec.alkalinity_sample_takenv3_4) if rec.alkalinity_sample_takenv3_4 else 0.0

            rec.alkalinity5 = (rec.alkalinity_titrationx1_5 * rec.alkalinity_normality_5 * 50 * 1000 / rec.alkalinity_sample_takenv3_5) if rec.alkalinity_sample_takenv3_5 else 0.0


    @api.depends('alkalinity1','alkalinity2','alkalinity3','alkalinity4','alkalinity5')
    def _compute_avg_alkalinity(self):
        for rec in self:
            rec.avg_alkalinity = (
                rec.alkalinity1 +
                rec.alkalinity2 +
                rec.alkalinity3 +
                rec.alkalinity4 +
                rec.alkalinity5
            ) / 5


    avg_alkalinity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_alkalinity_conformity", store=True)

    @api.depends('avg_alkalinity','eln_ref','grade')
    def _compute_avg_alkalinity_conformity(self):
            # remove this first when making changes
            self.avg_alkalinity_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_alkalinity_conformity = 'na'
                    continue

                record.avg_alkalinity_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','012478-ba0b-4e64-84d1-e3b23f30147g')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','012478-ba0b-4e64-84d1-e3b23f30147g')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_alkalinity - record.avg_alkalinity*mu_value
                        upper = record.avg_alkalinity + record.avg_alkalinity*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_alkalinity_conformity = 'pass'
                            break
                        else:
                            record.avg_alkalinity_conformity = 'fail'

    avg_alkalinity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_alkalinity_nabl", store=True)

    @api.depends('avg_alkalinity','eln_ref','grade')
    def _compute_avg_alkalinity_nabl(self):
        # remove this first
        self.avg_alkalinity_nabl = 'fail'
        
        for record in self:
            record.avg_alkalinity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','012478-ba0b-4e64-84d1-e3b23f30147g')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','012478-ba0b-4e64-84d1-e3b23f30147g')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_alkalinity - record.avg_alkalinity*mu_value
            upper = record.avg_alkalinity + record.avg_alkalinity*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_alkalinity_nabl = 'pass'
                break
            else:
                record.avg_alkalinity_nabl = 'fail'


    #  calcium
    
    calcium_name = fields.Char("Name",default="Calcium")
    calcium_visible = fields.Boolean("Calcium",compute="_compute_visible")


    calcium_sample_takenv_1 = fields.Float(string="Volume in ml of the sample taken for the test. (V)")
    calcium_sample_takenv_2 = fields.Float(string="Volume in ml of the sample taken for the test. (V)")
    calcium_sample_takenv_3 = fields.Float(string="Volume in ml of the sample taken for the test. (V)")
    calcium_sample_takenv_4 = fields.Float(string="Volume in ml of the sample taken for the test. (V)")
    calcium_sample_takenv_5 = fields.Float(string="Volume in ml of the sample taken for the test. (V)")

    calcium_titrationv1_1 = fields.Float(string="Volume in ml of EDTA solution used in the titration for Sample. (V1)")
    calcium_titrationv1_2 = fields.Float(string="Volume in ml of EDTA solution used in the titration for Sample. (V1)")
    calcium_titrationv1_3 = fields.Float(string="Volume in ml of EDTA solution used in the titration for Sample. (V1)")
    calcium_titrationv1_4 = fields.Float(string="Volume in ml of EDTA solution used in the titration for Sample. (V1)")
    calcium_titrationv1_5 = fields.Float(string="Volume in ml of EDTA solution used in the titration for Sample. (V1)")

    calcium1 = fields.Float(string="Calcium (mg/l)",compute="_compute_calcium", store=True)
    calcium2 = fields.Float(string="Calcium (mg/l)",compute="_compute_calcium", store=True)
    calcium3 = fields.Float(string="Calcium (mg/l)",compute="_compute_calcium", store=True)
    calcium4 = fields.Float(string="Calcium (mg/l)",compute="_compute_calcium", store=True)
    calcium5 = fields.Float(string="Calcium (mg/l)",compute="_compute_calcium", store=True)

    avg_calcium = fields.Float(string="Average Calcium (mg/l)",compute="_compute_avg_calcium", store=True)


    @api.depends('calcium1','calcium2','calcium3','calcium4','calcium5')
    def _compute_avg_calcium(self):
        for rec in self:
            rec.avg_calcium = (
                rec.calcium1 +
                rec.calcium2 +
                rec.calcium3 +
                rec.calcium4 +
                rec.calcium5
            ) / 5


    @api.depends(
    'calcium_sample_takenv_1','calcium_titrationv1_1',
    'calcium_sample_takenv_2','calcium_titrationv1_2',
    'calcium_sample_takenv_3','calcium_titrationv1_3',
    'calcium_sample_takenv_4','calcium_titrationv1_4',
    'calcium_sample_takenv_5','calcium_titrationv1_5',
    )
    def _compute_calcium(self):
        for rec in self:

            rec.calcium1 = (rec.calcium_titrationv1_1 * 0.4008 * 1000 / rec.calcium_sample_takenv_1) if rec.calcium_sample_takenv_1 else 0.0

            rec.calcium2 = (rec.calcium_titrationv1_2 * 0.4008 * 1000 / rec.calcium_sample_takenv_2) if rec.calcium_sample_takenv_2 else 0.0

            rec.calcium3 = (rec.calcium_titrationv1_3 * 0.4008 * 1000 / rec.calcium_sample_takenv_3) if rec.calcium_sample_takenv_3 else 0.0

            rec.calcium4 = (rec.calcium_titrationv1_4 * 0.4008 * 1000 / rec.calcium_sample_takenv_4) if rec.calcium_sample_takenv_4 else 0.0

            rec.calcium5 = (rec.calcium_titrationv1_5 * 0.4008 * 1000 / rec.calcium_sample_takenv_5) if rec.calcium_sample_takenv_5 else 0.0


    avg_calcium_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_calcium_conformity", store=True)

    @api.depends('avg_calcium','eln_ref','grade')
    def _compute_avg_calcium_conformity(self):
            # remove this first when making changes
            self.avg_calcium_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_calcium_conformity = 'na'
                    continue

                record.avg_calcium_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','654780-ba0b-4e64-84d1-e3b23f33214ty')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','654780-ba0b-4e64-84d1-e3b23f33214ty')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_calcium - record.avg_calcium*mu_value
                        upper = record.avg_calcium + record.avg_calcium*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_calcium_conformity = 'pass'
                            break
                        else:
                            record.avg_calcium_conformity = 'fail'

    avg_calcium_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_calcium_nabl", store=True)

    @api.depends('avg_calcium','eln_ref','grade')
    def _compute_avg_calcium_nabl(self):
        # remove this first
        self.avg_calcium_nabl = 'fail'
        
        for record in self:
            record.avg_calcium_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','654780-ba0b-4e64-84d1-e3b23f33214ty')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','654780-ba0b-4e64-84d1-e3b23f33214ty')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_calcium - record.avg_calcium*mu_value
            upper = record.avg_calcium + record.avg_calcium*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_calcium_nabl = 'pass'
                break
            else:
                record.avg_calcium_nabl = 'fail'

    #   MAGNESIUM
    
    magnesium_name = fields.Char("Name",default="Magnesium")
    magnesium_visible = fields.Boolean("Magnesium",compute="_compute_visible")

    cf_magnesium = fields.Float(string="Correction Factor (CF)")

    magnesium_sample_taken_1 = fields.Float(string="sample taken )")
    magnesium_sample_taken_2 = fields.Float(string="sample taken )")
    magnesium_sample_taken_3 = fields.Float(string="sample taken )")
    magnesium_sample_taken_4 = fields.Float(string="sample taken )")
    magnesium_sample_taken_5 = fields.Float(string="sample taken )")

    magnesium_calcium_titre_1 = fields.Float(string="calcium Titre Value")
    magnesium_calcium_titre_2 = fields.Float(string="calcium Titre Value")
    magnesium_calcium_titre_3 = fields.Float(string="calcium Titre Value")
    magnesium_calcium_titre_4 = fields.Float(string="calcium Titre Value")
    magnesium_calcium_titre_5 = fields.Float(string="calcium Titre Value") 

    magnesium_th_1 = fields.Float(string="Total Hardness (mg/l)")
    magnesium_th_2 = fields.Float(string="Total Hardness (mg/l)")
    magnesium_th_3 = fields.Float(string="Total Hardness (mg/l)")
    magnesium_th_4 = fields.Float(string="Total Hardness (mg/l)")
    magnesium_th_5 = fields.Float(string="Total Hardness (mg/l)")

    magnesium_ch_1 = fields.Float(string="Calcium Hardness (mg/l)",compute="_compute_magnesium_ch", store=True)
    magnesium_ch_2 = fields.Float(string="Calcium Hardness (mg/l)",compute="_compute_magnesium_ch", store=True)
    magnesium_ch_3 = fields.Float(string="Calcium Hardness (mg/l)",compute="_compute_magnesium_ch", store=True)
    magnesium_ch_4 = fields.Float(string="Calcium Hardness (mg/l)",compute="_compute_magnesium_ch", store=True)
    magnesium_ch_5 = fields.Float(string="Calcium Hardness (mg/l)",compute="_compute_magnesium_ch", store=True)

    
    magnesium_mh_1 = fields.Float(string="Magnesium Hardness", compute="_compute_magnesium_mh", store=True)
    magnesium_mh_2 = fields.Float(string="Magnesium Hardness", compute="_compute_magnesium_mh", store=True)
    magnesium_mh_3 = fields.Float(string="Magnesium Hardness", compute="_compute_magnesium_mh", store=True)
    magnesium_mh_4 = fields.Float(string="Magnesium Hardness", compute="_compute_magnesium_mh", store=True)
    magnesium_mh_5 = fields.Float(string="Magnesium Hardness", compute="_compute_magnesium_mh", store=True)

    magnesium_1 = fields.Float(string="Magnesium (mg/l)", compute="_compute_magnesium", store=True)
    magnesium_2 = fields.Float(string="Magnesium (mg/l)", compute="_compute_magnesium", store=True)
    magnesium_3 = fields.Float(string="Magnesium (mg/l)", compute="_compute_magnesium", store=True)
    magnesium_4 = fields.Float(string="Magnesium (mg/l)", compute="_compute_magnesium", store=True)
    magnesium_5 = fields.Float(string="Magnesium (mg/l)", compute="_compute_magnesium", store=True)

    avg_magnesium = fields.Float(string="Average Magnesium (mg/l)",)


    @api.depends('magnesium_1','magnesium_2','magnesium_3','magnesium_4','magnesium_5')
    def _compute_avg_magnesium(self):
        for rec in self:
            rec.avg_magnesium = (
                rec.magnesium_1 +
                rec.magnesium_2 +
                rec.magnesium_3 +
                rec.magnesium_4 +
                rec.magnesium_5
            ) / 5


    @api.depends(
    'cf_magnesium',
    'magnesium_sample_taken_1','magnesium_calcium_titre_1',
    'magnesium_sample_taken_2','magnesium_calcium_titre_2',
    'magnesium_sample_taken_3','magnesium_calcium_titre_3',
    'magnesium_sample_taken_4','magnesium_calcium_titre_4',
    'magnesium_sample_taken_5','magnesium_calcium_titre_5',
    )
    def _compute_magnesium_ch(self):
        for rec in self:
            rec.magnesium_ch_1 = (rec.magnesium_calcium_titre_1 * rec.cf_magnesium * 100 / rec.magnesium_sample_taken_1) if rec.magnesium_sample_taken_1 else 0.0
            rec.magnesium_ch_2 = (rec.magnesium_calcium_titre_2 * rec.cf_magnesium * 100 / rec.magnesium_sample_taken_2) if rec.magnesium_sample_taken_2 else 0.0
            rec.magnesium_ch_3 = (rec.magnesium_calcium_titre_3 * rec.cf_magnesium * 100 / rec.magnesium_sample_taken_3) if rec.magnesium_sample_taken_3 else 0.0
            rec.magnesium_ch_4 = (rec.magnesium_calcium_titre_4 * rec.cf_magnesium * 100 / rec.magnesium_sample_taken_4) if rec.magnesium_sample_taken_4 else 0.0
            rec.magnesium_ch_5 = (rec.magnesium_calcium_titre_5 * rec.cf_magnesium * 100 / rec.magnesium_sample_taken_5) if rec.magnesium_sample_taken_5 else 0.0

    @api.depends(
    'magnesium_th_1','magnesium_ch_1',
    'magnesium_th_2','magnesium_ch_2',
    'magnesium_th_3','magnesium_ch_3',
    'magnesium_th_4','magnesium_ch_4',
    'magnesium_th_5','magnesium_ch_5',
    )
    def _compute_magnesium_mh(self):
        for rec in self:
            rec.magnesium_mh_1 = rec.magnesium_th_1 - rec.magnesium_ch_1
            rec.magnesium_mh_2 = rec.magnesium_th_2 - rec.magnesium_ch_2
            rec.magnesium_mh_3 = rec.magnesium_th_3 - rec.magnesium_ch_3
            rec.magnesium_mh_4 = rec.magnesium_th_4 - rec.magnesium_ch_4
            rec.magnesium_mh_5 = rec.magnesium_th_5 - rec.magnesium_ch_5

    @api.depends(
    'magnesium_mh_1','magnesium_mh_2','magnesium_mh_3',
    'magnesium_mh_4','magnesium_mh_5'
    )
    def _compute_magnesium(self):
        for rec in self:
            rec.magnesium_1 = rec.magnesium_mh_1 * 0.243
            rec.magnesium_2 = rec.magnesium_mh_2 * 0.243
            rec.magnesium_3 = rec.magnesium_mh_3 * 0.243
            rec.magnesium_4 = rec.magnesium_mh_4 * 0.243
            rec.magnesium_5 = rec.magnesium_mh_5 * 0.243

    avg_magnesium_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_magnesium_conformity", store=True)

    @api.depends('avg_magnesium','eln_ref','grade')
    def _compute_avg_magnesium_conformity(self):
            # remove this first when making changes
            self.avg_magnesium_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_magnesium_conformity = 'na'
                    continue

                record.avg_magnesium_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32147t-ba0b-4e64-84d1-e3b23f33treb2')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32147t-ba0b-4e64-84d1-e3b23f33treb2')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_magnesium - record.avg_magnesium*mu_value
                        upper = record.avg_magnesium + record.avg_magnesium*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_magnesium_conformity = 'pass'
                            break
                        else:
                            record.avg_magnesium_conformity = 'fail'

    avg_magnesium_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_magnesium_nabl", store=True)

    @api.depends('avg_magnesium','eln_ref','grade')
    def _compute_avg_magnesium_nabl(self):
        # remove this first
        self.avg_magnesium_nabl = 'fail'
        
        for record in self:
            record.avg_magnesium_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32147t-ba0b-4e64-84d1-e3b23f33treb2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32147t-ba0b-4e64-84d1-e3b23f33treb2')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_magnesium - record.avg_magnesium*mu_value
            upper = record.avg_magnesium + record.avg_magnesium*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_magnesium_nabl = 'pass'
                break
            else:
                record.avg_magnesium_nabl = 'fail'

    
    # SULPHATE

    

    sulphate_name = fields.Char("Name",default="Sulphate")
    sulphate_visible = fields.Boolean("pH",compute="_compute_visible")
    
    sulphate_1 = fields.Float("Observation")
    sulphate_2 = fields.Float("Observation")
    sulphate_3 = fields.Float("Observation")
    sulphate_4 = fields.Float("Observation")
    sulphate_5 = fields.Float("Observation")
    sulphate_average = fields.Float("Average",compute="_compute_sulphate_average")

    @api.depends("sulphate_1",'sulphate_2','sulphate_3','sulphate_4','sulphate_5')
    def _compute_sulphate_average(self):
        for record in self:
            record.sulphate_average = (record.sulphate_1 + record.sulphate_2 + record.sulphate_3 + record.sulphate_4 + record.sulphate_5)/5

    sulphate_average_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_sulphate_average_conformity", store=True)

    @api.depends('sulphate_average','eln_ref','grade')
    def _compute_sulphate_average_conformity(self):
            # remove this first when making changes
            self.sulphate_average_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.sulphate_average_conformity = 'na'
                    continue

                record.sulphate_average_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','547uyt-ba0b-4e64-84d1-e3b23ftyrtf51')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','547uyt-ba0b-4e64-84d1-e3b23ftyrtf51')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.sulphate_average - record.sulphate_average*mu_value
                        upper = record.sulphate_average + record.sulphate_average*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.sulphate_average_conformity = 'pass'
                            break
                        else:
                            record.sulphate_average_conformity = 'fail'

    sulphate_average_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_sulphate_average_nabl", store=True)

    @api.depends('sulphate_average','eln_ref','grade')
    def _compute_sulphate_average_nabl(self):
        # remove this first
        self.sulphate_average_nabl = 'fail'
        
        for record in self:
            record.sulphate_average_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','547uyt-ba0b-4e64-84d1-e3b23ftyrtf51')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','547uyt-ba0b-4e64-84d1-e3b23ftyrtf51')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.sulphate_average - record.sulphate_average*mu_value
            upper = record.sulphate_average + record.sulphate_average*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.sulphate_average_nabl = 'pass'
                break
            else:
                record.sulphate_average_nabl = 'fail'


    # NITRATE
    
    nitrate_name = fields.Char("Name",default="Nitrate")
    nitrate_visible = fields.Boolean("pH",compute="_compute_visible")
    
    nitrate_1 = fields.Float("Observation")
    nitrate_2 = fields.Float("Observation")
    nitrate_3 = fields.Float("Observation")
    nitrate_4 = fields.Float("Observation")
    nitrate_5 = fields.Float("Observation")
    nitrate_average = fields.Float("Average",compute="_compute_nitrate_average")

    @api.depends("nitrate_1",'nitrate_2','nitrate_3','nitrate_4','nitrate_5')
    def _compute_nitrate_average(self):
        for record in self:
            record.nitrate_average = (record.nitrate_1 + record.nitrate_2 + record.nitrate_3 + record.nitrate_4 + record.nitrate_5)/5

    nitrate_average_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_nitrate_average_conformity", store=True)

    @api.depends('nitrate_average','eln_ref','grade')
    def _compute_nitrate_average_conformity(self):
            # remove this first when making changes
            self.nitrate_average_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.nitrate_average_conformity = 'na'
                    continue

                record.nitrate_average_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6547hy-ba0b-4e64-84d1-e3b23fty471lk')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6547hy-ba0b-4e64-84d1-e3b23fty471lk')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.nitrate_average - record.nitrate_average*mu_value
                        upper = record.nitrate_average + record.nitrate_average*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.nitrate_average_conformity = 'pass'
                            break
                        else:
                            record.nitrate_average_conformity = 'fail'

    nitrate_average_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_nitrate_average_nabl", store=True)

    @api.depends('nitrate_average','eln_ref','grade')
    def _compute_nitrate_average_nabl(self):
        # remove this first
        self.nitrate_average_nabl = 'fail'
        
        for record in self:
            record.nitrate_average_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6547hy-ba0b-4e64-84d1-e3b23fty471lk')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6547hy-ba0b-4e64-84d1-e3b23fty471lk')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.nitrate_average - record.nitrate_average*mu_value
            upper = record.nitrate_average + record.nitrate_average*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.nitrate_average_nabl = 'pass'
                break
            else:
                record.nitrate_average_nabl = 'fail'

    # REACTIVE SILICA
    
    silica_name = fields.Char("Name",default="Reactive Silica")
    silica_visible = fields.Boolean("pH",compute="_compute_visible")
    
    silica_1 = fields.Float("Observation")
    silica_2 = fields.Float("Observation")
    silica_3 = fields.Float("Observation")
    silica_4 = fields.Float("Observation")
    silica_5 = fields.Float("Observation")
    silica_average = fields.Float("Average",compute="_compute_silica_average")

    @api.depends("silica_1",'silica_2','silica_3','silica_4','silica_5')
    def _compute_silica_average(self):
        for record in self:
            record.silica_average = (record.silica_1 + record.silica_2 + record.silica_3 + record.silica_4 + record.silica_5)/5

    silica_average_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_silica_average_conformity", store=True)

    @api.depends('silica_average','eln_ref','grade')
    def _compute_silica_average_conformity(self):
            # remove this first when making changes
            self.silica_average_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.silica_average_conformity = 'na'
                    continue

                record.silica_average_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','75847y-ba0b-4e64-84d1-e3b23ftyytr56')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','75847y-ba0b-4e64-84d1-e3b23ftyytr56')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.silica_average - record.silica_average*mu_value
                        upper = record.silica_average + record.silica_average*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.silica_average_conformity = 'pass'
                            break
                        else:
                            record.silica_average_conformity = 'fail'

    silica_average_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_silica_average_nabl", store=True)

    @api.depends('silica_average','eln_ref','grade')
    def _compute_silica_average_nabl(self):
        # remove this first
        self.silica_average_nabl = 'fail'
        
        for record in self:
            record.silica_average_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','75847y-ba0b-4e64-84d1-e3b23ftyytr56')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','75847y-ba0b-4e64-84d1-e3b23ftyytr56')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.silica_average - record.silica_average*mu_value
            upper = record.silica_average + record.silica_average*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.silica_average_nabl = 'pass'
                break
            else:
                record.silica_average_nabl = 'fail'


    # Phosphorus
    phosphorus_name = fields.Char("Name",default="Phosphorus")
    phosphorus_visible = fields.Boolean("pH",compute="_compute_visible")
    
    phosphorus_1 = fields.Float("Observation")
    phosphorus_2 = fields.Float("Observation")
    phosphorus_3 = fields.Float("Observation")
    phosphorus_4 = fields.Float("Observation")
    phosphorus_5 = fields.Float("Observation")
    phosphorus_average = fields.Float("Average",compute="_compute_phosphorus_average")

    @api.depends("phosphorus_1",'phosphorus_2','phosphorus_3','phosphorus_4','phosphorus_5')
    def _compute_phosphorus_average(self):
        for record in self:
            record.phosphorus_average = (record.phosphorus_1 + record.phosphorus_2 + record.phosphorus_3 + record.phosphorus_4 + record.phosphorus_5)/5

    phosphorus_average_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_phosphorus_average_conformity", store=True)

    @api.depends('phosphorus_average','eln_ref','grade')
    def _compute_phosphorus_average_conformity(self):
            # remove this first when making changes
            self.phosphorus_average_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.phosphorus_average_conformity = 'na'
                    continue

                record.phosphorus_average_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62478ye-ba0b-4e64-84d1-e3b23ftyy147r')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62478ye-ba0b-4e64-84d1-e3b23ftyy147r')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.phosphorus_average - record.phosphorus_average*mu_value
                        upper = record.phosphorus_average + record.phosphorus_average*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.phosphorus_average_conformity = 'pass'
                            break
                        else:
                            record.phosphorus_average_conformity = 'fail'

    phosphorus_average_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_phosphorus_average_nabl", store=True)

    @api.depends('phosphorus_average','eln_ref','grade')
    def _compute_phosphorus_average_nabl(self):
        # remove this first
        self.phosphorus_average_nabl = 'fail'
        
        for record in self:
            record.phosphorus_average_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62478ye-ba0b-4e64-84d1-e3b23ftyy147r')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62478ye-ba0b-4e64-84d1-e3b23ftyy147r')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.phosphorus_average - record.phosphorus_average*mu_value
            upper = record.phosphorus_average + record.phosphorus_average*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.phosphorus_average_nabl = 'pass'
                break
            else:
                record.phosphorus_average_nabl = 'fail'

    
    # SODIUM
    
    sodium_name = fields.Char("Name",default="Sodium")
    sodium_visible = fields.Boolean("pH",compute="_compute_visible")
    
    sodium_1 = fields.Float("Observation")
    sodium_2 = fields.Float("Observation")
    sodium_3 = fields.Float("Observation")
    sodium_4 = fields.Float("Observation")
    sodium_5 = fields.Float("Observation")
    sodium_average = fields.Float("Average",compute="_compute_sodium_average")

    @api.depends("sodium_1",'sodium_2','sodium_3','sodium_4','sodium_5')
    def _compute_sodium_average(self):
        for record in self:
            record.sodium_average = (record.sodium_1 + record.sodium_2 + record.sodium_3 + record.sodium_4 + record.sodium_5)/5

    sodium_average_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_sodium_average_conformity", store=True)

    @api.depends('sodium_average','eln_ref','grade')
    def _compute_sodium_average_conformity(self):
            # remove this first when making changes
            self.sodium_average_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.sodium_average_conformity = 'na'
                    continue

                record.sodium_average_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','987bgrt-ba0b-4e64-84d1-e3b23f32147tr')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','987bgrt-ba0b-4e64-84d1-e3b23f32147tr')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.sodium_average - record.sodium_average*mu_value
                        upper = record.sodium_average + record.sodium_average*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.sodium_average_conformity = 'pass'
                            break
                        else:
                            record.sodium_average_conformity = 'fail'

    sodium_average_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_sodium_average_nabl", store=True)

    @api.depends('sodium_average','eln_ref','grade')
    def _compute_sodium_average_nabl(self):
        # remove this first
        self.sodium_average_nabl = 'fail'
        
        for record in self:
            record.sodium_average_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','987bgrt-ba0b-4e64-84d1-e3b23f32147tr')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','987bgrt-ba0b-4e64-84d1-e3b23f32147tr')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.sodium_average - record.sodium_average*mu_value
            upper = record.sodium_average + record.sodium_average*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.sodium_average_nabl = 'pass'
                break
            else:
                record.sodium_average_nabl = 'fail'

    # potassium
    potassium_name = fields.Char("Name",default="Potassium")
    potassium_visible = fields.Boolean("pH",compute="_compute_visible")
    
    potassium_1 = fields.Float("Observation")
    potassium_2 = fields.Float("Observation")
    potassium_3 = fields.Float("Observation")
    potassium_4 = fields.Float("Observation")
    potassium_5 = fields.Float("Observation")
    potassium_average = fields.Float("Average",compute="_compute_potassium_average")

    @api.depends("potassium_1",'potassium_2','potassium_3','potassium_4','potassium_5')
    def _compute_potassium_average(self):
        for record in self:
            record.potassium_average = (record.potassium_1 + record.potassium_2 + record.potassium_3 + record.potassium_4 + record.potassium_5)/5

    potassium_average_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_potassium_average_conformity", store=True)

    @api.depends('potassium_average','eln_ref','grade')
    def _compute_potassium_average_conformity(self):
            # remove this first when making changes
            self.potassium_average_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.potassium_average_conformity = 'na'
                    continue

                record.potassium_average_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6587yur-ba0b-4e64-84d1-e3b23f32rtefg')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6587yur-ba0b-4e64-84d1-e3b23f32rtefg')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.potassium_average - record.potassium_average*mu_value
                        upper = record.potassium_average + record.potassium_average*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.potassium_average_conformity = 'pass'
                            break
                        else:
                            record.potassium_average_conformity = 'fail'

    potassium_average_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_potassium_average_nabl", store=True)

    @api.depends('potassium_average','eln_ref','grade')
    def _compute_potassium_average_nabl(self):
        # remove this first
        self.potassium_average_nabl = 'fail'
        
        for record in self:
            record.potassium_average_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6587yur-ba0b-4e64-84d1-e3b23f32rtefg')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6587yur-ba0b-4e64-84d1-e3b23f32rtefg')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.potassium_average - record.potassium_average*mu_value
            upper = record.potassium_average + record.potassium_average*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.potassium_average_nabl = 'pass'
                break
            else:
                record.potassium_average_nabl = 'fail'

    





    @api.depends('sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.conductivity_visible = False
            
            record.ph_visible = False
            record.dissolved_solid_visible = False
            record.turbidity_visible = False
            record.chloride_visible = False
            record.hardness_visible = False
            record.alkalinity_visible = False
            record.calcium_visible = False
            record.magnesium_visible = False
            record.sulphate_visible = False
            record.nitrate_visible = False
            record.silica_visible = False
            record.phosphorus_visible = False
            record.sodium_visible = False
            record.potassium_visible = False
          

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '62tyubg0d-645d-4794-a0fd-3daa01247jht':
                    record.ph_visible = True
                if sample.internal_id == 'j4578m-ba0b-4e64-84d1-e3b23ftyuio1':
                    record.conductivity_visible = True
                if sample.internal_id == 'j3214t-ba0b-4e64-84d1-e3b23ftyrty12':
                    record.dissolved_solid_visible = True

                if sample.internal_id == '654783-ba0b-4e64-84d1-e3b23ftty543':
                    record.turbidity_visible = True

                if sample.internal_id == '32014y-ba0b-4e64-84d1-e3b23ft301yr':
                    record.chloride_visible = True

                if sample.internal_id == '30124t-ba0b-4e64-84d1-e3b23ft0147t':
                    record.hardness_visible = True

                if sample.internal_id == '012478-ba0b-4e64-84d1-e3b23f30147g':
                    record.alkalinity_visible = True

                if sample.internal_id == '654780-ba0b-4e64-84d1-e3b23f33214ty':
                    record.calcium_visible = True

                if sample.internal_id == '32147t-ba0b-4e64-84d1-e3b23f33treb2':
                    record.magnesium_visible = True

                if sample.internal_id == '547uyt-ba0b-4e64-84d1-e3b23ftyrtf51':
                    record.sulphate_visible = True

                if sample.internal_id == '6547hy-ba0b-4e64-84d1-e3b23fty471lk':
                    record.nitrate_visible = True

                if sample.internal_id == '75847y-ba0b-4e64-84d1-e3b23ftyytr56':
                    record.silica_visible = True

                if sample.internal_id == '62478ye-ba0b-4e64-84d1-e3b23ftyy147r':
                    record.phosphorus_visible = True

                if sample.internal_id == '987bgrt-ba0b-4e64-84d1-e3b23f32147tr':
                    record.sodium_visible = True

                if sample.internal_id == '6587yur-ba0b-4e64-84d1-e3b23f32rtefg':
                    record.potassium_visible = True

            



    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

            
            
            # Water Absorbtion
            if result.parameter.internal_id == '62tyubg0d-645d-4794-a0fd-3daa01247jht':
                result.result_char = round(self.ph_average,2)
                result.calculated = True
                if self.ph_average_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'j4578m-ba0b-4e64-84d1-e3b23ftyuio1':
                result.result_char = round(self.conductivity_average,2)
                result.calculated = True
                if self.conductivity_average_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'j3214t-ba0b-4e64-84d1-e3b23ftyrty12':
                result.result_char = round(self.avg_dissolved_solid,2)
                result.calculated = True
                if self.avg_dissolved_solid_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            
            if result.parameter.internal_id == '654783-ba0b-4e64-84d1-e3b23ftty543':
                result.result_char = round(self.turbidity_average,2)
                result.calculated = True
                if self.turbidity_average_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '32014y-ba0b-4e64-84d1-e3b23ft301yr':
                result.result_char = round(self.avg_chloride,2)
                result.calculated = True
                if self.avg_chloride_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '30124t-ba0b-4e64-84d1-e3b23ft0147t':
                result.result_char = round(self.avg_hardness,2)
                result.calculated = True
                if self.avg_hardness_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '012478-ba0b-4e64-84d1-e3b23f30147g':
                result.result_char = round(self.avg_alkalinity,2)
                result.calculated = True
                if self.avg_alkalinity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '654780-ba0b-4e64-84d1-e3b23f33214ty':
                result.result_char = round(self.avg_calcium,2)
                result.calculated = True
                if self.avg_calcium_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '32147t-ba0b-4e64-84d1-e3b23f33treb2':
                result.result_char = round(self.avg_magnesium,2)
                result.calculated = True
                if self.avg_magnesium_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '547uyt-ba0b-4e64-84d1-e3b23ftyrtf51':
                result.result_char = round(self.sulphate_average,2)
                result.calculated = True
                if self.sulphate_average_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '6547hy-ba0b-4e64-84d1-e3b23fty471lk':
                result.result_char = round(self.nitrate_average,2)
                result.calculated = True
                if self.nitrate_average_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '75847y-ba0b-4e64-84d1-e3b23ftyytr56':
                result.result_char = round(self.silica_average,2)
                result.calculated = True
                if self.silica_average_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '62478ye-ba0b-4e64-84d1-e3b23ftyy147r':
                result.result_char = round(self.phosphorus_average,2)
                result.calculated = True
                if self.phosphorus_average_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '987bgrt-ba0b-4e64-84d1-e3b23f32147tr':
                result.result_char = round(self.sodium_average,2)
                result.calculated = True
                if self.sodium_average_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '6587yur-ba0b-4e64-84d1-e3b23f32rtefg':
                result.result_char = round(self.potassium_average,2)
                result.calculated = True
                if self.potassium_average_nabl == 'pass':
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
        record = super(ChemicalDrinkingWater, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


        
    def get_all_fields(self):
        record = self.env['chemical.drinking.water'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    


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

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id








class ChemFineNotes(models.Model):
    _name = "chem.drinking.water.notes"

    parent_id = fields.Many2one('chemical.drinking.water',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
    