import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    team_id = fields.Many2one(
        "purchase.team",
        "Purchase Team",
        check_company=True,
    )

    @api.onchange("user_id")
    def onchange_user_id(self):
        if self.user_id:
            self.team_id = self.env["purchase.team"]._get_default_team_id(
                user_id=self.user_id.id
            )


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    user_id = fields.Many2one(
        "res.users", related="order_id.user_id", string="Purchase Representative"
    )
