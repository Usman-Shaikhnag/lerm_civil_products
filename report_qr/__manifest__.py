{
    "name": "Report QR Generator",
    'summary': """Report QR Generator""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Esehat",
    "version": "17.0.1.0.0",
    "category":"Lerm Civil",
    "depends": ["web","base","lerm_civil" ,'contacts','product'],
    "data": [
        "security/ir.model.access.csv",
        "views/lab_report_wizard_views.xml",
        "views/lab_report_views.xml",
        "views/menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            'https://cdn.jsdelivr.net/npm/chart.js',
            'report_qr/static/src/css/index.css',
        ],
    },
}
