import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class OvertimeType(models.Model):
    _inherit = "overtime.type"

    # state = fields.Selection([('draft', 'Draft'),
    #                           ('f_approve', 'Waiting'),
    #                           ('approved', 'Approved'),
    #                           ('refused', 'Refused')], string="state",
    #                          default="draft", help="State of the overtime "
    #                                                "request.")
    manager_id = fields.Many2one('res.users', help="Manager for Overtime Type")
