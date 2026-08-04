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

    chart1_cols = fields.Json(string="Chart 1 Columns", default=list)
    chart2_cols = fields.Json(string="Chart 2 Columns", default=list)


    eln_ref = fields.Many2one('lerm.eln',string="ELN")
    grade = fields.Char(string="Grade")
    size = fields.Many2one('lerm.size.line',string="Size",store=True)


    thickness = fields.Char('Thickness/Depth')
    data_logger_label = fields.Char('Data Logger Label')
    reference = fields.Char('Reference')

    thermocouple_locations = fields.Text(string="Thermocouple Locations", default=list)
    



    

    @api.model
    def create(self, vals):
        record = super(TempMonitoring, self).create(vals)
        # import wdb;wdb.set_trace()
        # record.get_all_fields()
        # self._compute_size_id()
        # self._compute_grade_id()
        record.eln_ref.write({'model_id':record.id})
        return record

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
        # react_url = f"http://147.93.154.53:5173/temp_monitoring?token={token}"

        # later replace with this 
        react_url = (
            "https://knack17.lerm.in/react/"
            f"temp_monitoring?token={token}"
        )

        # Step 5: Redirect to React app
        return {
            'type': 'ir.actions.act_url',
            'url': react_url,
            'target': 'new'
        }