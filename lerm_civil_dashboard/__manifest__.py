{
    "name": "Lerm Civil Dashboard",
    'summary': """Lerm Dashboard""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Esehat",
    "version": "17.0.1.0.0",
    "category":"Lerm Civil",
    "depends": ["web","base","lerm_civil"],
    "data": [
        "views/dashboard.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.5.0/chart.min.js",
            'https://cdn.jsdelivr.net/npm/chart.js',
            # 'lerm_civil_dashboard/static/src/components/chart_renderer/chart_renderer.js',
            # 'lerm_civil_dashboard/static/src/components/chart_renderer/chart_renderer.xml',
            # 'lerm_civil_dashboard/static/src/components/kpi_box/kpi_box.js', 
            # 'lerm_civil_dashboard/static/src/components/main_dashboard/main_dashboard.js', 
            # 'lerm_civil_dashboard/static/src/components/main_dashboard/main_dashboard.xml',
            # 'lerm_civil_dashboard/static/src/components/kpi_box/kpi_box.xml',
            "lerm_civil_dashboard/static/src/components/**/*.js",
            "lerm_civil_dashboard/static/src/components/**/*.xml",
            'lerm_civil_dashboard/static/src/css/dashboard_styles.css',
        ],
    },
}
