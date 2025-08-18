# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Shuttring Plywood',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Shuttering Plywood',
    'description': """
This module contains all the common features of Shuttering Plywood.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/shuttering_plywood.xml',
                 'reports/shuttering_datasheet.xml',
                 'reports/shuttering_report.xml'
    ],

    'assets': {
    'web.assets_backend': [
        'shuttering_plywood/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
