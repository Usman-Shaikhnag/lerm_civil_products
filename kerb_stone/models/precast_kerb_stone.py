from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class PrecastKerbMechanical(models.Model):
    _name = "mechanical.precast.kerb"
    _inherit = "lerm.eln"
    _rec_name = "name"


    name = fields.Char("Name",default="Precast Kerb Stone")
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    temp = fields.Char("Temperature",store=True)
    humidity = fields.Char("Humidity",store=True)

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
       
    


    notes_id = fields.One2many('mechanical.precast.kerb.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

    @api.model
    def _default_notes_lines(self):
        return [
            (0, 0, {
                'sr_no': 'i',
                'notes': 'The results stated in this report apply only to the tested sample(s) and are based on the conditions and parameters at the time of testing.',
            }),
            (0, 0, {
                'sr_no': 'ii',
                'notes': 'This report is invalid without the official paper seal of Make Infracon.',
            }),
            (0, 0, {
                'sr_no': 'iii',
                'notes': 'All test results are confidential and will not be disclosed to any third party without written consent of the client, except where required by law.',
            }),
            (0, 0, {
                'sr_no': 'iv',
                'notes': 'The # points mentioned in the report which information is given by Client/Customer.',
            }),

            (0, 0, {
                'sr_no': 'v',
                'notes': 'Any disputes shall be subject to jurisdiction of Nashik courts only.',
            }),
        ]
    

    # Dimension
    dimension_name = fields.Char(default="Dimension")
    dimension_visible = fields.Boolean(compute="_compute_visible")


    dimension_lines = fields.One2many('kerb.stone.dimension.line','parent_id',string="Parameter")

    avrg_length = fields.Float(string="Average length",compute="_compute_dimension",
    store=True)
    avrg_width = fields.Float(string="Average Width",compute="_compute_dimension",
    store=True)
    avrg_height = fields.Float(string="Average Height",compute="_compute_dimension",
    store=True)

    @api.depends('dimension_lines.lengthh', 'dimension_lines.width', 'dimension_lines.height')
    def _compute_dimension(self):
     for rec in self:

        lengths = [l for l in rec.dimension_lines.mapped('lengthh') if l]
        widths = [w for w in rec.dimension_lines.mapped('width') if w]
        heights = [h for h in rec.dimension_lines.mapped('height') if h]

        rec.avrg_length = sum(lengths) / len(lengths) if lengths else 0.0
        rec.avrg_width = sum(widths) / len(widths) if widths else 0.0
        rec.avrg_height = sum(heights) / len(heights) if heights else 0.0


    avrg_length_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_avrg_length_confirmity")

    avrg_length_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_avrg_length_nabl",store=True)


    @api.depends('avrg_length','eln_ref')
    def _compute_avrg_length_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avrg_length_confirmity = 'na'
                continue
            record.avrg_length_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9ee7f8c7-1c76-49d5-b8fd-a53e30f85706')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9ee7f8c7-1c76-49d5-b8fd-a53e30f85706')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avrg_length - record.avrg_length*mu_value
                    upper = record.avrg_length + record.avrg_length*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avrg_length_confirmity = 'pass'
                        break
                    else:
                        record.avrg_length_confirmity = 'fail'

    @api.depends('avrg_length','eln_ref')
    def _compute_avrg_length_nabl(self):
        
        for record in self:
            record.avrg_length_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9ee7f8c7-1c76-49d5-b8fd-a53e30f85706')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9ee7f8c7-1c76-49d5-b8fd-a53e30f85706')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.avrg_length - record.avrg_length*mu_value
                  upper = record.avrg_length + record.avrg_length*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.avrg_length_nabl = 'pass'
                      break
                  else:
                      record.avrg_length_nabl = 'fail'


    avrg_length_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avrg_length_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avrg_length_final_report", store=True)

    @api.depends('avrg_length_nabl', 'avrg_length_report_type')
    def _compute_avrg_length_final_report(self):
     for rec in self:

        # Manual override
        if rec.avrg_length_report_type == 'nabl':
            rec.avrg_length_final_report = 'nabl'

        elif rec.avrg_length_report_type == 'non_nabl':
            rec.avrg_length_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avrg_length_nabl == 'pass':
                rec.avrg_length_final_report = 'nabl'
            else:
                rec.avrg_length_final_report = 'non_nabl'


    

    avrg_width_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_avrg_width_confirmity")

    avrg_width_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_avrg_width_nabl",store=True)


    @api.depends('avrg_width','eln_ref')
    def _compute_avrg_width_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avrg_width_confirmity = 'na'
                continue
            record.avrg_width_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','643a2c94-641d-45ca-b908-a07122f0216c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','643a2c94-641d-45ca-b908-a07122f0216c')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avrg_width - record.avrg_width*mu_value
                    upper = record.avrg_width + record.avrg_width*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avrg_width_confirmity = 'pass'
                        break
                    else:
                        record.avrg_width_confirmity = 'fail'

    @api.depends('avrg_width','eln_ref')
    def _compute_avrg_width_nabl(self):
        
        for record in self:
            record.avrg_width_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','643a2c94-641d-45ca-b908-a07122f0216c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','643a2c94-641d-45ca-b908-a07122f0216c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.avrg_width - record.avrg_width*mu_value
                  upper = record.avrg_width + record.avrg_width*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.avrg_width_nabl = 'pass'
                      break
                  else:
                      record.avrg_width_nabl = 'fail'

    avrg_width_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avrg_width_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avrg_width_final_report", store=True)

    @api.depends('avrg_width_nabl', 'avrg_width_report_type')
    def _compute_avrg_width_final_report(self):
     for rec in self:

        # Manual override
        if rec.avrg_width_report_type == 'nabl':
            rec.avrg_width_final_report = 'nabl'

        elif rec.avrg_width_report_type == 'non_nabl':
            rec.avrg_width_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avrg_width_nabl == 'pass':
                rec.avrg_width_final_report = 'nabl'
            else:
                rec.avrg_width_final_report = 'non_nabl'


    avrg_height_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_avrg_height_confirmity")

    avrg_height_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_avrg_height_nabl",store=True)


    @api.depends('avrg_height','eln_ref')
    def _compute_avrg_height_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avrg_height_confirmity = 'na'
                continue
            record.avrg_height_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','90a040c2-8ac0-40d2-aff0-50f0c187697c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','90a040c2-8ac0-40d2-aff0-50f0c187697c')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avrg_height - record.avrg_height*mu_value
                    upper = record.avrg_height + record.avrg_height*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avrg_height_confirmity = 'pass'
                        break
                    else:
                        record.avrg_height_confirmity = 'fail'

    @api.depends('avrg_height','eln_ref')
    def _compute_avrg_height_nabl(self):
        
        for record in self:
            record.avrg_height_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','90a040c2-8ac0-40d2-aff0-50f0c187697c')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','90a040c2-8ac0-40d2-aff0-50f0c187697c')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.avrg_height - record.avrg_height*mu_value
                  upper = record.avrg_height + record.avrg_height*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.avrg_height_nabl = 'pass'
                      break
                  else:
                      record.avrg_height_nabl = 'fail'

    avrg_height_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avrg_height_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avrg_height_final_report", store=True)

    @api.depends('avrg_height_nabl', 'avrg_height_report_type')
    def _compute_avrg_height_final_report(self):
     for rec in self:

        # Manual override
        if rec.avrg_height_report_type == 'nabl':
            rec.avrg_height_final_report = 'nabl'

        elif rec.avrg_height_report_type == 'non_nabl':
            rec.avrg_height_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avrg_height_nabl == 'pass':
                rec.avrg_height_final_report = 'nabl'
            else:
                rec.avrg_height_final_report = 'non_nabl'


    # Compressive Strength
    compressive_strength_name = fields.Char(default="Compressive Strength")
    compressive_strength_visible = fields.Boolean(compute="_compute_visible")

    compressive_strength_table = fields.One2many('kerb.stone.compressive.line','parent_id', string="Compressive Strength")

    avg_compressive_strength = fields.Float(string="Average Strength",compute="_compute_average_strength",store=True)

    @api.depends('compressive_strength_table.compressive_strength')
    def _compute_average_strength(self):
     for rec in self:
        values = rec.compressive_strength_table.mapped('compressive_strength')
        rec.avg_compressive_strength = (
            sum(values) / len(values) if values else 0.0
        )


    

    avg_compressive_strength_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_avg_compressive_strength_confirmity")

    avg_compressive_strength_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_avg_compressive_strength_nabl",store=True)


    @api.depends('avg_compressive_strength','eln_ref')
    def _compute_avg_compressive_strength_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avg_compressive_strength_confirmity = 'na'
                continue
            record.avg_compressive_strength_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9dccce17-5e98-43c1-8d32-bbca24aae288')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9dccce17-5e98-43c1-8d32-bbca24aae288')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avg_compressive_strength - record.avg_compressive_strength*mu_value
                    upper = record.avg_compressive_strength + record.avg_compressive_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.avg_compressive_strength_confirmity = 'pass'
                        break
                    else:
                        record.avg_compressive_strength_confirmity = 'fail'

    @api.depends('avg_compressive_strength','eln_ref')
    def _compute_avg_compressive_strength_nabl(self):
        
        for record in self:
            record.avg_compressive_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9dccce17-5e98-43c1-8d32-bbca24aae288')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','9dccce17-5e98-43c1-8d32-bbca24aae288')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.avg_compressive_strength - record.avg_compressive_strength*mu_value
                  upper = record.avg_compressive_strength + record.avg_compressive_strength*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.avg_compressive_strength_nabl = 'pass'
                      break
                  else:
                      record.avg_compressive_strength_nabl = 'fail'


    compressive_strength_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    compressive_strength_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_compressive_strength_final_report", store=True)

    @api.depends('avg_compressive_strength_nabl', 'compressive_strength_report_type')
    def _compute_compressive_strength_final_report(self):
     for rec in self:

        # Manual override
        if rec.compressive_strength_report_type == 'nabl':
            rec.compressive_strength_final_report = 'nabl'

        elif rec.compressive_strength_report_type == 'non_nabl':
            rec.compressive_strength_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avg_compressive_strength_nabl == 'pass':
                rec.compressive_strength_final_report = 'nabl'
            else:
                rec.compressive_strength_final_report = 'non_nabl'

    

    # Water Absorption
    water_absorbtion_name = fields.Char(default="Water Absorption")
    water_absorption_visible = fields.Boolean(compute="_compute_visible")

    water_absorbtion_table = fields.One2many('mech.precast.water.absorbtion.line','parent_id',string="Water Absorption")

    @api.onchange('water_absorbtion_table')
    def _onchange_water_absorbtion_table(self):
        for rec in self:
            for index, line in enumerate(rec.water_absorbtion_table, start=1):
                line.serial_no = index

    average_water_absorption = fields.Float(
    string="Average Water Absorption (%)",
    compute="_compute_average_water_absorption",
    store=True,
)

    @api.depends('water_absorbtion_table.average')
    def _compute_average_water_absorption(self):
     for rec in self:
        values = [
            line.average
            for line in rec.water_absorbtion_table
            if line.average > 0
        ]

        rec.average_water_absorption = (
            sum(values) / len(values)
            if values else 0.0
        )

        
    average_water_absorption_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_average_water_absorption_confirmity")

    average_water_absorption_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_average_water_absorption_nabl",store=True)


    @api.depends('average_water_absorption','eln_ref')
    def _compute_average_water_absorption_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_water_absorption_confirmity = 'na'
                continue
            record.average_water_absorption_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f913fc79-eeb4-4e16-a7fc-75608384d9b0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f913fc79-eeb4-4e16-a7fc-75608384d9b0')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_water_absorption - record.average_water_absorption*mu_value
                    upper = record.average_water_absorption + record.average_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.average_water_absorption_confirmity = 'pass'
                        break
                    else:
                        record.average_water_absorption_confirmity = 'fail'

    @api.depends('average_water_absorption','eln_ref')
    def _compute_average_water_absorption_nabl(self):
        
        for record in self:
            record.average_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f913fc79-eeb4-4e16-a7fc-75608384d9b0')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','f913fc79-eeb4-4e16-a7fc-75608384d9b0')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.average_water_absorption - record.average_water_absorption*mu_value
                  upper = record.average_water_absorption + record.average_water_absorption*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.average_water_absorption_nabl = 'pass'
                      break
                  else:
                      record.average_water_absorption_nabl = 'fail'


    water_absorption_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    water_absorption_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_water_absorption_final_report", store=True)

    @api.depends('average_water_absorption_nabl', 'water_absorption_report_type')
    def _compute_water_absorption_final_report(self):
     for rec in self:

        # Manual override
        if rec.water_absorption_report_type == 'nabl':
            rec.water_absorption_final_report = 'nabl'

        elif rec.water_absorption_report_type == 'non_nabl':
            rec.water_absorption_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.average_water_absorption_nabl == 'pass':
                rec.water_absorption_final_report = 'nabl'
            else:
                rec.water_absorption_final_report = 'non_nabl'

    

    

    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(PrecastKerbMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    def get_all_fields(self):
        record = self.env['mechanical.precast.kerb'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

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


    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.dimension_visible  = False
            record.compressive_strength_visible = False
            record.water_absorption_visible  = False  
            

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == 'klrt1230t-eeb4-4e16-a7fc-7560838410lo':
                    record.dimension_visible = True

                if sample.internal_id == '9dccce17-5e98-43c1-8d32-bbca24aae288':
                    record.compressive_strength_visible = True

                if sample.internal_id == 'f913fc79-eeb4-4e16-a7fc-75608384d9b0':
                    record.water_absorption_visible = True
                

    # def open_eln_page(self):
        # import wdb; wdb.set_trace()




    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
          
            
            if result.parameter.internal_id == '9dccce17-5e98-43c1-8d32-bbca24aae288':
                result.result_char = round(self.avg_compressive_strength,2)
                result.calculated = True
                if self.avg_compressive_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == 'f913fc79-eeb4-4e16-a7fc-75608384d9b0':
                result.result_char = round(self.average_water_absorption,2)
                result.calculated = True
                if self.average_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue




            # Dimension
            if result.parameter.internal_id == 'klrt1230t-eeb4-4e16-a7fc-7560838410lo':
                result.calculated = True

            # Length - Dimension
            if result.parameter.internal_id == '9ee7f8c7-1c76-49d5-b8fd-a53e30f85706':
                result.result_char = round(self.avrg_length,2)
                result.calculated = True
                if self.avrg_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Width - Dimension
            if result.parameter.internal_id == '643a2c94-641d-45ca-b908-a07122f0216c':
                result.result_char = round(self.avrg_width,2)
                result.calculated = True
                if self.avrg_width_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Height - Dimension
            if result.parameter.internal_id == '90a040c2-8ac0-40d2-aff0-50f0c187697c':
                result.result_char = round(self.avrg_height,2)
                result.calculated = True
                if self.avrg_height_nabl == 'pass':
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


    

class KerbStoneDimensionLine(models.Model):
    _name = "kerb.stone.dimension.line"
    parent_id = fields.Many2one('mechanical.precast.kerb', string="Parent Id")

    serial_no = fields.Integer(string="Sr.No", readonly=True, copy=False, default=1)
    kerb_id = fields.Char(string="Kerb Stone ID")
    lengthh = fields.Float(string="Length (in mm)")
    width = fields.Float(string="Width (in mm)")
    height = fields.Float(string="Height (in mm)")

    remarks = fields.Char("Remarks")

    # @api.depends(
    #     'lengthh',
    #     'width',
    #     'height',
    #     'parent_id.nominal_length',
    #     'parent_id.nominal_width',
    #     'parent_id.nominal_height'
    # )
    # def _compute_remarks(self):
    #     for rec in self:
    #         result = []

    #         # Length tolerance
    #         if rec.parent_id.nominal_length:
    #             tol = min(rec.parent_id.nominal_length * 0.01, 10)
    #             if abs(rec.lengthh - rec.parent_id.nominal_length) <= tol:
    #                 result.append("Length OK")
    #             else:
    #                 result.append("Length Not OK")

    #         # Width tolerance (Face)
    #         if rec.parent_id.nominal_width:
    #             tol = min(rec.parent_id.nominal_width * 0.03, 5)
    #             if abs(rec.width - rec.parent_id.nominal_width) <= tol:
    #                 result.append("Width OK")
    #             else:
    #                 result.append("Width Not OK")

    #         # Height tolerance (Face)
    #         if rec.parent_id.nominal_height:
    #             tol = min(rec.parent_id.nominal_height * 0.03, 5)
    #             if abs(rec.height - rec.parent_id.nominal_height) <= tol:
    #                 result.append("Height OK")
    #             else:
    #                 result.append("Height Not OK")

    #         rec.remarks = ", ".join(result)
    
    
   
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(KerbStoneDimensionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class KerbStoneCompressiveLine(models.Model):
    _name = "kerb.stone.compressive.line"
    parent_id = fields.Many2one('mechanical.precast.kerb', string="Parent Id")

    serial_no = fields.Integer(string="Sr.No", readonly=True, copy=False, default=1)


    age = fields.Char(string="Age of Specimen")

    height = fields.Float("Height (mm)")
    diameter = fields.Float("Dia (mm)")

    hd_ratio = fields.Float(string="H/D Ratio (n)",compute="_compute_values",store=True)

    correction_factor = fields.Float(string="Correction factor f =0.11n+0.78 Where,  f= Correction factor,n= height to diameter ratio" , compute="_compute_values",store=True)

    area = fields.Float(string="Area (mm²) π r² ",compute="_compute_values",store=True,digits=(16,3))

    volume = fields.Float(string="Volume (cc) πr²h",compute="_compute_values",store=True)

    weight = fields.Float("Weight (gm)")

    density = fields.Float(
        string="Density (gm/cc)",
        compute="_compute_values",
        store=True,digits=(16,3)
    )

    load = fields.Float("Load (kN)")

    compressive_strength = fields.Float(
        string="Compressive Strength (N/mm²)",
        compute="_compute_values",
        store=True
    )

    @api.depends(
        'height',
        'diameter',
        'weight',
        'load'
    )
    def _compute_values(self):

        for rec in self:

            # H/D Ratio
            if rec.diameter:
                rec.hd_ratio = rec.height / rec.diameter
            else:
                rec.hd_ratio = 0

            # Correction Factor
            # Use the formula if required
            rec.correction_factor = round(
                (0.11 * rec.hd_ratio) + 0.78,
                2
            )

            # If you want exactly like Excel
            # uncomment below and remove above
            #
            # if rec.hd_ratio <= 2:
            #     rec.correction_factor = 1.00
            # else:
            #     rec.correction_factor = 1.01

            # Area
            if rec.diameter:
                rec.area = 3.14 * rec.diameter * rec.diameter / 4
            else:
                rec.area = 0

            # Volume
            rec.volume = (rec.area * rec.height) / 100

            # Density
            if rec.volume:
                rec.density = rec.weight / rec.volume
            else:
                rec.density = 0

            # Compressive Strength
            if rec.area:
                rec.compressive_strength = (
                    rec.load  / rec.area) * 1000
            else:
                rec.compressive_strength = 0

    
   
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(KerbStoneCompressiveLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1
   


class PrecastWaterAbsorbtionLine(models.Model):
    _name = "mech.precast.water.absorbtion.line"
    parent_id = fields.Many2one('mechanical.precast.kerb', string="Parent Id")

    serial_no = fields.Integer(string="Sr.No", readonly=True, copy=False, default=1)

    m1 = fields.Float(string="Mass of specimens immersed in water (M1)")
    m2 = fields.Float(string="Mass of dry specimen (M2)")

    water_absorption = fields.Float(
        string="Percentage water absorption=(M1-M2)/M2*100",
        compute="_compute_values",
        store=True,digits=(16,3)
    )

    average = fields.Float(
        string="Average",
        compute="_compute_average",
        store=True,digits=(16,3)
    )

    remark = fields.Char(string="Remark")

    @api.depends("m1", "m2")
    def _compute_values(self):
        for rec in self:
            if rec.m2:
                rec.water_absorption = ((rec.m1 - rec.m2) / rec.m2) * 100
            else:
                rec.water_absorption = 0.0

    @api.depends(
    'parent_id.water_absorbtion_table.water_absorption'
)
    def _compute_average(self):
     parents = self.mapped('parent_id')

     for parent in parents:
        lines = parent.water_absorbtion_table

        # Reset
        for line in lines:
            line.average = 0.0

        # Average every two rows
        for i in range(0, len(lines), 2):
            pair = lines[i:i + 2]

            if len(pair) == 2:
                avg = (pair[0].water_absorption + pair[1].water_absorption) / 2
                pair[0].average = avg
                pair[1].average = 0.0
            else:
                pair[0].average = pair[0].water_absorption

    

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(PrecastWaterAbsorbtionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1
   





    

    
class PrecastKerbMechanicalNotes(models.Model):
    _name = "mechanical.precast.kerb.notes"

    parent_id = fields.Many2one('mechanical.precast.kerb', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
