# controller
from odoo import http
from odoo.http import request
from datetime import datetime
from collections import defaultdict, Counter

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
        This data is used for the Technician Kanban/Card view on the dashboard.
        """
        # Extract parameters from **kw
        start_date = kw.get('start_date')
        end_date = kw.get('end_date')
        discipline = kw.get('discipline')

        Sample = request.env['lerm.srf.sample'].sudo()
        # Ensure the group is found, or gracefully handle if not (e.g., in testing/non-standard setups)
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
                # Log or handle date parsing error if necessary
                pass

        # 2. Discipline Filtering
        if discipline and discipline != "ALL":
            domain.append(('discipline_id.discipline', '=', discipline))


        data = []
        for user in users:
            # Filter samples assigned to the technician AND within the date/discipline range
            # Note: Assuming 'technicians' is the M2M field for technicians on the sample model
            user_domain = [('technicians', '=', user.id)] + domain
            samples = Sample.search(user_domain)
            
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
            })
            
        return data