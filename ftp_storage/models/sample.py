from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from odoo.addons.ftp_storage.models.dms_attachment import record_download_url

class SampleFTP(models.Model):
    
    _inherit = 'lerm.srf.sample'
    
    
    report_path = fields.Char(string="Report")
    datasheet_path = fields.Char(string="Datasheet")

    def download_attachment_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': record_download_url(self, 'report_path'),
            'target': 'self',
        }

    def open_file_upload_report(self):
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
                'default_form_name': 'lerm.srf.sample',
                'default_field_name':'report_path'
                }
            }
    
    
    def download_attachment_datasheet(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': record_download_url(self, 'datasheet_path'),
            'target': 'self',
        }
    
    def open_file_upload_datasheet(self):
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
                'default_form_name': 'lerm.srf.sample',
                'default_field_name':'datasheet_path'
                }
            }