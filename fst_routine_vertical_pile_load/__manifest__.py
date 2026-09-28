# -*- coding: utf-8 -*-
{
    'name': 'Routine Vertical Pile Load',
    'version': '1.0',
    'category': 'Lerm Civil',
    'summary': 'Routine Vertical Pile Load Test (FST)',
    'depends': ['base', 'lerm_civil', 'fst'],
    'data': [
        'security/ir.model.access.csv',
        'views/fst_routine_vertical_load_test_views.xml',
        'reports/routine_vertical_load_layout.xml',
        'reports/routine_vertical_load_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
