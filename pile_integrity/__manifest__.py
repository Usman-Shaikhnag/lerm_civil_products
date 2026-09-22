# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Pile Intergity',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Pile Intergity',
    'description': """
This module contains all the common features of Pile Intergity.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
           'security/ir.model.access.csv',
            'views/pile_integrity.xml',
            'reports/pile_integrity_report.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
