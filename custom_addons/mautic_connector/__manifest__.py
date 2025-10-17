{
    "name": "Connect Mautic",
    "summary": "Mautic Connection and Sync Leads",
    "version": "18.0.0.0.1",
    "author": "NOS ERP Consulting",
    "website": "https://www.nostech.vn",
    "license": "LGPL-3",
    "category": "Customized Module",
    # any module necessary for this one to work correctly
    "depends": ["base", "mail", "crm"],
    # always loaded
    "data": [
        # Data
        "data/utm_source.xml",
        "data/ir_config_parameter.xml",
        "data/ir_cron.xml",
        # Security
        "security/ir.model.access.csv",
        # # View
        "views/mautic_migrate_config_views.xml",
        "views/mautic_segment.xml",
        # # Wizard
        "wizard/mautic_confirm_migration_views.xml",
        # # Menu
        "menu/mautic_menu.xml",
    ],
    "application": True,
    "installable": True,
}
