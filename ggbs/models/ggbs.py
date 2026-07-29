from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math
from statistics import mean
from math import sqrt




class GgbsMechanical(models.Model):
    _name = "mechanical.ggbs"
    _inherit = "lerm.eln"
    _description = 'mechanical.ggbs'
    _rec_name = "name"


    name = fields.Char("Name",default="GGBS")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.ggbs.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    temp = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)


    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id



    #  Initial Setting Time And Final Setting Time

    setting_time_name = fields.Char("Name", default="Initial And Final Setting Time")
    setting_time_visible = fields.Boolean("Setting Time Visible",compute="_compute_visible")

    intial_time_lines = fields.One2many('ggbs.setting.time.initial.line','parent_id',string="Initial Time")

    final_time_lines = fields.One2many('ggbs.setting.time.final.line','parent_id',string="Initial Time")


    cement_weight = fields.Float(
        string="Weight of Sample taken (g)"
    )

    set_normal_consistency = fields.Float(
        string="Normal Consistency (%)"
    )

    weight_of_water = fields.Float(
        string="Weight of Water Added = 0.85 * Normal Consistency x Weight of Cement Sample in Initial & Final Setting Time",
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24c84ebd-55ce-4c9d-8cf7-562d5f2c341d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24c84ebd-55ce-4c9d-8cf7-562d5f2c341d')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24c84ebd-55ce-4c9d-8cf7-562d5f2c341d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','24c84ebd-55ce-4c9d-8cf7-562d5f2c341d')]).parameter_table
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


    initial_setting_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    initial_setting_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_initial_setting_final_report", store=True)

    @api.depends('initial_setting_time_nabl', 'initial_setting_report_type')
    def _compute_initial_setting_final_report(self):
     for rec in self:

        # Manual override
        if rec.initial_setting_report_type == 'nabl':
            rec.initial_setting_final_report = 'nabl'

        elif rec.initial_setting_report_type == 'non_nabl':
            rec.initial_setting_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.initial_setting_time_nabl == 'pass':
                rec.initial_setting_final_report = 'nabl'
            else:
                rec.initial_setting_final_report = 'non_nabl'

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a2aeca09-ec68-4567-964f-4edd0dbefa0f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a2aeca09-ec68-4567-964f-4edd0dbefa0f')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a2aeca09-ec68-4567-964f-4edd0dbefa0f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a2aeca09-ec68-4567-964f-4edd0dbefa0f')]).parameter_table
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


    final_setting_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    final_setting_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_final_setting_final_report", store=True)

    @api.depends('final_setting_time_nabl', 'final_setting_report_type')
    def _compute_final_setting_final_report(self):
     for rec in self:

        # Manual override
        if rec.final_setting_report_type == 'nabl':
            rec.final_setting_final_report = 'nabl'

        elif rec.final_setting_report_type == 'non_nabl':
            rec.final_setting_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.final_setting_time_nabl == 'pass':
                rec.final_setting_final_report = 'nabl'
            else:
                rec.final_setting_final_report = 'non_nabl'


    # FINENESS OF GGBS BY BLAINE AIR PERMEABILITY METHOD	
    fineness_blaine_name = fields.Char("Name",default="Fineness by Blaine's Air Permeability")
    fineness_blaine_visible = fields.Boolean("Fineness by Blaine's Air Permeability Visible",compute="_compute_visible")

    e = fields.Float(string="e")

    eta = fields.Float(string="η (is the viscosity of air at the test temperature)",digits=(16,4))

    density = fields.Float(string="Density of Sample (ρ)")

    apparatus_constant = fields.Float(string="Apparatus Constant (K)")

    fineness_blaine_ids = fields.One2many("ggbs.fineness.blaine.line","parent_id",string="Trial Lines")

    average_time = fields.Float(string="Average Time (t)",compute="_compute_blaine_results")

    sqrt_time = fields.Float(string="√t",compute="_compute_blaine_results",)

    specific_surface = fields.Float(string="Specific Surface (cm²/g)",compute="_compute_blaine_results")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6a94f8a3-dd41-4516-bd7b-d74c89bd924a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6a94f8a3-dd41-4516-bd7b-d74c89bd924a')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6a94f8a3-dd41-4516-bd7b-d74c89bd924a')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6a94f8a3-dd41-4516-bd7b-d74c89bd924a')]).parameter_table
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


    specific_surface_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    specific_surface_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_specific_surface_final_report", store=True)

    @api.depends('specific_surface_nabl', 'specific_surface_report_type')
    def _compute_specific_surface_final_report(self):
     for rec in self:

        # Manual override
        if rec.specific_surface_report_type == 'nabl':
            rec.specific_surface_final_report = 'nabl'

        elif rec.specific_surface_report_type == 'non_nabl':
            rec.specific_surface_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.specific_surface_nabl == 'pass':
                rec.specific_surface_final_report = 'nabl'
            else:
                rec.specific_surface_final_report = 'non_nabl'


    # SOUNDNESS OF GGBS BY LE-CHATELIER METHOD

    soundness_cement_name = fields.Char("Name",default="SOUNDNESS OF CEMENT BY LE-CHATELIER METHOD")
    soundness_cement_visible = fields.Boolean("SOUNDNESS OF GGBS BY LE-CHATELIER METHOD Visible",compute="_compute_visible")

    soundness_cement_lines = fields.One2many('ggbs.soundness.cement.line','parent_id',string="Soundness")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a76ec90d-a344-49de-9b98-ca0cda833fe5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a76ec90d-a344-49de-9b98-ca0cda833fe5')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a76ec90d-a344-49de-9b98-ca0cda833fe5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a76ec90d-a344-49de-9b98-ca0cda833fe5')]).parameter_table
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


    soundness_expansion_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    soundness_expansion_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_soundness_expansion_final_report", store=True)

    @api.depends('avg_soundness_expansion_nabl', 'soundness_expansion_report_type')
    def _compute_soundness_expansion_final_report(self):
     for rec in self:

        # Manual override
        if rec.soundness_expansion_report_type == 'nabl':
            rec.soundness_expansion_final_report = 'nabl'

        elif rec.soundness_expansion_report_type == 'non_nabl':
            rec.soundness_expansion_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_soundness_expansion_nabl == 'pass':
                rec.soundness_expansion_final_report = 'nabl'
            else:
                rec.soundness_expansion_final_report = 'non_nabl'


    # SPECIFIC GRAVITY OF GGBS

    specific_gravity_name = fields.Char("Name",default="Specific Gravity of GGBS")
    specific_gravity_visible = fields.Boolean("Specific Gravity of GGBS Visible",compute="_compute_visible")

    specific_gravity_line_ids = fields.One2many(
        "ggbs.specific.gravity.line",
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8d7d0d6c-9960-4ea6-b4eb-bca8b8cf78a1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8d7d0d6c-9960-4ea6-b4eb-bca8b8cf78a1')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8d7d0d6c-9960-4ea6-b4eb-bca8b8cf78a1')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8d7d0d6c-9960-4ea6-b4eb-bca8b8cf78a1')]).parameter_table
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

    specific_gravity_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    specific_gravity_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_specific_gravity_final_report", store=True)

    @api.depends('average_specific_gravity_nabl', 'specific_gravity_report_type')
    def _compute_specific_gravity_final_report(self):
     for rec in self:

        # Manual override
        if rec.specific_gravity_report_type == 'nabl':
            rec.specific_gravity_final_report = 'nabl'

        elif rec.specific_gravity_report_type == 'non_nabl':
            rec.specific_gravity_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.average_specific_gravity_nabl == 'pass':
                rec.specific_gravity_final_report = 'nabl'
            else:
                rec.specific_gravity_final_report = 'non_nabl'




    # MOISTURE CONTENT OF GGBS

    moisture_content_name = fields.Char("Name",default="Moisture Content of GGBS")
    moisture_content_visible = fields.Boolean("Moisture Content of GGBS Visible",compute="_compute_visible")

    
    moisture_content_line_ids = fields.One2many(
        "ggbs.moisture.content.line",
        "parent_id",
        string="Test Readings"
    )

    average_moisture = fields.Float(
        string="Average Moisture Content (%)",
        compute="_compute_average_moisture",
        store=True,
        digits=(16, 2)
    )

    @api.depends("moisture_content_line_ids.moisture_content")
    def _compute_average_moisture(self):
        for rec in self:
            values = rec.moisture_content_line_ids.mapped("moisture_content")
            rec.average_moisture = round(
                sum(values) / len(values), 2
            ) if values else 0.0


    average_moisture_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),('na', 'NA'),], string='Confirmity',compute="_compute_average_moisture_confirmity")
    
    @api.depends('average_moisture','eln_ref','grade')
    def _compute_average_moisture_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_moisture_confirmity = 'na'
                continue
            record.average_moisture_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c69ca85f-ab48-4370-9cd1-96f3374ac4dd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c69ca85f-ab48-4370-9cd1-96f3374ac4dd')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_moisture - record.average_moisture*mu_value
                    upper = record.average_moisture + record.average_moisture*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_moisture_confirmity = 'pass'
                        break
                    else:
                        record.average_moisture_confirmity = 'fail'

    average_moisture_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string='NABL', compute="_compute_average_moisture_nabl",store=True)

    @api.depends('average_moisture','eln_ref','grade')
    def _compute_average_moisture_nabl(self):
        
        for record in self:
            record.average_moisture_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c69ca85f-ab48-4370-9cd1-96f3374ac4dd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c69ca85f-ab48-4370-9cd1-96f3374ac4dd')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_moisture - record.average_moisture*mu_value
                    upper = record.average_moisture + record.average_moisture*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_moisture_nabl = 'pass'
                        break
                    else:
                        record.average_moisture_nabl = 'fail'

    average_moisture_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    average_moisture_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_average_moisture_final_report", store=True)

    @api.depends('average_moisture_nabl', 'average_moisture_report_type')
    def _compute_average_moisture_final_report(self):
     for rec in self:

        # Manual override
        if rec.average_moisture_report_type == 'nabl':
            rec.average_moisture_final_report = 'nabl'

        elif rec.average_moisture_report_type == 'non_nabl':
            rec.average_moisture_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.average_moisture_nabl == 'pass':
                rec.average_moisture_final_report = 'nabl'
            else:
                rec.average_moisture_final_report = 'non_nabl'



    

    

    

    ### Compute Visible
    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        

        for record in self:
            record.setting_time_visible = False
            record.fineness_blaine_visible = False
            record.soundness_cement_visible = False
            record.specific_gravity_visible = False
            record.moisture_content_visible = False

            
            
            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == 'b37bdc2f-7956-4120-aee4-bbe9724785e0':
                    record.setting_time_visible = True

                if sample.internal_id == '24c84ebd-55ce-4c9d-8cf7-562d5f2c341d':
                    record.setting_time_visible = True

                if sample.internal_id == 'a2aeca09-ec68-4567-964f-4edd0dbefa0f':
                    record.setting_time_visible = True

                if sample.internal_id == '6a94f8a3-dd41-4516-bd7b-d74c89bd924a':
                    record.fineness_blaine_visible = True

                if sample.internal_id == 'a76ec90d-a344-49de-9b98-ca0cda833fe5':
                    record.soundness_cement_visible = True

                if sample.internal_id == '8d7d0d6c-9960-4ea6-b4eb-bca8b8cf78a1':
                    record.specific_gravity_visible = True

                if sample.internal_id == 'c69ca85f-ab48-4370-9cd1-96f3374ac4dd':
                    record.moisture_content_visible = True


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
        
            # Setting Time
            if result.parameter.internal_id == 'b37bdc2f-7956-4120-aee4-bbe9724785e0':
                result.calculated = True


            # Initial Setting Time
            if result.parameter.internal_id == '24c84ebd-55ce-4c9d-8cf7-562d5f2c341d':
                result.result_char = self.initial_setting_time
                result.calculated = True
                if self.initial_setting_time_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Final Setting Time
            if result.parameter.internal_id == 'a2aeca09-ec68-4567-964f-4edd0dbefa0f':
                result.result_char = self.final_setting_time
                result.calculated = True
                if self.final_setting_time_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # FINENESS OF GGBS BY BLAINE AIR PERMEABILITY METHOD
            if result.parameter.internal_id == '6a94f8a3-dd41-4516-bd7b-d74c89bd924a':
                result.result_char = round(self.specific_surface,2)
                result.calculated = True
                if self.specific_surface_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # SOUNDNESS OF GGBS BY LE-CHATELIER METHOD
            if result.parameter.internal_id == 'a76ec90d-a344-49de-9b98-ca0cda833fe5':
                result.result_char = round(self.avg_soundness_expansion,2)
                result.calculated = True
                if self.avg_soundness_expansion_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # SPECIFIC GRAVITY OF GGBS							
            if result.parameter.internal_id == '8d7d0d6c-9960-4ea6-b4eb-bca8b8cf78a1':
                result.result_char = round(self.average_specific_gravity,2)
                result.calculated = True
                if self.average_specific_gravity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Moisture Content							
            if result.parameter.internal_id == 'c69ca85f-ab48-4370-9cd1-96f3374ac4dd':
                result.result_char = round(self.average_moisture,2)
                result.calculated = True
                if self.average_moisture_nabl == 'pass':
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
        record = super(GgbsMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


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
        record = self.env['mechanical.ggbs'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    notes_id = fields.One2many('mechanical.ggbs.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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

class GGBSCementSettingTimeInitialLine(models.Model):
    _name = 'ggbs.setting.time.initial.line'
    _description = 'Initial Setting Reading'

    parent_id = fields.Many2one('mechanical.ggbs', string="Parent Id")

    time = fields.Float("Time")
    elapsed_time = fields.Float("Elapsed Time (Min)")
    needle_penetration = fields.Float("Needle Penetration (mm)")


class GGBSCementSettingTimeFinalLine(models.Model):
    _name = 'ggbs.setting.time.final.line'
    _description = 'Final Setting Reading'

    parent_id = fields.Many2one('mechanical.ggbs', string="Parent Id")

    time = fields.Float("Time")
    elapsed_time = fields.Float("Elapsed Time (Min)")

    immersion_status = fields.Selection([
        ('appears', 'Immersion Appears'),
        ('disappears', 'Immersion Disappears')
    ], string="Needle Result")



class GGBSFinenessBlaineLine(models.Model):
    _name = "ggbs.fineness.blaine.line"
    parent_id = fields.Many2one('mechanical.ggbs', string="Parent Id")

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

        return super(GGBSFinenessBlaineLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1



class GGBSsoundnessCementLine(models.Model):
    _name = "ggbs.soundness.cement.line"
    parent_id = fields.Many2one('mechanical.ggbs', string="Parent Id")

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

        return super(GGBSsoundnessCementLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class GGBSSpecificGravityLine(models.Model):
    _name = "ggbs.specific.gravity.line"
    _description = "Specific Gravity Trial"

    parent_id = fields.Many2one('mechanical.ggbs', string="Parent Id")

    serial_no = fields.Integer(string="Trail No.", readonly=True, copy=False, default=1)

    weight_cement = fields.Float(string="Weight of  GGBS Sample -W1 in gm")

    initial_reading = fields.Float(string="Initial Reading of Flask V1 in (ml)")

    final_reading = fields.Float(string="Final Reading of Flask V2 in (ml)")

    volume_cement = fields.Float(string="Volume of GGBS (V2 - V1)",compute="_compute_values",store=True,)

    weight_equal_volume_water = fields.Float(string="Weight of Equal Volume of water=(V2-V1)xSpecific gravity of Water	",compute="_compute_values",store=True,)

    specific_gravity = fields.Float(string="Sp. Gravity of GGBS =W1/Weight of equal volume of Water",compute="_compute_values",store=True,)

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

        return super(GGBSSpecificGravityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class GGBSMoistureContentLine(models.Model):
    _name = "ggbs.moisture.content.line"
    _description = "Moisture Content Line"

    parent_id = fields.Many2one('mechanical.ggbs', string="Parent Id")

    serial_no = fields.Integer(string="Trail No.", readonly=True, copy=False, default=1)

    sample_id = fields.Char(string="Sample ID")

    w1 = fields.Float(
        string="Empty Container Weight (W1)"
    )

    w2 = fields.Float(
        string="Container + Wet Sample (W2)"
    )

    w3 = fields.Float(
        string="Container + Dry Sample (W3)"
    )

    wet_sample_weight = fields.Float(
        string="Wet Sample Weight (W2−W1) (g)",
        compute="_compute_values",
        store=True,
        digits=(16, 2)
    )

    dry_sample_weight = fields.Float(
        string="Dry Sample Weight (W3−W1) (g)",
        compute="_compute_values",
        store=True,
        digits=(16, 2)
    )

    moisture_weight = fields.Float(
        string="Moisture Weight (W2−W3) (g)",
        compute="_compute_values",
        store=True,
        digits=(16, 2)
    )

    moisture_content = fields.Float(
        string="Moisture Content (%)",
        compute="_compute_values",
        store=True,
        digits=(16, 2)
    )

    @api.depends("w1", "w2", "w3")
    def _compute_values(self):
        for rec in self:

            rec.wet_sample_weight = rec.w2 - rec.w1
            rec.dry_sample_weight = rec.w3 - rec.w1
            rec.moisture_weight = rec.w2 - rec.w3

            if rec.dry_sample_weight:
                rec.moisture_content = round(
                    (rec.moisture_weight / rec.dry_sample_weight) * 100,
                    2
                )
            else:
                rec.moisture_content = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(GGBSMoistureContentLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


    

class GgbsMechanicalNotes(models.Model):
    _name = "mechanical.ggbs.notes"

    parent_id = fields.Many2one('mechanical.ggbs', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
