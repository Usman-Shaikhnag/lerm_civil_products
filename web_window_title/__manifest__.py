# -*- coding: utf-8 -*-
{
    'license': 'LGPL-3',
    'name': "Web Window Title",
    'summary': "The custom web window title",
    'author': "renjie <i@renjie.me>",
    'website': "https://renjie.me",
    'support': 'i@renjie.me',
    'category': 'Extra Tools',
    'version': '1.1',
    'depends': ['base_setup','base','mail','auth_signup', 'web' ],
    'demo': [
        'data/demo.xml',
    ],
    'data': [
        'views/res_config.xml',
        'data/email_template.xml',
        'data/new_user_template.xml'

    ],
    'images': [
        'static/description/main_screenshot.png',
    ],
    'assets': {
        'web.assets_backend': [
            'web_window_title/static/src/js/web_window_title.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}