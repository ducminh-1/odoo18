import datetime
import logging

from markupsafe import Markup

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    birthday_coupon_id = fields.Many2one(
        "coupon.coupon", string="Birthday Coupon", readonly=True
    )
    is_birthday_coupon_sent = fields.Boolean(
        string="Is Birthday Coupon Sent", default=False
    )
    is_birthday_coupon_sent_this_month = fields.Boolean(
        string="Is Birthday Coupon Sent This Month",
        compute="_compute_is_birthday_coupon_sent_this_month",
        store=True,
    )

    @api.depends("birthday", "is_birthday_coupon_sent")
    def _compute_is_birthday_coupon_sent_this_month(self):
        today = datetime.datetime.today()
        for rec in self:
            if rec.birthday:
                rec.is_birthday_coupon_sent_this_month = (
                    rec.is_birthday_coupon_sent and rec.birthday.month == today.month
                )
            else:
                rec.is_birthday_coupon_sent_this_month = False

    def _get_birthday_partners(self):
        """Get birthday partners of current month"""
        today = datetime.datetime.today()
        month_need_action = "%-" + today.strftime("%m") + "-" + today.strftime("%d")
        partners = self.search(
            [("birthday", "!=", False), ("birthday", "like", month_need_action)]
        )
        return partners

    def _filter_birthday_coupon(self):
        return self.filtered(
            lambda r: not r.is_birthday_coupon_sent_this_month
            and r.company_type == "person"
            and r.loyalty_level_id
        )

    def _create_birthday_coupon(self):
        self.ensure_one()
        program = self.loyalty_level_id.birthday_coupon_program_id
        if program:
            coupon = self.env["coupon.coupon"].create(
                {
                    "program_id": program.id,
                    "partner_id": self.id,
                }
            )
            return coupon

    def _get_default_brandname(self):
        return (self.company_id or self.env.company).sms_birthday_coupon_brandname_id

    def send_birthday_coupon_sms(self):
        sms_template = (
            self.company_id or self.env.company
        ).sms_birthday_coupon_template_id
        zns_template = (
            self.company_id or self.env.company
        ).sms_birthday_coupon_brandname_id.zalo_oa_id.birthday_zns_template_id
        for rec in self._filter_birthday_coupon():
            coupon = rec._create_birthday_coupon()
            if coupon:
                rec.birthday_coupon_id = coupon.id
            else:
                continue
            body_sms = ""
            zns_template_vals = []
            try:
                body_sms = self.env["sms.template"]._render_template(
                    sms_template.xml_id, rec._name, rec.ids, engine="qweb_view"
                )[rec.id]
                if zns_template:
                    key_fields = zns_template.get_val_esc_in_xml_zns()
                    for key_field in key_fields:
                        val = {
                            "name": key_field,
                            "value": str(eval(key_field.replace("object.", "rec."))),
                        }
                        zns_template_vals.append((0, 0, val))
            except Exception as e:
                rec.message_post(body="Render body SMS fail: %s" % e)
            sms = (
                self.env["sms.sms"]
                .sudo()
                .create(
                    {
                        "sms_brandname_id": (
                            rec.company_id or rec.env.company
                        ).sms_birthday_coupon_brandname_id.id,
                        "body": body_sms,
                        "partner_id": rec.id,
                        "number": rec.phone or rec.mobile,
                        "zns_template_id": zns_template.zns_template_id
                        if zns_template
                        else False,
                        "zns_template_val_ids": zns_template_vals,
                        "only_sms": self.env.context.get("only_sms", False),
                    }
                )
            )
            rec.message_post(
                body=Markup(
                    "Create SMS in queue: <a href='#' data-oe-model='sms.sms' data-oe-id='{sms_id}'>{sms_name}</a>"
                ).format(
                    sms_id=sms.id, sms_name="%s-%s" % (sms.partner_id.name, sms.number)
                )
            )
            rec.is_birthday_coupon_sent = True

    def cron_partner_birthday_coupon(self):
        self._get_birthday_partners().with_context(
            only_sms=True
        ).send_birthday_coupon_sms()
