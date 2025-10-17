import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockLocation(models.Model):
    _inherit = "stock.location"

    misa_stock_code = fields.Char(string="Mã kho Misa")
