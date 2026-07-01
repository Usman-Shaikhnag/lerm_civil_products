{
    'name': 'General Ledger Report',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Reports',
    'summary': 'Modern, high-performance General Ledger report with Owl 2 frontend',
    'description': """
Modern General Ledger Report for Odoo 17
=========================================
A premium, accountant-friendly General Ledger report with:
- Interactive data table with sticky headers, sortable/resizable columns
- Powerful filtering (account, date range, journal, partner, analytic, state)
- Summary KPI cards (opening balance, total debit/credit, closing balance)
- Expandable rows with move lines, taxes, attachments
- Grouping by journal/month/partner/account with subtotals
- Server-side pagination supporting 100k+ move lines
- Export to Excel, CSV, PDF
- Mobile-responsive design
- Filter presets and dark mode support
    """,
    'author': 'Odoo Practice',
    'website': '',
    'depends': ['web', 'account', 'analytic'],
    'data': [
        'security/gl_security.xml',
        'security/ir.model.access.csv',
        'data/gl_report_data.xml',
        'data/gl_menu_data.xml',
        'report/gl_pdf_report.xml',
        'views/gl_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'account_gl_report/static/src/gl_report/__init__.js',
            'account_gl_report/static/src/gl_report/gl_report.js',
            'account_gl_report/static/src/gl_report/gl_report.xml',
            'account_gl_report/static/src/gl_report/gl_report.scss',
            'account_gl_report/static/src/services/gl_data_service.js',
            'account_gl_report/static/src/components/FilterToolbar/filter_toolbar.js',
            'account_gl_report/static/src/components/FilterToolbar/filter_toolbar.xml',
            'account_gl_report/static/src/components/FilterToolbar/filter_toolbar.scss',
            'account_gl_report/static/src/components/SummaryCards/summary_cards.js',
            'account_gl_report/static/src/components/SummaryCards/summary_cards.xml',
            'account_gl_report/static/src/components/SummaryCards/summary_cards.scss',
            'account_gl_report/static/src/components/LedgerTable/ledger_table.js',
            'account_gl_report/static/src/components/LedgerTable/ledger_table.xml',
            'account_gl_report/static/src/components/LedgerTable/ledger_table.scss',
            'account_gl_report/static/src/components/GroupHeader/group_header.js',
            'account_gl_report/static/src/components/GroupHeader/group_header.xml',
            'account_gl_report/static/src/components/GroupHeader/group_header.scss',
            'account_gl_report/static/src/components/ColumnChooser/column_chooser.js',
            'account_gl_report/static/src/components/ColumnChooser/column_chooser.xml',
            'account_gl_report/static/src/components/ColumnChooser/column_chooser.scss',
            'account_gl_report/static/src/components/ExportDialog/export_dialog.js',
            'account_gl_report/static/src/components/ExportDialog/export_dialog.xml',
            'account_gl_report/static/src/components/ExportDialog/export_dialog.scss',
            'account_gl_report/static/src/components/EmptyState/empty_state.js',
            'account_gl_report/static/src/components/EmptyState/empty_state.xml',
            'account_gl_report/static/src/components/EmptyState/empty_state.scss',
            'account_gl_report/static/src/components/MobileFilters/mobile_filters.js',
            'account_gl_report/static/src/components/MobileFilters/mobile_filters.xml',
            'account_gl_report/static/src/components/MobileFilters/mobile_filters.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
