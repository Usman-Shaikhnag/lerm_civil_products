# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Hollow Concrete Block',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Hollow Concrete Block.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/hollow_concrete_block.xml',
                 'reports/hollow_concrete_block_datasheet.xml',
                 'reports/hollow_concrete_block_report.xml'
    ],

    'assets': {
    'web.assets_backend': [
        'hollow_concrete_block/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
