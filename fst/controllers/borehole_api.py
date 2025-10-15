from odoo import http
from odoo.http import request, Response
import json

class BoreholeAPI(http.Controller):

    @http.route('/api/borehole/<int:parent_id>', type='json', auth='public', methods=['POST', 'OPTIONS'], csrf=False,cors='*')
    def get_borehole_data(self, parent_id, **kwargs):
        if request.httprequest.method == 'OPTIONS':
            # Preflight request
            return Response(status=200, headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            })

        parent = request.env['soil.borehole.parent'].sudo().browse(parent_id)
        if not parent.exists():
            data = {'error': 'Record not found'}
        else:
            data = {
                'id': parent.id,
                'name': parent.name,
                'rec_date': str(parent.rec_date or ''),
                'combined_images': [
                    {
                        'id': img.id,
                        'name': img.name,
                        'image_data': img.image_field
                    } for img in parent.combined_images
                ],
                'borehole_lines': [
                    {
                        'id': line.id,
                        'name': line.name,
                        'depth': line.depth,
                    } for line in parent.borehole_lines
                ]
            }

        return Response(
            json.dumps(data),
            content_type='application/json',
            headers={'Access-Control-Allow-Origin': '*'}
        )


