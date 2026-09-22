# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': ' KERB STONE',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
               'security/ir.model.access.csv',
                'views/precast_kerb_stone.xml',
                'reports/precast_kerb_datasheet.xml',
                'reports/precast_kerb_report.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}
