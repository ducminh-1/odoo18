import logging
from datetime import datetime, timezone, timedelta
from odoo import models, fields, api, _
from odoo.tools import float_round
from datetime import timedelta
from datetime import datetime
from pytz import timezone
from odoo.exceptions import UserError
from odoo.addons.resource.models.utils import Intervals
import pytz


_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    attendance_date = fields.Date(string='Date', readonly=True, compute='compute_attendance_date', store=True, tracking=True)
    late_hours = fields.Float(string="Late Hours", compute="_compute_late_early_hours", store=True)
    early_hours = fields.Float(string="Early Leave Hours", compute="_compute_late_early_hours", store=True)
    attendance_hours = fields.Float(string="Attendance Hours", compute="_compute_attendance_hours", store=True)
    working_schedule_id = fields.Many2one('resource.calendar', string='Working Schedule', related='employee_id.resource_calendar_id', readonly=False, store=True)

    @api.depends('check_in', 'check_out')
    def compute_attendance_date(self):
        for record in self:
            attendance_date = False
            if record.check_in and record.check_out:
                attendance_date = record.check_in
            elif record.check_in:
                attendance_date = record.check_in
            elif record.check_out:
                attendance_date = record.check_out

            # Make sure the date is in the user's timezone, avoid cases where the date stored in UTC make attendance_date is not in the same day
            # eg: check in shows 2025-04-15 06:00:00 GMT+07:00, then attendance_date is 2025-04-14 23:00:00 GMT+00:00
            user_tz = timezone(record.employee_id.tz or 'UTC')
            if attendance_date:
                attendance_date = attendance_date.astimezone(user_tz).date()
            else:
                attendance_date = False

            record.attendance_date = attendance_date

    @api.depends('check_in', 'check_out', 'employee_id')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in and attendance.employee_id:
                employee_tz = timezone(attendance.employee_id.tz or 'UTC')
                check_in = attendance.check_in.astimezone(employee_tz)
                check_out = attendance.check_out.astimezone(employee_tz)
                if check_in.date() != check_out.date():
                    raise UserError(_("Check-in and check-out dates must be the same!"))

                employee_tz = timezone(attendance.employee_id.tz or 'UTC')
                check_in_local = attendance.check_in.astimezone(employee_tz)
                check_out_local = attendance.check_out.astimezone(employee_tz)
                # if attendance.is_release_date:
                #     standard_check_in = self._get_standard_working_hours(attendance, 'morning', employee_tz, check_in_local, release_date=True)[0]
                #     standard_check_out = self._get_standard_working_hours(attendance, 'afternoon', employee_tz, check_out_local, release_date=True)[1]
                # else:
                standard_check_in = self._get_standard_working_hours(attendance, 'morning', employee_tz, check_in_local)[0]
                standard_check_out = self._get_standard_working_hours(attendance, 'afternoon', employee_tz, check_out_local)[1]
                lunch_time = self._get_standard_working_hours(attendance, 'lunch', employee_tz, check_in_local)[2]
                custom_leave_intervals = self._get_standard_working_hours(attendance, 'lunch', employee_tz, check_in_local)[3]
                global_leave_intervals = self._get_standard_working_hours(attendance, 'lunch', employee_tz, check_in_local)[4]

                calendar = attendance._get_employee_calendar()

                if not calendar:
                    raise UserError(_("No working schedule found for employee %s", attendance.employee_id.name))

                tz = timezone(calendar.tz)
                check_in_tz = attendance.check_in.astimezone(tz)
                check_out_tz = attendance.check_out.astimezone(tz)
                lunch_intervals = attendance.employee_id._employee_attendance_intervals(check_in_tz, check_out_tz,
                                                                                        lunch=True)
                if not standard_check_in or not standard_check_out:
                    attendance.worked_hours = 0.0
                    continue
                    # if not standard_check_in:
                    #     raise UserError(_("No standard check in found!"))
                    # if not standard_check_out:
                    #     raise UserError(_("No standard check out found!"))
                max_hours_per_day = ((standard_check_out - standard_check_in).total_seconds() - lunch_time) / 3600.0
                # if check_out_local > standard_check_out and ((check_in_local - standard_check_in).total_seconds() / 3600 > 0.5):
                # if check_out_local > standard_check_out:
                #     if 0 < ((check_in_local - standard_check_in).total_seconds() / 3600) <= 0.5:
                #         # Nếu vào muộn dưới 30 phút, thì du di giờ làm việc
                #         standard_check_out = standard_check_out + timedelta(minutes=30)  # Cộng thêm 30 phút để tránh trường hợp check_out đúng giờ kết thúc ca
                if check_out_local > standard_check_out:
                    delay_minutes = (check_in_local - standard_check_in).total_seconds() / 60
                    if 0 < delay_minutes <= 30:
                        # Kiểm tra xem khoảng đi trễ có nằm trong khoảng nghỉ phép hợp lệ không
                        delay_interval = Intervals([(standard_check_in, check_in_local, attendance)])
                        leave_covered = False
                        for leave_interval in custom_leave_intervals + global_leave_intervals:
                            # Nếu toàn bộ thời gian đi trễ nằm trong leave => không du di
                            if not (delay_interval - leave_interval):
                                leave_covered = True
                                break
                        if not leave_covered:
                            # Chỉ du di nếu không bị bao bởi nghỉ phép
                            standard_check_out = standard_check_out + timedelta(minutes=30)

                if check_in_local <= standard_check_in and check_out_local >= standard_check_out:
                    # Trường hợp 1: check_in và check_out bao quanh khoảng chuẩn
                    attendance_intervals = Intervals([(standard_check_in.astimezone(tz),
                                                       standard_check_out.astimezone(tz),
                                                       attendance)]) - lunch_intervals
                    for custom_leave_interval in custom_leave_intervals:
                        attendance_intervals -= custom_leave_interval
                    for global_leave_interval in global_leave_intervals:
                        attendance_intervals -= global_leave_interval
                elif standard_check_in <= check_in_local <= standard_check_out:
                    if check_out_local > standard_check_out:
                        # Trường hợp 2: check_in hợp lệ, check_out ngoài khoảng chuẩn
                        attendance_intervals = Intervals(
                            [(check_in_tz, standard_check_out.astimezone(tz), attendance)]) - lunch_intervals
                        for custom_leave_interval in custom_leave_intervals:
                            attendance_intervals -= custom_leave_interval
                        for global_leave_interval in global_leave_intervals:
                            attendance_intervals -= global_leave_interval
                    else:
                        # Trường hợp 3: check_in và check_out đều hợp lệ
                        attendance_intervals = Intervals([(check_in_tz, check_out_tz, attendance)]) - lunch_intervals
                        for custom_leave_interval in custom_leave_intervals:
                            attendance_intervals -= custom_leave_interval
                        for global_leave_interval in global_leave_intervals:
                            attendance_intervals -= global_leave_interval
                elif check_in_local < standard_check_in <= check_out_local <= standard_check_out:
                    # Trường hợp 4: check_in ngoài khoảng chuẩn, check_out trong khoảng chuẩn
                    attendance_intervals = Intervals(
                        [(standard_check_in.astimezone(tz), check_out_tz, attendance)]) - lunch_intervals
                    for custom_leave_interval in custom_leave_intervals:
                        attendance_intervals -= custom_leave_interval
                    for global_leave_interval in global_leave_intervals:
                        attendance_intervals -= global_leave_interval
                else:
                    # Các trường hợp khác: không tính giờ làm việc
                    attendance_intervals = Intervals([])

                # Tính tổng giờ làm việc
                delta = sum((i[1] - i[0]).total_seconds() for i in attendance_intervals)
                attendance.worked_hours = delta / 3600.0

                # - Nếu giờ chấm công ít hơn 6h => Làm tròn cho nhân viên, đơn vị nhỏ nhất là 0,5 giờ.
                #     Dưới 0,25 => làm tròn xuống 0
                #     Từ đủ 0,50 tới 0,74 => 0,5
                #     Dưới 0,75 => làm tròn lên 1.0
                if attendance.worked_hours:
                    # attendance.worked_hours = float_round(attendance.worked_hours + 0.25, 1)
                    minutes_part = (attendance.worked_hours - int(attendance.worked_hours)) * 60
                    # if minutes_part < 15:
                    #     attendance.worked_hours = int(attendance.worked_hours)
                    # elif 15 <= minutes_part < 45:
                    #     attendance.worked_hours = int(attendance.worked_hours) + 0.5
                    # elif minutes_part >= 45:
                    #     attendance.worked_hours = int(attendance.worked_hours) + 1.0
                    if minutes_part < 15:
                        attendance.worked_hours = int(attendance.worked_hours)
                    elif 15 <= minutes_part < 45:
                        attendance.worked_hours = int(attendance.worked_hours) + 0.5
                    elif minutes_part >= 45:
                        attendance.worked_hours = int(attendance.worked_hours) + 1.0




                # hour average per day
                # avg_hours = calendar.hours_per_day
                # if attendance.worked_hours > avg_hours:
                #     attendance.worked_hours = avg_hours
                if attendance.worked_hours > max_hours_per_day:
                    attendance.worked_hours = max_hours_per_day
            else:
                attendance.worked_hours = False

    @api.depends('check_in', 'check_out', 'employee_id')
    def _compute_attendance_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in and attendance.employee_id:
                employee_tz = timezone(attendance.employee_id.tz or 'UTC')
                check_in = attendance.check_in.astimezone(employee_tz)
                check_out = attendance.check_out.astimezone(employee_tz)
                employee_tz = timezone(attendance.employee_id.tz or 'UTC')
                check_in_local = attendance.check_in.astimezone(employee_tz)
                check_out_local = attendance.check_out.astimezone(employee_tz)

                calendar = attendance._get_employee_calendar()

                if not calendar:
                    raise UserError(_("No working schedule found for employee %s", attendance.employee_id.name))

                tz = timezone(calendar.tz)
                check_in_tz = attendance.check_in.astimezone(tz)
                check_out_tz = attendance.check_out.astimezone(tz)
                lunch_intervals = attendance.employee_id._employee_attendance_intervals(check_in_tz, check_out_tz,
                                                                                        lunch=True)
                attendance_intervals = Intervals([(check_in_tz, check_out_tz, attendance)]) - lunch_intervals
                delta = sum((i[1] - i[0]).total_seconds() for i in attendance_intervals)
                attendance.attendance_hours = delta / 3600.0
            else:
                attendance.attendance_hours = 0.0

    @api.depends("check_in", "check_out", "employee_id")
    def _compute_late_early_hours(self):
        for att in self:
            att.late_hours = att.early_hours = 0.0

            if not (att.check_in and att.check_out and att.employee_id):
                continue

            contract = att.employee_id.contract_id
            if not contract or not contract.deduct_late_early:
                continue

            calendar = att._get_employee_calendar()
            if not calendar:
                continue

            resource = att.employee_id.resource_id
            tz = timezone(calendar.tz or resource.tz or "UTC")
            check_in_tz = att.check_in.astimezone(tz)
            check_out_tz = att.check_out.astimezone(tz)
            weekday = str(check_in_tz.weekday())  # 0 = Monday

            # Lấy giờ làm trong ngày từ lịch làm việc
            day_attendances = calendar.attendance_ids.filtered(lambda a: a.dayofweek == weekday)

            if not day_attendances:
                continue  # Không có ca làm trong ngày này

            # # Giờ làm buổi sáng sớm nhất và buổi chiều trễ nhất
            # start_hour = min(day_attendances.mapped('hour_from'))
            # end_hour = max(day_attendances.mapped('hour_to'))
            #
            # start_work = check_in_tz.replace(hour=int(start_hour), minute=int((start_hour % 1) * 60), second=0, microsecond=0)
            # end_work = check_in_tz.replace(hour=int(end_hour), minute=int((end_hour % 1) * 60), second=0, microsecond=0)
            #
            # # Cho phép trễ 15 phút
            # allowed_late = start_work + timedelta(minutes=15)
            # time_off = self.get_time_off(att)
            #
            # # Kiểm tra nghỉ phép nữa ngày
            # have_time_off_am = any(leave.request_date_from_period == 'am' for leave in time_off)
            # have_time_off_pm = any(leave.request_date_from_period == 'pm' for leave in time_off)
            #
            # # Lấy giờ làm mặc định buổi sáng và buổi chiều
            # standard_check_in = self._get_standard_working_hours(att, 'morning', tz, check_in_tz)[1]
            # standard_check_in = self._get_standard_working_hours(att, 'morning', tz, check_in_tz)[0]
            # standard_check_out = self._get_standard_working_hours(att, 'afternoon', tz, check_out_tz)[0]
            # standard_check_out = self._get_standard_working_hours(att, 'afternoon', tz, check_out_tz)[1]
            start_work = self._get_start_of_attendance(att, tz, check_in_tz)
            end_work = self._get_end_of_attendance(att, tz, check_out_tz)

            # start_work = start_work + timedelta(minutes=15) if start_work else None  # Cho phép trễ 15 phút
            att.late_hours = (check_in_tz - start_work).total_seconds() / 3600.0 if start_work and check_in_tz > start_work else 0.0
            att.early_hours = (end_work - check_out_tz).total_seconds() / 3600.0 if end_work and check_out_tz < end_work else 0.0

            # att.late_hours = (standard_check_in - check_in_tz).total_seconds() / 3600.0 if standard_check_in and check_in_tz > standard_check_in else 0.0
            # if standard_check_in:
            #     start_work = standard_check_in
            #     allowed_late = start_work + timedelta(minutes=15)
            #     if check_in_tz > allowed_late:
            #         att.late_hours = float_round((check_in_tz - start_work).total_seconds() / 3600.0, 2)
            # att.early_hours = (check_out_tz - standard_check_out).total_seconds() / 3600.0 if standard_check_out and check_out_tz < standard_check_out else 0.0
            # if standard_check_out:
            #     end_work = standard_check_out
            #     if check_out_tz < end_work:
            #         att.early_hours = float_round((end_work - check_out_tz).total_seconds() / 3600.0, 2)

            # am_end = standard_check_in.astimezone(tz) if standard_check_in else end_work
            # pm_start = standard_check_out.astimezone(tz) if standard_check_out else start_work

            # if not have_time_off_am and not have_time_off_pm:
            #     # Làm full ngày → tính bình thường
            #     if check_in_tz > allowed_late:
            #         att.late_hours = float_round((check_in_tz - start_work).total_seconds() / 3600.0, 2)
            #     if check_out_tz < end_work:
            #         att.early_hours = float_round((end_work - check_out_tz).total_seconds() / 3600.0, 2)
            #
            # elif have_time_off_am and not have_time_off_pm:
            #     # Nghỉ sáng → chỉ tính ca chiều
            #     if check_in_tz > pm_start + timedelta(minutes=15):
            #         att.late_hours = float_round((check_in_tz - pm_start).total_seconds() / 3600.0, 2)
            #     if check_out_tz < end_work:
            #         att.early_hours = float_round((end_work - check_out_tz).total_seconds() / 3600.0, 2)
            #
            # elif have_time_off_pm and not have_time_off_am:
            #     # Nghỉ chiều → chỉ tính ca sáng
            #     if check_in_tz > allowed_late:
            #         att.late_hours = float_round((check_in_tz - start_work).total_seconds() / 3600.0, 2)
            #     if check_out_tz < am_end:
            #         att.early_hours = float_round((am_end - check_out_tz).total_seconds() / 3600.0, 2)
            #
            # else:
            #     # Nghỉ cả ngày (sáng + chiều)
            #     att.late_hours = att.early_hours = 0.0

    def _get_standard_working_hours(self, record, period, employee_tz, current_time, release_date=False):
        standard_check_in = None
        standard_check_out = None
        delta_lunch_break = 0.0

        # Lấy thông tin nghỉ phép
        time_off = self.get_time_off(record)  # nghỉ nửa buổi
        custom_time_off = self.get_custom_time_off(record)  # nghỉ theo giờ
        calendar_leaves = record.employee_id.resource_calendar_id.global_leave_ids.filtered(
            lambda l: l.date_from.date() <= current_time.date() <= (l.date_to.date() if l.date_to else l.date_from.date())
        )

        # Nếu nghỉ full ngày
        # if sum(time_off.mapped('number_of_days')) >= 1:
        #     raise UserError(_("You cannot create attendance records when you have full-day time off for that day."))
        if sum(time_off.mapped('number_of_days')) >= 1:
            return None, None, 0.0, [], []

        # Đánh dấu nghỉ sáng/chiều
        have_time_off_am = any(leave.request_date_from_period == 'am' for leave in time_off)
        have_time_off_pm = any(leave.request_date_from_period == 'pm' for leave in time_off)

        # Xác định working schedule theo period
        working_schedule = (
            record.employee_id.release_working_schedule_id if release_date
            else record.working_schedule_id
        )

        attendance_period = working_schedule.attendance_ids.filtered(
            lambda a: a.dayofweek == str(current_time.weekday()) and a.day_period == period
        )

        # Tính giờ nghỉ trưa (nếu có)
        lunch_break = working_schedule.attendance_ids.filtered(
            lambda l: l.dayofweek == str(current_time.weekday()) and l.day_period == "lunch"
        )
        if lunch_break:
            lunch_start = current_time.replace(hour=int(lunch_break.hour_from),
                                               minute=int((lunch_break.hour_from % 1) * 60), second=0)
            lunch_end = current_time.replace(hour=int(lunch_break.hour_to),
                                             minute=int((lunch_break.hour_to % 1) * 60), second=0)
            delta_lunch_break = (lunch_end - lunch_start).total_seconds()

        # Nếu không có period (ngày nghỉ)
        if not attendance_period:
            return None, None, 0.0, [], []

        # --- Tính giờ tiêu chuẩn ban đầu ---
        period_start = current_time.replace(hour=int(attendance_period.hour_from),
                                            minute=int((attendance_period.hour_from % 1) * 60), second=0)
        period_end = current_time.replace(hour=int(attendance_period.hour_to),
                                          minute=int((attendance_period.hour_to % 1) * 60), second=0)

        # --- Điều chỉnh nếu có nghỉ nửa ngày ---
        if period == 'morning' and have_time_off_am:
            # Nghỉ buổi sáng => không có check-in buổi sáng
            period_start = current_time.replace(hour=int(attendance_period.hour_to),
                                                minute=int((attendance_period.hour_to % 1) * 60), second=0)
            period_end = None
        elif period == 'afternoon' and have_time_off_pm:
            # Nghỉ buổi chiều => không có check-out buổi chiều
            period_start = None
            period_end = current_time.replace(hour=int(attendance_period.hour_from),
                                                minute=int((attendance_period.hour_from % 1) * 60), second=0)

        # --- Điều chỉnh theo nghỉ theo giờ tùy chỉnh ---
        custom_leave_intervals = []
        for leave in custom_time_off:
            leave_hour_from = leave.request_hour_from
            leave_hour_to = leave.request_hour_to
            leave_start = current_time.replace(hour=int(leave_hour_from),
                                                minute=int((leave_hour_from % 1) * 60), second=0)
            leave_end = current_time.replace(hour=int(leave_hour_to),
                                                minute=int((leave_hour_to % 1) * 60), second=0)
            custom_leave_intervals.append(Intervals([(leave_start, leave_end, leave)]))
        # for leave_start, leave_end in custom_leave_intervals:
            # Nếu leave nằm trong khung giờ làm việc

            # leave_start = leave.date_from.astimezone(employee_tz)
            # leave_end = leave.date_to.astimezone(employee_tz)
            #
            # # Nếu leave nằm trong khung giờ làm việc
            # if leave_start.date() == current_time.date():
            #     # Nếu nghỉ giữa ca, cắt lại thời gian làm
            #     if period_start and leave_start <= period_start < leave_end:
            #         period_start = leave_end  # bắt đầu sau khi nghỉ xong
            #     if period_end and leave_start < period_end <= leave_end:
            #         period_end = leave_start  # kết thúc trước khi nghỉ
            #
            #     # Nếu toàn bộ period nằm trong giờ nghỉ => không làm
            #     if period_start and period_end and leave_start <= period_start and period_end <= leave_end:
            #         period_start = None
            #         period_end = None
        global_leave_intervals = []
        for leave in calendar_leaves:
            leave_start = leave.date_from.astimezone(employee_tz)
            leave_end = leave.date_to.astimezone(employee_tz)
            global_leave_intervals.append(Intervals([(leave_start, leave_end, leave)]))

        # if period_end:
        #     period_end = period_end + timedelta(minutes=30) # Cộng thêm 30 phút để tránh trường hợp check_out đúng giờ kết thúc ca
        return period_start, period_end, delta_lunch_break, custom_leave_intervals, global_leave_intervals

    def get_time_off(self, attendance):
        if attendance:
            time_off = self.env['hr.leave'].search([
                ('employee_id', '=', attendance.employee_id.id),
                # ('request_unit_half', '=', True),
                ('request_unit_hours', '=', False),
                ('state', '=', 'validate'),
                ('date_from', '<=', attendance.attendance_date),
                '|',
                ('date_to', '=', False),
                ('date_to', '>=', attendance.attendance_date),
            ])
            return time_off

    def get_custom_time_off(self, attendance):
        if attendance:
            time_off = self.env['hr.leave'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('request_unit_hours', '=', True),
                ('state', '=', 'validate'),
                ('date_from', '<=', attendance.attendance_date),
                '|',
                ('date_to', '=', False),
                ('date_to', '>=', attendance.attendance_date),
            ])
            return time_off

    def _get_start_of_attendance(self, attendance, employee_tz, current_time):
        time_off = self.get_time_off(attendance)
        custom_time_off = self.get_custom_time_off(attendance)
        global_time_off = attendance.employee_id.resource_calendar_id.global_leave_ids.filtered(
            lambda l: l.date_from.date() <= current_time.date() <= (l.date_to.date() if l.date_to else l.date_from.date())
        )

        if sum(time_off.mapped('number_of_days')) >= 1:
            return None

        have_time_off_am = any(leave.request_date_from_period == 'am' for leave in time_off)
        have_time_off_pm = any(leave.request_date_from_period == 'pm' for leave in time_off)
        working_schedule = attendance.working_schedule_id

        attendance_period = working_schedule.attendance_ids.filtered(
            lambda a: a.dayofweek == str(current_time.weekday()) and a.day_period != 'lunch'
        )

        if not attendance_period:
            return None

        if have_time_off_am and have_time_off_pm:
            return None

        if have_time_off_am:
            attendance_period = attendance_period.filtered(lambda a: a.day_period == 'afternoon')
        elif have_time_off_pm:
            attendance_period = attendance_period.filtered(lambda a: a.day_period == 'morning')
        else:
            attendance_period = attendance_period.filtered(lambda a: a.day_period == 'morning')

        start_work = current_time.replace(hour=int(attendance_period.hour_from),
                                            minute=int((attendance_period.hour_from % 1) * 60), second=0)

        for global_to in global_time_off.sorted(key=lambda r: r.date_from):
            leave_start = global_to.date_from.astimezone(employee_tz)
            leave_end = global_to.date_to.astimezone(employee_tz)
            if leave_start <= start_work < leave_end:
                start_work = leave_end
                break

        valid_custom_time_off = custom_time_off.filtered(
            lambda r: r.request_hour_from <= attendance_period.hour_from < r.request_hour_to
        )

         # --- Điều chỉnh theo nghỉ theo giờ tùy chỉnh ---
        # for custom_to in custom_time_off.sorted(key=lambda r: r.request_hour_from):
        for custom_to in valid_custom_time_off.sorted(key=lambda r: r.request_hour_from):
            leave_hour_from = custom_to.request_hour_from
            leave_hour_to = custom_to.request_hour_to
            leave_start = current_time.replace(hour=int(leave_hour_from),
                                                minute=int((leave_hour_from % 1) * 60), second=0)
            leave_end = current_time.replace(hour=int(leave_hour_to),
                                                minute=int((leave_hour_to % 1) * 60), second=0)
            if leave_start <= start_work < leave_end:
                start_work = leave_end
                break # Found the relevant custom time off, no need to check further

        return start_work

    def _get_end_of_attendance(self, attendance, employee_tz, current_time):
        time_off = self.get_time_off(attendance)
        custom_time_off = self.get_custom_time_off(attendance)
        global_time_off = attendance.employee_id.resource_calendar_id.global_leave_ids.filtered(
            lambda l: l.date_from.date() <= current_time.date() <= (l.date_to.date() if l.date_to else l.date_from.date())
        )
        if sum(time_off.mapped('number_of_days')) >= 1:
            return None
        have_time_off_am = any(leave.request_date_from_period == 'am' for leave in time_off)
        have_time_off_pm = any(leave.request_date_from_period == 'pm' for leave in time_off)
        working_schedule = attendance.working_schedule_id

        attendance_period = working_schedule.attendance_ids.filtered(
            lambda a: a.dayofweek == str(current_time.weekday()) and a.day_period != 'lunch'
        )

        if not attendance_period:
            return None

        if have_time_off_am and have_time_off_pm:
            return None

        if have_time_off_am:
            attendance_period = attendance_period.filtered(lambda a: a.day_period == 'afternoon')
        elif have_time_off_pm:
            attendance_period = attendance_period.filtered(lambda a: a.day_period == 'morning')
        else:
            attendance_period = attendance_period.filtered(lambda a: a.day_period == 'afternoon')

        end_work = current_time.replace(hour=int(attendance_period.hour_to),
                                            minute=int((attendance_period.hour_to % 1) * 60), second=0)

        for global_to in global_time_off.sorted(key=lambda r: r.date_from):
            leave_start = global_to.date_from.astimezone(employee_tz)
            leave_end = global_to.date_to.astimezone(employee_tz)
            if leave_start < end_work <= leave_end:
                end_work = leave_start
                break

        valid_custom_time_off = custom_time_off.filtered(
            # lambda r: r.request_hour_from < attendance_period.hour_to <= r.request_hour_to
            lambda r: r.request_hour_from < attendance_period.hour_to <= r.request_hour_to
        )

         # --- Điều chỉnh theo nghỉ theo giờ tùy chỉnh ---
        # for custom_to in custom_time_off.sorted(key=lambda r: r.request_hour_from):
        for custom_to in valid_custom_time_off.sorted(key=lambda r: r.request_hour_from):
            leave_hour_from = custom_to.request_hour_from
            leave_hour_to = custom_to.request_hour_to
            leave_start = current_time.replace(hour=int(leave_hour_from),
                                                minute=int((leave_hour_from % 1) * 60), second=0)
            leave_end = current_time.replace(hour=int(leave_hour_to),
                                                minute=int((leave_hour_to % 1) * 60), second=0)
            if leave_start < end_work <= leave_end:
                end_work = leave_start
                break
        return end_work


    def action_recalculate_att(self):
        dayoff = self.get_time_off()
        