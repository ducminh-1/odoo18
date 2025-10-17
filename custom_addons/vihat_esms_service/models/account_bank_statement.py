from odoo import fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    is_send_sms = fields.Boolean(string="Is Send SMS", default=False)
