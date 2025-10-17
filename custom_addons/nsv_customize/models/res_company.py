from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    add_repair_src_location_id = fields.Many2one(
        "stock.location", copy=False, groups="base.group_system"
    )
    add_repair_des_location_id = fields.Many2one(
        "stock.location", copy=False, groups="base.group_system"
    )
    rm_repair_src_location_id = fields.Many2one(
        "stock.location", copy=False, groups="base.group_system"
    )
    rm_repair_des_location_id = fields.Many2one(
        "stock.location", copy=False, groups="base.group_system"
    )
    birthday_lead_user_id = fields.Many2one(
        "res.users", string="Birthday Lead Default Salesperson", copy=False
    )
    birthday_lead_team_id = fields.Many2one(
        "crm.team", string="Birthday Lead Default Sales Team", copy=False
    )
    months_to_downgrade = fields.Integer(
        string="Months to downgrade",
        help="Number of months without orders",
        default=24,
        copy=False,
    )
