# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Ferrous Estimating depth of Complete & Partial',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Ferrous Estimating depth of Complete & Partial',
    'description': """
This module contains all the common features of Ferrous Estimating depth of Complete & Partial.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
               'sequrity/ir.model.access.csv',
              'views/ferrous_complete_partial.xml',
              'reports/ferrous_partial_datasheet.xml',
              'reports/ferrous_partial_report.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
