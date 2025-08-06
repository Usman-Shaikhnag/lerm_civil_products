{
    'name': 'Lerm Equipments',
    'version': '1.0',
    'summary': 'Manage laboratory equipments',
    'description': """
        Module for managing laboratory equipments and their maintenance
    """,
    'author': 'Lerm',
    'website': 'https://www.lerm.com',
    'category': 'Laboratory',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/equipment_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}