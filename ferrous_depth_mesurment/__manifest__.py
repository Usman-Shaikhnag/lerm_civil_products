# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Ferrous Depth Measurement',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Ferrous Depth Mesurment',
    'description': """
This module contains all the common features of Ferrous Depth Mesurment.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
               'sequrity/ir.model.access.csv',
              'views/ferrous_depth_mesurment.xml',
              'reports/ferrous_depth_datasheet.xml',
              'reports/ferrous_depth_report.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
