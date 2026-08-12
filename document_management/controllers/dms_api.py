# -*- coding: utf-8 -*-

import datetime
import json
import logging
import os
import re

import requests

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request

from odoo.addons.document_management.controllers.token import issue_token

_logger = logging.getLogger(__name__)

ALLOWED_FILE_OPS = ('upload', 'download', 'preview', 'thumbnail')


def _sanitize(name):
    name = str(name or '').strip().replace(' ', '_')
    name = re.sub(r'[^A-Za-z0-9._-]', '', name)
    return name or 'untitled'


def _get_fastapi_url(server_side=False):
    icp = request.env['ir.config_parameter'].sudo()
    if server_side:
        url = icp.get_param('document_management.fastapi_server_url', '')
        if not url:
            url = icp.get_param('document_management.fastapi_url', '')
    else:
        url = icp.get_param('document_management.fastapi_url', '')
    return url.rstrip('/') if url else ''


def _fastapi_request(method, path, token, timeout=120, **kwargs):
    url = _get_fastapi_url(server_side=True)
    if not url:
        raise UserError('FastAPI URL is not configured. Please set it in Settings.')
    headers = {'Authorization': 'Bearer %s' % token}
    headers.update(kwargs.pop('headers', {}) or {})
    resp = requests.request(method, url + path, headers=headers, timeout=timeout, **kwargs)
    if resp.status_code >= 400:
        raise UserError('Backend service error (%s): %s' % (resp.status_code, resp.text[:300]))
    if resp.content:
        try:
            return resp.json()
        except Exception:
            return resp.text
    return {}


def _folder_path(folder):
    if not folder:
        return ''
    return folder.get_folder_path()


def _effective_cache():
    return {}


class DmsDriveController(http.Controller):

    # ------------------------------------------------------------------
    # App bootstrap
    # ------------------------------------------------------------------
    @http.route('/dms/config', type='json', auth='user', methods=['POST'])
    def get_config(self):
        fastapi_url = _get_fastapi_url()
        server_url = _get_fastapi_url(server_side=True)
        storage_path = request.env['ir.config_parameter'].sudo().get_param(
            'document_management.storage_path', '')
        return {
            'fastapi_url': fastapi_url,
            'server_url': server_url,
            'storage_path': storage_path,
            'configured': bool(fastapi_url),
            'user_id': request.env.user.id,
            'is_manager': request.env.user.has_group('document_management.group_dms_manager'),
        }

    # ------------------------------------------------------------------
    # Drive contents
    # ------------------------------------------------------------------
    def _serialize_folder(self, folder, user, cache):
        return {
            'id': folder.id,
            'name': folder.name,
            'parentId': folder.parent_id.id or 'root',
            'ownerId': folder.user_id.id,
            'ownerName': folder.user_id.name or '',
            'visibility': folder.visibility,
            'access': folder._effective_access(user, cache),
            'departmentId': folder.department_id.id or False,
            'teamId': folder.team_id.id or False,
            'folderCount': folder.folder_count,
            'fileCount': folder.file_count,
            'itemCount': folder.item_count,
            'description': folder.description or '',
        }

    def _serialize_file(self, file, user, cache):
        return {
            'id': file.id,
            'name': file.name,
            'originalName': file.original_name or '',
            'folderId': file.folder_id.id or 'root',
            'ownerId': file.user_id.id,
            'ownerName': file.user_id.name or '',
            'visibility': file.visibility,
            'mimeType': file.mime_type or '',
            'kind': file.kind,
            'size': file.size or 0,
            'sizeDisplay': file.size_display,
            'sha256': file.sha256 or '',
            'storagePath': file.storage_path or '',
            'documentTypeId': file.document_type_id.id or False,
            'departmentId': file.department_id.id or False,
            'projectId': file.project_id.id or False,
            'customerId': file.customer_id.id or False,
            'vendorId': file.vendor_id.id or False,
            'employeeId': file.employee_id.id or False,
            'documentDate': file.document_date.isoformat() if file.document_date else False,
            'expiryDate': file.expiry_date.isoformat() if file.expiry_date else False,
            'status': file.status,
            'description': file.description or '',
            'tagIds': file.tag_ids.ids,
            'access': file._effective_access(user, cache),
            'starred': user.id in file.star_user_ids.ids,
            'versionCount': file.version_count,
            'dateUploaded': file.date_uploaded.isoformat() if file.date_uploaded else False,
            'lastAccessDate': file.last_access_date.isoformat() if file.last_access_date else False,
        }

    @http.route('/dms/get_drive_contents', type='json', auth='user', methods=['POST'])
    def get_drive_contents(self):
        user = request.env.user
        cache = _effective_cache()
        Folder = request.env['dms.folder']
        File = request.env['dms.file']

        folders = []
        for folder in Folder.search([], order='name'):
            access = folder._effective_access(user, cache)
            if access.get('read'):
                folders.append(self._serialize_folder(folder, user, cache))

        files = []
        for file in File.search([('active', '=', True)], order='name'):
            access = file._effective_access(user, cache)
            if access.get('read'):
                files.append(self._serialize_file(file, user, cache))

        return {'folders': folders, 'files': files}

    # ------------------------------------------------------------------
    # Master data
    # ------------------------------------------------------------------
    @http.route('/dms/meta/users', type='json', auth='user', methods=['POST'])
    def meta_users(self):
        return [{'id': u.id, 'name': u.name} for u in
                request.env['res.users'].sudo().search([('share', '=', False)], order='name')]

    @http.route('/dms/meta/partners', type='json', auth='user', methods=['POST'])
    def meta_partners(self, partner_type='customer'):
        Partner = request.env['res.partner'].sudo()
        if partner_type == 'vendor':
            partners = Partner.search([('supplier_rank', '>', 0)], order='name')
        else:
            partners = Partner.search([('customer_rank', '>', 0)], order='name')
        return [{'id': p.id, 'name': p.name} for p in partners]

    @http.route('/dms/meta/employees', type='json', auth='user', methods=['POST'])
    def meta_employees(self):
        return [{'id': e.id, 'name': e.name} for e in
                request.env['hr.employee'].sudo().search([('active', '=', True)], order='name')]

    @http.route('/dms/meta/<string:collection>', type='json', auth='user', methods=['POST'])
    def meta_collection(self, collection):
        mapping = {
            'tags': ('dms.tag', 'name'),
            'document_types': ('dms.document.type', 'name'),
            'departments': ('dms.department', 'name'),
            'teams': ('dms.team', 'name'),
            'roles': ('dms.role', 'name'),
            'projects': ('dms.project', 'name'),
        }
        if collection not in mapping:
            return []
        model, field = mapping[collection]
        records = request.env[model].sudo().search([('active', '=', True)], order='name')
        return [{'id': r.id, 'name': r[field]} for r in records]

    @http.route('/dms/meta/custom_fields', type='json', auth='user', methods=['POST'])
    def meta_custom_fields(self):
        fields_def = request.env['dms.field.definition'].sudo().search(
            [('active', '=', True)], order='sequence, name')
        result = []
        for fd in fields_def:
            options = []
            if fd.field_type == 'selection' and fd.selection_options:
                options = [o.strip() for o in fd.selection_options.split(',') if o.strip()]
            result.append({
                'id': fd.id,
                'name': fd.name,
                'code': fd.code,
                'field_type': fd.field_type,
                'selection_options': options,
                'required': fd.required,
                'model': fd.model_id.model if fd.model_id else False,
            })
        return result

    # ------------------------------------------------------------------
    # Single file detail
    # ------------------------------------------------------------------
    @http.route('/dms/get_file/<int:file_id>', type='json', auth='user', methods=['POST'])
    def get_file(self, file_id):
        user = request.env.user
        file = request.env['dms.file'].browse(file_id)
        if not file.exists():
            raise UserError('Document not found.')
        if not file._effective_access(user).get('read'):
            raise AccessError('You do not have access to this document.')
        file.touch()

        custom_values = []
        for value in file.custom_value_ids:
            custom_values.append({
                'field_id': value.field_id.id,
                'code': value.field_id.code,
                'name': value.field_id.name,
                'field_type': value.field_id.field_type,
                'value': value.get_display_value(),
            })

        versions = [{
            'id': v.id,
            'version_no': v.version_no,
            'size': v.size,
            'sha256': v.sha256,
            'user_id': v.user_id.id,
            'user_name': v.user_id.name,
            'date': v.date.isoformat() if v.date else False,
            'note': v.note,
        } for v in file.version_ids]

        data = self._serialize_file(file, user, _effective_cache())
        data['customValues'] = custom_values
        data['versions'] = versions
        data['permissions'] = self._serialize_permissions(file.permissions)
        return data

    # ------------------------------------------------------------------
    # Tokens (for FastAPI file operations)
    # ------------------------------------------------------------------
    @http.route('/dms/get_token', type='json', auth='user', methods=['POST'])
    def get_token(self, file_id=None, folder_id=None, op='download'):
        user = request.env.user
        if op not in ALLOWED_FILE_OPS:
            raise UserError('Unsupported operation: %s' % op)

        if op == 'upload':
            folder = request.env['dms.folder'].browse(folder_id or 0)
            if folder:
                folder._check_permission('write')
                path = _folder_path(folder)
            else:
                path = ''
            return {
                'token': issue_token({
                    'uid': user.id, 'fid': 0, 'path': path, 'op': 'upload',
                }),
                'expires_in': 600,
            }

        file = request.env['dms.file'].browse(file_id or 0)
        if not file.exists():
            raise UserError('Document not found.')
        access = file._effective_access(user)
        if not access.get('read'):
            raise AccessError('You do not have access to this document.')
        if op == 'download' and not access.get('download'):
            raise AccessError('You do not have download permission for this document.')
        file.touch()
        request.env['dms.audit.trail'].log(
            op, model_name='dms.file', record_id=file.id, file_id=file.id,
            folder_id=file.folder_id.id)
        return {
            'token': issue_token({
                'uid': user.id, 'fid': file.id,
                'path': file.storage_path or '', 'op': op,
            }),
            'expires_in': 600,
        }

    # ------------------------------------------------------------------
    # Upload registration
    # ------------------------------------------------------------------
    @http.route('/dms/register_upload', type='json', auth='user', methods=['POST'])
    def register_upload(self, **data):
        name = data.get('name')
        if not name:
            raise UserError('A file name is required.')
        folder = request.env['dms.folder'].browse(data.get('folder_id') or 0)
        if folder:
            folder._check_permission('write')

        vals = {
            'name': name,
            'original_name': data.get('original_name') or name,
            'folder_id': folder.id or False,
            'mime_type': data.get('mime_type') or 'application/octet-stream',
            'size': data.get('size') or 0,
            'sha256': data.get('sha256') or '',
            'storage_path': data.get('storage_path') or '',
            'document_date': self._parse_date(data.get('document_date')),
            'expiry_date': self._parse_date(data.get('expiry_date')),
            'status': data.get('status') or 'draft',
            'description': data.get('description') or '',
            'tag_ids': [(6, 0, data.get('tag_ids') or [])],
        }
        self._apply_m2o(vals, ['document_type_id', 'department_id', 'project_id',
                               'customer_id', 'vendor_id', 'employee_id'])
        file = request.env['dms.file'].create(vals)
        self._save_custom_values(file, data.get('custom_values') or [])
        return {'id': file.id}

    @http.route('/dms/update_document/<int:file_id>', type='json', auth='user', methods=['POST'])
    def update_document(self, file_id, **data):
        file = request.env['dms.file'].browse(file_id)
        if not file.exists():
            raise UserError('Document not found.')
        file._check_permission('write')
        allowed = ['name', 'mime_type', 'document_type_id', 'department_id',
                   'project_id', 'customer_id', 'vendor_id', 'employee_id',
                   'document_date', 'expiry_date', 'status', 'description',
                   'visibility', 'tag_ids']
        vals = {}
        for key in allowed:
            if key not in data:
                continue
            if key in ('document_date', 'expiry_date'):
                vals[key] = self._parse_date(data[key])
            elif key == 'name':
                if data[key] and data[key] != file.name:
                    vals[key] = data[key]
            else:
                vals[key] = data[key]
        self._apply_m2o(vals, ['document_type_id', 'department_id', 'project_id',
                               'customer_id', 'vendor_id', 'employee_id'])
        if 'tag_ids' in vals:
            vals['tag_ids'] = [(6, 0, vals['tag_ids'] or [])]
        if vals:
            file.write(vals)
        self._save_custom_values(file, data.get('custom_values') or [])
        return {'id': file.id}

    # ------------------------------------------------------------------
    # Rename / Move / Delete (physical ops go through FastAPI)
    # ------------------------------------------------------------------
    @http.route('/dms/rename_file', type='json', auth='user', methods=['POST'])
    def rename_file(self, file_id, new_name):
        file = request.env['dms.file'].browse(file_id)
        if not file.exists():
            raise UserError('Document not found.')
        file._check_permission('write')
        new_name = _sanitize(new_name)
        if not new_name:
            raise UserError('A valid file name is required.')
        if not file.storage_path:
            file.name = new_name
            return {'id': file.id}
        old_path = file.storage_path
        new_path = os.path.join(os.path.dirname(old_path), new_name).replace('\\', '/')
        if old_path == new_path:
            file.name = new_name
            return {'id': file.id}
        token = issue_token({'uid': request.env.uid, 'fid': file.id,
                             'path': old_path, 'op': 'move'})
        _fastapi_request('POST', '/api/v1/files/move', token, json={'new_path': new_path})
        file.write({'name': new_name, 'storage_path': new_path})
        return {'id': file.id}

    @http.route('/dms/move_file', type='json', auth='user', methods=['POST'])
    def move_file(self, file_id, folder_id):
        file = request.env['dms.file'].browse(file_id)
        folder = request.env['dms.folder'].browse(folder_id or 0)
        if not file.exists():
            raise UserError('Document not found.')
        if folder and not folder.exists():
            raise UserError('Target folder not found.')
        file._check_permission('write')
        if folder:
            folder._check_permission('write')
        if file.folder_id == folder:
            return {'id': file.id}
        old_path = file.storage_path or ''
        new_path = os.path.join(_folder_path(folder), file.name).replace('\\', '/') if file.storage_path else ''
        if old_path and old_path != new_path:
            token = issue_token({'uid': request.env.uid, 'fid': file.id,
                                 'path': old_path, 'op': 'move'})
            _fastapi_request('POST', '/api/v1/files/move', token, json={'new_path': new_path})
        file.write({'folder_id': folder.id or False, 'storage_path': new_path})
        return {'id': file.id}

    @http.route('/dms/delete_file', type='json', auth='user', methods=['POST'])
    def delete_file(self, file_id):
        file = request.env['dms.file'].browse(file_id)
        if not file.exists():
            return {'deleted': True}
        file._check_permission('delete')
        if file.storage_path:
            token = issue_token({'uid': request.env.uid, 'fid': file.id,
                                 'path': file.storage_path, 'op': 'delete'})
            try:
                _fastapi_request('DELETE', '/api/v1/files', token)
            except UserError as e:
                _logger.warning('Physical delete failed, skipping: %s', e)
        file.unlink()
        return {'deleted': True}

    @http.route('/dms/delete_folder', type='json', auth='user', methods=['POST'])
    def delete_folder(self, folder_id):
        folder = request.env['dms.folder'].browse(folder_id)
        if not folder.exists():
            return {'deleted': True}
        folder._check_permission('delete')
        descendants = folder.get_descendant_folders()
        files = request.env['dms.file'].search([('folder_id', 'child_of', folder.ids)])
        # Remove physical files first (permission enforced per file), then records.
        for file in files:
            file._check_permission('delete')
            if file.storage_path:
                token = issue_token({'uid': request.env.uid, 'fid': file.id,
                                     'path': file.storage_path, 'op': 'delete'})
                try:
                    _fastapi_request('DELETE', '/api/v1/files', token)
                except UserError as e:
                    _logger.warning('Physical delete failed, skipping: %s', e)
        files.unlink()
        folder.unlink()
        return {'deleted': True}

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------
    def _serialize_permissions(self, permissions):
        result = []
        for p in permissions:
            result.append({
                'id': p.id,
                'user_id': p.user_id.id or False,
                'user_name': p.user_id.name if p.user_id else False,
                'role_id': p.role_id.id or False,
                'role_name': p.role_id.name if p.role_id else False,
                'team_id': p.team_id.id or False,
                'team_name': p.team_id.name if p.team_id else False,
                'department_id': p.department_id.id or False,
                'department_name': p.department_id.name if p.department_id else False,
                'can_read': p.can_read,
                'can_write': p.can_write,
                'can_download': p.can_download,
                'can_delete': p.can_delete,
                'can_manage': p.can_manage,
            })
        return result

    @http.route('/dms/get_folder_permissions/<int:folder_id>', type='json', auth='user', methods=['POST'])
    def get_folder_permissions(self, folder_id):
        folder = request.env['dms.folder'].browse(folder_id)
        if not folder.exists():
            raise UserError('Folder not found.')
        return {
            'owner': {'id': folder.user_id.id, 'name': folder.user_id.name},
            'permissions': self._serialize_permissions(folder.permissions),
        }

    @http.route('/dms/save_folder_permissions', type='json', auth='user', methods=['POST'])
    def save_folder_permissions(self, folder_id, grants):
        folder = request.env['dms.folder'].browse(folder_id)
        if not folder.exists():
            raise UserError('Folder not found.')
        folder._check_permission('manage')
        folder.permissions.unlink()
        created = 0
        for g in grants or []:
            uid = self._m2o(g.get('user_id'))
            rid = self._m2o(g.get('role_id'))
            tid = self._m2o(g.get('team_id'))
            did = self._m2o(g.get('department_id'))
            if not (uid or rid or tid or did):
                continue
            request.env['dms.folder.permission'].create({
                'folder_id': folder.id,
                'user_id': uid,
                'role_id': rid,
                'team_id': tid,
                'department_id': did,
                'can_read': g.get('can_read', True),
                'can_write': g.get('can_write', False),
                'can_download': g.get('can_download', False),
                'can_delete': g.get('can_delete', False),
                'can_manage': g.get('can_manage', False),
            })
            created += 1
        request.env['dms.audit.trail'].log(
            'permission_change', model_name='dms.folder', record_id=folder.id,
            folder_id=folder.id, details={'count': created})
        return True

    @http.route('/dms/get_file_permissions/<int:file_id>', type='json', auth='user', methods=['POST'])
    def get_file_permissions(self, file_id):
        file = request.env['dms.file'].browse(file_id)
        if not file.exists():
            raise UserError('Document not found.')
        return {
            'owner': {'id': file.user_id.id, 'name': file.user_id.name},
            'permissions': self._serialize_permissions(file.permissions),
        }

    @http.route('/dms/save_file_permissions', type='json', auth='user', methods=['POST'])
    def save_file_permissions(self, file_id, grants):
        file = request.env['dms.file'].browse(file_id)
        if not file.exists():
            raise UserError('Document not found.')
        file._check_permission('manage')
        file.permissions.unlink()
        created = 0
        for g in grants or []:
            uid = self._m2o(g.get('user_id'))
            rid = self._m2o(g.get('role_id'))
            tid = self._m2o(g.get('team_id'))
            did = self._m2o(g.get('department_id'))
            if not (uid or rid or tid or did):
                continue
            request.env['dms.file.permission'].create({
                'file_id': file.id,
                'user_id': uid,
                'role_id': rid,
                'team_id': tid,
                'department_id': did,
                'can_read': g.get('can_read', True),
                'can_write': g.get('can_write', False),
                'can_download': g.get('can_download', False),
                'can_delete': g.get('can_delete', False),
                'can_manage': g.get('can_manage', False),
            })
            created += 1
        request.env['dms.audit.trail'].log(
            'permission_change', model_name='dms.file', record_id=file.id,
            file_id=file.id, folder_id=file.folder_id.id, details={'count': created})
        return True

    @http.route('/dms/toggle_star', type='json', auth='user', methods=['POST'])
    def toggle_star(self, file_id):
        file = request.env['dms.file'].browse(file_id)
        if file.exists():
            file.toggle_star()
        return True

    @http.route('/dms/audit/<string:model>/<int:record_id>', type='json', auth='user', methods=['POST'])
    def get_audit(self, model, record_id):
        user = request.env.user
        if not user.has_group('document_management.group_dms_auditor') and \
           not user.has_group('document_management.group_dms_manager'):
            raise AccessError('You are not allowed to view the audit trail.')
        domain = [('model_name', '=', model), ('record_id', '=', record_id)]
        entries = request.env['dms.audit.trail'].sudo().search(
            domain, order='date desc', limit=200)
        return [{
            'id': e.id,
            'date': e.date.isoformat() if e.date else False,
            'user_name': e.user_name or '',
            'login': e.login or '',
            'action': e.action,
            'ip_address': e.ip_address or '',
            'session_id': e.session_id or '',
            'details': e.details or '',
        } for e in entries]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _parse_date(self, value):
        if not value:
            return False
        if isinstance(value, str):
            try:
                return datetime.date.fromisoformat(value[:10])
            except ValueError:
                return False
        return value or False

    def _m2o(self, value):
        """Robust many2one id casting (UI sends strings, '0'/''/False for empty)."""
        if not value:
            return False
        try:
            return int(value) or False
        except (TypeError, ValueError):
            return False

    def _apply_m2o(self, vals, keys):
        for key in keys:
            if key in vals:
                vals[key] = self._m2o(vals[key])
        return vals

    def _save_custom_values(self, file, custom_values):
        existing = {v.field_id.id: v for v in file.custom_value_ids}
        for item in custom_values or []:
            field_id = item.get('field_id')
            value = item.get('value')
            field = request.env['dms.field.definition'].browse(field_id)
            if not field.exists():
                continue
            vals = self._custom_value_vals(field, value)
            if not vals and not field.required:
                if field_id in existing:
                    existing[field_id].unlink()
                    del existing[field_id]
                continue
            if field_id in existing:
                existing[field_id].write(vals)
            else:
                request.env['dms.file.custom.value'].create(
                    dict({'file_id': file.id, 'field_id': field_id}, **vals))

    def _custom_value_vals(self, field, value):
        field_type = field.field_type
        if field_type == 'boolean':
            return {'value_boolean': bool(value)}
        if value in (None, '', False):
            return {}
        if field_type == 'char':
            return {'value_char': str(value)}
        if field_type == 'text':
            return {'value_text': str(value)}
        if field_type == 'integer':
            try:
                return {'value_integer': int(value)}
            except (ValueError, TypeError):
                return {}
        if field_type == 'float':
            try:
                return {'value_float': float(value)}
            except (ValueError, TypeError):
                return {}
        if field_type == 'date':
            return {'value_date': self._parse_date(value)}
        if field_type == 'datetime':
            return {'value_datetime': value}
        if field_type == 'boolean':
            return {'value_boolean': bool(value)}
        if field_type == 'selection':
            return {'value_char': str(value)}
        if field_type == 'many2one':
            try:
                return {'value_many2one': int(value)}
            except (ValueError, TypeError):
                return {}
        return {}
