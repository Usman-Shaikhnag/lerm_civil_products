# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Aluminium Macro Stractural',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Ferrous Depth Mesurment',
    'description': """
This module contains all the common features of Ferrous Depth Mesurment.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                'sequrity/ir.model.access.csv',
                'views/aluminium_macro_stractural.xml',
                'reports/aluminium_macro_datasheet.xml',
                'reports/aluminium_macro_report.xml',
                
               
             
    ],

    'installable': True,
    'auto_install': False,
   
}
