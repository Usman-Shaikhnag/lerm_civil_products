# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Fly Ash Chemical',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Fly Ash Chemical',
    'description': """
This module contains all the common features of Fly Ash Chemical.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/flyash.xml',
                 'reports/flyash_report.xml',
                 'reports/flyash_datasheet.xml'
    ],

    'assets': {
    'web.assets_backend': [
        'fly_ash_chemical/static/src/css/custom_styles.css',
    ],
   },
  

    'installable': True,
    'auto_install': False,
   
}
