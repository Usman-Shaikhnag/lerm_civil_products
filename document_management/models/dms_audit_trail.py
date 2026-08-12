# -*- coding: utf-8 -*-

import json

from odoo import api, fields, models
from odoo import http


class DmsAuditTrail(models.Model):
    _name = 'dms.audit.trail'
    _description = 'DMS Audit Trail'
    _order = 'date desc, id desc'

    date = fields.Datetime(string='Date', default=lambda self: fields.Datetime.now(),
                           required=True, index=True)
    user_id = fields.Many2one('res.users', string='User', required=True, index=True)
    user_name = fields.Char(string='User Name', compute='_compute_user_name', store=True)
    login = fields.Char(string='Login', readonly=True)
    action = fields.Selection([
        ('create', 'Create'),
        ('upload', 'Upload'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('rename', 'Rename'),
        ('move', 'Move'),
        ('download', 'Download'),
        ('preview', 'Preview'),
        ('delete', 'Delete'),
        ('permission_change', 'Permission Change'),
        ('version', 'New Version'),
        ('login_success', 'Login Success'),
        ('login_fail', 'Login Failed'),
        ('logout', 'Logout'),
    ], string='Action', required=True, index=True)
    model_name = fields.Char(string='Model')
    record_id = fields.Integer(string='Record ID')
    file_id = fields.Many2one('dms.file', string='Document', ondelete='set null', index=True)
    folder_id = fields.Many2one('dms.folder', string='Folder', ondelete='set null', index=True)
    ip_address = fields.Char(string='IP Address')
    session_id = fields.Char(string='Session')
    details = fields.Text(string='Details')
    old_value = fields.Text(string='Old Value')
    new_value = fields.Text(string='New Value')

    @api.depends('user_id')
    def _compute_user_name(self):
        for rec in self:
            rec.user_name = rec.user_id.name if rec.user_id else False

    @api.model
    def log(self, action, model_name=False, record_id=False,
            file_id=False, folder_id=False, details=None, old_value=None,
            new_value=None, user=None, ip=False, session=False, login=False):
        """Write an audit entry. Respects the global audit toggle."""
        icp = self.env['ir.config_parameter'].sudo()
        if icp.get_param('document_management.enable_audit', 'True') != 'True':
            return self
        if not ip:
            try:
                ip = http.request.httprequest.remote_addr if http.request else False
            except Exception:
                ip = False
        if not session:
            try:
                session = http.request.session.sid if http.request else False
            except Exception:
                session = False
        if isinstance(details, (dict, list)):
            details = json.dumps(details, default=str)
        try:
            self.sudo().create({
                'action': action,
                'model_name': model_name or False,
                'record_id': record_id or False,
                'file_id': file_id or False,
                'folder_id': folder_id or False,
                'details': details or False,
                'old_value': old_value or False,
                'new_value': new_value or False,
                'user_id': (user or self.env.user).id,
                'login': login or False,
                'ip_address': ip or False,
                'session_id': session or False,
            })
        except Exception:
            # Never let audit failure break the business flow.
            pass
        return self
