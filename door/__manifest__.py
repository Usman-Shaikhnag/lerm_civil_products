# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'DOOR',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Door Product',
    'description': """
This module contains all the common features of Door Products.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                'views/door.xml',
                'reports/door_datasheet.xml',
                'reports/door_report.xml'

    ],
    'assets': {
    'web.assets_backend': [
        'door/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
