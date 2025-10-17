import datetime  # noqa
import logging

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HelpDeskZaloOAConfig(models.Model):
    _name = "helpdesk.stage.zalo.oa"
    _description = "Helpdesk Stage Zalo OA"
    _rec_name = "zl_oa_id"

    stage_id = fields.Many2one("helpdesk.stage")
    zl_oa_id = fields.Many2one(
        "zalo.oa", string="Zalo OA", required=True, ondelete="cascade"
    )
    zns_template_id = fields.Many2one(
        "ir.ui.view",
        string="ZNS Template",
        domain="[('type','=','qweb'),('name','ilike', 'ZNS Template: '),('zalo_oa_id','=',zl_oa_id)]",
    )


class HelpdeskStage(models.Model):
    _inherit = "helpdesk.stage"

    sms_view_template_id = fields.Many2one(
        "ir.ui.view",
        string="SMS Template",
        domain=[("type", "=", "qweb"), ("name", "ilike", "SMS Template: ")],
    )
    # sms_view_template_id = fields.Many2one('ir.ui.view', string='SMS Template', domain=[('type','=','qweb'),('name','ilike', 'SMS Template: ')])
    is_send_oa_message = fields.Boolean(string="Is Send OA Message?")
    config_zl_oa_ids = fields.One2many(
        "helpdesk.stage.zalo.oa", "stage_id", string="Zalo OA"
    )


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    brandname_id = fields.Many2one("brand.name", tracking=True)

    def send_vihat_sms(self, sms_template, zns_template=None):
        body_sms = ""
        try:
            body_sms = self.env["sms.template"]._render_template(
                sms_template.xml_id, self._name, self.ids, engine="qweb"
            )[self.id]
        except Exception as e:
            raise UserError(e)
        zns_template_vals = []
        if zns_template:
            key_fields = zns_template.get_val_esc_in_xml()
            for key_field in key_fields:
                val = {
                    "name": key_field,
                    "value": eval(key_field.replace("object.", "self.")),
                }
                zns_template_vals.append((0, 0, val))
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
                    "zns_template_id": zns_template
                    and zns_template.zns_template_id
                    or False,
                    "zns_template_val_ids": zns_template_vals,
                }
            )
        )
        try:
            rlst = sms.sudo().send_vihat_esms()
            self.message_post(
                body=Markup(
                    "Send SMS: <a href='#' data-oe-model='sms.sms' data-oe-id='{sms_id}'>{sms_name}</a>"
                ).format(
                    sms_id=sms.id, sms_name="%s-%s" % (sms.partner_id.name, sms.number)
                )
            )
        except Exception as e:
            _logger.error("Error sending SMS: %s", e)

    def write(self, vals):
        if "stage_id" in vals:
            helpdesk_stage = self.env["helpdesk.stage"].browse(vals.get("stage_id"))
            if (
                helpdesk_stage.sms_view_template_id
                and self.brandname_id
                and self.brandname_id.sms_brandname_id
                and self.partner_id
                and self.partner_id.company_type == "person"
            ):
                if helpdesk_stage.is_send_oa_message:
                    zns_template = False
                    brandname = self.brandname_id
                    # lấy zns template theo config
                    # nếu trong nội dung cập nhật có brandname:
                    if "brandname_id" in vals:
                        brandname = self.env["brand.name"].browse(
                            vals.get("brandname_id")
                        )
                    zalo_oa = brandname.sms_brandname_id.zalo_oa_id
                    config_zl_oa = helpdesk_stage.config_zl_oa_ids.filtered(
                        lambda line: line.zl_oa_id.id == zalo_oa.id
                    )
                    if config_zl_oa and config_zl_oa[0].zns_template_id:
                        zns_template = config_zl_oa[0].zns_template_id
                    if zns_template:
                        self.send_vihat_sms(
                            sms_template=helpdesk_stage.sms_view_template_id,
                            zns_template=zns_template,
                        )
                    else:
                        self.send_vihat_sms(
                            sms_template=helpdesk_stage.sms_view_template_id
                        )
                else:
                    self.send_vihat_sms(
                        sms_template=helpdesk_stage.sms_view_template_id
                    )
            elif helpdesk_stage.sms_view_template_id and (
                not self.brandname_id
                or not self.brandname_id.sms_brandname_id
                or not self.partner_id
            ):
                self.message_post(
                    body="Không gửi được SMS - Vui lòng kiểm tra thông tin thiết lập"
                )
        return super().write(vals)

    @api.model_create_multi
    def create(self, list_value):
        tickets = super().create(list_value)
        for ticket in tickets:
            helpdesk_stage = ticket.stage_id
            if (
                helpdesk_stage
                and helpdesk_stage.sms_view_template_id
                and ticket.brandname_id
                and ticket.brandname_id.sms_brandname_id
                and ticket.partner_id
                and ticket.partner_id.company_type == "person"
            ):
                if helpdesk_stage.is_send_oa_message:
                    zns_template = False
                    # lấy zns template theo config
                    # nếu trong nội dung cập nhật có brandname:
                    config_zl_oa = helpdesk_stage.config_zl_oa_ids.filtered(
                        lambda line: line.zl_oa_id.id
                        == ticket.brandname_id.sms_brandname_id.zalo_oa_id.id
                    )
                    if config_zl_oa and config_zl_oa[0].zns_template_id:
                        zns_template = config_zl_oa[0].zns_template_id
                    if zns_template:
                        ticket.send_vihat_sms(
                            sms_template=helpdesk_stage.sms_view_template_id,
                            zns_template=zns_template,
                        )
                    else:
                        ticket.send_vihat_sms(
                            sms_template=helpdesk_stage.sms_view_template_id
                        )
                else:
                    ticket.send_vihat_sms(
                        sms_template=helpdesk_stage.sms_view_template_id
                    )
            elif helpdesk_stage.sms_view_template_id and (
                not ticket.brandname_id
                or not ticket.brandname_id.sms_brandname_id
                or not ticket.partner_id
            ):
                ticket.message_post(
                    body="Không gửi được SMS - Vui lòng kiểm tra thông tin thiết lập"
                )
        return tickets

    def _send_sms(self):
        # Override this method to prevent sending SMS
        pass
