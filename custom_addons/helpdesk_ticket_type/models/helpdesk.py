import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HelpdeskSLA(models.Model):
    _inherit = "helpdesk.sla"

    ticket_type_id = fields.Many2one(
        "helpdesk.ticket.type",
        "Ticket Type",
        help="Only apply the SLA to a specific ticket type. If left empty it will apply to all types.",  # noqa: E501
    )
