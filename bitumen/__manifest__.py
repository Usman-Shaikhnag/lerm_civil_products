# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'BITUMEN',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'LERM CIVIL',
    'description': """
This module contains all the common features of LERM CIVIL.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                'security/ir.model.access.csv',
                'views/bitumen.xml',
                'reports/bitumen_datasheet.xml',
                'reports/bitumen_report.xml'
    ],
    
    'installable': True,
    'auto_install': False,
   
}
