from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math



class HtStrand(models.Model):
    _name = "ht.strand"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name = fields.Char("Name",default="FERROUS MATERIALS (HT STAY WIRE)")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    temprature = fields.Float("Temperature (°C)", digits=(10,2))
    humidity = fields.Float("Humidity (%)", digits=(10,2))


    

    sample_submitted = fields.Char("Sample Submitted By")

    sample_status = fields.Char("Sample Status")

    No_of_sample = fields.Integer("Number Of Samples")

    description_work = fields.Text("Work Description")

    product_name = fields.Char(string="Product",compute="_compute_product_name")

    @api.depends('eln_ref', 'eln_ref.sub_product_id')
    def _compute_product_name(self):
        for record in self:
            if record.eln_ref and record.eln_ref.sub_product_id:
                record.product_name = record.eln_ref.sub_product_id.sub_product
            else:
                record.product_name = False

    remark_id = fields.One2many(
    'ht.strand.remark',
    'parent_id',
    string="Remark"
    )

    @api.model
    def default_get(self, fields_list):
        res = super(HtStrand, self).default_get(fields_list)

        default_remarks = [
            (0, 0, {
                'sr_no': 'a',
                'remark': 'Above Sample was cut, polished & etched.',
            }),
            (0, 0, {
                'sr_no': 'b',
                'remark': 'Observations found in respect of the sample tested.',
            }),
            (0, 0, {
                'sr_no': 'c',
                'remark': 'Micro structure grain flow lines observed.',
            }),
            
        ]

        res['remark_id'] = default_remarks

        return res




# remark

    notes_id = fields.One2many('htstrand.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(HtStrand, self).default_get(fields)

        default_notes = [
            (0, 0, {
                'sr_no': 'a',
                'notes': 'The information marked with an # received from customer',
            }),
            (0, 0, {
                'sr_no': 'b',
                'notes': 'The results listed refer only to tested parameters and sample as received from customer',
            }),
            (0, 0, {
                'sr_no': 'c',
                'notes': 'The balance samples if any will be discarded after 15 days from the date of issue of test certificate unless otherwise specified.',
            }),
            (0, 0, {
                'sr_no': 'd',
                'notes': 'This document shall not be reproduced in part or full without the approval of Genstru.',
            }),
        ]

        res['notes_id'] = default_notes
        return res


    @api.depends('eln_ref')
    def _compute_grade_id(self):
        if self.eln_ref:
            self.grade = self.eln_ref.grade_id.id



    ht_strand_name = fields.Char("Name",default="HT STAY WIRE")
    ht_strand_visible = fields.Boolean("Chequered Visible",compute="_compute_visible")   


    nominal_specification = fields.Char("NOMINAL DIAMETER Specification")
    cross_specification = fields.Char("CROSS SECTION  Area  mm2 Specification")
    mass_specification = fields.Char("MASS PER METERE Kg/MTR Specification")
    braking_specification = fields.Char("Braking Load (N) Specification")
    uts_specification = fields.Char("UTS N/MM2 Specification")
    yield_specification = fields.Char("YIELD STRESS N/MM2 Specification")
    proof_specification = fields.Char("0.2% PROOF LOAD(N) Specification")
    elongation_specification = fields.Char("% Elongation at maximum load Specification")

    


    ht_strand_lines = fields.One2many('mechanical.ht.strand.line','parent_id',string="Parameter")

   
    
    

    
     
      ### Compute Visible
    @api.depends('sample_parameters')
    def _compute_visible(self):
        
        for record in self:

            record.ht_strand_visible = False
           
            
            
            for sample in record.sample_parameters:
                print("Internal Ids",sample.internal_id)

               
                if sample.internal_id == "65895-a3df-4990-93d1-9904984644aoo2":
                    record.ht_strand_visible = True
                

    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:
            # import wdb;wdb.set_trace()
            
            if result.parameter.internal_id == '65895-a3df-4990-93d1-9904984644aoo2':
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
        record = super(HtStrand, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record







    # @api.depends('eln_ref')
    # def _compute_sample_parameters(self):
    #     # records = self.env['lerm.eln'].sudo().search([('id','=', record.eln_id.id)]).parameters_result
    #     # print("records",records)
    #     # self.sample_parameters = records
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



    def get_all_fields(self):
        record = self.env['ht.strand'].browse(self.ids[0])
        field_values = {}
        for field_name, field in record._fields.items():
            field_value = record[field_name]
            field_values[field_name] = field_value

        return field_values



class HtStrandLine(models.Model):
    _name = "mechanical.ht.strand.line"
    parent_id = fields.Many2one('ht.strand',string="Parent Id")
   
    sr_no = fields.Integer(string="Sr No.",readonly=True, copy=False, default=1)

    test_parameter = fields.Char(string="TEST PARAMETER")
    nominal_dia = fields.Float(string="NOMINAL DIAMETER")
    cross_section = fields.Float(string="CROSS SECTION  Area  mm2")
    mass_per = fields.Float(string="MASS PER METERE Kg/MTR")
    breaking_load = fields.Float(string="Braking Load (N)")
    uts = fields.Float(string="UTS N/MM2")
    yield_stress = fields.Float(string="YIELD STRESS N/MM2")
    proof_load = fields.Float(string="0.2% PROOF LOAD(N)")
    elongation = fields.Float(string="% Elongation at maximum load")


    
   


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('sr_no'))
                vals['sr_no'] = max_serial_no + 1

        return super(HtStrandLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in chequered_tiles_cement_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.sr_no = index + 1



class htstrandNotes(models.Model):
    _name = "htstrand.notes"

    parent_id = fields.Many2one('ht.strand',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")


class HTStrandRemark(models.Model):
    _name = "ht.strand.remark"

    parent_id = fields.Many2one('ht.strand',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    remark = fields.Char("Remark")




