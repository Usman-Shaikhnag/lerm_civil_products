from odoo import models
from odoo.modules.module import get_module_resource
import base64


class CustomGeotechReport(models.AbstractModel):
    _name = 'report.lerm_civil.custom_geotech_report'
    _description = 'Custom Geotech Report'

    def _get_report_values(self, docids, data=None):

        docs = self.env['sample.request.review'].browse(docids)

        logo_path = get_module_resource(
            'lerm_civil', 'static/src/img', 'genstru_logo.png'
        )

        logo_base64 = False
        if logo_path:
            with open(logo_path, 'rb') as f:
                logo_base64 = base64.b64encode(f.read()).decode('utf-8')

        return {
            'docs': docs,
            'logo_base64': logo_base64,
        }