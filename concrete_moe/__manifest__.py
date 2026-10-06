# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Concrete MOE',
    'version': '1.3',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'post_init_hook': 'post_init_hook',
    'data': [
                'security/ir.model.access.csv',
                'views/concrete_moe.xml',
                'reports/concrete_moe_datasheet.xml',
                'reports/concrete_moe_report.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'concrete_moe/static/src/css/custom_style.css',
        ],
    },
  
    'installable': True,
    'auto_install': False,
   
}
