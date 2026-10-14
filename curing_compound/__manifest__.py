# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Concrete Curing Compound',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil','gypsum_mechanical'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/curing_compound.xml',
                 'reports/curing_compound_datasheet.xml',
                 'reports/curing_compound_report.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}
