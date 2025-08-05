# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Fine Aggregate',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
          'security/ir.model.access.csv',
           'views/fine_aggregate.xml',
           'reports/fine_aggregate_datasheet.xml',
           'reports/fine_agg_report.xml'
        
    ],
        'assets': {
        'web.assets_backend': [
            'fine_aggregat_ssl/static/src/css/custom_style.css',
        ],
    },
  
    'installable': True,
    'auto_install': False,
   
}