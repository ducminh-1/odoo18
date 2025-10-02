import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HRContract(models.Model):
    _inherit = "hr.contract"

    name = fields.Char("Contract Reference", required=False)
    is_expiring_soon = fields.Boolean(compute="_compute_is_expiring_soon", store=True)
    policy_id = fields.Many2one(
        "hr.policy", string="Policy", tracking=True, ondelete="restrict"
    )
    hr_salary_type_line = fields.One2many(
        comodel_name="hr.salary.type.line",
        inverse_name="contract_id",
        string="Salary Type Lines",
        copy=True,
        auto_join=True,
        required=True,
    )
    salary_type_tracking = fields.One2many(
        comodel_name="salary.type.tracking",
        inverse_name="contract_id",
    )
    hourly_wage = fields.Monetary(
        tracking=True,
        help="Employee's hourly gross wage.",
        compute="_compute_total_salary", store=True
    )
    wage = fields.Monetary(
        required=True,
        tracking=True,
        help="Employee's monthly gross wage.",
        group_operator="avg",
        compute="_compute_total_salary", store=True
    )
    is_ssnid = fields.Boolean("SSNID", tracking=True)
    is_ssnid_only = fields.Boolean("SSNID Only", tracking=True)
    is_trade_union = fields.Boolean("Trade Union", tracking=True)

    luong_co_ban_bhxh = fields.Monetary(tracking=True)
    phu_cap_tien_an = fields.Monetary(tracking=True)
    phu_cap_xang_xe = fields.Monetary(tracking=True)
    phu_cap_khac = fields.Monetary(tracking=True)
    wage_type = fields.Selection([('monthly','Monthly'), ('hourly', 'Hourly')], string="Wage Type", store=True)

    @api.depends(
        "hr_salary_type_line",
        "hr_salary_type_line.salary_type_id",
        "hr_salary_type_line.amount",
        "wage_type",
        "luong_co_ban_bhxh",
        "phu_cap_tien_an",
        "phu_cap_xang_xe",
        "phu_cap_khac",
    )
    def _compute_total_salary(self):
        for rec in self:
            wage = 0
            # if len(rec.hr_salary_type_line) > 0:
            wage = sum(rec.hr_salary_type_line.mapped("amount"))
            wage += (rec.luong_co_ban_bhxh or 0.0) + (rec.phu_cap_tien_an or 0.0) + (rec.phu_cap_xang_xe or 0.0) + (rec.phu_cap_khac or 0.0)
            if rec.wage_type == "monthly":
                rec.wage = wage
                rec.hourly_wage = 0
            if rec.wage_type == "hourly":
                rec.hourly_wage = wage
                rec.wage = 0

    @api.depends("date_end", "company_id.contract_expiration_notice_period")
    def _compute_is_expiring_soon(self):
        for record in self.search([]):
            if record.date_end and record.company_id.contract_expiration_notice_period:
                expiration_date = record.date_end - timedelta(
                    days=record.company_id.contract_expiration_notice_period
                )
                record.is_expiring_soon = (
                    record.date_end > fields.Date.today() >= expiration_date
                )
            else:
                record.is_expiring_soon = False

    @api.model
    def update_state(self):
        res = super().update_state()
        if res:
            self._compute_is_expiring_soon()
        return res

    @api.model
    def create(self, vals):
        if len(vals.get("hr_salary_type_line", [])) == 0:
            raise ValidationError(
                _(
                    "You must enter complete information: Salary type and amount (Amount must be greater than 0)."  # noqa: E501
                )
            )
        if "name" not in vals or not vals["name"]:
            sequence = self.env["ir.sequence"].next_by_code("hr.contract")
            vals["name"] = sequence
        return super().create(vals)
