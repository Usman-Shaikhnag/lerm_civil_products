# -*- coding: utf-8 -*-
{
    'name': 'FST Routine Vertical Pile Load Test',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Routine Vertical Pile Load Test (FST)',
    'depends': ['base', 'lerm_civil', 'fst'],
    'data': [
        'security/ir.model.access.csv',
        'views/routine_pile_load_test_views.xml',
        'reports/routine_pile_load_test_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
