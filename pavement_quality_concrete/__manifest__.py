# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'PAVEMENT QUALITY CONCRETE (PQC)',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of PAVEMENT QUALITY CONCRETE (PQC).
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
                'security/ir.model.access.csv',
                'views/pqc.xml',
                'reports/pqc_datasheet.xml',
                'reports/pqc_report.xml'
    ],
    
    'installable': True,
    'auto_install': False,
   
}
