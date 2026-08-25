from odoo import http
from odoo.http import request
import requests

class DownloadController(http.Controller):
    @http.route('/web/binary/download_ftp', type='http', auth="user")
    def download_ftp(self, url, **kwargs):
        # Get the file from FTP server
        response = requests.get(url, stream=True)
        
        # Create a response with download headers
        return request.make_response(
            response.content,
            headers=[
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', f'attachment; filename="{url.split("/")[-1]}"'),
            ]
        )
