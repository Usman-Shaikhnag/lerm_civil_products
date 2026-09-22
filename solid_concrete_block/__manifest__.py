# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Solid Concrete Block',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Solid Concrete Block.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/solid_concrete_block.xml',
                 'reports/solid_concrete_block_datasheet.xml',
                 'reports/solid_concrete_block_report.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}
