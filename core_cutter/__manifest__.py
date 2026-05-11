# -*- coding: utf-8 -*-
{
    'name': 'CORE CUTTER',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base', 'sale', 'lerm_civil'],
    'data': [
                'security/ir.model.access.csv',
                'views/core_cutter.xml',
                'reports/core_cutter_report.xml',
                'reports/core_cutter_datasheet.xml'
    ],
   
   
    'installable': True,
    'auto_install': False,
}
