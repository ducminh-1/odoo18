# -*- coding: utf-8 -*-
##############################################################################
{
    'name': 'CRM - Vietnam Address Information',
    'summary': """
Adding and manage address infomation in Vietnam
""",
    'description': """
- Customize CRM to manage leads address information based on Vietnam address.
    """,
    'author': 'Vmax - Erp Consulting',
    'version': '18.0.0.1',
    'license': 'OPL-1',
    'price': 9.99,
    'currency': 'USD',
    'support': 'support@vmax.vn',
    'images': [
        'static/description/cover.png'
    ],
    'depends': ['partner_address_vn_base', 'crm'],
    'data': [
        'views/crm_views.xml'
    ],
    'auto_install': False,
    'installable': True,
    'category': 'Sales/CRM',
    'application': True,
    'sequence': 10,
}
