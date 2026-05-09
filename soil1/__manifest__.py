# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'SOIL',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
               'security/ir.model.access.csv',
               'views/soil.xml',
               'reports/soil_ssl_datasheet.xml',
               'reports/soil_report.xml',
               'reports/soil_report_first.xml',
               'reports/soil_report_rest.xml',
    ],

  
    'installable': True,
    'auto_install': False,
   
}
