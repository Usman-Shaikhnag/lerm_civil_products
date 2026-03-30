# controller
from odoo import http
from odoo.http import request
from datetime import datetime,timedelta,time
from collections import defaultdict, Counter
from operator import itemgetter # Required for sorting
import logging

_logger = logging.getLogger(__name__)

class LermCivilDashboard(http.Controller):

    @http.route(['/dashboard/getdata'], type="json", auth="user", methods=["POST"])
    def get_dashboard_data(self, **kw):
        """
        Fetches data for the charts and KPIs, filtered by date, discipline, lab, and company.
        """
        # Extract parameters from **kw
        start_date = kw.get('start_date')
        end_date = kw.get('end_date')
        discipline = kw.get('discipline')
        lab_id = kw.get('lab_id')
        company_id = kw.get('company_id')
        
        Sample = request.env['lerm.srf.sample'].sudo()
        
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except Exception:
            # Return error if dates are missing or invalid
            return {"error": "Invalid date format or missing dates"}

        # 1. Initial Domain (Date Filtering)
        domain = [
            ('sample_received_date', '>=', start_dt),
            ('sample_received_date', '<=', end_dt),
        ]

        # 2. Discipline Filtering
        if discipline and discipline != "ALL":
            domain.append(('discipline_id.discipline', '=', discipline))
            
        # 3. Lab Filtering
        if lab_id and lab_id != 'ALL':
            domain.append(('lab_location', '=', int(lab_id)))
            
        # 4. Company Filtering
        if company_id and company_id != 'ALL':
            domain.append(('lab_location.company_id', '=', int(company_id)))

        # Fetch samples
        samples = Sample.search(domain)

        # --- Time-based grouping ---
        days_range = (end_dt - start_dt).days
        period_counter = defaultdict(int)

        for sample in samples:
            date = sample.sample_received_date
            if not date:
                continue

            # Group by day if the range is 30 days or less, otherwise group by month
            if days_range <= 30:
                key = date.strftime("%d-%b") # e.g., 25-Oct
            else:
                key = date.strftime("%b %Y") # e.g., Oct 2023

            period_counter[key] += 1

        # Define the sorting logic
        def sort_key(x):
            try:
                if days_range <= 30:
                    return datetime.strptime(x, "%d-%b")
                else:
                    return datetime.strptime(x, "%b %Y")
            except ValueError:
                return datetime.min

        labels = sorted(
            period_counter.keys(),
            key=sort_key
        )
        counts = [period_counter[l] for l in labels]
        
        # full list of states with labels (including cancelled for completeness)
        ALL_STATES = {
            "1-allotment_pending": "Assignment Pending",
            "7-partially-alloted": "Partially Alloted",
            "2-alloted": "Alloted",
            "7-calculated": "Calculated",
            "3-pending_verification": "Pending Verification",
            "5-pending_approval": "Pending Approval",
            "4-in_report": "In Report",
            "6-cancelled": "Cancelled", 
        }
        
        # --- State-based grouping ---
        state_counter = Counter(samples.mapped("state"))

        state_data = []
        for state, label in ALL_STATES.items():
            state_data.append({
                "state": state,
                "state_label": label,
                "count": state_counter.get(state, 0),
            })
            
        # Prepare the lists needed by the frontend (MainDashboard.js)
        state_labels = [item['state_label'] for item in state_data]
        state_counts = [item['count'] for item in state_data]

        # --- Sample Aging Overview (Optimized with Nested Breakdowns) ---
        aging_domain = [
            ('state', 'in', ['2-alloted', '7-calculated', '3-pending_verification', '5-pending_approval']),
            ('eln_id', '!=', False)
        ]
        if discipline and discipline != "ALL":
            aging_domain.append(('discipline_id.discipline', '=', discipline))
        if lab_id and lab_id != 'ALL':
            aging_domain.append(('lab_location', '=', int(lab_id)))
        if company_id and company_id != 'ALL':
            aging_domain.append(('lab_location.company_id', '=', int(company_id)))

        aging_buckets = self._get_detailed_aging_data(Sample, aging_domain, breakdown_type='technician')

        return {
            "labels": labels,
            "counts": counts,
            "total_count": len(samples),
            "state_labels": state_labels, 
            "state_data": state_data,
            "state_counts": state_counts,
            "total_states": len(state_labels),
            "aging_data": aging_buckets,
        }

    def _get_detailed_aging_data(self, Sample, base_domain, breakdown_type='technician'):
        """
        Helper to calculate aging data with nested breakdowns (Technicians or Products).
        breakdown_type: 'technician' or 'product'
        """
        today_date = datetime.now().date()
        from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
        
        aging_data = {}
        B_RANGES = [
            ("0-7", 0, 7),
            ("8-15", 8, 15),
            ("16-30", 16, 30),
            ("31-45", 31, 45),
            ("46-60", 46, 60),
            ("60+", 61, None)
        ]

        for key, min_days, max_days in B_RANGES:
            d_max = datetime.combine(today_date - timedelta(days=min_days), time.max)
            
            bucket_domain = list(base_domain) + [
                ('eln_id.create_date', '<=', d_max.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
            ]
            if max_days is not None:
                d_min = datetime.combine(today_date - timedelta(days=max_days), time.min)
                bucket_domain.append(('eln_id.create_date', '>=', d_min.strftime(DEFAULT_SERVER_DATETIME_FORMAT)))
            
            # Fetch samples to build nested breakdown
            bucket_samples = Sample.search(bucket_domain)
            
            state_map = {} # state -> {count, breakdown_map}
            for s in bucket_samples:
                state = s.state
                if state not in state_map:
                    state_map[state] = {'count': 0, 'breakdown': {}}
                
                state_map[state]['count'] += 1
                
                # Nested Breakdown
                b_name = "Unknown"
                b_id = 0
                if breakdown_type == 'technician':
                    tech = None
                    if s.eln_id and s.eln_id.parameters_result:
                        for param_res in s.eln_id.parameters_result:
                            if param_res.technician:
                                tech = param_res.technician
                                break
                    if not tech:
                        tech = s.eln_id.technician or s.technicians
                        if not tech and s.eln_id.technician_ids:
                            tech = s.eln_id.technician_ids[0]

                    if tech:
                        b_name = tech.name
                        b_id = tech.id
                else: # product
                    prod = s.material_id
                    if prod:
                        b_name = prod.name
                        b_id = prod.id
                
                if b_id not in state_map[state]['breakdown']:
                    state_map[state]['breakdown'][b_id] = {'id': b_id, 'name': b_name, 'count': 0}
                state_map[state]['breakdown'][b_id]['count'] += 1

            # Format state_map for frontend
            formatted_states = {}
            for st, st_data in state_map.items():
                formatted_states[st] = {
                    'count': st_data['count'],
                    'breakdown': sorted(st_data['breakdown'].values(), key=lambda x: x['count'], reverse=True)
                }

            aging_data[key] = {
                "total": len(bucket_samples),
                "states": formatted_states
            }
            
            _logger.info(f"Aging Bucket {key}: {len(bucket_samples)} samples (breakdown_type: {breakdown_type})")

        return aging_data


    @http.route(['/lerm/overview/data'], type='json', auth='user', methods=["POST"])
    def overview_data(self, **kw):
        """
        Fetches sample counts grouped by technician (hr.employee), filtered by date, discipline, lab, and company.
        Includes a nested 'product_breakdown' showing sample status counts per product.
        """
        # Extract parameters from **kw
        start_date = kw.get('start_date')
        end_date = kw.get('end_date')
        discipline = kw.get('discipline')
        lab_id = kw.get('lab_id')
        company_id = kw.get('company_id')

        Sample = request.env['lerm.srf.sample'].sudo()
        Employee = request.env['hr.employee'].sudo()
        
        _logger.info("Fetching technician overview with params: lab=%s, company=%s", lab_id, company_id)

        # 1. Build Sample Domain
        domain = []
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                domain += [
                    ('sample_received_date', '>=', start_dt),
                    ('sample_received_date', '<=', end_dt),
                ]
            except Exception:
                pass

        if discipline and discipline != "ALL":
            domain.append(('discipline_id.discipline', '=', discipline))
            
        if lab_id and lab_id != 'ALL':
            domain.append(('lab_location', '=', int(lab_id)))
            
        if company_id and company_id != 'ALL':
            domain.append(('lab_location.company_id', '=', int(company_id)))

        # 2. Fetch relevant samples
        samples = Sample.search(domain)
        _logger.info("Found %d samples for technician overview", len(samples))

        if not samples:
            return []

        # 3. Map samples to technicians (user_id)
        # A sample can have multiple technicians (via ELN technician_ids or parameters_result)
        tech_to_samples = defaultdict(lambda: Sample.browse())
        for s in samples:
            u_ids = set()
            if s.eln_id and s.eln_id.parameters_result:
                for param_res in s.eln_id.parameters_result:
                    if param_res.technician:
                        u_ids.add(param_res.technician.id)
            if s.technicians:
                u_ids.add(s.technicians.id)
            if s.eln_id:
                if s.eln_id.technician:
                    u_ids.add(s.eln_id.technician.id)
                if s.eln_id.technician_ids:
                    u_ids.update(s.eln_id.technician_ids.ids)
            
            for uid in u_ids:
                tech_to_samples[uid] += s
        
        if not tech_to_samples:
            _logger.warning("No technicians (from sample or ELN) assigned to the found samples")
            return []

        # 4. Fetch Employees associated with these technicians
        emp_domain = [('user_id', 'in', list(tech_to_samples.keys()))]
        
        employees = Employee.search(emp_domain)
        _logger.info("Found %d employees with matching user_ids", len(employees))

        data = []
        for emp in employees:
            assigned_samples = tech_to_samples[emp.user_id.id]
            
            # --- START: Product Breakdown Calculation ---
            product_breakdown_map = {}

            for sample in assigned_samples:
                product = sample.material_id
                
                if not product:
                    product_id = 0
                    product_name = "No Product"
                else:
                    product_id = product.id
                    product_name = product.display_name
                    
                if product_id not in product_breakdown_map:
                    product_breakdown_map[product_id] = {
                        'product_id': product_id,
                        'product_name': product_name,
                        'total_samples': 0,
                        'alloted': 0,
                        'pending_verification': 0,
                        'pending_approval': 0,
                        'in_report': 0,
                        'cancelled': 0,
                    }
                
                prod_data = product_breakdown_map[product_id]
                prod_data['total_samples'] += 1
                
                state = sample.state
                if state == '2-alloted':
                    prod_data['alloted'] += 1
                elif state == '3-pending_verification':
                    prod_data['pending_verification'] += 1
                elif state == '5-pending_approval':
                    prod_data['pending_approval'] += 1
                elif state == '4-in_report':
                    prod_data['in_report'] += 1
                elif state == '6-cancelled':
                    prod_data['cancelled'] += 1
            
            product_breakdown_list = sorted(
                list(product_breakdown_map.values()),
                key=lambda x: x['total_samples'],
                reverse=True
            )
            
            data.append({
                'technician_id': emp.user_id.id,
                'technician_name': emp.name,
                'total_samples': len(assigned_samples),
                'assignment_pending': len(assigned_samples.filtered(lambda s: s.state == '1-allotment_pending')),
                'alloted': len(assigned_samples.filtered(lambda s: s.state == '2-alloted')),
                'pending_verification': len(assigned_samples.filtered(lambda s: s.state == '3-pending_verification')),
                'pending_approval': len(assigned_samples.filtered(lambda s: s.state == '5-pending_approval')),
                'in_report': len(assigned_samples.filtered(lambda s: s.state == '4-in_report')),
                'cancelled': len(assigned_samples.filtered(lambda s: s.state == '6-cancelled')),
                'product_breakdown': product_breakdown_list,
            })
            
        data = sorted(data, key=lambda x: x['total_samples'], reverse=True)
            
        return data

    @http.route(['/dashboard/get_filter_options'], type='json', auth='user', methods=["POST"])
    def get_filter_options(self, **kw):
        """
        Fetches Labs and Companies for frontend filters.
        """
        Labs = request.env['lerm.lab.master'].sudo().search([])
        Companies = request.env['res.company'].sudo().search([])
        
        return {
            "labs": [{"id": lab.id, "name": lab.lab_name, "company_id": lab.company_id.id} for lab in Labs],
            "companies": [{"id": comp.id, "name": comp.name} for comp in Companies]
        }
    
    
    @http.route(['/lerm/customer/overview/data'], type='json', auth='user', methods=["POST"])
    def customer_overview_data(self, **kw):
        """
        Fetches sample counts grouped by customer and product, filtered by date, discipline, and search query.
        Returns the paginated customer list and the total customer count.
        """
        start_date = kw.get('start_date')
        end_date = kw.get('end_date')
        discipline = kw.get('discipline')
        lab_id = kw.get('lab_id')
        company_id = kw.get('company_id')
        search_query = kw.get('search_query', '').strip() 

        # NEW: Pagination parameters with safe defaults
        page_size = int(kw.get('page_size', 10))  
        page_number = int(kw.get('page_number', 1))

        Sample = request.env['lerm.srf.sample'].sudo()
        domain = []

        # 1. Date Filtering
        if start_date and end_date:
            try:
                # Ensure datetime is imported correctly and parsing is attempted
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                # Use end_dt + 1 day minus 1 second to cover the whole end day, if needed, but for date filtering, this is usually fine:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                domain += [
                    ('sample_received_date', '>=', start_dt.strftime('%Y-%m-%d')), # Use string format for standard date domain
                    ('sample_received_date', '<=', end_dt.strftime('%Y-%m-%d')),
                ]
            except ValueError:
                 # If date format is wrong, the server logs will show this.
                 pass

        if discipline and discipline != "ALL":
            domain.append(('discipline_id.discipline', '=', discipline))
            
        if lab_id and lab_id != 'ALL':
            domain.append(('lab_location', '=', int(lab_id)))
            
        if company_id and company_id != 'ALL':
            domain.append(('lab_location.company_id', '=', int(company_id)))

        # 3. Search Query Filtering (Customer Name)
        if search_query:
            domain.append(('customer_id.name', 'ilike', f'%{search_query}%'))


        # 4. Find all distinct customers within the current domain
        samples_in_period = Sample.search(domain)
        
        # Using a set to ensure unique customer records, including False (No Customer)
        customers = set(samples_in_period.mapped('customer_id'))

        data = []
        for customer in customers:
            # Safely handle the case where customer is False (no customer)
            customer_id = customer.id if customer else 0
            customer_name = customer.name if customer else "No Customer"
            
            if customer:
                customer_samples = samples_in_period.filtered(lambda s: s.customer_id.id == customer_id)
            else:
                customer_samples = samples_in_period.filtered(lambda s: not s.customer_id)
                
            if len(customer_samples) > 0:
                # --- Product-Wise Aggregation ---
                product_data = []
                products = set(customer_samples.mapped('material_id')) 
                
                # Sort products by name for consistency
                # Use a lambda that safely handles case where product record might not have a name for some reason
                products_list = sorted(list(products), key=lambda p: p.name or 'No Product') 
                
                for product in products_list:
                    product_id = product.id if product else 0
                    product_name = product.name if product else "General/No Product"
                    
                    if product:
                        product_samples = customer_samples.filtered(lambda s: s.material_id.id == product_id)
                    else:
                        product_samples = customer_samples.filtered(lambda s: not s.material_id)
                    
                    if len(product_samples) > 0:
                        product_data.append({
                            'product_id': product_id,
                            'product_name': product_name,
                            'total_samples': len(product_samples),
                            # Calculate statuses for the specific product
                            'assignment_pending': len(product_samples.filtered(lambda s: s.state == '1-allotment_pending')),
                            'alloted': len(product_samples.filtered(lambda s: s.state == '2-alloted')),
                            'pending_verification': len(product_samples.filtered(lambda s: s.state == '3-pending_verification')),
                            'pending_approval': len(product_samples.filtered(lambda s: s.state == '5-pending_approval')),
                            'in_report': len(product_samples.filtered(lambda s: s.state == '4-in_report')),
                            'cancelled': len(product_samples.filtered(lambda s: s.state == '6-cancelled')),
                            'invoiced': len(product_samples.filtered(lambda s: s.invoice_status == '2-invoiced')),
                            'uninvoiced': len(product_samples.filtered(lambda s: s.invoice_status == '1-uninvoiced')),
                        })

                data.append({
                    'customer_id': customer_id, 
                    'customer_name': customer_name, 
                    'total_samples': len(customer_samples),
                    'assignment_pending': len(customer_samples.filtered(lambda s: s.state == '1-allotment_pending')),
                    'alloted': len(customer_samples.filtered(lambda s: s.state == '2-alloted')),
                    'pending_verification': len(customer_samples.filtered(lambda s: s.state == '3-pending_verification')),
                    'pending_approval': len(customer_samples.filtered(lambda s: s.state == '5-pending_approval')),
                    'in_report': len(customer_samples.filtered(lambda s: s.state == '4-in_report')),
                    'cancelled': len(customer_samples.filtered(lambda s: s.state == '6-cancelled')),
                    'invoiced': len(customer_samples.filtered(lambda s: s.invoice_status == '2-invoiced')),
                    'uninvoiced': len(customer_samples.filtered(lambda s: s.invoice_status == '1-uninvoiced')),
                    'product_breakdown': product_data, # Nested product data
                })
        
        # 5. Add Sample Aging Overview (with Product Breakdown)
        aging_domain = [
            ('state', 'in', ['2-alloted', '7-calculated', '3-pending_verification', '5-pending_approval']),
            ('eln_id', '!=', False)
        ]
        if discipline and discipline != "ALL":
            aging_domain.append(('discipline_id.discipline', '=', discipline))
        if lab_id and lab_id != 'ALL':
            aging_domain.append(('lab_location', '=', int(lab_id)))
        if company_id and company_id != 'ALL':
            aging_domain.append(('lab_location.company_id', '=', int(company_id)))
        if search_query:
            # For customer dashboard, aging samples should also be filtered by the searched customer
            aging_domain.append(('customer_id.name', 'ilike', f'%{search_query}%'))
            
        aging_buckets = self._get_detailed_aging_data(Sample, aging_domain, breakdown_type='technician')

        # 6. Sort and Paginate
        data.sort(key=itemgetter('total_samples'), reverse=True)
        total_customers = len(data)
        offset = (page_number - 1) * page_size
        paginated_data = data[offset : offset + page_size]

        return {
            'customers': paginated_data,
            'total_customers': total_customers,
            'aging_data': aging_buckets
        }
        
    @http.route(['/lerm/product/overview/data'], type='json', auth='user', methods=["POST"])
    def product_overview_data(self, **kw):
        """
        Fetches sample counts grouped by product (material), filtered by date, discipline, and multi-field search query.
        Returns the paginated product list and the total product count.
        """
        start_date = kw.get('start_date')
        end_date = kw.get('end_date')
        discipline = kw.get('discipline')
        lab_id = kw.get('lab_id')
        company_id = kw.get('company_id')
        search_query = kw.get('search_query', '').strip()
        search_type = kw.get('search_type', 'all') # Options: all, product, srf, ulr, report

        # Pagination parameters
        page_size = int(kw.get('page_size', 10))
        page_number = int(kw.get('page_number', 1))

        Sample = request.env['lerm.srf.sample'].sudo()
        domain = []

        # 1. Date Filtering
        if start_date and end_date:
            try:
                domain += [
                    ('sample_received_date', '>=', start_date),
                    ('sample_received_date', '<=', end_date),
                ]
            except Exception:
                pass
        
        if lab_id and lab_id != 'ALL':
            domain.append(('lab_location', '=', int(lab_id)))
            
        if company_id and company_id != 'ALL':
            domain.append(('lab_location.company_id', '=', int(company_id)))

        # 2. Discipline Filtering
        if discipline and discipline != "ALL":
            domain.append(('discipline_id.discipline', '=', discipline))

        # 3. Search Query Filtering
        if search_query:
            search_domain = []
            if search_type in ['all', 'product']:
                search_domain.append(('material_id.name', 'ilike', f'%{search_query}%'))
            if search_type in ['all', 'srf']:
                search_domain.append(('srf_id.srf_id', 'ilike', f'%{search_query}%'))
            if search_type in ['all', 'ulr']:
                search_domain.append(('ulr_no', 'ilike', f'%{search_query}%'))
            if search_type in ['all', 'report']:
                search_domain.append(('kes_no', 'ilike', f'%{search_query}%'))
            
            if search_domain:
                if len(search_domain) > 1:
                    actual_search_domain = ['|'] * (len(search_domain) - 1) + search_domain
                else:
                    actual_search_domain = search_domain
                domain += actual_search_domain

        # 4. Fetch samples and group by material
        samples_in_period = Sample.search(domain)
        # Using mapped and set to ensure we only get unique materials
        materials = set(samples_in_period.mapped('material_id'))

        data = []
        for material in materials:
            material_id = material.id if material else 0
            material_name = material.name if material else "General / No Material"
            
            if material:
                material_samples = samples_in_period.filtered(lambda s: s.material_id.id == material_id)
            else:
                material_samples = samples_in_period.filtered(lambda s: not s.material_id)
            
            if len(material_samples) > 0:
                data.append({
                    'product_id': material_id,
                    'product_name': material_name,
                    'total_samples': len(material_samples),
                    'assignment_pending': len(material_samples.filtered(lambda s: s.state == '1-allotment_pending')),
                    'alloted': len(material_samples.filtered(lambda s: s.state == '2-alloted')),
                    'pending_verification': len(material_samples.filtered(lambda s: s.state == '3-pending_verification')),
                    'pending_approval': len(material_samples.filtered(lambda s: s.state == '5-pending_approval')),
                    'in_report': len(material_samples.filtered(lambda s: s.state == '4-in_report')),
                    'cancelled': len(material_samples.filtered(lambda s: s.state == '6-cancelled')),
                    'invoiced': len(material_samples.filtered(lambda s: s.invoice_status == '2-invoiced')),
                    'uninvoiced': len(material_samples.filtered(lambda s: s.invoice_status == '1-uninvoiced')),
                })

        # 5. Add Sample Aging Overview (with Product Breakdown)
        # Use the same base domain logic from above (Date, Discipline, Search)
        # But filter for specific aging states as per requirement
        aging_domain = [
            ('state', 'in', ['2-alloted', '7-calculated', '3-pending_verification', '5-pending_approval']),
            ('eln_id', '!=', False)
        ]
        # Include current search filters if they match sample fields
        if discipline and discipline != "ALL":
            aging_domain.append(('discipline_id.discipline', '=', discipline))
            
        if lab_id and lab_id != 'ALL':
            aging_domain.append(('lab_location', '=', int(lab_id)))
            
        if company_id and company_id != 'ALL':
            aging_domain.append(('lab_location.company_id', '=', int(company_id)))
        
        # Apply name filter if it exists
        if search_query:
            if search_type in ['all', 'product']:
                aging_domain.append(('material_id.name', 'ilike', f'%{search_query}%'))

        aging_buckets = self._get_detailed_aging_data(Sample, aging_domain, breakdown_type='product')

        # 6. Sort the complete data set (Descending by total_samples)
        data.sort(key=itemgetter('total_samples'), reverse=True)

        # 7. Apply Pagination
        total_products = len(data)
        offset = (page_number - 1) * page_size
        paginated_data = data[offset : offset + page_size]

        return {
            'products': paginated_data,
            'total_products': total_products,
            'aging_data': aging_buckets
        }

