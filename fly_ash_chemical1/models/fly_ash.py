from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class ChemicalFlyAsh(models.Model):
    _name = "chemical.fly.ash"
    _inherit = "lerm.eln"
    _rec_name = "name1"

    name1 = fields.Char("Name",default="Fly Ash")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    notes_id = fields.One2many('chem.fly.ash.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(ChemicalFlyAsh, self).default_get(fields)

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


    
    # LOSS ON IGNITION
    

    loass_ingnition_name = fields.Char("Name",default="LOSS ON IGNITION")
    loass_ingnition_visible = fields.Boolean("LOSS ON IGNITION",compute="_compute_visible")

    loass_ingnition_sampleb_1 = fields.Float(string="Weight of Moisture free sample taken, B")
    loass_ingnition_sampleb_2 = fields.Float(string="Weight of Moisture free sample taken, B")
    loass_ingnition_sampleb_3 = fields.Float(string="Weight of Moisture free sample taken, B")
    loass_ingnition_sampleb_4 = fields.Float(string="Weight of Moisture free sample taken, B")
    loass_ingnition_sampleb_5 = fields.Float(string="Weight of Moisture free sample taken, B")

    loass_ingnition_cruciblew2_1 = fields.Float(string="Weight of Crucible and Sample (W2)")
    loass_ingnition_cruciblew2_2 = fields.Float(string="Weight of Crucible and Sample (W2)")
    loass_ingnition_cruciblew2_3 = fields.Float(string="Weight of Crucible and Sample (W2)")
    loass_ingnition_cruciblew2_4 = fields.Float(string="Weight of Crucible and Sample (W2)")
    loass_ingnition_cruciblew2_5 = fields.Float(string="Weight of Crucible and Sample (W2)")

    loass_ingnition_cruciblew3_1 = fields.Float(string="Weight of Crucible after ignition (W3)")
    loass_ingnition_cruciblew3_2 = fields.Float(string="Weight of Crucible after ignition (W3)")
    loass_ingnition_cruciblew3_3 = fields.Float(string="Weight of Crucible after ignition (W3)" )
    loass_ingnition_cruciblew3_4 = fields.Float(string="Weight of Crucible after ignition (W3)" )
    loass_ingnition_cruciblew3_5 = fields.Float(string="Weight of Crucible after ignition (W3)" )

    loass_ingnition_a_1 = fields.Float(string="Loss in Weight, A (W2-W3)" ,compute="_compute_loi_a",store=True)
    loass_ingnition_a_2 = fields.Float(string="Loss in Weight, A (W2-W3)",compute="_compute_loi_a",store=True)
    loass_ingnition_a_3 = fields.Float(string="Loss in Weight, A (W2-W3)" ,compute="_compute_loi_a",store=True)
    loass_ingnition_a_4 = fields.Float(string="Loss in Weight, A (W2-W3)",compute="_compute_loi_a",store=True )
    loass_ingnition_a_5 = fields.Float(string="Loss in Weight, A (W2-W3)",compute="_compute_loi_a",store=True )

    

    loass_ingnition_1 = fields.Float(string="Loass Ingnition %" ,compute="_compute_loi"  ,store=True)
    loass_ingnition_2 = fields.Float(string="Loass Ingnition %" ,compute="_compute_loi"  ,store=True)
    loass_ingnition_3 = fields.Float(string="Loass Ingnition %" ,compute="_compute_loi"  ,store=True)
    loass_ingnition_4 = fields.Float(string="Loass Ingnition %"  ,compute="_compute_loi"  ,store=True)
    loass_ingnition_5 = fields.Float(string="Loass Ingnition %" ,compute="_compute_loi"  ,store=True)

    avg_loass_ingnition = fields.Float(string="Average Loass Ingnition % ",compute="_compute_avg_loi",store=True)


    @api.depends(
    'loass_ingnition_1',
    'loass_ingnition_2',
    'loass_ingnition_3',
    'loass_ingnition_4',
    'loass_ingnition_5'
    )
    def _compute_avg_loi(self):
        for rec in self:

            rec.avg_loass_ingnition = (
                rec.loass_ingnition_1 +
                rec.loass_ingnition_2 +
                rec.loass_ingnition_3 +
                rec.loass_ingnition_4 +
                rec.loass_ingnition_5
            ) / 5


    @api.depends(
    'loass_ingnition_cruciblew2_1','loass_ingnition_cruciblew3_1',
    'loass_ingnition_cruciblew2_2','loass_ingnition_cruciblew3_2',
    'loass_ingnition_cruciblew2_3','loass_ingnition_cruciblew3_3',
    'loass_ingnition_cruciblew2_4','loass_ingnition_cruciblew3_4',
    'loass_ingnition_cruciblew2_5','loass_ingnition_cruciblew3_5',
    )
    def _compute_loi_a(self):
        for rec in self:

            rec.loass_ingnition_a_1 = (rec.loass_ingnition_cruciblew2_1 - rec.loass_ingnition_cruciblew3_1)
            rec.loass_ingnition_a_2 = (rec.loass_ingnition_cruciblew2_2 - rec.loass_ingnition_cruciblew3_2)
            rec.loass_ingnition_a_3 = (rec.loass_ingnition_cruciblew2_3 - rec.loass_ingnition_cruciblew3_3)
            rec.loass_ingnition_a_4 = (rec.loass_ingnition_cruciblew2_4 - rec.loass_ingnition_cruciblew3_4)
            rec.loass_ingnition_a_5 = (rec.loass_ingnition_cruciblew2_5 - rec.loass_ingnition_cruciblew3_5)

    @api.depends(
    'loass_ingnition_a_1','loass_ingnition_sampleb_1',
    'loass_ingnition_a_2','loass_ingnition_sampleb_2',
    'loass_ingnition_a_3','loass_ingnition_sampleb_3',
    'loass_ingnition_a_4','loass_ingnition_sampleb_4',
    'loass_ingnition_a_5','loass_ingnition_sampleb_5',
    )
    def _compute_loi(self):
        for rec in self:

            rec.loass_ingnition_1 = (
                (rec.loass_ingnition_a_1 / rec.loass_ingnition_sampleb_1) * 100
            ) if rec.loass_ingnition_sampleb_1 else 0.0

            rec.loass_ingnition_2 = (
                (rec.loass_ingnition_a_2 / rec.loass_ingnition_sampleb_2) * 100
            ) if rec.loass_ingnition_sampleb_2 else 0.0

            rec.loass_ingnition_3 = (
                (rec.loass_ingnition_a_3 / rec.loass_ingnition_sampleb_3) * 100
            ) if rec.loass_ingnition_sampleb_3 else 0.0

            rec.loass_ingnition_4 = (
                (rec.loass_ingnition_a_4 / rec.loass_ingnition_sampleb_4) * 100
            ) if rec.loass_ingnition_sampleb_4 else 0.0

            rec.loass_ingnition_5 = (
                (rec.loass_ingnition_a_5 / rec.loass_ingnition_sampleb_5) * 100
            ) if rec.loass_ingnition_sampleb_5 else 0.0


    avg_loass_ingnition_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_loass_ingnition_conformity", store=True)

    @api.depends('avg_loass_ingnition','eln_ref','grade')
    def _compute_avg_loass_ingnition_conformity(self):
            # remove this first when making changes
            self.avg_loass_ingnition_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_loass_ingnition_conformity = 'na'
                    continue

                record.avg_loass_ingnition_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','333114425-645d-4794-a0fd-3daa0124r0021478')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','333114425-645d-4794-a0fd-3daa0124r0021478')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_loass_ingnition - record.avg_loass_ingnition*mu_value
                        upper = record.avg_loass_ingnition + record.avg_loass_ingnition*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_loass_ingnition_conformity = 'pass'
                            break
                        else:
                            record.avg_loass_ingnition_conformity = 'fail'

    avg_loass_ingnition_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_loass_ingnition_nabl", store=True)

    @api.depends('avg_loass_ingnition','eln_ref','grade')
    def _compute_avg_loass_ingnition_nabl(self):
        # remove this first
        self.avg_loass_ingnition_nabl = 'fail'
        
        for record in self:
            record.avg_loass_ingnition_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','333114425-645d-4794-a0fd-3daa0124r0021478')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','333114425-645d-4794-a0fd-3daa0124r0021478')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_loass_ingnition - record.avg_loass_ingnition*mu_value
            upper = record.avg_loass_ingnition + record.avg_loass_ingnition*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_loass_ingnition_nabl = 'pass'
                break
            else:
                record.avg_loass_ingnition_nabl = 'fail'

    # SILICA

    
    silica_name = fields.Char("Name",default="SILICA")
    silica_visible = fields.Boolean("SILICA",compute="_compute_visible")

    silica_samplew_1 = fields.Float(string="Weight of sample taken for test (W)")
    silica_samplew_2 = fields.Float(string="Weight of sample taken for test (W)")
    silica_samplew_3 = fields.Float(string="Weight of sample taken for test (W)")
    silica_samplew_4 = fields.Float(string="Weight of sample taken for test (W)")
    silica_samplew_5 = fields.Float(string="Weight of sample taken for test (W)")

    silica_cruciblew2_1 = fields.Float(string="Weight of crucible with insoluble residue (W2)")
    silica_cruciblew2_2 = fields.Float(string="Weight of crucible with insoluble residue (W2)")
    silica_cruciblew2_3 = fields.Float(string="Weight of crucible with insoluble residue (W2)")
    silica_cruciblew2_4 = fields.Float(string="Weight of crucible with insoluble residue (W2)")
    silica_cruciblew2_5 = fields.Float(string="Weight of crucible with insoluble residue (W2)")

    silica_cruciblew1_1 = fields.Float(string="Weight of empty crucible (W1)")
    silica_cruciblew1_2 = fields.Float(string="Weight of empty crucible (W1)")
    silica_cruciblew1_3 = fields.Float(string="Weight of empty crucible (W1)" )
    silica_cruciblew1_4 = fields.Float(string="Weight of empty crucible (W1)" )
    silica_cruciblew1_5 = fields.Float(string="Weight of empty crucible (W1)" )

    
    

    silica_1 = fields.Float(string="Silica %" ,compute="_compute_silica"  ,store=True)
    silica_2 = fields.Float(string="Silica %"   ,compute="_compute_silica"  ,store=True)
    silica_3 = fields.Float(string="Silica %"   ,compute="_compute_silica"  ,store=True)
    silica_4 = fields.Float(string="Silica %"    ,compute="_compute_silica"  ,store=True)
    silica_5 = fields.Float(string="Silica %"   ,compute="_compute_silica"  ,store=True)

    avg_silica = fields.Float(string="Average Silica % ",compute="_compute_avg_silica",store=True)


    @api.depends(
    'silica_cruciblew2_1','silica_cruciblew1_1','silica_samplew_1',
    'silica_cruciblew2_2','silica_cruciblew1_2','silica_samplew_2',
    'silica_cruciblew2_3','silica_cruciblew1_3','silica_samplew_3',
    'silica_cruciblew2_4','silica_cruciblew1_4','silica_samplew_4',
    'silica_cruciblew2_5','silica_cruciblew1_5','silica_samplew_5',
    )
    def _compute_silica(self):
        for rec in self:

            rec.silica_1 = (
                ((rec.silica_cruciblew2_1 - rec.silica_cruciblew1_1) * 100) / rec.silica_samplew_1
            ) if rec.silica_samplew_1 else 0.0

            rec.silica_2 = (
                ((rec.silica_cruciblew2_2 - rec.silica_cruciblew1_2) * 100) / rec.silica_samplew_2
            ) if rec.silica_samplew_2 else 0.0

            rec.silica_3 = (
                ((rec.silica_cruciblew2_3 - rec.silica_cruciblew1_3) * 100) / rec.silica_samplew_3
            ) if rec.silica_samplew_3 else 0.0

            rec.silica_4 = (
                ((rec.silica_cruciblew2_4 - rec.silica_cruciblew1_4) * 100) / rec.silica_samplew_4
            ) if rec.silica_samplew_4 else 0.0

            rec.silica_5 = (
                ((rec.silica_cruciblew2_5 - rec.silica_cruciblew1_5) * 100) / rec.silica_samplew_5
            ) if rec.silica_samplew_5 else 0.0


    @api.depends(
    'silica_1',
    'silica_2',
    'silica_3',
    'silica_4',
    'silica_5'
    )
    def _compute_avg_silica(self):
        for rec in self:

            rec.avg_silica = (
                rec.silica_1 +
                rec.silica_2 +
                rec.silica_3 +
                rec.silica_4 +
                rec.silica_5
            ) / 5


    avg_silica_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_silica_conformity", store=True)

    @api.depends('avg_silica','eln_ref','grade')
    def _compute_avg_silica_conformity(self):
            # remove this first when making changes
            self.avg_silica_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_silica_conformity = 'na'
                    continue

                record.avg_silica_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','666557788ttn-645d-4794-a0fd-3daa0124r0021478')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','666557788ttn-645d-4794-a0fd-3daa0124r0021478')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_silica - record.avg_silica*mu_value
                        upper = record.avg_silica + record.avg_silica*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_silica_conformity = 'pass'
                            break
                        else:
                            record.avg_silica_conformity = 'fail'

    avg_silica_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_silica_nabl", store=True)

    @api.depends('avg_silica','eln_ref','grade')
    def _compute_avg_silica_nabl(self):
        # remove this first
        self.avg_silica_nabl = 'fail'
        
        for record in self:
            record.avg_silica_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','666557788ttn-645d-4794-a0fd-3daa0124r0021478')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','666557788ttn-645d-4794-a0fd-3daa0124r0021478')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_silica - record.avg_silica*mu_value
            upper = record.avg_silica + record.avg_silica*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_silica_nabl = 'pass'
                break
            else:
                record.avg_silica_nabl = 'fail'

    #  DETERMINATION OF FERRIC OXIDE + ALUMINA
    
    ferric_alumina_name = fields.Char("Name",default="FERRIC OXIDE + ALUMINA")
    ferric_alumina_visible = fields.Boolean("FERRIC OXIDE + ALUMINA",compute="_compute_visible")

    ferric_alumina_samplew_1 = fields.Float(string="Weight of sample taken (W)")
    ferric_alumina_samplew_2 = fields.Float(string="Weight of sample taken (W)")
    ferric_alumina_samplew_3 = fields.Float(string="Weight of sample taken (W)")
    ferric_alumina_samplew_4 = fields.Float(string="Weight of sample taken (W)")
    ferric_alumina_samplew_5 = fields.Float(string="Weight of sample taken (W)")

    ferric_alumina_cruciblew1_1 = fields.Float(string="Weight of Empty Crucible (W1)")
    ferric_alumina_cruciblew1_2 = fields.Float(string="Weight of Empty Crucible (W1)")
    ferric_alumina_cruciblew1_3 = fields.Float(string="Weight of Empty Crucible (W1)")
    ferric_alumina_cruciblew1_4 = fields.Float(string="Weight of Empty Crucible (W1)")
    ferric_alumina_cruciblew1_5 = fields.Float(string="Weight of Empty Crucible (W1)")

    ferric_alumina_cruciblew2_1 = fields.Float(string="Weight of Crucible + Residue in gm. (W2)")
    ferric_alumina_cruciblew2_2 = fields.Float(string="Weight of Crucible + Residue in gm. (W2)")
    ferric_alumina_cruciblew2_3 = fields.Float(string="Weight of Crucible + Residue in gm. (W2)" )
    ferric_alumina_cruciblew2_4 = fields.Float(string="Weight of Crucible + Residue in gm. (W2)" )
    ferric_alumina_cruciblew2_5 = fields.Float(string="Weight of Crucible + Residue in gm. (W2)" )

    
    

    ferric_alumina_1 = fields.Float(string="R2O3 %" ,compute="_compute_ferric_alumina", store=True)
    ferric_alumina_2 = fields.Float(string="R2O3 %"   ,compute="_compute_ferric_alumina", store=True)
    ferric_alumina_3 = fields.Float(string="R2O3 %"   ,compute="_compute_ferric_alumina", store=True)
    ferric_alumina_4 = fields.Float(string="R2O3 %"    ,compute="_compute_ferric_alumina", store=True)
    ferric_alumina_5 = fields.Float(string="R2O3 %"   ,compute="_compute_ferric_alumina", store=True)

    avg_ferric_alumina = fields.Float(string="Average Ferric Alumina % ",compute="_compute_avg_ferric_alumina", store=True)

    @api.depends(
    'ferric_alumina_1',
    'ferric_alumina_2',
    'ferric_alumina_3',
    'ferric_alumina_4',
    'ferric_alumina_5'
    )
    def _compute_avg_ferric_alumina(self):
        for rec in self:

            rec.avg_ferric_alumina = (
                rec.ferric_alumina_1 +
                rec.ferric_alumina_2 +
                rec.ferric_alumina_3 +
                rec.ferric_alumina_4 +
                rec.ferric_alumina_5
            ) / 5

    @api.depends(
    'ferric_alumina_cruciblew2_1','ferric_alumina_cruciblew1_1','ferric_alumina_samplew_1',
    'ferric_alumina_cruciblew2_2','ferric_alumina_cruciblew1_2','ferric_alumina_samplew_2',
    'ferric_alumina_cruciblew2_3','ferric_alumina_cruciblew1_3','ferric_alumina_samplew_3',
    'ferric_alumina_cruciblew2_4','ferric_alumina_cruciblew1_4','ferric_alumina_samplew_4',
    'ferric_alumina_cruciblew2_5','ferric_alumina_cruciblew1_5','ferric_alumina_samplew_5',
    )
    def _compute_ferric_alumina(self):
        for rec in self:

            rec.ferric_alumina_1 = (
                ((rec.ferric_alumina_cruciblew2_1 - rec.ferric_alumina_cruciblew1_1) / rec.ferric_alumina_samplew_1) * 100
            ) if rec.ferric_alumina_samplew_1 else 0.0

            rec.ferric_alumina_2 = (
                ((rec.ferric_alumina_cruciblew2_2 - rec.ferric_alumina_cruciblew1_2) / rec.ferric_alumina_samplew_2) * 100
            ) if rec.ferric_alumina_samplew_2 else 0.0

            rec.ferric_alumina_3 = (
                ((rec.ferric_alumina_cruciblew2_3 - rec.ferric_alumina_cruciblew1_3) / rec.ferric_alumina_samplew_3) * 100
            ) if rec.ferric_alumina_samplew_3 else 0.0

            rec.ferric_alumina_4 = (
                ((rec.ferric_alumina_cruciblew2_4 - rec.ferric_alumina_cruciblew1_4) / rec.ferric_alumina_samplew_4) * 100
            ) if rec.ferric_alumina_samplew_4 else 0.0

            rec.ferric_alumina_5 = (
                ((rec.ferric_alumina_cruciblew2_5 - rec.ferric_alumina_cruciblew1_5) / rec.ferric_alumina_samplew_5) * 100
            ) if rec.ferric_alumina_samplew_5 else 0.0


    avg_ferric_alumina_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_ferric_alumina_conformity", store=True)

    @api.depends('avg_ferric_alumina','eln_ref','grade')
    def _compute_avg_ferric_alumina_conformity(self):
            # remove this first when making changes
            self.avg_ferric_alumina_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_ferric_alumina_conformity = 'na'
                    continue

                record.avg_ferric_alumina_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','665478grtvb-645d-4794-a0fd-3daa0124r0021478')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','665478grtvb-645d-4794-a0fd-3daa0124r0021478')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_ferric_alumina - record.avg_ferric_alumina*mu_value
                        upper = record.avg_ferric_alumina + record.avg_ferric_alumina*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_ferric_alumina_conformity = 'pass'
                            break
                        else:
                            record.avg_ferric_alumina_conformity = 'fail'

    avg_ferric_alumina_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_ferric_alumina_nabl", store=True)

    @api.depends('avg_ferric_alumina','eln_ref','grade')
    def _compute_avg_ferric_alumina_nabl(self):
        # remove this first
        self.avg_ferric_alumina_nabl = 'fail'
        
        for record in self:
            record.avg_ferric_alumina_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','665478grtvb-645d-4794-a0fd-3daa0124r0021478')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','665478grtvb-645d-4794-a0fd-3daa0124r0021478')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_ferric_alumina - record.avg_ferric_alumina*mu_value
            upper = record.avg_ferric_alumina + record.avg_ferric_alumina*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_ferric_alumina_nabl = 'pass'
                break
            else:
                record.avg_ferric_alumina_nabl = 'fail'


    #  FERRIC OXIDE
    
    ferric_oxide_name = fields.Char("Name",default="FERRIC OXIDE")
    ferric_oxide_visible = fields.Boolean("FERRIC OXIDE",compute="_compute_visible")

    ferric_oxide_potassiumv_1 = fields.Float(string="Volume of 0.04 N potassium permanganate solution used in ml,(V)")
    ferric_oxide_potassiumv_2 = fields.Float(string="Volume of 0.04 N potassium permanganate solution used in ml,(V)")
    ferric_oxide_potassiumv_3 = fields.Float(string="Volume of 0.04 N potassium permanganate solution used in ml,(V)")
    ferric_oxide_potassiumv_4 = fields.Float(string="Volume of 0.04 N potassium permanganate solution used in ml,(V)")
    ferric_oxide_potassiumv_5 = fields.Float(string="Volume of 0.04 N potassium permanganate solution used in ml,(V)")

    ferric_oxide_potassiumn_1 = fields.Float(string="Normality of Potassium permanganate (N)")
    ferric_oxide_potassiumn_2 = fields.Float(string="Normality of Potassium permanganate (N)")
    ferric_oxide_potassiumn_3 = fields.Float(string="Normality of Potassium permanganate (N)")
    ferric_oxide_potassiumn_4 = fields.Float(string="Normality of Potassium permanganate (N)")
    ferric_oxide_potassiumn_5 = fields.Float(string="Normality of Potassium permanganate (N)")

    ferric_oxide_samplew_1 = fields.Float(string="Weight of the sample (W)")
    ferric_oxide_samplew_2 = fields.Float(string="Weight of the sample (W)")
    ferric_oxide_samplew_3 = fields.Float(string="Weight of the sample (W)" )
    ferric_oxide_samplew_4 = fields.Float(string="Weight of the sample (W)" )
    ferric_oxide_samplew_5 = fields.Float(string="Weight of the sample (W)" )

    
    

    ferric_oxide_1 = fields.Float(string="Ferric Oxide %", compute="_compute_ferric_oxide", store=True)
    ferric_oxide_2 = fields.Float(string="Ferric Oxide %"  , compute="_compute_ferric_oxide", store=True)
    ferric_oxide_3 = fields.Float(string="Ferric Oxide %"  , compute="_compute_ferric_oxide", store=True)
    ferric_oxide_4 = fields.Float(string="Ferric Oxide %"   , compute="_compute_ferric_oxide", store=True)
    ferric_oxide_5 = fields.Float(string="Ferric Oxide %"  , compute="_compute_ferric_oxide", store=True)

    avg_ferric_oxide = fields.Float(string="Average Ferric Oxide % ", compute="_compute_avg_ferric_oxide", store=True)

    @api.depends(
    'ferric_oxide_1',
    'ferric_oxide_2',
    'ferric_oxide_3',
    'ferric_oxide_4',
    'ferric_oxide_5'
    )
    def _compute_avg_ferric_oxide(self):
        for rec in self:

            rec.avg_ferric_oxide = (
                rec.ferric_oxide_1 +
                rec.ferric_oxide_2 +
                rec.ferric_oxide_3 +
                rec.ferric_oxide_4 +
                rec.ferric_oxide_5
            ) / 5


    @api.depends(
    'ferric_oxide_potassiumn_1','ferric_oxide_potassiumv_1','ferric_oxide_samplew_1',
    'ferric_oxide_potassiumn_2','ferric_oxide_potassiumv_2','ferric_oxide_samplew_2',
    'ferric_oxide_potassiumn_3','ferric_oxide_potassiumv_3','ferric_oxide_samplew_3',
    'ferric_oxide_potassiumn_4','ferric_oxide_potassiumv_4','ferric_oxide_samplew_4',
    'ferric_oxide_potassiumn_5','ferric_oxide_potassiumv_5','ferric_oxide_samplew_5',
    )
    def _compute_ferric_oxide(self):
        for rec in self:

            rec.ferric_oxide_1 = (
                (79.85 * rec.ferric_oxide_potassiumn_1 * rec.ferric_oxide_potassiumv_1)
                / rec.ferric_oxide_samplew_1
            ) if rec.ferric_oxide_samplew_1 else 0.0

            rec.ferric_oxide_2 = (
                (79.85 * rec.ferric_oxide_potassiumn_2 * rec.ferric_oxide_potassiumv_2)
                / rec.ferric_oxide_samplew_2
            ) if rec.ferric_oxide_samplew_2 else 0.0

            rec.ferric_oxide_3 = (
                (79.85 * rec.ferric_oxide_potassiumn_3 * rec.ferric_oxide_potassiumv_3)
                / rec.ferric_oxide_samplew_3
            ) if rec.ferric_oxide_samplew_3 else 0.0

            rec.ferric_oxide_4 = (
                (79.85 * rec.ferric_oxide_potassiumn_4 * rec.ferric_oxide_potassiumv_4)
                / rec.ferric_oxide_samplew_4
            ) if rec.ferric_oxide_samplew_4 else 0.0

            rec.ferric_oxide_5 = (
                (79.85 * rec.ferric_oxide_potassiumn_5 * rec.ferric_oxide_potassiumv_5)
                / rec.ferric_oxide_samplew_5
            ) if rec.ferric_oxide_samplew_5 else 0.0


    avg_ferric_oxide_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_ferric_oxide_conformity", store=True)

    @api.depends('avg_ferric_oxide','eln_ref','grade')
    def _compute_avg_ferric_oxide_conformity(self):
            # remove this first when making changes
            self.avg_ferric_oxide_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_ferric_oxide_conformity = 'na'
                    continue

                record.avg_ferric_oxide_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','663011247-645d-4794-a0fd-3daa0124r00219987')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','663011247-645d-4794-a0fd-3daa0124r00219987')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_ferric_oxide - record.avg_ferric_oxide*mu_value
                        upper = record.avg_ferric_oxide + record.avg_ferric_oxide*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_ferric_oxide_conformity = 'pass'
                            break
                        else:
                            record.avg_ferric_oxide_conformity = 'fail'

    avg_ferric_oxide_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_ferric_oxide_nabl", store=True)

    @api.depends('avg_ferric_oxide','eln_ref','grade')
    def _compute_avg_ferric_oxide_nabl(self):
        # remove this first
        self.avg_ferric_oxide_nabl = 'fail'
        
        for record in self:
            record.avg_ferric_oxide_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','663011247-645d-4794-a0fd-3daa0124r00219987')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','663011247-645d-4794-a0fd-3daa0124r00219987')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_ferric_oxide - record.avg_ferric_oxide*mu_value
            upper = record.avg_ferric_oxide + record.avg_ferric_oxide*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_ferric_oxide_nabl = 'pass'
                break
            else:
                record.avg_ferric_oxide_nabl = 'fail'

    # ALUMINA OXIDE
    
    alumina_oxide_name = fields.Char("Name",default="ALUMINA OXIDE")
    alumina_oxide_visible = fields.Boolean("ALUMINA OXIDE",compute="_compute_visible")

    alumina_oxide_fe2o3_1 = fields.Float(string="Percentage Of Ferric Oxide (Fe2O3)",compute="_compute_alumina_fe2o3", store=True)
    alumina_oxide_fe2o3_2 = fields.Float(string="Percentage Of Ferric Oxide (Fe2O3)",compute="_compute_alumina_fe2o3", store=True)
    alumina_oxide_fe2o3_3 = fields.Float(string="Percentage Of Ferric Oxide (Fe2O3)",compute="_compute_alumina_fe2o3", store=True)
    alumina_oxide_fe2o3_4 = fields.Float(string="Percentage Of Ferric Oxide (Fe2O3)",compute="_compute_alumina_fe2o3", store=True)
    alumina_oxide_fe2o3_5 = fields.Float(string="Percentage Of Ferric Oxide (Fe2O3)",compute="_compute_alumina_fe2o3", store=True)

    al2o3_1 = fields.Float(string="Al2O3",store=True)
    al2o3_2 = fields.Float(string="Al2O3 ",store=True)
    al2o3_3 = fields.Float(string="Al2O3",store=True)
    al2o3_4 = fields.Float(string="Al2O3",store=True)
    al2o3_5 = fields.Float(string="Al2O3",store=True)


    

    alumina_oxide_1 = fields.Float(string="Alumina Oxide (Al2O3)  %",store=True)
    alumina_oxide_2 = fields.Float(string="Alumina Oxide (Al2O3)  %"  ,store=True)
    alumina_oxide_3 = fields.Float(string="Alumina Oxide (Al2O3)  %"  ,store=True)
    alumina_oxide_4 = fields.Float(string="Alumina Oxide (Al2O3)  %"   ,store=True)
    alumina_oxide_5 = fields.Float(string="Alumina Oxide (Al2O3)  %"  ,store=True)

    avg_alumina_oxide = fields.Float(string="Average Alumina Oxide % ", store=True)


    @api.depends(
    'ferric_oxide_1',
    'ferric_oxide_2',
    'ferric_oxide_3',
    'ferric_oxide_4',
    'ferric_oxide_5'
    )
    def _compute_alumina_fe2o3(self):
        for rec in self:

            rec.alumina_oxide_fe2o3_1 = rec.ferric_oxide_1 or 0.0
            rec.alumina_oxide_fe2o3_2 = rec.ferric_oxide_2 or 0.0
            rec.alumina_oxide_fe2o3_3 = rec.ferric_oxide_3 or 0.0
            rec.alumina_oxide_fe2o3_4 = rec.ferric_oxide_4 or 0.0
            rec.alumina_oxide_fe2o3_5 = rec.ferric_oxide_5 or 0.0

    @api.depends(
    'alumina_oxide_fe2o3_1','alumina_oxide_fe2o3_2','alumina_oxide_fe2o3_3',
    'alumina_oxide_fe2o3_4','alumina_oxide_fe2o3_5',
    'al2o3_1','al2o3_2','al2o3_3','al2o3_4','al2o3_5'
    )
    def _compute_alumina_fe2o3(self):
        for rec in self:
            rec.alumina_oxide_1 = ((rec.alumina_oxide_fe2o3_1 + rec.al2o3_1) - rec.alumina_oxide_fe2o3_1)
            rec.alumina_oxide_2 = ((rec.alumina_oxide_fe2o3_2 + rec.al2o3_2) - rec.alumina_oxide_fe2o3_2)
            rec.alumina_oxide_3 = ((rec.alumina_oxide_fe2o3_3 + rec.al2o3_3) - rec.alumina_oxide_fe2o3_3)
            rec.alumina_oxide_4 = ((rec.alumina_oxide_fe2o3_4 + rec.al2o3_4) - rec.alumina_oxide_fe2o3_4)
            rec.alumina_oxide_5 = ((rec.alumina_oxide_fe2o3_5 + rec.al2o3_5) - rec.alumina_oxide_fe2o3_5)

    @api.depends(
    'alumina_oxide_1','alumina_oxide_2','alumina_oxide_3',
    'alumina_oxide_4','alumina_oxide_5'
    )
    def _compute_avg_alumina(self):
        for rec in self:
            rec.avg_alumina_oxide = (
                rec.alumina_oxide_1 +
                rec.alumina_oxide_2 +
                rec.alumina_oxide_3 +
                rec.alumina_oxide_4 +
                rec.alumina_oxide_5
            ) / 5


    avg_alumina_oxide_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_alumina_oxide_conformity", store=True)

    @api.depends('avg_alumina_oxide','eln_ref','grade')
    def _compute_avg_alumina_oxide_conformity(self):
            # remove this first when making changes
            self.avg_alumina_oxide_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_alumina_oxide_conformity = 'na'
                    continue

                record.avg_alumina_oxide_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','88835789b-645d-4794-a0fd-3daa0124r00219914')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','88835789b-645d-4794-a0fd-3daa0124r00219914')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_alumina_oxide - record.avg_alumina_oxide*mu_value
                        upper = record.avg_alumina_oxide + record.avg_alumina_oxide*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_alumina_oxide_conformity = 'pass'
                            break
                        else:
                            record.avg_alumina_oxide_conformity = 'fail'

    avg_alumina_oxide_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_alumina_oxide_nabl", store=True)

    @api.depends('avg_alumina_oxide','eln_ref','grade')
    def _compute_avg_alumina_oxide_nabl(self):
        # remove this first
        self.avg_alumina_oxide_nabl = 'fail'
        
        for record in self:
            record.avg_alumina_oxide_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','88835789b-645d-4794-a0fd-3daa0124r00219914')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','88835789b-645d-4794-a0fd-3daa0124r00219914')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_alumina_oxide - record.avg_alumina_oxide*mu_value
            upper = record.avg_alumina_oxide + record.avg_alumina_oxide*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_alumina_oxide_nabl = 'pass'
                break
            else:
                record.avg_alumina_oxide_nabl = 'fail'

    #  MAGNESIA (MgO)
    
    magnesia_name = fields.Char("Name",default="MAGNESIA (MgO)")
    magnesia_visible = fields.Boolean("MAGNESIA (MgO)",compute="_compute_visible")

    magnesia_samplew_1 = fields.Float(string="Weight of sample taken in gm.(W)")
    magnesia_samplew_2 = fields.Float(string="Weight of sample taken in gm.(W)")
    magnesia_samplew_3 = fields.Float(string="Weight of sample taken in gm.(W)")
    magnesia_samplew_4 = fields.Float(string="Weight of sample taken in gm.(W)")
    magnesia_samplew_5 = fields.Float(string="Weight of sample taken in gm.(W)")

    magnesia_cruciblew1_1 = fields.Float(string="Weight of empty crucible (W1)")
    magnesia_cruciblew1_2 = fields.Float(string="Weight of empty crucible (W1)")
    magnesia_cruciblew1_3 = fields.Float(string="Weight of empty crucible (W1)")
    magnesia_cruciblew1_4 = fields.Float(string="Weight of empty crucible (W1)")
    magnesia_cruciblew1_5 = fields.Float(string="Weight of empty crucible (W1)")

    magnesia_cruciblew2_1 = fields.Float(string="Weight of crucible + residue (W2)")
    magnesia_cruciblew2_2 = fields.Float(string="Weight of crucible + residue (W2)")
    magnesia_cruciblew2_3 = fields.Float(string="Weight of crucible + residue (W2)" )
    magnesia_cruciblew2_4 = fields.Float(string="Weight of crucible + residue (W2)" )
    magnesia_cruciblew2_5 = fields.Float(string="Weight of crucible + residue (W2)" )

    
    

    magnesia_1 = fields.Float(string="Magnesia (MgO) %",compute="_compute_magnesia",store=True)
    magnesia_2 = fields.Float(string="Magnesia (MgO) %"  , compute="_compute_magnesia",store=True)
    magnesia_3 = fields.Float(string="Magnesia (MgO) %"  , compute="_compute_magnesia",store=True)
    magnesia_4 = fields.Float(string="Magnesia (MgO) %"   , compute="_compute_magnesia",store=True)
    magnesia_5 = fields.Float(string="Magnesia (MgO) %"  , compute="_compute_magnesia",store=True)

    avg_magnesia = fields.Float(string="Average Magnesia % ",compute="_compute_avg_magnesia", store=True)

    @api.depends(
    'magnesia_samplew_1','magnesia_samplew_2','magnesia_samplew_3','magnesia_samplew_4','magnesia_samplew_5',
    'magnesia_cruciblew1_1','magnesia_cruciblew1_2','magnesia_cruciblew1_3','magnesia_cruciblew1_4','magnesia_cruciblew1_5',
    'magnesia_cruciblew2_1','magnesia_cruciblew2_2','magnesia_cruciblew2_3','magnesia_cruciblew2_4','magnesia_cruciblew2_5'
    )
    def _compute_magnesia(self):
        for rec in self:

            rec.magnesia_1 = ((rec.magnesia_cruciblew2_1 - rec.magnesia_cruciblew1_1) * 36.2) / rec.magnesia_samplew_1 if rec.magnesia_samplew_1 else 0.0

            rec.magnesia_2 = ((rec.magnesia_cruciblew2_2 - rec.magnesia_cruciblew1_2) * 36.2) / rec.magnesia_samplew_2 if rec.magnesia_samplew_2 else 0.0

            rec.magnesia_3 = ((rec.magnesia_cruciblew2_3 - rec.magnesia_cruciblew1_3) * 36.2) / rec.magnesia_samplew_3 if rec.magnesia_samplew_3 else 0.0

            rec.magnesia_4 = ((rec.magnesia_cruciblew2_4 - rec.magnesia_cruciblew1_4) * 36.2) / rec.magnesia_samplew_4 if rec.magnesia_samplew_4 else 0.0

            rec.magnesia_5 = ((rec.magnesia_cruciblew2_5 - rec.magnesia_cruciblew1_5) * 36.2) / rec.magnesia_samplew_5 if rec.magnesia_samplew_5 else 0.0


    @api.depends(
    'magnesia_1','magnesia_2','magnesia_3','magnesia_4','magnesia_5'
    )
    def _compute_avg_magnesia(self):
        for rec in self:
            rec.avg_magnesia = (
                rec.magnesia_1 +
                rec.magnesia_2 +
                rec.magnesia_3 +
                rec.magnesia_4 +
                rec.magnesia_5
            ) / 5


    avg_magnesia_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_magnesia_conformity", store=True)

    @api.depends('avg_magnesia','eln_ref','grade')
    def _compute_avg_magnesia_conformity(self):
            # remove this first when making changes
            self.avg_magnesia_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_magnesia_conformity = 'na'
                    continue

                record.avg_magnesia_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','33344ffrdb-645d-4794-a0fd-3daa0124r002rrtt64')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','33344ffrdb-645d-4794-a0fd-3daa0124r002rrtt64')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_magnesia - record.avg_magnesia*mu_value
                        upper = record.avg_magnesia + record.avg_magnesia*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_magnesia_conformity = 'pass'
                            break
                        else:
                            record.avg_magnesia_conformity = 'fail'

    avg_magnesia_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_magnesia_nabl", store=True)

    @api.depends('avg_magnesia','eln_ref','grade')
    def _compute_avg_magnesia_nabl(self):
        # remove this first
        self.avg_magnesia_nabl = 'fail'
        
        for record in self:
            record.avg_magnesia_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','33344ffrdb-645d-4794-a0fd-3daa0124r002rrtt64')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','33344ffrdb-645d-4794-a0fd-3daa0124r002rrtt64')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_magnesia - record.avg_magnesia*mu_value
            upper = record.avg_magnesia + record.avg_magnesia*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_magnesia_nabl = 'pass'
                break
            else:
                record.avg_magnesia_nabl = 'fail'


    # CALCIUM OXIDE (CaO)
    
    calcium_oxide_name = fields.Char("Name",default="CALCIUM OXIDE (CaO)")
    calcium_oxide_visible = fields.Boolean("CALCIUM OXIDE (CaO)",compute="_compute_visible")

    calcium_oxide_samplew_1 = fields.Float(string="Weight of sample taken in gm.(W)")
    calcium_oxide_samplew_2 = fields.Float(string="Weight of sample taken in gm.(W)")
    calcium_oxide_samplew_3 = fields.Float(string="Weight of sample taken in gm.(W)")
    calcium_oxide_samplew_4 = fields.Float(string="Weight of sample taken in gm.(W)")
    calcium_oxide_samplew_5 = fields.Float(string="Weight of sample taken in gm.(W)")

    calcium_oxide_cruciblew1_1 = fields.Float(string="Weight of empty crucible (W1)")
    calcium_oxide_cruciblew1_2 = fields.Float(string="Weight of empty crucible (W1)")
    calcium_oxide_cruciblew1_3 = fields.Float(string="Weight of empty crucible (W1)")
    calcium_oxide_cruciblew1_4 = fields.Float(string="Weight of empty crucible (W1)")
    calcium_oxide_cruciblew1_5 = fields.Float(string="Weight of empty crucible (W1)")

    calcium_oxide_cruciblew2_1 = fields.Float(string="Weight of crucible + residue (W2)")
    calcium_oxide_cruciblew2_2 = fields.Float(string="Weight of crucible + residue (W2)")
    calcium_oxide_cruciblew2_3 = fields.Float(string="Weight of crucible + residue (W2)" )
    calcium_oxide_cruciblew2_4 = fields.Float(string="Weight of crucible + residue (W2)" )
    calcium_oxide_cruciblew2_5 = fields.Float(string="Weight of crucible + residue (W2)" )

    
    

    calcium_oxide_1 = fields.Float(string="Calcium Oxide(CaO) %",compute="_compute_calcium_oxide",store=True)
    calcium_oxide_2 = fields.Float(string="Calcium Oxide(CaO) %",compute="_compute_calcium_oxide",store=True)
    calcium_oxide_3 = fields.Float(string="Calcium Oxide(CaO) %",compute="_compute_calcium_oxide",store=True)
    calcium_oxide_4 = fields.Float(string="Calcium Oxide(CaO) %" ,compute="_compute_calcium_oxide",store=True)
    calcium_oxide_5 = fields.Float(string="Calcium Oxide(CaO) %",compute="_compute_calcium_oxide",store=True)

    avg_calcium_oxide = fields.Float(string="Average Calcium Oxide(CaO) % ",compute="_compute_avg_calcium_oxide", store=True)

    @api.depends(
    'calcium_oxide_1','calcium_oxide_2','calcium_oxide_3',
    'calcium_oxide_4','calcium_oxide_5'
    )
    def _compute_avg_calcium_oxide(self):
        for rec in self:
            rec.avg_calcium_oxide = (
                rec.calcium_oxide_1 +
                rec.calcium_oxide_2 +
                rec.calcium_oxide_3 +
                rec.calcium_oxide_4 +
                rec.calcium_oxide_5
            ) / 5



    @api.depends(
    'calcium_oxide_samplew_1','calcium_oxide_samplew_2','calcium_oxide_samplew_3','calcium_oxide_samplew_4','calcium_oxide_samplew_5',
    'calcium_oxide_cruciblew1_1','calcium_oxide_cruciblew1_2','calcium_oxide_cruciblew1_3','calcium_oxide_cruciblew1_4','calcium_oxide_cruciblew1_5',
    'calcium_oxide_cruciblew2_1','calcium_oxide_cruciblew2_2','calcium_oxide_cruciblew2_3','calcium_oxide_cruciblew2_4','calcium_oxide_cruciblew2_5'
    )
    def _compute_calcium_oxide(self):
        for rec in self:

            rec.calcium_oxide_1 = ((rec.calcium_oxide_cruciblew2_1 - rec.calcium_oxide_cruciblew1_1) * 100) / rec.calcium_oxide_samplew_1 if rec.calcium_oxide_samplew_1 else 0.0

            rec.calcium_oxide_2 = ((rec.calcium_oxide_cruciblew2_2 - rec.calcium_oxide_cruciblew1_2) * 100) / rec.calcium_oxide_samplew_2 if rec.calcium_oxide_samplew_2 else 0.0

            rec.calcium_oxide_3 = ((rec.calcium_oxide_cruciblew2_3 - rec.calcium_oxide_cruciblew1_3) * 100) / rec.calcium_oxide_samplew_3 if rec.calcium_oxide_samplew_3 else 0.0

            rec.calcium_oxide_4 = ((rec.calcium_oxide_cruciblew2_4 - rec.calcium_oxide_cruciblew1_4) * 100) / rec.calcium_oxide_samplew_4 if rec.calcium_oxide_samplew_4 else 0.0

            rec.calcium_oxide_5 = ((rec.calcium_oxide_cruciblew2_5 - rec.calcium_oxide_cruciblew1_5) * 100) / rec.calcium_oxide_samplew_5 if rec.calcium_oxide_samplew_5 else 0.0


    avg_calcium_oxide_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_calcium_oxide_conformity", store=True)

    @api.depends('avg_calcium_oxide','eln_ref','grade')
    def _compute_avg_calcium_oxide_conformity(self):
            # remove this first when making changes
            self.avg_calcium_oxide_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_calcium_oxide_conformity = 'na'
                    continue

                record.avg_calcium_oxide_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','66622114vbf-645d-4794-a0fd-3daa0124r002rrtt78')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','66622114vbf-645d-4794-a0fd-3daa0124r002rrtt78')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_calcium_oxide - record.avg_calcium_oxide*mu_value
                        upper = record.avg_calcium_oxide + record.avg_calcium_oxide*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_calcium_oxide_conformity = 'pass'
                            break
                        else:
                            record.avg_calcium_oxide_conformity = 'fail'

    avg_calcium_oxide_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_calcium_oxide_nabl", store=True)

    @api.depends('avg_calcium_oxide','eln_ref','grade')
    def _compute_avg_calcium_oxide_nabl(self):
        # remove this first
        self.avg_calcium_oxide_nabl = 'fail'
        
        for record in self:
            record.avg_calcium_oxide_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','66622114vbf-645d-4794-a0fd-3daa0124r002rrtt78')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','66622114vbf-645d-4794-a0fd-3daa0124r002rrtt78')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_calcium_oxide - record.avg_calcium_oxide*mu_value
            upper = record.avg_calcium_oxide + record.avg_calcium_oxide*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_calcium_oxide_nabl = 'pass'
                break
            else:
                record.avg_calcium_oxide_nabl = 'fail'

    # SULPHURIC ANHYDRIDE (SO3)
    
    sulpuric_so3_name = fields.Char("Name",default="SULPHURIC ANHYDRIDE (SO3)")
    sulpuric_so3_visible = fields.Boolean("SULPHURIC ANHYDRIDE (SO3)",compute="_compute_visible")

    sulpuric_so3_samplew_1 = fields.Float(string="Wt. Of Sample taken(W)")
    sulpuric_so3_samplew_2 = fields.Float(string="Wt. Of Sample taken(W)")
    sulpuric_so3_samplew_3 = fields.Float(string="Wt. Of Sample taken(W)")
    sulpuric_so3_samplew_4 = fields.Float(string="Wt. Of Sample taken(W)")
    sulpuric_so3_samplew_5 = fields.Float(string="Wt. Of Sample taken(W)")

    sulpuric_so3_cruciblew1_1 = fields.Float(string="Wt. Of empty crucible(W1)")
    sulpuric_so3_cruciblew1_2 = fields.Float(string="Wt. Of empty crucible(W1)")
    sulpuric_so3_cruciblew1_3 = fields.Float(string="Wt. Of empty crucible(W1)")
    sulpuric_so3_cruciblew1_4 = fields.Float(string="Wt. Of empty crucible(W1)")
    sulpuric_so3_cruciblew1_5 = fields.Float(string="Wt. Of empty crucible(W1)")

    sulpuric_so3_cruciblew2_1 = fields.Float(string="Wt. Of crucible+ residue(W2)")
    sulpuric_so3_cruciblew2_2 = fields.Float(string="Wt. Of crucible+ residue(W2)")
    sulpuric_so3_cruciblew2_3 = fields.Float(string="Wt. Of crucible+ residue(W2)" )
    sulpuric_so3_cruciblew2_4 = fields.Float(string="Wt. Of crucible+ residue(W2)" )
    sulpuric_so3_cruciblew2_5 = fields.Float(string="Wt. Of crucible+ residue(W2)" )

    
    

    sulpuric_so3_1 = fields.Float(string="SO3 %",compute="_compute_sulpuric_so3",store=True)
    sulpuric_so3_2 = fields.Float(string="SO3 %",compute="_compute_sulpuric_so3",store=True)
    sulpuric_so3_3 = fields.Float(string="SO3 %",compute="_compute_sulpuric_so3",store=True)
    sulpuric_so3_4 = fields.Float(string="SO3 %" ,compute="_compute_sulpuric_so3",store=True)
    sulpuric_so3_5 = fields.Float(string="SO3 %",compute="_compute_sulpuric_so3",store=True)

    avg_sulpuric_so3 = fields.Float(string="Average SO3 % ",compute="_compute_avg_sulpuric_so3", store=True)

    @api.depends(
    'sulpuric_so3_1','sulpuric_so3_2','sulpuric_so3_3',
    'sulpuric_so3_4','sulpuric_so3_5'
    )
    def _compute_avg_sulpuric_so3(self):
        for rec in self:
            rec.avg_sulpuric_so3 = (
                rec.sulpuric_so3_1 +
                rec.sulpuric_so3_2 +
                rec.sulpuric_so3_3 +
                rec.sulpuric_so3_4 +
                rec.sulpuric_so3_5
            ) / 5


    @api.depends(
    'sulpuric_so3_samplew_1','sulpuric_so3_samplew_2','sulpuric_so3_samplew_3','sulpuric_so3_samplew_4','sulpuric_so3_samplew_5',
    'sulpuric_so3_cruciblew1_1','sulpuric_so3_cruciblew1_2','sulpuric_so3_cruciblew1_3','sulpuric_so3_cruciblew1_4','sulpuric_so3_cruciblew1_5',
    'sulpuric_so3_cruciblew2_1','sulpuric_so3_cruciblew2_2','sulpuric_so3_cruciblew2_3','sulpuric_so3_cruciblew2_4','sulpuric_so3_cruciblew2_5'
    )
    def _compute_sulpuric_so3(self):
        for rec in self:

            rec.sulpuric_so3_1 = ((rec.sulpuric_so3_cruciblew2_1 - rec.sulpuric_so3_cruciblew1_1) / rec.sulpuric_so3_samplew_1) * 34.3 if rec.sulpuric_so3_samplew_1 else 0.0

            rec.sulpuric_so3_2 = ((rec.sulpuric_so3_cruciblew2_2 - rec.sulpuric_so3_cruciblew1_2) / rec.sulpuric_so3_samplew_2) * 34.3 if rec.sulpuric_so3_samplew_2 else 0.0

            rec.sulpuric_so3_3 = ((rec.sulpuric_so3_cruciblew2_3 - rec.sulpuric_so3_cruciblew1_3) / rec.sulpuric_so3_samplew_3) * 34.3 if rec.sulpuric_so3_samplew_3 else 0.0

            rec.sulpuric_so3_4 = ((rec.sulpuric_so3_cruciblew2_4 - rec.sulpuric_so3_cruciblew1_4) / rec.sulpuric_so3_samplew_4) * 34.3 if rec.sulpuric_so3_samplew_4 else 0.0

            rec.sulpuric_so3_5 = ((rec.sulpuric_so3_cruciblew2_5 - rec.sulpuric_so3_cruciblew1_5) / rec.sulpuric_so3_samplew_5) * 34.3 if rec.sulpuric_so3_samplew_5 else 0.0


    avg_sulpuric_so3_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_sulpuric_so3_conformity", store=True)

    @api.depends('avg_sulpuric_so3','eln_ref','grade')
    def _compute_avg_sulpuric_so3_conformity(self):
            # remove this first when making changes
            self.avg_sulpuric_so3_conformity = 'fail'
        
            for record in self:

                if not record.eln_ref or not record.eln_ref.conformity:
                    record.avg_sulpuric_so3_conformity = 'na'
                    continue

                record.avg_sulpuric_so3_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','66554477vbv-645d-4794-a0fd-3daa0124r002332214')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','66554477vbv-645d-4794-a0fd-3daa0124r002332214')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.avg_sulpuric_so3 - record.avg_sulpuric_so3*mu_value
                        upper = record.avg_sulpuric_so3 + record.avg_sulpuric_so3*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.avg_sulpuric_so3_conformity = 'pass'
                            break
                        else:
                            record.avg_sulpuric_so3_conformity = 'fail'

    avg_sulpuric_so3_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_sulpuric_so3_nabl", store=True)

    @api.depends('avg_sulpuric_so3','eln_ref','grade')
    def _compute_avg_sulpuric_so3_nabl(self):
        # remove this first
        self.avg_sulpuric_so3_nabl = 'fail'
        
        for record in self:
            record.avg_sulpuric_so3_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','66554477vbv-645d-4794-a0fd-3daa0124r002332214')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','66554477vbv-645d-4794-a0fd-3daa0124r002332214')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_sulpuric_so3 - record.avg_sulpuric_so3*mu_value
            upper = record.avg_sulpuric_so3 + record.avg_sulpuric_so3*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_sulpuric_so3_nabl = 'pass'
                break
            else:
                record.avg_sulpuric_so3_nabl = 'fail'










   

    @api.depends('sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.loass_ingnition_visible = False
            record.silica_visible = False
            record.ferric_alumina_visible = False
            record.ferric_oxide_visible = False
            record.alumina_oxide_visible = False
            record.magnesia_visible = False
            record.calcium_oxide_visible = False
            record.sulpuric_so3_visible = False
        
            
          

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
               
                if sample.internal_id == '333114425-645d-4794-a0fd-3daa0124r0021478':
                    record.loass_ingnition_visible = True
                if sample.internal_id == '666557788ttn-645d-4794-a0fd-3daa0124r0021478':
                    record.silica_visible = True
                
                if sample.internal_id == '665478grtvb-645d-4794-a0fd-3daa0124r0021478':
                    record.ferric_alumina_visible = True

                if sample.internal_id == '663011247-645d-4794-a0fd-3daa0124r00219987':
                    record.ferric_oxide_visible = True
                
                if sample.internal_id == '88835789b-645d-4794-a0fd-3daa0124r00219914':
                    record.alumina_oxide_visible = True

                if sample.internal_id == '33344ffrdb-645d-4794-a0fd-3daa0124r002rrtt64':
                    record.magnesia_visible = True

                if sample.internal_id == '66622114vbf-645d-4794-a0fd-3daa0124r002rrtt78':
                    record.calcium_oxide_visible = True

                if sample.internal_id == '66554477vbv-645d-4794-a0fd-3daa0124r002332214':
                    record.sulpuric_so3_visible = True


              

                




    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

        
            if result.parameter.internal_id == '333114425-645d-4794-a0fd-3daa0124r0021478':
                result.result_char = round(self.avg_loass_ingnition,2)
                result.calculated = True
                if self.avg_loass_ingnition_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '666557788ttn-645d-4794-a0fd-3daa0124r0021478':
                result.result_char = round(self.avg_silica,2)
                result.calculated = True
                if self.avg_silica_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '665478grtvb-645d-4794-a0fd-3daa0124r0021478':
                result.result_char = round(self.avg_ferric_alumina,2)
                result.calculated = True
                if self.avg_ferric_alumina_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '663011247-645d-4794-a0fd-3daa0124r00219987':
                result.result_char = round(self.avg_ferric_oxide,2)
                result.calculated = True
                if self.avg_ferric_oxide_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '88835789b-645d-4794-a0fd-3daa0124r00219914':
                result.result_char = round(self.avg_alumina_oxide,2)
                result.calculated = True
                if self.avg_alumina_oxide_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '33344ffrdb-645d-4794-a0fd-3daa0124r002rrtt64':
                result.result_char = round(self.avg_magnesia,2)
                result.calculated = True
                if self.avg_magnesia_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '66622114vbf-645d-4794-a0fd-3daa0124r002rrtt78':
                result.result_char = round(self.avg_calcium_oxide,2)
                result.calculated = True
                if self.avg_calcium_oxide_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '66554477vbv-645d-4794-a0fd-3daa0124r002332214':
                result.result_char = round(self.avg_sulpuric_so3,2)
                result.calculated = True
                if self.avg_sulpuric_so3_nabl == 'pass':
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
        record = super(ChemicalFlyAsh, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


        
    def get_all_fields(self):
        record = self.env['chemical.fly.ash'].browse(self.ids[0])
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








class ChemFlyAshNotes(models.Model):
    _name = "chem.fly.ash.notes"

    parent_id = fields.Many2one('chemical.fly.ash',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
    