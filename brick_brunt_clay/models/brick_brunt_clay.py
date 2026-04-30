from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class MechanicalBricksBurntClay(models.Model):
    _name = "mechanical.bricks.burnt.clay"
    _inherit = "lerm.eln"
    _rec_name = "name2"

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    name2 = fields.Char("Name",default="Clay Bricks")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    brick_temperature = fields.Char("Temperature",store=True)
    brick_humidity = fields.Char("Humidity",store="True")

    compressive_strength_unit = fields.Char(
    compute="_compute_units", store=False
    )
    water_absorption_unit = fields.Char(
        compute="_compute_units", store=False
    )


    def _compute_units(self):
        for rec in self:
            comp_param = self.env['lerm.parameter.master'].search([
                ('internal_id', '=', '97928829-9b1f-4091-aa7f-4b76f98eb47f')
            ], limit=1)
            water_param = self.env['lerm.parameter.master'].search([
                ('internal_id', '=', '1ddc7095-da2d-44a2-a70a-ab97216aee77')
            ], limit=1)

            rec.compressive_strength_unit = comp_param.unit.name if comp_param.unit else ""
            rec.water_absorption_unit = water_param.unit.name if water_param.unit else ""

    length_in_mm = fields.Float(string="Length in mm")
    width_in_mm = fields.Float(string="Width in mm")
    height_in_mm = fields.Float(string="Height in mm")



    notes_id = fields.One2many('mechanical.bricks.clay.notes', 'parent_id',string="Notes",
    default=lambda self: self._default_notes_lines()
)
    
    @api.model
    def _default_notes_lines(self):
        return [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The results stated in this report apply only to the tested sample(s) and are based on the conditions and parameters at the time of testing. ',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'This report is invalid without the official paper seal of Make Infracon.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'All test results are confidential and will not be disclosed to any third party without written consent of the client, except where required by law.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'This report must not be used, in whole or in part, for advertising or promotional purposes without written authorization. or used as evidence in a court of law.',
            }),
            (0, 0, {
                'sr_no': 'e',
                'notes': 'Any disputes shall be subject to jurisdiction of {Your Nashik/Location}Courts Only.',
            }),
        ]
    

  
    


    # Dimension 

    dimension_visible = fields.Boolean("Dimension Visible",compute="_compute_visible")
    dimension_name = fields.Char("Name",default="Dimension (mm)")

    dimension_lines = fields.One2many('bricks.dimension.line','parent_id',string="Parameter")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','457360db-e033-49ed-9c93-11e3bf87548d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','457360db-e033-49ed-9c93-11e3bf87548d')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','457360db-e033-49ed-9c93-11e3bf87548d')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','457360db-e033-49ed-9c93-11e3bf87548d')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c41c2f45-dc62-4d9b-a08f-607a05b87115')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c41c2f45-dc62-4d9b-a08f-607a05b87115')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c41c2f45-dc62-4d9b-a08f-607a05b87115')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','c41c2f45-dc62-4d9b-a08f-607a05b87115')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b88e1360-4bdf-4170-b3bc-913bdbc467f6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b88e1360-4bdf-4170-b3bc-913bdbc467f6')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b88e1360-4bdf-4170-b3bc-913bdbc467f6')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b88e1360-4bdf-4170-b3bc-913bdbc467f6')]).parameter_table
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


    




    # Compressive Strength

    compressive_strength_visible = fields.Boolean("Compressive Strengt Visible",compute="_compute_visible")
    compressive_strength_name = fields.Char("Name",default="Compressive Strength")


    compressive_strength_lines = fields.One2many('mechanical.bricks.clay.compressive.line','parent_id',string="Parameter")

    avrg_compressive_strength = fields.Float(string="Average Compressive Strength",compute="_compute_avrg_compressive_strength")

    comp_strength_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ('na', 'NA'),], string='Confirmity', default='fail',compute="_compute_comp_strength_conformity")

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','97928829-9b1f-4091-aa7f-4b76f98eb47f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','97928829-9b1f-4091-aa7f-4b76f98eb47f')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','97928829-9b1f-4091-aa7f-4b76f98eb47f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','97928829-9b1f-4091-aa7f-4b76f98eb47f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.avrg_compressive_strength - record.avrg_compressive_strength*mu_value
                    upper = record.avrg_compressive_strength + record.avrg_compressive_strength*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.comp_strength_nabl = 'pass'
                        break
                    else:
                        record.comp_strength_nabl = 'fail'

    

    

    @api.depends('compressive_strength_lines.comp_strength_1')
    def _compute_avrg_compressive_strength(self):
        for rec in self:
            comp_strength_1s = rec.compressive_strength_lines.filtered(lambda l: l.comp_strength_1 is not None)
            total = sum(line.comp_strength_1 for line in comp_strength_1s)
            count = len(comp_strength_1s)
            rec.avrg_compressive_strength = total / count if count > 0 else 0.0

      


    

    

    # Water Absorption

    water_absorbtion_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")
    wt_absorption_name = fields.Char("Name",default="Water Absorption")
    water_absorption_lines = fields.One2many('mechanical.bricks.clay.water.absorption.line','parent_id',string="Parameter")
   
    avrg_water_absorption = fields.Float(string="Average Water Absorption, %", compute="_compute_avrg_water_absorption")
    @api.depends('water_absorption_lines.water_absorption')
    def _compute_avrg_water_absorption(self):
        for rec in self:
            water_absorptions = rec.water_absorption_lines.filtered(lambda l: l.water_absorption is not None)
            total = sum(line.water_absorption for line in water_absorptions)
            count = len(water_absorptions)
            rec.avrg_water_absorption = total / count if count > 0 else 0.0

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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1ddc7095-da2d-44a2-a70a-ab97216aee77')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1ddc7095-da2d-44a2-a70a-ab97216aee77')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1ddc7095-da2d-44a2-a70a-ab97216aee77')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','1ddc7095-da2d-44a2-a70a-ab97216aee77')]).parameter_table
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


    # Efflorescence Visual Observation 
    efflorescence_visible = fields.Boolean("Efflorescence Visible",compute="_compute_visible")
    visual_observation_name_efflorescence = fields.Char("Name",default="Efflorescence")
    visual_observation_1 = fields.Selection([('light', 'Light'), ('nil', 'Nil'), ('slight', 'Slight'), ('moderate', 'Moderate'), ('heavy', 'Heavy'), ('serious', 'Serious')],string='Visual observation')
    


    
    

    

    confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Confirmity', default='fail')


    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
            record.compressive_strength_visible = False
            record.water_absorbtion_visible = False
            record.efflorescence_visible = False
            record.dimension_visible = False
            

            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
                if sample.internal_id == "97928829-9b1f-4091-aa7f-4b76f98eb47f":
                    record.compressive_strength_visible = True
                if sample.internal_id == "1ddc7095-da2d-44a2-a70a-ab97216aee77":
                    record.water_absorbtion_visible = True
                if sample.internal_id == "3e9d3877-e657-4409-8e7c-12c066f3cf26":
                    record.efflorescence_visible = True
                if sample.internal_id == "9f1689be-107d-4e30-9d3d-2aff6292264d":
                    record.dimension_visible = True 


     
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
            # Compressive Strength 
            if result.parameter.internal_id == '97928829-9b1f-4091-aa7f-4b76f98eb47f':
                result.result_char = round(self.avrg_compressive_strength,2)
                result.calculated = True
                if self.comp_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # water absorbtion
            if result.parameter.internal_id == '1ddc7095-da2d-44a2-a70a-ab97216aee77':
                result.result_char = round(self.avrg_water_absorption,2)
                result.calculated = True
                if self.water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            # Efflorence
            if result.parameter.internal_id == '3e9d3877-e657-4409-8e7c-12c066f3cf26':
                result.result_char = self.visual_observation_1
                result.calculated = True

            # Dimension
            if result.parameter.internal_id == '9f1689be-107d-4e30-9d3d-2aff6292264d':
                result.calculated = True

            # Length - Dimension
            if result.parameter.internal_id == '457360db-e033-49ed-9c93-11e3bf87548d':
                result.result_char = round(self.avrg_length,2)
                result.calculated = True
                if self.avrg_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Width - Dimension
            if result.parameter.internal_id == 'c41c2f45-dc62-4d9b-a08f-607a05b87115':
                result.result_char = round(self.avrg_width,2)
                result.calculated = True
                if self.avrg_width_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Height - Dimension
            if result.parameter.internal_id == 'b88e1360-4bdf-4170-b3bc-913bdbc467f6':
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

    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(MechanicalBricksBurntClay, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id
    



    def read(self, fields=None, load='_classic_read'):

        self._compute_sample_parameters()
        self._compute_visible()

        return super(MechanicalBricksBurntClay, self).read(fields=fields, load=load)
    
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
        record = self.env['mechanical.bricks.burnt.clay'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    notes_id = fields.One2many('mechanical.bricks.burnt.clay.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

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



class CompressiveLine(models.Model):
    _name = "mechanical.bricks.clay.compressive.line"
    parent_id = fields.Many2one('mechanical.bricks.burnt.clay',string="Parent Id")

    serial_no = fields.Integer(string="Sample No", readonly=True, copy=False, default=1)
    identification_mark = fields.Char(string="Identification Mark")
    length = fields.Float(string="Length mm")
    width = fields.Float(string="Width mm")
    height = fields.Float(string="Height mm")
    area = fields.Float(string="Area (mm²)", digits=(12,4),compute="_compute_area")
    load = fields.Float(string=" Load in, Kn", digits=(12,1))
    comp_strength_1 = fields.Float(string="Compressive strength MPa",compute="_compute_comp_strength_1")




    @api.depends('length', 'width')
    def _compute_area(self):
        for record in self:
            record.area = record.length * record.width

    @api.depends('load', 'area')
    def _compute_comp_strength_1(self):
        for record in self:
            if record.area != 0:
                record.comp_strength_1 = record.load / record.area * 1000
            else:
                record.comp_strength_1 = 0.0
   
   
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(CompressiveLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class WaterAbsorptionLine(models.Model):
    _name = "mechanical.bricks.clay.water.absorption.line"
    parent_id = fields.Many2one('mechanical.bricks.burnt.clay',string="Parent Id")

    serial_no = fields.Integer(string="Sample No", readonly=True, copy=False, default=1)
    identification_mark = fields.Char(string="Identification Mark")
    initial_wt = fields.Float(string="Initial wt after 24 hr emersion water")
    final_wt = fields.Float(string="Final wt after 24 hr oven")
    water_absorption = fields.Float(string="Water Absorption %", compute="_compute_water_absorption")

    @api.depends('initial_wt' , 'final_wt')
    def _compute_water_absorption(self):
        for record in self:
            if record.initial_wt != 0:
                record.water_absorption = (record.final_wt - record.initial_wt) / record.initial_wt * 100
            else:
                record.water_absorption = 0
    



   
    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(WaterAbsorptionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1


class BrickDimensionLine(models.Model):
    _name = "bricks.dimension.line"
    parent_id = fields.Many2one('mechanical.bricks.burnt.clay',string="Parent Id")

    serial_no = fields.Integer(string="Sample No", readonly=True, copy=False, default=1)
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

        return super(BrickDimensionLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1




class MechanicalBrickClaysNotes(models.Model):
    _name = "mechanical.bricks.clay.notes"

    parent_id = fields.Many2one('mechanical.bricks.burnt.clay', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
