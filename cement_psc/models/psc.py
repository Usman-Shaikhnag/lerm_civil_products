from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math
from statistics import mean


class CementPSC(models.Model):
    _name = "cement.psc.ssl"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Cement")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    start_date = fields.Date(string="Start Date", compute="_compute_start_date", store=True)

    @api.depends('eln_ref.start_date')
    def _compute_start_date(self):
        for rec in self:
            rec.start_date = rec.eln_ref.start_date


  
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id


    ## Normal Consistency

    fineness_cement_name = fields.Char("Name",default="Fineness of Cement by Dry Sieving")
    fineness_cement_visible = fields.Boolean("Plan Area Visible",compute="_compute_visible")

    fneness_cement_lines = fields.One2many('fineness.cement.psc.ssl.line','parent_id',string="Fineness Cement")

    avg_cement = fields.Float(string="Avg Fineness Cement",compute="_compute_avg_wt_of_residue")

    avg_cement_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_avg_cement_conformity")

    avg_cement_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_cement_nabl")


    @api.depends('avg_cement','eln_ref','grade')
    def _compute_avg_cement_conformity(self):
        for record in self:
            record.avg_cement_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12457800-372f-4775-9bcb-e9dd70e6e6df')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12457800-372f-4775-9bcb-e9dd70e6e6df')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_cement - record.avg_cement*mu_value
                    upper = record.avg_cement + record.avg_cement*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_cement_conformity = 'pass'
                        break
                    else:
                        record.avg_cement_conformity = 'fail'

    @api.depends('avg_cement','eln_ref','grade')
    def _compute_avg_cement_nabl(self):
        
        for record in self:
            record.avg_cement_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12457800-372f-4775-9bcb-e9dd70e6e6df')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12457800-372f-4775-9bcb-e9dd70e6e6df')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_cement - record.avg_cement*mu_value
            upper = record.avg_cement + record.avg_cement*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_cement_nabl = 'pass'
                break
            else:
                record.avg_cement_nabl = 'fail'

    @api.depends('fneness_cement_lines.wt_of_residue')
    def _compute_avg_wt_of_residue(self):
        for rec in self:
            values = [line.wt_of_residue for line in rec.fneness_cement_lines if line.wt_of_residue is not None]
            rec.avg_cement = sum(values) / len(values) if values else 0.0

    wt_of_cement_a = fields.Float(string="Weight of the cement sample (a) ",compute="_compute_wt_of_cement_a")
    cement_passing_b = fields.Float(string="Cement Passing through the 90 Micron sieve (b)",compute="_compute_cement_passing_b")
    cement_retained_a_b = fields.Float(string="Cement retained in the 90 microns (a-b)",compute="_compute_cement_retained_a_b")

    @api.depends('fneness_cement_lines.wt_of_taken')
    def _compute_wt_of_cement_a(self):
        for rec in self:
            if rec.fneness_cement_lines:
                # 0th index (first line)
                rec.wt_of_cement_a = rec.fneness_cement_lines[0].wt_of_taken
            else:
                rec.wt_of_cement_a = 0.0

    @api.depends('wt_of_cement_a', 'avg_cement')
    def _compute_cement_passing_b(self):
        for rec in self:
            rec.cement_passing_b = rec.wt_of_cement_a - rec.avg_cement

    @api.depends('avg_cement')
    def _compute_cement_retained_a_b(self):
        for rec in self:
            rec.cement_retained_a_b = rec.avg_cement


        ## Density of Cement (Le-Chatlier Flask)

    density_cement_name = fields.Char("Name",default="Density of Cement (Le-Chatlier Flask)")
    density_cement_visible = fields.Boolean("Density of Cement (Le-Chatlier Flask) Visible",compute="_compute_visible")

    density_cement_lines = fields.One2many('density.cement.psc.ssl.line','parent_id',string="Fineness density")

    avg_density = fields.Float(string="Density of Cement g/cm3",compute="_compute_avg_density")

    specific_gravity = fields.Float(string="Specific Gravity of Cement",compute="_compute_cement_specific")

    specific_gravity_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_specific_gravity_conformity")

    specific_gravity_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_specific_gravity_nabl")


    @api.depends('specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_conformity(self):
        for record in self:
            record.specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104587frt-372f-4775-9bcb-e9dd70e6e6df')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104587frt-372f-4775-9bcb-e9dd70e6e6df')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.specific_gravity - record.specific_gravity*mu_value
                    upper = record.specific_gravity + record.specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.specific_gravity_conformity = 'fail'

    @api.depends('specific_gravity','eln_ref','grade')
    def _compute_specific_gravity_nabl(self):
        
        for record in self:
            record.specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104587frt-372f-4775-9bcb-e9dd70e6e6df')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','2104587frt-372f-4775-9bcb-e9dd70e6e6df')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.specific_gravity - record.specific_gravity*mu_value
            upper = record.specific_gravity + record.specific_gravity*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.specific_gravity_nabl = 'pass'
                break
            else:
                record.specific_gravity_nabl = 'fail'

    @api.depends('density_cement_lines.density')
    def _compute_avg_density(self):
        for rec in self:
            values = [line.density for line in rec.density_cement_lines if line.density is not None]
            rec.avg_density = sum(values) / len(values) if values else 0.0

    @api.depends('avg_density')
    def _compute_cement_specific(self):
        for rec in self:
            rec.specific_gravity = rec.avg_density


    ## Fineness by Blaine's Air Permeability

    fineness_blaine_name = fields.Char("Name",default="Fineness by Blaine's Air Permeability")
    fineness_blaine_visible = fields.Boolean("Fineness by Blaine's Air Permeability Visible",compute="_compute_visible")

    fineness_blaine_lines = fields.One2many('fineness.blaine.psc.ssl.line','parent_id',string="Fineness blaine")

    avg_fineness_blaine = fields.Float(string="Fineness of Cement, m2/kg ",compute="_compute_avg_fineness_blaine")

    avg_fineness_blaine_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_avg_fineness_blaine_conformity")

    avg_fineness_blaine_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_fineness_blaine_nabl")


    @api.depends('avg_fineness_blaine','eln_ref','grade')
    def _compute_avg_fineness_blaine_conformity(self):
        for record in self:
            record.avg_fineness_blaine_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3012478fffrr-372f-4775-9bcb-e9dd70214578r')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3012478fffrr-372f-4775-9bcb-e9dd70214578r')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_fineness_blaine - record.avg_fineness_blaine*mu_value
                    upper = record.avg_fineness_blaine + record.avg_fineness_blaine*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_fineness_blaine_conformity = 'pass'
                        break
                    else:
                        record.avg_fineness_blaine_conformity = 'fail'

    @api.depends('avg_fineness_blaine','eln_ref','grade')
    def _compute_avg_fineness_blaine_nabl(self):
        
        for record in self:
            record.avg_fineness_blaine_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3012478fffrr-372f-4775-9bcb-e9dd70214578r')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3012478fffrr-372f-4775-9bcb-e9dd70214578r')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_fineness_blaine - record.avg_fineness_blaine*mu_value
            upper = record.avg_fineness_blaine + record.avg_fineness_blaine*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_fineness_blaine_nabl = 'pass'
                break
            else:
                record.avg_fineness_blaine_nabl = 'fail'

    @api.depends('fineness_blaine_lines.fineness')
    def _compute_avg_fineness_blaine(self):
        for rec in self:
            values = [line.fineness for line in rec.fineness_blaine_lines if line.fineness is not None]
            rec.avg_fineness_blaine = sum(values) / len(values) if values else 0.0

    k = fields.Float("K :",digits=(12,3))
  
    e = fields.Float("E :")



      ## Soundness of Cement

    soundness_cement_name = fields.Char("Name",default="Soundness of Cement")
    soundness_cement_visible = fields.Boolean("Soundness of Cement Visible",compute="_compute_visible")

    soundness_cement_lines = fields.One2many('soundness.cement.psc.ssl.line','parent_id',string="Soundness")

    avg_soundness_cement = fields.Float(string="Fineness of Cement, m2/kg ",compute="_compute_avg_soundness_cement")

    avg_soundness_cement_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_avg_soundness_cement_conformity")

    avg_soundness_cement_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_soundness_cement_nabl")


    @api.depends('avg_soundness_cement','eln_ref','grade')
    def _compute_avg_soundness_cement_conformity(self):
        for record in self:
            record.avg_soundness_cement_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896f-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896f-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_soundness_cement - record.avg_soundness_cement*mu_value
                    upper = record.avg_soundness_cement + record.avg_soundness_cement*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_soundness_cement_conformity = 'pass'
                        break
                    else:
                        record.avg_soundness_cement_conformity = 'fail'

    @api.depends('avg_soundness_cement','eln_ref','grade')
    def _compute_avg_soundness_cement_nabl(self):
        
        for record in self:
            record.avg_soundness_cement_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896f-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896f-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_soundness_cement - record.avg_soundness_cement*mu_value
            upper = record.avg_soundness_cement + record.avg_soundness_cement*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_soundness_cement_nabl = 'pass'
                break
            else:
                record.avg_soundness_cement_nabl = 'fail'

    @api.depends('soundness_cement_lines.difference')
    def _compute_avg_soundness_cement(self):
        for rec in self:
            values = [line.difference for line in rec.soundness_cement_lines if line.difference is not None]
            rec.avg_soundness_cement = sum(values) / len(values) if values else 0.0


        ## Consistency of cement

    consistency_cement_name = fields.Char("Name",default="Consistency of cement")
    consistency_cement_visible = fields.Boolean("Consistency of cement Visible",compute="_compute_visible")

    consistency_cement_lines = fields.One2many('consistensy.cement.psc.ssl.line','parent_id',string="Consistency")

    consitency_of_cement = fields.Float(string="Consistency of Cement ",compute="_compute_consistency_of_cement")

    consitency_of_cement_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_consitency_of_cement_conformity")

    consitency_of_cement_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_consitency_of_cement_nabl")


    @api.depends('consitency_of_cement','eln_ref','grade')
    def _compute_consitency_of_cement_conformity(self):
        for record in self:
            record.consitency_of_cement_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','01247gggty-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','01247gggty-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.consitency_of_cement - record.consitency_of_cement*mu_value
                    upper = record.consitency_of_cement + record.consitency_of_cement*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.consitency_of_cement_conformity = 'pass'
                        break
                    else:
                        record.consitency_of_cement_conformity = 'fail'

    @api.depends('consitency_of_cement','eln_ref','grade')
    def _compute_consitency_of_cement_nabl(self):
        
        for record in self:
            record.consitency_of_cement_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','01247gggty-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','01247gggty-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.consitency_of_cement - record.consitency_of_cement*mu_value
            upper = record.consitency_of_cement + record.consitency_of_cement*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.consitency_of_cement_nabl = 'pass'
                break
            else:
                record.consitency_of_cement_nabl = 'fail'

    @api.depends('consistency_cement_lines.water_mix')
    def _compute_consistency_of_cement(self):
        for rec in self:
            lines = rec.consistency_cement_lines.filtered(lambda l: l.water_mix)
            if lines:
                last_line = lines.sorted('create_date')[-1]
                rec.consitency_of_cement = float(last_line.water_mix) or 0.0
            else:
                rec.consitency_of_cement = 0.0


            ## Setting Time

    setting_time_name = fields.Char("Name",default="Setting Time")
    setting_time_visible = fields.Boolean("Setting Time Visible",compute="_compute_visible")

    setting_time_lines = fields.One2many('setting.time.psc.ssl.line','parent_id',string="Setting time",default=lambda self: self._default_setting_time_lines())

    @api.model
    def _default_setting_time_lines(self):
        default_lines = [
            (0, 0, {'serial_no': 'Initial'}),
            (0, 0, {'serial_no': 'Final'})
          
        ]
        return default_lines

    initial_setting_time = fields.Float(string="Initial Setting Time",compute="_compute_setting_times",store=True)
    final_setting_time = fields.Float(string="Final Setting Time ",compute="_compute_setting_times",store=True)

    initial_setting_time_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_initial_setting_time_conformity")

    initial_setting_time_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_initial_setting_time_nabl")


    @api.depends('initial_setting_time','eln_ref','grade')
    def _compute_initial_setting_time_conformity(self):
        for record in self:
            record.initial_setting_time_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214ggt-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214ggt-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.initial_setting_time - record.initial_setting_time*mu_value
                    upper = record.initial_setting_time + record.initial_setting_time*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.initial_setting_time_conformity = 'pass'
                        break
                    else:
                        record.initial_setting_time_conformity = 'fail'

    @api.depends('initial_setting_time','eln_ref','grade')
    def _compute_initial_setting_time_nabl(self):
        
        for record in self:
            record.initial_setting_time_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214ggt-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214ggt-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.initial_setting_time - record.initial_setting_time*mu_value
            upper = record.initial_setting_time + record.initial_setting_time*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.initial_setting_time_nabl = 'pass'
                break
            else:
                record.initial_setting_time_nabl = 'fail'

    final_setting_time_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_final_setting_time_conformity")

    final_setting_time_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_final_setting_time_nabl")


    @api.depends('final_setting_time','eln_ref','grade')
    def _compute_final_setting_time_conformity(self):
        for record in self:
            record.final_setting_time_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5557tttyre-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5557tttyre-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.final_setting_time - record.final_setting_time*mu_value
                    upper = record.final_setting_time + record.final_setting_time*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.final_setting_time_conformity = 'pass'
                        break
                    else:
                        record.final_setting_time_conformity = 'fail'

    @api.depends('final_setting_time','eln_ref','grade')
    def _compute_final_setting_time_nabl(self):
        
        for record in self:
            record.final_setting_time_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5557tttyre-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5557tttyre-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.final_setting_time - record.final_setting_time*mu_value
            upper = record.final_setting_time + record.final_setting_time*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.final_setting_time_nabl = 'pass'
                break
            else:
                record.final_setting_time_nabl = 'fail'

    @api.depends('setting_time_lines.duration1')
    def _compute_setting_times(self):
        for rec in self:
            # Convert to list so index() works even for NewId
            lines_list = list(rec.setting_time_lines)

            # If sequence exists in model, use it, else fallback to current order in list
            if lines_list and hasattr(lines_list[0], 'sequence'):
                lines = sorted(lines_list, key=lambda l: l.sequence or 0)
            else:
                lines = lines_list  # Keep order as in the form view

            rec.initial_setting_time = lines[0].duration1 if len(lines) > 0 else 0.0
            rec.final_setting_time = lines[1].duration1 if len(lines) > 1 else 0.0


                ## Cement Compressive Strength

    compressive_name = fields.Char("Name",default="Cement Compressive Strength")
    compressive_visible = fields.Boolean("Cement Compressive Strength Visible",compute="_compute_visible")

    compressive_lines = fields.One2many('compressive.psc.ssl.line','parent_id',string="Compressive")

    avg_3_days = fields.Float(string="Avg Strength (3 Days)", compute="_compute_avg_strengths", store=True)

    avg_3_days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_avg_3_days_conformity")

    avg_3_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_3_days_nabl")


    @api.depends('avg_3_days','eln_ref','grade')
    def _compute_avg_3_days_conformity(self):
        for record in self:
            record.avg_3_days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','358789gtyg-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','358789gtyg-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_3_days - record.avg_3_days*mu_value
                    upper = record.avg_3_days + record.avg_3_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_3_days_conformity = 'pass'
                        break
                    else:
                        record.avg_3_days_conformity = 'fail'

    @api.depends('avg_3_days','eln_ref','grade')
    def _compute_avg_3_days_nabl(self):
        
        for record in self:
            record.avg_3_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','358789gtyg-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','358789gtyg-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_3_days - record.avg_3_days*mu_value
            upper = record.avg_3_days + record.avg_3_days*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_3_days_nabl = 'pass'
                break
            else:
                record.avg_3_days_nabl = 'fail'

    avg_7_days = fields.Float(string="Avg Strength (7 Days)", compute="_compute_avg_strengths", store=True)

    avg_7_days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_avg_7_days_conformity")

    avg_7_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_7_days_nabl")


    @api.depends('avg_7_days','eln_ref','grade')
    def _compute_avg_7_days_conformity(self):
        for record in self:
            record.avg_7_days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','555888ggghhjy-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','555888ggghhjy-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_7_days - record.avg_7_days*mu_value
                    upper = record.avg_7_days + record.avg_7_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_7_days_conformity = 'pass'
                        break
                    else:
                        record.avg_7_days_conformity = 'fail'

    @api.depends('avg_7_days','eln_ref','grade')
    def _compute_avg_7_days_nabl(self):
        
        for record in self:
            record.avg_7_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','555888ggghhjy-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','555888ggghhjy-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_7_days - record.avg_7_days*mu_value
            upper = record.avg_7_days + record.avg_7_days*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_7_days_nabl = 'pass'
                break
            else:
                record.avg_7_days_nabl = 'fail'


    avg_28_days = fields.Float(string="Avg Strength (28 Days)", compute="_compute_avg_strengths", store=True)

    avg_28_days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Conformity', default='fail',compute="_compute_avg_28_days_conformity")

    avg_28_days_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_28_days_nabl")


    @api.depends('avg_28_days','eln_ref','grade')
    def _compute_avg_28_days_conformity(self):
        for record in self:
            record.avg_28_days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5777fffrrtt11-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5777fffrrtt11-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_28_days - record.avg_28_days*mu_value
                    upper = record.avg_28_days + record.avg_28_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_28_days_conformity = 'pass'
                        break
                    else:
                        record.avg_28_days_conformity = 'fail'

    @api.depends('avg_28_days','eln_ref','grade')
    def _compute_avg_28_days_nabl(self):
        
        for record in self:
            record.avg_28_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5777fffrrtt11-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5777fffrrtt11-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_28_days - record.avg_28_days*mu_value
            upper = record.avg_28_days + record.avg_28_days*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_28_days_nabl = 'pass'
                break
            else:
                record.avg_28_days_nabl = 'fail'

    @api.depends('compressive_lines.days', 'compressive_lines.strenght')
    def _compute_avg_strengths(self):
        for rec in self:
            strengths_3 = [line.strenght for line in rec.compressive_lines if line.days == 3 and line.strenght]
            strengths_7 = [line.strenght for line in rec.compressive_lines if line.days == 7 and line.strenght]
            strengths_28 = [line.strenght for line in rec.compressive_lines if line.days == 28 and line.strenght]

            rec.avg_3_days = mean(strengths_3) if strengths_3 else 0.0
            rec.avg_7_days = mean(strengths_7) if strengths_7 else 0.0
            rec.avg_28_days = mean(strengths_28) if strengths_28 else 0.0




  

            
    ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.fineness_cement_visible = False
            record.density_cement_visible = False
            record.fineness_blaine_visible = False
            record.soundness_cement_visible = False
            record.consistency_cement_visible = False
            record.setting_time_visible = False
            record.compressive_visible = False
         
            

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '12457800-372f-4775-9bcb-e9dd70e6e6df':
                    record.fineness_cement_visible = True

                if sample.internal_id == '23145870-372f-4775-9bcb-e9dd70e3587g':
                    record.density_cement_visible = True

                if sample.internal_id == '3012478fffrr-372f-4775-9bcb-e9dd70214578r':
                    record.density_cement_visible = True
                    record.fineness_blaine_visible = True

                if sample.internal_id == '21457896f-372f-4775-9bcb-e9dd723547htui':
                    record.soundness_cement_visible = True

                if sample.internal_id == '01247gggty-372f-4775-9bcb-e9dd723547htui':
                    record.consistency_cement_visible = True

                if sample.internal_id == '3214578gg-372f-4775-9bcb-e9dd723547htui2':
                    record.consistency_cement_visible = True
                    record.setting_time_visible = True

                if sample.internal_id == '214578gt-372f-4775-9bcb-e9dd723547htui':
                    record.compressive_visible = True
             

    def open_eln_page(self):
    # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == '12457800-372f-4775-9bcb-e9dd70e6e6df':
                result.result_char = round(self.avg_cement,2)
                if self.avg_cement_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '2104587frt-372f-4775-9bcb-e9dd70e6e6df':
                result.result_char = round(self.specific_gravity,2)
                if self.specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '3012478fffrr-372f-4775-9bcb-e9dd70214578r':
                result.result_char = round(self.avg_fineness_blaine,2)
                if self.avg_fineness_blaine_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '21457896f-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.avg_soundness_cement,2)
                if self.avg_soundness_cement_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '01247gggty-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.consitency_of_cement,2)
                if self.consitency_of_cement_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '3214ggt-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.initial_setting_time,2)
                if self.initial_setting_time_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '5557tttyre-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.final_setting_time,2)
                if self.final_setting_time_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '358789gtyg-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.avg_3_days,2)
                if self.avg_3_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '555888ggghhjy-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.avg_7_days,2)
                if self.avg_7_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '5777fffrrtt11-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.avg_28_days,2)
                if self.avg_28_days_nabl == 'pass':
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
        record = super(CementPSC, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    # @api.model 
    # def write(self, values):
    #     # Perform additional actions or validations before update
    #     result = super(CementNormalConsistency, self).write(values)
    #     # Perform additional actions or validations after update
    #     return result
    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        # records = self.env['lerm.eln'].search([('id','=', record.eln_id.id)]).parameters_result
        # print("records",records)
        # self.sample_parameters = records
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['cement.psc.ssl'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value
        return field_values


class FinenessCementLine(models.Model):
    _name = "fineness.cement.psc.ssl.line"
    parent_id = fields.Many2one('cement.psc.ssl',string="Parent Id")

    serial_no = fields.Integer(string="Wt of Sample", readonly=True, copy=False, default=1)

   
    wt_of_taken = fields.Float(string=" Wt of Sample taken")
    wt_of_residue = fields.Float(string="Wt of residue")
    total_passed = fields.Float(string="Total wt Passed" ,compute="_compute_total_passed")

    @api.depends('wt_of_taken', 'wt_of_residue')
    def _compute_total_passed(self):
        for record in self:
            record.total_passed = record.wt_of_taken - record.wt_of_residue


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(FinenessCementLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class DensityCementLine(models.Model):
    _name = "density.cement.psc.ssl.line"
    parent_id = fields.Many2one('cement.psc.ssl',string="Parent Id")

    serial_no = fields.Integer(string="Trail No.", readonly=True, copy=False, default=1)

   
    wt_of_cement = fields.Float(string="Wt of Cement (g)")
    displaced_volume = fields.Float(string="Displaced Volume (cm3)")
    density = fields.Float(string="Density in g/cm3",compute="_compute_density",digits=(12,3))

    @api.depends('wt_of_cement', 'displaced_volume')
    def _compute_density(self):
        for rec in self:
            if rec.displaced_volume:  # Avoid division by zero
                rec.density = rec.wt_of_cement / rec.displaced_volume
            else:
                rec.density = 0.0




    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(DensityCementLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class FinenessBlaineLine(models.Model):
    _name = "fineness.blaine.psc.ssl.line"
    parent_id = fields.Many2one('cement.psc.ssl',string="Parent Id")

    serial_no = fields.Integer(string="Trail No.", readonly=True, copy=False, default=1)

   
    wt_of_cement1 = fields.Float(string="Wt of Cement (g)",digits=(12,3))
    time_sec = fields.Float(string="Time in Sec")
    fineness = fields.Float(string="Fineness m2/kg",compute="_compute_fineness")

    @api.depends('time_sec', 'parent_id.specific_gravity', 'parent_id.k', 'parent_id.e')
    def _compute_fineness(self):
        for rec in self:
            k = rec.parent_id.k
            e = rec.parent_id.e
            t = rec.time_sec
            s = rec.parent_id.specific_gravity

            if s and (1 - e) != 0 and t > 0:
                try:
                    part1 = (k / s)
                    part2 = math.sqrt(e ** 3) / (1 - e)
                    part3 = math.sqrt(t) / 0.001357
                    rec.fineness = part1 * part2 * part3
                except Exception:
                    rec.fineness = 0.0
            else:
                rec.fineness = 0.0

   




    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(FinenessBlaineLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class soundnessCementLine(models.Model):
    _name = "soundness.cement.psc.ssl.line"
    parent_id = fields.Many2one('cement.psc.ssl',string="Parent Id")

    serial_no = fields.Integer(string="Sr No.", readonly=True, copy=False, default=1)

   
    initial_distance = fields.Float(string="Initial Distance in mm")
    final_distance = fields.Float(string="Final distance in mm")
    difference = fields.Float(string="Difference in mm",compute="_compute_difference")


    @api.depends('initial_distance', 'final_distance')
    def _compute_difference(self):
        for rec in self:
            rec.difference = rec.final_distance - rec.initial_distance

   


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(soundnessCementLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1





class ConsistencyCementLine(models.Model):
    _name = "consistensy.cement.psc.ssl.line"
    parent_id = fields.Many2one('cement.psc.ssl',string="Parent Id")

    serial_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

   
    
    wt_of_cement1 = fields.Float(string="Wt of cement in gms")
    wt_of_water = fields.Float(string="wt of water in ml" ,compute="_compute_wt_of_water")
    water_mix = fields.Float(string="% of water mix")
    needle_penitration = fields.Float(string="Needle penetration in mm")
    duration = fields.Char(string="Duration of time in minutes")

    @api.depends('wt_of_cement1', 'water_mix')
    def _compute_wt_of_water(self):
        for rec in self:
            if rec.wt_of_cement1 and rec.water_mix:
                rec.wt_of_water = rec.wt_of_cement1 * rec.water_mix / 100
            else:
                rec.wt_of_water = 0.0


    

   


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ConsistencyCementLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1

class SettingTimetLine(models.Model):
    _name = "setting.time.psc.ssl.line"
    parent_id = fields.Many2one('cement.psc.ssl',string="Parent Id")

    serial_no = fields.Char(string="Test NO")

   
    
    wt_of_cements1 = fields.Float(string="Wt of cement in gms")
    wt_of_water1 = fields.Float(string="wt of water in ml" ,compute="_compute_wt_of_water1")
    water_mix1 = fields.Char(string="% of water mix")
    needle_penitration1 = fields.Char(string="Needle penetration in mm")
    duration1 = fields.Float(string="Duration of time in minutes")

   

    @api.depends('wt_of_cements1', 'parent_id.consitency_of_cement')
    def _compute_wt_of_water1(self):
        for rec in self:
            if rec.wt_of_cements1 and rec.parent_id.consitency_of_cement:
                rec.wt_of_water1 = rec.wt_of_cements1 * 0.85 * rec.parent_id.consitency_of_cement / 100
            else:
                rec.wt_of_water1 = 0.0



class CompressiveCementLine(models.Model):
    _name = "compressive.psc.ssl.line"
    parent_id = fields.Many2one('cement.psc.ssl',string="Parent Id")

    serial_no = fields.Integer(string="Specimen No", readonly=True, copy=False, default=1)

   
    
    dt_of_casting = fields.Date(string="Date of Casting ")
    days = fields.Integer(string="Days")
    dt_of_testing = fields.Date(string="Date of Testing")
    wt_of_cube = fields.Float(string="Wt of cube")
    area = fields.Float(string="Area",compute="_compute_area",store=True)
    load = fields.Float(string="Load in KN")
    strenght = fields.Float(string="Strength N/mm2",compute="_compute_strength")

    @api.onchange('parent_id')
    def _onchange_set_dt_of_casting(self):
        if self.parent_id and self.parent_id.start_date:
            self.dt_of_casting = self.parent_id.start_date

    @api.onchange('days')
    def _onchange_days_set_testing_date(self):
        if self.dt_of_casting and self.days:
            self.dt_of_testing = self.dt_of_casting + timedelta(days=self.days)
        else:
            self.dt_of_testing = False

    @api.depends('parent_id')
    def _compute_area(self):
        for rec in self:
            rec.area = 70.6 * 70.6

    @api.depends('load', 'area')
    def _compute_strength(self):
        for rec in self:
            if rec.area:
                rec.strenght = (rec.load * 1000) / rec.area
            else:
                rec.strenght = 0.0

    


    

   


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CompressiveCementLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1
    
