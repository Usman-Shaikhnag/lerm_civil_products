# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'HIGH STRENGTH DEFORMED STEEL BARS',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features Asphalt Mix.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/hsd_steel_bars.xml',
                 'reports/hsd_steel_bars_datasheet.xml',
                 'reports/hsd_steel_bars_report.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}
