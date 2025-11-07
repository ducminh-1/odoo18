import logging

from odoo import models, fields, api, _
from odoo import http
from odoo.addons.hr_attendance.controllers.main import HrAttendance as BaseHrAttendance
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrAttendance(BaseHrAttendance):

    @http.route('/hr_attendance/manual_selection', type="json", auth="public")
    def manual_selection_with_geolocation(self, token, employee_id, pin_code, latitude=False, longitude=False):
        if not latitude or not longitude:
            raise UserError(_("Geolocation data is required for manual attendance selection."))
        return super().manual_selection_with_geolocation(token, employee_id, pin_code, latitude, longitude)

    @http.route('/hr_attendance/systray_check_in_out', type="json", auth="user")
    def systray_attendance(self, latitude=False, longitude=False):
        if not latitude or not longitude:
            raise UserError(_("Geolocation data is required for systray attendance."))
        return super().systray_attendance(latitude, longitude)
