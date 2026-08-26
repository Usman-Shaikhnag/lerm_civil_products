from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math


class MechanicalTilesNBML(models.Model):
    _name = "mechanical.tiles.nbml"
    _inherit = "lerm.eln"
    _rec_name = "name2"

    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    name2 = fields.Char("Name",default="Tiles")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    size_id = fields.Many2one('lerm.size.line',string="Size",compute="_compute_size_id",store=True)

    @api.depends('eln_ref')
    def _compute_size_id(self):
        if self.eln_ref:
            self.size_id = self.eln_ref.size_id.id

    temprature = fields.Float("Temperature (°C)", digits=(10,2))
    humidity = fields.Float("Humidity (%)", digits=(10,2))

    week_no = fields.Char("Week No")

    other_details = fields.Char("Other Details")

    condition = fields.Char("Condition")

    description_work = fields.Text("Description Of Work")

    notes_id = fields.One2many('tiles.nbml.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(MechanicalTilesNBML, self).default_get(fields)

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



    dimension_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")
    dimension_name = fields.Char("Name",default="Dimension")


    length_in_mm = fields.Float(string="Length in mm")
    width_in_mm = fields.Float(string="Width in mm")
    height_in_mm = fields.Float(string="Height in mm")


    length_in_mm_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_length_in_mm_conformity")

    length_in_mm_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_length_in_mm_nabl")


    @api.depends('length_in_mm','eln_ref','grade')
    def _compute_length_in_mm_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.length_in_mm_conformity = 'na'
                continue
            record.length_in_mm_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','457360db-e033-49ed-9c93-113456783219')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','457360db-e033-49ed-9c93-113456783219')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.length_in_mm - record.length_in_mm*mu_value
                    upper = record.length_in_mm + record.length_in_mm*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.length_in_mm_conformity = 'pass'
                        break
                    else:
                        record.length_in_mm_conformity = 'fail'

    @api.depends('length_in_mm','eln_ref','grade')
    def _compute_length_in_mm_nabl(self):
        
        for record in self:
            
            record.length_in_mm_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','457360db-e033-49ed-9c93-113456783219')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','457360db-e033-49ed-9c93-113456783219')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.length_in_mm - record.length_in_mm*mu_value
            upper = record.length_in_mm + record.length_in_mm*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.length_in_mm_nabl = 'pass'
                break
            else:
                record.length_in_mm_nabl = 'fail'


    width_in_mm_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Width Conformity',compute="_compute_width_in_mm_conformity")

    width_in_mm_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='Width NABL', default='fail',compute="_compute_width_in_mm_nabl")


    @api.depends('width_in_mm','eln_ref','grade')
    def _compute_width_in_mm_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.width_in_mm_conformity = 'na'
                continue
            record.width_in_mm_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23456213-dc62-4d9b-a08f-607a05675432')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23456213-dc62-4d9b-a08f-607a05675432')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.width_in_mm - record.width_in_mm*mu_value
                    upper = record.width_in_mm + record.width_in_mm*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.width_in_mm_conformity = 'pass'
                        break
                    else:
                        record.width_in_mm_conformity = 'fail'

    @api.depends('width_in_mm','eln_ref','grade')
    def _compute_width_in_mm_nabl(self):
        
        for record in self:
            
            record.width_in_mm_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23456213-dc62-4d9b-a08f-607a05675432')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','23456213-dc62-4d9b-a08f-607a05675432')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.width_in_mm - record.width_in_mm*mu_value
            upper = record.width_in_mm + record.width_in_mm*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.width_in_mm_nabl = 'pass'
                break
            else:
                record.width_in_mm_nabl = 'fail'

    height_in_mm_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Height Conformity',compute="_compute_height_in_mm_conformity")

    height_in_mm_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='Height NABL', default='fail',compute="_compute_height_in_mm_nabl")


    @api.depends('height_in_mm','eln_ref','grade')
    def _compute_height_in_mm_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.height_in_mm_conformity = 'na'
                continue
            record.height_in_mm_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','k454321lk-4bdf-4170-b3bc-914567321345')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','k454321lk-4bdf-4170-b3bc-914567321345')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.height_in_mm - record.height_in_mm*mu_value
                    upper = record.height_in_mm + record.height_in_mm*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.height_in_mm_conformity = 'pass'
                        break
                    else:
                        record.height_in_mm_conformity = 'fail'

    @api.depends('height_in_mm','eln_ref','grade')
    def _compute_height_in_mm_nabl(self):
        
        for record in self:
            
            record.height_in_mm_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','k454321lk-4bdf-4170-b3bc-914567321345')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','k454321lk-4bdf-4170-b3bc-914567321345')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.height_in_mm - record.height_in_mm*mu_value
            upper = record.height_in_mm + record.height_in_mm*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.height_in_mm_nabl = 'pass'
                break
            else:
                record.height_in_mm_nabl = 'fail'


      #-4--------------  Water Absorption

    water_absorbtion_visible = fields.Boolean("Water Absorption Visible",compute="_compute_visible")
    wt_absorption_name = fields.Char("Name",default="Water Absorption")
    water_absorption_lines = fields.One2many('mechanical.tiles.nbml.water.absorption.line','parent_id',string="Parameter")
   
    avrg_water_absorption = fields.Float(string="Average Water Absorption, %", compute="_compute_avrg_water_absorption")

    @api.depends('water_absorption_lines.water_absorption')
    def _compute_avrg_water_absorption(self):
        for record in self:
            lines = record.water_absorption_lines
            if lines:
                record.avrg_water_absorption = sum(lines.mapped('water_absorption')) / len(lines)
            else:
                record.avrg_water_absorption = 0

    avrg_water_absorption_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'NA'),
    ], string='Conformity',compute="_compute_avrg_water_absorption_conformity")

    avrg_water_absorption_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'Non-NABL'),
    ], string='NABL', default='fail',compute="_compute_avrg_water_absorption_nabl")


    @api.depends('avrg_water_absorption','eln_ref','grade')
    def _compute_avrg_water_absorption_conformity(self):
        for record in self:
            if not record.eln_ref or not record.eln_ref.conformity:
                record.avrg_water_absorption_conformity = 'na'
                continue
            record.avrg_water_absorption_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','09543405-ed58-4374-bda7-28756432985')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','09543405-ed58-4374-bda7-28756432985')]).parameter_table
            mu_value = line.mu_value
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    # mu_value = line.mu_value
                    lower = record.avrg_water_absorption - record.avrg_water_absorption*mu_value
                    upper = record.avrg_water_absorption + record.avrg_water_absorption*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.avrg_water_absorption_conformity = 'pass'
                        break
                    else:
                        record.avrg_water_absorption_conformity = 'fail'

    @api.depends('avrg_water_absorption','eln_ref','grade')
    def _compute_avrg_water_absorption_nabl(self):
        
        for record in self:
            
            record.avrg_water_absorption_nabl = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','09543405-ed58-4374-bda7-28756432985')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','09543405-ed58-4374-bda7-28756432985')]).parameter_table
            
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.avrg_water_absorption - record.avrg_water_absorption*mu_value
            upper = record.avrg_water_absorption + record.avrg_water_absorption*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.avrg_water_absorption_nabl = 'pass'
                break
            else:
                record.avrg_water_absorption_nabl = 'fail'










    ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:
    
            record.dimension_visible = False

            record.water_absorbtion_visible = False
            

            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)
               
                if sample.internal_id == "p45329be-107d-4e30-9d3d-2a9054325678":
                    record.dimension_visible = True 

                if sample.internal_id == "09543405-ed58-4374-bda7-28756432985":
                    record.water_absorbtion_visible = True 

                

                
     
    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
           

            
            if result.parameter.internal_id == '457360db-e033-49ed-9c93-113456783219':
                result.result_char = round(self.length_in_mm,2)
                result.calculated = True
                if self.length_in_mm_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

           

            if result.parameter.internal_id == '23456213-dc62-4d9b-a08f-607a05675432':
                result.result_char = round(self.width_in_mm,2)
                result.calculated = True
                if self.width_in_mm_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

           
            if result.parameter.internal_id == 'k454321lk-4bdf-4170-b3bc-914567321345':
                result.result_char = round(self.height_in_mm,2)
                result.calculated = True
                if self.height_in_mm_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == '09543405-ed58-4374-bda7-28756432985':
                result.result_char = round(self.avrg_water_absorption,2)
                result.calculated = True
                if self.avrg_water_absorption_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue 

            if result.parameter.internal_id == 'p45329be-107d-4e30-9d3d-2a9054325678':
                # result.result_char = self.avg_specific_gravity
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
        record = super(MechanicalTilesNBML, self).create(vals)
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
        record = self.env['mechanical.tiles.nbml'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


class WaterAbsorptionLine(models.Model):
    _name = "mechanical.tiles.nbml.water.absorption.line"
    parent_id = fields.Many2one('mechanical.tiles.nbml',string="Parent Id")

    serial_no = fields.Integer(string="sample", readonly=True, copy=False, default=1)
    mass_of_saturated = fields.Float(string="Mass of saturated Specimen in gm-M1")
    mass_of_oven = fields.Float(string="Mass of oven dried Specimen in gm-M2")
    water_absorption = fields.Float(string="Water Absorption (%)=(M1-M2)/M2",compute="_compute_water_absorption",digits=(12,2))


    @api.depends('mass_of_saturated', 'mass_of_oven')
    def _compute_water_absorption(self):
        for record in self:
            if record.mass_of_oven:  # Avoid division by zero
                record.water_absorption = ((record.mass_of_saturated - record.mass_of_oven) / record.mass_of_oven) * 100
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



class TilesNBMLNotes(models.Model):
    _name = "tiles.nbml.notes"

    parent_id = fields.Many2one('mechanical.tiles.nbml',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
