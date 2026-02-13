# controller
from odoo import http
from odoo.http import request
from datetime import datetime
from collections import defaultdict, Counter
from operator import itemgetter # Required for sorting

class LermCivilDashboard(http.Controller):

    @http.route(['/dashboard/getdata'], type="json", auth="user", methods=["POST"])
    def get_dashboard_data(self, **kw):
        """
        Fetches data for the charts and KPIs, filtered by date and discipline.
        """
        # Extract parameters from **kw
        start_date = kw.get('start_date')
        end_date = kw.get('end_date')
        discipline = kw.get('discipline')
        
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
            "1-allotment_pending": "Allotment Pending",
            "2-alloted": "Alloted",
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

        return {
            "labels": labels,
            "counts": counts,
            "total_count": len(samples),
            "state_labels": state_labels, 
            "state_data": state_data,
            "state_counts": state_counts,
            "total_states": len(state_labels),
        }

    @http.route(['/lerm/overview/data'], type='json', auth='user', methods=["POST"])
    def overview_data(self, **kw):
        """
        Fetches sample counts grouped by technician, filtered by date and discipline.
        Includes a nested 'product_breakdown' showing sample status counts per product.
        """
        # Extract parameters from **kw
        start_date = kw.get('start_date')
        end_date = kw.get('end_date')
        discipline = kw.get('discipline')

        Sample = request.env['lerm.srf.sample'].sudo()
        
        # NOTE: Assuming 'lerm_civil.kes_technician_access_group' is the correct group XML ID
        tech_group = request.env.ref('lerm_civil.kes_technician_access_group', raise_if_not_found=False)
        users = request.env['res.users'].sudo().search([('groups_id', 'in', tech_group.id)])

        domain = []

        # 1. Date Filtering
        if start_date and end_date:
            try:
                # Convert date strings to datetime objects for filtering
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                domain += [
                    ('sample_received_date', '>=', start_dt),
                    ('sample_received_date', '<=', end_dt),
                ]
            except Exception:
                pass

        # 2. Discipline Filtering
        if discipline and discipline != "ALL":
            domain.append(('discipline_id.discipline', '=', discipline))


        data = []
        for user in users:
            # Filter samples assigned to the technician AND within the date/discipline range
            user_domain = [('technicians', '=', user.id)] + domain
            samples = Sample.search(user_domain)
            
            # --- START: Product Breakdown Calculation ---
            product_breakdown_map = {}

            for sample in samples:
                product = sample.material_id
                
                # Determine ID and Name for the product (Handle 'No Product' case)
                if not product:
                    product_id = 0
                    product_name = "No Product"
                else:
                    product_id = product.id
                    product_name = product.display_name
                    
                # Initialize the product entry if it doesn't exist
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
                
                # Update counts for the specific product
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
            
            # Convert map values to a list and sort by total samples (descending)
            product_breakdown_list = sorted(
                list(product_breakdown_map.values()),
                key=lambda x: x['total_samples'],
                reverse=True
            )
            # --- END: Product Breakdown Calculation ---
            
            
            data.append({
                'technician_id': user.id,
                'technician_name': user.name,
                'total_samples': len(samples),
                'assignment_pending': len(samples.filtered(lambda s: s.state == '1-allotment_pending')),
                'alloted': len(samples.filtered(lambda s: s.state == '2-alloted')),
                'pending_verification': len(samples.filtered(lambda s: s.state == '3-pending_verification')),
                'pending_approval': len(samples.filtered(lambda s: s.state == '5-pending_approval')),
                'in_report': len(samples.filtered(lambda s: s.state == '4-in_report')),
                'cancelled': len(samples.filtered(lambda s: s.state == '6-cancelled')),
                
                # NEW: Include the calculated product breakdown
                'product_breakdown': product_breakdown_list,
            })
            
        # Optional: Sort the main list by total samples as well
        data = sorted(data, key=lambda x: x['total_samples'], reverse=True)
            
        return data
    
    
    @http.route(['/lerm/customer/overview/data'], type='json', auth='user', methods=["POST"])
    def customer_overview_data(self, **kw):
        """
        Fetches sample counts grouped by customer and product, filtered by date, discipline, and search query.
        Returns the paginated customer list and the total customer count.
        """
        start_date = kw.get('start_date')
        end_date = kw.get('end_date')
        discipline = kw.get('discipline')
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
            except Exception as e:
                 # Catch other potential errors, but logging is essential here
                 request.env.cr.execute("ROLLBACK") # Defensive rollback in case of issues
                 pass


        # 2. Discipline Filtering
        if discipline and discipline != "ALL":
            domain.append(('discipline_id.discipline', '=', discipline))

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
                    'product_breakdown': product_data, # Nested product data
                })
        
        # 5. Sort the complete data set (Descending by total_samples)
        data.sort(key=itemgetter('total_samples'), reverse=True)

        # 6. Apply Pagination
        total_customers = len(data)
        
        # Calculate offset
        offset = (page_number - 1) * page_size
        
        # Apply limit and offset to slice the data
        paginated_data = data[offset : offset + page_size]
        
        return {
            'customers': paginated_data,
            'total_customers': total_customers
        }

