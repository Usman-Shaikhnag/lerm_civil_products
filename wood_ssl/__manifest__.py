# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'WOOD',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/wood_ssl.xml',
                 'reports/wood_datasheet.xml',
                 'reports/wood_report.xml'
    ],
          'assets': {
        'web.assets_backend': [
            'wood_ssl/static/src/css/wood_style.css',
        ],
    },  # ✅ COMMA added here
  
  
    'installable': True,
    'auto_install': False,
   
}