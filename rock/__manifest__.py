# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Rock',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'views/rock.xml',
                 'reports/rock_datasheet1.xml',
                 'reports/rock_report.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}
