import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    product_size = fields.Many2one("res.size", string="Product Size")
    carton_size = fields.Many2many(
        "res.size",
        "stock_move_carton_size_rel",
        "move_id",
        "size_id",
        string="Carton Size",
    )
    volume = fields.Float(
        string="Volume",
        digits="Volume",
        compute="_cal_move_volume",
        store=True,
        compute_sudo=True,
    )

    @api.depends("product_id", "product_uom_qty", "product_uom")
    def _cal_move_volume(self):
        moves_with_volume = self.filtered(lambda moves: moves.product_id.volume > 0.00)
        for move in moves_with_volume:
            move.volume = move.product_qty * move.product_id.volume
        (self - moves_with_volume).volume = 0

    @api.onchange("product_id")
    def _onchange_product_size(self):
        for rec in self:
            if self.product_id:
                rec.product_size = self.product_id.product_size
                rec.carton_size = self.product_id.carton_size
                rec.volume = self.product_id.volume

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(quantity, reserved_quant)
        vals.update(
            {
                "product_size": self.product_size.id,
                "carton_size": self.carton_size.ids,
                "weight": self.weight,
                "volume": self.volume,
            }
        )
        return vals

    def _prepare_procurement_values(self):
        vals = super()._prepare_procurement_values()
        vals.update(
            {
                "product_size": self.product_size.id,
                "carton_size": self.carton_size.ids,
                "volume": self.volume,
            }
        )
        return vals

    def action_show_details(self):
        res = super().action_show_details()
        res.get("context", {}).update(
            {
                **res.get("context", {}),
                "default_product_size": self.product_size.id,
                "default_carton_size": self.carton_size.ids,
                "default_weight": self.weight,
                "default_volume": self.volume,
            }
        )
        return res

    def _prepare_account_move_line(
        self, qty, cost, credit_account_id, debit_account_id, svl_id, description
    ):
        res = super()._prepare_account_move_line(
            qty, cost, credit_account_id, debit_account_id, svl_id, description
        )
        for line in res:
            if line[2] and self.picking_id:
                analytic_distribution = {}
                for analytic in self.picking_id.account_analytic_ids:
                    analytic_distribution.update({analytic.id: 100})
                if analytic_distribution:
                    line[2].update({"analytic_distribution": analytic_distribution})
        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    product_size = fields.Many2one("res.size", string="Product Size")
    carton_size = fields.Many2many(
        "res.size",
        "move_line_carton_size_rel",
        "move_line_id",
        "size_id",
        string="Carton Size",
    )
    weight = fields.Float("Weight", digits="Stock Weight")
    volume = fields.Float("Volume", digits="Volume")

    def _get_aggregated_product_quantities(self, **kwargs):
        aggregated_move_lines = super()._get_aggregated_product_quantities(**kwargs)
        for aggregated_move_line in aggregated_move_lines:
            aggregated_move_lines[aggregated_move_line]["weight"] = (
                aggregated_move_lines[aggregated_move_line]["move"].weight
            )
            aggregated_move_lines[aggregated_move_line]["volume"] = (
                aggregated_move_lines[aggregated_move_line]["move"].volume
            )
        return aggregated_move_lines
