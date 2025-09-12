# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Paver Block',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/paver_block.xml',
                 'reports/paver_datasheet.xml'
    ],

    'assets': {
    'web.assets_backend': [
        'paver_block/static/paver.css',
    ],
},
   
    'installable': True,
    'auto_install': False,
   
}
