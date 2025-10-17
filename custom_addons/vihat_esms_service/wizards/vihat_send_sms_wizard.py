import logging

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class VihatSendSMSWizard(models.TransientModel):
    _name = "vihat.send.sms.wizard"
    _description = "Vihat Send SMS Wizard"

    sms_brandname_id = fields.Many2one("sms.brandname", string="SMS Brandname")
    zalo_oa_id = fields.Many2one("zalo.oa", related="sms_brandname_id.zalo_oa_id")
    template_id = fields.Many2one(
        "ir.ui.view",
        domain=[("type", "=", "qweb"), ("name", "ilike", "SMS Template: ")],
    )
    zns_template_id = fields.Many2one(
        "ir.ui.view",
        domain="[('type','=','qweb'),('name','ilike', 'ZNS Template: '),('zalo_oa_id','=',zalo_oa_id)]",
    )
    body_sms = fields.Text()
    partner_id = fields.Many2one("res.partner", string="Customer")

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        active_id = self._context.get("active_id")
        active_model = self._context.get("active_model", False)
        current_object = self.env[active_model].browse(active_id)
        if active_model == "res.partner":
            res["partner_id"] = current_object.id
        else:
            res["partner_id"] = (
                current_object.partner_id and current_object.partner_id.id or False
            )
        if (
            "brandname_id" in self.env[active_model]._fields
            and current_object.brandname_id
            and current_object.brandname_id.sms_brandname_id
        ):
            res["sms_brandname_id"] = current_object.brandname_id.sms_brandname_id.id
        return res

    @api.onchange("template_id")
    def _onchange_body_sms(self):
        if self.template_id:
            active_id = self._context.get("active_id")
            active_model = self._context.get("active_model", False)
            current_object = self.env[active_model].browse(active_id)
            if current_object:
                try:
                    self.body_sms = self.env["sms.template"]._render_template(
                        self.template_id.xml_id,
                        current_object._name,
                        current_object.ids,
                        engine="qweb_view",
                    )[current_object.id]
                except Exception as e:
                    _logger.error(e)
                    raise UserError(e)

    def send_vihat_sms(self):
        active_id = self._context.get("active_id")
        active_model = self._context.get("active_model", False)
        current_object = self.env[active_model].browse(active_id)
        if not current_object or not self.partner_id:
            raise UserError(_("Không tìm thấy đối tượng gửi tin!"))
        zns_template_vals = []
        key_fields = self.zns_template_id.get_val_esc_in_xml()
        for key_field in key_fields:
            val = {
                "name": key_field,
                "value": eval(key_field.replace("object.", "current_object.")),
            }
            zns_template_vals.append((0, 0, val))
        sms = (
            self.env["sms.sms"]
            .sudo()
            .create(
                {
                    "sms_brandname_id": self.sms_brandname_id.id,
                    "body": self.body_sms,
                    "partner_id": self.partner_id.id,
                    "number": self.partner_id.phone
                    and self.partner_id.phone
                    or self.partner_id.mobile,
                    "zns_template_id": self.zns_template_id.zns_template_id,
                    "zns_template_val_ids": zns_template_vals,
                }
            )
        )
        rlst = sms.sudo().send_vihat_esms()
        body_msg_post = Markup(
            "Send SMS: <a href='#' data-oe-model='sms.sms' data-oe-id='{sms_id}'>{sms_name}</a>"
        ).format(sms_id=sms.id, sms_name="%s-%s" % (sms.partner_id.name, sms.number))
        if active_model == "account.bank.statement.line":
            current_object.is_send_sms = True
            current_object.statement_id.message_post(body=body_msg_post)
        else:
            current_object.message_post(body=body_msg_post)
