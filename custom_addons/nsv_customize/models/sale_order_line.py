import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # pos_account_tag_id = fields.Many2one(related='order_id.pos_account_tag_id', store=True, string='POS')
    # pos_ana
    product_size = fields.Many2one("res.size", string="Product Size")
    carton_size = fields.Many2many(
        "res.size", "so_line_size_rel", "so_line_id", "size_id", string="Carton Size"
    )
    weight = fields.Float("Weight", digits="Stock Weight")
    volume = fields.Float("Volume", digits="Volume")

    @api.onchange("product_id", "product_uom_qty")
    def _onchange_product_weight(self):
        if self.product_id:
            self.weight = self.product_id.weight * self.product_uom_qty
            self.volume = self.product_id.volume * self.product_uom_qty
            self.product_size = self.product_id.product_size
            self.carton_size = self.product_id.carton_size
        else:
            self.weight = 0.0
            self.volume = 0.0
            self.product_size = False
            self.carton_size = False

    # @api.onchange('product_id')
    # def _onchange_account_tag(self):
    #     if self.order_id.pos_account_tag_id and not self.display_type:
    #         self.analytic_tag_ids |= self.order_id.pos_account_tag_id
    #     if self.order_id.channel_account_tag_id and not self.display_type:
    #         self.analytic_tag_ids |= self.order_id.channel_account_tag_id

    @api.depends(
        "order_id.partner_id",
        "product_id",
        "order_id.project_id",
        "order_id.channel_analytic_account_id",
        "order_id.pos_analytic_account_id",
        "order_id.team_id",
    )
    def _compute_analytic_distribution(self):
        # super()._compute_analytic_distribution()
        # for line in self:
        #     if line.display_type or line.analytic_distribution or not line.product_id:
        #         continue
        #     project = line.product_id.project_id or line.order_id.project_id
        #     distribution = project._get_analytic_distribution()
        #     if distribution:
        #         line.analytic_distribution = distribution
        super()._compute_analytic_distribution()
        for line in self:
            if line.display_type or not line.product_id:
                continue
            # project = line.product_id.project_id or line.order_id.project_id
            distribution = line.analytic_distribution or {}
            if line.order_id.channel_analytic_account_id:
                distribution[line.order_id.channel_analytic_account_id.id] = 100
            if line.order_id.pos_analytic_account_id:
                distribution[line.order_id.pos_analytic_account_id.id] = 100
            if line.order_id.team_id.analytic_account_id:
                distribution[line.order_id.team_id.analytic_account_id.id] = 100
            line.analytic_distribution = distribution
            # line.analytic_distribution = {}
            # if distribution:
            #     line.analytic_distribution = distribution

    def _prepare_procurement_values(self, group_id=False):
        values = super()._prepare_procurement_values(group_id)
        values.update(
            {
                "product_size": self.product_size.id,
                "carton_size": self.carton_size.ids,
                "volume": self.volume,
            }
        )
        return values

    price_rule = fields.Float(string="Price rule")
    difference_ratio = fields.Float(
        string="Difference ratio", compute="_compute_difference_ratio", store=True
    )

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res:
            if res.product_id:
                price_rule = self.env["account.tax"]._fix_tax_included_price_company(
                    res._get_display_price(),
                    res.product_id.taxes_id,
                    res.tax_id,
                    res.company_id,
                )
                res.update({"price_rule": price_rule})
        return res

    @api.depends("price_unit", "price_rule")
    def _compute_difference_ratio(self):
        for line in self:
            line.difference_ratio = (
                (line.price_unit - line.price_rule) / line.price_rule
                if line.price_rule != 0
                else 0
            )

    @api.onchange("product_uom_qty", "date_order")
    def onchange_quantity(self):
        if self.product_id:
            price_rule = self.env["account.tax"]._fix_tax_included_price_company(
                self._get_display_price(),
                self.product_id.taxes_id,
                self.tax_id,
                self.company_id,
            )
            self.price_rule = price_rule
        # for rec in self:
        #     price_rule = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(), self.product_id.taxes_id, self.tax_id, self.company_id)
        #     rec.price_rule = price_rule
