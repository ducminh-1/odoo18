# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{

    "name": "MHD Data Old",
    "version": "1.0",
    "currency": 'VND',
    "summary": "MHD Control",
    'sequence': -99,
    "category": "Industries",
    "description": "Dữ liệu giá MHD từ 2016 - 2021",
    "depends": [
        'mail',
        # 'analytic',
        'web_google_maps',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/data_old.xml',
    ],
    "author": "Mr Ánh",
    "website": "https://sinhvienthamdinh.com",
    "installable": True,
    "application": True,
    "auto_install": False,
    "images": ["static/src/img/mhdvaluation.png"],

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
