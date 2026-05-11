from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class ChemicalWasteWater(models.Model):
    _name = "chemical.waste.water"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Drinking Water")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    notes_id = fields.One2many('chem.waste.water.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(ChemicalWasteWater, self).default_get(fields)

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
    
    ph_1_percent_a = fields.Float("pH")
    ph_1_percent_b = fields.Float("pH")
    ph_1_percent_c = fields.Float("pH")
    ph_1_percent_d = fields.Float("pH")
    ph_1_percent_e = fields.Float("pH")
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
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62147hjy-645d-4794-a0fd-3daa0124rtyu')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62147hjy-645d-4794-a0fd-3daa0124rtyu')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62147hjy-645d-4794-a0fd-3daa0124rtyu')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62147hjy-645d-4794-a0fd-3daa0124rtyu')]).parameter_table
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

    #   Total Suspended Solids (mg/l)
    
    suspended_solids_name = fields.Char("Name",default="Total Suspended Solids")
    suspended_solids_visible = fields.Boolean("Total Suspended Solids",compute="_compute_visible")

    suspended_solids_sample_taken1 = fields.Float(string="Sample Taken")
    suspended_solids_sample_taken2 = fields.Float(string="Sample Taken")
    suspended_solids_sample_taken3 = fields.Float(string="Sample Taken")
    suspended_solids_sample_taken4 = fields.Float(string="Sample Taken")
    suspended_solids_sample_taken5 = fields.Float(string="Sample Taken")

    suspended_solids_initial_wt1 = fields.Float(string="Initial wt. Gooch Crucible")
    suspended_solids_initial_wt2 = fields.Float(string="Initial wt. Gooch Crucible")
    suspended_solids_initial_wt3 = fields.Float(string="Initial wt. Gooch Crucible")
    suspended_solids_initial_wt4 = fields.Float(string="Initial wt. Gooch Crucible")
    suspended_solids_initial_wt5 = fields.Float(string="Initial wt. Gooch Crucible")

    suspended_solids_final_wt_1 = fields.Float(string="Final wt. of Gooch Crucible")
    suspended_solids_final_wt_2 = fields.Float(string="Final wt. of Gooch Crucible")
    suspended_solids_final_wt_3 = fields.Float(string="Final wt. of Gooch Crucible")
    suspended_solids_final_wt_4 = fields.Float(string="Final wt. of Gooch Crucible")
    suspended_solids_final_wt_5 = fields.Float(string="Final wt. of Gooch Crucible")

    suspended_solids_mass_1 = fields.Float(string="Mass in mg of Non filterable residue ( M )")
    suspended_solids_mass_2 = fields.Float(string="Mass in mg of Non filterable residue ( M )")
    suspended_solids_mass_3 = fields.Float(string="Mass in mg of Non filterable residue ( M )")
    suspended_solids_mass_4 = fields.Float(string="Mass in mg of Non filterable residue ( M )")
    suspended_solids_mass_5 = fields.Float(string="Mass in mg of Non filterable residue ( M )")

    suspended_solids_filterable1 = fields.Float(string="Non Filterable residue ( TSS ), in mg/l", compute="_compute_tss", store=True)
    suspended_solids_filterable2 = fields.Float(string="Non Filterable residue ( TSS ), in mg/l", compute="_compute_tss", store=True)
    suspended_solids_filterable3 = fields.Float(string="Non Filterable residue ( TSS ), in mg/l", compute="_compute_tss", store=True)
    suspended_solids_filterable4 = fields.Float(string="Non Filterable residue ( TSS ), in mg/l", compute="_compute_tss", store=True)
    suspended_solids_filterable5 = fields.Float(string="Non Filterable residue ( TSS ), in mg/l", compute="_compute_tss", store=True)

    avg_suspended_solids = fields.Float(string="Average Suspended Solids (mg/l)",compute="_compute_avg_suspended_solids",store=True)

    @api.depends(
    'suspended_solids_filterable1',
    'suspended_solids_filterable2',
    'suspended_solids_filterable3',
    'suspended_solids_filterable4',
    'suspended_solids_filterable5'
    )
    def _compute_avg_suspended_solids(self):
        for rec in self:
            rec.avg_suspended_solids = (
                rec.suspended_solids_filterable1 +
                rec.suspended_solids_filterable2 +
                rec.suspended_solids_filterable3 +
                rec.suspended_solids_filterable4 +
                rec.suspended_solids_filterable5
            ) / 5

    @api.depends(
    'suspended_solids_sample_taken1','suspended_solids_mass_1',
    'suspended_solids_sample_taken2','suspended_solids_mass_2',
    'suspended_solids_sample_taken3','suspended_solids_mass_3',
    'suspended_solids_sample_taken4','suspended_solids_mass_4',
    'suspended_solids_sample_taken5','suspended_solids_mass_5',
    )
    def _compute_tss(self):
        for rec in self:

            rec.suspended_solids_filterable1 = (rec.suspended_solids_mass_1 * 1000 / rec.suspended_solids_sample_taken1) if rec.suspended_solids_sample_taken1 else 0.0

            rec.suspended_solids_filterable2 = (rec.suspended_solids_mass_2 * 1000 / rec.suspended_solids_sample_taken2) if rec.suspended_solids_sample_taken2 else 0.0

            rec.suspended_solids_filterable3 = (rec.suspended_solids_mass_3 * 1000 / rec.suspended_solids_sample_taken3) if rec.suspended_solids_sample_taken3 else 0.0

            rec.suspended_solids_filterable4 = (rec.suspended_solids_mass_4 * 1000 / rec.suspended_solids_sample_taken4) if rec.suspended_solids_sample_taken4 else 0.0

            rec.suspended_solids_filterable5 = (rec.suspended_solids_mass_5 * 1000 / rec.suspended_solids_sample_taken5) if rec.suspended_solids_sample_taken5 else 0.0


    avg_suspended_solids_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_suspended_solids_conformity", store=True)

    @api.depends('avg_suspended_solids','eln_ref','grade')
    def _compute_avg_suspended_solids_conformity(self):
            # remove this first when making changes
            self.avg_suspended_solids_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_suspended_solids_conformity = 'na'
                    continue

                record.avg_suspended_solids_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','325478ht-645d-4794-a0fd-3daa012410tr')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','325478ht-645d-4794-a0fd-3daa012410tr')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_suspended_solids - record.avg_suspended_solids*mu_value
                        upper = record.avg_suspended_solids + record.avg_suspended_solids*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_suspended_solids_conformity = 'pass'
                            break
                        else:
                            record.avg_suspended_solids_conformity = 'fail'

    avg_suspended_solids_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_suspended_solids_nabl", store=True)

    @api.depends('avg_suspended_solids','eln_ref','grade')
    def _compute_avg_suspended_solids_nabl(self):
        # remove this first
        self.avg_suspended_solids_nabl = 'fail'
        
        for record in self:
            record.avg_suspended_solids_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','325478ht-645d-4794-a0fd-3daa012410tr')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','325478ht-645d-4794-a0fd-3daa012410tr')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_suspended_solids - record.avg_suspended_solids*mu_value
            upper = record.avg_suspended_solids + record.avg_suspended_solids*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_suspended_solids_nabl = 'pass'
                break
            else:
                record.avg_suspended_solids_nabl = 'fail'

    # CHEMICAL OXYGEN DEMAND
    oxygen_demand_name = fields.Char("Name",default="Chemical Oxygen Demand")
    oxygen_demand_visible = fields.Boolean("Oxygen Demand",compute="_compute_visible")

    oxygen_demand_sample_taken1 = fields.Float(string="Volume of sample taken for testing, in ml.(V)")
    oxygen_demand_sample_taken2 = fields.Float(string="Volume of sample taken for testing, in ml.(V)")
    oxygen_demand_sample_taken3 = fields.Float(string="Volume of sample taken for testing, in ml.(V)")
    oxygen_demand_sample_taken4 = fields.Float(string="Volume of sample taken for testing, in ml.(V)")
    oxygen_demand_sample_taken5 = fields.Float(string="Volume of sample taken for testing, in ml.(V)")

    oxygen_demand_titrationv1_1 = fields.Float(string="Volume of FAS. required far titration against the blank, in ml (V1)")
    oxygen_demand_titrationv1_2 = fields.Float(string="Volume of FAS. required far titration against the blank, in ml (V1)")
    oxygen_demand_titrationv1_3 = fields.Float(string="Volume of FAS. required far titration against the blank, in ml (V1)")
    oxygen_demand_titrationv1_4 = fields.Float(string="Volume of FAS. required far titration against the blank, in ml (V1)")
    oxygen_demand_titrationv1_5 = fields.Float(string="Volume of FAS. required far titration against the blank, in ml (V1)")

    oxygen_demand_titrationv2_1 = fields.Float(string="Volume of FAS. required for titration against the sample, in ml ( V2)")
    oxygen_demand_titrationv2_2 = fields.Float(string="Volume of FAS. required for titration against the sample, in ml ( V2)")
    oxygen_demand_titrationv2_3 = fields.Float(string="Volume of FAS. required for titration against the sample, in ml ( V2)")
    oxygen_demand_titrationv2_4 = fields.Float(string="Volume of FAS. required for titration against the sample, in ml ( V2)")
    oxygen_demand_titrationv2_5 = fields.Float(string="Volume of FAS. required for titration against the sample, in ml ( V2)")

    oxygen_demand_normality_1 = fields.Float(string="Normality of FAS")
    oxygen_demand_normality_2 = fields.Float(string="Normality of FAS")
    oxygen_demand_normality_3 = fields.Float(string="Normality of FAS")
    oxygen_demand_normality_4 = fields.Float(string="Normality of FAS")
    oxygen_demand_normality_5 = fields.Float(string="Normality of FAS")

    oxygen_demand_cod1 = fields.Float(string="Result COD mg/l", compute="_compute_cod", store=True)
    oxygen_demand_cod2 = fields.Float(string="Result COD mg/l", compute="_compute_cod", store=True)
    oxygen_demand_cod3 = fields.Float(string="Result COD mg/l", compute="_compute_cod", store=True)
    oxygen_demand_cod4 = fields.Float(string="Result COD mg/l", compute="_compute_cod", store=True)
    oxygen_demand_cod5 = fields.Float(string="Result COD mg/l", compute="_compute_cod", store=True)

    avg_oxygen_demand = fields.Float(string="Average Oxygen Demand (mg/l)",compute="_compute_avg_cod",store=True)


    @api.depends(
    'oxygen_demand_sample_taken1','oxygen_demand_titrationv1_1','oxygen_demand_titrationv2_1','oxygen_demand_normality_1',
    'oxygen_demand_sample_taken2','oxygen_demand_titrationv1_2','oxygen_demand_titrationv2_2','oxygen_demand_normality_2',
    'oxygen_demand_sample_taken3','oxygen_demand_titrationv1_3','oxygen_demand_titrationv2_3','oxygen_demand_normality_3',
    'oxygen_demand_sample_taken4','oxygen_demand_titrationv1_4','oxygen_demand_titrationv2_4','oxygen_demand_normality_4',
    'oxygen_demand_sample_taken5','oxygen_demand_titrationv1_5','oxygen_demand_titrationv2_5','oxygen_demand_normality_5',
    )
    def _compute_cod(self):
        for rec in self:

            rec.oxygen_demand_cod1 = (
                (rec.oxygen_demand_titrationv1_1 - rec.oxygen_demand_titrationv2_1)
                * rec.oxygen_demand_normality_1 * 8000
                / rec.oxygen_demand_sample_taken1
            ) if rec.oxygen_demand_sample_taken1 else 0.0

            rec.oxygen_demand_cod2 = (
                (rec.oxygen_demand_titrationv1_2 - rec.oxygen_demand_titrationv2_2)
                * rec.oxygen_demand_normality_2 * 8000
                / rec.oxygen_demand_sample_taken2
            ) if rec.oxygen_demand_sample_taken2 else 0.0

            rec.oxygen_demand_cod3 = (
                (rec.oxygen_demand_titrationv1_3 - rec.oxygen_demand_titrationv2_3)
                * rec.oxygen_demand_normality_3 * 8000
                / rec.oxygen_demand_sample_taken3
            ) if rec.oxygen_demand_sample_taken3 else 0.0

            rec.oxygen_demand_cod4 = (
                (rec.oxygen_demand_titrationv1_4 - rec.oxygen_demand_titrationv2_4)
                * rec.oxygen_demand_normality_4 * 8000
                / rec.oxygen_demand_sample_taken4
            ) if rec.oxygen_demand_sample_taken4 else 0.0

            rec.oxygen_demand_cod5 = (
                (rec.oxygen_demand_titrationv1_5 - rec.oxygen_demand_titrationv2_5)
                * rec.oxygen_demand_normality_5 * 8000
                / rec.oxygen_demand_sample_taken5
            ) if rec.oxygen_demand_sample_taken5 else 0.0

    @api.depends(
    'oxygen_demand_cod1',
    'oxygen_demand_cod2',
    'oxygen_demand_cod3',
    'oxygen_demand_cod4',
    'oxygen_demand_cod5'
    )
    def _compute_avg_cod(self):
        for rec in self:
            rec.avg_oxygen_demand = (
                rec.oxygen_demand_cod1 +
                rec.oxygen_demand_cod2 +
                rec.oxygen_demand_cod3 +
                rec.oxygen_demand_cod4 +
                rec.oxygen_demand_cod5
            ) / 5


    avg_oxygen_demand_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_oxygen_demand_conformity", store=True)

    @api.depends('avg_oxygen_demand','eln_ref','grade')
    def _compute_avg_oxygen_demand_conformity(self):
            # remove this first when making changes
            self.avg_oxygen_demand_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_oxygen_demand_conformity = 'na'
                    continue

                record.avg_oxygen_demand_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98745jyt-645d-4794-a0fd-3daa0123214hyt')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98745jyt-645d-4794-a0fd-3daa0123214hyt')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_oxygen_demand - record.avg_oxygen_demand*mu_value
                        upper = record.avg_oxygen_demand + record.avg_oxygen_demand*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_oxygen_demand_conformity = 'pass'
                            break
                        else:
                            record.avg_oxygen_demand_conformity = 'fail'

    avg_oxygen_demand_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_oxygen_demand_nabl", store=True)

    @api.depends('avg_oxygen_demand','eln_ref','grade')
    def _compute_avg_oxygen_demand_nabl(self):
        # remove this first
        self.avg_oxygen_demand_nabl = 'fail'
        
        for record in self:
            record.avg_oxygen_demand_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98745jyt-645d-4794-a0fd-3daa0123214hyt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98745jyt-645d-4794-a0fd-3daa0123214hyt')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_oxygen_demand - record.avg_oxygen_demand*mu_value
            upper = record.avg_oxygen_demand + record.avg_oxygen_demand*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_oxygen_demand_nabl = 'pass'
                break
            else:
                record.avg_oxygen_demand_nabl = 'fail'


    # CHEMICAL OXYGEN DEMAND
    biooxygen_demand_name = fields.Char("Name",default="Biochemical Oxygen Demand")
    biooxygen_demand_visible = fields.Boolean("Biochemical Oxygen Demand",compute="_compute_visible")

    biooxygen_demand_sample_valuem1 = fields.Float(string="Percentage dilution of sample (sample volume in ml/10). (P)")
    biooxygen_demand_sample_valuem2 = fields.Float(string="Percentage dilution of sample (sample volume in ml/10). (P)")
    biooxygen_demand_sample_valuem3 = fields.Float(string="Percentage dilution of sample (sample volume in ml/10). (P)")
    biooxygen_demand_sample_valuem4 = fields.Float(string="Percentage dilution of sample (sample volume in ml/10). (P)")
    biooxygen_demand_sample_valuem5 = fields.Float(string="Percentage dilution of sample (sample volume in ml/10). (P)")

    biooxygen_demand_initial_do_1 = fields.Float(string="Initial DO of sample in mg/l, (D1)")
    biooxygen_demand_initial_do_2 = fields.Float(string="Initial DO of sample in mg/l, (D1)")
    biooxygen_demand_initial_do_3 = fields.Float(string="Initial DO of sample in mg/l, (D1)")
    biooxygen_demand_initial_do_4 = fields.Float(string="Initial DO of sample in mg/l, (D1)")
    biooxygen_demand_initial_do_5 = fields.Float(string="Initial DO of sample in mg/l, (D1)")

    biooxygen_demand_after_do_1 = fields.Float(string="DO of sample after incubation in mg/l, (D2)")
    biooxygen_demand_after_do_2 = fields.Float(string="DO of sample after incubation in mg/l, (D2)")
    biooxygen_demand_after_do_3 = fields.Float(string="DO of sample after incubation in mg/l, (D2)")
    biooxygen_demand_after_do_4 = fields.Float(string="DO of sample after incubation in mg/l, (D2)")
    biooxygen_demand_after_do_5 = fields.Float(string="DO of sample after incubation in mg/l, (D2)")

    biooxygen_demand_bod_1 = fields.Float(string="Result BOD mg/l", compute="_compute_bod", store=True)
    biooxygen_demand_bod_2 = fields.Float(string="Result BOD mg/l", compute="_compute_bod", store=True)
    biooxygen_demand_bod_3 = fields.Float(string="Result BOD mg/l", compute="_compute_bod", store=True)
    biooxygen_demand_bod_4 = fields.Float(string="Result BOD mg/l", compute="_compute_bod", store=True)
    biooxygen_demand_bod_5 = fields.Float(string="Result BOD mg/l", compute="_compute_bod", store=True)

    avg_biooxygen_demand = fields.Float(string="Average Biochemical Oxygen Demand (mg/l)",compute="_compute_avg_bod",store=True)

    @api.depends(
    'biooxygen_demand_bod_1',
    'biooxygen_demand_bod_2',
    'biooxygen_demand_bod_3',
    'biooxygen_demand_bod_4',
    'biooxygen_demand_bod_5'
    )
    def _compute_avg_bod(self):
        for rec in self:

            rec.avg_biooxygen_demand = (
                rec.biooxygen_demand_bod_1 +
                rec.biooxygen_demand_bod_2 +
                rec.biooxygen_demand_bod_3 +
                rec.biooxygen_demand_bod_4 +
                rec.biooxygen_demand_bod_5
            ) / 5


    @api.depends(
        'biooxygen_demand_sample_valuem1','biooxygen_demand_initial_do_1','biooxygen_demand_after_do_1',
        'biooxygen_demand_sample_valuem2','biooxygen_demand_initial_do_2','biooxygen_demand_after_do_2',
        'biooxygen_demand_sample_valuem3','biooxygen_demand_initial_do_3','biooxygen_demand_after_do_3',
        'biooxygen_demand_sample_valuem4','biooxygen_demand_initial_do_4','biooxygen_demand_after_do_4',
        'biooxygen_demand_sample_valuem5','biooxygen_demand_initial_do_5','biooxygen_demand_after_do_5',
    )
    def _compute_bod(self):
        for rec in self:

            rec.biooxygen_demand_bod_1 = (rec.biooxygen_demand_initial_do_1 - rec.biooxygen_demand_after_do_1) * 1000 / rec.biooxygen_demand_sample_valuem1 if rec.biooxygen_demand_sample_valuem1 else 0.0

            rec.biooxygen_demand_bod_2 = (rec.biooxygen_demand_initial_do_2 - rec.biooxygen_demand_after_do_2) * 1000 / rec.biooxygen_demand_sample_valuem2 if rec.biooxygen_demand_sample_valuem2 else 0.0

            rec.biooxygen_demand_bod_3 = (rec.biooxygen_demand_initial_do_3 - rec.biooxygen_demand_after_do_3) * 1000 / rec.biooxygen_demand_sample_valuem3 if rec.biooxygen_demand_sample_valuem3 else 0.0

            rec.biooxygen_demand_bod_4 = (rec.biooxygen_demand_initial_do_4 - rec.biooxygen_demand_after_do_4) * 1000 / rec.biooxygen_demand_sample_valuem4 if rec.biooxygen_demand_sample_valuem4 else 0.0

            rec.biooxygen_demand_bod_5 = (rec.biooxygen_demand_initial_do_5 - rec.biooxygen_demand_after_do_5) * 1000 / rec.biooxygen_demand_sample_valuem5 if rec.biooxygen_demand_sample_valuem5 else 0.0


    avg_biooxygen_demand_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_biooxygen_demand_conformity", store=True)

    @api.depends('avg_biooxygen_demand','eln_ref','grade')
    def _compute_avg_biooxygen_demand_conformity(self):
            # remove this first when making changes
            self.avg_biooxygen_demand_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_biooxygen_demand_conformity = 'na'
                    continue

                record.avg_biooxygen_demand_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65478iuy-645d-4794-a0fd-3daa01232ygtr1')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65478iuy-645d-4794-a0fd-3daa01232ygtr1')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_biooxygen_demand - record.avg_biooxygen_demand*mu_value
                        upper = record.avg_biooxygen_demand + record.avg_biooxygen_demand*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_biooxygen_demand_conformity = 'pass'
                            break
                        else:
                            record.avg_biooxygen_demand_conformity = 'fail'

    avg_biooxygen_demand_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_biooxygen_demand_nabl", store=True)

    @api.depends('avg_biooxygen_demand','eln_ref','grade')
    def _compute_avg_biooxygen_demand_nabl(self):
        # remove this first
        self.avg_biooxygen_demand_nabl = 'fail'
        
        for record in self:
            record.avg_biooxygen_demand_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65478iuy-645d-4794-a0fd-3daa01232ygtr1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65478iuy-645d-4794-a0fd-3daa01232ygtr1')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_biooxygen_demand - record.avg_biooxygen_demand*mu_value
            upper = record.avg_biooxygen_demand + record.avg_biooxygen_demand*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_biooxygen_demand_nabl = 'pass'
                break
            else:
                record.avg_biooxygen_demand_nabl = 'fail'
  
    # OIL & GREASE
    
    grease_name = fields.Char("Name",default="OIL & GREASE")
    grease_visible = fields.Boolean("OIL & GREASE",compute="_compute_visible")

    grease_sample_taken1 = fields.Float(string="volume, in ml, of the sample taken (V)")
    grease_sample_taken2 = fields.Float(string="volume, in ml, of the sample taken (V)")
    grease_sample_taken3 = fields.Float(string="volume, in ml, of the sample taken (V)")
    grease_sample_taken4 = fields.Float(string="volume, in ml, of the sample taken (V)")
    grease_sample_taken5 = fields.Float(string="volume, in ml, of the sample taken (V)")

    grease_initial_dish_1 = fields.Float(string="Initial wt. Evaporating Dish gm")
    grease_initial_dish_2 = fields.Float(string="Initial wt. Evaporating Dish gm")
    grease_initial_dish_3 = fields.Float(string="Initial wt. Evaporating Dish gm")
    grease_initial_dish_4 = fields.Float(string="Initial wt. Evaporating Dish gm")
    grease_initial_dish_5 = fields.Float(string="Initial wt. Evaporating Dish gm")

    grease_final_dish_1 = fields.Float(string="Final wt. of Evaporating Dish gm")
    grease_final_dish_2 = fields.Float(string="Final wt. of Evaporating Dish gm")
    grease_final_dish_3 = fields.Float(string="Final wt. of Evaporating Dish gm")
    grease_final_dish_4 = fields.Float(string="Final wt. of Evaporating Dish gm")
    grease_final_dish_5 = fields.Float(string="Final wt. of Evaporating Dish gm")

    grease_normality_1 = fields.Float(string="Mass, in mg, of the residue (M)")
    grease_normality_2 = fields.Float(string="Mass, in mg, of the residue (M)")
    grease_normality_3 = fields.Float(string="Mass, in mg, of the residue (M)")
    grease_normality_4 = fields.Float(string="Mass, in mg, of the residue (M)")
    grease_normality_5 = fields.Float(string="Mass, in mg, of the residue (M)")

    grease_oil1 = fields.Float(string="Result Oil and grease mg/l",  compute="_compute_grease", store=True)
    grease_oil2 = fields.Float(string="Result Oil and grease mg/l",  compute="_compute_grease", store=True)
    grease_oil3 = fields.Float(string="Result Oil and grease mg/l",  compute="_compute_grease", store=True)
    grease_oil4 = fields.Float(string="Result Oil and grease mg/l",  compute="_compute_grease", store=True)
    grease_oil5 = fields.Float(string="Result Oil and grease mg/l",  compute="_compute_grease", store=True)

    avg_grease = fields.Float(string="Average Oil and grease (mg/l)",compute="_compute_avg_grease",store=True)

    @api.depends(
    'grease_oil1',
    'grease_oil2',
    'grease_oil3',
    'grease_oil4',
    'grease_oil5'
    )
    def _compute_avg_grease(self):
        for rec in self:

            rec.avg_grease = (
                rec.grease_oil1 +
                rec.grease_oil2 +
                rec.grease_oil3 +
                rec.grease_oil4 +
                rec.grease_oil5
            ) / 5


    @api.depends(
    'grease_sample_taken1','grease_normality_1',
    'grease_sample_taken2','grease_normality_2',
    'grease_sample_taken3','grease_normality_3',
    'grease_sample_taken4','grease_normality_4',
    'grease_sample_taken5','grease_normality_5',
    )
    def _compute_grease(self):
        for rec in self:

            rec.grease_oil1 = (1000 * rec.grease_normality_1 / rec.grease_sample_taken1) if rec.grease_sample_taken1 else 0.0

            rec.grease_oil2 = (1000 * rec.grease_normality_2 / rec.grease_sample_taken2) if rec.grease_sample_taken2 else 0.0

            rec.grease_oil3 = (1000 * rec.grease_normality_3 / rec.grease_sample_taken3) if rec.grease_sample_taken3 else 0.0

            rec.grease_oil4 = (1000 * rec.grease_normality_4 / rec.grease_sample_taken4) if rec.grease_sample_taken4 else 0.0

            rec.grease_oil5 = (1000 * rec.grease_normality_5 / rec.grease_sample_taken5) if rec.grease_sample_taken5 else 0.0

    avg_grease_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_grease_conformity", store=True)

    @api.depends('avg_grease','eln_ref','grade')
    def _compute_avg_grease_conformity(self):
            # remove this first when making changes
            self.avg_grease_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_grease_conformity = 'na'
                    continue

                record.avg_grease_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36547bbn-645d-4794-a0fd-3daa01232yertv')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36547bbn-645d-4794-a0fd-3daa01232yertv')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_grease - record.avg_grease*mu_value
                        upper = record.avg_grease + record.avg_grease*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_grease_conformity = 'pass'
                            break
                        else:
                            record.avg_grease_conformity = 'fail'

    avg_grease_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_grease_nabl", store=True)

    @api.depends('avg_grease','eln_ref','grade')
    def _compute_avg_grease_nabl(self):
        # remove this first
        self.avg_grease_nabl = 'fail'
        
        for record in self:
            record.avg_grease_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36547bbn-645d-4794-a0fd-3daa01232yertv')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36547bbn-645d-4794-a0fd-3daa01232yertv')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_grease - record.avg_grease*mu_value
            upper = record.avg_grease + record.avg_grease*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_grease_nabl = 'pass'
                break
            else:
                record.avg_grease_nabl = 'fail'

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
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32147h-ba0b-4e64-84d1-e3b23f3ty5610')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32147h-ba0b-4e64-84d1-e3b23f3ty5610')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32147h-ba0b-4e64-84d1-e3b23f3ty5610')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32147h-ba0b-4e64-84d1-e3b23f3ty5610')]).parameter_table
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

            rec.chloride1 = ((rec.chloride_nitratev1_1 - rec.chloride_nitratev2_1) * rec.chloride_normality1 * 5.45 * 10000 / rec.chloride_sample_taken1) if rec.chloride_sample_taken1 else 0.0

            rec.chloride2 = ((rec.chloride_nitratev1_2 - rec.chloride_nitratev2_2) * rec.chloride_normality2 * 5.45 * 1000 / rec.chloride_sample_taken2) if rec.chloride_sample_taken2 else 0.0

            rec.chloride3 = ((rec.chloride_nitratev1_3 - rec.chloride_nitratev2_3) * rec.chloride_normality3 * 5.45 * 1000/ rec.chloride_sample_taken3) if rec.chloride_sample_taken3 else 0.0

            rec.chloride4 = ((rec.chloride_nitratev1_4 - rec.chloride_nitratev2_4) * rec.chloride_normality4 * 5.45 * 1000/ rec.chloride_sample_taken4) if rec.chloride_sample_taken4 else 0.0

            rec.chloride5 = ((rec.chloride_nitratev1_5 - rec.chloride_nitratev2_5) * rec.chloride_normality5 * 5.45 * 1000/ rec.chloride_sample_taken5) if rec.chloride_sample_taken5 else 0.0

        
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
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2211bv-ba0b-4e64-84d1-e3b23ft301yr')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2211bv-ba0b-4e64-84d1-e3b23ft301yr')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2211bv-ba0b-4e64-84d1-e3b23ft301yr')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2211bv-ba0b-4e64-84d1-e3b23ft301yr')]).parameter_table
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
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','777bbbf-ba0b-4e64-84d1-e3b23f32147tr')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','777bbbf-ba0b-4e64-84d1-e3b23f32147tr')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','777bbbf-ba0b-4e64-84d1-e3b23f32147tr')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','777bbbf-ba0b-4e64-84d1-e3b23f32147tr')]).parameter_table
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
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','333yyy-ba0b-4e64-84d1-e3b23f32rtefg')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','333yyy-ba0b-4e64-84d1-e3b23f32rtefg')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','333yyy-ba0b-4e64-84d1-e3b23f32rtefg')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','333yyy-ba0b-4e64-84d1-e3b23f32rtefg')]).parameter_table
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
            record.ph_visible = False
            record.suspended_solids_visible = False
            record.oxygen_demand_visible = False
            record.biooxygen_demand_visible = False
            record.grease_visible = False
            record.calcium_visible = False
            record.chloride_visible = False
            record.sodium_visible = False
            record.potassium_visible = False
            
          

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '62147hjy-645d-4794-a0fd-3daa0124rtyu':
                    record.ph_visible = True

                if sample.internal_id == '325478ht-645d-4794-a0fd-3daa012410tr':
                    record.suspended_solids_visible = True

                if sample.internal_id == '98745jyt-645d-4794-a0fd-3daa0123214hyt':
                    record.oxygen_demand_visible = True

                if sample.internal_id == '65478iuy-645d-4794-a0fd-3daa01232ygtr1':
                    record.biooxygen_demand_visible = True
                
                if sample.internal_id == '36547bbn-645d-4794-a0fd-3daa01232yertv':
                    record.grease_visible = True
                
                if sample.internal_id == '32147h-ba0b-4e64-84d1-e3b23f3ty5610':
                    record.calcium_visible = True
                    
                if sample.internal_id == '2211bv-ba0b-4e64-84d1-e3b23ft301yr':
                    record.chloride_visible = True

                if sample.internal_id == '777bbbf-ba0b-4e64-84d1-e3b23f32147tr':
                    record.sodium_visible = True

                if sample.internal_id == '333yyy-ba0b-4e64-84d1-e3b23f32rtefg':
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
            if result.parameter.internal_id == '62147hjy-645d-4794-a0fd-3daa0124rtyu':
                result.result_char = round(self.ph_average,2)
                result.calculated = True
                if self.ph_average_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '325478ht-645d-4794-a0fd-3daa012410tr':
                result.result_char = round(self.avg_suspended_solids,2)
                result.calculated = True
                if self.avg_suspended_solids_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '98745jyt-645d-4794-a0fd-3daa0123214hyt':
                result.result_char = round(self.avg_oxygen_demand,2)
                result.calculated = True
                if self.avg_oxygen_demand_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '65478iuy-645d-4794-a0fd-3daa01232ygtr1':
                result.result_char = round(self.avg_biooxygen_demand,2)
                result.calculated = True
                if self.avg_biooxygen_demand_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '36547bbn-645d-4794-a0fd-3daa01232yertv':
                result.result_char = round(self.avg_grease,2)
                result.calculated = True
                if self.avg_grease_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '32147h-ba0b-4e64-84d1-e3b23f3ty5610':
                result.result_char = round(self.avg_calcium,2)
                result.calculated = True
                if self.avg_calcium_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '2211bv-ba0b-4e64-84d1-e3b23ft301yr':
                result.result_char = round(self.avg_chloride,2)
                result.calculated = True
                if self.avg_chloride_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '777bbbf-ba0b-4e64-84d1-e3b23f32147tr':
                result.result_char = round(self.sodium_average,2)
                result.calculated = True
                if self.sodium_average_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '333yyy-ba0b-4e64-84d1-e3b23f32rtefg':
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
        record = super(ChemicalWasteWater, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


        
    def get_all_fields(self):
        record = self.env['chemical.waste.water'].browse(self.ids[0])
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








class ChemWasteNotes(models.Model):
    _name = "chem.waste.water.notes"

    parent_id = fields.Many2one('chemical.waste.water',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
    