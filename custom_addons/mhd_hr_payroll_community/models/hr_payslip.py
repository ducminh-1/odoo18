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

    # @api.model
    # def get_worked_day_lines(self, contracts, date_from, date_to):
    #     res = super().get_worked_day_lines(contracts, date_from, date_to)
    #     attendance_res = []
    #     for contract in contracts.filtered(
    #             lambda contract: contract.resource_calendar_id):
    #         day_from = datetime.combine(fields.Date.from_string(date_from),
    #                                     time.min)
    #         day_to = datetime.combine(fields.Date.from_string(date_to),
    #                                   time.max)
            
    #         attendance_domain = [
    #             ('employee_id', '=', contract.employee_id.id),
    #             ('check_in', '>=', day_from),
    #             ('check_out', '<=', day_to),
    #             # ('state', '=', 'approved'),
    #         ]
    #         attendances = self.env['hr.attendance'].search(attendance_domain)
    #         attendance_data = {
    #             'name': _('Attendance'),
    #             'code': 'ATT',
    #             'contract_id': contract.id,
    #             'number_of_hours': sum(attendances.mapped('worked_hours')),
    #             'number_of_days': sum(attendances.mapped('worked_hours')) / contract.resource_calendar_id.hours_per_day,
    #         }
    #         attendance_res.append(attendance_data)

    #     res += attendance_res
    #     return res
    ### END OVERRIDE ###

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        self.ensure_one()
        """
        @param contracts: Browse record of contracts, date_from, date_to
        @return: returns a list of dict containing the input that should be
        applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(
                lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from),
                                        time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to),
                                      time.max)
            # compute leave days
            leaves = {}
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(
                day_from, day_to, calendar=contract.resource_calendar_id)
            multi_leaves = []
            for day, hours, leave in day_leave_intervals:
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if len(leave) > 1:
                    for each in leave:
                        if each.holiday_id:
                            multi_leaves.append(each.holiday_id)
                else:
                    holiday = leave.holiday_id
                    current_leave_struct = leaves.setdefault(
                        holiday.holiday_status_id, {
                            'name': holiday.holiday_status_id.name or _(
                                'Global Leaves'),
                            'sequence': 5,
                            'code': holiday.holiday_status_id.code or 'GLOBAL',
                            'number_of_days': 0.0,
                            'number_of_hours': 0.0,
                            'contract_id': contract.id,
                        })
                    current_leave_struct['number_of_hours'] += hours
                    if work_hours:
                        current_leave_struct[
                            'number_of_days'] += hours / work_hours
                        
            # compute worked days
            work_data = contract.employee_id.get_work_days_data(
                day_from, day_to, calendar=contract.resource_calendar_id)
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data['days'],
                'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }
            res.append(attendances)
            uniq_leaves = [*set(multi_leaves)]
            c_leaves = {}
            for rec in uniq_leaves:
                duration = self.env['hr.leave']._parse_duration_to_days(rec.duration_display)
                duration_in_hours = float(duration) * 24
                c_leaves.setdefault(rec.holiday_status_id,
                                    {'hours': duration_in_hours})
            for item in c_leaves:
                if not leaves or item not in leaves:
                    data = {
                        'name': item.name,
                        'sequence': 20,
                        'code': item.code or 'LEAVES',
                        'number_of_hours': c_leaves[item]['hours'],
                        'number_of_days': c_leaves[item][
                                              'hours'] / work_hours,
                        'contract_id': contract.id,
                    }
                    res.append(data)
                for time_off in leaves:
                    if item == time_off:
                        leaves[item]['number_of_hours'] += c_leaves[item][
                            'hours']
                        leaves[item]['number_of_days'] \
                            += c_leaves[item]['hours'] / work_hours
            res.extend(leaves.values())

             # Attendance
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
            res.append(attendance_data)
        return res