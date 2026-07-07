from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class MechanicalFastenerBolts(models.Model):
    _name = "mechanical.fastener.bolts"
    _inherit = "lerm.eln"
    _rec_name = "name2"

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    name2 = fields.Char("Name",default="Fastener / Bolts & Studs")
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

    notes_id = fields.One2many('fastener.bolts.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(MechanicalFastenerBolts, self).default_get(fields)

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


    proof_load_test_visible = fields.Boolean("Proof Load test Visible",compute="_compute_visible")
    proof_load_test_name = fields.Char("Name",default="Proof Load test - (IS 1367 Pt-3 : 2017: 2017)")
    proof_load_test = fields.Float(string="Proof Load test")

    proof_load_test_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_proof_load_test_conformity")

    proof_load_test_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_proof_load_test_nabl")


    @api.depends('proof_load_test','eln_ref','grade')
    def _compute_proof_load_test_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.proof_load_test_conformity = 'na'
                continue
            record.proof_load_test_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','mnbghtrbgt45-107d-4e30-9d3d-2a9009r1209764565')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','mnbghtrbgt45-107d-4e30-9d3d-2a9009r1209764565')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.proof_load_test - record.proof_load_test*mu_value
                    upper = record.proof_load_test + record.proof_load_test*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.proof_load_test_conformity = 'pass'
                        break
                    else:
                        record.proof_load_test_conformity = 'fail'

    @api.depends('proof_load_test','eln_ref','grade')
    def _compute_proof_load_test_nabl(self):
        
        for record in self:
            
            record.proof_load_test_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','mnbghtrbgt45-107d-4e30-9d3d-2a9009r1209764565')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','mnbghtrbgt45-107d-4e30-9d3d-2a9009r1209764565')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.proof_load_test - record.proof_load_test*mu_value
            upper = record.proof_load_test + record.proof_load_test*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.proof_load_test_nabl = 'pass'
                break
            else:
                record.proof_load_test_nabl = 'fail'

    proof_load_test_visible1 = fields.Boolean("Proof Load test Visible",compute="_compute_visible")
    proof_load_test_name1 = fields.Char("Name",default="Proof Load test - (ISO 898 (P-1): 2013: 2013)")
    proof_load_test1 = fields.Float(string="Proof Load test")

    proof_load_test1_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_proof_load_test1_conformity")

    proof_load_test1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_proof_load_test1_nabl")


    @api.depends('proof_load_test1','eln_ref','grade')
    def _compute_proof_load_test1_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.proof_load_test1_conformity = 'na'
                continue
            record.proof_load_test1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poknm5643rgt-107d-4e30-9d3d-2a9009riotyhnb545')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poknm5643rgt-107d-4e30-9d3d-2a9009riotyhnb545')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.proof_load_test1 - record.proof_load_test1*mu_value
                    upper = record.proof_load_test1 + record.proof_load_test1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.proof_load_test1_conformity = 'pass'
                        break
                    else:
                        record.proof_load_test1_conformity = 'fail'

    @api.depends('proof_load_test1','eln_ref','grade')
    def _compute_proof_load_test1_nabl(self):
        
        for record in self:
            
            record.proof_load_test1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poknm5643rgt-107d-4e30-9d3d-2a9009riotyhnb545')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','poknm5643rgt-107d-4e30-9d3d-2a9009riotyhnb545')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.proof_load_test1 - record.proof_load_test1*mu_value
            upper = record.proof_load_test1 + record.proof_load_test1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.proof_load_test1_nabl = 'pass'
                break
            else:
                record.proof_load_test1_nabl = 'fail'

    proof_load_test_visible2 = fields.Boolean("Proof Load test Visible",compute="_compute_visible")
    proof_load_test_name2 = fields.Char("Name",default="Proof Load test - (IS 1367 (Part 3) Clause 8.5: 2017)")
    proof_load_test2 = fields.Float(string="Proof Load test")

    proof_load_test2_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_proof_load_test2_conformity")

    proof_load_test2_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_proof_load_test2_nabl")


    @api.depends('proof_load_test2','eln_ref','grade')
    def _compute_proof_load_test2_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.proof_load_test2_conformity = 'na'
                continue
            record.proof_load_test2_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','yoknfvfvrgt-107d-4e30-2a9009rioty9687jknb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','yoknfvfvrgt-107d-4e30-2a9009rioty9687jknb')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.proof_load_test2 - record.proof_load_test2*mu_value
                    upper = record.proof_load_test2 + record.proof_load_test2*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.proof_load_test2_conformity = 'pass'
                        break
                    else:
                        record.proof_load_test2_conformity = 'fail'

    @api.depends('proof_load_test2','eln_ref','grade')
    def _compute_proof_load_test2_nabl(self):
        
        for record in self:
            
            record.proof_load_test2_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','yoknfvfvrgt-107d-4e30-2a9009rioty9687jknb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','yoknfvfvrgt-107d-4e30-2a9009rioty9687jknb')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.proof_load_test2 - record.proof_load_test2*mu_value
            upper = record.proof_load_test2 + record.proof_load_test2*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.proof_load_test2_nabl = 'pass'
                break
            else:
                record.proof_load_test2_nabl = 'fail'


    shear_strength_visible = fields.Boolean("Shear Strength Visible",compute="_compute_visible")
    shear_strength_name = fields.Char("Name",default="Shear Strength - (IS 12427: 2001 : 2021)")
    shear_strength = fields.Float(string="Shear Strength")

    shear_strength_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_shear_strength_conformity")

    shear_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_shear_strength_nabl")


    @api.depends('shear_strength','eln_ref','grade')
    def _compute_shear_strength_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.shear_strength_conformity = 'na'
                continue
            record.shear_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e8ffec21-b2c6-4273-8831-e4a5f046390c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e8ffec21-b2c6-4273-8831-e4a5f046390c')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.shear_strength - record.shear_strength*mu_value
                    upper = record.shear_strength + record.shear_strength*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.shear_strength_conformity = 'pass'
                        break
                    else:
                        record.shear_strength_conformity = 'fail'

    @api.depends('shear_strength','eln_ref','grade')
    def _compute_shear_strength_nabl(self):
        
        for record in self:
            
            record.shear_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e8ffec21-b2c6-4273-8831-e4a5f046390c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e8ffec21-b2c6-4273-8831-e4a5f046390c')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.shear_strength - record.shear_strength*mu_value
            upper = record.shear_strength + record.shear_strength*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.shear_strength_nabl = 'pass'
                break
            else:
                record.shear_strength_nabl = 'fail'

    tensile_load_bolt_visible = fields.Boolean("Tensile load for full size bolt Visible",compute="_compute_visible")
    tensile_load_bolt_name = fields.Char("Name",default="Tensile load for full size bolt - (IS 1367 (Part 3) Clause 8.2: 2017)")
    tensile_load_bolt = fields.Float(string="Tensile load for full size bolt")

    tensile_load_bolt_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_tensile_load_bolt_conformity")

    tensile_load_bolt_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_tensile_load_bolt_nabl")


    @api.depends('tensile_load_bolt','eln_ref','grade')
    def _compute_tensile_load_bolt_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.tensile_load_bolt_conformity = 'na'
                continue
            record.tensile_load_bolt_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d5f51845-1bf1-431c-b261-ccfd9ccc4ce7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d5f51845-1bf1-431c-b261-ccfd9ccc4ce7')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.tensile_load_bolt - record.tensile_load_bolt*mu_value
                    upper = record.tensile_load_bolt + record.tensile_load_bolt*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.tensile_load_bolt_conformity = 'pass'
                        break
                    else:
                        record.tensile_load_bolt_conformity = 'fail'

    @api.depends('tensile_load_bolt','eln_ref','grade')
    def _compute_tensile_load_bolt_nabl(self):
        
        for record in self:
            
            record.tensile_load_bolt_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d5f51845-1bf1-431c-b261-ccfd9ccc4ce7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d5f51845-1bf1-431c-b261-ccfd9ccc4ce7')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.tensile_load_bolt - record.tensile_load_bolt*mu_value
            upper = record.tensile_load_bolt + record.tensile_load_bolt*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.tensile_load_bolt_nabl = 'pass'
                break
            else:
                record.tensile_load_bolt_nabl = 'fail'


    tensile_load_wedge_visible = fields.Boolean("Tensile load under Wedge loading Visible",compute="_compute_visible")
    tensile_load_wedge_name = fields.Char("Name",default="Tensile load under Wedge loading - (IS 1367 (Part 3) Clause 8.6: 2017)")
    tensile_load_wedge = fields.Float(string="Tensile load under Wedge loading")

    tensile_load_wedge_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_tensile_load_wedge_conformity")

    tensile_load_wedge_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_tensile_load_wedge_nabl")


    @api.depends('tensile_load_wedge','eln_ref','grade')
    def _compute_tensile_load_wedge_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.tensile_load_wedge_conformity = 'na'
                continue
            record.tensile_load_wedge_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a95594db-fe52-4a37-bae8-149d0615ca2f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a95594db-fe52-4a37-bae8-149d0615ca2f')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.tensile_load_wedge - record.tensile_load_wedge*mu_value
                    upper = record.tensile_load_wedge + record.tensile_load_wedge*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.tensile_load_wedge_conformity = 'pass'
                        break
                    else:
                        record.tensile_load_wedge_conformity = 'fail'

    @api.depends('tensile_load_wedge','eln_ref','grade')
    def _compute_tensile_load_wedge_nabl(self):
        
        for record in self:
            
            record.tensile_load_wedge_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a95594db-fe52-4a37-bae8-149d0615ca2f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a95594db-fe52-4a37-bae8-149d0615ca2f')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.tensile_load_wedge - record.tensile_load_wedge*mu_value
            upper = record.tensile_load_wedge + record.tensile_load_wedge*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.tensile_load_wedge_nabl = 'pass'
                break
            else:
                record.tensile_load_wedge_nabl = 'fail'

    tensile_testing_visible = fields.Boolean("Tensile Testing Visible",compute="_compute_visible")
    tensile_testing_name = fields.Char("Name",default="Tensile Testing - (IS 1367 (Part 3) Cl 8.2: 2017)")
    tensile_testing = fields.Float(string="Tensile Testing")

    tensile_testing_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_tensile_testing_conformity")

    tensile_testing_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_tensile_testing_nabl")


    @api.depends('tensile_testing','eln_ref','grade')
    def _compute_tensile_testing_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.tensile_testing_conformity = 'na'
                continue
            record.tensile_testing_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e5b7556-f936-40f0-b7f2-1d023303871b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e5b7556-f936-40f0-b7f2-1d023303871b')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.tensile_testing - record.tensile_testing*mu_value
                    upper = record.tensile_testing + record.tensile_testing*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.tensile_testing_conformity = 'pass'
                        break
                    else:
                        record.tensile_testing_conformity = 'fail'

    @api.depends('tensile_testing','eln_ref','grade')
    def _compute_tensile_testing_nabl(self):
        
        for record in self:
            
            record.tensile_testing_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e5b7556-f936-40f0-b7f2-1d023303871b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8e5b7556-f936-40f0-b7f2-1d023303871b')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.tensile_testing - record.tensile_testing*mu_value
            upper = record.tensile_testing + record.tensile_testing*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.tensile_testing_nabl = 'pass'
                break
            else:
                record.tensile_testing_nabl = 'fail'


    proof_load_bolt_visible = fields.Boolean("Proof Load test Visible",compute="_compute_visible")
    proof_load_bolt_name = fields.Char("Name",default="Proof Load test - (IS 1367 (Part 3) Cl 8.5: 2017)")
    proof_load_bolt = fields.Float(string="Proof Load test")

    proof_load_bolt_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_proof_load_bolt_conformity")

    proof_load_bolt_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_proof_load_bolt_nabl")


    @api.depends('proof_load_bolt','eln_ref','grade')
    def _compute_proof_load_bolt_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.proof_load_bolt_conformity = 'na'
                continue
            record.proof_load_bolt_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9a7ac26-34cf-4859-983c-bec14b8894cb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9a7ac26-34cf-4859-983c-bec14b8894cb')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.proof_load_bolt - record.proof_load_bolt*mu_value
                    upper = record.proof_load_bolt + record.proof_load_bolt*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.proof_load_bolt_conformity = 'pass'
                        break
                    else:
                        record.proof_load_bolt_conformity = 'fail'

    @api.depends('proof_load_bolt','eln_ref','grade')
    def _compute_proof_load_bolt_nabl(self):
        
        for record in self:
            
            record.proof_load_bolt_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9a7ac26-34cf-4859-983c-bec14b8894cb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9a7ac26-34cf-4859-983c-bec14b8894cb')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.proof_load_bolt - record.proof_load_bolt*mu_value
            upper = record.proof_load_bolt + record.proof_load_bolt*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.proof_load_bolt_nabl = 'pass'
                break
            else:
                record.proof_load_bolt_nabl = 'fail'

    
    tensile_test_wedge_visible = fields.Boolean("Tensile test under wedge load test Visible",compute="_compute_visible")
    tensile_test_wedge_name = fields.Char("Name",default="Tensile test under wedge load test - (IS 1367 (Part 3) Cl. 8.6: 2017)")
    tensile_test_wedge = fields.Float(string="Tensile test under wedge load test")

    tensile_test_wedge_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_tensile_test_wedge_conformity")

    tensile_test_wedge_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_tensile_test_wedge_nabl")


    @api.depends('tensile_test_wedge','eln_ref','grade')
    def _compute_tensile_test_wedge_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.tensile_test_wedge_conformity = 'na'
                continue
            record.tensile_test_wedge_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f5c20e7-a493-4fee-a2bc-4b2376c80fe8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f5c20e7-a493-4fee-a2bc-4b2376c80fe8')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.tensile_test_wedge - record.tensile_test_wedge*mu_value
                    upper = record.tensile_test_wedge + record.tensile_test_wedge*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.tensile_test_wedge_conformity = 'pass'
                        break
                    else:
                        record.tensile_test_wedge_conformity = 'fail'

    @api.depends('tensile_test_wedge','eln_ref','grade')
    def _compute_tensile_test_wedge_nabl(self):
        
        for record in self:
            
            record.tensile_test_wedge_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f5c20e7-a493-4fee-a2bc-4b2376c80fe8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5f5c20e7-a493-4fee-a2bc-4b2376c80fe8')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.tensile_test_wedge - record.tensile_test_wedge*mu_value
            upper = record.tensile_test_wedge + record.tensile_test_wedge*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.tensile_test_wedge_nabl = 'pass'
                break
            else:
                record.tensile_test_wedge_nabl = 'fail'


    proof_loaad_test_nut1_visible = fields.Boolean("Proof Load Test Visible",compute="_compute_visible")
    proof_loaad_test_nut1_name = fields.Char("Name",default="Proof Load Test - (IS 1367 (Part 6) Cl 8.1: 2025)")
    proof_loaad_test_nut1 = fields.Float(string="Proof Load Test")

    proof_loaad_test_nut1_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_proof_loaad_test_nut1_conformity")

    proof_loaad_test_nut1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_proof_loaad_test_nut1_nabl")


    @api.depends('proof_loaad_test_nut1','eln_ref','grade')
    def _compute_proof_loaad_test_nut1_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.proof_loaad_test_nut1_conformity = 'na'
                continue
            record.proof_loaad_test_nut1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d39a11e6-b9f6-49cd-8715-e2b35f9b00c0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d39a11e6-b9f6-49cd-8715-e2b35f9b00c0')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.proof_loaad_test_nut1 - record.proof_loaad_test_nut1*mu_value
                    upper = record.proof_loaad_test_nut1 + record.proof_loaad_test_nut1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.proof_loaad_test_nut1_conformity = 'pass'
                        break
                    else:
                        record.proof_loaad_test_nut1_conformity = 'fail'

    @api.depends('proof_loaad_test_nut1','eln_ref','grade')
    def _compute_proof_loaad_test_nut1_nabl(self):
        
        for record in self:
            
            record.proof_loaad_test_nut1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d39a11e6-b9f6-49cd-8715-e2b35f9b00c0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d39a11e6-b9f6-49cd-8715-e2b35f9b00c0')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.proof_loaad_test_nut1 - record.proof_loaad_test_nut1*mu_value
            upper = record.proof_loaad_test_nut1 + record.proof_loaad_test_nut1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.proof_loaad_test_nut1_nabl = 'pass'
                break
            else:
                record.proof_loaad_test_nut1_nabl = 'fail'

    
    proof_loaad_test_nut2_visible = fields.Boolean("Proof Load Test Visible",compute="_compute_visible")
    proof_loaad_test_nut2_name = fields.Char("Name",default="Proof Load Test - (IS 1367 (Part 6) Cl 8.1: 2025)")
    proof_loaad_test_nut2 = fields.Float(string="Proof Load Test")

    proof_loaad_test_nut2_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_proof_loaad_test_nut2_conformity")

    proof_loaad_test_nut2_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_proof_loaad_test_nut2_nabl")


    @api.depends('proof_loaad_test_nut2','eln_ref','grade')
    def _compute_proof_loaad_test_nut2_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.proof_loaad_test_nut2_conformity = 'na'
                continue
            record.proof_loaad_test_nut2_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','88f412c0-4222-4b4d-803b-6d9789c4d113')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','88f412c0-4222-4b4d-803b-6d9789c4d113')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.proof_loaad_test_nut2 - record.proof_loaad_test_nut2*mu_value
                    upper = record.proof_loaad_test_nut2 + record.proof_loaad_test_nut2*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.proof_loaad_test_nut2_conformity = 'pass'
                        break
                    else:
                        record.proof_loaad_test_nut2_conformity = 'fail'

    @api.depends('proof_loaad_test_nut2','eln_ref','grade')
    def _compute_proof_loaad_test_nut2_nabl(self):
        
        for record in self:
            
            record.proof_loaad_test_nut2_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','88f412c0-4222-4b4d-803b-6d9789c4d113')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','88f412c0-4222-4b4d-803b-6d9789c4d113')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.proof_loaad_test_nut2 - record.proof_loaad_test_nut2*mu_value
            upper = record.proof_loaad_test_nut2 + record.proof_loaad_test_nut2*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.proof_loaad_test_nut2_nabl = 'pass'
                break
            else:
                record.proof_loaad_test_nut2_nabl = 'fail'



    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
    
            record.proof_load_test_visible = False
            record.proof_load_test_visible1 = False
            record.proof_load_test_visible2 = False

            record.shear_strength_visible = False

            record.tensile_load_bolt_visible = False

            record.tensile_load_wedge_visible = False

            record.tensile_testing_visible = False

            record.proof_load_bolt_visible = False

            record.tensile_test_wedge_visible = False

            record.proof_loaad_test_nut1_visible = False

            record.proof_loaad_test_nut2_visible = False
            
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
               
                if sample.internal_id == "mnbghtrbgt45-107d-4e30-9d3d-2a9009r1209764565":
                    record.proof_load_test_visible = True 
                if sample.internal_id == "poknm5643rgt-107d-4e30-9d3d-2a9009riotyhnb545":
                    record.proof_load_test_visible1 = True 
                if sample.internal_id == "yoknfvfvrgt-107d-4e30-2a9009rioty9687jknb":
                    record.proof_load_test_visible2 = True 

                if sample.internal_id == "e8ffec21-b2c6-4273-8831-e4a5f046390c":
                    record.shear_strength_visible = True 
                
                if sample.internal_id == "d5f51845-1bf1-431c-b261-ccfd9ccc4ce7":
                    record.tensile_load_bolt_visible = True 
                
                if sample.internal_id == "a95594db-fe52-4a37-bae8-149d0615ca2f":
                    record.tensile_load_wedge_visible = True 

                if sample.internal_id == "8e5b7556-f936-40f0-b7f2-1d023303871b":
                    record.tensile_testing_visible = True 

                if sample.internal_id == "e9a7ac26-34cf-4859-983c-bec14b8894cb":
                    record.proof_load_bolt_visible = True 

                if sample.internal_id == "5f5c20e7-a493-4fee-a2bc-4b2376c80fe8":
                    record.tensile_test_wedge_visible = True 

                if sample.internal_id == "d39a11e6-b9f6-49cd-8715-e2b35f9b00c0":
                    record.proof_loaad_test_nut1_visible = True 

                if sample.internal_id == "88f412c0-4222-4b4d-803b-6d9789c4d113":
                    record.proof_loaad_test_nut2_visible = True 
               
               
                

                
     
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
     

            if result.parameter.internal_id == 'mnbghtrbgt45-107d-4e30-9d3d-2a9009r1209764565':
                result.result_char = round(self.proof_load_test,2)
                result.calculated = True
                if self.proof_load_test_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'poknm5643rgt-107d-4e30-9d3d-2a9009riotyhnb545':
                result.result_char = round(self.proof_load_test1,2)
                result.calculated = True
                if self.proof_load_test1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            if result.parameter.internal_id == 'yoknfvfvrgt-107d-4e30-2a9009rioty9687jknb':
                result.result_char = round(self.proof_load_test2,2)
                result.calculated = True
                if self.proof_load_test2_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            
            if result.parameter.internal_id == 'e8ffec21-b2c6-4273-8831-e4a5f046390c':
                result.result_char = round(self.shear_strength,2)
                result.calculated = True
                if self.shear_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'd5f51845-1bf1-431c-b261-ccfd9ccc4ce7':
                result.result_char = round(self.tensile_load_bolt,2)
                result.calculated = True
                if self.tensile_load_bolt_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'a95594db-fe52-4a37-bae8-149d0615ca2f':
                result.result_char = round(self.tensile_load_wedge,2)
                result.calculated = True
                if self.tensile_load_wedge_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '8e5b7556-f936-40f0-b7f2-1d023303871b':
                result.result_char = round(self.tensile_testing,2)
                result.calculated = True
                if self.tensile_testing_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            
            if result.parameter.internal_id == 'e9a7ac26-34cf-4859-983c-bec14b8894cb':
                result.result_char = round(self.proof_load_bolt,2)
                result.calculated = True
                if self.proof_load_bolt_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '5f5c20e7-a493-4fee-a2bc-4b2376c80fe8':
                result.result_char = round(self.tensile_test_wedge,2)
                result.calculated = True
                if self.tensile_test_wedge_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'd39a11e6-b9f6-49cd-8715-e2b35f9b00c0':
                result.result_char = round(self.proof_loaad_test_nut1,2)
                result.calculated = True
                if self.proof_loaad_test_nut1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '88f412c0-4222-4b4d-803b-6d9789c4d113':
                result.result_char = round(self.proof_loaad_test_nut2,2)
                result.calculated = True
                if self.proof_loaad_test_nut2_nabl == 'pass':
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
        record = super(MechanicalFastenerBolts, self).create(vals)
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
        record = self.env['mechanical.fastener.bolts'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values





class FastenerBoltsNotes(models.Model):
    _name = "fastener.bolts.notes"

    parent_id = fields.Many2one('mechanical.fastener.bolts',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
