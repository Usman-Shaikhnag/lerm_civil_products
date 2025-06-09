# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'RCMT',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/rcmt.xml',
                 'reports/rcmt_datasheet.xml',
                 'reports/rcmt_report.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}
