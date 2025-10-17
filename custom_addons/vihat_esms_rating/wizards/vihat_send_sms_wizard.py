import logging

from odoo import api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class VihatSendSMSWizard(models.TransientModel):
    _inherit = "vihat.send.sms.wizard"

    @api.onchange("template_id")
    def _onchange_body_sms(self):
        if self.template_id:
            active_id = self._context.get("active_id")
            active_model = self._context.get("active_model", False)
            current_object = self.env[active_model].browse(active_id)
            brandname = (
                current_object.brandname_id.name
                if "brandname_id" in self.env[active_model]._fields
                else self.sms_brandname_id.name
            )
            if current_object:
                try:
                    self.body_sms = (
                        self.env["sms.template"]
                        .with_context(
                            {
                                "rating_website_id": self.sms_brandname_id.website_id.id,
                                "brandname": brandname or "",
                            }
                        )
                        ._render_template(
                            self.template_id.xml_id,
                            current_object._name,
                            current_object.ids,
                            engine="qweb_view",
                        )[current_object.id]
                    )
                except Exception as e:
                    _logger.error(e)
                    raise UserError(e)

    @api.onchange("sms_brandname_id")
    def _onchange_brandname_id(self):
        self.template_id = False
        self.body_sms = ""
