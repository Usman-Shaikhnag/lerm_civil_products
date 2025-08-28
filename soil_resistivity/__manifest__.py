# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'SOIL Resistivity',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
               'security/ir.model.access.csv',
               'views/soil_resistivity.xml',
               'reports/soil_resistivity_datasheet.xml',
               'reports/soil_resistivity_report.xml'
    ],

  
    'installable': True,
    'auto_install': False,
   
}
