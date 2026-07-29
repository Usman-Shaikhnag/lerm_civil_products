# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'MICROSILICA',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'MICROSILICA',
    'description': """
This module contains all the common features of MICROSILICA.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
               'security/ir.model.access.csv',
               'views/microsilica.xml',
               'reports/microsilica_datasheet.xml',
               'reports/microsilica_report.xml'
    ],
    'assets': {
    'web.assets_backend': [
        'microsilica/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
