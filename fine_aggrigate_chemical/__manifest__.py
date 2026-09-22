# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Fine Aggregate',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Fine Aggregate Chemical',
    'description': """
This module contains all the common features of Fine Aggregate Chemical.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                'views/fine_aggregate.xml',
                'reports/fine_aggregate_chemical_report.xml',
                'reports/fine_aggregate_chemical_datasheet.xml'
    ],

    'assets': {
    'web.assets_backend': [
        'fine_aggrigate_chemical/static/src/css/custom_styles.css',
    ],
   },
  
    'installable': True,
    'auto_install': False,
   
}
