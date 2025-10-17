import datetime

from markupsafe import Markup

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    brandname_id = fields.Many2one("brand.name", tracking=True)
    send_sms_rating = fields.Boolean(default=False, readonly=True)

    def send_vihat_sms(self, sms_template):
        body_sms = ""
        if sms_template:
            try:
                body_sms = self.env["sms.template"]._render_template(
                    sms_template.xml_id, self._name, self.ids, engine="qweb_view"
                )[self.id]
            except Exception as e:
                self.message_post(body="Render body SMS fail: %s" % e)
            sms = (
                self.env["sms.sms"]
                .sudo()
                .create(
                    {
                        "sms_brandname_id": self.brandname_id.sms_brandname_id.id,
                        "body": body_sms,
                        "partner_id": self.partner_id.id,
                        "number": self.partner_id.phone
                        and self.partner_id.phone
                        or self.partner_id.mobile,
                    }
                )
            )
            rlst = sms.sudo().send_vihat_esms()
            self.message_post(
                body=Markup(
                    "Send SMS: <a href='#' data-oe-model='sms.sms' data-oe-id='{sms_id}'>{sms_name}</a>"
                ).format(
                    sms_id=sms.id, sms_name="%s-%s" % (sms.partner_id.name, sms.number)
                )
            )
            return True
        return False

    def send_rating_sms(self):
        sms_template = self.env.company.sms_rating_template_id
        zns_template = (
            self.brandname_id.sms_brandname_id.zalo_oa_id.rating_zns_template_id
        )
        for rec in self.filtered(
            lambda r: not r.send_sms_rating and r.partner_id.company_type == "person"
        ):
            body_sms = ""
            zns_template_vals = []
            try:
                body_sms = self.env["sms.template"]._render_template(
                    sms_template.xml_id, rec._name, rec.ids, engine="qweb"
                )[rec.id]
                if zns_template:
                    key_fields = zns_template.get_val_esc_in_xml()
                    for key_field in key_fields:
                        val = {
                            "name": key_field,
                            "value": str(eval(key_field.replace("object.", "self."))),
                        }
                        zns_template_vals.append((0, 0, val))
            except Exception as e:
                rec.message_post(body="Render body SMS fail: %s" % e)
            date_exec = datetime.datetime.now()
            sms = (
                self.env["sms.sms"]
                .sudo()
                .create(
                    {
                        "sms_brandname_id": rec.brandname_id.sms_brandname_id.id,
                        "body": body_sms,
                        "partner_id": rec.partner_id.id,
                        "number": rec.partner_id.phone
                        and rec.partner_id.phone
                        or rec.partner_id.mobile,
                        "date_exec": date_exec,
                        "zns_template_id": zns_template.zns_template_id
                        if zns_template
                        else False,
                        "zns_template_val_ids": zns_template_vals,
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
            rec.send_sms_rating = True
