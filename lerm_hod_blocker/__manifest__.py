{
    'name': 'LERM HOD Sample Allotment Blocker',
    'version': '17.0.1.0.0',
    'summary': 'Blocks HOD until new KES samples are allotted to technicians',
    'description': """
        Periodically (interval configurable via the system parameter
        hod_blocker.check_interval_hours, default 2 hours) checks the HOD's
        department for pending samples. If pending samples exist they are
        shown in a popup (cancelable for same-day samples, blocking for
        samples from previous days). The HOD must allot each sample to a
        technician along with a report due date.
    """,
    'author': 'Esehat',
    'category': 'Lerm Civil',
    'depends': ['base', 'web', 'lerm_civil'],
    'data': [
        'data/config_parameter.xml',
        'security/ir.model.access.csv',
        'views/sample_allotment_wizard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'lerm_hod_blocker/static/src/js/hod_block_dialog.js',
            'lerm_hod_blocker/static/src/js/hod_blocker.js',
            'lerm_hod_blocker/static/src/js/hod_block_dialog.xml',
        ],
    },
    'installable': True,
    'application': False,
}
