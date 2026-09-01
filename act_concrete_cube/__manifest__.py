# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Compressive Strength of Concrete Cube By ACT',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/act_compressive_concrete_cube.xml',
                 'reports/act_datasheet.xml',
                 'reports/act_report.xml',
    ],
  
    'installable': True,
    'auto_install': False,
   
}
