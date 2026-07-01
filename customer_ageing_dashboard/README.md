# Customer Ageing Dashboard

Accounts receivable ageing analysis dashboard for LERM testing laboratory. Provides real-time visibility into outstanding invoice amounts bucketed by overdue periods, with drill-down to invoice-level detail per customer.

## Features

- **Ageing Buckets** — Outstanding invoices grouped into 0–30, 31–60, 61–90, and 90+ days overdue
- **Salesperson Filter** — View data filtered by salesperson; restricted salespersons see only their own invoices
- **Customer Grid** — Paginated table with per-customer bucket totals and total outstanding
- **Drill-Down** — Click any customer name or bucket value to see the underlying invoices with ageing details
- **KPI Summary** — Total outstanding, invoice count, active customer count, and overdue customer count at a glance
- **Export** — Detail report supports CSV/Excel export and print-to-PDF
- **Risk Insights** — Detail report highlights high-risk buckets, oldest invoices, and average ageing

## Dependencies

- `account` — Invoices and payment state
- `lerm_civil` — LERM base module (provides access category)
- `lerm_civil_inv` — LERM invoice customisations
- `sales_team` — Salesperson/user assignment on invoices

## Installation

1. Place the module in your Odoo addons directory.
2. Update the app list and install **Customer Ageing Dashboard**.
3. Grant the **Ageing Dashboard** group to users who should access the menu.
4. Optionally, assign the **Salesperson (Ageing)** group to restrict sales users to only their own invoices.

## Usage

### Main Dashboard

The dashboard opens from the top menu: **Customer Ageing Dashboard > Ageing Dashboard**.

1. **Salesperson filter** (top-left) — Select one or more salespeople. If you belong to the *Salesperson (Ageing)* group, only your own data is shown and the filter is hidden.
2. **As-of date** (top-right) — Set the date used for ageing calculation.
3. **Metric cards** — Total outstanding, total customers, overdue customers, total invoices.
4. **Bucket cards** — Click a bucket to drill down into invoices for that ageing range across all customers.
5. **Customer grid** — Shows each customer, their outstanding per bucket, and total. Click a customer name or a bucket value to drill down.

### Detail Report

The detail report shows all invoices for a selected customer/bucket combination.

- **KPI bar** — Total outstanding, invoice count, average ageing days, highest bucket.
- **Ageing distribution** — Horizontal bar chart showing amount per bucket. Click a bar to filter the invoice table.
- **Invoice table** — Lists individual invoices with dates, amounts, ageing days, and bucket. Click an invoice number to open it.
- **Customer sidebar** — Summary info and as-of date.
- **Risk insights** — Automated warnings for high-overdue percentages and other indicators.
- **Export** — *Excel* button downloads a CSV; *PDF* triggers browser print.

## Security Groups

| Group | Technical Name | Purpose |
|-------|----------------|---------|
| Ageing Dashboard | `group_ageing_dashboard` | Grants access to the dashboard menu |
| Salesperson (Ageing) | `group_accounts_saleperson_ageing` | Restricts to own invoices only |

## API Endpoints

All endpoints accept `POST` with JSON content type and require authentication.

### `/customer_ageing/metrics`

Returns aggregate ageing metrics.

**Payload:**
```json
{
  "as_of": "2025-01-15",
  "salesperson_ids": [1, 2]
}
```

### `/customer_ageing/customers`

Returns paginated customer rows with per-bucket totals.

**Payload:**
```json
{
  "as_of": "2025-01-15",
  "salesperson_ids": [1, 2],
  "limit": 50,
  "page": 1,
  "search": "Acme"
}
```

### `/customer_ageing/detail_invoices`

Returns invoice-level detail for a customer/bucket filter.

**Payload:**
```json
{
  "as_of": "2025-01-15",
  "partner_id": 42,
  "bucket_key": "90+",
  "salesperson_ids": [1, 2]
}
```

All salesperson parameters are optional. When omitted, all salespeople are included.

## Development

Built with Odoo 17 Owl components (JS framework). Styles in `static/src/css/ageing_dashboard.css`. After changing assets, run with `--dev all` and hard-refresh the browser.
