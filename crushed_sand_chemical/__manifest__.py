# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Crushed Sand',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/crushed_sand.xml',
                 'reports/crushed_sand_repot.xml',
                 'reports/crushed_sand_dataheet.xml'
    ],


    'assets': {
    'web.assets_backend': [
        'crushed_sand_chemical/static/src/css/custom_styles.css',
    ],
   },


  
    'installable': True,
    'auto_install': False,
   
}
