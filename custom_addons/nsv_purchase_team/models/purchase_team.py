from odoo import api, fields, models


class PurchaseTeam(models.Model):
    _name = "purchase.team"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin"]
    _description = "purchase team"
    _check_company_auto = True

    @api.model
    @api.returns("self", lambda value: value.id if value else False)
    def _get_default_team_id(self, user_id=None, domain=None):
        if not user_id:
            user_id = self.env.uid
        team_id = self.env["purchase.team"].search(
            [
                "|",
                ("user_id", "=", user_id),
                ("member_ids", "=", user_id),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        if not team_id and "default_team_id" in self.env.context:
            team_id = self.env["purchase.team"].browse(
                self.env.context.get("default_team_id")
            )
        if not team_id:
            team_id = self.env["purchase.team"]
        return team_id

    name = fields.Char(required=True)
    user_id = fields.Many2one("res.users", string="Team Leader", check_company=True)
    member_ids = fields.Many2many(
        "res.users",
        "purchase_team_user_rel",
        "purchase_team_id",
        "user_id",
        string="Team Members",
        check_company=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        index=True,
    )
    active = fields.Boolean(
        default=True,
        help="If the active field is set to false, it will allow you to hide the Purchase Team without removing it.",  # noqa: E501
    )

    # def _track_subtype(self, init_values):
    #     self.ensure_one()
    #     if "state" in init_values and self.state == "purchase":
    #         return self.env.ref("nsv_purchase_team.mt_rfq_new_confirmed")
    #     elif "state" in init_values and self.state == "to approve":
    #         return self.env.ref("nsv_purchase_team.mt_rfq_new_confirmed")
    #     elif "state" in init_values and self.state == "done":
    #         return self.env.ref("nsv_purchase_team.mt_rfq_new_done")
    #     return super()._track_subtype(init_values)
