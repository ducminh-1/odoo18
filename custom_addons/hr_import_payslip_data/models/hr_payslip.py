from odoo import fields, models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    imported = fields.Boolean(readonly=True)


class HrPayslipWorkedDays(models.Model):
    _inherit = "hr.payslip.worked.days"

    _sql_constraints = [
        (
            "payslip_work_entry_typ_uniq",
            "unique (payslip_id, work_entry_type_id)",
            "The combination of Payslip and Work Entry Type must be unique!",
        ),
    ]


class HrPayslipInput(models.Model):
    _inherit = "hr.payslip.input"

    _sql_constraints = [
        (
            "payslip_input_typ_uniq",
            "unique (payslip_id, input_type_id)",
            "The combination of Payslip and Input Type must be unique!",
        ),
    ]
