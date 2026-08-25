# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Structural Steel Round',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Structural Steel Round',
    'description': """
This module contains all the common features of Structural Steel Round.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
             'security/ir.model.access.csv',
            'views/ss_round.xml',
            'reports/ss_round_datasheet.xml',
            'reports/ss_round_report.xml'
             
    ],

    
    'installable': True,
    'auto_install': False,
   
}
