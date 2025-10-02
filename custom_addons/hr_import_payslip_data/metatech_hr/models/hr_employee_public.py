import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    id_card_issue_date = fields.Date(string="Identity card issue date")
    place_of_issue_id_card = fields.Char(string="Place of issue of ID card")
    tax_code = fields.Char(string="Tax code")
    ethnicity_id = fields.Many2one("hr.ethnicity", string="Ethnicity")
    dependent_ids = fields.One2many(
        comodel_name="hr.dependent",
        inverse_name="employee_id",
        string="Dependents",
        tracking=True,
    )

    clothing_code_id = fields.Many2one(
        "hr.clothing.code", ondelete="set null", tracking=True
    )
    salary_type_tracking = fields.One2many(
        comodel_name="salary.type.tracking",
        inverse_name="employee_id",
    )
    start_work_date = fields.Date(string="Start work date", required=True)
    seniority_type = fields.Selection(
        [
            ("by_attendance", "By Attendance"),
            ("by_month", "By Month"),
        ],
        default="by_attendance",
        required=True,
    )
    additional_seniority = fields.Boolean(default=False)
    additional_seniority_in_years = fields.Integer(
        string="Additional Seniority in years", default=0
    )
    additional_seniority_in_months = fields.Integer(
        string="Additional Seniority in months", default=0
    )
    seniority_in_years = fields.Integer(
        string="Seniority", compute="_compute_seniority"
    )
    seniority_in_months = fields.Integer(
        string="Seniority in months", compute="_compute_seniority"
    )
