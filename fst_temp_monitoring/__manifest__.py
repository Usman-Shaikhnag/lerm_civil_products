{
    'name': 'FST Temp Monitoring',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Temp Monitoring',
    'depends': ['base', 'lerm_civil', 'fst'],
    'data': [
        'security/ir.model.access.csv',
        'views/temp_monitoring.xml',
    ],
    'installable': True,
    'auto_install': False,
}
