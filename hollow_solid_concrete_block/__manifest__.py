# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Hollow And Solid Concrete Block',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Hollow And Solid Concrete Block.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/hollow_solid_block.xml',
                 'reports/hollow_solid_block_datasheet.xml',
                 'reports/hollow_solid_block_report.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}
