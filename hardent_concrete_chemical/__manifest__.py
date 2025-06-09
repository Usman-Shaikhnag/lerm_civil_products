# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Hardent Concrete Chemical',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                'security/ir.model.access.csv',
                'views/hardend_concrete.xml',
                'reports/hardend_concrete_report.xml',
                'reports/harden_concrete_datasheet.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}
