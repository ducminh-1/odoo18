{
    'name': 'Approvals Community',
    'version': '18.0.1.0.0',
    'category': 'Approvals',
    'summary': 'Approval Process Management - Community Version',
    'description': """
        Manage approval processes for various business needs.
        This module provides a complete approval workflow system similar to Odoo Enterprise.
    """,
    'author': 'Minh Le',
    'website': 'https://www.nostech.vn',
    'depends': ['base', 'mail', 'hr'],
    'data': [
        'security/approvals_security.xml',
        'security/ir.model.access.csv',
        'data/approvals_data.xml',
        'views/approval_category_views.xml',
        'views/approval_request_views.xml',
        'views/menus.xml',
    ],
    'assets': {},
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}