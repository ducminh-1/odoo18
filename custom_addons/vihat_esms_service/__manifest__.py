{
    "name": "VIHAT eSMS Service",
    "summary": "Integration to third-party sms service",
    "author": "NOS ERP Consulting",
    "license": "LGPL-3",
    "website": "https://www.nostech.vn",
    "category": "",
    "version": "18.0.0.0.1",
    # any module necessary for this one to work correctly
    "depends": [
        "sms",
        "helpdesk",
        "account_followup",
        "nsv_customize",
        "helpdesk_sms",
    ],
    # always loaded
    "data": [
        # data
        "data/ir_config_parameter.xml",
        "data/zalo_oa.xml",
        "data/ir_cron.xml",
        "security/ir.model.access.csv",
        "views/sms_templates.xml",
        "views/sms_brandname_views.xml",
        "wizards/vihat_send_sms_wizard_views.xml",
        "views/helpdesk_ticket_views.xml",
        "views/sms_sms_views.xml",
        # TODO: upgrade 18.0 like in thu/chi
        # 'views/account_payment_statement_views.xml',
        "views/stock_views.xml",
        "views/brand_name_views.xml",
        "views/sale_order_views.xml",
        "views/res_config_setting_views.xml",
        "views/ir_ui_view.xml",
        "views/zalo_oa_views.xml",
        "views/birthday_coupon_templates.xml",
        # Menu
        "menu/menu.xml",
    ],
    "installable": True,
    "application": True,
    "sequence": 2,
}
