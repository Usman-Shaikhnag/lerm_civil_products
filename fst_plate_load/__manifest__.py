# -*- coding: utf-8 -*-
{
    'name': 'FST Plate Load Test',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Plate Load Test (FST Dashboard)',
    'depends': ['base', 'lerm_civil', 'fst'],
    'data': [
        'security/ir.model.access.csv',
        'views/plate_load_test_views.xml',
        'reports/plate_load_test_template.xml',
    ],
    'installable': True,
    'auto_install': False,
}
