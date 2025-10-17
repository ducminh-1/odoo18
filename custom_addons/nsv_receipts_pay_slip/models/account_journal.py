from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_print = fields.Boolean(
        string="Print cash receipt & payment voucher", default=False
    )
    receipt_pay_sequence_id = fields.Many2one(
        "ir.sequence", string="Cash Statement Sequence"
    )
