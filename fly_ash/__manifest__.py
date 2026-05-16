# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'FLY ASH',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'FLY ASH PRODUCT',
    'description': """
This module contains all the common features of FLY ASH.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
              'security/ir.model.access.csv',
              'views/fly_ash.xml',
              'reports/fly_datasheet.xml',
              'reports/fly_ds_report.xml'
               
    ],

    'assets': {
    'web.assets_backend': [
        'fly_ash/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,

    
}
