from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def _default_zalo_oa(self):
        return self.env["zalo.oa"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )

    sms_rating_template_id = fields.Many2one(
        "ir.ui.view",
        string="SMS Template",
        domain=[("type", "=", "qweb"), ("name", "ilike", "SMS Template: ")],
        help="SMS sent to the customer once the order is paid.",
        related="company_id.sms_rating_template_id",
        readonly=False,
    )
    zalo_oa_id = fields.Many2one(
        "zalo.oa", string="Zalo OA", default=_default_zalo_oa, ondelete="cascade"
    )
    zns_rating_template_id = fields.Many2one(
        "ir.ui.view",
        string="SMS Template",
        domain="[('type','=','qweb'),('name','ilike', 'ZNS Template: '),('zalo_oa_id','=',zalo_oa_id)]",
        related="zalo_oa_id.rating_zns_template_id",
        help="Zalo OA sent message to the customer once the order is paid.",
        readonly=False,
    )
    sms_birthday_coupon_template_id = fields.Many2one(
        "ir.ui.view",
        string="Birthday Coupon SMS Template",
        domain=[("type", "=", "qweb"), ("name", "ilike", "SMS Template: ")],
        related="company_id.sms_birthday_coupon_template_id",
        readonly=False,
    )
    sms_birthday_coupon_brandname_id = fields.Many2one(
        "sms.brandname",
        string="Birthday Coupon SMS Brandname",
        related="company_id.sms_birthday_coupon_brandname_id",
        readonly=False,
    )
    zns_birthday_coupon_template_id = fields.Many2one(
        "ir.ui.view",
        string="Birthday Coupon ZNS Template",
        domain="[('type','=','qweb'), ('name','ilike', 'ZNS Template: '), ('zalo_oa_id','=',zalo_oa_id)]",
        related="zalo_oa_id.birthday_zns_template_id",
        readonly=False,
    )
