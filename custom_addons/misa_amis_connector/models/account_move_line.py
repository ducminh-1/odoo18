import logging

from odoo import fields, models
from odoo.fields import Command

_logger = logging.getLogger(__name__)

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    misa_sa_voucher_lines = fields.Many2many(
        "misa.sa_voucher.line",
        "account_move_line_sa_voucher_rel",
        "account_move_line_id",
        "sa_voucher_line_id",
        string="MISA SA Voucher Lines",
    )

    def _get_price_unit_excl_vat(self):
        self.ensure_one()
        if self.price_subtotal == 0.0 or self.quantity == 0.0:
            return 0.0
        return self.price_subtotal / self.quantity

    def _prepare_sa_voucher_line(self, **optional_values):
        self.ensure_one()
        tax_id = self.tax_ids[0] if self.tax_ids else False
        res = {
            "sequence": self.sequence,
            # 'credit_account': optional_values.get('credit_account'),
            "exchange_rate_operator": "*",
            "product_id": self.product_id.id,
            # 'inventory_item_code': optional_values.get('inventory_item_code'),
            # "description": self.name,
            # 'inventory_item_type': optional_values.get('inventory_item_type'),
            # 'debit_account': optional_values.get('debit_account'),
            # 'unit_name': self.product_uom.name,
            # 'main_unit_name': optional_values.get('main_unit_name', self.product_uom.name),
            # "main_unit_price": self.price_unit,
            "main_unit_price": self._get_price_unit_excl_vat(),
            "main_quantity": self.quantity,
            "quantity": self.quantity,
            # "unit_price": self.price_unit,
            "unit_price": self._get_price_unit_excl_vat(),
            "amount_oc": self.price_subtotal,
            "amount": self.price_subtotal,
            # "discount_rate": self.discount,
            # "discount_amount_oc": self.price_subtotal * (self.discount / 100.0),
            # "discount_amount": self.price_subtotal * (self.discount / 100.0),
            "discount_rate": 0.0,
            "discount_amount_oc": 0.0,
            "discount_amount": 0.0,
            "vat_rate": tax_id.amount if tax_id else 0.0,
            "vat_amount_oc": self.price_total - self.price_subtotal,
            "vat_amount": self.price_total - self.price_subtotal,
            "vat_account": tax_id.cash_basis_transition_account_id.misa_account_number
            if tax_id
            else "311",
            "main_convert_rate": 1.0,
            "invoice_line_ids": [Command.link(self.id)],
        }
        if optional_values:
            res.update(optional_values)
        return res
