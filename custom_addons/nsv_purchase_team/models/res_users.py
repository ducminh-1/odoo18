# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    purchase_team_ids = fields.Many2many(
        "purchase.team",
        "purchase_team_user_rel",
        "user_id",
        "purchase_team_id",
        "User's Purchase Team",
        help="Purchase Team the user is member of. Used to compute the members of a Purchase Team through the inverse one2many",  # noqa: E501
    )
