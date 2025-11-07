import logging

from odoo import api, models, _, fields
from odoo.exceptions import AccessError
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from pytz import timezone
import babel

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    ### OVERRIDE ###
    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
        """Override để bổ sung mô tả từ inputs/worked_days"""
        result = super()._get_payslip_lines(contract_ids, payslip_id)
        payslip = self.env["hr.payslip"].browse(payslip_id)

        # Tạo dict tra nhanh theo code
        input_map = {i.code: i for i in payslip.input_line_ids}
        wd_map = {w.code: w for w in payslip.worked_days_line_ids}

        for line in result:
            code = line.get("code")
            if code in input_map:
                input_line = input_map[code]
                line["name"] = input_line.name or line["name"]
            elif code in wd_map:
                wd_line = wd_map[code]
                line["name"] = wd_line.name or line["name"]

        return result

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        res = super().get_worked_day_lines(contracts, date_from, date_to)
        attendance_res = []
        for contract in contracts.filtered(
                lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from),
                                        time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to),
                                      time.max)
            attendance_domain = [
                ('employee_id', '=', contract.employee_id.id),
                ('check_in', '>=', day_from),
                ('check_out', '<=', day_to),
                # ('state', '=', 'approved'),
            ]
            attendances = self.env['hr.attendance'].search(attendance_domain)
            attendance_data = {
                'name': _('Attendance'),
                'code': 'ATT',
                'contract_id': contract.id,
                'number_of_hours': sum(attendances.mapped('worked_hours')),
                'number_of_days': sum(attendances.mapped('worked_hours')) / contract.resource_calendar_id.hours_per_day,
            }
            attendance_res.append(attendance_data)

        res += attendance_res
        return res
    ### END OVERRIDE ###
