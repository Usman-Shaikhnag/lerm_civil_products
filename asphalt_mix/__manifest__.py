# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Asphalt Mix',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features Asphalt Mix.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/asphalt_mix.xml',
                 'reports/asphalt_mix_datasheet.xml',
                 'reports/asphalt_mix_report.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}
