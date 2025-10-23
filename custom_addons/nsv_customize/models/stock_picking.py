from odoo import fields, models
from odoo.exceptions import UserError

from .share_func import amount_to_text


class StockPicking(models.Model):
    _inherit = "stock.picking"

    shipping_address = fields.Char(
      string="Shipping Address"
    )
    order_ref = fields.Char(
        related="sale_id.client_order_ref", string="Customer Reference"
    )
    account_analytic_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    account_analytic_ids = fields.Many2many(
        "account.analytic.account",
        string="Analytic Accounts",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    # analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tag', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    so_id = fields.Many2one("sale.order", string="Sale Order")
    po_id = fields.Many2one("purchase.order", string="Purchase Order")

    ticket_id = fields.Many2one("helpdesk.ticket", string="Helpdesk Ticket")
    note = fields.Text("Notes")

    def get_amount_text(self, number):
        return amount_to_text(number)

    def button_validate(self):
        user = self.env["res.users"].browse(self.env.uid)
        is_allowed = user.has_groups(
            "nsv_customize.group_validate_transfer_operations, stock.group_stock_manager"
        )
        if not is_allowed:
            if self.picking_type_code == "internal":
                raise UserError(
                    "Bạn cần liên hệ đến Quản trị viên để Xác nhận hoạt động này!"
                )

        if any(
            ml.location_dest_id != self.location_dest_id for ml in self.move_line_ids
        ):
            raise UserError(
                "Vui lòng kiểm tra lại vị trí đích của các dòng vận chuyển. Tất cả các dòng phải có cùng vị trí đích với phiếu này."
            )
        return super().button_validate()
