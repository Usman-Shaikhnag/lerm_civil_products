# controllers/drive_controller.py
from odoo import http
from odoo.http import request,Response
import requests
import json
import logging
import paramiko, base64
from io import BytesIO
from odoo.exceptions import UserError,AccessError

_logger = logging.getLogger(__name__)


def format_size(size_bytes):
    if size_bytes is None:
        return "0 KB"
    if size_bytes < 1024:
        return f"{size_bytes} Bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


class DriveController(http.Controller):

    @http.route('/my_drive/get_drive_contents', type='json', auth='user', methods=["POST"])
    def get_drive_contents(self, **kw):
        try:
            storage = request.env["ftp.storage"].sudo().search([('active','=',True)], limit=1)
            if not storage:
                return {'error': "No active FTP storage configuration"}

            Folder = request.env['document.folder'].sudo()
            File = request.env['document.file'].sudo()
            File.sync_with_sftp()

            # import wdb;wdb.set_trace()
            user = request.env.user
            allowed_folders = Folder.search([
                '|', '|',
                ('permissions.user_id', '=', user.id),
                ('user_id', '=', user.id),
                ('create_uid', '=', user.id),
            ])

            all_allowed_ids = set(allowed_folders.ids)
            checked_ids = set()

            while True:
                new_children = Folder.search([
                    ('parent_id', 'in', list(all_allowed_ids - checked_ids))
                ])
                checked_ids |= all_allowed_ids

                if not new_children:
                    break

                all_allowed_ids |= set(new_children.ids)

            allowed_folders = Folder.browse(list(all_allowed_ids))

            # import wdb;wdb.set_trace()
            allowed_files = File.search([
                '|', '|','|',
                ('permissions.user_id', '=', user.id),
                ('user_id', '=', user.id),
                ('create_uid', '=', user.id),
                ('folder_id', 'in', allowed_folders.ids),
                ])
            # import wdb;wdb.set_trace()
            folder_data = allowed_folders.read(['id', 'name', 'parent_id', 'user_id'])
            final_folders = []
            for f in folder_data:
                parent = f.get('parent_id')
                user_id_tuple = f.get('user_id')
                final_folders.append({
                    'id': str(f['id']),
                    'name': f.get('name') or "Unnamed Folder",
                    'parentId': str(parent[0]) if parent else "root",
                    'ownerId': user_id_tuple[0] if user_id_tuple else False,
                    'currentUserId': user.id,
                    'isFolder': True,
                })
            file_data = allowed_files.read(['id', 'name', 'type', 'size', 'folder_id', 'external_url', 'user_id'])
            final_files = []
            for f in file_data:
                folder_id = f.get('folder_id')
                folder_id_val = folder_id[0] if folder_id else None
                user_id_tuple = f.get('user_id')
                
                # Safely parse size to prevent float multiplication errors
                raw_size = f.get('size')
                calc_size = 0
                if raw_size is not None and raw_size is not False:
                    calc_size = int(float(raw_size) * 1024 * 1024)
                    
                raw_type = f.get('type')
                ext_url = f.get('external_url') or ""
                
                final_files.append({
                    'id': str(f['id']),
                    'name': f.get('name') or "Unnamed File",
                    'type': str(raw_type).split('/')[0] if raw_type else 'file',
                    'size': format_size(calc_size),
                    'parentId': str(folder_id_val) if folder_id_val else "root",
                    'downloadUrl': f"/web/binary/download_ftp?url=https://{storage.host}/files/{ext_url}",
                    'previewUrl': f"https://{storage.host}/files/{ext_url}",
                    'ownerId': user_id_tuple[0] if user_id_tuple else False,
                    'currentUserId': user.id,
                    'isFolder': False,
                })
            for f in final_folders:
                folder_rec = request.env['document.folder'].sudo().browse(int(f['id']))

                # Owner always has full control
                if folder_rec.user_id.id == request.env.uid:
                    f['access'] = "full"
                    continue

                # Check direct permission
                perm = folder_rec.permissions.filtered(lambda p: p.user_id.id == request.env.uid)
                if perm:
                    f['access'] = perm.access_level
                else:
                    f['access'] = "view"


            for f in final_files:
                file_rec = request.env['document.file'].sudo().browse(int(f['id']))
                folder = file_rec.folder_id

                # 1️⃣ Owner always has full
                if file_rec.user_id.id == request.env.uid:
                    f['access'] = "full"
                    continue

                # 2️⃣ Explicit file permission
                perm = file_rec.permissions.filtered(lambda p: p.user_id.id == request.env.uid)
                # import wdb;wdb.set_trace()
                if perm:
                    f['access'] = perm.access_level
                    continue

                # 3️⃣ Fallback to folder permission
                if folder:
                    folder_perm = folder.permissions.filtered(lambda p: p.user_id.id == request.env.uid)
                    if folder_perm:
                        f['access'] = folder_perm.access_level
                    elif folder.user_id.id == request.env.uid:
                        f['access'] = "full"
                    else:
                        continue
                else:
                    # 4️⃣ Root fallback
                    continue

                

            return {
                'folders': final_folders,
                'files': final_files,
            }

        except Exception as e:
            _logger.error(f"Drive load failed: {e}")
            return {'error': str(e)}



    # @http.route('/my_drive/upload_file', type='http', auth='user', methods=['POST'], csrf=False)
    # def upload_file(self, currentFolderId=None, **post):


    #     storage = request.env["ftp.storage"].sudo().search([('active','=',True)], limit=1)
    #     if not storage:
    #         return "No active FTP configuration found", 500

    #     uploaded = post.get('file')
    #     if not uploaded:
    #         return "No file provided", 400

    #     file_content = uploaded.read()
    #     file_name = uploaded.filename.replace(" ", "_")

    #     # Compute folder path on SFTP
    #     base_dir = f"/home/{storage.name}/Document"

    #     if currentFolderId and currentFolderId != "root":
    #         folder = request.env['document.folder'].sudo().browse(int(currentFolderId))
    #         folder_path = folder.get_sftp_folder_path()  # "Projects/Reports"
    #         remote_dir = f"{base_dir}/{folder_path}"
    #     else:
    #         folder_path = ""
    #         remote_dir = base_dir  # root upload

    #     # Connect SFTP
    #     transport = paramiko.Transport((storage.host, storage.port or 22))
    #     transport.connect(username=storage.username, password=storage.password)
    #     sftp = paramiko.SFTPClient.from_transport(transport)

    #     # Ensure directories exist
    #     for part in remote_dir.split("/"):
    #         if part:
    #             try:
    #                 sftp.stat(base_dir)
    #             except:
    #                 sftp.mkdir(base_dir)
    #             try:
    #                 sftp.stat(remote_dir)
    #             except:
    #                 sftp.mkdir(remote_dir)

    #     # Upload
    #     remote_path = f"{remote_dir}/{file_name}"
    #     sftp.putfo(BytesIO(file_content), remote_path)
    #     sftp.chmod(remote_path, 0o644)

    #     sftp.close()
    #     transport.close()

    #     # Save metadata in Odoo
    #     full_sftp_path = f"{storage.name}/Document/{folder_path}/{file_name}".strip("/")
    #     file_record = request.env['document.file'].sudo().create({
    #         'name': file_name,
    #         'type': uploaded.content_type,
    #         'size': len(file_content) / (1024*1024),
    #         'folder_id': int(currentFolderId) if currentFolderId and currentFolderId != "root" else False,
    #         'external_url': full_sftp_path,
    #     })
    #     request.env.cr.commit()

    #     return request.make_response(json.dumps({'status': 'success', 'file_id': file_record.id}),
    #                                 headers=[('Content-Type', 'application/json')])


    @http.route('/my_drive/preview', auth='user', type='http')
    def preview_file(self, url, **kw):
        """
        Stream file from SFTP link without forcing download.
        Supports PDF + Images preview.
        """
        try:
            # Fetch file from remote HTTP storage /files/<path>
            response = requests.get(url, stream=True)

            if response.status_code != 200:
                return request.not_found()

            # Detect content type (critical for preview)
            content_type = response.headers.get("Content-Type", "application/octet-stream")

            return request.make_response(
                response.content,
                headers=[("Content-Type", content_type)],  # ✅ No Content-Disposition
            )

        except Exception as e:
            return request.make_response(str(e), status=500)
        
    @http.route('/my_drive/get_users', type='json', auth='user')
    def get_users(self):
        users = request.env['res.users'].sudo().search([], order="name")
        return [{'id': u.id, 'name': u.name} for u in users]
    

    @http.route('/my_drive/get_folder_permissions', type='json', auth='user')
    def get_folder_permissions(self, folder_id):
        folder = request.env['document.folder'].browse(int(folder_id))
        users = request.env['res.users'].search([])

        return {
            'users': [
                {
                    'id': u.id,
                    'name': u.name,
                    'email': u.login,
                    'has_access': any(p.user_id.id == u.id for p in folder.permissions),
                    'can_edit': next((p.can_edit for p in folder.permissions if p.user_id.id == u.id), False),

                }
                for u in users
            ]
        }


    @http.route('/my_drive/get_available_users', type='json', auth='user')
    def get_available_users(self, folder_id):
        folder = request.env['document.folder'].sudo().browse(int(folder_id)).ensure_one()

        users = request.env['res.users'].sudo().search([], order="name")
        current_perms = folder.permissions  # Only permissions for THIS FOLDER

        # import wdb;wdb.set_trace()
        return {
            "users": [{"id": u.id, "name": u.name} for u in users],
            "permissions": [
                {
                    "user_id": p.user_id.id,
                    "name": p.user_id.name,
                    "access_level": p.access_level,
                }
                for p in current_perms
            ],
            "owner": {
                "user_id": folder.user_id.id,
                "name": folder.user_id.name,
            },
        }




    @http.route('/my_drive/save_folder_permissions', type='json', auth='user')
    def save_folder_permissions(self, folder_id, permissions):
        folder = request.env['document.folder'].sudo().browse(int(folder_id)).ensure_one()
        folder.permissions.unlink()

        # import wdb;wdb.set_trace();
        for p in permissions:
            request.env['document.folder.permission'].sudo().create({
                'folder_id': folder.id,
                'user_id': p['user_id'],
                'access_level': p['access_level'],
            })
        return True


    @http.route('/my_drive/get_file_permissions', type='json', auth='user')
    def get_file_permissions(self, file_id):
        file_rec = request.env['document.file'].sudo().browse(int(file_id)).ensure_one()
        users = request.env['res.users'].sudo().search([], order="name")
        # import wdb;wdb.set_trace()
        current_perms = file_rec.permissions
        return {
            "users": [{"id": u.id,"name": u.name}for u in users],
            "permissions": [
                {
                    "user_id": p.user_id.id,
                    "name": p.user_id.name,
                    "access_level": p.access_level,
                }
                for p in current_perms
            ],
            "owner": {
                "user_id": file_rec.user_id.id,
                "name": file_rec.user_id.name,
            },
        }


    @http.route('/my_drive/save_file_permissions', type='json', auth='user')
    def save_file_permissions(self, file_id, permissions):
        file_rec = request.env['document.file'].sudo().browse(int(file_id)).ensure_one()

        # import wdb;wdb.set_trace()
        # Only owner can manage permissions
        if file_rec.user_id.id != request.env.uid:
            raise AccessError("Only the file owner can modify permissions.")

        file_rec.permissions.unlink()
        for p in permissions:
            request.env['document.file.permission'].sudo().create({
                'file_id': file_rec.id,
                'user_id': p['user_id'],
                'access_level': p['access_level'],
            })

        return True

    @http.route('/api/products', auth='public', type='json', csrf=False, cors='*')
    def get_products(self, **kwargs):
        products = request.env['product.product'].sudo().search_read(
            [], ['name', 'list_price']
        )
        users = request.env['res.users'].sudo().search_read(
            [], ['name', 'login']
        )
        return {
            "products": products,
            "users": users,
        }
