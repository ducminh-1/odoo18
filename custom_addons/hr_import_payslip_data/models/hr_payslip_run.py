from odoo import fields, models


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"

    imported = fields.Boolean(readonly=True)
    last_import_date = fields.Datetime(default=False, readonly=True)
