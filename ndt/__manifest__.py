# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'NDT',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
              'security/ir.model.access.csv',
               'views/acil_crack_depth.xml',
               'views/acil_upv.xml',
               'views/carbonation_test.xml',
               'views/concrete_core.xml',
               'views/cover_meter.xml',
               'views/crack_depth.xml',
               'views/crack_width.xml',
               'views/half_cell.xml',
               'views/rebound_hammer.xml',
               'views/upv.xml',
    ],
  
    'installable': True,
    'auto_install': False,
   
}
