from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class ChemicalHasdenedConcrete(models.Model):
    _name = "chemical.hardened.concrete"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="HARDENED CONCRETE/MORTAR")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    state = fields.Selection([
        ('1-draft', 'In-Test'),
        ('2-confirm', 'In-Check'),
    ], string='State',default='1-draft')


    ph_name = fields.Char("Name",default="pH of 1 % Solution in water")
    ph_visible = fields.Boolean("pH",compute="_compute_visible")
    
    ph_1_percent_a = fields.Float("pH of 1 % Solution in water")
    ph_1_percent_b = fields.Float("pH of 1 % Solution in water")
    ph_1_percent_c = fields.Float("pH of 1 % Solution in water")
    ph_average = fields.Float("Average",compute="_compute_ph_average")

    @api.depends("ph_1_percent_a",'ph_1_percent_b','ph_1_percent_c')
    def _compute_ph_average(self):
        for record in self:
            record.ph_average = (record.ph_1_percent_a + record.ph_1_percent_b + record.ph_1_percent_c)/3

    ph_average_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_ph_average_conformity", store=True)

    @api.depends('ph_average','eln_ref','grade')
    def _compute_ph_average_conformity(self):
            # remove this first when making changes
            self.ph_average_conformity = 'fail'
        
            for record in self:
                record.ph_average_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9f2301d-bba0-42a2-bca8-ecbc5882a2b7')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9f2301d-bba0-42a2-bca8-ecbc5882a2b7')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9f2301d-bba0-42a2-bca8-ecbc5882a2b7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e9f2301d-bba0-42a2-bca8-ecbc5882a2b7')]).parameter_table
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


    #Dissolved Silica


    alkali_aggregate_reactivity_dissolved_name = fields.Char("Name",default="Alkali Aggregate Reactivity ( Dissolved Silica)")
    alkali_aggregate_dissolved_visible = fields.Boolean("Alkali Aggregate",compute="_compute_visible")

    wt_blank_crucible_after_ignition = fields.Float("Wt of Crucible + Blank residue after igniation (gm) (A)",digits=(16, 4))
    wt_blank_crucible_after_hf = fields.Float("Wt of  Cruciable +Blank residue after HF (gm) (B)",digits=(16, 4))
    diff_in_wt_of_silica_blank = fields.Float("Diff. in Wt of silica in Blank (gm)  = A - B ",compute="_compute_diff_in_wt_of_silica_blank",digits=(16, 4))

    # alkali_aggregate_reactivity_alkalinity_name = fields.Char("Name",default="Alkali Aggregate Reactivity (Reduction in Alkalinity)")
    # alkali_aggregate_alkalinity_visible = fields.Boolean("Alkali Aggregate",compute="_compute_visible")

    wt_crucible_after_ignition_a = fields.Float("Wt of Crucible + Sample residue after igniation (gm) (A)",digits=(16, 4))
    wt_crucible_after_hf_a = fields.Float("Wt of  Cruciable +Sample residue after HF (gm) (B)",digits=(16, 4))
    diff_in_wt_of_silica_a = fields.Float("Diff. in Wt of silica in Sample (gm)  = A - B ",compute="_compute_diff_in_wt_of_silica_a",digits=(16, 4))

    wt_crucible_after_ignition_b = fields.Float("Wt of Crucible + Sample residue after igniation (gm) (A)",digits=(16, 4))
    wt_crucible_after_hf_b = fields.Float("Wt of  Cruciable +Sample residue after HF (gm) (B)",digits=(16, 4))
    diff_in_wt_of_silica_b = fields.Float("Diff. in Wt of silica in Sample (gm)  = A - B ",compute="_compute_diff_in_wt_of_silica_b",digits=(16, 4))

    wt_crucible_after_ignition_c = fields.Float("Wt of Crucible + Sample residue after igniation (gm) (A)",digits=(16, 4))
    wt_crucible_after_hf_c = fields.Float("Wt of  Cruciable +Sample residue after HF (gm) (B)",digits=(16, 4))
    diff_in_wt_of_silica_c = fields.Float("Diff. in Wt of silica in Sample (gm)  = A - B ",compute="_compute_diff_in_wt_of_silica_c",digits=(16, 4))
    
    dissolved_silica_a = fields.Float("Dissolved Silica",compute="_compute_dissolved_silica_a",digits=(16, 3))
    dissolved_silica_b = fields.Float("Dissolved Silica",compute="_compute_dissolved_silica_b",digits=(16, 3))
    dissolved_silica_c = fields.Float("Dissolved Silica",compute="_compute_dissolved_silica_c",digits=(16, 3))

    average_dissolved_silica = fields.Float("Average",compute="_compute_average_dissolved_silica",digits=(16, 3))


    @api.depends('wt_blank_crucible_after_ignition','wt_blank_crucible_after_hf')
    def _compute_diff_in_wt_of_silica_blank(self):
        for record in self:
            record.diff_in_wt_of_silica_blank = record.wt_blank_crucible_after_ignition - record.wt_blank_crucible_after_hf

    @api.depends('wt_crucible_after_ignition_a','wt_crucible_after_hf_a')
    def _compute_diff_in_wt_of_silica_a(self):
        for record in self:
            record.diff_in_wt_of_silica_a = record.wt_crucible_after_ignition_a - record.wt_crucible_after_hf_a


    @api.depends('diff_in_wt_of_silica_blank','diff_in_wt_of_silica_a')
    def _compute_dissolved_silica_a(self):
        for record in self:
            record.dissolved_silica_a = (record.diff_in_wt_of_silica_a - record.diff_in_wt_of_silica_blank) * 3330

    @api.depends('diff_in_wt_of_silica_blank','diff_in_wt_of_silica_b')
    def _compute_dissolved_silica_b(self):
        for record in self:
            record.dissolved_silica_b = (record.diff_in_wt_of_silica_b - record.diff_in_wt_of_silica_blank) * 3330

    @api.depends('diff_in_wt_of_silica_blank','diff_in_wt_of_silica_c')
    def _compute_dissolved_silica_c(self):
        for record in self:
            record.dissolved_silica_c = (record.diff_in_wt_of_silica_c - record.diff_in_wt_of_silica_blank) * 3330
    
    
    # @api.depends('dissolved_silica_a','dissolved_silica_b','dissolved_silica_b')
    # def _compute_average_dissolved_silica(self):
    #     for record in self:
    #         record.average_dissolved_silica = (record.dissolved_silica_a + record.dissolved_silica_b + record.dissolved_silica_c)/3
    @api.depends('dissolved_silica_a', 'dissolved_silica_b', 'dissolved_silica_c')
    def _compute_average_dissolved_silica(self):
        for record in self:
            # Calculate the average dissolved silica
            dissolved_silica_sum = record.dissolved_silica_a + record.dissolved_silica_b + record.dissolved_silica_c
            record.average_dissolved_silica = dissolved_silica_sum / 3 if dissolved_silica_sum != 0 else 0.0


    @api.depends('wt_crucible_after_ignition_b','wt_crucible_after_hf_b')
    def _compute_diff_in_wt_of_silica_b(self):
        for record in self:
            record.diff_in_wt_of_silica_b = record.wt_crucible_after_ignition_b - record.wt_crucible_after_hf_b

    @api.depends('wt_crucible_after_ignition_c','wt_crucible_after_hf_c')
    def _compute_diff_in_wt_of_silica_c(self):
        for record in self:
            record.diff_in_wt_of_silica_c = record.wt_crucible_after_ignition_c - record.wt_crucible_after_hf_c

    average_dissolved_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_average_dissolved_conformity", store=True)

  
    @api.depends('average_dissolved_silica','eln_ref','grade')
    def _compute_average_dissolved_conformity(self):
        
        for record in self:
            record.average_dissolved_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e714e0ff-0fec-4367-86a6-1e89d42810e9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e714e0ff-0fec-4367-86a6-1e89d42810e9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_dissolved_silica - record.average_dissolved_silica*mu_value
                    upper = record.average_dissolved_silica + record.average_dissolved_silica*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_dissolved_conformity = 'pass'
                        break
                    else:
                        record.average_dissolved_conformity = 'fail'


    average_dissolved_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_average_dissolved_nabl", store=True)

    @api.depends('average_dissolved_silica','eln_ref','grade')
    def _compute_average_dissolved_nabl(self):
        
        for record in self:
            record.average_dissolved_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e714e0ff-0fec-4367-86a6-1e89d42810e9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e714e0ff-0fec-4367-86a6-1e89d42810e9')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_dissolved_silica - record.average_dissolved_silica*mu_value
            upper = record.average_dissolved_silica + record.average_dissolved_silica*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_dissolved_nabl = 'pass'
                break
            else:
                record.average_dissolved_nabl = 'fail'



    # Alkalinity Reduction
    
    alkali_aggregate_reactivity_alkalinity_name = fields.Char("Name",default="Alkali Aggregate Reactivity (Reduction in Alkalinity)")
    alkali_aggregate_alkalinity_visible = fields.Boolean("Alkali Aggregate",compute="_compute_visible")

    blank_reading1 = fields.Float("Blank Reading (ml) (A)")
    blank_reading2 = fields.Float("Blank Reading (ml) (A)")
    blank_reading3 = fields.Float("Blank Reading (ml) (A)")

    burette_reading1 = fields.Float("Burette Reading (sample) (ml) (B)")
    burette_reading2 = fields.Float("Burette Reading (sample) (ml) (B)")
    burette_reading3 = fields.Float("Burette Reading (sample) (ml) (B)")

    diff_in_reading1 = fields.Float("Diff in Reading (ml) (A-B)",compute="_compute_diff_reading1")
    diff_in_reading2 = fields.Float("Diff in Reading (ml) (A-B)",compute="_compute_diff_reading2")
    diff_in_reading3 = fields.Float("Diff in Reading (ml) (A-B)",compute="_compute_diff_reading3")

    normality1 = fields.Float("Normality of 0.05N HCL",digits=(16, 4))
    normality2 = fields.Float("Normality of 0.05N HCL",digits=(16, 4))
    normality3 = fields.Float("Normality of 0.05N HCL",digits=(16, 4))

    reduction_in_alkalinity1 = fields.Float("Reduction in Alkalinity" ,compute="_compute_reduction1")
    reduction_in_alkalinity2 = fields.Float("Reduction in Alkalinity",compute="_compute_reduction2")
    reduction_in_alkalinity3 = fields.Float("Reduction in Alkalinity",compute="_compute_reduction3")

    average_reduction_alkalinity = fields.Float("Average",compute="_compute_average_refuction_alkalinity")


    @api.depends('blank_reading1','burette_reading1')
    def _compute_diff_reading1(self):
        for record in self:
            record.diff_in_reading1 = record.blank_reading1 - record.burette_reading1


    @api.depends('blank_reading2','burette_reading2')
    def _compute_diff_reading2(self):
        for record in self:
            record.diff_in_reading2 = record.blank_reading2 - record.burette_reading2


    @api.depends('blank_reading3','burette_reading3')
    def _compute_diff_reading3(self):
        for record in self:
            record.diff_in_reading3 = record.blank_reading3 - record.burette_reading3

   
    @api.depends('diff_in_reading1','normality1')
    def _compute_reduction1(self):
        for record in self:
            record.reduction_in_alkalinity1 = record.diff_in_reading1 * record.normality1 * 1000


    @api.depends('diff_in_reading2','normality2')
    def _compute_reduction2(self):
        for record in self:
            record.reduction_in_alkalinity2 = record.diff_in_reading2 * record.normality2 * 1000

    @api.depends('diff_in_reading3','normality3')
    def _compute_reduction3(self):
        for record in self:
            record.reduction_in_alkalinity3 = record.diff_in_reading3 * record.normality3 * 1000


    @api.depends('reduction_in_alkalinity1','reduction_in_alkalinity2','reduction_in_alkalinity3')
    def _compute_average_refuction_alkalinity(self):
        for record in self:
            record.average_reduction_alkalinity = (record.reduction_in_alkalinity1 + record.reduction_in_alkalinity2 + record.reduction_in_alkalinity3)/3


    average_reduction_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_average_reduction_conformity",  store=True)

    @api.depends('average_reduction_alkalinity','eln_ref','grade')
    def _compute_average_reduction_conformity(self):
        
        for record in self:
            record.average_reduction_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ddb48f6-5260-4db7-a3a5-94f341db6d97')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ddb48f6-5260-4db7-a3a5-94f341db6d97')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_reduction_alkalinity - record.average_reduction_alkalinity*mu_value
                    upper = record.average_reduction_alkalinity + record.average_reduction_alkalinity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_reduction_conformity = 'pass'
                        break
                    else:
                        record.average_reduction_conformity = 'fail'

    average_reduction_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_average_reduction_nabl",  store=True)

    @api.depends('average_reduction_alkalinity','eln_ref','grade')
    def _compute_average_reduction_nabl(self):
        
        for record in self:
            record.average_reduction_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ddb48f6-5260-4db7-a3a5-94f341db6d97')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ddb48f6-5260-4db7-a3a5-94f341db6d97')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_reduction_alkalinity - record.average_reduction_alkalinity*mu_value
            upper = record.average_reduction_alkalinity + record.average_reduction_alkalinity*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_reduction_nabl = 'pass'
                break
            else:
                record.average_reduction_nabl = 'fail'




    #Chloride
    chloride_name = fields.Char("Name",default="Chloride as Cl  BS 1881 Part 124:2015(prestressed concrete)")
    chloride_visible = fields.Boolean("Chloride as Cl  BS 1881 Part 124:2015(prestressed concrete)",compute="_compute_visible")

    chloride_cube = fields.Float("A)Cube Density, Kg/m3")
    chloride_mass = fields.Float("B) Mass of the concrete cube taken for analysis ( gm)",digits=(16, 4))
    chloride_valume = fields.Float("C) Volume of 0.02 N (Silver nitrate added) in blank")
    chloride_reading = fields.Float("D) Burette Reading of 0.1N Ammonium thiocynate  Consumed for  Sample) ( ml)")
    chloride_normality = fields.Float("E) Normality of 0.1 N Ammonium thiocynate solution ( N)")
    chloride_p = fields.Float("F)Chloride, % = ( C-D) x E x 0.03545 x 100/ B",compute="_compute_chloride_p",digits=(12, 3))
    chloride_percent = fields.Float("G)Chloride, Kg/m3 = (F/100 x A)",compute="_compute_chloride_percent",digits=(12, 2))
    # normality_of_ammonia = fields.Float("Normality of ammonia thiocynate (0.1)",digits=(16, 4))
    # chloride_percent = fields.Float("Chloride %",compute="_compute_chloride_percent",digits=(16, 4))
    @api.depends('chloride_valume', 'chloride_reading', 'chloride_normality', 'chloride_mass')
    def _compute_chloride_p(self):
        for record in self:
            if record.chloride_mass != 0:
                record.chloride_p = (record.chloride_valume - record.chloride_reading) * record.chloride_normality * 0.03545 * 100 / record.chloride_mass
            else:
                record.chloride_p = 0.0  
    
    @api.depends('chloride_p', 'chloride_cube')
    def _compute_chloride_percent(self):
        for record in self:
            if record.chloride_cube != 0:
                record.chloride_percent = (record.chloride_p / 100) * record.chloride_cube
            else:
                record.chloride_percent = 0.0 
    

    chloride_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_chloride_conformity", store=True)

    @api.depends('chloride_percent','eln_ref','grade')
    def _compute_chloride_conformity(self):
        
        for record in self:
            record.chloride_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','034d2729-961c-40ae-a642-a26f03a2db5a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','034d2729-961c-40ae-a642-a26f03a2db5a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.chloride_percent - record.chloride_percent*mu_value
                    upper = record.chloride_percent + record.chloride_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.chloride_conformity = 'pass'
                        break
                    else:
                        record.chloride_conformity = 'fail'

    chloride_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_chloride_nabl", store=True)

    @api.depends('chloride_percent','eln_ref','grade')
    def _compute_chloride_nabl(self):
        
        for record in self:
            record.chloride_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','034d2729-961c-40ae-a642-a26f03a2db5a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','034d2729-961c-40ae-a642-a26f03a2db5a')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.chloride_percent - record.chloride_percent*mu_value
            upper = record.chloride_percent + record.chloride_percent*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.chloride_nabl = 'pass'
                break
            else:
                record.chloride_nabl = 'fail'

     #Chloride 2
    chloride_name1 = fields.Char("Name",default="Chloride  as Cl IS 14989 Pt2 :2001")
    chloride_visible1 = fields.Boolean("Chloride  as Cl IS 14989 Pt2 :2001",compute="_compute_visible")

    chloride_density = fields.Float("Density")
    chloride_mass1 = fields.Float("Mass of concrete  sample taken")
    chloride_valume1 = fields.Float("volume of 0.02N silver nitrate added")
    chloride_reading1 = fields.Float("volume of 0.02N ammonium thiocynate  consumed")
    diff = fields.Float("Diff",compute="_compute_diff",digits=(12,1))
    chloride_calculation = fields.Float("Calculation",compute="_compute_chloride_calculation",digits=(12, 3))
    chloride_acide = fields.Float("Acid soluble chloride as Cl Kg/m3",compute="_compute_chloride_acide",digits=(12, 2))
    # normality_of_ammonia = fields.Float("Normality of ammonia thiocynate (0.1)",digits=(16, 4))
    # chloride_percent = fields.Float("Chloride %",compute="_compute_chloride_percent",digits=(16, 4))

    @api.depends('chloride_valume1', 'chloride_reading1')
    def _compute_diff(self):
        for record in self:
            # Calculate the value of diff
            record.diff = record.chloride_valume1 - record.chloride_reading1

    @api.depends('diff', 'chloride_mass1')
    def _compute_chloride_calculation(self):
        for record in self:
            # Calculate the value of chloride_calculation
            record.chloride_calculation = (2 * 0.709 * record.diff / record.chloride_mass1 )  if record.chloride_mass1 != 0 else 0.0

    @api.depends('chloride_calculation', 'chloride_density')
    def _compute_chloride_acide(self):
        for record in self:
            # Calculate the value of chloride_acide
            record.chloride_acide = (record.chloride_calculation * record.chloride_density / 100) if record.chloride_density != 0 else 0.0

  

    chloride_conformity1 = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_chloride_conformity1", store=True)

    @api.depends('chloride_acide','eln_ref','grade')
    def _compute_chloride_conformity1(self):
        
        for record in self:
            record.chloride_conformity1 = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f324e2d6-649f-4223-887e-aec3d85dffa9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f324e2d6-649f-4223-887e-aec3d85dffa9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.chloride_acide - record.chloride_acide*mu_value
                    upper = record.chloride_acide + record.chloride_acide*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.chloride_conformity1 = 'pass'
                        break
                    else:
                        record.chloride_conformity1 = 'fail'

    chloride_nabl1 = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_chloride_nabl1", store=True)

    @api.depends('chloride_acide','eln_ref','grade')
    def _compute_chloride_nabl1(self):
        
        for record in self:
            record.chloride_nabl1 = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f324e2d6-649f-4223-887e-aec3d85dffa9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f324e2d6-649f-4223-887e-aec3d85dffa9')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.chloride_acide - record.chloride_acide*mu_value
            upper = record.chloride_acide + record.chloride_acide*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.chloride_nabl1 = 'pass'
                break
            else:
                record.chloride_nabl1 = 'fail'


        #Chloride
    chloride_name2 = fields.Char("Name",default="Chloride (prestressed concrete)")
    chloride_visible2 = fields.Boolean("Chloride (prestressed concrete)",compute="_compute_visible")

    chloride_cube2 = fields.Float("A)Cube Density, Kg/m3")
    chloride_mass2 = fields.Float("B) Mass of the concrete cube taken for analysis ( gm)",digits=(16, 4))
    chloride_valume2 = fields.Float("C) Volume of 0.02 N (Silver nitrate added) in blank")
    chloride_reading2 = fields.Float("D) Burette Reading of 0.1N Ammonium thiocynate  Consumed for  Sample) ( ml)")
    chloride_normality2 = fields.Float("E) Normality of 0.1 N Ammonium thiocynate solution ( N)")
    chloride_p2 = fields.Float("F)Chloride, % = ( C-D) x E x 0.03545 x 100/ B",compute="_compute_chloride_p2",digits=(12, 3))
    chloride_percent2 = fields.Float("G)Chloride, Kg/m3 = (F/100 x A)",compute="_compute_chloride_percent2",digits=(12, 3))
    # normality_of_ammonia = fields.Float("Normality of ammonia thiocynate (0.1)",digits=(16, 4))
    # chloride_percent = fields.Float("Chloride %",compute="_compute_chloride_percent",digits=(16, 4))
    @api.depends('chloride_valume2', 'chloride_reading2', 'chloride_normality2', 'chloride_mass2')
    def _compute_chloride_p2(self):
        for record in self:
            if record.chloride_mass2 != 0:
                record.chloride_p2 = (record.chloride_valume2 - record.chloride_reading2) * record.chloride_normality2 * 0.03545 * 100 / record.chloride_mass2
            else:
                record.chloride_p2 = 0.0  
    
    @api.depends('chloride_p2', 'chloride_cube2')
    def _compute_chloride_percent2(self):
        for record in self:
            if record.chloride_cube2 != 0:
                record.chloride_percent2 = (record.chloride_p2 / 100) * record.chloride_cube2
            else:
                record.chloride_percent2 = 0.0 
    

    chloride_conformity2 = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_chloride_conformity2", store=True)

    @api.depends('chloride_percent2','eln_ref','grade')
    def _compute_chloride_conformity2(self):
        
        for record in self:
            record.chloride_conformity2 = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98d321ee-f77f-434c-8bae-3711912c80f5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98d321ee-f77f-434c-8bae-3711912c80f5')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.chloride_percent2 - record.chloride_percent2*mu_value
                    upper = record.chloride_percent2 + record.chloride_percent2*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.chloride_conformity2 = 'pass'
                        break
                    else:
                        record.chloride_conformity2 = 'fail'

    chloride_nabl2 = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_chloride_nabl2", store=True)

    @api.depends('chloride_percent2','eln_ref','grade')
    def _compute_chloride_nabl2(self):
        
        for record in self:
            record.chloride_nabl2 = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98d321ee-f77f-434c-8bae-3711912c80f5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98d321ee-f77f-434c-8bae-3711912c80f5')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.chloride_percent2 - record.chloride_percent2*mu_value
            upper = record.chloride_percent2 + record.chloride_percent2*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.chloride_nabl2 = 'pass'
                break
            else:
                record.chloride_nabl2 = 'fail'





    #Sulphate
    sulphate_name = fields.Char("Name",default="Sulphate BS 1881 Part 124:2015")
    sulphate_visible = fields.Boolean("Sulphate",compute="_compute_visible")


    sample_wt_sulphate = fields.Float("A)Cement Content in concete %")
    volume_make_upto_sulphate = fields.Float("B)Mass of the concrete cube sample taken for analysis ( gm)",digits=(16, 4))
    wt_empty_crucible_after_ignition = fields.Float("C) Wt. of Empty crusible gm",digits=(16, 4))
    wt_empty_crucible = fields.Float("D) Wt. of Empty crusible + Residue wt gm",digits=(16, 4))
    difference_in_wt_sulphate = fields.Float("E) Residue Wt,  gm = ( D - C )",compute="_compute_difference_in_wt_sulphate",digits=(16, 4))
    sulphate_so3 = fields.Float("F)%Sulphate as SO3 = E x 34.3/B",compute="_compute_sulphate_so3",digits=(16, 2))
    sulphate_percent = fields.Float("G)Sulphate as SO3 on the basis of Cement content (F)*100/A",compute="_compute_sulphate_percent",digits=(16, 2))

    @api.depends('wt_empty_crucible', 'wt_empty_crucible_after_ignition')
    def _compute_difference_in_wt_sulphate(self):
        for record in self:
            record.difference_in_wt_sulphate = record.wt_empty_crucible - record.wt_empty_crucible_after_ignition

    @api.depends('difference_in_wt_sulphate', 'volume_make_upto_sulphate')
    def _compute_sulphate_so3(self):
        for record in self:
            if record.volume_make_upto_sulphate != 0:
                record.sulphate_so3 = (record.difference_in_wt_sulphate * 34.3) / record.volume_make_upto_sulphate
            else:
                record.sulphate_so3 = 0.0 

    @api.depends('sulphate_so3', 'sample_wt_sulphate')
    def _compute_sulphate_percent(self):
        for record in self:
            if record.sample_wt_sulphate != 0:
                record.sulphate_percent = (record.sulphate_so3 * 100) / record.sample_wt_sulphate
            else:
                record.sulphate_percent = 0.0 



  
    sulphate_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_sulphate_conformity", store=True)

    @api.depends('sulphate_percent','eln_ref','grade')
    def _compute_sulphate_conformity(self):
        
        for record in self:
            record.sulphate_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7dfdb9dd-0d82-4c89-bab8-3853a78dbab3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7dfdb9dd-0d82-4c89-bab8-3853a78dbab3')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.sulphate_percent - record.sulphate_percent*mu_value
                    upper = record.sulphate_percent + record.sulphate_percent*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.sulphate_conformity = 'pass'
                        break
                    else:
                        record.sulphate_conformity = 'fail'

    sulphate_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_sulphate_nabl",  store=True)

    @api.depends('sulphate_percent','eln_ref','grade')
    def _compute_sulphate_nabl(self):
        
        for record in self:
            record.sulphate_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7dfdb9dd-0d82-4c89-bab8-3853a78dbab3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','7dfdb9dd-0d82-4c89-bab8-3853a78dbab3')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.sulphate_percent - record.sulphate_percent*mu_value
            upper = record.sulphate_percent + record.sulphate_percent*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.sulphate_nabl = 'pass'
                break
            else:
                record.sulphate_nabl = 'fail'

    # Names for cement content and cement content is exchanged
    # Cement Content 
    cement_content_name = fields.Char("Name",default="Cement Content 1")
    cement_conten_visible = fields.Boolean("Cement Content",compute="_compute_visible")

    cement_content_mass = fields.Float("Mass of Sample taken",digits=(16, 4))
    cement_content_residue = fields.Float("Wt of crucible+ignited residue",digits=(16, 4))
    cement_content_residue_af = fields.Float("Wt of crucible+After HF residue",digits=(16, 4))

    cement_content_diff = fields.Float("Diff=A2-A3",compute="_compute_cement_content_diff",digits=(16, 4))
    cement_content_sio2 = fields.Float("Sio2=A4*100/A1",compute="_compute_cement_content_sio2",digits=(16, 2))
    cement_content = fields.Float("Cement Content=A5/0.2140",compute="_compute_cement_content",digits=(16, 2))



    @api.depends('cement_content_residue', 'cement_content_residue_af')
    def _compute_cement_content_diff(self):
        for record in self:
            record.cement_content_diff = record.cement_content_residue - record.cement_content_residue_af

    @api.depends('cement_content_diff', 'cement_content_mass')
    def _compute_cement_content_sio2(self):
        for record in self:
            if record.cement_content_mass != 0:
                record.cement_content_sio2 = (record.cement_content_diff * 100) / record.cement_content_mass
            else:
                record.cement_content_sio2 = 0.0

    @api.depends('cement_content_sio2')
    def _compute_cement_content(self):
        for record in self:
            if record.cement_content_sio2 != 0:
                record.cement_content = record.cement_content_sio2 / 0.214
            else:
                record.cement_content = 0.0



    cement_content_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_cement_content_conformity", store=True)

    @api.depends('cement_content','eln_ref','grade')
    def _compute_cement_content_conformity(self):
        
        for record in self:
            record.cement_content_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d8bbd906-0f24-4c77-abc6-b2a8a00d91e6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d8bbd906-0f24-4c77-abc6-b2a8a00d91e6')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.cement_content - record.cement_content*mu_value
                    upper = record.cement_content + record.cement_content*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.cement_content_conformity = 'pass'
                        break
                    else:
                        record.cement_content_conformity = 'fail'

    cement_content_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_cement_content_nabl",  store=True)

    @api.depends('cement_content','eln_ref','grade')
    def _compute_cement_content_nabl(self):
        
        for record in self:
            record.cement_content_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d8bbd906-0f24-4c77-abc6-b2a8a00d91e6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d8bbd906-0f24-4c77-abc6-b2a8a00d91e6')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.cement_content - record.cement_content*mu_value
            upper = record.cement_content + record.cement_content*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.cement_content_nabl = 'pass'
                break
            else:
                record.cement_content_nabl = 'fail'


    cement_content_1_name = fields.Char("Name",default="Cement Content")
    cement_content_1_visible = fields.Boolean("Cement Content",compute="_compute_visible")

    cement_content_wt_sample = fields.Float("Wt of Sample (gm)")
    cement_content_br = fields.Float("BR of 0.01N EDTA")
    cement_content_normality = fields.Float("Normality of EDTA")
    cement_content_dilution = fields.Float("Dilution")
    cement_content_br_n_dilution = fields.Float("BR *0.05608*N*100*dilution/S.wt " , compute="_compute_cement_content_br_n_dilution")
    cement_content_1 = fields.Float("Cement Content", compute="_compute_cement_content_1")
    
    #aggregate ratio

   




    @api.depends('cement_content_wt_sample','cement_content_br','cement_content_normality','cement_content_dilution')
    def _compute_cement_content_br_n_dilution(self):
        for record in self:
            if record.cement_content_wt_sample != 0:
                cement_content_br_n_dilution = (record.cement_content_br * 0.05608 * record.cement_content_normality * 100 * record.cement_content_dilution )/record.cement_content_wt_sample
                record.cement_content_br_n_dilution = round(cement_content_br_n_dilution,2)
            else:
                record.cement_content_br_n_dilution = 0


    @api.depends('cement_content_br_n_dilution')
    def _compute_cement_content_1(self):
        for record in self:
            cement_content_1 = record.cement_content_br_n_dilution * 100/63.5
            record.cement_content_1 = round(cement_content_1,2)

    #compute aggregate ratio
    
   

    cement_content_1_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_cement_content_1_conformity", store=True)

    @api.depends('cement_content','eln_ref','grade')
    def _compute_cement_content_1_conformity(self):
        
        for record in self:
            record.cement_content_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','97527435-edbc-4d33-817f-9596b56b4cd0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','97527435-edbc-4d33-817f-9596b56b4cd0')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.cement_content - record.cement_content*mu_value
                    upper = record.cement_content + record.cement_content*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.cement_content_1_conformity = 'pass'
                        break
                    else:
                        record.cement_content_1_conformity = 'fail'

    cement_content_1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_cement_content_1_nabl",  store=True)

    @api.depends('cement_content','eln_ref','grade')
    def _compute_cement_content_1_nabl(self):
        
        for record in self:
            record.cement_content_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','97527435-edbc-4d33-817f-9596b56b4cd0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','97527435-edbc-4d33-817f-9596b56b4cd0')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.cement_content - record.cement_content*mu_value
            upper = record.cement_content + record.cement_content*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.cement_content_1_nabl = 'pass'
                break
            else:
                record.cement_content_1_nabl = 'fail'

    # Lime 
    lime_name = fields.Char("Name",default="Lime")
    lime_visible = fields.Boolean("Cement Content",compute="_compute_visible")

    lime_wt_sample = fields.Float("Wt of Sample (gm)")
    lime_br = fields.Float("BR of 0.01N EDTA")
    lime_normality = fields.Float("Normality of EDTA")
    lime_dilution = fields.Float("Dilution")
    lime_br_n_dilution = fields.Float("BR *0.05608*N*100*dilution/S.wt ")
    
    

    lime_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_lime_conformity", store=True)

    @api.depends('cement_content','eln_ref','grade')
    def _compute_lime_conformity(self):
        
        for record in self:
            record.lime_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ad567820-1a05-4d8b-bc7e-f58b42f78076')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ad567820-1a05-4d8b-bc7e-f58b42f78076')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.lime_br_n_dilution - record.lime_br_n_dilution*mu_value
                    upper = record.lime_br_n_dilution + record.lime_br_n_dilution*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.lime_conformity = 'pass'
                        break
                    else:
                        record.lime_conformity = 'fail'

    

    lime_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_lime_nabl",  store=True)

    @api.depends('lime_br_n_dilution','eln_ref','grade')
    def _compute_lime_nabl(self):
        
        for record in self:
            record.lime_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ad567820-1a05-4d8b-bc7e-f58b42f78076')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ad567820-1a05-4d8b-bc7e-f58b42f78076')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.lime_br_n_dilution - record.lime_br_n_dilution*mu_value
            upper = record.lime_br_n_dilution + record.lime_br_n_dilution*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.lime_nabl = 'pass'
                break
            else:
                record.lime_nabl = 'fail'

   # cement Aggregate ratio 
    cement_aggregate_ratio_name = fields.Char("Name",default="Cement Aggregate Ratio")
    cement_aggregate_ratio_visible = fields.Boolean("Cement Aggregate Ratio",compute="_compute_visible")

    cement_aggregate_ratio_wt_sample = fields.Float("Wt of Sample (gm)",digits=(16,4))
    cement_aggregate_ratio_br = fields.Float("BR of 0.01N EDTA")
    cement_aggregate_ratio_normality = fields.Float("Normality of EDTA",digits=(16,4))
    cement_aggregate_ratio_dilution = fields.Float("Dilution")
    cement_aggregate_ratio_br_n_dilution = fields.Float("BR *0.05608*N*100*dilution/S.wt " , compute="_compute_cement_aggregate_br_n_dilution")
    cement_content_aggregate_ratio = fields.Float("Cement Content ", compute="_compute_cement_content_aggregate_ratio")
    cement_aggregate_percent = fields.Float('Aggregate %',compute="_commpute_aggregate_percent")
    cement_aggregate_ratio = fields.Float('Ratio',compute="_compute_cement_aggregate_ratio")
    cement_aggregate_ratio_result = fields.Char('Cement Content Ratio 1:H',compute="_compute_cement_aggregate_ratio_result")


    @api.depends('cement_aggregate_ratio_wt_sample','cement_aggregate_ratio_normality','cement_aggregate_ratio_br','cement_aggregate_ratio_dilution')
    def _compute_cement_aggregate_br_n_dilution(self):
        for record in self:
            if record.cement_aggregate_ratio_wt_sample !=0:
                br = (record.cement_aggregate_ratio_br * record.cement_aggregate_ratio_normality * 0.05608 * record.cement_aggregate_ratio_dilution * 100)/record.cement_aggregate_ratio_wt_sample
                record.cement_aggregate_ratio_br_n_dilution = round(br,2)
            else:
                record.cement_aggregate_ratio_br_n_dilution = 0


    @api.depends('cement_aggregate_ratio_br_n_dilution')
    def _compute_cement_content_aggregate_ratio(self):
        for record in self:
            cement_content_aggregate_ratio = (record.cement_aggregate_ratio_br_n_dilution * 100)/63.5
            record.cement_content_aggregate_ratio = round(cement_content_aggregate_ratio,2)

    @api.depends('cement_content_aggregate_ratio')
    def _commpute_aggregate_percent(self):
        for record in self:
            record.cement_aggregate_percent = 100 - record.cement_content_aggregate_ratio 

    @api.depends('cement_aggregate_percent','cement_content_aggregate_ratio')
    def _compute_cement_aggregate_ratio(self):
        for record in self:
            if record.cement_content_aggregate_ratio !=0:
                ratio = record.cement_aggregate_percent / record.cement_content_aggregate_ratio
                record.cement_aggregate_ratio = round(ratio,2)
            else:
                record.cement_aggregate_ratio = 0

    @api.depends('cement_aggregate_ratio')
    def _compute_cement_aggregate_ratio_result(self):
        for record in self:
            result = "1:"+str(record.cement_aggregate_ratio)
            record.cement_aggregate_ratio_result = result

    cement_aggregate_ratio_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_cement_aggregate_ratio_conformity", store=True)

    @api.depends('cement_content_aggregate_ratio','eln_ref','grade')
    def _compute_cement_aggregate_ratio_conformity(self):
        
        for record in self:
            record.cement_aggregate_ratio_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9fa390be-1b85-4a6e-908d-cf3068e5ced4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9fa390be-1b85-4a6e-908d-cf3068e5ced4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.cement_content_aggregate_ratio - record.cement_content_aggregate_ratio*mu_value
                    upper = record.cement_content_aggregate_ratio + record.cement_content_aggregate_ratio*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.cement_aggregate_ratio_conformity = 'pass'
                        break
                    else:
                        record.cement_aggregate_ratio_conformity = 'fail'

    cement_aggregate_ratio_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_cement_aggregate_ratio_nabl",  store=True)

    @api.depends('cement_content_aggregate_ratio','eln_ref','grade')
    def _compute_cement_aggregate_ratio_nabl(self):
        
        for record in self:
            record.cement_aggregate_ratio_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9fa390be-1b85-4a6e-908d-cf3068e5ced4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9fa390be-1b85-4a6e-908d-cf3068e5ced4')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.cement_content_aggregate_ratio - record.cement_content_aggregate_ratio*mu_value
            upper = record.cement_content_aggregate_ratio + record.cement_content_aggregate_ratio*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.cement_aggregate_ratio_nabl = 'pass'
                break
            else:
                record.cement_aggregate_ratio_nabl = 'fail'


    @api.depends('sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.chloride_visible = False
            record.sulphate_visible = False
            record.alkali_aggregate_alkalinity_visible = False
            record.ph_visible = False
            record.alkali_aggregate_dissolved_visible = False
            record.chloride_visible1 = False
            record.chloride_visible2 = False
            record.cement_conten_visible = False
            record.cement_content_1_visible = False
            record.lime_visible = False

            record.cement_aggregate_ratio_visible = False
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == 'e9f2301d-bba0-42a2-bca8-ecbc5882a2b7':
                    record.ph_visible = True
                if sample.internal_id == '034d2729-961c-40ae-a642-a26f03a2db5a':
                    record.chloride_visible = True
                if sample.internal_id == '7dfdb9dd-0d82-4c89-bab8-3853a78dbab3':
                    record.sulphate_visible = True
                if sample.internal_id == '5ddb48f6-5260-4db7-a3a5-94f341db6d97':
                    record.alkali_aggregate_alkalinity_visible = True
                if sample.internal_id == 'e714e0ff-0fec-4367-86a6-1e89d42810e9':
                    record.alkali_aggregate_dissolved_visible = True
                if sample.internal_id == 'f324e2d6-649f-4223-887e-aec3d85dffa9':
                    record.chloride_visible1 = True
                if sample.internal_id == '98d321ee-f77f-434c-8bae-3711912c80f5':
                    record.chloride_visible2 = True
                if sample.internal_id == 'd8bbd906-0f24-4c77-abc6-b2a8a00d91e6':
                    record.cement_conten_visible = True
                if sample.internal_id == '97527435-edbc-4d33-817f-9596b56b4cd0':
                    record.cement_content_1_visible = True
                if sample.internal_id == 'ad567820-1a05-4d8b-bc7e-f58b42f78076':
                    record.lime_visible = True
                if sample.internal_id == '9fa390be-1b85-4a6e-908d-cf3068e5ced4':
                    record.cement_aggregate_ratio_visible = True
                    	

    
          

    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        
        record = super(ChemicalHasdenedConcrete, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()
        

        return super(ChemicalHasdenedConcrete, self).read(fields=fields, load=load)
    
    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            # ph 
            if result.parameter.internal_id == 'e9f2301d-bba0-42a2-bca8-ecbc5882a2b7':
                result.result_char = round(self.ph_average,2)
                if self.ph_average_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # Dissolved Silica 
            if result.parameter.internal_id == 'e714e0ff-0fec-4367-86a6-1e89d42810e9':
                result.result_char = round(self.average_dissolved_silica,2)
                if self.average_dissolved_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # Chloride
            if result.parameter.internal_id == '034d2729-961c-40ae-a642-a26f03a2db5a':
                result.result_char = round(self.chloride_percent,2)
                if self.chloride_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # Sulphate 
            if result.parameter.internal_id == '7dfdb9dd-0d82-4c89-bab8-3853a78dbab3':
                result.result_char = round(self.sulphate_percent,2)
                if self.sulphate_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # Alkali Aggregate
            if result.parameter.internal_id == '5ddb48f6-5260-4db7-a3a5-94f341db6d97':
                result.result_char = round(self.average_reduction_alkalinity,2)
                if self.average_reduction_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # Chloride 1 
            if result.parameter.internal_id == 'f324e2d6-649f-4223-887e-aec3d85dffa9':
                result.result_char = round(self.chloride_acide,2)
                if self.chloride_nabl1 == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # Chloride 2
            if result.parameter.internal_id == '98d321ee-f77f-434c-8bae-3711912c80f5':
                result.result_char = round(self.chloride_percent2,2)
                if self.chloride_nabl2 == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # Cement Content
            if result.parameter.internal_id == 'd8bbd906-0f24-4c77-abc6-b2a8a00d91e6':
                result.result_char = round(self.cement_content,2)
                if self.cement_content_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # Cement Content 1
            if result.parameter.internal_id == '97527435-edbc-4d33-817f-9596b56b4cd0':
                result.result_char = round(self.cement_content_1,2)
                if self.cement_content_1_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # Lime
            if result.parameter.internal_id == 'ad567820-1a05-4d8b-bc7e-f58b42f78076':
                result.result_char = round(self.lime_br_n_dilution,2)
                if self.lime_nabl == 'pass':
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


        
    def get_all_fields(self):
        record = self.env['chemical.hardened.concrete'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    


    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
    