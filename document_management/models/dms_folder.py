# -*- coding: utf-8 -*-

import re

from odoo import api, fields, models


def sanitize(name):
    """Replace spaces with underscores and remove unsafe characters."""
    name = str(name or '').strip().replace(' ', '_')
    name = re.sub(r'[^A-Za-z0-9._-]', '', name)
    return name or 'untitled'


class DmsFolder(models.Model):
    _name = 'dms.folder'
    _description = 'DMS Folder'
    _inherit = ['dms.permission.mixin']
    _parent_store = True
    _order = 'name'

    name = fields.Char(string='Folder Name', required=True)
    parent_id = fields.Many2one('dms.folder', string='Parent Folder', ondelete='cascade', index=True)
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('dms.folder', 'parent_id', string='Child Folders')
    file_ids = fields.One2many('dms.file', 'folder_id', string='Documents')
    permissions = fields.One2many('dms.folder.permission', 'folder_id', string='Permissions')
    department_id = fields.Many2one('dms.department', string='Department')
    team_id = fields.Many2one('dms.team', string='Team')
    description = fields.Text(string='Description')
    folder_count = fields.Integer(compute='_compute_counts', store=True)
    file_count = fields.Integer(compute='_compute_counts', store=True)
    item_count = fields.Integer(compute='_compute_counts', store=True)

    @api.depends('child_ids', 'file_ids')
    def _compute_counts(self):
        for folder in self:
            folder.folder_count = len(folder.child_ids)
            folder.file_count = len(folder.file_ids)
            folder.item_count = folder.folder_count + folder.file_count

    @api.model_create_multi
    def create(self, vals_list):
        folders = super().create(vals_list)
        for folder in folders:
            folder._log_audit('create', details={'name': folder.name})
        return folders

    def write(self, vals):
        for folder in self:
            folder._check_permission('write')
        if 'name' in vals and len(self) == 1:
            self._log_audit('rename', details={'old_name': self.name, 'new_name': vals.get('name')})
        if 'permissions' in vals:
            self._log_audit('permission_change')
        res = super().write(vals)
        if 'name' in vals:
            self._log_audit('update', details={'fields': sorted(vals.keys())})
        return res

    def unlink(self):
        for folder in self:
            folder._check_permission('delete')
        ids = self.ids
        res = super().unlink()
        for folder_id in ids:
            self.env['dms.audit.trail'].log(
                'delete', model_name='dms.folder', record_id=folder_id,
                details={'folder_id': folder_id})
        return res

    # ------------------------------------------------------------------
    # Permission helpers
    # ------------------------------------------------------------------
    def _permission_chain(self):
        chain = []
        node = self
        while node:
            chain.append(node)
            node = node.parent_id
        return chain

    def get_sftp_path_parts(self):
        parts = []
        node = self
        while node:
            parts.insert(0, sanitize(node.name))
            node = node.parent_id
        return parts

    def get_folder_path(self):
        """Sanitized hierarchy path relative to the storage root."""
        return '/'.join(self.get_sftp_path_parts())

    def get_descendant_folders(self):
        return self.search([('id', 'child_of', self.ids)])

    def _log_audit(self, action, details=None):
        self.env['dms.audit.trail'].log(
            action, model_name='dms.folder', record_id=self.id,
            folder_id=self.id, details=details or {})
