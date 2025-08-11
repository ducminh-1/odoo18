# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{

    "name": "MHD Valuation",
    "version": "1.0",
    "currency": 'VND',
    "summary": "MHD Valuation",
    'sequence': -100,
    "category": "Industries",
    "description": "Phầm mềm quản lý MHD Valuation",
    "depends": [
        'mail',
        'project',
        # 'sale',
        'base',
        'mhd_unicode',
    ],
    "data": [
        'security/ir.model.access.csv',
        'security/mhd_security.xml',
        'views/templates.xml',
        'views/datalist.xml',
        'views/res_partner_views.xml',
        'views/cau_hinh.xml',
        'views/real_estate_draft.xml',
        'views/hopdong.xml',
        'views/chungthu.xml',
        'data/hopdong.xml',
        'data/mail_template.xml',
        'report/report.xml',
        'report/real_estate_draft.xml',
        'report/data_list.xml',
        'views/project.xml',
        'views/thanhtoan.xml',
        'wizard/tao_hop_dong.xml',
        'wizard/tao_chung_thu.xml',
    ],
    "author": "Mr Ánh",
    "website": "https://sinhvienthamdinh.com",
    "installable": True,
    "application": True,
    "auto_install": False,
    "images": ["static/src/img/mhdvaluation.png"],

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
