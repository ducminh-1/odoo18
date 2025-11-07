import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'


    slip_ids = fields.One2many('hr.payslip',
                               'employee_id', string='Payslips',
                               readonly=True,
                               help="Choose Payslip for Employee")
    payslip_count = fields.Integer(compute='_compute_payslip_count',
                                   string='Payslip Count',
                                   help="Set Payslip Count")

    def _compute_payslip_count(self):
        """Function for count Payslips"""
        payslip_data = self.env['hr.payslip'].read_group(
            [('employee_id', 'in', self.ids)],
            # [('employee_id', 'in', [self.env.user.employee_id.id])],
            ['employee_id'], ['employee_id'])
        result = dict(
            (data['employee_id'][0], data['employee_id_count']) for data in
            payslip_data)
        for employee in self:
            employee.payslip_count = result.get(employee.id, 0)
