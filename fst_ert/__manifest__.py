# -*- coding: utf-8 -*-
{
    'name': 'FST ERT',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Electrical Resistivity Testing (ERT)',
    'depends': ['base', 'lerm_civil', 'fst'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/ert.xml',
        'views/soil_resistivity.xml',
        'wizards/ert_report_wizard.xml',
        'reports/soil_resistivity_report_docx.xml',
    ],
    'installable': True,
    'auto_install': False,
}
