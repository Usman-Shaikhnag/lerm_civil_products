from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class MechanicalOtherNonFerrous(models.Model):
    _name = "mechanical.other.non.ferrous"
    _inherit = "lerm.eln"
    _rec_name = "name2"

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    name2 = fields.Char("Name",default="Other Non Ferrous Material")
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

    description_work = fields.Text("Description Of Work")

    notes_id = fields.One2many('other.non.ferrous.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(MechanicalOtherNonFerrous, self).default_get(fields)

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
    reduction_area_name = fields.Char("Name",default="% Reduction in Area")
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','li4564be-107d-4e30-9d3d-2a9009746532')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','li4564be-107d-4e30-9d3d-2a9009746532')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','li4564be-107d-4e30-9d3d-2a9009746532')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','li4564be-107d-4e30-9d3d-2a9009746532')]).parameter_table
            
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


    proof_stress_visible = fields.Boolean("0.2% Proof Stress Visible",compute="_compute_visible")
    proof_stress_name = fields.Char("Name",default="0.2% Proof Stress")
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oitr45be-107d-4e30-9d3d-2a90090985674')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oitr45be-107d-4e30-9d3d-2a90090985674')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oitr45be-107d-4e30-9d3d-2a90090985674')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','oitr45be-107d-4e30-9d3d-2a90090985674')]).parameter_table
            
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


    brinell_hardness_hbw_2_5_250_visible = fields.Boolean("Brinell Hardness (HBW 2.5/250) Visible",compute="_compute_visible")
    brinell_hardness_hbw_2_5_250_name = fields.Char("Name",default="Brinell Hardness (HBW 2.5/250) - (IS 1500 (Part 1): 2019: 2024)")
    brinell_hardness_hbw_2_5_250 = fields.Float(string="Brinell Hardness (HBW 2.5/250)")

    brinell_hardness_hbw_2_5_250_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_brinell_hardness_hbw_2_5_250_conformity")

    brinell_hardness_hbw_2_5_250_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_brinell_hardness_hbw_2_5_250_nabl")


    @api.depends('brinell_hardness_hbw_2_5_250','eln_ref','grade')
    def _compute_brinell_hardness_hbw_2_5_250_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.brinell_hardness_hbw_2_5_250_conformity = 'na'
                continue
            record.brinell_hardness_hbw_2_5_250_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0005t4r4-107d-4e30-9d3d-2a90090978644')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0005t4r4-107d-4e30-9d3d-2a90090978644')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.brinell_hardness_hbw_2_5_250 - record.brinell_hardness_hbw_2_5_250*mu_value
                    upper = record.brinell_hardness_hbw_2_5_250 + record.brinell_hardness_hbw_2_5_250*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.brinell_hardness_hbw_2_5_250_conformity = 'pass'
                        break
                    else:
                        record.brinell_hardness_hbw_2_5_250_conformity = 'fail'

    @api.depends('brinell_hardness_hbw_2_5_250','eln_ref','grade')
    def _compute_brinell_hardness_hbw_2_5_250_nabl(self):
        
        for record in self:
            
            record.brinell_hardness_hbw_2_5_250_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0005t4r4-107d-4e30-9d3d-2a90090978644')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0005t4r4-107d-4e30-9d3d-2a90090978644')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.brinell_hardness_hbw_2_5_250 - record.brinell_hardness_hbw_2_5_250*mu_value
            upper = record.brinell_hardness_hbw_2_5_250 + record.brinell_hardness_hbw_2_5_250*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.brinell_hardness_hbw_2_5_250_nabl = 'pass'
                break
            else:
                record.brinell_hardness_hbw_2_5_250_nabl = 'fail'

    brinell_hardness_hbw_2_5_250_visible1 = fields.Boolean("Brinell Hardness (HBW 2.5/250) Visible",compute="_compute_visible")
    brinell_hardness_hbw_2_5_250_name1 = fields.Char("Name",default="Brinell Hardness (HBW 2.5/250) - (ISO 6506 (Part 1): 2014: 2014)")
    brinell_hardness_hbw_2_5_2501 = fields.Float(string="Brinell Hardness (HBW 2.5/250)")

    brinell_hardness_hbw_2_5_2501_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_brinell_hardness_hbw_2_5_2501_conformity")

    brinell_hardness_hbw_2_5_2501_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_brinell_hardness_hbw_2_5_2501_nabl")


    @api.depends('brinell_hardness_hbw_2_5_2501','eln_ref','grade')
    def _compute_brinell_hardness_hbw_2_5_2501_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.brinell_hardness_hbw_2_5_2501_conformity = 'na'
                continue
            record.brinell_hardness_hbw_2_5_2501_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','00054345-107d-4e30-9d3d-2a9078956543')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','00054345-107d-4e30-9d3d-2a9078956543')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.brinell_hardness_hbw_2_5_2501 - record.brinell_hardness_hbw_2_5_2501*mu_value
                    upper = record.brinell_hardness_hbw_2_5_2501 + record.brinell_hardness_hbw_2_5_2501*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.brinell_hardness_hbw_2_5_2501_conformity = 'pass'
                        break
                    else:
                        record.brinell_hardness_hbw_2_5_2501_conformity = 'fail'

    @api.depends('brinell_hardness_hbw_2_5_2501','eln_ref','grade')
    def _compute_brinell_hardness_hbw_2_5_2501_nabl(self):
        
        for record in self:
            
            record.brinell_hardness_hbw_2_5_2501_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','00054345-107d-4e30-9d3d-2a9078956543')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','00054345-107d-4e30-9d3d-2a9078956543')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.brinell_hardness_hbw_2_5_2501 - record.brinell_hardness_hbw_2_5_2501*mu_value
            upper = record.brinell_hardness_hbw_2_5_2501 + record.brinell_hardness_hbw_2_5_2501*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.brinell_hardness_hbw_2_5_2501_nabl = 'pass'
                break
            else:
                record.brinell_hardness_hbw_2_5_2501_nabl = 'fail'
    
    brinell_hardness_hbw_5_250_visible = fields.Boolean("Brinell Hardness (HBW 5/250) Visible",compute="_compute_visible")
    brinell_hardness_hbw_5_250_name = fields.Char("Name",default="Brinell Hardness (HBW 5/250) - (IS 1500 (Part 1): 2019: 2024)")
    brinell_hardness_hbw_5_250 = fields.Float(string="Brinell Hardness (HBW 5/250)")

    brinell_hardness_hbw_5_250_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_brinell_hardness_hbw_5_250_conformity")

    brinell_hardness_hbw_5_250_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_brinell_hardness_hbw_5_250_nabl")


    @api.depends('brinell_hardness_hbw_5_250','eln_ref','grade')
    def _compute_brinell_hardness_hbw_5_250_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.brinell_hardness_hbw_5_250_conformity = 'na'
                continue
            record.brinell_hardness_hbw_5_250_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pp54324be-107d-4e30-9d3d-2a99995674326')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pp54324be-107d-4e30-9d3d-2a99995674326')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.brinell_hardness_hbw_5_250 - record.brinell_hardness_hbw_5_250*mu_value
                    upper = record.brinell_hardness_hbw_5_250 + record.brinell_hardness_hbw_5_250*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.brinell_hardness_hbw_5_250_conformity = 'pass'
                        break
                    else:
                        record.brinell_hardness_hbw_5_250_conformity = 'fail'

    @api.depends('brinell_hardness_hbw_5_250','eln_ref','grade')
    def _compute_brinell_hardness_hbw_5_250_nabl(self):
        
        for record in self:
            
            record.brinell_hardness_hbw_5_250_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pp54324be-107d-4e30-9d3d-2a99995674326')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pp54324be-107d-4e30-9d3d-2a99995674326')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.brinell_hardness_hbw_5_250 - record.brinell_hardness_hbw_5_250*mu_value
            upper = record.brinell_hardness_hbw_5_250 + record.brinell_hardness_hbw_5_250*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.brinell_hardness_hbw_5_250_nabl = 'pass'
                break
            else:
                record.brinell_hardness_hbw_5_250_nabl = 'fail'

    brinell_hardness_hbw_5_250_visible1 = fields.Boolean("Brinell Hardness (HBW 5/250) Visible",compute="_compute_visible")
    brinell_hardness_hbw_5_250_name1 = fields.Char("Name",default="Brinell Hardness (HBW 5/250) - (ISO 6506 (Part 1): 2014: 2014)")
    brinell_hardness_hbw_5_2501 = fields.Float(string="Brinell Hardness (HBW 5/250)")

    brinell_hardness_hbw_5_2501_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_brinell_hardness_hbw_5_2501_conformity")

    brinell_hardness_hbw_5_2501_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_brinell_hardness_hbw_5_2501_nabl")


    @api.depends('brinell_hardness_hbw_5_2501','eln_ref','grade')
    def _compute_brinell_hardness_hbw_5_2501_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.brinell_hardness_hbw_5_2501_conformity = 'na'
                continue
            record.brinell_hardness_hbw_5_2501_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ppp456743-107d-4e30-9d3d-2a90009543247')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ppp456743-107d-4e30-9d3d-2a90009543247')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.brinell_hardness_hbw_5_2501 - record.brinell_hardness_hbw_5_2501*mu_value
                    upper = record.brinell_hardness_hbw_5_2501 + record.brinell_hardness_hbw_5_2501*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.brinell_hardness_hbw_5_2501_conformity = 'pass'
                        break
                    else:
                        record.brinell_hardness_hbw_5_2501_conformity = 'fail'

    @api.depends('brinell_hardness_hbw_5_2501','eln_ref','grade')
    def _compute_brinell_hardness_hbw_5_2501_nabl(self):
        
        for record in self:
            
            record.brinell_hardness_hbw_5_2501_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ppp456743-107d-4e30-9d3d-2a90009543247')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ppp456743-107d-4e30-9d3d-2a90009543247')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.brinell_hardness_hbw_5_2501 - record.brinell_hardness_hbw_5_2501*mu_value
            upper = record.brinell_hardness_hbw_5_2501 + record.brinell_hardness_hbw_5_2501*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.brinell_hardness_hbw_5_2501_nabl = 'pass'
                break
            else:
                record.brinell_hardness_hbw_5_2501_nabl = 'fail'
    
    elongation_percent_visible = fields.Boolean("Elongation (%) Visible",compute="_compute_visible")
    elongation_percent_name = fields.Char("Name",default="Elongation (%) ")
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','rrt55566jj-107d-4e30-9d3d-2a9009rrr5554333')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','rrt55566jj-107d-4e30-9d3d-2a9009rrr5554333')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','rrt55566jj-107d-4e30-9d3d-2a9009rrr5554333')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','rrt55566jj-107d-4e30-9d3d-2a9009rrr5554333')]).parameter_table
            
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

    rockwell_hardness_hrbw_visible = fields.Boolean("Rockwell Hardness (HRBW)Visible",compute="_compute_visible")
    rockwell_hardness_hrbw_name = fields.Char("Name",default="Rockwell Hardness (HRBW) - (IS 1586 (Part 1) : 2018: 2023)")
    rockwell_hardness_hrbw = fields.Float(string="Rockwell Hardness (HRBW)")

    rockwell_hardness_hrbw_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_rockwell_hardness_hrbw_conformity")

    rockwell_hardness_hrbw_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_rockwell_hardness_hrbw_nabl")


    @api.depends('rockwell_hardness_hrbw','eln_ref','grade')
    def _compute_rockwell_hardness_hrbw_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.rockwell_hardness_hrbw_conformity = 'na'
                continue
            record.rockwell_hardness_hrbw_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ooer4366jj-107d-4e30-9d3d-2a9009rrr004533e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ooer4366jj-107d-4e30-9d3d-2a9009rrr004533e')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.rockwell_hardness_hrbw - record.rockwell_hardness_hrbw*mu_value
                    upper = record.rockwell_hardness_hrbw + record.rockwell_hardness_hrbw*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.rockwell_hardness_hrbw_conformity = 'pass'
                        break
                    else:
                        record.rockwell_hardness_hrbw_conformity = 'fail'

    @api.depends('rockwell_hardness_hrbw','eln_ref','grade')
    def _compute_rockwell_hardness_hrbw_nabl(self):
        
        for record in self:
            
            record.rockwell_hardness_hrbw_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ooer4366jj-107d-4e30-9d3d-2a9009rrr004533e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ooer4366jj-107d-4e30-9d3d-2a9009rrr004533e')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.rockwell_hardness_hrbw - record.rockwell_hardness_hrbw*mu_value
            upper = record.rockwell_hardness_hrbw + record.rockwell_hardness_hrbw*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.rockwell_hardness_hrbw_nabl = 'pass'
                break
            else:
                record.rockwell_hardness_hrbw_nabl = 'fail'

    rockwell_hardness_hrbw_visible1 = fields.Boolean("Rockwell Hardness (HRBW)Visible",compute="_compute_visible")
    rockwell_hardness_hrbw_name1 = fields.Char("Name",default="Rockwell Hardness (HRBW) - (ISO 6508 (Part 1): 2016: 2016)")
    rockwell_hardness_hrbw1 = fields.Float(string="Rockwell Hardness (HRBW)")

    rockwell_hardness_hrbw1_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_rockwell_hardness_hrbw1_conformity")

    rockwell_hardness_hrbw1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_rockwell_hardness_hrbw1_nabl")


    @api.depends('rockwell_hardness_hrbw1','eln_ref','grade')
    def _compute_rockwell_hardness_hrbw1_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.rockwell_hardness_hrbw1_conformity = 'na'
                continue
            record.rockwell_hardness_hrbw1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pprt5566jj-107d-4e30-9d3d-2a9009rrrllrt432gg')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pprt5566jj-107d-4e30-9d3d-2a9009rrrllrt432gg')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.rockwell_hardness_hrbw1 - record.rockwell_hardness_hrbw1*mu_value
                    upper = record.rockwell_hardness_hrbw1 + record.rockwell_hardness_hrbw1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.rockwell_hardness_hrbw1_conformity = 'pass'
                        break
                    else:
                        record.rockwell_hardness_hrbw1_conformity = 'fail'

    @api.depends('rockwell_hardness_hrbw1','eln_ref','grade')
    def _compute_rockwell_hardness_hrbw1_nabl(self):
        
        for record in self:
            
            record.rockwell_hardness_hrbw1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pprt5566jj-107d-4e30-9d3d-2a9009rrrllrt432gg')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pprt5566jj-107d-4e30-9d3d-2a9009rrrllrt432gg')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.rockwell_hardness_hrbw1 - record.rockwell_hardness_hrbw1*mu_value
            upper = record.rockwell_hardness_hrbw1 + record.rockwell_hardness_hrbw1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.rockwell_hardness_hrbw1_nabl = 'pass'
                break
            else:
                record.rockwell_hardness_hrbw1_nabl = 'fail'

    tensile_strength_uts_visible = fields.Boolean("Tensile Strength (UTS) Visible",compute="_compute_visible")
    tensile_strength_uts_name = fields.Char("Name",default="Tensile Strength (UTS)")
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ppt543266jj-107d-4e30-9d3d-2a9009rrr6754325')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ppt543266jj-107d-4e30-9d3d-2a9009rrr6754325')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ppt543266jj-107d-4e30-9d3d-2a9009rrr6754325')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ppt543266jj-107d-4e30-9d3d-2a9009rrr6754325')]).parameter_table
            
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

    yield_strength_visible = fields.Boolean("Yield Strength Visible",compute="_compute_visible")
    yield_strength_name = fields.Char("Name",default="Yield Strength")
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pppptttt5-107d-4e30-9d3d-2a9009rrr005674366')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pppptttt5-107d-4e30-9d3d-2a9009rrr005674366')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pppptttt5-107d-4e30-9d3d-2a9009rrr005674366')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','pppptttt5-107d-4e30-9d3d-2a9009rrr005674366')]).parameter_table
            
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

    vickers_hardness_hv30_visible = fields.Boolean("Vickers Hardness (HV30)  Visible",compute="_compute_visible")
    vickers_hardness_hv30_name = fields.Char("Name",default="Vickers Hardness (HV30) - (IS 1501 ( Part 1): 2020: 2020)")
    vickers_hardness_hv30 = fields.Float(string="Vickers Hardness (HV30)")


    vickers_hardness_hv30_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_vickers_hardness_hv30_conformity")

    vickers_hardness_hv30_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_vickers_hardness_hv30_nabl")


    @api.depends('vickers_hardness_hv30','eln_ref','grade')
    def _compute_vickers_hardness_hv30_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.vickers_hardness_hv30_conformity = 'na'
                continue
            record.vickers_hardness_hv30_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','kkkllrt432-107d-4e30-9d3d-2a9009rrooo4567321')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','kkkllrt432-107d-4e30-9d3d-2a9009rrooo4567321')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.vickers_hardness_hv30 - record.vickers_hardness_hv30*mu_value
                    upper = record.vickers_hardness_hv30 + record.vickers_hardness_hv30*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.vickers_hardness_hv30_conformity = 'pass'
                        break
                    else:
                        record.vickers_hardness_hv30_conformity = 'fail'

    @api.depends('vickers_hardness_hv30','eln_ref','grade')
    def _compute_vickers_hardness_hv30_nabl(self):
        
        for record in self:
            
            record.vickers_hardness_hv30_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','kkkllrt432-107d-4e30-9d3d-2a9009rrooo4567321')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','kkkllrt432-107d-4e30-9d3d-2a9009rrooo4567321')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.vickers_hardness_hv30 - record.vickers_hardness_hv30*mu_value
            upper = record.vickers_hardness_hv30 + record.vickers_hardness_hv30*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.vickers_hardness_hv30_nabl = 'pass'
                break
            else:
                record.vickers_hardness_hv30_nabl = 'fail'

    vickers_hardness_hv30_visible1 = fields.Boolean("Vickers Hardness (HV30)  Visible",compute="_compute_visible")
    vickers_hardness_hv30_name1 = fields.Char("Name",default="Vickers Hardness (HV30) - (IS 1501 ( Part 1): 2020: 2020)")
    vickers_hardness_hv301 = fields.Float(string="Vickers Hardness (HV30)")

    vickers_hardness_hv301_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_vickers_hardness_hv301_conformity")

    vickers_hardness_hv301_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_vickers_hardness_hv301_nabl")


    @api.depends('vickers_hardness_hv301','eln_ref','grade')
    def _compute_vickers_hardness_hv301_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.vickers_hardness_hv301_conformity = 'na'
                continue
            record.vickers_hardness_hv301_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','llltewqsd-107d-4e30-9d3d-2a9009rr00045321rjm')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','llltewqsd-107d-4e30-9d3d-2a9009rr00045321rjm')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.vickers_hardness_hv301 - record.vickers_hardness_hv301*mu_value
                    upper = record.vickers_hardness_hv301 + record.vickers_hardness_hv301*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.vickers_hardness_hv301_conformity = 'pass'
                        break
                    else:
                        record.vickers_hardness_hv301_conformity = 'fail'

    @api.depends('vickers_hardness_hv301','eln_ref','grade')
    def _compute_vickers_hardness_hv301_nabl(self):
        
        for record in self:
            
            record.vickers_hardness_hv301_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','llltewqsd-107d-4e30-9d3d-2a9009rr00045321rjm')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','llltewqsd-107d-4e30-9d3d-2a9009rr00045321rjm')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.vickers_hardness_hv301 - record.vickers_hardness_hv301*mu_value
            upper = record.vickers_hardness_hv301 + record.vickers_hardness_hv301*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.vickers_hardness_hv301_nabl = 'pass'
                break
            else:
                record.vickers_hardness_hv301_nabl = 'fail'


    

    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
    
            record.reduction_area_visible = False
            record.proof_stress_visible = False
            record.brinell_hardness_hbw_2_5_250_visible = False
            record.brinell_hardness_hbw_2_5_250_visible1 = False
            record.brinell_hardness_hbw_5_250_visible = False
            record.brinell_hardness_hbw_5_250_visible1 = False
            record.elongation_percent_visible = False
            record.rockwell_hardness_hrbw_visible = False
            record.rockwell_hardness_hrbw_visible1 = False
            record.tensile_strength_uts_visible = False
            record.yield_strength_visible = False
            record.vickers_hardness_hv30_visible = False
            record.vickers_hardness_hv30_visible1 = False
            
            
            

            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
               
                if sample.internal_id == "li4564be-107d-4e30-9d3d-2a9009746532":
                    record.reduction_area_visible = True 

                if sample.internal_id == "oitr45be-107d-4e30-9d3d-2a90090985674":
                    record.proof_stress_visible = True 

                if sample.internal_id == "0005t4r4-107d-4e30-9d3d-2a90090978644":
                    record.brinell_hardness_hbw_2_5_250_visible = True 

                if sample.internal_id == "00054345-107d-4e30-9d3d-2a9078956543":
                    record.brinell_hardness_hbw_2_5_250_visible1 = True 

                if sample.internal_id == "pp54324be-107d-4e30-9d3d-2a99995674326":
                    record.brinell_hardness_hbw_5_250_visible = True 

                if sample.internal_id == "ppp456743-107d-4e30-9d3d-2a90009543247":
                    record.brinell_hardness_hbw_5_250_visible1 = True 

                if sample.internal_id == "rrt55566jj-107d-4e30-9d3d-2a9009rrr5554333":
                    record.elongation_percent_visible = True 

                if sample.internal_id == "ooer4366jj-107d-4e30-9d3d-2a9009rrr004533e":
                    record.rockwell_hardness_hrbw_visible = True 

                if sample.internal_id == "pprt5566jj-107d-4e30-9d3d-2a9009rrrllrt432gg":
                    record.rockwell_hardness_hrbw_visible1 = True 

                if sample.internal_id == "ppt543266jj-107d-4e30-9d3d-2a9009rrr6754325":
                    record.tensile_strength_uts_visible = True 

                if sample.internal_id == "pppptttt5-107d-4e30-9d3d-2a9009rrr005674366":
                    record.yield_strength_visible = True 

                if sample.internal_id == "kkkllrt432-107d-4e30-9d3d-2a9009rrooo4567321":
                    record.vickers_hardness_hv30_visible = True 

                if sample.internal_id == "llltewqsd-107d-4e30-9d3d-2a9009rr00045321rjm":
                    record.vickers_hardness_hv30_visible1 = True 

               
                

                
     
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
           

            
            if result.parameter.internal_id == 'li4564be-107d-4e30-9d3d-2a9009746532':
                result.result_char = round(self.reduction_in_area_percent,2)
                result.calculated = True
                if self.reduction_in_area_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

           

            if result.parameter.internal_id == 'oitr45be-107d-4e30-9d3d-2a90090985674':
                result.result_char = round(self.proof_stress_0_2_percent,2)
                result.calculated = True
                if self.proof_stress_0_2_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

           
            if result.parameter.internal_id == '0005t4r4-107d-4e30-9d3d-2a90090978644':
                result.result_char = round(self.brinell_hardness_hbw_2_5_250,2)
                result.calculated = True
                if self.brinell_hardness_hbw_2_5_250_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '00054345-107d-4e30-9d3d-2a9078956543':
                result.result_char = round(self.brinell_hardness_hbw_2_5_2501,2)
                result.calculated = True
                if self.brinell_hardness_hbw_2_5_2501_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 


            if result.parameter.internal_id == 'pp54324be-107d-4e30-9d3d-2a99995674326':
                result.result_char = round(self.brinell_hardness_hbw_5_250,2)
                result.calculated = True
                if self.brinell_hardness_hbw_5_250_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 


            if result.parameter.internal_id == 'ppp456743-107d-4e30-9d3d-2a90009543247':
                result.result_char = round(self.brinell_hardness_hbw_5_2501,2)
                result.calculated = True
                if self.brinell_hardness_hbw_5_2501_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'rrt55566jj-107d-4e30-9d3d-2a9009rrr5554333':
                result.result_char = round(self.elongation_percent,2)
                result.calculated = True
                if self.elongation_percent_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 


            if result.parameter.internal_id == 'ooer4366jj-107d-4e30-9d3d-2a9009rrr004533e':
                result.result_char = round(self.rockwell_hardness_hrbw,2)
                result.calculated = True
                if self.rockwell_hardness_hrbw_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'pprt5566jj-107d-4e30-9d3d-2a9009rrrllrt432gg':
                result.result_char = round(self.rockwell_hardness_hrbw1,2)
                result.calculated = True
                if self.rockwell_hardness_hrbw1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'ppt543266jj-107d-4e30-9d3d-2a9009rrr6754325':
                result.result_char = round(self.tensile_strength_uts,2)
                result.calculated = True
                if self.tensile_strength_uts_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'pppptttt5-107d-4e30-9d3d-2a9009rrr005674366':
                result.result_char = round(self.yield_strength,2)
                result.calculated = True
                if self.yield_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'kkkllrt432-107d-4e30-9d3d-2a9009rrooo4567321':
                result.result_char = round(self.vickers_hardness_hv30,2)
                result.calculated = True
                if self.vickers_hardness_hv30_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'llltewqsd-107d-4e30-9d3d-2a9009rr00045321rjm':
                result.result_char = round(self.vickers_hardness_hv301,2)
                result.calculated = True
                if self.vickers_hardness_hv301_nabl == 'pass':
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
        record = super(MechanicalOtherNonFerrous, self).create(vals)
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
        record = self.env['mechanical.other.non.ferrous'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values





class OtherNonFerrousNotes(models.Model):
    _name = "other.non.ferrous.notes"

    parent_id = fields.Many2one('mechanical.other.non.ferrous',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
