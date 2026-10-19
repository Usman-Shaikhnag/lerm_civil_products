# -*- coding: utf-8 -*-
{
    'name': 'Uplift Load Test',
    'version': '1.0',
    'category': 'Lerm Civil',
    'summary': 'Uplift (Pull-out) Pile Load Test (FST)',
    'depends': ['base', 'lerm_civil', 'fst'],
    'data': [
        'security/ir.model.access.csv',
        'views/fst_uplift_load_test_views.xml',
        'reports/uplift_load_layout.xml',
        'reports/uplift_load_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
