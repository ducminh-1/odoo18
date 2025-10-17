import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CrmTeam(models.Model):
    _inherit = "account.analytic.account"

    misa_app_id = fields.Many2one("misa.app")
    misa_branch_id = fields.Many2one(
        "misa.branch", domain="[('misa_app_id', '=?', misa_app_id)]"
    )

    @api.onchange("misa_app_id")
    def _onchange_misa_app_id(self):
        if self.misa_app_id:
            if (
                not self.misa_branch_id
                or self.misa_branch_id.misa_app_id != self.misa_app_id
            ):
                self.misa_branch_id = False

    @api.onchange("misa_branch_id")
    def _onchange_misa_branch_id(self):
        if self.misa_branch_id:
            if (
                not self.misa_app_id
                or self.misa_branch_id.misa_app_id != self.misa_app_id
            ):
                self.misa_app_id = False
