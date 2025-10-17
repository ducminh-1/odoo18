import random
import string

from odoo import api, fields, models


class LinkTrackerCode(models.Model):
    _inherit = "link.tracker.code"

    @api.model
    def get_random_code_string(self):
        size = 5
        while True:
            code_proposition = "".join(
                random.choice(string.ascii_letters + string.digits) for _ in range(size)
            )

            if self.search([("code", "=", code_proposition)]):
                continue
                # size += 1
            else:
                return code_proposition


class LinkTracker(models.Model):
    _inherit = "link.tracker"

    short_url = fields.Char(
        string="Tracked URL", compute="_compute_short_url", readonly=False
    )
