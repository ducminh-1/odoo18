from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    product_categ_id = fields.Many2one(
        "product.category",
        "Product Category",
        related="product_id.categ_id",
        store=True,
    )
    # product_brand_id = fields.Many2one('common.product.brand.ept', related='product_id.product_brand_id', string="Product Brand", store=True)
    product_report_category = fields.Many2one(
        "product.public.category",
        related="product_id.product_report_category",
        store=True,
    )
