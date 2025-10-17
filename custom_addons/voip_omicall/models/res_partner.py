import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    call_log_count = fields.Integer("Call Count", compute="_compute_call_log_count")

    def _compute_call_log_count(self):
        for partner in self:
            logs = self.env["voip.call.log"].search(
                [("commercial_partner_id", "=", partner.commercial_partner_id.id)]
            )
            partner.call_log_count = len(logs)

    def button_open_call_log(self):
        self.ensure_one()
        action = self.env.ref("voip_omicall.open_call_logs").read()[0]
        action["context"] = dict(self.env.context, create=0, edit=0)
        action["domain"] = [
            ("commercial_partner_id", "=", self.commercial_partner_id.id)
        ]
        return action

    @api.model
    def get_info_omicall_customer(self, phone=None, transaction=None):
        if not phone:
            return ""
        try:
            phone_number = str(phone).strip()
            if len(phone_number) >= 10:
                format_phone = phone_number[-10:]
            else:
                format_phone = phone_number
            partner = self.search(
                [
                    "|",
                    ("phone", "like", format_phone),
                    ("mobile", "like", format_phone),
                ],
                order="user_id",
                limit=1,
            )

            if not partner:
                return ""

            if not partner.user_id:
                other_partner = self.search(
                    [
                        ("user_id", "!=", False),
                        "|",
                        ("parent_id", "child_of", partner.id),
                        ("parent_id", "parent_of", partner.id),
                    ],
                    order="user_id",
                    limit=1,
                )
                if not other_partner:
                    return ""
                else:
                    partner = other_partner

            user_login = partner.user_id.login or ""
            sip_login = partner.user_id.sip_login or ""
            return {"user_login": user_login, "sip_login": sip_login}

        except Exception as e:
            _logger.info("================= OMICALL: Encourage Error:\n %s" % e)
            return ""
