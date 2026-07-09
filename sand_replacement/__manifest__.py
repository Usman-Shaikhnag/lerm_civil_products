# -*- coding: utf-8 -*-
{
    'name': 'Sand Replacement',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base', 'sale', 'lerm_civil'],
    'data': [
                'security/ir.model.access.csv',
                'views/sand_replacement.xml',
                'reports/sand_replacement_report.xml',
                'reports/sand_replacement_datasheet.xml'
    ],
   
   
    'installable': True,
    'auto_install': False,
}
