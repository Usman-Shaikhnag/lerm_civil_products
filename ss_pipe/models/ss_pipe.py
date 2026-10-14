from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
import re
from decimal import Decimal, ROUND_HALF_UP


# SS Pipe Open Form parameter rows, in display order.
# Maps the visibility field that drives the row to the lerm.parameter.master
# internal_id of the parameter that must be selected in sample_parameters.
SS_PIPE_OPEN_FORM_PARAMETERS = [
    ('width_visible', 'a16cec22-5428-43f1-a8f6-d5d6e6ee3a9a'),
    ('thickness_visible', '02413117-81e7-4cbb-8c5c-15c515c3d7e7'),
    ('area_visible', '8f0f7137-d5da-4817-9ffc-dc530917f0ad'),
    ('gauge_length_visible', '56104329-1ec9-4523-81b5-7375335f885e'),
    ('final_length_visible', 'f42d31f0-eb4e-4a41-89f7-26c7bd2e7794'),
    ('yeild_load_visible', '69f08664-1a96-4a6b-846d-8f8360dc5839'),
    ('ultimate_load_visible', 'e81281b4-490b-491c-95f9-bc94719136de'),
    ('proof_yeid_stress_visible', '1c309c9f-dfb7-4c91-b54c-12ce5db48d74'),
    ('ult_tens_strgth_visible', '4088c109-b222-45b9-b558-e912766e8c9b'),
    ('elongation_visible', '4ffc84fb-37c0-472d-9b10-ca48b6a3406c'),
    ('flattening_test_visible', 'b13f7327-187d-40b6-a93e-ff649609d7db'),
    ('fracture_visible', 'e4caf2f5-dd42-4542-a423-5f360fd0eccf'),
]


class SsPipe(models.Model):
    _name = "ss.pipe"
    _inherit = "lerm.eln"
    _rec_name = "name"
   
    
   
    Id_no = fields.Char("ID No")
    name = fields.Char("Name",default="SS Pipe")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)
    width = fields.Float(string="Width mm")
    thickness = fields.Float(string="Thickness mm",digits=(16, 2))
    weight = fields.Float(string="Weight, in kg",digits=(10, 2))
    weight_per_meter = fields.Float(string="Weight per meter, kg/m",compute="_compute_weight_per_meter",store=True)
    area = fields.Float(string="AREA mm²",compute="_compute_area",store=True)
    gauge_length1 = fields.Integer(string="Gauge Length mm",compute="_compute_gauge_length",store=True)
    final_length = fields.Float(string="FINAL LENGTH mm")
    # proof_2_percent = fields.Float(string="0.2% proof Load / Yield Load, KN")
    elongation = fields.Float(string="% Elongation",compute="_compute_elongation_percent",store=True,digits=(12,2))
    yeild_load = fields.Float(string="0.2% proof Load / Yield Load, KN")
    ultimate_load = fields.Float(string="Ultimate Load, KN")
    proof_yeid_stress = fields.Float(string="0.2% Proof Stress / Yield Stress N/mm2",compute="_compute_proof_yeid_stress",store=True,digits=(12,2))
    ult_tens_strgth = fields.Float(string="Ultimate Tensile Strength, N/mm2",compute="_compute_ult_tens_strgth",store=True,digits=(12,2))
    fracture = fields.Char("Fracture (Within Gauge Length)",default="W.G.L")
    eln_ref = fields.Many2one('lerm.eln',string="ELN")
    ts_ys_ratio = fields.Float(string="TS/YS Ratio",compute="_compute_ts_ys_ratio",store=True)
    weight_per_meter = fields.Float(string="Weight per meter",compute="_compute_weight_per_meter",store=True)
    variation = fields.Float(string="Variation")

    requirement_utl = fields.Float(string="Requirement",compute="_compute_requirement_utl",store=True)
    requirement_yield = fields.Float(string="Requirement",compute="_compute_requirement_yield",store=True)
    requirement_ts_ys = fields.Float(string="Requirement",compute="_compute_requirement_ts_ys",store=True)
    requirement_elongation = fields.Float(string="Requirement",compute="_compute_requirement_elongation",store=True)
    requirement_weight_per_meter = fields.Float(string="Requirement",compute="_compute_requirement_weight_per_meter",digits=(16, 4),store=True)

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    tests = fields.Many2many("mechanical.tmt.test",string="Tests")
    # fracture_visible = fields.Boolean("Fracture visible",compute="_compute_visible",store=True)
    # flattening_visible = fields.Boolean("Flattening visible",compute="_compute_visible",store=True)
    # rebend_visible = fields.Boolean("Rebend visible",compute="_compute_visible",store=True)

    width2 = fields.Float(string="Width mm")
    thickness2 = fields.Float(string="Thickness mm",digits=(16, 2))
    area2 = fields.Float(string="AREA mm²",compute="_compute_area2",store=True)
    gauge_length2 = fields.Integer(string="Gauge Length mm",compute="_compute_gauge_length2",store=True)
    final_length2 = fields.Float(string="FINAL LENGTH mm")
    yeild_load2 = fields.Float(string="0.2% proof Load / Yield Load, KN")
    ultimate_load2 = fields.Float(string="Ultimate Load, KN")
    proof_yeid_stress2 = fields.Float(string="0.2% Proof Stress / Yield Stress N/mm2",compute="_compute_proof_yeid_stress2",store=True,digits=(12,2))
    ult_tens_strgth2 = fields.Float(string="Ultimate Tensile Strength, N/mm2",compute="_compute_ult_tens_strgth2",store=True,digits=(12,2))
    elongation2 = fields.Float(string="% Elongation",compute="_compute_elongation_percent2",store=True,digits=(12,2))
     
    flattening_test2 = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non-satisfactory', 'Non-Satisfactory')],"Flattening Test",store=True)
    
    fracture2 = fields.Char("Fracture (Within Gauge Length)",default="W.G.L")

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)


    @api.depends('width2', 'thickness2')
    def _compute_area2(self):
        for record in self:
            record.area2 = record.width2 * record.thickness2
            record.gauge_length2 = math.ceil(5.65 * math.sqrt(record.area2))

    @api.onchange('width2', 'thickness2')
    def _onchange_area2(self):
        self._compute_area2()

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

    @api.onchange('area2')
    def _onchange_gauge_length2(self):
        self._compute_gauge_length2()


    @api.depends('yeild_load2', 'area2')
    def _compute_proof_yeid_stress2(self):
        for record in self:
            if record.area2 != 0:
                proof_yeid_stress2 = Decimal(record.yeild_load2) / Decimal(record.area2) * 1000
                record.proof_yeid_stress2 = float(proof_yeid_stress2.quantize(Decimal('.01')))
            else:
                record.proof_yeid_stress2 = 0.0

    @api.depends('ultimate_load2', 'area2')
    def _compute_ult_tens_strgth2(self):
        for record in self:
            if record.area2 != 0:
                ult_tens_strgth2 = Decimal(record.ultimate_load2) / Decimal(record.area2) * Decimal('1000')
                float_result3 = float(ult_tens_strgth2.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP))
                record.ult_tens_strgth2 = round(float_result3, 2)
            else:
                record.ult_tens_strgth2 = 0.0

    @api.depends('gauge_length2','final_length2')
    def _compute_elongation_percent2(self):
        for record in self:
            if record.gauge_length2 != 0:
                record.elongation2 = ((record.final_length2 - record.gauge_length2)/record.gauge_length2)*100
            else:
                record.elongation2 = 0




    
    flattening_test = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non-satisfactory', 'Non-Satisfactory')],"Flattening Test",store=True)
    
    re_bend_test = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non-satisfactory', 'Non-Satisfactory')],"Re-Bend Test",store=True)


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

    # Visibility fields for dynamic Open Form parameter rows
    width_visible = fields.Boolean("Width", compute="_compute_visible")
    thickness_visible = fields.Boolean("Thickness", compute="_compute_visible")
    area_visible = fields.Boolean("Area", compute="_compute_visible")
    gauge_length_visible = fields.Boolean("Gauge Length", compute="_compute_visible")
    final_length_visible = fields.Boolean("Final Length", compute="_compute_visible")
    yeild_load_visible = fields.Boolean("Yield Load", compute="_compute_visible")
    ultimate_load_visible = fields.Boolean("Ultimate Load", compute="_compute_visible")
    proof_yeid_stress_visible = fields.Boolean("Proof/Yield Stress", compute="_compute_visible")
    ult_tens_strgth_visible = fields.Boolean("UTS", compute="_compute_visible")
    elongation_visible = fields.Boolean("Elongation", compute="_compute_visible")
    flattening_test_visible = fields.Boolean("Flattening Test", compute="_compute_visible")
    fracture_visible = fields.Boolean("Fracture", compute="_compute_visible")
    flattening_visible = fields.Boolean("Flattening Test", compute="_compute_visible")
    rebend_visible = fields.Boolean("Rebend Test", compute="_compute_visible")

    uts_nabl = fields.Selection([
        ('pass', 'Nabl'),
        ('fail', 'Non-Nabl')],string="NABL",compute="_compute_uts_nabl",store=True)

    yield_nabl = fields.Selection([
        ('pass', 'Nabl'),
        ('fail', 'Non-Nabl')],string="NABL",compute="_compute_yield_nabl",store=True)

    elongation_nabl = fields.Selection([
        ('pass', 'Nabl'),
        ('fail', 'Non-Nabl')],string="NABL",compute="_compute_elongation_nabl",store=True)

    ts_ys_nabl = fields.Selection([
        ('pass', 'Nabl'),
        ('fail', 'Non-Nabl')],string="NABL",compute="_compute_ts_ys_nabl",store=True)

    weight_per_meter_nabl = fields.Selection([
        ('pass', 'Nabl'),
        ('fail', 'Non-Nabl')],string="NABL",compute="_compute_weight_per_meter_nabl",store=True)

    @api.depends('eln_ref', 'sample_parameters')
    def _compute_visible(self):
        for record in self:
            for field_name, _internal_id in SS_PIPE_OPEN_FORM_PARAMETERS:
                record[field_name] = False
            for sample in record.sample_parameters:
                for field_name, internal_id in SS_PIPE_OPEN_FORM_PARAMETERS:
                    if sample.internal_id == internal_id:
                        record[field_name] = True
            record.flattening_visible = record.flattening_test_visible
            record.rebend_visible = False

    @api.depends('weight','thickness')
    def _compute_weight_per_meter(self):
        for record in self:
            if record.thickness != 0:   
                record.weight_per_meter =  record.weight/record.thickness
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4088c109-b222-45b9-b558-e912766e8c9b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4088c109-b222-45b9-b558-e912766e8c9b')]).parameter_table
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
            record.uts_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4088c109-b222-45b9-b558-e912766e8c9b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4088c109-b222-45b9-b558-e912766e8c9b')]).parameter_table
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

    def _parameter_line(self, internal_id):
        self.ensure_one()
        lines = self.env['lerm.parameter.master.table']
        parameter = self.env['lerm.parameter.master'].sudo().search([('internal_id','=',internal_id)], limit=1)
        if not parameter:
            return lines
        if parameter.fetch_by_grade and not self.grade:
            return lines
        if parameter.fetch_by_size and not self.size:
            return lines
        domain = [('parameter_id','=',parameter.id)]
        if parameter.fetch_by_grade:
            domain += [('grade','=',self.grade.id)]
        if parameter.fetch_by_size:
            domain += [('size','=',self.size.id)]
        lines = self.env['lerm.parameter.master.table'].sudo().search(domain)
        if self.eln_ref.material:
            lines = lines.filtered(lambda line: not line.material or line.material.id == self.eln_ref.material.id)
        return lines[:1]

    @api.depends('eln_ref','grade','size')
    def _compute_requirement_utl(self):
        for record in self:
            record.requirement_utl = record._parameter_line('4088c109-b222-45b9-b558-e912766e8c9b').req_min or 0.0



    @api.depends('elongation','eln_ref','grade')
    def _compute_elongation_conformity(self):
       
        for record in self:
            record.elongation_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4ffc84fb-37c0-472d-9b10-ca48b6a3406c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4ffc84fb-37c0-472d-9b10-ca48b6a3406c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.elongation - record.elongation*mu_value
                    upper = record.elongation + record.elongation*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.elongation_conformity = 'pass'
                        break
                    else:
                        record.elongation_conformity = 'fail'

    @api.depends('elongation','eln_ref','grade')
    def _compute_elongation_nabl(self):
       
        for record in self:
            record.elongation_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4ffc84fb-37c0-472d-9b10-ca48b6a3406c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4ffc84fb-37c0-472d-9b10-ca48b6a3406c')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
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

    @api.depends('eln_ref','grade','size')
    def _compute_requirement_elongation(self):
        for record in self:
            record.requirement_elongation = record._parameter_line('4ffc84fb-37c0-472d-9b10-ca48b6a3406c').req_min or 0.0


    @api.depends('proof_yeid_stress','eln_ref','grade')
    def _compute_yield_conformity(self):
    
        for record in self:
            record.yield_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1c309c9f-dfb7-4c91-b54c-12ce5db48d74')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1c309c9f-dfb7-4c91-b54c-12ce5db48d74')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1c309c9f-dfb7-4c91-b54c-12ce5db48d74')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1c309c9f-dfb7-4c91-b54c-12ce5db48d74')]).parameter_table
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


    @api.depends('eln_ref','grade','size')
    def _compute_requirement_yield(self):
        for record in self:
            record.requirement_yield = record._parameter_line('1c309c9f-dfb7-4c91-b54c-12ce5db48d74').req_min or 0.0
        
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
    def _compute_ts_ys_conformity(self):

        for record in self:
            record.ts_ys_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','de4bb55e-9318-4725-ac44-fd1850d9e2eb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','de4bb55e-9318-4725-ac44-fd1850d9e2eb')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    req_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.proof_yeid_stress - record.proof_yeid_stress*mu_value
                    upper = record.proof_yeid_stress + record.proof_yeid_stress*mu_value
                    if lower >= lab_min :
                        record.ts_ys_conformity = 'pass'
                        break
                    else:
                        record.ts_ys_conformity = 'fail'

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
        


    @api.depends('weight', 'thickness')
    def _compute_weight_per_meter(self):
        for record in self:
            if record.thickness != 0:
                record.weight_per_meter = record.weight / record.thickness
            else:
                record.weight_per_meter = 0.0



    @api.depends('width', 'thickness')
    def _compute_area(self):
        for record in self:
            record.area = record.width * record.thickness if (record.width or 0) and (record.thickness or 0) else 0.0

    @api.onchange('width', 'thickness')
    def _onchange_width_thickness(self):
        self.area = (self.width or 0.0) * (self.thickness or 0.0)

      
    @api.depends('area')
    def _compute_gauge_length(self):
        for record in self:
            if not record.area or record.area <= 0:
                record.gauge_length1 = 0
                continue
            gauge_length1 = math.sqrt(record.area) * 5.65
            if gauge_length1 - int(gauge_length1) >= 0.5:
                rounded_gauge_length1 = math.ceil(gauge_length1)
            else:
                rounded_gauge_length1 = math.floor(gauge_length1)
            record.gauge_length1 = int(rounded_gauge_length1)

    @api.onchange('area', 'width', 'thickness')
    def _onchange_area_computation(self):
        self.area = (self.width or 0.0) * (self.thickness or 0.0)


            
    @api.depends('yeild_load', 'area')
    def _compute_proof_yeid_stress(self):
        for record in self:
            if record.area != 0:
                proof_yeid_stress = Decimal(record.yeild_load) / Decimal(record.area) * 1000
                record.proof_yeid_stress = float(proof_yeid_stress.quantize(Decimal('.01')))
            else:
                record.proof_yeid_stress = 0.0

   
    @api.depends('ultimate_load', 'area')
    def _compute_ult_tens_strgth(self):
        for record in self:
            if record.area != 0:
                ult_tens_strgth = Decimal(record.ultimate_load) / Decimal(record.area) * Decimal('1000')
                float_result = float(ult_tens_strgth.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP))
                record.ult_tens_strgth = round(float_result, 2)
            else:
                record.ult_tens_strgth = 0.0


    @api.depends('gauge_length1','final_length')
    def _compute_elongation_percent(self):
        for record in self:
            if record.gauge_length1 != 0 and record.final_length != 0:
                record.elongation = ((record.final_length - record.gauge_length1)/record.final_length)*100
            else:
                record.elongation = 0

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
        record = super(SsPipe, self).create(vals)
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
            



class MechanicalTmtTest(models.Model):
    _name = "mechanical.tmt.test"
    _rec_name = "name"
    name = fields.Char("Name")