import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    pricelist_approver_ids = fields.One2many(
        "pricelist.approver", "company_id", string="Pricelist Approvers"
    )


class PricelistApprover(models.Model):
    _name = "pricelist.approver"
    _description = "Pricelist Approvers"
    _rec_name = "user_id"
    _order = "sequence"
    _check_company_auto = True

    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        ondelete="cascade",
        required=True,
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one(
        "res.users",
        string="User",
        ondelete="cascade",
        required=True,
        domain="[('id', 'not in', existing_user_ids)]",
        check_company=True,
    )
    required = fields.Boolean(default=True)

    existing_user_ids = fields.Many2many(
        "res.users", compute="_compute_existing_user_ids"
    )

    @api.depends("company_id")
    def _compute_existing_user_ids(self):
        for record in self:
            record.existing_user_ids = record.company_id.pricelist_approver_ids.mapped(
                "user_id"
            )
