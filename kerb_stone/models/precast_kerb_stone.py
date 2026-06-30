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

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
       
    


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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3cecadf0-b363-4bc8-86fc-97f4430d6ffd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3cecadf0-b363-4bc8-86fc-97f4430d6ffd')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3cecadf0-b363-4bc8-86fc-97f4430d6ffd')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','3cecadf0-b363-4bc8-86fc-97f4430d6ffd')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30c89fe6-da35-4545-94e5-dc2afd559f00')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30c89fe6-da35-4545-94e5-dc2afd559f00')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30c89fe6-da35-4545-94e5-dc2afd559f00')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','30c89fe6-da35-4545-94e5-dc2afd559f00')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0ba0f21f-2f41-4b8c-b166-84ba44a17aac')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0ba0f21f-2f41-4b8c-b166-84ba44a17aac')]).parameter_table
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
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0ba0f21f-2f41-4b8c-b166-84ba44a17aac')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','0ba0f21f-2f41-4b8c-b166-84ba44a17aac')]).parameter_table
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



# 


    transverse_name = fields.Char(default="Transverse Strength")
    transverse_visible = fields.Boolean(compute="_compute_visible")

    transverse_table = fields.One2many('mech.precast.transverse.line','parent_id')
    

    # Water Absorbtion
    water_absorbtion_name = fields.Char(default="Water Absorbtion")
    water_absorbtion_visible = fields.Boolean(compute="_compute_visible")

    water_absorbtion_table = fields.One2many('mech.precast.water.absorbtion.line','parent_id')
    

    

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

            record.transverse_visible = False
            record.water_absorbtion_visible  = False  
            

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)

                if sample.internal_id == 'klrt1230t-eeb4-4e16-a7fc-7560838410lo':
                    record.dimension_visible = True


                if sample.internal_id == '0b48abe6-07a4-4345-bcc1-30ff6e4830af':
                    record.transverse_visible = True
                if sample.internal_id == 'f913fc79-eeb4-4e16-a7fc-75608384d9b0':
                    record.water_absorbtion_visible = True
                

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
          
            
            if result.parameter.internal_id == '0b48abe6-07a4-4345-bcc1-30ff6e4830af':
                # result.result_char = round(self.average_density,2)
                result.calculated = True
                # if self.average_density_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue

            if result.parameter.internal_id == 'f913fc79-eeb4-4e16-a7fc-75608384d9b0':
                # result.result_char = round(self.average_density,2)
                result.calculated = True
                # if self.average_density_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
                # continue




            # Dimension
            if result.parameter.internal_id == 'klrt1230t-eeb4-4e16-a7fc-7560838410lo':
                result.calculated = True

            # Length - Dimension
            if result.parameter.internal_id == '3cecadf0-b363-4bc8-86fc-97f4430d6ffd':
                result.result_char = round(self.avrg_length,2)
                result.calculated = True
                if self.avrg_length_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Width - Dimension
            if result.parameter.internal_id == '30c89fe6-da35-4545-94e5-dc2afd559f00':
                result.result_char = round(self.avrg_width,2)
                result.calculated = True
                if self.avrg_width_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue

            # Height - Dimension
            if result.parameter.internal_id == '0ba0f21f-2f41-4b8c-b166-84ba44a17aac':
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

    serial_no = fields.Integer(string="Kerb Stone ID", readonly=True, copy=False, default=1)
    lengthh = fields.Float(string="Length (in mm)")
    width = fields.Float(string="Width (in mm)")
    height = fields.Float(string="Height (in mm)")

    remarks = fields.Char(string="Remarks")
    
    
   
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
   

class PrecastTransverseLine(models.Model):
    _name = "mech.precast.transverse.line"
    parent_id = fields.Many2one('mechanical.precast.kerb', string="Parent Id")

    trial_no = fields.Integer('Trial no')
    required_load = fields.Float('Required Load in (Ton)')
    observed_test_result = fields.Char('Observed Test Result')
    protocol = fields.Char('Protocol')
    requirement = fields.Char('Requirement')


class PrecastWaterAbsorbtionLine(models.Model):
    _name = "mech.precast.water.absorbtion.line"
    parent_id = fields.Many2one('mechanical.precast.kerb', string="Parent Id")

    dry_wt_oven = fields.Float('Dry Weight (after 24 hour in oven)')
    wt_10_min = fields.Float('Weight (wt. after 10 minutes emersion in water)')
    wt_24_hr = fields.Float('Weight (wt. after 24 hour emersion in water)')
    initial_water_absorbtion = fields.Float("Initial Water Absorption, %")
    final_water_absorbtion = fields.Float("Final Water Absorption, %")
    protocol = fields.Char('Protocol')





    

    
class PrecastKerbMechanicalNotes(models.Model):
    _name = "mechanical.precast.kerb.notes"

    parent_id = fields.Many2one('mechanical.precast.kerb', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
