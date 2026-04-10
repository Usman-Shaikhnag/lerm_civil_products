from odoo import models, fields, api
from odoo.exceptions import UserError
import paramiko
import re

def sanitize(name):
    """Replace spaces with underscores and remove unsafe characters."""
    name = name.strip().replace(" ", "_")
    name = re.sub(r"[^A-Za-z0-9._-]", "", name)
    return name

class DocumentFolder(models.Model):
    _name = 'document.folder'
    _description = 'Document Drive Folder Structure'
    _inherit = ["document.permission.mixin"]
    _parent_store = True  # For hierarchical structure

    # --- Structure Fields ---
    name = fields.Char(string='Folder Name', required=True)
    parent_id = fields.Many2one(
        'document.folder', 
        string='Parent Folder', 
        ondelete='cascade'
    )
    child_ids = fields.One2many(
        'document.folder', 
        'parent_id', 
        string='Child Folders'
    )
    parent_path = fields.Char(index=True) # Used by _parent_store

    # --- Item Count Fields ---
    # Files are linked via document.file's folder_id field
    file_ids = fields.One2many(
        'document.file', 
        'folder_id', 
        string='Documents in Folder'
    )
    
    # Compute the counts
    item_count = fields.Integer(
        string='Item Count', 
        compute='_compute_item_count', 
        store=True
    )
    folder_count = fields.Integer(compute='_compute_item_count', store=True)
    file_count = fields.Integer(compute='_compute_item_count', store=True)
    permissions = fields.One2many(
            "document.folder.permission",
            "folder_id",
            string="User Permissions"
        )
    
    
    @api.depends('child_ids', 'file_ids')
    def _compute_item_count(self):
        """Calculates the number of immediate sub-folders and files."""
        for folder in self:
            folder.folder_count = len(folder.child_ids)
            folder.file_count = len(folder.file_ids)
            folder.item_count = folder.folder_count + folder.file_count

    # --- Metadata ---
    user_id = fields.Many2one(
        'res.users', 
        string='Owner', 
        default=lambda self: self.env.user, 
        required=True
    )

    @api.model
    def create(self, vals):
        if not vals.get('user_id'):
            vals['user_id'] = self.env.user.id
        return super(DocumentFolder, self).create(vals)
    
    # document_folder.py (add at bottom)

    def get_sftp_folder_path(self):
        """Return folder hierarchy name path, sanitized exactly like document_file.py."""
        parts = []
        folder = self
        while folder:
            parts.insert(0, sanitize(folder.name))
            folder = folder.parent_id
        return "/".join(parts)  # e.g. "Projects/Reports"

    def write(self, vals):
        self._check_permission("edit")
        
        storage = self.env["ftp.storage"].sudo().search([('active', '=', True)], limit=1)
<<<<<<< HEAD
        old_paths = {}
        if 'name' in vals and storage:
            for folder in self:
                old_paths[folder.id] = f"/home/{storage.name}/Document/{folder.get_sftp_folder_path()}"
                
        res = super().write(vals)
        
        if 'name' in vals and storage:
            # Recompute new physical paths and rename on SFTP
=======
        
        sftp = None
        transport = None
        if 'name' in vals and storage:
>>>>>>> 5ad20fd5238828436f69896b2d852822c3723efe
            try:
                transport = paramiko.Transport((storage.host, storage.port or 22))
                transport.connect(username=storage.username, password=storage.password)
                sftp = paramiko.SFTPClient.from_transport(transport)
<<<<<<< HEAD
                
                for folder in self:
                    new_path = f"/home/{storage.name}/Document/{folder.get_sftp_folder_path()}"
                    old_path = old_paths.get(folder.id)
                    if old_path and old_path != new_path:
                        try:
                            sftp.rename(old_path, new_path)
                        except Exception:
                            pass  # Directory might not exist yet
=======
            except Exception:
                pass
                
        old_paths = {}
        if 'name' in vals and storage and sftp:
            for folder in self:
                ext_url = f"{storage.name}/Document/{folder.get_sftp_folder_path()}"
                old_paths[folder.id] = self.env['document.file']._get_sftp_remote_path(sftp, storage.name, ext_url)
                
        res = super().write(vals)
        
        if 'name' in vals and storage and sftp:
            # Recompute new physical paths and rename on SFTP
            for folder in self:
                ext_url = f"{storage.name}/Document/{folder.get_sftp_folder_path()}"
                new_path = self.env['document.file']._get_sftp_remote_path(sftp, storage.name, ext_url)
                old_path = old_paths.get(folder.id)
                if old_path and old_path != new_path:
                    try:
                        sftp.rename(old_path, new_path)
                    except Exception:
                        pass  # Directory might not exist yet
            try:
>>>>>>> 5ad20fd5238828436f69896b2d852822c3723efe
                sftp.close()
                transport.close()
            except Exception:
                pass
            
            # Update external URLs for all child files so sync_with_sftp doesn't delete them
            all_files = self.env['document.file'].sudo().search([('folder_id', 'child_of', self.ids)])
            for f in all_files:
                folder_path_parts = ["Document"]
                curr = f.folder_id
                while curr:
                    folder_path_parts.insert(1, sanitize(curr.name))
                    curr = curr.parent_id
                
                clean_filename = f.name
                relative_path = f"{storage.name}/" + "/".join(folder_path_parts + [clean_filename])
                f.write({'external_url': relative_path})

        return res

    def unlink(self):
        self._check_permission("full")
        storage = self.env["ftp.storage"].sudo().search([('active', '=', True)], limit=1)
        
        try:
            transport = paramiko.Transport((storage.host, storage.port or 22))
            transport.connect(username=storage.username, password=storage.password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except Exception:
            sftp = None

        for folder in self:
            # First, trigger unlink on all nested files so they get removed from SFTP
            if folder.file_ids:
                folder.file_ids.unlink()
            
            # Then, trigger unlink on sub-folders recursively
            if folder.child_ids:
                folder.child_ids.unlink()
                
            # Finally, remove the physical folder from SFTP
            if sftp:
                folder_path = folder.get_sftp_folder_path()
                if folder_path:  # Do not delete root Document
<<<<<<< HEAD
                    remote_path = f"/home/{storage.name}/Document/{folder_path}"
=======
                    ext_url = f"{storage.name}/Document/{folder_path}"
                    remote_path = self.env['document.file']._get_sftp_remote_path(sftp, storage.name, ext_url)
>>>>>>> 5ad20fd5238828436f69896b2d852822c3723efe
                    try:
                        sftp.rmdir(remote_path)
                    except Exception:
                        pass
        
        if sftp:
            sftp.close()
            transport.close()

        return super().unlink()