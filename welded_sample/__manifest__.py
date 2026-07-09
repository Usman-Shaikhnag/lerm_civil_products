# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Welded Sample',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Welded Sample',
    'description': """
This module contains all the common features of Welded Sample .
    """,
    'depends': ['base','lerm_civil'],
    'data': [
            'security/ir.model.access.csv',
            'views/welded_sample.xml',
            'reports/welded_sample_datasheet.xml',
            'reports/welded_sample_report.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
