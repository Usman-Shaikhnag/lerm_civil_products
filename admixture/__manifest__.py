{
    'name': 'Admixture',
    'version': '1.2',
    'category': 'Lerm Civil',
    'summary': 'Sales internal machinery',
    'description': """
This module contains all the common features of Sales Management and eCommerce.
    """,
    'depends': ['base','sale','lerm_civil'],
    'data': [
               'security/ir.model.access.csv',
               'views/admixture.xml',
               'reports/admixture_datasheet.xml',
               'reports/admixture_report.xml'
    ],

    
  
    'installable': True,
    'auto_install': False,
   
}