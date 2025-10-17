from odoo import api, fields, models

from ...nsv_customize.models.share_func import amount_to_text, convert_to_money


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    show_print = fields.Boolean(
        string="Show print", compute="_compute_show_print", default=False, store=True
    )
    payer = fields.Char(string="Payer/Recipient")
    number = fields.Char("Number")

    @api.depends("journal_id", "journal_id.type")
    def _compute_show_print(self):
        for line in self:
            if line.journal_id and line.journal_id.is_print:
                line.show_print = True
            else:
                line.show_print = False

    def print_receipts_pay_slip(self):
        return self.env.ref(
            "nsv_receipts_pay_slip.account_print_receipts_pay_slip"
        ).report_action(self)

    def get_amount_text(self, number):
        return amount_to_text(number)

    def get_account_debit_credit(self):
        account_debit_list = []
        account_credit_list = []
        entries = self.move_id.line_ids.mapped("move_id").mapped("line_ids")
        for item in entries:
            if item.debit:
                account_debit_list.append(item.account_id.code)
            if item.credit:
                account_credit_list.append(item.account_id.code)
        results = {
            "debit": ", ".join(list(set(account_debit_list))),
            "credit": ", ".join(list(set(account_credit_list))),
        }
        return results

    def convert_to_money(self, amount):
        convert_to_money(amount)

    @api.model
    def create(self, vals):
        statement_line = super().create(vals)
        if (
            statement_line.journal_id.type == "cash"
            and statement_line.journal_id.is_print
            and statement_line.journal_id.receipt_pay_sequence_id
        ):
            statement_line.number = (
                statement_line.journal_id.receipt_pay_sequence_id.next_by_id()
            )
        return statement_line
