# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Aluminum & its alloys',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Aluminum & its alloys',
    'description': """
This module contains all the common features of Aluminum & its alloys .
    """,
    'depends': ['base','lerm_civil'],
    'data': [
               'security/ir.model.access.csv',
               'views/aluminum_alloys.xml',
               'reports/aluminum_alloys_datasheet.xml',
               'reports/aluminum_alloys_report.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
