import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    is_loyalty_program = fields.Boolean(
        string="Is Loyalty Program",
        # compute='_compute_is_loyalty_program',
        # store=True,
        # readonly=False
    )
    # show_coupon_prefix = fields.Boolean(
    #     compute='_compute_show_coupon_prefix',
    #     store=True
    # )
    # coupon_prefix = fields.Char()
