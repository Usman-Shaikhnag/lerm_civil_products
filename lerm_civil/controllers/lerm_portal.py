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



from odoo import http
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)

class LermSampleController(http.Controller):

    @http.route('/create_temp_mon', methods=["POST"], type="json", auth='public', website=True, cors='*')
    def create_temp_mon(self, **kwargs):
        # Get raw POST data
        data = request.httprequest.get_data()
        request_json = json.loads(data)

        # Extract JSON arrays
        rows = request_json.get('rows', [])
        columns = request_json.get('columns', [])

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
        temp_record = request.env['temperature.monitoring.react'].sudo().create({
            'columns_data': columns,
            'rows_data': rows,
            'graph1': graph1_decoded,
            'graph2': graph2_decoded,
        })

        # Return the ID or success message
        return {'success': True, 'id': temp_record.id}
    
    @http.route('/get_temp_mon/<int:entry_id>', methods=["GET"], type="json", auth='public', website=True, cors='*')
    def get_temp_mon(self, entry_id, **kwargs):
        try:
            # Fetch specific record
            record = request.env['temperature.monitoring.react'].sudo().browse(entry_id)
            
            if not record.exists():
                return {
                    'success': False,
                    'error': 'Entry not found'
                }
            
            # Convert binary data to base64 for charts (if needed for display)
            graph1_b64 = None
            graph2_b64 = None
            
            if record.graph1:
                graph1_b64 = base64.b64encode(record.graph1).decode('utf-8')
            
            if record.graph2:
                graph2_b64 = base64.b64encode(record.graph2).decode('utf-8')
            
            return {
                'success': True,
                'id': record.id,
                'name': record.name,
                'columns': record.columns_data or [],
                'rows': record.rows_data or [],
                'graph1': graph1_b64,
                'graph2': graph2_b64,
                'create_date': record.create_date.isoformat() if record.create_date else None,
                'write_date': record.write_date.isoformat() if record.write_date else None,
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/sampleRequestList', type='http', auth='user', website=True)
    def sample_request_list(self, **kwargs):
        user = request.env.user
        partner_id = user.partner_id

        child_users = request.env['portal.user.master'].sudo().search([('customer','=',partner_id.id)]).child_users
        partner_ids = [partner_id.id]
        for child in child_users:
            partner_ids.append(child.partner_id.id)
        
        # Get pagination parameters from URL
        page = int(kwargs.get('page', 1))
        limit = 10  # Number of items per page
        
        # Get total count of records
        total = request.env['customer.sample.requests'].sudo().search_count([
            ('partner_id', 'in', partner_ids)
        ])
        
        # Calculate pagination values
        total_pages = max((total + limit - 1) // limit, 1)
        page = max(min(page, total_pages), 1)
        offset = (page - 1) * limit
        
        # Search with pagination and order by date descending (newest first)
        csr = request.env['customer.sample.requests'].sudo().search([
            ('partner_id', 'in', partner_ids)
        ], order='create_date desc', limit=limit, offset=offset)
        
        return request.render('lerm_civil.sample_requests_list', {
            'csr': csr,
            'partner': partner_id,
            'page': page,
            'total_pages': total_pages,
            'total': total,
            'offset': offset,
            'limit': limit,
        })

    @http.route('/viewReports', type='http', auth='user', website=True)
    def view_reports_list(self, **kwargs):
        user = request.env.user
        partner_id = user.partner_id

        child_users = request.env['portal.user.master'].sudo().search([('customer','=',partner_id.id)]).child_users
        partner_ids = [partner_id.id]
        for child in child_users:
            partner_ids.append(child.partner_id.id)

        total = request.env['lerm.srf.sample'].sudo().search_count([('srf_id.customer','in',partner_ids),('state','=','4-in_report'),('display_report_portal','=',True)])
        page = int(kwargs.get('page', 1))
        limit = 10  # Number of items per page
        total_pages = max((total + limit - 1) // limit, 1)
        page = max(min(page, total_pages), 1)
        offset = (page - 1) * limit
        samples = request.env['lerm.srf.sample'].sudo().search([('srf_id.customer','in',partner_ids),('state','=','4-in_report'),('display_report_portal','=',True)],order='create_date desc', limit=limit, offset=offset)

        return request.render('lerm_civil.sample_reports_list', {
            'samples': samples,
            'partner': partner_id,
            'page': page,
            'total_pages': total_pages,
            'total': total,
            'offset': offset,
            'limit': limit,
        })


    @http.route('/viewDocuments', type='http', auth='user', website=True)
    def shared_documents_list(self, **kwargs):
        user = request.env.user
        partner_id = user.partner_id

        child_users = request.env['portal.user.master'].sudo().search([('customer','=',partner_id.id)]).child_users
        partner_ids = [partner_id.id]
        for child in child_users:
            partner_ids.append(child.partner_id.id)
        
        # Get pagination parameters from URL
        page = int(kwargs.get('page', 1))
        limit = 10  # Number of items per page
        
        # Get total count of records
        total = request.env['partner.document'].sudo().search_count([
            ('partner_id', 'in', partner_ids)
        ])
        
        # Calculate pagination values
        total_pages = max((total + limit - 1) // limit, 1)
        page = max(min(page, total_pages), 1)
        offset = (page - 1) * limit
        
        # Search with pagination and order by date descending (newest first)
        records = request.env['partner.document'].sudo().search([
            ('partner_id', 'in', partner_ids)
        ], order='create_date desc', limit=limit, offset=offset)
        
        return request.render('lerm_civil.shared_documents_list', {
            'records': records,
            'partner': partner_id,
            'page': page,
            'total_pages': total_pages,
            'total': total,
            'offset': offset,
            'limit': limit,
        })

        
    
    @http.route('/sampleRequests', type='http', auth='user', website=True)
    def sampleRequests(self, **kwargs):
        user = request.env.user
        partner_id = user.partner_id
        child_users = request.env['portal.user.master'].sudo().search([('customer','=',partner_id.id)]).child_users
        partner_ids = [partner_id.id]
        for child in child_users:
            partner_ids.append(child.partner_id.id)
        # import wdb; wdb.set_trace()
        
        projects = request.env['res.partner.project'].sudo().search([('contact_id', 'in', partner_ids)])
        customers = request.env['res.partner'].sudo().search([('id', 'in', partner_ids)])
        
        
        return request.render('lerm_civil.sample_requests_form', {
            'projects': projects,
            'customers':customers
        })
    
    @http.route('/viewSampleRequests/<int:csr_id>', type='http', auth='user', website=True)
    def viewSampleRequests(self,csr_id, **kwargs):
        csr = request.env['customer.sample.requests'].sudo().search([('id','=',int(csr_id))],limit=1)
        return request.render('lerm_civil.view_sample_request', {
            'csr': csr
        })
    
    @http.route('/deleteSampleRequest/<int:csr_id>', type='http', auth='user', website=True)
    def deleteSampleRequest(self,csr_id, **kwargs):
        csr = request.env['customer.sample.requests'].sudo().search([('id','=',int(csr_id))],limit=1)
        samples = csr.samples
        if samples:
            samples.sudo().unlink()
        if csr:
            csr.sudo().unlink()

        return request.redirect('/sampleRequestList')

    @http.route('/lerm/get_projects', methods=["POST"], type="json", auth='user')
    def get_projects(self):

        # import wdb; wdb.set_trace()
        try:
            # Manually parse JSON data
            data = request.httprequest.get_data()
            import json
            request_json = json.loads(data)
            
            alias_id = request_json.get('customer_id')
            if not alias_id:
                return request.make_json_response({'error': 'alias_id missing'})
                
            projects = request.env['res.partner.project'].sudo().search([
                ('contact_id', '=', int(alias_id))
            ])
            
            return {
                'projects': [{
                    'id': project.id,
                    'name': project.project_name  
                } for project in projects]
            }
        except Exception as e:
            return request.make_json_response({'error': str(e)})

    
    @http.route('/lerm/get_groups', methods=["POST"], type="json", auth='user')
    def get_groups(self):

        # import wdb; wdb.set_trace()
        try:
            # Manually parse JSON data
            data = request.httprequest.get_data()
            import json
            request_json = json.loads(data)
            
            discipline_id = request_json.get('discipline_id')
            if not discipline_id:
                return request.make_json_response({'error': 'discipline_id missing'})
                
            groups = request.env['lerm_civil.group'].sudo().search([
                ('discipline', '=', int(discipline_id))
            ])
            
            return {
                'groups': [{
                    'id': group.id,
                    'name': group.group  
                } for group in groups]
            }
        except Exception as e:
            return request.make_json_response({'error': str(e)})
        
    @http.route('/lerm/get_products', methods=["POST"], type="json", auth='user')
    def get_products(self):

        # import wdb; wdb.set_trace()
        try:
            # Manually parse JSON data
            data = request.httprequest.get_data()
            import json
            request_json = json.loads(data)
            
            group_id = request_json.get('group_id')
            if not group_id:
                return request.make_json_response({'error': 'group_id missing'})
                
            products = request.env['product.template'].sudo().search([
                ('group', '=', int(group_id))
            ])
            
            return {
                'products': [{
                    'id': product.id,
                    'name': product.name  
                } for product in products]
            }
        except Exception as e:
            return request.make_json_response({'error': str(e)})
        
    @http.route('/lerm/get_parameters', methods=["POST"], type="json", auth='user')
    def get_parameters(self):

        # import wdb; wdb.set_trace()
        try:
            # Manually parse JSON data
            data = request.httprequest.get_data()
            import json
            request_json = json.loads(data)
            
            product_id = request_json.get('product_id')
            if not product_id:
                return request.make_json_response({'error': 'product_id missing'})
            
            grades = request.env['lerm.grade.line'].sudo().search([('product_id','=',int(product_id))])
            sizes = request.env['lerm.size.line'].sudo().search([('product_id','=',int(product_id))])

                
            parameters = request.env['lerm.parameter.master'].sudo().search([
                ('material', '=', int(product_id))
            ])
            # import wdb; wdb.set_trace()
            return {
                'parameters': [{
                    'id': parameter.id,
                    'name': parameter.parameter_name  
                } for parameter in parameters],
                'grades':[{
                    'id': grade.id,
                    'name': grade.grade  
                } for grade in grades],
                'sizes':[{
                    'id': size.id,
                    'name': size.size  
                } for size in sizes]
            }
        except Exception as e:
            return request.make_json_response({'error': str(e)})

    
    
    @http.route('/createSampleRequest', type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def custom_request_create(self, **kwargs):
        user = request.env.user
        partner_id = user.partner_id

        alias_data = kwargs.get('customer_id')
        billing_customer_data = kwargs.get('billing_customer_id')
        attachment = kwargs.get('attachment')

        

        alias_id = request.env['res.partner'].sudo().search([('id','=',int(alias_data))])
        # import wdb; wdb.set_trace()

        if billing_customer_data != '':

            billing_customer_id = request.env['res.partner'].sudo().search([('id','=',int(billing_customer_data))]).id
        else:
            billing_customer_id = False




        sample_count = sum(1 for key in kwargs if key.startswith("product_name_"))
        samples = []

        for i in range(sample_count):
            parameter_ids = [int(p) for p in kwargs.get(f"parameter_line_{i}", "").split(",") if p]

            # import wdb; wdb.set_trace()
            sample = {
                "discipline_id": int(kwargs.get(f"discipline_id_{i}")) if kwargs.get(f"discipline_id_{i}") else False,
                "group_id": int(kwargs.get(f"group_id_{i}")) if kwargs.get(f"group_id_{i}") else False,
                "product_id": int(kwargs.get(f"product_name_{i}")),
                "product_description":kwargs.get(f"description_{i}"),
                # "quantity":kwargs.get(f"quantity_{i}"),
                "grade_id": int(kwargs.get(f"grade_id_{i}")) if kwargs.get(f"grade_id_{i}") else False,
                "size_id": int(kwargs.get(f"size_id_{i}")) if kwargs.get(f"size_id_{i}") else False,
                "parameters": [(6, 0, parameter_ids)],
            }
            samples.append((0, 0, sample))  # Proper One2many format

        date = kwargs.get("request_date")
        project_id = int(kwargs.get("project_id"))

        data = {
            'partner_id': alias_id.id,
            'billing_customer':billing_customer_id,
            'project': project_id,
            'date': date,
            'samples': samples  # One2many field
        }

        if attachment:
            attachment_filename = attachment.filename
            attachment_binary  = base64.b64encode(attachment.read())
            data['attachment'] = attachment_binary
            data['attachment_name'] = attachment_filename

        request.env['customer.sample.requests'].sudo().create(data)

        return request.redirect('/sampleRequestList')



    @http.route('/download/sample/report/nabl/<int:sam_req_id>', type='http', auth='user', website=True)
    def download_sample_report(self, sam_req_id, **kw):
        sample = request.env['lerm.srf.sample'].sudo().search(
            [('customer_portal_sample', '=', sam_req_id)], limit=1
        )
        if not sample:
            return request.not_found()

        eln = request.env["lerm.eln"].sudo().search(
            [('sample_id', '=', sample.id)], limit=1
        )
        if not eln:
            return request.not_found()

        # Get template safely
        template = False
        if eln.is_product_based_calculation and eln.material.product_based_calculation:
            template = eln.material.product_based_calculation[:1].main_report_template
        elif eln.parameters_result.parameter:
            template = eln.parameters_result.parameter[:1].main_report_template

        if not template:
            return request.not_found()

        template = template[:1]

        # import wdb; wdb.set_trace()

        pdf_content = template._render_qweb_pdf(
            template,   
            [sample.id], 
            data={
                'fromsample': True,
                'inreport': sample.state,
                'nabl': True,
                'fromEln': False,
                'report_wizard': True,
                'sample': sample.id,
            }
        )

        # Safe filename
        safe_name = sample.material_id.lab_name or "Report"
        filename = f"{safe_name} Report.pdf"

        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', content_disposition(filename)),
            ],
        )
    

    @http.route('/download/sample/report/nonnabl/<int:sam_req_id>', type='http', auth='user', website=True)
    def download_sample_nonnabl_report(self, sam_req_id, **kw):
        sample = request.env['lerm.srf.sample'].sudo().search(
            [('customer_portal_sample', '=', sam_req_id)], limit=1
        )
        if not sample:
            return request.not_found()

        eln = request.env["lerm.eln"].sudo().search(
            [('sample_id', '=', sample.id)], limit=1
        )
        if not eln:
            return request.not_found()

        # Get template safely
        template = False
        if eln.is_product_based_calculation and eln.material.product_based_calculation:
            template = eln.material.product_based_calculation[:1].main_report_template
        elif eln.parameters_result.parameter:
            template = eln.parameters_result.parameter[:1].main_report_template

        if not template:
            return request.not_found()

        template = template[:1]

        # import wdb; wdb.set_trace()

        pdf_content = template._render_qweb_pdf(
            template,   
            [sample.id],   
            data={
                'fromsample': True,
                'inreport': sample.state,
                'nabl': False,
                'fromEln': False,
                'report_wizard': True,
                'sample': sample.id,
            }
        )

        # Safe filename
        safe_name = sample.material_id.lab_name or "Report"
        filename = f"{safe_name} Report.pdf"

        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', content_disposition(filename)),
            ],
        )
    

    @http.route('/downloadSampleReportNabl/<int:sample_id>', type='http', auth='user', website=True)
    def downloadNabl_report(self, sample_id, **kw):
        sample = request.env['lerm.srf.sample'].sudo().search([('id','=', sample_id)], limit=1)
        if not sample:
            return request.not_found()

        # Get ELN and report template name
        eln = request.env["lerm.eln"].sudo().search([('sample_id', '=', sample.id)], limit=1)
        if not eln:
            return request.not_found()

        if eln.is_product_based_calculation:
            template = eln.material.product_based_calculation[0].main_report_template
        else:
            template = eln.parameters_result.parameter[0].main_report_template

        template_name = template.report_name

        # Render PDF
        pdf_content, content_type = request.env.ref(template.xml_id).sudo()._render_qweb_pdf([sample.id], data={
            'fromsample': True,
            'inreport': sample.state,
            'nabl': True,
            'fromEln': False,
            'report_wizard':True,
            'sample':sample.id
        })

        # Return HTTP Response
        filename = str(sample.material_id.lab_name)+" Report"
        # filename = "Report.pdf"
        return request.make_response(pdf_content, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', content_disposition(filename))
        ])
    
    @http.route('/downloadSampleReportNonNabl/<int:sample_id>', type='http', auth='user', website=True)
    def download_nonNabl_report(self, sample_id, **kw):
        sample = request.env['lerm.srf.sample'].sudo().search([('id','=', sample_id)], limit=1)
        if not sample:
            return request.not_found()

        # Get ELN and report template name
        eln = request.env["lerm.eln"].sudo().search([('sample_id', '=', sample.id)], limit=1)
        if not eln:
            return request.not_found()

        if eln.is_product_based_calculation:
            template = eln.material.product_based_calculation[0].main_report_template
        else:
            template = eln.parameters_result.parameter[0].main_report_template

        template_name = template.report_name

        # Render PDF
        pdf_content, content_type = request.env.ref(template.xml_id).sudo()._render_qweb_pdf([sample.id], data={
            'fromsample': True,
            'inreport': sample.state,
            'nabl': False,
            'fromEln': False,
            'report_wizard':True,
            'sample':sample.id
        })

        # Return HTTP Response
        filename = str(sample.material_id.lab_name)+" Report"
        # filename = "Report.pdf"
        return request.make_response(pdf_content, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', content_disposition(filename))
        ])
    
    @http.route('/downloadDocument/<int:record_id>', type='http', auth='user', website=True)
    def download_document(self, record_id, **kwargs):
        document = request.env['partner.document'].sudo().browse(record_id)
        if not document.exists():
            return request.not_found()

        # Set filename (fallback if no name)
        filename = document.document_name or "document"
        # Detect file type from base64 (if you want you can be more precise)
        file_data = document.document
        if not file_data:
            return request.not_found()

        file_content = base64.b64decode(file_data)
        return request.make_response(
            file_content,
            headers=[
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', f'attachment; filename="{filename}"'),
            ]
        )