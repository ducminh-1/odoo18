from odoo import fields, models


class SaleChannel(models.Model):
    _name = "sale.channel"
    _description = "Sale Channel"
    _order = "sequence,id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char("Chanel", default="New", tracking=True)
    active = fields.Boolean("Active", default=True)
    sequence = fields.Integer("Sequence")
    # account_tag_id = fields.Many2one(
    #     'account.analytic.tag', 'Analytic Account Tag', tracking=True,
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    company_id = fields.Many2one(
        "res.company",
        "Company",
        default=lambda self: self.env.company,
        help="The company is automatically set from your user preferences.",
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        "Analytic Account",
        tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
