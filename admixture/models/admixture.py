from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class MechanicalAdmixture(models.Model):
    _name = "mechanical.admixture"
    _inherit = "lerm.eln"
    _rec_name = "name1"

    name1 = fields.Char("Name",default="Admixture")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    notes_id = fields.One2many('mecha.admixture.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(MechanicalAdmixture, self).default_get(fields)

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


    density_name = fields.Char("Name",default="Determination Specific Gravity Or Relative Density")
    density_visible = fields.Boolean("Determination Specific Gravity Or Relative Density",compute="_compute_visible")
    
    density_a = fields.Float("Relative Density by hydrometer")
    density_b = fields.Float("Relative Density by hydrometer")
    density_c = fields.Float("Relative Density by hydrometer")
    density_d = fields.Float("Relative Density by hydrometer")
    density_e = fields.Float("Relative Density by hydrometer")
    density_average = fields.Float("Average",compute="_compute_density_average")

    @api.depends("density_a",'density_b','density_c','density_d','density_e')
    def _compute_density_average(self):
        for record in self:
            record.density_average = (record.density_a + record.density_b + record.density_c + record.density_d + record.density_e)/5

    density_average_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_density_average_conformity", store=True)

    @api.depends('density_average','eln_ref','grade')
    def _compute_density_average_conformity(self):
            # remove this first when making changes
            self.density_average_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.density_average_conformity = 'na'
                    continue

                record.density_average_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','333llloo-645d-4794-a0fd-3daa0124rtyu')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','333llloo-645d-4794-a0fd-3daa0124rtyu')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.density_average - record.density_average*mu_value
                        upper = record.density_average + record.density_average*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.density_average_conformity = 'pass'
                            break
                        else:
                            record.density_average_conformity = 'fail'

    density_average_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_density_average_nabl", store=True)

    @api.depends('density_average','eln_ref','grade')
    def _compute_density_average_nabl(self):
        # remove this first
        self.density_average_nabl = 'fail'
        
        for record in self:
            record.density_average_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','333llloo-645d-4794-a0fd-3daa0124rtyu')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','333llloo-645d-4794-a0fd-3daa0124rtyu')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.density_average - record.density_average*mu_value
            upper = record.density_average + record.density_average*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.density_average_nabl = 'pass'
                break
            else:
                record.density_average_nabl = 'fail'


    # Dry Material Content

    dry_content_name = fields.Char("Name",default="Dry Material Content")
    dry_content_visible = fields.Boolean("Dry Material Content",compute="_compute_visible")

    dry_content_bottlew1_1 = fields.Float(string="Weight of bottle and sand (W1)")
    dry_content_bottlew1_2 = fields.Float(string="Weight of bottle and sand (W1)")
    dry_content_bottlew1_3 = fields.Float(string="Weight of bottle and sand (W1)")
    dry_content_bottlew1_4 = fields.Float(string="Weight of bottle and sand (W1)")
    dry_content_bottlew1_5 = fields.Float(string="Weight of bottle and sand (W1)")

    dry_content_bottlew2_1 = fields.Float(string="Weight of bottle, sand and sample (W2)")
    dry_content_bottlew2_2 = fields.Float(string="Weight of bottle, sand and sample (W2)")
    dry_content_bottlew2_3 = fields.Float(string="Weight of bottle, sand and sample (W2)")
    dry_content_bottlew2_4 = fields.Float(string="Weight of bottle, sand and sample (W2)")
    dry_content_bottlew2_5 = fields.Float(string="Weight of bottle, sand and sample (W2)")

    dry_content_wt_w2_w1_1 = fields.Float(string="Weight of sample (W2-W1)",compute="_compute_dry_sample", store=True)
    dry_content_wt_w2_w1_2 = fields.Float(string="Weight of sample (W2-W1)", compute="_compute_dry_sample", store=True)
    dry_content_wt_w2_w1_3 = fields.Float(string="Weight of sample (W2-W1)" ,compute="_compute_dry_sample", store=True)
    dry_content_wt_w2_w1_4 = fields.Float(string="Weight of sample (W2-W1)" ,compute="_compute_dry_sample", store=True)
    dry_content_wt_w2_w1_5 = fields.Float(string="Weight of sample (W2-W1)" ,compute="_compute_dry_sample", store=True)

    dry_content_driedw3_1 = fields.Float(string="Weight of bottle, sand and dried residue (W3)")
    dry_content_driedw3_2 = fields.Float(string="Weight of bottle, sand and dried residue (W3)")
    dry_content_driedw3_3 = fields.Float(string="Weight of bottle, sand and dried residue (W3)")
    dry_content_driedw3_4 = fields.Float(string="Weight of bottle, sand and dried residue (W3)")
    dry_content_driedw3_5 = fields.Float(string="Weight of bottle, sand and dried residue (W3)")

    dry_content_dried_w3_w1_1 = fields.Float(string="Weight of dried residue( W3-W1)", compute="_compute_dry_residue", store=True)
    dry_content_dried_w3_w1_2 = fields.Float(string="Weight of dried residue( W3-W1)", compute="_compute_dry_residue", store=True)
    dry_content_dried_w3_w1_3 = fields.Float(string="Weight of dried residue( W3-W1)", compute="_compute_dry_residue", store=True)
    dry_content_dried_w3_w1_4 = fields.Float(string="Weight of dried residue( W3-W1)", compute="_compute_dry_residue", store=True)
    dry_content_dried_w3_w1_5 = fields.Float(string="Weight of dried residue( W3-W1)", compute="_compute_dry_residue", store=True)

    dry_content_residue1 = fields.Float(string="Residue on drying", compute="_compute_dry_final", store=True)
    dry_content_residue2 = fields.Float(string="Residue on drying", compute="_compute_dry_final", store=True)
    dry_content_residue3 = fields.Float(string="Residue on drying", compute="_compute_dry_final", store=True)
    dry_content_residue4 = fields.Float(string="Residue on drying", compute="_compute_dry_final", store=True)
    dry_content_residue5 = fields.Float(string="Residue on drying", compute="_compute_dry_final", store=True)

    avg_dry_content = fields.Float(string="Average Dry Material Content ",compute="_compute_avg_dry_content",store=True)


    @api.depends(
    'dry_content_bottlew1_1','dry_content_bottlew2_1',
    'dry_content_bottlew1_2','dry_content_bottlew2_2',
    'dry_content_bottlew1_3','dry_content_bottlew2_3',
    'dry_content_bottlew1_4','dry_content_bottlew2_4',
    'dry_content_bottlew1_5','dry_content_bottlew2_5',
    )
    def _compute_dry_sample(self):
        for rec in self:

            rec.dry_content_wt_w2_w1_1 = rec.dry_content_bottlew2_1 - rec.dry_content_bottlew1_1
            rec.dry_content_wt_w2_w1_2 = rec.dry_content_bottlew2_2 - rec.dry_content_bottlew1_2
            rec.dry_content_wt_w2_w1_3 = rec.dry_content_bottlew2_3 - rec.dry_content_bottlew1_3
            rec.dry_content_wt_w2_w1_4 = rec.dry_content_bottlew2_4 - rec.dry_content_bottlew1_4
            rec.dry_content_wt_w2_w1_5 = rec.dry_content_bottlew2_5 - rec.dry_content_bottlew1_5

    @api.depends(
    'dry_content_driedw3_1','dry_content_bottlew1_1',
    'dry_content_driedw3_2','dry_content_bottlew1_2',
    'dry_content_driedw3_3','dry_content_bottlew1_3',
    'dry_content_driedw3_4','dry_content_bottlew1_4',
    'dry_content_driedw3_5','dry_content_bottlew1_5',
    )
    def _compute_dry_residue(self):
        for rec in self:

            rec.dry_content_dried_w3_w1_1 = rec.dry_content_driedw3_1 - rec.dry_content_bottlew1_1
            rec.dry_content_dried_w3_w1_2 = rec.dry_content_driedw3_2 - rec.dry_content_bottlew1_2
            rec.dry_content_dried_w3_w1_3 = rec.dry_content_driedw3_3 - rec.dry_content_bottlew1_3
            rec.dry_content_dried_w3_w1_4 = rec.dry_content_driedw3_4 - rec.dry_content_bottlew1_4
            rec.dry_content_dried_w3_w1_5 = rec.dry_content_driedw3_5 - rec.dry_content_bottlew1_5

    @api.depends(
    'dry_content_wt_w2_w1_1','dry_content_dried_w3_w1_1',
    'dry_content_wt_w2_w1_2','dry_content_dried_w3_w1_2',
    'dry_content_wt_w2_w1_3','dry_content_dried_w3_w1_3',
    'dry_content_wt_w2_w1_4','dry_content_dried_w3_w1_4',
    'dry_content_wt_w2_w1_5','dry_content_dried_w3_w1_5',
    )
    def _compute_dry_final(self):
        for rec in self:

            rec.dry_content_residue1 = ((rec.dry_content_dried_w3_w1_1 / rec.dry_content_wt_w2_w1_1) * 100) if rec.dry_content_wt_w2_w1_1 else 0.0

            rec.dry_content_residue2 = ((rec.dry_content_dried_w3_w1_2 / rec.dry_content_wt_w2_w1_2) * 100) if rec.dry_content_wt_w2_w1_2 else 0.0

            rec.dry_content_residue3 = ((rec.dry_content_dried_w3_w1_3 / rec.dry_content_wt_w2_w1_3) * 100) if rec.dry_content_wt_w2_w1_3 else 0.0

            rec.dry_content_residue4 = ((rec.dry_content_dried_w3_w1_4 / rec.dry_content_wt_w2_w1_4) * 100) if rec.dry_content_wt_w2_w1_4 else 0.0

            rec.dry_content_residue5 = ((rec.dry_content_dried_w3_w1_5 / rec.dry_content_wt_w2_w1_5) * 100) if rec.dry_content_wt_w2_w1_5 else 0.0

    @api.depends(
    'dry_content_residue1',
    'dry_content_residue2',
    'dry_content_residue3',
    'dry_content_residue4',
    'dry_content_residue5'
    )
    def _compute_avg_dry_content(self):
        for rec in self:

            rec.avg_dry_content = (
                rec.dry_content_residue1 +
                rec.dry_content_residue2 +
                rec.dry_content_residue3 +
                rec.dry_content_residue4 +
                rec.dry_content_residue5
            ) / 5

    avg_dry_content_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_dry_content_conformity", store=True)

    @api.depends('avg_dry_content','eln_ref','grade')
    def _compute_avg_dry_content_conformity(self):
            # remove this first when making changes
            self.avg_dry_content_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_dry_content_conformity = 'na'
                    continue

                record.avg_dry_content_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3000142-645d-4794-a0fd-3daa0124rtyu')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3000142-645d-4794-a0fd-3daa0124rtyu')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_dry_content - record.avg_dry_content*mu_value
                        upper = record.avg_dry_content + record.avg_dry_content*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_dry_content_conformity = 'pass'
                            break
                        else:
                            record.avg_dry_content_conformity = 'fail'

    avg_dry_content_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_dry_content_nabl", store=True)

    @api.depends('avg_dry_content','eln_ref','grade')
    def _compute_avg_dry_content_nabl(self):
        # remove this first
        self.avg_dry_content_nabl = 'fail'
        
        for record in self:
            record.avg_dry_content_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3000142-645d-4794-a0fd-3daa0124rtyu')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3000142-645d-4794-a0fd-3daa0124rtyu')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_dry_content - record.avg_dry_content*mu_value
            upper = record.avg_dry_content + record.avg_dry_content*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_dry_content_nabl = 'pass'
                break
            else:
                record.avg_dry_content_nabl = 'fail'

    #  ash_content
    ash_content_name = fields.Char("Name",default="Ash Content")
    ash_content_visible = fields.Boolean("Ash Content",compute="_compute_visible")

    ash_content_crucible1_1 = fields.Float(string="Weight of crucible (W1))")
    ash_content_crucible1_2 = fields.Float(string="Weight of crucible (W1))")
    ash_content_crucible1_3 = fields.Float(string="Weight of crucible (W1))")
    ash_content_crucible1_4 = fields.Float(string="Weight of crucible (W1))")
    ash_content_crucible1_5 = fields.Float(string="Weight of crucible (W1))")

    ash_content_cruciblew2_1 = fields.Float(string="Weight of crucible and sample (W2)")
    ash_content_cruciblew2_2 = fields.Float(string="Weight of crucible and sample (W2)")
    ash_content_cruciblew2_3 = fields.Float(string="Weight of crucible and sample (W2)")
    ash_content_cruciblew2_4 = fields.Float(string="Weight of crucible and sample (W2)")
    ash_content_cruciblew2_5 = fields.Float(string="Weight of crucible and sample (W2)")

   
    ash_content_cruciblew3_1 = fields.Float(string="Weight of crucible and Ash (W3)")
    ash_content_cruciblew3_2 = fields.Float(string="Weight of crucible and Ash (W3)")
    ash_content_cruciblew3_3 = fields.Float(string="Weight of crucible and Ash (W3)")
    ash_content_cruciblew3_4 = fields.Float(string="Weight of crucible and Ash (W3)")
    ash_content_cruciblew3_5 = fields.Float(string="Weight of crucible and Ash (W3)")

    ash_content_1 = fields.Float(string="Ash Content %", compute="_compute_ash_content", store=True)
    ash_content_2 = fields.Float(string="Ash Content %", compute="_compute_ash_content", store=True)
    ash_content_3 = fields.Float(string="Ash Content %", compute="_compute_ash_content", store=True)
    ash_content_4 = fields.Float(string="Ash Content %", compute="_compute_ash_content", store=True)
    ash_content_5 = fields.Float(string="Ash Content %", compute="_compute_ash_content", store=True)

    

    avg_ash_content = fields.Float(string="Average Ash Content  (%) ",compute="_compute_avg_ash_content",store=True)

    @api.depends(
    'ash_content_1',
    'ash_content_2',
    'ash_content_3',
    'ash_content_4',
    'ash_content_5'
    )
    def _compute_avg_ash_content(self):
        for rec in self:

            rec.avg_ash_content = (
                rec.ash_content_1 +
                rec.ash_content_2 +
                rec.ash_content_3 +
                rec.ash_content_4 +
                rec.ash_content_5
            ) / 5


    @api.depends(
    'ash_content_crucible1_1','ash_content_cruciblew2_1','ash_content_cruciblew3_1',
    'ash_content_crucible1_2','ash_content_cruciblew2_2','ash_content_cruciblew3_2',
    'ash_content_crucible1_3','ash_content_cruciblew2_3','ash_content_cruciblew3_3',
    'ash_content_crucible1_4','ash_content_cruciblew2_4','ash_content_cruciblew3_4',
    'ash_content_crucible1_5','ash_content_cruciblew2_5','ash_content_cruciblew3_5',
    )
    def _compute_ash_content(self):
        for rec in self:

            rec.ash_content_1 = (
                ((rec.ash_content_cruciblew3_1 - rec.ash_content_crucible1_1) /
                (rec.ash_content_cruciblew2_1 - rec.ash_content_crucible1_1)) * 100
            ) if (rec.ash_content_cruciblew2_1 - rec.ash_content_crucible1_1) else 0.0

            rec.ash_content_2 = (
                ((rec.ash_content_cruciblew3_2 - rec.ash_content_crucible1_2) /
                (rec.ash_content_cruciblew2_2 - rec.ash_content_crucible1_2)) * 100
            ) if (rec.ash_content_cruciblew2_2 - rec.ash_content_crucible1_2) else 0.0

            rec.ash_content_3 = (
                ((rec.ash_content_cruciblew3_3 - rec.ash_content_crucible1_3) /
                (rec.ash_content_cruciblew2_3 - rec.ash_content_crucible1_3)) * 100
            ) if (rec.ash_content_cruciblew2_3 - rec.ash_content_crucible1_3) else 0.0

            rec.ash_content_4 = (
                ((rec.ash_content_cruciblew3_4 - rec.ash_content_crucible1_4) /
                (rec.ash_content_cruciblew2_4 - rec.ash_content_crucible1_4)) * 100
            ) if (rec.ash_content_cruciblew2_4 - rec.ash_content_crucible1_4) else 0.0

            rec.ash_content_5 = (
                ((rec.ash_content_cruciblew3_5 - rec.ash_content_crucible1_5) /
                (rec.ash_content_cruciblew2_5 - rec.ash_content_crucible1_5)) * 100
            ) if (rec.ash_content_cruciblew2_5 - rec.ash_content_crucible1_5) else 0.0

    avg_ash_content_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_ash_content_conformity", store=True)

    @api.depends('avg_ash_content','eln_ref','grade')
    def _compute_avg_ash_content_conformity(self):
            # remove this first when making changes
            self.avg_ash_content_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_ash_content_conformity = 'na'
                    continue

                record.avg_ash_content_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','55oop00-645d-4794-a0fd-3daa0124rtyu')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','55oop00-645d-4794-a0fd-3daa0124rtyu')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_ash_content - record.avg_ash_content*mu_value
                        upper = record.avg_ash_content + record.avg_ash_content*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_ash_content_conformity = 'pass'
                            break
                        else:
                            record.avg_ash_content_conformity = 'fail'

    avg_ash_content_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_ash_content_nabl", store=True)

    @api.depends('avg_ash_content','eln_ref','grade')
    def _compute_avg_ash_content_nabl(self):
        # remove this first
        self.avg_ash_content_nabl = 'fail'
        
        for record in self:
            record.avg_ash_content_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','55oop00-645d-4794-a0fd-3daa0124rtyu')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','55oop00-645d-4794-a0fd-3daa0124rtyu')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_ash_content - record.avg_ash_content*mu_value
            upper = record.avg_ash_content + record.avg_ash_content*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_ash_content_nabl = 'pass'
                break
            else:
                record.avg_ash_content_nabl = 'fail'


     #  CHLORIDE
     
    chloride_name = fields.Char("Name",default="Chloride")
    chloride_visible = fields.Boolean("Chloride",compute="_compute_visible")

    chloride_samplew_1 = fields.Float(string="Weight of sample taken in gm (W)")
    chloride_samplew_2 = fields.Float(string="Weight of sample taken in gm (W)")
    chloride_samplew_3 = fields.Float(string="Weight of sample taken in gm (W)")
    chloride_samplew_4 = fields.Float(string="Weight of sample taken in gm (W)")
    chloride_samplew_5 = fields.Float(string="Weight of sample taken in gm (W)")

    chloride_nitratew1_1 = fields.Float(string="Added of Silver Nitrate 0.1N(W1) ml")
    chloride_nitratew1_2 = fields.Float(string="Added of Silver Nitrate 0.1N(W1) ml")
    chloride_nitratew1_3 = fields.Float(string="Added of Silver Nitrate 0.1N(W1) ml")
    chloride_nitratew1_4 = fields.Float(string="Added of Silver Nitrate 0.1N(W1) ml")
    chloride_nitratew1_5 = fields.Float(string="Added of Silver Nitrate 0.1N(W1) ml")

   
    chloride_ammoniumw2_1 = fields.Float(string="Titer value of ammonium thiocyanate 0.1N (W2)")
    chloride_ammoniumw2_2 = fields.Float(string="Titer value of ammonium thiocyanate 0.1N (W2)")
    chloride_ammoniumw2_3 = fields.Float(string="Titer value of ammonium thiocyanate 0.1N (W2)")
    chloride_ammoniumw2_4 = fields.Float(string="Titer value of ammonium thiocyanate 0.1N (W2)")
    chloride_ammoniumw2_5 = fields.Float(string="Titer value of ammonium thiocyanate 0.1N (W2)")

    chloride_1 = fields.Float(string="Chloride %", compute="_compute_chloride_percent", store=True)
    chloride_2 = fields.Float(string="Chloride %", compute="_compute_chloride_percent", store=True)
    chloride_3 = fields.Float(string="Chloride %", compute="_compute_chloride_percent", store=True)
    chloride_4 = fields.Float(string="Chloride %", compute="_compute_chloride_percent", store=True)
    chloride_5 = fields.Float(string="Chloride %", compute="_compute_chloride_percent", store=True)

    

    avg_chloride = fields.Float(string="Average Chloride % ",compute="_compute_avg_chloride_percent",store=True)

    @api.depends(
    'chloride_samplew_1','chloride_nitratew1_1','chloride_ammoniumw2_1',
    'chloride_samplew_2','chloride_nitratew1_2','chloride_ammoniumw2_2',
    'chloride_samplew_3','chloride_nitratew1_3','chloride_ammoniumw2_3',
    'chloride_samplew_4','chloride_nitratew1_4','chloride_ammoniumw2_4',
    'chloride_samplew_5','chloride_nitratew1_5','chloride_ammoniumw2_5',
    )
    def _compute_chloride_percent(self):
        for rec in self:

            rec.chloride_1 = (
                ((rec.chloride_nitratew1_1 - rec.chloride_ammoniumw2_1) * 0.003546)
                / rec.chloride_samplew_1 * 100
            ) if rec.chloride_samplew_1 else 0.0

            rec.chloride_2 = (
                ((rec.chloride_nitratew1_2 - rec.chloride_ammoniumw2_2) * 0.003546)
                / rec.chloride_samplew_2 * 100
            ) if rec.chloride_samplew_2 else 0.0

            rec.chloride_3 = (
                ((rec.chloride_nitratew1_3 - rec.chloride_ammoniumw2_3) * 0.003546)
                / rec.chloride_samplew_3 * 100
            ) if rec.chloride_samplew_3 else 0.0

            rec.chloride_4 = (
                ((rec.chloride_nitratew1_4 - rec.chloride_ammoniumw2_4) * 0.003546)
                / rec.chloride_samplew_4 * 100
            ) if rec.chloride_samplew_4 else 0.0

            rec.chloride_5 = (
                ((rec.chloride_nitratew1_5 - rec.chloride_ammoniumw2_5) * 0.003546)
                / rec.chloride_samplew_5 * 100
            ) if rec.chloride_samplew_5 else 0.0

    @api.depends(
    'chloride_1',
    'chloride_2',
    'chloride_3',
    'chloride_4',
    'chloride_5'
    )
    def _compute_avg_chloride_percent(self):
        for rec in self:

            rec.avg_chloride = (
                rec.chloride_1 +
                rec.chloride_2 +
                rec.chloride_3 +
                rec.chloride_4 +
                rec.chloride_5
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
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','33yyy11-645d-4794-a0fd-3daa01200014')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','33yyy11-645d-4794-a0fd-3daa01200014')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','33yyy11-645d-4794-a0fd-3daa01200014')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','33yyy11-645d-4794-a0fd-3daa01200014')]).parameter_table
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

    # pH
    
    ph_name = fields.Char("Name",default="pH")
    ph_visible = fields.Boolean("pH",compute="_compute_visible")
    
    ph_a = fields.Float("pH")
    ph_b = fields.Float("pH")
    ph_c = fields.Float("pH")
    ph_d = fields.Float("pH")
    ph_e = fields.Float("pH")
    ph_average = fields.Float("Average pH",compute="_compute_ph_average")

    @api.depends("ph_a",'ph_b','ph_c','ph_d','ph_e')
    def _compute_ph_average(self):
        for record in self:
            record.ph_average = (record.ph_a + record.ph_b + record.ph_c + record.ph_d + record.ph_e)/5

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
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','555ppp1-645d-4794-a0fd-3daa0124r0014')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','555ppp1-645d-4794-a0fd-3daa0124r0014')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','555ppp1-645d-4794-a0fd-3daa0124r0014')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','555ppp1-645d-4794-a0fd-3daa0124r0014')]).parameter_table
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



    




    @api.depends('sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.density_visible = False
            record.dry_content_visible = False
            record.ash_content_visible = False
            record.chloride_visible = False
            record.ph_visible = False
            
          

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '333llloo-645d-4794-a0fd-3daa0124rtyu':
                    record.density_visible = True

                if sample.internal_id == '3000142-645d-4794-a0fd-3daa0124rtyu':
                    record.dry_content_visible = True

                if sample.internal_id == '55oop00-645d-4794-a0fd-3daa0124rtyu':
                    record.ash_content_visible = True

                if sample.internal_id == '33yyy11-645d-4794-a0fd-3daa01200014':
                    record.chloride_visible = True

                if sample.internal_id == '555ppp1-645d-4794-a0fd-3daa0124r0014':
                    record.ph_visible = True





    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

            
            
            # Water Absorbtion
            if result.parameter.internal_id == '333llloo-645d-4794-a0fd-3daa0124rtyu':
                result.result_char = round(self.density_average,2)
                result.calculated = True
                if self.density_average_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '3000142-645d-4794-a0fd-3daa0124rtyu':
                result.result_char = round(self.avg_dry_content,2)
                result.calculated = True
                if self.avg_dry_content_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '55oop00-645d-4794-a0fd-3daa0124rtyu':
                result.result_char = round(self.avg_ash_content,2)
                result.calculated = True
                if self.avg_ash_content_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '33yyy11-645d-4794-a0fd-3daa01200014':
                result.result_char = round(self.avg_chloride,2)
                result.calculated = True
                if self.avg_chloride_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '555ppp1-645d-4794-a0fd-3daa0124r0014':
                result.result_char = round(self.ph_average,2)
                result.calculated = True
                if self.ph_average_nabl == 'pass':
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
        record = super(MechanicalAdmixture, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


        
    def get_all_fields(self):
        record = self.env['mechanical.admixture'].browse(self.ids[0])
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








class MechaAdmixtureNotes(models.Model):
    _name = "mecha.admixture.notes"

    parent_id = fields.Many2one('mechanical.admixture',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
    