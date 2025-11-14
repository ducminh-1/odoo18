from odoo import api, models, _, fields

class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _parse_duration_to_days(self, duration_display):
        duration_display = (duration_display or "").strip().lower()
        if not duration_display:
            return 0.0
        
        if "days" in duration_display:
            return float(duration_display.replace("days", "").strip())

        if "giờ" in duration_display:
            time_part = duration_display.replace("giờ", "").strip()
            if ":" in time_part:
                hours, minutes = map(int, time_part.split(":"))
                return (hours + minutes / 60.0) / 24.0
            else:
                return float(time_part) / 24.0
        return 0.0