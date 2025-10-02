{
    "name": "Viettel Invoice Import",
    "version": "1.0.0",
    "summary": "",
    "author": "Minh Le",
    "category": "Purchase/Vendor Bills",
    "depends": ["base", "purchase", "product"],
    "data": [
    "security/ir.model.access.csv",
    "data/cron.xml",
    "views/invoice_sync_views.xml",
    ],
    "installable": True,
}