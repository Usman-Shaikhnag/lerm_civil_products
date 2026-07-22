# -*- coding: utf-8 -*-
{
    'name': 'FST Vertical Pile Load Test',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Initial Vertical Pile Load Test (FST)',
    'depends': ['base', 'lerm_civil', 'fst'],
    'data': [
        'security/ir.model.access.csv',
        'views/pile_load_test.xml',
        'reports/vertical_pile_load_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
