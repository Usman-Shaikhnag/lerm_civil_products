# -*- coding: utf-8 -*-
{
    'name': 'LERM Accountant',
    'summary': 'Accountant-specific sample views under Accounting app',
    'author': 'Usman Shaikhnag and Khan Afzal',
    'website': 'http://www.esehat.org',
    'category': 'Lerm Civil',
    'version': '1.0.1',
    'depends': [
        'base',
        'lerm_civil',
        'lerm_civil_inv',
        'account',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sample_views.xml',
        'views/menu_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
