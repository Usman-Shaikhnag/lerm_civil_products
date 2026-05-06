# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Waste Water',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Waste Water Chemical',
    'description': """
This module contains all the common features of Waste Water Chemical.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
               'sequrity/ir.model.access.csv',
               'views/waste_water.xml',
               'reports/waste_water_datasheet.xml',
               'reports/waste_water_report.xml'
    ],

    'installable': True,
    'auto_install': False,
   
}
