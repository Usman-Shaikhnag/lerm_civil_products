# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Particle Board',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Particle Board',
    'description': """
This module contains all the common features of Particle Board.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                'security/ir.model.access.csv',
                'views/particle_board.xml',
                'reports/particl_datasheet.xml',
                'reports/particle_report.xml'
    ],

    'assets': {
    'web.assets_backend': [
        'shuttering_plywood/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
