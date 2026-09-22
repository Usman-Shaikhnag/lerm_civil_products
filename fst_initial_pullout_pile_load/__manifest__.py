# -*- coding: utf-8 -*-
{
    'name': 'FST Initial Pull-Out Pile Load Test',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Initial Pull-Out Pile Load Test (FST)',
    'depends': ['base', 'lerm_civil', 'fst'],
    'data': [
        'security/ir.model.access.csv',
        'views/initial_pullout_pile_load_views.xml',
        'reports/initial_pullout_pile_load_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
