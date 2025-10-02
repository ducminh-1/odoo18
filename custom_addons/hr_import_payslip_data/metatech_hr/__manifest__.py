{
    "name": "Metatech Human Resources",
    "version": "1.0",
    "author": "Metatech Solutions JSC",
    "website": "http://metatechsolutions.vn/",
    "depends": [
        "hr",
        "hr_holidays",
        # "hr_payroll",
        "hr_contract",
        "hr_skills",
        "hr_attendance",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/contract_sequence.xml",
        # "data/hr.ethnicity.csv",
        "data/hr_resume_data.xml",
        "views/hr_views.xml",
        "views/hr_poliy_views.xml",
        "views/hr_contract_views.xml",
        "views/hr_salary_type_views.xml",
        "views/hr_clothing_code_views.xml",
        "views/res_company_views.xml",
        "views/hr_ethnicity_views.xml",
        "views/hr_applicant_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "metatech_hr/static/src/fields/**/*",
        ],
    },
    "license": "OEEL-1",
}
