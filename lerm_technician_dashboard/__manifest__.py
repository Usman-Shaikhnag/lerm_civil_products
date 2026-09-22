{
    "name": "Lerm Technician Dashboard",
    'summary': """Personal daily work dashboard for lab technicians""",
    'description': """
        Per-user dashboard showing a technician's overdue / due-today / in-progress /
        completed samples, their day plan, next action, work waiting on others and a
        filterable list of their own samples.
    """,
    'author': "Esehat",
    "version": "17.0.1.0.0",
    "category": "Lerm Civil",
    "depends": ["web", "base", "lerm_civil"],
    "data": [
        "views/technician_dashboard.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "lerm_technician_dashboard/static/src/components/technician_dashboard/technician_dashboard.js",
            "lerm_technician_dashboard/static/src/components/technician_dashboard/technician_dashboard.xml",
            'lerm_technician_dashboard/static/src/css/technician_dashboard.css',
        ],
    },
}
