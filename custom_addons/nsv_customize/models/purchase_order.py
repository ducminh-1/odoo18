from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    invoice_number = fields.Char(
        "Invoice Number", compute="_compute_invoice_number", store=True
    )

    @api.depends("state", "invoice_ids.state", "invoice_ids.invoice_number")
    def _compute_invoice_number(self):
        for order in self:
            if order.state not in ("done", "purchase"):
                order.invoice_number = False
            else:
                invoices = self.env["account.move"].search(
                    [("invoice_origin", "=", order.name), ("state", "=", "posted")]
                )
                if len(invoices) > 0:
                    order.invoice_number = " + ".join(
                        [inv.invoice_number for inv in invoices if inv.invoice_number]
                    )
                else:
                    order.invoice_number = False

    def unlink(self):
        for order in self:
            if order.picking_ids or order.invoice_ids:
                raise UserError(
                    _(
                        "You can not delete a purchase order which is related to a picking or a invoice."
                    )
                )
        return super().unlink()

    def _prepare_picking(self):
        res = super()._prepare_picking()
        res["po_id"] = self.id
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    product_size = fields.Many2one("res.size", string="Product Size")
    carton_size = fields.Many2many(
        "res.size",
        "po_line_carton_size_rel",
        "po_line_id",
        "size_id",
        string="Carton Size",
    )
    weight = fields.Float("Weight")
    volume = fields.Float("Volume")

    @api.onchange("product_id", "product_qty")
    def _onchange_product_weight(self):
        if self.product_id:
            self.weight = (
                self.product_id.weight * self.product_qty if self.product_qty else 0
            )
            self.volume = (
                self.product_id.volume * self.product_qty if self.product_qty else 0
            )
            self.product_size = self.product_id.product_size
            self.carton_size = self.product_id.carton_size
        else:
            self.weight = 0.0
            self.volume = 0.0
            self.product_size = False
            self.carton_size = False

    def _prepare_stock_move_vals(
        self, picking, price_unit, product_uom_qty, product_uom
    ):
        vals = super()._prepare_stock_move_vals(
            picking, price_unit, product_uom_qty, product_uom
        )
        vals.update(
            {
                "product_size": self.product_size.id,
                "carton_size": self.carton_size.ids,
                "weight": self.weight,
                "volume": self.volume,
            }
        )
        return vals
