from collections import defaultdict

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

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

    @api.onchange("additional_seniority_in_months")
    def _onchange_additional_seniority_in_months(self):
        if self.additional_seniority_in_months:
            self.additional_seniority_in_years = (
                self.additional_seniority_in_years
                + self.additional_seniority_in_months // 12
            )
            self.additional_seniority_in_months = (
                self.additional_seniority_in_months % 12
            )

    def _compute_seniority(self):
        for employee in self:
            if not employee.start_work_date:
                employee.seniority_in_years = 0
                employee.seniority_in_months = 0
                continue
            if employee.seniority_type == "by_month":
                today = fields.Date.today()
                start_work_date = employee.start_work_date

                months = (
                    (today.year - start_work_date.year) * 12
                    + today.month
                    - start_work_date.month
                )
                years = months // 12
                months = months % 12
            elif employee.seniority_type == "by_attendance":
                today = fields.Date.today()
                start_work_date = employee.start_work_date

                attendance_data = self._get_monthly_attendance(
                    employee, start_work_date, today
                )

                valid_months = 0
                for days_worked in attendance_data.values():
                    if days_worked >= 13:
                        valid_months += 1

                years = valid_months // 12
                months = valid_months % 12
            if employee.additional_seniority:
                total_months = months + employee.additional_seniority_in_months
                years += employee.additional_seniority_in_years + total_months // 12
                months = total_months % 12
            employee.seniority_in_years = years
            employee.seniority_in_months = months

    def _get_monthly_attendance(self, employee_id, start_date, end_date):
        attendance_summary = defaultdict(int)

        user_tz = pytz.timezone(self.env.user.tz or "UTC")
        start_date = (
            fields.Datetime.to_datetime(start_date)
            .replace(tzinfo=user_tz)
            .astimezone(pytz.utc)
        )
        end_date = (
            fields.Datetime.to_datetime(end_date)
            .replace(tzinfo=user_tz)
            .astimezone(pytz.utc)
        )

        domain = [
            ("employee_id", "=", employee_id.id),
            ("check_in", ">=", start_date),
            ("check_in", "<=", end_date),
        ]
        aggregated_data = self.env["hr.attendance"].read_group(
            domain, ["check_in"], ["check_in:month"]
        )

        for data in aggregated_data:
            month = data["check_in:month"]
            count = data["check_in_count"]
            attendance_summary[month] = count

        return attendance_summary

    def write(self, vals):
        if "clothing_code_id" in vals:
            new_clothing_code = self.env["hr.clothing.code"].browse(
                vals["clothing_code_id"]
            )
            if new_clothing_code:
                if self.clothing_code_id:
                    self.clothing_code_id.write({"employee_id": False})
                if new_clothing_code.employee_id != self:
                    new_clothing_code.write({"employee_id": self.id})
        if "additional_seniority_in_years" in vals:
            if vals["additional_seniority_in_years"] < 0:
                raise ValidationError(_("Seniority must be greater than or equal to 0"))
        if "additional_seniority_in_months" in vals:
            if vals["additional_seniority_in_months"] < 0:
                raise ValidationError(_("Seniority must be greater than or equal to 0"))
            vals["additional_seniority_in_years"] = (
                vals.get("additional_seniority_in_years", 0)
                + vals.get("additional_seniority_in_months", 0) // 12
            )
            vals["additional_seniority_in_months"] = (
                vals.get("additional_seniority_in_months", 0) % 12
            )
        return super().write(vals)

    def generate_random_barcode(self):
        for employee in self:
            if employee.company_id:
                acronym = (
                    employee.company_id.acronym.upper()
                    if employee.company_id.acronym
                    else ""
                )
                sequence_code = f"employee.sequence.{employee.company_id.id}"
                sequence = self.env["ir.sequence"].search(
                    [("code", "=", sequence_code)], limit=1
                )
                if not sequence:
                    sequence = self.env["ir.sequence"].create(
                        {
                            "name": f"Employee Sequence for {employee.company_id.name}",
                            "code": sequence_code,
                            "prefix": acronym + ".",
                            "padding": 6,
                            "number_next": 1,
                            "company_id": employee.company_id.id,
                            "implementation": "no_gap",
                        }
                    )
                max_employee_barcode = self.env["hr.employee"].search(
                    [
                        ("company_id", "=", employee.company_id.id),
                        ("barcode", "like", sequence.prefix + "%"),
                    ],
                    limit=1,
                    order="barcode desc",
                )
                if max_employee_barcode:
                    current_max_number = int(
                        max_employee_barcode.barcode.split(".")[-1]
                    )
                    next_number = current_max_number + 1
                    if next_number > sequence.number_next:
                        sequence.number_next = next_number
                employee.barcode = sequence.next_by_id()

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if "clothing_code_id" in vals:
            clothing_code_id = self.env["hr.clothing.code"].browse(
                vals.get("clothing_code_id", False)
            )
            if (
                clothing_code_id.employee_id
                and clothing_code_id.employee_id.id != self.id
            ):
                raise ValidationError(
                    _("Clothing code has been assigned to another employee")
                )
            elif not clothing_code_id.employee_id:
                clothing_code_id.write({"employee_id": res.id})
        return res
