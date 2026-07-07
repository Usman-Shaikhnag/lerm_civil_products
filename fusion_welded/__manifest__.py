# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Fusion welded Ferrous Materials',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Fusion welded Ferrous Materials',
    'description': """
This module contains all the common features of Fusion welded Ferrous Materials .
    """,
    'depends': ['base','lerm_civil'],
    'data': [
             'security/ir.model.access.csv',
             'views/fusion_welded.xml',
             'reports/fusion_welded_report.xml',
             'reports/fusion_welded_datasheet.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
