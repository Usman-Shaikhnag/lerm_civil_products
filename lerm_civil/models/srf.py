from odoo import api, fields, models,_
from odoo.exceptions import UserError ,ValidationError
import logging
from datetime import datetime
import paramiko
import time
from io import BytesIO
import os
import base64
import re
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
    product = fields.Many2one('product.template',"Product")
    parameter = fields.Many2many('lerm.parameter.master',domain="[('material', '=', product)]", string="Parameter")




class SrfForm(models.Model):
    _name = "lerm.civil.srf"
    _description = "SRF"
    _inherit = ['mail.thread','mail.activity.mixin']
    _rec_name = 'srf_id'



    srf_id = fields.Char(string="SRF ID",tracking=True)
    kes_number = fields.Char(string="UID",tracking=True)
    # job_no = fields.Char(string="Job NO.")
    # srf_date = fields.Date(string="SRF Date",default=lambda self: self._get_default_date(),tracking=True)
    srf_date = fields.Date(
        string="SRF Date",
        default=fields.Date.context_today,
        tracking=True
    )
    job_date = fields.Date(string="JOB Date")
    customer = fields.Many2one('res.partner',string="Customer",tracking=True)
    billing_customer = fields.Many2one('res.partner',string="Billing Customer")
    contact_person = fields.Many2one('res.partner',string="Contact Person")
    client = fields.Char("Client")
    # site_address = fields.Many2one('res.partner',string="Site Address")
    site_address = fields.Char(string="Site Address",compute="_compute_site_address")
    name_work = fields.Many2one('res.partner.project',string="Name of Work")

    consultant_name1 = fields.Char(string="Consultant Name")
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
    
    attachment_path = fields.Char("Attachment")
    customer_portal_request = fields.Many2one('customer.sample.line',string="Customer Portal Request", readonly=True)

    
    def download_attachment(self):
        host = self.env["ftp.storage"].sudo().search([('active','=',True)]).host
        ftp_url = f"https://{host}/files/{self.attachment_path}"
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/binary/download_ftp?url={ftp_url}",
            'target': 'self',
        }


    
    def open_file_upload(self):
        action = self.env.ref('lerm_civil.view_ftp_upload_wizard_form')
        return {
            'name': "Upload File Wizard",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'file.upload.wizard',
            'view_id': action.id,
            'target': 'new',
            'context': {
                'default_form_name': 'lerm.civil.srf',
                'default_field_name':'attachment_path'
                }
            }


    def _compute_date_editable(self):
        for record in self:
            # print("COMPUTE SRF DATE")
            # import wdb;wdb.set_trace()

            backdate_group_id = record.env.ref('lerm_civil.kes_srf_backdate_creation_group').id

            if backdate_group_id in self.env.user.groups_id.ids:
                record.date_editable = True
            else:
                record.date_editable = False

    def read(self, fields=None, load='_classic_read'):

        self._compute_date_editable()
        
        return super(SrfForm, self).read(fields=fields, load=load)


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



    # def confirm_srf(self):
    #     srf_ids=[]
        
    #     # import wdb; wdb.set_trace()
        
    #     count = self.env['lerm.srf.sample'].search_count([('srf_id.srf_date','=',self.srf_date),('kes_no','!=','New'),('status','=','2-confirmed')]) 

    #     for record in self.sample_range_table:
    #         sam_next_number = self.env['ir.sequence'].search([('code','=','lerm.srf.sample')]).number_next_actual
    #         kes_next_number = self.env['ir.sequence'].search([('code','=','lerm.srf.sample.kes')]).number_next_actual
           
    #         sample_range = "SAM/"+str(sam_next_number)+"-"+str(sam_next_number+record.sample_qty-1)
    #         kes_range = "LERM/"+str(count+1)+"-"+str(count+1+record.sample_qty-1)
    #         record.write({'sample_range': sample_range , 'kes_range': kes_range })
    #         samples = self.env['lerm.srf.sample'].search([('sample_range_id','=',record.id)])
            
            
    #         for sample in samples:
    #             # import wdb; wdb.set_trace()
    #             sample_id = self.env['ir.sequence'].next_by_code('lerm.srf.sample') or 'New'

    #             year = str(self.srf_date.year)[-2:]
    #             month = str(self.srf_date.month).zfill(2)
    #             day = str(self.srf_date.day).zfill(2)
    #             count = count + 1

    #             kes_no = "LERM/TR/"+ year+month+day + str(count).zfill(3) or "New"

    #             kes_no_daywise = self.env['ir.sequence'].next_by_code('lerm.sample.daywise.seq') 
    #             # kes_no = self.env['ir.sequence'].next_by_code('lerm.srf.sample.kes') + kes_no_daywise or 'New'
    #             # lab_l_id =  self.env['lab.location'].search([('id','=',self.env.context['allowed_company_ids'][0])])
    #             company =  self.env['res.company'].search([('id','=',self.env.context['allowed_company_ids'][0])])
                
    #             if sample.scope == 'nabl':

    #                 if sample.lab_location:
    #                     code = sample.lab_location.ulr_sequence.code
    #                     seqq = self.env['ir.sequence'].sudo().search([('code', '=', code)], limit=1)

    #                     matched_record = None
    #                     for date_range in seqq.date_range_ids:
    #                         if date_range.date_from <= self.srf_date <= date_range.date_to:
    #                             matched_record = date_range
    #                             break

    #                     lab_loc = sample.location_name.location_code or ''
    #                     lab_cert_no = sample.lab_location.lab_certificate_no or ''
    #                     padding = int(seqq.padding or 5)
    #                     suffix = seqq.suffix or ''

    #                     if matched_record:
    #                         next_actual = str(matched_record.number_next_actual)
    #                         ulr_no = lab_cert_no + year + lab_loc + next_actual.zfill(padding) + suffix

    #                         # Increment and save the updated next number
    #                         matched_record.sudo().write({
    #                             'number_next_actual': matched_record.number_next_actual + 1
    #                         })
    #                     else:
    #                         # Fall back to next_by_code
    #                         ulr_no = self.env['ir.sequence'].next_by_code(code) or 'New'




    #                     # code = sample.lab_location.ulr_sequence.code
    #                     # ulr_no = self.env['ir.sequence'].next_by_code(code) or 'New'
    #                     # lab_loc = sample.location_name.location_code
    #                     # lab_cert_no = sample.lab_location.lab_certificate_no
    #                     # ulr_no = ulr_no.replace('(lab_certificate_no)', lab_cert_no)                
    #                     # ulr_no = ulr_no.replace('(lab_no_value)', lab_loc)
                        


    #                 else:
    #                     lab_loc = str(sample.lab_no_value)
    #                     lab_cert_no = str(company.lab_certificate_no)
    #                     # lab_loc = company.lab_seq_no
    #                     ulr_no = self.env['ir.sequence'].next_by_code('sample.ulr.seq') or 'New'
    #                     ulr_no = ulr_no.replace('(lab_certificate_no)', lab_cert_no)                
    #                     ulr_no = ulr_no.replace('(lab_no_value)', lab_loc)
    #             else:
    #                 ulr_no = ''
    #             # import wdb ; wdb.set_trace()
              
    #             sample.write({'sample_no':sample_id,'kes_no':kes_no,'status':'2-confirmed','ulr_no':ulr_no})
    #             self.env.cr.commit()
        
    
    #     first_sample_range = self.sample_range_table[0].kes_range
    #     last_sample_range = self.sample_range_table[-1].kes_range  
    #     first_samplerange_slash_index = first_sample_range.find("/")
    #     srffirstnumber_str = first_sample_range[first_samplerange_slash_index+1:first_sample_range.find("-")]
    #     last_sample_range_index = last_sample_range.find("-")
    #     srf_last_number = last_sample_range[last_sample_range_index+1:]

      
    #     modified_srf_id = f"SRF/"+year+month+day+srffirstnumber_str.zfill(3)+"-"+year+month+day+srf_last_number.zfill(3)
    #     modified_kes_number = f"LERM/TR/DUS"
    #     self.write({'srf_id': modified_srf_id})
    #     self.write({'kes_number': modified_kes_number})
    #     self.write({'state': '2-confirm'})
        
        
    #     attachment_path = self.attachment_path
    #     pattern = r'(?<=/)\d+(?=/)'

    #     if attachment_path:
    #         if re.search(pattern, attachment_path):
    #             # Replace the number with your desired value (e.g., 'XX')
    #             old_path = re.sub(pattern, str(self.id) , attachment_path)
    #             # import wdb;wdb.set_trace()
    #             file_name = old_path.rsplit('/', 1)[1]
                
    #             old_path = old_path.rsplit('/', 1)[0]
                
                
    #             new_path = re.sub(pattern, self.srf_id.replace("/", "").replace("-", ""), attachment_path)
    #             # import wdb;wdb.set_trace()
                
    #             new_path = new_path.rsplit('/', 1)[0]

                
                
    #             ftp_storage = self.env["ftp.storage"].search([("active","=",True)])
                
    #             transport = paramiko.Transport((ftp_storage.host, ftp_storage.port or 22))
    #             transport.banner_timeout = 60
    #             transport.connect(
    #                 username=ftp_storage.username,
    #                 password=ftp_storage.password
    #             )
    #             sftp = paramiko.SFTPClient.from_transport(transport)
                
    #             # sftp.rename("/home/"+old_path,"/home/"+new_path)
                

    #             try:
    #                 print(f"Source file attributes: {sftp.stat('/home/' + old_path)}")
    #             except FileNotFoundError:
    #                 print("ERROR: Source file doesn't exist!")
    #                 # List directory contents to see what's actually there
    #                 dir_path = os.path.dirname('/home/' + old_path)
    #                 print(f"Contents of {dir_path}: {sftp.listdir(dir_path)}")
                
    #             # Perform the rename
    #             # import wdb;wdb.set_trace()
                
    #             try:
    #                 sftp.rename("/home/"+old_path, "/home/"+new_path)
    #                 self.write({'attachment_path': new_path+"/"+file_name})
    #             except Exception as e:
    #                 print(f"Rename failed: {str(e)}")
    #                 raise



    #             sftp.close()
                
                
                
    #         else:
    #             print("No number found in the middle")
            
        
        
        # for record in self:


    



    # def confirm_srf(self):
    #     import re
    #     import paramiko
    #     import os

    #     for rec in self:

    #         # -----------------------
    #         # SRF SEQUENCE
    #         # -----------------------
    #         srf_seq = self.env['ir.sequence'].search([
    #             ('code', '=', 'lerm.srf.main.seq')
    #         ], limit=1)

    #         srf_first = self.env['ir.sequence'].next_by_code('lerm.srf.main.seq')

    #         prefix = srf_first.rsplit('/', 1)[0]

    #         # ✅ FIX: Only take last 3 digits
    #         full_number = srf_first.rsplit('/', 1)[1]
    #         first_number = int(full_number[-3:])

    #         total_samples = sum(rec.sample_range_table.mapped('sample_qty'))
    #         last_number = first_number + total_samples - 1

    #         # ✅ UPDATE SRF SEQUENCE POINTER (SAFE)
    #         if srf_seq:
    #             srf_seq.sudo().write({
    #                 'number_next_actual': last_number + 1
    #             })

    #         modified_srf_id = "%s/%s-%s" % (
    #             prefix,
    #             str(first_number).zfill(3),
    #             str(last_number).zfill(3)
    #         )

    #         # -----------------------
    #         # KES SEQUENCE
    #         # -----------------------
    #         kes_seq = self.env['ir.sequence'].search([
    #             ('code', '=', 'lerm.kes.main.seq')
    #         ], limit=1)

    #         kes_first = self.env['ir.sequence'].next_by_code('lerm.kes.main.seq')
    #         kes_prefix = kes_first.rsplit('/', 1)[0]

    #         # ✅ FIX: only last 3 digits
    #         kes_full = kes_first.rsplit('/', 1)[1]
    #         kes_counter = int(kes_full[-3:])

    #         # ✅ SYNC KES SEQUENCE
    #         if kes_seq:
    #             kes_seq.sudo().write({
    #                 'number_next_actual': last_number + 1
    #             })

    #         # Start from SRF first number
    #         kes_counter = first_number

    #         # -----------------------
    #         # SAMPLE PROCESS
    #         # -----------------------
    #         for range_line in rec.sample_range_table:

    #             sam_seq = self.env['ir.sequence'].search([
    #                 ('code', '=', 'lerm.srf.sample')
    #             ], limit=1)

    #             sam_next = sam_seq.number_next_actual

    #             sample_range = "SAM/%s-%s" % (
    #                 sam_next,
    #                 sam_next + range_line.sample_qty - 1
    #             )

    #             # Update sample sequence
    #             sam_seq.sudo().write({
    #                 'number_next_actual': sam_next + range_line.sample_qty
    #             })

    #             # -----------------------
    #             # KES RANGE
    #             # -----------------------
    #             kes_start_num = kes_counter
    #             kes_end_number = kes_counter + range_line.sample_qty - 1

    #             kes_range = "%s/%s-%s" % (
    #                 kes_prefix,
    #                 str(kes_start_num).zfill(3),
    #                 str(kes_end_number).zfill(3)
    #             )

    #             range_line.write({
    #                 'sample_range': sample_range,
    #                 'kes_range': kes_range
    #             })

    #             # -----------------------
    #             # FETCH SAMPLES
    #             # -----------------------
    #             samples = self.env['lerm.srf.sample'].search([
    #                 ('sample_range_id', '=', range_line.id)
    #             ])

    #             for sample in samples:

    #                 sample_no = self.env['ir.sequence'].next_by_code('lerm.srf.sample') or 'New'

    #                 kes_no = "%s/%s" % (
    #                     kes_prefix,
    #                     str(kes_counter).zfill(3)
    #                 )

    #                 kes_counter += 1

    #                 # -----------------------
    #                 # ULR
    #                 # -----------------------
    #                 ulr_no = ''
    #                 if sample.scope == 'nabl':

    #                     seq_val = self.env['ir.sequence'].next_by_code('sample.ulr.seq') or 'New'

    #                     lab = sample.lab_location
    #                     lab_cert = lab.lab_certificate_no or ''
    #                     lab_loc = sample.location_name.location_code if sample.location_name else ''

    #                     ulr_no = seq_val.replace('(lab_certificate_no)', lab_cert)\
    #                                     .replace('(lab_no_value)', lab_loc)

    #                 sample.write({
    #                     'sample_no': sample_no,
    #                     'kes_no': kes_no,
    #                     'status': '2-confirmed',
    #                     'ulr_no': ulr_no
    #                 })

    #         # -----------------------
    #         # WRITE SRF
    #         # -----------------------
    #         rec.write({
    #             'srf_id': modified_srf_id,
    #             'kes_number': "%s/%s" % (
    #                 kes_prefix,
    #                 str(first_number).zfill(3)
    #             ),
    #             'state': '2-confirm'
    #         })

    #         # -----------------------
    #         # FTP RENAME
    #         # -----------------------
    #         attachment_path = rec.attachment_path
    #         pattern = r'(?<=/)\d+(?=/)'

    #         if attachment_path and re.search(pattern, attachment_path):

    #             old_path = re.sub(pattern, str(rec.id), attachment_path)

    #             file_name = old_path.rsplit('/', 1)[1]
    #             old_dir = old_path.rsplit('/', 1)[0]

    #             new_path = re.sub(
    #                 pattern,
    #                 rec.srf_id.replace("/", "").replace("-", ""),
    #                 attachment_path
    #             )

    #             new_dir = new_path.rsplit('/', 1)[0]

    #             ftp_storage = self.env["ftp.storage"].search([
    #                 ("active", "=", True)
    #             ], limit=1)

    #             transport = paramiko.Transport(
    #                 (ftp_storage.host, ftp_storage.port or 22)
    #             )

    #             transport.connect(
    #                 username=ftp_storage.username,
    #                 password=ftp_storage.password
    #             )

    #             sftp = paramiko.SFTPClient.from_transport(transport)

    #             try:
    #                 sftp.rename(
    #                     "/home/" + old_dir,
    #                     "/home/" + new_dir
    #                 )

    #                 rec.write({
    #                     'attachment_path': new_dir + "/" + file_name
    #                 })

    #             except Exception as e:
    #                 raise Exception("FTP Rename Failed: %s" % str(e))

    #             sftp.close()

 

    def confirm_srf(self):
        import re
        import paramiko

        for rec in self:

            # -----------------------
            # SRF SEQUENCE
            # -----------------------
            srf_seq = self.env['ir.sequence'].search([
                ('code', '=', 'lerm.srf.main.seq')
            ], limit=1)

            srf_first = self.env['ir.sequence'].next_by_code('lerm.srf.main.seq')

            srf_parts = srf_first.split('/')

            base_prefix = srf_parts[0]
            full_part = srf_parts[1]

            date_part = full_part[:6]
            first_number = int(full_part[-3:])

            total_samples = sum(rec.sample_range_table.mapped('sample_qty'))
            last_number = first_number + total_samples - 1

            if srf_seq:
                srf_seq.sudo().write({
                    'number_next_actual': last_number + 1
                })

            modified_srf_id = "%s/%s%s-%s%s" % (
                base_prefix,
                date_part,
                str(first_number).zfill(3),
                date_part,
                str(last_number).zfill(3)
            )

            # -----------------------
            # SAMPLE PROCESS
            # -----------------------
            for range_line in rec.sample_range_table:

                sam_seq = self.env['ir.sequence'].search([
                    ('code', '=', 'lerm.srf.sample')
                ], limit=1)

                sam_next = sam_seq.number_next_actual

                sample_range = "SAM/%s-%s" % (
                    sam_next,
                    sam_next + range_line.sample_qty - 1
                )

                sam_seq.sudo().write({
                    'number_next_actual': sam_next + range_line.sample_qty
                })

                # ❌ DO NOT CALL KES SEQUENCE HERE
                # ❌ NO LOOP FOR KES RANGE

                range_line.write({
                    'sample_range': sample_range,
                    'kes_range': ''
                })

                # -----------------------
                # SAMPLES
                # -----------------------
                samples = self.env['lerm.srf.sample'].search([
                    ('sample_range_id', '=', range_line.id)
                ])

                for sample in samples:

                    sample_no = self.env['ir.sequence'].next_by_code('lerm.srf.sample') or 'New'

                    # ✅ SINGLE CALL ONLY (NO JUMP)
                    kes_no = self.env['ir.sequence'].next_by_code('lerm.kes.main.seq')

                    ulr_no = ''
                    if sample.scope == 'nabl':

                        seq_val = self.env['ir.sequence'].next_by_code('sample.ulr.seq') or 'New'

                        lab = sample.lab_location
                        lab_cert = lab.lab_certificate_no or ''
                        lab_loc = sample.location_name.location_code if sample.location_name else ''

                        ulr_no = seq_val.replace('(lab_certificate_no)', lab_cert)\
                                        .replace('(lab_no_value)', lab_loc)

                    sample.write({
                        'sample_no': sample_no,
                        'kes_no': kes_no,
                        'status': '2-confirmed',
                        'ulr_no': ulr_no
                    })

            # -----------------------
            # FINAL WRITE
            # -----------------------
            rec.write({
                'srf_id': modified_srf_id,
                'kes_number': kes_no,
                'state': '2-confirm'
            })

            # -----------------------
            # FTP RENAME
            # -----------------------
            attachment_path = rec.attachment_path
            pattern = r'(?<=/)\d+(?=/)'

            if attachment_path and re.search(pattern, attachment_path):

                old_path = re.sub(pattern, str(rec.id), attachment_path)

                file_name = old_path.rsplit('/', 1)[1]
                old_dir = old_path.rsplit('/', 1)[0]

                new_path = re.sub(
                    pattern,
                    rec.srf_id.replace("/", "").replace("-", ""),
                    attachment_path
                )

                new_dir = new_path.rsplit('/', 1)[0]

                ftp_storage = self.env["ftp.storage"].search([
                    ("active", "=", True)
                ], limit=1)

                transport = paramiko.Transport(
                    (ftp_storage.host, ftp_storage.port or 22)
                )

                transport.connect(
                    username=ftp_storage.username,
                    password=ftp_storage.password
                )

                sftp = paramiko.SFTPClient.from_transport(transport)

                try:
                    sftp.rename(
                        "/home/" + old_dir,
                        "/home/" + new_dir
                    )

                    rec.write({
                        'attachment_path': new_dir + "/" + file_name
                    })

                except Exception as e:
                    raise Exception("FTP Rename Failed: %s" % str(e))

                sftp.close()
            





    
    
   
    

    

    # name_of_work = fields.Many2one('res.partner.project',string='Name of Work')
    last_srf_number = fields.Integer(string="Last SRF Number", default=0)

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
            contact_ids = self.env['res.partner'].search([('parent_id', '=', record.customer.id)])
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
            discipline_id = samples[-1].discipline_id.id
            group_id = samples[-1].group_id.id
            material_id = samples[-1].material_id.id
            # lab_l_id = samples[-1].lab_l_id.id
            lab_no_value = samples[-1].lab_no_value
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
            # import wdb ; wdb.set_trace()


            return {
            'name': "Add Sample",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.srf.sample.wizard',
            'view_id': action.id,
            'target': 'new',
            'context': {
                'default_discipline_id' : discipline_id,
                'default_group_id':group_id,
                'default_material_id' : material_id,
                'default_alias':alias,
                'default_brand':brand,
                'default_size_id':size_id,
                'default_grade_id':grade_id,
                'default_location':location,
                'default_sample_condition':sample_condition,
                'default_sample_reject_reason':sample_reject_reason,
                'default_witness':witness,
                # 'default_department_id':department_id,
                'default_scope':scope,
                'default_sample_description':sample_description,
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
    location = fields.Char(string="Location Code")
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
    customer_id = fields.Many2one('res.partner' , string="Customer",compute="_compute_customer_id")
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
    lab_location = fields.Many2one('lerm.lab.master',string="Lab Name",default=lambda self: self._get_oldest_lab())
    location_name = fields.Many2one('lerm.lab.location.master',string="Location Name")
    customer = fields.Many2one('res.partner', string="Customer")

    show_reject_reason = fields.Boolean(compute='_compute_show_reject_reason')
    show_witness = fields.Boolean(compute='_compute_show_witness')
    show_days_casting = fields.Boolean(compute='_compute_show_casting')
    is_readonly_qty = fields.Boolean(compute='_compute_is_readonly_qty')
    
    available_parameter_ids = fields.Many2many(
        'lerm.parameter.master',
        compute='_compute_available_parameters',
        string='Available Parameters'
    )

    @api.model
    def _get_oldest_lab(self):
        oldest_lab = self.env['lerm.lab.master'].search([], order="create_date asc", limit=1)
        return oldest_lab.id if oldest_lab else False

    @api.onchange('lab_location')
    def _default_location_name(self):
        for record in self:
            if record.lab_location and len(record.lab_location.lab_location_line) > 0:
                record.location_name = record.lab_location.lab_location_line[0]

    # @api.onchange('lab_location')
    # def _default_location(self):
    #     for record in self:
    #         if record.lab_location and len(record.lab_location.lab_location_line) > 0:
    #             record.location = record.lab_location.lab_location_line[0]

    @api.onchange('lab_location')
    def _default_location(self):
        for record in self:
            location_code = False
            if record.lab_location and record.lab_location.lab_location_line:
                location_line = record.lab_location.lab_location_line[0]
                location_code = location_line.location_code

            record.location = location_code


    @api.depends('material_id')
    def _compute_available_parameters(self):
        for rec in self:
            if rec.material_id:
                rec.available_parameter_ids = rec.material_id.parameter_table1
            else:
                rec.available_parameter_ids = [(5, 0, 0)]  # clear


    quantity = fields.Integer(string="Quantity")
    # sample_quantity = fields.Integer(string="Sample Quantity")
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")  # kg, mm, etc.
    quantity_received = fields.Integer(string="Quantiyty Received")
    quantity_consumed = fields.Integer(string="Quantity Consumed")
    quantity_balance = fields.Integer(string="Quantity Balance", compute="compute_quantity_balance", readonly=True)

    @api.depends('quantity_received', 'quantity_consumed')
    def compute_quantity_balance(self):
        for rec in self:
            rec.quantity_balance = rec.quantity_received - rec.quantity_consumed
    @api.depends('sample_condition')
    def _compute_show_reject_reason(self):
        for rec in self:
            rec.show_reject_reason = rec.sample_condition == 'non_satisfactory'

    @api.depends('has_witness')
    def _compute_show_witness(self):
        for rec in self:
            rec.show_witness = rec.has_witness

    @api.depends('casting')
    def _compute_show_casting(self):
        for rec in self:
            rec.show_days_casting = rec.casting

    @api.depends('is_update')
    def _compute_is_readonly_qty(self):
        for rec in self:
            rec.is_readonly_qty = rec.is_update


    @api.depends('customer')
    def _compute_customer_id(self):
        for rec in self:
            rec.customer_id = rec.customer if rec.customer else False

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

        # import wdb; wdb.set_trace()
        for record in self:
            if record.material_id:
                parameters_ids = []
                print("MATERIAL__IDD",self.env['product.template'].search([('id','=', record.material_id.id)]))
                product_records = self.env['product.template'].search([('id','=', record.material_id.id)]).parameter_table1
                record.product_name = self.pricelist.item_ids.search([('pricelist_id','=',self.pricelist.id),('product_tmpl_id.lab_name','=',self.material_id.lab_name)]).product_tmpl_id.id
                for rec in product_records:
                    parameters_ids.append(rec.id)
                # domain = {'parameters': [('id', 'in', parameters_ids)]}
                # return {'domain': domain}
                # import wdb; wdb.set_trace()
                return {'domain': {'parameters': [('id', 'in', parameters_ids)]}}
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
                    
                    sample = self.env["lerm.srf.sample"].create({
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
                        'quantity':self.quantity,
                        'uom_id':self.uom_id.id,
                        'quantity_received':self.quantity_received,
                        'quantity_consumed':self.quantity_consumed,
                        'quantity_balance':self.quantity_balance

                    })
                    self.env['lerm.sample.register'].sudo().create({
                        'sample':sample.id,
                        'quantity':self.quantity,
                        'uom_id':self.uom_id.id,
                        'quantity_received':self.quantity_received,
                        'quantity_consumed':self.quantity_consumed,
                        'quantity_balance':self.quantity_balance

                    })

                return {'type': 'ir.actions.act_window_close'}
            else:
                raise UserError("Sample Quantity Must be Greater Than Zero")

    def close_sample_wizard(self):
        return {'type': 'ir.actions.act_window_close'}

    
    class AllotSampleWizard(models.TransientModel):
        _name = "sample.allotment.wizard"
        _inherit = ['mail.thread','mail.activity.mixin']

        allocation_type = fields.Selection(
            [('sample','Sample'), ('parameter','Parameter')],
            string='Allocate By',
            default='sample',
            required=True,
        )

        # used in Sample mode (single tech)
        technicians = fields.Many2one("res.users", string="Technician")

        # used in Parameter mode (final technician set to be stored in ELN)
        technician_ids = fields.Many2many('res.users',string='Technicians',store=True)

        allowed_technician_domain_ids = fields.Many2many(
            'res.users',
            compute='_compute_allowed_technician_domain_ids',
            store=False
        )

        sample_id = fields.Many2one('lerm.srf.sample', string='Sample')   # optional
        line_ids = fields.One2many('sample.allot.line', 'wizard_id', string='Parameters')

        @api.depends('sample_id', 'sample_id.lab_location')
        def _compute_allowed_technician_domain_ids(self):
            for wizard in self:
                if wizard.sample_id and wizard.sample_id.lab_location:
                    lab = wizard.sample_id.lab_location
                    employees = self.env['hr.employee'].sudo().search([
                        ('lab_ids', 'in', [lab.id])
                    ])
                    employee_user_ids = employees.mapped('user_id').ids
                    wizard.allowed_technician_domain_ids = [(6, 0, employee_user_ids)]
                else:
                    wizard.allowed_technician_domain_ids = [(5,)]


        @api.model
        def default_get(self, fields):
            res = super().default_get(fields)
            active_ids = self.env.context.get('active_ids') or []
            if not active_ids:
                return res

            # Only support one sample in parameter mode
            sample = self.env['lerm.srf.sample'].browse(active_ids[0])

            res['sample_id'] = sample.id

            lines = []

            eln = sample.eln_id.sudo()

            for param in sample.parameters:
                assigned_tech = False
                is_locked = False

                # If ELN exists, try to find existing parameter_result
                if eln:
                    pr = eln.parameters_result.sudo().filtered(lambda r: r.parameter.id == param.id)
                    if pr and pr[0].technician:
                        assigned_tech = pr[0].technician.id
                        is_locked = True

                lines.append((0, 0, {
                    'sample_id': sample.id,
                    'parameter_id': param.id,
                    'technician': assigned_tech,
                    'is_locked': is_locked,
                }))

            res['line_ids'] = lines
            if sample.eln_id:
                res['allocation_type'] = 'parameter'


            return res

    
        @api.onchange('allocation_type')
        def _onchange_allocation_type(self):
            # When switching to parameter mode, populate technician_ids from sample.parameters if active_ids present
            if self.allocation_type == 'parameter':
                active_ids = self.env.context.get('active_ids') or []
                techs = self.env['res.users']
                for sid in active_ids:
                    sample = self.env['lerm.srf.sample'].browse(sid)
                    # import wdb;wdb.set_trace()
                    for param in sample.parameters:
                        if hasattr(param, 'allowed_technicians'):
                            techs |= param.allowed_technicians
                if techs:
                    self.technician_ids = [(6, 0, techs.ids)]
            else:
                # clear technician_ids on sample mode switch
                self.technician_ids = [(5,)]

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
            active_ids = self.env.context.get('active_ids') or []
            is_reallocation = self.env.context.get('is_reallocation', False)  # 🔑 CHECK FLAG
            
            if not active_ids:
                raise UserError(_("No samples selected."))

            Sample = self.env['lerm.srf.sample'].sudo()
            ELN = self.env['lerm.eln'].sudo()

            for rec_id in active_ids:
                sample = Sample.browse(rec_id)
                if not sample or sample.state not in ('1-allotment_pending', '7-partially-alloted', '2-alloted'):  # 🔑 ALLOW '2-alloted' FOR REALLOCATION
                    if not is_reallocation:  # 🔑 ONLY ENFORCE STATE CHECK IF NOT REALLOCATION
                        continue

                # Prepare variables
                parameters_result = []
                eln_tech_ids = []

                if self.allocation_type == 'parameter':
                    # enforce single-sample mode (recommended)
                    if len(active_ids) > 1:
                        raise UserError(_("Parameter allocation supports only one sample at a time. Select a single sample."))

                    if not self.line_ids:
                        raise UserError(_("No parameters available to assign."))

                    # Determine new sample state: fully alloted if no unassigned lines else partially alloted
                    existing_param_tech = {}
                    if sample.eln_id:
                        for pr in sample.eln_id.parameters_result:
                            existing_param_tech[pr.parameter.id] = pr.technician.id if pr.technician else False

                    # Partition lines into assigned / unassigned
                    valid_lines = [line for line in self.line_ids if line.parameter_id]

                    assigned_lines = [line for line in valid_lines if line.technician]
                    unassigned_lines = []

                    for line in valid_lines:
                        param_id = line.parameter_id.id
                        wizard_tech = line.technician.id if line.technician else False
                        existing_tech = existing_param_tech.get(param_id)

                        # unassigned ONLY if neither wizard nor existing ELN has technician
                        if not wizard_tech and not existing_tech:
                            unassigned_lines.append(line)


                    if len(assigned_lines) == 0:
                        # No technician assigned at all → not allowed
                        raise UserError(_("Please assign at least one technician."))

                    # Build parameter rows from lines (only for this sample)
                    params_for_eln = []
                    tech_ids_from_lines = set()
                    for line in self.line_ids:
                        if line.sample_id and line.sample_id.id != sample.id:
                            continue

                        # 🔑 Skip locked check during reallocation
                        if line.is_locked and not is_reallocation:
                            continue 
                            
                        if not line.parameter_id:
                            continue
                        params_for_eln.append(line.parameter_id)
                        parameters_result.append((0, 0, {
                            'parameter': line.parameter_id.id,
                            'unit': line.parameter_id.unit.id if line.parameter_id.unit else False,
                            'test_method': line.parameter_id.test_method.id if line.parameter_id.test_method else False,
                            'technician': line.technician.id if line.technician else False,
                        }))
                        if line.technician:
                            tech_ids_from_lines.add(line.technician.id)

                    # Prefer user-edited union (tag field). If not present, use line assignments union.
                    eln_tech_ids = self.technician_ids.ids if self.technician_ids else list(tech_ids_from_lines)

                    # If still empty, fallback to allowed_technicians union from parameter masters
                    if not eln_tech_ids:
                        techs = self.env['res.users']
                        for param in sample.parameters:
                            if hasattr(param, 'allowed_technicians'):
                                techs |= param.allowed_technicians
                        eln_tech_ids = techs.ids

                    if not eln_tech_ids:
                        raise UserError(_("No technicians available/selected for Parameter mode."))


                    new_state = '2-alloted' if len(unassigned_lines) == 0 else '7-partially-alloted'

                else:
                    # Sample mode: single technician applies to all parameters
                    parameters_result = []
                    for parameter in sample.parameters:
                        parameters_result.append((0, 0, {
                            'parameter': parameter.id,
                            'unit': parameter.unit.id if parameter.unit else False,
                            'test_method': parameter.test_method.id if parameter.test_method else False,
                            'technician': self.technicians.id
                        }))

                    if not self.technicians:
                        raise UserError(_("Please choose a technician for Sample mode."))
                    eln_tech_ids = [self.technicians.id]
                    new_state = '2-alloted'

                # If an ELN already exists for this sample, update it instead of creating a new one
                if sample.eln_id:
                    eln = ELN.browse(sample.eln_id.id)
                    if not eln:
                        # defensive: if eln_id set but record missing, create a new one
                        eln = None
                else:
                    eln = None

                # If ELN exists: update technicians (union) and add any missing parameter lines
                if eln:
                    # union existing technicians with new ones
                    existing_tech_ids = eln.technician_ids.ids or []
                    combined_tech_ids = list(set(existing_tech_ids) | set(eln_tech_ids))

                    # update technician_ids
                    eln.write({'technician_ids': [(6, 0, combined_tech_ids)]})

                    # add missing parameter_result lines (avoid duplicates)
                    existing_results = {
                        pr.parameter.id: pr
                        for pr in eln.parameters_result
                    }

                    for pr in parameters_result:
                        vals = pr[2]
                        param_id = vals.get('parameter')
                        technician_id = vals.get('technician')

                        if param_id in existing_results:
                            # 🔑 UPDATE existing line - ALWAYS UPDATE DURING REALLOCATION
                            existing_pr = existing_results[param_id]

                            if is_reallocation:
                                # During reallocation, always update the technician
                                existing_pr.write({
                                    'technician': technician_id if technician_id else False
                                })
                            elif technician_id and not existing_pr.technician:
                                # During initial allotment, only update if no existing technician
                                existing_pr.write({
                                    'technician': technician_id
                                })
                        else:
                            # CREATE new line
                            eln.write({'parameters_result': [(0, 0, vals)]})
                else:
                    # Create a new ELN
                    eln_vals = {
                        'srf_id': sample.srf_id.id if sample.srf_id else False,
                        'srf_date': sample.srf_id.srf_date if sample.srf_id else False,
                        'kes_no': sample.kes_no,
                        'discipline': sample.discipline_id.id if sample.discipline_id else False,
                        'lab_no_value': sample.lab_no_value,
                        'group': sample.group_id.id if sample.group_id else False,
                        'material': sample.material_id.id if sample.material_id else False,
                        'witness_name': sample.witness,
                        'sample_id': sample.id,
                        'parameters_result': parameters_result,
                        'technician_ids': [(6, 0, eln_tech_ids)],
                        'conformity': sample.conformity,
                        'has_witness': sample.has_witness,
                        'size_id': sample.size_id.id if sample.size_id else False,
                        'grade_id': sample.grade_id.id if sample.grade_id else False,
                        'department_id': sample.department_id,
                        'casting_date': sample.casting_date,
                        'quantity': sample.quantity,
                        'uom_id': sample.uom_id.id if sample.uom_id else False,
                        'quantity_received': sample.quantity_received,
                        'quantity_consumed': sample.quantity_consumed,
                        'quantity_balance': sample.quantity_balance,
                    }
                    eln = ELN.create(eln_vals)

                # Update sample state and link eln if not already linked
                # if new_state == '2-alloted':
                #     eln.write({'state': '2-confirm'})
                # else:
                #     eln.write({'state': '1-draft'})
                sample_vals = {'state': new_state, 'eln_id': eln.id}
                sample.write(sample_vals)

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


class SampleAllotLine(models.TransientModel):
    _name = 'sample.allot.line'
    _description = 'Sample Allotment Line (wizard)'

    wizard_id = fields.Many2one('sample.allotment.wizard', ondelete='cascade')
    sample_id = fields.Many2one('lerm.srf.sample', string='Sample')
    parameter_id = fields.Many2one('lerm.parameter.master', string='Parameter', required=True)
    technician = fields.Many2one('res.users', string='Technician')

    # 🔑 helper field
    allowed_technician_ids = fields.Many2many(
        'res.users',
        compute='_compute_allowed_technicians',
        store=False
    )
    is_locked = fields.Boolean(string="Locked", default=False)

    @api.depends('parameter_id')
    def _compute_allowed_technicians(self):
        for line in self:
            line.allowed_technician_ids = (
                line.parameter_id.allowed_technicians
                if line.parameter_id
                else self.env['res.users']
            )

    @api.onchange('parameter_id')
    def _onchange_parameter_id(self):
        if self.parameter_id and hasattr(self.parameter_id, 'allowed_technicians'):
            return {'domain': {'technician': [('id', 'in', self.parameter_id.allowed_technicians.ids)]}}
        return {}