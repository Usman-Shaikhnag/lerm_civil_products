# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'ROCK',
    'version': '1.2',
    'category': 'Sales/Sales',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of ROCK.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                 
                 'security/ir.model.access.csv',
                 'views/rock.xml',
                 'report/rock_ds_report.xml'
    ],
  
    'installable': True,
    'auto_install': False,
   
}