# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.



{
    'name': 'Concrete Paving Block',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Concrete Paving Block Reports',
    'description': """
This module contains Concrete Paving Block report templates and related features.
    """,
    'depends': ['base', 'sale', 'lerm_civil'],
    'data': [
        'security/ir.model.access.csv',
        'views/paving_block.xml',
        'reports/paving_datasheet.xml',
    ],

    'installable': True,
    'auto_install': False,

}
