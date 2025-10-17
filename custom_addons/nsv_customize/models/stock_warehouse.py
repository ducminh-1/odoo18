from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    # analytic_tag_id = fields.Many2one('account.analytic.tag', 'Account Tag',
    #                                   domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        "Analytic Account",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        tracking=True,
    )
