# -*- coding: utf-8 -*-

{
    'name': 'CS PIPE',
    'version': '1.0.1',
    'category': 'LERM CIVIL',
    'summary': 'CS Pipe Testing',
    'description': """
This module contains CS Pipe testing and reporting features.
    """,

    'depends': [
        'base',
        'lerm_civil',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/cs_pipe.xml',
        'reports/cs_pipe_datasheet.xml',
        'reports/cs_pipe_report.xml',
    ],

    'installable': True,
    'auto_install': False,
}