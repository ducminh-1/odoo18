import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class MisaBranch(models.Model):
    _name = "misa.branch"
    _description = "MISA Branch"

    misa_id = fields.Char()
    misa_app_id = fields.Many2one("misa.app", required=True, ondelete="cascade")
    name = fields.Char(required=True)
