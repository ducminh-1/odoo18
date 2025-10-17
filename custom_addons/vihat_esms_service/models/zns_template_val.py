from odoo import fields, models


class BrandName(models.Model):
    _name = "zns.template.val"
    _description = "ZNS Template Value"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char("Name", tracking=True)
    value = fields.Char()
    sms_id = fields.Many2one("sms.sms")
