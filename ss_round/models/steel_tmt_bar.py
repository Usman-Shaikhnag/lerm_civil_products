from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re
from decimal import Decimal, ROUND_HALF_UP



class StructuralSteelRound(models.Model):
    _name = "structural.steel.round"
    _inherit = "lerm.eln"
    _rec_name = "name"
   
    
   
   
    grade = fields.Many2one('lerm.grade.line', string="Grade", compute="_compute_grade_id", store=True)
    name = fields.Char("Name",default="Structural Steel Round")
    size = fields.Many2one('lerm.size.line', string="Size", compute="_compute_size_id", store=True)
    dia1 = fields.Float(string="Dia mm")
    area1 = fields.Float(string="AREA mm²", compute="_compute_area", store=True)
    gauge_length1 = fields.Integer(string="Gauge Length mm", compute="_compute_gauge_length", store=True)
    final_length1 = fields.Float(string="FINAL LENGTH mm")
    yeild_load1 = fields.Float(string="0.2% proof Load / Yield Load, KN")
    ultimate_load1 = fields.Float(string="Ultimate Load, KN")
    proof_yeid_stress1 = fields.Float(string="0.2% Proof Stress / Yield Stress N/mm2", compute="_compute_proof_yield_stress", store=True,digits=(12,2))
    ult_tens_strgth1 = fields.Float(string="Ultimate Tensile Strength, N/mm2", compute="_compute_ultimate_tensile_strength", store=True,digits=(12,2))
    elongation1 = fields.Float(string="% Elongation", compute="_compute_elongation", store=True,digits=(12,2))

    @api.depends('dia1')
    def _compute_area(self):
        for record in self:
            record.area1 = (record.dia1 * record.dia1 * 3.1416) / 4

    # @api.depends('area1')
    # def _compute_gauge_length(self):
    #     for record in self:
    #         record.gauge_length1 = 5.65 * (record.area1 ** 0.5)

    @api.depends('area1')
    def _compute_gauge_length(self):
        for record in self:
            gauge_length1 = math.sqrt(record.area1) * 5.65
            # Check if the decimal part is greater than or equal to 0.5
            if gauge_length1 - int(gauge_length1) >= 0.5:
                rounded_gauge_length1 = math.ceil(gauge_length1)
            else:
                rounded_gauge_length1 = math.floor(gauge_length1)
            record.gauge_length1 = int(rounded_gauge_length1)

   
    @api.depends('yeild_load1', 'area1')
    def _compute_proof_yield_stress(self):
        for record in self:
            if record.area1 != 0:
                proof_yield_stress_decimal1 = (Decimal(record.yeild_load1) / Decimal(record.area1)) * 1000
                record.proof_yeid_stress1 = proof_yield_stress_decimal1.quantize(Decimal('0.01'))
            else:
                record.proof_yeid_stress1 = 0.0


    # @api.depends('ultimate_load1', 'area1')
    # def _compute_ultimate_tensile_strength(self):
    #     for record in self:
    #         if record.area1 != 0:
    #             record.ult_tens_strgth1 = (record.ultimate_load1 / record.area1) * 1000
    @api.depends('ultimate_load1', 'area1')
    def _compute_ultimate_tensile_strength(self):
        for record in self:
            if record.area1 != 0:
                ult_tensile_strength_decimal = Decimal(record.ultimate_load1 / record.area1 * 1000)
                record.ult_tens_strgth1 = ult_tensile_strength_decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                record.ult_tens_strgth1 = 0.0

   
                
    @api.depends('final_length1', 'gauge_length1')
    def _compute_elongation(self):
        for record in self:
            if record.gauge_length1 != 0:
                elongation_decimal1 = ((Decimal(record.final_length1) - Decimal(record.gauge_length1)) / Decimal(record.gauge_length1)) * 100
                record.elongation1 = elongation_decimal1.quantize(Decimal('0.01'))
            else:
                record.elongation1 = 0.0
   
    fracture1 = fields.Char("Fracture",default="W.G.L")
    bend_test = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non-satisfactory', 'Non-Satisfactory')],"Bend Test",store=True)
    
    re_bend_test = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non-satisfactory', 'Non-Satisfactory')],"Re-Bend Test",store=True)
    
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.fracture_visible = False
            record.bend_visible  = False  
            record.rebend_visible = False
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '62ffe6d0-ca87-41f6-9e18-47169dc04398':
                    record.fracture_visible = True
                if sample.internal_id == '43b89870-ec82-488f-866f-4a5a953073aa':
                    record.bend_visible = True
                if sample.internal_id == 'f781bfd8-550b-45f4-81ac-43f856d147b8':
                    record.rebend_visible = True

    fracture_visible = fields.Boolean("Fracture",compute="_compute_visible")
    bend_visible = fields.Boolean("Bend Test",compute="_compute_visible")
    rebend_visible = fields.Boolean("Rebend Test",compute="_compute_visible")

    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.fracture_visible = False
            record.bend_visible  = False  
            record.rebend_visible = False
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '62ffe6d0-ca87-41f6-9e18-47169dc04398':
                    record.fracture_visible = True
                if sample.internal_id == '43b89870-ec82-488f-866f-4a5a953073aa':
                    record.bend_visible = True
                if sample.internal_id == 'f781bfd8-550b-45f4-81ac-43f856d147b8':
                    record.rebend_visible = True


    dia2 = fields.Float(string="Dia mm")
    area2 = fields.Float(string="AREA mm²",compute="_compute_area2", store=True)
    gauge_length2 = fields.Integer(string="Gauge Length mm",compute="_compute_gauge_length2", store=True)
    final_length2 = fields.Float(string="FINAL LENGTH mm")
    yeild_load2 = fields.Float(string="0.2% proof Load / Yield Load, KN")
    ultimate_load2 = fields.Float(string="Ultimate Load, KN")
    proof_yeid_stress2 = fields.Float(string="0.2% Proof Stress / Yield Stress N/mm2",compute="_compute_proof_yield_stress2", store=True,digits=(12,2))
    ult_tens_strgth2 = fields.Float(string="Ultimate Tensile Strength, N/mm2",compute="_compute_ultimate_tensile_strength2", store=True,digits=(12,2))
    elongation2 = fields.Float(string="% Elongation",compute="_compute_elongation2", store=True,digits=(12,2))

    @api.depends('dia2')
    def _compute_area2(self):
        for record in self:
            record.area2 = ((record.dia2 * record.dia2 * 3.1416) / 4)

    # @api.depends('area2')
    # def _compute_gauge_length2(self):
    #     for record in self:
    #         record.gauge_length2 = 5.65 * (record.area2 ** 0.5)
    @api.depends('area2')
    def _compute_gauge_length2(self):
        for record in self:
            gauge_length2 = math.sqrt(record.area2) * 5.65
            # Check if the decimal part is greater than or equal to 0.5
            if gauge_length2 - int(gauge_length2) >= 0.5:
                rounded_gauge_length2 = math.ceil(gauge_length2)
            else:
                rounded_gauge_length2 = math.floor(gauge_length2)
            record.gauge_length2 = int(rounded_gauge_length2)

    # @api.depends('yeild_load2', 'area2')
    # def _compute_proof_yield_stress2(self):
    #     for record in self:
    #         if record.area2 != 0:
    #             proof_yield_stress_decimal = (Decimal(record.yeild_load2) / Decimal(record.area2)) * 1000
    #             record.proof_yeid_stress2 = proof_yield_stress_decimal.quantize(Decimal('0.0'), rounding=ROUND_HALF_UP)
            
    @api.depends('yeild_load2', 'area2')
    def _compute_proof_yield_stress2(self):
        for record in self:
            if record.area2 != 0:
                proof_yield_stress_decimal = (Decimal(record.yeild_load2) / Decimal(record.area2)) * 1000
                record.proof_yeid_stress2 = proof_yield_stress_decimal.quantize(Decimal('0.01'))
            else:
                record.proof_yeid_stress2 = 0.0

    @api.depends('ultimate_load2', 'area2')
    def _compute_ultimate_tensile_strength2(self):
        for record in self:
            if record.area2 != 0:
                record.ult_tens_strgth2 = (record.ultimate_load2 / record.area2) * 1000

    # @api.depends('final_length2', 'gauge_length2')
    # def _compute_elongation2(self):
    #     for record in self:
    #         if record.gauge_length2 != 0:
    #             elongation_decimal = ((Decimal(record.final_length2) - Decimal(record.gauge_length2)) / Decimal(record.gauge_length2)) * 100
    #             record.elongation2 = elongation_decimal.quantize(Decimal('0.0'), rounding=ROUND_HALF_UP)
                
    @api.depends('final_length2', 'gauge_length2')
    def _compute_elongation2(self):
        for record in self:
            if record.gauge_length2 != 0:
                elongation_decimal = ((Decimal(record.final_length2) - Decimal(record.gauge_length2)) / Decimal(record.gauge_length2)) * 100
                record.elongation2 = elongation_decimal.quantize(Decimal('0.01'))
            else:
                record.elongation2 = 0.0
    

   
    fracture2 = fields.Char("Fracture",default="W.G.L")

    bend_test2 = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non-satisfactory', 'Non-Satisfactory')],"Bend Test",store=True)
    
    re_bend_test2 = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non-satisfactory', 'Non-Satisfactory')],"Re-Bend Test",store=True)


    eln_ref = fields.Many2one('lerm.eln',string="ELN")
   
    requirement_utl1 = fields.Float(string="Requirement",compute="_compute_requirement_utl1",store=True)
    requirement_yield1 = fields.Float(string="Requirement",compute="_compute_requirement_yield1",store=True)
   
    requirement_elongation1 = fields.Float(string="Requirement",compute="_compute_requirement_elongation1",store=True)
   
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
  
    # fracture_visible = fields.Boolean("Fracture visible",compute="_compute_visible",store=True)
    # bend_visible = fields.Boolean("Bend visible",compute="_compute_visible",store=True)
    # rebend_visible = fields.Boolean("Rebend visible",compute="_compute_visible",store=True)


    
  

   
   
    @api.depends('eln_ref','grade')
    def _compute_requirement_utl1(self):
        for record in self:
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bd4a58b3-d439-4d80-aadb-0a33f1d3bec2')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    record.requirement_utl1 = req_min
                    break
                else:
                    record.requirement_utl1 = 0

    @api.depends('eln_ref','grade')
    def _compute_requirement_yield1(self):
        for record in self:
            # record.requirement_yield = 0
            # line = self.env['eln.parameters.result'].sudo().search([('eln_id','=',record.eln_ref.id),('parameter.parameter_name','=','Yield Stress (TMT)')]).parameter
            # materials = self.env['lerm.parameter.master'].sudo().search([('id','=',line.id)]).parameter_table
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','afa815b6-a7ce-4272-b062-ca6b2fe55b01')]).parameter_table
            
            for material in materials:
                print("DATA ", material)
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    record.requirement_yield1 = req_min
                    break
                else:
                    record.requirement_yield1 = 0

    @api.depends('eln_ref','grade')
    def _compute_requirement_elongation1(self):
        for record in self:
            # record.requirement_elongation = 0
            # line = self.env['eln.parameters.result'].sudo().search([('eln_id','=',record.eln_ref.id),('parameter.parameter_name','=','% Elongation (TMT)')]).parameter
            # materials = self.env['lerm.parameter.master'].sudo().search([('id','=',line.id)]).parameter_table
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','70fecea5-c9de-4ede-a7f9-fd2a8ad9697d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    record.requirement_elongation1 = req_min
                    break
                else:
                    record.requirement_elongation1 = 0

        
                    



    

   

   



    proof_yeid_stress1_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_proof_yeid_stress1_confirmity")

  
    @api.depends('proof_yeid_stress1','eln_ref')
    def _compute_proof_yeid_stress1_confirmity(self):
        for record in self:
            record.proof_yeid_stress1_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','afa815b6-a7ce-4272-b062-ca6b2fe55b01')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','afa815b6-a7ce-4272-b062-ca6b2fe55b01')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.proof_yeid_stress1 - record.proof_yeid_stress1*mu_value
                    upper = record.proof_yeid_stress1 + record.proof_yeid_stress1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.proof_yeid_stress1_confirmity = 'pass'
                        break
                    else:
                        record.proof_yeid_stress1_confirmity = 'fail'


    proof_yeid_stress1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')],string="NABL",compute="_compute_proof_yeid_stress1_nabl",store=True)



    @api.depends('proof_yeid_stress1','eln_ref')
    def _compute_proof_yeid_stress1_nabl(self):
        
        for record in self:
            record.proof_yeid_stress1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','afa815b6-a7ce-4272-b062-ca6b2fe55b01')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','afa815b6-a7ce-4272-b062-ca6b2fe55b01')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.proof_yeid_stress1 - record.proof_yeid_stress1*mu_value
                    upper = record.proof_yeid_stress1 + record.proof_yeid_stress1*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.proof_yeid_stress1_nabl = 'pass'
                        break
                    else:
                        record.proof_yeid_stress1_nabl = 'fail'


    ult_tens_strgth1_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_ult_tens_strgth1_confirmity")

  
    @api.depends('ult_tens_strgth1','eln_ref')
    def _compute_ult_tens_strgth1_confirmity(self):
        for record in self:
            record.ult_tens_strgth1_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bd4a58b3-d439-4d80-aadb-0a33f1d3bec2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bd4a58b3-d439-4d80-aadb-0a33f1d3bec2')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.ult_tens_strgth1 - record.ult_tens_strgth1*mu_value
                    upper = record.ult_tens_strgth1 + record.ult_tens_strgth1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.ult_tens_strgth1_confirmity = 'pass'
                        break
                    else:
                        record.ult_tens_strgth1_confirmity = 'fail'


    ult_tens_strgth1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')],string="NABL",compute="_compute_ult_tens_strgth1_nabl",store=True)



    @api.depends('ult_tens_strgth1','eln_ref')
    def _compute_ult_tens_strgth1_nabl(self):
        
        for record in self:
            record.ult_tens_strgth1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bd4a58b3-d439-4d80-aadb-0a33f1d3bec2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bd4a58b3-d439-4d80-aadb-0a33f1d3bec2')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.ult_tens_strgth1 - record.ult_tens_strgth1*mu_value
                    upper = record.ult_tens_strgth1 + record.ult_tens_strgth1*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.ult_tens_strgth1_nabl = 'pass'
                        break
                    else:
                        record.ult_tens_strgth1_nabl = 'fail'



    elongation1_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail',compute="_compute_elongation1_confirmity")

  
    @api.depends('elongation1','eln_ref')
    def _compute_elongation1_confirmity(self):
        for record in self:
            record.elongation1_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','70fecea5-c9de-4ede-a7f9-fd2a8ad9697d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','70fecea5-c9de-4ede-a7f9-fd2a8ad9697d')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.elongation1 - record.elongation1*mu_value
                    upper = record.elongation1 + record.elongation1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.elongation1_confirmity = 'pass'
                        break
                    else:
                        record.elongation1_confirmity = 'fail'


    elongation1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')],string="NABL",compute="_compute_elongation1_nabl",store=True)



    @api.depends('elongation1','eln_ref')
    def _compute_elongation1_nabl(self):
        
        for record in self:
            record.elongation1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','70fecea5-c9de-4ede-a7f9-fd2a8ad9697d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','70fecea5-c9de-4ede-a7f9-fd2a8ad9697d')]).parameter_table
            for material in materials:
                # if material.grade.id == record.grade.id:
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
        
        



    def open_eln_page(self):
        # import wdb; wdb.set_trace()

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
        record = super(StructuralSteelRound, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
    

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size = self.eln_ref.size_id.id




    

    



    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)
            



# class MechanicalTmtTest(models.Model):
#     _name = "mechanical.tmt.test"
#     _rec_name = "name"
#     name = fields.Char("Name")