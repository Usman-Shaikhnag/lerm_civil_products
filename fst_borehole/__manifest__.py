{
    'name': 'FST Borehole',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Borehole Logging and Soil Testing',
    'depends': ['base', 'lerm_civil', 'fst'],
    'data': [
        'security/ir.model.access.csv',
        'views/fst_borehole_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
