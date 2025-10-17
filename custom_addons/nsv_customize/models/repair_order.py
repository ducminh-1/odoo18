from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class RepairOrder(models.Model):
    _inherit = "repair.order"

    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        "Analytic Account",
        copy=False,
        check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="The analytic account related to a sales order.",
    )
    channel_id = fields.Many2one(
        "sale.channel",
        "Channel",
        tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    # channel_account_tag_id = fields.Many2one('account.analytic.tag', related='channel_id.account_tag_id',
    channel_analytic_account_id = fields.Many2one(
        "account.analytic.account",
        related="channel_id.analytic_account_id",
        string="Channel Analytic Account",
    )
    #                                          string="Channel Tag")
    # pos_account_tag_id = fields.Many2one(
    #     'account.analytic.tag', 'POS', tracking=True,
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    pos_analytic_account_id = fields.Many2one(
        "account.analytic.account",
        "POS",
        tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    payment_term_id = fields.Many2one(
        "account.payment.term",
        string="Payment Terms",
        check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    warehouse_id = fields.Many2one("stock.warehouse", compute="_compute_warehouse")

    def _compute_warehouse(self):
        for repair in self:
            if repair.location_id:
                warehouse = self.env["stock.warehouse"].search(
                    [("view_location_id", "parent_of", self.location_id.id)], limit=1
                )
                repair.warehouse_id = warehouse or False

    @api.onchange("partner_id")
    def _onchange_partner_to_channel(self):
        if self.partner_id:
            self.channel_id = self.partner_id.channel_id or False
            if self.partner_id.user_id:
                team_id = self.env["crm.team"].search(
                    [("member_ids", "=", self.partner_id.user_id.id)], limit=1
                )
                self.analytic_account_id = team_id.analytic_account_id or False

    # @api.onchange('location_id')
    # def _onchange_location_to_pos(self):
    #     if self.location_id:
    #         self.pos_account_tag_id = self.warehouse_id.analytic_tag_id or False

    def _create_invoices(self, group=False):
        """Creates invoice(s) for repair order.
        @param group: It is set to true when group invoice is to be generated.
        @return: Invoice Ids.
        """
        grouped_invoices_vals = {}
        repairs = self.filtered(
            lambda repair: repair.state not in ("draft", "cancel")
            and not repair.invoice_id
            and repair.invoice_method != "none"
        )
        for repair in repairs:
            repair = repair.with_company(repair.company_id)
            partner_invoice = repair.partner_invoice_id or repair.partner_id
            if not partner_invoice:
                raise UserError(
                    _("You have to select an invoice address in the repair form.")
                )

            narration = repair.quotation_notes
            currency = repair.pricelist_id.currency_id
            company = repair.env.company

            journal = (
                repair.env["account.move"]
                .with_context(move_type="out_invoice")
                ._get_default_journal()
            )
            if not journal:
                raise UserError(
                    _(
                        "Please define an accounting sales journal for the company %s (%s)."
                    )
                    % (company.name, company.id)
                )

            if (
                partner_invoice.id,
                currency.id,
                company.id,
            ) not in grouped_invoices_vals:
                grouped_invoices_vals[
                    (partner_invoice.id, currency.id, company.id)
                ] = []
            current_invoices_list = grouped_invoices_vals[
                (partner_invoice.id, currency.id, company.id)
            ]

            if not group or len(current_invoices_list) == 0:
                fpos = self.env["account.fiscal.position"].get_fiscal_position(
                    partner_invoice.id, delivery_id=repair.address_id.id
                )
                invoice_vals = {
                    "move_type": "out_invoice",
                    "partner_id": partner_invoice.id,
                    "partner_shipping_id": repair.address_id.id,  # customized value
                    "currency_id": currency.id,
                    "narration": narration,
                    "invoice_origin": repair.name,
                    "repair_ids": [(4, repair.id)],
                    "invoice_line_ids": [],
                    "fiscal_position_id": fpos.id,
                    "invoice_payment_term_id": repair.payment_term_id.id,  # customize: add payment terms to invoice
                }
                if partner_invoice.property_payment_term_id:
                    invoice_vals["invoice_payment_term_id"] = (
                        partner_invoice.property_payment_term_id.id
                    )
                current_invoices_list.append(invoice_vals)
            else:
                # if group == True: concatenate invoices by partner and currency
                invoice_vals = current_invoices_list[0]
                invoice_vals["invoice_origin"] += ", " + repair.name
                invoice_vals["repair_ids"].append((4, repair.id))
                if not invoice_vals["narration"]:
                    invoice_vals["narration"] = narration
                else:
                    invoice_vals["narration"] += "\n" + narration

            # Create invoice lines from operations.
            for operation in repair.operations.filtered(lambda op: op.type == "add"):
                if group:
                    name = repair.name + "-" + operation.name
                else:
                    name = operation.name

                account = operation.product_id.product_tmpl_id._get_product_accounts()[
                    "income"
                ]
                if not account:
                    raise UserError(
                        _(
                            'No account defined for product "%s".',
                            operation.product_id.name,
                        )
                    )

                invoice_line_vals = {
                    "name": name,
                    "account_id": account.id,
                    "quantity": operation.product_uom_qty,
                    "tax_ids": [(6, 0, operation.tax_id.ids)],
                    "product_uom_id": operation.product_uom.id,
                    "price_unit": operation.price_unit,
                    "product_id": operation.product_id.id,
                    "repair_line_ids": [(4, operation.id)],
                    "analytic_tag_ids": [
                        (6, 0, operation.analytic_tag_ids.ids)
                    ],  # customized value
                    "analytic_account_id": repair.analytic_account_id.id
                    or False,  # customized value
                }

                if currency == company.currency_id:
                    balance = -(operation.product_uom_qty * operation.price_unit)
                    invoice_line_vals.update(
                        {
                            "debit": balance > 0.0 and balance or 0.0,
                            "credit": balance < 0.0 and -balance or 0.0,
                        }
                    )
                else:
                    amount_currency = -(
                        operation.product_uom_qty * operation.price_unit
                    )
                    balance = currency._convert(
                        amount_currency,
                        company.currency_id,
                        company,
                        fields.Date.today(),
                    )
                    invoice_line_vals.update(
                        {
                            "amount_currency": amount_currency,
                            "debit": balance > 0.0 and balance or 0.0,
                            "credit": balance < 0.0 and -balance or 0.0,
                            "currency_id": currency.id,
                        }
                    )
                invoice_vals["invoice_line_ids"].append((0, 0, invoice_line_vals))

            # Create invoice lines from fees.
            for fee in repair.fees_lines:
                if group:
                    name = repair.name + "-" + fee.name
                else:
                    name = fee.name

                if not fee.product_id:
                    raise UserError(_("No product defined on fees."))

                account = fee.product_id.product_tmpl_id._get_product_accounts()[
                    "income"
                ]
                if not account:
                    raise UserError(
                        _('No account defined for product "%s".', fee.product_id.name)
                    )

                invoice_line_vals = {
                    "name": name,
                    "account_id": account.id,
                    "quantity": fee.product_uom_qty,
                    "tax_ids": [(6, 0, fee.tax_id.ids)],
                    "product_uom_id": fee.product_uom.id,
                    "price_unit": fee.price_unit,
                    "product_id": fee.product_id.id,
                    "repair_fee_ids": [(4, fee.id)],
                    "analytic_tag_ids": [
                        (6, 0, fee.analytic_tag_ids.ids)
                    ],  # customized value
                    "analytic_account_id": repair.analytic_account_id.id
                    or False,  # customized value
                }

                if currency == company.currency_id:
                    balance = -(fee.product_uom_qty * fee.price_unit)
                    invoice_line_vals.update(
                        {
                            "debit": balance > 0.0 and balance or 0.0,
                            "credit": balance < 0.0 and -balance or 0.0,
                        }
                    )
                else:
                    amount_currency = -(fee.product_uom_qty * fee.price_unit)
                    balance = currency._convert(
                        amount_currency,
                        company.currency_id,
                        company,
                        fields.Date.today(),
                    )
                    invoice_line_vals.update(
                        {
                            "amount_currency": amount_currency,
                            "debit": balance > 0.0 and balance or 0.0,
                            "credit": balance < 0.0 and -balance or 0.0,
                            "currency_id": currency.id,
                        }
                    )
                invoice_vals["invoice_line_ids"].append((0, 0, invoice_line_vals))

        # Create invoices.
        invoices_vals_list_per_company = defaultdict(list)
        for (
            partner_invoice_id,
            currency_id,
            company_id,
        ), invoices in grouped_invoices_vals.items():
            for invoice in invoices:
                invoices_vals_list_per_company[company_id].append(invoice)

        for company_id, invoices_vals_list in invoices_vals_list_per_company.items():
            # VFE TODO remove the default_company_id ctxt key ?
            # Account fallbacks on self.env.company, which is correct with with_company
            self.env["account.move"].with_company(company_id).with_context(
                default_company_id=company_id, default_move_type="out_invoice"
            ).create(invoices_vals_list)

        repairs.write({"invoiced": True})
        repairs.mapped("operations").filtered(lambda op: op.type == "add").write(
            {"invoiced": True}
        )
        repairs.mapped("fees_lines").write({"invoiced": True})

        return dict((repair.id, repair.invoice_id.id) for repair in repairs)

    # def unlink(self):
    #     for repair in self:
    #         moves = self.env['stock.move'].search([('repair_id', '=', repair.id), ('state', '=', 'done')])
    #         if moves:
    #             raise UserError(
    #                 _('You can not delete the repair order with Stock Move done !'))
    #     return super(RepairOrder, self).unlink()
    #
    # def action_repair_cancel(self):
    #     allow_access = self.env.user.has_group('account.group_account_user')
    #     for repair in self:
    #         if (repair.invoice_id.state == 'posted' or repair.state == 'done') and not allow_access:
    #             raise UserError(_("Unable to cancel this repair order because a invoice related to it is posted !"))
    #     return super(RepairOrder, self).action_repair_cancel()

    def action_create_sale_order(self):
        res = super().action_create_sale_order()
        for repair in self:
            if repair.channel_id and repair.sale_order_id:
                repair.sale_order_id.channel_id = repair.channel_id
            if repair.pos_analytic_account_id and repair.sale_order_id:
                repair.sale_order_id.pos_analytic_account_id = (
                    repair.pos_analytic_account_id
                )
            if repair.sale_order_id and not repair.sale_order_id.client_order_ref:
                repair.sale_order_id.client_order_ref = repair.name
        return res

    def action_repair_done(self):
        """
        Override base method to add the following features:
        - Check owner in product source location
        """

        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        product_move_vals = []

        # Cancel moves with 0 quantity
        self.move_ids.filtered(
            lambda m: float_is_zero(
                m.quantity, precision_rounding=m.product_uom.rounding
            )
        )._action_cancel()

        no_service_policy = "service_policy" not in self.env["product.template"]
        # SOL qty delivered = repair.move_ids.quantity
        for repair in self:
            if all(not move.picked for move in repair.move_ids):
                repair.move_ids.picked = True
            if repair.sale_order_line_id:
                ro_origin_product = repair.sale_order_line_id.product_template_id
                # TODO: As 'service_policy' only appears with 'sale_project' module, isolate conditions related to this field in a 'sale_project_repair' module if it's worth
                if ro_origin_product.type == "service" and (
                    no_service_policy
                    or ro_origin_product.service_policy == "ordered_prepaid"
                ):
                    repair.sale_order_line_id.qty_delivered = (
                        repair.sale_order_line_id.product_uom_qty
                    )
            if not repair.product_id:
                continue

            if (
                repair.product_id.product_tmpl_id.tracking != "none"
                and not repair.lot_id
            ):
                raise ValidationError(
                    _(
                        "Serial number is required for product to repair : %s",
                        repair.product_id.display_name,
                    )
                )

            # Try to create move with the appropriate owner
            owner_id = False
            available_qty_owner = self.env["stock.quant"]._get_available_quantity(
                repair.product_id,
                repair.product_location_src_id,
                repair.lot_id,
                owner_id=repair.partner_id,
                strict=True,
            )
            if (
                float_compare(
                    available_qty_owner, repair.product_qty, precision_digits=precision
                )
                >= 0
            ):
                owner_id = repair.partner_id.id

            product_move_vals.append(
                {
                    "name": repair.name,
                    "product_id": repair.product_id.id,
                    "product_uom": repair.product_uom.id or repair.product_id.uom_id.id,
                    "product_uom_qty": repair.product_qty,
                    "partner_id": repair.partner_id.id,
                    "location_id": repair.product_location_src_id.id,
                    "location_dest_id": repair.product_location_dest_id.id,
                    "picked": True,
                    "picking_id": False,
                    "move_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": repair.product_id.id,
                                "lot_id": repair.lot_id.id,
                                "product_uom_id": repair.product_uom.id
                                or repair.product_id.uom_id.id,
                                "quantity": repair.product_qty,
                                "package_id": False,
                                "result_package_id": False,
                                "owner_id": owner_id,
                                "location_id": repair.product_location_src_id.id,
                                "company_id": repair.company_id.id,
                                "location_dest_id": repair.product_location_dest_id.id,
                                "consume_line_ids": [
                                    (6, 0, repair.move_ids.move_line_ids.ids)
                                ],
                            },
                        )
                    ],
                    "repair_id": repair.id,
                    "origin": repair.name,
                    "company_id": repair.company_id.id,
                }
            )

        product_moves = self.env["stock.move"].create(product_move_vals)
        repair_move = {m.repair_id.id: m for m in product_moves}
        for repair in self:
            move_id = repair_move.get(repair.id, False)
            if move_id:
                repair.move_id = move_id
        all_moves = self.move_ids + product_moves
        all_moves._action_done(cancel_backorder=True)

        for sale_line in self.move_ids.sale_line_id:
            price_unit = sale_line.price_unit
            sale_line.write(
                {"product_uom_qty": sale_line.qty_delivered, "price_unit": price_unit}
            )

        self.state = "done"
        return True
