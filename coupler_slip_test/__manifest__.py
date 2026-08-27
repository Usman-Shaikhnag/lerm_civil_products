# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Coupler Slip Test',
    'version': '1.0',
    'category': 'Lerm Civil',
    'summary': 'Coupler Slip Test',
    'description': """
    This module contains all the common features of coupler slip test.
    """,
    'depends': ['base','lerm_civil'],  
    'data': [
        'security/ir.model.access.csv', 
        'views/coupler.xml',  
        'reports/coupler_slip_report.xml',  
        'reports/coupler_slip_datasheet.xml',  
    ],
    'installable': True,
    'auto_install': False,
}
