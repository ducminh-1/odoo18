from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sms_rating_template_id = fields.Many2one(
        "ir.ui.view",
        string="SMS Template",
        domain=[("type", "=", "qweb"), ("name", "ilike", "SMS Template: ")],
        help="SMS sent to the customer once the order is paid.",
        copy=False,
    )
    sms_birthday_coupon_template_id = fields.Many2one(
        "ir.ui.view",
        string="Birthday Coupon SMS Template",
        domain=[("type", "=", "qweb"), ("name", "ilike", "SMS Template: ")],
    )
    sms_birthday_coupon_brandname_id = fields.Many2one(
        "sms.brandname", string="Birthday Coupon SMS Brandname"
    )
