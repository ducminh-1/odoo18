{
    "name": "VIHAT eSMS Rating",
    "summary": "Integration to third-party sms service",
    "author": "NOS ERP Consulting",
    "website": "https://www.nostech.vn",
    "license": "LGPL-3",
    "category": "",
    "version": "18.0.0.0.1",
    # any module necessary for this one to work correctly
    "depends": ["vihat_esms_service", "rating", "link_tracker", "web"],
    # always loaded
    "data": [
        # data
        # security
        "security/security.xml",
        # 'security/ir.model.access.csv',
        # view
        # 'views/assets.xml',
        "views/rating_templates.xml",
        "views/sms_templates.xml",
        "views/sms_brandname_views.xml",
        "views/link_tracker_views.xml",
        "views/helpdesk_views.xml",
        "views/rating_views.xml",
        # Menu
        "menu/menu.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "vihat_esms_rating/static/src/scss/rating.scss",
            "vihat_esms_rating/static/src/js/rating_form.js",
        ],
    },
    "installable": True,
    "application": True,
    "sequence": 2,
}
