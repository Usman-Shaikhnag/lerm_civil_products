{
    "name": "Document Filestore",
    'summary': """Document Filestore""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Esehat",
    "version": "17.0.1.0.0",
    "category":"Lerm Civil",
    "depends": ["web","base","lerm_civil", "ftp_storage",],
    "data": [
        'views/document_menu.xml',
        'security/ir.model.access.csv',
    ],
    "assets": {
        "web.assets_backend": [
            'https://cdn.jsdelivr.net/npm/chart.js',
            "document_filestore/static/src/components/**/*.js",
            "document_filestore/static/src/components/**/*.xml",
            "document_filestore/static/src/css/drive.scss",
        ],
    },
}
