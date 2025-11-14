{
    "name": "Document Department",
    "version": "18.0.1.0.0",
    "author": "NOS ERP Consulting",
    "category": "Productivity/Documents",
    "maintainer": ["tinnguyen189atnos"],
    "license": "OPL-1",
    "website": "https://www.nostech.vn",
    "depends": ["web", "documents", "hr"],
    "data": [
        "views/documents_document_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "nos_document_department/static/src/js/document_department.esm.js",
            "nos_document_department/static/src/views/document_inspector.xml",
        ],
    },
    "installable": True,
}
