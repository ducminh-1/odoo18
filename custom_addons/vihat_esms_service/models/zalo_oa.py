from odoo import fields, models


class ZaloOA(models.Model):
    _name = "zalo.oa"
    _description = "Zalo OA"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True)
    oa_id = fields.Char(string="Zalo OA ID")
    rating_zns_template_id = fields.Many2one("ir.ui.view")
    birthday_zns_template_id = fields.Many2one("ir.ui.view")
    guarantee_register_zns_template_id = fields.Many2one("ir.ui.view")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
