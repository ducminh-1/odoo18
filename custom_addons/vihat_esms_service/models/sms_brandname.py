from odoo import fields, models


class SMSBrandName(models.Model):
    _name = "sms.brandname"
    _description = "SMS Brandname"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True)
    zalo_oa_id = fields.Many2one("zalo.oa", string="Zalo OA")
