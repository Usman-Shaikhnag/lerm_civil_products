# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'SS TMT BAR',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
            'security/ir.model.access.csv',
            'views/mechanical/ferrous_structural_steel.xml',
            'reports/ferrous_structural_steel_datasheet.xml',
            'reports/ferrous_structural_steel.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ferrous_steel/static/src/css/custom_style.css',
        ],
    },
  
    'installable': True,
    'auto_install': False,
   
}
