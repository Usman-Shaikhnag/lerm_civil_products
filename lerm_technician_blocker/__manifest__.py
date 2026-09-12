{
    'name': 'LERM Technician New Work Blocker',
    'version': '17.0.1.0.0',
    'summary': 'Shows technicians a periodic popup of newly assigned work',
    'description': """
        Products (materials) carry an ownership field listing the technicians
        responsible for them. Once a confirmed sample of an owned material is
        alloted/in-test, it becomes pending work for its owner-technicians.

        At configurable daily windows (default 13:00, 15:00, 18:00) a server
        cron consolidates each technician's NEW work - samples that have never
        been notified to that technician - into a digest. Each job is notified
        once and never re-shown in a regular digest. The popup is delivered to
        online technicians shortly after the window and to offline technicians
        on their next login (cancelable digest popup).
    """,
    'author': 'Esehat',
    'category': 'Lerm Civil',
    'depends': ['base', 'web', 'lerm_civil'],
    'data': [
        'data/cron.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/product_template.xml',
        'views/res_config_settings.xml',
        'views/digest_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'lerm_technician_blocker/static/src/js/technician_block_dialog.js',
            'lerm_technician_blocker/static/src/js/technician_blocker.js',
            'lerm_technician_blocker/static/src/js/technician_block_dialog.xml',
        ],
    },
    'installable': True,
    'application': False,
}
