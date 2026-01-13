# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Plate Load',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/plate_load.xml',
                 'reports/plate_load_report.xml',
                 'reports/plate_load_datasheet.xml'
    ],
   
    'installable': True,
    'auto_install': False,
   
}
