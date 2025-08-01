{
    'name': 'FTP Storage',
    'version': '1.0',
    'summary': 'Manage FTP storage connections',
    'description': 'Module to manage FTP storage connections and configurations',
    'author': 'Your Name',
    'depends': ['base','lerm_civil'],
    'external_dependencies': {
        'python': ['paramiko'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/ftp_storage_views.xml',
        'views/ftp_upload_wizard_views.xml',
        'views/srf_ftp_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}