from odoo import api, fields, models,_
from odoo.exceptions import UserError ,ValidationError
import logging
from datetime import datetime


# _logger = logging.getLogger(__name__)

class Discipline(models.Model):
    _name = "lerm_civil.discipline"
    _description = "Lerm Discipline"
    _rec_name = 'discipline'

    internal_id = fields.Char(string="Internal ID")
    discipline = fields.Char(string="Discipline", required=True,tracking=True)
    hod = fields.Many2one('res.users',string="Head of Department")

    lab_no = fields.Integer(string="Lab Location")  # Reference the correct model
#     # lab_c_no = fields.Char("Lab Certificate No .",size=6, size_min=6)
    # non_nabl = fields.Char(string="Non-NABL")


    # lab_l_ids = fields.One2many('lab.location','parent_id',string="Parameter")
    # lab_no = fields.Integer(string="Lab Location")  # Reference the correct model
    # # lab_c_no = fields.Char("Lab Certificate No .",size=6, size_min=6)
    # lab_adress = fields.Char(string="Lab Address")

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         name = f"{record.lab_no}"
    #         result.append((record.id, name))
    #     return result

 


 
    
    def __str__(self):
        return self.discipline
    
    @api.model
    def create(self, vals):
        # import wdb;wdb.set_trace()
        record = super(Discipline, self).create(vals)
        record.get_all_fields()
        # record.eln_ref.write({'model_id':record.id})
        return record
    # @api.model
    # def create(self, vals):
    #     record = super(Discipline, self).create(vals)
    #     record.get_all_fields()
    #     return record
    
    def get_all_fields(self):
        # Your implementation to retrieve all fields goes here
        pass
    

# class LabLocation(models.Model):
#     _name = "lab.location"

#     parent_id = fields.Many2one('lerm_civil.discipline',string="Parent Id")

#     lab_no = fields.Integer(string="Lab Location")  # Reference the correct model
#     # lab_c_no = fields.Char("Lab Certificate No .",size=6, size_min=6)
#     lab_adress = fields.Char(string="Lab Address")

#     def name_get(self):
#         result = []
#         for record in self:
#             name = f"{record.lab_no}"
#             result.append((record.id, name))
#         return result




class Group(models.Model):
    _name = "lerm_civil.group"
    _description = "Lerm Group"
    _rec_name = 'group'

    discipline = fields.Many2one('lerm_civil.discipline', string="Discipline", required=True)
    group = fields.Char(string="Group", required=True)
    def __str__(self):
        return self.group
    
class TestMethod(models.Model):
    _name = "lerm_civil.test_method"
    _description = "Lerm Test Method"
    _rec_name = 'test_method'

    test_method = fields.Char(string="Test Method", required=True)



class SrfForm(models.Model):
    _name = "lerm.civil.srf"
    _description = "SRF"
    _inherit = ['mail.thread','mail.activity.mixin']
    _rec_name = 'srf_id'


    # group_id = fields.Many2one('lerm_civil.group', string='Group')
    # discipline_id = fields.Many2one('lerm_civil.discipline', string='Discipline', related='group_id.discipline')
    # lab_no = fields.Integer(string="Lab Location", compute='_compute_lab_no', store=True)

    # @api.depends('group_id.discipline.lab_no')
    # def _compute_lab_no(self):
    #     for record in self:
    #         lab_no = record.group_id.discipline.lab_no
    #         record.lab_no = lab_no
    #         print(f"Computed lab_no: {lab_no}")


  

    srf_id = fields.Char(string="SRF ID",tracking=True)
    kes_number = fields.Char(string="KES No",tracking=True)
    # job_no = fields.Char(string="Job NO.")
    srf_date = fields.Date(string="SRF Date",default=lambda self: self._get_default_date(),tracking=True)
    job_date = fields.Date(string="JOB Date")
    customer = fields.Many2one('res.partner',string="Customer",tracking=True)
    billing_customer = fields.Many2one('res.partner',string="Billing Customer")
    contact_person = fields.Many2one('res.partner',string="Contact Person")
    client = fields.Char("Client",compute="_compute_name_client1")
    # site_address = fields.Many2one('res.partner',string="Site Address")
    site_address = fields.Char(string="Site Address",compute="_compute_site_address")
    name_work = fields.Many2one('res.partner.project',string="Name of Work")
    consultant_name1 = fields.Char(string="Consultant Name",compute="_compute_consultant_name1")
    # department_id = fields.Many2one('hr.department', string='Department')

    department_id = fields.Char(string='Department')

    name_works = fields.Many2many('res.partner.project',string="Name of Work",compute="_compute_name_work")

    client_refrence = fields.Char(string="Client Reference Letter")
    samples = fields.One2many('lerm.srf.sample' , 'srf_id' , string="Samples",tracking=True)
    contact_other_ids = fields.Many2many('res.partner',string="Other Ids",compute="compute_other_ids")
    contact_contact_ids = fields.Many2many('res.partner',string="Contact Ids",compute="compute_contact_ids")
    contact_site_ids = fields.Many2many('res.partner',string="Site Ids",compute="compute_site_ids")
    attachment = fields.Binary(string="Attachment")
    attachment_name = fields.Char(string="Attachment Name")

    state = fields.Selection([
        ('1-draft', 'Draft'),
        ('2-confirm', 'Confirm')
    ], string='State', default='1-draft')
    sample_count = fields.Integer(string="Sample Count", compute='compute_sample_count')
    eln_count = fields.Integer(string="ELN Count", compute='compute_eln_count')
    sample_range_table = fields.One2many('sample.range.line','srf_id',string="Sample Range")
    contractor = fields.Many2one('lerm.contractor.line',string="Contractor")
    contractor_ids = fields.Many2many('lerm.contractor.line')
    casting = fields.Boolean(string="Casting")
    
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
    
    date_casting = fields.Date(string="Date of Casting")
    date_editable = fields.Boolean(string="SRF Date editable",default=False,compute="_compute_date_editable")
    active = fields.Boolean(string="Active",default=True)


    def _compute_date_editable(self):
        for record in self:
            backdate_group_id = record.env.ref('lerm_civil.kes_srf_backdate_creation_group').id

            if backdate_group_id in self.env.user.groups_id.ids:
                record.date_editable = True
            else:
                record.date_editable = False

    def read(self, fields=None, load='_classic_read'):

        self._compute_date_editable()
        
        return super(SrfForm, self).read(fields=fields, load=load)




    # @api.depends('department_id')
    # def _compute_department(self):
    #     for record in self:
    #         record.department = record.department_id.name if record.department_id else False


   


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
    def _compute_name_work(self):
        for record in self:
            if record.customer:
                # import wdb; wdb.set_trace() 
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
    #         if record.customer:
    #             import wdb; wdb.set_trace() 
    #             child_ids = record.env['res.partner'].sudo().search([('child_ids', 'in',record.customer.id)])
    #             if child_ids:
    #                 partner_record = record.env['res.partner'].browse(child_ids.id)
    #             else:
    #                 partner_record = record.env['res.partner'].browse(record.customer.id)
    #             name_work = partner_record.projects
    #             print("Name Work", name_work)
    #             record.name_works = name_work
    #         else:
    #             record.name_works = None

    @api.onchange('name_work')
    def _onchange_name_work(self):
        # Set the value of consultant_name1 based on the selected name_work
        if self.name_work:
            self.consultant_name1 = self.name_work.consultant_name

    @api.depends('name_work')
    def _compute_consultant_name1(self):
        # Update consultant_name1 when name_work changes
        for record in self:
            if record.name_work:
                record.consultant_name1 = record.name_work.consultant_name
            else:
                record.consultant_name1 = False



    @api.onchange('name_work')
    def _onchange_name_client(self):
        # Set the value of consultant_name1 based on the selected name_work
        if self.name_work:
            self.client = self.name_work.client_name

    @api.depends('name_work')
    def _compute_name_client1(self):
        # Update client when name_work changes
        for record in self:
            if record.name_work:
                record.client = record.name_work.client_name
            else:
                record.client = False

    @api.model
    def create(self, vals):
        previous_record_date = self.search([], order='srf_date desc', limit=1).srf_date
        
        # previous_record_date = datetime.strptime(previous_record_date, "%Y-%m-%d").date()
        # date2 = datetime.strptime(vals["srf_date"], "%Y-%m-%d").date()
      
        try:
            date1 = datetime.strptime(str(previous_record_date), "%Y-%m-%d")
            date2 = datetime.strptime(str(vals["srf_date"]), "%Y-%m-%d")

            group_name = 'lerm_civil.kes_srf_backdate_creation_group'

            if date1 > date2:
                user_has_group = self.env.user.has_group(group_name)
                if user_has_group:
                    record = super(SrfForm, self).create(vals)
                    return record
                else:
                    raise ValidationError("Backdate SRF Creation Not allowed")
            else:
                record = super(SrfForm, self).create(vals)
                return record
        except:
            record = super(SrfForm, self).create(vals)
        
        return record

    
        
        
    @api.model
    def _get_default_date(self):
        previous_record = self.search([], order='srf_date desc', limit=1)
        current_date =  datetime.now().date()

        # srf_group_id = self.env.ref('lerm_civil.kes_access_srf').id
        # import wdb; wdb.set_trace()
        
        
        # if backdate_group_id in self.env.user.groups_id.ids:
        #     return datetime.now().date()
        # print("+++++++++++++>",previous_record)
        return current_date
    
    def action_srf_sent_mail(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new'
        }


    def sample_count_button(self):
        return {
        'name': 'Sample',
        'domain': [('srf_id', '=', self.id)],
        'view_type': 'form',
        'res_model': 'lerm.srf.sample',
        'view_id': False,
        'view_mode': 'tree,form',
        'type': 'ir.actions.act_window'
    }
    def compute_eln_count(self):
        count = self.env['lerm.eln'].search_count([('srf_id', '=', self.id)])
        self.eln_count = count
        

    @api.onchange('customer')
    def compute_client(self):
        for record in self:
            if record.customer:
                self.client = self.env['res.partner'].search([("id","=",self.customer.id)]).consultant



    def eln_count_button(self):
        return {
        'name': 'ELN',
        'domain': [('srf_id', '=', self.id)],
        'view_type': 'form',
        'res_model': 'lerm.eln',
        'view_id': False,
        'view_mode': 'tree,form',
        'type': 'ir.actions.act_window'
    }
    def compute_sample_count(self):
        count = self.env['lerm.srf.sample'].search_count([('srf_id', '=', self.id)])
        self.sample_count = count



    def confirm_srf(self):
        srf_ids=[]
        
        # import wdb; wdb.set_trace()
        
        count = self.env['lerm.srf.sample'].search_count([('srf_id.srf_date','=',self.srf_date),('kes_no','!=','New'),('status','=','2-confirmed')]) 

        for record in self.sample_range_table:
            sam_next_number = self.env['ir.sequence'].search([('code','=','lerm.srf.sample')]).number_next_actual
            kes_next_number = self.env['ir.sequence'].search([('code','=','lerm.srf.sample.kes')]).number_next_actual
            



            sample_range = "SAM/"+str(sam_next_number)+"-"+str(sam_next_number+record.sample_qty-1)
            kes_range = "KES/"+str(count+1)+"-"+str(count+1+record.sample_qty-1)
            record.write({'sample_range': sample_range , 'kes_range': kes_range })
            samples = self.env['lerm.srf.sample'].search([('sample_range_id','=',record.id)])
            



            
            for sample in samples:
                # import wdb; wdb.set_trace()
                sample_id = self.env['ir.sequence'].next_by_code('lerm.srf.sample') or 'New'

                year = str(self.srf_date.year)[-2:]
                month = str(self.srf_date.month).zfill(2)
                day = str(self.srf_date.day).zfill(2)
                count = count + 1

                kes_no = "KES"+ year+month+day + str(count).zfill(3) or "New"

                # kes_no = "KES"+ str(record.srf_date) + self.env['ir.sequence'].next_by_code('lerm.srf.sample.kes') or 'New'
                kes_no_daywise = self.env['ir.sequence'].next_by_code('lerm.sample.daywise.seq') 
                # kes_no = self.env['ir.sequence'].next_by_code('lerm.srf.sample.kes') + kes_no_daywise or 'New'
                # lab_l_id =  self.env['lab.location'].search([('id','=',self.env.context['allowed_company_ids'][0])])
                company =  self.env['res.company'].search([('id','=',self.env.context['allowed_company_ids'][0])])
                # lab_location =  self.env.context['discipline_id']
                # print('<<<<<<<<<<<<<<<<<<<<',lab_location)
                # lab_cert_no = str(sample.lab_certificate_no)
                # import wdb; wdb.set_trace()

                # try: 
                #     sample.received_by_id = self.env.user
                # except:
                #     pass

                

                
                if sample.scope == 'nabl':

                    if sample.lab_location:
                        code = sample.lab_location.ulr_sequence.code
                        ulr_no = self.env['ir.sequence'].next_by_code(code) or 'New'
                        lab_loc = sample.location_name.location_code
                        lab_cert_no = sample.lab_location.lab_certificate_no
                        ulr_no = ulr_no.replace('(lab_certificate_no)', lab_cert_no)                
                        ulr_no = ulr_no.replace('(lab_no_value)', lab_loc)
                        


                    else:
                        lab_loc = str(sample.lab_no_value)
                        lab_cert_no = str(company.lab_certificate_no)
                        # lab_loc = company.lab_seq_no
                        ulr_no = self.env['ir.sequence'].next_by_code('sample.ulr.seq') or 'New'
                        ulr_no = ulr_no.replace('(lab_certificate_no)', lab_cert_no)                
                        ulr_no = ulr_no.replace('(lab_no_value)', lab_loc)
                else:
                    ulr_no = ''
                # import wdb ; wdb.set_trace()
              
             
        

              
                
                sample.write({'sample_no':sample_id,'kes_no':kes_no,'status':'2-confirmed','ulr_no':ulr_no})
                self.env.cr.commit()
        
   

   
    # def confirm_srf(self):
    #     srf_ids=[]
        
    #     # import wdb; wdb.set_trace()
        
    #     count = self.env['lerm.srf.sample'].search_count([('srf_id.srf_date','=',self.srf_date),('kes_no','!=','New'),('status','=','2-confirmed')]) 

    #     for record in self.sample_range_table:
    #         sam_next_number = self.env['ir.sequence'].search([('code','=','lerm.srf.sample')]).number_next_actual
    #         kes_next_number = self.env['ir.sequence'].search([('code','=','lerm.srf.sample.kes')]).number_next_actual
            



    #         sample_range = "SAM/"+str(sam_next_number)+"-"+str(sam_next_number+record.sample_qty-1)
    #         kes_range = "KES/"+str(count+1)+"-"+str(count+1+record.sample_qty-1)
    #         record.write({'sample_range': sample_range , 'kes_range': kes_range })
    #         samples = self.env['lerm.srf.sample'].search([('sample_range_id','=',record.id)])
            



            
    #         for sample in samples:
    #             # import wdb; wdb.set_trace()
    #             sample_id = self.env['ir.sequence'].next_by_code('lerm.srf.sample') or 'New'

    #             year = str(self.srf_date.year)[-2:]
    #             month = str(self.srf_date.month).zfill(2)
    #             day = str(self.srf_date.day).zfill(2)
    #             count = count + 1

    #             kes_no = "KES"+ year+month+day + str(count).zfill(3) or "New"

    #             # kes_no = "KES"+ str(record.srf_date) + self.env['ir.sequence'].next_by_code('lerm.srf.sample.kes') or 'New'
    #             kes_no_daywise = self.env['ir.sequence'].next_by_code('lerm.sample.daywise.seq') 
    #             # kes_no = self.env['ir.sequence'].next_by_code('lerm.srf.sample.kes') + kes_no_daywise or 'New'
    #             # lab_l_id =  self.env['lab.location'].search([('id','=',self.env.context['allowed_company_ids'][0])])
    #             company =  self.env['res.company'].search([('id','=',self.env.context['allowed_company_ids'][0])])
    #             # lab_location =  self.env.context['discipline_id']
    #             # print('<<<<<<<<<<<<<<<<<<<<',lab_location)
    #             # lab_cert_no = str(sample.lab_certificate_no)
    #             # import wdb; wdb.set_trace()

    #             # try: 
    #             #     sample.received_by_id = self.env.user
    #             # except:
    #             #     pass

                

                
    #             if sample.scope == 'nabl':

    #                 if sample.lab_location:
    #                     code = sample.lab_location.ulr_sequence.code
    #                     ulr_no = self.env['ir.sequence'].next_by_code(code) or 'New'
    #                     lab_loc = sample.location_name.location_code
    #                     lab_cert_no = sample.lab_location.lab_certificate_no
    #                     ulr_no = ulr_no.replace('(lab_certificate_no)', lab_cert_no)                
    #                     ulr_no = ulr_no.replace('(lab_no_value)', lab_loc)
                        


    #                 else:
    #                     srf_date = sample.srf_id.srf_date
    #                     next_number = ''
    #                     ulr = self.env['ir.sequence'].sudo().search([('code', '=', 'sample.ulr.seq')])

    #                     # Instead of using `next_by_code`, rely on `ulr.date_range_ids`
    #                     for dt in ulr.date_range_ids:
    #                         from_date = dt.date_from
    #                         to_date = dt.date_to
    #                         if from_date <= srf_date <= to_date:
    #                             next_number = dt.number_next_actual
    #                             prefix = ulr.prefix or ''
    #                             suffix = ulr.suffix or ''
                                
    #                             lab_location = str(sample.lab_no_value)
    #                             lab_certificate_no = str(company.lab_certificate_no)

    #                             # Replace placeholders in prefix
    #                             prefix = prefix.replace('(lab_certificate_no)', lab_certificate_no)
    #                             prefix = prefix.replace('(lab_no_value)', lab_location)
    #                             prefix = prefix.replace('%(y)s', str(srf_date.year)[-2:])
                                
    #                             # Construct the final sequence number
    #                             ulr_no = f"{prefix}{str(next_number).zfill(8)}{suffix}"

    #                             # Increment and update the `number_next_actual`
    #                             dt.write({'number_next_actual': next_number + 1})
    #                             break


                                





    #                     # lab_loc = str(sample.lab_no_value)
    #                     # lab_cert_no = str(company.lab_certificate_no)
    #                     # # lab_loc = company.lab_seq_no
    #                     # ulr_no = self.env['ir.sequence'].next_by_code('sample.ulr.seq') or 'New'
    #                     # ulr_no = ulr_no.replace('(lab_certificate_no)', lab_cert_no)                
    #                     # ulr_no = ulr_no.replace('(lab_no_value)', lab_loc)
    #             else:
    #                 ulr_no = ''
    #             # import wdb ; wdb.set_trace()
              
             
        

              
                
    #             sample.write({'sample_no':sample_id,'kes_no':kes_no,'status':'2-confirmed','ulr_no':ulr_no})
    #             self.env.cr.commit()
        
   
                

                    
        

        # for record in self.samples:
        #     # if vals.get('sample_no', 'New') == 'New' and vals.get('kes_no', 'New') == 'New':
        #     sample_id = self.env['ir.sequence'].next_by_code('lerm.srf.sample') or 'New'
        #     kes_no = self.env['ir.sequence'].next_by_code('lerm.srf.sample.kes') or 'New'
        #     # res = super(LermSampleForm, self).create(vals)
        #     #     return res
        #     record.write({'status':'2-confirmed','sample_no':sample_id,'kes_no':kes_no})
        #     srf_ids.append(sample_id)
        #     if len(srf_ids) == 1:
        #         srfidstring = srf_ids[0]
        #     else:
        #         srfidstring = str(srf_ids[0])+'/'+str(srf_ids[-1])
            
        # Extracting the numbers from the original string
        # numbers = srfidstring.split("/")

        # # Formatting the numbers in the desired format
        # formatted_numbers = "-".join([f"{int(num):05d}" for num in numbers])

        # Creating the modified string
        # import wdb; wdb.set_trace()
        first_sample_range = self.sample_range_table[0].kes_range
        last_sample_range = self.sample_range_table[-1].kes_range  
        first_samplerange_slash_index = first_sample_range.find("/")
        srffirstnumber_str = first_sample_range[first_samplerange_slash_index+1:first_sample_range.find("-")]
        last_sample_range_index = last_sample_range.find("-")
        srf_last_number = last_sample_range[last_sample_range_index+1:]

      
        modified_srf_id = f"SRF/"+year+month+day+srffirstnumber_str.zfill(3)+"-"+year+month+day+srf_last_number.zfill(3)
        modified_kes_number = f"KES/DUS"
        self.write({'srf_id': modified_srf_id})
        self.write({'kes_number': modified_kes_number})
        self.write({'state': '2-confirm'})
        # for record in self:

    # name_of_work = fields.Many2one('res.partner.project',string='Name of Work')

    @api.depends('customer')
    def compute_contact_ids(self):
        for record in self:
            contact_ids = self.env['res.partner'].search([('parent_id', '=', record.customer.id),('type','=','contact')])
            record.contact_contact_ids = contact_ids

    @api.onchange('customer')
    def compute_contractor_ids(self):
        for record in self:
            contractor_ids = self.env['res.partner'].search([('id', '=', record.customer.id)]).contractor_table
            record.contractor_ids = contractor_ids

    

    @api.depends('customer')
    def compute_other_ids(self):
        for record in self:
            contact_ids = self.env['res.partner'].search([('parent_id', '=', record.customer.id),('type','=','other')])
            record.contact_other_ids = contact_ids

    @api.depends('customer')
    def compute_site_ids(self):
        for record in self:
            contact_ids = self.env['res.partner'].search([('parent_id', '=', record.customer.id),('type','=','delivery')])
            record.contact_site_ids = contact_ids
    
    def open_edit_srf_header_wizard(self):
        action = self.env.ref('lerm_civil.edit_srf_wizard_form')
        
        return {
            'name': "Edit SRF Header",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'edit.lerm.civil.srf',
            'view_id': action.id,
            'target': 'new',
            'context': {
                'default_srf_id' : self.id,
                'default_customer': self.customer.id,
            'default_srf_date': self.srf_date,
            'default_client': self.client,
            'default_contact_person': self.contact_person.id,
            'default_contractor': self.contractor.id,
            'default_billing_customer': self.billing_customer.id,
            'default_client_refrence': self.client_refrence,
            'default_name_work': self.name_work.id,
            'default_attachment':self.attachment,
            'default_attachment_name':self.attachment_name
            }
            }
        
    
    def open_sample_add_wizard(self):

        samples = self.env["lerm.srf.sample"].search([("srf_id","=",self.id)])
        # print("Samples "+ str(samples))


        action = self.env.ref('lerm_civil.srf_sample_wizard_form')
        if len(samples) > 0:
            print(samples[0].material_id.id , 'error')
            discipline_id = samples[-1].discipline_id.id
            # lab_l_id = samples[-1].lab_l_id.id
            lab_no_value = samples[-1].lab_no_value
            material_id = samples[-1].material_id.id
            group_id = samples[-1].group_id.id
            department_id = samples[-1].department_id
            alias = samples[-1].alias
            brand = samples[-1].brand
            size_id = samples[-1].size_id.id
            grade_id = samples[-1].grade_id.id
            sample_received_date = samples[-1].sample_received_date
            location = samples[-1].location
            sample_condition = samples[-1].sample_condition
            sample_reject_reason = samples[-1].sample_reject_reason
            witness = samples[-1].witness
            scope = samples[-1].scope
            sample_description = samples[-1].sample_description
            sample_received_date = self.srf_date

            return {
            'name': "Add Sample",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.srf.sample.wizard',
            'view_id': action.id,
            'target': 'new',
            'context': {
            # 'default_discipline_id' : discipline_id,
            'default_material_id' : material_id,
            'default_alias':alias,
            'default_brand':brand,
            'default_size_id':size_id,
            'default_grade_id':grade_id,
            'default_sample_received_date': sample_received_date,
            'default_location':location,
            'default_sample_condition':sample_condition,
            'default_sample_reject_reason':sample_reject_reason,
            'default_witness':witness,
            # 'default_department_id':department_id,
            'default_scope':scope,
            'default_sample_description':sample_description,
            'default_group_id':group_id,
            'default_sample_received_date':sample_received_date
            }
        }
        else:
            return {
            'name': "Add Sample",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.srf.sample.wizard',
            'view_id': action.id,
            'target': 'new'
            }


    def open_new_sample_add_wizard(self):
        

        # import wdb;wdb.set_trace()
        samples = self.env["lerm.srf.sample"].search([("srf_id","=",self.id)])
        action = self.env.ref('lerm_civil.srf_sample_wizard_form')
        return {
            'name': "Add Sample",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.srf.sample.wizard',
            'view_id': action.id,
            'target': 'new',
            'context':{
                'default_customer_id': self.customer.id,
                'default_sample_received_date':self.srf_date,
                'default_pricelist':self.customer.property_product_pricelist.id,
                'default_is_update': False,
                # 'default_discipline_id': self.discipline_id.id,
                }
            }

     



class CreateSampleWizard(models.TransientModel):
    _name = 'create.srf.sample.wizard'
    # _rec_name = 'lab_l_id'

    # lab_l_id = fields.Many2one('lab.location', string="Lab Locations",domain="[('parent_id', '=', discipline_id)]")
    # lab_l_id = fields.Integer(string="Lab Locations",domain="[('parent_id', '=', discipline_id)]")

   
    # @api.onchange('discipline_id')
    # def onchange_discipline_id(self):
    #     if self.discipline_id:
    #         domain = [('parent_id', '=', self.discipline_id.id)]
    #         return {'domain': {'lab_l_id': domain}}
    #     else:
    #         return {'domain': {'lab_l_id': []}}
  
  




    # def name_get(self):
    #     result = []
    #     for record in self:
    #         name = f"Lab Locations: {', '.join(str(lab.lab_no) for lab in record.lab_l_id)}"
    #         result.append((record.id, name))
    #     return result
    lab_no_value = fields.Char(string="Value")
    @api.depends('discipline_id.lab_no')
    def _compute_lab_no(self):
        for record in self:
            lab_no_value = record.discipline_id.lab_no
            record.lab_no_value = lab_no_value

    @api.onchange('discipline_id')
    def onchange_discipline_id(self):
        edit_mode = self.edit_mode
        # Trigger the computation of lab_no_value
        print("Before Edit Mode", edit_mode)
        if not edit_mode: 
            self.group_id = None
            self.material_id = None
            self.grade_id = None
            self.size_id = None
            self.parameters = None
        
        print("After Edit Mode", edit_mode)
        
        self.edit_mode = False
        self._compute_lab_no()
   
    
    srf_id = fields.Many2one('lerm.civil.srf' , string="Srf Id")
    
    edit_mode = fields.Boolean(string="Casting")
    sample_id = fields.Char(string="Sample Id")
    casting = fields.Boolean(string="Casting")
    discipline_id = fields.Many2one('lerm_civil.discipline',string="Discipline")
   
    group_id = fields.Many2one('lerm_civil.group',string="Group")
    # department_id = fields.Char(string='Department')
    material_id = fields.Many2one('product.template',string="Material")
    brand = fields.Char(string="Brand")
    size_id = fields.Many2one('lerm.size.line',string="Size")
    size_ids = fields.Many2many('lerm.size.line',string="Size")
    grade_id = fields.Many2one('lerm.grade.line',string="Grade")
    
    grade_ids = fields.Many2many('lerm.grade.line',string="Grades")
    grade_required = fields.Boolean(string="Grade Required",compute="compute_grade_required")

    sample_qty = fields.Integer(string="Sample Quantity",default=1)
    received_by_id = fields.Many2one('res.users',string="Received By",default=lambda self: self.env.user)
    sample_received_date = fields.Date(string="Sample Received Date")
    sample_condition = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('non_satisfactory', 'Non-Satisfactory'),
    ], string='Sample Condition', default='satisfactory')
    location = fields.Char(string="Location")
    sample_reject_reason = fields.Char(string="Sample Reject Reason")
    has_witness = fields.Boolean(string="Witness")
    witness = fields.Char(string="Witness name")
    scope = fields.Selection([
        ('nabl', 'NABL'),
        ('non_nabl', 'Non-NABL'),
    ], string='Scope', default='nabl')
    sample_description = fields.Text(string="Sample Description")
    group_ids = fields.Many2many('lerm_civil.group',string="Group Ids")
    material_ids = fields.Many2many('product.template',string="Material Ids")
    client_sample_id = fields.Char(string="Client Sample Id")
    # size_ids = fields.Many2many('lerm.size.line',string="Size Ids")
    # grade_ids = fields.Many2many('lerm.grade.line',string="Grade Ids")
    # qty_ids = fields.Many2many('lerm.qty.line',string="Qty Ids")
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
    ], string='Days of Testing', default='3')
    date_casting = fields.Date(string="Date of Casting")
    customer_id = fields.Many2one('res.partner' , string="Customer")
    product_aliases = fields.Many2many('product.product',string="Product Aliases")
    product_alias = fields.Many2one('product.product',string="Product Alias")
    parameters = fields.Many2many('lerm.parameter.master',string="Parameter")
    conformity = fields.Boolean(string="Conformity Requested")
    volume = fields.Char(string="Volume")
    product_name = fields.Many2one('product.template',string="Product Name")
    pricelist = fields.Many2one('product.pricelist',string='Pricelist')
    main_name = fields.Char(string="Product Name",compute='compute_main_name',store=True)
    price = fields.Float(string="Price",compute='compute_price',store=True)

    sample = fields.Many2one('lerm.srf.sample',string="Sample")
    is_update = fields.Boolean('Is Update')

    department_id = fields.Char(string='Department')
    lab_location = fields.Many2one('lerm.lab.master',string="Lab Location")
    location_name = fields.Many2one('lerm.lab.location.master',string="Location Name")

    @api.onchange('discipline_id', 'group_id', 'material_id')
    def onchange_discipline_group_material(self):
        if self.discipline_id and self.group_id and self.material_id:
            # Assuming you have a relation between Material and CreateSampleWizard models
            material = self.env['product.template'].search([
                ('id', '=', self.material_id.id),
                ('discipline', '=', self.discipline_id.id),
                ('group', '=', self.group_id.id)], limit=1)
            if material:
                self.department_id = material.department_ids.name

    # @api.depends('discipline_id', 'group_id')
    # def compute_discipline_id(self):
    #     for record in self:
    #         material = self.env['product.template'].search([('discipline', '=', record.discipline_id.id), ('group', '=', record.group_id.id)], limit=1)
    #         if material:
    #             record.department_id = material.department_id.id


   
   

    # @api.depends('discipline_id')
    # def compute_grade_required(self):
    #     for wizard in self:
    #         wizard.grade_required = wizard.discipline_id and wizard.discipline_id.lab_l_ids


    @api.depends('product_name')
    def compute_main_name(self):
        for record in self:
            record.main_name = record.product_name.name
    
    @api.depends('pricelist','material_id')
    def compute_price(self):
        for record in self:
            if record.pricelist.id and record.material_id:
            # record.main_name = record.product_name.name
                record.price = self.pricelist.item_ids.search([('pricelist_id','=',self.pricelist.id),('product_tmpl_id.lab_name','=',self.material_id.lab_name)]).fixed_price

    @api.onchange('material_id')
    def compute_grade_required(self):
        for record in self:
            
            for material in record.material_id:
                # import wdb; wdb.set_trace()
                if len(material.grade_table) > 0:
                    record.grade_required = True
                else:
                    record.grade_required = False


    @api.onchange('material_id')
    def compute_grade(self):        

        
        for record in self:
            if record.material_id:
                record.grade_ids = self.env['product.template'].search([('id','=', record.material_id.id)]).grade_table
    

    @api.onchange('material_id')
    def compute_size(self):
        for record in self:
            if record.material_id:
                record.size_ids = self.env['product.template'].search([('id','=', record.material_id.id)]).size_table

    @api.onchange('material_id')
    def compute_volume(self):
        for record in self:
            if record.material_id:
                record.volume = self.env['product.template'].search([('id','=', record.material_id.id)]).volume

    @api.onchange('material_id')
    def compute_parameters(self):
        for record in self:
            if record.material_id:
                parameters_ids = []
                print("MATERIAL__IDD",self.env['product.template'].search([('id','=', record.material_id.id)]))
                product_records = self.env['product.template'].search([('id','=', record.material_id.id)]).parameter_table1
                record.product_name = self.pricelist.item_ids.search([('pricelist_id','=',self.pricelist.id),('product_tmpl_id.lab_name','=',self.material_id.lab_name)]).product_tmpl_id.id
                # import wdb; wdb.set_trace()
                for rec in product_records:
                    parameters_ids.append(rec.id)
                domain = {'parameters': [('id', 'in', parameters_ids)]}
                return {'domain': domain}
            else:
                domain = {'parameters': [('id', 'in', [])]}
                return {'domain': domain}
    


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
    
    @api.onchange('material_id' ,'customer_id')
    def compute_product_aliases(self):
        for record in self:
            if record.material_id and record.customer_id:
                result = self.env['lerm.alias.line'].search([('customer', '=', record.customer_id.id),('product_id', '=', record.material_id.id)])
                record.product_aliases = result.product_alias.ids
            else:
                record.product_aliases = None
                
    def edit_current_sample(self,data=False):
        
            

        group_id =  self.group_id.id
        department_id = self.department_id
        # alias = self.alias
        material_id = self.material_id.id
        size_id = self.size_id.id
        brand = self.brand
        grade_id = self.grade_id.id
        sample_received_date = self.sample_received_date
        location = self.location
        
        discipline_id = self.discipline_id.id
        lab_no_value = self.lab_no_value
        # lab_l_id = self.lab_l_id.id
        sample_description =self.sample_description
        parameters = self.parameters
        discipline_id = self.discipline_id
        casting = self.casting
        client_sample_id = self.client_sample_id
        conformity = self.conformity
        volume = self.volume
        product_name = self.product_name


        if self.grade_required:
            if not self.grade_id:
                raise UserError("Grade is Required")
            

        if not parameters:
            raise UserError("Add atleast one Parameter")
        
        if discipline_id.internal_id == '742c99ff-c484-4806-bb68-11b4271d6147':
            if len(parameters) > 1:
                raise UserError("Only one Parameter is allowed in Non Destructive Testing")
        
        sample_id = self.env.context.get('active_id')
        sample = self.env['lerm.srf.sample'].search([('id','=',sample_id)])

        eln = self.env['lerm.eln'].search([('sample_id','=',sample.id)])
        eln.sudo().write({
            'grade_id':grade_id,
            'size_id':size_id,
            'casting_date':self.date_casting
        })

        # import wdb; wdb.set_trace()


        sample.write({
            'discipline_id': discipline_id,
            # 'lab_l_id': lab_l_id,
            'lab_no_value':lab_no_value,
            'group_id':group_id,
            'material_id' : material_id,
            'grade_id' : grade_id,
            'parameters':parameters,
            # 'sample_range_id':sample_range.id,
            'size_id':size_id,
            'sample_description':sample_description,
            'casting':casting,
            'date_casting':self.date_casting,
            'days_casting':self.days_casting,
            'brand':brand,
            'sample_received_date':sample_received_date,
            'location':location,
            'sample_condition' : self.sample_condition,
            'sample_reject_reason' : self.sample_reject_reason,
            'has_witness' : self.has_witness,
            'witness' : self.witness,
            'department_id': department_id,
            'client_sample_id':client_sample_id,
            'conformity':conformity,
            'volume':volume,
            'product_name':product_name,
            'lab_location':self.lab_location.id,
            'location_name':self.location_name.id

            
        })
        return {'type': 'ir.actions.act_window_close'}


           

    # @api.onchange('material_id' ,'customer_id', 'material_id')
    # def onchange_material_id(self):
    #     for record in self:
    #         result = self.env['lerm.alias.line'].search([('customer', '=', record.customer_id.id),('product_id', '=', record.material_id.id)])
    #         print(result)
            
    #         record.product_alias = result.product_alias.id

    # @api.onchange('discipline_id', 'lab_l_id')
    # def onchange_discipline_id(self):
    #     if self.discipline_id and self.lab_l_id:
    #         # Assuming you are interested in the first selected location
    #         self.lab_l_id = self.lab_l_id[0]
    #     else:
    #         self.lab_l_id = False
       
   

    def add_sample(self,data=False):

        # import wdb; wdb.set_trace()
        if data:
            discipline_id = data['discipline_id']
            lab_no_value = data['lab_no_value']
            # lab_l_id = data['lab_l_id']
            group_id =  data['group_id']
            department_id = data['department_id']
            material_id = data['material_id']
            grade_id = data['grade_id']
            srf_id  = data['srf_id']
            parameters = data['parameter']
            sample_description = data['sample_description']
            size_id = data['size_id']
            casting = data["casting"]
            days_casting = data["days_casting"]
            date_casting = data["date_casting"]

            
            sample_range = self.env['sample.range.line'].create({
                'srf_id': srf_id,
                'group_id':group_id,
                'discipline_id' : discipline_id,
                # 'lab_l_id': lab_l_id,
                'lab_no_value':lab_no_value,
                'material_id' : material_id,
                'grade_id' : grade_id,
                'department_id': department_id,
                'sample_qty':1,
                'parameters':parameters,
                'size_id':size_id,
                'sample_description':sample_description,
                'casting':casting,
                'date_casting':date_casting,
                'days_casting':days_casting
            })
            
            srf = self.env["lerm.srf.sample"].create({
                'srf_id':srf_id,
                'discipline_id': discipline_id,
                # 'lab_l_id': lab_l_id,
                'lab_no_value':lab_no_value,
                'group_id':group_id,
                'material_id' : material_id,
                'department_id': department_id,
                'grade_id' : grade_id,
                'parameters':parameters,
                'sample_range_id':sample_range.id,
                'size_id':size_id,
                'sample_description':sample_description,
                'casting':casting,
                'date_casting':date_casting,
                'days_casting':days_casting,
                'lab_location':self.lab_location.id,
                'location_name':self.location_name.id


            })
            
        
        
        else:
            # print("From else")
          

            group_id =  self.group_id.id
            # alias = self.alias
            material_id = self.material_id.id
            size_id = self.size_id.id
            brand = self.brand
            grade_id = self.grade_id.id
           
            sample_received_date = self.sample_received_date
            location = self.location
            sample_condition = self.sample_condition
            sample_reject_reason = self.sample_reject_reason
            has_witness = self.has_witness
            witness = self.witness
            department_id: self.department_id
            discipline_id = self.discipline_id.id
            lab_no_value = self.lab_no_value
            # lab_l_id = self.lab_l_id.id
            scope = self.scope
            sample_description =self.sample_description
            parameters = self.parameters
            discipline_id = self.discipline_id
            casting = self.casting
            sample_qty = self.sample_qty
            client_sample_id = self.client_sample_id
            conformity = self.conformity
            volume = self.volume
            product_name = self.product_name
            lab_location  = self.lab_location.id
            location_name = self.location_name.id



            if self.grade_required:
                if not self.grade_id:
                    raise UserError("Grade is Required")
                

            if not parameters:
                raise UserError("Add atleast one Parameter")
            
            if discipline_id.internal_id == '742c99ff-c484-4806-bb68-11b4271d6147':
                if len(parameters) > 1:
                    raise UserError("Only one Parameter is allowed in Non Destructive Testing")

            

            srf_ids = []
            #     for i in range(1, self.qty_id + 1):
            #         srf_number = str(i).zfill(4)  # Pad the number with leading zeros
            #         srf_id = f"SRF/{srf_number}-{str(self.qty_id).zfill(4)}"
            #         srf_ids.append(srf_id)

            if self.sample_qty > 0:

                sample_range = self.env['sample.range.line'].create({
                    'srf_id': self.env.context.get('active_id'),
                    'group_id':group_id,
                    'product_alias':self.product_alias.id,
                    'discipline_id': discipline_id,
                    # 'lab_l_id': lab_l_id,
                    'lab_no_value':lab_no_value,
                    'material_id' : self.material_id.id,
                    'size_id':size_id,
                    'brand':brand,
                    'grade_id':grade_id,
                    'sample_received_date':sample_received_date,
                    'location':location,
                    'sample_condition':sample_condition,
                    'sample_reject_reason':sample_reject_reason,
                    'has_witness':has_witness,
                    'witness':witness,
                    'department_id':self.department_id,
                    'conformity':conformity,
                    'scope':scope,
                    'sample_description':sample_description,
                    'parameters':parameters,
                    'discipline_id':discipline_id.id,
                    'casting':casting,
                    'sample_qty':sample_qty,
                    'client_sample_id':client_sample_id,
                    'casting_date':self.date_casting,
                    'volume':volume,
                    'product_name':product_name.id,
                    'main_name':self.main_name,
                    'price':self.price,
                    'date_casting':self.date_casting

                })
                for i in range(self.sample_qty):
                    self.env["lerm.srf.sample"].create({
                        'srf_id': self.env.context.get('active_id'),
                        'group_id':group_id,
                       
                        # 'alias':alias,
                        'discipline_id': discipline_id,
                        # 'lab_l_id': lab_l_id,
                        'lab_no_value':lab_no_value,
                        'material_id' : self.material_id.id,
                        'size_id':size_id,
                        'brand':brand,
                        'grade_id':grade_id,
                        'sample_received_date':sample_received_date,
                        'location':location,
                        'sample_condition':sample_condition,
                        'sample_reject_reason':sample_reject_reason,
                        'has_witness':has_witness,
                        'witness':witness,
                        'department_id':self.department_id,
                        'conformity':conformity,
                        'scope':scope,
                        'sample_description':sample_description,
                        'parameters':parameters,
                        'discipline_id':discipline_id.id,
                        'casting':casting,
                        'sample_range_id':sample_range.id,
                        'client_sample_id':client_sample_id,
                        'casting_date':self.date_casting,
                        'days_casting':self.days_casting,
                        'casting':self.casting,
                        'volume':volume,
                        'product_name':product_name.id,
                        'main_name':self.main_name,
                        'price':self.price,
                        'date_casting':self.date_casting,
                        'product_alias':self.product_alias.id,
                        'lab_location':lab_location,
                        'location_name':location_name,

                    })

                return {'type': 'ir.actions.act_window_close'}
            else:
                raise UserError("Sample Quantity Must be Greater Than Zero")

    def close_sample_wizard(self):
        return {'type': 'ir.actions.act_window_close'}

    
    class AllotSampleWizard(models.TransientModel):
        _name = "sample.allotment.wizard"
        _inherit = ['mail.thread','mail.activity.mixin']

        technicians = fields.Many2one("res.users",string="Technicians")
        

        @api.onchange('technicians')
        def onchange_technicians(self):
            users = self.env.ref('lerm_civil.kes_technician_access_group').users
            ids = []
            for user_id in users:
                ids.append(user_id.id)
            print("IDS " + str(ids))
            # import wdb; wdb.set_trace()

            return {'domain': {'technicians': [('id', 'in', ids)]}}
        

        # @api.one
        def allot_sample(self):
            # import wdb;wdb.set_trace()

            active_ids = self.env.context.get('active_ids')
            for id in active_ids:
                parameters = []
                parameters_result = []

                sample = self.env['lerm.srf.sample'].sudo().search([('id','=',id)])
                if sample.state == '1-allotment_pending':
                    for parameter in sample.parameters:
                        parameters.append((0,0,{'parameter':parameter.id ,'spreadsheet_template':parameter.spreadsheet_template.id}))
                        parameters_result.append((0,0,{'parameter':parameter.id,'unit': parameter.unit.id,'test_method':parameter.test_method.id}))
                    
                    eln_id = self.env['lerm.eln'].sudo().create({
                        'srf_id': sample.srf_id.id,
                        'srf_date':sample.srf_id.srf_date,
                        'kes_no':sample.kes_no,
                        'discipline':sample.discipline_id.id,
                        # 'lab_l_id': sample.lab_l_id.id,
                        'lab_no_value': sample.lab_no_value,
                        'group': sample.group_id.id,
                        'material': sample.material_id.id,
                        'witness_name': sample.witness,
                        # 'department_id': sample.department_id.id,
                        'sample_id':sample.id,
                        'parameters':parameters,
                        'technician': self.technicians.id,
                        'parameters_result':parameters_result,
                        'conformity':sample.conformity,
                        'has_witness':sample.has_witness,
                        'size_id':sample.size_id.id,
                        'grade_id':sample.grade_id.id,
                        'department_id':sample.department_id,
                        'casting_date':sample.casting_date,

                    })
                    # import wdb;wdb.set_trace()
                    sample.write({'state':'2-alloted' , 'technicians':self.technicians.id , 'eln_id':eln_id.id})
                else:
                    pass

         
            return {'type': 'ir.actions.act_window_close'}


        def close_allotment_wizard(self):
            return {'type': 'ir.actions.act_window_close'}
        
        def schedule_activity(self):
        # Schedule an activity for the current record
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                note='Your activity description here',
                user_id=self.env.user.id,
                date_deadline=fields.Date.today(),
                summary='Your activity summary here'
            )
            return True


