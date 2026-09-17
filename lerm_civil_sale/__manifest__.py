# -*- coding: utf-8 -*-
{
    'name': 'LERM Civil Sale',
    'summary': 'Push Sales Order prices to the customer pricelist (parameter-aware)',
    'author': 'LERM',
    'website': 'http://www.esehat.org',
    'category': 'Lerm Civil',
    'version': '1.0.0',
    'depends': [
        'sale',
        'lerm_civil',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/pricelist_wizard_views.xml',
        'views/pricelist_item_views.xml',
        'views/pricelist_audit_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
