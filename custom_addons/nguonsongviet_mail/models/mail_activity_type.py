import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class MailActivityType(models.Model):
    _inherit = "mail.activity.type"

    keep_done = fields.Boolean(default=True, readonly=True)
