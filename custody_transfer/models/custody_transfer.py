from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
from datetime import date, datetime
import requests





class CustodyTransfer(models.Model):
    _name = 'custody.transfer'
    _description = "Custody Transfer"
    _inherit = ['mail.thread','mail.activity.mixin']
    _rec_name = 'collection_order_id'
    
    collection_order_id = fields.Char("Collection Order ID",default='New')
    customer = fields.Many2one('res.partner',string="Customer")
    contact_site_ids = fields.Many2many('res.partner',string="Site Ids",compute="compute_site_ids")
    site_address = fields.Many2one('res.partner',string="Site Address")
    name_work = fields.Many2one('res.partner.project',string="Name of Work")
    discipline_id = fields.Many2one('lerm_civil.discipline',string="Discipline")
    group_id = fields.Many2one('lerm_civil.group',string="Group")
    material_id = fields.Many2one('product.template',string="Material")
    group_ids = fields.Many2many('lerm_civil.group',string="Group Ids")
    material_ids = fields.Many2many('product.template',string="Material Ids")
    parameters = fields.Many2many('lerm.parameter.master',string="Parameter")
    srf = fields.Many2one('lerm.civil.srf',string="SRF")
    brand = fields.Char("Brand")
    client_refrence = fields.Char("Client Reference")
    size_id = fields.Many2one('lerm.size.line',string="Size")
    size_ids = fields.Many2many('lerm.size.line',string="Size Ids",compute="compute_size_ids")
    client_sample_id = fields.Char("Client Sample ID")
    client = fields.Char("Client")
    conformity_requested = fields.Boolean("Conformity Requested")
    sample_description = fields.Text("Sample Description")
    grade_id = fields.Many2one('lerm.grade.line',string="Grade")
    grade_ids = fields.Many2many('lerm.grade.line',string="Grades")
    state = fields.Selection([
        ('1-draft', 'Draft'),
        ('2-confirmed', 'Confirmed'),
        ('3-picked_up', 'Picked Up'),
        ('4-delivered', 'Delivered'),
    ], string='State', default='1-draft')
    casting = fields.Boolean(string="Casting")
    days_casting = fields.Selection([
        ('3', '3 Days'),
        ('7', '7 Days'),
        ('14', '14 Days'),
        ('28', '28 Days'),
    ], string='Days of Testing', default='3')
    date_casting = fields.Date(string="Date of Casting")
    lattitude = fields.Float("Lattitude",wdigits=(16, 4))
    longitude = fields.Float("Longitude", digits=(16, 4))
    pickup_location = fields.Char("Pickup Location")
    drop_location = fields.Char("Drop Location")
    picked_by = fields.Many2one('res.users',string="Picked By")
    pickup_date = fields.Datetime("Pickup Date/Time")
    delivery_date = fields.Datetime("Delivery Date/Time")
    
    
    
    def get_ip(self):
        response = requests.get('https://api64.ipify.org?format=json').json()
        return response["ip"]
    
    def get_location(self):
        ip_address = self.get_ip()
        response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
        location_data = {
            "latitude": response.get("latitude"),
            "longitude": response.get("longitude")
        }
        return location_data
    
    @api.depends('material_id')
    def compute_size_ids(self):
        for record in self:
            if record.material_id:
                size_ids = self.env['lerm.size.line'].search([('product_id','=', record.material_id.id)])
                record.size_ids = size_ids
            else:
                record.size_ids = None
    
    
    @api.onchange('material_id')
    def compute_grade(self):
        for record in self:
            if record.material_id:
                record.grade_ids = self.env['product.template'].search([('id','=', record.material_id.id)]).grade_table
    
    
    @api.onchange('material_id')
    def compute_parameters(self):
        for record in self:
            if record.material_id:
                parameters_ids = []
                product_records = self.env['product.template'].search([('id','=', record.material_id.id)]).parameter_table1
                # record.product_name = self.pricelist.item_ids.search([('pricelist_id','=',self.pricelist.id),('product_tmpl_id.lab_name','=',self.material_id.lab_name)]).product_tmpl_id.id
                # import wdb; wdb.set_trace()
                for rec in product_records:
                    parameters_ids.append(rec.id)
                domain = {'parameters': [('id', 'in', parameters_ids)]}
                return {'domain': domain}
            else:
                domain = {'parameters': [('id', 'in', [])]}
                return {'domain': domain}
    
    @api.depends('customer')
    def compute_site_ids(self):
        for record in self:
            contact_ids = self.env['res.partner'].search([('parent_id', '=', record.customer.id),('type','=','delivery')])
            record.contact_site_ids = contact_ids
    
    
    @api.onchange('discipline_id')
    def compute_group_ids(self):
        for record in self:
            group_ids = self.env['lerm_civil.group'].search([('discipline','=', record.discipline_id.id)])
            record.group_ids = group_ids
    
    @api.onchange('discipline_id' , 'group_id')
    def compute_material_ids(self):
        for record in self:
            if record.discipline_id and record.group_id:
                material_ids = self.env['product.template'].search([('discipline','=', record.discipline_id.id) , ('group','=', record.group_id.id)])
                record.material_ids = material_ids
            else:
                record.material_ids = None
    
    
    def generate_sequence_and_confirm(self):
        self.collection_order_id = self.env['ir.sequence'].next_by_code('lerm.collection.order') or 'New'
        self.state = '2-confirmed'

        # Get the current date and time
        current_date = datetime.now()

        # Create a log in the chatter with the date
        log_message = f"Collection Order {self.collection_order_id} has been confirmed on {current_date}."
        self.message_post(body=log_message)
        
    def open_srf(self):
        print("SRF open here")
    
    def action_picked_up(self):
        self.state = '3-picked_up'
        

        # Get the current date and time
        current_date = datetime.now()
        self.pickup_date = current_date
        current_user = self.env.user.id
        self.picked_by = current_user
        # Create a log in the chatter with the date and custom message
        log_message = f"Collection Order {self.collection_order_id} has been picked up on {current_date}."
        self.message_post(body=log_message)

    
    def action_deliver(self):
        self.state = '4-delivered'

        current_date = datetime.now()

        log_message = f"Collection Order  {self.collection_order_id} has been delivered on {current_date}."
        self.message_post(body=log_message)
        # sample_sequence = self.env['ir.sequence'].next_by_code('lerm.sample') or 'New'
        location = self.get_location()

        srf = self.env['lerm.civil.srf'].create({
            'collection_order': self.id,
            'document_origin':'custody_transfer',
            'customer':self.customer.id,
            'site_address':self.site_address.id,
            'name_work':self.name_work.id if self.name_work else False,
            'client_refrence':self.client_refrence,
            'client':self.client
            })
        
        self.write({'srf':srf.id , 'lattitude': location['latitude'] ,'longitude':location['longitude']})
        
        data = {
            "discipline_id": self.discipline_id.id,
            "group_id": self.group_id.id ,
            "material_id":self.material_id.id,
            "grade_id":self.grade_id.id,
            "parameter":self.parameters.ids,
            "size_id":self.size_id.id,
            "srf_id":self.srf.id,
            "sample_description":self.sample_description,
            "casting":self.casting,
            "days_casting":self.days_casting,
            "date_casting":self.date_casting
        }
        
        sample_creation_wizard = self.env['create.srf.sample.wizard'].add_sample(data)