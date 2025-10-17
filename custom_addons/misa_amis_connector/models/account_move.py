import logging

from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.fields import Command

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    misa_sa_voucher_ids = fields.One2many(
        "misa.sa_voucher", "move_id", string="Chứng từ bán hàng Misa"
    )
    misa_sa_voucher_count = fields.Integer(
        compute="_compute_misa_sa_voucher_count",
        string="Số lượng Chứng từ bán hàng Misa",
    )
    can_create_misa_sa_voucher = fields.Boolean(
        compute="_compute_can_create_misa_sa_voucher",
        string="Có thể tạo Chứng từ bán hàng Misa",
    )
    is_invoice_machine = fields.Boolean(string="Là hóa đơn máy tính tiền")
    misa_post_status = fields.Selection(
        [
            ("success", "Success"),
        ],
        compute="_compute_misa_post_status",
        store=True,
        string="Trạng thái MISA",
    )

    @api.depends("misa_sa_voucher_ids")
    def _compute_misa_sa_voucher_count(self):
        """Compute the number of MISA SA Vouchers linked to this move."""
        for move in self:
            move.misa_sa_voucher_count = len(move.misa_sa_voucher_ids)

    @api.depends("state", "move_type", "sale_id")
    def _compute_can_create_misa_sa_voucher(self):
        """Check if the move can create a MISA SA Voucher."""
        for move in self:
            move.can_create_misa_sa_voucher = (
                move.state == "posted"
                and move.move_type in ("out_invoice")
                and move.sale_id
            )

    @api.depends("misa_sa_voucher_ids", "misa_sa_voucher_ids.state")
    def _compute_misa_post_status(self):
        for move in self:
            if move.misa_sa_voucher_ids:
                # Assuming 'success' is the only state we care about for now
                if any(
                    voucher.state == "posted" for voucher in move.misa_sa_voucher_ids
                ):
                    move.misa_post_status = "success"
                else:
                    move.misa_post_status = False
            else:
                move.misa_post_status = False

    def _prepare_misa_sa_voucher(self):
        self.ensure_one()
        return {
            "voucher_type": "13",
            "org_refid": self.id,
            "org_refno": self.sale_id.name,
            "org_reftype_name": "Odoo Sale Order",
            # "is_sale_with_outward": True,
            "include_invoice": "1",
            "total_sale_amount_oc": self.amount_untaxed,
            "total_sale_amount": self.amount_untaxed,
            "total_amount_oc": self.amount_total,
            "total_amount": self.amount_total,
            "total_discount_amount_oc": sum(
                [line.discount_balance for line in self.invoice_line_ids]
            ),
            "total_discount_amount": sum(
                [line.discount_balance for line in self.invoice_line_ids]
            ),
            "total_vat_amount_oc": self.amount_tax,
            "total_vat_amount": self.amount_tax,
            "move_id": self.id,
            "partner_id": self.sale_id.partner_shipping_id.id,
            "voucher_line_ids": [],
            "invoice_is_invoice_machine": self.is_invoice_machine,
            "invoice_inv_series": "1C25MYY" if self.is_invoice_machine else "1C25TAA",
            "invoice_inv_template_no": "1",
            "misa_app_id": self.team_id.analytic_account_id.misa_app_id.id,
            "misa_branch_id": self.team_id.analytic_account_id.misa_branch_id.id,
        }

    def _create_misa_sa_vouchers(self):
        """Create invoice(s) for the given Sales Order(s).

        :param bool grouped: if True, invoices are grouped by SO id.
            If False, invoices are grouped by keys returned by :meth:`_get_invoice_grouping_keys`
        :param bool final: if True, refunds will be generated if necessary
        :param date: unused parameter
        :returns: created invoices
        :rtype: `misa.sa_voucher` recordset
        :raises: UserError if one of the orders has no invoiceable lines.
        """
        if not self.env["misa.sa_voucher"].has_access("create"):
            try:
                self.check_access("write")
            except AccessError:
                return self.env["misa.sa_voucher"]

        # 1) Create invoices.
        voucher_vals_list = []
        voucher_item_sequence = (
            0  # Incremental sequencing to keep the lines move on the invoice.
        )
        for move in self:
            move = move.with_context(lang=move.partner_id.lang)
            move = move.with_company(move.company_id)

            voucher_vals = move._prepare_misa_sa_voucher()
            voucher_line_vals = []
            for line in move.invoice_line_ids:
                voucher_line_vals.append(
                    Command.create(
                        line._prepare_sa_voucher_line(sequence=voucher_item_sequence)
                    ),
                )
                voucher_item_sequence += 1

            voucher_vals["voucher_line_ids"] += voucher_line_vals
            voucher_vals_list.append(voucher_vals)

        if len(voucher_vals_list) < len(self):
            SaleOrderLine = self.env["sale.order.line"]
            for invoice in voucher_vals_list:
                sequence = 1
                for line in invoice["voucher_line_ids"]:
                    line[2]["sequence"] = SaleOrderLine._get_invoice_line_sequence(
                        new=sequence, old=line[2]["sequence"]
                    )
                    sequence += 1

        _logger.info("%s", voucher_vals_list)
        # vouchers = (
        #     self.env["misa.sa_voucher"].sudo().with_context().create(voucher_vals_list)
        # )
        vouchers = self.env["misa.sa_voucher"]
        for vals in voucher_vals_list:
            voucher = self.env["misa.sa_voucher"].create(vals)
            # Delete other previous vouchers for the same move
            # voucher.misa_sa_voucher_ids.filtered(lambda v: v.id != voucher.id).unlink()
            voucher.move_id.misa_sa_voucher_ids.filtered(
                lambda v: v.id != voucher.id
            ).write({"state": "cancelled"})

            vouchers |= voucher
        _logger.info(
            "Created %s MISA SA Vouchers for %s Sale Orders",
            len(vouchers),
            len(self),
        )

        for voucher in vouchers:
            voucher.message_post_with_source(
                "mail.message_origin_link",
                # render_values={'self': voucher, 'origin': voucher.line_ids.sale_line_ids.order_id},
                render_values={"self": voucher, "origin": voucher.move_id},
                subtype_xmlid="mail.mt_note",
            )
        return vouchers

    def action_view_misa_sa_vouchers(self, sa_vouchers=None):
        if not sa_vouchers:
            sa_vouchers = self.mapped("misa_sa_voucher_ids")
        action = self.env["ir.actions.actions"]._for_xml_id(
            "misa_amis_connector.misa_sa_voucher_action"
        )
        if len(sa_vouchers) > 1:
            action["domain"] = [("id", "in", sa_vouchers.ids)]
        elif len(sa_vouchers) == 1:
            form_view = [
                (self.env.ref("misa_amis_connector.misa_sa_voucher_form").id, "form")
            ]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = sa_vouchers.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        context = {
            #     'default_vouchert_type': '1',
        }
        action["context"] = context
        return action
