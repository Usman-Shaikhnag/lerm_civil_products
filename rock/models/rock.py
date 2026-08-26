from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math
from math import pi


class MechanicalRock(models.Model):
    _name = "mechanical.rock"
    _inherit = "lerm.eln"
    _rec_name = "name_rock"


    name_rock = fields.Char("Name",default="ROCK")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    temprature = fields.Float("Temperature (°C)", digits=(10,2))
    humidity = fields.Float("Humidity (%)", digits=(10,2))

    week_no = fields.Char("Week No")

    other_details = fields.Char("Other Details")

    condition = fields.Char("Condition")

    description_work = fields.Text("Description Of Work")


    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'mechanical.rock.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }




    # remark

    notes_id = fields.One2many('rock.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(MechanicalRock, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The report shall not be reproduced in full or partially without written approval of the laboratory HOD/CEO/Maganement.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'Sampling is not done by us unless mentioned otherwide.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'without a QR Code and hologram this report is considered invalid.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'The Result listed refer only to tested samples & applicable parameter Endorsement of product is neither interred nor inplied.',
            }),

            (0, 0, {
                'sr_no': 'e',
                'notes': 'The use or report for arbitration, publicity & evidence in legal dispute is forbidden except with prior written consent NBML Lab.',
            }),
             (0, 0, {
                'sr_no': 'f',
                'notes': 'All disputed are subject to Raipur jurisdiction 7 days correction to this report invalidates this report.',
            }),

             (0, 0, {
                'sr_no': 'g',
                'notes': 'Sample will be destroyed after 30-days from the date of test report unless otherwise Specified.',
            }),
        ]

        res['notes_id'] = default_notes
        return res
    




    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id



    child_lines = fields.One2many('mechanical.rock.line','parent_id',string="Parameter")
    
    avg_porosity = fields.Float("Average porosity",compute="_compute_avg_porosity")
    avg_water_absorption = fields.Float("Average Water Absorption",compute="_compute_water_absorption")
    avg_dry_density = fields.Float("Dry Density",compute="_compute_avg_dry_density")
    avg_saturated_spc_gravity = fields.Float("Saturated Specific Gravity",compute="_compute_saturated_spc_gravity")


    

    @api.depends('child_lines.porosity')
    def _compute_avg_porosity(self):
        for record in self:
            porosity_values = [line.porosity for line in record.child_lines]
            if porosity_values:
                record.avg_porosity = sum(porosity_values) / len(porosity_values)
            else:
                record.avg_porosity = 0.0


    @api.depends('child_lines.water_absorption')
    def _compute_water_absorption(self):
        for record in self:
            water_absorption_values = [line.water_absorption for line in record.child_lines]
            if water_absorption_values:
                record.avg_water_absorption = sum(water_absorption_values) / len(water_absorption_values)
            else:
                record.avg_water_absorption = 0.0


    @api.depends('child_lines.dry_density')
    def _compute_avg_dry_density(self):
        for record in self:
            dry_density_values = [line.dry_density for line in record.child_lines]
            if dry_density_values:
                record.avg_dry_density = sum(dry_density_values) / len(dry_density_values)
            else:
                record.avg_dry_density = 0.0

    @api.depends('child_lines.saturated_spc_gravity')
    def _compute_saturated_spc_gravity(self):
        for record in self:
            saturated_spc_gravity_values = [line.saturated_spc_gravity for line in record.child_lines]
            if saturated_spc_gravity_values:
                record.avg_saturated_spc_gravity = sum(saturated_spc_gravity_values) / len(saturated_spc_gravity_values)
            else:
                record.avg_saturated_spc_gravity = 0.0


    
    #usc
    # parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    usc_name = fields.Char("Name",default="UCS")
    usc_visible = fields.Boolean("USC Visible",compute="_compute_visible")
    child_lines1 = fields.One2many('mechanical.usc.line','parent_id',string="Parameter")
    
    avg_usc = fields.Float("Average USC",compute="_compute_avg_usc")

    avg_usc_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_usc_conformity", store=True)

    @api.depends('avg_usc','eln_ref','grade')
    def _compute_avg_usc_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_usc_conformity = 'na'
                continue

            record.avg_usc_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_usc - record.avg_usc*mu_value
                    upper = record.avg_usc + record.avg_usc*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_usc_conformity = 'pass'
                        break
                    else:
                        record.avg_usc_conformity = 'fail'

    avg_usc_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_usc_nabl", store=True)

    @api.depends('avg_usc','eln_ref','grade')
    def _compute_avg_usc_nabl(self):
        
        for record in self:
            record.avg_usc_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_usc - record.avg_usc*mu_value
            upper = record.avg_usc + record.avg_usc*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_usc_nabl = 'pass'
                break
            else:
                record.avg_usc_nabl = 'fail'


    @api.depends('child_lines1.usc')
    def _compute_avg_usc(self):
        for record in self:
            usc_values = record.child_lines1.mapped('usc')
            if usc_values:
                record.avg_usc = sum(usc_values) / len(usc_values)
            else:
                record.avg_usc = 0

    porosity_visible = fields.Boolean("Porosity Visible",compute="_compute_visible")
    specific_gravity_visible = fields.Boolean("Saturated Specific Gravity Visible",compute="_compute_visible")
    dry_density_visible = fields.Boolean("Dry Density Visible",compute="_compute_visible")
    water_absorption_visible = fields.Boolean("USC Visible",compute="_compute_visible")


      # parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    cerchar_abrsivity_name = fields.Char("Name",default="Cerchar Abrsivity Index")
    cerchar_abrsivity_visible = fields.Boolean("Cerchar Abrsivity Index Visible",compute="_compute_visible")

    child_lines_cerchar_abrsivity = fields.One2many('mechanical.rock.cerchar.abrsivity.line', 'parent_id', string='Wear Flat Diameters')
    cai = fields.Float('Cerchar Abrasivity Index', compute='_compute_cai', store=True)

    cai_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_cai_conformity", store=True)

    @api.depends('cai','eln_ref','grade')
    def _compute_cai_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.cai_conformity = 'na'
                continue

            record.cai_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-89d87355786tt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-89d87355786tt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.cai - record.cai*mu_value
                    upper = record.cai + record.cai*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.cai_conformity = 'pass'
                        break
                    else:
                        record.cai_conformity = 'fail'

    cai_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_cai_nabl", store=True)

    @api.depends('cai','eln_ref','grade')
    def _compute_cai_nabl(self):
        
        for record in self:
            record.cai_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-89d87355786tt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-89d87355786tt')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.cai - record.cai*mu_value
            upper = record.cai + record.cai*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.cai_nabl = 'pass'
                break
            else:
                record.cai_nabl = 'fail'


    @api.depends('child_lines_cerchar_abrsivity.value')
    def _compute_cai(self):
        for record in self:
            diameters = [d.value for d in record.child_lines_cerchar_abrsivity if d.value]
            if diameters:
                average = sum(diameters) / len(diameters)
                record.cai = average * 10
            else:
                record.cai = 0.0


    modulus_of_elasticity_name = fields.Char("Name",default="Modulus of Elasticity")
    modulus_of_elasticity_visible = fields.Boolean("Modulus of Elasticity Visible",compute="_compute_visible")

    modulus_of_elasticity_line_ids = fields.One2many("mechanical.rock.elasticity.line", "parent_id", string="Test Readings")

    modulus_e = fields.Float(string="Modulus of Elasticity E (MPa)", compute="_compute_modulus", store=True)

    modulus_e_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_modulus_e_conformity", store=True)

    @api.depends('modulus_e','eln_ref','grade')
    def _compute_modulus_e_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.modulus_e_conformity = 'na'
                continue

            record.modulus_e_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-9654tyu145er2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-9654tyu145er2')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.modulus_e - record.modulus_e*mu_value
                    upper = record.modulus_e + record.modulus_e*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.modulus_e_conformity = 'pass'
                        break
                    else:
                        record.modulus_e_conformity = 'fail'

    modulus_e_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_modulus_e_nabl", store=True)

    @api.depends('modulus_e','eln_ref','grade')
    def _compute_modulus_e_nabl(self):
        
        for record in self:
            record.modulus_e_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-9654tyu145er2')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','71e24ae1-b9a9-41cb-86a5-9654tyu145er2')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.modulus_e - record.modulus_e*mu_value
            upper = record.modulus_e + record.modulus_e*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.modulus_e_nabl = 'pass'
                break
            else:
                record.modulus_e_nabl = 'fail'

    @api.depends("modulus_of_elasticity_line_ids.stress", "modulus_of_elasticity_line_ids.strain")
    def _compute_modulus(self):
        """E = (σ2 - σ1) / (ε2 - ε1) using first & last readings"""
        for rec in self:
            if rec.modulus_of_elasticity_line_ids and len(rec.modulus_of_elasticity_line_ids) >= 2:
                first = rec.modulus_of_elasticity_line_ids[0]
                last = rec.modulus_of_elasticity_line_ids[-1]

                delta_sigma = last.stress - first.stress
                delta_epsilon = last.strain - first.strain

                rec.modulus_e = (delta_sigma / delta_epsilon) if delta_epsilon != 0 else 0
            else:
                rec.modulus_e = 0


#    Point load Index
    ponit_load_name = fields.Char("Name",default="Point load Index")
    ponit_load_visible = fields.Boolean("Point load Index Visible",compute="_compute_visible")

    ponit_load_ids = fields.One2many('mechanical.point.load.line', 'parent_id', string="Samples")
    
    # aggregate results
    avg_is_uncorrected = fields.Float(string="Average Is (uncorrected)", compute="_compute_average", store=True)
    avg_is50 = fields.Float(string="Average Is(50)", compute="_compute_average", store=True)

    avg_is50_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_is50_conformity", store=True)

    @api.depends('avg_is50','eln_ref','grade')
    def _compute_avg_is50_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_is50_conformity = 'na'
                continue

            record.avg_is50_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6tr24ae1-b9a9-41cb-86a5-9654578gtr32e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6tr24ae1-b9a9-41cb-86a5-9654578gtr32e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_is50 - record.avg_is50*mu_value
                    upper = record.avg_is50 + record.avg_is50*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_is50_conformity = 'pass'
                        break
                    else:
                        record.avg_is50_conformity = 'fail'

    avg_is50_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_is50_nabl", store=True)

    @api.depends('avg_is50','eln_ref','grade')
    def _compute_avg_is50_nabl(self):
        
        for record in self:
            record.avg_is50_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6tr24ae1-b9a9-41cb-86a5-9654578gtr32e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6tr24ae1-b9a9-41cb-86a5-9654578gtr32e')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_is50 - record.avg_is50*mu_value
            upper = record.avg_is50 + record.avg_is50*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_is50_nabl = 'pass'
                break
            else:
                record.avg_is50_nabl = 'fail'

    @api.depends('ponit_load_ids.is_uncorrected', 'ponit_load_ids.is50')
    def _compute_average(self):
        for rec in self:
            if rec.ponit_load_ids:
                rec.avg_is_uncorrected = sum(rec.ponit_load_ids.mapped('is_uncorrected')) / len(rec.ponit_load_ids)
                rec.avg_is50 = sum(rec.ponit_load_ids.mapped('is50')) / len(rec.ponit_load_ids)
            else:
                rec.avg_is_uncorrected = 0.0
                rec.avg_is50 = 0.0

    #    Poison's Ratio
    poison_ratio_name = fields.Char("Name",default="Poison's Ratio")
    poison_ratio_visible = fields.Boolean("Poison's Ratio Visible",compute="_compute_visible")

    poison_ratio_line_ids = fields.One2many('mechanical.poisson.line', 'parent_id', string="Samples")

    avg_nu = fields.Float(string="Average Poison's Ratio", compute="_compute_avg", store=True)


    avg_nu_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_nu_conformity", store=True)

    @api.depends('avg_nu','eln_ref','grade')
    def _compute_avg_nu_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_nu_conformity = 'na'
                continue

            record.avg_nu_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3tr74ae1-b9a9-41cb-86a5-965457878tyrw')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3tr74ae1-b9a9-41cb-86a5-965457878tyrw')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_nu - record.avg_nu*mu_value
                    upper = record.avg_nu + record.avg_nu*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_nu_conformity = 'pass'
                        break
                    else:
                        record.avg_nu_conformity = 'fail'

    avg_nu_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_nu_nabl", store=True)

    @api.depends('avg_nu','eln_ref','grade')
    def _compute_avg_nu_nabl(self):
        
        for record in self:
            record.avg_nu_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3tr74ae1-b9a9-41cb-86a5-965457878tyrw')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3tr74ae1-b9a9-41cb-86a5-965457878tyrw')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_nu - record.avg_nu*mu_value
            upper = record.avg_nu + record.avg_nu*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_nu_nabl = 'pass'
                break
            else:
                record.avg_nu_nabl = 'fail'

    @api.depends('poison_ratio_line_ids.poisson_nu')
    def _compute_avg(self):
        for rec in self:
            if rec.poison_ratio_line_ids:
                rec.avg_nu = sum(rec.poison_ratio_line_ids.mapped('poisson_nu')) / len(rec.poison_ratio_line_ids)
            else:
                rec.avg_nu = 0.0

      #    Slake durability index
    slake_index_name = fields.Char("Name",default="Slake durability index")
    slake_index_visible = fields.Boolean("Slake durability index Visible",compute="_compute_visible")

    slake_index_line_ids = fields.One2many('mechanical.rock.slake.durability.line', 'parent_id', string="Cycles")

    avg_index = fields.Float(string="Average Slake Durability Index", compute="_compute_avg_index", store=True)

    avg_index_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_index_conformity", store=True)

    @api.depends('avg_index','eln_ref','grade')
    def _compute_avg_index_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_index_conformity = 'na'
                continue

            record.avg_index_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78er74ae1-b9a9-41cb-86a5-96578rtew214q')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78er74ae1-b9a9-41cb-86a5-96578rtew214q')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_index - record.avg_index*mu_value
                    upper = record.avg_index + record.avg_index*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_index_conformity = 'pass'
                        break
                    else:
                        record.avg_index_conformity = 'fail'

    avg_index_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_index_nabl", store=True)

    @api.depends('avg_index','eln_ref','grade')
    def _compute_avg_index_nabl(self):
        
        for record in self:
            record.avg_index_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78er74ae1-b9a9-41cb-86a5-96578rtew214q')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','78er74ae1-b9a9-41cb-86a5-96578rtew214q')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_index - record.avg_index*mu_value
            upper = record.avg_index + record.avg_index*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_index_nabl = 'pass'
                break
            else:
                record.avg_index_nabl = 'fail'

    @api.depends('slake_index_line_ids.sdi')
    def _compute_avg_index(self):
        for rec in self:
            sdi_values = rec.slake_index_line_ids.mapped('sdi')
            if sdi_values:
                rec.avg_index = sum(sdi_values) / len(sdi_values)
            else:
                rec.avg_index = 0.0


    #  Tensile Strength
    tensile_strength_name = fields.Char("Name",default="Tensile Strength")
    tensile_strength_visible = fields.Boolean("Tensile Strength Visible",compute="_compute_visible")

    tensile_strength_line_ids = fields.One2many('mechanical.rock.tensile.strength.line', 'parent_id', string="Tensile Strength Lines")

    avg_tensile_strength = fields.Float(string="Average Tensile Strength (MPa)", compute="_compute_avg_strength", store=True)

    avg_tensile_strength_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_avg_tensile_strength_conformity", store=True)

    @api.depends('avg_tensile_strength','eln_ref','grade')
    def _compute_avg_tensile_strength_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_tensile_strength_conformity = 'na'
                continue

            record.avg_tensile_strength_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','88er74ae1-b9a9-41cb-86a5-9657878rte214w')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','88er74ae1-b9a9-41cb-86a5-9657878rte214w')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_tensile_strength - record.avg_tensile_strength*mu_value
                    upper = record.avg_tensile_strength + record.avg_tensile_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_tensile_strength_conformity = 'pass'
                        break
                    else:
                        record.avg_tensile_strength_conformity = 'fail'

    avg_tensile_strength_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_avg_tensile_strength_nabl", store=True)

    @api.depends('avg_tensile_strength','eln_ref','grade')
    def _compute_avg_tensile_strength_nabl(self):
        
        for record in self:
            record.avg_tensile_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','88er74ae1-b9a9-41cb-86a5-9657878rte214w')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','88er74ae1-b9a9-41cb-86a5-9657878rte214w')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avg_tensile_strength - record.avg_tensile_strength*mu_value
            upper = record.avg_tensile_strength + record.avg_tensile_strength*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avg_tensile_strength_nabl = 'pass'
                break
            else:
                record.avg_tensile_strength_nabl = 'fail'

    @api.depends('tensile_strength_line_ids.tensile_strength')
    def _compute_avg_strength(self):
        for rec in self:
            values = rec.tensile_strength_line_ids.mapped('tensile_strength')
            rec.avg_tensile_strength = sum(values) / len(values) if values else 0.0

     # Unconsolidated Undrained Triaxial Test (Angle of Friction)
    uu_triaxial_angle_name = fields.Char("Name",default="Triaxial Compression Test- (Angle of Internal Friction)")
    uu_triaxial_angle_visible = fields.Boolean("Triaxial Compression Test- (Angle of Internal Friction) Visible",compute="_compute_visible")

    uu_triaxial_angle_line_ids = fields.One2many("mechanical.rock.uu.triaxial.line", "parent_id", string="Test Observations")

    phi_deg_uu_triaxial_angle = fields.Float(string="Angle of Friction φ (°)", compute="_compute_phi_c", store=True)
    cohesion_uu_triaxial_angle = fields.Float(string="Cohesion c (kPa)", compute="_compute_phi_c", store=True)

    phi_deg_uu_triaxial_angle_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_phi_deg_uu_triaxial_angle_conformity", store=True)

    @api.depends('phi_deg_uu_triaxial_angle','eln_ref','grade')
    def _compute_phi_deg_uu_triaxial_angle_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.phi_deg_uu_triaxial_angle_conformity = 'na'
                continue

            record.phi_deg_uu_triaxial_angle_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9rtr74ae1-b9a9-41cb-86a5-96578723147gtre')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9rtr74ae1-b9a9-41cb-86a5-96578723147gtre')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.phi_deg_uu_triaxial_angle - record.phi_deg_uu_triaxial_angle*mu_value
                    upper = record.phi_deg_uu_triaxial_angle + record.phi_deg_uu_triaxial_angle*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.phi_deg_uu_triaxial_angle_conformity = 'pass'
                        break
                    else:
                        record.phi_deg_uu_triaxial_angle_conformity = 'fail'

    phi_deg_uu_triaxial_angle_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_phi_deg_uu_triaxial_angle_nabl", store=True)

    @api.depends('phi_deg_uu_triaxial_angle','eln_ref','grade')
    def _compute_phi_deg_uu_triaxial_angle_nabl(self):
        
        for record in self:
            record.phi_deg_uu_triaxial_angle_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9rtr74ae1-b9a9-41cb-86a5-96578723147gtre')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9rtr74ae1-b9a9-41cb-86a5-96578723147gtre')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.phi_deg_uu_triaxial_angle - record.phi_deg_uu_triaxial_angle*mu_value
            upper = record.phi_deg_uu_triaxial_angle + record.phi_deg_uu_triaxial_angle*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.phi_deg_uu_triaxial_angle_nabl = 'pass'
                break
            else:
                record.phi_deg_uu_triaxial_angle_nabl = 'fail'

    @api.depends("uu_triaxial_angle_line_ids.sigma", "uu_triaxial_angle_line_ids.tau")
    def _compute_phi_c(self):
        for rec in self:
            lines = rec.uu_triaxial_angle_line_ids

            # किमान 2 data points असले पाहिजेत
            if not lines or len(lines) < 2:
                rec.phi_deg_uu_triaxial_angle = 0.0
                rec.cohesion_uu_triaxial_angle = 0.0
                continue

            slopes = []
            intercepts = []

            # सर्व सलग points वरून slope व intercept काढा
            for i in range(len(lines) - 1):
                p1 = lines[i]
                p2 = lines[i + 1]

                if (p2.sigma - p1.sigma) == 0:
                    continue

                m = (p2.tau - p1.tau) / (p2.sigma - p1.sigma)
                c = p1.tau - m * p1.sigma
                slopes.append(m)
                intercepts.append(c)

            if not slopes:
                rec.phi_deg_uu_triaxial_angle = 0.0
                rec.cohesion_uu_triaxial_angle = 0.0
                continue

            avg_m = sum(slopes) / len(slopes)
            avg_c = sum(intercepts) / len(intercepts)

            phi_rad = math.atan(avg_m)
            phi_deg = phi_rad * 180.0 / math.pi

            rec.phi_deg_uu_triaxial_angle = round(phi_deg, 3)
            rec.cohesion_uu_triaxial_angle = round(avg_c, 3)

    #    Triaxial Compression Test – Cohesion
    uu_triaxial_cohesion_name = fields.Char("Name",default="Triaxial Compression Test – Cohesion")
    uu_triaxial_cohesion_visible = fields.Boolean("Triaxial Compression Test – Cohesion Visible",compute="_compute_visible")

    uu_triaxial_cohesion_line_ids = fields.One2many("mechanical.rock.uu.triaxial.cohesion.line", "parent_id", string="Test Observations")

    phi_deg_uu_triaxial_cohesion = fields.Float(string="Angle of Friction φ (°)", compute="_compute_phi_cohesion", store=True)
    cohesion_uu_triaxial_cohesion = fields.Float(string="Cohesion c (kPa)", compute="_compute_phi_cohesion", store=True)

    cohesion_uu_triaxial_cohesion_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('na', 'NA'),
            ], string="Conformity", compute="_compute_cohesion_uu_triaxial_cohesion_conformity", store=True)

    @api.depends('cohesion_uu_triaxial_cohesion','eln_ref','grade')
    def _compute_cohesion_uu_triaxial_cohesion_conformity(self):
        
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.cohesion_uu_triaxial_cohesion_conformity = 'na'
                continue

            record.cohesion_uu_triaxial_cohesion_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0rte74ae1-b9a9-41cb-86a5-96578721254789rt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0rte74ae1-b9a9-41cb-86a5-96578721254789rt')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.cohesion_uu_triaxial_cohesion - record.cohesion_uu_triaxial_cohesion*mu_value
                    upper = record.cohesion_uu_triaxial_cohesion + record.cohesion_uu_triaxial_cohesion*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.cohesion_uu_triaxial_cohesion_conformity = 'pass'
                        break
                    else:
                        record.cohesion_uu_triaxial_cohesion_conformity = 'fail'

    cohesion_uu_triaxial_cohesion_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')], string="NABL", compute="_compute_cohesion_uu_triaxial_cohesion_nabl", store=True)

    @api.depends('cohesion_uu_triaxial_cohesion','eln_ref','grade')
    def _compute_cohesion_uu_triaxial_cohesion_nabl(self):
        
        for record in self:
            record.cohesion_uu_triaxial_cohesion_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0rte74ae1-b9a9-41cb-86a5-96578721254789rt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0rte74ae1-b9a9-41cb-86a5-96578721254789rt')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.cohesion_uu_triaxial_cohesion - record.cohesion_uu_triaxial_cohesion*mu_value
            upper = record.cohesion_uu_triaxial_cohesion + record.cohesion_uu_triaxial_cohesion*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.cohesion_uu_triaxial_cohesion_nabl = 'pass'
                break
            else:
                record.cohesion_uu_triaxial_cohesion_nabl = 'fail'

    @api.depends("uu_triaxial_cohesion_line_ids.sigma", "uu_triaxial_cohesion_line_ids.tau")
    def _compute_phi_cohesion(self):
        for rec in self:
            lines = rec.uu_triaxial_cohesion_line_ids

            # किमान 2 data points असले पाहिजेत
            if not lines or len(lines) < 2:
                rec.phi_deg_uu_triaxial_cohesion = 0.0
                rec.cohesion_uu_triaxial_cohesion = 0.0
                continue

            slopes = []
            intercepts = []

            # सर्व सलग points वरून slope व intercept काढा
            for i in range(len(lines) - 1):
                p1 = lines[i]
                p2 = lines[i + 1]

                if (p2.sigma - p1.sigma) == 0:
                    continue

                m = (p2.tau - p1.tau) / (p2.sigma - p1.sigma)
                c = p1.tau - m * p1.sigma
                slopes.append(m)
                intercepts.append(c)

            if not slopes:
                rec.phi_deg_uu_triaxial_cohesion = 0.0
                rec.cohesion_uu_triaxial_cohesion = 0.0
                continue

            avg_m = sum(slopes) / len(slopes)
            avg_c = sum(intercepts) / len(intercepts)

            phi_rad = math.atan(avg_m)
            phi_deg = phi_rad * 180.0 / math.pi

            rec.phi_deg_uu_triaxial_cohesion = round(phi_deg, 3)
            rec.cohesion_uu_triaxial_cohesion = round(avg_c, 3)

   
    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.usc_visible = False
            record.porosity_visible = False
            record.specific_gravity_visible = False
            record.dry_density_visible = False
            record.water_absorption_visible = False
            record.cerchar_abrsivity_visible = False
            record.modulus_of_elasticity_visible = False
            record.ponit_load_visible = False
            record.poison_ratio_visible = False
            record.slake_index_visible = False
            record.tensile_strength_visible = False
            record.uu_triaxial_angle_visible = False
            record.uu_triaxial_cohesion_visible = False

          
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                if sample.internal_id == "a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d":
                    record.usc_visible = True
                if sample.internal_id == "a4eb1d5e-9d64-48cd-8277-ad734e0edd84":
                    record.porosity_visible = True
                if sample.internal_id == "bf5d3d97-9a52-4242-9a36-2e40e5fc8247":
                    record.specific_gravity_visible = True
                if sample.internal_id == "87ec776a-11eb-45ef-addf-e183edabd6dd":
                    record.dry_density_visible = True
                if sample.internal_id == "71e24ae1-b9a9-41cb-86a5-89d87312f3d6":
                    record.water_absorption_visible = True
                if sample.internal_id == "71e24ae1-b9a9-41cb-86a5-89d87355786tt":
                    record.cerchar_abrsivity_visible = True

                if sample.internal_id == "71e24ae1-b9a9-41cb-86a5-9654tyu145er2":
                    record.modulus_of_elasticity_visible = True

                if sample.internal_id == "6tr24ae1-b9a9-41cb-86a5-9654578gtr32e":
                    record.ponit_load_visible = True

                if sample.internal_id == "3tr74ae1-b9a9-41cb-86a5-965457878tyrw":
                    record.poison_ratio_visible = True

                if sample.internal_id == "78er74ae1-b9a9-41cb-86a5-96578rtew214q":
                    record.slake_index_visible = True

                if sample.internal_id == "88er74ae1-b9a9-41cb-86a5-9657878rte214w":
                    record.tensile_strength_visible = True

                if sample.internal_id == "9rtr74ae1-b9a9-41cb-86a5-96578723147gtre":
                    record.uu_triaxial_angle_visible = True

                if sample.internal_id == "0rte74ae1-b9a9-41cb-86a5-96578721254789rt":
                    record.uu_triaxial_cohesion_visible = True
                
              
               

                
    
   
            
           

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()
            
            
            
            if result.parameter.internal_id == 'a1f9c5d0-0bc7-41a6-a2bb-0fe9d898008d':
                result.result_char = round(self.avg_usc,2)
                result.calculated = True
                if self.avg_usc_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'a4eb1d5e-9d64-48cd-8277-ad734e0edd84':
                result.result_char = round(self.avg_porosity,2)
                result.calculated = True
                # if self.aggregate_combine_conformity == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue

            if result.parameter.internal_id == 'bf5d3d97-9a52-4242-9a36-2e40e5fc8247':
                # result.result_char = round(self.aggregate_elongation,2)
                result.calculated = True
                # if self.aggregate_combine_conformity == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue


            if result.parameter.internal_id == '87ec776a-11eb-45ef-addf-e183edabd6dd':
                result.result_char = round(self.avg_dry_density,2)
                result.calculated = True
                # if self.aggregate_combine_conformity == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue


            if result.parameter.internal_id == '71e24ae1-b9a9-41cb-86a5-89d87312f3d6':
                result.result_char = round(self.avg_water_absorption,2)
                result.calculated = True
                # if self.aggregate_combine_conformity == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue


            if result.parameter.internal_id == '71e24ae1-b9a9-41cb-86a5-89d87355786tt':
                result.result_char = round(self.cai,2)
                result.calculated = True
                if self.cai_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '71e24ae1-b9a9-41cb-86a5-9654tyu145er2':
                result.result_char = round(self.modulus_e,2)
                result.calculated = True
                if self.modulus_e_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '6tr24ae1-b9a9-41cb-86a5-9654578gtr32e':
                result.result_char = round(self.avg_is50,2)
                result.calculated = True
                if self.avg_is50_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '3tr74ae1-b9a9-41cb-86a5-965457878tyrw':
                result.result_char = round(self.avg_nu,2)
                result.calculated = True
                if self.avg_nu_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '78er74ae1-b9a9-41cb-86a5-96578rtew214q':
                result.result_char = round(self.avg_index,2)
                result.calculated = True
                if self.avg_index_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '88er74ae1-b9a9-41cb-86a5-9657878rte214w':
                result.result_char = round(self.avg_tensile_strength,2)
                result.calculated = True
                if self.avg_tensile_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '9rtr74ae1-b9a9-41cb-86a5-96578723147gtre':
                result.result_char = round(self.phi_deg_uu_triaxial_angle,2)
                result.calculated = True
                if self.phi_deg_uu_triaxial_angle_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            if result.parameter.internal_id == '0rte74ae1-b9a9-41cb-86a5-96578721254789rt':
                result.result_char = round(self.cohesion_uu_triaxial_cohesion,2)
                result.calculated = True
                if self.cohesion_uu_triaxial_cohesion_nabl == 'pass':
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
        record = super(MechanicalRock, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     # records = self.env['lerm.eln'].sudo().search([('id','=', record.eln_id.id)]).parameters_result
    #     # print("records",records)
    #     # self.sample_parameters = records
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

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
        record = self.env['mechanical.rock'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



class MechanicalRockLine(models.Model):
    _name = "mechanical.rock.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")
   
    sr_no = fields.Integer(string="Specimen NO.", readonly=True, copy=False, default=1)
    location = fields.Char(string="Location")
    sample_no = fields.Char(string="Sample Number")
    depth = fields.Char(string="Depth in (mtr)", size=100) 
    ssd_weight = fields.Float(string="SSD weight of sample in kg, Msat",digits=(16, 3))
    wt_sample_water = fields.Float(string="Weight of sample in water in kg, Msub",digits=(16, 3))
    oven_dry_wt = fields.Float(string="Oven dry weight of sample in kg, Ms",digits=(16, 3))
    porosity = fields.Float(string="Porosity",compute="_compute_porosity")
    water_absorption = fields.Float(string="Water Absorption",compute="_compute_water_absorption")
    dry_density = fields.Float(string="Dry Density",compute="_compute_dry_density",digits=(16, 2))
    saturated_spc_gravity = fields.Float(string="Saturated Specific Gravity",compute="_compute_saturated_spc_gravity",digits=(16, 2))

    @api.depends('ssd_weight', 'wt_sample_water', 'oven_dry_wt')
    def _compute_porosity(self):
        for record in self:
            # if record.ssd_weight and record.wt_sample_water and (record.ssd_weight - record.wt_sample_water) != 0:
            if record.ssd_weight and record.wt_sample_water != record.ssd_weight:
                record.porosity = (record.ssd_weight - record.oven_dry_wt) / (record.ssd_weight - record.wt_sample_water) * 100
            else:
                record.porosity = 0.0
        print("<<<<<<<<<<<<<")
    
    @api.depends('ssd_weight', 'oven_dry_wt')
    def _compute_water_absorption(self):
        for record in self:
            if record.oven_dry_wt and record.ssd_weight:
                record.water_absorption = ((record.ssd_weight - record.oven_dry_wt) / record.oven_dry_wt) * 100
            else:
                record.water_absorption = 0.0

    # @api.depends('wt_sample_water', 'wt_sample_water', 'oven_dry_wt')
    # def _compute_dry_density(self):
    #     for record in self:
    #         if record.ssd_weight and record.wt_sample_water and record.oven_dry_wt:
    #             record.dry_density = record.oven_dry_wt / record.ssd_weight - record.wt_sample_water
    #         else:
    #             record.dry_density = 0.0
                
    @api.depends('ssd_weight', 'wt_sample_water', 'oven_dry_wt')
    def _compute_saturated_spc_gravity(self):
        for record in self:
            if record.ssd_weight and record.wt_sample_water and record.oven_dry_wt:
                record.saturated_spc_gravity = record.oven_dry_wt / (record.ssd_weight - record.wt_sample_water)
            else:
                record.saturated_spc_gravity = 0.0

    # @api.depends('oven_dry_wt','dry_density')
    # def _compute_saturated_spc_gravity(self):
    #     for record in self:
    #         if record.dry_density != 0:
    #             record.saturated_spc_gravity = record.oven_dry_wt/record.dry_density
    #         else:
    #             record.saturated_spc_gravity = 0.0
                
    @api.depends('ssd_weight', 'wt_sample_water', 'oven_dry_wt')
    def _compute_dry_density(self):
        for record in self:
            if record.ssd_weight and record.wt_sample_water and record.oven_dry_wt:
                record.dry_density = record.oven_dry_wt / (record.ssd_weight - record.wt_sample_water)
            else:
                record.dry_density = 0.0

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalRockLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class MechanicalUSCLine(models.Model):
    _name = "mechanical.usc.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")
   
    
    location = fields.Char(string="Location")
    sr_no = fields.Integer(string="Sample NO.", readonly=True, copy=False, default=1)
    depth = fields.Char(string="Depth in (mtr)")
    diameter = fields.Float(string="Dia. in mm")
    length = fields.Float(string="Length in mm")
    ld_ratio = fields.Float(string="L/D ratio",compute="_compute_ld_ratio")
    area = fields.Float(string="Area in mm2",compute="_compute_area",digits=(16,2))
    load = fields.Float(string="Load in KN",digits=(16,2))
    usc = fields.Float(string="UCS in N/mm2",compute="_compute_usc")


    @api.depends('length', 'diameter')
    def _compute_ld_ratio(self):
        for record in self:
            if record.diameter != 0:
                record.ld_ratio = record.length / record.diameter
            else:
                record.ld_ratio = 0


    # @api.depends('length')
    # def _compute_area(self):
    #     for record in self:
    #         record.area = (3.143 )* (record.length * record.length) / 4
                
    @api.depends('diameter')
    def _compute_area(self):
        for record in self:
            record.area = (3.14 * record.diameter * record.diameter) / 4  # Round the result to 2 decimal places
    
    @api.depends('load', 'area')
    def _compute_usc(self):
        for record in self:
            if record.area != 0:
                record.usc = round((record.load / record.area) * 1000, 2)  # Round the result to 2 decimal places
            else:
                record.usc = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(MechanicalUSCLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class RockWearDiameterLine(models.Model):
    _name = "mechanical.rock.cerchar.abrsivity.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")

    sr_no = fields.Integer(string="Sample NO.", readonly=True, copy=False, default=1)

    value = fields.Float('Wear Flat Diameter (mm)')
   
    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(RockWearDiameterLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class RockElasticityLine(models.Model):
    _name = "mechanical.rock.elasticity.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")

    sr_no = fields.Integer(string="Sample NO.", readonly=True, copy=False, default=1)

    diameter = fields.Float(string="Diameter (mm)")
    length = fields.Float(string="Length (mm)")
    load = fields.Float(string="Load (N)")
    delta_l = fields.Float(string="ΔL (mm)")

    area = fields.Float(string="Area (mm²)", compute="_compute_values", store=True)
    stress = fields.Float(string="Stress σ (MPa)", compute="_compute_values", store=True)
    strain = fields.Float(string="Strain ε", compute="_compute_values", store=True)

    @api.depends("diameter", "length", "load", "delta_l")
    def _compute_values(self):
        for rec in self:
            # Cross-sectional area
            rec.area = math.pi * (rec.diameter ** 2) / 4 if rec.diameter else 0
            # Stress = Load / Area
            rec.stress = (rec.load / rec.area) if rec.area else 0
            # Strain = ΔL / Length
            rec.strain = (rec.delta_l / rec.length) if rec.length else 0
   
    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(RockElasticityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class RockPointLoadLine(models.Model):
    _name = "mechanical.point.load.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")

    sr_no = fields.Integer(string="Sample NO.", readonly=True, copy=False, default=1)


    diameter_mm = fields.Float(string="Platen separation / Diameter D (mm)", digits=(12,4), required=True)
    failure_load_n = fields.Float(string="Failure Load P (N)", digits=(12,3), required=True)

    equivalent_de = fields.Float(string="Equivalent diameter De (mm)", compute="_compute_equivalent", store=True)
    area_mm2 = fields.Float(string="Area  (mm²)", compute="_compute_area", store=True)
    is_uncorrected = fields.Float(string="uncorrected N/mm²", compute="_compute_is", store=True)
    size_correction_f = fields.Float(string="Size correction F", compute="_compute_size_correction", store=True)
    is50 = fields.Float(string="Is(50) corrected N/mm²", compute="_compute_is50", store=True)

    @api.depends('diameter_mm')
    def _compute_equivalent(self):
        for r in self:
            r.equivalent_de = r.diameter_mm or 0.0

    @api.depends('equivalent_de')
    def _compute_area(self):
        for r in self:
            r.area_mm2 = (pi * (r.equivalent_de ** 2) / 4.0) if r.equivalent_de else 0.0

    @api.depends('failure_load_n', 'equivalent_de')
    def _compute_is(self):
        for r in self:
            if r.equivalent_de > 0:
                r.is_uncorrected = r.failure_load_n / (r.equivalent_de ** 2)
            else:
                r.is_uncorrected = 0.0

    @api.depends('equivalent_de')
    def _compute_size_correction(self):
        for r in self:
            if r.equivalent_de > 0:
                r.size_correction_f = (r.equivalent_de / 50.0) ** 0.45
            else:
                r.size_correction_f = 0.0

    @api.depends('is_uncorrected', 'size_correction_f')
    def _compute_is50(self):
        for r in self:
            r.is50 = r.is_uncorrected * r.size_correction_f


   
    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(RockPointLoadLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class PoissonsTestLine(models.Model):
    _name = "mechanical.poisson.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")

    sr_no = fields.Integer(string="Sample NO.", readonly=True, copy=False, default=1)

    L0_mm = fields.Float(string="Original length L0 (mm)", digits=(12,2))
    delta_L_mm = fields.Float(string="Axial extension ΔL (mm)", digits=(12,2))
    d0_mm = fields.Float(string="Original diameter d0 (mm)", digits=(12,2))
    delta_d_mm = fields.Float(string="Lateral change Δd (mm)", digits=(12,2))

    axial_strain = fields.Float(string="Axial strain ε_axial", compute="_compute_strains", store=True)
    lateral_strain = fields.Float(string="Lateral strain ε_lat", compute="_compute_strains", store=True)
    poisson_nu = fields.Float(string="Poisson's ratio ν", compute="_compute_poisson", store=True)

    @api.depends('L0_mm', 'delta_L_mm', 'd0_mm', 'delta_d_mm')
    def _compute_strains(self):
        for r in self:
            r.axial_strain = (r.delta_L_mm / r.L0_mm) if r.L0_mm else 0.0
            r.lateral_strain = (r.delta_d_mm / r.d0_mm) if r.d0_mm else 0.0

    @api.depends('axial_strain', 'lateral_strain')
    def _compute_poisson(self):
        for r in self:
            if r.axial_strain and abs(r.axial_strain) > 1e-12:
                r.poisson_nu = abs(r.lateral_strain / r.axial_strain)  # ✅ always positive
            else:
                r.poisson_nu = 0.0




    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(PoissonsTestLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class SlakeDurabilityLine(models.Model):
    _name = "mechanical.rock.slake.durability.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")

    sr_no = fields.Integer(string="Sample NO.", readonly=True, copy=False, default=1)

    w1 = fields.Float(string="Initial Dry Weight W₁ (g)", digits=(12,3))
    w2 = fields.Float(string="Final Dry Weight W₂ (g)", digits=(12,3))
    sdi = fields.Float(string="Slake Durability Index Id (%)", compute="_compute_sdi", store=True, readonly=False)

    @api.depends('w1', 'w2')
    def _compute_sdi(self):
        for rec in self:
            rec.sdi = (rec.w2 / rec.w1 * 100) if rec.w1 else 0.0

    @api.onchange('w1', 'w2')
    def _onchange_calculate_sdi(self):
        for rec in self:
            rec.sdi = (rec.w2 / rec.w1 * 100) if rec.w1 else 0.0

    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(SlakeDurabilityLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1


class TensileStrengthLine(models.Model):
    _name = "mechanical.rock.tensile.strength.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")

    sr_no = fields.Integer(string="Sample NO.", readonly=True, copy=False, default=1)

    load_kn = fields.Float(string="Failure Load P (kN)", digits=(12,3))
    diameter_mm = fields.Float(string="Diameter D (mm)", digits=(12,3))
    length_mm = fields.Float(string="Length L (mm)", digits=(12,3))
    tensile_strength = fields.Float(string="Tensile Strength σt (MPa)", compute="_compute_tensile_strength", store=True, readonly=False)

    @api.depends('load_kn', 'diameter_mm', 'length_mm')
    def _compute_tensile_strength(self):
        for rec in self:
            if rec.diameter_mm and rec.length_mm:
                rec.tensile_strength = (2 * rec.load_kn * 1000) / (math.pi * rec.diameter_mm * rec.length_mm)
            else:
                rec.tensile_strength = 0.0

    @api.onchange('load_kn', 'diameter_mm', 'length_mm')
    def _onchange_tensile_strength(self):
        for rec in self:
            if rec.diameter_mm and rec.length_mm:
                rec.tensile_strength = (2 * rec.load_kn * 1000) / (math.pi * rec.diameter_mm * rec.length_mm)
            else:
                rec.tensile_strength = 0.0



    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(TensileStrengthLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class UUTriaxialLine(models.Model):
    _name = "mechanical.rock.uu.triaxial.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    confining_pressure = fields.Float(string="Minor Principal Stress σ3 (kPa)")   # cell pressure
    deviator_stress = fields.Float(string="Deviator Stress qf (kPa)")

    sigma1 = fields.Float(string="Major Principal Stress σ1 (kPa)", compute="_compute_sigma_tau", store=True)
    sigma = fields.Float(string="σ (Mohr center)", compute="_compute_sigma_tau", store=True)
    tau = fields.Float(string="τ (Mohr radius)", compute="_compute_sigma_tau", store=True)

    @api.depends("confining_pressure", "deviator_stress")
    def _compute_sigma_tau(self):
        for rec in self:
            if rec.confining_pressure and rec.deviator_stress:
                rec.sigma1 = rec.confining_pressure + rec.deviator_stress
                rec.sigma = (rec.sigma1 + rec.confining_pressure) / 2.0
                rec.tau = (rec.sigma1 - rec.confining_pressure) / 2.0
            else:
                rec.sigma1 = rec.sigma = rec.tau = 0.0


   

    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(UUTriaxialLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class UUTriaxialCohesionLine(models.Model):
    _name = "mechanical.rock.uu.triaxial.cohesion.line"
    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")

    serial_no = fields.Integer(string="SR NO",readonly=True, copy=False, default=1)

    confining_pressure = fields.Float(string="Minor Principal Stress σ3 (kPa)")   # cell pressure
    deviator_stress = fields.Float(string="Deviator Stress qf (kPa)")

    sigma1 = fields.Float(string="Major Principal Stress σ1 (kPa)", compute="_compute_sigma_chausion", store=True)
    sigma = fields.Float(string="σ (Mohr center)", compute="_compute_sigma_chausion", store=True)
    tau = fields.Float(string="τ (Mohr radius)", compute="_compute_sigma_chausion", store=True)

    @api.depends("confining_pressure", "deviator_stress")
    def _compute_sigma_chausion(self):
        for rec in self:
            if rec.confining_pressure and rec.deviator_stress:
                rec.sigma1 = rec.confining_pressure + rec.deviator_stress
                rec.sigma = (rec.sigma1 + rec.confining_pressure) / 2.0
                rec.tau = (rec.sigma1 - rec.confining_pressure) / 2.0
            else:
                rec.sigma1 = rec.sigma = rec.tau = 0.0


   

    
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(UUTriaxialCohesionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class rockNotes(models.Model):
    _name = "rock.notes"

    parent_id = fields.Many2one('mechanical.rock',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")



