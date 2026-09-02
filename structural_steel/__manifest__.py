# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Structural Steel Bar',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Structural Steel',
    'description': """
This module contains all the common features of Structural Steel.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
             'security/ir.model.access.csv',
            'views/structural_steel.xml',
            'reports/structural_steel_datasheet.xml',
            'reports/structural_steel_report.xml'
             
    ],

    
    'installable': True,
    'auto_install': False,
   
}
