
from odoo import http
from odoo.http import request

class DebugController(http.Controller):
    @http.route('/debug/samples', type='json', auth='user')
    def get_samples(self):
        Sample = request.env['lerm.srf.sample'].sudo()
        samples = Sample.search([('report_due_date', '!=', False)])
        res = []
        for s in samples:
            res.append({
                'id': s.id,
                'name': s.name,
                'due_date': s.report_due_date,
                'state': s.state,
                'eln_id': s.eln_id.id if s.eln_id else False
            })
        return res
