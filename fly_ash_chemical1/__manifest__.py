# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Fly Ash Chemical',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Fly Ash Chemical',
    'description': """
This module contains all the common features of Fly Ash Chemical.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                 'sequrity/ir.model.access.csv',
                 'views/fly_ash.xml',
                 'reports/fly_ash_dataseet.xml',
                 'reports/fly_ash_report.xml'
    ],
    'installable': True,
    'auto_install': False,
   
}
