# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Concrete Cylinder',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/concret_cylinder.xml',
                 'reports/cylinder_datasheet.xml',
                #  'reports/cube_report.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'concrete_cube/static/src/css/custom_style.css',
        ],
    },
  
    'installable': True,
    'auto_install': False,
   
}
