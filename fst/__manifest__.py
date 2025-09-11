# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'FST',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': '',
    'description': """
    """,
    'depends': ['base','lerm_civil','soil_resistivity'],
    'data': [
                 'security/security.xml',
                 'views/ert.xml',
                 'views/soil_resistivity.xml',
                 'data/sequence.xml',
                 'reports/soil_resistivity_report_docx.xml',
                 'security/ir.model.access.csv',

    ],
    'assets': {
        'web.assets_backend': [
            'fst/static/src/css/custom_style.css',
        ],
    },
  
    'installable': True,
    'auto_install': False,
   
}
