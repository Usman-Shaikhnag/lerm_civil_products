import base64
import os
import shutil
import subprocess
import tempfile
from ..serializers.pile_load import PileLoadSerializer
import json
import base64
import hmac
import hashlib
from odoo import http
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

class PileLoadReportController(http.Controller):
    
    def _get_secret_key(self):
        return request.env['ir.config_parameter'].sudo().get_param('pile_load_report_secret_key')

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
        
    # @http.route("/api/report/pile/<int:record_id>", type='json', methods=['POST', 'OPTIONS'], auth='public', csrf=False, cors='*')
    # def pile_report(self, record_id):

    #     rec = request.env["pile.load.test.parent"].browse(record_id)

    #     return {
    #         "report_no": rec.name,
    #         "project": rec.project_name,
    #         "client": rec.client_name,
    #         "location": rec.location,
    #         "test_date": str(rec.test_date),
    #     }

    @http.route("/api/report/verify",type="json",auth="public",methods=["POST", "OPTIONS"],csrf=False,cors="*",)
    def verify_report(self, **post):

        if request.httprequest.method == "OPTIONS":
            return {}
        try:

            # Read token
            if not request.params:
                data = json.loads(request.httprequest.get_data())
            else:
                data = request.params

            # print("DATA:", data)
            token = data.get("token")

            # Verify token
            verified = self._verify_token(token)
            if not verified:
                return {"error": "Invalid token"}
            model = verified.get("model")
            record_id = verified.get("record_id")

            record = request.env[model].sudo().browse(record_id)
            # print("RECORD:", record)
            if not record.exists():
                return {"error": "Record not found"}

            serializer = PileLoadSerializer(record)
            data = serializer.serialize()
            # import wdb;wdb.set_trace()
            # _logger.info(data)
            return data
            
        except Exception as e:
            return {"error": str(e)}