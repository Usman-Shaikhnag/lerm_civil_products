# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Concrete Cube Water Absorption',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Waste Water Chemical',
    'description': """
This module contains all the common features of Waste Water Chemical.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
               'sequrity/ir.model.access.csv',
               'views/cube_water_absorption.xml',
               'reports/cube_water_datasheet.xml',
               'reports/cube_water_report.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
