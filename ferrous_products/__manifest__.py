# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Ferrous Materials, Alloys & Products',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Ferrous Materials, Alloys & Products',
    'description': """
This module contains all the common features of Ferrous Materials, Alloys & Products .
    """,
    'depends': ['base','lerm_civil'],
    'data': [
             'security/ir.model.access.csv',
             'views/ferrous_products.xml',
             'reports/ferrous_product_datasheet.xml',
             'reports/ferrous_products_report.xml',
    ],

    'installable': True,
    'auto_install': False,
   
}
