import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = "hr.contract"

    deduct_late_early = fields.Boolean(string="Deduct Late/Early Leave", default=False,
                                       help="If checked, late arrival and early leave hours will be calculated for this contract.")
