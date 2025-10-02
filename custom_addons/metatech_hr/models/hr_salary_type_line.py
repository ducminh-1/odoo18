from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HRSalaryTypeLine(models.Model):
    _name = "hr.salary.type.line"
    _description = "Salary Type Line"

    sequence = fields.Integer(default=10)
    contract_id = fields.Many2one(
        "hr.contract", string="Contract", ondelete="cascade", copy=False
    )
    salary_type_id = fields.Many2one(
        "hr.salary.type", string="Salary Type", ondelete="restrict", required=True
    )
    amount = fields.Monetary(required=True)
    currency_id = fields.Many2one(
        string="Currency", related="contract_id.currency_id", readonly=True
    )

    @api.constrains("amount")
    def _check_salary_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_("Salary amount must be greater than 0."))

    @api.model
    def create(self, values):
        res = super().create(values)
        if res:
            total_salary = self._get_total_salary(res)
            self._create_tracking(res, res.salary_type_id, 0, res.amount, total_salary)
        return res

    def write(self, values):
        for rec in self:
            total_salary = self._get_total_salary(rec)
            old_amount = rec.amount
            old_salary_type = rec.salary_type_id

            amount_changed = self._is_amount_changed(values, rec)
            salary_type_changed = self._is_salary_type_changed(values, rec)

            # Handles the case of changing both amount and salary_type_id
            if amount_changed and salary_type_changed:
                self._create_tracking(rec, old_salary_type, old_amount, 0, total_salary)
                new_salary_type = self.env["hr.salary.type"].browse(
                    values.get("salary_type_id")
                )
                self._create_tracking(
                    rec, new_salary_type, 0, values.get("amount", 0), total_salary
                )
            # Handles the case of changing amount
            elif amount_changed:
                self._create_tracking(
                    rec,
                    old_salary_type,
                    old_amount,
                    values.get("amount", 0),
                    total_salary,
                )
            # Handles the case of changing salary_type_id
            elif salary_type_changed:
                # Tracking for old salary_type_id
                self._create_tracking(rec, old_salary_type, old_amount, 0, total_salary)
                new_salary_type = self.env["hr.salary.type"].browse(
                    values.get("salary_type_id")
                )
                # Tracking for new salary_type_id
                self._create_tracking(rec, new_salary_type, 0, old_amount, total_salary)
        return super().write(values)

    def _get_total_salary(self, rec):
        if rec.contract_id.wage_type == "monthly":
            return rec.contract_id.wage
        elif rec.contract_id.wage_type == "hourly":
            return rec.contract_id.hourly_wage
        return 0

    def _is_amount_changed(self, values, rec):
        return "amount" in values and values.get("amount") != rec.amount

    def _is_salary_type_changed(self, values, rec):
        return (
            "salary_type_id" in values
            and values.get("salary_type_id") != rec.salary_type_id.id
        )

    def _create_tracking(self, rec, salary_type, old_value, new_value, total_salary):
        self.env["salary.type.tracking"].sudo().create(
            {
                "contract_id": rec.contract_id.id,
                "employee_id": rec.contract_id.employee_id.id,
                "salary_type_id": salary_type.id,
                "salary_type_line": rec.id,
                "old_value": old_value,
                "new_value": new_value,
                "policy_id": rec.contract_id.policy_id.id,
                "total_salary": total_salary,
                "currency_id": rec.contract_id.currency_id.id,
            }
        )

    def unlink(self):
        for rec in self:
            total_salary = self._get_total_salary(rec)
            self._create_tracking(rec, rec.salary_type_id, rec.amount, 0, total_salary)
        return super().unlink()
