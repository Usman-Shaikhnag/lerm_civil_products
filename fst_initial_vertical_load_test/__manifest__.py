# -*- coding: utf-8 -*-
{
    'name': 'FST Initial Vertical Load Test',
    'version': '1.0',
    'category': 'Lerm Civil',
    'summary': 'Initial Vertical Pile Load Test (FST)',
    'depends': ['base', 'lerm_civil', 'fst'],
    'data': [
        'security/ir.model.access.csv',
        'views/fst_initial_vertical_load_test_views.xml',
        'reports/initial_vertical_load_layout.xml',
        'reports/initial_vertical_load_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
