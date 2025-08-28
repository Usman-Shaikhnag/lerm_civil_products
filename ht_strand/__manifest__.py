# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'HT STRAND',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'HT STRAND',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
             'security/ir.model.access.csv',
             'views/ht_strand.xml',
             'reports/ht_datasheet.xml',
             'reports/ht_report.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}
