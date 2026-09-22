{
    'name': 'Lab Control Center',
    'summary': 'Operational command center for LERM Management and HOD',
    'description': """
        Lab Control Center gives Management (Lerm Admin) and Head of
        Department users a single operational view of the testing pipeline:
        live KPIs (total / overdue / due today / testing / approval),
        needs-attention flags, the sample pipeline funnel, technician
        workload, sample aging against the report due date and a priority
        sample list. Every widget drills down into the matching
        lerm.srf.sample list.

        Data is scoped automatically: HOD users only see samples of the
        disciplines they head (discipline.hod == user), Management sees all
        companies / labs / disciplines.
    """,
    'author': 'Esehat',
    'version': '17.0.1.0.0',
    'category': 'Lerm Civil',
    'depends': ['base', 'web', 'lerm_civil'],
    'data': [
        'views/lab_control_center.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'lab_control_center/static/src/components/control_center/control_center.js',
            'lab_control_center/static/src/components/control_center/control_center.xml',
            'lab_control_center/static/src/css/control_center.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
