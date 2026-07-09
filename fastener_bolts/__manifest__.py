# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Fastener / Bolts & Studs',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Fastener / Bolts & Studs',
    'description': """
This module contains all the common features of Fastener / Bolts & Studs .
    """,
    'depends': ['base','lerm_civil'],
    'data': [
             'security/ir.model.access.csv',
             'views/fastener_bolts.xml',
             'reports/fastener_bolts_datasheet.xml',
             'reports/fastener_bolts_report.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
