# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'ULTRAFINE GGBS',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'ULTRAFINE GGBS',
    'description': """
This module contains all the common features of GGBS.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
               'security/ir.model.access.csv',
               'views/ultrafine_ggbs.xml',
               'reports/ultrafine_ggbs_datasheet.xml',
               'reports/ultrafine_ggbs_report.xml'
               
    ],
    'assets': {
    'web.assets_backend': [
        'ultrafine_ggbs/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
