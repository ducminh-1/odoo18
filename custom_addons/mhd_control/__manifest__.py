# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{

    "name": "MHD Control",
    "version": "1.0",
    "currency": 'VND',
    "summary": "MHD Control",
    'sequence': -99,
    "category": "Industries",
    "description": "Xây dựng hàm MHD Valuation",
    "depends": [
        'mail',
        'project',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/project.xml',
        # 'wizard/tao_hop_dong.xml',
    ],
    "author": "Mr Ánh",
    "website": "https://sinhvienthamdinh.com",
    "installable": True,
    "application": True,
    "auto_install": False,
    "images": ["static/src/img/mhdvaluation.png"],

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
