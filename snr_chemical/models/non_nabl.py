from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class SNRNONNABL(models.Model):
    _name = "snr.chemical"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="SNR CHEMICAL")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)
    sample_id = fields.Many2one('lerm.srf.sample', string="Sample")

    def action_print_nonnabl_report(self):
        self.ensure_one()
        return self.env.ref('nbml_nonnabl.action_nbml_nonnabl_report').report_action(
            self.ids,   # ✅ VERY IMPORTANT
            data={'nabl': False}
        )
    notes_id = fields.One2many('snr.chemical.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(SNRNONNABL, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The report shall not be reproduced in fullor partially without written approval of the laboratory HOD/CEO/Maganement.',
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
                'notes': 'Sample willbe destroyed after 30-days from the date of test report unless otherwise Specified.',
            }),
        ]

        res['notes_id'] = default_notes
        return res


    # ph_name = fields.Char("Name",default="pH of 1 % Solution in water")
    nan_nabl_visible = fields.Boolean("pH",compute="_compute_visible")


    customer_name = fields.Text("Customer Party Name")
    sample_description = fields.Text("Samples Description")
    project_name = fields.Text("Project Name")
    no_of_samples = fields.Integer("No. of Samples")
    date_received = fields.Date("Date of Samples Received")
    brand_grade = fields.Char("Brand & Grade")
    size = fields.Char("Size")
    week_no = fields.Char("Week No")
    test_method = fields.Char("Test Method Adopted")
    source_sample = fields.Char("Source of Sample")
    specification = fields.Char("Specifications")

    customer_ref = fields.Char("Customer Ref No")
    letter_date = fields.Date("Letter Date")
    # srf_no = fields.Char("SRF No")
    test_init_date = fields.Date("Date of Test Initiation")
    test_comp_date = fields.Date("Date of Test Completion")
    sample = fields.Char("Sample ID")

    line_ids = fields.One2many('chemical.snr.line', 'parent_id', string="Test Lines")
    
   


    




    @api.depends('sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.nan_nabl_visible = False
          
            
          

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == '633547hjy-645d-4794-a0fd-5587865258':
                    record.nan_nabl_visible = True

               


    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

            
            
            # Water Absorbtion
            if result.parameter.internal_id == '633547hjy-645d-4794-a0fd-5587865258':
                # result.result_char = round(self.ph_average,2)
                result.calculated = True
              
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
        record = super(SNRNONNABL, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


        
    def get_all_fields(self):
        record = self.env['snr.chemical'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values
    


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

    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id




class ChemicalNonnablLine(models.Model):
    _name = "chemical.snr.line"
    parent_id = fields.Many2one('snr.chemical',string="Parent Id")

    sr_no = fields.Integer(string="Sr.No.",readonly=True, copy=False, default=1)
    test_name = fields.Char("Test")
    unit = fields.Char("Unit")
    test_method = fields.Char("Test Method")
    result = fields.Char("Result")
    specification = fields.Char("Specification")
  





  

    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(ChemicalNonnablLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1








class SNRNotes(models.Model):
    _name = "snr.chemical.notes"

    parent_id = fields.Many2one('snr.chemical',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")
    