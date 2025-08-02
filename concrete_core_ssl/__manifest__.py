# -*- coding: utf-8 -*-
{
    'name': 'CONCRETE CORE',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base', 'sale', 'lerm_civil'],
    'data': [
        'security/ir.model.access.csv',
        'views/concrete_core.xml',
        'reports/concrete_core_datasheet.xml',
        'reports/concrere_core_report.xml'
    ],
    'assets': {
        'web.assets_backend': [
            # 'concrete_core_ssl/static/src/css/custom_style.css',
        ],
    },  # ✅ COMMA added here
    'installable': True,
    'auto_install': False,
}
