# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'TMT BAR',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
             'security/ir.model.access.csv',
             'views/tmt_bar.xml',
             'reports/tmt_bar_ds_report.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}
