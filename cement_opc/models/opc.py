from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math
from statistics import mean


class CementNormalConsistency(models.Model):
    _name = "cement.opc"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Cement")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    avg_fineness_unit = fields.Char("Avg Fineness Cement Unit",compute="_compute_units", store=False)
    avg_fineness_blaine_unit = fields.Char("avg fineness blaine Unit",compute="_compute_units", store=False)
    avg_soundness_cement_unit = fields.Char("avg soundness cement Unit",compute="_compute_units", store=False)
    consitency_of_cement_unit = fields.Char("consitency of cement Unit", compute="_compute_units", store=False)
    avg_3_days_unit = fields.Char("Avg 3 days Unit",compute="_compute_units", store=False)
    avg_7_days_unit = fields.Char("avg 7 days Unit",compute="_compute_units", store=False)
    avg_28_days_unit = fields.Char("avg 28 days Unit",compute="_compute_units", store=False)
    avg_density_unit = fields.Char("avg density Unit",compute="_compute_units", store=False)
    avg_specific_gravity_unit = fields.Char("avg specific gravity Unit",compute="_compute_units", store=False)
    initial_time_unit = fields.Char("Initial Setting Time Unit",compute="_compute_units", store=False)
    final_time_unit = fields.Char("Final Setting Time Unit",compute="_compute_units", store=False)



    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'cement ppc.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }
    
    

    # ---- helper method
    def _get_unit(self, internal_id):
        param = self.env['lerm.parameter.master'].search([
            ('internal_id', '=', internal_id)
        ], limit=1)
        return param.unit.name if param.unit else ""

    # ---- compute + default values
    def _compute_units(self):
        for rec in self:
            rec.avg_fineness_unit = rec._get_unit("a9e97cea-372f-4775-9bcb-e9dd70e6e6df")
            rec.avg_fineness_blaine_unit = rec._get_unit("32457fg-372f-4775-9bcb-e9dd70214578r")
            rec.avg_soundness_cement_unit = rec._get_unit("23547gtyu-372f-4775-9bcb-e9dd723547htui")
            rec.consitency_of_cement_unit = rec._get_unit("3214578nbhgt2-372f-4775-9bcb-e9dd723547htui")
            rec.avg_3_days_unit = rec._get_unit("0124578hgggt-372f-4775-9bcb-e9dd723547htui")
            rec.avg_7_days_unit = rec._get_unit("30124587hhhy-372f-4775-9bcb-e9dd723547htui")
            rec.avg_28_days_unit = rec._get_unit("3012456998ffff-372f-4775-9bcb-e9dd723547htui")
            rec.avg_density_unit = rec._get_unit("254gt2547-372f-4775-9bcb-e9dd70e3587g")
            rec.avg_specific_gravity_unit = rec._get_unit("63254170yt0-372f-4775-9bcb-e9dd723547htui")
            rec.initial_time_unit = rec._get_unit("40ce7425-30fe-4043-b518-015f5c60d916")
            rec.final_time_unit = rec._get_unit("d339933c-5e9c-4335-9ea2-2d87624c3061")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res.update({
            'avg_fineness_unit':    self._get_unit("a9e97cea-372f-4775-9bcb-e9dd70e6e6df"),
            'avg_fineness_blaine_unit':        self._get_unit("32457fg-372f-4775-9bcb-e9dd70214578r"),
            'avg_soundness_cement_unit':       self._get_unit("23547gtyu-372f-4775-9bcb-e9dd723547htui"),
            'consitency_of_cement_unit': self._get_unit("3214578nbhgt2-372f-4775-9bcb-e9dd723547htui"),
            'avg_3_days_unit':        self._get_unit("0124578hgggt-372f-4775-9bcb-e9dd723547htui"),
            'avg_7_days_unit':        self._get_unit("30124587hhhy-372f-4775-9bcb-e9dd723547htui"),
            'avg_28_days_unit':        self._get_unit("3012456998ffff-372f-4775-9bcb-e9dd723547htui"),
            'avg_density_unit':        self._get_unit("254gt2547-372f-4775-9bcb-e9dd70e3587g"),
            'avg_specific_gravity_unit':        self._get_unit("63254170yt0-372f-4775-9bcb-e9dd723547htui"),
            'initial_time_unit':        self._get_unit("40ce7425-30fe-4043-b518-015f5c60d916"),
            'final_time_unit':        self._get_unit("d339933c-5e9c-4335-9ea2-2d87624c3061"),
        })
        return res

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id
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

    fneness_cement_lines = fields.One2many('fineness.cement.line','parent_id',string="Fineness Cement")

    avg_cement = fields.Float(string="Avg Fineness Cement",compute="_compute_avg_wt_of_residue")

    avg_cement_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity', default='fail',compute="_compute_avg_cement_conformity")

    avg_cement_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_cement_nabl")


    @api.depends('avg_cement','eln_ref','grade')
    def _compute_avg_cement_conformity(self):
        for record in self:


            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_cement_conformity = 'na'
                continue
             


            record.avg_cement_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a9e97cea-372f-4775-9bcb-e9dd70e6e6df')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a9e97cea-372f-4775-9bcb-e9dd70e6e6df')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a9e97cea-372f-4775-9bcb-e9dd70e6e6df')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a9e97cea-372f-4775-9bcb-e9dd70e6e6df')]).parameter_table
            
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

    density_cement_lines = fields.One2many('density.cement.line','parent_id',string="Fineness density")

    avg_density = fields.Float(string="Density of Cement",compute="_compute_avg_density")

    # specific_gravity = fields.Float(string="Specific Gravity of Cement",compute="_compute_cement_specific")

    avg_density_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity', default='fail',compute="_compute_avg_density_conformity")

    avg_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_density_nabl")


    @api.depends('avg_density','eln_ref','grade')
    def _compute_avg_density_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_density_conformity = 'na'
                continue
             


            record.avg_density_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254gt2547-372f-4775-9bcb-e9dd70e3587g')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254gt2547-372f-4775-9bcb-e9dd70e3587g')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_density - record.avg_density*mu_value
                    upper = record.avg_density + record.avg_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_density_conformity = 'pass'
                        break
                    else:
                        record.avg_density_conformity = 'fail'

    @api.depends('avg_density','eln_ref','grade')
    def _compute_avg_density_nabl(self):
        
        for record in self:
            record.avg_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254gt2547-372f-4775-9bcb-e9dd70e3587g')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254gt2547-372f-4775-9bcb-e9dd70e3587g')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_density - record.avg_density*mu_value
            upper = record.avg_density + record.avg_density*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_density_nabl = 'pass'
                break
            else:
                record.avg_density_nabl = 'fail'

    @api.depends('density_cement_lines.density')
    def _compute_avg_density(self):
        for rec in self:
            values = [line.density for line in rec.density_cement_lines if line.density is not None]
            rec.avg_density = sum(values) / len(values) if values else 0.0




    ## Fineness by Blaine's Air Permeability

    fineness_blaine_name = fields.Char("Name",default="Fineness by Blaine's Air Permeability")
    fineness_blaine_visible = fields.Boolean("Fineness by Blaine's Air Permeability Visible",compute="_compute_visible")

    fineness_blaine_lines = fields.One2many('fineness.blaine.line','parent_id',string="Fineness blaine")

    avg_fineness_blaine = fields.Float(string="Fineness of Cement ",compute="_compute_avg_fineness_blaine")

    avg_fineness_blaine_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ],  string='Conformity', default='fail',compute="_compute_avg_fineness_blaine_conformity")

    avg_fineness_blaine_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_fineness_blaine_nabl")


    @api.depends('avg_fineness_blaine','eln_ref','grade')
    def _compute_avg_fineness_blaine_conformity(self):
        for record in self:


            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_fineness_blaine_conformity = 'na'
                continue
             
            record.avg_fineness_blaine_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32457fg-372f-4775-9bcb-e9dd70214578r')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32457fg-372f-4775-9bcb-e9dd70214578r')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32457fg-372f-4775-9bcb-e9dd70214578r')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32457fg-372f-4775-9bcb-e9dd70214578r')]).parameter_table
            
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

    soundness_cement_lines = fields.One2many('soundness.cement.line','parent_id',string="Soundness")

    avg_soundness_cement = fields.Float(string="Soundness of Cement ",compute="_compute_avg_soundness_cement")

    avg_soundness_cement_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ],  string='Conformity', default='fail',compute="_compute_avg_soundness_cement_conformity")

    avg_soundness_cement_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_soundness_cement_nabl")


    @api.depends('avg_soundness_cement','eln_ref','grade')
    def _compute_avg_soundness_cement_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_soundness_cement_conformity = 'na'
                continue
             

            record.avg_soundness_cement_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23547gtyu-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23547gtyu-372f-4775-9bcb-e9dd723547htui')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23547gtyu-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23547gtyu-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            
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

    consistency_cement_lines = fields.One2many('consistensy.cement.line','parent_id',string="Consistency")

    consitency_of_cement = fields.Float(string="Consistency of Cement ",compute="_compute_consistency_of_cement")

    consitency_of_cement_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ],   string='Conformity', default='fail',compute="_compute_consitency_of_cement_conformity")

    consitency_of_cement_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string="NABL",compute="_compute_consitency_of_cement_nabl")


    @api.depends('consitency_of_cement','eln_ref','grade')
    def _compute_consitency_of_cement_conformity(self):
        for record in self:


            if not record.eln_ref or not record.eln_ref.conformity:
                record.consitency_of_cement_conformity = 'na'
                continue
             

            record.consitency_of_cement_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214578nbhgt2-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214578nbhgt2-372f-4775-9bcb-e9dd723547htui')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214578nbhgt2-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3214578nbhgt2-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            
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





     ### setting Time,Final Setting Time	

    setting_time_name = fields.Char("Name", default="Setting Time")

    intial_time_lines = fields.One2many('initial.time.line','parent_id',string="Initial Time")

    final_time_lines = fields.One2many('final.time.line','parent_id',string="Initial Time")

    initial_setting_time_visible = fields.Boolean("Initial Setting Time Visible",compute="_compute_visible")
    initial_setting_time_name = fields.Char("Name",default="Initial Setting Time")

    temp_percent_setting = fields.Float("Temperature °C",digits=(16,1))
    humidity_percent_setting = fields.Float("Humidity %")
    start_date_setting = fields.Date("Start Date")
    end_date_setting = fields.Date("End Date")

    # wt_of_cement_setting_time = fields.Float("Wt. of Cement(g)",default=400)
    # wt_of_water_required_setting_time = fields.Float("Wt.of water required (g) (0.85*P%)" , compute="_compute_wt_of_water_required",store=True )

    # @api.depends('normal_consistency_trial1','wt_of_cement_setting_time')
    # def _compute_wt_of_water_required(self):
    #     for record in self:
    #         record.wt_of_water_required_setting_time =  (((0.85 * record.normal_consistency_trial1) / 100) * record.wt_of_cement_setting_time)

    #Initial setting Time

    
    time_water_added = fields.Datetime("The Time When water is added to cement (t1)",compute="_compute_initial_times",store=True)
    time_needle_fails = fields.Datetime("The time at which needle fails to penetrate the test block to a point 5 ± 0.5 mm (t2)",compute="_compute_initial_times",store=True)
    initial_setting_time_hours = fields.Char("Initial Setting Time (t2-t1) (Hours)", compute="_compute_initial_setting_time")
    initial_setting_time_minutes = fields.Integer("Initial Setting Time Rounded", compute="_compute_initial_setting_time")
    initial_setting_time_minutes_unrounded = fields.Char("Initial Setting Time",compute="_compute_initial_setting_time")

    @api.depends("intial_time_lines.clock_time", "intial_time_lines.serial_no")
    def _compute_initial_times(self):
        for rec in self:
            if rec.intial_time_lines:
                sorted_lines = rec.intial_time_lines.sorted("serial_no")
                rec.time_water_added = sorted_lines[0].clock_time if sorted_lines else False
                rec.time_needle_fails = sorted_lines[-1].clock_time if sorted_lines else False
            else:
                rec.time_water_added = False
                rec.time_needle_fails = False

    initial_setting_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ],   string='Conformity', default='fail',compute="_compute_initial_setting_conformity")

    initial_setting_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL' ,compute="_compute_initial_setting_nabl" ,store=True)


    @api.depends('initial_setting_time_minutes_unrounded','eln_ref','grade')
    def _compute_initial_setting_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.initial_setting_conformity = 'na'
                continue


            record.initial_setting_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','40ce7425-30fe-4043-b518-015f5c60d916')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','40ce7425-30fe-4043-b518-015f5c60d916')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = float(record.initial_setting_time_minutes_unrounded) - float(record.initial_setting_time_minutes_unrounded)*mu_value
                    upper = float(record.initial_setting_time_minutes_unrounded) + float(record.initial_setting_time_minutes_unrounded)*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.initial_setting_conformity = 'pass'
                        break
                    else:
                        record.initial_setting_conformity = 'fail'

    @api.depends('initial_setting_time_minutes_unrounded','eln_ref','grade')
    def _compute_initial_setting_nabl(self):
        
        for record in self:
            record.initial_setting_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','40ce7425-30fe-4043-b518-015f5c60d916')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','40ce7425-30fe-4043-b518-015f5c60d916')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = float(record.initial_setting_time_minutes_unrounded) - float(record.initial_setting_time_minutes_unrounded)*mu_value
            upper = float(record.initial_setting_time_minutes_unrounded) + float(record.initial_setting_time_minutes_unrounded)*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.initial_setting_nabl = 'pass'
                break
            else:
                record.initial_setting_nabl = 'fail'


    @api.depends('time_water_added', 'time_needle_fails')
    def _compute_initial_setting_time(self):
        for record in self:
            if record.time_water_added and record.time_needle_fails:
                t1 = record.time_water_added
                t2 = record.time_needle_fails
                time_difference = t2 - t1

                # Convert time difference to seconds and then to minutes
                time_difference_minutes = time_difference.total_seconds() / 60

                initial_setting_time_hours = time_difference.total_seconds() / 3600
                time_delta = timedelta(hours=initial_setting_time_hours)
                record.initial_setting_time_hours = "{:0}:{:02}".format(int(time_delta.total_seconds() // 3600), int((time_delta.total_seconds() % 3600) // 60))
                if time_difference_minutes % 5 == 0:
                    record.initial_setting_time_minutes = time_difference_minutes
                else:
                    record.initial_setting_time_minutes = round(time_difference_minutes / 5) * 5

                record.initial_setting_time_minutes_unrounded = time_difference_minutes

            else:
                record.initial_setting_time_hours = False
                record.initial_setting_time_minutes = False
                record.initial_setting_time_minutes_unrounded = False



    #Final setting Time

    final_setting_time_visible = fields.Boolean("Final Setting Time Visible",compute="_compute_visible")
    final_setting_time_name = fields.Char("Name",default="Final Setting Time")

    time_needle_make_impression = fields.Datetime("The Time at which the needle make an impression on the surface of test block while attachment fails to do (t3)",compute="_compute_final_time",store=True)
    final_setting_time_hours = fields.Char("Final Setting Time (t3-t1) (Hours)",compute="_compute_final_setting_time")
    final_setting_time_minutes_unrounded = fields.Char("Final Setting Time",compute="_compute_final_setting_time")
    final_setting_time_minutes = fields.Char("Final Setting Time Rounded",compute="_compute_final_setting_time")

    @api.depends("final_time_lines.clock_time1", "final_time_lines.serial_no")
    def _compute_final_time(self):
        for rec in self:
            if rec.final_time_lines:
                # Sort lines by serial_no
                sorted_lines = rec.final_time_lines.sorted("serial_no")
                rec.time_needle_make_impression = sorted_lines[-1].clock_time1
            else:
                rec.time_needle_make_impression = False

    final_setting_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity', default='fail',compute="_compute_final_setting_conformity")

    final_setting_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', compute="_compute_final_setting_nabl")


    @api.depends('final_setting_time_minutes_unrounded','eln_ref','grade')
    def _compute_final_setting_conformity(self):
        for record in self:


            if not record.eln_ref or not record.eln_ref.conformity:
                record.final_setting_conformity = 'na'
                continue
             

            record.final_setting_conformity = 'fail'
            line = self.env['lerm.parameter.master'].search([('internal_id','=','d339933c-5e9c-4335-9ea2-2d87624c3061')])
            materials = self.env['lerm.parameter.master'].search([('internal_id','=','d339933c-5e9c-4335-9ea2-2d87624c3061')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = float(record.final_setting_time_minutes_unrounded) - float(record.final_setting_time_minutes_unrounded)*mu_value
                    upper = float(record.final_setting_time_minutes_unrounded) + float(record.final_setting_time_minutes_unrounded)*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.final_setting_conformity = 'pass'
                        break
                    else:
                        record.final_setting_conformity = 'fail'

    @api.depends('final_setting_time_minutes_unrounded','eln_ref','grade')
    def _compute_final_setting_nabl(self):
        
        for record in self:
            record.final_setting_nabl = 'fail'
            line = self.env['lerm.parameter.master'].search([('internal_id','=','d339933c-5e9c-4335-9ea2-2d87624c3061')])
            materials = self.env['lerm.parameter.master'].search([('internal_id','=','d339933c-5e9c-4335-9ea2-2d87624c3061')]).parameter_table
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            lower = float(record.final_setting_time_minutes_unrounded) - float(record.final_setting_time_minutes_unrounded)*mu_value
            upper = float(record.final_setting_time_minutes_unrounded) + float(record.final_setting_time_minutes_unrounded)*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.final_setting_nabl = 'pass'
                break
            else:
                record.final_setting_nabl = 'fail'



    @api.depends('time_needle_make_impression')
    def _compute_final_setting_time(self):
        for record in self:
            if record.time_needle_make_impression and record.time_water_added:
                t1 = record.time_water_added
                t2 = record.time_needle_make_impression
                time_difference = t2 - t1
                record.final_setting_time_minutes = time_difference
                record.final_setting_time_hours = time_difference
                final_setting_time_decimal = time_difference.total_seconds() / 60
                final_setting_time = int(final_setting_time_decimal)
                if final_setting_time % 5 == 0:
                    record.final_setting_time_minutes = final_setting_time
                else:
                    record.final_setting_time_minutes =  round(final_setting_time / 5) * 5
                record.final_setting_time_minutes_unrounded = final_setting_time
            else:
                record.final_setting_time_hours = False
                record.final_setting_time_minutes = False
                record.final_setting_time_minutes_unrounded = False

       # Specific gravity of Cement

    specific_gravity_name = fields.Char("Name",default="Specific Gravity of Cement")
    specific_gravity_visible = fields.Boolean("Specific gravity of Cement Visible",compute="_compute_visible")

    wt_of_empty_bottle = fields.Float(string="Weight of empty bottle (W₁ g)")
    wt_of_bottle_cement = fields.Float(string="Weight of bottle + Cement ( W₂ g)")
    wt_of_specific_bpttle = fields.Float(string="Weight of Specific gravity bottle + Cement + Kerosene ( W₃ g)")
    wt_of_kerosene = fields.Float(string="Weight of bottle + Full Kerosene( W₄ g)")
    wt_of_bottle_water = fields.Float(string="Weight of bottle + Full Water ( W₅ g)")

    specific_gravity = fields.Float(string="Specific gravity ",compute="_compute_specific_gravity",digits=(12,3))

    @api.depends('wt_of_empty_bottle', 'wt_of_bottle_cement', 'wt_of_specific_bpttle', 'wt_of_kerosene')
    def _compute_specific_gravity(self):
        for rec in self:
            if rec.wt_of_empty_bottle and rec.wt_of_bottle_cement and rec.wt_of_specific_bpttle and rec.wt_of_kerosene:
                numerator = rec.wt_of_bottle_cement - rec.wt_of_empty_bottle
                denominator = ((rec.wt_of_bottle_cement - rec.wt_of_empty_bottle) - (rec.wt_of_specific_bpttle - rec.wt_of_kerosene)) * 0.79
                rec.specific_gravity = numerator / denominator if denominator else 0.0
            else:
                rec.specific_gravity = 0.0




    wt_of_empty_bottle1 = fields.Float(string="Weight of empty bottle (W₁ g)")
    wt_of_bottle_cement1 = fields.Float(string="Weight of bottle + Cement ( W₂ g)")
    wt_of_specific_bpttle1 = fields.Float(string="Weight of Specific gravity bottle + Cement + Kerosene ( W₃ g)")
    wt_of_kerosene1 = fields.Float(string="Weight of bottle + Full Kerosene( W₄ g)")
    wt_of_bottle_water1 = fields.Float(string="Weight of bottle + Full Water ( W₅ g)")

    specific_gravity1 = fields.Float(string="Specific gravity ",compute="_compute_specific_gravity1",digits=(12,3))

    @api.depends('wt_of_empty_bottle1', 'wt_of_bottle_cement1', 'wt_of_specific_bpttle1', 'wt_of_kerosene1')
    def _compute_specific_gravity1(self):
        for rec in self:
            if rec.wt_of_empty_bottle1 and rec.wt_of_bottle_cement1 and rec.wt_of_specific_bpttle1 and rec.wt_of_kerosene1:
                numerator1 = rec.wt_of_bottle_cement1 - rec.wt_of_empty_bottle1
                denominator1 = ((rec.wt_of_bottle_cement1 - rec.wt_of_empty_bottle1) - (rec.wt_of_specific_bpttle1 - rec.wt_of_kerosene1)) * 0.79
                rec.specific_gravity1 = numerator1 / denominator1 if denominator1 else 0.0
            else:
                rec.specific_gravity1 = 0.0

    avg_specific_gravity = fields.Float(string="Avg Specific gravity",compute="_compute_avg_specific_gravity",digits=(12,3))

    # Average
    @api.depends('specific_gravity', 'specific_gravity1')
    def _compute_avg_specific_gravity(self):
        for rec in self:
            if rec.specific_gravity and rec.specific_gravity1:
                rec.avg_specific_gravity = (rec.specific_gravity + rec.specific_gravity1) / 2
            else:
                rec.avg_specific_gravity = 0.0


    avg_specific_gravity_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ],  string='Conformity', default='fail',compute="_compute_avg_specific_gravity_conformity")

    avg_specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string="NABL",compute="_compute_avg_specific_gravity_nabl")


    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_conformity(self):
        for record in self:


            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_specific_gravity_conformity = 'na'
                continue
             

            record.avg_specific_gravity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','63254170yt0-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','63254170yt0-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avg_specific_gravity - record.avg_specific_gravity*mu_value
                    upper = record.avg_specific_gravity + record.avg_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_specific_gravity_conformity = 'pass'
                        break
                    else:
                        record.avg_specific_gravity_conformity = 'fail'

    @api.depends('avg_specific_gravity','eln_ref','grade')
    def _compute_avg_specific_gravity_nabl(self):
        
        for record in self:
            record.avg_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','63254170yt0-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','63254170yt0-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_specific_gravity - record.avg_specific_gravity*mu_value
            upper = record.avg_specific_gravity + record.avg_specific_gravity*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_specific_gravity_nabl = 'pass'
                break
            else:
                record.avg_specific_gravity_nabl = 'fail'

    




                ## Cement Compressive Strength

    compressive_name = fields.Char("Name",default="Cement Compressive Strength")
    compressive_visible = fields.Boolean("Cement Compressive Strength Visible",compute="_compute_visible")

    compressive_lines = fields.One2many('compressive.line','parent_id',string="Compressive")

    @api.onchange('start_date', 'compressive_lines')
    def _onchange_start_date_or_lines(self):
        for line in self.compressive_lines:
            if not line.dt_of_casting:  
                line.dt_of_casting = self.start_date

    avg_3_days = fields.Float(string="Avg Strength (3 Days)", compute="_compute_avg_strengths", store=True)

    avg_3_days_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ],   string='Conformity', default='fail',compute="_compute_avg_3_days_conformity")

    avg_3_days_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_3_days_nabl")


    @api.depends('avg_3_days','eln_ref','grade')
    def _compute_avg_3_days_conformity(self):
        for record in self:


            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_3_days_conformity = 'na'
                continue


            record.avg_3_days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0124578hgggt-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0124578hgggt-372f-4775-9bcb-e9dd723547htui')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0124578hgggt-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0124578hgggt-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            
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
        ('na', 'NA'),
    ],   string='Conformity', default='fail',compute="_compute_avg_7_days_conformity")

    avg_7_days_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_7_days_nabl")


    @api.depends('avg_7_days','eln_ref','grade')
    def _compute_avg_7_days_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_7_days_conformity = 'na'
                continue


            record.avg_7_days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30124587hhhy-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30124587hhhy-372f-4775-9bcb-e9dd723547htui')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30124587hhhy-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30124587hhhy-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            
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
        ('na', 'NA'),
    ],  string='Conformity', default='fail',compute="_compute_avg_28_days_conformity")

    avg_28_days_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avg_28_days_nabl")


    @api.depends('avg_28_days','eln_ref','grade')
    def _compute_avg_28_days_conformity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_28_days_conformity = 'na'
                continue
              

            record.avg_28_days_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3012456998ffff-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3012456998ffff-372f-4775-9bcb-e9dd723547htui')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3012456998ffff-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3012456998ffff-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            
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
            record.final_setting_time_visible = False
            record.compressive_visible = False
            record.initial_setting_time_visible = False
            record.specific_gravity_visible = False
         
            

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == 'a9e97cea-372f-4775-9bcb-e9dd70e6e6df':
                    record.fineness_cement_visible = True

                if sample.internal_id == '254gt2547-372f-4775-9bcb-e9dd70e3587g':
                    record.density_cement_visible = True

                if sample.internal_id == '32457fg-372f-4775-9bcb-e9dd70214578r':
                    record.density_cement_visible = True
                    record.fineness_blaine_visible = True

                if sample.internal_id == '23547gtyu-372f-4775-9bcb-e9dd723547htui':
                    record.soundness_cement_visible = True

                if sample.internal_id == '3214578nbhgt2-372f-4775-9bcb-e9dd723547htui':
                    record.consistency_cement_visible = True

                if sample.internal_id == 'd339933c-5e9c-4335-9ea2-2d87624c3061':
                    record.consistency_cement_visible = True
                    record.final_setting_time_visible = True

                if sample.internal_id == '40ce7425-30fe-4043-b518-015f5c60d916':
                    record.consistency_cement_visible = True
                    record.initial_setting_time_visible = True

                if sample.internal_id == '2014587ghty1-372f-4775-9bcb-e9dd723547htui':
                    record.compressive_visible = True

                if sample.internal_id == '63254170yt0-372f-4775-9bcb-e9dd723547htui':
                    record.specific_gravity_visible = True
             

    def open_eln_page(self):
    # import wdb; wdb.set_trace()
        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == 'a9e97cea-372f-4775-9bcb-e9dd70e6e6df':
                result.result_char = round(self.avg_cement,2)
                if self.avg_cement_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '254gt2547-372f-4775-9bcb-e9dd70e3587g':
                result.result_char = round(self.avg_density,2)
                if self.avg_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '32457fg-372f-4775-9bcb-e9dd70214578r':
                result.result_char = round(self.avg_fineness_blaine,2)
                if self.avg_fineness_blaine_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '23547gtyu-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.avg_soundness_cement,2)
                if self.avg_soundness_cement_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '3214578nbhgt2-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.consitency_of_cement,2)
                if self.consitency_of_cement_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

          
            if result.parameter.internal_id == '0124578hgggt-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.avg_3_days,2)
                if self.avg_3_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '30124587hhhy-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.avg_7_days,2)
                if self.avg_7_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == '3012456998ffff-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.avg_28_days,2)
                if self.avg_28_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '40ce7425-30fe-4043-b518-015f5c60d916':
                result.result_char = self.initial_setting_time_minutes_unrounded
                if self.initial_setting_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue
            if result.parameter.internal_id == 'd339933c-5e9c-4335-9ea2-2d87624c3061':
                result.result_char = self.final_setting_time_minutes_unrounded
                if self.final_setting_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '63254170yt0-372f-4775-9bcb-e9dd723547htui':
                result.result_char = self.avg_specific_gravity
                if self.avg_specific_gravity_nabl == 'pass':
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
        record = super(CementNormalConsistency, self).create(vals)
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
        record = self.env['cement.opc'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value
        return field_values


class FinenessCementLine(models.Model):
    _name = "fineness.cement.line"
    parent_id = fields.Many2one('cement.opc',string="Parent Id")

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
    _name = "density.cement.line"
    parent_id = fields.Many2one('cement.opc',string="Parent Id")

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
    _name = "fineness.blaine.line"
    parent_id = fields.Many2one('cement.opc',string="Parent Id")

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
    _name = "soundness.cement.line"
    parent_id = fields.Many2one('cement.opc',string="Parent Id")

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
    _name = "consistensy.cement.line"
    parent_id = fields.Many2one('cement.opc',string="Parent Id")

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

# class SettingTimetLine(models.Model):
#     _name = "setting.time.ssl.line"
#     parent_id = fields.Many2one('cement.opc',string="Parent Id")

#     serial_no = fields.Char(string="Test NO")

   
    
#     wt_of_cements1 = fields.Float(string="Wt of cement in gms")
#     wt_of_water1 = fields.Float(string="wt of water in ml" ,compute="_compute_wt_of_water1")
#     water_mix1 = fields.Char(string="% of water mix")
#     needle_penitration1 = fields.Char(string="Needle penetration in mm")
#     duration1 = fields.Float(string="Duration of time in minutes")

   

#     @api.depends('wt_of_cements1', 'parent_id.consitency_of_cement')
#     def _compute_wt_of_water1(self):
#         for rec in self:
#             if rec.wt_of_cements1 and rec.parent_id.consitency_of_cement:
#                 rec.wt_of_water1 = rec.wt_of_cements1 * 0.85 * rec.parent_id.consitency_of_cement / 100
#             else:
#                 rec.wt_of_water1 = 0.0



class CompressiveCementLine(models.Model):
    _name = "compressive.line"
    parent_id = fields.Many2one('cement.opc',string="Parent Id")

    serial_no = fields.Integer(string="Specimen No", readonly=True, copy=False, default=1)

   
    
    dt_of_casting = fields.Date(string="Date of Casting ")
    days = fields.Integer(string="Days")
    dt_of_testing = fields.Date(string="Date of Testing")
    wt_of_cube = fields.Float(string="Wt of cube")
    area = fields.Float(string="Area",compute="_compute_area",store=True)
    load = fields.Float(string="Load in KN")
    strenght = fields.Float(string="Strength N/mm2",compute="_compute_strength")

    # @api.onchange('parent_id')
    # def _onchange_set_dt_of_casting(self):
    #     if self.parent_id and self.parent_id.start_date:
    #         self.dt_of_casting = self.parent_id.start_date

    

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

class InitialTimeLine(models.Model):
    _name = "initial.time.line"
    parent_id = fields.Many2one('cement.opc',string="Parent Id")

    serial_no = fields.Integer(string="Sr.No", readonly=True, copy=False, default=1)

   
    
    clock_time = fields.Datetime(string="Date & Time")
    time_in_minutes = fields.Char("Time In minutes",compute="_compute_time_in_minutes",store=True)
    penetration_intial = fields.Float(string="Penetration Of Needle")


    @api.depends('clock_time', 'parent_id.intial_time_lines.clock_time')
    def _compute_time_in_minutes(self):
      
        for rec in self:
            rec.time_in_minutes = 0.0
            if rec.parent_id:
                first_line = rec.parent_id.intial_time_lines.sorted('serial_no')[:1]
                if first_line and first_line.clock_time and rec.clock_time:
                    diff = (rec.clock_time - first_line.clock_time).total_seconds() / 60.0
                    rec.time_in_minutes = round(diff, 2)

    

    


    

   


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(InitialTimeLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class FinalTimeLine(models.Model):
    _name = "final.time.line"
    parent_id = fields.Many2one('cement.opc',string="Parent Id")

    serial_no = fields.Integer(string="Sr.No", readonly=True, copy=False, default=1)

   
    
    clock_time1 = fields.Datetime(string="Date & Time")
    time_in_minutes1 = fields.Char("Time In minutes",compute="_compute_time_in_minutes1",store=True)
    impression_intial1 = fields.Float(string="Impression Of Needle")

    @api.depends('clock_time1', 'parent_id.intial_time_lines.clock_time')
    def _compute_time_in_minutes1(self):
      
        for rec in self:
            rec.time_in_minutes1 = 0.0
            if rec.parent_id:
                init_first = rec.parent_id.intial_time_lines.sorted('serial_no')[:1]
                if init_first and init_first.clock_time and rec.clock_time1:
                    diff = (rec.clock_time1 - init_first.clock_time).total_seconds() / 60.0
                    rec.time_in_minutes1 = round(diff, 2)

    


    

   


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(FinalTimeLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1
    
    

   







  