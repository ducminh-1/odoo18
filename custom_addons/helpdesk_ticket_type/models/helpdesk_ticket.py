import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    ticket_type_id = fields.Many2one("helpdesk.ticket.type", string="Ticket Type")
