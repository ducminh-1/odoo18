{
    "name": "Document Dates",
    "version": "18.0.1.0.0",
    "author": "NOS ERP Consulting",
    "category": "Productivity/Documents",
    "maintainer": ["tinnguyen189atnos"],
    "license": "OPL-1",
    "website": "https://www.nostech.vn",
    "depends": ["web", "documents"],
    "data": [
        "data/ir_cron_data.xml",
        "views/documents_document_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "nos_document_dates/static/src/**/*",
        ],
    },
    "installable": True,
}
