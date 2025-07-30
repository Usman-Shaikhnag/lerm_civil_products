from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging
import paramiko
import time
from io import BytesIO
import os
import base64



class UploadWizard(models.TransientModel):
    _name = "file.upload.wizard"
    _description = "SFTP File Upload Wizard"
    
    def _default_ftp_storage_id(self):
        return self.env['ftp.storage'].search([('active', '=', True)], limit=1).id

    ftp_storage_id = fields.Many2one(
        'ftp.storage',
        string='SFTP Server',
        required=True,
        default=_default_ftp_storage_id
    )
    file_data = fields.Binary(
        string='File to Upload',
        required=True
    )
    file_name = fields.Char(
        string='Filename',
        required=True
    )
    form_name = fields.Char(
        string='Form Name',
        help='Name of the form calling this wizard',
        required=True
    )
    
    field_name = fields.Char(
        string='Field Name',
        help='Field that need to be updated',
        required=True
    )
    
    def action_upload_files(self):
        
        self.ensure_one()
        transport = None
        sftp = None
        try:
            # Validate server details
            if not self.ftp_storage_id.host:
                raise UserError(_("SFTP host is not configured"))
            if not self.ftp_storage_id.username:
                raise UserError(_("SFTP username is not configured"))

            # Connect to SFTP server
            transport = paramiko.Transport((self.ftp_storage_id.host, self.ftp_storage_id.port or 22))
            transport.banner_timeout = 60
            transport.connect(
                username=self.ftp_storage_id.username,
                password=self.ftp_storage_id.password
            )
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # Get SRF details
            if self.form_name == "lerm.civil.srf":
                srf_id = self.env.context.get("active_id")
                srf = self.env[self.form_name].sudo().browse(srf_id)
                
                if not srf.srf_id:
                    raise ValidationError("SRF not Confirmed")

                # Create directory structure if needed
                base_dir = f"/home/{self.ftp_storage_id.name}"
                srf_id = srf.srf_id.replace("/", "-")
                # remote_dir = f"{base_dir}/{srf.srf_id}"
                remote_dir = f"{base_dir}/{srf_id}"
                
                try:
                    sftp.stat(base_dir)
                except FileNotFoundError:
                    sftp.mkdir(base_dir)
                    sftp.chmod(base_dir, 0o755)  # Set proper permissions
                
                try:
                    sftp.stat(remote_dir)
                except FileNotFoundError:
                    sftp.mkdir(remote_dir)
                    sftp.chmod(remote_dir, 0o755)
                
                # Prepare file data
                if isinstance(self.file_data, str):
                    file_data = self.file_data.encode('utf-8')
                else:
                    file_data = base64.b64decode(self.file_data)
                
                # Upload file with proper handling
                file_name = self.file_name.replace(" ", "_")

                remote_path = f"{remote_dir}/{file_name}"
                with BytesIO(file_data) as file_obj:
                    sftp.putfo(file_obj, remote_path)
                    
                    
                field = self.field_name
                
                # Set file permissions (read/write for owner, read for others)
                sftp.chmod(remote_path, 0o644)
                srf.write({field: self.ftp_storage_id.name+"/"+srf_id+"/"+file_name })
                
                message = _("File %s uploaded successfully to %s") % (self.file_name, remote_path)
                
                return {
                    'type': 'ir.actions.act_window_close',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Upload Successful"),
                        'message': message,
                        'sticky': False,
                    }
                }
            
            if self.form_name == "lerm.srf.sample":
                

                sample_id = self.env.context.get("active_id")
                sample = self.env[self.form_name].sudo().browse(sample_id)
                base_dir = f"/home/{self.ftp_storage_id.name}"
                srf_id = sample.srf_id.srf_id.replace("/", "-")
                
                sample_id = sample.kes_no.replace("/", "-")
                remote_dir = f"{base_dir}/{srf_id}"
                sample_dir = f"{base_dir}/{srf_id}/{sample_id}"
                
                
                try:
                    sftp.stat(base_dir)
                except FileNotFoundError:
                    sftp.mkdir(base_dir)
                    sftp.chmod(base_dir, 0o755)  # Set proper permissions
                    
                try:
                    sftp.stat(remote_dir)
                except FileNotFoundError:
                    sftp.mkdir(remote_dir)
                    sftp.chmod(remote_dir, 0o755)
                    
                try:
                    sftp.stat(sample_dir)
                except FileNotFoundError:
                    sftp.mkdir(sample_dir)
                    sftp.chmod(sample_dir, 0o755)
                    
                # Prepare file data
                if isinstance(self.file_data, str):
                    file_data = self.file_data.encode('utf-8')
                else:
                    file_data = base64.b64decode(self.file_data)
                
                # Upload file with proper handling
                file_name = self.file_name.replace(" ", "_")

                remote_path = f"{sample_dir}/{file_name}"
                with BytesIO(file_data) as file_obj:
                    sftp.putfo(file_obj, remote_path)
                    
                
                self.ftp_storage_id.name+"/"+srf_id+"/"    
                    
                field = self.field_name
                
                upload_path = self.ftp_storage_id.name+"/"+srf_id+"/"+sample_id+"/"+file_name

                # Set file permissions (read/write for owner, read for others)
                sftp.chmod(remote_path, 0o644)
                sample.write({field: upload_path })
                
                message = _("File %s uploaded successfully to %s") % (self.file_name, remote_path)
                
                return {
                    'type': 'ir.actions.act_window_close',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Upload Successful"),
                        'message': message,
                        'sticky': False,
                    }
                }
            
            if self.form_name == "lerm.eln":
                eln_id = self.env.context.get("active_id")
                eln = self.env[self.form_name].sudo().browse(eln_id)
                base_dir = f"/home/{self.ftp_storage_id.name}"
                srf_id = eln.sample_id.srf_id.srf_id.replace("/", "-")
                eln_id = eln.eln_id
                
                sample_id = eln.sample_id.kes_no.replace("/", "-")
                remote_dir = f"{base_dir}/{srf_id}"
                sample_dir = f"{base_dir}/{srf_id}/{sample_id}"
                eln_dir = f"{base_dir}/{srf_id}/{sample_id}/{eln_id}"
                
                
                try:
                    sftp.stat(base_dir)
                except FileNotFoundError:
                    sftp.mkdir(base_dir)
                    sftp.chmod(base_dir, 0o755)  # Set proper permissions
                
                try:
                    sftp.stat(remote_dir)
                except FileNotFoundError:
                    sftp.mkdir(remote_dir)
                    sftp.chmod(remote_dir, 0o755)
                
                try:
                    sftp.stat(sample_dir)
                except FileNotFoundError:
                    sftp.mkdir(sample_dir)
                    sftp.chmod(sample_dir, 0o755)
                    
                try:
                    sftp.stat(eln_dir)
                except FileNotFoundError:
                    sftp.mkdir(eln_dir)
                    sftp.chmod(eln_dir, 0o755)
                
                
                
                # Prepare file data
                if isinstance(self.file_data, str):
                    file_data = self.file_data.encode('utf-8')
                else:
                    file_data = base64.b64decode(self.file_data)
                    
                    
                file_name = self.file_name.replace(" ", "_")
                
                
                
                remote_path = f"{eln_dir}/{file_name}"
                with BytesIO(file_data) as file_obj:
                    sftp.putfo(file_obj, remote_path)
                
                field = self.field_name
                
                upload_path = self.ftp_storage_id.name+"/"+srf_id+"/"+sample_id+"/"+eln_id +"/"+file_name
                # import wdb; wdb.set_trace()
                
                sftp.chmod(remote_path, 0o644)
                eln.write({field: upload_path })
                
                message = _("File %s uploaded successfully to %s") % (self.file_name, remote_path)
                
                return {
                    'type': 'ir.actions.act_window_close',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Upload Successful"),
                        'message': message,
                        'sticky': False,
                    }
                }
                
                
      

                
        except paramiko.SSHException as e:
            logging.error("SSH Error: %s", str(e), exc_info=True)
            raise UserError(_("SSH Connection Error: %s") % str(e))
        except IOError as e:
            logging.error("IO Error: %s", str(e), exc_info=True)
            raise UserError(_("File Operation Error: %s") % str(e))
        except Exception as e:
            logging.error("Unexpected Error: %s", str(e), exc_info=True)
            raise UserError(_("Unexpected Error: %s") % str(e))
        finally:
            if sftp:
                sftp.close()
            if transport:
                transport.close()
                
