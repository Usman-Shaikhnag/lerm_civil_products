# -*- coding: utf-8 -*-
{
    'name': 'LERM Civil Sale',
    'summary': 'Sales Order to LERM Civil SRF integration',
    'author': 'LERM',
    'website': 'http://www.esehat.org',
    'category': 'Lerm Civil',
    'version': '1.0.0',
    'depends': [
        'sale',
        'lerm_civil',
        'lerm_accountant',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/srf_views.xml',
        'views/sale_order_srf_wizard_views.xml',
        'views/pricelist_wizard_views.xml',
        'views/pricelist_audit_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
