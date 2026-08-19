# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Threaded Steel Fasteners',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Threaded Steel Fasteners',
    'description': """
This module contains all the common features of Threaded Steel Fasteners.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/threaded_steel.xml',
                 'reports/threaded_steel_datasheet.xml',
                 'reports/threaded_steel_report.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'threaded_steel/static/src/css/custom_style.css',
        ],
    },
  
    'installable': True,
    'auto_install': False,
   
}
