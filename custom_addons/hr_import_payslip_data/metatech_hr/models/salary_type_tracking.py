from odoo import fields, models


class SalaryTypeTracking(models.Model):
    _name = "salary.type.tracking"
    _description = "Salary Type Tracking"

    contract_id = fields.Many2one(
        "hr.contract", string="Contract", ondelete="cascade", copy=False
    )
    salary_type_line = fields.Many2one("hr.salary.type.line", copy=False)
    old_value = fields.Monetary(string="Old Amount")
    new_value = fields.Monetary(string="New Amount")
    currency_id = fields.Many2one(
        string="Currency", related="contract_id.currency_id", readonly=True
    )
    salary_type_id = fields.Many2one("hr.salary.type", string="Salary Type")
    employee_id = fields.Many2one("hr.employee", string="Employee")
    policy_id = fields.Many2one(
        "hr.policy", string="Policy", related="contract_id.policy_id", readonly=True
    )
    total_salary = fields.Monetary(
        string="Total Salary", related="contract_id.wage", readonly=True
    )
    contract_code = fields.Char(
        string="Contract Code", related="contract_id.name", readonly=True
    )
    department_id = fields.Many2one(
        "hr.department",
        string="Department",
        related="contract_id.department_id",
        readonly=True,
    )
    job_id = fields.Many2one(
        "hr.job", string="Job Position", related="contract_id.job_id", readonly=True
    )
    date_start = fields.Date(
        string="Start Date", related="contract_id.date_start", readonly=True
    )
    date_end = fields.Date(
        string="End Date", related="contract_id.date_end", readonly=True
    )
    contract_type_id = fields.Many2one(
        "hr.contract.type",
        string="Contract Type",
        related="contract_id.contract_type_id",
        readonly=True,
    )
    contract_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("open", "Open"),
            ("close", "Closed"),
            ("cancel", "Cancelled"),
        ],
        string="Contract State",
        related="contract_id.state",
        readonly=True,
    )
