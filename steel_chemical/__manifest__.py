# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Steel Chemical',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Steel Chemical',
    'description': """
This module contains all the common features of Steel Chemical.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
               'sequrity/ir.model.access.csv',
               'views/steel_chemical.xml',
               'reports/steel_chemical_datasheet.xml',
               'reports/steel_chemical_report.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
