from odoo import _, api, models
from odoo.exceptions import UserError

# class AccountAnalyticTag(models.Model):
#     _inherit = 'account.analytic.tag'
#
#     tag_type = fields.Selection([('channel', 'Channel'), ('pos', 'POS')], string="Tag Type", default=False)


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    @api.model
    def create(self, vals):
        if not self.env.user.has_groups("account.group_account_manager"):
            raise UserError(
                _("You do not have the access rights to create an analytic account.")
            )
        return super().create(vals)
