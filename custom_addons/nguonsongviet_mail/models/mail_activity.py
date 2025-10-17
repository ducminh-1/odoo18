import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    _inherit = "mail.activity"

    hours_diff = fields.Float(compute="_compute_hours_diff", store=True)
    days_diff = fields.Float(compute="_compute_hours_diff", store=True)
    working_state = fields.Selection(
        [
            ("in_progress", "In Progress"),
            ("late", "Late"),
            ("on_time", "On Time"),
            ("early", "Early"),
        ],
        compute="_compute_working_state",
        store=True,
    )

    @api.depends("date_deadline", "date_done")
    def _compute_hours_diff(self):
        for activity in self:
            if activity.date_done and activity.date_deadline:
                hours_diff = (
                    activity.date_done - activity.date_deadline
                ).total_seconds() / 3600
                activity.hours_diff = hours_diff
                activity.days_diff = hours_diff / 24

    @api.depends("hours_diff")
    def _compute_working_state(self):
        not_done_activities = self.filtered(lambda activity: not activity.date_done)
        not_done_activities.working_state = "in_progress"
        for activity in self - not_done_activities:
            if activity.hours_diff > 0:
                activity.working_state = "late"
            elif activity.hours_diff < 0:
                activity.working_state = "early"
            else:
                activity.working_state = "on_time"
