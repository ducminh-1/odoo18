from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    add_repair_src_location_id = fields.Many2one(
        "stock.location",
        string="Add Part From Location",
        related="company_id.add_repair_src_location_id",
        readonly=False,
    )
    add_repair_des_location_id = fields.Many2one(
        "stock.location",
        string="Add Part To Location",
        related="company_id.add_repair_des_location_id",
        readonly=False,
    )
    rm_repair_src_location_id = fields.Many2one(
        "stock.location",
        string="Remove Part From Location",
        related="company_id.rm_repair_src_location_id",
        readonly=False,
    )
    rm_repair_des_location_id = fields.Many2one(
        "stock.location",
        string="Remove Part To Location",
        related="company_id.rm_repair_des_location_id",
        readonly=False,
    )
    birthday_lead_user_id = fields.Many2one(
        "res.users",
        string="Birthday Lead Default Salesperson",
        related="company_id.birthday_lead_user_id",
        readonly=False,
    )
    birthday_lead_team_id = fields.Many2one(
        "crm.team",
        string="Birthday Lead Default Sales Team",
        related="company_id.birthday_lead_team_id",
        readonly=False,
    )
    months_to_downgrade = fields.Integer(
        string="Months to downgrade",
        help="Number of months without orders",
        related="company_id.months_to_downgrade",
        readonly=False,
    )

    @api.onchange("birthday_lead_user_id")
    def _onchange_lead_user_id(self):
        if self.birthday_lead_user_id:
            team = self.env["crm.team"]._get_default_team_id(
                user_id=self.birthday_lead_user_id.id, domain=[("use_leads", "=", True)]
            )
            self.birthday_lead_team_id = team.id
        else:
            self.birthday_lead_team_id = False
