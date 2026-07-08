from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class MechanicalFerrousPoduct(models.Model):
    _name = "mechanical.ferrous.product"
    _inherit = "lerm.eln"
    _rec_name = "name2"

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    name2 = fields.Char("Name",default="Ferrous Materials, Alloys & Products")
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

    notes_id = fields.One2many('ferrous.product.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(MechanicalFerrousPoduct, self).default_get(fields)

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


    double_shear_strength_visible = fields.Boolean("Double Shear strength Visible",compute="_compute_visible")
    double_shear_strength_name = fields.Char("Name",default="Double Shear strength - (IS 5242: 1979 : 2022)")
    double_shear_strength = fields.Float(string="Double Shear strength")

    double_shear_strength_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_double_shear_strength_conformity")

    double_shear_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_double_shear_strength_nabl")


    @api.depends('double_shear_strength','eln_ref','grade')
    def _compute_double_shear_strength_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.double_shear_strength_conformity = 'na'
                continue
            record.double_shear_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0okjui67c-107d-4e30-9d3d-2a9009r98jhnbhy45')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0okjui67c-107d-4e30-9d3d-2a9009r98jhnbhy45')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.double_shear_strength - record.double_shear_strength*mu_value
                    upper = record.double_shear_strength + record.double_shear_strength*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.double_shear_strength_conformity = 'pass'
                        break
                    else:
                        record.double_shear_strength_conformity = 'fail'

    @api.depends('double_shear_strength','eln_ref','grade')
    def _compute_double_shear_strength_nabl(self):
        
        for record in self:
            
            record.double_shear_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0okjui67c-107d-4e30-9d3d-2a9009r98jhnbhy45')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0okjui67c-107d-4e30-9d3d-2a9009r98jhnbhy45')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.double_shear_strength - record.double_shear_strength*mu_value
            upper = record.double_shear_strength + record.double_shear_strength*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.double_shear_strength_nabl = 'pass'
                break
            else:
                record.double_shear_strength_nabl = 'fail'

    yield_strength_visible = fields.Boolean("Yield Strength Visible",compute="_compute_visible")
    yield_strength_name = fields.Char("Name",default="Yield Strength - (ASTM A 370 a: 2024)")
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8iu76y643rgt-107d-4e30-9d3d-2a9009roiu890nh')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8iu76y643rgt-107d-4e30-9d3d-2a9009roiu890nh')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8iu76y643rgt-107d-4e30-9d3d-2a9009roiu890nh')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8iu76y643rgt-107d-4e30-9d3d-2a9009roiu890nh')]).parameter_table
            
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

    elongation_visible = fields.Boolean("% Elongation Visible",compute="_compute_visible")
    elongation_name = fields.Char("Name",default="% Elongation - (ASTM A 370: 2024)")
    elongation = fields.Float(string="% Elongation")

    elongation_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_elongation_conformity")

    elongation_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_elongation_nabl")


    @api.depends('elongation','eln_ref','grade')
    def _compute_elongation_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.elongation_conformity = 'na'
                continue
            record.elongation_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f19a8f44-6ebe-4039-87f5-303a861b5032')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f19a8f44-6ebe-4039-87f5-303a861b5032')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.elongation - record.elongation*mu_value
                    upper = record.elongation + record.elongation*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.elongation_conformity = 'pass'
                        break
                    else:
                        record.elongation_conformity = 'fail'

    @api.depends('elongation','eln_ref','grade')
    def _compute_elongation_nabl(self):
        
        for record in self:
            
            record.elongation_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f19a8f44-6ebe-4039-87f5-303a861b5032')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f19a8f44-6ebe-4039-87f5-303a861b5032')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.elongation - record.elongation*mu_value
            upper = record.elongation + record.elongation*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.elongation_nabl = 'pass'
                break
            else:
                record.elongation_nabl = 'fail'


    elongation_visible1 = fields.Boolean("% Elongation Visible",compute="_compute_visible")
    elongation_name1 = fields.Char("Name",default="% Elongation - (ISO 6892-1 : 2019: 2019)")
    elongation1 = fields.Float(string="% Elongation")

    elongation1_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_elongation1_conformity")

    elongation1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_elongation1_nabl")


    @api.depends('elongation1','eln_ref','grade')
    def _compute_elongation1_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.elongation1_conformity = 'na'
                continue
            record.elongation1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ed2b93b9-d941-4897-8d28-34b58f9d3c14')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ed2b93b9-d941-4897-8d28-34b58f9d3c14')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.elongation1 - record.elongation1*mu_value
                    upper = record.elongation1 + record.elongation1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.elongation1_conformity = 'pass'
                        break
                    else:
                        record.elongation1_conformity = 'fail'

    @api.depends('elongation1','eln_ref','grade')
    def _compute_elongation1_nabl(self):
        
        for record in self:
            
            record.elongation1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ed2b93b9-d941-4897-8d28-34b58f9d3c14')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ed2b93b9-d941-4897-8d28-34b58f9d3c14')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.elongation1 - record.elongation1*mu_value
            upper = record.elongation1 + record.elongation1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.elongation1_nabl = 'pass'
                break
            else:
                record.elongation1_nabl = 'fail'

    reduction_area_visible = fields.Boolean("% Reduction in area Visible",compute="_compute_visible")
    reduction_area_name = fields.Char("Name",default="% Reduction in area - (ASTM A 370 a: 2023)")
    reduction_area = fields.Float(string="% Reduction in area")

    reduction_area_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_reduction_area_conformity")

    reduction_area_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_reduction_area_nabl")


    @api.depends('reduction_area','eln_ref','grade')
    def _compute_reduction_area_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.reduction_area_conformity = 'na'
                continue
            record.reduction_area_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0519d498-037d-4ef5-a8c1-00865a94b76c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0519d498-037d-4ef5-a8c1-00865a94b76c')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.reduction_area - record.reduction_area*mu_value
                    upper = record.reduction_area + record.reduction_area*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.reduction_area_conformity = 'pass'
                        break
                    else:
                        record.reduction_area_conformity = 'fail'

    @api.depends('reduction_area','eln_ref','grade')
    def _compute_reduction_area_nabl(self):
        
        for record in self:
            
            record.reduction_area_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0519d498-037d-4ef5-a8c1-00865a94b76c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0519d498-037d-4ef5-a8c1-00865a94b76c')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.reduction_area - record.reduction_area*mu_value
            upper = record.reduction_area + record.reduction_area*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.reduction_area_nabl = 'pass'
                break
            else:
                record.reduction_area_nabl = 'fail'


    proof_strss_visible = fields.Boolean("0.2 % Proof Stress Visible",compute="_compute_visible")
    proof_strss_name = fields.Char("Name",default="0.2 % Proof Stress - (ASTM E8/E8M: 2022)")
    proof_strss = fields.Float(string="0.2 % Proof Stress")

    proof_strss_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_proof_strss_conformity")

    proof_strss_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_proof_strss_nabl")


    @api.depends('proof_strss','eln_ref','grade')
    def _compute_proof_strss_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.proof_strss_conformity = 'na'
                continue
            record.proof_strss_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','43e5c105-5285-4540-bdda-eceb731c6944')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','43e5c105-5285-4540-bdda-eceb731c6944')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.proof_strss - record.proof_strss*mu_value
                    upper = record.proof_strss + record.proof_strss*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.proof_strss_conformity = 'pass'
                        break
                    else:
                        record.proof_strss_conformity = 'fail'

    @api.depends('proof_strss','eln_ref','grade')
    def _compute_proof_strss_nabl(self):
        
        for record in self:
            
            record.proof_strss_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','43e5c105-5285-4540-bdda-eceb731c6944')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','43e5c105-5285-4540-bdda-eceb731c6944')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.proof_strss - record.proof_strss*mu_value
            upper = record.proof_strss + record.proof_strss*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.proof_strss_nabl = 'pass'
                break
            else:
                record.proof_strss_nabl = 'fail'

    proof_stress_visible1 = fields.Boolean("0.2 % Proof Stress Visible",compute="_compute_visible")
    proof_stress_name1 = fields.Char("Name",default="0.2 % Proof Stress - (ASTM A 370 a: 2024)")
    proof_stress1 = fields.Float(string="0.2 % Proof Stress")

    proof_stress1_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_proof_stress1_conformity")

    proof_stress1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_proof_stress1_nabl")


    @api.depends('proof_stress1','eln_ref','grade')
    def _compute_proof_stress1_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.proof_stress1_conformity = 'na'
                continue
            record.proof_stress1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7ff3ff7f-8f2b-49d8-96e1-1069f6139462')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7ff3ff7f-8f2b-49d8-96e1-1069f6139462')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.proof_stress1 - record.proof_stress1*mu_value
                    upper = record.proof_stress1 + record.proof_stress1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.proof_stress1_conformity = 'pass'
                        break
                    else:
                        record.proof_stress1_conformity = 'fail'

    @api.depends('proof_stress1','eln_ref','grade')
    def _compute_proof_stress1_nabl(self):
        
        for record in self:
            
            record.proof_stress1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7ff3ff7f-8f2b-49d8-96e1-1069f6139462')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7ff3ff7f-8f2b-49d8-96e1-1069f6139462')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.proof_stress1 - record.proof_stress1*mu_value
            upper = record.proof_stress1 + record.proof_stress1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.proof_stress1_nabl = 'pass'
                break
            else:
                record.proof_stress1_nabl = 'fail'


    brinell_2_5_250_visible = fields.Boolean("Brinell Hardness 2.5/250 Visible",compute="_compute_visible")
    brinell_2_5_250_name = fields.Char("Name",default="Brinell Hardness 2.5/250 - (IS 1500 (Part 1): 2019: 2024)")
    brinell_2_5_250 = fields.Float(string="Brinell Hardness 2.5/250")

    brinell_2_5_250_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_brinell_2_5_250_conformity")

    brinell_2_5_250_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_brinell_2_5_250_nabl")


    @api.depends('brinell_2_5_250','eln_ref','grade')
    def _compute_brinell_2_5_250_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.brinell_2_5_250_conformity = 'na'
                continue
            record.brinell_2_5_250_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','618e99db-7d15-40d2-a03e-98457e778315')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','618e99db-7d15-40d2-a03e-98457e778315')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.brinell_2_5_250 - record.brinell_2_5_250*mu_value
                    upper = record.brinell_2_5_250 + record.brinell_2_5_250*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.brinell_2_5_250_conformity = 'pass'
                        break
                    else:
                        record.brinell_2_5_250_conformity = 'fail'

    @api.depends('brinell_2_5_250','eln_ref','grade')
    def _compute_brinell_2_5_250_nabl(self):
        
        for record in self:
            
            record.brinell_2_5_250_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','618e99db-7d15-40d2-a03e-98457e778315')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','618e99db-7d15-40d2-a03e-98457e778315')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.brinell_2_5_250 - record.brinell_2_5_250*mu_value
            upper = record.brinell_2_5_250 + record.brinell_2_5_250*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.brinell_2_5_250_nabl = 'pass'
                break
            else:
                record.brinell_2_5_250_nabl = 'fail'

    
    brinell_2_5_250_visible1 = fields.Boolean("Brinell Hardness 2.5/250 Visible",compute="_compute_visible")
    brinell_2_5_250_name1 = fields.Char("Name",default="Brinell Hardness 2.5/250 - (ISO 6506 (Part 1): 2014: 2014)")
    brinell_2_5_2501 = fields.Float(string="Brinell Hardness 2.5/250")

    brinell_2_5_2501_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_brinell_2_5_2501_conformity")

    brinell_2_5_2501_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_brinell_2_5_2501_nabl")


    @api.depends('brinell_2_5_2501','eln_ref','grade')
    def _compute_brinell_2_5_2501_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.brinell_2_5_2501_conformity = 'na'
                continue
            record.brinell_2_5_2501_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cb2bd2ab-2986-44b7-bde6-330be8149816')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cb2bd2ab-2986-44b7-bde6-330be8149816')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.brinell_2_5_2501 - record.brinell_2_5_2501*mu_value
                    upper = record.brinell_2_5_2501 + record.brinell_2_5_2501*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.brinell_2_5_2501_conformity = 'pass'
                        break
                    else:
                        record.brinell_2_5_2501_conformity = 'fail'

    @api.depends('brinell_2_5_2501','eln_ref','grade')
    def _compute_brinell_2_5_2501_nabl(self):
        
        for record in self:
            
            record.brinell_2_5_2501_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cb2bd2ab-2986-44b7-bde6-330be8149816')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cb2bd2ab-2986-44b7-bde6-330be8149816')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.brinell_2_5_2501 - record.brinell_2_5_2501*mu_value
            upper = record.brinell_2_5_2501 + record.brinell_2_5_2501*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.brinell_2_5_2501_nabl = 'pass'
                break
            else:
                record.brinell_2_5_2501_nabl = 'fail'


    brinell_5_250_visible = fields.Boolean("Brinell Hardness 5/250 Visible",compute="_compute_visible")
    brinell_5_250_name = fields.Char("Name",default="Brinell Hardness 5/250 - (IS 1500 (Part 1): 2019: 2024)")
    brinell_5_250 = fields.Float(string="Brinell Hardness 5/250")

    brinell_5_250_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_brinell_5_250_conformity")

    brinell_5_250_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_brinell_5_250_nabl")


    @api.depends('brinell_5_250','eln_ref','grade')
    def _compute_brinell_5_250_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.brinell_5_250_conformity = 'na'
                continue
            record.brinell_5_250_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','724610c7-9359-498c-9e29-029d1f44ab93')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','724610c7-9359-498c-9e29-029d1f44ab93')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.brinell_5_250 - record.brinell_5_250*mu_value
                    upper = record.brinell_5_250 + record.brinell_5_250*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.brinell_5_250_conformity = 'pass'
                        break
                    else:
                        record.brinell_5_250_conformity = 'fail'

    @api.depends('brinell_5_250','eln_ref','grade')
    def _compute_brinell_5_250_nabl(self):
        
        for record in self:
            
            record.brinell_5_250_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','724610c7-9359-498c-9e29-029d1f44ab93')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','724610c7-9359-498c-9e29-029d1f44ab93')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.brinell_5_250 - record.brinell_5_250*mu_value
            upper = record.brinell_5_250 + record.brinell_5_250*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.brinell_5_250_nabl = 'pass'
                break
            else:
                record.brinell_5_250_nabl = 'fail'

    
    brinell_5_250_visible1 = fields.Boolean("Brinell Hardness 5/250 Visible",compute="_compute_visible")
    brinell_5_250_name1 = fields.Char("Name",default="Brinell Hardness 5/250 - (ISO 6506 (Part 1): 2014: 2014)")
    brinell_5_2501 = fields.Float(string="Brinell Hardness 5/250")

    brinell_5_2501_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_brinell_5_2501_conformity")

    brinell_5_2501_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_brinell_5_2501_nabl")


    @api.depends('brinell_5_2501','eln_ref','grade')
    def _compute_brinell_5_2501_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.brinell_5_2501_conformity = 'na'
                continue
            record.brinell_5_2501_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','92865cd2-4a1c-496c-948f-f3ec9e7ec05a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','92865cd2-4a1c-496c-948f-f3ec9e7ec05a')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.brinell_5_2501 - record.brinell_5_2501*mu_value
                    upper = record.brinell_5_2501 + record.brinell_5_2501*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.brinell_5_2501_conformity = 'pass'
                        break
                    else:
                        record.brinell_5_2501_conformity = 'fail'

    @api.depends('brinell_5_2501','eln_ref','grade')
    def _compute_brinell_5_2501_nabl(self):
        
        for record in self:
            
            record.brinell_5_2501_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','92865cd2-4a1c-496c-948f-f3ec9e7ec05a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','92865cd2-4a1c-496c-948f-f3ec9e7ec05a')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.brinell_5_2501 - record.brinell_5_2501*mu_value
            upper = record.brinell_5_2501 + record.brinell_5_2501*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.brinell_5_2501_nabl = 'pass'
                break
            else:
                record.brinell_5_2501_nabl = 'fail'



    rockwell_hrbw_visible = fields.Boolean("Rockwell Hardness HRBW Visible",compute="_compute_visible")
    rockwell_hrbw_name = fields.Char("Name",default="Rockwell Hardness HRBW - (ISO 6508 (Part 1): 2016: 2023)")
    rockwell_hrbw = fields.Float(string="Rockwell Hardness HRBW")

    rockwell_hrbw_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_rockwell_hrbw_conformity")

    rockwell_hrbw_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_rockwell_hrbw_nabl")


    @api.depends('rockwell_hrbw','eln_ref','grade')
    def _compute_rockwell_hrbw_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.rockwell_hrbw_conformity = 'na'
                continue
            record.rockwell_hrbw_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ef7334ab-c781-4f43-88f8-ddd262b2bdd9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ef7334ab-c781-4f43-88f8-ddd262b2bdd9')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.rockwell_hrbw - record.rockwell_hrbw*mu_value
                    upper = record.rockwell_hrbw + record.rockwell_hrbw*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.rockwell_hrbw_conformity = 'pass'
                        break
                    else:
                        record.rockwell_hrbw_conformity = 'fail'

    @api.depends('rockwell_hrbw','eln_ref','grade')
    def _compute_rockwell_hrbw_nabl(self):
        
        for record in self:
            
            record.rockwell_hrbw_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ef7334ab-c781-4f43-88f8-ddd262b2bdd9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ef7334ab-c781-4f43-88f8-ddd262b2bdd9')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.rockwell_hrbw - record.rockwell_hrbw*mu_value
            upper = record.rockwell_hrbw + record.rockwell_hrbw*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.rockwell_hrbw_nabl = 'pass'
                break
            else:
                record.rockwell_hrbw_nabl = 'fail'

    rockwell_hrc_visible = fields.Boolean("Rockwell Hardness HRC Visible",compute="_compute_visible")
    rockwell_hrc_name = fields.Char("Name",default="Rockwell Hardness HRC - (ISO 6508 (Part 1): 2016: 2023)")
    rockwell_hrc = fields.Float(string="Rockwell Hardness HRC")

    rockwell_hrc_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_rockwell_hrc_conformity")

    rockwell_hrc_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_rockwell_hrc_nabl")


    @api.depends('rockwell_hrc','eln_ref','grade')
    def _compute_rockwell_hrc_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.rockwell_hrc_conformity = 'na'
                continue
            record.rockwell_hrc_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','05445bfa-79d6-4acd-ab0b-4de192f38427')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','05445bfa-79d6-4acd-ab0b-4de192f38427')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.rockwell_hrc - record.rockwell_hrc*mu_value
                    upper = record.rockwell_hrc + record.rockwell_hrc*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.rockwell_hrc_conformity = 'pass'
                        break
                    else:
                        record.rockwell_hrc_conformity = 'fail'

    @api.depends('rockwell_hrc','eln_ref','grade')
    def _compute_rockwell_hrc_nabl(self):
        
        for record in self:
            
            record.rockwell_hrc_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','05445bfa-79d6-4acd-ab0b-4de192f38427')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','05445bfa-79d6-4acd-ab0b-4de192f38427')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.rockwell_hrc - record.rockwell_hrc*mu_value
            upper = record.rockwell_hrc + record.rockwell_hrc*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.rockwell_hrc_nabl = 'pass'
                break
            else:
                record.rockwell_hrc_nabl = 'fail'


    tensile_strength_visible1 = fields.Boolean("Tensile Strength Visible",compute="_compute_visible")
    tensile_strength_name1 = fields.Char("Name",default="Tensile Strength - (ISO 6892-1 : 2019: 2019)")
    tensile_strength1 = fields.Float(string="Tensile Strength")

    tensile_strength1_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_tensile_strength1_conformity")

    tensile_strength1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_tensile_strength1_nabl")


    @api.depends('tensile_strength1','eln_ref','grade')
    def _compute_tensile_strength1_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.tensile_strength1_conformity = 'na'
                continue
            record.tensile_strength1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ae131ed1-5258-49f9-b04a-44be4680f35c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ae131ed1-5258-49f9-b04a-44be4680f35c')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.tensile_strength1 - record.tensile_strength1*mu_value
                    upper = record.tensile_strength1 + record.tensile_strength1*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.tensile_strength1_conformity = 'pass'
                        break
                    else:
                        record.tensile_strength1_conformity = 'fail'

    @api.depends('tensile_strength1','eln_ref','grade')
    def _compute_tensile_strength1_nabl(self):
        
        for record in self:
            
            record.tensile_strength1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ae131ed1-5258-49f9-b04a-44be4680f35c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ae131ed1-5258-49f9-b04a-44be4680f35c')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.tensile_strength1 - record.tensile_strength1*mu_value
            upper = record.tensile_strength1 + record.tensile_strength1*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.tensile_strength1_nabl = 'pass'
                break
            else:
                record.tensile_strength1_nabl = 'fail'


    yield_strength_visible1 = fields.Boolean("Yield Strength Visible",compute="_compute_visible")
    yield_strength_name1 = fields.Char("Name",default="Yield Strength - (ISO 6892-1 : 2019: 2019)")
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','899aaab4-f013-49e3-b5b2-9daf72233bb8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','899aaab4-f013-49e3-b5b2-9daf72233bb8')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','899aaab4-f013-49e3-b5b2-9daf72233bb8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','899aaab4-f013-49e3-b5b2-9daf72233bb8')]).parameter_table
            
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

    charpy_impact_visible = fields.Boolean("Charpy Impact test V notch Visible",compute="_compute_visible")
    charpy_impact_name = fields.Char("Name",default="Charpy Impact test V notch - (ISO 148 (Part 1) : 2016: 2016)")
    charpy_impact = fields.Char(string="Charpy Impact test V notch")
    charpy_impact_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non-NABL'),
        ],
        string="Test Type",
        default='nabl',
    )



    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
    
            record.double_shear_strength_visible = False
            record.yield_strength_visible = False
            record.elongation_visible = False

            record.elongation_visible1 = False

            record.reduction_area_visible = False

            record.proof_strss_visible = False

            record.proof_stress_visible1 = False

            record.brinell_2_5_250_visible = False

            record.brinell_2_5_250_visible1 = False

            record.brinell_5_250_visible = False

            record.brinell_5_250_visible1 = False

            record.rockwell_hrbw_visible = False

            record.rockwell_hrc_visible = False

            record.tensile_strength_visible1 = False

            record.yield_strength_visible1 = False

            record.charpy_impact_visible = False
            
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
               
                if sample.internal_id == "0okjui67c-107d-4e30-9d3d-2a9009r98jhnbhy45":
                    record.double_shear_strength_visible = True 
                if sample.internal_id == "8iu76y643rgt-107d-4e30-9d3d-2a9009roiu890nh":
                    record.yield_strength_visible = True 
                if sample.internal_id == "f19a8f44-6ebe-4039-87f5-303a861b5032":
                    record.elongation_visible = True 

                if sample.internal_id == "ed2b93b9-d941-4897-8d28-34b58f9d3c14":
                    record.elongation_visible1 = True 
                
                if sample.internal_id == "0519d498-037d-4ef5-a8c1-00865a94b76c":
                    record.reduction_area_visible = True 
                
                if sample.internal_id == "43e5c105-5285-4540-bdda-eceb731c6944":
                    record.proof_strss_visible = True 

                if sample.internal_id == "7ff3ff7f-8f2b-49d8-96e1-1069f6139462":
                    record.proof_stress_visible1 = True 

                if sample.internal_id == "618e99db-7d15-40d2-a03e-98457e778315":
                    record.brinell_2_5_250_visible = True 

                if sample.internal_id == "cb2bd2ab-2986-44b7-bde6-330be8149816":
                    record.brinell_2_5_250_visible1 = True 

                if sample.internal_id == "724610c7-9359-498c-9e29-029d1f44ab93":
                    record.brinell_5_250_visible = True 

                if sample.internal_id == "92865cd2-4a1c-496c-948f-f3ec9e7ec05a":
                    record.brinell_5_250_visible1 = True 
                
                if sample.internal_id == "ef7334ab-c781-4f43-88f8-ddd262b2bdd9":
                    record.rockwell_hrbw_visible = True

                if sample.internal_id == "05445bfa-79d6-4acd-ab0b-4de192f38427":
                    record.rockwell_hrc_visible = True

                if sample.internal_id == "ae131ed1-5258-49f9-b04a-44be4680f35c":
                    record.tensile_strength_visible1 = True

                if sample.internal_id == "899aaab4-f013-49e3-b5b2-9daf72233bb8":
                    record.yield_strength_visible1 = True

                if sample.internal_id == "8fb31161-2670-4987-9f53-2c96dee66b12":
                    record.charpy_impact_visible = True
               
               
                

                
     
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
     

            if result.parameter.internal_id == '0okjui67c-107d-4e30-9d3d-2a9009r98jhnbhy45':
                result.result_char = round(self.double_shear_strength,2)
                result.calculated = True
                if self.double_shear_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '8iu76y643rgt-107d-4e30-9d3d-2a9009roiu890nh':
                result.result_char = round(self.yield_strength,2)
                result.calculated = True
                if self.yield_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            if result.parameter.internal_id == 'f19a8f44-6ebe-4039-87f5-303a861b5032':
                result.result_char = round(self.elongation,2)
                result.calculated = True
                if self.elongation_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            
            if result.parameter.internal_id == 'ed2b93b9-d941-4897-8d28-34b58f9d3c14':
                result.result_char = round(self.elongation1,2)
                result.calculated = True
                if self.elongation1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '0519d498-037d-4ef5-a8c1-00865a94b76c':
                result.result_char = round(self.reduction_area,2)
                result.calculated = True
                if self.reduction_area_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '43e5c105-5285-4540-bdda-eceb731c6944':
                result.result_char = round(self.proof_strss,2)
                result.calculated = True
                if self.proof_strss_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '7ff3ff7f-8f2b-49d8-96e1-1069f6139462':
                result.result_char = round(self.proof_stress1,2)
                result.calculated = True
                if self.proof_stress1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 
            
            if result.parameter.internal_id == '618e99db-7d15-40d2-a03e-98457e778315':
                result.result_char = round(self.brinell_2_5_250,2)
                result.calculated = True
                if self.brinell_2_5_250_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'cb2bd2ab-2986-44b7-bde6-330be8149816':
                result.result_char = round(self.brinell_2_5_2501,2)
                result.calculated = True
                if self.brinell_2_5_2501_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '724610c7-9359-498c-9e29-029d1f44ab93':
                result.result_char = round(self.brinell_5_250,2)
                result.calculated = True
                if self.brinell_5_250_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '92865cd2-4a1c-496c-948f-f3ec9e7ec05a':
                result.result_char = round(self.brinell_5_2501,2)
                result.calculated = True
                if self.brinell_5_2501_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'ef7334ab-c781-4f43-88f8-ddd262b2bdd9':
                result.result_char = round(self.rockwell_hrbw,2)
                result.calculated = True
                if self.rockwell_hrbw_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '05445bfa-79d6-4acd-ab0b-4de192f38427':
                result.result_char = round(self.rockwell_hrc,2)
                result.calculated = True
                if self.rockwell_hrc_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'ae131ed1-5258-49f9-b04a-44be4680f35c':
                result.result_char = round(self.tensile_strength1,2)
                result.calculated = True
                if self.tensile_strength1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '899aaab4-f013-49e3-b5b2-9daf72233bb8':
                result.result_char = round(self.yield_strength1,2)
                result.calculated = True
                if self.yield_strength1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '8fb31161-2670-4987-9f53-2c96dee66b12':
                # result.result_char = round(self.yield_strength1,2)
                result.calculated = True
                # if self.yield_strength1_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
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
        record = super(MechanicalFerrousPoduct, self).create(vals)
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
        record = self.env['mechanical.ferrous.product'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values





class FerrousProductNotes(models.Model):
    _name = "ferrous.product.notes"

    parent_id = fields.Many2one('mechanical.ferrous.product',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
