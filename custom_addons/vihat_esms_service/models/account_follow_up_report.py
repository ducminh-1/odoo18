# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, models
from odoo.exceptions import UserError


class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.followup.report"

    # def _execute_followup_partner(self, partner):
    #     if partner.followup_status == 'in_need_of_action':
    #         followup_line = partner.followup_level
    #         if followup_line.send_sms:
    #             options = {'partner_id': partner.id}
    #             self._action_send_sms_followup(options)
    #             return True
    #     return super(AccountFollowupReport, self)._execute_followup_partner(partner)

    @api.model
    def send_sms(self, options):
        partner_id = options.get("partner_id", "")
        partner = self.env["res.partner"].browse(partner_id)
        if not partner:
            raise UserError(_("Invalid recipient information. Please update it."))
        view_id = self.env.ref("vihat_esms_service.send_sms_wizard_form").id
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "name": _("Send SMS Text Message"),
            "views": [(view_id, "form")],
            "res_model": "vihat.send.sms.wizard",
            "target": "new",
            "view_id": view_id,
            "context": {"active_model": "res.partner", "active_id": partner_id},
        }

    # def _action_send_sms_followup(self, options):
    #     partner_id = options.get('partner_id', '')
    #     partner = self.env['res.partner'].browse(partner_id)
    #     if not partner:
    #         raise UserError(_('Invalid recipient information. Please update it.'))
    #     sms = self.env['sms.sms'].sudo().create({
    #         'body': self._get_sms_summary(options),
    #         'partner_id': partner.id,
    #         'number': partner.phone and partner.phone or partner.mobile,
    #     })
    #     sms.send_vihat_esms()
    #     # lognote send sms reminder payment
    #     body_msg_post = 'Send Payment Reminder SMS: <a href=# data-oe-model=sms.sms data-oe-id=%d>%s-%s</a>' % (sms.id, sms.partner_id.name, sms.number)
    #     partner.message_post(body=body_msg_post)
    #     return True
