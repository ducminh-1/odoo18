import logging

from odoo import fields, models
from odoo.tools.sql import SQL

_logger = logging.getLogger(__name__)


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    team_id = fields.Many2one("purchase.team", "Purchase Team", readonly=True)

    def _select(self) -> SQL:
        return SQL(
            """%s,
            po.team_id as team_id
        """,
            super()._select(),
        )

    def _groupby(self) -> SQL:
        return SQL(
            """%s,
            po.team_id
        """,
            super()._groupby(),
        )
