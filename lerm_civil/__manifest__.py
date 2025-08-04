{'name':'LERM_CIVIL',
 'summary': "LERM_CIVIL",
 'author': "Usman Shaikhnag", 
 'website': "http://www.esehat.org", 
 'category': 'Lerm Civil', 
 'version': '13.0.1', 
 'depends':['base' , 'contacts','product' ,'hr','lerm_civil_inv', 'mail','attachment_indexation','maintenance','portal'],
 'data': [
    'security/security.xml',
    'data/sequence.xml',
    # 'data/module_category_data.xml',
    'views/enviroment_register.xml',
    'views/sample_register.xml',
    'views/lerm.xml',
    'views/groups.xml',
    'views/res_company.xml',
    'views/material.xml',
    'views/srf.xml',
    'views/edit_srf_header_wizard.xml',
    'views/parameter_master.xml',
    'views/datasheet_master.xml',
    'views/sample.xml',
    'views/sample_range.xml',
    'views/eln.xml',
    'views/contractor.xml',
    'views/lab_master.xml',
    'views/employee.xml',
    'views/product_grade_wizard.xml',
    'views/reallocation_wizard.xml',
    # 'views/ftp_upload_wizard_views.xml',
    # 'views/ftp_upload_wizard_views.xml',
    # 'views/mechanical/sieve_analysis.xml',
    'reports/eln_report_action.xml',
    'reports/eln_report_template.xml',
    'reports/general_report_template.xml',
    'reports/general_template.xml',
    'reports/mechanical_general_template.xml',
    'security/ir.model.access.csv'
   


    # 'views/portal_template.xml'
    


    
    
 



    # 'security/ir.model.access.csv',
    ],
    'assets': {
    'web.assets_backend':[
        'lerm_civil/static/src/css/custom_styles.css',
    ],
    'web.report_assets_common': [
            '/lerm_civil/static/src/css/eln_report.scss',
            '/lerm_civil/static/src/css/data_sheet_styles.scss',

        ],
    'web.assets_qweb': [
    ],
        }
}
