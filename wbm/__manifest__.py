# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'WBM',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'WBM',
    'description': """
This module contains all the common features of WBM.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                'security/ir.model.access.csv',
                'views/wbm.xml',
                'reports/wbm_datasheet.xml',
                'reports/wbm_report.xml'
    ],
    'assets': {
    'web.assets_backend': [
        'wbm/static/src/css/custom_styles.css',
    ],
   },
  
  
    'installable': True,
    'auto_install': False,
   
}
