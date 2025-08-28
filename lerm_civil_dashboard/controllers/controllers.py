# controller
from odoo import http
from odoo.http import request
from datetime import datetime
from collections import defaultdict, Counter

class LermCivilDashboard(http.Controller):

    @http.route(['/dashboard/getdata'], type="json", auth="user", methods=["POST"])
    def get_dashboard_data(self, **kw):
        start_date = kw.get('start_date')
        end_date = kw.get('end_date')

        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except Exception:
            return {"error": "Invalid date format"}

        domain = [
            ('sample_received_date', '>=', start_dt),
            ('sample_received_date', '<=', end_dt),
        ]
        samples = request.env['lerm.srf.sample'].sudo().search(domain)

        # --- Time-based grouping (existing) ---
        days_range = (end_dt - start_dt).days
        period_counter = defaultdict(int)

        for sample in samples:
            date = sample.sample_received_date
            if not date:
                continue

            if days_range <= 30:
                key = date.strftime("%d-%b")
            else:
                key = date.strftime("%b %Y")

            period_counter[key] += 1

        labels = sorted(
            period_counter.keys(),
            key=lambda x: datetime.strptime(x, "%d-%b") if days_range <= 30 else datetime.strptime(x, "%b %Y")
        )
        counts = [period_counter[l] for l in labels]
        # full list of states with labels
        ALL_STATES = {
            "1-allotment_pending": "Allotment Pending",
            "2-alloted": "Alloted",
            "3-pending_verification": "Pending Verification",
            "4-in_report": "In Report",
            "5-pending_approval": "Pending Approval",
        }
        # --- NEW: state-based grouping ---
        state_counter = Counter(samples.mapped("state"))

        state_labels = list(state_counter.keys())
        state_counts = list(state_counter.values())

        state_data = []
        for state, label in ALL_STATES.items():
            state_data.append({
                "state": state,
                "state_label": label,
                "count": state_counter.get(state, 0),
            })
        return {
            "labels": labels,
            "counts": counts,
            "total_count": len(samples),
            "state_labels": state_labels,
            "state_data":state_data,
            "state_counts": state_counts,
            "total_states": len(state_labels),
        }
