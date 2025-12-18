from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import logging
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta, date

# _logger = logging.getLogger(__name__)



class LermSampleForm(models.Model):
    _name = "lerm.srf.sample"
    _inherit = ['mail.thread','mail.activity.mixin']

    _description = "Sample"
    _rec_name = 'kes_no'

    client_reference1 = fields.Char(string="Client Reference",compute="_compute_client_reference", store=True)
    srf_id = fields.Many2one('lerm.civil.srf',ondelete="cascade", string="SRF ID" ,tracking=True)
    sample_range_id = fields.Many2one('sample.range.line',string="Sample Range")
    eln_id = fields.Many2one('lerm.eln',string="ELN",ondelete="set null")
    sample_no = fields.Char(string="Sample ID." ,required=True,readonly=True, default=lambda self: 'New')
    casting = fields.Boolean(string="Casting")
    discipline_id = fields.Many2one('lerm_civil.discipline',string="Discipline")
    lab_no_value = fields.Char(string="Value")
    group_id = fields.Many2one('lerm_civil.group',string="Group")
    # department_id = fields.Many2one('hr.department', string='Department')
    department_id = fields.Char(string='Department')
    material_id = fields.Many2one('product.template',string="Material")
    material_id_lab_name = fields.Char(string="Material",compute="compute_material_id_lab_name",store=True)
    ulr_no = fields.Char(string="ULR No." ,readonly=True, default=lambda self: 'New')
    brand = fields.Char(string="Brand")
    size_id = fields.Many2one('lerm.size.line',string="Size")
    grade_id = fields.Many2one('lerm.grade.line',string="Grade")
    # qty_id = fields.Many2one('lerm.qty.line',string="Quantity")
    sample_qty = fields.Integer(string="Sample Quantity")
    received_by_id = fields.Many2one('res.partner',string="Received By")
    sample_received_date = fields.Date(string="Sample Received Date")
    sample_condition = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non_satisfactory', 'Non-Satisfactory'),
    ], string='Sample Condition', default='satisfactory')
    technicians = fields.Many2one("res.users",string="Technicians",tracking=5)
    location = fields.Char(string="Location")
    sample_reject_reason = fields.Char(string="Sample Reject Reason")
    has_witness = fields.Boolean(string="Witness")
    witness = fields.Char(string="Witness Name")
    scope = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),
    ], string='Scope', default='nabl')
    sample_description = fields.Text(string="Sample Description")
    source_sample = fields.Char(string="Source of Sample")
    group_ids = fields.Many2many('lerm_civil.group',string="Group Ids",compute="compute_group_ids")
    material_ids = fields.Many2many('product.template',string="Material Ids",compute="compute_material_ids")
    size_ids = fields.Many2many('lerm.size.line',string="Size Ids",compute="compute_size_ids")
    grade_ids = fields.Many2many('lerm.grade.line',string="Grade Ids",compute="compute_grade_ids")
    qty_ids = fields.Many2many('lerm.qty.line',string="Qty Ids",compute="compute_qty_ids")
    days_casting = fields.Selection([
        ('1', '1 Days'),
        ('3', '3 Days'),
        ('7', '7 Days'),
        ('14', '14 Days'),
        ('21', '21 Days'),
        ('28', '28 Days'),
        ('45', '45 Days'),
        ('56', '56 Days'),
        ('112', '112 Days'),
    ], string='Days of casting', default='3')
    date_casting = fields.Date("Date of Casting")
    customer_id = fields.Many2one('res.partner' , string="Customer")
    alias = fields.Char(string="Alias")
    product_alias = fields.Many2one('product.product',string="Product Alias")
    parameters = fields.Many2many('lerm.parameter.master',string="Parameter")
    kes_no = fields.Char("UID",required=True,readonly=True, default=lambda self: 'New' ,tracking=True)
    casting_date = fields.Date(string="Casting Date")
    client_sample_id = fields.Char(string='Client Sample ID')
    filled_by = fields.Many2one('res.users',string="Filled By")
    check_by = fields.Many2one('res.users',string="Check By")
    approved_by = fields.Many2one('res.users',string="Approved By")
    checkby_signature_required = fields.Boolean("Checked by Signature")
    approveby_signature_required = fields.Boolean("Approved by Signature")
    testedby_signature_required = fields.Boolean("Tested by Signature")
    page_break = fields.Integer("Page break",default=6)

    active = fields.Boolean(string="Active",default=True)

    invoice_number = fields.Many2one(
        'account.move',  
        string="Invoice Number",  
        help="Select the invoice number",  
        domain="[('move_type', '=', 'out_invoice')]",  
       
        store=True
    )

    invoice_status = fields.Selection([
        ('1-uninvoiced', 'Uninvoiced'),
        ('2-invoiced', 'Invoiced'),
        ('3-closed', 'Closed'),
    ], string='Invoice Status',  store=True, default='1-uninvoiced')

    print_button_visible = fields.Boolean("Print Nabl visible",compute="_compute_print_nabl_visible")
   
    lab_location = fields.Many2one('lerm.lab.master',string="Lab Location")
    location_name = fields.Many2one('lerm.lab.location.master',string="Location Name")

    file_upload = fields.Many2many(
        'ir.attachment',
        'lerm_file_upload_rel',
        'sample_id',
        'attachment_id',
        string='Datasheet Upload',
        help='Attach multiple images to the sample',
    )
    
    
    report_upload = fields.Many2many(
        'ir.attachment',
        'lerm_report_upload_rel',
        'sample_id',
        'attachment_id',
        string='Report Upload',
        help='Attach multiple images to the sample',
    )
        


    status = fields.Selection([
        ('1-pending', 'Pending'),
        ('2-confirmed', 'Confirmed'),
    ], string='Status', default='1-pending')

    state = fields.Selection([
        ('1-allotment_pending', 'Assignment Pending'),
        ('2-alloted', 'Alloted'),
        ('3-pending_verification','Pending Verification'),
        ('5-pending_approval','Pending Approval'),
        ('4-in_report', 'In-Report'),
        ('6-cancelled', 'Cancelled'),
    ], string='State',default='1-allotment_pending')
    conformity = fields.Boolean(string="Conformity")
    parameters_result = fields.One2many('sample.parameters.result','sample_id',string="Parameters Result")
    volume = fields.Char(string="Volume")
    product_name = fields.Many2one('product.template',string="Product Name")
    main_name = fields.Char(string="Product Name")
    price = fields.Float(string="Price")
    product_or_form_based = fields.Boolean("Product or Form Based",compute="compute_form_product_based")
    
    cancellation_reason = fields.Selection([
        ('software_error', 'Software Error'),
        ('work_cancelled', 'Work has been Cancelled'),
        ('out_of_scope', 'Out of Scope'),
        ('other', 'Other'),


    ])
    other_cancellation_reason = fields.Text("Cancellation Reason")
    
    tested_by_signature_datasheet = fields.Boolean(string="Tested By Signature Datasheet")
    checked_by_signature_datasheet = fields.Boolean(string="Checked By Signature Datasheet")

    quantity = fields.Integer(string="Quantity")
    # lab_id = fields.Char( string="Lab ID",readonly=True,tracking=True,store=True )
    lab_id = fields.Char(
        string="Lab ID",
        readonly=True,
        tracking=True,
        store=True,
        compute="_compute_lab_id"
       
    )

    lab_ids_raw = fields.Char()


    def _get_lab_sequence_code(self, product):
        mapping = {
            'Burnt Clay Bricks': 'lerm.eln.bric',
            'Aggregate - Coarse': 'lerm.eln.coag',
            'CEMENT MECHANICAL OPC': 'lerm.eln.cemt',
            'CEMENT MECHANICAL PPC': 'lerm.eln.cemt',
            'Fine Aggregate': 'lerm.eln.fiag',
            'Fly Ash': 'lerm.eln.flas',
            'GGBS': 'lerm.eln.ggbs',
            'PAVER BLOCK': 'lerm.eln.pvlb',
            'ROCK': 'lerm.eln.rock',
            'Soil': 'lerm.eln.soil',
            'Stone': 'lerm.eln.ns',
            'Fly Ash Bricks': 'lerm.eln.fab',
            'Concrete Cubes Compressive Strength': 'lerm.eln.conc',
        }
        return mapping.get(product.name) if product else False

    # --------------------
    # COMPUTE (🔥 CONSUME SEQUENCE HERE)
    # --------------------
    @api.depends('material_id', 'quantity')
    def _compute_lab_id(self):
        for rec in self:
            rec.lab_id = False
            rec.lab_ids_raw = False

            if not rec.material_id or rec.quantity <= 0:
                continue

            # prevent double consume
            if rec.lab_ids_raw:
                continue

            seq_code = rec._get_lab_sequence_code(rec.material_id)
            if not seq_code:
                continue

            ids = []
            for i in range(rec.quantity):
                lab = rec.env['ir.sequence'].next_by_code(seq_code)
                if not lab:
                    break
                ids.append(lab)

            if not ids:
                continue

            # ✅ store consumed IDs
            rec.lab_ids_raw = ','.join(ids)

            # preview
            if len(ids) == 1:
                rec.lab_id = ids[0]
            else:
                rec.lab_id = f"{ids[0]} - {ids[-1]}"


    def action_create_sample(self):
        self.ensure_one()

        if not self.lab_ids_raw:
            return

        ids = self.lab_ids_raw.split(',')

        lines = [{
            'srf_id': self.srf_id.id,
            'material_id': self.material_id.id,
            'lab_id': lab,
        } for lab in ids]

        self.env['lerm.srf.sample'].create(lines)

        return {'type': 'ir.actions.act_window_close'}

    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")  # kg, mm, etc.
    quantity_received = fields.Integer(string="Quantiyty Received")
    quantity_consumed = fields.Integer(string="Quantity Consumed")
    quantity_discarded = fields.Integer(string="Quantity Discarded")
    quantity_balance = fields.Integer(string="Quantity Balance", compute="compute_quantity_balance", readonly=True)

    resampled = fields.Boolean("Resampled")
    report_issued_date = fields.Date("Report Issued Date")

    display_report_portal = fields.Boolean("Display on Portal")
    customer_portal_sample = fields.Many2one('customer.sample.line',string="Customer Portal Sample", readonly=True)

    @api.depends('quantity_received', 'quantity_consumed','quantity_discarded')
    def compute_quantity_balance(self):
        for rec in self:
            rec.quantity_balance = rec.quantity_received - rec.quantity_consumed - rec.quantity_discarded

            
    
    
    
    
    @api.depends('srf_id.client_refrence')
    def _compute_client_reference(self):
        for record in self:
            record.client_reference1 = record.srf_id.client_refrence




    @api.depends('scope','state')
    def _compute_print_nabl_visible(self):
        for record in self:
            if record.scope == 'nabl' and record.state == '4-in_report':
                record.print_button_visible = True
            else:
                record.print_button_visible =  False


    def cancel_sample(self):
        # import wdb;wdb.set_trace()
        eln_id = self.env['lerm.eln'].sudo().search([('sample_id','=',self.id)],limit=1)
        if eln_id:
            eln_id.write({'state':'5-cancelled'})

        action = self.env.ref('lerm_civil.sample_rejection_wizard')
        return {
            'name': "Cancel Sample",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sample.cancellation.wizard',
            'view_id': action.id,
            'target': 'new',
            'context':{
                'default_sample': self.id,
                }
            }

        


    def edit_sample(self):
        

        # samples = self.env["lerm.srf.sample"].search([("srf_id","=",self.id)])
        action = self.env.ref('lerm_civil.srf_sample_wizard_form')
        return {
            'name': "Edit Sample",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.srf.sample.wizard',
            'view_id': action.id,
            'target': 'new',
            'context':{
                'default_edit_mode': True, 
                'default_sample': self.id,
                'default_is_update':True,
                'default_parameters':self.parameters.ids,
                'default_discipline_id': self.discipline_id.id,
                'default_group_id': self.group_id.id,
                'default_material_id': self.material_id.id,
                'default_brand': self.brand,
                'default_size_id': self.size_id.id,
                'default_grade_id': self.grade_id.id,
                'default_sample_qty': self.sample_qty,
                'default_received_by_id': self.received_by_id.id,
                'default_sample_received_date':self.sample_received_date,
                'default_sample_condition':self.sample_condition,

                'default_sample_reject_reason': self.sample_reject_reason,
                'default_location': self.location,
                'default_received_by_id': self.received_by_id.id,
                'default_sample_received_date':self.sample_received_date,

                'default_witness':self.witness,
                'default_scope':self.scope,
                'default_sample_description':self.sample_description,
                'default_client_sample_id':self.client_sample_id,
                'default_days_casting':self.days_casting,
                'default_casting':self.casting,


                'default_date_casting':self.date_casting,
                'default_customer_id':self.customer_id.id,
                # 'default_product_aliases':self.product_aliases.ids,

                'default_product_alias':self.product_alias.id,
                'default_conformity':self.conformity,
                'default_product_name':self.product_name.id,
                # 'default_pricelist':self.pricelist.id,
                'default_main_name':self.main_name,
                'default_price':self.price,
                }
            }

    


    @api.depends('state')
    def compute_form_product_based(self):
        for record in self:

            record.product_or_form_based = True
            print("SAMPLE STATE",record.state)
            if record.state != '1-allotment_pending':
                eln_id = self.env['lerm.eln'].sudo().search([('sample_id','=',record.id)])
                if eln_id and eln_id.parameters_result:  # Check if eln_id and parameters_result are not empty
                    print("DATA",eln_id.parameters_result)
                    is_product_based = eln_id.is_product_based_calculation
                    is_form_based = eln_id.parameters_result[0].calculation_type == "form_based"
                    if is_product_based or is_form_based:
                        record.product_or_form_based = True
                        record.parameters_result.write({'verified':True})
                    else:
                        record.product_or_form_based = False
            else:
                record.product_or_form_based = False

    @api.depends('material_id')
    def compute_material_id_lab_name(self):
        for record in self:
            record.material_id_lab_name = record.material_id.lab_name


    def open_form(self):

        eln = self.env['lerm.eln'].sudo().search([('sample_id','=',self.id)])
        if self.product_or_form_based:
            if eln.is_product_based_calculation:
                model_record = self.env['lerm.product.based.calculation'].sudo().search([('product_id','=',eln.material.id),('grade','=',eln.grade_id.id)])
                model = model_record.ir_model.model
                return {
                        'view_mode': 'form',
                        'res_model': model,
                        'type': 'ir.actions.act_window',
                        'target': 'current',
                        'res_id': eln.model_id,
                        }
            else:
                if eln.parameters_result[0].calculation_type == 'form_based':
                    model = eln.parameters_result[0].parameter.ir_model.model
                    print(model)
                    return {
                        'view_mode': 'form',
                        'res_model': model,
                        'type': 'ir.actions.act_window',
                        'target': 'current',
                        'res_id': eln.parameters_result[0].model_id,
                        }
                    


    def open_related_eln(self):

        #  self.env['lerm.eln'].search()
        # import wdb ; wdb.set_trace()
        # Assuming you want to open a record in the 'res.partner' model
        eln_id = self.env['lerm.eln'].sudo().search([('sample_id','=',self.id)]).id  # Replace with the actual ID of the record you want to open

        eln = self.env['lerm.eln'].browse(eln_id)

        if eln:
            # Open the record in a form view
            return {
                'name': eln.eln_id,
                'view_mode': 'form',
                'res_model': 'lerm.eln',
                'res_id': eln.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
            }
        else:
            raise UserError('ELN record not found!')




    @api.onchange('material_id')
    def compute_parameters(self):
        for record in self:
            if record.material_id:
                parameters_ids = []
                product_records = self.env['product.template'].search([('id','=', record.material_id.id)]).parameter_table1
                for rec in product_records:
                    parameters_ids.append(rec.id)
                domain = {'parameters': [('id', 'in', parameters_ids)]}
                return {'domain': domain}
            else:
                domain = {'parameters': [('id', 'in', [])]}
                return {'domain': domain}

    # def open_bulk_allotment_wizard(self):
    #     print("Workign")


    def approve_sample(self):
        for result in self.parameters_result:
            self.check_by = self.env.user
            if not result.verified:
                raise ValidationError("Not all parameters are verified. Please ensure all parameters are verified before proceeding.")
        self.write({
            'state': '5-pending_approval',
            'checked_by_signature_datasheet':True
                          
                          }),
       
        # eln = self.env['lerm.eln'].search([('sample_id','=',self.id)])
        # eln.write({'state':'3-approved'})


    # def approve_pending_sample(self):
    #     for result in self.parameters_result:
    #         self.approved_by = self.env.user
    #         if not result.verified:
    #             raise ValidationError("Not all parameters are verified. Please ensure all parameters are verified before proceeding.")
    #     if len(self.file_upload) > 0:
    #         self.write({'state': '4-in_report'})
    #         eln = self.env['lerm.eln'].sudo().search([('sample_id','=',self.id)])
    #         approved_by = self.env.user
    #         eln.write({'state':'3-approved'})
    #     else:
    #         raise ValidationError("Please attach datasheet before submitting")

    def approve_pending_sample(self):
        for result in self.parameters_result:
            if not result.verified:
                raise ValidationError("Not all parameters are verified. Please ensure all parameters are verified before proceeding.")
        
        if not self.datasheet_path:
            raise ValidationError("Please attach datasheet before submitting.")
        import wdb ; wdb.set_trace()
        
        sample_register = self.env['lerm.sample.register'].sudo().search([('sample','=',self.id)])
        try:
            sample_register.sudo().write({
                'report_issued_date':date.today()
            })
        except:
            print('Sample Register Not Updated')
            
        self.approved_by = self.env.user
        self.write({'state': '4-in_report'})
        
        eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', self.id)])
        eln.write({'state': '3-approved'})

        

    # def reject_pending_sample(self):
    #     self.write({'state': '2-alloted'})
    #     eln = self.env['lerm.eln'].search([('sample_id','=',self.id)])
    #     eln.write({'state':'1-draft'})



    def reject_sample(self):
        # self.write({'state': '2-alloted'})
        # eln = self.env['lerm.eln'].search([('sample_id','=',self.id)])
        # eln.write({'state':'4-rejected'})

        action = self.env.ref('lerm_civil.sample_reject_wizard')
        return {
            'name': "Reject Sample",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sample.reject.wizard',
            'view_id': action.id,
            'target': 'new'
            }
    
    def reallocate_sample(self):
        # import wdb ; wdb.set_trace()
        action = self.env.ref('lerm_civil.sample_reallocation_wizard')
        return {
            'name': "Reallocate",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sample.reallocation.wizard',
            'view_id': action.id,
            'target': 'new'
            }

    def send_mail_action(self):
        # import wdb ; wdb.set_trace()
        action = self.env.ref('lerm_civil.send_mail_wizard')
        return {
            'name': "Send Mail",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'send.mail.wizard',
            'view_id': action.id,
            'target': 'new'
            }

    def print_datasheet(self):
        eln = self.env["lerm.eln"].sudo().search([('sample_id','=', self.id)])
        is_product_based = eln.is_product_based_calculation
        if is_product_based == True:
            template_name = eln.material.product_based_calculation[0].datasheet_report_template.report_name
        else:
            template_name = eln.parameters_result.parameter[0].datasheet_report_template.report_name
        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': template_name,
            'report_file': template_name,
            'data' : {'fromsample' : True}
        }
        
    def print_nabl_report(self):
        inreport = self.state
        eln = self.env["lerm.eln"].sudo().search([('sample_id','=', self.id)])
        is_product_based = eln.is_product_based_calculation
        if is_product_based == True:
            template_name = eln.material.product_based_calculation[0].main_report_template.report_name
        else:
            template_name = eln.parameters_result.parameter[0].main_report_template.report_name
        # import wdb ; wdb.set_trace()
        return {
            # 'name':str(self.kes_no),
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': template_name,
            'report_file': template_name,
            'data' : {'fromsample' : True , 'inreport' : inreport , 'nabl' : True,'fromEln':False}
        }
    def print_non_nabl_report(self):
        inreport = self.state
        eln = self.env["lerm.eln"].sudo().search([('sample_id','=', self.id)])
        is_product_based = eln.is_product_based_calculation
        if is_product_based == True:
            template_name = eln.material.product_based_calculation[0].main_report_template.report_name
        else:
            template_name = eln.parameters_result.parameter[0].main_report_template.report_name
        print("Template name",template_name)

        return {
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': template_name,
            'report_file': template_name,
            'data' : {'fromsample' : True , 'inreport' : inreport , 'nabl' : False,'fromEln':False}
        }

    
    # def print_sample_report(self):
    #     eln = self.env["lerm.eln"].search([('sample_id','=', self.id)])
    #     is_product_based = eln.is_product_based_calculation
    #     model_record = eln.material.product_based_calculation.filtered(lambda r: r.grade.id == eln.grade_id.id)
        
    #     if is_product_based:
    #         template_name = model_record.main_report_template.report_name
    #         return {
    #         'type': 'ir.actions.report',
    #         'report_type': 'qweb-pdf',
    #         'report_name': template_name,
    #         'report_file': template_name
    #         }
    #     else:
    #         template_name = eln.parameters_result.parameter[0].main_report_template.report_name
    #         return {
    #         'type': 'ir.actions.report',
    #         'report_type': 'qweb-pdf',
    #         'report_name': template_name,
    #         'report_file': template_name
    #         }



        # sample = self
        # # print(self.kes_no , 'UID of self')

        # template_name = sample.parameters_result.parameter[0].datasheet_report_template.report_name

        # report = self.env.ref('lerm_civil.sample_report_action')
        # report_action = report.report_action(self)
        # import wdb;wdb.set_trace()
        # Generate the report and retrieve the file content
        # report_data = report.render_qweb_pdf(self.ids)[0]
        # report_name = report.filename

        # Return the report as a file to be downloaded or printed
        # dynamic_part = "sample_report_template"
        # dynamic_part = "10per_fine_coarse_agg_mechanical"

        # report_name = f"lerm_civil.{dynamic_part}"
        
        # return {
        #     'type': 'ir.actions.report',
        #     'report_type': 'qweb-pdf',
        #     'report_name': template_name,
        #     'report_file': template_name
        # }
        # return self.env.ref('lerm_civil.sample_report_action').report_action(self)

    def open_sample_allotment_wizard(self):
        
        action = self.env.ref('lerm_civil.srf_sample_allotment_wizard')
        return {
            'name': "Allot Sample",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sample.allotment.wizard',
            'view_id': action.id,
            'target': 'new'
            }


    # @api.model
    # def create(self, vals):
    #     if vals.get('sample_no', 'New') == 'New' and vals.get('kes_no', 'New') == 'New':
    #         vals['sample_no'] = self.env['ir.sequence'].next_by_code('lerm.srf.sample') or 'New'
    #         vals['kes_no'] = self.env['ir.sequence'].next_by_code('lerm.srf.sample.kes') or 'New'
    #         res = super(LermSampleForm, self).create(vals)
    #         return res


    # @api.depends('material_id')
    # def compute_param_ids(self):
    #     for record in self:
    #         parameters_ids = self.env['lerm.datasheet.line'].search([('datasheet_id','=', record.material_id.data_sheet_format_no.id)])
    #         print("sas",parameters_ids)
    #         record.parameters_ids = parameters_ids
                

    @api.onchange('material_id.casting_required','material_id')
    def onchange_material_id(self):
        for record in self:
            if record.material_id.casting_required:
                record.casting = True
            else:
                record.casting = False

    @api.onchange('material_id.alias' ,'customer_id', 'material_id')
    def onchange_material_id(self):
        for record in self:
            result = self.env['lerm.alias.line'].search([('customer', '=', record.customer_id.id),('product_id', '=', record.material_id.id)])
            try:
                record.alias = result.alias
            except:
                record.alias = None




    @api.depends('discipline_id')
    def compute_group_ids(self):
        for record in self:
            group_ids = self.env['lerm_civil.group'].search([('discipline','=', record.discipline_id.id)])
            record.group_ids = group_ids

    @api.depends('discipline_id' , 'group_id')
    def compute_material_ids(self):
        for record in self:
            if record.discipline_id and record.group_id:
                material_ids = self.env['product.template'].search([('discipline','=', record.discipline_id.id) , ('group','=', record.group_id.id)])
                record.material_ids = material_ids
            else:
                record.material_ids = None

    @api.depends('material_id')
    def compute_size_ids(self):
        for record in self:
            if record.material_id:
                size_ids = self.env['lerm.size.line'].search([('product_id','=', record.material_id.id)])
                record.size_ids = size_ids
            else:
                record.size_ids = None

    @api.depends('material_id')
    def compute_grade_ids(self):
        for record in self:
            if record.material_id:
                grade_ids = self.env['lerm.grade.line'].search([('product_id','=', record.material_id.id)])
                record.grade_ids = grade_ids
            else:
                record.grade_ids = None

    @api.depends('material_id')
    def compute_qty_ids(self):
        for record in self:
            if record.material_id:
                qty_ids = self.env['lerm.qty.line'].search([('product_id','=', record.material_id.id)])
                record.qty_ids = qty_ids
            else:
                record.qty_ids = None


class SampleParameter(models.Model):
    _name = "lerm.srf.sample.parameter"
    _description = "Sample Parameter"
    sample_id = fields.Many2one('',string="Sample Id")
    product_id = fields.Many2one('product.template' , string="Product Id")
    paramter = fields.Many2one('lerm.parameter.master' , string="Parameter")


class RejectSampleWizard(models.Model):
    _name = 'sample.reject.wizard'

    sample_id = fields.Many2one('lerm.srf.sample',string="Sample")
    reject_reason = fields.Char('Reject Reason')


    def reject_sample_button(self):
        # return {'type': 'ir.actions.act_window_close'}
        if self.reject_reason:
            sample_id = self.env.context.get('active_id')
            sample = self.env['lerm.srf.sample'].search([('id','=',sample_id)]).write({'state': '2-alloted'})
            eln = self.env['lerm.eln'].sudo().search([('sample_id','=',sample_id)])
            eln.write({'state':'4-rejected'})
            eln.message_post(body="<b>Sample Rejected :<b> " + self.reject_reason)

            

            return {'type': 'ir.actions.act_window_close'}
        else:
            raise UserError("Please Specify Reject Reason")

    def close_reject_wizard(self):
        return {'type': 'ir.actions.act_window_close'}


class SampleParametersResult(models.Model):
    _name = 'sample.parameters.result'
    _rec_name = 'parameter'
    sample_id = fields.Many2one('lerm.srf.sample',string="Sample ID")
    parameter = fields.Many2one('lerm.parameter.master',string="Parameter")
    unit = fields.Many2one('uom.uom',string="Unit")
    test_method = fields.Many2one('lerm_civil.test_method',string="Test Method")
    specification = fields.Text(string="Specification")
    verified = fields.Boolean("Verified")
    result = fields.Float(string="Result",digits=(12, 5))


# 