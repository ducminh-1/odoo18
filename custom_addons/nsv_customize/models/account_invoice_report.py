from odoo import fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    employee_id = fields.Many2one("hr.employee", string="Employee")

    def _select(self):
        # return super(AccountInvoiceReport, self)._select() + ", move.employee_id as employee_id"
        # return super()._select() + SQL('''
        #     , move.employee_id as employee_id
        # ''')
        return SQL("%s, move.employee_id as employee_id", super()._select())
