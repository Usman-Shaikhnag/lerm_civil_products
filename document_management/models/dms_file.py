# -*- coding: utf-8 -*-

import os

from odoo import api, fields, models


class DmsFileVersion(models.Model):
    _name = 'dms.file.version'
    _description = 'DMS Document Version'
    _order = 'version_no desc, date desc'

    file_id = fields.Many2one('dms.file', string='Document', required=True,
                              ondelete='cascade', index=True)
    version_no = fields.Integer(string='Version', default=1)
    storage_path = fields.Char(string='Storage Path')
    sha256 = fields.Char(string='Checksum')
    size = fields.Integer(string='Size (bytes)')
    user_id = fields.Many2one('res.users', string='Uploaded By',
                              default=lambda self: self.env.user)
    date = fields.Datetime(string='Date', default=lambda self: fields.Datetime.now())
    note = fields.Char(string='Note')


class DmsFile(models.Model):
    _name = 'dms.file'
    _description = 'DMS Document'
    _inherit = ['dms.permission.mixin']
    _order = 'name'

    name = fields.Char(string='File Name', required=True)
    original_name = fields.Char(string='Original Name')
    folder_id = fields.Many2one('dms.folder', string='Folder', ondelete='set null',
                                index=True)
    permissions = fields.One2many('dms.file.permission', 'file_id', string='Permissions')

    mime_type = fields.Char(string='MIME Type')
    kind = fields.Selection([
        ('image', 'Image'),
        ('pdf', 'PDF'),
        ('word', 'Word'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('other', 'Other'),
    ], compute='_compute_kind', store=True)
    size = fields.Integer(string='Size (bytes)')
    size_display = fields.Char(string='Size', compute='_compute_size_display')
    sha256 = fields.Char(string='SHA-256 Checksum')
    storage_path = fields.Char(string='Storage Path',
                               help='Relative path of the file under the storage root.')
    date_uploaded = fields.Datetime(string='Uploaded On',
                                    default=lambda self: fields.Datetime.now())
    last_access_date = fields.Datetime(string='Last Access')

    # ---- Metadata / Tags ----
    document_type_id = fields.Many2one('dms.document.type', string='Document Type')
    department_id = fields.Many2one('dms.department', string='Department')
    project_id = fields.Many2one('dms.project', string='Project')
    customer_id = fields.Many2one('res.partner', string='Customer')
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    document_date = fields.Date(string='Document Date')
    expiry_date = fields.Date(string='Expiry Date')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('archived', 'Archived'),
    ], string='Status', default='draft')
    description = fields.Text(string='Description')
    tag_ids = fields.Many2many('dms.tag', string='Tags')
    custom_value_ids = fields.One2many('dms.file.custom.value', 'file_id',
                                       string='Custom Values')
    star_user_ids = fields.Many2many('res.users', string='Starred By')

    version_ids = fields.One2many('dms.file.version', 'file_id', string='Versions')
    version_count = fields.Integer(string='Version Count', compute='_compute_version_count')
    is_latest_version = fields.Boolean(string='Is Latest', default=True)

    active = fields.Boolean(default=True)
    locked_by = fields.Many2one('res.users', string='Locked By')

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------
    @api.depends('name', 'mime_type')
    def _compute_kind(self):
        for file in self:
            ext = os.path.splitext(file.name or '')[1].lower()
            mime = (file.mime_type or '').lower()
            if mime.startswith('image/') or ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp'):
                kind = 'image'
            elif mime == 'application/pdf' or ext == '.pdf':
                kind = 'pdf'
            elif mime in ('application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                          'application/msword') or ext in ('.docx', '.doc'):
                kind = 'word'
            elif mime in ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                          'application/vnd.ms-excel') or ext in ('.xlsx', '.xls'):
                kind = 'excel'
            elif mime in ('text/csv', 'text/comma-separated-values') or ext == '.csv':
                kind = 'csv'
            else:
                kind = 'other'
            file.kind = kind

    @api.depends('size')
    def _compute_size_display(self):
        for file in self:
            size = file.size or 0
            if size < 1024:
                file.size_display = '%d B' % size
            elif size < 1024 * 1024:
                file.size_display = '%.1f KB' % (size / 1024)
            else:
                file.size_display = '%.2f MB' % (size / (1024 * 1024))

    @api.depends('version_ids')
    def _compute_version_count(self):
        for file in self:
            file.version_count = len(file.version_ids)

    # ------------------------------------------------------------------
    # CRUD + audit
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        files = super().create(vals_list)
        for file in files:
            file._log_audit('upload', details={'folder_id': file.folder_id.id})
        return files

    def write(self, vals):
        for file in self:
            file._check_permission('write')
        if 'permissions' in vals:
            self._log_audit('permission_change')
        if 'folder_id' in vals and len(self) == 1:
            self._log_audit('move', details={'to_folder': vals.get('folder_id')})
        if 'name' in vals:
            self._log_audit('rename', details={'old_name': self.name,
                                               'new_name': vals.get('name')})
        res = super().write(vals)
        if vals.keys() - {'permissions', 'folder_id', 'name', 'last_access_date'}:
            self._log_audit('update', details={'fields': sorted(vals.keys())})
        return res

    def unlink(self):
        for file in self:
            file._check_permission('delete')
        ids = self.ids
        res = super().unlink()
        for file_id in ids:
            self.env['dms.audit.trail'].log(
                'delete', model_name='dms.file', record_id=file_id,
                details={'file_id': file_id})
        return res

    # ------------------------------------------------------------------
    # Permission helpers
    # ------------------------------------------------------------------
    def _permission_chain(self):
        chain = [self]
        node = self.folder_id
        while node:
            chain.append(node)
            node = node.parent_id
        return chain

    def touch(self):
        """Record that the file was read/downloaded/previewed.

        This is an internal tracking update, so it bypasses the write
        permission check (read/download-only users would otherwise fail).
        """
        self.sudo().write({'last_access_date': fields.Datetime.now()})

    def toggle_star(self):
        user = self.env.user
        for file in self:
            if user in file.star_user_ids:
                file.star_user_ids -= user
            else:
                file.star_user_ids += user

    def create_version_record(self, storage_path, size, sha256, note=False):
        """Archive the current physical file as a version record."""
        self.ensure_one()
        latest_no = max([v.version_no for v in self.version_ids] or [0])
        self.env['dms.file.version'].create({
            'file_id': self.id,
            'version_no': latest_no + 1,
            'storage_path': self.storage_path,
            'sha256': self.sha256,
            'size': self.size,
            'note': note,
        })
        self._log_audit('version', details={'version_no': latest_no + 1})
        return latest_no + 1

    def get_custom_values_map(self):
        result = {}
        for value in self.custom_value_ids:
            result[value.field_id.id] = value.get_display_value()
        return result

    def _log_audit(self, action, details=None):
        self.env['dms.audit.trail'].log(
            action, model_name='dms.file', record_id=self.id,
            file_id=self.id, folder_id=self.folder_id.id, details=details or {})
