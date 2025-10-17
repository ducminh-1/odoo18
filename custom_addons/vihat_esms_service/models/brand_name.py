from odoo import fields, models


class BrandName(models.Model):
    _inherit = "brand.name"

    sms_brandname_id = fields.Many2one("sms.brandname")
