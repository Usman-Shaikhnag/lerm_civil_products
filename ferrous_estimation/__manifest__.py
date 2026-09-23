# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Ferrous Materials Estimation',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Ferrous Materials Estimation',
    'description': """
This module contains all the common features of Ferrous Materials Estimation.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
               'sequrity/ir.model.access.csv',
              'views/ferrous_estimation.xml',
              'reports/ferrous_estimation_datasheet.xml',
              'reports/ferrous_estimation_report.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
