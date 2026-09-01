{
    'name': 'Keyboard Navigation Enhancer',
    'version': '17.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Arrow-key navigation across form views and One2many tables',
    'description': '''
        Adds spreadsheet-like keyboard navigation to all Odoo 17 form views
        and editable One2many tree views. Navigate fields with arrow keys,
        Enter, and Shift+Enter. Skips hidden/readonly fields automatically.
        Works with notebook tabs, dialogs, and dynamically rendered components.
    ''',
    'author': 'Odoo AI TUI',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'keyboard_nav/static/src/keyboard_nav.esm.js',
            'keyboard_nav/static/src/keyboard_nav.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
