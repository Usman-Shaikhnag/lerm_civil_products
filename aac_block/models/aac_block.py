from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class AacBlockMechanical(models.Model):
    _name = "mechanical.aac.block"
    _inherit = "lerm.eln"
    _description = 'mechanical.aac.block'
    _rec_name = "name"



    name = fields.Char("Name",default="AAC Block")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    temprature = fields.Float("Temperature (°C)", digits=(10,2))
    humidity = fields.Float("Humidity (%)", digits=(10,2))

    grade_type = fields.Selection(
        [
            ('grade1', 'GRADE 1'),
            ('grade2', 'GRADE 2'),
        ],
        string="Grade Type",
        
    )

    size = fields.Char("Size")

    other_details = fields.Char("Other Details")

    condition = fields.Char("Condition")

    description_work = fields.Text("Description Of Work")

    

    def prefill_data(self):
        # import wdb; wdb.set_trace()
        return {
            'name': 'Prefill Data',
            'type': 'ir.actions.act_window',
            'res_model': 'mechanical.aac.block.prefill.data',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.eln_ref.sample_id.material_id.id,
                'exclude_sample_id': self.eln_ref.sample_id.id,
                },
        }


    

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
        record = self.env['mechanical.aac.block'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.dimension_visible = False
            record.density_visible = False
            record.drying_shrinkage_visible = False
            record.compressive_strength_visible = False
            record.thermal_conductivity_visible = False

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '12478fdr3w-ac79-4102-aeda-622dc0f973f6':
                    record.dimension_visible = True
               
                if sample.internal_id == '254879sw-4ef4-4e51-abeb-57dd2abe29a4':
                    record.density_visible = True
                if sample.internal_id == '214578ews-b1a2-4dac-b8cb-e077770af52f':
                    record.drying_shrinkage_visible = True
                if sample.internal_id == '21457896dfe-cb61-45db-91c5-0167b27a9ab5':
                    record.compressive_strength_visible = True
                if sample.internal_id == '098765y63-b1a2-4dac-b8cb-e077770af7865':
                    record.thermal_conductivity_visible = True

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
            # Dimension
            if result.parameter.internal_id == '12478fdr3w-ac79-4102-aeda-622dc0f973f6':
                # result.result_char = round(self.aggregate_elongation,2)
                result.calculated = True
                # if self.aggregate_combine_conformity == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue

            


             # Density
            if result.parameter.internal_id == '254879sw-4ef4-4e51-abeb-57dd2abe29a4':
                result.result_char = round(self.average_density,2)
                result.calculated = True
                if self.density_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


             # Drying Shrinkage
            if result.parameter.internal_id == '214578ews-b1a2-4dac-b8cb-e077770af52f':
                result.result_char = round(self.average_drying_shrinkage,2)
                result.calculated = True
                if self.drying_shrinkage_aac_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


             # Compressive Strength
            if result.parameter.internal_id == '21457896dfe-cb61-45db-91c5-0167b27a9ab5':
                result.result_char = round(self.average_compressive_strength,2)
                result.calculated = True
                if self.compressive_strength_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '36578952-e033-49ed-9c93-11e320145875':
                result.result_char = round(self.average_length,2)
                result.calculated = True
                if self.average_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '32145832-dc62-4d9b-a08f-607a23145687':
                result.result_char = round(self.average_width,2)
                result.calculated = True
                if self.average_width_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '33311144-4bdf-4170-b3bc-913bdbc467f6tt':
                result.result_char = round(self.average_height,2)
                result.calculated = True
                if self.average_height_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            if result.parameter.internal_id == '098765y63-b1a2-4dac-b8cb-e077770af7865':
                result.result_char = round(self.average_thermal_conductivity,2)
                result.calculated = True
                if self.thermal_conductivity_aac_nabl == 'pass':
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
        record = super(AacBlockMechanical, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

  
    def get_all_fields(self):
        record = self.env['mechanical.aac.block'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

 

    



    # remark

    notes_id = fields.One2many('aac.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(AacBlockMechanical, self).default_get(fields)

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






    # Dimension
    dimension_name = fields.Char(default="Dimension")
    dimension_visible = fields.Boolean(compute="_compute_visible")
    

    dimension_table = fields.One2many('mech.aac.dimension.line','parent_id')
    average_length = fields.Float('Average Length',compute="_compute_average_length")
    length_grade1 = fields.Char("Length Specification",default="±5 mm")
    # length_grade2 = fields.Char("Length Specification Grade - 2")

    average_width = fields.Float('Average Width',compute="_compute_average_width")
    width_grade1 = fields.Char("Width Specification",default="±3 mm")
    # width_grade2 = fields.Char("Width Specification Grade - 2")

    average_height = fields.Float('Average Height',compute="_compute_average_height")

    height_grade1 = fields.Char("Height Specification",default="±3 mm")
    # height_grade2 = fields.Char("Height Specification Grade - 2")

    average_length_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Length Conformity',compute="_compute_average_length_conformity")

    average_length_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='Length NABL', default='fail',compute="_compute_average_length_nabl")


    @api.depends('average_length','eln_ref','grade')
    def _compute_average_length_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_length_conformity = 'na'
                continue
            record.average_length_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36578952-e033-49ed-9c93-11e320145875')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36578952-e033-49ed-9c93-11e320145875')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.average_length - record.average_length*mu_value
                    upper = record.average_length + record.average_length*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_length_conformity = 'pass'
                        break
                    else:
                        record.average_length_conformity = 'fail'

    @api.depends('average_length','eln_ref','grade')
    def _compute_average_length_nabl(self):
        
        for record in self:
            
            record.average_length_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36578952-e033-49ed-9c93-11e320145875')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','36578952-e033-49ed-9c93-11e320145875')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_length - record.average_length*mu_value
            upper = record.average_length + record.average_length*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_length_nabl = 'pass'
                break
            else:
                record.average_length_nabl = 'fail'


    average_width_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_average_width_conformity")

    average_width_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_average_width_nabl")


    @api.depends('average_width','eln_ref','grade')
    def _compute_average_width_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_width_conformity = 'na'
                continue
            record.average_width_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32145832-dc62-4d9b-a08f-607a23145687')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32145832-dc62-4d9b-a08f-607a23145687')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.average_width - record.average_width*mu_value
                    upper = record.average_width + record.average_width*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_width_conformity = 'pass'
                        break
                    else:
                        record.average_width_conformity = 'fail'

    @api.depends('average_width','eln_ref','grade')
    def _compute_average_width_nabl(self):
        
        for record in self:
            
            record.average_width_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32145832-dc62-4d9b-a08f-607a23145687')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','32145832-dc62-4d9b-a08f-607a23145687')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_width - record.average_width*mu_value
            upper = record.average_width + record.average_width*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_width_nabl = 'pass'
                break
            else:
                record.average_width_nabl = 'fail'

    average_height_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_average_height_conformity")

    average_height_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_average_height_nabl")


    @api.depends('average_height','eln_ref','grade')
    def _compute_average_height_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.average_height_conformity = 'na'
                continue
            record.average_height_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','33311144-4bdf-4170-b3bc-913bdbc467f6tt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','33311144-4bdf-4170-b3bc-913bdbc467f6tt')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.average_height - record.average_height*mu_value
                    upper = record.average_height + record.average_height*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.average_height_conformity = 'pass'
                        break
                    else:
                        record.average_height_conformity = 'fail'

    @api.depends('average_height','eln_ref','grade')
    def _compute_average_height_nabl(self):
        
        for record in self:
            
            record.average_height_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','33311144-4bdf-4170-b3bc-913bdbc467f6tt')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','33311144-4bdf-4170-b3bc-913bdbc467f6tt')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_height - record.average_height*mu_value
            upper = record.average_height + record.average_height*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.average_height_nabl = 'pass'
                break
            else:
                record.average_height_nabl = 'fail'




    @api.depends('dimension_table.length')
    def _compute_average_length(self):
        for record in self:
            try:
                record.average_length = round(sum(record.dimension_table.mapped('length')) / len(
                    record.dimension_table),2)
            except:
                record.average_length = 0

    
    @api.depends('dimension_table.width')
    def _compute_average_width(self):
        for record in self:
            try:
                record.average_width = round(sum(record.dimension_table.mapped('width')) / len(
                    record.dimension_table),2)
            except:
                record.average_width = 0


    @api.depends('dimension_table.height')
    def _compute_average_height(self):
        for record in self:
            try:
                record.average_height = round(sum(record.dimension_table.mapped('height')) / len(
                    record.dimension_table),2)
            except:
                record.average_height = 0

    # Moisture Content
    # moisture_name = fields.Char(default="Moisture Content")
    # moisture_visible = fields.Boolean(compute="_compute_visible")
    # moisture_grade1 = fields.Char("Specification Grade - 1")
    # moisture_grade2 = fields.Char("Specification Grade - 2")

    # moisture_content_table = fields.One2many('mech.aac.moisture.line','parent_id')
    # average_moisture_content = fields.Float("Average Moisture Content %",compute="_compute_average_moisture_content")
    # moisture_confirmity = fields.Selection([
    #     ('pass', 'Pass'),
    #     ('fail', 'Fail'),
    #     ('na', 'NA'),
    # ], string='Confirmity', default='fail',compute="_compute_moisture_confirmity")
    # moisture_nabl = fields.Selection([
    #     ('pass', 'NABL'),
    #     ('fail', 'NON NABL'),
    # ], string='NABL', compute="_compute_moisture_nabl")


    # @api.depends('average_moisture_content','eln_ref','grade')
    # def _compute_moisture_confirmity(self):
    #     for record in self:

    #         if not record.eln_ref or not record.eln_ref.conformity:
    #             record.moisture_confirmity = 'na'
    #             continue

    #         record.moisture_confirmity = 'fail'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6478fde2-8097-4275-b80f-48ebdbcfe244')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6478fde2-8097-4275-b80f-48ebdbcfe244')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 req_min = material.req_min
    #                 req_max = material.req_max
    #                 mu_value = line.mu_value
    #                 lower = record.average_moisture_content - record.average_moisture_content*mu_value
    #                 upper = record.average_moisture_content + record.average_moisture_content*mu_value
    #                 if lower >= req_min and upper <= req_max :
    #                     record.moisture_confirmity = 'pass'
    #                     break
    #                 else:
    #                     record.moisture_confirmity = 'fail'

    # @api.depends('average_moisture_content','eln_ref','grade')
    # def _compute_moisture_nabl(self):
        
    #     for record in self:
    #         record.moisture_nabl = 'pass'
    #         line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6478fde2-8097-4275-b80f-48ebdbcfe244')])
    #         materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6478fde2-8097-4275-b80f-48ebdbcfe244')]).parameter_table
    #         for material in materials:
    #             if material.grade.id == record.grade.id:
    #                 lab_min = line.lab_min_value
    #                 lab_max = line.lab_max_value
    #                 mu_value = line.mu_value
                    
    #                 lower = record.average_moisture_content - record.average_moisture_content*mu_value
    #                 upper = record.average_moisture_content + record.average_moisture_content*mu_value
    #                 if lower >= lab_min and upper <= lab_max:
    #                     record.moisture_nabl = 'pass'
    #                     break
    #                 else:
    #                     record.moisture_nabl = 'fail'

    # @api.depends('moisture_content_table.moisture_content')
    # def _compute_average_moisture_content(self):
    #     for record in self:
    #         try:
    #             record.average_moisture_content = round(sum(record.moisture_content_table.mapped('moisture_content')) / len(
    #                 record.moisture_content_table),2)
    #         except:
    #             record.average_moisture_content = 0

    # Density 
    density_name = fields.Char(default="Density")
    density_visible = fields.Boolean(compute="_compute_visible")

    density_grade1 = fields.Char("Specification")


    density_table = fields.One2many('mech.aac.density.line','parent_id')
    average_density = fields.Integer("Average Density Kg/cm3",compute="_compute_average_density")

    density_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Confirmity', compute="_compute_density_confirmity")
    density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', compute="_compute_density_nabl")


    @api.depends('average_density','eln_ref','grade')
    def _compute_density_confirmity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.density_confirmity = 'na'
                continue


            record.density_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_density - record.average_density*mu_value
                    upper = record.average_density + record.average_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.density_confirmity = 'pass'
                        break
                    else:
                        record.density_confirmity = 'fail'

    @api.depends('average_density','eln_ref','grade')
    def _compute_density_nabl(self):
        
        for record in self:
            record.density_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','254879sw-4ef4-4e51-abeb-57dd2abe29a4')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_density - record.average_density*mu_value
                    upper = record.average_density + record.average_density*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.density_nabl = 'pass'
                        break
                    else:
                        record.density_nabl = 'fail'

    @api.depends('density_table.density')
    def _compute_average_density(self):
        for record in self:
            try:
                record.average_density = round(sum(record.density_table.mapped('density')) / len(
                    record.density_table),1)
            except:
                record.average_density = 0

    # Drying Shrinkage
    drying_shrinkage_name = fields.Char(default="Drying Shrinkage")
    drying_shrinkage_visible = fields.Boolean(compute="_compute_visible")

    average_drying_shrinkage = fields.Float("Average Drying Shrinkage",digits=(12,3))
    drying_grade1 = fields.Char("Specification")
    drying_shrinkage_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Confirmity', compute="_compute_drying_shrinkage_confirmity")
    

    drying_shrinkage_aac_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', compute="_compute_drying_shrinkage_nabl")


    @api.depends('average_drying_shrinkage','eln_ref','grade')
    def _compute_drying_shrinkage_confirmity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.drying_shrinkage_confirmity = 'na'
                continue

            record.drying_shrinkage_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_drying_shrinkage - record.average_drying_shrinkage*mu_value
                    upper = record.average_drying_shrinkage + record.average_drying_shrinkage*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.drying_shrinkage_confirmity = 'pass'
                        break
                    else:
                        record.drying_shrinkage_confirmity = 'fail'


    @api.depends('average_drying_shrinkage','eln_ref','grade')
    def _compute_drying_shrinkage_nabl(self):
        
        for record in self:
            record.drying_shrinkage_aac_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','214578ews-b1a2-4dac-b8cb-e077770af52f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_drying_shrinkage - record.average_drying_shrinkage*mu_value
                    upper = record.average_drying_shrinkage + record.average_drying_shrinkage*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.drying_shrinkage_aac_nabl = 'pass'
                        break
                    else:
                        record.drying_shrinkage_aac_nabl = 'fail'



    #Thermal Conductivity
    thermal_conductivity_name = fields.Char(default="Thermal Conductivity")
    thermal_conductivity_visible = fields.Boolean(compute="_compute_visible")

    average_thermal_conductivity = fields.Float("Thermal Conductivity",digits=(12,2))
    thermal_conductivity_grade1 = fields.Char("Specification")
    thermal_conductivity_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Confirmity', compute="_compute_thermal_conductivity_confirmity")
    

    thermal_conductivity_aac_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', compute="_compute_thermal_conductivity_nabl")


    @api.depends('average_thermal_conductivity','eln_ref','grade')
    def _compute_thermal_conductivity_confirmity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.thermal_conductivity_confirmity = 'na'
                continue

            record.thermal_conductivity_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','098765y63-b1a2-4dac-b8cb-e077770af7865')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','098765y63-b1a2-4dac-b8cb-e077770af7865')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_thermal_conductivity - record.average_thermal_conductivity*mu_value
                    upper = record.average_thermal_conductivity + record.average_thermal_conductivity*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.thermal_conductivity_confirmity = 'pass'
                        break
                    else:
                        record.thermal_conductivity_confirmity = 'fail'


    @api.depends('average_thermal_conductivity','eln_ref','grade')
    def _compute_thermal_conductivity_nabl(self):
        
        for record in self:
            record.thermal_conductivity_aac_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','098765y63-b1a2-4dac-b8cb-e077770af7865')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','098765y63-b1a2-4dac-b8cb-e077770af7865')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_thermal_conductivity - record.average_thermal_conductivity*mu_value
                    upper = record.average_thermal_conductivity + record.average_thermal_conductivity*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.thermal_conductivity_aac_nabl = 'pass'
                        break
                    else:
                        record.thermal_conductivity_aac_nabl = 'fail'

    


    # Compressive Strength
    compressive_strength_name = fields.Char(default="Compressive Strength")
    compressive_strength_visible = fields.Boolean(compute="_compute_visible")

    compressive_strength_table = fields.One2many('mech.aac.compressive.strength.line','parent_id')
    average_compressive_strength = fields.Float("Average Compressive Strength",compute="_compute_average_compressive_strength")
    compressive_grade1 = fields.Char("Specification")
    compressive_strength_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Confirmity', compute="_compute_compressive_strength_confirmity")
    compressive_strength_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', default='fail',compute="_compute_compressive_strength_nabl")


    @api.depends('average_compressive_strength','eln_ref','grade')
    def _compute_compressive_strength_confirmity(self):
        for record in self:

            if not record.eln_ref or not record.eln_ref.conformity:
                record.compressive_strength_confirmity = 'na'
                continue

            record.compressive_strength_confirmity = 'fail'   
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896dfe-cb61-45db-91c5-0167b27a9ab5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896dfe-cb61-45db-91c5-0167b27a9ab5')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_compressive_strength - record.average_compressive_strength*mu_value
                    upper = record.average_compressive_strength + record.average_compressive_strength*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.compressive_strength_confirmity = 'pass'
                        break
                    else:
                        record.compressive_strength_confirmity = 'fail'

    @api.depends('average_compressive_strength','eln_ref','grade')
    def _compute_compressive_strength_nabl(self):
        
        for record in self:
            record.compressive_strength_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896dfe-cb61-45db-91c5-0167b27a9ab5')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','21457896dfe-cb61-45db-91c5-0167b27a9ab5')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_compressive_strength - record.average_compressive_strength*mu_value
                    upper = record.average_compressive_strength + record.average_compressive_strength*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.compressive_strength_nabl = 'pass'
                        break
                    else:
                        record.compressive_strength_nabl = 'fail'

    
    @api.depends('compressive_strength_table.compressive_strength')
    def _compute_average_compressive_strength(self):
        for record in self:
            try:
                average_compressive_strength = sum(record.compressive_strength_table.mapped('compressive_strength')) / len(
                record.compressive_strength_table)
                record.average_compressive_strength = round(average_compressive_strength,2)
            except:
                record.average_compressive_strength = 0

class AacDimensionLine(models.Model):
    _name = "mech.aac.dimension.line"
    parent_id = fields.Many2one('mechanical.aac.block', string="Parent Id")

    length = fields.Float('Length')
    width = fields.Float('Width')
    height = fields.Float('Height')


# class AacMoistureLine(models.Model):
#     _name = "mech.aac.moisture.line"
#     parent_id = fields.Many2one('mechanical.aac.block', string="Parent Id")

#     wt_sample = fields.Float('Weight of sample W1 in gm')
#     oven_wt = fields.Float('Oven dry Weight of sample W in gm')
#     moisture_content = fields.Float('Moisture Content %',compute="_compute_moisture_content")

#     @api.depends('wt_sample','oven_wt')
#     def _compute_moisture_content(self):
#         for record in self:
#             if record.oven_wt != 0:
#                 moisture = (record.wt_sample - record.oven_wt)/record.oven_wt *100
#                 record.moisture_content = round(moisture,2)
#             else:
#                 record.moisture_content = 0

class AacDensityLine(models.Model):
    _name = "mech.aac.density.line"
    parent_id = fields.Many2one('mechanical.aac.block', string="Parent Id")

    length = fields.Float(string='Length', digits=(16, 2), )
    width = fields.Float(string='Width', digits=(16, 2))
    height = fields.Float(string='Height', digits=(16, 2))
    volume = fields.Float(string="Volume of Sample (V) cm3", compute="_compute_volume", digits=(16, 2))
    initial_wt = fields.Float(string='Initial Weight (W1) gm', digits=(16, 2))
    dry_wt = fields.Float(string='Oven Dry Weight (W2) gm', digits=(16, 2))
    density = fields.Float(string='Density of Sample Kg/cm3', compute="_compute_density", digits=(16, 3))
    moisture = fields.Float(string='Moisture Content (%) F = ((W1-W2)/W2) *100', compute="_compute_moisture",digits=(16, 2))

    

    @api.depends('length', 'width', 'height')
    def _compute_volume(self):
        for record in self:
            record.volume = record.length * record.width * record.height


    @api.depends('dry_wt', 'volume')
    def _compute_density(self):
        for record in self:
            if record.volume:
                record.density = (record.dry_wt / record.volume)*1000
            else:
                record.density = 0.0


    @api.depends('initial_wt', 'dry_wt')
    def _compute_moisture(self):
        for record in self:
            if record.dry_wt:
                record.moisture = (
                    (record.initial_wt - record.dry_wt) / record.dry_wt
                ) * 100
            else:
                record.moisture = 0.0
        



class AacCompressiveStrengthLine(models.Model):
    _name = "mech.aac.compressive.strength.line"
    parent_id = fields.Many2one('mechanical.aac.block', string="Parent Id")


    length = fields.Float(string="Length (mm)")
    breadth = fields.Float(string="Width (mm)")
    height = fields.Float(string="Height (mm)")
    area = fields.Float(string="Cross Sectional Area (mm2), A", compute="_compute_area")

    @api.depends('length', 'breadth')
    def _compute_area(self):
        for rec in self:
            rec.area = rec.length * rec.breadth

    aac_load = fields.Float('Load (p) kN')
    compressive_strength = fields.Float('Compressive Strength (N/mm2)  σcu = L/A ',compute="_compute_compressive_strength",digits=(12,2))
    kg_cm = fields.Float('kg/cm2',compute="_compute_kg_cm",digits=(12,5))

    @api.depends('aac_load')
    def _compute_compressive_strength(self):
        for record in self:
            record.compressive_strength = record.aac_load / 22.5


    @api.depends('compressive_strength')
    def _compute_kg_cm(self):
        for record in self:
            record.kg_cm = record.compressive_strength * 10.1972


    


class aacNotes(models.Model):
    _name = "aac.notes"

    parent_id = fields.Many2one('mechanical.aac.block',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")



