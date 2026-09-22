{
    'name': 'FST Lateral Pile Load',
    'version': '17.0.1.0.0',
    'category': 'Testing',
    'summary': 'Initial Lateral Pile Load Test',
    'description': """\
Lateral Pile Load Test management for civil engineering laboratories.
- Record loading/unloading readings
- Automatic settlement summary computation
- Load-displacement graph generation
- QWeb PDF report and datasheet
- Excel bulk upload of readings
""",
    'license': 'LGPL-3',
    'author': 'FST',
    'website': 'https://www.knackengineeringservices.com',
    'depends': ['base', 'web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'wizards/excel_upload_wizard.xml',
        'views/fst_lateral_pile_load_views.xml',
        'reports/lateral_pile_load_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
