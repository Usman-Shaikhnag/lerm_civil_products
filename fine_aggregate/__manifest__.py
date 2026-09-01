# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Fine Aggregate',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Fine Aggregate PRODUCT',
    'description': """
This module contains all the common features of Fine Aggregate.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
              'security/ir.model.access.csv',
              'views/fine_aggregate.xml',
              'reports/fine_agg_report.xml',
              'reports/fine_aggregate_datasheet.xml'

               
    ],

  
    'installable': True,
    'auto_install': False,

    
}
