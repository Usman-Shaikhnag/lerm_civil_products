{
    "name": "Audit Trail",
    "summary": "Log every create, change and delete on any model you choose, with restore of deleted records",
    "description": "Admins pick models from the UI through Audit Rules. Subscribed models log who created, changed or deleted a record, when, and the old and new value of each field. Deleted records keep a snapshot that an Audit Manager can restore. Logs cannot be edited or deleted.",
    "author": "Esehat",
    "version": "17.0.1.0.0",
    "category": "Tools",
    "depends": ["base"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/audit_log_views.xml",
        "views/audit_rule_views.xml",
        "views/menu_views.xml",
    ],
    "uninstall_hook": "uninstall_hook",
    "license": "LGPL-3",
}
