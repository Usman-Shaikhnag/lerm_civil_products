# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Bentonite',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Bentonite Material Testing',
    'description': """
This module contains the testing workflow for Bentonite material.
    """,
    'depends': ['base', 'sale', 'lerm_civil'],
    'data': [
        'security/ir.model.access.csv',
        'views/bentonite.xml',
        'reports/bentonite_datasheet.xml',
        'reports/bentonite_report.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'bentonite/static/src/css/custom_style.css',
        ],
    },

    'installable': True,
    'auto_install': False,

}
