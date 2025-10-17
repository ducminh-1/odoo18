import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleMakeSAVoucher(models.TransientModel):
    _name = "inv.make_sa_voucher"
    _description = "IV Make SA Voucher"

    count = fields.Integer(compute="_compute_count")
    account_move_ids = fields.Many2many(
        "account.move", default=lambda self: self.env.context.get("active_ids")
    )
    valid_account_move_ids = fields.Many2many(
        "account.move",
        compute="_compute_valid_account_move_ids",
        string="Valid Account Moves",
    )

    @api.depends("account_move_ids")
    def _compute_count(self):
        for record in self:
            record.count = len(record.account_move_ids)

    @api.depends("account_move_ids")
    def _compute_valid_account_move_ids(self):
        for record in self:
            record.valid_account_move_ids = record.account_move_ids.filtered(
                lambda m: m.can_create_misa_sa_voucher
            )

    def create_misa_sa_vouchers(self):
        vouchers = self._create_misa_sa_vouchers(self.valid_account_move_ids)
        return self.valid_account_move_ids.action_view_misa_sa_vouchers(
            sa_vouchers=vouchers
        )

    def _create_misa_sa_vouchers(self, moves):
        return moves._create_misa_sa_vouchers()
