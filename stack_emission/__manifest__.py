# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Stack Emission',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
           'views/stack_emission.xml',
           'security/ir.model.access.csv',
           'reports/stack_emission_datasheet.xml'
    ],
   
    'installable': True,
    'auto_install': False,
   
}
