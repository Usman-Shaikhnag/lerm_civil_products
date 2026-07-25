from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class SampleFTP(models.Model):
    
    _inherit = 'lerm.srf.sample'
    
    
    report_path = fields.Char(string="Report")
    datasheet_path = fields.Char(string="Datasheet")

    
    
    
    def download_attachment_report(self):
        host = self.env["ftp.storage"].sudo().search([('active','=',True)]).host
        if not self.report_path:
            raise ValidationError("Report Not Uploaded")
        ftp_url = f"https://{host}/files/{self.report_path}"
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/binary/download_ftp?url={ftp_url}",
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
        host = self.env["ftp.storage"].sudo().search([('active','=',True)]).host
        if not self.datasheet_path:
            raise ValidationError("Datasheet Not Uploaded")
        ftp_url = f"https://{host}/files/{self.datasheet_path}"
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/binary/download_ftp?url={ftp_url}",
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