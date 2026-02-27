# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Gypsum Plaster Board',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'SGypsum Plaster Board',
    'description': """
This module contains all the common features of Gypsum Plaster Board.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/gypsum_plaster.xml',
                 'reports/datasheet.xml',
                 'reports/report.xml'
    ],

    'assets': {
    'web.assets_backend': [
        'gypsum_plaster_board/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
