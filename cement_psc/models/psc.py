from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta
import math
from statistics import mean
from statistics import mean
from math import sqrt


class CementPSC(models.Model):
    _name = "cement.psc"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Cement")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    start_date = fields.Date(string="Start Date", compute="_compute_start_date", store=True)

    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")
    date_of_testing = fields.Date(string="Date of Testing",compute="_compute_date_testing")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)


    @api.depends('eln_ref')
    def _compute_date_testing(self):
        if self.eln_ref:
            self.date_of_testing = self.eln_ref.date_testing
        else:
            self.date_of_testing = ''

    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'cement.psc.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    @api.depends('eln_ref.start_date')
    def _compute_start_date(self):
        for rec in self:
            rec.start_date = rec.eln_ref.start_date


  
    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id



    # Fineness of Cement by Dry Sieving

    fineness_cement_name = fields.Char("Name",default="Fineness of Cement by Dry Sieving")
    fineness_cement_visible = fields.Boolean("Plan Area Visible",compute="_compute_visible")

    fneness_cement_lines = fields.One2many('fineness.cement.psc.line','parent_id',string="Fineness Cement")

    avg_fineness = fields.Float(
        string="Average Fineness (%)",
        compute="_compute_avg_fineness",
        store=True
    )

    @api.depends('fneness_cement_lines.fineness')
    def _compute_avg_fineness(self):
        for record in self:
            if record.fneness_cement_lines:
                record.avg_fineness = sum(record.fneness_cement_lines.mapped('fineness')) / len(record.fneness_cement_lines)
            else:
                record.avg_fineness = 0.0



    avg_fineness_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_fineness_confirmity")
    
    @api.depends('avg_fineness','eln_ref','grade')
    def _compute_avg_fineness_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_fineness_confirmity = 'na'
                continue
            record.avg_fineness_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12457800-372f-4775-9bcb-e9dd70e6e6df')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12457800-372f-4775-9bcb-e9dd70e6e6df')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_fineness - record.avg_fineness*mu_value
                    upper = record.avg_fineness + record.avg_fineness*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_fineness_confirmity = 'pass'
                        break
                    else:
                        record.avg_fineness_confirmity = 'fail'

    avg_fineness_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_fineness_nabl",store=True)

    @api.depends('avg_fineness','eln_ref','grade')
    def _compute_avg_fineness_nabl(self):
        
        for record in self:
            record.avg_fineness_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12457800-372f-4775-9bcb-e9dd70e6e6df')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','12457800-372f-4775-9bcb-e9dd70e6e6df')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_fineness - record.avg_fineness*mu_value
                    upper = record.avg_fineness + record.avg_fineness*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_fineness_nabl = 'pass'
                        break
                    else:
                        record.avg_fineness_nabl = 'fail'


        # Consistency of cement

    consistency_cement_name = fields.Char("Name",default="Consistency of Cement")
    consistency_cement_visible = fields.Boolean("Consistency of cement Visible",compute="_compute_visible")

    consistency_cement_lines = fields.One2many('consistensy.cement.psc.line','parent_id',string="Consistency")

    average_consistency = fields.Float(
        string="Final Consistency (%)",
        compute="_compute_average_consistency",
        store=True
    )

    @api.depends('consistency_cement_lines.consistency')
    def _compute_average_consistency(self):
     for rec in self:
        if rec.consistency_cement_lines:
            rec.average_consistency = rec.consistency_cement_lines[-1].consistency
        else:
            rec.average_consistency = 0.0

    average_consistency_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_average_consistency_confirmity")
    
    @api.depends('average_consistency','eln_ref','grade')
    def _compute_average_consistency_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_consistency_confirmity = 'na'
                continue
            record.average_consistency_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','01247gggty-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','01247gggty-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_consistency - record.average_consistency*mu_value
                    upper = record.average_consistency + record.average_consistency*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_consistency_confirmity = 'pass'
                        break
                    else:
                        record.average_consistency_confirmity = 'fail'

    average_consistency_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_average_consistency_nabl",store=True)

    @api.depends('average_consistency','eln_ref','grade')
    def _compute_average_consistency_nabl(self):
        
        for record in self:
            record.average_consistency_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','01247gggty-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','01247gggty-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_consistency - record.average_consistency*mu_value
                    upper = record.average_consistency + record.average_consistency*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_consistency_nabl = 'pass'
                        break
                    else:
                        record.average_consistency_nabl = 'fail'


    #  Initial Setting Time And Final Setting Time

    setting_time_name = fields.Char("Name", default="Initial And Final Setting Time")
    setting_time_visible = fields.Boolean("Setting Time Visible",compute="_compute_visible")

    intial_time_lines = fields.One2many('cement.psc.setting.time.initial.line','parent_id',string="Initial Time")

    final_time_lines = fields.One2many('cement.psc.setting.time.final.line','parent_id',string="Initial Time")


    cement_weight = fields.Float(
        string="Weight of Cement (g)"
    )

    set_normal_consistency = fields.Float(
        string="Normal Consistency (%)"
    )

    weight_of_water = fields.Float(
        string="Weight of Water Added (0.85 x Normal Consistency)",
        compute="_compute_weight_of_water",
        store=True,
        readonly=True,
    )

    @api.depends("cement_weight", "set_normal_consistency")
    def _compute_weight_of_water(self):
        for rec in self:
            rec.weight_of_water = (
                rec.cement_weight
                * rec.set_normal_consistency
                * 0.85
                / 100.0
            )


    initial_setting_time = fields.Float(
        string="Initial Setting Time (Min)",
        compute="_compute_setting_time",
        store=True,
        readonly=True,
    )

    final_setting_time = fields.Float(
        string="Final Setting Time (Min)",
        compute="_compute_setting_time",
        store=True,
        readonly=True,
    )

    @api.depends(
    'intial_time_lines',
    'intial_time_lines.elapsed_time',
    'final_time_lines',
    'final_time_lines.elapsed_time',
)
    def _compute_setting_time(self):
     for rec in self:
        rec.initial_setting_time = 0.0
        rec.final_setting_time = 0.0

        # Last Initial row
        if rec.intial_time_lines:
            last_initial = rec.intial_time_lines[-1]
            rec.initial_setting_time = last_initial.elapsed_time or 0.0

        # Last Final row
        if rec.final_time_lines:
            last_final = rec.final_time_lines[-1]
            rec.final_setting_time = last_final.elapsed_time or 0.0


    initial_setting_time_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_initial_setting_time_confirmity")
    
    @api.depends('initial_setting_time','eln_ref','grade')
    def _compute_initial_setting_time_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.initial_setting_time_confirmity = 'na'
                continue
            record.initial_setting_time_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','psc5478-30fe-4043-b518-015f5c60d916')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','psc5478-30fe-4043-b518-015f5c60d916')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.initial_setting_time - record.initial_setting_time*mu_value
                    upper = record.initial_setting_time + record.initial_setting_time*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.initial_setting_time_confirmity = 'pass'
                        break
                    else:
                        record.initial_setting_time_confirmity = 'fail'

    initial_setting_time_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_initial_setting_time_nabl",store=True)

    @api.depends('initial_setting_time','eln_ref','grade')
    def _compute_initial_setting_time_nabl(self):
        
        for record in self:
            record.initial_setting_time_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','psc5478-30fe-4043-b518-015f5c60d916')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','psc5478-30fe-4043-b518-015f5c60d916')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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

    final_setting_time_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_final_setting_time_confirmity")
    
    @api.depends('final_setting_time','eln_ref','grade')
    def _compute_final_setting_time_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.final_setting_time_confirmity = 'na'
                continue
            record.final_setting_time_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','987psc47-5e9c-4335-9ea2-2d87624c3061')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','987psc47-5e9c-4335-9ea2-2d87624c3061')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.final_setting_time - record.final_setting_time*mu_value
                    upper = record.final_setting_time + record.final_setting_time*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.final_setting_time_confirmity = 'pass'
                        break
                    else:
                        record.final_setting_time_confirmity = 'fail'

    final_setting_time_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_final_setting_time_nabl",store=True)

    @api.depends('final_setting_time','eln_ref','grade')
    def _compute_final_setting_time_nabl(self):
        
        for record in self:
            record.final_setting_time_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','987psc47-5e9c-4335-9ea2-2d87624c3061')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','987psc47-5e9c-4335-9ea2-2d87624c3061')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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


    # Compressive Strength Of Cement

    compressive_name = fields.Char("Name",default="Compressive Strength Of Cement")
    compressive_visible = fields.Boolean("Compressive Strength Of Cement Visible",compute="_compute_visible")

    compressive_lines = fields.One2many('compressive.psc.line','parent_id',string="Compressive",default=lambda self: self.compressive_lines_days())

    @api.model
    def compressive_lines_days(self):
        default_lines = [
            (0, 0, {'days': '3 Days'}),
            (0, 0, {'days': '3 Days'}),
            (0, 0, {'days': '3 Days'}),
            (0, 0, {'days': '7 Days'}),
            (0, 0, {'days': '7 Days'}),
            (0, 0, {'days': '7 Days'}),
            (0, 0, {'days': '14 Days'}),
            (0, 0, {'days': '14 Days'}),
            (0, 0, {'days': '14 Days'}),
            (0, 0, {'days': '28 Days'}),
            (0, 0, {'days': '28 Days'}),
            (0, 0, {'days': '28 Days'}),
            
        ]
        return default_lines 

    @api.onchange('start_date', 'compressive_lines')
    def _onchange_start_date_or_lines(self):
        for line in self.compressive_lines:
            if not line.dt_of_casting:  
                line.dt_of_casting = self.start_date

    avg_3_days = fields.Float(string="Avg Compressive Strength (3 Days)", compute="_compute_avg_strengths", store=True)

    avg_7_days = fields.Float(string="Avg Compressive Strength (7 Days)", compute="_compute_avg_strengths", store=True)

    avg_14_days = fields.Float(string="Avg Compressive Strength (14 Days)", compute="_compute_avg_strengths", store=True)

    avg_28_days = fields.Float(string="Avg Compressive Strength (28 Days)", compute="_compute_avg_strengths", store=True)


    @api.depends('compressive_lines.days', 'compressive_lines.compressive_strength')
    def _compute_avg_strengths(self):
        for rec in self:
            strengths_3 = [line.compressive_strength for line in rec.compressive_lines if line.days == '3 Days' and line.compressive_strength]
            strengths_7 = [line.compressive_strength for line in rec.compressive_lines if line.days == '7 Days' and line.compressive_strength]
            strengths_14 = [line.compressive_strength for line in rec.compressive_lines if line.days == '14 Days' and line.compressive_strength]
            strengths_28 = [line.compressive_strength for line in rec.compressive_lines if line.days == '28 Days' and line.compressive_strength]

            rec.avg_3_days = mean(strengths_3) if strengths_3 else 0.0
            rec.avg_7_days = mean(strengths_7) if strengths_7 else 0.0
            rec.avg_14_days = mean(strengths_14) if strengths_14 else 0.0
            rec.avg_28_days = mean(strengths_28) if strengths_28 else 0.0

    avg_3_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_3_days_confirmity")
    
    @api.depends('avg_3_days','eln_ref','grade')
    def _compute_avg_3_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_3_days_confirmity = 'na'
                continue
            record.avg_3_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','358789gtyg-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','358789gtyg-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_3_days - record.avg_3_days*mu_value
                    upper = record.avg_3_days + record.avg_3_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_3_days_confirmity = 'pass'
                        break
                    else:
                        record.avg_3_days_confirmity = 'fail'

    avg_3_days_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_3_days_nabl",store=True)

    @api.depends('avg_3_days','eln_ref','grade')
    def _compute_avg_3_days_nabl(self):
        
        for record in self:
            record.avg_3_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','358789gtyg-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','358789gtyg-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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

    

    avg_7_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_7_days_confirmity")
    
    @api.depends('avg_7_days','eln_ref','grade')
    def _compute_avg_7_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_7_days_confirmity = 'na'
                continue
            record.avg_7_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','555888ggghhjy-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','555888ggghhjy-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_7_days - record.avg_7_days*mu_value
                    upper = record.avg_7_days + record.avg_7_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_7_days_confirmity = 'pass'
                        break
                    else:
                        record.avg_7_days_confirmity = 'fail'

    avg_7_days_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_7_days_nabl",store=True)

    @api.depends('avg_7_days','eln_ref','grade')
    def _compute_avg_7_days_nabl(self):
        
        for record in self:
            record.avg_7_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','555888ggghhjy-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','555888ggghhjy-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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

   

    

    avg_14_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_14_days_confirmity")
    
    @api.depends('avg_14_days','eln_ref','grade')
    def _compute_avg_14_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_14_days_confirmity = 'na'
                continue
            record.avg_14_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a3525d21-e21a-44d3-a09c-f87afc1fbcc4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a3525d21-e21a-44d3-a09c-f87afc1fbcc4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_14_days - record.avg_14_days*mu_value
                    upper = record.avg_14_days + record.avg_14_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_14_days_confirmity = 'pass'
                        break
                    else:
                        record.avg_14_days_confirmity = 'fail'

    avg_14_days_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_14_days_nabl",store=True)

    @api.depends('avg_14_days','eln_ref','grade')
    def _compute_avg_14_days_nabl(self):
        
        for record in self:
            record.avg_14_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a3525d21-e21a-44d3-a09c-f87afc1fbcc4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a3525d21-e21a-44d3-a09c-f87afc1fbcc4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_14_days - record.avg_14_days*mu_value
                    upper = record.avg_14_days + record.avg_14_days*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_14_days_nabl = 'pass'
                        break
                    else:
                        record.avg_14_days_nabl = 'fail'


    avg_28_days_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_28_days_confirmity")
    
    @api.depends('avg_28_days','eln_ref','grade')
    def _compute_avg_28_days_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_28_days_confirmity = 'na'
                continue
            record.avg_28_days_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5777fffrrtt11-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5777fffrrtt11-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_28_days - record.avg_28_days*mu_value
                    upper = record.avg_28_days + record.avg_28_days*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_28_days_confirmity = 'pass'
                        break
                    else:
                        record.avg_28_days_confirmity = 'fail'

    avg_28_days_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_28_days_nabl",store=True)

    @api.depends('avg_28_days','eln_ref','grade')
    def _compute_avg_28_days_nabl(self):
        
        for record in self:
            record.avg_28_days_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5777fffrrtt11-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5777fffrrtt11-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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


    # SOUNDNESS OF CEMENT BY LE-CHATELIER METHOD

    soundness_cement_name = fields.Char("Name",default="SOUNDNESS OF CEMENT BY LE-CHATELIER METHOD")
    soundness_cement_visible = fields.Boolean("SOUNDNESS OF CEMENT BY LE-CHATELIER METHOD Visible",compute="_compute_visible")

    soundness_cement_lines = fields.One2many('soundness.cement.psc.line','parent_id',string="Soundness")

    avg_soundness_expansion = fields.Float(
        string="Average Expansion (mm)",
        compute="_compute_avg_soundness_expansion",
        store=True,
    )

    @api.depends("soundness_cement_lines.expansion")
    def _compute_avg_soundness_expansion(self):
        for rec in self:
            expansions = rec.soundness_cement_lines.mapped("expansion")
            if expansions:
                rec.avg_soundness_expansion = sum(expansions) / len(expansions)
            else:
                rec.avg_soundness_expansion = 0.0


    avg_soundness_expansion_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_avg_soundness_expansion_confirmity")
    
    @api.depends('avg_soundness_expansion','eln_ref','grade')
    def _compute_avg_soundness_expansion_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_soundness_expansion_confirmity = 'na'
                continue
            record.avg_soundness_expansion_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896f-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896f-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_soundness_expansion - record.avg_soundness_expansion*mu_value
                    upper = record.avg_soundness_expansion + record.avg_soundness_expansion*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_soundness_expansion_confirmity = 'pass'
                        break
                    else:
                        record.avg_soundness_expansion_confirmity = 'fail'

    avg_soundness_expansion_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_avg_soundness_expansion_nabl",store=True)

    @api.depends('avg_soundness_expansion','eln_ref','grade')
    def _compute_avg_soundness_expansion_nabl(self):
        
        for record in self:
            record.avg_soundness_expansion_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896f-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896f-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_soundness_expansion - record.avg_soundness_expansion*mu_value
                    upper = record.avg_soundness_expansion + record.avg_soundness_expansion*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_soundness_expansion_nabl = 'pass'
                        break
                    else:
                        record.avg_soundness_expansion_nabl = 'fail'


    # SPECIFIC GRAVITY OF CEMENT

    specific_gravity_name = fields.Char("Name",default="Specific Gravity of Cement")
    specific_gravity_visible = fields.Boolean("Specific Gravity of Cement Visible",compute="_compute_visible")

    specific_gravity_line_ids = fields.One2many(
        "cement.psc.specific.gravity.line",
        "parent_id",
        string="Trial Lines",
    )

    average_specific_gravity = fields.Float(
        string="Average Specific Gravity",
        compute="_compute_average_specific_gravity",
        store=True,
    )

    @api.depends("specific_gravity_line_ids.specific_gravity")
    def _compute_average_specific_gravity(self):
        for rec in self:
            values = rec.specific_gravity_line_ids.mapped("specific_gravity")
            values = [v for v in values if v]

            if values:
                rec.average_specific_gravity = sum(values) / len(values)
            else:
                rec.average_specific_gravity = 0.0


    average_specific_gravity_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_average_specific_gravity_confirmity")
    
    @api.depends('average_specific_gravity','eln_ref','grade')
    def _compute_average_specific_gravity_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_specific_gravity_confirmity = 'na'
                continue
            record.average_specific_gravity_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0157yutr1034-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0157yutr1034-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_specific_gravity - record.average_specific_gravity*mu_value
                    upper = record.average_specific_gravity + record.average_specific_gravity*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_specific_gravity_confirmity = 'pass'
                        break
                    else:
                        record.average_specific_gravity_confirmity = 'fail'

    average_specific_gravity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_average_specific_gravity_nabl",store=True)

    @api.depends('average_specific_gravity','eln_ref','grade')
    def _compute_average_specific_gravity_nabl(self):
        
        for record in self:
            record.average_specific_gravity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0157yutr1034-372f-4775-9bcb-e9dd723547htui')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0157yutr1034-372f-4775-9bcb-e9dd723547htui')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_specific_gravity - record.average_specific_gravity*mu_value
                    upper = record.average_specific_gravity + record.average_specific_gravity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_specific_gravity_nabl = 'pass'
                        break
                    else:
                        record.average_specific_gravity_nabl = 'fail'

    

        # DENSITY OF CEMENT						
    density_cement_name = fields.Char("Name",default="Density of Cement")
    density_cement_visible = fields.Boolean("Density of Cement Visible",compute="_compute_visible")

    

    density_line_ids = fields.One2many(
        "density.cement.psc.line",
        "parent_id",
        string="Trial Lines",
    )

    average_density = fields.Float(
        string="Average Specific Gravity",
        compute="_compute_average_density",
        store=True,
    )

    @api.depends("density_line_ids.specific_gravity")
    def _compute_average_density(self):
        for rec in self:
            values = rec.density_line_ids.mapped("specific_gravity")
            values = [v for v in values if v]

            if values:
                rec.average_density = sum(values) / len(values)
            else:
                rec.average_density = 0.0


    average_density_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_average_density_confirmity")
    
    @api.depends('average_density','eln_ref','grade')
    def _compute_average_density_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_density_confirmity = 'na'
                continue
            record.average_density_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23145870-372f-4775-9bcb-e9dd70e3587g')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23145870-372f-4775-9bcb-e9dd70e3587g')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_density - record.average_density*mu_value
                    upper = record.average_density + record.average_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_density_confirmity = 'pass'
                        break
                    else:
                        record.average_density_confirmity = 'fail'

    average_density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_average_density_nabl",store=True)

    @api.depends('average_density','eln_ref','grade')
    def _compute_average_density_nabl(self):
        
        for record in self:
            record.average_density_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23145870-372f-4775-9bcb-e9dd70e3587g')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23145870-372f-4775-9bcb-e9dd70e3587g')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_density - record.average_density*mu_value
                    upper = record.average_density + record.average_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_density_nabl = 'pass'
                        break
                    else:
                        record.average_density_nabl = 'fail'






    # FINENESS OF CEMENT BY BLAINE AIR PERMEABILITY METHOD	
    fineness_blaine_name = fields.Char("Name",default="Fineness by Blaine's Air Permeability")
    fineness_blaine_visible = fields.Boolean("Fineness by Blaine's Air Permeability Visible",compute="_compute_visible")

    e = fields.Float(string="e")

    eta = fields.Float(string="η (is the viscosity of air at the test temperature)",digits=(16,4))

    density = fields.Float(string="Density of Sample (ρ)")

    apparatus_constant = fields.Float(string="Apparatus Constant (K)")

    fineness_blaine_ids = fields.One2many("fineness.blaine.psc.line","parent_id",string="Trial Lines")

    average_time = fields.Float(string="Average Time (t)",compute="_compute_blaine_results",store=True,)

    sqrt_time = fields.Float(string="√t",compute="_compute_blaine_results",store=True,)

    specific_surface = fields.Float(string="Specific Surface (cm²/g)",compute="_compute_blaine_results",store=True,)

    @api.depends(
    "fineness_blaine_ids.time",
    "eta",
    "e",
    "density",
    "apparatus_constant",
)
    def _compute_blaine_results(self):
     for rec in self:
        times = rec.fineness_blaine_ids.filtered(
            lambda line: line.time > 0
        ).mapped("time")

        rec.average_time = 0.0
        rec.sqrt_time = 0.0
        rec.specific_surface = 0.0

        if not times:
            continue

        avg_time = sum(times) / len(times)

        rec.average_time = avg_time
        rec.sqrt_time = sqrt(avg_time)

        if (
            rec.apparatus_constant > 0
            and rec.density > 0
            and rec.eta > 0
            and 0 < rec.e < 1
        ):
            rec.specific_surface = (
                (rec.apparatus_constant / rec.density)
                * (sqrt(rec.e ** 3) / (1 - rec.e))
                * (rec.sqrt_time / sqrt(0.1 * rec.eta))
            )

    specific_surface_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_specific_surface_confirmity")
    
    @api.depends('specific_surface','eln_ref','grade')
    def _compute_specific_surface_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.specific_surface_confirmity = 'na'
                continue
            record.specific_surface_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3012478fffrr-372f-4775-9bcb-e9dd70214578r')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3012478fffrr-372f-4775-9bcb-e9dd70214578r')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.specific_surface - record.specific_surface*mu_value
                    upper = record.specific_surface + record.specific_surface*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.specific_surface_confirmity = 'pass'
                        break
                    else:
                        record.specific_surface_confirmity = 'fail'

    specific_surface_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_specific_surface_nabl",store=True)

    @api.depends('specific_surface','eln_ref','grade')
    def _compute_specific_surface_nabl(self):
        
        for record in self:
            record.specific_surface_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3012478fffrr-372f-4775-9bcb-e9dd70214578r')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3012478fffrr-372f-4775-9bcb-e9dd70214578r')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.specific_surface - record.specific_surface*mu_value
                    upper = record.specific_surface + record.specific_surface*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.specific_surface_nabl = 'pass'
                        break
                    else:
                        record.specific_surface_nabl = 'fail'



    # DRYING SHRINKAGE OF CEMENT
    drying_shrinkage_name = fields.Char("Name", default="Drying Shrinkage Of Cement")
    drying_shrinkage_visible = fields.Boolean("Drying Shrinkage Of Cement", compute="_compute_visible")

    drying_child_lines = fields.One2many('drying.shrinkage.psc.line','parent_id',string="Parameter" )

    average_delta_l = fields.Float(
        string="Average ΔL (mm)",
        compute="_compute_result",
        store=True,
    )

    drying_shrinkage = fields.Float(
        string="Drying Shrinkage (%)",
        compute="_compute_result",
        store=True,
    )

    @api.depends("drying_child_lines.delta_l")
    def _compute_result(self):
        for rec in self:
            rec.average_delta_l = 0.0
            rec.drying_shrinkage = 0.0

            values = rec.drying_child_lines.mapped("delta_l")

            if values:
                rec.average_delta_l = sum(values) / len(values)

            
            rec.drying_shrinkage = (rec.average_delta_l / 250) * 100

    

    drying_shrinkage_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
    ('na', 'NA'),], string="Conformity", compute="_compute_drying_shrinkage_conformity", store=True)

    @api.depends('drying_shrinkage','eln_ref','grade')
    def _compute_drying_shrinkage_conformity(self):
        
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.drying_shrinkage_conformity = 'na'
                continue
            record.drying_shrinkage_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c16b7457-0c65-4f5d-90b4-e94fa41405e8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c16b7457-0c65-4f5d-90b4-e94fa41405e8')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.drying_shrinkage - record.drying_shrinkage*mu_value
                    upper = record.drying_shrinkage + record.drying_shrinkage*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.drying_shrinkage_conformity = 'pass'
                        break
                    else:
                        record.drying_shrinkage_conformity = 'fail'

    drying_shrinkage_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_drying_shrinkage_nabl", store=True)

    @api.depends('drying_shrinkage','eln_ref','grade')
    def _compute_drying_shrinkage_nabl(self):
        
        for record in self:
            record.drying_shrinkage_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c16b7457-0c65-4f5d-90b4-e94fa41405e8')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c16b7457-0c65-4f5d-90b4-e94fa41405e8')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.drying_shrinkage - record.drying_shrinkage*mu_value
                  upper = record.drying_shrinkage + record.drying_shrinkage*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.drying_shrinkage_nabl = 'pass'
                      break
                  else:
                      record.drying_shrinkage_nabl = 'fail'





    

  

            
    ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.fineness_cement_visible = False
            record.consistency_cement_visible = False
            record.setting_time_visible = False
            record.compressive_visible = False
            record.soundness_cement_visible = False
            record.specific_gravity_visible = False
            record.density_cement_visible = False
            record.fineness_blaine_visible = False
            record.drying_shrinkage_visible = False
         
            

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)


                if sample.internal_id == '12457800-372f-4775-9bcb-e9dd70e6e6df':
                    record.fineness_cement_visible = True

                if sample.internal_id == '01247gggty-372f-4775-9bcb-e9dd723547htui':
                    record.consistency_cement_visible = True

                if sample.internal_id == '72096e8f-63cb-474b-822f-9b631d7b3553':
                    record.setting_time_visible = True

                if sample.internal_id == '214578gt-372f-4775-9bcb-e9dd723547htui':
                    record.compressive_visible = True

                if sample.internal_id == '21457896f-372f-4775-9bcb-e9dd723547htui':
                    record.soundness_cement_visible = True

                if sample.internal_id == '0157yutr1034-372f-4775-9bcb-e9dd723547htui':
                    record.specific_gravity_visible = True

                if sample.internal_id == '23145870-372f-4775-9bcb-e9dd70e3587g':
                    record.density_cement_visible = True

                if sample.internal_id == '3012478fffrr-372f-4775-9bcb-e9dd70214578r':
                    record.fineness_blaine_visible = True

                if sample.internal_id == "c16b7457-0c65-4f5d-90b4-e94fa41405e8":
                    record.drying_shrinkage_visible = True


                

                

             
             

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

            # Fineness of Cement by Dry Sieving
            if result.parameter.internal_id == '12457800-372f-4775-9bcb-e9dd70e6e6df':
                result.result_char = round(self.avg_fineness,2)
                result.calculated = True
                if self.avg_fineness_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Consistency of Cement
            if result.parameter.internal_id == '01247gggty-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.average_consistency,2)
                result.calculated = True
                if self.average_consistency_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Setting Time
            if result.parameter.internal_id == '72096e8f-63cb-474b-822f-9b631d7b3553':
                result.calculated = True


            # Initial Setting Time
            if result.parameter.internal_id == 'psc5478-30fe-4043-b518-015f5c60d916':
                result.result_char = self.initial_setting_time
                result.calculated = True
                if self.initial_setting_time_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Final Setting Time
            if result.parameter.internal_id == '987psc47-5e9c-4335-9ea2-2d87624c3061':
                result.result_char = self.final_setting_time
                result.calculated = True
                if self.final_setting_time_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Compressive Strength
            if result.parameter.internal_id == '214578gt-372f-4775-9bcb-e9dd723547htui':
                result.calculated = True

          
            # Compressive Strength (3 Days)
            if result.parameter.internal_id == '358789gtyg-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.avg_3_days,2)
                result.calculated = True
                if self.avg_3_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Compressive Strength (7 Days)
            if result.parameter.internal_id == '555888ggghhjy-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.avg_7_days,2)
                result.calculated = True
                if self.avg_7_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Compressive Strength (14 Days)
            if result.parameter.internal_id == 'a3525d21-e21a-44d3-a09c-f87afc1fbcc4':
                result.result_char = round(self.avg_14_days,2)
                result.calculated = True
                if self.avg_14_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Compressive Strength (28 Days)
            if result.parameter.internal_id == '5777fffrrtt11-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.avg_28_days,2)
                result.calculated = True
                if self.avg_28_days_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # SOUNDNESS OF CEMENT BY LE-CHATELIER METHOD
            if result.parameter.internal_id == '21457896f-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.avg_soundness_expansion,2)
                result.calculated = True
                if self.avg_soundness_expansion_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # SPECIFIC GRAVITY OF CEMENT							
            if result.parameter.internal_id == '0157yutr1034-372f-4775-9bcb-e9dd723547htui':
                result.result_char = round(self.average_specific_gravity,2)
                result.calculated = True
                if self.average_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # DENSITY OF CEMENT
            if result.parameter.internal_id == '23145870-372f-4775-9bcb-e9dd70e3587g':
                result.result_char = round(self.average_density,2)
                result.calculated = True
                if self.average_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue



            # FINENESS OF CEMENT BY BLAINE AIR PERMEABILITY METHOD
            if result.parameter.internal_id == '3012478fffrr-372f-4775-9bcb-e9dd70214578r':
                result.result_char = round(self.specific_surface,2)
                result.calculated = True
                if self.specific_surface_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Drying Skrinkage
            if result.parameter.internal_id == 'c16b7457-0c65-4f5d-90b4-e94fa41405e8':
                result.result_char = round(self.drying_shrinkage,2)
                result.calculated = True
                if self.drying_shrinkage_nabl == 'pass':
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
    @api.depends('eln_ref', 'eln_ref.parameters_result.technician')
    def _compute_sample_parameters(self):
        current_user = self.env.user

        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            # Check if user is in Lerm Admin group
            if (
                current_user.has_group('lerm_civil.kes_admin_access_group')
                or current_user.has_group('lerm_civil.lerm_sample_verification')
                or current_user.has_group('lerm_civil.lerm_sample_approval')
            ):
                # Admin sees all parameters
                parameter_ids = record.eln_ref.parameters_result.mapped('parameter').ids
            else:
                # Other users only see parameters assigned to them
                user_param_results = record.eln_ref.parameters_result.filtered(
                    lambda r: r.technician and r.technician.id == current_user.id
                )
                parameter_ids = user_param_results.mapped('parameter').ids

            record.sample_parameters = [(6, 0, parameter_ids)]
    def get_all_fields(self):
        record = self.env['cement.psc'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value
        return field_values


    notes_id = fields.One2many('cement.psc.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

    @api.model
    def _default_notes_lines(self):
        return [
            (0, 0, {'sr_no': 'i', 'notes': 'The results stated in this report apply only to the tested sample(s) and are based on the conditions and parameters at the time of testing.'}),
            (0, 0, {'sr_no': 'ii', 'notes': 'This report is invalid without the official paper seal of Make Infracon.'}),
            (0, 0, {'sr_no': 'iii', 'notes': 'All test results are confidential and will not be disclosed to any third party without written consent of the client, except where required by law.'}),
            (0, 0, {'sr_no': 'iv', 'notes': 'Any discrepancies or complaints regarding this report must be communicated in writing within 7 days from the date of issue.'}),
            (0, 0, {'sr_no': 'v', 'notes': 'This report shall not be reproduced, except in full, without the prior written approval of Make Infracon.'}),
            (0, 0, {'sr_no': 'vi', 'notes': 'The laboratory assumes no responsibility for the purpose for which the test results are used or for any subsequent actions taken based on these results.'}),
        ]


class FinenessCementPSCLine(models.Model):
    _name = "fineness.cement.psc.line"
    parent_id = fields.Many2one('cement.psc',string="Parent Id")

    serial_no = fields.Integer(string="Wt of Sample", readonly=True, copy=False, default=1)

   
    wt_of_sample_taken = fields.Float(string="Wt. of Sample taken (W1) gm")
    wt_of_residue = fields.Float(string="Wt. of residue on 90μ sieve (W Max. 10% 2) gm")
    fineness = fields.Float(string="Fineness (%) (W2/W1) X100" ,compute="_compute_fineness")

    @api.depends('wt_of_sample_taken', 'wt_of_residue')
    def _compute_fineness(self):
        for record in self:
            if record.wt_of_sample_taken:
                record.fineness = (record.wt_of_residue / record.wt_of_sample_taken) * 100
            else:
                record.fineness = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(FinenessCementPSCLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class ConsistencyCementPSCLine(models.Model):
    _name = "consistensy.cement.psc.line"
    parent_id = fields.Many2one('cement.psc',string="Parent Id")

    serial_no = fields.Integer(string="Trial No", readonly=True, copy=False, default=1)

   
    weight_of_cement = fields.Float(
        string="Weight of Cement Taken (g)"
    )

    weight_of_water = fields.Float(
        string="Weight of Water Taken (g)"
    )

    plunger_penetration = fields.Float(
        string="Plunger Penetration from Bottom of Mould (mm)"
    )

    time_taken = fields.Float(
        string="Time Taken from Adding Water to Cement (min)"
    )

    consistency = fields.Float(
        string="Consistency of Cement (%)",
        compute="_compute_consistency",
        store=True
    )

    @api.depends('weight_of_cement', 'weight_of_water')
    def _compute_consistency(self):
        for rec in self:
            if rec.weight_of_cement:
                rec.consistency = round(
                    (rec.weight_of_water / rec.weight_of_cement) * 100,
                    1
                )
            else:
                rec.consistency = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(ConsistencyCementPSCLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class CementPSCSettingTimeInitialLine(models.Model):
    _name = 'cement.psc.setting.time.initial.line'
    _description = 'Initial Setting Reading'

    parent_id = fields.Many2one('cement.psc',string="Parent Id")

    time = fields.Float("Time")
    elapsed_time = fields.Float("Elapsed Time (Min)")
    needle_penetration = fields.Float("Needle Penetration (mm)")


class CementPSCSettingTimeFinalLine(models.Model):
    _name = 'cement.psc.setting.time.final.line'
    _description = 'Final Setting Reading'

    parent_id = fields.Many2one('cement.psc',string="Parent Id")

    time = fields.Float("Time")
    elapsed_time = fields.Float("Elapsed Time (Min)")

    immersion_status = fields.Selection([
        ('appears', 'Immersion Appears'),
        ('disappears', 'Immersion Disappears')
    ], string="Needle Result")


class CompressiveCementPSCLine(models.Model):
    _name = "compressive.psc.line"
    parent_id = fields.Many2one('cement.psc',string="Parent Id")

    serial_no = fields.Integer(string="Specimen No", readonly=True, copy=False, default=1)

    dt_of_casting = fields.Date(string="Date of Casting ")
    days = fields.Char(string="Age in Days")
    dt_of_testing = fields.Date(string="Date of Testing")
    wt_of_cube = fields.Float(string="Weight (g)")
    density = fields.Float(string="Density (g/cc)",compute="_compute_density",store=True)
    area = fields.Float(string="Area",compute="_compute_area",store=True)
    load = fields.Float(string="Load at Failure (kN)")
    compressive_strength = fields.Float(string="Compressive Strength of Individual Sample (f1) in (N/mm2)",compute="_compute_strength")

    

    @api.onchange('days')
    def _onchange_days_set_testing_date(self):
        if self.dt_of_casting and self.days:
            self.dt_of_testing = self.dt_of_casting + timedelta(days=self.days)
        else:
            self.dt_of_testing = False

    @api.depends('parent_id')
    def _compute_area(self):
        for rec in self:
            rec.area = 7.06 * 7.06

    

    @api.depends('wt_of_cube')
    def _compute_density(self):
      volume = 7.06 * 7.06 * 7.06  

      for rec in self:
        rec.density = (rec.wt_of_cube or 0.0) / volume

    @api.depends('load', 'area')
    def _compute_strength(self):
        for rec in self:
            if rec.area:
                rec.compressive_strength = (rec.load / rec.area)
            else:
                rec.compressive_strength = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CompressiveCementPSCLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class soundnessCementPSCLine(models.Model):
    _name = "soundness.cement.psc.line"
    parent_id = fields.Many2one('cement.psc',string="Parent Id")

    serial_no = fields.Integer(string="Sr No.", readonly=True, copy=False, default=1)

   
    l1 = fields.Float(string="Measurement taken after 24 hours of immersion in water at a temp. of 27 + 20C = L1 (mm)")

    l2 = fields.Float(string="Measurement taken after 3 hours of immersion in water at a Boiling Temperature = L2 (mm)")

    expansion = fields.Float(
        string="Expansion L1-L2 (mm)",
        compute="_compute_expansion",
        store=True,
    )

    @api.depends("l1", "l2")
    def _compute_expansion(self):
        for rec in self:
            rec.expansion = (rec.l2 or 0.0) - (rec.l1 or 0.0)


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(soundnessCementPSCLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class CementPSCSpecificGravityLine(models.Model):
    _name = "cement.psc.specific.gravity.line"
    _description = "Specific Gravity Trial"

    parent_id = fields.Many2one('cement.psc',string="Parent Id")

    serial_no = fields.Integer(string="Trail No.", readonly=True, copy=False, default=1)

    weight_cement = fields.Float(string="Weight of Cement Sample W1 in (g)")

    initial_reading = fields.Float(string="Initial Reading of Flask V1 in (ml)")

    final_reading = fields.Float(string="Final Reading of Flask V2 in (ml)")

    volume_cement = fields.Float(string="Volume of Cement (V2 - V1)",compute="_compute_values",store=True,)

    weight_equal_volume_water = fields.Float(string="Weight of Equal Volume of water=(V2-V1)xSpecific gravity of Water	",compute="_compute_values",store=True,)

    specific_gravity = fields.Float(string="Sp. Gravity of Cement=W1/Weight of equal volume of Water",compute="_compute_values",store=True,)

    @api.depends(
        "weight_cement",
        "initial_reading",
        "final_reading",
    )
    def _compute_values(self):
        for rec in self:

            rec.volume_cement = (
                rec.final_reading - rec.initial_reading
            )

            # Specific gravity of water = 1 g/ml
            rec.weight_equal_volume_water = rec.volume_cement * 1.0

            if rec.weight_equal_volume_water:
                rec.specific_gravity = (
                    rec.weight_cement /
                    rec.weight_equal_volume_water
                )
            else:
                rec.specific_gravity = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CementPSCSpecificGravityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class DensityCementPSCLine(models.Model):
    _name = "density.cement.psc.line"
    parent_id = fields.Many2one('cement.psc',string="Parent Id")

    serial_no = fields.Integer(string="Trail No.", readonly=True, copy=False, default=1)

   
    weight_cement = fields.Float(string="Weight of Cement Sample W1 in (g)")

    initial_reading = fields.Float(string="Initial Reading of Flask V1 in (ml)")

    final_reading = fields.Float(string="Final Reading of Flask V2 in (ml)")

    volume_cement = fields.Float(string="Volume of Cement (V2 - V1)",compute="_compute_values",store=True,)

    weight_equal_volume_water = fields.Float(string="Weight of Equal Volume of water=(V2-V1)xSpecific gravity of Water	",compute="_compute_values",store=True,)

    specific_gravity = fields.Float(string="Sp. Gravity of Cement=W1/Weight of equal volume of Water",compute="_compute_values",store=True,)

    @api.depends(
        "weight_cement",
        "initial_reading",
        "final_reading",
    )
    def _compute_values(self):
        for rec in self:

            rec.volume_cement = (
                rec.final_reading - rec.initial_reading
            )

            # Specific gravity of water = 1 g/ml
            rec.weight_equal_volume_water = rec.volume_cement * 1.0

            if rec.weight_equal_volume_water:
                rec.specific_gravity = (
                    rec.weight_cement /
                    rec.weight_equal_volume_water
                )
            else:
                rec.specific_gravity = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(DensityCementPSCLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class FinenessBlainePSCLine(models.Model):
    _name = "fineness.blaine.psc.line"
    parent_id = fields.Many2one('cement.psc',string="Parent Id")

    serial_no = fields.Integer(string="Trail No.", readonly=True, copy=False, default=1)

    mass = fields.Float(
        string="Mass of Sample (m) gms"
    )

    time = fields.Float(
        string="Time (sec)"
    )

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(FinenessBlainePSCLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1







class MechanicalDryingShrinkagPSCLine(models.Model):
    _name = "drying.shrinkage.psc.line"
    parent_id = fields.Many2one('cement.psc',string="Parent Id")
   
    sr_no = fields.Integer(string="Sample No.", readonly=True, copy=False, default=1)

    initial_length = fields.Float(
        string="Initial Length (Li) at 7 Days (mm)"
    )

    final_length = fields.Float(
        string="Final Length (Lf) at 35 Days (mm)"
    )

    delta_l = fields.Float(
        string="Change in Length (ΔL) (mm)",
        compute="_compute_delta_l",
        store=True,
    )

    @api.depends(
        "initial_length",
        "final_length",
    )
    def _compute_delta_l(self):
        for rec in self:
            rec.delta_l = (
                (rec.initial_length or 0.0)
                - (rec.final_length or 0.0)
            )

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalDryingShrinkagPSCLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1
    

class CementPSCNotes(models.Model):
    _name = "cement.psc.notes"

    parent_id = fields.Many2one('cement.psc', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
