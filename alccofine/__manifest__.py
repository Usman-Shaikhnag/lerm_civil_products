# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'ALCCOFINE',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'ALCCOFINE',
    'description': """
This module contains all the common features of GGBS.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
               'security/ir.model.access.csv',
               'views/alccofine.xml',
               'reports/alccofine_datasheet.xml',
               'reports/alccofine_report.xml'
               
    ],
    'assets': {
    'web.assets_backend': [
        'alccofine/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
