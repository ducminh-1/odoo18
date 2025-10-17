from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def write(self, vals):
        res = super().write(vals)
        if (
            "date_done" in vals
            and vals.get("date_done")
            and self.location_dest_id.usage == "customer"
        ):
            self.sale_id.send_rating_sms()
        return res
