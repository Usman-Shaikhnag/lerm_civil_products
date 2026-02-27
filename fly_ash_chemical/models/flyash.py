from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math


class ChemicalFlyAsh(models.Model):
    _name = "chemical.flyash"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Fly Ash")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)


    # % Silica

    Silica_name = fields.Char("Name",default="% Silica")
    Silica_visible = fields.Boolean("% Silica",compute="_compute_visible")

    siliceous1 = fields.Char(string="Siliceous Pulverized Fuel Ash",default="35.0 Min")
    calcareous1 = fields.Char(string="Calcareous Pulverized Fuel Ash",default="25.0 Min")

    wt_of_sample = fields.Float("Wt of sample taken W1 (gm)",digits=(16, 4))
    wt_of_two_rp = fields.Float("Wt of two residue and paper after ignition at 1100˚C in crucible gm",digits=(16, 4))
    wt_of_two_r = fields.Float("Weight of residues in crucible after HF at 1100˚C gm",digits=(16, 4))
    difference_in_wt = fields.Float("Difference in weight = ( B - C )",compute="_compute_difference_in_wt",digits=(16, 4))
    Silica = fields.Float("SiO₂ = D x 100/A",compute="_compute_silica_percentage")

    Silica_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_Silica_conformity", store=True)

    @api.depends('Silica','eln_ref','grade')
    def _compute_Silica_conformity(self):
        
        for record in self:
            record.Silica_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6b064931-b820-44dd-a096-99c2666bd191')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6b064931-b820-44dd-a096-99c2666bd191')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.Silica - record.Silica*mu_value
                    upper = record.Silica + record.Silica*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.Silica_conformity = 'pass'
                        break
                    else:
                        record.Silica_conformity = 'fail'

    Silica_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_Silica_nabl", store=True)

    @api.depends('Silica','eln_ref','grade')
    def _compute_Silica_nabl(self):
        
        for record in self:
            record.Silica_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6b064931-b820-44dd-a096-99c2666bd191')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6b064931-b820-44dd-a096-99c2666bd191')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.Silica - record.Silica*mu_value
                    upper = record.Silica + record.Silica*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.Silica_nabl = 'pass'
                        break
                    else:
                        record.Silica_nabl = 'fail'


    @api.depends('wt_of_two_rp', 'wt_of_two_r')
    def _compute_difference_in_wt(self):
        for record in self:
            record.difference_in_wt = record.wt_of_two_rp - record.wt_of_two_r


    @api.depends('difference_in_wt', 'wt_of_sample')
    def _compute_silica_percentage(self):
        for record in self:
            if record.wt_of_sample:
                record.Silica = (record.difference_in_wt * 100) / record.wt_of_sample
            else:
                record.Silica = 0.0


    # Combined Ferric Oxide and Alumina

    r2o3_name = fields.Char("Name",default="Combined Ferric Oxide and Alumina")
    r2o3_visible = fields.Boolean("Combined Ferric Oxide and Alumina",compute="_compute_visible")

    siliceous2 = fields.Char(string="Siliceous Pulverized Fuel Ash" ,default="70.0 Min")
    calcareous2 = fields.Char(string="Calcareous Pulverized Fuel Ash",default="50.0 Min")

    wt_of_empty_combine = fields.Float("Wt of empty crucible (gm)",digits=(16, 4))
    wt_of_cr_combine = fields.Float("Wt of  empty  crucible + residue (gm)",digits=(16, 4))
    wt_of_sample_combine = fields.Float("Wt of sample (gm)",digits=(16, 4))
    difference_in_wt_combaine = fields.Float("Difference in weight = (B - A)",compute="_compute_difference_in_wt_combaine",digits=(16, 4))
    r2o3 = fields.Float("Combined Ferric Oxide and Alumina (R2O3) = D x 100/C",compute="_compute_r2o3")


    @api.depends('wt_of_cr_combine', 'wt_of_empty_combine')
    def _compute_difference_in_wt_combaine(self):
        for record in self:
            record.difference_in_wt_combaine = record.wt_of_cr_combine - record.wt_of_empty_combine

    @api.depends('difference_in_wt_combaine', 'wt_of_sample_combine')
    def _compute_r2o3(self):
        for record in self:
            if record.wt_of_sample_combine:
                record.r2o3 = (record.difference_in_wt_combaine * 100) / record.wt_of_sample_combine
            else:
                record.r2o3 = 0.0

    r2o3_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_r2o3_conformity", store=True)

    @api.depends('r2o3','eln_ref','grade')
    def _compute_r2o3_conformity(self):
        
        for record in self:
            record.r2o3_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','de00fb1d-bf64-4c65-b098-b22066eed595')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','de00fb1d-bf64-4c65-b098-b22066eed595')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.r2o3 - record.r2o3*mu_value
                    upper = record.r2o3 + record.r2o3*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.r2o3_conformity = 'pass'
                        break
                    else:
                        record.r2o3_conformity = 'fail'

    r2o3_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_r2o3_nabl", store=True)

    @api.depends('r2o3','eln_ref','grade')
    def _compute_r2o3_nabl(self):
        
        for record in self:
            record.r2o3_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','de00fb1d-bf64-4c65-b098-b22066eed595')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','de00fb1d-bf64-4c65-b098-b22066eed595')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.r2o3 - record.r2o3*mu_value
                    upper = record.r2o3 + record.r2o3*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.r2o3_nabl = 'pass'
                        break
                    else:
                        record.r2o3_nabl = 'fail'



    # %Ferric Oxide

    ferric_oxide_name = fields.Char("Name",default="% Ferric Oxide")
    ferric_oxide_visible = fields.Boolean("% Ferric Oxide",compute="_compute_visible")

    siliceous3 = fields.Char(string="Siliceous Pulverized Fuel Ash",default="--")
    calcareous3 = fields.Char(string="Calcareous Pulverized Fuel Ash",default="--")

    wt_of_sample_ferric_oxide = fields.Float("Wt of sample (gm)",digits=(16, 4))
    burette_ferric_oxide  = fields.Float("Burette reading of KMnO4 for sampl (ml)")
    normality_ferric_oxide = fields.Float("Normality of KMnO4")
    ferric_oxide = fields.Float("Ferric Oxide = B x Cx 0.05585 x 1.43 x 100/A",compute="_compute_ferric_oxide")

    @api.depends('burette_ferric_oxide', 'normality_ferric_oxide', 'wt_of_sample_ferric_oxide')
    def _compute_ferric_oxide(self):
        for record in self:
            if record.wt_of_sample_ferric_oxide:
                record.ferric_oxide = record.burette_ferric_oxide * record.normality_ferric_oxide * 0.05585 * 1.43 * 100 / record.wt_of_sample_ferric_oxide
            else:
                record.ferric_oxide = 0.0

    ferric_oxide_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_ferric_oxide_conformity", store=True)

    @api.depends('ferric_oxide','eln_ref','grade')
    def _compute_ferric_oxide_conformity(self):
        
        for record in self:
            record.ferric_oxide_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f41a3a24-c81f-480d-88b1-5f0711870d3d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f41a3a24-c81f-480d-88b1-5f0711870d3d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.ferric_oxide - record.ferric_oxide*mu_value
                    upper = record.ferric_oxide + record.ferric_oxide*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.ferric_oxide_conformity = 'pass'
                        break
                    else:
                        record.ferric_oxide_conformity = 'fail'

    ferric_oxide_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_ferric_oxide_nabl", store=True)

    @api.depends('ferric_oxide','eln_ref','grade')
    def _compute_ferric_oxide_nabl(self):
        
        for record in self:
            record.ferric_oxide_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f41a3a24-c81f-480d-88b1-5f0711870d3d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f41a3a24-c81f-480d-88b1-5f0711870d3d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.ferric_oxide - record.ferric_oxide*mu_value
                    upper = record.ferric_oxide + record.ferric_oxide*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.ferric_oxide_nabl = 'pass'
                        break
                    else:
                        record.ferric_oxide_nabl = 'fail'

    
    # %Alumina

    alumina_name = fields.Char("Name",default="% Alumina")
    alumina1_visible = fields.Boolean("% Alumina",compute="_compute_visible")

    siliceous4 = fields.Char(string="Siliceous Pulverized Fuel Ash",default="--")
    calcareous4 = fields.Char(string="Calcareous Pulverized Fuel Ash",default="--")

    alumina = fields.Float(string="Alumina = R2O3 - Ferric oxide",compute="_compute_alumina")

    @api.depends('r2o3', 'ferric_oxide')
    def _compute_alumina(self):
        for record in self:
            record.alumina = record.r2o3 - record.ferric_oxide


    alumina_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_alumina_conformity", store=True)

    @api.depends('alumina','eln_ref','grade')
    def _compute_alumina_conformity(self):
        
        for record in self:
            record.alumina_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','399adf9d-d71d-486b-b40b-676b09173d18')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','399adf9d-d71d-486b-b40b-676b09173d18')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.alumina - record.alumina*mu_value
                    upper = record.alumina + record.alumina*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.alumina_conformity = 'pass'
                        break
                    else:
                        record.alumina_conformity = 'fail'

    alumina_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_alumina_nabl", store=True)

    @api.depends('alumina','eln_ref','grade')
    def _compute_alumina_nabl(self):
        
        for record in self:
            record.alumina_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','399adf9d-d71d-486b-b40b-676b09173d18')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','399adf9d-d71d-486b-b40b-676b09173d18')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.alumina - record.alumina*mu_value
                    upper = record.alumina + record.alumina*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.alumina_nabl = 'pass'
                        break
                    else:
                        record.alumina_nabl = 'fail'




    # CaO

    
    cao_name = fields.Char("Name",default="CaO")
    cao_visible = fields.Boolean("CaO",compute="_compute_visible")

    siliceous5 = fields.Char(string="Siliceous Pulverized Fuel Ash")
    calcareous5 = fields.Char(string="Calcareous Pulverized Fuel Ash")

    wt_of_sample_cao = fields.Float("Wt of sample (gm)",digits=(16, 4))
    burette_cao  = fields.Float("BR of 0.01N EDTA")
    normality_cao = fields.Float("Normality OF EDTA")
    dilution_cao = fields.Float("Dilution")
    cao = fields.Float("BR*0.05608*N*100*dilution/S.wt",compute="_compute_cao")


    @api.depends('burette_cao', 'normality_cao', 'dilution_cao', 'wt_of_sample_cao')
    def _compute_cao(self):
        for record in self:
            if record.wt_of_sample_cao != 0:  # Check for division by zero
                record.cao = (record.burette_cao * record.normality_cao * 0.05608 * record.dilution_cao * 100) / record.wt_of_sample_cao
            else:
                record.cao = 0  # Handle the case where wt_of_sample_cao is zero



    cao_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_cao_conformity", store=True)

    @api.depends('cao','eln_ref','grade')
    def _compute_cao_conformity(self):
        
        for record in self:
            record.cao_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cad7aa77-fad0-44bf-a374-48c100f86bfe')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cad7aa77-fad0-44bf-a374-48c100f86bfe')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.cao - record.cao*mu_value
                    upper = record.cao + record.cao*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.cao_conformity = 'pass'
                        break
                    else:
                        record.cao_conformity = 'fail'

    cao_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_cao_nabl", store=True)

    @api.depends('cao','eln_ref','grade')
    def _compute_cao_nabl(self):
        
        for record in self:
            record.cao_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cad7aa77-fad0-44bf-a374-48c100f86bfe')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cad7aa77-fad0-44bf-a374-48c100f86bfe')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.cao - record.cao*mu_value
                    upper = record.cao + record.cao*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.cao_nabl = 'pass'
                        break
                    else:
                        record.cao_nabl = 'fail'




    # MgO
    mgo_name = fields.Char("Name",default="MgO")
    mgo_visible = fields.Boolean("MgO",compute="_compute_visible")

    siliceous6 = fields.Char(string="Siliceous Pulverized Fuel Ash",default="5.0 Max")
    calcareous6 = fields.Char(string="Calcareous Pulverized Fuel Ash",default="5.0 Max")

    wt_of_sample_mgo = fields.Float("Wt of sample (gm)",digits=(16, 4))
    burette_mgo  = fields.Float("BR of 0.01N EDTA")
    normality_mgo = fields.Float("Normality OF EDTA")
    dilution_mgo = fields.Float("Dilution")
    mgo = fields.Float("BR*N*0.04032*25*100/S.wt",compute="_compute_mgo")


    @api.depends('burette_mgo', 'normality_mgo', 'dilution_mgo', 'wt_of_sample_mgo')
    def _compute_mgo(self):
        for record in self:
            if record.wt_of_sample_mgo != 0:  # Check for division by zero
                record.mgo = (record.burette_mgo * record.normality_mgo * 0.04032 * record.dilution_mgo * 100) / record.wt_of_sample_mgo
            else:
                record.mgo = 0  # Handle the case where wt_of_sample_cao is zero

    mgo_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_mgo_conformity", store=True)

    @api.depends('mgo','eln_ref','grade')
    def _compute_mgo_conformity(self):
        
        for record in self:
            record.mgo_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a50a3026-4c50-4314-83b2-8c66b259756a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a50a3026-4c50-4314-83b2-8c66b259756a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.mgo - record.mgo*mu_value
                    upper = record.mgo + record.mgo*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.mgo_conformity = 'pass'
                        break
                    else:
                        record.mgo_conformity = 'fail'

    mgo_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_mgo_nabl", store=True)

    @api.depends('mgo','eln_ref','grade')
    def _compute_mgo_nabl(self):
        
        for record in self:
            record.mgo_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a50a3026-4c50-4314-83b2-8c66b259756a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a50a3026-4c50-4314-83b2-8c66b259756a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.mgo - record.mgo*mu_value
                    upper = record.mgo + record.mgo*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.mgo_nabl = 'pass'
                        break
                    else:
                        record.mgo_nabl = 'fail'




    # % Calicum Oxide

    calicum_oxide_name = fields.Char("Name",default="% Calicum Oxide")
    calicum_oxide_visible = fields.Boolean("MgO",compute="_compute_visible")

    siliceous7 = fields.Char(string="Siliceous Pulverized Fuel Ash")
    calcareous7 = fields.Char(string="Calcareous Pulverized Fuel Ash")

    wt_of_sample_calicum_oxide = fields.Float("sample wt (gm)",digits=(16, 4))
    wt_cr_calicum_oxide  = fields.Float("wt of crucible + residue (gm)",digits=(16, 4))
    wt_empty_calicum_oxide = fields.Float("wt of empty crucible (gm)",digits=(16, 4))
    difference_calicum_oxide = fields.Float("Difference = ( B - C ) gm",compute="_compute_difference_calicum_oxide",digits=(16, 4))
    calicum_oxide = fields.Float("% CaO = D  x 100/A",compute="_compute_calicum_oxide")


    @api.depends('wt_cr_calicum_oxide', 'wt_empty_calicum_oxide')
    def _compute_difference_calicum_oxide(self):
        for record in self:
            record.difference_calicum_oxide = record.wt_cr_calicum_oxide - record.wt_empty_calicum_oxide


    @api.depends('wt_cr_calicum_oxide', 'wt_empty_calicum_oxide', 'wt_of_sample_calicum_oxide')
    def _compute_calicum_oxide(self):
        for record in self:
            if record.wt_of_sample_calicum_oxide != 0:  # Check for division by zero
                record.calicum_oxide = ((record.wt_cr_calicum_oxide - record.wt_empty_calicum_oxide) * 100) / record.wt_of_sample_calicum_oxide
            else:
                record.calicum_oxide = 0 


    calicum_oxide_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_calicum_oxide_conformity", store=True)

    @api.depends('calicum_oxide','eln_ref','grade')
    def _compute_calicum_oxide_conformity(self):
        
        for record in self:
            record.calicum_oxide_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4ddec5e4-d9eb-480b-8965-78c1d92f7349')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4ddec5e4-d9eb-480b-8965-78c1d92f7349')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.calicum_oxide - record.calicum_oxide*mu_value
                    upper = record.calicum_oxide + record.calicum_oxide*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.calicum_oxide_conformity = 'pass'
                        break
                    else:
                        record.calicum_oxide_conformity = 'fail'

    calicum_oxide_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_calicum_oxide_nabl", store=True)

    @api.depends('calicum_oxide','eln_ref','grade')
    def _compute_calicum_oxide_nabl(self):
        
        for record in self:
            record.calicum_oxide_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4ddec5e4-d9eb-480b-8965-78c1d92f7349')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4ddec5e4-d9eb-480b-8965-78c1d92f7349')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.calicum_oxide - record.calicum_oxide*mu_value
                    upper = record.calicum_oxide + record.calicum_oxide*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.calicum_oxide_nabl = 'pass'
                        break
                    else:
                        record.calicum_oxide_nabl = 'fail'





    # %Magnesium Oxide
    magnesium_oxide_name = fields.Char("Name", default="% Magnesium Oxide")
    magnesium_oxide_visible = fields.Boolean("MgO", compute="_compute_visible")

    siliceous8 = fields.Char(string="Siliceous Pulverized Fuel Ash",default="5.0 Max")
    calcareous8 = fields.Char(string="Calcareous Pulverized Fuel Ash",default="5.0 Max")

    wt_of_sample_magnesium_oxide = fields.Float("sample wt (gm)",digits=(16, 4))
    wt_cr_magnesium_oxide = fields.Float("wt of crucible + residue (gm)",digits=(16, 4))
    wt_empty_magnesium_oxide = fields.Float("wt of empty crucible (gm)",digits=(16, 4))
    difference_magnesium_oxide = fields.Float("Difference = ( B - C ) gm", compute="_compute_difference_magnesium_oxide",digits=(16, 4))
    magnesium_oxide = fields.Float("% MgO = D x 0.3621 x 100/A", compute="_compute_magnesium_oxide")

    @api.depends('wt_cr_magnesium_oxide', 'wt_empty_magnesium_oxide')
    def _compute_difference_magnesium_oxide(self):
        for record in self:
            record.difference_magnesium_oxide = record.wt_cr_magnesium_oxide - record.wt_empty_magnesium_oxide

    @api.depends('wt_cr_magnesium_oxide', 'wt_empty_magnesium_oxide', 'wt_of_sample_magnesium_oxide')
    def _compute_magnesium_oxide(self):
        for record in self:
            if record.wt_of_sample_magnesium_oxide != 0:  # Check for division by zero
                record.magnesium_oxide = ((record.wt_cr_magnesium_oxide - record.wt_empty_magnesium_oxide) * 36.21) / record.wt_of_sample_magnesium_oxide
            else:
                record.magnesium_oxide = 0



    magnesium_oxide_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_magnesium_oxide_conformity", store=True)

    @api.depends('magnesium_oxide','eln_ref','grade')
    def _compute_magnesium_oxide_conformity(self):
        
        for record in self:
            record.magnesium_oxide_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bff1cbf6-c067-430d-9391-616a077daa73')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bff1cbf6-c067-430d-9391-616a077daa73')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.magnesium_oxide - record.magnesium_oxide*mu_value
                    upper = record.magnesium_oxide + record.magnesium_oxide*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.magnesium_oxide_conformity = 'pass'
                        break
                    else:
                        record.magnesium_oxide_conformity = 'fail'

    magnesium_oxide_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_magnesium_oxide_nabl", store=True)

    @api.depends('magnesium_oxide','eln_ref','grade')
    def _compute_magnesium_oxide_nabl(self):
        
        for record in self:
            record.magnesium_oxide_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bff1cbf6-c067-430d-9391-616a077daa73')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','bff1cbf6-c067-430d-9391-616a077daa73')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.magnesium_oxide - record.magnesium_oxide*mu_value
                    upper = record.magnesium_oxide + record.magnesium_oxide*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.magnesium_oxide_nabl = 'pass'
                        break
                    else:
                        record.magnesium_oxide_nabl = 'fail'

    # %Sulphur trioxide (SO3)
    so3_name = fields.Char("Name", default="% Sulphur trioxide (SO3)")
    so3_visible = fields.Boolean("SO3", compute="_compute_visible")

    siliceous9 = fields.Char(string="Siliceous Pulverized Fuel Ash",default="3.0 Max")
    calcareous9 = fields.Char(string="Calcareous Pulverized Fuel Ash",default="3.0 Max")

    wt_of_sample_so3 = fields.Float("sample wt (gm)",digits=(16, 4))
    wt_cr_so3 = fields.Float("wt of crucible + residue (gm)",digits=(16, 4))
    wt_empty_co3 = fields.Float("wt of empty crucible (gm)",digits=(16, 4))
    difference_co3 = fields.Float("Residue weight = (B - C) gm", compute="_compute_difference_so3",digits=(16, 4))
    so3 = fields.Float("% Sulphur trioxide (SO3)", compute="_compute_so3")

    @api.depends('wt_cr_so3', 'wt_empty_co3')
    def _compute_difference_so3(self):
        for record in self:
            record.difference_co3 = record.wt_cr_so3 - record.wt_empty_co3

    @api.depends('difference_co3', 'wt_of_sample_so3')
    def _compute_so3(self):
        for record in self:
            if record.wt_of_sample_so3 != 0:  # Check for division by zero
                record.so3 = record.difference_co3 * 34.3 / record.wt_of_sample_so3
            else:
                record.so3 = 0


    so3_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_so3_conformity", store=True)

    @api.depends('so3','eln_ref','grade')
    def _compute_so3_conformity(self):
        
        for record in self:
            record.so3_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','789c0940-27b3-42a0-aacf-4d2a8d2e9a19')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','789c0940-27b3-42a0-aacf-4d2a8d2e9a19')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','789c0940-27b3-42a0-aacf-4d2a8d2e9a19')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','789c0940-27b3-42a0-aacf-4d2a8d2e9a19')]).parameter_table
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
    loi_name = fields.Char("Name", default="% Loss on Ignition")
    loi_visible = fields.Boolean("% Loss on Ignition", compute="_compute_visible")

    siliceous10 = fields.Char(string="Siliceous Pulverized Fuel Ash",default="5.0 Max")
    calcareous10 = fields.Char(string="Calcareous Pulverized Fuel Ash",default="5.0 Max")

    wt_of_empty_loi = fields.Float("wt of empty crucible (gm)",digits=(16, 4))
    wt_empty_cs_loi = fields.Float("wt of empty crucible + sample before ignition gm",digits=(16, 4))
    wt_cs_loi = fields.Float("wt of crucible + sample after ignition gm",digits=(16, 4))
    wt_of_sample_loi = fields.Float("Wt of sample gm = B - C", compute="_compute_wt_of_sample_loi",digits=(16, 4))
    loi_in_wt = fields.Float("Loss in weight = B - A", compute="_compute_loi_in_wt",digits=(16, 4))
    loi = fields.Float("Loss on ignition = E x 100/ D", compute="_compute_loi")

    @api.depends('wt_empty_cs_loi', 'wt_cs_loi')
    def _compute_wt_of_sample_loi(self):
        for record in self:
            record.wt_of_sample_loi = record.wt_empty_cs_loi - record.wt_cs_loi

    @api.depends('wt_empty_cs_loi', 'wt_of_empty_loi')
    def _compute_loi_in_wt(self):
        for record in self:
            record.loi_in_wt = record.wt_empty_cs_loi - record.wt_of_empty_loi

    @api.depends('wt_of_sample_loi', 'loi_in_wt')
    def _compute_loi(self):
        for record in self:
            if record.loi_in_wt != 0:  # Check for division by zero
                record.loi = (record.wt_of_sample_loi * 100) / record.loi_in_wt
            else:
                record.loi = 0



    loi_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_loi_conformity", store=True)

    @api.depends('loi','eln_ref','grade')
    def _compute_loi_conformity(self):
        
        for record in self:
            record.loi_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e09ddd61-2d20-4d5a-b922-bea8bbdeea72')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e09ddd61-2d20-4d5a-b922-bea8bbdeea72')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.loi - record.loi*mu_value
                    upper = record.loi + record.loi*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.loi_conformity = 'pass'
                        break
                    else:
                        record.loi_conformity = 'fail'

    loi_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_loi_nabl", store=True)

    @api.depends('loi','eln_ref','grade')
    def _compute_loi_nabl(self):
        
        for record in self:
            record.loi_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e09ddd61-2d20-4d5a-b922-bea8bbdeea72')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','e09ddd61-2d20-4d5a-b922-bea8bbdeea72')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.loi - record.loi*mu_value
                    upper = record.loi + record.loi*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.loi_nabl = 'pass'
                        break
                    else:
                        record.loi_nabl = 'fail'



    # Alkali as Na₂O Clause  

    casting_28_name = fields.Char("Name",default="28 Days")
    casting_date_28days = fields.Date(string="Date of Casting")
    testing_date_28days = fields.Date(string="Date of Testing",compute="_compute_testing_date_28days")
    status_28days = fields.Boolean("Done")

    @api.depends('casting_date_28days')
    def _compute_testing_date_28days(self):
        for record in self:
            if record.casting_date_28days:
                cast_date = fields.Datetime.from_string(record.casting_date_28days)
                testing_date = cast_date + timedelta(days=28)
                record.testing_date_28days = fields.Datetime.to_string(testing_date)
            else:
                record.testing_date_28days = False

    na2o_name = fields.Char("Name", default="Alkali as Na₂O")
    na2o_visible = fields.Boolean("Alkali as Na₂O", compute="_compute_visible")

    siliceous11 = fields.Char(string="Siliceous Pulverized Fuel Ash" , default="--")
    calcareous11 = fields.Char(string="Calcareous Pulverized Fuel Ash", default="--")

    wt_of_sample_na2o = fields.Float("Weight of sample taken",digits=(16, 4))
    dilution_na2o = fields.Float("Dilution")
    sodium_reading_na2o = fields.Float("Sodium reading")
    ffg_na2o = fields.Float("Factor from graph")
    na2o_calculation = fields.Float("Dilution *Reading* factor *100/10000*wt of sample*A4",compute="_compute_na2o_calculation")
    na2o_round = fields.Float("Na * 1.3480",compute="_compute_na2o_round")
    

    @api.depends('dilution_na2o', 'sodium_reading_na2o', 'ffg_na2o', 'wt_of_sample_na2o')
    def _compute_na2o_calculation(self):
        for record in self:
            denominator = 10000 * record.wt_of_sample_na2o
            if denominator != 0:
                record.na2o_calculation = (record.dilution_na2o * record.sodium_reading_na2o * record.ffg_na2o * 100) / denominator
            else:
                record.na2o_calculation = 0

    @api.depends('na2o_calculation')
    def _compute_na2o_round(self):
        for record in self:
            record.na2o_round = record.na2o_calculation * 1.3480


    na2o_round_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_na2o_round_conformity", store=True)

    @api.depends('na2o_round','eln_ref','grade')
    def _compute_na2o_round_conformity(self):
        
        for record in self:
            record.na2o_round_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ccd6049-2b3d-42a0-a78f-b83e49eeff6a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ccd6049-2b3d-42a0-a78f-b83e49eeff6a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.na2o_round - record.na2o_round*mu_value
                    upper = record.na2o_round + record.na2o_round*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.na2o_round_conformity = 'pass'
                        break
                    else:
                        record.na2o_round_conformity = 'fail'

    na2o_round_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_na2o_round_nabl", store=True)

    @api.depends('na2o_round','eln_ref','grade')
    def _compute_na2o_round_nabl(self):
        
        for record in self:
            record.na2o_round_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ccd6049-2b3d-42a0-a78f-b83e49eeff6a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3ccd6049-2b3d-42a0-a78f-b83e49eeff6a')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.na2o_round - record.na2o_round*mu_value
                    upper = record.na2o_round + record.na2o_round*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.na2o_round_nabl = 'pass'
                        break
                    else:
                        record.na2o_round_nabl = 'fail'



    # Alkali as K₂O 


    casting_28_name_k2o = fields.Char("Name",default="28 Days")
    casting_date_28days_k2o = fields.Date(string="Date of Casting")
    testing_date_28days_k2o = fields.Date(string="Date of Testing",compute="_compute_testing_date_28days_k2o")
    status_28days_k2o = fields.Boolean("Done")

    @api.depends('casting_date_28days_k2o')
    def _compute_testing_date_28days_k2o(self):
        for record in self:
            if record.casting_date_28days_k2o:
                cast_date = fields.Datetime.from_string(record.casting_date_28days_k2o)
                testing_date = cast_date + timedelta(days=28)
                record.testing_date_28days_k2o = fields.Datetime.to_string(testing_date)
            else:
                record.testing_date_28days_k2o = False

    k2o_name = fields.Char("Name", default="Alkali as K₂O")
    k2o_visible = fields.Boolean("Alkali as K₂O", compute="_compute_visible")

    siliceous12 = fields.Char(string="Siliceous Pulverized Fuel Ash" , default="--")
    calcareous12 = fields.Char(string="Calcareous Pulverized Fuel Ash", default="--")

    wt_of_sample_k2o = fields.Float("Weight of sample taken",digits=(16, 4))
    dilution_k2o = fields.Float("Dilution")
    potasium_reading_k2o = fields.Float("Potasium reading")
    ffg_k2o = fields.Float("Factor from graph")
    k2o_calculation = fields.Float("Dilution *Reading* factor *100/10000*wt of sample*A4",compute="_compute_k2o_calculation")
    k2o_round = fields.Float("K *1.20",compute="_compute_k2o_round")

    @api.depends('dilution_k2o', 'potasium_reading_k2o', 'ffg_k2o', 'wt_of_sample_k2o')
    def _compute_k2o_calculation(self):
        for record in self:
            denominator = 10000 * record.wt_of_sample_k2o
            if denominator != 0:
                record.k2o_calculation = (record.dilution_k2o * record.potasium_reading_k2o * record.ffg_k2o * 100) / denominator
            else:
                record.k2o_calculation = 0

    @api.depends('k2o_calculation')
    def _compute_k2o_round(self):
        for record in self:
            record.k2o_round = record.k2o_calculation * 1.20


    k2o_round_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_k2o_round_conformity", store=True)

    @api.depends('k2o_round','eln_ref','grade')
    def _compute_k2o_round_conformity(self):
        
        for record in self:
            record.k2o_round_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b6fb80a6-b992-477e-9048-c40b58e28a6c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b6fb80a6-b992-477e-9048-c40b58e28a6c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.k2o_round - record.k2o_round*mu_value
                    upper = record.k2o_round + record.k2o_round*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.k2o_round_conformity = 'pass'
                        break
                    else:
                        record.k2o_round_conformity = 'fail'

    k2o_round_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_k2o_round_nabl", store=True)

    @api.depends('k2o_round','eln_ref','grade')
    def _compute_k2o_round_nabl(self):
        
        for record in self:
            record.k2o_round_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b6fb80a6-b992-477e-9048-c40b58e28a6c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b6fb80a6-b992-477e-9048-c40b58e28a6c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.k2o_round - record.k2o_round*mu_value
                    upper = record.k2o_round + record.k2o_round*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.k2o_round_nabl = 'pass'
                        break
                    else:
                        record.k2o_round_nabl = 'fail'



    # Available alkalis  % = A+B (0.65)

    available_alkalis_name = fields.Char("Name", default="Available alkalies as Na2O")
    available_alkalis_visible = fields.Boolean("Available alkalis", compute="_compute_visible")

    siliceous13 = fields.Char(string="Siliceous Pulverized Fuel Ash" ,  default="1.5 Max")
    calcareous13 = fields.Char(string="Calcareous Pulverized Fuel Ash",  default="1.5 Max")

    available_alkalis = fields.Float("Available alkalis  % = A+B (0.65)",compute="_compute_available_alkalis")

    @api.depends('na2o_round', 'k2o_round')
    def _compute_available_alkalis(self):
        for record in self:
            record.available_alkalis = record.na2o_round + (record.k2o_round * 0.65)

    available_alkalis_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_available_alkalis_conformity", store=True)

    @api.depends('available_alkalis','eln_ref','grade')
    def _compute_available_alkalis_conformity(self):
        
        for record in self:
            record.available_alkalis_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ab486ca-fb44-437b-adeb-8b6928ac43b0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ab486ca-fb44-437b-adeb-8b6928ac43b0')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.available_alkalis - record.available_alkalis*mu_value
                    upper = record.available_alkalis + record.available_alkalis*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.available_alkalis_conformity = 'pass'
                        break
                    else:
                        record.available_alkalis_conformity = 'fail'

    available_alkalis_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_available_alkalis_nabl", store=True)

    @api.depends('available_alkalis','eln_ref','grade')
    def _compute_available_alkalis_nabl(self):
        
        for record in self:
            record.available_alkalis_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ab486ca-fb44-437b-adeb-8b6928ac43b0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5ab486ca-fb44-437b-adeb-8b6928ac43b0')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.available_alkalis - record.available_alkalis*mu_value
                    upper = record.available_alkalis + record.available_alkalis*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.available_alkalis_nabl = 'pass'
                        break
                    else:
                        record.available_alkalis_nabl = 'fail'








    #Chloride
    chloride_name = fields.Char("Name",default="Chloride")
    chloride_visible = fields.Boolean("Chloride",compute="_compute_visible")

    siliceous14 = fields.Char(string="Siliceous Pulverized Fuel Ash",default="0.05 Max")
    calcareous14 = fields.Char(string="Calcareous Pulverized Fuel Ash",default="0.05 Max")

    burette_reading_chloride = fields.Float("Burette reading for Blank")
    burette_reading_sample_chloride = fields.Float("Burette reading  for sample (ml)")
    diff_chloride = fields.Float("Diff. in Burette readings = (A - B )",compute="_compute_diff_chloride")
    normality_chloride = fields.Float("Normarility of 0.025N NH₄SCN")
    wt_of_sample_chloride  = fields.Float("weight of sample (gm)",digits=(16, 4))
    chloride = fields.Float("Chloride % = C x D x 0.03545 x 100 / E",compute="_compute_chloride",digits=(12,3))

    @api.depends('burette_reading_chloride', 'burette_reading_sample_chloride')
    def _compute_diff_chloride(self):
        for record in self:
            record.diff_chloride = record.burette_reading_chloride - record.burette_reading_sample_chloride


    @api.depends('diff_chloride', 'normality_chloride', 'wt_of_sample_chloride')
    def _compute_chloride(self):
        for record in self:
            if record.wt_of_sample_chloride != 0:
                record.chloride = (record.diff_chloride * record.normality_chloride * 0.03545 * 100) / record.wt_of_sample_chloride
            else:
                record.chloride = 0

    chloride_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_chloride_conformity", store=True)

    @api.depends('chloride','eln_ref','grade')
    def _compute_chloride_conformity(self):
        
        for record in self:
            record.chloride_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ab368a42-36c6-44f2-81af-7b81a6ea81e7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ab368a42-36c6-44f2-81af-7b81a6ea81e7')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.chloride - record.chloride*mu_value
                    upper = record.chloride + record.chloride*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.chloride_conformity = 'pass'
                        break
                    else:
                        record.chloride_conformity = 'fail'

    chloride_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_chloride_nabl", store=True)

    @api.depends('chloride','eln_ref','grade')
    def _compute_chloride_nabl(self):
        
        for record in self:
            record.chloride_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ab368a42-36c6-44f2-81af-7b81a6ea81e7')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','ab368a42-36c6-44f2-81af-7b81a6ea81e7')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.chloride - record.chloride*mu_value
                    upper = record.chloride + record.chloride*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.chloride_nabl = 'pass'
                        break
                    else:
                        record.chloride_nabl = 'fail'



     #combined_percentage
    combined_percentage_name = fields.Char("Name",default="SiO2 + Al2O3 + Fe2O3 %")
    combined_percentage_visible = fields.Boolean("SiO2 + Al2O3 + Fe2O3 %",compute="_compute_visible")

    siliceous15 = fields.Char(string="Siliceous Pulverized Fuel Ash",default="70.0 Min")
    calcareous15 = fields.Char(string="Calcareous Pulverized Fuel Ash",default="50.0 Min")

    combined_percentage = fields.Float("SiO2 + Al2O3 + Fe2O3 %", compute="_compute_combined_percentage")

    @api.depends('Silica', 'alumina', 'ferric_oxide')
    def _compute_combined_percentage(self):
        for record in self:
            combined_percentage = record.Silica + record.alumina + record.ferric_oxide
            record.combined_percentage = combined_percentage

    combined_percentage_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_combined_percentage_conformity", store=True)

    @api.depends('combined_percentage','eln_ref','grade')
    def _compute_combined_percentage_conformity(self):
        
        for record in self:
            record.combined_percentage_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fca3ebf1-b4fd-4597-81e1-37bf499c5a35')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fca3ebf1-b4fd-4597-81e1-37bf499c5a35')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.combined_percentage - record.combined_percentage*mu_value
                    upper = record.combined_percentage + record.combined_percentage*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.combined_percentage_conformity = 'pass'
                        break
                    else:
                        record.combined_percentage_conformity = 'fail'

    combined_percentage_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_combined_percentage_nabl", store=True)

    @api.depends('combined_percentage','eln_ref','grade')
    def _compute_combined_percentage_nabl(self):
        
        for record in self:
            record.combined_percentage_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fca3ebf1-b4fd-4597-81e1-37bf499c5a35')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','fca3ebf1-b4fd-4597-81e1-37bf499c5a35')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.combined_percentage - record.combined_percentage*mu_value
                    upper = record.combined_percentage + record.combined_percentage*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.combined_percentage_nabl = 'pass'
                        break
                    else:
                        record.combined_percentage_nabl = 'fail'



 
    


   

    @api.depends('sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.Silica_visible = False
            record.r2o3_visible = False
            record.ferric_oxide_visible = False
            record.alumina1_visible = False
            record.cao_visible = False
            record.mgo_visible = False
            record.calicum_oxide_visible = False
            record.magnesium_oxide_visible = False
            record.so3_visible = False
            record.loi_visible = False
            record.na2o_visible = False
            record.k2o_visible = False
            record.available_alkalis_visible = False
            record.chloride_visible = False
            record.combined_percentage_visible = False
           
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '6b064931-b820-44dd-a096-99c2666bd191':
                    record.Silica_visible = True
                if sample.internal_id == 'de00fb1d-bf64-4c65-b098-b22066eed595':
                    record.r2o3_visible = True
                if sample.internal_id == 'f41a3a24-c81f-480d-88b1-5f0711870d3d':
                    record.ferric_oxide_visible = True
                if sample.internal_id == '399adf9d-d71d-486b-b40b-676b09173d18':
                    record.alumina1_visible = True
                if sample.internal_id == 'cad7aa77-fad0-44bf-a374-48c100f86bfe':
                    record.cao_visible = True
                if sample.internal_id == 'a50a3026-4c50-4314-83b2-8c66b259756a':
                    record.mgo_visible = True
                if sample.internal_id == '4ddec5e4-d9eb-480b-8965-78c1d92f7349':
                    record.calicum_oxide_visible = True
                if sample.internal_id == 'bff1cbf6-c067-430d-9391-616a077daa73':
                    record.magnesium_oxide_visible = True
                if sample.internal_id == '789c0940-27b3-42a0-aacf-4d2a8d2e9a19':
                    record.so3_visible = True
                if sample.internal_id == 'e09ddd61-2d20-4d5a-b922-bea8bbdeea72':
                    record.loi_visible = True
                if sample.internal_id == '3ccd6049-2b3d-42a0-a78f-b83e49eeff6a':
                    record.na2o_visible = True
                if sample.internal_id == 'b6fb80a6-b992-477e-9048-c40b58e28a6c':
                    record.k2o_visible = True
                if sample.internal_id == '5ab486ca-fb44-437b-adeb-8b6928ac43b0':
                    record.available_alkalis_visible = True
                if sample.internal_id == 'ab368a42-36c6-44f2-81af-7b81a6ea81e7':
                    record.chloride_visible = True
                if sample.internal_id == 'fca3ebf1-b4fd-4597-81e1-37bf499c5a35':
                    record.combined_percentage_visible = True
               

    
          

    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(ChemicalFlyAsh, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


        
    def get_all_fields(self):
        record = self.env['chemical.flyash'].browse(self.ids[0])
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
    
