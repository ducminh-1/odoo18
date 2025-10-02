from odoo import api, fields, models


class HrStaffingPlan(models.Model):
    _name = "hr.staffing.plan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Staffing Plan"

    name = fields.Char(stringrequired=True)
    date_from = fields.Date(string="From Date", required=True, tracking=True)
    date_to = fields.Date(string="To Date", required=True, tracking=True)
    department_id = fields.Many2one("hr.department", required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("rejected", "Rejected"),
            ("confirmed", "Confirmed"),
            ("done", "Done"),
        ],
        default="draft",
        readonly=True,
        tracking=True,
    )
    line_ids = fields.One2many(
        "hr.staffing.plan.line", "staffing_plan_id", string="Staffing Plan Lines"
    )
    confirmed_by = fields.Many2one("res.users", readonly=True)
    confirmed_date = fields.Datetime(readonly=True)
    rejected_by = fields.Many2one("res.users", readonly=True)
    rejected_date = fields.Datetime(readonly=True)
    done_by = fields.Many2one("res.users", readonly=True)
    done_date = fields.Datetime(readonly=True)
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )

    def action_draft(self):
        self.write({"state": "draft"})

    def action_reject(self):
        self.write(
            {
                "state": "rejected",
                "rejected_by": self.env.user.id,
                "rejected_date": fields.Datetime.now(),
            }
        )

    def action_confirm(self):
        self.write(
            {
                "state": "confirmed",
                "confirmed_by": self.env.user.id,
                "confirmed_date": fields.Datetime.now(),
            }
        )

    def action_done(self):
        self.write(
            {
                "state": "done",
                "done_by": self.env.user.id,
                "done_date": fields.Datetime.now(),
            }
        )


class HrStaffingPlanLine(models.Model):
    _name = "hr.staffing.plan.line"
    _description = "Staffing Plan Line"

    sequence = fields.Integer()
    department_id = fields.Many2one("hr.department")
    staffing_plan_id = fields.Many2one("hr.staffing.plan", ondelete="cascade")
    job_id = fields.Many2one("hr.job", required=True)
    no_of_positions = fields.Integer(string="No. of Positions", required=True)
    actual_no_of_positions = fields.Integer(string="Actual No. of Positions")
    estimated_cost = fields.Monetary(required=True)
    actual_cost = fields.Monetary()
    amount = fields.Monetary(compute="_compute_amount", store=True)
    difference = fields.Monetary(compute="_compute_difference", store=True)
    difference_percentage = fields.Float(
        compute="_compute_difference",
        store=True,
    )
    responsible_id = fields.Many2one("res.users")
    notes = fields.Text()
    currency_id = fields.Many2one(
        "res.currency", related="staffing_plan_id.currency_id"
    )

    @api.depends("no_of_positions", "estimated_cost")
    def _compute_amount(self):
        for line in self:
            line.amount = line.no_of_positions * line.estimated_cost

    @api.depends("actual_no_of_positions", "actual_cost")
    def _compute_difference(self):
        for line in self:
            if line.actual_no_of_positions and line.actual_cost:
                line.difference = (
                    line.actual_no_of_positions * line.actual_cost
                ) - line.amount
                if line.amount:
                    line.difference_percentage = line.difference / line.amount
                else:
                    line.difference_percentage = 0.0
            else:
                line.difference = 0.0
                line.difference_percentage = 0.0
