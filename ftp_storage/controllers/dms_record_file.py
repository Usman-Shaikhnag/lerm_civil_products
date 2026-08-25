# -*- coding: utf-8 -*-

from werkzeug.utils import redirect

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request

from odoo.addons.document_management.controllers.token import issue_token

from odoo.addons.ftp_storage.models.dms_attachment import DMS_RECORD_MODELS, dms_secret


class DmsRecordFileController(http.Controller):

    @http.route('/dms/record_file/<string:model>/<int:record_id>/<string:record_field>/download',
                type='http', auth='user')
    def download(self, model, record_id, record_field):
        return self._serve(model, record_id, record_field, 'download')

    @http.route('/dms/record_file/<string:model>/<int:record_id>/<string:record_field>/preview',
                type='http', auth='user')
    def preview(self, model, record_id, record_field):
        return self._serve(model, record_id, record_field, 'preview')

    def _serve(self, model, record_id, record_field, op):
        if model not in DMS_RECORD_MODELS:
            raise UserError('Unknown record model: %s' % model)

        record = request.env[model].browse(record_id)
        if not record.exists():
            raise UserError('Record not found.')
        # Enforce the record's own read access (ACL + record rules).
        record.check_access_rights('read')
        record.check_access_rule('read')

        dms_file = request.env['dms.file'].sudo().search([
            ('res_model', '=', model),
            ('res_id', '=', record_id),
            ('record_field', '=', record_field),
        ], order='id desc', limit=1)
        if not dms_file:
            raise UserError('No file has been uploaded for this record yet.')

        url = (request.env['ir.config_parameter'].sudo().get_param(
            'document_management.fastapi_url') or '').rstrip('/')
        if not url:
            raise UserError('The DMS FastAPI backend is not configured.')

        token = issue_token({'uid': request.env.uid, 'fid': dms_file.id,
                             'path': dms_file.storage_path or '', 'op': op},
                            secret=dms_secret(request.env))
        endpoint = '/api/v1/files/content' if op == 'download' else '/api/v1/files/preview'
        return redirect(url + endpoint + '?token=' + token)
