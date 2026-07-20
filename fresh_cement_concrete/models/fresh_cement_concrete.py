from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class FreshCementConcrete(models.Model):
    _name = "mechanical.fresh.cement.concrete"
    _inherit = "lerm.eln"
    _description = 'mechanical.fresh.cement.concrete'
    _rec_name = "name"


    name = fields.Char("Name",default="Fresh Cement Concrete")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    aac_temp = fields.Char("Temperature",store=True)
    aac_humidity = fields.Char("Humidity",store=True)

    @api.depends("eln_ref")
    def _compute_size_id(self):
        for record in self:
            print("Size iD",record.eln_ref.size_id)
            record.size_id = record.eln_ref.size_id.id

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'aac.block.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }

    # Slump Test
    slump_test_name = fields.Char(default="Slump Test")
    slump_test_visible = fields.Boolean(string="Slump Test Visible" ,compute="_compute_visible")

    slump_test_line_ids = fields.One2many('fcc.slump.test.line','parent_id',string='Slump Test Lines')

    
    avg_slump_value = fields.Float(
        string="Average Slump Value (mm)",
        compute="_compute_avg_slump_value",
        store=True
    )

    required_slump = fields.Float(string="Required Slump (mm)")

    @api.depends('slump_test_line_ids.slump_value')
    def _compute_avg_slump_value(self):
        for rec in self:
            if rec.slump_test_line_ids:
                rec.avg_slump_value = sum(
                    rec.slump_test_line_ids.mapped('slump_value')
                ) / len(rec.slump_test_line_ids)
            else:
                rec.avg_slump_value = 0

    avg_slump_value_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_slump_value_confirmity")
    
    @api.depends('avg_slump_value','eln_ref','grade')
    def _compute_avg_slump_value_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_slump_value_confirmity = 'na'
                continue
            record.avg_slump_value_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','49f934a0-ebd7-478b-a11e-641d7babc9c0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','49f934a0-ebd7-478b-a11e-641d7babc9c0')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_slump_value - record.avg_slump_value*mu_value
                    upper = record.avg_slump_value + record.avg_slump_value*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_slump_value_confirmity = 'pass'
                        break
                    else:
                        record.avg_slump_value_confirmity = 'fail'

    avg_slump_value_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_slump_value_nabl")
    
    @api.depends('avg_slump_value','eln_ref','grade')
    def _compute_avg_slump_value_nabl(self):
        
        for record in self:
            record.avg_slump_value_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','49f934a0-ebd7-478b-a11e-641d7babc9c0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','49f934a0-ebd7-478b-a11e-641d7babc9c0')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_slump_value - record.avg_slump_value*mu_value
                    upper = record.avg_slump_value + record.avg_slump_value*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_slump_value_nabl = 'pass'
                        break
                    else:
                        record.avg_slump_value_nabl = 'fail'


    # Density
    density_name = fields.Char(default="Density Test")
    density_visible = fields.Boolean(string="Density Test Visible" ,compute="_compute_visible")

    density_line_ids = fields.One2many('fcc.density.test.line','parent_id',string='Density Test Lines')

    
    avg_density = fields.Float(
        string="Average Density (kg/m³)",
        compute="_compute_avg_density",
        store=True
    )

    @api.depends('density_line_ids.density')
    def _compute_avg_density(self):
        for rec in self:
            if rec.density_line_ids:
                rec.avg_density = sum(
                    rec.density_line_ids.mapped('density')
                ) / len(rec.density_line_ids)
            else:
                rec.avg_density = 0

    avg_density_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_density_confirmity")
    
    @api.depends('avg_density','eln_ref','grade')
    def _compute_avg_density_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_density_confirmity = 'na'
                continue
            record.avg_density_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','021ea043-8164-487b-8857-6aa4240a38df')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','021ea043-8164-487b-8857-6aa4240a38df')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_density - record.avg_density*mu_value
                    upper = record.avg_density + record.avg_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_density_confirmity = 'pass'
                        break
                    else:
                        record.avg_density_confirmity = 'fail'

    avg_density_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_density_nabl")
    
    @api.depends('avg_density','eln_ref','grade')
    def _compute_avg_density_nabl(self):
        
        for record in self:
            record.avg_density_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','021ea043-8164-487b-8857-6aa4240a38df')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','021ea043-8164-487b-8857-6aa4240a38df')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
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


    # Flow of Concrete of High Workability Test
    flow_high_work_name = fields.Char(default="Flow of Concrete of High Workability Test")
    flow_high_work_visible = fields.Boolean(string="Flow of Concrete of High Workability Test Visible" ,compute="_compute_visible")

    flow_high_work_line_ids = fields.One2many('fcc.flow.high.test.line','parent_id',string='Flow of Concrete of High Workability Test Lines')

    
    avg_flow_high = fields.Float(
        string="Average Flow of Concrete of High Workability (%)",
        compute="_compute_avg_flow_high",
        store=True
    )

    @api.depends('flow_high_work_line_ids.flow')
    def _compute_avg_flow_high(self):
        for rec in self:
            if rec.flow_high_work_line_ids:
                rec.avg_flow_high = sum(
                    rec.flow_high_work_line_ids.mapped('flow')
                ) / len(rec.flow_high_work_line_ids)
            else:
                rec.avg_flow_high = 0

    avg_flow_high_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_flow_high_confirmity")
    
    @api.depends('avg_flow_high','eln_ref','grade')
    def _compute_avg_flow_high_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_flow_high_confirmity = 'na'
                continue
            record.avg_flow_high_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','664503ee-02ac-48cf-88b0-a5e3bc33f290')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','664503ee-02ac-48cf-88b0-a5e3bc33f290')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_flow_high - record.avg_flow_high*mu_value
                    upper = record.avg_flow_high + record.avg_flow_high*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_flow_high_confirmity = 'pass'
                        break
                    else:
                        record.avg_flow_high_confirmity = 'fail'

    avg_flow_high_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_flow_high_nabl")
    
    @api.depends('avg_flow_high','eln_ref','grade')
    def _compute_avg_flow_high_nabl(self):
        
        for record in self:
            record.avg_flow_high_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','664503ee-02ac-48cf-88b0-a5e3bc33f290')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','664503ee-02ac-48cf-88b0-a5e3bc33f290')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_flow_high - record.avg_flow_high*mu_value
                    upper = record.avg_flow_high + record.avg_flow_high*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_flow_high_nabl = 'pass'
                        break
                    else:
                        record.avg_flow_high_nabl = 'fail'


    # Wet Density Test
    wet_density_name = fields.Char(default="Wet Density Test")
    wet_density_visible = fields.Boolean(string="Wet Density Test Visible" ,compute="_compute_visible")

    wet_density_line_ids = fields.One2many('fcc.wet.density.test.line','parent_id',string='Wet Density Test Lines')

    
    avg_wet_density = fields.Float(
        string="Average Wet Density (kg/m³)",
        compute="_compute_avg_wet_density",
        store=True
    )

    @api.depends('wet_density_line_ids.wet_density')
    def _compute_avg_wet_density(self):
        for rec in self:
            if rec.wet_density_line_ids:
                rec.avg_wet_density = sum(
                    rec.wet_density_line_ids.mapped('wet_density')
                ) / len(rec.wet_density_line_ids)
            else:
                rec.avg_wet_density = 0

    avg_wet_density_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_wet_density_confirmity")
    
    @api.depends('avg_wet_density','eln_ref','grade')
    def _compute_avg_wet_density_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_wet_density_confirmity = 'na'
                continue
            record.avg_wet_density_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d0855037-7ccd-4238-bc7b-674a40d40580')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d0855037-7ccd-4238-bc7b-674a40d40580')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_wet_density - record.avg_wet_density*mu_value
                    upper = record.avg_wet_density + record.avg_wet_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_wet_density_confirmity = 'pass'
                        break
                    else:
                        record.avg_wet_density_confirmity = 'fail'

    avg_wet_density_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_wet_density_nabl")
    
    @api.depends('avg_wet_density','eln_ref','grade')
    def _compute_avg_wet_density_nabl(self):
        
        for record in self:
            record.avg_wet_density_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d0855037-7ccd-4238-bc7b-674a40d40580')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','d0855037-7ccd-4238-bc7b-674a40d40580')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_wet_density - record.avg_wet_density*mu_value
                    upper = record.avg_wet_density + record.avg_wet_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_wet_density_nabl = 'pass'
                        break
                    else:
                        record.avg_wet_density_nabl = 'fail'


    # Flow Test of Fresh Cement Concrete 
    flow_test_name = fields.Char(default="Flow Test of Fresh Cement Concrete")
    flow_test_visible = fields.Boolean(string="Flow Test of Fresh Cement Concrete Visible" ,compute="_compute_visible")

    flow_test_line_ids = fields.One2many('fcc.flow.table.test.line','parent_id',string='Flow Test of Fresh Cement Concrete Lines')

    
    avg_flow_test = fields.Float(
        string="Average Flow (%)  (((B − A)/A) × 100)",
        compute="_compute_avg_flow_test",
        store=True
    )

    @api.depends('flow_test_line_ids.flow')
    def _compute_avg_flow_test(self):
        for rec in self:
            if rec.flow_test_line_ids:
                rec.avg_flow_test = sum(
                    rec.flow_test_line_ids.mapped('flow')
                ) / len(rec.flow_test_line_ids)
            else:
                rec.avg_flow_test = 0

    avg_flow_test_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_avg_flow_test_confirmity")
    
    @api.depends('avg_flow_test','eln_ref','grade')
    def _compute_avg_flow_test_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_flow_test_confirmity = 'na'
                continue
            record.avg_flow_test_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c3cad715-b384-4ac6-955d-e4d3248a8bfb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c3cad715-b384-4ac6-955d-e4d3248a8bfb')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.avg_flow_test - record.avg_flow_test*mu_value
                    upper = record.avg_flow_test + record.avg_flow_test*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avg_flow_test_confirmity = 'pass'
                        break
                    else:
                        record.avg_flow_test_confirmity = 'fail'

    avg_flow_test_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='NABL', default='fail',compute="_compute_avg_flow_test_nabl")
    
    @api.depends('avg_flow_test','eln_ref','grade')
    def _compute_avg_flow_test_nabl(self):
        
        for record in self:
            record.avg_flow_test_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c3cad715-b384-4ac6-955d-e4d3248a8bfb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c3cad715-b384-4ac6-955d-e4d3248a8bfb')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avg_flow_test - record.avg_flow_test*mu_value
                    upper = record.avg_flow_test + record.avg_flow_test*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.avg_flow_test_nabl = 'pass'
                        break
                    else:
                        record.avg_flow_test_nabl = 'fail'







    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

        
    def get_all_fields(self):
        record = self.env['mechanical.fresh.cement.concrete'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.slump_test_visible = False
            record.density_visible = False
            record.flow_high_work_visible = False
            record.wet_density_visible = False
            record.flow_test_visible = False

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                
                if sample.internal_id == '49f934a0-ebd7-478b-a11e-641d7babc9c0':
                    record.slump_test_visible = True

                if sample.internal_id == '021ea043-8164-487b-8857-6aa4240a38df':
                    record.density_visible = True

                if sample.internal_id == '664503ee-02ac-48cf-88b0-a5e3bc33f290':
                    record.flow_high_work_visible = True

                if sample.internal_id == 'd0855037-7ccd-4238-bc7b-674a40d40580':
                    record.wet_density_visible = True

                if sample.internal_id == 'c3cad715-b384-4ac6-955d-e4d3248a8bfb':
                    record.flow_test_visible = True

                

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
            # Slump Test
            if result.parameter.internal_id == '49f934a0-ebd7-478b-a11e-641d7babc9c0':
                result.result_char = round(self.avg_slump_value,2)
                result.calculated = True
                if self.avg_slump_value_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Density Test
            if result.parameter.internal_id == '021ea043-8164-487b-8857-6aa4240a38df':
                result.result_char = round(self.avg_density,2)
                result.calculated = True
                if self.avg_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Flow of Concrete of High Workability Test
            if result.parameter.internal_id == '664503ee-02ac-48cf-88b0-a5e3bc33f290':
                result.result_char = round(self.avg_flow_high,2)
                result.calculated = True
                if self.avg_flow_high_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


            # Wet Density Test
            if result.parameter.internal_id == 'd0855037-7ccd-4238-bc7b-674a40d40580':
                result.result_char = round(self.avg_wet_density,2)
                result.calculated = True
                if self.avg_wet_density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Flow Test of Fresh Cement Concrete 
            if result.parameter.internal_id == 'c3cad715-b384-4ac6-955d-e4d3248a8bfb':
                result.result_char = round(self.avg_flow_test,2)
                result.calculated = True
                if self.avg_flow_test_nabl == 'pass':
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
        record = super(FreshCementConcrete, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     for record in self:
    #         records = record.eln_ref.parameters_result.parameter.ids
    #         record.sample_parameters = records
    #         print("Records",records)

    def get_all_fields(self):
        record = self.env['mechanical.fresh.cement.concrete'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
        
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



    
    


    


    

    

    


    notes_id = fields.One2many('mechanical.fresh.cement.concrete.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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
    



class FCCSlumpTestLine(models.Model):
    _name = "fcc.slump.test.line"
    _description = 'Slump Trial Line'

    parent_id = fields.Many2one('mechanical.fresh.cement.concrete', string="Parent Id")

    sample_no = fields.Integer(string="Trial No.", readonly=True, copy=False, default=1)

    cone_height = fields.Float(
        string="Height of Cone (mm)",
    )

    height_after_slump = fields.Float(
        string="Height After Slump (mm)"
    )

    slump_value = fields.Float(
        string="Slump Value (mm)",
        compute="_compute_slump",
        store=True
    )

    slump_type = fields.Selection([
        ('true', 'True'),
        ('shear', 'Shear'),
        ('collapse', 'Collapse')
    ], string="Type of Slump")

    @api.depends('cone_height', 'height_after_slump')
    def _compute_slump(self):
        for rec in self:
            rec.slump_value = rec.cone_height - rec.height_after_slump


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(FCCSlumpTestLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class FCCDensityTestLine(models.Model):
    _name = "fcc.density.test.line"
    _description = 'Density Trial Line'

    parent_id = fields.Many2one('mechanical.fresh.cement.concrete', string="Parent Id")

    sample_no = fields.Integer(string="Sr No.", readonly=True, copy=False, default=1)


    weight_container = fields.Float(string="Weight of Empty Container (W1) (kg)")
    weight_container_concrete = fields.Float(string="Weight of Empty Container + Fresh Compacted Concrete (Wc) (kg)")

    net_weight = fields.Float(string="Net Weight of Fresh Concrete (Wn = Wc  - W1) (kg) ",compute="_compute_net_weight",store=True,)

    volume = fields.Float(string="Calibrated Volume of Container (V) (m³)")

    density = fields.Float(string="Fresh Concrete Density (Y = Wn/V ) (kg/m³)",compute="_compute_density",store=True,)

    fresh_slump_value = fields.Float(string="Fresh Concrete Slump Value (Optional) (mm)")

    fresh_temp = fields.Float(string="Fresh Concrete Temperature (°C)")

    @api.depends('weight_container', 'weight_container_concrete')
    def _compute_net_weight(self):
     for rec in self:
        rec.net_weight = rec.weight_container_concrete - rec.weight_container

    @api.depends('net_weight', 'volume')
    def _compute_density(self):
     for rec in self:
        rec.density = rec.net_weight / rec.volume if rec.volume else 0.0


    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(FCCDensityTestLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1



class FCCFlowHighTestLine(models.Model):
    _name = "fcc.flow.high.test.line"
    _description = 'Flow Table Test Line'

    parent_id = fields.Many2one('mechanical.fresh.cement.concrete', string="Parent Id")

    sample_no = fields.Integer(string="Trial No.", readonly=True, copy=False, default=1)


    diameter_direction1 = fields.Float(
        string='Diameter Direction 1 (mm)'
    )

    diameter_direction2 = fields.Float(
        string='Diameter Direction 2 (mm)'
    )

    average_diameter = fields.Float(
        string='Average Diameter (mm)',
        compute='_compute_average',
        store=True
    )

    flow = fields.Float(
        string='Flow (%)',
        compute='_compute_flow',
        store=True
    )

    @api.depends('diameter_direction1', 'diameter_direction2')
    def _compute_average(self):
        for rec in self:
            rec.average_diameter = (
                rec.diameter_direction1 + rec.diameter_direction2
            ) / 2 if (rec.diameter_direction1 or rec.diameter_direction2) else 0.0

    @api.depends('average_diameter')
    def _compute_flow(self):
        """
        Flow % = ((Average Diameter - Base Diameter) / Base Diameter) * 100

        Base Diameter = 200 mm
        """
        BASE_DIAMETER = 200

        for rec in self:
            if rec.average_diameter:
                rec.flow = (
                    (rec.average_diameter - BASE_DIAMETER)
                    / BASE_DIAMETER
                ) * 100
            else:
                rec.flow = 0.0

    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(FCCFlowHighTestLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1




class FCCWetDensityTestLine(models.Model):
    _name = "fcc.wet.density.test.line"
    _description = 'Wet Density Trial Line'

    parent_id = fields.Many2one('mechanical.fresh.cement.concrete', string="Parent Id")

    sample_no = fields.Integer(string="Sr No.", readonly=True, copy=False, default=1)


    volume = fields.Float("Volume of Container (m³) (V)")
    weight_empty = fields.Float("Weight of Empty Container (kg) (W1)")
    weight_full = fields.Float("Weight of Container + Fresh Concrete (kg) (W2)")

    weight = fields.Float("Weight of Fresh Concrete (kg) (W = W₂ − W₁)",
    compute="_compute_values",store=True)

    wet_density = fields.Float("Wet Density of Fresh Concrete (kg/m³) (D = W/V)",compute="_compute_values",store=True)

    @api.depends('volume', 'weight_empty', 'weight_full')
    def _compute_values(self):
     for rec in self:
        rec.weight = rec.weight_full - rec.weight_empty
        rec.wet_density = rec.weight / rec.volume if rec.volume else 0


    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(FCCWetDensityTestLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1




class FCCFlowTableTestLine(models.Model):
    _name = "fcc.flow.table.test.line"
    _description = 'Flow Table Observation Line'

    parent_id = fields.Many2one('mechanical.fresh.cement.concrete', string="Parent Id")

    sample_no = fields.Integer(string="Sr No.", readonly=True, copy=False, default=1)

    initial_d1 = fields.Float("Initial Diameter D₁ (mm)")

    initial_d2 = fields.Float("Initial Diameter D₂ (mm)")

    final_d1 = fields.Float("Final Spread Diameter D₁ (mm)")

    final_d2 = fields.Float("Final Spread Diameter D₂ (mm)")

    drops = fields.Integer("Number of Drops/Jolts")

    duration = fields.Float("Test Duration (s)")

    avg_initial = fields.Float("Average Initial Diameter (mm)((D₁ + D₂)/2)",
        compute="_compute_average",
        store=True,
    )

    avg_final = fields.Float("Average Final Spread Diameter (mm)((D₁ + D₂)/2)",
        compute="_compute_average",
        store=True,
    )

    flow = fields.Float("Flow (%)  (((B − A)/A) × 100)",
        compute="_compute_average",
        store=True,
    )

    @api.depends("initial_d1", "initial_d2", "final_d1", "final_d2")
    def _compute_average(self):
        for rec in self:

            rec.avg_initial = (rec.initial_d1 + rec.initial_d2) / 2

            rec.avg_final = (rec.final_d1 + rec.final_d2) / 2

            if rec.avg_initial:
                rec.flow = (
                    (rec.avg_final - rec.avg_initial)
                    / rec.avg_initial
                ) * 100
            else:
                rec.flow = 0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(FCCFlowTableTestLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1
    




class FreshCementConcreteNotes(models.Model):
    _name = "mechanical.fresh.cement.concrete.notes"

    parent_id = fields.Many2one('mechanical.fresh.cement.concrete', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
