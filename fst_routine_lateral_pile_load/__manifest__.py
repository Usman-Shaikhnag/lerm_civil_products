# -*- coding: utf-8 -*-
{
    'name': 'FST Routine Lateral Pile Load Test',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Routine Lateral Pile Load Test (FST)',
    'depends': ['base', 'lerm_civil', 'fst'],
    'data': [
        'security/ir.model.access.csv',
        'views/routine_lateral_pile_load_views.xml',
        'reports/routine_lateral_pile_load_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
