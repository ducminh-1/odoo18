from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    misa_account_number = fields.Char(string="Mã Misa")
