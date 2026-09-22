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
        data = request.httprequest.get_data()
        request_json = json.loads(data)
        token = request_json.get('token')
        
        # Extract JSON arrays
        rows = request_json.get('rows', [])
        columns = request_json.get('columns', [])
        sections = request_json.get('sections', [])
        chart1_cols = request_json.get('chart1_cols', [])
        chart2_cols = request_json.get('chart2_cols', [])
        thermocouple_locations = request_json.get('thermocouple_locations', [])
        
        _logger.info("=== DEBUG THERMOCOUPLE SUBMIT ===")
        _logger.info(f"Received thermocouple_locations: {thermocouple_locations}")
        _logger.info("=================================")
        
        # Extract charts
        graph1 = request_json.get('chart1', None)
        graph2 = request_json.get('chart2', None)
        
        # Helper to clean data URI and decode
        def decode_chart(chart_data):
            if chart_data and chart_data.startswith('data:image/png;base64,'):
                chart_data = chart_data.split(',', 1)[1]
            return chart_data
        graph1_decoded = decode_chart(graph1)
        graph2_decoded = decode_chart(graph2)
        req_data = self._verify_token(token)
        if not req_data:
            return {"error": "Invalid or expired token"}
        form_id = req_data.get("form_id")
        uid = req_data.get("uid")
        temp_record = request.env['lerm.temp.monitoring'].sudo().search([('id','=',form_id)])
        
        temp_record.sudo().write({
            'columns_data': columns,
            'rows_data': rows,
            'sections_data': sections,
            'graph1': graph1_decoded,
            'graph2': graph2_decoded,
            'chart1_cols': chart1_cols,
            'chart2_cols': chart2_cols,
            # Convert list to JSON string if your Odoo field is a Char/Text field
            'thermocouple_locations': json.dumps(thermocouple_locations) if thermocouple_locations else "[]"
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
    

    @http.route('/api/temp_monitoring/verify', type='json', auth='public', methods=['POST', 'OPTIONS'], csrf=False,cors='*')
    def verify_and_get_data(self, **post):
        data = request.httprequest.get_data()
        request_json = json.loads(data)
        """
        Verify the token, and if valid, return the form data.
        """
        token = request_json.get('token')
        if not token:
            return {"error": "Missing token"}
        # Verify token
        data = self._verify_token(token)
        if not data:
            return {"error": "Invalid or expired token"}
        form_id = data.get("form_id")
        
        # Fetch record securely
        form = request.env['lerm.temp.monitoring'].sudo().browse(form_id)
        if not form.exists():
            return {"error": "Form not found"}
            
        # Parse the JSON string back to a Python list, or provide an empty list if not set
        parsed_thermocouple_locations = []
        if form.thermocouple_locations:
            try:
                parsed_thermocouple_locations = json.loads(form.thermocouple_locations)
            except json.JSONDecodeError:
                parsed_thermocouple_locations = []
        # Return relevant form data
        return {
            "valid": True,
            "form_id": form.id,
            "project_name": form.project_name,
            "columns_data": form.columns_data,
            "rows_data": form.rows_data,
            "sections_data": form.sections_data,
            "graph1": bool(form.graph1),  # True if present
            "graph2": bool(form.graph2),
            "chart1_cols": form.chart1_cols,
            "chart2_cols": form.chart2_cols,
            "customer": form.eln_ref.srf_id.customer.name if form.eln_ref and form.eln_ref.srf_id and form.eln_ref.srf_id.customer else "",
            "project": form.eln_ref.srf_id.name_work.project_name if form.eln_ref and form.eln_ref.srf_id and form.eln_ref.srf_id.name_work else "",
            "sample_description": form.eln_ref.sample_id.sample_description if form.eln_ref and form.eln_ref.sample_id else "",
            "test_start": form.eln_ref.start_date,
            "test_end": form.eln_ref.end_date,
            "client_name": form.eln_ref.srf_id.client if form.eln_ref and form.eln_ref.srf_id else "",
            "consultant_name": form.eln_ref.srf_id.consultant_name1 if form.eln_ref and form.eln_ref.srf_id else "",
            "group": form.eln_ref.group.group if form.eln_ref and form.eln_ref.group else "",
            "test_name": form.eln_ref.material.name if form.eln_ref and form.eln_ref.material else "",
            "client_reference":form.eln_ref.srf_id.client_refrence if form.eln_ref and form.eln_ref.srf_id else "",
            "reference": form.eln_ref.material.method_reference,
            "grade": form.grade,
            "size": form.size.size if form.size else "",
            "discipline":form.eln_ref.discipline.discipline,
            "test_report_no": form.eln_ref.kes_no if form.eln_ref else "",
            "report_issue_date": form.eln_ref.end_date if form.eln_ref else "",
            "data_logger_label": form.data_logger_label,
            "thickness": form.thickness,
            "thermocouple_locations": parsed_thermocouple_locations,
            "checked_by_person":form.eln_ref.sample_id.check_by.name,
            "approved_by_person":form.eln_ref.sample_id.approved_by.name,
            "checked_by_designation":form.eln_ref.sample_id.check_by.job_title,
            "approved_by_designation":form.eln_ref.sample_id.approved_by.job_title,
        }