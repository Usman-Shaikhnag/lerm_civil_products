from odoo import models, fields, api
from odoo.exceptions import AccessError

class DocumentFolderPermission(models.Model):
    _name = "document.folder.permission"
    _description = "Folder User Permissions"
    _rec_name = "user_id"

    folder_id = fields.Many2one("document.folder", required=True, ondelete="cascade")
    user_id = fields.Many2one("res.users", required=True)
    # can_edit = fields.Boolean("Can Edit", default=False)

    _sql_constraints = [
        ('folder_user_unique', 'unique(folder_id, user_id)',
         'User already has permissions for this folder.')
    ]
    access_level = fields.Selection([
        ('view', "View Only"),
        ('edit', "Edit"),
        ('full', "Full Control (Delete/Rename)")
    ], default="view")



class DocumentPermissionMixin(models.AbstractModel):
    _name = "document.permission.mixin"
    _description = "Permission Rules for Document Items"

    def _check_permission(self, level):
        """
        level = "view" | "edit" | "full"
        """
        user = self.env.user

        for record in self:
            # Owners always have full access
            if record.user_id.id == user.id:
                continue

            perm = record.permissions.filtered(lambda p: p.user_id.id == user.id)
            if not perm:
                raise AccessError("You do not have permission to view this folder.")

            if level == "edit" and perm.access_level not in ("edit", "full"):
                raise AccessError("You do not have edit permission for this folder.")

            if level == "full" and perm.access_level != "full":
                raise AccessError("You need full control to perform this action.")



class DocumentFilePermission(models.Model):
    _name = "document.file.permission"
    _description = "Access Permissions for Files"
    _inherit = ["document.permission.mixin"]

    file_id = fields.Many2one('document.file', ondelete='cascade', required=True)
    user_id = fields.Many2one('res.users', required=True)
    access_level = fields.Selection([
        ('view', 'View Only'),
        ('edit', 'Can Edit'),
        ('full', 'Full Access'),
    ], default='view', required=True)