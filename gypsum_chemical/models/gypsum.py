from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class ChemicalGyspum(models.Model):
    _name = "chemical.gyspum"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Gyspum")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)


    # %Sulphur trioxide (SO3)
    so3_name = fields.Char("Name", default="SO3")
    so3_visible = fields.Boolean("SO3", compute="_compute_visible")

    plaster1 = fields.Char(string="Plaster Of Paris",default="35 Min")
    retarded1 = fields.Char(string="Retarded Hemihydrate Gypsum Plaster",default="35 Min")
    anhydrous1 = fields.Char(string="Anhydrous Gypsum Plaster",default="40 Min")
    keenes1 = fields.Char(string="Keene's Plaster",default="47 Min")

    wt_of_sample_so3 = fields.Float("A) Wt of Sample (gm)",digits=(16, 4))
    wt_cr_so3 = fields.Float("B) Wt of crucible +Residue after ignition (gm)",digits=(16, 4))
    wt_empty_co3 = fields.Float("C) Wt of empty crucible (gm)",digits=(16, 4))
    difference_co3 = fields.Float("D)Diff. in weight(gm)=( B - C )",compute="_compute_difference_co3",digits=(12,4))
    so3 = fields.Float("SO3  % =  D x 34.30  / A",compute="_compute_so3",digits=(12,3))

    @api.depends('wt_cr_so3', 'wt_empty_co3')
    def _compute_difference_co3(self):
        for record in self:
            record.difference_co3 = record.wt_cr_so3 - record.wt_empty_co3

    @api.depends('difference_co3', 'wt_of_sample_so3')
    def _compute_so3(self):
        for record in self:
              if self.wt_of_sample_so3 != 0:
                 self.so3 = self.difference_co3 * 34.30 / self.wt_of_sample_so3
              else:
                self.so3 = 0.0

  
    so3_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_so3_conformity", store=True)

    @api.depends('so3','eln_ref','grade')
    def _compute_so3_conformity(self):
        
        for record in self:
            record.so3_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a58cb5bc-d2d2-4756-81d2-6571ae81a813')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a58cb5bc-d2d2-4756-81d2-6571ae81a813')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.so3 - record.so3*mu_value
                    upper = record.so3 + record.so3*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.so3_conformity = 'pass'
                        break
                    else:
                        record.so3_conformity = 'fail'

    so3_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_so3_nabl", store=True)

    @api.depends('so3','eln_ref','grade')
    def _compute_so3_nabl(self):
        
        for record in self:
            record.so3_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a58cb5bc-d2d2-4756-81d2-6571ae81a813')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a58cb5bc-d2d2-4756-81d2-6571ae81a813')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.so3 - record.so3*mu_value
                    upper = record.so3 + record.so3*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.so3_nabl = 'pass'
                        break
                    else:
                        record.so3_nabl = 'fail'


       # %Loss on Ignition
    loi_name = fields.Char("Name", default="Loss on Ignition")
    loi_visible = fields.Boolean("Loss on Ignition", compute="_compute_visible")

    plaster2 = fields.Char(string="Plaster Of Paris",default="Not gerater than 9 and less than 4")
    retarded2 = fields.Char(string="Retarded Hemihydrate Gypsum Plaster",default="Not gerater than 9 and less than 4")
    anhydrous2 = fields.Char(string="Anhydrous Gypsum Plaster",default="3.0 Max")
    keenes2 = fields.Char(string="Keene's Plaster",default="2.0 Max")

    wt_of_empty_loi = fields.Float("A) Wt of empty weighing bottle (gm)",digits=(16, 4))
    wt_empty_cs_loi = fields.Float("B) (Wt of empty weighing bottle + Sample) before ignition, gm",digits=(16, 4))
    wt_cs_loi = fields.Float("C) Wt.of sample (B-A) ( gm )", compute="_compute_wt_cs_loi", store=True,digits=(16, 4))
    wt_of_sample_loi = fields.Float("D) (Wt of empty weighing bottle + Sample) after ignition, (gm)",digits=(16, 4))
    loi_in_wt = fields.Float("E) Diff. in weight = (B - D), gm", compute="_compute_loi_in_wt", store=True,digits=(16, 4))
    loi = fields.Float("LOI % = E x 100 / C", compute="_compute_loi", store=True)

    @api.depends('wt_empty_cs_loi', 'wt_of_empty_loi')
    def _compute_wt_cs_loi(self):
        for record in self:
            record.wt_cs_loi = record.wt_empty_cs_loi - record.wt_of_empty_loi

    @api.depends('wt_empty_cs_loi', 'wt_of_sample_loi')
    def _compute_loi_in_wt(self):
        for record in self:
            record.loi_in_wt = record.wt_empty_cs_loi - record.wt_of_sample_loi

    @api.depends('wt_cs_loi', 'loi_in_wt')
    def _compute_loi(self):
        for record in self:
            if record.wt_cs_loi != 0:
                record.loi = (record.loi_in_wt * 100) / record.wt_cs_loi
            else:
                record.loi = 0.0
  



    loss_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_loss_conformity", store=True)

    @api.depends('loi','eln_ref','grade')
    def _compute_loss_conformity(self):
        
        for record in self:
            record.loss_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','df12ceda-8e7d-4cb0-af54-0561796f5fdf')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','df12ceda-8e7d-4cb0-af54-0561796f5fdf')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.loi - record.loi*mu_value
                    upper = record.loi + record.loi*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.loss_conformity = 'pass'
                        break
                    else:
                        record.loss_conformity = 'fail'

    loss_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_loss_nabl", store=True)

    @api.depends('loi','eln_ref','grade')
    def _compute_loss_nabl(self):
        
        for record in self:
            record.loss_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','df12ceda-8e7d-4cb0-af54-0561796f5fdf')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','df12ceda-8e7d-4cb0-af54-0561796f5fdf')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.loi - record.loi*mu_value
                    upper = record.loi + record.loi*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.loss_nabl = 'pass'
                        break
                    else:
                        record.loss_nabl = 'fail'




     # CaO

    
    cao_name = fields.Char("Name",default="CaO")
    cao_visible = fields.Boolean("CaO",compute="_compute_visible")

    plaster3 = fields.Char(string="Plaster Of Paris",default="2/3 of SO3 content")
    retarded3 = fields.Char(string="Retarded Hemihydrate Gypsum Plaster",default="2/3 of SO3 content")
    anhydrous3 = fields.Char(string="Anhydrous Gypsum Plaster",default="2/3 of SO3 content")
    keenes3 = fields.Char(string="Keene's Plaster",default="2/3 of SO3 content")

    wt_of_sample_cao1 = fields.Float("A) Wt of Sample (gm)",digits=(16, 4))
    burette_cao1  = fields.Float("B) Burrette reading (ml)")
    normality_cao1 = fields.Float("C) Normality of 0.1N KMnO₄")
    cao1 = fields.Float("CaO  % = B x C x 11.22/ A",compute="_compute_cao1")

    @api.depends('burette_cao1', 'normality_cao1', 'wt_of_sample_cao1')
    def _compute_cao1(self):
        for record in self:
            if record.wt_of_sample_cao1 != 0:
                record.cao1 = (record.burette_cao1 * record.normality_cao1 * 11.22) / record.wt_of_sample_cao1
            else:
                record.cao1 = 0.0


   


    cao1_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_cao1_conformity", store=True)

    @api.depends('cao1','eln_ref','grade')
    def _compute_cao1_conformity(self):
        
        for record in self:
            record.cao1_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','80cbb8c4-5b52-4c0b-97f8-b5b66af79982')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','80cbb8c4-5b52-4c0b-97f8-b5b66af79982')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.cao1 - record.cao1*mu_value
                    upper = record.cao1 + record.cao1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.cao1_conformity = 'pass'
                        break
                    else:
                        record.cao1_conformity = 'fail'

    cao1_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_cao1_nabl", store=True)

    @api.depends('cao1','eln_ref','grade')
    def _compute_cao1_nabl(self):
        
        for record in self:
            record.cao1_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','80cbb8c4-5b52-4c0b-97f8-b5b66af79982')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','80cbb8c4-5b52-4c0b-97f8-b5b66af79982')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.cao1 - record.cao1*mu_value
                    upper = record.cao1 + record.cao1*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.cao1_nabl = 'pass'
                        break
                    else:
                        record.cao1_nabl = 'fail'


    

     # MgO
    mgo_name = fields.Char("Name",default="MgO")
    mgo_visible = fields.Boolean("MgO",compute="_compute_visible")

    plaster4= fields.Char(string="Plaster Of Paris",default="0.3 Max")
    retarded4 = fields.Char(string="Retarded Hemihydrate Gypsum Plaster",default="0.3 Max")
    anhydrous4 = fields.Char(string="Anhydrous Gypsum Plaster",default="0.3 Max")
    keenes4 = fields.Char(string="Keene's Plaster",default="0.3 Max")


    wt_of_sample_mgo1 = fields.Float("A) Wt of Sample (gm)",digits=(16, 4))
    burette_mgo1 = fields.Float("B) Wt of crucible + Residue after ignition (gm)")
    normality_mgo1 = fields.Float("C) Wt of empty Cruible (gm)")
    dilution_mgo1 = fields.Float("D) Diff. in weight (gm)", compute="_compute_dilution_mgo1",digits=(16,4), store=True)
    dilution_mgo2 = fields.Float("Dilution")
    mgo1 = fields.Float("MgO % = D x 36.21/ A", compute="_compute_mgo1", store=True)

    @api.depends('burette_mgo1', 'normality_mgo1')
    def _compute_dilution_mgo1(self):
        for record in self:
            record.dilution_mgo1 = record.burette_mgo1 - record.normality_mgo1

    @api.depends('dilution_mgo1', 'wt_of_sample_mgo1' , 'dilution_mgo2')
    def _compute_mgo1(self):
        for record in self:
            if record.wt_of_sample_mgo1 != 0:
                record.mgo1 = (record.dilution_mgo1 * 36.21 * record.dilution_mgo2) / record.wt_of_sample_mgo1
            else:
                record.mgo1 = 0.0

  
    mgo_conformity1 = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_mgo_conformity1", store=True)

    @api.depends('mgo1','eln_ref','grade')
    def _compute_mgo_conformity1(self):
        
        for record in self:
            record.mgo_conformity1 = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ef8ce36-8db8-4557-ad95-14b199bc9ff0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ef8ce36-8db8-4557-ad95-14b199bc9ff0')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.mgo1 - record.mgo1*mu_value
                    upper = record.mgo1 + record.mgo1*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.mgo_conformity1 = 'pass'
                        break
                    else:
                        record.mgo_conformity1 = 'fail'

    mgo_nabl1 = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_mgo_nabl1", store=True)

    @api.depends('mgo1','eln_ref','grade')
    def _compute_mgo_nabl1(self):
        
        for record in self:
            record.mgo_nabl1 = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ef8ce36-8db8-4557-ad95-14b199bc9ff0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ef8ce36-8db8-4557-ad95-14b199bc9ff0')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.mgo1 - record.mgo1*mu_value
                    upper = record.mgo1 + record.mgo1*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.mgo_nabl1 = 'pass'
                        break
                    else:
                        record.mgo_nabl1 = 'fail'



     # CaO2

    
    cao_name2 = fields.Char("Name",default="CaO")
    cao_visible2 = fields.Boolean("CaO",compute="_compute_visible")

    plaster5= fields.Char(string="Plaster Of Paris",default="--")
    retarded5 = fields.Char(string="Retarded Hemihydrate Gypsum Plaster",default="--")
    anhydrous5 = fields.Char(string="Anhydrous Gypsum Plaster",default="--")
    keenes5 = fields.Char(string="Keene's Plaster",default="--")


    wt_of_sample_cao2 = fields.Float("A) Wt of Sample (gm)",digits=(16, 4))
    burette_cao2 = fields.Float("B) BR of 0.01N EDTA")
    normality_cao2 = fields.Float("C) Normality OF EDTA")
    dilution_cao2 = fields.Float("D) Dilution")
    cao2 = fields.Float("E) BR *0.05608*N*100*dilution/S.wt", compute="_compute_cao2", store=True)

    @api.depends('burette_cao2', 'normality_cao2', 'dilution_cao2', 'wt_of_sample_cao2')
    def _compute_cao2(self):
        for record in self:
            if record.wt_of_sample_cao2 != 0:
                record.cao2 = (record.burette_cao2 * record.normality_cao2 * 0.05608 * record.dilution_cao2 * 100) / record.wt_of_sample_cao2
            else:
                record.cao2 = 0.0

   

    cao_conformity2 = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_cao_conformity2", store=True)

    @api.depends('cao2','eln_ref','grade')
    def _compute_cao_conformity2(self):
        
        for record in self:
            record.cao_conformity2 = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','abc60d60-0e94-4a2a-a08f-04650534fa9f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','abc60d60-0e94-4a2a-a08f-04650534fa9f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.cao2 - record.cao2*mu_value
                    upper = record.cao2 + record.cao2*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.cao_conformity2 = 'pass'
                        break
                    else:
                        record.cao_conformity2 = 'fail'

    cao_nabl2 = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_cao_nabl2", store=True)

    @api.depends('cao2','eln_ref','grade')
    def _compute_cao_nabl2(self):
        
        for record in self:
            record.cao_nabl2 = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','abc60d60-0e94-4a2a-a08f-04650534fa9f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','abc60d60-0e94-4a2a-a08f-04650534fa9f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.cao2 - record.cao2*mu_value
                    upper = record.cao2 + record.cao2*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.cao_nabl2 = 'pass'
                        break
                    else:
                        record.cao_nabl2 = 'fail'


     # MgO2
    mgo_name2 = fields.Char("Name",default="MgO")
    mgo_visible2 = fields.Boolean("MgO",compute="_compute_visible")

    plaster6= fields.Char(string="Plaster Of Paris",default="--")
    retarded6 = fields.Char(string="Retarded Hemihydrate Gypsum Plaster",default="--")
    anhydrous6 = fields.Char(string="Anhydrous Gypsum Plaster",default="--")
    keenes6 = fields.Char(string="Keene's Plaster",default="--")


    wt_of_sample_mgo2 = fields.Float("A) Wt of Sample (gm)",digits=(16, 4))
    burette_mgo2 = fields.Float("B) BR of 0.01N CaO - BR of 0.01N EDTA")
    normality_mgo2 = fields.Float("C) Normality of EDTA")
    dilution_mgo2 = fields.Float("D) Dilution")
    mgo2 = fields.Float("MgO = BR * N * 0.04032 * 25 * 100 / S.w", compute="_compute_mgo2", store=True)

    @api.depends('burette_mgo2', 'normality_mgo2', 'dilution_mgo2', 'wt_of_sample_mgo2')
    def _compute_mgo2(self):
        for record in self:
            if record.wt_of_sample_mgo2 != 0:
                record.mgo2 = (record.burette_mgo2 * record.normality_mgo2 * 0.04032 * record.dilution_mgo2 * 100) / record.wt_of_sample_mgo2
            else:
                record.mgo2 = 0.0
   

  
    mgo_conformity2 = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_mgo_conformity2", store=True)

    @api.depends('mgo2','eln_ref','grade')
    def _compute_mgo_conformity2(self):
        
        for record in self:
            record.mgo_conformity2 = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b3b623fc-ff8b-44b8-884b-869139ff0912')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b3b623fc-ff8b-44b8-884b-869139ff0912')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.mgo2 - record.mgo2*mu_value
                    upper = record.mgo2 + record.mgo2*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.mgo_conformity2 = 'pass'
                        break
                    else:
                        record.mgo_conformity2 = 'fail'

    mgo_nabl2 = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_mgo_nabl2", store=True)

    @api.depends('mgo2','eln_ref','grade')
    def _compute_mgo_nabl2(self):
        
        for record in self:
            record.mgo_nabl2 = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b3b623fc-ff8b-44b8-884b-869139ff0912')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b3b623fc-ff8b-44b8-884b-869139ff0912')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.mgo2 - record.mgo2*mu_value
                    upper = record.mgo2 + record.mgo2*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.mgo_nabl2 = 'pass'
                        break
                    else:
                        record.mgo_nabl2 = 'fail'




      # Free Lime
    free_lime_name = fields.Char("Name",default="Free Lime")
    free_lime_visible = fields.Boolean("Free Lime",compute="_compute_visible")

    plaster7= fields.Char(string="Plaster Of Paris",default="--")
    retarded7 = fields.Char(string="Retarded Hemihydrate Gypsum Plaster",default="3 Min")
    anhydrous7 = fields.Char(string="Anhydrous Gypsum Plaster",default="--")
    keenes7 = fields.Char(string="Keene's Plaster",default="--")


    free_lime_wt = fields.Float("A) Wt.of sample (gm)",digits=(16, 4))
    free_lime_br = fields.Float("B) Burette reading (ml)")
    free_lime_nor = fields.Float("C) Normality of 0.5N HCL")
    free_lime = fields.Float("Free lime % = B x C x 0.0037 x 100/ A", compute="_compute_free_lime",digits=(16,3), store=True)

    @api.depends('free_lime_br', 'free_lime_nor', 'free_lime_wt')
    def _compute_free_lime(self):
        for record in self:
            if record.free_lime_wt != 0:
                record.free_lime = (record.free_lime_br * record.free_lime_nor * 0.0037 * 100) / record.free_lime_wt
            else:
                record.free_lime = 0.0
  
  
    free_lime_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_free_lime_conformity", store=True)

    @api.depends('free_lime','eln_ref','grade')
    def _compute_free_lime_conformity(self):
        
        for record in self:
            record.free_lime_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1959c613-48ed-494d-93a3-b4c831e37b51')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1959c613-48ed-494d-93a3-b4c831e37b51')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.free_lime - record.free_lime*mu_value
                    upper = record.free_lime + record.free_lime*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.free_lime_conformity = 'pass'
                        break
                    else:
                        record.free_lime_conformity = 'fail'

    free_lime_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_free_lime_nabl_nabl", store=True)

    @api.depends('free_lime','eln_ref','grade')
    def _compute_free_lime_nabl_nabl(self):
        
        for record in self:
            record.free_lime_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1959c613-48ed-494d-93a3-b4c831e37b51')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1959c613-48ed-494d-93a3-b4c831e37b51')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.free_lime - record.free_lime*mu_value
                    upper = record.free_lime + record.free_lime*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.free_lime_nabl = 'pass'
                        break
                    else:
                        record.free_lime_nabl = 'fail'




       # Soluble sodium oxide ( By Flame photo meter )

    soluble_sodium_name = fields.Char("Name",default="Soluble sodium oxide ( By Flame photo meter )")
    soluble_sodium_visible = fields.Boolean("Soluble sodium oxide ( By Flame photo meter )",compute="_compute_visible")

    plaster8= fields.Char(string="Plaster Of Paris",default="0.3 Max")
    retarded8 = fields.Char(string="Retarded Hemihydrate Gypsum Plaster",default="0.3 Max")
    anhydrous8 = fields.Char(string="Anhydrous Gypsum Plaster",default="0.3 Max")
    keenes8 = fields.Char(string="Keene's Plaster",default="0.3 Max")


    soluble_sodium_wt = fields.Float("A) Wt.of sample (gm)",digits=(16, 4))
    soluble_sodium_re = fields.Float("B) Reading")
    soluble_sodium_fa = fields.Float("C) Factor")
    soluble_sodium = fields.Float("Soluble sodium oxide % (Na2O)", compute="_compute_soluble_sodium", store=True ,digits=(16, 3))

    @api.depends('soluble_sodium_wt', 'soluble_sodium_re', 'soluble_sodium_fa')
    def _compute_soluble_sodium(self):
        for record in self:
            if record.soluble_sodium_wt != 0:
                record.soluble_sodium = ((record.soluble_sodium_re * record.soluble_sodium_fa * 100) / (10000 * record.soluble_sodium_wt)) * 1.348
            else:
                record.soluble_sodium = 0.0
 
 
  
    soluble_sodium_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_soluble_sodium_conformity", store=True)

    @api.depends('soluble_sodium','eln_ref','grade')
    def _compute_soluble_sodium_conformity(self):
        
        for record in self:
            record.soluble_sodium_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e54abac7-52ff-41a2-8ef1-cd536cde4e2d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e54abac7-52ff-41a2-8ef1-cd536cde4e2d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.soluble_sodium - record.soluble_sodium*mu_value
                    upper = record.soluble_sodium + record.soluble_sodium*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.soluble_sodium_conformity = 'pass'
                        break
                    else:
                        record.soluble_sodium_conformity = 'fail'

    soluble_sodium_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_soluble_sodium_nabl_nabl", store=True)

    @api.depends('soluble_sodium','eln_ref','grade')
    def _compute_soluble_sodium_nabl_nabl(self):
        
        for record in self:
            record.soluble_sodium_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e54abac7-52ff-41a2-8ef1-cd536cde4e2d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e54abac7-52ff-41a2-8ef1-cd536cde4e2d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.soluble_sodium - record.soluble_sodium*mu_value
                    upper = record.soluble_sodium + record.soluble_sodium*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.soluble_sodium_nabl = 'pass'
                        break
                    else:
                        record.soluble_sodium_nabl = 'fail'



       # Free Water
    free_water_name = fields.Char("Name",default="Free Water")
    free_water_visible = fields.Boolean("Free Water",compute="_compute_visible")

    plaster9= fields.Char(string="Plaster Of Paris",default="--")
    retarded9 = fields.Char(string="Retarded Hemihydrate Gypsum Plaster",default="--")
    anhydrous9 = fields.Char(string="Anhydrous Gypsum Plaster",default="--")
    keenes9 = fields.Char(string="Keene's Plaster",default="--")



    wt_of_empty_water = fields.Float("A) Wt of empty weighing bottle (gm)",digits=(16, 4))
    wt_empty_cs_water = fields.Float("B) (Wt of empty weighing bottle + Sample) before ignition, gm",digits=(16, 4))
    wt_cs_water = fields.Float("C) Wt.of sample (B-A) ( gm )", compute="_compute_wt_cs_water", store=True,digits=(16, 4))
    wt_of_sample_water = fields.Float("D) (Wt of empty weighing bottle + Sample) after ignition, (gm)",digits=(16, 4))
    water_in_wt = fields.Float("E) Diff. in weight = (B - D), gm", compute="_compute_water_in_wt", store=True,digits=(16, 4))
    free_water = fields.Float("Free water = E x 100 / C", compute="_compute_water", store=True)

    @api.depends('wt_empty_cs_water', 'wt_of_empty_water')
    def _compute_wt_cs_water(self):
        for record in self:
            record.wt_cs_water = record.wt_empty_cs_water - record.wt_of_empty_water

    @api.depends('wt_empty_cs_water', 'wt_of_sample_water')
    def _compute_water_in_wt(self):
        for record in self:
            record.water_in_wt = record.wt_empty_cs_water - record.wt_of_sample_water

    @api.depends('wt_cs_water', 'water_in_wt')
    def _compute_water(self):
        for record in self:
            if record.wt_cs_water != 0:
                record.free_water = (record.water_in_wt * 100) / record.wt_cs_water
            else:
                record.free_water = 0.0
  


    # free_water_wt = fields.Float("Mass of sample",digits=(16, 4))
    # free_water_br = fields.Float("Mass in gm of the material after drying")
    # free_water_nor = fields.Float("Diff", compute="_compute_free_water_nor", store=True)
    # free_water = fields.Float("Free water = diff * 100 / Mass", compute="_compute_free_water", store=True)

    # @api.depends('free_water_wt', 'free_water_br')
    # def _compute_free_water_nor(self):
    #     for record in self:
    #         record.free_water_nor = record.free_water_wt - record.free_water_br

    # @api.depends('free_water_nor', 'free_water_wt')
    # def _compute_free_water(self):
    #     for record in self:
    #         if record.free_water_wt != 0:
    #             record.free_water = (record.free_water_nor * 100) / record.free_water_wt
    #         else:
    #             record.free_water = 0.0
   
  
  
    free_water_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_free_water_conformity", store=True)

    @api.depends('free_water','eln_ref','grade')
    def _compute_free_water_conformity(self):
        
        for record in self:
            record.free_water_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c3ac1330-a4d9-4526-9533-4130ff635bf6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c3ac1330-a4d9-4526-9533-4130ff635bf6')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.free_water - record.free_water*mu_value
                    upper = record.free_water + record.free_water*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.free_water_conformity = 'pass'
                        break
                    else:
                        record.free_water_conformity = 'fail'

    free_water_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_free_water_nabl_nabl", store=True)

    @api.depends('free_water','eln_ref','grade')
    def _compute_free_water_nabl_nabl(self):
        
        for record in self:
            record.free_water_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c3ac1330-a4d9-4526-9533-4130ff635bf6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c3ac1330-a4d9-4526-9533-4130ff635bf6')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.free_water - record.free_water*mu_value
                    upper = record.free_water + record.free_water*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.free_water_nabl = 'pass'
                        break
                    else:
                        record.free_water_nabl = 'fail'



        # Combined Water
    combined_water_name = fields.Char("Name",default="Combined Water")
    combined_water_visible = fields.Boolean("Combined Water",compute="_compute_visible")

    plaster10= fields.Char(string="Plaster Of Paris",default="--")
    retarded10 = fields.Char(string="Retarded Hemihydrate Gypsum Plaster",default="--")
    anhydrous10 = fields.Char(string="Anhydrous Gypsum Plaster",default="--")
    keenes10 = fields.Char(string="Keene's Plaster",default="--")


    combined_water_wt = fields.Float("Mass of prepared sample",digits=(16, 4))
    combined_water_br = fields.Float("Mass in gm of the material before drying")
    combined_water_nor = fields.Float("Mass in gm of the material after drying")
    combined_water_di = fields.Float("Diff", compute="_compute_combined_water_di",digits=(16,3), store=True)
    combined_water = fields.Float("Combined Water", compute="_compute_combined_water",digits=(16,4), store=True)

    @api.depends('combined_water_br', 'combined_water_nor')
    def _compute_combined_water_di(self):
        for record in self:
            record.combined_water_di = record.combined_water_br - record.combined_water_nor

    @api.depends('combined_water_di', 'combined_water_wt')
    def _compute_combined_water(self):
        for record in self:
            if record.combined_water_wt != 0:
                record.combined_water = (record.combined_water_di * 100) / record.combined_water_wt
            else:
                record.combined_water = 0.0
  
  
  
    combined_water_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_combined_water_conformity", store=True)

    @api.depends('combined_water','eln_ref','grade')
    def _compute_combined_water_conformity(self):
        
        for record in self:
            record.combined_water_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1afa0443-8649-48a3-b73e-49f9fbb08d3d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1afa0443-8649-48a3-b73e-49f9fbb08d3d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.combined_water - record.combined_water*mu_value
                    upper = record.combined_water + record.combined_water*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.combined_water_conformity = 'pass'
                        break
                    else:
                        record.combined_water_conformity = 'fail'

    combined_water_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_combined_water_nabl_nabl", store=True)

    @api.depends('combined_water','eln_ref','grade')
    def _compute_combined_water_nabl_nabl(self):
        
        for record in self:
            record.combined_water_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1afa0443-8649-48a3-b73e-49f9fbb08d3d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1afa0443-8649-48a3-b73e-49f9fbb08d3d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.combined_water - record.combined_water*mu_value
                    upper = record.combined_water + record.combined_water*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.combined_water_nabl = 'pass'
                        break
                    else:
                        record.combined_water_nabl = 'fail'



     # CaO2

    
    calcium_oxide_name = fields.Char("Name",default="Calcium Oxide")
    calcium_oxide_visible2 = fields.Boolean("CaO",compute="_compute_visible")

    plaster11= fields.Char(string="Plaster Of Paris",default="--")
    retarded11 = fields.Char(string="Retarded Hemihydrate Gypsum Plaster",default="--")
    anhydrous11 = fields.Char(string="Anhydrous Gypsum Plaster",default="--")
    keenes11 = fields.Char(string="Keene's Plaster",default="--")


    wt_of_sample_calcium_oxide = fields.Float("A) Wt of Sample (gm)",digits=(16, 4))
    burette_calcium_oxide = fields.Float("B) Burrette reading" ,digits=(16, 4))
    normality_calcium_oxide = fields.Float("C) Normality of 0.1N KMnO4" ,digits=(16, 4))
    dilution_calcium_oxide = fields.Float("D) Dilution")
    calcium_oxide = fields.Float("Calcium Oxide = B*C*2.8*D/A", compute="_compute_calcium_oxide", store=True)

    @api.depends('burette_calcium_oxide', 'normality_calcium_oxide', 'dilution_calcium_oxide', 'wt_of_sample_calcium_oxide')
    def _compute_calcium_oxide(self):
        for record in self:
            if record.wt_of_sample_calcium_oxide != 0:
                record.calcium_oxide = (record.burette_calcium_oxide * record.normality_calcium_oxide * 2.8 * record.dilution_calcium_oxide) / record.wt_of_sample_calcium_oxide
            else:
                record.calcium_oxide = 0.0

   

    calcium_oxide_conformity2 = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_calcium_oxide_conformity2", store=True)

    @api.depends('calcium_oxide','eln_ref','grade')
    def _compute_calcium_oxide_conformity2(self):
        
        for record in self:
            record.calcium_oxide_conformity2 = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','966341bc-cef0-49da-8f72-df520a8c702e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','966341bc-cef0-49da-8f72-df520a8c702e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.calcium_oxide - record.calcium_oxide*mu_value
                    upper = record.calcium_oxide + record.calcium_oxide*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.calcium_oxide_conformity2 = 'pass'
                        break
                    else:
                        record.calcium_oxide_conformity2 = 'fail'

    calcium_oxide_nabl2 = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_calcium_oxide_nabl", store=True)

    @api.depends('calcium_oxide','eln_ref','grade')
    def _compute_calcium_oxide_nabl(self):
        
        for record in self:
            record.calcium_oxide_nabl2 = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','966341bc-cef0-49da-8f72-df520a8c702e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','966341bc-cef0-49da-8f72-df520a8c702e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.calcium_oxide - record.calcium_oxide*mu_value
                    upper = record.calcium_oxide + record.calcium_oxide*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.calcium_oxide_nabl2 = 'pass'
                        break
                    else:
                        record.calcium_oxide_nabl2 = 'fail'















  
          

   




    @api.depends('sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.so3_visible = False
            record.loi_visible = False
            record.cao_visible = False
            record.mgo_visible = False
            record.cao_visible2 = False
            record.mgo_visible2 = False
            record.free_lime_visible = False
            record.soluble_sodium_visible = False
            record.free_water_visible = False
            record.combined_water_visible = False
            record.calcium_oxide_visible2 = False
         
           
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == 'a58cb5bc-d2d2-4756-81d2-6571ae81a813':
                    record.so3_visible = True
                if sample.internal_id == 'df12ceda-8e7d-4cb0-af54-0561796f5fdf':
                    record.loi_visible = True
                if sample.internal_id == '80cbb8c4-5b52-4c0b-97f8-b5b66af79982':
                    record.cao_visible = True

                if sample.internal_id == '3ef8ce36-8db8-4557-ad95-14b199bc9ff0':
                    record.mgo_visible = True
                
                if sample.internal_id == 'abc60d60-0e94-4a2a-a08f-04650534fa9f':
                    record.cao_visible2 = True
                if sample.internal_id == 'b3b623fc-ff8b-44b8-884b-869139ff0912':
                    record.mgo_visible2 = True
                if sample.internal_id == '1959c613-48ed-494d-93a3-b4c831e37b51':
                    record.free_lime_visible = True
                if sample.internal_id == 'e54abac7-52ff-41a2-8ef1-cd536cde4e2d':
                    record.soluble_sodium_visible = True
                if sample.internal_id == 'c3ac1330-a4d9-4526-9533-4130ff635bf6':
                    record.free_water_visible = True
                if sample.internal_id == '1afa0443-8649-48a3-b73e-49f9fbb08d3d':
                    record.combined_water_visible = True
                if sample.internal_id == '966341bc-cef0-49da-8f72-df520a8c702e':
                    record.calcium_oxide_visible2 = True






   
               

    
          

    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(ChemicalGyspum, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


        
    def get_all_fields(self):
        record = self.env['chemical.gyspum'].browse(self.ids[0])
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
    

