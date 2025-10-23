from odoo import api, fields, models
from odoo.exceptions import UserError

class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def unlink(self):
        for attachment in self:
            if attachment.res_model == 'survey.user_input':
                continue
            if attachment.res_model and attachment.res_id:
                re_source = (
                    self.env[attachment.res_model].sudo().browse([attachment.res_id])
                )
                if re_source and hasattr(re_source, "message_post"):
                    re_source.message_post(
                        body="Đã xóa tệp đính kèm %s" % (attachment.name)
                    )
        return super().unlink()