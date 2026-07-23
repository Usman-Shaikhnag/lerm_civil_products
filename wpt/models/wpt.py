from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import datetime , timedelta
import math



class WptMechanical(models.Model):
    _name = "mechanical.wpt"
    _inherit = "lerm.eln"
    _description = 'mechanical.wpt'
    _rec_name = "name"


    name = fields.Char("Name",default="Water Permeability Test")
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")

    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)

    
    child_lines = fields.One2many('mechanical.wpt.line','parent_id',string="Parameter")



    average_of_wpt = fields.Float(string="Average of WPT", compute="_compute_average_of_averages")

    @api.depends('child_lines.average')
    def _compute_average_of_averages(self):
        for record in self:
            if record.child_lines:
                record.average_of_wpt = round(sum(line.average for line in record.child_lines) / len(record.child_lines), 3)
            else:
                record.average_of_wpt = 0.0


    wpt_conformity = fields.Selection([
            ('pass', 'Pass'),
            ('fail', 'Fail')], string="Conformity", compute="_compute_wpt_conformity", store=True)

    @api.depends('average_of_wpt','eln_ref','grade')
    def _compute_wpt_conformity(self):
        
        for record in self:
            record.wpt_conformity = 'fail'
            line = self.env['lerm.parameter.master'].search([('internal_id','=','32145ght-0268-46ef-ba88-9c0453210lkit1')])
            materials = self.env['lerm.parameter.master'].search([('internal_id','=','32145ght-0268-46ef-ba88-9c0453210lkit1')]).parameter_table
            for material in materials:
                if material.grade.id == record.grade.id:
                    req_min = material.req_min
                    req_max = material.req_max
                    mu_value = line.mu_value
                    
                    lower = record.average_of_wpt - record.average_of_wpt*mu_value
                    upper = record.average_of_wpt + record.average_of_wpt*mu_value
                    if lower >= req_min and upper <= req_max:
                        record.wpt_conformity = 'pass'
                        break
                    else:
                        record.wpt_conformity = 'fail'


    wpt_nabl = fields.Selection([
        ('pass', 'NABL'),
        ('fail', 'NON NABL')], string="NABL", default='fail',compute="_compute_wpt_nabl", store=True)

    @api.depends('average_of_wpt','eln_ref','grade')
    def _compute_wpt_nabl(self):
        
        for record in self:
            record.wpt_nabl = 'fail'
            line = self.env['lerm.parameter.master'].search([('internal_id','=','32145ght-0268-46ef-ba88-9c0453210lkit1')])
            materials = self.env['lerm.parameter.master'].search([('internal_id','=','32145ght-0268-46ef-ba88-9c0453210lkit1')]).parameter_table
            # for material in materials:
            #     if material.grade.id == record.grade.id:
            lab_min = line.lab_min_value
            lab_max = line.lab_max_value
            mu_value = line.mu_value
            
            lower = record.average_of_wpt - record.average_of_wpt*mu_value
            upper = record.average_of_wpt + record.average_of_wpt*mu_value
            if lower >= lab_min and upper <= lab_max:
                record.wpt_nabl = 'pass'
                break
            else:
                record.wpt_nabl = 'fail'



    temp_wpt = fields.Float("Temperature °C")
    humidity_percent_wpt = fields.Float("Humidity %")
    quantity = fields.Char("Quantity",compute="_compute_quantity")
    size = fields.Many2one('lerm.size.line',string="Specimen Size (mm)",compute="_compute_size",store=True)

    # start_date_wpt = fields.Date("Start Date")
    # end_date_wpt = fields.Date("End Date")
      

    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)

    # casting_date = fields.Date("Date of Casting",compute="_compute_casting_date")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    age_of_days = fields.Selection([
        ('3days', '3 Days'),
        ('7days', '7 Days'),
        ('14days', '14 Days'),
        ('28days', '28 Days'),
    ], string='Age', default='28days',required=True,compute="_compute_age_of_days")
    date_of_casting = fields.Date(string="Date of Casting",compute="compute_date_of_casting")
    date_of_testing = fields.Date(string="Date of Testing")

    age_of_test = fields.Integer("Age of Test, days",compute="compute_age_of_test")
    difference = fields.Integer("Difference",compute="compute_difference")

    @api.onchange('eln_ref')
    def _compute_age_of_days(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).days_casting
                if sample_record == '3':
                    record.age_of_days = '3days'
                elif sample_record == '7':
                    record.age_of_days = '7days'
                elif sample_record == '14':
                    record.age_of_days = '14days'
                elif sample_record == '28':
                    record.age_of_days = '28days'
                else:
                    record.age_of_days = None
            else:
                record.age_of_days = None

    @api.onchange('eln_ref')
    def compute_date_of_casting(self):
        for record in self:
            if record.eln_ref.sample_id:
                sample_record = self.env['lerm.srf.sample'].sudo().search([('id','=', record.eln_ref.sample_id.id)]).date_casting
                record.date_of_casting = sample_record
            else:
                record.date_of_casting = None

    @api.depends('date_of_testing','date_of_casting')
    def compute_age_of_test(self):
        for record in self:
            if record.date_of_casting and record.date_of_testing:
                date1 = fields.Date.from_string(record.date_of_casting)
                date2 = fields.Date.from_string(record.date_of_testing)
                date_difference = (date2 - date1).days
                record.age_of_test = date_difference
            else:
                record.age_of_test = 0
    
    @api.depends('age_of_test','age_of_days')
    def compute_difference(self):
        for record in self:
            age_of_days = 0
            if record.age_of_days == '3days':
                age_of_days = 3
            elif record.age_of_days == '7days':
                age_of_days = 7
            elif record.age_of_days == '14days':
                age_of_days = 14
            elif record.age_of_days == '28days':
                age_of_days = 28
            else:
                age_of_days = 0
            record.difference = record.age_of_test - age_of_days


  
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
    def open_eln_page(self):
        # import wdb; wdb.set_trace()

        for result in self.eln_ref.parameters_result:
            if result.parameter.internal_id == '32145ght-0268-46ef-ba88-9c0453210lkit1':
                result.result_char = round(self.average_of_wpt,2)
                result.calculated = True
                if self.wpt_nabl == 'pass':
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
        record = super(WptMechanical, self).create(vals)
        record.parameter_id.write({'model_id':record.id})
        record.eln_ref.write({'model_id':record.id})
        return record

    @api.depends('eln_ref')
    def _compute_job_no(self):
        for record in self:
            record.job_no = record.eln_ref.sample_id

    @api.depends('eln_ref')
    def _compute_size(self):
        if self.eln_ref:
            self.size = self.eln_ref.size_id.id

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id

    @api.depends('eln_ref')
    def _compute_quantity(self):
        if self.eln_ref:
            self.quantity = self.eln_ref.sample_id.volume


    notes_id = fields.One2many('mechanical.wpt.notes', 'parent_id', string="Notes", default=lambda self: self._default_notes_lines())

    @api.model
    def _default_notes_lines(self):
        return [
            (0, 0, {
                'sr_no': 'i',
                'notes': 'Attention is drawn to the limitations of liability, indemnification, and jurisdiction provisions applicable to this report. The information contained herein reflects the findings of Geonyms India Private Limited at the time of testing and only within the scope of work and instructions received from the Client, where applicable',
            }),
            (0, 0, {
                'sr_no': 'ii',
                'notes': 'The Companys responsibility is limited to the Client for whom this report has been issued. This report does not relieve any party from exercising its rights and fulfilling its obligations under any contract, agreement, or applicable statutory requirements. Unless otherwise stated, the results reported herein relate only to the sample(s) tested and do not necessarily indicate the quality of the entire lot, batch, or material from which the sample(s) were drawn. ',
            }),
            (0, 0, {
                'sr_no': 'iii',
                'notes': 'The sample(s) tested shall be retained for a period of ninety (90) days from the date of issue of this report unless otherwise agreed with the Client. This report shall not be reproduced, except in full, without the prior written approval of Geonyms India Private Limited. ',
            }),
            (0, 0, {
                'sr_no': 'iv',
                'notes': 'Partial reproduction, unauthorized alteration, forgery, falsification, or misuse of this report is prohibited and may result in legal action.',
            }),

            (0, 0, {
                'sr_no': 'v',
                'notes': ' Any complaint concerning this report shall be submitted in writing within fifteen (15) days from the date of issue of the report. The use of this report or extracts thereof in advertisements, promotional material, media publications, or any public disclosure requires prior written approval from Geonyms India Private Limited',
            }),
        ]

    # @api.depends('eln_ref')
    # def _compute_casting_date(self):
    #     if self.eln_ref:
    #         self.casting_date = self.eln_ref.sample_id.date_casting
    


class WptMechanicalLine(models.Model):
    _name = "mechanical.wpt.line"
    parent_id = fields.Many2one('mechanical.wpt',string="Parent Id")

    sample = fields.Char(string="Sample",compute="_compute_sample_id")
    depth1 = fields.Float(string="Specimen 1")
    depth2 = fields.Float(string="Specimen 2")
    depth3 = fields.Float(string="Specimen 3")
    average = fields.Float(string="Average",compute="_compute_average")

    @api.depends('depth1','depth2','depth3')
    def _compute_average(self):
        for record in self:
            average = round(((record.depth1 + record.depth2 + record.depth3)/3),2)
            record.average = average


    # @api.depends('parent_id')
    # def _compute_sample_id(self):
    #     for record in self:
    #         try:
    #             record.sample = record.parent_id.eln_ref.sample_id.client_sample_id
    #         except:
    #             record.sample = None

    @api.depends('parent_id')
    def _compute_sample_id(self):
        for record in self:
            try:
                record.sample = record.parent_id.eln_ref.sample_id.client_sample_id
            except:
                record.sample = None

class WptMechanicalNotes(models.Model):
    _name = "mechanical.wpt.notes"

    parent_id = fields.Many2one('mechanical.wpt', string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
