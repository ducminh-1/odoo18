{
    "name": "VOIP Omicall",
    "summary": "VOIP ",
    "version": "18.0.1.0.0",
    "author": "NOS ERP Consulting",
    "website": "http://www.vmax.vn",
    "license": "OEEL-1",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Customized Module",
    # any module necessary for this one to work correctly
    "depends": ["base", "contacts"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/voip_call_log_views.xml",
        "views/res_partner_views.xml",
    ],
    # only loaded in demonstration mode
    "demo": [],
    "application": True,
    "installable": True,
    "sequence": 2,
}
