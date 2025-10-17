import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HelpdeskTicketType(models.Model):
    _name = "helpdesk.ticket.type"
    _description = "Helpdesk Ticket Type"
    _order = "sequence"

    name = fields.Char("Type", required=True)
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ("name_uniq", "unique (name)", "Type name already exists !"),
    ]
