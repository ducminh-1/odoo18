{
    "name": "HR - Import Payslip",
    "version": "18.0.0.1.1",
    "summary": "HR - Import Payslip",
    "license": "OEEL-1",
    "sequence": 18,
    "website": "https://www.nostech.vn",
    "depends": ["hr", "hr_payroll_community"],
    "author": "NOS ERP Consulting",
    "maintainers": ["tinnguyen189atnos"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/hr_payslip_import_views.xml",
        "views/hr_payslip_run_views.xml",
        "views/hr_payslip_views.xml",
    ],
    "installable": True,
    "application": True,
}
