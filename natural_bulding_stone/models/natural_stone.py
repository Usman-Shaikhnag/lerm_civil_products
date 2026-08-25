from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math



class NaturalBuildingStone(models.Model):
    _name = "mechanical.natural.bulding.stone"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="Natural Building Stone")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    notes_id = fields.One2many('mechanical.precast.kerb.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(NaturalBuildingStone, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The Test Report(s) is/are valid only to the sample submitted to the laboratory.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'Sample(s) was/were not drawn by laboratory.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'This Report may not be reproduced in except full/ part without the permission of the Lab Head of the Laboratory.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': '# - Information provided by the customer.',
            }),
        ]

        res['notes_id'] = default_notes
        return res

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

   
    asgapw_name = fields.Char("Name",default="Apparent Specific Gravity, Apparent Porosity and Water Absorption")
    asgapw_visible = fields.Boolean("Visible",compute="_compute_visible")   

   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_asgapw = fields.One2many('mechanical.asgapwline.line','parent_id',string="Parameter")

    average_asg = fields.Float(string="Apparent Specific Gravity ",compute="_compute_average_asg",digits=(12,2),store=True)

    @api.depends('child_lines_asgapw.apparent_specific')
    def _compute_average_asg(self):
        for record in self:
            asg = record.child_lines_asgapw.mapped('apparent_specific')
            if asg:
                record.average_asg = sum(asg) / len(asg)
            else:
                record.average_asg = 0.0

    average_asg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')
            ], string="Apparent Specific Gravity Conformity", compute="_compute_average_asg_conformity", store=True)



    @api.depends('average_asg','eln_ref','grade')
    def _compute_average_asg_conformity(self):
        
        for record in self:
            record.average_asg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','40b1c07c-0495-4df5-9a14-0c432e24164f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','40b1c07c-0495-4df5-9a14-0c432e24164f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                     # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.average_asg_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_asg - record.average_asg*mu_value
                    upper = record.average_asg + record.average_asg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_asg_conformity = 'pass'
                        break
                    else:
                        record.average_asg_conformity = 'fail'

    average_asg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Apparent Specific Gravity NABL", compute="_compute_average_asg_nabl", store=True)

    @api.depends('average_asg','eln_ref','grade')
    def _compute_average_asg_nabl(self):
        
        for record in self:
            record.average_asg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','40b1c07c-0495-4df5-9a14-0c432e24164f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','40b1c07c-0495-4df5-9a14-0c432e24164f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_asg - record.average_asg*mu_value
                    upper = record.average_asg + record.average_asg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_asg_nabl = 'pass'
                        break
                    else:
                        record.average_asg_nabl = 'fail'

    average_ap = fields.Float(string="Apparent Porosity, %",compute="_compute_average_ap",digits=(12,2),store=True)

    @api.depends('child_lines_asgapw.apparent_porosity')
    def _compute_average_ap(self):
        for record in self:
            ap = record.child_lines_asgapw.mapped('apparent_porosity')
            if ap:
                record.average_ap = sum(ap) / len(ap)
            else:
                record.average_ap = 0.0

    average_ap_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')
            ], string="Apparent Porosity Conformity", compute="_compute_average_ap_conformity", store=True)



    @api.depends('average_ap','eln_ref','grade')
    def _compute_average_ap_conformity(self):
        
        for record in self:
            record.average_ap_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','92a28155-9d10-4e98-8130-819e4a763891')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','92a28155-9d10-4e98-8130-819e4a763891')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                     # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.average_ap_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_ap - record.average_ap*mu_value
                    upper = record.average_ap + record.average_ap*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_ap_conformity = 'pass'
                        break
                    else:
                        record.average_ap_conformity = 'fail'

    average_ap_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Apparent Porosity NABL", compute="_compute_average_ap_nabl", store=True)

    @api.depends('average_ap','eln_ref','grade')
    def _compute_average_ap_nabl(self):
        
        for record in self:
            record.average_ap_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','92a28155-9d10-4e98-8130-819e4a763891')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','92a28155-9d10-4e98-8130-819e4a763891')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_ap - record.average_ap*mu_value
                    upper = record.average_ap + record.average_ap*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_ap_nabl = 'pass'
                        break
                    else:
                        record.average_ap_nabl = 'fail'


    average_wa = fields.Float(string="Water Absorption, %",compute="_compute_average_wa",digits=(12,2),store=True)

    @api.depends('child_lines_asgapw.water_absorption')
    def _compute_average_wa(self):
        for record in self:
            wa = record.child_lines_asgapw.mapped('water_absorption')
            if wa:
                record.average_wa = sum(wa) / len(wa)
            else:
                record.average_wa = 0.0

    average_wa_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')
            ], string="Water Absorption Conformity", compute="_compute_average_wa_conformity", store=True)



    @api.depends('average_wa','eln_ref','grade')
    def _compute_average_wa_conformity(self):
        
        for record in self:
            record.average_wa_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cea73556-7261-4a40-a72e-6961e80e374f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cea73556-7261-4a40-a72e-6961e80e374f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                     # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.average_wa_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_wa - record.average_wa*mu_value
                    upper = record.average_wa + record.average_wa*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_wa_conformity = 'pass'
                        break
                    else:
                        record.average_wa_conformity = 'fail'

    average_wa_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="Water Absorption NABL", compute="_compute_average_wa_nabl", store=True)

    @api.depends('average_wa','eln_ref','grade')
    def _compute_average_wa_nabl(self):
        
        for record in self:
            record.average_wa_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cea73556-7261-4a40-a72e-6961e80e374f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','cea73556-7261-4a40-a72e-6961e80e374f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_wa - record.average_wa*mu_value
                    upper = record.average_wa + record.average_wa*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_wa_nabl = 'pass'
                        break
                    else:
                        record.average_wa_nabl = 'fail'


                

    psg_name = fields.Char("Name",default="True Porosity and True Specific Gravity")
    psg_visible = fields.Boolean("True Porosity and True Specific Gravity Visible",compute="_compute_visible")   

   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_psg = fields.One2many('mechanical.psg.line','parent_id',string="Parameter")

    average_psg = fields.Float(string="True Specific Gravity ",compute="_compute_average_psg",digits=(12,2),store=True)

    @api.depends('child_lines_psg.true_specific')
    def _compute_average_psg(self):
        for record in self:
            psg = record.child_lines_psg.mapped('true_specific')
            if psg:
                record.average_psg = sum(psg) / len(psg)
            else:
                record.average_psg = 0.0
    
    average_psg_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')
            ], string="True Specific Gravity Conformity", compute="_compute_average_psg_conformity", store=True)



    @api.depends('average_psg','eln_ref','grade')
    def _compute_average_psg_conformity(self):
        
        for record in self:
            record.average_psg_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3512d128-3699-451b-aa93-6863ee08e62d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3512d128-3699-451b-aa93-6863ee08e62d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                     # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.average_psg_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_psg - record.average_psg*mu_value
                    upper = record.average_psg + record.average_psg*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_psg_conformity = 'pass'
                        break
                    else:
                        record.average_psg_conformity = 'fail'

    average_psg_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="True Specific Gravity NABL", compute="_compute_average_psg_nabl", store=True)

    @api.depends('average_psg','eln_ref','grade')
    def _compute_average_psg_nabl(self):
        
        for record in self:
            record.average_psg_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3512d128-3699-451b-aa93-6863ee08e62d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3512d128-3699-451b-aa93-6863ee08e62d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_psg - record.average_psg*mu_value
                    upper = record.average_psg + record.average_psg*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_psg_nabl = 'pass'
                        break
                    else:
                        record.average_psg_nabl = 'fail'

    true_porosity = fields.Float(string="True Porosity, % ",compute="_compute_true_porosity",digits=(12,2),store=True)

    @api.depends('average_psg', 'average_asg')
    def _compute_true_porosity(self):
        for record in self:
            if record.average_psg:  # Avoid division by zero
                record.true_porosity = ((record.average_psg - record.average_asg) / record.average_psg) * 100
            else:
                record.true_porosity = 0.0

    true_porosity_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')], string="True Porosity Conformity", compute="_compute_true_porosity_conformity", store=True)




    @api.depends('true_porosity','eln_ref','grade')
    def _compute_true_porosity_conformity(self):
        
        for record in self:
            record.true_porosity_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','47eb5ceb-a3d0-465b-8cd4-d83d4a43a965')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','47eb5ceb-a3d0-465b-8cd4-d83d4a43a965')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                     # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.true_porosity_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.true_porosity - record.true_porosity*mu_value
                    upper = record.true_porosity + record.true_porosity*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.true_porosity_conformity = 'pass'
                        break
                    else:
                        record.true_porosity_conformity = 'fail'

    true_porosity_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="True Porosity NABL", compute="_compute_true_porosity_nabl", store=True)

    @api.depends('true_porosity','eln_ref','grade')
    def _compute_true_porosity_nabl(self):
        
        for record in self:
            record.true_porosity_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','47eb5ceb-a3d0-465b-8cd4-d83d4a43a965')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','47eb5ceb-a3d0-465b-8cd4-d83d4a43a965')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.true_porosity - record.true_porosity*mu_value
                    upper = record.true_porosity + record.true_porosity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.true_porosity_nabl = 'pass'
                        break
                    else:
                        record.true_porosity_nabl = 'fail'

    dry_dencity_natural_name = fields.Char("Name",default="Dry Density")
    dry_dencity_natural_visible = fields.Boolean("Dry Density Visible",compute="_compute_visible")   

   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_dry_dencity_natural = fields.One2many('mechanical.naturaldrydensity.line','parent_id',string="Parameter")

    average_dry_dencity_natural = fields.Float(string="Dry Density, Kg/m3",compute="_compute_average_dry_dencity_natural",digits=(12,2),store=True)

    average_dry_dencity_natural_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')
            ], string="Conformity", compute="_compute_average_dry_dencity_natural_conformity", store=True)



    @api.depends('average_dry_dencity_natural','eln_ref','grade')
    def _compute_average_dry_dencity_natural_conformity(self):
        
        for record in self:
            record.average_dry_dencity_natural_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b0d2809b-94bf-46d5-8aa8-423c86dd7ddc')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b0d2809b-94bf-46d5-8aa8-423c86dd7ddc')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                     # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.average_dry_dencity_natural_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_dry_dencity_natural - record.average_dry_dencity_natural*mu_value
                    upper = record.average_dry_dencity_natural + record.average_dry_dencity_natural*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_dry_dencity_natural_conformity = 'pass'
                        break
                    else:
                        record.average_dry_dencity_natural_conformity = 'fail'

    average_dry_dencity_natural_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_average_dry_dencity_natural_nabl", store=True)

    @api.depends('average_dry_dencity_natural','eln_ref','grade')
    def _compute_average_dry_dencity_natural_nabl(self):
        
        for record in self:
            record.average_dry_dencity_natural_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b0d2809b-94bf-46d5-8aa8-423c86dd7ddc')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b0d2809b-94bf-46d5-8aa8-423c86dd7ddc')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_dry_dencity_natural - record.average_dry_dencity_natural*mu_value
                    upper = record.average_dry_dencity_natural + record.average_dry_dencity_natural*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.average_dry_dencity_natural_nabl = 'pass'
                        break
                    else:
                        record.average_dry_dencity_natural_nabl = 'fail'

    @api.depends('child_lines_dry_dencity_natural.dry_dencity')
    def _compute_average_dry_dencity_natural(self):
        for record in self:
            dry = record.child_lines_dry_dencity_natural.mapped('dry_dencity')
            if dry:
                record.average_dry_dencity_natural = sum(dry) / len(dry)
            else:
                record.average_dry_dencity_natural = 0.0

    
    moisture_natural_name = fields.Char("Name",default="Moisture Content")
    moisture_natural_visible = fields.Boolean("Moisture Content Visible",compute="_compute_visible")   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_moisture_natural = fields.One2many('mechanical.naturalmoisture.line','parent_id',string="Parameter")

    avg_moisture = fields.Float(string="Moisture Content, %" ,digits=(12,1),compute="_compute_average_moisture_natural")

    avg_moisture_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')
            ], string="Conformity", compute="_compute_avg_moisture_conformity", store=True)



    @api.depends('avg_moisture','eln_ref','grade')
    def _compute_avg_moisture_conformity(self):
        
        for record in self:
            record.avg_moisture_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8245b6e4-763b-4cca-bcc0-0068ea2c98bd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8245b6e4-763b-4cca-bcc0-0068ea2c98bd')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                     # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.avg_moisture_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_moisture - record.avg_moisture*mu_value
                    upper = record.avg_moisture + record.avg_moisture*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_moisture_conformity = 'pass'
                        break
                    else:
                        record.avg_moisture_conformity = 'fail'

    avg_moisture_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_moisture_nabl", store=True)

    @api.depends('avg_moisture','eln_ref','grade')
    def _compute_avg_moisture_nabl(self):
        
        for record in self:
            record.avg_moisture_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8245b6e4-763b-4cca-bcc0-0068ea2c98bd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','8245b6e4-763b-4cca-bcc0-0068ea2c98bd')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_moisture - record.avg_moisture*mu_value
                    upper = record.avg_moisture + record.avg_moisture*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_moisture_nabl = 'pass'
                        break
                    else:
                        record.avg_moisture_nabl = 'fail'

    @api.depends('child_lines_dry_dencity_natural.dry_dencity')
    def _compute_average_dry_dencity_natural(self):
        for record in self:
            dry = record.child_lines_dry_dencity_natural.mapped('dry_dencity')
            if dry:
                record.average_dry_dencity_natural = sum(dry) / len(dry)
            else:
                record.average_dry_dencity_natural = 0.0

    @api.depends('child_lines_moisture_natural.moisture_content')
    def _compute_average_moisture_natural(self):
        for record in self:
            moisture = record.child_lines_moisture_natural.mapped('moisture_content')
            if moisture:
                record.avg_moisture = sum(moisture) / len(moisture)
            else:
                record.avg_moisture = 0.0


    scratch_natural_name = fields.Char("Name",default="Scratch hardness according to Moh's Scale")
    scratch_natural_visible = fields.Boolean("Scratch hardness according to Moh's Scale Visible",compute="_compute_visible")   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_scratch_natural = fields.One2many('mechanical.naturalscratch.line','parent_id',string="Parameter")

    avg_scratch = fields.Float(string="Moh's Scratch Hardness" ,digits=(12,1),compute="_compute_average_scratch_natural")

    avg_scratch_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('--', '--')
            ], string="Conformity", compute="_compute_avg_scratch_conformity", store=True)



    @api.depends('avg_scratch','eln_ref','grade')
    def _compute_avg_scratch_conformity(self):
        
        for record in self:
            record.avg_scratch_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4d8ddbd7-f253-4755-b630-08bdab7ac0d9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4d8ddbd7-f253-4755-b630-08bdab7ac0d9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:

                     # Check if permissible limit is '--' or empty
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.avg_scratch_conformity = '--'
                        break

                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_scratch - record.avg_scratch*mu_value
                    upper = record.avg_scratch + record.avg_scratch*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_scratch_conformity = 'pass'
                        break
                    else:
                        record.avg_scratch_conformity = 'fail'

    avg_scratch_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL')], string="NABL", compute="_compute_avg_scratch_nabl", store=True)

    @api.depends('avg_scratch','eln_ref','grade')
    def _compute_avg_scratch_nabl(self):
        
        for record in self:
            record.avg_scratch_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4d8ddbd7-f253-4755-b630-08bdab7ac0d9')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','4d8ddbd7-f253-4755-b630-08bdab7ac0d9')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_scratch - record.avg_scratch*mu_value
                    upper = record.avg_scratch + record.avg_scratch*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_scratch_nabl = 'pass'
                        break
                    else:
                        record.avg_scratch_nabl = 'fail'

    @api.depends('child_lines_scratch_natural.scratch_hardness')
    def _compute_average_scratch_natural(self):
        for record in self:
            scratch = record.child_lines_scratch_natural.mapped('scratch_hardness')
            if scratch:
                record.avg_scratch = sum(scratch) / len(scratch)
            else:
                record.avg_scratch = 0.0


    compressive_natural_name = fields.Char("Name",default="Compressive strength")
    compressive_natural_visible = fields.Boolean("Compressive strength Visible",compute="_compute_visible")   

    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    child_lines_compressive_natural1 = fields.One2many('mechanical.naturalcompressive1.line','parent_id',string="Parameter",default=lambda self: self._default_child_lines_compressive_natural1())

    avg_uniaxial_compressive = fields.Float(string="Average UniAxial Compressive Strength, N/mm2",digits=(12,2),compute="_compute_average_values")
    avg_kg = fields.Float(string="Average kg/cm2",digits=(12,4),compute="_compute_average_values")

    dry_state_perpendicular = fields.Float(string="Dry State- Perpendicular to the plane",digits=(12,4),compute="_compute_dry_state_perpendicular")

    @api.model
    def _default_child_lines_compressive_natural1(self):
        default_lines = [
            (0, 0, {'condition': 'Dry / Perpendicular to the Plane'}),
            (0, 0, {'condition': 'Dry / Perpendicular to the Plane'}),
            (0, 0, {'condition': 'Dry / Perpendicular to the Plane'}),
            (0, 0, {'condition': 'Dry / Perpendicular to the Plane'}),
            (0, 0, {'condition': 'Dry / Perpendicular to the Plane'}),
         
        ]
        return default_lines

    @api.depends('avg_kg')
    def _compute_dry_state_perpendicular(self):
        for record in self:
            record.dry_state_perpendicular = record.avg_kg

    @api.depends('child_lines_compressive_natural1.uniaxial_compressive', 'child_lines_compressive_natural1.kg')
    def _compute_average_values(self):
        for record in self:
            lines = record.child_lines_compressive_natural1
            if lines:
                uniaxial_compressive_values = lines.mapped('uniaxial_compressive')
                kg_values = lines.mapped('kg')

                record.avg_uniaxial_compressive = sum(uniaxial_compressive_values) / len(uniaxial_compressive_values) if uniaxial_compressive_values else 0.0
                record.avg_kg = sum(kg_values) / len(kg_values) if kg_values else 0.0
            else:
                record.avg_uniaxial_compressive = 0.0
                record.avg_kg = 0.0


    child_lines_compressive_natural2 = fields.One2many('mechanical.naturalcompressive2.line','parent_id',string="Parameter",default=lambda self: self._default_child_lines_compressive_natural2())

    @api.model
    def _default_child_lines_compressive_natural2(self):
        default_lines = [
            (0, 0, {'condition1': 'Dry / Parallel to the Plane'}),
            (0, 0, {'condition1': 'Dry / Parallel to the Plane'}),
            (0, 0, {'condition1': 'Dry / Parallel to the Plane'}),
            (0, 0, {'condition1': 'Dry / Parallel to the Plane'}),
            (0, 0, {'condition1': 'Dry / Parallel to the Plane'}),
         
        ]
        return default_lines

    avg_uniaxial_compressive2 = fields.Float(string="Average UniAxial Compressive Strength, N/mm2",digits=(12,2),compute="_compute_average_values2")
    avg_kg2 = fields.Float(string="Average kg/cm2",digits=(12,4),compute="_compute_average_values2")

    dry_state_paraller = fields.Float(string="Dry State- Parallel to the plane",digits=(12,4),compute="_compute_dry_state_paraller")

    @api.depends('avg_kg2')
    def _compute_dry_state_paraller(self):
        for record in self:
            record.dry_state_paraller = record.avg_kg2

    @api.depends('child_lines_compressive_natural2.uniaxial_compressive1', 'child_lines_compressive_natural2.kg1')
    def _compute_average_values2(self):
        for record in self:
            lines = record.child_lines_compressive_natural2
            if lines:
                uniaxial_compressive1_values = lines.mapped('uniaxial_compressive1')
                kg1_values = lines.mapped('kg1')

                record.avg_uniaxial_compressive2 = sum(uniaxial_compressive1_values) / len(uniaxial_compressive1_values) if uniaxial_compressive1_values else 0.0
                record.avg_kg2 = sum(kg1_values) / len(kg1_values) if kg1_values else 0.0
            else:
                record.avg_uniaxial_compressive2 = 0.0
                record.avg_kg2 = 0.0

    child_lines_compressive_natural3 = fields.One2many('mechanical.naturalcompressive3.line','parent_id',string="Parameter",default=lambda self: self._default_child_lines_compressive_natural3())

    @api.model
    def _default_child_lines_compressive_natural3(self):
        default_lines = [
            (0, 0, {'condition3': 'Wet / Perpendicular to the Plane'}),
            (0, 0, {'condition3': 'Wet / Perpendicular to the Plane'}),
            (0, 0, {'condition3': 'Wet / Perpendicular to the Plane'}),
            (0, 0, {'condition3': 'Wet / Perpendicular to the Plane'}),
            (0, 0, {'condition3': 'Wet / Perpendicular to the Plane'}),
         
        ]
        return default_lines

    avg_uniaxial_compressive3 = fields.Float(string="Average UniAxial Compressive Strength, N/mm2",digits=(12,2),compute="_compute_average_values3")
    avg_kg3 = fields.Float(string="Average kg/cm2",digits=(12,4),compute="_compute_average_values3")

    wet_state_perpendicular = fields.Float(string="Wet State- Perpendicular to the plane",digits=(12,4),compute="_compute_wet_state_perpendicular")

    @api.depends('avg_kg3')
    def _compute_wet_state_perpendicular(self):
        for record in self:
            record.wet_state_perpendicular = record.avg_kg3

    @api.depends('child_lines_compressive_natural3.uniaxial_compressive3', 'child_lines_compressive_natural3.kg3')
    def _compute_average_values3(self):
        for record in self:
            lines = record.child_lines_compressive_natural3
            if lines:
                uniaxial_compressive3_values = lines.mapped('uniaxial_compressive3')
                kg3_values = lines.mapped('kg3')

                record.avg_uniaxial_compressive3 = sum(uniaxial_compressive3_values) / len(uniaxial_compressive3_values) if uniaxial_compressive3_values else 0.0
                record.avg_kg3 = sum(kg3_values) / len(kg3_values) if kg3_values else 0.0
            else:
                record.avg_uniaxial_compressive3 = 0.0
                record.avg_kg3 = 0.0

    child_lines_compressive_natural4 = fields.One2many('mechanical.naturalcompressive4.line','parent_id',string="Parameter",default=lambda self: self._default_child_lines_compressive_natural4())

    @api.model
    def _default_child_lines_compressive_natural4(self):
        default_lines = [
            (0, 0, {'condition4': 'Wet / Parallel to the Plane'}),
            (0, 0, {'condition4': 'Wet / Parallel to the Plane'}),
            (0, 0, {'condition4': 'Wet / Parallel to the Plane'}),
            (0, 0, {'condition4': 'Wet / Parallel to the Plane'}),
            (0, 0, {'condition4': 'Wet / Parallel to the Plane'}),
         
        ]
        return default_lines

    avg_uniaxial_compressive4 = fields.Float(string="Average UniAxial Compressive Strength, N/mm2",digits=(12,2),compute="_compute_average_values4")
    avg_kg4 = fields.Float(string="Average kg/cm2",digits=(12,4),compute="_compute_average_values4")

    wet_state_paraller = fields.Float(string="Wet State- Parallel to the plane",digits=(12,4),compute="_compute_wet_state_paraller")

    @api.depends('avg_kg4')
    def _compute_wet_state_paraller(self):
        for record in self:
            record.wet_state_paraller = record.avg_kg4

    @api.depends('child_lines_compressive_natural4.uniaxial_compressive4', 'child_lines_compressive_natural4.kg4')
    def _compute_average_values4(self):
        for record in self:
            lines = record.child_lines_compressive_natural4
            if lines:
                uniaxial_compressive4_values = lines.mapped('uniaxial_compressive4')
                kg4_values = lines.mapped('kg4')

                record.avg_uniaxial_compressive4 = sum(uniaxial_compressive4_values) / len(uniaxial_compressive4_values) if uniaxial_compressive4_values else 0.0
                record.avg_kg4 = sum(kg4_values) / len(kg4_values) if kg4_values else 0.0
            else:
                record.avg_uniaxial_compressive4 = 0.0
                record.avg_kg4 = 0.0



         ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.asgapw_visible = False
            record.psg_visible = False
            record.dry_dencity_natural_visible = False
            record.moisture_natural_visible = False
            record.scratch_natural_visible = False
            record.compressive_natural_visible = False
          
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
                if sample.internal_id == "7c729ec4-ddf2-49ce-9839-715d30f9ccb5":
                    record.asgapw_visible = True

                if sample.internal_id == "396d6df0-37de-4fa7-90f7-08ea7b6b59a6":
                    record.psg_visible = True

                if sample.internal_id == "b0d2809b-94bf-46d5-8aa8-423c86dd7ddc":
                    record.dry_dencity_natural_visible = True

                if sample.internal_id == "8245b6e4-763b-4cca-bcc0-0068ea2c98bd":
                    record.moisture_natural_visible = True
                
                if sample.internal_id == "4d8ddbd7-f253-4755-b630-08bdab7ac0d9":
                    record.scratch_natural_visible = True

                if sample.internal_id == "c3b03713-2274-4d60-ba93-43cbbf385fc7":
                    record.compressive_natural_visible = True


             
              




    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:



            if result.parameter.internal_id == '7c729ec4-ddf2-49ce-9839-715d30f9ccb5':
                # result.result_char = self.initial_setting_time_minutes_unrounded
                result.calculated = True
                # if self.initial_setting_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '06463454b28-7a9b-4616-bad5-88eb1b26070834':
                # result.result_char = round(self.average_cememt_flatness,2)
                result.calculated = True
                # if self.average_cememt_flatness_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'b0d2809b-94bf-46d5-8aa8-423c86dd7ddc':
                result.result_char = round(self.average_dry_dencity_natural,2)
                result.calculated = True
                if self.average_dry_dencity_natural_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '8245b6e4-763b-4cca-bcc0-0068ea2c98bd':
                result.result_char = round(self.avg_moisture,2)
                result.calculated = True
                if self.avg_moisture_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '4d8ddbd7-f253-4755-b630-08bdab7ac0d9':
                result.result_char = round(self.avg_scratch,2)
                result.calculated = True
                if self.avg_scratch_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'c3b03713-2274-4d60-ba93-43cbbf385fc7':
                # result.result_char = round(self.average_length,2)
                result.calculated = True
                # if self.average_length_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '40b1c07c-0495-4df5-9a14-0c432e24164f':
                result.result_char = round(self.average_asg,2)
                result.calculated = True
                if self.average_asg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '92a28155-9d10-4e98-8130-819e4a763891':
                result.result_char = round(self.average_ap,2)
                result.calculated = True
                if self.average_ap_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'cea73556-7261-4a40-a72e-6961e80e374f':
                result.result_char = round(self.average_wa,2)
                result.calculated = True
                if self.average_wa_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '3512d128-3699-451b-aa93-6863ee08e62d':
                result.result_char = round(self.average_psg,2)
                result.calculated = True
                if self.average_psg_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '47eb5ceb-a3d0-465b-8cd4-d83d4a43a965':
                result.result_char = round(self.true_porosity,2)
                result.calculated = True
                if self.true_porosity_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '396d6df0-37de-4fa7-90f7-08ea7b6b59a6':
                # result.result_char = round(self.true_porosity,2)
                result.calculated = True
                # if self.true_porosity_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '83a4b3bf-95e1-49ee-ab59-8e9fbdd72924':
                # result.result_char = round(self.true_porosity,2)
                result.calculated = True
                # if self.true_porosity_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '2b881570-fb63-4a94-9de8-eaf89209071a':
                # result.result_char = round(self.true_porosity,2)
                result.calculated = True
                # if self.true_porosity_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'a44ee427-6467-45b2-b423-8c6b1b2c02d7':
                # result.result_char = round(self.true_porosity,2)
                result.calculated = True
                # if self.true_porosity_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '109f62cd-1855-4a42-94a9-63813ac1ef85':
                # result.result_char = round(self.true_porosity,2)
                result.calculated = True
                # if self.true_porosity_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
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
        record = super(NaturalBuildingStone, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        # records = self.env['lerm.eln'].sudo().search([('id','=', record.eln_id.id)]).parameters_result
        # print("records",records)
        # self.sample_parameters = records
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)



    def get_all_fields(self):
        record = self.env['mechanical.natural.bulding.stone'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


class AsgapwLine(models.Model):
    _name = "mechanical.asgapwline.line"
    parent_id = fields.Many2one('mechanical.natural.bulding.stone',string="Parent Id")
   
    sr_no = fields.Integer(string="Observations",readonly=True, copy=False, default=1)

    weight_of_saturated = fields.Float(string="Weight of Saturated Surface Dry Test piece, g (B)",digits=(12,2))
    quantity_of_water = fields.Float(string="Quantity of water added in 1000-ml jar containing the test piece, g (C)",digits=(12,2))
    weight_of_oven = fields.Float(string="Weight of oven-dry test piece (A)",digits=(12,2))
    apparent_specific = fields.Float(string="Apparent Specific Gravity A/(1000-C)" ,compute="_compute_apparent_specific",digits=(12,2))
    apparent_porosity = fields.Float(string="Apparent Porosity, % (B-A)/(1000-C)*100",digits=(12,2),compute="_compute_apparent_porosity")
    water_absorption = fields.Float(string="Water Absorption, % (B-A)/A*100",digits=(12,2),compute="_compute_water_absorption")


    @api.depends('weight_of_oven', 'quantity_of_water')
    def _compute_apparent_specific(self):
        for record in self:
            if record.quantity_of_water != 1000:
                record.apparent_specific = record.weight_of_oven / (1000 - record.quantity_of_water)
            else:
                record.apparent_specific = 0.0  # Avoid division by zero

    @api.depends('weight_of_saturated', 'weight_of_oven','quantity_of_water')
    def _compute_apparent_porosity(self):
        for record in self:
            if record.quantity_of_water != 1000:
                record.apparent_porosity = (
                    (record.weight_of_saturated - record.weight_of_oven) / 
                    (1000 - record.quantity_of_water)
                ) * 100
            else:
                record.apparent_porosity = 0.0  # Avoid division by zero

    @api.depends('weight_of_saturated', 'weight_of_oven')
    def _compute_water_absorption(self):
        for record in self:
            if record.weight_of_oven != 0:
                record.water_absorption = (
                    (record.weight_of_saturated - record.weight_of_oven) / 
                    record.weight_of_oven
                ) * 100
            else:
                record.water_absorption = 0.0  # Avoid division by zero
    

  
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(AsgapwLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1

class PsgLine(models.Model):
    _name = "mechanical.psg.line"
    parent_id = fields.Many2one('mechanical.natural.bulding.stone',string="Parent Id")
   
    sr_no = fields.Integer(string="Observations",readonly=True, copy=False, default=1)

    mass_empty = fields.Float(string="Mass of Empty Specific Gravity Bottle,g W1",digits=(12,3))
    mass_specific = fields.Float(string="Mass of Specific Gravity bottle + Powder,g W2",digits=(12,3))
    mass_specific_gravity = fields.Float(string="Mass of Specific Gravity bottle + Powder + Distilled Water, g W3",digits=(12,3))
    mass_specific_bottle = fields.Float(string="Mass of Specific Gravity bottle + Distilled Water,g W4 A/(1000-C)" ,digits=(12,3))
    true_specific = fields.Float(string="True Specific Gravity, (W2-W1)/ (W4-W1)-(W3-W2)",digits=(12,2),compute="_compute_true_specific")


    @api.depends('mass_empty', 'mass_specific', 'mass_specific_gravity', 'mass_specific_bottle')
    def _compute_true_specific(self):
        for record in self:
            if (record.mass_specific_bottle - record.mass_empty) != (record.mass_specific_gravity - record.mass_specific):
                try:
                    record.true_specific = (record.mass_specific - record.mass_empty) / (
                        (record.mass_specific_bottle - record.mass_empty) - (record.mass_specific_gravity - record.mass_specific)
                    )
                except ZeroDivisionError:
                    record.true_specific = 0.0
            else:
                record.true_specific = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(PsgLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class DryDensityLine(models.Model):
    _name = "mechanical.naturaldrydensity.line"
    parent_id = fields.Many2one('mechanical.natural.bulding.stone',string="Parent Id")
   
    sr_no = fields.Integer(string="Observations",readonly=True, copy=False, default=1)

    mass_oven = fields.Float(string="Mass of Oven Dried Sample, g",digits=(12,3))
    volume_sample = fields.Float(string="Volume of Sample, m3",digits=(12,3))
    dry_dencity = fields.Float(string="Dry Density of Sample, Kg/m3",digits=(12,1),compute="_compute_dry_dencity")
    dry_dencity_sample = fields.Float(string="Dry Density of Sample, g/cc" ,digits=(12,2),compute="_compute_dry_dencity")

    @api.depends('mass_oven', 'volume_sample')
    def _compute_dry_dencity(self):
        for record in self:
            if record.volume_sample:  # Avoid division by zero
                record.dry_dencity = (record.mass_oven / record.volume_sample) * 1_000_000
                record.dry_dencity_sample = record.dry_dencity / 1_000
            else:
                record.dry_dencity = 0.0
                record.dry_dencity_sample = 0.0


    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(DryDensityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class MoistureContentLine(models.Model):
    _name = "mechanical.naturalmoisture.line"
    parent_id = fields.Many2one('mechanical.natural.bulding.stone',string="Parent Id")
   
    sr_no = fields.Integer(string="Observations",readonly=True, copy=False, default=1)

    mass_sample = fields.Float(string="Mass of Sample before Drying, g",digits=(12,3))
    volume_oven = fields.Float(string="Mass of Oven Dried Sample, g",digits=(12,3))
    moisture_content = fields.Float(string="Moisture Content, %",digits=(12,2),compute="_compute_moisture_content")


    @api.depends('mass_sample', 'volume_oven')
    def _compute_moisture_content(self):
        for record in self:
            if record.volume_oven:  # Avoid division by zero
                record.moisture_content = ((record.mass_sample - record.volume_oven) / record.volume_oven) * 100
            else:
                record.moisture_content = 0.0
    

    
    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MoistureContentLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class ScratchhardnessLine(models.Model):
    _name = "mechanical.naturalscratch.line"
    parent_id = fields.Many2one('mechanical.natural.bulding.stone',string="Parent Id")
   
    sr_no = fields.Integer(string="Observations",readonly=True, copy=False, default=1)

    scratch_hardness = fields.Float(string="Moh's Scratch Hardness",digits=(12,3))
   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(ScratchhardnessLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class CompressivestrengthLine(models.Model):
    _name = "mechanical.naturalcompressive1.line"
    parent_id = fields.Many2one('mechanical.natural.bulding.stone',string="Parent Id")
   
    sr_no = fields.Integer(string="Sample No.",readonly=True, copy=False, default=1)

    condition = fields.Char(string="Condition")
    length = fields.Float(string="Length ,mm",digits=(12,2))
    width = fields.Float(string="Width ,mm",digits=(12,2))
    bearing_surface = fields.Float(string="Bearing Surface Area, mm x mm",digits=(12,3),compute="_compute_bearing_surface")
    max_compressive = fields.Float(string="Max Compressive Load for Failure, KN",digits=(12,1))
    uniaxial_compressive = fields.Float(string="UniAxial Compressive Strength, N/mm2",digits=(12,3),compute="_compute_compressive_values")
    kg = fields.Float(string="kg/cm2",digits=(12,4),compute="_compute_compressive_values")

  


    @api.depends('max_compressive', 'bearing_surface')
    def _compute_compressive_values(self):
        for record in self:
            if record.bearing_surface:  # Avoid division by zero
                record.uniaxial_compressive = (record.max_compressive / record.bearing_surface) * 1000
                record.kg = record.uniaxial_compressive * 10.197
            else:
                record.uniaxial_compressive = 0.0
                record.kg = 0.0
    
    @api.depends('length', 'width')
    def _compute_bearing_surface(self):
        for record in self:
            if record.length and record.width:
                record.bearing_surface = record.length * record.width
            else:
                record.bearing_surface = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(CompressivestrengthLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class CompressivestrengthLine2(models.Model):
    _name = "mechanical.naturalcompressive2.line"
    parent_id = fields.Many2one('mechanical.natural.bulding.stone',string="Parent Id")
   
    sr_no = fields.Integer(string="Sample No.",readonly=True, copy=False, default=1)

    condition1 = fields.Char(string="Condition")
    length1 = fields.Float(string="Length ,mm",digits=(12,2))
    width1 = fields.Float(string="Width ,mm",digits=(12,2))
    bearing_surface1 = fields.Float(string="Bearing Surface Area, mm x mm",digits=(12,3),compute="_compute_bearing_surface1")
    max_compressive1 = fields.Float(string="Max Compressive Load for Failure, KN",digits=(12,1))
    uniaxial_compressive1 = fields.Float(string="UniAxial Compressive Strength, N/mm2",digits=(12,3),compute="_compute_compressive_values1")
    kg1 = fields.Float(string="kg/cm2",digits=(12,4),compute="_compute_compressive_values1")

    @api.depends('length1', 'width1')
    def _compute_bearing_surface1(self):
        for record in self:
            if record.length1 and record.width1:
                record.bearing_surface1 = record.length1 * record.width1
            else:
                record.bearing_surface1 = 0.0

  


    @api.depends('max_compressive1', 'bearing_surface1')
    def _compute_compressive_values1(self):
        for record in self:
            if record.bearing_surface1:  # Avoid division by zero
                record.uniaxial_compressive1 = (record.max_compressive1 / record.bearing_surface1) * 1000
                record.kg1 = record.uniaxial_compressive1 * 10.197
            else:
                record.uniaxial_compressive1 = 0.0
                record.kg1 = 0.0
   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(CompressivestrengthLine2, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class CompressivestrengthLine3(models.Model):
    _name = "mechanical.naturalcompressive3.line"
    parent_id = fields.Many2one('mechanical.natural.bulding.stone',string="Parent Id")
   
    sr_no = fields.Integer(string="Sample No.",readonly=True, copy=False, default=1)

    condition3 = fields.Char(string="Condition")
    length3 = fields.Float(string="Length ,mm",digits=(12,2))
    width3 = fields.Float(string="Width ,mm",digits=(12,2))
    bearing_surface3 = fields.Float(string="Bearing Surface Area, mm x mm",digits=(12,3),compute="_compute_bearing_surface3")
    max_compressive3 = fields.Float(string="Max Compressive Load for Failure, KN",digits=(12,1))
    uniaxial_compressive3 = fields.Float(string="UniAxial Compressive Strength, N/mm2",digits=(12,3),compute="_compute_compressive_values3")
    kg3 = fields.Float(string="kg/cm2",digits=(12,4),compute="_compute_compressive_values3")

    @api.depends('length3', 'width3')
    def _compute_bearing_surface3(self):
        for record in self:
            if record.length3 and record.width3:
                record.bearing_surface3 = record.length3 * record.width3
            else:
                record.bearing_surface3 = 0.0

  


    @api.depends('max_compressive3', 'bearing_surface3')
    def _compute_compressive_values3(self):
        for record in self:
            if record.bearing_surface3:  # Avoid division by zero
                record.uniaxial_compressive3 = (record.max_compressive3 / record.bearing_surface3) * 1000
                record.kg3 = record.uniaxial_compressive3 * 10.197
            else:
                record.uniaxial_compressive3 = 0.0
                record.kg3 = 0.0
   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(CompressivestrengthLine3, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class CompressivestrengthLine4(models.Model):
    _name = "mechanical.naturalcompressive4.line"
    parent_id = fields.Many2one('mechanical.natural.bulding.stone',string="Parent Id")
   
    sr_no = fields.Integer(string="Sample No.",readonly=True, copy=False, default=1)

    condition4 = fields.Char(string="Condition")
    length4 = fields.Float(string="Length ,mm",digits=(12,2))
    width4 = fields.Float(string="Width ,mm",digits=(12,2))
    bearing_surface4 = fields.Float(string="Bearing Surface Area, mm x mm",digits=(12,3),compute="_compute_bearing_surface4")
    max_compressive4 = fields.Float(string="Max Compressive Load for Failure, KN",digits=(12,1))
    uniaxial_compressive4 = fields.Float(string="UniAxial Compressive Strength, N/mm2",digits=(12,3),compute="_compute_compressive_values4")
    kg4 = fields.Float(string="kg/cm2",digits=(12,4),compute="_compute_compressive_values4")

    @api.depends('length4', 'width4')
    def _compute_bearing_surface4(self):
        for record in self:
            if record.length4 and record.width4:
                record.bearing_surface4 = record.length4 * record.width4
            else:
                record.bearing_surface4 = 0.0

  


    @api.depends('max_compressive4', 'bearing_surface4')
    def _compute_compressive_values4(self):
        for record in self:
            if record.bearing_surface4:  # Avoid division by zero
                record.uniaxial_compressive4 = (record.max_compressive4 / record.bearing_surface4) * 1000
                record.kg4 = record.uniaxial_compressive4 * 10.197
            else:
                record.uniaxial_compressive4 = 0.0
                record.kg4 = 0.0
   

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(CompressivestrengthLine4, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class NaturalStoneNotes(models.Model):
    _name = "mechanical.natural.bulding.stone.notes"

    parent_id = fields.Many2one('mechanical.natural.bulding.stone',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")