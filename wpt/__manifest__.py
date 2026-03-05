# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'WPT',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'WPT',
    'description': """
This module contains all the common features of WPT.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
           'security/ir.model.access.csv',
           'views/wpt.xml',
           'reports/wpt_datasheet.xml',
           'reports/wpt_report.xml'
               
    ],
    'assets': {
    'web.assets_backend': [
        'wpt/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
