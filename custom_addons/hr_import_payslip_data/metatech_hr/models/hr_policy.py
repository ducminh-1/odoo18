from odoo import _, fields, models
from odoo.exceptions import ValidationError


class HRPolicy(models.Model):
    _name = "hr.policy"
    _description = "Policy"

    sequence = fields.Integer(default=10)
    name = fields.Char()
    contract_ids = fields.One2many("hr.contract", "policy_id", string="Contracts")

    def unlink(self):
        for policy in self:
            if policy.contract_ids:
                raise ValidationError(
                    _(
                        "You cannot delete this policy because it is linked to one or more contracts."  # noqa: E501
                    )
                )
        return super().unlink()
