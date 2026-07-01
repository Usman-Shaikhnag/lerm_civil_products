{
    "name": "Customer Ageing Dashboard",
    "summary": "Accounts receivable ageing analysis dashboard for LERM testing laboratory",
    "description": "Customer Ageing Dashboard provides real-time visibility into outstanding invoice amounts bucketed by overdue periods (0-30, 31-60, 61-90, 90+ days), with drill-down to invoices per customer, filterable by salesperson. Supports side-drawer drill-down from any aging bucket value, including vendor totals and grand totals.",
    "author": "Esehat",
    "version": "17.0.2.0.0",
    "category": "Lerm Civil",
    "depends": ["base", "web", "account", "lerm_civil", "lerm_civil_inv", "sales_team"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/dashboard.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "customer_ageing_dashboard/static/src/components/**/*.js",
            "customer_ageing_dashboard/static/src/components/**/*.xml",
            "customer_ageing_dashboard/static/src/css/ageing_dashboard.css",
        ],
    },
    "license": "LGPL-3",
}
