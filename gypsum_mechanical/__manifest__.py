# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Gypsum Mechanical',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Gypsum Mechanical',
    'description': """
This module contains all the common features of Gypsum Mechanical.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/gypsum.xml',
                 'reports/gypsum_report.xml',
                 'reports/gypsum_datasheet.xml'
    ],

    'assets': {
    'web.assets_backend': [
        'gypsum_mechanical/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
