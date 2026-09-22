# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Hardent Concrete Chemical',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Hardent Concrete Chemical',
    'description': """
This module contains all the common features of Hardent Concrete Chemical.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                'security/ir.model.access.csv',
                'views/hardend_concrete.xml',
                'reports/hardend_concrete_report.xml',
                'reports/harden_concrete_datasheet.xml'
    ],

    'assets': {
    'web.assets_backend': [
        'hardent_concrete_chemical/static/src/css/custom_styles.css',
    ],
   },
  
  
    'installable': True,
    'auto_install': False,
   
}
