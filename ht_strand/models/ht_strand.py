from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math



class HtStrand(models.Model):
    _name = "ht.strand"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="HT STRAND")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)




# remark

    notes_id = fields.One2many('htstrand.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(HtStrand, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The information marked with an # received from customer',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'The results listed refer only to tested parameters and sample as received from customer',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'The balance samples if any will be discarded after 15 days from the date of issue of test certificate unless otherwise specified.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'This document shall not be reproduced in part or full without the approval of Genstru.',
            }),
        ]

        res['notes_id'] = default_notes
        return res


    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id



    ht_strand_name = fields.Char("Name",default=" Ht")
    ht_strand_visible = fields.Boolean("Chequered Visible",compute="_compute_visible")   

    diameter = fields.Float(string="Outer Strand Dia , mm")
    crossectional_area = fields.Float(string="Nominal Area of Strand (mm2)",compute="_compute_crossectional_area")
    crossectional_area_visible = fields.Boolean("Nominal Area",compute="_compute_visible")

    requirement_crossectional_area = fields.Char(string="Requirement")

    crossectional_area_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string=" Conformity", compute="_compute_crossectional_area_conformity", store=True)


    @api.depends('crossectional_area','eln_ref','grade')
    def _compute_crossectional_area_conformity(self):
        
        for record in self:
            record.crossectional_area_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65895-a3df-4990-93d1-9904984644aoo2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65895-a3df-4990-93d1-9904984644aoo2')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.crossectional_area - record.crossectional_area*mu_value
                    upper = record.crossectional_area + record.crossectional_area*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.crossectional_area_conformity = 'pass'
                        break
                    else:
                        record.crossectional_area_conformity = 'fail'

    crossectional_area_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string=" NABL", compute="_compute_crossectional_area_nabl", store=True)

    @api.depends('crossectional_area','eln_ref','grade')
    def _compute_crossectional_area_nabl(self):
        
        for record in self:
            record.crossectional_area_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65895-a3df-4990-93d1-9904984644aoo2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','65895-a3df-4990-93d1-9904984644aoo2')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.crossectional_area - record.crossectional_area*mu_value
                    upper = record.crossectional_area + record.crossectional_area*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.crossectional_area_nabl = 'pass'
                        break
                    else:
                        record.crossectional_area_nabl = 'fail'

    per_diff_dia = fields.Float(string="Percentage Diff in Diameter ",compute="_compute_per_diff_dia",store=True)

    per_diff_dia_visible = fields.Boolean("Percentage Diff in Diameter",compute="_compute_visible")

    requirement_per_diff_dia = fields.Char(string="Requirement")

    per_diff_dia_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string=" Conformity", compute="_compute_per_diff_dia_conformity", store=True)


    @api.depends('per_diff_dia','eln_ref','grade')
    def _compute_per_diff_dia_conformity(self):
        
        for record in self:
            record. per_diff_dia_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','632547l-a3df-4990-93d1-9904984644au4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','632547l-a3df-4990-93d1-9904984644au4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record. per_diff_dia - record. per_diff_dia*mu_value
                    upper = record. per_diff_dia + record. per_diff_dia*mu_value
                    if lower >= req_min and upper <= req_max:
                        record. per_diff_dia_conformity = 'pass'
                        break
                    else:
                        record. per_diff_dia_conformity = 'fail'

    per_diff_dia_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string=" NABL", compute="_compute_per_diff_dia_nabl", store=True)

    @api.depends('per_diff_dia','eln_ref','grade')
    def _compute_per_diff_dia_nabl(self):
        
        for record in self:
            record.per_diff_dia_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','632547l-a3df-4990-93d1-9904984644au4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','632547l-a3df-4990-93d1-9904984644au4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.per_diff_dia - record.per_diff_dia*mu_value
                    upper = record.per_diff_dia + record.per_diff_dia*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.per_diff_dia_nabl = 'pass'
                        break
                    else:
                        record.per_diff_dia_nabl = 'fail'

    weight = fields.Float(string="Weight, gm",digits=(10, 3))
    lenght = fields.Float(string="Length, mm",digits=(10, 3))
   
    weight_per_meter = fields.Float(string="Weight per Meter, g/m",compute="_compute_weight_per_meter",store=True,digits=(12,3))

    weight_per_meter_visible = fields.Boolean("Weight per Meter, g/m",compute="_compute_visible")

    requirement_weight_per_meter = fields.Char(string="Requirement")

    weight_per_meter_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string=" Conformity", compute="_compute_weight_per_meter_conformity", store=True)


    @api.depends('weight_per_meter','eln_ref','grade')
    def _compute_weight_per_meter_conformity(self):
        
        for record in self:
            record. weight_per_meter_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6897ert-a3df-4978-93d1-990498464785yt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6897ert-a3df-4978-93d1-990498464785yt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record. weight_per_meter - record. weight_per_meter*mu_value
                    upper = record. weight_per_meter + record. weight_per_meter*mu_value
                    if lower >= req_min and upper <= req_max:
                        record. weight_per_meter_conformity = 'pass'
                        break
                    else:
                        record. weight_per_meter_conformity = 'fail'

    weight_per_meter_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string=" NABL", compute="_compute_weight_per_meter_nabl", store=True)

    @api.depends('weight_per_meter','eln_ref','grade')
    def _compute_weight_per_meter_nabl(self):
        
        for record in self:
            record.weight_per_meter_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6897ert-a3df-4978-93d1-990498464785yt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6897ert-a3df-4978-93d1-990498464785yt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.weight_per_meter - record.weight_per_meter*mu_value
                    upper = record.weight_per_meter + record.weight_per_meter*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.weight_per_meter_nabl = 'pass'
                        break
                    else:
                        record.weight_per_meter_nabl = 'fail'
    
    
    lay_length = fields.Float(string="Lay Length mm")

    lay_length_visible = fields.Boolean("Lay Length mm",compute="_compute_visible")

    requirement_lay_length = fields.Char(string="Requirement")

    lay_length_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string=" Conformity", compute="_compute_lay_length_conformity", store=True)


    @api.depends('lay_length','eln_ref','grade')
    def _compute_lay_length_conformity(self):
        
        for record in self:
            record. lay_length_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','984fgtrvv-a3df-4978-93d1-990498464785yt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','984fgtrvv-a3df-4978-93d1-990498464785yt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record. lay_length - record. lay_length*mu_value
                    upper = record. lay_length + record. lay_length*mu_value
                    if lower >= req_min and upper <= req_max:
                        record. lay_length_conformity = 'pass'
                        break
                    else:
                        record. lay_length_conformity = 'fail'

    lay_length_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string=" NABL", compute="_compute_lay_length_nabl", store=True)

    @api.depends('lay_length','eln_ref','grade')
    def _compute_lay_length_nabl(self):
        
        for record in self:
            record.lay_length_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','984fgtrvv-a3df-4978-93d1-990498464785yt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','984fgtrvv-a3df-4978-93d1-990498464785yt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.lay_length - record.lay_length*mu_value
                    upper = record.lay_length + record.lay_length*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.lay_length_nabl = 'pass'
                        break
                    else:
                        record.lay_length_nabl = 'fail'


    gauge_length = fields.Float(string="Guage  Length mm",store=True)
    proof_stress2per = fields.Float(string="0.2 % Proof Load, (kN)",store=True)

    proof_stress2per_visible = fields.Boolean("0.2 % Proof Load, (kN)",compute="_compute_visible")

    requirement_proof_stress2per = fields.Char(string="Requirement")

    proof_stress2per_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string=" Conformity", compute="_compute_proof_stress2per_conformity", store=True)


    @api.depends('proof_stress2per','eln_ref','grade')
    def _compute_proof_stress2per_conformity(self):
        
        for record in self:
            record. proof_stress2per_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6325578-a3df-4990-93d1-9904984644a75')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6325578-a3df-4990-93d1-9904984644a75')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record. proof_stress2per - record. proof_stress2per*mu_value
                    upper = record. proof_stress2per + record. proof_stress2per*mu_value
                    if lower >= req_min and upper <= req_max:
                        record. proof_stress2per_conformity = 'pass'
                        break
                    else:
                        record. proof_stress2per_conformity = 'fail'

    proof_stress2per_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string=" NABL", compute="_compute_proof_stress2per_nabl", store=True)

    @api.depends('proof_stress2per','eln_ref','grade')
    def _compute_proof_stress2per_nabl(self):
        
        for record in self:
            record.proof_stress2per_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6325578-a3df-4990-93d1-9904984644a75')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6325578-a3df-4990-93d1-9904984644a75')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.proof_stress2per - record.proof_stress2per*mu_value
                    upper = record.proof_stress2per + record.proof_stress2per*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.proof_stress2per_nabl = 'pass'
                        break
                    else:
                        record.proof_stress2per_nabl = 'fail'

    breaking_load = fields.Float(string="Breaking Load,  (kN)")

    breaking_load_visible = fields.Boolean("Breaking Load,  (kN)",compute="_compute_visible")

    requirement_breaking_load = fields.Char(string="Requirement")

    breaking_load_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string=" Conformity", compute="_compute_breaking_load_conformity", store=True)


    @api.depends('breaking_load','eln_ref','grade')
    def _compute_breaking_load_conformity(self):
        
        for record in self:
            record. breaking_load_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6325487-a3df-4978-93d1-9904984644au4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6325487-a3df-4978-93d1-9904984644au4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record. breaking_load - record. breaking_load*mu_value
                    upper = record. breaking_load + record. breaking_load*mu_value
                    if lower >= req_min and upper <= req_max:
                        record. breaking_load_conformity = 'pass'
                        break
                    else:
                        record. breaking_load_conformity = 'fail'

    breaking_load_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string=" NABL", compute="_compute_breaking_load_nabl", store=True)

    @api.depends('breaking_load','eln_ref','grade')
    def _compute_breaking_load_nabl(self):
        
        for record in self:
            record.breaking_load_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6325487-a3df-4978-93d1-9904984644au4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6325487-a3df-4978-93d1-9904984644au4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.breaking_load - record.breaking_load*mu_value
                    upper = record.breaking_load + record.breaking_load*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.breaking_load_nabl = 'pass'
                        break
                    else:
                        record.breaking_load_nabl = 'fail'


    tensile_strength = fields.Float(string="Tensile Strength Mpa",compute="_compute_tensile_strength")

    tensile_strength_visible = fields.Boolean("Tensile Strength Mpa",compute="_compute_visible")

    requirement_tensile_strength = fields.Char(string="Requirement")

    tensile_strength_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string=" Conformity", compute="_compute_tensile_strength_conformity", store=True)


    @api.depends('tensile_strength','eln_ref','grade')
    def _compute_tensile_strength_conformity(self):
        
        for record in self:
            record. tensile_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','879542-a3df-4978-93d1-990498464785yt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','879542-a3df-4978-93d1-990498464785yt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record. tensile_strength - record. tensile_strength*mu_value
                    upper = record. tensile_strength + record. tensile_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record. tensile_strength_conformity = 'pass'
                        break
                    else:
                        record. tensile_strength_conformity = 'fail'

    tensile_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string=" NABL", compute="_compute_tensile_strength_nabl", store=True)

    @api.depends('tensile_strength','eln_ref','grade')
    def _compute_tensile_strength_nabl(self):
        
        for record in self:
            record.tensile_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','879542-a3df-4978-93d1-990498464785yt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','879542-a3df-4978-93d1-990498464785yt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.tensile_strength - record.tensile_strength*mu_value
                    upper = record.tensile_strength + record.tensile_strength*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.tensile_strength_nabl = 'pass'
                        break
                    else:
                        record.tensile_strength_nabl = 'fail'

    
    elongation = fields.Float(string="Elongation %",store=True)

    elongation_visible = fields.Boolean("Elongation",compute="_compute_visible")

    requirement_elongation = fields.Char(string="Requirement")

    elongation_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string=" Conformity", compute="_compute_elongation_conformity", store=True)


    @api.depends('elongation','eln_ref','grade')
    def _compute_elongation_conformity(self):
        
        for record in self:
            record. elongation_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36578ee-a3df-4978-93d1-990498464785yt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36578ee-a3df-4978-93d1-990498464785yt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record. elongation - record. elongation*mu_value
                    upper = record. elongation + record. elongation*mu_value
                    if lower >= req_min and upper <= req_max:
                        record. elongation_conformity = 'pass'
                        break
                    else:
                        record. elongation_conformity = 'fail'

    elongation_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string=" NABL", compute="_compute_elongation_nabl", store=True)

    @api.depends('elongation','eln_ref','grade')
    def _compute_elongation_nabl(self):
        
        for record in self:
            record.elongation_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36578ee-a3df-4978-93d1-990498464785yt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36578ee-a3df-4978-93d1-990498464785yt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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


    center_dia = fields.Float("Centre Diameter (mm) ",compute="_compute_max_dia")
    individual_dia = fields.Float(string="Individual Dia Average , mm",compute="_compute_individual_dia",store=True)
    individual_dia_seven = fields.Float(string="Individual Seven Dia Max in mm",compute="_compute_max_dia",store=True,digits=(10, 2))
    individual_dia_six = fields.Float(string="Individual Six Dia Max in mm",compute="_compute_max_dia")

    modulus_of_ela = fields.Float(string="Modulus of Elasticity (GPa) ")

    modulus_of_ela_visible = fields.Boolean("Modulus of Elasticity (GPa) ",compute="_compute_visible")

    requirement_modulus_of_ela = fields.Char(string="Requirement")

    modulus_of_ela_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string=" Conformity", compute="_compute_modulus_of_ela_conformity", store=True)


    @api.depends('modulus_of_ela','eln_ref','grade')
    def _compute_modulus_of_ela_conformity(self):
        
        for record in self:
            record. modulus_of_ela_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3147tyr4-a3df-4978-93d1-990498464785yt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3147tyr4-a3df-4978-93d1-990498464785yt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record. modulus_of_ela - record. modulus_of_ela*mu_value
                    upper = record. modulus_of_ela + record. modulus_of_ela*mu_value
                    if lower >= req_min and upper <= req_max:
                        record. modulus_of_ela_conformity = 'pass'
                        break
                    else:
                        record. modulus_of_ela_conformity = 'fail'

    modulus_of_ela_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string=" NABL", compute="_compute_modulus_of_ela_nabl", store=True)

    @api.depends('modulus_of_ela','eln_ref','grade')
    def _compute_modulus_of_ela_nabl(self):
        
        for record in self:
            record.modulus_of_ela_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3147tyr4-a3df-4978-93d1-990498464785yt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3147tyr4-a3df-4978-93d1-990498464785yt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.modulus_of_ela - record.modulus_of_ela*mu_value
                    upper = record.modulus_of_ela + record.modulus_of_ela*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.modulus_of_ela_nabl = 'pass'
                        break
                    else:
                        record.modulus_of_ela_nabl = 'fail'


    @api.depends('ht_strand_lines.individual_area')
    def _compute_crossectional_area(self):
        for rec in self:
            rec.crossectional_area = sum(line.individual_area for line in rec.ht_strand_lines)

    @api.depends('weight', 'lenght')
    def _compute_weight_per_meter(self):
        for rec in self:
            if rec.lenght:
                rec.weight_per_meter = (rec.weight / rec.lenght)*1000
            else:
                rec.weight_per_meter = 0.0

    @api.depends('breaking_load', 'crossectional_area')
    def _compute_tensile_strength(self):
        for rec in self:
            if rec.crossectional_area:  
                rec.tensile_strength = (rec.breaking_load / rec.crossectional_area) * 1000
            else:
                rec.tensile_strength = 0.0

    @api.depends('ht_strand_lines.individual_dia1')
    def _compute_max_dia(self):
        for rec in self:
            if rec.ht_strand_lines:
                values = rec.ht_strand_lines.mapped('individual_dia1')

                # All values max → Seven
                max_val = max(values) if values else 0.0
                rec.center_dia = max_val
                rec.individual_dia_seven = max_val

                # First 6 values max → Six
                first_six = values[:6] if values else []
                rec.individual_dia_six = max(first_six) if first_six else 0.0
            else:
                rec.center_dia = 0.0
                rec.individual_dia_seven = 0.0
                rec.individual_dia_six = 0.0

    @api.depends('ht_strand_lines.individual_dia1')
    def _compute_individual_dia(self):
        for rec in self:
            values = rec.ht_strand_lines.mapped('individual_dia1')
            rec.individual_dia = (sum(values) / len(values)) if values else 0.0

    @api.depends('individual_dia_seven', 'individual_dia_six')
    def _compute_per_diff_dia(self):
        for rec in self:
            if rec.individual_dia_six: 
                rec.per_diff_dia = ((rec.individual_dia_seven - rec.individual_dia_six) / rec.individual_dia_six) * 100
            else:
                rec.per_diff_dia = 0.0


    ht_strand_lines = fields.One2many('mechanical.ht.strand.line','parent_id',string="Parameter")

   
    
    

    
     
      ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.crossectional_area_visible = False
            record.per_diff_dia_visible = False
            record.proof_stress2per_visible = False
            record.breaking_load_visible = False
            record.tensile_strength_visible = False
            record.elongation_visible = False
            record.weight_per_meter_visible = False
            record.lay_length_visible = False
            record.modulus_of_ela_visible = False

            

            
            
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
                if sample.internal_id == "65895-a3df-4990-93d1-9904984644aoo2":
                    record.crossectional_area_visible = True
                if sample.internal_id == "632547l-a3df-4990-93d1-9904984644au4":
                    record.per_diff_dia_visible = True
                if sample.internal_id == "6325578-a3df-4990-93d1-9904984644a75":
                    record.proof_stress2per_visible = True

                if sample.internal_id == "6325487-a3df-4978-93d1-9904984644au4":
                    record.breaking_load_visible = True

                if sample.internal_id == "879542-a3df-4978-93d1-990498464785yt":
                    record.tensile_strength_visible = True
                if sample.internal_id == "36578ee-a3df-4978-93d1-990498464785yt":
                    record.elongation_visible = True

                if sample.internal_id == "6897ert-a3df-4978-93d1-990498464785yt":
                    record.weight_per_meter_visible = True

                if sample.internal_id == "984fgtrvv-a3df-4978-93d1-990498464785yt":
                    record.lay_length_visible = True

                if sample.internal_id == "3147tyr4-a3df-4978-93d1-990498464785yt":
                    record.modulus_of_ela_visible = True

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()
            
            if result.parameter.internal_id == '65895-a3df-4990-93d1-9904984644aoo2':
                result.result_char = round(self.crossectional_area,2)
                result.calculated = True
                if self.crossectional_area_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '632547l-a3df-4990-93d1-9904984644au4':
                result.result_char = round(self.per_diff_dia,2)
                result.calculated = True
                if self.per_diff_dia_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '6325578-a3df-4990-93d1-9904984644a75':
                result.result_char = round(self.proof_stress2per,2)
                result.calculated = True
                if self.proof_stress2per_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '6325487-a3df-4978-93d1-9904984644au4':
                result.result_char = round(self.breaking_load,2)
                result.calculated = True
                if self.breaking_load_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '879542-a3df-4978-93d1-990498464785yt':
                result.result_char = round(self.tensile_strength,2)
                result.calculated = True
                if self.tensile_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '36578ee-a3df-4978-93d1-990498464785yt':
                result.result_char = round(self.elongation,2)
                result.calculated = True
                if self.elongation_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '6897ert-a3df-4978-93d1-990498464785yt':
                result.result_char = round(self.weight_per_meter,2)
                result.calculated = True
                if self.weight_per_meter_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '984fgtrvv-a3df-4978-93d1-990498464785yt':
                result.result_char = round(self.lay_length,2)
                result.calculated = True
                if self.lay_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '3147tyr4-a3df-4978-93d1-990498464785yt':
                result.result_char = round(self.modulus_of_ela,2)
                result.calculated = True
                if self.modulus_of_ela_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '333b8761-c035-44ff-a610-31b3fb5337d0':
                # result.result_char = round(self.modulus_of_ela,2)
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
        record = super(HtStrand, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        # records = self.env['lerm.eln'].sudo().search([('id','=', record.eln_id.id)]).parameters_result
        # print("records",records)
        # self.sample_parameters = records
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)



    def get_all_fields(self):
        record = self.env['ht.strand'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



class HtStrandLine(models.Model):
    _name = "mechanical.ht.strand.line"
    parent_id = fields.Many2one('ht.strand',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    individual_dia1 = fields.Float(string="Individual Dia")
    individual_area = fields.Float(string="Individual Area ",compute="_compute_individual_area")

    @api.depends('individual_dia1')
    def _compute_individual_area(self):
        for rec in self:
            if rec.individual_dia1:
                rec.individual_area = 3.1416 * rec.individual_dia1 * rec.individual_dia1 / 4
            else:
                rec.individual_area = 0.0
   


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(HtStrandLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in chequered_tiles_cement_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class htstrandNotes(models.Model):
    _name = "htstrand.notes"

    parent_id = fields.Many2one('ht.strand',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")




