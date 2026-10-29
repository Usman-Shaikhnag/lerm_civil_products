{
    "name": "LERM Audit Trail",
    "summary": "Audit trail for LERM master data: parameters, specifications, test methods, products and other masters",
    "description": "Preloads Audit Trail rules for the LERM CIVIL Master Data menu and adds an Audit Trail entry under it. More models can be audited from Settings > Technical > Audit Trail > Audit Rules without code.",
    "author": "Esehat",
    "version": "17.0.1.0.0",
    "category": "Lerm Civil",
    "depends": ["audit_trail", "lerm_civil"],
    "data": [
        "data/audit_rule_data.xml",
        "views/menu_views.xml",
    ],
    "license": "LGPL-3",
}
