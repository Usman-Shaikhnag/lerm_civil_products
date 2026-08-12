# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dms_storage_path = fields.Char(
        string='Storage Path',
        config_parameter='document_management.storage_path',
        default='/var/lib/dms_files',
        help='Absolute path on the server where documents are stored. '
             'The FastAPI service must have read/write access to this folder.')
    dms_fastapi_url = fields.Char(
        string='FastAPI Base URL',
        config_parameter='document_management.fastapi_url',
        default='http://localhost:8000',
        help='Base URL of the FastAPI document backend as seen from the '
             'browser (e.g. http://localhost:8000).')
    dms_fastapi_server_url = fields.Char(
        string='FastAPI Server URL',
        config_parameter='document_management.fastapi_server_url',
        help='Base URL of the FastAPI backend as seen from the Odoo server '
             'itself (e.g. http://host.docker.internal:8000 when Odoo runs in '
             'Docker). Leave empty to reuse the browser URL.')
    dms_fastapi_secret = fields.Char(
        string='Shared Secret',
        config_parameter='document_management.fastapi_secret',
        help='Shared secret used to sign tokens between Odoo and the FastAPI backend.')
    dms_enable_audit = fields.Boolean(
        string='Enable Audit Trail',
        config_parameter='document_management.enable_audit',
        default=True)
