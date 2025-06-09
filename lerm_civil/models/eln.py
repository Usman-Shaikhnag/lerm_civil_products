from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError
from datetime import datetime
import math
from decimal import Decimal
from matplotlib import pyplot as plt
from datetime import datetime, timedelta
# import io
# from PIL import Image
# import base64



import base64
import json

class ELN(models.Model):
    _name = 'lerm.eln'
    _inherit = ['mail.thread','mail.activity.mixin']
    _rec_name = 'eln_id'


    eln_id = fields.Char("ELN ID",required=True,readonly=True, default=lambda self: 'New',tracking=3)
    ir_model = fields.Many2one('ir.model',string="Model")

    srf_id = fields.Many2one('lerm.civil.srf',string="SRF ID")
    technician = fields.Many2one('res.users',string="Technicians",tracking=5)
    sample_id = fields.Many2one('lerm.srf.sample',string='Sample ID',tracking=True,ondelete="cascade")
    srf_date = fields.Date(string='SRF Date',tracking=True)
    kes_no = fields.Char(string="KES NO",tracking=True)
    discipline = fields.Many2one('lerm_civil.discipline',string="Discipline",tracking=4)
    lab_no_value = fields.Char(string="Value")
    # lab_l_id = fields.Integer(string="Lab Locations",domain="[('parent_id', '=', discipline_id)]")
    # lab_l_id = fields.Many2one('lab.location', string="Lab Locations",domain="[('parent_id', '=', discipline_id)]")
    group = fields.Many2one('lerm_civil.group',string="Group")
    # department_id = fields.Many2one('hr.department', string='Department')
    department_id = fields.Char(string='Department')
    material = fields.Many2one('product.template',string='Material')
    witness_name = fields.Char(string="Witness Name")
    witness_description = fields.Char(string="Witness Description")
    witness_photo = fields.Binary(string="Witness Photo")
    witness_photo_name = fields.Char(string="Witness Photo Name")
    casting_date = fields.Date(string="Casting Date",compute="_compute_casting_date")
    attachment = fields.Binary(string="Attachment")
    attachment_name = fields.Char(string="Attachment Name")
    parameters = fields.One2many('eln.parameters','eln_id',string="Parameters")
    datasheets = fields.One2many('eln.spreadsheets','eln_id',string="Datasheets")
    fetch_ds_button = fields.Float(string="Fetch Datasheet")
    ir_model = fields.Many2one('ir.model',string="Model")



    
    size_id = fields.Many2one('lerm.size.line',string="Size")
    size_ids = fields.Many2many('lerm.size.line',string="Size", compute="compute_size")
    grade_id = fields.Many2one('lerm.grade.line',string="Grade")
    grade_ids = fields.Many2many('lerm.grade.line',string="Grades", compute="compute_grade")

    update_result = fields.Integer("Update Result")
    state = fields.Selection([
        ('1-draft', 'In-Test'),
        ('2-confirm', 'In-Check'),
        ('3-approved','Approved'),
        ('4-rejected','Rejected'),
        ('5-cancelled','Cancelled')
    ], string='State',default='1-draft')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    remarks = fields.Text("Remarks")
    parameters_result = fields.One2many('eln.parameters.result','eln_id',string="Parameters")
    parameters_input = fields.One2many('eln.parameters.inputs','eln_id',string="Parameters Inputs") 
    conformity = fields.Boolean(string="Conformity")
    has_witness = fields.Boolean(string="Witness")
    invisible_fetch_inputs = fields.Boolean(string="Fetch Inputs")
    name = fields.Char(string="Name")
    image = fields.Binary(string="Image", attachment=True)
    is_product_based_calculation = fields.Boolean(string="Product Based Calculation",compute="_compute_product_based")
    model_id = fields.Integer("Model ID")
    temperature = fields.Float("Temperature")
    instrument = fields.Many2one('maintenance.equipment',string="Instrument")
    sop = fields.Html(string='SOP',compute="comput_sop")
    date_testing = fields.Date("Date of Testing",compute="_compute_date_testing")
    # data_sheet = fields.Binary(string="Data Sheet", attachment=True)

    # file_upload = fields.Many2many(
    #     'ir.attachment',
    #     'lerm_report_upload_rel_eln',
    #     'eln_id',
    #     'attachment_id_1',
    #     string='Datasheet Upload',
    #     help='Attach multiple images to the sample',
    # )

    file_upload = fields.Many2many(
        'ir.attachment',
        string='Datasheet Upload',
        help='Attach multiple images to the sample',
    )

    
    active = fields.Boolean(string="Active",default=True)

    
   
   

    # report_upload = fields.Many2many(
    #     'ir.attachment',
    #     string='Report Upload',
    #     help='Attach multiple images to the sample',
    # )


    @api.depends('sample_id')
    def _compute_date_testing(self):
        for record in self:
            if record.sample_id.casting and record.sample_id.casting_date:
                date_casting = record.sample_id.casting_date
                days_casting = 0
                if record.sample_id.days_casting == '1':
                    days_casting = 1
                elif record.sample_id.days_casting == '3':
                    days_casting = 3
                elif record.sample_id.days_casting == '7':
                    days_casting = 7
                elif record.sample_id.days_casting == '14':
                    days_casting = 14
                elif record.sample_id.days_casting == '21':
                    days_casting = 21
                elif record.sample_id.days_casting == '28':
                    days_casting = 28
                elif record.sample_id.days_casting == '45':
                    days_casting = 45
                elif record.sample_id.days_casting == '56':
                    days_casting = 56
                elif record.sample_id.days_casting == '112':
                    days_casting = 112
                # import wdb; wdb.set_trace()
                
                record.date_testing = date_casting + timedelta(days=int(days_casting))
            else:
                 record.date_testing = False


    # @api.onchange('start_date','srf_date')
    # def _start_date_validate(self):
    #     for record in self:
    #         if record.start_date < record.srf_date:
    #             record.start_date = record.srf_date
    #             raise ValidationError("Start Date cannot be before SRF creation date")
    #         else:
    #             pass
    @api.depends('casting_date','sample_id')
    def _compute_casting_date(self):
        for record in self:
            if record.sample_id.casting:
                record.casting_date = record.sample_id.date_casting
            else:
                record.casting_date = None

    @api.onchange('start_date', 'srf_date')
    def _start_date_validate(self):
        for record in self:
            if record.start_date and record.srf_date and record.start_date < record.srf_date:
                record.start_date = record.srf_date
                raise ValidationError("Start Date cannot be before SRF creation date")
                # record.update({'start_date': record.srf_date})



    
    
    @api.depends('material')
    def compute_grade(self):        
        for record in self:
            try:
                if record.material:
                    record.grade_ids = self.env['product.template'].search([('id','=', record.material.id)]).grade_table
            except:
                record.grade_ids = False


    @api.depends('material')
    def compute_size(self):
        for record in self:
            try:
                if record.material:
                    record.size_ids = self.env['product.template'].search([('id','=', record.material.id)]).size_table
            except:
                record.size_ids = False

    @api.onchange('witness')
    def update_witness_name(self):
        if self.env.context.get('update_witness_name'):
            self.witness_name = self.witness

    # @api.depends('material')
    # def compute_grade(self):        
    #     for record in self:
    #         if record.material:
    #             record.grade_ids = self.env['product.template'].search([('id','=', record.material.id)]).grade_table

    # @api.depends('material')
    # def compute_size(self):
    #     for record in self:
    #         if record.material:
    #             record.size_ids = self.env['product.template'].search([('id','=', record.material.id)]).size_table
    
    @api.model
    def create(self, values):
        record = super(ELN, self).create(values)
        record.update_witness_name()
        return record


    def get_dynamic_report_name(self):
        # Implement your logic to generate the dynamic report name based on the field value.
        # You can access the current record's field values using `self`.
        return "Report " + self.sample_id 
    
    
    @api.depends("material")
    def comput_sop(self):
        for rec in self:
            rec.sop = rec.material.sop



    def get_product_base_calc_line(self,data):
        line = self.env["lerm.product.based.calculation"].search([('product_id','=',data["material_id"]),('grade','=',data["grade_id"])])
        return line


    def open_product_based_form(self):
        model_record = self.material.product_based_calculation.filtered(lambda r: r.grade.id == self.grade_id.id)
        model = model_record.ir_model.model

        print("material ",self.material.product_based_calculation)
        print("model ",model)

        if self.model_id != 0:
            # import wdb; wdb.set_trace()
            return {
                'view_mode': 'form',
                'res_model': model,
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.model_id,
                'context': {
                    'default_srf_id':self.srf_id.id,
                    'default_sample_id': self.sample_id.id,
                    'default_eln_ref':self.id
                 }
            }
        
        else:
            # import wdb; wdb.set_trace()
            return {
                'view_mode': 'form',
                'res_model': model,
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': {
                    'default_srf_id':self.srf_id.id,
                    'default_sample_id': self.sample_id.id,
                    'default_eln_ref':self.id
                 }
                }

   


    @api.depends('material')
    def _compute_product_based(self):
        for record in self:
            record.is_product_based_calculation = record.material.is_product_based_calculation
    # def calculate_graphs(self):
    #     import wdb; wdb.set_trace()
    #     x = [1, 2, 3, 4, 5]
    #     y = [1, 4, 9, 16, 25]

    #     # Plot the line chart
    #     plt.plot(x, y)
    #     plt.xlabel('X values')
    #     plt.ylabel('Y values')
    #     plt.title('Line Chart')

    #     # Save the chart as an image file
    #     buffer = io.BytesIO()
    #     plt.savefig(buffer, format='png')
    #     buffer.seek(0)
    #     image_data = buffer.read()
    #     buffer.close()

    #     # Convert the image data to base64 format
    #     encoded_image_data = base64.b64encode(image_data)

    #     # Update the image field with the chart image
    #     self.image = encoded_image_data

    #     # Close the plot to release resources
    #     plt.close()

    def fetch_inputs(self):
        self.write({
            "invisible_fetch_inputs": True
        })

        # parameter = self.env['lerm.parameter.master'].browse(7)  # Replace 'parameter_id' with the actual ID of the parameter
        # dependent_parameters = parameter.fetch_dependent_parameters_recursive(depth=80)  # Fetch up to 3 levels of dependent parameters
        # # import wdb ; wdb.set_trace() 
        # for dependent_parameter in dependent_parameters:
        #     import wdb ; wdb.set_trace() 
        #     print(dependent_parameter.parameter_name)
        # parameters = []

        for record in self.parameters_result:
            parameter = self.env['lerm.parameter.master'].browse(record.parameter.id)
            # import wdb ; wdb.set_trace() 

            for inputs in parameter.dependent_inputs:
                self.write({"parameters_input":[(0,0,{'parameter_result':record.id,"is_parameter_dependent":inputs.is_parameter_dependent,'identifier':inputs.identifier,'inputs':inputs.id,'value':inputs.default})]})
            
            dependent_parameters = parameter.fetch_dependent_parameters_recursive(depth=80)
            for dependent_parameter in dependent_parameters:
                # import wdb ; wdb.set_trace()
                data = self.env["eln.parameters.result"].create({"eln_id":self.id,'parameter':dependent_parameter.id})
                # data = self.write({"parameters_result":[(0,0,{'parameter':dependent_parameter.id})]})
                for inputs in dependent_parameter.dependent_inputs:
                    # import wdb ; wdb.set_trace() 
                    self.write({"parameters_input":[(0,0,{'parameter_result':data.id,"is_parameter_dependent":inputs.is_parameter_dependent,'identifier':inputs.identifier,'inputs':inputs.id,'value':inputs.default})]})



            # dependent_parameters = parameter.fetch_dependent_parameters_recursive(depth=80)

            # for inputs in record.parameter.dependent_inputs:
                
            #     self.write({"parameters_input":[(0,0,{'parameter_result':record.id,'identifier':inputs.identifier,'inputs':inputs.id})]})
            #     if inputs.is_parameter_dependent:

            #         # data = self.write({"parameters_result":[(0,0,{'parameter':inputs.parameter.id})]})
            #         data = self.env["eln.parameters.result"].create({"eln_id":self.id,'parameter':inputs.parameter.id})
            #         import wdb ; wdb.set_trace()
            #         for inputs in data.parameter.dependent_inputs: 
            #             self.write({"parameters_input":[(0,0,{'parameter_result':data.id,'identifier':inputs.identifier,'inputs':inputs.id})]})

            #         self.env.cr.commit()

    def calculate_results(self):
        for record in self.parameters_result:
            inputs = self.env["eln.parameters.inputs"].search([("parameter_result","=",record.id)])
            values = {
                        'datetime':datetime
                    }
            for input in inputs:
                values[input.identifier] = input.value
            result = safe_eval(record.parameter.formula, values)
            record.write({'result':result})
            print(result) 



    # def confirm_eln(self):
    #     self.sample_id.write({'state':'3-pending_verification'})
    #     # import wdb;wdb.set_trace();
    #     self.sample_id.parameters_result.unlink()
    #     self.end_date = datetime.now().date()
    #     if self.srf_date:
    #         if self.start_date < self.srf_date:
    #             raise ValidationError("Start Date cannot be less than SRF Date")

    #     for result in self.parameters_result:
    #         if not result.calculated:
    #             raise ValidationError("Not all parameters are calculated. Please ensure all parameters are calculated before proceeding.")

    #     for result in self.parameters_result:
    #         self.env["sample.parameters.result"].create({
    #             'sample_id':self.sample_id.id,
    #             'parameter': result.parameter.id,
    #             'result': result.result,
    #             'unit':result.unit.id,
    #             'specification':result.specification,
    #             'test_method':result.test_method.id
    #         })
    #     self.write({'state': '2-confirm'})
            
    # def confirm_eln(self):
    #     self.sample_id.write({'state':'3-pending_verification'})
    #     # import wdb;wdb.set_trace();
    #     self.sample_id.parameters_result.unlink()
        
    #     # Fetch start_date and set it as end_date
    #     start_date = self.start_date
    #     # Ensure end_date is not the current date
    #     desired_end_date = start_date if start_date != datetime.now().date() else start_date + timedelta(days=1)

    #     self.end_date = desired_end_date
        
    #     if self.srf_date:
    #         if self.start_date < self.srf_date:
    #             raise ValidationError("Start Date cannot be less than SRF Date")

    #     for result in self.parameters_result:
    #         if not result.calculated:
    #             raise ValidationError("Not all parameters are calculated. Please ensure all parameters are calculated before proceeding.")

    #     for result in self.parameters_result:
    #         self.env["sample.parameters.result"].create({
    #             'sample_id':self.sample_id.id,
    #             'parameter': result.parameter.id,
    #             'result': result.result,
    #             'unit':result.unit.id,
    #             'specification':result.specification,
    #             'test_method':result.test_method.id
    #         })
    #     self.write({'state': '2-confirm'})
    def confirm_eln(self):

        # if not self.data_sheet:
        #     raise ValidationError("Please attach a data sheet before confirming ELN.")

        
            
        sample_id = self.sample_id.sudo()
        sample_id.write({'state':'3-pending_verification'})
        sample_id.parameters_result.unlink()
            
        start_date = self.start_date
        
        # Ensure end_date is not before start_date
        if self.end_date and self.end_date < start_date:
            raise ValidationError("End Date cannot be before Start Date")
        # import wdb;wdb.set_trace()
        
        # if len(self.file_upload) > 0:
        #     self.sample_id.sudo().file_upload = self.file_upload
        # else:
        #     raise ValidationError("Please attach datasheet before submitting")
        
        # If end_date is not provided, set it to the next day after start_date
        if not self.end_date:
            self.end_date = start_date + timedelta(days=1)
        else:
            # If end_date is provided, check if it's before start_date
            if self.end_date < start_date:
                raise ValidationError("End Date cannot be before Start Date")
            
        if self.srf_date:
            if self.start_date < self.srf_date:
                raise ValidationError("Start Date cannot be less than SRF Date")

        for result in self.parameters_result:
            if not result.calculated:
                raise ValidationError("Not all parameters are calculated. Please ensure all parameters are calculated before proceeding.")

        for result in self.parameters_result:
            self.env["sample.parameters.result"].sudo().create({
                'sample_id':self.sample_id.id,
                'parameter': result.parameter.id,
                'result': result.result,
                'unit':result.unit.id,
                'specification':result.specification,
                'test_method':result.test_method.id
            })
        self.write({'state': '2-confirm'})


    def reupdate_result(self):
        sample = self.sample_id.sudo()
        # sample = self.sample_id
        # import wdb;wdb.set_trace()
        # print(sample)
        self.sample_id.sudo().file_upload = self.file_upload
        sample.parameters_result.sudo().unlink()
        for result in self.parameters_result:
            sample.parameters_result.sudo().create({
                'sample_id':self.sample_id.id,
                'parameter': result.parameter.id,
                'result': result.result,
                'unit':result.unit.id,
                'specification':result.specification,
                'test_method':result.test_method.id 
            })
        # for result in self.parameters_result:
        #     self.env["sample.parameters.result"].create({
        #         'sample_id':self.sample_id.id,
        #         'parameter': result.parameter.id,
        #         'result': result.result,
        #         'unit':result.unit.id,
        #         'specification':result.specification,
        #         'test_method':result.test_method.id
        #     })
        


    

    

    # def create_sample_parameters_result(self):
    #     lerm_eln_obj = self.env['lerm.eln'].browse(self._context.get('active_id'))
    #     lerm_eln_obj.ensure_one()
    #     for wizard in self:
    #         lerm_eln_obj.parameters_result.create({
    #             'sample_id': wizard.sample_id.id,
    #             'parameter': wizard.parameter.id,
    #             'result': wizard.result,
    #             'unit': wizard.unit.id,
    #             'specification': wizard.specification,
    #             'test_method': wizard.test_method.id,
    #         })
    #     return {'type': 'ir.actions.act_window_close'}

        # parameters = fields.One2many('eln_id','eln.parameters',string="Parameters")

    

        def open_result_wizard(self):
            action = self.env.ref('lerm_civil.eln_result_update_wizard')

            parameters = []
            for parameter in self.parameters:
                parameters.append((0,0,{'parameter':parameter.id}))
            
            return {
                'name': "Result Update",
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'eln.update.result.wizard',
                'view_id': action.id,
                'target': 'new',
                'context': {
                    'default_results':parameters
                }
            }
            
    def print_datasheet(self):
        # import wdb ; wdb.set_trace()

        # sample_id = self.sample_id
        # sample_id.print_datasheet()

        eln = self
        # eln = self.env["lerm.eln"].search([('sample_id','=', eln.sample_id.id)])S

        is_product_based = eln.is_product_based_calculation
        if is_product_based == True:
            template_name = eln.material.product_based_calculation[0].datasheet_report_template.report_name
        else:
            template_name = eln.parameters_result.parameter[0].datasheet_report_template.report_name
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': template_name,
            'report_file': template_name,
            'data' : {'fromsample' : False,'eln_id':self.id,'report_wizard':False}
            
        }
        

    # def print_datasheet(self):
    #     eln = self
    #     is_product_based = eln.is_product_based_calculation
    #     if is_product_based == True:
    #         template_name = eln.material.product_based_calculation[0].datasheet_report_template.report_name
    #     else:
    #         template_name = eln.parameters_result.parameter[0].datasheet_report_template.report_name
    #     return {
    #         'type': 'ir.actions.report',
    #         'report_type': 'qweb-html',
    #         'report_name': template_name,
    #         'report_file': template_name
    #     }
    def print_report(self):
        eln = self
        is_product_based = eln.material.is_product_based_calculation
        if is_product_based == True:
            template_name = eln.material.product_based_calculation[0].main_report_template.report_name
        else:
            template_name = eln.parameters_result.parameter[0].main_report_template.report_name
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': template_name,
            'report_file': template_name,
            'data' : {'fromsample' : False , 'inreport' : self , 'nabl' : False,'fromEln':True}

        }
    def print_nabl_report(self):
        eln = self
        is_product_based = eln.is_product_based_calculation
        if is_product_based == True:
            template_name = eln.material.product_based_calculation[0].main_report_template.report_name
        else:
            template_name = eln.parameters_result.parameter[0].main_report_template.report_name
        return {
            'name':self.kes_no,
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': template_name,
            'report_file': template_name,
            'data' : {'nabl' : True}
        }
    def print_non_nabl_report(self):
        eln = self
        is_product_based = eln.is_product_based_calculation
        if is_product_based == True:
            template_name = eln.material.product_based_calculation[0].main_report_template.report_name
        else:
            template_name = eln.parameters_result.parameter[0].main_report_template.report_name
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': template_name,
            'report_file': template_name,
            'data' : {'nabl' : False}
        }

    @api.model
    def create(self,vals):
        if vals.get('eln_id', 'New') == 'New':
            vals['eln_id'] = self.env['ir.sequence'].next_by_code('lerm.eln.seq') or 'New'
            res = super(ELN, self).create(vals)
            return res




    @api.onchange('sample_id')
    def compute_kes_no(self):
        for record in self:
            if record.sample_id:
                sample_record = self.env['lerm.srf.sample'].search([('id','=', record.sample_id.id)]).kes_no
                record.kes_no = sample_record
            else:
                record.kes_no = None
    
    @api.onchange('sample_id')
    def compute_discipline(self):
        for record in self:
            if record.sample_id:
                sample_record = self.env['lerm.srf.sample'].search([('id','=', record.sample_id.id)]).discipline_id
                record.discipline = sample_record
            else:
                record.discipline = None

    @api.onchange('sample_id')
    def compute_group(self):
        for record in self:
            if record.sample_id:
                sample_record = self.env['lerm.srf.sample'].search([('id','=', record.sample_id.id)]).group_id
                record.group = sample_record
            else:
                record.group = None

    
    @api.onchange('sample_id')
    def compute_material(self):
        for record in self:
            if record.sample_id:
                sample_record = self.env['lerm.srf.sample'].search([('id','=', record.sample_id.id)]).material_id
                record.material = sample_record
            else:
                record.material = None

    @api.onchange('sample_id')
    def compute_witness(self):
        for record in self:
            if record.sample_id:
                sample_record = self.env['lerm.srf.sample'].search([('id','=', record.sample_id.id)]).witness
                record.witness_name = sample_record
            else:
                record.witness_name = None

    @api.onchange('sample_id')
    def compute_casting_date(self):
        for record in self:
            if record.sample_id:
                sample_record = self.env['lerm.srf.sample'].search([('id','=', record.sample_id.id)]).casting_date
                record.casting_date = sample_record
            else:
                record.casting_date = None

    @api.onchange('srf_id')
    def compute_srf_date(self):
        for record in self:
            if record.srf_id:
                srf_record = self.env['lerm.civil.srf'].search([('id','=', record.srf_id.id)]).srf_date
                record.srf_date = srf_record
            else:
                record.srf_date = None

class ParameteResultCalculationWizard(models.TransientModel):
    _name = 'parameter.calculation.wizard'
    parameter = fields.Many2one('lerm.parameter.master',string="Parameter")
    time_based = fields.Boolean("Time Based",compute="compute_is_time")
    inputs_lines = fields.One2many('input.line.wizard', 'wizard_id', string='Inputs')
    nabl_status = fields.Selection([
        ('nabl', 'NABL'),
        ('non-nabl', 'Non-NABL')
    ],compute="compute_nabl_status", string='NABL Status')
    conformity_status = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')
    ],compute="compute_conformity_status",string='Conformity Status')
    result = fields.Float(string="Result",compute="compute_result",digits=(16, 5))
    # result_char = fields.Char(string="Result")

    eln_state = fields.Selection([
        ('1-draft', 'In-Test'),
        ('2-confirm', 'In-Check'),
        ('3-approved','Approved'),
        ('4-rejected','Rejected')
    ], string='State',default='1-draft')

    result_editable = fields.Boolean('Editable',default=True,compute="_compute_result_editable")

    @api.depends('eln_state')
    def _compute_result_editable(self):
        state = self.eln_state
        current_user_groups = self.env.user.groups_id.ids
        hod_group_id = self.env.ref('lerm_civil.kes_hod_access_group').id

        if state != '1-draft' and hod_group_id not in current_user_groups:
            self.result_editable = False
        else:
            self.result_editable = True

    @api.depends('parameter')
    def compute_is_time(self):
        for rec in self:
            rec.time_based = rec.parameter.time_based

    @api.depends('result')
    def compute_conformity_status(self):
        for record in self:
            # import wdb;wdb.set_trace()
            material_table = self.parameter.parameter_table.filtered(lambda rec: rec.grade.id == self.env.context.get('grade_id') and rec.material.id == self.env.context.get('material_id') and rec.size.id == self.env.context.get('size_id'))
            req_min = material_table.req_min
            req_max = material_table.req_max
            mu_neg = record.result - record.result*record.parameter.mu_value

            mu_pos = record.result + record.result*record.parameter.mu_value

        
            if req_min <= mu_neg <= req_max and req_min <= mu_pos <= req_max:
                record.conformity_status = "pass"
            else:
                record.conformity_status = "fail"


    @api.depends('result')
    def compute_nabl_status(self):
        for record in self:
            if record.parameter.lab_min_value <= record.result <= record.parameter.lab_max_value:
                record.nabl_status = 'nabl'
            elif record.parameter.lab_min_value <= record.result and record.parameter.lab_max_value == 0:
                record.nabl_status = 'nabl'
            else:
                record.nabl_status = 'non-nabl'

    
    # old code imp
    def update_result(self):
        # import wdb; wdb.set_trace()
        result_id = self.env.context.get('result_id')
        result_id = self.env["eln.parameters.result"].search([('id','=',result_id)])
        self.env["eln.parameters.inputs"].search([('eln_id','=',self.env.context.get('eln_id'))])
        self.env["eln.parameters.inputs"].sudo().search([('eln_id','=',self.env.context.get('eln_id')),('inputs.label','=',self.parameter.parameter_name)]).write({'value':self.result})
        for input in self.inputs_lines:
            # import wdb; wdb.set_trace()
            self.env["eln.parameters.inputs"].search([('eln_id','=',self.env.context.get('eln_id')),('id','=',input.inputs_id.id)]).write({'value':input.value,'date_time':input.date_time})




        result_id.sudo().write({'result':self.result,'calculated':True,'nabl_status':self.nabl_status,'conformity_status':self.conformity_status})
        return {'type': 'ir.actions.act_window_close'}
    
    
                
    # def update_result(self):
    #     # Check if the result has already been updated
    #     if self.env.context.get('result_updated'):
    #         # If the result has already been updated, do nothing
    #         return {'type': 'ir.actions.act_window_close'}
        
    #     # Get the result ID from the context
    #     result_id = self.env.context.get('result_id')
    #     result = self.env["eln.parameters.result"].browse(result_id)

    #     # Update inputs in ELN
    #     self.env["eln.parameters.inputs"].sudo().search([('eln_id','=',self.env.context.get('eln_id')),('inputs.label','=',self.parameter.parameter_name)]).write({'value':self.result})
    #     for input in self.inputs_lines:
    #         self.env["eln.parameters.inputs"].search([('eln_id','=',self.env.context.get('eln_id')),('id','=',input.inputs_id.id)]).write({'value':input.value,'date_time':input.date_time})

    #     # Update result in SampleParametersResult
    #     sample_results = self.env['sample.parameters.result'].search([('parameter', '=', result.parameter.id)])
    #     sample_results.write({'result': result.result})
        
    #     # Update result in ELN
    #     result.write({'result':self.result,'calculated':True,'nabl_status':self.nabl_status,'conformity_status':self.conformity_status})

    #     # Create a mutable copy of the context and set a flag to indicate that the result has been updated
    #     context = dict(self.env.context)
    #     context['result_updated'] = True

    #     return {'type': 'ir.actions.act_window_close', 'context': context}


    # def update_result(self):
    #     if self.env.context.get('result_updated'):
    #         return {'type': 'ir.actions.act_window_close'}
        
        
    #     eln_id = self.env.context.get('eln_id')
    #     result_id = self.env.context.get('result_id')
    #     result = self.env["eln.parameters.result"].browse(result_id)
    #     sample_id = self.env["lerm.eln"].browse(eln_id).sample_id.id
        

    #     self.env["eln.parameters.inputs"].sudo().search([('eln_id','=',self.env.context.get('eln_id')),('inputs.label','=',self.parameter.parameter_name)]).write({'value':self.result})
    #     for input in self.inputs_lines:
    #         self.env["eln.parameters.inputs"].search([('eln_id','=',self.env.context.get('eln_id')),('id','=',input.inputs_id.id)]).write({'value':input.value,'date_time':input.date_time})

    #     sample_results = self.env['sample.parameters.result'].search([('sample_id','=',sample_id),('parameter', '=', result.parameter.id)])
    #     if not sample_results.filtered(lambda r: r.result == self.result):
    #         sample_results.write({'result': self.result})
        
    #     result.write({'result': self.result, 'calculated': True, 'nabl_status': self.nabl_status, 'conformity_status': self.conformity_status})

    #     context = dict(self.env.context)
    #     context['result_updated'] = True

    #     return {'type': 'ir.actions.act_window_close', 'context': context}
    # def calculate(self):
    #     values = {}
    #     for input in self.inputs_lines:
    #         values[input.identifier] = input.value
        

    #     result_id = self.env.context.get('result_id')
    #     result_id = self.env["eln.parameters.result"].search([('id','=',result_id)])
    #     result = safe_eval(result_id.parameter.formula, values)
    #     # import wdb; wdb.set_trace()
    #     self.write({'result':result})

    @api.depends('inputs_lines.value')
    def compute_result(self):
        for record in self:
            values = {
                        'datetime':datetime
                                            
                    }
            try:
                for input in self.inputs_lines:
                    if record.time_based:
                        values[input.identifier] = input.date_time
                    else:
                        values[input.identifier] = input.value

                
                result_id = self.env.context.get('result_id')
                result_id = self.env["eln.parameters.result"].search([('id','=',result_id)])
                result = safe_eval(result_id.parameter.formula, values)
                if record.time_based:
                    record.result = result.total_seconds() / 60
                else:
                    record.result = result
            except:
                record.result = 0
                pass

        # print(input)


class InputLines(models.TransientModel):
    _name = 'input.line.wizard'
    wizard_id = fields.Many2one('parameter.calculation.wizard', string='Wizard')
    inputs_id = fields.Many2one('eln.parameters.inputs', string='Inputs ID')
    parameter_result = fields.Many2one('eln.parameters.result',string="Parameter")
    is_parameter_dependent = fields.Boolean("Parameter Dependent")
    identifier = fields.Char(string="Identifier")
    inputs = fields.Many2one('lerm.dependent.inputs',string="Inputs")
    value = fields.Float(string="Value",digits=(12, 5))
    date_time = fields.Datetime("Time") 
    
    @api.onchange('value')
    def _onchange_value(self):
        decimal_digits_limit = self.inputs.decimal_place

        for record in self:
         
            formatted_number = self.remove_zeros_after_12_digits(record.value)
            print("formatted_number ================>",str(formatted_number))

            decimal_part = str(formatted_number).split('.')[1] if '.' in str(formatted_number) else ''
            print("================>",decimal_part)
            # if len(decimal_part) > decimal_digits_limit:
            #     raise ValidationError("Number of digits after decimal should not exceed %s." % decimal_digits_limit)


    def remove_zeros_after_12_digits(self,number):
        # Convert the number to a string
        number_str = str(number)

        # Split the string into the integer and decimal parts
        integer_part, decimal_part = number_str.split('.')

        # Remove zeros after 12 digits from the decimal point
        truncated_decimal_part = decimal_part[:12]

        # Combine the integer part and truncated decimal part
        result = f"{integer_part}.{truncated_decimal_part}"

        # Convert the result back to a floating-point number
        result_number = float(result)

        return result_number



  
                


class ELNSpreadsheet(models.Model):
    _name = 'eln.spreadsheets'
    _rec_name = 'datasheet'
    eln_id = fields.Many2one('lerm.eln',string="ELN ID")
    datasheet = fields.Many2one('documents.document',string="Datasheet")
    spreadsheet_template = fields.Many2one("spreadsheet.template",string="Spreadsheet Template")
    related_parameters = fields.Many2many("eln.parameters",string="Related Parameters")
    fill_datasheet = fields.Integer("Fill Spreadsheet")


class ELNParametersResult(models.Model):
    _name = 'eln.parameters.result'
    _rec_name = 'parameter'
    eln_id = fields.Many2one('lerm.eln',string="ELN ID")
    parameter = fields.Many2one('lerm.parameter.master',string="Parameter")
    unit = fields.Many2one('uom.uom',string="Unit")
    context_data = fields.Text("Context Data")
    calculated = fields.Boolean("Calculated")
    calculation_type = fields.Selection([('parameter_based', 'Parameter Based'), ('form_based', 'Form Based')],compute='_compute_calculation_type',string='Calculation Type')
    test_method = fields.Many2one('lerm_civil.test_method',string="Specification")
    specification_permissible_limit = fields.Text(string="Specification",compute='_compute_specification')
    specification = fields.Text(string="Test Method", compute='_compute_specification')


    nabl_status = fields.Selection([
        ('nabl', 'NABL'),
        ('non-nabl', 'Non-NABL')

    ], string='NABL Status')
    conformity_status = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')
    ],string='Conformity Status')
    model_id = fields.Integer(string="Model Id")
    result = fields.Float(string="Result",digits=(16,5))
    result_type = fields.Selection([
        ('char', 'Character'),
        ('number', 'Number')
    ],string='Result Type',default="number")
    result_char = fields.Char("Result")
    sequence = fields.Char("Sequence")

    


    # @api.depends('result')
    # def compute_nabl_status(self):
    #     for record in self:
    #         if record.parameter.lab_min_value <= record.result <= record.parameter.lab_max_value:
    #             record.nabl_status = 'nabl'
    #         elif record.parameter.lab_min_value <= record.result and record.parameter.lab_max_value == 0:
    #             record.nabl_status = 'nabl'
    #         else:
    #             record.nabl_status = 'non-nabl'

    @api.depends('parameter.calculation_type')
    def _compute_calculation_type(self):
        for record in self:
            record.calculation_type = record.parameter.calculation_type


    @api.depends('eln_id.material', 'eln_id.grade_id', 'eln_id.size_id','parameter')
    def _compute_specification(self):
        for record in self:
            # import wdb; wdb.set_trace()
            material_id = record.eln_id.material.id
            grade_id = record.eln_id.grade_id.id
            size_id = record.eln_id.size_id.id
            parameter_id = record.parameter.id
            parameter = record.parameter

            if parameter.fetch_by_grade and parameter.fetch_by_size and grade_id != False and size_id != False:
                try:
                    specification = record.env['lerm.parameter.master.table'].search([('material','=',material_id),('size','=',size_id),('grade','=',grade_id),('parameter_id','=',parameter_id)])[0].specification
                except:
                    specification = False
            elif parameter.fetch_by_grade and grade_id != False:
                try:
                    specification = record.env['lerm.parameter.master.table'].search([('material','=',material_id),('grade','=',grade_id),('parameter_id','=',parameter_id)])[0].specification
                except:
                    specification = False
            elif parameter.fetch_by_size and size_id != False:
                try:
                    specification = record.env['lerm.parameter.master.table'].search([('material','=',material_id),('size','=',size_id),('parameter_id','=',parameter_id)])[0].specification
                except:
                    specification = False
            else:
                try:
                    specification = record.env['lerm.parameter.master.table'].search([('material','=',material_id),('size','=',size_id),('grade','=',grade_id),('parameter_id','=',parameter_id)])[0].specification
                except:
                    specification = False
            print("specsi")
            print(specification)
            table_record = record.env['lerm.parameter.master.table'].search([('material','=',material_id),('size','=',size_id),('grade','=',grade_id),('parameter_id','=',parameter_id)])
            try:
                record.specification = specification
            except:
                record.specification = False

            if parameter.fetch_by_grade and parameter.fetch_by_size and grade_id != False and size_id != False:
                try:
                    specification_permissible_limit = record.env['lerm.parameter.master.table'].search([('material','=',material_id),('size','=',size_id),('grade','=',grade_id),('parameter_id','=',parameter_id)])[0].permissable_limit
                except:
                    specification_permissible_limit = False
            elif parameter.fetch_by_grade and grade_id != False:
                try:    
                    specification_permissible_limit = record.env['lerm.parameter.master.table'].search([('material','=',material_id),('grade','=',grade_id),('parameter_id','=',parameter_id)])[0].permissable_limit
                except:
                    specification_permissible_limit = False
            elif parameter.fetch_by_size and size_id != False:
                try:
                
                    specification_permissible_limit = record.env['lerm.parameter.master.table'].search([('material','=',material_id),('size','=',size_id),('parameter_id','=',parameter_id)])[0].permissable_limit
                except:
                    specification_permissible_limit = False
            else:
                try:
                    specification_permissible_limit = record.env['lerm.parameter.master.table'].search([('material','=',material_id),('size','=',size_id),('grade','=',grade_id),('parameter_id','=',parameter_id)])[0].permissable_limit
                except:
                    specification_permissible_limit = False
            try:
                record.specification_permissible_limit = specification_permissible_limit
            except:
                record.specification_permissible_limit = False
            print("permisss")
            print(specification_permissible_limit)

    # @api.depends('eln_id.material', 'eln_id.grade_id', 'eln_id.size_id','parameter')
    # def _compute_specification(self):
    #     for record in self:
    #         # import wdb; wdb.set_trace()
    #         material_id = record.eln_id.material.id
    #         grade_id = record.eln_id.grade_id.id
    #         size_id = record.eln_id.size_id.id
    #         parameter_id = record.parameter.id
    #         specification = self.env['lerm.parameter.master.table'].search([('material','=',material_id),('size','=',size_id),('grade','=',grade_id),('parameter_id','=',parameter_id)]).specification
    #         print("specsi")
    #         print(specification)
    #         table_record = self.env['lerm.parameter.master.table'].search([('material','=',material_id),('size','=',size_id),('grade','=',grade_id),('parameter_id','=',parameter_id)])
    #         record.specification = specification
    #         record.specification_permissible_limit = table_record.permissable_limit

    def open_form(self):
        # import wdb; wdb.set_trace()
        if self.model_id != 0:
            return {
                'view_mode': 'form',
                'res_model': self.parameter.ir_model.model,
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.model_id,
                'context': {
                    'default_srf_id':self.eln_id.srf_id.id,
                    'default_sample_id': self.eln_id.sample_id.id,
                    'default_parameter_id':self.id,
                    'default_eln_ref':self.eln_id.id
                 }
            }
        else:
            return {
                'view_mode': 'form',
                'res_model': self.parameter.ir_model.model,
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': {
                    'default_srf_id':self.eln_id.srf_id.id,
                    'default_sample_id': self.eln_id.sample_id.id,
                    'default_parameter_id':self.id,
                    'default_eln_ref':self.eln_id.id

                 }
                }
        
    



    def open_calculation_wizard(self):
        # wizard = self.env['parameter.calculation.wizard'].create({})
        action = self.env.ref('lerm_civil.parameter_calculation_wizard')

        inputs =self.env["eln.parameters.inputs"].search([("eln_id","=",self.eln_id.id),("parameter_result","=",self.id)])
        parameters_inputs=[]
        for input in inputs:
            # import wdb; wdb.set_trace()
            parameters_input = (0,0,{'inputs_id':input.id,'parameter_result':input.parameter_result.id,"is_parameter_dependent":input.is_parameter_dependent,'identifier':input.identifier,'inputs':input.inputs.id,'value':input.value})
            parameters_inputs.append(parameters_input)
        # import wdb; wdb.set_trace()


        return {
            'name': "Calculation",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'parameter.calculation.wizard',
            'view_id': action.id,
            'target': 'new',
            'context':{
                'default_parameter':self.parameter.id,
                'default_inputs_lines': parameters_inputs,
                'material_id':self.eln_id.material.id,
                'size_id':self.eln_id.size_id.id,
                'grade_id':self.eln_id.grade_id.id,
                'result_id':self.id,
                'eln_id':self.eln_id.id,
                'eln_state':self.eln_id.state
            }
            }


    
    

class ELNParametersInputs(models.Model):
    _name = 'eln.parameters.inputs'
    eln_id = fields.Many2one('lerm.eln',string="ELN ID")
    parameter_result = fields.Many2one('eln.parameters.result',string="Parameter")
    is_parameter_dependent = fields.Boolean("Parameter Dependent")
    identifier = fields.Char(string="Identifier")
    inputs = fields.Many2one('lerm.dependent.inputs',string="Inputs")
    value = fields.Float(string="Value",digits=(12, 5))
    date_time = fields.Datetime("Time") 






class ELNParameters(models.Model):
    _name = 'eln.parameters'
    _rec_name = 'parameter'
    eln_id = fields.Many2one('lerm.eln',string="ELN ID")
    parameter = fields.Many2one('lerm.parameter.master',string="Parameter")
    specification = fields.Text(string="Specification")
    test_method = fields.Many2one('lerm_civil.test_method',compute="compute_method",string="Test Method")
    datasheet = fields.Many2one('documents.document',string="Datasheet")
    result = fields.Float(string="Result")
    button = fields.Float(string="Button")
    result_json = fields.Text(string="Result JSON")
    spreadsheet_template = fields.Many2one("spreadsheet.template",string="Spreadsheet Template")
    set_result_button = fields.Float(string="Button")


    def set_result(self):
        binary_data = base64.b64decode(self.datasheet.datas)
        json_data = json.loads(binary_data.decode('utf-8'))
        print(json_data)
        # sheet_name = self.parameter.sheets
        # cell = self.parameter.cell
        # filtered_sheet = next((sheet for sheet in json_data["sheets"] if sheet["name"] == sheet_name), None)
        # if filtered_sheet:
        #     print(filtered_sheet)

        
    @api.depends('parameter')
    def compute_method(self):
        for record in self:
            record.test_method = record.parameter.test_method.id

    

class UpdateResult(models.TransientModel):
    _name = 'eln.update.result.wizard'

    results = fields.One2many('eln.result.child','wizard_id',string="Parameters")



    def update_result(self):
        print("working")



class UpdateResultChild(models.TransientModel):
    _name ="eln.result.child"
    wizard_id = fields.Many2one('eln.update.result.wizard')
    parameter = fields.Many2one('eln.parameters',string="Parameter")
    result = fields.Float(string="Result")






