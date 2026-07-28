# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'DRY LEAN CONCRETE (DLC)',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'DRY LEAN CONCRETE (DLC)',
    'description': """
This module contains all the common features of DRY LEAN CONCRETE (DLC).
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/dlc.xml',
                 'reports/dlc_datasheet.xml',
                 'reports/dlc_report.xml'
    ],

    'assets': {
    'web.assets_backend': [
        'gsb/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
