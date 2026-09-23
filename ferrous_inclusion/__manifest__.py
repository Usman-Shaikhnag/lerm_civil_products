# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Ferrous  Inclusion',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Ferrous  Inclusion',
    'description': """
This module contains all the common features of Ferrous  Inclusion.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
               'sequrity/ir.model.access.csv',
              'views/ferrous_inclusion.xml',
              'reports/ferrous_inclusion_datasheet.xml',
              'reports/ferrous_inclusion_report.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
