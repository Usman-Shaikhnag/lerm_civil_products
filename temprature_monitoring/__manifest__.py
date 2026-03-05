# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Temprature Monitoring',
    'version': '1.2',
    'category': 'LERM CIVIL',
    'summary': 'Temprature Monitoring',
    'description': """
This module contains all the common features of Temprature Monitoring.
    """,
    'depends': ['base','lerm_civil'],
    'data': [
                'security/ir.model.access.csv',
                'views/temprature_monitoring.xml',
                'reports/temprature_datasheet.xml',
                'reports/temprature_monitoring_report.xml'
    ],

    
  
    'installable': True,
    'auto_install': False,
   
}
