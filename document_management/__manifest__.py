{
    'name': 'Document Management System',
    'version': '17.0.1.0.0',
    'category': 'Document Management',
    'summary': 'Local-file DMS with OWL UI and FastAPI backend',
    'description': """
Document Management System
==========================
A document management module that stores files locally on the server.

* OWL based Drive-like UI (grid / list, search, filters)
* FastAPI microservice for file storage, streaming and preview conversion
* Configurable storage location (res.config.settings)
* Previews for PDF, DOCX, XLSX, CSV and images
* Access control: user / role / team / department based permissions
* Read / Write / Download / Delete / Manage granular permissions
* Public and private documents
* Audit trail
* Tags, document types, custom fields and rich metadata
    """,
    'author': 'Knack17',
    'website': 'https://example.com',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'contacts', 'hr', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/dms_data.xml',
        'views/dms_menus.xml',
        'views/dms_master_data_views.xml',
        'views/dms_audit_views.xml',
        'views/dms_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'document_management/static/src/css/dms.scss',
            'document_management/static/src/utils.js',
            'document_management/static/src/components/**/*.js',
            'document_management/static/src/components/**/*.xml',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
}
