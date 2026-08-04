from odoo import http, fields
from odoo.http import request
from datetime import date


AGEING_BUCKETS = [
    {"key": "0-30", "label": "0-30 Days", "min": 0, "max": 30, "color": "#10B981"},
    {"key": "31-60", "label": "31-60 Days", "min": 31, "max": 60, "color": "#F59E0B"},
    {"key": "61-90", "label": "61-90 Days", "min": 61, "max": 90, "color": "#F97316"},
    {"key": "90+", "label": "90+ Days", "min": 91, "max": 99999, "color": "#EF4444"},
]


def _compute_bucket(days_overdue):
    for b in AGEING_BUCKETS:
        if b["min"] <= days_overdue <= b["max"]:
            return b["key"]
    return "90+"


def _bucket_amounts(invoices, as_of):
    buckets = {b["key"]: 0.0 for b in AGEING_BUCKETS}
    for inv in invoices:
        due = inv.invoice_date_due or inv.invoice_date
        days = (as_of - due).days if due else 0
        key = _compute_bucket(max(days, 0))
        buckets[key] += inv.amount_residual_signed or 0.0
    return buckets


class CustomerAgeingDashboard(http.Controller):

    def _get_salesperson_users(self):
        group = request.env.ref(
            "customer_ageing_dashboard.group_accounts_saleperson_ageing",
            raise_if_not_found=False,
        )
        if group and group.users:
            return group.users
        Invoice = request.env["account.move"].sudo()
        invoice_users = Invoice.search_read(
            [("move_type", "in", ["out_invoice", "out_refund"]), ("state", "=", "posted")],
            ["invoice_user_id"],
            order="invoice_user_id",
        )
        user_ids = set()
        for inv in invoice_users:
            uid = inv["invoice_user_id"]
            if uid:
                user_ids.add(uid[0] if isinstance(uid, (list, tuple)) else uid)
        return request.env["res.users"].browse(list(user_ids)) if user_ids else request.env["res.users"]

    def _resolve_salesperson_ids(self, payload_ids=None):
        user = request.env.user
        group = request.env.ref(
            "customer_ageing_dashboard.group_accounts_saleperson_ageing",
            raise_if_not_found=False,
        )
        if group and user in group.users:
            return [user.id]
        if payload_ids is not None:
            return payload_ids
        return self._get_salesperson_users().ids

    def _build_customer_domain(self, salesperson_ids):
        domain = [("lerm_customer", "=", True)]
        if salesperson_ids is None:
            return domain
        filtered = [s for s in salesperson_ids if s != "unassigned"]
        has_unassigned = "unassigned" in (salesperson_ids or [])
        if not salesperson_ids:
            domain.append(("id", "=", False))
        elif filtered and has_unassigned:
            domain = ["|", ("user_id", "in", filtered), ("user_id", "=", False)] + domain
        elif filtered:
            domain.append(("user_id", "in", filtered))
        elif has_unassigned:
            domain.append(("user_id", "=", False))
        return domain

    def _build_invoice_domain(self, salesperson_ids):
        domain = [
            ("move_type", "in", ["out_invoice", "out_refund"]),
            ("state", "=", "posted"),
            ("payment_state", "not in", ["paid", "reversed", "in_payment"]),
        ]
        if salesperson_ids is None:
            return domain
        filtered = [s for s in salesperson_ids if s != "unassigned"]
        has_unassigned = "unassigned" in (salesperson_ids or [])
        if not salesperson_ids:
            domain.append(("id", "=", False))
        elif filtered and has_unassigned:
            domain = ["|", ("invoice_user_id", "in", filtered), ("invoice_user_id", "=", False)] + domain
        elif filtered:
            domain.append(("invoice_user_id", "in", filtered))
        elif has_unassigned:
            domain.append(("invoice_user_id", "=", False))
        return domain

    @http.route(
        "/customer_ageing/salespersons", type="json", auth="user", methods=["POST"]
    )
    def get_salespersons(self):
        user = request.env.user
        group = request.env.ref(
            "customer_ageing_dashboard.group_accounts_saleperson_ageing",
            raise_if_not_found=False,
        )
        if group and user in group.users:
            result = [{"id": user.id, "name": user.name}]
        else:
            users = self._get_salesperson_users()
            result = [{"id": u.id, "name": u.name} for u in users]
            result.append({"id": "unassigned", "name": "Unassigned"})
        return result

    @http.route(
        "/customer_ageing/metrics", type="json", auth="user", methods=["POST"]
    )
    def get_metrics(self, **kw):
        salesperson_ids = kw.get("salesperson_ids")
        as_of_str = kw.get("as_of")
        as_of = (
            fields.Date.to_date(as_of_str) if as_of_str else fields.Date.today()
        )

        resolved_ids = self._resolve_salesperson_ids(salesperson_ids)
        Partner = request.env["res.partner"].sudo()
        Invoice = request.env["account.move"].sudo()

        partner_domain = self._build_customer_domain(resolved_ids)
        total_customers = Partner.search_count(partner_domain)

        inv_domain = self._build_invoice_domain(resolved_ids)
        invoices = Invoice.search(inv_domain)
        buckets = _bucket_amounts(invoices, as_of)

        total_outstanding = sum(buckets.values())
        overdue_customers = (
            Partner.search(partner_domain + [("id", "in", invoices.mapped("partner_id").ids)]).ids
        )

        return {
            "total_outstanding": total_outstanding,
            "total_customers": total_customers,
            "overdue_customers": len(overdue_customers),
            "total_invoices": len(invoices),
            "buckets": buckets,
            "as_of": fields.Date.to_string(as_of),
        }

    @http.route(
        "/customer_ageing/customers", type="json", auth="user", methods=["POST"]
    )
    def get_customers(self, **kw):
        salesperson_ids = kw.get("salesperson_ids")
        as_of_str = kw.get("as_of")
        as_of = (
            fields.Date.to_date(as_of_str) if as_of_str else fields.Date.today()
        )
        limit = int(kw.get("limit", 50))
        page = int(kw.get("page", 1))
        search = kw.get("search", "").strip()

        resolved_ids = self._resolve_salesperson_ids(salesperson_ids)
        Partner = request.env["res.partner"].sudo()
        Invoice = request.env["account.move"].sudo()

        partner_domain = self._build_customer_domain(resolved_ids)
        if search:
            partner_domain.append(("name", "ilike", f"%{search}%"))
        total_count = Partner.search_count(partner_domain)
        partners = Partner.search(
            partner_domain, offset=(page - 1) * limit, limit=limit, order="name"
        )

        inv_domain_base = self._build_invoice_domain(resolved_ids)

        rows = []
        grand_buckets = {b["key"]: 0.0 for b in AGEING_BUCKETS}
        grand_outstanding = 0.0
        grand_invoices = 0

        for partner in partners:
            p_invoices = Invoice.search(
                inv_domain_base + [("partner_id", "=", partner.id)]
            )
            p_buckets = _bucket_amounts(p_invoices, as_of)
            p_total = sum(p_buckets.values())
            for k in grand_buckets:
                grand_buckets[k] += p_buckets[k]
            grand_outstanding += p_total
            grand_invoices += len(p_invoices)

            rows.append(
                {
                    "partner_id": partner.id,
                    "partner_name": partner.name,
                    "buckets": p_buckets,
                    "total_outstanding": p_total,
                    "invoice_count": len(p_invoices),
                }
            )

        return {
            "rows": rows,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "totals": {
                "buckets": grand_buckets,
                "total_outstanding": grand_outstanding,
                "invoice_count": grand_invoices,
            },
        }

    @http.route(
        "/customer_ageing/detail_invoices",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def get_detail_invoices(self, **kw):
        salesperson_ids = kw.get("salesperson_ids")
        as_of_str = kw.get("as_of")
        partner_id = kw.get("partner_id")
        bucket_key = kw.get("bucket_key")
        as_of = (
            fields.Date.to_date(as_of_str) if as_of_str else fields.Date.today()
        )
        Invoice = request.env["account.move"].sudo()
        Partner = request.env["res.partner"].sudo()
        inv_domain = self._build_invoice_domain(None if partner_id else salesperson_ids)
        if partner_id:
            inv_domain.append(("partner_id", "=", partner_id))
            partner = Partner.browse(partner_id)
            partner_name = partner.name if partner else ""
        else:
            partner_name = "All Customers"
        all_invoices = Invoice.search(inv_domain, order="invoice_date_due ASC")
        matched = []
        for inv in all_invoices:
            due = inv.invoice_date_due or inv.invoice_date
            days = (as_of - due).days if due else 0
            days_overdue = max(days, 0)
            inv_bucket = _compute_bucket(days_overdue)
            if bucket_key and inv_bucket != bucket_key:
                continue
            matched.append({
                "id": inv.id,
                "invoice_date": fields.Date.to_string(inv.invoice_date) if inv.invoice_date else "",
                "due_date": fields.Date.to_string(inv.invoice_date_due) if inv.invoice_date_due else "",
                "invoice_number": inv.name or "",
                "original_amount": inv.amount_total_signed or 0.0,
                "outstanding_balance": inv.amount_residual_signed or 0.0,
                "aging_days": days_overdue,
                "aging_bucket": inv_bucket,
            })
        total_amount = sum(inv["outstanding_balance"] for inv in matched)
        avg_aging_days = 0
        highest_bucket = ""
        highest_invoice = ""
        if matched:
            avg_aging_days = round(sum(inv["aging_days"] for inv in matched) / len(matched))
            bucket_order = {"0-30": 0, "31-60": 1, "61-90": 2, "90+": 3}
            highest = max(matched, key=lambda i: (bucket_order.get(i["aging_bucket"], -1), i["outstanding_balance"]))
            highest_bucket = highest["aging_bucket"]
            highest_invoice = highest["invoice_number"]

        return {
            "invoices": matched,
            "total": total_amount,
            "invoice_count": len(matched),
            "partner_name": partner_name,
            "avg_aging_days": avg_aging_days,
            "highest_bucket": highest_bucket,
            "highest_invoice": highest_invoice,
        }
