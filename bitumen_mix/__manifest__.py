# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Bituminous Mix',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
            'security/ir.model.access.csv',
            'views/bitumen_mix.xml',
            'reports/bitumen_mix_datasheet.xml',
            'reports/bitument_mix_report.xml'
    ],
      
  
    'installable': True,
    'auto_install': False,
   
}
