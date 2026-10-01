from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import math

class AluminiumMacroStractural(models.Model):
    _name = "aluminium.macro.stractural"
    _inherit = "lerm.eln"
    _rec_name = "name"

    name1 = fields.Char("Name",default="Aluminium Materials, Alloys & Products (Macro Structural Analysis)")
    eln_state = fields.Selection(related='eln_ref.state', string="ELN State", store=True)
    parameter_id = fields.Many2one('eln.parameters.result',string="Parameter")
    sample_parameters = fields.Many2many('lerm.parameter.master',string="Parameters",compute="_compute_sample_parameters",store=True)
    eln_ref = fields.Many2one('lerm.eln',string="Eln")
    grade = fields.Many2one('lerm.grade.line',string="Grade",compute="_compute_grade_id",store=True)

    temprature = fields.Float("Temperature (°C)", digits=(10,2))
    humidity = fields.Float("Humidity (%)", digits=(10,2))


    magnification = fields.Char("MAGNIFICATION")


    etching = fields.Char("ETCHING ECHANT")

    sample_submitted = fields.Char("Sample Submitted By")

    sample_status = fields.Char("Sample Status")

    No_of_sample = fields.Integer("Number Of Samples")

    description_work = fields.Text("Work Description")

    product_name = fields.Char(string="Product",compute="_compute_product_name")

    # Image Fields
    # original_image = fields.Image(string="Original Image", attachment=True)
    # processed_image = fields.Image(string="Processed Image", attachment=True)

    original_image = fields.Many2many(
    'ir.attachment',
    'aluminium_macro_original_image_rel',
    'measurement_id',
    'attachment_id',
    string='Original Image',
    help='Attach multiple original images to the sample',
    )

    processed_image = fields.Many2many(
        'ir.attachment',
        'aluminium_macro_processed_image_rel',
        'measurement_id',
        'attachment_id',
        string='Processed Image',
        help='Attach multiple processed images to the sample',
    )


    @api.depends('eln_ref', 'eln_ref.sub_product_id')
    def _compute_product_name(self):
        for record in self:
            if record.eln_ref and record.eln_ref.sub_product_id:
                record.product_name = record.eln_ref.sub_product_id.sub_product
            else:
                record.product_name = False

    

    notes_id = fields.One2many('aluminium.macro.stractural.notes', 'parent_id', string="Notes")
    
    @api.model
    def default_get(self, fields):
        res = super(AluminiumMacroStractural, self).default_get(fields)

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


    remark_id = fields.One2many(
    'aluminium.macro.stractural.remark',
    'parent_id',
    string="Remark"
    )

    @api.model
    def default_get(self, fields_list):
        res = super(AluminiumMacroStractural, self).default_get(fields_list)

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


    aluminium_macro_name = fields.Char("Name",default="Macro Structural Analysis")
    aluminium_macro_visible = fields.Boolean("pH",compute="_compute_visible")

    aluminium_macro_lines = fields.One2many('aluminium.macro.stractural.line','parent_id',string="Parameter")
    
    
   


    @api.depends('sample_parameters')
    def _compute_visible(self):
        for record in self:
            record.aluminium_macro_visible = False
           
            
            
          

            for sample in record.sample_parameters:
                print("Samples internal id",sample.internal_id)
                if sample.internal_id == 'o897654rft-978b-483c-9988-27158907890765':
                    record.aluminium_macro_visible = True

               
                
                
            



    def open_eln_page(self):
        # parameter_based_assignment
        current_user = self.env.user
        # 🔹 Only results assigned to current technician
        technician_results = self.eln_ref.parameters_result.filtered(
            lambda r: r.technician == current_user
        )

        for result in technician_results:

            
            
            # Water Absorbtion
            if result.parameter.internal_id == 'o897654rft-978b-483c-9988-27158907890765':
                # result.result_char = round(self.carbon_percentage,3)
                result.calculated = True
                # if self.carbon_percentage_nabl == 'pass':
                #     result.nabl_status = 'nabl'
                # else:
                #     result.nabl_status = 'non-nabl'
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
        record = super(AluminiumMacroStractural, self).create(vals)
        # record.get_all_fields()
        record.eln_ref.write({'model_id':record.id})
        return record


        
    def get_all_fields(self):
        record = self.env['aluminium.macro.stractural'].browse(self.ids[0])
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


class AluminiumMacroStracturalLine(models.Model):
    _name = "aluminium.macro.stractural.line"
    parent_id = fields.Many2one('aluminium.macro.stractural',string="Parent Id")

    serial_no = fields.Integer(string="SL. No", readonly=True, copy=False, default=1)
    sample_identity = fields.Char(string="Sample  Identity")
    sample_no = fields.Char(string="SAMPLE NO.")
   
    # f10 = fields.Integer(string="10")
    result = fields.Char(string="RESULT ")

    remarks = fields.Char(string="REMARKS")

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        if self.parent_id:
            self.sample_identity = self.parent_id.product_name
        else:
            self.sample_identity = False
    


    @api.model
    def create(self, vals):
        # Set the serial_no based on the existing records for the same parent
        if vals.get('parent_id'):
            existing_records = self.search([('parent_id', '=', vals['parent_id'])])
            if existing_records:
                max_serial_no = max(existing_records.mapped('serial_no'))
                vals['serial_no'] = max_serial_no + 1

        return super(AluminiumMacroStracturalLine, self).create(vals)

    def _reorder_serial_numbers(self):
        # Reorder the serial numbers based on the positions of the records in child_lines
        records = self.sorted('id')
        for index, record in enumerate(records):
            record.serial_no = index + 1








class AluminiumMacroStracturalNotes(models.Model):
    _name = "aluminium.macro.stractural.notes"

    parent_id = fields.Many2one('aluminium.macro.stractural',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    notes = fields.Char("Notes")

class AluminiumMacroStracturalRemark(models.Model):
    _name = "aluminium.macro.stractural.remark"

    parent_id = fields.Many2one('aluminium.macro.stractural',string="Parent Id")
    sr_no = fields.Char("Sr. No.")
    remark = fields.Char("Remark")
    