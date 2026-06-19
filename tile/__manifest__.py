# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'TILE',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'TILE',
    'description': """
This module contains all the common features of TILE.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
             'security/ir.model.access.csv',
              'views/tile.xml',
              'reports/tile_datasheet.xml',
              'reports/tile_ds_report.xml'
    ],

    'assets': {
    'web.assets_backend': [
        'tile/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
