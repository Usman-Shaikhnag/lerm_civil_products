# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'AAC Block',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'views/aac_block.xml',
                 'reports/aac_datasheet.xml',
                 'reports/aac_report.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}
