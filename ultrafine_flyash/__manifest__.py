# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'ULTRAFINE FLY ASH',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'ULTRAFINE FLY ASH PRODUCT',
    'description': """
This module contains all the common features of ULTRAFINE FLY ASH.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
              'security/ir.model.access.csv',
              'views/ultrafine_flyash.xml',
              'reports/ultrafine_flyash_datasheet.xml',
              'reports/ultrafine_flyash_report.xml',
               
    ],

    'assets': {
    'web.assets_backend': [
        'ultrafine_flyash/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,

    
}
