# -*- coding: utf-8 -*-
##############################################################################
{
    'name': 'Vietnam Address Information',
    'summary': """
Adding and manage address infomation in Vietnam
""",
    'description': """
- Adding Vietnam address: ward, district, city
- Customize module Contacts to manage address information based on Vietnam address.
    """,
    'author': 'Vmax - Erp Consulting',
    'version': '18.0.0.1',
    'license': 'OPL-1',
    'support': 'support@vmax.vn',
    'images': [
        'static/description/cover.png'
    ],
    'depends': [
        'base',
        # 'base_address_city',
        'base_address_extended',
        'contacts'
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # View
        'views/res_bank.xml',
        'views/res_city.xml',
        'views/res_company.xml',
        'views/res_district.xml',
        'views/res_partner.xml',
        'views/res_ward.xml',
        # Menu
        'menu/menu.xml',
    ],
    'post_init_hook': '_install_init_data',
    'auto_install': False,
    'installable': True,
    'category': 'Sales/CRM',
    'application': True,
    'sequence': 10,
}
