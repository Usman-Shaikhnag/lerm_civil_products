from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from collections import defaultdict


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

        days_range = (end_dt - start_dt).days
        period_counter = defaultdict(int)

        for sample in samples:
            date = sample.sample_received_date
            if not date:
                continue

            if days_range <= 30:
                # group by day instead of week
                key = date.strftime("%d-%b")  # e.g. 19-Aug
            else:
                # group by month
                key = date.strftime("%b %Y")  # e.g. Aug 2025

            period_counter[key] += 1

        # Ensure labels are sorted in chronological order
        labels = sorted(period_counter.keys(), key=lambda x: datetime.strptime(x, "%d-%b") if days_range <= 30 else datetime.strptime(x, "%b %Y"))
        counts = [period_counter[l] for l in labels]

        return {
            "labels": labels,
            "counts": counts,
            "total_count": len(samples),
        }
