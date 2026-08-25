# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'DRYING SHRINKAGE',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'DRYING SHRINKAGE PRODUCT',
    'description': """
This module contains all the common features of DRYING SHRINKAGE.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/drying_shrinkage.xml',
                 'reports/drying_ds_report.xml'
    ],
    'assets': {
    'web.assets_backend': [
        'drying_shrinkage/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
