from odoo import models, fields, api

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
        """Return folder hierarchy name path, sanitized."""
        parts = []
        folder = self
        while folder:
            name = folder.name.replace(" ", "_")
            for ch in "/\\:*?\"<>|":
                name = name.replace(ch, "")
            parts.insert(0, name)
            folder = folder.parent_id
        return "/".join(parts)  # "Projects/Reports"
    def write(self, vals):
        self._check_permission("edit")
        return super().write(vals)

    def unlink(self):
        self._check_permission("full")
        return super().unlink()