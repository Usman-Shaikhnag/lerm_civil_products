# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Welded Steel',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Welded Steel',
    'description': """
This module contains all the common features of Welded Steel .
    """,
    'depends': ['base','lerm_civil'],
    'data': [
           'security/ir.model.access.csv',
           'views/welded_steel.xml',
           'reports/welded_steel_datasheet.xml',
           'reports/welded_steel_report.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
