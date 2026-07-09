from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class MechanicalAluminumAlloys(models.Model):
    _name = "mechanical.aluminum.alloys"
    _inherit = "lerm.eln"
    _rec_name = "name2"

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    name2 = fields.Char("Name",default="Aluminum & its alloys")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    temprature = fields.Integer("Temperature (°C)", digits=(10,2))
    humidity = fields.Integer("Humidity (%)", digits=(10,2))

    week_no = fields.Char("Week No")

    other_details = fields.Char("Other Details")

    condition = fields.Char("Condition")
    product_name = fields.Char("Product Name")

    description_work = fields.Text("Description Of Work")

    notes_id = fields.One2many('aluminum.alloys.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(MechanicalAluminumAlloys, self).default_get(fields)

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



    reduction_area_visible = fields.Boolean("% Reduction in Area Visible",compute="_compute_visible")
    reduction_area_name = fields.Char("Name",default="% Reduction in Area - (ASTM B557:2015: 2023)")
    reduction_in_area_percent = fields.Float(string="% Reduction in Area")

    reduction_in_area_percent_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_reduction_in_area_percent_conformity")

    reduction_in_area_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_reduction_in_area_percent_nabl")


    @api.depends('reduction_in_area_percent','eln_ref','grade')
    def _compute_reduction_in_area_percent_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.reduction_in_area_percent_conformity = 'na'
                continue
            record.reduction_in_area_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poi56784-107d-4e30-9d3d-2a096785432g')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poi56784-107d-4e30-9d3d-2a096785432g')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.reduction_in_area_percent - record.reduction_in_area_percent*mu_value
                    upper = record.reduction_in_area_percent + record.reduction_in_area_percent*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.reduction_in_area_percent_conformity = 'pass'
                        break
                    else:
                        record.reduction_in_area_percent_conformity = 'fail'

    @api.depends('reduction_in_area_percent','eln_ref','grade')
    def _compute_reduction_in_area_percent_nabl(self):
        
        for record in self:
            
            record.reduction_in_area_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poi56784-107d-4e30-9d3d-2a096785432g')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poi56784-107d-4e30-9d3d-2a096785432g')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.reduction_in_area_percent - record.reduction_in_area_percent*mu_value
            upper = record.reduction_in_area_percent + record.reduction_in_area_percent*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.reduction_in_area_percent_nabl = 'pass'
                break
            else:
                record.reduction_in_area_percent_nabl = 'fail'

    reduction_area_visible1 = fields.Boolean("% Reduction in Area Visible",compute="_compute_visible")
    reduction_area_name1 = fields.Char("Name",default="% Reduction in Area - (ISO 6892 (Part 1): 2019: 2019)")
    reduction_in_area_percent1 = fields.Float(string="% Reduction in Area")

    reduction_in_area_percent1_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_reduction_in_area_percent1_conformity")

    reduction_in_area_percent1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_reduction_in_area_percent1_nabl")


    @api.depends('reduction_in_area_percent1','eln_ref','grade')
    def _compute_reduction_in_area_percent1_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.reduction_in_area_percent1_conformity = 'na'
                continue
            record.reduction_in_area_percent1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','654rt4325-107d-4e30-9d3d-2aiu45634237')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','654rt4325-107d-4e30-9d3d-2aiu45634237')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.reduction_in_area_percent1 - record.reduction_in_area_percent1*mu_value
                    upper = record.reduction_in_area_percent1 + record.reduction_in_area_percent1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.reduction_in_area_percent1_conformity = 'pass'
                        break
                    else:
                        record.reduction_in_area_percent1_conformity = 'fail'

    @api.depends('reduction_in_area_percent1','eln_ref','grade')
    def _compute_reduction_in_area_percent1_nabl(self):
        
        for record in self:
            
            record.reduction_in_area_percent1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','654rt4325-107d-4e30-9d3d-2aiu45634237')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','654rt4325-107d-4e30-9d3d-2aiu45634237')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.reduction_in_area_percent1 - record.reduction_in_area_percent1*mu_value
            upper = record.reduction_in_area_percent1 + record.reduction_in_area_percent1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.reduction_in_area_percent1_nabl = 'pass'
                break
            else:
                record.reduction_in_area_percent1_nabl = 'fail'

    reduction_area_visible2 = fields.Boolean("% Reduction in Area Visible",compute="_compute_visible")
    reduction_area_name2 = fields.Char("Name",default="% Reduction in Area - (ASTM E8/E8M: 2022)")
    reduction_in_area_percent2 = fields.Float(string="% Reduction in Area")

    reduction_in_area_percent2_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_reduction_in_area_percent2_conformity")

    reduction_in_area_percent2_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_reduction_in_area_percent2_nabl")


    @api.depends('reduction_in_area_percent2','eln_ref','grade')
    def _compute_reduction_in_area_percent2_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.reduction_in_area_percent2_conformity = 'na'
                continue
            record.reduction_in_area_percent2_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5754ert342-107d-4e30-9d3d-2a9864532345')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5754ert342-107d-4e30-9d3d-2a9864532345')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.reduction_in_area_percent2 - record.reduction_in_area_percent2*mu_value
                    upper = record.reduction_in_area_percent2 + record.reduction_in_area_percent2*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.reduction_in_area_percent2_conformity = 'pass'
                        break
                    else:
                        record.reduction_in_area_percent2_conformity = 'fail'

    @api.depends('reduction_in_area_percent2','eln_ref','grade')
    def _compute_reduction_in_area_percent2_nabl(self):
        
        for record in self:
            
            record.reduction_in_area_percent2_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5754ert342-107d-4e30-9d3d-2a9864532345')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5754ert342-107d-4e30-9d3d-2a9864532345')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.reduction_in_area_percent2 - record.reduction_in_area_percent2*mu_value
            upper = record.reduction_in_area_percent2 + record.reduction_in_area_percent2*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.reduction_in_area_percent2_nabl = 'pass'
                break
            else:
                record.reduction_in_area_percent2_nabl = 'fail'


    proof_stress_visible = fields.Boolean("0.2% Proof Stress Visible",compute="_compute_visible")
    proof_stress_name = fields.Char("Name",default="0.2% Proof Stress - (ASTM B557:2015: 2023)")
    proof_stress_0_2_percent = fields.Float(string="0.2% Proof Stress")

    proof_stress_0_2_percent_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_proof_stress_0_2_percent_conformity")

    proof_stress_0_2_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_proof_stress_0_2_percent_nabl")


    @api.depends('proof_stress_0_2_percent','eln_ref','grade')
    def _compute_proof_stress_0_2_percent_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.proof_stress_0_2_percent_conformity = 'na'
                continue
            record.proof_stress_0_2_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','murt4563-107d-4e30-9d3d-2a9p0456321we')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','murt4563-107d-4e30-9d3d-2a9p0456321we')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.proof_stress_0_2_percent - record.proof_stress_0_2_percent*mu_value
                    upper = record.proof_stress_0_2_percent + record.proof_stress_0_2_percent*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.proof_stress_0_2_percent_conformity = 'pass'
                        break
                    else:
                        record.proof_stress_0_2_percent_conformity = 'fail'

    @api.depends('proof_stress_0_2_percent','eln_ref','grade')
    def _compute_proof_stress_0_2_percent_nabl(self):
        
        for record in self:
            
            record.proof_stress_0_2_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','murt4563-107d-4e30-9d3d-2a9p0456321we')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','murt4563-107d-4e30-9d3d-2a9p0456321we')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.proof_stress_0_2_percent - record.proof_stress_0_2_percent*mu_value
            upper = record.proof_stress_0_2_percent + record.proof_stress_0_2_percent*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.proof_stress_0_2_percent_nabl = 'pass'
                break
            else:
                record.proof_stress_0_2_percent_nabl = 'fail'

    proof_stress_visible1 = fields.Boolean("0.2% Proof Stress Visible",compute="_compute_visible")
    proof_stress_name1 = fields.Char("Name",default="0.2% Proof Stress - (ISO 6892 (Part 1): 2019: 2019)")
    proof_stress_0_2_percent1 = fields.Float(string="0.2% Proof Stress")

    proof_stress_0_2_percent1_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_proof_stress_0_2_percent1_conformity")

    proof_stress_0_2_percent1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_proof_stress_0_2_percent1_nabl")


    @api.depends('proof_stress_0_2_percent1','eln_ref','grade')
    def _compute_proof_stress_0_2_percent1_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.proof_stress_0_2_percent1_conformity = 'na'
                continue
            record.proof_stress_0_2_percent1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','port54321d-107d-4e30-9d3d-2a9o456tyr345')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','port54321d-107d-4e30-9d3d-2a9o456tyr345')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.proof_stress_0_2_percent1 - record.proof_stress_0_2_percent1*mu_value
                    upper = record.proof_stress_0_2_percent1 + record.proof_stress_0_2_percent1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.proof_stress_0_2_percent1_conformity = 'pass'
                        break
                    else:
                        record.proof_stress_0_2_percent1_conformity = 'fail'

    @api.depends('proof_stress_0_2_percent1','eln_ref','grade')
    def _compute_proof_stress_0_2_percent1_nabl(self):
        
        for record in self:
            
            record.proof_stress_0_2_percent1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','port54321d-107d-4e30-9d3d-2a9o456tyr345')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','port54321d-107d-4e30-9d3d-2a9o456tyr345')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.proof_stress_0_2_percent1 - record.proof_stress_0_2_percent1*mu_value
            upper = record.proof_stress_0_2_percent1 + record.proof_stress_0_2_percent1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.proof_stress_0_2_percent1_nabl = 'pass'
                break
            else:
                record.proof_stress_0_2_percent1_nabl = 'fail'

    proof_stress_visible2 = fields.Boolean("0.2% Proof Stress Visible",compute="_compute_visible")
    proof_stress_name2 = fields.Char("Name",default="0.2% Proof Stress - (ASTM E8/E8M: 2022)")
    proof_stress_0_2_percent2 = fields.Float(string="0.2% Proof Stress")

    proof_stress_0_2_percent2_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_proof_stress_0_2_percent2_conformity")

    proof_stress_0_2_percent2_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_proof_stress_0_2_percent2_nabl")


    @api.depends('proof_stress_0_2_percent2','eln_ref','grade')
    def _compute_proof_stress_0_2_percent2_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.proof_stress_0_2_percent2_conformity = 'na'
                continue
            record.proof_stress_0_2_percent2_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poit56745-107d-4e30-9d3d-2a94567432erth6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poit56745-107d-4e30-9d3d-2a94567432erth6')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.proof_stress_0_2_percent2 - record.proof_stress_0_2_percent2*mu_value
                    upper = record.proof_stress_0_2_percent2 + record.proof_stress_0_2_percent2*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.proof_stress_0_2_percent2_conformity = 'pass'
                        break
                    else:
                        record.proof_stress_0_2_percent2_conformity = 'fail'

    @api.depends('proof_stress_0_2_percent2','eln_ref','grade')
    def _compute_proof_stress_0_2_percent2_nabl(self):
        
        for record in self:
            
            record.proof_stress_0_2_percent2_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poit56745-107d-4e30-9d3d-2a94567432erth6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poit56745-107d-4e30-9d3d-2a94567432erth6')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.proof_stress_0_2_percent2 - record.proof_stress_0_2_percent2*mu_value
            upper = record.proof_stress_0_2_percent2 + record.proof_stress_0_2_percent2*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.proof_stress_0_2_percent2_nabl = 'pass'
                break
            else:
                record.proof_stress_0_2_percent2_nabl = 'fail'


    
    
    elongation_percent_visible = fields.Boolean("Elongation (%) Visible",compute="_compute_visible")
    elongation_percent_name = fields.Char("Name",default="Elongation (%) - (ASTM B557:2015: 2023)")
    elongation_percent = fields.Float(string="Elongation (%)")


    elongation_percent_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_elongation_percent_conformity")

    elongation_percent_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_elongation_percent_nabl")


    @api.depends('elongation_percent','eln_ref','grade')
    def _compute_elongation_percent_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.elongation_percent_conformity = 'na'
                continue
            record.elongation_percent_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pp7654tp-107d-4e30-9d3d-2a9009uuu6554327')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pp7654tp-107d-4e30-9d3d-2a9009uuu6554327')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.elongation_percent - record.elongation_percent*mu_value
                    upper = record.elongation_percent + record.elongation_percent*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.elongation_percent_conformity = 'pass'
                        break
                    else:
                        record.elongation_percent_conformity = 'fail'

    @api.depends('elongation_percent','eln_ref','grade')
    def _compute_elongation_percent_nabl(self):
        
        for record in self:
            
            record.elongation_percent_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pp7654tp-107d-4e30-9d3d-2a9009uuu6554327')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pp7654tp-107d-4e30-9d3d-2a9009uuu6554327')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.elongation_percent - record.elongation_percent*mu_value
            upper = record.elongation_percent + record.elongation_percent*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.elongation_percent_nabl = 'pass'
                break
            else:
                record.elongation_percent_nabl = 'fail'

    elongation_percent_visible1 = fields.Boolean("Elongation (%) Visible",compute="_compute_visible")
    elongation_percent_name1 = fields.Char("Name",default="Elongation (%) - (ISO 6892 (Part 1): 2019: 2019)")
    elongation_percent1 = fields.Float(string="Elongation (%)")

    elongation_percent1_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_elongation_percent1_conformity")

    elongation_percent1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_elongation_percent1_nabl")


    @api.depends('elongation_percent1','eln_ref','grade')
    def _compute_elongation_percent1_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.elongation_percent1_conformity = 'na'
                continue
            record.elongation_percent1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','irtmyjrfrt-107d-4e30-9d3d-2a9009uoiuty45321')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','irtmyjrfrt-107d-4e30-9d3d-2a9009uoiuty45321')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.elongation_percent1 - record.elongation_percent1*mu_value
                    upper = record.elongation_percent1 + record.elongation_percent1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.elongation_percent1_conformity = 'pass'
                        break
                    else:
                        record.elongation_percent1_conformity = 'fail'

    @api.depends('elongation_percent1','eln_ref','grade')
    def _compute_elongation_percent1_nabl(self):
        
        for record in self:
            
            record.elongation_percent1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','irtmyjrfrt-107d-4e30-9d3d-2a9009uoiuty45321')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','irtmyjrfrt-107d-4e30-9d3d-2a9009uoiuty45321')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.elongation_percent1 - record.elongation_percent1*mu_value
            upper = record.elongation_percent1 + record.elongation_percent1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.elongation_percent1_nabl = 'pass'
                break
            else:
                record.elongation_percent1_nabl = 'fail'

    elongation_percent_visible2 = fields.Boolean("Elongation (%) Visible",compute="_compute_visible")
    elongation_percent_name2 = fields.Char("Name",default="Elongation (%) - (ASTM E8/E8M: 2022)")
    elongation_percent2 = fields.Float(string="Elongation (%)")

    elongation_percent2_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_elongation_percent2_conformity")

    elongation_percent2_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_elongation_percent2_nabl")


    @api.depends('elongation_percent2','eln_ref','grade')
    def _compute_elongation_percent2_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.elongation_percent2_conformity = 'na'
                continue
            record.elongation_percent2_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','096543ert-107d-4e30-9d3d-2a90099iuyhn456y')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','096543ert-107d-4e30-9d3d-2a90099iuyhn456y')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.elongation_percent2 - record.elongation_percent2*mu_value
                    upper = record.elongation_percent2 + record.elongation_percent2*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.elongation_percent2_conformity = 'pass'
                        break
                    else:
                        record.elongation_percent2_conformity = 'fail'

    @api.depends('elongation_percent2','eln_ref','grade')
    def _compute_elongation_percent2_nabl(self):
        
        for record in self:
            
            record.elongation_percent2_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','096543ert-107d-4e30-9d3d-2a90099iuyhn456y')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','096543ert-107d-4e30-9d3d-2a90099iuyhn456y')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.elongation_percent2 - record.elongation_percent2*mu_value
            upper = record.elongation_percent2 + record.elongation_percent2*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.elongation_percent2_nabl = 'pass'
                break
            else:
                record.elongation_percent2_nabl = 'fail'

    

    tensile_strength_uts_visible = fields.Boolean("Tensile Strength (UTS) Visible",compute="_compute_visible")
    tensile_strength_uts_name = fields.Char("Name",default="Tensile Strength (UTS) - (ASTM B557:2015: 2023)")
    tensile_strength_uts = fields.Float(string="Tensile Strength (UTS)")

    tensile_strength_uts_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_tensile_strength_uts_conformity")

    tensile_strength_uts_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_tensile_strength_uts_nabl")


    @api.depends('tensile_strength_uts','eln_ref','grade')
    def _compute_tensile_strength_uts_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.tensile_strength_uts_conformity = 'na'
                continue
            record.tensile_strength_uts_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','tre433567y-107d-4e30-9d3d-2a9009904567ytg')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','tre433567y-107d-4e30-9d3d-2a9009904567ytg')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.tensile_strength_uts - record.tensile_strength_uts*mu_value
                    upper = record.tensile_strength_uts + record.tensile_strength_uts*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.tensile_strength_uts_conformity = 'pass'
                        break
                    else:
                        record.tensile_strength_uts_conformity = 'fail'

    @api.depends('tensile_strength_uts','eln_ref','grade')
    def _compute_tensile_strength_uts_nabl(self):
        
        for record in self:
            
            record.tensile_strength_uts_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','tre433567y-107d-4e30-9d3d-2a9009904567ytg')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','tre433567y-107d-4e30-9d3d-2a9009904567ytg')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.tensile_strength_uts - record.tensile_strength_uts*mu_value
            upper = record.tensile_strength_uts + record.tensile_strength_uts*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.tensile_strength_uts_nabl = 'pass'
                break
            else:
                record.tensile_strength_uts_nabl = 'fail'

    tensile_strength_uts_visible1 = fields.Boolean("Tensile Strength (UTS) Visible",compute="_compute_visible")
    tensile_strength_uts_name1 = fields.Char("Name",default="Tensile Strength (UTS) - (ISO 6892 (Part 1): 2019: 2019)")
    tensile_strength_uts1 = fields.Float(string="Tensile Strength (UTS)")

    tensile_strength_uts1_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_tensile_strength_uts1_conformity")

    tensile_strength_uts1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_tensile_strength_uts1_nabl")


    @api.depends('tensile_strength_uts1','eln_ref','grade')
    def _compute_tensile_strength_uts1_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.tensile_strength_uts1_conformity = 'na'
                continue
            record.tensile_strength_uts1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','rtgfvbtre43-107d-4e30-9d3d-2a900123456789r')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','rtgfvbtre43-107d-4e30-9d3d-2a900123456789r')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.tensile_strength_uts1 - record.tensile_strength_uts1*mu_value
                    upper = record.tensile_strength_uts1 + record.tensile_strength_uts1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.tensile_strength_uts1_conformity = 'pass'
                        break
                    else:
                        record.tensile_strength_uts1_conformity = 'fail'

    @api.depends('tensile_strength_uts1','eln_ref','grade')
    def _compute_tensile_strength_uts1_nabl(self):
        
        for record in self:
            
            record.tensile_strength_uts1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','rtgfvbtre43-107d-4e30-9d3d-2a900123456789r')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','rtgfvbtre43-107d-4e30-9d3d-2a900123456789r')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.tensile_strength_uts1 - record.tensile_strength_uts1*mu_value
            upper = record.tensile_strength_uts1 + record.tensile_strength_uts1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.tensile_strength_uts1_nabl = 'pass'
                break
            else:
                record.tensile_strength_uts1_nabl = 'fail'

    tensile_strength_uts_visible2 = fields.Boolean("Tensile Strength (UTS) Visible",compute="_compute_visible")
    tensile_strength_uts_name2 = fields.Char("Name",default="Tensile Strength (UTS) - (ASTM E8/E8M: 2022)")
    tensile_strength_uts2 = fields.Float(string="Tensile Strength (UTS)")

    tensile_strength_uts2_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_tensile_strength_uts2_conformity")

    tensile_strength_uts2_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_tensile_strength_uts2_nabl")


    @api.depends('tensile_strength_uts2','eln_ref','grade')
    def _compute_tensile_strength_uts2_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.tensile_strength_uts2_conformity = 'na'
                continue
            record.tensile_strength_uts2_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bgnhyt543-107d-4e30-9d3d-2a900321wertfvgd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bgnhyt543-107d-4e30-9d3d-2a900321wertfvgd')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.tensile_strength_uts2 - record.tensile_strength_uts2*mu_value
                    upper = record.tensile_strength_uts2 + record.tensile_strength_uts2*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.tensile_strength_uts2_conformity = 'pass'
                        break
                    else:
                        record.tensile_strength_uts2_conformity = 'fail'

    @api.depends('tensile_strength_uts2','eln_ref','grade')
    def _compute_tensile_strength_uts2_nabl(self):
        
        for record in self:
            
            record.tensile_strength_uts2_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bgnhyt543-107d-4e30-9d3d-2a900321wertfvgd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bgnhyt543-107d-4e30-9d3d-2a900321wertfvgd')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.tensile_strength_uts2 - record.tensile_strength_uts2*mu_value
            upper = record.tensile_strength_uts2 + record.tensile_strength_uts2*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.tensile_strength_uts2_nabl = 'pass'
                break
            else:
                record.tensile_strength_uts2_nabl = 'fail'

    yield_strength_visible = fields.Boolean("Yield Strength Visible",compute="_compute_visible")
    yield_strength_name = fields.Char("Name",default="Yield Strength - (ASTM B557:2015: 2023)")
    yield_strength = fields.Float(string="Yield Strength")

    yield_strength_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_yield_strength_conformity")

    yield_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_yield_strength_nabl")


    @api.depends('yield_strength','eln_ref','grade')
    def _compute_yield_strength_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.yield_strength_conformity = 'na'
                continue
            record.yield_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ujhgty654-107d-4e30-9d3d-2a9009rr5tgbvcfder')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ujhgty654-107d-4e30-9d3d-2a9009rr5tgbvcfder')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.yield_strength - record.yield_strength*mu_value
                    upper = record.yield_strength + record.yield_strength*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.yield_strength_conformity = 'pass'
                        break
                    else:
                        record.yield_strength_conformity = 'fail'

    @api.depends('yield_strength','eln_ref','grade')
    def _compute_yield_strength_nabl(self):
        
        for record in self:
            
            record.yield_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ujhgty654-107d-4e30-9d3d-2a9009rr5tgbvcfder')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ujhgty654-107d-4e30-9d3d-2a9009rr5tgbvcfder')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.yield_strength - record.yield_strength*mu_value
            upper = record.yield_strength + record.yield_strength*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.yield_strength_nabl = 'pass'
                break
            else:
                record.yield_strength_nabl = 'fail'

    yield_strength_visible1 = fields.Boolean("Yield Strength Visible",compute="_compute_visible")
    yield_strength_name1 = fields.Char("Name",default="Yield Strength - (ISO 6892 (Part 1): 2019: 2019)")
    yield_strength1 = fields.Float(string="Yield Strength")

    yield_strength1_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_yield_strength1_conformity")

    yield_strength1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_yield_strength1_nabl")


    @api.depends('yield_strength1','eln_ref','grade')
    def _compute_yield_strength1_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.yield_strength1_conformity = 'na'
                continue
            record.yield_strength1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oiujnhtr4-107d-4e30-9d3d-2a9009rr09876543e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oiujnhtr4-107d-4e30-9d3d-2a9009rr09876543e')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.yield_strength1 - record.yield_strength1*mu_value
                    upper = record.yield_strength1 + record.yield_strength1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.yield_strength1_conformity = 'pass'
                        break
                    else:
                        record.yield_strength1_conformity = 'fail'

    @api.depends('yield_strength1','eln_ref','grade')
    def _compute_yield_strength1_nabl(self):
        
        for record in self:
            
            record.yield_strength1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oiujnhtr4-107d-4e30-9d3d-2a9009rr09876543e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oiujnhtr4-107d-4e30-9d3d-2a9009rr09876543e')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.yield_strength1 - record.yield_strength1*mu_value
            upper = record.yield_strength1 + record.yield_strength1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.yield_strength1_nabl = 'pass'
                break
            else:
                record.yield_strength1_nabl = 'fail'

    yield_strength_visible2 = fields.Boolean("Yield Strength Visible",compute="_compute_visible")
    yield_strength_name2 = fields.Char("Name",default="Yield Strength - (ASTM E8/E8M: 2022)")
    yield_strength2 = fields.Float(string="Yield Strength")

    yield_strength2_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_yield_strength2_conformity")

    yield_strength2_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_yield_strength2_nabl")


    @api.depends('yield_strength2','eln_ref','grade')
    def _compute_yield_strength2_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.yield_strength2_conformity = 'na'
                continue
            record.yield_strength2_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oikmnhbgt45-107d-4e30-9d3d-2a9009rrthnbgtr45')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oikmnhbgt45-107d-4e30-9d3d-2a9009rrthnbgtr45')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.yield_strength2 - record.yield_strength2*mu_value
                    upper = record.yield_strength2 + record.yield_strength2*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.yield_strength2_conformity = 'pass'
                        break
                    else:
                        record.yield_strength2_conformity = 'fail'

    @api.depends('yield_strength2','eln_ref','grade')
    def _compute_yield_strength2_nabl(self):
        
        for record in self:
            
            record.yield_strength2_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oikmnhbgt45-107d-4e30-9d3d-2a9009rrthnbgtr45')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oikmnhbgt45-107d-4e30-9d3d-2a9009rrthnbgtr45')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.yield_strength2 - record.yield_strength2*mu_value
            upper = record.yield_strength2 + record.yield_strength2*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.yield_strength2_nabl = 'pass'
                break
            else:
                record.yield_strength2_nabl = 'fail'

    

    

    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
    
            record.reduction_area_visible = False
            record.reduction_area_visible1 = False
            record.reduction_area_visible2 = False

            record.proof_stress_visible = False
            record.proof_stress_visible1 = False
            record.proof_stress_visible2 = False

            
            record.elongation_percent_visible = False
            record.elongation_percent_visible1 = False
            record.elongation_percent_visible2 = False

            
            record.tensile_strength_uts_visible = False
            record.tensile_strength_uts_visible1 = False
            record.tensile_strength_uts_visible2 = False

            record.yield_strength_visible = False
            record.yield_strength_visible1 = False
            record.yield_strength_visible2 = False
            
            
            
            

            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
               
                if sample.internal_id == "poi56784-107d-4e30-9d3d-2a096785432g":
                    record.reduction_area_visible = True 
                if sample.internal_id == "654rt4325-107d-4e30-9d3d-2aiu45634237":
                    record.reduction_area_visible1 = True
                if sample.internal_id == "5754ert342-107d-4e30-9d3d-2a9864532345":
                    record.reduction_area_visible2 = True

                if sample.internal_id == "murt4563-107d-4e30-9d3d-2a9p0456321we":
                    record.proof_stress_visible = True 
                if sample.internal_id == "port54321d-107d-4e30-9d3d-2a9o456tyr345":
                    record.proof_stress_visible1 = True 
                if sample.internal_id == "poit56745-107d-4e30-9d3d-2a94567432erth6":
                    record.proof_stress_visible2 = True 


                if sample.internal_id == "pp7654tp-107d-4e30-9d3d-2a9009uuu6554327":
                    record.elongation_percent_visible = True 
                if sample.internal_id == "irtmyjrfrt-107d-4e30-9d3d-2a9009uoiuty45321":
                    record.elongation_percent_visible1 = True 
                if sample.internal_id == "096543ert-107d-4e30-9d3d-2a90099iuyhn456y":
                    record.elongation_percent_visible2 = True 

                

                if sample.internal_id == "tre433567y-107d-4e30-9d3d-2a9009904567ytg":
                    record.tensile_strength_uts_visible = True 
                if sample.internal_id == "rtgfvbtre43-107d-4e30-9d3d-2a900123456789r":
                    record.tensile_strength_uts_visible1 = True 
                if sample.internal_id == "bgnhyt543-107d-4e30-9d3d-2a900321wertfvgd":
                    record.tensile_strength_uts_visible2 = True 
                

                if sample.internal_id == "ujhgty654-107d-4e30-9d3d-2a9009rr5tgbvcfder":
                    record.yield_strength_visible = True 
                if sample.internal_id == "oiujnhtr4-107d-4e30-9d3d-2a9009rr09876543e":
                    record.yield_strength_visible1 = True
                if sample.internal_id == "oikmnhbgt45-107d-4e30-9d3d-2a9009rrthnbgtr45":
                    record.yield_strength_visible2 = True

                

               

               
                

                
     
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
           

            
            if result.parameter.internal_id == 'poi56784-107d-4e30-9d3d-2a096785432g':
                result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                if self.reduction_in_area_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            if result.parameter.internal_id == '654rt4325-107d-4e30-9d3d-2aiu45634237':
                result.result_char = round(self.reduction_in_area_percent1,2)
                result.calculated = True
                if self.reduction_in_area_percent1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            if result.parameter.internal_id == '5754ert342-107d-4e30-9d3d-2a9864532345':
                result.result_char = round(self.reduction_in_area_percent2,2)
                result.calculated = True
                if self.reduction_in_area_percent2_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

           

            if result.parameter.internal_id == 'murt4563-107d-4e30-9d3d-2a9p0456321we':
                result.result_char = round(self.proof_stress_0_2_percent,2)
                result.calculated = True
                if self.proof_stress_0_2_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            if result.parameter.internal_id == 'port54321d-107d-4e30-9d3d-2a9o456tyr345':
                result.result_char = round(self.proof_stress_0_2_percent1,2)
                result.calculated = True
                if self.proof_stress_0_2_percent1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            if result.parameter.internal_id == 'poit56745-107d-4e30-9d3d-2a94567432erth6':
                result.result_char = round(self.proof_stress_0_2_percent2,2)
                result.calculated = True
                if self.proof_stress_0_2_percent2_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

           

            
            if result.parameter.internal_id == 'pp7654tp-107d-4e30-9d3d-2a9009uuu6554327':
                result.result_char = round(self.elongation_percent,2)
                result.calculated = True
                if self.elongation_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            if result.parameter.internal_id == 'irtmyjrfrt-107d-4e30-9d3d-2a9009uoiuty45321':
                result.result_char = round(self.elongation_percent1,2)
                result.calculated = True
                if self.elongation_percent1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            if result.parameter.internal_id == '096543ert-107d-4e30-9d3d-2a90099iuyhn456y':
                result.result_char = round(self.elongation_percent2,2)
                result.calculated = True
                if self.elongation_percent2_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 


            

            if result.parameter.internal_id == 'tre433567y-107d-4e30-9d3d-2a9009904567ytg':
                result.result_char = round(self.tensile_strength_uts,2)
                result.calculated = True
                if self.tensile_strength_uts_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            if result.parameter.internal_id == 'rtgfvbtre43-107d-4e30-9d3d-2a900123456789r':
                result.result_char = round(self.tensile_strength_uts1,2)
                result.calculated = True
                if self.tensile_strength_uts1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            if result.parameter.internal_id == 'bgnhyt543-107d-4e30-9d3d-2a900321wertfvgd':
                result.result_char = round(self.tensile_strength_uts2,2)
                result.calculated = True
                if self.tensile_strength_uts2_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'ujhgty654-107d-4e30-9d3d-2a9009rr5tgbvcfder':
                result.result_char = round(self.yield_strength,2)
                result.calculated = True
                if self.yield_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            if result.parameter.internal_id == 'oiujnhtr4-107d-4e30-9d3d-2a9009rr09876543e':
                result.result_char = round(self.yield_strength1,2)
                result.calculated = True
                if self.yield_strength1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'oikmnhbgt45-107d-4e30-9d3d-2a9009rrthnbgtr45':
                result.result_char = round(self.yield_strength2,2)
                result.calculated = True
                if self.yield_strength2_nabl == 'pass':
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
        record = super(MechanicalAluminumAlloys, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
    

   

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
        record = self.env['mechanical.aluminum.alloys'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values





class AluminumAlloysNotes(models.Model):
    _name = "aluminum.alloys.notes"

    parent_id = fields.Many2one('mechanical.aluminum.alloys',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
