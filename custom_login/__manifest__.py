{
    'name': 'Custom Login',
    'version': '1.0',
    'summary': 'Customize the Odoo login page',
    'description': 'Modifies the login page to show custom branding',
    'author': 'Your Name',
    'depends': ['web'],
    'data': [
        'views/login_templates.xml',
    ],
    'assets': {
    'web.assets_backend':[
        'custom_login/static/src/css/custom_styles.css',
    ],
        },
    'installable': True,
    'application': False,
}