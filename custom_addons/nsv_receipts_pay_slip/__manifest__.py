{
    "name": "NSV - Phiếu thu chi",
    "version": "18.0.1.1.0",
    "category": "General",
    "author": "NOS ERP Consulting",
    "website": "https://www.nostech.vn",
    "license": "AGPL-3",
    "summary": """
Bản in phiếu thu - chi tiền mặt""",
    "depends": ["base", "account", "account_accountant", "nsv_customize"],
    "data": [
        # data
        "data/ir.sequence.data.xml",
        # Views
        "views/account_journal_view.xml",
        "views/account_payment_statement_views.xml",
        "report/report_receipts_pay_slip.xml",
        # Menu
        # Security
    ],
    "assets": {
        "web.assets_backend": [
            "nsv_receipts_pay_slip/static/src/**/*",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": True,
    "sequence": 2,
}
