import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"

    def done_payslip_run(self):
        for line in self.slip_ids:
            line.action_payslip_done()
        return self.write({'state': 'close'})
