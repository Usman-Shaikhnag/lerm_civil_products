{
    'name': 'FTP Storage',
    'version': '1.0',
    'summary': 'Manage FTP storage connections',
    'description': 'Module to manage FTP storage connections and configurations. '
                   'SRF / Sample / ELN attachments are stored in the Document Management System.',
    'author': 'Your Name',
    'depends': ['base', 'lerm_civil', 'document_management'],
    'external_dependencies': {
        'python': ['paramiko'],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/ftp_dms_data.xml',
        'views/ftp_storage_views.xml',
        'views/ftp_upload_wizard_views.xml',
        'views/srf_ftp_views.xml',
        'views/sample_ftp_views.xml',
        'views/eln_ftp_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}