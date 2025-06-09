# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'SOIL',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'views/soil.xml',
                 'reports/soil_datasheet.xml',
                 'reports/soil_report.xml'
                
    ],
  
    'installable': True,
    'auto_install': False,
   
}
