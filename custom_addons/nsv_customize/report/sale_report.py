from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    channel_id = fields.Many2one("sale.channel", "Channel")
    # pos_account_tag_id = fields.Many2one('account.analytic.tag', 'POS')
    pos_analytic_account_id = fields.Many2one("account.analytic.account", "POS")

    # price_unit = fields.Float('Price Unit', readonly=True)
    product_report_category = fields.Many2one(
        "product.public.category", string="Product Report Category"
    )

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res["channel_id"] = "s.channel_id"
        # res['pos_account_tag_id'] = "s.pos_account_tag_id"
        res["pos_analytic_account_id"] = "s.pos_analytic_account_id"
        # res['price_unit'] = "MAX(l.price_unit)"
        res["product_report_category"] = "t.product_report_category"
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        # res += ', s.channel_id, s.pos_account_tag_id, l.price_unit, t.product_report_category'
        # res += ', s.channel_id, l.price_unit, t.product_report_category'
        # res += ', s.channel_id, t.product_report_category'
        res += ", s.channel_id, s.pos_analytic_account_id, t.product_report_category"
        return res

    # def _query(self):
    #     fields['channel_id'] = ", s.channel_id as channel_id"
    #     fields['pos_account_tag_id'] = ", s.pos_account_tag_id as pos_account_tag_id"
    #     fields['price_unit'] = ", MAX(l.price_unit) as price_unit"
    #     fields['product_report_category'] = ", t.product_report_category as product_report_category"
    #     groupby += ', s.channel_id, s.pos_account_tag_id, l.price_unit, t.product_report_category'
    #     return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
