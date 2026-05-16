# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Admixture',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Admixture Chemical',
    'description': """
This module contains all the common features of Admixture Chemical.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
               'sequrity/ir.model.access.csv',
               'views/admixture.xml',
               'reports/admixture_datasheet.xml',
               'reports/admixture_report.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
