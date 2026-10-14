# -*- coding: utf-8 -*-

{
    'name': 'SS PIPE',
    'version': '1.0.1',
    'category': 'LERM CIVIL',
    'summary': 'SS Pipe Testing',
    'description': """
This module contains SS Pipe testing and reporting features.
    """,

    'depends': [
        'base',
        'lerm_civil',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/ss_pipe_views.xml',
        'reports/ss_pipe_datasheet.xml',
        'reports/ss_pipe_report.xml',
    ],

    'installable': True,
    'auto_install': False,
}