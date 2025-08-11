from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ElnFTP(models.Model):
    _inherit = 'lerm.eln'
    
    witness_path = fields.Char(string="Witness")
    attachment_path = fields.Char(string="Attachment")
    
    
    
    def open_attachment_path_upload(self):
        action = self.env.ref('ftp_storage.view_ftp_upload_wizard_form')
        return {
            'name': "Upload File Wizard",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'file.upload.wizard',
            'view_id': action.id,
            'target': 'new',
            'context': {
                'default_form_name': 'lerm.eln',
                'default_field_name':'attachment_path'
                }
            }

    def download_attachment(self):
        host = self.env["ftp.storage"].sudo().search([('active','=',True)]).host
        ftp_url = f"https://{host}/files/{self.attachment_path}"
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/binary/download_ftp?url={ftp_url}",
            'target': 'self',
        }
    
   
    def open_witness_photo_upload(self):
        action = self.env.ref('ftp_storage.view_ftp_upload_wizard_form')
        return {
            'name': "Upload File Wizard",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'file.upload.wizard',
            'view_id': action.id,
            'target': 'new',
            'context': {
                'default_form_name': 'lerm.eln',
                'default_field_name':'witness_path'
                }
            }
    
    def download_witness_photo(self):
        host = self.env["ftp.storage"].sudo().search([('active','=',True)]).host
        ftp_url = f"https://{host}/files/{self.witness_path}"
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/binary/download_ftp?url={ftp_url}",
            'target': 'self',
        }

