from odoo import fields, models


class SMSBrandName(models.Model):
    _inherit = "sms.brandname"

    website_id = fields.Many2one("website")
