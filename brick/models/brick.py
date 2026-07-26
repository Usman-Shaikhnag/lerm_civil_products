from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class MechanicalBricks(models.Model):
    _name = "mechanical.bricks"
    _inherit = "lerm.eln"
    _description = 'mechanical.bricks'
    _rec_name = "name"

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    name = fields.Char("Name",default="Fly Ash Bricks")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    brick_temperature = fields.Char("Temperature",store=True)
    brick_humidity = fields.Char("Humidity",store="True")

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'bricks.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }
    

    notes_id = fields.One2many('mechanical.bricks.notes', 'parent_id',string="Notes",
    default=lambda self: self._default_notes_lines()
)
    
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
    

    
    


    #  Water Absorption
    water_absorbtion_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")
    wt_absorption_name = fields.Char("Name",default="Water Absorption")

    water_absorbtion_line_ids = fields.One2many('brick.water.absorption.line', 'parent_id', string="Observations")

    @api.depends('water_absorbtion_line_ids.water_absorption')
    def _compute_avrg_water_absorption(self):
        for rec in self:
            values = rec.water_absorbtion_line_ids.mapped('water_absorption')
            rec.avrg_water_absorption = sum(values) / len(values) if values else 0.0

    avrg_water_absorption = fields.Float(string="Average Water Absorption, %", compute="_compute_avrg_water_absorption", digits=(16, 2))

    water_absorption_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_water_absorption_confirmity")

    water_absorption_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_water_absorption_nabl",store=True)


    @api.depends('avrg_water_absorption','eln_ref')
    def _compute_water_absorption_confirmity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.water_absorption_confirmity = 'na'
                continue
            record.water_absorption_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321475gfet1-f3ab-4b19-af25-91a4671baf5f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321475gfet1-f3ab-4b19-af25-91a4671baf5f')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avrg_water_absorption - record.avrg_water_absorption*mu_value
                    upper = record.avrg_water_absorption + record.avrg_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.water_absorption_confirmity = 'pass'
                        break
                    else:
                        record.water_absorption_confirmity = 'fail'

    @api.depends('avrg_water_absorption','eln_ref')
    def _compute_water_absorption_nabl(self):
        
        for record in self:
            record.water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321475gfet1-f3ab-4b19-af25-91a4671baf5f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','321475gfet1-f3ab-4b19-af25-91a4671baf5f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                  lab_min = line.lab_min_value
                  lab_max = line.lab_max_value
                  mu_value = line.mu_value
            
                  lower = record.avrg_water_absorption - record.avrg_water_absorption*mu_value
                  upper = record.avrg_water_absorption + record.avrg_water_absorption*mu_value
                  if lower >= lab_min and upper <= lab_max:
                      record.water_absorption_nabl = 'pass'
                      break
                  else:
                      record.water_absorption_nabl = 'fail'


    water_absorption_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    water_absorption_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_water_absorption_final_report", store=True)

    @api.depends('water_absorption_nabl', 'water_absorption_report_type')
    def _compute_water_absorption_final_report(self):
     for rec in self:

        # Manual override
        if rec.water_absorption_report_type == 'nabl':
            rec.water_absorption_final_report = 'nabl'

        elif rec.water_absorption_report_type == 'non_nabl':
            rec.water_absorption_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.water_absorption_nabl == 'pass':
                rec.water_absorption_final_report = 'nabl'
            else:
                rec.water_absorption_final_report = 'non_nabl'

  



    #  Compressive Strength

    compressive_strength_visible = fields.Boolean("Compressive Strengt Visible",compute="_compute_visible")
    compressive_strength_name = fields.Char("Name",default="Compressive Strength")

    compressive_strength_line_ids = fields.One2many('brick.compressive.line', 'parent_id', string="Observations")

    @api.depends('compressive_strength_line_ids.compressive_strength')
    def _compute_avrg_compressive_strength(self):
        for rec in self:
            values = rec.compressive_strength_line_ids.mapped('compressive_strength')
            rec.avrg_compressive_strength = sum(values) / len(values) if values else 0.0

    
    avrg_compressive_strength = fields.Float(string="Average Compressive Strength",compute="_compute_avrg_compressive_strength", digits=(16, 2))

    comp_strength_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', compute="_compute_comp_strength_conformity")

    comp_strength_nabl = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')],string="NABL",compute="_compute_comp_strength_nabl",store=True)

    @api.depends('avrg_compressive_strength','eln_ref')
    def _compute_comp_strength_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.comp_strength_confirmity = 'na'
                continue
            record.comp_strength_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','31478fghht-9287-48c7-a607-bf1b64a8115d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','31478fghht-9287-48c7-a607-bf1b64a8115d')]).parameter_table
            for material in materials:
                
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.avrg_compressive_strength - record.avrg_compressive_strength*mu_value
                    upper = record.avrg_compressive_strength + record.avrg_compressive_strength*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.comp_strength_confirmity = 'pass'
                        break
                    else:
                        record.comp_strength_confirmity = 'fail'

    @api.depends('avrg_compressive_strength','eln_ref')
    def _compute_comp_strength_nabl(self):
        
        for record in self:
            record.comp_strength_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','31478fghht-9287-48c7-a607-bf1b64a8115d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','31478fghht-9287-48c7-a607-bf1b64a8115d')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avrg_compressive_strength - record.avrg_compressive_strength*mu_value
            upper = record.avrg_compressive_strength + record.avrg_compressive_strength*mu_value
            # import wdb;wdb.set_trace()
            if lower >= lab_min and upper <= lab_max:
                record.comp_strength_nabl = 'pass'
                break
            else:
                record.comp_strength_nabl = 'fail'


    comp_strength_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    comp_strength_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_comp_strength_final_report", store=True)

    @api.depends('comp_strength_nabl', 'comp_strength_report_type')
    def _compute_comp_strength_final_report(self):
     for rec in self:

        # Manual override
        if rec.comp_strength_report_type == 'nabl':
            rec.comp_strength_final_report = 'nabl'

        elif rec.comp_strength_report_type == 'non_nabl':
            rec.comp_strength_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.comp_strength_nabl == 'pass':
                rec.comp_strength_final_report = 'nabl'
            else:
                rec.comp_strength_final_report = 'non_nabl'

    


    


        

    # Dimension 

    dimension_visible = fields.Boolean("Dimension Visible",compute="_compute_visible")
    dimension_name = fields.Char("Name",default="Dimension (mm)")

    dimension_lines = fields.One2many('fly.bricks.dimension.line','parent_id',string="Parameter")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','50e5bbcc-df2c-4fa9-8360-d0567d753361')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','50e5bbcc-df2c-4fa9-8360-d0567d753361')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','50e5bbcc-df2c-4fa9-8360-d0567d753361')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','50e5bbcc-df2c-4fa9-8360-d0567d753361')]).parameter_table
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


    avg_length_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_length_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_length_final_report", store=True)

    @api.depends('avrg_length_nabl', 'avg_length_report_type')
    def _compute_avg_length_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_length_report_type == 'nabl':
            rec.avg_length_final_report = 'nabl'

        elif rec.avg_length_report_type == 'non_nabl':
            rec.avg_length_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avrg_length_nabl == 'pass':
                rec.avg_length_final_report = 'nabl'
            else:
                rec.avg_length_final_report = 'non_nabl'


    

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62fd063f-251a-4ab3-9025-d90755deb02e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62fd063f-251a-4ab3-9025-d90755deb02e')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62fd063f-251a-4ab3-9025-d90755deb02e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','62fd063f-251a-4ab3-9025-d90755deb02e')]).parameter_table
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

    avg_width_report_type = fields.Selection([
    ('auto', 'Auto'),
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], string="Report Type", default='auto')

    avg_width_final_report = fields.Selection([
    ('nabl', 'NABL'),
    ('non_nabl', 'Non-NABL'),], compute="_compute_avg_width_final_report", store=True)

    @api.depends('avrg_width_nabl', 'avg_width_report_type')
    def _compute_avg_width_final_report(self):
     for rec in self:

        # Manual override
        if rec.avg_width_report_type == 'nabl':
            rec.avg_width_final_report = 'nabl'

        elif rec.avg_width_report_type == 'non_nabl':
            rec.avg_width_final_report = 'non_nabl'

        # Automatic
        else:
            if rec.avrg_width_nabl == 'pass':
                rec.avg_width_final_report = 'nabl'
            else:
                rec.avg_width_final_report = 'non_nabl'


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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d967f0e-21de-4c17-9f98-8202f3133ccb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d967f0e-21de-4c17-9f98-8202f3133ccb')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d967f0e-21de-4c17-9f98-8202f3133ccb')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5d967f0e-21de-4c17-9f98-8202f3133ccb')]).parameter_table
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


    


    

    #  Efflorescence 
    efflorescence_visible = fields.Boolean("Efflorescence Visible",compute="_compute_visible")
    visual_observation_name_efforescence = fields.Char("Name",default="Efflorescence")

    efflorescence_line_ids = fields.One2many(
        "fly.bricks.efflorescence.line",
        "parent_id",
        string="Observation Lines"
    )


    report_type = fields.Selection(
        [
            ('nabl', 'NABL'),
            ('non_nabl', 'Non NABL'),
        ],
        string="Report Type",
        default='nabl',
        required=True,
    )

    efflorescence_nabl = fields.Selection(
    [('pass', 'Pass'), ('fail', 'Fail')],
    compute="_compute_efflorescence_nabl",
    store=True
)

    @api.depends('report_type')
    def _compute_efflorescence_nabl(self):
     for rec in self:
        rec.efflorescence_nabl = 'pass' if rec.report_type == 'nabl' else 'fail'


    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.compressive_strength_visible = False
            record.water_absorbtion_visible = False
            record.efflorescence_visible = False
            record.dimension_visible = False
            record.efflorescence_visible=False
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

                if sample.internal_id == "31478fghht-9287-48c7-a607-bf1b64a8115d":
                    record.compressive_strength_visible = True

                if sample.internal_id == "321475gfet1-f3ab-4b19-af25-91a4671baf5f":
                    record.water_absorbtion_visible = True

                if sample.internal_id == "3214598fgrt-d27d-4ef9-9b27-e8eb4e7ae6ac":
                    record.efflorescence_visible = True

                if sample.internal_id == "125478bvf3-8d5d-4f45-8afb-b911f9cafe41":
                    record.dimension_visible = True 

                if sample.internal_id == "3214598fgrt-d27d-4ef9-9b27-e8eb4e7ae6ac":
                    record.efflorescence_visible = True 
                


     
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
            # Compressive Strength 
            if result.parameter.internal_id == '31478fghht-9287-48c7-a607-bf1b64a8115d':
                result.result_char = round(self.avrg_compressive_strength,2)
                result.calculated = True
                if self.comp_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # water absorbtion
            if result.parameter.internal_id == '321475gfet1-f3ab-4b19-af25-91a4671baf5f':
                result.result_char = round(self.avrg_water_absorption,2)
                result.calculated = True
                if self.water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            # Efflorence
            if result.parameter.internal_id == '3214598fgrt-d27d-4ef9-9b27-e8eb4e7ae6ac':
                # result.result_char = round(self.avrg_water_absorption,2)
                result.calculated = True


            # Dimension
            if result.parameter.internal_id == '125478bvf3-8d5d-4f45-8afb-b911f9cafe41':
                result.calculated = True

            # Length - Dimension
            if result.parameter.internal_id == '50e5bbcc-df2c-4fa9-8360-d0567d753361':
                result.result_char = round(self.avrg_length,2)
                result.calculated = True
                if self.avrg_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Width - Dimension
            if result.parameter.internal_id == '62fd063f-251a-4ab3-9025-d90755deb02e':
                result.result_char = round(self.avrg_width,2)
                result.calculated = True
                if self.avrg_width_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Height - Dimension
            if result.parameter.internal_id == '5d967f0e-21de-4c17-9f98-8202f3133ccb':
                result.result_char = round(self.avrg_height,2)
                result.calculated = True
                if self.avrg_height_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue



            # Efflorescence
            if result.parameter.internal_id == '3214598fgrt-d27d-4ef9-9b27-e8eb4e7ae6ac':
                
                result.calculated = True
            
            

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
        record = super(MechanicalBricks, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
    

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
        record = self.env['mechanical.bricks'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    
    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()

        return super(MechanicalBricks, self).read(fields=fields, load=load)
    
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
    


class BrickWaterAbsorptionLine(models.Model):
    _name = "brick.water.absorption.line"
    _description = "Water Absorption Test"

    parent_id = fields.Many2one('mechanical.bricks',string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)

    
    identifi_no = fields.Char("Bricks Identification No.")
    w1 = fields.Float("Weight of Oven Dried Sample (W1)")
    w2 = fields.Float("Weight of Sample After Water Absorption (W2)")

    water_absorption = fields.Float("% Water Aborption (W2-W1/W1)*100", compute="_compute_values", store=True)

    @api.depends('w1', 'w2')
    def _compute_values(self):
        for rec in self:
            if rec.w1:
                rec.water_absorption = ((rec.w2 - rec.w1) / rec.w1) * 100
            else:
                rec.water_absorption = 0.0


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(BrickWaterAbsorptionLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1

class BrickCompressiveLine(models.Model):
    _name = "brick.compressive.line"
    _description = "Brick Compressive Test"

    parent_id = fields.Many2one('mechanical.bricks',string="Parent Id")

    sample_no = fields.Integer(string="Sample", readonly=True, copy=False, default=1)

    length = fields.Float("Length in mm")
    width = fields.Float("Width in  mm")
    area = fields.Float("Area in mm2", compute="_compute_area", store=True)
    load_kn = fields.Float("Load in KN")
    compressive_strength = fields.Float("Compressive Strength (N/mm2)", compute="_compute_area", store=True)

    @api.depends('length', 'width','load_kn')
    def _compute_area(self):
        for record in self:
                record.area = record.length * record.width
                if record.area != 0:
                  record.compressive_strength = record.load_kn / record.area * 1000
                else:
                  record.compressive_strength = 0.0

            


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sample_no'))
                vals['sample_no'] = max_serial_no + 1

        return super(BrickCompressiveLine, self).create(vals)


    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sample_no = index + 1


class FLYBrickDimensionLine(models.Model):
    _name = "fly.bricks.dimension.line"
    parent_id = fields.Many2one('mechanical.bricks',string="Parent Id")

    serial_no = fields.Integer(string="Sample No", readonly=True, copy=False, default=1)

    no_bricks = fields.Float(string="No. of Bricks")
    lengthh = fields.Float(string="Length")
    width = fields.Float(string="Width")
    height = fields.Float(string="Height")
    
   
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(FLYBrickDimensionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class BrickEflorescenceLine(models.Model):
    _name = "fly.bricks.efflorescence.line"
    parent_id = fields.Many2one('mechanical.bricks',string="Parent Id")

    serial_no = fields.Integer(string="Sample No", readonly=True, copy=False, default=1)

    brick_identification_no = fields.Char(
        string="Brick Identification No."
    )

    water_level = fields.Float(
        string="Water Level (mm)"
    )

    first_cycle = fields.Selection([
        ('nil', 'NIL'),
        ('slight', 'SLIGHT'),
        ('moderate', 'MODERATE'),
        ('heavy', 'HEAVY'),
        ('serious', 'SERIOUS'),
    ], string="1st Cycle Observation")

    second_cycle = fields.Selection([
        ('nil', 'NIL'),
        ('slight', 'SLIGHT'),
        ('moderate', 'MODERATE'),
        ('heavy', 'HEAVY'),
        ('serious', 'SERIOUS'),
    ], string="2nd Cycle Observation")

    efflorescence_rating = fields.Selection([
        ('nil', 'NIL'),
        ('slight', 'SLIGHT'),
        ('moderate', 'MODERATE'),
        ('heavy', 'HEAVY'),
        ('serious', 'SERIOUS'),
    ], string="Efflorescence Rating")

    remarks = fields.Char("Remarks")
    
   
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(BrickEflorescenceLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class MechanicalBricksNotes(models.Model):
    _name = "mechanical.bricks.notes"

    parent_id = fields.Many2one('mechanical.bricks',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")