# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'TMT BAR',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'TILE',
    'description': """
This module contains all the common features of TILE.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
             'security/ir.model.access.csv',
            'views/steel_tmt_bar.xml',
            'reports/steel_tmt_bar_datasheet.xml',
            'reports/steel_tmt_bar_report.xml'
             
    ],

    
    'installable': True,
    'auto_install': False,
   
}
