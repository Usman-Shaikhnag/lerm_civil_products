# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

ACCESS_FLAGS = ('read', 'write', 'download', 'delete', 'manage')


class DmsGrantMixin(models.AbstractModel):
    _name = 'dms.grant.mixin'
    _description = 'DMS Grant (principal + access flags)'

    user_id = fields.Many2one('res.users', string='User', ondelete='cascade')
    role_id = fields.Many2one('dms.role', string='Role', ondelete='cascade')
    team_id = fields.Many2one('dms.team', string='Team', ondelete='cascade')
    department_id = fields.Many2one('dms.department', string='Department', ondelete='cascade')
    can_read = fields.Boolean(string='Read', default=True)
    can_write = fields.Boolean(string='Write')
    can_download = fields.Boolean(string='Download')
    can_delete = fields.Boolean(string='Delete')
    can_manage = fields.Boolean(string='Manage')

    @api.constrains('user_id', 'role_id', 'team_id', 'department_id')
    def _check_principal(self):
        for rec in self:
            principals = (rec.user_id, rec.role_id, rec.team_id, rec.department_id)
            if not any(principals):
                raise ValidationError(
                    'A permission must target at least one user, role, team or department.')

    @api.constrains('can_read', 'can_write', 'can_download', 'can_delete')
    def _check_read_always(self):
        for rec in self:
            if not (rec.can_read or rec.can_write or rec.can_download or rec.can_delete):
                raise ValidationError('A permission grant needs at least one access flag.')

    def matches(self, user):
        self.ensure_one()
        if self.user_id and self.user_id.id == user.id:
            return True
        if self.role_id and user.id in self.role_id.user_ids.ids:
            return True
        if self.team_id and user.id in self.team_id.member_ids.ids:
            return True
        if self.department_id and user.id in self.department_id.user_ids.ids:
            return True
        return False


class DmsFolderPermission(models.Model):
    _name = 'dms.folder.permission'
    _description = 'DMS Folder Permission'
    _inherit = ['dms.grant.mixin']

    folder_id = fields.Many2one('dms.folder', string='Folder', required=True,
                                ondelete='cascade', index=True)

    _sql_constraints = [
        ('folder_grant_unique',
         'unique(folder_id, user_id, role_id, team_id, department_id)',
         'This permission already exists for the folder.'),
    ]


class DmsFilePermission(models.Model):
    _name = 'dms.file.permission'
    _description = 'DMS Document Permission'
    _inherit = ['dms.grant.mixin']

    file_id = fields.Many2one('dms.file', string='Document', required=True,
                              ondelete='cascade', index=True)

    _sql_constraints = [
        ('file_grant_unique',
         'unique(file_id, user_id, role_id, team_id, department_id)',
         'This permission already exists for the document.'),
    ]


class DmsPermissionMixin(models.AbstractModel):
    _name = 'dms.permission.mixin'
    _description = 'DMS Permission Resolution'

    user_id = fields.Many2one('res.users', string='Owner',
                              default=lambda self: self.env.user, required=True, index=True)
    visibility = fields.Selection([
        ('private', 'Private'),
        ('public', 'Public'),
    ], string='Visibility', default='private', required=True)

    # Implemented on the concrete models (dms.folder / dms.file):
    # permissions = fields.One2many(...)

    def _permission_chain(self):
        """Records to walk when resolving permissions (self + ancestors)."""
        return [self]

    def _matches_user(self, user):
        return self.user_id.id == user.id

    def _compute_node_access(self, user):
        """Access flags contributed by this record's own grants."""
        res = {flag: False for flag in ACCESS_FLAGS}
        for grant in self.permissions:
            if grant.matches(user):
                for flag in ACCESS_FLAGS:
                    if getattr(grant, 'can_%s' % flag):
                        res[flag] = True
                res['read'] = True
        if self.visibility == 'public':
            res['read'] = True
            res['download'] = True
        return res

    def _effective_access(self, user=None, cache=None):
        """
        Return dict of effective access flags for `user` on this record.
        Owners always get full access. Permissions are inherited from ancestors
        and public documents grant read + download to every authenticated user.
        """
        user = user or self.env.user
        cache = cache if cache is not None else {}
        res = {flag: False for flag in ACCESS_FLAGS}
        if self._matches_user(user):
            return {flag: True for flag in ACCESS_FLAGS}
        for node in self._permission_chain():
            if node.id in cache:
                node_access = cache[node.id]
            else:
                node_access = node._compute_node_access(user)
                cache[node.id] = node_access
            for flag in ACCESS_FLAGS:
                res[flag] = res[flag] or node_access[flag]
        return res

    def _merge_access(self, target, other):
        for flag in ACCESS_FLAGS:
            target[flag] = target[flag] or bool(other.get(flag))

    def get_access_flags(self, user=None):
        return self._effective_access(user)

    def _check_permission(self, perm, user=None):
        user = user or self.env.user
        if perm not in ACCESS_FLAGS:
            raise ValueError('Unknown permission level: %s' % perm)
        if self.env.su or user.has_group('document_management.group_dms_manager'):
            return True
        self.ensure_one()
        access = self._effective_access(user)
        if not access.get(perm):
            raise AccessError(
                'You do not have "%s" permission on this document.' % perm)
        return True
