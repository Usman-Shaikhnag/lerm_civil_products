# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Natural Building Stone',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
               'security/ir.model.access.csv',
               'views/natural_stone.xml',
               'reports/natural_stone_datasheet.xml',
               'reports/natural_stone_report.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'concrete_cube/static/src/css/custom_style.css',
        ],
    },
  
    'installable': True,
    'auto_install': False,
   
}
