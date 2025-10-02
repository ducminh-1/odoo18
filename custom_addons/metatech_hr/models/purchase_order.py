from odoo import fields, models

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    user_id = fields.Many2one(
        "res.users", related="order_id.user_id", string="Purchase Representative"
    )
