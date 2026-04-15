from odoo import api, fields, models
import hmac
import hashlib
import base64
import json

class TempMonitoring(models.Model):
    _name = "lerm.temp.monitoring"
    _rec_name = "project_name"

    project_name = fields.Char("Project Name")
    columns_data = fields.Json(string="Columns", default=list)
    rows_data = fields.Json(string="Rows", default=list)
    sections_data = fields.Json(string="Sections", default=list)
    graph1 = fields.Binary()
    graph2 = fields.Binary()

    def _get_secret_key(self):
        """Fetch the secret key from system parameters"""
        key = self.env['ir.config_parameter'].sudo().get_param('temp_monitoring_secret_key')
        if not key:
            raise ValueError("Missing secret key! Please set 'temp_monitoring_secret_key' in System Parameters.")
        return key

    def open_form(self):
        """Redirect user to React page with secure token"""
        self.ensure_one()

        secret_key = self._get_secret_key()

        # Step 1: Create token data
        data = {
            "form_id": self.id,
            "uid": self.env.user.id,
        }

        # Step 2: Convert to JSON and sign it
        payload = json.dumps(data, separators=(',', ':'))
        signature = hmac.new(
            secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        # Step 3: Encode final token
        token = base64.urlsafe_b64encode(
            json.dumps({
                "data": data,
                "sig": signature
            }).encode()
        ).decode()

        # Step 4: React app URL
        react_url = f"http://147.93.154.53:5173/temp_monitoring?token={token}"

        # Step 5: Redirect to React app
        return {
            'type': 'ir.actions.act_url',
            'url': react_url,
            'target': 'new'
        }