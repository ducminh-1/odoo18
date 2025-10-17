from odoo import fields, models


class BrandName(models.Model):
    _name = "brand.name"
    _description = "Brand Name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char("Name", tracking=True)
    company_id = fields.Many2one(
        "res.company",
        ondelete="restrict",
        string="Company",
        default=lambda self: self.env.user.company_id.id,
    )
