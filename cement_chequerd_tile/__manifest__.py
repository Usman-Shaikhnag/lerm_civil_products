# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Cement Chequerd Tile',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Cement Chequerd Tile',
    'description': """
This module contains all the common features of Cement Chequerd Tile.
    """,
    'depends': ['base','lerm_civil'],
    'data': [   
                 'security/ir.model.access.csv',
                 'views/cement_chequerd_tile.xml',
                 'reports/cement_tile_datasheet.xml',
                 'reports/cement_tile_report.xml'
    ],

    'assets': {
    'web.assets_backend': [
        'cement_chequerd_tile/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
