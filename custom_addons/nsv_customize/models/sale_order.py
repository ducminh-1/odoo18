import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    channel_id = fields.Many2one(
        "sale.channel",
        "Channel",
        tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    # channel_account_tag_id = fields.Many2one('account.analytic.tag', related='channel_id.account_tag_id', string="Channel Tag")
    channel_analytic_account_id = fields.Many2one(
        "account.analytic.account",
        related="channel_id.analytic_account_id",
        string="Channel Analytic Account",
    )
    # pos_account_tag_id = fields.Many2one(
    #     'account.analytic.tag', 'POS', tracking=True,
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    pos_analytic_account_id = fields.Many2one(
        "account.analytic.account",
        "POS",
        tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    invoice_number = fields.Char(
        "Invoice Number", compute="_compute_invoice_number", store=True, readonly=True
    )
    employee_id = fields.Many2one("hr.employee", string="Employee")
    customer_phone = fields.Char(
        "Customer Phone", related="partner_id.phone", store=True
    )
    loyalty_level_id = fields.Many2one(
        "loyalty.level",
        string="Loyalty Level",
        related="partner_id.loyalty_level_id",
        store=True,
        tracking=True,
    )
    customer_birthday = fields.Date(
        related="partner_id.birthday", string="Customer Birthday", store=True
    )
    customer_loyalty_point_amount = fields.Float(
        related="partner_id.loyalty_point_amount", string="Loyalty Point Amount"
    )
    customer_tag = fields.Many2many(related="partner_id.category_id", string="Tag")
    is_have_applicable_loyalty_counpon_program = fields.Boolean(
        string="Is Have Applicable Loyalty Counpon Program",
        compute="_compute_is_have_applicable_loyalty_counpon_program",
    )
    applicable_loyalty_coupon_program_display_string = fields.Html(
        string="Applicable Loyalty Coupon Display String",
        compute="_compute_is_have_applicable_loyalty_counpon_program",
    )
    ticket_ids = fields.One2many("helpdesk.ticket", "so_id", string="Tickets")
    ticket_count = fields.Integer(
        "Tickets", compute="_compute_ticket_count", store=True
    )
    price_difference_order = fields.Boolean(
        "Price difference order", compute="_compute_price_difference_order", store=True
    )

    @api.depends("ticket_ids")
    def _compute_ticket_count(self):
        for record in self:
            record.ticket_count = len(record.ticket_ids.ids)

    @api.onchange("partner_id")
    def _onchange_partner_to_channel(self):
        if self.partner_id:
            self.channel_id = self.partner_id.channel_id or False

    # @api.onchange('user_id', 'team_id', 'partner_id')
    # def onchange_team_id(self):
    #     if self.team_id:
    #         self.analytic_account_id = self.team_id.analytic_account_id or False

    # @api.onchange('warehouse_id')
    # def onchange_warehouse_id(self):
    #     self.pos_account_tag_id = self.warehouse_id.analytic_tag_id or False

    @api.onchange("warehouse_id")
    def onchange_warehouse_id(self):
        #     self.pos_account_tag_id = self.warehouse_id.analytic_tag_id or False
        if self.warehouse_id:
            self.pos_analytic_account_id = (
                self.warehouse_id.analytic_account_id or False
            )

    @api.depends("state", "order_line.invoice_lines.move_id.invoice_number")
    def _compute_invoice_number(self):
        for order in self:
            if order.state not in ("done", "sale"):
                order.invoice_number = False
            else:
                invoices = self.env["account.move"].search(
                    [("invoice_origin", "=", order.name), ("state", "=", "posted")]
                )
                if len(invoices) > 0:
                    order.invoice_number = " + ".join(
                        [inv.invoice_number for inv in invoices if inv.invoice_number]
                    )
                else:
                    order.invoice_number = False

    def _compute_is_have_applicable_loyalty_counpon_program(self):
        readonly_orders = self.filtered(lambda order: order._is_readonly())
        for order in self - readonly_orders:
            loyalty_programs = order._get_applicable_loyalty_program()
            order.is_have_applicable_loyalty_counpon_program = (
                loyalty_programs and True or False
            )
            order.applicable_loyalty_coupon_program_display_string = (
                order._get_applicable_loyalty_coupon_display_string(loyalty_programs)
            )
        readonly_orders.is_have_applicable_loyalty_counpon_program = False
        readonly_orders.applicable_loyalty_coupon_program_display_string = ""

    def _get_applicable_loyalty_program(self):
        self.ensure_one()
        domain = [("is_loyalty_program", "=", True)]
        domain = expression.AND([self._get_program_domain(), domain])
        # No other way than to test all programs to the order
        programs = self.env["loyalty.program"].search(domain)
        # all_status = self._program_check_compute_points(programs)
        # program_points = {p: status['points'][0] for p, status in all_status.items() if 'points' in status}
        return programs

    def _get_applicable_loyalty_coupon_display_string(self, programs):
        return_string = ""
        suggest_string = _("Use following code:")
        for program in programs:
            display_string = "<div>"
            if program.program_type == "promo_code":
                display_string += f'{program.name} - {suggest_string}: {program.promo_code}' + linebreak
                # display_string += f'{program.name} - {suggest_string}: {", ".join(program.rule_ids.mapped('code'))}'
            else:
                display_string += program.name
            display_string += "</div>"
            return_string += display_string
        return return_string

    def _create_reward_coupon(self, program):
        return super(
            SaleOrder, self.with_context(coupon_prefix=program.coupon_prefix)
        )._create_reward_coupon(program)

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res["employee_id"] = self.employee_id and self.employee_id.id or False
        return res

    def unlink(self):
        for order in self:
            if order.picking_ids:
                raise UserError(
                    _("You can not delete a sales order which is related to a picking.")
                )
            if order.invoice_ids:
                raise UserError(
                    _("You can not delete a sales order which is invoiced already.")
                )
        return super().unlink()

    def action_cancel(self):
        # Check if there is any done picking!
        if self.picking_ids.filtered(lambda p: p.state == "done"):
            raise UserError(
                _(
                    "You can not cancel the Sale Order which is related to a done picking !"
                )
            )
        if self.invoice_ids.filtered(lambda l: l.move_id.posted_before):
            raise UserError(
                _(
                    "You can not cancel the Sale Order which is related to (a) posted once invoice(s) !"
                )
            )
        return super().action_cancel()

    def action_view_applicable_loyalty_coupon_program(self):
        self.ensure_one()
        action = self.env.ref("coupon.coupon_program_action_promo_program").read()[0]
        applicable_programs = self._get_applicable_programs().filtered(
            lambda p: p.is_loyalty_program
        )
        action["domain"] = [("id", "in", applicable_programs.ids)]
        return action

    def action_view_ticket_from_sale_order(self):
        self.ensure_one()
        action = self.env.ref("helpdesk.helpdesk_ticket_action_main_tree").read()[0]
        if self.ticket_count == 1:
            action["views"] = [
                (self.env.ref("helpdesk.helpdesk_ticket_view_form").id, "form")
            ]
            action["res_id"] = self.ticket_ids[0].id
        else:
            action["domain"] = [("so_id", "=", self.id)]
        return action

    def action_confirm(self):
        res = super().action_confirm()
        for rec in self:
            rec.picking_ids.write({"so_id": rec.id})
        return res

    def _create_invoices(self, grouped=True, final=False, date=None):
        return super()._create_invoices(grouped=grouped, final=final, date=date)

    def update_prices(self):
        super().update_prices()
        for rec in self.order_line:
            rec.price_rule = rec.price_unit

    @api.depends("order_line", "pricelist_id", "order_line.price_unit")
    def _compute_price_difference_order(self):
        for rec in self:
            price_difference_order = False
            if sum(rec.order_line.mapped("difference_ratio")) != 0:
                price_difference_order = True
            rec.price_difference_order = price_difference_order

    def action_unlock(self):
        for sale in self:
            if any(sale.invoice_ids.filtered(lambda inv: inv.state != "cancel")):
                raise UserError(
                    _(
                        'You cannot unlock a sale order that has invoices in a state other than "cancel".'
                    )
                )
        return super().action_unlock()
