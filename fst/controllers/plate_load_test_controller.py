from odoo import http
from odoo.http import request
import json
import base64
import hmac
import hashlib
import logging

_logger = logging.getLogger(__name__)


class PlateLoadTestController(http.Controller):
    @http.route('/test_cors', type='http', auth='public', cors='*')
    def test_cors(self, **kwargs):
        return "CORS WORKING"

    def _get_secret_key(self):
        return request.env['ir.config_parameter'].sudo().get_param('plate_load_secret_key')

    def _verify_token(self, token):
        secret_key = self._get_secret_key()
        try:
            decoded = json.loads(base64.urlsafe_b64decode(token))
            data = decoded["data"]
            sig = decoded["sig"]

            expected_sig = hmac.new(
                secret_key.encode(),
                json.dumps(data, separators=(',', ':')).encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(sig, expected_sig):
                return None
            return data
        except:
            return None

    @http.route('/api/plate_load_test/create', type='json', methods=['POST', 'OPTIONS'], auth='public', csrf=False, cors='*')
    def create_plate_load_test(self, **kwargs):
        _logger.info("Plate Load Test: Create request received")
        if request.httprequest.method == 'OPTIONS':
            return {}

        try:
            # Handle potential manual parsing if needed, but type='json' usually populates request.params
            # if request.params is empty, try manual parsing for robustness
            if not request.params:
                data = json.loads(request.httprequest.get_data())
            else:
                data = request.params

            token = data.get("token")
            verified = self._verify_token(token)
            if not verified:
                return {"error": "Invalid token"}

            form_id = verified.get("form_id")
            record = request.env['lerm.plate.load.test'].sudo().browse(form_id)

            sections = data.get("sections")
            loading_cols = data.get("loading_columns")
            loading_rows = data.get("loading_rows")
            unloading_cols = data.get("unloading_columns")
            unloading_rows = data.get("unloading_rows")
            image_sections = data.get("image_sections")

            _logger.info(f"Writing data to record {form_id}")

            graph = record.generate_pressure_line_chart(loading_rows, unloading_rows)
            # import wdb;wdb.set_trace()
            record.write({
                "sections_data": sections,
                "loading_columns_data": loading_cols,
                "loading_table_data": loading_rows,
                "unloading_columns_data": unloading_cols,
                "unloading_table_data": unloading_rows,
                "image_sections": image_sections,
                "graph": graph,
            })

            pdf = record.generate_pdf_report()
            record.write({"pdf_report": pdf})

            return {"success": True, "graph": graph}
        except Exception as e:
            _logger.error(f"Plate Load Test Save Error: {str(e)}")
            return {"error": str(e)}

    @http.route('/api/plate_load_test/verify', type='json', methods=['POST', 'OPTIONS'], auth='public', csrf=False, cors='*')
    def verify_and_get_data(self, **post):
        _logger.info("Plate Load Test: Verify request received")
        if request.httprequest.method == 'OPTIONS':
            return {}

        try:
            # type='json' routes populate request.params directly
            if not request.params:
                data = json.loads(request.httprequest.get_data())
            else:
                data = request.params

            token = data.get("token")
            verified = self._verify_token(token)
            if not verified:
                return {"error": "Invalid token"}

            form_id = verified.get("form_id")
            record = request.env['lerm.plate.load.test'].sudo().browse(form_id)

            if not record.exists():
                return {"error": "Record not found"}

            _logger.info(f"Returning data for record {form_id}")
            graph = record.generate_pressure_line_chart(record.loading_table_data, record.unloading_table_data)
            return {
                "valid": True,
                "form_id": form_id,
                "sections_data": record.sections_data,
                "loading_columns": record.loading_columns_data,
                "loading_rows": record.loading_table_data,
                "unloading_columns": record.unloading_columns_data,
                "unloading_rows": record.unloading_table_data,
                "image_sections": record.image_sections,
                "graph": graph, 
            }
        except Exception as e:
            _logger.error(f"Plate Load Test Verify Error: {str(e)}")
            return {"error": str(e)}

    @http.route('/api/plate_load_test/download_pdf', type='http', methods=['POST', 'OPTIONS'], auth='public', csrf=False, cors='*')
    def download_pdf(self, **kwargs):
        _logger.info("Plate Load Test: Download PDF request received")
        if request.httprequest.method == 'OPTIONS':
            response = request.make_response('')
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response

        try:
            data = json.loads(request.httprequest.get_data())
            token = data.get("token")

            verified = self._verify_token(token)
            if not verified:
                return request.make_response(
                    json.dumps({"error": "Invalid token"}),
                    headers={'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
                )

            form_id = verified.get("form_id")
            record = request.env['lerm.plate.load.test'].sudo().browse(form_id)

            if not record.pdf_report:
                return request.make_response(
                    json.dumps({"error": "No PDF report available"}),
                    headers={'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
                )

            pdf_data = base64.b64decode(record.pdf_report)
            filename = record.pdf_filename or 'Plate_Load_Test_Report.pdf'

            _logger.info(f"Serving PDF for record {form_id}")
            return request.make_response(
                pdf_data,
                headers={
                    'Content-Type': 'application/pdf',
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Access-Control-Allow-Origin': '*'
                }
            )
        except Exception as e:
            _logger.error(f"Plate Load Test Download PDF Error: {str(e)}")
            return request.make_response(
                json.dumps({"error": str(e)}),
                headers={'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
            )
