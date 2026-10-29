from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class ConcreteCuringCompound(models.Model):
    _name = "mechanical.curing.compound"
    _inherit = "lerm.eln"
    _description = 'mechanical.curing.compound'
    _rec_name = "name"



    name = fields.Char("Name",default="Concrete Curing Compound")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result', string="Parameter")

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    tests = fields.Many2many("mechanical.gypsum.test",string="Tests")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    @api.depends("eln_ref")
    def _compute_size_id(self):
        for record in self:
            print("Size iD",record.eln_ref.size_id)
            record.size_id = record.eln_ref.size_id.id


    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

        
    def get_all_fields(self):
        record = self.env['mechanical.curing.compound'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values


    @api.depends('eln_ref','sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.density_test_data_visible = False
            record.drying_time_test_data_visible  = False
            record.water_retention_test_data_visible = False


            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '5a57bf7a-5316-40a0-a702-e030cbd40479':
                    record.density_test_data_visible = True
                if sample.internal_id == 'b595d12d-af10-4955-9c17-0f412c260d8f':
                     record.drying_time_test_data_visible = True
                if sample.internal_id == '6487f7d1-9f5a-415d-adca-ce9e83d80b0e':
                    record.water_retention_test_data_visible = True
                

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            
            # density test data
            if result.parameter.internal_id == '5a57bf7a-5316-40a0-a702-e030cbd40479':
                            result.result_char = round(self.average_density,3)
                            result.calculated = True
                            if self.density_nabl == 'pass':
                                result.nabl_status = 'nabl'
                            else:
                                result.nabl_status = 'non-nabl'
                            continue

             # drying time test data
            if result.parameter.internal_id == 'b595d12d-af10-4955-9c17-0f412c260d8f':
                result.result_char = round(self.average_drying_time,3)
                result.calculated = True
                if self.drying_time_nabl == 'pass':
                    result.nabl_status = 'nabl'
                else:
                    result.nabl_status = 'non-nabl'
                continue


             # water retention test data
            if result.parameter.internal_id == '6487f7d1-9f5a-415d-adca-ce9e83d80b0e':
                result.result_char = round(self.average_water_loss_per_area,3)
                result.calculated = True
                if self.water_retention_nabl == 'pass':
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
        record = super(ConcreteCuringCompound, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref')
    def _compute_sample_parameters(self):
        for record in self:
            records = record.eln_ref.parameters_result.parameter.ids
            record.sample_parameters = records
            print("Records",records)

    def get_all_fields(self):
        record = self.env['mechanical.curing.compound'].browse(self.ids[0])
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
        # parameter_based_assignment
        current_user = self.env.user
        for record in self:
            if not record.eln_ref:
                record.sample_parameters = [(6, 0, [])]
                continue

            # filter parameter results by current user
            user_param_results = record.eln_ref.parameters_result.filtered(
                lambda r: r.technician and r.technician.id == current_user.id
            )

            # map to parameter master IDs
            parameter_ids = user_param_results.mapped('parameter').ids

            record.sample_parameters = [(6, 0, parameter_ids)]





    # remark

    notes_id = fields.One2many('curing.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(ConcreteCuringCompound, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'notes': 'The Test Report(s) is/are valid only to the sample submitted to the laboratory.',
            }),
            (0, 0, {
                'notes': 'Sample(s) was/were not drawn by laboratory.',
            }),
            (0, 0, {
                'notes': 'This Report may not be reproduced in except full/ part without the permission of the Lab Head of the Laboratory.',
            }),
            (0, 0, {
                'notes': '# - Information provided by the customer.',
            }),
        ]

        res['notes_id'] = default_notes
        return res






    # Density Test Data
    density_test_name = fields.Char(default="Density Test Data")
    density_test_data_visible = fields.Boolean(compute="_compute_visible")
    Mass = fields.Float("Mass of Empty Cup W0 (g)")
    Mass_of_Cup_with_Sample = fields.Float("Mass of Cup with Sample W1 (g)")
    volume = fields.Float("Volume of Cup V (ml)")
    density = fields.Float("Density = (W1 - W0)/V (g/ml)",compute="_compute_density",store=True,digits=(10, 4))
    
    average_density = fields.Float('Average Density',compute="_compute_average_density")
    density_test_data_table = fields.One2many('mech.curing.density.test.line','parent_id')
   
    density_test_conformity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('--', '--')
    ], string='Conformity', default='fail',compute="_compute_density_test_conformity")
    density_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', default='fail',compute="_compute_density_nabl")

    @api.depends('Mass_of_Cup_with_Sample','Mass', 'volume')
    def _compute_density(self):
        for record in self:
            if record.volume:
                record.density = round((record.Mass_of_Cup_with_Sample - record.Mass) / record.volume, 4)
            else:
                record.density = 0
    
    
    @api.depends('density_test_data_table.density')
    def _compute_average_density(self):
        for record in self:
            try:
                record.average_density = round(sum(record.density_test_data_table.mapped('density')) / len(
                    record.density_test_data_table),4)
            except:
                record.average_density = 0

    @api.depends('average_density','eln_ref','grade')
    def _compute_density_test_conformity(self):
        for record in self:
            record.density_test_conformity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5a57bf7a-5316-40a0-a702-e030cbd40479')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5a57bf7a-5316-40a0-a702-e030cbd40479')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    # import wdb;wdb.set_trace();
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.density_test_conformity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_density - record.average_density*mu_value
                    upper = record.average_density + record.average_density*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.density_test_conformity = 'pass'
                        break
                    else:
                        record.density_test_conformity = 'fail'

    @api.depends('average_density','eln_ref','grade')
    def _compute_density_nabl(self):

        for record in self:
            record.density_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5a57bf7a-5316-40a0-a702-e030cbd40479')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','5a57bf7a-5316-40a0-a702-e030cbd40479')]).parameter_table
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

    
  

   

    # Drying Time Test Data
    drying_time_test_name = fields.Char(default="DRYING TIME TEST DATA (SET-TO-TOUCH)")
    drying_time_test_data_visible = fields.Boolean(compute="_compute_visible")
    application_time = fields.Char("Application Time")
    application_time_am_pm = fields.Selection([('AM', 'AM'),('PM', 'PM'),],string="AM / PM") 
    observation_time= fields.Char("Set-to-Touch Observation Time")
    observation_time_am_pm = fields.Selection([('AM', 'AM'),('PM', 'PM'),],string="AM / PM") 
    drying_time = fields.Float("Drying Time (in hours)")
    drying_time_test_table = fields.One2many('mech.curing.dry.test.line','parent_id')
    average_drying_time = fields.Float("Average Drying Time",compute="_compute_average_drying_time",store=True)
    drying_time_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('--', '--')
    ], string='Confirmity', default='fail',compute="_compute_drying_time_confirmity")
    drying_time_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', default='fail',compute="_compute_drying_time_nabl")


    @api.depends('drying_time_test_table.drying_time')
    def _compute_average_drying_time(self):
        for record in self:
            drying_time = []
            for line in record.drying_time_test_table:
                try:
                    drying_time.append(float(line.drying_time))
                except (TypeError, ValueError):
                    continue

            if drying_time:
                record.average_drying_time = round(sum(drying_time) / len(drying_time),4)
            else:
                record.average_drying_time = 0.0


    @api.depends('average_drying_time','eln_ref','grade')
    def _compute_drying_time_confirmity(self):
        for record in self:
            record.drying_time_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b595d12d-af10-4955-9c17-0f412c260d8f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b595d12d-af10-4955-9c17-0f412c260d8f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.drying_time_confirmity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_drying_time - record.average_drying_time*mu_value
                    upper = record.average_drying_time + record.average_drying_time*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.drying_time_confirmity = 'pass'
                        break
                    else:
                        record.drying_time_confirmity = 'fail'

    @api.depends('average_drying_time','eln_ref','grade')
    def _compute_drying_time_nabl(self):
        
        for record in self:
            record.drying_time_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b595d12d-af10-4955-9c17-0f412c260d8f')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','b595d12d-af10-4955-9c17-0f412c260d8f')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_drying_time - record.average_drying_time*mu_value
                    upper = record.average_drying_time + record.average_drying_time*mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.drying_time_nabl = 'pass'
                        break
                    else:
                        record.drying_time_nabl = 'fail'

    

    # Water Retention Test Data
    water_retention_test_name = fields.Char(default="WATER RETENTION TEST DATA")
    water_retention_test_data_visible = fields.Boolean(compute="_compute_visible") 
    
    surface_area = fields.Char("Surface Area A (m²)")
    initial_wt = fields.Char("Initial Wt. M1 (kg)")
    final_wt = fields.Char("Final Wt. after 72h M2 (kg)")
    loss_of_water = fields.Char("Loss of Water M1-M2 (kg)",compute="_compute_loss_of_water")
    water_loss_per_area = fields.Char("Loss of Water per unit area (kg/m²)",compute="_compute_water_loss_per_area")

    water_retention_test_table = fields.One2many('mech.curing.water.retention.test.line','parent_id')
    average_water_loss_per_area = fields.Float("Average Water Loss per Area",compute="_compute_average_water_loss_per_area")

    water_retention_confirmity = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('--', '--')
    ], string='Confirmity', default='fail',compute="_compute_water_retention_confirmity")
    water_retention_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL'),
    ], string='NABL', default='fail',compute="_compute_water_retention_nabl")

    @api.depends('initial_wt','final_wt')
    def _compute_loss_of_water(self):
        for record in self:
            try:
                if record.final_wt:
                    record.loss_of_water = round(float(record.initial_wt) - float(record.final_wt), 4)
                else:
                    record.loss_of_water = 0
            except (TypeError, ValueError):
                record.loss_of_water = 0

    @api.depends('loss_of_water', 'surface_area')
    def _compute_water_loss_per_area(self):
        for record in self:
            try:
                if record.surface_area and record.loss_of_water:
                    record.water_loss_per_area = round(float(record.loss_of_water) / float(record.surface_area), 4)
                else:
                    record.water_loss_per_area = 0
            except (TypeError, ValueError):
                record.water_loss_per_area = 0

    @api.depends('water_retention_test_table.water_loss_per_area')
    def _compute_average_water_loss_per_area(self):
        for record in self:
            water_loss_per_area = []
            for line in record.water_retention_test_table:
                try:
                    water_loss_per_area.append(float(line.water_loss_per_area))
                except (TypeError, ValueError):
                    continue

            if water_loss_per_area:
                record.average_water_loss_per_area = round(sum(water_loss_per_area) / len(water_loss_per_area), 4)
            else:
                record.average_water_loss_per_area = 0.0


    @api.depends('average_water_loss_per_area','eln_ref','grade')
    def _compute_water_retention_confirmity(self):
        for record in self:
            record.water_retention_confirmity = 'fail'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6487f7d1-9f5a-415d-adca-ce9e83d80b0e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6487f7d1-9f5a-415d-adca-ce9e83d80b0e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    if hasattr(material, 'permissable_limit') and (material.permissable_limit == '--' or not material.permissable_limit):
                        record.water_retention_confirmity = '--'
                        break
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    lower = record.average_water_loss_per_area - record.average_water_loss_per_area*mu_value
                    upper = record.average_water_loss_per_area + record.average_water_loss_per_area*mu_value
                    if lower >= req_min and upper <= req_max :
                        record.water_retention_confirmity = 'pass'
                        break
                    else:
                        record.water_retention_confirmity = 'fail'

    @api.depends('average_water_loss_per_area','eln_ref','grade')
    def _compute_water_retention_nabl(self):
        
        for record in self:
            record.water_retention_nabl = 'pass'
            line = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6487f7d1-9f5a-415d-adca-ce9e83d80b0e')])
            materials = self.env['lerm.parameter.master'].sudo().search([('internal_id','=','6487f7d1-9f5a-415d-adca-ce9e83d80b0e')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    lab_min = line.lab_min_value
                    lab_max = line.lab_max_value
                    mu_value = line.mu_value
                    
                    lower = record.average_water_loss_per_area - record.average_water_loss_per_area*mu_value
                    upper = record.average_water_loss_per_area + record.average_water_loss_per_area *mu_value
                    if lower >= lab_min and upper <= lab_max:
                        record.water_retention_nabl = 'pass'
                        break
                    else:
                        record.water_retention_nabl = 'fail'

    

class CuringDensityTestLine(models.Model):
    _name ="mech.curing.density.test.line"
    parent_id = fields.Many2one('mechanical.curing.compound', string="Parent Id")
    density = fields.Float("Density = (W1 - W0)/V (g/ml)",compute="_compute_density",store=True,digits=(10, 4))
    Mass = fields.Float("Mass of Empty Cup W0 (g)")
    Mass_of_Cup_with_Sample = fields.Float("Mass of Cup with Sample W1 (g)")
    volume = fields.Float("Volume of Cup V (ml)")

    @api.depends('Mass_of_Cup_with_Sample', 'Mass', 'volume')
    def _compute_density(self):
        for record in self:
            if record.volume:
                record.density = round((record.Mass_of_Cup_with_Sample - record.Mass) / record.volume, 3)
            else:
                record.density = 0

class CuringDryTestLine(models.Model):
    _name = "mech.curing.dry.test.line"
    parent_id = fields.Many2one('mechanical.curing.compound', string="Parent Id")
    application_time = fields.Float("Application Time")
    application_time_am_pm = fields.Selection([('AM', 'AM'),('PM', 'PM'),],string="AM / PM") 
    observation_time = fields.Float("Set-to-Touch Observation Time")
    observation_time_am_pm = fields.Selection([('AM', 'AM'),('PM', 'PM'),],string="AM / PM") 
    drying_time = fields.Char("Drying Time (in hours)")
    

class CuringWaterRetentionTestLine(models.Model):
    _name = "mech.curing.water.retention.test.line"
    parent_id = fields.Many2one('mechanical.curing.compound', string="Parent Id")
    surface_area = fields.Char("Surface Area A (m²)")
    initial_wt = fields.Char("Initial Wt. M1 (kg)")
    final_wt = fields.Char("Final Wt. after 72h M2 (kg)")
    loss_of_water = fields.Char("Loss of Water M1-M2 (kg)",compute="_compute_loss_of_water")
    water_loss_per_area = fields.Char("Loss of Water per unit area (kg/m²)",compute="_compute_water_loss_per_area")

    @api.depends('initial_wt','final_wt')
    def _compute_loss_of_water(self):
        for record in self:
            try:
                if record.final_wt:
                    record.loss_of_water = round(float(record.initial_wt) - float(record.final_wt), 4)
                else:
                    record.loss_of_water = 0
            except (TypeError, ValueError):
                record.loss_of_water = 0

    @api.depends('loss_of_water', 'surface_area')
    def _compute_water_loss_per_area(self):
        for record in self:
            try:
                if record.surface_area and record.loss_of_water:
                    record.water_loss_per_area = round(float(record.loss_of_water) / float(record.surface_area), 4)
                else:
                    record.water_loss_per_area = 0
            except (TypeError, ValueError):
                record.water_loss_per_area = 0



    

class CuringNotes(models.Model):
    _name = "curing.notes"

    parent_id = fields.Many2one('mechanical.curing.compound',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")



