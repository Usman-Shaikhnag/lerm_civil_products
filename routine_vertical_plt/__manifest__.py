# -*- coding: utf-8 -*-
{
    'name': 'Routine Vertical Pile Load Test',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Routine Vertical Pile Load Test with T1L, T1U, and F1 analysis per IS 2911',
    'depends': ['base', 'lerm_civil'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/routine_vplt_views.xml',
    ],
    'tests': ['tests/'],
    'installable': True,
    'auto_install': False,
}
