from odoo import api, fields, models,_
from odoo.exceptions import UserError
import logging
import wdb


class SendMailWizard(models.TransientModel):
    _name = "send.mail.wizard"

    email_from = fields.Char("Email From")
    email_to = fields.Char("Email To")
    email_subject = fields.Char("Subject")
    email_body = fields.Text("Email Body")
    attachment = fields.Binary('Attachment')
    attachment_name = fields.Char("Attachment Name")


   

    @api.model
    def default_get(self, fields_list):
        res = super(SendMailWizard, self).default_get(fields_list)

        active_id = self.env.context.get('active_id')
        if active_id:
            sample = self.env['lerm.srf.sample'].sudo().browse(active_id)
            if sample.srf_id and sample.srf_id.customer and sample.srf_id.customer.email:
                res['email_to'] = sample.srf_id.customer.email

        return res

     # def read(self, fields=None, load='_classic_read'):
    #     # import wdb ; wdb.set_trace()
    #     email_to = self.env['lerm.srf.sample'].sudo().search([('id','=',self._context['active_id'])]).srf_id.customer.email
    #     if email_to:
    #         self.email_to = email_to
    #     return super(SendMailWizard, self).read(fields=fields, load=load)
    
    # def send_mail(self):
    #     mail = self.env['mail.mail'].sudo().create({
    #         'subject': self.email_subject,
    #         'body_html': self.email_body,
    #         'email_to': self.email_to,
    #         'email_from': self.email_from,
    #     })
    #     mail.send()


    def send_mail(self):
        # Step 1: Create the attachment if it exists
        attachment_id = False
        if self.attachment:
            attachment_id = self.env['ir.attachment'].sudo().create({
                'name': self.attachment_name or 'attachment',
                'type': 'binary',
                'datas': self.attachment,
                'res_model': self._name,
                'res_id': self.id,
            })

        # Step 2: Create the mail with the attachment (if any)
        mail_values = {
            'subject': self.email_subject,
            'body_html': self.email_body,
            'email_to': self.email_to,
            'email_from': self.email_from,
        }

        if attachment_id:
            mail_values['attachment_ids'] = [(4, attachment_id.id)]

        mail = self.env['mail.mail'].sudo().create(mail_values)

        # Step 3: Send the mail
        mail.send()


    def discard_send(self):
        return {'type': 'ir.actions.act_window_close'}