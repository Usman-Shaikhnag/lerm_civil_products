from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from odoo.addons.ftp_storage.models.dms_attachment import record_download_url

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
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': record_download_url(self, 'attachment_path'),
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
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': record_download_url(self, 'witness_path'),
            'target': 'self',
        }

