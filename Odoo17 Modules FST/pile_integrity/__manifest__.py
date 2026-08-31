{
    'name': 'Pile Integrity Test',
    'version': '17.0.1.0.0',
    'category': 'Testing',
    'summary': 'Low Strain Pile Integrity Test (PIT)',
    'description': """\
Low Strain Pile Integrity Test management for civil engineering laboratories.
- Pile integrity report sections (introduction, methodology, interpretation, etc.)
- Pile integrity test results table
- Site photographs and contents/TOC
- QWeb PDF report
""",
    'license': 'LGPL-3',
    'author': 'FST',
    'website': 'https://www.knackengineeringservices.com',
    'depends': ['base', 'web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/pile_integrity_views.xml',
        'reports/pile_integrity_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
