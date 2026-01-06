from odoo.addons.portal.controllers.portal import CustomerPortal , pager
from odoo.http import request,content_disposition
from odoo import http
from werkzeug.utils import secure_filename
import base64
import csv
import io
from io import StringIO
from datetime import datetime
import xlsxwriter
from odoo.exceptions import UserError,ValidationError
import json
from io import BytesIO
import xlrd
import logging
from odoo.exceptions import ValidationError

import hmac
import hashlib


from odoo import http
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)

class TemperatureMonitoringController(http.Controller):
    @http.route('/create_temp_mon', type='json', auth='public', methods=['POST', 'OPTIONS'], csrf=False,cors='*')
    def create_temp_mon(self, **kwargs):
        # Get raw POST data
        # import wdb; wdb.set_trace()

        data = request.httprequest.get_data()
        request_json = json.loads(data)
        token = request_json.get('token')
        # Extract JSON arrays
        rows = request_json.get('rows', [])
        columns = request_json.get('columns', [])
        sections = request_json.get('sections', [])

        # Extract charts
        graph1 = request_json.get('chart1', None)
        graph2 = request_json.get('chart2', None)
        # import wdb; wdb.set_trace()
        # Helper to clean data URI and decode
        def decode_chart(chart_data):
            if chart_data and chart_data.startswith('data:image/png;base64,'):
                chart_data = chart_data.split(',', 1)[1]
            return chart_data  # can leave as base64 string, Odoo handles Binary fields

        graph1_decoded = decode_chart(graph1)
        graph2_decoded = decode_chart(graph2)

        # Create the record
        # temp_record = request.env['lerm.temp.monitoring'].sudo().create({
        #     'columns_data': columns,
        #     'rows_data': rows,
        #     'graph1': graph1_decoded,
        #     'graph2': graph2_decoded,
        # })
        req_data = self._verify_token(token)
        if not req_data:
            return {"error": "Invalid or expired token"}

        form_id = req_data.get("form_id")
        uid = req_data.get("uid")
        temp_record = request.env['lerm.temp.monitoring'].sudo().search([('id','=',form_id)])
        # import wdb; wdb.set_trace()
        temp_record.sudo().write({
            'columns_data': columns,
            'rows_data': rows,
            'sections_data': sections,
            'graph1': graph1_decoded,
            'graph2': graph2_decoded,
        })

        # Return the ID or success message
        return {'success': True, 'id': temp_record.id}
    
    def _get_secret_key(self):
        """Fetch the secret key from system parameters"""
        key = request.env['ir.config_parameter'].sudo().get_param('temp_monitoring_secret_key')
        if not key:
            raise ValueError("Missing secret key in system parameters.")
        return key
    
    def _verify_token(self, token):
        """Verify HMAC token and return decoded data if valid"""
        secret_key = self._get_secret_key()

        try:
            decoded = json.loads(base64.urlsafe_b64decode(token))
            data = decoded["data"]
            sig = decoded["sig"]

            # Recreate expected signature
            expected_sig = hmac.new(
                secret_key.encode(),
                json.dumps(data, separators=(',', ':')).encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(sig, expected_sig):
                return None  # invalid signature

            return data

        except Exception:
            return None  # invalid format or base64 error
    
    # @http.route('/get_temp_mon/<int:entry_id>', methods=["GET"], type="json", auth='public', website=True, cors='*')
    # def get_temp_mon(self, entry_id, **kwargs):
    #     try:
    #         # Fetch specific record
    #         record = request.env['lerm.temp.monitoring'].sudo().browse(entry_id)
            
    #         if not record.exists():
    #             return {
    #                 'success': False,
    #                 'error': 'Entry not found'
    #             }
            
    #         # Convert binary data to base64 for charts (if needed for display)
    #         graph1_b64 = None
    #         graph2_b64 = None
            
    #         if record.graph1:
    #             graph1_b64 = base64.b64encode(record.graph1).decode('utf-8')
            
    #         if record.graph2:
    #             graph2_b64 = base64.b64encode(record.graph2).decode('utf-8')
            
    #         return {
    #             'success': True,
    #             'id': record.id,
    #             'name': record.name,
    #             'columns': record.columns_data or [],
    #             'rows': record.rows_data or [],
    #             'graph1': graph1_b64,
    #             'graph2': graph2_b64,
    #             'create_date': record.create_date.isoformat() if record.create_date else None,
    #             'write_date': record.write_date.isoformat() if record.write_date else None,
    #         }
            
    #     except Exception as e:
    #         return {
    #             'success': False,
    #             'error': str(e)
    #         }

    @http.route('/api/temp_monitoring/verify', type='json', auth='public', methods=['POST', 'OPTIONS'], csrf=False,cors='*')
    def verify_and_get_data(self, **post):
        # import wdb; wdb.set_trace()
        data = request.httprequest.get_data()
        request_json = json.loads(data)
        """
        Verify the token, and if valid, return the form data.
        """
        token = request_json['token']
        if not token:
            return {"error": "Missing token"}

        # Verify token
        data = self._verify_token(token)
        if not data:
            return {"error": "Invalid or expired token"}

        form_id = data.get("form_id")
        uid = data.get("uid")

        # Fetch record securely
        form = request.env['lerm.temp.monitoring'].sudo().browse(form_id)
        if not form.exists():
            return {"error": "Form not found"}

        # Optional: You could also verify the user (uid)
        # if form.create_uid.id != uid:
        #     return {"error": "User not authorized"}

        # Return relevant form data
        return {
            "valid": True,
            "form_id": form.id,
            "project_name": form.project_name,
            "columns_data": form.columns_data,
            "rows_data": form.rows_data,
            "graph1": bool(form.graph1),  # True if present
            "graph2": bool(form.graph2),
        }