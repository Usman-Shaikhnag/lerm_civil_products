# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Drinking Water',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Drinking Water Chemical',
    'description': """
This module contains all the common features of Drinking Water Chemical.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                'security/ir.model.access.csv',
                 'views/drinking_water.xml',
                 'reports/drinking_water_datasheet.xml',
                 'reports/drinking_water_report.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
