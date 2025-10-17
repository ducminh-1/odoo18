from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        values = super()._get_custom_move_fields()
        values += ["product_size", "carton_size", "volume"]
        return values

    def _push_prepare_move_copy_values(self, move_to_copy, new_date):
        new_move_vals = super()._push_prepare_move_copy_values(move_to_copy, new_date)
        new_move_vals.update(
            {
                "volume": move_to_copy.volume,
            }
        )
        return new_move_vals
