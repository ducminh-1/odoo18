from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    warehouse_id = fields.Many2one("stock.warehouse", compute="_compute_warehouse")

    def _compute_warehouse(self):
        for loc in self:
            warehouse = self.env["stock.warehouse"].search(
                [("view_location_id", "parent_of", loc.id)], limit=1
            )
            if warehouse:
                loc.warehouse_id = warehouse
            else:
                loc.warehouse_id = False
