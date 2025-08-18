# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'GGBS',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'GGBS',
    'description': """
This module contains all the common features of GGBS.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
               'security/ir.model.access.csv',
               'views/ggbs.xml',
               'reports/ggbs_datasheet.xml',
               'reports/ggbs_report.xml'
               
    ],
    'assets': {
    'web.assets_backend': [
        'ggbs/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
