# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HelpdeskTicketReport(models.Model):
    _inherit = "helpdesk.ticket.report.analysis"

    ticket_type_id = fields.Many2one(
        "helpdesk.ticket.type", string="Ticket Type", readonly=True
    )
    date_order = fields.Datetime(string="Order Date", readonly=True)

    def _select(self):
        select_str = super()._select()
        select_str += ", T.ticket_type_id as ticket_type_id, T.date_order as date_order"
        return select_str
