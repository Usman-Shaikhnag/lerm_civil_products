# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Marsh Cone Compatibility Test With Admixture & Cement',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Marsh Cone Compatibility Test With Admixture & Cement',
    'description': """
This module contains all the common features of Marsh Cone Compatibility Test With Admixture & Cement.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
               'security/ir.model.access.csv',
               'views/marsh_cone.xml',
               'reports/marsh_cone_datasheet.xml',
               'reports/marsh_cone_report.xml'
    ],
    'assets': {
    'web.assets_backend': [
        'marsh_cone/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
