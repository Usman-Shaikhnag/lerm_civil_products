{
    'name': 'FST Lateral Pile Load',
    'version': '1.5',
    'category': 'Lerm Civil',
    'summary': 'Initial Lateral Pile Load Test',
    'depends': ['base', 'lerm_civil', 'fst'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/excel_upload_wizard.xml',
        'views/fst_lateral_pile_load_views.xml',
        'reports/lateral_pile_load_layout.xml',
        'reports/lateral_pile_load_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
