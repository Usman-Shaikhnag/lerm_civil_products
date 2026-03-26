from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re



class SteelTmtBarLine(models.Model):
    _name = "steel.tmt.bar"
    _inherit = "lerm.eln"
    _rec_name = "name"
   
    
    Id_no = fields.Char("ID No")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    name = fields.Char("Name",default="STEEL TMT BAR")
    size = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    diameter = fields.Integer(string="Dia. in mm",compute="_compute_dia")
    lentgh = fields.Float(string="Length in meter",digits=(10, 3))
    weight = fields.Float(string="Weight, in kg",digits=(10, 3))
    weight_per_meter = fields.Float(string="Weight per meter, kg/m",compute="_compute_weight_per_meter",store=True)
    crossectional_area = fields.Float(string="Cross sectional Area, mm²",compute="_compute_crossectional_area")
    gauge_length = fields.Integer(string="Gauge Length mm",compute="_compute_gauge_length",store=True)
    elongated_gauge_length = fields.Float(string="Elongated Gauge Length, mm")
    percent_elongation = fields.Float(string="% Elongation",compute="_compute_elongation_percent",store=True)
    yeild_load = fields.Float(string="Yield Load  KN")
    ultimate_load = fields.Float(string="Ultimate Load, Kn")
    proof_yeid_stress = fields.Float(string="0.2% Proof Stress / Yield Stress N/mm2",compute="_compute_proof_yeid_stress",store=True)
    ult_tens_strgth = fields.Float(string="Ultimate Tensile Strength, N/mm2",compute="_compute_ult_tens_strgth",store=True)
    fracture = fields.Char("Fracture (Within Gauge Length)",default="W.G.L")
    eln_ref = fields.Many2one('lerm.eln',string="ELN")
    ts_ys_ratio = fields.Float(string="TS/YS Ratio",compute="_compute_ts_ys_ratio",store=True)
    weight_per_meter = fields.Float(string="Weight per meter",compute="_compute_weight_per_meter",store=True,digits=(10, 3))
    variation = fields.Float(string="Variation")

    requirement_utl = fields.Float(string="Requirement",compute="_compute_requirement_utl",store=True)
    requirement_yield = fields.Float(string="Requirement",compute="_compute_requirement_yield",store=True)
    requirement_ts_ys = fields.Float(string="Requirement",compute="_compute_requirement_ts_ys",store=True)
    requirement_elongation = fields.Float(string="Requirement",compute="_compute_requirement_elongation",store=True)
    requirement_weight_per_meter = fields.Float(string="Requirement",compute="_compute_requirement_weight_per_meter",digits=(16, 4),store=True)

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    tests = fields.Many2many("mechanical.tmt.test",string="Tests")
    # fracture_visible = fields.Boolean("Fracture visible",compute="_compute_visible",store=True)
    # bend_visible = fields.Boolean("Bend visible",compute="_compute_visible",store=True)
    # rebend_visible = fields.Boolean("Rebend visible",compute="_compute_visible",store=True)
    # bend_test_text = fields.Char(string="Bend Test Text", compute="_compute_bend_test_text", store=True)


    
    # bend_test = fields.Selection([
    #     ('satisfactory', 'Satisfactory'),
    #     ('non-satisfactory', 'Non-Satisfactory')],"Bend Test",store=True)
    
    # re_bend_test = fields.Selection([
    #     ('satisfactory', 'Satisfactory'),
    #     ('non-satisfactory', 'Non-Satisfactory')],"Re-Bend Test",store=True)
    bend_test1 = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non-satisfactory', 'Non-Satisfactory')],"Bend Test",store=True)
    
    re_bend_test1 = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non-satisfactory', 'Non-Satisfactory')],"Re-Bend Test",store=True)
    
      

    # @api.depends('bend_test')
    # def _compute_bend_test_text(self):
    #     for record in self:
    #         if record.bend_test == '1':
    #             record.bend_test_text = 'Satisfactory'
    #         elif record.bend_test == '2':
    #             record.bend_test_text = 'Non-Satisfactory'
    #         else:
    #             record.bend_test_text = 'Undefined'
    


    uts_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="Conformity",compute="_compute_uts_conformity",store=True)

    yield_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="Conformity",compute="_compute_yield_conformity",store=True)

    elongation_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="Conformity",compute="_compute_elongation_conformity",store=True)

    ts_ys_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="Conformity",compute="_compute_ts_ys_conformity",store=True)

    weight_per_meter_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="Conformity",compute="_compute_weight_per_meter_conformity",store=True)

    fracture_visible = fields.Boolean("Fracture",compute="_compute_visible")
    bend_visible = fields.Boolean("Bend Test",compute="_compute_visible")
    rebend_visible = fields.Boolean("Rebend Test",compute="_compute_visible")

    uts_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_uts_nabl",store=True)

    yield_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_yield_nabl",store=True)

    elongation_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_elongation_nabl",store=True)

    ts_ys_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_ts_ys_nabl",store=True)
    
    

    weight_per_meter_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_weight_per_meter_nabl",store=True)

    

    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.fracture_visible = False
            record.bend_visible  = False  
            record.rebend_visible = False
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '9156ec17-ae78-4f98-987f-af5d39e407f2':
                    record.fracture_visible = True
                if sample.internal_id == 'addd0c61-adb6-447d-b668-1fba0744680f':
                    record.bend_visible = True
                if sample.internal_id == 'f781bfd8-550b-45f4-81ac-43f856d147b8':
                    record.rebend_visible = True

    fracture_visible = fields.Boolean("Fracture",compute="_compute_visible")
    bend_visible = fields.Boolean("Bend Test",compute="_compute_visible")
    rebend_visible = fields.Boolean("Rebend Test",compute="_compute_visible")
    
    uts_visible = fields.Boolean("Ultimate Tensile Strength",compute="_compute_visible")
    elongation_visible = fields.Boolean("Elongation",compute="_compute_visible")
    weight_per_meter_visible = fields.Boolean("Weight Per Meter",compute="_compute_visible")
    yield_visible = fields.Boolean("Yield",compute="_compute_visible")
    ts_ys_visible = fields.Boolean("TS/YS",compute="_compute_visible")


    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.fracture_visible = False
            record.bend_visible  = False  
            record.rebend_visible = False

            record.uts_visible = False
            record.elongation_visible  = False  
            record.weight_per_meter_visible = False
            record.yield_visible  = False  
            record.ts_ys_visible = False
            
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '9156ec17-ae78-4f98-987f-af5d39e407f2':
                    record.fracture_visible = True
                if sample.internal_id == 'addd0c61-adb6-447d-b668-1fba0744680f':
                    record.bend_visible = True
                if sample.internal_id == 'f781bfd8-550b-45f4-81ac-43f856d147b8':
                    record.rebend_visible = True

                if sample.internal_id == '7da4cce7-4027-4d73-955e-ca7f7a2a2228':
                    record.uts_visible = True
                if sample.internal_id == 'b4ae8d8f-9cbd-4bf5-abe4-c0bf0379b725':
                    record.elongation_visible = True
                if sample.internal_id == '15558232-8a13-472c-b10d-1fc011e63aeb':
                    record.weight_per_meter_visible = True
                if sample.internal_id == 'c732ed77-4c06-4cd4-ae85-b7424c1a24c7':
                    record.yield_visible = True
                if sample.internal_id == 'de4bb55e-9318-4725-ac44-fd1850d9e2eb':
                    record.ts_ys_visible = True


    @api.depends('weight','lentgh')
    def _compute_weight_per_meter(self):
        for record in self:
            if record.lentgh != 0:   
                record.weight_per_meter =  record.weight/record.lentgh
            else:
                record.weight_per_meter = 0

    @api.depends('weight_per_meter','eln_ref','size')
    def _compute_weight_per_meter_nabl(self):
      

        for record in self:
            record.weight_per_meter_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15558232-8a13-472c-b10d-1fc011e63aeb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15558232-8a13-472c-b10d-1fc011e63aeb')]).parameter_table
            # for material in materials:
            #     if material.size.id == record.size.id:
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

    @api.depends('weight_per_meter','eln_ref','size')
    def _compute_weight_per_meter_conformity(self):
        for record in self:
            record.weight_per_meter_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15558232-8a13-472c-b10d-1fc011e63aeb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15558232-8a13-472c-b10d-1fc011e63aeb')]).parameter_table
            for material in materials:
                if material.size.id == record.size.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.weight_per_meter - record.weight_per_meter*mu_value
                    upper = record.weight_per_meter + record.weight_per_meter*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.weight_per_meter_conformity = 'pass'
                        break
                    else:
                        record.weight_per_meter_conformity = 'fail'

    @api.depends('eln_ref','size')
    def _compute_requirement_weight_per_meter(self):
        for record in self:
            # record.requirement_yield = 0
            # line = self.env['eln.parameters.result'].sudo().search([('eln_id','=',record.eln_ref.id),('parameter.parameter_name','=','Yield Stress (TMT)')]).parameter
            # materials = self.env['lerm.parameter.master'].sudo().search([('id','=',line.id)]).parameter_table
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','15558232-8a13-472c-b10d-1fc011e63aeb')]).parameter_table
            for material in materials:
                if material.size.id == record.size.id:
                    req_min = material.req_min
                    record.requirement_weight_per_meter = req_min
                    break
                else:
                    record.requirement_weight_per_meter = 0

    @api.depends('ult_tens_strgth','proof_yeid_stress')
    def _compute_ts_ys_ratio(self):
        for record in self:
            if record.proof_yeid_stress != 0:
                record.ts_ys_ratio = record.ult_tens_strgth / record.proof_yeid_stress
            else:
                record.ts_ys_ratio = 0


    @api.depends('ult_tens_strgth','eln_ref','grade')
    def _compute_uts_conformity(self):
        
        for record in self:
            record.uts_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7da4cce7-4027-4d73-955e-ca7f7a2a2228')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7da4cce7-4027-4d73-955e-ca7f7a2a2228')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.ult_tens_strgth - record.ult_tens_strgth*mu_value
                    upper = record.ult_tens_strgth + record.ult_tens_strgth*mu_value
           
                    if lower >= req_min and upper <= req_max:
                        record.uts_conformity = 'pass'
                        break
                    else:
                        record.uts_conformity = 'fail'

    @api.depends('ult_tens_strgth','eln_ref','grade')
    def _compute_uts_nabl(self):
        
        for record in self:
            # import wdb; wdb.set_trace()

            record.uts_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7da4cce7-4027-4d73-955e-ca7f7a2a2228')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7da4cce7-4027-4d73-955e-ca7f7a2a2228')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.ult_tens_strgth - record.ult_tens_strgth*mu_value
            upper = record.ult_tens_strgth + record.ult_tens_strgth*mu_value
            
            if lower >= lab_min and upper <= lab_max:
                record.uts_nabl = 'pass'
                break
            else:
                record.uts_nabl = 'fail'

    @api.depends('eln_ref','grade')
    def _compute_requirement_utl(self):
        for record in self:
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7da4cce7-4027-4d73-955e-ca7f7a2a2228')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    record.requirement_utl = req_min
                    break
                else:
                    record.requirement_utl = 0
                    


    @api.depends('percent_elongation','eln_ref','grade')
    def _compute_elongation_conformity(self):
       
        for record in self:
            record.elongation_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b4ae8d8f-9cbd-4bf5-abe4-c0bf0379b725')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b4ae8d8f-9cbd-4bf5-abe4-c0bf0379b725')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.percent_elongation - record.percent_elongation*mu_value
                    upper = record.percent_elongation + record.percent_elongation*mu_value
                    

                    if lower >= req_min and upper <= req_max:
                        record.elongation_conformity = 'pass'
                        break
                    else:
                        record.elongation_conformity = 'fail'

    @api.depends('percent_elongation','eln_ref','grade')
    def _compute_elongation_nabl(self):
       
        for record in self:
            record.elongation_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b4ae8d8f-9cbd-4bf5-abe4-c0bf0379b725')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b4ae8d8f-9cbd-4bf5-abe4-c0bf0379b725')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.percent_elongation - record.percent_elongation*mu_value
            upper = record.percent_elongation + record.percent_elongation*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.elongation_nabl = 'pass'
                break
            else:
                record.elongation_nabl = 'fail'

    @api.depends('eln_ref','grade')
    def _compute_requirement_elongation(self):
        for record in self:
            # record.requirement_elongation = 0
            # line = self.env['eln.parameters.result'].sudo().search([('eln_id','=',record.eln_ref.id),('parameter.parameter_name','=','% Elongation (TMT)')]).parameter
            # materials = self.env['lerm.parameter.master'].sudo().search([('id','=',line.id)]).parameter_table
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b4ae8d8f-9cbd-4bf5-abe4-c0bf0379b725')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    record.requirement_elongation = req_min
                    break
                else:
                    record.requirement_elongation = 0


    @api.depends('proof_yeid_stress','eln_ref','grade')
    def _compute_yield_conformity(self):
    
        for record in self:
            record.yield_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c732ed77-4c06-4cd4-ae85-b7424c1a24c7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c732ed77-4c06-4cd4-ae85-b7424c1a24c7')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.proof_yeid_stress - record.proof_yeid_stress*mu_value
                    upper = record.proof_yeid_stress + record.proof_yeid_stress*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.yield_conformity = 'pass'
                        break
                    else:
                        record.yield_conformity = 'fail'

    @api.depends('proof_yeid_stress','eln_ref','grade')
    def _compute_yield_nabl(self):
    
        for record in self:
            record.yield_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c732ed77-4c06-4cd4-ae85-b7424c1a24c7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c732ed77-4c06-4cd4-ae85-b7424c1a24c7')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.proof_yeid_stress - record.proof_yeid_stress*mu_value
            upper = record.proof_yeid_stress + record.proof_yeid_stress*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.yield_nabl = 'pass'
                break
            else:
                record.yield_nabl = 'fail'


    @api.depends('eln_ref','grade')
    def _compute_requirement_yield(self):
        for record in self:
            # record.requirement_yield = 0
            # line = self.env['eln.parameters.result'].sudo().search([('eln_id','=',record.eln_ref.id),('parameter.parameter_name','=','Yield Stress (TMT)')]).parameter
            # materials = self.env['lerm.parameter.master'].sudo().search([('id','=',line.id)]).parameter_table
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c732ed77-4c06-4cd4-ae85-b7424c1a24c7')]).parameter_table
            
            for material in materials:
                print("DATA ", material)
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    record.requirement_yield = req_min
                    break
                else:
                    record.requirement_yield = 0
        
    @api.depends('ts_ys_ratio','eln_ref','grade')
    def _compute_ts_ys_conformity(self):

        for record in self:
            record.ts_ys_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','de4bb55e-9318-4725-ac44-fd1850d9e2eb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','de4bb55e-9318-4725-ac44-fd1850d9e2eb')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.proof_yeid_stress - record.proof_yeid_stress*mu_value
                    upper = record.proof_yeid_stress + record.proof_yeid_stress*mu_value
                    if lower >= req_min :
                        record.ts_ys_conformity = 'pass'
                        break
                    else:
                        record.ts_ys_conformity = 'fail'


    @api.depends('ts_ys_ratio','eln_ref','grade')
    def _compute_ts_ys_nabl(self):

        for record in self:
            record.ts_ys_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','de4bb55e-9318-4725-ac44-fd1850d9e2eb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','de4bb55e-9318-4725-ac44-fd1850d9e2eb')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            req_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.proof_yeid_stress - record.proof_yeid_stress*mu_value
            upper = record.proof_yeid_stress + record.proof_yeid_stress*mu_value
            if lower >= lab_min :
                record.ts_ys_nabl = 'pass'
                break
            else:
                record.ts_ys_nabl = 'fail'

    @api.depends('eln_ref','grade')
    def _compute_requirement_ts_ys(self):
        for record in self:
            # record.requirement_yield = 0
            # line = self.env['eln.parameters.result'].sudo().search([('eln_id','=',record.eln_ref.id),('parameter.parameter_name','=','Yield Stress (TMT)')]).parameter
            # materials = self.env['lerm.parameter.master'].sudo().search([('id','=',line.id)]).parameter_table
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','de4bb55e-9318-4725-ac44-fd1850d9e2eb')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    record.requirement_ts_ys = req_min
                    break
                else:
                    record.requirement_ts_ys = 0
        


    @api.depends('weight', 'lentgh')
    def _compute_weight_per_meter(self):
        for record in self:
            if record.lentgh != 0:
                record.weight_per_meter = record.weight / record.lentgh
                # to be removed
                self._compute_sample_parameters()

            else:
                record.weight_per_meter = 0.0

    @api.depends('weight', 'lentgh')
    def _compute_crossectional_area(self):
        for record in self:
            if record.lentgh != 0:
                # print(record.weight / (0.00785 * record.lentgh))
                record.crossectional_area = round((record.weight / (0.00785 * record.lentgh)),2)
                
            else:
                record.crossectional_area = 0.0

    
    # @api.depends('crossectional_area')
    # def _compute_gauge_length(self):
    #     for record in self:
    #         record.gauge_length = ((5.65 * math.sqrt(record.crossectional_area)),2)
    # @api.depends('crossectional_area')
    # def _compute_gauge_length(self):
    #     for record in self:
    #         gauge_length = round((math.sqrt(record.crossectional_area) * 5.65),2)
    #         record.gauge_length = gauge_length
            # record.gauge_length = round(gauge_length, 2)
                
   

    # @api.depends('crossectional_area')
    # def _compute_gauge_length(self):
    #     for record in self:
    #         gauge_length = math.ceil(math.sqrt(record.crossectional_area) * 5.65)
    #         record.gauge_length = gauge_length
    @api.depends('crossectional_area')
    def _compute_gauge_length(self):
        for record in self:
            gauge_length = math.sqrt(record.crossectional_area) * 5.65
            # Check if the decimal part is greater than or equal to 0.5
            if gauge_length - int(gauge_length) >= 0.5:
                rounded_gauge_length = math.ceil(gauge_length)
            else:
                rounded_gauge_length = math.floor(gauge_length)
            record.gauge_length = int(rounded_gauge_length)

    @api.depends('yeild_load','crossectional_area')
    def _compute_proof_yeid_stress(self):
        for record in self:
            if record.crossectional_area != 0:
                record.proof_yeid_stress = record.yeild_load / record.crossectional_area * 1000
            else:
                record.proof_yeid_stress = 0.0

    @api.depends('ultimate_load')
    def _compute_ult_tens_strgth(self):
        for record in self:
            if record.crossectional_area != 0:
                record.ult_tens_strgth = record.ultimate_load / record.crossectional_area * 1000
            else:
                record.ult_tens_strgth = 0.0


    @api.depends('gauge_length','elongated_gauge_length')
    def _compute_elongation_percent(self):
        for record in self:
            if record.gauge_length != 0:
                record.percent_elongation = ((record.elongated_gauge_length - record.gauge_length)/record.gauge_length)*100
            else:
                record.percent_elongation = 0


    @api.model
    def create(self, vals):
        record = super(SteelTmtBarLine, self).create(vals)
        # import wdb;wdb.set_trace()
        # record.get_all_fields()
        self._compute_size_id()
        self._compute_grade_id()
        self._compute_sample_parameters()
        record.eln_ref.write({'model_id':record.id})
        return record

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()
        self._compute_size_id()
        self._compute_grade_id()
        self._compute_requirement_weight_per_meter()
        self._compute_requirement_elongation()
        self._compute_requirement_ts_ys()
        self._compute_requirement_yield()
        self._compute_requirement_utl()

        return super(SteelTmtBarLine, self).read(fields=fields, load=load)


    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    # @api.onchange('bend_test1')
    # def _compute_wdb(self):
    #     import wdb; wdb.set_trace()
        
    

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size = self.eln_ref.size_id.id

    @api.depends('eln_ref')
    def _compute_dia(self):
        for record in self:
            pattern = r'\d+'
            match = re.search(pattern, str(record.eln_ref.size_id.size))
            if match:
                dia = int(match.group())
                record.diameter = int(match.group())
            else:
                record.diameter = 0
                 


    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == '7da4cce7-4027-4d73-955e-ca7f7a2a2228':
                result.result_char = round(self.ult_tens_strgth,2)
                if self.uts_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == 'c732ed77-4c06-4cd4-ae85-b7424c1a24c7':
                result.result_char = round(self.proof_yeid_stress,2)
                if self.yield_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == 'b4ae8d8f-9cbd-4bf5-abe4-c0bf0379b725':
                result.result_char = self.percent_elongation
                if self.elongation_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == 'de4bb55e-9318-4725-ac44-fd1850d9e2eb':
                result.result_char = round(self.ts_ys_ratio,2)
                if self.ts_ys_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '15558232-8a13-472c-b10d-1fc011e63aeb':
                result.result_char = round(self.weight_per_meter,3)
                if self.weight_per_meter_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '9156ec17-ae78-4f98-987f-af5d39e407f2':
                result.result_char =self.fracture
                continue
            if result.parameter.internal_id == 'addd0c61-adb6-447d-b668-1fba0744680f':
                result.result_char = self.bend_test1
                continue
            if result.parameter.internal_id == 'f781bfd8-550b-45f4-81ac-43f856d147b8':
                result.result_char = self.re_bend_test1
                continue

        return {
                'view_mode': 'form',
                'res_model': "lerm.eln",
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.eln_ref.id,
                
            }
        # return {'type': 'ir.actions.client', 'tag': 'history_back'}

    


    # @api.depends('tests')
    # def _compute_visible(self):
    #     fracture_test = self.env['mechanical.tmt.test'].sudo().search([('name', '=', 'Fracture')])
    #     bend_test = self.env['mechanical.tmt.test'].sudo().search([('name', '=', 'Bend Test')])
    #     rebend_test = self.env['mechanical.tmt.test'].sudo().search([('name', '=', 'Rebend Test')])


    #     for record in self:
    #         record.fracture_visible = False
    #         record.bend_visible  = False  
    #         record.rebend_visible = False
            
    #         if fracture_test in record.tests:
    #             record.fracture_visible = True
    #         if bend_test in record.tests:
    #             record.bend_visible = True
    #         if rebend_test in record.tests:
    #             record.rebend_visible = True

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)
            



class MechanicalTmtTest(models.Model):
    _name = "mechanical.tmt.test"
    _rec_name = "name"
    name = fields.Char("Name")