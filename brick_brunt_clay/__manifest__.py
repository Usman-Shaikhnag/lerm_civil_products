# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'BRICK BRUNT CLAY',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
            'security/ir.model.access.csv',
             'views/brick_brunt_clay.xml',
             'reports/brick_burnt_datasheet.xml',
             'reports/brick_burnt_clay_report.xml'
    ],
     'assets': {
        'web.assets_backend': [
            'concrete_core_ssl/static/src/css/custom_style.css',
           
        ],
    },  # ✅ COMMA added here
  
  
    'installable': True,
    'auto_install': False,
   
}
