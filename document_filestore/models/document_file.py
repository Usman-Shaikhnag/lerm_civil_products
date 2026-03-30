from odoo import models, fields, api
from odoo.exceptions import UserError,AccessError
import base64
import paramiko
import logging
import re
from io import BytesIO
_logger = logging.getLogger(__name__)

def sanitize(name):
    """
    Replace spaces with underscores and remove unsafe characters.
    """
    name = name.strip().replace(" ", "_")
    name = re.sub(r"[^A-Za-z0-9._-]", "", name)
    return name


class DriveFile(models.Model):
    _name = 'document.file'
    _inherit = ["document.permission.mixin"]
    _description = 'Document File'

    name = fields.Char(required=True)
    type = fields.Char(required=True)
    size = fields.Float(string='Size (MB)', readonly=True)
    external_url = fields.Char(string='SFTP Path', readonly=True)
    folder_id = fields.Many2one('document.folder', string='Folder', ondelete='cascade')
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, required=True)
    permissions = fields.One2many('document.file.permission', 'file_id', string='Permissions')

    @api.model
    def create_and_store_file(self, file_data, folder_id=False):
        """
        Upload file to SFTP under:
        /home/<ftp_storage.name>/Document/<folder1>/<folder2>/<file>
        """

        # 1) Get active storage
        storage = self.env["ftp.storage"].sudo().search([('active', '=', True)], limit=1)
        if not storage:
            raise UserError("No active FTP storage configured.")

        # 2) Decode file
        # import wdb;wdb.set_trace()

        try:
            file_binary = base64.b64decode(file_data["file_base64"])
        except:
            raise UserError("Invalid Base64 file data.")

        clean_filename = sanitize(file_data["name"])

        # 3) Build folder path by walking parents (using names)
        folder_path_parts = ["Document"]
        if folder_id:
            folder = self.env["document.folder"].browse(folder_id).sudo()
            while folder:
                folder_path_parts.insert(1, sanitize(folder.name))
                folder = folder.parent_id

        # Example → /home/Demo/Document/Projects/Reports
        remote_dir = f"/home/{storage.name}/" + "/".join(folder_path_parts)

        # Final file path
        remote_path = f"{remote_dir}/{clean_filename}"

        # 4) Connect & upload
        transport = paramiko.Transport((storage.host, storage.port or 22))
        transport.connect(username=storage.username, password=storage.password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        # Ensure directories exist
        try:
            sftp.stat(f"/home/{storage.name}")
        except FileNotFoundError:
            raise UserError(f"Base path /home/{storage.name} does not exist on server.")

        # Make intermediate directories
        path_accum = f"/home/{storage.name}"
        for part in folder_path_parts:
            path_accum += f"/{part}"
            try:
                sftp.stat(path_accum)
            except FileNotFoundError:
                sftp.mkdir(path_accum, mode=0o755)

        # Upload file
        try:
            with BytesIO(file_binary) as f:
                sftp.putfo(f, remote_path)
        except Exception as e:
            raise UserError(f"Failed to upload file to SFTP: {str(e)}")
            
        try:
            sftp.chmod(remote_path, 0o644)  # readable
        except Exception as e:
            _logger.warning(f"SFTP chmod failed (ignoring): {str(e)}")

        sftp.close()
        transport.close()

        # 5) Save metadata (storing *relative* path for easy download/preview)
        relative_path = f"{storage.name}/" + "/".join(folder_path_parts + [clean_filename])

        record = self.create({
            "name": clean_filename,
            "type": file_data["type"],
            "size": file_data["size"] / (1024 * 1024),
            "folder_id": folder_id,
            "external_url": relative_path,
        })
        return record.read()[0]


    def write(self, vals):
        storage = self.env["ftp.storage"].sudo().search([('active', '=', True)], limit=1)
        if not storage:
            return super().write(vals)

        for file in self:
            if file.folder_id:
                file.folder_id._check_permission("edit")

            # If name changes → rename on SFTP
            if 'name' in vals and file.external_url:
                new_name = sanitize(vals['name'])
                new_url = "/".join(file.external_url.split("/")[:-1] + [new_name])


                if file.external_url.startswith(storage.name):
                    old_path = f"/home/{file.external_url}"
                    new_path = f"/home/{new_url}"
                else:
                    old_path = f"/home/{storage.name}/{file.external_url}"
                    new_path = f"/home/{storage.name}/{new_url}"
                try:
                    transport = paramiko.Transport((storage.host, storage.port or 22))
                    transport.connect(username=storage.username, password=storage.password)
                    sftp = paramiko.SFTPClient.from_transport(transport)
                    sftp.rename(old_path, new_path)
                    sftp.close()
                    transport.close()
                except Exception as e:
                    raise UserError(f"SFTP rename failed: {str(e)}")

                vals['external_url'] = new_url

        return super().write(vals)


    def unlink(self):
        """
        Delete the file from the SFTP server when deleted in Odoo.
        Also enforce folder permissions.
        """
        storage = self.env["ftp.storage"].sudo().search([('active', '=', True)], limit=1)
        if not storage:
            raise UserError("No active FTP storage configured.")

        for file in self:
            # Permission Check (full control required)
            if file.folder_id:
                file.folder_id._check_permission("full")

            if file.external_url:
                if file.external_url.startswith(storage.name):
                    remote_path = f"/home/{file.external_url}"
                else:
                    remote_path = f"/home/{storage.name}/{file.external_url}"


                try:
                    # SFTP Connect
                    transport = paramiko.Transport((storage.host, storage.port or 22))
                    transport.connect(username=storage.username, password=storage.password)
                    sftp = paramiko.SFTPClient.from_transport(transport)

                    try:
                        sftp.remove(remote_path)
                        # _logger.info(f"SFTP: deleted {remote_path}")
                    except FileNotFoundError:
                        # _logger.warning(f"SFTP file not found (skipped delete): {remote_path}")
                        pass

                    sftp.close()
                    transport.close()
                except Exception as e:
                    raise UserError(f"Failed to delete file from SFTP: {str(e)}")

        return super().unlink()

    def sync_with_sftp(self):
        """Ensure DB file list matches actual SFTP files."""
        storage = self.env["ftp.storage"].sudo().search([('active', '=', True)], limit=1)
        if not storage:
            return

        transport = paramiko.Transport((storage.host, storage.port or 22))
        transport.connect(username=storage.username, password=storage.password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        all_files = self.sudo().search([])
        missing = []
        # import wdb;wdb.set_trace()
        for file in all_files:
            if file.external_url.startswith(storage.name):
                remote_path = f"/home/{file.external_url}"
            else:
                remote_path = f"/home/{storage.name}/{file.external_url}"
            try:
                sftp.stat(remote_path)
            except FileNotFoundError:
                missing.append(file.name)
                file.unlink()

        sftp.close()
        transport.close()
        if missing:
            _logger.warning(f"Removed metadata for {len(missing)} missing SFTP files: {missing}")

    def _check_permission(self, level):
        for record in self:
            folder = record.folder_id
            if folder:
                folder._check_permission(level)
            else:
                # root file: only owner can edit/delete
                if record.user_id.id != self.env.uid and level in ("edit", "full"):
                    raise AccessError("You do not have permission to modify this file.")

    def get_access_level(self):
        self.ensure_one()
        uid = self.env.uid

        # 1️⃣ Explicit file-level permission
        perm = self.permissions.filtered(lambda p: p.user_id.id == uid)
        if perm:
            return perm.access_level

        # 2️⃣ Fallback to folder permission
        if self.folder_id:
            return self.folder_id.get_access_level()

        # 3️⃣ Root fallback: only owner has full
        return "full" if self.user_id.id == uid else "view"
