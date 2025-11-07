import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HrPayslipConfirmation(models.Model):
    _name = "hr.payslip.confirmation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "payslip_id"

    payslip_id = fields.Many2one(
        "hr.payslip", required=True, ondelete="cascade"
    )
    employee_id = fields.Many2one(
        "hr.employee", related="payslip_id.employee_id", store=True
    )
    status = fields.Selection(
        [
            ("new", "New"),
            ("sent", "Sent"),
            ("changes_requested", "Changes Requested"),
            ("confirmed", "Confirmed"),
        ],
        default="new",
        tracking=True,
    )
