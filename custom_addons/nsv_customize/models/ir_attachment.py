from odoo import _, exceptions, models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def unlink(self):
        for attachment in self:
            if self.env.user.has_group(
                "nsv_customize.group_not_deleted_attachment"
            ) and attachment.mimetype not in [
                "application/javascript",
                "text/css",
                "text/scss",
            ]:
                raise exceptions.UserError(
                    _("You are not allowed to delete this attachment.")
                )
            if attachment.res_model and attachment.res_id:
                re_source = (
                    self.env[attachment.res_model].sudo().browse([attachment.res_id])
                )
                if re_source and hasattr(re_source, "message_post"):
                    re_source.message_post(
                        body="Đã xóa tệp đính kèm %s" % (attachment.name)
                    )
        return super().unlink()
