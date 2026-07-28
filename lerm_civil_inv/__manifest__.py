{'name':'LERM_Invoicing',
 'summary': "Invoicing",
 'author': "Usman Shaikhnag and Khan Afzal", 
 'website': "http://www.esehat.org", 
 'category': 'Lerm Civil', 
 'version': '13.0.1', 
 'depends':['base' ,'sale', 'contacts','account','product', 'web','l10n_in','base_account_budget','account_invoice_pricelist','base_accounting_kit'],
 'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'report/kes_invoice_action.xml',
        'report/kes_invoice_template.xml',
        'report/kes_invoice_template_without_header.xml',
        'views/customer.xml',
        'views/company.xml',
        'wizards/bulk_invoice_wizard_views.xml',
    ],
 'assets': {
        'web.report_assets_common': [
            '/lerm_civil_inv/static/src/css/kes_invoice.scss',
        ],
    }
}


