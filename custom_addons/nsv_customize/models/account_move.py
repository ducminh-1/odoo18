import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_id = fields.Many2one(
        "sale.order", string="Sale Order", compute="_compute_sale_id", store=True
    )
    invoice_number = fields.Char("Invoice Number")
    channel_id = fields.Many2one(
        "sale.channel", "Channel", related="sale_id.channel_id"
    )
    # pos_account_tag_id = fields.Many2one('account.analytic.tag', 'POS', related='sale_id.pos_account_tag_id')
    pos_analytic_account_id = fields.Many2one(
        "account.analytic.account", "POS", related="sale_id.pos_analytic_account_id"
    )
    employee_id = fields.Many2one("hr.employee", "Employee", tracking=True)
    landed_costs_visible = fields.Boolean(
        compute="_compute_landed_costs_visible", search="_search_landed_costs_visible"
    )

    def _search_landed_costs_visible(self, operator, value):
        assert operator in ("=", "!=", "<>") and value in (
            True,
            False,
        ), "Operation not supported"
        landed_costs_visible_ids = self.search(
            [
                ("landed_costs_ids", "=", False),
                ("line_ids.is_landed_costs_line", "=", True),
            ]
        ).ids
        if (operator == "=" and value is True) or (
            operator in ("<>", "!=") and value is False
        ):
            search_operator = "in"
        else:
            search_operator = "not in"
        return [("id", search_operator, landed_costs_visible_ids)]

    @api.depends("invoice_origin")
    def _compute_sale_id(self):
        for record in self:
            if record.invoice_origin:
                sale_ids = self.env["sale.order"].search(
                    [("name", "=", record.invoice_origin)]
                )
                record["sale_id"] = sale_ids and sale_ids[0] or False

    # @api.depends(
    #     'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
    #     'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
    #     'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
    #     'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
    #     'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
    #     'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
    #     'line_ids.debit',
    #     'line_ids.credit',
    #     'line_ids.currency_id',
    #     'line_ids.amount_currency',
    #     'line_ids.amount_residual',
    #     'line_ids.amount_residual_currency',
    #     'line_ids.payment_id.state',
    #     'line_ids.full_reconcile_id')
    # def _compute_amount(self):
    #     for move in self:
    #
    #         if move.payment_state == 'invoicing_legacy':
    #             # invoicing_legacy state is set via SQL when setting setting field
    #             # invoicing_switch_threshold (defined in account_accountant).
    #             # The only way of going out of this state is through this setting,
    #             # so we don't recompute it here.
    #             move.payment_state = move.payment_state
    #             continue
    #
    #         total_untaxed = 0.0
    #         total_untaxed_currency = 0.0
    #         total_tax = 0.0
    #         total_tax_currency = 0.0
    #         total_to_pay = 0.0
    #         total_residual = 0.0
    #         total_residual_currency = 0.0
    #         total = 0.0
    #         total_currency = 0.0
    #         currencies = move._get_lines_onchange_currency().currency_id
    #
    #         for line in move.line_ids:
    #             if move.is_invoice(include_receipts=True):
    #                 # === Invoices ===
    #
    #                 if not line.exclude_from_invoice_tab:
    #                     # Untaxed amount.
    #                     total_untaxed += line.balance
    #                     total_untaxed_currency += line.amount_currency
    #                     total += line.balance
    #                     total_currency += line.amount_currency
    #                 elif line.tax_line_id:
    #                     # Tax amount.
    #                     total_tax += line.balance
    #                     total_tax_currency += line.amount_currency
    #                     total += line.balance
    #                     total_currency += line.amount_currency
    #                 elif line.account_id.user_type_id.type in ('receivable', 'payable'):
    #                     # Residual amount.
    #                     total_to_pay += line.balance
    #                     total_residual += line.amount_residual
    #                     total_residual_currency += line.amount_residual_currency
    #             else:
    #                 # === Miscellaneous journal entry ===
    #                 if line.debit:
    #                     total += line.balance
    #                     total_currency += line.amount_currency
    #
    #         if move.move_type == 'entry' or move.is_outbound():
    #             sign = 1
    #         else:
    #             sign = -1
    #         move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
    #         move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
    #         move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
    #         move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
    #         move.amount_untaxed_signed = -total_untaxed
    #         move.amount_tax_signed = -total_tax
    #         move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
    #         move.amount_residual_signed = total_residual
    #
    #         currency = len(currencies) == 1 and currencies or move.company_id.currency_id
    #
    #         # Compute 'payment_state'.
    #         new_pmt_state = 'not_paid' if move.move_type != 'entry' else False
    #
    #         if move.is_invoice(include_receipts=True) and move.state == 'posted':
    #
    #             if currency.is_zero(move.amount_residual):
    #                 reconciled_payments = move._get_reconciled_payments()
    #                 if not reconciled_payments or all(payment.is_matched for payment in reconciled_payments):
    #                     new_pmt_state = 'paid'
    #                 else:
    #                     new_pmt_state = move._get_invoice_in_payment_state()
    #             elif currency.compare_amounts(total_to_pay, total_residual) != 0:
    #                 new_pmt_state = 'partial'
    #
    #         if new_pmt_state == 'paid' and move.move_type in ('in_invoice', 'out_invoice', 'entry'):
    #             reverse_type = move.move_type == 'in_invoice' and 'in_refund' or move.move_type == 'out_invoice' and 'out_refund' or 'entry'
    #             reverse_moves = self.env['account.move'].search([('reversed_entry_id', '=', move.id), ('state', '=', 'posted'), ('move_type', '=', reverse_type)])
    #
    #             # We only set 'reversed' state in cas of 1 to 1 full reconciliation with a reverse entry; otherwise, we use the regular 'paid' state
    #             reverse_moves_full_recs = reverse_moves.mapped('line_ids.full_reconcile_id')
    #             if reverse_moves_full_recs.mapped('reconciled_line_ids.move_id').filtered(lambda x: x not in (reverse_moves + reverse_moves_full_recs.mapped('exchange_move_id'))) == move:
    #                 new_pmt_state = 'reversed'
    #
    #         # move.payment_state = new_pmt_state
    #         move.write({"payment_state": new_pmt_state}) # gọi method write kiểm tra cập nhật

    def write(self, vals):
        need_update = self.env["account.move"].sudo()
        for move in self.filtered(
            lambda mv: mv.move_type in ["out_invoice", "out_refund"]
            and not mv.partner_id.is_company
            and not mv.partner_id.parent_id
        ):
            line_ids = move.invoice_line_ids.filtered(
                lambda line: line.product_id.type == "product"
            )
            loyalty_point_amount = 1
            need_action = False
            if "payment_state" in vals and line_ids and move.sale_id:
                # thay đổi từ đã thanh toán sang trạng thái khác
                if vals["payment_state"] != "paid" and move.payment_state == "paid":
                    need_action = True
                    # nếu là công nợ âm cộng lại điểm, công nợ bán hàng thì trừ điểm
                    loyalty_point_amount = -1
                # đổi trạng thái thành đã thanh toán và trạng thái trước đó là chưa thanh toán
                elif vals["payment_state"] == "paid" and move.payment_state != "paid":
                    # nếu là công nợ âm trừ điểm, công nợ bán hàng thì cộng điểm
                    need_action = True
            if need_action:
                need_update |= move
        res = super().write(vals)
        for inv in need_update:
            point = inv.amount_total_signed / 1000
            inv.partner_id.update_loyalty_point()
            move_msg = (
                _("Cộng điểm tích lũy thanh toán thành công từ hóa đơn:")
                + " <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>"
                % (self.id, self.name)
                + "<br/>Số điểm: %s" % point
            )
            if loyalty_point_amount < 0:
                move_msg = (
                    _("Trừ điểm tích lũy thanh toán thành công từ hóa đơn:")
                    + " <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>"
                    % (self.id, self.name)
                    + "<br/>Số điểm: %s" % point
                )
            inv.sale_id.message_post(body=move_msg)
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    price_rule = fields.Float(compute="compute_price_rule")
    difference_ratio = fields.Float(compute="compute_price_rule")

    def compute_price_rule(self):
        for line in self:
            price_rule = 0
            difference_ratio = 0
            if line.sale_line_ids:
                price_rule = line.sale_line_ids[0].price_rule
                difference_ratio = line.sale_line_ids[0].difference_ratio
            line.price_rule = price_rule
            line.difference_ratio = difference_ratio
