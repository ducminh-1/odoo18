{
    "name": "Sync Data VaoBep App",
    "version": "18.0.1.0.0",
    "category": "General",
    "author": "NOS ERP Consulting",
    "website": "https://www.nostech.vn",
    "license": "AGPL-3",
    "summary": """
Custom for Nguon Song Viet
        """,
    "depends": [
        "base",
        "web",
        "website",
        "crm",
        "helpdesk",
        "partner_address_vn_base",
        "vihat_esms_service",
    ],
    "data": [
        #     # Views
        #     'views/assets.xml',
        "views/guarantee_registers_views.xml",
        "views/templates.xml",
        "views/res_partner_views.xml",
        "views/res_config_settings_views.xml",
        # Menu
        # Security
        "security/ir.model.access.csv",
        # Data
        "data/ir_config_param.xml",
        # Report
    ],
    "assets": {
        "web.assets_frontend": [
            "nsv_sync_crm_vaobep/static/src/js/guarantee-registers.js"
        ],
        # 'web.assets_qweb': [
        #     'sync_data_vbapp/static/src/xml/**/*',
        # ],
    },
    "installable": True,
    "auto_install": False,
    "application": True,
    "sequence": 5,
}
