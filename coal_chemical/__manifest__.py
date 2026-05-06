# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Coal',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Coal Chemical',
    'description': """
This module contains all the common features of Coal Chemical.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
               'security/ir.model.access.csv',
               'views/coal.xml',
               'reports/coal_datasheet.xml',
               'reports/coal_report.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
