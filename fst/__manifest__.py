# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'FST',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': '',
    'description': """
    """,
    'depends': ['base','lerm_civil','report_py3o',],
    'data': [
                 'security/security.xml',
                 'views/fst_dashboard.xml',
                 'security/ir.model.access.csv',
                #  'views/pile_load_import_wizard_view.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'fst/static/src/css/custom_style.css',
        ],
    },
  
    'installable': True,
    'auto_install': False,
   
}
