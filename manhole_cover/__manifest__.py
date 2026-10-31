# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'CONCRETE MANHOLE COVER AND FRAME',
    'version': '1.3',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil','gypsum_mechanical'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/manhole_cover.xml',
                 'reports/manhole_datasheet.xml',
                 'reports/manhole_report.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}
