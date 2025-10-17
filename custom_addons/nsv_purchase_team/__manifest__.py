{
    "name": "NSV - Purchase Team Allocation",
    "version": "18.0.1.0.0",
    "license": "OEEL-1",
    "summary": "App Purchase Team Purchase analysis Team analysis for team in purchase report purchase team analysis purchase team reports team allocation in purchase Purchase Indent purchase user allocation purchase team report specific team for purchase order",  # noqa: E501
    "author": "NOS ERP Consulting",
    "website": "https://www.nostech.vn",
    "maintainer": ["tinnguyen189atnos"],
    "depends": ["base", "purchase"],
    "data": [
        "security/ir.model.access.csv",
        "security/purchase_team_security.xml",
        "data/mail_message_subtype.xml",
        "views/purchase_team_views.xml",
        "views/purchase_order_views.xml",
        "report/purchase_report_views.xml",
    ],
    "category": "Purchase",
    "application": True,
    "sequence": 3,
}
