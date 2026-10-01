# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Ferrous Material Plate',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Ferrous Material Plate',
    'description': """
This module contains all the common features of Ferrous Material Plate.
    """,
    'depends': ['base','lerm_civil','gypsum_mechanical'],
    'data': [
             'security/ir.model.access.csv',
            'views/ferrous_material_plate.xml',
            'reports/ferrous_material_plate_datasheet.xml',
            'reports/ferrous_material_report.xml'
             
    ],

    
    'installable': True,
    'auto_install': False,
   
}
