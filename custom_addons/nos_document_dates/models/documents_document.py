import logging
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Document(models.Model):
    _inherit = "documents.document"

    start_date = fields.Date(tracking=True)
    end_date = fields.Date(tracking=True)
    # Trạng thái hiệu lực
    status_validity = fields.Selection(
        [
            ("valid", "Valid"),
            ("expired", "Expired"),
            ("about_to_expire", "About to Expire"),
            ("no_validity", "No Validity"),
        ],
        compute="_compute_status_validity",
        store=True,
        tracking=True,
    )
    handover_date = fields.Date(string="Handover Date", tracking=True)
    profile_code = fields.Char(string="Profile Code", tracking=True)
    contract_code = fields.Char(string="Contract Code", tracking=True)

    _sql_constraints = [
        (
            "check_date",
            "CHECK(start_date <= end_date)",
            "The start date must be before or equal to the end date.",
        ),
    ]

    @api.depends("start_date", "end_date")
    def _compute_status_validity(self):
        for record in self:
            if not record.start_date and not record.end_date:
                record.status_validity = "no_validity"
            elif record.end_date and record.end_date < fields.Date.today():
                record.status_validity = "expired"
            elif (
                record.end_date
                and record.end_date >= fields.Date.today()
                and record.end_date <= fields.Date.today() + timedelta(days=7)
            ):
                record.status_validity = "about_to_expire"
            else:
                record.status_validity = "valid"

    def cron_update_status_validity(self):
        documents = self.search(
            [
                "|",
                ("start_date", "!=", False),
                ("end_date", "!=", False),
            ]
        )
        documents._compute_status_validity()
        _logger.info("Updated status validity for %d documents", len(documents))
