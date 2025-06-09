# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Gypsum Chemical',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/gypsum.xml',
                 'reports/gypsum_report.xml',
                 'reports/gypsum_datasheet.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}
