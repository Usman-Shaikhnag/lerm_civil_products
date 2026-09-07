# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'GSB',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'GSB',
    'description': """
This module contains all the common features of GSB.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/gsb_soil.xml',
                 'reports/gsb_datasheet_soil.xml',
                 'reports/gsb_report_soil.xml'
    ],

    'assets': {
    'web.assets_backend': [
        'gsb/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
