# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Copper Macro Stractural',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Ferrous Depth Mesurment',
    'description': """
This module contains all the common features of Ferrous Depth Mesurment.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                'sequrity/ir.model.access.csv',
                'views/copper_macro_stractural.xml',
                'reports/copper_macro_datasheet.xml',
                'reports/copper_macro_report.xml',
                
               
             
    ],

    'installable': True,
    'auto_install': False,
   
}
