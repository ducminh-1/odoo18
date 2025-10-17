from odoo import models


class ApprovalApprover(models.Model):
    _inherit = "approval.approver"

    def _get_user_related_to_deleted_appover(self, approver):
        domain = [
            ("res_model", "=", "approval.request"),
            ("res_id", "=", approver.request_id.id),
            (
                "activity_type_id",
                "=",
                self.env.ref("approvals.mail_activity_data_approval").id,
            ),
            ("user_id", "=", approver.user_id.id),
        ]
        activities = self.env["mail.activity"].search(domain)
        return activities

    def unlink(self):
        for approver in self:
            self.sudo()._get_user_related_to_deleted_appover(approver=approver).unlink()
        return super().unlink()
