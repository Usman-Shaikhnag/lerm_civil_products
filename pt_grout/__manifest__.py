# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'PT Grout',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'PT Grout',
    'description': """
This module contains all the common features of PT Grout.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/pt_grout.xml',
                 'reports/pt_datasheet.xml',
                 'reports/pt_report.xml'
    ],

     'assets': {
    'web.assets_backend': [
        'pt_grout/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
