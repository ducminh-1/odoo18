# -*- coding: utf-8 -*-
{
    'name': 'MHD Maps',
    'version': '1.0.0',
    'author': 'Anh_Le',
    'license': 'AGPL-3',
    'maintainer': 'Le Anh<lnanh81@gmail.com>',
    'support': 'lnanh81@gmail.com',
    'category': 'Industries',
    'description': """
MHD Maps
========

Thêm chế độ xem bản đồ cho Datalist
""",
    'depends': ['web_google_maps', 'mhd_valuation'],
    'website': '',
    'data': [
        'views/mhd_datalist_maps.xml',
        'views/project.xml',
        # 'views/res_partner.xml',
    ],
    'demo': [],
    'installable': True
}
