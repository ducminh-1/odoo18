import logging

from odoo import models

_logger = logging.getLogger(__name__)


class BaseModel(models.AbstractModel):
    _inherit = "base"

    def _phone_format_number(
        self, number, country, force_format="E164", raise_exception=False
    ):
        # Override the _phone_format_number method to handle the phone number formatting
        return number or False
