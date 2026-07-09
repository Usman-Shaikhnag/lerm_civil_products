# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Fresh Cement Concrete',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features Fresh Cement Concrete.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 'security/ir.model.access.csv',
                 'views/fresh_cement_concrete.xml',
                 'reports/fresh_cement_concrete_datasheet.xml',
                 'reports/fresh_cement_concrete_report.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}
