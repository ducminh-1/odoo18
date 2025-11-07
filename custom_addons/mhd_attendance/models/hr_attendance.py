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

                calendar = attendance._get_employee_calendar()

                if not calendar:
                    raise UserError(_("No working schedule found for employee %s", attendance.employee_id.name))

                tz = timezone(calendar.tz)
                check_in_tz = attendance.check_in.astimezone(tz)
                check_out_tz = attendance.check_out.astimezone(tz)
                lunch_intervals = attendance.employee_id._employee_attendance_intervals(check_in_tz, check_out_tz,
                                                                                        lunch=True)
                if not standard_check_in or not standard_check_out:
                    if not standard_check_in:
                        raise UserError(_("No standard check in found!"))
                    if not standard_check_out:
                        raise UserError(_("No standard check out found!"))
                max_hours_per_day = ((standard_check_out - standard_check_in).total_seconds() - lunch_time) / 3600.0
                # if check_out_local > standard_check_out and ((check_in_local - standard_check_in).total_seconds() / 3600 > 0.5):
                if check_out_local > standard_check_out:
                    if 0 < ((check_in_local - standard_check_in).total_seconds() / 3600) <= 0.5:
                        # Nếu vào muộn dưới 30 phút, thì du di giờ làm việc
                        standard_check_out = standard_check_out + timedelta(minutes=30)  # Cộng thêm 30 phút để tránh trường hợp check_out đúng giờ kết thúc ca

                if check_in_local <= standard_check_in and check_out_local >= standard_check_out:
                    # Trường hợp 1: check_in và check_out bao quanh khoảng chuẩn
                    attendance_intervals = Intervals([(standard_check_in.astimezone(tz),
                                                       standard_check_out.astimezone(tz),
                                                       attendance)]) - lunch_intervals
                elif standard_check_in <= check_in_local <= standard_check_out:
                    if check_out_local > standard_check_out:
                        # Trường hợp 2: check_in hợp lệ, check_out ngoài khoảng chuẩn
                        attendance_intervals = Intervals(
                            [(check_in_tz, standard_check_out.astimezone(tz), attendance)]) - lunch_intervals
                    else:
                        # Trường hợp 3: check_in và check_out đều hợp lệ
                        attendance_intervals = Intervals([(check_in_tz, check_out_tz, attendance)]) - lunch_intervals
                elif check_in_local < standard_check_in <= check_out_local <= standard_check_out:
                    # Trường hợp 4: check_in ngoài khoảng chuẩn, check_out trong khoảng chuẩn
                    attendance_intervals = Intervals(
                        [(standard_check_in.astimezone(tz), check_out_tz, attendance)]) - lunch_intervals
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

    @api.depends("check_in", "check_out")
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
            # tz = pytz.timezone("Asia/Ho_Chi_Minh")
            # check_in_tz = datetime.now(tz)
            # check_out_tz = datetime.now(tz)
            weekday = str(check_in_tz.weekday())  # 0 = Monday
                
            # Lấy giờ làm trong ngày từ lịch làm việc
            day_attendances = calendar.attendance_ids.filtered(lambda a: a.dayofweek == weekday)


            
            if not day_attendances:
                continue  # Không có ca làm trong ngày này

            # Giờ làm buổi sáng sớm nhất và buổi chiều trễ nhất
            start_hour = min(day_attendances.mapped('hour_from'))
            end_hour = max(day_attendances.mapped('hour_to'))

            start_work = check_in_tz.replace(hour=int(start_hour), minute=int((start_hour % 1) * 60), second=0, microsecond=0)
            end_work = check_in_tz.replace(hour=int(end_hour), minute=int((end_hour % 1) * 60), second=0, microsecond=0)


            # Cho phép trễ 15 phút
            allowed_late = start_work + timedelta(minutes=15)
            time_off = self.get_time_off(att)

            # Kiểm tra nghỉ phép nữa ngày
            have_time_off_am = any(leave.request_date_from_period == 'am' for leave in time_off)
            have_time_off_pm = any(leave.request_date_from_period == 'pm' for leave in time_off)
            
            # Lấy giờ làm mặc định buổi sáng và buổi chiều
            standard_check_in = self._get_standard_working_hours(att, 'morning', tz, check_in_tz)[1]
            standard_check_out = self._get_standard_working_hours(att, 'afternoon', tz, check_out_tz)[0]
            # Lấy giờ làm trong ngày nếu có giờ tùy chinh
            period_start_am, period_end_am, delta_lunch_break = self._get_standard_working_hours(att, 'morning', tz, check_in_tz)
            period_start_pm, period_end_pm, delta_lunch_break = self._get_standard_working_hours(att, 'afternoon', tz, check_in_tz)


            if period_start_am and period_start_am < check_in_tz:
                att.late_hours = float_round((check_in_tz - period_start_am).total_seconds() / 3600.0, 2)
            elif period_start_pm and period_start_pm < check_in_tz:
                att.late_hours = float_round((check_in_tz - period_start_am).total_seconds() / 3600.0, 2)

            if period_end_am > check_out_tz:
                att.early_hours = float_round((period_end_am - check_out_tz).total_seconds() / 3600.0, 2)
            elif period_end_pm > check_out_tz:
                att.early_hours = float_round((period_end_pm - check_out_tz).total_seconds() / 3600.0, 2)
                continue

            am_end = standard_check_in.astimezone(tz) if standard_check_in else end_work
            pm_start = standard_check_out.astimezone(tz) if standard_check_out else start_work
            if not have_time_off_am and not have_time_off_pm:
                # Tính giờ đi trễ cả ngày
                if check_in_tz > allowed_late and not period_end_am:
                    att.late_hours = float_round((check_in_tz - start_work).total_seconds() / 3600.0, 2)
                if check_out_tz < end_work and not period_end_pm:
                    att.early_hours = float_round((end_work - check_out_tz).total_seconds() / 3600.0, 2)
                
            elif have_time_off_am and not have_time_off_pm:
                # Nghỉ sáng → chỉ tính ca chiều
                if check_in_tz > pm_start + timedelta(minutes=15):
                    att.late_hours = float_round((check_in_tz - pm_start).total_seconds() / 3600.0, 2)
                if check_out_tz < end_work:
                    att.early_hours = float_round((end_work - check_out_tz).total_seconds() / 3600.0, 2)

            elif have_time_off_pm and not have_time_off_am:
                # Nghỉ chiều → chỉ tính ca sáng
                if check_in_tz > allowed_late:
                    att.late_hours = float_round((check_in_tz - start_work).total_seconds() / 3600.0, 2)
                if check_out_tz < am_end:
                    att.early_hours = float_round((am_end - check_out_tz).total_seconds() / 3600.0, 2)

            else:
                # Nghỉ cả ngày (sáng + chiều)
                att.late_hours = att.early_hours = 0.0
            
            

    def _get_standard_working_hours(self, record, period, employee_tz, current_time, release_date=False):
        standard_check_in = None
        standard_check_out = None
        delta_lunch_break = 0.0

        # Lấy thông tin time off của nhân viên
        time_off = self.get_time_off(record)
        custom_time_off = self.get_custom_time_off(record)

        # Kiểm tra nếu nhân viên nghỉ full ngày
        if sum(time_off.mapped('number_of_days')) >= 1:
            raise UserError(_("You cannot create attendance records when you have time off for that day."))

        # Kiểm tra nghỉ buổi sáng hoặc buổi chiều
        have_time_off_am = any(leave.request_date_from_period == 'am' for leave in time_off)
        have_time_off_pm = any(leave.request_date_from_period == 'pm' for leave in time_off)

        # Lấy attendance_period dựa trên period và ngày hiện tại
        attendance_period = record.working_schedule_id.attendance_ids.filtered(
            lambda a: a.dayofweek == str(current_time.weekday()) and a.day_period == period
        ) if not release_date else record.employee_id.release_working_schedule_id.attendance_ids.filtered(
            lambda a: a.dayofweek == str(current_time.weekday()) and a.day_period == period
        )

        lunch_break = record.working_schedule_id.attendance_ids.filtered(
            lambda l: l.dayofweek == str(current_time.weekday()) and l.day_period == "lunch"
        ) if not release_date else record.employee_id.release_working_schedule_id.attendance_ids.filtered(
            lambda a: a.dayofweek == str(current_time.weekday()) and a.day_period == "lunch"
        )
        if lunch_break:
            lunch_break_start = current_time.replace(hour=int(lunch_break.hour_from),
                                                     minute=int((lunch_break.hour_from % 1) * 60), second=0)
            lunch_break_end = current_time.replace(hour=int(lunch_break.hour_to),
                                                   minute=int((lunch_break.hour_to % 1) * 60), second=0)
            delta_lunch_break = (lunch_break_end - lunch_break_start).total_seconds()

        if period == 'morning':
            if have_time_off_pm:
                # Nếu nghỉ chiều, chỉ lấy khung giờ buổi sáng
                attendance_period = record.working_schedule_id.attendance_ids.filtered(
                    lambda a: a.dayofweek == str(current_time.weekday()) and a.day_period == 'morning'
                ) if not release_date else record.employee_id.release_working_schedule_id.attendance_ids.filtered(
                    lambda a: a.dayofweek == str(current_time.weekday()) and a.day_period == "morning"
                )
                delta_lunch_break = delta_lunch_break  # Lunch break vẫn tính vì đây là buổi sáng

            if have_time_off_am:
                # Nếu nghỉ sáng, khung giờ làm việc buổi sáng bị giới hạn
                attendance_period = record.working_schedule_id.attendance_ids.filtered(
                    lambda a: a.dayofweek == str(current_time.weekday()) and a.day_period == 'afternoon'
                ) if not release_date else record.employee_id.release_working_schedule_id.attendance_ids.filtered(
                    lambda a: a.dayofweek == str(current_time.weekday()) and a.day_period == "afternoon"
                )
                delta_lunch_break = 0.0  # Không tính lunch vì đây là buổi chiều (làm bù)

            if attendance_period and have_time_off_pm:
                if len(attendance_period) > 1:
                    # Check-in: lấy thời gian bắt đầu sớm nhất
                    attendance_check_in = max(attendance_period, key=lambda a: a.duration_days, default=None)
                    # Check-out: lấy thời gian kết thúc muộn nhất
                    attendance_check_out = min(attendance_period, key=lambda a: a.duration_days, default=None)
                    if attendance_check_in and attendance_check_out:
                        standard_check_in = current_time.replace(hour=int(attendance_check_in.hour_from),
                                                                 minute=int((attendance_check_in.hour_from % 1) * 60),
                                                                 second=0)
                        standard_check_out = current_time.replace(hour=int(attendance_check_out.hour_to),
                                                                  minute=int((attendance_check_out.hour_to % 1) * 60),
                                                                  second=0)
                else:
                    standard_check_in = current_time.replace(hour=int(attendance_period.hour_from),
                                                         minute=int((attendance_period.hour_from % 1) * 60),
                                                         second=0)
                    standard_check_out = current_time.replace(hour=int(attendance_period.hour_to),
                                                              minute=int((attendance_period.hour_to % 1) * 60),
                                                              second=0)


            if attendance_period and have_time_off_am:
                standard_check_in = current_time.replace(hour=int(attendance_period.hour_from),
                                                         minute=int((attendance_period.hour_from % 1) * 60),
                                                         second=0)
                standard_check_out = current_time.replace(hour=int(attendance_period.hour_to),
                                                          minute=int((attendance_period.hour_to % 1) * 60),
                                                          second=0)
            if attendance_period and not have_time_off_pm and not have_time_off_am:
                if len(attendance_period) > 1:
                    # Check-in: lấy thời gian bắt đầu sớm nhất
                    attendance_check_in = max(attendance_period, key=lambda a: a.duration_days, default=None)
                    standard_check_in = current_time.replace(hour=int(attendance_check_in.hour_from),
                                                             minute=int((attendance_check_in.hour_from % 1) * 60),
                                                             second=0
                    )
                else:
                    standard_check_in = current_time.replace(hour=int(attendance_period.hour_from),
                                                             minute=int((attendance_period.hour_from % 1) * 60),
                                                             second=0
                                                             )

        elif period == 'afternoon':
            if have_time_off_am:
                # Nếu nghỉ sáng, chỉ lấy khung giờ buổi chiều
                attendance_period = record.working_schedule_id.attendance_ids.filtered(
                    lambda a: a.dayofweek == str(current_time.weekday()) and a.day_period == 'afternoon'
                ) if not release_date else record.employee_id.release_working_schedule_id.attendance_ids.filtered(
                    lambda a: a.dayofweek == str(current_time.weekday()) and a.day_period == "afternoon"
                )
                delta_lunch_break = 0.0  # Không tính lunch break vì đây là buổi chiều

            if have_time_off_pm:
                # Nếu nghỉ chiều, khung giờ làm việc buổi chiều bị giới hạn
                attendance_period = record.working_schedule_id.attendance_ids.filtered(
                    lambda a: a.dayofweek == str(current_time.weekday()) and a.day_period == 'morning'
                ) if not release_date else record.employee_id.release_working_schedule_id.attendance_ids.filtered(
                    lambda a: a.dayofweek == str(current_time.weekday()) and a.day_period == "morning"
                )
                delta_lunch_break = delta_lunch_break  # Lunch break được tính vì đây là buổi sáng

            if attendance_period and have_time_off_pm:
                if len(attendance_period) > 1:
                    # Check-in: lấy thời gian bắt đầu sớm nhất
                    attendance_check_in = max(attendance_period, key=lambda a: a.duration_days, default=None)
                    # Check-out: lấy thời gian kết thúc muộn nhất
                    attendance_check_out = min(attendance_period, key=lambda a: a.duration_days, default=None)

                    if attendance_check_in and attendance_check_out:
                        standard_check_in = current_time.replace(hour=int(attendance_check_in.hour_from),
                                                                 minute=int((attendance_check_in.hour_from % 1) * 60),
                                                                 second=0)
                        standard_check_out = current_time.replace(hour=int(attendance_check_out.hour_to),
                                                                  minute=int((attendance_check_out.hour_to % 1) * 60),
                                                                  second=0)
                else:
                    standard_check_in = current_time.replace(hour=int(attendance_period.hour_from),
                                                             minute=int((attendance_period.hour_from % 1) * 60),
                                                             second=0)
                    standard_check_out = current_time.replace(hour=int(attendance_period.hour_to),
                                                              minute=int((attendance_period.hour_to % 1) * 60),
                                                              second=0)
            if attendance_period and have_time_off_am:
                standard_check_in = current_time.replace(hour=int(attendance_period.hour_from),
                                                         minute=int((attendance_period.hour_from % 1) * 60),
                                                         second=0)
                standard_check_out = current_time.replace(hour=int(attendance_period.hour_to),
                                                          minute=int((attendance_period.hour_to % 1) * 60),
                                                          second=0)
            if attendance_period and not have_time_off_pm and not have_time_off_am:
                if len(attendance_period) > 1:
                    # Check-in: lấy thời gian bắt đầu sớm nhất
                    attendance_check_out = max(attendance_period, key=lambda a: a.duration_days, default=None)
                    standard_check_out = current_time.replace(hour=int(attendance_check_out.hour_to),
                                                             minute=int((attendance_check_out.hour_to % 1) * 60),
                                                              second=0
                    )
                else:
                    standard_check_out = current_time.replace(hour=int(attendance_period.hour_to),
                                                             minute=int((attendance_period.hour_to % 1) * 60),
                                                              second=0
                                                             )

        return standard_check_in, standard_check_out, delta_lunch_break

    def _get_standard_working_hours(self, record, period, employee_tz, current_time, release_date=False):
        standard_check_in = None
        standard_check_out = None
        delta_lunch_break = 0.0

        # Lấy thông tin nghỉ phép
        time_off = self.get_time_off(record)  # nghỉ nửa buổi
        custom_time_off = self.get_custom_time_off(record)  # nghỉ theo giờ

        # Nếu nghỉ full ngày
        if any(leave.request_date_from_period == 'full' for leave in time_off) or sum(time_off.mapped('number_of_days')) >= 1:
            raise UserError(_("You cannot create attendance records when you have full-day time off for that day."))

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
            return None, None, 0.0

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
        for leave in custom_time_off:
            # import pdb; pdb.set_trace()
            leave_start = leave.date_from.astimezone(employee_tz)
            leave_end = leave.date_to.astimezone(employee_tz)

            # Nếu leave nằm trong khung giờ làm việc
            if leave_start.date() == current_time.date():
                # Nếu nghỉ giữa ca, cắt lại thời gian làm
                if period_start and leave_start <= period_start < leave_end:
                    period_start = leave_end  # bắt đầu sau khi nghỉ xong
                if period_end and leave_start < period_end <= leave_end:
                    period_end = leave_start  # kết thúc trước khi nghỉ

                # Nếu toàn bộ period nằm trong giờ nghỉ => không làm
                if period_start and period_end and leave_start <= period_start and period_end <= leave_end:
                    period_start = None
                    period_end = None
                # print(period_start)
                # print(period_end)
                # print(delta_lunch_break)
                
        # if period_end:
        #     period_end = period_end + timedelta(minutes=30) # Cộng thêm 30 phút để tránh trường hợp check_out đúng giờ kết thúc ca
        return period_start, period_end, delta_lunch_break

    def get_time_off(self, attendance):
        if attendance:
            time_off = self.env['hr.leave'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('request_unit_half', '=', True),
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
