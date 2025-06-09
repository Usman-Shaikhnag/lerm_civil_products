from odoo import api, fields, models,_
from odoo.exceptions import UserError
import logging



class SRFEditWizard(models.TransientModel):
    _name = "edit.lerm.civil.srf"
    _description = 'Edit SRF Header Wizard'
    
    
    srf_id = fields.Many2one('lerm.civil.srf',string="SRF ID")
    kes_number = fields.Char(string="KES No")
    # job_no = fields.Char(string="Job NO.")
    srf_date = fields.Date(string="SRF Date",default=lambda self: self._get_default_date())
    job_date = fields.Date(string="JOB Date")
    customer = fields.Many2one('res.partner',string="Customer",tracking=True)
    billing_customer = fields.Many2one('res.partner',string="Billing Customer")
    contact_person = fields.Many2one('res.partner',string="Contact Person")
    client = fields.Char("Client")
    # site_address = fields.Many2one('res.partner',string="Site Address")
    site_address = fields.Char(string="Site Address",compute="_compute_site_address")
    name_work = fields.Many2one('res.partner.project',string="Name of Work")
    name_works = fields.Many2many('res.partner.project',string="Name of Work",compute="_compute_name_work")

    client_refrence = fields.Char(string="Client Reference Letter")
    samples = fields.One2many('lerm.srf.sample' , 'srf_id' , string="Samples",tracking=True)
    contact_other_ids = fields.Many2many('res.partner',string="Other Ids",compute="compute_other_ids")
    contact_contact_ids = fields.Many2many('res.partner',string="Contact Ids",compute="compute_contact_ids")
    contact_site_ids = fields.Many2many('res.partner',string="Site Ids",compute="compute_site_ids")
    contractor = fields.Many2one('lerm.contractor.line',string="Contractor")
    contractor_ids = fields.Many2many('lerm.contractor.line')
    attachment = fields.Binary(string="Attachment")
    attachment_name = fields.Char(string="Attachment Name")
    
    
    
    def update_sample_header(self):
        
        self.srf_id.write({
            'customer': self.customer.id,
            'srf_date': self.srf_date,
            'client': self.client,
            'contact_person': self.contact_person.id,
            'contractor': self.contractor.id,
            'billing_customer': self.billing_customer.id,
            'client_refrence': self.client_refrence,
            'name_work': self.name_work.id,
            'attachment':self.attachment,
            'attachment_name':self.attachment_name
        })
        samples = self.env['lerm.civil.srf'].search([("id","=",self.srf_id.id)]).samples
        for sample in samples:
            sample.write({
                'customer_id': self.customer.id
                # 'sample_received_date':self.srf_date
            })
        
    
    
    @api.model
    def _get_default_date(self):
        previous_record = self.search([], limit=1, order='id desc')
        return previous_record.srf_date if previous_record else None
    
    
    
    @api.depends('contact_person')
    def _compute_site_address(self):
        for record in self:
            contact_person = record.contact_person
            if(contact_person):
                street1 = record.env['res.partner'].search([("id","=",record.contact_person.id)]).street
                street2 = record.env['res.partner'].search([("id","=",record.contact_person.id)]).street2
                city = record.env['res.partner'].search([("id","=",record.contact_person.id)]).city
                state_id = record.env['res.partner'].search([("id","=",record.contact_person.id)]).state_id
                zip = record.env['res.partner'].search([("id","=",record.contact_person.id)]).zip
                address = str(street1) + ', ' + str(street2) + ", " + str(city) + ", " + str(state_id.name) + ", " + str(zip)
                record.site_address = address
            else:
                record.site_address = ''
    
    
    @api.depends('customer')
    def _compute_name_work(self):
        for record in self:
            # customer = record.customer
            if(record.customer):
                child_ids = record.env['res.partner'].sudo().search([('child_ids', 'in',record.customer.id)])
                if child_ids:
                    partner_record = record.env['res.partner'].browse(child_ids.id)
                else:
                    partner_record = record.env['res.partner'].browse(record.customer.id)
                name_work = partner_record.projects
                print("Name Work", name_work)
                record.name_works = name_work
            else:
                record.name_works = None

    # @api.depends('customer')
    # def _compute_name_work(self):
    #     for record in self:
    #         customer = record.customer
    #         if(customer):
    #             name_work = record.env['res.partner'].search([("id","=",record.customer.id)]).projects
    #             print("Name Work",name_work)
    #             record.name_works = name_work

    #         else:
    #             record.name_works = None
    
    @api.depends('customer')
    def compute_other_ids(self):
        for record in self:
            contact_ids = self.env['res.partner'].search([('parent_id', '=', record.customer.id),('type','=','other')])
            record.contact_other_ids = contact_ids
    
    
    @api.depends('customer')
    def compute_contact_ids(self):
        for record in self:
            contact_ids = self.env['res.partner'].search([('parent_id', '=', record.customer.id),('type','=','contact')])
            record.contact_contact_ids = contact_ids

    @api.depends('customer')
    def compute_site_ids(self):
        for record in self:
            contact_ids = self.env['res.partner'].search([('parent_id', '=', record.customer.id),('type','=','delivery')])
            record.contact_site_ids = contact_ids

    @api.onchange('customer')
    def compute_client(self):
        for record in self:
            if record.customer:
                self.client = self.env['res.partner'].search([("id","=",self.customer.id)]).consultant