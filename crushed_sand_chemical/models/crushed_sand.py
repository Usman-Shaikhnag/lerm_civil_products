from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class ChemicalCrushedSand(models.Model):
    _name = "chemical.crushed.sand"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="CRUSHED SAND/NATURAL SAND/MANUFACTURED SAND")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)


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

    ph_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_ph_conformity", store=True)

    @api.depends('ph_average','eln_ref','grade')
    def _compute_ph_conformity(self):
            # remove this first when making changes
            self.ph_conformity = 'fail'
        
            for record in self:
                record.ph_conformity = 'fail'
                line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','481fb826-5804-40f1-b7a1-54d435149afb')])
                materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','481fb826-5804-40f1-b7a1-54d435149afb')]).parameter_table
                for material in materials:
                    if material.grade.id == record.grade.id:
                        req_min = material.req_min
                        req_max = material.req_max
                        mu_value = line.mu_value
                        
                        lower = record.ph_average - record.ph_average*mu_value
                        upper = record.ph_average + record.ph_average*mu_value
                        if lower >= req_min and upper <= req_max:
                            record.ph_conformity = 'pass'
                            break
                        else:
                            record.ph_conformity = 'fail'

    ph_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_ph_nabl", store=True)

    # @api.depends('ph_average','eln_ref','grade')
    # def _compute_ph_nabl(self):
    #     # remove this first
    #     self.ph_nabl = 'fail'
        
    #     for record in self:
    #         record.ph_nabl = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','481fb826-5804-40f1-b7a1-54d435149afb')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','481fb826-5804-40f1-b7a1-54d435149afb')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 lab_min = line.lab_min_value
    #                 lab_max = line.lab_max_value
    #                 mu_value = line.mu_value
                    
    #                 lower = record.ph_average - record.ph_average*mu_value
    #                 upper = record.ph_average + record.ph_average*mu_value
    #                 if lower >= lab_min and upper <= lab_max:
    #                     record.ph_nabl = 'pass'
    #                     break
    #                 else:
    #                     record.ph_nabl = 'fail'


    @api.depends('ph_average','eln_ref','grade')
    def _compute_ph_nabl(self):
        
        for record in self:
            record.ph_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','481fb826-5804-40f1-b7a1-54d435149afb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','481fb826-5804-40f1-b7a1-54d435149afb')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.ph_average - record.ph_average*mu_value
            upper = record.ph_average + record.ph_average*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.ph_nabl = 'pass'
                break
            else:
                record.ph_nabl = 'fail'


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

    average_dissolved_silica = fields.Float("Average",compute="_compute_average_dissolved_silica",digits=(16, 4))


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
    
    
    @api.depends('dissolved_silica_a','dissolved_silica_b','dissolved_silica_b')
    def _compute_average_dissolved_silica(self):
        for record in self:
            record.average_dissolved_silica = (record.dissolved_silica_a + record.dissolved_silica_b + record.dissolved_silica_c)/3

    @api.depends('wt_crucible_after_ignition_b','wt_crucible_after_hf_b')
    def _compute_diff_in_wt_of_silica_b(self):
        for record in self:
            record.diff_in_wt_of_silica_b = record.wt_crucible_after_ignition_b - record.wt_crucible_after_hf_b

    @api.depends('wt_crucible_after_ignition_c','wt_crucible_after_hf_c')
    def _compute_diff_in_wt_of_silica_c(self):
        for record in self:
            record.diff_in_wt_of_silica_c = record.wt_crucible_after_ignition_c - record.wt_crucible_after_hf_c

    dissolved_silica_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_dissolved_silica_conformity", store=True)

    @api.depends('average_dissolved_silica','eln_ref','grade')
    def _compute_dissolved_silica_conformity(self):
        
        for record in self:
            record.dissolved_silica_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a228b5d-5c83-4bb7-b6c7-2e7767b6181b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a228b5d-5c83-4bb7-b6c7-2e7767b6181b')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_dissolved_silica - record.average_dissolved_silica*mu_value
                    upper = record.average_dissolved_silica + record.average_dissolved_silica*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.dissolved_silica_conformity = 'pass'
                        break
                    else:
                        record.dissolved_silica_conformity = 'fail'

    dissolved_silica_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_dissolved_silica_nabl", store=True)

    # @api.depends('average_dissolved_silica','eln_ref','grade')
    # def _compute_dissolved_silica_nabl(self):
        
    #     for record in self:
    #         record.dissolved_silica_nabl = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a228b5d-5c83-4bb7-b6c7-2e7767b6181b')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a228b5d-5c83-4bb7-b6c7-2e7767b6181b')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 lab_min = line.lab_min_value
    #                 lab_max = line.lab_max_value
    #                 mu_value = line.mu_value
                    
    #                 lower = record.average_dissolved_silica - record.average_dissolved_silica*mu_value
    #                 upper = record.average_dissolved_silica + record.average_dissolved_silica*mu_value
    #                 if lower >= lab_min and upper <= lab_max:
    #                     record.dissolved_silica_nabl = 'pass'
    #                     break
    #                 else:
    #                     record.dissolved_silica_nabl = 'fail'

    @api.depends('average_dissolved_silica','eln_ref','grade')
    def _compute_dissolved_silica_nabl(self):
        
        for record in self:
            record.dissolved_silica_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a228b5d-5c83-4bb7-b6c7-2e7767b6181b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3a228b5d-5c83-4bb7-b6c7-2e7767b6181b')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_dissolved_silica - record.average_dissolved_silica*mu_value
            upper = record.average_dissolved_silica + record.average_dissolved_silica*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.dissolved_silica_nabl = 'pass'
                break
            else:
                record.dissolved_silica_nabl = 'fail'



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


    reduction_alkalinity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_reduction_alkalinity_conformity",  store=True)

    @api.depends('average_reduction_alkalinity','eln_ref','grade')
    def _compute_reduction_alkalinity_conformity(self):
        
        for record in self:
            record.reduction_alkalinity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98067b4a-3581-4712-b691-3df067e49a2c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98067b4a-3581-4712-b691-3df067e49a2c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_reduction_alkalinity - record.average_reduction_alkalinity*mu_value
                    upper = record.average_reduction_alkalinity + record.average_reduction_alkalinity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.reduction_alkalinity_conformity = 'pass'
                        break
                    else:
                        record.reduction_alkalinity_conformity = 'fail'

    reduction_alkalinity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_reduction_alkalinity_nabl",  store=True)

    # @api.depends('average_reduction_alkalinity','eln_ref','grade')
    # def _compute_reduction_alkalinity_nabl(self):
        
    #     for record in self:
    #         record.reduction_alkalinity_nabl = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98067b4a-3581-4712-b691-3df067e49a2c')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98067b4a-3581-4712-b691-3df067e49a2c')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 lab_min = line.lab_min_value
    #                 lab_max = line.lab_max_value
    #                 mu_value = line.mu_value
                    
    #                 lower = record.average_reduction_alkalinity - record.average_reduction_alkalinity*mu_value
    #                 upper = record.average_reduction_alkalinity + record.average_reduction_alkalinity*mu_value
    #                 if lower >= lab_min and upper <= lab_max:
    #                     record.reduction_alkalinity_nabl = 'pass'
    #                     break
    #                 else:
    #                     record.reduction_alkalinity_nabl = 'fail'

    @api.depends('average_reduction_alkalinity','eln_ref','grade')
    def _compute_reduction_alkalinity_nabl(self):
        
        for record in self:
            record.reduction_alkalinity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98067b4a-3581-4712-b691-3df067e49a2c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','98067b4a-3581-4712-b691-3df067e49a2c')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_reduction_alkalinity - record.average_reduction_alkalinity*mu_value
            upper = record.average_reduction_alkalinity + record.average_reduction_alkalinity*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.reduction_alkalinity_nabl = 'pass'
                break
            else:
                record.reduction_alkalinity_nabl = 'fail'




    #Chloride
    chloride_name = fields.Char("Name",default="Chloride")
    chloride_visible = fields.Boolean("Chloride",compute="_compute_visible")

    sample_wt_chloride = fields.Float("Sample Wt",digits=(16, 4))
    volume_make_upto_chloride = fields.Float("Volume make Upto")
    aliqote_taken_chloride = fields.Float("Aliqote taken")
    volume_silver_nitrate_added = fields.Float("Volume of silver nitrate added")
    volume_ammonia_blank = fields.Float("Volume of ammonia thiocynate for (Blank)")
    volume_ammonia_sample = fields.Float("Volume of ammonia thiocynate for (Sample)")
    # volume_ammonia_consumed = fields.Float("Volume of ammonia thiocynate consumed",compute="_compute_volume_ammonia_consumed")
    volume_ammonia_consumed = fields.Float("Volume of ammonia thiocynate consumed", compute="_compute_volume_ammonia_consumed", store=True)
    normality_of_ammonia = fields.Float("Normality of ammonia thiocynate (0.1)",digits=(16, 4))
    # chloride_percent = fields.Float("Chloride %",compute="_compute_chloride_percent",digits=(16, 4))
    chloride_percent = fields.Float("Chloride %", digits=(16, 4), compute="_compute_chloride_percent", store=True)

    # @api.depends('volume_ammonia_blank','volume_ammonia_blank')
    # def _compute_volume_ammonia_consumed(self):
    #     for record in self:
    #         record.volume_ammonia_consumed = record.volume_ammonia_blank - record.volume_ammonia_sample

    # Volume of ammonia consumed calculation
    @api.depends('volume_ammonia_blank', 'volume_ammonia_sample')
    def _compute_volume_ammonia_consumed(self):
        for record in self:
            record.volume_ammonia_consumed = record.volume_ammonia_blank - record.volume_ammonia_sample

    # @api.depends('volume_ammonia_consumed','normality_of_ammonia','aliqote_taken_chloride')
    # def _compute_chloride_percent(self):
    #     for record in self:
    #         if record.aliqote_taken_chloride != 0:
    #             record.chloride_percent = (record.volume_ammonia_consumed * record.normality_of_ammonia * 0.03545 * 100)/record.aliqote_taken_chloride
    #         else:
    #             record.chloride_percent = 0

    # Chloride percent calculation
    @api.depends('volume_ammonia_consumed', 'normality_of_ammonia', 'aliqote_taken_chloride')
    def _compute_chloride_percent(self):
        for record in self:
            if record.aliqote_taken_chloride != 0:
                record.chloride_percent = (record.volume_ammonia_consumed * record.normality_of_ammonia * 0.03545 * 100) / record.aliqote_taken_chloride
            else:
                record.chloride_percent = 0.0

    chloride_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_chloride_conformity", store=True)

    @api.depends('chloride_percent','eln_ref','grade')
    def _compute_chloride_conformity(self):
        
        for record in self:
            record.chloride_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','83c6e99e-d967-4162-8124-93fc8240ae24')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','83c6e99e-d967-4162-8124-93fc8240ae24')]).parameter_table
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

    # @api.depends('chloride_percent','eln_ref','grade')
    # def _compute_chloride_nabl(self):
        
    #     for record in self:
    #         record.chloride_nabl = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','83c6e99e-d967-4162-8124-93fc8240ae24')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','83c6e99e-d967-4162-8124-93fc8240ae24')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 lab_min = line.lab_min_value
    #                 lab_max = line.lab_max_value
    #                 mu_value = line.mu_value
                    
    #                 lower = record.chloride_percent - record.chloride_percent*mu_value
    #                 upper = record.chloride_percent + record.chloride_percent*mu_value
    #                 if lower >= lab_min and upper <= lab_max:
    #                     record.chloride_nabl = 'pass'
    #                     break
    #                 else:
    #                     record.chloride_nabl = 'fail'

    

    @api.depends('chloride_percent','eln_ref','grade')
    def _compute_chloride_nabl(self):
        
        for record in self:
            record.chloride_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','83c6e99e-d967-4162-8124-93fc8240ae24')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','83c6e99e-d967-4162-8124-93fc8240ae24')]).parameter_table
            
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





    #Sulphate
    sulphate_name = fields.Char("Name",default="Sulphate")
    sulphate_visible = fields.Boolean("Sulphate",compute="_compute_visible")


    sample_wt_sulphate = fields.Float("Sample Wt",digits=(16, 4))
    volume_make_upto_sulphate = fields.Float("Volume make Upto")
    aliqote_taken_sulphate = fields.Float("Aliqote taken")
    wt_empty_crucible_after_ignition = fields.Float("Wt. of empty crucible+residue after ignition",digits=(16, 4))
    wt_empty_crucible = fields.Float("Weight of empty crucible",digits=(16, 4))
    difference_in_wt_sulphate = fields.Float("Difference in Weight",compute="_compute_wt_difference_sulphate",digits=(16, 4))
    sulphate_percent = fields.Float("SO3 %",compute="_compute_sulphate_percent",digits=(16, 4))


    @api.depends('wt_empty_crucible_after_ignition','wt_empty_crucible')
    def _compute_wt_difference_sulphate(self):
        for record in self:
            record.difference_in_wt_sulphate = record.wt_empty_crucible_after_ignition - record.wt_empty_crucible

    @api.depends('difference_in_wt_sulphate')
    def _compute_sulphate_percent(self):
        for record in self:
            record.sulphate_percent = 2 * record.difference_in_wt_sulphate * 0.343

    sulphate_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_sulphate_conformity", store=True)

    @api.depends('sulphate_percent','eln_ref','grade')
    def _compute_sulphate_conformity(self):
        
        for record in self:
            record.sulphate_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8765b291-5596-4d10-9702-0e221e9379cd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8765b291-5596-4d10-9702-0e221e9379cd')]).parameter_table
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

    avrg_avrg_sulphate_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_avrg_avrg_sulphate_nabl",  store=True)

    # @api.depends('sulphate_percent','eln_ref','grade')
    # def _compute_avrg_avrg_sulphate_nabl(self):
        
    #     for record in self:
    #         record.avrg_avrg_sulphate_nabl = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8765b291-5596-4d10-9702-0e221e9379cd')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8765b291-5596-4d10-9702-0e221e9379cd')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 lab_min = line.lab_min_value
    #                 lab_max = line.lab_max_value
    #                 mu_value = line.mu_value
                    
    #                 lower = record.sulphate_percent - record.sulphate_percent*mu_value
    #                 upper = record.sulphate_percent + record.sulphate_percent*mu_value
    #                 if lower >= lab_min and upper <= lab_max:
    #                     record.avrg_avrg_sulphate_nabl = 'pass'
    #                     break
    #                 else:
    #                     record.avrg_avrg_sulphate_nabl = 'fail'

    @api.depends('sulphate_percent','eln_ref','grade')
    def _compute_avrg_avrg_sulphate_nabl(self):
        
        for record in self:
            record.avrg_avrg_sulphate_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8765b291-5596-4d10-9702-0e221e9379cd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8765b291-5596-4d10-9702-0e221e9379cd')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.sulphate_percent - record.sulphate_percent*mu_value
            upper = record.sulphate_percent + record.sulphate_percent*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avrg_avrg_sulphate_nabl = 'pass'
                break
            else:
                record.avrg_avrg_sulphate_nabl = 'fail'





     #Alkali as Na₂O Clause  4.11.4 ( By Flame Photometer)

    na2O_name = fields.Char("Name",default="Na₂O")
    na2O_name_visible = fields.Boolean("Na₂O",compute="_compute_visible")


    sample_wt_na2O = fields.Float("A)Weight of sample taken",digits=(16, 4))
    dilution_na2O = fields.Float("B)Dilution")
    sidium_reading_na2O = fields.Float("C)Sodium reading")
    factor_graph_na2O = fields.Float("D)Factor from graph",digits=(16, 4))
    dilution_reading_na2O = fields.Float("E)Dilution *Reading* factor *100/10000*wt of sample*A4",compute="_compute_dilution_reading_na2O",digits=(16, 2))
    na2O = fields.Float("F)Na *1.3480",compute="_compute_na2O_percent",digits=(16, 2))


    @api.depends('dilution_na2O', 'sidium_reading_na2O', 'factor_graph_na2O', 'sample_wt_na2O')
    def _compute_dilution_reading_na2O(self):
        for record in self:
            record.dilution_reading_na2O = (
                record.dilution_na2O
                * record.sidium_reading_na2O
                * record.factor_graph_na2O
                * 100
                / 10000
                * record.sample_wt_na2O
            )

    @api.depends('dilution_reading_na2O')
    def _compute_na2O_percent(self):
        for record in self:
            record.na2O = record.dilution_reading_na2O * 1.348




    



    

    na2O_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_na2O_conformity", store=True)

    @api.depends('na2O','eln_ref','grade')
    def _compute_na2O_conformity(self):
        
        for record in self:
            record.na2O_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3380972d-6290-4e34-aa61-6a707a4d788a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3380972d-6290-4e34-aa61-6a707a4d788a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.na2O - record.na2O*mu_value
                    upper = record.na2O + record.na2O*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.na2O_conformity = 'pass'
                        break
                    else:
                        record.na2O_conformity = 'fail'

    na2O_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_na2O_nabl",  store=True)

   
    @api.depends('na2O','eln_ref','grade')
    def _compute_na2O_nabl(self):
        
        for record in self:
            record.na2O_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3380972d-6290-4e34-aa61-6a707a4d788a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3380972d-6290-4e34-aa61-6a707a4d788a')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.na2O - record.na2O*mu_value
            upper = record.na2O + record.na2O*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.na2O_nabl = 'pass'
                break
            else:
                record.na2O_nabl = 'fail'


    # Alkali as K₂O Clause  4.11.4 ( By Flame Photometer)

    k2O_name = fields.Char("Name",default="K₂O")
    k2O_name_visible = fields.Boolean("K₂O",compute="_compute_visible")


    sample_wt_k2O = fields.Float("A)Weight of sample taken",digits=(16, 4))
    dilution_k2O = fields.Float("B)Dilution")
    sidium_reading_k2O = fields.Float("C)Potasium reading")
    factor_graph_k2O = fields.Float("D)Factor from graph",digits=(16, 4))
    dilution_reading_k2O = fields.Float("E)Dilution *Reading* factor *100/10000*wt of sample*A4",compute="_compute_dilution_reading_k2O",digits=(16, 2))
    k2O = fields.Float("F)K *1.20",compute="_compute_k2O_percent",digits=(16, 2))


    @api.depends('dilution_k2O', 'sidium_reading_k2O', 'factor_graph_k2O', 'sample_wt_k2O')
    def _compute_dilution_reading_k2O(self):
        for record in self:
            record.dilution_reading_k2O = (
                record.dilution_k2O
                * record.sidium_reading_k2O
                * record.factor_graph_k2O
                * 100
                / 10000
                * record.sample_wt_k2O
            )

    @api.depends('dilution_reading_k2O')
    def _compute_k2O_percent(self):
        for record in self:
            record.k2O = record.dilution_reading_k2O * 1.20

            


    



    

    k2O_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_k2O_conformity", store=True)

    @api.depends('k2O','eln_ref','grade')
    def _compute_k2O_conformity(self):
        
        for record in self:
            record.k2O_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ec3bb101-9088-4156-8af5-608a64fe4b7b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ec3bb101-9088-4156-8af5-608a64fe4b7b')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.k2O - record.k2O*mu_value
                    upper = record.k2O + record.k2O*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.k2O_conformity = 'pass'
                        break
                    else:
                        record.k2O_conformity = 'fail'

    k2O_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_k2O_nabl",  store=True)

   
    @api.depends('k2O','eln_ref','grade')
    def _compute_k2O_nabl(self):
        
        for record in self:
            record.k2O_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ec3bb101-9088-4156-8af5-608a64fe4b7b')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ec3bb101-9088-4156-8af5-608a64fe4b7b')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.k2O - record.k2O*mu_value
            upper = record.k2O + record.k2O*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.k2O_nabl = 'pass'
                break
            else:
                record.k2O_nabl = 'fail'






    total_alkali_content_name = fields.Char("Name",default="Total alkali content as Na2O")
    total_alkali_content_visible = fields.Boolean("equivalent, % ",compute="_compute_visible")

    total_alkali_content = fields.Float("Total Alkali Content (%)", compute="_compute_total_alkali_content", digits=(16, 2))

    @api.depends('na2O', 'k2O')
    def _compute_total_alkali_content(self):
        for record in self:
            record.total_alkali_content = record.na2O + 0.65 * record.k2O



    total_alkali_content_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity",compute="_compute_total_alkali_content_conformity", store=True)

    @api.depends('total_alkali_content','eln_ref','grade')
    def _compute_total_alkali_content_conformity(self):
        
        for record in self:
            record.total_alkali_content_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','338565ad-67d6-4795-880b-def72791b2c3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','338565ad-67d6-4795-880b-def72791b2c3')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.total_alkali_content - record.total_alkali_content*mu_value
                    upper = record.total_alkali_content + record.total_alkali_content*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.total_alkali_content_conformity = 'pass'
                        break
                    else:
                        record.total_alkali_content_conformity = 'fail'

    total_alkali_content_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL",compute="_compute_total_alkali_content_nabl",  store=True)

   
    @api.depends('total_alkali_content','eln_ref','grade')
    def _compute_total_alkali_content_nabl(self):
        
        for record in self:
            record.total_alkali_content_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','338565ad-67d6-4795-880b-def72791b2c3')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','338565ad-67d6-4795-880b-def72791b2c3')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.total_alkali_content - record.total_alkali_content*mu_value
            upper = record.total_alkali_content + record.total_alkali_content*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.total_alkali_content_nabl = 'pass'
                break
            else:
                record.total_alkali_content_nabl = 'fail'






    

    @api.depends('sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.chloride_visible = False
            record.sulphate_visible = False
            record.alkali_aggregate_alkalinity_visible = False
            record.ph_visible = False
            record.alkali_aggregate_dissolved_visible = False
            record.na2O_name_visible = False
            record.k2O_name_visible = False
            record.total_alkali_content_visible = False
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '481fb826-5804-40f1-b7a1-54d435149afb':
                    record.ph_visible = True
                if sample.internal_id == '83c6e99e-d967-4162-8124-93fc8240ae24':
                    record.chloride_visible = True
                if sample.internal_id == '8765b291-5596-4d10-9702-0e221e9379cd':
                    record.sulphate_visible = True
                if sample.internal_id == '98067b4a-3581-4712-b691-3df067e49a2c':
                    record.alkali_aggregate_alkalinity_visible = True
                if sample.internal_id == '3a228b5d-5c83-4bb7-b6c7-2e7767b6181b':
                    record.alkali_aggregate_dissolved_visible = True
                if sample.internal_id == '3380972d-6290-4e34-aa61-6a707a4d788a':
                    record.na2O_name_visible = True
                if sample.internal_id == 'ec3bb101-9088-4156-8af5-608a64fe4b7b':
                    record.k2O_name_visible = True
                if sample.internal_id == '338565ad-67d6-4795-880b-def72791b2c3':
                    record.total_alkali_content_visible = True
                    	



    def open_eln_page(self):
        # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            # ph 
            if result.parameter.internal_id == '481fb826-5804-40f1-b7a1-54d435149afb':
                result.result_char = round(self.ph_average,2)
                if self.ph_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            
            # Chloride
            if result.parameter.internal_id == '83c6e99e-d967-4162-8124-93fc8240ae24':
                result.result_char = round(self.chloride_percent,2)
                if self.chloride_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # Sulphate 
            if result.parameter.internal_id == '8765b291-5596-4d10-9702-0e221e9379cd':
                result.result_char = round(self.sulphate_percent,2)
                if self.avrg_avrg_sulphate_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # Alkali Aggregate
            if result.parameter.internal_id == '98067b4a-3581-4712-b691-3df067e49a2c':
                result.result_char = round(self.average_reduction_alkalinity,2)
                if self.reduction_alkalinity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            # Alkali Dissolved
            if result.parameter.internal_id == '3a228b5d-5c83-4bb7-b6c7-2e7767b6181b':
                result.result_char = round(self.average_dissolved_silica,2)
                if self.dissolved_silica_nabl == 'pass':
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
        record = super(ChemicalCrushedSand, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


        
    def get_all_fields(self):
        record = self.env['chemical.crushed.sand'].browse(self.ids[0])
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
    